#ifndef OLED_MANAGER_H
#define OLED_MANAGER_H

#include <Arduino.h>
#include <Adafruit_SSD1306.h>

// forwar decalration to keep header light
class RtcManager;
class TempSensorManager;
class FeederManager;

class OledManager {
public:
    OledManager() = default;
    //Wire dependencies

    void begin(Adafruit_SSD1306 &displayRef,
            RtcManager &rtcRef,
            TempSensorManager &tempsRef,
            FeederManager &feederRef);
    
    void loop();
    void refreshNow();

    void setUpdateInterval(unsigned long ms) {intervalMs = ms;}
    void setEnabled(bool en) {enabled = en;}
    bool isEnabled() const {return enabled;}

private:
    Adafruit_SSD1306* oled = nullptr;
    RtcManager* rtc = nullptr;
    TempSensorManager* temps = nullptr;
    FeederManager* feeder = nullptr;

    //timing
    unsigned long intervalMs = 3000;
    unsigned long lastMs = 0;
    bool enabled = true;
    bool ready = false;

    // Rendering helpers
    void render();
    static String formatTime12h(int hour24, int minute);
};

#endif 