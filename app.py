import dash
from dash import dcc, html
from mqtt_client import sensor_data, mqtt_client, sensor_timestamps, reset_stale_sensor_data  # Import here
from navbar import navbar

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


if __name__ == '__main__':
    app.run(debug =True, host='0.0.0.0', port=8050)