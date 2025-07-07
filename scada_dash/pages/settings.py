import dash
from dash import html

dash.register_page(__name__, path="/settings", name="Settings")

layout = html.Div([
    html.H2("Settings Page"),
    html.P("Configure feed times, light schedule, and auto mode here.")
])
