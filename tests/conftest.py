import pytest
from os import environ
import pickle
import pandas as pd
from sources import Binance
from sinks import TimescaleDB
from config import Config


@pytest.fixture
def timescaleDB():
    return TimescaleDB(
        host=environ.get("TEST_TIMESCALE_HOST", "localhost"),
        port=environ.get("TEST_TIMESCALE_PORT", 5432),
        username=environ.get("TEST_TIMESCALE_USERNAME", "postgres"),
        password=environ.get("TEST_TIMESCALE_PASSWORD", "postgres")
    )


@pytest.fixture
def database():
    return environ.get("TEST_DATABASE", "binance")


@pytest.fixture
def symbol():
    return environ.get("TEST_SYMBOL", "BTCUSDT")


@pytest.fixture
def binance() -> Binance:
    return Binance()


@pytest.fixture
def test_data():
    with open('tests/test_data.pkl', 'rb') as file:
        data = pickle.load(file)
    return data


@pytest.fixture
def test_dataframe():
    return pd.read_pickle('tests/test_dataframe.pkl')


@pytest.fixture
def config(timescaleDB, database, symbol):
    config = Config()
    config.symbols = [symbol]
    config.database = database
    config.timescaledb = timescaleDB
    return config
