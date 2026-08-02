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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS feeding_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'controller'
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

    def get_recent_temperatures(self, days=7):
        with self._connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM temperature_log
                WHERE timestamp >= DATETIME('now', 'localtime', ?)
                ORDER BY timestamp ASC
                """,
                (f"-{int(days)} days",),
            ).fetchall()

    def insert_feeding_event(self, timestamp, source="controller"):
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO feeding_log (timestamp, source)
                VALUES (?, ?)
                """,
                (timestamp, source),
            )

    def get_recent_feeding_events(self, days=30):
        with self._connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM feeding_log
                WHERE timestamp >= DATETIME('now', 'localtime', ?)
                ORDER BY timestamp ASC
                """,
                (f"-{int(days)} days",),
            ).fetchall()
