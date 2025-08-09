#ifndef RTC_MANAGER_H
#define RTC_MANAGER_H

#include <RTClib.h>

class RtcManager
{
public:
    void begin();
    void update();            // Sync NTP every few hours
    DateTime getTime() const; // Get latest RTC time

private:
    RTC_DS3231 rtc;
    DateTime currentTime;

    const char *ntpServer = "pool.ntp.org";
    const long gmtOffset_sec = -5 * 3600;
    const int daylightOffset_sec = 3600;

    unsigned long lastSync = 0;
    const unsigned long syncInterval = 3UL * 60 * 60 * 1000; // 3 hours

    void syncFromNTP(); // Internal use
};

#endif
