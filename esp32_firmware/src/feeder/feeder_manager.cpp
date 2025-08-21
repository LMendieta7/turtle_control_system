#include "feeder_manager.h"
#include <Preferences.h>
#include "auto_mode/auto_mode_manager.h"

void FeederManager::begin(PubSubClient *mqttClient, AutoModeManager *autoModeManager)
{
    client = mqttClient;
    autoMode = autoModeManager;

    pinMode(AIN1, OUTPUT);
    pinMode(AIN2, OUTPUT);
    pinMode(PWMA, OUTPUT);
    pinMode(STBY, OUTPUT);
    pinMode(HALL_SENSOR, INPUT_PULLUP);

    attachInterrupt(digitalPinToInterrupt(HALL_SENSOR), []()
                    { feeder.handleHallSensor(); }, FALLING);

    Preferences prefs;
    prefs.begin("config", true);
    feedCount = prefs.getInt("feedCount", 0);
    prefs.end();
}

void FeederManager::update(const DateTime &now)
{
    if (autoMode && autoMode->isEnabled() && now.hour() == feedHour && now.minute() == feedMinute && !hasFedToday)
    {
        Serial.println("[Feeder] Auto scheduled feed");
        runScheduled();
        hasFedToday = true;
    }

    if (now.hour() == 0 && now.minute() == 0)
    {
        hasFedToday = false;
        feedCount = 0;
        saveFeedCount();
    }
}

void FeederManager::runScheduled()
{
    if (!motorRunning)
        startMotor();
}

void FeederManager::runManual()
{
    if (autoMode && autoMode->isEnabled())
    {
        Serial.println("[Feeder] Manual run ignored — Auto Mode is ON");
        return;
    }

    if (!motorRunning)
        startMotor();
}

void FeederManager::startMotor()
{
    Serial.println("[Feeder] Starting motor...");
    digitalWrite(STBY, HIGH);
    digitalWrite(AIN1, HIGH);
    digitalWrite(AIN2, LOW);
    analogWrite(PWMA, 130);

    motorRunning = true;
    hallTriggered = false;
    motorStartTime = millis();
    publishState("RUNNING");
}

void FeederManager::stop()
{
    analogWrite(PWMA, 0);
    digitalWrite(AIN1, LOW);
    digitalWrite(AIN2, LOW);
    digitalWrite(STBY, LOW);

    motorRunning = false;
    feedCount++;
    saveFeedCount();
    publishState("IDLE");
}

void FeederManager::handleTimeout()
{
    if (motorRunning && millis() - motorStartTime > TIMEOUT_MS)
    {
        Serial.println("[Feeder] Timeout");
        stop();
    }
}

void FeederManager::handleHallSensor()
{
    unsigned long now = millis();
    if (motorRunning && (now - lastHallTriggerTime > DEBOUNCE_MS))
    {
        hallTriggered = true;
        lastHallTriggerTime = now;
    }
}

void FeederManager::handleHallSensorTrigger()
{
    if (motorRunning && hallTriggered)
    {
        stop();
        hallTriggered = false;
    }
}

bool FeederManager::isRunning() const
{
    return motorRunning;
}

int FeederManager::getFeedCount() const
{
    return feedCount;
}

void FeederManager::setFeedTime(int hour, int minute)
{
    feedHour = hour;
    feedMinute = minute;
}

void FeederManager::publishState(const char *state)
{
    if (client)
    {
        client->publish("turtle/feeder_state", state, true);
        client->publish("turtle/feed_count", String(feedCount).c_str(), true);
    }
}

void FeederManager::saveFeedCount()
{
    Preferences prefs;
    prefs.begin("config", false);
    prefs.putInt("feedCount", feedCount);
    prefs.end();
}
