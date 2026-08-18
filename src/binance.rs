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
