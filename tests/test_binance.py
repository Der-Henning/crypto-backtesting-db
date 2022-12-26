from sources.binance import Binance, columns
import pandas as pd
import pytest
import pickle


@pytest.fixture
def binance() -> Binance:
    return Binance()


@pytest.fixture
def test_data():
    with open('tests/test_data.pkl', 'rb') as file:
        data = pickle.load(file)
    return data


def test_make_dataframe(binance: Binance, test_data: list):
    df = binance.make_dataframe(test_data)
    assert isinstance(df, pd.DataFrame)
    assert any(col in df.columns for col in columns[:, 0])
