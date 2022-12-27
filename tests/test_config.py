import pytest
from config import Config
from sinks import TimescaleDB
from sources import Binance


@pytest.fixture
def environment() -> dict:
    return {
        "DEBUG": "true",
        "SYMBOLS": '["BTCUSDT","ETHUSDT"]',
        "START_DATE": "01.01.2021",
        "END_DATE": "01.02.2021",
        "SLEEP_TIME": "30",
        "TIMESCALE_HOST": "postgres",
        "TIMESCALE_PORT": "1234",
        "TIMESCALE_USERNAME": "user",
        "TIMESCALE_PASSWORD": "password",
        "BINANCE_API_KEY": "123456789",
        "BINANCE_API_SECRET": "abcdefghijklmn"
    }


@pytest.fixture
def assert_config():
    return {
        "debug": True,
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "start_time": "01.01.2021",
        "end_time": "01.02.2021",
        "sleep_time": 30,
        "timescaledb": TimescaleDB(
            host="postgres",
            port="1234",
            username="user",
            password="password"
        ),
        "binance": Binance(
            api_key="123456789",
            api_secret="abcdefghijklmn"
        ),
        "database": "binance"
    }


def test_config(monkeypatch: pytest.MonkeyPatch, environment: dict, assert_config: dict):
    for key in environment.keys():
        monkeypatch.setenv(key, environment[key])

    config = Config()

    for key in config.__dict__.keys():
        if type(config.__dict__[key]) in [TimescaleDB, Binance]:
            assert config.__dict__[key].__dict__ == assert_config[key].__dict__
        else:
            assert config.__dict__[key] == assert_config[key]
