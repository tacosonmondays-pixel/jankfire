# THE TRAINING REDO KIT (20 Nov 2026; vault Hubs/Training redo plan.md): the shaped pieces of the new compound
# (studio-tools/TrainingCompound.luau builds the big surfaces out of plain parts and places these). The 16 Nov way
# (training_models.py): a few big shapes, a 2-step bevel and a Weighted Normal, nothing under about a third of a stud,
# flat quiet colours; the 20 Nov layer on top is a SUBTLE texture, put on in Studio by MaterialVariants (the builder
# picks one per piece colour: walls plaster, piers and frames paint, slate masses slate). The old kit's cover wall,
# cover block, bench, target and grapple hoop (tv_*) are used as they are.
# 1 unit = 1 stud, Z up, a model's front faces -Y (Roblox +Z after the import), the floor is z 0 unless said.
#   tr_portal     a deep framed opening 16 wide x 14 high inside, 6 deep, 3-stud jambs and head, cut top corners
#   tr_portalBig  the same, 24 x 16 (the gatehouse's portal onto the balcony)
#   tr_parapet    an 8-long run of the balcony's parapet: a slate plinth, a pale body, a thick rounded cap, 3.2 high
#   tr_post       a distance post 2.4 x 2.4 x 6.6: a slate foot, a shaft, a sunk plate on its front, a rounded cap
#   tr_tower      the gantry's tower 8.8 x 8.8 x 16.2: plinth, body with cut corners, two bands, sunk panels, cap
#   tr_crown      the TOP's arch: two legs and a heavy lintel, 24 wide x 17.5 high x 4 deep, an amber strip under it
#   tr_desk       the tutorial console's desk 8.4 x 3 x 3.05 (the screen and its light are the builder's)
#   tr_projector  a ceiling projector ring, 10 across (z 0 = the ceiling; it hangs 1.4)
#   tr_lamp       a wall light: a chunky housing with a white panel, 3.2 x 1.1 x 4.2 (front -Y, z 0 = its foot)
# run: blender -b --factory-startup -P tools/roblox/training_redo_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *
from structkit import _emit

WALL, WALL2, PIER, PIER2, TRIM = 'c9c3b8', 'd3cec4', '8e9197', '7b7f87', 'e4e0d6'
SLATE, DEEP, AMBER, WHITE, TEAL = '5f646e', '4f545d', 'f0a53a', 'f4f6f8', '8fd8cf'
reset()

# ------------------------------------------------------------------ tr_portal, tr_portalBig
def frame(name, W, H, jamb, head, cut, depth):
    pts = [(-W / 2 - jamb, 0.0), (-W / 2 - jamb, H + head), (W / 2 + jamb, H + head), (W / 2 + jamb, 0.0),
           (W / 2, 0.0), (W / 2, H - cut), (W / 2 - cut, H), (-W / 2 + cut, H), (-W / 2, H - cut), (-W / 2, 0.0)]
    prism('plastic', PIER, pts, depth, bevel=0.35, segs=2)
    for sx in (-1, 1):  # a slate foot on each jamb, a hair proud
        soft('plastic', SLATE, jamb + 0.4, depth + 0.4, 1.4, sx * (W / 2 + jamb / 2), 0, 0.7, 0.2, pick='up', segs=2, small=0.0)
    # a pale reveal band round the inside of the head, a hair proud of the opening's top
    bx('plastic', TRIM, W - 2 * cut + 0.2, depth + 0.1, 0.6, 0, 0, H + 0.25, 0.15)
    # a thick pale sill line across the head's two faces (the sign's shelf)
    for sy in (-1, 1):
        soft('plastic', TRIM, W + 2 * jamb + 0.4, 0.7, 0.7, 0, sy * (depth / 2 + 0.25), H + head - 0.2, 0.3, pick='x', segs=2, small=0.0)
    keep(name)

frame('tr_portal', 16.0, 14.0, 3.0, 3.0, 3.0, 6.0)
frame('tr_portalBig', 24.0, 16.0, 3.6, 3.4, 4.0, 6.0)

# ------------------------------------------------------------------ tr_parapet (an 8-long run; joins end to end)
soft('plastic', SLATE, 8.0, 2.2, 0.6, 0, 0, 0.3, 0.2, pick='x', segs=2, small=0.0)
soft('plastic', WALL2, 8.0, 1.6, 2.1, 0, 0, 0.6 + 1.05, 0.1, pick='x', segs=2, small=0.0)
soft('plastic', TRIM, 8.0, 2.5, 0.7, 0, 0, 2.6 + 0.35, 0.3, pick='x', segs=3, small=0.0)
keep('tr_parapet')

# ------------------------------------------------------------------ tr_post (front -Y: the plate faces the firing line)
soft('plastic', SLATE, 2.4, 2.4, 0.6, 0, 0, 0.3, 0.25, pick='up', segs=2, small=0.0)
soft('plastic', PIER, 1.8, 1.8, 5.4, 0, 0, 0.6 + 2.7, 0.4, pick='up', segs=3, small=0.1)
bx('plastic', DEEP, 1.4, 0.3, 2.0, 0, -0.85, 4.3, 0.1)  # the sunk plate (its face 0.05 proud of the shaft)
soft('plastic', TRIM, 2.4, 2.4, 0.6, 0, 0, 6.0 + 0.3, 0.3, pick='all', segs=2, small=0.0)
keep('tr_post')

# ------------------------------------------------------------------ tr_tower (the gantry's: its cap carries the beam)
soft('plastic', DEEP, 8.8, 8.8, 1.0, 0, 0, 0.5, 0.3, pick='up', segs=2, small=0.0)
soft('plastic', PIER2, 8.0, 8.0, 14.0, 0, 0, 1.0 + 7.0, 1.2, pick='up', segs=3, small=0.15)
for zb in (5.5, 10.5):
    soft('plastic', TRIM, 8.5, 8.5, 0.7, 0, 0, zb, 1.3, pick='up', segs=3, small=0.12)
for a in range(4):
    M = RZ(a * math.pi / 2)
    for z0, z1 in ((1.6, 5.0), (6.0, 10.0), (11.0, 14.6)):
        bx('plastic', WALL2, 4.6, 0.4, z1 - z0, 0, -3.85, (z0 + z1) / 2, 0.12, M=M)
soft('plastic', TRIM, 8.8, 8.8, 1.2, 0, 0, 15.0 + 0.6, 0.5, pick='all', segs=2, small=0.0)
keep('tr_tower')

# ------------------------------------------------------------------ tr_crown (the TOP's arch, front -Y)
for sx in (-1, 1):
    soft('plastic', SLATE, 4.8, 4.8, 1.2, sx * 10.0, 0, 0.6, 0.3, pick='up', segs=2, small=0.0)
    soft('plastic', PIER, 4.0, 4.0, 13.0, sx * 10.0, 0, 1.2 + 6.5, 0.6, pick='up', segs=3, small=0.12)
soft('plastic', PIER2, 24.0, 4.0, 3.6, 0, 0, 14.2 + 1.8, 0.7, pick='x', segs=3, small=0.1)
soft('plastic', TRIM, 24.6, 4.6, 0.7, 0, 0, 17.8 + 0.35, 0.3, pick='all', segs=2, small=0.0)
bx('neon', AMBER, 15.6, 3.0, 0.3, 0, 0, 14.1, 0.1)  # under the lintel, between the legs: where you finish
keep('tr_crown')

# ------------------------------------------------------------------ tr_desk (the screen and lights are the builder's)
soft('plastic', DEEP, 7.6, 2.4, 0.5, 0, 0, 0.25, 0.2, pick='up', segs=2, small=0.0)
soft('plastic', SLATE, 7.2, 2.0, 2.2, 0, 0, 0.5 + 1.1, 0.35, pick='up', segs=3, small=0.1)
bx('plastic', PIER, 5.6, 0.3, 1.3, 0, -1.05, 1.5, 0.1)  # a sunk panel on its front
soft('plastic', PIER2, 8.4, 3.0, 0.35, 0, 0, 2.7 + 0.175, 0.15, pick='all', segs=2, small=0.0)
keep('tr_desk')

# ------------------------------------------------------------------ tr_projector (z 0 = the ceiling)
cy('plastic', PIER2, 5.0, 0.6, 0, 0, -0.3, segs=32, bevel=0.2)
lathe('plastic', TRIM, ring_prof(4.4, 0.6, 10), segs=40, cap=False, M=T(0, 0, -0.9))
cy('plastic', DEEP, 3.0, 0.5, 0, 0, -1.0, segs=32, bevel=0.15)
cy('neon', TEAL, 1.2, 0.2, 0, 0, -1.3, segs=24, bevel=0.05)
keep('tr_projector')

# ------------------------------------------------------------------ tr_lamp (front -Y; its back on the wall at y 0.55)
soft('plastic', PIER2, 3.2, 1.1, 4.2, 0, 0, 2.1, 0.35, pick='all', segs=2, small=0.0)
bx('neon', WHITE, 2.4, 0.25, 3.3, 0, -0.5, 2.1, 0.08)
keep('tr_lamp')

export_all('training_redo.glb')
if len(sys.argv) > sys.argv.index('--') + 2:
    preview(sys.argv[sys.argv.index('--') + 2], cols=5)
