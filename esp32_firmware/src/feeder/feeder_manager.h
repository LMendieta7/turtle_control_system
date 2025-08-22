#ifndef FEEDER_MANAGER_H
#define FEEDER_MANAGER_H

#include <Arduino.h>
#include <PubSubClient.h>
#include <RTClib.h>

class AutoModeManager;

class FeederManager
{
public:
    void begin(PubSubClient *mqttClient, AutoModeManager *autoMode);
    void update(const DateTime &now);
    void runScheduled();
    void runManual();
    void stop();
    void handleTimeout();
    void handleHallSensor();
    void handleHallSensorTrigger();
    void setFeedTime(int hour, int minute);
    bool isRunning() const;
    int getFeedCount() const;

private:
    PubSubClient *client = nullptr;
    AutoModeManager *autoMode = nullptr;

    static constexpr int AIN1 = 16;
    static constexpr int AIN2 = 18;
    static constexpr int PWMA = 15;
    static constexpr int STBY = 21;
    static constexpr int HALL_SENSOR = 12;

    const unsigned long TIMEOUT_MS = 13000;
    const unsigned long DEBOUNCE_MS = 100;

    bool motorRunning = false;
    volatile bool hallTriggered = false;

    int feedHour = 9;
    int feedMinute = 20;
    bool hasFedToday = false;
    int feedCount = 0;

    unsigned long motorStartTime = 0;
    unsigned long lastHallTriggerTime = 0;
    void publishState(const char *state);
    void saveFeedCount();
    void startMotor();
};

extern FeederManager feeder;
#endif
