#include <Arduino.h>
#include <ArduinoOTA.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Fonts/FreeSans9pt7b.h> // Include a font for OLED display
#include "esp_system.h"
#include "wifi/wifi_manager.h"
#include "mqtt/mqtt_manager.h"
#include "auto_mode/auto_mode_manager.h"
#include "feeder/feeder_manager.h"
#include "rtc/rtc_manager.h"
#include "lights/light_manager.h"
#include "temp_sensor/temp_sensor_manager.h"
#include "current_sensor/current_sensor_manager.h"

CurrentSensorManager currents;
TempSensorManager tempSensors;

AutoModeManager autoMode;
RtcManager rtc;

WiFiManager wifi;
MqttManager mqtt;

FeederManager feeder;
LightManager lights;

// OLED display dimensions
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

// Initialize OLED display
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

unsigned long lastOledUpdate;
const unsigned long oledUpInterval = 3000;

unsigned long lastStatusPublish = 0;
const unsigned long statusPublishInterval = 5000;

// prototype

uint32_t getFreeHeap();

void publishStatus()
{
  // Read only the basking pin for combined light state
  String lightStatus = lights.isOn() ? "ON" : "OFF";
  mqtt.getClient().publish("turtle/lights_state", lightStatus.c_str(), true);

  // Feeder status
  const char *feederStatus = feeder.isRunning() ? "RUNNING" : "IDLE";
  mqtt.getClient().publish("turtle/feeder_state", feederStatus);

  // Auto mode status
  mqtt.getClient().publish("turtle/auto_mode_state", autoMode.isEnabled() ? "on" : "off", true);

  mqtt.getClient().publish("turtle/feed_count", String(feeder.getFeedCount()).c_str(), true);

  // publish current IP
  String ip = WiFi.localIP().toString();
  mqtt.getClient().publish("turtle/esp_ip", ip.c_str(), true);

  // mqtt status
  const char *mqttStatus = mqtt.getClient().connected() ? "connected" : "disconnected";
  mqtt.getClient().publish("turtle/esp_mqtt", mqttStatus, true);

  String heapStr = String(getFreeHeap() / 1024) + " KB";
  mqtt.getClient().publish("turtle/heap", heapStr.c_str(), true);

  // Publish  uptime in ms
  uint64_t uptime_ms = esp_timer_get_time() / 1000; // convert microseconds to milliseconds
  mqtt.getClient().publish("turtle/esp_uptime_ms", String(uptime_ms).c_str(), true);
}

// Get free heap (available RAM)
uint32_t getFreeHeap()
{
  return esp_get_free_heap_size();
}

// Function to initialize OLED
void initializeOLED()
{
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C))
  { // Change 0x3C to your OLED's I2C address if different
    Serial.println(F("SSD1306 allocation failed"));
    for (;;)
      ;
  }
  // display.display();
  // delay(2000);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
}

// Function to format time in 12-hour format
String formatTime12Hour(int hour, int minute)
{
  String period = (hour < 12) ? " AM" : " PM";
  hour = hour % 12;
  if (hour == 0)
    hour = 12; // Convert 0 to 12 for 12-hour format
  return String(hour) + ":" + (minute < 10 ? "0" : "") + String(minute) + period;
}

void OledDisplayUpdate()
{
  display.clearDisplay();
  display.setFont(&FreeSans9pt7b);

  display.setCursor(25, 12);
  display.print(formatTime12Hour(rtc.getTime().hour(), rtc.getTime().minute()));

  display.setCursor(0, 33);
  display.print("BT: ");
  display.print(tempSensors.getBaskingTemp());
  display.print(" F");

  display.setCursor(0, 54);
  display.print("WT: ");
  display.print(tempSensors.getWaterTemp());
  display.print(" F fc:");
  display.print(feeder.getFeedCount());

  display.display();
}

// Function to display data on OLED
void displayData(int16_t baskingTemp, int16_t waterTemp, DateTime now)
{
  display.clearDisplay();
  display.setFont(&FreeSans9pt7b);

  display.setCursor(25, 12);
  display.print(formatTime12Hour(rtc.getTime().hour(), rtc.getTime().minute()));

  display.setCursor(0, 33);
  display.print("BT: ");
  display.print(tempSensors.getBaskingTemp());
  display.print(" F");

  display.setCursor(0, 54);
  display.print("WT: ");
  display.print(tempSensors.getWaterTemp());
  display.print("F fc:");
  display.print(feeder.getFeedCount());

  display.display();
}

// MQTT callback function
void mqttCallback(char *topic, byte *payload, unsigned int length)
{
  String message = "";
  for (unsigned int i = 0; i < length; i++)
  {
    message += (char)payload[i];
  }

  Serial.print("Message received: ");
  Serial.println(message);

  // Check the message and trigger feeder if "1" or "feed" is received
  if (String(topic) == "turtle/feed")
  {

    if (autoMode.isEnabled())
    {
      Serial.println("Feed request ignored — Auto Mode is ON");
      return;
    }

    if (message == "1" || message == "feed")
    {
      feeder.runManual(); // Call the runFeeder function
    }
  }

  // MQTT callback check for auto mode
  else if (String(topic) == "turtle/auto_mode")
  {
    autoMode.setEnabled(message == "on");
  }

  else if (String(topic) == "turtle/lights")
  {

    if (message == "ON" && !autoMode.isEnabled())
    {
      lights.turnOnBoth();
    }
    else if (message == "OFF" && !autoMode.isEnabled())
    {
      lights.turnOffBoth();
    }
  }
}

void setup()
{
  // Start Serial Monitor
  // Serial.begin(9600);
  Wire.begin();
  rtc.begin();
  esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_ALL);

  // Initialize components
  initializeOLED();
  tempSensors.begin(4, 5); // your pins for basking/water DS18B20s

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

  // Setup MQTT
  mqtt.begin("172.22.80.5", 1883);
  mqtt.setCallback(mqttCallback);
  mqtt.reconnectIfNeeded();
  mqtt.setOnReconnectSuccess([&]()
                             {
                               publishStatus();
                               tempSensors.publishNow(&mqtt.getClient()); // push temps immediately on reconnect
                             });

  feeder.begin(&mqtt.getClient(), &autoMode);
  autoMode.begin(&mqtt.getClient());
  lights.begin(&mqtt.getClient(), &autoMode);

  display.clearDisplay();
  display.setTextSize(1);

  display.setCursor(0, 14);
  display.display();
  delay(2000);

  display.clearDisplay();
  display.setTextSize(1);
  display.print("Free RAM: ");
  display.print(getFreeHeap() / 1024.0);
  display.println(" KB");
  display.display();

  ArduinoOTA.begin();
  delay(1000);
  // mqtt.getClient().publish("turtle/auto_mode_state", autoModeEnabled ? "on" : "off");
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
  currents.readAndPublish();

  if (millis() - lastOledUpdate >= oledUpInterval)
  {
    lastOledUpdate = millis();
    OledDisplayUpdate();
  }

  tempSensors.updateReadings(3000);
  tempSensors.publishIfDue(5000, &mqtt.getClient());

  if (millis() - lastStatusPublish >= statusPublishInterval)
  {
    lastStatusPublish = millis();
    publishStatus(); // Periodic status update
  }
}
