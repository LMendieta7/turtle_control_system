#include "wifi_manager.h"
#include <Preferences.h>

void WiFiManager::begin()
{
    Preferences preferences;
    preferences.begin("wifi-creds", true);
    ssid = preferences.getString("ssid", "");
    password = preferences.getString("password", "");
    preferences.end();

    if (ssid.isEmpty() || password.isEmpty())
    {
        Serial.println("[WiFi] No credentials found in NVS");
        return;
    }

    WiFi.onEvent([](arduino_event_id_t event, arduino_event_info_t info)
                 {
        if (event == ARDUINO_EVENT_WIFI_STA_CONNECTED) {
            Serial.println("[WiFi] Connected to AP");
        } else if (event == ARDUINO_EVENT_WIFI_STA_GOT_IP) {
            Serial.print("[WiFi] Got IP: ");
            Serial.println(WiFi.localIP());
        } else if (event == ARDUINO_EVENT_WIFI_STA_DISCONNECTED) {
            Serial.println("[WiFi] Disconnected, retrying...");
            WiFi.reconnect();
        } });

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid.c_str(), password.c_str());

    Serial.print("[WiFi] Connecting to ");
    Serial.println(ssid);
}

String WiFiManager::getSSID() const
{
    return ssid;
}

String WiFiManager::getPassword() const
{
    return password;
}

String WiFiManager::getIP() const
{
    return WiFi.localIP().toString();
}

bool WiFiManager::isConnected() const
{
    return WiFi.status() == WL_CONNECTED;
}