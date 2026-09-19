// MotoGlow — build-time configuration
// Everything you are likely to want to change lives in this file.
#pragma once

// ─── Board ───────────────────────────────────────────────────────────────────
// Target: Raspberry Pi Pico 2 W  (FQBN rp2040:rp2040:rpipico2w)
// The W variant is specified so Bluetooth control can be added later without
// changing the board. The radio is never initialised by this firmware.

// ─── Pin map (see docs/WIRING.md) ────────────────────────────────────────────
#define PIN_RUN0        2   // LEFT chain   : fork L -> tank L -> seat L -> swingarm L
#define PIN_RUN1        3   // RIGHT chain  : fork R -> tank R -> seat R -> swingarm R
#define PIN_RUN2        4   // CENTRE LOW   : engine underglow
#define PIN_RUN3        5   // REAR         : tail
#define PIN_BUTTON      6   // momentary, active LOW, external 10k pull-up
#define PIN_STATUS      7   // on-board status LED (through 1k)
#define PIN_VSENSE     26   // ADC0, 47k/10k divider off the switched 12V rail

// ─── LED strip ───────────────────────────────────────────────────────────────
// Default part: BTF-LIGHTING FCOB WS2811 RGB, 12 V, 720 LEDs/m, 20 ICs/m.
// One "pixel" is a 50 mm continuously-glowing block — that is the cut interval.
#define LED_CHIPSET         WS2811
#define LED_COLOR_ORDER     GRB     // verify with COLOR_ORDER_TEST below
#define PIXELS_PER_METER    20.0f
#define STRIP_WATTS_PER_M   10.0f   // 12 V 720 LEDs/m FCOB, full white

// Set to 1, flash, and check: pixel 0 = RED, 1 = GREEN, 2 = BLUE on every run.
// If the colours are wrong, change LED_COLOR_ORDER until they are right.
#define COLOR_ORDER_TEST    0

// ─── Power budget ────────────────────────────────────────────────────────────
// The renderer estimates strip current every frame and scales brightness down
// if a frame would exceed this. Keep it comfortably under the fuse rating.
#define MAX_STRIP_CURRENT_MA   4000
#define SUPPLY_VOLTS           12.0f

// Battery protection. The bike is wired battery-direct, so the firmware watches
// the pack and gets progressively more insistent rather than silently draining.
#define VSENSE_R_TOP        47000.0f
#define VSENSE_R_BOTTOM     10000.0f
#define VSENSE_ADC_REF      3.3f
#define V_CHARGING          13.0f  // above this, the engine is running
#define V_WARN              11.6f  // below this for V_WARN_HOLD_S: dim + pulse
#define V_CRITICAL          11.0f  // below this: strips off, status LED blinks
#define V_WARN_HOLD_S       20     // sustained seconds before acting
#define BATTERY_PROTECT     1      // set 0 to disable all voltage-based action

// Optional idle timeout. OFF by default: you asked for "on whenever the switch
// is on". Set to a non-zero number of minutes to fade out after that long
// without the engine running. Any button press resets the timer.
#define IDLE_FADE_MINUTES   0

// ─── Motion ──────────────────────────────────────────────────────────────────
#define TARGET_FPS          60
// Global speed multipliers cycled by a 3-second button hold.
#define SPEED_LEVELS        { 0.55f, 1.00f, 1.70f }
// Brightness levels cycled by a 0.8-second button hold, as a fraction of cap.
#define BRIGHTNESS_LEVELS   { 0.18f, 0.40f, 0.70f, 1.00f }
#define BRIGHTNESS_CAP      255

// ─── Button timing (ms) ──────────────────────────────────────────────────────
#define BTN_DEBOUNCE_MS     25
#define BTN_LONG_MS         800
#define BTN_VLONG_MS        3000
#define BTN_MULTI_GAP_MS    300   // window for double/triple press

// ─── Persistence ─────────────────────────────────────────────────────────────
#define SETTINGS_SAVE_DELAY_MS  5000  // idle time before a flash write
#define SETTINGS_MAGIC          0x4D47   // 'MG'
#define SETTINGS_VERSION        1
