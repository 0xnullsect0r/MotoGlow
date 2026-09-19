// MotoGlow — settings persistence
//
// Flash has a finite erase budget, so writes are deferred: the settings are
// only committed once nothing has changed for SETTINGS_SAVE_DELAY_MS. Riding
// through ten presets therefore costs one write, not ten.
#pragma once
#include <Arduino.h>

struct Settings {
  uint16_t magic;
  uint8_t  version;
  uint8_t  preset;
  uint8_t  brightness;   // index into BRIGHTNESS_LEVELS
  uint8_t  speed;        // index into SPEED_LEVELS
  uint8_t  checksum;
};

extern Settings g_settings;

void settingsLoad();          // loads, or installs defaults if blank/corrupt
void settingsTouch();         // mark dirty; schedules a deferred write
void settingsTick();          // call every frame; performs the deferred write
