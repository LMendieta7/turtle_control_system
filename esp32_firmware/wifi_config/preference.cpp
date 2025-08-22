#include <Arduino.h>
#include <Preferences.h>

Preferences preferences;

void setup()
{
    Serial.begin(115200);

    // Initialize Preferences
    preferences.begin("wifi-creds", false);

    // Save Wi-Fi credentials
    preferences.putString("ssid", "network name here");
    preferences.putString("password", "password here");

    Serial.println("Wi-Fi credentials saved!");

    // Close Preferences
    preferences.end();
}

void loop()
{
    // Nothing to do here
}