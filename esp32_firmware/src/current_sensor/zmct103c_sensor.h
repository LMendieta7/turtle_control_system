#ifndef ZMCT103C_SENSOR_H
#define ZMCT103C_SENSOR_H

#include <Arduino.h>
#include "ads1115/ads1115_driver.h"

class PubSubClient;
class LightManager;

class Zmct103cSensor
{
public:
    // pair: 0 => AIN0-AIN1, 1 => AIN2-AIN3
    // burdenOhms defaults to 0.5 Ω like your original code
    // thresholdA is optional; used for OK/FLT when publishing status
    Zmct103cSensor(Ads1115Driver &ads,
                   uint8_t pair,
                   const char *name,
                   float burdenOhms = 0.5f,
                   float thresholdA = 0.0f);

    // Auto-zero with lamps OFF (baseline offset in counts)
    void calibrateOffset(uint16_t samples = 100, uint16_t delayMsPerSample = 5);

    // Your original math:
    // avg(|raw - offset|) * lsbVolts / burden → amps
    float readCurrentA(uint16_t samples = 40, uint16_t delayUsPerSample = 500) const;

    // Convenience (optional) publish
    void publishOnce(PubSubClient &mqtt,
                     const LightManager &lights,
                     const char *topicCurrent,
                     const char *topicStatus) const;

    // Tweaks / accessors
    void setBurdenOhms(float ohms) { burdenOhms = ohms; }
    float getBurdenOhms() const { return burdenOhms; }
    void setThresholdA(float a) { thresholdA = a; }
    float getThresholdA() const { return thresholdA; }
    const char *getName() const { return name; }

private:
    Ads1115Driver &ads; // REQUIRED (reference)
    uint8_t pair;       // 0 or 1
    const char *name;   // label
    float burdenOhms;
    float thresholdA;
    float offsetCounts = 0.0f;

    int16_t readRawOnce_() const;
};

#endif