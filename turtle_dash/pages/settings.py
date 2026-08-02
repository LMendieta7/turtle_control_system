# pages/settings.py
import dash
from dash import html, dcc, Input, Output, State, no_update, ctx
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

def _to_12h_parts(hhmm: str):
    h, m = [int(x) for x in hhmm.split(":")]
    return str(h % 12 or 12), f"{m:02d}", "AM" if h < 12 else "PM"

def _to_24h(hour, minute, period):
    h = int(hour)
    if period == "AM":
        h = 0 if h == 12 else h
    else:
        h = 12 if h == 12 else h + 12
    return f"{h:02d}:{int(minute):02d}"

# ---------- layout ----------
def layout():
    # Pull retained schedule published by ESP
    on_str  = status.get_status("lights_on_str",  "07:30")
    off_str = status.get_status("lights_off_str", "19:00")
    on_hh24, on_mm = _split_or_default(on_str, "07:30")
    off_hh24, off_mm = _split_or_default(off_str, "19:00")
    on_hh, on_mm, on_period = _to_12h_parts(f"{on_hh24}:{on_mm}")
    off_hh, off_mm, off_period = _to_12h_parts(f"{off_hh24}:{off_mm}")

    hour_opts = [{"label": str(h), "value": str(h)} for h in range(1, 13)]
    minute_values = sorted(set(range(0, 60, 5)) | {int(on_mm), int(off_mm)})
    minute_opts = [{"label": f"{m:02d}", "value": f"{m:02d}"} for m in minute_values]
    period_opts = [{"label": period, "value": period} for period in ("AM", "PM")]

    return html.Main([
        html.Div([
            html.H1("Settings"),
        ], className="settings-header"),

        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fa-regular fa-clock"),
                ], className="card-icon schedule-icon"),
                html.Div([
                    html.H2("Light Schedule"),
                    html.P("Choose when Auto Mode runs both lights.", className="card-description"),
                ]),
            ], className="card-heading"),

            # Current (live) schedule from ESP + duration
            html.Div(id="current-light-schedule", className="current-schedule"),
            dcc.Interval(id="sched-poll", interval=2000, n_intervals=0),

            html.Div([
                # Start
                html.Div([
                    html.Div([
                        html.I(className="fa-solid fa-sun"),
                        html.Label("Lights on", className="time-label"),
                    ], className="time-field-heading lights-on-heading"),
                    html.Div([
                        dcc.Dropdown(id="light-start-hour", options=hour_opts, value=on_hh, clearable=False, className="time-dropdown"),
                        html.Span(":", className="time-separator"),
                        dcc.Dropdown(id="light-start-minute", options=minute_opts, value=on_mm, clearable=False, className="time-dropdown"),
                        dcc.RadioItems(
                            id="light-start-period",
                            options=period_opts,
                            value=on_period,
                            className="period-selector",
                            inputClassName="period-selector-input",
                            labelClassName="period-selector-option",
                        ),
                    ], className="time-select"),
                ], className="time-field"),

                # End
                html.Div([
                    html.Div([
                        html.I(className="fa-solid fa-moon"),
                        html.Label("Lights off", className="time-label"),
                    ], className="time-field-heading lights-off-heading"),
                    html.Div([
                        dcc.Dropdown(id="light-end-hour", options=hour_opts, value=off_hh, clearable=False, className="time-dropdown"),
                        html.Span(":", className="time-separator"),
                        dcc.Dropdown(id="light-end-minute", options=minute_opts, value=off_mm, clearable=False, className="time-dropdown"),
                        dcc.RadioItems(
                            id="light-end-period",
                            options=period_opts,
                            value=off_period,
                            className="period-selector",
                            inputClassName="period-selector-input",
                            labelClassName="period-selector-option",
                        ),
                    ], className="time-select"),
                ], className="time-field"),
            ], className="time-row"),

            # Live summary of selected interval
            html.Div(id="selected-interval-summary", className="schedule-summary"),

            html.Div([
                html.Button([
                    html.I(className="fa-regular fa-floppy-disk"),
                    html.Span("Save schedule"),
                ], id="save-light-schedule", n_clicks=0, className="primary-btn"),
                html.Div(id="schedule-save-status", className="action-message"),
            ], className="card-actions"),
        ], className="settings-card"),

        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fa-regular fa-lightbulb"),
                ], className="card-icon control-icon"),
                html.Div([
                    html.H2("Individual Lights"),
                    html.P("Manual control for each habitat bulb.", className="card-description"),
                ]),
            ], className="card-heading"),
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className="fa-solid fa-fire-flame-curved"),
                    ], className="bulb-icon heat-icon"),
                    html.Div("Heat Bulb", className="individual-light-name"),
                    html.Div([
                        html.Span(className="state-dot"),
                        html.Span(id="heat-light-state"),
                    ], id="heat-light-status", className="individual-light-state"),
                    html.Button(
                        id="heat-light-btn",
                        n_clicks=0,
                        className="individual-light-btn light-off",
                    ),
                ], className="individual-light-control"),
                html.Div([
                    html.Div([
                        html.I(className="fa-solid fa-sun"),
                    ], className="bulb-icon uv-icon"),
                    html.Div("UV Bulb", className="individual-light-name"),
                    html.Div([
                        html.Span(className="state-dot"),
                        html.Span(id="uv-light-state"),
                    ], id="uv-light-status", className="individual-light-state"),
                    html.Button(
                        id="uv-light-btn",
                        n_clicks=0,
                        className="individual-light-btn light-off",
                    ),
                ], className="individual-light-control"),
            ], className="individual-light-grid"),
            html.Div(id="light-command-status", className="action-message light-command-message"),
            html.P([
                html.I(className="fa-solid fa-circle-info"),
                html.Span(" Using a manual control turns off Auto Mode so the command can run."),
            ], className="control-note"),
            html.Div([
                html.Div([
                    html.Div("Schedule control", className="auto-return-label"),
                    html.Div(
                        "Return both lights to the saved automatic schedule.",
                        className="auto-return-description",
                    ),
                ]),
                html.Button([
                    html.I(className="fa-solid fa-rotate"),
                    html.Span(id="return-auto-mode-label"),
                ], id="return-auto-mode-btn", n_clicks=0, className="auto-return-btn"),
            ], className="auto-return-row"),
            html.Div(
                id="auto-mode-return-status",
                className="action-message auto-return-message",
            ),
        ], className="settings-card"),
    ], className="settings-page")

# ---------- callbacks ----------

@dash.callback(
    Output("current-light-schedule", "children"),
    Input("sched-poll", "n_intervals"),
)
def show_current_schedule(_):
    on  = status.get_status("lights_on_str",  "07:30")
    off = status.get_status("lights_off_str", "19:00")
    mins = _minutes_between(on, off)
    return f"Current: {_fmt_12h(on)} – {_fmt_12h(off)} • {_fmt_duration(mins)}"

@dash.callback(
    Output("selected-interval-summary", "children"),
    Input("light-start-hour", "value"),
    Input("light-start-minute", "value"),
    Input("light-start-period", "value"),
    Input("light-end-hour", "value"),
    Input("light-end-minute", "value"),
    Input("light-end-period", "value"),
)
def summarize_selected(sh, sm, sp, eh, em, ep):
    if not all([sh, sm, sp, eh, em, ep]):
        return no_update
    on = _to_24h(sh, sm, sp)
    off = _to_24h(eh, em, ep)
    mins = _minutes_between(on, off)
    if mins == 0:
        return "Choose different on and off times."
    return f"Runs {_fmt_12h(on)} – {_fmt_12h(off)} • {_fmt_duration(mins)}"

@dash.callback(
    Output("schedule-save-status", "children"),
    Input("save-light-schedule", "n_clicks"),
    State("light-start-hour", "value"),
    State("light-start-minute", "value"),
    State("light-start-period", "value"),
    State("light-end-hour", "value"),
    State("light-end-minute", "value"),
    State("light-end-period", "value"),
    prevent_initial_call=True,
)
def save_schedule(n, sh, sm, sp, eh, em, ep):
    on = _to_24h(sh or "7", sm or "00", sp or "AM")
    off = _to_24h(eh or "7", em or "00", ep or "PM")
    mins = _minutes_between(on, off)
    if mins == 0:
        return "On and off times must be different."
    payload = json.dumps({"on": on, "off": off})
    try:
        # retained command -> ESP persists to NVS and republishes lights/schedule
        mqtt_client.publish("turtle/lights/schedule/cmd", payload, qos=0, retain=True)
        # optimistic local cache so UI updates immediately
        status.update_status("lights_on_str",  on)
        status.update_status("lights_off_str", off)
        return f"Saved: {_fmt_12h(on)} – {_fmt_12h(off)} • {_fmt_duration(mins)}"
    except Exception as e:
        return f"Error: {e}"


def _normalize_light_state(value):
    return str(value or "OFF").strip().upper()


def _render_individual_light(value):
    is_on = _normalize_light_state(value) == "ON"
    state = "On" if is_on else "Off"
    action = "Turn Off" if is_on else "Turn On"
    css_class = "light-on" if is_on else "light-off"
    return (
        state,
        f"individual-light-state {css_class}",
        action,
        f"individual-light-btn {css_class}",
    )


@dash.callback(
    Output("heat-light-state", "children"),
    Output("heat-light-status", "className"),
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
    Output("uv-light-status", "className"),
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

    auto_was_on = str(status.get_status("auto_mode", default="off")).lower() == "on"
    if auto_was_on:
        # The ESP rejects manual light commands in Auto Mode. MQTT preserves
        # publish order on this connection, so disable Auto Mode first.
        mqtt_client.publish("turtle/auto_mode/cmd", "off")
        status.update_status("auto_mode", "off")

    mqtt_client.publish(command_topic, new_state)
    status.update_status(status_key, new_state)
    return new_state, auto_was_on


@dash.callback(
    Output("light-command-status", "children"),
    Input("heat-light-btn", "n_clicks"),
    Input("uv-light-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_individual_light(_, __):
    light_id = ctx.triggered_id
    if light_id == "heat-light-btn":
        label, key, topic = "Heat bulb", "heat_bulb_status", "turtle/lights/heat/cmd"
    elif light_id == "uv-light-btn":
        label, key, topic = "UV bulb", "uv_bulb_status", "turtle/lights/uv/cmd"
    else:
        return no_update

    try:
        new_state, auto_was_on = _toggle_individual_light(key, topic)
        mode_message = " Auto Mode was turned off." if auto_was_on else ""
        return f"{label} command sent: {new_state.title()}.{mode_message}"
    except Exception as exc:
        return f"Could not control {label.lower()}: {exc}"


@dash.callback(
    Output("return-auto-mode-label", "children"),
    Output("return-auto-mode-btn", "disabled"),
    Output("return-auto-mode-btn", "className"),
    Input("sched-poll", "n_intervals"),
)
def render_return_to_auto_mode(_):
    auto_is_on = (
        str(status.get_status("auto_mode", default="off")).strip().lower() == "on"
    )
    if auto_is_on:
        return "Auto Mode Active", True, "auto-return-btn active"
    return "Return to Auto Mode", False, "auto-return-btn"


@dash.callback(
    Output("auto-mode-return-status", "children"),
    Input("return-auto-mode-btn", "n_clicks"),
    prevent_initial_call=True,
)
def return_to_auto_mode(_):
    try:
        mqtt_client.publish("turtle/auto_mode/cmd", "on")
        status.update_status("auto_mode", "on")
        return "Auto Mode enabled. The saved light schedule is now in control."
    except Exception as exc:
        return f"Could not enable Auto Mode: {exc}"
