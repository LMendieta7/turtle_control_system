from services.esp_status_monitor import EspStatusMonitor
from services.temperature_logger import TemperatureLogger
from mqtt.client import start_mqtt


esp_monitor = EspStatusMonitor(
    ip_key="esp_ip",
    status_key="esp_online",
    interval_s=5.0,
    timeout_ms=1000
)
temp_logger = TemperatureLogger(interval_s=1800)


def start_background_services():
    """Start MQTT and the app's background monitors."""
    start_mqtt()
    esp_monitor.start()
    temp_logger.start()
