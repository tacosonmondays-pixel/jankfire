# SDF_KIT (18 Nov 2026): organic ONE-PIECE solids for the kit, after the owner asked for the Hand Slapper: "can you fuse
# the fingers so its all one piece?". A shape is a signed distance field of points in the weapon frame (metres; x right,
# y up, z back; negative inside), built from round primitives joined by SMOOTH UNIONS (smin: where two meet the surface
# rolls from one to the other in a real fillet about k wide, the way a sculptor blends clay; never a crease or a
# primitive stuck on a block). mesh() samples the field on a grid, makes the surface with surface nets (one closed,
# manifold quad skin), pulls every vertex onto the true surface (Newton steps on the field), then a Collapse decimate
# takes it to a triangle budget and the vertices are pulled onto the surface once more. Pure numpy + bmesh, headless
# Blender, no add-ons. Used by gun_batch_a.slapper (the fused hand).
#   a field is f(p) -> d, p an (N, 3) array, d an (N,) array.
import numpy as np
import bpy, bmesh
from mathutils import Vector


def _len(v): return np.sqrt((v * v).sum(-1))


# ------------------------------------------------------------------------------------------------ primitives
def capsule(a, b, ra, rb=None):
    """a round-ended tube from a to b (the ends' CENTRES), radius ra at a easing to rb at b"""
    a = np.asarray(a, float); b = np.asarray(b, float); rb = ra if rb is None else rb
    ba = b - a; L2 = float(ba.dot(ba))
    def f(p):
        pa = p - a
        h = np.clip((pa @ ba) / L2, 0.0, 1.0)
        return _len(pa - h[:, None] * ba) - (ra + (rb - ra) * h)
    return f


def tube(pts, radii, k=0.0):
    """a bent tube through pts (centres), radius per point: capsules end to end (smoothly joined when k > 0)"""
    segs = [capsule(pts[i], pts[i + 1], radii[i], radii[i + 1]) for i in range(len(pts) - 1)]
    return union(*segs, k=k)


def ellipsoid(c, r):
    """an ellipsoid at c with radii r (x, y, z): a close bound, exact on the axes"""
    c = np.asarray(c, float); r = np.asarray(r, float)
    def f(p):
        q = p - c
        k0 = _len(q / r); k1 = _len(q / (r * r))
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-12)
    return f


def polygon2(poly):
    """the signed distance to a closed 2D polygon [(u, v)] (negative inside): f(u, v) on arrays"""
    V = np.asarray(poly, float); n = len(V)
    def f(u, v):
        P = np.stack([u, v], -1)
        d = ((P - V[0]) ** 2).sum(-1); s = np.ones_like(u)
        for i in range(n):
            vi, vj = V[i], V[i - 1]
            e = vj - vi; w = P - vi
            b = w - e * np.clip((w @ e) / e.dot(e), 0.0, 1.0)[:, None]
            d = np.minimum(d, (b * b).sum(-1))
            c1 = P[:, 1] >= vi[1]; c2 = P[:, 1] < vj[1]; c3 = e[0] * w[:, 1] > e[1] * w[:, 0]
            flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
            s = np.where(flip, -s, s)
        return s * np.sqrt(d)
    return f


def slab(poly, hx, r, grow=0.0, x0=0.0):
    """a side-view polygon [(z, y)] grown out by `grow` (round corners in the side view), pushed out +-hx across x about
       x0, every edge of the slab rounded by r (a pillow edge)"""
    p2 = polygon2(poly)
    def f(p):
        d2 = p2(p[:, 2], p[:, 1]) - grow + r
        dx = np.abs(p[:, 0] - x0) - (hx - r)
        w0 = np.maximum(d2, 0.0); w1 = np.maximum(dx, 0.0)
        return np.minimum(np.maximum(d2, dx), 0.0) + np.sqrt(w0 * w0 + w1 * w1) - r
    return f


# ------------------------------------------------------------------------------------------------ joins
def smin(a, b, k):
    """the polynomial smooth minimum: a fillet about k wide where the two surfaces meet (k 0 = a plain union)"""
    if k <= 0: return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def union(*fs, k=0.0):
    def f(p):
        d = fs[0](p)
        for g in fs[1:]: d = smin(d, g(p), k)
        return d
    return f


def blend(a, b, k):
    """a joined to b with a fillet k"""
    return lambda p: smin(a(p), b(p), k)


def carve(a, b, k=0.0):
    """b taken out of a (a smooth edge k wide)"""
    return lambda p: -smin(-a(p), b(p), k)


# ------------------------------------------------------------------------------------------------ to a mesh
def _grad(f, v, e):
    g = np.zeros_like(v)
    for i in range(3):
        d = np.zeros(3); d[i] = e
        g[:, i] = (f(v + d) - f(v - d)) / (2 * e)
    return g


def snap(f, v, e, steps=4):
    """pull points onto the surface f = 0 (Newton steps along the field's gradient)"""
    for _ in range(steps):
        d = f(v); g = _grad(f, v, e)
        v = v - (d / np.maximum((g * g).sum(-1), 1e-12))[:, None] * g
    return v


def nets(f, lo, hi, h):
    """surface nets: the field sampled every h over the box lo..hi (weapon frame) -> (verts (N, 3), quads (M, 4))"""
    lo = np.asarray(lo, float) - 2 * h; hi = np.asarray(hi, float) + 2 * h
    axes = [np.arange(lo[i], hi[i] + h, h) for i in range(3)]
    X, Y, Z = np.meshgrid(*axes, indexing='ij')
    F = np.concatenate([f(np.stack([X[i].ravel(), Y[i].ravel(), Z[i].ravel()], 1)) for i in range(X.shape[0])])
    F = F.reshape(X.shape)
    nx, ny, nz = F.shape
    ins = F < 0
    acc = np.zeros((nx - 1, ny - 1, nz - 1, 3)); cnt = np.zeros((nx - 1, ny - 1, nz - 1))
    corners = [(i, j, k) for i in (0, 1) for j in (0, 1) for k in (0, 1)]
    edges = [(a, b) for a in corners for b in corners if a < b and sum(abs(a[t] - b[t]) for t in range(3)) == 1]
    C = lambda c: F[c[0]:nx - 1 + c[0], c[1]:ny - 1 + c[1], c[2]:nz - 1 + c[2]]
    for a, b in edges:
        fa, fb = C(a), C(b)
        m = (fa < 0) != (fb < 0)
        t = np.where(m, fa / np.where(m, fa - fb, 1.0), 0.0)
        pa, pb = np.array(a, float), np.array(b, float)
        acc += np.where(m[..., None], pa + t[..., None] * (pb - pa), 0.0)
        cnt += m
    has = cnt > 0
    idx = -np.ones(cnt.shape, int); idx[has] = np.arange(int(has.sum()))
    verts = lo + (np.argwhere(has) + acc[has] / cnt[has][:, None]) * h
    quads = []
    # an edge of the grid with a sign change gets the quad of the four cells round it, wound outward
    ex = ins[:-1, :, :] != ins[1:, :, :]
    for i, j, k in np.argwhere(ex):
        if 0 < j < ny - 1 and 0 < k < nz - 1:
            q = [idx[i, j - 1, k - 1], idx[i, j, k - 1], idx[i, j, k], idx[i, j - 1, k]]
            quads.append(q if ins[i, j, k] else q[::-1])
    ey = ins[:, :-1, :] != ins[:, 1:, :]
    for i, j, k in np.argwhere(ey):
        if 0 < i < nx - 1 and 0 < k < nz - 1:
            q = [idx[i - 1, j, k - 1], idx[i - 1, j, k], idx[i, j, k], idx[i, j, k - 1]]
            quads.append(q if ins[i, j, k] else q[::-1])
    ez = ins[:, :, :-1] != ins[:, :, 1:]
    for i, j, k in np.argwhere(ez):
        if 0 < i < nx - 1 and 0 < j < ny - 1:
            q = [idx[i - 1, j - 1, k], idx[i, j - 1, k], idx[i, j, k], idx[i - 1, j, k]]
            quads.append(q if ins[i, j, k] else q[::-1])
    return verts, np.asarray(quads, int)


def _P(v):
    """weapon frame -> Blender (gunkit.P): (x, y, z) -> (x, -z, y)"""
    return np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1)


def _W(v):
    return np.stack([v[:, 0], v[:, 2], -v[:, 1]], 1)


def mesh(f, lo, hi, h=0.0012, tris=3000, name='sdf', relax_steps=4):
    """the field's surface as a smooth-shaded bmesh in Blender's frame, about `tris` triangles, every vertex on the
       surface. lo / hi: a box round the WHOLE shape (weapon frame; a shape past it is cut open there)"""
    v, q = nets(f, lo, hi, h)
    v = snap(f, v, h * 0.25)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(c) for c in _P(v)], [], [tuple(int(i) for i in r) for r in q])
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    n = sum(len(p.vertices) - 2 for p in me.polygons)
    if n > tris:
        d = o.modifiers.new('dc', 'DECIMATE'); d.decimate_type = 'COLLAPSE'; d.ratio = tris / n
        d.use_collapse_triangulate = True
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        o.modifiers.clear()
    else:
        me2 = me.copy()
    bm = bmesh.new(); bm.from_mesh(me2)
    bpy.data.objects.remove(o); bpy.data.meshes.remove(me); bpy.data.meshes.remove(me2)
    relax(bm, f, h, steps=relax_steps)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for fc in bm.faces: fc.smooth = True
    bm.normal_update()
    return bm


def relax(bm, f, h, steps=4, amount=0.5):
    """even out a decimated skin and keep it on the surface: each step moves every vertex `amount` of the way to its
       neighbours' middle, then pulls it back onto f = 0 (a decimate's collapses can leave a fold or a dent where long
       thin triangles cross a curve; this spreads them out). steps 0 = only the pull"""
    bm.verts.index_update()
    co = _W(np.array([tuple(vt.co) for vt in bm.verts]))
    nb = [[e.other_vert(vt).index for e in vt.link_edges] for vt in bm.verts]
    deg = np.array([len(n) for n in nb], float)
    src = np.concatenate([np.full(len(n), i) for i, n in enumerate(nb)]).astype(int)
    dst = np.concatenate([np.asarray(n, int) for n in nb])
    for _ in range(steps):
        mid = np.zeros_like(co)
        np.add.at(mid, src, co[dst])
        mid /= np.maximum(deg, 1)[:, None]
        co = snap(f, co + amount * (mid - co), h * 0.25)
    if steps == 0: co = snap(f, co, h * 0.25)
    for vt, c in zip(bm.verts, _P(co)): vt.co = Vector(c)


def folds(bm, f, h):
    """faces turned away from the field's outward direction (a fold or a dent): (count, worst dot)"""
    out, worst = 0, 1.0
    bm.normal_update()
    cs = _W(np.array([tuple(fc.calc_center_median()) for fc in bm.faces]))
    ns = _W(np.array([tuple(fc.normal) for fc in bm.faces]))
    g = _grad(f, cs, h * 0.25); g /= np.maximum(_len(g), 1e-12)[:, None]
    d = (ns * g).sum(-1)
    return int((d < 0.7).sum()), float(d.min())


def report(bm):
    """triangles, and whether the skin is one closed manifold piece (every edge between exactly two faces)"""
    bm.verts.index_update()
    tri = sum(len(fc.verts) - 2 for fc in bm.faces)
    bad = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    seen, parts = set(), 0
    for v0 in bm.verts:
        if v0.index in seen: continue
        parts += 1; stack = [v0]; seen.add(v0.index)
        while stack:
            v = stack.pop()
            for e in v.link_edges:
                w = e.other_vert(v)
                if w.index not in seen: seen.add(w.index); stack.append(w)
    return {'tris': tri, 'open_edges': bad, 'parts': parts}
