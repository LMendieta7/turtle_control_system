#ifndef CURRENT_SENSOR_MANAGER_H
#define CURRENT_SENSOR_MANAGER_H

#include <Arduino.h>
#include "ads1115/ads1115_driver.h"
#include "current_sensor/zmct103c_sensor.h"


// Lightweight forward declares
class PubSubClient;
class LightManager;
class FeederManager;

class CurrentSensorManager
{
public:
    explicit CurrentSensorManager(uint8_t adsAddr = 0x48);

    // Wire services + configure
    void begin(PubSubClient &mqttClient,
               LightManager &lights,
               FeederManager &feeder,
               unsigned long publishIntervalMs = 4000,
               float burdenHeat = 0.5f,
               float burdenUV = 0.5f,
               float thHeatA = 0.20f,
               float thUvA = 0.05f);

    // Non-blocking loop (call from your main loop)
    void readAndPublish();

    // Force an immediate read & publish, ignoring the interval
    void publishNow();

    // Optional tuning
    void setEnabled(bool en) { enabled = en; }
    void setAutoZeroOnLightsOff(bool en, uint32_t quietMs = 2000)
    {
        autoZero = en;
        autoZeroQuietMs = quietMs;
    }
    void setThresholds(float heatA, float uvA)
    {
        heat.setThresholdA(heatA);
        uv.setThresholdA(uvA);
    }

    // Read last values
    float lastHeatA() const { return lastHeat; }
    float lastUvA() const { return lastUv; }

private:
    // Owned hardware/sensors (no heap)
    Ads1115Driver ads;
    Zmct103cSensor heat;
    Zmct103cSensor uv;

    // Cross-services (wired in begin)
    PubSubClient *mqtt = nullptr;
    LightManager *lights = nullptr;
    FeederManager *feeder = nullptr;

    // Timing/state
    bool enabled = true;
    bool ready = false;
    unsigned long intervalMs = 4000;
    unsigned long lastRunMs = 0;

    // Auto-zero after lights OFF for a quiet period
    bool autoZero = false;
    uint32_t autoZeroQuietMs = 2000;
    bool wasLightsOn = false;
    uint32_t lightsOffSinceMs = 0;

    // Last readings
    float lastHeat = 0.0f;
    float lastUv = 0.0f;

    // soft mute when lights are off

    bool muteLightsOff = true;
    bool offAnnounced = false;

    // Internals
    void sampleAndPublish_(Zmct103cSensor &s, float &lastA,
                           const char *topicCur, const char *topicStat);
    void trackLightsForAutoZero_(unsigned long now);
};

#endif