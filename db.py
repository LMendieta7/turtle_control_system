import sqlite3

DB_FILE = "turtle.db"

def init_db():
    """Create the SQLite database and the temperature_log table if not exists."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS temperature_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            basking_temp REAL NOT NULL,
            water_temp REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def insert_temperature(basking_temp, water_temp, timestamp):
    """Insert a temperature record into the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO temperature_log (timestamp, basking_temp, water_temp)
        VALUES (?, ?, ?)
    """, (timestamp, basking_temp, water_temp))
    conn.commit()
    conn.close()
