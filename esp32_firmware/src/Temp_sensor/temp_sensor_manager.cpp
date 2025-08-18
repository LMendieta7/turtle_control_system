#include "temp_sensor_manager.h"

void TempSensorManager::begin(uint8_t baskingPin, uint8_t waterPin)
{
    basking.begin(baskingPin);
    water.begin(waterPin);
}

void TempSensorManager::updateReadings(unsigned long readIntervalMs)
{
    unsigned long now = millis();

    // Kick off a new conversion every readIntervalMs
    if (!waitingForRead && (now - lastReadTick >= readIntervalMs))
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

void TempSensorManager::publishIfDue(unsigned long publishIntervalMs, PubSubClient *mqtt)
{
    unsigned long now = millis();
    if (now - lastPublishTick < publishIntervalMs)
        return;

    publishNow(mqtt);
    lastPublishTick = now;
}

void TempSensorManager::publishNow(PubSubClient *mqtt)
{
    // Publish whatever the latest cached temps are (even if they’re from <publishIntervalMs ago)
    mqtt->publish("turtle/basking_temperature", String(basking.getTemperatureF()).c_str(), true);
    mqtt->publish("turtle/water_temperature", String(water.getTemperatureF()).c_str(), true);

    // If you want to only publish when changed, track last published values here
    // and early-return when unchanged.
}

int TempSensorManager::getBaskingTemp() const { return basking.getTemperatureF(); }
int TempSensorManager::getWaterTemp() const { return water.getTemperatureF(); }
