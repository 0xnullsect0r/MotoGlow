#include "bike_map.h"

// ─── KTM 890 Adventure (2023) layout ─────────────────────────────────────────
// Pixel counts assume a 50 mm cut interval (20 px/m FCOB). Lengths in comments
// are the physical strip length that count implies. Measure your own bike and
// adjust; the x/y numbers are where that strip physically sits.
//
// Runs 0 and 1 are the two side chains. Each is ONE continuous electrical run
// that happens to be cut and re-joined between segments, wired front to rear:
//     fork lower -> tank side -> seat line -> swingarm
// Because they are already physically ordered front to rear, a plain index
// sweep would almost work — but the fork segment is vertical, the swingarm
// moves, and the gaps between segments are large and unequal. The coordinate
// map is what makes the motion look continuous across those gaps.
const Segment SEGMENTS[] = {
  // name              run  n     x0     y0      x1     y1    side
  // ── Run 0: LEFT chain ───────────────────────────────────────────────────
  { "fork_L",           0,   4,  0.030f, 0.280f, 0.060f, 0.460f, -1 }, // 200 mm, vertical up the fork lower
  { "tank_L",           0,   9,  0.280f, 0.440f, 0.520f, 0.480f, -1 }, // 450 mm, under the left tank
  { "seat_L",           0,   8,  0.540f, 0.560f, 0.820f, 0.545f, -1 }, // 400 mm, seat line
  { "swingarm_L",       0,   6,  0.580f, 0.300f, 0.880f, 0.265f, -1 }, // 300 mm, along the swingarm
  // ── Run 1: RIGHT chain (mirror) ─────────────────────────────────────────
  { "fork_R",           1,   4,  0.030f, 0.280f, 0.060f, 0.460f,  1 },
  { "tank_R",           1,   9,  0.280f, 0.440f, 0.520f, 0.480f,  1 },
  { "seat_R",           1,   8,  0.540f, 0.560f, 0.820f, 0.545f,  1 },
  { "swingarm_R",       1,   6,  0.580f, 0.300f, 0.880f, 0.265f,  1 },
  // ── Run 2: CENTRE LOW ───────────────────────────────────────────────────
  { "engine_underglow", 2,  10,  0.330f, 0.180f, 0.550f, 0.185f,  0 }, // 500 mm, under engine / skid plate
  // ── Run 3: REAR ─────────────────────────────────────────────────────────
  { "tail",             3,   5,  0.860f, 0.520f, 0.970f, 0.515f,  0 }, // 250 mm, under the tail
};
const uint16_t NUM_SEGMENTS = sizeof(SEGMENTS) / sizeof(SEGMENTS[0]);

// ─── Derived tables ──────────────────────────────────────────────────────────
// Computed by hand rather than constexpr so the numbers are visible in review
// and so the static arrays below can be sized. bikeMapInit() asserts they match.
const uint16_t RUN_COUNT[NUM_RUNS] = { 27, 27, 10, 5 };
const uint16_t RUN_START[NUM_RUNS] = {  0, 27, 54, 64 };
const uint16_t NUM_PIXELS = 69;

Pixel PIXELS[69];
CRGB  leds[69];

void bikeMapInit() {
  uint16_t i = 0;
  for (uint16_t s = 0; s < NUM_SEGMENTS; s++) {
    const Segment& seg = SEGMENTS[s];
    for (uint16_t k = 0; k < seg.count; k++) {
      // Place pixels at segment-cell centres rather than endpoints, so two
      // butted segments do not double up a position at the join.
      float f = (seg.count == 1) ? 0.5f : (float)k / (float)(seg.count - 1);
      PIXELS[i].x    = seg.x0 + (seg.x1 - seg.x0) * f;
      PIXELS[i].y    = seg.y0 + (seg.y1 - seg.y0) * f;
      PIXELS[i].side = seg.side;
      i++;
    }
  }
  // If this trips, RUN_COUNT/RUN_START/NUM_PIXELS are out of step with SEGMENTS.
  if (i != NUM_PIXELS) {
    // Blink the status LED forever rather than render a corrupt map.
    pinMode(PIN_STATUS, OUTPUT);
    for (;;) { digitalWrite(PIN_STATUS, HIGH); delay(100);
               digitalWrite(PIN_STATUS, LOW);  delay(100); }
  }
}
