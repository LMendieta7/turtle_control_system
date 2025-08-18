#ifndef ADS1115_DRIVER_H
#define ADS1115_DRIVER_H

#include <Arduino.h>
#include <Adafruit_ADS1X15.h>

class Ads1115Driver {
    public:
        explicit Ads1115Driver(uint8_t i2cAddr = 0x48);
        // Initialize the chip; returns false if not found on I2C
        bool begin(adsGain_t gain = GAIN_EIGHT, uint16_t dataRate = RATE_ADS1115_128SPS);

        // Change gain / data rate at runtime (optional)
        void setGain(adsGain_t gain);
        adsGain_t getGain() const { return currentGain; }
        void setDataRate(uint16_t dataRate);

        // Differential pairs: 0 => AIN0-AIN1, 1 => AIN2-AIN3
        int16_t readDiffPair(uint8_t pair) const;

        // Volts per LSB for current gain setting
        float lsbVolts() const;

    private:
        Adafruit_ADS1115 ads;
        uint8_t addr;
        adsGain_t currentGain;
        uint16_t currentDataRate;
};

#endif