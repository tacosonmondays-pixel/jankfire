# Blade kit for the Blender knives and swords: the same real silhouettes the code models use (public/js/blades/kit.js),
# built as proper geometry. Model space is every weapon's: tip / forward = -z, up = +y, the grip at the origin, the
# blade's thickness along x. Blades are edge down: spine on top, cutting edge at the bottom. Side-view profiles are
# lists of (z, y) points in metres, real sizes.
#   curve(ctrl, n)        a smooth line through control points (what kit.js curve() gives: the same shapes)
#   resample(pts, n)      n points spread evenly along a line
#   blade(...)            a ground blade from its spine and edge lines: flats, a bevel from the grind line down to a
#                         real edge, a distal taper, fullers cut in as grooves, the steel painted by a function of
#                         (how far along, how high) so coatings, bare edges, hamons and etchings land where they should
#   oval(), torus()       small shapes the knives need
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _place, _link


def curve(ctrl, n=16, tension=0.5):
    """n points on a Catmull-Rom spline through ctrl [(z, y)], evenly in its parameter (three's CatmullRomCurve3
    'catmullrom' with this tension, which is what the code blades are drawn with)"""
    P = [Vector((p[0], p[1])) for p in ctrl]; m = len(P) - 1; out = []
    for k in range(max(2, n)):
        u = k / (max(2, n) - 1) * m; i = min(m - 1, int(math.floor(u))); t = u - i
        p0 = P[i - 1] if i > 0 else P[i] - (P[i + 1] - P[i]); p1, p2 = P[i], P[i + 1]
        p3 = P[i + 2] if i + 2 <= m else P[i + 1] + (P[i + 1] - P[i])
        t0, t1 = (p2 - p0) * tension, (p3 - p1) * tension
        c2 = (p2 - p1) * 3 - t0 * 2 - t1; c3 = (p1 - p2) * 2 + t0 + t1  # (Hermite, as three's CubicPoly)
        q = p1 + t0 * t + c2 * t * t + c3 * t * t * t
        out.append((q.x, q.y))
    return out


def resample(pts, n):
    acc = [0.0]
    for i in range(1, len(pts)): acc.append(acc[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    L = acc[-1] or 1.0; out = []
    for k in range(n):
        s = k / (n - 1) * L; i = 1
        while i < len(acc) - 1 and acc[i] < s: i += 1
        t = (s - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1.0)
        out.append((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t))
    return out


class Lines:
    """a blade's spine and edge, resampled to n stations: heights and fractions for placing things in millimetres"""
    def __init__(self, spine, edge, n):
        self.n = n; self.S = resample(spine, n); self.E = resample(edge, n)
    def _at(self, s, k, arr):
        f = max(0.0, min(1.0, s)) * (self.n - 1); i = min(self.n - 2, int(f)); t = f - i
        return arr[i][k] + (arr[i + 1][k] - arr[i][k]) * t
    def sy(self, s): return self._at(s, 1, self.S)
    def ey(self, s): return self._at(s, 1, self.E)
    def hgt(self, s): return max(1e-4, self.sy(s) - self.ey(s))
    def frac(self, s, y): return (y - self.ey(s)) / self.hgt(s)  # a height y (m) -> 0 at the edge .. 1 at the spine


def ramp(x, a, b): return max(0.0, min(1.0, (x - a) / (b - a))) if b != a else float(x >= a)


def blade(spine, edge, m, n=40, thick=0.004, grind=0.4, taper=0.55, edge_thick=0.0004, grooves=(), swedge=None, name='blade', x=0.0, rows=3):
    """spine / edge: (z, y) lines from the heel to the tip (they may meet at the tip or not: a cleaver's blunt front).
    grind: where the bevel starts, as a share of the height above the edge. taper: how much thinner at the tip.
    grooves: [(lo(s), hi(s), depth(s))] fullers: lo / hi = shares of the height, depth in metres (0 = no groove there).
    swedge: (lo(s), thin(s)) a false edge ground into the spine: from the share lo up, the blade thins to thin(s) of
    its thickness at the spine. UVs: u = along (0 heel .. 1 tip), v = up (0 edge .. 1 spine): paint it with paint()."""
    L = Lines(spine, edge, n); et = edge_thick / 2
    half = lambda i: thick * (1 - taper * i / (n - 1)) / 2
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    def vrows(s):
        up = []  # the rows above the grind line: fullers' lips and beds, the swedge's start (always the same count)
        for lo, hi, dp in grooves:
            a, b = lo(s), hi(s); up += [a, (a + b) / 2, b]
        if swedge: up.append(swedge[0](s))
        g, top, gap = grind + 0.012, 0.992, 0.006
        up = [max(g, min(top, v)) for v in sorted(up)]
        for k in range(1, len(up)): up[k] = max(up[k], up[k - 1] + gap)  # never two rows on one line...
        for k in range(len(up) - 1, -1, -1): up[k] = min(up[k], top - gap * (len(up) - 1 - k))  # ...and none over the spine
        return [grind * k / rows for k in range(rows)] + [grind] + up + [1.0]
    def xat(i, s, v, k, vs):
        t = half(i); e = min(et, t)
        xx = t if v >= grind else e + (t - e) * (v / grind)
        for lo, hi, dp in grooves:
            a, b = lo(s), hi(s)
            if a < v < b: xx -= dp(s) * math.sin(math.pi * (v - a) / (b - a)) ** 0.8
        if swedge:
            a = swedge[0](s)
            if v > a: xx *= 1 - (1 - swedge[1](s)) * (v - a) / max(1e-6, 1 - a)
        return max(e * 0.5, xx)
    G = {}
    for i in range(n):
        s = i / (n - 1); vs = vrows(s); (sz, sy), (ez, ey) = L.S[i], L.E[i]
        for sx in (1, -1):
            col = []
            for k, v in enumerate(vs):
                col.append((bm.verts.new(gv(x + sx * xat(i, s, v, k, vs), ey + (sy - ey) * v, ez + (sz - ez) * v)), (s, v)))
            G[(i, sx)] = col
    def face(vs, uvs):
        try: f = bm.faces.new(vs)
        except ValueError: return
        for lp, uv in zip(f.loops, uvs): lp[uvl].uv = uv
    nr = len(G[(0, 1)])
    for i in range(n - 1):
        for sx in (1, -1):
            A, B2 = G[(i, sx)], G[(i + 1, sx)]
            for k in range(nr - 1):
                q = [A[k], B2[k], B2[k + 1], A[k + 1]]
                if sx < 0: q = q[::-1]
                face([v for v, _ in q], [uv for _, uv in q])
        # the spine's back and the edge's flat (a hair wide)
        for k, rev in ((nr - 1, False), (0, True)):
            q = [G[(i, 1)][k], G[(i + 1, 1)][k], G[(i + 1, -1)][k], G[(i, -1)][k]]
            dv = -0.02 if k else 0.02  # (a sliver of the skin for the strip: its two sides can't share a line of it)
            uvs = [q[0][1], q[1][1], (q[2][1][0], q[2][1][1] + dv), (q[3][1][0], q[3][1][1] + dv)]
            if rev: q = q[::-1]; uvs = uvs[::-1]
            face([v for v, _ in q], uvs)
    for i, rev in ((0, False), (n - 1, True)):  # the heel, and the front if it is blunt
        if i and math.hypot(L.S[i][0] - L.E[i][0], L.S[i][1] - L.E[i][1]) < 0.001: continue
        t = half(i); u0 = 0.0 if i == 0 else 0.97  # (an end face, in strips across, mapped flat onto a corner of the skin)
        cu = lambda sx, v: u0 + 0.03 * (0.5 + 0.5 * sx * min(1.0, xat(i, i / (n - 1), v, 0, None) / max(t, 1e-6)))
        for k in range(nr - 1):
            q = [(G[(i, 1)][k][0], (cu(1, G[(i, 1)][k][1][1]), G[(i, 1)][k][1][1])), (G[(i, -1)][k][0], (cu(-1, G[(i, -1)][k][1][1]), G[(i, -1)][k][1][1])),
                 (G[(i, -1)][k + 1][0], (cu(-1, G[(i, -1)][k + 1][1][1]), G[(i, -1)][k + 1][1][1])), (G[(i, 1)][k + 1][0], (cu(1, G[(i, 1)][k + 1][1][1]), G[(i, 1)][k + 1][1][1]))]
            if rev: q = q[::-1]
            face([v for v, _ in q], [uv for _, uv in q])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, dist=2e-6, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 28)
    return o


def paint(name, L, fn, w=256, h=64):
    """the blade's skin: fn(s, v, y) -> 0xRRGGBB for the point s along (0 heel .. 1 tip), v up (0 edge .. 1 spine),
    y = its real height in metres. small and crusty on purpose (nearest filtered in the game)"""
    def draw(px):
        r = np.random.default_rng(abs(hash(name)) % 9973)
        for col in range(w):
            s = (col + 0.5) / w
            for row in range(h):
                v = 1 - (row + 0.5) / h; c = hexrgb(fn(s, v, L.ey(s) + L.hgt(s) * v))
                px[row, col] = c * (0.94 + 0.12 * r.random())
    return tex_canvas(name, w, h, draw)


def oval(rx, ry, n=24, p=2.0):
    """a superellipse outline [(x, y)], counter-clockwise (p 2 = an ellipse, 2.4 = a little fuller)"""
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n; c, s = math.cos(a), math.sin(a)
        out.append((rx * math.copysign(abs(c) ** (2 / p), c), ry * math.copysign(abs(s) ** (2 / p), s)))
    return out


def plate(outline, depth, z, m, name='plate', bev=0.0, bend=None):
    """a front-view outline [(x, y)] extruded along the blade (z), its middle at z. bend(x, y) -> how far that point
    leans toward +z (a guard whose points tip back at the hand)"""
    bm = bmesh.new(); rings = []
    for dz in (-depth / 2, depth / 2):
        rings.append([bm.verts.new(gv(px, py, z + dz + (bend(px, py) if bend else 0.0))) for px, py in outline])
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    bm.faces.new(rings[0]); bm.faces.new(rings[1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 40); bevel(o, bev, 2, 40)
    return o


def torus(R, r, pos, m, axis='x', seg=20, sides=8, name='ring'):
    """a ring: axis x = the hole goes across the knife (a karambit's finger ring)"""
    bm = bmesh.new(); rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; ring = []
        for j in range(sides):
            b = 2 * math.pi * j / sides; rr = R + r * math.cos(b); off = r * math.sin(b)
            p = {'x': (off, math.sin(a) * rr, math.cos(a) * rr), 'z': (math.cos(a) * rr, math.sin(a) * rr, off), 'y': (math.cos(a) * rr, off, math.sin(a) * rr)}[axis]
            ring.append(bm.verts.new(gv(pos[0] + p[0], pos[1] + p[1], pos[2] + p[2])))
        rings.append(ring)
    for i in range(seg):
        A, B2 = rings[i], rings[(i + 1) % seg]
        for j in range(sides): bm.faces.new((A[j], A[(j + 1) % sides], B2[(j + 1) % sides], B2[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o


def squash(o, sx=1.0, sy=1.0):
    """an oval section: scale a lathed part across (x) and up (y)"""
    o.data.transform(Matrix.Diagonal((sx, 1.0, sy, 1.0)))  # blender axes: x, y = -game z, z = game y
    return o
