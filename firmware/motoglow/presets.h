// MotoGlow — the preset library
#pragma once
#include "animations.h"

struct Preset {
  const char*   name;
  Motion        motion;
  const CRGBPalette16* palette;
  EffectParams  fx;
};

extern const Preset PRESETS[];
extern const uint8_t NUM_PRESETS;
