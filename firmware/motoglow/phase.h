// MotoGlow — travelling-phase helpers
//
// This header is deliberately free of any Arduino or FastLED dependency so the
// direction invariant can be tested on the host: see tools/test_phase.cpp.
//
// THE INVARIANT: features travel from the FRONT of the bike (x = 0) to the
// REAR (x = 1) as t increases. Every effect in animations.cpp derives its
// position from one of these two functions, so no effect can express any other
// direction. If you ever want a front-running effect, negate speed — do not
// write new phase math.
#pragma once

// Fractional part, always in [0,1).
inline float fracf(float v) {
  float f = v - (long)v;
  return f < 0.0f ? f + 1.0f : f;
}

// Phase of a pixel relative to a feature that repeats every bike-length and
// travels front to rear. Zero at the feature, rising toward the front.
inline float phaseAt(float x, float t, float speed) { return fracf(x - t * speed); }

// How far a pixel sits BEHIND the travelling head, in bike-lengths, in [0,1).
// Zero at the head; grows toward the front of the bike, which is where a
// comet's tail belongs.
inline float behindHead(float x, float t, float speed) { return fracf(t * speed - x); }
