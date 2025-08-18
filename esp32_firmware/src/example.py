# #include <Adafruit_ADS1X15.h>

# Adafruit_ADS1115 ads;


# // Burden resistor you trimmed on each CT (Ω)
# #define BURDEN 0.5f

# // ADS1115 in ±0.512 V mode → 0.512 V/32768 ≈ 15.6 µV/count
# #define ADS_GAIN GAIN_EIGHT
# const float ADS_LSB = 0.512f / 32768.0f;

# // Thresholds for “lamp ON” (amps)
# #define TH_HEAT 0.20f // roughly half your 50 W lamp’s ≈0.43 A
# #define TH_UV 0.05f   // roughly half your 13 W lamp’s ≈0.11 A

# // How many samples to auto-zero / measure
# #define CAL_SAMPLES 100
# #define READ_SAMPLES 50
# // ────────────────────────────────────────────────────────────────
# float offsetHeat, offsetUV;

# unsigned long lastPublishCurrent;
# const unsigned long publishCurrentInterval = 4000;


# float readCurrent(uint8_t pair, float offset);

# void publishCurrent()
# {
#   if (feeder.isRunning())
#     return; // Safety guard
#   // publish uv & heat bulb current to determine  bulbs OK or FAULT
#   float heatA = readCurrent(0, offsetHeat);
#   mqtt.getClient().publish("turtle/heat_bulb/current", String(heatA, 2).c_str(), true);

#   float uvA = readCurrent(1, offsetUV);
#   mqtt.getClient().publish("turtle/uv_bulb/current", String(uvA, 2).c_str(), true);

#   // Decide ok/fault
#   bool heatOk = heatA > TH_HEAT;
#   bool uvOk = uvA > TH_UV;
#   if (lights.isOn())
#   {
#     mqtt.getClient().publish("turtle/heat_bulb/status", heatOk ? "OK" : "FLT", true);
#     mqtt.getClient().publish("turtle/uv_bulb/status", uvOk ? "OK" : "FLT", true);
#   }
#   else
#   {
#     mqtt.getClient().publish("turtle/heat_bulb/status", "OFF", true);
#     mqtt.getClient().publish("turtle/uv_bulb/status", "OFF", true);
#   }
# }

# float readCurrent(uint8_t pair, float offset)
# {
#   long sumDev = 0;
#   for (int i = 0; i < READ_SAMPLES; i++)
#   {
#     int16_t raw = (pair == 0)
#                       ? ads.readADC_Differential_0_1()
#                       : ads.readADC_Differential_2_3();
#     sumDev += abs(raw - offset);
#     delayMicroseconds(500);
#   }
#   float avgCounts = sumDev / float(READ_SAMPLES);
#   float volts = avgCounts * ADS_LSB; // V across burden
#   return volts / BURDEN;             // I = V / R
# }

# void setup()
# {
#     ads.begin();

#     ads.setGain(ADS_GAIN);

#     // 1) Auto-zero with both lamps OFF
#     long sumH = 0, sumU = 0;
#     for (int i = 0; i < CAL_SAMPLES; i++)
#     {
#         sumH += ads.readADC_Differential_0_1(); // Heat CT on AIN0–AIN1
#         sumU += ads.readADC_Differential_2_3(); //  UV CT on AIN2–AIN3
#         delay(5);
#     }
#     offsetHeat = sumH / float(CAL_SAMPLES);
#     offsetUV = sumU / float(CAL_SAMPLES);

# }


# void loop(){
#     if (millis() - lastPublishCurrent >= publishCurrentInterval && !feeder.isRunning())
#   {
#     lastPublishCurrent = millis();
#     publishCurrent();
#   }

# }
