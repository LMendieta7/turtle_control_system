import threading
import time
from utils.network import esp_ping
from mqtt_client import status

class EspStatusMonitor:
    """
    Background monitor that periodically pings the ESP and updates
    the server-side status flag in StatusManager.

    Attributes:
        ip_key (str): StatusManager key where the ESP publishes its IP.
        status_key (str): StatusManager key for recording online/offline.
        interval (float): Seconds between pings.
        timeout_ms (int): Ping timeout in milliseconds.
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

        # Start the background thread
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        while True:
            # 1) Retrieve the last known ESP IP
            esp_ip = status.get_status(self.ip_key, default='172.22.80.58')

            # 2) Ping if we have an IP, else mark offline
            if esp_ip:
                alive = esp_ping(esp_ip, timeout_ms=self.timeout_ms)
            else:
                alive = False

            # 3) Update StatusManager
            status.update_status(self.status_key, alive)

            # 4) Wait until next ping cycle
            time.sleep(self.interval)
