#ifndef TEMP_SENSOR_MANAGER_H
#define TEMP_SENSOR_MANAGER_H

#include <PubSubClient.h>
#include "ds18b20_sensor.h"

class TempSensorManager
{
public:
    // Provide pins for each DS18B20
    void begin(uint8_t baskingPin, uint8_t waterPin);

    // 1) Refresh readings on your chosen cadence (non-blocking)
    void updateReadings(unsigned long readIntervalMs);

    // 2) Publish latest cached readings if publish interval elapsed
    void publishIfDue(unsigned long publishIntervalMs, PubSubClient *mqtt);

    // 3) Publish immediately (e.g., after MQTT reconnect)
    void publishNow(PubSubClient *mqtt);

    // Accessors for OLED/UI
    int getBaskingTemp() const;
    int getWaterTemp() const;

private:
    DS18B20Sensor basking{"basking"};
    DS18B20Sensor water{"water"};

    // Reading cadence
    unsigned long lastReadTick = 0;
    bool waitingForRead = false;

    // Publish cadence
    unsigned long lastPublishTick = 0;

    // Optional: cache last published values if you want "publish on change" later
    // int lastPubBasking = INT_MIN;
    // int lastPubWater   = INT_MIN;
};

#endif // TEMP_SENSOR_MANAGER_H
