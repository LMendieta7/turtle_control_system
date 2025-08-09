# import dash
# from dash import html

# dash.register_page(__name__, path="/settings", name="Settings")

# layout = html.Div([
#     html.H2("Settings Page"),
#     html.P("Configure feed times, light schedule, and auto mode here.")
# ])

import dash
from dash import html, dcc, Input, Output

dash.register_page(__name__, path="/settings", name="Settings")

def layout():
    
    return html.Div([
    html.H1("Tank Controls"),

    html.Div([
        html.H3("Light Schedule"),

        html.Div([
            # Start Time
            html.Div([
                html.Label("Start Time:"),
                dcc.Dropdown(
                    id="light-start-hour",
                    options=[{"label": f"{h:02d}", "value": f"{h:02d}"} for h in range(24)],
                    value="08",
                    clearable=False,
                    className="dropdown"
                ),
                html.Span(":", className="time-separator"),
                dcc.Dropdown(
                    id="light-start-minute",
                    options=[{"label": f"{m:02d}", "value": f"{m:02d}"} for m in range(0, 60, 5)],
                    value="00",
                    clearable=False,
                    className="dropdown"
                )
            ], className="time-select"),

            # End Time
            html.Div([
                html.Label("End Time:"),
                dcc.Dropdown(
                    id="light-end-hour",
                    options=[{"label": f"{h:02d}", "value": f"{h:02d}"} for h in range(24)],
                    value="18",
                    clearable=False,
                    className="dropdown"
                ),
                html.Span(":", className="time-separator"),
                dcc.Dropdown(
                    id="light-end-minute",
                    options=[{"label": f"{m:02d}", "value": f"{m:02d}"} for m in range(0,60,5)],
                    value="00",
                    clearable=False,
                    className="dropdown"
                )
            ], className="time-select")
        ], className="time-row"),  # <- new flex container

    ], className="card")
])

