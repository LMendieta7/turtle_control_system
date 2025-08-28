#include "light_manager.h"
#include "auto_mode/auto_mode_manager.h"
#include "topics.h"
#include <ArduinoJson.h>

void LightManager::begin(PubSubClient *mqttClient, AutoModeManager *autoModeManager)
{
    client = mqttClient;
    autoMode = autoModeManager;

    pinMode(BASKING_LIGHT_PIN, OUTPUT);
    pinMode(UV_LIGHT_PIN, OUTPUT);

    digitalWrite(BASKING_LIGHT_PIN, LOW);
    digitalWrite(UV_LIGHT_PIN, LOW);

    loadScheduleFromNvs_();
    const String onS = hhmmToStr_(lightOnTime);
    const String offS = hhmmToStr_(lightOffTime);
    publishSchedule(onS.c_str(), offS.c_str());

    lightsAreOn = false;
    publishState(); // Start with known OFF state
}

void LightManager::publishCurrentSchedule()
{
    String onS = hhmmToStr_(lightOnTime);
    String offS = hhmmToStr_(lightOffTime);
    publishSchedule(onS.c_str(), offS.c_str());
}
void LightManager::updateSchedule(const DateTime &now)
{
    if (!autoMode || !autoMode->isEnabled())
    {
        return; // Only process schedule when auto mode is ON
    }

    int currentTime = now.hour() * 100 + now.minute();

    if (currentTime >= lightOnTime && currentTime < lightOffTime)
    {
        turnOnBoth(); // auto logic
    }
    else
    {
        turnOffBoth(); // auto logic
    }
}

void LightManager::turnOnBoth()
{

    heatOn();
    uvOn();
    lightsAreOn = true;
    publishState();
}

void LightManager::turnOffBoth()
{

    heatOff();
    uvOff();
    lightsAreOn = false;
    publishState();
}

void LightManager::heatOn()
{
    digitalWrite(BASKING_LIGHT_PIN, HIGH);
    heatIsOn = true;
    client->publish(TOPIC_HEAT_STATUS, "ON", true);
}

void LightManager::heatOff()
{

    digitalWrite(BASKING_LIGHT_PIN, LOW);
    heatIsOn = false;
    client->publish(TOPIC_HEAT_STATUS, "OFF", true);
}

void LightManager::uvOn()
{

    digitalWrite(UV_LIGHT_PIN, HIGH);
    uvIsOn = true;
    client->publish(TOPIC_UV_STATUS, "ON", true);
}

void LightManager::uvOff()
{

    digitalWrite(UV_LIGHT_PIN, LOW);
    uvIsOn = false;
    client->publish(TOPIC_UV_STATUS, "OFF", true);
}

bool LightManager::isOn() const
{
    return lightsAreOn;
}

void LightManager::publishState()
{
    if (!client)
        return;
    const char *state = lightsAreOn ? "ON" : "OFF";
    client->publish(TOPIC_LIGHTS_STATUS, state, true);
}

String LightManager::hhmmToStr_(int hhmm)
{
    int hh = (hhmm / 100) % 24, mm = hhmm % 100;
    char s[6];
    snprintf(s, sizeof(s), "%02d:%02d", hh, mm);
    return String(s);
}
int LightManager::clampHHMM_(int t)
{
    if (t < 0)
        t = 0;
    if (t > 2359)
        t = 2359;
    int hh = t / 100, mm = t % 100;
    if (hh > 23)
        hh = 23;
    if (mm > 59)
        mm = 59;
    return hh * 100 + mm;
}

void LightManager::publishSchedule(const char *onStr, const char *offStr)
{
    if (!client)
        return;
    JsonDocument doc;
    doc["on"] = onStr;
    doc["off"] = offStr;
    char buf[96];
    serializeJson(doc, buf, sizeof(buf));
    client->publish(TOPIC_LIGHTS_SCHEDULE, buf, true); // retained
}

void LightManager::loadScheduleFromNvs_()
{
    _prefs.begin("lights", true);                 // RO
    uint16_t on = _prefs.getUShort("on", 800);    // 07:30 default
    uint16_t off = _prefs.getUShort("off", 1800); // 19:00 default
    _prefs.end();
    lightOnTime = clampHHMM_(on);
    lightOffTime = clampHHMM_(off);
}
void LightManager::saveScheduleToNvs_() const
{
    Preferences p;
    p.begin("lights", false); // RW
    p.putUShort("on", (uint16_t)lightOnTime);
    p.putUShort("off", (uint16_t)lightOffTime);
    p.end();
}

void LightManager::setLightTime(int onTimeHHMM, int offTimeHHMM)
{
    lightOnTime = clampHHMM_(onTimeHHMM);
    lightOffTime = clampHHMM_(offTimeHHMM);
    saveScheduleToNvs_();
    const String onS = hhmmToStr_(lightOnTime);
    const String offS = hhmmToStr_(lightOffTime);
    publishSchedule(onS.c_str(), offS.c_str()); // keep Dash in sync
}
