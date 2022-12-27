import pandas as pd
from sinks.timescaledb import TimescaleDB


def test_database(timescaledb: TimescaleDB, database: str, symbol: str, test_dataframe: pd.DataFrame):
    timescaledb.dropDatabase(database)

    timescaledb.createDatabase(database)
    timescaledb.createDatabase(database, False)
    timescaledb.createDatabase(database, True)

    timescaledb.createTable(database, symbol, False)
    timescaledb.createTable(database, symbol, False)
    timescaledb.createTable(database, symbol, True)
    timescaledb.dropTable(database, symbol)
    timescaledb.createTable(database, symbol, False)

    timescaledb.write(database, symbol, test_dataframe)
    first_ts = timescaledb.getFirstTimestamp(database, symbol)
    assert pd.Timestamp(test_dataframe['time'].values[0]).tz_localize(
        'UTC') == pd.to_datetime(first_ts)

    last_ts = timescaledb.getLastTimestamp(database, symbol)
    assert pd.Timestamp(test_dataframe['time'].values[-1]
                        ).tz_localize('UTC') == pd.to_datetime(last_ts)

    timescaledb.deleteLastTimestamp(database, symbol)
    last_ts = timescaledb.getLastTimestamp(database, symbol)
    assert pd.Timestamp(test_dataframe['time'].values[-2]
                        ).tz_localize('UTC') == pd.to_datetime(last_ts)

    timescaledb.dropDatabase(database)
