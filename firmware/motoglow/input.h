// MotoGlow — handlebar button state machine
//
// The toggle switch is not wired to the microcontroller at all: it drives the
// relay coil, so "off" means the whole box is unpowered and the bike draws
// nothing. Everything below is about the single momentary button.
//
//   short press      next preset
//   double press     previous preset
//   triple press     jump to preset 1
//   hold  0.8 s      cycle brightness (flashes the new level as feedback)
//   hold  3.0 s      cycle animation speed
#pragma once
#include <Arduino.h>

enum ButtonEvent : uint8_t {
  EV_NONE = 0, EV_SHORT, EV_DOUBLE, EV_TRIPLE, EV_LONG, EV_VLONG
};

void        buttonInit();
ButtonEvent buttonPoll();   // call every frame; returns at most one event
