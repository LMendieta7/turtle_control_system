import paho.mqtt.client as mqtt
import time

# Global variables for sensor data
sensor_data = {
    "basking_temperature": 0,
    "water_temperature": 0, 
    "light_status": "OFF", 
    "feeder_state": "IDLE", 
    "auto_mode": "on",
    "feed_count": 0,
    "esp_ip": "N/A",
    "heap": "N/A",
    "mqtt_status": "disconnected",
    "esp_uptime_ms": 0
}

# Timestamps to track when each value was last updated
sensor_timestamps = {

    "mqtt_status": 0,
    "esp_uptime_ms": 0,
    "basking_temperature": 0,
    "water_temperature": 0,
}

# Reset sensor values if stale
def reset_stale_sensor_data(timeout=10):
    now = time.time()
    for key, ts in sensor_timestamps.items():
        if now - ts > timeout:
            if key == "mqtt_status":
                sensor_data["mqtt_status"] = "disconnected"
            elif key == "esp_uptime_ms":
                sensor_data["esp_uptime_ms"] = 0
            elif key == "basking_temperature":
                sensor_data["basking_temperature"] = 0
            elif key == "water_temperature":
                sensor_data["water_temperature"] = 0

# MQTT callback functions
def on_connect(client, userdata, flags, rc, properties):
    print(f"Connected with result code {rc}")
    client.subscribe("turtle/basking_temperature")  # Subscribe to basking temp
    client.subscribe("turtle/water_temperature")    # Subscribe to water temp
    client.subscribe("turtle/lights_state")  
    client.subscribe("turtle/feeder_state")
    client.subscribe("turtle/auto_mode_state")
    client.subscribe("turtle/feed_count")
    client.subscribe("turtle/mqtt_status")
    client.subscribe("turtle/heap")
    client.subscribe("turtle/esp_ip")
    client.subscribe("turtle/esp_uptime_ms")


def on_message(client, userdata, msg):
    global sensor_data, sensor_timestamps
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        now = time.time()

        if topic == "turtle/basking_temperature":
            sensor_data["basking_temperature"] = float(payload)
            sensor_timestamps["basking_temperature"] = now
        elif topic == "turtle/water_temperature":
            sensor_data["water_temperature"] = float(payload)
            sensor_timestamps["water_temperature"] = now
        elif topic == "turtle/lights_state":
            sensor_data["light_status"] = payload
            #sensor_timestamps["light_status"] = now
        elif topic == "turtle/feeder_state":
            sensor_data["feeder_state"] = payload
            #sensor_timestamps["feeder_state"] = now
        elif topic == "turtle/auto_mode_state":
            sensor_data["auto_mode"] = payload
            #sensor_timestamps["auto_mode"] = now
        elif topic == "turtle/feed_count":
            sensor_data["feed_count"] = int(payload)
           # sensor_timestamps["feed_count"] = now
        elif topic == "turtle/esp_ip":
            sensor_data["esp_ip"] = payload
            #sensor_timestamps["esp_ip"] = now
        elif topic == "turtle/heap":
            sensor_data["heap"] = payload
            #sensor_timestamps["heap"] = now
        elif topic == "turtle/mqtt_status":
            sensor_data["mqtt_status"] = payload
            sensor_timestamps["mqtt_status"] = now
        elif topic == "turtle/esp_uptime_ms":
            sensor_data["esp_uptime_ms"] = int(payload)
            sensor_timestamps["esp_uptime_ms"] = now


    except ValueError:
        print(f"Invalid value received on {msg.topic}")

# MQTT Client setup
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to MQTT broker
mqtt_client.connect("172.22.80.5", 1883, 60)
mqtt_client.loop_start()