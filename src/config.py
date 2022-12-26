from os import environ
import json
from sinks import TimescaleDB
from sources import Binance


class Config():
    def __init__(self):
        self.debug: bool = True if environ.get(
            "DEBUG", "").lower() in ('true', '1', 't') else False
        self.symbols: list[str] = json.loads(environ.get("SYMBOLS", "[]"))
        self.start_time: str = environ.get("START_DATE", "")
        self.sleep_time: int = int(environ.get("SLEEP_TIME", 60))
        self.timescaledb: TimescaleDB = TimescaleDB(
            host=environ.get("TIMESCALE_HOST", "localhost"),
            port=environ.get("TIMESCALE_PORT", 5432),
            username=environ.get("TIMESCALE_USERNAME", "postgres"),
            password=environ.get("TIMESCALE_PASSWORD", "postgres")
        )
        self.binance: Binance = Binance(
            api_key=environ.get("BINANCE_API_KEY", None),
            api_secret=environ.get("BINANCE_API_SECRET", None)
        )
        self.database: str = "binance"
