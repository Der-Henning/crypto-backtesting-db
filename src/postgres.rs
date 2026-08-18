use crate::binance::KlineDataVec;
use sqlx::postgres::{PgConnectOptions, PgPoolOptions};
use sqlx::types::chrono::{DateTime, Utc};
use sqlx::{Error, PgPool, Postgres, QueryBuilder};
use std::time::Duration;

#[derive(Debug, Clone)]
pub struct PgConnector {
    pub pool: PgPool,
}

impl PgConnector {
    pub async fn new(
        host: &str,
        port: u16,
        user: &str,
        password: &str,
        dbname: &str,
        max_connections: u32,
    ) -> Result<Self, Error> {
        let opts = PgConnectOptions::new()
            .host(host)
            .port(port)
            .username(user)
            .password(password)
            .database(dbname);
        let pool = PgPoolOptions::new()
            .max_connections(max_connections)
            .acquire_slow_threshold(Duration::from_secs(10))
            .connect_with(opts)
            .await?;
        Ok(Self { pool })
    }

    pub async fn get_last_timestamp(&self, symbol: &str) -> Result<Option<DateTime<Utc>>, Error> {
        const SQL: &str = "SELECT time FROM market WHERE symbol=$1 ORDER BY time DESC LIMIT 1";
        let res: Option<(DateTime<Utc>,)> = sqlx::query_as(SQL)
            .bind(symbol)
            .fetch_optional(&self.pool)
            .await?;
        match res {
            Some((ts,)) => Ok(Some(ts)),
            _ => Ok(None),
        }
    }

    pub async fn get_first_timestamp(&self, symbol: &str) -> Result<Option<DateTime<Utc>>, Error> {
        const SQL: &str = "SELECT time FROM market WHERE symbol=$1 ORDER BY time ASC LIMIT 1";
        let res: Option<(DateTime<Utc>,)> = sqlx::query_as(SQL)
            .bind(symbol)
            .fetch_optional(&self.pool)
            .await?;
        match res {
            Some((ts,)) => Ok(Some(ts)),
            _ => Ok(None),
        }
    }

    pub async fn is_hypertable(&self, table: &str) -> Result<bool, sqlx::Error> {
        static SQL: &str =
            "SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = $1";
        Ok(sqlx::query(SQL)
            .bind(table)
            .fetch_optional(&self.pool)
            .await?
            .is_some())
    }

    pub async fn create_market_table(&self) -> Result<(), sqlx::Error> {
        const SQL: &str = r#"
        CREATE TABLE IF NOT EXISTS market (
            symbol TEXT NOT NULL,
            time TIMESTAMP WITH TIME ZONE NOT NULL,
            open NUMERIC(20,10) NOT NULL,
            high NUMERIC(20,10) NOT NULL,
            low NUMERIC(20,10) NOT NULL,
            close NUMERIC(20,10) NOT NULL,
            volume NUMERIC(28,10) NOT NULL,
            close_time TIMESTAMP WITH TIME ZONE NOT NULL,
            quote_asset_volume NUMERIC(28,10) NOT NULL,
            number_of_trades BIGINT NOT NULL,
            taker_buy_base_asset_volume NUMERIC(28,10) NOT NULL,
            taker_buy_quote_asset_volume NUMERIC(28,10) NOT NULL,
            PRIMARY KEY (symbol, time)
        )
        "#;
        sqlx::query(SQL).execute(&self.pool).await?;
        if !self.is_hypertable("market").await? {
            const SQL: &str = "SELECT create_hypertable('market', 'time')";
            sqlx::query(SQL).execute(&self.pool).await?;
        }
        Ok(())
    }

    pub async fn insert(&self, symbol: &str, klines: KlineDataVec) -> Result<u64, Error> {
        let rows = klines
            .0
            .into_iter()
            .map(|row| {
                let time = DateTime::from_timestamp_millis(row.time)
                    .ok_or_else(|| Error::Protocol("invalid Binance open timestamp".into()))?;
                let close_time = DateTime::from_timestamp_millis(row.close_time)
                    .ok_or_else(|| Error::Protocol("invalid Binance close timestamp".into()))?;

                Ok((
                    time,
                    row.open,
                    row.high,
                    row.low,
                    row.close,
                    row.volume,
                    close_time,
                    row.quote_asset_volume,
                    row.number_of_trades,
                    row.taker_buy_base_asset_volume,
                    row.taker_buy_quote_asset_volume,
                ))
            })
            .collect::<Result<Vec<_>, Error>>()?;

        if rows.is_empty() {
            return Ok(0);
        }

        let mut query = QueryBuilder::<Postgres>::new(
            "INSERT INTO market (\
                symbol, time, open, high, low, close, volume, close_time, \
                quote_asset_volume, number_of_trades, taker_buy_base_asset_volume, \
                taker_buy_quote_asset_volume\
            ) ",
        );
        query.push_values(rows, |mut values, row| {
            values
                .push_bind(symbol)
                .push_bind(row.0)
                .push_bind(row.1)
                .push_bind(row.2)
                .push_bind(row.3)
                .push_bind(row.4)
                .push_bind(row.5)
                .push_bind(row.6)
                .push_bind(row.7)
                .push_bind(row.8)
                .push_bind(row.9)
                .push_bind(row.10);
        });
        query.push(
            " ON CONFLICT (symbol, time) DO UPDATE SET \
                open = EXCLUDED.open, \
                high = EXCLUDED.high, \
                low = EXCLUDED.low, \
                close = EXCLUDED.close, \
                volume = EXCLUDED.volume, \
                close_time = EXCLUDED.close_time, \
                quote_asset_volume = EXCLUDED.quote_asset_volume, \
                number_of_trades = EXCLUDED.number_of_trades, \
                taker_buy_base_asset_volume = EXCLUDED.taker_buy_base_asset_volume, \
                taker_buy_quote_asset_volume = EXCLUDED.taker_buy_quote_asset_volume",
        );

        Ok(query.build().execute(&self.pool).await?.rows_affected())
    }
}
