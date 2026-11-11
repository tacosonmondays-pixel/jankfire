# The Islands lighthouse (shared/map.js lighthouse()): drawn over its own boxes (tools/arch/dump.mjs), which stay what
# you bump into (an octagon in boxes: octoBoxes). An octagonal masonry tower, 6 m across its flats, tapering a little
# toward the top (its corners cut deeper as it rises), on a flared stone plinth; red and white bands with string
# courses between them, small framed windows climbing round it with the stair, a door at the foot; the iron stair
# once round all eight faces (shared/map.js lhStair: its steps are the game's): chequer-plate treads on brackets bolted
# into the stone, an outer stringer, a handrail on balusters, grated landings at the corners; up through a stairwell
# onto an octagonal gallery on long iron brackets with a baluster railing; the
# lantern room, an octagon of glowing glass behind diamond glazing bars, under a red domed cap with a vent ball and
# a lightning rod (the light inside is the game's). Islands S&D's has no stair and no gallery (lighthouse_sd).
# local frame = the map's (the tower over x 79..85, z -9..-3).
# run: node tools/arch/dump.mjs islands lighthouse tools/blender/arch/boxes/lighthouse.json
#      node tools/arch/dump.mjs islands_sd lighthouse_sd tools/blender/arch/boxes/lighthouse_sd.json
#      blender52 -b --python tools/blender/arch/make_lighthouse.py -- [lighthouse|lighthouse_sd]   (both by default)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'lhwhite': ('trim', '#ffffff', {}), 'lhred': ('trim', '#f0302a', {}), 'course': ('trim', '#e2dccf', {}), 'plinth': ('concrete', '#c4bcae', {}),
    'iron': ('metalplate', '#2b4a3a', {}), 'tread': ('metalplate', '#9a9ca6', {}), 'bolt': ('metalplate', '#6a6458', {}), 'rust': ('stucco', '#9a5230', {}), 'roof': ('trim', '#d8302a', {}), 'brass': ('metalplate', '#e0b040', {}),
    'pane': ('glass', '#283040', {}), 'door': ('planks', '#3a8ad8', {}), 'frame': ('trim', '#ffffff', {}), 'lamp': ('stucco', '#ffd98a', {'glow': True}),
})
NOCAST.update({'iron', 'brass', 'pane', 'frame', 'lamp', 'bolt', 'rust'})
X0, X1, Z0, Z1, TOP = 79.0, 85.0, -9.0, -3.0, 18.0  # the tower's flats
CX, CZ = 82.0, -6.0


def octo(x0, z0, x1, z1, c, y, o=0.0):
    """the 8 corners of an octagon over a rectangle (flats on its sides, corners cut c), pushed out o, at height y,
    in order round it"""
    c = c + o * (2 - math.sqrt(2)); x0 -= o; z0 -= o; x1 += o; z1 += o
    return [Vector(p) for p in ((x0 + c, y, z0), (x1 - c, y, z0), (x1, y, z0 + c), (x1, y, z1 - c), (x1 - c, y, z1), (x0 + c, y, z1), (x0, y, z1 - c), (x0, y, z0 + c))]


def face_out(q, mat, centre=None, sub=None):
    """a quad (or tri) wound to face away from the centre line (or from centre)"""
    cen = sum(q, Vector()) / len(q); ref = Vector((CX, cen.y, CZ)) if centre is None else centre
    n = (q[1] - q[0]).cross(q[-1] - q[0])
    if n.dot(cen - ref) < 0: q = q[::-1]
    if len(q) == 3: K.tri(q, mat)
    else: K.quad(q, mat, sub=sub)


def band(A, B, mat, sub=1.5):
    """the skin between two rings of 8 (A below, B above)"""
    for i in range(8):
        j = (i + 1) % 8
        face_out([A[i], A[j], B[j], B[i]], mat, sub=sub)


def cap(R, mat, up=True):
    """an octagon's flat top (or underside): a fan round its middle"""
    c = sum(R, Vector()) / 8
    for i in range(8):
        t = [c, R[i], R[(i + 1) % 8]]
        n = (t[1] - t[0]).cross(t[2] - t[0])
        K.tri(t if (n.y > 0) == up else t[::-1], mat)


def taper(y):  # the tower's corner cut at height y: deeper toward the top (it narrows across the corners)
    return 1.62 + 0.4 * max(0.0, min(1.0, (y - 1.2) / (TOP - 1.4)))


def ring(y, o=0.03): return octo(X0, Z0, X1, Z1, taper(y), y, o)


def inside(p, poly):
    x, z = p[0], p[1]; n = len(poly); c = False
    for i in range(n):
        (ax, az), (bx, bz) = poly[i], poly[(i + 1) % n]
        if (az > z) != (bz > z) and x < ax + (z - az) * (bx - ax) / (bz - az): c = not c
    return c


def poly_fill(outer, holes, y, mat, up=True):
    """a flat floor: the outer outline (x, z) with holes cut out, triangulated, at height y"""
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
        if n.length < 1e-4: continue  # (a sliver)
        K.tri(t if (n.y > 0) == up else t[::-1], mat)
    bm.free()


def window(face, y, h=1.1, w=0.7):
    """a small framed window on tower face `face` (0..7, the ring's edges) centred at height y"""
    A, B = ring(y - h / 2), ring(y + h / 2)
    a0, a1, b0, b1 = A[face], A[(face + 1) % 8], B[face], B[(face + 1) % 8]
    c = (a0 + a1 + b0 + b1) / 4; along = (a1 - a0).normalized(); up = ((b0 + b1) / 2 - (a0 + a1) / 2).normalized()
    out = along.cross(up).normalized()
    if out.dot(Vector((c.x - CX, 0, c.z - CZ))) < 0: out = -out
    def P(u, v, d): return c + along * u + up * v + out * d
    face_out([P(-w / 2 - 0.03, -h / 2 - 0.03, 0.03), P(w / 2 + 0.03, -h / 2 - 0.03, 0.03), P(w / 2 + 0.03, h / 2 + 0.03, 0.03), P(-w / 2 - 0.03, h / 2 + 0.03, 0.03)], 'pane', centre=c - out)  # (its edges under the frame)
    # the frame: one moulding round it (front, outer and inner edges back to the wall), no overlapping pieces
    o_, i_ = [(-w / 2 - 0.1, -h / 2 - 0.1), (w / 2 + 0.1, -h / 2 - 0.1), (w / 2 + 0.1, h / 2 + 0.1), (-w / 2 - 0.1, h / 2 + 0.1)], [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    for k in range(4):
        k2 = (k + 1) % 4
        face_out([P(*o_[k], 0.07), P(*o_[k2], 0.07), P(*i_[k2], 0.07), P(*i_[k], 0.07)], 'frame', centre=c - out * 2)
        em = (P(*o_[k], 0) + P(*o_[k2], 0)) / 2; face_out([P(*o_[k], 0.07), P(*o_[k2], 0.07), P(*o_[k2], 0.005), P(*o_[k], 0.005)], 'frame', centre=c)
        im = (P(*i_[k], 0) + P(*i_[k2], 0)) / 2; face_out([P(*i_[k], 0.07), P(*i_[k2], 0.07), P(*i_[k2], 0.015), P(*i_[k], 0.015)], 'frame', centre=im + (im - c).normalized() * 0.5)
    FL.bar(K, P(-w / 2 - 0.2, -h / 2 - 0.15, 0.09), P(w / 2 + 0.2, -h / 2 - 0.15, 0.09), 0.16, 'course', h=0.07)  # the sill


# ---- the iron stair: the same numbers as shared/map.js lhStair (faces in climbing order: 0 = south-west ... 7 = west)
SA0, SA1, STN = 3.0, 4.8, math.tan(math.pi / 8)
SL = SA0 * STN; SG = 2 * SL / 9; SR = 18 / 80; SE = SA1 * STN


def sf(k):
    a = math.radians(135 - 45 * k); return (math.cos(a), math.sin(a)), (math.sin(a), -math.cos(a))


def sat(k, u, s, y):
    (nx, nz), (tx, tz) = sf(k); return Vector((CX + nx * u + tx * s, y, CZ + nz * u + tz * s))


def wall_u(k, y):  # how far out face k of the drawn tower is at height y (the cut faces creep in as it tapers)
    if k % 2: return 3.03
    return (6.06 - taper(y) - 0.03 * (2 - math.sqrt(2))) / math.sqrt(2)


def clip(poly, planes):
    """a convex polygon [(x, z)] cut by half-planes (a, b, c): keeps a*x + b*z <= c"""
    for (a, b, c) in planes:
        out = []
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
            if fp <= 0: out.append(p)
            if (fp < 0 < fq) or (fq < 0 < fp):
                t = fp / (fp - fq); out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        poly = out
        if len(poly) < 3: return []
    return poly


def us_plane(k, which, v):  # the half-plane u_k <= v ('u'), u_k >= v ('-u'), s_k <= v ('s'), s_k >= v ('-s'), as (a, b, c)
    (nx, nz), (tx, tz) = sf(k)
    a, b, o = (nx, nz, nx * CX + nz * CZ) if which in ('u', '-u') else (tx, tz, tx * CX + tz * CZ)
    return (a, b, v + o) if which in ('u', 's') else (-a, -b, -(v + o))


def slab(poly, y, th, top, side):
    """a flat plate: poly [(x, z)] (convex, any winding) th thick under y. top / sides / underside"""
    if len(poly) < 3: return
    P = [Vector((x, y, z)) for (x, z) in poly]; Q = [Vector((x, y - th, z)) for (x, z) in poly]
    up = (P[1] - P[0]).cross(P[2] - P[0]).y > 0
    if not up: P, Q = P[::-1], Q[::-1]
    for i in range(1, len(P) - 1): K.tri([P[0], P[i], P[i + 1]], top); K.tri([Q[0], Q[i + 1], Q[i]], side)
    c = sum(P, Vector()) / len(P)
    for i in range(len(P)):
        j = (i + 1) % len(P); face_out([P[i], P[j], Q[j], Q[i]], side, centre=c - Vector((0, th / 2, 0)))


def obb(c, ax, ay, az, hx, hy, hz, mat):
    """a box turned to the axes ax, ay, az (unit), half sizes hx, hy, hz round c"""
    P = lambda i, j, k: c + ax * (hx * i) + ay * (hy * j) + az * (hz * k)
    F = [[P(1, -1, -1), P(1, 1, -1), P(1, 1, 1), P(1, -1, 1)], [P(-1, -1, -1), P(-1, -1, 1), P(-1, 1, 1), P(-1, 1, -1)],
         [P(-1, 1, -1), P(-1, 1, 1), P(1, 1, 1), P(1, 1, -1)], [P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1), P(-1, -1, 1)],
         [P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1)], [P(-1, -1, -1), P(-1, 1, -1), P(1, 1, -1), P(1, -1, -1)]]
    for q in F: face_out(q, mat, centre=c)


def stair(rng):
    def rail_y(k, s):  # the flight's rail line: from the landing below (s = -SL) to the landing above (s = SL)
        return SR * (10 * k + 10 * (s + SL) / (2 * SL))
    for k in range(8):
        (nx, nz), (tx, tz) = sf(k)
        # the treads: chequer plate with a lip, out to the stringer
        for j in range(9):
            h = (10 * k + j + 1) * SR; ui = wall_u(k, h) - 0.03; s0, s1 = -SL + j * SG - 0.03, -SL + (j + 1) * SG
            slab([(p.x, p.z) for p in (sat(k, ui, s0, 0), sat(k, SA1, s0, 0), sat(k, SA1, s1, 0), sat(k, ui, s1, 0))], h, 0.04, 'tread', 'iron')
            FL.bar(K, sat(k, ui + 0.05, s0 + 0.01, h - 0.05), sat(k, SA1 - 0.02, s0 + 0.01, h - 0.05), 0.03, 'iron', h=0.03)  # (its turned-down front edge)
            sm = (s0 + s1) / 2 + 0.015
            if h < 1.0:  # the first steps stand on legs
                for u in (ui + 0.75, SA1 - 0.12): FL.bar(K, sat(k, u, sm, h - 0.02), sat(k, u, sm, 0.0), 0.05, 'iron')
                continue
            # the bracket: a plate bolted to the stone, an arm under the tread, a strut up to it
            wp = sat(k, wall_u(k, h - 0.3) + 0.016, sm, 0); wn = Vector((nx, 0, nz))
            obb(Vector((wp.x, h - 0.27, wp.z)), Vector((tx, 0, tz)), Vector((0, 1, 0)), wn, 0.045, 0.23, 0.02, 'iron')  # (its back sunk a little into the stone)
            FL.bar(K, sat(k, ui, sm, h - 0.062), sat(k, SA1 - 0.06, sm, h - 0.062), 0.04, 'iron', h=0.05)  # (its end sunk into the stone)
            FL.bar(K, sat(k, wall_u(k, h - 0.42) + 0.03, sm, h - 0.42), sat(k, ui + 0.95, sm, h - 0.08), 0.035, 'iron')
            for yb in (h - 0.14, h - 0.4):
                b0 = Vector((wp.x, yb, wp.z)) + wn * 0.018; FL.tube(K, b0, b0 + wn * 0.025, 0.024, 0.018, 'bolt', n=4, caps=(False, True))
            if rng.random() < 0.3:  # a rust streak down the stone from the plate
                ru = wall_u(k, h - 0.7) + 0.006; a = sat(k, ru, sm - 0.025, h - 0.5); b = sat(k, ru, sm + 0.025, h - 0.5)
                c, d = sat(k, ru, sm + 0.012, h - 0.5 - rng.uniform(0.25, 0.6)), sat(k, ru, sm - 0.012, h - 0.5 - 0.2)
                face_out([a, b, c, d], 'rust')
        # the outer stringer and the rail, from the landing below to the landing above
        s_a, s_b = -SL, SL
        y_a, y_b = rail_y(k, s_a), rail_y(k, s_b)
        uo = SA1 + 0.025
        for (sa, sb) in ((s_a + (SG if k == 0 else 0), s_b),):  # (the first one starts off the sand)
            A, Bp = sat(k, uo, sa, rail_y(k, sa) - 0.08), sat(k, uo, sb, y_b - 0.08)
            FL.bar(K, A, Bp, 0.04, 'iron', h=0.3)  # (a flat bar on edge, its top just over the nosings)
        r0 = 3 if k == 0 else 0  # (no rail by the first three steps: the game's posts start there too)
        sr = -SL + r0 * SG if r0 else s_a
        uo2 = SA1 + 0.07
        FL.bar(K, sat(k, uo2, sr, rail_y(k, sr) + 1.02), sat(k, uo2, s_b, y_b + 1.02), 0.06, 'iron', h=0.05)
        FL.bar(K, sat(k, uo2, sr, rail_y(k, sr) + 0.52), sat(k, uo2, s_b, y_b + 0.52), 0.03, 'iron')
        for j in range(r0, 9):  # a baluster at every step
            sb = -SL + (j + 0.5) * SG
            FL.bar(K, sat(k, uo2, sb, rail_y(k, sb) + 0.07), sat(k, uo2, sb, rail_y(k, sb) + 1.0), 0.03, 'iron')
        if r0:  # the newel post at the rail's foot, a brass knob on it
            nb = sat(k, uo2, sr, rail_y(k, sr)); FL.obox(K, (nb.x - 0.05, nb.y - 0.3, nb.z - 0.05), (nb.x + 0.05, nb.y + 1.08, nb.z + 0.05), 'iron')
            FL.tube(K, Vector((nb.x, nb.y + 1.08, nb.z)), Vector((nb.x, nb.y + 1.2, nb.z)), 0.06, 0.03, 'brass', n=8)
        if k == 7: continue
        # the landing round the corner: a grated plate (a frame, bars across, a cross bar or two), its own bracket
        hl = (10 * k + 10) * SR
        P = clip([(60, -30), (100, -30), (100, 20), (60, 20)], [us_plane(k, '-s', SL), us_plane(k + 1, 's', -SL), us_plane(k, 'u', SA1), us_plane(k + 1, 'u', SA1),
                                                                 us_plane(k, '-u', wall_u(k, hl) - 0.03), us_plane(k + 1, '-u', wall_u(k + 1, hl) - 0.03)])
        if not P: continue
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            FL.bar(K, Vector((a[0], hl - 0.025 - 0.004 * (i % 2), a[1])), Vector((b[0], hl - 0.025 - 0.004 * (i % 2), b[1])), 0.05, 'iron', h=0.05)  # (every other one a hair lower: where they cross at the corners, not one face on another)
        ph = math.radians(135 - 45 * k - 22.5); d = (math.cos(ph), math.sin(ph)); q = (-d[1], d[0])
        cx = sum(p[0] for p in P) / len(P); cz = sum(p[1] for p in P) / len(P)
        for i in range(-13, 14):  # bars along the corner's bisector, 9 cm apart
            o = i * 0.09; base = (cx + q[0] * o, cz + q[1] * o)
            seg = clip([(base[0] - d[0] * 3 - q[0] * 0.006, base[1] - d[1] * 3 - q[1] * 0.006), (base[0] + d[0] * 3 - q[0] * 0.006, base[1] + d[1] * 3 - q[1] * 0.006),
                        (base[0] + d[0] * 3 + q[0] * 0.006, base[1] + d[1] * 3 + q[1] * 0.006), (base[0] - d[0] * 3 + q[0] * 0.006, base[1] - d[1] * 3 + q[1] * 0.006)],
                       _shrink(P, 0.035))
            if len(seg) >= 3: slab(seg, hl - 0.004, 0.036, 'iron', 'iron')
        for o in (-0.35, 0.35):  # cross bars under them
            base = (cx + d[0] * o, cz + d[1] * o)
            seg = clip([(base[0] - q[0] * 3 - d[0] * 0.01, base[1] - q[1] * 3 - d[1] * 0.01), (base[0] + q[0] * 3 - d[0] * 0.01, base[1] + q[1] * 3 - d[1] * 0.01),
                        (base[0] + q[0] * 3 + d[0] * 0.01, base[1] + q[1] * 3 + d[1] * 0.01), (base[0] - q[0] * 3 + d[0] * 0.01, base[1] - q[1] * 3 + d[1] * 0.01)], _shrink(P, 0.035))
            if len(seg) >= 3: slab(seg, hl - 0.042, 0.02, 'iron', 'iron')
        # under it: a strut from low on the corner out to under its outer point, an arm back to the stone
        R0 = SA0 / math.cos(math.pi / 8); R1 = SA1 / math.cos(math.pi / 8)
        wc = Vector((CX + d[0] * (R0 - 0.05), 0, CZ + d[1] * (R0 - 0.05)))
        oc = Vector((CX + d[0] * (R1 - 0.15), hl - 0.06, CZ + d[1] * (R1 - 0.15)))
        FL.bar(K, Vector((wc.x, hl - 0.95, wc.z)), oc, 0.05, 'iron')
        FL.bar(K, Vector((wc.x, hl - 0.07, wc.z)), oc, 0.045, 'iron', h=0.05)
        # its rail round the outer corner, balusters at the corner and between
        O = Vector((CX + d[0] * (R1 + 0.07 / math.cos(math.pi / 8)), 0, CZ + d[1] * (R1 + 0.07 / math.cos(math.pi / 8))))
        e1, e2 = sat(k, SA1 + 0.07, SL, 0), sat(k + 1, SA1 + 0.07, -SL, 0)
        for (a, b) in ((e1, O), (O, e2)):
            for (yy, w, hh) in ((1.02, 0.06, 0.05), (0.52, 0.03, None)):
                FL.bar(K, Vector((a.x, hl + yy, a.z)), Vector((b.x, hl + yy, b.z)), w, 'iron', h=hh)
            for t in (0.5,):
                m = a.lerp(b, t); FL.bar(K, Vector((m.x, hl + 0.07, m.z)), Vector((m.x, hl + 1.0, m.z)), 0.03, 'iron')
            FL.bar(K, Vector((a.x, hl - 0.075, a.z)), Vector((b.x, hl - 0.075, b.z)), 0.04, 'iron', h=0.12)  # (the landing's edge plate)
        FL.bar(K, Vector((O.x, hl - 0.15, O.z)), Vector((O.x, hl + 1.06, O.z)), 0.05, 'iron')  # (the corner post)


def _shrink(P, m):
    """a convex polygon's half-planes pulled in m: (a, b, c) with a*x + b*z <= c"""
    cx = sum(p[0] for p in P) / len(P); cz = sum(p[1] for p in P) / len(P); out = []
    for i in range(len(P)):
        (ax, az), (bx, bz) = P[i], P[(i + 1) % len(P)]
        nx, nz = bz - az, -(bx - ax); l = math.hypot(nx, nz)
        if l < 1e-6: continue
        nx, nz = nx / l, nz / l
        if nx * (cx - ax) + nz * (cz - az) > 0: nx, nz = -nx, -nz
        out.append((nx, nz, nx * ax + nz * az - m))
    return out


def build(kind):
    global K
    K = Kit(os.path.join(HERE, 'boxes', kind + '.json'), seed=3)
    K.ground = 0.0
    for b in K.boxes: b['_done'] = True
    K.solids = [(b['min'], b['max']) for b in K.boxes if not (b['mat'] == 'metal' and b['min'][1] < 17.59)]  # (the stair's steps and posts: not solid stone for the AO)
    # ---- the plinth: flared stone; the tower: bands, string courses, a cornice, its top
    P0, P1, P2 = octo(X0, Z0, X1, Z1, 1.62, 0.0, 0.55), octo(X0, Z0, X1, Z1, 1.62, 0.9, 0.2), octo(X0, Z0, X1, Z1, 1.62, 1.2, 0.2)
    band(P0, P1, 'plinth'); band(P1, P2, 'plinth'); cap(P2, 'plinth')
    ys = [1.2, 4.5, 9.0, 13.5, TOP - 0.3]
    for k in range(4): band(ring(ys[k]), ring(ys[k + 1]), 'lhred' if k % 2 else 'lhwhite', sub=1.2)
    for y in (4.5, 9.0, 13.5):  # string courses: proud rings where the colours change
        band(ring(y - 0.09, 0.11), ring(y + 0.09, 0.11), 'course', sub=None); cap(ring(y + 0.09, 0.11), 'course'); cap(ring(y - 0.09, 0.11), 'course', up=False)
    top = TOP - (0.02 if kind == 'lighthouse' else 0.0)
    band(ring(TOP - 0.3, 0.2), ring(top, 0.2), 'course', sub=None); cap(ring(TOP - 0.3, 0.2), 'course', up=False)
    if kind == 'lighthouse_sd': cap(ring(TOP + 0.005, 0.2), 'tread')
    else: cap(ring(18.005, 0.0), 'tread')  # (level with the gallery's floor round it)
    # windows climbing round with the stair: one on each face at head height as the stair goes past (ring faces: 0 north,
    # then round by east; the stair climbs south-west, south, south-east, east, north-east, north, north-west), the door
    # at the foot of the north face
    if kind == 'lighthouse':
        for (face, k) in ((5, 0), (4, 1), (3, 2), (2, 3), (1, 4), (0, 5), (7, 6)):
            window(face, (10 * k + 5) * SR + 1.55)
    else:
        for (face, y) in ((1, 2.8), (2, 5.4), (3, 7.8), (4, 10.4), (5, 12.0), (6, 14.6), (7, 11.2), (0, 15.4), (2, 15.8), (4, 3.2), (6, 6.6)):
            window(face, y)
    face_out([Vector((81.3, 1.2, Z0 - 0.06)), Vector((82.7, 1.2, Z0 - 0.06)), Vector((82.7, 3.4, Z0 - 0.06)), Vector((81.3, 3.4, Z0 - 0.06))], 'door')
    for (a, b, y0, y1) in ((81.1, 81.3, 1.2, 3.4), (82.7, 82.9, 1.2, 3.4), (81.1, 82.9, 3.4, 3.6)): FL.obox(K, (a, y0, Z0 - 0.2), (b, y1, Z0 - 0.031), 'frame')
    FL.tube(K, (82.5, 2.3, Z0 - 0.06), (82.5, 2.3, Z0 - 0.15), 0.05, 0.05, 'brass', n=6)
    FL.obox(K, (80.9, 0.0, Z0 - 1.5), (83.1, 0.4, Z0 - 0.9), 'plinth'); FL.obox(K, (80.92, 0.0, Z0 - 0.9), (83.08, 0.8, Z0 - 0.5), 'plinth')  # two stone steps up to it

    # ---- the lantern room: a low wall, glowing panes behind diamond glazing bars, mullions; the dome; the vent ball
    LC = 1.172
    band(octo(80, -8, 84, -4, LC, TOP, 0.04), octo(80, -8, 84, -4, LC, TOP + 0.84, 0.04), 'lhwhite')
    band(octo(80, -8, 84, -4, LC, TOP + 0.84, 0.12), octo(80, -8, 84, -4, LC, TOP + 0.9, 0.12), 'iron', sub=None)
    cap(octo(80, -8, 84, -4, LC, TOP + 0.84, 0.12), 'iron', up=False)
    G0, G1 = octo(80, -8, 84, -4, LC, TOP + 0.9, 0.0), octo(80, -8, 84, -4, LC, 20.86, 0.0)
    band(G0, G1, 'lamp', sub=None)
    for i in range(8):
        a0, a1, b0, b1 = G0[i], G0[(i + 1) % 8], G1[i], G1[(i + 1) % 8]
        a0, a1, b0, b1 = a0 + Vector((0, 0.02, 0)), a1 + Vector((0, 0.02, 0)), b0 - Vector((0, 0.02, 0)), b1 - Vector((0, 0.02, 0))  # (their ends tucked into the ledge and the head)
        out = Vector(((a0.x + a1.x) / 2 - CX, 0, (a0.z + a1.z) / 2 - CZ)).normalized() * 0.04
        FL.bar(K, a0 + out, b0 + out, 0.1, 'iron')  # the mullion at each corner
        for k in range(3):  # the diamond lattice: bars up across each pane both ways
            t0, t1 = k / 3, (k + 1) / 3
            FL.bar(K, a0.lerp(a1, t0) + out, b0.lerp(b1, t1) + out, 0.03, 'iron')
            FL.bar(K, a0.lerp(a1, t1) + out * 1.4, b0.lerp(b1, t0) + out * 1.4, 0.03, 'iron')
    band(octo(80, -8, 84, -4, LC, 20.86, 0.1), octo(80, -8, 84, -4, LC, 21.0, 0.1), 'iron', sub=None)
    cap(octo(80, -8, 84, -4, LC, 20.86, 0.1), 'iron', up=False)
    # the dome: from a rim over the roof's boxes up in a curve to a small cap
    prev = None
    for k in range(8):
        t = k / 7; y = 21.0 + 1.22 * math.sin(t * math.pi / 2); h = 2.44 * (1 - t ** 1.8) + 0.3 * t ** 1.8
        Rg = octo(CX - h, CZ - h, CX + h, CZ + h, h * 0.586, y)
        if prev: band(prev, Rg, 'roof', sub=None)
        else: cap(Rg, 'roof', up=False)
        prev = Rg
    cap(prev, 'roof')
    FL.tube(K, (CX, 22.2, CZ), (CX, 22.3, CZ), 0.14, 0.14, 'iron', n=8)
    vb = [[Vector((CX + 0.3 * math.cos(la) * math.cos(lo), 22.56 + 0.3 * math.sin(la), CZ + 0.3 * math.cos(la) * math.sin(lo))) for lo in [2 * math.pi * i / 10 for i in range(10)]] for la in [-math.pi / 2 + math.pi * j / 6 for j in range(7)]]
    for j in range(6):
        for i in range(10):
            a, b, c, d = vb[j][i], vb[j][(i + 1) % 10], vb[j + 1][(i + 1) % 10], vb[j + 1][i]
            vc = Vector((CX, 22.56, CZ))
            if j == 0: face_out([a, c, d], 'iron', centre=vc)
            elif j == 5: face_out([a, b, d], 'iron', centre=vc)
            else: face_out([a, b, c, d], 'iron', centre=vc)
    FL.tube(K, (CX, 22.84, CZ), (CX, 24.3, CZ), 0.04, 0.0, 'brass', n=6)

    if kind == 'lighthouse':
        stair(K.rng)
        # ---- the gallery: an octagonal chequer floor round the top (open over the stair), its edge, its brackets
        GO = [(p.x, p.z) for p in octo(76, -12, 88, 0, 3.515, 0)]
        tower = [(p.x, p.z) for p in octo(X0, Z0, X1, Z1, taper(TOP), 0)]
        HX0, HZ0, HX1, HZ1 = 76.0, -8.75, 79.0, -4.757  # the stairwell (shared/map.js LH.hole)
        for (y, up) in ((18.005, True), (17.6, False)):
            for part in ([(1, 0, HX0)], [(-1, 0, -HX1)], [(0, 1, HZ0), (-1, 0, -HX0), (1, 0, HX1)], [(0, -1, -HZ1), (-1, 0, -HX0), (1, 0, HX1)]):
                Pp = clip(GO, part)
                if len(Pp) < 3: continue
                poly_fill(Pp, [tower] if any(inside(t, Pp) for t in tower) else [], y, 'tread' if up else 'iron', up=up)
        band(octo(76, -12, 88, 0, 3.515, 17.6), octo(76, -12, 88, 0, 3.515, 18.005), 'iron', sub=None)
        FL.obox(K, (76.005, 17.6, -8.485), (76.12, 18.0, HZ1), 'iron')  # (the beam along the stairwell's outer side, under the railing)
        for (z, s) in ((HZ0, 1), (HZ1, -1)):  # the stairwell's edges
            x0 = 76.0 + max(0.0, (-8.485 - z)) if z < -8.485 else 76.12
            q = [Vector((x0, 17.6, z)), Vector((HX1, 17.6, z)), Vector((HX1, 18.0, z)), Vector((x0, 18.0, z))]
            K.quad(q if (q[1] - q[0]).cross(q[3] - q[0]).z * s > 0 else q[::-1], 'iron')
        for (a, b) in (((76.3, HZ0 - 0.05), (HX1, HZ0 - 0.05)), ((76.15, HZ1 + 0.05), (77.0, HZ1 + 0.05))):  # its rails (the way off the stair: the south end, by the wall)
            A, Bv = Vector((a[0], 18.0, a[1])), Vector((b[0], 18.0, b[1])); n = max(1, round((Bv - A).length / 0.32))
            for k in range(n + 1): pp = A.lerp(Bv, k / n); FL.bar(K, pp + Vector((0, 0.03, 0)), pp + Vector((0, 0.97, 0)), 0.04, 'iron')
            FL.bar(K, A + Vector((0, 1.0, 0)), Bv + Vector((0, 1.0, 0)), 0.08, 'iron', h=0.05); FL.bar(K, A + Vector((0, 0.5, 0)), Bv + Vector((0, 0.5, 0)), 0.035, 'iron')
        TR = ring(15.0, 0.0)
        for i in range(8):  # brackets: a long strut from each tower corner and face out to under the gallery's edge
            for t in (0.0, 0.5):
                a = TR[i].lerp(TR[(i + 1) % 8], t)
                if a.x < CX - 0.5 and a.z < CZ + 1.3: continue  # (the west and north-west faces: the stair's last flights run up them)
                d = Vector((a.x - CX, 0, a.z - CZ)).normalized(); e = a + d * 2.6; e.y = 17.58
                FL.bar(K, a, e, 0.12, 'iron'); FL.bar(K, Vector((a.x, 17.48, a.z)), Vector((e.x, 17.48, e.z)), 0.1, 'iron')
        # the railing: balusters all round (where the corners' close-set posts are), top and middle rails, a kick plate
        GP = octo(76, -12, 88, 0, 3.515, 18.0, -0.09)
        for i in range(8):
            a, b = GP[i], GP[(i + 1) % 8]; n = max(1, round((b - a).length / 0.32))
            for k in range(n): p = a.lerp(b, k / n); FL.bar(K, p + Vector((0, 0.13, 0)), p + Vector((0, 0.97, 0)), 0.04, 'iron')
            FL.bar(K, a + Vector((0, 1.0, 0)), b + Vector((0, 1.0, 0)), 0.08, 'iron', h=0.05)
            FL.bar(K, a + Vector((0, 0.5, 0)), b + Vector((0, 0.5, 0)), 0.035, 'iron')
            FL.bar(K, a + Vector((0, 0.07, 0)), b + Vector((0, 0.07, 0)), 0.025, 'iron', h=0.13)
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in ('lighthouse', 'lighthouse_sd')] or ['lighthouse', 'lighthouse_sd']):
    build(kind)
