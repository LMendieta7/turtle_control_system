# mqtt/topics.py

TOPICS = [
    # Sensors (telemetry)
    "turtle/sensors/temp/basking",
    "turtle/sensors/temp/water",
    "turtle/sensors/current/heat",
    "turtle/sensors/current/uv",

    # Lights
    "turtle/lights/status",          # ON/OFF both bulbs
    "turtle/lights/schedule",        # JSON {"on":"HH:MM","off":"HH:MM"} (retained)
    "turtle/lights/heat/status",     # ON/OFF  individual bulb
    "turtle/lights/uv/status",       # ON/OFF individual bulb

    # Feeder
    "turtle/feeder/state",           # IDLE/RUNNING
    "turtle/feeder/count",

    # Auto mode
    "turtle/auto_mode/status",       # on/off

    # ESP / health
    "turtle/esp/ip",
    "turtle/esp/heap",
    "turtle/esp/uptime_ms",
    "turtle/esp/mqtt",
]
