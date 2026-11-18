# THE CUTE SET, ROUND 3: BIGGER SIGNATURE PIECES (17 Nov 2026). The owner, on round 1: "Cute concept has potential but
# the shapes are irregular and aren't cohesive to how a gun should look!! Like it should have some elements of the base
# gun"; then: "I want bigger more noticeable decorations do research on those themes and how they're applied in other
# games and take from it and learn". Brief: vault Research/Skin concepts/Skin briefs.md, "Cute set v3: bigger signature
# pieces"; research: "Cute set - big decorations.md"; blockouts: sketches/src/blockouts/cute_v3.py (cards in
# sketches/blockout-cards/*_v3.png). E Daydream is dropped.
#
# EVERY SKIN HERE IS THE LIVE GUN ITSELF (gun_models_c.BUILD: the picked C rifle and C Plan B), every solid kept where
# it is and repainted, with the decoration added on top: the base gun's lines stay readable. What the research set:
#   - the outline grows about +15-25% through ONE hero piece 20-35% of the gun's height on the LEFT flank (first person
#     sees the top and the left), ahead of the hand and under the sight line; smaller pieces reshape the ends (muzzle,
#     magazine tip, stock end) and the underside;
#   - fluff is one soft object at a joint or a charm, never a coat; jewels sit in settings (bezel and claws); wings are
#     puffy lobes rooted at a joint and swept back; crystals cluster on one station and grow out of a real part; a candy
#     cane needs its hook; a bow is tied over a ribbon band;
#   - nothing floats, nothing rises above the sight line, the bore end stays dark, the hands' spots stay clear (the
#     Rifle's off hand at z -0.34..-0.22, the thumb behind z 0.02).
#   a  Velvet      an oval jewel locket (gold bezel, velvet bed, pearl rim, a big lavender stone in four claws), a fur
#                  muff at the stock joint, a pom-pom charm, a tufted cushion stock with a tassel, pearls at the ends
#   b  Starlight   puffy three-lobe wings rooted where the handguard meets the receiver, a star collar at the muzzle (one
#                  point down), big gold stars on the stock and magazine, ribbons tied under the front and at the wrist
#   c  Glasswing   a stained-glass butterfly on the flank, a seven-crystal cluster growing from the handguard's front,
#                  swept crystals at the muzzle, a butterfly stock, a wing-tip fin at the magazine base
#   d  Sweet Shop  a ribbon band with one big bow, a candy cane under the barrel hooked down at the muzzle, three gumdrop
#                  lights on the handguard, raised stripes, the stock end a wrapper twist
# THE CONTRACT (gunskin_kit.py): the live gun's spots, its moving nodes where they were (ar: mag, charge; pistol: slide,
# mag, hammer), the base gun's slim sights (gun_sights.py, near-black) and wrap zones (_wzA shells kept). Decoration that
# rides on the slide or the magazine is on that node. The rest sits on its own nodes (locket, wing, bow ...) so the
# hold rows (holds.json ads.skins hide / near) can name it.
# LAYERS AND FLICKER: every raised layer of another colour stands at least 4.5 mm (Rifle) / 2.5 mm (Plan B) over the
# face under it (the flicker scan's 0.02 studs on the armory racks), rims are round tubes, plates are soft lenses.
# Built only when named (gun_set.py reads JF_EXTRA); these builders replace gun_sets_cute.py's for the same keys:
#   JF_EXTRA=gun_sets_cute3 blender -b --factory-startup -P tools/roblox/gun_set.py -- <out_dir> ar@ar_cute_a ...
#   JF_EXTRA=gun_sets_cute3 blender -b --factory-startup -P tools/roblox/gun_check.py -- ar@ar_cute_a ...
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector
import gunkit
from gunkit import Gun, P
import gun_sights as SG
from gun_models_c3 import loft
from gun_sets import tsweep
from gun_sets_ducky import pillow
from gun_sets_cute import ellipsoid, chaikin, _nuv, diamond, inside

RAD = math.radians
AR_SY, PB_SY = 0.114, 0.0585
PB_RAKE = -0.297

# ------------------------------------------------------------------------------------------------ the palettes
# (the v2 concept palettes, Skin briefs.md; cdark the sights' near-black, cblack the slots and ports)
PAL = {
    'A': dict(main='d9a6b0', main2='ecd0d5', cdark='3b3036', cblack='211b1f', ctrim='c6a25c', cglow=('a47cff', 'n'),
              soft='f3ede5', soft2='ddd3cb'),
    'B': dict(main='ece5e8', main2='c75a76', cdark='3b3437', cblack='211c1f', ctrim='cfa451', cglow=('ff4f8e', 'n'),
              soft='f7f3f1', soft2='efcfd8'),
    'C': dict(main='e9e5ee', main2='b6a8da', cdark='3d3a44', cblack='222027', ctrim='cfc7e6', cglow=('5fe2dc', 'n'),
              soft='a8d8c8', soft2='efc6b4'),
    'D': dict(main='efe4d3', main2='cf6d7e', cdark='3d3638', cblack='231e20', ctrim='f7f1e6', cglow=('ff4f86', 'n'),
              soft='a3d6c4', soft2='8a6458'),
}
# the brief's new slots (gem: a solid lavender stone; only its small table is Neon: a Neon stone renders near-white)
EXTRA = dict(pearl='f6f1ea', fur='f5efe8', fur2='e8ddd4', gem='9b84d6', deep='a9475f', glass='c6e6ec', bowin='a94e60',
             velvet='bf7d8c', velvet2='a26877', lav='8a78b8', gumglow=('c8406a', 'n'))  # (velvet: A's cushion a step deeper; lav: C's collar and crystal bed)


def new_gun(key, wid, skinid):
    g = Gun('w_%s@%s' % (wid, skinid))
    for k, v in list(PAL[key].items()) + list(EXTRA.items()):
        if isinstance(v, tuple): g.slot(k, *v)
        else: g.slot(k, v)
    return g


# ------------------------------------------------------------------------------------------------ the base gun
def _split(bm):
    """a piece's mesh cut into its connected solids: [(bmesh, lo, hi)] (lo / hi in the gun's frame)"""
    bm.verts.index_update(); bm.verts.ensure_lookup_table()
    par = list(range(len(bm.verts)))
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for e in bm.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b: par[a] = b
    groups = {}
    for v in bm.verts: groups.setdefault(find(v.index), []).append(v)
    out = []
    for root, vs in groups.items():
        nb = bmesh.new()
        m = {v.index: nb.verts.new(v.co) for v in vs}
        for f in bm.faces:
            if find(f.verts[0].index) != root: continue
            nf = nb.faces.new([m[v.index] for v in f.verts]); nf.smooth = f.smooth
        for e in bm.edges:
            if find(e.verts[0].index) != root: continue
            ne = nb.edges.get([m[e.verts[0].index], m[e.verts[1].index]])
            if ne: ne.smooth = e.smooth
        lo = [min(v.co.x for v in vs), min(v.co.z for v in vs), min(-v.co.y for v in vs)]
        hi = [max(v.co.x for v in vs), max(v.co.z for v in vs), max(-v.co.y for v in vs)]
        out.append((nb, lo, hi))
    return out


def _put(g, piece, nb):
    me = bpy.data.meshes.new('tmp')
    nb.to_mesh(me); nb.free()
    g._bm(piece).from_mesh(me)
    bpy.data.meshes.remove(me)


def rebase(g, wid, tag, paint):
    """the live gun's solids into g, each repainted: tag(node, slot, lo, hi) names the solid, paint[name] is its new
       slot (the node kept), a whole piece name 'node__slot', or None (left out). Takes the live gun's spots"""
    import gun_models_c as CC
    gunkit.use_style('C')
    base = CC.BUILD[wid]()
    g.spots = dict(base.spots)
    for (node, slot), bm in base.pieces.items():
        for nb, lo, hi in _split(bm):
            name = tag(node, slot, lo, hi)
            if name not in paint: raise SystemExit('%s: no paint for %s (%s__%s)' % (g.name, name, node, slot))
            new = paint[name]
            if new is None: nb.free(); continue
            _put(g, new if '__' in new else node + '__' + new, nb)
        bm.free()
    return base


def ar_tag(node, slot, lo, hi):
    n = node.split('_wz')[0]
    if n == 'body':
        if node.endswith('A'): return 'cover'
        if node.endswith('N'): return 'ribs'
        return 'gastube' if hi[2] < -0.19 else 'receiver'
    if n in ('rivet', 'mark', 'dot', 'charge'): return n
    if n == 'sight': return 'rail' if slot == 'frame' else 'sights'
    if n == 'trim': return 'ports' if hi[2] < -0.6 else ('port' if lo[0] > 0.02 else 'railslot')
    if n == 'guard': return ('guard' if lo[1] < 0 else 'guardtop') if node.endswith('A') else 'grooves'
    if n == 'barrel': return 'brake' if hi[2] < -0.63 else ('gasblock' if hi[1] > 0.06 else 'barrel')
    if n == 'mag': return 'magplate' if node.endswith('N') else ('mag' if lo[1] < -0.2 else 'magrib')
    if n == 'grip': return 'grip' if lo[1] < -0.15 else 'tguard'
    if n == 'stock':
        if node.endswith('A'): return 'stock'
        return 'tube' if hi[2] < 0.34 else ('cheek' if lo[1] > 0.06 else 'pad')
    return n


def pb_tag(node, slot, lo, hi):
    n = node.split('_wz')[0]
    if n == 'slide':
        if node.endswith('A'): return 'slide'
        if slot == 'black': return 'slideblack'
        if lo[1] > 0.049: return 'sights'
        if lo[2] < -0.239: return 'bushing' if hi[1] > 0.02 else 'plug'
        return 'grooves'
    if n == 'body':
        if node.endswith('N'): return 'stop' if hi[2] < 0 else 'safety'
        if hi[2] < -0.19: return 'barrel'
        if lo[1] > -0.03: return 'frame'
        return 'tguard' if lo[1] < -0.07 else 'trigger'
    if n == 'grip': return 'panels' if node.endswith('A') else ('grip' if lo[1] < -0.1 else 'tang')
    if n == 'rivet': return 'screws'
    if n == 'mag': return 'magbase' if node.endswith('N') else 'mag'
    return n


AR_PAINT = dict(receiver='main', gastube='main2', cover='main2', ribs='ctrim', rivet='ctrim', mark=None, rail='cdark',
                railslot='cblack', sights='cdark', ports='cblack', port='cblack', guard='main2', guardtop='main2',
                grooves='ctrim', brake='cdark', barrel='cdark', gasblock='cdark', dot='cglow', mag='cdark',
                magrib='cdark', magplate='ctrim', grip='cdark', tguard='cdark', stock='main2', tube='cdark',
                cheek='main', pad='main', charge='ctrim')
PB_PAINT = dict(slide='main', sights='cdark', bushing='cdark', plug='cdark', grooves='ctrim', slideblack='cblack',
                barrel='cdark', frame='main2', tguard='main2', trigger='ctrim', stop='ctrim', safety='cdark', grip='cdark',
                tang='cdark', panels='main2', screws='ctrim', mag='cdark', magbase='ctrim', hammer='ctrim')


def short_stop(g, slot):
    """Plan B's slide stop, shortened to its thumb piece (z -0.042..-0.016): a slide that locks back on an empty
       magazine carries its decoration 38 mm back, over where the long lever was"""
    g.prism('body_wzN__' + slot, [(-0.040, 0.002), (-0.022, 0.002), (-0.016, -0.006), (-0.022, -0.014), (-0.036, -0.012),
                                   (-0.042, -0.006)], 0.004, x=-0.0215, bev=0.0015)
    g.cyl('body_wzN__' + slot, 0.0052, (-0.0235, -0.005, -0.034), (-0.0256, -0.005, -0.034), sides=8, bev=0.001)


# ------------------------------------------------------------------------------------------------ outlines
def ell(c, a, b, rot=0.0, n=24, p=2.0):
    """an ellipse [(z, y)] round c, half axes a (along z before turning) and b, turned rot degrees; p > 2 blunts it
       toward a rounded box"""
    cr, sr = math.cos(RAD(rot)), math.sin(RAD(rot))
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        ct, st_ = math.cos(t), math.sin(t)
        u, v = a * math.copysign(abs(ct) ** (2.0 / p), ct), b * math.copysign(abs(st_) ** (2.0 / p), st_)
        out.append((c[0] + u * cr - v * sr, c[1] + u * sr + v * cr))
    return out


def oval_even(c, a, b, n, x=0.0):
    """n points evenly spaced ALONG an ellipse's edge (its arc), as (x, y, z)"""
    M = 720
    pts = [(c[0] + a * math.cos(2 * math.pi * i / M), c[1] + b * math.sin(2 * math.pi * i / M)) for i in range(M)]
    cum = [0.0]
    for i in range(1, M + 1):
        p, q = pts[i - 1], pts[i % M]
        cum.append(cum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    tot = cum[-1]
    out, j = [], 0
    for k in range(n):
        s = tot * k / n
        while cum[j + 1] < s: j += 1
        f = (s - cum[j]) / max(1e-12, cum[j + 1] - cum[j])
        p, q = pts[j], pts[(j + 1) % M]
        out.append((x, p[1] + (q[1] - p[1]) * f, p[0] + (q[0] - p[0]) * f))
    return out, tot


def star_pts(c, R, r, n=5, ang=90.0):
    return [(c[0] + (R if i % 2 == 0 else r) * math.cos(RAD(ang + 180.0 * i / n)),
             c[1] + (R if i % 2 == 0 else r) * math.sin(RAD(ang + 180.0 * i / n))) for i in range(2 * n)]


def soft_star(c, R, r, n=5, ang=90.0, it=2):
    """a five-point star with rounded points [(u, v)], its points still reaching R"""
    pts = chaikin(star_pts(c, R, r, n, ang), it)
    m = max(math.hypot(p[0] - c[0], p[1] - c[1]) for p in pts)
    k = R / m
    return [(c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k) for p in pts]


def area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) / 2


def resample(pts, n):
    """a closed outline resampled to n points evenly spaced along its edge"""
    m = len(pts)
    cum = [0.0]
    for i in range(1, m + 1):
        p, q = pts[i - 1], pts[i % m]
        cum.append(cum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    out, j = [], 0
    for k in range(n):
        t = cum[-1] * k / n
        while cum[j + 1] < t: j += 1
        f = (t - cum[j]) / max(1e-12, cum[j + 1] - cum[j])
        p, q = pts[j], pts[(j + 1) % m]
        out.append((p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f))
    return out


def shrink(pts, k):
    """a closed outline scaled by k toward its centroid"""
    n = len(pts)
    cu, cv = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
    return [(cu + (u - cu) * k, cv + (v - cv) * k) for u, v in pts]


def fillet_poly(pts, r, seg=6):
    """a closed outline [(u, v)] with every corner rounded to radius r (at most 45% of the shorter edge beside it)"""
    n = len(pts)
    out = []
    for i in range(n):
        A, Pp, B = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        a, b = A - Pp, B - Pp
        la, lb = a.length, b.length
        d1, d2 = a / la, b / lb
        th = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        if th > math.pi - 0.02 or th < 0.02: out.append(tuple(Pp)); continue
        t = min(r / math.tan(th / 2), 0.45 * min(la, lb))
        rr = t * math.tan(th / 2)
        T1, T2 = Pp + d1 * t, Pp + d2 * t
        C = Pp + (d1 + d2).normalized() * (rr / math.sin(th / 2))
        a1 = math.atan2(T1.y - C.y, T1.x - C.x)
        da = (math.atan2(T2.y - C.y, T2.x - C.x) - a1 + math.pi) % (2 * math.pi) - math.pi
        for k in range(seg + 1):
            out.append((C.x + rr * math.cos(a1 + da * k / seg), C.y + rr * math.sin(a1 + da * k / seg)))
    return out


def inset(pts, d):
    """a closed outline moved d inward along its normals (negative d: outward)"""
    s = 1.0 if area(pts) > 0 else -1.0
    n = len(pts)
    out = []
    for i in range(n):
        a, b = pts[i - 1], pts[(i + 1) % n]
        tz, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tz, ty) or 1.0
        out.append((pts[i][0] - ty / L * d * s, pts[i][1] + tz / L * d * s))
    return out


def bez(p0, p1, p2, n=16):
    return [tuple((1 - t) ** 2 * p0[k] + 2 * (1 - t) * t * p1[k] + t * t * p2[k] for k in range(len(p0)))
            for t in [i / n for i in range(n + 1)]]


def clip(poly, edges):
    """a polygon [(z, y)] clipped to a convex outline (Sutherland-Hodgman); edges: the outline, counter-clockwise"""
    out = list(poly)
    m = len(edges)
    for i in range(m):
        a, b = edges[i], edges[(i + 1) % m]
        def inside(p): return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0
        def cross(p, q):
            x1, y1, x2, y2 = p[0], p[1], q[0], q[1]
            x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
            den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
            return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
        src, out = out, []
        if not src: break
        for j in range(len(src)):
            p, q = src[j - 1], src[j]
            if inside(q):
                if not inside(p): out.append(cross(p, q))
                out.append(q)
            elif inside(p): out.append(cross(p, q))
    return out


def polar_union(o, ells, pad, n=96):
    """the outline [(u, v)] of a union of ellipses [(centre, a, b, turn)] each grown by pad, swept round o (o must lie
       inside one of them): a wing's backing that follows its lobes, notches and all"""
    out = []
    for i in range(n):
        ph = 2 * math.pi * i / n
        best = 0.0
        for c, a, b, rot in ells:
            A, B = a + pad, b + pad
            cr, sr = math.cos(RAD(rot)), math.sin(RAD(rot))
            ox, oy = o[0] - c[0], o[1] - c[1]
            ox, oy = ox * cr + oy * sr, -ox * sr + oy * cr
            dx, dy = math.cos(ph) * cr + math.sin(ph) * sr, -math.cos(ph) * sr + math.sin(ph) * cr
            qa = dx * dx / A / A + dy * dy / B / B
            qb = 2 * (ox * dx / A / A + oy * dy / B / B)
            qc = ox * ox / A / A + oy * oy / B / B - 1
            disc = qb * qb - 4 * qa * qc
            if disc < 0: continue
            best = max(best, (-qb + math.sqrt(disc)) / (2 * qa))
        out.append((o[0] + best * math.cos(ph), o[1] + best * math.sin(ph)))
    return out


def bite(pts, c, r, n_arc=12):
    """a closed outline with a round bite (centre c, radius r) taken out where the circle cuts it (one run of points)"""
    n = len(pts)
    ins = [math.hypot(q[0] - c[0], q[1] - c[1]) < r for q in pts]
    if not any(ins): return list(pts)
    s0 = next(i for i in range(n) if not ins[i] and ins[(i + 1) % n])
    e0 = next(i for i in range(n) if ins[i] and not ins[(i + 1) % n])
    def edge(po, pi):
        lo, hi = 0.0, 1.0
        for _ in range(40):
            m = (lo + hi) / 2
            q = (po[0] + (pi[0] - po[0]) * m, po[1] + (pi[1] - po[1]) * m)
            if math.hypot(q[0] - c[0], q[1] - c[1]) < r: hi = m
            else: lo = m
        return (po[0] + (pi[0] - po[0]) * lo, po[1] + (pi[1] - po[1]) * lo)
    a = edge(pts[s0], pts[(s0 + 1) % n])
    b = edge(pts[(e0 + 1) % n], pts[e0])
    ta, tb = math.atan2(a[1] - c[1], a[0] - c[0]), math.atan2(b[1] - c[1], b[0] - c[0])
    cu = sum(q[0] for q in pts) / n; cv = sum(q[1] for q in pts) / n
    best = None
    for d in ((tb - ta) % (2 * math.pi), (tb - ta) % (2 * math.pi) - 2 * math.pi):
        mid = ta + d / 2
        dist = math.hypot(c[0] + r * math.cos(mid) - cu, c[1] + r * math.sin(mid) - cv)
        if best is None or dist < best[0]: best = (dist, d)
    arc = [(c[0] + r * math.cos(ta + best[1] * k / n_arc), c[1] + r * math.sin(ta + best[1] * k / n_arc)) for k in range(1, n_arc)]
    keep = [pts[(e0 + 1 + k) % n] for k in range((s0 - e0) % n)]
    return keep + [a] + arc + [b]


def tail_poly(path, w0, w1, notch):
    """a ribbon tail along a path [(u, v)], w0 wide at its root and w1 at its end, a V cut notch deep into its end"""
    n = len(path)
    L, R = [], []
    for i, p in enumerate(path):
        a, b = path[max(0, i - 1)], path[min(n - 1, i + 1)]
        tz, ty = b[0] - a[0], b[1] - a[1]
        d = math.hypot(tz, ty) or 1
        w = (w0 + (w1 - w0) * i / max(1, n - 1)) / 2
        L.append((p[0] - ty / d * w, p[1] + tz / d * w)); R.append((p[0] + ty / d * w, p[1] - tz / d * w))
    e, f = path[-1], path[-2]
    dz, dy = e[0] - f[0], e[1] - f[1]; dl = math.hypot(dz, dy) or 1
    v = (e[0] - dz / dl * notch, e[1] - dy / dl * notch)
    return L + [v] + R[::-1]


# ------------------------------------------------------------------------------------------------ frames and solids
def side(sx, xm):
    """a plane on a side of the gun at |x| = xm: (O, U back, V up, N out). outlines in it are (z, y)"""
    return (Vector((sx * xm, 0.0, 0.0)), Vector((0, 0, 1)), Vector((0, 1, 0)), Vector((sx, 0, 0)))


MID = (Vector((0, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0)), Vector((1, 0, 0)))  # the gun's middle plane


def at(frame, u, v, h=0.0):
    O, U, V, N = frame
    return tuple(O + U * u + V * v + N * h)


def lens(g, piece, outline, frame, out, back, e=None, cap=0.05, nd=2, back_full=False):
    """a soft solid from an outline [(u, v)] in a frame's plane: its widest ring in the plane, domed `out` along N and
       `back` against it, the edge rounded (e). The dome closes to a tiny cap (no big flat face to flicker); the back is
       a plain chamfered face (it is buried in what it stands on) unless back_full (both sides seen: domed alike)"""
    O, U, V, N = frame
    n = len(outline)
    cu = sum(p[0] for p in outline) / n
    cv = sum(p[1] for p in outline) / n
    R = sum(math.hypot(u - cu, v - cv) for u, v in outline) / n
    def prof(t):
        ee = e if e is not None else min(0.45 * t, 0.006, 0.3 * R)
        ee = min(ee, 0.9 * t)
        ph = math.radians(65)
        lv = [(1 - ee * (1 - math.cos(ph)) / R, ee * math.sin(ph))]
        s1 = 1 - ee / R
        for j in range(1, nd + 1):
            f = j / nd
            lv.append((s1 * (1 - (1 - cap) * f), ee + (t - ee) * (1 - (1 - f) ** 2)))
        return lv
    def ring(s, h):
        return [tuple(O + U * (cu + (u - cu) * s) + V * (cv + (v - cv) * s) + N * h) for u, v in outline]
    if back_full:
        bk = list(reversed(prof(back)))
    else:
        bk = [(0.1, back)]  # (a shallow cone to a tiny cap: buried, and no big flat face to flicker against)
    rings = [ring(s, -h) for s, h in bk] + [ring(1.0, 0.0)] + [ring(s, h) for s, h in prof(out)]
    loft(g, piece, rings, group=lambda i, k: 'r')


def slab(g, piece, outline, frame, t, e, n_arc=3, h0=0.0):
    """a flat plate from an outline [(u, v)] in a frame's plane, t thick (from h0 to h0 + t along N), every edge rounded
       over by e (ribbons, fins, tails)"""
    O, U, V, N = frame
    hm = h0 + t / 2
    hs = max(0.0, t / 2 - e)
    prof = []
    for i in range(n_arc, -1, -1):
        ph = math.pi / 2 * i / n_arc
        prof.append((e * (1 - math.cos(ph)), hm - hs - e * math.sin(ph)))
    if hs > 1e-5: prof.append((0.0, hm + hs))
    for i in range(1, n_arc + 1):
        ph = math.pi / 2 * i / n_arc
        prof.append((e * (1 - math.cos(ph)), hm + hs + e * math.sin(ph)))
    rings = [[tuple(O + U * u + V * v + N * h) for u, v in inset(outline, d)] for d, h in prof]
    loft(g, piece, rings, group=lambda i, k: 'r')


def tloop(g, piece, pts, N, r, rn=None, n=6):
    """a soft round tube along a CLOSED path [(x, y, z)] lying in a plane whose normal is N: r across in the plane, rn
       along N (rims, bezels, bands)"""
    rn = rn or r
    N = Vector(N).normalized()
    m = len(pts)
    C = sum((Vector(p) for p in pts), Vector()) / m
    bm = bmesh.new()
    rows = []
    for i in range(m):
        p = Vector(pts[i])
        T = (Vector(pts[(i + 1) % m]) - Vector(pts[i - 1])).normalized()
        B = T.cross(N).normalized()
        if B.dot(p - C) < 0: B = -B
        rows.append([bm.verts.new(P(*(p + B * (r * math.cos(math.pi * (2 * j + 1) / n)) + N * (rn * math.sin(math.pi * (2 * j + 1) / n)))))  # (half a step round: no face lies flat on the plane)
                     for j in range(n)])
    for i in range(m):
        for j in range(n):
            bm.faces.new([rows[i][j], rows[(i + 1) % m][j], rows[(i + 1) % m][(j + 1) % n], rows[i][(j + 1) % n]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(piece, bm, smooth=lambda f: True)


def rim(g, piece, outline, frame, h, r, rn=None, n=6):
    """a round tube round an outline [(u, v)] at height h in a frame"""
    tloop(g, piece, [at(frame, u, v, h) for u, v in outline], frame[3], r, rn, n)


def gem_stone(g, piece, table_piece, c, nrm, r, n=8, crown=0.36, table=0.56, pav=0.62, band=0.1, plug=None):
    """a faceted round stone, its girdle at c facing nrm: the pavilion sunk to a point, a short girdle, crown facets up
       to the table ring; the table is a separate plug (the Neon) a hair proud of it, so no two flat faces of the stone
       and its light lie on each other. returns the table's height over c"""
    N, U, V = _nuv(nrm)
    G = Vector(c)
    off = math.pi / n
    bm = bmesh.new()
    def ring(cen, rad):
        return [bm.verts.new(P(*(cen + (U * math.cos(off + 2 * math.pi * i / n) + V * math.sin(off + 2 * math.pi * i / n)) * rad)))
                for i in range(n)]
    g0, g1 = ring(G, r), ring(G + N * (band * r), r)
    ht = (band + crown) * r
    tb = ring(G + N * ht, r * table)
    tip = bm.verts.new(P(*(G - N * (pav * r))))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([g0[j], g0[i], tip])
        bm.faces.new([g0[i], g0[j], g1[j], g1[i]])
        bm.faces.new([g1[i], g1[j], tb[j], tb[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(piece, bm)
    bm = bmesh.new()
    pk = plug or table
    lo = ring(G + N * (ht - 0.004), r * pk * 0.97)
    hi = ring(G + N * (ht + 0.0008), r * pk)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
    bm.faces.new(lo[::-1]); bm.faces.new(hi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    g._add(table_piece, bm)
    if plug and plug < table:  # (a lavender step round a smaller glowing table)
        bm = bmesh.new()
        lo = ring(G + N * (ht - 0.0085), r * table * 0.9)  # (its buried bottom well clear of the light's)
        hi = ring(G + N * (ht - 0.0004), r * table)
        top = ring(G + N * (ht + 0.0004), r * plug * 0.995)  # (its open top tucked under the light's rim)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new([lo[i], lo[j], hi[j], hi[i]])
            bm.faces.new([hi[i], hi[j], top[j], top[i]])
        bm.faces.new(lo[::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        g._add(piece, bm)
    return ht


def claws(g, piece, c, nrm, r, ht, angs=(45, 135, 225, 315), rc=0.0034):
    """gold claws holding a stone (girdle at c, radius r, table ht over it): each rises from the bed beside the girdle
       and bends over the crown"""
    N, U, V = _nuv(nrm)
    G = Vector(c)
    for a in angs:
        d = U * math.cos(RAD(a)) + V * math.sin(RAD(a))
        p0 = G + d * (r * 1.12) - N * (r * 0.25)
        p1 = G + d * (r * 1.08) + N * (ht * 0.35)
        p2 = G + d * (r * 0.84) + N * (ht * 0.62)
        tsweep(g, piece, [tuple(p0), tuple(p1), tuple(p2)], [rc, rc * 0.95, rc * 0.8], n=5, side=tuple(N.cross(d)))
        pearl(g, piece, rc * 0.85, tuple(p2), n=5, m=2)


def ellip(g, piece, c, axes, n=8, m=4):
    """a smooth ellipsoid at c with three half axes [(direction, radius)]: n round, m from pole to pole"""
    C = Vector(c)
    A = [Vector(d).normalized() * r for d, r in axes]
    rings = []
    for ph in [0.3 * math.pi / m] + [math.pi * i / m for i in range(1, m)] + [math.pi - 0.3 * math.pi / m]:
        rings.append([tuple(C + A[2] * (-math.cos(ph)) + (A[0] * math.cos(2 * math.pi * j / n) + A[1] * math.sin(2 * math.pi * j / n)) * math.sin(ph))
                      for j in range(n)])
    loft(g, piece, rings, group=lambda i, k: 'r')  # (its small flat caps sit right at the poles)


def pearl(g, piece, r, c, n=8, m=4):
    ellip(g, piece, c, [((1, 0, 0), r), ((0, 1, 0), r), ((0, 0, 1), r)], n, m)


def pearl_ring(g, piece, c, a, b, x, r, gap=1.03):
    pts, per = oval_even(c, a, b, 400, x)
    n = max(6, int(per / (2 * r * gap)))
    pts, _ = oval_even(c, a, b, n, x)
    for p in pts: pearl(g, piece, r, p, n=6 if r >= 0.0065 else 5, m=3)
    return n


def _ell_field(c, axes):
    """ellip()'s shape as an exact field: an ellipsoid at c with axes [(direction, radius)] x 3"""
    import numpy as np
    import sdf_kit as SDF
    R = np.array([list(Vector(d).normalized()) for d, r in axes]).T
    return SDF.ellipsoid(tuple(c), tuple(r for d, r in axes), rot=R)


def pompom_fields(c, R, n=24, k=1.0):
    """pompom()'s core and tufts as exact fields: (the main shade's, the second shade's)"""
    C = Vector(c)
    fa, fb = [_ell_field(C, [((1, 0, 0), R * 0.8), ((0, 1, 0), R * 0.8), ((0, 0, 1), R * 0.8)])], []
    for i in range(n):
        yy = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(max(0.0, 1 - yy * yy))
        th = i * 2.39996
        d = Vector((rr * math.cos(th), yy, rr * math.sin(th))).normalized()
        s = R * (0.40 + 0.07 * ((i * 7) % 4) / 3) * k
        o = d.orthogonal().normalized()
        (fb if (i % 3 == 0 or yy < -0.75) else fa).append(
            _ell_field(C + d * (R * (0.6 + 0.4 * (1 - k))), [(o, s), (d.cross(o), s * 0.92), (d, s * 0.72)]))
    return fa, fb


def fur_ring_fields(z, cy, R, r, n=12, rows=3, dz=0.016, flat=0.62):
    """fur_ring()'s core tube and clumps as exact fields: (the main shade's, the second shade's)"""
    import numpy as np
    h = (rows - 1) / 2 * dz + r * 0.5
    def core(p):   # (the core tube round the z axis at (0, cy), R round, z +- h)
        q0 = np.sqrt(p[:, 0] ** 2 + (p[:, 1] - cy) ** 2) - R
        q1 = np.abs(p[:, 2] - z) - h
        return np.minimum(np.maximum(q0, q1), 0.0) + np.sqrt(np.maximum(q0, 0.0) ** 2 + np.maximum(q1, 0.0) ** 2)
    fa, fb = [core], []
    for row in range(rows):
        for kk in range(n):
            a = math.pi / 2 + 2 * math.pi * (kk + 0.5 * row) / n
            rr = r * (1.0 if (kk + row) % 2 == 0 else 0.82)
            ca, sa = math.cos(a), math.sin(a)
            (fb if (sa < -0.5 or (kk * 5 + row * 3) % 7 == 0) else fa).append(
                _ell_field((R * ca, cy + R * sa, z + (row - (rows - 1) / 2) * dz),
                           [((-sa, ca, 0), rr), ((0, 0, 1), rr * 0.9), ((ca, sa, 0), rr * flat)]))
    return fa, fb


def fuse_soft(g, node, fields, kin, h, tris, seam_k=0.7):
    """ONE SOFT FORM (18 Nov 2026; the owner: shapes stuck together look AI-made): a fur muff's clumps and a pom-pom's
       tufts were separate low-poly balls pushed into each other. sdf_kit.fuse melts them into one fluffy skin from
       their exact shapes (fields: (the main shade's, the second shade's), from pompom_fields / fur_ring_fields; a
       fillet kin between neighbours), each tuft still painted its own shade. (The bows were tried too: they already
       read as one shape and came out lumpier, so they stay as built)"""
    import sdf_kit as SDF
    fa, fb = fields
    parts = [((node, 'fur'), 0, SDF.union(*fa, k=kin))]
    if fb and (node, 'fur2') in g.pieces: parts.append(((node, 'fur2'), kin, SDF.union(*fb, k=kin)))
    return SDF.fuse(g, parts, h=h, tris=tris, name='soft_' + node, seam_k=seam_k)


def pompom(g, pa, pb, c, R, n=24, k=1.0):
    """one soft fluffy ball: a core and n squashed tufts spread round it (two shades)"""
    C = Vector(c)
    ellip(g, pa, tuple(C), [((1, 0, 0), R * 0.8), ((0, 1, 0), R * 0.8), ((0, 0, 1), R * 0.8)], n=10, m=5)
    for i in range(n):
        yy = 1 - 2 * (i + 0.5) / n
        rr = math.sqrt(max(0.0, 1 - yy * yy))
        th = i * 2.39996
        d = Vector((rr * math.cos(th), yy, rr * math.sin(th))).normalized()
        s = R * (0.40 + 0.07 * ((i * 7) % 4) / 3) * k
        o = d.orthogonal().normalized()
        ellip(g, pb if (i % 3 == 0 or yy < -0.75) else pa, tuple(C + d * (R * (0.6 + 0.4 * (1 - k)))),
              [(o, s), (d.cross(o), s * 0.92), (d, s * 0.72)], n=7, m=3)


def fur_ring(g, pa, pb, z, cy, R, r, n=12, rows=3, dz=0.016, flat=0.62):
    """a fat fur muff round the z axis at (0, cy): rows of squashed clumps in two sizes and two shades on a core tube"""
    for row in range(rows):
        for k in range(n):
            a = math.pi / 2 + 2 * math.pi * (k + 0.5 * row) / n
            rr = r * (1.0 if (k + row) % 2 == 0 else 0.82)
            ca, sa = math.cos(a), math.sin(a)
            pc = pb if (sa < -0.5 or (k * 5 + row * 3) % 7 == 0) else pa
            ellip(g, pc, (R * ca, cy + R * sa, z + (row - (rows - 1) / 2) * dz),
                  [((-sa, ca, 0), rr), ((0, 0, 1), rr * 0.9), ((ca, sa, 0), rr * flat)], n=7, m=3)
    h = (rows - 1) / 2 * dz + r * 0.5
    g.cyl(pa, R, (0, cy, z - h), (0, cy, z + h), sides=12, bev=0.0)


def chain(g, piece, p0, p1, r):
    A, B = Vector(p0), Vector(p1)
    k = max(2, int(math.ceil((B - A).length / (r * 1.7))) + 1)
    for i in range(k):
        pearl(g, piece, r, tuple(A.lerp(B, i / (k - 1))), n=5, m=3)


def bead_drop(g, piece, top, y1, r=0.0045, x=None):
    """a gold bead chain hanging straight down from top (x, y, z) to y1"""
    chain(g, piece, top, (top[0], y1, top[2]), r)


def tassel(g, cap, body, top, L, r0, r1, k=8):
    """a tassel hanging from top (x, y, z): a gold cap and bead, a ridged skirt of strands flaring from r0 to r1 over L,
       its ends rounded under"""
    x, y, z = top
    g.cyl(cap, r0 * 0.7, (x, y + 0.002, z), (x, y - 0.014, z), r2=r0 * 1.25, sides=12, bev=0.0012)
    pearl(g, cap, r0 * 0.75, (x, y - 0.018, z))
    y0 = y - 0.021
    rings = []
    prof = [(0.0, 0.85), (0.08, 1.0), (0.4, 1.18), (0.75, 1.4), (0.92, 1.42), (0.985, 1.1), (1.0, 0.5)]
    for u, w in prof:
        rad = r0 + (r1 - r0) * (w - 0.85) / 0.57 if w > 0.85 else r0 * w / 0.85
        rings.append([(x + rad * (1.0 if j % 2 == 0 else 0.86) * math.cos(math.pi * j / k), y0 - L * u,
                       z + rad * (1.0 if j % 2 == 0 else 0.86) * math.sin(math.pi * j / k)) for j in range(2 * k)])
    loft(g, body, rings, group=lambda i, kk: 'r')
    g.ring(cap, r0 * 1.05, r0 * 0.6, (x, y0 - L * 0.06, z), (x, y0 - L * 0.16, z), sides=12, bev=0.001)


def loop_uv(knot, ang, L, W, n=16, pinch=0.66):
    """a bow's loop seen flat [(u, v)]: a teardrop from the knot out along ang (degrees), L long, W wide"""
    ca, sa = math.cos(RAD(ang)), math.sin(RAD(ang))
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        u = L / 2 * (1 - math.cos(t))
        k = 1 - pinch * (1 - u / L) ** 2
        v = W / 2 * math.sin(t) * k
        out.append((knot[0] + u * ca - v * sa, knot[1] + u * sa + v * ca))
    return out


def bow(g, node, frame, knot, s, t, sl, fold, knot_sl, angs=(160.0, 20.0), L=1.0, W=0.66, tails=None, tail_w=(0.28, 0.34),
        tail_t=None, centred=False, sweet=None, knot_k=(0.21, 0.27), tail_h0=-0.001):
    """a puffy ribbon bow in a frame's plane, knot at (u, v), s its size: two loops (a soft round rim each and the darker
       inner fold showing inside it), a wrapped knot (or a round sweet: sweet = its slot), tails [(path)] with V cut ends.
       centred: it stands across the frame's plane (hangs under the gun); else it lies on the plane (a flank)"""
    O, U, V, N = frame
    rn = t / 2
    hc = 0.0 if centred else rn * 0.8
    for ang in angs:
        ol = loop_uv(knot, ang, L * s, W * s)
        rr = W * s * 0.17
        rim(g, node + '__' + sl, inset(ol, rr), frame, hc, rr, rn, n=6)
        fo = inset(ol, rr * 1.55)
        if centred: lens(g, node + '__' + fold, fo, frame, out=rn * 0.5, back=rn * 0.5, back_full=True)
        else: lens(g, node + '__' + fold, fo, frame, out=hc + rn * 0.35, back=0.002)
    tt = tail_t or t * 0.38
    for path in tails or []:
        tp = tail_poly(path, tail_w[0] * s, tail_w[1] * s, 0.14 * s)
        if centred: slab(g, node + '__' + sl, tp, frame, tt, min(0.0018, tt * 0.4), h0=-tt / 2, n_arc=2)
        else: slab(g, node + '__' + sl, tp, frame, tt, min(0.0018, tt * 0.4), h0=tail_h0, n_arc=2)
    kz, ky = knot_k
    if centred:
        lens(g, node + '__' + (knot_sl if not sweet else sl), ell(knot, kz * s, ky * s, n=14), frame, out=rn * 1.15, back=rn * 1.15, back_full=True)
        # (the ribbon gathered under the knot, over the tails' roots: the gap between them read as a hole)
        lens(g, node + '__' + sl, ell((knot[0], knot[1] - 0.3 * s), 0.2 * s, 0.24 * s, n=14), frame, out=rn * 0.85, back=rn * 0.85, back_full=True)
    else:
        lens(g, node + '__' + (knot_sl if not sweet else sl), ell(knot, kz * s, ky * s, n=14), frame, out=hc + rn * 1.1, back=0.002)
    if sweet:  # the round sweet over the knot (D: the glow), the ribbon gathered under it over the tails' roots
        if not centred:
            lens(g, node + '__' + sl, ell((knot[0], knot[1] - 0.2 * s), 0.17 * s, 0.17 * s, n=14), frame, out=hc + rn * 0.55, back=0.002)
        h = rn * 1.15 if centred else hc + rn * 1.1
        lens(g, node + '__' + sweet, ell(knot, kz * s * 1.05, kz * s * 1.05, n=14), frame, out=h + 0.0055, back=0.0008 if not centred else h,
             back_full=centred)


def soft_bow(g, node, frame, knot, s, t, sl, fold, knot_sl, angs=(160.0, 20.0), L=1.0, W=0.66, tails=None,
             tail_w=(0.28, 0.34), tail_t=None, centred=False, sweet=None, knot_k=(0.21, 0.27), tail_h0=-0.001, h=None,
             tris=1600):
    """THE SAME BOW AS bow() (its place, size, loop angles and tails), ONE MOULDED SKIN (18 Nov 2026; the owner: shapes
       stuck together look AI-made, and every bow in the game should match the Tripo bow's puffy one-piece look): two
       closed puffy loops (pillows on bow()'s teardrop outlines, thin where they pinch into the knot, fat at their
       ends), a rounded knot they melt into, the tails as soft ribbon slabs, the sweet (if any) a dome on the knot. One
       distance field (sdf_kit), painted: loops and tails `sl`, the knot `knot_sl`, the sweet `sweet` (the old inner
       fold colour is not used: the loops are closed). Its pieces are added to the node's as their own closed skin"""
    import numpy as np
    import sdf_kit as SDF
    O, U, V, N = [np.array(tuple(x), float) for x in frame]
    rn = t / 2
    nc = 0.0 if centred else rn * 0.55          # (the loops' middle above the plane: sunk a little into the gun)
    def local(p):
        q = p - O
        return q @ U, q @ V, q @ N
    def loop(ang):
        ol = loop_uv(knot, ang, L * s, W * s)
        d2 = SDF.polygon2(ol)
        dirv = np.array([math.cos(RAD(ang)), math.sin(RAD(ang))])
        def f(p):
            u, v, n = local(p)
            along = np.clip(((u - knot[0]) * dirv[0] + (v - knot[1]) * dirv[1]) / (L * s), 0.0, 1.0)
            hx = t * (0.32 + 0.42 * along)
            q0 = d2(u, v) + hx; q1 = np.abs(n - nc)
            return np.minimum(np.maximum(q0, q1), 0.0) + np.sqrt(np.maximum(q0, 0.0) ** 2 + np.maximum(q1, 0.0) ** 2) - hx
        return f
    loops = SDF.union(*[loop(a) for a in angs], k=0.002)
    tt = tail_t or t * 0.38
    tl = []
    for path in tails or []:
        tp = tail_poly(path, tail_w[0] * s, tail_w[1] * s, 0.14 * s)
        d2 = SDF.polygon2(tp)
        hz = tt / 2; r = min(0.0018, tt * 0.45)
        n0 = 0.0 if centred else tail_h0 + hz
        def tf(p, d2=d2, hz=hz, r=r, n0=n0):
            u, v, n = local(p)
            q0 = d2(u, v) + r; q1 = np.abs(n - n0) - (hz - r)
            return np.minimum(np.maximum(q0, q1), 0.0) + np.sqrt(np.maximum(q0, 0.0) ** 2 + np.maximum(q1, 0.0) ** 2) - r
        tl.append(tf)
    ribbon = SDF.union(loops, *tl, k=0.0025) if tl else loops
    kz, ky = knot_k
    R3 = np.stack([U, V, N], 1)
    kc = O + U * knot[0] + V * knot[1] + N * nc
    knotf = SDF.ellipsoid(tuple(kc), (kz * s, ky * s, rn * 1.5), rot=R3)
    whole = SDF.blend(ribbon, knotf, 0.0025)
    parts, labels = [ribbon, knotf], [sl, knot_sl]
    if sweet:
        sw = SDF.ellipsoid(tuple(kc + N * (rn * 1.2 if not centred else 0.0)), (kz * s * 0.95, kz * s * 0.95, rn * 1.1 + 0.002), rot=R3)
        whole = SDF.blend(whole, sw, 0.0015); parts.append(sw); labels.append(sweet)
    # the box round it: the loops, the knot and the tails' outlines, in the frame, then in the weapon frame
    uv = [pt for a in angs for pt in loop_uv(knot, a, L * s, W * s)]
    for path in tails or []: uv += tail_poly(path, tail_w[0] * s, tail_w[1] * s, 0.14 * s)
    nn = [-t * 1.6, t * 1.6] if centred else [-t, t * 1.8 + 0.006]
    corners = [O + U * a + V * b + N * c for a, b in uv for c in nn]
    lo = np.min(corners, 0) - 0.004; hi = np.max(corners, 0) + 0.004
    step = h or min(t / 9, tt / 5)
    lab_idx = list(range(len(labels)))
    # (labels that name the same slot share one piece)
    names = []
    for lb in labels:
        if lb not in names: names.append(lb)
    near = SDF.nearest(*parts)
    cls = lambda p: np.array([names.index(labels[i]) for i in near(p)])
    out = SDF.mesh_paint(whole, cls, names, lo, hi, h=step, tris=tris, name='bow_' + node, seam_k=1.0)
    for lb, bm in out.items():
        me = bpy.data.meshes.new('bow'); bm.to_mesh(me); bm.free()
        g._bm(node + '__' + lb).from_mesh(me)
        bpy.data.meshes.remove(me)


def crystal(g, piece, base, tip, r, tipk=0.3, tipr=0.08):
    """a hexagonal crystal from base to tip: a straight body, then a faceted point"""
    B, T = Vector(base), Vector(tip)
    m = B.lerp(T, 1 - tipk)
    g.cyl(piece, r, tuple(B), tuple(m), sides=6, r2=r * 0.94, bev=0.0012, smooth=False)
    g.cyl(piece, r * 0.94, tuple(m), tuple(T), sides=6, r2=r * tipr, bev=0.0008, smooth=False)


def star_badge(g, node, c, R, r, w, sl_gold, sl_fill, sl_core=None, ang=90.0, fill_k=0.8, core_k=0.37, h=(0.0065, 0.0085),
               bev=0.004, sides=(-1, 1)):
    """a big chunky star through a part (w thick, centred on the gun's middle), a puffy fill star on each face and a
       glowing core star on it"""
    g.prism(node + '__' + sl_gold, soft_star(c, R, r, ang=ang, it=1), w, bev=bev)
    for sx in sides:
        fr = side(sx, w / 2 - 0.001)
        lens(g, node + '__' + sl_fill, soft_star(c, R * fill_k, r * fill_k, ang=ang, it=1), fr, out=h[0] + 0.001, back=0.002)
        if sl_core:
            lens(g, node + '__' + sl_core, soft_star(c, R * core_k, r * core_k, ang=ang, it=1), side(sx, w / 2 + h[0] - 0.002),
                 out=h[1], back=0.003)


def bez_mag(t, front=True):
    """the C rifle's curved magazine edges (gun_models_c.ar: curved_mag control points), at t (0 top .. 1 bottom)"""
    P0, P1, P2 = ((-0.165, -0.05), (-0.172, -0.18), (-0.235, -0.3)) if front else ((-0.045, -0.05), (-0.055, -0.18), (-0.115, -0.31))
    return tuple((1 - t) ** 2 * P0[k] + 2 * (1 - t) * t * P1[k] + t * t * P2[k] for k in (0, 1))


def mag_z_at(y, front=True):
    lo, hi = 0.0, 1.0
    for _ in range(40):
        m = (lo + hi) / 2
        if bez_mag(m, front)[1] > y: lo = m
        else: hi = m
    return bez_mag((lo + hi) / 2, front)[0]


def flare(g, piece, c0, c1, U, V, a0, b0, a1, b1, k, depth, steps=5, p=3.2, ease=0.8, lip=0.004, crest=None, crest_r=0.0024,
          crest_steps=None, zig=0.0, crest_on='U'):
    """a pleated wrapper flare from the section at c0 (half sizes a0 along U, b0 along V) out to c1 (a1, b1): rounded
       box sections whose edge is cut in k pleats, deepening as it opens, a rounded lip at the end. crest: a slot for a
       thin raised line along each pleat's crest (icing lines)"""
    C0, C1, U, V = Vector(c0), Vector(c1), Vector(U).normalized(), Vector(V).normalized()
    A = (C1 - C0).normalized()
    M = k * 6
    def sec(f, sc=1.0, push=0.0):
        C = C0.lerp(C1, f) + A * push
        a = a0 + (a1 - a0) * f ** ease
        b = b0 + (b1 - b0) * f ** ease
        dep = depth * f
        pts = []
        for j in range(M):
            th = 2 * math.pi * j / M
            ca, sa = math.cos(th), math.sin(th)
            x = a * math.copysign(abs(ca) ** (2.0 / p), ca)
            y = b * math.copysign(abs(sa) ** (2.0 / p), sa)
            m = (1 - dep * (0.5 - 0.5 * math.cos(k * th))) * sc
            zz = zig * f ** 3 * (0.5 + 0.5 * math.cos(k * th))  # (the crests run further out: a zig-zag end)
            pts.append(tuple(C + U * (x * m) + V * (y * m) + A * zz))
        return pts
    rings = [sec(i / steps) for i in range(steps + 1)]
    rings += [sec(1.0, 0.97, lip * 0.6), sec(1.0, 0.9, lip)]
    loft(g, piece, rings, group=lambda i, kk: 'r')
    if crest:
        for j in range(k):
            th = 2 * math.pi * j / k
            if abs(math.cos(th) if crest_on == 'U' else math.sin(th)) < 0.6: continue
            idx = int(round(th / (2 * math.pi) * M)) % M
            line = []
            for i in range(1, (crest_steps or steps) + 1):
                f = 0.12 + 0.86 * i / (crest_steps or steps)
                q = Vector(sec(f)[idx])
                Cc = C0.lerp(C1, f)
                out = (q - Cc - A * (q - Cc).dot(A)).normalized()
                line.append(tuple(q + out * crest_r * 0.8))
            tsweep(g, crest, line, [crest_r] * len(line), n=5, side=tuple(A))
            pearl(g, crest, crest_r, line[-1], n=6, m=3)


def cane(g, pa, pb, pts, r, k=3, turn=0.045, t=0.0022, m=3, cap=True):
    """a candy cane along a path [(x, y, z)]: a core and 2k helical stripes (pa, pb), one turn every `turn`
       metres along it, its end rounded (pa)"""
    V = [Vector(p) for p in pts]
    n = len(V)
    T = [(V[min(n - 1, i + 1)] - V[max(0, i - 1)]).normalized() for i in range(n)]
    # frames carried along the path (no twist)
    up = Vector((1, 0, 0)) if abs(T[0].x) < 0.9 else Vector((0, 1, 0))
    Nn = [(up - T[0] * up.dot(T[0])).normalized()]
    for i in range(1, n):
        q = Nn[-1] - T[i] * Nn[-1].dot(T[i])
        Nn.append(q.normalized())
    Bn = [T[i].cross(Nn[i]) for i in range(n)]
    s = [0.0]
    for i in range(1, n): s.append(s[-1] + (V[i] - V[i - 1]).length)
    for j in range(2 * k):
        rings = []
        for i in range(n):
            a0 = 2 * math.pi * (s[i] / turn) + 2 * math.pi * j / (2 * k)
            angs = [a0 + (2 * math.pi / (2 * k)) * q / (m - 1) for q in range(m)]
            ro = [tuple(V[i] + (Nn[i] * math.cos(a) + Bn[i] * math.sin(a)) * r) for a in angs]
            ri = [tuple(V[i] + (Nn[i] * math.cos(a) + Bn[i] * math.sin(a)) * (r - t)) for a in angs[::-1]]
            rings.append(ro + ri)
        loft(g, pa if j % 2 == 0 else pb, rings, group=lambda i, kk: 'r' if kk < m - 1 else None)
    core = []
    for i in range(n):
        core.append([tuple(V[i] + (Nn[i] * math.cos(2 * math.pi * q / 8) + Bn[i] * math.sin(2 * math.pi * q / 8)) * (r - t * 0.6))
                     for q in range(8)])
    loft(g, pb, core, group=lambda i, kk: 'r')
    if cap: pearl(g, pa, r * 0.985, tuple(V[-1]))


def hook_path(z0, z1, y, hc, hr, step=0.0105, a_end=330):
    """a cane's path at height y from z0 forward to z1, then round a hook down and back (centre hc (z, y), radius hr)"""
    pts = []
    k = max(2, int(abs(z1 - z0) / step))
    for i in range(k + 1): pts.append((0.0, y, z0 + (z1 - z0) * i / k))
    for a in range(98, a_end + 1, 13):
        t = RAD(a)
        pts.append((0.0, hc[1] + hr * math.sin(t), hc[0] + hr * math.cos(t)))
    return pts


def gumdrop(g, piece, x, y, z, r, h, n=12, tilt=0.0):
    """a gumdrop standing on a surface at (x, y, z): a sugared dome on a short slanted wall, its axis tilted `tilt`
       degrees from straight up toward the left"""
    prof = [(-0.0015, 1.0), (0.3, 0.98), (0.55, 0.9), (0.74, 0.74), (0.88, 0.52), (0.96, 0.28), (1.0, 0.06)]
    A = Vector((-math.sin(RAD(tilt)), math.cos(RAD(tilt)), 0.0))
    U = Vector((math.cos(RAD(tilt)), math.sin(RAD(tilt)), 0.0)); W = Vector((0, 0, 1))
    O = Vector((x, y, z))
    rings = [[tuple(O + A * (h * u) + (U * math.cos(2 * math.pi * j / n) + W * math.sin(2 * math.pi * j / n)) * (r * w)) for j in range(n)]
             for u, w in prof]
    loft(g, piece, rings, group=lambda i, k: 'r')


# ------------------------------------------------------------------------------------------------ the hero pieces
def quilt(g, cushion, button, poly, xface, z0, z1, y0, y1, hz, hy, t=0.007, br=0.005):
    """tufted upholstery on both faces of a cushion at |x| = xface: puffy diamonds on a diagonal lattice wherever they
       fit inside poly (side view), a round gold button where their corners meet (gun_sets_cute.quilt, lighter)"""
    cells, j, y = [], 0, y1
    while y >= y0:
        z = z0 + (j % 2) * hz
        while z <= z1:
            if all(inside(poly, cz, cy) for cz, cy in ((z - hz, y), (z + hz, y), (z, y - hy), (z, y + hy))):
                cells.append((z, y))
            z += 2 * hz
        y -= hy
        j += 1
    nodes = set()
    for z, y in cells:
        for cz, cy in ((z - hz, y), (z + hz, y), (z, y - hy), (z, y + hy)):
            nodes.add((round(cz, 5), round(cy, 5)))
    for sx in (-1, 1):
        for z, y in cells:
            lens(g, cushion, diamond(z, y, hz, hy, n=8), side(sx, xface - 0.001), out=t, back=0.0005)
        for cz, cy in nodes:
            pearl(g, button, br, (sx * (xface + br * 0.5), cy, cz), n=5, m=2)
    return cells


def locket(g, node, c, a, b, F, sx, pr, gem, side_stones=False, sink=0.001, back=0.003, pearl_x=0.42):
    """A VELVET: an oval jewel locket set on a flank (|x| = F, side sx): a round gold bezel, a cream velvet bed puffing
       up inside it, a rim of pearls round it, one big table-cut lavender stone held by four gold claws (its small
       table the glow), and (side_stones) two small stones in gold collets either side"""
    gold, bed, pearl, gemp, glow = (node + '__' + s for s in ('ctrim', 'soft', 'pearl', 'gem', 'cglow'))
    bw = max(0.0042, 0.11 * b)
    bt = max(0.0026, 0.06 * b)
    xb = F + bt - sink
    pts, _ = oval_even(c, a - bw, b - bw, 30 if b > 0.04 else 18, sx * xb)
    tloop(g, gold, pts, (1, 0, 0), bw, bt, n=8)
    hb = max(0.0045, 0.12 * b)
    lens(g, bed, ell(c, a - 1.55 * bw, b - 1.55 * bw, n=24 if b > 0.04 else 14), side(sx, F - sink), out=hb + sink, back=back)
    pearl_ring(g, pearl, c, a + pr * 0.45, b + pr * 0.45, sx * (F + pr * pearl_x), pr)
    gc = (sx * (F + hb * 0.85), c[1], c[0])
    ht = gem_stone(g, gemp, glow, gc, (sx, 0, 0), gem, plug=0.34)
    claws(g, gold, gc, (sx, 0, 0), gem, ht, rc=max(0.0024, gem * 0.105))
    if side_stones:
        rs = 0.3 * gem
        for dz in (-1, 1):
            zc = c[0] + dz * (a - 1.55 * bw - rs * 1.6)
            g.ring(gold, rs * 1.32, rs * 0.86, (sx * (F + 0.002), c[1], zc), (sx * (F + hb * 0.9 + 0.002), c[1], zc), sides=10,
                   bev=0.0)
            gem_stone(g, gemp, gemp, (sx * (F + hb * 0.9), c[1], zc), (sx, 0, 0), rs)


def puffy_wing(g, node, root, k, F, sx, H=None, sink=0.001, turn=0.0):
    """B STARLIGHT: a puffy wing lying on a flank (|x| = F, side sx), rooted at root (z, y) and swept back: a rose
       shoulder, three long round white lobes (24, 12 and 2 degrees) each with a soft rose rim, a gold leading edge along
       the top lobe that curls round a white boss with a glowing star at the root"""
    H = H or dict(sh=0.007, lobe=(0.0115, 0.0155, 0.0195), eq=(0.0015, 0.006, 0.0105), rim=0.0042, edge=(0.0065, 0.003),
                  disc=0.0085, star=0.0085, back=0.003)
    z0, y0 = root
    ct, st = math.cos(RAD(turn)), math.sin(RAD(turn))
    def L(u, v): return (z0 + (u * ct - v * st) * k, y0 + (u * st + v * ct) * k)
    rose, white, white2, gold, glow = (node + '__' + s for s in ('bowin', 'soft', 'soft2', 'ctrim', 'cglow'))  # (a deep rose under white: it reads at a grazing angle)
    nn = 18 if k > 0.6 else 14
    lens(g, rose, ell(L(0.050, 0.030), 0.056 * k, 0.037 * k, turn, n=nn), side(sx, F - sink), out=H['sh'] + sink, back=H['back'])
    lobes = [((0.062, -0.006), 0.058, 0.0235, 2), ((0.115, 0.026), 0.068, 0.0245, 12), ((0.165, 0.060), 0.072, 0.0235, 24)]
    LP = 2.5  # (round-ended lobes)
    # a rose backing under the whole wing, following its lobes (white lobes on rose, not on the pearl receiver)
    ells = [(L(0.050, 0.030), 0.056 * k, 0.037 * k, turn)] + [(L(*c), a * k, b * k, rot + turn) for c, a, b, rot in lobes]
    lens(g, rose, polar_union(L(0.016, 0.034), ells, H.get('pad', 0.0062), n=32), side(sx, F - sink),
         out=H.get('bk', 0.004) + sink, back=H['back'])
    for i, (c, a, b, rot) in enumerate(lobes):  # (bottom first: each lobe lies over the one below it)
        eq = F + H['eq'][i]
        ol = ell(L(*c), a * k, b * k, rot + turn, n=nn, p=LP)
        lens(g, white2 if i == 1 else white, ol, side(sx, eq), out=H['lobe'][i] - H['eq'][i], back=H['eq'][i] + H.get('lb', 0.003))  # (a steep back cone, clear of the backing's shallow one)
        rim(g, rose, inset(ol, -H['rim'] * 0.35), side(sx, eq), 0.0, H['rim'], H['rim'] * 1.05, n=8)
    # the gold leading edge: from the curl round the boss, over the shoulder's top, along the top lobe's upper edge
    Bc = L(0.016, 0.034)
    r0, r1 = 0.016 * k / 0.92, 0.026 * k / 0.92
    path = []
    for i in range(13):
        f = i / 12
        ph = RAD(360 - 270 * f)
        rr = r0 + (r1 - r0) * f
        path.append((Bc[0] + rr * math.cos(ph), Bc[1] + rr * math.sin(ph)))
    (c, a, b, rot) = lobes[2]
    cc = L(*c)
    cr, srt = math.cos(RAD(rot + turn)), math.sin(RAD(rot + turn))
    def lob(t, d=0.0):
        ct, st_ = math.cos(RAD(t)), math.sin(RAD(t))
        u, v = (a * k - d) * math.copysign(abs(ct) ** (2.0 / LP), ct), (b * k - d) * math.copysign(abs(st_) ** (2.0 / LP), st_)
        return (cc[0] + u * cr - v * srt, cc[1] + u * srt + v * cr)
    top = path[-1]
    e0 = lob(138, H['edge'][0] * 0.4)
    for q in bez(top, (top[0] + (e0[0] - top[0]) * 0.55, top[1] + 0.006 * k / 0.92), e0, 8)[1:]: path.append(q)
    for t in range(130, 4, -14): path.append(lob(t, H['edge'][1] * 0.6))
    xs = F + H['eq'][2] + 0.003
    pts = [(sx * xs, v, u) for u, v in path]
    m = len(pts)
    radii = [H['edge'][0] * (0.8 + 0.2 * min(1.0, i / 12)) if i <= 12 else
             H['edge'][0] + (H['edge'][1] - H['edge'][0]) * (i - 12) / (m - 13) for i in range(m)]
    tsweep(g, gold, pts, radii, n=6, side=(sx, 0, 0))
    pearl(g, gold, H['edge'][1], pts[-1], n=6, m=3)
    pearl(g, gold, H['edge'][0] * 0.8, pts[0], n=6, m=3)
    lens(g, white, ell(Bc, r0 * 0.98, r0 * 0.98, n=16), side(sx, F + 0.003), out=H['disc'] - 0.003, back=0.004)
    lens(g, glow, soft_star(Bc, r0 * 0.9, r0 * 0.42), side(sx, F + H['disc'] - 0.003), out=H['star'], back=0.003)


def bfly_outlines(c, s, npts=22):
    """C GLASSWING: a butterfly seen face-on with its body upright at c (z, y), s its size: forewings up-front and
       up-back, hindwings with a short tail. returns [(outline, 'fore' | 'hind', sg)]"""
    cz, cy = c
    out = []
    for sg in (-1, 1):
        fw = [(cz, cy + 0.02 * s), (cz + sg * 0.22 * s, cy + 0.62 * s), (cz + sg * 0.60 * s, cy + 0.93 * s),
              (cz + sg * 0.95 * s, cy + 0.83 * s), (cz + sg * 1.0 * s, cy + 0.50 * s), (cz + sg * 0.78 * s, cy + 0.16 * s),
              (cz + sg * 0.42 * s, cy - 0.02 * s)]
        hw = [(cz, cy - 0.04 * s), (cz + sg * 0.45 * s, cy - 0.06 * s), (cz + sg * 0.76 * s, cy - 0.28 * s),
              (cz + sg * 0.74 * s, cy - 0.58 * s), (cz + sg * 0.55 * s, cy - 0.74 * s), (cz + sg * 0.50 * s, cy - 0.98 * s),
              (cz + sg * 0.36 * s, cy - 0.80 * s), (cz + sg * 0.12 * s, cy - 0.50 * s)]
        for poly, kind in ((fw, 'fore'), (hw, 'hind')):
            if sg < 0: poly = poly[::-1]
            out.append((resample(chaikin(poly, 2), npts), kind, sg))
    return out


def glass_bfly(g, node, c, s, F, sx, panes=('glass', 'soft2'), frame='main2', body='cglow', dot='pearl', H=None,
               through=None, sink=0.001, nd=2, npts=22):
    """C GLASSWING: a stained-glass butterfly on a face (|x| = F, side sx): a lavender frame under each wing, a pale
       pane in it (glass forewings, peach hindwings) edged by a raised lavender leading, white dots near the wing tips,
       a glowing crystal body and head. through = w: the frames are one chunky plate through the part (w thick), the
       panes on both its faces"""
    H = H or dict(fr=0.005, pane=0.0105, lead=0.0028, back=0.003)
    fsl, bsl, dsl = node + '__' + frame, node + '__' + body, node + '__' + dot
    wings = bfly_outlines(c, s, npts)
    sides = (-1, 1) if through else (sx,)
    for ol, kind, sg in wings:
        if through:
            g.prism(fsl, ol, through, bev=0.003)
        else:
            lens(g, fsl, ol, side(sx, F - sink), out=H['fr'] + sink, back=H['back'], nd=nd)
    for sxx in sides:
        F0 = through / 2 if through else F
        for ol, kind, sg in wings:
            pane = shrink(ol, 0.74)
            psl = node + '__' + (panes[0] if kind == 'fore' else panes[1])
            lens(g, psl, pane, side(sxx, F0 + H['fr'] - 0.002), out=H['pane'] - H['fr'] + 0.002, back=0.0005, e=0.0018, nd=nd)
            # (the leading stands a little over the pane round its edge)
            rim(g, fsl, resample(shrink(ol, 0.78), 12), side(sxx, F0), H['pane'] - H['lead'] * 0.9, H['lead'], H['lead'] * 1.6, n=5)
            if kind == 'fore':
                tip = (c[0] + sg * 0.70 * s, c[1] + 0.64 * s)
                pearl(g, dsl, max(0.004, 0.075 * s), (sxx * (F0 + H['pane'] - 0.0015), tip[1], tip[0]), n=6, m=3)
        # the body: a glowing crystal lying upright on the face, the head a round bead above it
        rb = max(0.0055, 0.1 * s)
        xb = sxx * (F0 + H['fr'] + rb * 0.25)
        crystal(g, bsl, (xb, c[1] - 0.62 * s, c[0]), (xb, c[1] + 0.48 * s, c[0]), rb, tipk=0.12, tipr=0.3)
        g.cyl(bsl, rb * 0.94, (xb, c[1] - 0.62 * s, c[0]), (xb, c[1] - 0.78 * s, c[0]), sides=6, r2=rb * 0.2, bev=0.0006, smooth=False)
        pearl(g, bsl, rb * 1.05, (xb, c[1] + 0.6 * s, c[0]))


# ================================================================================================= A  VELVET
def ar_cute_a():
    """VELVET rifle: the live rifle in rose and light rose, gold trims, a berry grip; the hero an oval jewel locket on
       the left receiver flank (gold bezel, velvet bed, pearl rim, a big lavender stone in four claws, two side stones; a
       small one on the right ahead of the port); a fat fur muff round the stock tube behind the rear sight; a big
       pom-pom on a gold bead chain from the handguard's front left; the stock a tufted rose cushion with gold buttons
       and a gold-capped berry tassel at its heel; a ring of pearls round the muzzle device, a row down each magazine
       face"""
    g = new_gun('A', 'ar', 'ar_cute_a')
    rebase(g, 'ar', ar_tag, dict(AR_PAINT, grip='deep', tguard='ctrim', stock=None, cheek=None, pad=None))
    F = 0.032
    # HERO: the locket, 0.17 x 0.12 m (about a quarter of the gun's height), ahead of the hand, under the sight line
    locket(g, 'locket_wzN', (-0.088, 0.0), 0.084, 0.062, F, -1, pr=0.0085, gem=0.036, side_stones=True)
    locket(g, 'locket_wzN', (-0.150, 0.010), 0.034, 0.028, F, 1, pr=0.006, gem=0.014)
    # the soft object at the joint: a fat fur muff round the stock tube (its top under the rear sight's stem)
    fur_ring(g, 'muff_wzN__fur', 'muff_wzN__fur2', 0.283, 0.03, 0.047, 0.031, n=9, rows=2, dz=0.021, flat=0.62)
    # the charm: a gold eyelet on the handguard's lower left, a bead chain, a big pom-pom (ahead of the off hand)
    g.cyl('charm_wzN__ctrim', 0.0062, (-0.030, -0.036, -0.448), (-0.0425, -0.036, -0.448), sides=10, bev=0.0012)
    g.ring('charm_wzN__ctrim', 0.0088, 0.0046, (-0.040, -0.0505, -0.4512), (-0.040, -0.0505, -0.4448), sides=12, bev=0.001)
    bead_drop(g, 'charm_wzN__ctrim', (-0.040, -0.064, -0.448), -0.099, r=0.0046)
    g.cyl('charm_wzN__ctrim', 0.0055, (-0.040, -0.100, -0.448), (-0.040, -0.111, -0.448), r2=0.012, sides=12, bev=0.0012)
    pompom(g, 'charm_wzN__fur', 'charm_wzN__fur2', (-0.040, -0.152, -0.448), 0.054, n=20, k=1.0)
    # the stock: a tufted velvet cushion over the live stock (puffed past its edges, its top kept at the cheek rest's)
    cush = fillet_poly([(0.289, -0.016), (0.291, 0.096), (0.480, 0.106), (0.500, -0.192), (0.396, -0.192), (0.324, -0.048)],
                       0.021, seg=7)
    slab(g, 'stock_wzA__velvet2', cush, MID, 0.078, 0.014, n_arc=2, h0=-0.039)
    quilt(g, 'stock_wzA__velvet', 'stock_wzN__ctrim', inset(cush, 0.010), 0.039, 0.312, 0.492, -0.194, 0.096, 0.0255, 0.032,
          t=0.0068, br=0.0052)
    tassel(g, 'stock_wzN__ctrim', 'stock_wzN__deep', (0.0, -0.184, 0.480), 0.062, 0.009, 0.018)
    # the ends: twelve pearls round the muzzle device (between its ports), five down each magazine face (node "mag")
    for i in range(12):
        a = 2 * math.pi * (i + 0.5) / 12
        pearl(g, 'barrel_wzN__pearl', 0.0075, (0.0318 * math.cos(a), 0.015 + 0.0318 * math.sin(a), -0.680), n=6, m=3)
    for t in (0.3, 0.45, 0.6, 0.75, 0.9):
        fz, fy = bez_mag(t, True); bz, by = bez_mag(t, False)
        z, y = fz * 0.55 + bz * 0.45, fy * 0.55 + by * 0.45
        for sx in (-1, 1): pearl(g, 'mag_wzN__pearl', 0.0115, (sx * 0.0278, y, z), n=7, m=3)
    fuse_soft(g, 'muff_wzN', fur_ring_fields(0.283, 0.03, 0.047, 0.031, n=9, rows=2, dz=0.021, flat=0.62), 0.0018, 0.0011, 1400)
    fuse_soft(g, 'charm_wzN', pompom_fields((-0.040, -0.152, -0.448), 0.054, n=20, k=1.0), 0.0015, 0.0008, 1100)
    return g


def pistol_cute_a():
    """VELVET Plan B: a rose slide, light rose frame, berry grip panels quilted with gold buttons; the hero the locket
       on the slide's left (it moves with the slide; a small one on the right ahead of the port); a pom-pom on a short
       bead chain from the grip's heel; a row of pearls along each side of the dust cover. (The slide stop is left off:
       the locket rides over its place when the slide locks back)"""
    g = new_gun('A', 'pistol', 'pistol_cute_a')
    rebase(g, 'pistol', pb_tag, dict(PB_PAINT, panels='deep', screws=None, stop=None))
    F = 0.022
    # (its back side stops 0.5 mm off the frame's flank: the frame stays put while the slide runs over it)
    locket(g, 'slide_wzN', (-0.105, 0.010), 0.050, 0.036, F, -1, pr=0.0055, gem=0.019, back=0.0005, pearl_x=0.75)
    locket(g, 'slide_wzN', (-0.165, 0.012), 0.022, 0.020, F, 1, pr=0.0042, gem=0.0095, back=0.0005, pearl_x=0.75)
    # the grip panels quilted: puffy berry diamonds in the grip's rake, gold buttons where they meet
    rk = lambda u, v: (0.0325 + u * math.cos(PB_RAKE) + v * math.sin(PB_RAKE), -0.0745 + v * math.cos(PB_RAKE) - u * math.sin(PB_RAKE))
    hu, hv = 0.0108, 0.018
    for sx in (-1, 1):
        for u in (-0.0108, 0.0108):
            for v in (-0.036, 0.0, 0.036):
                out = [rk(u + hu * math.copysign(abs(math.cos(a)) ** 1.5, math.cos(a)), v + hv * math.copysign(abs(math.sin(a)) ** 1.5, math.sin(a)))
                       for a in (2 * math.pi * (j + 0.5) / 12 for j in range(12))]
                lens(g, 'grip_wzA__deep', out, side(sx, 0.0255), out=0.0065, back=0.0005)
        for v in (-0.054, -0.018, 0.018, 0.054):
            z, y = rk(0.0, v)
            pearl(g, 'grip_wzN__ctrim', 0.0036, (sx * 0.0272, y, z), n=6, m=3)
    # the soft object: a pom-pom on a bead chain from a gold loop at the grip's heel
    g.ring('grip_wzN__ctrim', 0.0078, 0.0042, (-0.003, -0.1295, 0.0825), (0.003, -0.1295, 0.0825), sides=12, bev=0.001)
    chain(g, 'grip_wzN__ctrim', (0.0, -0.1405, 0.086), (0.0, -0.160, 0.092), 0.004)
    g.cyl('grip_wzN__ctrim', 0.0042, (0.0, -0.1625, 0.0925), (0.0, -0.1705, 0.0935), r2=0.0085, sides=12, bev=0.001)
    pompom(g, 'grip_wzN__fur', 'grip_wzN__fur2', (0.0, -0.1705 - 0.8 * 0.035 + 0.003, 0.0945), 0.035, n=18)
    # a row of pearls along the dust cover's right side, behind where the small locket reaches when the slide locks
    # back (on the left the big locket hangs over the dust cover)
    for sx in (-1, 1):
        for z in (-0.201, -0.190, -0.179, -0.168):
            pearl(g, 'body_wzN__pearl', 0.0055, (sx * 0.0125, -0.0222, z), n=6, m=3)
    fuse_soft(g, 'grip_wzN', pompom_fields((0.0, -0.1705 - 0.8 * 0.035 + 0.003, 0.0945), 0.035, n=18), 0.0011, 0.0006, 900)
    return g


# ================================================================================================= B  STARLIGHT
def ar_cute_b():
    """STARLIGHT rifle: a pearl receiver and stock, a rose cover and handguard with gold grooves; the hero a puffy wing on
       each receiver flank rooted where the handguard meets the receiver (three white lobes with rose rims, a rose
       shoulder, a gold leading edge curling round a glowing star; the right one smaller, clear of the port); a gold
       five-point star collar round the muzzle device (one point down); a rose bow on a band under the handguard's front
       with two long V-cut tails; a big gold star with a rose fill and glowing core through the stock end; a rose ribbon
       round the stock tube with a bow each side and two tails down behind the grip; a big gold star through the
       magazine, its points past the front edge"""
    g = new_gun('B', 'ar', 'ar_cute_b')
    rebase(g, 'ar', ar_tag, dict(AR_PAINT, stock='main', tube='cdark', cheek='main2', pad='main2', gastube='ctrim'))
    F = 0.032
    puffy_wing(g, 'wing_wzN', (-0.188, 0.008), 0.95, F, -1, turn=-3.0,
               H=dict(sh=0.007, lobe=(0.0115, 0.0155, 0.0195), eq=(0.0015, 0.006, 0.0105), rim=0.0052, edge=(0.0065, 0.003),
                      disc=0.0085, star=0.0085, back=0.003, pad=0.012, bk=0.0045))
    puffy_wing(g, 'wing_wzN', (-0.188, 0.016), 0.45, F, 1, H=dict(sh=0.0078, lobe=(0.0125, 0.0165, 0.0205), eq=(0.0025, 0.0065, 0.0105),
               rim=0.0024, edge=(0.0045, 0.0024), disc=0.0075, star=0.0065, back=0.003, pad=0.004, bk=0.0065))
    # the star collar round the muzzle device, between its two ports (no point up into the sights)
    outer = soft_star((0.0, 0.015), 0.052, 0.024, ang=-90.0, it=1)
    inner = []
    for x, y in outer:
        a = math.atan2(y - 0.015, x)
        inner.append((0.0215 * math.cos(a), 0.015 + 0.0215 * math.sin(a)))
    SG.xframe(g, 'muz_wzN__ctrim', outer, inner, -0.6875, -0.6725, bev=0.0012)
    # under the front: a rose band round the handguard and a bow tied on it, two long tails (ahead of the off hand)
    SG.xsolid(g, 'ribbon_wzN__main2', [(-0.0415, -0.0465), (0.0415, -0.0465), (0.0415, 0.020), (-0.0415, 0.020)], -0.477, -0.461,
              bev=0.0015)
    bow(g, 'ribbon_wzN', MID, (-0.469, -0.0565), 0.052, 0.017, 'main2', 'bowin', 'ctrim', angs=(192.0, -12.0), W=0.74,
        tails=[bez((-0.473, -0.061), (-0.500, -0.130), (-0.478, -0.208), 7), bez((-0.465, -0.061), (-0.436, -0.112), (-0.410, -0.180), 7)],
        tail_w=(0.62, 0.78), tail_t=0.006, centred=True)
    # the stock end: a big gold star through the stock, its points past the butt and below it
    star_badge(g, 'sstar_wzN', (0.428, -0.040), 0.122, 0.056, 0.074, 'ctrim', 'main2', 'cglow')
    # the wrist: a rose ribbon round the stock tube, a bow each side, two tails down the gap behind the grip
    g.ring('wrist_wzN__main2', 0.0292, 0.020, (0, 0.03, 0.252), (0, 0.03, 0.272), sides=12, bev=0.002)
    for sx in (-1, 1):
        bow(g, 'wrist_wzN', side(sx, 0.0285), (0.262, 0.030), 0.037, 0.012, 'main2', 'bowin', 'ctrim', angs=(152.0, 28.0), W=0.74)
    for path in (bez((0.257, 0.004), (0.234, -0.062), (0.247, -0.138), 7), bez((0.267, 0.004), (0.297, -0.050), (0.298, -0.114), 7)):
        slab(g, 'wrist_wzN__main2', tail_poly(path, 0.019, 0.024, 0.014), MID, 0.006, 0.002, h0=-0.003)
    # the magazine: a big gold star through it, its front points past the front edge (node "mag")
    star_badge(g, 'mag_wzN', (-0.182, -0.180), 0.058, 0.027, 0.066, 'ctrim', 'main2', None)
    return g


def pistol_cute_b():
    """STARLIGHT Plan B: a pearl slide, rose frame and grip; the hero a puffy wing on each side of the slide rooted at
       its front and swept back under its top line (it moves with the slide); a gold star collar round the slide's nose
       (one point down, the upper points under the slide's top); a rose bow on the trigger guard's front facing forward,
       two tails hanging to y -0.16; a big gold star with a glowing core through the grip, turned with its rake"""
    g = new_gun('B', 'pistol', 'pistol_cute_b')
    rebase(g, 'pistol', pb_tag, dict(PB_PAINT, slide='main', frame='main2', tguard='main2', panels='main2', screws=None,
                                     grip='cdark', stop=None))
    short_stop(g, 'ctrim')
    F = 0.022
    Hp = dict(sh=0.0042, lobe=(0.0068, 0.0094, 0.012), eq=(0.0012, 0.0038, 0.0064), rim=0.0027, edge=(0.0036, 0.0017),
              disc=0.0068, star=0.0042, back=0.001, pad=0.0062, bk=0.0025, lb=0.0018)
    for sx in (-1, 1):
        puffy_wing(g, 'slide_wzN', (-0.226, -0.012), 0.56, F, sx, H=Hp)
    # the star collar round the nose (behind the bushing: the bore and the barrel's end stay clear in front of it)
    g.xprism('slide_wzN__ctrim', bite(soft_star((0.0, 0.002), 0.046, 0.021, ang=-90.0, it=1), (0.0, 0.030), 0.0108), -0.2565, -0.2475,
             bev=0.0016)
    face = (Vector((0.0, 0.0, -0.2560)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, -1)))
    lens(g, 'slide_wzN__main2', bite(soft_star((0.0, 0.002), 0.030, 0.0143, ang=-90.0), (0.0, 0.030), 0.0142), face, out=0.0032,
         back=0.001, e=0.0012)
    # a band round the trigger guard's front and a bow on it facing forward, two tails hanging down
    g.yprism('body_wzN__main2', [(-0.0155, -0.1128), (0.0155, -0.1128), (0.0155, -0.0938), (-0.0155, -0.0938)], -0.0535, -0.0395,
             bev=0.0015)
    fr = (Vector((0.0, 0.0, -0.1145)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, -1)))
    bow(g, 'ribbon_wzN', fr, (0.0, -0.0465), 0.040, 0.0115, 'main2', 'bowin', 'ctrim', angs=(16.0, 164.0), W=0.74, centred=True)
    # (the tails hang in the side plane, one forward, one back under the guard's corner: the outline shows them)
    for path in (bez((-0.113, -0.052), (-0.136, -0.105), (-0.119, -0.158), 10), bez((-0.107, -0.054), (-0.088, -0.096), (-0.066, -0.140), 10)):
        slab(g, 'ribbon_wzN__main2', tail_poly(path, 0.0115, 0.0145, 0.0085), MID, 0.0045, 0.0016, h0=-0.00225)
    # the grip: a big gold star through it, turned with the grip's rake, a rose fill and a glowing core on each side
    star_badge(g, 'gstar_wzN', (0.046, -0.080), 0.044, 0.020, 0.058, 'ctrim', 'main2', 'cglow', ang=125.0, h=(0.0032, 0.0048),
               bev=0.0025)
    return g


# ================================================================================================= C  GLASSWING
def ar_cute_c():
    """GLASSWING rifle: a pearl receiver, lilac cover and handguard, a mint stock; the hero a stained-glass butterfly
       landed on the left receiver flank (lavender leading, pale glass forewings, peach hindwings, white tip dots, a
       glowing crystal body); a cluster of seven hex crystals growing down, forward and out to the left from a pale
       lavender collar at the handguard's front (the longest and one more glowing); five crystals swept back round the
       muzzle device (none up); a big butterfly through the stock, its wings past the butt and below; a crystal set
       in the right flank under the port; a swept wing-tip fin at the magazine base"""
    g = new_gun('C', 'ar', 'ar_cute_c')
    rebase(g, 'ar', ar_tag, dict(AR_PAINT, stock='soft', cheek='soft', pad='soft', grooves='ctrim', magplate='main2', tguard='cdark', charge='main2',
                                 rivet='main2', ribs='main2', gastube='ctrim'))
    F = 0.032
    glass_bfly(g, 'bfly_wzN', (-0.090, 0.012), 0.092, F, -1)
    # the crystal cluster at the handguard's front: a pale lavender collar, a rocky bed under the left front, 7 crystals
    SG.xsolid(g, 'cluster_wzN__lav', [(-0.045, -0.050), (0.045, -0.050), (0.045, 0.0345), (-0.045, 0.0345)], -0.486, -0.456,
              bev=0.003)
    ellip(g, 'cluster_wzN__lav', (-0.016, -0.036, -0.452), [((1, 0, 0), 0.030), ((0, 0, 1), 0.036), ((0, 1, 0), 0.016)], n=10, m=5)
    for a, b, r, sl in [((-0.022, -0.036, -0.452), (-0.066, -0.196, -0.484), 0.027, 'cglow'),
                        ((0.010, -0.040, -0.462), (0.034, -0.150, -0.515), 0.019, 'ctrim'),
                        ((-0.030, -0.030, -0.420), (-0.092, -0.122, -0.426), 0.019, 'glass'),
                        ((-0.034, -0.006, -0.466), (-0.100, -0.060, -0.508), 0.016, 'cglow'),
                        ((-0.002, -0.042, -0.424), (0.004, -0.112, -0.402), 0.014, 'glass'),
                        ((0.026, -0.030, -0.440), (0.080, -0.098, -0.458), 0.015, 'ctrim'),
                        ((-0.012, -0.040, -0.484), (-0.020, -0.105, -0.540), 0.012, 'glass')]:
        crystal(g, 'cluster_wzN__' + sl, a, b, r)
    # the muzzle: five crystals swept back round the device, clear of its ports, none up
    for i, ang in enumerate((200, 235, 270, 305, 340)):
        c, s = math.cos(RAD(ang)), math.sin(RAD(ang))
        crystal(g, 'muz_wzN__' + ('ctrim' if i % 2 else 'glass'), (0.019 * c, 0.015 + 0.019 * s, -0.681), (0.070 * c, 0.015 + 0.070 * s, -0.630), 0.0106)
    # the stock: a big stained-glass butterfly through it, its wings past the butt and below
    glass_bfly(g, 'sbfly_wzN', (0.394, -0.027), 0.132, 0.0, 1, through=0.074,
               H=dict(fr=0.0, pane=0.0055, lead=0.003, back=0.003))
    # a crystal set in the right flank, under the port
    crystal(g, 'gem_wzN__cglow', (0.030, -0.040, 0.050), (0.037, 0.004, 0.050), 0.0095, tipk=0.35)
    # the magazine base: a swept wing-tip fin pointing back (node "mag")
    fin = loop_uv((-0.072, -0.357), 152.0, 0.070, 0.036, n=20, pinch=0.72)
    lens(g, 'mag_wzN__main2', fin, MID, out=0.0085, back=0.0085, e=0.003, back_full=True)  # (a soft lens: its point stays clean)
    for sx in (-1, 1):
        lens(g, 'mag_wzN__glass', shrink(fin, 0.6), side(sx, 0.006), out=0.0068, back=0.002, e=0.0018)
    return g


def pistol_cute_c():
    """GLASSWING Plan B: a pearl slide, lilac frame, mint grip panels; the hero a stained-glass butterfly on each side
       of the slide ahead of the port (it moves with the slide), its lower wings over the frame's flank; four hex
       crystals growing from a lavender bed under the dust cover, the biggest glowing, one out to the left; a swept
       wing-tip fin at the magazine base"""
    g = new_gun('C', 'pistol', 'pistol_cute_c')
    rebase(g, 'pistol', pb_tag, dict(PB_PAINT, panels='soft', screws='main2', stop=None, grooves='main2',
                                     hammer='main2', magbase='main2', trigger='main2'))
    short_stop(g, 'main2')
    Hp = dict(fr=0.003, pane=0.0058, lead=0.0016, back=0.0008)
    for sx in (-1, 1):
        glass_bfly(g, 'slide_wzN', (-0.156, -0.002), 0.055, 0.022, sx, H=Hp, nd=2, npts=16)
    # the crystals under the dust cover, on a lavender bed (its top inside the frame: the slide's nose passes over it)
    ellip(g, 'cluster_wzN__main2', (0.0, -0.028, -0.176), [((1, 0, 0), 0.0135), ((0, 0, 1), 0.021), ((0, 1, 0), 0.0115)], n=10, m=5)
    for a, b, r, sl in [((0.0, -0.030, -0.184), (-0.004, -0.098, -0.216), 0.013, 'cglow'),
                        ((0.008, -0.032, -0.166), (0.024, -0.080, -0.178), 0.009, 'glass'),
                        ((-0.010, -0.030, -0.172), (-0.050, -0.068, -0.186), 0.0095, 'glass'),
                        ((-0.004, -0.032, -0.190), (-0.020, -0.072, -0.238), 0.008, 'glass')]:
        crystal(g, 'cluster_wzN__' + sl, a, b, r)
    # the magazine base: a swept wing-tip fin (node "mag")
    fin = loop_uv((0.109, -0.173), 152.0, 0.054, 0.027, n=18, pinch=0.72)
    lens(g, 'mag_wzN__main2', fin, MID, out=0.0062, back=0.0062, e=0.0022, back_full=True)
    for sx in (-1, 1):
        lens(g, 'mag_wzN__glass', shrink(fin, 0.6), side(sx, 0.0045), out=0.0046, back=0.0015, e=0.0012)
    return g


# ================================================================================================= D  SWEET SHOP
def ar_cute_d():
    """SWEET SHOP rifle: a cream receiver and stock, strawberry cover and handguard (raised cream stripes round it), a
       mint magazine with a strawberry band, a cocoa grip; the hero a strawberry ribbon band round the receiver under the
       rail and one big puffy bow tied on the left flank (loops with darker folds, a glowing round sweet for the knot,
       two V-cut tails); a candy cane under the barrel hooked down at the muzzle, held by a cream clamp at the sight
       block; three glowing gumdrops along the handguard's top; the stock end the sweet's wrapper twist (a strawberry
       cinch and a pleated fan past the butt with cream icing lines)"""
    g = new_gun('D', 'ar', 'ar_cute_d')
    rebase(g, 'ar', ar_tag, dict(AR_PAINT, grooves=None, mag='soft', magrib='soft', magplate='ctrim', grip='soft2',
                                 tguard='soft2', stock='main', tube='soft', cheek='soft', pad=None, gastube='ctrim',
                                 ribs='main', rivet='main', charge='main'))
    # raised cream stripes round the handguard (clipped to its two parts, 4.5 mm proud)
    lower = inset([(-0.48, -0.042), (-0.215, -0.042), (-0.205, -0.03), (-0.205, 0.03), (-0.48, 0.03), (-0.49, 0.018), (-0.49, -0.03)], -0.0045)
    upper = inset([(-0.46, 0.03), (-0.215, 0.03), (-0.215, 0.07), (-0.44, 0.07), (-0.46, 0.058)], -0.0045)
    for zt in (-0.462, -0.392, -0.322, -0.252):
        par = [(zt - 0.034, -0.06), (zt - 0.018, -0.06), (zt + 0.016, 0.09), (zt, 0.09)]
        lo = clip(par, lower)
        if len(lo) >= 3: g.prism('stripe_wzN__ctrim', lo, 0.083, bev=0.002)
    # three gumdrop lights on the handguard's top, between the stripes (a later idea: one lights per kill)
    for z in (-0.427, -0.357, -0.287):
        gumdrop(g, 'gum_wzN__gumglow', -0.0205, 0.0655, z, 0.0118, 0.0138, tilt=38.0)
    # HERO: a strawberry band round the receiver and cover (under the rail), a big bow tied on the left flank
    band = [(-0.0365, -0.0665), (0.0365, -0.0665), (0.0365, 0.0565), (0.0335, 0.0605), (0.0275, 0.0925), (-0.0275, 0.0925),
            (-0.0335, 0.0605), (-0.0365, 0.0565)]
    SG.xsolid(g, 'band_wzN__main2', band, -0.112, -0.082, bev=0.002)
    bow(g, 'bow_wzN', side(-1, 0.033), (-0.097, 0.012), 0.098, 0.016, 'main2', 'bowin', 'main2', angs=(158.0, 22.0),
        L=1.1, W=0.8, tails=[bez((-0.103, 0.0), (-0.122, -0.055), (-0.140, -0.115), 12), bez((-0.091, 0.0), (-0.072, -0.055), (-0.056, -0.112), 12)],
        tail_w=(0.30, 0.36), tail_t=0.0055, sweet='cglow', tail_h0=0.0025)
    # the candy cane under the barrel: from the handguard's front (a cream collar where it goes in), hooked down and
    # back at the muzzle, held by a cream clamp at the sight block
    CY = -0.031
    cane(g, 'cane_wzN__ctrim', 'cane_wzN__main2', hook_path(-0.468, -0.705, CY, (-0.705, CY - 0.032), 0.032), 0.0135,
         k=2, turn=0.13)
    g.ring('cane_wzN__ctrim', 0.0178, 0.0115, (0, CY, -0.497), (0, CY, -0.486), sides=16, bev=0.0015)
    g.ring('cane_wzN__ctrim', 0.0182, 0.0115, (0, CY, -0.527), (0, CY, -0.513), sides=16, bev=0.0015)
    g.box('cane_wzN__ctrim', (-0.0075, 0.0075), (CY + 0.012, -0.004), (-0.526, -0.514), bev=0.0015)
    # the stock end: the wrapper's twist, a strawberry cinch and a pleated fan past the butt with cream icing lines
    SG.xsolid(g, 'wrap_wzN__main2', [(-0.0315, -0.1545), (0.0315, -0.1545), (0.0315, 0.0845), (-0.0315, 0.0845)], 0.432, 0.452, bev=0.003)
    flare(g, 'wrap_wzN__main2', (0.0, -0.035, 0.447), (0.0, -0.056, 0.532), (1, 0, 0), (0, 1, 0), 0.0255, 0.1145, 0.056, 0.160,
          k=8, depth=0.3, ease=0.6, zig=0.016, crest='wrap_wzN__ctrim', crest_r=0.0046)
    # the magazine: a strawberry band round it (node "mag")
    y0, y1 = -0.148, -0.180
    zf0, zf1, zb0, zb1 = mag_z_at(y0, True), mag_z_at(y1, True), mag_z_at(y0, False), mag_z_at(y1, False)
    g.prism('mag_wzN__main2', [(zf0 - 0.0045, y0), (zb0 + 0.0045, y0), (zb1 + 0.0045, y1), (zf1 - 0.0045, y1)], 0.063, bev=0.002)
    return g


def pistol_cute_d():
    """SWEET SHOP Plan B: a cream slide and frame, mint grip panels; raised strawberry stripes leaning back across the
       slide; the hero a strawberry ribbon band round the slide ahead of the port and a big bow on its left with a
       glowing round sweet for the knot (both ride on the slide); a candy cane under the dust cover hooked down at the
       front; the magazine base a pleated strawberry wrapper fan with cream icing lines (node "mag")"""
    g = new_gun('D', 'pistol', 'pistol_cute_d')
    rebase(g, 'pistol', pb_tag, dict(PB_PAINT, slide='main', frame='main', tguard='main', panels='soft', screws='main2',
                                     stop=None, grooves='main2', trigger='main2',
                                     hammer='main2', magbase='main2'))
    short_stop(g, 'main2')
    # the slide's stripes (clipped to the slide's outline, 2.5 mm proud) and the band
    nose = [(-0.2505, -0.0195), (-0.19, -0.0195), (-0.19, 0.042), (-0.2505, 0.042)]
    main = [(-0.19, 0.0015), (0.0565, 0.0015), (0.0565, 0.042), (-0.19, 0.042)]
    for z0 in (-0.246, -0.209):
        par = [(z0, -0.03), (z0 + 0.0095, -0.03), (z0 + 0.0095 + 0.022, 0.06), (z0 + 0.022, 0.06)]
        for box in (nose, main):
            pc = clip(par, box)
            if len(pc) >= 3 and abs(area(pc)) > 2e-6: g.prism('slide_wzN__main2', pc, 0.049, bev=0.0018)
    ring_xy = fillet_poly([(-0.022, 0.0105), (0.022, 0.0105), (0.022, 0.052), (-0.022, 0.052)], 0.0055, seg=4)
    tloop(g, 'slide_wzN__main2', [(x, y, -0.110) for x, y in ring_xy], (0, 0, 1), 0.0028, 0.0085, n=6)
    bow(g, 'slide_wzN', side(-1, 0.0235), (-0.110, 0.014), 0.040, 0.0085, 'main2', 'bowin', 'main2', angs=(160.0, 20.0),
        L=1.15, W=0.8, tails=[bez((-0.113, 0.006), (-0.119, -0.007), (-0.126, -0.021), 8), bez((-0.107, 0.006), (-0.101, -0.007), (-0.096, -0.020), 8)],
        tail_w=(0.30, 0.36), tail_t=0.0032, sweet='cglow', tail_h0=0.0015)
    # the candy cane under the dust cover, from the trigger guard's front, hooked down at the front; a clamp up into
    # the frame
    cane(g, 'cane_wzN__ctrim', 'cane_wzN__main2', hook_path(-0.1165, -0.212, -0.043, (-0.212, -0.066), 0.023, step=0.005),
         0.0085, k=2, turn=0.085, t=0.0016)
    pearl(g, 'cane_wzN__ctrim', 0.0085 * 0.985, (0.0, -0.043, -0.1165))
    g.ring('cane_wzN__ctrim', 0.0112, 0.0072, (0, -0.043, -0.171), (0, -0.043, -0.161), sides=14, bev=0.001)
    g.box('cane_wzN__ctrim', (-0.0055, 0.0055), (-0.034, -0.0165), (-0.170, -0.162), bev=0.0012)
    # the magazine base: a pleated wrapper fan flaring down the grip's rake (node "mag")
    dn = Vector((0.0, -math.cos(PB_RAKE), -math.sin(PB_RAKE)))   # down the grip (the way the magazine drops)
    U = Vector((0.0, -math.sin(PB_RAKE), math.cos(PB_RAKE)))     # across the grip, front to back
    c0 = Vector((0.0, -0.1445, 0.0545)) + dn * 0.004              # inside the magazine's base plate
    flare(g, 'mag_wzN__main2', tuple(c0), tuple(c0 + dn * 0.042), tuple(U), (1, 0, 0), 0.031, 0.0225, 0.052, 0.027,
          k=7, depth=0.2, zig=0.006, crest='mag_wzN__ctrim', crest_r=0.0031, crest_on='V')
    return g


SKINS = {'ar@ar_cute_a': ar_cute_a, 'pistol@pistol_cute_a': pistol_cute_a,
         'ar@ar_cute_b': ar_cute_b, 'pistol@pistol_cute_b': pistol_cute_b,
         'ar@ar_cute_c': ar_cute_c, 'pistol@pistol_cute_c': pistol_cute_c,
         'ar@ar_cute_d': ar_cute_d, 'pistol@pistol_cute_d': pistol_cute_d}
