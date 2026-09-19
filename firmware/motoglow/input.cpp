#include "input.h"
#include "config.h"

static bool     s_stable      = true;   // true = released (active LOW input)
static bool     s_lastRaw     = true;
static uint32_t s_lastChange  = 0;
static uint32_t s_pressStart  = 0;
static uint8_t  s_clicks      = 0;
static uint32_t s_lastRelease = 0;
static bool     s_holdFired   = false;
static bool     s_vlongFired  = false;

void buttonInit() {
  pinMode(PIN_BUTTON, INPUT_PULLUP);   // external 10k as well, for the long run
  s_stable = s_lastRaw = digitalRead(PIN_BUTTON);
  s_lastChange = millis();
}

ButtonEvent buttonPoll() {
  uint32_t now = millis();
  bool raw = digitalRead(PIN_BUTTON);

  if (raw != s_lastRaw) { s_lastRaw = raw; s_lastChange = now; }

  if (raw != s_stable && (now - s_lastChange) >= BTN_DEBOUNCE_MS) {
    s_stable = raw;
    if (!s_stable) {                       // pressed
      s_pressStart = now;
      s_holdFired = s_vlongFired = false;
    } else {                               // released
      if (!s_holdFired && !s_vlongFired) {
        s_clicks++;
        s_lastRelease = now;
      }
      // A hold has already reported itself; the release just ends it.
    }
  }

  // Holds fire while the button is still down, so the feedback is immediate.
  if (!s_stable) {
    uint32_t held = now - s_pressStart;
    if (!s_vlongFired && held >= BTN_VLONG_MS) {
      s_vlongFired = true; s_clicks = 0; return EV_VLONG;
    }
    if (!s_holdFired && held >= BTN_LONG_MS) {
      s_holdFired = true; s_clicks = 0; return EV_LONG;
    }
    return EV_NONE;
  }

  // Click runs resolve once the multi-press window closes.
  if (s_clicks && (now - s_lastRelease) >= BTN_MULTI_GAP_MS) {
    uint8_t n = s_clicks;
    s_clicks = 0;
    if (n == 1) return EV_SHORT;
    if (n == 2) return EV_DOUBLE;
    return EV_TRIPLE;
  }
  return EV_NONE;
}
