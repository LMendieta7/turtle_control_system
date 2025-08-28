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
