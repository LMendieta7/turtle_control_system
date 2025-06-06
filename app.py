import dash
from dash import dcc, html, callback_context
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
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
    "mqtt_status": "disconnected"
}

# Timestamps to track when each value was last updated
sensor_timestamps = {
    "basking_temperature": 0,
    "water_temperature": 0,
    "light_status": 0,
    "feeder_state": 0,
    "auto_mode": 0,
    "feed_count": 0,
    "esp_ip": 0,
    "heap": 0,
    "mqtt_status": 0
}

# Reset sensor values if stale
def reset_stale_sensor_data(timeout=10):
    now = time.time()
    for key, ts in sensor_timestamps.items():
        if now - ts > timeout:
            if key in ["basking_temperature", "water_temperature", "feed_count"]:
                sensor_data[key] = 0
            elif key in ["esp_ip", "heap"]:
                sensor_data[key] = "N/A"
            else:
                sensor_data[key] = "disconnected"


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
            sensor_timestamps["light_status"] = now
        elif topic == "turtle/feeder_state":
            sensor_data["feeder_state"] = payload
            sensor_timestamps["feeder_state"] = now
        elif topic == "turtle/auto_mode_state":
            sensor_data["auto_mode"] = payload
            sensor_timestamps["auto_mode"] = now
        elif topic == "turtle/feed_count":
            sensor_data["feed_count"] = int(payload)
            sensor_timestamps["feed_count"] = now
        elif topic == "turtle/esp_ip":
            sensor_data["esp_ip"] = payload
            sensor_timestamps["esp_ip"] = now
        elif topic == "turtle/heap":
            sensor_data["heap"] = payload
            sensor_timestamps["heap"] = now
        elif topic == "turtle/mqtt_status":
            sensor_data["mqtt_status"] = payload
            sensor_timestamps["mqtt_status"] = now


    except ValueError:
        print(f"Invalid value received on {msg.topic}")

# MQTT Client setup
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to MQTT broker
mqtt_client.connect("10.0.0.130", 1883, 60)
mqtt_client.loop_start()

# Initialize Dash app
app = dash.Dash(__name__)
app.layout = html.Div([

    html.Div([
        html.Div(id='mqtt-status')    #  Style now handled in style.css
    ], style={'position': 'relative'}),


    html.H1("Turtle Control System", style={'text-align': 'center'}),
    
    # Basking Temperature Gauge
    dcc.Graph(id='basking-gauge', config={'displayModeBar': False}, style={'width': '100%','margin': '10px'}),
    
    # Water Temperature Gauge
    dcc.Graph(id='water-gauge', config={'displayModeBar': False},  style={'width': '100%', 'margin': '10px'}),
    
        # Control Buttons
    html.Div([
        html.Button('Feed Turtle', id='feed-btn', n_clicks=0, style={'margin': '12px', 'padding': '12px'}),
        
        html.Button('Turn Light ON', id='light-btn', n_clicks=0, style={'margin': '12px', 'padding': '12px'})
    ], style={'text-align': 'center'}),


     # Auto Mode Toggle Button (new)
    html.Div([
        html.Button("Auto On", id="auto-toggle-btn", n_clicks=0, style={
    'border-radius': '50%',
    'padding': '17px 22px',
    'font-size': '14px',
    'border': 'none',
    'cursor': 'pointer',
    'color': 'white',
    'backgroundColor': 'blue'  # neutral default (will get overwritten)
    }),
    
    html.Div(id='feed-count-display', style={'fontSize': '16px', 'marginTop': '4px'}),
    html.Div(id="auto-status", style={"marginTop": "10px", "color": "#333"})
    ], style={'text-align': 'center', 'marginTop': '20px'}),

    # Store for auto mode status
    dcc.Store(id='auto-mode-store', data=True),  # True means Auto Mode is enabled

    # Interval for updating gauges
    dcc.Interval(id='interval-update', interval=2000, n_intervals=0),
    
    # Hidden store to remember light status
    dcc.Store(id='light-status-store', data='OFF'),
    dcc.Store(id='feeder-state-store', data='IDLE'),
    dcc.Store(id='auto-mode-state-store', data='on')

])

@app.callback(
    Output('mqtt-status', 'children'),
    Input('interval-update', 'n_intervals')
)

def update_status_display(n):
        
    reset_stale_sensor_data(timeout=10)

    esp_status = sensor_data.get("mqtt_status", "disconnected")
    esp_ip = sensor_data.get("esp_ip", "N/A")
    heap = sensor_data.get("heap", "N/A")

    esp_color = "green" if esp_status == "connected" else "gray"
    
    return html.Div([
        html.Span("ESP Status: ", style={"fontWeight": "bold"}),
        html.Span(style={
            "display": "inline-block",
            "width": "10px",
            "height": "10px",
            "borderRadius": "50%",
            "backgroundColor": esp_color,
            "marginRight": "5px"
        }, title="ESP status"),
        html.Span("ESP IP: ", style={"fontWeight": "bold"}),
        html.Span(esp_ip),
        html.Br(),
        html.Span("Free RAM: ", style={"fontWeight": "bold"}),
        html.Span(heap)
    ])

# Callbacks to update the temperature gauges
@app.callback(
    [Output('basking-gauge', 'figure'),
     Output('water-gauge', 'figure')],
     Input('interval-update', 'n_intervals')
)
def update_gauges(n):
    global sensor_data
    
    basking_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sensor_data["basking_temperature"],
        title={'text': "Basking Temp", 'font': {'size': 24}},
        gauge={'axis': {'range': [45, 105], 'tickvals': list(range(0, 111, 10)),}, 'bar': {'color': "red"}},
        number={'suffix': "°F"}  # Append °F after the value
    ))
    
    water_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sensor_data["water_temperature"],
        title={'text': "Water Temp", 'font': {'size': 24}},
        gauge={'axis': {'range': [45, 105], 'tickvals': list(range(0, 111, 10)), }, 'bar': {'color': "blue"}},
        number={'suffix': "°F"}  # Append °F after the value
    ))
    
    return basking_fig, water_fig

# Publish feed command
@app.callback(
    Output('feed-btn', 'n_clicks'),
    Input('feed-btn', 'n_clicks'),
    State('auto-mode-store', 'data'),  # Get the current auto mode state
    prevent_initial_call=True
)

def feed_turtle(n_clicks, auto_mode):
    if auto_mode:  # Check if auto mode is enabled
        print("Auto Mode is ON, feeding is disabled.")
        return 0  # Don't allow feeding
    elif n_clicks > 0:
        mqtt_client.publish("turtle/feed", "1")  # Publish feeding message
        return 0  # Reset button state
    return n_clicks

@app.callback(
    [Output('feed-btn', 'children'),
     Output('feed-btn', 'style')],
    Input('feeder-state-store', 'data')
)

def update_feed_button(state):
    is_running = state == "RUNNING"
    label = "Feeding..." if is_running else "Feed Turtle"
    color = "green" if is_running else "gray"

    return label, {
        'backgroundColor': color,
        'color': 'white',
        'margin': '8px',
        'padding': '10px 16px',
        'fontSize': '14px',
        'border': 'none',
        'borderRadius': '8px',
        'width': '110px'
    }


# Toggle lights
@app.callback(
    Output('light-btn', 'n_clicks'),
    Input('light-btn', 'n_clicks'),
    State('auto-mode-store', 'data'),
    State('light-status-store', 'data'),
    prevent_initial_call=True
)

def handle_light_toggle(n_clicks, auto_mode, current_status):
    if auto_mode:
        print("Auto Mode is ON — manual toggle disabled.")
        return 0
    new_status = "OFF" if current_status == "ON" else "ON"
    mqtt_client.publish("turtle/lights", new_status)
    return 0

# Update light status store
@app.callback(
    Output('light-status-store', 'data'),
    Input('interval-update', 'n_intervals')
)

def update_light_status(n):
    return sensor_data.get("light_status", "OFF")

# Update light button
@app.callback(
    [Output('light-btn', 'children'),
     Output('light-btn', 'style')],
    Input('light-status-store', 'data')
)
def update_light_button(current_status):
    is_on = current_status == "ON"
    label = "Lights ON" if is_on else "Lights OFF"
    color = "#FFD966" if is_on else "gray"
    label_color = "black" if is_on else "white"
    return label, {
        'margin': '8px',
        'padding': '10px 16px',
        'backgroundColor': color,
        'color': label_color,
        'fontSize': '14px',
        'border': 'none',
        'borderRadius': '8px',
        'width': '110px'
        
    }

# Unified auto mode button
@app.callback(
    [Output('auto-toggle-btn', 'style'),
     Output('auto-toggle-btn', 'children'),
     Output('auto-mode-store', 'data')],
    [Input('auto-toggle-btn', 'n_clicks'),
     Input('interval-update', 'n_intervals')],
    [State('auto-mode-store', 'data')],
    prevent_initial_call=True
)
def sync_auto_mode(n_clicks, _, current_mode):
    triggered = callback_context.triggered[0]['prop_id'].split('.')[0]

    if triggered == "auto-toggle-btn":
        new_mode = not current_mode
        mqtt_client.publish("turtle/auto_mode", "on" if new_mode else "off")
    else:
        new_mode = sensor_data.get("auto_mode", "off") == "on"

    label = "Auto On" if new_mode else "Auto Off"
    color = "blue" if new_mode else "gray"
    return {
        'border-radius': '50%',
        'padding': '17px 22px',
        'font-size': '14px',
        'border': 'none',
        'cursor': 'pointer',
        'backgroundColor': color,
        'color': 'white'
    }, label, new_mode

# Store updates

@app.callback(
    Output('feed-count-display', 'children'),
    Input('interval-update', 'n_intervals')
)
def update_feed_count_display(n):
    return f"Feed: {sensor_data.get('feed_count', 0)}"

@app.callback(
    Output('feeder-state-store', 'data'),
    Input('interval-update', 'n_intervals')
)
def update_feeder_state(n):
    return sensor_data.get("feeder_state", "IDLE")

@app.callback(
    Output('auto-mode-state-store', 'data'),
    Input('interval-update', 'n_intervals')
)
def update_auto_mode_state(n):
    return sensor_data.get("auto_mode", "off")


if __name__ == '__main__':
    app.run(debug =True, host='0.0.0.0', port=8050)