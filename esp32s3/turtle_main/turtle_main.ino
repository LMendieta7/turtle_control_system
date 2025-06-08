#include <Preferences.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <RTClib.h>
#include <WiFi.h>
#include <Fonts/FreeSans9pt7b.h> // Include a font for OLED display
#include <WiFiUdp.h>
#include <NTPClient.h>
#include "esp_system.h"
#include <PubSubClient.h>

#define AIN1 16        // Motor direction pin
#define AIN2 18        // Motor direction pin
#define PWMA 15        // Motor speed (PWM)
#define STBY 21        // Standby (enable motor)
#define HALL_SENSOR 12 // Hall effect sensor pin

// MQTT Broker Settings
const char *mqttServer = "10.0.0.130"; // IP address of your MQTT broker (e.g., Mosquitto)
const int mqttPort = 1883;             // Default MQTT port

unsigned long lastMQTTReconnectAttempt = 0;    // Track the last time we attempted to reconnect
const unsigned long reconnectInterval = 15000; // Time between reconnect attempts (5 seconds)

// WiFi and MQTT Client Setup
WiFiClient espClient;
PubSubClient client(espClient);

const unsigned long TIMEOUT_MS = 13000; // Emergency stop after 12 seconds

bool hasFedToday = false; // Flag to track feeding
bool motorRunning = false;
volatile bool hallTriggered = false; // Interrupt flag
int feedCount = 0;
unsigned long motorStartTime = 0; // Track motor run time

// Set feeding time (change this to your desired time)
int feedHour = 9;
int feedMinute = 20;
bool autoModeEnabled = true;

static unsigned long lastWIFIReconnectAttempt = 0;

unsigned long lastRTCCheck = 0;
const unsigned long checkRTCInterval = 1000; // Check every second

// GPIO Pins for Lights
#define BASKING_LIGHT_PIN 1 // GPIO 1 for basking light
#define UV_LIGHT_PIN 2      // GPIO 2 for UV light

// Light Schedule
const int lightOnTime = 800;   // Lights turn on at 8am
const int lightOffTime = 1800; // Lights stay on for 10 hours 1800(6pm)

// Declare preferences globally
Preferences preferences;

// Wi-Fi credentials
String ssid;
String password;

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

RTC_DS3231 rtc;
DateTime now; // Global variable

// Set time zone for New York (Eastern Time with DST)
const char *ntpServer = "pool.ntp.org";
const long gmtOffset_sec = -5 * 3600; // UTC-5 (Standard Time)
const int daylightOffset_sec = 3600;  // +1 hour for DST

// ntp sync every 12 hours
unsigned long lastSyncTime = 0;
const unsigned long syncInterval = 3 * 60 * 60 * 1000; // 3 hours in milliseconds

// Timing variables for display data
unsigned long previousMillis = 0;
const long interval = 5000; // Update interval in milliseconds (2 second)

unsigned long lastStatusPublish = 0;
const unsigned long statusPublishInterval = 8000;

volatile unsigned long lastHallTriggerTime = 0;
const unsigned long debounceDelay = 200; // ms

void publishStatus()
{
  // Read only the basking pin for combined light state
  String lightStatus = (digitalRead(BASKING_LIGHT_PIN) == HIGH) ? "ON" : "OFF";
  client.publish("turtle/lights_state", lightStatus.c_str());

  // Feeder status
  const char *feederStatus = motorRunning ? "RUNNING" : "IDLE";
  client.publish("turtle/feeder_state", feederStatus);

  // Auto mode status
  client.publish("turtle/auto_mode_state", autoModeEnabled ? "on" : "off");

  client.publish("turtle/feed_count", String(feedCount).c_str());

  // publish current IP
  String ip = WiFi.localIP().toString();
  client.publish("turtle/esp_ip", ip.c_str());

  // mqtt status
  const char *mqttStatus = client.connected() ? "connected" : "disconnected";
  client.publish("turtle/mqtt_status", mqttStatus);

  String heapStr = String(getFreeHeap() / 1024) + " KB";
  client.publish("turtle/heap", heapStr.c_str());
}

void IRAM_ATTR hallSensorISR()
{
  unsigned long now = millis();
  if (motorRunning && (now - lastHallTriggerTime > debounceDelay))
  {
    hallTriggered = true;
    lastHallTriggerTime = now;
  }
}

void runFeeder()
{
  if (motorRunning)
    return; // Prevent re-triggering

  Serial.println("Starting motor...");
  digitalWrite(STBY, HIGH); // Enable motor driver
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  analogWrite(PWMA, 120);

  motorRunning = true;
  hallTriggered = false;
  motorStartTime = millis(); // Start tracking time
  publishStatus();
}

void stopMotor()
{
  Serial.println("Stopping motor...");
  analogWrite(PWMA, 0);
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  digitalWrite(STBY, LOW);

  motorRunning = false;
  feedCount++;
  client.publish("turtle/feed_count", String(feedCount).c_str());
  publishStatus();
}

// Get free heap (available RAM)
uint32_t getFreeHeap()
{
  return esp_get_free_heap_size();
}

void checkWiFi()
{
  if (WiFi.status() == WL_CONNECTED)
    return;

  if (millis() - lastWIFIReconnectAttempt >= 30000)
  {
    lastWIFIReconnectAttempt = millis();
    Serial.println("WiFi Disconnected. Attempting to reconnect...");
    WiFi.reconnect();
    delay(20); // Just a tiny buffer if needed
  }
}

// Function to turn on the lights
void turnOnLights()
{
  digitalWrite(BASKING_LIGHT_PIN, HIGH); // Turn on basking light
  digitalWrite(UV_LIGHT_PIN, HIGH);      // Turn on UV light
  publishStatus();                       // Send status after turning on
}

// Function to turn off the lights
void turnOffLights()
{
  digitalWrite(BASKING_LIGHT_PIN, LOW); // Turn off basking light
  digitalWrite(UV_LIGHT_PIN, LOW);      // Turn off UV light
  publishStatus();
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
}

// Function to initialize DS3231
void initializeDS3231()
{
  // Initialize RTC
  if (!rtc.begin())
  {
    Serial.println("Couldn't find RTC");
    while (1)
      ;
  }

  if (rtc.lostPower())
  {

    Serial.println("RTC lost power! Syncing from NTP...");
    syncTimeFromNTP();
  }
  delay(1000);
  syncTimeFromNTP();
}

void syncTimeFromNTP()
{

  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  struct tm timeinfo;

  if (!getLocalTime(&timeinfo))
  {
    Serial.println("Failed to obtain time from NTP. Using RTC instead.");

    return;
  }

  // Update DS3231 RTC with new time
  rtc.adjust(DateTime(timeinfo.tm_year + 1900, timeinfo.tm_mon + 1, timeinfo.tm_mday,
                      timeinfo.tm_hour, timeinfo.tm_min, timeinfo.tm_sec));
}

// Function to connect to Wi-Fi
void connectToWiFi()
{
  display.clearDisplay();
  display.setTextSize(1);

  display.setCursor(0, 14);
  display.print("Connecting to Wi-Fi...");
  display.display();

  WiFi.begin(ssid, password);

  unsigned long startAttemptTime = millis(); // Track time since Wi-Fi attempt started

  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 20000)
  {
    delay(500); // Delay to prevent locking up CPU entirely
    display.print(".");
    display.display();
  }

  if (WiFi.status() == WL_CONNECTED)
  {
    // Successful connection
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 14);
    display.print("Wi-Fi connected!");

    display.setCursor(0, 30);
    display.print("IP: ");
    display.print(WiFi.localIP());
    display.display();
    delay(2000); // Show Wi-Fi connection status for 2 seconds
  }
  else
  {
    // Timeout case
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 14);
    display.print("Wi-Fi connect failed");
    display.display();
    delay(2000); // Show failure message for 2 seconds
  }
}

// Function to read temperature in Fahrenheit from a specific sensor
int16_t readTemperatureF(DallasTemperature &sensor)
{
  sensor.requestTemperatures();
  int16_t tempF = sensor.getTempFByIndex(0);
  return tempF; // Classic integer math
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

void handleScheduledFeeding()
{

  if (autoModeEnabled && now.hour() == feedHour && now.minute() == feedMinute && !hasFedToday)
  {
    Serial.println("Scheduled auto feeding time reached!");
    runFeeder();
    hasFedToday = true;
  }

  if (now.hour() == 0 && now.minute() == 0)
  {
    hasFedToday = false;
    feedCount = 0;
  }
}

void handleLightSchedule()
{
  int currentTime = now.hour() * 100 + now.minute();
  if (currentTime >= lightOnTime && currentTime < lightOffTime)
  {
    turnOnLights();
  }
  else
  {
    turnOffLights();
  }
}

void sensorDisplayUpdate()
{
  if (millis() - previousMillis >= interval)
  {
    previousMillis = millis();

    int16_t baskingTemp = readTemperatureF(sensor1);
    int16_t waterTemp = readTemperatureF(sensor2);

    // Convert to string for MQTT
    char baskingTempStr[8];
    char waterTempStr[8];
    itoa(baskingTemp, baskingTempStr, 10); // Convert basking temperature to string
    itoa(waterTemp, waterTempStr, 10);     // Convert water temperature to string

    // Publish temperature to respective MQTT topics
    client.publish("turtle/basking_temperature", baskingTempStr); // Send basking temperature
    client.publish("turtle/water_temperature", waterTempStr);     // Send basking temperature

    displayData(baskingTemp, waterTemp, now);
  }
}

void handleMotorTimeout()
{
  if (motorRunning && (millis() - motorStartTime > TIMEOUT_MS))
  {
    Serial.println("Motor timeout reached. Stopping motor.");
    stopMotor();
  }
}

void handleHallSensorTrigger()
{
  if (hallTriggered && motorRunning)
  {
    stopMotor(); // Stop motor if hall sensor is triggered
    hallTriggered = false;
  }
}

void handleTimeSync()
{
  if (millis() - lastSyncTime >= syncInterval)
  {
    Serial.println("Syncing time with NTP...");
    syncTimeFromNTP();
    lastSyncTime = millis();
  }
}

// Function to display data on OLED
void displayData(int16_t baskingTemp, int16_t waterTemp, DateTime now)
{
  display.clearDisplay();
  display.setFont(&FreeSans9pt7b);

  display.setCursor(25, 12);
  display.print(formatTime12Hour(now.hour(), now.minute()));

  display.setCursor(0, 33);
  display.print("BT: ");
  display.print(baskingTemp);
  display.print(" F");

  display.setCursor(0, 54);
  display.print("WT: ");
  display.print(waterTemp);
  display.print("F fc:");
  display.print(feedCount);

  display.display();
}

void reconnectMQTT()
{
  if (client.connected())
  {
    return; // No need to reconnect if already connected
  }

  unsigned long currentMillis = millis();

  // Only attempt reconnect if the interval has passed
  if (currentMillis - lastMQTTReconnectAttempt >= reconnectInterval)
  {
    lastMQTTReconnectAttempt = currentMillis;

    Serial.print("Attempting MQTT connection...");

    // Try to connect to MQTT broker
    if (client.connect("ESP32_TestClient"))
    {
      Serial.println("connected");
      // Subscribe to topics (this can be adjusted to your needs)
      client.subscribe("turtle/feed");
      client.subscribe("turtle/lights");
      client.subscribe("turtle/auto_mode");

      client.publish("turtle/mqtt_status", "connected");
      const char *wifiStatus = (WiFi.status() == WL_CONNECTED) ? "connected" : "disconnected";
      client.publish("turtle/wifi_status", wifiStatus);

      String ip = WiFi.localIP().toString();
      client.publish("turtle/esp_ip", ip.c_str());

      String heapStr = String(getFreeHeap() / 1024) + " KB";
      client.publish("turtle/heap", heapStr.c_str());
    }
    else
    {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
    }
    delay(60);
  }
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

    if (autoModeEnabled)
    {
      Serial.println("Feed request ignored — Auto Mode is ON");
      return;
    }

    if (message == "1" || message == "feed")
    {
      runFeeder(); // Call the runFeeder function
    }
  }

  // MQTT callback check for auto mode
  if (String(topic) == "turtle/auto_mode")
  {
    if (message == "on")
    {
      autoModeEnabled = true;
    }
    else if (message == "off")
    {
      autoModeEnabled = false;
    }
    // Always publish the actual state after changing it
    client.publish("turtle/auto_mode_state", autoModeEnabled ? "on" : "off");
  }

  if (String(topic) == "turtle/lights")
  {

    if (autoModeEnabled)
    {
      Serial.println("Light toggle ignored — Auto Mode is ON");
      return;
    }

    if (message == "ON")
    {
      turnOnLights();
    }
    else if (message == "OFF")
    {
      turnOffLights();
    }
  }
}

void setup()
{
  // Start Serial Monitor
  Serial.begin(9600);
  esp_sleep_disable_wakeup_source(ESP_SLEEP_WAKEUP_ALL);

  // Initialize GPIO Pins
  pinMode(BASKING_LIGHT_PIN, OUTPUT);
  pinMode(UV_LIGHT_PIN, OUTPUT);
  digitalWrite(BASKING_LIGHT_PIN, LOW); // Ensure lights are off initially
  digitalWrite(UV_LIGHT_PIN, LOW);

  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(PWMA, OUTPUT);
  pinMode(STBY, OUTPUT);
  pinMode(HALL_SENSOR, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(HALL_SENSOR), hallSensorISR, FALLING); // Trigger on magnet pass

  // Initialize components
  initializeOLED();
  initializeDS18B20();

  // Initialize Preferences
  preferences.begin("wifi-creds", true);

  // Retrieve Wi-Fi credentials
  ssid = preferences.getString("ssid", "");
  password = preferences.getString("password", "");

  // Close Preferences
  preferences.end();

  // Connect to Wi-Fi
  connectToWiFi();

  delay(2000);

  initializeDS3231();
  delay(500);
  now = rtc.now();
  // Setup MQTT
  client.setServer(mqttServer, mqttPort);
  client.setCallback(mqttCallback);

  // Attempt to connect to MQTT server
  if (WiFi.status() == WL_CONNECTED)
  {
    reconnectMQTT();
  }

  lastSyncTime = millis(); // Reset sync timer

  display.clearDisplay();
  display.setTextSize(1);

  display.setCursor(0, 14);
  display.print("NTP Update Successful");
  display.display();
  delay(2000);

  display.clearDisplay();
  display.setTextSize(1);
  display.print("Free RAM: ");
  display.print(getFreeHeap() / 1024.0);
  display.println(" KB");
  display.display();
  delay(3000);
  client.publish("turtle/auto_mode_state", autoModeEnabled ? "on" : "off");
}

void loop()
{
  checkWiFi();
  bool wifiConnected = WiFi.status() == WL_CONNECTED;

  if (wifiConnected)

  {
    reconnectMQTT(); //  Only try if Wi-Fi is okay
    client.loop();   // MQTT processing
    delay(20);
  }
  handleMotorTimeout();
  handleHallSensorTrigger();
  handleTimeSync();

  unsigned long currentMillis = millis();
  if (currentMillis - lastRTCCheck >= checkRTCInterval)
  {
    lastRTCCheck = currentMillis;

    now = rtc.now();
    handleScheduledFeeding();

    if (autoModeEnabled)
    {
      handleLightSchedule();
    }
  }

  sensorDisplayUpdate();

  if (millis() - lastStatusPublish >= statusPublishInterval)
  {
    lastStatusPublish = millis();
    publishStatus(); // Periodic status update
  }
}