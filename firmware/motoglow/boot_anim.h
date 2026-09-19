// MotoGlow — power-on sequence: two fast sweeps front to rear, then a bloom
// that resolves into whichever preset was active when you last switched off.
#pragma once
#include "presets.h"

void runBootAnimation(const Preset& target, uint8_t brightness);
