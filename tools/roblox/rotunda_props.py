# THE ROTUNDA'S PROP KIT (16 Nov 2026): new chunky props for the hub (studio-tools/HubRotunda*.luau places them). the
# owner after a play-test: "in the match pads theres random pots on the ground? some of the props dont look super like
# rivals ones!". the pots went; these replace the hub's weakest old bc_* props (faceted barrels for punch bags, black
# faceted tyres, a spindly glass coffee table, spiky plants, flat teal locker boxes, a thin dumbbell rack, a plank
# bench) the chunky way: few big rounded shapes, flat matte mid-value colours, nothing near-black, no metal.
# 1 unit = 1 stud, Z up, a model's front faces -Y (Roblox +Z after the import), the floor is z 0.
#   rk_planter      a square planter with a soft bush, 3.4 x 3.4, 4.7 tall
#   rk_punchbag     a free-standing heavy bag on a weighted base, 3.2 across, 7.4 tall
#   rk_tyres        two training tyres stacked, 4.2 across, 2.3 tall
#   rk_coffeetable  a low timber table on two slab legs, 4.6 x 2.6, 1.7 tall
#   rk_lockers      a bank of three lockers on a plinth, 6.4 wide, 2 deep, 7.6 tall
#   rk_dumbbells    a low rack with three pairs of round dumbbells, 4.8 long (X), 1.8 deep, 2.6 tall
#   rk_bench        a padded gym bench, 4.6 long (X), 1.5 wide, 1.9 tall
#   rk_duckTrophy   a rubber-duck trophy on a plinth, 1.3 across, 2.4 tall (its metal painted per copy)
# run: blender -b --factory-startup -P tools/roblox/rotunda_props.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *

SLATE, SLATE2, DARK, CREAM, CREAM2 = '68707c', '5a616d', '4c535e', 'c4bfb5', 'b3aea4'
WOOD, WOOD2, LEAF, LEAF2, LEAF3, SOIL = 'a48f6c', '8c7758', '7f8f70', '6e7f62', '8e9c7c', '5e5650'
BAG, BAND, TYRE, HUB, IRON = '7e4a46', 'c4bfb5', '565b63', '8e939a', '5a616d'
reset()

# ------------------------------------------------------------------ rk_planter: a square planter with a soft bush
soft('plastic', CREAM, 3.4, 3.4, 2.2, 0, 0, 1.15, 0.45, pick='all', segs=3, small=0.0)  # (its bottom above the foot's)
soft('plastic', SLATE2, 3.6, 3.6, 0.3, 0, 0, 0.15, 0.12, pick='all', segs=2, small=0.0)   # its foot
bx('plastic', SOIL, 2.8, 2.8, 0.2, 0, 0, 2.2, 0.08)  # (0.05 over the body's top)
ball('plastic', LEAF, 1.35, 0, 0.1, 3.25, sub=3, sc=(1.0, 1.0, 0.9))
ball('plastic', LEAF2, 1.0, -0.85, -0.45, 2.85, sub=3)
ball('plastic', LEAF3, 0.95, 0.9, -0.35, 2.95, sub=3)
ball('plastic', LEAF2, 0.8, 0.25, 0.85, 2.75, sub=3)
keep('rk_planter')

# ------------------------------------------------------------------ rk_punchbag: a heavy bag on a weighted round base
lathe('plastic', DARK, dome_prof(1.6, 0.7, rim=0.35, steps=6), segs=32)                   # the weighted base
cy('plastic', SLATE, 0.45, 0.8, 0, 0, 1.3, segs=24, bevel=0.08)                          # its neck
_bag = [(0.0, 1.55), (0.7, 1.58), (0.98, 1.75), (1.1, 2.1), (1.12, 6.3), (1.0, 6.75), (0.7, 6.95), (0.0, 7.0)]
lathe('plastic', BAG, _bag, segs=36)
for z in (2.6, 5.7):                                                                     # two pale straps
    cy('plastic', BAND, 1.15, 0.32, 0, 0, z, segs=36, bevel=0.06)
cy('plastic', SLATE, 0.5, 0.45, 0, 0, 7.2, segs=24, bevel=0.1)                           # the top cap
keep('rk_punchbag')

# ------------------------------------------------------------------ rk_tyres: two tyres stacked
for i, z in enumerate((0.55, 1.68)):
    M = T(0.12 * i, -0.08 * i, z) @ RZ(D(14 * i))
    lathe('plastic', TYRE, ring_prof(1.55, 0.55, steps=14), M=M, segs=40, cap=False)
    cy('plastic', HUB, 1.05, 0.5, 0, 0, 0, segs=32, bevel=0.08, M=M)
keep('rk_tyres')

# ------------------------------------------------------------------ rk_coffeetable: a timber top on two slab legs
soft('plastic', WOOD, 4.6, 2.6, 0.5, 0, 0, 1.45, 0.22, pick='all', segs=3, small=0.0)
for sx in (-1, 1):
    soft('plastic', SLATE, 0.55, 2.1, 1.25, sx * 1.6, 0, 0.62, 0.18, pick='all', segs=2, small=0.0)
soft('plastic', WOOD2, 3.0, 1.6, 0.25, 0, 0, 0.45, 0.1, pick='all', segs=2, small=0.0)    # the shelf under it
keep('rk_coffeetable')

# ------------------------------------------------------------------ rk_lockers: three lockers on a plinth
soft('plastic', SLATE, 6.4, 2.0, 7.0, 0, 0, 0.6 + 3.5, 0.3, pick='all', segs=3, small=0.0)
soft('plastic', DARK, 6.2, 1.8, 0.6, 0, 0.05, 0.3, 0.15, pick='all', segs=2, small=0.0)
soft('plastic', SLATE2, 6.6, 2.2, 0.35, 0, 0, 7.72, 0.15, pick='all', segs=2, small=0.0)  # (its top above the body's: no shared plane)
for i in range(3):
    x = -2.05 + 2.05 * i
    soft('plastic', CREAM, 1.8, 0.2, 6.3, x, -1.02, 0.6 + 3.35, 0.12, pick='all', segs=2, small=0.0)
    for k in range(3):                                                                   # vents near the top
        soft('plastic', DARK, 1.0, 0.12, 0.16, x, -1.14, 5.9 + 0.32 * k, 0.06, pick='all', segs=2, small=0.0)
    soft('plastic', SLATE2, 0.18, 0.2, 0.9, x + 0.6, -1.18, 3.9, 0.08, pick='all', segs=2, small=0.0)  # the handle
keep('rk_lockers')

# ------------------------------------------------------------------ rk_dumbbells: a low rack, three pairs on it
for sx in (-1, 1):
    soft('plastic', SLATE, 0.5, 1.8, 1.9, sx * 2.15, 0, 0.95, 0.2, pick='all', segs=2, small=0.0)
for z, y in ((1.25, -0.42), (1.6, 0.42)):                                                # two rails, the back one higher
    soft('plastic', DARK, 4.4, 0.42, 0.22, 0, y, z, 0.1, pick='all', segs=2, small=0.0)
for i in range(3):
    x = -1.35 + 1.35 * i
    for y, z in ((-0.42, 1.25), (0.42, 1.6)):
        cy('plastic', HUB, 0.12, 0.7, x, y, z + 0.4, axis='x', segs=12, bevel=0.02)
        r = 0.3 + 0.06 * i
        for s in (-1, 1):
            cy('plastic', IRON, r, 0.26, x + s * 0.42, y, z + 0.4, axis='x', segs=24, bevel=0.07)
keep('rk_dumbbells')

# ------------------------------------------------------------------ rk_bench: a padded gym bench
soft('plastic', BAG, 4.6, 1.5, 0.45, 0, 0, 1.62, 0.2, pick='all', segs=3, small=0.0)      # the pad
soft('plastic', SLATE, 4.2, 1.1, 0.22, 0, 0, 1.28, 0.08, pick='all', segs=2, small=0.0)   # its board
for sx in (-1, 1):
    soft('plastic', SLATE, 0.5, 1.2, 1.2, sx * 1.6, 0, 0.65, 0.15, pick='all', segs=2, small=0.0)  # (above the foot's bottom)
    soft('plastic', DARK, 0.8, 1.5, 0.2, sx * 1.6, 0, 0.1, 0.08, pick='all', segs=2, small=0.0)
keep('rk_bench')

# ------------------------------------------------------------------ rk_duckTrophy: a rubber-duck trophy (owner, 16 Nov: "can the trophy
# case, can they be ducky trophies?"). a slate plinth with a blank little plate, a short stem and a dish, the duck on it
# in one metal colour. METAL is a stand-in: each copy is painted gold, silver or bronze (B.put's colour map)
METAL = 'b0b4ba'
soft('plastic', DARK, 1.3, 1.3, 0.5, 0, 0, 0.25, 0.14, pick='all', segs=3, small=0.0)          # the plinth
soft('plastic', CREAM2, 0.72, 0.08, 0.24, 0, -0.66, 0.26, 0.04, pick='all', segs=2, small=0.0)  # its little plate (blank)
cy('plastic', METAL, 0.5, 0.1, 0, 0, 0.55, segs=32, bevel=0.03)                                  # a foot on the plinth
cy('plastic', METAL, 0.17, 0.36, 0, 0, 0.78, segs=20, bevel=0.03)                                # the stem
cy('plastic', METAL, 0.42, 0.12, 0, 0, 1.0, segs=32, bevel=0.04)                                 # the dish
ball('plastic', METAL, 0.56, 0, 0.06, 1.42, sc=(0.86, 1.18, 0.78), sub=3)                       # the body
ball('plastic', METAL, 0.36, 0, -0.34, 2.0, sub=3)                                              # the head
soft('plastic', METAL, 0.36, 0.32, 0.15, 0, -0.68, 1.95, 0.07, pick='all', segs=2, small=0.0)   # the beak
ball('plastic', METAL, 0.24, 0, 0.62, 1.62, sc=(0.8, 1.0, 1.15), sub=2)                         # the tail
for sx in (-1, 1):
    ball('plastic', METAL, 0.32, sx * 0.47, 0.1, 1.42, sc=(0.42, 1.0, 0.72), sub=2)             # the wings
keep('rk_duckTrophy')

export_all('rotunda_props.glb')
if len(sys.argv) > sys.argv.index('--') + 2:
    preview(sys.argv[sys.argv.index('--') + 2], cols=4)
