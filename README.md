# Turtle Control System

Turtle Control is a small monitoring and automation system for a turtle habitat. An ESP32 reads the sensors and controls the lights and feeder. A Python dashboard shows the current conditions and sends commands through MQTT.

## What it does

- Displays basking and water temperatures
- Shows ESP32, MQTT, memory, uptime, and bulb status
- Controls the heat bulb, UV bulb, and feeder
- Runs the lights on a saved daily schedule
- Tracks temperature and feeding history
- Highlights days with no recorded feeding

## Project structure

```text
esp32_firmware/   ESP32 firmware and hardware control
turtle_dash/      Python Dash dashboard and services
```

The ESP32 and dashboard communicate through MQTT. The dashboard stores temperature and feeding history in SQLite.

## Run the dashboard

From the `turtle_dash` directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:8050`.

The MQTT broker address and ESP32 network settings must match your local setup.

## Main tools

- Python and Dash
- Plotly
- MQTT
- SQLite
- ESP32

## Status

This is a personal project built for a working turtle habitat. I am continuing to improve the history views, reliability, and setup process.
