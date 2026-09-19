# MotoGlow

Addressable accent lighting for a 2023 KTM 890 Adventure. Sixteen animated
presets, all flowing front to rear, on a Raspberry Pi Pico 2 W driving four runs
of 12 V addressable COB strip, in a printed enclosure you can hose off.

Everything here is built and checked, not sketched: the firmware compiles clean
for the RP2350, the CAD renders to manifold STLs, and the PCB passes
connectivity, clearance, edge and ground-pour checks.

```
firmware/motoglow/   Arduino / FastLED firmware for the Pico 2 W
cad/                 Parametric OpenSCAD enclosure, saddle, strip clips, end caps
hardware/motoglow-pcb/  KiCad board, generated + routed + verified by script
docs/                Parts list, wiring, build guide, bike map, presets
tools/               Host test for the direction invariant
```

Start with [docs/PARTS.md](docs/PARTS.md), then
[docs/BUILD.md](docs/BUILD.md).

---

## The one idea worth reading about

Almost every DIY strip controller animates against the LED index — pixel 0,
then 1, then 2. That works on a bench and falls apart on a motorcycle, because
the LEDs are not in a line. A run goes up a fork leg, jumps a metre of air to
the tank, runs level along the seat, then drops onto a swingarm. An index sweep
crawls up the fork, teleports across the gap, then races down the seat. It reads
as four separate strips blinking in sequence.

MotoGlow gives every pixel a physical position on the bike and renders effects
as a function of **position and time**:

```c
x      0.0 = front axle    1.0 = rear axle     (1509 mm on this bike)
y      0.0 = ground        1.0 = 1350 mm up
side  -1 left    0 centre    +1 right
```

A block moving at 0.38 bike-lengths per second moves at that speed across the
*bike*. It takes the right amount of time to cross the fork, is absent for
exactly as long as the gap is wide, and reappears on the tank where it should.
Your eye joins it up, and the whole bike reads as one object rather than as
several strips.

The consequences are practical. You can rewire a run backwards, shorten a
segment, or add one, and only a table in `bike_map.cpp` changes. Rainbows,
comets, gradients and wipes are three lines of maths each. And "always flows
front to rear" is structural rather than a convention: the two phase helpers in
`phase.h` are the only way any effect can express position, and they only run
one way. There is a host test that proves it, including after 99,999 seconds of
runtime, where float precision starts to bite.

---

## What's in the box

**Firmware.** 16 presets over 8 motion primitives, 400 ms crossfades, a
two-sweep-then-bloom power-on sequence, and per-frame current estimation derived
from the strip's datasheet figures rather than guessed. Settings survive power
cycles, with flash writes deferred 5 seconds so clicking through ten presets
costs one erase. Battery protection is staged — the strips visibly back off and
breathe before the pack gets low enough to strand you — because this is a
battery-direct install with no ignition interlock.

**Electronics.** A P-channel MOSFET master switch means the handlebar toggle
carries about 110 µA instead of 3 A, and that the box draws exactly nothing when
it's off. A 74AHCT125 buffers all four data lines to 5 V, which is the single
most common reason home-built strip controllers glitch: the strips want 3.5 V on
data and a Pico puts out 3.3 V — fine on a bench, unreliable on three feet of
wire next to an ignition system. Reverse polarity is cleared by a TVS blowing
the fuse, so **the fuse is a functional part of the circuit, not a formality.**

**Enclosure.** Parametric, because the PCB size will change at least twice
before you're done. The gasket groove sits inboard of the lid screws, so a screw
hole that takes on water is still outside the seal, and nothing penetrates the
floor — the frame-tube saddle is a separate part for exactly that reason.

---

## Honest limitations

- The bike-space coordinates are my reading of an 890 Adventure's proportions,
  not measurements of your bike. They'll look fine as shipped and better after
  ten minutes with a tape measure — see [docs/BIKE_MAP.md](docs/BIKE_MAP.md).
- Nothing here has been built in the physical world. Every check that can be run
  in software has been; none of it has been run on a bike.
- IP65–66 realistically, not IP68. Rain, spray and a hose are fine. A pressure
  washer lance is not, whatever anyone claims about FDM parts.
- There's no brake or turn-signal integration, by choice. Strip runs and the
  loom are simpler for it.
- This is show lighting. Underglow that's on while moving is restricted or
  banned in a good number of US states, and red or blue visible from the front
  is a criminal matter rather than a ticket in some of them. The toggle is the
  compliance mechanism.

---

## Verification

| | |
|---|---|
| Firmware | Compiles clean for `rp2040:rp2040:rpipico2w` at `--warnings all`; 8% flash, 14% RAM |
| Direction invariant | 18 host assertions pass (`g++ -o /tmp/t tools/test_phase.cpp && /tmp/t`) |
| Enclosure | All 5 STLs render 2-manifold; dimensions checked against the parameters |
| PCB | 0 unconnected nets, 0 clearance violations below 0.25 mm, 0 items within 0.3 mm of the outline, ground pour is a single region reaching all 35 ground pads |
| Fab output | 124 plated drill hits + 4 NPTH at 2.7 mm, matching the design exactly |
