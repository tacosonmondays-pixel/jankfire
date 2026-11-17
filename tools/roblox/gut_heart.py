# THE HEART TOWER for the Gut arena (17 Nov 2026). The owner: "Can we have a map based on the gut district? We have this
# awesome heart tower build it would be a shame to not use it!!". The web model (docs/story/gut/GUT_HEART_MODEL.md) is
# body horror: 1,700 fused hearts, vessels, a bone spine with skulls. None of that may go to Roblox (the account has a
# content warning). This keeps its silhouette only: a tall spiral stair tower on flared legs, a big heart held at the
# top, and turns it into a clean sculpture: a smooth glossy heart like a giant candy or enamel piece, a pale spiral
# stair with a rail and balusters (a lattice, no bone, no skulls), smooth flared legs, a jewel-setting cradle.
# No veins, no vessels, no anatomy.
#
# Used by gut_takes.py (the owner's sheet of three hearts) and gut_models.py (the arena). Roblox studs, y up; the
# heart's front faces +z unless turned (yaw).
import math, bmesh
from mathutils import Matrix, Vector
import arenakit as K
from arenakit import put, Tr, Ry, Rx, Rz, I4

# ---------------------------------------------------------------- palette (soft pinks, corals and creams; quiet base)
IVORY, CREAM, BLUSH, ROSE = 'efe3d6', 'e6d3c2', 'e9bdb6', 'd99a98'
CORAL, CORAL2, DEEP = 'e0566a', 'c9475b', '9e3346'
GLOW, GLOW2 = 'ff5c7c', 'ff9ab0'
ROSEGOLD, ROSEGOLD2 = 'd8a28c', 'b98471'

# ---------------------------------------------------------------- the heart's outline: radius per angle round a point
_TAB = None
_N = 720
def _table(smooth_deg=7.0):
    """R(theta) of the classic heart curve, unit width, round the point (0, c) inside it, smoothed for a puffy cleft"""
    global _TAB
    if _TAB is not None: return _TAB
    pts = []
    for i in range(4000):
        t = 2 * math.pi * i / 4000
        pts.append((16 * math.sin(t) ** 3, 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)))
    cy = -2.0
    pol = sorted((math.atan2(y - cy, x), math.hypot(x, y - cy) / 32.0) for x, y in pts)
    raw = []
    j = 0
    for i in range(_N):
        th = -math.pi + 2 * math.pi * i / _N
        while j < len(pol) - 1 and pol[j + 1][0] < th: j += 1
        a, b = pol[j], pol[min(j + 1, len(pol) - 1)]
        f = 0.0 if b[0] == a[0] else max(0.0, min(1.0, (th - a[0]) / (b[0] - a[0])))
        raw.append(a[1] + (b[1] - a[1]) * f)
    w = max(1, int(smooth_deg / 360 * _N))
    _TAB = [sum(raw[(i + k) % _N] for k in range(-w, w + 1)) / (2 * w + 1) for i in range(_N)]
    return _TAB

def R(th):
    tab = _table()
    u = ((th + math.pi) / (2 * math.pi)) * _N
    i = int(math.floor(u)) % _N
    f = u - math.floor(u)
    return tab[i] * (1 - f) + tab[(i + 1) % _N] * f

def heart_bm(W, D, nt=64, nphi=24, puff=0.8):
    """a closed heart, W wide, D thick at its middle, centred on its outline's inner point; front +z"""
    bm = bmesh.new()
    front = bm.verts.new((0, 0, D / 2))
    back = bm.verts.new((0, 0, -D / 2))
    rings = []
    for k in range(1, nphi):
        ph = math.pi * k / nphi
        s, c = math.sin(ph), math.cos(ph)
        sp = s ** puff
        cp = math.copysign(abs(c) ** puff, c)
        ring = []
        for i in range(nt):
            th = -math.pi + 2 * math.pi * i / nt
            r = R(th) * W
            ring.append(bm.verts.new((r * math.cos(th) * sp, r * math.sin(th) * sp, cp * D / 2)))
        rings.append(ring)
    for i in range(nt):
        j = (i + 1) % nt
        bm.faces.new((front, rings[0][j], rings[0][i]))
        bm.faces.new((back, rings[-1][i], rings[-1][j]))
    for a, b in zip(rings, rings[1:]):
        for i in range(nt):
            j = (i + 1) % nt
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def outline_pts(W, n=96, z=0.0, grow=0.0):
    return [Vector(((R(th) * W + grow) * math.cos(th), (R(th) * W + grow) * math.sin(th), z))
            for th in (-math.pi + 2 * math.pi * i / n for i in range(n))]

def heart_extent(W):
    """(lowest y, highest y) of the outline, relative to its inner point"""
    ys = [p.y for p in outline_pts(W, 360)]
    return min(ys), max(ys)

def slice_bm(bm, y0, y1):
    """the part of a mesh between two heights (open at the cuts)"""
    b = bm.copy()
    bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=(0, y0, 0), plane_no=(0, 1, 0), clear_inner=True)
    bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=(0, y1, 0), plane_no=(0, 1, 0), clear_outer=True)
    return b

# ---------------------------------------------------------------- swept tubes
def tube(model, col, pts, rad, segs=10, kind='plastic', closed=False, M=I4, caps=True):
    """a round tube along points (Vector, Roblox space), radius per point or one radius"""
    n = len(pts)
    rads = list(rad) if isinstance(rad, (list, tuple)) else [rad] * n
    T = []
    for i in range(n):
        if closed: a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        else: a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        T.append((b - a).normalized())
    up = Vector((0, 1, 0)) if abs(T[0].y) < 0.9 else Vector((1, 0, 0))
    N = T[0].cross(up).normalized()
    bm = bmesh.new()
    rings = []
    for i in range(n):
        if i > 0:
            ax = T[i - 1].cross(T[i])
            if ax.length > 1e-7:
                N = Matrix.Rotation(T[i - 1].angle(T[i]), 3, ax.normalized()) @ N
        N = (N - T[i] * N.dot(T[i])).normalized()
        Bv = T[i].cross(N)
        rings.append([bm.verts.new(pts[i] + (N * math.cos(2 * math.pi * k / segs) + Bv * math.sin(2 * math.pi * k / segs)) * rads[i]) for k in range(segs)])
    for i in range(n if closed else n - 1):
        a, b = rings[i], rings[(i + 1) % n]
        for k in range(segs):
            bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k]))
    if not closed and caps:
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    put(model, kind, col, bm, M)

def lathe_loop(model, col, prof, x, y, z, segs=48, kind='plastic'):
    """spin a closed profile [(r, y), ...] round the up axis: a ring with a hole (arenakit.lathe would cap it)"""
    bm = bmesh.new()
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * i / segs), h, r * math.sin(2 * math.pi * i / segs))) for i in range(segs)] for r, h in prof]
    n = len(rings)
    for k in range(n):
        a, b = rings[k], rings[(k + 1) % n]
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    put(model, kind, col, bm, Tr(x, y, z))

def bez(p0, p1, p2, n):
    return [p0 * (1 - t) ** 2 + p1 * 2 * (1 - t) * t + p2 * t * t for t in (i / (n - 1) for i in range(n))]

def ball(model, col, p, r, kind='plastic', sy=1.0):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r)
    if sy != 1.0: bmesh.ops.scale(bm, vec=(1, sy, 1), verts=bm.verts)
    put(model, kind, col, bm, Tr(p.x, p.y, p.z))

# ---------------------------------------------------------------- the tower
# the numbers (shared with the hit boxes in gut_layout.py)
from gut_heart_dims import *

def tower(m, take, x=0.0, y=0.0, z=0.0, yaw=0.0, legs=4, phase=0.0, heart=True, leg0=None):
    """the whole tower at (x, y, z), turned yaw radians round its up axis. the stair starts at angle `phase` (in the
    tower's own frame) and climbs 315 degrees round to the balcony, then on up to the cradle (look only above a gate).
    models: <m>_tw (plinth, core, legs, balcony, stair), <m>_cr (the cradle), <m>_ht (the heart: its own model so the
    game can turn it and make it beat)"""
    O = Tr(x, y, z) @ Ry(yaw)
    mt, mh, mc = m + '_tw', m + '_ht', m + '_cr'
    V = lambda a, b, c: (O @ Vector((a, b, c, 1))).xyz
    circ = lambda r, h, n=64: [V(r * math.cos(t), h, r * math.sin(t)) for t in (2 * math.pi * k / n for k in range(n))]
    # the plinth: two soft round steps
    (r1, h1), (r2, h2) = PLINTH
    K.lathe(mt, CREAM, [(0, 0), (r1, 0), (r1, h1 - 0.35), (r1 - 0.35, h1), (r2, h1), (r2, h2 - 0.35), (r2 - 0.35, h2), (0, h2)], x, y, z, segs=48)
    # the core: one smooth column with a rounded collar every 12 studs
    prof = [(0, h2 - 0.2)]
    for k in range(0, int((CORE_TOP - h2) / 0.75) + 1):
        h = h2 + k * 0.75
        ph = ((h - h2) % 12.0) / 12.0
        prof.append((4.7 + 1.05 * (0.5 + 0.5 * math.cos(2 * math.pi * ph)) ** 6, h))
    prof.append((0, prof[-1][1]))
    K.lathe(mt, IVORY, prof, x, y, z, segs=28)
    # the legs: smooth flared arcs from round foot pads on the diagonals up under the balcony's outer edge
    for i in range(legs):
        a = (math.pi / legs if leg0 is None else leg0) + 2 * math.pi * i / legs
        ca, sa = math.cos(a), math.sin(a)
        p0 = V(LEG_FOOT * ca, 2.0, LEG_FOOT * sa)
        p1 = V((LEG_FOOT - 4.5) * ca, 11.0, (LEG_FOOT - 4.5) * sa)
        p2 = V((BALC_R1 - 1.2) * ca, BALC_Y - 1.4, (BALC_R1 - 1.2) * sa)
        n = 14
        tube(mt, CREAM, bez(p0, p1, p2, n), [3.6 - 1.2 * (k / (n - 1)) for k in range(n)], segs=14)
        ball(mt, CREAM, V((LEG_FOOT + 0.6) * ca, 0.0, (LEG_FOOT + 0.6) * sa), 5.0, sy=0.5)
        # a slimmer brace on from the balcony up to the lattice band
        tube(mt, CREAM, [V((BALC_R1 - 1.5) * ca, BALC_Y + 0.2, (BALC_R1 - 1.5) * sa), V(17.0 * ca, 46.0, 17.0 * sa),
                         V(15.2 * ca, 72.0, 15.2 * sa)], 1.1, segs=10)
    # the balcony: a flat ring you can walk on, a rounded edge, a rail on posts
    lathe_loop(mt, CREAM, [(BALC_R0, BALC_Y - 1.6), (BALC_R1 - 0.6, BALC_Y - 1.6), (BALC_R1, BALC_Y - 1.0), (BALC_R1, BALC_Y - 0.4),
                            (BALC_R1 - 0.4, BALC_Y), (BALC_R0, BALC_Y)], x, y, z, segs=64)
    tube(mt, ROSE, circ(BALC_R1 - 0.5, BALC_Y + 3.4, 72), 0.42, segs=8, closed=True)
    for k in range(24):
        t = 2 * math.pi * k / 24
        p = V((BALC_R1 - 0.5) * math.cos(t), BALC_Y, (BALC_R1 - 0.5) * math.sin(t))
        K.cyl(mt, IVORY, p.x, p.y, p.z, 0.3, 3.4, segs=8, bev=0.0)
    # the lattice band higher up
    tube(mt, CREAM, circ(15.2, 72.0), 0.9, segs=10, closed=True)
    # the stair: rounded treads round the core, a stringer under their outer ends, a rail and balusters
    tr = stair_treads(phase=phase)
    nwalk = len(walk_treads(phase))
    for a, ty in tr:
        c = V(((STAIR_R0 + STAIR_R1) / 2) * math.cos(a), ty - 0.35, ((STAIR_R0 + STAIR_R1) / 2) * math.sin(a))
        K.Bc(mt, BLUSH, c.x, c.y, c.z, STAIR_R1 - STAIR_R0, 0.7, 3.25, bev=0.28, yaw=(yaw - a))
    def helix(seg, r, dy, n_per=4):
        pts = []
        for (a0, y0), (a1, y1) in zip(seg, seg[1:]):
            for k in range(n_per):
                f = k / n_per
                pts.append(V(r * math.cos(a0 + (a1 - a0) * f), y0 + (y1 - y0) * f + dy, r * math.sin(a0 + (a1 - a0) * f)))
        a, yy = seg[-1]
        pts.append(V(r * math.cos(a), yy + dy, r * math.sin(a)))
        return pts
    tube(mt, IVORY, helix(tr, STAIR_R1 - 0.3, -0.9), 0.75, segs=10)          # the stringer, all the way
    low, high = tr[:nwalk - 2], tr[nwalk + 1:]                                # the rail stops where you step off
    tube(mt, ROSE, helix(low, STAIR_R1 - 0.2, 3.4), 0.42, segs=8)
    tube(mt, ROSE, helix(high, STAIR_R1 - 0.2, 3.4), 0.42, segs=8)
    for k, (a, ty) in enumerate(tr):
        if k % 2 or (nwalk - 2 <= k <= nwalk): continue
        p = V((STAIR_R1 - 0.2) * math.cos(a), ty, (STAIR_R1 - 0.2) * math.sin(a))
        K.cyl(mt, IVORY, p.x, p.y, p.z, 0.22, 3.4, segs=6, bev=0.0)
    # the gate across the stair just over the balcony: rose-gold bars (above it the stair is look only)
    ga, gy = tr[nwalk]
    gt = ga - STAIR_STEP * 0.5
    for j in range(5):
        r = STAIR_R0 + 0.9 + j * (STAIR_R1 - STAIR_R0 - 1.8) / 4
        p = V(r * math.cos(gt), gy - 1.2, r * math.sin(gt))
        K.cyl(mt, ROSEGOLD, p.x, p.y, p.z, 0.32, 5.6, segs=8, bev=0.0)
    tube(mt, ROSEGOLD, [V(r * math.cos(gt), gy + 4.2, r * math.sin(gt)) for r in (STAIR_R0 + 0.4, STAIR_R1 - 0.4)], 0.4, segs=8)
    # the lattice: eight upright rods from the balcony's edge to the band, and on in to the cradle
    for i in range(8):
        a = 2 * math.pi * i / 8 + math.pi / 8
        tube(mt, IVORY, [V((BALC_R1 - 1.0) * math.cos(a), BALC_Y + 3.6, (BALC_R1 - 1.0) * math.sin(a)), V(15.2 * math.cos(a), 72.0, 15.2 * math.sin(a)),
                         V(12.0 * math.cos(a), CORE_TOP + 2.0, 12.0 * math.sin(a))], 0.45, segs=6)
    # the cradle: a flared cup on the core and six prongs that hold the heart's lower half from outside, like a jewel's
    K.lathe(mc, ROSEGOLD, [(0, CORE_TOP - 2), (5.2, CORE_TOP - 2), (7.5, CORE_TOP + 1.5), (12.5, CORE_TOP + 4.0),
                            (13.0, CORE_TOP + 5.0), (11.6, CORE_TOP + 5.0), (6.0, CORE_TOP + 3.0), (0, CORE_TOP + 3.0)], x, y, z, segs=40)
    for i in range(6):
        a = 2 * math.pi * i / 6
        ca, sa = math.cos(a), math.sin(a)
        pts = bez(V(12.2 * ca, CORE_TOP + 4.5, 12.2 * sa), V(21.5 * ca, CORE_TOP + 11, 21.5 * sa), V(19.0 * ca, CORE_TOP + 21, 19.0 * sa), 12)
        tube(mc, ROSEGOLD, pts, [1.25 - 0.45 * (k / 11) for k in range(12)], segs=8)
        ball(mc, ROSEGOLD2, pts[-1], 1.3)
    if heart:
        heart_take(mh, take, O @ Tr(0, HEART_Y, 0))
    return tr, nwalk

def heart_take(m, take, M):
    """the heart itself, centred at M (its outline's inner point), facing M's +z, tipped a little"""
    if take in ('chunky', 'vessels', 'grand'):      # the anatomical takes (the owner: "We can do an actual heart")
        import gut_heart_anat
        gut_heart_anat.anat_heart(m, take, M)
        return
    T = M @ Rz(math.radians(-10))
    lo, hi = heart_extent(HEART_W)
    if take == 'candy':
        # a puffy glossy coral heart with a cream piping round its edge, like an enamel pin or a sugar heart
        put(m, 'plastic', CORAL, heart_bm(HEART_W, HEART_D, 72, 26, puff=0.72), T)
        tube(m, IVORY, [T @ p for p in outline_pts(HEART_W, 120, grow=0.15)], 0.9, segs=10, closed=True)
    elif take == 'gem':
        # a cut ruby: flat facets of see-through coral with a glowing heart inside it
        g = heart_bm(HEART_W, HEART_D * 1.05, 22, 7, puff=1.0)
        for e in g.edges: e.smooth = False
        put(m, 'glass', 'e8506a', g, T)
        put(m, 'neon', GLOW, heart_bm(HEART_W * 0.52, HEART_D * 0.5, 40, 16, puff=0.75), T)
    elif take == 'lantern':
        # an enamel lantern: the coral heart banded by glowing seams (a wave of light climbs them on each beat), a
        # rose-gold hoop round it
        body = heart_bm(HEART_W, HEART_D, 72, 26, puff=0.72)
        put(m, 'plastic', CORAL, body, T)
        shell = heart_bm(HEART_W * 1.025, HEART_D * 1.05, 72, 26, puff=0.72)
        span = hi - lo
        for k in range(1, 6):
            yy = lo + span * k / 6.0
            put(m, 'neon', GLOW2 if k % 2 else GLOW, slice_bm(shell, yy - 0.55, yy + 0.55), T)
        shell.free()
        H = T @ Rx(math.radians(70))
        tube(m, ROSEGOLD, [H @ Vector((25 * math.cos(t), 25 * math.sin(t), 0)) for t in (2 * math.pi * k / 72 for k in range(72))], 0.85, segs=10, closed=True)
    else:
        raise ValueError(take)
