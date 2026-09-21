# Parts list

Prices are what these went for at the time of writing, from the usual mix of
Amazon, AliExpress and DigiKey. Treat them as a sanity check, not a quote.

You said you already have cable and a box of odds and ends, so the list is split
into what you almost certainly need to buy and what you may already own.

---

## 1. Must buy

### Controller board — about $32

| Qty | Part | Notes | ~$ |
|----:|------|-------|---:|
| 1 | **PCB**, 2-layer 80 × 60 mm | Upload `hardware/motoglow-pcb/motoglow-gerbers.zip`. 1.6 mm, 1 oz, any colour. You get 5 boards; shipping dominates. | 12 |
| 1 | **Raspberry Pi Pico 2 W** | The W is deliberate — it costs ~$2 more and leaves the door open for Bluetooth control later with no board change. | 7 |
| 1 | RECOM **R-78E5.0-1.0** | 12 V→5 V switching regulator in a 3-pin package. Do not substitute a 7805: it would work, but this is 96% efficient and survives a far wider input range. | 5 |
| 1 | **IRF4905** P-channel MOSFET, TO-220 | Master switch. Any P-FET with Vds ≥ 55 V, Id ≥ 20 A, Rds(on) ≤ 0.05 Ω and logic-friendly threshold works. | 1.50 |
| 1 | **74AHCT125N**, DIP-14 | Level shifter. Must be **AHCT**, not HC or AHC — the HCT input threshold is what makes 3.3 V look like a valid logic high. | 0.60 |
| 1 | DIP-14 socket | | 0.20 |
| 1 | **1.5KE18A** TVS diode, DO-201AD | Transient clamp and reverse-polarity crowbar. | 0.50 |
| 1 | BZX55C15 15 V zener, DO-35 | Gate clamp for Q1. | 0.10 |
| 1 | 1N5819 Schottky, DO-41 | Stops the Pico back-feeding the 5 V rail over USB. | 0.10 |
| 1 | 470 µF 35 V electrolytic, 10 mm | **35 V, not 25 V** — a 16 V part will not survive a load dump. | 0.40 |
| 1 | 10 µF 16 V electrolytic, 5 mm | | 0.10 |
| 6 | 100 nF ceramic, 5 mm pitch | One of them, C8, is Q1's soft-start. | 0.60 |
| 11 | ¼ W resistors: 100 k, 47 k, 10 k ×2, 1 k, 470 R, 330 R ×4 | Mounted standing up. | 0.50 |
| 1 | 3 mm LED, any colour | Status indicator, only visible with the lid off. | 0.10 |
| 5 | 3.5 mm 4-way screw terminal (KF128 / Phoenix PT-1,5-4-3.5-H) | J2–J6 | 2.50 |
| 1 | 5.08 mm 2-way screw terminal | J1, battery feed | 0.40 |
| 2 | 1×20 2.54 mm pin header strips | For the Pico. **Solder both ends** — don't socket it. | 0.50 |

### LED strip — about $48

| Qty | Part | Notes | ~$ |
|----:|------|-------|---:|
| 5 m | **12 V addressable COB strip, WS2811 RGB, 720 LEDs/m, 20 ICs/m, IP67** | e.g. BTF-LIGHTING FCOB RGB-IC. The IP67 version is silicone-sleeved. ~3.5 m gets used; the rest is spare and offcuts. | 48 |

COB is why this will look better than a kit. A 5050 strip gives you a row of
dots; COB gives a continuous line of light, so a colour block sweeping down the
bike reads as a moving *band* rather than a moving row of LEDs. One "pixel" is a
50 mm continuously glowing block — that's the cut interval, and it's what the
firmware's pixel counts assume.

**Budget alternative (−$20):** 12 V WS2815, 60 LEDs/m, IP67. Dotted rather than
continuous, but it has a backup data line, so one dead LED doesn't kill the rest
of the run. If you take this route, change `PIXELS_PER_METER` to 60,
`STRIP_WATTS_PER_M` to 18 and `LED_CHIPSET` to `WS2815` in `config.h`, and
recount the pixels per segment in `bike_map.cpp`. The board already brings a
second ground to every connector; a WS2815 backup data line goes there instead.

### Sealing and connectors — about $47

| Qty | Part | Notes | ~$ |
|----:|------|-------|---:|
| 5 | **SP13 4-pin panel-mount connector pairs**, IP67/68 | 13 mm panel hole. One per strip run plus one for the handlebar loom. | 22 |
| 1 | M12 cable gland | Battery feed. Permanent, so a gland rather than a connector. | 2 |
| 1 m | **2 mm silicone O-ring cord stock** | Cut to length, glue the ends with superglue to form a loop, drop into the lid groove. | 6 |
| — | **Adhesive-lined** heatshrink, 3–12 mm | The adhesive lining is the point; plain heatshrink is not a seal. | 8 |
| 6 | M3 brass heat-set inserts + M3 × 8 screws | Lid | 6 |
| 4 | M2.5 heat-set inserts + M2.5 × 6 screws | Board standoffs | 3 |

### Handlebar controls — about $24

| Qty | Part | Notes | ~$ |
|----:|------|-------|---:|
| 1 | **Latching** toggle switch, 22 mm bar clamp, IP67 | Master on/off. It only carries ~110 µA, so buy for feel and weather sealing, not current rating. | 12 |
| 1 | **Momentary** push button, 22 mm bar clamp, IP67 | Preset / brightness / speed | 12 |

If you want the nice version, motogadget's `m.switch` is the same idea in
billet aluminium for around $70 each. Nothing in the design cares.

### Power wiring — about $11

| Qty | Part | Notes | ~$ |
|----:|------|-------|---:|
| 1 | Inline ATO fuse holder + **5 A** fuses | Mounts at the battery, not at the box. | 5 |
| 3 m | 4-core 22 AWG shielded cable | Handlebar loom | 6 |

### Printed parts

~110 g of **ASA** (the box is 115 × 110 × 43 mm). Not PETG and definitely not PLA: this box sits in the sun on a
bike. ASA holds about 100 °C and is UV-stable; PLA will sag in a closed car park
in August. Your X1C is enclosed and its stock nozzle is hardened, so you already
have everything you need — dry the filament at 80 °C for 8 hours first, run the
bed at 100 °C with the door shut and the fan off, and use a brim.

---

## 2. You probably already have

16 AWG wire for the battery feed, ring terminals, zip ties, solder, neutral-cure
silicone sealant, isopropyl alcohol, 3 M primer.

---

## Totals

| | |
|---|---:|
| Everything above | **~$165** |
| If you already have heatshrink, inserts, screws, fuse holder and handlebar cable | **~$140** |
| Cable glands instead of SP13 connectors (permanent, not serviceable) | **−$18** |
| WS2815 dotted strip instead of COB | **−$20** |

The floor, if you own the consumables and take both substitutions, is around
**$100**. I'd spend the money on the COB strip — it's the single part that
decides whether this looks like a kit or like it came with the bike.

---

## Deliberately not on this list

**Anything connected to brakes or turn signals.** You said no, and it keeps the
loom to four strip runs and one switch cable.

**A DC-DC for the strips.** They run directly off 12 V, which is the whole
reason for choosing a 12 V strip over a 5 V one on a vehicle.

**A relay.** An earlier version of this design had one. The P-channel MOSFET
does the same job with no coil current, no contacts to pit, nothing to chatter
over a pothole, and about 20 mm less height in the box.
