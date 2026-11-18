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


def ellipsoid(c, r, rot=None):
    """an ellipsoid at c with radii r (x, y, z): a close bound, exact on the axes. rot: a 3 x 3 turn (its columns the
       ellipsoid's own axes in the frame)"""
    c = np.asarray(c, float); r = np.asarray(r, float)
    R = None if rot is None else np.asarray(rot, float)
    def f(p):
        q = p - c
        if R is not None: q = q @ R
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


def intersect(a, b, k=0.0):
    """inside both a and b (the edge where they meet rounded k wide)"""
    return lambda p: -smin(-a(p), -b(p), k)


def half(n, d):
    """the half space n . p < d (n a unit vector): intersect a shape with it to flatten one side"""
    n = np.asarray(n, float)
    return lambda p: p @ n - d


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


def relax(bm, f, h, steps=4, amount=0.5, fixed=None):
    """even out a decimated skin and keep it on the surface: each step slides every vertex (along the surface)
       `amount` of the way to its neighbours' middle, then pulls it back onto f = 0 (a decimate's collapses can leave a fold or a dent where long
       thin triangles cross a curve; this spreads them out). steps 0 = only the pull. fixed(vert) -> True: left where
       it is (a painted piece's seam)"""
    bm.verts.index_update()
    co = _W(np.array([tuple(vt.co) for vt in bm.verts]))
    hold = np.array([bool(fixed(vt)) for vt in bm.verts]) if fixed else np.zeros(len(co), bool)
    keep = co[hold].copy()
    nb = [[e.other_vert(vt).index for e in vt.link_edges] for vt in bm.verts]
    deg = np.array([len(n) for n in nb], float)
    src = np.concatenate([np.full(len(n), i) for i, n in enumerate(nb)]).astype(int)
    dst = np.concatenate([np.asarray(n, int) for n in nb])
    for _ in range(steps):
        mid = np.zeros_like(co)
        np.add.at(mid, src, co[dst])
        mid /= np.maximum(deg, 1)[:, None]
        # slide along the surface only (the move's part along the field's normal taken out): a plain average pulls
        # every tip and thin end inward (the first painted chicken lost 2 cm of beak and 1 cm of toes to it)
        g = _grad(f, co, h * 0.25); g /= np.maximum(_len(g), 1e-12)[:, None]
        dv = mid - co; dv -= (dv * g).sum(-1)[:, None] * g
        co = snap(f, co + amount * dv, h * 0.25)
        co[hold] = keep
    if steps == 0:
        co = snap(f, co, h * 0.25); co[hold] = keep
    for vt, c in zip(bm.verts, _P(co)): vt.co = Vector(c)


def mesh_paint(f, cls, labels, lo, hi, h=0.0012, tris=3000, name='sdf', relax_steps=3, floor=24, seam_k=1.5, hold=()):
    """ONE skin of the field, painted: cls(points (N, 3), weapon frame) -> the label index of each point (usually the
       component field nearest there: see nearest()). The dense skin is cut by label along its own quads, so the
       colour pieces share their seam vertices exactly (no gap, no face over another). Each piece is decimated to its
       share of `tris` (by area, at least `floor`) with its seam held (a decimate vertex group at 0: Blender 5.3 never
       collapses those), relaxed and snapped back onto the surface, and given the field's own normals (custom normals
       from the gradient, so the shading runs across the seams unbroken). hold: points (weapon frame) whose nearest
       vertices are never collapsed either: the tips of thin parts (a beak, toes), which a decimate otherwise eats
       (a held tip costs a few triangles; holding by curvature kept whole fingertips dense). Returns {label: bmesh in
       Blender's frame}"""
    v, q = nets(f, lo, hi, h)
    v = snap(f, v, h * 0.25)
    lab = np.asarray(cls(v[q].mean(1)), int)
    v = _smooth_seams(f, v, q, lab, h)
    counts = np.bincount(lab, minlength=len(labels))
    # a seam vertex is one used by quads of two labels: each piece keeps its seam whole, so it gets seam_k triangles
    # per seam vertex on top of its share by area (else the decimate meets the ratio by collapsing a thin part away: the
    # first painted chicken lost its beak's tip that way)
    owner = -np.ones(len(v), int); shared = np.zeros(len(v), bool)
    for i in range(len(labels)):
        used = np.unique(q[lab == i])
        shared[used[owner[used] >= 0]] = True
        owner[used] = i
    out = {}
    for i, lname in enumerate(labels):
        sel = q[lab == i]
        if not len(sel): continue
        used = np.unique(sel)
        remap = -np.ones(len(v), int); remap[used] = np.arange(len(used))
        seam = int(shared[used].sum())
        budget = max(floor, int(tris * counts[i] / max(1, counts.sum())) + int(seam_k * seam))
        out[lname] = _piece(f, v[used], remap[sel], budget, h, '%s_%s' % (name, lname), relax_steps, hold)
    return out


def _smooth_seams(f, v, q, lab, h, steps=6, amount=0.5):
    """the paint's edges follow the grid's quads: a staircase one cell high. Relax each seam vertex along its seam (to
       the middle of its two seam neighbours) and back onto the surface, before the skin is cut, so both colours
       keep the same smooth edge. Where three colours meet the vertex stays put"""
    e = np.concatenate([q[:, [0, 1]], q[:, [1, 2]], q[:, [2, 3]], q[:, [3, 0]]])
    el = np.concatenate([lab, lab, lab, lab])
    key = np.sort(e, 1)
    order = np.lexsort((key[:, 1], key[:, 0]))
    key, el = key[order], el[order]
    same = np.all(key[1:] == key[:-1], 1)
    seam = key[:-1][same & (el[1:] != el[:-1])]
    if not len(seam): return v
    nb = {}
    for a, b in seam:
        nb.setdefault(int(a), []).append(int(b)); nb.setdefault(int(b), []).append(int(a))
    ids = np.array([i for i, n in nb.items() if len(n) == 2])
    if not len(ids): return v
    pa = np.array([nb[i][0] for i in ids]); pb = np.array([nb[i][1] for i in ids])
    v = v.copy()
    for _ in range(steps):
        mid = (v[pa] + v[pb]) * 0.5
        v[ids] = snap(f, v[ids] + amount * (mid - v[ids]), h * 0.25)
    return v


def nearest(*comps, bias=None):
    """a classifier for mesh_paint: the index of the component field nearest each point (bias: added to a component's
       distance, + to shrink its region, - to grow it)"""
    bias = bias or [0.0] * len(comps)
    def cls(p):
        return np.argmin(np.stack([c(p) + b for c, b in zip(comps, bias)], 0), 0)
    return cls


def _piece(f, v, q, budget, h, name, relax_steps, hold=()):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(c) for c in _P(v)], [], [tuple(int(i) for i in r) for r in q])
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me)
    edge = set(vt.index for vt in bm.verts if vt.is_boundary)
    bm.free()
    for p in hold:
        d = _len(v - np.asarray(p, float))
        if d.min() < 3 * h: edge |= set(np.where(d < d.min() + 0.75 * h)[0].tolist())
    n = sum(len(p.vertices) - 2 for p in me.polygons)
    if n > budget:
        vg = o.vertex_groups.new(name='free')
        for vt in me.vertices: vg.add([vt.index], 0.0 if vt.index in edge else 1.0, 'REPLACE')
        d = o.modifiers.new('dc', 'DECIMATE'); d.decimate_type = 'COLLAPSE'; d.ratio = budget / n
        d.use_collapse_triangulate = True; d.vertex_group = 'free'
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    else:
        me2 = me.copy()
    bm = bmesh.new(); bm.from_mesh(me2)
    bpy.data.objects.remove(o); bpy.data.meshes.remove(me); bpy.data.meshes.remove(me2)
    bmesh.ops.triangulate(bm, faces=[fc for fc in bm.faces if len(fc.verts) > 3])
    relax(bm, f, h, steps=relax_steps, fixed=lambda vt: vt.is_boundary)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # the field's normals as custom normals (through a mesh: bmesh keeps them)
    bm.verts.index_update()
    co = _W(np.array([tuple(vt.co) for vt in bm.verts]))
    g = _grad(f, co, h * 0.25); g /= np.maximum(_len(g), 1e-12)[:, None]
    me3 = bpy.data.meshes.new(name); bm.to_mesh(me3); bm.free()
    for p in me3.polygons: p.use_smooth = True
    me3.normals_split_custom_set_from_vertices([tuple(c) for c in _P(g)])
    bm = bmesh.new(); bm.from_mesh(me3); bpy.data.meshes.remove(me3)
    return bm


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


# ------------------------------------------------------------------------------------------------ fields of meshes
def solids_of(bm):
    """a piece's bmesh (Blender's frame) split into its closed solids: [(verts (N, 3) weapon frame, tris (M, 3))]"""
    b = bm.copy()
    bmesh.ops.remove_doubles(b, verts=b.verts[:], dist=1e-6)
    bmesh.ops.triangulate(b, faces=b.faces[:])
    b.verts.index_update(); b.faces.index_update(); b.faces.ensure_lookup_table()
    seen, out = set(), []
    for f0 in b.faces:
        if f0.index in seen: continue
        stack, fs = [f0], []; seen.add(f0.index)
        while stack:
            f = stack.pop(); fs.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); stack.append(g)
        vid = sorted({v.index for f in fs for v in f.verts})
        rm = {i: j for j, i in enumerate(vid)}
        out.append((vid, [[rm[v.index] for v in f.verts] for f in fs]))
    b.verts.ensure_lookup_table()
    res = [(_W(np.array([tuple(b.verts[i].co) for i in vid])), np.array(tris, int)) for vid, tris in out]
    b.free()
    return res


def mesh_field(verts, tris, pad=0.03):
    """a closed mesh (weapon frame) as a distance field: |p - its nearest surface point|, signed by that face's
       outward side. Outside its box (+ pad) only the box distance (a lower bound: fine for unions whose fillets are
       narrower than pad)"""
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromPolygons([tuple(map(float, v)) for v in verts], [tuple(map(int, t)) for t in tris])
    blo, bhi = verts.min(0), verts.max(0)
    def f(p):
        d = np.maximum(np.maximum(blo - p, p - bhi), 0.0)
        out = _len(d)
        near = np.where(np.all((p > blo - pad) & (p < bhi + pad), 1))[0]
        for i in near:
            q = Vector(p[i])
            loc, nor, _, dist = tree.find_nearest(q)
            if loc is None: continue
            out[i] = dist if (q - loc).dot(nor) >= 0 else -dist
        return out
    return f



def grid_field(verts, tris, h, pad=0.03, smooth=1):
    """a closed mesh (weapon frame) as a distance field SAMPLED on a grid (spacing h, its box + pad), read back by
       trilinear interpolation. The sign by WINDING along one ray in x per grid row (entries minus exits behind a
       point: inside where > 0; right at sharp edges, where a nearest face's normal is not, and where a solid passes
       through itself, a rope's loops, where plain parity is not). The distance to the nearest surface point exactly
       within a band round the surface (pad), from a grid 4 times coarser farther out. Outside the grid: the distance
       to the grid's box plus the edge value (a lower bound). smooth: passes of a 1-2-1 blur over the samples (a kit
       solid's flat facets otherwise come back as lumps)"""
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromPolygons([tuple(map(float, v)) for v in verts], [tuple(map(int, t)) for t in tris])
    lo = verts.min(0) - pad; hi = verts.max(0) + pad
    ax = [np.arange(lo[i], hi[i] + h, h) for i in range(3)]
    nx, ny, nz = len(ax[0]), len(ax[1]), len(ax[2])
    wind = np.zeros((nx, ny, nz), np.int16)
    jit = (1.3e-7, 0.7e-7)
    X0 = Vector((1, 0, 0))
    for j in range(ny):
        for k in range(nz):
            o = Vector((ax[0][0] - h, ax[1][j] + jit[0], ax[2][k] + jit[1]))
            xs, ss = [], []
            for _ in range(256):
                loc, nor, _, dist = tree.ray_cast(o, X0)
                if loc is None: break
                xs.append(loc.x); ss.append(1 if nor.x < 0 else -1)
                o = Vector((loc.x + 1e-6, o.y, o.z))
            if xs:
                c = np.searchsorted(np.array(xs), ax[0])
                acc = np.concatenate([[0], np.cumsum(ss)])
                wind[:, j, k] = acc[c]
    inside = wind > 0
    fn = tree.find_nearest
    # coarse distances (every 4th sample), then exact ones where the coarse says the surface is near
    cx = [a[::4] for a in ax]
    CX, CY, CZ = np.meshgrid(*cx, indexing='ij')
    cp = np.stack([CX.ravel(), CY.ravel(), CZ.ravel()], 1)
    C = np.fromiter((fn(q)[3] for q in cp.tolist()), float, count=len(cp)).reshape(CX.shape)
    ii = np.minimum(np.arange(nx) // 4, C.shape[0] - 1); jj = np.minimum(np.arange(ny) // 4, C.shape[1] - 1)
    kk = np.minimum(np.arange(nz) // 4, C.shape[2] - 1)
    G = C[np.ix_(ii, jj, kk)]
    near = np.argwhere(G < pad + 8 * h)
    if len(near):
        pts = np.stack([ax[0][near[:, 0]], ax[1][near[:, 1]], ax[2][near[:, 2]]], 1)
        G[near[:, 0], near[:, 1], near[:, 2]] = np.fromiter((fn(q)[3] for q in pts.tolist()), float, count=len(pts))
    G[inside] *= -1
    for _ in range(smooth):
        for a in range(3):
            Gp = np.concatenate([np.take(G, [0], a), G, np.take(G, [-1], a)], a)
            sl = lambda i, j: tuple(slice(i, j) if b == a else slice(None) for b in range(3))
            G = 0.25 * Gp[sl(0, -2)] + 0.5 * Gp[sl(1, -1)] + 0.25 * Gp[sl(2, None)]
    lo_ = np.array([ax[0][0], ax[1][0], ax[2][0]]); n = np.array([nx, ny, nz])
    def f(p):
        u = (p - lo_) / h
        out_d = _len(np.maximum(np.maximum(-u, u - (n - 1)), 0.0)) * h
        u = np.clip(u, 0, n - 1 - 1e-9)
        i0 = np.floor(u).astype(int); t = u - i0
        i1 = np.minimum(i0 + 1, n - 1)
        x0, y0, z0 = i0.T; x1, y1, z1 = i1.T; tx, ty, tz = t.T
        c00 = G[x0, y0, z0] * (1 - tx) + G[x1, y0, z0] * tx
        c10 = G[x0, y1, z0] * (1 - tx) + G[x1, y1, z0] * tx
        c01 = G[x0, y0, z1] * (1 - tx) + G[x1, y0, z1] * tx
        c11 = G[x0, y1, z1] * (1 - tx) + G[x1, y1, z1] * tx
        return (c00 * (1 - ty) + c10 * ty) * (1 - tz) + (c01 * (1 - ty) + c11 * ty) * tz + out_d
    return f

def fuse(g, parts, h=0.001, tris=3000, name='fuse', hold=(), relax_steps=3, pad=0.016, smooth=1, seam_k=1.5):
    """FUSE A BUILT MODEL'S STUCK-TOGETHER PARTS INTO ONE SKIN (the owner's "AI-made" tell, 18 Nov). parts: [(piece key
       (node_wz, slot), k[, field[, pick[, kin]]])] of g.pieces (field: that part's exact field, else its solids are
       sampled; pick(point) -> True: only the piece's faces whose centre it picks take part, the rest of the piece
       stays; kin: the fillet between that piece's own solids, e.g. a bunch of bananas or a cloud's puffs): the first is the base, each next one is joined to what came before with a
       fillet k wide (0: a plain union, for a thin painted line such as a seam rod). Every closed solid of those pieces
       becomes a field (mesh_field), the whole is meshed once (mesh_paint) and painted back by the nearest source piece,
       so each piece keeps its name, look and wrap zone, but no face of one lies inside another any more and every join
       is filleted. Pieces not named stay as they were. Returns the report() of each new piece"""
    fields, keys, rest = [], [], {}
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for part in parts:
        key, k = part[0], part[1]
        bm = g.pieces.get(key)
        if bm is None: raise KeyError('fuse: no piece %s' % (key,))
        pick = part[3] if len(part) > 3 else None
        if pick is not None:
            # only this piece's faces with pick(centre (weapon frame)) take part; the others stay as they were
            keep = bm.copy()
            gone = [fc for fc in keep.faces if pick(_W(np.array([tuple(fc.calc_center_median())]))[0])]
            sub = bm.copy()
            bmesh.ops.delete(sub, geom=[fc for fc in sub.faces if not pick(_W(np.array([tuple(fc.calc_center_median())]))[0])], context='FACES')
            bmesh.ops.delete(keep, geom=gone, context='FACES')
            rest[key] = keep
            sols = solids_of(sub); sub.free()
        else:
            sols = solids_of(bm)
        for v, _ in sols:
            lo = np.minimum(lo, v.min(0)); hi = np.maximum(hi, v.max(0))
        kin = part[4] if len(part) > 4 else 0.0
        if len(part) > 2 and part[2] is not None:
            fld = part[2]        # (the part's own exact field: a plain shape, no facets to sample)
        else:
            sol = [grid_field(v, t, h, pad, smooth) for v, t in sols]
            fld = union(*sol, k=kin) if len(sol) > 1 else sol[0]
        fields.append((fld, k)); keys.append(key)
    whole = fields[0][0]
    for fld, k in fields[1:]: whole = blend(whole, fld, k)
    out = mesh_paint(whole, nearest(*[fl for fl, _ in fields]), [str(i) for i in range(len(keys))], lo - 2 * h,
                     hi + 2 * h, h=h, tris=tris, name=name, relax_steps=relax_steps, hold=hold, seam_k=seam_k)
    rep = {}
    for i, key in enumerate(keys):
        old = g.pieces.pop(key); old.free()
        new = out.get(str(i))
        if new is not None: rep[key] = report(new)
        if key in rest:          # (the piece's other faces, back beside the fused part)
            me = bpy.data.meshes.new('rest'); rest[key].to_mesh(me); rest[key].free()
            if new is None: new = bmesh.new()
            new.from_mesh(me); bpy.data.meshes.remove(me)
        if new is not None: g.pieces[key] = new
    return rep
