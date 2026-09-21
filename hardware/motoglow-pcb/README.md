# MotoGlow controller PCB

Two layers, 80 × 60 mm, every part through-hole so it can be hand-assembled.
All signal routing is on the top layer; the bottom is an uninterrupted ground
pour. The board uses zero vias, which is a happy accident of that split and
means nothing to go wrong in plating.

## Ordering it

Upload `motoglow-gerbers.zip` to any fab. Defaults are fine: 2 layers, 1.6 mm,
1 oz copper, HASL or ENIG, any colour. Nothing on the board is near a process
limit — the tightest trace is 0.3 mm, the tightest clearance 0.25 mm, and the
smallest drill 0.8 mm.

No assembly service is needed or wanted: the whole point of an all-through-hole
board is that you solder it yourself in an evening.

## Regenerating

```
python3 gen_pico_fp.py      # writes lib.pretty/RPi_Pico_2W_Horizontal.kicad_mod
python3 route.py            # export DSN -> freerouting -> import SES -> pour
python3 verify_board.py     # connectivity, clearance, edge, pour, silkscreen
python3 verify_fit.py       # does the enclosure fit this board?
python3 export_pcb_data.py  # hand the board's real dimensions to the CAD
```

`mech.py` holds every number that couples the board to the enclosure, and both
sides read it. `../../cad/build.sh` runs the exporter and the fit check before
it renders anything, so a board change that breaks the case stops the build
rather than the print.

`route.py` needs `freerouting.jar` (set `FREEROUTING_JAR`) and runs it under
`xvfb-run`, because freerouting insists on a display even in batch mode.

`motoglow.ses` is committed deliberately. Freerouting does not guarantee a
identical result between runs, so keeping the session file means the board in
`motoglow.kicad_pcb` can be reproduced exactly rather than approximately.

## Why the checks are hand-written

KiCad 7's command line has no `pcb drc` subcommand — that arrived in KiCad 8 —
so `verify_board.py` does the job geometrically. It checks four things:

- **Connectivity.** Every pad of every routed net lands in one connected group
  of copper. This is what catches a coordinate sign or scale error in the SES
  import, which otherwise produces a board that looks entirely plausible and is
  wired to nothing.
- **Clearance.** No two pieces of copper on different nets come closer than
  0.25 mm. Pads are modelled by their true shape; a rectangular pad treated as
  a circle through its corners over-states it by 0.35 mm on a 1.7 mm pad and
  invents violations that are not there.
- **Board edge.** Nothing within 0.3 mm of the outline.
- **Ground pour.** The pour is a single region, and every ground pad reaches it
  through at least two thermal spokes. A pad sitting inside its relief with no
  spoke bridging to the pour looks perfect on screen and is not connected.

`verify_fit.py` is the fifth check, and the one this project learned the hard
way. Revision A shipped a case built for a 75 x 55 mm board that had since
become 80 x 60, with all six connector bodies landing inside components. Both
halves passed their own checks perfectly; nothing compared them. It also has a
negative test: forcing revision A's geometry back in makes it report all 19
collisions.

Current state: **0 unconnected nets, 0 clearance violations, 0 edge violations,
0 silkscreen over pads, pour is 1 region with all 35 ground pads connected,
0 connector/component collisions.**

## Two things worth knowing before you power it

**The fuse is not optional.** Reverse polarity protection here is D2, a
unidirectional TVS across the input. Connect the battery backwards and D2
conducts, which is only a protection strategy if there is a fuse for it to
blow. Without one, D2 becomes the fuse, once.

**Tall parts live in the middle of the board.** Anything standing within 14 mm
of an edge shares that space with a panel connector's barrel, so `mech.py` caps
it at 11 mm — the height of the screw terminals, which genuinely have to be on
the edge. That is why Q1, C1 and D2 are in the middle rather than tucked
tidily against a wall. `verify_fit.py` enforces it.

**Q1 is the master switch and the handlebar toggle barely touches it.** Q1 is a
P-channel MOSFET with its source on the battery; the toggle pulls its gate down
through R2 and draws about 110 µA doing it. So the switch wiring is signal wire,
not power wire, and with the toggle open the board's draw is zero rather than
small — which matters on a battery-direct install that may sit for a month.
