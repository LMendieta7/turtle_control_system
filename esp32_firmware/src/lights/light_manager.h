#ifndef LIGHT_MANAGER_H
#define LIGHT_MANAGER_H

#include <Arduino.h>
#include <PubSubClient.h>
#include <RTClib.h>
#include <Preferences.h>

class AutoModeManager;

class LightManager
{
public:
    // Initialize with references to MQTT and AutoModeManager
    void begin(PubSubClient *mqttClient, AutoModeManager *autoMode);

    // Called regularly to check time and apply schedule logic
    void updateSchedule(const DateTime &now);

    void publishSchedule(const char *onStr, const char *offStr);
    void publishCurrentSchedule();
    // Manual controls for both lights
    void turnOnBoth();
    void turnOffBoth();

    // Manual controls for individual lights
    void heatOn();
    void heatOff();
    void uvOn();
    void uvOff();

    // Light state query
    bool isOn() const;

    bool isHeatOn() const { return heatIsOn; }
    bool isUVOn() const { return uvIsOn; }

    // Configure the light ON and OFF times (HHMM format)
    void setLightTime(int onTimeHHMM, int offTimeHHMM);
    int getOnHHMM() const { return lightOnTime; }
    int getOffHHMM() const { return lightOffTime; }

private:
    PubSubClient *client = nullptr;
    AutoModeManager *autoMode = nullptr;

    bool lightsAreOn = false;

    static constexpr int BASKING_LIGHT_PIN = 1;
    static constexpr int UV_LIGHT_PIN = 2;

    int lightOnTime = 800;   // Default: 8:00 AM
    int lightOffTime = 1800; // Default: 6:00 PM
    void publishState();

    void loadScheduleFromNvs_();
    void saveScheduleToNvs_() const;
    static String hhmmToStr_(int hhmm);
    static int clampHHMM_(int hhmm);

    Preferences _prefs;

    bool heatIsOn = false;
    bool uvIsOn = false;

     // MQTT publish of "turtle/lights_state"
};

#endif