#include "boot_anim.h"
#include "bike_map.h"
#include "power.h"
#include "config.h"
#include <math.h>

// Timeline, in milliseconds from power-on:
//   0 -  300   first sweep: narrow white band, front axle to tail
// 260 -  540   second sweep: faster and slightly wider, overlapping the first
// 540 - 1120   bloom: the preset rises everywhere, overshooting then settling
//1120 - 1450   settle: the white cast drains out, leaving the preset running
#define T_SWEEP1_END   300.0f
#define T_SWEEP2_BEG   260.0f
#define T_SWEEP2_END   540.0f
#define T_BLOOM_BEG    540.0f
#define T_BLOOM_END   1120.0f
#define T_SETTLE_END  1450.0f

static inline float clamp01(float v) { return v < 0 ? 0 : (v > 1 ? 1 : v); }
static inline float easeOut(float v)  { float k = 1.0f - v; return 1.0f - k * k * k; }

// A band centred at cx with the given half-width, in bike-space.
static float band(float x, float cx, float halfWidth) {
  float d = fabsf(x - cx);
  if (d >= halfWidth) return 0.0f;
  float f = 1.0f - d / halfWidth;
  return f * f;   // soft shoulders, so the band does not step between cells
}

void runBootAnimation(const Preset& target, uint8_t brightness) {
  const uint32_t t0 = millis();
  EffectParams fx = target.fx;

  for (;;) {
    float ms = (float)(millis() - t0);
    if (ms > T_SETTLE_END) break;

    for (uint16_t i = 0; i < NUM_PIXELS; i++) {
      const Pixel& p = PIXELS[i];
      CRGB out = CRGB::Black;

      // ── Sweeps ──────────────────────────────────────────────────────────
      if (ms <= T_SWEEP1_END) {
        float u  = ms / T_SWEEP1_END;
        float cx = -0.15f + u * 1.30f;          // starts ahead of the front axle
        float a  = band(p.x, cx, 0.13f);
        out |= CRGB((uint8_t)(255 * a), (uint8_t)(250 * a), (uint8_t)(235 * a));
      }
      if (ms >= T_SWEEP2_BEG && ms <= T_SWEEP2_END) {
        float u  = (ms - T_SWEEP2_BEG) / (T_SWEEP2_END - T_SWEEP2_BEG);
        float cx = -0.15f + u * 1.30f;
        float a  = band(p.x, cx, 0.18f);
        out |= CRGB((uint8_t)(255 * a), (uint8_t)(255 * a), (uint8_t)(255 * a));
      }

      // ── Bloom and settle ────────────────────────────────────────────────
      if (ms >= T_BLOOM_BEG) {
        // The preset, frozen at t=0 so the reveal is a still image that then
        // starts moving as the main loop takes over.
        CRGB pc = shadePixel(target.motion, *target.palette, fx, p, 0.0f);

        float amp, white;
        if (ms <= T_BLOOM_END) {
          float u = (ms - T_BLOOM_BEG) / (T_BLOOM_END - T_BLOOM_BEG);
          float e = easeOut(u);
          amp   = e * 1.15f;                    // deliberate overshoot
          white = clamp01(1.0f - u * 1.4f);     // starts white, gains colour
        } else {
          float u = (ms - T_BLOOM_END) / (T_SETTLE_END - T_BLOOM_END);
          amp   = 1.15f - 0.15f * easeOut(u);   // relax back down to 1.0
          white = 0.0f;
        }
        CRGB blended = blend(pc, CRGB(255, 252, 245), (uint8_t)(white * 255.0f));
        float a = clamp01(amp);
        out |= CRGB((uint8_t)(blended.r * a), (uint8_t)(blended.g * a), (uint8_t)(blended.b * a));
      }

      leds[i] = out;
    }

    FastLED.setBrightness(limitBrightness(leds, NUM_PIXELS, brightness));
    FastLED.show();
    delay(1000 / TARGET_FPS);
  }
}
