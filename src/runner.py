from typing import NoReturn
from os import environ
from config import Config
from psycopg2.errors import DuplicateDatabase
import logging
import sys
from time import sleep
from worker import Worker
from http.client import HTTPConnection


def main() -> NoReturn:
    config = Config()

    HTTPConnection.debuglevel = 0
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)
    logging.root.setLevel(logging.DEBUG if config.debug else logging.INFO)
    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)-8s %(message)s'
    )
    stream_handler.setFormatter(stream_formatter)
    logging.root.addHandler(stream_handler)

    logger = logging.getLogger('cryptodb')

    try:
        config.timescaledb.createDatabase("binance", False)
        logger.info("DB binance created")
    except DuplicateDatabase:
        logger.debug("DB binance already exists")

    worker = Worker(config)

    while True:
        logger.info("Started crypto scanner")
        try:
            worker.run()
        except:
            logger.error("Job Error! - {0}".format(sys.exc_info()))
        finally:
            sleep(config.sleep_time)


if __name__ == "__main__":
    main()
