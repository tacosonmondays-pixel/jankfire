# THE GIANT FOOD kit for Roblox in the chunky style (see chunky.py): one giant food for the roof of each food-court
# stall, so a stall can be told from across the room, and the station's buffer stop.
# few big shapes, every sharp edge rounded off, flat colours. 1 unit = 1 stud, Z up, the front faces -Y, the flat
# bottom at z 0. nothing is thinner than about a third of a stud.
#   fc_food_noodles  ONE ON ONE NOODLES: an oval bowl (pink rim) and a rope of noodles pulled up out of it by two fat
#                    chopsticks that run off to the right; an egg and a fish cake stand in the broth, facing -Y
#   fc_food_kebab    THREE'S A CROWD KEBABS: one fat skewer leaning out of a round board, three chunks crowded on it
#                    (meat, green pepper, tomato)
#   fc_food_taco     TWO FOR TWO TACOS: one taco side on, its fold flat on the roof, lettuce, tomato and cheese
#                    spilling over the round edge
#   fc_food_burger   TRIPLE STACK BURGERS: three patties, two slices of cheese, lettuce, tomato, a seeded bun (an oval)
#   fc_food_pizza    FOUR SQUARE PIZZA: a slice standing on its crust, point up, four pepperoni on the -Y face
#   fc_food_fries    HIGH FIVE FRIES: a carton with five fat fries held up like the fingers of a hand, thumb to +X
#   st_buffer        a railway buffer stop 8 x 3 x 4.2: two raked side frames over the rails (x -2.5 and +2.5), a yellow
#                    beam and two round buffers on the -Y face (the side the train comes from), a red lamp on top
# run: blender -b --factory-startup -P tools/roblox/giantfood_models.py -- <out_dir>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chunky import *
from chunky import _emit, _bevel

PALE, MID, TILE, RED = 'a4aab8', '5b6478', 'e8ecf4', 'ff3b3b'
BUN, PATTY, CHEESE, LETTUCE, TOMATO, SEED = 'dc9a45', '8a5330', 'ffc93a', '6fbf4a', 'e23b3b', 'f6e3b4'
NOODLE, BROTH, YOLK, STICK, SHELL, CHEDDAR, PEPPERONI, FRY = 'f6dc8a', 'e8963a', 'ffb52e', 'e3c88a', 'e9b04a', 'ff9a1f', 'c9412f', 'ffcf3f'
RZ = lambda a: Matrix.Rotation(a, 4, 'Z')
T = lambda x, y, z: Matrix.Translation((x, y, z))
D = lambda x, y, z: Matrix.Diagonal((x, y, z, 1.0))
ID = Matrix.Identity(4)

# ------------------------------------------------------------------ extra primitives
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
    _bevel(bm, min(bevel, depth * 0.42, min(r, r if r2 is None else r2) * 0.42))
    _emit(kind + '_' + hexc, bm, mat)

def blobm(kind, hexc, rx, ry, rz, mat, sub=2):
    """a rounded blob: an icosphere squashed to the three radii, placed by a whole matrix"""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    _emit(kind + '_' + hexc, bm, mat @ D(rx, ry, rz))

def taper(kind, hexc, w0, d0, w1, d1, h, mat, bevel=0.3):
    """a box standing on its own z 0, w0 x d0 at the bottom and w1 x d1 at the top"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        top = v.co.z > 0
        v.co.x *= w1 if top else w0
        v.co.y *= d1 if top else d0
        v.co.z = h if top else 0.0
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, mat)

def prismm(kind, hexc, pts, y0, y1, mat=None, bevel=0.2):
    """a convex outline given as (x, z) points, pulled along Y from y0 to y1, placed by a whole matrix"""
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
    _emit(kind + '_' + hexc, bm, mat or ID)

def xprism(kind, hexc, pts, x0, x1, bevel=0.2):
    """a convex outline given as (y, z) points, pulled along X from x0 to x1 (the buffer's raked frames)"""
    bm = bmesh.new()
    a = [bm.verts.new((x0, y, z)) for y, z in pts]
    b = [bm.verts.new((x1, y, z)) for y, z in pts]
    bm.faces.new(a)
    bm.faces.new(b[::-1])
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((a[j], a[i], b[i], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, ID)

def ring(kind, hexc, r_in, r_out, z0, z1, segs=18, bevel=0.2, mat=None):
    """a flat-topped ring"""
    bm = bmesh.new()
    def loop(r, z):
        return [bm.verts.new((r * math.sin(2 * math.pi * i / segs), r * math.cos(2 * math.pi * i / segs), z)) for i in range(segs)]
    ob, ot, ib, it = loop(r_out, z0), loop(r_out, z1), loop(r_in, z0), loop(r_in, z1)
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, mat or ID)

def lathe(kind, hexc, prof, mat, segs=24, bevel=0.0):
    """an (r, z) outline, bottom to top, spun round Z: r 0 at an end closes it to a point, anything else gets a flat cap"""
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r <= 1e-6: rings.append([bm.verts.new((0.0, 0.0, z))])
        else: rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z)) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) == 1 and len(b) == 1: continue
            if len(a) == 1: bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1: bm.faces.new((a[i], a[j], b[0]))
            else: bm.faces.new((a[i], a[j], b[j], b[i]))
    if len(rings[0]) > 1: bm.faces.new(rings[0][::-1])
    if len(rings[-1]) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, mat)

def tube(kind, hexc, pts, r, segs=8, mat=None):
    """a fat round rope through the points, its two ends rounded off (noodles)"""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    tans = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    # one extra, smaller loop past each end, then a point: a rounded end
    path = [(pts[0] - tans[0] * r * 0.55, tans[0], 0.72)] + [(pts[i], tans[i], 1.0) for i in range(n)] + [(pts[-1] + tans[-1] * r * 0.55, tans[-1], 0.72)]
    up = Vector((0, 1, 0)) if abs(tans[0].y) < 0.9 else Vector((1, 0, 0))
    nrm = (up - tans[0] * up.dot(tans[0])).normalized()
    bm = bmesh.new()
    loops, prev = [], None
    for p, t, k in path:
        if prev is not None:
            ax = prev.cross(t)
            if ax.length > 1e-6: nrm = Matrix.Rotation(prev.angle(t), 3, ax.normalized()) @ nrm
        nrm = (nrm - t * nrm.dot(t)).normalized()
        bi = t.cross(nrm)
        loops.append([bm.verts.new(p + (nrm * math.cos(2 * math.pi * j / segs) + bi * math.sin(2 * math.pi * j / segs)) * r * k) for j in range(segs)])
        prev = t
    for a, b in zip(loops, loops[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((a[i], a[j], b[j], b[i]))
    e0 = bm.verts.new(pts[0] - tans[0] * r * 0.9)
    e1 = bm.verts.new(pts[-1] + tans[-1] * r * 0.9)
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((e0, loops[0][j], loops[0][i]))
        bm.faces.new((e1, loops[-1][i], loops[-1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _emit(kind + '_' + hexc, bm, mat or ID)

def wavy(kind, hexc, r, t, mat, waves=6, amp=0.28, segs=30, bevel=0.18):
    """a disc whose rim goes up and down (a lettuce leaf)"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=segs, radius1=r, radius2=r, depth=t)
    for v in bm.verts:
        if math.hypot(v.co.x, v.co.y) > 0.01: v.co.z += amp * math.sin(waves * math.atan2(v.co.y, v.co.x))
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, mat)

def arch(r, straight, n=16):
    """the outline of a taco seen side on: a half disc of radius r standing on a straight strip"""
    return [(r, 0.0)] + [(r * math.cos(math.pi * i / n), straight + r * math.sin(math.pi * i / n)) for i in range(n + 1)] + [(-r, 0.0)]

# ------------------------------------------------------------------ fc_food_noodles (about 10.6 x 8 x 10.6)
reset()
OVAL = D(1, 0.81, 1)                                                          # the bowl is an oval, 9.7 across and 7.9 deep
cylm('plastic', TILE, 2.4, 0.9, T(0, 0, 0.45) @ OVAL, segs=24, bevel=0.22)    # the foot
cylm('plastic', TILE, 2.6, 2.6, T(0, 0, 1.9) @ OVAL, segs=28, bevel=0.3, r2=4.7)
ring('plastic', PINK, 4.1, 4.85, 2.8, 3.6, segs=28, bevel=0.24, mat=OVAL)     # one fat pink rim
cylm('plastic', BROTH, 4.2, 0.4, T(0, 0, 3.25) @ OVAL, segs=28, bevel=0)
MX, MY, MZ, MC = 3.3, 2.5, 1.35, 3.5                                          # the heap of noodles in the bowl
blobm('plastic', NOODLE, MX, MY, MZ, T(0, 0.2, MC), sub=3)
for yaw, off in ((0.5, -0.5), (-0.4, 0.0), (0.9, 0.55), (-1.0, -0.6)):        # ...with a few fat noodles lying over it
    pts = []
    for i in range(11):
        a = math.radians(25 + 13 * i)
        u = RZ(yaw) @ Vector((math.cos(a), off, math.sin(a))).normalized()
        pts.append((u.x * MX, 0.2 + u.y * MY, MC + u.z * MZ))
    tube('plastic', NOODLE, pts, 0.4)
for x0 in (-0.95, 0.0, 0.95):                                                 # three wavy noodles pulled up to the chopsticks
    pts = [(x0 + 0.32 * math.sin(s * 9.4), 0.2 + 0.12 * math.cos(s * 9.4 + x0), 4.3 + s * 3.8) for s in [i / 15 for i in range(16)]]
    tube('plastic', NOODLE, pts, 0.42)
blobm('plastic', NOODLE, 1.7, 1.05, 0.85, T(0, 0.2, 8.2))                     # the bunch the chopsticks grip
for tz, a in ((7.75, 5), (8.45, 13)):                                          # two fat chopsticks, off to the right
    cylm('wood', WOOD, 0.36, 7.4, T(-1.9, 0.2, tz) @ RY(math.radians(90 - a)) @ T(0, 0, 3.7), segs=8, bevel=0.12, r2=0.52)
EGG = T(-2.35, -1.95, 3.9) @ RZ(-0.3) @ RX(math.radians(60))                  # half an egg stood in the broth
cylm('plastic', 'f4f8ff', 1.25, 0.6, EGG, segs=16, bevel=0.2)
cylm('plastic', YOLK, 0.62, 0.4, EGG @ T(0, 0, 0.22), segs=12, bevel=0.14)
blobm('plastic', LETTUCE, 1.25, 0.55, 1.5, T(2.5, -1.7, 3.9) @ RZ(0.35) @ RX(math.radians(-25)))   # and one fat green leaf
flush('fc_food_noodles')

# ------------------------------------------------------------------ fc_food_kebab (about 7.5 x 6.3 x 10.5)
reset()
cylm('wood', WOOD, 3.7, 1.0, T(0, 0, 0.5) @ D(1, 0.85, 1), segs=28, bevel=0.32)   # the board it is stuck in
SK = T(-1.5, 0, 0.5) @ RY(math.radians(16))                                   # the skewer's own frame: its z runs up it
cylm('plastic', STICK, 0.36, 9.2, SK @ T(0, 0, 4.6), segs=10, bevel=0.08)
cylm('plastic', STICK, 0.36, 1.2, SK @ T(0, 0, 9.75), segs=10, bevel=0.06, r2=0.15)   # its blunt point
boxm('plastic', PATTY, 4.2, 3.6, 2.4, SK @ T(0, 0, 2.7) @ RZ(0.2), bevel=0.7)        # meat
boxm('plastic', LETTUCE, 4.6, 3.2, 1.8, SK @ T(0, 0, 4.85) @ RZ(-0.3), bevel=0.6)    # a slab of green pepper
blobm('plastic', TOMATO, 1.95, 1.95, 1.5, SK @ T(0, 0, 7.2), sub=3)                  # a tomato
flush('fc_food_kebab')

# ------------------------------------------------------------------ fc_food_taco (about 13.4 x 5.4 x 9.4)
reset()
R, S0 = 6.0, 1.8
box('plastic', SHELL, 11.9, 2.6, 1.1, 0, 0, 0.55, bevel=0.45)                 # the fold it stands on
for s in (-1, 1):                                                             # the two sides of the shell, leaning apart
    prismm('plastic', SHELL, arch(R, S0), -0.35, 0.35, T(0, s * 1.0, 0.1) @ RX(math.radians(-s * 9)), bevel=0.25)
prismm('plastic', PATTY, arch(R - 0.12, S0), -1.3, 1.3, bevel=0.2)            # the meat between them (it ends inside the shell's thickness: no slit)
for i in range(11):                                                           # lettuce: a fat frill round the edge
    a = math.radians(18 + 14.4 * i)
    blobm('plastic', LETTUCE, 1.15, 1.9, 1.0, T((R - 0.15) * math.cos(a), 0, S0 + (R - 0.15) * math.sin(a)) @ RY(math.pi / 2 - a))
for deg, y in ((52, -0.5), (93, 0.5), (132, -0.4)):                           # tomatoes
    a = math.radians(deg)
    blobm('plastic', TOMATO, 1.05, 1.05, 0.95, T((R + 0.6) * math.cos(a), y, S0 + (R + 0.6) * math.sin(a)) @ RY(math.pi / 2 - a))
for deg, y in ((32, 0.5), (72, 0.3), (113, -0.5), (152, 0.4)):                # chunks of cheese
    a = math.radians(deg)
    boxm('plastic', CHEDDAR, 1.7, 1.3, 1.1, T((R + 0.55) * math.cos(a), y, S0 + (R + 0.55) * math.sin(a)) @ RY(math.pi / 2 - a) @ RZ(0.4), bevel=0.32)
flush('fc_food_taco')

# ------------------------------------------------------------------ fc_food_burger (about 10.4 x 8 x 10.1)
reset()
OV = D(1, 0.77, 1)                                                            # an oval, to fit the depth of a stall's roof
L_ = lambda z: T(0, 0, z) @ OV
cylm('plastic', BUN, 4.75, 1.6, L_(0.8), segs=32, bevel=0.55)                 # the bottom bun
for i in range(3):
    z = 2.125 + i * 1.6
    cylm('plastic', PATTY, 4.95, 1.25, L_(z), segs=32, bevel=0.4)             # three patties...
    if i < 2: boxm('plastic', CHEESE, 7.8, 7.8, 0.46, L_(z + 0.8) @ RZ(math.radians(22 if i == 0 else -22)), bevel=0.15)   # ...two slices of cheese, corners out
wavy('plastic', LETTUCE, 5.15, 0.55, L_(6.2))
cylm('plastic', TOMATO, 4.6, 0.75, L_(6.7), segs=32, bevel=0.28)
RB, ZB, LIP, HB = 4.85, 6.95, 0.5, 2.65
prof = [(0.0, ZB), (RB - 0.55, ZB), (RB - 0.16, ZB + 0.16), (RB, ZB + LIP)]
prof += [(RB * math.cos(math.pi / 2 * i / 8), ZB + LIP + HB * math.sin(math.pi / 2 * i / 8)) for i in range(1, 8)] + [(0.0, ZB + LIP + HB)]
lathe('plastic', BUN, prof, OV, segs=32)                                      # the top bun
for el, az, spin in ((52, -90, 0.3), (36, -48, -0.5), (36, -132, 0.6), (64, -15, 1.0), (64, -165, -0.9), (24, -92, 1.4), (44, 30, 0.2), (44, 150, -0.3), (50, 90, 0.8)):
    e, a = math.radians(el), math.radians(az)                                 # nine fat seeds
    p = Vector((RB * math.cos(e) * math.cos(a), RB * 0.77 * math.cos(e) * math.sin(a), ZB + LIP + HB * math.sin(e)))
    nrm = Vector((p.x / RB ** 2, p.y / (RB * 0.77) ** 2, (p.z - ZB - LIP) / HB ** 2)).normalized()
    blobm('plastic', SEED, 0.66, 0.4, 0.3, T(p.x, p.y, p.z) @ Vector((0, 0, 1)).rotation_difference(nrm).to_matrix().to_4x4() @ RZ(spin))
flush('fc_food_burger')

# ------------------------------------------------------------------ fc_food_pizza (about 10.8 x 3 x 10.2)
reset()
box('plastic', BUN, 10.8, 3.0, 2.4, 0, 0, 1.2, bevel=0.95)                    # the crust it stands on
prismm('plastic', BUN, ((-4.9, 1.2), (4.9, 1.2), (0.0, 10.5)), 0.0, 1.0, bevel=0.42)     # the base
prismm('plastic', CHEESE, ((-4.3, 1.6), (4.3, 1.6), (0.0, 9.7)), -0.9, 0.2, bevel=0.4)   # the cheese, on the -Y face
for x, z, r in ((0.0, 7.3, 0.9), (-0.9, 5.2, 1.0), (1.6, 3.9, 1.0), (-2.1, 3.35, 0.95)): # four pepperoni
    cyl('plastic', PEPPERONI, r, 0.6, x, -1.0, z, axis='y', segs=16, bevel=0.2)
flush('fc_food_pizza')

# ------------------------------------------------------------------ fc_food_fries (about 10.3 x 3.8 x 10.3)
reset()
cw = lambda z: 5.2 + 2.4 * z / 5.0                                            # the carton's width and depth at a height
cd = lambda z: 3.0 + 0.8 * z / 5.0
taper('plastic', TOMATO, cw(0), cd(0), cw(5), cd(5), 5.0, ID, bevel=0.45)
box('plastic', TOMATO, 7.6, 1.0, 2.2, 0, 1.4, 5.6, bevel=0.42)                # its tall back
taper('plastic', TILE, cw(1.9) + 0.2, cd(1.9) + 0.2, cw(3.3) + 0.2, cd(3.3) + 0.2, 1.4, T(0, 0, 1.9), bevel=0.15)   # one fat pale band
def fry(xb, y, zb, deg, length):
    boxm('plastic', FRY, 1.25, 1.25, length, T(xb, y, zb) @ RY(math.radians(deg)) @ T(0, 0, length / 2), bevel=0.3)
for xb, deg, length in ((-2.5, -9, 6.6), (-1.2, -4, 8.0), (0.1, 0, 8.8), (1.4, 5, 8.1)): fry(xb, -0.75, 1.5, deg, length)   # four fingers
fry(2.4, -0.75, 3.6, 38, 5.2)                                                 # and a thumb
for xb, deg, length in ((-1.9, -6, 5.6), (-0.55, -2, 6.4), (0.8, 3, 6.0)): fry(xb, 0.75, 1.5, deg, length)                  # a shorter row behind
flush('fc_food_fries')

# ------------------------------------------------------------------ st_buffer (8 x 3 x 4.2; the rails run in at x -2.5 and +2.5)
reset()
for s in (-1, 1):
    xprism('plastic', MID, ((-0.8, 0.0), (1.5, 0.0), (1.5, 1.0), (0.3, 4.0), (-0.8, 4.0)), s * 2.5 - 0.7, s * 2.5 + 0.7, bevel=0.3)   # a raked frame over each rail
    cyl('plastic', PALE, 0.85, 0.5, s * 2.5, -1.25, 3.1, axis='y', segs=16, bevel=0.16)   # a round buffer
    box('plastic', DARK, 0.8, 1.06, 1.26, s * 0.8, -0.6, 3.1, bevel=0.12)                 # a fat dark stripe
box('plastic', YEL, 8.0, 1.0, 1.2, 0, -0.6, 3.1, bevel=0.3)                   # the beam
box('wood', WOOD2, 7.4, 1.0, 0.7, 0, 0.9, 0.35, bevel=0.2)                    # one sleeper across the back
cyl('neon', RED, 0.55, 0.5, 0, -0.5, 3.95, segs=14, bevel=0.16)               # the red lamp
flush('st_buffer')
