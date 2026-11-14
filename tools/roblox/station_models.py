# THE PLATFORM kit for Roblox in the chunky style (see chunky.py): the underground station used as the game's lobby.
# 1 unit = 1 stud, Z up, the front faces -Y, the floor at z 0, each model centred on x 0, y 0.
#   st_train   one metro car, 30 x 10 x 12; the -Y side has two double doorways (x -7.5 and +7.5), the +Y side windows only.
#              the body shell is the colour key ff4fd8 (recoloured per car); the door leaves and the stripe are one trim
#              piece (c9cedb); a dark 6 x 1 label plate sits over each doorway (its face is y -5, z 9.58 .. 10.58)
#   st_board   a hanging departures board: the ceiling is z 0, two posts, then a 30 x 9 x 1.5 housing (z -12 .. -3) with a
#              flat recessed 28 x 7.4 dark plate on both faces (y -0.6 and +0.6) and a clock in each face's top right corner
#   st_bench   a platform bench, 10 x 3 x 3.2; the seat and back are the colour key ffe14d
#   st_gate    a ticket barrier cabinet, 2.2 x 6 x 4 (x -1.1 .. 1.1), a green arrow lamp on its slanted front top and two
#              pink paddle flaps sticking out to x +2.7
#   st_tunnel  a tunnel mouth surround, 22 x 16 x 3, round an opening 16 x 12; a signal box on the left leg
#   st_totem   an info totem, 3 x 1.2 x 10: a 2.4 x 5 dark panel on both faces (y -0.57 and +0.57, z 3.2 .. 8.2), the lit
#              cap is the colour key 37d6ff
# run: blender -b --factory-startup -P tools/roblox/station_models.py -- <out_dir>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chunky import *
from chunky import _emit, _bevel

PALE, MID, LENS, WARM, TILE = 'a4aab8', '5b6478', 'f4f8ff', 'ffe9b8', 'e8ecf4'
TOXIC, RED, LEAF = '7dff4f', 'ff3b3b', 'c9cedb'

# ------------------------------------------------------------------ extra primitives
def arc(cu, cv, r, a0, a1, n):
    """n + 1 points on an arc round (cu, cv), angles in degrees"""
    return [(cu + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cv + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

def rrect(w, h, r, n=3, cu=0.0, cv=0.0):
    """the outline of a rounded rectangle, anticlockwise from the bottom right corner"""
    a, b = w / 2, h / 2
    r = min(r, a - 0.01, b - 0.01)
    return (arc(cu + a - r, cv - b + r, r, -90, 0, n) + arc(cu + a - r, cv + b - r, r, 0, 90, n)
            + arc(cu - a + r, cv + b - r, r, 90, 180, n) + arc(cu - a + r, cv - b + r, r, 180, 270, n))

def _v(axis, u, v, w):
    """an outline point (u, v) pushed w along `axis`: y -> the outline is in XZ, x -> in YZ, z -> in XY"""
    return (u, w, v) if axis == 'y' else (w, u, v) if axis == 'x' else (u, v, w)

def _rim(bm, verts_sets, amount, segs=2):
    """round off only the edges that run round the given loops of verts (the rims of a cap)"""
    if amount <= 0: return
    edges = [e for e in bm.edges if any(e.verts[0] in s and e.verts[1] in s for s in verts_sets)]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=amount, offset_type='OFFSET', segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)

def prism(kind, hexc, pts, depth, x, y, z, axis='y', bevel=0.15, rim_only=False, segs=2, rot=None):
    """a flat outline [(u, v), ...] pushed out into a slab `depth` thick (centred on its middle plane)"""
    bm = bmesh.new()
    a = [bm.verts.new(_v(axis, u, v, -depth / 2)) for u, v in pts]
    b = [bm.verts.new(_v(axis, u, v, depth / 2)) for u, v in pts]
    n = len(pts)
    bm.faces.new(a); bm.faces.new(b)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if rim_only: _rim(bm, (set(a), set(b)), bevel, segs)
    else: _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, Matrix.Translation((x, y, z)) @ (rot or Matrix.Identity(4)))

def plate(kind, hexc, w, h, depth, x, y, z, r=0.5, axis='y', bevel=0.0, n=3):
    """a slab with rounded corners (w x h in the face, `depth` thick)"""
    prism(kind, hexc, rrect(w, h, r, n), depth, x, y, z, axis=axis, bevel=bevel, rim_only=True)

def ring(kind, hexc, outer, inner, depth, x, y, z, axis='y', bevel=0.15):
    """a frame: the band between two outlines with the same number of points, `depth` thick"""
    bm = bmesh.new()
    oa = [bm.verts.new(_v(axis, u, v, -depth / 2)) for u, v in outer]
    ob = [bm.verts.new(_v(axis, u, v, depth / 2)) for u, v in outer]
    ia = [bm.verts.new(_v(axis, u, v, -depth / 2)) for u, v in inner]
    ib = [bm.verts.new(_v(axis, u, v, depth / 2)) for u, v in inner]
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((oa[i], oa[j], ob[j], ob[i]))
        bm.faces.new((ia[j], ia[i], ib[i], ib[j]))
        bm.faces.new((oa[j], oa[i], ia[i], ia[j]))
        bm.faces.new((ob[i], ob[j], ib[j], ib[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, Matrix.Translation((x, y, z)))

def lathe(kind, hexc, prof, x, y, z, axis='z', segs=14, flip=False):
    """spin a profile [(radius, height), ...] round its axis; start and end it on radius 0"""
    bm = bmesh.new()
    rings = []
    for r, h in prof:
        if r < 1e-6: rings.append([bm.verts.new((0, 0, h))])
        else: rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), h)) for i in range(segs)])
    for p, q in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(p) == 1: bm.faces.new((p[0], q[i], q[j]))
            elif len(q) == 1: bm.faces.new((p[j], p[i], q[0]))
            else: bm.faces.new((p[i], p[j], q[j], q[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    rot = Matrix.Identity(4)
    if axis == 'y': rot = Matrix.Rotation(math.pi / 2 * (1 if flip else -1), 4, 'X')     # heights run along +Y (-Y flipped)
    if axis == 'x': rot = Matrix.Rotation(math.pi / 2 * (-1 if flip else 1), 4, 'Y')     # heights run along +X (-X flipped)
    _emit(kind + '_' + hexc, bm, Matrix.Translation((x, y, z)) @ rot)

def wheel(hexc, r, w, x, y, z, axis='y', segs=16, ch=0.22):
    """a fat wheel with chamfered shoulders"""
    lathe('plastic', hexc, [(0, -w / 2), (r - ch, -w / 2), (r, -w / 2 + ch), (r, w / 2 - ch), (r - ch, w / 2), (0, w / 2)], x, y, z, axis=axis, segs=segs)

def car_shell(kind, hexc, half_len, hw, z0, z1, rb, rt, doors, door_hw, door_top, sink, jamb=0.15, bevel=0.6, segs=4):
    """the train's body: one rounded tube along X with flat ends; on the -Y side a pocket `sink` deep is pressed in for
    each doorway (centre x in `doors`, half width door_hw, from the bottom edge up to door_top)"""
    prof = arc(-hw + rb, z0 + rb, rb, 270, 180, 4)                 # the -Y bottom corner (moves in with the pocket)
    n_move = len(prof) + 1
    prof += [(-hw, door_top), (-hw, door_top + jamb)]
    prof += arc(-hw + rt, z1 - rt, rt, 180, 90, 2) + arc(hw - rt, z1 - rt, rt, 90, 0, 2) + arc(hw - rb, z0 + rb, rb, 0, -90, 4)
    stations = [(-half_len, False)]
    for c in sorted(doors):
        stations += [(c - door_hw - jamb, False), (c - door_hw, True), (c + door_hw, True), (c + door_hw + jamb, False)]
    stations.append((half_len, False))
    bm = bmesh.new()
    secs = []
    for sx, bay in stations:
        secs.append([bm.verts.new((sx, py + (sink if bay and i < n_move else 0.0), pz)) for i, (py, pz) in enumerate(prof)])
    n = len(prof)
    for p, q in zip(secs, secs[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((p[i], p[j], q[j], q[i]))
    bm.faces.new(secs[0]); bm.faces.new(secs[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _rim(bm, (set(secs[0]), set(secs[-1])), bevel, segs)
    _emit(kind + '_' + hexc, bm, Matrix.Identity(4))

# ------------------------------------------------------------------ st_train (30 x 10 x 12; the platform side is -Y)
reset()
BL, BW = 14.6, 4.85                      # the body's half length and half width (the couplers reach x 15, the windows y 5)
DOORS, DTOP = (-7.5, 7.5), 9.45
car_shell('plastic', PINK, BL, BW, 1.7, 10.9, 0.8, 0.3, DOORS, 2.45, DTOP, 0.5, bevel=0.9)
# the roof: a low loaf with two pods on it
prism('plastic', TILE, [(4.7 * math.cos(math.radians(a)), 10.6 + 1.05 * math.sin(math.radians(a))) for a in range(0, 181, 15)],
      BL * 2, 0, 0, 0, axis='x', bevel=0.9, rim_only=True, segs=4)
for x in DOORS: box('plastic', PALE, 5.6, 5.2, 1.0, x, 0, 11.5, bevel=0.35)
# the underframe, the gear under the floor, the couplers
box('plastic', DARK, 28.4, 8.0, 0.9, 0, 0, 1.45, bevel=0.2)
box('plastic', MID, 7.0, 7.6, 1.2, 0, 0, 0.95, bevel=0.3)
for s in (-1, 1):
    box('plastic', INK, 1.7, 2.0, 0.9, s * 14.15, 0, 1.3, bevel=0.25)
    # a bogie: a block, four fat wheels and a beam between each pair
    box('plastic', DARK, 6.6, 7.4, 1.0, s * 9.6, 0, 1.0, bevel=0.25)
    for f in (-1, 1):
        box('plastic', DARK, 2.4, 0.9, 0.8, s * 9.6, f * 4.2, 1.0, bevel=0.2)
        for dx in (-2.0, 2.0):
            wheel(INK, 0.9, 1.2, s * 9.6 + dx, f * 4.15, 0.9)
            lathe('plastic', PALE, [(0, 0), (0.5, 0), (0.36, 0.28), (0, 0.28)], s * 9.6 + dx, f * 4.72, 0.9, axis='y', segs=10, flip=f < 0)
    # the end wall: a gangway door with a lit window
    plate('plastic', INK, 3.6, 7.4, 0.3, s * (BL - 0.02), 0, 5.9, r=0.8, axis='x')
    plate('neon', WARM, 2.0, 2.8, 0.3, s * (BL + 0.03), 0, 7.0, r=0.5, axis='x')
# the platform side: two doorways...
for c in DOORS:
    box('plastic', INK, 4.9, 0.4, DTOP - 1.8, c, -4.3, (DTOP + 1.8) / 2, bevel=0)                # the dark behind the leaves
    for s in (-1, 1):
        box('plastic', LEAF, 2.3, 0.4, 7.3, c + s * 1.3, -4.55, 5.72, bevel=0.15)                # a door leaf
        plate('neon', WARM, 1.4, 3.0, 0.3, c + s * 1.3, -4.68, 6.9, r=0.5, n=5)
    box('plastic', YEL, 5.0, 0.9, 0.45, c, -4.55, 1.86, bevel=0.15)                              # the step
    box('plastic', INK, 6.0, 0.4, 1.0, c, -4.8, 10.08, bevel=0.12)                               # the label plate
# ...the windows between and beside them, and a stripe in the doors' shade under the windows
def window(x, w, face, panes=1, h=3.5, z=7.0, n=4):
    plate('plastic', INK, w + 0.7, h + 0.7, 0.3, x, face * (BW - 0.05), z, r=0.8, n=n)
    pw = (w - 0.45 * (panes - 1)) / panes
    for i in range(panes):
        plate('neon', WARM, pw, h, 0.3, x - w / 2 + pw / 2 + i * (pw + 0.45), face * BW, z, r=0.5, n=n)
def stripe(x, w, face): plate('plastic', LEAF, w, 0.9, 0.3, x, face * (BW - 0.05), 3.5, r=0.44)
window(0, 7.9, -1, panes=2, n=5)
stripe(0, 8.6, -1)
for x in (-12.0, 12.0):
    window(x, 2.5, -1, n=5)
    stripe(x, 3.2, -1)
# the far side: three long windows
for x in (-9.5, 0, 9.5): window(x, 7.4, 1, panes=2)
stripe(0, 27.1, 1)
flush('st_train')

# ------------------------------------------------------------------ st_board (hangs from z 0; the housing is z -12 .. -3)
reset()
ring('plastic', PALE, rrect(30, 9, 0.9), rrect(28, 7.4, 0.45), 1.5, 0, 0, -7.5, bevel=0.18)
box('plastic', INK, 28.4, 1.2, 7.8, 0, 0, -7.5, bevel=0)                    # the two text faces: y -0.6 and y +0.6
for s in (-1, 1):
    box('plastic', MID, 1.3, 1.3, 3.4, s * 9.0, 0, -1.7, bevel=0.3)         # a post
    box('plastic', DARK, 2.6, 1.6, 0.5, s * 9.0, 0, -0.25, bevel=0.16)      # its plate on the ceiling
    box('plastic', DARK, 2.0, 1.7, 0.5, s * 9.0, 0, -3.05, bevel=0.14)      # its shoe on the housing
    # a clock in the top right corner of the face that looks along f (so each face has its own, at opposite ends)
    f = s
    cx, cz = -f * 13.25, -4.55
    lathe('plastic', PALE, [(0, 0), (1.3, 0), (1.3, 0.6), (1.14, 0.78), (1.0, 0.78), (1.0, 0.6), (0, 0.6)], cx, 0, cz, axis='y', segs=20, flip=f < 0)
    lathe('plastic', LENS, [(0, 0), (0.99, 0), (0.99, 0.68), (0, 0.68)], cx, 0, cz, axis='y', segs=20, flip=f < 0)
    for length, ang in ((0.6, -1.05), (0.88, 1.05)):                        # ten past ten
        box('plastic', INK, 0.3, 0.2, length, cx + 0.5 * length * math.sin(ang), f * 0.72, cz + 0.5 * length * math.cos(ang), bevel=0.06, rot=RY(ang))
    lathe('plastic', INK, [(0, 0), (0.24, 0), (0.24, 0.86), (0, 0.86)], cx, 0, cz, axis='y', segs=8, flip=f < 0)
flush('st_board')

# ------------------------------------------------------------------ st_bench (10 x 3 x 3.2; you sit facing -Y)
reset()
box('plastic', YEL, 10, 2.3, 0.7, 0, -0.35, 1.5, bevel=0.28)                                   # the seat
box('plastic', YEL, 10, 0.7, 1.3, 0, 0.9, 2.52, bevel=0.28, rot=RX(-0.14))                     # the back
for x in (-3.3, 3.3):
    # a fat leg: a boot shape seen from the side (y, z)
    prism('plastic', DARK, [(-1.25, 0), (1.5, 0), (1.5, 2.75), (0.85, 2.75), (0.85, 1.3), (-1.25, 1.3)], 1.3, x, 0, 0, axis='x', bevel=0.2)
flush('st_bench')

# ------------------------------------------------------------------ st_gate (the cabinet is x -1.1 .. 1.1, y -3 .. 3; the flaps reach x 2.7)
reset()
SLOPE = math.atan2(1.2, 3.1)
box('plastic', INK, 2.2, 6.0, 0.6, 0, 0, 0.3, bevel=0.18)                                      # the plinth
prism('plastic', PALE, [(-2.9, 0.3), (2.9, 0.3), (2.9, 4.0), (0.2, 4.0), (-2.9, 2.8)], 2.0, 0, 0, 0, axis='x', bevel=0.3)
box('plastic', DARK, 2.2, 2.6, 2.1, 0, 0.9, 2.0, bevel=0.22)                                   # the band the flaps come out of
for y in (0.25, 1.55):
    plate('plastic', PINK, 2.2, 1.6, 0.5, 1.6, y, 2.0, r=0.6, bevel=0.12, n=4)                 # a paddle flap
# the arrow lamp on the slanted top, pointing the way through
tilt = RX(SLOPE)
mid_y, mid_z = -1.35, 2.8 + 1.2 * (1.55 / 3.1)
box('plastic', INK, 1.6, 2.4, 0.3, 0, mid_y, mid_z, bevel=0.12, rot=tilt)
prism('neon', TOXIC, [(-0.28, -0.95), (0.28, -0.95), (0.28, 0.0), (0.62, 0.0), (0, 0.95), (-0.62, 0.0), (-0.28, 0.0)], 0.3,
      0, mid_y - 0.1 * math.sin(SLOPE), mid_z + 0.1 * math.cos(SLOPE), axis='z', bevel=0.05, rot=tilt)
flush('st_gate')

# ------------------------------------------------------------------ st_tunnel (22 x 16 x 3; the opening is x -8 .. 8, z 0 .. 12)
reset()
def mouth(half_out, top, r_out, half_in, top_in, r_in, n=8):
    """an upside-down U: the outside from the right foot round to the left, then back along the opening"""
    return ([(half_out, 0)] + arc(half_out - r_out, top - r_out, r_out, 0, 90, n) + arc(-half_out + r_out, top - r_out, r_out, 90, 180, n)
            + [(-half_out, 0), (-half_in, 0)] + arc(-half_in + r_in, top_in - r_in, r_in, 180, 90, n) + arc(half_in - r_in, top_in - r_in, r_in, 90, 0, n)
            + [(half_in, 0)])
prism('plastic', PALE, mouth(10.8, 16, 2.6, 8.4, 12.4, 3.4), 2.6, 0, 0, 0, bevel=0.35)
prism('plastic', DARK, mouth(9.0, 13.0, 4.0, 8.0, 12.0, 3.0), 2.8, 0, 0, 0, bevel=0.25)        # the dark lining of the mouth
for s in (-1, 1):
    box('plastic', YEL, 3.1, 2.9, 5.0, s * 9.4, 0, 2.5, bevel=0.3)                             # a hazard block round each foot...
    for z in (1.5, 3.5): box('plastic', INK, 3.2, 3.0, 1.0, s * 9.4, 0, z, bevel=0.1)          # ...with two ink belts
# the signal box on the left leg (it wraps the leg, so the back shows a plain block)
box('plastic', INK, 3.2, 3.0, 4.0, -9.4, 0, 7.8, bevel=0.3)
cyl('neon', RED, 0.75, 0.4, -9.4, -1.4, 8.8, axis='y', segs=16, bevel=0.1)
cyl('neon', TOXIC, 0.75, 0.4, -9.4, -1.4, 6.8, axis='y', segs=16, bevel=0.1)
flush('st_tunnel')

# ------------------------------------------------------------------ st_totem (3 x 1.2 x 10)
reset()
box('plastic', INK, 3.0, 1.2, 0.6, 0, 0, 0.3, bevel=0.2)
box('plastic', PALE, 2.7, 0.9, 8.7, 0, 0, 4.65, bevel=0.3)
box('plastic', DARK, 2.9, 1.1, 0.5, 0, 0, 9.0, bevel=0.15)
box('neon', CYAN, 3.0, 1.2, 0.9, 0, 0, 9.55, bevel=0.3)
for s in (-1, 1):
    box('plastic', INK, 2.4, 0.3, 5.0, 0, s * 0.42, 5.7, bevel=0.1)
    cyl('plastic', YEL, 0.55, 0.3, 0, s * 0.42, 2.0, axis='y', segs=14, bevel=0.08)
flush('st_totem')
