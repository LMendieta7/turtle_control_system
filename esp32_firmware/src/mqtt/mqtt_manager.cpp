#include "mqtt_manager.h"
#include "mqtt_command_router.h"

void MqttManager::begin(const char *server, int port)
{
    client.setServer(server, port);
}

void MqttManager::setCallback(MQTT_CALLBACK_SIGNATURE)
{
    client.setCallback(callback);
}

void MqttManager::loop()
{
    if (client.connected())
    {
        client.loop();
    }
}

void MqttManager::reconnectIfNeeded()
{
    if (client.connected())
        return;

    unsigned long now = millis();
    if (now - lastReconnectAttempt >= reconnectInterval)
    {
        lastReconnectAttempt = now;

        Serial.print("[MQTT] Attempting to connect...");

        if (client.connect("Esp32_Client"))
        {
            Serial.println("connected");

            if (onReconnectSuccess)
            {
                onReconnectSuccess();
            }
        }
        else
        {
            Serial.print(" failed, rc=");
            Serial.print(client.state());
            Serial.println(" — will retry");
        }

        delay(5); // short delay to avoid spam
    }
}

bool MqttManager::isConnected()
{
    return client.connected();
}

PubSubClient &MqttManager::getClient()
{
    return client;
}