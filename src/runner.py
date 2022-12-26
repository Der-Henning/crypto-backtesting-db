from typing import NoReturn
from os import environ
from config import Config
from psycopg2.errors import DuplicateDatabase
import logging
import sys
from time import sleep
from worker import Worker


def main() -> NoReturn:
    config = Config()

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG if config.debug else logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler()
        ])
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
