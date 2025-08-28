#include "status_publisher.h"

// Keep heavy headers local to the .cpp to reduce compile dependencies:
#include "esp_system.h" // esp_get_free_heap_size
#include "esp_timer.h"  // esp_timer_get_time
#include "wifi/wifi_manager.h"
#include "mqtt/mqtt_manager.h"
#include "auto_mode/auto_mode_manager.h"
#include "feeder/feeder_manager.h"
#include "lights/light_manager.h"
#include "topics.h"

StatusPublisher::StatusPublisher(LightManager &lights,
                                 FeederManager &feeder,
                                 AutoModeManager &autoMode,
                                 MqttManager &mqtt)
    : lights_(lights),
      feeder_(feeder),
      autoMode_(autoMode),
      mqtt_(mqtt) {}

void StatusPublisher::begin(uint32_t intervalMs)
{
    intervalMs_ = intervalMs;
    lastTick_ = millis();
    prevMqttConnected_ = mqtt_.getClient().connected();
    if (prevMqttConnected_)
        publishAll_(); // initial snapshot if online
}

void StatusPublisher::update()
{
    bool nowConn = mqtt_.getClient().connected();

    // Immediate publish after reconnect
    if (nowConn && !prevMqttConnected_)
    {
        publishAll_();
        lastTick_ = millis();
    }
    prevMqttConnected_ = nowConn;

    uint32_t now = millis();
    if ((uint32_t)(now - lastTick_) >= intervalMs_)
    {
        lastTick_ = now;
        publishAll_();
    }
}

void StatusPublisher::publishNow()
{
    publishAll_();
}

void StatusPublisher::publishAll_()
{
    auto &client = mqtt_.getClient();
    if (!client.connected())
        return;

    // Lights
    {
        String v = lights_.isOn() ? "ON" : "OFF";
        client.publish(TOPIC_LIGHTS_STATUS, v.c_str(), R_LIGHTS);
    }

    // Feeder
    {
        const char *v = feeder_.isRunning() ? "RUNNING" : "IDLE";
        client.publish(TOPIC_FEEDER_STATE, v, R_FEEDER);

        String countStr(feeder_.getFeedCount());
        client.publish(TOPIC_FEEDER_COUNT, countStr.c_str(), R_FEED_COUNT);
    }

    // Auto mode
    {
        const char *v = autoMode_.isEnabled() ? "on" : "off";
        client.publish(TOPIC_AUTO_MODE_STATUS, v, R_AUTO);
    }

    // IP
    {
        String ip = WiFi.localIP().toString();
        client.publish(TOPIC_ESP_IP, ip.c_str(), R_IP);
    }

    // MQTT status echo
    {
        const char *v = client.connected() ? "connected" : "disconnected";
        client.publish(TOPIC_ESP_MQTT, v, R_MQTT);
    }

    // Heap (KB)
    {
        size_t heapBytes = esp_get_free_heap_size();
        String heapStr = String(heapBytes / 1024) + " KB";
        client.publish(TOPIC_ESP_HEAP, heapStr.c_str(), R_HEAP);
    }

    // Uptime (ms)
    {
        uint64_t uptime_ms = esp_timer_get_time() / 1000ULL;
        String upStr = String((unsigned long long)uptime_ms);
        client.publish(TOPIC_ESP_UPTIME, upStr.c_str(), R_UPTIME);
    }
}
