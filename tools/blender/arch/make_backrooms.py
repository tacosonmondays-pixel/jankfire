# The Backrooms' walls (shared/map.js backrooms()): every wallpaper box on the map (the maze's walls, the hall's walls
# and its freestanding and half walls, every pillar) drawn as one Blender model over its own boxes, which stay what you
# bump into. Level 0 the way people remember it, so the emptiness reads:
#  - the wallpaper (brtex.py br_wall): 0.53 m strips with their seams, a stripe pair and a chevron column on each,
#    and here and there a strip peeling off at the top (the bare drywall behind it, the paper's back curling out)
#  - a painted skirting board with a chamfered top round every wall foot, the drop ceiling's white wall angle where the
#    wall meets the ceiling, every outside corner chamfered and grubby where hands brush it, ivory corner guards on
#    the pillars
#  - painted casings and jamb liners round the openings that have a head (the hall's tall doorways, the doorway to
#    nowhere, the window), a wooden cap on the half walls, a drywall top on the freestanding ones
#  - the wall's stuff, sparse (brtex.py br_fix): outlets, switches by doorways, return-air grilles, thermostats, the odd
#    fire alarm pull, a paper sign with nothing useful on it
#  - damp (brtex.py br_stain): tide marks up from the floor, drips down from the ceiling, mould, leak rings
#  - vertex AO from the walls, the floor and the ceilings
# The maze is procedural but fixed (seed 1777), so this is built over the real boxes. Look only: tools/arch/gamehash.mjs
# is the same with or without it.
# run: node tools/arch/dump.mjs backrooms backrooms tools/blender/arch/boxes/backrooms.json
#      python3 tools/blender/arch/brtex.py
#      blender52 -b --python tools/blender/arch/make_backrooms.py [-- --no-ao]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import archkit
from archkit import Kit, OUTDIR, MATS, NOCAST, KIT
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
KIT.update({'br_wall': {'tile': 1.06}, 'br_stain': {'tile': 1.0}, 'br_fix': {'tile': 1.0}})  # (brtex.py TILES)
MATS.update({
    'br_wall': ('br_wall', '#ffffff', {}), 'br_edge': ('br_wall', '#b4a06a', {}),
    'br_skirt': ('trim', '#a89058', {}), 'br_casing': ('trim', '#e4d59e', {}), 'br_angle': ('trim', '#f6f2e4', {}),
    'br_guard': ('trim', '#f0e8cc', {}), 'br_cap': ('trim', '#c4a464', {}), 'br_top': ('stucco', '#d8cea4', {}),
    'br_back': ('stucco', '#f2ead2', {}), 'br_drywall': ('stucco', '#d4d0c2', {}),
    'br_tide': ('br_wall', '#dccfa6', {}), 'br_tideline': ('br_wall', '#a89260', {}),
    'br_fix': ('br_fix', '#ffffff', {}), 'br_fixside': ('trim', '#e2d8b8', {}), 'br_stain': ('br_stain', '#ffffff', {'alpha': True, 'decal': True}),
})
NOCAST.update({'br_tide', 'br_tideline', 'br_edge', 'br_skirt', 'br_casing', 'br_angle', 'br_guard', 'br_cap', 'br_back', 'br_drywall', 'br_fix', 'br_fixside', 'br_stain'})

_mm = archkit.make_material
def _make_material(name):  # (extras 'decal': the game pulls it toward the camera, so it can lie right on the wall)
    m = _mm(name)
    if MATS[name][2].get('decal'): m['decal'] = 1
    return m
archkit.make_material = _make_material

H, HH, HALL = 4.2, 9.0, 32.0   # the drop ceiling, the hall's ceiling, the hall's half size (shared/map.js)
EPS = 0.004
CH = 0.012                     # the chamfer on outside corners
SK, SKH = 0.016, 0.1           # skirting: how proud, how tall
R = random.Random(1777)

K = Kit(os.path.join(HERE, 'boxes', 'backrooms.json'))
BX = [(tuple(b['min']), tuple(b['max'])) for b in K.boxes]
K.extra_occ = [((-120, -0.6, -120), (120, 0, 120))]  # the floor and the ceilings darken the corners too
for (x0, z0, x1, z1) in ((-120, -120, 120, -HALL), (-120, HALL, 120, 120), (-120, -HALL, -HALL, HALL), (HALL, -HALL, 120, HALL)):
    K.extra_occ.append(((x0, H, z0), (x1, H + 0.3, z1)))
K.extra_occ.append(((-HALL, HH, -HALL), (HALL, HH + 0.3, HALL)))


def ceil_at(x, z): return HH if -HALL < x < HALL and -HALL < z < HALL else H


# ------------------------------------------------------------ a grid of the boxes, to find neighbours fast
GRID = {}
for i, (mn, mx) in enumerate(BX):
    for gx in range(int(math.floor(mn[0] / 4)), int(math.floor(mx[0] / 4)) + 1):
        for gz in range(int(math.floor(mn[2] / 4)), int(math.floor(mx[2] / 4)) + 1):
            GRID.setdefault((gx, gz), []).append(i)


def near(mn, mx):
    out = set()
    for gx in range(int(math.floor((mn[0] - 0.1) / 4)), int(math.floor((mx[0] + 0.1) / 4)) + 1):
        for gz in range(int(math.floor((mn[2] - 0.1) / 4)), int(math.floor((mx[2] + 0.1) / 4)) + 1):
            out.update(GRID.get((gx, gz), ()))
    return out


def solid_at(p, skip=-1):
    for i in near(p, p):
        if i == skip: continue
        mn, mx = BX[i]
        if all(mn[k] - 1e-5 <= p[k] <= mx[k] + 1e-5 for k in range(3)): return i
    return None


def rsub(rs, c):
    """rects (u0, y0, u1, y1) minus rect c"""
    out = []
    for r in rs:
        if c[2] <= r[0] + 1e-5 or c[0] >= r[2] - 1e-5 or c[3] <= r[1] + 1e-5 or c[1] >= r[3] - 1e-5: out.append(r); continue
        if c[0] > r[0]: out.append((r[0], r[1], c[0], r[3]))
        if c[2] < r[2]: out.append((c[2], r[1], r[2], r[3]))
        a, b = max(r[0], c[0]), min(r[2], c[2])
        if c[1] > r[1]: out.append((a, r[1], b, c[1]))
        if c[3] < r[3]: out.append((a, c[3], b, r[3]))
    return [r for r in out if r[2] - r[0] > 1e-4 and r[3] - r[1] > 1e-4]


# ------------------------------------------------------------ faces. a side face: axis a (0 = faces x, 2 = faces z),
# plane coordinate c, sign s (+1/-1); in-plane u runs along the other horizontal axis (ua), v is y
class Face:
    def __init__(self, bi, a, s):
        mn, mx = BX[bi]
        self.bi, self.a, self.s = bi, a, s
        self.ua = 2 if a == 0 else 0
        self.c = mx[a] if s > 0 else mn[a]
        self.u0, self.u1 = mn[self.ua], mx[self.ua]
        self.y0, self.y1 = mn[1], mx[1]
        self.thin = (mx[a] - mn[a]) <= 0.25 and (mx[self.ua] - mn[self.ua]) > 0.25   # a wall's broad face
        self.jamb = (mx[self.ua] - mn[self.ua]) <= 0.25                              # a thin wall's end
        self.pillar = (mx[a] - mn[a]) > 0.25 and (mx[self.ua] - mn[self.ua]) > 0.25

    def P(self, u, y, o=0.0):
        p = [0.0, y, 0.0]; p[self.a] = self.c + self.s * o; p[self.ua] = u
        return tuple(p)

    def front(self, u, y): return self.P(u, y, EPS)

    def n(self):
        v = [0, 0, 0]; v[self.a] = self.s; return Vector(v)


def uv_of(n, p):
    """world-scale uvs like archkit's (so a peeled strip keeps its pattern)"""
    t = KIT['br_wall']['tile']; q = Vector(p)
    if abs(n.x) > 0.5: return (q.z / t, q.y / t) if n.x < 0 else (-q.z / t, q.y / t)
    return (q.x / t, q.y / t) if n.z > 0 else (-q.x / t, q.y / t)


def fq(pts, mat, want, uv=None, sub=None):
    """a quad facing `want` whatever order the corners came in"""
    p = [Vector(q) for q in pts]
    if (p[1] - p[0]).cross(p[2] - p[0]).dot(want) < 0: pts = pts[::-1]; uv = uv[::-1] if uv else None
    K.quad(pts, mat, uv=uv, sub=sub)


def slab(F, u0, u1, y0, y1, o0, o1, mat, sides=True, ends=(True, True), top=True, bottom=False, front_mat=None, front_uv=None):
    """a little box sitting on face F: u0..u1 along it, y0..y1, from o0 to o1 out from it. no back (against the wall)"""
    n = F.n(); ue = Vector([0, 0, 0]); ue[F.ua] = 1
    fq([F.P(u0, y0, o1), F.P(u1, y0, o1), F.P(u1, y1, o1), F.P(u0, y1, o1)], front_mat or mat, n, uv=front_uv)
    if top: fq([F.P(u0, y1, o0), F.P(u1, y1, o0), F.P(u1, y1, o1), F.P(u0, y1, o1)], mat, Vector((0, 1, 0)))
    if bottom: fq([F.P(u0, y0, o0), F.P(u1, y0, o0), F.P(u1, y0, o1), F.P(u0, y0, o1)], mat, Vector((0, -1, 0)))
    if sides:
        if ends[0]: fq([F.P(u0, y0, o0), F.P(u0, y0, o1), F.P(u0, y1, o1), F.P(u0, y1, o0)], mat, -ue)
        if ends[1]: fq([F.P(u1, y0, o0), F.P(u1, y0, o1), F.P(u1, y1, o1), F.P(u1, y1, o0)], mat, ue)


# ------------------------------------------------------------ pass 1: every visible side face, cut where something covers it
faces = []          # (Face, [rects])
planes = {}         # (a, c, s) -> rects already drawn on that plane (two boxes in a row overlap by the wall's thickness)
tops, bottoms = [], []
for bi, (mn, mx) in enumerate(BX):
    for a in (0, 2):
        for s in (1, -1):
            F = Face(bi, a, s)
            cy = ceil_at(*[F.front(0.5 * (F.u0 + F.u1), 1.0)[k] for k in (0, 2)])
            if F.y0 >= cy - 1e-4: continue
            rs = [(F.u0, F.y0, F.u1, min(F.y1, cy))]
            pm, px = list(F.P(F.u0, F.y0, 0)), list(F.P(F.u1, F.y1, 0.002))
            for k in range(3):
                if pm[k] > px[k]: pm[k], px[k] = px[k], pm[k]
            for j in near(tuple(pm), tuple(px)):
                if j == bi: continue
                qn, qx = BX[j]
                if not (qn[a] - 1e-5 <= F.c + s * 0.002 <= qx[a] + 1e-5): continue
                rs = rsub(rs, (qn[F.ua], qn[1], qx[F.ua], qx[1]))
                if not rs: break
            key = (a, round(F.c, 4), s)
            for r in planes.get(key, []):
                rs = rsub(rs, r)
            if rs:
                planes.setdefault(key, []).extend(rs)
                faces.append((F, rs))
    cy = ceil_at(0.5 * (mn[0] + mx[0]), 0.5 * (mn[2] + mx[2]))
    if mx[1] < cy - 1e-3 and solid_at((0.5 * (mn[0] + mx[0]), mx[1] + 0.002, 0.5 * (mn[2] + mx[2])), bi) is None: tops.append(bi)
    if mn[1] > 1e-3 and solid_at((0.5 * (mn[0] + mx[0]), mn[1] - 0.002, 0.5 * (mn[2] + mx[2])), bi) is None: bottoms.append(bi)
print('faces', len(faces), 'tops', len(tops), 'heads', len(bottoms))

# ------------------------------------------------------------ openings with a head: casings, jamb liners (no chamfer there)
cased = set()   # (box index, which end: 0 = u0, 1 = u1) whose jamb gets a liner + casings instead of a chamfer
heads = []      # (box index of the head, the line's face axis, u0, u1, y head, y sill)
for bi in bottoms:
    mn, mx = BX[bi]
    if mx[0] - mn[0] <= 0.25: a, ua = 0, 2
    elif mx[2] - mn[2] <= 0.25: a, ua = 2, 0
    else: continue
    yh = mn[1]
    mid_a = 0.5 * (mn[a] + mx[a])
    def at(u, y):
        p = [0, y, 0]; p[a] = mid_a; p[ua] = u; return tuple(p)
    # the jambs: the boxes on either side under the head
    l = solid_at(at(mn[ua] - 0.002, yh * 0.5)); r = solid_at(at(mx[ua] + 0.002, yh * 0.5))
    sill = solid_at(at(0.5 * (mn[ua] + mx[ua]), 0.6))
    ys = BX[sill][1][1] if sill is not None and BX[sill][1][1] < yh else 0.0
    heads.append((bi, a, mn[ua], mx[ua], yh, ys))
    if l is not None: cased.add((l, 1))
    if r is not None: cased.add((r, 0))
print('cased openings', len(heads))

# ------------------------------------------------------------ pass 2: chamfered outside corners. for every jamb (a thin
# wall's end, or a pillar's side) and its visible y spans, trim the faces either side and lay a chamfer across
chamfers = []   # (Face of the broad side, u at the corner, dir (-1: corner at u1 side... ), y0, y1, end Face)
face_by_box = {}
for F, rs in faces: face_by_box.setdefault((F.bi, F.a, F.s), []).append((F, rs))


def visible_spans(bi, a, s):
    out = []
    for F, rs in face_by_box.get((bi, a, s), []):
        out += [(r[1], r[3]) for r in rs]
    return out


trims = {}   # (bi, a, s) -> extra rects to cut out of that face
for bi, (mn, mx) in enumerate(BX):
    for a in (0, 2):
        ua = 2 if a == 0 else 0
        for s in (1, -1):  # the end face (a, s); its neighbours are the faces (ua, +-1). each corner once: from a thin
            # wall's end, or from a pillar's x-facing sides
            for F, rs in face_by_box.get((bi, a, s), []):
                if not (F.jamb or (F.pillar and a == 0)): continue
                for r in rs:
                    # the end's two vertical edges: at u = r[0] and r[2] on the end face. each is an outside corner if the
                    # broad face round it is visible over the same span
                    for side, u in ((-1, r[0]), (1, r[2])):
                        if abs(u - (mn[ua] if side < 0 else mx[ua])) > 1e-4: continue
                        end_u = 0 if s < 0 else 1
                        if (bi, end_u) in cased and F.jamb: continue
                        G = [g for g, _ in face_by_box.get((bi, ua, side), [])]
                        if not G: continue
                        y0, y1 = r[1], r[3]
                        ok = [(max(y0, b0), min(y1, b1)) for (b0, b1) in visible_spans(bi, ua, side) if min(y1, b1) - max(y0, b0) > 0.05]
                        for (b0, b1) in ok:
                            trims.setdefault((bi, a, s), []).append((u - CH if side > 0 else u, b0, u + CH if side < 0 else u, b1))
                            gc = F.c  # the corner's coordinate along a
                            trims.setdefault((bi, ua, side), []).append((gc - CH if s > 0 else gc, b0, gc + CH if s < 0 else gc, b1))
                            chamfers.append((bi, a, s, ua, side, F.c, u, b0, b1))
faces2 = []
for F, rs in faces:
    for t in trims.get((F.bi, F.a, F.s), []): rs = rsub(rs, t)
    if rs: faces2.append((F, rs))
faces = faces2
print('chamfers', len(chamfers))

# ------------------------------------------------------------ pass 3: draw. walls cut into cells for the AO (rows near the
# floor and the ceiling, 4 m columns on world lines so neighbours share their vertices)
ROWS = [0.0, 0.4, H - 0.5, H, HH - 0.6, HH]  # (where the AO changes: the floor, the ceiling)
liners = set()
for F, rs in faces:
    n = F.n()
    end_u = None
    if F.jamb: end_u = 0 if F.s < 0 else 1
    mat = 'br_casing' if (F.jamb and (F.bi, end_u) in cased) else 'br_wall'
    for (u0, y0, u1, y1) in rs:
        cy = [y0] + [r for r in ROWS if y0 + 0.02 < r < y1 - 0.02] + [y1] if u1 - u0 > 0.3 else [y0, y1]  # (a jamb: one quad)
        cu = [u0] + [k * 4.0 for k in range(int(math.ceil(u0 / 4.0 + 1e-6)), int(math.floor(u1 / 4.0 - 1e-6)) + 1) if u0 + 0.02 < k * 4.0 < u1 - 0.02] + [u1]
        for i in range(len(cu) - 1):
            for j in range(len(cy) - 1):
                fq([F.P(cu[i], cy[j]), F.P(cu[i + 1], cy[j]), F.P(cu[i + 1], cy[j + 1]), F.P(cu[i], cy[j + 1])], mat, n)
# the chamfers across outside corners: from the end face (trimmed CH in from the corner) to the broad face
for (bi, a, s, ua, side, c, u, y0, y1) in chamfers:
    def pt(da, du, y):
        p = [0, y, 0]; p[a] = c + da; p[ua] = u + du; return tuple(p)
    p0, p1 = pt(0, -side * CH, y0), pt(-s * CH, 0, y0)
    want = Vector([0, 0, 0]); want[a] = s; want[ua] = side
    fq([p0, p1, pt(-s * CH, 0, y1), pt(0, -side * CH, y1)], 'br_edge', want.normalized())

# tops: half walls get a wooden cap rail, taller freestanding walls a drywall top
for bi in tops:
    mn, mx = BX[bi]
    if mx[1] < 2.0:
        ax = 0 if (mx[0] - mn[0]) <= 0.25 else 2
        lo, hi = list(mn), list(mx)
        lo[ax] -= 0.025; hi[ax] += 0.025
        oa = 2 if ax == 0 else 0  # along the wall: overhang where the end is free
        mid = [0.5 * (mn[0] + mx[0]), mx[1] - 0.05, 0.5 * (mn[2] + mx[2])]
        e0 = list(mid); e0[oa] = mn[oa] - 0.003; e1 = list(mid); e1[oa] = mx[oa] + 0.003
        if solid_at(tuple(e0), bi) is None: lo[oa] -= 0.025
        if solid_at(tuple(e1), bi) is None: hi[oa] += 0.025
        lo[1] = mx[1]; hi[1] = mx[1] + 0.045
        K.box(tuple(lo), tuple(hi), {'all': 'br_cap'}, cull=False)
    else:
        x0, z0, x1, z1, y = mn[0], mn[2], mx[0], mx[2], mx[1]
        if mx[0] - mn[0] <= 0.25: z0 += CH; z1 -= CH
        else: x0 += CH; x1 -= CH
        fq([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], 'br_top', Vector((0, 1, 0)))
# heads: the underside lined, casings round the opening on both faces
for (bi, a, u0, u1, yh, ys) in heads:
    mn, mx = BX[bi]
    ua = 2 if a == 0 else 0
    lo, hi = mn[a], mx[a]
    def P(av, u, y):
        p = [0, y, 0]; p[a] = av; p[ua] = u; return tuple(p)
    fq([P(lo, u0, yh), P(hi, u0, yh), P(hi, u1, yh), P(lo, u1, yh)], 'br_casing', Vector((0, -1, 0)))
    for s, c in ((1, hi), (-1, lo)):
        F = Face(bi, a, s); F.c = c
        cy = ceil_at(*[F.front(0.5 * (u0 + u1), 1.0)[k] for k in (0, 2)])
        W, D = 0.075, 0.016
        if yh + W <= cy: slab(F, u0 - W, u1 + W, yh, yh + W, 0, D, 'br_casing', bottom=True)
        for (ua0, ua1, e) in ((u0 - W, u0, (True, False)), (u1, u1 + W, (False, True))):
            slab(F, ua0, ua1, max(ys, SKH if ys == 0 else ys), min(yh, cy), 0, D, 'br_casing', ends=e, top=False)
        if ys > 0: slab(F, u0 - W, u1 + W, ys - W, ys, 0, D, 'br_casing', bottom=True, top=False)

# skirting round every wall foot, the ceiling's wall angle along every top, corner guards on the pillars
prof = [(0.0, 0.0), (SK, 0.0), (SK, SKH), (0.0, SKH)]  # (o, y) up the face and back


def chop4(a, b):
    """a..b cut on the 4 m world lines (a strip tens of metres long in one quad sparkles through walls on some GPUs)"""
    if b - a <= 8.0: return [(a, b)]  # (only the long runs: a wall's ends hang 0.1 m past the grid lines, no slivers there)
    cuts = [a] + [k * 4.0 for k in range(int(math.floor(a / 4.0)) + 1, int(math.ceil(b / 4.0))) if a + 0.5 < k * 4.0 < b - 0.5] + [b]
    return list(zip(cuts[:-1], cuts[1:]))
for F, rs in faces:
    n = F.n(); ue = Vector([0, 0, 0]); ue[F.ua] = 1
    cy = ceil_at(*[F.front(0.5 * (F.u0 + F.u1), 1.0)[k] for k in (0, 2)])
    for (u0, y0, u1, y1) in rs:
        if y0 < 1e-3:
            a0, a1 = u0, u1
            if abs(u0 - F.u0 - CH) < 1e-4: a0 -= CH  # (round the chamfer: the skirting's corner stays square)
            if abs(u1 - F.u1 + CH) < 1e-4: a1 += CH
            if (F.jamb or F.pillar) and abs(a0 - F.u0) < 1e-4: a0 -= SK  # (wraps round the end over the side skirting)
            if (F.jamb or F.pillar) and abs(a1 - F.u1) < 1e-4: a1 += SK
            for k in range(len(prof) - 1):
                (o0, ya), (o1, yb) = prof[k], prof[k + 1]
                if o0 == o1 == 0: continue
                if ya == yb == 0: continue
                want = (n * (yb - ya) - Vector((0, 1, 0)) * (o1 - o0))
                for (c0, c1) in chop4(a0, a1):
                    fq([F.P(c0, ya, o0), F.P(c1, ya, o0), F.P(c1, yb, o1), F.P(c0, yb, o1)], 'br_skirt', want if want.length > 0 else n)
        if abs(y1 - cy) < 1e-3:
            # the wall angle: a white L the ceiling tiles sit on
            for (c0, c1) in chop4(u0, u1): slab(F, c0, c1, cy - 0.03, cy - 0.003, 0, 0.004, 'br_angle', top=False, sides=False, bottom=True)
# corner guards: an ivory L up the pillars' corners to shoulder height
for (bi, a, s, ua, side, c, u, y0, y1) in chamfers:
    mn, mx = BX[bi]
    if (mx[0] - mn[0]) <= 0.25 or (mx[2] - mn[2]) <= 0.25: continue
    g0, g1, W, o = max(y0, SKH), min(y1, 1.35), 0.045, 0.004
    if g1 - g0 < 0.2: continue
    def pt(da, du, y):
        p = [0, y, 0]; p[a] = c + da; p[ua] = u + du; return tuple(p)
    na = Vector([0, 0, 0]); na[a] = s; nu = Vector([0, 0, 0]); nu[ua] = side; nc = (na + nu).normalized()
    oc = nc * o
    def off(p, v): return tuple(Vector(p) + v)
    fq([off(pt(0, -side * W, g0), na * o), off(pt(0, -side * CH, g0), na * o), off(pt(0, -side * CH, g1), na * o), off(pt(0, -side * W, g1), na * o)], 'br_guard', na)
    fq([off(pt(-s * W, 0, g0), nu * o), off(pt(-s * CH, 0, g0), nu * o), off(pt(-s * CH, 0, g1), nu * o), off(pt(-s * W, 0, g1), nu * o)], 'br_guard', nu)
    fq([off(pt(0, -side * CH, g0), na * o), off(pt(-s * CH, 0, g0), nu * o), off(pt(-s * CH, 0, g1), nu * o), off(pt(0, -side * CH, g1), na * o)], 'br_guard', nc)

# ------------------------------------------------------------ the wall's stuff and the damp, on the broad wall faces
CELL = {'outlet': (0, 0.5, 0.25, 1), 'switch': (0.25, 0.5, 0.5, 1), 'thermo': (0.5, 0.5, 0.75, 1), 'pull': (0.75, 0.5, 1, 1),
        'grille': (0, 0, 0.5, 0.5), 'sign': (0.5, 0, 1, 0.5)}
STAIN = {'tide': (0, 0.5, 0.5, 1), 'drip': (0.5, 0.5, 1, 1), 'mould': (0, 0, 0.5, 0.5), 'ring': (0.5, 0, 1, 0.5)}
counts = {}
WHERE = {}  # kind -> a few spots (for the pictures: -- --spots out.json)


def fixture(F, kind, uc, yc, w, h, d):
    c = CELL[kind]
    WHERE.setdefault(kind, []).append((F.P(uc, yc, 0), tuple(F.n())))
    uvs = [(c[0], 1 - c[1]), (c[2], 1 - c[1]), (c[2], 1 - c[3]), (c[0], 1 - c[3])]  # (the game loads the kit flipY: v runs down the image)
    # the corners as the face sees them from in front: left-to-right is +u when s, ua line up, else flipped
    right = 1 if (F.a == 2 and F.s > 0) or (F.a == 0 and F.s < 0) else -1
    ul, ur = uc - right * w / 2, uc + right * w / 2
    pts = [F.P(ul, yc - h / 2, d), F.P(ur, yc - h / 2, d), F.P(ur, yc + h / 2, d), F.P(ul, yc + h / 2, d)]
    K.quad(pts, 'br_fix', uv=uvs, flip=(Vector(pts[1]) - Vector(pts[0])).cross(Vector(pts[2]) - Vector(pts[0])).dot(F.n()) < 0)
    lo, hi = min(ul, ur), max(ul, ur)
    n = F.n(); ue = Vector([0, 0, 0]); ue[F.ua] = 1
    fq([F.P(lo, yc + h / 2, 0), F.P(hi, yc + h / 2, 0), F.P(hi, yc + h / 2, d), F.P(lo, yc + h / 2, d)], 'br_fixside', Vector((0, 1, 0)))
    fq([F.P(lo, yc - h / 2, 0), F.P(hi, yc - h / 2, 0), F.P(hi, yc - h / 2, d), F.P(lo, yc - h / 2, d)], 'br_fixside', Vector((0, -1, 0)))
    if d < 0.01: counts[kind] = counts.get(kind, 0) + 1; return  # (a plate: its edges are too thin to see)
    fq([F.P(lo, yc - h / 2, 0), F.P(lo, yc - h / 2, d), F.P(lo, yc + h / 2, d), F.P(lo, yc + h / 2, 0)], 'br_fixside', -ue)
    fq([F.P(hi, yc - h / 2, 0), F.P(hi, yc - h / 2, d), F.P(hi, yc + h / 2, d), F.P(hi, yc + h / 2, 0)], 'br_fixside', ue)
    counts[kind] = counts.get(kind, 0) + 1


def stain(F, kind, u0, u1, y0, y1, o, taken):
    if any(not (u1 < q[0] - 0.05 or u0 > q[1] + 0.05 or y1 < q[2] - 0.05 or y0 > q[3] + 0.05) for q in taken): return
    taken.append((u0, u1, y0, y1))
    WHERE.setdefault(kind, []).append((F.P(0.5 * (u0 + u1), 0.5 * (y0 + y1), 0), tuple(F.n())))
    c = STAIN[kind]
    if R.random() < 0.5: c = (c[2], c[1], c[0], c[3])  # (mirrored now and then)
    right = 1 if (F.a == 2 and F.s > 0) or (F.a == 0 and F.s < 0) else -1
    ul, ur = (u0, u1) if right > 0 else (u1, u0)
    pts = [F.P(ul, y0, o), F.P(ur, y0, o), F.P(ur, y1, o), F.P(ul, y1, o)]
    uvs = [(c[0], 1 - c[1]), (c[2], 1 - c[1]), (c[2], 1 - c[3]), (c[0], 1 - c[3])]
    K.quad(pts, 'br_stain', uv=uvs, flip=(Vector(pts[1]) - Vector(pts[0])).cross(Vector(pts[2]) - Vector(pts[0])).dot(F.n()) < 0)
    counts[kind] = counts.get(kind, 0) + 1


def tide(F, a, b, h, taken):
    """a tide mark: the wallpaper gone darker from the floor up to a wavy brown line (geometry, so the paper's
    pattern carries on through it)"""
    if any(not (b < q[0] - 0.05 or a > q[1] + 0.05 or h < q[2] - 0.05) for q in taken): return
    taken.append((a, b, 0, h + 0.06))
    n = F.n(); k = max(3, int((b - a) / 0.22)); ph = R.random() * 9
    hs = [h * (0.82 + 0.1 * math.sin(ph + i * 0.9) + 0.08 * math.sin(ph * 2.3 + i * 2.1)) for i in range(k + 1)]
    hs[0] *= 0.5; hs[-1] *= 0.5  # (it fades out at the ends)
    us = [a + (b - a) * i / k for i in range(k + 1)]
    for i in range(k):
        fq([F.P(us[i], SKH * 0.5, 0.003), F.P(us[i + 1], SKH * 0.5, 0.003), F.P(us[i + 1], hs[i + 1] - 0.022, 0.003), F.P(us[i], hs[i] - 0.022, 0.003)], 'br_tide', n)
        fq([F.P(us[i], hs[i] - 0.022, 0.003), F.P(us[i + 1], hs[i + 1] - 0.022, 0.003), F.P(us[i + 1], hs[i + 1], 0.003), F.P(us[i], hs[i], 0.003)], 'br_tideline', n)
    counts['tide'] = counts.get('tide', 0) + 1
    WHERE.setdefault('tide', []).append((F.P(0.5 * (a + b), h * 0.5, 0), tuple(n)))


def peel(F, us, y_top, w, L):
    """a strip of wallpaper come loose from the ceiling down, curling out into the room: bare drywall behind it"""
    n = F.n()
    ya = y_top - L
    slab(F, us, us + w, ya, y_top - 0.03, 0, 0.002, 'br_drywall', sides=False, top=False)
    TH = 1.3 + R.random() * 0.9   # how far it has curled (radians)
    rad = L / TH
    seg = 6
    rows = []
    for k in range(seg + 1):
        th = TH * k / seg
        y = ya + rad * math.sin(th); o = 0.003 + rad * (1 - math.cos(th))
        shrink = (k / seg) ** 1.5 * w * (0.15 + 0.25 * R.random())  # torn narrower toward the free end
        rows.append((y, o, us + shrink * 0.4, us + w - shrink * 0.6, ya + L * k / seg))
    flip = None
    for k in range(seg):
        (ya0, o0, l0, r0, yo0), (ya1, o1, l1, r1, yo1) = rows[k], rows[k + 1]
        q = [F.P(l0, ya0, o0), F.P(r0, ya0, o0), F.P(r1, ya1, o1), F.P(l1, ya1, o1)]
        # the printed side faces out (its pattern where it used to hang), the back faces the wall
        uv = [uv_of(n, F.P(l0, yo0)), uv_of(n, F.P(r0, yo0)), uv_of(n, F.P(r1, yo1)), uv_of(n, F.P(l1, yo1))]
        if flip is None: flip = (Vector(q[1]) - Vector(q[0])).cross(Vector(q[3]) - Vector(q[0])).dot(n) < 0  # (one winding for the whole curl)
        K.quad(q, 'br_wall', uv=uv, flip=flip)
        K.quad(q, 'br_back', flip=not flip)
    counts['peel'] = counts.get('peel', 0) + 1
    WHERE.setdefault('peel', []).append((F.P(us + w / 2, y_top - L / 2, 0), tuple(n)))


wallfaces = [(F, r) for F, rs in faces if F.thin for r in rs if r[2] - r[0] > 1.0]
R.shuffle(wallfaces)
for F, (u0, y0, u1, y1) in wallfaces:
    L = u1 - u0
    used = []  # (u0, u1, y0, y1) taken on this face
    damp = []  # the same for the stains (they lie under the fixtures, but not on each other or a peel)
    def free(a, b, c, d):
        return a > u0 + 0.12 and b < u1 - 0.12 and all(b < q[0] - 0.08 or a > q[1] + 0.08 or d < q[2] - 0.05 or c > q[3] + 0.05 for q in used)
    def take(kind, w, h, yc, d, u=None):
        for _ in range(4):
            uc = u if u is not None else u0 + 0.3 + R.random() * max(0.01, L - 0.6)
            if free(uc - w / 2, uc + w / 2, yc - h / 2, yc + h / 2):
                used.append((uc - w / 2, uc + w / 2, yc - h / 2, yc + h / 2)); fixture(F, kind, uc, yc, w, h, d); return True
            if u is not None: return False
        return False
    if y0 < 1e-3:
        # switches by the doorways: this face ends where its box ends and the end is open
        mn, mx = BX[F.bi]
        for end, uu, sg in ((0, F.u0, 1), (1, F.u1, -1)):
            if abs((u0 if end == 0 else u1) - uu) < 0.05 and R.random() < 0.2:
                if solid_at(F.P(uu - sg * 0.05, 1.2, -0.1), F.bi) is None: take('switch', 0.075, 0.12, 1.22, 0.008, uu + sg * 0.2)
        for _ in range(int(L / 3.6) + (1 if R.random() < (L % 3.6) / 3.6 else 0)):
            if R.random() < 0.16: take('outlet', 0.075, 0.12, 0.32, 0.008)
        if R.random() < 0.05 and L > 2: take('grille', 0.6, 0.3, 0.31, 0.012)
        if R.random() < 0.012: take('thermo', 0.09, 0.14, 1.5, 0.026)
        if R.random() < 0.006: take('pull', 0.11, 0.17, 1.25, 0.034)
        if R.random() < 0.006: take('sign', 0.3, 0.32, 1.55, 0.004)
        if R.random() < 0.12:  # a tide mark rising off the floor
            w = min(L - 0.1, 1.2 + R.random() * 2.3); a = u0 + 0.05 + R.random() * (L - 0.1 - w)
            tide(F, a, a + w, 0.35 + R.random() * 0.5, damp)
        elif R.random() < 0.03:
            s_ = 0.4 + R.random() * 0.6; a = u0 + 0.05 + R.random() * max(0.01, L - 0.1 - s_)
            stain(F, 'mould', a, a + s_, 0.05 + R.random() * 0.3, 0.05 + s_ * 0.8, 0.0012, damp)
    cy = ceil_at(*[F.front(0.5 * (u0 + u1), 1.0)[k] for k in (0, 2)])
    if abs(y1 - cy) < 1e-3 and y1 - y0 > 2.5:
        if R.random() < 0.08:  # drips down from the ceiling
            w = min(L - 0.1, 0.6 + R.random() * 0.9); a = u0 + 0.05 + R.random() * (L - 0.1 - w)
            stain(F, 'drip', a, a + w, cy - 0.8 - R.random() * 1.2, cy - 0.03, 0.0012, damp)
        elif R.random() < 0.03:
            s_ = 0.5 + R.random() * 0.7; a = u0 + 0.05 + R.random() * max(0.01, L - 0.1 - s_); yc = 2.2 + R.random() * (cy - 3.2)
            stain(F, 'ring', a, a + s_, yc, yc + s_ * 0.8, 0.0012, damp)
        if R.random() < 0.06 and L > 1.6:  # a strip peeling off at a seam
            seams = [k * 0.53 for k in range(int(math.ceil((u0 + 0.4) / 0.53)), int(math.floor((u1 - 0.95) / 0.53)) + 1)]
            if seams:
                us = R.choice(seams); w = 0.53 if R.random() < 0.6 else 0.26
                if free(us, us + w, cy - 1.4, cy) and all(us + w < q[0] - 0.05 or us > q[1] + 0.05 or q[3] < cy - 1.5 for q in damp): used.append((us, us + w, cy - 1.4, cy)); peel(F, us, cy - 0.03, w, 0.6 + R.random() * 0.7)
print('stuff', counts)
if '--spots' in argv:
    import json
    json.dump({k: v[:12] for k, v in WHERE.items()}, open(argv[argv.index('--spots') + 1], 'w'))

# ------------------------------------------------------------ a z-fight check that scales to the whole map (archkit's is
# pairwise per plane): a sweep along each plane
def zcheck_fast(limit=12):
    bad = 0
    for k, lst in getattr(K, '_planes', {}).items():
        lst = sorted(lst, key=lambda e: e[0][0])
        act = []
        for e in lst:
            act = [q for q in act if q[0][2] > e[0][0] + 0.002]
            for q in act:
                a, b = q[0], e[0]
                ox = min(a[2], b[2]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[1], b[1])
                if ox > 0.002 and oy > 0.002 and q[1] != e[1] and not ('(tri)' in q[1] and '(tri)' in e[1]) and {q[1], e[1]} != {'br_tide', 'br_tideline'}:  # (a tide band and its line only touch: their wavy quads' boxes overlap)
                    bad += 1
                    if bad <= limit: print('ZFIGHT', 'xyz'[k[0]], k[1], q[1], q[2], '<->', e[1], e[2])
            act.append(e)
    print('zfight pairs:', bad)
    return bad


K.zcheck = zcheck_fast
tris = sum(len(g['f']) * 2 for g in K.geo.values())
print('quads ~tris', tris)
out = os.path.join(OUTDIR, 'backrooms.glb')
K.finish(out, ao='--no-ao' not in argv)
