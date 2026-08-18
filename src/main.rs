use anyhow::{Context, Result};
use binance::BinanceClient;
use binance_sdk::spot::rest_api::KlinesIntervalEnum;
use clap::Parser;
use dotenvy::dotenv;
use futures_util::StreamExt;
use log::LevelFilter::Info;
use log::{error, info};
use postgres::PgConnector;
use sqlx::types::chrono::{DateTime, Utc};
use std::pin::pin;
use std::time::Duration;
use tokio::task::JoinSet;

pub mod binance;
pub mod postgres;

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    #[arg(short('s'), long, env = "BINANCE_SYMBOLS", value_delimiter = ',')]
    symbols: Vec<String>,
    #[arg(short('i'), long, env = "BINANCE_INTERVAL", default_value = "1m")]
    interval: KlinesIntervalEnum,
    #[arg(short('H'), long, env = "TIMESCALE_HOST", default_value = "127.0.0.1")]
    db_host: String,
    #[arg(short('u'), long, env = "TIMESCALE_PORT")]
    db_port: u16,
    #[arg(short('P'), long, env = "TIMESCALE_USERNAME")]
    db_username: String,
    #[arg(short('p'), long, env = "TIMESCALE_PASSWORD")]
    db_password: String,
    #[arg(short('d'), long, env = "TIMESCALE_DBNAME")]
    db_name: String,
    #[arg(env = "BINANCE_API_KEY")]
    api_key: String,
    #[arg(env = "BINANCE_API_SECRET")]
    api_secret: String,
    #[arg(short('S'), long, env = "BINANCE_START_DATE")]
    start_date: DateTime<Utc>,
    #[arg(short('T'), long, env = "BINANCE_USE_TESTNET", default_value_t = false)]
    use_testnet: bool,
    #[arg(long, env = "SLEEP_TIME", default_value_t = 60)]
    sleep_time: u64,
}

#[tokio::main]
async fn main() -> Result<()> {
    dotenv().ok();
    env_logger::builder()
        .format_target(false)
        .filter_level(Info)
        .parse_default_env()
        .init();

    let args = Args::parse();

    let db = PgConnector::new(
        &args.db_host,
        args.db_port,
        &args.db_username,
        &args.db_password,
        &args.db_name,
    )
    .await?;
    db.create_market_table().await?;

    let client = BinanceClient::new(&args.api_key, &args.api_secret, args.use_testnet)?;

    let mut ticker = tokio::time::interval(Duration::from_secs(args.sleep_time));

    info!("Configured symbols: {:?}", args.symbols);

    loop {
        ticker.tick().await;
        let mut set = JoinSet::new();
        args.symbols.iter().for_each(|symbol| {
            let db = db.clone();
            let client = client.clone();
            let interval = args.interval.clone();
            let symbol = symbol.clone();
            set.spawn(
                async move { update_symbol(client, db, symbol, interval, args.start_date).await },
            );
        });
        while let Some(result) = set.join_next().await {
            match result {
                Ok(Ok(())) => {}
                Ok(Err(err)) => error!("Symbol update failed: {err:#}"),
                Err(err) => error!("Symbol task failed to join: {err}"),
            }
        }
    }
}

async fn update_symbol(
    client: BinanceClient,
    postgres: PgConnector,
    symbol: String,
    interval: KlinesIntervalEnum,
    start_date: DateTime<Utc>,
) -> Result<()> {
    info!("Updating {}", symbol);
    let start_date = postgres
        .get_last_timestamp(&symbol)
        .await?
        .unwrap_or(start_date);
    let end_date = Utc::now();

    let mut s = pin!(client.get_klines_iter(&symbol, interval, start_date, end_date, 1000));

    while let Some(chunk) = s.next().await {
        let klines = chunk.with_context(|| format!("Failed to fetch {symbol}"))?;
        postgres
            .insert(&symbol, klines)
            .await
            .with_context(|| format!("Failed to insert {symbol}"))?;
    }
    Ok(())
}
