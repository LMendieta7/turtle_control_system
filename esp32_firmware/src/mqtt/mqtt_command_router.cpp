#include "mqtt/mqtt_command_router.h"
#include "auto_mode/auto_mode_manager.h"
#include "feeder/feeder_manager.h"
#include "lights/light_manager.h"

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

    // build topics from current prefix
    tFeed = prefix + "feed";
    tAutoMode = prefix + "auto_mode";
    tLights = prefix + "lights";
    tHeatBulb = prefix + "heat_bulb";
    tUvBulb = prefix + "uv_bulb";
    tReboot = prefix + "reboot";
}

void MqttCommandRouter::setTopicPrefix(const char *pfx)
{
    if (!pfx || !*pfx)
        return;
    prefix = pfx;
    if (prefix.length() && prefix[prefix.length() - 1] != '/')
        prefix += '/';

    // rebuild topics
    tFeed = prefix + "feed";
    tAutoMode = prefix + "auto_mode";
    tLights = prefix + "lights";
    tHeatBulb = prefix + "heat_bulb";
    tUvBulb = prefix + "uv_bulb";
    tReboot = prefix + "reboot";
}

void MqttCommandRouter::attach()
{
    if (!mqtt)
        return;
    self = this;
    mqtt->setCallback(&MqttCommandRouter::bridge);
}

void MqttCommandRouter::subscribeAll()
{
    if (!mqtt)
        return;
    mqtt->subscribe(tFeed.c_str());
    mqtt->subscribe(tAutoMode.c_str());
    mqtt->subscribe(tLights.c_str());
    mqtt->subscribe(tHeatBulb.c_str());
    mqtt->subscribe(tUvBulb.c_str());
    mqtt->subscribe(tReboot.c_str());
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
    if (topicIs(topic, tFeed.c_str()))
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
    if (topicIs(topic, tAutoMode.c_str()))
    {
        autoMode->setEnabled(msgLower == "on");
        return;
    }

    // Lights on/off --------------------------------------------------
    if (topicIs(topic, tLights.c_str()))
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
    if (topicIs(topic, tHeatBulb.c_str()))
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
    if (topicIs(topic, tUvBulb.c_str()))
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
    if (topicIs(topic, tReboot.c_str()))
    {
        if (msgLower == "1" || msgLower == "now")
        {
            delay(50);
            ESP.restart();
        }
        return;
    }

    // Unknown topic → ignore
}
