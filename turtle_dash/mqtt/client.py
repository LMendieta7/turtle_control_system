# mqtt_client.py

import time
import threading
import paho.mqtt.client as mqtt
from mqtt.sensors import Sensor
from mqtt.status_manager import status, StatusManager
from mqtt.topics import TOPICS

# ————————————————————————————————
# 1) Your sensors and status manager
basking_sensor = Sensor("Basking", default=0, valid_range=(40, 130))
water_sensor  = Sensor("Water",  default=0, valid_range=(40, 130))

# ————————————————————————————————
# 2) MQTT callbacks

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected (rc={rc})")
    status.update_status("mqtt_status", "connected")
    for topic in TOPICS:
        client.subscribe(topic)

def on_message(client, userdata, msg):
    try:
        # every message is a heartbeat
        status.update_status("mqtt_status", "connected")

        topic, payload = msg.topic, msg.payload.decode()

        if topic == "turtle/sensors/temp/basking":
            basking_sensor.update(float(payload))
            return
        if topic == "turtle/sensors/temp/water":
            water_sensor.update(float(payload))
            return

        # Simple mapping for everything else (new topics → existing keys)
        mapping = {
            # Lights
            "turtle/lights/status":          ("light_status", str),
            "turtle/lights/heat/status":     ("heat_bulb_status", str),
            "turtle/lights/uv/status":       ("uv_bulb_status", str),

            # Feeder
            "turtle/feeder/state":           ("feeder_state", str),
            "turtle/feeder/count":           ("feed_count", int),

            # Auto mode
            "turtle/auto_mode/status":       ("auto_mode", str),

            # ESP / health
            "turtle/esp/ip":                 ("esp_ip", str),
            "turtle/esp/heap":               ("heap", int),
            "turtle/esp/uptime_ms":          ("esp_uptime_ms", int),
            "turtle/esp/mqtt":               ("esp_mqtt", str),

            # Currents (new paths)
            "turtle/sensors/current/heat":   ("heat_bulb_current", float),
            "turtle/sensors/current/uv":     ("uv_bulb_current", float),
            "turtle/sensors/current/heat/status":   ("heat_bulb_current_status", str),
            "turtle/sensors/current/uv/status":     ("uv_bulb_current_status", str),
        }

        entry = mapping.get(topic)
        if entry:
            key, caster = entry
            try:
                val = caster(payload)
            except Exception:
                # fall back to raw if cast fails
                val = payload
            status.update_status(key, val)

    except Exception as e:
        # Log and swallow any errors so the thread never dies
        print(f"[MQTT:on_message] Error parsing {msg.topic}: {e}")

def on_disconnect(client, userdata, *args):
    """
    Called whenever the MQTT client loses its connection.
    We don’t care what extra parameters Paho passes—just mark us disconnected.
    """
    status.update_status("mqtt_status", "disconnected")
    print("[MQTT] Disconnected")

# ————————————————————————————————
# 3) Create and configure the client

mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect    = on_connect
mqtt_client.on_message    = on_message
mqtt_client.on_disconnect = on_disconnect

# Tell Paho to auto-reconnect with backoff (1s → 120s)
mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

def start_mqtt():
    def _connect():
        while True:
            try:
                mqtt_client.connect_async("172.22.80.5", 1883, 60)
                mqtt_client.loop_start()
                break
            except Exception as e:
                print(f"[MQTT] Initial connect failed: {e} — retrying in 5s")
                time.sleep(5)

    threading.Thread(target=_connect, daemon=True).start()

