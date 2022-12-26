from typing import Union
import logging
import pandas as pd
import psycopg2
from psycopg2.errors import DuplicateDatabase, InvalidCatalogName, UndefinedTable, DatabaseError
from pgcopy import CopyManager
from sources import binanceColumns

log = logging.getLogger("cryptoDB")
class TimescaleDB():
    def __init__(self, host: str, port: Union[str, int], username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connStr = "postgres://{}:{}@{}:{}/".format(
            self.username, self.password, self.host, self.port)

    def createDatabase(self, name: str, clear: bool = False) -> None:
        if clear:
            self.dropDatabase(name)
        try:
            connection = psycopg2.connect(self.connStr)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("CREATE DATABASE {}".format(name.lower()))
        except DuplicateDatabase as err:
            log.debug(err)
        finally:
            if connection:
                connection.close()

    def dropDatabase(self, name: str) -> None:
        try:
            connection = psycopg2.connect(self.connStr)
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute("DROP DATABASE {}".format(name.lower()))
        except InvalidCatalogName as err:
            log.debug(err)
        finally:
            if connection:
                connection.close()

    def createTable(self, database: str, symbol: str, clear: bool = False) -> None:
        if clear:
            self.dropTable(database, symbol)
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            with conn.cursor() as cursor:
                try:
                    query_create_table = "CREATE TABLE IF NOT EXISTS {} ({})".format(
                        symbol.lower(),
                        (', '.join("{} {}".format(row[0], row[1])
                        for row in binanceColumns))
                    )
                    query_create_hypertable = "SELECT create_hypertable('{}', '{}')".format(
                        symbol.lower(),
                        binanceColumns[0][0]
                    )
                    cursor.execute(query_create_table)
                    cursor.execute(query_create_hypertable)
                except DatabaseError as err:
                    log.debug(err)

    def dropTable(self, database: str, symbol: str) -> None:
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("DROP TABLE {}".format(symbol.lower()))
                except UndefinedTable as err:
                    log.debug(err)

    def write(self, database: str, symbol: str, df: pd.DataFrame) -> None:
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            mgr = CopyManager(conn, symbol.lower(), df.columns)
            self.deleteLastTimestamp(database, symbol)
            mgr.copy(df.to_numpy())
            conn.commit()

    def deleteLastTimestamp(self, database: str, symbol: str) -> None:
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            ts = self.getLastTimestamp(database, symbol)
            if ts:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM {} WHERE time='{}'".format(symbol.lower(), ts))
                conn.commit()
                cursor.close()

    def getLastTimestamp(self, database: str, symbol: str) -> Union[str, None]:
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT time FROM {} ORDER BY time DESC LIMIT 1".format(symbol.lower()))
            response = cursor.fetchone()
            ts = None
            if response:
                ts = response[0]
            cursor.close()
            return ts

    def getFirstTimestamp(self, database: str, symbol: str) -> Union[str, None]:
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT time FROM {} ORDER BY time ASC LIMIT 1".format(symbol.lower()))
            response = cursor.fetchone()
            ts = None
            if response:
                ts = response[0]
            cursor.close()
            return ts
