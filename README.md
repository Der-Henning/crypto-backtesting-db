[![Publish multi-arch Docker images](https://github.com/Der-Henning/crypto-backtesting-db/actions/workflows/docker-multi-arch.yml/badge.svg)](https://github.com/Der-Henning/crypto-backtesting-db/actions/workflows/docker-multi-arch.yml)
[![Tests](https://github.com/Der-Henning/crypto-backtesting-db/actions/workflows/tests.yml/badge.svg)](https://github.com/Der-Henning/crypto-backtesting-db/actions/workflows/tests.yml)
[![Publish multi-arch Docker images](https://github.com/Der-Henning/crypto-backtesting-db/actions/workflows/docker-multi-arch.yml/badge.svg)](https://github.com/Der-Henning/crypto-backtesting-db/actions/workflows/docker-multi-arch.yml)

# Crypto Backtesting Database

TimescaleDB to store historical crypto data from binance.com locally to generate data for backtesting fast.

## Installation

Install docker and docker compose.
Modify environment variables and mounts in `docker-compose.yml`.
Then run:

````bash
docker-compose up
````

The script will download the data for the selected symbols with an interval of 1m. If you select a start date far back in time the initial download will take a long time because of the limitations of the binance API. After that the script will only add new data fast.

## Usage

Now you can use the database as source for backtesting projects.

Connect to the PostgresDB as usually:

- Port: 5432
- Username: postgres
- Password: as set in `docker-compose.yml`
- Database: binance
- Table: lowercase symbol

Example SQL Query to create data for the BTC/USDT symbol on 5m interval for the last year from today:

````sql
SELECT
    time_bucket('5 minutes', time) AS opentime,
    first(open, time) AS open,
    min(low) AS low,
    max(high) AS high,
    last(close, time) AS close,
    sum(volume) AS volume,
    last(close_time, time) AS close_time,
    sum(quote_asset_volume) AS quote_asset_volume,
    sum(number_trades) AS number_trades,
    sum(taker_buy_base_asset_volume) AS taker_buy_base_asset_volume,
    sum(taker_buy_quote_asset_volume) AS taker_buy_quote_asset_volume
FROM btcusdt WHERE
    time > now() - INTERVAL '1 year' AND
    time <= now()
GROUP BY opentime
````
