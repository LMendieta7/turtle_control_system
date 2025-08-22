from services.esp_status_monitor import EspStatusMonitor
from services.temperature_logger import TemperatureLogger

# Future: from monitors.sensor_alert_monitor import SensorAlertMonitor

# Create instance of your ESP connectivity monitor
esp_monitor = EspStatusMonitor(
    ip_key="esp_ip",
    status_key="esp_online",
    interval_s=5.0,
    timeout_ms=1000
)

# create instance of temperature logger

temp_logger = TemperatureLogger(interval_s=1800)

def start_esp_monitor():
    """Start the ESP ping monitor in a background thread."""
    print("[MONITORING] Starting ESP monitor...")
    esp_monitor.start()

def start_temperature_logger():
    print("Temperature logger started")
    temp_logger.start()

def start_all_monitors():
    """Start all background monitoring threads."""
    start_esp_monitor()

    # Future: start_sensor_monitor()
    start_temperature_logger()
