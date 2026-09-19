// ─────────────────────────────────────────────────────────────────────────────
//  MotoGlow — strip mounting hardware
//
//  The 3M tape on the back of an LED strip is fine on a desk and useless on a
//  motorcycle: heat cycling, vibration and pressure washing all beat it. These
//  clips carry the load mechanically; the tape only has to hold the strip
//  against the clip while you fit it.
//
//      openscad -D 'part="clip"'    -o clip.stl    strip_parts.scad
//      openscad -D 'part="endcap"'  -o endcap.stl  strip_parts.scad
//      openscad -D 'part="clip_x8"' -o clip_x8.stl strip_parts.scad
// ─────────────────────────────────────────────────────────────────────────────
include <params.scad>

part = "clip";

// The default strip is 12 mm wide FCOB in an IP67 silicone sleeve, which
// measures about 12.6 x 3.6 mm once the sleeve is allowed for. Measure yours.
strip_w   = 12.6;
strip_h   = 3.6;
clip_wall = 2.0;
clip_len  = 12.0;        // along the strip
lip       = 1.2;         // how far the lips fold over the strip (also their height)

// ─── Clip ────────────────────────────────────────────────────────────────────
// A C-channel the strip presses into, on a base with two zip-tie wings.
// The lip undersides are 45 degrees, which does two things at once: pressing
// the strip down wedges the lips apart so it snaps in, and the overhang prints
// cleanly with no support.
clip_base   = 2.4;       // base plate thickness under the strip
clip_wing   = 6.5;       // how far the tie wings stick out past each wall

module _clip_profile() {
  ow = strip_w + 2*clip_wall + 2*fit;
  ch = strip_h + 2*fit;                     // channel height
  cw = strip_w + 2*fit;                     // channel width
  mw = cw - 2*lip;                          // mouth width, narrower than the strip
  difference() {
    // Body: walls plus base, with the wings either side.
    union() {
      translate([-ow/2, 0]) square([ow, clip_base + ch + lip]);
      translate([-ow/2 - clip_wing, 0]) square([ow + 2*clip_wing, clip_base]);
    }
    // Channel, with the 45 degree lip undersides built into the cut.
    polygon([
      [-cw/2, clip_base],
      [ cw/2, clip_base],
      [ cw/2, clip_base + ch],
      [ mw/2, clip_base + ch + lip],        // 45 deg because lip height == lip inset
      [ mw/2, clip_base + ch + lip + 4],
      [-mw/2, clip_base + ch + lip + 4],
      [-mw/2, clip_base + ch + lip],
      [-cw/2, clip_base + ch],
    ]);
  }
}

module strip_clip() {
  ow = strip_w + 2*clip_wall + 2*fit;
  difference() {
    rotate([90, 0, 0])
      linear_extrude(height = clip_len, center = true)
        _clip_profile();
    // Tie slot in each wing: the tie passes up through one, around the tube or
    // frame member, and down through the other.
    for (sx = [-1, 1])
      translate([sx * (ow/2 + clip_wing/2), 0, clip_base/2])
        cube([tie_slot_w * shrink, tie_slot_h * shrink, clip_base + 2], center = true);
  }
}

// ─── Cut-end cap ─────────────────────────────────────────────────────────────
// Every cut you make in the strip is a hole straight into the electronics. Fill
// this cup with neutral-cure silicone, push it onto the cut end, then slide
// adhesive-lined heatshrink over the whole joint. That end is then better
// sealed than the factory one.
module strip_endcap() {
  ow = strip_w + 2*1.6 + 2*fit;
  oh = strip_h + 2*1.6 + 2*fit;
  d  = 9.0;    // how far it swallows the strip
  difference() {
    translate([-ow/2, -oh/2, 0]) cube([ow, oh, d + 1.6]);
    translate([0, 0, -0.01])
      cube([strip_w + 2*fit, strip_h + 2*fit, 2*d], center = true);
    // Bleed hole so trapped silicone can escape rather than push the cap off
    translate([0, 0, d + 1.6 - 0.8]) cylinder(d = 2.0, h = 3, center = true);
  }
}

if      (part == "clip")    strip_clip();
else if (part == "endcap")  strip_endcap();
else if (part == "clip_x8") for (i = [0:7]) translate([0, i * (clip_len + 4), 0]) strip_clip();
else if (part == "endcap_x4") for (i = [0:3]) translate([i * 22, 0, 0]) strip_endcap();
