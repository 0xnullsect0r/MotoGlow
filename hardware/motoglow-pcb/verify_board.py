#!/usr/bin/env python3
"""Geometric verification of the routed MotoGlow board.

KiCad 7's command line has no DRC subcommand, so this does the two checks that
actually matter after an autoroute-and-import cycle:

  CONNECTIVITY  every pad of a net must end up in one connected group of
                copper. This is the check that catches a coordinate sign or
                scale error in the SES import, which would otherwise produce a
                board that looks plausible and is wired to nothing.
  CLEARANCE     no two pieces of copper on different nets may come closer than
                the design rule, and nothing may run off the board edge.

Shapes are modelled as capsules (a segment with a radius) and rectangles, so
every pairwise distance is closed-form rather than polygon marching.
"""
import pcbnew, sys, math
from collections import defaultdict

CLEARANCE_MM = 0.25
EDGE_MM      = 0.30


def seg_seg(p, q, r, s):
    """Shortest distance between segments pq and rs."""
    def dot(a, b): return a[0]*b[0] + a[1]*b[1]
    u = (q[0]-p[0], q[1]-p[1]); v = (s[0]-r[0], s[1]-r[1]); w = (p[0]-r[0], p[1]-r[1])
    a, b, c, d, e = dot(u,u), dot(u,v), dot(v,v), dot(u,w), dot(v,w)
    D = a*c - b*b
    if D < 1e-12:
        sc, tc = 0.0, (d/b if abs(b) > 1e-12 else (e/c if c > 1e-12 else 0.0))
    else:
        sc = (b*e - c*d)/D; tc = (a*e - b*d)/D
    sc = max(0.0, min(1.0, sc)); tc = max(0.0, min(1.0, tc))
    # Re-clamp the partner after clamping, so endpoint cases are exact.
    if a > 1e-12: sc = max(0.0, min(1.0, (b*tc - d)/a))
    if c > 1e-12: tc = max(0.0, min(1.0, (b*sc + e)/c))
    dx = (p[0] + sc*u[0]) - (r[0] + tc*v[0])
    dy = (p[1] + sc*u[1]) - (r[1] + tc*v[1])
    return math.hypot(dx, dy)


def pt_in_poly(p, poly):
    inside = False
    n = len(poly)
    for k in range(n):
        x1, y1 = poly[k]; x2, y2 = poly[(k+1) % n]
        if (y1 > p[1]) != (y2 > p[1]):
            xin = x1 + (p[1]-y1) * (x2-x1) / (y2-y1)
            if p[0] < xin:
                inside = not inside
    return inside


class Item:
    """Copper, as a set of segments grown by a radius.

    A round or oval pad, a track and a via are all one segment with a radius.
    A rectangular pad is its four edges with zero radius -- modelling it as a
    circle through its corners, which is the tempting shortcut, over-states it
    by 0.35 mm on a 1.7 mm pad and manufactures clearance violations that are
    not there.
    """
    __slots__ = ("segs","r","poly","layers","net","tag")
    def __init__(self, segs, r, layers, net, tag, poly=None):
        self.segs, self.r, self.poly = segs, r, poly
        self.layers, self.net, self.tag = layers, net, tag

    @staticmethod
    def capsule(a, b, r, layers, net, tag):
        return Item([(a, b)], r, layers, net, tag)

    @staticmethod
    def rect(cx, cy, w, h, ang, layers, net, tag):
        ca, sa = math.cos(ang), math.sin(ang)
        corners = []
        for dx, dy in ((-w/2,-h/2), (w/2,-h/2), (w/2,h/2), (-w/2,h/2)):
            corners.append((cx + dx*ca - dy*sa, cy + dx*sa + dy*ca))
        segs = [(corners[k], corners[(k+1) % 4]) for k in range(4)]
        return Item(segs, 0.0, layers, net, tag, poly=corners)

    def bbox(self):
        xs = [p[0] for s in self.segs for p in s]
        ys = [p[1] for s in self.segs for p in s]
        return (min(xs)-self.r, min(ys)-self.r, max(xs)+self.r, max(ys)+self.r)


def gap(i, j):
    # Containment: a segment endpoint of one inside the other's outline.
    if i.poly and any(pt_in_poly(p, i.poly) for s in j.segs for p in s):
        return -1.0
    if j.poly and any(pt_in_poly(p, j.poly) for s in i.segs for p in s):
        return -1.0
    best = 1e9
    for (a, b) in i.segs:
        for (c, d) in j.segs:
            v = seg_seg(a, b, c, d)
            if v < best:
                best = v
    return best - i.r - j.r


def mm(v): return v / 1e6


def collect(board):
    items = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            pos = (mm(p.GetPosition().x), mm(p.GetPosition().y))
            w, h = mm(p.GetSize().x), mm(p.GetSize().y)
            ang = math.radians(p.GetOrientationDegrees())
            # Model every pad as a capsule along its long axis. For a circle the
            # segment has zero length; for a rectangle this under-covers the
            # corners slightly, so rectangles are grown to their circumcircle
            # instead, which is conservative.
            shape = p.GetShape()
            layers = {pcbnew.F_Cu, pcbnew.B_Cu} if p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD \
                     else {p.GetLayer()}
            tag = f"{fp.GetReference()}.{p.GetNumber()}"
            net = p.GetNetname()
            if shape in (pcbnew.PAD_SHAPE_RECT, pcbnew.PAD_SHAPE_ROUNDRECT):
                items.append(Item.rect(pos[0], pos[1], w, h, ang, layers, net, tag))
            elif shape == pcbnew.PAD_SHAPE_CIRCLE:
                items.append(Item.capsule(pos, pos, w/2, layers, net, tag))
            else:                                   # oval and anything else
                L = max(w, h) - min(w, h); r = min(w, h)/2
                dx, dy = (L/2*math.cos(ang), L/2*math.sin(ang)) if w >= h \
                         else (-L/2*math.sin(ang), L/2*math.cos(ang))
                items.append(Item.capsule((pos[0]-dx, pos[1]-dy), (pos[0]+dx, pos[1]+dy),
                                          r, layers, net, tag))
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            pos = (mm(t.GetPosition().x), mm(t.GetPosition().y))
            items.append(Item.capsule(pos, pos, mm(t.GetWidth())/2,
                                      {pcbnew.F_Cu, pcbnew.B_Cu}, t.GetNetname(), "via"))
        else:
            a = (mm(t.GetStart().x), mm(t.GetStart().y))
            b = (mm(t.GetEnd().x),   mm(t.GetEnd().y))
            items.append(Item.capsule(a, b, mm(t.GetWidth())/2, {t.GetLayer()},
                                      t.GetNetname(), "track"))
    return items


def main(path):
    board = pcbnew.LoadBoard(path)
    items = collect(board)
    print(f"{len(items)} copper items")

    # ── Connectivity ────────────────────────────────────────────────────────
    parent = list(range(len(items)))
    def find(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb

    boxes = [it.bbox() for it in items]
    touch_tol = 1e-6
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            if items[i].net != items[j].net or not items[i].net:
                continue
            if not (items[i].layers & items[j].layers):
                continue
            bi, bj = boxes[i], boxes[j]
            if bi[2] < bj[0] or bj[2] < bi[0] or bi[3] < bj[1] or bj[3] < bi[1]:
                continue
            if gap(items[i], items[j]) <= touch_tol:
                union(i, j)

    bad_nets = []
    for net in sorted({it.net for it in items if it.net}):
        if net == "GND":          # carried by the pour; checked separately below
            continue
        pads = [k for k, it in enumerate(items) if it.net == net and "." in it.tag]
        if len(pads) < 2:
            continue
        groups = {find(k) for k in pads}
        if len(groups) > 1:
            members = defaultdict(list)
            for k in pads: members[find(k)].append(items[k].tag)
            bad_nets.append((net, list(members.values())))

    print(f"\nCONNECTIVITY: {len(bad_nets)} net(s) not fully connected")
    for net, groups in bad_nets:
        print(f"  {net}: {len(groups)} islands -> " +
              " | ".join(",".join(sorted(g)) for g in groups))

    # ── Clearance ───────────────────────────────────────────────────────────
    viol = []
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            a, b = items[i], items[j]
            if a.net == b.net and a.net:
                continue
            if not (a.layers & b.layers):
                continue
            bi, bj = boxes[i], boxes[j]
            pad = CLEARANCE_MM
            if bi[2]+pad < bj[0] or bj[2]+pad < bi[0] or bi[3]+pad < bj[1] or bj[3]+pad < bi[1]:
                continue
            g = gap(a, b)
            if g < CLEARANCE_MM - 1e-6:
                viol.append((g, a.tag, a.net, b.tag, b.net))
    viol.sort()
    print(f"\nCLEARANCE: {len(viol)} violation(s) below {CLEARANCE_MM} mm")
    for g, ta, na, tb, nb in viol[:25]:
        print(f"  {g:6.3f} mm  {ta}[{na}] <-> {tb}[{nb}]")

    # ── Board edge ──────────────────────────────────────────────────────────
    xs, ys = [], []
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts:
            xs += [mm(d.GetStart().x), mm(d.GetEnd().x)]
            ys += [mm(d.GetStart().y), mm(d.GetEnd().y)]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    edge = []
    for it in items:
        bb = it.bbox()
        if bb[0] < x0+EDGE_MM or bb[1] < y0+EDGE_MM or bb[2] > x1-EDGE_MM or bb[3] > y1-EDGE_MM:
            edge.append(it.tag)
    print(f"\nEDGE: {len(edge)} item(s) within {EDGE_MM} mm of the outline"
          + (": " + ", ".join(sorted(set(edge))[:12]) if edge else ""))

    # ── Ground pour ─────────────────────────────────────────────────────────
    # GND is carried by the bottom pour rather than tracks, so the check is:
    # does every ground pad actually reach the copper, and is that copper one
    # island rather than several? A pad sitting inside its thermal relief with
    # no spoke reaching the pour looks perfect on screen and is not connected.
    pour_bad = []
    pour_regions = 0
    for z in [board.GetArea(i) for i in range(board.GetAreaCount())]:
        if z.GetNetname() != "GND":
            continue
        poly = z.GetFilledPolysList(pcbnew.B_Cu)
        pour_regions = poly.OutlineCount()
        for fp in board.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() != "GND":
                    continue
                cx, cy = p.GetPosition().x, p.GetPosition().y
                reach = max(p.GetSize().x, p.GetSize().y)/2 + pcbnew.FromMM(0.12)
                hits = 0
                for dx, dy in ((reach,0), (-reach,0), (0,reach), (0,-reach)):
                    if poly.Contains(pcbnew.VECTOR2I(int(cx+dx), int(cy+dy))):
                        hits += 1
                if hits < 2:
                    pour_bad.append(f"{fp.GetReference()}.{p.GetNumber()}({hits} spokes)")
    print(f"\nGND POUR: {pour_regions} region(s); "
          f"{len(pour_bad)} pad(s) with fewer than 2 spokes into copper"
          + (": " + ", ".join(pour_bad) if pour_bad else ""))

    ok = not bad_nets and not viol and not edge and not pour_bad and pour_regions == 1
    print("\n" + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "motoglow.kicad_pcb"))
