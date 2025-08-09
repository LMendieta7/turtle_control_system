import threading
import time
from datetime import datetime
from mqtt.client import basking_sensor, water_sensor
from services.db.database import Database

db = Database()


class TemperatureLogger:
    def __init__(self, interval_s=1800):
        self.interval = interval_s
        self.running = False
        self._thread = None

    def _log_once(self):
        bask = basking_sensor.get(timeout=10, fallback_on_stale=True)
        water = water_sensor.get(timeout=10, fallback_on_stale=True)

        if bask != 0 and water != 0:
            db.insert_temperature(
                bask,
                water,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            print(f"[TempLogger] Skipped: stale or missing value — Basking={bask}, Water={water}")

    def _run(self):

        print("[TempLogger] Waiting for valid sensor readings...")
        # Wait until both sensors have valid (non-default) values
        while True:
            bask = basking_sensor.get(timeout=10, fallback_on_stale=True)
            water = water_sensor.get(timeout=10, fallback_on_stale=True)
            if bask != 0 and water != 0:
                print(f"[TempLogger] Initial values OK — Basking={bask}, Water={water}")
                break
            print(f"[TempLogger] Waiting for valid readings... Basking={bask}, Water={water}")
            time.sleep(5)

        while self.running:
            self._log_once()
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self.running = False
