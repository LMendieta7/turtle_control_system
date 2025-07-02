import dash
from dash import dcc, html
from navbar import navbar
from db import init_db, insert_temperature
import threading
import time
from datetime import datetime
from mqtt_client import sensor_data

# Initialize the database (creates table if needed)
init_db()

external_stylesheets = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
]

app = dash.Dash(__name__, use_pages=True, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([
    dcc.Location(id="url"),
    navbar,
    dash.page_container
])

def log_temperature():
    while True:
        bask = sensor_data["basking_temperature"]
        water = sensor_data["water_temperature"]

        # Only log if values look like real Fahrenheit temps
        if 40 < bask < 130 and 40 < water < 130:
            insert_temperature(
                bask,
                water,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        else:
            print(f"Skipped logging: Sensor value not valid (Basking: {bask}, Water: {water})")
        time.sleep(1800)  # or 1800 for 30min

def wait_for_valid_sensor_data():
    while True:
        bask = sensor_data["basking_temperature"]
        water = sensor_data["water_temperature"]
        if 40 < bask < 130 and 40 < water < 130:
            print(f"Found valid sensor data: Basking={bask} Water={water}")
            break
        print(f"Waiting for valid sensor data... (Basking={bask}, Water={water})")
        time.sleep(2)  # Check every 2 seconds

# Call this before starting the logging thread
wait_for_valid_sensor_data()


threading.Thread(target=log_temperature, daemon=True).start()

if __name__ == '__main__':
    app.run(debug =True, host='0.0.0.0', port=8050)