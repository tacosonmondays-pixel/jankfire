# Lasso + its Garden Hose skin: the coil you hold (lasso_model.js coilGroup + buildLassoModel). The loop hanging beside
# it (ring at x 0.075, centre y -0.27, z -0.06, r 0.12, its honda at (0.075, -0.15, -0.06)) and the spoke up to the fist
# stay code (simulated rope), so everything here stays left of x ~0.045 below the fist.
# Lasso: a ranch lariat, three-strand laid rope (32 mm here, the code's size: real ones are 3/8in, so ~x3), one rope
# wound into four teardrop loops that hang from the fist at the origin (a flattened helix: each turn one rope-width
# over, the step hidden in the hand), bunched at the top and fanned out at the bottom, each a bit different. In front of
# the hand a leather coil keeper with a brass snap; behind it the tail wraps round the bundle and hangs down the left
# side with an overhand knot, a red whipping and a frayed end. The gag: a manila price tag on the tail: 100% ROPE
# (on the back: MAY CONTAIN COW).
# Garden Hose: a 5/8in garden hose (x2, like the code's), green PVC with ribs and a yellow tracer, three stiffer round
# loops, duct tape either side of the hand, the tap end hanging out of the bundle on a crimped ferrule with a knurled
# brass swivel nut and its black washer. The gag: the store's cardboard sleeve is still on it: GARDEN HOSE 50 FT,
# LASSO USE VOIDS WARRANTY. (Its brass nozzle is the code honda on the hanging loop.)
# Wrap zones: rope / hose A, keeper / whipping / tape / coupling B, tag / sleeve N.
# run: blender -b --python tools/blender/make_lasso.py   (-- --no-sheet, -- --qa = the blender-asset-qa gate)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
V3 = Vector
FONT.setdefault('%', ['11001', '11010', '00010', '00100', '01000', '01011', '10011'])


# ------------------------------------------------------------ curves
def catmull(cp, closed=True, n=10):
    """centripetal catmull-rom through 3d control points -> dense polyline"""
    P = [V3(p) for p in cp]
    if closed: P = [P[-1]] + P + [P[0], P[1]]
    else: P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        def tj(ti, a, b): return ti + max(1e-6, (b - a).length) ** 0.5
        t0 = 0.0; t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3)
        for k in range(n):
            t = t1 + (t2 - t1) * k / n
            a1 = p0 * ((t1 - t) / (t1 - t0)) + p1 * ((t - t0) / (t1 - t0))
            a2 = p1 * ((t2 - t) / (t2 - t1)) + p2 * ((t - t1) / (t2 - t1))
            a3 = p2 * ((t3 - t) / (t3 - t2)) + p3 * ((t - t2) / (t3 - t2))
            b1 = a1 * ((t2 - t) / (t2 - t0)) + a2 * ((t - t0) / (t2 - t0))
            b2 = a2 * ((t3 - t) / (t3 - t1)) + a3 * ((t - t1) / (t3 - t1))
            out.append(b1 * ((t2 - t) / (t2 - t1)) + b2 * ((t - t1) / (t2 - t1)))
    if not closed: out.append(V3(cp[-1]))
    return out


def resample(pts, step):
    S = [0.0]
    for a, b in zip(pts, pts[1:]): S.append(S[-1] + (b - a).length)
    n = max(2, int(round(S[-1] / step)) + 1)
    out, j = [], 0
    for i in range(n):
        s = S[-1] * i / (n - 1)
        while j < len(S) - 2 and S[j + 1] < s: j += 1
        f = (s - S[j]) / max(1e-9, S[j + 1] - S[j])
        out.append(pts[j].lerp(pts[j + 1], min(1.0, max(0.0, f))))
    return out


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------ the coil
def loop_shape(A, H, g):
    """one hanging loop in its own plane: (y, z) control points from the top middle, heading back (+z) along the
    gathered top, down the back, round the bottom, up the front"""
    return [(0, 0), (0, g * 0.5), (0, g), (-0.1 * H, 0.85 * A), (-0.28 * H, 1.0 * A), (-0.5 * H, 1.04 * A), (-0.72 * H, 0.92 * A), (-0.9 * H, 0.56 * A),
            (-H, 0), (-0.9 * H, -0.56 * A), (-0.72 * H, -0.92 * A), (-0.5 * H, -1.04 * A), (-0.28 * H, -1.0 * A), (-0.1 * H, -0.85 * A), (0, -g), (0, -g * 0.5)]


def coil_path(n, x0, dx, A, H, g, fan, tilt, wob, step, seed):
    """n loops of one rope from the +x side of the bundle to the -x side: returns points + the loop index at each"""
    rng = random.Random(seed)
    out = []
    for k in range(n):
        Ak = A * (1 + 0.06 * math.sin(2.4 * k + 0.7)); Hk = H * (1 + 0.05 * math.sin(1.7 * k + 0.3))
        shp = catmull([V3((0, y, z)) for y, z in loop_shape(Ak, Hk, g)], True, 12)
        shp.append(shp[0].copy())
        dense = resample(shp, step * 0.5)
        S = [0.0]
        for a, b in zip(dense, dense[1:]): S.append(S[-1] + (b - a).length)
        ph = rng.uniform(0, 6.28)
        phi, psi = fan[k], tilt[k]
        for i, p in enumerate(dense[:-1] if k < n - 1 else dense):
            f = S[i] / S[-1]
            xk = x0 - dx * (k + smoothstep(0.955, 1.0, f))  # the step to the next turn: in the hand
            w = smoothstep(0.03, 0.2, f) * smoothstep(0.97, 0.8, f)  # splay below the hand only
            y, z = p.y, p.z
            x = xk + wob * math.sin(4 * math.pi * f + ph) * (-y / Hk)
            # swing the loop's bottom sideways (about z) and front/back (about x), round the top of the loop
            a = phi * w
            x, y = xk + (x - xk) * math.cos(a) - y * math.sin(a), (x - xk) * math.sin(a) + y * math.cos(a)
            b = psi * w
            y, z = y * math.cos(b) - z * math.sin(b), y * math.sin(b) + z * math.cos(b)
            out.append(V3((x, y, z)))
    return out


# ------------------------------------------------------------ meshes
def rope_mesh(name, pts, r, m, sides=9, prof=None, lay=None, uv_len=0.064, caps=(True, True), radius=None, seam_up=(0, 1, 0), closed=False):
    """a tube along game points with parallel-transport frames. prof = radius per side (repeats: a 3-strand lay),
    lay = twist length (the section turns with the strands), uv u along (per uv_len metres), v round (follows the
    strands). radius(i, t) scales the section per ring. caps: triangle fans."""
    if closed:  # a ring: the last point repeats the first; tangents wrap, the last ring joins the first
        pts = pts[:-1] if (pts[-1] - pts[0]).length < 1e-9 else pts
        caps = (False, False)
    n = len(pts)
    S = [0.0]
    for a, b in zip(pts, pts[1:]): S.append(S[-1] + (b - a).length)
    if closed: T = [(pts[(i + 1) % n] - pts[i - 1]).normalized() for i in range(n)]
    else: T = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    up = V3(seam_up)
    if abs(T[0].dot(up)) > 0.9: up = V3((1, 0, 0))
    N = (up - T[0] * T[0].dot(up)).normalized()
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for i in range(n):
        N = (N - T[i] * T[i].dot(N)).normalized()
        B = T[i].cross(N)
        psi = 2 * math.pi * S[i] / lay if lay else 0.0
        k_r = radius(i, S[i] / S[-1]) if radius else 1.0
        ring = []
        for k in range(sides):
            a = psi + 2 * math.pi * k / sides
            rr = r * k_r * (prof[k % len(prof)] if prof else 1.0)
            ring.append(bm.verts.new(gv(*(pts[i] + (N * math.cos(a) + B * math.sin(a)) * rr))))
        rings.append(ring)
    for i in range(n - 1):
        for k in range(sides):
            kk = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[i][kk], rings[i + 1][kk], rings[i + 1][k]))
            uv = [(S[i] / uv_len, k / sides), (S[i] / uv_len, (k + 1) / sides), (S[i + 1] / uv_len, (k + 1) / sides), (S[i + 1] / uv_len, k / sides)]
            for lp, q in zip(f.loops, uv): lp[uvl].uv = q
    if closed:  # the twist made a whole number of strand turns (lay chosen so): ring 0 is the next one, shifted
        Lc = S[-1] + (pts[0] - pts[-1]).length
        shift = int(round((2 * math.pi * Lc / lay if lay else 0.0) / (2 * math.pi / sides))) % sides
        for k in range(sides):
            kk = (k + 1) % sides
            f = bm.faces.new((rings[-1][k], rings[-1][kk], rings[0][(kk - shift) % sides], rings[0][(k - shift) % sides]))
            uv = [(S[-1] / uv_len, k / sides), (S[-1] / uv_len, (k + 1) / sides), (Lc / uv_len, (k + 1) / sides), (Lc / uv_len, k / sides)]
            for lp, q in zip(f.loops, uv): lp[uvl].uv = q
    for end, i in ((0, 0), (1, n - 1)):
        if not caps[end]: continue
        c = bm.verts.new(gv(*pts[i]))
        ring = rings[i]
        for k in range(sides):
            kk = (k + 1) % sides
            f = bm.faces.new((ring[kk], ring[k], c) if end == 0 else (ring[k], ring[kk], c))
            for lp in f.loops:
                if lp.vert is c: lp[uvl].uv = (S[i] / uv_len, 0.5)
                else:
                    a = 2 * math.pi * ring.index(lp.vert) / sides
                    lp[uvl].uv = (S[i] / uv_len + 0.02 * math.cos(a), 0.5 + 0.3 * math.sin(a))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 80)
    return o


def stadium_pts(cx, cy, hw, hh, n=24, a0=0.0):
    """a stadium (rounded-end oval) round (cx, cy) in the XY plane: hw half width, hh half height (= end radius),
    starting at angle a0 (0 = the +x end), going counter-clockwise as seen from +z"""
    L = max(0.0, hw - hh)
    per = 4 * L + 2 * math.pi * hh
    out = []
    for i in range(n):
        s = (per * i / n + a0 / (2 * math.pi) * per) % per
        # +x end semicircle, top straight (toward -x), -x end, bottom straight
        if s < math.pi * hh:  # +x end: from (cx+L, cy-hh)... measured from the rightmost point upward
            a = s / hh - math.pi / 2
            if a < 0: a += 0
        segs = [(math.pi * hh / 2, 'r1'), (2 * L, 't'), (math.pi * hh, 'l'), (2 * L, 'b'), (math.pi * hh / 2, 'r2')]
        acc, x, y = 0.0, 0, 0
        for ln, kind in segs:
            if s <= acc + ln + 1e-12:
                u = s - acc
                if kind == 'r1': a = u / hh; x, y = cx + L + hh * math.cos(a), cy + hh * math.sin(a)
                elif kind == 't': x, y = cx + L - u, cy + hh
                elif kind == 'l': a = math.pi / 2 + u / hh; x, y = cx - L + hh * math.cos(a), cy + hh * math.sin(a)
                elif kind == 'b': x, y = cx - L + u, cy - hh
                else: a = -math.pi / 2 + u / hh; x, y = cx + L + hh * math.cos(a), cy + hh * math.sin(a)
                break
            acc += ln
        out.append((x, y))
    return out


def band(name, m, cx, cy, hw, hh, z0, z1, thick, n=32, uv_u=1.0, uv_face=None):
    """a strap round a bundle: stadium section (inner hw x hh), from z0 to z1, `thick` thick. uvs: u round it
    (uv_u repeats), v across. uv_face(x, y, z, normal) can override a face's uvs (a printed front)"""
    inner = stadium_pts(cx, cy, hw, hh, n)
    outer = stadium_pts(cx, cy, hw + thick, hh + thick, n)
    rings = [[(x, y, z1 + 0.0004) for x, y in inner], [(x, y, z1) for x, y in outer], [(x, y, z0) for x, y in outer], [(x, y, z0 - 0.0004) for x, y in inner]]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vs = [[bm.verts.new(gv(*p)) for p in r] for r in rings]
    for j in range(n):
        jj = (j + 1) % n
        for k in range(4):
            kk = (k + 1) % 4
            f = bm.faces.new((vs[k][j], vs[k][jj], vs[kk][jj], vs[kk][j]))
            uv = [(j / n * uv_u, k / 4), ((j + 1) / n * uv_u, k / 4), ((j + 1) / n * uv_u, (k + 1) / 4), (j / n * uv_u, (k + 1) / 4)]
            for lp, q in zip(f.loops, uv): lp[uvl].uv = q
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 40)
    return o


def weld(o, dist=1e-6):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    return o


def uv_unzero(o, eps=2e-3):
    me = o.data
    if not me.uv_layers: return o
    uv = me.uv_layers.active.data
    for p in me.polygons:
        pts = [uv[li].uv.copy() for li in p.loop_indices]
        a2 = sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
        if abs(a2) < 1e-9:
            for k, li in enumerate(p.loop_indices):
                a = 2 * math.pi * k / len(pts)
                uv[li].uv = (pts[0].x + eps * math.cos(a), pts[0].y + eps * math.sin(a))
    return o


def card(name, m_front, m_back, centre, w, h, t, right, up, clip=0.18, hole=None):
    """a flat tag: rectangle w x h with the two top corners clipped, t thick, facing right x up; uvs 0..1 on both faces
    (each reads the right way round from its own side)"""
    c, R, U = V3(centre), V3(right).normalized(), V3(up).normalized()
    Nn = R.cross(U)
    cl = clip * min(w, h)
    out2 = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2 - cl), (w / 2 - cl, h / 2), (-w / 2 + cl, h / 2), (-w / 2, h / 2 - cl)]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    fv = [bm.verts.new(gv(*(c + R * a + U * b + Nn * t / 2))) for a, b in out2]
    bv = [bm.verts.new(gv(*(c + R * a + U * b - Nn * t / 2))) for a, b in out2]
    ff = bm.faces.new(fv); fb = bm.faces.new(bv[::-1])
    for lp in ff.loops:
        i = fv.index(lp.vert); a, b = out2[i]; lp[uvl].uv = (a / w + 0.5, b / h + 0.5)
    for lp in fb.loops:
        i = bv.index(lp.vert); a, b = out2[i]; lp[uvl].uv = (-a / w + 0.5, b / h + 0.5)
    k = len(out2)
    for i in range(k):
        j = (i + 1) % k
        f = bm.faces.new((fv[i], bv[i], bv[j], fv[j]))
        for lp in f.loops: lp[uvl].uv = (0.02 + 0.01 * (lp.vert in bv), 0.02 + 0.01 * (lp.vert in (fv[j], bv[j])))
    bmesh.ops.triangulate(bm, faces=[ff, fb])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m_front)
    o.data.materials.append(m_back)
    # faces looking along -Nn are the back
    for p in o.data.polygons:
        n = V3((p.normal.x, p.normal.z, -p.normal.y))
        if n.dot(Nn) < -0.5: p.material_index = 1
    return o


# ------------------------------------------------------------ textures
def rope_px(px):
    """3-strand manila: 9 sides x 4 px round (v), each strand: crown, shoulders; the groove face dark; fibres along u"""
    h, w = px.shape[:2]
    r = np.random.default_rng(5)
    base, light, dark, groove = hexrgb(0xc69c62), hexrgb(0xd8b882), hexrgb(0x8a5e30), hexrgb(0x5a3c1e)
    for y in range(h):
        side = y // 4; sub = y % 4
        kind = side % 3  # 0 crown->shoulder, 1 the groove (between two strands), 2 shoulder->crown
        if kind == 1: c = groove if sub in (1, 2) else dark
        elif kind == 0: c = light if sub == 0 else base
        else: c = light if sub == 3 else base
        px[y, :] = c
    px[:] *= (0.92 + 0.12 * r.random((h, w, 1)))
    for k in range(46):  # fibre streaks along the strands, a few pale hairy ones
        y = int(r.integers(0, h)); x0 = int(r.integers(0, w)); L = int(r.integers(3, 9))
        if (y // 4) % 3 == 1: continue
        col = hexrgb(0xa8783a) if k % 4 else hexrgb(0xecd49c)
        for x in range(x0, x0 + L): px[y, x % w] = col
    return px


def hose_px(px):
    """green PVC hose: fine ribs round it, a yellow tracer stripe, faint printed dashes"""
    h, w = px.shape[:2]
    r = np.random.default_rng(6)
    px[:] = hexrgb(0x23893a)
    px[:] *= (0.95 + 0.07 * r.random((h, w, 1)))
    for x in range(0, w, 4): px[:, x] = hexrgb(0x17642a)
    px[0:1, :] = hexrgb(0xf2c21e); px[0:1, ::4] = hexrgb(0xc8961a)  # a thin tracer stripe
    for x0 in range(4, w, 32): px[11:12, x0:x0 + 9] = hexrgb(0xa8d8b0)
    return px


def leather_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(7)
    lo = np.kron(r.random((h // 2 + 1, w // 4 + 1)), np.ones((2, 4)))[:h, :w]
    px[:] = hexrgb(0x6a3418)[None, None] * (0.85 + 0.25 * lo[:, :, None])
    px[2, ::3] = hexrgb(0xf0d8a0); px[h - 3, 1::3] = hexrgb(0xf0d8a0)  # stitching along both edges
    px[0, :] = px[-1, :] = hexrgb(0x4a2410)
    return px


def whip_px(px):
    h, w = px.shape[:2]
    for x in range(w): px[:, x] = hexrgb(0xe0302a) if x % 2 == 0 else hexrgb(0xa81a18)
    return px


def tag_front_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(8)
    px[:] = hexrgb(0xe8cf98) * (0.95 + 0.06 * r.random((h, w, 1)))
    text_px(px, '100%', 10, 7, 2, 0x2a1a10)
    text_px(px, 'ROPE', 10, 25, 2, 0xc8202a)
    px[1, :] = px[-2, :] = hexrgb(0xb8995c)


def tag_back_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(9)
    px[:] = hexrgb(0xe8cf98) * (0.95 + 0.06 * r.random((h, w, 1)))
    text_px(px, 'MAY', 6, 9, 1, 0x2a1a10)
    text_px(px, 'CONTAIN', 6, 18, 1, 0x2a1a10)
    text_px(px, 'COW', 6, 27, 1, 0x2a1a10)
    px[1, :] = px[-2, :] = hexrgb(0xb8995c)


def sleeve_px(px):
    """the store's cardboard sleeve: GARDEN HOSE / 50 FT / LASSO USE VOIDS WARRANTY"""
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffb81a)
    px[:7, :] = hexrgb(0x1e6a2c)
    text_px(px, 'GARDEN HOSE', (w - 66) // 2, 0, 1, 0xffffff)
    for dx in (0, 1): text_px(px, '50 FT', (w - 60) // 2 + dx, 10, 2, 0x1a1a1a)
    text_px(px, 'LASSO USE', (w - 54) // 2, 28, 1, 0xc8202a)
    text_px(px, 'VOIDS WARRANTY', (w - 84) // 2, 37, 1, 0xc8202a)
    px[-2:, :] = hexrgb(0x1e6a2c)


# ------------------------------------------------------------ the stopper knot
def knot_turn(name, m, centre, axis, r, tilt=0.6, spin=0.0):
    """the wrapping turn of a pulled-tight overhand knot: a rope ring round the swollen tail, tilted across it"""
    ax = V3(axis).normalized()
    side = ax.cross(V3((0, 0, 1)) if abs(ax.z) < 0.9 else V3((1, 0, 0))).normalized()
    up = side.cross(ax)
    q = Matrix.Rotation(tilt, 3, side) @ Matrix.Rotation(spin, 3, ax)
    pts = []
    R = 1.62 * r
    for i in range(29):
        a = 2 * math.pi * i / 28
        p = side * math.cos(a) * R + up * math.sin(a) * R
        pts.append(V3(centre) + q @ p)
    L = sum((b - a).length for a, b in zip(pts, pts[1:]))
    lay = 3 * L / max(1, round(3 * L / 0.11))  # the strands come round to meet themselves
    return rope_mesh(name, pts, r * 0.96, m, sides=9, prof=[1.0, 0.87, 0.87], lay=lay, uv_len=0.064, closed=True)


# ------------------------------------------------------------ the brass coupling (hose tap end)
def coupling(prefix, m_brass, m_washer, m_ferrule, base, d, r_hose):
    """female hose coupling at `base` pointing along d: crimped ferrule over the hose end, knurled swivel nut with an
    open threaded bore, the black washer at its bottom"""
    d = V3(d).normalized()
    fr = r_hose * 1.16
    nr = r_hose * 1.5
    prof = [(r_hose * 0.95, 0.0), (fr, -0.002), (fr, -0.012), (fr * 0.92, -0.015), (fr, -0.018), (fr, -0.028), (fr * 0.92, -0.031), (fr, -0.034), (fr, -0.046), (fr * 1.04, -0.05)]
    parts = [(lathe(prof, (0, 0, 0), m_ferrule, seg=16, axis='z', name=prefix + 'ferrule', cap=False), 0.0),
             (lathe([(fr * 1.03, 0.0), (nr * 0.98, 0.0), (nr * 0.98, -0.0041), (fr * 1.03, -0.0041)], (0, 0, 0), m_brass, seg=20, axis='z', name=prefix + 'nutback'), 0.0465),
             (knurl(prefix + 'nut', m_brass, nr, 0.036, ridges=22, bore=nr * 0.8, depth=0.024), 0.05),
             (lathe([(0.0, 0.0), (nr * 0.8, 0.0), (nr * 0.8, -0.0012), (0.0, -0.0012)], (0, 0, 0), m_washer, seg=20, axis='z', name=prefix + 'washer'), 0.0612)]
    out = []
    q = V3((0, 0, -1)).rotation_difference(d)
    for o, along in parts:
        apply_mods(o)
        o.data.transform(_game_rot(q))
        o.data.transform(Matrix.Translation(gv(*(V3(base) + d * along))))
        out.append(o)
    return out


def _game_rot(q):
    """a rotation given in game axes, as a blender matrix (gv is a proper rotation: conjugate it)"""
    G = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))  # game -> blender
    return (G @ q.to_matrix() @ G.inverted()).to_4x4()


def knurl(name, m, r, length, ridges=20, bore=None, depth=0.0):
    """a straight-knurled nut along game -z from 0: alternating ridge / valley radii, chamfered ends; with `bore`, the
    front (-z) end is open: an annulus and a bore `depth` deep with a flat bottom"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    n = ridges * 2
    prof = [(0.0, 0.9), (-0.003, 1.0), (-length + 0.003, 1.0), (-length, 0.9)]
    rings = []
    for z, k in prof:
        rings.append([bm.verts.new(gv(math.cos(2 * math.pi * i / n) * r * k * (1.0 if i % 2 == 0 else 0.93), math.sin(2 * math.pi * i / n) * r * k * (1.0 if i % 2 == 0 else 0.93), z)) for i in range(n)])
    if bore:
        for z in (-length, -length + depth):
            rings.append([bm.verts.new(gv(math.cos(2 * math.pi * i / n) * bore, math.sin(2 * math.pi * i / n) * bore, z)) for i in range(n)])
    def quad(a, b, i, u0, u1):
        j = (i + 1) % n
        f = bm.faces.new((a[i], a[j], b[j], b[i]))
        for lp in f.loops: lp[uvl].uv = (u1 if (lp.vert in b) else u0, (i + (1 if lp.vert in (a[j], b[j]) else 0)) / n)
    for ri in range(len(rings) - 1):
        for i in range(n): quad(rings[ri], rings[ri + 1], i, ri / len(rings), (ri + 1) / len(rings))
    def fan(ring, z, flip):
        c = bm.verts.new(gv(0, 0, z))
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((ring[j], ring[i], c) if not flip else (ring[i], ring[j], c))
            for lp in f.loops:
                a = 2 * math.pi * (i if lp.vert is ring[i] else j) / n
                lp[uvl].uv = (0.5, 0.5) if lp.vert is c else (0.5 + 0.4 * math.cos(a), 0.5 + 0.4 * math.sin(a))
    fan(rings[0], 0.0, False)
    if bore: fan(rings[-1], -length + depth, True)
    else: fan(rings[3], -length, True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, 30)
    return o


# ------------------------------------------------------------ the lariat
R_ROPE = 0.016


def lariat():
    rope = mat('ls_rope', 0xffffff, rough=0.8, tex=tex_canvas('ls_rope_t', 64, 36, rope_px))
    leather = mat('ls_leather', 0xffffff, rough=0.55, clearcoat=0.3, tex=tex_canvas('ls_leather_t', 32, 12, leather_px))
    brass = mat('ls_brass', 0xe0ac3c, rough=0.22, metal=1.0)
    whip = mat('ls_whip', 0xffffff, rough=0.7, tex=tex_canvas('ls_whip_t', 16, 4, whip_px))
    string = mat('ls_string', 0xd8202a, rough=0.8)
    tagf = mat('ls_tag', 0xffffff, rough=0.85, tex=tex_canvas('ls_tag_t', 64, 40, tag_front_px))
    tagb = mat('ls_tag_back', 0xffffff, rough=0.85, tex=tex_canvas('ls_tagb_t', 64, 40, tag_back_px))
    paper = mat('ls_eyelet', 0xf4f0e0, rough=0.8)
    N_LOOPS, X0, DX = 4, 0.024, 0.033
    A, H, Gt = 0.13, 0.31, 0.08
    fan = [-0.05 - 0.035 * k for k in range(N_LOOPS)]
    tilt = [0.07 * (k - 1.5) + 0.03 * math.sin(3.1 * k) for k in range(N_LOOPS)]
    loops = coil_path(N_LOOPS, X0, DX, A, H, Gt, fan, tilt, 0.005, 0.0125, 3)
    # the tail: on out of the last turn, 1.5 turns round the bundle behind the hand, then down the left side
    x_end = X0 - DX * N_LOOPS
    xc = (X0 + x_end) / 2
    hw = (X0 - x_end) / 2 + 2 * R_ROPE + 0.0012
    hh = 2 * R_ROPE + 0.0012
    wrap = []
    pitch = 2 * R_ROPE + 0.0015
    st = stadium_pts(xc, 0.0, hw, hh, 48, a0=math.pi * 1.1)
    for i in range(49):
        x, y = st[i % 48]
        wrap.append(V3((x, y, 0.036 + pitch * i / 48)))
    lead = [V3((x_end - 0.004, -0.006, 0.012)), V3((x_end - 0.014, -0.02, 0.026))]
    hang = wrap[-1]
    XT = x_end - 0.045
    kn_c = V3((XT, -0.16, 0.1))
    tail_ctrl = [loops[-2], loops[-1]] + lead + wrap + [hang + V3((-0.008, -0.03, 0.008)), V3((XT, -0.085, 0.098)), V3((XT, -0.125, 0.1)),
                                                        kn_c, V3((XT + 0.002, -0.2, 0.101)), V3((XT + 0.003, -0.235, 0.102)), V3((XT + 0.004, -0.262, 0.103))]
    full = loops[:-1] + catmull(tail_ctrl, False, 4)[4:]
    full = resample(full, 0.0125)
    S_ = [0.0]
    for a_, b_ in zip(full, full[1:]): S_.append(S_[-1] + (b_ - a_).length)
    L = S_[-1]
    ik = min(range(len(full)), key=lambda i: (full[i] - kn_c).length)
    s_knot = S_[ik]
    def frayed(i, t):  # the knot swells the tail, the last 2 cm splays out into loose fibres
        s_ = t * L
        k = 1.0 + 0.42 * math.exp(-((s_ - s_knot) / 0.016) ** 2)
        return k if s_ < L - 0.02 else k + 0.4 * (s_ - (L - 0.02)) / 0.02
    coil = rope_mesh('ls_coil', full, R_ROPE, rope, sides=9, prof=[1.0, 0.87, 0.87], lay=0.11, uv_len=0.064, radius=frayed)
    kdir = (full[ik + 1] - full[ik - 1]).normalized()
    turn = knot_turn('ls_knot', rope, full[ik], kdir, R_ROPE * 1.08, tilt=0.62, spin=0.4)
    # whipping: red twine bound round the rope above the frayed end
    end_dir = (full[-1] - full[-4]).normalized()
    wpts = [full[-1] - end_dir * (0.022 + 0.026 * i / 6) for i in range(7)]
    whipping = rope_mesh('ls_whipping', wpts, R_ROPE * 1.09, whip, sides=12, uv_len=0.004)
    # the coil keeper in front of the hand: leather strap, brass snap on the outside
    kz0, kz1 = -0.064, -0.04
    keeper = band('ls_keeper', leather, (X0 + (X0 - DX * (N_LOOPS - 1))) / 2, 0.0, (DX * (N_LOOPS - 1)) / 2 + R_ROPE + 0.0008, R_ROPE + 0.0008, kz0, kz1, 0.0032, n=36, uv_u=3.0)
    kx = (X0 + (X0 - DX * (N_LOOPS - 1))) / 2 - ((DX * (N_LOOPS - 1)) / 2 + R_ROPE + 0.004)
    snap = lathe([(0.0, 0.0), (0.0072, 0.0), (0.0068, -0.0018), (0.0052, -0.0034), (0.0, -0.0042)], (kx, 0.0, (kz0 + kz1) / 2), brass, seg=14, axis='x', name='ls_snap')
    # the price tag on its red string, hanging off the whipping
    wc = wpts[3]
    loopc = [wc + V3((math.cos(2 * math.pi * i / 10) * R_ROPE * 1.25, 0, math.sin(2 * math.pi * i / 10) * R_ROPE * 1.25)) for i in range(10)]
    tie = tube(loopc, 0.0013, string, seg=6, name='ls_tie', closed=True)
    TR, TU = V3((-0.25, 0, 1.0)).normalized(), V3((0.08, 1, 0.12)).normalized()
    TN = TR.cross(TU)
    tag_c = wc + V3((-R_ROPE * 1.3 - 0.006, -0.046, -0.01))
    hole = tag_c + TU * (0.02 - 0.0075)
    s_pts = [wc + V3((-R_ROPE * 1.25, 0, 0)), wc + V3((-R_ROPE * 1.4, -0.012, -0.004)), hole + TU * 0.006, hole, hole - TN * 0.0016]
    strng = rope_mesh('ls_string', resample(catmull(s_pts, False, 6), 0.003), 0.0012, string, sides=6, uv_len=0.01)
    tag = card('ls_tagcard', tagf, tagb, tag_c, 0.06, 0.04, 0.0016, right=tuple(TR), up=tuple(TU))
    eye = lathe([(0.0022, 0.0), (0.0042, 0.0), (0.0042, -0.0008), (0.0022, -0.0008)], (0, 0, 0), paper, seg=12, axis='z', name='ls_eyelet')
    apply_mods(eye)
    eye.data.transform(_game_rot(V3((0, 0, -1)).rotation_difference(TN)))
    eye.data.transform(Matrix.Translation(gv(*(hole + TN * 0.0004))))
    parts = [coil, turn, whipping, keeper, snap, tie, strng, tag, eye]
    for p in parts: apply_mods(p); uv_unzero(p)
    for p in (snap, tie, eye): uv_box(p, 0.02)
    meta = {'kind': 'weapon', 'id': 'lasso', 'paint': ['ls_rope'], 'muzzle': [0.03, -0.03, -0.04], 'hatAt': [[0, 0.04, 0], 0.07]}
    return parts, meta


def lasso_file():
    parts, meta = lariat()
    if '--qa' in ARGV: qa(parts, 'lasso')
    zones = {'ls_rope': 'a', 'ls_leather': 'b', 'ls_brass': 'b', 'ls_whip': 'b', 'ls_string': 'n', 'ls_tag': 'n', 'ls_eyelet': 'n'}
    nodes = zone_join(parts, 'lasso', zones, default='a')
    print('JF_META', json.dumps(meta))
    return finish('w_lasso', nodes, meta)


# ------------------------------------------------------------ the garden hose
R_HOSE = 0.022


def garden_hose():
    hose = mat('lh_hose', 0xffffff, rough=0.45, clearcoat=0.35, tex=tex_canvas('lh_hose_t', 64, 24, hose_px))
    tape = mat('lh_tape', 0xffffff, rough=0.55, metal=0.2, tex=tex_noise('lh_tape_t', 0x8e939c, var=0.1, size=16, speck=0x6a6e76, speck_p=0.18, seed=12))
    brass = mat('lh_brass', 0xe0ac3c, rough=0.24, metal=1.0, tex=tex_noise('lh_brass_t', 0xe0ac3c, var=0.06, size=8, seed=13))
    alu = mat('lh_ferrule', 0xd8c070, rough=0.3, metal=1.0)
    washer = mat('lh_washer', 0x18181a, rough=0.7)
    card_m = mat('lh_sleeve', 0xffffff, rough=0.75, tex=tex_canvas('lh_sleeve_t', 96, 46, sleeve_px))
    card_back = mat('lh_sleeve_back', 0xffffff, rough=0.75, tex=tex_noise('lh_sleeveb_t', 0xc8a868, var=0.08, size=16, seed=14))
    N_LOOPS, X0, DX = 3, 0.012, 0.046
    A, H, Gt = 0.14, 0.30, 0.06
    fan = [-0.04 - 0.03 * k for k in range(N_LOOPS)]
    tilt = [0.06 * (k - 1) + 0.02 * math.sin(2.3 * k) for k in range(N_LOOPS)]
    loops = coil_path(N_LOOPS, X0, DX, A, H, Gt, fan, tilt, 0.003, 0.016, 5)
    x_end = X0 - DX * N_LOOPS
    # the tap end: out of the last turn under the hand, over to the left and down, the coupling pointing at the floor
    tail = [V3((x_end + 0.012, 0.0, 0.004)), V3((x_end - 0.004, -0.004, 0.016)), V3((x_end - 0.024, -0.03, 0.03)), V3((x_end - 0.034, -0.07, 0.036)), V3((x_end - 0.036, -0.1, 0.036))]
    full = loops[:-1] + catmull([loops[-2], loops[-1]] + tail, False, 10)[10:]
    full = resample(full, 0.016)
    tube_o = rope_mesh('lh_coil', full, R_HOSE, hose, sides=10, uv_len=0.064, caps=(True, False))
    d_end = (full[-1] - full[-2]).normalized()
    cp = coupling('lh_', brass, washer, alu, full[-1] - d_end * 0.044, d_end, R_HOSE)
    # duct tape either side of the hand round the three top strands
    xc = (X0 + (X0 - DX * (N_LOOPS - 1))) / 2
    thw = DX * (N_LOOPS - 1) / 2 + R_HOSE + 0.0006
    t1 = band('lh_tape1', tape, xc, 0.0, thw, R_HOSE + 0.0006, -0.06, -0.036, 0.0012, n=36, uv_u=4.0)
    t2 = band('lh_tape2', tape, xc, 0.0, thw, R_HOSE + 0.0006, 0.034, 0.056, 0.0012, n=36, uv_u=4.0)
    # the store's cardboard sleeve round the front of the three loops, halfway down
    yc = -0.15
    near = []
    for p in full:
        if abs(p.y - yc) < 0.03 and p.z < -0.05: near.append(p)
    xs = [p.x for p in near]; zs = [p.z for p in near]
    sx0, sx1 = min(xs) - R_HOSE - 0.0008, max(xs) + R_HOSE + 0.0008
    sz0, sz1 = min(zs) - R_HOSE - 0.0008, max(zs) + R_HOSE + 0.0008
    sl = sleeve_box('lh_sleeve', card_m, card_back, (sx0, sx1), (sz0, sz1), yc - 0.036, yc + 0.036, 0.0016)
    parts = [tube_o, t1, t2, sl] + cp
    for p in parts: apply_mods(p); uv_unzero(p)
    for p in cp: uv_box(p, 0.03)
    meta = {'kind': 'weapon', 'id': 'lasso', 'skin': 'lasso_hose', 'paint': ['lh_hose'], 'muzzle': [0.03, -0.03, -0.04], 'hatAt': [[0, 0.05, 0], 0.07]}
    print('JF_SLEEVE x', round(sx0, 3), round(sx1, 3), 'z', round(sz0, 3), round(sz1, 3))
    return parts, meta


def sleeve_box(name, m_front, m_back, xr, zr, y0, y1, t):
    """a cardboard band round the hoses (a rounded box tube, axis y), the print on the face toward -z (the front)"""
    x0, x1 = xr; z0, z1 = zr
    rc = min(0.01, (z1 - z0) * 0.3)
    def outline(off):
        pts = []
        cs = [(x1 - rc, z0 + rc, -90), (x1 - rc, z1 - rc, 0), (x0 + rc, z1 - rc, 90), (x0 + rc, z0 + rc, 180)]
        for cx, cz, a0 in cs:
            for i in range(4):
                a = math.radians(a0 + 90 * i / 3)
                pts.append((cx + (rc + off) * math.cos(a), cz + (rc + off) * math.sin(a)))
        return pts
    inn, out = outline(0.0), outline(t)
    n = len(inn)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = [[bm.verts.new(gv(x, y1, z)) for x, z in inn], [bm.verts.new(gv(x, y1, z)) for x, z in out], [bm.verts.new(gv(x, y0, z)) for x, z in out], [bm.verts.new(gv(x, y0, z)) for x, z in inn]]
    for j in range(n):
        jj = (j + 1) % n
        for k in range(4):
            kk = (k + 1) % 4
            f = bm.faces.new((rings[k][j], rings[k][jj], rings[kk][jj], rings[kk][j]))
            front = k == 1 and all(lp.vert.co.y > -z0 - t * 0.5 - 1e-6 for lp in f.loops)  # outer face on the -z side (blender +y)
            for lp in f.loops:
                g = V3((lp.vert.co.x, lp.vert.co.z, -lp.vert.co.y))
                if front: lp[uvl].uv = (1 - (g.x - x0) / (x1 - x0), (g.y - y0) / (y1 - y0))
                else: lp[uvl].uv = ((g.x + g.z) * 8, g.y * 8)
            f.material_index = 0 if front else 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m_front)
    o.data.materials.append(m_back)
    smooth(o, 30)
    return o


def hose_file():
    parts, meta = garden_hose()
    if '--qa' in ARGV: qa(parts, 'hose')
    zones = {'lh_hose': 'a', 'lh_tape': 'b', 'lh_brass': 'b', 'lh_ferrule': 'b', 'lh_washer': 'b', 'lh_sleeve': 'n'}
    nodes = zone_join(parts, 'hose', zones, default='b')
    print('JF_META', json.dumps(meta))
    return finish('w_lasso_hose', nodes, meta)


def qa(parts, tag):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[p.name for p in parts], profile='game', eps=0.0002, tol=0.0008)
    print('QA_PASS', tag, res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], tag, e)
    for n, m in res.get('objects', {}).items():
        bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'boundary_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts', 'islands') and v}
        print('QA_PART', tag, n, m.get('tris'), bad)


def closeups(root, tag):
    for a_ in ARGV:
        if a_.startswith('--close='):
            sys.path.insert(0, '/tmp/claude-0/-workspace-jankfire/86957797-7d93-5698-a006-852e0a15c9f9/scratchpad/agents/misc')
            import closeup
            closeup.shots(root, [('side', (-0.6, -0.15, -0.05), (-0.03, -0.15, 0.0), 45), ('front', (-0.1, -0.1, -0.6), (-0.03, -0.15, 0.0), 45),
                                 ('top', (-0.03, 0.35, 0.05), (-0.03, 0.0, 0.0), 45), ('tail', (-0.3, -0.12, 0.3), (-0.12, -0.15, 0.08), 40),
                                 ('right', (0.6, -0.15, 0.05), (-0.03, -0.15, 0.0), 45), ('hand', (-0.2, 0.12, -0.25), (-0.03, 0.0, 0.0), 40)], a_.split('=', 1)[1], tag, exposure=-0.3)


def build_all():
    out = []
    r1 = lasso_file(); closeups(r1, 'lasso'); out.append((r1, 'w_lasso'))
    r2 = hose_file(); out.append((r2, 'w_lasso_hose'))
    return out


main_multi(build_all, exposure=-0.3)
