import dash
from dash import dcc, html, Input, Output, State, callback_context, no_update
import plotly.graph_objects as go
import time

from mqtt_client import mqtt_client, status, basking_sensor, water_sensor

dash.register_page(__name__, path="/", name="Dashboard")

def layout():
    # ─── Seed Auto-Mode from ESP on initial load ─────────────────────────
    auto_on = status.get_status("auto_mode", default="off") == "on"

    btn_txt    = "Auto On"        if auto_on else "Auto Off"
    btn_cls    = "auto-on"        if auto_on else "auto-off"
    status_txt = "Automatic mode" if auto_on else "Manual mode"
    status_cls = btn_cls

    return html.Div([

       # ─── PAGE TITLE ────────────────────────────────────────────────
        html.H1("Turtle SCADA", className="page-title"),

         # ─── STATUS BAR ────────────────────────────────────────────────
        html.Div(id="status-container"),

        # ─── GAUGES ────────────────────────────────────────────────────
        html.Div([
            dcc.Graph(id="basking-gauge", config={"displayModeBar": False}),
            dcc.Graph(id="water-gauge",   config={"displayModeBar": False}),
        ], id="gauge-container"),

        # ─── FEED & LIGHT ──────────────────────────────────────────────
        html.Div([
            html.Button("Feed (0)",
                        id="feed-btn",
                        n_clicks=0,
                        className="feed-idle"),
            html.Button("Lights On",
                        id="light-btn",
                        n_clicks=0,
                        className="light-off"),
        ], className="button-row"),

        # ─── AUTO MODE ─────────────────────────────────────────────────
        html.Div([
            html.Button(btn_txt,
                        id="auto-toggle-btn",
                        n_clicks=0,
                        className=btn_cls),
            html.Div(status_txt,
                     id="auto-status",
                     className=status_cls)
        ], className="auto-container"),

        # ─── STORES & INTERVAL ────────────────────────────────────────
        dcc.Store(id="auto-mode-store",    data=auto_on),
        dcc.Store(id="light-status-store", data="OFF"),
        dcc.Store(id="feeder-state-store", data="IDLE"),
        dcc.Store(id="auto-mode-cooldown-until", data=0),
        dcc.Interval(id="interval-update", interval=1000, n_intervals=0),

    ])

@dash.callback(
    Output("auto-mode-cooldown-until", "data"),
    Input("auto-toggle-btn", "n_clicks"),
    State("auto-mode-cooldown-until", "data"),
    prevent_initial_call=True
)
def start_auto_mode_cooldown(n_clicks, prev_until):
    return time.time() + 1.5

# ─── STATUS BAR ────────────────────────────────────────────────────────
@dash.callback(
    Output("status-container", "children"),
    Input("interval-update", "n_intervals"),
)
def update_status_display(n):

    esp_mqtt = status.get_status("esp_mqtt", default="disconnected", timeout=15, fallback_on_stale=True)
    mqtt_s   = status.get_status("mqtt_status", default="disconnected")
    mqtt_col = "green" if mqtt_s=="connected" else "gray"

    esp_o    = status.get_status("esp_online", default=False)
    esp_col  = (
        "green" if esp_o and esp_mqtt=="connected" else
        "red"   if esp_o else
        "gray"
    )

    ip   = status.get_status("esp_ip",        default="N/A")
    ram  = status.get_status("heap",          default="N/A")
    upms = status.get_status("esp_uptime_ms", default=0)
    heat_current = status.get_status("heat_bulb_current", default=0.0)
    uv_current   = status.get_status("uv_bulb_current",   default=0.0)
    heat_status  = status.get_status("heat_bulb_status",  default="OFF")
    uv_status    = status.get_status("uv_bulb_status",    default="OFF")

    def fmt(ms):
        s = ms // 1000
        return f"{s//86400}d {(s%86400)//3600}h {(s%3600)//60}m"

    return html.Div([
        html.Div([
            html.Span("ESP32:", title="ESP32-S3 status/mqtt ", className="status-label"),
            html.Span(className=f"status-dot {esp_col}")
        ], className="status-item"),
        html.Div([
            html.Span("MQTT(B):", title="DASH MQTT broker connection status", className="status-label" ),
            html.Span(className=f"status-dot {mqtt_col}")
        ], className="status-item"),

        html.Div([
            html.Span("IP:", title="ESP32-S3 IP ADDRESS", className="status-label"),
            html.Span(ip, className="status-value")
        ], className="status-item"),

        html.Div([
            html.Span("UP:", title="ESP32-S3 uptime since boot", className="status-label"),
            html.Span(fmt(upms), className="status-value")
        ], className="status-item"),

        html.Div([
            html.Span("RAM:", title="ESP32-S3 free RAM available", className="status-label"),
            html.Span(ram, className="status-value")
        ], className="status-item"),
        
        html.Div([
            html.Span("HT B:", title="Heat bulb status and current reading in amps", className="status-label"),
            html.Span(f"{heat_status} ({heat_current:.2f} A)", className="status-value", style={
                "color": (
                "green" if heat_status == "OK"
                else "red" if heat_status == "FLT"
                else "black"  # for "OFF" or anything else
            )
            })

        ], className="status-item"),
        html.Div([
            html.Span("UV B:", title="UV bulb status and current reading in amps", className="status-label"),
            html.Span(f"{uv_status} ({uv_current:.2f} A)", className="status-value", style={
                "color": (
                "green" if uv_status == "OK"
                else "red" if uv_status == "FLT"
                else "black"  # for "OFF" or anything else
            )
            
            })
        ], className="status-item"),
       

    ], className="status-bar")

# ─── GAUGES ────────────────────────────────────────────────────────────
@dash.callback(
    [Output("basking-gauge","figure"),
     Output("water-gauge",  "figure")],
    Input("interval-update","n_intervals")
)
def update_gauges(n):
    bval, wval      = basking_sensor.get(),      water_sensor.get()
    b_stale, w_stale = basking_sensor.is_stale(15), water_sensor.is_stale(15)

    bb = 'darkred'  if not b_stale else 'lightgray'
    wb = 'darkblue' if not w_stale else 'lightgray'
    bt = 'black'    if not b_stale else 'lightgray'
    wt = 'black'    if not w_stale else 'lightgray'

    fig1 = go.Figure(go.Indicator(
        mode="gauge+number", value=bval,
        title={'text': "Basking Temp", 'font': {'size': 19,'color': 'black'}},
        gauge={'axis': {'range': [45, 105], 'tickvals': list(range(0, 111, 10)),}, 'bar': {'color': bb}},
        number={'suffix': "°F", 'font': {'size': 36,'color': bt}}
    ))
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number", value=wval,
        title={'text': "Water Temp", 'font': {'size': 19, 'color': 'black'}},
        gauge={'axis': {'range': [45, 105], 'tickvals': list(range(0, 111, 10)), }, 'bar': {'color': wb}},
        number={'suffix': "°F", 'font': {'size': 36,'color': wt}}
    ))

    for fig in (fig1, fig2):
        fig.update_layout(
            paper_bgcolor='#f5f5f5',
            plot_bgcolor='#f5f5f5',
            margin={'l':30,'r':30,'t':4,'b':0},
        )

    return fig1, fig2



# ─── FEED BUTTON ───────────────────────────────────────────────────────
@dash.callback(
    Output("feed-btn","n_clicks"),
    Input("feed-btn","n_clicks"),
    State("auto-mode-store","data"),
    prevent_initial_call=True
)
def on_feed_click(n, auto_on):
    if auto_on: return 0
    mqtt_client.publish("turtle/feed","1")
    return 0

@dash.callback(
    Output("feed-btn","children"),
    Output("feed-btn","className"),
    Input("interval-update","n_intervals")
)
def render_feed(n):
    state      = status.get_status("feeder_state", default="IDLE")
    feed_count = status.get_status("feed_count",   default=0)
    running    = (state == "RUNNING")
    label      = "Feeding..." if running else f"Feed ({feed_count})"
    cls        = "feed-active" if running else "feed-idle"
    return label, cls

# ─── LIGHT BUTTON ──────────────────────────────────────────────────────
@dash.callback(
    Output("light-status-store","data"),
    Input("interval-update","n_intervals")
)
def poll_light(n):
    return status.get_status("light_status", default="OFF")

@dash.callback(
    Output("light-btn","children"),
    Output("light-btn","className"),
    Input("light-status-store","data")
)
def render_light(light_s):
    on  = (light_s=="ON")
    txt = "Lights Off" if on else "Lights On"
    cls = "light-on" if on else "light-off"
    return txt, cls

@dash.callback(
    Output("light-btn","n_clicks"),
    Input("light-btn","n_clicks"),
    State("auto-mode-store","data"),
    State("light-status-store","data"),
    prevent_initial_call=True
)
def on_light_click(n, auto_on, cur):
    if auto_on: return 0
    new = "OFF" if cur=="ON" else "ON"
    mqtt_client.publish("turtle/lights", new)
    return 0

# ─── AUTO MODE STORE UPDATE ───────────────────────────────────────────
@dash.callback(
    Output("auto-mode-store", "data"),
    [Input("auto-toggle-btn", "n_clicks"),
     Input("interval-update", "n_intervals")],
    [State("auto-mode-store", "data"),
     State("auto-mode-cooldown-until", "data")]
)
def update_auto_store(n_clicks, n_intervals, current, cooldown_until):
    now = time.time()
    triggered = callback_context.triggered[0]["prop_id"].split(".")[0]
    if triggered == "auto-toggle-btn":
        new = not current
        mqtt_client.publish("turtle/auto_mode", "on" if new else "off")
        return new
    # Only sync to broker if cooldown has expired
    if now < cooldown_until:
        return no_update
    actual = status.get_status("auto_mode", default="off") == "on"
    if actual != current:
        return actual
    return no_update


# ─── AUTO MODE RENDER ─────────────────────────────────────────────────
@dash.callback(
    Output("auto-toggle-btn","children"),
    Output("auto-toggle-btn","className"),
    Output("auto-status",       "children"),
    Output("auto-status",       "className"),
    Input("auto-mode-store",    "data")
)
def render_auto(on):
    btn_txt    = "Auto On"        if on else "Auto Off"
    btn_cls    = "auto-on"        if on else "auto-off"
    status_txt = "Automatic mode"  if on else "Manual mode"
    status_cls = btn_cls
    return btn_txt, btn_cls, status_txt, status_cls
