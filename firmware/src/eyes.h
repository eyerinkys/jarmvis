#pragma once
#include <Arduino.h>
#include <U8g2lib.h>

class EyeController {
private:
    U8G2 &u8g2;
    int eyeL_x = 42, eyeL_y = 32;
    int eyeR_x = 86, eyeR_y = 32;
    int eye_w = 26, eye_h = 30;
    int pupil_dx = 0, pupil_dy = 0;
    String current_state = "ALERT";
    unsigned long last_blink = 0;
    bool is_blinking = false;

public:
    EyeController(U8G2 &disp) : u8g2(disp) {}

    void setState(const String &st, int px = 0, int py = 0) {
        current_state = st;
        current_state.toUpperCase();
        pupil_dx = px;
        pupil_dy = py;
    }

    String getState() const {
        return current_state;
    }

    void update() {
        unsigned long now = millis();

        // Automatic natural blinking every 3.5 - 5 seconds
        if (now - last_blink > 4200) {
            is_blinking = true;
            last_blink = now;
        }
        if (is_blinking && (now - last_blink > 140)) {
            is_blinking = false;
        }

        u8g2.clearBuffer();

        if (is_blinking) {
            // Closed eyes slit
            u8g2.drawBox(eyeL_x - eye_w / 2, eyeL_y - 1, eye_w, 3);
            u8g2.drawBox(eyeR_x - eye_w / 2, eyeR_y - 1, eye_w, 3);
        } else if (current_state == "SAD") {
            // Sad droop: Upper half occluded, lower crescent looking down
            u8g2.drawRBox(eyeL_x - eye_w / 2, eyeL_y + 4, eye_w, 14, 4);
            u8g2.drawRBox(eyeR_x - eye_w / 2, eyeR_y + 4, eye_w, 14, 4);
            // Slanted droop brow
            u8g2.drawLine(eyeL_x - eye_w / 2, eyeL_y, eyeL_x + eye_w / 2, eyeL_y + 6);
            u8g2.drawLine(eyeR_x - eye_w / 2, eyeR_y + 6, eyeR_x + eye_w / 2, eyeR_y);
        } else if (current_state == "ALERT") {
            // Big wide open surprised eyes
            u8g2.drawDisc(eyeL_x, eyeL_y, 15);
            u8g2.drawDisc(eyeR_x, eyeR_y, 15);
            // Inverted white pupil highlight
            u8g2.setDrawColor(0);
            u8g2.drawDisc(eyeL_x + pupil_dx, eyeL_y + pupil_dy, 5);
            u8g2.drawDisc(eyeR_x + pupil_dx, eyeR_y + pupil_dy, 5);
            u8g2.setDrawColor(1);
        } else if (current_state == "HAPPY") {
            // Smiling crescent eyes (^ ^)
            u8g2.drawRBox(eyeL_x - eye_w / 2, eyeL_y - 8, eye_w, 18, 5);
            u8g2.drawRBox(eyeR_x - eye_w / 2, eyeR_y - 8, eye_w, 18, 5);
            u8g2.setDrawColor(0);
            u8g2.drawBox(eyeL_x - eye_w / 2, eyeL_y + 2, eye_w, 12);
            u8g2.drawBox(eyeR_x - eye_w / 2, eyeR_y + 2, eye_w, 12);
            u8g2.setDrawColor(1);
        } else if (current_state == "CURIOUS") {
            // Inquisitive asymmetrical squint (one eye slightly higher and larger)
            u8g2.drawRBox(eyeL_x - eye_w / 2, eyeL_y - 12, eye_w + 2, eye_h, 6);
            u8g2.drawRBox(eyeR_x - eye_w / 2, eyeR_y - 4, eye_w - 4, eye_h - 8, 4);
            u8g2.setDrawColor(0);
            u8g2.drawDisc(eyeL_x + 3, eyeL_y - 5, 4);
            u8g2.drawDisc(eyeR_x + 2, eyeR_y, 3);
            u8g2.setDrawColor(1);
        } else if (current_state == "THINKING") {
            // Thinking pupils looking up and oscillating slightly
            int shift = (int)(sin(now / 300.0) * 4);
            u8g2.drawRBox(eyeL_x - eye_w / 2, eyeL_y - eye_h / 2, eye_w, eye_h - 6, 6);
            u8g2.drawRBox(eyeR_x - eye_w / 2, eyeR_y - eye_h / 2, eye_w, eye_h - 6, 6);
            u8g2.setDrawColor(0);
            u8g2.drawDisc(eyeL_x + shift, eyeL_y - 8, 5);
            u8g2.drawDisc(eyeR_x + shift, eyeR_y - 8, 5);
            u8g2.setDrawColor(1);
        } else if (current_state == "ANGRY") {
            // Angry sharp slanted eyes
            u8g2.drawRBox(eyeL_x - eye_w / 2, eyeL_y - eye_h / 2, eye_w, eye_h, 4);
            u8g2.drawRBox(eyeR_x - eye_w / 2, eyeR_y - eye_h / 2, eye_w, eye_h, 4);
            u8g2.setDrawColor(0);
            u8g2.drawTriangle(eyeL_x - eye_w / 2, eyeL_y - eye_h / 2, eyeL_x + eye_w / 2, eyeL_y - eye_h / 2, eyeL_x + eye_w / 2, eyeL_y);
            u8g2.drawTriangle(eyeR_x - eye_w / 2, eyeR_y - eye_h / 2, eyeR_x + eye_w / 2, eyeR_y - eye_h / 2, eyeR_x - eye_w / 2, eyeR_y);
            u8g2.drawDisc(eyeL_x + 2, eyeL_y + 2, 4);
            u8g2.drawDisc(eyeR_x - 2, eyeR_y + 2, 4);
            u8g2.setDrawColor(1);
        } else if (current_state == "ANNOYED") {
            // Unimpressed half-lidded flat gaze / side-eye
            u8g2.drawRBox(eyeL_x - eye_w / 2, eyeL_y - 2, eye_w, eye_h / 2 + 2, 4);
            u8g2.drawRBox(eyeR_x - eye_w / 2, eyeR_y - 2, eye_w, eye_h / 2 + 2, 4);
            // Heavy eyelid brow lines
            u8g2.drawHLine(eyeL_x - eye_w / 2 - 2, eyeL_y - 3, eye_w + 4);
            u8g2.drawHLine(eyeR_x - eye_w / 2 - 2, eyeR_y - 3, eye_w + 4);
            u8g2.setDrawColor(0);
            u8g2.drawDisc(eyeL_x + 4, eyeL_y + 5, 4);
            u8g2.drawDisc(eyeR_x + 4, eyeR_y + 5, 4);
            u8g2.setDrawColor(1);
        } else if (current_state == "FOCUSED") {
            // Intense horizontal slit eyes
            u8g2.drawRBox(eyeL_x - eye_w / 2, eyeL_y - 6, eye_w, 14, 3);
            u8g2.drawRBox(eyeR_x - eye_w / 2, eyeR_y - 6, eye_w, 14, 3);
            u8g2.setDrawColor(0);
            u8g2.drawDisc(eyeL_x + pupil_dx, eyeL_y, 4);
            u8g2.drawDisc(eyeR_x + pupil_dx, eyeR_y, 4);
            u8g2.setDrawColor(1);
        } else if (current_state == "CONFUSED") {
            // Uneven cockeyed gaze
            u8g2.drawRBox(eyeL_x - eye_w / 2, eyeL_y - 12, eye_w - 4, eye_h - 4, 4);
            u8g2.drawRBox(eyeR_x - eye_w / 2, eyeR_y + 2, eye_w + 2, eye_h - 10, 4);
            u8g2.setDrawColor(0);
            u8g2.drawDisc(eyeL_x - 3, eyeL_y - 4, 3);
            u8g2.drawDisc(eyeR_x + 3, eyeR_y + 6, 4);
            u8g2.setDrawColor(1);
        } else {
            // Standard NEUTRAL rounded rectangular eyes with animated pupils
            u8g2.drawRBox(eyeL_x - eye_w / 2, eyeL_y - eye_h / 2, eye_w, eye_h, 6);
            u8g2.drawRBox(eyeR_x - eye_w / 2, eyeR_y - eye_h / 2, eye_w, eye_h, 6);
            u8g2.setDrawColor(0);
            u8g2.drawDisc(eyeL_x + pupil_dx, eyeL_y + pupil_dy, 4);
            u8g2.drawDisc(eyeR_x + pupil_dx, eyeR_y + pupil_dy, 4);
            u8g2.setDrawColor(1);
        }

        u8g2.sendBuffer();
    }
};

