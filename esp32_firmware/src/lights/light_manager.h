#ifndef LIGHT_MANAGER_H
#define LIGHT_MANAGER_H

#include <Arduino.h>
#include <PubSubClient.h>
#include <RTClib.h>
#include "auto_mode/auto_mode_manager.h"

class LightManager
{
public:
    // Initialize with references to MQTT and AutoModeManager
    void begin(PubSubClient *mqttClient, AutoModeManager *autoMode);

    // Called regularly to check time and apply schedule logic
    void updateSchedule(const DateTime &now);

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
    int getOnTime() const { return lightOnTime; }
    int getOffTime() const { return lightOffTime; }

private:
    PubSubClient *client = nullptr;
    AutoModeManager *autoMode = nullptr;

    bool lightsAreOn = false;

    static constexpr int BASKING_LIGHT_PIN = 1;
    static constexpr int UV_LIGHT_PIN = 2;

    int lightOnTime = 800;   // Default: 8:00 AM
    int lightOffTime = 1800; // Default: 6:00 PM

    bool heatIsOn = false;
    bool uvIsOn = false;

    void publishState(); // MQTT publish of "turtle/lights_state"
};

#endif