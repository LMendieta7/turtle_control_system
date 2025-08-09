from services.monitoring import start_all_monitors
import dash 
from dash import dcc, html
from navbar import navbar
from services.db.database import Database
import time
from mqtt.client import start_mqtt          # To connect and run MQTT in background

Database()
start_mqtt()
time.sleep(1)
start_all_monitors()

# Initialize the database (creates table if needed)

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