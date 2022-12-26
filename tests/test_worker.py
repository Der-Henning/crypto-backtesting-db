from typing import Generator
import pandas as pd
from worker import Worker
from config import Config
from sources import Binance


class OfflineBinance(Binance):
    def __init__(self, data: pd.DataFrame, api_key: str = None, api_secret: str = None):
        super().__init__(api_key, api_secret)
        self._data = data
        self._data_generator = self._make_data_generator()
        self._next_data = next(self._data_generator, None)
        self._has_next = True

    def _make_data_generator(self) -> Generator[pd.DataFrame, None, None]:
        chunk_size = 100
        pos = 0
        while pos < len(self._data):
            yield self._data.iloc[pos:pos+chunk_size]
            pos = pos + chunk_size

    def get_klines(self, symbol: str, startTime: str, endTime: str = 'NOW', interval: str = '1m') -> pd.DataFrame:
        data = self._next_data
        self._next_data = next(self._data_generator, None)
        if self._next_data is None:
            self._has_next = False
        return data


def test_worker(config: Config):
    df = pd.read_pickle('tests/test_dataframe.pkl')

    config.timescaledb.createDatabase(config.database)

    # Test with subset
    config.start_time = "25.12.2021"
    config.binance = OfflineBinance(data=df[df['time'].dt.day == 25])
    worker = Worker(config)
    while config.binance._has_next:
        worker.run()

    # Use earlier start time and newer data
    config.start_time = "24.12.2021"
    config.binance = OfflineBinance(data=df)
    worker = Worker(config)
    while config.binance._has_next:
        worker.run()

    config.timescaledb.dropDatabase(config.database)
