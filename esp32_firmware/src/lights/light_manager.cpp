#include "light_manager.h"
#include "auto_mode/auto_mode_manager.h"

void LightManager::begin(PubSubClient *mqttClient, AutoModeManager *autoModeManager)
{
    client = mqttClient;
    autoMode = autoModeManager;

    pinMode(BASKING_LIGHT_PIN, OUTPUT);
    pinMode(UV_LIGHT_PIN, OUTPUT);

    digitalWrite(BASKING_LIGHT_PIN, LOW);
    digitalWrite(UV_LIGHT_PIN, LOW);

    lightsAreOn = false;
    publishState(); // Start with known OFF state
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
    client->publish("turtle/heat_status", heatIsOn ? "ON" : "OFF", true);
}

void LightManager::heatOff()
{

    digitalWrite(BASKING_LIGHT_PIN, LOW);
    heatIsOn = false;
}

void LightManager::uvOn()
{

    digitalWrite(UV_LIGHT_PIN, HIGH);
    uvIsOn = true;
    client->publish("turtle/uv_status", uvIsOn ? "ON" : "OFF", true);
}

void LightManager::uvOff()
{

    digitalWrite(UV_LIGHT_PIN, LOW);
    uvIsOn = false;
}

bool LightManager::isOn() const
{
    return lightsAreOn;
}

void LightManager::setLightTime(int onTimeHHMM, int offTimeHHMM)
{
    lightOnTime = onTimeHHMM;
    lightOffTime = offTimeHHMM;
}

void LightManager::publishState()
{
    if (!client)
        return;
    const char *state = lightsAreOn ? "ON" : "OFF";
    client->publish("turtle/lights_state", state, true);
}
