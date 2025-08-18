#ifndef MQTT_MANAGER_H
#define MQTT_MANAGER_H

#include <Arduino.h>
#include <PubSubClient.h>
#include <functional>
#include <WiFi.h>

class MqttManager
{
public:
    void begin(const char *server, int port);
    void setCallback(MQTT_CALLBACK_SIGNATURE);
    void loop();
    void subscribe(const char *topic);
    bool isConnected();
    void reconnectIfNeeded();
    PubSubClient &getClient();
    void subscribeToTopics();

    std::function<void()> onReconnectSuccess;
    void setOnReconnectSuccess(std::function<void()> callback)
    {
        onReconnectSuccess = callback;
    }

private:
    WiFiClient wifiClient;
    PubSubClient client{wifiClient};

    const unsigned long reconnectInterval = 15000;
    unsigned long lastReconnectAttempt = 0;
};

#endif