# Wiring

## The power path, end to end

```
  BATTERY +  ──[ 5A ATO FUSE ]──┐   (fuse AT THE BATTERY, not at the box)
                                │
                          ┌─────┴──────────────────────────────────────┐
                          │  J1.1                          CONTROLLER  │
                          │    │                                       │
                          │    ├──────────────┬──────────────┐         │
                          │    │              │              │         │
                          │  Q1 source    D2 cathode      R1 100k      │
                          │    │           (1.5KE18A)        │         │
                          │  Q1 ┤gate ─────────┬─────────────┘         │
                          │    │               │                       │
                          │    │            D1 anode (15V zener,       │
                          │    │               │      cathode to +)    │
                          │    │            R2 10k                     │
                          │    │               │                       │
                          │    │             J6.1 ──► handlebar TOGGLE │
                          │    │                        │              │
                          │  Q1 drain  = +12VSW       J6.2 ──► GND     │
                          │    │                                       │
                          │    ├── C1 470µF/35V ── GND                 │
                          │    │   (C8 100nF gate-source = soft start) │
                          │    ├── U1 R-78E5.0 ──► +5V ──► 74AHCT125  │
                          │    │                   └─ D3 ─► Pico VSYS  │
                          │    ├── R9/R10 divider ──► Pico GP26 (Vbat) │
                          │    │                                       │
                          │    └── J2.1 J3.1 J4.1 J5.1  (strip +12V)   │
                          │                                            │
                          │  J1.2 = GND ── ground pour ── J2.2/.4 …    │
                          └────────────────────────────────────────────┘
  BATTERY −  ─────────────────────► J1.2
```

**Why the toggle isn't in the power path.** Q1 is a P-channel MOSFET with its
source on the battery and its drain feeding everything else. R1 holds its gate
at the source voltage, which keeps it off. Closing the handlebar toggle pulls
the gate down through R2 — about 110 µA — and Q1 turns on. So the handlebar
carries a signal, not 3 amps: thin wire, no volt drop, and any switch you like
the feel of will outlive the bike. With the toggle open, Q1 is fully off and the
board draws *nothing*, which is what makes a battery-direct install safe to
leave for a month.

**Why there's a diode into VSYS.** D3 lets the 5 V rail feed the Pico but not
the other way round. Without it, plugging in USB with the bike's supply off
back-feeds 4.7 V into the rail, through U1's output and weakly onto the strip
supply. Harmless but untidy, and it costs one 10c diode to not happen.

**Why C8 is there.** Q1's gate would otherwise switch in about 36 µs, slamming
470 µF of bulk capacitance and four strip runs onto the battery in one step.
C8 across gate and source stretches that to roughly a millisecond.

**Why there's no reverse-polarity MOSFET.** D2 is a unidirectional TVS across
the input. Wire the battery backwards and it conducts, shorting the input and
blowing the 5 A fuse before anything downstream sees more than a diode drop.
This is the standard automotive trick and it costs one component — but it means
**the fuse is a functional part of the circuit, not a formality.** Run it
unfused and D2 becomes the fuse, exactly once.

## Where to tap power on a 2023 KTM 890 Adventure

The battery is under the seat. KTM also provides two accessory leads behind a
cap in the fairing: **ACC1** is permanently live, **ACC2** is switched by the
ignition, and both are fused at 10 A.

You asked for battery-direct, so:

1. Ring-terminal the positive lead straight to the battery **+** post, with the
   5 A fuse holder within 100 mm of that post. A fuse protects the *wire*, so it
   belongs at the source; a fuse at the far end protects nothing.
2. Ring-terminal the negative lead to the battery **−** post or a frame ground.
3. Run 16 AWG. It's oversized for 2.5 A and that's fine — voltage drop over the
   run matters more than ampacity here.

ACC1 would also work and saves a trip to the battery terminals, but it's a
10 A circuit shared with whatever else you hang off it, and you'd still want
your own 5 A fuse.

## Connector pinouts

Also printed on the **back of the PCB**, so you can read it with the loom in
your hands.

**J1 — battery, 5.08 mm terminal, enters through the M12 gland**

| Pin | | Wire |
|---|---|---|
| 1 | +12 V, fused | red, 16 AWG |
| 2 | GND | black, 16 AWG |

All four strip connectors are on one long face of the box, above the terminal
block edge, so the pigtails inside stay short. The handlebar connector is on
one end, the battery gland on the other.

**J2–J5 — strip runs, 3.5 mm terminals, each to one SP13 panel connector**

| Pin | | SP13 pin |
|---|---|---|
| 1 | +12 V | 1 |
| 2 | GND | 2 |
| 3 | DATA | 3 |
| 4 | GND (second return) | 4 |

Two grounds is not padding. Each run's return carries up to ~1 A and the second
conductor halves the drop; if you later move to WS2815, its backup data line
goes on pin 4 instead.

| Connector | Run | Goes to |
|---|---|---|
| J2 | RUN0 | Left chain: fork L → tank L → seat line L → swingarm L |
| J3 | RUN1 | Right chain: fork R → tank R → seat line R → swingarm R |
| J4 | RUN2 | Engine underglow (centre, low) |
| J5 | RUN3 | Tail |

**J6 — handlebar loom, 3.5 mm terminal, to one SP13 panel connector**

| Pin | | |
|---|---|---|
| 1 | SWITCH | one side of the latching toggle |
| 2 | GND | other side of the toggle |
| 3 | BUTTON | one side of the momentary button |
| 4 | GND | other side of the button |

Neither handlebar wire is polarity-sensitive; both switches are simple closures
to ground. Use shielded 4-core and land the shield on J6.2.

## Wiring the strips

Each run is one continuous electrical chain cut into segments, wired front to
rear. Data flows in the same direction: **the arrow printed on the strip must
point rearward** on every segment.

Between segments, run three wires (+12 V, GND, DATA) plus a second ground if you
have the conductor spare. Keep the jumper between the fork and the frame long
enough to take full steering lock *and* full suspension travel, and do the same
where a run crosses onto the swingarm. Cable-tie a service loop; don't let a
wire become the thing that limits steering.

**Every cut end needs sealing.** A cut strip is an open hole into the
electronics — this is where water actually gets in, not through the silicone
jacket. Print the end caps from `cad/strip_parts.scad`, fill one with
neutral-cure silicone, push it onto the cut end, then slide adhesive-lined
heatshrink over the whole joint. Do this on solder joints too.

## Grounding

The board's bottom layer is a solid ground pour, so every ground on the board is
already one low-impedance node. Bring the strip grounds back to the board rather
than picking up a chassis ground near each strip: a frame ground that shares a
path with the ignition system is how you get glitching data lines.

## First power-up

Do this on a bench supply, or with the bike's fuse pulled and a 12 V supply
clipped to J1, before anything is bolted to the bike:

1. Board only, no strips, no Pico. Check +5 V at the Pico's VSYS pad.
2. Fit the Pico, flash with `COLOR_ORDER_TEST 1` in `config.h`. Connect one
   strip run. Confirm its first three pixels read red, green, blue — if not,
   change `LED_COLOR_ORDER` until they do.
3. Set `COLOR_ORDER_TEST 0`, reflash, and check the boot sweep runs front to
   rear across each run in turn.
4. Only then seal the lid.
