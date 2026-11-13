# The tiki village (shared/map.js tikiBar(), bigTiki(), hut() x2, surfSchool()), drawn over its own boxes as one model per
# map (tiki on Islands, tiki_sd on S&D: the tiki islet and the huts' islet), which stay what you bump into.
# The tiki bar: four fat bamboo posts lashed to a top beam, knee braces, a three-tier palm-thatch roof with flared eaves
# and a ragged fringe, bamboo rafters under it; the counter faced in half-culms with lashed rails, a plank top with
# coconut cups (tiny umbrellas, as the sign says); a plank-doored back bar with its bottles; drum stools; two tiki
# torches and a string of bulbs under the front eave; the sign (the game's) in a lashed bamboo frame.
# The big tiki: a carved log on a basalt plinth, a heavy brow, big shell eyes looking at the bar, a wide grin with
# teeth (one gold), a broad nose, long ears, hands on his belly, a woven band and a hat of palm fronds with a cocktail
# umbrella stuck in it, offerings on the plinth (coconuts, a pineapple, bananas).
# The huts: bamboo walls on short stilts (a woven skirt between the stilt ends, a floor beam), fat corner posts, a door
# frame with the blind rolled up over it, a slatted shutter propped open over the window, a hipped thatch roof with a
# ridge roll and tufts, rafters inside, a striped hammock slung across (hung clear of the sand that blew in).
# The surf school: the boards (the game's three colours) stuck nose-up in sand mounds, leaning, one with a shark bite
# out of it ("lesson 1: do not"); the sign (the game's) in a bamboo frame on its post.
# The crates (a prop model) and the two signs' faces (the game's ad textures) stay the game's.
# local frame = the map's (placement at 0,0,0; the pieces are found from their boxes, so S&D's moved ones just work).
# run: node tools/arch/dump.mjs islands tiki tools/blender/arch/boxes/tiki.json --deco
#      node tools/arch/dump.mjs islands_sd tiki_sd tools/blender/arch/boxes/tiki_sd.json --deco
#      node tools/arch/dumpground.mjs islands -25 12 28 24 0.25 tools/blender/arch/boxes/tiki_ground.json
#      blender52 -b --python tools/blender/arch/make_tiki.py -- [tiki|tiki_sd]   (both by default)
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'tkbam': ('bamboo', '#ffffff', {}), 'tkbamold': ('bamboo', '#d8ccb4', {}), 'tkwall': ('bamwall', '#ffffff', {}),
    'tkthatch': ('thatch', '#ffffff', {}), 'tkthatchd': ('thatch', '#6a5a4a', {}), 'tkfringe': ('fringe', '#ffffff', {'alpha': True}),
    'tkgrain': ('grain', '#c08654', {}), 'tkgraind': ('grain', '#6e4a30', {}), 'tkfrond': ('frond', '#ffffff', {'alpha': True}),
    'tkweave': ('weave', '#e2c88e', {}), 'tkweaved': ('weave', '#8a6a42', {}), 'tkhammock': ('hammock', '#ffffff', {'alpha': True}),
    'tkplank': ('planks', '#e0b88c', {}), 'tkrope': ('stucco', '#e6c890', {}), 'tkbasalt': ('stone', '#6e6670', {}),
    'tkwhite': ('trim', '#fffaf0', {}), 'tkblack': ('tar', '#2a2226', {}), 'tkmouth': ('stucco', '#a8203a', {}), 'tkgold': ('metalplate', '#ffd040', {}),
    'tkpink': ('trim', '#ff4fd8', {}), 'tkyellow': ('trim', '#ffe14d', {}), 'tkcyan': ('trim', '#4fd8ff', {}), 'tkglass': ('trim', '#a8f0d8', {}),
    'tkcoco': ('stucco', '#7a5230', {}), 'tkgreen': ('stucco', '#4aa83a', {}), 'tksand': ('stucco', '#f0d494', {}),
    'tkflame': ('trim', '#ffb040', {'glow': True, 'glowcol': '#ff8a20'}), 'tkbulb': ('trim', '#ffe890', {'glow': True, 'glowcol': '#ffd860'}),
    'tkbulbp': ('trim', '#ff9ae8', {'glow': True, 'glowcol': '#ff60d0'}),
})
NOCAST.update({'tkfringe', 'tkrope', 'tkwhite', 'tkblack', 'tkmouth', 'tkgold', 'tkpink', 'tkyellow', 'tkcyan', 'tkglass', 'tkcoco', 'tkgreen',
               'tkflame', 'tkbulb', 'tkbulbp', 'tkhammock', 'tksand', 'tkfrond'})

# ------------------------------------------------------------ geometry: everything goes through XF (the piece's frame)
XF = [lambda p: Vector(p)]


def X(p): return XF[-1](p)


def Q(p, mat, uv=None, out=None, sub=None):
    """a quad (local points); out: a direction it must face (it's flipped if it doesn't)"""
    p = [X(q) for q in p]
    if out is not None:
        n = (p[1] - p[0]).cross(p[2] - p[0])
        if n.length < 1e-12: n = (p[2] - p[0]).cross(p[3] - p[0])
        if n.dot(XD(out)) < 0: p = p[::-1]; uv = uv[::-1] if uv else None
    K.quad(p, mat, uv=uv, sub=sub)


def T3(p, mat, out=None):
    p = [X(q) for q in p]
    if out is not None and (p[1] - p[0]).cross(p[2] - p[0]).dot(XD(out)) < 0: p = p[::-1]
    K.tri(p, mat)


def XD(d):
    """a direction through the frame (its rotation only)"""
    return X(Vector(d)) - X(Vector((0, 0, 0)))


def shift(ox, oy, oz, rot=0, cx=0.0, cz=0.0):
    """a frame: points move by (ox, oy, oz); rot = 2 turns them half round (cx, cz) first (a hut the other way round)"""
    def f(p):
        x, y, z = p
        if rot == 2: x, z = 2 * cx - x, 2 * cz - z
        return Vector((x + ox, y + oy, z + oz))
    return f


def basis(d):
    d = Vector(d).normalized()
    up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(up).normalized(); v = u.cross(d).normalized()
    return u, v


def pole(a, b, r, mat, n=8, caps=(True, True), r1=None, rot=0.0, vt=1.0):
    """a round pole from a to b: uvs once round it and down its length (the bamboo nodes come out as rings)"""
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


def lash(c, d, r, mat='tkrope', w=0.07):
    """rope wrapped round a pole of radius r at c (pole along d): a band cut a little into it, turned so it shows"""
    c, d = Vector(c), Vector(d).normalized()
    pole(c - d * w / 2, c + d * w / 2, r * 1.1 + 0.004, mat, n=6, rot=math.pi / 6, caps=(False, False))


def lathe(c, prof, mat, n=8, rot=0.0, axis=(0, 1, 0)):
    """a turned shape round an axis at c: prof [(radius, height)] bottom to top; a radius of 0 closes it"""
    c = Vector(c); ax = Vector(axis).normalized(); u, v = basis(ax)
    rings = [[c + ax * h + (u * math.cos(rot + k * math.tau / n) + v * math.sin(rot + k * math.tau / n)) * r for k in range(n)] for r, h in prof]
    s = 0.0
    for i in range(len(prof) - 1):
        (r0, h0), (r1, h1) = prof[i], prof[i + 1]; L = math.hypot(r1 - r0, h1 - h0); A, Bb = rings[i], rings[i + 1]
        for k in range(n):
            j = (k + 1) % n; mid = (A[k] + A[j] + Bb[k] + Bb[j]) / 4
            ctr = c + ax * ((mid - c).dot(ax)); out = mid - ctr
            if out.length < 1e-6: out = ax * (1 if h1 > h0 else -1)
            # (a cap facing down: out = -axis; a disc facing up: +axis)
            if abs(h1 - h0) < 1e-6: out = ax * (1 if r1 < r0 else -1)
            uv = [(k / n, s), ((k + 1) / n, s), ((k + 1) / n, s + L), (k / n, s + L)]
            if r0 < 1e-5: T3([A[k], Bb[j], Bb[k]], mat, out=out)
            elif r1 < 1e-5: T3([A[k], A[j], Bb[k]], mat, out=out)
            else: Q([A[k], A[j], Bb[j], Bb[k]], mat, uv=uv, out=out)
        s += L


def bx(mn, mx, mats, skip=()):
    """a box from local corners; mats: {'px','nx','py','ny','pz','nz' | 'side','top','bottom','all'}; skip: faces left out"""
    (x0, y0, z0), (x1, y1, z1) = mn, mx
    get = lambda f: mats.get(f, mats.get('top' if f == 'py' else 'bottom' if f == 'ny' else 'side', mats.get('all')))
    F = {'px': ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0)), 'nx': ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0)),
         'py': ([(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], (0, 1, 0)), 'ny': ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
         'pz': ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1)), 'nz': ([(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)], (0, 0, -1))}
    for f, (q, o) in F.items():
        m = get(f)
        if m and f not in skip: Q(q, m, out=o)


def prism(poly, y0, y1, mat, top=None, bottom=None, side_sub=None):
    """a polygon in x-z (convex, any winding) extruded from y0 to y1; top / bottom: their materials (None: open)"""
    n = len(poly); cx = sum(p[0] for p in poly) / n; cz = sum(p[1] for p in poly) / n
    for k in range(n):
        (ax, az), (bx_, bz) = poly[k], poly[(k + 1) % n]
        o = ((ax + bx_) / 2 - cx, 0, (az + bz) / 2 - cz)
        Q([(ax, y0, az), (bx_, y0, bz), (bx_, y1, bz), (ax, y1, az)], mat, out=o, sub=side_sub)
    for (m, y, o) in ((top, y1, (0, 1, 0)), (bottom, y0, (0, -1, 0))):
        if m:
            for k in range(1, n - 1): T3([(poly[0][0], y, poly[0][1]), (poly[k][0], y, poly[k][1]), (poly[k + 1][0], y, poly[k + 1][1])], m, out=o)


def plate(pts, z0, z1, mat, sides=None, back=False):
    """a flat shape on a +z face: pts [(x, y)] (convex) from z0 out to z1: front cap, sides; back cap only if asked"""
    n = len(pts); cx = sum(p[0] for p in pts) / n; cy = sum(p[1] for p in pts) / n
    for k in range(1, n - 1): T3([(pts[0][0], pts[0][1], z1), (pts[k][0], pts[k][1], z1), (pts[k + 1][0], pts[k + 1][1], z1)], mat, out=(0, 0, 1))
    if back:
        for k in range(1, n - 1): T3([(pts[0][0], pts[0][1], z0), (pts[k][0], pts[k][1], z0), (pts[k + 1][0], pts[k + 1][1], z0)], mat, out=(0, 0, -1))
    for k in range(n):
        (ax, ay), (bx_, by) = pts[k], pts[(k + 1) % n]
        Q([(ax, ay, z0), (bx_, by, z0), (bx_, by, z1), (ax, ay, z1)], sides or mat, out=((ax + bx_) / 2 - cx, (ay + by) / 2 - cy, 0))


def ellipse(cx, cy, rx, ry, n=10, rot=0.0):
    return [(cx + rx * math.cos(rot + k * math.tau / n), cy + ry * math.sin(rot + k * math.tau / n)) for k in range(n)]


def sheet(pts, mat, uv):
    """a single-sided sheet (alpha materials draw both sides)"""
    Q(pts, mat, uv=uv)


# ------------------------------------------------------------ the ground (Islands' dunes), for things that sit on the sand
G = None


def ground(x, z):
    """the sand's height at local (x, z) (through the frame): 0 off the grid (S&D's islets are flat)"""
    if not G: return 0.0
    p = X((x, 0, z)); i = (p.x - G['x0']) / G['step']; j = (p.z - G['z0']) / G['step']
    i0, j0 = int(math.floor(i)), int(math.floor(j))
    hs = []
    for (a, b) in ((i0, j0), (i0 + 1, j0), (i0, j0 + 1), (i0 + 1, j0 + 1)):
        if 0 <= a < G['nx'] and 0 <= b < G['nz']:
            h = G['h'][b * G['nx'] + a]
            if h is not None: hs.append(h)
    return max(hs) if hs else 0.0


# ------------------------------------------------------------ roofs: tiered palm thatch over stacked slabs
def skirt(inner, y_in, fp, y_fp, ov, y_eave, fl, mat='tkthatch', under='tkthatchd', y_under=None, fringe_skip=None, cap=False):
    """one tier of thatch: from the inner rectangle (x0, z0, x1, z1) at y_in down to the slab's own edge fp at y_fp
    (gentle: you can stand on it), then out past it by ov (per side n, s, w, e) down to y_eave (the flared eave), with a
    ragged fringe fl long hanging off the eave (per side), and the eave's underside back to the slab's bottom y_under.
    fringe_skip: {side: (a0, a1, short)}: from a0 to a1 (x on the n / s sides, z on e / w) the fringe is only `short` long
    (a sign hangs there). cap: the inner rectangle's own top (the top tier)"""
    ex = (fp[0] - ov['w'], fp[1] - ov['n'], fp[2] + ov['e'], fp[3] + ov['s'])
    ye = y_eave if isinstance(y_eave, dict) else {k: y_eave for k in 'nswe'}  # (a corner takes the lower of its two sides)
    def corners(r, y): return {'nw': Vector((r[0], y, r[1])), 'ne': Vector((r[2], y, r[1])), 'se': Vector((r[2], y, r[3])), 'sw': Vector((r[0], y, r[3]))}
    I, F, E = corners(inner, y_in), corners(fp, y_fp), corners(ex, 0)
    for c in E: E[c].y = min(ye[c[0]], ye[c[1]])
    sides = {'n': ('nw', 'ne', (0, 1, -0.3)), 'e': ('ne', 'se', (0.3, 1, 0)), 's': ('se', 'sw', (0, 1, 0.3)), 'w': ('sw', 'nw', (-0.3, 1, 0))}
    for s, (a, b, o) in sides.items():
        along = (F[b] - F[a]).normalized()
        def uvp(p, v0): return (p.dot(along), v0)
        # inner band (a triangle where the inner rectangle is a ridge line)
        dI, dF = 0.0, -max(0.05, ((F[a] + F[b]) / 2 - (I[a] + I[b]) / 2).length)
        dE = dF - ((E[a] + E[b]) / 2 - (F[a] + F[b]) / 2).length
        if (I[b] - I[a]).length < 1e-4:
            T3([I[a], F[a], F[b]], mat, out=o)
        else:
            Q([I[a], I[b], F[b], F[a]], mat, uv=[uvp(I[a], dI), uvp(I[b], dI), uvp(F[b], dF), uvp(F[a], dF)], out=o)
        Q([F[a], F[b], E[b], E[a]], mat, uv=[uvp(F[a], dF), uvp(F[b], dF), uvp(E[b], dE), uvp(E[a], dE)], out=o)
        # the eave's underside, back to the slab's bottom edge
        yu = y_under if y_under is not None else y_fp - 0.3
        Ua, Ub = Vector((F[a].x, yu, F[a].z)), Vector((F[b].x, yu, F[b].z))
        Q([Ua, Ub, E[b] - Vector((0, 0.04, 0)), E[a] - Vector((0, 0.04, 0))], under, uv=[uvp(Ua, 0), uvp(Ub, 0), uvp(E[b], 0.4), uvp(E[a], 0.4)], out=(-o[0], -1, -o[2]))
        # the eave's lip (4 cm of thatch end-on)
        Q([E[a] - Vector((0, 0.04, 0)), E[b] - Vector((0, 0.04, 0)), E[b], E[a]], under, uv=[uvp(E[a], 0), uvp(E[b], 0), uvp(E[b], 0.04), uvp(E[a], 0.04)], out=(o[0], 0, o[2]))
        # the fringe: hanging off the eave's lip, flaring out a touch; shorter where something hangs under it
        L = fl[s]
        if L <= 0: continue
        outv = Vector((o[0], 0, o[2])).normalized()
        A0, B0 = E[a] - Vector((0, 0.02, 0)), E[b] - Vector((0, 0.02, 0))  # (on the lip: it hangs off it)
        span = [(0.0, 1.0, L)]
        if fringe_skip and s in fringe_skip:
            a0, a1, short = fringe_skip[s]; ax = 0 if s in 'ns' else 2
            t0, t1 = sorted(((a0 - A0[ax]) / (B0[ax] - A0[ax]), (a1 - A0[ax]) / (B0[ax] - A0[ax])))
            span = [(0.0, t0, L), (t0, t1, short), (t1, 1.0, L)]
        for (t0, t1, l) in span:
            if t1 - t0 < 1e-3 or l <= 0.005: continue
            P0, P1 = A0.lerp(B0, t0), A0.lerp(B0, t1)
            dn = Vector((0, -l, 0)) + outv * l * 0.18
            sheet([P0, P1, P1 + dn, P0 + dn], 'tkfringe', uv=[(P0.dot(along), 1), (P1.dot(along), 1), (P1.dot(along), 1 - l / 0.32), (P0.dot(along), 1 - l / 0.32)])
    if cap and (I['ne'] - I['nw']).length > 1e-4 and (I['se'] - I['ne']).length > 1e-4:
        Q([I['nw'], I['ne'], I['se'], I['sw']], mat, uv=[(I['nw'].x, 0), (I['ne'].x, 0), (I['se'].x, I['se'].z - I['ne'].z), (I['sw'].x, I['se'].z - I['ne'].z)], out=(0, 1, 0))


def tier_rect(b): return (b['min'][0], b['min'][2], b['max'][0], b['max'][2])


# ------------------------------------------------------------ the tiki bar
def tiki_bar(bb, deco):
    """bb: its B boxes; deco: its render-only ones (counter top, bottles)"""
    th = sorted([b for b in bb if b['mat'] == 'thatch'], key=lambda b: b['min'][1])
    posts = [b for b in bb if b['mat'] == 'bamboo' and b['max'][1] - b['min'][1] > 2.5]
    stools = [b for b in bb if b['mat'] == 'bamboo' and abs(b['max'][1] - b['min'][1] - 0.7) < 1e-3]
    counter = next(b for b in bb if b['mat'] == 'bamboo' and abs(b['max'][1] - b['min'][1] - 1.1) < 1e-3)
    back = next(b for b in bb if b['mat'] == 'wood')
    top = next(b for b in deco if b['mat'] == 'wood')
    bottles = [b for b in deco if b is not top and b['min'][1] > 1.6]
    # ---- the roof: three tiers. the front (+z) eave is short and high: the sign hangs under it
    T = [tier_rect(b) for b in th]; Y = [(b['min'][1], b['max'][1]) for b in th]
    cx = (T[2][0] + T[2][2]) / 2
    ridge = (T[2][0] + 0.9, (T[2][1] + T[2][3]) / 2 - 0.08, T[2][2] - 0.9, (T[2][1] + T[2][3]) / 2 + 0.08)
    sign = (cx - 3.0, cx + 3.0)  # (the sign: shared/map.js tikiBar, x -16..-10)
    up1, up2 = Y[0][1] + 0.12, Y[1][1] + 0.12
    skirt(T[1], up1, T[0], Y[0][1] - 0.08, {'n': 0.55, 's': 0.24, 'w': 0.55, 'e': 0.55}, {'n': Y[0][0] - 0.14, 's': Y[0][0] - 0.03, 'w': Y[0][0] - 0.14, 'e': Y[0][0] - 0.14},
          {'n': 0.32, 's': 0.3, 'w': 0.32, 'e': 0.32}, y_under=Y[0][0], fringe_skip={'s': (sign[0] - 0.15, sign[1] + 0.15, 0.05)})
    # (the upper tiers' eaves stand ~10 cm clear of the tier below, like the huts': at a cm or two the dark lip and
    # underside cut through the lower thatch and Potato's vertex snap broke them into black dashes)
    skirt(T[2], up2, T[1], Y[1][1] - 0.08, {k: 0.44 for k in 'nswe'}, up1 + 0.04, {k: 0.2 for k in 'nswe'}, y_under=Y[1][0])
    skirt(ridge, Y[2][1] + 0.26, T[2], Y[2][1] - 0.06, {k: 0.38 for k in 'nswe'}, up2 + 0.05, {k: 0.16 for k in 'nswe'}, y_under=Y[2][0], cap=True)
    yr = Y[2][1] + 0.26; fz = (ridge[1] + ridge[3]) / 2
    pole((ridge[0] - 0.45, yr + 0.03, fz), (ridge[2] + 0.45, yr + 0.03, fz), 0.14, 'tkthatch', n=8, vt=1.0)
    for x in (ridge[0] - 0.3, ridge[2] + 0.3, cx - 0.9, cx + 0.9): lash((x, yr + 0.03, fz), (1, 0, 0), 0.14, w=0.09)
    # the finial: a little tiki on a bamboo spike, top of the roof, grinning at the beach
    pole((cx, yr + 0.1, fz), (cx, yr + 0.55, fz), 0.04, 'tkbam', n=6)
    prism([(cx - 0.16, fz - 0.12), (cx + 0.16, fz - 0.12), (cx + 0.16, fz + 0.12), (cx - 0.16, fz + 0.12)], yr + 0.55, yr + 1.02, 'tkgrain', top='tkgraind', bottom='tkgraind')
    for s in (-1, 1):
        bx((cx + s * 0.07 - 0.04, yr + 0.82, fz + 0.115), (cx + s * 0.07 + 0.04, yr + 0.9, fz + 0.14), {'all': 'tkwhite'}, skip=('nz',))
        bx((cx + s * 0.07 - 0.015, yr + 0.83, fz + 0.135), (cx + s * 0.07 + 0.015, yr + 0.86, fz + 0.15), {'all': 'tkblack'}, skip=('nz',))
    bx((cx - 0.17, yr + 0.92, fz - 0.13), (cx + 0.17, yr + 0.97, fz + 0.16), {'all': 'tkgraind'})
    bx((cx - 0.1, yr + 0.64, fz + 0.115), (cx + 0.1, yr + 0.72, fz + 0.14), {'all': 'tkmouth'}, skip=('nz',))
    for k in range(3): bx((cx - 0.075 + k * 0.055, yr + 0.685, fz + 0.135), (cx - 0.035 + k * 0.055, yr + 0.715, fz + 0.15), {'all': 'tkwhite'}, skip=('nz',))
    # the ceiling: dark thatch, rafters along z, beams along x on the posts
    y0 = Y[0][0]
    Q([(T[0][0], y0, T[0][1]), (T[0][2], y0, T[0][1]), (T[0][2], y0, T[0][3]), (T[0][0], y0, T[0][3])], 'tkthatchd', out=(0, -1, 0), sub=2.0)
    xs = sorted({(p['min'][0] + p['max'][0]) / 2 for p in posts}); zs = sorted({(p['min'][2] + p['max'][2]) / 2 for p in posts})
    for x in [xs[0] + (xs[1] - xs[0]) * k / 4 for k in range(5)]:
        pole((x, y0 - 0.05, T[0][1] + 0.05), (x, y0 - 0.05, T[0][3] - 0.05), 0.055, 'tkbamold', n=6)
    for z in zs:
        pole((xs[0] - 0.4, y0 - 0.14, z), (xs[1] + 0.4, y0 - 0.14, z), 0.1, 'tkbam', n=8)
        for x in xs: lash((x, y0 - 0.14, z), (1, 0, 0), 0.1, w=0.1)
    # the posts: fat bamboo into the sand, lashed under the beam, knee braces up to it
    for p in posts:
        x, z = (p['min'][0] + p['max'][0]) / 2, (p['min'][2] + p['max'][2]) / 2; yb = p['min'][1]
        pole((x, yb - 0.2, z), (x, p['max'][1] + 0.02, z), 0.17, 'tkbam', n=8, caps=(False, True))
        lash((x, y0 - 0.32, z), (0, 1, 0), 0.17, w=0.1); lash((x, yb + 0.25, z), (0, 1, 0), 0.17, w=0.06)
        sx = 1 if x < cx else -1
        pole((x + sx * 0.1, y0 - 0.85, z), (x + sx * 0.75, y0 - 0.16, z), 0.045, 'tkbamold', n=6)
    # the counter: half-culms down its customer face and its ends, two lashed rails across, planks on the inside
    (x0, yb, z0), (x1, yt, z1) = counter['min'], counter['max']
    def culms(a0, a1, face, axis, y0_, y1_, r=0.06):
        n = int(round((a1 - a0) / (2 * r))); w = (a1 - a0) / n
        for k in range(n):
            a = a0 + (k + 0.5) * w; rr = w / 2 * 0.98
            if axis == 'x': c0, c1, d = (a, y0_, face[0]), (a, y1_, face[0]), face[1]
            else: c0, c1, d = (face[0], y0_, a), (face[0], y1_, a), face[1]
            # half a culm: the four segments facing out from the face (the rest would be inside it)
            for i in range(3):
                t0, t1 = math.pi * i / 3, math.pi * (i + 1) / 3
                def P(c, t):
                    if axis == 'x': return (c[0] + rr * math.cos(t), c[1], c[2] + d * rr * math.sin(t))
                    return (c[0] + d * rr * math.sin(t), c[1], c[2] + rr * math.cos(t))
                mid = (t0 + t1) / 2
                o = (math.cos(mid), 0, d * math.sin(mid)) if axis == 'x' else (d * math.sin(mid), 0, math.cos(mid))
                L = y1_ - y0_; off = (k * 0.37) % 1.0
                Q([P(c0, t0), P(c0, t1), P(c1, t1), P(c1, t0)], 'tkbam' if k % 5 else 'tkbamold', uv=[(i / 6, off), ((i + 1) / 6, off), ((i + 1) / 6, off + L), (i / 6, off + L)], out=o)
    culms(x0, x1, (z1, 1), 'x', yb - 0.02, yt)
    culms(z0, z1, (x0, -1), 'z', yb - 0.02, yt); culms(z0, z1, (x1, 1), 'z', yb - 0.02, yt)
    Q([(x0, yb, z0), (x0, yt, z0), (x1, yt, z0), (x1, yb, z0)], 'tkplank', out=(0, 0, -1))
    for y in (yb + 0.22, yt - 0.25):
        pole((x0 - 0.06, y, z1 + 0.085), (x1 + 0.06, y, z1 + 0.085), 0.04, 'tkbamold', n=6)
        for k in range(4): lash((x0 + 0.5 + k * (x1 - x0 - 1.0) / 3, y, z1 + 0.085), (1, 0, 0), 0.04, w=0.05)
    (tx0, ty0, tz0), (tx1, ty1, tz1) = top['min'], top['max']
    bx((tx0, ty0, tz0), (tx1, ty1, tz1), {'top': 'tkplank', 'side': 'tkgraind', 'bottom': 'tkgraind'})
    # coconut cups on it, each with a straw and a tiny umbrella
    for k, (fx, col) in enumerate(((0.12, 'tkpink'), (0.37, 'tkcyan'), (0.63, 'tkyellow'), (0.86, 'tkpink'))):
        x = tx0 + (tx1 - tx0) * fx; z = tz1 - 0.3 - 0.12 * (k % 2); y = ty1
        lathe((x, y - 0.002, z), [(0.05, 0.0), (0.08, 0.05), (0.075, 0.1)], 'tkcoco', n=6)
        lathe((x, y - 0.002, z), [(0.075, 0.1), (0.0, 0.092)], 'tkwhite', n=6)
        pole((x + 0.02, y + 0.08, z), (x + 0.07, y + 0.26, z - 0.02), 0.008, col, n=4)
        pole((x - 0.03, y + 0.08, z + 0.01), (x - 0.06, y + 0.3, z + 0.03), 0.004, 'tkwhite', n=4, caps=(False, False))
        lathe((x - 0.06, y + 0.27, z + 0.03), [(0.11, 0.0), (0.0, 0.05)], ('tkcyan', 'tkyellow', 'tkpink', 'tkcyan')[k], n=6)
    # the back bar: plank doors in a bamboo frame facing the counter, bamboo round the back, a plank top, the bottles
    (bx0, by0, bz0), (bx1, by1, bz1) = back['min'], back['max']
    bx((bx0, by0, bz0), (bx1, by1, bz1), {'pz': 'tkplank', 'nz': 'tkwall', 'px': 'tkwall', 'nx': 'tkwall'}, skip=('py', 'ny'))
    bx((bx0 - 0.04, by1, bz0 - 0.04), (bx1 + 0.04, by1 + 0.05, bz1 + 0.04), {'all': 'tkplank', 'side': 'tkgraind', 'bottom': 'tkgraind'})
    for y in (by0 + 0.08, by1 - 0.06): pole((bx0 + 0.01, y, bz1 + 0.02), (bx1 - 0.01, y, bz1 + 0.02), 0.04, 'tkbam', n=6)
    for k in range(5):
        x = bx0 + 0.04 + k * (bx1 - bx0 - 0.08) / 4
        pole((x, by0 - 0.02, bz1 + 0.02), (x, by1 - 0.02, bz1 + 0.02), 0.04, 'tkbam', n=6)
        if k < 4:
            for s in (-1, 1): bx((x + (bx1 - bx0) / 8 + s * 0.12 - 0.025, by0 + 0.85, bz1), (x + (bx1 - bx0) / 8 + s * 0.12 + 0.025, by0 + 0.95, bz1 + 0.04), {'all': 'tkgold'}, skip=('nz',))
    lc = Vector(((bx0 + bx1) / 2 + 1.6, by0 + 1.0, bz0 - 0.075)); NR = 12
    # (one mitred ring of hex sections, a point to the front: no straight-cut segments overlapping at the joins)
    sec = lambda a: [lc + Vector((math.cos(a), math.sin(a), 0)) * (0.27 + 0.07 * math.sin(t)) + Vector((0, 0, 0.07 * math.cos(t))) for t in (j * math.tau / 6 for j in range(6))]
    for k in range(NR):
        A, Bq = sec(k * math.tau / NR), sec((k + 1) * math.tau / NR)
        for j in range(6):
            i = (j + 1) % 6; mid = (A[j] + A[i] + Bq[j] + Bq[i]) / 4; ax = lc + Vector((mid.x - lc.x, mid.y - lc.y, 0)).normalized() * 0.27
            Q([A[j], A[i], Bq[i], Bq[j]], 'tkpink' if (k // 3) % 2 else 'tkwhite', out=mid - ax)
    pole(lc + Vector((-0.3, 0.32, 0.03)), lc + Vector((0.3, 0.32, 0.03)), 0.012, 'tkrope', n=4)
    col = {'glass': 'tkglass', 'toyteal': 'tkcyan', 'toypink': 'tkpink', 'toyyellow': 'tkyellow'}
    for k, b in enumerate(sorted(bottles, key=lambda b: b['min'][0])):
        x, z = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2; y = by1 + 0.048
        h = 0.3 + 0.1 * ((k * 7) % 3) / 2; r = 0.07 if k % 3 else 0.085
        if k % 4 == 1:  # a squat round one
            lathe((x, y, z), [(r * 1.1, 0.0), (r * 1.25, h * 0.3), (r * 0.9, h * 0.6), (0.025, h * 0.72), (0.025, h * 0.9), (0.0, h * 0.9)], col.get(b['mat'], 'tkglass'), n=6)
        else:
            lathe((x, y, z), [(r, 0.0), (r, h * 0.62), (0.022, h * 0.8), (0.022, h), (0.0, h)], col.get(b['mat'], 'tkglass'), n=6)
    # drum stools: bamboo slats round a drum, a woven seat on top
    for b in stools:
        x, z = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2; ys, yt_ = b['min'][1], b['max'][1]
        lathe((x, ys - 0.05, z), [(0.27, 0.0), (0.27, yt_ - ys - 0.01)], 'tkwall', n=8, rot=0.3)
        lathe((x, ys - 0.05, z), [(0.25, yt_ - ys - 0.05), (0.29, yt_ - ys - 0.02), (0.29, yt_ - ys + 0.07), (0.0, yt_ - ys + 0.07)], 'tkweave', n=8, rot=0.3)
        lash((x, ys + 0.18, z), (0, 1, 0), 0.27, w=0.05)
    # the sign (the game's): a lashed bamboo frame round it, hung off the ceiling
    sx0, sx1, sy0, sy1, sz = cx - 3.0, cx + 3.0, y0 - 0.7, y0 - 0.05, T[0][3] + 0.06
    pole((sx0 - 0.1, sy1 + 0.035, sz), (sx1 + 0.1, sy1 + 0.035, sz), 0.035, 'tkbam', n=6)
    pole((sx0 - 0.1, sy0 - 0.035, sz), (sx1 + 0.1, sy0 - 0.035, sz), 0.035, 'tkbam', n=6)
    for x in (sx0 - 0.04, sx1 + 0.04): pole((x, sy0 - 0.12, sz), (x, y0 + 0.01, sz), 0.035, 'tkbam', n=6)
    # tiki torches lashed to the front posts, and bulbs strung under the front eave
    front = [p for p in posts if (p['min'][2] + p['max'][2]) / 2 > (T[0][1] + T[0][3]) / 2]
    for p in front:
        x, z = (p['min'][0] + p['max'][0]) / 2, (p['min'][2] + p['max'][2]) / 2; s = -1 if x < cx else 1
        a, b = Vector((x + s * 0.2, 1.1 + p['min'][1], z + 0.06)), Vector((x + s * 0.3, 2.35 + p['min'][1], z + 0.1))
        pole(a, b, 0.035, 'tkbamold', n=6)
        for y in (1.5, 2.0): lash(a.lerp(b, (y - 1.1) / 1.25), b - a, 0.035, w=0.04)
        lathe(b, [(0.035, 0.0), (0.075, 0.05), (0.075, 0.16), (0.06, 0.16)], 'tkweaved', n=6)
        lathe(b + Vector((0, 0.15, 0)), [(0.0, 0.0), (0.055, 0.01), (0.075, 0.09), (0.04, 0.2), (0.0, 0.3)], 'tkflame', n=6)
    back_ = [p for p in posts if p not in front]
    pa = min(front, key=lambda p: p['min'][0]); pb = max(back_, key=lambda p: p['min'][0])
    A = Vector(((pa['min'][0] + pa['max'][0]) / 2 + 0.17, y0 - 0.3, (pa['min'][2] + pa['max'][2]) / 2))
    Bv = Vector(((pb['min'][0] + pb['max'][0]) / 2 - 0.17, y0 - 0.3, (pb['min'][2] + pb['max'][2]) / 2))
    n = 14; prev = A
    for i in range(1, n + 1):
        t = i / n; q = A.lerp(Bv, t) - Vector((0, 0.45 * 4 * t * (1 - t), 0))
        pole(prev, q, 0.008, 'tkblack', n=4, caps=(False, False))
        if i < n: lathe(q - Vector((0, 0.15, 0)), [(0.0, 0.0), (0.045, 0.06), (0.02, 0.14), (0.0, 0.155)], 'tkbulb' if i % 2 else 'tkbulbp', n=4)
        prev = q


# ------------------------------------------------------------ the big tiki
def big_tiki(bb, deco):
    base = next(b for b in bb if b['mat'] == 'basalt'); log = next(b for b in bb if b['mat'] == 'wood')
    (px0, py0, pz0), (px1, py1, pz1) = base['min'], base['max']
    (lx0, ly0, lz0), (lx1, ly1, lz1) = log['min'], log['max']
    cx, cz = (lx0 + lx1) / 2, (lz0 + lz1) / 2; m = 0.03; ch = 0.16
    # the plinth: rough basalt, a chamfered top edge, sunk into the sand
    P2 = [(px0 - 0.02, pz0 + 0.06), (px0 + 0.06, pz0 - 0.02), (px1 - 0.06, pz0 - 0.02), (px1 + 0.02, pz0 + 0.06), (px1 + 0.02, pz1 - 0.06), (px1 - 0.06, pz1 + 0.02), (px0 + 0.06, pz1 + 0.02), (px0 - 0.02, pz1 - 0.06)]
    prism(P2, py0 - 0.15, py1 + 0.002, 'tkbasalt', top='tkbasalt', side_sub=0.8)
    # the log: chamfered, a hair outside its box; carved bands round the foot and under the hat
    oct_ = lambda e: [(lx0 - e + ch, lz0 - e), (lx1 + e - ch, lz0 - e), (lx1 + e, lz0 - e + ch), (lx1 + e, lz1 + e - ch), (lx1 + e - ch, lz1 + e), (lx0 - e + ch, lz1 + e), (lx0 - e, lz1 + e - ch), (lx0 - e, lz0 - e + ch)]
    prism(oct_(m), ly0, ly1, 'tkgrain', top='tkgrain', side_sub=0.7)
    for (y0, y1) in ((ly0 + 0.01, ly0 + 0.15), (ly1 - 0.28, ly1 - 0.16)):
        prism(oct_(m + 0.04), y0, y1, 'tkgraind', top='tkgraind', bottom='tkgraind')
    zf = lz1 + m  # the face
    def rel(a): return cx + a
    # the brow: a heavy ridge, wider than the head
    br = next(b for b in deco if b['mat'] == 'wood')
    (bx0, by0, bz0), (bx1, by1, bz1) = br['min'], br['max']
    NB = 14; hw_ = (bx1 - bx0) / 2 + 0.02
    def bot(a): return by0 + 0.03 + 0.13 * max(0.0, 1 - ((abs(a) - 0.4) / 0.55) ** 2)
    def front(a): return bz1 + 0.02 - 0.05 * (abs(a) / hw_) ** 2
    av_ = [-hw_ + 2 * hw_ * k / NB for k in range(NB + 1)]
    for k in range(NB):
        a0, a1 = av_[k], av_[k + 1]
        Q([(rel(a0), bot(a0), front(a0) - 0.08), (rel(a1), bot(a1), front(a1) - 0.08), (rel(a1), by1, front(a1)), (rel(a0), by1, front(a0))], 'tkgraind', out=(0, 0.2, 1))
        Q([(rel(a0), bot(a0), zf - 0.01), (rel(a1), bot(a1), zf - 0.01), (rel(a1), bot(a1), front(a1) - 0.08), (rel(a0), bot(a0), front(a0) - 0.08)], 'tkgraind', out=(0, -1, 0))
        Q([(rel(a0), by1, zf - 0.01), (rel(a1), by1, zf - 0.01), (rel(a1), by1, front(a1)), (rel(a0), by1, front(a0))], 'tkgraind', out=(0, 1, 0))
    for a, o in ((-hw_, -1), (hw_, 1)):
        Q([(rel(a), bot(a), zf - 0.01), (rel(a), bot(a), front(a) - 0.08), (rel(a), by1, front(a)), (rel(a), by1, zf - 0.01)], 'tkgraind', out=(o, 0, 0))
    # the eyes: a raised socket rim, a shell eyeball, a black pupil where the game puts it (looking at the bar)
    whites = sorted([b for b in deco if b['mat'] == 'white'], key=lambda b: b['min'][0])
    pupils = sorted([b for b in deco if b['mat'] == 'tire'], key=lambda b: b['min'][0])
    for w, p in zip(whites, pupils):
        ex, ey = (w['min'][0] + w['max'][0]) / 2, (w['min'][1] + w['max'][1]) / 2
        rim_o, rim_i = ellipse(ex, ey, 0.29, 0.33, 12), ellipse(ex, ey, 0.21, 0.26, 12)
        for k in range(12):  # the rim: a ring, front face and inner wall
            a0, a1, b0, b1 = rim_o[k], rim_o[(k + 1) % 12], rim_i[k], rim_i[(k + 1) % 12]
            Q([(a0[0], a0[1], zf + 0.09), (a1[0], a1[1], zf + 0.09), (b1[0], b1[1], zf + 0.09), (b0[0], b0[1], zf + 0.09)], 'tkgraind', out=(0, 0, 1))
            Q([(a0[0], a0[1], zf - 0.005), (a1[0], a1[1], zf - 0.005), (a1[0], a1[1], zf + 0.09), (a0[0], a0[1], zf + 0.09)], 'tkgraind', out=(a0[0] - ex, a0[1] - ey, 0))
            Q([(b0[0], b0[1], zf + 0.03), (b1[0], b1[1], zf + 0.03), (b1[0], b1[1], zf + 0.09), (b0[0], b0[1], zf + 0.09)], 'tkgraind', out=(ex - b0[0], ey - b0[1], 0))
        ball = ellipse(ex, ey, 0.215, 0.265, 12)
        for k in range(12):  # the eyeball: a shallow dome
            a0, a1 = ball[k], ball[(k + 1) % 12]
            T3([(ex, ey, zf + 0.085), (a0[0], a0[1], zf + 0.035), (a1[0], a1[1], zf + 0.035)], 'tkwhite', out=(0, 0, 1))
        qx, qy = ex + 0.09, ey - 0.04  # (looking over at the bar, a bit shifty)
        plate(ellipse(qx, qy, 0.085, 0.095, 8), zf + 0.05, zf + 0.1, 'tkblack')
        plate(ellipse(qx + 0.03, qy + 0.035, 0.022, 0.022, 6), zf + 0.09, zf + 0.104, 'tkwhite')  # (a glint)
    # the nose: broad, flared nostrils, sloping out from between the eyes
    ny0, ny1 = 1.72 + ly0 - 0.623, 2.78 + ly0 - 0.623
    nb, nt = [(-0.27, ny0), (0.27, ny0)], [(0.1, ny1), (-0.1, ny1)]
    pts = [(rel(-0.27), ny0, zf + 0.2), (rel(0.27), ny0, zf + 0.2), (rel(0.1), ny1, zf + 0.06), (rel(-0.1), ny1, zf + 0.06)]
    Q(pts, 'tkgrain', out=(0, 0.3, 1))
    back_ = [(rel(-0.27), ny0, zf - 0.01), (rel(0.27), ny0, zf - 0.01), (rel(0.1), ny1, zf - 0.01), (rel(-0.1), ny1, zf - 0.01)]
    Q([back_[0], back_[1], pts[1], pts[0]], 'tkgraind', out=(0, -1, 0))
    Q([back_[1], back_[2], pts[2], pts[1]], 'tkgrain', out=(1, 0, 0)); Q([back_[3], back_[0], pts[0], pts[3]], 'tkgrain', out=(-1, 0, 0))
    Q([back_[2], back_[3], pts[3], pts[2]], 'tkgrain', out=(0, 1, 0.3))
    for s in (-1, 1):  # nostril flares
        lathe((rel(s * 0.23), ny0 + 0.08, zf + 0.1), [(0.0, -0.09), (0.09, -0.07), (0.11, 0.0), (0.08, 0.07), (0.0, 0.09)], 'tkgrain', n=8, axis=(0, 0, 1))
    # the grin: lips round a dark mouth, teeth hanging off the top lip (one gold), a few at the bottom, a tongue
    mo = next(b for b in deco if b['mat'] == 'toyred')
    my1 = mo['max'][1] - 0.05; A_ = 0.66; N = 12
    up = lambda a: my1 - 0.07 * (1 - (a / A_) ** 2)
    lo = lambda a: my1 - 0.33 * max(0.0, 1 - (a / A_) ** 2) ** 0.6
    av = [-A_ + 2 * A_ * k / N for k in range(N + 1)]
    for k in range(N):
        a0, a1 = av[k], av[k + 1]
        if k == 0: T3([(rel(a0), up(a0), zf + 0.03), (rel(a1), lo(a1), zf + 0.03), (rel(a1), up(a1), zf + 0.03)], 'tkmouth', out=(0, 0, 1))
        elif k == N - 1: T3([(rel(a0), up(a0), zf + 0.03), (rel(a0), lo(a0), zf + 0.03), (rel(a1), up(a1), zf + 0.03)], 'tkmouth', out=(0, 0, 1))
        else: Q([(rel(a0), lo(a0), zf + 0.03), (rel(a1), lo(a1), zf + 0.03), (rel(a1), up(a1), zf + 0.03), (rel(a0), up(a0), zf + 0.03)], 'tkmouth', out=(0, 0, 1))
        for (f, s) in ((up, 1), (lo, -1)):  # the lips: a band outside the mouth line, standing 10 cm proud
            c0, c1 = f(a0), f(a1); w0 = 0.08 + 0.04 * (1 - (a0 / A_) ** 2); w1 = 0.08 + 0.04 * (1 - (a1 / A_) ** 2)
            o0, o1 = c0 + s * w0, c1 + s * w1
            ea0, ea1 = a0 * (1 + 0.12 * (k == 0)), a1 * (1 + 0.12 * (k == N - 1))
            Q([(rel(ea0), c0, zf + 0.1), (rel(ea1), c1, zf + 0.1), (rel(ea1), o1, zf + 0.1), (rel(ea0), o0, zf + 0.1)], 'tkgrain', out=(0, 0, 1))
            Q([(rel(ea0), o0, zf - 0.005), (rel(ea1), o1, zf - 0.005), (rel(ea1), o1, zf + 0.1), (rel(ea0), o0, zf + 0.1)], 'tkgraind', out=(0, s, 0))
            Q([(rel(ea0), c0, zf + 0.03), (rel(ea1), c1, zf + 0.03), (rel(ea1), c1, zf + 0.1), (rel(ea0), c0, zf + 0.1)], 'tkgraind', out=(0, -s, 0))
    for k in range(6):
        a = -0.45 + k * 0.18
        t0, t1 = up(a - 0.07), up(a + 0.07)
        bx((rel(a - 0.07), min(t0, t1) - 0.11, zf + 0.025), (rel(a + 0.07), min(t0, t1) + 0.005, zf + 0.075), {'all': 'tkgold' if k == 4 else 'tkwhite'}, skip=('nz',))
    for a in (-0.24, 0.24):
        bx((rel(a - 0.06), lo(a) - 0.005, zf + 0.025), (rel(a + 0.06), lo(a) + 0.08, zf + 0.07), {'all': 'tkwhite'}, skip=('nz',))
    plate(ellipse(rel(0.05), lo(0.05) + 0.07, 0.16, 0.06, 8), zf + 0.025, zf + 0.06, 'tkpink')
    # the ears: long lobes on the sides, a carved swirl in each
    for s, x in ((-1, lx0 - m), (1, lx1 + m)):
        ey0 = 1.95 + ly0 - 0.623; ec = cz + 0.25
        ear = [(ec - 0.22, ey0 + 0.9), (ec + 0.18, ey0 + 0.95), (ec + 0.28, ey0 + 0.6), (ec + 0.2, ey0 + 0.05), (ec - 0.05, ey0 - 0.12), (ec - 0.25, ey0 + 0.1)]
        inner = [(ec - 0.1, ey0 + 0.72), (ec + 0.1, ey0 + 0.75), (ec + 0.15, ey0 + 0.5), (ec + 0.08, ey0 + 0.15), (ec - 0.08, ey0 + 0.1)]
        for poly, d0, d1, mat in ((ear, -0.005, 0.08, 'tkgrain'), (inner, 0.07, 0.11, 'tkgraind')):
            n_ = len(poly); cy_ = sum(p[1] for p in poly) / n_; czz = sum(p[0] for p in poly) / n_
            for k in range(1, n_ - 1): T3([(x + s * d1, poly[0][1], poly[0][0]), (x + s * d1, poly[k][1], poly[k][0]), (x + s * d1, poly[k + 1][1], poly[k + 1][0])], mat, out=(s, 0, 0))
            for k in range(n_):
                (za, ya), (zb, yb) = poly[k], poly[(k + 1) % n_]
                Q([(x + s * d0, ya, za), (x + s * d0, yb, zb), (x + s * d1, yb, zb), (x + s * d1, ya, za)], mat, out=(0, (ya + yb) / 2 - cy_, (za + zb) / 2 - czz))
    # hands on his belly, fingers pointing in; arms carved down his sides to them
    hy = ly0 + 0.3
    for s in (-1, 1):
        xs_ = lx0 - m if s < 0 else lx1 + m
        path = [((xs_, ly0 + 1.45, lz0 + 0.45), (s, 0, 0)), ((xs_, ly0 + 0.75, lz1 + m - ch - 0.12), (s, 0, 0)),
                ((xs_ - s * ch / 2, hy + 0.02, lz1 + m - ch / 2), (s, 0, 1)), ((rel(s * 0.78), hy, zf), (0, 0, 1))]
        secs = []
        for i, (pp, nn) in enumerate(path):
            pp = Vector(pp); nn = Vector(nn).normalized()
            t = (Vector(path[min(i + 1, len(path) - 1)][0]) - Vector(path[max(i - 1, 0)][0])).normalized()
            wv = nn.cross(t).normalized() * 0.1
            secs.append((pp - wv, pp + wv, nn))
        L0 = 0.0  # (explicit uvs: along the arm and across it. world-planar ones fold flat where it turns the corner)
        for i in range(len(secs) - 1):
            (a0, b0, n0), (a1, b1, n1) = secs[i], secs[i + 1]; L1 = L0 + ((a1 + b1) / 2 - (a0 + b0) / 2).length
            Q([a0 + n0 * 0.06, b0 + n0 * 0.06, b1 + n1 * 0.06, a1 + n1 * 0.06], 'tkgrain', out=n0 + n1, uv=[(0, L0), (0.2, L0), (0.2, L1), (0, L1)])
            Q([a0 - n0 * 0.01, a1 - n1 * 0.01, a1 + n1 * 0.06, a0 + n0 * 0.06], 'tkgraind', out=a0 - b0, uv=[(L0, 0), (L1, 0), (L1, 0.07), (L0, 0.07)])
            Q([b0 - n0 * 0.01, b1 - n1 * 0.01, b1 + n1 * 0.06, b0 + n0 * 0.06], 'tkgraind', out=b0 - a0, uv=[(L0, 0), (L1, 0), (L1, 0.07), (L0, 0.07)])
            L0 = L1
        a0, b0, n0 = secs[0]
        Q([a0 - n0 * 0.01, b0 - n0 * 0.01, b0 + n0 * 0.06, a0 + n0 * 0.06], 'tkgraind', out=(0, 1, 0), uv=[(0, 0), (0.2, 0), (0.2, 0.07), (0, 0.07)])
    for s in (-1, 1):
        bx((rel(s * 0.78), hy - 0.13, zf - 0.01), (rel(s * 0.36), hy + 0.13, zf + 0.07), {'all': 'tkgrain'}, skip=('nz',))
        for f in range(4):
            y = hy - 0.11 + f * 0.075
            a0, a1 = sorted((rel(s * 0.38), rel(s * 0.12 + s * 0.03 * (f in (1, 2)))))
            bx((a0, y, zf - 0.01), (a1, y + 0.06, zf + 0.06), {'all': 'tkgrain'}, skip=('nz',))
    # the hat: a woven band, palm fronds fanned out over it, a hibiscus, a cocktail umbrella stuck in the top
    hat = next(b for b in deco if b['mat'] == 'leaves2')
    yh = ly1
    prism(oct_(m + 0.07), yh - 0.12, yh + 0.12, 'tkweave', top='tkweaved', bottom='tkweaved')
    hc = Vector((cx, yh + 0.1, cz)); up_ = Vector((0, 1, 0))
    for k in range(9):
        ang = math.tau * k / 9 + 0.35
        d = Vector((math.cos(ang), 0, math.sin(ang))); side = Vector((-d.z, 0, d.x))
        reach = 1.45 if abs(math.sin(ang)) < 0.75 else 1.15  # (longer out to the sides: the hat is wider than deep)
        P_ = [hc + d * 0.05, hc + d * 0.3 + up_ * 0.42, hc + d * (reach * 0.6) + up_ * 0.6, hc + d * reach + up_ * (0.28 - 0.12 * (k % 2))]
        Wd = [0.12, 0.26, 0.3, 0.12]; V = [1.0, 0.72, 0.38, 0.0]
        for i in range(3):
            sheet([P_[i] - side * Wd[i], P_[i] + side * Wd[i], P_[i + 1] + side * Wd[i + 1], P_[i + 1] - side * Wd[i + 1]], 'tkfrond',
                  uv=[(0.5 - Wd[i] / 0.6, V[i]), (0.5 + Wd[i] / 0.6, V[i]), (0.5 + Wd[i + 1] / 0.6, V[i + 1]), (0.5 - Wd[i + 1] / 0.6, V[i + 1])])
    for k in range(5):
        ang = math.tau * k / 5; d = Vector((math.cos(ang), 0, math.sin(ang))); side = Vector((-d.z, 0, d.x))
        P_ = [hc + d * 0.02, hc + d * 0.12 + up_ * 0.5, hc + d * 0.45 + up_ * 0.78]
        sheet([P_[0] - side * 0.08, P_[0] + side * 0.08, P_[1] + side * 0.2, P_[1] - side * 0.2], 'tkfrond', uv=[(0.37, 1), (0.63, 1), (0.83, 0.5), (0.17, 0.5)])
        sheet([P_[1] - side * 0.2, P_[1] + side * 0.2, P_[2] + side * 0.05, P_[2] - side * 0.05], 'tkfrond', uv=[(0.17, 0.5), (0.83, 0.5), (0.58, 0.0), (0.42, 0.0)])
    fx_, fy_, fz_ = lx0 - m - 0.06, yh + 0.0, lz1 - 0.15  # the flower, on the band at the front left
    for k in range(5):
        a0 = math.tau * k / 5; a1 = a0 + 0.9
        T3([(fx_ - 0.005, fy_, fz_), (fx_ - 0.02, fy_ + 0.16 * math.sin(a0), fz_ + 0.16 * math.cos(a0)), (fx_ - 0.02, fy_ + 0.16 * math.sin(a1), fz_ + 0.16 * math.cos(a1))], 'tkpink', out=(-1, 0, 0))
    lathe((fx_ - 0.01, fy_, fz_), [(0.03, 0.0), (0.03, 0.04), (0.0, 0.07)], 'tkyellow', n=6, axis=(-1, 0, 0))
    ub = Vector((cx + 0.35, yh + 0.1, cz - 0.2)); ut = ub + Vector((0.12, 0.75, 0.05))
    pole(ub, ut, 0.012, 'tkwhite', n=4)
    lathe(ut - Vector((0, 0.03, 0)), [(0.3, 0.0), (0.0, 0.14)], 'tkpink', n=8, rot=0.2)
    lathe(ut - Vector((0, 0.03, 0)), [(0.0, 0.0), (0.3, 0.0)], 'tkyellow', n=8, rot=0.2)
    # offerings on the plinth in front of him: two coconuts, a pineapple, a bunch of bananas
    yo = py1 + 0.003; zo = (zf + pz1) / 2 + 0.02
    for (a, r) in ((-0.75, 0.1), (-0.55, 0.085)):
        lathe((rel(a), yo, zo), [(0.0, 0.0), (r * 0.7, 0.01), (r, r * 0.9), (r * 0.7, r * 1.7), (0.0, r * 1.85)], 'tkcoco', n=8)
    lathe((rel(0.55), yo, zo), [(0.0, 0.0), (0.07, 0.01), (0.1, 0.1), (0.08, 0.21), (0.03, 0.24), (0.0, 0.24)], 'tkyellow', n=8)
    pc = Vector((rel(0.55), yo + 0.2, zo))
    for k in range(3):
        ang = k * math.pi / 3; side = Vector((math.cos(ang), 0, math.sin(ang))) * 0.1
        sheet([pc - side * 0.3, pc + side * 0.3, pc + side + Vector((0, 0.26, 0)), pc - side + Vector((0, 0.26, 0))], 'tkfrond', uv=[(0.4, 1), (0.6, 1), (1, 0.2), (0, 0.2)])
    st = Vector((rel(0.2), yo + 0.02, zo))  # bananas: a bunch off one stalk, curving up at the tips
    pole(st, st + Vector((-0.07, 0.03, 0.0)), 0.016, 'tkgreen', n=4)
    for k in range(4):
        ang = -0.5 + k * 0.33; d = Vector((math.cos(ang), 0, math.sin(ang)))
        pts = [st + d * (0.07 * t) + Vector((0, 0.035 * t * t, 0)) for t in range(4)]
        for i in range(3): pole(pts[i], pts[i + 1], 0.022, 'tkyellow', n=5, caps=(False, i == 2))


# ------------------------------------------------------------ a beach hut (built door to -z; turned if it faces +z)
def hut(walls, roofs, cloth, crate=None):
    r1, r2 = sorted(roofs, key=lambda b: b['min'][1])
    cx, cz = (r1['min'][0] + r1['max'][0]) / 2, (r1['min'][2] + r1['max'][2]) / 2; yb = min(b['min'][1] for b in walls)
    win = next(b for b in walls if abs(b['max'][1] - yb - 1.0) < 1e-3)
    rot = 2 if (win['min'][2] + win['max'][2]) / 2 < cz else 0  # (the window's side is the back)
    XF.append(shift(0, 0, 0, rot, cx, cz))
    def L(b):  # a box in the hut's own frame (back where it would be if it faced -z)
        if rot != 2: return b
        return {'min': [2 * cx - b['max'][0], b['min'][1], 2 * cz - b['max'][2]], 'max': [2 * cx - b['min'][0], b['max'][1], 2 * cz - b['min'][2]], 'mat': b['mat']}
    W = [L(b) for b in walls]
    x0 = min(b['min'][0] for b in W) + 0.1; x1 = max(b['max'][0] for b in W) - 0.1
    z0 = min(b['min'][2] for b in W) + 0.1; z1 = max(b['max'][2] for b in W) - 0.1
    ys = 0.42 + yb  # the floor beam: everything under it is the stilts and the skirt
    K.solids = [(b['min'], b['max']) for b in W]  # (only the hut's own: so its faces against its own walls drop out)
    sol = K.solids
    def hidden(c, n):
        p = [c[i] + n[i] * 0.004 for i in range(3)]
        return any(all(mn[i] - 1e-4 <= p[i] <= mx[i] + 1e-4 for i in range(3)) for mn, mx in sol)
    for b in W:
        (bx0, by0, bz0), (bx1, by1, bz1) = b['min'], b['max']
        thin_x = bx1 - bx0 < 0.3
        for f, n in (('px', (1, 0, 0)), ('nx', (-1, 0, 0)), ('pz', (0, 0, 1)), ('nz', (0, 0, -1))):
            ax = 0 if f[1] == 'x' else 2
            c = [(bx0 + bx1) / 2, (by0 + by1) / 2, (bz0 + bz1) / 2]; c[ax] = (b['max'][ax] if f[0] == 'p' else b['min'][ax])
            broad = (thin_x and ax == 0) or (not thin_x and ax == 2)
            if not broad:
                if hidden(c, n): continue
                # a jamb or the wall's end: bamboo end-on look
                a0, a1 = ((bz0, bz1) if ax == 0 else (bx0, bx1))
                if ax == 0: q = [(c[0], by0, a0), (c[0], by0, a1), (c[0], by1, a1), (c[0], by1, a0)]
                else: q = [(a0, by0, c[2]), (a1, by0, c[2]), (a1, by1, c[2]), (a0, by1, c[2])]
                Q(q, 'tkbamold', out=n); continue
            outside = (ax == 0 and ((f == 'px') == (c[0] > cx))) or (ax == 2 and ((f == 'pz') == (c[2] > cz)))
            a0, a1 = ((bz0, bz1) if ax == 0 else (bx0, bx1))
            for (ya, yb_, mat) in ((by0, min(by1, ys), 'tkweaved' if outside else 'tkwall'), (max(by0, ys), by1, 'tkwall')):
                if yb_ - ya < 1e-3: continue
                if ax == 0: q = [(c[0], ya, a0), (c[0], ya, a1), (c[0], yb_, a1), (c[0], yb_, a0)]
                else: q = [(a0, ya, c[2]), (a1, ya, c[2]), (a1, yb_, c[2]), (a0, yb_, c[2])]
                Q(q, mat, out=n, sub=1.2)
        for f, n, y in (('py', (0, 1, 0), by1), ('ny', (0, -1, 0), by0)):
            if y >= r1['min'][1] - 1e-3 or y <= yb + 1e-3 or hidden(((bx0 + bx1) / 2, y, (bz0 + bz1) / 2), n): continue
            Q([(bx0, y, bz0), (bx1, y, bz0), (bx1, y, bz1), (bx0, y, bz1)], 'tkbamold', out=n)
    K.solids = []
    # corner posts (into the sand, up into the thatch), lashed at the floor beam and the wall plate
    for (x, z) in ((x0, z0), (x1, z0), (x1, z1), (x0, z1)):
        pole((x, yb - 0.25, z), (x, r1['min'][1] + 0.05, z), 0.15, 'tkbam', n=8, caps=(False, True), rot=0.2)
        lash((x, ys, z), (0, 1, 0), 0.15, w=0.09); lash((x, r1['min'][1] - 0.18, z), (0, 1, 0), 0.15, w=0.09)
    # the floor beam and stilt ends round the outside, the wall plate under the eaves (not across the door)
    dx0, dx1 = cx - 0.6, cx + 0.6
    for (za, s) in ((z0, -1), (z1, 1)):
        zo = za + s * 0.155
        segs = [(x0, dx0 - 0.08), (dx1 + 0.08, x1)] if s < 0 else [(x0, x1)]
        for (a, b) in segs: pole((a - 0.05 if a == x0 else a, ys, zo), (b + 0.05 if b == x1 else b, ys, zo), 0.06, 'tkbamold', n=6)
        pole((x0 - 0.05, r1['min'][1] - 0.12, zo), (x1 + 0.05, r1['min'][1] - 0.12, zo), 0.055, 'tkbam', n=6)
        for k in range(1, 4):
            x = x0 + k * (x1 - x0) / 4
            if s < 0 and dx0 - 0.15 < x < dx1 + 0.15: x = dx0 - 0.2 if x < cx else dx1 + 0.2
            pole((x, yb - 0.2, zo - s * 0.01), (x, ys + 0.03, zo - s * 0.01), 0.075, 'tkbam', n=6, caps=(False, True))
    for (xa, s) in ((x0, -1), (x1, 1)):
        xo = xa + s * 0.155
        pole((xo, ys, z0 - 0.05), (xo, ys, z1 + 0.05), 0.06, 'tkbamold', n=6)
        pole((xo, r1['min'][1] - 0.12, z0 - 0.05), (xo, r1['min'][1] - 0.12, z1 + 0.05), 0.055, 'tkbam', n=6)
        for k in (1, 2):
            z = z0 + k * (z1 - z0) / 3
            pole((xo - s * 0.01, yb - 0.2, z), (xo - s * 0.01, ys + 0.03, z), 0.075, 'tkbam', n=6, caps=(False, True))
    # the door: a frame of poles, a split-log step half in the sand, the blind rolled up over it
    for x in (dx0 - 0.03, dx1 + 0.03): pole((x, yb - 0.05, z0), (x, yb + 2.2, z0), 0.075, 'tkbam', n=6)
    pole((dx0 - 0.15, yb + 2.15, z0), (dx1 + 0.15, yb + 2.15, z0), 0.07, 'tkbam', n=6)
    pole((dx0 - 0.05, yb + 2.33, z0 - 0.19), (dx1 + 0.05, yb + 2.33, z0 - 0.19), 0.1, 'tkweave', n=8)
    for x in (dx0 + 0.1, dx1 - 0.1): pole((x, yb + 2.45, z0 - 0.14), (x, yb + 2.26, z0 - 0.2), 0.012, 'tkrope', n=4)
    bx((dx0 - 0.05, yb - 0.08, z0 - 0.46), (dx1 + 0.05, yb + 0.07, z0 - 0.05), {'top': 'tkplank', 'side': 'tkgraind'}, skip=('ny', 'pz'))
    # the window: a frame, the shutter propped open over it
    wy0, wy1 = yb + 1.0, yb + 1.9; wa, wb = cx - 0.8, cx + 0.8
    for y in (wy0, wy1): pole((wa - 0.12, y, z1), (wb + 0.12, y, z1), 0.06, 'tkbam', n=6)
    for x in (wa, wb): pole((x, wy0 - 0.1, z1), (x, wy1 + 0.1, z1), 0.05, 'tkbam', n=6)
    h0 = Vector((0, wy1 + 0.04, z1 + 0.1)); h1 = h0 + Vector((0, 0.38, 0.6))
    for (a, b) in ((wa - 0.1, wb + 0.1),):
        p = [Vector((a, h0.y, h0.z)), Vector((b, h0.y, h0.z)), Vector((b, h1.y, h1.z)), Vector((a, h1.y, h1.z))]
        nrm = (p[1] - p[0]).cross(p[3] - p[0]).normalized() * 0.025
        for (u0, u1, o) in ((p, None, None),):
            Q([p[0] + nrm, p[1] + nrm, p[2] + nrm, p[3] + nrm], 'tkwall', out=nrm, uv=[(0, 0), (1.8, 0), (1.8, 0.7), (0, 0.7)])
            Q([p[0] - nrm, p[1] - nrm, p[2] - nrm, p[3] - nrm], 'tkwall', out=-nrm, uv=[(0, 0), (1.8, 0), (1.8, 0.7), (0, 0.7)])
            for (i, j) in ((0, 1), (1, 2), (2, 3), (3, 0)):
                Q([p[i] - nrm, p[j] - nrm, p[j] + nrm, p[i] + nrm], 'tkbamold', out=(p[i] + p[j]) / 2 - (p[0] + p[2]) / 2)
    for x in (wa + 0.05, wb - 0.05): pole((x, wy0 + 0.05, z1 + 0.06), (x, h1.y - 0.04, h1.z - 0.02), 0.022, 'tkbamold', n=4)
    # the roof: hipped thatch over the two slabs, a ridge roll with tufts at its ends
    R1, R2 = tier_rect(r1), tier_rect(r2)
    R1, R2 = [tier_rect(L(r1)), tier_rect(L(r2))]
    zm = (R2[1] + R2[3]) / 2; hw = (R2[2] - R2[0]) / 2 - (R2[3] - R2[1]) / 2
    ridge = (cx - hw, zm, cx + hw, zm)
    skirt(R2, r1['max'][1] + 0.02, R1, r1['max'][1] - 0.08, {k: 0.36 for k in 'nswe'}, r1['min'][1] - 0.06, {k: 0.28 for k in 'nswe'}, y_under=r1['min'][1])
    yr = r2['max'][1] + 0.14
    skirt(ridge, yr, R2, r2['max'][1] - 0.08, {k: 0.3 for k in 'nswe'}, r2['min'][1] + 0.08, {k: 0.16 for k in 'nswe'}, y_under=r2['min'][1])
    pole((ridge[0] - 0.25, yr + 0.02, zm), (ridge[2] + 0.25, yr + 0.02, zm), 0.12, 'tkthatch', n=8)
    for x in (ridge[0] - 0.1, ridge[2] + 0.1):
        lash((x, yr + 0.02, zm), (1, 0, 0), 0.11)
        for k in range(5):
            ang = k * math.tau / 5 + 0.3; d = Vector((math.cos(ang) * 0.8, 1, math.sin(ang) * 0.8)).normalized()
            base = Vector((x, yr + 0.06, zm)); side = Vector((-math.sin(ang), 0, math.cos(ang))) * 0.16
            mid = base + d * 0.4; tip = base + d * 0.75 + Vector((math.cos(ang), -0.5, math.sin(ang))) * 0.2
            sheet([base - side * 0.3, base + side * 0.3, mid + side, mid - side], 'tkfrond', uv=[(0.4, 1), (0.6, 1), (0.9, 0.5), (0.1, 0.5)])
            sheet([mid - side, mid + side, tip + side * 0.2, tip - side * 0.2], 'tkfrond', uv=[(0.1, 0.5), (0.9, 0.5), (0.55, 0.0), (0.45, 0.0)])
    # inside: the ceiling, rafters across, the hammock slung between the side walls
    yc = r1['min'][1]
    wo = (x0 - 0.1, z0 - 0.1, x1 + 0.1, z1 + 0.1)  # the soffit: under the slab, from the walls out to its edge
    for (a, b, c, d_) in (((R1[0], R1[1]), (R1[2], R1[1]), (wo[2], wo[1]), (wo[0], wo[1])), ((R1[2], R1[1]), (R1[2], R1[3]), (wo[2], wo[3]), (wo[2], wo[1])),
                          ((R1[2], R1[3]), (R1[0], R1[3]), (wo[0], wo[3]), (wo[2], wo[3])), ((R1[0], R1[3]), (R1[0], R1[1]), (wo[0], wo[1]), (wo[0], wo[3]))):
        Q([(a[0], yc, a[1]), (b[0], yc, b[1]), (c[0], yc, c[1]), (d_[0], yc, d_[1])], 'tkthatchd', out=(0, -1, 0))
    Q([(x0 + 0.1, yc, z0 + 0.1), (x1 - 0.1, yc, z0 + 0.1), (x1 - 0.1, yc, z1 - 0.1), (x0 + 0.1, yc, z1 - 0.1)], 'tkthatchd', out=(0, -1, 0))
    for x in (cx - 1.1, cx, cx + 1.1): pole((x, yc - 0.05, z0 + 0.08), (x, yc - 0.05, z1 - 0.08), 0.05, 'tkbamold', n=6)
    if cloth:
        c = L(cloth); hz = (c['min'][2] + c['max'][2]) / 2; ha, hb = c['min'][0] + 0.05, c['max'][0] - 0.05
        sand = max(ground(x, z) for x in [ha + (hb - ha) * k / 8 for k in range(9)] for z in (hz - 0.3, hz, hz + 0.3))
        lift = max(0.0, sand + 0.32 - (yb + 0.9))
        yh, ysp, ym = yb + 1.75 + lift, yb + 1.28 + lift, yb + 0.9 + lift
        for (xw, xs) in ((x0 + 0.1, ha), (x1 - 0.1, hb)):
            pole((xw, yh - 0.05, hz), (xw, yh + 0.05, hz), 0.03, 'tkgraind', n=4)  # (the hook peg)
            pole((xs, ysp, hz - 0.36), (xs, ysp, hz + 0.36), 0.025, 'tkbam', n=4)
            for dz in (-0.33, 0.33): pole((xw + (0.03 if xw < cx else -0.03), yh, hz), (xs, ysp, hz + dz), 0.01, 'tkrope', n=4)
        NA, NC = 10, 2
        def hp(i, j):
            t = i / NA; x = ha + (hb - ha) * t; s = j / NC * 2 - 1
            return Vector((x, ysp - (ysp - ym) * 4 * t * (1 - t) - 0.1 * (1 - s * s) * (4 * t * (1 - t)) ** 0.5, hz + s * 0.34 * (1 - 0.25 * (4 * t * (1 - t)) ** 0.0)))
        for i in range(NA):
            for j in range(NC):
                sheet([hp(i, j), hp(i + 1, j), hp(i + 1, j + 1), hp(i, j + 1)], 'tkhammock', uv=[(j / NC, i / NA * 3.4), (j / NC, (i + 1) / NA * 3.4), ((j + 1) / NC, (i + 1) / NA * 3.4), ((j + 1) / NC, i / NA * 3.4)])
    XF.pop()


# ------------------------------------------------------------ the surf school
def surf(deco):
    post = next(b for b in deco if b['mat'] == 'wood')
    boards = sorted([b for b in deco if b['mat'] != 'wood'], key=lambda b: b['min'][0])
    px, pz = (post['min'][0] + post['max'][0]) / 2, (post['min'][2] + post['max'][2]) / 2; yb = post['min'][1]
    pole((px, yb - 0.2, pz), (px, yb + 2.78, pz), 0.065, 'tkbam', n=6)
    lathe((px, yb + 2.78, pz), [(0.0, -0.01), (0.08, 0.03), (0.09, 0.1), (0.0, 0.17)], 'tkcoco', n=8)  # (a coconut on top, obviously)
    # the sign (the game's: shared/map.js surfSchool, x -1.2..+1.3 of the post, y 1.6..2.6, just in front of it): framed
    sx0, sx1, sy0, sy1, sz = px - 1.26, px + 1.24, yb + 1.6, yb + 2.6, pz + 0.1
    pole((sx0 - 0.08, sy1 + 0.04, sz), (sx1 + 0.08, sy1 + 0.04, sz), 0.04, 'tkbam', n=6)
    pole((sx0 - 0.08, sy0 - 0.04, sz), (sx1 + 0.08, sy0 - 0.04, sz), 0.04, 'tkbam', n=6)
    for x in (sx0 - 0.04, sx1 + 0.04): pole((x, sy0 - 0.1, sz), (x, sy1 + 0.1, sz), 0.04, 'tkbam', n=6)
    for (x, y) in ((px, sy1 + 0.04), (px, sy0 - 0.04)): lash((x, y, sz), (1, 0, 0), 0.04, w=0.06)
    # the boards, nose up, leaning, each in a little mound of sand
    mats = {'toypink': 'tkpink', 'toyyellow': 'tkyellow', 'toyteal': 'tkcyan'}
    for k, b in enumerate(boards):
        x, z = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2; g = max(ground(x + dx, z + dz) for dx in (-0.3, 0, 0.3) for dz in (-0.2, 0, 0.2))
        mat = mats.get(b['mat'], 'tkpink'); y0 = b['min'][1] - 0.3; H = 2.45; Wd = 0.29; th = 0.035
        tilt, lean, twist = (-0.12, 0.06, -0.1), (0.1, -0.02, -0.1), (0.25, -0.2, 0.12)
        ca, sa = math.cos(twist[k % 3]), math.sin(twist[k % 3])
        def P(a, y, o):  # board space (across, up, out of its face) -> local, leaning back and to the side, twisted
            v = Vector((a, y, o))
            v = Vector((v.x, v.y * math.cos(tilt[k % 3]) - v.z * math.sin(tilt[k % 3]), v.y * math.sin(tilt[k % 3]) + v.z * math.cos(tilt[k % 3])))
            v = Vector((v.x * math.cos(lean[k % 3]) - v.y * math.sin(lean[k % 3]), v.x * math.sin(lean[k % 3]) + v.y * math.cos(lean[k % 3]), v.z))
            v = Vector((v.x * ca + v.z * sa, v.y, -v.x * sa + v.z * ca))
            return Vector((x, y0, z)) + v
        NY = 8
        def w(t): return Wd * (0.72 + 0.28 * math.sin(min(1.0, t / 0.45) * math.pi / 2)) if t < 0.5 else Wd * math.sqrt(max(0.0, 1 - ((t - 0.5) / 0.5) ** 2.2))
        def bite(t): return 0.17 * max(0.0, 1 - ((t - 0.58) / 0.09) ** 2) ** 0.5 * (1.0 if round((t - 0.49) / 0.0225) % 2 else 0.7) if k == 1 else 0.0
        ts = sorted(set([i / NY for i in range(NY + 1)] + ([0.49 + 0.0225 * j for j in range(9)] if k == 1 else [])))
        rows = [(t, -w(t), w(t) - bite(t)) for t in ts]
        for i in range(len(rows) - 1):
            (t0, l0, r0), (t1, l1, r1_) = rows[i], rows[i + 1]
            for o, s in ((th, 1), (-th, -1)):
                pts = [P(l0, t0 * H, o), P(r0, t0 * H, o), P(r1_, t1 * H, o), P(l1, t1 * H, o)]
                if (pts[2] - pts[3]).length < 1e-4: T3([pts[0], pts[1], pts[2]], mat, out=P(0, 0, s) - P(0, 0, 0))
                else: Q(pts, mat, out=P(0, 0, s) - P(0, 0, 0))
            for (e0, e1, s) in ((l0, l1, -1), (r0, r1_, 1)):
                if abs(e0 - e1) < 1e-5 and abs(e0) < 1e-5: continue
                pts = [P(e0, t0 * H, -th), P(e1, t1 * H, -th), P(e1, t1 * H, th), P(e0, t0 * H, th)]
                if (pts[1] - pts[2]).length < 1e-5: continue
                Q(pts, 'tkwhite', out=P(s, 0, 0) - P(0, 0, 0))
        Q([P(-w(0), 0, -th), P(w(0), 0, -th), P(w(0), 0, th), P(-w(0), 0, th)], 'tkwhite', out=P(0, -1, 0) - P(0, 0, 0))
        for o in (th, -th):  # the stringer, a racing stripe across
            s = 1 if o > 0 else -1
            for (a0, a1, y_0, y_1, m, h) in ((-0.012, 0.012, 0.02, H - 0.1, 'tkwhite', 0.003), (-w(0.4) + 0.02, w(0.4) - 0.02, 0.36 * H, 0.4 * H, 'tkwhite' if k != 2 else 'tkpink', 0.006)):
                pts = [P(a0, y_0, o + s * h), P(a1, y_0, o + s * h), P(a1, y_1, o + s * h), P(a0, y_1, o + s * h)]
                Q(pts, m, out=P(0, 0, s) - P(0, 0, 0))
                for (i, j) in ((0, 1), (1, 2), (2, 3), (3, 0)):
                    Q([pts[i], pts[j], pts[j] - (P(0, 0, s * (h + 0.002)) - P(0, 0, 0)), pts[i] - (P(0, 0, s * (h + 0.002)) - P(0, 0, 0))], m, out=(pts[i] + pts[j]) / 2 - (pts[0] + pts[2]) / 2)
        lathe((x, g - 0.06, z), [(0.5, 0.0), (0.38, 0.09), (0.16, 0.16), (0.0, 0.18)], 'tksand', n=10, rot=0.1 * k)


# ------------------------------------------------------------ build
def build(kind):
    global K, G
    d = json.load(open(os.path.join(HERE, 'boxes', kind + '.json')))
    K = Kit(d, seed=13)
    K.ground = -1e9
    G = json.load(open(os.path.join(HERE, 'boxes', 'tiki_ground.json'))) if kind == 'tiki' else None
    bs = [b for b in d['boxes'] if not b.get('deco')]; ds = [b for b in d['boxes'] if b.get('deco')]
    K.solids = [(b['min'], b['max']) for b in bs]
    def near(b, c, r): return abs((b['min'][0] + b['max'][0]) / 2 - c[0]) < r[0] and abs((b['min'][2] + b['max'][2]) / 2 - c[1]) < r[1]
    def tris(): return sum(2 if len(f) == 4 else 1 for g in K.geo.values() for f in g['f'])
    stats = []; mark = lambda name: stats.append((name, tris()))
    # the bar: round its back bar
    back = next(b for b in bs if b['mat'] == 'wood' and b['max'][1] - b['min'][1] > 1.5 and b['max'][0] - b['min'][0] > 7)
    bc = ((back['min'][0] + back['max'][0]) / 2, (back['min'][2] + back['max'][2]) / 2 + 2.6)
    tiki_bar([b for b in bs if near(b, bc, (6, 4.5))], [b for b in ds if near(b, bc, (6, 4.5))]); mark('tiki bar')
    # the big tiki: round its plinth
    base = next(b for b in bs if b['mat'] == 'basalt'); tc = ((base['min'][0] + base['max'][0]) / 2, (base['min'][2] + base['max'][2]) / 2)
    big_tiki([b for b in bs if near(b, tc, (1.5, 1.5))], [b for b in ds if near(b, tc, (1.5, 1.5))]); mark('big tiki')
    # the huts: one per lower thatch slab
    for r in [b for b in bs if b['mat'] == 'thatch' and abs(b['max'][0] - b['min'][0] - 5.4) < 1e-3]:
        hc = ((r['min'][0] + r['max'][0]) / 2, (r['min'][2] + r['max'][2]) / 2)
        mine = [b for b in bs if near(b, hc, (3, 2.6))]
        hut([b for b in mine if b['mat'] == 'bamboo'], [b for b in mine if b['mat'] == 'thatch'], next((b for b in ds if b['mat'] == 'cloth' and near(b, hc, (3, 2.6))), None)); mark('hut')
    # the surf school: round its post
    post = next(b for b in ds if b['mat'] == 'wood' and b['max'][1] - b['min'][1] > 2.5 and b['max'][0] - b['min'][0] < 0.2)
    sc = ((post['min'][0] + post['max'][0]) / 2 + 2, (post['min'][2] + post['max'][2]) / 2 + 0.6)
    surf([b for b in ds if near(b, sc, (3.5, 1.5))]); mark('surf school')
    print('tris by piece:', ', '.join(f'{n} {t - (stats[i - 1][1] if i else 0)}' for i, (n, t) in enumerate(stats)), '| all', stats[-1][1])
    K.solids = [(b['min'], b['max']) for b in bs]
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in ('tiki', 'tiki_sd')] or ['tiki', 'tiki_sd']):
    build(kind)
