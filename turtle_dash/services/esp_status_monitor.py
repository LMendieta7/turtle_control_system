import threading
import time
from utils.network import esp_ping
from mqtt.status_manager import status


class EspStatusMonitor:
    """
    Background monitor that periodically pings the ESP and updates
    the server-side status flag in StatusManager.
    """

    def __init__(
        self,
        ip_key: str = "esp_ip",
        status_key: str = "esp_online",
        interval_s: float = 4.0,
        timeout_ms: int = 500
    ):
        self.ip_key = ip_key
        self.status_key = status_key
        self.interval = interval_s
        self.timeout_ms = timeout_ms
        self.running = False
        self._thread = None

    def _run(self):
        while self.running:
            esp_ip = status.get_status(self.ip_key, default="172.22.80.58")

            alive = esp_ping(esp_ip, timeout_ms=self.timeout_ms) if esp_ip else False
            status.update_status(self.status_key, alive)

            time.sleep(self.interval)

    def start(self):
        """Starts the background ping monitor thread."""
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        """Stops the background thread loop."""
        self.running = False