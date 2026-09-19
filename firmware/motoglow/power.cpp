#include "power.h"
#include "config.h"

static float      s_volts   = 12.6f;
static PowerState s_state   = PW_NORMAL;
static uint32_t   s_lowSince = 0;

// Full-white current for a single pixel, derived from the strip's datasheet
// figures in config.h rather than guessed. For the default 12 V 720 LEDs/m
// FCOB (10 W/m, 20 px/m) this is 0.5 W / 12 V = 41.7 mA.
static const float MA_PER_PIXEL_FULL =
    (STRIP_WATTS_PER_M / PIXELS_PER_METER) / SUPPLY_VOLTS * 1000.0f;

void powerInit() {
  analogReadResolution(12);
  pinMode(PIN_VSENSE, INPUT);
  // Seed the filter so the first frames do not see a false brownout.
  for (int i = 0; i < 16; i++) powerTick();
  s_lowSince = 0;
  s_state = PW_NORMAL;
}

float batteryVolts()   { return s_volts; }
bool  engineRunning()  { return s_volts >= V_CHARGING; }
PowerState powerState(){ return s_state; }

void powerTick() {
  int raw = analogRead(PIN_VSENSE);
  float atPin = (raw / 4095.0f) * VSENSE_ADC_REF;
  float v = atPin * (VSENSE_R_TOP + VSENSE_R_BOTTOM) / VSENSE_R_BOTTOM;
  // Heavy smoothing: the rail moves with every animation frame's current draw,
  // and a single dip must not be read as a flat battery.
  s_volts += (v - s_volts) * 0.02f;

#if BATTERY_PROTECT
  uint32_t now = millis();
  if (s_volts < V_CRITICAL) {
    if (!s_lowSince) s_lowSince = now;
    if (now - s_lowSince > (uint32_t)V_WARN_HOLD_S * 1000UL) s_state = PW_CRITICAL;
  } else if (s_volts < V_WARN) {
    if (!s_lowSince) s_lowSince = now;
    if (now - s_lowSince > (uint32_t)V_WARN_HOLD_S * 1000UL)
      s_state = (s_state == PW_CRITICAL) ? PW_CRITICAL : PW_WARN;
  } else {
    s_lowSince = 0;
    // Recover only well clear of the threshold, so it cannot chatter.
    if (s_volts > V_WARN + 0.4f) s_state = PW_NORMAL;
  }
#endif
}

float estimateAmps(const CRGB* px, uint16_t n, uint8_t brightness) {
  uint32_t sum = 0;
  for (uint16_t i = 0; i < n; i++) sum += px[i].r + px[i].g + px[i].b;
  float duty = (float)sum / (765.0f * (float)n);          // 0..1 across the run
  float mA   = duty * n * MA_PER_PIXEL_FULL * (brightness / 255.0f);
  return mA / 1000.0f;
}

uint8_t limitBrightness(const CRGB* px, uint16_t n, uint8_t desired) {
  float amps = estimateAmps(px, n, desired);
  float budget = MAX_STRIP_CURRENT_MA / 1000.0f;
  if (amps <= budget || amps <= 0.0001f) return desired;
  float scale = budget / amps;
  uint8_t out = (uint8_t)(desired * scale);
  return out < 1 ? 1 : out;
}
