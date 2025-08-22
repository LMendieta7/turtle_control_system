#include "oled/oled_manager.h"
#include <Fonts/FreeSans9pt7b.h>

#include "rtc/rtc_manager.h"
#include "temp_sensor/temp_sensor_manager.h"
#include "feeder/feeder_manager.h"

void OledManager::begin(Adafruit_SSD1306 &displayRef,
                        RtcManager &rtcRef,
                        TempSensorManager &tempsRef,
                        FeederManager &feederRef) {

    oled = &displayRef;
    rtc = &rtcRef;
    temps = &tempsRef;
    feeder = &feederRef;
   

    // Basic SSD1306 init is assumed already done in main.cpp (display.begin(...)).
    // We just do presentation defaults here:
    if (oled)
    {
        oled->clearDisplay();
        oled->setTextSize(1);
        oled->setTextColor(SSD1306_WHITE);
        oled->setFont(&FreeSans9pt7b); // comment if using default font
        oled->display();
    }

    lastMs = millis();
    ready = (oled && rtc && temps && feeder);

}

void OledManager::loop()
{
    if (!ready || !enabled)
        return;
    const unsigned long now = millis();
    if (now - lastMs < intervalMs)
        return;
    lastMs = now;
    render();
}

void OledManager::refreshNow()
{
    if (!ready || !enabled)
        return;
    render();
    lastMs = millis();
}

String OledManager::formatTime12h(int hour24, int minute)
{
    const bool am = (hour24 < 12);
    int h = hour24 % 12;
    if (h == 0)
        h = 12;
    String mm = (minute < 10 ? "0" : "") + String(minute);
    return String(h) + ":" + mm + (am ? " AM" : " PM");
}

void OledManager::render()
{
    if (!oled || !rtc || !temps || !feeder)
        return;

    oled->clearDisplay();

    // Time (top)
    oled->setFont(&FreeSans9pt7b);
    oled->setTextSize(1);
    oled->setCursor(25, 12);
    const int hh = rtc->getTime().hour();
    const int mm = rtc->getTime().minute();
    oled->print(formatTime12h(hh, mm));

    // Basking temp
    oled->setCursor(0, 33);
    oled->print("BT: ");
    oled->print(temps->getBaskingTemp());
    oled->print(" F");

    // Water temp + feed count
    oled->setCursor(0, 54);
    oled->print("WT: ");
    oled->print(temps->getWaterTemp());
    oled->print(" F  fc:");
    oled->print(feeder->getFeedCount());

    oled->display();
}