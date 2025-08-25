#include <Arduino.h>
#include <ArduinoOTA.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "wifi/wifi_manager.h"
#include "mqtt/mqtt_manager.h"
#include "auto_mode/auto_mode_manager.h"
#include "feeder/feeder_manager.h"
#include "rtc/rtc_manager.h"
#include "lights/light_manager.h"
#include "temp_sensor/temp_sensor_manager.h"
#include "current_sensor/current_sensor_manager.h"
#include "status/status_publisher.h"
#include "oled/oled_manager.h"
#include "mqtt/mqtt_command_router.h"

// OLED display dimensions
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

CurrentSensorManager currents;
TempSensorManager tempSensors;

AutoModeManager autoMode;
RtcManager rtc;

WiFiManager wifi;
MqttManager mqtt;

FeederManager feeder;
LightManager lights;
OledManager oled;
MqttCommandRouter cmdRouter;

StatusPublisher statusPub(lights, feeder, autoMode, mqtt);

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

void initOled()
{
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C))
  {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;)
      ; // halt
  }
  display.clearDisplay();
  display.display();
}

void setup()
{
  // Start Serial Monitor
  // Serial.begin(9600);
  Wire.begin();
  rtc.begin();
  esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_ALL);

  // Initialize components
  feeder.begin(&mqtt.getClient(), &autoMode);
  autoMode.begin(&mqtt.getClient());
  lights.begin(&mqtt.getClient(), &autoMode);
  tempSensors.begin(mqtt.getClient(),
                    /* baskin pin*/ 4,
                    /* uv pin */ 5,
                    /* read interval */ 3000,
                    /* publish interval */ 5000);
  wifi.begin();

  currents.begin(
      mqtt.getClient(),
      lights,
      feeder,
      /*publishIntervalMs=*/7000,
      /*burdenHeat=*/0.50f,
      /*burdenUV=*/0.50f,
      /*thHeatA=*/0.20f,
      /*thUvA=*/0.05f);

  // currents.setAutoZeroOnLightsOff(true);

  statusPub.begin(5000); // publish every 5s
  //  Setup MQTT
  mqtt.begin("172.22.80.5", 1883);
  cmdRouter.begin(mqtt.getClient(), autoMode, feeder, lights);
  cmdRouter.attach();
  mqtt.setOnReconnectSuccess([&]()
                             {
                               cmdRouter.subscribeAll();
                               statusPub.publishNow();
                               tempSensors.publishNow(); // push temps immediately on reconnect
                             });
  mqtt.reconnectIfNeeded();
  
  // init oled
  initOled();
  oled.begin(display, rtc, tempSensors, feeder);
  oled.setUpdateInterval(3000); // 3 seconds
  oled.refreshNow();            // draw immediately at boot

  ArduinoOTA.begin();
  delay(1000);
}

void loop()
{
  ArduinoOTA.handle();
  rtc.update();
  DateTime now = rtc.getTime();

  feeder.handleHallSensorTrigger();

  if (wifi.isConnected())

  {
    mqtt.reconnectIfNeeded(); //  Only try if Wi-Fi is okay
    mqtt.loop();
    delay(5);
  }

  // handleTimeSync();
  feeder.handleTimeout();
  feeder.update(now);

  lights.updateSchedule(now);

  oled.loop();

  currents.readAndPublish();

  tempSensors.updateReadings();
  tempSensors.publishIfDue();

  statusPub.update();
}
