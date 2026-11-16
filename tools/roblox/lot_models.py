# THE BACK LOT KIT (16 Nov 2026): the shaped pieces of the training area's secret outdoor grounds, behind the garage
# door at the end of the dummy yard (studio-tools/TrainingLot.luau builds the grounds out of plain parts and places
# these). the same rules as the training v2 kit: few big rounded pieces, flat matte colours, the quiet family (concrete,
# mid greys, off-white), amber as the one accent. a piece whose colour is a stand-in (CONT, DRUM) is painted per copy.
# 1 unit = 1 stud, Z up, a model's front faces -Y (Roblox +Z after the import), the floor is z 0 unless said.
#   tl_container    a shipping container, 20 x 8 x 8.6 (long along X, doors at +X)
#   tl_barrier      a concrete road barrier, 10 long (X) x 2.6 x 3.6
#   tl_treeRound    a round tree, about 12 across and 17 tall
#   tl_treeCone     a cone tree, about 10 across and 19 tall
#   tl_bollard      a concrete post with an amber band, 1.4 x 3.4
#   tl_drum         an oil drum, 2.8 x 4.3
#   tl_crate        a wooden crate, 4 x 4 x 4
#   tl_tyres        three tyres stacked, 5.3 across, 4.5 tall
#   tl_roller       the garage door's roller box, 30 long (X), 4.4 x 4.4 (z 0 = its underside)
#   tl_beacon       an amber turning beacon, 2.4 x 2.7
#   tl_garageFrame  the garage door's portal through a 4-thick wall: 24 wide x 16.5 high inside, 6.4 deep
#   tl_portal       the outer opening of the loading bay: 36 wide x 22 high inside, 6 deep
#   tl_mast         a grapple mast, 40 tall, an amber hoop on top facing -Y
#   tl_flood        a yard floodlight on a pole, 30 tall, the lamp facing -Y
#   tl_tower        the watchtower on the hill: 14 x 14, deck at z 18, roof to z 31
# run: blender -b --factory-startup -P tools/roblox/lot_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *
from structkit import _emit

PIER, PIER2, TRIM, SLATE = '8f9299', '7d8088', 'e2ded5', '5f646e'
CONC, CONC2, AMBER, WHITE, TAN, TAN2 = 'c9c4ba', 'b3aea5', 'f0a53a', 'f4f6f8', 'b49a7a', '9c8466'
GREEN, GREEN2, BARK, TYRE = '7f8f70', '6e7f62', '7a6c5e', '50545b'
CONT, DRUM = 'a0a8b2', 'a88a6a'  # stand-ins, painted per copy
reset()
RX = lambda a: Matrix.Rotation(a, 4, 'X')

# ------------------------------------------------------------------ tl_container (20 x 8 x 8.6, doors at +X)
soft('plastic', CONT, 19.2, 7.4, 7.8, 0, 0, 0.4 + 3.9, 0.35, pick='all', segs=2, small=0.0)
for i in range(6):  # big vertical ribs on both long faces
    x = -7.5 + 3.0 * i
    for sy in (-1, 1):
        soft('plastic', CONT, 1.1, 0.5, 7.0, x, sy * 3.8, 4.3, 0.2, pick='all', segs=2, small=0.0)
for sx in (-1, 1):  # corner posts and the rails between them
    for sy in (-1, 1):
        soft('plastic', SLATE, 1.0, 1.0, 8.6, sx * 9.6, sy * 3.6, 4.3, 0.25, pick='up', segs=2, small=0.08)
    for z in (0.45, 8.15):
        bx('plastic', SLATE, 1.0, 7.4, 0.9, sx * 9.6, 0, z, 0.15)
for sy in (-1, 1):
    for z in (0.45, 8.15):
        bx('plastic', SLATE, 19.2, 1.0, 0.9, 0, sy * 3.6, z, 0.15)
for y in (-2.9, -1.1, 1.1, 2.9):  # the door end: four lock bars
    cy('plastic', SLATE, 0.2, 6.6, 9.85, y, 4.3, segs=10, bevel=0.06)
bx('plastic', SLATE, 0.2, 0.25, 7.0, 9.9, 0, 4.3, 0.05)  # the doors' meeting line
keep('tl_container')

# ------------------------------------------------------------------ tl_barrier (10 long along X)
prof = [(-1.3, 0.0), (1.3, 0.0), (1.3, 0.55), (0.75, 1.3), (0.5, 3.6), (-0.5, 3.6), (-0.75, 1.3), (-1.3, 0.55)]
prism('plastic', CONC, prof, 10.0, M=RZ(math.pi / 2), bevel=0.22, segs=2)
bx('plastic', SLATE, 10.05, 2.0, 0.35, 0, 0, 0.17, 0.05)
keep('tl_barrier')

# ------------------------------------------------------------------ trees
cy('plastic', BARK, 0.95, 8.0, 0, 0, 4.0, segs=12, bevel=0.2, r2=0.7)
ball('plastic', GREEN, 5.4, 0, 0, 11.0, sc=(1, 1, 0.82), sub=2)
ball('plastic', GREEN2, 4.0, 2.6, 1.2, 13.4, sc=(1, 1, 0.85), sub=2)
ball('plastic', GREEN, 3.6, -2.6, -1.4, 13.0, sc=(1, 1, 0.85), sub=2)
keep('tl_treeRound')
cy('plastic', BARK, 0.8, 6.0, 0, 0, 3.0, segs=12, bevel=0.2, r2=0.6)
cy('plastic', GREEN2, 5.2, 7.5, 0, 0, 7.8, segs=14, bevel=0.5, r2=1.6)
cy('plastic', GREEN, 4.2, 6.5, 0, 0, 12.0, segs=14, bevel=0.5, r2=1.0)
cy('plastic', GREEN2, 3.0, 5.0, 0, 0, 16.2, segs=14, bevel=0.5, r2=0.3)
keep('tl_treeCone')

# ------------------------------------------------------------------ small things
cy('plastic', CONC2, 0.7, 3.0, 0, 0, 1.5, segs=16, bevel=0.15)
cy('plastic', AMBER, 0.74, 0.5, 0, 0, 2.3, segs=16, bevel=0.08)
lathe('plastic', CONC2, dome_prof(0.7, 0.4, steps=4), M=T(0, 0, 3.0), segs=16)
keep('tl_bollard')

cy('plastic', DRUM, 1.4, 4.2, 0, 0, 2.1, segs=24, bevel=0.15)
for z in (1.4, 2.8):
    lathe('plastic', DRUM, ring_prof(1.4, 0.13, 8), M=T(0, 0, z), segs=24, cap=False)
cy('plastic', SLATE, 1.25, 0.12, 0, 0, 4.24, segs=24, bevel=0.03)
keep('tl_drum')

soft('plastic', TAN, 3.8, 3.8, 3.8, 0, 0, 2.0, 0.25, pick='all', segs=2, small=0.0)
for sx in (-1, 1):
    for sy in (-1, 1):
        bx('plastic', TAN2, 0.6, 0.6, 4.0, sx * 1.75, sy * 1.75, 2.0, 0.12)
    for z in (0.3, 3.7):
        bx('plastic', TAN2, 0.6, 4.0, 0.6, sx * 1.75, 0, z, 0.12)
for sy in (-1, 1):
    for z in (0.3, 3.7):
        bx('plastic', TAN2, 4.0, 0.6, 0.6, 0, sy * 1.75, z, 0.12)
keep('tl_crate')

for k in range(3):
    lathe('plastic', TYRE, ring_prof(1.9, 0.75, 12), M=T(0, 0, 0.75 + 1.5 * k), segs=24, cap=False)
keep('tl_tyres')

# ------------------------------------------------------------------ the garage door's roller box and its beacon
soft('plastic', PIER2, 29.0, 4.4, 4.4, 0, 0, 2.2, 1.9, pick='x', segs=3, small=0.1)
for sx in (-1, 1):
    cy('plastic', TRIM, 2.55, 1.0, sx * 14.9, 0, 2.2, axis='x', segs=28, bevel=0.25)
    cy('plastic', SLATE, 1.0, 1.2, sx * 15.0, 0, 2.2, axis='x', segs=16, bevel=0.15)
bx('plastic', SLATE, 28.0, 0.3, 0.6, 0, -2.15, 0.6, 0.05)
keep('tl_roller')

cy('plastic', SLATE, 1.2, 0.6, 0, 0, 0.3, segs=20, bevel=0.15)
cy('plastic', SLATE, 0.6, 1.7, 0, 0, 1.45, segs=16, bevel=0.1)
for sx in (-1, 1):
    soft('neon', AMBER, 0.7, 1.3, 1.3, sx * 0.75, 0, 1.45, 0.3, pick='all', segs=2, small=0.0)
lathe('plastic', SLATE, dome_prof(1.0, 0.45, steps=4), M=T(0, 0, 2.25), segs=20)
keep('tl_beacon')

# ------------------------------------------------------------------ frames: an inverted U with cut top corners
def frame(name, W, H, jamb, head, cut, depth, col, guides=False):
    pts = [(-W / 2 - jamb, 0.0), (-W / 2 - jamb, H + head), (W / 2 + jamb, H + head), (W / 2 + jamb, 0.0),
           (W / 2, 0.0), (W / 2, H - cut), (W / 2 - cut, H), (-W / 2 + cut, H), (-W / 2, H - cut), (-W / 2, 0.0)]
    prism('plastic', col, pts, depth, bevel=0.4, segs=2)
    for sx in (-1, 1):  # a slate foot on each jamb
        bx('plastic', SLATE, jamb + 0.4, depth + 0.4, 1.6, sx * (W / 2 + jamb / 2), 0, 0.8, 0.15)
        if guides:  # the channels the door runs in
            bx('plastic', SLATE, 1.0, 1.6, H - cut, sx * (W / 2 - 0.3), 0, (H - cut) / 2, 0.12)
    bx('plastic', TRIM, W - 2 * cut + 0.3, depth + 0.15, 0.6, 0, 0, H + 0.3, 0.15)
    keep(name)

frame('tl_garageFrame', 24.0, 16.5, 3.0, 3.5, 1.6, 6.4, PIER, guides=True)
frame('tl_portal', 36.0, 22.0, 4.0, 5.0, 3.0, 6.0, PIER2)

# ------------------------------------------------------------------ tl_mast: 40 tall, an amber hoop on top facing -Y
soft('plastic', SLATE, 4.4, 4.4, 1.4, 0, 0, 0.7, 0.5, pick='all', segs=2, small=0.0)
cy('plastic', PIER, 0.85, 34.0, 0, 0, 1.4 + 17.0, segs=16, bevel=0.2)
for z in (12.0, 24.0):
    cy('plastic', TRIM, 1.05, 0.8, 0, 0, z, segs=16, bevel=0.2)
cy('plastic', SLATE, 1.2, 1.4, 0, 0, 35.6, segs=16, bevel=0.25)
lathe('plastic', AMBER, ring_prof(2.6, 0.6, 10), M=T(0, 0, 38.4) @ RX(math.pi / 2), segs=36, cap=False)
bx('plastic', SLATE, 0.7, 0.7, 1.8, 0, 0, 36.0 + 0.6, 0.1)
keep('tl_mast')

# ------------------------------------------------------------------ tl_flood: a floodlight on a pole, 30 tall
soft('plastic', SLATE, 2.6, 2.6, 1.0, 0, 0, 0.5, 0.4, pick='all', segs=2, small=0.0)
cy('plastic', PIER, 0.55, 28.0, 0, 0, 15.0, segs=14, bevel=0.15)
soft('plastic', SLATE, 4.6, 1.6, 2.6, 0, -0.6, 29.0, 0.5, pick='all', segs=2, small=0.0, rot=RX(math.radians(-20)))
bx('neon', WHITE, 3.8, 0.2, 1.8, 0, -1.45, 28.7, 0.05, rot=RX(math.radians(-20)))
keep('tl_flood')

# ------------------------------------------------------------------ tl_tower: the hill's watchtower
for sx in (-1, 1):
    for sy in (-1, 1):
        soft('plastic', SLATE, 1.8, 1.8, 18.0, sx * 5.6, sy * 5.6, 9.0, 0.5, pick='up', segs=2, small=0.1)
for a in range(4):  # a brace ring halfway up
    bx('plastic', PIER2, 12.6, 0.9, 0.9, 0, -5.6, 9.0, 0.2, M=RZ(a * math.pi / 2))
soft('plastic', PIER2, 15.0, 15.0, 1.4, 0, 0, 18.7, 0.5, pick='all', segs=2, small=0.0)
for a in range(4):  # half walls on three sides (the -Y side open for the way up)
    if a == 0: continue
    soft('plastic', CONC, 15.0, 0.9, 3.4, 0, -7.0, 19.4 + 1.7, 0.3, pick='all', segs=2, small=0.0, M=RZ(a * math.pi / 2))
for sx in (-1, 1):
    for sy in (-1, 1):
        cy('plastic', PIER, 0.45, 8.0, sx * 6.9, sy * 6.9, 23.4, segs=12, bevel=0.1)
soft('plastic', PIER2, 17.0, 17.0, 1.4, 0, 0, 28.1, 0.6, pick='all', segs=2, small=0.0)
soft('plastic', TRIM, 17.4, 17.4, 0.5, 0, 0, 27.3, 0.25, pick='all', segs=2, small=0.0)
bx('neon', AMBER, 15.4, 15.4, 0.3, 0, 0, 27.0, 0.05)
keep('tl_tower')

# ------------------------------------------------------------------ tl_ball: a smooth unit sphere (diameter 2, centred on z 0), for
# the near ridge's long ellipsoids (a MeshPart sized per lump). Roblox's own sphere mesh shows straight facets against
# the sky at 600 studs (judge round 2); this one has 64 sides. colour stand-in, painted per lump
def _uvsphere(bm, segs=64, rings=32):
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
_bm = bmesh.new()
_uvsphere(_bm)
_emit('plastic_' + CONT, _bm, I4)
keep('tl_ball')

# ------------------------------------------------------------------ tl_cylinder: a smooth 64-sided unit cylinder (diameter 2, height 1, centred),
# sized per use as the hill's tiers (Roblox's own cylinder shows straight facets at 100 studs across, judge round 3)
cy('plastic', CONT, 1.0, 1.0, 0, 0, 0, segs=64, bevel=0.0)
keep('tl_cylinder')

# ------------------------------------------------------------------ tl_bank: the hill's grass bank, a truncated cone 140 across at
# the foot and 104 at the top, 8 high, its top edge rounded (judge round 3: three drums on flat grass read as a cake stand)
_prof = [(0.0, 0.0), (70.0, 0.0), (62.0, 3.3), (55.2, 6.1), (54.0, 6.9), (53.0, 7.5), (52.2, 7.9), (51.5, 8.0), (0.0, 8.0)]
lathe('plastic', 'a0a8b2', _prof, segs=96, cap=False)
keep('tl_bank')

export_all('training_lot.glb')
if len(sys.argv) > sys.argv.index('--') + 2:
    preview(sys.argv[sys.argv.index('--') + 2], cols=5)
