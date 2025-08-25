#include "auto_mode_manager.h"
#include "topics.h"
void AutoModeManager::begin(PubSubClient *mqttClient)
{
    client = mqttClient;
    loadFromPreferences();
    publishState();
}

bool AutoModeManager::isEnabled() const
{
    return autoModeEnabled;
}

void AutoModeManager::setEnabled(bool enabled)
{
    if (autoModeEnabled != enabled)
    {
        autoModeEnabled = enabled;
        saveToPreferences();
        publishState();
    }
}

void AutoModeManager::toggle()
{
    setEnabled(!autoModeEnabled);
}

void AutoModeManager::loadFromPreferences()
{
    preferences.begin("config", false);
    autoModeEnabled = preferences.getBool("autoMode", true);
    preferences.end();
}

void AutoModeManager::saveToPreferences()
{
    preferences.begin("config", false);
    preferences.putBool("autoMode", autoModeEnabled);
    preferences.end();
}

void AutoModeManager::publishState()
{
    if (client && client->connected())
    {
        client->publish(TOPIC_AUTO_MODE_STATUS, autoModeEnabled ? "on" : "off", true);
    }
}
