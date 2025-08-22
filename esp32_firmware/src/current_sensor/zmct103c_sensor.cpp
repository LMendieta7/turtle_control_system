#include "current_sensor/zmct103c_sensor.h"
#include <PubSubClient.h>
#include "lights/light_manager.h"

Zmct103cSensor::Zmct103cSensor(Ads1115Driver &ads,
                               uint8_t pair,
                               const char *name,
                               float burdenOhms,
                               float thresholdA)
    : ads(ads), pair(pair), name(name),
      burdenOhms(burdenOhms), thresholdA(thresholdA)
{
    // Ensure intended gain for CT + burden (±0.512 V recommended here)
    ads.setGain(GAIN_EIGHT);
}

void Zmct103cSensor::calibrateOffset(uint16_t samples, uint16_t delayMsPerSample)
{
    long sum = 0;
    for (uint16_t i = 0; i < samples; ++i)
    {
        sum += readRawOnce_();
        delay(delayMsPerSample);
    }
    offsetCounts = float(sum) / float(samples);
}

float Zmct103cSensor::readCurrentA(uint16_t samples, uint16_t delayUsPerSample) const
{
    long sumAbsDev = 0;
    for (uint16_t i = 0; i < samples; ++i)
    {
        const int16_t raw = readRawOnce_();
        sumAbsDev += abs(raw - int16_t(offsetCounts));
        delayMicroseconds(delayUsPerSample);
    }
    const float avgCounts = float(sumAbsDev) / float(samples);
    const float volts = avgCounts * ads.lsbVolts(); // across burden
    return volts / burdenOhms;                      // I = V / R
}

void Zmct103cSensor::publishOnce(PubSubClient &mqtt,
                                 const LightManager &lights,
                                 const char *topicCurrent,
                                 const char *topicStatus) const
{
    const float amps = readCurrentA();
    if (topicCurrent && topicCurrent[0])
    {
        mqtt.publish(topicCurrent, String(amps, 2).c_str(), true);
    }
    if (topicStatus && topicStatus[0])
    {
        if (!lights.isOn())
        {
            mqtt.publish(topicStatus, "OFF", true);
        }
        else
        {
            mqtt.publish(topicStatus, (amps > thresholdA) ? "OK" : "FLT", true);
        }
    }
}

int16_t Zmct103cSensor::readRawOnce_() const
{
    return ads.readDiffPair(pair); // 0 => AIN0-1, 1 => AIN2-3
}
