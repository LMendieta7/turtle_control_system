#include "ads1115/ads1115_driver.h"

Ads1115Driver::Ads1115Driver(uint8_t i2cAddr): addr(i2cAddr), currentGain(GAIN_TWOTHIRDS), currentDataRate(RATE_ADS1115_128SPS){}

bool Ads1115Driver::begin(adsGain_t gain, uint16_t dataRate)
{
    // Ensure Wire.begin() runs in your setup before calling this if needed
    if (!ads.begin(addr))
        return false;
    setGain(gain);
    setDataRate(dataRate);
    return true;
}

void Ads1115Driver::setGain(adsGain_t gain)
{
    currentGain = gain;
    ads.setGain(gain);
}

void Ads1115Driver::setDataRate(uint16_t dataRate)
{
    currentDataRate = dataRate;
    ads.setDataRate(dataRate);
}

int16_t Ads1115Driver::readDiffPair(uint8_t pair) const
{
    // Adafruit API read methods are non-const; const_cast is OK here
    switch (pair)
    {
    case 0:
        return const_cast<Adafruit_ADS1115 &>(ads).readADC_Differential_0_1();
    case 1:
        return const_cast<Adafruit_ADS1115 &>(ads).readADC_Differential_2_3();
    default:
        return 0;
    }
}

float Ads1115Driver::lsbVolts() const
{
    // Full-scale / 32768 (signed 16-bit)
    switch (currentGain)
    {
    case GAIN_TWOTHIRDS:
        return 6.144f / 32768.0f;
    case GAIN_ONE:
        return 4.096f / 32768.0f;
    case GAIN_TWO:
        return 2.048f / 32768.0f;
    case GAIN_FOUR:
        return 1.024f / 32768.0f;
    case GAIN_EIGHT:
        return 0.512f / 32768.0f; // ≈ 15.625 µV/LSB
    case GAIN_SIXTEEN:
        return 0.256f / 32768.0f;
    default:
        return 2.048f / 32768.0f;
    }
}