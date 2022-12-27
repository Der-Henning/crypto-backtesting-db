from config import Config
import logging
from binance import helpers
from datetime import datetime


class Worker():
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger("cryptodb")

    def run(self):
        for symbol in self.config.symbols:
            self.logger.info("Current Symbol: {}".format(symbol))
            try:
                self.config.timescaledb.createTable(
                    self.config.database, symbol)
            except:
                # psycopg2.DatabaseError: table "btcusdt" is already a hypertable
                pass

            start_time = self.config.start_time
            start_timestamp = helpers.convert_ts_str(start_time) / 1000
            first_time = self.config.timescaledb.getFirstTimestamp(
                self.config.database, symbol)

            if start_timestamp and first_time and start_timestamp < datetime.timestamp(first_time):
                self.logger.warning(
                    "Start time before first timestamp in database")
                self.logger.warning(
                    "Recreating table {}".format(symbol.lower()))
                self.config.timescaledb.createTable(
                    self.config.database, symbol, True)

            last_time = self.config.timescaledb.getLastTimestamp(
                self.config.database, symbol)
            if last_time:
                start_time = str(last_time)
            klines_df = self.config.binance.get_klines(
                symbol, startTime=start_time, endTime=self.config.end_time)
            self.logger.debug(klines_df)
            self.config.timescaledb.write(
                self.config.database, symbol, klines_df)
