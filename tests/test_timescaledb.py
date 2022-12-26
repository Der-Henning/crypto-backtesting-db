import pandas as pd
from sinks.timescaledb import TimescaleDB


def test_database(timescaleDB: TimescaleDB, database: str, symbol: str, test_dataframe: pd.DataFrame):
    timescaleDB.dropDatabase(database)

    timescaleDB.createDatabase(database)
    timescaleDB.createDatabase(database, False)
    timescaleDB.createDatabase(database, True)

    timescaleDB.createTable(database, symbol, False)
    timescaleDB.createTable(database, symbol, False)
    timescaleDB.createTable(database, symbol, True)
    timescaleDB.dropTable(database, symbol)
    timescaleDB.createTable(database, symbol, False)

    timescaleDB.write(database, symbol, test_dataframe)
    first_ts = timescaleDB.getFirstTimestamp(database, symbol)
    assert pd.Timestamp(test_dataframe['time'].values[0]).tz_localize(
        'UTC') == pd.to_datetime(first_ts)

    last_ts = timescaleDB.getLastTimestamp(database, symbol)
    assert pd.Timestamp(test_dataframe['time'].values[-1]
                        ).tz_localize('UTC') == pd.to_datetime(last_ts)

    timescaleDB.deleteLastTimestamp(database, symbol)
    last_ts = timescaleDB.getLastTimestamp(database, symbol)
    assert pd.Timestamp(test_dataframe['time'].values[-2]
                        ).tz_localize('UTC') == pd.to_datetime(last_ts)

    timescaleDB.dropDatabase(database)
