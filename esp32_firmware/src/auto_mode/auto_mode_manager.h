#ifndef AUTO_MODE_MANAGER_H
#define AUTO_MODE_MANAGER_H

#include <Preferences.h>
#include <PubSubClient.h>

class AutoModeManager
{
public:
    void begin(PubSubClient *mqttClient);
    bool isEnabled() const;
    void setEnabled(bool enabled);
    void toggle();
    void loadFromPreferences();
    void saveToPreferences();
    void publishState();

private:
    bool autoModeEnabled = true;
    Preferences preferences;
    PubSubClient *client;
};

#endif
