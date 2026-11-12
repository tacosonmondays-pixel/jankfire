# The Backrooms' drop ceilings (shared/map.js backrooms(): the 4.2 m ceiling everywhere, the hall's at 9 m, and the
# render-only overlays that make some rooms flicker or go dark) as one Blender model over their own boxes:
#  - an exposed T-bar grid of 0.5 x 1 m lay-in tiles (2 x 4 ft, near enough; the grid is in the tile texture), cut tiles
#    at the walls like a real fit-out, the main runners every 0.5 m along z, cross tees every 1 m
#  - a recessed 2x4 troffer in the middle of every 4 m cell (where the old panels were): white sides, a prismatic lens
#    that glows. rooms that flicker keep flickering (their lenses and tiles take the br_*f1..3 materials, which
#    public/js/backrooms.js drives with the same flicker as before), dead rooms stay dead (grey lenses, tiles that don't glow)
#  - here and there a tile gone (black plenum behind, a duct crossing some), a tile hanging down by one edge, tiles
#    sagging with damp, water stains
#  - vertex AO from the walls
# Look only: tools/arch/gamehash.mjs is the same with or without it.
# run: node tools/blender/arch/brceil_dump.mjs
#      python3 tools/blender/arch/brceiltex.py
#      blender52 -b --python tools/blender/arch/make_backrooms_ceil.py [-- --no-ao] [-- --spots out.json]
import os, sys, math, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import archkit
from archkit import Kit, OUTDIR, MATS, NOCAST, KIT
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
KIT.update({'br_ceil': {'tile': 1.0}, 'br_lens': {'tile': 1.0}, 'br_cstain': {'tile': 1.0}})  # (brceiltex.py TILES)
GL = '#7c7666'  # the tiles' own glow: light bouncing round the room (the old ceiling texture glowed this much)
MATS.update({
    'br_ceil': ('br_ceil', '#ffffff', {'glow': True, 'glowcol': GL}), 'br_ceildark': ('br_ceil', '#b0aa98', {}),
    'br_ceilf1': ('br_ceil', '#ffffff', {'glow': True, 'glowcol': GL}), 'br_ceilf2': ('br_ceil', '#ffffff', {'glow': True, 'glowcol': GL}),
    'br_ceilf3': ('br_ceil', '#ffffff', {'glow': True, 'glowcol': GL}),
    'br_lens': ('br_lens', '#ffffff', {'glow': True, 'glowcol': '#fff2d2'}), 'br_lensdead': ('br_lens', '#8a8676', {}),
    'br_lensf1': ('br_lens', '#ffffff', {'glow': True, 'glowcol': '#fff2d2'}), 'br_lensf2': ('br_lens', '#ffffff', {'glow': True, 'glowcol': '#fff2d2'}),
    'br_lensf3': ('br_lens', '#ffffff', {'glow': True, 'glowcol': '#fff2d2'}),
    'br_trof': ('trim', '#f6f2e6', {'glow': True, 'glowcol': '#a8a290'}),
    'br_void': ('tar', '#1c1812', {}), 'br_duct': ('metalplate', '#8c8c88', {}), 'br_tileback': ('stucco', '#8a7e64', {}),
    'br_cstain': ('br_cstain', '#ffffff', {'alpha': True, 'decal': True}),
})
NOCAST.update(k for k in list(MATS) if k.startswith('br_'))  # (a ceiling casts no sun shadow down here)

_mm = archkit.make_material
def _make_material(name):  # (extras 'decal': the game pulls it toward the camera, so it can lie right on the tile)
    m = _mm(name)
    if MATS[name][2].get('decal'): m['decal'] = 1
    return m
archkit.make_material = _make_material

H, HH, HALL, O, N, U = 4.2, 9.0, 32.0, -120.0, 60, 4.0
R = random.Random(4242)
D = json.load(open(os.path.join(HERE, 'boxes', 'backrooms_ceil.json')))
K = Kit(D)
K.extra_occ = [(tuple(b['min']), tuple(b['max'])) for b in D['walls']]  # the walls darken the ceiling next to them
WALLS = K.extra_occ
WG = {}
for i, (mn, mx) in enumerate(WALLS):
    for gx in range(int(math.floor(mn[0] / 4)), int(math.floor(mx[0] / 4)) + 1):
        for gz in range(int(math.floor(mn[2] / 4)), int(math.floor(mx[2] / 4)) + 1): WG.setdefault((gx, gz), []).append(i)


def hits_wall(x0, z0, x1, z1, y):
    """does a ceiling rect touch a wall that goes up through the ceiling there?"""
    for gx in range(int(math.floor((x0 - 0.2) / 4)), int(math.floor((x1 + 0.2) / 4)) + 1):
        for gz in range(int(math.floor((z0 - 0.2) / 4)), int(math.floor((z1 + 0.2) / 4)) + 1):
            for i in WG.get((gx, gz), ()):
                mn, mx = WALLS[i]
                if mx[1] >= y - 1e-3 and mn[0] < x1 + 0.03 and mx[0] > x0 - 0.03 and mn[2] < z1 + 0.03 and mx[2] > z0 - 0.03: return True
    return False


def in_hall(x, z): return -HALL < x < HALL and -HALL < z < HALL


# which light each cell has: the overlays are whole rooms (or a stretch of a hall)
KIND = {}
for b in D['lights']:
    k = {'ceilflick': 'f1', 'ceilflick2': 'f2', 'ceilflick3': 'f3', 'ceildark': 'dark'}[b['mat']]
    for i in range(N):
        for j in range(N):
            cx, cz = O + (i + 0.5) * U, O + (j + 0.5) * U
            if b['min'][0] < cx < b['max'][0] and b['min'][2] < cz < b['max'][2]: KIND[(i, j)] = k


def rsub(rs, c):
    out = []
    for r in rs:
        if c[2] <= r[0] + 1e-5 or c[0] >= r[2] - 1e-5 or c[3] <= r[1] + 1e-5 or c[1] >= r[3] - 1e-5: out.append(r); continue
        if c[0] > r[0]: out.append((r[0], r[1], c[0], r[3]))
        if c[2] < r[2]: out.append((c[2], r[1], r[2], r[3]))
        a, b = max(r[0], c[0]), min(r[2], c[2])
        if c[1] > r[1]: out.append((a, r[1], b, c[1]))
        if c[3] < r[3]: out.append((a, c[3], b, r[3]))
    return [r for r in out if r[2] - r[0] > 1e-4 and r[3] - r[1] > 1e-4]


DOWN, UP = Vector((0, -1, 0)), Vector((0, 1, 0))


def fq(pts, mat, want, uv=None):
    p = [Vector(q) for q in pts]
    if (p[1] - p[0]).cross(p[2] - p[0]).dot(want) < 0: pts = pts[::-1]; uv = uv[::-1] if uv else None
    K.quad(pts, mat, uv=uv)


def flat(x0, z0, x1, z1, y, mat, want=DOWN, uv=None):
    fq([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], mat, want, uv=uv)


def well(x0, z0, x1, z1, y0, y1, mat):
    """the four inner sides of a hole from y0 up to y1, facing in"""
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    for (a, b) in (((x0, z0), (x1, z0)), ((x1, z0), (x1, z1)), ((x1, z1), (x0, z1)), ((x0, z1), (x0, z0))):
        m = Vector(((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2)); want = Vector((cx, 0, cz)) - m
        fq([(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], mat, want.normalized())


WHERE = {}
counts = {}
def note(k, p): counts[k] = counts.get(k, 0) + 1; WHERE.setdefault(k, []).append(p)


# ------------------------------------------------------------ cells: the tiles' plane (with holes), the troffer
def tile_slots(cx, cz):
    """the cell's whole tiles (0.5 x 1 m, on the grid): x edges at 0.25 + 0.5 k, z edges at 0.5 + k"""
    out = []
    x0, z0 = cx - 2, cz - 2
    for a in range(1, 8):
        for b in range(1, 4):
            tx, tz = x0 + 0.25 + 0.5 * (a - 1), z0 + 0.5 + (b - 1)
            if abs(tx + 0.25 - cx) < 0.01 and abs(tz + 0.5 - cz) < 0.01: continue  # (the troffer's slot)
            out.append((tx, tz, tx + 0.5, tz + 1.0))
    return out


def cell(i, j, y, hall):
    cx, cz = O + (i + 0.5) * U, O + (j + 0.5) * U
    kind = 'n' if hall else KIND.get((i, j), 'n')
    pm = {'n': 'br_ceil', 'dark': 'br_ceildark', 'f1': 'br_ceilf1', 'f2': 'br_ceilf2', 'f3': 'br_ceilf3'}[kind]
    lm = {'n': 'br_lens', 'dark': 'br_lensdead', 'f1': 'br_lensf1', 'f2': 'br_lensf2', 'f3': 'br_lensf3'}[kind]
    tx0, tz0, tx1, tz1 = cx - 0.25, cz - 0.5, cx + 0.25, cz + 0.5
    holes = [(tx0, tz0, tx1, tz1)]
    # the troffer: white sides up to the lens, 8 cm up
    well(tx0, tz0, tx1, tz1, y, y + 0.08, 'br_trof')
    flat(tx0, tz0, tx1, tz1, y + 0.08, lm, uv=[(0, 1), (1, 1), (1, 0), (0, 0)])
    # a tile or two gone wrong, now and then (not in the hall: up at 9 m nobody would see it, and not touching a wall)
    if not hall:
        slots = [s for s in tile_slots(cx, cz) if not hits_wall(s[0], s[1], s[2], s[3], y)]
        R.shuffle(slots)
        r = R.random()
        if slots and r < 0.018: holes.append(slots[0]); missing(slots[0], y, R.random() < 0.4)
        elif slots and r < 0.026: holes.append(slots[0]); hanging(slots[0], y, pm)
        elif slots and r < 0.06: holes.append(slots[0]); sag(slots[0], y, pm)
        if slots and R.random() < 0.09:
            s = slots[-1]; w = 0.35 + R.random() * 0.15; ccx, ccz = (s[0] + s[2]) / 2 + (R.random() - 0.5) * 0.08, (s[1] + s[3]) / 2 + (R.random() - 0.5) * 0.3
            c = (0.0, 0.5) if R.random() < 0.7 else (0.5, 1.0)
            fl = R.random() < 0.5
            flat(ccx - w / 2, ccz - w, ccx + w / 2, ccz + w, y - 0.0012, 'br_cstain', uv=[(c[1] if fl else c[0], 1), (c[0] if fl else c[1], 1), (c[0] if fl else c[1], 0), (c[1] if fl else c[0], 0)])
            note('stain', (ccx, y, ccz))
    rs = [(cx - 2, cz - 2, cx + 2, cz + 2)]
    for h in holes: rs = rsub(rs, h)
    for (x0, z0, x1, z1) in rs: flat(x0, z0, x1, z1, y, pm)


def missing(s, y, duct):
    x0, z0, x1, z1 = s
    well(x0, z0, x1, z1, y, y + 0.28, 'br_void')
    flat(x0, z0, x1, z1, y + 0.28, 'br_void')
    if duct:  # a round flex duct crossing the gap, a hand's width above the grid
        cz, r, cyy = (z0 + z1) / 2 + (R.random() - 0.5) * 0.4, 0.11, y + 0.16
        seg = 8
        for k in range(seg):
            a0, a1 = k / seg * math.tau, (k + 1) / seg * math.tau
            p = lambda x, a: (x, cyy + r * math.sin(a), cz + r * math.cos(a))
            fq([p(x0 + 0.002, a0), p(x1 - 0.002, a0), p(x1 - 0.002, a1), p(x0 + 0.002, a1)], 'br_duct',
               Vector((0, math.sin((a0 + a1) / 2), math.cos((a0 + a1) / 2))))
    note('missing', ((x0 + x1) / 2, y, (z0 + z1) / 2))


def hanging(s, y, pm):
    """the tile's fallen out of its slot on one long side and hangs off the T-bar by the other"""
    x0, z0, x1, z1 = s
    missing(s, y, False)
    ang = math.radians(28 + R.random() * 35)
    hinge = x0 if R.random() < 0.5 else x1; sg = 1 if hinge == x0 else -1
    w = (x1 - x0) * 0.98; dx, dy = sg * w * math.cos(ang), -w * math.sin(ang)
    th = 0.016
    P = [(hinge, y - 0.006, z0 + 0.01), (hinge + dx, y - 0.006 + dy, z0 + 0.01), (hinge + dx, y - 0.006 + dy, z1 - 0.01), (hinge, y - 0.006, z1 - 0.01)]
    n = Vector((dx, dy, 0)).cross(Vector((0, 0, 1))).normalized()
    if n.y > 0: n = -n
    fq(P, pm, n)
    Q = [tuple(Vector(p) - n * th) for p in P]
    fq(Q, 'br_tileback', -n)
    for a, b in ((0, 1), (1, 2), (2, 3)):  # the edges
        e = (Vector(P[b]) - Vector(P[a])).cross(n).normalized()
        fq([P[a], P[b], Q[b], Q[a]], 'br_tileback', -e if e.dot(Vector(P[a]) - Vector(((x0 + x1) / 2, y, (z0 + z1) / 2))) < 0 else e)
    note('hanging', ((x0 + x1) / 2, y, (z0 + z1) / 2))


def sag(s, y, pm):
    """a tile gone soft with damp and bowed down in the middle, a stain where it's wettest"""
    x0, z0, x1, z1 = s
    d = 0.04 + R.random() * 0.05
    nx, nz = 3, 5
    def at(a, b):
        x, z = x0 + (x1 - x0) * a / nx, z0 + (z1 - z0) * b / nz
        return (x, y - d * math.sin(math.pi * a / nx) * math.sin(math.pi * b / nz), z)
    for a in range(nx):
        for b in range(nz):
            fq([at(a, b), at(a + 1, b), at(a + 1, b + 1), at(a, b + 1)], pm, DOWN)
    # its edges show where it pulled away from the grid
    for a in range(nx):
        for (b, zz) in ((0, z0), (nz, z1)):
            p0, p1 = at(a, b), at(a + 1, b)
            fq([p0, p1, (p1[0], y, zz), (p0[0], y, zz)], 'br_tileback', Vector((0, 0, 1 if b == 0 else -1)))
    for b in range(nz):
        for (a, xx) in ((0, x0), (nx, x1)):
            p0, p1 = at(a, b), at(a, b + 1)
            fq([p0, p1, (xx, y, p1[2]), (xx, y, p0[2])], 'br_tileback', Vector((1 if a == 0 else -1, 0, 0)))
    w = (x1 - x0) * 0.42; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    yb = y - d * 0.95 - 0.0012
    flat(cx - w, cz - w * 1.4, cx + w, cz + w * 1.4, yb, 'br_cstain', uv=[(0, 1), (0.5, 1), (0.5, 0), (0, 0)])
    note('sag', (cx, y, cz))


for i in range(N):
    for j in range(N):
        cx, cz = O + (i + 0.5) * U, O + (j + 0.5) * U
        cell(i, j, HH if in_hall(cx, cz) else H, in_hall(cx, cz))


# (the T-bar grid itself is in the br_ceil texture: drawn as 240 m strips it sparkled through the walls, and cut into
# 4 m pieces it cost 86k triangles for a 6 mm lip nobody sees. what has real depth is modelled: the troffers' recess, the
# holes, the hanging and sagging tiles)
print('stuff', counts)
if '--spots' in argv:
    json.dump({k: v[:12] for k, v in WHERE.items()}, open(argv[argv.index('--spots') + 1], 'w'))


def zcheck_fast(limit=12):
    bad = 0
    for kk, lst in getattr(K, '_planes', {}).items():
        lst = sorted(lst, key=lambda e: e[0][0]); act = []
        for e in lst:
            act = [q for q in act if q[0][2] > e[0][0] + 0.002]
            for q in act:
                a, b = q[0], e[0]
                if min(a[2], b[2]) - max(a[0], b[0]) > 0.002 and min(a[3], b[3]) - max(a[1], b[1]) > 0.002 and q[1] != e[1]:
                    bad += 1
                    if bad <= limit: print('ZFIGHT', 'xyz'[kk[0]], kk[1], q[1], q[2], '<->', e[1], e[2])
            act.append(e)
    print('zfight pairs:', bad)
    return bad


K.zcheck = zcheck_fast
K.finish(os.path.join(OUTDIR, 'backrooms_ceil.glb'), ao='--no-ao' not in argv)
