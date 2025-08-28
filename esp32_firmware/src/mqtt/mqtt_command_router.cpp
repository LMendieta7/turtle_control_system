#include "mqtt/mqtt_command_router.h"
#include "auto_mode/auto_mode_manager.h"
#include "feeder/feeder_manager.h"
#include "lights/light_manager.h"
#include "topics.h"
#include <ArduinoJson.h>

MqttCommandRouter *MqttCommandRouter::self = nullptr;

void MqttCommandRouter::begin(PubSubClient &client,
                              AutoModeManager &autoModeRef,
                              FeederManager &feederRef,
                              LightManager &lightsRef)
{
    mqtt = &client;
    autoMode = &autoModeRef;
    feeder = &feederRef;
    lights = &lightsRef;
    self = this;
}

void MqttCommandRouter::attach()
{
    if (!mqtt)
        return;

    mqtt->setCallback(&MqttCommandRouter::bridge);
}

void MqttCommandRouter::subscribeAll()
{
    if (!mqtt)
        return;
    // ---- Option A: explicit list from topics.h (recommended for clarity) ----
    for (size_t i = 0; i < SUBSCRIBE_COUNT; ++i)
    {
        mqtt->subscribe(SUBSCRIBE_TOPICS[i]);
    }

    // ---- Option B: wildcards (comment out A if you prefer this) ----
    // mqtt->subscribe(TOPIC_ROOT "+/cmd");     // feeder/cmd, lights/cmd, auto_mode/cmd
    // mqtt->subscribe(TOPIC_ROOT "+/+/cmd");   // lights/heat/cmd, lights/uv/cmd, lights/schedule/cm
}

// static
void MqttCommandRouter::bridge(char *topic, byte *payload, unsigned int length)
{
    if (self)
        self->handle(topic, payload, length);
}

void MqttCommandRouter::handle(const char *topic, const byte *payload, unsigned int length)
{
    if (!mqtt || !autoMode || !feeder || !lights || !topic)
        return;

    const String msg = toString(payload, length);
    const String msgLower = lower(msg);
    // Serial.printf("MQTT in [%s]: %s\n", topic, msg.c_str());

    //  Feed -----------------------------------------------------------
    if (topicIs(topic, TOPIC_FEEDER_CMD))
    {
        if (autoMode->isEnabled())
        {
            Serial.println(F("Feed ignored — Auto Mode is ON"));
            return;
        }
        if (msgLower == "1" || msgLower == "feed")
        {
            feeder->runManual();
        }
        return;
    }

    //  Auto mode on/off ----------------------------------------------
    if (topicIs(topic, TOPIC_AUTO_MODE_CMD))
    {
        autoMode->setEnabled(msgLower == "on");
        return;
    }

    // Lights on/off --------------------------------------------------
    if (topicIs(topic, TOPIC_LIGHTS_CMD))
    {
        if (autoMode->isEnabled())
            return; // respect Auto Mode
        if (msgLower == "on")
        {
            lights->turnOnBoth();
        }
        else if (msgLower == "off")
        {
            lights->turnOffBoth();
        }
        return;
    }

    // heat_bulb ---------------------------------------------------------
    if (topicIs(topic, TOPIC_HEAT_CMD))
    {
        if (autoMode->isEnabled())
            return;
        if (msgLower == "on")
        {
            lights->heatOn();
        }
        else if (msgLower == "off")
        {
            lights->heatOff();
        }
        return;
    }

    // uv_bulb -----------------------------------------------------------
    if (topicIs(topic, TOPIC_UV_CMD))
    {
        if (autoMode->isEnabled())
            return;
        if (msgLower == "on")
        {
            lights->uvOn();
        }
        else if (msgLower == "off")
        {
            lights->uvOff();
        }
        return;
    }

    // reboot ------------------------------------------------------------
    if (topicIs(topic, TOPIC_REBOOT_CMD))
    {
        if (msgLower == "1" || msgLower == "now")
        {
            delay(50);
            ESP.restart();
        }
        return;
    }

    if (topicIs(topic, TOPIC_LIGHTS_SCHEDULE_CMD))
    {
        // Payload is raw bytes from PubSubClient; parse without copying
        JsonDocument doc;
        DeserializationError err = deserializeJson(doc, payload, length);
        if (!err)
        {
            const char *onStr = doc["on"] | "08:00";
            const char *offStr = doc["off"] | "18:00";

            auto toHHMM = [](const char *s) -> int
            {
                int hh = atoi(s);
                const char *c = strchr(s, ':');
                int mm = c ? atoi(c + 1) : 0;
                return hh * 100 + mm;
            };

            lights->setLightTime(toHHMM(onStr), toHHMM(offStr)); // persists to NVS + republishes retained schedule
        }
        return;
    }

    // Unknown topic → ignore
}
