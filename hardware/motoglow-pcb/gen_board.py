#!/usr/bin/env python3
"""Generate the MotoGlow controller PCB.

Two-layer, 80 x 60 mm, entirely through-hole so it can be hand-assembled.
Run this, then:
    kicad-cli pcb drc     motoglow.kicad_pcb --exit-code-violations
    kicad-cli pcb export gerbers motoglow.kicad_pcb -o gerbers/

CIRCUIT NOTES

Master switch and reverse polarity. Q1 is a P-channel MOSFET high-side switch:
source to the battery, drain to everything else. The handlebar toggle does not
carry load current -- it pulls Q1's gate down through R2, drawing about 110 uA,
so the switch contacts never see more than a trickle and the box draws exactly
nothing when it is off. D1 clamps Vgs so a load dump cannot punch through the
gate oxide. Reverse polarity is handled by D2, a unidirectional TVS across the
input: connect the battery backwards and it conducts, blowing the inline fuse
before anything downstream notices. Q1 also stays off under reverse polarity,
because its gate cannot be pulled negative of its source.

Level shifting. The strips want at least 3.5 V on the data line and the Pico
puts out 3.3 V. That is marginal on a bench and unreliable on three feet of
wire next to an ignition system, so U2 buffers all four data lines up to 5 V.
This is the single most common reason a home-built strip controller glitches.
"""
import pcbnew, os, sys

MM   = pcbnew.FromMM
BW, BH = 80.0, 60.0                       # board size
HERE = os.path.dirname(os.path.abspath(__file__))
SYSFP = '/usr/share/kicad/footprints'

# ─── Bill of materials / placement ──────────────────────────────────────────
# ref, library, footprint, x, y, rotation, value, comment for the silkscreen
PARTS = [
 ("U3","LOCAL","RPi_Pico_2W_Horizontal",            40,13,   0,"Pico 2 W",""),
 ("U2","Package_DIP","DIP-14_W7.62mm_Socket",44,28,0,"74AHCT125N",""),
 ("U1","Converter_DCDC","Converter_DCDC_RECOM_R-78E-0.5_THT",60,31,0,"R-78E5.0-1.0",""),
 ("Q1","Package_TO_SOT_THT","TO-220-3_Vertical",8,29,0,"IRF4905",""),
 ("C1","Capacitor_THT","CP_Radial_D10.0mm_P5.00mm",70,40,0,"470uF 35V",""),
 ("C3","Capacitor_THT","CP_Radial_D5.0mm_P2.50mm",58,37,0,"10uF 16V",""),
 ("C2","Capacitor_THT","C_Disc_D5.0mm_W2.5mm_P5.00mm",58,42,0,"100nF",""),
 ("C4","Capacitor_THT","C_Disc_D5.0mm_W2.5mm_P5.00mm",58,46,0,"100nF",""),
 ("C5","Capacitor_THT","C_Disc_D5.0mm_W2.5mm_P5.00mm",36,43,0,"100nF",""),
 ("C6","Capacitor_THT","C_Disc_D5.0mm_W2.5mm_P5.00mm",36,31,0,"100nF",""),
 ("C7","Capacitor_THT","C_Disc_D5.0mm_W2.5mm_P5.00mm",32,35,0,"100nF",""),
 ("D2","Diode_THT","D_DO-201AD_P3.81mm_Vertical_KathodeUp",76,29,90,"1.5KE18A",""),
 ("D1","Diode_THT","D_DO-35_SOD27_P2.54mm_Vertical_KathodeUp",8,34,0,"BZX55C15",""),
 ("R1","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",4,39,0,"100k",""),
 ("R2","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",10,39,0,"10k",""),
 ("R3","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",18,47,0,"330",""),
 ("R4","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",28,47,0,"330",""),
 ("R5","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",38,47,0,"330",""),
 ("R6","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",48,47,0,"330",""),
 ("R7","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",70,22,0,"10k",""),
 ("R8","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",38,27,0,"1k",""),
 ("R9","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",28,27,0,"47k",""),
 ("R10","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",28,31,0,"10k",""),
 ("R11","Resistor_THT","R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",4,46,0,"470",""),
 ("LED1","LED_THT","LED_D3.0mm",9,46,0,"STATUS",""),
 ("J1","TerminalBlock_Phoenix","TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
                                                    72,16,  90,"12V IN",""),
 ("J6","TerminalBlock_Phoenix","TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal",
                                                     8,20,  90,"BAR",""),
 ("J2","TerminalBlock_Phoenix","TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal",
                                                    13,53,   0,"RUN0 L",""),
 ("J3","TerminalBlock_Phoenix","TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal",
                                                    28.5,53,   0,"RUN1 R",""),
 ("J4","TerminalBlock_Phoenix","TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal",
                                                    44,53,   0,"RUN2 ENG",""),
 ("J5","TerminalBlock_Phoenix","TerminalBlock_Phoenix_PT-1,5-4-3.5-H_1x04_P3.50mm_Horizontal",
                                                    59.5,53,   0,"RUN3 TAIL",""),
 ("H1","MountingHole","MountingHole_2.7mm_M2.5",     3.5, 3.5,0,"M2.5",""),
 ("H2","MountingHole","MountingHole_2.7mm_M2.5",    76.5, 3.5,0,"M2.5",""),
 ("H3","MountingHole","MountingHole_2.7mm_M2.5",     3.5,56.5,0,"M2.5",""),
 ("H4","MountingHole","MountingHole_2.7mm_M2.5",    76.5,56.5,0,"M2.5",""),
]

# ─── Netlist ────────────────────────────────────────────────────────────────
# Polarity conventions, all marked on the silkscreen by add_polarity_marks():
#   D1, D2  pad 1 = cathode (the footprints already silk a "K" there)
#   C1, C3  pad 1 = positive
#   LED1    pad 1 = anode
#   Q1      1 = gate, 2 = drain, 3 = source   (IRF4905 TO-220AB)
#   U1      1 = Vin,  2 = GND,   3 = Vout     (RECOM R-78E)
NETS = {
 "BAT+":   [("J1","1"),("D2","1"),("Q1","3"),("R1","2"),("D1","1")],
 "GATE":   [("Q1","1"),("R1","1"),("R2","1"),("D1","2")],
 "SW_A":   [("R2","2"),("J6","1")],
 "+12VSW": [("Q1","2"),("C1","1"),("C2","1"),("U1","1"),("R9","1"),
            ("J2","1"),("J3","1"),("J4","1"),("J5","1")],
 "+5V":    [("U1","3"),("C3","1"),("C4","1"),("U2","14"),("U3","39")],
 "+3V3":   [("U3","36"),("R7","1")],
 "GP2":    [("U3","4"),("U2","2")],
 "GP3":    [("U3","5"),("U2","5")],
 "GP4":    [("U3","6"),("U2","9")],
 "GP5":    [("U3","7"),("U2","12")],
 "Y1":     [("U2","3"),("R3","1")],
 "Y2":     [("U2","6"),("R4","1")],
 "Y3":     [("U2","8"),("R5","1")],
 "Y4":     [("U2","11"),("R6","1")],
 "DATA0":  [("R3","2"),("J2","3")],
 "DATA1":  [("R4","2"),("J3","3")],
 "DATA2":  [("R5","2"),("J4","3")],
 "DATA3":  [("R6","2"),("J5","3")],
 "BTN":    [("J6","3"),("R7","2"),("R8","1")],
 "GP6":    [("R8","2"),("U3","9"),("C6","1")],
 "VSENSE": [("R9","2"),("R10","1"),("C7","1"),("U3","31")],
 "GP7":    [("U3","10"),("R11","1")],
 "LED_A":  [("R11","2"),("LED1","1")],
 "GND":    [("J1","2"),("D2","2"),("C1","2"),("C2","2"),("C3","2"),("C4","2"),
            ("C5","2"),("C6","2"),("C7","2"),("U1","2"),("C5","1"),
            ("U2","1"),("U2","4"),("U2","7"),("U2","10"),("U2","13"),
            ("U3","3"),("U3","8"),("U3","13"),("U3","18"),
            ("U3","23"),("U3","28"),("U3","33"),("U3","38"),
            ("R10","2"),("LED1","2"),
            ("J2","2"),("J2","4"),("J3","2"),("J3","4"),
            ("J4","2"),("J4","4"),("J5","2"),("J5","4"),
            ("J6","2"),("J6","4")],
}
# C5 decouples U2; its pad 1 belongs to +5V, not GND. Fix that here so the
# GND list above stays a simple flat dump of every grounded pad.
NETS["GND"].remove(("C5","1"))
NETS["+5V"].append(("C5","1"))


def _text(board, txt, x, y, size, layer, mirror=False, bold=False, just=None):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size)))
    t.SetTextThickness(MM(size * (0.18 if bold else 0.14)))
    t.SetBold(bold)
    t.SetMirrored(mirror)
    if just is not None:
        t.SetHorizJustify(just)
    board.Add(t)
    return t


def add_silkscreen(board):
    """Front title, and a full connector legend on the back.

    There is nowhere on the front to print connector pinouts -- the terminal
    blocks sit against the board edge and their own bodies would cover any text
    next to them. The back of the board is completely empty, so the legend goes
    there, where you can read it while the loom is in your hands. Polarity marks
    for the diodes, electrolytics and the LED come from the stock footprints.
    """
    _text(board, "MOTOGLOW  CONTROLLER  v1", BW/2, 26.5, 1.4, pcbnew.F_SilkS, bold=True)

    legend = [
        ("MOTOGLOW CONTROLLER v1", 1.6, True),
        ("KTM 890 Adventure  -  4x 12V WS2811 runs", 1.0, False),
        ("", 0.8, False),
        ("J1  1:+12V (5A FUSE AT BATTERY)   2:GND", 1.1, False),
        ("J2  RUN0 left chain    J3  RUN1 right chain", 1.1, False),
        ("J4  RUN2 engine        J5  RUN3 tail", 1.1, False),
        ("    all four:  1:+12V  2:GND  3:DATA  4:GND", 1.1, False),
        ("J6  1:SWITCH  2:GND  3:BUTTON  4:GND", 1.1, False),
        ("", 0.8, False),
        ("Q1 IRF4905 G-D-S      U1 R-78E5.0 Vin-GND-Vout", 0.95, False),
        ("U2 74AHCT125 (pin1 = notch)   U3 Pico 2 W", 0.95, False),
        ("D1 BZX55C15  D2 1.5KE18A   pin 1 = cathode", 0.95, False),
        ("C1 470u/35V  C3 10u/16V    pin 1 = positive", 0.95, False),
        ("", 0.8, False),
        ("DO NOT run without the fuse. Reverse polarity", 0.95, False),
        ("is cleared by D2 blowing that fuse.", 0.95, False),
    ]
    y = 8.0
    for txt, size, bold in legend:
        if txt:
            _text(board, txt, BW/2, y, size, pcbnew.B_SilkS, mirror=True, bold=bold)
        y += size * 2.0 + 0.8


def build():
    board = pcbnew.BOARD()

    # Design rules. Conservative against any 2-layer fab: JLCPCB's floor is
    # 0.127 mm trace and space, and we are nowhere near it.
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    nc = board.GetAllNetClasses()['Default']
    nc.SetClearance(MM(0.25)); nc.SetTrackWidth(MM(0.3))
    nc.SetViaDiameter(MM(0.8)); nc.SetViaDrill(MM(0.4))

    # Board outline.
    for (x1,y1,x2,y2) in ((0,0,BW,0),(BW,0,BW,BH),(BW,BH,0,BH),(0,BH,0,0)):
        seg = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(MM(x1),MM(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(MM(x2),MM(y2)))
        seg.SetLayer(pcbnew.Edge_Cuts); seg.SetWidth(MM(0.1))
        board.Add(seg)

    # Footprints.
    for ref, lib, fp, x, y, rot, val, _c in PARTS:
        path = os.path.join(HERE,'lib.pretty') if lib=="LOCAL" else os.path.join(SYSFP, lib+'.pretty')
        m = pcbnew.FootprintLoad(path, fp)
        if m is None:
            sys.exit(f"footprint not found: {lib}:{fp}")
        m.SetReference(ref); m.SetValue(val)
        board.Add(m)
        m.SetPosition(pcbnew.VECTOR2I(MM(x),MM(y)))
        if rot: m.SetOrientationDegrees(rot)

    add_silkscreen(board)

    # Nets.
    for name, pads in NETS.items():
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
        for ref, padnum in pads:
            fpr = board.FindFootprintByReference(ref)
            if fpr is None: sys.exit(f"no footprint {ref}")
            pad = fpr.FindPadByNumber(padnum)
            if pad is None: sys.exit(f"{ref} has no pad {padnum}")
            pad.SetNet(net)
    return board


if __name__ == "__main__":
    b = build()
    out = os.path.join(HERE,'motoglow.kicad_pcb')
    b.Save(out)
    print("wrote", out)
    # Dump geometry so routing can be written against real numbers.
    for ref,_l,_f,_x,_y,_r,_v,_c in PARTS:
        m = b.FindFootprintByReference(ref)
        bb = m.GetBoundingBox(False, False)
        print(f"{ref:5s} bbox x {pcbnew.ToMM(bb.GetLeft()):6.2f}..{pcbnew.ToMM(bb.GetRight()):6.2f}"
              f"  y {pcbnew.ToMM(bb.GetTop()):6.2f}..{pcbnew.ToMM(bb.GetBottom()):6.2f}")
