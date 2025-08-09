import sqlite3

class Database:
    def __init__(self, path="turtle.db"):
        self.path = path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.path)
    
    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS temperature_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    basking_temp REAL NOT NULL,
                    water_temp REAL NOT NULL
                )
            """)
            conn.commit()
      
    def insert_temperature(self, basking_temp, water_temp, timestamp):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO temperature_log (timestamp, basking_temp, water_temp)
                VALUES (?, ?, ?)""", 
                (timestamp, basking_temp, water_temp)
            )
            conn.commit()
            
        
            
        
























# DB_FILE = "turtle.db"

# def init_db():
#     """Create the SQLite database and the temperature_log table if not exists."""
#     conn = sqlite3.connect(DB_FILE)
#     c = conn.cursor()
#     c.execute("""
#         CREATE TABLE IF NOT EXISTS temperature_log (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             timestamp TEXT NOT NULL,
#             basking_temp REAL NOT NULL,
#             water_temp REAL NOT NULL
#         )
#     """)
#     conn.commit()
#     conn.close()

# def insert_temperature(basking_temp, water_temp, timestamp):
#     """Insert a temperature record into the database."""
#     conn = sqlite3.connect(DB_FILE)
#     c = conn.cursor()
#     c.execute("""
#         INSERT INTO temperature_log (timestamp, basking_temp, water_temp)
#         VALUES (?, ?, ?)
#     """, (timestamp, basking_temp, water_temp))
#     conn.commit()
#     conn.close()
