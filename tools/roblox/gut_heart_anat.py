# THE GUT's heart, anatomical (17 Nov 2026). The owner, after the first sheet of Valentine hearts: "We can do an actual
# heart" (main session's brief: the real shape, the vessels arching out of the top, coronary veins over the surface, in
# our chunky kit style: clean modelled forms, flat deep reds and pinks, blue and purple vessels, a slow beat; no blood,
# no drips, no wet-meat texture). Follows the web model's silhouette (docs/story/gut/gut_heart_close.jpg): the
# ventricles' cone with its apex down and to one side, the atria and auricles on top, the aortic arch, the pulmonary
# trunk, the venae cavae, the coronary vessels in their grooves. Three takes:
#   chunky   the big forms and the main vessels only, thick and toy-like
#   vessels  the same with the whole coronary tree, the pulmonary veins, forked branches
#   grand    the web's silhouette: the arch and the cavae as ropes of smaller vessels, feelers curling up off the arch
# Local frame: the heart's centre at the origin, y up, its front toward +z, the apex down and toward +x.
import math, bmesh
from mathutils import Vector, Matrix
import arenakit as K
from arenakit import put, Tr
import gut_heart as G

# flat colours: the muscle in deep reds, the atria a shade darker, arteries pink-red, veins blue and violet
MUSCLE, MUSCLE2, ATRIUM = 'b8323f', 'c9434f', '9c2a3c'
AORTA, ARTERY = 'd9646f', 'e0505c'
PULM, VEIN, CAVA = '5c63c9', '4a55b8', '5a44a6'
PVEIN = 'c2485a'

TILT = math.radians(28)                     # the long axis leans this far from straight down, toward +x
AX = Vector((math.sin(TILT), -math.cos(TILT), 0))   # base -> apex
UX = Vector((math.cos(TILT), math.sin(TILT), 0))    # across, in the front plane
WZ = Vector((0, 0, 1))
L, R0, FLAT = 36.0, 14.5, 0.82              # the ventricles' length, widest radius, front-to-back flattening
BASE = -AX * (L * 0.40)                     # the middle of the ventricles' base (where the atria sit)

def prof(s):
    """the ventricles' radius along the axis (0 base .. 1 apex; below 0 the rounded top under the atria)"""
    if s < -0.15: return 0.0
    if s < 0.0: return 0.8 * math.sqrt(max(0.0, 1 - (s / 0.15) ** 2))
    if s < 0.22: return 0.8 + 0.2 * math.sin(math.pi / 2 * s / 0.22)
    return math.sqrt(max(0.0, 1 - ((s - 0.22) / 0.78) ** 2))

def surf(s, phi, lift=0.0):
    """a point on the ventricles' surface: s along the axis, phi round it (90 degrees = the front)"""
    r = R0 * prof(s) + lift
    return BASE + AX * (s * L) + UX * (math.cos(phi) * r) + WZ * (math.sin(phi) * r * FLAT)

def ventricles(m, M, col=MUSCLE):
    bm = bmesh.new()
    rings, n = [], 36
    ss = [-0.15 + 1.15 * (k / 30) ** 1.0 for k in range(31)]
    top = bm.verts.new(BASE + AX * (-0.15 * L))
    for s in ss[1:-1]:
        rings.append([bm.verts.new(surf(s, 2 * math.pi * i / n)) for i in range(n)])
    tip = bm.verts.new(BASE + AX * L)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((top, rings[0][j], rings[0][i]))
        bm.faces.new((tip, rings[-1][i], rings[-1][j]))
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    put(m, 'plastic', col, bm, M)

def ellip(m, col, M, c, r, rot=None, sub=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
    bmesh.ops.scale(bm, vec=r, verts=bm.verts)
    if rot is not None: bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
    put(m, 'plastic', col, bm, M @ Tr(c[0], c[1], c[2]))

def spline(pts, n=10):
    """Catmull-Rom through points (Vectors), n samples a span"""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out

def V(*a): return Vector(a)

def vessel(m, col, M, pts, r0, r1=None, segs=12, n=10):
    p = spline([M @ q for q in pts], n)
    r1 = r0 if r1 is None else r1
    G.tube(m, col, p, [r0 + (r1 - r0) * k / max(1, len(p) - 1) for k in range(len(p))], segs=segs)
    return p

def rope(m, col, M, pts, R, strands, rr, twist=2.5, n=10, segs=8):
    """a vessel as a rope of smaller ones twisted round its line (the web's arch)"""
    c = spline([M @ q for q in pts], n)
    N = len(c)
    T = [(c[min(i + 1, N - 1)] - c[max(i - 1, 0)]).normalized() for i in range(N)]
    up = Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else Vector((1, 0, 0))
    nrm = T[0].cross(up).normalized()
    frames = []
    for i in range(N):
        if i > 0:
            ax = T[i - 1].cross(T[i])
            if ax.length > 1e-7: nrm = Matrix.Rotation(T[i - 1].angle(T[i]), 3, ax.normalized()) @ nrm
        nrm = (nrm - T[i] * nrm.dot(T[i])).normalized()
        frames.append((nrm, T[i].cross(nrm)))
    for k in range(strands):
        pts_k = []
        for i in range(N):
            a = 2 * math.pi * k / strands + twist * 2 * math.pi * i / N
            nn, bb = frames[i]
            pts_k.append(c[i] + (nn * math.cos(a) + bb * math.sin(a)) * R)
        G.tube(m, col, pts_k, rr, segs=segs)

def on_surface(m, col, M, path, r, lift=None, n=6, segs=8):
    """a coronary vessel lying on the ventricles: path = [(s, phi degrees), ...]"""
    lift = r * 0.55 if lift is None else lift
    pts = [surf(s, math.radians(ph), lift) for (s, ph) in path]
    p = spline([M @ q for q in pts], n)
    G.tube(m, col, p, [r * (1 - 0.45 * k / max(1, len(p) - 1)) for k in range(len(p))], segs=segs)

def anat_heart(m, style, M):
    """the anatomical heart in one of three takes, placed by M"""
    ventricles(m, M)
    # a soft groove between the ventricles, front and back (a slightly darker band, lying on the surface)
    for ph in (78.0, 262.0):
        on_surface(m, MUSCLE2 if style == 'chunky' else ATRIUM, M, [(0.02, ph - 6), (0.3, ph), (0.6, ph + 6), (0.92, ph + 14)], 0.9, lift=0.05, segs=6)
    # the atria and their auricles
    ellip(m, ATRIUM, M, (-9.5, 12.5, -1.5), (9.5, 7.8, 8.5))
    ellip(m, ATRIUM, M, (5.0, 13.5, -6.5), (8.5, 6.8, 7.5))
    ellip(m, MUSCLE2, M, (-11.0, 9.0, 6.5), (4.8, 2.6, 3.6), Matrix.Rotation(math.radians(-25), 3, 'Z'))
    ellip(m, MUSCLE2, M, (9.5, 10.5, 5.0), (4.2, 2.3, 3.2), Matrix.Rotation(math.radians(30), 3, 'Z'))
    # the great vessels: aorta (rising, arching back over toward +x, down behind), pulmonary trunk (in front of it,
    # splitting left and right under the arch), superior vena cava (up from the right atrium), inferior (down behind)
    arch = [V(-1, 9, 2), V(-2, 22, 2.5), V(0, 30, 0), V(5, 31, -4), V(9, 25, -8), V(9.5, 12, -10), V(9.5, 2, -10.5)]
    trunk = [V(4, 5, 6.5), V(4.5, 15, 6.5), V(5.5, 20.5, 3.5)]
    lpa = [V(5.5, 20.5, 3.5), V(12, 22, 0), V(18, 20.5, -3)]
    rpa = [V(5.5, 20.5, 3.5), V(-2, 21.5, -3), V(-14, 20, -5)]
    svc = [V(-11.5, 15, -1), V(-12, 24, -1.5), V(-12.5, 33, -2)]
    ivc = [V(-8.5, 6, -6.5), V(-8, -2, -8), V(-7.5, -8, -9)]
    brs = [[V(-1.5, 29, 0.5), V(-3, 36, 0.5), V(-4.5, 41, 0)], [V(2.5, 31, -1.5), V(2.5, 38, -2.5), V(3, 43, -3)], [V(6, 30, -4.5), V(8, 36, -5), V(9.5, 40, -5)]]
    if style == 'grand':
        rope(m, AORTA, M, arch, 2.1, 6, 1.25, twist=1.6)
        rope(m, CAVA, M, svc, 1.4, 4, 1.0, twist=1.2)
    else:
        vessel(m, AORTA, M, arch, 3.6, 3.2, segs=16)
        vessel(m, CAVA, M, svc, 2.5, 2.3)
    vessel(m, PULM, M, trunk, 3.0, 2.8, segs=14)
    vessel(m, PULM, M, lpa, 2.1, 1.6)
    vessel(m, PULM, M, rpa, 2.1, 1.6)
    if style != 'chunky':
        vessel(m, CAVA, M, ivc, 2.2, 2.0)
        for pv in ([V(9, 13.5, -11), V(14, 15, -14), V(18, 16, -16)], [V(9, 11, -11), V(14, 10, -14.5), V(18, 9.5, -16)],
                   [V(1, 14, -12), V(-3, 16, -15), V(-6, 17, -17)]):
            vessel(m, PVEIN, M, pv, 1.4, 1.2, segs=10)
    # the three branches off the top of the arch (forked in the detailed takes, curling feelers in the grand one)
    for k, b in enumerate(brs):
        p = vessel(m, AORTA, M, b, 1.5 if style == 'chunky' else 1.25, 1.1, segs=10)
        if style == 'vessels':
            tipv = b[-1]
            for d in (-1, 1):
                vessel(m, AORTA, M, [tipv, tipv + V(d * 1.8, 2.6, d * 0.6), tipv + V(d * 3.2, 4.8, d * 1.2)], 0.9, 0.6, segs=8)
        if style == 'grand':
            tipv = b[-1]
            for d in (-1, 0, 1):
                ang = d * 0.9 + k * 0.7
                vessel(m, AORTA, M, [tipv, tipv + V(1.5 * math.sin(ang), 4, 1.5 * math.cos(ang)), tipv + V(4 * math.sin(ang + 0.6), 8, 3 * math.cos(ang + 0.6)),
                                     tipv + V(5.5 * math.sin(ang + 1.6), 11, 4 * math.cos(ang + 1.6))], 0.6, 0.3, segs=6)
    # the coronary vessels in their grooves: arteries pink-red, veins blue
    big = 1.15 if style == 'chunky' else 0.85
    on_surface(m, ARTERY, M, [(0.0, 72), (0.2, 76), (0.45, 70), (0.7, 76), (0.95, 84)], big)                 # anterior descending
    on_surface(m, ARTERY, M, [(0.02, 100), (0.05, 140), (0.07, 185), (0.06, 230)], big)                      # right coronary
    on_surface(m, VEIN, M, [(0.02, 64), (0.25, 62), (0.5, 58), (0.75, 64), (0.93, 74)], big * 0.85)          # great cardiac vein
    if style != 'chunky':
        on_surface(m, ARTERY, M, [(0.02, 60), (0.05, 20), (0.06, -20), (0.07, -60)], big)                      # circumflex
        for (s0, p0, s1, p1) in ((0.25, 74, 0.5, 35), (0.42, 72, 0.7, 30), (0.3, 78, 0.6, 118), (0.08, 160, 0.55, 165),
                                 (0.07, 210, 0.5, 225), (0.06, 0, 0.55, -10)):
            on_surface(m, ARTERY, M, [(s0, p0), ((s0 + s1) / 2, (p0 + p1) / 2 + 4), (s1, p1)], big * 0.7)
        for (s0, p0, s1, p1) in ((0.2, 60, 0.55, 22), (0.1, 150, 0.6, 150), (0.08, 260, 0.75, 262), (0.15, 300, 0.6, 320)):
            on_surface(m, VEIN, M, [(s0, p0), ((s0 + s1) / 2, (p0 + p1) / 2 - 3), (s1, p1)], big * 0.65)
