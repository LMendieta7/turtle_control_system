import dash
from dash import html
from dash import dcc, html, callback, Input, Output
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from datetime import datetime

dash.register_page(__name__, path="/trends", name="Temperatures")

layout = html.Div([
    html.H1("Hourly Temperature", style={'textAlign': 'center', 'color': '#183A73', 'fontWeight': 'bold'}),
    dcc.Graph(id='trends-graph', config={'displayModeBar': False}, style={'margin': 'auto', 'maxWidth': '98vw'}),
    dcc.Interval(id='trends-interval', interval=60*1000, n_intervals=0)  # Update every minute
])


# Graph update callback
@callback(
    Output('trends-graph', 'figure'),
    Input('trends-interval', 'n_intervals')
)
def update_trends(n):
    try:
        # Connect and load today's data
        conn = sqlite3.connect("turtle.db")
        df = pd.read_sql_query(
            "SELECT * FROM temperature_log WHERE DATE(timestamp) = DATE('now', 'localtime')",
            conn
        )
        conn.close()

        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                xaxis_title="Hour of Day",
                yaxis_title="Temperature (°F)",
                title="No data logged for today yet.",
                yaxis=dict(
                    tickformat="d",
                    dtick=2
                )
            )
            return fig

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        hourly = df.groupby('hour').mean(numeric_only=True).reset_index()

        # If you want to round to integers explicitly (not necessary if your DB has only ints):
        # hourly["basking_temp"] = hourly["basking_temp"].round(0)
        # hourly["water_temp"] = hourly["water_temp"].round(0)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hourly["hour"], y=hourly["basking_temp"],
            name="Basking Temp", mode="lines+markers", line=dict(width=4, color='darkred'),
            hovertemplate='Hour: %{x}:00<br>Basking Temp: %{y:.0f}°F'
        ))
        fig.add_trace(go.Scatter(
            x=hourly["hour"], y=hourly["water_temp"],
            name="Water Temp", mode="lines+markers", line=dict(width=4, color='darkblue'),
            hovertemplate='Hour: %{x}:00<br>Water Temp: %{y:.0f}°F'
        ))
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(0, 24,2)),   # Ticks at every 2 hours
                ticktext=[f"{str(h).zfill(2)}:00" for h in range(0, 24,2)],
                title="Hour of Day"
            ),
            yaxis=dict(
                title="Temperature (°F)",
                tickformat="d",    # Only show whole numbers
                dtick=5,
                range=[60, 110]            # Ticks every 2°F
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
            margin=dict(l=32, r=16, t=32, b=32),
        )
        return fig

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(
            title=f"Error loading data: {e}",
            xaxis_title="Hour of Day",
            yaxis_title="Temperature (°F)",
            yaxis=dict(
                tickformat="d",
                dtick=2
            )
        )
        return fig