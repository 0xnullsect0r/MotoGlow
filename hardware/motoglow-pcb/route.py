#!/usr/bin/env python3
"""Route the MotoGlow board with freerouting, then import the result.

KiCad 7's CLI cannot export Specctra DSN, so this writes the DSN directly from
the pcbnew board object and reads the SES session file back in. Two details
worth knowing if you touch this:

  * Specctra's Y axis points up and KiCad's points down, so every coordinate is
    negated on the way out and again on the way in.
  * Rather than emit one library image per footprint TYPE with local pad
    coordinates and a placement rotation, this emits one image per component
    INSTANCE with absolute pad coordinates, placed at the origin with zero
    rotation. It is more verbose but removes every rotation and mirroring
    ambiguity between the two coordinate conventions.

Usage:  python3 route.py            (export, route, import, save)
        python3 route.py --passes 40
"""
import pcbnew, os, sys, subprocess, re, math

HERE = os.path.dirname(os.path.abspath(__file__))
FREEROUTING = os.environ.get("FREEROUTING_JAR", "/tmp/freerouting.jar")

# Net classes. The three nets that carry strip current get fat tracks. GND is
# one of them: every run's return lands on this board, so GND sees the whole
# load, not a fraction of it. At 1.5 mm on 1 oz copper that is about 3.7 A by
# IPC-2221 for a 20 C rise, against a hard ceiling of 2.9 A if every one of the
# 69 pixels were driven to full white at once.
#
# A ground pour would normally do this job, but KiCad 7's standalone Python
# zone filler segfaults, and shipping gerbers with an unfilled zone would mean
# shipping a board with no ground. Fat routed GND is unambiguous.
POWER_NETS = {"BAT+", "+12VSW"}

# GND is a plane net: it is deliberately left out of the netlist handed to the
# autorouter and carried by a bottom-layer pour instead. Every return from every
# strip run lands on this board, so GND sees the whole load; a pour has orders
# of magnitude more copper than any track the router would have drawn, and the
# router had no chance of connecting 35 scattered pads at power width anyway.
# Its pads are still present in the library images, so they remain obstacles.
PLANE_NET = "GND"
W_SIGNAL, W_POWER, CLEARANCE = 300, 1500, 250      # micrometres
VIA_DIA, VIA_DRILL = 800, 400


def um(v):  # KiCad internal units (nm) -> integer micrometres
    return int(round(v / 1000.0))


def write_dsn(board, path):
    fps = [f for f in board.GetFootprints()]
    lines = []
    A = lines.append
    A('(pcb motoglow')
    A('  (parser (string_quote ")(space_in_quoted_tokens on)'
      '(host_cad "kicad")(host_version "7.0"))')
    A('  (resolution um 1)')
    A('  (unit um)')
    A('  (structure')
    A('    (layer F.Cu (type signal)(property (index 0)))')
    A('    (layer B.Cu (type signal)(property (index 1)))')

    # Board boundary, taken from the Edge.Cuts segments.
    pts = []
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            pts.append((um(d.GetStart().x), -um(d.GetStart().y)))
            pts.append((um(d.GetEnd().x),   -um(d.GetEnd().y)))
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    A(f'    (boundary (path pcb 0 {x0} {y0} {x1} {y0} {x1} {y1} {x0} {y1} {x0} {y0}))')

    # Non-plated holes become keepouts so nothing is routed through a screw.
    for f in fps:
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                d = um(max(p.GetSize().x, p.GetSize().y)) + 500
                cx, cy = um(p.GetPosition().x), -um(p.GetPosition().y)
                for lay in ("F.Cu", "B.Cu"):
                    A(f'    (keepout "" (circle {lay} {d} {cx} {cy}))')

    A(f'    (via "Via[0-1]_{VIA_DIA}:{VIA_DRILL}_um")')
    A(f'    (rule (width {W_SIGNAL})(clearance {CLEARANCE})'
      f'(clearance {CLEARANCE} (type wire_area))'
      f'(clearance {max(CLEARANCE-50,100)} (type smd_to_turn_gap)))')
    A('  )')

    # Every component instance is placed at the origin; its image carries the
    # already-transformed absolute pad positions.
    A('  (placement')
    for f in fps:
        if all(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for p in f.Pads()):
            continue
        A(f'    (component "IMG_{f.GetReference()}" (place "{f.GetReference()}" 0 0 front 0))')
    A('  )')

    A('  (library')
    stacks = {}
    for f in fps:
        pads = [p for p in f.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
        if not pads:
            continue
        A(f'    (image "IMG_{f.GetReference()}"')
        for p in pads:
            # Every pad is handed to the router as a circle. For a rectangular
            # pad that circle must be the CIRCUMSCRIBED one, not max(w,h):
            # otherwise the pad's corners stick out past what the router was
            # avoiding, and tracks end up legally routed and physically shorted.
            w, h = p.GetSize().x, p.GetSize().y
            if p.GetShape() in (pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_ROUNDRECT):
                d = um(int(math.hypot(w, h)))
            else:
                d = um(max(w, h))
            sid = f"Round_{d}_um"
            stacks[sid] = d
            A(f'      (pin "{sid}" "{p.GetNumber()}" '
              f'{um(p.GetPosition().x)} {-um(p.GetPosition().y)})')
        A('    )')
    for sid, d in sorted(stacks.items()):
        A(f'    (padstack "{sid}" (shape (circle F.Cu {d}))'
          f'(shape (circle B.Cu {d}))(attach off))')
    A(f'    (padstack "Via[0-1]_{VIA_DIA}:{VIA_DRILL}_um"'
      f'(shape (circle F.Cu {VIA_DIA}))(shape (circle B.Cu {VIA_DIA}))(attach off))')
    A('  )')

    A('  (network')
    netnames = []
    for f in fps:
        for p in f.Pads():
            n = p.GetNetname()
            if n and n not in netnames:
                netnames.append(n)
    routed = [n for n in netnames if n != PLANE_NET]
    for n in routed:
        pins = [f'"{f.GetReference()}"-"{p.GetNumber()}"'
                for f in fps for p in f.Pads() if p.GetNetname() == n]
        A(f'    (net "{n}" (pins {" ".join(pins)}))')
    sig = [n for n in routed if n not in POWER_NETS]
    pwr = [n for n in routed if n in POWER_NETS]
    A('    (class kicad_default ' + ' '.join(f'"{n}"' for n in sig))
    A(f'      (circuit (use_via "Via[0-1]_{VIA_DIA}:{VIA_DRILL}_um"))')
    A(f'      (rule (width {W_SIGNAL})(clearance {CLEARANCE})))')
    if pwr:
        A('    (class power ' + ' '.join(f'"{n}"' for n in pwr))
        A(f'      (circuit (use_via "Via[0-1]_{VIA_DIA}:{VIA_DRILL}_um"))')
        A(f'      (rule (width {W_POWER})(clearance {CLEARANCE})))')
    A('  )')
    A('  (wiring)')
    A(')')
    open(path, 'w').write('\n'.join(lines) + '\n')
    return len(routed)


# ─── Specctra session parsing ───────────────────────────────────────────────
def sexp(text):
    tok = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', text)
    def parse(i):
        out = []
        while i < len(tok):
            t = tok[i]
            if t == '(':
                sub, i = parse(i + 1); out.append(sub)
            elif t == ')':
                return out, i + 1
            else:
                out.append(t.strip('"')); i += 1
        return out, i
    return parse(0)[0]


def find_all(node, tag):
    if isinstance(node, list):
        if node and node[0] == tag:
            yield node
        for c in node:
            yield from find_all(c, tag)


def import_ses(board, path):
    tree = sexp(open(path).read())
    layers = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu}
    tracks = vias = 0
    for net_node in find_all(tree, 'net'):
        if len(net_node) < 2 or not isinstance(net_node[1], str):
            continue
        name = net_node[1]
        netinfo = board.FindNet(name)
        if netinfo is None:
            continue
        for wire in find_all(net_node, 'wire'):
            for p in find_all(wire, 'path'):
                lay = layers.get(p[1])
                if lay is None:
                    continue
                w = int(float(p[2]))
                coords = [float(v) for v in p[3:]]
                pts = [(coords[i], -coords[i + 1]) for i in range(0, len(coords) - 1, 2)]
                for a, b in zip(pts, pts[1:]):
                    if a == b:
                        continue
                    t = pcbnew.PCB_TRACK(board)
                    t.SetStart(pcbnew.VECTOR2I(int(a[0] * 1000), int(a[1] * 1000)))
                    t.SetEnd(pcbnew.VECTOR2I(int(b[0] * 1000), int(b[1] * 1000)))
                    t.SetWidth(int(w * 1000)); t.SetLayer(lay); t.SetNet(netinfo)
                    board.Add(t); tracks += 1
        for v in find_all(net_node, 'via'):
            x, y = float(v[2]), -float(v[3])
            pv = pcbnew.PCB_VIA(board)
            pv.SetPosition(pcbnew.VECTOR2I(int(x * 1000), int(y * 1000)))
            pv.SetWidth(int(VIA_DIA * 1000 / 1000 * 1000))
            pv.SetDrill(int(VIA_DRILL * 1000 / 1000 * 1000))
            pv.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            pv.SetNet(netinfo)
            board.Add(pv); vias += 1
    return tracks, vias


GND_CLEARANCE_MM = 0.30
THERMAL_GAP_MM   = 0.40
SPOKE_W_MM       = 0.70
EDGE_INSET_MM    = 0.50


def _capsule_poly(ax, ay, bx, by, r, n=16):
    """Polygon for a track: a rectangle capped by two half circles.

    PCB_TRACK.TransformShapeToPolygon needs an ERROR_LOC enum value that this
    KiCad build does not expose to Python, so the capsule is built directly.
    """
    ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
    dx, dy = bx-ax, by-ay
    L = math.hypot(dx, dy)
    ux, uy = (dx/L, dy/L) if L > 1e-9 else (1.0, 0.0)
    nx, ny = -uy, ux
    for i in range(n+1):                      # cap around b
        t = -math.pi/2 + math.pi*i/n
        c, sn = math.cos(t), math.sin(t)
        ps.Append(pcbnew.FromMM(bx + r*(nx*c + ux*sn)),
                  pcbnew.FromMM(by + r*(ny*c + uy*sn)))
    for i in range(n+1):                      # cap around a
        t = math.pi/2 + math.pi*i/n
        c, sn = math.cos(t), math.sin(t)
        ps.Append(pcbnew.FromMM(ax + r*(nx*c + ux*sn)),
                  pcbnew.FromMM(ay + r*(ny*c + uy*sn)))
    return ps


def _poly_rect(x0, y0, x1, y1):
    ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
    for x, y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)):
        ps.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    return ps


def build_gnd_pour(board):
    """Bottom-layer ground pour, built by polygon subtraction.

    KiCad 7's standalone Python ZONE_FILLER segfaults, so the fill is computed
    here instead: start with the board inset from its edge, subtract every
    foreign piece of copper grown by the clearance, and subtract a thermal
    relief ring around each ground pad. The rings are cut with four spokes left
    intact, so the pour reaches the pad through the spokes -- without them a
    through-hole pad backed by a solid plane sinks so much heat that it is
    genuinely hard to solder by hand.
    """
    net = board.FindNet(PLANE_NET)
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu); zone.SetNet(net)
    zone.SetLocalClearance(pcbnew.FromMM(GND_CLEARANCE_MM))
    zone.SetMinThickness(pcbnew.FromMM(0.25))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetThermalReliefGap(pcbnew.FromMM(THERMAL_GAP_MM))
    zone.SetThermalReliefSpokeWidth(pcbnew.FromMM(SPOKE_W_MM))
    zone.SetZoneName("GND pour")

    xs, ys = [], []
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            xs += [d.GetStart().x, d.GetEnd().x]; ys += [d.GetStart().y, d.GetEnd().y]
    x0, y0 = pcbnew.ToMM(min(xs)), pcbnew.ToMM(min(ys))
    x1, y1 = pcbnew.ToMM(max(xs)), pcbnew.ToMM(max(ys))

    o = zone.Outline(); o.NewOutline()
    for x, y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1)):
        o.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))

    fill = _poly_rect(x0+EDGE_INSET_MM, y0+EDGE_INSET_MM,
                      x1-EDGE_INSET_MM, y1-EDGE_INSET_MM)
    FAST = pcbnew.SHAPE_POLY_SET.PM_FAST
    clr = pcbnew.FromMM(GND_CLEARANCE_MM)

    gnd_pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                hole = pcbnew.SHAPE_POLY_SET()
                pad.TransformHoleToPolygon(hole, pcbnew.FromMM(0.5), pcbnew.FromMM(0.005))
                fill.BooleanSubtract(hole, FAST)
                continue
            if pad.GetNetname() == PLANE_NET:
                gnd_pads.append(pad); continue
            shp = pcbnew.SHAPE_POLY_SET()
            pad.TransformShapeToPolygon(shp, pcbnew.B_Cu, clr, pcbnew.FromMM(0.005))
            fill.BooleanSubtract(shp, FAST)

    for t in board.GetTracks():
        if t.GetNetname() == PLANE_NET:
            continue
        if not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() != pcbnew.B_Cu:
            continue
        ax, ay = pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)
        bx, by = pcbnew.ToMM(t.GetEnd().x),   pcbnew.ToMM(t.GetEnd().y)
        r = pcbnew.ToMM(t.GetWidth())/2 + GND_CLEARANCE_MM
        fill.BooleanSubtract(_capsule_poly(ax, ay, bx, by, r), FAST)

    # Thermal reliefs: a ring per ground pad, with four spokes left in place.
    for pad in gnd_pads:
        ring = pcbnew.SHAPE_POLY_SET()
        pad.TransformShapeToPolygon(ring, pcbnew.B_Cu, pcbnew.FromMM(THERMAL_GAP_MM),
                                    pcbnew.FromMM(0.005))
        px = pcbnew.ToMM(pad.GetPosition().x); py = pcbnew.ToMM(pad.GetPosition().y)
        reach = max(pcbnew.ToMM(pad.GetSize().x), pcbnew.ToMM(pad.GetSize().y))/2 \
                + THERMAL_GAP_MM + 0.4
        h = SPOKE_W_MM/2
        spokes = _poly_rect(px-reach, py-h, px+reach, py+h)
        spokes.BooleanAdd(_poly_rect(px-h, py-reach, px+h, py+reach), FAST)
        ring.BooleanSubtract(spokes, FAST)
        fill.BooleanSubtract(ring, FAST)

    # Drop slivers and orphan islands too small to be useful copper.
    fill.Simplify(FAST)
    for i in range(fill.OutlineCount()-1, -1, -1):
        area = abs(pcbnew.ToMM(pcbnew.ToMM(fill.Outline(i).Area())))
        if area < 2.0:
            fill.DeletePolygon(i)
    keep = fill

    zone.SetFilledPolysList(pcbnew.B_Cu, keep)
    zone.SetIsFilled(True)
    zone.SetNeedRefill(False)
    board.Add(zone)
    return zone, keep


if __name__ == "__main__":
    passes = 30
    if "--passes" in sys.argv:
        passes = int(sys.argv[sys.argv.index("--passes") + 1])

    sys.path.insert(0, HERE)
    import gen_board
    board = gen_board.build()

    dsn = os.path.join(HERE, "motoglow.dsn")
    ses = os.path.join(HERE, "motoglow.ses")
    n = write_dsn(board, dsn)
    print(f"wrote {dsn}: {n} nets")

    if "--export-only" in sys.argv:
        sys.exit(0)

    cmd = ["xvfb-run", "-a", "java", "-jar", FREEROUTING,
           "-de", dsn, "-do", ses, "-mp", str(passes), "-da"]
    print("routing:", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3000)
    tail = [l for l in (r.stdout + r.stderr).splitlines()
            if "Picked up" not in l and "multi-release" not in l]
    print("\n".join(tail[-12:]))
    if not os.path.exists(ses):
        sys.exit("freerouting produced no session file")

    t, v = import_ses(board, ses)
    print(f"imported {t} track segments, {v} vias")
    zone, poly = build_gnd_pour(board)
    print(f"ground pour: {poly.OutlineCount()} region(s), "
          f"{pcbnew.ToMM(pcbnew.ToMM(poly.Area())):.1f} mm2 of copper")
    out = os.path.join(HERE, "motoglow.kicad_pcb")
    board.Save(out)
    print("saved", out)
