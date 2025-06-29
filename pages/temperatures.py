import dash
from dash import html

dash.register_page(__name__, path="/temperatures", name="Temperatures")

layout = html.Div([
    html.H2("Temperature Logs"),
    html.P("Graphs and temperature history will be shown here.")
])
