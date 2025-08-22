#include <Arduino.h>
#include <ArduinoOTA.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_ADS1X15.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <RTClib.h>
#include <Fonts/FreeSans9pt7b.h> // Include a font for OLED display
#include "esp_system.h"
#include <PubSubClient.h>
#include "wifi_manager.h"
#include "mqtt_manager.h"
#include "auto_mode_manager.h"
#include "feeder_manager.h"
#include "rtc_manager.h"
#include "light_manager.h" 

AutoModeManager autoMode;
RtcManager rtc;

WiFiManager wifi;
MqttManager mqtt;
// ADS1115
Adafruit_ADS1115 ads;

FeederManager feeder;
LightManager lights;

// Burden resistor you trimmed on each CT (Ω)
#define BURDEN 0.5f

// ADS1115 in ±0.512 V mode → 0.512 V/32768 ≈ 15.6 µV/count
#define ADS_GAIN GAIN_EIGHT
const float ADS_LSB = 0.512f / 32768.0f;

// Thresholds for “lamp ON” (amps)
#define TH_HEAT 0.20f // roughly half your 50 W lamp’s ≈0.43 A
#define TH_UV 0.05f   // roughly half your 13 W lamp’s ≈0.11 A

// How many samples to auto-zero / measure
#define CAL_SAMPLES 100
#define READ_SAMPLES 50
// ────────────────────────────────────────────────────────────────
float offsetHeat, offsetUV;

// OLED display dimensions
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

// Initialize OLED display
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// Initialize DS18B20 sensors
#define ONE_WIRE_BUS_1 4 // First DS18B20 basking temperature on GPIO4
#define ONE_WIRE_BUS_2 5 // Second DS18B20 water temperature on GPIO5

OneWire oneWire1(ONE_WIRE_BUS_1);
OneWire oneWire2(ONE_WIRE_BUS_2);

DallasTemperature sensor1(&oneWire1);
DallasTemperature sensor2(&oneWire2);

int16_t globalBaskingTemp = 0;
int16_t globalWaterTemp = 0;

unsigned long lastTempRequestTime = 0;
bool tempConversionInProgress = false;
unsigned long lastReadTemp;
const unsigned long readTempInterval = 5000;

unsigned long lastPublishCurrent;
const unsigned long publishCurrentInterval = 4000;

unsigned long lastOledUpdate;
const unsigned long oledUpInterval = 3000;

unsigned long lastStatusPublish = 0;
const unsigned long statusPublishInterval = 5000;

// prototype

uint32_t getFreeHeap();
float readCurrent(uint8_t pair, float offset);

void publishCurrent()
{
  if (feeder.isRunning())
    return; // Safety guard
  // publish uv & heat bulb current to determine  bulbs OK or FAULT
  float heatA = readCurrent(0, offsetHeat);
  mqtt.getClient().publish("turtle/heat_bulb/current", String(heatA, 2).c_str(), true);

  float uvA = readCurrent(1, offsetUV);
  mqtt.getClient().publish("turtle/uv_bulb/current", String(uvA, 2).c_str(), true);

  // Decide ok/fault
  bool heatOk = heatA > TH_HEAT;
  bool uvOk = uvA > TH_UV;

  if (lights.isOn())
  {
    mqtt.getClient().publish("turtle/heat_bulb/status", heatOk ? "OK" : "FLT", true);
    mqtt.getClient().publish("turtle/uv_bulb/status", uvOk ? "OK" : "FLT", true);
  }
  else
  {
    mqtt.getClient().publish("turtle/heat_bulb/status", "OFF", true);
    mqtt.getClient().publish("turtle/uv_bulb/status", "OFF", true);
  }
}

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

// Function to initialize DS18B20
void initializeDS18B20()
{
  sensor1.begin();
  sensor2.begin();
  sensor1.setWaitForConversion(false); // Non-blocking
  sensor2.setWaitForConversion(false);
}

void readTemperature()
{
  // if (motorRunning) return;  // Avoid blocking feeder logic

  unsigned long nowMs = millis();

  // Step 1: Start temp conversion (assumed interval handled externally)
  if (!tempConversionInProgress)
  {
    sensor1.requestTemperatures();
    sensor2.requestTemperatures();
    tempConversionInProgress = true;
    lastTempRequestTime = nowMs; // Now used for the 750ms delay only
    return;
  }

  // Step 2: After 750ms, read temps
  if (tempConversionInProgress && (nowMs - lastTempRequestTime >= 750))
  {
    globalBaskingTemp = (int16_t)round(sensor1.getTempFByIndex(0));
    globalWaterTemp = (int16_t)round(sensor2.getTempFByIndex(0));
    tempConversionInProgress = false;

    mqtt.getClient().publish("turtle/basking_temperature", String(globalBaskingTemp).c_str(), true);
    mqtt.getClient().publish("turtle/water_temperature", String(globalWaterTemp).c_str(), true);
  }
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
  display.print(globalBaskingTemp);
  display.print(" F");

  display.setCursor(0, 54);
  display.print("WT: ");
  display.print(globalWaterTemp);
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
  display.print(baskingTemp);
  display.print(" F");

  display.setCursor(0, 54);
  display.print("WT: ");
  display.print(waterTemp);
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

float readCurrent(uint8_t pair, float offset)
{
  long sumDev = 0;
  for (int i = 0; i < READ_SAMPLES; i++)
  {
    int16_t raw = (pair == 0)
                      ? ads.readADC_Differential_0_1()
                      : ads.readADC_Differential_2_3();
    sumDev += abs(raw - offset);
    delayMicroseconds(500);
  }
  float avgCounts = sumDev / float(READ_SAMPLES);
  float volts = avgCounts * ADS_LSB; // V across burden
  return volts / BURDEN;             // I = V / R
}

void setup()
{
  // Start Serial Monitor
  // Serial.begin(9600);
  Wire.begin();
  rtc.begin();
  ads.begin();

  ads.setGain(ADS_GAIN);

  // 1) Auto-zero with both lamps OFF
  long sumH = 0, sumU = 0;
  for (int i = 0; i < CAL_SAMPLES; i++)
  {
    sumH += ads.readADC_Differential_0_1(); // Heat CT on AIN0–AIN1
    sumU += ads.readADC_Differential_2_3(); //  UV CT on AIN2–AIN3
    delay(5);
  }
  offsetHeat = sumH / float(CAL_SAMPLES);
  offsetUV = sumU / float(CAL_SAMPLES);

  delay(500);
  esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_ALL);

  // Initialize components
  initializeOLED();
  initializeDS18B20();

  wifi.begin();

  delay(500);

  // Setup MQTT
  mqtt.begin("172.22.80.5", 1883);
  mqtt.setCallback(mqttCallback);
  mqtt.reconnectIfNeeded();
  mqtt.setOnReconnectSuccess([]()
                             {
    publishStatus();
    readTemperature();
    publishCurrent(); });

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
  delay(3000);
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

  if (millis() - lastOledUpdate >= oledUpInterval)
  {
    lastOledUpdate = millis();
    OledDisplayUpdate();
  }

  if (millis() - lastPublishCurrent >= publishCurrentInterval && !feeder.isRunning())
  {
    lastPublishCurrent = millis();
    publishCurrent();
  }

  if (millis() - lastReadTemp >= readTempInterval)
  {
    lastReadTemp = millis();
    readTemperature();
  }

  if (millis() - lastStatusPublish >= statusPublishInterval)
  {
    lastStatusPublish = millis();
    publishStatus(); // Periodic status update
  }
}
