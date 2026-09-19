#include "presets.h"

// ─── Palettes ────────────────────────────────────────────────────────────────
// How a palette is read depends on the motion it is paired with:
//   M_BLOCK    index 0 = background tint, 128 = block core, 228 = block edge
//   M_COMET    index 0 = head colour, 255 = far tail colour, 8 = background
//   M_BARBER   index 0 and 255 are the two stripe colours
//   M_PULSE    laid out along the bike, front = 0, rear = 255
//   others     read across the whole range
#define GP DEFINE_GRADIENT_PALETTE

GP(p_ignition) {       // orange block, white-hot core, near-black background
    0,   6,  1,  0,
  100,  10,  2,  0,
  128, 255,255,225,
  160, 255,120,  0,
  228, 255, 40,  0,
  255,  40,  4,  0 };

GP(p_orange_crush) {   // KTM orange through amber and back
    0, 255, 55,  0,
   70, 255,120,  0,
  130, 255,180, 25,
  190, 255, 90,  0,
  255, 255, 55,  0 };

GP(p_race) {           // comet: white head into orange into deep red tail
    0, 255,245,230,
   40, 255,140,  0,
  120, 255, 45,  0,
  255,  24,  2,  0 };

GP(p_ice) {            // white -> cyan -> deep blue
    0, 235,250,255,
   64,  70,200,255,
  140,   0, 90,230,
  200,   4, 30,140,
  255, 235,250,255 };

GP(p_deep_blue) {      // block: white leading edge over electric blue
    0,   0,  2, 14,
  100,   2,  6, 30,
  128, 230,245,255,
  170,  10, 90,255,
  228,   0, 30,190,
  255,   0,  8, 60 };

GP(p_menace) {         // comet: white-hot head, blood red tail
    0, 255,200,180,
   30, 255, 30,  0,
  110, 150,  0,  0,
  255,  30,  0,  0 };

GP(p_synthwave) {      // barber: magenta vs cyan
    0, 255,  0,140,
  110, 255, 30,180,
  145,   0,220,255,
  255,   0,160,255 };

GP(p_toxic) {          // acid greens and a little lime
    0,  30,255,  0,
   90, 170,255,  0,
  160,  10,255, 60,
  255,  60,255,  0 };

GP(p_gold) {           // warm gold, champagne highlights
    0, 255,150,  0,
   80, 255,200, 60,
  150, 255,235,170,
  255, 255,140,  0 };

GP(p_violet) {         // purple -> pink -> violet
    0, 120,  0,255,
   70, 220,  0,220,
  140, 255, 40,150,
  200, 170,  0,255,
  255, 120,  0,255 };

GP(p_firefly) {        // warm white sparks on almost nothing
    0, 255,190,110,
  120, 255,225,175,
  200, 255,160, 70,
  255, 255,190,110 };

GP(p_ember) {          // classic heat ramp for the noise field
    0,   0,  0,  0,
   40, 120,  0,  0,
  110, 235, 45,  0,
  180, 255,140,  0,
  230, 255,215, 90,
  255, 255,255,210 };

GP(p_arctic) {         // pulse base: pale ice to deep glacier
    0, 200,240,255,
   90,  40,150,255,
  170,   0, 70,200,
  255, 160,225,255 };

GP(p_midnight) {       // very deep indigo, barely-there
    0,   8,  0, 40,
   80,  30,  0,110,
  150,  60, 10,160,
  220,  20,  0, 80,
  255,   8,  0, 40 };

GP(p_mono_white) {     // block: clean white over black, the "chrome" look
    0,   2,  2,  3,
  100,   6,  6,  8,
  128, 255,255,255,
  180, 210,225,255,
  228, 120,160,220,
  255,  10, 14, 24 };

static const CRGBPalette16 PAL_IGNITION(p_ignition);
static const CRGBPalette16 PAL_ORANGE  (p_orange_crush);
static const CRGBPalette16 PAL_RACE    (p_race);
static const CRGBPalette16 PAL_ICE     (p_ice);
static const CRGBPalette16 PAL_DEEPBLUE(p_deep_blue);
static const CRGBPalette16 PAL_MENACE  (p_menace);
static const CRGBPalette16 PAL_SYNTH   (p_synthwave);
static const CRGBPalette16 PAL_TOXIC   (p_toxic);
static const CRGBPalette16 PAL_GOLD    (p_gold);
static const CRGBPalette16 PAL_VIOLET  (p_violet);
static const CRGBPalette16 PAL_FIREFLY (p_firefly);
static const CRGBPalette16 PAL_EMBER   (p_ember);
static const CRGBPalette16 PAL_ARCTIC  (p_arctic);
static const CRGBPalette16 PAL_MIDNIGHT(p_midnight);
static const CRGBPalette16 PAL_WHITE   (p_mono_white);

// ─── Presets ─────────────────────────────────────────────────────────────────
// fx = { speed (bike-lengths/sec), width, param, background level }
// Every one of these moves front to rear. That is not a per-preset choice —
// the primitives in animations.h cannot express any other direction.
const Preset PRESETS[] = {
  { "Ignition",      M_BLOCK,    &PAL_IGNITION, { 0.38f, 0.22f, 0.0f,  18 } },
  { "Orange Crush",  M_GRADIENT, &PAL_ORANGE,   { 0.22f, 0.0f,  1.0f,   0 } },
  { "Ready to Race", M_COMET,    &PAL_RACE,     { 0.85f, 0.0f,  0.16f, 30 } },
  { "Rainbow Flow",  M_RAINBOW,  &PAL_ICE,      { 0.20f, 0.0f,  1.0f,   0 } },
  { "Ice",           M_GRADIENT, &PAL_ICE,      { 0.14f, 0.0f,  1.0f,   0 } },
  { "Deep Blue",     M_BLOCK,    &PAL_DEEPBLUE, { 0.30f, 0.28f, 0.0f,  26 } },
  { "Chrome",        M_BLOCK,    &PAL_WHITE,    { 0.34f, 0.20f, 0.0f,  14 } },
  { "Menace",        M_COMET,    &PAL_MENACE,   { 0.55f, 0.0f,  0.22f, 55 } },
  { "Synthwave",     M_BARBER,   &PAL_SYNTH,    { 0.30f, 0.0f,  4.0f,   0 } },
  { "Toxic",         M_SPARKLE,  &PAL_TOXIC,    { 0.65f, 0.05f, 9.0f,  40 } },
  { "Gold Rush",     M_SPARKLE,  &PAL_GOLD,     { 0.45f, 0.06f, 6.0f,  90 } },
  { "Violet Drift",  M_GRADIENT, &PAL_VIOLET,   { 0.12f, 0.0f,  1.0f,   0 } },
  { "Firefly",       M_SPARKLE,  &PAL_FIREFLY,  { 0.28f, 0.045f,3.0f,  12 } },
  { "Ember",         M_EMBER,    &PAL_EMBER,    { 0.18f, 0.0f, 26.0f,   0 } },
  { "Arctic Pulse",  M_PULSE,    &PAL_ARCTIC,   { 0.35f, 0.0f,  2.5f,  60 } },
  { "Midnight",      M_PULSE,    &PAL_MIDNIGHT, { 0.09f, 0.0f,  1.5f,  35 } },
};
const uint8_t NUM_PRESETS = sizeof(PRESETS) / sizeof(PRESETS[0]);
