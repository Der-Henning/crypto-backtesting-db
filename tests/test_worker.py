from datetime import datetime, timezone

from config import Config
from worker import Worker


def test_worker(config: Config, responses, binance_ping_response, binance_get_klines_response):
    config.timescaledb.createDatabase(config.database, True)

    # Test with subset
    config.start_time = "25.12.2022"
    config.end_time = "26.12.2022"
    worker = Worker(config)
    worker.run()

    assert len(responses.calls) == 4
    assert config.timescaledb.getFirstTimestamp(
        config.database, config.symbols[0]) == datetime(2022, 12, 25, tzinfo=timezone.utc)
    assert config.timescaledb.getLastTimestamp(
        config.database, config.symbols[0]) == datetime(2022, 12, 26, tzinfo=timezone.utc)

    # Use earlier start time and newer data
    config.start_time = "24.12.2022"
    config.end_time = "NOW"
    worker = Worker(config)
    worker.run()

    assert len(responses.calls) == 10
    assert config.timescaledb.getFirstTimestamp(
        config.database, config.symbols[0]) == datetime(2022, 12, 24, tzinfo=timezone.utc)
    assert config.timescaledb.getLastTimestamp(
        config.database, config.symbols[0]) == datetime(2022, 12, 26, 17, 38, tzinfo=timezone.utc)

    config.timescaledb.dropDatabase(config.database)
