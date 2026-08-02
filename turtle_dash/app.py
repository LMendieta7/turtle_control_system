import dash
from dash import dcc, html

from components.navbar import navbar
from services.monitoring import start_background_services

external_stylesheets = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"
]

app = dash.Dash(__name__, use_pages=True, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([
    dcc.Location(id="url"),
    navbar,
    dash.page_container
])

start_background_services()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
