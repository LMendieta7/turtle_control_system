#ifndef TOPICS_H
#define TOPICS_H

// ==============================
// MQTT Topic Map (Scalable)
// ==============================
//
// Root namespace: change once here to rename everything (e.g., "turtle/" or "turtle/tank1/").
// Use trailing slash!
#define TOPIC_ROOT "turtle/"

// ------------------------------
// Sensors (telemetry only)
// ------------------------------
// Temperatures
#define TOPIC_TEMP_BASKING TOPIC_ROOT "sensors/temp/basking" // float/number
#define TOPIC_TEMP_WATER TOPIC_ROOT "sensors/temp/water"     // float/number

// Currents (for devices that draw power)
#define TOPIC_CURRENT_HEAT TOPIC_ROOT "sensors/current/heat" // float/number (amps)
#define TOPIC_CURRENT_UV TOPIC_ROOT "sensors/current/uv"     // float/number (amps)

#define TOPIC_CURRENT_HEAT_STATUS TOPIC_ROOT "sensors/current/heat/status"  //  "OK"/"FLT"
#define TOPIC_CURRENT_UV_STATUS TOPIC_ROOT "sensors/current/uv/status"  //  "OK"/"FLT"
// (Add more later, e.g.)
// #define TOPIC_CURRENT_PUMP    TOPIC_ROOT "sensors/current/pump"
// #define TOPIC_HUMIDITY_AIR    TOPIC_ROOT "sensors/humidity/air"

// ------------------------------
// Lights (device state + control)
// ------------------------------
#define TOPIC_LIGHTS_STATUS TOPIC_ROOT "lights/status"             // "ON"/"OFF" (retained)
#define TOPIC_LIGHTS_CMD TOPIC_ROOT "lights/cmd"                   // "ON"/"OFF" (manual override)
#define TOPIC_LIGHTS_SCHEDULE TOPIC_ROOT "lights/schedule"         // JSON {"on":"HH:MM","off":"HH:MM"} (retained)
#define TOPIC_LIGHTS_SCHEDULE_CMD TOPIC_ROOT "lights/schedule/cmd" // JSON {"on":"HH:MM","off":"HH:MM"}

// Optional per‑channel states
// Per-channel
#define TOPIC_HEAT_STATUS TOPIC_ROOT "lights/heat/status"
#define TOPIC_HEAT_CMD TOPIC_ROOT "lights/heat/cmd"
#define TOPIC_UV_STATUS TOPIC_ROOT "lights/uv/status"
#define TOPIC_UV_CMD TOPIC_ROOT "lights/uv/cmd"

// ------------------------------
// Feeder (device state + control)
// ------------------------------
#define TOPIC_FEEDER_STATE TOPIC_ROOT "feeder/state" // "IDLE"/"RUNNING" (retained)
#define TOPIC_FEEDER_COUNT TOPIC_ROOT "feeder/count" // integer (retained)
#define TOPIC_FEEDER_CMD TOPIC_ROOT "feeder/cmd"     // "feed" or "1"

// ------------------------------
// Auto Mode (mode state + control)
// ------------------------------
#define TOPIC_AUTO_MODE_STATUS TOPIC_ROOT "auto_mode/status" // "on"/"off" (retained)
#define TOPIC_AUTO_MODE_CMD TOPIC_ROOT "auto_mode/cmd"       // "on"/"off"

// ------------------------------
// ESP / Health (telemetry only)
// ------------------------------
#define TOPIC_ESP_IP TOPIC_ROOT "esp/ip"            // "192.168.x.x" (retained)
#define TOPIC_ESP_HEAP TOPIC_ROOT "esp/heap"        // integer bytes
#define TOPIC_ESP_UPTIME TOPIC_ROOT "esp/uptime_ms" // integer ms
#define TOPIC_ESP_MQTT TOPIC_ROOT "esp/mqtt"        // "connected"/"reconnected"/...
#define TOPIC_REBOOT_CMD TOPIC_ROOT "reboot/cmd"

// (Optional) RTC/time control endpoints if you want them later:
// #define TOPIC_RTC_TIME        TOPIC_ROOT "rtc/time"               // publish current HH:MM:SS (retained)
// #define TOPIC_RTC_SYNC_CMD    TOPIC_ROOT "rtc/sync/cmd"           // trigger NTP sync

// ── Group: commands to SUBSCRIBE to (UI → ESP) ───────────────────────
static const char *const SUBSCRIBE_TOPICS[] = {
    TOPIC_LIGHTS_CMD,
    TOPIC_LIGHTS_SCHEDULE_CMD,
    TOPIC_HEAT_CMD,
    TOPIC_UV_CMD,
    TOPIC_FEEDER_CMD,
    TOPIC_AUTO_MODE_CMD
    // , TOPIC_REBOOT_CMD
};
static const size_t SUBSCRIBE_COUNT =
    sizeof(SUBSCRIBE_TOPICS) / sizeof(SUBSCRIBE_TOPICS[0]);

// (Optional) Wildcards; use these instead of the list above if you prefer
static const char *const SUBSCRIBE_WILDCARDS[] = {
    TOPIC_ROOT "+/cmd",  // feeder/cmd, lights/cmd, auto_mode/cmd
    TOPIC_ROOT "+/+/cmd" // lights/heat/cmd, lights/uv/cmd, lights/schedule/cmd
};
static const size_t SUBSCRIBE_WILDCARDS_COUNT =
    sizeof(SUBSCRIBE_WILDCARDS) / sizeof(SUBSCRIBE_WILDCARDS[0]);

#endif // TOPICS_H
