# THE PENTHOUSE LOUNGE, THE CABANAS AND THE TRAINING TENT (structure pass, 15 Nov 2026). chunky style, the serious
# pass's palette. most pieces are made to FIT one of the map's own boxes (the box stays the collision, the model is
# what you see), so the cover in the arena's middle does not change. 1 unit = 1 stud, Z up, front = -Y.
#   ph_sofa       the upper floor's sofa, 16.2 x 5.15 x 3.0 (seat 3.6 deep, back cushions behind it)
#   ph_sofalow    the lower floor's sofa, 10.5 x 3.8 x 2.85 (back cushions on the seat's rear)
#   ph_bar        the bar, 18 x 6.2 x 3.5: a counter in front, a back bar with bottles
#   ph_stool      a bar stool, 1.5 x 1.5 x 2.7
#   ph_table      a standing table, 4.2 x 4.2 x 2.75
#   ph_cabinet    a drinks fridge, 3.6 x 3.3 x 5.4 (glass door in front, lit inside)
#   ph_planter    the long planter, 12 x 6.6 x 3.7 with low shrubs
#   ph_pot        a big pot with a broad-leaved plant, 2.6 x 2.6 x 6.4
#   ph_pooltable  a pool table, 9 x 5 x 3 (new: it stands on the map's centre line)
#   ph_coffee     a low table, 7 x 3.2 x 1.3 (new, one in front of each upper sofa)
#   ph_raft       a hanging light raft, 12 x 3 x 1.9 (the ceiling is at its top)
#   ph_ring       a ring light on three rods, 9.6 across x 2.4 (the ceiling is at its top)
#   rt_cabana     a cabana, 12.9 x 12.9 x 11.4: four posts, a sagging canvas roof with a scalloped edge, a gathered
#                 drape at each post, a lantern
#   rt_cabwall    one padded side of a cabana, 11.1 x 0.5 x 3.3
#   rt_daybed     a daybed, 7.2 x 3.6 x 1.9
#   tr_tent       the training hall's tent, 12 x 8.3 x 6.8: the cabana's frame and roof in plain canvas, a floor mat
# run: blender -b --factory-startup -P tools/roblox/lounge_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *

TRIM, CASE, MIDG, GRAPH, DARK, SLATE = 'c9c7c1', '9a9da3', '6a6e77', '4d515a', '34363d', '3e4048'
AMBER, WARM, GLASS, ROOM = 'd6a738', 'f2dcc0', '465a69', 'e8d2b0'
UPH, UPH2, BASE = '747882', '8b8f98', '4a4e57'           # upholstery, its lighter cushion, the plinth under it
CANVAS, CANVAS2, TIMBER = 'c9c5ba', 'a9a59b', '5b5d63'   # cabana cloth, its padded sides, the frame
LEAF, LEAF2, SOIL, FELT = '4f7044', '5f7a4c', '4a4038', '3f4f49'
reset()

def cushion(hexc, sx, sy, sz, x, y, z, r=0.32, rot=None):
    soft('fabric', hexc, sx, sy, sz, x, y, z, r, pick='all', segs=3, small=0.0, rot=rot)

# ------------------------------------------------------------------ ph_sofa (16.2 x 5.15 x 3.0)
def sofa(L, DP, seat_d, H, n, back_on_seat):
    # origin: middle of the footprint; the front (where you sit down) is -Y
    y0 = -DP / 2
    bx('plastic', BASE, L, DP, 0.5, 0, 0, 0.25, 0.14)
    arm = 1.0
    w = (L - 2 * arm) / n
    for i in range(n):
        x = -L / 2 + arm + w * (i + 0.5)
        cushion(UPH, w - 0.08, seat_d - 0.1, 0.95, x, y0 + seat_d / 2 + 0.05, 0.95)
        bd = DP - seat_d if not back_on_seat else 1.4
        by = DP / 2 - bd / 2
        cushion(UPH2 if i != n - 1 else UPH2, w - 0.12, bd - 0.1, H - 1.45, x, by, 1.42 + (H - 1.45) / 2, r=0.38)
    for s in (-1, 1):
        soft('fabric', UPH, arm, DP, 2.15, s * (L / 2 - arm / 2), 0, 1.075 + 0.02, 0.4, pick='top', segs=3)
    # one amber pillow, one pale
    px = -L / 2 + arm + w * 0.5
    cushion(AMBER, 1.7, 0.7, 1.5, px, y0 + seat_d - 0.75, 2.05, r=0.3, rot=RZ(D(8)))
    cushion(TRIM, 1.6, 0.7, 1.4, L / 2 - arm - w * 0.45, y0 + seat_d - 0.75, 2.0, r=0.3, rot=RZ(D(-6)))

sofa(16.2, 5.15, 3.6, 3.0, 3, False)
keep('ph_sofa')
sofa(10.5, 3.8, 3.8, 2.85, 2, True)
keep('ph_sofalow')

# ------------------------------------------------------------------ ph_bar (18 x 6.2 x 3.5), front -Y
soft('plastic', GRAPH, 18.0, 1.7, 3.1, 0, -2.25, 1.55, 0.3, pick='up')
for i in range(9):
    soft('plastic', SLATE, 1.2, 0.35, 2.3, -8.0 + i * 2.0, -3.12, 1.55, 0.17, pick='up', segs=2)
bx('plastic', AMBER, 17.6, 0.2, 0.5, 0, -3.14, 0.3, 0.06)
soft('plastic', TRIM, 18.0, 2.5, 0.38, 0, -1.9, 3.3, 0.18, pick='up')
bx('plastic', DARK, 18.0, 2.2, 0.2, 0, 0.4, 0.1, 0.05)                           # the floor behind the counter
soft('plastic', SLATE, 18.0, 1.5, 3.3, 0, 2.35, 1.65, 0.25, pick='up')           # back bar
bx('plastic', TRIM, 17.4, 1.2, 0.2, 0, 2.2, 3.35, 0.06)
bottle_cols = ('6f8a78', '8a6c5e', 'c9c7c1', '556070', 'b89c46')   # (the fridge's small bottles)
soft('plastic', SLATE, 17.6, 0.36, 2.9, 0, 3.0, 4.95, 0.12, pick='y')
bx('neon', 'd9c4a0', 16.6, 0.14, 2.1, 0, 2.8, 4.95, 0.04)
for i, (c, h, r) in enumerate((('c9c7c1', 1.7, 0.44), ('8b8f98', 1.35, 0.5), (AMBER, 1.9, 0.4), ('6a6e77', 1.5, 0.48), ('c9c7c1', 1.25, 0.52))):
    x = -6.4 + i * 3.2
    cy('plastic', c, r, h, x, 2.15, 3.45 + h / 2, segs=12, bevel=0.12)
    cy('plastic', c, r * 0.4, 0.5, x, 2.15, 3.45 + h + 0.22, segs=8, bevel=0.05)
bx('neon', WARM, 17.0, 0.16, 0.16, 0, 1.55, 3.3, 0.04)                           # a strip of light under the bottles
keep('ph_bar')

# ------------------------------------------------------------------ ph_stool (1.5 x 1.5 x 2.7)
cy('plastic', GRAPH, 0.72, 0.16, 0, 0, 0.08, segs=16, bevel=0.05)
cy('plastic', GRAPH, 0.2, 2.0, 0, 0, 1.1, segs=10, bevel=0.03)
lathe('plastic', AMBER, ring_prof(0.55, 0.09, 8), T(0, 0, 0.85), segs=16, cap=False)
lathe('fabric', UPH, [(0.0, 0.0), (0.6, 0.0), (0.74, 0.12), (0.75, 0.38), (0.66, 0.54), (0.4, 0.6), (0.0, 0.6)], T(0, 0, 2.1), segs=16)
keep('ph_stool')

# ------------------------------------------------------------------ ph_table (4.2 x 4.2 x 2.75)
cy('plastic', GRAPH, 1.75, 0.3, 0, 0, 0.15, segs=20, bevel=0.1)
cy('plastic', GRAPH, 1.3, 2.1, 0, 0, 1.3, segs=20, bevel=0.12, r2=1.05)
soft('plastic', TRIM, 4.2, 4.2, 0.42, 0, 0, 2.54, 0.8, pick='up', segs=4)
keep('ph_table')

# ------------------------------------------------------------------ ph_cabinet (3.6 x 3.3 x 5.4)
soft('plastic', GRAPH, 3.6, 3.3, 5.4, 0, 0, 2.7, 0.3, pick='up')
bx('neon', ROOM, 2.8, 0.2, 4.2, 0, -1.5, 2.95, 0.03)
for z in (1.7, 2.95, 4.2): bx('plastic', DARK, 2.8, 0.5, 0.14, 0, -1.42, z, 0.03)
for i in range(4):
    for z in (1.78, 3.03, 4.28):
        cy('plastic', bottle_cols[(i + int(z)) % 5], 0.22, 0.75, -1.05 + i * 0.7, -1.5, z + 0.4, segs=8, bevel=0.05)
bx('glass', GLASS, 2.9, 0.12, 4.4, 0, -1.68, 2.95, 0.03)
bx('plastic', TRIM, 0.16, 0.22, 2.4, 1.2, -1.76, 2.95, 0.05)
bx('plastic', DARK, 3.4, 0.2, 0.5, 0, -1.6, 0.35, 0.05)
keep('ph_cabinet')

# ------------------------------------------------------------------ ph_planter (12 x 6.6 x 3.7)
soft('concrete', '8b8d93', 12.0, 6.6, 2.5, 0, 0, 1.25, 0.5, pick='up')
soft('plastic', TRIM, 12.2, 6.8, 0.36, 0, 0, 2.5, 0.5, pick='up')
bx('plastic', SOIL, 11.0, 5.6, 0.2, 0, 0, 2.6, 0.05)
shrubs = [(-4.0, 0.3, 1.55, LEAF), (-1.2, -0.5, 1.25, LEAF2), (1.6, 0.5, 1.6, LEAF), (4.2, -0.2, 1.35, LEAF2), (-2.8, 1.3, 1.0, LEAF2), (3.0, -1.4, 0.95, LEAF)]
for x, y, r, c in shrubs: ball('plastic', c, r, x, y, 2.55 + r * 0.42, sc=(1.25, 1.15, 0.62))
keep('ph_planter')

# ------------------------------------------------------------------ ph_pot (2.6 x 2.6 x 6.4)
lathe('plastic', '8b8d93', [(0.0, 0.0), (0.85, 0.0), (1.2, 0.9), (1.25, 2.1), (1.1, 2.4), (0.95, 2.4), (0.95, 2.15), (0.0, 2.15)], I4, segs=16)
cy('plastic', SOIL, 0.94, 0.1, 0, 0, 2.2, segs=16, bevel=0.02)
cy('plastic', '6b5a48', 0.2, 2.2, 0, 0, 3.3, segs=8, bevel=0.03)
for i, (a, tilt, zz, s) in enumerate([(0, 38, 4.3, 1.0), (120, 46, 4.0, 0.9), (240, 34, 4.7, 1.05), (60, 20, 5.3, 0.85), (200, 52, 3.6, 0.8)]):
    M = RZ(D(a)) @ T(0.15, 0, zz) @ RY(D(-tilt))
    ball('plastic', LEAF if i % 2 == 0 else LEAF2, 1.0, 0.95 * s, 0, 0, M=M, sc=(1.05 * s, 0.62 * s, 0.1))
keep('ph_pot')

# ------------------------------------------------------------------ ph_pooltable (9 x 5 x 3)
for sx in (-3.3, 3.3):
    soft('plastic', GRAPH, 1.3, 3.6, 2.0, sx, 0, 1.0, 0.3, pick='up')
soft('plastic', GRAPH, 9.0, 5.0, 0.9, 0, 0, 2.35, 0.45, pick='up', segs=3)
soft('plastic', TRIM, 9.0, 5.0, 0.26, 0, 0, 2.87, 0.45, pick='up', segs=3)
bx('fabric', FELT, 7.9, 3.9, 0.3, 0, 0, 2.9, 0.04)
for x in (-3.95, 0, 3.95):
    for y in (-1.95, 1.95): cy('plastic', DARK, 0.3, 0.32, x, y, 2.9, segs=10, bevel=0.02)
k = 0
for row in range(3):
    for j in range(row + 1):
        ball('plastic', AMBER if k == 2 else TRIM, 0.21, 1.6 + row * 0.38, (j - row / 2) * 0.44, 3.26, sub=1)
        k += 1
ball('plastic', TRIM, 0.21, -2.2, 0.3, 3.26, sub=1)
keep('ph_pooltable')

# ------------------------------------------------------------------ ph_coffee (7 x 3.2 x 1.3)
for sx in (-2.3, 2.3): soft('plastic', GRAPH, 1.0, 2.4, 0.95, sx, 0, 0.475, 0.25, pick='up')
soft('plastic', TRIM, 7.0, 3.2, 0.36, 0, 0, 1.12, 0.6, pick='up', segs=4)
keep('ph_coffee')

# ------------------------------------------------------------------ ph_raft (12 x 3 x 1.9): the ceiling is at z 0, it hangs down
for sx in (-4.2, 4.2): bx('plastic', DARK, 0.3, 0.3, 1.4, sx, 0, -0.7, 0.06)
soft('plastic', DARK, 12.0, 3.0, 0.5, 0, 0, -1.6, 0.22, pick='up')
bx('neon', WARM, 11.2, 2.3, 0.14, 0, 0, -1.87, 0.04)
keep('ph_raft')

# ------------------------------------------------------------------ ph_ring (9.6 across): the ceiling is at z 0
for a in (90, 210, 330):
    bx('plastic', DARK, 0.26, 0.26, 2.0, 4.45 * math.cos(D(a)), 4.45 * math.sin(D(a)), -1.0, 0.05)
lathe('plastic', DARK, ring_prof(4.45, 0.36, 10), T(0, 0, -2.05), segs=40, cap=False)
lathe('neon', WARM, [(4.2, 0.0), (4.7, 0.0), (4.7, 0.1), (4.2, 0.1), (4.2, 0.0)], T(0, 0, -2.47), segs=40, cap=False)
keep('ph_ring')

# ------------------------------------------------------------------ rt_cabana (12.9 x 12.9 x 11.4)
def canopy(side_x, side_y, z0, rise, cloth, sag=0.5):
    """a sagging square tent roof standing on z0 (lathe with four sides, stretched to side_x by side_y)"""
    R = side_x / math.sqrt(2)
    prof = [(R, 0.0), (R, 0.3)]
    for i in range(1, 7):
        t = i / 6
        prof.append((R * (1 - t) + 0.02, 0.3 + rise * (t ** (1 + sag))))
    prof.append((0.0, 0.3 + rise + 0.05))
    lathe('fabric', cloth, prof, T(0, 0, z0) @ Matrix.Diagonal((1, side_y / side_x, 1, 1)) @ RZ(D(45)), segs=4, bevel=0.0)

def tent_frame(hx, hy, post_h, frame, post=0.9):
    for sx in (-1, 1):
        for sy in (-1, 1):
            soft('plastic', frame, post, post, post_h, sx * hx, sy * hy, post_h / 2, 0.2, pick='up')
            bx('plastic', frame, post + 0.5, post + 0.5, 0.4, sx * hx, sy * hy, 0.2, 0.1)
    for sy in (-1, 1): bx('plastic', frame, 2 * hx + post, 0.7, 0.7, 0, sy * hy, post_h - 0.35, 0.14)
    for sx in (-1, 1): bx('plastic', frame, 0.7, 2 * hy + post, 0.7, sx * hx, 0, post_h - 0.35, 0.14)

def scallops(hx, hy, z, cloth, n_x=0, n_y=0, drop=1.3):
    """the roof's hanging edge: one plain band of cloth on each side, its edges rounded"""
    for s_ in (-1, 1):
        soft('fabric', cloth, 2 * hx + 1.5, 0.3, drop, 0, s_ * (hy + 0.6), z - drop / 2 + 0.35, 0.14, pick='all', segs=2, small=0.0)
        soft('fabric', cloth, 0.3, 2 * hy + 1.5, drop, s_ * (hx + 0.6), 0, z - drop / 2 + 0.35, 0.14, pick='all', segs=2, small=0.0)

tent_frame(6.0, 6.0, 8.4, TIMBER)
canopy(13.5, 13.5, 8.35, 4.4, CANVAS, sag=0.7)
scallops(6.0, 6.0, 8.0, CANVAS)
drape = [(0.0, 0.25), (0.6, 0.25), (0.82, 0.7), (0.66, 2.2), (0.36, 3.5), (0.34, 3.9), (0.62, 5.2), (0.88, 7.3), (0.92, 7.75), (0.0, 7.75)]
for sx in (-1, 1):
    for sy in (-1, 1):
        lathe('fabric', CANVAS, drape, T(sx * 5.05, sy * 5.05, 0), segs=10)
        cy('plastic', AMBER, 0.42, 0.3, sx * 5.05, sy * 5.05, 3.7, segs=10, bevel=0.08)
cy('plastic', TIMBER, 0.14, 2.4, 0, 0, 10.1, segs=6, bevel=0.02)
ball('neon', ROOM, 0.75, 0, 0, 8.55, sc=(1, 1, 0.9))
cy('plastic', TIMBER, 0.4, 0.22, 0, 0, 9.22, segs=10, bevel=0.05)
keep('rt_cabana')

# ------------------------------------------------------------------ rt_cabwall (11.1 x 0.5 x 3.3)
bx('plastic', TIMBER, 11.1, 0.3, 0.35, 0, 0, 0.175, 0.06)
for i in (-1, 0, 1): cushion('858990', 3.55, 0.5, 2.9, i * 3.7, 0, 1.8, r=0.2)
keep('rt_cabwall')

# ------------------------------------------------------------------ rt_daybed (7.2 x 3.6 x 1.9)
soft('plastic', TIMBER, 7.2, 3.6, 0.6, 0, 0, 0.3, 0.2, pick='up')
cushion('8b8f98', 7.0, 3.4, 0.85, 0, 0, 1.02, r=0.3)
cy('fabric', '747882', 0.45, 3.1, -3.0, 0, 1.75, axis='y', segs=12, bevel=0.15)
cushion(AMBER, 1.5, 1.5, 0.5, -1.7, 0.6, 1.62, r=0.2, rot=RZ(D(12)))
cushion(TRIM, 1.5, 1.5, 0.5, -1.6, -0.8, 1.6, r=0.2, rot=RZ(D(-10)))
keep('rt_daybed')

# ------------------------------------------------------------------ tr_tent (12 x 8.3 x 6.8): mid greys (the hall's lamps light paint to about twice its value)
TCAN, TFRAME, TMAT = '8f9196', '4b505b', '3a3d47'
tent_frame(5.5, 3.65, 4.6, TFRAME, post=0.7)
canopy(12.4, 8.7, 4.55, 2.9, TCAN, sag=0.6)
scallops(5.5, 3.65, 4.25, TCAN, n_x=9, n_y=6)
bx('plastic', TMAT, 10.6, 6.9, 0.14, 0, 0, 0.07, 0.04)
bx('plastic', AMBER, 10.6, 0.3, 0.16, 0, -3.3, 0.08, 0.03)
bx('plastic', AMBER, 10.6, 0.3, 0.16, 0, 3.3, 0.08, 0.03)
for sx in (-1.6, 1.6): soft('plastic', TFRAME, 0.9, 2.0, 2.2, -1.2 + sx, 0.6, 1.24, 0.25, pick='up')
soft('plastic', 'a9abaf', 5.6, 2.8, 0.36, -1.2, 0.6, 2.5, 0.5, pick='up', segs=3)
soft('plastic', '5e6168', 2.4, 1.8, 1.5, 3.2, -1.2, 0.89, 0.25, pick='all')
soft('plastic', '6c7078', 1.9, 1.5, 1.1, 3.3, -1.1, 2.19, 0.22, pick='all')
bx('plastic', AMBER, 0.5, 0.2, 0.4, 3.2, -2.12, 1.1, 0.05)
bx('plastic', AMBER, 0.45, 0.2, 0.36, 3.3, -1.87, 2.3, 0.05)
keep('tr_tent')

# ------------------------------------------------------------------ round 2 (after the first judging)
# ph_tub: a tub chair, 2.9 x 2.9 x 2.7 (you sit facing -Y)
cy('plastic', BASE, 1.2, 0.5, 0, 0, 0.25, segs=18, bevel=0.1)
lathe('fabric', UPH, [(0.0, 0.5), (1.3, 0.5), (1.42, 0.7), (1.42, 1.25), (1.25, 1.45), (0.0, 1.45)], I4, segs=18)
lathe('fabric', UPH2, [(0.0, 1.4), (1.02, 1.4), (1.1, 1.55), (1.0, 1.75), (0.0, 1.8)], T(0, -0.1, 0), segs=18)
for (x, y, sx, sy, h) in ((0, 1.08, 2.5, 0.7, 1.5), (-1.08, 0.2, 0.7, 2.0, 1.15), (1.08, 0.2, 0.7, 2.0, 1.15)):
    soft('fabric', UPH, sx, sy, h, x, y, 1.3 + h / 2, 0.3, pick='all', segs=3, small=0.0)
keep('ph_tub')

# ph_console: a long low sideboard, 16.2 x 2.4 x 3.4 with its lamp (front -Y)
bx('plastic', DARK, 15.4, 1.8, 0.3, 0, 0, 0.15, 0.05)
soft('plastic', GRAPH, 16.0, 2.2, 1.8, 0, 0, 1.2, 0.25, pick='up')
for i in range(4): bx('plastic', SLATE, 3.5, 0.14, 1.3, -5.7 + i * 3.8, -1.1, 1.2, 0.06)
soft('plastic', TRIM, 16.2, 2.4, 0.3, 0, 0, 2.25, 0.3, pick='up')
cy('plastic', GRAPH, 0.5, 0.2, -6.3, 0, 2.5, segs=14, bevel=0.05)
cy('plastic', GRAPH, 0.14, 0.5, -6.3, 0, 2.8, segs=8, bevel=0.03)
lathe('neon', 'e6cfa8', dome_prof(0.6, 0.55, rim=0.25, steps=5), T(-6.3, 0, 2.95), segs=16)
lathe('plastic', '8b8d93', [(0.0, 0.0), (0.55, 0.0), (0.95, 0.5), (1.0, 0.75), (0.9, 0.75), (0.0, 0.3)], T(4.6, 0.1, 2.4), segs=16)
soft('plastic', UPH2, 2.2, 1.5, 0.3, 0.6, 0.1, 2.55, 0.1, pick='up')
soft('plastic', AMBER, 1.9, 1.3, 0.26, 0.5, 0.05, 2.83, 0.1, pick='up')
keep('ph_console')

export_all('lounge.glb')
argv = sys.argv[sys.argv.index('--') + 1:]
if len(argv) > 2: MODELS[:] = [m for m in MODELS if m[0] in argv[2].split(',')]
if len(argv) > 1: preview(argv[1], cols=6)
