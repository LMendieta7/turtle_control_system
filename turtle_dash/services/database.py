import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "turtle.db"


class Database:
    def __init__(self, path=DEFAULT_DB_PATH):
        self.path = Path(path)
        self._create_tables()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _create_tables(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS temperature_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    basking_temp REAL NOT NULL,
                    water_temp REAL NOT NULL
                )
                """
            )

    def insert_temperature(self, basking_temp, water_temp, timestamp):
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO temperature_log (timestamp, basking_temp, water_temp)
                VALUES (?, ?, ?)
                """,
                (timestamp, basking_temp, water_temp),
            )

    def get_todays_temperatures(self):
        with self._connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM temperature_log
                WHERE DATE(timestamp) = DATE('now', 'localtime')
                """
            ).fetchall()
