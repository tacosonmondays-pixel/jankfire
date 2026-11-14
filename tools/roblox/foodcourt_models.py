# THE FOOD COURT kit for Roblox in the chunky style (see chunky.py): a mall food court used as the game's lobby.
# few big shapes, every sharp edge rounded off, flat colours. 1 unit = 1 stud, Z up, the front faces -Y, the floor at
# z 0, each model centred on x 0, y 0. "colour key" = a hex used for that one piece only: it is recoloured per copy.
#   fc_stall     a food stall 26 x 9 x 14: counter, back wall, two cheeks, a striped awning (colour key ff4fd8),
#                a dark sign plate under a lit strip, three menu panels, trays and two giant sauce bottles
#   fc_table     a round table (top surface z 3.2, colour key ffe14d) on one fat foot, four stools 4.6 out
#   fc_tree      a square planter 7 x 7 x 2.6, a fat trunk and a canopy of four blobs, 16 tall
#   fc_duck      the centrepiece: a giant rubber duck (beak toward -Y) in a round fountain basin of radius 11, 13 tall
#   fc_skytruss  a 60-long skylight truss (z 2.4 .. 5.4), a knee brace at each end, three round lamps hanging to z 0
#   fc_wetfloor  a comically large wet-floor A-sign 3 x 2.6 x 4.4 with a slipping figure on both faces
#   fc_bin       a tray-return bin 3 x 3 x 5: swing flap, pink band, trays on top
# run: blender -b --factory-startup -P tools/roblox/foodcourt_models.py -- <out_dir>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chunky import *
from chunky import _emit, _bevel

PALE, MID, LENS, WARM, TILE = 'a4aab8', '5b6478', 'f4f8ff', 'ffe9b8', 'e8ecf4'
LEAF, LEAF2, ORANGE, SOIL, RED = '4f9a3a', '6fbf4a', 'ff9a1f', '4a3424', 'e23b3b'
RZ = lambda a: Matrix.Rotation(a, 4, 'Z')
T = lambda x, y, z: Matrix.Translation((x, y, z))

def boxm(kind, hexc, sx, sy, sz, mat, bevel=0.2):
    """a box placed by a whole matrix"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    _bevel(bm, min(bevel, min(sx, sy, sz) * 0.42))
    _emit(kind + '_' + hexc, bm, mat)

def cylm(kind, hexc, r, depth, mat, segs=18, bevel=0.15, r2=None):
    """a cylinder (or cone: r at the bottom, r2 at the top) placed by a whole matrix"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    _bevel(bm, min(bevel, depth * 0.42, r * 0.42))
    _emit(kind + '_' + hexc, bm, mat)

def blob(kind, hexc, rx, ry, rz, x, y, z, sub=2, rot=None):
    """a rounded blob: an icosphere squashed to the three radii"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    _emit(kind + '_' + hexc, bm, T(x, y, z) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((rx, ry, rz, 1.0)))

def ring(kind, hexc, r_in, r_out, z0, z1, segs=18, bevel=0.2, phase=0.0, mat=None):
    """a flat-topped ring; phase turns it (radians): with 18 sides, phase 10 degrees puts a flat toward -Y"""
    bm = bmesh.new()
    def loop(r, z):
        return [bm.verts.new((r * math.sin(phase + 2 * math.pi * i / segs), r * math.cos(phase + 2 * math.pi * i / segs), z)) for i in range(segs)]
    ob, ot, ib, it = loop(r_out, z0), loop(r_out, z1), loop(r_in, z0), loop(r_in, z1)
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, mat or Matrix.Identity(4))

def prism(kind, hexc, pts, y0, y1, bevel=0.2):
    """a convex outline given as (x, z) points, pulled along Y from y0 to y1 (wedges, braces)"""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(a)
    bm.faces.new(b[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((a[j], a[i], b[i], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, Matrix.Identity(4))

def leanbox(kind, hexc, sx, sy, sz, x, y, z0, k, bevel=0.2, rot=None):
    """a box standing on z0 whose top is pushed k * sz along Y: its top and bottom stay level"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    for v in bm.verts:
        v.co.z += sz / 2
        v.co.y += k * v.co.z
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, (rot or Matrix.Identity(4)) @ T(x, y, z0))

def trays(x, y, z0, cols, w=2.6, d=1.9, t=0.3, yaws=(0.07, -0.12, 0.05, -0.05)):
    """a slightly untidy stack of trays standing on z0; the top one shows its sunk middle"""
    for i, c in enumerate(cols):
        box('plastic', c, w, d, t, x, y, z0 + t * (i + 0.5), bevel=0.1, rot=RZ(yaws[i % len(yaws)]))
    n = len(cols)
    box('plastic', DARK, w - 0.7, d - 0.7, 0.2, x, y, z0 + t * n - 0.06, bevel=0.05, rot=RZ(yaws[(n - 1) % len(yaws)]))

def bottle(hexc, x, y, z0):
    """a comically large squeeze bottle standing on z0, 3.7 tall"""
    cyl('plastic', hexc, 0.78, 2.2, x, y, z0 + 1.1, segs=14, bevel=0.22)
    cyl('plastic', TILE, 0.84, 0.9, x, y, z0 + 1.15, segs=14, bevel=0.08)           # the label
    cyl('plastic', hexc, 0.74, 0.8, x, y, z0 + 2.5, segs=14, bevel=0.1, r2=0.36)    # the shoulder
    cyl('plastic', hexc, 0.34, 0.9, x, y, z0 + 3.25, segs=10, bevel=0.06, r2=0.18)  # the nozzle

# ------------------------------------------------------------------ fc_stall (26 x 9 x 14; the sign plate's face is y -1.7)
reset()
box('plastic', TILE, 26, 1.0, 10, 0, 4.0, 5.0, bevel=0.3)                    # the back wall
for s in (-1, 1):
    box('plastic', PALE, 2.4, 5.1, 10.0, s * 11.8, 1.05, 5.0, bevel=0.5)     # two fat cheeks
box('plastic', DARK, 25.6, 3.2, 0.6, 0, 2.8, 10.2, bevel=0.15)               # a roof slab behind the header
box('plastic', PALE, 26, 3.0, 4.0, 0, 0, 12.0, bevel=0.5)                    # the header the sign sits on
box('plastic', DARK, 22, 0.4, 3.1, 0, -1.5, 11.95, bevel=0.12)               # the sign plate, for text later
box('neon', LENS, 22, 0.5, 0.45, 0, -1.6, 13.72, bevel=0.14)                 # a lit strip along its top
box('plastic', PINK, 26, 3.4, 1.0, 0, -2.8, 9.8, bevel=0.4)                  # the awning: COLOUR KEY
for i in range(6):
    box('plastic', TILE, 2.0, 3.5, 1.1, -10 + i * 4, -2.8, 9.8, bevel=0.42)  # ...with fat white stripes
# the counter
box('plastic', DARK, 25.2, 2.2, 0.7, 0, -3.0, 0.35, bevel=0.1)
box('plastic', MID, 25.6, 2.6, 3.2, 0, -3.0, 2.0, bevel=0.3)
box('plastic', TILE, 26, 3.0, 0.5, 0, -3.0, 3.75, bevel=0.18)
box('plastic', TILE, 25.7, 0.3, 0.7, 0, -4.22, 2.3, bevel=0.1)               # one fat stripe along its front
# three menu panels on the back wall, a lamp over them
box('neon', WARM, 20.4, 0.5, 0.4, 0, 3.15, 9.4, bevel=0.12)
for i, c in enumerate((ORANGE, YEL, CYAN)):
    x = -7.0 + i * 7.0
    box('plastic', DARK, 6.4, 0.3, 3.2, x, 3.4, 7.3, bevel=0.12)
    box('plastic', c, 2.0, 0.3, 2.0, x - 1.8, 3.3, 7.3, bevel=0.1)
    for z in (6.8, 7.8): box('plastic', TILE, 2.4, 0.3, 0.5, x + 1.3, 3.3, z, bevel=0.1)
# on the counter
trays(-8.5, -3.0, 4.0, (ORANGE, MID, ORANGE, MID))
bottle(RED, 7.3, -3.0, 4.0)
bottle(YEL, 9.4, -2.9, 4.0)
flush('fc_stall')

# ------------------------------------------------------------------ fc_table (top surface z 3.2, stools on the X and Y axes)
reset()
cyl('plastic', DARK, 1.7, 0.5, 0, 0, 0.25, bevel=0.18)
cyl('plastic', MID, 0.65, 2.4, 0, 0, 1.6, segs=12, bevel=0.1)
cyl('plastic', DARK, 1.2, 0.4, 0, 0, 2.55, segs=14, bevel=0.12)
cyl('plastic', YEL, 3.0, 0.5, 0, 0, 2.95, bevel=0.18)                        # the top: COLOUR KEY
for x, y in ((4.6, 0), (-4.6, 0), (0, 4.6), (0, -4.6)):
    cyl('plastic', DARK, 0.85, 0.4, x, y, 0.2, segs=14, bevel=0.14)
    cyl('plastic', MID, 0.45, 1.3, x, y, 0.9, segs=10, bevel=0.08)
    cyl('plastic', TILE, 1.1, 0.65, x, y, 1.675, segs=16, bevel=0.25)
flush('fc_table')

# ------------------------------------------------------------------ fc_tree (planter 7 x 7 x 2.6, 16 tall)
reset()
ring('plastic', TILE, 2.6 * math.sqrt(2), 3.5 * math.sqrt(2), 0, 2.6, segs=4, bevel=0.4, phase=math.pi / 4)
box('plastic', SOIL, 5.6, 5.6, 2.2, 0, 0, 1.2, bevel=0.1)
cyl('wood', WOOD2, 0.8, 7.6, 0, 0, 5.9, segs=12, bevel=0.2, r2=0.6)
blob('plastic', LEAF, 3.6, 3.4, 3.0, -1.6, -0.6, 11.2)
blob('plastic', LEAF2, 3.4, 3.4, 3.0, 1.8, 0.6, 11.4)
blob('plastic', LEAF, 3.2, 3.2, 2.7, 0.0, 0.6, 13.3)
blob('plastic', LEAF2, 2.6, 2.6, 2.3, 0.3, -1.9, 12.2)
flush('fc_tree')

# ------------------------------------------------------------------ fc_duck (basin radius 11 x 2; the text plate's face is y -11.2)
reset()
ring('plastic', TILE, 9.6, 11.0, 0, 2.0, segs=18, bevel=0.35, phase=math.radians(10))
cyl('plastic', CYAN, 9.8, 0.5, 0, 0, 1.35, segs=18, bevel=0)                 # the water, just below the rim
ring('plastic', 'bdf1ff', 7.4, 8.0, 1.3, 1.68, segs=18, bevel=0, mat=T(0, 0.9, 0))   # one fat ripple round the duck
box('plastic', DARK, 6.0, 0.8, 1.2, 0, -10.8, 1.0, bevel=0.12)               # a plate for text later
blob('plastic', YEL, 4.1, 5.6, 3.7, 0, 0.9, 5.0, sub=3)                      # the body
blob('plastic', YEL, 3.0, 3.0, 3.0, 0, -2.7, 10.0, sub=2)                    # the head (sub=3 is rounder, +240 triangles)
for s in (-1, 1):
    blob('plastic', YEL, 1.25, 2.7, 1.75, s * 3.35, 1.7, 5.5, rot=RX(0.25))  # wings: fat bumps on its sides
    d = Vector((s * 0.5, -0.72, 0.42)).normalized() * 2.75
    blob('plastic', INK, 0.55, 0.55, 0.55, d.x, -2.7 + d.y, 10.0 + d.z)      # eyes
blob('plastic', ORANGE, 1.5, 1.6, 0.75, 0, -5.6, 9.5)                        # the beak
cylm('plastic', YEL, 1.9, 3.0, T(0, 5.6, 7.6) @ RX(math.radians(-40)), segs=12, bevel=0.3, r2=0.5)   # a tail flick
flush('fc_duck')

# ------------------------------------------------------------------ fc_skytruss (beam z 2.4 .. 5.4, lamps hang to z 0)
reset()
box('plastic', TILE, 60, 2.4, 0.8, 0, 0, 2.8, bevel=0.28)                    # two chords...
box('plastic', TILE, 60, 2.4, 0.8, 0, 0, 5.0, bevel=0.28)
for i in range(11):
    box('plastic', TILE, 2.2, 2.0, 1.6, -28.9 + i * 5.78, 0, 3.9, bevel=0.2) # ...and fat posts: you see sky through it
for s in (-1, 1):
    prism('plastic', MID, ((s * 30, 0.0), (s * 30, 2.6), (s * 23.6, 2.6)), -1.0, 1.0, bevel=0.25)   # knee braces
for x in (-17.34, 0, 17.34):
    cyl('plastic', DARK, 0.5, 1.6, x, 0, 1.75, segs=10, bevel=0.1)
    cyl('plastic', DARK, 2.2, 0.9, x, 0, 0.6, bevel=0.3)
    cyl('neon', LENS, 1.7, 0.4, x, 0, 0.2, bevel=0.1)
flush('fc_skytruss')

# ------------------------------------------------------------------ fc_wetfloor (3 x 2.6 x 4.4)
reset()
K = 0.8 / 4.2                                                                # how far each face leans in per stud up
face = T(0, -1.3, 0) @ RX(-math.atan(K))                                     # the front face: x across, z up the slope
for turn in (0, math.pi):
    leanbox('plastic', YEL, 3.0, 0.5, 4.2, 0, -1.05, 0, K, bevel=0.14, rot=RZ(turn))
    f = RZ(turn) @ face
    def bar(w, h, u, v, a): boxm('plastic', INK, w, 0.3, h, f @ T(u, -0.03, v) @ RY(math.radians(a)), bevel=0.1)
    cylm('plastic', INK, 0.38, 0.3, f @ T(-0.62, -0.03, 3.1) @ RX(math.pi / 2), segs=12, bevel=0.08)   # head
    bar(0.46, 1.3, -0.1, 2.25, -39)                                          # body, falling back
    bar(0.38, 1.15, 0.68, 2.2, 49)                                           # a leg in the air
    bar(0.38, 1.0, 0.68, 1.6, 118)                                           # the other leg
    bar(0.36, 0.9, -0.85, 2.2, 55)                                           # an arm
    bar(2.3, 0.34, 0, 1.0, 0)                                                # the wet floor
box('plastic', DARK, 3.0, 1.1, 0.5, 0, 0, 4.15, bevel=0.18)                  # the hinge cap
flush('fc_wetfloor')

# ------------------------------------------------------------------ fc_bin (3 x 3 x 5)
reset()
box('plastic', DARK, 2.6, 2.4, 0.5, 0, 0.1, 0.25, bevel=0.1)
box('plastic', PALE, 3.0, 2.8, 3.8, 0, 0.1, 2.2, bevel=0.4)
box('plastic', PINK, 3.1, 2.9, 0.6, 0, 0.1, 1.5, bevel=0.12)                 # one pink band
box('plastic', INK, 2.4, 0.3, 1.4, 0, -1.21, 3.1, bevel=0.12)                # the flap's dark mouth
boxm('plastic', DARK, 2.0, 0.3, 1.0, T(0, -1.45, 3.65) @ RX(0.14) @ T(0, 0, -0.5), bevel=0.1)   # the swing flap, hung from its top edge
trays(0, 0.1, 4.1, (ORANGE, MID, ORANGE), w=2.5)
flush('fc_bin')
