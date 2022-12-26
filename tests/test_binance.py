from sources.binance import Binance, columns
from datetime import datetime, timedelta
import pandas as pd
import pytest


@pytest.fixture
def binance() -> Binance:
    return Binance()


def test_get_klines(binance):
    data = binance.get_klines('BTCUSDT', str(
        (datetime.now() - timedelta(hours=1)).date()))
    assert isinstance(data, pd.DataFrame)
    assert any(col in data.columns for col in columns[:, 0])
