# JANKFIRE round 4, batch A: the maps' trees and plants as glossy Blender models. The game draws them GPU-instanced in
# place of their kit boxes (shared/map.js; the boxes stay the collision): each is built on its kit function's layout
# with the trunk on the origin, y = 0 the ground, front -z, and carries meta.box = the box version's extent at the
# reference parameters (for props that turn per copy: averaged over the kit's own random turns, measured like
# shared/propcap.js propOf() does), so every copy is fitted from its own boxes. lod0 = up close (casts shadows),
# lod1 = a hand-made far silhouette. AO baked into COLOR_0. One small nearest-filtered atlas per prop, 1-2 materials.
#   p_lollipop  lollipop() / tree(), built at h 6.5 (the median copy; the crown boxes are 2.7 m on every copy): a clipped
#               standard street tree, a flared stem forking into a ball of glossy leaf-cluster puffs in `tint` (leaf
#               green, dark green or blossom pink per copy), an aluminium city tag on the trunk that says TREE.
#               meta.top = ['tint']: the crown could keep its height on every copy (see the meta note below).
#   p_conifer   conifer() h 6: a fir in four whorled star tiers, hedge green / lime alternating like the boxes.
#   p_pine      pine() h 14, w0 4.2: the Scary Forest spruce, six drooping star tiers turned against each other like
#               the box tiers (tier i at the boxes' yaw + 0.7 i), night colours, one material. 2,536 copies: 248 / 24.
#   p_birch     birch() h 9: a silver birch, a leaning white trunk with black lenticels, chevrons, a black foot and the
#               two "eyes" birches grow where branches fell off (on the front, at eye height), three weeping cushions.
#   p_deadtree  deadTree() h 8: a crooked grey snag with a splintered top, five branches out and an elbow up at the end,
#               a second kink and finger twigs on some (too many elbows), bleached wood at the break.
#   p_palm      palm() h 7.2 (the median copy): a coconut palm leaning toward +x (lx 0.18 a segment; the game turns each copy to its own
#               lean), a ringed trunk in the boxes' two woods, eight arching V-folded fronds, a fibrous heart, coconuts.
#               Trunk and crown are their own materials (meta.top = ['pm_crown']).
#   p_saguaro   saguaro() h 4: the cartoon saguaro in glossy toy green: five ribs, two J arms, spine dots, white flowers.
#   p_fern      the Scary Forest's ferns (three crossed fronds in the boxes, s 1): six arching fronds and a fiddlehead.
#   p_bush      the Scary Forest's bushes (s 1): a glossy holly clump of puffs round a core, red berries.
# meta.top (a suggestion for the fit, propfield.js): parts in these materials keep their own height and ride the top of
# each copy's extent; the rest stretches. The kit keeps those crowns one size whatever the trunk's height.
# run: blender -b --python tools/blender/make_trees.py   (-- --only=lollipop,pine  -- --qa (the blender-asset-qa gate,
#      lod0 and lod1 apart)  -- --no-sheet  -- --no-export  -- --close=<dir> close-up review renders)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link, _image
import lib
from mathutils.bvhtree import BVHTree

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = next((a.split('=', 1)[1].split(',') for a in ARGV if a.startswith('--only=')), None)
CLOSE = next((a.split('=', 1)[1] for a in ARGV if a.startswith('--close=')), None)
V3 = Vector
TAU = 2 * math.pi


# ------------------------------------------------------------ textures (numpy, rows top-down, tile where they must)
def vnoise(h, w, cy, cx, rng):
    """smooth value noise h x w px, cy x cx cells, wraps on both axes (so a stripe tiles top to bottom)"""
    lat = rng.random((cy, cx))
    def ax(n, c):
        t = np.arange(n) * c / n
        i0 = np.floor(t).astype(int) % c
        f = t - np.floor(t)
        return i0, (i0 + 1) % c, f * f * (3 - 2 * f)
    y0, y1, fy = ax(h, cy); x0, x1, fx = ax(w, cx)
    a = lat[y0][:, x0] * (1 - fx)[None] + lat[y0][:, x1] * fx[None]
    b = lat[y1][:, x0] * (1 - fx)[None] + lat[y1][:, x1] * fx[None]
    return a * (1 - fy)[:, None] + b * fy[:, None]


def speckle(h, w, rng, px=2):
    """the game's own canvas speckle: random blocks px x px"""
    s = rng.random(((h + px - 1) // px, (w + px - 1) // px))
    return np.kron(s, np.ones((px, px)))[:h, :w]


def paint_bark(px, r0, r1, c0, c1, base, dark, light, seed, grooves=6, var=0.18, wob=1.2, knots=2):
    """bark into px[r0:r1, c0:c1]: mottled base + speckle, wobbly dark grooves running down (periodic: tiles in both
    axes), a light ridge beside each groove, a few knots"""
    rng = np.random.default_rng(seed)
    h, w = r1 - r0, c1 - c0
    n = 0.5 * vnoise(h, w, 6, max(2, w // 6), rng) + 0.3 * vnoise(h, w, 12, max(2, w // 3), rng) + 0.2 * speckle(h, w, rng)
    reg = hexrgb(base)[None, None] * (1 - var + 2 * var * n[:, :, None])
    D, Lc = hexrgb(dark), hexrgb(light)
    for g in range(grooves):
        x = (g + rng.uniform(0.2, 0.8)) * w / grooves
        k1, k2 = int(rng.integers(1, 3)), int(rng.integers(2, 5)); p1, p2 = rng.uniform(0, TAU, 2)
        for y in range(h):
            if rng.random() < 0.07: continue
            xx = x + wob * math.sin(TAU * k1 * y / h + p1) + 0.5 * wob * math.sin(TAU * k2 * y / h + p2)
            xi = int(round(xx)) % w
            reg[y, xi] = D * rng.uniform(0.8, 1.1)
            reg[y, (xi + 1) % w] = reg[y, (xi + 1) % w] * 0.55 + Lc * 0.45
    for k in range(knots):
        cy, cx = rng.uniform(0, h), rng.uniform(0, w)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                d = (dx * dx) / 4.0 + (dy * dy) / 2.2
                if d <= 1.0: reg[int(cy + dy) % h, int(cx + dx) % w] = D * (0.7 if d < 0.4 else 1.0)
    px[r0:r1, c0:c1] = np.clip(reg, 0, 1)


def paint_leaf(px, r0, r1, c0, c1, base, seed, var=0.16, dark=0.62, light=1.3, dots=0.05, spots=0.08, mottle=0.12):
    """foliage into px[r0:r1, c0:c1]: the game's 2 px speckle round a base green, soft mottling, darker leaf-shadow
    blocks and a few light glints (leaves catching the sun)"""
    rng = np.random.default_rng(seed)
    h, w = r1 - r0, c1 - c0
    n = vnoise(h, w, 4, max(2, w // 8), rng)
    sp = speckle(h, w, rng)
    reg = hexrgb(base)[None, None] * (1 - mottle + 2 * mottle * n[:, :, None]) * (1 - var + 2 * var * sp[:, :, None])
    blk = speckle(h, w, rng)
    reg[blk < spots] *= dark
    reg[blk > 1 - dots] *= light
    px[r0:r1, c0:c1] = np.clip(reg, 0, 1)


def paint_needles(px, r0, r1, c0, c1, base, seed, var=0.2, dash=0.62, glint=None):
    """conifer needles into px[r0:r1, c0:c1], like the forest's own needle texture: 2 px speckle round a base green,
    staggered dark dashes (needle shadows), a few lighter needle tips"""
    rng = np.random.default_rng(seed)
    h, w = r1 - r0, c1 - c0
    reg = hexrgb(base)[None, None] * (1 - var + 2 * var * speckle(h, w, rng)[:, :, None])
    reg *= (0.9 + 0.2 * vnoise(h, w, 4, max(2, w // 8), rng))[:, :, None]
    for y in range(3, h, 4):
        for x in range((y >> 2) % 2 * 2, w, 4):
            reg[y, x:x + 2] *= dash
    if glint is not None:
        m = rng.random((h, w)) < 0.035
        reg[m] = hexrgb(glint)
    px[r0:r1, c0:c1] = np.clip(reg, 0, 1)


def img(name, px):
    return _image(name, np.clip(px, 0, 1).astype(np.float32))


# ------------------------------------------------------------ uv: regions of a small atlas
def _region(rect, W, H):
    """rect = (r0, r1, c0, c1) in px (rows top-down) -> (u0, u1, v0, v1) with a half-texel margin"""
    r0, r1, c0, c1 = rect
    return ((c0 + 0.5) / W, (c1 - 0.5) / W, 1 - (r1 - 0.5) / H, 1 - (r0 + 0.5) / H)


def _fold(t):
    t = t % 2.0
    return t if t <= 1 else 2 - t


def uv_region(o, rect, W, H, proj='box', ppm=12.0, umode='fold', vmode='fold', axis_c=(0.0, 0.0), arc_r=0.25, fit=None):
    """UVs for o into one region of an atlas. proj: 'box' (per face: the plane its normal faces most), 'cyl' (around a
    vertical axis through axis_c = (x, z), arc length at radius arc_r), 'up' (top-down x/z). Each axis either 'tile'
    (free: the region spans the whole texture that way), 'fold' (mirrors back and forth inside the region, so no face
    leaves it) or 'fit' (the object's extent squeezed into the region, fit = (lo, hi) metres). ppm = pixels per metre."""
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world; nm = mw.to_3x3()
    u0, u1, v0, v1 = _region(rect, W, H)
    su, sv = (rect[3] - rect[2] - 1) / ppm, (rect[1] - rect[0] - 1) / ppm  # metres across the region
    def coords(poly):
        n = nm @ poly.normal; gn = (n.x, n.z, -n.y)
        g = []
        for li in poly.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            g.append((p.x, p.z, -p.y))
        if proj == 'box':
            ax = max(range(3), key=lambda i: abs(gn[i]))
            if ax == 1: return [(q[0] * (1 if gn[1] > 0 else -1), q[2]) for q in g]
            if ax == 0: return [(-q[2] * (1 if gn[0] > 0 else -1), q[1]) for q in g]
            return [(q[0] * (1 if gn[2] > 0 else -1), q[1]) for q in g]
        if proj == 'up': return [(q[0], q[2]) for q in g]
        ang = [math.atan2(q[2] - axis_c[1], q[0] - axis_c[0]) for q in g]
        ref = ang[0]
        ang = [a + TAU * round((ref - a) / TAU) for a in ang]
        return [(a * arc_r, q[1]) for a, q in zip(ang, g)]
    def one(m, lo, hi, s, mode, ext):
        if mode == 'tile': return m / s * (hi - lo)  # (the region spans the texture that way: it repeats)
        if mode == 'fit': return lo + (m - ext[0]) / max(ext[1] - ext[0], 1e-6) * (hi - lo)
        return lo + _fold(m / s) * (hi - lo)
    polys = list(me.polygons)
    allc = [coords(p) for p in polys]
    ext_u = ext_v = (0, 1)
    if 'fit' in (umode, vmode):
        us = [a for c in allc for a, _ in c]; vs = [b for c in allc for _, b in c]
        ext_u, ext_v = (fit[0] if fit else (min(us), max(us))), (fit[1] if fit else (min(vs), max(vs)))
    for poly, cs in zip(polys, allc):
        ab = [(one(a, u0, u1, su, umode, ext_u), one(b, v0, v1, sv, vmode, ext_v)) for a, b in cs]
        # a fold running through a face squashes it: lay that face out flat inside the region instead
        def area(pts): return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))))
        raw = [((a / su) * (u1 - u0), (b / sv) * (v1 - v0)) for a, b in cs]
        if area(ab) < 0.3 * area(raw):
            def lay(vals, lo, hi, mode):
                if mode in ('tile', 'fit'): return None
                k = math.floor(min(vals)); t = [x - k for x in vals]
                if max(t) > 1: t = [x / max(t) for x in t]
                return [lo + x * (hi - lo) for x in t]
            lu = lay([a / su for a, _ in cs], u0, u1, umode); lv = lay([b / sv for _, b in cs], v0, v1, vmode)
            ab = [(lu[i] if lu else ab[i][0], lv[i] if lv else ab[i][1]) for i in range(len(ab))]
        for li, q in zip(poly.loop_indices, ab): uv[li].uv = q
    return o


def uv_decal(o, rect, W, H, centre, size, facing=(0, 0, -1), right=(-1, 0, 0), up=(0, 1, 0), thr=0.6, plain=None):
    """straight-on UVs for the faces of o that face `facing` (game): the decal rect fills size = (w, h) metres round
    centre; the other faces get a tiny patch of `plain` (a rect) so nothing has zero area"""
    bpy.context.view_layer.update()
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world; nm = mw.to_3x3()
    u0, u1, v0, v1 = _region(rect, W, H)
    pu0, pu1, pv0, pv1 = _region(plain or rect, W, H)
    F, R, U, C = V3(facing), V3(right), V3(up), V3(centre)
    for poly in me.polygons:
        n = nm @ poly.normal; gn = V3((n.x, n.z, -n.y))
        pts = []
        for li in poly.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            pts.append(V3((p.x, p.z, -p.y)))
        if gn.dot(F) > thr:
            for li, p in zip(poly.loop_indices, pts):
                d = p - C
                uv[li].uv = (u0 + (0.5 + d.dot(R) / size[0]) * (u1 - u0), v0 + (0.5 + d.dot(U) / size[1]) * (v1 - v0))
        else:
            cu, cv = (pu0 + pu1) / 2, (pv0 + pv1) / 2
            for k, li in enumerate(poly.loop_indices):
                a = TAU * k / len(pts)
                uv[li].uv = (cu + 0.3 * (pu1 - pu0) * math.cos(a), cv + 0.3 * (pv1 - pv0) * math.sin(a))
    return o


# ------------------------------------------------------------ geometry helpers
def weld(o, dist=1e-5, recalc=False):
    """merge doubles, drop slivers and loose verts. recalc only on closed parts: open shells (culled lumps) can flip"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    if recalc: bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    o.data.update()
    return o


def bake_tf(o):
    """apply modifiers and the object transform into the mesh (the object ends at the origin, identity)"""
    apply_mods(o)
    bpy.context.view_layer.update()  # (matrix_world is stale right after placing)
    o.data.transform(o.matrix_world)
    o.matrix_world = Matrix.Identity(4)
    return o


def gpts(o):
    """mesh verts in game coords (object transform applied first)"""
    return [V3((v.co.x, v.co.z, -v.co.y)) for v in o.data.vertices]


def bbox(objs):
    lo = V3((1e9,) * 3); hi = V3((-1e9,) * 3)
    for o in objs:
        for p in gpts(o):
            lo = V3(map(min, lo, p)); hi = V3(map(max, hi, p))
    return lo, hi


def fit_box(objs, lo, hi, axes=(0, 1, 2)):
    """scale + move the meshes of objs (transforms baked) so their joint bbox spans lo..hi (game) on the given axes"""
    a, b = bbox(objs)
    for o in objs:
        for v in o.data.vertices:
            g = [v.co.x, v.co.z, -v.co.y]
            for i in axes:
                g[i] = lo[i] + (g[i] - a[i]) / max(b[i] - a[i], 1e-9) * (hi[i] - lo[i])
            v.co = gv(*g)
        o.data.update()


def edit_verts(o, fn):
    """fn(game point) -> new game point, on every vertex (transforms baked)"""
    for v in o.data.vertices:
        g = fn(V3((v.co.x, v.co.z, -v.co.y)))
        v.co = gv(*g)
    o.data.update()
    return o


def lump(c, r, m, name, seg=8, rings=6, rot=(0, 0, 0)):
    """a smooth ellipsoid lump (radii r = game x, y, z), turned by rot (game euler), transforms baked"""
    o = ball(1.0, (0, 0, 0), m, scale=r, seg=seg, rings=rings, name=name)
    o.rotation_euler = Euler((rot[0], -rot[2], rot[1]), 'YZX')
    o.location = gv(*c)
    bpy.context.view_layer.update()
    return bake_tf(o)


def cull_inside(objs, margin=0.01):
    """delete the faces of each mesh that sit wholly inside one other (convex) mesh of the set: overlapping lumps keep
    only their outer skin (no hidden triangles). (inside one and the same lump: a face with corners in two different
    lumps can still poke out of the crease between them)"""
    trees = []
    for o in objs:
        bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
        trees.append(BVHTree.FromBMesh(bm)); bm.free()
    for i, o in enumerate(objs):
        bm = bmesh.new(); bm.from_mesh(o.data)
        mw = o.matrix_world
        def inside(p):
            s = set()
            for j, t in enumerate(trees):
                if j == i: continue
                loc, n, _, d = t.find_nearest(p)
                if loc is not None and (p - loc).dot(n) < 0 and d > margin: s.add(j)
            return s
        flags = {v: inside(mw @ v.co) for v in bm.verts}
        dead = [f for f in bm.faces if set.intersection(*[flags[v] for v in f.verts])]
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bm.to_mesh(o.data); bm.free(); o.data.update()
    return objs


def tris_of(o):
    me = o.data; me.calc_loop_triangles(); return len(me.loop_triangles)


def jit(o, amount, seed, keep_y_below=None):
    """push verts in/out a bit (hand-made wobble); verts below keep_y_below (on the ground) stay put"""
    r = random.Random(seed)
    me = o.data
    for v in me.vertices:
        if keep_y_below is not None and v.co.z < keep_y_below: continue
        v.co += V3((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1))) * amount
    me.update()
    return o


def nocull(*ms):
    for m in ms: m.use_backface_culling = False  # glTF doubleSided (fronds)


def cull(*ms):
    for m in ms: m.use_backface_culling = True  # glTF single-sided: closed meshes, half the fragment work


def mesh_from(name, verts, faces, m, smooth_all=True):
    """a mesh from game-space verts + faces (index lists)"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(*p)) for p in verts]
    for f in faces:
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    if smooth_all:
        for p in o.data.polygons: p.use_smooth = True
    return o


def stitch(bm, A, B, ca, cb):
    """triangles between two closed rings of verts (any counts) sorted by angle round centres ca, cb (game x, z):
    a zipper that always advances the ring whose next vertex comes first. len(A) + len(B) triangles"""
    def ang(v, c):
        g = (v.co.x, -v.co.y)
        return math.atan2(g[1] - c[1], g[0] - c[0]) % TAU
    ia = min(range(len(A)), key=lambda i: ang(A[i], ca)); ib = min(range(len(B)), key=lambda i: ang(B[i], cb))
    A = A[ia:] + A[:ia]; B = B[ib:] + B[:ib]
    aa = [ang(v, ca) for v in A] + [TAU + ang(A[0], ca)]; ab = [ang(v, cb) for v in B] + [TAU + ang(B[0], cb)]
    i = j = 0
    while i < len(A) or j < len(B):
        if j >= len(B) or (i < len(A) and aa[i + 1] <= ab[j + 1]):
            bm.faces.new((A[i], A[(i + 1) % len(A)], B[j % len(B)])); i += 1
        else:
            bm.faces.new((A[i % len(A)], B[(j + 1) % len(B)], B[j])); j += 1


def blob(name, m, rings, bottom=None, top=None, noise=0.0, seed=1):
    """a hand-made low blob for far LODs (and simple lumps): rings = [(y, r, n, phase deg, cx, cz, sx, sz)] bottom to
    top (sx / sz squash the ring), bottom / top = (x, y, z) apex points or None (left open). smooth shaded"""
    rnd = random.Random(seed)
    bm = bmesh.new()
    R = []
    for ring in rings:
        y, r, n, ph = ring[:4]
        cx, cz, sx, sz = (list(ring[4:]) + [0, 0, 1, 1][len(ring) - 4:])[:4] if len(ring) > 4 else (0, 0, 1, 1)
        vs = []
        for k in range(n):
            a = math.radians(ph) + TAU * k / n
            rr = r * (1 + rnd.uniform(-noise, noise))
            vs.append(bm.verts.new(gv(cx + math.cos(a) * rr * sx, y, cz + math.sin(a) * rr * sz)))
        R.append((vs, (cx, cz)))
    for (A, ca), (B, cb) in zip(R, R[1:]): stitch(bm, A, B, ca, cb)
    if bottom is not None:
        c = bm.verts.new(gv(*bottom)); A = R[0][0]
        for k in range(len(A)): bm.faces.new((A[(k + 1) % len(A)], A[k], c))
    if top is not None:
        c = bm.verts.new(gv(*top)); A = R[-1][0]
        for k in range(len(A)): bm.faces.new((A[k], A[(k + 1) % len(A)], c))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def profile(objs, ys, band=0.2):
    """the widest radius (from the y axis) of some meshes at each height in ys: a far blob follows the near outline"""
    pts = [p for o in objs for p in gpts(o)]
    out = []
    for y in ys:
        near = [math.hypot(p.x, p.z) for p in pts if abs(p.y - y) <= band]
        out.append(max(near) if near else 0.0)
    return out


def kill_faces(o, test):
    """delete faces whose centre (game) passes test (hidden backs, caps nobody sees)"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    dead = []
    for f in bm.faces:
        c = f.calc_center_median(); g = V3((c.x, c.z, -c.y))
        n = f.normal; gn = V3((n.x, n.z, -n.y))
        if test(g, gn): dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(o.data); bm.free(); o.data.update()
    return o


def puff_crown(name, m, c, R, layout, seed=4, rad=(0.55, 0.72), depth=0.45, seg=6, rings=4, core=(7, 4), squash=0.88, wob=0.25):
    """a crown of leaf clusters: an ellipsoid core (centre c, radii R) with puffs sat on it in rings: layout =
    [(latitude -1..1, count, phase deg)], each puff sunk `depth` of its radius into the core along the core's normal,
    turned and nudged a bit at random so the rings don't read. Faces hidden inside another lump are dropped. returns
    the lumps (join them)"""
    rnd = random.Random(seed)
    spec = [(c, R, (0, 0.2, 0), core)]
    for lat, cnt, ph in layout:
        for k in range(cnt):
            yk = max(-1.0, min(1.0, lat + rnd.uniform(-0.06, 0.06)))
            rr = math.sqrt(max(0.0, 1 - yk * yk)); a = math.radians(ph) + TAU * k / max(cnt, 1) + rnd.uniform(-wob, wob)
            d = V3((math.cos(a) * rr, yk, math.sin(a) * rr))
            p = V3((c[0] + d.x * R[0], c[1] + d.y * R[1], c[2] + d.z * R[2]))
            r = rnd.uniform(*rad)
            p -= V3((d.x / R[0], d.y / R[1], d.z / R[2])).normalized() * r * depth  # along the core's surface normal
            spec.append((tuple(p), (r, r * squash, r), (rnd.uniform(-0.3, 0.3), rnd.uniform(0, 3), rnd.uniform(-0.3, 0.3)), (seg, rings)))
    ls = [lump(cc, rr_, m, f'{name}{i}', seg=sr[0], rings=sr[1], rot=rt) for i, (cc, rr_, rt, sr) in enumerate(spec)]
    return cull_inside(ls)


def tier(name, m, y0, y1, r, n, phase=0.0, notch=0.78, notch_up=0.2, droop=0.12, mid=0.52, mid_h=0.42, mid_out=0.0,
         under=0.32, apex_up=0.25, sq=1.0, rnd=None, jag=0.0, mid2=None, mid2_h=0.8):
    """one whorl of a conifer (or a leaf cushion): n branch tips (radius r, drooping `droop` below y0) with notches
    between them (radius r * notch, `notch_up` above y0), a ring over the tips at `mid` radius / `mid_h` up the tier
    (and a second, `mid2` / `mid2_h`, for a rounded cushion), an apex at y1 + apex_up (hidden inside the next tier, or
    the tree's tip), and a shallow underside up to the trunk. 6n triangles (8n with mid2, 4n with mid=None). sq
    squashes it along z. jag = random wobble of the tips"""
    rnd = rnd or random.Random(1)
    hh = y1 - y0
    V, F = [], []
    def add(p): V.append(p); return len(V) - 1
    T, N, M, M2 = [], [], [], []
    for k in range(n):
        a = phase + TAU * k / n + rnd.uniform(-jag, jag) * TAU / n
        rr = r * (1 + rnd.uniform(-jag, jag) * 0.5)
        T.append(add((math.cos(a) * rr, y0 - droop * (1 + rnd.uniform(-jag, jag)), math.sin(a) * rr * sq)))
        b = phase + TAU * (k + 0.5) / n
        N.append(add((math.cos(b) * r * notch, y0 + notch_up, math.sin(b) * r * notch * sq)))
        if mid is not None:
            M.append(add((math.cos(a) * r * mid, y0 + hh * mid_h + mid_out, math.sin(a) * r * mid * sq)))
        if mid2 is not None:
            M2.append(add((math.cos(a + math.pi / n) * r * mid2, y0 + hh * mid2_h, math.sin(a + math.pi / n) * r * mid2 * sq)))
    top = add((0.0, y1 + apex_up, 0.0)); bot = add((0.0, y0 + hh * under, 0.0))
    for k in range(n):
        k1 = (k + 1) % n
        if mid is not None:
            F += [(T[k], N[k], M[k]), (N[k], M[k1], M[k]), (N[k], T[k1], M[k1])]
            if mid2 is not None: F += [(M[k], M[k1], M2[k]), (M2[k], M[k1], M2[k1]), (M2[k], M2[k1], top)]
            else: F += [(M[k], M[k1], top)]
        else:
            F += [(T[k], N[k], top), (N[k], T[k1], top)]
        F += [(N[k], T[k], bot), (T[k1], N[k], bot)]
    o = mesh_from(name, V, F, m)
    weld(o, recalc=True)
    return o


def hard(o, angle=55):
    """smooth shading with hard edges past angle (hems, rims)"""
    for p in o.data.polygons: p.use_smooth = True
    if hasattr(o.data, 'use_auto_smooth'):
        o.data.use_auto_smooth = True; o.data.auto_smooth_angle = math.radians(angle)
    return o


def ribbed(name, m, pts, radii, ribs=5, groove=0.14, tip=0.12, phase=0.0, up=(0, 1, 0)):
    """a ribbed column along a path of game points (cactus trunks and arms): a star cross-section of 2 * ribs verts
    (crests at radius r, grooves at r * (1 - groove)), parallel-transported along the path (no twist), closed with a
    point `tip` metres past the last ring (a rounded end if the last radii shrink). open at the start"""
    P = [V3(p) for p in pts]; n = len(P)
    T = [(P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized() for i in range(n)]
    U = V3(up)
    if abs(T[0].dot(U)) > 0.9: U = V3((1, 0, 0))
    N = (U - T[0] * T[0].dot(U)).normalized()
    bm = bmesh.new(); rings = []
    k = 2 * ribs
    for i, p in enumerate(P):
        N = (N - T[i] * T[i].dot(N)).normalized(); B = T[i].cross(N)
        ring = []
        for j in range(k):
            a = phase + TAU * j / k
            rr = radii[i] * (1 - groove * (j % 2))
            ring.append(bm.verts.new(gv(*(p + (N * math.cos(a) + B * math.sin(a)) * rr))))
        rings.append(ring)
    for A, Bv in zip(rings, rings[1:]):
        for j in range(k):
            jj = (j + 1) % k
            bm.faces.new((A[j], A[jj], Bv[jj], Bv[j]))
    if tip is not None:
        c = bm.verts.new(gv(*(P[-1] + T[-1] * tip)))
        R = rings[-1]
        for j in range(k): bm.faces.new((R[j], R[(j + 1) % k], c))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    for f in o.data.polygons: f.use_smooth = True
    return o


def flower(name, m, c, r, n=5, cup=0.03, tilt=(0.0, 0.0), uvc=(0.5, 0.5), uvt=(0.5, 0.5), inner=0.42):
    """a little star flower: a fan of 2n triangles from its heart (uv uvc) to n petal tips (uv uvt), the notches
    between them at `inner` of the radius; the tips lift `cup` (a cupped bloom). tilt = (x, z) lean of its face"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    C = V3(c)
    nx, nz = tilt
    def pt(a, rr, lift):
        q = V3((math.cos(a) * rr, lift, math.sin(a) * rr))
        q.y += q.x * nx + q.z * nz
        return C + q
    ctr = bm.verts.new(gv(*(C + V3((0, 0.012, 0)))))
    ring = []
    for k in range(2 * n):
        a = TAU * k / (2 * n)
        tipk = k % 2 == 0
        ring.append((bm.verts.new(gv(*pt(a, r if tipk else r * inner, cup if tipk else cup * 0.3))), tipk))
    dv = 0.08
    for k in range(2 * n):
        (v0, t0), (v1, t1) = ring[k], ring[(k + 1) % (2 * n)]
        f = bm.faces.new((ctr, v1, v0))
        for lp in f.loops:
            if lp.vert is ctr: lp[uvl].uv = uvc
            else:
                tk = t0 if lp.vert is v0 else t1
                lp[uvl].uv = (uvt[0], uvt[1] + dv) if tk else ((uvc[0] + uvt[0]) / 2, uvc[1] - dv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0: f.normal_flip()
    o = _obj(name, bm, m)
    for f in o.data.polygons: f.use_smooth = True
    return o


# ------------------------------------------------------------ finishing: AO, root, QA, sheet
def finish_prop(fid, lod0, lod1, meta, ao0=0.6, ao1=0.6):
    for o in lod0 + lod1:
        bake_tf(o); weld(o)
        for p in o.data.polygons: p.use_smooth = True
    bake_ao(lod0, dist=ao0)
    bake_ao(lod1, dist=ao1)
    root = prop_finish(fid, lod0, lod1, meta)
    t0, t1 = prop_stats(root)
    m0 = sorted({s.material.name for o in lod0 for s in o.material_slots if s.material})
    m1 = sorted({s.material.name for o in lod1 for s in o.material_slots if s.material})
    print(f'JF_TREE {fid}: lod0 {t0} tris {m0} | lod1 {t1} tris {m1} | meta {json.dumps(meta)}')
    root['jf_stats'] = json.dumps({'t0': t0, 't1': t1, 'm0': m0, 'm1': m1})
    if '--qa' in ARGV: qa(fid, lod0, lod1)
    return root


def qa(fid, lod0, lod1):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    for tag, objs in (('lod0', lod0), ('lod1', lod1)):
        res = qa_check.run(objects=[p.name for p in objs], profile='game', eps=0.001, tol=0.003)
        print('QA_PASS', fid, tag, res.get('pass'))
        for k in ('errors', 'warnings'):
            for e in res.get(k, []): print('QA_' + k.upper()[:-1], fid, tag, e)
        for n, mt in res.get('objects', {}).items():
            bad = {k: v for k, v in mt.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts', 'uv_zero_area_faces', 'ngons') and v}
            print('QA_PART', fid, tag, n, mt.get('tris'), 'islands', mt.get('islands'), bad)


def preview(root, tint=0x3c8c32):
    """sheet only (after the export): multiply the baked AO into every material like the game does, and give the tint
    material a sample colour, so the sheet shows what the game draws"""
    done = set()
    for o in root.children_recursive:
        if o.type != 'MESH': continue
        for sl in o.material_slots:
            m = sl.material
            if not m or m.name in done or not m.node_tree: continue
            done.add(m.name)
            nt = m.node_tree; b = nt.nodes['Principled BSDF']; bc = b.inputs['Base Color']
            src = bc.links[0].from_socket if bc.is_linked else None
            col = tuple(bc.default_value)
            ao = nt.nodes.new('ShaderNodeVertexColor'); ao.layer_name = 'AO'
            mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs[0].default_value = 1.0
            if src: nt.links.new(src, mx.inputs[6])
            else: mx.inputs[6].default_value = col
            nt.links.new(ao.outputs['Color'], mx.inputs[7])
            out = mx.outputs[2]
            if m.name == 'tint':
                m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; m2.blend_type = 'MULTIPLY'
                m2.inputs[0].default_value = 1.0; nt.links.new(out, m2.inputs[6]); m2.inputs[7].default_value = srgb(tint)
                out = m2.outputs[2]
            nt.links.new(out, bc)


def sheet_lods(root, fid, gap=1.0, **kw):
    """the turnaround sheet with lod1 stood beside lod0 (to its +x), so both are reviewed in every view"""
    st = json.loads(root['jf_stats'])
    e = next((c for c in root.children if c.name.startswith('lod1')), None)
    lo, hi = bbox([c for c in root.children if c.type == 'MESH'])
    if e: e.location.x = (hi.x - lo.x) + gap
    note = f"| LOD0 {st['t0']} / LOD1 {st['t1']} TRIS, {len(st['m0'])} + {len(st['m1'])} MATS"
    sheet(root, fid, extra_note=note, **kw)
    if e: e.location.x = 0


SHEET_KW = {}
PROPS = []
def prop(fn):
    PROPS.append(fn)
    return fn


# ============================================================ p_lollipop
@prop
def lollipop():
    # built at h 6.5 (9.2 m), near the median copy (the maps plant them at h 2.2..11, most in the woodland belts at
    # 5..8.5): the box crown is 2.7 m on every copy, so the closer the reference, the less a copy's fit stretches it
    H = 6.5; TOP = H + 2.7  # trunk to h, crown boxes h..h+2.7
    D = H - 4.5  # (the crown and the fork, laid out at h 4.5 first, ride up by this)
    # bark: tiles round the trunk (u), the top 80 rows run up it (v fitted), the bottom 16 rows are the tag
    W, Hh, RB = 64, 96, 80
    px = np.zeros((Hh, W, 3), np.float32)
    paint_bark(px, 0, RB, 0, W, 0x6e4a2e, 0x2e1c10, 0x9a7454, 11, grooves=9, wob=1.4, knots=4)
    def tagpx():  # an aluminium city tree tag, rows 80..95, columns 8..55
        r0, c0, c1 = RB, 8, 56
        rng = np.random.default_rng(3)
        px[r0:Hh, :] = hexrgb(0xc2c8d0)[None, None] * (0.92 + 0.12 * speckle(16, W, rng))[:, :, None]
        px[r0, c0:c1] = px[Hh - 1, c0:c1] = hexrgb(0x6a727c); px[r0:Hh, c0] = px[r0:Hh, c1 - 1] = hexrgb(0x6a727c)
        text_px(px, 'TREE', c0 + 1, r0 + 1, 2, 0x16181c)
    tagpx()
    bark = mat('lp_bark', 0xffffff, rough=0.6, clearcoat=0.15, tex=img('lp_bark_t', px))
    tp = np.zeros((32, 32, 3), np.float32)
    paint_leaf(tp, 0, 32, 0, 32, 0xf4f4f4, 5, var=0.05, dark=0.87, light=1.0, dots=0.0, spots=0.12, mottle=0.04)
    tint = mat('tint', 0xffffff, rough=0.42, clearcoat=0.38, tex=img('lp_tint_t', tp))
    cull(bark, tint)
    BARKR, VFIT = (0, RB, 0, W), ((0, 1), (0.0, H + 1.2))

    # ---- trunk: a seven-sided stem with three root buttresses, the leader + two limbs forking up into the crown
    prof = [(0.43, 0.0), (0.32, 0.25), (0.27, 0.9), (0.245, 3.6), (0.2, H + 0.6)]  # (the leader runs well up into the crown)
    trunk = lathe(prof, (0, 0, 0), bark, seg=7, axis='y', name='lp_trunk', cap=False)
    bake_tf(trunk)
    def flare(p):
        if p.y > 0.5: return p
        a = math.atan2(p.z, p.x); k = (0.5 - p.y) / 0.5
        r = math.hypot(p.x, p.z)
        s = (r + 0.12 * k * max(0.0, math.cos(1.5 * (a - 0.4) * 2)) ** 2) / max(r, 1e-6)
        return V3((p.x * s, p.y, p.z * s))
    edit_verts(trunk, flare)
    jit(trunk, 0.01, 3, keep_y_below=0.01)
    # turn the trunk so one of its seven flats faces the front (-z): the tag sits flat on it
    trunk.data.transform(Matrix.Rotation(math.radians(282.857 - 270), 4, 'Z'))
    limbs = []
    for k, (pts, rr) in enumerate((
            ([(0.0, 3.7 + D, 0.0), (0.34, 4.4 + D, 0.1), (0.74, 5.3 + D, 0.22)], [0.15, 0.115, 0.08]),
            ([(0.0, 3.95 + D, 0.0), (-0.3, 4.6 + D, -0.28), (-0.57, 5.4 + D, -0.56)], [0.14, 0.105, 0.075]))):
        limbs.append(bake_tf(sweep(pts, rr, bark, seg=4, name=f'lp_limb{k}', cap=False)))
    ap = 0.27 * math.cos(math.pi / 7)  # the flat's distance from the axis at the tag's height
    tag = bake_tf(box((0.2, 0.067, 0.04), (0.0, 1.62, -(ap + 0.003)), bark, name='lp_tag'))
    kill_faces(tag, lambda c, n: n.z > 0.9)  # its back is in the bark
    for o in [trunk] + limbs: uv_region(o, BARKR, W, Hh, proj='cyl', ppm=12, umode='tile', vmode='fit', arc_r=0.27, fit=VFIT)
    uv_decal(tag, (RB, Hh, 8, 56), W, Hh, (0, 1.62, -0.28), (0.2, 0.067), plain=(RB + 2, Hh - 2, 2, 6))

    # ---- crown: a clipped ball of leaf clusters: a core with glossy puffs sunk into it (only their outer skin kept)
    lumps = puff_crown('lp_l', tint, (0, 5.75 + D, 0), (1.42, 1.05, 1.42), [(-0.15, 5, 10), (0.5, 4, 50), (1.0, 1, 0)], seed=4,
                       rad=(0.88, 1.01), depth=0.5, seg=6, rings=4)
    crown = join(lumps, 'lp_crown'); bake_tf(crown)
    fit_box([crown], V3((-1.8, H, -1.8)), V3((1.8, TOP, 1.8)))
    uv_box(crown, 1.2)
    trunk_all = join([trunk] + limbs + [tag], 'lp_trunk')

    # ---- lod1: a hand-made blob on the crown's own outline + a three-sided trunk
    ys = [4.8 + D, 5.55 + D, 6.6 + D]
    rr = profile([crown], ys, 0.2)
    far_crown = blob('lp_far_crown', tint, [(ys[0], rr[0] * 0.9, 6, 0), (ys[1], rr[1] * 0.96, 6, 30), (ys[2], rr[2] * 0.92, 5, 50)],
                     bottom=(0, H + 0.05, 0), top=(0, TOP, 0), noise=0.05, seed=3)
    fit_box([far_crown], V3((-1.8, H, -1.8)), V3((1.8, TOP, 1.8)))
    uv_box(far_crown, 1.2)
    far_trunk = lathe([(0.3, 0.0), (0.22, H + 0.5)], (0, 0, 0), bark, seg=3, axis='y', name='lp_far_trunk', cap=False)
    bake_tf(far_trunk)
    uv_region(far_trunk, BARKR, W, Hh, proj='cyl', ppm=12, umode='tile', vmode='fit', arc_r=0.27, fit=VFIT)
    meta = {'id': 'lollipop', 'lod': 60, 'tint': True, 'box': [[-1.8, 0, -1.8], [1.8, TOP, 1.8]], 'ref': {'h': H},
            'top': ['tint']}  # (if the fit learns it: tint parts keep their height and ride the copy's top, the rest stretches)
    return finish_prop('p_lollipop', [trunk_all, crown], [far_trunk, far_crown], meta, ao0=0.7, ao1=0.7)


# ============================================================ p_conifer
@prop
def conifer():
    Hh = 6.0
    y0 = 2 + ((Hh * 7.31) % 0.4)  # = 2.26, as conifer() works it out
    TOP = y0 + Hh
    W, H = 64, 64  # atlas: bark | hedge green | lime, full-height stripes (v tiles)
    px = np.zeros((H, W, 3), np.float32)
    paint_bark(px, 0, H, 0, 16, 0x6e4a2e, 0x2e1c10, 0x9a7454, 21, grooves=3, wob=1.0, knots=1)
    paint_needles(px, 0, H, 16, 40, 0x326e2d, 22, glint=0x5aa84a)
    paint_needles(px, 0, H, 40, 64, 0x96f01e, 23, dash=0.72, glint=0xd8ff80)
    m = mat('cf_tree', 0xffffff, rough=0.44, clearcoat=0.32, tex=img('cf_tree_t', px))
    cull(m)
    BARK, GREEN, LIME = (0, H, 0, 16), (0, H, 16, 40), (0, H, 40, 64)
    rnd = random.Random(6)
    parts = []
    trunk = lathe([(0.34, 0.0), (0.27, 0.3), (0.22, 1.6), (0.17, y0 + 0.55)], (0, 0, 0), m, seg=7, axis='y', name='cf_trunk', cap=False)
    bake_tf(trunk); jit(trunk, 0.008, 2, keep_y_below=0.01)
    uv_region(trunk, BARK, W, H, proj='cyl', ppm=14, umode='fold', vmode='tile', arc_r=0.25)
    parts.append(trunk)
    widths = [4.2 - i * 0.95 for i in range(4)]
    for i, w in enumerate(widths):
        ya, yb = y0 + i * Hh / 4, y0 + (i + 1) * Hh / 4
        n = (12, 11, 9, 7)[i]
        last = i == 3
        t = tier(f'cf_tier{i}', m, ya + 0.12, yb, w / 2 * 1.15, n, phase=(0 if i == 0 else rnd.uniform(0, TAU)), notch=0.84, notch_up=0.16,
                 droop=0.14, mid=0.62, mid_h=0.46, under=0.3, apex_up=(0.0 if last else 0.75), rnd=rnd, jag=0.15 if i else 0.0)
        uv_region(t, LIME if i % 2 else GREEN, W, H, proj='up', ppm=10, umode='fold', vmode='tile')
        parts.append(t)
    tree = join(parts, 'cf_tree'); bake_tf(tree); hard(tree, 50)
    fit_box([tree], V3((0, 0, 0)), V3((0, TOP, 0)), axes=(1,))
    # ---- lod1: the four tiers as cones in their own greens (five sides at the bottom, four above, each closed underneath
    # so the apex below runs into it) + a three-sided trunk
    far = []
    for i, w in enumerate(widths):
        ya = y0 + i * Hh / 4
        yb = (TOP if i == 3 else ya + Hh / 4 + 0.6)
        c = blob(f'cf_far{i}', m, [(ya, w / 2 * (1.18 if i == 0 else 1.26), 5 if i == 0 else 4, 45 * (i % 2))], bottom=(0, ya + 0.3, 0), top=(0, yb, 0))
        uv_region(c, LIME if i % 2 else GREEN, W, H, proj='up', ppm=10, umode='fold', vmode='tile')
        far.append(c)
    ft = lathe([(0.3, 0.0), (0.2, y0 + 0.4)], (0, 0, 0), m, seg=3, axis='y', name='cf_far_trunk', cap=False); bake_tf(ft)
    uv_region(ft, BARK, W, H, proj='cyl', ppm=14, umode='fold', vmode='tile', arc_r=0.25)
    farm = join(far + [ft], 'cf_far'); bake_tf(farm); hard(farm, 50)
    fit_box([farm], V3((0, 0, 0)), V3((0, TOP, 0)), axes=(1,))
    meta = {'id': 'conifer', 'lod': 60, 'tint': False, 'box': [[-2.1, 0, -2.1], [2.1, round(TOP, 3), 2.1]], 'ref': {'h': Hh}}
    return finish_prop('p_conifer', [tree], [farm], meta, ao0=0.6, ao1=0.6)


# ============================================================ p_pine
@prop
def pine():
    Hh, W0, TW = 14.0, 4.2, 0.34  # h, the bottom tier's width, the trunk's half width (0.26..0.42 in pine())
    base = Hh * 0.34; span = Hh - base; n = 6
    TOP = Hh + 1.0  # the tip box tops out at h + 1
    W, H = 64, 64  # atlas: bark | pine | pine2
    px = np.zeros((H, W, 3), np.float32)
    paint_bark(px, 0, H, 0, 20, 0x4a3628, 0x1e140c, 0x6a5040, 31, grooves=4, wob=1.0, knots=1)
    paint_needles(px, 0, H, 20, 42, 0x1e3e2c, 32, var=0.22, glint=0x2e5a3e)
    paint_needles(px, 0, H, 42, 64, 0x163228, 33, var=0.22, glint=0x244a38)
    # rough, no coat: the game's studio reflection lit glossy needles up like snow in the night forest
    m = mat('pn_tree', 0xffffff, rough=0.92, clearcoat=0.0, tex=img('pn_tree_t', px))
    cull(m)
    BARK, PA, PB = (0, H, 0, 20), (0, H, 20, 42), (0, H, 42, 64)
    rnd = random.Random(9)
    trunk = lathe([(TW * 1.25, 0.0), (TW, 0.35), (TW * 0.8, base + 0.6)], (0, 0, 0), m, seg=6, axis='y', name='pn_trunk', cap=False)
    bake_tf(trunk); jit(trunk, 0.01, 4, keep_y_below=0.01)
    uv_region(trunk, BARK, W, H, proj='cyl', ppm=10, umode='fold', vmode='tile', arc_r=0.3)
    parts = [trunk]
    for i in range(n):
        k = i / n; w = W0 * (1 - k * 0.82); y = base + k * span
        ya = y + span / n * 0.62 - span / n * 0.65  # the box's bottom
        yb = y + span / n * 0.62 + span / n * 0.65
        last = i == n - 1
        nt = (8, 8, 8, 7, 7, 6)[i]
        t = tier(f'pn_tier{i}', m, ya + 0.25, (TOP if last else yb), w / 2 * 1.1, nt, phase=-0.7 * i, notch=0.72, notch_up=0.3,
                 droop=0.3, mid=(0.5 if i < 3 else None), mid_h=0.36, under=0.22, apex_up=(0.0 if last else 0.35),
                 sq=0.97, rnd=rnd, jag=0.22)
        uv_region(t, PB if (i % 3 == 2) else PA, W, H, proj='up', ppm=9, umode='fold', vmode='tile')
        parts.append(t)
    tree = join(parts, 'pn_tree'); bake_tf(tree); hard(tree, 50)
    fit_box([tree], V3((0, 0, 0)), V3((0, TOP, 0)), axes=(1,))
    # ---- lod1 (24): two stacked pentagonal cones + a three-sided trunk
    c1 = blob('pn_far0', m, [(base, W0 / 2 * 1.08, 5, 0)], bottom=(0, base + 0.5, 0), top=(0, base + span * 0.62, 0))
    c2 = blob('pn_far1', m, [(base + span * 0.42, W0 * 0.33, 4, 45)], bottom=(0, base + span * 0.42 + 0.4, 0), top=(0, TOP, 0))
    for c in (c1, c2): uv_region(c, PA, W, H, proj='up', ppm=9, umode='fold', vmode='tile')
    ft = lathe([(TW * 1.2, 0.0), (TW * 0.8, base + 0.6)], (0, 0, 0), m, seg=3, axis='y', name='pn_far_trunk', cap=False); bake_tf(ft)
    uv_region(ft, BARK, W, H, proj='cyl', ppm=10, umode='fold', vmode='tile', arc_r=0.3)
    farm = join([c1, c2, ft], 'pn_far'); bake_tf(farm); hard(farm, 50)
    fit_box([farm], V3((0, 0, 0)), V3((0, TOP, 0)), axes=(1,))
    # box: pineBoxes() at h 14, w0 4.2, n 6, measured like propOf() in world axes and averaged over the tiers' random
    # yaw (5.43 across; 5.07 if the fit were measured in the tiers' own frame)
    meta = {'id': 'pine', 'lod': 45, 'tint': False, 'box': [[-2.714, 0, -2.714], [2.714, TOP, 2.714]], 'ref': {'h': Hh, 'w0': W0, 'trunk': 2 * TW}}
    return finish_prop('p_pine', [tree], [farm], meta, ao0=0.8, ao1=0.8)


SHEET_KW['pine'] = {'exposure': 1.2, 'tint': 0xffffff}


# ============================================================ p_birch
def birch_bark_px(px, r0, r1, W, seed=41):
    """silver birch bark into rows r0..r1 (the trunk once round, ground at the bottom): cream white, black lenticel
    dashes, dark chevrons under the branch scars, a black fissured foot, and two birch eyes facing the front (u 0.25)"""
    rng = np.random.default_rng(seed)
    h = r1 - r0
    reg = hexrgb(0xdcd8ca)[None, None] * (0.93 + 0.1 * speckle(h, W, rng)[:, :, None]) * (0.95 + 0.08 * vnoise(h, W, 8, 8, rng))[:, :, None]
    blk = hexrgb(0x1e1c1a)
    for k in range(int(h * W / 30)):  # lenticels: thin black dashes, more of them low down
        y = int(h * (1 - rng.random() ** 1.6)); x = int(rng.integers(0, W)); L = int(rng.integers(2, 6))
        for i in range(L): reg[min(y, h - 1), (x + i) % W] = blk * rng.uniform(0.8, 1.3)
    for k in range(7):  # chevrons under branch scars
        cy, cx = int(rng.uniform(0.15, 0.85) * h), int(rng.integers(0, W))
        for i in range(-4, 5):
            for t in range(2):
                reg[min(h - 1, cy + abs(i) // 2 + t), (cx + i) % W] = blk
    foot = int(h * 0.09)  # the black fissured foot of an old birch
    for y in range(h - foot, h):
        k = (y - (h - foot)) / foot
        for x in range(W):
            if rng.random() < 0.35 + 0.6 * k: reg[y, x] = hexrgb(0x2a2622) * rng.uniform(0.8, 1.25)
    for ex in (0.25 - 0.085, 0.25 + 0.085):  # the eyes: dark almonds with a pale lid line and a glint, at 2 m on the front
        cx, cy = ex * W, h * (1 - 2.0 / 9.3)
        for y in range(-2, 3):
            for x in range(-5, 6):
                d = (x / 4.2) ** 2 + (y / 1.7) ** 2
                if d <= 1.0: reg[int(round(cy + y)), int(round(cx + x)) % W] = blk * (0.75 if d > 0.55 else 1.0)
        for x in range(-3, 4): reg[int(round(cy)) - 2, int(round(cx + x)) % W] = hexrgb(0x8a8478)
        reg[int(round(cy)), int(round(cx)) % W] = hexrgb(0xd8d0bc)  # a glint
    px[r0:r1] = np.clip(reg, 0, 1)


@prop
def birch():
    Hh = 9.0
    W, H = 64, 256  # atlas: rows 0..239 the bark (once round, the trunk's height: ~26 rows a metre), 240..255 leaves
    px = np.zeros((H, W, 3), np.float32)
    birch_bark_px(px, 0, 240, W)
    paint_leaf(px, 240, 256, 0, W, 0x5c6e34, 42, var=0.2, spots=0.12, dots=0.06, light=1.35)
    m = mat('bc_tree', 0xffffff, rough=0.85, clearcoat=0.0, tex=img('bc_tree_t', px))  # (night forest: see the pine)
    cull(m)
    BARK, LEAF = (0, 240, 0, W), (240, 256, 0, W)
    def lean(p):  # birches lean and wander: the foot stays in the collision box
        k = p.y / Hh
        return V3((p.x + 0.26 * k * k + 0.05 * math.sin(k * 5.0), p.y, p.z - 0.08 * k * k + 0.04 * math.sin(k * 3.0 + 1)))
    trunk = lathe([(0.24, 0.0), (0.2, 0.3), (0.18, 2.0), (0.15, 4.5), (0.11, 6.8), (0.07, 8.4), (0.03, Hh)], (0, 0, 0), m, seg=7, axis='y', name='bc_trunk', cap=False)
    bake_tf(trunk)
    trunk.data.transform(Matrix.Rotation(math.radians(282.857 - 270), 4, 'Z'))  # a flat to the front (the eyes)
    # once round (u 0..1 from +x toward -z, so the front is u = 0.25), ground..top fitted into the bark rows
    me = trunk.data; uv = (me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')).data
    _, _, v0, v1 = _region(BARK, W, H)
    for poly in me.polygons:
        us = []
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co; g = (co.x, co.z, -co.y)
            us.append(((math.atan2(-g[2], g[0]) / TAU) % 1.0, g[1]))
        ref = us[0][0]
        for li, (u, y) in zip(poly.loop_indices, us):
            u += round(ref - u)
            uv[li].uv = (u, v0 + y / (Hh + 0.3) * (v1 - v0))
    edit_verts(trunk, lean)
    parts = [trunk]
    # three weeping clumps (birch(): 2.4 x 2.0, 1.9 x 1.6, 1.4 x 1.2, each 1.1 tall, at 0.62 / 0.75 / 0.88 h), offset side to side
    rnd = random.Random(8)
    clumps = [((0.42, 0.62 * Hh, -0.18), 2.4, 2.0, 0.3), ((-0.3, 0.75 * Hh, 0.26), 1.9, 1.6, 1.4), ((0.3, 0.88 * Hh, 0.06), 1.4, 1.2, 2.6)]
    for i, (c, w, d, yaw) in enumerate(clumps):
        cy = c[1]; ya, yb = cy - 0.55, cy + 0.55
        n = (9, 8, 7)[i]
        t = tier(f'bc_clump{i}', m, ya + 0.2, yb, w / 2, n, phase=yaw, notch=0.88, notch_up=0.12, droop=0.24, mid=0.84, mid_h=0.42,
                 mid2=0.5, mid2_h=0.84, under=0.2, apex_up=0.0, sq=d / w, rnd=rnd, jag=0.3)
        sway = lean(V3((0, cy, 0))) - V3((0, cy, 0))  # (tier() builds at its own height: only move it sideways)
        t.data.transform(Matrix.Translation(gv(*(sway + V3((c[0], 0, c[2]))))))
        uv_region(t, LEAF, W, H, proj='up', ppm=12, umode='tile', vmode='fold')
        parts.append(t)
        # the branch that holds it up
        a = lean(V3((0, cy - 1.0, 0))); b = lean(V3((0, cy, 0))) + V3((c[0] * 0.9, -0.05, c[2] * 0.9))
        mid_ = (a + b) / 2 + V3((0, 0.15, 0))
        br = sweep([tuple(a), tuple(mid_), tuple(b)], [0.06, 0.045, 0.03], m, seg=4, name=f'bc_branch{i}', cap=False)
        bake_tf(br)
        uv_region(br, (222, 238, 0, W), W, H, proj='box', ppm=20, umode='tile', vmode='fold')  # the dark foot rows: dark twigs
        parts.append(br)
    tree = join(parts, 'bc_tree'); bake_tf(tree); hard(tree, 55)
    # ---- lod1: three squashed bipyramids + a three-sided trunk
    far = []
    for i, (c, w, d, yaw) in enumerate(clumps):
        cy = c[1]; q = lean(V3((0, cy, 0))) + V3((c[0], 0, c[2]))
        far.append(blob(f'bc_far{i}', m, [(cy - 0.1, w / 2, 5, math.degrees(yaw), q.x, q.z, 1.0, d / w)], bottom=(q.x, cy - 0.5, q.z), top=(q.x, cy + 0.58, q.z)))
    for o in far: uv_region(o, LEAF, W, H, proj='up', ppm=12, umode='tile', vmode='fold')
    ft = lathe([(0.2, 0.0), (0.05, Hh)], (0, 0, 0), m, seg=3, axis='y', name='bc_far_trunk', cap=False); bake_tf(ft)
    ft.data.transform(Matrix.Rotation(math.radians(30), 4, 'Z'))
    uv_region(ft, (20, 200, 4, 40), W, H, proj='cyl', ppm=10, umode='fold', vmode='fit', arc_r=0.2, fit=((0, 1), (0, 12)))
    edit_verts(ft, lean)
    farm = join(far + [ft], 'bc_far'); bake_tf(farm); hard(farm, 55)
    meta = {'id': 'birch', 'lod': 50, 'tint': False, 'box': [[-1.46, 0, -1.46], [1.46, Hh, 1.46]], 'ref': {'h': Hh}}  # (birchBoxes() at h 9, averaged)
    return finish_prop('p_birch', [tree], [farm], meta, ao0=0.6, ao1=0.6)


SHEET_KW['birch'] = {'exposure': 0.3, 'tint': 0xffffff}


# ============================================================ p_deadtree
@prop
def deadtree():
    Hh = 8.0
    W, H = 64, 64  # atlas: grey bark (columns 0..47, v tiles) | bleached broken wood (48..63)
    px = np.zeros((H, W, 3), np.float32)
    paint_bark(px, 0, H, 0, 48, 0x76726a, 0x3a3832, 0xa8a49a, 51, grooves=7, wob=1.6, knots=3, var=0.2)
    paint_bark(px, 0, H, 48, 64, 0xc8bea4, 0x8a7e66, 0xe8e0cc, 52, grooves=3, wob=0.6, knots=0, var=0.1)
    m = mat('dt_tree', 0xffffff, rough=0.9, clearcoat=0.0, tex=img('dt_tree_t', px))  # (night forest: see the pine)
    cull(m)
    BARK, PALE = (0, H, 0, 48), (0, H, 48, 64)
    def twist(p):  # a slow twist and a lean: dead wood dries crooked
        k = p.y / Hh
        a = 0.55 * k
        x, z = p.x * math.cos(a) - p.z * math.sin(a), p.x * math.sin(a) + p.z * math.cos(a)
        return V3((x + 0.18 * k * k - 0.06 * math.sin(k * 7), p.y, z + 0.1 * math.sin(k * 4.0)))
    prof = [(0.44, 0.0), (0.33, 0.28), (0.29, 1.0), (0.26, 3.0), (0.22, 5.0), (0.18, 6.8), (0.15, Hh - 0.45)]
    trunk = lathe(prof, (0, 0, 0), m, seg=7, axis='y', name='dt_trunk', cap=False)
    bake_tf(trunk)
    def roots(p):
        if p.y > 0.45: return p
        a = math.atan2(p.z, p.x); k = (0.45 - p.y) / 0.45; r = math.hypot(p.x, p.z)
        s_ = (r + 0.16 * k * max(0.0, math.cos(2.0 * (a - 1.1))) ** 3 + 0.08 * k * max(0.0, math.cos(3 * (a + 0.3)))) / max(r, 1e-6)
        return V3((p.x * s_, p.y, p.z * s_))
    edit_verts(trunk, roots)
    uv_region(trunk, BARK, W, H, proj='cyl', ppm=11, umode='fold', vmode='tile', arc_r=0.3)
    # the splintered top: the last ring jagged up into spikes, a broken crater inside
    bm = bmesh.new(); top_r = 0.15; yb = Hh - 0.45
    ring = []
    for k in range(7):
        a = TAU * k / 7
        ring.append(bm.verts.new(gv(math.cos(a) * top_r, yb, math.sin(a) * top_r)))
    spikes = [0.45, 0.12, 0.3, 0.05, 0.38, 0.18, 0.08]
    tips = [bm.verts.new(gv(math.cos(TAU * (k + 0.5) / 7) * top_r * 0.85, yb + spikes[k], math.sin(TAU * (k + 0.5) / 7) * top_r * 0.85)) for k in range(7)]
    pit = bm.verts.new(gv(0.02, yb - 0.06, 0.0))
    for k in range(7):
        k1 = (k + 1) % 7
        bm.faces.new((ring[k], ring[k1], tips[k]))  # outside of the splinter
        bm.faces.new((tips[k], ring[k1], pit)); bm.faces.new((ring[k], tips[k], pit))  # inside, down into the crater
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    crown = _obj('dt_top', bm, m)
    uv_region(crown, PALE, W, H, proj='box', ppm=30, umode='fold', vmode='tile')
    parts = [trunk, crown]
    # five branches (deadTree(): at h * (0.4 + 0.12 i), out 1.2..3 m, then an elbow up 0.9 m), spread round the trunk
    lens = [2.35, 1.75, 2.1, 1.55, 1.5]
    for i in range(5):
        y = Hh * (0.4 + i * 0.12); L = lens[i]; a = 0.7 + i * 2.39996
        d = V3((math.cos(a), 0, math.sin(a))); sd = V3((-d.z, 0, d.x))
        r0 = 0.15 - i * 0.014
        p0 = d * 0.05 + V3((0, y - 0.1, 0)); p1 = d * (L * 0.42) + V3((0, y + 0.06, 0)) + sd * 0.14
        p2 = d * (L * 0.88) + V3((0, y + 0.02, 0)); p3 = d * L + V3((0, y + 0.3, 0)) + sd * -0.05
        p4 = d * (L + 0.04) + V3((0, y + 0.9, 0))
        if i in (1, 3):  # one more elbow on the way out
            p1 = d * (L * 0.38) + V3((0, y + 0.32, 0)) + sd * -0.1
        br = sweep([tuple(q) for q in (p0, p1, p2, p3, p4)], [r0, r0 * 0.72, r0 * 0.55, r0 * 0.45, r0 * 0.26], m, seg=5, name=f'dt_branch{i}', cap=True)
        bake_tf(br)
        kill_faces(br, lambda c, n, p0=p0: (c - p0).length < 0.05)  # the cap inside the trunk
        uv_region(br, BARK, W, H, proj='box', ppm=14, umode='fold', vmode='tile')
        parts.append(br)
        if i % 2 == 0:  # a finger off the elbow: too many elbows
            q0 = p3; q1 = p3 + d * 0.28 + sd * 0.18 + V3((0, 0.32, 0)); q2 = q1 + d * 0.06 + V3((0, 0.28, 0))
            f = sweep([tuple(q0), tuple(q1), tuple(q2)], [r0 * 0.36, r0 * 0.26, r0 * 0.14], m, seg=3, name=f'dt_finger{i}', cap=True)
            bake_tf(f); uv_region(f, BARK, W, H, proj='box', ppm=14, umode='fold', vmode='tile')
            parts.append(f)
    tree = join(parts, 'dt_tree'); bake_tf(tree)
    edit_verts(tree, twist)
    hard(tree, 60)
    # ---- lod1: a three-sided trunk, each branch one prism from the trunk to the top of its elbow
    far = []
    ft = lathe([(0.36, 0.0), (0.15, Hh)], (0, 0, 0), m, seg=3, axis='y', name='dt_far_trunk', cap=False); bake_tf(ft)
    uv_region(ft, BARK, W, H, proj='cyl', ppm=11, umode='fold', vmode='tile', arc_r=0.3)
    far.append(ft)
    for i in range(5):
        y = Hh * (0.4 + i * 0.12); L = lens[i]; a = 0.7 + i * 2.39996
        d = V3((math.cos(a), 0, math.sin(a)))
        r0 = 0.15 - i * 0.014
        b = sweep([tuple(d * -0.05 + V3((0, y - 0.15, 0))), tuple(d * L + V3((0, y + 0.85, 0)))], [r0 * 1.1, r0 * 0.45], m, seg=3, name=f'dt_far_b{i}', cap=False)
        bake_tf(b); uv_region(b, BARK, W, H, proj='box', ppm=14, umode='fold', vmode='tile')
        far.append(b)
    farm = join(far, 'dt_far'); bake_tf(farm); edit_verts(farm, twist); hard(farm, 60)
    meta = {'id': 'deadtree', 'lod': 50, 'tint': False, 'box': [[-1.675, 0, -1.675], [1.675, Hh, 1.675]], 'ref': {'h': Hh}}  # (deadTreeBoxes() at h 8, averaged)
    return finish_prop('p_deadtree', [tree], [farm], meta, ao0=0.5, ao1=0.5)


SHEET_KW['deadtree'] = {'exposure': 0.2}


# ============================================================ p_palm
def palm_px(W, H, seed=61):
    """palm atlas 64 x 64: columns 0..23 the trunk's rings (two woods like the boxes, a dark scar line between, v
    tiles), 24..55 one whole frond (u across, v base to tip: green midrib, leaflets, green to lime), 56..63 coconut
    brown (rows 0..31) and the heart's fibre (rows 32..63)"""
    rng = np.random.default_rng(seed)
    px = np.zeros((H, W, 3), np.float32)
    # trunk: two bands per tile (each 32 rows = one segment), a dark scar ring, fibres
    for y in range(H):
        band = (y // 32) % 2; k = (y % 32) / 32
        base = hexrgb(0xa06e3c if band else 0xc8a064)
        shade = 0.82 + 0.25 * k  # each drum darker at its foot, lighter under the next ring
        for x in range(24):
            px[y, x] = base * shade * (0.9 + 0.2 * rng.random())
        if y % 32 in (0, 1): px[y, :24] = hexrgb(0x4a3018) * (0.9 + 0.2 * rng.random())
        if y % 32 == 2: px[y, :24] = hexrgb(0xe0c08a)
    for x in range(1, 24, 3): px[:, x] *= 0.86  # vertical fibre lines
    # frond: u across (0 = left edge, 0.5 = midrib), v base -> tip
    for y in range(H):
        t = 1 - y / (H - 1)  # 0 at the base (bottom rows), 1 at the tip
        for x in range(24, 56):
            u = (x - 24 + 0.5) / 32; d = abs(u - 0.5) * 2
            g = hexrgb(0x2e8a2a) * (1 - t) + hexrgb(0x8ee01e) * t
            leaflet = ((y * 0.9 + d * 9.0) % 4.0) < 1.2  # diagonal leaflet gaps running out from the midrib
            c = g * (0.78 if leaflet else 1.0) * (0.92 + 0.12 * rng.random())
            if d < 0.12: c = hexrgb(0xd8e070) * (0.85 + 0.15 * t)  # the yellow midrib
            if d > 0.9: c = c * 0.8
            px[y, x] = c
    px[0:32, 56:64] = hexrgb(0x6a4422)[None, None] * (0.85 + 0.3 * speckle(32, 8, rng))[:, :, None]
    px[32:64, 56:64] = hexrgb(0x6a6a2a)[None, None] * (0.8 + 0.35 * speckle(32, 8, rng))[:, :, None]
    return np.clip(px, 0, 1)


def frond(name, m, root, d, L, rise, tip_y, widths, region, W, H, fold=0.16, bend=0.0, flat=False):
    """one pinnate frond: a V-folded strip (the midrib the crest) along an arching rachis from root along direction d
    (game, horizontal) out L, rising `rise` before it droops to tip_y. widths = half widths at the stations (zigzag =
    leaflets). u across, v along: the whole frond texture once"""
    d = V3(d).normalized(); side = V3((-d.z, 0, d.x)); n = len(widths)
    y0 = root[1]
    pts = []
    for i in range(n):
        t = i / (n - 1)
        h = y0 + rise * math.sin(math.pi * min(t / 0.75, 1.0) * 0.5) * (1 - t) * 1.6 + (tip_y - y0) * t ** 1.8
        pts.append(V3(root) + d * (L * t) + side * (bend * t * t) + V3((0, h - y0, 0)))
    V, F, UV = [], [], []
    u0, u1, v0, v1 = _region(region, W, H)
    for i, (p, w) in enumerate(zip(pts, widths)):
        t = i / (n - 1)
        tang = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        sd = tang.cross(V3((0, 1, 0))).normalized() * -1
        drop = V3((0, -fold * (w / max(max(widths), 1e-6)) - 0.02, 0))
        vv = v0 + t * (v1 - v0)
        if flat:
            V += [p + sd * max(w, 0.01), p - sd * max(w, 0.01)]; UV += [(u0, vv), (u1, vv)]
        else:
            V += [p + sd * w + drop, p + V3((0, 0.01, 0)), p - sd * w + drop]
            UV += [(u0, vv), ((u0 + u1) / 2, vv), (u1, vv)]
    for i in range(n - 1):
        if flat:
            a, b = 2 * i, 2 * (i + 1)
            F += [(a, b, b + 1), (a, b + 1, a + 1)]
            continue
        a, b = 3 * i, 3 * (i + 1)
        F += [(a, b, b + 1), (a, b + 1, a + 1), (a + 1, b + 1, b + 2), (a + 1, b + 2, a + 2)]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*q)) for q in V]
    for f in F:
        try:
            face = bm.faces.new([vs[i] for i in f])
            for lp, i in zip(face.loops, f): lp[uvl].uv = UV[i]
        except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    o = _obj(name, bm, m)
    for p_ in o.data.polygons: p_.use_smooth = True
    return o


@prop
def palm():
    Hh, LX = 7.2, 0.18  # h (the median copy), the lean per segment toward +x (palm()'s lx; lz = 0: the game turns copies to their lean)
    n = max(3, round(Hh / 1.4)); seg = Hh / n
    TX = LX * n  # the crown's offset
    W, H = 64, 64
    atlas = img('pm_tree_t', palm_px(W, H))
    mt = mat('pm_trunk', 0xffffff, rough=0.5, clearcoat=0.25, tex=atlas)
    m = mat('pm_crown', 0xffffff, rough=0.46, clearcoat=0.3, tex=atlas)  # (its own material: the crown can keep its size)
    cull(mt); nocull(m)  # the fronds are single sheets
    RING, FROND, NUT, FIBRE = (0, H, 0, 24), (0, H, 24, 56), (2, 30, 57, 63), (34, 62, 57, 63)
    def axis(y):  # the trunk's centre line: leans like the boxes (lx per segment), a little bow, straight at the foot
        t = y / Hh
        return V3((TX * (t * 0.82 + 0.18 * t * t) - 0.05 * math.sin(math.pi * t), y, 0.0))
    # trunk: one ring per segment boundary, each pushed out a bit (the stacked drums), tapering 0.55 -> 0.45
    prof = [(0.33, 0.0)] + [(0.275 - 0.01 * i + 0.03, (i + 1) * seg) for i in range(n - 1)] + [(0.2, Hh + 0.15)]
    trunk = lathe(prof, (0, 0, 0), mt, seg=6, axis='y', name='pm_trunk', cap=False)
    bake_tf(trunk)
    uv_region(trunk, RING, W, H, proj='cyl', ppm=24, umode='fold', vmode='tile', arc_r=0.27)
    # v of the rings: one band per segment exactly (32 rows = seg metres)
    me = trunk.data; uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            y = me.vertices[me.loops[li].vertex_index].co.z
            uv[li].uv = (uv[li].uv[0], 1 - (y / seg) * 0.5)
    edit_verts(trunk, lambda p: p + V3((axis(p.y).x, 0, 0)))
    parts = [trunk]
    top = axis(Hh)
    # the heart: the leaf bases round the top, a fibrous lump
    heart = blob('pm_heart', m, [(Hh - 0.2, 0.42, 6, 0, top.x, 0), (Hh + 0.12, 0.66, 7, 20, top.x, 0), (Hh + 0.34, 0.4, 6, 40, top.x, 0)],
                 bottom=(top.x, Hh - 0.35, 0), top=(top.x, Hh + 0.4, 0), noise=0.08, seed=5)
    uv_region(heart, FIBRE, W, H, proj='box', ppm=30, umode='fold', vmode='fold')
    parts.append(heart)
    # three coconuts tucked under the leaves
    for k, (a, yy) in enumerate(((0.4, Hh - 0.12), (2.5, Hh - 0.2), (4.4, Hh - 0.08))):
        c = V3((top.x + 0.32 * math.cos(a), yy, 0.32 * math.sin(a)))
        nut = lump(tuple(c), (0.21, 0.24, 0.21), m, f'pm_nut{k}', seg=5, rings=3, rot=(0.3, a, 0.2))
        uv_region(nut, NUT, W, H, proj='box', ppm=40, umode='fold', vmode='fold')
        parts.append(nut)
    # eight fronds: four long ones along the axes (palm(): out to ~4 m, tips down to h - 0.6), four younger ones between
    wl = [0.07, 0.48, 0.32, 0.56, 0.34, 0.48, 0.24, 0.0]
    ws = [0.06, 0.38, 0.24, 0.42, 0.26, 0.32, 0.0]
    root = (top.x, Hh + 0.1, 0.0)
    rnd = random.Random(17)
    for k in range(8):
        a = TAU * k / 8 + (0 if k % 2 == 0 else rnd.uniform(-0.25, 0.25))  # the long ones stay on the axes (the boxes' reach)
        d = (math.cos(a), 0, math.sin(a))
        r0 = V3(root) + V3(d) * 0.25
        if k % 2 == 0:
            f = frond(f'pm_frond{k}', m, tuple(r0), d, 3.75, 0.45, Hh - 0.62, wl, FROND, W, H, fold=0.22, bend=0.25 * (1 if k % 4 else -1))
        else:
            f = frond(f'pm_frond{k}', m, tuple(r0 + V3((0, 0.1, 0))), d, rnd.uniform(2.5, 2.95), 0.3, Hh - rnd.uniform(0.1, 0.5), ws, FROND, W, H, fold=0.14, bend=rnd.uniform(-0.3, 0.3))
        parts.append(f)
    tree = join(parts, 'pm_tree'); bake_tf(tree); hard(tree, 70)
    # ---- lod1: a three-sided trunk + eight two-segment frond strips
    far = []
    ft = lathe([(0.3, 0.0), (0.2, Hh + 0.1)], (0, 0, 0), mt, seg=3, axis='y', name='pm_far_trunk', cap=False)
    bake_tf(ft)
    uv_region(ft, RING, W, H, proj='cyl', ppm=24, umode='fold', vmode='tile', arc_r=0.27)
    edit_verts(ft, lambda p: p + V3((axis(p.y).x, 0, 0)))
    far.append(ft)
    for k in range(8):
        a = TAU * k / 8; d = (math.cos(a), 0, math.sin(a))
        r0 = V3(root) + V3(d) * 0.1
        if k % 2 == 0: f = frond(f'pm_far_f{k}', m, tuple(r0), d, 3.9, 0.45, Hh - 0.62, [0.1, 0.54, 0.0], FROND, W, H, flat=True)
        else: f = frond(f'pm_far_f{k}', m, tuple(r0), d, 2.8, 0.3, Hh - 0.3, [0.08, 0.4, 0.0], FROND, W, H, flat=True)
        far.append(f)
    farm = join(far, 'pm_far'); bake_tf(farm); hard(farm, 70)
    meta = {'id': 'palm', 'lod': 70, 'tint': False, 'box': [[round(TX - 4.0, 3), 0, -4.0], [round(TX + 4.0, 3), round(Hh + 0.4, 3), 4.0]],
            'ref': {'h': Hh, 'lx': LX, 'lz': 0}, 'lean': [round(TX, 3), 0], 'crown': [round(top.x, 3), Hh, 0],
            'top': ['pm_crown']}  # (if the fit learns it: the crown keeps its height and rides the copy's top)
    return finish_prop('p_palm', [tree], [farm], meta, ao0=0.6, ao1=0.6)


# ============================================================ p_saguaro
@prop
def saguaro():
    Hh = 4.0
    W, H = 64, 32  # atlas: columns 0..47 toy green with spine dots (u folds, v tiles), 48..63 the flower (heart -> petal)
    px = np.zeros((H, W, 3), np.float32)
    rng = np.random.default_rng(71)
    px[:, :48] = hexrgb(0x2cc84a)[None, None] * (0.93 + 0.1 * speckle(H, 48, rng)[:, :, None]) * (0.95 + 0.08 * vnoise(H, 48, 4, 6, rng))[:, :, None]
    for x in range(0, 48, 4): px[:, x] *= 0.9  # faint lines down the ribs
    for k in range(70):  # areoles: little cream spine tufts
        y, x = int(rng.integers(0, H)), int(rng.integers(0, 48))
        px[y, x] = hexrgb(0xf4f0c8)
        if rng.random() < 0.4: px[(y + 1) % H, x] = hexrgb(0xc8c090)
    for x in range(48, 64):  # the flower: a gold heart out to white petals with a pink blush at the tips
        t = (x - 48) / 15
        c = hexrgb(0xffd21a) * (1 - min(1, t * 2.5)) + hexrgb(0xfff8ee) * min(1, t * 2.5)
        if t > 0.8: c = c * (1 - (t - 0.8) * 2) + hexrgb(0xffb0dc) * (t - 0.8) * 2
        px[:, x] = c
    m = mat('sg_cactus', 0xffffff, rough=0.3, clearcoat=0.35, tex=img('sg_cactus_t', px))  # (more coat washed the toy green out to mint in the game)
    cull(m)
    GREEN, FLOWER = (0, H, 0, 48), (0, H, 48, 64)
    _, _, fv0, fv1 = _region(FLOWER, W, H); fu0, fu1, _, _ = _region(FLOWER, W, H)
    fvm = (fv0 + fv1) / 2
    # the trunk (saguaro(): 0.6 x h), five ribs, a domed top
    tr = ribbed('sg_trunk', m, [(0, 0.0, 0), (0, 0.14, 0), (0, 1.1, 0), (0, 2.3, 0), (0, 3.3, 0), (0, 3.72, 0), (0, 3.93, 0)],
                [0.3, 0.33, 0.335, 0.33, 0.32, 0.275, 0.15], ribs=5, groove=0.15, tip=0.07, phase=0.3)
    # the arms: out from the trunk and up (saguaro(): right at 0.45 h out to x 0.95, up to 0.62 h + 0.45; left at 0.6 h)
    ra = ribbed('sg_armR', m, [(0.12, 1.79, 0), (0.48, 1.76, 0), (0.72, 1.83, 0), (0.85, 2.04, 0), (0.865, 2.42, 0), (0.86, 2.7, 0), (0.855, 2.83, 0)],
                [0.19, 0.215, 0.22, 0.22, 0.22, 0.2, 0.13], ribs=4, groove=0.15, tip=0.07, phase=0.4)
    la = ribbed('sg_armL', m, [(-0.12, 2.39, 0), (-0.44, 2.36, 0), (-0.65, 2.43, 0), (-0.75, 2.63, 0), (-0.758, 2.98, 0), (-0.755, 3.13, 0), (-0.752, 3.23, 0)],
                [0.17, 0.195, 0.2, 0.2, 0.2, 0.18, 0.11], ribs=4, groove=0.15, tip=0.06, phase=0.1)
    for o in (tr, ra, la): uv_region(o, GREEN, W, H, proj='cyl', ppm=40, umode='fold', vmode='tile', arc_r=0.3)
    fl = flower('sg_flower', m, (0.03, 3.972, -0.02), 0.2, n=5, cup=0.045, tilt=(0.05, -0.08), uvc=(fu0, fvm), uvt=(fu1, fvm))
    fl2 = flower('sg_flower2', m, (0.865, 2.86, 0.01), 0.14, n=5, cup=0.035, tilt=(0.25, 0.0), uvc=(fu0, fvm), uvt=(fu1, fvm))
    tree = join([tr, ra, la, fl, fl2], 'sg_cactus'); bake_tf(tree); hard(tree, 70)
    # ---- lod1: a five-sided trunk with a point, two three-sided arms of two segments
    ft = ribbed('sg_far_trunk', m, [(0, 0.0, 0), (0, 3.6, 0)], [0.32, 0.3], ribs=2, groove=0.0, tip=0.4, phase=0.3)
    # (ribs=2, groove 0 -> a 4-sided column; good enough far away)
    fa = sweep([(0.1, 1.8, 0), (0.85, 1.85, 0), (0.86, 2.85, 0)], [0.19, 0.2, 0.12], m, seg=3, name='sg_far_armR', cap=True)
    fb = sweep([(-0.1, 2.4, 0), (-0.75, 2.44, 0), (-0.755, 3.22, 0)], [0.17, 0.18, 0.1], m, seg=3, name='sg_far_armL', cap=True)
    for o in (fa, fb): bake_tf(o)
    for o in (ft, fa, fb): uv_region(o, GREEN, W, H, proj='cyl', ppm=40, umode='fold', vmode='tile', arc_r=0.3)
    farm = join([ft, fa, fb], 'sg_far'); bake_tf(farm); hard(farm, 70)
    meta = {'id': 'saguaro', 'lod': 60, 'tint': False, 'box': [[-0.93, 0, -0.3], [1.05, Hh, 0.3]], 'ref': {'h': Hh}}
    return finish_prop('p_saguaro', [tree], [farm], meta, ao0=0.4, ao1=0.4)


# ============================================================ p_fern
def frond_px(px, r0, r1, c0, c1, base, tip, rib, seed):
    """one whole frond into a region: u across (midrib in the middle), v from the base (bottom rows) to the tip"""
    rng = np.random.default_rng(seed)
    h, w = r1 - r0, c1 - c0
    for y in range(h):
        t = 1 - y / (h - 1)
        for x in range(w):
            u = (x + 0.5) / w; d = abs(u - 0.5) * 2
            g = hexrgb(base) * (1 - t) + hexrgb(tip) * t
            leaflet = ((y * 1.1 + d * 7.0) % 3.5) < 1.0
            c = g * (0.72 if leaflet else 1.0) * (0.9 + 0.15 * rng.random())
            if d < 0.14: c = hexrgb(rib) * (0.85 + 0.2 * t)
            px[r0 + y, c0 + x] = c


@prop
def fern():
    W, H = 32, 32
    px = np.zeros((H, W, 3), np.float32)
    frond_px(px, 0, H, 0, W, 0x284e28, 0x4e8a3e, 0x7a9a4a, 81)
    m = mat('fn_fern', 0xffffff, rough=0.85, clearcoat=0.0, tex=img('fn_fern_t', px))  # (night forest: see the pine)
    nocull(m)
    REG = (0, H, 0, W)
    _, _, v0, v1 = _region(REG, W, H); u0, u1, _, _ = _region(REG, W, H)
    rnd = random.Random(19)
    parts = []
    for k in range(6):  # three crossed fronds in the boxes = six arms
        a = TAU * k / 6 + rnd.uniform(-0.15, 0.15)
        d = (math.cos(a), 0, math.sin(a))
        L = 0.74 * rnd.uniform(0.86, 1.0)
        f = frond(f'fn_frond{k}', m, (d[0] * 0.03, 0.03, d[2] * 0.03), d, L, rnd.uniform(0.62, 0.72), rnd.uniform(0.02, 0.08),
                  [0.04, 0.17, 0.11, 0.12, 0.0], REG, W, H, fold=0.035, bend=rnd.uniform(-0.1, 0.1))
        parts.append(f)
    # a fiddlehead: a young frond still curled up like a violin's scroll
    fh = sweep([(0.04, 0.0, 0.03), (0.06, 0.28, 0.02), (0.13, 0.4, 0.0), (0.17, 0.33, -0.01)], [0.022, 0.02, 0.026, 0.02], m, seg=3, name='fn_fiddle', cap=True)
    bake_tf(fh)
    uv_region(fh, (10, 22, 13, 19), W, H, proj='box', ppm=60, umode='fold', vmode='fold')
    parts.append(fh)
    tree = join(parts, 'fn_fern'); bake_tf(tree); hard(tree, 80)
    # ---- lod1: six flat diamond leaves
    V, F, UV = [], [], []
    for k in range(6):  # root, the two sides at the arch, the tip
        a = TAU * k / 6; d = V3((math.cos(a), 0, math.sin(a))); sd = V3((-d.z, 0, d.x))
        b = len(V)
        V += [V3((0, 0.01, 0)), d * 0.32 + sd * 0.16 + V3((0, 0.4, 0)), d * 0.72 + V3((0, 0.05, 0)), d * 0.32 - sd * 0.16 + V3((0, 0.4, 0))]
        UV += [((u0 + u1) / 2, v0), (u0, (v0 + v1) / 2), ((u0 + u1) / 2, v1), (u1, (v0 + v1) / 2)]
        F += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new(gv(*q)) for q in V]
    for f in F:
        face = bm.faces.new([vs[i] for i in f])
        for lp, i in zip(face.loops, f): lp[uvl].uv = UV[i]
    farm = _obj('fn_far', bm, m); hard(farm, 80)
    meta = {'id': 'fern', 'lod': 25, 'tint': False, 'box': [[-0.725, 0, -0.725], [0.725, 0.56, 0.725]], 'ref': {'s': 1}}
    return finish_prop('p_fern', [tree], [farm], meta, ao0=0.25, ao1=0.25)


SHEET_KW['fern'] = {'exposure': 1.0}


# ============================================================ p_bush
@prop
def bush():
    W, H = 32, 32
    px = np.zeros((H, W, 3), np.float32)
    paint_leaf(px, 0, H, 0, W, 0x223a24, 91, var=0.2, spots=0.14, dots=0.08, light=1.6, mottle=0.12)
    rng = np.random.default_rng(92)
    for k in range(9):  # holly berries
        y, x = int(rng.integers(1, H - 2)), int(rng.integers(1, W - 2))
        px[y:y + 2, x:x + 2] = hexrgb(0xd81e30); px[y, x] = hexrgb(0xff8a8a)
    m = mat('bs_bush', 0xffffff, rough=0.7, clearcoat=0.0, tex=img('bs_bush_t', px))  # (night forest: see the pine)
    cull(m)
    lumps = puff_crown('bs_l', m, (0, 0.24, 0), (0.52, 0.34, 0.43), [(0.05, 4, 20)], seed=7, rad=(0.28, 0.34), depth=0.5,
                       seg=5, rings=3, core=(6, 3), squash=0.85, wob=0.3)
    lumps.append(lump((0.2, 0.7, -0.1), (0.37, 0.26, 0.3), m, 'bs_top', seg=6, rings=3, rot=(0.1, 0.8, 0.05)))
    cull_inside(lumps)
    bush_ = join(lumps, 'bs_bush'); bake_tf(bush_)
    kill_faces(bush_, lambda c, n: c.y < 0.0)  # (under the ground)
    lo, hi = bbox([bush_])
    fit_box([bush_], V3((lo.x, 0.0, lo.z)), V3((hi.x, 0.95, hi.z)), axes=(1,))
    uv_box(bush_, 0.6)
    # ---- lod1 (12): a four-sided mound in two rings and a top
    farm = blob('bs_far', m, [(0.0, 0.5, 4, 10, 0.03, -0.02, 1.0, 0.85), (0.42, 0.62, 4, 55, 0.06, -0.04, 1.0, 0.85)], top=(0.15, 0.95, -0.08))
    uv_box(farm, 0.6)
    meta = {'id': 'bush', 'lod': 30, 'tint': False, 'box': [[-0.64, 0, -0.645], [0.67, 0.95, 0.645]], 'ref': {'s': 1}}
    return finish_prop('p_bush', [bush_], [farm], meta, ao0=0.25, ao1=0.25)


SHEET_KW['bush'] = {'exposure': 1.0}


# ============================================================ run: one fresh scene per prop
def run():
    for fn in PROPS:
        fid = 'p_' + fn.__name__
        if ONLY and fn.__name__ not in ONLY: continue
        reset(); lib._mats.clear()
        root = fn()
        if '--no-export' not in ARGV: export(root, fid)
        kw = dict(SHEET_KW.get(fn.__name__, {}))
        preview(root, kw.pop('tint', 0x3c8c32))
        if CLOSE: close(root, fid)
        if '--no-sheet' not in ARGV: sheet_lods(root, fid, **kw)



def close(root, fid):
    sys.path.insert(0, '/tmp/claude-0/-workspace-jankfire/86957797-7d93-5698-a006-852e0a15c9f9/scratchpad/agents/misc')
    import closeup
    lo, hi = bbox([c for c in root.children_recursive if c.type == 'MESH' and not c.parent.name.startswith('lod1')])
    c = (lo + hi) / 2; s = (hi - lo).length
    views = [('eye', (c.x + s * 0.55, 1.7, c.z - s * 0.75), (c.x, hi.y * 0.55, c.z), 35),
             ('up', (c.x + 1.2, 1.6, c.z - 2.2), (c.x, hi.y * 0.8, c.z), 24),
             ('far', (c.x + s * 4.0, 1.7 + s * 0.4, c.z - s * 6.0), (c.x, hi.y * 0.5, c.z), 50),
             ('top', (c.x + s * 0.5, hi.y + s * 0.9, c.z - s * 0.6), (c.x, hi.y * 0.6, c.z), 35)]
    far = [o for o in root.children_recursive if o.type == 'MESH' and o.parent.name.startswith('lod1')]
    for o in far: o.hide_render = True
    closeup.shots(root, views, CLOSE, fid, res=(640, 480), exposure=SHEET_KW.get(fid[2:], {}).get('exposure', 0.0))
    for o in far: o.hide_render = False


run()
