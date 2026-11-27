# SPOOKY FOREST for Roblox (18 Nov 2026): the kit for the layout in forest_layout.py (the web's "Scary Forest", cropped).
# The owner: "We need more map variety ... bring back spooky forest and back room!!".
# A pine wood at night by a lake, in our chunky style: stylised pines from a few rounded tiers, white birches, grey dead
# trees, rounded boulders, a log cabin built from round logs, a timber lookout tower, a lattice radio mast in muted red and
# white, a rusted sedan, a dock. Flat colours in mid values (night light is dim: dark paint would go black), greens and
# bark browns, one accent (the mast's red). Warm light only where something makes it: the cabin's lamp through its
# windows and the porch light, the camp lantern, the car's hazards, the lookout's lamp, a lamp at the dock's end, the
# mast's red beacons. No text, no logos, no marks on the ground but the trails' own worn earth.
#
# run: blender -b --factory-startup -P tools/roblox/forest_models.py -- <out_dir> [preview_dir] [--no-glb] [--no-preview] [--day] [--views=a,b]
#   writes <out_dir>/forest.glb and roblox/studio-tools/ForestLayout.luau
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
import arenakit as K
from arenakit import B, Bc, cyl, cylx, cylz, lathe, blob, sphere, plate, light, Tr, Ry
import forest_layout as L

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_forest')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
os.makedirs(OUT_DIR, exist_ok=True)
LAYOUT = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'studio-tools', 'ForestLayout.luau'))
INFO = dict(name='Forest', title='SPOOKY FOREST', look='forest', mapId='forest', kit='forest',
            about='the web map "forest" (Scary Forest), cropped to its middle',
            origin=(0, 0, -42000), killY=-150, centreX=0, maxTeam=0)
rnd = random.Random(6660)
S, D, C = K.S, L.D, L.COL

# ---------------------------------------------------------------- palette (mid values: night light is dim)
GROUND, GROUND2, TRAIL = '6f6953', '6f6953', '776e59'
PINE = ['587752', '4f6c4b', '62805a']
PINE_FAR = ['4c6449', '536b4e']
BARK, BARK2, DEAD, BIRCH, BIRCHBAND, BIRCHLEAF = '6c5948', '614f42', '8e8a84', 'dcd8d0', '55524d', '7d905e'
FERN, BUSH, BUSH2 = '5e7a4b', '587049', '62784f'
LOG, LOGEND, PLANK, PLANK2 = '7b6047', 'b39572', '8a7056', '7d6550'
ROOF, ROOF2 = '625e59', '6e6964'
STONE, STONE2 = '8f8a82', '7f7a73'
ROCK, MOSS = '87847b', '6f7a60'
TOWER = '7c6b56'
MUD, MUD2, BED = '5d5547', '544d41', '48463f'
WARM, WARM2 = 'ffcf8c', 'ffb870'
RED_LAMP = 'ff5a46'

def M_of(p0, p1):
    """a frame at p0 whose +x points at p1 (for bars in any direction)"""
    d = Vector(p1) - Vector(p0)
    q = d.to_track_quat('X', 'Z' if abs(d.normalized().z) < 0.95 else 'Y')
    return Tr(*p0) @ q.to_matrix().to_4x4(), d.length

def bar(m, col, p0, p1, t=0.3, kind='plastic'):
    M, ln = M_of(p0, p1)
    if ln < 1e-3: return
    B(m, col, 0, -t / 2, -t / 2, ln, t / 2, t / 2, bev=0.0, kind=kind, M=M)

def ocyl(m, col, x, y0, z, r, h, segs=7, r2=None):
    """an open cylinder (no caps: trunks start under the ground and end inside a canopy)"""
    bm = bmesh.new()
    r2 = r if r2 is None else r2
    lo = [bm.verts.new((r * math.cos(2 * math.pi * k / segs), 0, r * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
    hi = [bm.verts.new((r2 * math.cos(2 * math.pi * k / segs), h, r2 * math.sin(2 * math.pi * k / segs))) for k in range(segs)]
    for k in range(segs):
        j = (k + 1) % segs
        bm.faces.new((lo[k], lo[j], hi[j], hi[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    K.put(m, 'plastic', col, bm, Tr(x, y0, z))

# ================================================================ the ground: the web's heightfield, smooth, every 2 m
T = L.T
TX0, TZ0, TNX, TNZ = L.TX0, L.TZ0, L.TNX, L.TNZ
def noise2(x, z):
    return (math.sin(x * 0.021 + 1.3) * math.cos(z * 0.027 - 0.4) + 0.6 * math.sin(x * 0.053 + z * 0.041 + 2.0))

def ground():
    STEP = 2
    vs = {}
    bms = {GROUND: bmesh.new(), GROUND2: bmesh.new()}
    dev = 0.0
    def v(bm, i, j):
        k = (id(bm), i, j)
        if k not in vs: vs[k] = bm.verts.new((L.lx(TX0 + i), L.h2(i, j) * S + 0.03, L.lz(TZ0 + j)))
        return vs[k]
    for i in range(0, TNX, STEP):
        for j in range(0, TNZ, STEP):
            i2, j2 = min(TNX, i + STEP), min(TNZ, j + STEP)
            cx, cz = L.lx(TX0 + (i + i2) / 2), L.lz(TZ0 + (j + j2) / 2)
            col = GROUND
            bm = bms[col]
            bm.faces.new((v(bm, i, j), v(bm, i, j2), v(bm, i2, j2), v(bm, i2, j)))
            # (how far the 2 m surface strays from the 1 m one in its middle)
            if i2 - i == 2 and j2 - j == 2:
                mid = (L.h_at(i, j) + L.h_at(i2, j) + L.h_at(i, j2) + L.h_at(i2, j2)) / 4
                dev = max(dev, abs(mid - L.h_at(i + 1, j + 1)) * S)
    for col, bm in bms.items():
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            if f.normal.y < 0: f.normal_flip()
        K.put('fo_ground', 'plastic', col, bm)
    print('GROUND: the 2 m surface (which the hit boxes follow) is at most %.2f studs off the web 1 m one' % dev)
    # the flat forest floor round the shaped part, out to the kit's edge (the web's own ground there is flat)
    ex0, ex1, ez0, ez1 = L.lx(TX0), L.lx(TX0 + TNX), L.lz(TZ0), L.lz(TZ0 + TNZ)
    for (a0, c0, a1, c1) in ((-900, -900, L.SHORE, ez0), (-900, ez1, L.SHORE, 900), (-900, ez0, ex0, ez1)):
        B('fo_ground', GROUND, a0, -1.0, c0, a1, 0.0, c1, bev=0.0, flat=True)
    # the trails: the web's worn paths (flat ground there), a hair over it, the earth's own tone
    for i, b in enumerate(bb for bb in D['deco'] if bb['mat'] == 'trail'):
        cx, cz = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2
        sx, sz = (b['max'][0] - b['min'][0]), (b['max'][2] - b['min'][2])
        a = b.get('rot', 0.0)
        # (each a hair higher than the last, as the web does: where trails cross, no two share a plane)
        Bc('fo_ground', TRAIL, L.lx(cx), 0.08 + (i % 9) * 0.025, L.lz(cz), sx * S, 0.04, sz * S, bev=0.0, yaw=a)

# ================================================================ the lake: a bed that shelves away, the far shore
def lake():
    m = 'fo_lake'
    X, Z, P = L.X_EDGE, L.Z_EDGE, 30.0
    cols = [MUD, MUD2, BED, BED]
    for k, (xa, xb, top, _) in enumerate(L.SHELVES):
        xb2 = 680.0 if k == len(L.SHELVES) - 1 else xb
        B(m, cols[k], xa, top - 2.0, -900, xb2, top, 900, bev=0.0, flat=True)
    # the far shore: a strip of forest floor, its woods (trees()) and the water up to it
    B(m, GROUND, 672, -1.0, -900, 900, 0.6, 900, bev=0.0, flat=True)
    B(m, MUD, 664, -3.0, -900, 676, -0.4, 900, bev=0.0, flat=True)
    # reeds along the shore (the web's)
    for b in D['deco']:
        if b['mat'] != 'reed': continue
        cx, cz = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2
        h = (b['max'][1] - b['min'][1]) * S
        x, z = L.lx(cx), L.lz(cz)
        if abs(z) > 880: continue
        for k in range(2):
            a = rnd.random() * 6.28
            ox, oz = 0.5 * math.cos(a), 0.5 * math.sin(a)
            bar('fo_reeds', '7d7a5a', (x + ox, -1.2, z + oz), (x + ox * 1.6 + 0.3, -1.2 + h * (0.8 + 0.3 * rnd.random()), z + oz * 1.6), t=0.22)

# ================================================================ trees
def pine(m, x, y, z, ht, r0, col, tiers=3, segs=7, trunk_r=0.9, tsegs=7, simple=False):
    yb = y + ht * 0.3
    span = ht - ht * 0.3
    if trunk_r > 0:
        ocyl('fo_trunks' if m == 'fo_trees' else m, BARK, x, y - 1.5, z, trunk_r, ht * 0.62 + 1.5, segs=tsegs, r2=trunk_r * 0.6)
    for k in range(tiers):
        f = k / max(1, tiers - 1) if tiers > 1 else 0
        y0 = yb + k * span * (0.6 / max(1, tiers - 1)) if tiers > 1 else yb
        th = span * (0.5 if tiers > 2 else 0.62)
        r = r0 * (1.0 - f * 0.55)
        prof = [(0, y0 - 0.4), (r, y0 + th * 0.1), (r * 0.82, y0 + th * 0.3), (0, y0 + th + (0.6 if k == tiers - 1 else 0))]
        if simple: prof = [(0, y0 - 0.4), (r, y0 + th * 0.1), (0, y0 + th)]
        lathe(m, col, prof, x, 0, z, segs=segs)

def birch(x, y, z, ht, yaw):
    m = 'fo_birch'
    ocyl(m, BIRCH, x, y - 1.0, z, 0.62, ht * 0.85 + 1.0, segs=8, r2=0.45)
    for k, hh in enumerate((0.26, 0.55)):
        ocyl(m, BIRCHBAND, x, y + ht * hh, z, 0.64, 0.4, segs=8)
    for k in range(2):
        a = yaw + k * 2.4
        rr = 1.6 if k else 0.4
        blob('fo_leaves', BIRCHLEAF, x + rr * math.cos(a), y + ht * (0.72 + 0.12 * k), z + rr * math.sin(a), 3.6 - k * 0.8, sy=0.7, sub=1)

def dead(x, y, z, ht, yaw, branches=True):
    m = 'fo_dead'
    ocyl(m, DEAD, x, y - 1.0, z, 0.85, ht + 1.0, segs=6, r2=0.45)
    for k in range(3 if branches else 0):
        a = yaw + k * 1.7 + 0.3
        yy = y + ht * (0.45 + k * 0.12)
        ln = (3.6 + 2.0 * ((k * 7) % 3) / 2) * (1 - k * 0.12)
        p0 = (x, yy, z); p1 = (x + ln * math.cos(a), yy + 0.8, z + ln * math.sin(a))
        bar(m, DEAD, p0, p1, t=0.42)
        bar(m, DEAD, p1, (p1[0], p1[1] + 2.2, p1[2]), t=0.34)

def trees():
    cleared = L.CLEARED
    n = {'play': 0, 'band': 0, 'far': 0}
    def skip(wx, wz):
        return any(abs(wx - cx) < 0.3 and abs(wz - cz) < 0.3 for (cx, cz) in cleared)
    for p in D['props']:
        kind = p['id']
        if kind not in ('pine', 'birch', 'deadtree'): continue
        wx, wy, wz = p['a']
        if skip(wx, wz): continue
        x, y, z = L.lx(wx), wy * S, L.lz(wz)
        ht = p['hi'][1] * S
        r0 = max(p['hi'][0], p['hi'][2]) * S
        yaw = p.get('y', 0.0)
        where = 'play' if L.in_crop(wx, wz) else ('band' if L.in_crop(wx, wz, 16) else 'far')
        n[where] += 1
        if kind == 'pine':
            tw = 0.9
            if where == 'play':
                pine('fo_trees', x, y, z, ht, r0, PINE[int(abs(wx * 7 + wz * 3)) % 3], tiers=3, segs=7, trunk_r=tw)
            elif where == 'band':
                pine('fo_trees', x, y, z, ht, r0, PINE[int(abs(wx * 7 + wz * 3)) % 3], tiers=2, segs=6, trunk_r=tw, tsegs=5)
            else:
                pine('fo_far', x, y, z, ht, r0, PINE_FAR[int(abs(wx + wz)) % 2], tiers=2, segs=6, trunk_r=0.8, tsegs=4, simple=True)
        elif kind == 'birch':
            birch(x, y, z, p['hi'][1] * S, yaw)
        else:
            dead(x, y, z, p['hi'][1] * S * 0.95, yaw, branches=(where != 'far'))
    # the woods past the edge (the web's render-only pines), thinned with distance; the far shore's tree line
    kept = 0
    for p in D['decoProps']:
        if p['id'] != 'pine': continue
        wx, wy, wz = p['a']
        x, z = L.lx(wx), L.lz(wz)
        if abs(x) > 960 or abs(z) > 940: continue
        far_shore = wx > 200
        dx = max(0.0, abs(x) - L.X_EDGE) if x < 0 else 0.0
        dz = max(0.0, abs(z) - L.Z_EDGE)
        d = math.hypot(dx, dz)
        keep = 0.85 if d < 150 else (0.42 if d < 330 else 0.2)
        if far_shore: keep = 0.6
        if rnd.random() > keep: continue
        kept += 1
        ht = p['hi'][1] * S
        pine('fo_far', x, wy * S, z, ht, max(p['hi'][0], p['hi'][2]) * S, PINE_FAR[kept % 2], tiers=2, segs=5, trunk_r=0.0, simple=True)
    print('TREES: play %d, band %d, far %d, woods past the edge %d' % (n['play'], n['band'], n['far'], kept))

def undergrowth():
    """the web's ferns and bushes (only drawn: bullets go through, eyes don't), near the play area"""
    nf = nb = 0
    for p in D['decoProps']:
        if p['id'] not in ('fern', 'bush'): continue
        wx, wy, wz = p['a']
        if not L.in_crop(wx, wz, 16): continue
        x, y, z = L.lx(wx), wy * S, L.lz(wz)
        s = max(p['hi'][0], p['hi'][2]) * S
        a = p.get('y', 0.0)
        if p['id'] == 'fern':
            nf += 1
            for k in range(3):
                Bc('fo_brush', FERN, x, y + s * 0.18, z, s * 1.6, s * 0.4, 0.25, bev=0.0, yaw=a + k * 1.05)
        else:
            nb += 1
            blob('fo_brush', BUSH if nb % 2 else BUSH2, x, y + s * 0.35, z, s * 0.9, sy=0.62, sub=1)
    print('UNDERGROWTH: ferns %d, bushes %d' % (nf, nb))

# ================================================================ the web's boxes, dressed
def disc_or_log(m, col, b, endcol=None):
    """a box that is a log (long one way) or a disc (thin one way): the round thing it stands for"""
    x0, y0, z0, x1, y1, z1 = b
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    big = max(sx, sy, sz)
    if sy == big and sy > 2.5 * max(sx, sz):           # an upright post
        cyl(m, col, cx, y0, cz, max(sx, sz) / 2 * 1.05, sy, segs=8, bev=0.0); return
    if sx == big:
        cylx(m, col, x0, x1, cy, cz, min(sy, sz) / 2, segs=10, bev=0.0)
    elif sz == big:
        cylz(m, col, z0, z1, cx, cy, min(sx, sy) / 2, segs=10, bev=0.0)
    else:
        B(m, col, *b, bev=0.15)

def thin_axis(b):
    s = (b[3] - b[0], b[4] - b[1], b[5] - b[2])
    return s.index(min(s)), s

def logwall(b):
    """a log wall: round logs stacked along its length, their ends past the corners"""
    m = 'fo_cabin'
    x0, y0, z0, x1, y1, z1 = b
    along_x = (x1 - x0) >= (z1 - z0)
    th = min(x1 - x0, z1 - z0)
    r = th * 0.62
    n = max(1, int(round((y1 - y0) / (r * 1.75))))
    step = (y1 - y0) / n
    for k in range(n):
        yy = y0 + step * (k + 0.5)
        col = LOG if k % 2 == 0 else '735a43'
        if along_x: cylx(m, col, x0 - 0.5, x1 + 0.5, yy, (z0 + z1) / 2, r, segs=8, bev=0.0)
        else: cylz(m, col, z0 - 0.5, z1 + 0.5, (x0 + x1) / 2, yy, r, segs=8, bev=0.0)

def chainlink(b):
    """a chain-link run: rails top and bottom, the mesh as a diamond lattice"""
    m = 'fo_fence'
    x0, y0, z0, x1, y1, z1 = b
    along_x = (x1 - x0) >= (z1 - z0)
    c = (z0 + z1) / 2 if along_x else (x0 + x1) / 2
    a0, a1 = (x0, x1) if along_x else (z0, z1)
    P = lambda u, y: (u, y, c) if along_x else (c, y, u)
    for yy in (y0 + 0.25, y1):
        bar(m, '8d9196', P(a0, yy), P(a1, yy), t=0.28)
    h = y1 - y0
    u = a0 - h
    while u < a1:
        for sgn in (1, -1):
            ua, ub = (u, u + h) if sgn > 0 else (u + h, u)
            # clip the diagonal to the run
            pa, pb = [ua, y0], [ub, y1]
            for q in (pa, pb):
                pass
            t0, t1 = 0.0, 1.0
            du = ub - ua
            if abs(du) > 1e-6:
                for lim, lo in ((a0, True), (a1, False)):
                    t = (lim - ua) / du
                    if (du > 0) == lo: t0 = max(t0, t)
                    else: t1 = min(t1, t)
            if t1 - t0 > 0.02:
                bar(m, 'a3a7ab', P(ua + du * t0, y0 + h * t0), P(ua + du * t1, y0 + h * t1), t=0.13)
        u += 2.2

def rock(m, col, b, seed, sub=2):
    """a boulder over a box: a lumpy rounded mass a little bigger than the box, its foot sunk into the ground"""
    bm, M = rock_mesh(b, seed, sub)
    K.put(m, 'plastic', col, bm, M)

def rock_mesh(b, seed, sub=2):
    x0, y0, z0, x1, y1, z1 = b
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    r = random.Random(seed)
    ph = [r.random() * 6.28 for _ in range(4)]
    for v in bm.verts:
        d = v.co.normalized()
        n = 0.09 * math.sin(3.1 * d.x + ph[0]) * math.cos(2.7 * d.z + ph[1]) + 0.06 * math.sin(5.3 * d.y + ph[2]) + 0.05 * math.cos(4.1 * (d.x + d.z) + ph[3])
        v.co = d * (1.0 + n)
        v.co.x *= sx * 0.58; v.co.y *= sy * 0.62; v.co.z *= sz * 0.58
        if v.co.y < -sy * 0.3: v.co.y = -sy * 0.3 - (v.co.y + sy * 0.3) * 0.2     # (a flatter foot)
    return bm, Tr((x0 + x1) / 2, y0 + sy * 0.42, (z0 + z1) / 2)

def rocks(items):
    """the web's boulders (a big block, a smaller one on it, a mossy one shoved against them: touching boxes are one
    boulder), standing stones (one tall box), the camp's ring stones. which boxes make one boulder, its seed and its
    detail: forest_layout.rock_groups (19 Nov 2026: the boulders' hit shapes are made from the same list)"""
    for (bb, mat, seed, sub) in L.rock_groups(items):
        rock('fo_rocks', ROCK if mat == 'rockf' else MOSS, bb, seed, sub=sub)

# the broken-down car (27 Nov 2026, the vehicles pass: "Can the vehicles on all maps be made a bit better?"): the web
# game's own sedan over the web car's boxes (broken_car below); --box-car brings back the old dressed boxes
WEB_CAR = '--box-car' not in K.FLAGS
CAR_REGION = (L.lx(-10.45), -1.0, L.lz(55.0), L.lx(-5.55), 7.0, L.lz(58.4))    # (local studs: the car's boxes)
CAR_MATS = ('carrust', 'glassdark', 'chrome', 'tire', 'hazard2')
def in_car(b):
    r = CAR_REGION
    return r[0] - 0.01 <= b[0] and b[3] <= r[3] + 0.01 and r[2] - 0.01 <= b[2] and b[5] <= r[5] + 0.01 and b[4] <= r[4]

def dress():
    tents = {}
    rocks_in = []
    for (b, mat, w) in L.KEPT:
        if w.get('pv') in ('pine', 'birch', 'deadtree'): continue        # (trees: trees())
        if WEB_CAR and mat in CAR_MATS and in_car(b): continue          # (the car: broken_car())
        x0, y0, z0, x1, y1, z1 = b
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
        col = C.get(mat, 'b0aca4')
        if mat in ('tentorange', 'tentgreen'):
            tents.setdefault(mat, []).append(b); continue
        if mat == 'logwall': logwall(b); continue
        if mat == 'chainlink': chainlink(b); continue
        if mat in ('mastlight', 'hazard2', 'lantern'):
            B('fo_glow', col, x0, y0, z0, x1, y1, z1, bev=min(0.15, min(sx, sy, sz) * 0.4), kind='neon')
            continue
        if mat in ('rockf', 'rockmoss'):
            rocks_in.append((b, mat)); continue
        if mat in ('logside', 'logend', 'deadbark', 'bark', 'bark2', 'rootball', 'cable'):
            ax, s = thin_axis(b)
            if mat == 'rootball':
                blob('fo_logs', C['rootball'], cx, cy, cz, 1.0, sy=sy * 0.6, sub=1, sx=sx * 0.62, sz=sz * 0.62); continue
            if mat == 'logend' and min(s) < 0.5 and sorted(s)[1] > 1.5:     # a log's cut end or a cable drum's flange: a disc
                r = sorted(s)[1] / 2
                if ax == 0: cylx('fo_logs', LOGEND, x0, x1, cy, cz, r, segs=10, bev=0.0)
                elif ax == 2: cylz('fo_logs', LOGEND, z0, z1, cx, cy, r, segs=10, bev=0.0)
                else: cyl('fo_logs', LOGEND, cx, y0, cz, r, sy, segs=10, bev=0.0)
                continue
            if mat == 'logend' and sy < 0.5:                               # firewood rows in the shed: a stack
                B('fo_logs', LOGEND, *b, bev=0.12); continue
            disc_or_log('fo_logs' if mat not in ('deadbark',) else 'fo_road', DEAD if mat == 'deadbark' else (C['cable'] if mat == 'cable' else (LOGEND if mat == 'logend' else LOG)), b)
            continue
        if mat in ('mastred', 'mastwhite'):
            cyl('fo_mast', col, cx, y0, cz, 0.42, sy, segs=6, bev=0.0); continue
        if mat == 'metal' and max(sx, sz) > 4.0 and sy < 0.5 and y0 > 3.0:   # the mast's braces: a little thicker than the boxes
            if sx > sz: bar('fo_mast', '8f9398', (x0, cy, cz), (x1, cy, cz), t=0.34)
            else: bar('fo_mast', '8f9398', (cx, cy, z0), (cx, cy, z1), t=0.34)
            continue
        if mat == 'metal' and sy > 2.0 and max(sx, sz) < 0.6:              # posts: round
            cyl('fo_yard', '8d9196', cx, y0, cz, max(sx, sz) / 2 * 1.2, sy, segs=6, bev=0.0); continue
        if mat == 'tire':
            ax, s = thin_axis(b)
            r = sy / 2
            if sx < sz: cylx('fo_road', C['tire'], x0, x1, cy, cz, r, segs=12, bev=0.05)
            else: cylz('fo_road', C['tire'], z0, z1, cx, cy, r, segs=12, bev=0.05)
            continue
        model = {'carrust': 'fo_road', 'glassdark': 'fo_road', 'chrome': 'fo_road', 'dirtroad': 'fo_ground',
                 'towerwood': 'fo_tower', 'cabinroof': 'fo_cabin', 'cabinroof2': 'fo_cabin', 'stonebase': 'fo_cabin',
                 'shedmetal': 'fo_yard', 'roofg': 'fo_yard', 'generator': 'fo_yard', 'concrete': 'fo_yard', 'gravel': 'fo_ground',
                 'boatwood': 'fo_dock', 'canoe': 'fo_dock'}.get(mat, 'fo_props')
        if mat == 'dirtroad':
            B('fo_ground', C['dirtroad'], x0, y0 - 0.4, z0, x1, y1, z1, bev=0.0, flat=True); continue
        if mat == 'gravel':
            B('fo_ground', C['gravel'], x0, y0 - 0.3, z0, x1, y1 + 0.02, z1, bev=0.0, flat=True); continue
        if mat in ('cabinroof', 'cabinroof2'):
            B(model, ROOF if mat == 'cabinroof' else ROOF2, x0 - 0.15, y0, z0 - 0.15, x1 + 0.15, y1, z1 + 0.15, bev=0.25, segs=1); continue
        if mat == 'carrust':
            B(model, col, *b, bev=min(0.7, min(sx, sy, sz) * 0.4)); continue
        if mat == 'planks' and sy < 0.9 and sx * sz > 20:                   # floors and decks: boards
            along_x = sx >= sz
            n = max(1, int((sz if along_x else sx) / 1.6))
            for k in range(n):
                if along_x: B(model, PLANK if k % 2 else PLANK2, x0, y0, z0 + k * sz / n + 0.05, x1, y1, z0 + (k + 1) * sz / n - 0.05, bev=0.08, segs=1)
                else: B(model, PLANK if k % 2 else PLANK2, x0 + k * sx / n + 0.05, y0, z0, x0 + (k + 1) * sx / n - 0.05, y1, z1, bev=0.08, segs=1)
            continue
        B(model, col, *b, bev=min(0.3, min(sx, sy, sz) * 0.35), segs=1)
    rocks(rocks_in)
    # the tents: an A-frame over each one's stepped boxes, a dark door flap at its end (the flap's box is dressed above)
    for mat, bs in tents.items():
        x0 = min(b[0] for b in bs); x1 = max(b[3] for b in bs); z0 = min(b[2] for b in bs); z1 = max(b[5] for b in bs)
        y0 = min(b[1] for b in bs); y1 = max(b[4] for b in bs)
        if (x1 - x0) >= (z1 - z0):
            pts = [(-(z0 - 0.3), y0), (-(z0 + z1) / 2, y1 + 0.3), (-(z1 + 0.3), y0)]
            plate('fo_camp', C[mat], pts, x1 - x0, Tr(x0, 0, 0) @ Ry(math.pi / 2), bev=0.12)
        else:
            pts = [(x0 - 0.3, y0), ((x0 + x1) / 2, y1 + 0.3), (x1 + 0.3, y0)]
            plate('fo_camp', C[mat], pts, z1 - z0, Tr(0, 0, z0), bev=0.12)

# ================================================================ set pieces the boxes don't carry
CAB = (L.lx(-50), L.lz(-24))
def cabin_extras():
    m = 'fo_cabin'
    cx, cz = CAB
    F = 0.35 * S
    # window and door frames (the web's openings), white-grey boards proud of the logs both sides
    def frame_x(zf, a0, a1, y0, y1, sill=True):
        for zz in (zf - 0.95, zf + 0.95):
            for (u0, u1, v0, v1) in ((a0 - 0.35, a1 + 0.35, y1, y1 + 0.35), (a0 - 0.35, a0, y0, y1), (a1, a1 + 0.35, y0, y1)) + (((a0 - 0.45, a1 + 0.45, y0 - 0.3, y0),) if sill else ()):
                B(m, '9a8a75', cx + u0, v0, zz - 0.18, cx + u1, v1, zz + 0.18, bev=0.06)
    def frame_z(xf, a0, a1, y0, y1):
        for xx in (xf - 0.95, xf + 0.95):
            for (u0, u1, v0, v1) in ((a0 - 0.35, a1 + 0.35, y1, y1 + 0.35), (a0 - 0.35, a0, y0, y1), (a1, a1 + 0.35, y0, y1), (a0 - 0.45, a1 + 0.45, y0 - 0.3, y0)):
                B(m, '9a8a75', xx - 0.18, v0, cz + u0, xx + 0.18, v1, cz + u1, bev=0.06)
    hd, hw = 4.5 * S, 6.5 * S
    frame_x(cz + hd, 0, 2.0 * S, F, F + 2.3 * S, sill=False)
    for (a0, a1) in ((-4.6, -3.0), (2.8, 4.4)): frame_x(cz + hd, a0 * S, a1 * S, F + 1.0 * S, F + 2.1 * S)
    frame_x(cz - hd, 3.0 * S, 5.0 * S, F, F + 2.3 * S, sill=False)
    frame_x(cz - hd, -3.6 * S, -2.2 * S, F + 1.0 * S, F + 2.1 * S)
    frame_z(cx - hw, -0.8 * S, 0.8 * S, F + 1.0 * S, F + 2.1 * S)
    frame_z(cx + hw, 1.4 * S, 2.6 * S, F + 1.0 * S, F + 2.1 * S)
    # a lamp on the table, a warm light inside each room, the porch light by the door
    B('fo_glow', WARM, cx + 2.4 * S - 0.35, F + 0.85 * S, cz - 0.1 * S - 0.35, cx + 2.4 * S + 0.35, F + 0.85 * S + 1.1, cz - 0.1 * S + 0.35, bev=0.15, kind='neon')
    light('point', cx + 2.4 * S, F + 0.85 * S + 1.6, cz - 0.1 * S, (0, -1, 0), 1.1, 24, 0, 'ffc98a')
    light('point', cx - 4.5 * S, F + 2.2 * S, cz - 1.5 * S, (0, -1, 0), 0.5, 16, 0, 'ffc98a')
    B('fo_glow', WARM, cx + 2.6 * S, F + 2.0 * S, cz + hd + 1.1, cx + 2.6 * S + 0.7, F + 2.0 * S + 0.9, cz + hd + 1.6, bev=0.12, kind='neon')
    light('point', cx + 2.6 * S + 0.35, F + 2.0 * S + 0.4, cz + hd + 2.6, (0, -1, 0), 0.8, 18, 0, 'ffcf96')

def camp_extras():
    cx, cz = L.lx(-30), L.lz(30)
    # charcoal from the dead fire (the web's), the lantern's light
    for b in D['deco']:
        if b['mat'] != 'charcoal': continue
        mx, mz = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2
        ln = (b['max'][0] - b['min'][0]) * S
        a = b.get('rot', 0.0)
        p0 = (L.lx(mx) - ln / 2 * math.cos(a), (b['min'][1] + b['max'][1]) / 2 * S, L.lz(mz) + ln / 2 * math.sin(a))
        p1 = (L.lx(mx) + ln / 2 * math.cos(a), p0[1], L.lz(mz) - ln / 2 * math.sin(a))
        bar('fo_camp', '3e3b38', p0, p1, t=0.55)
    light('point', L.lx(-33), 2.0 * S, L.lz(33.4), (0, -1, 0), 0.9, 24, 0, 'ffc27a')

def tower_extras():
    tx, tz = L.lx(24), L.lz(-50)
    B('fo_glow', WARM, tx + 1.5 * S - 0.3, L.TOWER_FLOOR + 2.4, tz - 0.3, tx + 1.5 * S + 0.3, L.TOWER_FLOOR + 3.2, tz + 0.3, bev=0.1, kind='neon')
    light('point', tx + 1.5 * S, L.TOWER_FLOOR + 4.5, tz, (0, -1, 0), 0.7, 20, 0, 'ffc98a')

def mast_extras():
    # the red beacons (their boxes are dressed as neon): a red light at each
    for (b, mat, w) in L.KEPT:
        if mat == 'mastlight':
            cx, cy, cz = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2
            light('point', cx, cy, cz, (0, -1, 0), 1.0 if cy > 100 else 0.7, 26, 0, 'ff5a46')
    # a lamp in the radio shed
    sx, sz = L.lx(47), L.lz(3)
    light('point', sx, 2.4 * S, sz, (0, -1, 0), 0.5, 14, 0, 'e6ecff')

def road_extras():
    # the car's hazards blink orange (their boxes are neon): a soft light front and back
    car = (L.lx(-8), L.lz(56.2))
    for dx in (-2.4, 2.4):
        light('point', car[0] + dx * S, 0.75 * S, car[1], (0, -1, 0), 0.5, 12, 0, 'ffa448')
    # the power line: wires between the poles (the web's two wires, only over the crop and a little past)
    for b in D['deco']:
        if b['mat'] != 'tire' or b['min'][1] < 5: continue
        y = (b['min'][1] + b['max'][1]) / 2 * S
        z = (b['min'][2] + b['max'][2]) / 2 * S + L.OFFZ
        x0, x1 = max(L.lx(b['min'][0]), -420.0), L.lx(b['max'][0])
        bar('fo_road', '3b3c3f', (x0, y, z), (x1, y, z), t=0.18)

def broken_car():
    """the broken-down car on the road: the web game's own sedan (public/models/p_car_sedan.glb, every face one flat
    colour sampled from its textures, the plates blank: vehicle_port) laid over the web car's boxes the way they tell
    it: the bonnet stood up (web box 1415), the rear door on the road's south side swung open (1417, hinged at the
    B-pillar), the front tyre on the north side flat (1413), the hazards blinking (its indicators are neon ffa448, the
    colour ForestLife's blinker finds). The boxes stay the collision; the engine block (1416) keeps its own dressing.
    Inside, where the open door and the bonnet let you look: a dark cabin with seats, a dark engine bay."""
    import vehicle_port as VP
    # (round 2, the critics: the rust-brown car sank into the brown road at night; an aged off-white reads, quietly)
    DARK_IN, SEAT, BODY = '3e4045', '595e67', 'b5afa3'
    tris = VP.port('p_car_sedan', VP.CAR_RULES(body=BODY, ind='ffa448', ind_kind='neon'))
    # (the sedan's own frame, studs, front +Z: the windscreen's foot at z 3.91, y 2.72; the B-pillar's back edge at z
    # 0.05; the body's sides at x +-2.74; the wheels' centres at z 4.27 and -3.98)
    ZH, YH = 3.91, 2.72
    for (p, n) in (((0, 0, ZH), (0, 0, 1)), ((2.35, 0, 0), (1, 0, 0)), ((-2.35, 0, 0), (1, 0, 0)),
                   ((0, 0, 0.05), (0, 0, 1)), ((0, 0, -2.55), (0, 0, 1)), ((0, 0.85, 0), (0, 1, 0))):
        tris = VP.clip(tris, p, n)
    def is_hood(t):
        c = VP.centre(t)
        return t['mat'] == 'tint' and c.z > ZH and abs(c.x) < 2.35 and t['n'].y > 0.3 and c.y > 2.3
    def is_door(t):
        c = VP.centre(t)
        return c.x < -1.8 and t['n'].x < -0.45 and -2.55 < c.z < 0.05 and c.y > 0.85 and t['obj'] not in ('wheel_rr', 'wheel_fr')
    hood, tris = VP.split(tris, is_hood)
    door, tris = VP.split(tris, is_door)
    hood = VP.hinge(VP.thicken(hood, 0.12), (0, YH, ZH), (1, 0, 0), -math.radians(86))
    door = VP.hinge(VP.thicken(door, 0.15, look=('plastic', '4a4d52')), (-2.74, 0, 0.05), (0, 1, 0), math.radians(88))
    # the flat tyre: squashed onto the road, a little wider
    fl, tris = VP.split(tris, lambda t: t['obj'] == 'wheel_fl')
    fl = VP.transform(fl, Matrix.Translation((2.38, 0, 0)) @ Matrix.Diagonal((1.1, 0.74, 1.0, 1)) @ Matrix.Translation((-2.38, 0, 0)))
    # where the openings let you look in, the shell gets a dark inner skin (Roblox draws only a face's front, so a bare
    # shell would show the road through the car), with a rim round the cut edges; floors and seats inside
    def near(t):
        c = VP.centre(t)
        return t['obj'] == 'shell' and abs(c.x) < 2.76 and -2.75 < c.z < 7.3 and c.y > 0.6
    inside, tris = VP.split(tris, near)
    inside = VP.thicken(inside, 0.08, look=('plastic', DARK_IN))
    room = (VP.box(-2.6, 0.7, -2.6, 2.6, 1.0, 3.4, ('plastic', DARK_IN))                # the cabin floor
            + VP.box(-2.4, 0.95, ZH - 0.1, 2.4, 1.2, 6.7, ('plastic', DARK_IN))         # the engine bay's floor
            + VP.box(-2.2, 1.0, -2.4, 2.2, 1.95, -0.7, ('plastic', SEAT))              # the back seat
            + VP.box(-2.2, 1.95, -2.45, 2.2, 3.3, -1.95, ('plastic', SEAT))
            + VP.box(-2.05, 1.0, 0.35, -0.35, 3.35, 1.0, ('plastic', SEAT))            # the front seats' backs
            + VP.box(0.35, 1.0, 0.35, 2.05, 3.35, 1.0, ('plastic', SEAT)))
    car = tris + inside + hood + door + fl + room
    # onto the web car's body box (x -10.3..-5.7, z 55.25..57.15 m), front +X: a touch wider and taller than the
    # sedan (the box car was), the wheels on the road
    cx, cz = L.lx(-8.0), L.lz(56.2)
    M = Tr(cx, 0.0, cz) @ Matrix.Rotation(math.pi / 2, 4, 'Y') @ Matrix.Diagonal((5.7 / 5.48, 1.08, 13.8 / 14.3, 1))
    n = VP.place('fo_road', car, M)
    print('BROKEN CAR: the web sedan, %d triangles' % n)

def dock_extras():
    # posts down to the lake bed (their boxes stop just under the water), a lamp on a post at the dock's end
    for (b, mat, w) in L.KEPT:
        if mat == 'logside' and b[0] > L.SHORE - 15 and b[1] < 0 and (b[4] - b[1]) < 6:
            cx, cz = (b[0] + b[3]) / 2, (b[2] + b[5]) / 2
            bed = -14.0 if cx > L.SHORE + 42 else (-4.5 if cx > L.SHORE + 27 else -1.5)
            cyl('fo_dock', LOG, cx, bed, cz, 0.42, b[1] - bed + 0.2, segs=8, bev=0.0)
    x, z = L.lx(72 + 17.6), L.lz(-30.9)
    cyl('fo_dock', LOG, x, 0.9, z, 0.3, 7.0, segs=8, bev=0.05)
    B('fo_dock', '4a4b4d', x - 0.55, 7.6, z - 0.55, x + 0.55, 8.0, z + 0.55, bev=0.1)
    B('fo_glow', WARM, x - 0.42, 6.6, z - 0.42, x + 0.42, 7.6, z + 0.42, bev=0.12, kind='neon')
    light('point', x, 6.8, z, (0, -1, 0), 0.8, 22, 0, 'ffc98a')

# ================================================================ the edge: a rail fence on the crop's line, a thicket past it
def edge():
    X, Z, SH = L.X_EDGE, L.Z_EDGE, L.SHORE
    road = (L.lz(52) - 3, L.lz(60) + 3)
    runs = [((-X, -Z), (SH - 4, -Z)), ((-X, Z), (SH - 4, Z)), ((-X, -Z), (-X, Z))]
    m = 'fo_edge'
    for (a, b) in runs:
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(ln / 12))
        for k in range(n + 1):
            t = k / n
            x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            if a[0] == b[0] and road[0] < z < road[1]: continue
            cyl(m, '6f5c4a', x, -0.5, z, 0.45, 5.0, segs=6, bev=0.0)
        for yy in (2.0, 3.8):
            # the rails, broken at the road (its gate)
            if a[0] == b[0]:
                for (z0, z1) in ((a[1], road[0]), (road[1], b[1])):
                    bar(m, '7a6450', (a[0], yy, z0), (a[0], yy, z1), t=0.42)
            else:
                bar(m, '7a6450', (a[0], yy, a[1]), (b[0], yy, b[1]), t=0.42)
        # the thicket: low bushes just past the line
        k = 0.0
        while k < ln:
            t = k / ln
            x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            ox = -1 if a[0] == b[0] else 0
            oz = 0 if a[0] == b[0] else (1 if z > 0 else -1)
            d = 4.0 + rnd.random() * 5
            if not (a[0] == b[0] and road[0] - 4 < z < road[1] + 4):
                blob(m, BUSH if int(k) % 2 else BUSH2, x + ox * d, 1.2, z + oz * d, 3.6 + rnd.random() * 1.6, sy=0.6, sub=1)
            k += 8.0 + rnd.random() * 4
    # the road's gate at the west edge: two posts, a timber bar and a brace across the road
    gx = -X
    for zz in (road[0], road[1]):
        cyl(m, '6f5c4a', gx, -0.5, zz, 0.7, 6.0, segs=8, bev=0.1)
    bar(m, '8a7056', (gx, 3.6, road[0]), (gx, 3.6, road[1]), t=0.8)
    bar(m, '8a7056', (gx, 1.2, road[0] + 1), (gx, 3.4, road[1] - 1), t=0.5)
    bar(m, '8a7056', (gx, 1.2, road[0] + 1), (gx, 1.2, road[1] - 1), t=0.5)

# ================================================================ build
bpy.ops.wm.read_factory_settings(use_empty=True)
ground(); lake(); trees(); undergrowth(); dress()
cabin_extras(); camp_extras(); tower_extras(); mast_extras(); road_extras(); dock_extras(); edge()
if WEB_CAR: broken_car()

HIT = L.MATS
solid = [(b[0], b[1], b[2], b[3], b[4], b[5]) + HIT[b[6]] for b in L.HIT_SOLID]
rotb = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) + HIT[r[7]] + (r[8],) for r in L.HIT_ROT]
cylb = [tuple(c[:7]) + HIT[c[7]] + (c[8],) for c in L.HIT_CYL]
tiltb = [tuple(t[:12]) + HIT[t[12]] + (t[13], t[14]) for t in L.HIT_TILT]
INFO.update(L.WALLBOX)
water = [tuple(w) for w in L.WATER + L.WATER_FAR]
K.write_layout(LAYOUT, INFO, solid, [], [tuple(p) for p in L.SPAWNS], L.TEAM, water=water, src='tools/roblox/forest_models.py', rot=rotb, cyl=cylb, tilt=tiltb)

# (19 Nov 2026) the boulders' hit cylinders must sit inside the drawn rocks: points on each cylinder's side, tested
# against the rock's own mesh (inside when the nearest face looks away from the point)
BADS = []
def hull_check():
    from mathutils.bvhtree import BVHTree
    worst, bad, n, under, uworst = 0.0, 0, 0, 0, 0.0
    for (bb, mat, seed, sub, hgt, fl) in L.ROCKS:
        bm, M = rock_mesh(bb, seed, sub)
        cy = M.translation.y
        foot = min(v.co.y for v in bm.verts if v.co.y >= -(bb[4] - bb[1]) * 0.3 - 1e-6) + cy   # (its lowest edge: the dish's rim)
        bm.transform(M)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        tree = BVHTree.FromBMesh(bm)
        x0, y0, z0, x1, y1, z1 = bb
        for c in L.CYL:
            if c[7] != mat or not (x0 - 0.5 <= c[0] <= x1 + 0.5 and z0 - 0.5 <= c[2] <= z1 + 0.5) or abs(c[0] - c[3]) > 1e-6: continue
            lo, hi, r = min(c[1], c[4]), max(c[1], c[4]), c[6]
            for k in range(5):
                yy = lo + (hi - lo) * (k + 0.5) / 5
                for a in range(16):
                    pt = Vector((c[0] + r * math.cos(a * math.pi / 8), yy, c[2] + r * math.sin(a * math.pi / 8)))
                    hit = tree.find_nearest(pt)
                    if hit[0] is None: continue
                    n += 1
                    out = (pt - hit[0]).dot(hit[1])
                    if out > 0.02:
                        # (under the rock's foot, between the floor and the rock's lowest edge, the rock overhangs it:
                        # counted apart; only what's beside the rock's sides counts as showing)
                        g = L.floor_min([(pt.x, pt.z)])
                        if yy <= foot + 0.05 or yy <= g + 0.1: under += 1; uworst = max(uworst, out)
                        else:
                            bad += 1; worst = max(worst, out)
                            if len(BADS) < 400: BADS.append((round(out, 2), round(yy - foot, 2), round(hi - yy, 2), round(r, 2), mat, sub, round(c[0], 1), round(c[2], 1)))
        bm.free()
    print('HULL CHECK: %d points on the boulders\' hit cylinders, %d outside the drawn rock\'s sides (worst %.2f studs), %d under its foot (worst %.2f)' % (n, bad, worst, under, uworst))
hull_check()
for _b in sorted(BADS, reverse=True)[:3]: print('HULL OUT (worst: out, over the foot, under the top, radius, mat, sub, x, z)', _b)
print('LAYOUT SIZE %d characters' % os.path.getsize(LAYOUT))
_tri = {}
for (mname, key), items in K.PIECES.items():
    _tri[mname] = _tri.get(mname, 0) + sum(sum(len(f.verts) - 2 for f in bm.faces) for bm, M in items)
print('TRIS BY MODEL', sorted(_tri.items(), key=lambda kv: -kv[1]), 'TOTAL', sum(_tri.values()))

# local studs: (name, camera, look at, lens)
A0 = L.TEAM['att'][3]; D0 = L.TEAM['def'][3]
VIEWS = [
    ('overview', (-470, 300, 420), (0, -20, -10), 24),
    ('att_spawn', (A0[0], 6.0, A0[2]), (D0[0], 8.0, D0[2]), 20),
    ('def_spawn', (D0[0], 6.0, D0[2]), (A0[0], 8.0, A0[2]), 20),
    ('cabin', (-112, 9, -18), (-168, 7, -69), 20),
    ('clearing', (34, 9, 20), (-18, 4, -27), 20),
    ('tower', (6, 10, -96), (54, 22, -147), 20),
    ('mastyard_dock', (205, 8, 70), (140, 14, -30), 20),
    ('campsite', (-58, 9, 128), (-108, 3, 90), 20),
    ('road_car', (30, 7, 150), (-42, 3, 171), 20),
    ('car_close', (-20, 10, 158), (-42, 3, 171.6), 55),
    ('car_door', (-60, 9, 194), (-42, 3, 172), 55),
    ('clearing_high', (-30, 60, 40), (-18, 0, -27), 22),
]
DAY = '--day' in K.FLAGS

def render_night(folder, views, prefix, **pv):
    os.makedirs(folder, exist_ok=True)
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new('cam'); cam_data.clip_end = 8000
    cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
    moon = bpy.data.lights.new('moon', 'SUN'); moon.energy = 3.0 if DAY else 1.1; moon.angle = 0.1
    moon.color = (1.0, 0.95, 0.88) if DAY else (0.72, 0.8, 1.0)
    mo = bpy.data.objects.new('moon', moon); sc.collection.objects.link(mo); mo.rotation_euler = tuple(math.radians(a) for a in (48, 0, -150))
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.5, 0.55, 0.62, 1) if DAY else (0.16, 0.2, 0.3, 1)
    bg.inputs['Strength'].default_value = 1.0 if DAY else 0.55
    sc.world = w
    if not DAY:
        # a thin fog volume so the far woods fall back the way the game's haze will do it
        vol = bpy.data.materials.new('fog'); vol.use_nodes = True
        nt = vol.node_tree; nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial'); sv = nt.nodes.new('ShaderNodeVolumeScatter')
        sv.inputs['Density'].default_value = 0.0016; sv.inputs['Color'].default_value = (0.42, 0.5, 0.66, 1)
        nt.links.new(sv.outputs['Volume'], out.inputs['Volume'])
        bpy.ops.mesh.primitive_cube_add(size=1)
        cube = bpy.context.active_object; cube.scale = (2400, 2400, 400); cube.location = (0, 0, 150)
        cube.data.materials.append(vol)
    # (preview only: the lake's water, which in the game is terrain water from the layout's water boxes)
    wm = bpy.data.materials.new('lakewater'); wm.use_nodes = True
    bs = wm.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (0.03, 0.05, 0.07, 1); bs.inputs['Roughness'].default_value = 0.08
    wme = bpy.data.meshes.new('lakewater')
    wme.from_pydata([(-240, -720, 0), (240, -720, 0), (240, 720, 0), (-240, 720, 0)], [], [(0, 1, 2, 3)])
    wp = bpy.data.objects.new('lakewater', wme); sc.collection.objects.link(wp)
    wp.location = (K.P @ Vector((440, L.WATER_Y, 0, 1))).xyz
    wme.materials.append(wm)
    if not DAY:
        for (kind, p, d, b, r, a, col) in K.LIGHTS:
            ld = bpy.data.lights.new('l', 'POINT'); ld.energy = b * r * r * 6.0; ld.shadow_soft_size = 0.8
            ld.color = [int(col[j:j + 2], 16) / 255 for j in (0, 2, 4)]
            ob = bpy.data.objects.new('l', ld); sc.collection.objects.link(ob)
            ob.location = (K.P @ Vector((p[0], p[1], p[2], 1))).xyz
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
    sc.cycles.volume_step_rate = 4.0
    sc.render.resolution_x, sc.render.resolution_y = 1000, 560
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.exposure = 0.0 if DAY else 1.2
    sc.render.image_settings.file_format = 'JPEG'
    for (name, cp, tp, lens) in views:
        c = K.P @ Vector((cp[0], cp[1], cp[2], 1)); t = K.P @ Vector((tp[0], tp[1], tp[2], 1))
        cam.location = c.xyz
        cam.rotation_euler = (t.xyz - c.xyz).to_track_quat('-Z', 'Y').to_euler()
        cam_data.lens = lens
        sc.render.filepath = os.path.join(folder, '%s_%s%s.jpg' % (prefix, name, '_day' if DAY else ''))
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)

if PREVIEW and '--no-preview' not in K.FLAGS:
    K.render_previews = render_night
    PICK = [a.split('=', 1)[1] for a in K.FLAGS if a.startswith('--views=')]
    if PICK: VIEWS = [v for v in VIEWS if v[0] in PICK[0].split(',')]
K.finish('forest', OUT_DIR, PREVIEW if '--no-preview' not in K.FLAGS else None, VIEWS, prefix='forest')
