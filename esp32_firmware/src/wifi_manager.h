#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <Arduino.h>
#include <WiFi.h>

class WiFiManager
{
public:
    void begin();
    String getSSID() const;
    String getPassword() const;
    String getIP() const;
    bool isConnected() const;

private:
    String ssid;
    String password;
};

#endif
