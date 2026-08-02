from datetime import datetime, timedelta

import dash
from dash import Input, Output, callback, dcc, html
import pandas as pd
import plotly.graph_objects as go

from services.database import Database


dash.register_page(__name__, path="/trends", name="Trends")

GRAPH_CONFIG = {"displayModeBar": False, "responsive": True}

layout = html.Main([
    html.Div([
        html.H1("Habitat Trends"),
        html.P("Temperature history and feeding consistency over the last seven days."),
    ], className="trends-header"),

    html.Div([
        html.Div([
            html.Span("Latest basking", className="trend-stat-label"),
            html.Strong(id="latest-basking", className="trend-stat-value"),
        ], className="trend-stat"),
        html.Div([
            html.Span("Latest water", className="trend-stat-label"),
            html.Strong(id="latest-water", className="trend-stat-value"),
        ], className="trend-stat"),
        html.Div([
            html.Span("Last feeding", className="trend-stat-label"),
            html.Strong(id="last-feeding", className="trend-stat-value"),
        ], className="trend-stat"),
        html.Div([
            html.Span("Missed days", className="trend-stat-label"),
            html.Strong(id="missed-feeding-days", className="trend-stat-value"),
        ], className="trend-stat"),
    ], className="trend-stats"),

    html.Section([
        html.Div([
            html.H2("Temperature history"),
            html.P("Basking and water readings from the last seven days."),
        ], className="trend-card-heading"),
        dcc.Graph(id="temperature-trends-graph", config=GRAPH_CONFIG),
    ], className="trend-card"),

    html.Section([
        html.Div([
            html.H2("Feeding history"),
            html.P("Daily feeding events. Red bars identify days with no recorded feeding."),
        ], className="trend-card-heading"),
        dcc.Graph(id="feeding-trends-graph", config=GRAPH_CONFIG),
        html.P(
            "Feeding history begins after this update and is recorded when the controller reports that the feeder is running.",
            className="feeding-history-note",
        ),
    ], className="trend-card"),

    dcc.Interval(id="trends-interval", interval=60 * 1000, n_intervals=0),
], className="trends-page")


def empty_figure(message, y_title):
    figure = go.Figure()
    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 15, "color": "#667987"},
    )
    figure.update_layout(
        height=320,
        margin={"l": 48, "r": 20, "t": 20, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title=y_title,
    )
    return figure


@callback(
    Output("latest-basking", "children"),
    Output("latest-water", "children"),
    Output("last-feeding", "children"),
    Output("missed-feeding-days", "children"),
    Output("temperature-trends-graph", "figure"),
    Output("feeding-trends-graph", "figure"),
    Input("trends-interval", "n_intervals"),
)
def update_trends(_):
    database = Database()
    temperature_df = pd.DataFrame(
        database.get_recent_temperatures(7),
        columns=["id", "timestamp", "basking_temp", "water_temp"],
    )
    feeding_df = pd.DataFrame(
        database.get_recent_feeding_events(30),
        columns=["id", "timestamp", "source"],
    )

    latest_basking = "No data"
    latest_water = "No data"
    temperature_figure = empty_figure(
        "No temperature readings recorded in the last seven days.",
        "Temperature (°F)",
    )

    if not temperature_df.empty:
        temperature_df["timestamp"] = pd.to_datetime(temperature_df["timestamp"])
        temperature_df = temperature_df.sort_values("timestamp")
        latest = temperature_df.iloc[-1]
        latest_basking = f"{latest['basking_temp']:.1f}°F"
        latest_water = f"{latest['water_temp']:.1f}°F"

        temperature_figure = go.Figure()
        temperature_figure.add_trace(go.Scatter(
            x=temperature_df["timestamp"],
            y=temperature_df["basking_temp"],
            name="Basking",
            mode="lines+markers",
            line={"width": 3, "color": "#8b1e2d"},
            marker={"size": 5},
            hovertemplate="%{x|%a %I:%M %p}<br>Basking: %{y:.1f}°F<extra></extra>",
        ))
        temperature_figure.add_trace(go.Scatter(
            x=temperature_df["timestamp"],
            y=temperature_df["water_temp"],
            name="Water",
            mode="lines+markers",
            line={"width": 3, "color": "#1769c2"},
            marker={"size": 5},
            hovertemplate="%{x|%a %I:%M %p}<br>Water: %{y:.1f}°F<extra></extra>",
        ))
        temperature_figure.update_layout(
            height=340,
            hovermode="x unified",
            margin={"l": 48, "r": 20, "t": 20, "b": 40},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend={"orientation": "h", "y": 1.12, "x": 0.5, "xanchor": "center"},
            xaxis={"title": None, "gridcolor": "#edf1f4"},
            yaxis={"title": "Temperature (°F)", "gridcolor": "#edf1f4"},
        )

    today = datetime.now().date()
    last_seven_days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    daily_counts = {day: 0 for day in last_seven_days}
    last_feeding = "No history yet"
    missed_days_display = "No history"

    if not feeding_df.empty:
        feeding_df["timestamp"] = pd.to_datetime(feeding_df["timestamp"])
        feeding_df = feeding_df.sort_values("timestamp")
        latest_feeding = feeding_df.iloc[-1]["timestamp"].to_pydatetime()
        elapsed = datetime.now() - latest_feeding
        if elapsed.total_seconds() < 86400:
            hours = max(0, int(elapsed.total_seconds() // 3600))
            last_feeding = "Today" if hours == 0 else f"{hours}h ago"
        else:
            last_feeding = f"{elapsed.days}d ago"

        for feeding_time in feeding_df["timestamp"]:
            feeding_day = feeding_time.date()
            if feeding_day in daily_counts:
                daily_counts[feeding_day] += 1
        missed_days = sum(count == 0 for count in daily_counts.values())
        missed_days_display = f"{missed_days} of 7"

    feeding_figure = go.Figure(go.Bar(
        x=[day.strftime("%a<br>%b %-d") for day in last_seven_days],
        y=list(daily_counts.values()),
        marker_color=[
            "#d95b5b" if count == 0 else "#2f8f5b"
            for count in daily_counts.values()
        ],
        text=list(daily_counts.values()),
        textposition="outside",
        hovertemplate="%{x}<br>Feedings: %{y}<extra></extra>",
    ))
    feeding_figure.update_layout(
        height=300,
        margin={"l": 48, "r": 20, "t": 20, "b": 40},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis={"title": None, "gridcolor": "#edf1f4"},
        yaxis={"title": "Feedings", "dtick": 1, "rangemode": "tozero", "gridcolor": "#edf1f4"},
    )

    return (
        latest_basking,
        latest_water,
        last_feeding,
        missed_days_display,
        temperature_figure,
        feeding_figure,
    )
