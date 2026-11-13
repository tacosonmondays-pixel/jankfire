# The long pier east (Islands, from Volcano Island to Lighthouse Point) and the bait shack on its wide bit (shared/map.js:
# the pier boxes in islands(), baitShack()), drawn over their boxes as one model, which stay what you bump into.
# The pier: deck boards laid across it with gaps between (a couple patched, one painted pink), a fascia beam round its
# edge, headstock ends poking out, round timber piles standing proud of the edges with weed and barnacles at the waterline
# (you see them go down into the shallows at both ends), a sleeper where it lands on each beach. Cast-iron bollards (the
# game's black boxes) with candy caps, tyre fenders hung on ropes, a mooring line still tied to a bollard (no boat), the
# handrails as posts and a rail. A seagull on a bollard.
# The bait shack: plank walls in leftover paint, corner posts, crooked patch boards, a skirting board; the hatch's flap
# propped up on two sticks over the counter (a bait bucket, a jar of worms on it); the sign (the game's) in a frame; two
# little lamps; a tin roof of corrugated sheets (one pink, one bare) with a tyre on it to hold it down and a gull; a net
# hung on the west wall with cork floats, another drying over the rail; buoys hung on the east wall; a life ring; hand-
# painted boards ("gone fishin", "worms: no refunds"); inside, a bulb, a shelf of tins, a trophy fish.
# The crates, the barrel (prop models) and the sign's face (the game's ad texture) stay the game's.
# local frame = the map's (placement at 0,0,0).
# run: node tools/arch/dump.mjs islands pier tools/blender/arch/boxes/pier.json --deco
#      blender52 -b --python tools/blender/arch/make_pier.py
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
WY = -0.25  # the sea (shared/map.js ISL.WY)
MATS.update({
    'pdeck': ('timber', '#c9a47a', {}), 'pdeck2': ('timber', '#a49684', {}), 'pdeck3': ('timber', '#dcbc92', {}), 'pdeckp': ('timber', '#ff8ac8', {}),
    'pgap': ('tar', '#2a1e18', {}), 'pbeam': ('timber', '#8a6a4e', {}), 'ppile': ('timber', '#9a8470', {}), 'ppost': ('timber', '#b08e6a', {}),
    'pweed': ('stucco', '#4e8a2e', {}), 'pbarn': ('stucco', '#ece6d6', {}), 'pzinc': ('metalplate', '#c8ccd4', {'gloss': 0.5, 'metal': 1}),
    'piron': ('metalplate', '#2c2a34', {'gloss': 0.55}), 'pcap': ('trim', '#ffe14d', {'gloss': 0.6}), 'ptyre': ('tread', '#ffffff', {}),
    'prope': ('rope', '#e8cf9c', {}), 'pwall': ('shackwall', '#ffffff', {}), 'pin': ('timber', '#6a5444', {}), 'pinside': ('timber', '#4a3a30', {}),
    'ptin': ('corrugated', '#2cc4c0', {'gloss': 0.3}), 'ptinp': ('corrugated', '#ff7ac8', {'gloss': 0.3}), 'ptinb': ('corrugated', '#d4d8dc', {'gloss': 0.35, 'metal': 1}),
    'pnet': ('net', '#d8dcc4', {'alpha': True}), 'pnetg': ('net', '#9ad0a8', {'alpha': True}), 'pcork': ('stucco', '#ff9a3c', {'gloss': 0.4}),
    'pbuoyp': ('trim', '#ff4fd8', {'gloss': 0.7}), 'pbuoyy': ('trim', '#ffe14d', {'gloss': 0.7}), 'pbuoyc': ('trim', '#4fd8ff', {'gloss': 0.7}),
    'pbuoyw': ('trim', '#fff8ee', {'gloss': 0.7}), 'pbuoyr': ('trim', '#ff3040', {'gloss': 0.7}), 'ptags': ('shacktags', '#ffffff', {}),
    'pgull': ('trim', '#fbfbf6', {}), 'pgullg': ('trim', '#a8b0bc', {}), 'pbeak': ('trim', '#ffc020', {}), 'pblack': ('tar', '#1a161c', {}),
    'pbulb': ('trim', '#fff0a0', {'glow': True, 'glowcol': '#ffd860'}), 'pjar': ('trim', '#ff6ab8', {'gloss': 0.8}), 'ptin2': ('metalplate', '#d84a3a', {'gloss': 0.4}),
    'ptrimp': ('timber', '#ff4fd8', {'gloss': 0.3}), 'ptrimc': ('timber', '#4fd8ff', {'gloss': 0.3}), 'ptrimy': ('timber', '#ffe14d', {'gloss': 0.3}),
    'prail': ('timber', '#ffd23c', {}), 'pcapp': ('trim', '#ff4fd8', {'gloss': 0.6}), 'pcapc': ('trim', '#4fd8ff', {'gloss': 0.6}), 'pdoor': ('shackwall', '#4fd8ff', {'gloss': 0.25}),
    'pfish': ('trim', '#3ad0a0', {'gloss': 0.7}), 'pfishb': ('trim', '#f6f0d8', {'gloss': 0.5}), 'pbucket': ('metalplate', '#4fd8ff', {'gloss': 0.5}),
})
NOCAST.update({'pcapp', 'pcapc', 'ptrimy', 'pweed', 'pbarn', 'pzinc', 'pcap', 'prope', 'pnet', 'pnetg', 'pcork', 'pbuoyp', 'pbuoyy', 'pbuoyc', 'pbuoyw', 'pbuoyr', 'ptags',
               'pgull', 'pgullg', 'pbeak', 'pblack', 'pbulb', 'pjar', 'ptin2', 'pfish', 'pfishb', 'pbucket'})


# ------------------------------------------------------------ geometry helpers (game space, y up)
def Q(p, mat, uv=None, out=None):
    """a quad; out: a direction it must face (it's flipped if it doesn't)"""
    p = [Vector(q) for q in p]
    if out is not None:
        n = (p[1] - p[0]).cross(p[2] - p[0])
        if n.length < 1e-12: n = (p[2] - p[0]).cross(p[3] - p[0])
        if n.dot(Vector(out)) < 0: p = p[::-1]; uv = uv[::-1] if uv else None
    K.quad(p, mat, uv=uv)


def T3(p, mat, out=None):
    p = [Vector(q) for q in p]
    if out is not None and (p[1] - p[0]).cross(p[2] - p[0]).dot(Vector(out)) < 0: p = p[::-1]
    K.tri(p, mat)


def basis(d):
    d = Vector(d).normalized()
    up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(up).normalized(); v = u.cross(d).normalized()
    return u, v


def pole(a, b, r, mat, n=8, caps=(True, True), r1=None, rot=0.0, vt=1.0):
    """a round pole from a to b: uvs once round it and along it (timber grain runs up a pile, rope twists along)"""
    a, b = Vector(a), Vector(b); d = b - a; L = d.length
    if L < 1e-5: return
    u, v = basis(d); r1 = r if r1 is None else r1
    ring = lambda c, rr: [c + (u * math.cos(rot + k * math.tau / n) + v * math.sin(rot + k * math.tau / n)) * rr for k in range(n)]
    A, Bb = ring(a, r), ring(b, r1)
    for k in range(n):
        j = (k + 1) % n; mid = (A[k] + A[j] + Bb[k] + Bb[j]) / 4
        out = mid - (a + d * ((mid - a).dot(d) / L / L))
        Q([A[k], A[j], Bb[j], Bb[k]], mat, uv=[(k / n, 0), ((k + 1) / n, 0), ((k + 1) / n, L / vt), (k / n, L / vt)], out=out)
    if caps[0] and r > 1e-4:
        for k in range(1, n - 1): T3([A[0], A[k], A[k + 1]], mat, out=-d)
    if caps[1] and r1 > 1e-4:
        for k in range(1, n - 1): T3([Bb[0], Bb[k], Bb[k + 1]], mat, out=d)


def lathe(c, prof, mat, n=8, rot=0.0, axis=(0, 1, 0), scale=(1, 1)):
    """a turned shape round an axis at c: prof [(radius, height)] bottom to top; a radius of 0 closes it. mat: one
    material, or a function (ring index) -> material (bands). scale: squash it across (an egg-shaped buoy)"""
    c = Vector(c); ax = Vector(axis).normalized(); u, v = basis(ax)
    rings = [[c + ax * h + (u * math.cos(rot + k * math.tau / n) * scale[0] + v * math.sin(rot + k * math.tau / n) * scale[1]) * r for k in range(n)] for r, h in prof]
    s = 0.0
    for i in range(len(prof) - 1):
        (r0, h0), (r1, h1) = prof[i], prof[i + 1]; L = math.hypot(r1 - r0, h1 - h0); A, Bb = rings[i], rings[i + 1]
        m = mat(i) if callable(mat) else mat
        for k in range(n):
            j = (k + 1) % n; mid = (A[k] + A[j] + Bb[k] + Bb[j]) / 4
            ctr = c + ax * ((mid - c).dot(ax)); out = mid - ctr
            if out.length < 1e-6 or abs(h1 - h0) < 1e-6: out = ax * (1 if r1 < r0 else -1) if abs(h1 - h0) < 1e-6 else ax * (1 if h1 > h0 else -1)
            uv = [(k / n, s), ((k + 1) / n, s), ((k + 1) / n, s + L), (k / n, s + L)]
            if r0 < 1e-5: T3([A[k], Bb[j], Bb[k]], m, out=out)
            elif r1 < 1e-5: T3([A[k], A[j], Bb[k]], m, out=out)
            else: Q([A[k], A[j], Bb[j], Bb[k]], m, uv=uv, out=out)
        s += L


def torus(c, axis, R, r, mat, n=8, m=4, rot=0.0, tiles=4, boff=0.35):
    """a ring round axis at c (a tyre, a life ring): R to the tube's middle, r the tube. mat: one, or (segment) -> mat.
    uvs: u round the ring (tiles times), v round the tube"""
    c = Vector(c); ax = Vector(axis).normalized(); u, v = basis(ax)
    def P(i, j):
        a = rot + i * math.tau / n; b = j * math.tau / m + boff  # (boff: no face dead flat to the axis, so neighbours never read as coplanar)
        rd = u * math.cos(a) + v * math.sin(a)
        return c + rd * (R + r * math.cos(b)) + ax * (r * math.sin(b))
    for i in range(n):
        mm = mat(i) if callable(mat) else mat
        for j in range(m):
            p = [P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)]
            a = rot + (i + 0.5) * math.tau / n; rd = u * math.cos(a) + v * math.sin(a)
            mid = sum(p, Vector()) / 4; out = mid - (c + rd * R)
            Q(p, mm, uv=[(i / n * tiles, j / m), ((i + 1) / n * tiles, j / m), ((i + 1) / n * tiles, (j + 1) / m), (i / n * tiles, (j + 1) / m)], out=out)


def tb(mn, mx, mat, along='x', skip=(), t=1.0, mats=None):
    """a timber box whose grain runs along `along` (explicit uvs: v along the grain). skip: faces left out
    ('px','nx','py','ny','pz','nz'); mats: {face: mat} overrides"""
    (x0, y0, z0), (x1, y1, z1) = mn, mx
    A = 'xyz'.index(along)
    F = {'px': ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0)), 'nx': ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0)),
         'py': ([(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], (0, 1, 0)), 'ny': ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
         'pz': ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)), 'nz': ([(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)], (0, 0, -1))}
    for f, (q, o) in F.items():
        if f in skip: continue
        nax = 'xyz'.index(f[1]); other = [i for i in range(3) if i != nax]
        va = A if A in other else other[1]; ua = [i for i in other if i != va][0]
        Q(q, (mats or {}).get(f, mat), uv=[(p[ua] / t, p[va] / t) for p in q], out=o)


def plate(pts, z0, z1, mat, side=None, uvf=None):
    """a flat shape facing +z: pts [(x, y)] (convex) from z0 to z1; uvf(x, y) -> uv for the front"""
    n = len(pts); cx = sum(p[0] for p in pts) / n; cy = sum(p[1] for p in pts) / n
    for k in range(1, n - 1):
        T3([(pts[0][0], pts[0][1], z1), (pts[k][0], pts[k][1], z1), (pts[k + 1][0], pts[k + 1][1], z1)], mat, out=(0, 0, 1))
    for k in range(n):
        (ax, ay), (bx_, by) = pts[k], pts[(k + 1) % n]
        Q([(ax, ay, z0), (bx_, by, z0), (bx_, by, z1), (ax, ay, z1)], side or mat, out=((ax + bx_) / 2 - cx, (ay + by) / 2 - cy, 0))


def both(p, mat, uv):
    """a single sheet seen from both sides (alpha materials draw both sides, the rest need the back)"""
    K.quad([Vector(q) for q in p], mat, uv=uv); K.quad([Vector(q) for q in p[::-1]], mat, uv=uv[::-1])


def rope(pts, r=0.018, n=4):
    for a, b in zip(pts, pts[1:]): pole(a, b, r, 'prope', n=n, caps=(False, False), vt=0.25)


def sag(a, b, dip, k=6):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / k) - Vector((0, dip * 4 * (i / k) * (1 - i / k), 0)) for i in range(k + 1)]


# ------------------------------------------------------------ the pier
DECK = [(28, 4.5, 62, 7.5), (42, 2, 50, 4.5), (42, 7.5, 50, 10.5)]  # (the deck boxes, x0 z0 x1 z1)
PITCH = 1 / 3  # a board every third of a metre: the deck's ends and the wide bit's sides fall in gaps


def deck():
    rr = K.rng
    # what shows between the boards: the deck's top, dark
    for (x0, z0, x1, z1) in DECK:
        Q([(x0, 0.0, z0), (x0, 0.0, z1), (x1, 0.0, z1), (x1, 0.0, z0)], 'pgap', out=(0, 1, 0))
    k = 0; x = 28.0
    while x < 62 - 1e-6:
        a, b = x + 0.015, x + PITCH - 0.015
        wide = a > 42 and b < 50
        z0, z1 = (2.0, 10.5) if wide else (4.5, 7.5)
        h = 0.03 + rr.random() * 0.014
        m = 'pdeck2' if rr.random() < 0.18 else 'pdeck3' if rr.random() < 0.15 else 'pdeck'
        if k == 20: m = 'pdeckp'  # (somebody had pink paint left over)
        # a board: top, its two sides down to the deck (its ends are behind the fascia)
        if rr.random() < 0.08 and not wide:  # a split one: two lengths butting
            s = z0 + 0.8 + rr.random() * (z1 - z0 - 1.6)
            tb((a, 0, z0), (b, h, s - 0.01), m, along='z', skip=('ny', 'nz', 'pz')); tb((a, 0, s + 0.01), (b, h - 0.006, z1), m, along='z', skip=('ny', 'nz', 'pz'))
        else:
            tb((a, 0, z0), (b, h, z1), m, along='z', skip=('ny', 'nz', 'pz'))
        x += PITCH; k += 1
    # the fascia beam round the edge (it hides the board ends), runs along x over the corners
    F0, F1 = -0.27, 0.052; t = 0.07
    runs_x = [(28, 42, 4.5, -1), (50, 62, 4.5, -1), (42, 50, 2.0, -1), (28, 42, 7.5, 1), (50, 62, 7.5, 1), (42, 50, 10.5, 1)]
    for (a, b, z, s) in runs_x:
        e0, e1 = (a - t if a in (42, 50) else a), (b + t if b in (42, 50) else b)
        zz = (z - t, z) if s < 0 else (z, z + t)
        tb((e0, F0, zz[0]), (e1, F1, zz[1]), 'pbeam', along='x', skip=('nx', 'px') if a not in (42, 50) and b not in (42, 50) else ())
    for (x, z0, z1, s) in [(42, 2.0, 4.5, -1), (50, 2.0, 4.5, 1), (42, 7.5, 10.5, -1), (50, 7.5, 10.5, 1)]:
        xx = (x - t, x) if s < 0 else (x, x + t)
        tb((xx[0], F0, z0 + (0 if z0 == 2.0 else 0)), (xx[1], F1, z1), 'pbeam', along='z', skip=('nz', 'pz'))
    # the land ends: a sleeper half in the sand where it comes ashore
    for (x0, x1) in ((27.55, 28.0), (62.0, 62.45)):
        tb((x0, -0.12, 4.3), (x1, 0.05, 7.7), 'pbeam', along='z')
    # headstocks: a beam across under each pair of piles, its ends poking out past the fascia
    for x in [30 + 4 * i for i in range(8)]:
        tb((x - 0.11, -0.34, 4.28), (x + 0.11, -0.1, 7.72), 'pbeam', along='z')


def piles():
    """round timber piles standing proud of the edges, down into the sea (you see them in the shallows at the ends)"""
    rr = K.rng
    at = [(x, z) for x in (30, 34, 38, 54, 58) for z in (4.27, 7.73)]
    at += [(41.79, 2.25), (46.0, 1.79), (50.21, 2.25), (41.79, 10.25), (46.0, 10.71), (50.21, 10.25)]  # (the wide bit's: its corners and middles)
    for (x, z) in at:
        top = 0.32 + rr.random() * 0.1; lean = (rr.random() - 0.5) * 0.06
        r = 0.15 + rr.random() * 0.02
        ro = rr.random()
        pole((x + lean, -2.5, z), (x, top, z), r, 'ppile', n=6, caps=(False, False), rot=ro)
        lathe((x, top - 0.012, z), [(r + 0.016, 0.0), (0.0, 0.075)], 'pzinc', n=6, rot=ro)  # a zinc cap against the rain
        ax = lambda y: x + lean * (top - y) / (top + 2.5)  # (the pile's middle at height y: it leans)
        pole((ax(WY - 0.3), WY - 0.3, z), (ax(WY + 0.07), WY + 0.07, z), r + 0.022, 'pweed', n=6, caps=(False, False), rot=ro)
        for kk in range(1):  # a barnacle just over the weed
            a = rr.random() * math.tau; y = WY + 0.12 + rr.random() * 0.1
            c = Vector((x + math.cos(a) * (r + 0.004), y, z + math.sin(a) * (r + 0.004)))
            pole(c - Vector((0, 0.018, 0)), c + Vector((0, 0.018, 0)), 0.026, 'pbarn', n=3, r1=0.01, caps=(False, True))


def bollard(x, z, cap='pcap'):
    """a cast-iron bollard over the game's 0.36 m box: a bolted base plate, a waisted barrel, a lipped candy cap"""
    tb((x - 0.2, 0.03, z - 0.2), (x + 0.2, 0.075, z + 0.2), 'piron', skip=('ny',))
    lathe((x, 0.075, z), [(0.155, 0.0), (0.128, 0.26), (0.16, 0.44)], 'piron', n=8, rot=0.39)
    lathe((x, 0.075, z), [(0.16, 0.44), (0.205, 0.47), (0.2, 0.52), (0.0, 0.565)], cap, n=8, rot=0.39)


def fender(x, z, s, y=-0.2, rot=0.0):
    """a tyre hung on the fascia (s: which way is out, along z), on a rope to the deck edge"""
    c = (x, y, z + s * 0.12)
    torus(c, (0, 0, 1), 0.24, 0.095, 'ptyre', n=8, m=4, rot=rot, tiles=4)
    top = Vector((x, y + 0.33, z + s * 0.12)); edge = Vector((x, 0.06, z + s * 0.01))
    rope([top, edge + Vector((0, 0, s * 0.05)), edge + Vector((0, 0.01, -s * 0.12))], r=0.016, n=3)


def gull(c, yaw, scale=1.0):
    """a seagull standing, looking smug: a body, a head with a yellow beak, grey folded wings, a black tail tip, legs"""
    c = Vector(c); ca, sa = math.cos(yaw), math.sin(yaw)
    def P(x, y, z): return c + Vector((x * ca - z * sa, y, x * sa + z * ca)) * scale  # (local: x forward, z left)
    body = [P(0.16, 0.16, 0), P(0.0, 0.22, 0), P(-0.18, 0.17, 0), P(-0.26, 0.14, 0), P(0.0, 0.08, 0)]
    w = 0.075
    nose, back = P(0.18, 0.15, 0), P(-0.28, 0.15, 0)
    ring = [P(0.08, 0.215, 0), P(0.08, 0.15, w), P(0.08, 0.09, 0), P(0.08, 0.15, -w), P(-0.12, 0.2, 0), P(-0.12, 0.15, w * 0.9), P(-0.12, 0.1, 0), P(-0.12, 0.15, -w * 0.9)]
    F = ring[:4]; Bk = ring[4:]
    for k in range(4):
        j = (k + 1) % 4
        T3([nose, F[k], F[j]], 'pgull', out=F[k] + F[j] - nose * 2 + (P(1, 0, 0) - c) * 0.0)
        Q([F[k], Bk[k], Bk[j], F[j]], 'pgull', out=(F[k] + F[j]) / 2 - (P(-0.02, 0.15, 0)))
        T3([back, Bk[j], Bk[k]], 'pgull' if k != 0 else 'pgullg', out=(Bk[k] + Bk[j]) / 2 - back)
    for s in (-1, 1):  # folded wings: a grey slab down each side, black tips crossed over the tail
        a, b, d, e = P(0.06, 0.2, s * 0.07), P(-0.3, 0.17, s * 0.03), P(-0.3, 0.12, s * 0.035), P(0.04, 0.12, s * 0.078)
        Q([a, b, d, e], 'pgullg', out=P(0, 0, s) - P(0, 0, 0)); Q([a, e, d, b], 'pgullg', out=P(0, 0, -s) - P(0, 0, 0))
        T3([b, d, P(-0.36, 0.14, s * 0.01)], 'pblack', out=P(0, 0, s) - P(0, 0, 0)); T3([b, P(-0.36, 0.14, s * 0.01), d], 'pblack', out=P(0, 0, -s) - P(0, 0, 0))
    lathe(P(0.13, 0.25, 0), [(0.0, -0.06), (0.05, -0.04), (0.055, 0.0), (0.035, 0.04), (0.0, 0.05)], 'pgull', n=5)  # the head
    hb = P(0.17, 0.25, 0); tip = P(0.27, 0.235, 0)
    for (o1, o2) in ((P(0.17, 0.265, 0.012), P(0.17, 0.24, 0.012)), (P(0.17, 0.24, -0.012), P(0.17, 0.265, -0.012))):
        T3([o1, tip, o2], 'pbeak', out=o1 + o2 - hb * 2)
    T3([P(0.17, 0.265, 0.012), P(0.17, 0.265, -0.012), tip], 'pbeak', out=(0, 1, 0)); T3([P(0.17, 0.24, -0.012), P(0.17, 0.24, 0.012), tip], 'pbeak', out=(0, -1, 0))
    pole(P(0.15, 0.268, -0.062), P(0.15, 0.268, 0.062), 0.011, 'pblack', n=3)  # beady eyes: a little rod through the head, its ends showing
    for s in (-1, 1):  # legs
        pole(P(0.0, 0.1, s * 0.03), P(0.01, 0.0, s * 0.035), 0.008, 'pbeak', n=3, caps=(False, False))
        T3([P(0.01, 0.002, s * 0.035), P(0.07, 0.002, s * 0.06), P(0.07, 0.002, s * 0.01)], 'pbeak', out=(0, 1, 0))


def rails():
    """the handrails (the game's boxes: posts every 2 m, a rail at 0.9-1.0): square posts with a chamfered head, a rail"""
    for (x0, x1) in ((33, 42), (50, 57)):
        for (z, s) in ((4.56, -1), (7.44, 1)):
            x = x0 + 0.1
            while x < x1:
                c = x + 0.05
                tb((c - 0.06, 0.03, z - 0.065), (c + 0.06, 0.88, z + 0.065), 'prail', along='y', skip=('ny', 'py'))
                x += 2
            tb((x0 - 0.02, 0.88, z - 0.075), (x1 + 0.02, 1.0, z + 0.075), 'prail', along='x')
            # a chamfered cap on the rail: the top's edges taken off
            for (a, b) in ((z - 0.075, z - 0.04), (z + 0.04, z + 0.075)):
                o = -1 if a < z else 1
                Q([(x0 - 0.02, 1.0, z + o * 0.075), (x1 + 0.02, 1.0, z + o * 0.075), (x1 + 0.02, 1.025, z + o * 0.04), (x0 - 0.02, 1.025, z + o * 0.04)], 'prail', out=(0, 1, o),
                  uv=[(0, x0), (0, x1), (0.04, x1), (0.04, x0)])
            Q([(x0 - 0.02, 1.025, z - 0.04), (x0 - 0.02, 1.025, z + 0.04), (x1 + 0.02, 1.025, z + 0.04), (x1 + 0.02, 1.025, z - 0.04)], 'prail', out=(0, 1, 0),
              uv=[(0, x0), (0.08, x0), (0.08, x1), (0, x1)])
            for xe in (x0 - 0.02, x1 + 0.02):
                o = -1 if xe < x0 else 1
                Q([(xe, 1.0, z - 0.075), (xe, 1.0, z + 0.075), (xe, 1.025, z + 0.04), (xe, 1.025, z - 0.04)], 'prail', out=(o, 0, 0))


def net_sheet(P, nu, nv, mat, tile=(1.0, 1.0)):
    """a net from a function P(u, v) (0..1 each) -> point: nu x nv cells, uvs in metres along it"""
    pts = [[Vector(P(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    Lu = sum((pts[i + 1][0] - pts[i][0]).length for i in range(nu)); Lv = sum((pts[0][j + 1] - pts[0][j]).length for j in range(nv))
    for i in range(nu):
        for j in range(nv):
            q = [pts[i][j], pts[i + 1][j], pts[i + 1][j + 1], pts[i][j + 1]]
            uv = [(i / nu * Lu / 0.5, j / nv * Lv / 0.5), ((i + 1) / nu * Lu / 0.5, j / nv * Lv / 0.5), ((i + 1) / nu * Lu / 0.5, (j + 1) / nv * Lv / 0.5), (i / nu * Lu / 0.5, (j + 1) / nv * Lv / 0.5)]
            K.quad(q, mat, uv=uv)


def pier_extras():
    rr = K.rng
    for i, x in enumerate((32, 38, 54, 60)):
        for j, z in enumerate((4.75, 7.25)): bollard(x, z, ('pcap', 'pcapp', 'pcapc')[(i + j * 2) % 3])
    gull((32, 0.635, 4.75), 2.2)  # on the first bollard, watching you walk in
    # the mooring line: still round the last bollard, over the edge and into the sea. no boat
    b = Vector((60, 0.42, 7.25))
    lp = [b + Vector((math.cos(a) * 0.15, 0.0 if i % 2 else 0.03, math.sin(a) * 0.15)) for i, a in enumerate([k * math.tau / 7 for k in range(8)])]
    rope(lp, r=0.022, n=4)
    rope([lp[-1], Vector((60.25, 0.2, 7.55)), Vector((60.4, 0.08, 7.82)), Vector((60.55, -0.12, 7.95)), Vector((60.8, -0.45, 8.1))], r=0.022, n=4)
    # tyre fenders where boats come alongside: the wide bit's seaward faces, by two bollards
    for (x, z, s) in ((43.6, 2.0, -1), (48.4, 2.0, -1), (44.6, 10.5, 1), (47.6, 10.5, 1), (54.0, 4.5, -1)):
        fender(x, z if s < 0 else z, s, y=-0.2 + rr.random() * 0.04, rot=rr.random())
    rails()
    # a net drying over the north rail by the shack, hanging down both sides
    def nP(u, v):
        x = 50.6 + u * 2.4; sw = 0.12 * math.sin(u * math.pi * 2.0)  # (it hangs in folds)
        if v < 0.5:  # the outside: up from just over the water to the rail
            t = v / 0.5; return (x, 0.15 + t * 0.87 - 0.05 * math.sin(u * math.pi * 3) * (1 - t), 7.62 + 0.04 * (1 - t) + sw * (1 - t) * 0.3)
        t = (v - 0.5) / 0.5; return (x, 1.02 - t * (0.7 + 0.15 * math.sin(u * math.pi * 2.5)), 7.29 - sw * t * 0.3)
    net_sheet(nP, 5, 4, 'pnetg')
    for k in range(4): lathe((50.8 + k * 0.62, 1.04, 7.44), [(0.0, -0.05), (0.045, -0.03), (0.045, 0.03), (0.0, 0.05)], ('pbuoyy', 'pbuoyc', 'pbuoyp')[k % 3], n=5, axis=(0, 0, 1))


# ------------------------------------------------------------ the bait shack
X0, X1, ZF, ZB = 43.0, 49.0, 8.2, 10.4  # its outside faces: west, east, front (the pier side), back
HX0, HX1, HY0, HY1 = 44.2, 47.8, 1.0, 2.0  # the hatch


def clad(axis, c, a0, a1, y0, y1, out, mat='pwall', t=1.6):
    """a wall face (axis 'x': runs along x at z = c) from a0 to a1, y0 to y1, facing out (+1 / -1)"""
    if axis == 'x': p = [(a0, y0, c), (a1, y0, c), (a1, y1, c), (a0, y1, c)]; o = (0, 0, out)
    else: p = [(c, y0, a0), (c, y0, a1), (c, y1, a1), (c, y1, a0)]; o = (out, 0, 0)
    uv = [(a0 / t, y0 / t), (a1 / t, y0 / t), (a1 / t, y1 / t), (a0 / t, y1 / t)]
    Q(p, mat, uv=uv if out > 0 else [(-u, v) for u, v in uv], out=o)


def shack():
    rr = K.rng
    # outside: the boards (front round the hatch), corner posts, a skirting board
    clad('x', ZF, X0, HX0, 0.0, 2.8, -1); clad('x', ZF, HX1, X1, 0.0, 2.8, -1); clad('x', ZF, HX0, HX1, 0.0, HY0, -1); clad('x', ZF, HX0, HX1, HY1, 2.8, -1)
    clad('x', ZB, X0, X1, 0.0, 2.8, 1); clad('z', X0, ZF, ZB, 0.0, 2.8, -1); clad('z', X1, ZF, ZB, 0.0, 2.8, 1)
    for (x, z, sx, sz) in ((X0, ZF, -1, -1), (X1, ZF, 1, -1), (X0, ZB, -1, 1), (X1, ZB, 1, 1)):
        xa, xb = sorted((x - sx * 0.08, x + sx * 0.04)); za, zb = sorted((z - sz * 0.08, z + sz * 0.04))
        tb((xa, 0.03, za), (xb, 2.82, zb), 'ptrimc', along='y', skip=('ny',))
    for (axis, c, a0, a1, o) in (('x', ZF, X0 + 0.04, X1 - 0.04, -1), ('x', ZB, X0 + 0.04, X1 - 0.04, 1), ('z', X0, ZF + 0.04, ZB - 0.04, -1), ('z', X1, ZF + 0.04, ZB - 0.04, 1)):
        c0, c1 = sorted((c, c + o * 0.025))
        inner = ('nz' if o > 0 else 'pz') if axis == 'x' else ('nx' if o > 0 else 'px')  # (its back is on the wall)
        if axis == 'x': tb((a0, 0.03, c0), (a1, 0.24, c1), 'ppile', along='x', skip=('ny', inner))
        else: tb((c0, 0.03, a0), (c1, 0.24, a1), 'ppile', along='z', skip=('ny', inner))
    # patch boards nailed on crooked (over the holes, presumably)
    for (axis, c, o, a, y, L, ang, m) in (('x', ZB, 1, 44.2, 1.3, 1.1, 0.12, 'pdeckp'), ('x', ZB, 1, 47.0, 0.6, 0.9, -0.2, 'pdeck2'), ('z', X0, -1, 8.9, 1.9, 0.8, 0.3, 'pdeck3'),
                                          ('z', X1, 1, 9.0, 0.5, 0.9, -0.1, 'pdeck'), ('x', ZF, -1, 43.25, 0.45, 0.8, 0.15, 'pdeck2'), ('x', ZF, -1, 47.9, 0.35, 1.0, -0.08, 'pdeckp')):
        w, th = 0.16, 0.018
        dx, dy = math.cos(ang), math.sin(ang)
        corners = [(0, -w / 2), (L, -w / 2), (L, w / 2), (0, w / 2)]
        pts2 = [(a + u * dx - v * dy, y + u * dy + v * dx) for u, v in corners]
        if axis == 'x':
            z0, z1 = (c, c + o * th) if o > 0 else (c + o * th, c)
            front = [(p[0], p[1], c + o * th) for p in pts2]; back = [(p[0], p[1], c) for p in pts2]
        else:
            front = [(c + o * th, p[1], p[0]) for p in pts2]; back = [(c, p[1], p[0]) for p in pts2]
        nrm = (0, 0, o) if axis == 'x' else (o, 0, 0)
        Q(front, m, uv=[(0, 0), (L, 0), (L, w), (0, w)], out=nrm)
        for i in range(4):
            j = (i + 1) % 4; mid = [(front[i][q] + front[j][q]) / 2 for q in range(3)]; ctr = [sum(f[q] for f in front) / 4 for q in range(3)]
            Q([back[i], back[j], front[j], front[i]], m, out=tuple(mid[q] - ctr[q] for q in range(3)))
    # the hatch: its reveal (the wall's thickness, raw), a frame, the counter (the game's box) on two brackets
    for (p, o) in ((((HX0, HY0, 8.2), (HX0, HY0, 8.4), (HX0, HY1, 8.4), (HX0, HY1, 8.2)), (1, 0, 0)), (((HX1, HY0, 8.2), (HX1, HY1, 8.2), (HX1, HY1, 8.4), (HX1, HY0, 8.4)), (-1, 0, 0)),
                   (((HX0, HY1, 8.2), (HX1, HY1, 8.2), (HX1, HY1, 8.4), (HX0, HY1, 8.4)), (0, -1, 0)), (((HX0, HY0, 8.2), (HX0, HY0, 8.4), (HX1, HY0, 8.4), (HX1, HY0, 8.2)), (0, 1, 0))):
        Q(p, 'pin', out=o)
    for x in (HX0 - 0.08, HX1):
        tb((x, HY0 - 0.04, 8.15), (x + 0.08, HY1, 8.2), 'ptrimy', along='y', skip=('pz',))
    tb((43.2, 1.0, 7.95), (48.8, 1.08, 8.2), 'ptrimy', along='x', skip=('pz',))  # the counter
    for x in (43.6, 48.4):  # its brackets: a knee down to the wall
        a, b, c = (x, 0.99, 8.0), (x, 0.99, 8.19), (x, 0.62, 8.19)
        for dx in (-0.025, 0.025):
            T3([(a[0] + dx, a[1], a[2]), (b[0] + dx, b[1], b[2]), (c[0] + dx, c[1], c[2])], 'ptrimy', out=(dx, 0, 0))
        Q([(x - 0.025, 0.99, 8.0), (x + 0.025, 0.99, 8.0), (x + 0.025, 0.62, 8.19), (x - 0.025, 0.62, 8.19)], 'ptrimy', out=(0, -1, -1))
    # the flap: hinged on the frame's head, propped up a touch over level on two sticks from the counter
    ang = math.radians(7); L = 1.06; hy = 2.02
    def fp(u, d, th): return Vector((u, hy + d * math.sin(ang) - th * math.cos(ang), 8.17 - d * math.cos(ang) - th * math.sin(ang)))
    a0, a1 = HX0 - 0.1, HX1 + 0.1
    top = [fp(a0, 0, 0), fp(a1, 0, 0), fp(a1, L, 0), fp(a0, L, 0)]; bot = [fp(a0, 0, -0.04), fp(a1, 0, -0.04), fp(a1, L, -0.04), fp(a0, L, -0.04)]
    Q(top, 'pwall', uv=[(a0 / 1.6, 0), (a1 / 1.6, 0), (a1 / 1.6, L / 1.6), (a0 / 1.6, L / 1.6)], out=(0, 1, 0))
    Q(bot, 'ptrimp', uv=[(a0, 0), (a1, 0), (a1, L), (a0, L)], out=(0, -1, 0))  # (painted pink inside: when it's up, that's what you see)
    for (i, j) in ((0, 1), (1, 2), (2, 3), (3, 0)):
        Q([top[i], top[j], bot[j], bot[i]], 'ptrimy', out=(top[i] + top[j]) / 2 - (top[0] + top[2]) / 2)
    for x in (HX0 + 0.2, HX1 - 0.2):  # iron hinge straps on the flap's top
        s0, s1 = fp(x - 0.04, 0.0, 0.004), fp(x + 0.04, 0.0, 0.004); e0, e1 = fp(x - 0.04, 0.35, 0.004), fp(x + 0.04, 0.35, 0.004)
        Q([s0, s1, e1, e0], 'piron', out=(0, 1, 0))
    for x in (HX0 + 0.25, HX1 - 0.25):  # the props: sticks from the counter's front edge up under the flap's lip
        tip = fp(x, L - 0.12, -0.045)
        pole((x, 1.08, 7.99), tip, 0.025, 'ppile', n=5, caps=(False, False))
    # on the counter: a bait bucket (a fish tail sticking out) and a jar of worms
    lathe((44.55, 1.08, 8.07), [(0.09, 0.0), (0.11, 0.2), (0.0, 0.16)], 'pbucket', n=7)
    T3([(44.55, 1.24, 8.07), (44.5, 1.42, 8.02), (44.62, 1.4, 8.11)], 'pfish', out=(1, 0, -1)); T3([(44.55, 1.24, 8.07), (44.62, 1.4, 8.11), (44.5, 1.42, 8.02)], 'pfish', out=(-1, 0, 1))
    lathe((47.5, 1.08, 8.08), [(0.065, 0.0), (0.065, 0.15), (0.045, 0.17), (0.0, 0.18)], lambda i: 'pjar' if i < 1 else 'ptin2', n=6)
    # the sign (the game's ad, on the wall over the hatch) in a frame; the frame's foot is the hinge rail
    for (mn, mx, al) in (((43.52, 2.0, 8.13), (48.48, 2.06, 8.2), 'x'), ((43.52, 2.75, 8.13), (48.48, 2.8, 8.2), 'x'),
                         ((43.52, 2.06, 8.13), (43.6, 2.75, 8.2), 'y'), ((48.4, 2.06, 8.13), (48.48, 2.75, 8.2), 'y')):
        tb(mn, mx, 'ptrimp', along=al, skip=('pz',))
    # two little lamps under the roof's overhang, either side of the sign
    for x in (43.3, 48.7):
        tb((x - 0.02, 2.55, 8.12), (x + 0.02, 2.62, 8.2), 'piron', skip=('pz',))
        pole((x, 2.6, 8.14), (x, 2.6, 7.98), 0.012, 'piron', n=4, caps=(False, False))
        lathe((x, 2.47, 7.96), [(0.0, 0.0), (0.05, 0.04), (0.04, 0.11), (0.0, 0.13)], 'pbulb', n=5)
        lathe((x, 2.6, 7.96), [(0.075, -0.0), (0.0, 0.04)], 'piron', n=6)
    # a life ring on the front wall, left of the hatch (red and white quarters)
    torus((43.62, 1.55, 8.2 - 0.07), (0, 0, 1), 0.27, 0.065, lambda i: 'pbuoyr' if (i // 2) % 2 == 0 else 'pbuoyw', n=12, m=4, rot=0.2, tiles=1)
    rope([Vector((43.62, 1.89, 8.19)), Vector((43.62, 1.84, 8.12))], r=0.012)
    # hand-painted boards: "worms: no refunds" right of the hatch, "gone fishin" on the back, each on a nail, crooked
    def tag(cx, cy, c, axis, o, ang, half):
        w, h = 0.56, 0.26
        pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
        R = [(cx + u * math.cos(ang) - v * math.sin(ang), cy + u * math.sin(ang) + v * math.cos(ang)) for u, v in pts]
        va, vb = (0.0, 0.5) if half else (0.5, 1.0)  # (half 0: "gone fishin", the image's top; 1: "worms")
        uv = [(0, va), (1, va), (1, vb), (0, vb)]
        if o < 0: front = [(cx - (p[0] - cx), p[1], c - 0.025) for p in R]  # (facing -z: mirrored, so it reads from the front)
        else: front = [(p[0], p[1], c + 0.025) for p in R]
        back = [(f[0], f[1], c) for f in front]; nrm = (0, 0, o)
        Q(front, 'ptags', uv=uv, out=nrm)
        for i in range(4):
            j = (i + 1) % 4; ctr = Vector([sum(f[q] for f in front) / 4 for q in range(3)])
            Q([back[i], back[j], front[j], front[i]], 'pbeam', out=(Vector(front[i]) + Vector(front[j])) / 2 - ctr)
    tag(48.42, 1.5, ZF, 'x', -1, -0.06, 1)
    DX0, DX1, DH = 45.45, 46.55, 2.05
    clad('x', ZB + 0.03, DX0, DX1, 0.03, DH, 1, 'pdoor', 1.6)
    for (mn, mx) in (((DX0, 0.03, ZB), (DX1, DH, ZB + 0.03)),):  # its edges
        tb(mn, mx, 'pdoor', along='y', skip=('pz', 'nz', 'ny'))
    for (mn, mx, al) in (((DX0 - 0.09, 0.03, ZB), (DX0, DH + 0.09, ZB + 0.045), 'y'), ((DX1, 0.03, ZB), (DX1 + 0.09, DH + 0.09, ZB + 0.045), 'y'),
                         ((DX0, DH, ZB), (DX1, DH + 0.09, ZB + 0.045), 'x')):
        tb(mn, mx, 'ptrimy', along=al, skip=('nz', 'ny'))
    for y in (0.35, 1.7):  # z-braced ledges: two rails across it
        tb((DX0 + 0.06, y, ZB + 0.03), (DX1 - 0.06, y + 0.12, ZB + 0.05), 'pdoor', along='x', skip=('nz',))
    tb((DX1 - 0.16, 1.0, ZB + 0.03), (DX1 - 0.06, 1.1, ZB + 0.05), 'piron', skip=('nz',))  # hasp
    lathe((DX1 - 0.11, 0.9, ZB + 0.07), [(0.0, -0.05), (0.05, -0.04), (0.05, 0.03), (0.0, 0.04)], 'pcap', n=5, axis=(0, 0, 1))  # a padlock (yellow)
    pole((DX1 - 0.14, 0.94, ZB + 0.07), (DX1 - 0.08, 1.02, ZB + 0.07), 0.008, 'pzinc', n=3, caps=(False, False))
    tag(46.0, 1.32, ZB + 0.03, 'x', 1, 0.09, 0)
    # buoys hung on the east wall from a peg on ropes: round candy floats and a striped one
    peg = Vector((X1 + 0.05, 2.25, 9.3))
    pole((X1, 2.25, 9.3), (X1 + 0.09, 2.27, 9.3), 0.02, 'pbeam', n=4, caps=(False, True))
    for (dz, y, r, m, kind) in ((-0.42, 1.55, 0.15, ('pbuoyp', 'pbuoyy'), 0), (-0.05, 1.32, 0.17, ('pbuoyy', 'pbuoyc'), 0), (0.36, 1.62, 0.14, ('pbuoyc', 'pbuoyp'), 0), (0.72, 1.08, 0.13, 'stripe', 1)):
        c = Vector((X1 + r + 0.01, y, 9.3 + dz))
        if kind == 0:
            lathe(c - Vector((0, r, 0)), [(0.0, 0.0), (r * 0.75, r * 0.32), (r, r), (r * 0.75, r * 1.68), (0.03, r * 2.0)], lambda i, m=m: m[1] if i in (1, 2) else m[0], n=7)  # (a band round its belly)
            lathe(c + Vector((0, r, 0)), [(0.03, 0.0), (0.0, 0.06)], 'pblack', n=4)
        else:
            lathe(c - Vector((0, r * 1.8, 0)), [(0.0, 0.0), (r * 0.8, r * 0.3), (r, r * 0.9), (r, r * 1.8), (r, r * 2.7), (r * 0.8, r * 3.3), (0.03, r * 3.6)],
                  lambda i: 'pbuoyy' if i in (2, 4) else 'pbuoyp', n=7)
        rope([peg, c + Vector((0, r * (1.8 if kind else 1.0) + 0.05, 0))], r=0.01, n=3)
    # a net hung on the west wall from two nails, sagging, cork floats along its head rope
    def wP(u, v):
        z = 8.6 + u * 1.45; hang = 2.45 - 0.22 * math.sin(u * math.pi)  # (the head rope sags between the nails)
        y = hang - v * (1.35 - 0.25 * math.sin(u * math.pi * 2.2) * v)
        return (X0 - 0.045 - 0.1 * v * math.sin(u * math.pi) - 0.02 * math.sin(u * 7 + v * 3), y, z + 0.08 * v * math.sin(u * 5))
    net_sheet(wP, 5, 3, 'pnet')
    rope([Vector(wP(i / 6, 0)) + Vector((-0.02, 0.012, 0)) for i in range(7)], r=0.012, n=3)
    for k in range(5):
        p = Vector(wP((k + 0.5) / 5, 0)) + Vector((-0.02, -0.02, 0))
        lathe(p, [(0.0, -0.06), (0.04, -0.035), (0.04, 0.035), (0.0, 0.06)], ('pbuoyp', 'pbuoyy', 'pbuoyc')[k % 3], n=5, axis=(0, 0, 1))
    # inside (seen through the hatch): dark boards, a ceiling, a bulb on its flex, a shelf of tins, a trophy fish
    for (axis, c, a0, a1, o) in (('x', 8.4, 43.2, 48.8, 1), ('x', 10.2, 43.2, 48.8, -1), ('z', 43.2, 8.4, 10.2, 1), ('z', 48.8, 8.4, 10.2, -1)):
        if axis == 'x' and o > 0:
            clad('x', c, a0, HX0, 0, 2.8, o, 'pinside', 1.0); clad('x', c, HX1, a1, 0, 2.8, o, 'pinside', 1.0)
            clad('x', c, HX0, HX1, 0, HY0, o, 'pinside', 1.0); clad('x', c, HX0, HX1, HY1, 2.8, o, 'pinside', 1.0)
        else: clad(axis, c, a0, a1, 0, 2.8, o, 'pinside', 1.0)
    Q([(43.2, 2.8, 8.4), (48.8, 2.8, 8.4), (48.8, 2.8, 10.2), (43.2, 2.8, 10.2)], 'pinside', out=(0, -1, 0))
    for x in (44.6, 46.0, 47.4): tb((x - 0.05, 2.62, 8.4), (x + 0.05, 2.8, 10.2), 'pbeam', along='z', skip=('py', 'nz', 'pz'))
    pole((46.0, 2.62, 9.3), (46.0, 2.25, 9.3), 0.008, 'pblack', n=3, caps=(False, False))
    lathe((46.0, 2.1, 9.3), [(0.0, 0.0), (0.045, 0.03), (0.05, 0.08), (0.02, 0.15), (0.0, 0.15)], 'pbulb', n=6)
    tb((43.6, 1.55, 9.95), (48.4, 1.59, 10.2), 'pbeam', along='x', skip=('pz',))
    for k in range(5):
        x = 44.2 + k * 0.9 + rr.random() * 0.2; m = ['ptin2', 'pjar', 'pbucket'][k % 3]
        lathe((x, 1.59, 10.08), [(0.065, 0.0), (0.065, 0.12 + rr.random() * 0.08), (0.0, 0.13)], m, n=5)
    fish = [(-0.32, 0.0), (-0.12, 0.11), (0.14, 0.09), (0.3, 0.0), (0.14, -0.08), (-0.12, -0.09)]
    tb((45.5, 1.85, 10.17), (46.5, 2.25, 10.2), 'ppost', along='x', skip=('pz',))  # its plaque
    fx, fy = 46.0, 2.05
    pts = [(fx + x, fy + y) for x, y in fish]
    for k in range(1, len(pts) - 1): T3([(pts[0][0], pts[0][1], 10.13), (pts[k][0], pts[k][1], 10.13), (pts[k + 1][0], pts[k + 1][1], 10.13)], 'pfish', out=(0, 0, -1))
    for k in range(len(pts)): Q([(pts[k][0], pts[k][1], 10.13), (pts[(k + 1) % 6][0], pts[(k + 1) % 6][1], 10.13), (pts[(k + 1) % 6][0], pts[(k + 1) % 6][1], 10.17), (pts[k][0], pts[k][1], 10.17)], 'pfishb', out=(pts[k][0] + pts[(k + 1) % 6][0] - 2 * fx, pts[k][1] + pts[(k + 1) % 6][1] - 2 * fy, 0))
    T3([(fx + 0.3, fy, 10.14), (fx + 0.46, fy + 0.13, 10.14), (fx + 0.46, fy - 0.13, 10.14)], 'pfish', out=(0, 0, -1))


def roof():
    """the tin roof: fascia boards round the game's slab, four corrugated sheets over it (real ridges, one pink, one
    bare), a tyre holding it down, a gull"""
    x0, y0, z0, x1, y1, z1 = 42.6, 2.8, 7.8, 49.4, 3.05, 10.8
    t = 0.025
    tb((x0 - t, y0, z0 - t), (x1 + t, y1, z0), 'ptrimp', along='x'); tb((x0 - t, y0, z1), (x1 + t, y1, z1 + t), 'ptrimp', along='x')
    tb((x0 - t, y0, z0), (x0, y1, z1), 'ptrimp', along='z', skip=('nz', 'pz')); tb((x1, y0, z0), (x1 + t, y1, z1), 'ptrimp', along='z', skip=('nz', 'pz'))
    Q([(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], 'pin', out=(0, 1, 0))  # (the slab's top, under the sheets: no sky through the ridges)
    # the soffit: the slab's underside, outside the walls
    for (a, b, c, d) in (((x0, z0), (x1, z0), (x1, ZF), (x0, ZF)), ((x0, ZB), (x1, ZB), (x1, z1), (x0, z1)), ((x0, ZF), (X0, ZF), (X0, ZB), (x0, ZB)), ((X1, ZF), (x1, ZF), (x1, ZB), (X1, ZB))):
        Q([(a[0], y0, a[1]), (b[0], y0, b[1]), (c[0], y0, c[1]), (d[0], y0, d[1])], 'pin', out=(0, -1, 0))
    # rafter tails poking out under the front and back eaves
    for k in range(7):
        x = 43.3 + k * 0.9
        for (za, zb, sk) in ((z0 + 0.02, 8.12, 'pz'), (ZB, z1 - 0.02, 'nz')):
            tb((x - 0.035, y0 - 0.1, za), (x + 0.035, y0, zb), 'pbeam', along='z', skip=('py', sk))
    # the sheets: x 42.5..49.5, front z 7.72 to back 10.88, ridges every 25 cm (the texture's); their edges closed down to the slab
    zA, zB, P = 7.72, 10.88, 0.25
    mats = ['ptin', 'ptinp', 'ptin', 'ptinb']
    for s in range(4):
        sx = 42.5 + s * 1.75; base0 = y1 + 0.008 + (0.006 if s % 2 else 0.0); m = mats[s]
        def Y(z, ridge): return base0 + (0.028 if ridge else 0.0)
        xs = [sx + i * P / 2 for i in range(15)]
        for i in range(14):
            xa, xb = xs[i], xs[i + 1]; ra, rb = i % 2 == 1, (i + 1) % 2 == 1
            ua, ub = (xa - sx) - 0.0625, (xb - sx) - 0.0625
            top = [(xa, Y(zA, ra), zA), (xb, Y(zA, rb), zA), (xb, Y(zB, rb), zB), (xa, Y(zB, ra), zB)]
            Q(top, m, uv=[(ua, zA), (ub, zA), (ub, zB), (ua, zB)], out=(0, 1, 0))
            for zz, o in ((zA, -1), (zB, 1)):  # the sheet's cut edge: its corrugated profile
                Q([(xa, y1 - 0.004, zz), (xb, y1 - 0.004, zz), (xb, Y(zz, rb), zz), (xa, Y(zz, ra), zz)], m, out=(0, 0, o))
        for xe, o in ((sx, -1), (sx + 1.75, 1)):
            if (s == 0 and o < 0) or (s == 3 and o > 0):
                Q([(xe, y1 - 0.004, zA), (xe, y1 - 0.004, zB), (xe, Y(zB, False), zB), (xe, Y(zA, False), zA)], m, out=(o, 0, 0))
    yu = y1 - 0.004  # the sheets' overhang past the fascia, from under
    for (a0, b0, a1_, b1_) in ((42.5, zA, 49.5, z0 - t), (42.5, z1 + t, 49.5, zB), (42.5, z0 - t, x0 - t, z1 + t), (x1 + t, z0 - t, 49.5, z1 + t)):
        Q([(a0, yu, b0), (a1_, yu, b0), (a1_, yu, b1_), (a0, yu, b1_)], 'ptinb', out=(0, -1, 0))
    # a stovepipe out of the back, leaning, with its little hat and a guy wire
    sp0, sp1 = Vector((48.3, y1 + 0.01, 10.2)), Vector((48.42, 3.95, 10.26))
    pole(sp0, sp1, 0.065, 'pzinc', n=6, caps=(False, False))
    lathe(sp0 + Vector((0, 0.03, 0)), [(0.11, 0.0), (0.065, 0.06)], 'pzinc', n=6)
    lathe(sp1 + Vector((0, 0.03, 0)), [(0.0, -0.01), (0.15, 0.0), (0.0, 0.1)], 'piron', n=6)
    pole(sp1 - Vector((0, 0.01, 0)), sp1 + Vector((0, 0.03, 0)), 0.03, 'piron', n=4, caps=(False, False))
    rope([sp1 - Vector((0, 0.25, 0)), Vector((47.2, y1 + 0.04, 10.7))], r=0.006, n=3)
    # a tyre lying on it to hold the tin down, and a gull on the front corner
    torus((47.9, y1 + 0.12, 9.6), (0, 1, 0), 0.25, 0.085, 'ptyre', n=9, m=4, rot=0.3)
    gull((43.0, y1 + 0.05, 7.95), -0.7, 1.05)


def build():
    global K
    d = json.load(open(os.path.join(HERE, 'boxes', 'pier.json')))
    K = Kit(d, seed=46)
    K.ground = -1e9
    solid = [b for b in d['boxes'] if not b.get('deco')]
    K.solids = [(b['min'], b['max']) for b in solid]
    def tris(): return sum(2 if len(f) == 4 else 1 for g in K.geo.values() for f in g['f'])
    stats = []; mark = lambda name: stats.append((name, tris()))
    deck(); mark('deck'); piles(); mark('piles'); pier_extras(); mark('bollards, fenders, rails, net, gull')
    shack(); mark('shack'); roof(); mark('roof')
    print('tris by piece:', ', '.join(f'{n} {t - (stats[i - 1][1] if i else 0)}' for i, (n, t) in enumerate(stats)), '| all', stats[-1][1])
    K.finish(os.path.join(OUTDIR, 'pier.glb'))


build()
