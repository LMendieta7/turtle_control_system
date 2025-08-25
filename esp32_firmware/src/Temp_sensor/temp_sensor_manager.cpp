#include "temp_sensor_manager.h"
#include <PubSubClient.h>
#include "topics.h"

void TempSensorManager::begin(PubSubClient &mqttClient,
                              uint8_t baskingPin,
                              uint8_t waterPin,
                              unsigned long readIntervalMs,
                              unsigned long publishIntervalMs)
{
    mqtt = &mqttClient;
    basking.begin(baskingPin);
    water.begin(waterPin);
    readIntMs = readIntervalMs;
    pubIntervalMs = publishIntervalMs;
}

void TempSensorManager::updateReadings()
{
    unsigned long now = millis();

    // Kick off a new conversion every readIntervalMs
    if (!waitingForRead && (now - lastReadTick >= readIntMs))
    {
        basking.requestTemperature();
        water.requestTemperature();
        lastReadTick = now; // mark start of conversion
        waitingForRead = true;
        return;
    }

    // After the sensor's internal conversion time, capture values
    if (waitingForRead && (now - lastReadTick >= DS18B20Sensor::CONVERSION_DELAY_MS))
    {
        bool ok1 = basking.readTemperature();
        bool ok2 = water.readTemperature();
        if (ok1 && ok2)
        {
            waitingForRead = false;
            // lastReadTick remains the time we triggered the conversion,
            // which keeps the overall cadence consistent.
        }
    }
}

void TempSensorManager::publishIfDue()
{
    unsigned long now = millis();
    if (now - lastPublishTick < pubIntervalMs)
        return;

    publishNow();
    lastPublishTick = now;
}

void TempSensorManager::publishNow()
{
    // Publish whatever the latest cached temps are (even if they’re from <publishIntervalMs ago)
    mqtt->publish(TOPIC_TEMP_BASKING, String(basking.getTemperatureF()).c_str(), true);
    mqtt->publish(TOPIC_TEMP_WATER, String(water.getTemperatureF()).c_str(), true);

    // If you want to only publish when changed, track last published values here
    // and early-return when unchanged.
}

int TempSensorManager::getBaskingTemp() const { return basking.getTemperatureF(); }
int TempSensorManager::getWaterTemp() const { return water.getTemperatureF(); }
