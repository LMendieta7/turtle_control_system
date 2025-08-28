#ifndef STATUS_PUBLISHER_H
#define STATUS_PUBLISHER_H

#include <Arduino.h>
#include <WiFi.h>

// Forward declares to avoid pulling heavy headers into every includer:
class LightManager;
class FeederManager;
class AutoModeManager;
class MqttManager;

class StatusPublisher
{
public:
    StatusPublisher(LightManager &lights,
                    FeederManager &feeder,
                    AutoModeManager &autoMode,
                    MqttManager &mqtt);

    // Set cadence and push an initial snapshot if already connected
    void begin(uint32_t intervalMs = 7000);

    // Call from loop()
    void update();

    // Optional: push immediately (e.g., on state change or MQTT reconnect)
    void publishNow();

    // Change interval at runtime
    void setInterval(uint32_t ms) { intervalMs_ = ms; }

private:
    void publishAll_();

    // Retained flags
    static constexpr bool R_LIGHTS = true;
    static constexpr bool R_FEEDER = false;
    static constexpr bool R_AUTO = true;
    static constexpr bool R_FEED_COUNT = true;
    static constexpr bool R_IP = true;
    static constexpr bool R_MQTT = true;
    static constexpr bool R_HEAP = true;
    static constexpr bool R_UPTIME = true;

    LightManager &lights_;
    FeederManager &feeder_;
    AutoModeManager &autoMode_;
    MqttManager &mqtt_;

    uint32_t intervalMs_ = 7000;
    uint32_t lastTick_ = 0;
    bool prevMqttConnected_ = false;
};
#endif