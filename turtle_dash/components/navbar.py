from dash import html, dcc
from dash import callback, Output, Input

navbar = html.Div([
    dcc.Link([
        html.I(className="fa-solid fa-turtle nav-brand-icon"),
        html.Span("Turtle Control", className="nav-brand-name"),
    ], href="/", className="nav-brand"),
    html.Div([
        dcc.Link("DASHBOARD", href="/", id="link-dashboard", className="nav-link"),
        dcc.Link("TRENDS", href="/trends", id="link-trends", className="nav-link"),
        dcc.Link("SETTINGS", href="/settings", id="link-settings", className="nav-link"),
    ], className="nav-links"),
    html.Div([
        html.I(className="fa-solid fa-user-circle user-icon")


    ], className="nav-right")
], className="navbar")

@callback(
    [Output("link-dashboard", "className"),
     Output("link-trends", "className"),
     Output("link-settings", "className")],
    Input("url", "pathname")
)
def update_active_link(path):
    return [
        "nav-link active" if path == "/" else "nav-link",
        "nav-link active" if path.startswith("/trends") else "nav-link",
        "nav-link active" if path.startswith("/settings") else "nav-link"
    ]
