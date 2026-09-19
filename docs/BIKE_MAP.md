# The bike map

This is the part that makes the difference between "LED strips on a motorcycle"
and something that looks like it was designed for the bike.

## The idea

Almost every DIY strip controller animates against the LED index: pixel 0, then
1, then 2. That works on a straight strip on a bench. On a bike it falls apart,
because the LEDs are not in a line. A run goes up a fork leg, jumps a metre of
empty air to the tank, runs level along the seat, then drops onto a swingarm.
An index sweep moving at constant speed crawls up the fork, teleports across the
gap, then races down the seat line. It reads as four separate strips blinking in
sequence.

MotoGlow gives every pixel a physical position on the bike and renders effects
as a function of **position and time**, not index. A block moving at 0.38
bike-lengths per second moves at that speed across the *bike*: it takes the
right amount of time to cross the fork, disappears into the gap for exactly as
long as the gap is wide, and reappears on the tank in the right place. Your eye
joins it up.

The coordinate system, from `firmware/motoglow/bike_map.h`:

```
x      0.0 = front axle          1.0 = rear axle
       (wheelbase of the 890 Adventure is 1509 mm, so 0.1 x ≈ 151 mm)
y      0.0 = ground              1.0 = 1350 mm up
side  -1 = left    0 = centre    +1 = right
```

## The stock layout

Shipped in `bike_map.cpp`, for a 2023 890 Adventure with 50 mm-per-pixel COB:

| Segment | Run | Px | Length | x from → to | y |
|---|---|---:|---:|---|---|
| fork_L | 0 | 4 | 200 mm | 0.030 → 0.060 | 0.28 → 0.46 |
| tank_L | 0 | 9 | 450 mm | 0.280 → 0.520 | 0.44 → 0.48 |
| seat_L | 0 | 8 | 400 mm | 0.540 → 0.820 | 0.56 → 0.545 |
| swingarm_L | 0 | 6 | 300 mm | 0.580 → 0.880 | 0.30 → 0.265 |
| *(right side mirrors the left on run 1)* | 1 | 27 | | | |
| engine_underglow | 2 | 10 | 500 mm | 0.330 → 0.550 | 0.18 |
| tail | 3 | 5 | 250 mm | 0.860 → 0.970 | 0.52 |

**69 pixels, 3.45 m of strip.** Full white at once would be 2.88 A; the firmware
caps frames at 2.5 A.

These numbers are my best reading of an 890 Adventure's proportions, not
measurements of *your* bike. They will look fine as shipped. They will look
better after ten minutes with a tape measure.

## Measuring your own

You need two numbers per segment end: how far back it sits, and how high.

1. Put the bike on level ground, on the centre stand or a paddock stand, with
   the forks straight.
2. Measure the **wheelbase**, axle centre to axle centre. Call it `W`
   (1509 mm stock).
3. For each end of each strip segment, measure the horizontal distance back
   from the **front axle centre**. Divide by `W` — that's your `x`.
4. Measure its height off the ground. Divide by 1350 — that's your `y`.
5. Count pixels: segment length in mm ÷ 50 (or ÷ your strip's cut interval).

Then edit the `SEGMENTS` table. Nothing else in the firmware needs to change.

```c
{ "tank_L",  0,  9,  0.280f, 0.440f,  0.520f, 0.480f, -1 },
//  name    run  n     x0      y0       x1      y1   side
```

Rules the code relies on:

- **Segments must be grouped by run**, and runs must appear in order 0, 1, 2, 3.
- `x0,y0` is the position of the segment's **first** pixel — the end nearest the
  controller in the data chain. If you wire a segment back-to-front, swap the
  start and end coordinates rather than reversing anything in code.
- After changing pixel counts, update `RUN_COUNT`, `RUN_START` and `NUM_PIXELS`
  at the bottom of `bike_map.cpp`, and the array sizes on the two lines below
  them. Get it wrong and the firmware blinks the status LED at 5 Hz forever
  instead of rendering a corrupt map — a deliberate check, not an accident.

## Adding a segment

Say you add 300 mm under the beak, 6 pixels, on the front of run 0:

```c
{ "beak", 0, 6, 0.090f, 0.560f, 0.150f, 0.570f, 0 },   // first entry for run 0
```

then `RUN_COUNT[0]` 27 → 33, `RUN_START` for runs 1–3 each +6, `NUM_PIXELS`
69 → 75, and the two array sizes. Re-check the current budget: 75 px × 41.7 mA
= 3.1 A at full white, still under the 3.7 A trace rating but now above the
2.5 A software cap, so the limiter will be doing real work on white frames.

## Why `y` barely matters (for now)

Only `M_EMBER` samples `y`, to stop the noise field looking identical on the
left and right sides. Everything else is a function of `x` and `t`. It's there
because the moment you want an effect that rises off the ground or pours down
the forks, the data already exists and you won't have to re-measure the bike.
