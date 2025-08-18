#include "ds18b20_sensor.h"

DS18B20Sensor::DS18B20Sensor(const String &name)
    : sensorName(name) {}

void DS18B20Sensor::begin(uint8_t pin)
{
    dataPin = pin;
    oneWire = new OneWire(dataPin); // allocate bus on this pin
    sensor.setOneWire(oneWire);
    sensor.begin();
    sensor.setWaitForConversion(false); // non-blocking conversions
}

void DS18B20Sensor::requestTemperature()
{
    if (!waiting)
    {
        sensor.requestTemperatures(); // triggers async conversion
        requestTime = millis();
        waiting = true;
    }
}

bool DS18B20Sensor::readTemperature()
{
    if (!waiting)
        return false;

    if (millis() - requestTime >= CONVERSION_DELAY_MS)
    {
        // Read °F and round to int (keeps your existing topic format)
        temperatureF = static_cast<int>(round(sensor.getTempFByIndex(0)));
        waiting = false;
        return true;
    }
    return false;
}

int DS18B20Sensor::getTemperatureF() const
{
    return temperatureF;
}

String DS18B20Sensor::getName() const
{
    return sensorName;
}
