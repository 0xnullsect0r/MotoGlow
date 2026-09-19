#!/usr/bin/env python3
"""Generate the Raspberry Pi Pico 2 W footprint.

KiCad 7 ships no Pico footprint, and building it from two 1x20 headers makes the
pad numbering ambiguous (pin 21 is adjacent to pin 20, so the second header runs
backwards). Generating all 40 pads explicitly removes that ambiguity.

Orientation: USB connector to the RIGHT. Pins 1-20 run right-to-left along the
BOTTOM row, pins 21-40 left-to-right along the TOP row. That puts GP2..GP7 on
the bottom row facing the rest of the circuit, which is what keeps the level
shifter fan-out free of vias.
"""
import os

PITCH, ROW_SEP = 2.54, 17.78
N_SIDE, BODY_L, BODY_W = 20, 51.0, 21.0
HALF = (N_SIDE - 1) * PITCH / 2.0          # 24.13

NAMES = {
    1:"GP0",2:"GP1",3:"GND",4:"GP2",5:"GP3",6:"GP4",7:"GP5",8:"GND",9:"GP6",10:"GP7",
    11:"GP8",12:"GP9",13:"GND",14:"GP10",15:"GP11",16:"GP12",17:"GP13",18:"GND",
    19:"GP14",20:"GP15",21:"GP16",22:"GP17",23:"GND",24:"GP18",25:"GP19",26:"GP20",
    27:"GP21",28:"GND",29:"GP22",30:"RUN",31:"GP26_A0",32:"GP27_A1",33:"AGND",
    34:"GP28_A2",35:"ADC_VREF",36:"3V3_OUT",37:"3V3_EN",38:"GND",39:"VSYS",40:"VBUS",
}

def pad_pos(pin):
    if pin <= N_SIDE:                       # bottom row, right to left
        return (HALF - (pin - 1) * PITCH,  ROW_SEP / 2.0)
    return (-HALF + (pin - 21) * PITCH, -ROW_SEP / 2.0)   # top row, left to right

lines = [
 '(footprint "RPi_Pico_2W_Horizontal" (version 20221018) (generator motoglow)',
 '  (layer "F.Cu")',
 '  (descr "Raspberry Pi Pico 2 W, through-hole, USB to the right. '
 'Solder to header pins at both ends rather than socketing it: sockets back out under vibration.")',
 '  (tags "raspberry pi pico rp2350 module")',
 '  (attr through_hole)',
 f'  (fp_text reference "U**" (at 0 {-BODY_W/2 - 2.2}) (layer "F.SilkS")'
 ' (effects (font (size 1 1) (thickness 0.15))))',
 f'  (fp_text value "RPi_Pico_2W" (at 0 {BODY_W/2 + 2.2}) (layer "F.Fab")'
 ' (effects (font (size 1 1) (thickness 0.15))))',
]

# Body outline on silk, broken around the pin rows, plus a fabrication outline.
hx, hy = BODY_L / 2.0, BODY_W / 2.0
for layer, w in (("F.SilkS", 0.12), ("F.Fab", 0.10)):
    for (x1, y1, x2, y2) in ((-hx,-hy, hx,-hy), (hx,-hy, hx,hy),
                             (hx,hy, -hx,hy), (-hx,hy, -hx,-hy)):
        lines.append(f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) '
                     f'(stroke (width {w}) (type solid)) (layer "{layer}"))')
# USB end marker so the module cannot be fitted backwards.
lines.append(f'  (fp_line (start {hx-4} {-hy}) (end {hx-4} {hy}) '
             '(stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
lines.append(f'  (fp_text user "USB" (at {hx-2} 0 90) (layer "F.SilkS") '
             '(effects (font (size 0.8 0.8) (thickness 0.12))))')
# Courtyard, as four lines: KiCad builds the courtyard outline from graphic
# segments, and a polygon here is not picked up by the overlap check.
cx, cy = hx + 0.25, hy + 0.25
for (x1, y1, x2, y2) in ((-cx,-cy, cx,-cy), (cx,-cy, cx,cy),
                         (cx,cy, -cx,cy), (-cx,cy, -cx,-cy)):
    lines.append(f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) '
                 '(stroke (width 0.05) (type solid)) (layer "F.CrtYd"))')

for pin in range(1, 41):
    x, y = pad_pos(pin)
    shape = "rect" if pin == 1 else "circle"
    lines.append(f'  (pad "{pin}" thru_hole {shape} (at {x:.2f} {y:.2f}) '
                 f'(size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask"))')
    # Pin name on the fab layer, so the board is readable during bring-up.
    ty = y + (2.2 if y > 0 else -2.2)
    lines.append(f'  (fp_text user "{NAMES[pin]}" (at {x:.2f} {ty:.2f} 90) (layer "F.Fab") '
                 '(effects (font (size 0.5 0.5) (thickness 0.08))))')
lines.append(')')

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib.pretty',
                   'RPi_Pico_2W_Horizontal.kicad_mod')
open(out, 'w').write('\n'.join(lines) + '\n')
print("wrote", out)
