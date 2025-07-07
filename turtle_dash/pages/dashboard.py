import dash
from dash import dcc, html, Input, Output, State, callback_context, callback
import plotly.graph_objects as go
from mqtt_client import mqtt_client, sensor_data, reset_stale_sensor_data

dash.register_page(__name__, path="/", name="Dashboard")


layout = html.Div([

    html.Div([
        html.Div(id='mqtt-status')    #  Style now handled in style.css
    ], style={'position': 'relative'}),


    html.H1("Turtle Dashboard", style={'text-align': 'center'}),
    
    
    html.Div([
        dcc.Graph(id='basking-gauge', config={'displayModeBar': False}),
        dcc.Graph(id='water-gauge', config={'displayModeBar': False}),
    ], id='gauge-container'),
    

    
        # Control Buttons
    html.Div([
        html.Button(id='feed-btn', n_clicks=0),
        
        html.Button(id='light-btn', n_clicks=0)
    ], style={'text-align': 'center'}),


     # Auto Mode Toggle Button (new)
    html.Div([
        html.Button("Auto On", id="auto-toggle-btn", n_clicks=0, style={
        'border-radius': '50%',
        'padding': '17px 22px',
        'font-size': '15px',
        'border': 'none',
        'cursor': 'pointer',
        'color': 'white',
        'backgroundColor': 'darkblue'  # neutral default (will get overwritten)
    }),
    
    html.Div(id="auto-status", style={"color": "#333"})
    ], style={'text-align': 'center'}),

    # Store for auto mode status
    dcc.Store(id='auto-mode-store', data=True),  # True means Auto Mode is enabled

    # Interval for updating gauges
    dcc.Interval(id='interval-update', interval=2000, n_intervals=0),
    
    # Hidden store to remember light status
    dcc.Store(id='light-status-store', data='OFF'),
    dcc.Store(id='feeder-state-store', data='IDLE'),
    dcc.Store(id='auto-mode-state-store', data='on'),
    dcc.Store(id='esp-uptime-ms-store', data=0),


])

@callback(
    Output('mqtt-status', 'children'),
    Input('interval-update', 'n_intervals')
)

def update_status_display(n):
        
    reset_stale_sensor_data(timeout=10)

    esp_status = sensor_data.get("mqtt_status", "disconnected")
    esp_ip = sensor_data.get("esp_ip", "N/A")
    heap = sensor_data.get("heap", "N/A")
    uptime_ms = sensor_data.get("esp_uptime_ms", 0)
    
    esp_color = "green" if esp_status == "connected" else "gray"

    def format_uptime(ms):
        seconds = ms // 1000
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        return f"{days}d {hours}h {minutes}m"
    
    return html.Div([
    html.Div([
        html.Span("ESP STATUS: ", style={"fontWeight": "bold"}),
        html.Span(style={
            "display": "inline-block",
            "width": "10px",
            "height": "10px",
            "borderRadius": "50%",
            "backgroundColor": esp_color,
            "marginLeft": "6px"
        })
    ], style={"marginBottom": "2px"}),

    html.Div([
        html.Span("UPTIME: " , style={"fontWeight": "bold"}),
        html.Span(format_uptime(uptime_ms))
    ], style={"marginBottom": "2px"}),

    html.Div([
        html.Span("IP: ", style={"fontWeight": "bold"}),
        html.Span(esp_ip)
    ], style={"marginBottom": "2px"}),

    html.Div([
        html.Span("RAM: ", style={"fontWeight": "bold"}),
        html.Span(heap)
    ])
])


# Callbacks to update the temperature gauges
@callback(
    [Output('basking-gauge', 'figure'),
     Output('water-gauge', 'figure')],
     Input('interval-update', 'n_intervals')
)
def update_gauges(n):
    global sensor_data
    
    basking_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sensor_data["basking_temperature"],
        title={'text': "Basking Temp", 'font': {'size': 19,'color': 'black'}},
        gauge={'axis': {'range': [45, 105], 'tickvals': list(range(0, 111, 10)),}, 'bar': {'color': "darkred"}},
        number={'suffix': "°F",'font': {'size': 41}}  # Append °F after the value
    ))
    
    water_fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sensor_data["water_temperature"],
        title={'text': "Water Temp", 'font': {'size': 19, 'color': 'black'}},
        gauge={'axis': {'range': [45, 105], 'tickvals': list(range(0, 111, 10)), }, 'bar': {'color': "darkblue"}},
        number={'suffix': "°F", 'font': {'size': 41}}  # Append °F after the value
    ))

    basking_fig.update_layout(
        margin={'l':79,'r':79,'t':42,'b':0},
        paper_bgcolor='#f5f5f5',   # light gray canvas
        plot_bgcolor='#f5f5f5'     # light gray plot area
    )
    water_fig.update_layout(
        margin={'l':79,'r':79,'t':30,'b':0},
        paper_bgcolor='#f5f5f5',
        plot_bgcolor='#f5f5f5'
    )

    
    return basking_fig, water_fig

# Publish feed command
@callback(
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

@callback(
    [Output('feed-btn', 'children'),
     Output('feed-btn', 'style')],
    [Input('feeder-state-store', 'data'),
     Input('interval-update', 'n_intervals')]
)

def update_feed_button(state, _):
    is_running = state == "RUNNING"
    count = sensor_data.get("feed_count", 0)
    label = "Feeding..." if is_running else f"Feed ({count})"
    color = "green" if is_running else "gray"

    return label, {
        'backgroundColor': color,
        'color': 'white'       
    }


# Toggle lights
@callback(
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
@callback(
    Output('light-status-store', 'data'),
    Input('interval-update', 'n_intervals')
)

def update_light_status(n):
    return sensor_data.get("light_status", "OFF")

# Update light button
@callback(
    [Output('light-btn', 'children'),
     Output('light-btn', 'style')],
    Input('light-status-store', 'data')
)
def update_light_button(current_status):
    is_on = current_status == "ON"
    label = "Lights OFF" if is_on else "Lights ON"
    color = "#FFD966" if is_on else "gray"
    label_color = "black" if is_on else "white"
    return label, {
        'backgroundColor': color,
        'color': label_color,    
    }

# Unified auto mode button
@callback(
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
    color = "darkblue" if new_mode else "gray"
    return {
        'border-radius': '50%',
        'padding': '17px 22px',
        'font-size': '15px',
        'border': 'none',
        'cursor': 'pointer',
        'backgroundColor': color,
        'color': 'white'
    }, label, new_mode


@callback(
    Output('feeder-state-store', 'data'),
    Input('interval-update', 'n_intervals')
)
def update_feeder_state(n):
    return sensor_data.get("feeder_state", "IDLE")

@callback(
    Output('auto-mode-state-store', 'data'),
    Input('interval-update', 'n_intervals')
)
def update_auto_mode_state(n):
    return sensor_data.get("auto_mode", "off")


