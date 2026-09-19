// MotoGlow — motion primitives
//
// Every primitive is a pure function of a pixel's bike-space position and the
// animation clock. They all share one invariant: features travel from the FRONT
// of the bike to the REAR. That is enforced in one place — the phase helpers
// below — so no individual effect can get the direction wrong.
#pragma once
#include <FastLED.h>
#include "bike_map.h"
#include "phase.h"   // fracf / phaseAt / behindHead — the direction invariant

struct EffectParams {
  float    speed;    // bike-lengths per second
  float    width;    // feature size, in bike-lengths
  float    param;    // effect-specific (tail length, stripe count, density…)
  uint8_t  bgLevel;  // how bright the "black" between features is, 0-255
};

enum Motion : uint8_t {
  M_BLOCK,     // solid block of colour sweeping rearward over the background
  M_COMET,     // bright head with an exponential tail stretching forward
  M_GRADIENT,  // the whole palette drifting rearward, continuous
  M_RAINBOW,   // continuous hue cycle drifting rearward
  M_SPARKLE,   // sparks born at the front, carried rearward
  M_BARBER,    // hard-edged two-or-more tone stripes travelling rearward
  M_PULSE,     // brightness wave travelling rearward over a palette base
  M_EMBER,     // scrolling noise field through a heat palette
};

// Advance any effect state that is not a pure function of time (currently just
// the spark pool). Call once per frame, before shading.
void effectsTick(Motion m, const EffectParams& p, float dt, float t);

// Colour for one pixel.
CRGB shadePixel(Motion m, const CRGBPalette16& pal, const EffectParams& p,
                const Pixel& px, float t);

void effectsReset();
