# Mount Kaboom on Islands S&D (shared/map.js volcano()): drawn over its own boxes (tools/arch/dump.mjs), which stay what
# you bump into. A stepped volcano of columnar basalt: each of its three terraces is ringed by tall hexagonal columns
# (split by cross joints, a little out of true, a few broken stubs at their feet), their tops flush with the floor you
# walk on; rough cut stone steps up its six stairs; a jagged crater rim round the top; the throat glowing from the lava
# down in it (the lava itself is the game's); two lava falls pouring from the crater down the north and west sides
# into glowing pools on the beach; steam vents; the terrace boulders are heaps of broken columns.
# local frame = volcano()'s (the map puts it 10 m north: placement p [0, 0, -10]).
# run: node tools/arch/dump.mjs islands_sd volcano_sd tools/blender/arch/boxes/volcano_sd.json
#      blender52 -b --python tools/blender/arch/make_volcano_sd.py
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'vbasalt': ('concrete', '#c4b4e6', {}), 'vbasalt2': ('concrete', '#a898cc', {}), 'vtop': ('concrete', '#dacfe6', {}), 'vstep': ('concrete', '#e6dcec', {}),  # (x the grey concrete texture: dark violet basalt in the sunset)
    'vlava': ('stucco', '#ff7a1c', {'glow': True, 'glowcol': '#ff7a1c'}), 'vglow': ('stucco', '#ff4a10', {'glow': True, 'glowcol': '#e8400c'}), 'vcrust': ('concrete', '#9a4a36', {}), 'vash': ('stucco', '#a89ea8', {}),
})
NOCAST.update({'vlava', 'vglow'})
C1, C2 = 4.5, 2.5  # the terraces' corner cuts (shared/map.js VOLC)
TIERS = [  # outline, floor height, the height under it
    ((-15, -16, 15, 10), C1, 3.0, -0.4),
    ((-10, -13.5, 10, 7.5), C2, 6.0, 3.0),
    ((-6, -9, 6, 3), 0.0, 9.0, 6.0),
]
THROAT = (-2, -5, 2, -1)
rng = random.Random(11)
SEQ = iter(range(10 ** 6))  # (each column's top a hair off its neighbours')


def octo2(r, c):  # (x, z) corners of a rectangle cut c across its corners, in order round it
    x0, z0, x1, z1 = r
    if c <= 0: return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    return [(x0 + c, z0), (x1 - c, z0), (x1, z0 + c), (x1, z1 - c), (x1 - c, z1), (x0 + c, z1), (x0, z1 - c), (x0, z0 + c)]


def inside(p, poly):
    x, z = p; n = len(poly); c = False
    for i in range(n):
        (ax, az), (bx, bz) = poly[i], poly[(i + 1) % n]
        if (az > z) != (bz > z) and x < ax + (z - az) * (bx - ax) / (bz - az): c = not c
    return c


def poly_fill(outer, holes, y, mat, up=True):
    bm = bmesh.new(); edges = []
    for pts in [outer] + holes:
        vs = [bm.verts.new((p[0], p[1], 0.0)) for p in pts]
        edges += [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    for f in [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]:
        cen = f.calc_center_median()
        if any(inside((cen.x, cen.y), h) for h in holes) or not inside((cen.x, cen.y), outer): continue
        t = [Vector((v.co.x, y, v.co.y)) for v in f.verts]
        n = (t[1] - t[0]).cross(t[2] - t[0])
        if n.length < 1e-4: continue
        K.tri(t if (n.y > 0) == up else t[::-1], mat)
    bm.free()


def hexcol(cx, cz, r, y0, y1, rot, side, top='vtop', cap=True, lean=(0.0, 0.0)):
    """a hexagonal column from y0 to y1 (its top leaning off by lean over its height)"""
    P0 = [Vector((cx + r * math.cos(rot + k * math.pi / 3), y0, cz + r * math.sin(rot + k * math.pi / 3))) for k in range(6)]
    P1 = [Vector((p.x + lean[0], y1, p.z + lean[1])) for p in P0]
    c = Vector((cx, (y0 + y1) / 2, cz))
    for k in range(6):
        j = (k + 1) % 6; q = [P0[k], P0[j], P1[j], P1[k]]
        n = (q[1] - q[0]).cross(q[3] - q[0]); m = (q[0] + q[2]) / 2
        K.quad(q if n.dot(m - c) > 0 else q[::-1], side)
    if cap:
        ct = Vector((cx + lean[0], y1, cz + lean[1]))
        for k in range(6):
            t = [ct, P1[k], P1[(k + 1) % 6]]; n = (t[1] - t[0]).cross(t[2] - t[0])
            K.tri(t if n.y > 0 else t[::-1], top)


def column(cx, cz, r, ybase, ytop, side):
    """a basalt column, broken into stacked lengths at its cross joints (each a hair narrower, a little off true)"""
    n = 1 if ytop - ybase < 1.6 else rng.choice((2, 2, 3))
    cuts = sorted(rng.uniform(ybase + 0.6, ytop - 0.5) for _ in range(n - 1)) if n > 1 else []
    ys = [ybase] + cuts + [ytop]; rot = rng.uniform(0, math.pi / 3)
    for i in range(len(ys) - 1):
        last = i == len(ys) - 2
        jx, jz = (0.0, 0.0) if last else (rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03))
        rr = r - (0.0 if last else rng.uniform(0.0, 0.03))
        g = 0.0 if last else 0.04  # (a small crack between lengths)
        hexcol(cx + jx, cz + jz, rr, ys[i], ys[i + 1] - g, rot + rng.uniform(-0.04, 0.04), side, cap=last or rng.random() < 0.5)


def ring(poly, ybase, ytop, skip=()):
    """columns round an outline, their outer faces at its edge, their tops flush with the floor"""
    n = len(poly)
    for i in range(n):
        a, b = Vector((poly[i][0], 0, poly[i][1])), Vector((poly[(i + 1) % n][0], 0, poly[(i + 1) % n][1]))
        d = b - a; L = d.length; d.normalize(); inw = Vector((-d.z, 0, d.x))
        mid = (a + b) / 2
        if not inside((mid.x + inw.x * 0.5, mid.z + inw.z * 0.5), poly): inw = -inw
        k = max(1, round(L / 0.92))
        for j in range(k):
            t = (j + 0.5) / k; p = a.lerp(b, t)
            if any(s[0] <= p.x <= s[2] and s[1] <= p.z <= s[3] for s in skip): continue
            r = rng.uniform(0.46, 0.54); c = p + inw * (r * 0.88 - rng.uniform(0.0, 0.06))
            column(c.x, c.z, r, ybase, ytop + rng.choice((0.03, 0.05, 0.08)) + 0.0021 * (next(SEQ) % 7), rng.choice(('vbasalt', 'vbasalt', 'vbasalt2')))  # (never two neighbours' tops at one height: they overlap a little)
            if rng.random() < 0.18 and ytop - ybase > 2:  # a broken stub at its foot
                o = c - inw * (r * 2.0); hexcol(o.x, o.z, r * 0.9, ybase, ybase + rng.uniform(0.15, 0.35), rng.uniform(0, 1), 'vbasalt2')


def build():
    global K
    K = Kit(os.path.join(HERE, 'boxes', 'volcano_sd.json'), seed=7)
    K.ground = -0.4
    for b in K.boxes: b['_done'] = True
    # (the AO: the terraces' boxes pulled in behind the columns, so the columns aren't 'inside the rock'; the steps and
    # the rim stay out of it: they're drawn over their own boxes)
    K.solids = []
    for b in K.boxes:
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        if x1 - x0 > 2.2 and z1 - z0 > 2.2 and y1 - y0 >= 2.9: K.solids.append(((x0 + 1.1, y0, z0 + 1.1), (x1 - 1.1, y1 - 0.05, z1 - 1.1)))
    # ---- the stairs: cut stone, a paler tread on top (from their boxes: solid steps)
    stairs = []
    for b in K.boxes:
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        thin = min(x1 - x0, z1 - z0)
        if b['mat'] == 'basalt' and thin < 0.5 and max(x1 - x0, z1 - z0) > 3.4 and y0 in (0.0, 3.0, 6.0) and y1 - y0 < 3.05: stairs.append(b)
    for b in stairs: K.box(b['min'], b['max'], {'top': 'vstep', 'side': 'vbasalt2', 'bottom': None}, cull=True)
    stair_boxes = [(b['min'][0] - 0.05, b['min'][2] - 0.05, b['max'][0] + 0.05, b['max'][2] + 0.05) for b in stairs]
    # ---- the terraces: their floors, the column cliffs round them
    for i, (r, c, ytop, ybase) in enumerate(TIERS):
        poly = octo2(r, c)
        holes = [octo2(TIERS[i + 1][0], TIERS[i + 1][1])] if i < 2 else [[(-2.3, -5.3), (2.3, -5.3), (2.3, -0.7), (-2.3, -0.7)]]
        poly_fill(poly, holes, ytop, 'vtop')
        ring(poly, ybase, ytop)
    # ---- the boulders: heaps of broken columns over their boxes
    for b in K.boxes:
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        if b['mat'] != 'basalt' or y0 not in (3.0, 6.0) or not (0.7 < x1 - x0 < 3 and 0.7 < z1 - z0 < 3) or (x1 - x0) < 1.5 and (y1 - y0) > 2: continue
        if abs((y1 - y0) - (x1 - x0) * 0.6) > 0.05: continue
        cx, cz, h = (x0 + x1) / 2, (z0 + z1) / 2, y1 - y0
        for (ox, oz, hh) in ((-0.25, -0.15, 1.0), (0.3, 0.1, 0.8), (-0.05, 0.35, 0.65)):
            hexcol(cx + ox * (x1 - x0), cz + oz * (z1 - z0), min(x1 - x0, z1 - z0) * 0.3, y0, y0 + h * hh, rng.uniform(0, 1), 'vbasalt', lean=(rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1)))
        FL.bar(K, Vector((x0 - 0.2, y0 + 0.25, cz + 0.6)), Vector((x1 + 0.3, y0 + 0.2, cz - 0.4)), min(x1 - x0, z1 - z0) * 0.32, 'vbasalt2')  # (one lying down)
    # ---- the crater: the rim's jagged rocks over its boxes, the lip, the throat glowing down to the lava
    for b in K.boxes:
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        if b['mat'] != 'basalt' or abs(y0 - 9.0) > 1e-3: continue
        if abs(y1 - 9.9) < 1e-3:  # the rim: jagged teeth along it
            L = max(x1 - x0, z1 - z0); n = max(1, round(L / 0.7)); ax = (x1 - x0) > (z1 - z0)
            for k in range(n):
                t0, t1 = k / n, (k + 1) / n
                a0 = (x0 + (x1 - x0) * t0, z0) if ax else (x0, z0 + (z1 - z0) * t0)
                a1 = (x0 + (x1 - x0) * t1, z1) if ax else (x1, z0 + (z1 - z0) * t1)
                hgt = rng.uniform(9.85, 10.05)
                FL.obox(K, (a0[0] - 0.04, 9.0, a0[1] - 0.04), (a1[0] + 0.04, hgt - 0.12, a1[1] + 0.04), 'vbasalt')
                cx, cz = (a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2
                FL.tube(K, (cx, hgt - 0.13, cz), (cx + rng.uniform(-0.05, 0.05), hgt, cz + rng.uniform(-0.05, 0.05)), min(a1[0] - a0[0], a1[1] - a0[1]) * 0.55 + 0.05, 0.08, 'vbasalt2', n=5)
        elif abs(y1 - 9.3) < 1e-3:  # the lip round the throat: cooled crust
            FL.obox(K, (x0, 9.0, z0), (x1, 9.3, z1), 'vcrust')
    tx0, tz0, tx1, tz1 = THROAT
    for (a, b) in (((tx0, tz0), (tx1, tz0)), ((tx1, tz0), (tx1, tz1)), ((tx1, tz1), (tx0, tz1)), ((tx0, tz1), (tx0, tz0))):  # the throat's walls: dark above, glowing down by the lava
        for (ya, yb, m) in ((4.3, 5.6, 'vglow'), (5.6, 9.0, 'vcrust')):
            q = [Vector((a[0], ya, a[1])), Vector((b[0], ya, b[1])), Vector((b[0], yb, b[1])), Vector((a[0], yb, a[1]))]
            n = (q[1] - q[0]).cross(q[3] - q[0]); c = Vector((0, 0, -3))
            K.quad(q if n.dot(Vector(((a[0] + b[0]) / 2, 0, (a[1] + b[1]) / 2)) - c) < 0 else q[::-1], m)
    # ---- two lava falls: out over the rim, down each terrace face, across the floors, into a pool on the beach
    def fall(path, w, across):
        for (p, q) in zip(path, path[1:]):
            P, Q = Vector(p), Vector(q); d = Q - P
            side = Vector(across) * (w / 2)  # (across the stream: the same way down a face as along a floor)
            out = Vector((0, 1, 0)) if abs(d.y) < 1e-3 else Vector((d.x, 0, d.z)).normalized()
            off = Vector((0, -0.018, 0)) if abs(d.y) < 1e-3 else Vector((0, 0, 0))  # (on the floor at +0.012: under the columns' tops)
            q4 = [P - side + off, P + side + off, Q + side + off, Q - side + off]
            n = (q4[1] - q4[0]).cross(q4[3] - q4[0])
            if abs(d.y) < 1e-3: K.quad(q4 if n.y > 0 else q4[::-1], 'vlava')
            else: FL.both(K, q4, 'vlava')
    fall([(3.5, 9.95, -9.07), (3.5, 6.03, -9.07), (3.5, 6.03, -13.54), (3.5, 3.03, -13.54), (3.5, 3.03, -16.04), (3.5, 0.03, -16.04), (3.5, 0.03, -18.6)], 0.7, (1, 0, 0))  # (down the columns' faces)
    fall([(-6.02, 9.95, -3.5), (-6.02, 6.03, -3.5), (-10.02, 6.03, -3.5), (-10.02, 3.03, -3.5), (-15.02, 3.03, -3.5), (-15.02, 0.03, -3.5), (-17.4, 0.03, -3.5)], 0.6, (0, 0, 1))  # (clear of the west stair)
    for (cx, cz, r) in ((3.85, -19.4, 1.1), (-18.0, -3.3, 0.9)):  # the pools, a crust round them
        pts = [(cx + r * math.cos(a) * rng.uniform(0.85, 1.1), cz + r * math.sin(a) * rng.uniform(0.85, 1.1)) for a in [2 * math.pi * k / 10 for k in range(10)]]
        poly_fill(pts, [], 0.045, 'vlava')
        for k in range(10):
            a, b = pts[k], pts[(k + 1) % 10]
            FL.bar(K, Vector((a[0], 0.06, a[1])), Vector((b[0], 0.06, b[1])), 0.16, 'vcrust', h=0.1)
    # ---- steam vents on the terraces: a cone of ash with a glowing mouth
    for (x, y, z) in ((-12.5, 3.0, -1.5), (11.5, 3.0, -12.5), (6.5, 6.0, 4.5), (-7.5, 6.0, -11.5)):
        FL.tube(K, (x, y - 0.02, z), (x, y + 0.35, z), 0.45, 0.16, 'vash', n=7, caps=(False, False))
        FL.tube(K, (x, y + 0.34, z), (x, y + 0.36, z), 0.15, 0.15, 'vglow', n=7, caps=(False, True))
    K.finish(os.path.join(OUTDIR, 'volcano_sd.glb'))


build()
