#ifndef MQTT_COMMAND_ROUTER_H
#define MQTT_COMMAND_ROUTER_H

#include <Arduino.h>
#include <PubSubClient.h>

// Forward declarations
class AutoModeManager;
class FeederManager;
class LightManager;

class MqttCommandRouter
{
public:
    MqttCommandRouter() = default;

    void begin(PubSubClient &client,
               AutoModeManager &autoModeRef,
               FeederManager &feederRef,
               LightManager &lightsRef);

    // Install this router as PubSubClient's callback
    void attach();

    // Subscribe to control topics (call after connect / reconnect)
    void subscribeAll();

private:
    // PubSubClient requires a static callback → bridge into instance
    static void bridge(char *topic, byte *payload, unsigned int length);
    void handle(const char *topic, const byte *payload, unsigned int length);

    // Helpers
    static inline bool topicIs(const char *a, const char *b)
    {
        return a && b && strcmp(a, b) == 0;
    }
    static String toString(const byte *payload, unsigned int len)
    {
        String s;
        s.reserve(len);
        for (unsigned int i = 0; i < len; ++i)
            s += (char)payload[i];
        return s;
    }
    static String lower(const String &in)
    {
        String s = in;
        s.toLowerCase();
        return s;
    }

    // Deps
    PubSubClient *mqtt = nullptr;
    AutoModeManager *autoMode = nullptr;
    FeederManager *feeder = nullptr;
    LightManager *lights = nullptr;

    // Active instance pointer (one router)
    static MqttCommandRouter *self;
};

#endif // MQTT_COMMAND_ROUTER_H
