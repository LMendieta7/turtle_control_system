import dash
from dash import dcc, html, Input, Output, State, callback_context, no_update
import time

from mqtt.client import mqtt_client, status, basking_sensor, water_sensor

dash.register_page(__name__, path="/", name="Dashboard")

def layout():
    # ─── Seed Auto-Mode from ESP on initial load ─────────────────────────
    auto_on = status.get_status("auto_mode", default="off") == "on"

    btn_txt    = "Turn Auto Off"  if auto_on else "Turn Auto On"
    btn_cls    = "auto-on"        if auto_on else "auto-off"
    status_txt = "Automatic mode" if auto_on else "Manual mode"
    status_cls = btn_cls

    return html.Main([

        # ─── PAGE HEADER ───────────────────────────────────────────────
        html.Div([
            html.H1("Dashboard", className="page-title"),
            html.P(
                "Live conditions and habitat controls.",
                className="dashboard-subtitle",
            ),
        ], className="dashboard-header"),

        # ─── SYSTEM STATUS ─────────────────────────────────────────────
        html.Section([
            html.Div([
                html.Div(html.I(className="fa-solid fa-signal"), className="section-icon status-icon"),
                html.Div([
                    html.H2("System Status"),
                    html.P("Controller, network, and bulb health.", className="section-description"),
                ]),
            ], className="section-heading"),
            html.Div(id="status-container"),
        ], className="dashboard-card status-card"),

        # ─── TEMPERATURE GAUGES ────────────────────────────────────────
        html.Div([
            html.Section([
                html.Div([
                    html.Div(html.I(className="fa-solid fa-temperature-high"), className="metric-icon basking-icon"),
                    html.Div([
                        html.Div("Basking Area", className="metric-title"),
                        html.Div("Surface temperature", className="metric-description"),
                    ]),
                ], className="metric-heading"),
                html.Div([
                    html.Div([
                        html.Span(id="basking-gauge-value", className="gauge-value"),
                        html.Span("°F", className="gauge-unit"),
                    ], className="gauge-readout"),
                ], id="basking-gauge", className="radial-gauge basking-gauge"),
                html.Div([
                    html.Span("45°F"),
                    html.Span("105°F"),
                ], className="gauge-range"),
            ], className="dashboard-card metric-card"),
            html.Section([
                html.Div([
                    html.Div(html.I(className="fa-solid fa-water"), className="metric-icon water-icon"),
                    html.Div([
                        html.Div("Water", className="metric-title"),
                        html.Div("Tank temperature", className="metric-description"),
                    ]),
                ], className="metric-heading"),
                html.Div([
                    html.Div([
                        html.Span(id="water-gauge-value", className="gauge-value"),
                        html.Span("°F", className="gauge-unit"),
                    ], className="gauge-readout"),
                ], id="water-gauge", className="radial-gauge water-gauge"),
                html.Div([
                    html.Span("45°F"),
                    html.Span("105°F"),
                ], className="gauge-range"),
            ], className="dashboard-card metric-card"),
        ], id="gauge-container"),

        # ─── CONTROLS ──────────────────────────────────────────────────
        html.Div([
            html.Section([
                html.Div([
                    html.Div(html.I(className="fa-solid fa-sliders"), className="section-icon control-section-icon"),
                    html.Div([
                        html.H2("Quick Controls"),
                        html.P("Manual feeder and lighting actions.", className="section-description"),
                    ]),
                ], className="section-heading"),
                html.Div([
                    html.Div([
                        html.Div(html.I(className="fa-solid fa-bowl-food"), className="action-icon"),
                        html.Div("Feeder", className="action-label"),
                        html.Button("Feed (0)",
                                    id="feed-btn",
                                    n_clicks=0,
                                    className="feed-idle"),
                    ], className="action-control"),
                    html.Div([
                        html.Div(html.I(className="fa-regular fa-lightbulb"), className="action-icon"),
                        html.Div("Tank Lights", className="action-label"),
                        html.Button("Lights On",
                                    id="light-btn",
                                    n_clicks=0,
                                    className="light-off"),
                    ], className="action-control"),
                ], className="button-row"),
            ], className="dashboard-card controls-card"),

            html.Section([
                html.Div([
                    html.Div(html.I(className="fa-solid fa-clock-rotate-left"), className="section-icon auto-section-icon"),
                    html.Div([
                        html.H2("Operating Mode"),
                        html.P("Choose scheduled or manual control.", className="section-description"),
                    ]),
                ], className="section-heading"),
                html.Div([
                    html.Div([
                        html.Div("Current mode", className="mode-label"),
                        html.Div(status_txt,
                                 id="auto-status",
                                 className=status_cls),
                    ], className="mode-copy"),
                    html.Button([
                        html.I(className="fa-solid fa-power-off"),
                        html.Span(btn_txt),
                    ],
                        id="auto-toggle-btn",
                        n_clicks=0,
                        className=btn_cls),
                ], className="auto-container"),
                html.P(
                    "Auto Mode follows the saved light schedule and disables manual actions.",
                    className="mode-note",
                ),
            ], className="dashboard-card auto-card"),
        ], className="controls-grid"),

        # ─── STORES & INTERVAL ────────────────────────────────────────
        dcc.Store(id="auto-mode-store",    data=auto_on),
        dcc.Store(id="light-status-store", data="OFF"),
        dcc.Store(id="feeder-state-store", data="IDLE"),
        dcc.Store(id="auto-mode-cooldown-until", data=0),
        dcc.Interval(id="interval-update", interval=1000, n_intervals=0),

    ], className="dashboard-page")

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
    heat_status  = status.get_status("heat_bulb_current_status",  default="OFF")
    uv_status    = status.get_status("uv_bulb_current_status",    default="OFF")
    
    def bulb_stat_color(status):
        if status == "OK":
            return "green"
        elif status == "FLT":
            return "red"
        else :
            return "gray"

    def fmt(ms):
        s = ms // 1000
        return f"{s//86400}d {(s%86400)//3600}h {(s%3600)//60}m"

    return html.Div([
        html.Div([
            html.Span(className=f"status-dot {esp_col}"),
            html.Div([
                html.Span("ESP32", title="ESP32-S3 status/MQTT", className="status-label"),
                html.Span("Controller", className="status-detail"),
            ], className="status-copy"),
        ], className="status-item"),
        html.Div([
            html.Span(className=f"status-dot {mqtt_col}"),
            html.Div([
                html.Span("MQTT", title="Dashboard MQTT broker connection", className="status-label"),
                html.Span("Broker", className="status-detail"),
            ], className="status-copy"),
        ], className="status-item"),

        html.Div([
            html.I(className="fa-solid fa-network-wired status-item-icon"),
            html.Div([
                html.Span("IP address", title="ESP32-S3 IP address", className="status-label"),
                html.Span(ip, className="status-value"),
            ], className="status-copy"),
        ], className="status-item"),

        html.Div([
            html.I(className="fa-regular fa-clock status-item-icon"),
            html.Div([
                html.Span("Uptime", title="ESP32-S3 uptime since boot", className="status-label"),
                html.Span(fmt(upms), className="status-value"),
            ], className="status-copy"),
        ], className="status-item"),

        html.Div([
            html.I(className="fa-solid fa-memory status-item-icon"),
            html.Div([
                html.Span("Free memory", title="ESP32-S3 free RAM", className="status-label"),
                html.Span(f"{ram} B" if isinstance(ram, (int, float)) else ram, className="status-value"),
            ], className="status-copy"),
        ], className="status-item"),

        html.Div([
            html.Span(className=f"status-dot {bulb_stat_color(heat_status)}"),
            html.Div([
                html.Span("Heat bulb", title="Heat bulb current and health", className="status-label"),
                html.Span(f"{heat_current:.2f} A", className="status-value"),
            ], className="status-copy"),
        ], className="status-item"),
        html.Div([
            html.Span(className=f"status-dot {bulb_stat_color(uv_status)}"),
            html.Div([
                html.Span("UV bulb", title="UV bulb current and health", className="status-label"),
                html.Span(f"{uv_current:.2f} A", className="status-value"),
            ], className="status-copy"),
        ], className="status-item"),

    ], className="status-bar")

# ─── GAUGES ────────────────────────────────────────────────────────────
@dash.callback(
    Output("basking-gauge-value", "children"),
    Output("basking-gauge", "style"),
    Output("basking-gauge", "className"),
    Output("water-gauge-value", "children"),
    Output("water-gauge", "style"),
    Output("water-gauge", "className"),
    Input("interval-update","n_intervals")
)
def update_gauges(n):
    bval, wval      = basking_sensor.get(),      water_sensor.get()
    b_stale, w_stale = basking_sensor.is_stale(15), water_sensor.is_stale(15)

    def gauge_data(value, stale, gauge_type):
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = 0.0

        percent = max(0.0, min(100.0, (numeric_value - 45.0) / 60.0 * 100.0))
        style = {"--gauge-fill": f"{percent * 1.8:.1f}deg"}
        css_class = f"radial-gauge {gauge_type}-gauge"
        if stale:
            css_class += " gauge-stale"
        display_value = f"{numeric_value:.1f}"
        return display_value, style, css_class

    b_display, b_style, b_class = gauge_data(bval, b_stale, "basking")
    w_display, w_style, w_class = gauge_data(wval, w_stale, "water")
    return b_display, b_style, b_class, w_display, w_style, w_class



# ─── FEED BUTTON ───────────────────────────────────────────────────────
@dash.callback(
    Output("feed-btn","n_clicks"),
    Input("feed-btn","n_clicks"),
    State("auto-mode-store","data"),
    prevent_initial_call=True
)
def on_feed_click(n, auto_on):
    if auto_on: return 0
    mqtt_client.publish("turtle/feeder/cmd","1")
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
    mqtt_client.publish("turtle/lights/cmd", new)
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
        mqtt_client.publish("turtle/auto_mode/cmd", "on" if new else "off")
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
    btn_txt    = "Turn Auto Off"   if on else "Turn Auto On"
    btn_cls    = "auto-on"        if on else "auto-off"
    status_txt = "Automatic mode"  if on else "Manual mode"
    status_cls = btn_cls
    btn_content = [
        html.I(className="fa-solid fa-power-off"),
        html.Span(btn_txt),
    ]
    return btn_content, btn_cls, status_txt, status_cls
