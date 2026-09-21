# Build guide

Rough order and rough times. The soldering is an evening; the printing is
overnight; fitting it to the bike is an afternoon done properly.

## 1. Print the parts (overnight)

```
cd cad && ./build.sh
```

Five STLs land in `cad/stl/`:

| File | Qty | Notes |
|---|---:|---|
| `motoglow_case_tub.stl` | 1 | Print as oriented, open side up. No supports. |
| `motoglow_case_lid.stl` | 1 | Flat side down. |
| `motoglow_tube_saddle.stl` | 0–1 | Only if mounting to a frame tube. Set `tube_dia` in `params.scad` first. |
| `motoglow_strip_clips_x8.stl` | 2–3 | Eight per plate. Print as many as you need. |
| `motoglow_strip_endcaps_x4.stl` | 1 | One per cut strip end. Count your cuts. |

The box is 115 × 110 × 43 mm, so the tub is a ~6 hour print.

**ASA on the X1C:** dry at 80 °C for 8 h, nozzle 250 °C, bed 100 °C, chamber
closed, top glass on, fan off, brim on the tub and lid. Preheat the bed for
10–15 minutes with the door shut before starting — that pre-warms the chamber
and is most of the difference between a good part and a warped one.

Then heat-set the inserts: six M3 in the lid ears, four M2.5 in the board posts.
Go in slowly and square; ASA is more forgiving than PLA but will still mushroom
if you rush.

## 2. Assemble the board (2 hours)

Order matters — shortest parts first, so the board sits flat on the bench:

1. Resistors (standing), zener D1, Schottky D3, TVS D2
2. DIP-14 socket (note the notch), ceramic caps
3. Electrolytics C1 and C3 — **check polarity**. The stock KiCad electrolytic
   footprint has no polarity mark of its own, so the board prints a `+` beside
   pad 1 for each of them. Same for `G D S` at Q1, `IN G 5V` at U1 and `K`/`A`
   at the status LED: every orientation-sensitive part is labelled.
4. Q1 (TO-220, lying flat), U1 (R-78E, 3 pins)
5. LED1 — pad 1 is the **cathode**, pad 2 the anode; both are marked
6. Terminal blocks, all facing outward
7. Pico last, on header strips **soldered at both ends**

Don't socket the Pico. A socket will back out on a bike; two soldered header
strips will not. If you want it removable, accept that you'll be desoldering.

Connector pinouts are printed on the back of the board.

**Before fitting the 74AHCT125 in its socket**, power the board from a bench
supply at 12 V and confirm:

- 5.0 V ±0.15 V at the Pico's VSYS pad
- ~1.1 V on Q1's gate with the toggle closed, and ≈ supply with it open
- Nothing hot

Then fit U2 and the Pico.

## 3. Flash it (15 minutes)

Arduino IDE or `arduino-cli`, with the
[arduino-pico](https://github.com/earlephilhower/arduino-pico) core and FastLED
installed.

```
arduino-cli core install rp2040:rp2040
arduino-cli lib install FastLED
arduino-cli compile --fqbn rp2040:rp2040:rpipico2w firmware/motoglow
arduino-cli upload  --fqbn rp2040:rp2040:rpipico2w -p /dev/ttyACM0 firmware/motoglow
```

First flash: hold BOOTSEL while plugging in USB, and the Pico appears as a mass
storage device — copy the `.uf2` across.

Run the colour-order test before anything else. Set `COLOR_ORDER_TEST 1` in
`config.h`, flash, connect one strip run, and confirm its first three pixels are
red, green, blue. Batches of 12 V COB vary; if the colours are wrong, change
`LED_COLOR_ORDER` (`GRB`, `RGB`, `BRG`) until they're right. Then set the test
back to 0.

## 4. Cut and prepare the strips (2 hours, take your time)

Measure on the bike before cutting anything. The stock lengths are in
[BIKE_MAP.md](BIKE_MAP.md) — 200 mm fork, 450 mm tank, 400 mm seat line,
300 mm swingarm, 500 mm engine, 250 mm tail.

**Cut only on the marked cut lines**, every 50 mm on the default strip. Cutting
between them destroys the segment.

For each cut end:

1. Trim the silicone sleeve back ~8 mm to expose the pads.
2. Solder wires on, respecting the direction arrow — **data must flow rearward**.
3. Push a printed end cap filled with neutral-cure silicone over the joint.
4. Slide adhesive-lined heatshrink over the whole thing and shrink it until
   adhesive squeezes out both ends.

That last step is the one people skip and the reason home-built strips die over
one winter. A cut strip is an open hole into the electronics; the silicone
jacket protects everything except exactly where you cut it.

## 5. Fit to the bike (an afternoon)

1. **Dry-fit everything first.** Lay the strips where they'll go, with the box
   where it'll live, and check every cable reaches with slack to spare.
2. Clean every mounting surface with isopropyl alcohol. Let it flash off.
3. Strip clips where you can get a zip tie around something; 3M tape plus a clip
   where you can't. Tape alone will let go — heat cycling and vibration beat it.
4. **Service loops** where a run crosses the steering head and where it crosses
   onto the swingarm. Turn the bars lock to lock and compress the suspension by
   hand before you commit to a cable length.
5. Route strip cables away from exhaust headers and away from anything that
   moves against them.
6. Mount the box: zip ties through the wings, under the seat or on the
   subframe. Print the saddle if you're clamping to a tube.
7. Handlebar switches on the left bar, loom down the fork with the existing
   cables, again with a steering-lock service loop.
8. Battery lead last, with the fuse holder within 100 mm of the positive post.

## 6. Seal it

1. Glue the 2 mm O-ring cord into a loop — butt the ends, one drop of superglue
   — and press it into the lid groove.
2. Six M3 screws, tightened in a cross pattern, snug not gorilla-tight. You're
   compressing the cord about 25%; over-tightening bows the lid and makes the
   seal *worse* in the middle.
3. Nip up the SP13 nuts and the cable gland.
4. A smear of dielectric grease in each SP13 before mating.

Realistic result: IP65–66. Rain, road spray and a hose are fine. Do not put a
pressure washer lance on it — no FDM part is IP68, whatever the internet says.

## 7. Before the first ride

- Toggle off → measure current at the battery lead. Should read **zero**, not
  a few milliamps. If it doesn't, Q1 isn't fully off and something is wrong.
- Toggle on → boot sweep runs front to rear across the whole bike, then the
  preset starts moving.
- Click through all sixteen presets.
- Hold for brightness, hold longer for speed.
- Leave it running for 20 minutes and check nothing in the box is warm.

## Maintenance

Once a season: pull the lid, look for water staining or corrosion, check the
O-ring hasn't taken a set, re-tighten the strip clips. If you ever find water
inside, the usual culprit is a strip cut end, not the box.
