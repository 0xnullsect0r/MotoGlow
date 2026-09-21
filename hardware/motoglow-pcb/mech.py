"""Mechanical facts shared by the PCB generator, the fit checker and the case.

The first version of this project had the board and the enclosure designed
against separate, silently divergent assumptions: the case was built for a
75 x 55 mm board that had become 80 x 60, and every panel connector's body
landed inside a component. Both halves verified perfectly on their own.

So the numbers that couple them live here, once, and everything reads them.
"""

# ─── Board ───────────────────────────────────────────────────────────────────
BOARD_W, BOARD_H = 80.0, 60.0
HOLE_INSET       = 3.5          # M2.5 mounting holes, in from each corner
PCB_T            = 1.6

# ─── Stack-up inside the case ────────────────────────────────────────────────
FLOOR_T   = 2.8                 # outside of the tub floor to its inside face
STANDOFF  = 4.0                 # inside floor to the underside of the PCB
PCB_TOP   = STANDOFF + PCB_T    # inside floor to the top of the PCB
MARGIN    = 4.0                 # board edge to the inside face of the wall

# MARGIN is 4 mm rather than 2 for a reason: it is nearly the depth of a panel
# connector's nut, so the wide part of the connector sits almost entirely off
# the board and only the narrower barrel reaches over it. That buys about 3 mm
# of box height, which is worth more than 4 mm of width.

# ─── Panel connector envelope ────────────────────────────────────────────────
# An SP13 reaches into the box in two stages: the nut is wide but shallow and
# sits against the wall, then the body behind it is narrower and goes deeper.
NUT_R      = 10.0               # nut across corners / 2
NUT_DEPTH  = 5.0                # how far in the nut reaches
BODY_R     = 7.0                # connector barrel behind the nut
BODY_DEPTH = 14.0               # how far in the whole connector reaches

# THE RULE that keeps the two halves compatible:
# any component standing within BODY_DEPTH of a board edge shares space with a
# connector, so it may be no taller than KEEPOUT_MAX_H. The screw terminals are
# the tall things that genuinely have to live on the edge, so they set it.
KEEPOUT_MAX_H = 11.0

# Component heights above the PCB, in millimetres. Catalogue worst cases, since
# these set the height of the box and being wrong costs a reprint.
HEIGHTS = {
    "U3": 7.0,    # Pico on soldered header strips, USB shell included
    "U2": 8.0,    # DIP-14 in a socket
    "U1": 10.4,   # RECOM R-78E, datasheet
    "Q1": 16.0,   # TO-220 standing up
    "C1": 20.0,   # 470 uF 35 V, 10 x 20 can
    "C3": 11.0,   # 10 uF 16 V, 5 x 11 can
    "D2": 12.0,   # 1.5KE in DO-201AD, standing
    "D1": 6.0, "D3": 6.0,
    "LED1": 5.0,
    "J1": 11.0,                                   # 5.08 mm terminal block
    "J2": 10.0, "J3": 10.0, "J4": 10.0, "J5": 10.0, "J6": 10.0,
}
for _r in ("C2","C4","C5","C6","C7","C8"):
    HEIGHTS[_r] = 7.0                             # 5 mm disc ceramics
for _i in range(1, 12):
    HEIGHTS[f"R{_i}"] = 8.0                       # axial resistors standing up

DEFAULT_H = 11.0                                  # unknown part: assume the limit


def height(ref):
    return HEIGHTS.get(ref, DEFAULT_H)


def port_centre_z():
    """Height of the connector axis above the inside floor.

    The barrel, not the nut, is what passes over the board, so this clears the
    tallest thing allowed on the board edge by the barrel radius. verify_fit.py
    checks the real geometry rather than trusting this formula.
    """
    return PCB_TOP + KEEPOUT_MAX_H + 1.0 + BODY_R


def interior_h():
    """Inside floor to rim: the nut must still fit, with headroom over it."""
    return port_centre_z() + NUT_R + 2.5


# ─── Panel ports, in BOARD coordinates ───────────────────────────────────────
# Faces: W = the x=0 edge, E = x=BOARD_W, N = y=0, S = y=BOARD_H.
# `at` is a position along that face: an x for N/S, a y for W/E.
# The four strip connectors go on the S face because that is the edge the
# strip terminal blocks sit on, so the pigtails inside stay short.
GLAND_R = 9.0                   # M12 cable gland body / 2
PORTS = [
    ("S",  7.0, "sp13",  "RUN0 left chain"),
    ("S", 29.0, "sp13",  "RUN1 right chain"),
    ("S", 51.0, "sp13",  "RUN2 engine"),
    ("S", 73.0, "sp13",  "RUN3 tail"),
    ("W", 30.0, "sp13",  "handlebar"),
    ("E", 30.0, "gland", "battery feed"),
]
HOLE_D = {"sp13": 13.2, "gland": 12.2}
FLANGE_R = {"sp13": NUT_R, "gland": GLAND_R}


if __name__ == "__main__":
    print(f"PCB top          {PCB_TOP:5.1f} mm above the inside floor")
    print(f"keep-out zone    {BODY_DEPTH:5.1f} mm in from each edge, max {KEEPOUT_MAX_H} mm tall")
    print(f"port centre      {port_centre_z():5.1f} mm")
    print(f"interior height  {interior_h():5.1f} mm")
    print(f"outside height   {FLOOR_T + interior_h() + 3.0:5.1f} mm (floor + inside + lid)")
    print(f"interior         {BOARD_W + 2*MARGIN:.0f} x {BOARD_H + 2*MARGIN:.0f} mm")
