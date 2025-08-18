#include "rtc_manager.h"
#include <time.h>
#include <Arduino.h>

void RtcManager::begin()
{
    if (!rtc.begin())
    {
        Serial.println("Couldn't find RTC");
        while (1)
            ;
    }

    if (rtc.lostPower())
    {
        Serial.println("[RTC] Lost power, syncing from NTP...");
        syncFromNTP();
    }

    syncFromNTP();
    currentTime = rtc.now();
    lastSync = millis();
}

void RtcManager::update()
{
    currentTime = rtc.now();

    if (millis() - lastSync >= syncInterval)
    {
        Serial.println("[RTC] Syncing from NTP...");
        syncFromNTP();
        lastSync = millis();
    }
}

DateTime RtcManager::getTime() const
{
    return currentTime;
}

void RtcManager::syncFromNTP()
{
    configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo))
    {
        Serial.println("[RTC] Failed to sync from NTP");
        return;
    }

    rtc.adjust(DateTime(timeinfo.tm_year + 1900, timeinfo.tm_mon + 1,
                        timeinfo.tm_mday, timeinfo.tm_hour,
                        timeinfo.tm_min, timeinfo.tm_sec));
}
