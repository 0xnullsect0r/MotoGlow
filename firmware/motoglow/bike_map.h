// MotoGlow — bike-space pixel map
//
// The whole point of this file: animations are never written against LED
// indexes. Every pixel is given a physical position on the motorcycle, and
// effects are rendered as a function of that position and time. A colour block
// "flowing front to rear" therefore flows front to rear across the real bike,
// no matter which strip a pixel belongs to, which direction that strip was
// soldered, or how long each segment is.
//
// Coordinate system (right-handed, viewed from the left side of the bike):
//   x   0.0 = front axle, 1.0 = rear axle. Wheelbase for the KTM 890
//       Adventure is 1509 mm, so 0.1 x-units = 151 mm.
//   y   0.0 = ground, 1.0 = 1350 mm up. Only used by effects that want height.
//   side  -1 = left, 0 = centre, +1 = right.
//
// To adapt to a different bike or layout, edit SEGMENTS below. Nothing else in
// the firmware needs to change. See docs/BIKE_MAP.md for a measuring worksheet.
#pragma once
#include <FastLED.h>
#include "config.h"

#define NUM_RUNS 4

struct Segment {
  const char* name;
  uint8_t  run;     // which output channel; segments must be grouped by run
  uint16_t count;   // pixels in this segment
  float    x0, y0;  // bike-space position of the FIRST pixel
  float    x1, y1;  // bike-space position of the LAST pixel
  int8_t   side;    // -1 left, 0 centre, +1 right
};

struct Pixel {
  float  x, y;
  int8_t side;
};

extern const Segment SEGMENTS[];
extern const uint16_t NUM_SEGMENTS;
extern const uint16_t RUN_COUNT[NUM_RUNS];   // pixels per run
extern const uint16_t RUN_START[NUM_RUNS];   // index of each run's first pixel
extern const uint16_t NUM_PIXELS;

// Filled in by bikeMapInit(): position of every pixel, in run order.
extern Pixel   PIXELS[];
extern CRGB    leds[];

void bikeMapInit();
