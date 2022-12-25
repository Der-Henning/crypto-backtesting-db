from typing import Literal
from binance import Client
import numpy as np
import pandas as pd

columns = np.array([
    ('time', 'TIMESTAMPTZ PRIMARY KEY'),
    ('open', 'DOUBLE PRECISION'),
    ('low', 'DOUBLE PRECISION'),
    ('high', 'DOUBLE PRECISION'),
    ('close', 'DOUBLE PRECISION'),
    ('volume', 'DOUBLE PRECISION'),
    ('close_time', 'TIMESTAMP'),
    ('quote_asset_volume', 'DOUBLE PRECISION'),
    ('number_trades', 'INTEGER'),
    ('taker_buy_base_asset_volume', 'DOUBLE PRECISION'),
    ('taker_buy_quote_asset_volume', 'DOUBLE PRECISION')
])


class Binance():
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = Client(api_key, api_secret)

    def get_klines(self,
                   symbol: str,
                   startTime: str,
                   endTime: str = 'NOW',
                   interval: Literal = Client.KLINE_INTERVAL_1MINUTE
                   ) -> pd.DataFrame:
        klines = self.client.get_historical_klines(
            symbol, interval, startTime, endTime)
        data = np.array(klines)
        df = pd.DataFrame({
            'time': pd.to_datetime(data[:, 0], unit='ms'),
            'open': pd.to_numeric(data[:, 1]),
            'high': pd.to_numeric(data[:, 2]),
            'low': pd.to_numeric(data[:, 3]),
            'close': pd.to_numeric(data[:, 4]),
            'volume': pd.to_numeric(data[:, 5]),
            'close_time': pd.to_datetime(data[:, 6], unit='ms'),
            'quote_asset_volume': pd.to_numeric(data[:, 7]),
            'number_trades': pd.to_numeric(data[:, 8]),
            'taker_buy_base_asset_volume': pd.to_numeric(data[:, 9]),
            'taker_buy_quote_asset_volume': pd.to_numeric(data[:, 10])
        })
        return df
