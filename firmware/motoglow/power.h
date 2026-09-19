// MotoGlow — power budget and battery watch
//
// Two jobs:
//  1. Never let a frame ask the strips for more current than the wiring and
//     fuse allow. White-heavy frames are the danger; the renderer scales the
//     whole frame down rather than clipping individual pixels.
//  2. Watch the battery. The bike is wired battery-direct with no ignition
//     interlock, so if the pack sags the firmware says so in a way you can see
//     from outside the bike, then protects it.
#pragma once
#include <FastLED.h>

enum PowerState : uint8_t { PW_NORMAL, PW_WARN, PW_CRITICAL };

void       powerInit();
void       powerTick();              // call every frame
float      batteryVolts();
bool       engineRunning();          // rail above the charging threshold
PowerState powerState();

// Largest brightness <= desired that keeps the frame inside the current budget.
uint8_t    limitBrightness(const CRGB* px, uint16_t n, uint8_t desired);
float      estimateAmps(const CRGB* px, uint16_t n, uint8_t brightness);
