// Host test for the MotoGlow direction invariant.
//
// The single most important behavioural claim in this project is that every
// animation travels from the front of the bike to the rear. All effects derive
// their position from phaseAt() or behindHead(), so proving those two move the
// right way proves it for the whole preset library.
//
//   g++ -std=c++17 -O2 -o /tmp/test_phase tools/test_phase.cpp && /tmp/test_phase
#include "../firmware/motoglow/phase.h"
#include <cstdio>
#include <cmath>
#include <initializer_list>

static int failures = 0;
static void check(bool ok, const char* what) {
  if (!ok) { printf("  FAIL  %s\n", what); failures++; }
  else     { printf("  ok    %s\n", what); }
}

// Scan bike-space for the x that best matches the feature, i.e. minimises the
// phase function. That x is where the feature visibly is.
static float featureX(float (*fn)(float, float, float), float t, float speed) {
  float best = 0.0f, bestVal = 2.0f;
  for (int i = 0; i < 20000; i++) {
    float x = (float)i / 20000.0f;
    float v = fn(x, t, speed);
    float d = v > 0.5f ? 1.0f - v : v;   // distance to phase 0, wrapped
    if (d < bestVal) { bestVal = d; best = x; }
  }
  return best;
}

int main() {
  printf("fracf\n");
  check(fabsf(fracf(0.25f)  - 0.25f) < 1e-6f, "fracf(0.25) == 0.25");
  check(fabsf(fracf(-0.25f) - 0.75f) < 1e-6f, "fracf(-0.25) == 0.75  (negatives wrap up)");
  check(fabsf(fracf(3.5f)   - 0.50f) < 1e-6f, "fracf(3.5) == 0.5");
  check(fracf(-7.75f) >= 0.0f && fracf(-7.75f) < 1.0f, "fracf always in [0,1)");
  check(fabsf(fracf(-7.75f) - 0.25f) < 1e-6f, "fracf(-7.75) == 0.25  (large negatives)");

  printf("\nphaseAt: feature moves front -> rear as t increases\n");
  for (float speed : {0.09f, 0.20f, 0.38f, 0.85f}) {
    // Sample within a single traversal so there is no wrap to reason about.
    float period = 1.0f / speed;
    float prev = featureX(phaseAt, 0.02f * period, speed);
    bool monotonic = true;
    float travelled = 0.0f;
    for (int k = 2; k <= 48; k++) {
      float t = (k * 0.02f) * period;
      float x = featureX(phaseAt, t, speed);
      if (x < prev - 1e-3f) { monotonic = false; break; }
      travelled += x - prev;
      prev = x;
    }
    char buf[128];
    snprintf(buf, sizeof buf, "speed %.2f: feature x increases monotonically", speed);
    check(monotonic, buf);
    snprintf(buf, sizeof buf, "speed %.2f: traversed %.2f of the bike (expect ~0.92)", speed, travelled);
    check(travelled > 0.85f && travelled < 1.0f, buf);
  }

  printf("\nphaseAt: speed is honoured in bike-lengths per second\n");
  {
    float speed = 0.25f;                 // a quarter of the bike each second
    float x0 = featureX(phaseAt, 1.0f, speed);
    float x1 = featureX(phaseAt, 2.0f, speed);
    float step = x1 - x0; if (step < 0) step += 1.0f;
    check(fabsf(step - 0.25f) < 0.01f, "one second at speed 0.25 moves 0.25 bike-lengths");
  }

  printf("\nbehindHead: head travels rearward, tail trails toward the front\n");
  {
    float speed = 0.5f;
    float head0 = featureX(behindHead, 0.20f, speed);
    float head1 = featureX(behindHead, 0.60f, speed);
    float step = head1 - head0; if (step < 0) step += 1.0f;
    check(fabsf(step - 0.20f) < 0.01f, "comet head advances rearward at the set speed");

    // A point just FORWARD of the head must be recently-passed tail (small
    // behindHead), and a point just REARWARD must be far from the head.
    float t = 1.0f, head = fracf(t * speed);
    float justForward = fracf(head - 0.05f);
    float justRear    = fracf(head + 0.05f);
    check(behindHead(justForward, t, speed) < 0.06f,
          "0.05 in front of the head is bright tail (behindHead ~= 0.05)");
    check(behindHead(justRear, t, speed) > 0.90f,
          "0.05 behind the head is dark (behindHead ~= 0.95)");
  }

  printf("\nranges\n");
  {
    bool inRange = true;
    for (int i = 0; i < 5000; i++) {
      float x = (float)i / 5000.0f;
      float t = (float)i * 0.37f;
      for (float s : {0.09f, 1.7f, 0.85f * 1.7f}) {
        float a = phaseAt(x, t, s), b = behindHead(x, t, s);
        if (!(a >= 0.0f && a < 1.0f && b >= 0.0f && b < 1.0f)) inRange = false;
      }
    }
    check(inRange, "phaseAt/behindHead stay in [0,1) across 5000 samples");
  }

  printf("\nlong-running clock (the firmware wraps s_t at 100000 s)\n");
  {
    // At the fastest preset x speed multiplier, phase must still be sane after
    // hours of running. float32 has ~7 digits, so this is a real risk.
    float speed = 0.85f * 1.7f;
    float t = 99999.0f;
    float v = phaseAt(0.5f, t, speed);
    check(v >= 0.0f && v < 1.0f, "phase still in range at t = 99999 s");
    float a = phaseAt(0.5f, t, speed), b = phaseAt(0.5f, t + 1.0f, speed);
    float step = a - b; if (step < 0) step += 1.0f;
    check(fabsf(step - fracf(speed)) < 0.02f,
          "one second of motion still resolves correctly at t = 99999 s");
  }

  printf("\n%s (%d failure%s)\n", failures ? "FAILED" : "PASSED",
         failures, failures == 1 ? "" : "s");
  return failures ? 1 : 0;
}
