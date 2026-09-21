// ─────────────────────────────────────────────────────────────────────────────
//  MotoGlow — controller enclosure
//
//  Render one part at a time:
//      openscad -D 'part="tub"'    -o tub.stl    motoglow_case.scad
//      openscad -D 'part="lid"'    -o lid.stl    motoglow_case.scad
//      openscad -D 'part="saddle"' -o saddle.stl motoglow_case.scad
//  or just run ./build.sh, which renders all of them.
//
//  Sealing strategy, in one paragraph: the tub rim carries a groove holding
//  2 mm silicone O-ring cord. The lid presses that cord flat. The six lid
//  screws are OUTBOARD of that groove, in a flange, so water that gets into a
//  screw hole is still outside the seal. Nothing penetrates the floor. Cables
//  enter only through panel connectors and one gland, each with its own gasket.
//  That gets you a solid IP65-66 in practice; treat true IP68 from an FDM part
//  as marketing, and do not pressure-wash it directly.
// ─────────────────────────────────────────────────────────────────────────────
include <params.scad>

part = "tub";   // "tub" | "lid" | "saddle" | "preview"

// ─── Helpers ────────────────────────────────────────────────────────────────

// Rounded rectangular prism, centred in XY, sitting on z = 0.
module rrect(x, y, r, h) {
  linear_extrude(height = h)
    offset(r = r) square([x - 2*r, y - 2*r], center = true);
}

// Lid screw positions: four corners plus evenly spaced intermediates.
function _span(n, half) = n < 2 ? [0] :
  [ for (i = [0 : n-1]) -half + 2*half*i/(n-1) ];

function screw_pts() =
  let (cx = shell_x/2 + flange_w/2,
       cy = shell_y/2 + flange_w/2)
  concat(
    [ for (x = _span(n_screws_long, cx - corner_r*0.25), y = [-cy, cy]) [x, y] ],
    n_screws_short > 2
      ? [ for (y = _span(n_screws_short, cy - corner_r*0.25), x = [-cx, cx])
            if (abs(y) < cy - 0.01) [x, y] ]
      : []
  );

module screw_positions() { for (p = screw_pts()) translate([p[0], p[1], 0]) children(); }

// ─── Ports ───────────────────────────────────────────────────────────────────
// The port list comes from pcb_data.scad in BOARD coordinates, so it cannot
// drift from what the board actually needs. Board coordinates have their
// origin at the board's bottom-left corner; the case is centred on the origin,
// so a board point maps to the case by subtracting half the board size.
function b2c_x(bx) = bx - pcb_x/2;
function b2c_y(by) = by - pcb_y/2;

// Inside face of each wall, in case coordinates.
function wall_in(face) =
    face == "W" ? -inner_x/2 : face == "E" ? inner_x/2 :
    face == "N" ? -inner_y/2 : inner_y/2;

module port_cuts() {
  z = floor_t + port_z;
  for (p = ports) {
    face = p[0]; at = p[1]; d = p[2] * shrink;
    // Start outside the shell and cut right through the wall, with margin at
    // both ends so the hole is never left blind by a rounding error.
    if (face == "W")
      translate([-shell_x/2 - 1, b2c_y(at), z]) rotate([0, 90, 0])
        cylinder(d = d, h = wall + 3);
    if (face == "E")
      translate([ shell_x/2 + 1, b2c_y(at), z]) rotate([0, -90, 0])
        cylinder(d = d, h = wall + 3);
    if (face == "N")
      translate([b2c_x(at), -shell_y/2 - 1, z]) rotate([-90, 0, 0])
        cylinder(d = d, h = wall + 3);
    if (face == "S")
      translate([b2c_x(at),  shell_y/2 + 1, z]) rotate([90, 0, 0])
        cylinder(d = d, h = wall + 3);
  }
}

// ─── Screw ears ──────────────────────────────────────────────────────────────
// One boss per lid screw, hulled back to a point inside the shell so it fuses
// into the wall. Discrete rather than a continuous flange: a flange running all
// the way round would sit directly over the connector holes and cap them off.
module screw_ears() {
  d = ear_d;
  for (p = screw_pts()) {
    // Companion point, clamped inside the shell footprint, gives the hull
    // something solid to merge with regardless of which side the ear is on.
    qx = max(min(p[0], shell_x/2 - d/2 - 1), -(shell_x/2 - d/2 - 1));
    qy = max(min(p[1], shell_y/2 - d/2 - 1), -(shell_y/2 - d/2 - 1));
    hull() {
      translate([p[0], p[1], tub_h - ear_h]) cylinder(d = d, h = ear_h);
      translate([qx,   qy,   tub_h - ear_h]) cylinder(d = d, h = ear_h);
    }
  }
}

// ─── Tub ─────────────────────────────────────────────────────────────────────
module pcb_posts() {
  for (h = pcb_holes)
    translate([b2c_x(h[0]), b2c_y(h[1]), floor_t])
      cylinder(d = post_d, h = pcb_standoff);
}

module pcb_post_holes() {
  // M2.5 brass heat-set inserts, pressed in from above.
  for (h = pcb_holes)
    translate([b2c_x(h[0]), b2c_y(h[1]), floor_t + pcb_standoff - 5.0])
      cylinder(d = 3.4 * shrink, h = 5.2);
}

module wings() {
  for (sy = [-1, 1])
    hull() {
      translate([-shell_x/2 + corner_r, sy * (shell_y/2 - 1), 0])
        cylinder(r = corner_r, h = wing_t);
      translate([ shell_x/2 - corner_r, sy * (shell_y/2 - 1), 0])
        cylinder(r = corner_r, h = wing_t);
      translate([-shell_x/2 + corner_r + 8, sy * (shell_y/2 + wing_w - corner_r), 0])
        cylinder(r = corner_r, h = wing_t);
      translate([ shell_x/2 - corner_r - 8, sy * (shell_y/2 + wing_w - corner_r), 0])
        cylinder(r = corner_r, h = wing_t);
    }
}

module wing_slots() {
  // Two zip-tie slots per side. The tie passes up through the slot, over
  // whatever you are strapping to, and back down through its partner.
  for (sy = [-1, 1], sx = [-1, 1])
    translate([sx * 24, sy * (shell_y/2 + wing_w/2 + 1), -1])
      cube([tie_slot_w * shrink, tie_slot_h * shrink, wing_t + 2], center = true);
}

module tub() {
  union() {
    difference() {
      union() {
        rrect(shell_x, shell_y, corner_r, tub_h);
        screw_ears();
        wings();
      }

      // Interior cavity.
      translate([0, 0, floor_t])
        rrect(inner_x, inner_y, max(corner_r - wall, 1), inner_h + 1);

      // Gasket groove, sunk into the rim. 1.3 mm of rim inboard of it and
      // 1.5 mm outboard, so neither lip is thin enough to split.
      translate([0, 0, tub_h - groove_d])
        difference() {
          rrect(inner_x + 2*(1.3 + groove_w), inner_y + 2*(1.3 + groove_w),
                corner_r - wall + 1.3 + groove_w, groove_d + 1);
          translate([0, 0, -0.5])
            rrect(inner_x + 2*1.3, inner_y + 2*1.3,
                  corner_r - wall + 1.3, groove_d + 2);
        }

      // Heat-set inserts for the lid screws.
      screw_positions()
        translate([0, 0, tub_h - insert_h - 0.4])
          cylinder(d = insert_d * shrink, h = insert_h + 1);

      port_cuts();
      wing_slots();
    }

    // Board posts go on AFTER the cavity is cut — they live inside it.
    difference() { pcb_posts(); pcb_post_holes(); }
  }
}

// ─── Lid ─────────────────────────────────────────────────────────────────────
// The lid outline is derived from the screw positions rather than picked by
// hand. Its corner radius equals the ear radius plus 1 mm, and the corner arcs
// are centred exactly on the corner screws — so a screw hole can never break
// out through the edge no matter how the box is resized.
function _maxabs(v, i) = max([for (p = v) abs(p[i])]);
lid_corner_r = ear_d/2 + 1.0;
lid_x = 2 * (_maxabs(screw_pts(), 0) + lid_corner_r);
lid_y = 2 * (_maxabs(screw_pts(), 1) + lid_corner_r);

module lid() {
  difference() {
    union() {
      rrect(lid_x, lid_y, lid_corner_r, lid_t);
      // Locating lip that drops into the cavity. It does no sealing — it stops
      // the lid sliding while you tighten the screws and squash the cord.
      translate([0, 0, -1.5])
        rrect(inner_x - 2*fit, inner_y - 2*fit, max(corner_r - wall - fit, 1), 1.5);
    }
    // Screw clearance, countersunk so nothing proud catches a knee or a bag.
    screw_positions() {
      translate([0, 0, -1]) cylinder(d = lid_screw * shrink + 0.4, h = lid_t + 4);
      translate([0, 0, lid_t - 1.6])
        cylinder(d1 = lid_screw * shrink + 0.4, d2 = lid_screw * 2.0, h = 1.7);
    }
    if (emboss_text)
      translate([0, 0, lid_t - 0.6])
        linear_extrude(height = 1.0)
          text(label, size = 9, halign = "center", valign = "center",
               font = "Liberation Sans:style=Bold");
  }
}

// ─── Optional frame-tube saddle ──────────────────────────────────────────────
// Printed separately and strapped to the tube; the box then sits on its flat
// top. Keeping this off the box means the sealed floor is never drilled or
// curved, which is the whole reason it is a separate part.
//
// Strapping: a zip tie goes up through one of the box's wing slots, down the
// channel moulded into that side of the saddle, under the tube, up the far
// channel and through the opposite wing slot. Two ties, front and back.
module saddle() {
  h = tube_dia/2 + 8;          // groove depth plus 8 mm of solid above it
  w = tube_dia + 20;

  module wrap_channel(xpos, depth) {
    difference() {
      translate([xpos, 0, h/2]) cube([tie_slot_w * shrink, w + 6, h * 3], center = true);
      translate([xpos, 0, h/2]) cube([tie_slot_w * shrink + 4, w - 2*depth, h * 3 + 2], center = true);
    }
  }

  difference() {
    rrect(shell_x, w, 5, h);
    // Tube groove in the underside. Centred on z = 0 so it is a clean half round.
    rotate([0, 90, 0]) cylinder(d = tube_dia + 2*fit, h = shell_x + 2, center = true);
    // Tie channels, aligned with the box's wing slots.
    for (sx = [-1, 1]) wrap_channel(sx * 24, 2.0);
  }
}

// ─── Part selection ──────────────────────────────────────────────────────────
if      (part == "tub")    tub();
else if (part == "lid")    lid();
else if (part == "saddle") saddle();
else if (part == "preview") {
  tub();
  translate([0, 0, tub_h + 18]) lid();
  translate([0, lid_y + 22, 0]) saddle();
}
