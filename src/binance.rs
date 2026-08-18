use anyhow::{Result, anyhow};
use async_stream::stream;
use binance_sdk::common::config::ConfigurationRestApi;
use binance_sdk::config::ConfigurationWebsocketStreams;
use binance_sdk::spot::rest_api::ExchangeInfoParams;
use binance_sdk::spot::websocket_streams::TradeParams;
use binance_sdk::spot::{
    SpotRestApi, SpotWsStreams,
    rest_api::{KlinesIntervalEnum, KlinesItemInner, KlinesParams, RestApi},
    websocket_streams::WebsocketStreamsHandle,
};
use futures_core::stream::Stream;
use sqlx::types::{
    Decimal,
    chrono::{DateTime, Utc},
};
use std::str::FromStr;
use std::sync::Arc;
use tokio::time::{Duration, sleep};

#[derive(Debug)]
pub struct KlineData {
    pub time: i64,
    pub open: Decimal,
    pub high: Decimal,
    pub low: Decimal,
    pub close: Decimal,
    pub volume: Decimal,
    pub close_time: i64,
    pub quote_asset_volume: Decimal,
    pub number_of_trades: i64,
    pub taker_buy_base_asset_volume: Decimal,
    pub taker_buy_quote_asset_volume: Decimal,
}

impl TryFrom<Vec<KlinesItemInner>> for KlineData {
    type Error = anyhow::Error;

    fn try_from(value: Vec<KlinesItemInner>) -> Result<Self> {
        fn try_to_decimal(v: &KlinesItemInner) -> Result<Decimal> {
            match v {
                KlinesItemInner::String(s) => Ok(Decimal::from_str(s)?),
                _ => Err(anyhow!("Invalid type for decimal field")),
            }
        }

        fn try_to_i64(v: &KlinesItemInner) -> Result<i64> {
            match v {
                KlinesItemInner::Integer(i) => Ok(*i),
                _ => Err(anyhow!("Invalid type for integer field")),
            }
        }

        if value.len() < 11 {
            return Err(anyhow!("Invalid klines vec"));
        }

        Ok(KlineData {
            time: try_to_i64(&value[0])?,
            open: try_to_decimal(&value[1])?,
            high: try_to_decimal(&value[2])?,
            low: try_to_decimal(&value[3])?,
            close: try_to_decimal(&value[4])?,
            volume: try_to_decimal(&value[5])?,
            close_time: try_to_i64(&value[6])?,
            quote_asset_volume: try_to_decimal(&value[7])?,
            number_of_trades: try_to_i64(&value[8])?,
            taker_buy_base_asset_volume: try_to_decimal(&value[9])?,
            taker_buy_quote_asset_volume: try_to_decimal(&value[10])?,
        })
    }
}

#[derive(Debug)]
pub struct KlineDataVec(pub Vec<KlineData>);

impl TryFrom<Vec<Vec<KlinesItemInner>>> for KlineDataVec {
    type Error = anyhow::Error;

    fn try_from(value: Vec<Vec<KlinesItemInner>>) -> Result<Self> {
        Ok(Self(
            value
                .into_iter()
                .map(KlineData::try_from)
                .collect::<Result<Vec<_>>>()?,
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn valid_kline(time: i64, close_time: i64) -> Vec<KlinesItemInner> {
        vec![
            KlinesItemInner::Integer(time),
            KlinesItemInner::String("100.12345678".to_owned()),
            KlinesItemInner::String("101.12345678".to_owned()),
            KlinesItemInner::String("99.12345678".to_owned()),
            KlinesItemInner::String("100.98765432".to_owned()),
            KlinesItemInner::String("42.50000000".to_owned()),
            KlinesItemInner::Integer(close_time),
            KlinesItemInner::String("4250.12345678".to_owned()),
            KlinesItemInner::Integer(1234),
            KlinesItemInner::String("21.25000000".to_owned()),
            KlinesItemInner::String("2125.12345678".to_owned()),
            KlinesItemInner::String("ignored field".to_owned()),
        ]
    }

    #[test]
    fn parses_a_valid_binance_kline() {
        let kline = KlineData::try_from(valid_kline(1_700_000_000_000, 1_700_000_059_999))
            .expect("valid Binance kline should parse");

        assert_eq!(kline.time, 1_700_000_000_000);
        assert_eq!(kline.open, Decimal::from_str("100.12345678").unwrap());
        assert_eq!(kline.high, Decimal::from_str("101.12345678").unwrap());
        assert_eq!(kline.low, Decimal::from_str("99.12345678").unwrap());
        assert_eq!(kline.close, Decimal::from_str("100.98765432").unwrap());
        assert_eq!(kline.volume, Decimal::from_str("42.50000000").unwrap());
        assert_eq!(kline.close_time, 1_700_000_059_999);
        assert_eq!(
            kline.quote_asset_volume,
            Decimal::from_str("4250.12345678").unwrap()
        );
        assert_eq!(kline.number_of_trades, 1234);
        assert_eq!(
            kline.taker_buy_base_asset_volume,
            Decimal::from_str("21.25000000").unwrap()
        );
        assert_eq!(
            kline.taker_buy_quote_asset_volume,
            Decimal::from_str("2125.12345678").unwrap()
        );
    }

    #[test]
    fn rejects_a_kline_with_too_few_fields() {
        let error = KlineData::try_from(valid_kline(1, 2)[..10].to_vec())
            .expect_err("short Binance kline must be rejected");

        assert_eq!(error.to_string(), "Invalid klines vec");
    }

    #[test]
    fn rejects_incorrect_field_types() {
        let mut kline = valid_kline(1, 2);
        kline[1] = KlinesItemInner::Integer(100);

        let error = KlineData::try_from(kline).expect_err("numeric open price must be a string");

        assert_eq!(error.to_string(), "Invalid type for decimal field");
    }

    #[test]
    fn rejects_invalid_decimal_values() {
        let mut kline = valid_kline(1, 2);
        kline[4] = KlinesItemInner::String("not-a-decimal".to_owned());

        assert!(KlineData::try_from(kline).is_err());
    }

    #[test]
    fn converts_batches_in_order_and_rejects_invalid_rows() {
        let batch = KlineDataVec::try_from(vec![valid_kline(1, 2), valid_kline(3, 4)])
            .expect("valid Binance kline batch should parse");
        assert_eq!(batch.0.len(), 2);
        assert_eq!(batch.0[0].time, 1);
        assert_eq!(batch.0[1].time, 3);

        let mut invalid_kline = valid_kline(5, 6);
        invalid_kline[8] = KlinesItemInner::String("1234".to_owned());
        assert!(KlineDataVec::try_from(vec![valid_kline(1, 2), invalid_kline]).is_err());
    }
}

#[derive(Debug)]
pub struct TradeData {
    pub time: u64,
    pub id: u64,
    pub price: Decimal,
    pub qty: Decimal,
    pub quote_qty: Decimal,
    pub is_buyer_maker: bool,
    pub is_best_match: bool,
}

#[derive(Debug)]
pub struct TradeDataVec(pub Vec<TradeData>);

#[derive(Clone)]
pub struct BinanceClient {
    rest_client: Arc<RestApi>,
    stream_client: Arc<WebsocketStreamsHandle>,
}

impl BinanceClient {
    pub fn new(api_key: &str, secret_key: &str, testnet: bool) -> Result<Self> {
        let api_configuration = ConfigurationRestApi::builder()
            .api_key(api_key)
            .api_secret(secret_key)
            .build()?;
        let stream_configuration = ConfigurationWebsocketStreams::builder().build()?;
        let client = if testnet {
            Self {
                rest_client: Arc::new(SpotRestApi::testnet(api_configuration)),
                stream_client: Arc::new(SpotWsStreams::testnet(stream_configuration)),
            }
        } else {
            Self {
                rest_client: Arc::new(SpotRestApi::production(api_configuration)),
                stream_client: Arc::new(SpotWsStreams::production(stream_configuration)),
            }
        };
        Ok(client)
    }

    pub async fn get_exchange_info(&self) -> Result<()> {
        let params = ExchangeInfoParams::builder().build()?;
        let info = self.rest_client.exchange_info(params).await?;
        println!("{:?}", info.data().await?);
        Ok(())
    }

    pub fn get_klines_iter<'a>(
        &'a self,
        symbol: &'a str,
        interval: KlinesIntervalEnum,
        start_time: DateTime<Utc>,
        end_time: DateTime<Utc>,
        limit: i32,
    ) -> impl Stream<Item = Result<KlineDataVec>> {
        let mut current_start = start_time.timestamp_millis();
        let mut done = false;

        stream! {
            while !done {
                let data = self.get_klines(
                    symbol,
                    interval.clone(),
                    current_start,
                    end_time.timestamp_millis(),
                    limit,
                ).await?;
                done = data.0.len() < limit as usize;
                if !done {
                    current_start = data.0.last().unwrap().close_time + 1;
                }
                yield Ok(data)
            }
        }
    }

    /// https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints
    pub async fn get_klines(
        &self,
        symbol: &str,
        interval: KlinesIntervalEnum,
        start_time: i64,
        end_time: i64,
        limit: i32,
    ) -> Result<KlineDataVec> {
        let params = KlinesParams::builder(symbol.to_string(), interval)
            .start_time(start_time)
            .end_time(end_time)
            .limit(limit)
            .build()?;
        let response = self.rest_client.klines(params).await?;

        let raw_data = response.data().await?;
        let data = KlineDataVec::try_from(raw_data)?;

        Ok(data)
    }

    pub async fn get_order_market(&self, symbol: &str) -> Result<()> {
        let con = self.stream_client.connect().await?;
        let params = TradeParams::builder(symbol.to_string()).build()?;
        let stream = con.trade(params).await?;

        stream.on_message(|data| {
            println!("{:?}", data);
        });

        sleep(Duration::from_secs(30)).await;

        stream.unsubscribe().await;

        Ok(())
    }
}
