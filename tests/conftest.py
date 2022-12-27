import pytest
import requests
import json
from os import environ
import pickle
import pandas as pd
from sources import Binance
from sinks import TimescaleDB
from config import Config


@pytest.fixture(scope='function')
def timescaledb():
    return TimescaleDB(
        host=environ.get("TEST_TIMESCALE_HOST", "localhost"),
        port=environ.get("TEST_TIMESCALE_PORT", 5432),
        username=environ.get("TEST_TIMESCALE_USERNAME", "postgres"),
        password=environ.get("TEST_TIMESCALE_PASSWORD", "postgres")
    )


@pytest.fixture(scope='function')
def database():
    return environ.get("TEST_DATABASE", "binance")


@pytest.fixture(scope='function')
def symbol():
    return environ.get("TEST_SYMBOL", "BTCUSDT")


@pytest.fixture(scope='function')
def binance() -> Binance:
    return Binance()


@pytest.fixture(scope='function')
def test_data():
    with open('tests/test_data.pkl', 'rb') as file:
        data = pickle.load(file)
    return data


@pytest.fixture(scope='function')
def test_dataframe():
    return pd.read_pickle('tests/test_dataframe.pkl')


@pytest.fixture(scope='function')
def binance_ping_response(responses):
    responses.add(
        responses.GET,
        "https://api.binance.com/api/v3/ping",
        body="{}",
        status=200
    )


@pytest.fixture(scope='function')
def binance_get_klines_response(responses, test_data: list[list]):
    def request_callback(request: requests.PreparedRequest):
        start = int(request.params.get("startTime"))
        end = int(request.params.get("endTime"))
        limit = int(request.params.get("limit"))
        response_data = []
        for row in test_data:
            if len(response_data) > limit:
                break
            if row[0] >= start and row[0] <= end:
                response_data.append(row)
        return (200, {}, json.dumps(response_data))

    responses.add_callback(
        responses.GET,
        "https://api.binance.com/api/v3/klines",
        callback=request_callback,
        content_type="text/plain"
    )


@pytest.fixture(scope='function')
def config(timescaledb, binance, database, symbol):
    config = Config()
    config.symbols = [symbol]
    config.database = database
    config.timescaledb = timescaledb
    config.binance = binance
    return config
