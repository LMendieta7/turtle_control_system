#ifndef DS18B20_SENSOR_H
#define DS18B20_SENSOR_H

#include <Arduino.h>
#include <DallasTemperature.h>
#include <OneWire.h>

class DS18B20Sensor
{
public:
    // name is useful for logs/MQTT if you ever need it
    DS18B20Sensor(const String &name);

    // Call once with the GPIO pin the sensor is connected to
    void begin(uint8_t pin);

    // Start a conversion (non-blocking). Safe to call repeatedly; it will self-guard.
    void requestTemperature();

    // After CONVERSION_DELAY_MS, call this to capture the reading.
    // Returns true once a new reading was taken.
    bool readTemperature();

    // Latest cached result (°F, rounded to int)
    int getTemperatureF() const;
    String getName() const;

    // Public so a manager can reference the delay
    static constexpr unsigned long CONVERSION_DELAY_MS = 750;

private:
    uint8_t dataPin = 0;
    String sensorName;

    OneWire *oneWire = nullptr;        // allocated in begin()
    DallasTemperature sensor{nullptr}; // bound to oneWire in begin()

    int temperatureF = 0;
    bool waiting = false;
    unsigned long requestTime = 0;
};

#endif // DS18B20_SENSOR_H
