# JANKFIRE Battle Island: THE ROCKS, a kit of stylised anime coastline rock (shared/battleisland.js RK + rockPlan():
# every piece's numbers are read from there with node, so the models can't drift from the boxes). Real-reference shapes
# (sea cliffs, sea stacks, a boulder field, a wave-cut shelf), made clean: chunky faceted slabs in stacked strata, warm
# grey-tan, lit tops lighter and shadows cooler (painted into the vertex colours with the baked AO), a dark wet band at
# the waterline, moss and grass on the top ledges. One shared material and atlas (a strata band that tiles, a moss cell,
# a sunlit-top cell): every piece is instanced (propfield.js), lod0 for near, a few-dozen-triangle lod1 for the blimp.
#   p_bi_boulder_s/m/l  boulders: two crossed strata layers each (L: two layers and a mossy top)
#   p_bi_ledge          a flat wave-cut shelf at the waterline: climb out of the sea onto it
#   p_bi_stack_a        a tall sea stack: a wave-cut notch at the water, four layers stepping in, a mossy top
#   p_bi_stack_b        a squat stack, its top layer stepped off to one side
#   p_bi_cliff_a/b      cliff faces: a skin of strata ledges over the ground's sheer face (look only), a notch at the foot
#   p_bi_cliff_c        a buttress between them: ribbed, standing out a little more
# Colliding pieces are built round their boxes (RK.col, a little bigger: the boxes never poke out, checked); meta.box is
# their extent (RK.ext), which is what each copy is fitted onto. +z is the front (the sea side) in the game's frame.
# run: blender52 -b --python tools/blender/make_birocks.py -- [--only=boulder_s,cliff_a] [--qa] [--no-sheet]
#      [--no-export] [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas
from lib import *
from lib import _link
import lib
import bikit as BK

V3 = Vector
TAU = 2 * math.pi
ONLY = MK.ONLY
RK = BK.jsdata('shared/battleisland.js', 'm.RK')
PROPS = []
def prop(fid):
    def reg(fn): PROPS.append((fid, fn)); return fn
    return reg


# ------------------------------------------------------------ the atlas: one for the whole kit (128 x 256)
UV_H = 6.0  # metres of height the strata band spans
UV_W = 4.0  # metres along per repeat of it


def paint_strata(px, seed):
    """horizontal layers of warm grey-tan, each its own tone with soft variation, a lit lip on top and a dark seam
    under it, a faint bedding line in the thick ones, the odd vertical joint. tiles along u"""
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    pal = [0xcbb693, 0xb5a083, 0xd8c6a2, 0xa8988a, 0xc2b398, 0xe0cfab, 0xae9878, 0xbdb3a6, 0xc9ae8a]
    y, last = 0, -1
    while y < h:
        t = min(int(r.integers(10, 38)), h - y)
        if h - y - t < 8: t = h - y
        c = int(r.integers(len(pal)))
        while c == last: c = int(r.integers(len(pal)))
        last = c
        b = px[y:y + t]; b[:] = hexrgb(pal[c])
        b *= (0.93 + 0.14 * MK.tnoise(w, t, 3, 1 + t // 14, r))[:, :, None]
        if t > 18 and r.random() < 0.6: b[int(t * (0.4 + 0.2 * r.random()))] *= 0.93
        b[0] = b[0] * 0.5 + hexrgb(0xf4e8cc) * 0.5  # the lit lip
        b[1] = b[1] * 0.8 + hexrgb(0xf4e8cc) * 0.2
        b[-1] *= 0.58; b[-2] *= 0.84  # the seam under it
        if r.random() < 0.45:  # a joint: a vertical crack through the layer
            x = int(r.integers(0, w)); b[2:t - 1, x] *= 0.72
        y += t


def paint_moss(px, seed):
    """clean anime moss and grass: a fresh green with darker clumps and light flecks, no noise"""
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    px[:] = hexrgb(0x74c04a)
    n = MK.tnoise(w, h, 4, 4, r); MK.mix(px, 0x4f9a36, np.clip((n - 0.55) * 4, 0, 1) * 0.8)
    n2 = MK.tnoise(w, h, 8, 8, r); MK.mix(px, 0xa8e06e, np.clip((n2 - 0.7) * 5, 0, 1) * 0.7)


def paint_top(px, seed):
    """a sunlit rock top: pale warm stone, a few lichen spots"""
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    px[:] = hexrgb(0xd8c8aa); px *= (0.94 + 0.12 * MK.tnoise(w, h, 4, 4, r))[:, :, None]
    for _ in range(14):
        cx, cy, rr = int(r.integers(0, w)), int(r.integers(0, h)), int(r.integers(1, 4))
        yy, xx = np.ogrid[:h, :w]; m = (xx - cx) ** 2 + (yy - cy) ** 2 <= rr * rr
        px[m] = hexrgb([0xe6d27e, 0xa9b86a, 0xc9c8b8][int(r.integers(3))])


ATLAS = None
def kit_mat():
    global ATLAS
    A = Atlas('birock_atlas', 128, 256)
    A.band('strata', 192, lambda px: paint_strata(px, 71))
    A.band('moss', 32, lambda px: paint_moss(px, 72))
    A.band('top', 32, lambda px: paint_top(px, 73))
    ATLAS = A
    return mat('birock', 0xffffff, rough=0.72, tex=A.image())


# ------------------------------------------------------------ the mesh: game points + faces + a tag per face
def mk_mesh(name, verts, faces, tags, M):
    me = bpy.data.meshes.new(name)
    me.from_pydata([gv(*p) for p in verts], [], [list(f) for f in faces])
    me.update()
    o = _link(bpy.data.objects.new(name, me)); me.materials.append(M)
    for p in me.polygons: p.use_smooth = False  # (faceted: the chunky look)
    uv_rock(o, tags)
    return o


def uv_rock(o, tags):
    """strata faces: u along the face, v up the height inside the tier's own window of the band; tops: moss or the
    sunlit cell, projected from above"""
    A = ATLAS; me = o.data
    uvl = me.uv_layers.new(name='UVMap').data
    su0, sv0, su1, sv1 = A.uvrect('strata', inset=0.5)
    for poly, tg in zip(me.polygons, tags):
        n = MK._gn(poly.normal)
        P = [V3((me.vertices[me.loops[li].vertex_index].co.x, me.vertices[me.loops[li].vertex_index].co.z, -me.vertices[me.loops[li].vertex_index].co.y)) for li in poly.loop_indices]
        if tg[0] in ('moss', 'top'):
            u0, v0, u1, v1 = A.uvrect(tg[0], inset=0.5)
            mz = min(q.z for q in P); e = max(1.0, max(q.z for q in P) - mz)  # (u wraps along the band: 2 m a repeat; v across it, 1 m or the face's depth)
            for li, p in zip(poly.loop_indices, P):
                uvl[li].uv = (p.x / 2.0, v0 + (v1 - v0) * (1 - (p.z - mz) / e))
            continue
        hx, hz = n.x, n.z; hl = math.hypot(hx, hz)
        if hl < 1e-4: hx, hz, hl = 0.0, 1.0, 1.0
        tx, tz = -hz / hl, hx / hl
        y0, off = tg[1], tg[2]
        for li, p in zip(poly.loop_indices, P):
            u = (p.x * tx + p.z * tz) / UV_W + tg[3]
            v = min(1.0, max(0.0, (p.y - y0 + off) / UV_H))
            uvl[li].uv = (u, sv0 + (sv1 - sv0) * v)


import zlib
def hh(s, y): return (zlib.crc32(f'{s}:{y:.2f}'.encode()) % 1000) / 1000  # (a steady hash: python's own changes per run)


# ------------------------------------------------------------ 2D helpers (x, z)
def hull(pts):
    pts = sorted(set((round(a, 5), round(b, 5)) for a, b in pts))
    if len(pts) < 3: return pts
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def polar(poly, th, c=(0.0, 0.0)):
    """distance from c to the convex polygon's edge along angle th"""
    dx, dz = math.cos(th), math.sin(th); best = 1e9
    for i in range(len(poly)):
        ax, az = poly[i][0] - c[0], poly[i][1] - c[1]; bx, bz = poly[(i + 1) % len(poly)][0] - c[0], poly[(i + 1) % len(poly)][1] - c[1]
        ex, ez = bx - ax, bz - az; den = dx * ez - dz * ex
        if abs(den) < 1e-9: continue
        t = (ax * ez - az * ex) / den; s = (ax * dz - az * dx) / den
        if t > 0 and -1e-6 <= s <= 1 + 1e-6: best = min(best, t)
    return best


def inside(poly, x, z):
    n = len(poly); c = False
    for i in range(n):
        ax, az = poly[i]; bx, bz = poly[(i + 1) % n]
        if (az > z) != (bz > z) and x < ax + (z - az) * (bx - ax) / (bz - az): c = not c
    return c


# ------------------------------------------------------------ a colliding piece: strata layers lofted round its boxes
def tiers_of(col):
    T = {}
    for b in col: T.setdefault((b[1], b[4]), []).append(b)
    return [(y0, y1, T[(y0, y1)]) for (y0, y1) in sorted(T)]


def strata_rock(name, M, col, seed, n=12, margin=0.2, jit=0.18, mids=1.4, cham=0.14, groove=0.07, dome=0.05, skirt=0.45,
                moss_top=True, moss_ledges=0.5, wet_y=0.0, lod=False, cen=(0.0, 0.0), top_tilt=0.0, cap=0.3):
    """one closed faceted mesh: per layer a ring at its foot, rings up its side (facets, a groove or two: bedding
    planes), a chamfer and a flat-ish top; the next layer starts on that top (a ledge). every ring holds the layer's
    boxes inside it (pushed out until it does)"""
    r = random.Random(seed); T = tiers_of(col)
    ph = r.random() * TAU / n
    # the facet columns: one at every corner of the foot layer's boxes (so a ring holds them without bulging out between),
    # the rest splitting the widest gaps, a little uneven
    cols = sorted(math.atan2(z - cen[1], x - cen[0]) % TAU for x, z in hull([(b[i], b[j]) for b in T[0][2] for i in (0, 3) for j in (2, 5)]))
    cols = [a + (r.random() - 0.5) * 0.06 for a in cols][:n]
    while len(cols) < n:
        g = max(range(len(cols)), key=lambda i: (cols[(i + 1) % len(cols)] - cols[i]) % TAU)
        w = (cols[(g + 1) % len(cols)] - cols[g]) % TAU
        cols.insert(g + 1, (cols[g] + w * (0.4 + 0.2 * r.random())) % TAU)
    cols.sort()
    cleft = [(-(0.6 + 0.4 * r.random()) if r.random() < 0.2 else 0.0) + (r.random() - 0.5) * 0.6 for _ in range(n)]  # (a column's own lean: a cleft down the whole rock, a bulge)
    tn = {}
    def tnz(k):  # each layer's own outline wobble (so the layers don't stack like a cake)
        if k not in tn: q = random.Random(seed * 31 + k * 7); tn[k] = [q.random() * 2 - 1 for _ in range(n)]
        return tn[k]
    def outline(boxes, m):
        pts = []
        for b in boxes:
            for x in (b[0], b[3]):
                for z in (b[2], b[5]):
                    for k in range(8): pts.append((x + m * math.cos(k * TAU / 8), z + m * math.sin(k * TAU / 8)))
        return hull(pts)
    def edge_pts(boxes, m=0.03):  # what a ring has to hold: the boxes' outline, corners and along the edges, a few cm out
        out = []
        for b in boxes:
            xa, xb, za, zb = b[0] - m, b[3] + m, b[2] - m, b[5] + m
            for f in (0.0, 0.25, 0.5, 0.75):
                out += [(xa + (xb - xa) * f, za), (xb, za + (zb - za) * f), (xb - (xb - xa) * f, zb), (xa, zb - (zb - za) * f)]
        return out
    def ring(k, boxes, y, m, j, inset=0.0, need=None, sc=1.0):
        poly = outline(boxes, m); t = tnz(k)
        base = [polar(poly, a, cen) for a in cols]  # (the boxes' hull, margin out)
        rad = [max(0.2, min(b * sc * (1 + j * (0.55 * t[i] + 0.45 * cleft[i]) + j * 0.25 * (r.random() - 0.5)), b + cap) - inset) for i, b in enumerate(base)]  # (never more than `cap` past it)
        P = edge_pts(need if need is not None else boxes)
        for _ in range(80):  # (pushed out wherever the boxes' outline isn't inside yet)
            pts = [(cen[0] + math.cos(a) * rr, cen[1] + math.sin(a) * rr) for a, rr in zip(cols, rad)]
            bad = [(x, z) for x, z in P if not inside(pts, x, z)]
            if not bad: break
            push = set()
            for x, z in bad:
                a = math.atan2(z - cen[1], x - cen[0]) % TAU
                i = min(range(n), key=lambda q: (a - cols[q]) % TAU)  # (the column just before it, going round)
                push.update((i, (i + 1) % n))
            for q in push: rad[q] *= 1.02
        return [(cen[0] + math.cos(a) * rr, y, cen[1] + math.sin(a) * rr) for a, rr in zip(cols, rad)]
    rings, rt = [], []  # rt: what the band above each ring is ('s', layer foot) / ('l') a ledge
    tilt = (r.random() - 0.5) * 0.06, (r.random() - 0.5) * 0.06
    for k, (y0, y1, boxes) in enumerate(T):
        H = y1 - y0
        if k == 0:  # the buried skirt and the foot
            rings.append(ring(k, boxes, y0 - skirt, margin + 0.1, jit)); rt.append(('s', y0))
        rings.append(ring(k, boxes, y0, margin, jit, sc=1.07)); rt.append(('s', y0))  # (each layer splays out at its foot)
        nm = 0 if lod else max(0, int(H / mids))
        for i in range(nm):
            yy = y0 + H * (i + 1) / (nm + 1)
            rr = ring(k, boxes, yy, margin, jit * (0.7 + 0.5 * r.random()))
            rr = [(x, y + tilt[0] * x + tilt[1] * z, z) for x, y, z in rr]  # (bedding planes dip a little)
            if not lod and groove and H > 1.0 and r.random() < 0.6:  # a groove: a bedding plane weathered in
                rings.append([(x, y - 0.06, z) for x, y, z in rr]); rt.append(('s', y0))
                g = [(x * (1 - groove / max(0.3, math.hypot(x, z))), y, z * (1 - groove / max(0.3, math.hypot(x, z)))) for x, y, z in rr]
                rings.append(g); rt.append(('s', y0))
                rr = [(x, y + 0.06, z) for x, y, z in rr]
            rings.append(rr); rt.append(('s', y0))
        top = (k == len(T) - 1)
        if not lod: rings.append(ring(k, boxes, y1 - cham, margin, jit * 0.8, sc=0.96)); rt.append(('s', y0))
        rings.append(ring(k, boxes, y1 + (0.03 if top else 0.0), margin, jit * 0.6, inset=cham if not lod else cham * 0.5, sc=0.96)); rt.append(('l', y1))
    if top_tilt:  # the top: a tilted slab, its high side up to top_tilt over the box (never under it)
        a = r.random() * TAU; dx, dz = math.cos(a), math.sin(a); R = max(math.hypot(x, z) for x, _, z in rings[-1]) or 1
        rings[-1] = [(x, y + top_tilt * (0.5 + 0.5 * (x * dx + z * dz) / R), z) for x, y, z in rings[-1]]
    # faces: the bands between rings, the top cap (a fan to a raised middle), the bottom cap
    V = [p for rg in rings for p in rg]; F, tags = [], []
    rs = random.Random(seed + 9)
    for k in range(len(rings) - 1):
        a0, b0 = k * n, (k + 1) * n
        flat = abs(rings[k][0][1] - rings[k + 1][0][1]) < 1e-6 and rt[k][0] == 'l'  # (a ledge between two layers)
        for i in range(n):
            j = (i + 1) % n
            F.append((a0 + i, a0 + j, b0 + j, b0 + i))
            ymid = (rings[k][i][1] + rings[k + 1][i][1]) / 2
            if flat:
                up = math.hypot(rings[k + 1][i][0], rings[k + 1][i][2]) < math.hypot(rings[k][i][0], rings[k][i][2])  # (stepping in: a ledge you see from above)
                tags.append(('moss',) if up and ymid > wet_y + 0.3 and rs.random() < moss_ledges else ('top',) if up else ('s', rt[k][1], 0.0, 0.0))
            else:
                y0 = rt[k][1]; tags.append(('s', y0, hh(name, y0) * max(0.0, UV_H - 4.6), hh(name + 'u', y0)))
    last = (len(rings) - 1) * n
    cx = sum(p[0] for p in rings[-1]) / n; cz = sum(p[2] for p in rings[-1]) / n; cy = sum(p[1] for p in rings[-1]) / n + dome
    V.append((cx, cy, cz)); ci = len(V) - 1
    for i in range(n): F.append((last + (i + 1) % n, last + i, ci)); tags.append(('moss',) if moss_top else ('top',))
    V.append((sum(p[0] for p in rings[0]) / n, rings[0][0][1], sum(p[2] for p in rings[0]) / n)); bi = len(V) - 1
    for i in range(n): F.append((i, (i + 1) % n, bi)); tags.append(('s', 0.0, 0.0, 0.0))
    # (the bands wound so normals face out: rings go round counter-clockwise seen from above in game x/z = clockwise in
    # blender... fix by recalculating after)
    o = mk_mesh(name, V, F, tags, M)
    fix_normals(o)
    return o


def fix_normals(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free(); o.data.update()
    return o


def boxes_inside(o, col, tag):
    """how far any collision box pokes out of the mesh (sampled over its faces): must be ~0"""
    me = o.data; worst = 0.0
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromBMesh(bm)
    def outside(p):  # ray parity along three directions: outside if most say so
        votes = 0
        for d in (V3((0.13, 0.21, 0.97)), V3((0.95, -0.2, 0.24)), V3((-0.3, 0.92, -0.25))):
            d.normalize(); q, hits = p.copy(), 0
            for _ in range(64):
                loc, nrm, idx, dist = bvh.ray_cast(q, d)
                if loc is None: break
                hits += 1; q = loc + d * 1e-4
            votes += hits % 2 == 0
        return votes >= 2
    for b in col:
        for fx in (0.0, 0.5, 1.0):
            for fy in (0.02, 0.5, 0.98):
                for fz in (0.0, 0.5, 1.0):
                    if fx not in (0.0, 1.0) and fz not in (0.0, 1.0): continue
                    p = gv(b[0] + (b[3] - b[0]) * fx, b[1] + (b[4] - b[1]) * fy, b[2] + (b[5] - b[2]) * fz)
                    if outside(p): worst = max(worst, bvh.find_nearest(p)[3])
    bm.free()
    print(f'JF_BOXES {tag}: worst poke-out {worst * 1000:.0f} mm')
    return worst


# ------------------------------------------------------------ a cliff face: a skin of strata over a sheer face
def cliff_face(name, M, ext, seed, nf=14, tiers=None, lod=False, rib=0.0, notch=1.5, wet_y=1.6, moss_ledges=0.55):
    """front +z. the back is flat at the box's back (buried in the cliff top); the front leans back up the height (2.5 at
    the foot, -1.0 at the top: it hugs the ground's face from just outside), each strata layer bulging out a little more
    at its foot than its top (a ledge on every layer), a wave-cut notch at the bottom, the ends rounding back into the
    cliff (the next piece overlaps them)"""
    (x0, y0, z0), (x1, y1, z1) = ext
    W, H, D = x1 - x0, y1 - y0, z1 - z0
    r = random.Random(seed)
    if tiers is None:
        tiers, y = [], notch
        while y < H - 0.8:
            t = min(H - y, 1.3 + r.random() * 2.2)
            if H - (y + t) < 1.0: t = H - y
            tiers.append((y, y + t)); y += t
    xs = [x0 + W * i / (nf - 1) for i in range(nf)]
    def vn(sd, x, cell=1.6):  # 1D value noise in [-1, 1] (the same for both LODs: a function of x, not of the vertex)
        i = math.floor(x / cell); f = x / cell - i; f = f * f * (3 - 2 * f)
        h = lambda q: (zlib.crc32(f'{seed}:{sd}:{q}'.encode()) % 2001) / 1000 - 1
        return h(i) * (1 - f) + h(i + 1) * f
    def cl(x): return min(0.0, vn('cleft', x, 2.4) + 0.35) * 1.3 + rib * (0.5 + 0.5 * math.cos((x - x0) / W * TAU * 1.5 + 0.7))  # (clefts down the whole face, ribs on a buttress)
    def front(y): return z1 - 3.5 * (y - y0) / H  # (the lean)
    def endk(x): q = abs(2 * (x - (x0 + x1) / 2) / W); return 1 - q ** 3  # 1 in the middle, 0 at the ends
    def ring(y, out, j, inset=0.0, notchk=0.0, k=0):
        pts = [(x0, y, z0)]
        for i, x in enumerate(xs):
            e = endk(x)
            zf = front(y) + out + j * (0.6 * vn(k, x, 1.3) + 0.25 * vn(k * 7 + 3, x, 0.5)) + cl(x) - inset - notchk
            zf = z0 + 0.25 + (zf - z0 - 0.25) * (0.15 + 0.85 * e ** 0.5)  # (the ends round back)
            pts.append((x, y, min(z1 + 0.6, max(z0 + 0.25, zf))))
        pts.append((x1, y, z0))
        return pts
    rings, tg = [], []
    jt = 0.45
    rings.append(ring(y0 - 0.01, 0.0, jt, notchk=0.15, k=99)); tg.append(('s', y0))
    if not lod: rings.append(ring(notch * 0.55, 0.0, jt, notchk=0.75, k=98)); tg.append(('s', y0))  # the notch's back
    if lod: tiers = [(tiers[i][0], tiers[min(i + 1, len(tiers) - 1)][1]) for i in range(0, len(tiers), 2)]  # (far: two layers in one)
    for k, (ta, tb) in enumerate(tiers):
        out = 0.55 + 0.35 * r.random()
        rings.append(ring(ta, out, jt, k=k)); tg.append(('s', ta))
        if not lod and tb - ta > 1.6:
            rings.append(ring((ta + tb) / 2, out * 0.6, jt, k=k)); tg.append(('s', ta))
        top = k == len(tiers) - 1
        if not lod: rings.append(ring(tb - 0.18, 0.18 + (0.0 if top else 0.1), jt * 0.8, k=k)); tg.append(('s', ta))
        rings.append(ring(tb, 0.0, jt * 0.7, inset=0.28 if top else 0.05, k=k)); tg.append(('l', tb))
    n = len(rings[0])
    V = [p for rg in rings for p in rg]; F, tags = [], []
    rs = random.Random(seed + 5)
    for k in range(len(rings) - 1):
        a0, b0 = k * n, (k + 1) * n
        flat = abs(rings[k][1][1] - rings[k + 1][1][1]) < 1e-6
        for i in range(n):
            j = (i + 1) % n
            if i == n - 1:  # the back: one strip from the right end round to the left
                F.append((a0 + i, a0 + 0, b0 + 0, b0 + i)); tags.append(('s', 0.0, 0.0, 0.0)); continue
            F.append((a0 + i, a0 + j, b0 + j, b0 + i))
            if flat:
                ymid = rings[k][i][1]
                tags.append(('moss',) if ymid > wet_y + 0.4 and rs.random() < moss_ledges else ('top',))
            else:
                ya = tg[k][1]; tags.append(('s', ya, hh(name, ya) * max(0.0, UV_H - 4.2), hh(name + 'u', ya)))
    # caps: the top (flat, under the cliff-top's grass: moss) and the bottom
    top = rings[-1]; t0 = len(V) - n
    V.append((sum(p[0] for p in top) / n, top[0][1], (z0 + sum(p[2] for p in top) / n) / 2)); ci = len(V) - 1
    for i in range(n): F.append((t0 + i, t0 + (i + 1) % n, ci)); tags.append(('moss',))
    bot = rings[0]
    V.append((sum(p[0] for p in bot) / n, bot[0][1], (z0 + sum(p[2] for p in bot) / n) / 2)); bi = len(V) - 1
    for i in range(n): F.append(((i + 1) % n, i, bi)); tags.append(('s', 0.0, 0.0, 0.0))
    o = mk_mesh(name, V, F, tags, M)
    fix_normals(o)
    return o


# ------------------------------------------------------------ colour: lit tops, cool undersides, the wet band
def shade_rock(o, wet_y, wet_k=(0.5, 0.54, 0.6), top_k=(1.0, 0.98, 0.94), side_k=(0.9, 0.9, 0.93), under_k=(0.58, 0.64, 0.8)):
    """painted into the AO colours (the game multiplies them in): faces up are lit warm, sides a touch cooler, faces down
    a cool blue-grey; everything below wet_y (with a soft 0.35 m edge) darker and cooler: the wet band"""
    me = o.data; ca = me.color_attributes.get('AO')
    for p in me.polygons:
        n = MK._gn(p.normal); ny = n.y
        if ny > 0.55: k = top_k
        elif ny < -0.3: k = under_k
        else:
            t = max(0.0, min(1.0, (ny + 0.3) / 0.85)); k = [under_k[i] + (side_k[i] - under_k[i]) * min(1, t * 2) if t < 0.5 else side_k[i] + (top_k[i] - side_k[i]) * (t - 0.5) * 2 for i in range(3)]
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co; y = v.z
            w = max(0.0, min(1.0, (wet_y - y) / 0.35 + 0.5)) if wet_y > 0 else 0.0
            c = ca.data[li].color
            m = [k[i] * (1 - w + w * wet_k[i]) for i in range(3)]
            ca.data[li].color = (c[0] * m[0], c[1] * m[1], c[2] * m[2], 1.0)


# ------------------------------------------------------------ the flow (make_bipark's run_bi, slimmed)
def run_rock(fid, fn):
    lib.reset(); lib._mats.clear()
    d = fn()
    lo, hi = V3(d['box'][0]), V3(d['box'][1])
    if MK.opt('qa'):
        MK.qa(d['lod0'], fid + ':lod0', eps=0.001); MK.qa(d['lod1'], fid + ':lod1', eps=0.001)
    print(f'JF_PARTS {fid}: lod0 {MK.tris_of(d["lod0"])} tris, lod1 {MK.tris_of(d["lod1"])} tris')
    if d.get('col'):
        for o in d['lod0'] + d['lod1']: boxes_inside(o, d['col'], o.name)
    l0 = join(d['lod0'], fid + '_lod0'); l1 = join(d['lod1'], fid + '_lod1')
    MK.box_report(l0, lo, hi, fid + ' lod0'); MK.box_report(l1, lo, hi, fid + ' lod1')
    bake_ao([l0], dist=d.get('ao', 1.0), lo=0.5); bake_ao([l1], dist=d.get('ao', 1.0), lo=0.5)
    for o in (l0, l1): shade_rock(o, d['wet'])
    meta = dict(id=fid[2:], lod=d.get('lod', 60), tint=False, size=[round(hi[i] - lo[i], 3) for i in range(3)],
                box=[[round(v, 3) for v in lo], [round(v, 3) for v in hi]])
    root = prop_finish(fid, [l0], [l1], meta)
    t0, t1 = prop_stats(root)
    print(f'JF_MATS {fid}: lod0 {[m.name for m in l0.data.materials]} lod1 {[m.name for m in l1.data.materials]}  meta {json.dumps(meta)}')
    if not MK.opt('no-export'): export(root, fid)
    if MK.opt('preview'): MK.preview(root, fid, MK.opt('preview'), focus=d.get('focus', ()))
    elif not MK.opt('no-sheet'): MK.sheet4(root, fid, t0, t1, 1, 1, **d.get('sheet', {}))
    return root


def colliding(fid, seed, n0, n1, wet, lod, **kw):
    K = RK[fid]; M = kit_mat()
    l0 = strata_rock(fid + '_rock', M, K['col'], seed, n=n0, wet_y=wet, **kw)
    kw1 = {k: v for k, v in kw.items() if k not in ('mids', 'groove')}
    l1 = strata_rock(fid + '_far', M, K['col'], seed, n=n1, wet_y=wet, lod=True, **kw1)
    return dict(lod0=[l0], lod1=[l1], box=K['ext'], col=K['col'], wet=wet, lod=lod, ao=1.2, sheet=dict(exposure=-0.6))


@prop('p_bi_boulder_s')
def build_boulder_s(): return colliding('bi_boulder_s', 11, 7, 5, 0.12, 35, margin=0.12, jit=0.14, mids=9, cham=0.08, skirt=0.25, moss_top=False, dome=0.08, top_tilt=0.15, cap=0.15)
@prop('p_bi_boulder_m')
def build_boulder_m(): return colliding('bi_boulder_m', 12, 10, 8, 0.2, 50, margin=0.16, jit=0.16, mids=9, cham=0.12, skirt=0.35, moss_top=False, moss_ledges=0.3, dome=0.08, top_tilt=0.25, cap=0.22)
@prop('p_bi_boulder_l')
def build_boulder_l(): return colliding('bi_boulder_l', 13, 11, 8, 0.3, 70, margin=0.2, jit=0.18, mids=1.6, cham=0.15, skirt=0.5, moss_top=True, moss_ledges=0.5, dome=0.1, top_tilt=0.3, cap=0.3)
@prop('p_bi_ledge')
def build_ledge(): return colliding('bi_ledge', 14, 11, 8, 0.75, 60, margin=0.2, jit=0.14, mids=9, cham=0.15, skirt=0.6, moss_top=False, moss_ledges=0.0, dome=0.03, top_tilt=0.08, cap=0.3)
@prop('p_bi_stack_a')
def build_stack_a(): return colliding('bi_stack_a', 15, 12, 8, 2.2, 130, margin=0.22, jit=0.17, mids=2.2, cham=0.16, skirt=0.8, moss_top=True, moss_ledges=0.55, dome=0.05, top_tilt=0.2, cap=0.4)
@prop('p_bi_stack_b')
def build_stack_b(): return colliding('bi_stack_b', 16, 12, 8, 1.8, 120, margin=0.22, jit=0.17, mids=2.0, cham=0.16, skirt=0.8, moss_top=True, moss_ledges=0.6, dome=0.05, top_tilt=0.2, cap=0.4)


def face(fid, seed, nf0, nf1, lod, **kw):
    K = RK[fid]; M = kit_mat(); ext = K['ext']
    l0 = cliff_face(fid + '_face', M, ext, seed, nf=nf0, **kw)
    l1 = cliff_face(fid + '_far', M, ext, seed, nf=nf1, lod=True, **kw)
    return dict(lod0=[l0], lod1=[l1], box=ext, wet=1.6, lod=lod, ao=1.6, sheet=dict(exposure=-0.6))


@prop('p_bi_cliff_a')
def build_cliff_a(): return face('bi_cliff_a', 21, 15, 5, 110)
@prop('p_bi_cliff_b')
def build_cliff_b(): return face('bi_cliff_b', 22, 12, 5, 110)
@prop('p_bi_cliff_c')
def build_cliff_c(): return face('bi_cliff_c', 23, 9, 4, 110, rib=0.55)


if __name__ == '__main__':
    todo = [(f, fn) for f, fn in PROPS if not ONLY or f[5:] in ONLY or f[2:] in ONLY or f in ONLY]
    for fid, fn in todo:
        run_rock(fid, fn)
