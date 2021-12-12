# Crypto Backtesting Database

TimescaleDB to store historical crypto data from binance.com. 

## Installation

Install docker and docker compose.
Modify environment variables and mounts in ``docker-compose.yml``.
Then run:

```
docker-compose up
```

## Usage

Now you can use the database as source for backtesting projects.

Example SQL Query to create any time interval:

```sql
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
    time <= now() - INTERVAL 'now'
GROUP BY opentime
```
