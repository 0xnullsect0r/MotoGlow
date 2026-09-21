// ─────────────────────────────────────────────────────────────────────────────
//  MotoGlow enclosure — parameters
//
//  The board's size, its mounting holes, the panel-port positions and the
//  interior height are NOT set here. They come from pcb_data.scad, which is
//  generated from the real board by hardware/motoglow-pcb/export_pcb_data.py.
//
//  That indirection exists because the first revision of this case kept its
//  own hand-typed copy of those numbers. The board grew from 75 x 55 to
//  80 x 60 mm and the case did not, so it was built for a board that no longer
//  existed, and every connector's body landed inside a component. Both halves
//  passed their own checks. Nothing compared them. Now verify_fit.py does.
// ─────────────────────────────────────────────────────────────────────────────
include <pcb_data.scad>

/* [Printer fit] */
// Extra clearance on every mating surface. 0.20 suits a well-tuned X1C in ASA.
// Raise to 0.30 if the lid is tight, lower to 0.15 if it rattles.
fit           = 0.20;
// ASA shrinks as it cools. 1.004 adds 0.4% so holes land on size.
shrink        = 1.004;

/* [Shell] */
// One wall thickness, used for the shell, for the port cut depth and for the
// rim that carries the gasket groove. An earlier version had two different
// numbers for this and cut the connector holes 0.4 mm short of going through.
wall          = 5.2;
lid_t         = 3.0;
corner_r      = 4.0;

/* [Board fixing] */
pcb_screw     = 2.5;         // M2.5 into heat-set inserts in the floor posts
post_d        = 6.0;

/* [Seal] */
// 2 mm silicone O-ring cord stock, joined into a loop with cyanoacrylate.
// The groove compresses it to 1.5 mm — about 25%, which is the right range for
// a printed sealing face. Thinner cord does not tolerate layer lines.
cord_d        = 2.0;
groove_w      = cord_d * 1.2;
groove_d      = cord_d * 0.75;

/* [Lid fixing] */
// Screws sit OUTBOARD of the gasket, so a screw hole that takes on water
// cannot feed it into the box. This is why the ears exist at all.
flange_w      = 6.5;         // how far a screw ear stands off the shell wall
ear_h         = 8.0;         // enough depth to swallow the heat-set insert
ear_d         = 10.0;        // ear boss diameter; 3 mm of ASA around an M3
lid_screw     = 3.0;
insert_d      = 4.0;         // M3 brass heat-set insert, outer diameter
insert_h      = 5.7;
boss_d        = 7.0;
n_screws_long = 3;           // per long side (corners + one mid-span)
n_screws_short= 2;           // per short side (the corners, shared)

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
inner_x  = pcb_x + 2*case_margin;
inner_y  = pcb_y + 2*case_margin;
inner_h  = case_inner_h;
floor_t  = case_floor_t;
shell_x  = inner_x + 2*wall;
shell_y  = inner_y + 2*wall;
tub_h    = floor_t + inner_h;

$fn = 64;
