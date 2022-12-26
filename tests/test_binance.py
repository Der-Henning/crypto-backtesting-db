from sources.binance import Binance, columns
import pandas as pd


def test_make_dataframe(binance: Binance, test_data: list):
    df = binance.make_dataframe(test_data)
    assert isinstance(df, pd.DataFrame)
    assert any(col in df.columns for col in columns[:, 0])
