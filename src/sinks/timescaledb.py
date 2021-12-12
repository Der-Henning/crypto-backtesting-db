import psycopg2
from pgcopy import CopyManager
from sources import binanceColumns

class TimescaleDB():
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connStr = "postgres://{}:{}@{}:{}/".format(self.username, self.password, self.host, self.port)

    def createDatabase(self, name, clear=False):
        # try:
        #     connection = psycopg2.connect(self.connStr,)
        #     connection.autocommit = True
        #     cursor = connection.cursor()
            
        #     if clear:
        #         cursor.execute("DROP DATABASE {}".format(name.lower()))
        #     cursor.execute("CREATE DATABASE {}".format(name.lower()))
        #     cursor.close()
        # finally:
        #     if connection:
        #         connection.close()


        with psycopg2.connect(self.connStr) as conn:
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            conn.autocommit = True
            cursor = conn.cursor()
            if clear:
                cursor.execute("DROP DATABASE {}".format(name.lower()))
            cursor.execute("CREATE DATABASE {}".format(name.lower()))
            #conn.commit()
            cursor.close()

    def createTable(self, database, symbol, clear=False):
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            cursor = conn.cursor()
            if clear: 
                cursor.execute("DROP TABLE {}".format(symbol.lower()))
            query_create_table = "CREATE TABLE IF NOT EXISTS {} ({})".format(
                symbol.lower(),
                (', '.join("{} {}".format(row[0], row[1]) for row in binanceColumns))
            )
            query_create_hypertable = "SELECT create_hypertable('{}', '{}')".format(
                symbol.lower(),
                binanceColumns[0][0]
            )
            cursor.execute(query_create_table)
            cursor.execute(query_create_hypertable)
            conn.commit()
            cursor.close()

    def write(self, database, symbol, df):
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            mgr = CopyManager(conn, symbol.lower(), df.columns)
            self.deleteLastTimestamp(database, symbol)
            mgr.copy(df.to_numpy())
            conn.commit()

    def deleteLastTimestamp(self, database, symbol):
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            ts = self.getLastTimestamp(database, symbol)
            if ts:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM {} WHERE time='{}'".format(symbol.lower(), ts))
                conn.commit()
                cursor.close()

    def getLastTimestamp(self, database, symbol):
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT time FROM {} ORDER BY time DESC LIMIT 1".format(symbol.lower()))
            response = cursor.fetchone()
            ts = None
            if response:
                ts = response[0]
            cursor.close()
            return ts
            
    def getFirstTimestamp(self, database, symbol):
        with psycopg2.connect("{}{}".format(self.connStr, database.lower())) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT time FROM {} ORDER BY time ASC LIMIT 1".format(symbol.lower()))
            response = cursor.fetchone()
            ts = None
            if response:
                ts = response[0]
            cursor.close()
            return ts
            