#include <Arduino.h>
#include <ArduinoJson.h>
#include <U8g2lib.h>
#include "eyes.h"

// 6 Servo PWM GPIO Pins
const int SERVO_PINS[6] = {13, 12, 14, 27, 26, 25};
const int PWM_FREQ = 50;       // 50Hz standard servo frequency
const int PWM_RES = 16;        // 16-bit resolution (0 - 65535)

// Safe Angle Limits (Min, Max) for each joint
const float ANGLE_MIN[6] = {0.0, 15.0, 15.0, 0.0, 0.0, 10.0};
const float ANGLE_MAX[6] = {180.0, 165.0, 165.0, 180.0, 180.0, 120.0};

// Current & Target Angles (initialized to neutral HOME position)
float current_angles[6] = {90.0, 90.0, 90.0, 90.0, 90.0, 30.0};
float target_angles[6]  = {90.0, 90.0, 90.0, 90.0, 90.0, 30.0};
float move_speed = 2.0;

// OLED Display (SSD1306 128x64 I2C: GPIO 21 SDA, GPIO 22 SCL)
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);
EyeController eyes(u8g2);

uint32_t angleToDuty(float angle) {
    // Standard servo timing: 0.5ms (0 deg) to 2.5ms (180 deg) out of 20ms period
    // Duty = (pulse_ms / 20.0ms) * 65535 (16-bit)
    float pulse_ms = 0.5 + (constrain(angle, 0.0, 180.0) / 180.0) * 2.0;
    return (uint32_t)((pulse_ms / 20.0) * 65535.0);
}

void writeServoPWM(int jointIndex, float angle) {
    uint32_t duty = angleToDuty(angle);
#if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
    ledcWrite(SERVO_PINS[jointIndex], duty);
#else
    ledcWrite(jointIndex, duty);
#endif
}

void parseJsonPacket(const String &json_str) {
    JsonDocument doc;
    DeserializationError err = deserializeJson(doc, json_str);
    if (err) return;

    const char* cmd = doc["cmd"] | "";

    if (strcmp(cmd, "pose") == 0) {
        JsonArray angles = doc["angles"];
        for (size_t i = 0; i < 6 && i < angles.size(); i++) {
            float val = angles[i].as<float>();
            target_angles[i] = constrain(val, ANGLE_MIN[i], ANGLE_MAX[i]);
        }
        int speed_val = doc["speed"] | 50;
        move_speed = max(0.5f, min(12.0f, (float)speed_val / 15.0f));

        if (doc["face"].is<const char*>()) {
            eyes.setState(doc["face"].as<String>());
        }
    } else if (strcmp(cmd, "reflex") == 0) {
        const char* type = doc["type"] | "";
        if (strcmp(type, "PERK_UP") == 0) {
            target_angles[1] = 110.0; // Shoulder erect
            target_angles[2] = 80.0;  // Elbow alert
            move_speed = 7.0;         // Snappy reaction
            eyes.setState("ALERT");
        } else if (strcmp(type, "THINK") == 0) {
            target_angles[3] = 75.0;  // Inquisitive head tilt
            eyes.setState("THINKING");
        } else if (strcmp(type, "DROOP") == 0) {
            target_angles[1] = 40.0;  // Lower head to table
            target_angles[2] = 140.0;
            move_speed = 1.2;         // Dejected, slow movement
            eyes.setState("SAD");
        } else if (strcmp(type, "STARTLE") == 0) {
            target_angles[1] = 65.0;  // Recoil back
            target_angles[2] = 120.0;
            move_speed = 9.0;
            eyes.setState("ALERT");
        }
    } else if (strcmp(cmd, "face") == 0) {
        String state = doc["state"] | "NEUTRAL";
        int px = doc["pupil_x"] | 0;
        int py = doc["pupil_y"] | 0;
        eyes.setState(state, px, py);
    }
}

void setup() {
    Serial.begin(115200);
    while (!Serial && millis() < 1500) {}

    // Initialize OLED Face
    u8g2.begin();
    eyes.setState("ALERT");
    eyes.update();

    // Initialize 6 LEDC hardware PWM channels
    for (int i = 0; i < 6; i++) {
#if ESP_ARDUINO_VERSION >= ESP_ARDUINO_VERSION_VAL(3, 0, 0)
        ledcAttach(SERVO_PINS[i], PWM_FREQ, PWM_RES);
#else
        ledcSetup(i, PWM_FREQ, PWM_RES);
        ledcAttachPin(SERVO_PINS[i], i);
#endif
        writeServoPWM(i, current_angles[i]);
    }

    // Handshake packet to laptop
    Serial.println("{\"status\":\"ready\",\"device\":\"jarmvis_esp32\",\"version\":\"1.0\"}");
}

void loop() {
    // Process incoming USB serial JSON packets
    if (Serial.available()) {
        String line = Serial.readStringUntil('\n');
        line.trim();
        if (line.length() > 0) {
            parseJsonPacket(line);
        }
    }

    // 50Hz Smooth Motion Interpolation Step (every 20ms)
    static unsigned long last_motor_update = 0;
    unsigned long now = millis();
    if (now - last_motor_update >= 20) {
        last_motor_update = now;
        for (int i = 0; i < 6; i++) {
            float diff = target_angles[i] - current_angles[i];
            if (abs(diff) > 0.4) {
                float step = (diff > 0.0 ? 1.0 : -1.0) * min(abs(diff), move_speed);
                current_angles[i] += step;
                writeServoPWM(i, current_angles[i]);
            }
        }
    }

    // Refresh Animated OLED Eyes (~30-50 FPS)
    static unsigned long last_eye_update = 0;
    if (now - last_eye_update >= 30) {
        last_eye_update = now;
        eyes.update();
    }
}

