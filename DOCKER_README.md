# Quick reference

Readme, source and documentation on [https://github.com/Der-Henning/crypto-backtesting-db](https://github.com/Der-Henning/crypto-backtesting-db).

# Supported Tags and respective `Dockerfile` links

 The `latest` images represent the latest stable release.
 The `edge` images contain the latest commits to the main branch.

- [`edge`](https://github.com/Der-Henning/crypto-backtesting-db/blob/main/Dockerfile)
- [`v0.2`, `v0.2.2`, `latest`](https://github.com/Der-Henning/crypto-backtesting-db/blob/v0.2.2/Dockerfile)

# Quick Start

**Docker Compose Example:**

````xml
services:
  worker:
    image: derhenning/crypto-db:latest
    environment:
      - DEBUG=false                                  ## true for debug log messages
      - BINANCE_SYMBOLS=BTCUSDT,ETHUSDT              ## Symbols as JSON array
      - BINANCE_START_DATE=2026-08-01T00:00:00+00:00 ## Beginn of time series
      - SLEEP_TIME=60                                ## Time to wait till next scan in seconds - default 60 seconds
      - BINANCE_API_KEY=$BINANCE_API_KEY             ## your Binance API Key
      - BINANCE_API_SECRET=$BINANCE_API_SECRET       ## your Binance API Secret
      - TIMESCALE_HOST=db
      - TIMESCALE_PORT=5432
      - TIMESCALE_USERNAME=postgres
      - TIMESCALE_PASSWORD=postgres
      - TIMESCALE_DBNAME=binance

  db:
    image: timescale/timescaledb:2.29.1-pg18
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: binance
    ports:
      - 5432:5432
    volumes:
      - data:/var/lib/postgresql

volumes:
  data:
````
