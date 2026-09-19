// ─────────────────────────────────────────────────────────────────────────────
//  MotoGlow enclosure — parameters
//
//  Everything dimensional lives here. Change a number, re-run build.sh, get new
//  STLs. That is the whole reason this is OpenSCAD and not a mesh someone drew
//  once: the PCB will change size at least twice before you are done.
// ─────────────────────────────────────────────────────────────────────────────

/* [Printer fit] */
// Extra clearance on every mating surface. 0.20 suits a well-tuned X1C in ASA.
// Raise to 0.30 if the lid is tight, lower to 0.15 if it rattles.
fit           = 0.20;
// ASA shrinks as it cools. 1.004 adds 0.4% so holes land on size.
shrink        = 1.004;

/* [PCB] */
pcb_x         = 75.0;
pcb_y         = 55.0;
pcb_t         = 1.6;
pcb_standoff  = 4.0;    // clearance under the board for clipped through-hole leads
pcb_hole_inset= 3.5;    // mounting-hole centres, in from each corner
pcb_screw     = 2.5;    // M2.5 board screws

/* [Shell] */
wall          = 2.8;
floor_t       = 2.8;
lid_t         = 3.0;
inner_margin  = 2.0;    // air gap between PCB edge and wall
// Interior height is driven by the panel connectors, not by the components:
// an SP13 body must sit entirely above the PCB, and its nut (~20 mm across)
// must clear the board edge. That sets the minimum. See port_z below.
inner_h       = 31.0;   // floor to rim, inside
corner_r      = 4.0;

/* [Seal] */
// 2 mm silicone O-ring cord stock, joined into a loop with cyanoacrylate.
// The groove compresses it to 1.5 mm — about 25%, which is the right range for
// a printed sealing face. Thinner cord does not tolerate layer lines.
cord_d        = 2.0;
groove_w      = cord_d * 1.2;
groove_d      = cord_d * 0.75;
rim_w         = 5.2;    // rim thickness carrying the groove

/* [Lid fixing] */
// Screws sit OUTBOARD of the gasket, so a screw hole that takes on water
// cannot feed it into the box. This is why the flange exists at all.
// Screw ears are discrete, not a continuous flange: a flange all the way round
// would sit directly over the port holes and cap them off.
flange_w      = 6.5;         // how far a screw ear stands off the shell wall
ear_h         = 8.0;         // enough depth to swallow the heat-set insert
ear_d         = 10.0;        // ear boss diameter; 3 mm of ASA around an M3 insert
lid_screw     = 3.0;         // M3
insert_d      = 4.0;         // M3 brass heat-set insert, outer diameter
insert_h      = 5.7;
boss_d        = 7.0;
n_screws_long = 3;           // per long side (corners + one mid-span)
n_screws_short= 2;           // per short side (the corners, shared)

/* [Ports] */
// SP13 4-pin panel connectors: 13 mm threaded barrel, ~20 mm nut across flats.
// port_z is the hole centre above the inside floor. It is set 11 mm above the
// top of the PCB so the nut, which reaches ~10 mm out from the hole centre,
// passes clear over the board edge instead of fouling it.
sp13_hole     = 13.2;
sp13_nut_r    = 10.0;        // clearance radius needed inside for the nut
port_z        = pcb_standoff + pcb_t + 11.0;
// M12 cable gland for the permanently-wired battery feed.
gland_hole    = 12.2;

/* [Mounting] */
// The floor is never cut for mounting — a hole through a sealed floor is a leak
// waiting to happen. The box always has flat zip-tie wings, and if you want it
// on a frame tube you print the separate saddle part and zip-tie the box to
// that. Set tube_dia to the tube you are clamping to.
tube_dia      = 28.0;
wing_w        = 16.0;
wing_t        = 4.0;
tie_slot_w    = 5.0;         // fits a standard 4.8 mm zip tie
tie_slot_h    = 2.6;

/* [Cosmetic] */
emboss_text   = true;
label         = "MOTOGLOW";

// ─── Derived ────────────────────────────────────────────────────────────────
inner_x  = pcb_x + 2*inner_margin;
inner_y  = pcb_y + 2*inner_margin;
shell_x  = inner_x + 2*rim_w;
shell_y  = inner_y + 2*rim_w;
outer_x  = shell_x + 2*flange_w;
outer_y  = shell_y + 2*flange_w;
tub_h    = floor_t + inner_h;

$fn = 64;
