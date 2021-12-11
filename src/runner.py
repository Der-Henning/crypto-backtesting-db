from os import environ
import json
from sinks import TimescaleDB
from sources import Binance
from psycopg2.errors import DuplicateDatabase
from binance import helpers
from datetime import datetime
import logging
import sys
from time import sleep

config = {
    'symbols': json.loads(environ.get("SYMBOLS", "[]")),
    'start_time': environ.get("START_DATE"),
    'sleep_time': environ.get("SLEEP_TIME", 60),
    'binance': {
        'api_key': environ.get("BINANCE_API_KEY"),
        'api_secret': environ.get("BINANCE_API_SECRET")
    },
    'timescale': {
        'host': environ.get("TIMESCALE_HOST"),
        'port': environ.get("TIMESCALE_PORT"),
        'username': environ.get("TIMESCALE_USERNAME"),
        'password': environ.get("TIMESCALE_PASSWORD")
    }
}

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        #logging.FileHandler(log_file, mode="w"),
        logging.StreamHandler()
    ])
log = logging.getLogger('runner')

def worker():
    log.debug(config)
    timescaleDB = TimescaleDB(**config['timescale'])
    binance = Binance(**config['binance'])
    try:
        timescaleDB.createDatabase("binance", False)
        log.info("DB binance created")
    except DuplicateDatabase:
        log.debug("DB binance already exists")

    database = 'binance'

    for symbol in config['symbols']:
        log.info("Current Symbol: {}".format(symbol))
        try:
            timescaleDB.createTable(database, symbol)
        except:
            ## psycopg2.DatabaseError: table "btcusdt" is already a hypertable
            pass

        start_time = config['start_time']
        last_time = timescaleDB.getLastTimestamp(database, symbol)
        first_timestamp = datetime.timestamp(timescaleDB.getFirstTimestamp(database, symbol))
        start_timestamp = helpers.convert_ts_str(start_time) / 1000

        if start_timestamp and first_timestamp and start_timestamp < first_timestamp:
            log.warn("Start time befor first timestamp in database")
            log.warn("Recreating table {}".format(symbol.lower()))
            timescaleDB.createTable(database, symbol, True)

        if last_time:
            start_time = str(last_time)
        klines_df = binance.get_klines(symbol, startTime=start_time)
        log.debug(klines_df)
        timescaleDB.write(database, symbol, klines_df)


def main():
    while True:
        log.info("Started crypto scanner")
        try:
            worker()
        except:
            log.error("Job Error! - {0}".format(sys.exc_info()))
        finally:
            sleep(config['sleep_time'])

if __name__ == "__main__":
    main()