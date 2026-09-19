// ─────────────────────────────────────────────────────────────────────────────
//  MotoGlow — addressable accent lighting for a KTM 890 Adventure
//
//  Target : Raspberry Pi Pico 2 W   (rp2040:rp2040:rpipico2w)
//  Strips : 12 V addressable COB, WS2811, 20 px/m, 4 runs, 69 pixels total
//
//  Animations are rendered in bike-space, not in LED-index space — see
//  bike_map.h for why that matters. Every effect travels front to rear.
// ─────────────────────────────────────────────────────────────────────────────
#include <FastLED.h>
#include "config.h"
#include "bike_map.h"
#include "animations.h"
#include "presets.h"
#include "input.h"
#include "power.h"
#include "storage.h"
#include "boot_anim.h"

static const float SPEED_TABLE[]  = SPEED_LEVELS;
static const float BRIGHT_TABLE[] = BRIGHTNESS_LEVELS;
static const uint8_t NUM_SPEEDS  = sizeof(SPEED_TABLE)  / sizeof(SPEED_TABLE[0]);
static const uint8_t NUM_BRIGHTS = sizeof(BRIGHT_TABLE) / sizeof(BRIGHT_TABLE[0]);

static float    s_t          = 0.0f;   // animation clock, seconds
static uint32_t s_lastFrame  = 0;
static uint32_t s_lastInput  = 0;

// Preset crossfade
static uint8_t  s_prevPreset = 0;
static uint32_t s_fadeStart  = 0;
#define FADE_MS 400

static uint8_t targetBrightness() {
  float f = BRIGHT_TABLE[g_settings.brightness % NUM_BRIGHTS];
  uint8_t b = (uint8_t)(BRIGHTNESS_CAP * f);
  return b ? b : 1;
}

// ─── Feedback ────────────────────────────────────────────────────────────────
// Short acknowledgements for settings that have no other visible effect.
static void blipAck(uint8_t count, uint8_t level) {
  for (uint8_t i = 0; i < count; i++) {
    fill_solid(leds, NUM_PIXELS, CRGB(255, 250, 240));
    FastLED.setBrightness(limitBrightness(leds, NUM_PIXELS, level));
    FastLED.show();
    delay(70);
    fill_solid(leds, NUM_PIXELS, CRGB::Black);
    FastLED.show();
    delay(90);
  }
}

// ─── Rendering ───────────────────────────────────────────────────────────────
static void renderPreset(const Preset& pr, float t, float speedMul, CRGB* dst) {
  EffectParams fx = pr.fx;
  fx.speed *= speedMul;
  for (uint16_t i = 0; i < NUM_PIXELS; i++)
    dst[i] = shadePixel(pr.motion, *pr.palette, fx, PIXELS[i], t);
}

static CRGB s_scratch[69];

static void renderFrame(float dt) {
  const float speedMul = SPEED_TABLE[g_settings.speed % NUM_SPEEDS];
  const Preset& cur = PRESETS[g_settings.preset % NUM_PRESETS];

  EffectParams tickFx = cur.fx;
  tickFx.speed *= speedMul;
  effectsTick(cur.motion, tickFx, dt, s_t);

  renderPreset(cur, s_t, speedMul, leds);

  // Crossfade out of the previous preset so switching does not snap.
  uint32_t since = millis() - s_fadeStart;
  if (s_fadeStart && since < FADE_MS) {
    const Preset& prev = PRESETS[s_prevPreset % NUM_PRESETS];
    renderPreset(prev, s_t, speedMul, s_scratch);
    uint8_t mix = (uint8_t)(255.0f * (float)since / (float)FADE_MS);
    for (uint16_t i = 0; i < NUM_PIXELS; i++) leds[i] = blend(s_scratch[i], leds[i], mix);
  } else {
    s_fadeStart = 0;
  }
}

// ─── Button handling ─────────────────────────────────────────────────────────
static void selectPreset(uint8_t next) {
  if (next == g_settings.preset) return;
  s_prevPreset = g_settings.preset;
  s_fadeStart  = millis();
  if (!s_fadeStart) s_fadeStart = 1;   // millis() can be 0 exactly once
  g_settings.preset = next;
  settingsTouch();
}

static void handleButton() {
  ButtonEvent ev = buttonPoll();
  if (ev == EV_NONE) return;
  s_lastInput = millis();

  switch (ev) {
    case EV_SHORT:
      selectPreset((uint8_t)((g_settings.preset + 1) % NUM_PRESETS));
      break;
    case EV_DOUBLE:
      selectPreset((uint8_t)((g_settings.preset + NUM_PRESETS - 1) % NUM_PRESETS));
      break;
    case EV_TRIPLE:
      selectPreset(0);
      break;
    case EV_LONG:
      g_settings.brightness = (uint8_t)((g_settings.brightness + 1) % NUM_BRIGHTS);
      settingsTouch();
      blipAck(1, targetBrightness());
      break;
    case EV_VLONG:
      g_settings.speed = (uint8_t)((g_settings.speed + 1) % NUM_SPEEDS);
      settingsTouch();
      blipAck((uint8_t)(g_settings.speed + 1), targetBrightness());
      break;
    default: break;
  }
}

// ─── Status LED ──────────────────────────────────────────────────────────────
static void updateStatusLed() {
  uint32_t m = millis();
  bool on;
  switch (powerState()) {
    case PW_CRITICAL: on = (m % 200)  < 100; break;   // fast: battery is low, switch off
    case PW_WARN:     on = (m % 1200) < 200; break;   // slow blink: getting low
    default:          on = (m % 3000) < 40;  break;   // heartbeat: alive
  }
  digitalWrite(PIN_STATUS, on ? HIGH : LOW);
}

// ─── Setup / loop ────────────────────────────────────────────────────────────
void setup() {
  pinMode(PIN_STATUS, OUTPUT);
  digitalWrite(PIN_STATUS, HIGH);

  bikeMapInit();

  FastLED.addLeds<LED_CHIPSET, PIN_RUN0, LED_COLOR_ORDER>(leds + RUN_START[0], RUN_COUNT[0]);
  FastLED.addLeds<LED_CHIPSET, PIN_RUN1, LED_COLOR_ORDER>(leds + RUN_START[1], RUN_COUNT[1]);
  FastLED.addLeds<LED_CHIPSET, PIN_RUN2, LED_COLOR_ORDER>(leds + RUN_START[2], RUN_COUNT[2]);
  FastLED.addLeds<LED_CHIPSET, PIN_RUN3, LED_COLOR_ORDER>(leds + RUN_START[3], RUN_COUNT[3]);

  // Temporal dithering looks good to the eye but beats against phone cameras,
  // and this bike is going to get filmed. Off.
  FastLED.setDither(0);
  FastLED.clear(true);

  settingsLoad();
  powerInit();
  buttonInit();
  effectsReset();

  s_lastFrame = millis();
  s_lastInput = millis();

#if COLOR_ORDER_TEST
  // Flash this, then confirm each run shows RED, GREEN, BLUE on its first three
  // pixels. If not, change LED_COLOR_ORDER in config.h.
  for (;;) {
    fill_solid(leds, NUM_PIXELS, CRGB::Black);
    for (uint8_t r = 0; r < NUM_RUNS; r++) {
      if (RUN_COUNT[r] > 0) leds[RUN_START[r] + 0] = CRGB::Red;
      if (RUN_COUNT[r] > 1) leds[RUN_START[r] + 1] = CRGB::Green;
      if (RUN_COUNT[r] > 2) leds[RUN_START[r] + 2] = CRGB::Blue;
    }
    FastLED.setBrightness(60);
    FastLED.show();
    delay(500);
  }
#endif

  runBootAnimation(PRESETS[g_settings.preset % NUM_PRESETS], targetBrightness());
}

void loop() {
  uint32_t now = millis();
  float dt = (now - s_lastFrame) / 1000.0f;
  if (dt < 1.0f / TARGET_FPS) { delay(1); return; }
  if (dt > 0.25f) dt = 0.25f;          // never let a stall jump the animation
  s_lastFrame = now;

  handleButton();
  powerTick();
  settingsTick();
  updateStatusLed();

  // Battery protection takes priority over whatever preset is selected.
  if (powerState() == PW_CRITICAL) {
    fill_solid(leds, NUM_PIXELS, CRGB::Black);
    FastLED.setBrightness(0);
    FastLED.show();
    return;
  }

  s_t += dt;
  if (s_t > 100000.0f) s_t -= 100000.0f;   // keep float precision usable

  renderFrame(dt);

  uint8_t want = targetBrightness();

  if (powerState() == PW_WARN) {
    // Visibly back off and breathe, so it is obvious from outside the bike
    // that the pack is getting low rather than the lights just looking dim.
    float breathe = 0.45f + 0.55f * (0.5f + 0.5f * cosf(now / 500.0f));
    want = (uint8_t)(want * 0.30f * breathe);
    if (!want) want = 1;
  }

#if IDLE_FADE_MINUTES > 0
  if (!engineRunning()) {
    uint32_t idleMs = now - s_lastInput;
    uint32_t limit  = (uint32_t)IDLE_FADE_MINUTES * 60000UL;
    if (idleMs > limit) {
      uint32_t over = idleMs - limit;
      if (over > 10000UL) { want = 0; }
      else { want = (uint8_t)(want * (1.0f - over / 10000.0f)); }
    }
  } else {
    s_lastInput = now;   // engine running resets the idle timer
  }
#endif

  FastLED.setBrightness(limitBrightness(leds, NUM_PIXELS, want));
  FastLED.show();
}
