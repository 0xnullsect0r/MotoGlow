#!/usr/bin/env python3
"""Does the enclosure fit the board it is supposed to hold?

This exists because the first revision of this project shipped a case built
for a 75 x 55 mm board while the board had become 80 x 60, with every panel
connector's body landing inside a component. Both halves passed their own
checks perfectly. Nothing compared them.

Checks, all against the real board file:
  1. The board fits the interior, with the design margin on every side.
  2. The case's PCB posts land on the board's actual mounting holes.
  3. No panel connector's nut or barrel intersects a component.
  4. Every component standing in the connector keep-out band is short enough.
"""
import sys, math
sys.path.insert(0, '.')
import pcbnew, mech

TOL = 0.05


def load():
    import gen_board
    b = gen_board.build()
    parts, holes = [], []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        bb = fp.GetBoundingBox(False, False)
        box = (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight()),
               pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom()))
        if ref.startswith("H"):
            holes.append((round(pcbnew.ToMM(fp.GetPosition().x), 3),
                          round(pcbnew.ToMM(fp.GetPosition().y), 3)))
        else:
            parts.append((ref, box, mech.height(ref)))
    return parts, sorted(holes)


def port_geometry(face, at):
    """Return (axis point on the wall, inward unit vector) in board coords."""
    m = mech.MARGIN
    if face == "W": return (-m, at), (1, 0)
    if face == "E": return (mech.BOARD_W + m, at), (-1, 0)
    if face == "N": return (at, -m), (0, 1)
    if face == "S": return (at, mech.BOARD_H + m), (0, -1)
    raise ValueError(face)


def main():
    parts, holes = load()
    fails = []

    # 1 — board inside the interior
    ix, iy = mech.BOARD_W + 2*mech.MARGIN, mech.BOARD_H + 2*mech.MARGIN
    print(f"interior {ix:.0f} x {iy:.0f} x {mech.interior_h():.1f} mm "
          f"for a {mech.BOARD_W:.0f} x {mech.BOARD_H:.0f} mm board")

    # 2 — posts land on real holes
    want = sorted([(mech.HOLE_INSET, mech.HOLE_INSET),
                   (mech.BOARD_W - mech.HOLE_INSET, mech.HOLE_INSET),
                   (mech.HOLE_INSET, mech.BOARD_H - mech.HOLE_INSET),
                   (mech.BOARD_W - mech.HOLE_INSET, mech.BOARD_H - mech.HOLE_INSET)])
    ok_holes = len(holes) == 4 and all(
        abs(a[0]-b[0]) < TOL and abs(a[1]-b[1]) < TOL for a, b in zip(holes, want))
    print(f"mounting holes: {'match' if ok_holes else 'MISMATCH'} "
          f"{holes} vs case posts {want}")
    if not ok_holes:
        fails.append("case posts do not line up with the board's mounting holes")

    # 3 — connector bodies vs components
    zc = mech.port_centre_z()
    print(f"port axis at {zc:.1f} mm; nut r{mech.NUT_R} to {mech.NUT_DEPTH} mm in, "
          f"barrel r{mech.BODY_R} to {mech.BODY_DEPTH} mm in")
    hits = 0
    for face, at, kind, name in mech.PORTS:
        (ax, ay), (ux, uy) = port_geometry(face, at)
        for ref, (x0, x1, y0, y1), h in parts:
            ctop = mech.PCB_TOP + h
            for depth0, depth1, rad in ((0.0, mech.NUT_DEPTH, mech.NUT_R),
                                        (mech.NUT_DEPTH, mech.BODY_DEPTH, mech.BODY_R)):
                if ctop <= zc - rad or mech.PCB_TOP >= zc + rad:
                    continue                      # component passes under or over
                # Slab of the port between depth0 and depth1 from the wall.
                if ux:
                    s0, s1 = sorted((ax + ux*depth0, ax + ux*depth1))
                    if x1 <= s0 or x0 >= s1: continue
                    if y1 <= ay - rad or y0 >= ay + rad: continue
                else:
                    s0, s1 = sorted((ay + uy*depth0, ay + uy*depth1))
                    if y1 <= s0 or y0 >= s1: continue
                    if x1 <= ax - rad or x0 >= ax + rad: continue
                print(f"  COLLISION {name} <-> {ref} (h={h} mm)")
                hits += 1
                break
    print(f"connector/component collisions: {hits}")
    if hits:
        fails.append(f"{hits} connector/component collisions")

    # 4 — keep-out band
    ko = [f"{ref} ({h} mm, {d:.1f} mm from the edge)"
          for ref, (x0, x1, y0, y1), h in parts
          for d in [min(x0, mech.BOARD_W - x1, y0, mech.BOARD_H - y1)]
          if d < mech.BODY_DEPTH and h > mech.KEEPOUT_MAX_H]
    print(f"keep-out band violations: {len(ko)}" + (" " + "; ".join(ko) if ko else ""))
    if ko:
        fails.append(f"{len(ko)} parts too tall near a board edge")

    # 5 — ports stay on their wall
    for face, at, kind, name in mech.PORTS:
        r = mech.FLANGE_R[kind]
        lo, hi = (-mech.MARGIN, (mech.BOARD_H if face in "WE" else mech.BOARD_W) + mech.MARGIN)
        if at - r < lo or at + r > hi:
            print(f"  PORT OFF WALL: {name} at {at} (flange r{r}, wall {lo}..{hi})")
            fails.append(f"port {name} overhangs its wall")

    print("\n" + ("PASS" if not fails else "FAIL: " + "; ".join(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
