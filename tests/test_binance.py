from sources.binance import Binance, columns
import pandas as pd


def test_make_dataframe(binance: Binance, test_data: list):
    df = binance.make_dataframe(test_data)
    assert isinstance(df, pd.DataFrame)
    assert any(col in df.columns for col in columns[:, 0])


def test_binance_ping(binance: Binance, responses, binance_ping_response):
    binance.client.ping()
    assert len(responses.calls) == 2


def test_binance_get_klines(binance: Binance, symbol: str, test_dataframe: pd.DataFrame, responses, binance_ping_response, binance_get_klines_response):
    df = binance.get_klines(symbol, '24.12.2022')
    assert len(responses.calls) == 6
    assert df.equals(test_dataframe)
