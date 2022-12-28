# Quick reference

Readme, source and documentation on [https://github.com/Der-Henning/crypto-backtesting-db](https://github.com/Der-Henning/crypto-backtesting-db).

# Supported Tags and respective `Dockerfile` links

 The `latest` images represent the latest stable release.
 The `edge` images contain the latest commits to the main branch.

- [`edge`](https://github.com/Der-Henning/crypto-backtesting-db/blob/main/Dockerfile)
- [`v0.1`, `v0.1.3`, `latest`](https://github.com/Der-Henning/crypto-backtesting-db/blob/v0.1.2/Dockerfile)

# Quick Start

**Docker Compose Example:**

````xml
version: "3.3"
services:
  worker:
    image: derhenning/crypto-db:latest
    environment:
      - DEBUG=false                 ## true for debug log messages
      - SYMBOLS=["BTCUSDT"]         ## Symbols as JSON array
      - START_DATE=Januar 01, 2020  ## Beginn of time series
      - SLEEP_TIME=60               ## Time to wait till next scan in seconds - default 60 seconds
      - BINANCE_API_KEY=            ## your Binance API Key
      - BINANCE_API_SECRET=         ## your Binance API Secret
      - TIMESCALE_HOST=db
      - TIMESCALE_PORT=5432
      - TIMESCALE_USERNAME=postgres
      - TIMESCALE_PASSWORD=postgres
  db:
    image: timescale/timescaledb:2.9.1-pg14
    environment:
      - POSTGRES_PASSWORD=postgres
    ports:
      - 5432:5432
    volumes:
      - data:/var/lib/postgresql/data

volumes:
  data:
````
