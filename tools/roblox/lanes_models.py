# THE LANES kit for Roblox in the chunky style (see chunky.py): the bowling alley that is the game's lobby. a few big
# rounded shapes, flat colours, nothing thin. 1 unit = 1 stud, Z up, the front faces -Y, the floor at z 0, centred on x 0 y 0.
#   bw_pins        ten fat pins in a triangle on a 9 x 9 deck plate, the head pin toward -Y, one pin on its way over
#   bw_pinsetter   the housing over the pins, 14 x 6 x 7, on two cheeks (opening 10 x 4.2); a dark score plate and five
#                  lit dots in its front face. the body is the colour key ff4fd8
#   bw_ballreturn  a ball return, 4 x 9 x 3.4: a low rack of four balls running out of a hood at the +Y end
#   bw_booth       a U-shaped sofa, 14 x 8 x 4.2, round a small round table; open toward -Y. cushions: colour key 37d6ff
#   bw_counter     the shoe counter, 20 x 8 x 10: a counter in front, a wall of shoes behind, a fat bell
#   bw_giantpin    a giant pin on a round plinth with a lit ring, a lit star on top, 9 across x 17.4 tall
# run: blender -b --factory-startup -P tools/roblox/lanes_models.py -- <out_dir>
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chunky import *
from chunky import _emit, _bevel

PALE, MID, LENS, WARM = 'a4aab8', '5b6478', 'f4f8ff', 'ffe9b8'
GREEN, PINW, LANE, CARPET = '7dff4f', 'f4f2ec', 'e2c08a', '4b2a6b'
RZ = lambda a: Matrix.Rotation(a, 4, 'Z')
T = lambda x, y, z: Matrix.Translation((x, y, z))

# ------------------------------------------------------------------ extra primitives
def _bev(bm, edges, amount, segs=2):
    edges = [e for e in edges if e.is_valid]
    if edges and amount > 0:
        bmesh.ops.bevel(bm, geom=edges, offset=amount, offset_type='OFFSET', segments=segs, profile=0.5, affect='EDGES', clamp_overlap=True)

def _sharp(bm):
    return [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.9]

def soft(kind, hexc, sx, sy, sz, x, y, z, r, pick='all', segs=3, small=0.12, rot=None):
    """a box with some of its edges rounded properly (radius r, several steps); the rest get the usual small bevel.
    pick: 'all', 'top' (the top rim and the four uprights), 'up' (the four uprights), 'topx' / 'topy' (the two top
    edges that run along X / Y: an arch)"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    def want(e):
        a, b = e.verts[0].co, e.verts[1].co
        d = b - a
        ax = max(range(3), key=lambda k: abs(d[k]))
        top = a.z > 0 and b.z > 0
        if pick == 'all': return True
        if pick == 'top': return top or ax == 2
        if pick == 'up': return ax == 2
        if pick == 'topx': return top and ax == 0
        if pick == 'topy': return top and ax == 1
        return False
    _bev(bm, [e for e in bm.edges if want(e)], r, segs)
    _bevel(bm, small)
    _emit(kind + '_' + hexc, bm, T(x, y, z) @ (rot or Matrix.Identity(4)))

def lathe(kind, hexc, prof, mat, segs=12, bevel=0.0, cap=True):
    """spin a profile [(r, z), ...] (bottom to top) round Z; r 0 at the top closes it with a fan"""
    bm = bmesh.new()
    rings = []
    for r, h in prof:
        if r < 1e-5: rings.append([bm.verts.new((0, 0, h))])
        else: rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), h)) for i in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) > 1 and len(b) > 1: bm.faces.new((a[i], a[j], b[j], b[i]))
            elif len(a) > 1: bm.faces.new((a[i], a[j], b[0]))
            elif len(b) > 1: bm.faces.new((a[0], b[j], b[i]))
    if cap and len(rings[0]) > 1: bm.faces.new(rings[0][::-1])
    if cap and len(rings[-1]) > 1: bm.faces.new(rings[-1])
    _bevel(bm, bevel)
    _emit(kind + '_' + hexc, bm, mat)

def finer(prof):
    """one round of smooth subdivision of a lathe profile"""
    out, n = [], len(prof)
    for i in range(n - 1):
        p0, p1, p2, p3 = prof[max(i - 1, 0)], prof[i], prof[i + 1], prof[min(i + 2, n - 1)]
        out.append(p1)
        out.append((max(0.0, (-p0[0] + 9 * p1[0] + 9 * p2[0] - p3[0]) / 16), (-p0[1] + 9 * p1[1] + 9 * p2[1] - p3[1]) / 16))
    out.append(prof[-1])
    return out

def ball(kind, hexc, r, x, y, z, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    _emit(kind + '_' + hexc, bm, T(x, y, z) @ (rot or Matrix.Identity(4)))

def prism(kind, hexc, pts, depth, mat, bevel=0.1, segs=2):
    """a flat outline [(u, v), ...] drawn in the XZ plane and made `depth` thick along Y"""
    bm = bmesh.new()
    f = [bm.verts.new((u, -depth / 2, v)) for u, v in pts]
    b = [bm.verts.new((u, depth / 2, v)) for u, v in pts]
    n = len(pts)
    bm.faces.new(f); bm.faces.new(b[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((f[j], f[i], b[i], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _bev(bm, _sharp(bm), bevel, segs)
    _emit(kind + '_' + hexc, bm, mat)

def notch_box(kind, hexc, sx, sy, sz, x, y, z, nw, brow, depth, bevel=0.2, corner=0.6):
    """a box with a recess in its -Y face: `nw` wide, `depth` deep, from the underside up to `brow` below the top"""
    hx, hy, hz, n = sx / 2, sy / 2, sz / 2, nw / 2
    zt, yf, yr = hz - brow, -hy, -hy + depth
    bm = bmesh.new()
    V = lambda *c: bm.verts.new(c)
    F = lambda *vs: bm.faces.new(vs)
    a0, a1, a2, a3 = V(-hx, yf, -hz), V(hx, yf, -hz), V(hx, hy, -hz), V(-hx, hy, -hz)
    b0, b1, b2, b3 = V(-hx, yf, hz), V(hx, yf, hz), V(hx, hy, hz), V(-hx, hy, hz)
    r0, r1, r2, r3 = V(-n, yf, -hz), V(n, yf, -hz), V(n, yf, zt), V(-n, yf, zt)
    f0, f1, f2, f3 = V(-n, yr, -hz), V(n, yr, -hz), V(n, yr, zt), V(-n, yr, zt)
    F(b0, b1, b2, b3); F(a0, r0, f0, f1, r1, a1, a2, a3)
    F(a1, a2, b2, b1); F(a3, a0, b0, b3); F(a2, a3, b3, b2)
    F(a0, r0, r3, b0); F(r3, r2, b1, b0); F(r1, a1, b1, r2)
    F(r0, f0, f3, r3); F(f3, f2, r2, r3); F(f1, r1, r2, f2); F(f0, f1, f2, f3)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    outer = {a0, a1, a2, a3, b0, b1, b2, b3}
    _bev(bm, [e for e in bm.edges if e.verts[0] in outer and e.verts[1] in outer and abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-4], corner, 3)
    inside = lambda v: abs(v.co.x) <= n + 1e-4 and v.co.y <= yr + 1e-4
    _bev(bm, [e for e in _sharp(bm) if not (inside(e.verts[0]) and inside(e.verts[1]))], bevel, 2)
    _bev(bm, _sharp(bm), 0.05, 1)
    _emit(kind + '_' + hexc, bm, T(x, y, z))

# a fat pin, 3.2 tall, belly 0.6: (radius, height) up the side; and the band round its neck
PIN = [(0.34, 0.0), (0.44, 0.12), (0.54, 0.45), (0.595, 0.8), (0.60, 1.0), (0.57, 1.3), (0.48, 1.6), (0.37, 1.85),
       (0.31, 2.02), (0.285, 2.18), (0.30, 2.36), (0.355, 2.55), (0.40, 2.74), (0.405, 2.9), (0.34, 3.05), (0.2, 3.16), (0.0, 3.2)]
BAND = [(1.96, -0.5), (2.03, 1), (2.18, 1), (2.37, 1), (2.44, -0.5)]     # (height, how far it stands off the pin)

def pin(x, y, z0, kr=1.0, kz=1.0, segs=12, lean=None, fine=0, proud=0.05):
    def r_at(h):
        for (r0, h0), (r1, h1) in zip(PIN, PIN[1:]):
            if h0 <= h <= h1: return r0 + (r1 - r0) * (h - h0) / (h1 - h0)
    m = T(x, y, z0) @ (lean or Matrix.Identity(4))
    body, band = [(r * kr, h * kz) for r, h in PIN], [(r_at(h) * kr + d * proud, h * kz) for h, d in BAND]
    for _ in range(fine): body, band = finer(body), finer(band)
    lathe('plastic', PINW, body, m, segs=segs)
    lathe('plastic', PINK, band, m, segs=segs, cap=False)

def shoe(hexc, x, y, z0, yaw=0.0, segs=1):
    """one chunky shoe standing on z0, seen from the side: 1.8 long (its toe toward +X), 0.56 wide, 1.15 tall"""
    m = T(x, y, z0) @ RZ(yaw)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(1.8, 0.56, 0.2), verts=bm.verts)
    _emit('plastic_' + INK, bm, m @ T(0, 0, 0.1))
    side = [(-0.85, 0.0), (0.85, 0.0), (0.85, 0.42), (-0.02, 0.64), (-0.2, 1.0), (-0.85, 1.0)]
    prism('plastic', hexc, side, 0.5, m @ T(0, 0, 0.15), bevel=0.14, segs=segs)

# ------------------------------------------------------------------ bw_pins (deck 9 x 9 x 0.3, pins stand on it)
reset()
box('plastic', DARK, 9.0, 9.0, 0.3, 0, 0, 0.15, bevel=0.1)
for row in range(4):
    for i in range(row + 1):
        lean = None
        if (row, i) == (1, 1): lean = Matrix.Rotation(math.radians(13), 4, Vector((0.35, 1.0, 0)).normalized())   # this one is on its way over
        pin((i - row / 2) * 2.3, -3.0 + row * 2.0, 0.3, lean=lean)
flush('bw_pins')

# ------------------------------------------------------------------ bw_pinsetter (opening under it: x -5 .. 5, z 0 .. 4.2)
reset()
notch_box('plastic', 'ff4fd8', 14.0, 6.0, 2.8, 0, 0, 5.6, nw=11.2, brow=0.3, depth=0.5, bevel=0.2, corner=0.6)
box('plastic', INK, 11.3, 0.3, 2.53, 0, -2.6, 5.485, bevel=0.05)           # the score plate, a mesh of its own (its face is y -2.75)
for i in range(5):
    cyl('neon', LENS, 0.26, 0.3, (i - 2) * 2.2, -2.8, 4.62, axis='y', segs=12, bevel=0.06)
for s in (-1, 1):
    box('plastic', PALE, 1.85, 5.6, 3.9, s * 5.975, 0, 2.35, bevel=0.35)   # a cheek
    box('plastic', DARK, 2.0, 6.0, 0.7, s * 6.0, 0, 0.35, bevel=0.2)       # its foot
    box('plastic', YEL, 1.2, 0.3, 0.7, s * 5.975, -2.8, 3.3, bevel=0.12)
flush('bw_pinsetter')

# ------------------------------------------------------------------ bw_ballreturn (the hood is at +Y, the balls run toward -Y)
reset()
box('plastic', DARK, 3.6, 8.6, 0.5, 0, 0, 0.25, bevel=0.15)                              # the kick plinth
soft('plastic', PALE, 4.0, 9.0, 1.1, 0, 0, 0.85, r=0.5, pick='top', segs=3)              # the low body, top at 1.4
soft('plastic', PALE, 3.6, 2.3, 3.1, 0, 3.35, 1.85, r=1.4, pick='topy', segs=5, small=0.25)   # the hood
soft('plastic', INK, 2.4, 0.3, 1.8, 0, 2.2, 2.25, r=1.05, pick='topy', segs=4, small=0.05)    # its mouth
for s in (-1, 1):
    box('plastic', DARK, 0.5, 6.6, 0.7, s * 1.3, -0.9, 1.55, bevel=0.18)                 # the rack's side rails
box('plastic', DARK, 3.1, 0.5, 0.8, 0, -4.1, 1.6, bevel=0.18)                            # ...and its end stop
for k, c in enumerate((PINK, CYAN, YEL, GREEN)):
    ball('plastic', c, 0.85, 0, -3.0 + k * 1.72, 2.2, rot=RZ(k * 0.7))
flush('bw_ballreturn')

# ------------------------------------------------------------------ bw_booth (back of the U at +Y, table at y -1.5)
reset()
KEY = '37d6ff'
# the tub the cushions sit in: one U-shaped wall, 0.5 thick and 3.8 tall, its two back corners rounded
R = 0.9
arc = lambda cx, cy, a0: [(cx + R * math.cos(math.radians(a0 + 22.5 * k)), cy + R * math.sin(math.radians(a0 + 22.5 * k))) for k in range(5)]
TUB = [(-7, -3.3), (-6.5, -3.3), (-6.5, 3.5), (6.5, 3.5), (6.5, -3.3), (7, -3.3)] + arc(7 - R, 4 - R, 0) + arc(-7 + R, 4 - R, 90)
prism('plastic', DARK, TUB, 3.8, T(0, 0, 1.9) @ RX(-math.pi / 2), bevel=0.2)
box('plastic', INK, 8.4, 2.6, 0.9, 0, 2.3, 0.45, bevel=0.15)                             # the base under the back seat
for s in (-1, 1):
    soft('plastic', DARK, 3.1, 0.8, 2.0, s * 5.45, -3.6, 1.0, r=0.3, pick='top')         # an arm at the open end
    soft('plastic', KEY, 3.15, 0.9, 0.8, s * 5.425, -3.55, 2.25, r=0.36)                 # ...with a pad on it
    box('plastic', INK, 2.6, 7.0, 0.9, s * 5.3, 0.1, 0.45, bevel=0.15)                   # the base under a side seat
    for yc in (-1.47, 1.82):
        soft('plastic', KEY, 2.7, 3.26, 1.15, s * 5.15, yc, 1.425, r=0.38)               # side seat cushions
        soft('plastic', KEY, 0.9, 3.26, 2.4, s * 6.05, yc, 3.0, r=0.4)                   # side back cushions
    soft('plastic', KEY, 3.72, 2.7, 1.15, s * 1.89, 2.15, 1.425, r=0.38)                 # back seat cushions
for xc in (-3.72, 0, 3.72):
    soft('plastic', KEY, 3.66, 0.9, 2.4, xc, 3.05, 3.0, r=0.4)                           # back cushions
TY = -1.5
cyl('plastic', DARK, 1.3, 0.45, 0, TY, 0.225, segs=16, bevel=0.15)                       # the table: one fat foot
cyl('plastic', MID, 0.6, 2.6, 0, TY, 1.6, segs=12, bevel=0.1)
cyl('plastic', DARK, 1.9, 0.3, 0, TY, 2.75, segs=16, bevel=0.1)
cyl('plastic', PINW, 2.2, 0.5, 0, TY, 3.05, segs=16, bevel=0.18)
cyl('plastic', DARK, 0.5, 0.3, 0, TY, 3.42, segs=12, bevel=0.1)                          # a little table lamp
lathe('neon', WARM, [(0.42, 0), (0.42, 0.12), (0.36, 0.32), (0.22, 0.46), (0, 0.52)], T(0, TY, 3.55), segs=12)
flush('bw_booth')

# ------------------------------------------------------------------ bw_counter (counter y -4 .. 1, shoe wall y 2.5 .. 4)
reset()
box('plastic', DARK, 19.2, 4.3, 0.6, 0, -1.35, 0.3, bevel=0.15)                          # toe kick
box('plastic', PALE, 19.6, 4.7, 3.0, 0, -1.35, 2.0, bevel=0.35)                          # the counter's body
box('wood', LANE, 20.0, 5.0, 0.6, 0, -1.5, 3.7, bevel=0.2)                               # its top
for k, c in enumerate((PINK, YEL, CYAN)):
    x = (k - 1) * 6.3
    box('plastic', CARPET, 5.7, 0.3, 2.1, x, -3.72, 1.95, bevel=0.14)                    # three front panels
    cyl('plastic', c, 0.62, 0.3, x, -3.82, 1.95, axis='y', segs=14, bevel=0.1)           # ...each with a fat dot
# the bell
BX, BY = 6.6, -2.6
cyl('plastic', DARK, 0.85, 0.25, BX, BY, 4.12, segs=14, bevel=0.1)
lathe('plastic', YEL, [(0.72, 0), (0.72, 0.14), (0.64, 0.4), (0.46, 0.6), (0.24, 0.71), (0, 0.74)], T(BX, BY, 4.22), segs=14)
cyl('plastic', DARK, 0.2, 0.3, BX, BY, 5.06, segs=10, bevel=0.08)
# a pair somebody left on the counter
shoe(PINK, -6.4, -1.9, 4.0, yaw=0.12, segs=2)
shoe(PINK, -5.9, -2.9, 4.0, yaw=-0.3, segs=2)
# the shoe wall
WY = 3.25
box('plastic', DARK, 20.0, 1.5, 4.4, 0, WY, 2.2, bevel=0.2)                              # the cupboard under the shelves
box('plastic', INK, 19.4, 0.4, 5.4, 0, 3.8, 7.0, bevel=0.1)                              # the back
for s in (-1, 1): box('plastic', MID, 0.6, 1.5, 5.3, s * 9.7, WY, 6.85, bevel=0.18)      # the ends
box('plastic', MID, 20.0, 1.5, 0.6, 0, WY, 9.7, bevel=0.2)                               # the top
box('neon', WARM, 17.6, 0.45, 0.3, 0, 2.78, 9.32, bevel=0.1)                              # a lamp under it
for top in (6.2, 8.0): box('wood', LANE, 18.9, 1.4, 0.4, 0, WY + 0.02, top - 0.2, bevel=0.12)
COLS = (PINK, CYAN, YEL, PINW)
for r, z0 in enumerate((4.4, 6.2, 8.0)):
    for i in range(6):
        px = (i - 2.5) * 3.1
        shoe(COLS[(i + r) % 4], px - 0.28, 3.31, z0)                                      # each pair: one behind,
        shoe(COLS[(i + r) % 4], px + 0.28, 2.79, z0)                                      # one in front
flush('bw_counter')

# ------------------------------------------------------------------ bw_giantpin (the text plate faces -Y at y -4.5)
reset()
cyl('plastic', DARK, 4.35, 0.5, 0, 0, 0.25, segs=16, bevel=0.15)                         # the plinth: a dark step,
cyl('neon', CYAN, 4.5, 0.45, 0, 0, 0.675, segs=16, bevel=0.12)                           # the lit ring standing proud of it,
cyl('plastic', DARK, 4.25, 0.35, 0, 0, 1.0, segs=16, bevel=0.12)                         # another dark step
cyl('plastic', PALE, 3.9, 0.4, 0, 0, 1.2, segs=16, bevel=0.15)                           # and a pale top
box('plastic', PALE, 5.7, 1.2, 1.4, 0, -3.8, 0.7, bevel=0.2)                             # the block the plate sits on
box('plastic', INK, 5.0, 0.2, 1.0, 0, -4.4, 0.7, bevel=0.06)                             # the text plate, 5 x 1, a mesh of its own
for k in range(4):                                                                       # four fat uplights
    a = math.radians(45 + 90 * k)
    cyl('plastic', DARK, 0.55, 0.35, 3.05 * math.cos(a), 3.05 * math.sin(a), 1.52, segs=12, bevel=0.1)
    cyl('neon', WARM, 0.36, 0.2, 3.05 * math.cos(a), 3.05 * math.sin(a), 1.66, segs=12, bevel=0.06)
pin(0, 0, 1.4, kr=5.0, kz=4.5, segs=16, fine=1, proud=0.12)
STAR = [(rad * math.cos(a), rad * math.sin(a)) for rad, a in ((1.25 if k % 2 == 0 else 0.62, math.pi / 2 + k * math.pi / 5) for k in range(10))]
prism('neon', YEL, STAR, 0.7, T(0, 0, 16.2), bevel=0.12)
prism('neon', YEL, STAR, 0.7, T(0, 0, 16.2) @ RZ(math.pi / 2), bevel=0.12)
flush('bw_giantpin')
