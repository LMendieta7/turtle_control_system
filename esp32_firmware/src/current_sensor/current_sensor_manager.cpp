#include "current_sensor/current_sensor_manager.h"
#include <PubSubClient.h>
#include "lights/light_manager.h"
#include "feeder/feeder_manager.h"
#include "topics.h"

CurrentSensorManager::CurrentSensorManager(uint8_t adsAddr)
    : ads(adsAddr),
      heat(ads, 0, "Heat", 0.5f, 0.20f),
      uv(ads, 1, "UV", 0.5f, 0.05f)
{
}

void CurrentSensorManager::begin(PubSubClient &mqttClient,
                                 LightManager &lightsRef,
                                 FeederManager &feederRef,
                                 unsigned long publishIntervalMs,
                                 float burdenHeat,
                                 float burdenUV,
                                 float thHeatA,
                                 float thUvA)
{
    mqtt = &mqttClient;
    lights = &lightsRef;
    feeder = &feederRef;

    intervalMs = publishIntervalMs;

    if (!ads.begin(GAIN_EIGHT, RATE_ADS1115_128SPS))
    {
        ready = false;
        return;
    }

    heat.setBurdenOhms(burdenHeat);
    uv.setBurdenOhms(burdenUV);
    heat.setThresholdA(thHeatA);
    uv.setThresholdA(thUvA);

    // Initial auto-zero (ideally lights are OFF here)
    heat.calibrateOffset(100, 5);
    uv.calibrateOffset(100, 5);

    wasLightsOn = lights->isOn();
    if (!wasLightsOn)
    {
        lightsOffSinceMs = millis();
    }

    lastRunMs = millis();
    ready = true;
}

void CurrentSensorManager::publishNow()
{
    if (!ready || !enabled)
        return;
    if (!mqtt || !lights || !feeder)
        return;

    // Skip if feeder is running
    if (feeder->isRunning())
        return;

    // Mute when lights are OFF
    if (muteLightsOff && !lights->isOn())
    {
        if (!offAnnounced)
        {
            mqtt->publish(TOPIC_HEAT_STATUS, "OFF", true);
            mqtt->publish(TOPIC_UV_STATUS, "OFF", true);
            mqtt->publish(TOPIC_CURRENT_HEAT, "0.00", true);
            mqtt->publish(TOPIC_CURRENT_UV, "0.00", true);
            offAnnounced = true;
        }
        // no currents while OFF
        lastRunMs = millis();
        return;
    }

    sampleAndPublish_(heat, lastHeat, TOPIC_CURRENT_HEAT, TOPIC_HEAT_STATUS);
    sampleAndPublish_(uv, lastUv, TOPIC_CURRENT_UV, TOPIC_UV_STATUS);

    // Reset interval timer
    lastRunMs = millis();
}

void CurrentSensorManager::readAndPublish()
{
    if (!ready || !enabled)
        return;
    if (!mqtt || !lights || !feeder)
        return;

    const unsigned long now = millis();

    // Auto-zero logic based on lights state
    trackLightsForAutoZero_(now);

    // Safety: skip while feeder is running
    if (feeder->isRunning())
        return;

    // Mute when lights are OFF
    if (muteLightsOff && !lights->isOn())
    {
        if (!offAnnounced)
        {
            mqtt->publish(TOPIC_HEAT_STATUS, "OFF", true);
            mqtt->publish(TOPIC_UV_STATUS, "OFF", true);
            mqtt->publish(TOPIC_CURRENT_HEAT, "0.00", true);
            mqtt->publish(TOPIC_CURRENT_UV, "0.00", true);
            offAnnounced = true;
        }
        // no currents while OFF
        lastRunMs = millis();
        return;
    }

    // Timer
    if (now - lastRunMs < intervalMs)
        return;
    lastRunMs = now;

    // Read + publish both channels
    sampleAndPublish_(heat, lastHeat, TOPIC_CURRENT_HEAT, TOPIC_HEAT_STATUS);
    sampleAndPublish_(uv, lastUv, TOPIC_CURRENT_UV, TOPIC_UV_STATUS);
}

void CurrentSensorManager::sampleAndPublish_(Zmct103cSensor &s, float &lastA,
                                             const char *topicCur, const char *topicStat)
{
    lastA = s.readCurrentA();

    if (topicCur && topicCur[0])
    {
        mqtt->publish(topicCur, String(lastA, 2).c_str(), true);
    }

    if (topicStat && topicStat[0])
    {
        if (!lights->isOn())
        {
            mqtt->publish(topicStat, "OFF", true);
        }
        else
        {
            const bool ok = (lastA > s.getThresholdA());
            mqtt->publish(topicStat, ok ? "OK" : "FLT", true);
        }
    }
}

void CurrentSensorManager::trackLightsForAutoZero_(unsigned long now)
{
    const bool on = lights->isOn();

    // ON → OFF edge detection
    if (wasLightsOn && !on)
    {
        lightsOffSinceMs = now;
        offAnnounced = false;
    }

    if (!wasLightsOn && on)
    {
        offAnnounced = false;
    }

    wasLightsOn = on;

    // If lights are OFF and it's been quiet long enough, re-zero
    if (autoZero && !on)
    {
        if (lightsOffSinceMs && (now - lightsOffSinceMs >= autoZeroQuietMs))
        {
            heat.calibrateOffset(60, 3);
            uv.calibrateOffset(60, 3);
            // Prevent repeated re-zero until lights toggle again
            lightsOffSinceMs = 0;
        }
    }
}
