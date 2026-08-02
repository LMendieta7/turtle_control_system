# pages/settings.py
import dash
from dash import html, dcc, Input, Output, State, no_update
import json
from mqtt.status_manager import status
from mqtt.client import mqtt_client

dash.register_page(__name__, path="/settings", name="Settings")

# ---------- helpers ----------
def _split_or_default(s: str, fallback="07:30"):
    try:
        hh, mm = (s or fallback).split(":")
        return f"{int(hh):02d}", f"{int(mm):02d}"
    except Exception:
        return fallback.split(":")

def _minutes_between(start_hhmm: str, end_hhmm: str) -> int:
    """Minutes from start to end, wrapping over midnight if needed."""
    sh, sm = [int(x) for x in start_hhmm.split(":")]
    eh, em = [int(x) for x in end_hhmm.split(":")]
    s = sh * 60 + sm
    e = eh * 60 + em
    diff = (e - s) % (24 * 60)  # overnight handled
    return diff

def _fmt_duration(mins: int) -> str:
    h = mins // 60
    m = mins % 60
    return f"{h}h {m}m"

def _fmt_12h(hhmm: str) -> str:
    h, m = [int(x) for x in hhmm.split(":")]
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0: h12 = 12
    return f"{h12}:{m:02d} {suffix}"

# ---------- layout ----------
def layout():
    # Pull retained schedule published by ESP
    on_str  = status.get_status("lights_on_str",  "07:30")
    off_str = status.get_status("lights_off_str", "19:00")
    on_hh, on_mm   = _split_or_default(on_str)
    off_hh, off_mm = _split_or_default(off_str)

    hour_opts   = [{"label": f"{h:02d}", "value": f"{h:02d}"} for h in range(24)]
    minute_opts = [{"label": f"{m:02d}", "value": f"{m:02d}"} for m in range(0, 60, 5)]

    return html.Div([
        html.H1("Tank Controls"),

        html.Div([
            html.H3("Light Schedule"),

            # Current (live) schedule from ESP + duration
            html.Div(id="current-light-schedule", className="muted", style={"marginBottom": 8}),
            dcc.Interval(id="sched-poll", interval=2000, n_intervals=0),

            html.Div([
                # Start
                html.Div([
                    html.Label("Start Time:"),
                    dcc.Dropdown(id="light-start-hour",   options=hour_opts,   value=on_hh,  clearable=False, className="dropdown"),
                    html.Span(":", className="time-separator"),
                    dcc.Dropdown(id="light-start-minute", options=minute_opts, value=on_mm,  clearable=False, className="dropdown"),
                ], className="time-select"),

                # End
                html.Div([
                    html.Label("End Time:"),
                    dcc.Dropdown(id="light-end-hour",     options=hour_opts,   value=off_hh, clearable=False, className="dropdown"),
                    html.Span(":", className="time-separator"),
                    dcc.Dropdown(id="light-end-minute",   options=minute_opts, value=off_mm, clearable=False, className="dropdown"),
                ], className="time-select"),
            ], className="time-row"),

            # Live summary of selected interval
            html.Div(id="selected-interval-summary", className="muted", style={"marginTop": 8}),

            html.Button("Save Schedule", id="save-light-schedule", n_clicks=0, className="btn"),
            html.Div(id="schedule-save-status", className="muted", style={"marginTop": 8}),
        ], className="card"),

        html.Div([
            html.H3("Individual Light Control"),
            html.P(
                "Control each bulb separately. Bulb states refresh automatically.",
                className="muted",
            ),
            html.Div([
                html.Div([
                    html.Div("Heat Bulb", className="individual-light-name"),
                    html.Div(id="heat-light-state", className="individual-light-state"),
                    html.Button(
                        id="heat-light-btn",
                        n_clicks=0,
                        className="individual-light-btn light-off",
                    ),
                ], className="individual-light-control"),
                html.Div([
                    html.Div("UV Bulb", className="individual-light-name"),
                    html.Div(id="uv-light-state", className="individual-light-state"),
                    html.Button(
                        id="uv-light-btn",
                        n_clicks=0,
                        className="individual-light-btn light-off",
                    ),
                ], className="individual-light-control"),
            ], className="individual-light-grid"),
        ], className="card"),
    ])

# ---------- callbacks ----------

@dash.callback(
    Output("current-light-schedule", "children"),
    Input("sched-poll", "n_intervals"),
)
def show_current_schedule(_):
    on  = status.get_status("lights_on_str",  "07:30")
    off = status.get_status("lights_off_str", "19:00")
    mins = _minutes_between(on, off)
    # show both 24h and 12h for readability
    return f"Current schedule: {on} → {off}  ({_fmt_12h(on)} → {_fmt_12h(off)}) • total {_fmt_duration(mins)}"

@dash.callback(
    Output("selected-interval-summary", "children"),
    Input("light-start-hour", "value"),
    Input("light-start-minute", "value"),
    Input("light-end-hour", "value"),
    Input("light-end-minute", "value"),
)
def summarize_selected(sh, sm, eh, em):
    if not all([sh, sm, eh, em]):  # not ready yet
        return no_update
    on  = f"{sh}:{sm}"
    off = f"{eh}:{em}"
    mins = _minutes_between(on, off)
    extra = " (0h → lights never auto-on)" if mins == 0 else ""
    return f"Selected: {on} → {off}  ({_fmt_12h(on)} → {_fmt_12h(off)}) • total {_fmt_duration(mins)}{extra}"

@dash.callback(
    Output("schedule-save-status", "children"),
    Input("save-light-schedule", "n_clicks"),
    State("light-start-hour", "value"),
    State("light-start-minute", "value"),
    State("light-end-hour", "value"),
    State("light-end-minute", "value"),
    prevent_initial_call=True,
)
def save_schedule(n, sh, sm, eh, em):
    on  = f"{(sh or '07'):0>2}:{(sm or '00'):0>2}"
    off = f"{(eh or '19'):0>2}:{(em or '00'):0>2}"
    payload = json.dumps({"on": on, "off": off})
    try:
        # retained command -> ESP persists to NVS and republishes lights/schedule
        mqtt_client.publish("turtle/lights/schedule/cmd", payload, qos=0, retain=True)
        # optimistic local cache so UI updates immediately
        status.update_status("lights_on_str",  on)
        status.update_status("lights_off_str", off)
        mins = _minutes_between(on, off)
        return f"Saved: {on} → {off} • total {_fmt_duration(mins)}"
    except Exception as e:
        return f"Error: {e}"


def _normalize_light_state(value):
    return str(value or "OFF").strip().upper()


def _render_individual_light(value):
    is_on = _normalize_light_state(value) == "ON"
    state = "On" if is_on else "Off"
    action = "Turn Off" if is_on else "Turn On"
    css_class = "light-on" if is_on else "light-off"
    return state, action, f"individual-light-btn {css_class}"


@dash.callback(
    Output("heat-light-state", "children"),
    Output("heat-light-btn", "children"),
    Output("heat-light-btn", "className"),
    Input("sched-poll", "n_intervals"),
)
def render_heat_light(_):
    return _render_individual_light(
        status.get_status("heat_bulb_status", default="OFF")
    )


@dash.callback(
    Output("uv-light-state", "children"),
    Output("uv-light-btn", "children"),
    Output("uv-light-btn", "className"),
    Input("sched-poll", "n_intervals"),
)
def render_uv_light(_):
    return _render_individual_light(
        status.get_status("uv_bulb_status", default="OFF")
    )


def _toggle_individual_light(status_key, command_topic):
    current = _normalize_light_state(status.get_status(status_key, default="OFF"))
    new_state = "OFF" if current == "ON" else "ON"
    mqtt_client.publish(command_topic, new_state)
    status.update_status(status_key, new_state)


@dash.callback(
    Output("heat-light-btn", "n_clicks"),
    Input("heat-light-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_heat_light(_):
    _toggle_individual_light("heat_bulb_status", "turtle/lights/heat/cmd")
    return 0


@dash.callback(
    Output("uv-light-btn", "n_clicks"),
    Input("uv-light-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_uv_light(_):
    _toggle_individual_light("uv_bulb_status", "turtle/lights/uv/cmd")
    return 0
