# THE DEPOT kit for Roblox in the chunky style (see chunky.py): the delivery depot that is the game's lobby. it sits
# beside the warehouse kit (same steel, same safety yellow). 1 unit = 1 stud, Z up, the front faces -Y, the floor at z 0.
#   dp_dockbay     the surround of one loading bay, 24 x 21 x 2 round an EMPTY 20 x 18 opening (the wall is y +1.0),
#                  with a number plate and a light bar on the header, two bumpers, and a 20 x 8 dock plate in front
#   dp_conveyor    20 of straight roller conveyor, 4 wide, the roller tops at z 3.6, three cartons riding on it
#   dp_office      the dispatch cabin, 26 x 12 x 11 (13 with the roof kit): lit windows across the front and the +X
#                  side, a door on the -X side, a sign plate over the front windows
#   dp_palletjack  a hand pallet truck (forks at -Y, the handle at +Y) carrying a pallet and two cartons
# the plates that get a number or a sign later are the only piece of their colour (PLATE) in their model.
# run: blender -b --factory-startup -P tools/roblox/depot_models.py -- <out_dir>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chunky import *
from chunky import _emit, _bevel

WARM, ROLL, PLATE, GREEN = 'ffe9b8', '8a909e', '1f2230', '7dff4f'

# ------------------------------------------------------------------ dp_dockbay (the wall is at y +1.0; the opening is x -10 .. 10, z 0 .. 18)
reset()
for s in (-1, 1):
    box('plastic', STEEL, 2.0, 2.0, 18.3, s * 11.0, 0, 9.15, bevel=0.4)                    # a leg
    box('plastic', YEL, 2.1, 1.25, 3.0, s * 10.9, -1.525, 1.5, bevel=0.3)                  # its bumper, out to y -2.2
    for z in (0.85, 2.15): box('plastic', INK, 2.2, 1.35, 0.6, s * 10.9, -1.525, z, bevel=0.12)
box('plastic', STEEL, 24.0, 2.0, 3.0, 0, 0, 19.5, bevel=0.5)                              # the header
box('plastic', PLATE, 5.0, 0.4, 2.3, 0, -1.05, 19.8, bevel=0.12)                          # the bay-number plate
box('plastic', INK, 17.0, 1.1, 0.6, 0, -1.45, 18.3, bevel=0.18)                           # the light bar on the header's lower edge
box('neon', LIGHT, 15.6, 0.6, 0.48, 0, -1.76, 18.2, bevel=0.12)
box('diamond', STEEL, 19.96, 7.3, 0.4, 0, -4.65, 0.2, bevel=0.1)                          # the dock plate, y -1 .. -9
box('plastic', YEL, 20.0, 0.8, 0.44, 0, -8.6, 0.22, bevel=0.12)                           # ...with a yellow front edge
flush('dp_dockbay')

# ------------------------------------------------------------------ dp_conveyor (runs along X; the roller tops are z 3.6)
reset()
TOP, R = 3.6, 0.45
box('plastic', DARK, 19.6, 3.0, 0.6, 0, 0, 2.55, bevel=0.15)                              # the bed under the rollers
for s in (-1, 1):
    box('plastic', YEL, 20.0, 0.66, 1.5, 0, s * 1.64, 3.15, bevel=0.22)                   # a side rail
    for x in (-8, 8): box('plastic', INK, 1.3, 0.72, 1.58, x, s * 1.64, 3.15, bevel=0.16)  # ...clamped where a leg meets it
for i in range(16):
    cyl('plastic', ROLL, R, 2.8, -9.375 + i * 1.25, 0, TOP - R, axis='y', segs=10, bevel=0.1)
for x in (-8, 8):
    for s in (-1, 1):
        box('plastic', STEEL, 1.0, 1.0, 2.4, x, s * 1.45, 1.4, bevel=0.22)                # a leg
        box('plastic', DARK, 1.7, 1.1, 0.5, x, s * 1.45, 0.25, bevel=0.14)                # ...and its foot
    box('plastic', STEEL, 0.7, 2.4, 0.7, x, 0, 1.3, bevel=0.16)
box('plastic', STEEL, 3.2, 2.6, 1.4, 0, 0, 1.6, bevel=0.3)                                # the drive box
cyl('neon', GREEN, 0.4, 0.3, 0.8, -1.35, 1.7, axis='y', segs=10, bevel=0.08)              # ...with a running lamp
carton(-5.6, 0.0, TOP, 3.2, 2.3, 2.9, 0.05)
carton(0.4, 0.05, TOP, 2.4, 2.2, 1.8, -0.12)
carton(5.9, -0.02, TOP, 3.0, 2.3, 2.3, 0.07)
flush('dp_conveyor')

# ------------------------------------------------------------------ dp_office (x -13 .. 13, y -6 .. 6; the roof is z 11)
reset()
box('plastic', DARK, 25.6, 11.6, 1.5, 0, 0, 0.75, bevel=0.3)                              # the base band
box('plastic', STEEL, 25.2, 11.2, 9.2, 0, 0, 5.8, bevel=0.5)                              # the cabin
box('plastic', DARK, 26.0, 12.0, 0.9, 0, 0, 10.55, bevel=0.3)                             # the flat roof
# the window band wraps the front +X corner: one dark block showing on those two faces, the panes on top of it
bx0, bx1, by0, by1 = -11.7, 12.8, -5.8, 4.6
box('plastic', INK, bx1 - bx0, by1 - by0, 4.2, (bx0 + bx1) / 2, (by0 + by1) / 2, 5.0, bevel=0.2)
for x in (-9.5, -5.7, -1.9, 1.9, 5.7, 9.5):
    box('neon', WARM, 3.2, 0.3, 3.4, x, -5.73, 5.0, bevel=0.1)
for y in (-3.45, -0.35, 2.75):
    box('neon', WARM, 0.3, 2.5, 3.4, 12.73, y, 5.0, bevel=0.1)
box('plastic', PLATE, 12.0, 0.3, 2.0, 0, -5.65, 8.6, bevel=0.1)                           # the sign plate
sx0, sx1, sy0, sy1 = bx0 - 0.1, bx1 + 0.06, by0 - 0.06, by1 + 0.1                           # a sill under the windows, round the same corner
box('plastic', YEL, sx1 - sx0, sy1 - sy0, 0.55, (sx0 + sx1) / 2, (sy0 + sy1) / 2, 2.65, bevel=0.16)
# the door on the -X side
box('plastic', DARK, 0.4, 4.4, 7.7, -12.66, 0, 3.85, bevel=0.14)
box('plastic', YEL, 0.4, 3.4, 7.0, -12.74, 0, 3.6, bevel=0.14)
box('neon', WARM, 0.3, 1.8, 1.8, -12.85, 0, 5.3, bevel=0.1)
box('plastic', INK, 0.36, 0.5, 1.0, -12.82, -1.1, 3.3, bevel=0.1)
# on the roof: one fat AC unit and an antenna stub
box('plastic', ROLL, 7.0, 4.6, 1.6, 5.0, 0.6, 11.75, bevel=0.4)
cyl('plastic', INK, 1.6, 0.5, 6.4, 0.6, 12.65, segs=14, bevel=0.14)
cyl('plastic', ROLL, 0.55, 0.3, 6.4, 0.6, 12.85, segs=10, bevel=0.1)
box('plastic', DARK, 3.0, 0.3, 0.9, 3.4, -1.72, 11.75, bevel=0.1)
cyl('plastic', DARK, 1.0, 0.6, -8.0, 2.0, 11.25, segs=12, bevel=0.16)
cyl('plastic', STEEL, 0.45, 1.0, -8.0, 2.0, 12.0, segs=10, bevel=0.1)
cyl('neon', PINK, 0.6, 0.6, -8.0, 2.0, 12.7, segs=10, bevel=0.2)
flush('dp_office')

# ------------------------------------------------------------------ dp_palletjack (forks at -Y, y -3.5 .. 3.5; the pallet overhangs the tips)
reset()
FT = 0.7                                                                                  # the fork tops: the pallet deck rests on them
for s in (-1, 1):
    box('plastic', YEL, 0.95, 5.2, 0.45, s * 0.92, -0.9, FT - 0.225, bevel=0.2)           # a fork
    cyl('plastic', INK, 0.32, 0.6, s * 0.92, -2.7, 0.32, axis='x', segs=10, bevel=0.1)    # its load wheel
    cyl('plastic', INK, 0.65, 0.7, s * 0.5, 2.5, 0.65, axis='x', segs=12, bevel=0.18)     # a steer wheel
box('plastic', YEL, 2.8, 0.9, 1.5, 0, 1.55, 1.0, bevel=0.3)                               # the fork carriage
box('plastic', YEL, 2.0, 1.4, 1.9, 0, 2.5, 1.75, bevel=0.4)                               # the pump tower
cyl('plastic', DARK, 0.62, 0.5, 0, 2.6, 2.8, segs=12, bevel=0.14)                         # ...and its cap
box('plastic', DARK, 0.6, 0.6, 1.9, 0, 2.85, 3.25, bevel=0.18, rot=RX(-0.35))             # the handle: a fat T
box('plastic', INK, 2.8, 0.75, 0.75, 0, 3.125, 4.025, bevel=0.24)
box('wood', WOOD, 5.0, 5.0, 0.3, 0, -1.5, FT + 0.15, bevel=0.08)                          # the pallet: a deck on three runners, 0.2 off the floor
for x in (-2.05, 0, 2.05):
    box('wood', WOOD2, 0.8, 4.8, 0.5, x, -1.5, FT - 0.25, bevel=0.1)
carton(-0.1, -1.5, FT + 0.3, 4.2, 4.0, 2.7, 0.04)
carton(0.5, -1.2, FT + 3.0, 2.6, 2.4, 1.8, 0.4)
flush('dp_palletjack')
