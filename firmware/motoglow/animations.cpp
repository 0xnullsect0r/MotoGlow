#include "animations.h"
#include <math.h>

// ─── Spark pool (M_SPARKLE) ──────────────────────────────────────────────────
// Sparks live in continuous bike-space, are born just ahead of the front axle
// and drift rearward. Rendering sums a narrow gaussian per spark, so sparks
// cross segment gaps smoothly instead of popping between LED indexes.
#define MAX_SPARKS 28
struct Spark { float x; float age; float life; uint8_t hue; bool active; };
static Spark  s_sparks[MAX_SPARKS];
static float  s_spawnAccum = 0.0f;

void effectsReset() {
  for (int i = 0; i < MAX_SPARKS; i++) s_sparks[i].active = false;
  s_spawnAccum = 0.0f;
}

static void sparkTick(const EffectParams& p, float dt) {
  for (int i = 0; i < MAX_SPARKS; i++) {
    if (!s_sparks[i].active) continue;
    s_sparks[i].x   += p.speed * dt;
    s_sparks[i].age += dt;
    if (s_sparks[i].x > 1.05f || s_sparks[i].age > s_sparks[i].life)
      s_sparks[i].active = false;
  }
  // p.param is sparks per second.
  s_spawnAccum += p.param * dt;
  while (s_spawnAccum >= 1.0f) {
    s_spawnAccum -= 1.0f;
    for (int i = 0; i < MAX_SPARKS; i++) {
      if (s_sparks[i].active) continue;
      s_sparks[i].x      = -0.02f;
      s_sparks[i].age    = 0.0f;
      s_sparks[i].life   = 1.2f + (random8() / 255.0f) * 1.8f;
      s_sparks[i].hue    = random8();
      s_sparks[i].active = true;
      break;
    }
  }
}

void effectsTick(Motion m, const EffectParams& p, float dt, float) {
  if (m == M_SPARKLE) sparkTick(p, dt);
}

// ─── Shading ─────────────────────────────────────────────────────────────────
static inline CRGB scaled(const CRGB& c, float f) {
  if (f <= 0.0f) return CRGB::Black;
  if (f >= 1.0f) return c;
  return CRGB((uint8_t)(c.r * f), (uint8_t)(c.g * f), (uint8_t)(c.b * f));
}

CRGB shadePixel(Motion m, const CRGBPalette16& pal, const EffectParams& p,
                const Pixel& px, float t) {
  switch (m) {

    case M_BLOCK: {
      // Wrapped distance to the leading edge of the block.
      float u = phaseAt(px.x, t, p.speed);
      float d = (u < 0.5f) ? u : 1.0f - u;
      float half = p.width * 0.5f;
      if (d <= half) {
        // Soft shoulder over the outer 20% of the block so the edges do not
        // strobe as the block steps between 50 mm COB cells.
        float edge = 1.0f;
        float soft = half * 0.20f;
        if (soft > 0.0f && d > half - soft) edge = (half - d) / soft;
        // Colour varies slightly across the block for depth.
        CRGB c = ColorFromPalette(pal, (uint8_t)(128 + (d / half) * 100.0f), 255, LINEARBLEND);
        return scaled(c, edge);
      }
      return scaled(ColorFromPalette(pal, 0, 255, LINEARBLEND), p.bgLevel / 255.0f * 0.35f);
    }

    case M_COMET: {
      float b = behindHead(px.x, t, p.speed);
      // p.param is the tail length in bike-lengths.
      float amp = expf(-b / (p.param > 0.001f ? p.param : 0.001f));
      CRGB c = ColorFromPalette(pal, (uint8_t)(255.0f * (1.0f - amp)), 255, LINEARBLEND);
      CRGB out = scaled(c, amp);
      uint8_t bg = p.bgLevel;
      if (bg) {
        CRGB base = scaled(ColorFromPalette(pal, 8, 255, LINEARBLEND), bg / 255.0f * 0.30f);
        out |= base;   // per-channel max, so the tail never dips below the base
      }
      return out;
    }

    case M_GRADIENT: {
      float u = phaseAt(px.x, t, p.speed);
      // p.param = how many palette repeats fit along the bike.
      uint8_t idx = (uint8_t)(fracf(u * p.param) * 255.0f);
      return ColorFromPalette(pal, idx, 255, LINEARBLEND);
    }

    case M_RAINBOW: {
      float u = phaseAt(px.x, t, p.speed);
      uint8_t hue = (uint8_t)(fracf(u * p.param) * 255.0f);
      return CHSV(hue, 245, 255);
    }

    case M_SPARKLE: {
      // Dim moving base so the bike never goes fully dark between sparks.
      float u = phaseAt(px.x, t, p.speed * 0.25f);
      CRGB out = scaled(ColorFromPalette(pal, (uint8_t)(u * 255.0f), 255, LINEARBLEND),
                        p.bgLevel / 255.0f * 0.22f);
      float sigma = p.width * 0.5f;
      if (sigma < 0.004f) sigma = 0.004f;
      for (int i = 0; i < MAX_SPARKS; i++) {
        if (!s_sparks[i].active) continue;
        float d = px.x - s_sparks[i].x;
        if (d < -0.12f || d > 0.12f) continue;
        float g = expf(-(d * d) / (2.0f * sigma * sigma));
        // Fade each spark in and out over its life.
        float lf = 1.0f - (s_sparks[i].age / s_sparks[i].life);
        CRGB c = ColorFromPalette(pal, s_sparks[i].hue, 255, LINEARBLEND);
        out |= scaled(c, g * lf);
      }
      return out;
    }

    case M_BARBER: {
      // Stagger the two sides so the stripes read as a helix around the bike.
      float offset = (px.side < 0) ? 0.0f : (px.side > 0 ? 0.5f : 0.25f);
      float u = fracf((phaseAt(px.x, t, p.speed) * p.param) + offset);
      // Hard edges, softened just enough not to alias on 50 mm cells.
      uint8_t band = (u < 0.5f) ? 0 : 255;
      float edgeD = fminf(fabsf(u - 0.5f), fminf(u, 1.0f - u));
      float soft  = 0.06f;
      CRGB c = ColorFromPalette(pal, band, 255, LINEARBLEND);
      if (edgeD < soft) {
        CRGB other = ColorFromPalette(pal, band ? 0 : 255, 255, LINEARBLEND);
        c = blend(other, c, (uint8_t)(128 + (edgeD / soft) * 127.0f));
      }
      return c;
    }

    case M_PULSE: {
      // Palette laid out along the bike, with a brightness wave running rearward.
      CRGB base = ColorFromPalette(pal, (uint8_t)(px.x * 255.0f), 255, LINEARBLEND);
      float u = phaseAt(px.x, t, p.speed);
      float wave = 0.5f + 0.5f * cosf(u * p.param * 6.2831853f);
      float amp  = (p.bgLevel / 255.0f) + (1.0f - p.bgLevel / 255.0f) * wave;
      return scaled(base, amp);
    }

    case M_EMBER: {
      // A noise field sampled at (x - t*speed) drifts rearward by construction.
      float q = (px.x - t * p.speed) * p.param;
      uint16_t nx = (uint16_t)(fracf(q / 16.0f) * 65535.0f);
      uint16_t ny = (uint16_t)(px.y * 12000.0f);
      uint8_t  h  = inoise8(nx, ny);
      h = qsub8(h, 16);
      h = qadd8(scale8(h, 200), 24);
      return ColorFromPalette(pal, h, 255, LINEARBLEND);
    }
  }
  return CRGB::Black;
}
