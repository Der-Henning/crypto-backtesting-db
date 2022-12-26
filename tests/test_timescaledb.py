from os import environ
import pytest
import pandas as pd
from sinks.timescaledb import TimescaleDB


@pytest.fixture
def timescaleDB():
    return TimescaleDB(
        host=environ.get("TEST_TIMESCALE_HOST", "localhost"),
        port=environ.get("TEST_TIMESCALE_PORT", 5432),
        username=environ.get("TEST_TIMESCALE_USERNAME", "postgres"),
        password=environ.get("TEST_TIMESCALE_PASSWORD", "MyPassword")
    )


@pytest.fixture
def database():
    return environ.get("TEST_DATABASE", "binance")


@pytest.fixture
def symbol():
    return environ.get("TEST_SYMBOL", "BTCUSDT")


@pytest.fixture
def test_data():
    return pd.read_pickle('tests/test_data.pkl')


def test_database(timescaleDB: TimescaleDB, database: str, symbol: str, test_data: pd.DataFrame):
    timescaleDB.dropDatabase(database)

    timescaleDB.createDatabase(database)
    timescaleDB.createDatabase(database, False)
    timescaleDB.createDatabase(database, True)

    timescaleDB.createTable(database, symbol, False)
    timescaleDB.createTable(database, symbol, False)
    timescaleDB.createTable(database, symbol, True)
    timescaleDB.dropTable(database, symbol)
    timescaleDB.createTable(database, symbol, False)

    timescaleDB.write(database, symbol, test_data)
    first_ts = timescaleDB.getFirstTimestamp(database, symbol)
    assert pd.Timestamp(test_data['time'].values[0]).tz_localize(
        'UTC') == pd.to_datetime(first_ts)

    last_ts = timescaleDB.getLastTimestamp(database, symbol)
    assert pd.Timestamp(test_data['time'].values[-1]
                        ).tz_localize('UTC') == pd.to_datetime(last_ts)

    timescaleDB.dropDatabase('binance')
