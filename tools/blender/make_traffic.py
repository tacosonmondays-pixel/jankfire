# Traffic (round 4): the eight moving cars public/js/cars.js builds in code, as glossy Blender models. Same wheel spots,
# lamp spots, sizes and silhouettes as the code cars (shared/traffic.js CARS), then made good: real proportions of a
# supermini (hatch), a saloon (sedan), the saloon as a cab (taxi, fixed livery + the TAXI? roof light), a full-size
# pickup, a panel van, the ice cream van (fixed livery, serving hatch, the giant cone), a low-floor city bus (fixed
# JANK TRANSIT livery) and a box truck (JANK COLA on the box).
# Facing +z, origin on the ground under the middle. Each file:
#   body      empty: every body mesh (the game pitches / rolls it), materials tint (or the livery), trim, glass, plus
#             lamps (headlights, material lamp), tails (tail lights + the brake light, tail), inds (indicators +
#             side repeaters, ind): their own meshes so the game can switch them
#   wheel_fl / wheel_fr / wheel_rl / wheel_rr: one mesh each, origin on the hub, axle along x, rims face out on both
#             sides (l = +x, the car's left; the duals are part of the rear wheels of the bus and the truck)
#   lod1      empty: one 300-triangle mesh of the whole car + wheels (parked copies far away)
# The body is lofted along z (a cross-section per station: tumblehome, plan-view taper, crowned bonnet and roof, the
# arches cut by raising the floor round each wheel); the glass house is a second loft; lamps, grilles, plates and trims
# are cast onto the body (ray hits) so they hug it. Paint = tint (white with a faint crusty grain, the seams painted in:
# the game colours it per car); the trim is one atlas (black plastic, chrome, rubber, the tread, plates, stickers) with
# a metal/roughness map, so a car is 3 materials + its 3 lamp ones. Baked AO in the vertex colours.
# run: blender -b --python tools/blender/make_traffic.py   (-- --only=sedan,taxi  --no-sheet  --qa  --preview=<dir>)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib
from mathutils.bvhtree import BVHTree
from bisect import bisect_right

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
V3 = Vector
lerp = lambda a, b, t: a + (b - a) * t
clamp = lambda v, a, b: max(a, min(b, v))


def arg(k, d=None):
    for a in ARGV:
        if a.startswith('--' + k + '='): return a.split('=', 1)[1]
        if a == '--' + k: return True
    return d


# ------------------------------------------------------------ curves
def spline(pts):
    """smooth monotone curve through [(x, y)] (Fritsch-Carlson: no overshoot), clamped at the ends"""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; n = len(xs)
    if n == 1: return lambda x: ys[0]
    d = [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(n - 1)]
    m = [d[0]] + [((d[i - 1] + d[i]) / 2 if d[i - 1] * d[i] > 0 else 0.0) for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):
        if d[i] == 0: m[i] = m[i + 1] = 0.0; continue
        a, b = m[i] / d[i], m[i + 1] / d[i]
        s = a * a + b * b
        if s > 9: t = 3 / math.sqrt(s); m[i] = t * a * d[i]; m[i + 1] = t * b * d[i]
    def f(x):
        if x <= xs[0]: return ys[0]
        if x >= xs[-1]: return ys[-1]
        i = bisect_right(xs, x) - 1
        h = xs[i + 1] - xs[i]; t = (x - xs[i]) / h
        t2, t3 = t * t, t * t * t
        return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h * m[i + 1]
    return f


def linear(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    def f(x):
        if x <= xs[0]: return ys[0]
        if x >= xs[-1]: return ys[-1]
        i = bisect_right(xs, x) - 1
        return lerp(ys[i], ys[i + 1], (x - xs[i]) / (xs[i + 1] - xs[i]))
    return f


def stations(z0, z1, step, arches=(), extra=(), arch_n=8, sill=None):
    """station z values from z0 (rear) to z1 (front): the ends, each arch sampled round its circle from hub height (or
    where it meets the sill, if that's higher) plus a station just outside each end (the arch drops straight to the
    sill there), feature stations, filled so no gap is longer than step"""
    zs = [z0, z1] + list(extra)
    for az, hub, r in arches:
        s = sill if sill is not None else hub
        a0 = math.asin(clamp((s - hub) / r, 0, 1))
        for k in range(arch_n + 1):
            a = a0 + (math.pi - 2 * a0) * k / arch_n
            zs.append(az + math.cos(a) * r * (0.999 if k in (0, arch_n) else 1))
        if s < hub: zs += [az - r - 0.014, az + r + 0.014]
    zs = sorted(z for z in zs if z0 - 1e-6 <= z <= z1 + 1e-6)
    out = []
    for z in zs:
        if not out or z - out[-1] > 0.01: out.append(z)
    full = [out[0]]
    for z in out[1:]:
        a = full[-1]
        n = max(1, int(math.ceil((z - a) / step)))
        for k in range(1, n): full.append(lerp(a, z, k / n))
        full.append(z)
    return full


def arch_floor(z, arches, sill):
    """the body's floor at z: the sill, raised round the wheels (a circle round each hub)"""
    y = sill(z) if callable(sill) else sill
    for az, hub, r in arches:
        dz = z - az
        if abs(dz) < r: y = max(y, hub + math.sqrt(r * r - dz * dz))
    return y


# ------------------------------------------------------------ meshes
def zloft(name, zs, half, mat_fn=None, nmat=1, caps=(True, True), open_bottom=False, full=False):
    """a shell lofted along game z. half(z) -> [(x, y)] for x >= 0, from the bottom outer point up the side and over
    to the top centre (last point x = 0): mirrored into a ring per station. Faces between station i and i+1 on ring
    slot j get material mat_fn(i, j, nslots) (j = 0 is the slot from P1 upward on the +x side; the last slot is the
    bottom, P1' -> P1). caps = (rear, front) n-gon end caps."""
    bm = bmesh.new()
    rings = []
    for z in zs:
        h = half(z)
        ring = list(h) if full else list(h) + [(-x, y) for x, y in reversed(h[:-1])]  # full: the ring as given (a wall off the middle)
        rings.append([bm.verts.new(gv(x, y, z)) for x, y in ring])
    k = len(rings[0])
    faces = []
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(k):
            if open_bottom and j == k - 1: continue
            jj = (j + 1) % k
            f = bm.faces.new((a[j], a[jj], b[jj], b[j]))
            f.material_index = mat_fn(i, j, k) if mat_fn else 0
            faces.append(f)
    if caps[0]:
        f = bm.faces.new(list(reversed(rings[0]))); f.material_index = mat_fn(-1, -1, k) if mat_fn else 0
    if caps[1]:
        f = bm.faces.new(list(rings[-1])); f.material_index = mat_fn(len(rings) - 1, -1, k) if mat_fn else 0
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    o = _obj(name, bm, None)
    return o


def set_mats(o, mats):
    me = o.data
    idx = [0] * len(me.polygons); me.polygons.foreach_get('material_index', idx)
    me.materials.clear()  # (this zeroes the face indices: put them back)
    for m in mats: me.materials.append(m)
    me.polygons.foreach_set('material_index', [min(i, len(mats) - 1) for i in idx])
    return o


def g2b(p): return gv(*p)
def b2g(v): return V3((v.x, v.z, -v.y))


class Surf:
    """ray hits on a set of meshes (game coordinates in and out)"""
    def __init__(self, objs):
        bm = bmesh.new()
        for o in objs:
            apply_mods(o)
            me = o.data.copy(); me.transform(o.matrix_world); bm.from_mesh(me); bpy.data.meshes.remove(me)
        bm.normal_update()
        self.bm = bm
        self.t = BVHTree.FromBMesh(bm)

    def hit(self, p, d):
        loc, nor, idx, dist = self.t.ray_cast(g2b(p), g2b(d).normalized())
        if loc is None: return None
        n = b2g(nor)
        if n.dot(V3(d)) > 0: n = -n
        return b2g(loc), n.normalized()

    def onto(self, p, d, back=3.0):
        """cast from p - d*back along d: the first surface point (or None)"""
        P = V3(p); D = V3(d).normalized()
        return self.hit(P - D * back, D)


def slab(name, grid, m, off=0.006, depth=0.03, uvr=None, tex=None, flipu=False, back=False):
    """a part hugging the body: grid = rows (bottom to top) x cols of (point, normal) on the surface. Its face sits off
    along the normal, its edges run depth back into the body (no back face: it's inside). uvr = a pixel rect of tex
    (w, h) the face fills (u across the columns, v up the rows); the edges get a sliver of the same rect."""
    R, C = len(grid), len(grid[0])
    grid = grid_normals(grid)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    edge = [(r, 0) for r in range(R)] + [(R - 1, c) for c in range(1, C)] + [(r, C - 1) for r in range(R - 2, -1, -1)] + [(0, c) for c in range(C - 2, 0, -1)]
    fr = [[bm.verts.new(g2b(p + n * off)) for p, n in row] for row in grid]
    bk = {}
    for r in range(R):
        for c in range(C):
            if back or (r, c) in edge: p, n = grid[r][c]; bk[r, c] = bm.verts.new(g2b(p - n * (depth - off)))
    def uvof(r, c, k=1.0):
        s = c / (C - 1); t = r / (R - 1)
        if flipu: s = 1 - s
        if k != 1:
            s, t = 0.5 + (s - 0.5) * 0.3, 0.5 + (t - 0.5) * 0.3
            if k == 0.5: s, t = s + 0.05, t + 0.05  # (edge walls: never a zero-area strip)
        if uvr is None: return (s, t)
        return uv_px(uvr, tex, s, t)
    def quad(vs, uvs):
        f = bm.faces.new(vs)
        for lp, q in zip(f.loops, uvs): lp[uvl].uv = q
        return f
    nrm = sum((n for row in grid for _, n in row), V3()).normalized()
    for r in range(R - 1):
        for c in range(C - 1):
            f = quad((fr[r][c], fr[r][c + 1], fr[r + 1][c + 1], fr[r + 1][c]), (uvof(r, c), uvof(r, c + 1), uvof(r + 1, c + 1), uvof(r + 1, c)))
            if back: quad((bk[r, c], bk[r + 1, c], bk[r + 1, c + 1], bk[r, c + 1]), (uvof(r, c, 0), uvof(r + 1, c, 0), uvof(r + 1, c + 1, 0), uvof(r, c + 1, 0)))
    for e0, e1 in zip(edge, edge[1:] + edge[:1]):
        quad((fr[e1[0]][e1[1]], bk[e1], bk[e0], fr[e0[0]][e0[1]]), (uvof(*e1, 0), uvof(*e1, 0.5), uvof(*e0, 0.5), uvof(*e0, 0)))
    # wind it so the face points out along the surface normal
    bm.normal_update(); bm.faces.ensure_lookup_table()
    f0 = bm.faces[0]
    if b2g(f0.normal).dot(nrm) < 0:
        for f in bm.faces: f.normal_flip()
    o = _obj(name, bm, m)
    smooth(o, 40)
    return o


def grid_normals(grid):
    """the grid's own vertex normals (the average of its cells round each point), turned to agree with the hits: an
    offset along them stays an offset off the part's faces, even on a tight curve"""
    R, C = len(grid), len(grid[0])
    P = [[p for p, _ in row] for row in grid]
    out = []
    for r in range(R):
        row = []
        for c in range(C):
            acc = V3()
            for dr, dc in ((0, 0), (-1, 0), (0, -1), (-1, -1)):
                r0, c0 = r + dr, c + dc
                if 0 <= r0 < R - 1 and 0 <= c0 < C - 1:
                    acc += (P[r0][c0 + 1] - P[r0][c0]).cross(P[r0 + 1][c0] - P[r0][c0]) + (P[r0 + 1][c0 + 1] - P[r0 + 1][c0]).cross(P[r0 + 1][c0 + 1] - P[r0][c0 + 1])
            n0 = grid[r][c][1]
            if acc.length < 1e-12: row.append((P[r][c], n0)); continue
            acc.normalize()
            if acc.dot(n0) < 0: acc = -acc
            row.append((P[r][c], acc))
        out.append(row)
    return out


def refine(rays, sub):
    """resample a rows x cols grid of (origin, direction) rays sub times finer (bilinear)"""
    if sub <= 1: return rays
    R, C = len(rays), len(rays[0])
    nr, nc = (R - 1) * sub + 1, (C - 1) * sub + 1
    out = []
    for i in range(nr):
        u = i / sub; i0 = min(int(u), R - 2); fu = u - i0
        row = []
        for j in range(nc):
            v = j / sub; j0 = min(int(v), C - 2); fv = v - j0
            def bl(k):
                a = rays[i0][j0][k] * (1 - fv) + rays[i0][j0 + 1][k] * fv
                b = rays[i0 + 1][j0][k] * (1 - fv) + rays[i0 + 1][j0 + 1][k] * fv
                return a * (1 - fu) + b * fu
            row.append((bl(0), bl(1).normalized()))
        out.append(row)
    return out


def clearance(S, rays, grid, off):
    """how far the surface bulges past a face sitting off out (sampled at each cell's middle): add it to off"""
    worst = 0.0
    R, C = len(grid), len(grid[0])
    grid = grid_normals(grid)
    for r in range(R - 1):
        for c in range(C - 1):
            o4 = [rays[r][c], rays[r][c + 1], rays[r + 1][c], rays[r + 1][c + 1]]
            p = sum((q[0] for q in o4), V3()) / 4; d = sum((q[1] for q in o4), V3()).normalized()
            h = S.onto(p, d, 0.0)
            if h is None: continue
            f = sum((grid[a][b][0] + grid[a][b][1] * off for a, b in ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))), V3()) / 4
            nn = sum((grid[a][b][1] for a, b in ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))), V3()).normalized()
            worst = max(worst, (h[0] - f).dot(nn))
    return worst


def cast_grid(S, rays):
    """rays = rows x cols of (origin, direction): the surface points + normals (None if any missed)"""
    out = []
    for row in rays:
        r = []
        for p, d in row:
            h = S.onto(p, d, 0.0)
            if h is None: raise RuntimeError(f'ray missed the body at {p} {d}')
            r.append(h)
        out.append(r)
    return out


def front_rays(xs, ys, z, d=-1):
    """rows (ys, bottom to top) x cols (xs) of rays along z (d = -1: from the front toward -z)"""
    return [[(V3((x, y, z)), V3((0, 0, d))) for x in xs] for y in ys]


def side_rays(zs, ys, x, d=-1):
    """rays along x (d = -1: from +x inward)"""
    return [[(V3((x, y, z)), V3((d, 0, 0))) for z in zs] for y in ys]


def swept(cx, cz, cols, rows=2, R=4.0, s=1):
    """corner rays where every column has its own height range: cols = [(phi, y_bottom, y_top)], mirrored for s = -1"""
    out = []
    for i in range(rows):
        t = i / (rows - 1); row = []
        for ph, y0, y1 in cols:
            a = math.radians(ph * s); d = V3((math.sin(a), 0, math.cos(a)))
            row.append((V3((cx * s, lerp(y0, y1, t), cz)) + d * R, -d))
        out.append(row)
    return out


def corner_rays(cx, cz, phis, ys, R=4.0):
    """rays from outside toward a vertical axis at (cx, cz): phi = 0 looks from +z, 90 from +x, 180 from -z (degrees)"""
    out = []
    for y in ys:
        row = []
        for ph in phis:
            a = math.radians(ph); d = V3((math.sin(a), 0, math.cos(a)))
            row.append((V3((cx, y, cz)) + d * R, -d))
        out.append(row)
    return out


# ------------------------------------------------------------ UV atlases
def uv_px(rect, tex, s, t, m=0.6):
    """(s, t) in 0..1 inside a pixel rect (x, y from the top, w, h) of a tex (w, h) -> blender uv, m px inside"""
    x, y, w, h = rect[:4]
    tw, th = tex
    u = (x + m + s * (w - 2 * m)) / tw
    v = 1 - (y + m + (1 - t) * (h - 2 * m)) / th
    return (u, v)


def face_axis(n):
    ax = max(range(3), key=lambda i: abs(n[i]))
    return ax, (1 if n[ax] > 0 else -1)


def uv_fill(o, rect, tex):
    """every face of o into one pixel rect (a flat colour of an atlas): box-projected, scaled to the part's size"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    pts = [b2g(mw @ v.co) for v in me.vertices]
    lo = V3([min(p[i] for p in pts) for i in range(3)]); hi = V3([max(p[i] for p in pts) for i in range(3)])
    ext = hi - lo
    for p in me.polygons:
        n = b2g(mw.to_3x3() @ p.normal)
        ax, _ = face_axis(n)
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for li in p.loop_indices:
            q = pts[me.loops[li].vertex_index]
            s = (q[a] - lo[a]) / (ext[a] or 1); t = (q[b] - lo[b]) / (ext[b] or 1)
            uv[li].uv = uv_px(rect, tex, s, t)
    return o


def uv_box_world(o, size=1.0):
    """tiling box UVs in world metres / size (the glass streaks, grain)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    for p in me.polygons:
        n = b2g(mw.to_3x3() @ p.normal)
        ax, sg = face_axis(n)
        for li in p.loop_indices:
            q = b2g(mw @ me.vertices[me.loops[li].vertex_index].co)
            if ax == 0: u, v = -q.z * sg, q.y
            elif ax == 1: u, v = q.x, -q.z * sg
            else: u, v = q.x * sg, q.y
            uv[li].uv = (u / size, v / size)
    return o


class Paint:
    """the body texture of one car: orthographic maps of its sides, top, front and back in one image (the left side
    seen from +x has the car's front on the left, the right side from -x has it on the right, so writing reads on both).
    Faces pick their map by their normal. Draw with world coordinates; the base is white with a faint grain (tint) or a
    livery."""
    def __init__(self, name, F, W=256, side_h=80, top_h=64, end_h=64, y0=0.0):
        self.name = name; self.F = F; self.y0 = y0  # F = (zmin, zmax, ymax, hw)
        H = 2 * side_h + top_h + end_h
        self.W, self.H = W, H
        zmin, zmax, ymax, hw = F
        self.R = {'L': (0, 0, W, side_h), 'R': (0, side_h, W, side_h), 'T': (0, 2 * side_h, W, top_h),
                  'F': (0, H - end_h, W // 4, end_h), 'B': (W // 4, H - end_h, W // 4, end_h), 'U': (W // 2, H - end_h, W // 4, end_h),
                  'X': (3 * W // 4, H - end_h, W // 4, end_h)}
        self.px = np.ones((H, W, 3), dtype=np.float32)

    # world -> (region, s, t)
    def st(self, reg, p):
        zmin, zmax, ymax, hw = self.F
        x, y, z = p
        yt = (y - self.y0) / (ymax - self.y0)
        if reg == 'L': return (zmax - z) / (zmax - zmin), yt
        if reg == 'R': return (z - zmin) / (zmax - zmin), yt
        if reg == 'T': return (z - zmin) / (zmax - zmin), (x + hw) / (2 * hw)
        if reg == 'F': return (x + hw) / (2 * hw), yt
        if reg == 'B': return (hw - x) / (2 * hw), yt
        if reg == 'U': return (z - zmin) / (zmax - zmin), (x + hw) / (2 * hw)
        return 0.5, 0.5

    def pix(self, reg, p):
        s, t = self.st(reg, p)
        x, y, w, h = self.R[reg]
        return x + s * w, y + (1 - t) * h

    def region_of(self, n, p=None):
        ax, sg = face_axis(n)
        if ax == 0: return 'L' if sg > 0 else 'R'
        if ax == 1: return 'T' if sg > 0 else 'U'
        return 'F' if sg > 0 else 'B'

    def uv(self, o, override=None):
        """UVs of a body part: each face into the map its normal faces. override(n, centre) can force a region."""
        me = o.data
        if not me.uv_layers: me.uv_layers.new(name='UVMap')
        uv = me.uv_layers.active.data
        mw = o.matrix_world
        for p in me.polygons:
            n = b2g(mw.to_3x3() @ p.normal)
            c = b2g(mw @ p.center)
            reg = (override(n, c) if override else None) or self.region_of(n)
            for li in p.loop_indices:
                q = b2g(mw @ me.vertices[me.loops[li].vertex_index].co)
                s, t = self.st(reg, q)
                uv[li].uv = uv_px(self.R[reg], (self.W, self.H), clamp(s, 0, 1), clamp(t, 0, 1), m=0.6)
        return o

    # painting (colours as hex)
    def fill(self, reg, col, var=0.035, seed=1):
        x, y, w, h = self.R[reg]
        r = np.random.default_rng(seed)
        lo = r.random((h // 4 + 1, w // 4 + 1))
        big = np.kron(lo, np.ones((4, 4)))[:h, :w]
        n = 0.6 * big + 0.4 * r.random((h, w))
        self.px[y:y + h, x:x + w] = hexrgb(col)[None, None] * (1 - var + 2 * var * n[:, :, None])

    def line(self, regs, pts, col, w=1.0):
        """a polyline of world points on each region in regs (seams, shut lines)"""
        for reg in regs:
            q = [self.pix(reg, p) for p in pts]
            for (x0, y0), (x1, y1) in zip(q, q[1:]): px_line(self.px, x0, y0, x1, y1, col, w)

    def rect(self, reg, p0, p1, col):
        (x0, y0), (x1, y1) = self.pix(reg, p0), self.pix(reg, p1)
        xa, xb = sorted((int(round(x0)), int(round(x1)))); ya, yb = sorted((int(round(y0)), int(round(y1))))
        self.px[ya:yb, xa:xb] = hexrgb(col)

    def poly(self, reg, pts, col):
        """a filled polygon of world points (livery shapes)"""
        q = [self.pix(reg, p) for p in pts]
        x, y, w, h = self.R[reg]
        yy, xx = np.mgrid[y:y + h, x:x + w] + 0.5
        inside = np.zeros(yy.shape, bool)
        n = len(q)
        for i in range(n):
            (x0, y0), (x1, y1) = q[i], q[(i + 1) % n]
            cond = ((y0 > yy) != (y1 > yy)) & (xx < (x1 - x0) * (yy - y0) / ((y1 - y0) or 1e-9) + x0)
            inside ^= cond
        sub = self.px[y:y + h, x:x + w]
        sub[inside] = hexrgb(col)

    def text(self, reg, p, s, scale, col, anchor='c', shadow=None):
        """bitmap text at world point p (its centre with anchor c), reading left to right as seen on that region"""
        x, y = self.pix(reg, p)
        w = len(s) * 6 * scale - scale; h = 7 * scale
        x0 = int(round(x - (w / 2 if anchor == 'c' else 0))); y0 = int(round(y - h / 2))
        if shadow is not None:
            text_px(self.px, s, x0 + max(1, scale // 2), y0 + max(1, scale // 2), scale, shadow)
        text_px(self.px, s, x0, y0, scale, col)

    def image(self):
        return lib._image(self.name, np.clip(self.px, 0, 1))


# the trim atlas: 128 x 128, 16 px cells. name: (x, y, w, h, colour, roughness, metallic)
TEX_TRIM = (128, 128)
TRIM = {
    'black': (0, 0, 16, 16, 0x1c1c21, 0.3, 0.0),     # gloss black plastic (pillars, mirror caps, surrounds)
    'plastic': (16, 0, 16, 16, 0x2b2b31, 0.62, 0.0),  # textured bumper / cladding plastic
    'rubber': (32, 0, 16, 16, 0x1a1a1d, 0.88, 0.0),   # tyres
    'wall': (48, 0, 16, 16, 0x26262a, 0.8, 0.0),      # tyre sidewalls
    'chrome': (64, 0, 16, 16, 0xdde2ea, 0.1, 1.0),
    'silver': (80, 0, 16, 16, 0xb4bac4, 0.28, 0.85),  # alloy rims
    'metal': (96, 0, 16, 16, 0x5c6068, 0.45, 0.7),    # exhaust, chassis, steel wheels in grey
    'white': (112, 0, 16, 16, 0xf2f2ee, 0.35, 0.0),
    'tread': (0, 16, 16, 16, 0x1a1a1d, 0.9, 0.0),     # one tread block (each tyre segment shows one)
    'grille': (16, 16, 32, 16, 0x141418, 0.5, 0.2),   # honeycomb
    'plate': (48, 16, 48, 16, 0xf4f1e4, 0.35, 0.0),
    'amber': (96, 16, 16, 16, 0xff9a1a, 0.2, 0.0),    # reflectors
    'red': (112, 16, 16, 16, 0xc01818, 0.2, 0.0),
    'glass': (0, 32, 16, 16, 0x23364e, 0.08, 0.6),    # lod1's windows
    'hazard': (16, 32, 32, 16, 0xffd21a, 0.4, 0.0),   # yellow / black stripes
    'sticker': (48, 32, 64, 16, 0x7dff4f, 0.4, 0.0),
    'dark': (112, 32, 16, 16, 0x0c0c0e, 0.9, 0.0),    # inside the wheel wells, vents
    'steel': (0, 48, 16, 16, 0xe8e8ea, 0.32, 0.6),    # white steel wheels (van, bus, truck)
    'gold': (16, 48, 16, 16, 0xffc23a, 0.2, 1.0),
    'pink': (32, 48, 16, 16, 0xff4fd8, 0.3, 0.0),
    'yellow': (48, 48, 16, 16, 0xffe14d, 0.3, 0.0),
    'sticker2': (64, 48, 64, 16, 0xffe14d, 0.4, 0.0),
    'sign': (0, 64, 64, 32, 0x111111, 0.3, 0.0),      # a lit sign / destination board
    'menu': (64, 64, 64, 32, 0xffffff, 0.4, 0.0),
    'cone': (0, 96, 32, 32, 0xd8a050, 0.6, 0.0),      # waffle
    'cream': (32, 96, 16, 16, 0xff9ad5, 0.35, 0.0),
    'cream2': (48, 96, 16, 16, 0xfff4e0, 0.35, 0.0),
    'cherry': (64, 96, 16, 16, 0xe8323c, 0.15, 0.0),
    'choc': (80, 96, 16, 16, 0x5a3418, 0.4, 0.0),
    'mint': (96, 96, 16, 16, 0xbff5e4, 0.35, 0.0),
    'blue': (112, 96, 16, 16, 0x2f6fe0, 0.3, 0.0),
    'orange': (96, 112, 16, 16, 0xe86a22, 0.3, 0.0),
    'cyan': (112, 112, 16, 16, 0x4fd8ff, 0.3, 0.0),
}


def trim_textures(name, draw_extra=None):
    """the trim atlas (base colour) + its metal/roughness map (G = roughness, B = metal)"""
    W, H = TEX_TRIM
    px = np.zeros((H, W, 3), np.float32); orm = np.ones((H, W, 3), np.float32)
    r = np.random.default_rng(11)
    for k, (x, y, w, h, col, ro, me) in TRIM.items():
        n = r.random((h, w))[:, :, None]
        px[y:y + h, x:x + w] = hexrgb(col)[None, None] * (0.94 + 0.12 * n)
        orm[y:y + h, x:x + w] = (1.0, ro, me)
    def cell(k):
        x, y, w, h = TRIM[k][:4]; return px[y:y + h, x:x + w]
    # a tread block: two chunky lugs on black
    t = cell('tread'); t[:] = hexrgb(0x121214)
    t[1:7, 2:14] = hexrgb(0x2a2a2e); t[9:15, 0:6] = hexrgb(0x2a2a2e); t[9:15, 10:16] = hexrgb(0x2a2a2e)
    # tyre sidewall: a raised lettering stripe
    s = cell('wall'); s[6:9, :] = hexrgb(0x34343a)
    # honeycomb grille
    g = cell('grille'); g[:] = hexrgb(0x0e0e10)
    for yy in range(0, 16, 4):
        for xx in range(0, 32, 4):
            o = 2 if (yy // 4) % 2 else 0
            g[yy:yy + 3, (xx + o) % 32:(xx + o) % 32 + 3] = hexrgb(0x2e2e34)
    # hazard stripes
    hz = cell('hazard')
    yy, xx = np.mgrid[0:16, 0:32]
    hz[((xx + yy) // 4) % 2 == 0] = hexrgb(0x141414)
    # waffle cone: a diamond lattice
    c = cell('cone'); c[:] = hexrgb(0xe0aa5c)
    yy, xx = np.mgrid[0:32, 0:32]
    c[((xx + yy) % 8 == 0) | ((xx - yy) % 8 == 0)] = hexrgb(0xa8702e)
    if draw_extra: draw_extra(px, cell)
    base = lib._image(name + '_t', np.clip(px, 0, 1))
    img = bpy.data.images.new(name + '_mr', W, H, alpha=False); img.colorspace_settings.is_data = True  # before the pixels: blender 5.2 wipes a generated image when its colour space changes
    a = np.ones((H, W, 4), np.float32); a[:, :, :3] = orm[::-1]
    img.pixels.foreach_set(a.ravel()); img.file_format = 'PNG'; img.pack(); assert np.array(img.pixels[:], np.float32)[1::4].max() > 0, img.name + ': roughness map came out black (set the colour space before the pixels)'
    return base, img


def mat_trim(name, draw_extra=None):
    base, mr = trim_textures(name, draw_extra)
    m = mat(name, 0xffffff, rough=0.5, tex=base)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = mr; t.interpolation = 'Closest'
    sp = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(t.outputs['Color'], sp.inputs['Color'])
    nt.links.new(sp.outputs['Green'], b.inputs['Roughness']); nt.links.new(sp.outputs['Blue'], b.inputs['Metallic'])
    return m


def mat_glass(name, img):
    """opaque dark blue-grey glass on the car's own glass map (glass_paint paints it once the car is built)"""
    return mat(name, 0xffffff, rough=0.05, metal=0.55, tex=img)


# ------------------------------------------------------------ the glass map: what the windows show
G_DARK, G_MID, G_LITE = 0x131a24, 0x2b3d55, 0x4d6c92  # the inside low down -> the far windows (the street through the car)
G_SEAT, G_FAR, G_DASH, G_RIM = 0x0b0f15, 0x18212d, 0x080b0f, 0x2c3746  # (the wheel's rim a shade up: it shows on the seat)
G_MOQ, G_MOQ2 = 0x40163a, 0x6a2660  # the bus's seats


def g_grad(G, reg, y0, y1, top=G_LITE):
    """a region's base: dark at y0 (the window's bottom), light at y1, by world height"""
    x, y, w, h = G.R[reg]
    for r in range(h):
        t = 1 - (r + 0.5) / h
        yw = G.y0 + t * (G.F[2] - G.y0)
        k = clamp((yw - y0) / ((y1 - y0) or 1), 0, 1)
        if k < 0.55: c = hexrgb(G_DARK) + (hexrgb(G_MID) - hexrgb(G_DARK)) * (k / 0.55)
        else: c = hexrgb(G_MID) + (hexrgb(top) - hexrgb(G_MID)) * ((k - 0.55) / 0.45)
        G.px[y + r, x:x + w] = c


def g_poly(G, regs, pts, col, end=False):
    """a filled shape: pts (z, y) on the sides, (x, y) at the ends"""
    for reg in regs: G.poly(reg, [((u, v, 0.0) if end else (0.0, v, u)) for u, v in pts], col)


def g_round(cx, cy, w, h, r=0.035, n=3):
    """a rounded box's outline (headrests, seat tops)"""
    r = min(r, w / 2, h / 2); out = []
    for qx, qy, a0 in ((cx + w / 2 - r, cy + h / 2 - r, 0), (cx - w / 2 + r, cy + h / 2 - r, 90), (cx - w / 2 + r, cy - h / 2 + r, 180), (cx + w / 2 - r, cy - h / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n); out.append((qx + r * math.cos(a), qy + r * math.sin(a)))
    return out


def g_streaks(G, regs):
    """the reflections: a pale diagonal band every 1.4 m (in metres on every view, in chunky 3 cm steps)"""
    for reg in regs:
        x, y, w, h = G.R[reg]
        zmin, zmax, ymax, hw = G.F
        mx = ((zmax - zmin) if reg in 'LRTU' else 2 * hw) / w
        my = ((ymax - G.y0) if reg in 'LRFBX' else 2 * hw) / h
        yy, xx = np.mgrid[0:h, 0:w]
        u = np.floor(xx * mx / 0.03) * 0.03; v = np.floor(yy * my / 0.03) * 0.03
        band = (u + v * 0.8 + (0.5 if reg in 'RB' else 0.0)) % 1.4
        sub = G.px[y:y + h, x:x + w]
        hi = (band > 0.08) & (band < 0.25); ed = (band >= 0.25) & (band < 0.31)
        sub[hi] = sub[hi] * 0.3 + hexrgb(0x7a9cc4) * 0.7
        sub[ed] = sub[ed] * 0.45 + hexrgb(0x5b7da6) * 0.55


def g_cabin(G, cab, yr):
    """the seats, dash and wheel through the glass. yr: region -> (y0, y1) of the glass that faces it"""
    rows = sorted(cab.get('rows', []), key=lambda r_: -r_[0])  # front first
    for i, (zc, yt, xs) in enumerate(rows):  # from the side: headrest + a seat back leaning back
        g_poly(G, 'LR', [(zc + 0.13, cab['belt'] - 0.2), (zc + 0.02, yt - 0.19), (zc - 0.15, yt - 0.205), (zc - 0.08, cab['belt'] - 0.2)], G_SEAT)
        g_poly(G, 'LR', g_round(zc - 0.06, yt - 0.085, 0.18, 0.17), G_SEAT)
    if 'F' in yr and rows:  # through the windscreen: the far rows, the front row, the dash, the wheel
        for zc, yt, xs in rows[1:]:
            for s in (1, -1): g_poly(G, 'F', g_round(s * xs, yt - 0.075, 0.16, 0.13), G_FAR, end=True)
        zc, yt, xs = rows[0]
        for s in (1, -1):
            g_poly(G, 'F', [(s * xs - 0.25, cab['dash'] - 0.05), (s * xs - 0.21, yt - 0.19), (s * xs + 0.21, yt - 0.19), (s * xs + 0.25, cab['dash'] - 0.05)], G_SEAT, end=True)
            g_poly(G, 'F', g_round(s * xs, yt - 0.085, 0.22, 0.17), G_SEAT, end=True)
        hw = G.F[3]
        g_poly(G, 'F', [(-hw, G.y0), (-hw, cab['dash'] - 0.03), (-hw * 0.5, cab['dash']), (hw * 0.5, cab['dash']), (hw, cab['dash'] - 0.03), (hw, G.y0)], G_DASH, end=True)
        if cab.get('wheel'):
            wx, wy, rx, ry = cab['wheel']
            ring = [(wx + rx * math.cos(a), wy + ry * math.sin(a), 0.0) for a in np.linspace(0, 2 * math.pi, 25)]
            G.line('F', [(wx, wy - ry, 0.0), (wx, cab['dash'] - 0.02, 0.0)], G_DASH, 2.0)  # (the column)
            G.line('F', ring, G_RIM, 2.0)
    if 'B' in yr and rows and cab.get('shelf'):  # through the back window: the front row far, the back row near, the shelf
        for zc, yt, xs in rows[:-1]:
            for s in (1, -1): g_poly(G, 'B', g_round(s * xs, yt - 0.075, 0.16, 0.13), G_FAR, end=True)
        zc, yt, xs = rows[-1]
        y0, y1 = cab['shelf']
        for s in (1, -1):
            g_poly(G, 'B', [(s * xs - 0.26, y0), (s * xs - 0.22, yt - 0.19), (s * xs + 0.22, yt - 0.19), (s * xs + 0.26, y0)], G_SEAT, end=True)
            g_poly(G, 'B', g_round(s * xs, yt - 0.085, 0.22, 0.17), G_SEAT, end=True)
        hw = G.F[3]
        g_poly(G, 'B', [(-hw, G.y0), (-hw, y1), (hw, y1), (hw, G.y0)], G_DASH, end=True)
    bus = cab.get('bus')
    if bus:  # rows of high-backed seats down both sides, the poles by the doors, the driver up front
        for zc in bus['seats']:  # (the seats in the company moquette: they read through the dark glass)
            g_poly(G, 'LR', [(zc + 0.09, bus['y0']), (zc + 0.05, bus['ytop'] - 0.07), (zc - 0.01, bus['ytop']), (zc - 0.12, bus['ytop'] - 0.01), (zc - 0.11, bus['y0'])], G_MOQ)
            g_poly(G, 'LR', [(zc + 0.05, bus['ytop'] - 0.07), (zc - 0.01, bus['ytop']), (zc - 0.12, bus['ytop'] - 0.01), (zc - 0.115, bus['ytop'] - 0.07)], G_MOQ2)
        for zp in bus.get('poles', ()):
            G.line('L', [(0.0, 0.75, zp), (0.0, 2.75, zp)], 0xd8b020, 2.0)
            G.line('L', [(0.0, 0.75, zp - 0.025), (0.0, 2.75, zp - 0.025)], 0x7a6010, 1.0)
        dz, dyt, dx = bus['drv']
        g_poly(G, 'R', [(dz + 0.12, bus['y0']), (dz + 0.04, dyt - 0.19), (dz - 0.12, dyt - 0.205), (dz - 0.2, bus['y0'])], G_SEAT)
        g_poly(G, 'R', g_round(dz - 0.03, dyt - 0.085, 0.22, 0.17), G_SEAT)
        hw = G.F[3]
        for k, yb in enumerate(bus['rowtops']):  # through the screen: seat tops shrinking away down the bus
            for s in (1, -1):
                g_poly(G, 'F', g_round(s * (0.62 - 0.03 * k), yb, 0.62 - 0.08 * k, 0.2 - 0.03 * k, 0.04), G_MOQ, end=True)
        g_poly(G, 'F', [(dx - 0.25, bus['dash']), (dx - 0.21, dyt - 0.19), (dx + 0.21, dyt - 0.19), (dx + 0.25, bus['dash'])], G_SEAT, end=True)
        g_poly(G, 'F', g_round(dx, dyt - 0.085, 0.24, 0.17), G_SEAT, end=True)
        g_poly(G, 'F', [(-hw, G.y0), (-hw, bus['dash']), (hw, bus['dash']), (hw, G.y0)], G_DASH, end=True)
        wx, wy, rx, ry = bus['wheel']
        G.line('F', [(wx + rx * math.cos(a), wy + ry * math.sin(a), 0.0) for a in np.linspace(0, 2 * math.pi, 25)], G_RIM, 2.0)
        for k in range(5):  # the back row, over the engine
            g_poly(G, 'B', g_round(-0.96 + 0.48 * k, bus['back'], 0.4, 0.2, 0.05), G_MOQ, end=True)
            g_poly(G, 'B', g_round(-0.96 + 0.48 * k, bus['back'] + 0.06, 0.4, 0.08, 0.04), G_MOQ2, end=True)


def glass_paint(car):
    """the glass's own map, one per car: dark low down, the far windows lighter, the seats, headrests, dash and wheel
    as dark shapes in it (from car.cabin), the streaky reflections over the lot. Each glass face goes into the view it
    faces (sides, front, back, top); mirrors into a plain spot"""
    bpy.context.view_layer.update()
    cab = getattr(car, 'cabin', None) or {}
    faces, pts = [], []
    for o in car.body:
        me = o.data
        gi = {i for i, m in enumerate(me.materials) if m == car.glass}
        if not gi: continue
        mw = o.matrix_world
        for p in me.polygons:
            if p.material_index in gi:
                q = [b2g(mw @ me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
                faces.append((o, p, b2g(mw.to_3x3() @ p.normal), q)); pts += q
    if not faces: return
    zmin, zmax = min(q.z for q in pts) - 0.03, max(q.z for q in pts) + 0.03
    ylo, yhi = min(q.y for q in pts) - 0.03, max(q.y for q in pts) + 0.03
    hw = max(abs(q.x) for q in pts) + 0.03
    G = Paint('glass_' + car.id, (zmin, zmax, yhi, hw), W=cab.get('W', 256), side_h=cab.get('side_h', 48), top_h=8, end_h=cab.get('end_h', 32), y0=ylo)

    def cands(n):
        out = []
        for ax in sorted(range(3), key=lambda i: -abs(n[i])):
            if ax == 0: out.append('L' if n.x > 0 else 'R')
            elif ax == 2: out.append('F' if n.z > 0 else 'B')
            else:
                if abs(n.z) > 0.2: out.append('F' if n.z > 0 else 'B')
                out.append('T' if n.y > 0 else 'U')
        return out
    plan, yr = [], {}
    for o, p, n, q in faces:
        forced = 'X' if '_mgl_' in o.name else None
        best = None
        for reg in cands(n):
            sts = [G.st(reg, v) for v in q]
            out = [uv_px(G.R[forced or reg], (G.W, G.H), clamp(a, 0, 1), clamp(b, 0, 1)) for a, b in sts]
            best = best or (reg, out)
            if _area2(out) > 1e-9: best = (reg, out); break
        plan.append((o, p, best[1]))
        if not forced:
            lo_, hi_ = yr.get(best[0], (1e9, -1e9)); yr[best[0]] = (min(lo_, min(v.y for v in q)), max(hi_, max(v.y for v in q)))
    # paint: the base per view, the cabin, the reflections
    for reg in 'LRTUFBX':
        a, b = yr.get(reg, (ylo, yhi))
        if reg in 'LR' and 'belt' in cab: a, b = cab['belt'], cab['top']
        g_grad(G, reg, a, b, top=cab.get('far', G_LITE) if reg == 'F' else G_LITE)
    G.px[G.R['X'][1]:G.R['X'][1] + G.R['X'][3], G.R['X'][0]:G.R['X'][0] + G.R['X'][2]] = hexrgb(G_MID)
    g_grad(G, 'X', ylo, yhi)
    g_cabin(G, cab, yr)
    g_streaks(G, 'LRTUFBX')
    for o, p, out in plan:
        me = o.data
        if not me.uv_layers: me.uv_layers.new(name='UVMap')
        uv = me.uv_layers.active.data
        for li, u in zip(p.loop_indices, out): uv[li].uv = u
    car.gimg.scale(G.W, G.H)
    a = np.ones((G.H, G.W, 4), np.float32); a[:, :, :3] = np.clip(G.px, 0, 1)[::-1]
    car.gimg.pixels.foreach_set(a.ravel()); car.gimg.file_format = 'PNG'; car.gimg.pack()
    car.gpaint = G
    if isinstance(arg('dump'), str):
        os.makedirs(arg('dump'), exist_ok=True)
        im = bpy.data.images.new('gdump_' + car.id, G.W, G.H, alpha=False); im.pixels.foreach_set(a.ravel())
        im.filepath_raw = os.path.join(arg('dump'), car.id + '_glass.png'); im.file_format = 'PNG'; im.save()


def flat_ao(o, v=1.0):
    """a constant AO layer (lamps stay as bright as the game makes them)"""
    me = o.data
    for c in list(me.color_attributes): me.color_attributes.remove(c)
    ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER')
    me.color_attributes.active_color = ca
    for d in ca.data: d.color = (v, v, v, 1.0)
    return o


# ------------------------------------------------------------ wheels: axle along x, outer face +x, centred on the hub
def lathe_x(name, prof, seg, m, uvfn, x0=0.0, phase=0.0, cap_end=False):
    """revolve [(radius, x)] round the game x axis. uvfn(band, k, corner) -> uv (corner 0..3 round the quad)."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for r, x in prof:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * (k + phase) / seg
            ring.append(bm.verts.new(gv(x + x0, math.cos(a) * r, math.sin(a) * r)))
        rings.append(ring)
    for b in range(len(rings) - 1):
        A_, B_ = rings[b], rings[b + 1]
        for k in range(seg):
            kk = (k + 1) % seg
            if prof[b][0] < 1e-6 and prof[b + 1][0] < 1e-6: continue
            f = bm.faces.new((A_[k], A_[kk], B_[kk], B_[k]))
            for c, lp in enumerate(f.loops): lp[uvl].uv = uvfn(b, k, c)
    if cap_end:
        f = bm.faces.new(rings[-1])
        for c, lp in enumerate(f.loops):
            a = 2 * math.pi * c / seg; lp[uvl].uv = uvfn(-1, c, (math.cos(a), math.sin(a)))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 50)
    return o


def cell_uv(key, s, t):
    return uv_px(TRIM[key], TEX_TRIM, s, t, m=1.0)


def quad_cell(key):
    """uvfn for lathe_x: every quad fills the cell (a tread block per segment)"""
    Q = ((0, 0), (1, 0), (1, 1), (0, 1))
    def f(b, k, c):
        if b < 0: return cell_uv(key, 0.5 + 0.4 * c[0], 0.5 + 0.4 * c[1])
        return cell_uv(key, *Q[c])
    return f


def band_cells(keys):
    """uvfn: band b uses cell keys[b] (stretched round, a sliver per segment so it never has zero area)"""
    Q = ((0, 0), (1, 0), (1, 1), (0, 1))
    def f(b, k, c):
        key = keys[min(b, len(keys) - 1)] if b >= 0 else keys[-1]
        if b < 0: return cell_uv(key, 0.5 + 0.4 * c[0], 0.5 + 0.4 * c[1])
        s, t = Q[c]
        return cell_uv(key, s, t)
    return f


def tyre(name, r, w, rb, m, seg=16, x0=0.0, chunky=False):
    """the tyre: inner bead, sidewall, rounded shoulders, the tread band (a tread block per segment), outer side"""
    sh = 0.9 if chunky else 0.94
    prof = [(0.0, -w / 2 + 0.03), (rb, -w / 2 + 0.008), (r, -w * 0.3), (r, w * 0.3), (r * sh, w / 2), (rb, w / 2 - 0.008)]  # (closed on the inside)
    o = lathe_x(name, prof, seg, m, band_cells(['dark', 'rubber', 'tread', 'rubber', 'wall']), x0=x0, phase=0.5)
    return o


def spoke(bm, uvl, a, r0, r1, w0, w1, x_in, x_out0, x_out1, key):
    """one spoke from radius r0 to r1 at angle a (in the y-z plane), w0 / w1 wide, standing from x_in to x_out"""
    c, s = math.cos(a), math.sin(a)
    t = (-s, c)  # across the spoke
    def P(rr, ww, x): return gv(x, c * rr + t[0] * ww, s * rr + t[1] * ww)
    vs = [bm.verts.new(P(r0, -w0 / 2, x_in)), bm.verts.new(P(r0, w0 / 2, x_in)), bm.verts.new(P(r1, w1 / 2, x_in)), bm.verts.new(P(r1, -w1 / 2, x_in)),
          bm.verts.new(P(r0, -w0 / 2, x_out0)), bm.verts.new(P(r0, w0 / 2, x_out0)), bm.verts.new(P(r1, w1 / 2, x_out1)), bm.verts.new(P(r1, -w1 / 2, x_out1))]
    for q in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        f = bm.faces.new([vs[i] for i in q])
        for i, lp in enumerate(f.loops): lp[uvl].uv = cell_uv(key, *((0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8))[i])


def wheel_mesh(name, r, w, style, trim, seg=16, dual=0.0, side=1):
    """a whole wheel as one mesh (tyre(s) + rim), axle along x, outer face toward +x (side -1 mirrors it)"""
    parts = []
    rb = r * (0.66 if style in ('alloy', 'chrome6', 'alloy6') else 0.6)
    face = w / 2
    parts.append(tyre(name + '_ty', r, w, rb, trim, seg, chunky=style == 'chrome6'))
    if dual:
        parts.append(tyre(name + '_ty2', r, w, rb, trim, seg, x0=-dual))
        parts.append(lathe_x(name + '_sp', [(rb, -dual + w / 2 - 0.03), (rb, -w / 2 + 0.03)], seg, trim, band_cells(['dark'])))  # (into both beads)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    key = {'alloy': 'silver', 'alloy6': 'silver', 'chrome6': 'chrome', 'cap': 'silver', 'steel': 'steel', 'steelb': 'black', 'truck': 'steel'}[style]
    if style in ('alloy', 'alloy6', 'chrome6'):
        n = 5 if style == 'alloy' else 6
        lip = lathe_x(name + '_lip', [(rb + 0.012, face - 0.01), (rb - 0.012, face - 0.002)], seg, trim, band_cells([key]))
        dish = lathe_x(name + '_dish', [(rb - 0.012, face - 0.002), (0.0, face - 0.055)], seg, trim, band_cells(['dark']), phase=0.5)
        parts += [lip, dish]
        ws = (0.055, 0.075) if n == 5 else (0.04, 0.06)
        for k in range(n):
            a = 2 * math.pi * k / n + math.pi / 2
            spoke(bm, uvl, a, 0.035, rb - 0.012, ws[0] * r / 0.33, ws[1] * r / 0.33, face - 0.052, face + 0.004, face - 0.012, key)
        cap = lathe_x(name + '_cap', [(r * 0.2, face - 0.03), (r * 0.17, face + 0.01), (0.0, face + 0.02)], 8, trim, band_cells([key, 'chrome']))
        parts.append(cap)
    else:
        # a steel disc dished in, round holes near the rim, a raised hub with nuts, a domed cap
        hole_r = rb * 0.62
        if style == 'cap':  # only the outer ring shows round the hubcap
            disc = lathe_x(name + '_disc', [(rb + 0.012, face - 0.01), (rb - 0.004, face - 0.004), (rb * 0.8, face - 0.042)], seg, trim, band_cells([key, key]))
        else:
            disc = lathe_x(name + '_disc', [(rb + 0.012, face - 0.01), (rb - 0.006, face - 0.004), (rb * 0.45, face - 0.04), (0.0, face - 0.03)], seg, trim, band_cells([key, key, key]))
        parts.append(disc)
        nh = 8 if style == 'truck' else (6 if style != 'cap' else 10)
        for k in range(nh):
            a = 2 * math.pi * (k + 0.5) / nh
            hole_r_ = rb * 0.5 if style == 'cap' else hole_r
            cy, cz = math.cos(a) * hole_r_, math.sin(a) * hole_r_
            hr = rb * (0.11 if style != 'cap' else 0.075)
            xs = face + 0.0215 if style == 'cap' else face - 0.036 + 0.0045
            ring = [bm.verts.new(gv(xs, cy + math.cos(2 * math.pi * j / 6) * hr, cz + math.sin(2 * math.pi * j / 6) * hr * (1.5 if style == 'cap' else 1.0))) for j in range(6)]
            f = bm.faces.new(ring)
            for j, lp in enumerate(f.loops): lp[uvl].uv = cell_uv('dark', 0.5 + 0.4 * math.cos(2 * math.pi * j / 6), 0.5 + 0.4 * math.sin(2 * math.pi * j / 6))
        if style == 'cap':
            cap = lathe_x(name + '_cap', [(rb * 0.86, face - 0.036), (rb * 0.72, face + 0.012), (0.0, face + 0.03)], seg, trim, band_cells(['silver', 'chrome']), phase=0.5)
        elif style == 'truck':
            cap = lathe_x(name + '_cap', [(rb * 0.4, face - 0.044), (rb * 0.36, face + 0.03), (rb * 0.18, face + 0.08), (0.0, face + 0.09)], 10, trim, band_cells(['steel', 'metal', 'chrome']))
            for k in range(6):  # wheel nuts round the hub
                a = 2 * math.pi * k / 6
                c_ = cyl(0.022, 0.05, (face + 0.02, math.cos(a) * rb * 0.3, math.sin(a) * rb * 0.3), trim, axis='x', seg=4, name=name + f'_nut{k}')
                uv_fill(c_, TRIM['chrome'], TEX_TRIM); parts.append(c_)
        else:
            cap = lathe_x(name + '_cap', [(rb * 0.36, face - 0.044), (rb * 0.34, face + 0.008), (rb * 0.2, face + 0.02), (0.0, face + 0.024)], 10, trim, band_cells(['black' if style == 'steelb' else 'chrome', 'chrome', 'chrome']))
        parts.append(cap)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    sp = _obj(name + '_spk', bm, trim)
    smooth(sp, 30)
    parts.append(sp)
    o = join(parts, name)
    me = o.data
    if side < 0:
        me.transform(Matrix.Scale(-1, 4, V3((1, 0, 0))))
        me.flip_normals()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.to_mesh(me); bm.free()
    smooth(o, 45)
    return o


# ------------------------------------------------------------ one car: materials, parts, the shell helpers
class Car:
    def __init__(self, cid, F, livery=None, W=256, side_h=80, top_h=64, end_h=64, atlas=None):
        self.id = cid
        self.F = F  # (zmin, zmax, ymax, hw) of the body map
        self.paint = Paint((livery or 'tint') + '_t', F, W, side_h, top_h, end_h)
        self.pimg = bpy.data.images.new(self.paint.name, self.paint.W, self.paint.H, alpha=False)
        self.livery = livery
        if livery:  # a fixed livery: the colours are in the texture, the game leaves it alone
            self.tint = mat(livery, 0xffffff, rough=0.26, metal=0.08, clearcoat=1.0, tex=self.pimg)
        else:       # white + grain: the game colours it per car
            self.tint = mat('tint', 0xffffff, rough=0.26, metal=0.12, clearcoat=1.0, tex=self.pimg)
        self.trim = mat_trim('trim', atlas)
        self.gimg = bpy.data.images.new('glass_' + cid, 4, 4, alpha=False)  # (sized and painted once the car is built: glass_paint)
        self.glass = mat_glass('glass', self.gimg)
        # (as authored they look switched off: parked cars draw them; traffic swaps in the game's lit ones)
        self.lamp_m = mat('lamp', 0xe4ecf4, rough=0.06, metal=0.25, clearcoat=1.0)
        self.tail_m = mat('tail', 0xa8141a, rough=0.1, clearcoat=1.0)
        self.ind_m = mat('ind', 0xe8901c, rough=0.1, clearcoat=1.0)
        self.body, self.lamps, self.tails, self.inds, self.lod1 = [], [], [], [], []
        self.tint_parts = []
        self.wheels = []
        self.meta = {}
        self.S = None
        self.n = 0

    def nm(self, s):
        self.n += 1
        return f'{self.id}_{s}_{self.n}'

    # parts
    def add_tint(self, o):
        set_mats(o, [self.tint]); self.tint_parts.append(o); self.body.append(o); return o

    def add_trim(self, o, key=None):
        set_mats(o, [self.trim])
        if key: uv_fill(o, TRIM[key], TEX_TRIM)
        self.body.append(o); return o

    def add_glass(self, o):
        set_mats(o, [self.glass]); uv_box_world(o, 1.4); self.body.append(o); return o

    def surf(self, objs):
        self.S = Surf(objs)

    def on(self, name, rays, key, off=0.006, depth=0.03, to=None, m=None, uv_full=False, sub=1, over=None):
        """a part cast onto the body: key = trim cell (filled or, uv_full, the face spans it). sub = finer grid on
        curved spots; the face is pushed out wherever the body would bulge through it"""
        rays = refine(rays, sub)
        g = cast_grid(self.S, rays)
        off = off + clearance(self.S, rays, g, off)
        if over is not None: off = max(off, over['off'] + 0.005)  # (a lens stays in front of its housing)
        if to is None:
            o = slab(self.nm(name), g, self.trim, off, depth, uvr=TRIM[key] if uv_full else None, tex=TEX_TRIM)
            if not uv_full: uv_fill(o, TRIM[key], TEX_TRIM)
            self.body.append(o)
        else:
            o = slab(self.nm(name), g, m, off, depth)
            uv_fill(o, TRIM['white'], TEX_TRIM)
            to.append(o)
        o['off'] = off
        return o

    def glass_on(self, name, rays, off=0.006, depth=0.03, over=None):
        g = cast_grid(self.S, rays)
        off = off + clearance(self.S, rays, g, off)
        if over is not None: off = max(off, over['off'] + 0.005)
        o = slab(self.nm(name), g, self.glass, off, depth)
        uv_box_world(o, 1.4); self.body.append(o); o['off'] = off
        return o

    def on_tint(self, name, rays, off=0.006, depth=0.03):
        g = cast_grid(self.S, rays)
        o = slab(self.nm(name), g, self.tint, off, depth)
        return self.add_tint(o)

    def rod_on(self, name, a, b, d, r, key, off=0.012, seg=5):  # (a rod lying on the body: wipers, aerials)
        ha = self.S.onto(a, d, 0.0); hb = self.S.onto(b, d, 0.0)
        p0 = ha[0] + ha[1] * off; p1 = hb[0] + hb[1] * off
        o = rod(tuple(p0), tuple(p1), r, self.trim, seg=seg, name=self.nm(name))
        return self.add_trim(o, key)

    def wheel(self, node, x, z, r, w, front, style, dual=0.0):
        self.wheels.append(dict(node=node, x=x, y=r, z=z, r=r, w=w, front=front, style=style, dual=dual))

    def wheels4(self, F, B, r, w, x, style, rear_style=None, dual=0.0, rear_w=None):
        self.wheel('wheel_fl', x, F, r, w, True, style)
        self.wheel('wheel_fr', -x, F, r, w, True, style)
        self.wheel('wheel_rl', x, B, r, rear_w or w, False, rear_style or style, dual)
        self.wheel('wheel_rr', -x, B, r, rear_w or w, False, rear_style or style, dual)


def body_half(b, t, H, tu, yw, c, r_low=0.04, r_sh=0.05):
    """one half of a body cross-section (x >= 0): tucked sill, widest at yw, tumblehome to the belt, the shoulder
    roundover, a crowned top"""
    h = t - b
    y2 = b + min(r_low, h * 0.22)
    y3 = clamp(yw, y2 + 0.025, t - 0.035) if h > 0.1 else b + h * 0.55
    top = t + r_sh * 0.55 + c
    return [(H - r_low * 1.25, b), (H - r_low * 0.3, y2), (H, y3), (H - tu, t), (H - tu - r_sh, t + r_sh * 0.55), ((H - tu - r_sh) * 0.55, top - c * 0.3), (0.0, top)]


def house_half(yb, yr, yt, Xb, Xr, edge=0.06):
    """one half of a glass-house section: base (sunk in the body), the side glass up to the rail, the roof edge, the
    crowned roof"""
    yr = max(yr, yb + 0.004); yt = max(yt, yr + 0.012)
    y2 = yr + min(0.03, (yt - yr) * 0.55)
    y3 = y2 + (yt - y2) * 0.72
    return [(Xb, yb), (Xr, yr), (Xr - edge, y2), ((Xr - edge) * 0.52, y3), (0.0, yt)]


def zone(zc, zones, default):
    for a, b, v in zones:
        if a <= zc <= b: return v
    return default


def _area2(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))))


def uv_car(car, o, trim_key='black', override=None):
    """UVs for a mixed part: tint / livery faces into the body map, glass in world metres, trim into one cell. A face
    whose projection would collapse (thin bevels) falls back to its next axis."""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    names = [m.name for m in me.materials]
    P = car.paint
    pts = [b2g(mw @ v.co) for v in me.vertices]
    lo = V3([min(p[i] for p in pts) for i in range(3)]); ext = V3([max(p[i] for p in pts) for i in range(3)]) - lo
    REG = {0: ('L', 'R'), 1: ('T', 'U'), 2: ('F', 'B')}
    for p in me.polygons:
        mn = names[p.material_index] if names else ''
        n = b2g(mw.to_3x3() @ p.normal)
        qs = [pts[me.loops[li].vertex_index] for li in p.loop_indices]
        order = sorted(range(3), key=lambda i: -abs(n[i]))
        forced = (override(n, b2g(mw @ p.center)) if override else None) if mn == car.tint.name else None
        best = None
        for ax in order:
            sg = 1 if n[ax] >= 0 else -1
            if mn == car.tint.name:
                reg = REG[ax][0 if sg > 0 else 1]
                sts = [P.st(reg, q) for q in qs]  # (an override keeps this projection, only lands in its own rect)
                out = [uv_px(P.R[forced or reg], (P.W, P.H), clamp(a, 0, 1), clamp(b, 0, 1)) for a, b in sts]
            elif mn == car.glass.name:
                f = {0: lambda q: (-q.z * sg, q.y), 1: lambda q: (q.x, -q.z * sg), 2: lambda q: (q.x * sg, q.y)}[ax]
                out = [(a / 1.4, b / 1.4) for a, b in map(f, qs)]
            else:
                a_, b_ = [(2, 1), (0, 2), (0, 1)][ax]
                out = [cell_uv(trim_key, (q[a_] - lo[a_]) / (ext[a_] or 1), (q[b_] - lo[b_]) / (ext[b_] or 1)) for q in qs]
            best = best or out
            if _area2(out) > 1e-9: best = out; break
        for li, u in zip(p.loop_indices, best): uv[li].uv = u
    return o


def mirror_rays(rays, s):
    if s > 0: return rays
    return [[(V3((-p.x, p.y, p.z)), V3((-d.x, d.y, d.z))) for p, d in row] for row in rays]


def sided(fn):
    """fn(s) for s = +1 (left, +x) and -1"""
    return [fn(1), fn(-1)]


def lod_stations(z0, z1, axles, extra=()):
    """the far LOD's stations: the ends, a pentagon round each wheel (its arch hugs the tyre), a few more"""
    zs = [z0, z1] + list(extra)
    for az, r in axles: zs += [az - r * 0.995, az - r * 0.45, az + r * 0.45, az + r * 0.995]
    return sorted(z for z in zs if z0 <= z <= z1)


def lod_wheels(car, seg=8):
    out = []
    for w in car.wheels:
        s = 1 if w['x'] > 0 else -1
        prof = [(w['r'], -w['w'] / 2 - w['dual']), (w['r'], w['w'] / 2), (0.0, w['w'] / 2)]
        o = lathe_x(car.nm('lw'), prof, seg, car.trim, band_cells(['rubber', 'wall']), phase=0.5)
        if s < 0: o.data.transform(Matrix.Scale(-1, 4, V3((1, 0, 0)))); o.data.flip_normals()
        o.data.transform(Matrix.Translation(gv(w['x'], w['y'], w['z'])))
        out.append(o)
    return out


# ------------------------------------------------------------ the saloon (and the taxi on it)
def car_body(car, b):
    """the lofted shell + glass house + the far LOD of both, from a spec. Returns the shape functions.
    b: F, B, R (axles, wheel radius), ar (arch radius), zr, zf, sill, bot / belt / hw / crown [(z, v)] curves, tu, yw,
    r_sh, step, extra stations, house: {zb, zw, roof [(z, y)], drop, k, taper, extra, ws, bl, side (z0, z1), pillars
    [(z0, z1)]} (no house: a van-style body with its own glazing)"""
    F, Bk, R, ar = b['F'], b['B'], b['R'], b['ar']
    zr, zf, sill = b['zr'], b['zf'], b['sill']
    arches = b.get('arches') or [(F, R, ar), (Bk, R, ar)]
    bot0 = spline(b['bot'])
    bot = lambda z: arch_floor(z, arches, bot0)
    belt = spline(b['belt'])
    fl = b.get('flare', 0.012)
    flare = lambda z: sum(fl * max(0.0, 1 - ((z - az) / (r * 1.25)) ** 2) for az, _, r in arches)
    hw0 = spline(b['hw'])
    hw = lambda z: hw0(z) + flare(z)
    crown = spline(b['crown'])
    tu, yw, r_sh = b.get('tu', 0.035), b.get('yw', 0.6), b.get('r_sh', 0.05)
    zs = stations(zr, zf, b.get('step', 0.36), arches, extra=b.get('extra', []), arch_n=6, sill=sill)
    half = lambda z: body_half(bot(z), belt(z), hw(z), tu, yw, crown(z), r_sh=r_sh)
    shell = car.add_tint(zloft(car.nm('shell'), zs, half))
    out = dict(bot=bot, bot0=bot0, belt=belt, hw=hw, hw0=hw0, crown=crown, tu=tu, shell=shell, arches=arches, zr=zr, zf=zf)
    h = b.get('house')
    parts = [shell]
    if h:
        Xb = lambda z: hw0(z) - tu - r_sh - 0.012
        yb = lambda z: belt(z) - 0.016
        zw, zb = h['zw'], h['zb']
        rc = h.get('rear_cap')
        roof = spline(([] if rc else [(zb, yb(zb) + 0.012)]) + h['roof'] + [(zw, yb(zw) + 0.012)])
        drop = h.get('drop', 0.068)
        rail = lambda z: roof(z) - drop
        k_t, taper = h.get('k', 0.3), h.get('taper', (0.02, -0.3))
        Xr = lambda z: Xb(z) - k_t * max(0.0, rail(z) - yb(z)) - taper[0] * clamp((taper[1] - z) / 1.0, 0, 1)
        gz = stations(zb, zw, h.get('step', 0.42), extra=h.get('extra', []))
        ws, bl, (s0, s1) = h['ws'], h['bl'], h['side']
        def gmat(i, j, k):
            if i < 0: return 1 if (rc and j < 0) else 0  # (the rear cap: the back window)
            if i >= len(gz) - 1: return 0
            zc = (gz[i] + gz[i + 1]) / 2
            if 2 <= j <= 5: return 1 if (zc > ws or zc < bl) else 0
            if j in (1, 6): return 0
            for a, c in h.get('pillars', []):
                if a < zc < c: return 2
            if zc >= s1 or zc <= s0: return 0
            return 1
        house = zloft(car.nm('house'), gz, lambda z: house_half(yb(z), rail(z), roof(z), Xb(z), Xr(z)), gmat, open_bottom=True, caps=(bool(rc), False))
        set_mats(house, [car.tint, car.glass, car.trim]); car.tint_parts.append(house); car.body.append(house)
        parts.append(house)
        out.update(house=house, roof=roof, rail=rail, Xb=Xb, Xr=Xr, yb=yb, zb=zb, zw=zw)
    car.surf(parts)
    # the far LOD: a pentagon arch round each tyre (it touches), 7-point sections; a 5-point glass house
    lz = lod_stations(zr, zf, [(a, r_) for a, r_, _ in arches], b.get('lod_extra', [zr + 0.12, zf - 0.14, 0.0]))
    tight = [(a, r_, r_ + 0.004) for a, r_, _ in arches]
    def lhalf(z):
        bb, t, H, c = arch_floor(z, tight, bot0), belt(z), hw(z), crown(z)
        return [(H - 0.03, bb), (H - tu, t), (H * 0.62, t + 0.03 + c * 0.7), (0.0, t + 0.0275 + c)]
    lb = zloft(car.nm('l1b'), lz, lhalf, open_bottom=True, caps=(True, True))
    set_mats(lb, [car.tint])
    car.lod1 += [lb]
    if h:
        gz1 = sorted({zb, zw, min(ws, zw), max(bl, zb)} | set(h.get('lod', [])))
        def lmat(i, j, k):
            zc = (gz1[max(i, 0)] + gz1[min(i + 1, len(gz1) - 1)]) / 2
            if j in (0, 3): return 1 if s0 < zc < s1 else 0
            return 1 if (zc > ws or zc < bl) else 0
        def lmat2(i, j, k):
            if i < 0 or i >= len(gz1) - 1: return 1
            return lmat(i, j, k)
        lg = zloft(car.nm('l1g'), gz1, lambda z: [(Xb(z), yb(z)), (Xr(z), roof(z) - 0.03), (0.0, roof(z))], lmat2, open_bottom=True, caps=(bool(rc), False))
        set_mats(lg, [car.tint, car.trim])
        car.lod1 += [lg]
    return out


def sedan(car, taxi=False, base=0xf2f2f2, seam=0x5a5a62):
    F, B, R, ar = 1.42, -1.33, 0.335, 0.40
    zr, zf = -2.35, 2.36
    sill = 0.27
    car.wheels4(F, B, R, 0.22, 0.78, 'cap' if taxi else 'alloy6')
    body = car_body(car, dict(
        F=F, B=B, R=R, ar=ar, zr=zr, zf=zf, sill=sill,
        bot=[(zr, 0.37), (-2.25, 0.31), (-2.05, 0.285), (-1.8, sill), (1.85, sill), (2.1, 0.285), (2.27, 0.31), (zf, 0.35)],
        belt=[(zr, 0.74), (-2.33, 0.81), (-2.27, 0.865), (-2.15, 0.905), (-1.9, 0.925), (-1.35, 0.935), (0.0, 0.928), (1.3, 0.92),
              (1.75, 0.878), (2.1, 0.822), (2.25, 0.765), (2.32, 0.7), (zf, 0.6)],
        hw=[(zr, 0.74), (-2.32, 0.82), (-2.24, 0.875), (-2.05, 0.905), (-1.7, 0.915), (1.8, 0.915), (2.08, 0.9), (2.24, 0.865), (2.32, 0.81), (zf, 0.72)],
        crown=[(zr, 0.004), (-2.22, 0.016), (-1.5, 0.02), (1.4, 0.022), (2.2, 0.016), (zf, 0.004)],
        extra=[zr + 0.025, zr + 0.07, zr + 0.15, zf - 0.025, zf - 0.07, zf - 0.15, -1.33, 1.3],
        house=dict(zb=-1.34, zw=1.30, roof=[(-1.14, 1.15), (-0.9, 1.335), (-0.7, 1.42), (-0.4, 1.452), (0.0, 1.46), (0.3, 1.447), (0.5, 1.405), (0.7, 1.29), (1.0, 1.1)],
                   extra=[-1.25, -1.12, -0.98, -0.86, -0.7, -0.21, -0.11, 0.4, 0.52, 0.66, 0.84, 1.04, 1.16, 1.25],
                   ws=0.47, bl=-0.84, side=(-0.86, 1.16), pillars=[(-0.21, -0.11)], lod=[-1.1, 1.0])))
    shell, house = body['shell'], body['house']
    car.surf([shell, house])
    S = car.S
    cr = lambda cx, cz, phis, ys, s: corner_rays(s * cx, cz, [s * p for p in phis], ys)
    for s in (1, -1):
        # headlights: a gloss black housing swept round the corner, the lens in it
        hh = car.on('hlh', swept(0.34, 1.9, [(0, 0.632, 0.75), (16, 0.636, 0.765), (32, 0.645, 0.78), (46, 0.66, 0.792), (58, 0.68, 0.8), (66, 0.70, 0.802)], 3, s=s), 'black', off=0.003)
        car.on('hl', over=hh, rays=swept(0.34, 1.9, [(2, 0.645, 0.738), (13, 0.649, 0.748), (25, 0.655, 0.762)], 3, s=s), key=None, off=0.009, to=car.lamps, m=car.lamp_m)
        car.on('hl', over=hh, rays=swept(0.34, 1.9, [(30, 0.66, 0.768), (45, 0.674, 0.78), (56, 0.692, 0.788), (63, 0.71, 0.79)], 3, s=s), key=None, off=0.009, to=car.lamps, m=car.lamp_m)
        car.on('ifr', swept(0.34, 1.9, [(50, 0.565, 0.625), (59, 0.585, 0.64), (68, 0.6, 0.65)], 2, s=s), None, off=0.007, to=car.inds, m=car.ind_m)
        car.on('rep', side_rays([1.94, 2.02], [0.755, 0.782], s * 3, -s), None, off=0.007, depth=0.015, to=car.inds, m=car.ind_m)
        # tail lights round the back corners, the indicators under them
        th = car.on('tlh', cr(0.38, -1.85, [181, 168, 155, 142, 129, 117], [0.70, 0.79, 0.885], s), 'black', off=0.003)
        car.on('tl', cr(0.38, -1.85, [179, 168, 155, 142, 129, 120], [0.762, 0.815, 0.872], s), None, off=0.009, to=car.tails, m=car.tail_m, over=th)
        car.on('ird', cr(0.38, -1.85, [179, 168, 155, 142, 129, 120], [0.712, 0.752], s), None, off=0.007, to=car.inds, m=car.ind_m, over=th)
        # black sills between the arches, the chrome strip along the window line
        car.on('sill', side_rays([F - 0.43, 0.4, -0.4, B + 0.43], [0.285, 0.34], s * 3, -s), 'plastic', off=0.006, depth=0.03)
        car.on('blt', side_rays([1.2, 0.5, -0.2, -0.9, -1.3], [0.915, 0.928], s * 3, -s), 'chrome', off=0.004, depth=0.02)
        # door handles, the mirror on its arm
        for zh in (0.12, -0.98):
            car.on('dh', side_rays([zh + 0.075, zh - 0.075], [0.842, 0.872], s * 3, -s), 'chrome', off=0.01, depth=0.022)
        p, n = S.onto((s * 3, 0.955, 1.12), (-s, 0, 0), 0.0)
        arm = box((0.12, 0.045, 0.07), (p.x + s * 0.03, 0.975, 1.12), None, name=car.nm('marm'))
        car.add_tint(arm)
        hs = box((0.17, 0.115, 0.095), (p.x + s * 0.12, 1.02, 1.12), None, bev=0.03, seg=1, rot=(0, s * 0.12, 0), name=car.nm('mir'))
        car.add_tint(hs)
        car.add_glass(box((0.13, 0.08, 0.012), (p.x + s * 0.125, 1.02, 1.072), None, rot=(0, s * 0.12, 0), name=car.nm('mgl')))
    # grille, the chrome bar on it, the intake, plates
    gr = car.on('gr', front_rays([-0.33, -0.11, 0.11, 0.33], [0.61, 0.665, 0.718], 4), 'grille', off=0.003, uv_full=True)
    car.on('grc', front_rays([-0.35, -0.12, 0.12, 0.35], [0.722, 0.74], 4), 'chrome', off=0.006)
    car.on('in', front_rays([-0.56, -0.19, 0.19, 0.56], [0.334, 0.374, 0.415], 4), 'grille', off=0.003, uv_full=True)
    car.on('lip', front_rays([-0.86, -0.45, 0.0, 0.45, 0.86], [0.298, 0.327], 4), 'plastic', off=0.005)
    car.on('pf', front_rays([-0.25, 0.25], [0.432, 0.538], 4), 'plate', off=0.008, depth=0.02, uv_full=True)
    car.on('pr', front_rays([0.25, -0.25], [0.6, 0.706], -4, 1), 'plate', off=0.008, depth=0.02, uv_full=True)
    car.on('dif', front_rays([0.72, 0.3, -0.3, -0.72], [0.325, 0.395], -4, 1), 'plastic', off=0.006)
    car.on('stk', front_rays([0.66, 0.24], [0.44, 0.5], -4, 1), 'sticker', off=0.005, depth=0.015, uv_full=True)
    car.on('bk', [[(V3((x, y, -4.0)), V3((0, 0, 1))) for x in (0.22, 0.0, -0.22)] for y in (1.372, 1.392)], None, off=0.004, depth=0.02, to=car.tails, m=car.tail_m)  # the brake light, top of the back window
    car.add_trim(cyl(0.034, 0.16, (-0.48, 0.31, -2.29), None, axis='z', seg=8, name=car.nm('exh')), 'chrome')
    # wipers parked on the scuttle, the whip aerial on the back wing
    car.rod_on('wp', (0.04, 3, 1.235), (0.62, 3, 1.17), (0, -1, 0), 0.011, 'black')
    car.rod_on('wp', (-0.58, 3, 1.235), (-0.06, 3, 1.215), (0, -1, 0), 0.011, 'black')
    p, n = S.onto((-0.74, 3, -1.95), (0, -1, 0), 0.0)
    car.add_trim(rod(tuple(p - n * 0.01), tuple(p + V3((-0.02, 0.62, -0.09))), 0.006, None, seg=4, name=car.nm('ant')), 'black')
    car.add_trim(cyl(0.012, 0.03, tuple(p + V3((-0.02, 0.62, -0.09))), None, axis='y', seg=6, name=car.nm('antb')), 'black')
    for az in (F, B):  # wheel tubs: the dark inside of the arches
        car.add_trim(box((2 * (0.78 - 0.11 - 0.035), 0.5, 0.5), (0, 0.41, az), None, name=car.nm('tub')), 'dark')
    # the body map: seams, shut lines, the fuel flap
    P = car.paint
    for reg in ('L', 'R'): P.fill(reg, base, seed=3 if reg == 'L' else 4)
    for reg in ('T', 'F', 'B', 'X'): P.fill(reg, base, seed=5)
    P.fill('U', 0x3a3a3f, seed=6)
    P.line('LR', [(0, 0.3, 1.02), (0, 0.6, 1.03), (0, 0.925, 1.08)], seam)
    P.line('LR', [(0, 0.29, -0.16), (0, 0.93, -0.16)], seam)
    P.line('LR', [(0, 0.93, -1.1), (0, 0.79, -1.08), (0, 0.68, -0.99), (0, 0.56, -0.9), (0, 0.29, -0.88)], seam)
    P.line('LR', [(0, 0.292, 1.02), (0, 0.292, -0.88)], seam)
    P.line('LR', [(0, 0.93, -0.16), (0, 0.935, -1.1)], seam)
    P.line('T', [(-0.8, 0, 1.33), (0.8, 0, 1.33)], seam); P.line('T', [(0.8, 0, 1.33), (0.8, 0, 2.27)], seam); P.line('T', [(-0.8, 0, 1.33), (-0.8, 0, 2.27)], seam)
    P.line('T', [(-0.78, 0, -1.37), (0.78, 0, -1.37)], seam); P.line('T', [(0.78, 0, -1.37), (0.78, 0, -2.3)], seam); P.line('T', [(-0.78, 0, -1.37), (-0.78, 0, -2.3)], seam)
    P.line('B', [(0.76, 0.58, 0), (-0.76, 0.58, 0)], seam)
    P.rect('L', (0, 0.785, -1.93), (0, 0.895, -1.81), seam); P.rect('L', (0, 0.795, -1.92), (0, 0.885, -1.82), base)
    P.line('LR', [(0, 0.775, -2.2), (0, 0.79, 2.1)], 0xd4d4d8, 1.0)  # the shoulder crease (a shadow line)
    car.meta.update(id='taxi' if taxi else 'sedan', lamps=[[0.58, 0.72, 2.36], [-0.58, 0.72, 2.36]], wb=round(F - B, 3))
    car.cabin = dict(belt=0.93, top=1.39, rows=[(0.02, 1.30, 0.36), (-0.68, 1.27, 0.4)], dash=1.0, wheel=(-0.36, 1.08, 0.18, 0.09), shelf=(0.9, 0.99))  # (right-hand drive: they keep left)
    return body


# ------------------------------------------------------------ atlas painters (plates, stickers, signs)
def atlas(plate='JNK 420', sticker=('HONK IF U R', 'JANK'), sticker_bg=0x7dff4f, sticker_fg=(0x101010, 0xff1aa0), extra=None):
    def f(px, cell):
        c = cell('plate'); c[:] = hexrgb(0xf4f1e4)
        c[0, :] = c[-1, :] = hexrgb(0x2a2a40); c[:, 0] = c[:, -1] = hexrgb(0x2a2a40)
        w = len(plate) * 6 - 1
        text_px(c, plate, (48 - w) // 2, 5, 1, 0x1a1a3a)
        st = cell('sticker'); st[:] = hexrgb(sticker_bg)
        for i, line in enumerate(sticker):
            w = len(line) * 6 - 1
            text_px(st, line, (64 - w) // 2, 1 + i * 8 if len(sticker) > 1 else 5, 1, sticker_fg[min(i, len(sticker_fg) - 1)])
        if extra: extra(px, cell)
    return f


# ------------------------------------------------------------ finishing: maps, joins, AO, QA, hierarchy
def write_paint(car):
    P = car.paint
    if isinstance(arg('dump'), str):
        os.makedirs(arg('dump'), exist_ok=True)
        im = bpy.data.images.new('dump_' + car.id, P.W, P.H, alpha=False)
        a = np.ones((P.H, P.W, 4), np.float32); a[:, :, :3] = np.clip(P.px, 0, 1)[::-1]
        im.pixels.foreach_set(a.ravel()); im.filepath_raw = os.path.join(arg('dump'), car.id + '_paint.png'); im.file_format = 'PNG'; im.save()
    a = np.ones((P.H, P.W, 4), np.float32); a[:, :, :3] = np.clip(P.px, 0, 1)[::-1]
    car.pimg.pixels.foreach_set(a.ravel()); car.pimg.file_format = 'PNG'; car.pimg.pack()


def weld(o, dist=1e-5):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bm.to_mesh(o.data); bm.free()
    return o


def qa(tag, objs, eps=0.0008, tol=0.003):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=eps, tol=tol)
    print('QA_PASS', tag, res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], tag, e)
    return res


def finish_car(car, fid, size):
    write_paint(car)
    for P_, img in getattr(car, 'extra_paints', []):
        a = np.ones((P_.H, P_.W, 4), np.float32); a[:, :, :3] = np.clip(P_.px, 0, 1)[::-1]
        img.pixels.foreach_set(a.ravel()); img.file_format = 'PNG'; img.pack()
    for o in car.body + car.lamps + car.tails + car.inds + car.lod1: apply_mods(o)
    if arg('parts'):
        dg = bpy.context.evaluated_depsgraph_get(); tally = {}
        for o in car.body + car.lamps + car.tails + car.inds:
            me = o.data; me.calc_loop_triangles(); k = o.name.split('_')[1]; tally[k] = tally.get(k, 0) + len(me.loop_triangles)
        print('JF_PARTS', sorted(tally.items(), key=lambda kv: -kv[1]))
    for o in car.tint_parts: uv_car(car, o, 'black', override=(lambda n, c, r=o['reg']: r) if 'reg' in o else None)
    glass_paint(car)  # (after uv_car: the glass faces take their own map)
    shell = join(car.body, 'shell')
    lamps = join(car.lamps, 'lamps'); tails = join(car.tails, 'tails'); inds = join(car.inds, 'inds')
    for o in (shell, lamps, tails, inds): weld(o, 1e-6); smooth(o, 40)
    wheels = []
    for w in car.wheels:
        o = wheel_mesh(w['node'], w['r'], w['w'], w['style'], car.trim, dual=w['dual'], side=1 if w['x'] > 0 else -1)
        o.location = gv(w['x'], w['y'], w['z'])
        wheels.append(o)
    if arg('parts'):
        for o in wheels: o.data.calc_loop_triangles(); print('JF_WHEEL', o.name, len(o.data.loop_triangles))
    lw_ = lod_wheels(car)
    if getattr(car, 'lod_cola', None):
        cm, BP_ = car.lod_cola
        for o in lw_: set_mats(o, [cm]); uv_fill(o, BP_.R['U'], (BP_.W, BP_.H))
        for o in car.lod1:
            if o.data.materials and len(o.data.materials) > 1 and o.data.materials[1] == cm:  # the cab's far glass
                uv_car(car, o, 'glass')
                me = o.data; uv = me.uv_layers.active.data
                for p in me.polygons:
                    if p.material_index == 1:
                        for k_, li in enumerate(p.loop_indices):
                            a_ = 2 * math.pi * k_ / len(p.loop_indices); uv[li].uv = uv_px(BP_.R['X'], (BP_.W, BP_.H), 0.5 + 0.3 * math.cos(a_), 0.5 + 0.3 * math.sin(a_))
    car.lod1 += lw_
    for o in car.lod1:
        if o.data.materials and o.data.materials[0].name == car.tint.name and not o.data.uv_layers: uv_car(car, o, 'glass')
    l1 = join(car.lod1, 'lod1_mesh'); weld(l1, 1e-6); smooth(l1, 40)
    bpy.context.view_layer.update()
    if not arg('no-ao'):
        bake_ao([shell, lamps, tails, inds] + wheels, dist=0.6)
        for w in wheels: bake_ao([w], dist=0.2, floor=False, lo=0.55)
        bake_ao([l1], dist=0.6)
    for o in (lamps, tails, inds): flat_ao(o)
    res = {}
    if arg('qa'):
        res['body'] = qa(car.id + ':body', [shell, lamps, tails, inds])
        for w in wheels: res[w.name] = qa(car.id + ':' + w.name, [w])
        res['lod1'] = qa(car.id + ':lod1', [l1], tol=0.01)
    body = _link(bpy.data.objects.new('body', None))
    for o in (shell, lamps, tails, inds): o.parent = body
    meta = dict(car.meta)
    meta.update(kind='car', lod=60, tint=car.livery is None, size=list(size),
                wheels=[dict(node=w['node'], x=round(w['x'], 4), y=round(w['y'], 4), z=round(w['z'], 4), r=w['r'], w=w['w'], front=w['front'], **({'dual': True} if w['dual'] else {})) for w in car.wheels])
    if car.livery: meta['livery'] = car.livery
    meta['lamps'] = [[round(v, 3) for v in q] for q in meta['lamps']]
    print('JF_META', json.dumps(meta))
    root = prop_finish(fid, [body] + wheels, [l1], meta)
    t0, t1 = prop_stats(root)
    mats0 = sorted({m.name for o in [shell, lamps, tails, inds] + wheels for m in o.data.materials})
    mats1 = sorted({m.name for m in l1.data.materials})
    print(f'JF_CAR {fid}: lod0 {t0} tris, lod1 {t1} tris, body mats {[m.name for m in shell.data.materials]}, all {mats0}, lod1 {mats1}')
    car.out = dict(root=root, shell=shell, lamps=lamps, tails=tails, inds=inds, wheels=wheels, l1=l1, t0=t0, t1=t1, qa=res)
    return root


def tint_for_render(m, hexcol):
    """the sheet shows a tinted car: multiply the paint texture by a colour (after the export)"""
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tex = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs['Fac'].default_value = 1.0
    mix.inputs['Color2'].default_value = srgb(hexcol)
    nt.links.new(tex.outputs['Color'], mix.inputs['Color1']); nt.links.new(mix.outputs['Color'], b.inputs['Base Color'])


def clear_studio():
    for o in list(bpy.data.objects):
        if o.type in ('LIGHT', 'CAMERA'): bpy.data.objects.remove(o, do_unlink=True)


def sheets(car, fid, colour):
    o = car.out
    if colour is not None: tint_for_render(car.tint, colour)
    note = f'LOD0 {o["t0"]} LOD1 {o["t1"]}'
    for c in o['l1'].parent.children_recursive if o['l1'].parent else [o['l1']]: c.hide_render = True
    o['l1'].hide_render = True
    sheet(o['root'], fid, extra_note=note)
    clear_studio()
    for x in [o['shell'], o['lamps'], o['tails'], o['inds']] + o['wheels']: x.hide_render = True
    o['l1'].hide_render = False
    sheet(o['root'], fid + '_lod1', views=('persp', 'left', 'back_persp'), res=(480, 300), extra_note='FAR')
    clear_studio()
    for x in [o['shell'], o['lamps'], o['tails'], o['inds']] + o['wheels']: x.hide_render = False


def preview(car, fid, outdir, colour):
    """quick look while iterating: 4 views, fewer samples"""
    o = car.out
    if colour is not None and not any(n.type == 'MIX_RGB' for n in car.tint.node_tree.nodes): tint_for_render(car.tint, colour)
    o['l1'].hide_render = True
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'; sc.eevee.taa_render_samples = 12
    sc.render.resolution_x, sc.render.resolution_y = (int(x) for x in arg('res', '640x400').split('x'))
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = float(arg('exposure', '-0.35'))
    w = bpy.data.worlds.new('pw'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(0x3a3346); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
    tris, lo, hi = stats(o['root'])
    c = (gv(*lo) + gv(*hi)) / 2; size = (gv(*hi) - gv(*lo)).length
    def light(energy, loc, sz, col=(1, 1, 1)):
        L = bpy.data.lights.new('pl', 'AREA'); L.energy = energy * size * size; L.color = col; L.size = sz * size
        ob = _link(bpy.data.objects.new('pl', L)); ob.location = c + V3(loc) * size; lib._look_at(ob, c)
    light(200, (1.2, -1.4, 1.6), 1.2); light(70, (-1.6, -0.6, 0.6), 1.5, (0.85, 0.9, 1.0)); light(150, (-0.4, 1.8, 1.2), 0.6, (1.0, 0.8, 0.95)); light(40, (0.2, 0.2, -1.6), 1.5)
    cam = _link(bpy.data.objects.new('pc', bpy.data.cameras.new('pc'))); sc.camera = cam
    shots = []
    views = arg('views', 'fl,rr,side,front')
    for k, v in enumerate(views.split(',')):
        cd = cam.data; cd.type = 'PERSP'; cd.lens = 50; cd.clip_start = 0.05; cd.clip_end = 200
        dirs = {'fl': (1.0, -1.25, 0.45), 'rr': (-1.0, 1.25, 0.5), 'side': (1, 0, 0.08), 'front': (0.0, -1, 0.12), 'back': (0, 1, 0.15), 'top': (0.3, -0.4, 1.6),
                'low': (1.0, -0.9, 0.05), 'wheel': (1.0, -0.35, 0.05), 'rside': (-1, 0, 0.08), 'fr': (-1.0, -1.25, 0.45), 'rl': (1.0, 1.25, 0.5)}
        d = V3(dirs.get(v, (1, -1, 0.5))).normalized()
        if v in ('side', 'rside', 'front', 'back'):
            cd.type = 'ORTHO'; cd.ortho_scale = size * (0.95 if v in ('side', 'rside') else 0.55)
            cam.location = c + d * size * 3
        elif v == 'wheel':
            cd.lens = 70; cam.location = c + d * size * 0.9
        elif v in ('nose', 'tail', 'nose2', 'tail2'):
            o_ = o['root']; zf_ = max(b2g(x.matrix_world @ V3(cb)).z for x in o_.children_recursive if x.type == 'MESH' and x.name != 'lod1_mesh' for cb in x.bound_box)
            zr_ = min(b2g(x.matrix_world @ V3(cb)).z for x in o_.children_recursive if x.type == 'MESH' and x.name != 'lod1_mesh' for cb in x.bound_box)
            tgt = gv(0, 0.65 * (hi[1] - lo[1]) * 0.6, zf_ - 0.6) if v.startswith('nose') else gv(0, 0.65 * (hi[1] - lo[1]) * 0.6, zr_ + 0.6)
            dd = {'nose': (0.55, -1.0, 0.25), 'nose2': (-0.1, -1.0, 0.12), 'tail': (-0.55, 1.0, 0.3), 'tail2': (0.1, 1.0, 0.12)}[v]
            cd.lens = 50; cam.location = tgt + V3(dd).normalized() * max(3.2, (hi[0] - lo[0]) * 1.6); lib._look_at(cam, tgt)
            p = os.path.join(outdir, f'{fid}_{v}.png'); sc.render.filepath = p
            bpy.ops.render.render(write_still=True); shots.append(p)
            continue
        else:
            cam.location = c + d * size * 1.6
        lib._look_at(cam, c)
        p = os.path.join(outdir, f'{fid}_{v}.png'); sc.render.filepath = p
        bpy.ops.render.render(write_still=True); shots.append(p)
    clear_studio()
    print('JF_PREVIEW', ' '.join(shots))


# ------------------------------------------------------------ the cars
def build_sedan():
    car = Car('sedan', (-2.37, 2.39, 1.5, 0.95), atlas=atlas('JNK 420'))
    sedan(car)
    return car, 'p_car_sedan', (1.84, 1.46, 4.7), 0xe8323c


def build_taxi():
    def sign_px(px, cell):
        pass
    car = Car('taxi', (-2.37, 2.39, 1.8, 0.95), livery='livery', side_h=80, atlas=atlas('FARE 4U', ('CASH ONLY', 'NO REFUNDS'), 0xffffff, (0x101010, 0xe8323c)))
    yel, ink = 0xffd21a, 0x141414
    sedan(car, taxi=True, base=yel, seam=0x7a5e10)
    P = car.paint
    # the checker band on both sides, in whole pixels so the squares stay square
    for reg in ('L', 'R'):
        x0, y0 = P.pix(reg, (0, 0.735, 1.0 if reg == 'L' else -1.12))
        x1, y1 = P.pix(reg, (0, 0.6, -1.12 if reg == 'L' else 1.0))
        xa, xb = int(round(min(x0, x1))), int(round(max(x0, x1))); ya, yb = int(round(min(y0, y1))), int(round(max(y0, y1)))
        hh = max(2, (yb - ya) // 2)
        for yy in range(ya, ya + 2 * hh):
            for xx in range(xa, xb):
                if (((xx - xa) // 6) + ((yy - ya) // hh)) % 2 == 0: P.px[yy, xx] = hexrgb(ink)
        P.text(reg, (0, 0.82, 0.45), 'JANK CABS', 1, ink)
    P.fill('X', 0xfff6c8, var=0.01, seed=9)
    X = P.R['X']
    for k, s in enumerate(('TAXI?', 'TAXI?')):
        x, y, w, h = X[0], X[1] + k * 24, X[2], 24
        P.px[y:y + h, x:x + w] = hexrgb(0xfff6c8)
        P.px[y:y + 2, x:x + w] = hexrgb(yel); P.px[y + h - 2:y + h, x:x + w] = hexrgb(yel)
        text_px(P.px, s, x + (w - 58) // 2, y + 5, 2, 0x1a1a1a)
    # the roof light: a black foot, the trapezoid sign (TAXI? both ways)
    S = car.S
    yr = min(S.onto((x, 3, z), (0, -1, 0), 0.0)[0].y for x in (-0.3, 0.3) for z in (-0.25, 0.05))
    foot = box((0.52, 0.035, 0.24), (0, yr + 0.012, -0.1), None, name=car.nm('signfoot'))
    car.add_trim(foot, 'black')
    sg = side([(-0.155, 0.0), (0.155, 0.0), (0.105, 0.225), (-0.105, 0.225)], 0.66, (0, yr + 0.026, -0.1), None, bev=0.018, seg=1, name=car.nm('sign'))
    apply_mods(sg); set_mats(sg, [car.tint]); car.body.append(sg)
    me = sg.data; me.uv_layers.new(name='UVMap'); uv = me.uv_layers.active.data
    y0s, y1s = yr + 0.026, yr + 0.251
    mw = sg.matrix_world
    for p in me.polygons:
        n = b2g(mw.to_3x3() @ p.normal)
        for li in p.loop_indices:
            q = b2g(mw @ me.vertices[me.loops[li].vertex_index].co)
            t = clamp((q.y - y0s) / (y1s - y0s), 0, 1)
            if n.z > 0.35: r = (X[0], X[1], X[2], 24); s_ = (q.x + 0.33) / 0.66
            elif n.z < -0.35: r = (X[0], X[1] + 24, X[2], 24); s_ = (0.33 - q.x) / 0.66
            else:  # top, ends, bevels: plain cream, box-mapped
                r = (X[0], X[1] + 50, X[2], 12)
                ax, _ = face_axis(n)
                s_, t = [((q.z + 0.1 + 0.2) / 0.4, t), ((q.x + 0.33) / 0.66, (q.z + 0.1 + 0.2) / 0.4), ((q.x + 0.33) / 0.66, t)][ax]
            uv[li].uv = uv_px(r, (P.W, P.H), clamp(s_, 0, 1), clamp(t, 0, 1), m=0.8)
    car.meta['sign'] = True
    return car, 'p_car_taxi', (1.84, 1.78, 4.7), None


# ------------------------------------------------------------ the supermini
def hatch(car, base=0xf2f2f2, seam=0x5a5a62):
    F, B, R, ar = 1.2, -1.3, 0.31, 0.37
    zr, zf, sill = -1.97, 1.98, 0.28
    car.wheels4(F, B, R, 0.2, 0.75, 'alloy')
    body = car_body(car, dict(
        F=F, B=B, R=R, ar=ar, zr=zr, zf=zf, sill=sill, yw=0.6,
        bot=[(zr, 0.37), (-1.88, 0.31), (-1.72, 0.29), (-1.62, sill), (1.52, sill), (1.78, 0.29), (1.92, 0.32), (zf, 0.37)],
        belt=[(zr, 0.91), (-1.94, 0.965), (-1.86, 0.985), (-1.5, 0.99), (-0.5, 0.963), (0.6, 0.942), (1.04, 0.93), (1.45, 0.893), (1.75, 0.842), (1.88, 0.775), (1.94, 0.7), (zf, 0.61)],
        hw=[(zr, 0.66), (-1.94, 0.765), (-1.86, 0.83), (-1.65, 0.862), (-1.3, 0.866), (1.2, 0.866), (1.55, 0.856), (1.78, 0.82), (1.9, 0.765), (zf, 0.67)],
        crown=[(zr, 0.004), (-1.85, 0.01), (-1.0, 0.012), (1.05, 0.02), (1.85, 0.014), (zf, 0.004)],
        extra=[zr + 0.025, zr + 0.07, zr + 0.13, zf - 0.025, zf - 0.07, zf - 0.14, 1.04],
        house=dict(zb=-1.935, zw=1.04, roof=[(-1.885, 1.06), (-1.8, 1.215), (-1.7, 1.345), (-1.58, 1.42), (-1.35, 1.452), (-0.6, 1.482), (0.0, 1.49), (0.22, 1.475), (0.42, 1.405), (0.62, 1.255), (0.85, 1.07)],
                   extra=[-1.9, -1.84, -1.76, -1.66, -1.56, -1.3, -1.1, -0.55, -0.45, 0.12, 0.3, 0.45, 0.6, 0.76, 0.9, 0.99], taper=(0.035, -0.4),
                   ws=0.27, bl=-1.6, side=(-1.3, 0.95), pillars=[(-0.55, -0.45)], lod=[-1.75, 0.7])))
    S = car.S
    cr = lambda cx, cz, phis, ys, s: corner_rays(s * cx, cz, [s * p for p in phis], ys)
    for s in (1, -1):
        hh = car.on('hlh', swept(0.3, 1.45, [(0, 0.61, 0.72), (14, 0.615, 0.745), (28, 0.625, 0.77), (40, 0.64, 0.79), (51, 0.665, 0.8), (60, 0.69, 0.805)], 3, s=s), 'black', off=0.003)
        car.on('hl', swept(0.3, 1.45, [(2, 0.624, 0.708), (12, 0.627, 0.727), (23, 0.634, 0.746)], 3, s=s), None, off=0.009, to=car.lamps, m=car.lamp_m, over=hh)
        car.on('hl', swept(0.3, 1.45, [(28, 0.64, 0.756), (40, 0.653, 0.776), (50, 0.675, 0.788), (58, 0.698, 0.792)], 3, s=s), None, off=0.009, to=car.lamps, m=car.lamp_m, over=hh)
        car.on('ifr', swept(0.3, 1.45, [(52, 0.555, 0.605), (60, 0.575, 0.625), (68, 0.595, 0.64)], 2, s=s), None, off=0.007, to=car.inds, m=car.ind_m)
        car.on('rep', side_rays([1.56, 1.63], [0.775, 0.8], s * 3, -s), None, off=0.007, depth=0.015, to=car.inds, m=car.ind_m)
        # tall tail lights up the back corners (into the pillars), the indicator in their foot
        th = car.on('tlh', cr(0.5, -1.62, [178, 165, 152, 139, 127], [0.665, 0.8, 0.94, 1.02], s), 'black', off=0.003)
        car.on('tl', cr(0.5, -1.62, [176, 165, 152, 139, 129], [0.735, 0.8, 0.94, 1.005], s), None, off=0.009, to=car.tails, m=car.tail_m, over=th)
        car.on('ird', cr(0.5, -1.62, [176, 165, 152, 139, 129], [0.678, 0.722], s), None, off=0.007, to=car.inds, m=car.ind_m, over=th)
        car.on('sill', side_rays([F - 0.41, 0.3, -0.5, B + 0.41], [0.295, 0.35], s * 3, -s), 'plastic', off=0.006, depth=0.03)
        for zh in (-0.06, -1.06):
            car.on('dh', side_rays([zh + 0.07, zh - 0.07], [0.858, 0.886], s * 3, -s), 'black', off=0.01, depth=0.022)
        p, n = S.onto((s * 3, 0.965, 0.92), (-s, 0, 0), 0.0)
        car.add_tint(box((0.11, 0.045, 0.065), (p.x + s * 0.025, 0.985, 0.92), None, name=car.nm('marm')))
        car.add_trim(box((0.16, 0.11, 0.09), (p.x + s * 0.11, 1.03, 0.92), None, bev=0.028, seg=1, rot=(0, s * 0.12, 0), name=car.nm('mir')), 'black')
        car.add_glass(box((0.12, 0.075, 0.012), (p.x + s * 0.115, 1.03, 0.874), None, rot=(0, s * 0.12, 0), name=car.nm('mgl')))
    # face: the slot over the plate, the big trapezoid mouth, the plate, a black lip
    car.on('gr', front_rays([-0.28, 0.0, 0.28], [0.665, 0.712], 4), 'grille', off=0.003, uv_full=True)
    car.on('in', [[(V3((x * k, y, 4.0)), V3((0, 0, -1))) for x in (-0.5, -0.17, 0.17, 0.5)] for y, k in ((0.335, 0.86), (0.4, 0.93), (0.462, 1.0))], 'grille', off=0.003, uv_full=True)
    car.on('pf', front_rays([-0.23, 0.23], [0.49, 0.59], 4), 'plate', off=0.008, depth=0.02, uv_full=True)
    car.on('lip', front_rays([-0.8, -0.4, 0.0, 0.4, 0.8], [0.3, 0.328], 4), 'plastic', off=0.005)
    # back: plate on the tailgate, a black diffuser, the sticker, the spoiler with the brake light, the rear wiper
    car.on('pr', front_rays([0.22, -0.22], [0.6, 0.7], -4, 1), 'plate', off=0.008, depth=0.02, uv_full=True)
    car.on('dif', front_rays([0.66, 0.25, -0.25, 0.66 * -1], [0.31, 0.44], -4, 1), 'plastic', off=0.005)
    car.on('stk', front_rays([0.56, 0.28], [0.75, 0.81], -4, 1), 'sticker', off=0.005, depth=0.015, uv_full=True)
    ry = body['roof'](-1.62)
    sp = side([(-1.47, ry - 0.03), (-1.66, ry - 0.025), (-1.79, ry - 0.075), (-1.74, ry - 0.105), (-1.62, ry - 0.07), (-1.47, ry - 0.07)], 1.26, (0, 0, 0), None, bev=0.012, seg=1, name=car.nm('spoiler'))
    car.add_tint(sp)
    car.surf([body['shell'], body['house'], sp])
    car.on('bk', [[(V3((x, y, -4.0)), V3((0, 0, 1))) for x in (0.2, 0.0, -0.2)] for y in (ry - 0.098, ry - 0.08)], None, off=0.003, depth=0.02, to=car.tails, m=car.tail_m)
    car.rod_on('rwp', (0.0, 1.07, -4), (0.33, 1.24, -4), (0, 0, 1), 0.01, 'black', off=0.012)
    car.add_trim(cyl(0.03, 0.14, (-0.42, 0.31, -1.92), None, axis='z', seg=8, name=car.nm('exh')), 'metal')
    car.rod_on('wp', (0.02, 3, 0.99), (0.56, 3, 0.93), (0, -1, 0), 0.01, 'black')
    car.rod_on('wp', (-0.54, 3, 0.99), (-0.04, 3, 0.975), (0, -1, 0), 0.01, 'black')
    p, n = S.onto((0.0, 3, -1.42), (0, -1, 0), 0.0)
    car.add_trim(rod(tuple(p - n * 0.01), tuple(p + V3((0, 0.2, -0.17))), 0.007, None, seg=4, name=car.nm('ant')), 'black')  # the bee-sting aerial
    for az in (F, B):
        car.add_trim(box((2 * (0.75 - 0.1 - 0.035), 0.46, 0.46), (0, 0.39, az), None, name=car.nm('tub')), 'dark')
    P = car.paint
    for reg in ('L', 'R'): P.fill(reg, base, seed=13 if reg == 'L' else 14)
    for reg in ('T', 'F', 'B', 'X'): P.fill(reg, base, seed=15)
    P.fill('U', 0x3a3a3f, seed=16)
    P.line('LR', [(0, 0.3, 0.92), (0, 0.6, 0.94), (0, 0.935, 0.99)], seam)
    P.line('LR', [(0, 0.3, -0.5), (0, 0.95, -0.5)], seam)
    P.line('LR', [(0, 0.965, -1.3), (0, 0.8, -1.3), (0, 0.7, -1.14), (0, 0.58, -0.99), (0, 0.3, -0.93)], seam)
    P.line('LR', [(0, 0.302, 0.92), (0, 0.302, -0.93)], seam)
    P.line('LR', [(0, 0.79, -1.85), (0, 0.8, 1.8)], 0xd4d4d8, 1.0)
    P.line('T', [(-0.74, 0, 1.06), (0.74, 0, 1.06)], seam); P.line('T', [(0.74, 0, 1.06), (0.7, 0, 1.9)], seam); P.line('T', [(-0.74, 0, 1.06), (-0.7, 0, 1.9)], seam)
    P.line('B', [(0.6, 0.5, 0), (-0.6, 0.5, 0)], seam); P.line('B', [(0.6, 0.5, 0), (0.62, 0.95, 0)], seam); P.line('B', [(-0.6, 0.5, 0), (-0.62, 0.95, 0)], seam)
    P.rect('L', (0, 0.8, -1.62), (0, 0.9, -1.52), seam); P.rect('L', (0, 0.81, -1.61), (0, 0.89, -1.53), base)
    car.meta.update(id='hatch', lamps=[[0.56, 0.7, 1.97], [-0.56, 0.7, 1.97]], wb=round(F - B, 3))
    car.cabin = dict(belt=0.96, top=1.43, rows=[(-0.28, 1.34, 0.34), (-1.12, 1.31, 0.38)], dash=1.04, wheel=(-0.34, 1.11, 0.17, 0.085), shelf=(0.98, 1.06))
    return body


def build_hatch():
    car = Car('hatch', (-1.99, 2.0, 1.55, 0.9), atlas=atlas('LIL JNK', ('0 TO 60:', 'EVENTUALLY'), 0xffe14d, (0x101010, 0xe8323c)))
    hatch(car)
    return car, 'p_car_hatch', (1.76, 1.5, 3.95), 0x2f6fe0


# ------------------------------------------------------------ the full-size pickup
def arch_rays(az, hub, r0, r1, s, n=7, a0=17, a1=163, x=3.0):
    """rays from the side onto a band round a wheel arch (radii r0..r1 round the hub): flares"""
    rows = []
    for rr in (r0, r1):
        row = []
        for k in range(n):
            a = math.radians(a0 + (a1 - a0) * k / (n - 1))
            row.append((V3((s * x, hub + math.sin(a) * rr, az + math.cos(a) * rr)), V3((-s, 0, 0))))
        rows.append(row)
    return rows


def pickup(car, base=0xf2f2f2, seam=0x5a5a62):
    F, B, R, ar = 1.78, -1.55, 0.39, 0.46
    zr, zf, sill = -0.58, 2.71, 0.46
    HW = 0.985
    car.wheels4(F, B, R, 0.28, 0.84, 'chrome6')
    body = car_body(car, dict(
        F=F, B=B, R=R, ar=ar, zr=zr, zf=zf, sill=sill, arches=[(F, R, ar)], tu=0.025, yw=0.85, r_sh=0.06, flare=0.0,
        bot=[(zr, sill), (1.2, sill), (2.35, 0.5), (2.6, 0.58), (zf, 0.62)],
        belt=[(zr, 1.095), (-0.4, 1.105), (0.6, 1.12), (1.12, 1.13), (1.9, 1.12), (2.45, 1.105), (2.6, 1.09), (2.67, 1.06), (zf, 1.01)],
        hw=[(zr, 0.975), (-0.45, HW), (2.35, HW), (2.58, 0.975), (2.67, 0.955), (zf, 0.925)],
        crown=[(zr, 0.01), (0.0, 0.015), (1.2, 0.02), (2.5, 0.015), (zf, 0.006)],
        extra=[zr + 0.02, zr + 0.06, zf - 0.02, zf - 0.06, zf - 0.13, 1.12], lod_extra=[zf - 0.1],
        house=dict(rear_cap=True, zb=zr + 0.012, zw=1.12, roof=[(zr + 0.012, 1.85), (-0.49, 1.885), (0.0, 1.9), (0.45, 1.885), (0.62, 1.8), (0.86, 1.52)],
                   drop=0.07, k=0.22, taper=(0.0, 0.0), extra=[-0.52, -0.46, -0.42, -0.2, 0.15, 0.25, 0.52, 0.6, 0.7, 0.82, 0.94, 1.04],
                   ws=0.6, bl=-10, side=(-0.42, 1.0), pillars=[(0.15, 0.25)], lod=[0.3])))
    S = car.S
    # the bed: two walls with the rear arch through them, the bulkhead, the floor, tubs, the tailgate
    bz = stations(-2.7, -0.64, 0.4, [(B, R, ar)], extra=[-2.68, -0.66], arch_n=6, sill=sill)
    bot = lambda z: arch_floor(z, [(B, R, ar)], sill)
    def wall(s):
        def ring(z):
            b = bot(z); bi = max(0.78, b); h = HW - (0.01 if z < -2.66 else 0.0)
            r_ = [(h, b), (h, 1.105), (h - 0.015, 1.14), (h - 0.085, 1.14), (h - 0.1, 1.125), (h - 0.1, bi)]
            return r_ if s > 0 else [(-x, y) for x, y in reversed(r_)]
        return car.add_tint(zloft(car.nm('bedwall'), bz, ring, full=True))
    walls = [wall(1), wall(-1)]
    car.add_tint(box((2 * (HW - 0.095), 0.36, 0.06), (0, 0.96, -0.67), None, name=car.nm('bulk')))['reg'] = 'X'  # (plain: not the tailgate's letters)
    car.add_trim(box((2 * (HW - 0.1) + 0.004, 0.05, 1.98), (0, 0.765, -1.67), None, name=car.nm('bedfloor')), 'plastic')
    for s in (1, -1):
        car.add_trim(box((HW - 0.095 - 0.52, 0.2, 0.98), (s * (0.52 + (HW - 0.095 - 0.52) / 2), 0.87, B), None, bev=0.03, seg=1, name=car.nm('bedtub')), 'plastic')
        car.add_trim(box((0.115, 0.03, 2.05), (s * (HW - 0.045), 1.152, -1.67), None, name=car.nm('rail')), 'plastic')
    tg = car.add_tint(box((2 * (HW - 0.1) - 0.004, 0.53, 0.06), (0, 0.865, -2.665), None, bev=0.012, seg=1, name=car.nm('tailgate')))
    car.add_trim(box((2 * (HW - 0.1) - 0.01, 0.025, 0.07), (0, 1.14, -2.665), None, name=car.nm('tgcap')), 'plastic')
    # chrome bumpers, the grille, the toolbox
    fb = car.add_trim(box((2.06, 0.24, 0.2), (0, 0.56, 2.69), None, bev=0.05, seg=2, name=car.nm('fbump')), 'chrome')
    rb_ = car.add_trim(box((2.04, 0.2, 0.18), (0, 0.55, -2.785), None, bev=0.035, seg=1, name=car.nm('rbump')), 'chrome')
    car.add_trim(box((1.0, 0.022, 0.12), (0, 0.655, -2.79), None, name=car.nm('step')), 'plastic')
    car.add_trim(box((1.76, 0.07, 0.12), (0, 0.415, 2.6), None, name=car.nm('dam')), 'plastic')
    tb = car.add_trim(box((1.98, 0.25, 0.4), (0, 1.29, -0.93), None, bev=0.02, seg=1, name=car.nm('toolbox')), 'chrome')
    car.add_trim(box((1.9, 0.012, 0.012), (0, 1.33, -1.131), None, name=car.nm('tbline')), 'black')
    for x in (-0.6, 0.6): car.add_trim(box((0.12, 0.03, 0.03), (x, 1.36, -1.135), None, name=car.nm('tblatch')), 'black')
    # a borrowed traffic cone rolling round the bed
    cone = lathe_x(car.nm('cone'), [(0.17, -0.36), (0.17, -0.33), (0.11, -0.31), (0.085, -0.1), (0.07, -0.02), (0.04, 0.27), (0.02, 0.33), (0.0, 0.335)], 10, car.trim, band_cells(['orange', 'orange', 'orange', 'white', 'orange', 'orange', 'orange']))
    cone.data.transform(Matrix.Rotation(0.5, 4, 'Z')); cone.location = gv(0.1, 0.92, -1.95); car.body.append(cone)
    car.surf([body['shell'], body['house']] + walls + [fb, rb_, tg, tb])
    S = car.S
    car.on('grs', front_rays([-0.49, -0.16, 0.16, 0.49], [0.665, 0.83, 0.985], 4), 'chrome', off=0.006)
    gs = car.S
    for s in (1, -1):
        hb = car.on('hlb', front_rays([s * 0.5, s * 0.68, s * 0.87], [0.825, 0.99], 4), 'chrome', off=0.006)
        car.on('hl', front_rays([s * 0.52, s * 0.68, s * 0.85], [0.845, 0.97], 4), None, off=0.01, to=car.lamps, m=car.lamp_m, over=hb)
        car.on('ifr', corner_rays(s * 0.62, 2.3, [s * a for a in (8, 22, 36)], [0.71, 0.8]), None, off=0.008, to=car.inds, m=car.ind_m)
        car.on('sm', side_rays([2.42, 2.5], [0.78, 0.82], s * 3, -s), 'amber', off=0.006, depth=0.015)
        # tail lights + indicators on the ends of the bed walls
        car.on('tl', front_rays([s * 0.895, s * 0.975], [0.8, 0.96, 1.115], -4, 1), None, off=0.008, to=car.tails, m=car.tail_m)
        car.on('ird', front_rays([s * 0.895, s * 0.975], [0.69, 0.785], -4, 1), None, off=0.008, to=car.inds, m=car.ind_m)
        car.on('rsm', side_rays([-2.5, -2.42], [0.98, 1.02], s * 3, -s), 'red', off=0.006, depth=0.015)
        # flares round both arches, running boards, mud flaps
        car.on('flf', arch_rays(F, R, ar + 0.006, ar + 0.075, s), 'plastic', off=0.012, depth=0.04)
        car.on('flr', arch_rays(B, R, ar + 0.006, ar + 0.075, s), 'plastic', off=0.012, depth=0.04)
        car.add_trim(box((0.11, 0.045, 2.3), (s * (HW + 0.02), 0.405, 0.12), None, bev=0.01, seg=1, name=car.nm('board')), 'plastic')
        car.add_trim(box((0.012, 0.11, 2.3), (s * (HW - 0.03), 0.44, 0.12), None, name=car.nm('boardleg')), 'dark')
        car.add_trim(box((0.24, 0.3, 0.015), (s * 0.86, 0.325, B - 0.5), None, name=car.nm('flap')), 'black')  # (tops up into the body)
        car.add_trim(box((0.24, 0.3, 0.015), (s * 0.86, 0.325, F - 0.5), None, name=car.nm('flap')), 'black')
        car.on('dh', side_rays([0.38, 0.24], [1.02, 1.055], s * 3, -s), 'black', off=0.012, depth=0.024)
        # towing mirrors on two arms
        p, n = S.onto((s * 3, 1.16, 1.02), (-s, 0, 0), 0.0)
        car.add_trim(rod((p.x - s * 0.01, 1.16, 1.02), (p.x + s * 0.13, 1.2, 1.0), 0.014, None, seg=5, name=car.nm('marm')), 'black')
        car.add_trim(rod((p.x - s * 0.01, 1.3, 1.04), (p.x + s * 0.13, 1.4, 1.0), 0.014, None, seg=5, name=car.nm('marm')), 'black')
        car.add_trim(box((0.07, 0.3, 0.17), (p.x + s * 0.15, 1.3, 1.0), None, bev=0.02, seg=1, name=car.nm('mir')), 'black')
        car.add_glass(box((0.05, 0.25, 0.012), (p.x + s * 0.15, 1.3, 0.912), None, name=car.nm('mgl')))
    car.on('grm', front_rays([-0.45, -0.15, 0.15, 0.45], [0.69, 0.84, 0.96], 4), 'grille', off=0.012, uv_full=True)
    for y in (0.775, 0.885):
        car.on('grb', front_rays([-0.46, -0.15, 0.15, 0.46], [y, y + 0.03], 4), 'chrome', off=0.02)
    car.on('pf', front_rays([-0.23, 0.23], [0.5, 0.605], 4), 'plate', off=0.006, depth=0.02, uv_full=True)
    car.on('pr', front_rays([0.23, -0.23], [0.655, 0.76], -4, 1), 'plate', off=0.006, depth=0.02, uv_full=True)
    car.on('stk', front_rays([0.75, 0.45], [0.66, 0.72], -4, 1), 'sticker', off=0.005, depth=0.015, uv_full=True)
    car.on('tgh', front_rays([0.12, -0.12], [1.0, 1.04], -4, 1), 'black', off=0.008, depth=0.02)
    for x in (-0.28, 0.0, 0.28):  # roof clearance lights (they blink with the hazards)
        car.on('mk', [[(V3((x + dx, 3, z)), V3((0, -1, 0))) for dx in (-0.045, 0.045)] for z in (0.5, 0.46)], None, off=0.008, depth=0.02, to=car.inds, m=car.ind_m)
    car.add_trim(box((0.1, 0.09, 0.28), (0, 0.44, -2.9), None, name=car.nm('hitch')), 'metal')
    car.add_trim(cyl(0.035, 0.06, (0, 0.505, -2.98), None, axis='y', seg=8, name=car.nm('ball')), 'chrome')
    car.add_trim(cyl(0.04, 0.18, (-0.62, 0.42, -2.84), None, axis='z', seg=8, name=car.nm('exh')), 'chrome')
    car.rod_on('wp', (0.04, 3, 1.08), (0.66, 3, 1.04), (0, -1, 0), 0.012, 'black')
    car.rod_on('wp', (-0.62, 3, 1.08), (-0.02, 3, 1.07), (0, -1, 0), 0.012, 'black')
    p, n = S.onto((0.9, 3, 2.1), (0, -1, 0), 0.0)
    car.add_trim(rod(tuple(p - n * 0.01), tuple(p + V3((0, 0.85, -0.12))), 0.006, None, seg=4, name=car.nm('ant')), 'black')
    car.add_trim(box((2 * 0.84 - 0.32, 0.46, 0.5), (0, 0.57, F), None, name=car.nm('tub')), 'dark')
    car.add_trim(box((2 * 0.84 - 0.32, 0.3, 0.5), (0, 0.6, B), None, name=car.nm('tub')), 'dark')
    P = car.paint
    for reg in ('L', 'R'): P.fill(reg, base, seed=23 if reg == 'L' else 24)
    for reg in ('T', 'F', 'B', 'X'): P.fill(reg, base, seed=25)
    P.fill('U', 0x3a3a3f, seed=26)
    P.line('LR', [(0, 0.48, 1.24), (0, 0.8, 1.24), (0, 1.12, 1.16)], seam)
    P.line('LR', [(0, 0.48, 0.2), (0, 1.12, 0.2)], seam)
    P.line('LR', [(0, 0.48, -0.5), (0, 1.1, -0.5)], seam)
    P.line('LR', [(0, 0.49, 1.24), (0, 0.49, -0.5)], seam)
    P.line('LR', [(0, 0.95, -2.68), (0, 0.95, -0.66)], 0xd4d4d8)  # the bed's swage line
    P.line('LR', [(0, 0.95, 2.6), (0, 0.95, 1.3)], 0xd4d4d8)
    P.line('T', [(-0.88, 0, 1.15), (0.88, 0, 1.15)], seam); P.line('T', [(0.88, 0, 1.15), (0.86, 0, 2.6)], seam); P.line('T', [(-0.88, 0, 1.15), (-0.86, 0, 2.6)], seam)
    P.rect('L', (0, 0.88, -1.05), (0, 1.0, -0.93), seam); P.rect('L', (0, 0.89, -1.04), (0, 0.99, -0.94), base)
    # the tailgate: big stamped letters
    P.text('B', (0, 0.9, 0), 'JANK', 1, 0xbcbcc2)
    car.meta.update(id='pickup', lamps=[[0.66, 0.92, 2.73], [-0.66, 0.92, 2.73]], wb=round(F - B, 3))
    car.cabin = dict(belt=1.12, top=1.82, rows=[(0.42, 1.72, 0.42), (-0.22, 1.56, 0.42)], dash=1.22, wheel=(-0.42, 1.3, 0.19, 0.09), shelf=(1.1, 1.3))
    # far LOD: the bed walls as two 4-point rings, the floor + tailgate as one box
    lz = [-2.7] + [B + R * k for k in (-0.995, -0.45, 0.45, 0.995)] + [-0.64]
    for s in (1, -1):
        def lring(z, s=s):
            b = arch_floor(z, [(B, R, R + 0.004)], sill); h = HW
            r_ = [(h, b), (h, 1.14), (h - 0.1, 1.14), (h - 0.1, max(0.78, b))]
            return r_ if s > 0 else [(-x, y) for x, y in reversed(r_)]
        w_ = zloft(car.nm('l1bed'), lz, lring, full=True, caps=(True, False)); set_mats(w_, [car.tint]); car.lod1.append(w_)
    fl = box((2 * (HW - 0.103), 0.36, 2.04), (0, 0.96, -1.68), None, name=car.nm('l1bin'))
    bm = bmesh.new(); bm.from_mesh(fl.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z > 0.5 or abs(f.normal.x) > 0.5], context='FACES')  # (an open box: floor, bulkhead, tailgate)
    bm.to_mesh(fl.data); bm.free()
    set_mats(fl, [car.tint]); car.lod1.append(fl)
    return body


def build_pickup():
    car = Car('pickup', (-2.9, 2.82, 1.95, 1.0), atlas=atlas('YEEHAW', ('I BRAKE FOR', 'NOTHING'), 0xff4fd8, (0xffffff, 0xffe14d)))
    pickup(car)
    return car, 'p_car_pickup', (2.0, 1.92, 5.4), 0x3fae5a


# ------------------------------------------------------------ the panel van and the ice cream van
def van_half(b, t, H, c, ywin=1.3, ywt=2.12, tu1=0.006, tu=0.02, r_sh=0.08):
    """a van section: a tucked sill, a flat side up to the cab window line, the window band, a big rounded roof edge"""
    h = t - b
    y2 = b + min(0.04, h * 0.2)
    y3 = min(ywin, t - 0.13)
    y3b = clamp(t - 0.085, y3 + 0.02, ywt)
    top = t + r_sh * 0.55 + c
    return [(H - 0.05, b), (H - 0.012, y2), (H, y3), (H - tu1, y3b), (H - tu, t), (H - tu - r_sh, t + r_sh * 0.55), ((H - tu - r_sh) * 0.55, top - c * 0.3), (0.0, top)]


def van(car, ice=False, base=0xf2f2f2, seam=0x5a5a62):
    F, B, R, ar = 1.68, -1.55, 0.36, 0.43
    half, top, HW = (2.7, 2.56, 1.05) if ice else (2.55, 2.38, 1.0)
    zr, zf, sill = -half, half, 0.36
    wx = HW - 0.15
    car.wheels4(F, B, R, 0.24, wx, 'steel' if ice else 'steelb')
    arches = [(F, R, ar), (B, R, ar)]
    bot0 = spline([(zr, 0.4), (zr + 0.12, 0.37), (zr + 0.35, sill), (zf - 0.4, sill), (zf - 0.15, 0.37), (zf, 0.4)])
    bot = lambda z: arch_floor(z, arches, bot0)
    ws0, ws1 = 1.02, 1.86  # the windscreen, top and bottom
    tl = spline([(zr, top - 0.1), (zr + 0.03, top - 0.03), (zr + 0.1, top - 0.004), (ws0 - 0.2, top), (ws0 - 0.02, top - 0.02), (ws0 + 0.06, top - 0.1), (1.45, 1.75), (ws1, 1.2),
                 (2.1, 1.13), (zf - 0.12, 1.04), (zf - 0.04, 0.93), (zf, 0.8)])
    flare = lambda z: sum(0.01 * max(0.0, 1 - ((z - az) / (r * 1.25)) ** 2) for az, _, r in arches)
    hw0 = spline([(zr, HW - 0.035), (zr + 0.05, HW - 0.008), (zr + 0.15, HW), (zf - 0.5, HW), (zf - 0.2, HW - 0.02), (zf - 0.07, HW - 0.06), (zf, HW - 0.13)])
    hw = lambda z: hw0(z) + flare(z)
    crown = spline([(zr, 0.02), (zr + 0.2, 0.04), (ws0 - 0.1, 0.04), (ws0 + 0.2, 0.02), (ws1, 0.01), (zf, 0.004)])
    zs = stations(zr, zf, 0.5, arches, extra=[zr + 0.03, zr + 0.1, ws0 - 0.2, ws0, ws0 + 0.06, ws0 + 0.16, 1.3, 1.45, 1.6, 1.74, ws1, 2.1, zf - 0.12, zf - 0.05, 0.95, 0.25, -0.95, 0.88], arch_n=6, sill=sill)
    cw0, cw1 = 0.95, 1.72  # the cab's side windows
    def vmat(i, j, k):
        if i < 0 or i >= len(zs) - 1: return 0
        zc = (zs[i] + zs[i + 1]) / 2
        if 4 <= j <= 9 and ws0 + 0.03 < zc < ws1 - 0.02: return 1
        if j in (2, 11) and cw0 < zc < cw1: return 1
        return 0
    half_ = lambda z: van_half(bot(z), tl(z), hw(z), crown(z))
    shell = zloft(car.nm('shell'), zs, half_, vmat)
    set_mats(shell, [car.tint, car.glass]); car.tint_parts.append(shell); car.body.append(shell)
    car.surf([shell])
    S = car.S
    cr = lambda cx, cz, phis, ys, s: corner_rays(s * cx, cz, [s * p for p in phis], ys)
    for s in (1, -1):
        hh = car.on('hlh', swept(0.45, 2.1, [(0, 0.875, 1.065), (14, 0.875, 1.07), (28, 0.88, 1.075), (40, 0.89, 1.08), (52, 0.9, 1.08)], 3, s=s), 'black', off=0.004)
        car.on('hl', swept(0.45, 2.1, [(2, 0.89, 1.05), (14, 0.89, 1.055), (27, 0.895, 1.06)], 3, s=s), None, off=0.01, to=car.lamps, m=car.lamp_m, over=hh)
        car.on('hl', swept(0.45, 2.1, [(31, 0.9, 1.06), (40, 0.905, 1.065), (50, 0.912, 1.065)], 3, s=s), None, off=0.01, to=car.lamps, m=car.lamp_m, over=hh)
        car.on('ifr', swept(0.45, 2.1, [(44, 0.79, 0.86), (54, 0.79, 0.86), (64, 0.79, 0.86)], 2, s=s), None, off=0.007, to=car.inds, m=car.ind_m)
        car.on('rep', side_rays([zf - 0.62, zf - 0.55], [1.02, 1.05], s * 3, -s), None, off=0.007, depth=0.015, to=car.inds, m=car.ind_m)
        th = car.on('tlh', cr(HW - 0.2, zr + 0.25, [180, 160, 140, 120], [0.6, 0.95, 1.27], s), 'black', off=0.004)
        car.on('tl', cr(HW - 0.2, zr + 0.25, [178, 160, 140, 123], [0.79, 1.02, 1.25], s), None, off=0.009, to=car.tails, m=car.tail_m, over=th)
        car.on('ird', cr(HW - 0.2, zr + 0.25, [178, 160, 140, 123], [0.62, 0.765], s), None, off=0.009, to=car.inds, m=car.ind_m, over=th)
        # black bumper corners + side strips, the step, door handles, big mirrors on stalks
        car.on('rub', side_rays([F - 0.47, 0.1, B + 0.47], [0.42, 0.54], s * 3, -s), 'plastic', off=0.008, depth=0.03)
        car.on('rub', side_rays([B - 0.47, zr + 0.22], [0.42, 0.54], s * 3, -s), 'plastic', off=0.008, depth=0.03)
        car.on('dh', side_rays([1.06, 0.96], [1.24, 1.28], s * 3, -s), 'black', off=0.012, depth=0.024)
        p, n = S.onto((s * 3, 1.5, 1.55), (-s, 0, 0), 0.0)
        car.add_trim(rod((p.x - s * 0.01, 1.5, 1.55), (p.x + s * 0.17, 1.62, 1.52), 0.016, None, seg=5, name=car.nm('marm')), 'black')
        car.add_trim(box((0.07, 0.34, 0.19), (p.x + s * 0.19, 1.72, 1.52), None, bev=0.022, seg=1, name=car.nm('mir')), 'black')
        car.add_glass(box((0.05, 0.29, 0.012), (p.x + s * 0.19, 1.72, 1.422), None, name=car.nm('mgl')))
        if not ice: car.add_trim(box((0.05, 0.05, 2.9), (s * (HW - 0.2), top + 0.06, -0.9), None, name=car.nm('rail')), 'plastic')  # roof rails
    for z in ((-2.0, -0.9, 0.2) if not ice else ()):
        car.add_trim(box(((HW - 0.2) * 2 + 0.05, 0.035, 0.06), (0, top + 0.1, z), None, name=car.nm('bar')), 'metal')
    # nose: grille, plate, bumpers; back: barn doors with windows, a handle, the plate, the brake light
    car.on('gr', front_rays([-0.4, -0.13, 0.13, 0.4], [0.73, 0.82, 0.9], 4), 'grille', off=0.004, uv_full=True)
    fbs = car.on('fb', front_rays([-HW + 0.1, -0.5, 0.0, 0.5, HW - 0.1], [0.38, 0.47, 0.58], 4), 'plastic', off=0.012, depth=0.04)
    car.on('rb', front_rays([HW - 0.1, 0.5, 0.0, -0.5, -HW + 0.1], [0.38, 0.47, 0.58], -4, 1), 'plastic', off=0.012, depth=0.04)
    pf = car.on('pf', front_rays([-0.23, 0.23], [0.43, 0.535], 4), 'plate', off=0.022, depth=0.03, uv_full=True, over=fbs)
    car.on('pr', front_rays([0.23, -0.23], [0.67, 0.775], -4, 1), 'plate', off=0.006, depth=0.02, uv_full=True)
    for x in (0.44, -0.44):
        car.on('rw', front_rays([x + 0.33, x - 0.33] if x > 0 else [x + 0.33, x - 0.33], [1.6, 1.85, 2.12], -4, 1), 'glass', off=0.006, depth=0.02)
    car.on('rh', front_rays([0.2, 0.08], [1.18, 1.23], -4, 1), 'black', off=0.01, depth=0.02)
    car.on('stk', front_rays([0.72, 0.3], [0.8, 0.87], -4, 1) if ice else front_rays([-0.3, -0.72], [1.3, 1.37], -4, 1), 'sticker', off=0.005, depth=0.015, uv_full=True)
    car.on('bk', [[(V3((x, y, -4.0)), V3((0, 0, 1))) for x in (0.18, 0.0, -0.18)] for y in (top - 0.05, top - 0.02)], None, off=0.004, depth=0.02, to=car.tails, m=car.tail_m)
    car.rod_on('wp', (0.04, 3, ws1 - 0.07), (0.66, 3, ws1 - 0.13), (0, -1, 0), 0.012, 'black')
    car.rod_on('wp', (-0.62, 3, ws1 - 0.07), (-0.02, 3, ws1 - 0.09), (0, -1, 0), 0.012, 'black')
    car.add_trim(cyl(0.035, 0.16, (-0.55, 0.33, zr + 0.1), None, axis='z', seg=8, name=car.nm('exh')), 'metal')
    for az in (F, B):
        car.add_trim(box((2 * (wx - 0.12 - 0.035), 0.52, 0.56), (0, 0.5, az), None, name=car.nm('tub')), 'dark')
    P = car.paint
    for reg in ('L', 'R'): P.fill(reg, base, seed=33 if reg == 'L' else 34)
    for reg in ('T', 'F', 'B', 'X'): P.fill(reg, base, seed=35)
    P.fill('U', 0x3a3a3f, seed=36)
    # cab doors, the sliding door + its track, the rear doors
    P.line('LR', [(0, 0.86, 1.76), (0, 1.32, 1.76)], seam); P.line('LR', [(0, 0.4, 0.94), (0, 2.14, 0.94)], seam)
    P.line('LR', [(0, 0.41, 0.94), (0, 0.41, 1.24)], seam)
    if not ice:
        P.line('LR', [(0, 0.4, 0.86), (0, 2.08, 0.86)], seam); P.line('LR', [(0, 0.4, -0.95), (0, 2.08, -0.95)], seam)
        P.line('LR', [(0, 2.08, 0.86), (0, 2.08, -0.95)], seam); P.line('LR', [(0, 0.41, 0.86), (0, 0.41, -0.95)], seam)
        P.line('LR', [(0, 1.32, -0.97), (0, 1.32, -2.3)], 0x3a3a40, 1.5)  # the sliding door's track
    P.line('B', [(0.0, 0.4, 0), (0.0, top - 0.06, 0)], seam); P.line('B', [(HW - 0.14, 0.62, 0), (-HW + 0.14, 0.62, 0)], seam)
    P.line('T', [(-HW + 0.12, 0, ws1 + 0.02), (HW - 0.12, 0, ws1 + 0.02)], seam)
    P.line('T', [(HW - 0.12, 0, ws1 + 0.02), (HW - 0.14, 0, zf - 0.1)], seam); P.line('T', [(-HW + 0.12, 0, ws1 + 0.02), (-HW + 0.14, 0, zf - 0.1)], seam)
    for zz in (-1.8, -1.2, -0.6, 0.0, 0.6):  # stiffening ribs pressed into the roof
        P.line('T', [(-HW + 0.3, 0, zz), (HW - 0.3, 0, zz)], 0xdedee2, 1.5)
    # far LOD
    lz = lod_stations(zr, zf, [(F, R), (B, R)], [ws0, ws1, zf - 0.08] if ice else [zr + 0.1, ws0, ws0 + 0.15, ws1, zf - 0.08, 0.0])
    tight = [(a, r_, r_ + 0.004) for a, r_, _ in arches]
    def lhalf(z):
        bb, t, H, c = arch_floor(z, tight, bot0), tl(z), hw(z), crown(z)
        y3 = min(1.3, t - 0.13)
        return [(H - 0.03, bb), (H, y3), (H - 0.04, t), (0.0, t + 0.04 + c)]
    def lmat(i, j, k):
        zc = (lz[max(i, 0)] + lz[min(i + 1, len(lz) - 1)]) / 2
        if i < 0 or i >= len(lz) - 1: return 0
        if j in (2, 3) and ws0 + 0.03 < zc < ws1: return 1
        if j in (1, 4) and cw0 < zc < cw1: return 1
        return 0
    lb = zloft(car.nm('l1b'), lz, lhalf, lmat, open_bottom=True, caps=(True, True))
    set_mats(lb, [car.tint, car.trim]); car.lod1.append(lb)
    car.meta.update(id='icecream' if ice else 'van', lamps=[[0.64, 0.98, half], [-0.64, 0.98, half]], wb=round(F - B, 3))
    car.cabin = dict(belt=1.3, top=2.12, rows=[(1.12, 2.02, 0.45)], dash=1.33, wheel=(-0.45, 1.43, 0.2, 0.06), far=0x2a3a50)  # (the bulkhead behind the seats)
    return dict(shell=shell, tl=tl, hw=hw, top=top, HW=HW, half=half, bot=bot)


def build_van():
    car = Car('van', (-2.57, 2.57, 2.5, 1.02), atlas=atlas('VAN GO', ("HOW'S MY", 'DRIVING? NO'), 0xffffff, (0x101010, 0xe8323c)))
    van(car)
    # the game's own livery decal (plumbing / moving / hot dogs / cola) sits on the flat sides here
    car.meta['decal'] = dict(x=1.014, y=1.55, z=-1.05, w=2.6, h=0.8)
    for reg in ('L', 'R'):  # until then every van is a courier's (inside the decal's spot: the decal covers it)
        car.paint.text(reg, (0, 1.75, -1.05), 'JANK POST', 2, 0x26262c)
        car.paint.text(reg, (0, 1.44, -1.05), 'LEFT IN A SAFE PLACE', 1, 0x26262c)
    return car, 'p_car_van', (2.0, 2.4, 5.1), 0xe86a22


def ice_atlas(px, cell):
    """the ice cream van's extras: sprinkles on the scoops, the candy awning, the menu board"""
    r = np.random.default_rng(77)
    for k, base in (('cream', 0xff9ad5), ('cream2', 0xffc2e6)):
        c = cell(k); c[:] = hexrgb(base)
        for _ in range(26):
            y, x = r.integers(0, 16, 2); c[y, x] = hexrgb(int(r.choice([0xffe14d, 0x4fd8ff, 0x7dff4f, 0xffffff, 0x9b5cff])))
    a = cell('sign'); yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    a[:] = np.where((((xx + yy) // 6) % 2 == 0)[:, :, None], hexrgb(0xff9ad5), hexrgb(0xffffff))
    m = cell('menu'); m[:] = hexrgb(0xfff6e0); m[0, :] = m[-1, :] = m[:, 0] = m[:, -1] = hexrgb(0xff4fd8)
    text_px(m, 'MENU', 20, 2, 1, 0xff4fd8)
    for i, (cx, col) in enumerate(((10, 0xff9ad5), (32, 0xff9ad5), (54, 0xff9ad5))):  # three pink ice creams: the choice
        px_disc(m, cx, 15, 4.2, col); m[19:28, cx - 2:cx + 2] = hexrgb(0xd8a050); m[19:24, cx - 3:cx + 3] = hexrgb(0xd8a050)


def build_icecream():
    car = Car('icecream', (-2.72, 2.72, 2.7, 1.07), livery='livery', side_h=112, atlas=atlas('BRRR 99', ('HONK FOR', 'SPRINKLES'), 0xff9ad5, (0x5a1040, 0xffffff), extra=ice_atlas))
    mint, pink, plum, white = 0xbff5e4, 0xff4fd8, 0x5a1040, 0xffffff
    v = van(car, ice=True, base=mint, seam=0x6a9a8c)
    HW, top, S = v['HW'], v['top'], car.S
    P = car.paint
    # candy stripes along the top of both sides, the name, the joke
    for reg in ('L', 'R'):
        x0, y0 = P.pix(reg, (0, top - 0.06, 2.0 if reg == 'L' else -2.6)); x1, y1 = P.pix(reg, (0, top - 0.3, -2.6 if reg == 'L' else 2.0))
        xa, xb = sorted((int(x0), int(x1))); ya, yb = sorted((int(y0), int(y1)))
        for yy in range(ya, yb):
            for xx in range(xa, xb): P.px[yy, xx] = hexrgb(0xff9ad5 if ((xx + yy) // 5) % 2 == 0 else white)
    P.text('L', (0, 2.12, -0.9), 'ICE SCREAM', 1, pink, shadow=plum)
    P.text('R', (0, 1.66, -0.9), 'ICE SCREAM', 2, pink, shadow=plum)
    P.text('R', (0, 1.25, -0.9), 'ONE FLAVOUR. IT IS PINK.', 1, plum)
    P.text('B', (0, 1.36, 0), 'MIND', 1, pink, shadow=plum); P.text('B', (0, 1.04, 0), 'THE CONE', 1, pink, shadow=plum)
    # the serving hatch (curb side, +x): the dark opening, the counter, the awning propped up on two struts, the menu
    car.on('hatch', side_rays([-1.85, -1.2, -0.55, 0.05], [1.12, 1.56, 2.0], 3, -1), 'dark', off=0.004, depth=0.03)
    car.add_trim(box((0.24, 0.05, 2.0), (HW + 0.1, 1.1, -0.9), None, name=car.nm('counter')), 'white')
    aw = box((0.56, 0.035, 2.1), (HW + 0.27, 2.12, -0.9), None, rot=(0, 0, -0.35), name=car.nm('awning'))
    car.add_trim(aw); uv_fill(aw, TRIM['sign'], TEX_TRIM)
    for z in (-1.8, 0.0):
        car.add_trim(rod((HW + 0.005, 1.75, z), (HW + 0.48, 2.03, z), 0.012, None, seg=4, name=car.nm('strut')), 'chrome')
    car.on('menu', side_rays([0.72, 0.18], [1.25, 1.9], 3, -1), 'menu', off=0.006, depth=0.02, uv_full=True)
    # the cone the size of a child, on a post, two scoops with sprinkles, a drip, a cherry, a flake; the speaker for the song
    zc_, yb_ = -0.6, top + 0.08
    car.add_trim(cyl(0.05, 0.2, (0, top + 0.06, zc_), None, axis='y', seg=6, name=car.nm('post')), 'metal')
    cone = lathe([(0.02, 0.0), (0.42, 1.04), (0.45, 1.06), (0.45, 1.14), (0.38, 1.14)], (0, yb_, zc_), None, seg=11, axis='y', name=car.nm('cone'))
    car.add_trim(cone, 'cone')
    def scoop(r_, y, key, seed, sq=0.82):
        b_ = ball(r_, (0, y, zc_), None, scale=(1.0, sq, 1.0), seg=9, rings=6, name=car.nm('scoop'))
        jitter(b_, r_ * 0.06, seed=seed)
        return car.add_trim(b_, key)
    scoop(0.44, yb_ + 1.28, 'cream', 3)
    scoop(0.33, yb_ + 1.62, 'cream2', 4)
    for a_, k in ((0.4, 0), (2.6, 1)):  # drips down the cone
        d = ball(0.07, (math.cos(a_) * 0.4, yb_ + 1.07, zc_ + math.sin(a_) * 0.4), None, scale=(1, 2.2, 1), seg=5, rings=3, name=car.nm('drip'))
        car.add_trim(d, 'cream')
    car.add_trim(ball(0.085, (0.04, yb_ + 1.95, zc_), None, seg=7, rings=4, name=car.nm('cherry')), 'cherry')
    car.add_trim(rod((0.05, yb_ + 2.0, zc_), (0.1, yb_ + 2.12, zc_ + 0.03), 0.008, None, seg=4, name=car.nm('stem')), 'choc')
    car.add_trim(box((0.07, 0.42, 0.07), (-0.2, yb_ + 1.62, zc_ + 0.12), None, rot=(0.2, 0, 0.45), name=car.nm('flake')), 'choc')
    horn = lathe([(0.04, 0.0), (0.06, -0.12), (0.17, -0.3), (0.18, -0.31)], (0, top + 0.2, 0.75), None, seg=8, axis='z', name=car.nm('horn'), cap=False)
    car.add_trim(horn, 'chrome')
    car.add_trim(cyl(0.035, 0.18, (0, top + 0.1, 0.75), None, axis='y', seg=6, name=car.nm('hornpost')), 'metal')
    # far: the cone and one scoop (the van's whole silhouette from across the map)
    lc = lathe([(0.0, 0.0), (0.44, 1.1)], (0, yb_, zc_), None, seg=6, axis='y', name=car.nm('l1cone'))  # (the scoop sits on its lid)
    apply_mods(lc); set_mats(lc, [car.trim]); uv_fill(lc, TRIM['cone'], TEX_TRIM); car.lod1.append(lc)
    ls_ = ball(0.46, (0, yb_ + 1.1 + 0.46 * 1.1 - 0.004, zc_), None, scale=(1, 1.1, 1), seg=6, rings=3, name=car.nm('l1scoop'))  # (on the lid, as tall as both scoops)
    apply_mods(ls_); set_mats(ls_, [car.trim]); uv_fill(ls_, TRIM['cream'], TEX_TRIM); car.lod1.append(ls_)
    car.meta.update(cone=[0, round(yb_ + 1.8, 3), zc_])
    return car, 'p_car_icecream', (2.1, 3.05, 5.4), None


# ------------------------------------------------------------ the city bus
def box_half(b, t, H, c, ywin, r_roof=0.14, tu=0.02):
    """a bus / box-body section: tucked skirt, flat side to the window line, a slight lean to the roof, a round roof edge"""
    y2 = b + 0.05
    y3 = clamp(ywin, y2 + 0.03, t - 0.1)
    top = t + r_roof * 0.5 + c
    return [(H - 0.06, b), (H - 0.015, y2), (H, y3), (H - tu, t), (H - tu - r_roof, t + r_roof * 0.5), ((H - tu - r_roof) * 0.55, top - c * 0.3), (0.0, top)]


def bus_atlas(px, cell):
    g = cell('sign'); g[:] = hexrgb(0x0c0c0e)
    text_px(g, 'NOT IN', 14, 4, 1, 0xffae1a); text_px(g, 'SERVICE', 11, 14, 1, 0xffae1a)
    text_px(g, '69', 2, 22, 1, 0xffae1a)
    m = cell('menu'); m[:] = hexrgb(0xffe14d); m[0, :] = m[-1, :] = m[:, 0] = m[:, -1] = hexrgb(0x141414)
    text_px(m, 'YOUR AD', 11, 5, 1, 0x141414); text_px(m, 'HERE', 20, 15, 1, 0xff4fd8); text_px(m, '(PLEASE)', 8, 24, 1, 0x141414)


def build_bus():
    pink, yel, white, ink, black = 0xff4fd8, 0xffe14d, 0xf4f4f0, 0x2a0a26, 0x16161a
    car = Car('bus', (-5.95, 5.95, 3.45, 1.3), livery='livery', W=512, side_h=96, top_h=64, end_h=64,
              atlas=atlas('JNK BUS', ('NO STANDING', '(OR SITTING)'), 0xffffff, (0x101010, 0xe8323c), extra=bus_atlas))
    F, B, R = 3.55, -2.45, 0.5
    half, HW, top = 5.9, 1.275, 3.18
    zr, zf, sill = -half, half, 0.4
    car.wheel('wheel_fl', HW - 0.2, F, R, 0.3, True, 'truck'); car.wheel('wheel_fr', -(HW - 0.2), F, R, 0.3, True, 'truck')
    car.wheel('wheel_rl', HW - 0.2, B, R, 0.3, False, 'truck', dual=0.33); car.wheel('wheel_rr', -(HW - 0.2), B, R, 0.3, False, 'truck', dual=0.33)
    arches = [(F, R, 0.58), (B, R, 0.6)]
    bot0 = spline([(zr, 0.45), (zr + 0.2, sill), (zf - 0.2, sill), (zf, 0.45)])
    bot = lambda z: arch_floor(z, arches, bot0)
    tl = spline([(zr, top - 0.14), (zr + 0.04, top - 0.05), (zr + 0.14, top), (zf - 0.18, top), (zf - 0.05, top - 0.1), (zf, top - 0.2)])
    hw0 = spline([(zr, HW - 0.2), (zr + 0.04, HW - 0.07), (zr + 0.12, HW - 0.02), (zr + 0.3, HW), (zf - 0.3, HW), (zf - 0.12, HW - 0.02), (zf - 0.04, HW - 0.07), (zf, HW - 0.2)])
    crown = spline([(zr, 0.02), (zr + 0.3, 0.05), (zf - 0.3, 0.05), (zf, 0.02)])
    zs = stations(zr, zf, 0.95, arches, extra=[zr + 0.04, zr + 0.12, zr + 0.3, zf - 0.04, zf - 0.12, zf - 0.3], arch_n=6, sill=sill)
    shell = car.add_tint(zloft(car.nm('shell'), zs, lambda z: box_half(bot(z), tl(z), hw0(z), crown(z), 1.6)))
    car.surf([shell])
    S = car.S
    # the glazing: panes on the painted black band, the curb side (+x) has two glass doors
    def panes(s, z0, z1, n, y0=1.66, y1=2.84):
        w = (z1 - z0) / n
        for k in range(n):
            a, b = z0 + k * w + 0.06, z0 + (k + 1) * w - 0.06
            car.glass_on('pane', side_rays([a, b] if s < 0 else [b, a], [y0, y1], s * 4, -s))
    panes(1, -5.45, -0.95, 4); panes(1, 0.55, 4.1, 3); panes(-1, -5.45, 4.1, 8)
    car.glass_on('drv', side_rays([4.25, 5.55], [1.66, 2.84], -4, 1))
    for zc in (4.85, -0.2):
        fr = car.on('door', side_rays([zc + 0.62, zc - 0.62], [0.42, 1.5, 2.86], 4, -1), 'black', off=0.006)
        for a, b in ((zc + 0.57, zc + 0.03), (zc - 0.03, zc - 0.57)):
            car.glass_on('dglass', side_rays([a, b], [0.6, 1.55, 2.78], 4, -1), over=fr)
    # front: windscreen, the destination sign over it, lamps, bumper, plate, wipers, the mirrors on their stalks
    car.glass_on('ws', front_rays([-HW + 0.12, -0.6, 0.0, 0.6, HW - 0.12], [1.05, 2.0, 2.86], 6))
    car.on('dest', front_rays([-0.9, 0.9], [2.9, 3.1], 6), 'sign', off=0.008, uv_full=True)
    for s in (1, -1):
        hh = car.on('hlh', front_rays([s * (HW - 0.62), s * (HW - 0.4), s * (HW - 0.15)], [0.66, 0.9], 6), 'black', off=0.005)
        car.on('hl', front_rays([s * (HW - 0.6), s * (HW - 0.42)], [0.69, 0.87], 6), None, off=0.01, to=car.lamps, m=car.lamp_m, over=hh)
        car.on('hl', front_rays([s * (HW - 0.38), s * (HW - 0.2)], [0.69, 0.87], 6), None, off=0.01, to=car.lamps, m=car.lamp_m, over=hh)
        car.on('ifr', corner_rays(s * (HW - 0.3), zf - 0.3, [s * a for a in (52, 66, 80)], [0.7, 0.82]), None, off=0.008, to=car.inds, m=car.ind_m)
        th = car.on('tlh', front_rays([s * (HW - 0.36), s * (HW - 0.1)], [0.66, 0.8, 1.26], -6, 1), 'black', off=0.005)
        car.on('tl', front_rays([s * (HW - 0.34), s * (HW - 0.12)], [0.86, 1.04, 1.23], -6, 1), None, off=0.01, to=car.tails, m=car.tail_m, over=th)
        car.on('ird', front_rays([s * (HW - 0.34), s * (HW - 0.12)], [0.69, 0.82], -6, 1), None, off=0.01, to=car.inds, m=car.ind_m, over=th)
        car.on('rep', side_rays([2.85, 2.75] if s > 0 else [2.75, 2.85], [1.2, 1.26], s * 4, -s), None, off=0.007, depth=0.015, to=car.inds, m=car.ind_m)
        for zz in (-4.0, -1.2, 1.6):
            car.on('sm', side_rays([zz + 0.05, zz - 0.05], [0.5, 0.56], s * 4, -s), 'amber', off=0.006, depth=0.015)
        # rabbit-ear mirrors: a stalk out of the roof corner, bent down in front of the windscreen
        p0 = (s * (HW - 0.06), top - 0.08, zf - 0.12)
        p1 = (s * (HW + 0.18), top - 0.2, zf + 0.12); p2 = (s * (HW + 0.2), top - 0.6, zf + 0.22)
        car.add_trim(rod(p0, p1, 0.022, None, seg=5, name=car.nm('stalk')), 'black')
        car.add_trim(rod(p1, p2, 0.022, None, seg=5, name=car.nm('stalk')), 'black')
        car.add_trim(box((0.24, 0.42, 0.08), (s * (HW + 0.2), top - 0.8, zf + 0.22), None, bev=0.02, seg=1, name=car.nm('mir')), 'black')
        car.add_glass(box((0.2, 0.37, 0.012), (s * (HW + 0.2), top - 0.8, zf + 0.22 - 0.04 - 0.004), None, name=car.nm('mgl')))
    car.on('fb', front_rays([-HW + 0.14, -0.6, 0.0, 0.6, HW - 0.14], [0.47, 0.55, 0.64], 6), 'plastic', off=0.012, depth=0.04)
    car.on('rbp', front_rays([HW - 0.14, 0.6, 0.0, -0.6, -HW + 0.14], [0.47, 0.55, 0.64], -6, 1), 'plastic', off=0.012, depth=0.04)
    car.on('fgr', front_rays([-0.56, -0.19, 0.19, 0.56], [0.7, 0.78, 0.86], 6), 'grille', off=0.006, uv_full=True)  # a vent over the bumper
    car.on('pf', front_rays([-0.23, 0.23], [0.5, 0.605], 6), 'plate', off=0.03, depth=0.04, uv_full=True)
    car.on('pr', front_rays([0.23, -0.23], [0.76, 0.865], -6, 1), 'plate', off=0.008, depth=0.02, uv_full=True)
    car.on('lv', front_rays([0.95, 0.0, -0.95], [0.95, 1.3, 1.62], -6, 1), 'grille', off=0.006, uv_full=True)  # the engine's louvres
    car.glass_on('rwin', front_rays([HW - 0.3, 0.0, -HW + 0.3], [2.1, 2.85], -6, 1))
    car.on('ad', front_rays([0.62, -0.62], [1.75, 2.02], -6, 1), 'menu', off=0.006, depth=0.02, uv_full=True)
    car.on('stk', front_rays([0.9, 0.48], [0.68, 0.74], -6, 1), 'sticker', off=0.005, depth=0.015, uv_full=True)
    car.rod_on('wp', (0.05, 1.12, 6), (0.85, 1.55, 6), (0, 0, -1), 0.016, 'black', off=0.025)
    car.rod_on('wp', (-0.95, 1.12, 6), (-0.15, 1.55, 6), (0, 0, -1), 0.016, 'black', off=0.025)
    # roof: the AC pod, two hatches
    car.add_trim(box((1.6, 0.3, 2.4), (0, top + 0.2, -2.6), None, bev=0.07, seg=1, name=car.nm('ac')), 'white')
    car.add_trim(box((1.2, 0.04, 1.9), (0, top + 0.36, -2.6), None, name=car.nm('acgr')), 'grille')
    for z in (0.8, 3.0):
        car.add_trim(box((0.7, 0.07, 0.7), (0, top + 0.15, z), None, bev=0.02, seg=1, name=car.nm('hatch')), 'plastic')
    for az, _, r_ in arches:
        car.add_trim(box((2 * (HW - 0.2 - 0.15 - 0.035) - (0.33 if az < 0 else 0), 0.62, 0.7), (0, 0.66, az), None, name=car.nm('tub')), 'dark')
    # the livery: pink below, a yellow band, the black window band, white roof; the name on both sides
    P = car.paint
    for reg in ('L', 'R'):
        P.fill(reg, pink, var=0.03, seed=41 if reg == 'L' else 42)
        P.rect(reg, (0, 1.45, zr), (0, 1.62, zf), yel)
        P.rect(reg, (0, 1.62, zr), (0, 2.88, zf), black)
        P.rect(reg, (0, 2.88, zr), (0, 3.45, zf), white)
        P.poly(reg, [(0, 1.62, -3.2), (0, 1.62, -4.4), (0, 0.45, -5.95), (0, 0.45, -4.75)], yel)  # the swoosh at the back
        if reg == 'L': P.text(reg, (0, 1.37, 2.25), 'JANK TRANSIT', 2, white, shadow=ink)  # (curb side: between the doors)
        else:
            P.text(reg, (0, 1.06, 0.45), 'JANK TRANSIT', 3, white, shadow=ink)
            P.text(reg, (0, 0.66, 0.45), 'WE GO PLACES. EVENTUALLY.', 1, ink)
    P.fill('F', pink, var=0.03, seed=43); P.rect('F', (-1.3, 1.45, 0), (1.3, 1.62, 0), yel); P.rect('F', (-1.3, 1.62, 0), (1.3, 3.45, 0), black)
    P.fill('B', pink, var=0.03, seed=44); P.rect('B', (-1.3, 1.62, 0), (1.3, 1.72, 0), yel); P.rect('B', (-1.3, 2.05, 0), (1.3, 2.9, 0), black); P.rect('B', (-1.3, 2.9, 0), (1.3, 3.45, 0), white)
    P.fill('T', white, var=0.03, seed=45); P.fill('U', 0x2a2a2e, seed=46); P.fill('X', pink, seed=47)
    # far LOD: the box with its arches, the glazing as trim (glass) faces
    lz = lod_stations(zr, zf, [(F, R), (B, R)], [zr + 0.12, zf - 0.12])
    tight = [(F, R, R + 0.004), (B, R, R + 0.004)]
    lb = zloft(car.nm('l1b'), lz, lambda z: [(hw0(z) - 0.03, arch_floor(z, tight, bot0)), (hw0(z), 1.62), (hw0(z) - 0.02, 2.88), (hw0(z) - 0.15, tl(z) + 0.07), (0.0, tl(z) + 0.12)],
               lambda i, j, k: 1 if j in (1, 6) and 0 <= i < len(lz) - 1 else 0, open_bottom=True, caps=(True, True))
    set_mats(lb, [car.tint, car.trim]); car.lod1.append(lb)
    car.meta.update(id='bus', lamps=[[HW - 0.4, 0.78, half], [-(HW - 0.4), 0.78, half]], wb=round(F - B, 3))
    car.cabin = dict(W=512, side_h=64, end_h=64, bus=dict(seats=[-5.2, -4.45, -3.7, -2.95, -2.2, -1.45, 1.0, 1.75, 2.5, 3.25], y0=1.3, ytop=2.06,
                     poles=[5.45, 4.25, 0.4, -0.8], drv=(4.45, 2.42, -0.72), dash=1.38, wheel=(-0.72, 1.52, 0.24, 0.06), rowtops=[1.95, 1.9, 1.86], back=2.2))
    return car, 'p_car_bus', (2.55, 3.25, 11.8), None


# ------------------------------------------------------------ the box truck
lib.FONT.setdefault('%', ['11001', '11010', '00010', '00100', '01000', '01011', '10011'])
lib.FONT.setdefault('(', ['00010', '00100', '01000', '01000', '01000', '00100', '00010'])
lib.FONT.setdefault(')', ['01000', '00100', '00010', '00010', '00010', '00100', '01000'])


def uv_paint(P, o, override=None):
    """UVs of a part onto a second body map (the truck's box), each face into the map its normal faces"""
    bpy.context.view_layer.update()  # (a fresh object's matrix_world is stale until then)
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; mw = o.matrix_world
    for p in me.polygons:
        n = b2g(mw.to_3x3() @ p.normal)
        reg = (override(n, b2g(mw @ p.center)) if override else None) or P.region_of(n)
        for li in p.loop_indices:
            q = b2g(mw @ me.vertices[me.loops[li].vertex_index].co)
            s_, t = P.st(reg, q)
            uv[li].uv = uv_px(P.R[reg], (P.W, P.H), clamp(s_, 0, 1), clamp(t, 0, 1))
    return o


def build_truck():
    def badge(px, cell):  # the cab's nameplate
        b_ = cell('sticker2'); b_[:] = hexrgb(0x18181c); b_[0, :] = b_[-1, :] = hexrgb(0xb8bec8)
        text_px(b_, 'JANK', (64 - 23) // 2, 5, 1, 0xdde2ea)
    car = Car('truck', (2.4, 4.42, 3.0, 1.23), atlas=atlas('FIZZ 9', ('CAUTION:', 'FIZZY LOAD'), 0xffe14d, (0x101010, 0xe8323c), extra=badge))
    F, B, R = 3.15, -2.6, 0.5
    half, HW, HC = 4.4, 1.25, 1.21  # half length, the box's half width, the cab's
    car.wheel('wheel_fl', HW - 0.22, F, R, 0.3, True, 'truck'); car.wheel('wheel_fr', -(HW - 0.22), F, R, 0.3, True, 'truck')
    car.wheel('wheel_rl', HW - 0.22, B, R, 0.3, False, 'truck', dual=0.33); car.wheel('wheel_rr', -(HW - 0.22), B, R, 0.3, False, 'truck', dual=0.33)
    # the cab: a short-nose cab-over, its windscreen raked like the code's
    z0, zf, sill = 2.42, half, 0.55
    arches = [(F, R, 0.58)]
    bot0 = spline([(z0, sill), (4.15, 0.56), (zf, 0.6)])
    bot = lambda z: arch_floor(z, arches, bot0)
    tl = spline([(z0, 2.82), (z0 + 0.05, 2.855), (3.6, 2.86), (3.72, 2.82), (4.22, 1.92), (4.32, 1.48), (zf, 1.22)])
    hw0 = spline([(z0, HC - 0.02), (z0 + 0.08, HC), (4.1, HC), (4.3, HC - 0.03), (zf, HC - 0.09)])
    crown = spline([(z0, 0.02), (3.5, 0.03), (zf, 0.005)])
    zs = stations(z0, zf, 0.3, arches, extra=[z0 + 0.03, z0 + 0.08, 2.95, 3.6, 3.68, 3.74, 3.9, 4.05, 4.2, 4.27, 4.34, zf - 0.03], arch_n=6, sill=sill)
    def cmat(i, j, k):
        if i < 0 or i >= len(zs) - 1: return 0
        zc = (zs[i] + zs[i + 1]) / 2
        if 4 <= j <= 9 and 3.76 < zc < 4.2: return 1
        if j in (2, 11) and 2.95 < zc < 4.0: return 1
        return 0
    cab = zloft(car.nm('cab'), zs, lambda z: van_half(bot(z), tl(z), hw0(z), crown(z), ywin=1.75, ywt=2.62, tu1=0.02, tu=0.04, r_sh=0.07), cmat)
    set_mats(cab, [car.tint, car.glass]); car.tint_parts.append(cab); car.body.append(cab)
    # the air deflector over the cab, up to the box's roof
    dfl = side([(z0 + 0.0, 2.86), (3.42, 2.86), (3.3, 2.98), (z0 + 0.25, 3.75), (z0 + 0.0, 3.78)], 2.0, (0, 0, 0), None, bev=0.03, seg=1, name=car.nm('deflector'))
    car.add_tint(dfl)
    # the box: its own map (the JANK COLA livery, the roller door), corner posts, rails
    BP = Paint('cola_t', (-4.42, 2.34, 3.9, HW + 0.02), W=256, side_h=128, top_h=32, end_h=64, y0=1.05)
    bimg = bpy.data.images.new('cola_t', BP.W, BP.H, alpha=False)
    cola = mat('cola', 0xffffff, rough=0.3, metal=0.05, clearcoat=0.8, tex=bimg)
    car.extra_paints = [(BP, bimg)]
    bx = box((2 * HW, 2.72, 6.7), (0, 2.47, -1.05), None, bev=0.035, seg=1, name=car.nm('box'))
    apply_mods(bx); set_mats(bx, [cola]); uv_paint(BP, bx); car.body.append(bx)
    for sx in (1, -1):
        for zz in (2.29, -4.39):
            car.add_trim(box((0.07, 2.76, 0.07), (sx * (HW - 0.01), 2.47, zz), None, name=car.nm('post')), 'metal')
        car.add_trim(box((0.05, 0.1, 6.66), (sx * (HW + 0.012), 3.79, -1.05), None, name=car.nm('topr')), 'metal')
        car.add_trim(box((0.06, 0.13, 6.66), (sx * (HW + 0.015), 1.15, -1.05), None, name=car.nm('botr')), 'metal')
    car.add_trim(box((0.92, 0.35, 6.6), (0, 0.955, -1.05), None, name=car.nm('frame')), 'dark')  # (up into the box floor)
    car.surf([cab, dfl, bx])
    S = car.S
    for s in (1, -1):
        hh = car.on('hlh', front_rays([s * (HC - 0.58), s * (HC - 0.36), s * (HC - 0.14)], [0.82, 1.08], 6), 'black', off=0.005)
        car.on('hl', front_rays([s * (HC - 0.56), s * (HC - 0.36)], [0.85, 1.05], 6), None, off=0.01, to=car.lamps, m=car.lamp_m, over=hh)
        car.on('ifr', front_rays([s * (HC - 0.32), s * (HC - 0.16)], [0.85, 1.05], 6), None, off=0.01, to=car.inds, m=car.ind_m, over=hh)
        car.on('rep', side_rays([4.05, 4.15] if s < 0 else [4.15, 4.05], [1.3, 1.36], s * 4, -s), None, off=0.007, depth=0.015, to=car.inds, m=car.ind_m)
        # tail lights + indicators on the under-run frame's ends (the box floor's back corners)
        car.on('tl', front_rays([s * (HW - 0.34), s * (HW - 0.1)], [1.27, 1.5], -6, 1), None, off=0.012, to=car.tails, m=car.tail_m)
        car.on('ird', front_rays([s * (HW - 0.34), s * (HW - 0.1)], [1.54, 1.66], -6, 1), None, off=0.012, to=car.inds, m=car.ind_m)
        for zz in (-3.8, -2.0, -0.2, 1.6):
            car.on('sm', side_rays([zz + 0.05, zz - 0.05] if s > 0 else [zz - 0.05, zz + 0.05], [1.24, 1.3], s * 4, -s), 'amber', off=0.03, depth=0.04)
        # mirrors (main + wide angle) on a bent arm, side guards, mud flaps, the rear mudguards
        p, n = S.onto((s * 4, 2.25, 4.02), (-s, 0, 0), 0.0)
        car.add_trim(rod((p.x - s * 0.01, 2.25, 4.02), (p.x + s * 0.2, 2.3, 4.05), 0.02, None, seg=5, name=car.nm('marm')), 'black')
        car.add_trim(box((0.08, 0.44, 0.2), (p.x + s * 0.22, 2.3, 4.05), None, bev=0.02, seg=1, name=car.nm('mir')), 'black')
        car.add_glass(box((0.06, 0.38, 0.012), (p.x + s * 0.22, 2.3, 4.05 - 0.1 - 0.004), None, name=car.nm('mgl')))
        car.add_trim(box((0.08, 0.2, 0.18), (p.x + s * 0.22, 1.98, 4.05), None, bev=0.015, seg=1, name=car.nm('mir2')), 'black')
        for y in (0.5, 0.78):
            car.add_trim(box((0.04, 0.07, 3.3), (s * (HW - 0.05), y, -0.35), None, name=car.nm('guard')), 'metal')
        car.add_trim(box((0.05, 0.62, 0.05), (s * (HW - 0.05), 0.82, 1.28), None, name=car.nm('gpost')), 'metal')
        car.add_trim(box((0.05, 0.62, 0.05), (s * (HW - 0.05), 0.82, -1.98), None, name=car.nm('gpost')), 'metal')
        car.add_trim(box((0.7, 0.05, 1.3), (s * 0.9, 1.07, B), None, name=car.nm('mudg')), 'plastic')
        car.add_trim(box((0.7, 0.6, 0.015), (s * 0.9, 0.78, B - 0.66), None, name=car.nm('flap')), 'black')
        car.on('dh', side_rays([3.12, 2.98] if s > 0 else [2.98, 3.12], [1.66, 1.71], s * 4, -s), 'black', off=0.012, depth=0.024)
    # face: grille + bars, bumper with a step, plate, the sun visor, roof markers, wipers
    car.on('gr', front_rays([-0.78, -0.26, 0.26, 0.78], [0.78, 0.98, 1.18], 6), 'grille', off=0.006, uv_full=True)
    for y in (0.83, 0.93, 1.03, 1.13):
        car.on('grb', front_rays([-0.76, -0.26, 0.26, 0.76], [y, y + 0.025], 6), 'chrome', off=0.016)
    fb = car.on('fb', front_rays([-HC + 0.1, -0.6, 0.0, 0.6, HC - 0.1], [0.62, 0.7, 0.8], 6), 'plastic', off=0.02, depth=0.05)
    car.on('pf', front_rays([-0.23, 0.23], [0.64, 0.745], 6), 'plate', off=0.03, depth=0.04, uv_full=True, over=fb)
    car.add_trim(box((2.06, 0.03, 0.28), (0, 2.78, 3.8), None, rot=(-0.25, 0, 0), name=car.nm('visor')), 'black')
    car.on('cowl', front_rays([-1.0, -0.35, 0.35, 1.0], [1.78, 1.86], 6), 'black', off=0.006)
    car.on('badge', front_rays([-0.26, 0.26], [1.36, 1.49], 6), 'sticker2', off=0.008, depth=0.02, uv_full=True)
    for x in (-0.5, 0.0, 0.5):
        car.add_trim(box((0.12, 0.05, 0.06), (x, 2.82, 3.93), None, name=car.nm('mkb')), 'black')
        mk = box((0.09, 0.034, 0.014), (x, 2.82, 3.965), None, name=car.nm('mk')); set_mats(mk, [car.ind_m]); uv_fill(mk, TRIM['white'], TEX_TRIM); car.inds.append(mk)  # (blink with the hazards)
    car.rod_on('wp', (0.05, 1.98, 6), (0.85, 2.32, 6), (0, 0, -1), 0.016, 'black', off=0.014)
    car.rod_on('wp', (-0.95, 1.98, 6), (-0.15, 2.32, 6), (0, 0, -1), 0.016, 'black', off=0.014)
    # back: the roller door's handle, the under-run bar (hazard), the plate, a sticker
    car.on('rh', front_rays([0.15, -0.15], [1.28, 1.34], -6, 1), 'metal', off=0.012, depth=0.024)
    ub = car.add_trim(box((2.2, 0.16, 0.1), (0, 0.62, -4.52), None, name=car.nm('underrun')))
    uv_fill(ub, TRIM['hazard'], TEX_TRIM)
    for x in (-0.7, 0.7): car.add_trim(box((0.08, 0.5, 0.08), (x, 0.87, -4.45), None, name=car.nm('urpost')), 'metal')
    car.on('pr', [[(V3((x, y, -6)), V3((0, 0, 1))) for x in (0.23, -0.23)] for y in (1.6, 1.705)], 'plate', off=0.006, depth=0.02, uv_full=True)
    car.on('stk', front_rays([0.95, 0.55], [1.62, 1.68], -6, 1), 'sticker', off=0.005, depth=0.015, uv_full=True)
    # the fuel tank (curb side), the battery box, the stack behind the cab
    car.add_trim(cyl(0.3, 1.1, (HW - 0.38, 0.83, 1.75), None, axis='z', seg=12, name=car.nm('tank')), 'chrome')  # (hung under the box floor)
    for zz in (1.35, 2.15): car.add_trim(box((0.66, 0.05, 0.05), (HW - 0.38, 0.52, zz), None, name=car.nm('strap')), 'black')
    car.add_trim(box((0.5, 0.42, 0.7), (-(HW - 0.34), 0.91, 1.75), None, bev=0.02, seg=1, name=car.nm('batt')), 'plastic')
    car.add_trim(rod((-(HW - 0.15), 1.05, 2.37), (-(HW - 0.15), 3.35, 2.37), 0.065, None, seg=8, name=car.nm('stack')), 'chrome')
    car.add_trim(rod((-(HW - 0.15), 3.35, 2.37), (-(HW - 0.15), 3.5, 2.3), 0.065, None, seg=8, name=car.nm('stacktip')), 'chrome')
    car.add_trim(box((2 * (HC - 0.22 - 0.15 - 0.03), 0.6, 0.62), (0, 0.85, F), None, name=car.nm('tub')), 'dark')
    # cab paint: door + cab seams; the box: the livery
    P = car.paint
    for reg in ('L', 'R'): P.fill(reg, 0xf2f2f2, seed=51 if reg == 'L' else 52)
    for reg in ('T', 'F', 'B', 'X'): P.fill(reg, 0xf2f2f2, seed=53)
    P.fill('U', 0x3a3a3f, seed=54)
    seam = 0x5a5a62
    P.line('LR', [(0, 0.62, 2.9), (0, 2.66, 2.9)], seam); P.line('LR', [(0, 1.3, 3.95), (0, 1.75, 4.02)], seam); P.line('LR', [(0, 0.62, 2.9), (0, 0.62, 3.0)], seam)
    pink, yel, ink, cyan = 0xff2fa8, 0xffe14d, 0x3a0030, 0x4fd8ff
    for reg in ('L', 'R'):
        BP.fill(reg, 0xf4f4f0, var=0.02, seed=61)
        BP.rect(reg, (0, 1.4, -4.15), (0, 3.4, 2.05), pink)
        zA, zB = (-4.15, 2.05) if reg == 'R' else (2.05, -4.15)
        BP.poly(reg, [(0, 1.4, zA), (0, 1.4, zA + (zB - zA) * 0.45), (0, 2.25, zA + (zB - zA) * 0.62), (0, 2.1, zB), (0, 1.4, zB)], yel)
        mid = -1.45  # (the bottle stands at the cab end)
        BP.text(reg, (0, 2.82, mid), 'JANK COLA', 3, 0xffffff, shadow=ink)
        BP.text(reg, (0, 2.26, mid), 'NOW WITH 40% MORE FIZZ', 1, ink)
        BP.text(reg, (0, 2.03, mid), '(LEGALLY)', 1, ink)
        zb_ = 1.55
        BP.rect(reg, (0, 1.55, zb_ - 0.17), (0, 2.75, zb_ + 0.17), cyan); BP.rect(reg, (0, 2.75, zb_ - 0.07), (0, 3.1, zb_ + 0.07), cyan)
        BP.rect(reg, (0, 1.7, zb_ - 0.1), (0, 2.6, zb_ - 0.04), 0xffffff); BP.rect(reg, (0, 3.1, zb_ - 0.09), (0, 3.18, zb_ + 0.09), 0xe8323c)
    BP.fill('B', 0xd8dade, var=0.02, seed=62)
    for k in range(18):  # the roller door's slats
        y = 1.18 + k * 0.145
        BP.line('B', [(HW - 0.08, y, 0), (-HW + 0.08, y, 0)], 0x9a9ea6)
    BP.fill('T', 0xf4f4f0, seed=63); BP.fill('F', 0xf4f4f0, seed=64); BP.fill('U', 0x2a2a2e, seed=65); BP.fill('X', 0x1e2c40, seed=66)
    # far LOD: the cab (tint), the box + its wheels and glass in the box map (2 materials)
    lz = [z0, F - R * 0.995, F - R * 0.45, F + R * 0.45, F + R * 0.995, 3.74, 4.2, zf]
    tight = [(F, R, R + 0.004)]
    l1c = zloft(car.nm('l1c'), lz, lambda z: [(hw0(z) - 0.03, arch_floor(z, tight, bot0)), (hw0(z), min(1.75, tl(z) - 0.13)), (hw0(z) - 0.04, tl(z)), (0.0, tl(z) + 0.05)],
                lambda i, j, k: 1 if (0 <= i < len(lz) - 1 and ((j in (2, 3) and 3.74 <= lz[i] < 4.2) or (j in (1, 4) and 2.95 < (lz[i] + lz[i + 1]) / 2 < 4.0))) else 0, open_bottom=True, caps=(True, True))
    set_mats(l1c, [car.tint, cola]); car.lod1.append(l1c)
    l1x = box((2 * HW, 2.72, 6.7), (0, 2.47, -1.05), None, name=car.nm('l1box')); set_mats(l1x, [cola]); uv_paint(BP, l1x); car.lod1.append(l1x)
    l1d = side([(z0, 2.86), (3.42, 2.86), (z0, 3.78)], 2.0, (0, 0, 0), None, name=car.nm('l1dfl')); set_mats(l1d, [car.tint]); car.lod1.append(l1d)
    for sx in (1, -1):
        g_ = box((0.66, 0.2, 1.1), (sx * 0.9, 1.03, B), None, name=car.nm('l1mud')); set_mats(g_, [cola]); uv_fill(g_, BP.R['U'], (BP.W, BP.H)); car.lod1.append(g_)
    car.lod_cola = (cola, BP)
    car.meta.update(id='truck', lamps=[[HC - 0.46, 0.95, half], [-(HC - 0.46), 0.95, half]], wb=round(F - B, 3), livery='cola box')  # (on the lenses)
    car.cabin = dict(belt=1.75, top=2.62, rows=[(3.15, 2.56, 0.5)], dash=2.04, wheel=(-0.5, 2.13, 0.22, 0.065), far=0x26354a)
    return car, 'p_car_truck', (2.5, 3.75, 8.8), 0x2f6fe0


BUILDERS = {'sedan': build_sedan, 'taxi': build_taxi, 'hatch': build_hatch, 'pickup': build_pickup, 'van': build_van, 'icecream': build_icecream, 'bus': build_bus, 'truck': build_truck}


def main():
    only = arg('only')
    ids = only.split(',') if isinstance(only, str) else list(BUILDERS)
    pdir = arg('preview')
    for cid in ids:
        lib.reset(); lib._mats.clear()
        car, fid, size, colour = BUILDERS[cid]()
        root = finish_car(car, fid, size)
        if not arg('no-export'): export(root, fid)
        if isinstance(pdir, str): os.makedirs(pdir, exist_ok=True); preview(car, fid, pdir, colour)
        if not arg('no-sheet') and not isinstance(pdir, str): sheets(car, fid, colour)


main()
