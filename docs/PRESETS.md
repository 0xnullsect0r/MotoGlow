# Presets

Sixteen, all animated, all flowing front to rear. The direction isn't a
per-preset setting — the two phase helpers in `phase.h` are the only way any
effect can express position, and they only run one way. That invariant has a
host test (`tools/test_phase.cpp`) that checks the feature actually traverses
the bike, at every speed, including after 99,999 seconds of runtime when float
precision starts to matter.

## The library

| # | Name | Motion | Looks like |
|--:|------|--------|------------|
| 1 | **Ignition** | block | KTM orange block with a white-hot core, sweeping over near-black. The default, and the one the boot sequence resolves into. |
| 2 | **Orange Crush** | gradient | Orange through amber and back, drifting. No hard edges — a slow wash of colour moving rearward. |
| 3 | **Ready to Race** | comet | Fast white-headed comet with an orange-into-deep-red tail. The aggressive one. |
| 4 | **Rainbow Flow** | rainbow | Continuous hue cycle drifting rearward. Constant motion, never stops, never repeats visibly. |
| 5 | **Ice** | gradient | White → cyan → deep blue, slow. Cold and expensive-looking. |
| 6 | **Deep Blue** | block | Electric blue block with a white leading edge, over a very dark blue background. |
| 7 | **Chrome** | block | Clean white block on black, with a faint blue-grey trailing edge. The subtle one. |
| 8 | **Menace** | comet | Blood-red comet on a dark red glow. |
| 9 | **Synthwave** | barber | Magenta and cyan stripes, staggered left to right so they read as a helix around the bike. |
| 10 | **Toxic** | sparkle | Acid green sparks born at the front axle, carried rearward over a dim green wash. |
| 11 | **Gold Rush** | sparkle | Warm gold with champagne highlights, on a brighter base than Toxic. |
| 12 | **Violet Drift** | gradient | Purple → pink → violet, very slow. |
| 13 | **Firefly** | sparkle | Sparse warm-white sparks on near-black. Slow, quiet. |
| 14 | **Ember** | noise | A heat field drifting rearward — deep red through orange to pale yellow. The only one with no repeating pattern. |
| 15 | **Arctic Pulse** | pulse | Brightness waves running rearward over icy blue. |
| 16 | **Midnight** | pulse | Deep indigo, very slow, very dim. For when you want it on but not shouting. |

## The eight motions underneath

Each is a pure function of a pixel's position and the clock, in
`firmware/motoglow/animations.cpp`:

- **block** — a solid band of the palette sweeping rearward over a background.
  The outer 20% of the band is a soft shoulder, because a hard edge visibly
  strobes as it steps between 50 mm COB cells.
- **comet** — a bright head with an exponential tail stretching *forward*, which
  is where a tail belongs on something moving rearward. The tail is combined
  with the background by per-channel maximum, so it never dips below it.
- **gradient** — the palette laid along the bike and drifting. No features, just
  continuous colour movement.
- **rainbow** — hue as a function of position and time.
- **sparkle** — sparks live in continuous bike-space, are born just ahead of the
  front axle and drift rearward, rendered as narrow gaussians. Because they live
  in space rather than in the LED array, they cross the gaps between segments
  smoothly instead of popping.
- **barber** — hard-edged stripes, softened by 6% so they don't alias, offset by
  side so the left and right are staggered.
- **pulse** — a static palette along the bike with a brightness wave travelling
  rearward over it.
- **ember** — a Perlin noise field sampled at `(x − t·speed)`, so it drifts
  rearward by construction.

## Power-on

Two fast white sweeps front to rear, overlapping slightly, then a bloom: the
active preset rises everywhere at once, overshoots about 15%, and settles. The
white cast drains out as the colour comes up. About 1.5 seconds, then the main
loop takes over and it starts moving.

The preset it resolves into is whichever was active when you last switched off.

## Controls

The toggle is power — it's not wired to the microcontroller at all, so "off"
means the whole box is unpowered and the bike draws nothing.

Everything else is the one momentary button:

| | |
|---|---|
| press | next preset (400 ms crossfade, not a snap) |
| double press | previous preset |
| triple press | jump to Ignition |
| hold 0.8 s | next brightness — 18 / 40 / 70 / 100%, flashes once to confirm |
| hold 3 s | next speed — 0.55× / 1.0× / 1.7×, flashes 1/2/3 times |

Preset, brightness and speed all survive a power cycle. Writes to flash are
deferred 5 seconds, so clicking through ten presets costs one erase, not ten.

## Changing a preset

Presets are a table at the bottom of `presets.cpp`:

```c
{ "Ignition", M_BLOCK, &PAL_IGNITION, { 0.38f, 0.22f, 0.0f, 18 } },
//  name      motion    palette         speed  width param  background
```

`speed` is in bike-lengths per second: 0.38 means a feature takes about 2.6
seconds to travel from the front axle to the rear. `width` is in the same units
(0.22 ≈ 330 mm of bike). `param` is motion-specific — comet tail length,
stripe count, sparks per second, noise scale. `background` is how bright the
"black" between features sits, 0–255.

Palettes are `DEFINE_GRADIENT_PALETTE` blocks above the table. How the palette
is read depends on the motion it's paired with, and that mapping is documented
in a comment at the top of the palette section — worth reading before you write
a new one, because e.g. a comet reads index 0 as its head colour and 255 as the
far tail, which is not obvious.
