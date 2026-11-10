# Helicopter: JANK NEWS 7, tail number J-ANKY. An original light single-turbine news / utility helicopter with the
# proportions of the real ones (9.4 m pod-and-boom fuselage, 1.58 m cabin, 2.1 m skid track, a 9.8 m three-blade
# rotor on a short mast, a two-blade tail rotor on the left of a swept fin), then made fun. Front = +x, skids on y = 0,
# the origin on the ground under the rotor mast (so the game can yaw it about the origin).
#   body          empty: shell (lofted fuselage, cowl, fin, stabiliser, skids, aerials: materials heli_paint +
#                 heli_trim), glass (the see-through bubble, chin, door and roof windows: heli_glass), cabin (liner,
#                 floor, seats, console, pedals, a duck, fuzzy dice), lamps (landing + nav lights, the instrument
#                 screens: heli_glow), beacon (the red + white anti-collision lights, their own mesh so the game can
#                 blink them)
#   rotor_main    origin on the mast axis at the hub: mast, swashplate, pitch links, hub, grips, 3 blades (spin about y)
#   rotor_tail    origin on its hub: 2 striped blades (spin about z)
#   camera        the news camera ball under the nose, origin at its centre (tilt about z, pan about y)
#   searchlight   the belly searchlight drum, origin on its yoke pin (tilt about z)
#   lod1          empty: lod1_mesh (the whole airframe in ~400 triangles, windows painted on) + lod1_rotor_main +
#                 lod1_rotor_tail (origins on the same hubs)
# The fuselage is one loft (a cross-section per station: egg nose, slab-sided cabin, the belly sweeping up into a round
# boom); the windows are faces of that loft handed to the glass, so nothing floats or z-fights, with rubber gaskets on
# every pane edge and a liner 3 cm inside so the cabin has walls. Paint = one 512 x 256 livery map: each side seen
# straight on (so the writing reads on both), wrapped round the boom and over the cowl like a decal (square pixels from
# any angle), flat swatches where a face looks along the map (nose cap, keel), own patches for the belly and the
# stabiliser. Trim = one swatch atlas with a metal / roughness map, so the whole thing is 4 materials. Baked AO in the
# vertex colours (COLOR_0), like the round-4 map props. Not in a map yet and not wired into the game: the root's jf
# meta says where everything turns (rotors, camera, searchlight, blink).
# run: blender52 -b -P tools/blender/make_heli.py   -> public/models/p_heli.glb, sheets/p_heli.jpg (turnaround),
#      p_heli_lod1.jpg, p_heli_detail.jpg (close-ups), heli_hero.jpg (path traced). Blender 5.2; 4.0.2 builds it too.
#      flags after '--': --no-sheet --no-hero --no-export --no-ao  --qa (the asset-QA gate, per node)  --stats --parts
#      --preview=<dir> [--views=fl,side,cockpit,...] [--lod] (quick looks while iterating)  --hero-cam=x,y,z,tx,ty,tz,lens
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib
from bisect import bisect_right
import mathutils.kdtree

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
V3 = Vector
FID = 'p_heli'
PINK, YEL, CYAN, INK, WHITE = 0xff38c8, 0xffe14d, 0x4fd8ff, 0x1a0c22, 0xf6f2ea
G_DARK, G_MID = 0x14263a, 0x2f4f72  # the windows painted on the far model


def arg(k, d=None):
    for a in ARGV:
        if a.startswith('--' + k + '='): return a.split('=', 1)[1]
        if a == '--' + k: return True
    return d


# ------------------------------------------------------------ blender 5.x: no auto smooth, so sharp edges by angle
_SM = {}
_smooth0 = lib.smooth
def _smooth(o, angle=35):
    _smooth0(o, angle); _SM[o.name] = angle
    return o
lib.smooth = smooth = _smooth  # (lib's own primitives call it too)


def done(o, m):
    """a finished part: modifiers applied, edges sharper than its smooth angle split (a hardened bevel brings its own
    normals), one material"""
    apply_mods(o)
    me = o.data
    if hasattr(me, 'use_auto_smooth'): me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(_SM.get(o.name, 40))  # (blender 4.0)
    elif not me.has_custom_normals: me.set_sharp_from_angle(angle=math.radians(_SM.get(o.name, 40)))
    me.materials.clear(); me.materials.append(m)
    return o


# ------------------------------------------------------------ curves
def spline(pts):
    """smooth monotone curve through [(x, y)] (Fritsch-Carlson: no overshoot), clamped at the ends"""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; n = len(xs)
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


XN, XE, XT = 2.70, -6.40, -6.64  # nose tip, where the boom's end cap starts, the tail tip
def prof(pts):
    """a fuselage curve through [(x, value)], interpolated over sqrt(distance from the nose) so the nose comes out round"""
    f = spline(sorted((math.sqrt(max(0.0, XN - x)), v) for x, v in pts))
    return lambda x: f(math.sqrt(max(0.0, XN - x)))


# the fuselage, nose to tail: roof line, keel line, half width, the height of the widest point, how square the
# section is above / below it (2 = an ellipse, 3.4 = slab sides with a tight radius)
TOP = prof([(2.70, 1.06), (2.60, 1.33), (2.40, 1.59), (2.10, 1.845), (1.70, 2.06), (1.30, 2.185), (0.95, 2.235), (0.50, 2.25), (-0.50, 2.25),
            (-1.35, 2.21), (-1.95, 2.10), (-2.55, 1.995), (-2.85, 1.965), (-6.40, 1.94), (-6.64, 1.94)])
BOT = prof([(2.70, 1.06), (2.60, 0.885), (2.40, 0.765), (2.10, 0.675), (1.70, 0.625), (1.20, 0.61), (0.0, 0.60), (-1.05, 0.62), (-1.35, 0.70),
            (-1.65, 0.90), (-1.95, 1.15), (-2.25, 1.33), (-2.55, 1.425), (-2.85, 1.455), (-6.40, 1.69), (-6.64, 1.69)])
WID = prof([(2.70, 0.0), (2.60, 0.27), (2.40, 0.46), (2.10, 0.62), (1.70, 0.725), (1.20, 0.775), (0.50, 0.79), (-0.60, 0.785), (-1.05, 0.76),
            (-1.35, 0.70), (-1.65, 0.60), (-1.95, 0.48), (-2.25, 0.375), (-2.55, 0.30), (-2.85, 0.258), (-6.40, 0.125), (-6.64, 0.125)])
CYL = prof([(2.70, 1.06), (2.40, 1.10), (2.00, 1.16), (1.45, 1.21), (0.95, 1.22), (-1.05, 1.22), (-1.35, 1.30), (-1.95, 1.60), (-2.55, 1.705),
            (-2.85, 1.71), (-6.40, 1.815), (-6.64, 1.815)])
NT = prof([(2.70, 2.0), (2.00, 2.1), (0.95, 2.45), (-1.05, 2.5), (-1.95, 2.2), (-2.85, 2.0), (-6.64, 2.0)])
NB = prof([(2.70, 2.0), (2.00, 2.3), (1.20, 3.2), (-1.05, 3.4), (-1.65, 2.6), (-2.25, 2.1), (-2.85, 2.0), (-6.64, 2.0)])


def ring_pt(x, a):
    """the fuselage section at x: a = the angle round it from straight down toward +z (radians) -> (y, z)"""
    t, b, w, c = TOP(x), BOT(x), WID(x), CYL(x)
    s, co = math.sin(a), -math.cos(a)
    n = NT(x) if co > 0 else NB(x)
    z = w * math.copysign(abs(s) ** (2 / n), s)
    y = c + ((t - c) if co > 0 else (c - b)) * math.copysign(abs(co) ** (2 / n), co)
    k = 1.0 if x >= XE else math.sqrt(max(0.0, 1 - ((XE - x) / (XE - XT)) ** 2))  # the boom's rounded end
    return c + (y - c) * k, z * k


def hp(x, deg, off=0.0):
    """a point on the fuselage skin: station x, deg round from the keel (+ = the right side, +z), off metres out"""
    y, z = ring_pt(x, math.radians(abs(deg)))
    p = V3((x, y, z if deg >= 0 else -z))
    return p + hn(x, deg) * off if off else p


def hn(x, deg):
    e = 0.01
    du = hp(x + e, deg) - hp(x - e, deg); dv = hp(x, deg + 0.6) - hp(x, deg - 0.6)
    n = du.cross(dv)
    if n.dot(hp(x, deg) - V3((x, CYL(x), 0))) < 0: n = -n
    return n.normalized()


def hy(x, y, sg=1):
    """the point on the fuselage skin at station x and height y on one side (sg), and the normal there"""
    lo_, hi_ = 0.0, math.pi
    for _ in range(40):
        m = (lo_ + hi_) / 2
        if ring_pt(x, m)[0] < y: lo_ = m
        else: hi_ = m
    d = sg * math.degrees((lo_ + hi_) / 2)
    return hp(x, d), hn(x, d)


# the cowl (the doghouse on the roof: gearbox under the mast, the engine behind it)
CT = spline(sorted([(0.44, 2.25), (0.36, 2.33), (0.25, 2.43), (0.10, 2.54), (-0.10, 2.62), (-0.40, 2.66), (-0.80, 2.66), (-1.30, 2.61), (-1.70, 2.51),
                    (-2.05, 2.36), (-2.35, 2.20), (-2.60, 2.03)]))
CW = spline(sorted([(0.44, 0.05), (0.36, 0.13), (0.25, 0.20), (0.10, 0.30), (-0.10, 0.38), (-0.40, 0.44), (-0.80, 0.46), (-1.30, 0.44), (-1.70, 0.39),
                    (-2.05, 0.31), (-2.35, 0.21), (-2.60, 0.09)]))


def cowl_pt(x, a):
    """the cowl's arch at x: a from 0 (its +z foot, sunk in the roof) over the top to pi (the -z foot) -> (y, z)"""
    t, w = CT(x), CW(x); base = TOP(x) - 0.16
    c, s = math.cos(a), math.sin(a)
    return base + (t - base) * abs(s) ** (2 / 3.0), w * math.copysign(abs(c) ** (2 / 3.0), c)


# ------------------------------------------------------------ lofted skins
class Grid:
    """a skin through rows of game points (a row per station, the same count in each). A row of one repeated point is
    a tip. Rows nose to tail and each row from the keel up the +z side wind the faces outward."""
    def __init__(s, rows, cyclic=True):
        s.P = [[V3(p) for p in row] for row in rows]; s.n = len(rows); s.k = len(rows[0]); s.cyc = cyclic
        s.tip = [all((p - row[0]).length < 1e-7 for p in row) for row in s.P]
        s.nj = s.k if cyclic else s.k - 1
        acc = {}
        for r in range(s.n - 1):
            for j in range(s.nj):
                a, b, c, d = s.P[r][j % s.k], s.P[r][(j + 1) % s.k], s.P[r + 1][(j + 1) % s.k], s.P[r + 1][j % s.k]
                n = (c - a).cross(d - b)
                for q in s.quad(r, j): acc[q] = acc.get(q, V3()) + n
        s.N = {q: (v.normalized() if v.length > 1e-12 else V3((0, 1, 0))) for q, v in acc.items()}

    def key(s, r, j): return (r, 0) if s.tip[r] else (r, j % s.k)

    def quad(s, r, j):
        out = []
        for q in (s.key(r, j), s.key(r, j + 1), s.key(r + 1, j + 1), s.key(r + 1, j)):
            if q not in out: out.append(q)
        return out

    def pt(s, r, j, off=0.0):
        q = s.key(r, j)
        return s.P[q[0]][q[1]] + s.N[q] * off

    def nrm(s, r, j): return s.N[s.key(r, j)]

    def mesh(s, name, pick=None, off=0.0, flip=False):
        """the faces pick(row, slot) keeps (all of them without it), off metres out along the normals. s.faces = the
        (row, slot) of each polygon, in order"""
        bm = bmesh.new(); vs = {}; s.faces = []
        def v(q):
            if q not in vs: vs[q] = bm.verts.new(gv(*s.pt(q[0], q[1], off)))
            return vs[q]
        for r in range(s.n - 1):
            for j in range(s.nj):
                if pick and not pick(r, j): continue
                q = s.quad(r, j)
                if len(q) < 3: continue
                try: bm.faces.new([v(x) for x in (q[::-1] if flip else q)])
                except ValueError: pass
                else: s.faces.append((r, j))
        o = _obj(name, bm, None)
        for p in o.data.polygons: p.use_smooth = True
        _SM[o.name] = 80
        return o


def ribbon(name, P, N, hw=0.022, h=0.012, dip=0.004, closed=False):
    """a low arched bead along a path on a surface (window gaskets, rails): P = points, N = the surface normal at each.
    Its two edges dip into the surface, so it never floats and never lies flat on it."""
    P = [V3(p) for p in P]; n = len(P)
    if not closed:
        P[0] = P[0] - (P[1] - P[0]).normalized() * hw; P[-1] = P[-1] + (P[-1] - P[-2]).normalized() * hw
    bm = bmesh.new(); rows = []
    for i in range(n):
        a = P[i - 1] if (i > 0 or closed) else P[i]; b = P[(i + 1) % n] if (i < n - 1 or closed) else P[i]
        t = (b - a).normalized(); k = 1.0
        if closed or 0 < i < n - 1: k = 1 / max(0.6, (P[i] - a).normalized().dot(t))  # mitre: a corner keeps its width
        nn = (N[i] - t * N[i].dot(t)).normalized(); bb = t.cross(nn)
        rows.append([bm.verts.new(gv(*(P[i] - bb * hw * k - nn * dip))), bm.verts.new(gv(*(P[i] + nn * h))), bm.verts.new(gv(*(P[i] + bb * hw * k - nn * dip)))])
    for i in range(n if closed else n - 1):
        A_, B_ = rows[i], rows[(i + 1) % n]
        bm.faces.new((A_[0], A_[1], B_[1], B_[0])); bm.faces.new((A_[1], A_[2], B_[2], B_[1]))
    if not closed: bm.faces.new(rows[0][::-1]); bm.faces.new(rows[-1])
    o = _obj(name, bm, None)
    for p in o.data.polygons: p.use_smooth = True
    _SM[o.name] = 75
    return o


# ------------------------------------------------------------ UVs
def g_of(v): return V3((v.x, v.z, -v.y))  # blender -> game


def wpts(o):
    mw = o.matrix_basis
    return [g_of(mw @ v.co) for v in o.data.vertices]


def uv_data(o):
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    return me.uv_layers.active.data


def face_axis(n):
    ax = max(range(3), key=lambda i: abs(n[i]))
    return ax, (1 if n[ax] > 0 else -1)


def px_uv(rect, tex, s, t, m=1.0):
    """(s, t) in 0..1 inside a pixel rect (x, y from the top, w, h) of a tex (w, h) -> blender uv, m px inside"""
    x, y, w, h = rect[:4]
    return ((x + m + s * (w - 2 * m)) / tex[0], 1 - (y + m + (1 - t) * (h - 2 * m)) / tex[1])


def fix_uv(o):
    """faces whose UVs collapsed to a line (seen edge on by their projection) get a tiny triangle round their own
    middle: the same pixel, but nothing with zero UV area"""
    me = o.data; uv = me.uv_layers.active.data
    for pg in me.polygons:
        L_ = list(pg.loop_indices); P = [V3((uv[i].uv[0], uv[i].uv[1], 0)) for i in L_]
        ar = sum(P[k].x * P[(k + 1) % len(P)].y - P[(k + 1) % len(P)].x * P[k].y for k in range(len(P))) / 2
        if abs(ar) > 1e-8: continue
        c = sum(P, V3()) / len(P)
        for k, i in enumerate(L_):
            t = 2 * math.pi * k / len(L_); uv[i].uv = (c.x + 0.0006 * math.cos(t), c.y + 0.0006 * math.sin(t))
    return o


def uv_fill(o, rect, tex, m=1.0, keyfn=None):
    """every face into one pixel rect (a swatch, a pattern): box-projected over the part's own size. keyfn(face
    index) -> another rect for that face (blade tips, bands)"""
    me = o.data; uv = uv_data(o); rm = o.matrix_basis.to_3x3()
    pts = wpts(o)
    lo = V3([min(p[i] for p in pts) for i in range(3)]); ext = V3([max(p[i] for p in pts) for i in range(3)]) - lo
    for p in me.polygons:
        ax, _ = face_axis(g_of(rm @ p.normal))
        a, b = [(2, 1), (0, 2), (0, 1)][ax]
        rc = (keyfn(p.index) if keyfn else None) or rect
        for li in p.loop_indices:
            q = pts[me.loops[li].vertex_index]
            uv[li].uv = px_uv(rc, tex, (q[a] - lo[a]) / (ext[a] or 1), (q[b] - lo[b]) / (ext[b] or 1), m)
    return fix_uv(o)


def uv_decal(o, rect, tex, view='-x', m=0.5):
    """a picture straight onto a part as seen from one side (the instrument panel): right way up, not mirrored. Uses
    the part's own axes, so it can be turned afterwards."""
    me = o.data; uv = uv_data(o)
    pts = [g_of(v.co) for v in me.vertices]
    lo = V3([min(p[i] for p in pts) for i in range(3)]); ext = V3([max(p[i] for p in pts) for i in range(3)]) - lo
    a, sa, b = {'-x': (2, 1, 1), '+x': (2, -1, 1), '+z': (0, 1, 1), '-z': (0, -1, 1)}[view]
    for p in me.polygons:
        for li in p.loop_indices:
            q = pts[me.loops[li].vertex_index]
            s = (q[a] - lo[a]) / (ext[a] or 1); t = (q[b] - lo[b]) / (ext[b] or 1)
            uv[li].uv = px_uv(rect, tex, s if sa > 0 else 1 - s, t, m)
    return fix_uv(o)


# ------------------------------------------------------------ the livery map
class Paint:
    """the body paint: the right side seen from +z (R), the left from -z (L: mirrored, so writing reads), the belly
    from below (U) and the stabiliser from above (S), plus flat swatches. Draw in metres on each view's own plane:
    (x, y) on the sides, (x, z) under the belly, (z, x) on the stabiliser."""
    W, H = 512, 256
    X0, X1, Y0, Y1 = -7.05, 2.75, 0.50, 3.10
    UX0, UX1, UZ0, UZ1 = -1.15, 1.55, -0.5, 0.5
    SZ0, SZ1, SX0, SX1 = -1.06, 1.06, -5.02, -4.44
    R = {'R': (0, 0, 512, 112), 'L': (0, 112, 512, 112), 'U': (0, 224, 96, 32), 'S': (96, 224, 112, 32),
         'pink': (208, 224, 16, 16), 'yellow': (224, 224, 16, 16), 'cyan': (240, 224, 16, 16), 'ink': (256, 224, 16, 16), 'white': (272, 224, 16, 16)}
    SIDES = ('R', 'L')

    def __init__(s, name):
        s.px = np.zeros((s.H, s.W, 3), np.float32)
        s.img = bpy.data.images.new(name, s.W, s.H, alpha=False)

    def st(s, reg, a, b):
        if reg == 'R': return (a - s.X0) / (s.X1 - s.X0), (b - s.Y0) / (s.Y1 - s.Y0)
        if reg == 'L': return (s.X1 - a) / (s.X1 - s.X0), (b - s.Y0) / (s.Y1 - s.Y0)
        if reg == 'U': return (a - s.UX0) / (s.UX1 - s.UX0), (b - s.UZ0) / (s.UZ1 - s.UZ0)
        return (a - s.SZ0) / (s.SZ1 - s.SZ0), (b - s.SX0) / (s.SX1 - s.SX0)

    def pix(s, reg, a, b):
        u, v = s.st(reg, a, b); x, y, w, h = s.R[reg]
        return x + u * w, y + (1 - v) * h

    def uv(s, reg, p):
        if reg not in ('R', 'L', 'U', 'S'): x, y, w, h = s.R[reg]; return ((x + w / 2) / s.W, 1 - (y + h / 2) / s.H)  # a swatch: one flat colour
        a, b = (p[0], p[1]) if reg in s.SIDES else (p[0], p[2]) if reg == 'U' else (p[2], p[0])
        u, v = s.st(reg, a, b); x, y, w, h = s.R[reg]
        u = min(max(u, 0.5 / w), 1 - 0.5 / w); v = min(max(v, 0.5 / h), 1 - 0.5 / h)
        return ((x + u * w) / s.W, 1 - (y + (1 - v) * h) / s.H)

    def sub(s, reg):
        x, y, w, h = s.R[reg]
        return s.px[y:y + h, x:x + w]

    def mask(s, reg, pts):
        x, y, w, h = s.R[reg]
        q = [s.pix(reg, a, b) for a, b in pts]
        yy, xx = np.mgrid[y:y + h, x:x + w] + 0.5
        ins = np.zeros(yy.shape, bool)
        for i in range(len(q)):
            (x0, y0), (x1, y1) = q[i], q[i - 1]
            ins ^= ((y0 > yy) != (y1 > yy)) & (xx < (x1 - x0) * (yy - y0) / ((y1 - y0) or 1e-9) + x0)
        return ins

    def poly(s, regs, pts, col, hazard=None):
        for reg in regs:
            sub = s.sub(reg); ins = s.mask(reg, pts)
            sub[ins] = hexrgb(col)
            if hazard is not None:
                yy, xx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
                sub[ins & (((xx + yy) // 5) % 2 == 0)] = hexrgb(hazard)

    def line(s, regs, pts, col, w=1.0):
        for reg in regs:
            x, y = s.R[reg][:2]; sub = s.sub(reg)
            q = [s.pix(reg, a, b) for a, b in pts]
            for (x0, y0), (x1, y1) in zip(q, q[1:]): px_line(sub, x0 - x, y0 - y, x1 - x, y1 - y, col, w)

    def dots(s, regs, pts, col, step=3):
        """a dotted line (rivets): a pixel every step px along the path"""
        for reg in regs:
            x, y = s.R[reg][:2]; sub = s.sub(reg)
            q = [s.pix(reg, a, b) for a, b in pts]
            for (x0, y0), (x1, y1) in zip(q, q[1:]):
                n = max(1, int(round(max(abs(x1 - x0), abs(y1 - y0)) / step)))
                for i in range(n + 1):
                    cx, cy = int(x0 + (x1 - x0) * i / n - x), int(y0 + (y1 - y0) * i / n - y)
                    if 0 <= cy < sub.shape[0] and 0 <= cx < sub.shape[1]: sub[cy, cx] = hexrgb(col)

    def text(s, regs, a, b, st, scale, col, shadow=None, sh=1):
        for reg in regs:
            cx, cy = s.pix(reg, a, b); x, y, w, h = s.R[reg]; sub = s.sub(reg)
            tw = (len(st) * 6 - 1) * scale; th = 7 * scale
            x0 = int(round(cx - x - tw / 2)); y0 = int(round(cy - y - th / 2))
            assert x0 >= 0 and y0 >= 0 and x0 + tw + sh <= w and y0 + th + sh <= h, f'text {st!r} is off the {reg} map'
            if shadow is not None: text_px(sub, st, x0 + sh, y0 + sh, scale, shadow)
            text_px(sub, st, x0, y0, scale, col)

    def grain(s, amp=0.03, seed=5):
        """a faint crusty grain in 2 px blocks (three flat steps, so the png stays tiny)"""
        n = np.random.default_rng(seed).integers(0, 3, (s.H // 2, s.W // 2)) - 1
        s.px *= (1 + amp * np.kron(n, np.ones((2, 2))))[:, :, None]

    def write(s):
        a = np.ones((s.H, s.W, 4), np.float32); a[:, :, :3] = np.clip(s.px, 0, 1)[::-1]
        s.img.pixels.foreach_set(a.ravel()); s.img.file_format = 'PNG'; s.img.pack()


def uv_paint(o, mode=None):
    """body paint UVs: each face into the view its normal faces. mode(normal, centre, face index, side) can name
    another view or a swatch, or hand back its own point -> uv"""
    me = o.data; uv = uv_data(o); rm = o.matrix_basis.to_3x3()
    pts = wpts(o)
    for p in me.polygons:
        n = g_of(rm @ p.normal); c = sum((pts[i] for i in p.vertices), V3()) / len(p.vertices)
        side = 'R' if (n.z > 1e-4 or (abs(n.z) <= 1e-4 and c.z >= 0)) else 'L'
        reg = (mode(n, c, p.index, side) if mode else None) or side
        for li in p.loop_indices: q = pts[me.loops[li].vertex_index]; uv[li].uv = reg(q) if callable(reg) else PA.uv(reg, q)
    return fix_uv(o)


def boom_uv(side):
    """the boom's paint goes round it like a wrapped decal (its height on the map = the distance round the tube), so the
    registration keeps square pixels from above and below instead of smearing over the top"""
    def f(p):
        cy = CYL(p.x); R = math.hypot(p.y - cy, p.z)
        return PA.uv(side, V3((p.x, cy + R * math.atan2(p.y - cy, abs(p.z)) if R > 1e-6 else cy, p.z)))
    return f


# ------------------------------------------------------------ the trim atlas (64 x 64, 8 px cells) + its metal / roughness map
TEX_TRIM = (64, 64)
TRIM = {  # name: (x, y, w, h, colour, roughness, metallic)
    'black': (0, 0, 8, 8, 0x18181c, 0.35, 0.0), 'plastic': (8, 0, 8, 8, 0x2c2c33, 0.62, 0.0), 'rubber': (16, 0, 8, 8, 0x131316, 0.9, 0.0),
    'steel': (24, 0, 8, 8, 0x5c6068, 0.42, 0.75), 'chrome': (32, 0, 8, 8, 0xdde2ea, 0.1, 1.0), 'alu': (40, 0, 8, 8, 0xb9bfc8, 0.3, 0.9),
    'white': (48, 0, 8, 8, 0xf2f2ee, 0.35, 0.0), 'dark': (56, 0, 8, 8, 0x0a0a0c, 0.95, 0.0),
    'yellow': (0, 8, 8, 8, 0xffe14d, 0.3, 0.0), 'cyan': (8, 8, 8, 8, 0x4fd8ff, 0.28, 0.0), 'pink': (16, 8, 8, 8, 0xff4fd8, 0.3, 0.0),
    'red': (24, 8, 8, 8, 0xe8323c, 0.3, 0.0), 'blade': (32, 8, 8, 8, 0x2e3038, 0.5, 0.1), 'burnt': (40, 8, 8, 8, 0x74584a, 0.42, 0.9),
    'cabin': (48, 8, 8, 8, 0x756a8c, 0.8, 0.0), 'floor': (56, 8, 8, 8, 0x2a2333, 0.85, 0.0),
    'seat': (0, 16, 16, 16, 0x5a2a9c, 0.75, 0.0), 'dice': (16, 16, 16, 16, 0xff4fd8, 0.6, 0.0), 'grille': (32, 16, 16, 16, 0x101014, 0.5, 0.3),
    'louvre': (48, 16, 16, 16, 0x0e0e12, 0.55, 0.3),
    'stripe': (0, 32, 16, 16, 0xf2f2ee, 0.35, 0.0), 'hazard': (16, 32, 16, 8, 0xffd21a, 0.45, 0.0), 'lens': (32, 32, 16, 16, 0x16263c, 0.05, 0.8),
    'duck': (48, 32, 8, 8, 0xffd21a, 0.25, 0.0), 'beak': (56, 32, 8, 8, 0xff8a1a, 0.3, 0.0), 'gold': (16, 40, 8, 8, 0xffc23a, 0.2, 1.0),
    'lodglass': (24, 40, 8, 8, 0x1c3048, 0.08, 0.6),
}


def mat_trim(name):
    W, H = TEX_TRIM
    px = np.zeros((H, W, 3), np.float32); orm = np.ones((H, W, 3), np.float32)
    for k, (x, y, w, h, col, ro, me) in TRIM.items():
        px[y:y + h, x:x + w] = hexrgb(col); orm[y:y + h, x:x + w] = (1.0, ro, me)
    def cell(k):
        x, y, w, h = TRIM[k][:4]; return px[y:y + h, x:x + w]
    s = cell('seat')  # quilted purple with cyan piping
    for r in (3, 7, 11, 15): s[r, :] = hexrgb(0x42207a)
    for c in (2, 13): s[:, c] = hexrgb(CYAN)
    d = cell('dice'); d[0, :] = d[-1, :] = d[:, 0] = d[:, -1] = hexrgb(0xc02a9c)  # a five
    for cx, cy in ((4, 4), (11, 4), (7, 7), (4, 11), (11, 11)): d[cy:cy + 2, cx:cx + 2] = hexrgb(0xffffff)
    g = cell('grille'); yy, xx = np.mgrid[0:16, 0:16]  # woven intake screen
    g[((xx + yy) % 4 == 0) | ((xx - yy) % 4 == 0)] = hexrgb(0x4a4a56)
    lv = cell('louvre')
    for r in (2, 6, 10, 14): lv[r:r + 2, 1:15] = hexrgb(0x3c3c46)
    stp = cell('stripe')  # the tail rotor: red bands along the blade
    for r in (0, 8): stp[r:r + 4, :] = hexrgb(0xe8323c)
    hz = cell('hazard'); yy, xx = np.mgrid[0:8, 0:16]; hz[((xx + yy) // 3) % 2 == 0] = hexrgb(0x141414)
    ln = cell('lens')  # the camera's glass: rings and a glint
    px_disc(ln, 8, 8, 8.5, 0x0a0a0e); px_disc(ln, 8, 8, 6.5, 0x1c3050); px_disc(ln, 8, 8, 4.5, 0x0c1420); px_disc(ln, 8, 8, 2.5, 0x3a2a6a); px_disc(ln, 5.5, 5.5, 1.3, 0xbfe8ff)
    base = lib._image(name + '_t', np.clip(px, 0, 1))
    img = bpy.data.images.new(name + '_mr', W, H, alpha=False)
    a = np.ones((H, W, 4), np.float32); a[:, :, :3] = orm[::-1]
    img.pixels.foreach_set(a.ravel()); img.colorspace_settings.is_data = True; img.file_format = 'PNG'; img.pack()
    m = mat(name, 0xffffff, rough=0.5, tex=base)
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest'
    sp = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(t.outputs['Color'], sp.inputs['Color'])
    nt.links.new(sp.outputs['Green'], b.inputs['Roughness']); nt.links.new(sp.outputs['Blue'], b.inputs['Metallic'])
    return m


# the lights (one glowing atlas): flat lamp colours + the instrument panel
TEX_GLOW = (32, 32)
GLOW = {'white': (0, 0, 8, 8), 'red': (8, 0, 8, 8), 'green': (16, 0, 8, 8), 'strobe': (24, 0, 8, 8), 'panel': (0, 16, 32, 16)}


def mat_glow(name):
    def draw(px):
        for k, c in (('white', 0xfff0c8), ('red', 0xff2030), ('green', 0x39ff14), ('strobe', 0xffffff)):
            x, y, w, h = GLOW[k]; px[y:y + h, x:x + w] = hexrgb(c)
        p = px[16:32, 0:32]; p[:] = hexrgb(0x0b0b12)
        p[2:10, 2:13] = hexrgb(0x08303c)  # a moving map: coast, a route, you
        for i in range(2, 13): p[2 + (i * 5 // 9) % 7, i] = hexrgb(0x4fd8ff)
        px_line(p, 3, 8, 11, 3, 0xff4fd8, 1.0); p[5:7, 7:9] = hexrgb(0xffe14d)
        p[2:10, 19:30] = hexrgb(0x0c2410)  # engine page: green bars, one in the red
        for k_, hgt in enumerate((5, 6, 4, 6, 3)):
            p[9 - hgt:9, 20 + k_ * 2] = hexrgb(0x39ff14 if k_ != 2 else 0xff3030)
        for cx in (15.0, 16.5): px_disc(p, cx, 4.0 if cx < 16 else 8.0, 1.6, 0xf2f2ee, r_in=0.8)
        for k_, c in enumerate((0xff3030, 0xffa020, 0x39ff14, 0x4fd8ff, 0xff4fd8, 0xffe14d, 0xff3030, 0x39ff14)):
            p[12:14, 3 + k_ * 3:5 + k_ * 3] = hexrgb(c)  # the annunciator row
    img = tex_canvas(name + '_t', 32, 32, draw)
    return mat(name, 0xffffff, rough=0.25, emit=0xffffff, strength=2.2, tex=img, emit_tex=True)


def mat_glass(name, color=0x163646, alpha=0.36):
    """see-through tinted glass (blender 5: blended; 4.0: the old blend mode)"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(color); b.inputs['Alpha'].default_value = alpha
    b.inputs['Roughness'].default_value = 0.05; b.inputs['Metallic'].default_value = 0.5
    if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
    else: m.blend_method = 'BLEND'; m.shadow_method = 'HASHED'
    m['jf_color'] = color
    lib._mats[name] = m
    return m


M = {}; PA = None
def T(o, key='black', keyfn=None):  # a trim part on a swatch
    done(o, M['trim'])
    return uv_fill(o, TRIM[key][:4], TEX_TRIM, keyfn=(lambda i: TRIM[keyfn(i)][:4]) if keyfn else None)
def GL(o, key='white'): done(o, M['glow']); return uv_fill(o, GLOW[key], TEX_GLOW)
def PT(o, mode=None): done(o, M['paint']); return uv_paint(o, mode)
def PS(o, key): done(o, M['paint']); return uv_fill(o, PA.R[key], (PA.W, PA.H), m=3)


def turn(o, axis, deg, c=(0, 0, 0)):
    """bake a turn about a game axis through game point c into the mesh. y: + swings +x toward +z (the rotor's
    azimuth); z: + tips +y toward -x; x: + tips +y toward +z"""
    apply_mods(o)
    me = o.data; me.transform(o.matrix_basis); o.matrix_basis = Matrix.Identity(4)
    a = math.radians(deg)
    R_ = {'y': Matrix.Rotation(-a, 4, 'Z'), 'z': Matrix.Rotation(-a, 4, 'Y'), 'x': Matrix.Rotation(a, 4, 'X')}[axis]
    T_ = Matrix.Translation(gv(*c))
    me.transform(T_ @ R_ @ T_.inverted()); me.update()
    return o


def pipe(points, r, seg=6):
    """lib.tube with its end caps welded on (the curve's caps come with their own copies of the rim)"""
    o = tube(points, r, None, seg=seg)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(o.data); bm.free()
    return o


def stud(p, n, r, d0, d1, seg=10, bev=0.0):
    """a disc / post standing on a surface: from p + n * d0 to p + n * d1"""
    return rod(tuple(p + n * d0), tuple(p + n * d1), r, None, seg=seg, bev=bev)


# ------------------------------------------------------------ the fuselage
K = 32  # points round a section
XS = [2.70, 2.688, 2.655, 2.60, 2.52, 2.40, 2.22, 2.02, 1.82, 1.63, 1.45, 1.20, 0.95, 0.85, 0.55, 0.25, -0.05, -0.25, -0.65, -1.05, -1.35, -1.65,
      -1.95, -2.25, -2.55, -2.85, -3.75, -4.65, -5.55, -6.40, -6.52, -6.60, -6.64]
RI = {x: i for i, x in enumerate(XS)}
# the glass: (name, front x, rear x, first + last slot up one side). A slot is 11.25 degrees of the section, 0 at the
# keel, 8 = the first above the widest point, 15 = the last before the roof's centre line
WIN = [('wind', 2.40, 0.95, 8, 15), ('chin', 2.40, 1.45, 3, 6), ('door', 0.85, -0.05, 8, 12), ('sky', 0.85, 0.25, 13, 14), ('rear', -0.25, -1.05, 8, 11)]
LT, FLOOR, XFLOOR, XBULK = 0.03, 0.80, 1.45, -1.35  # liner thickness, cabin floor height, its front edge, the rear bulkhead
HUB, TRC, CAMC, SLC = (0.0, 3.00, 0.0), (-6.42, 1.83, -0.30), (2.33, 0.49, 0.0), (0.25, 0.42, -0.38)
SKZ = 1.05  # skid track / 2


def slot(j):
    j %= K
    return j if j < K // 2 else K - 1 - j


def wid(r, j):
    if r < 0 or r >= len(XS) - 1: return None
    s = slot(j)
    for nm, xa, xb, s0, s1 in WIN:
        if RI[xa] <= r < RI[xb] and s0 <= s <= s1: return nm
    return None


def is_glass(r, j): return wid(r, j) is not None


def frame_runs():
    """the pane edges as paths along the loft's own lines: every edge with glass on one side and something else on the
    other (paint, or another window)"""
    runs = []; nr = len(XS)
    for j in range(K):  # along the fuselage: the edge row r -> r + 1 at j parts faces (r, j - 1) and (r, j)
        r = 0
        while r < nr - 1:
            if wid(r, j - 1) != wid(r, j):
                r0 = r
                while r < nr - 1 and wid(r, j - 1) != wid(r, j): r += 1
                runs.append([(q, j) for q in range(r0, r + 1)])
            else: r += 1
    for r in range(1, nr - 1):  # round it: the edge j -> j + 1 on row r parts faces (r - 1, j) and (r, j)
        fl = [wid(r - 1, j) != wid(r, j) for j in range(K)]
        if not any(fl) or r == RI[2.40]: continue  # (the nose cap's joint gets a whole ring instead)
        j = fl.index(False) + 1; end = j + K
        while j < end:
            if fl[j % K]:
                a = j
                while fl[j % K]: j += 1
                runs.append([(r, q) for q in range(a, j + 1)])
            else: j += 1
    return runs


def build():
    global PA
    PA = Paint('heli_paint_t')
    M.update(paint=mat('heli_paint', PINK, rough=0.26, metal=0.08, clearcoat=1.0, tex=PA.img), trim=mat_trim('heli_trim'),
             glass=mat_glass('heli_glass'), glow=mat_glow('heli_glow'))
    SHELL, GLASS, CABIN, LAMPS, BEACON, RMAIN, RTAIL, CAM, SLITE = [], [], [], [], [], [], [], [], []
    S = SHELL.append

    # ================================================== the hull: one loft, the windows are its own faces
    H = Grid([[V3((x,) + ring_pt(x, 2 * math.pi * j / K)) for j in range(K)] for x in XS])
    hull = H.mesh('hull', lambda r, j: not is_glass(r, j)); hf = H.faces
    def hull_view(n, c, i, side):
        r, j = hf[i]
        if r < RI[2.40]: return 'yellow'  # the nose cap faces forward: a side-on map would smear across it
        if r >= RI[-2.85]: return boom_uv(side)
        if slot(j) <= 2 and XS[r + 1] > -2.3: return 'U' if (n.y < -0.85 and abs(c.z) < 0.47 and -1.1 < c.x < 1.5) else 'ink'  # the keel (HI MOM in the middle)
    S(PT(hull, hull_view))
    g = done(H.mesh('canopy', is_glass), M['glass'])
    uv = uv_data(g)
    for p, q in zip([lp.vertex_index for lp in g.data.loops], uv): c = g_of(g.data.vertices[p].co); q.uv = ((c.x + 2) / 5, (c.y + abs(c.z) * 0.3) / 3)
    GLASS.append(fix_uv(g))
    # gaskets on every pane edge, a fatter centre post down the bubble
    for run in frame_runs():
        S(T(ribbon('gasket', [H.pt(r, j) for r, j in run], [H.nrm(r, j) for r, j in run]), 'rubber'))
    ring = [(RI[2.40], j) for j in range(K)]
    S(T(ribbon('gasket', [H.pt(r, j) for r, j in ring], [H.nrm(r, j) for r, j in ring], closed=True), 'rubber'))
    for sg in (1, -1):  # a cyan rub strip where the dark keel starts
        bead = [(r, 3 * sg) for r in range(RI[2.40], RI[-2.25] + 1)]
        S(T(ribbon('bead', [H.pt(r, j) for r, j in bead], [H.nrm(r, j) for r, j in bead], hw=0.015, h=0.011), 'cyan'))
    post = [(r, K // 2) for r in range(RI[2.40], RI[0.95] + 1)]
    S(T(ribbon('post', [H.pt(r, j) for r, j in post], [H.nrm(r, j) for r, j in post], hw=0.034, h=0.02), 'rubber'))
    # the rear doors slide back: a level track behind each, above and below the window
    for sg in (1, -1):
        for y, xs in ((1.235, (-1.09, -1.22, -1.36, -1.50)), (2.045, (-1.09, -1.26, -1.44, -1.62))):
            pn_ = [hy(x, y, sg) for x in xs]
            S(T(ribbon('rail', [q[0] for q in pn_], [q[1] for q in pn_], hw=0.014, h=0.013), 'steel'))

    # ================================================== the cabin: a liner 3 cm inside the skin, pane reveals, floor, bulkhead
    rb, rf = RI[XBULK], RI[XFLOOR]
    def liner_pick(r, j):
        if r >= rb or is_glass(r, j): return False
        if XS[r + 1] >= XFLOOR - 1e-6: return True  # the nose and the footwell: all of it (you see in through the chin)
        return max(H.pt(*q).y for q in H.quad(r, j)) > FLOOR - 0.005  # behind that, only what's above the floor
    liner = T(H.mesh('liner', liner_pick, off=-LT, flip=True), 'cabin')
    bm = bmesh.new()
    for r in range(len(XS) - 1):
        for j in range(K):
            if not is_glass(r, j): continue
            cen = sum((H.pt(*q) for q in H.quad(r, j)), V3()) / 4
            for a, b, nb in (((r, j), (r, j + 1), (r - 1, j)), ((r, j + 1), (r + 1, j + 1), (r, j + 1)), ((r + 1, j + 1), (r + 1, j), (r + 1, j)), ((r + 1, j), (r, j), (r, j - 1))):
                if is_glass(*nb): continue
                f = [H.pt(*a), H.pt(*b), H.pt(*b, -LT), H.pt(*a, -LT)]
                if (f[1] - f[0]).cross(f[3] - f[0]).dot(cen - f[0]) < 0: f.reverse()
                bm.faces.new([bm.verts.new(gv(*p)) for p in f])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    rv = _obj('reveal', bm, None); _SM[rv.name] = 30
    for p in rv.data.polygons: p.use_smooth = True
    lr = join([liner, T(rv, 'plastic')], 'liner')  # one welded shell: the reveals share the liner's edge
    bm = bmesh.new(); bm.from_mesh(lr.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(lr.data); bm.free()
    if not hasattr(lr.data, 'use_auto_smooth'): lr.data.set_sharp_from_angle(angle=math.radians(35))
    CABIN.append(lr)
    inner = lambda r: [H.pt(r, j, -LT) for j in range(K)]
    def zfloor(r):  # the liner's half width at floor height
        q = inner(r)
        for j in range(K // 4):
            if q[j].y <= FLOOR <= q[j + 1].y: t = (FLOOR - q[j].y) / ((q[j + 1].y - q[j].y) or 1); return q[j].z + (q[j + 1].z - q[j].z) * t, j
        return q[0].z, 0
    bm = bmesh.new()
    row = []
    for r in range(rf, rb + 1):
        z, _ = zfloor(r); row.append((bm.verts.new(gv(XS[r], FLOOR, z + 0.012)), bm.verts.new(gv(XS[r], FLOOR, -z - 0.012))))
    for a, b in zip(row, row[1:]): bm.faces.new((a[0], a[1], b[1], b[0]))
    z, jc = zfloor(rf); q = inner(rf)  # the kick wall at the floor's front edge, down to the liner
    kick = [V3((XFLOOR, FLOOR, z))] + [q[j] for j in range(jc, -1, -1)] + [q[K - j] for j in range(1, jc + 1)] + [V3((XFLOOR, FLOOR, -z))]
    bm.faces.new([bm.verts.new(gv(*p)) for p in kick])
    bm.faces.new([bm.verts.new(gv(*p)) for p in inner(rb)])  # the rear bulkhead
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    fl = _obj('floor', bm, None); _SM[fl.name] = 30
    me = fl.data
    for p in me.polygons:  # recalc guesses on open sheets: the floor looks up, the walls look forward
        want = V3((0, 0, 1)) if abs(p.normal.z) > 0.5 else V3((1, 0, 0))
        if p.normal.dot(want) < 0: p.flip()
    CABIN.append(T(fl, 'floor'))
    C = lambda o, key: CABIN.append(T(o, key))
    for z in (0.36, -0.36):  # two front seats
        C(box((0.44, 0.22, 0.44), (0.50, 0.90, z), None), 'plastic')
        C(box((0.46, 0.10, 0.46), (0.50, 1.05, z), None, bev=0.03, seg=1), 'seat')
        C(box((0.11, 0.68, 0.46), (0.235, 1.41, z), None, bev=0.035, seg=1, rot=(0, 0, 0.15)), 'seat')
        C(box((0.08, 0.17, 0.24), (0.165, 1.83, z), None, bev=0.028, seg=1, rot=(0, 0, 0.15)), 'seat')
        C(rod((0.88, 0.79, z), (0.80, 1.20, z), 0.013, None, seg=6), 'black')  # cyclic
        C(box((0.035, 0.10, 0.04), (0.795, 1.24, z), None, bev=0.01, seg=1, rot=(0, 0, 0.2)), 'plastic')
        C(rod((0.22, 0.86, z - 0.27), (0.64, 1.04, z - 0.27), 0.014, None, seg=6), 'black')  # collective
        C(box((0.11, 0.045, 0.045), (0.67, 1.05, z - 0.27), None, bev=0.012, seg=1, rot=(0, 0, 0.4)), 'yellow')
        for dz in (-0.075, 0.075):  # pedals out in the footwell, behind the chin glass
            C(rod((1.74, 0.80, z + dz), (1.90, 0.86, z + dz), 0.011, None, seg=5), 'steel')
            C(box((0.03, 0.11, 0.085), (1.905, 0.885, z + dz), None, bev=0.008, seg=1, rot=(0, 0, 0.45)), 'alu')
    C(box((0.46, 0.22, 1.20), (-0.85, 0.90, 0), None), 'plastic')  # the back bench
    C(box((0.48, 0.10, 1.24), (-0.85, 1.05, 0), None, bev=0.03, seg=1), 'seat')
    C(box((0.11, 0.66, 1.24), (-1.14, 1.40, 0), None, bev=0.035, seg=1, rot=(0, 0, 0.1)), 'seat')
    C(box((0.50, 0.50, 0.26), (1.52, 0.90, 0), None, bev=0.02, seg=1), 'plastic')  # console: pedestal, panel, glareshield
    C(box((0.16, 0.34, 0.76), (1.72, 1.27, 0), None, bev=0.022, seg=1, rot=(0, 0, -0.22)), 'plastic')
    C(box((0.30, 0.035, 0.84), (1.71, 1.455, 0), None, bev=0.012, seg=1, rot=(0, 0, -0.06)), 'black')
    pn = box((0.014, 0.30, 0.70), (0, 0, 0), None)
    done(pn, M['glow']); uv_decal(pn, GLOW['panel'], TEX_GLOW, '-x')
    pn.location = gv(1.72 - 0.086 * math.cos(0.22), 1.27 + 0.086 * math.sin(0.22), 0); pn.rotation_euler = Euler((0, 0.22, 0), 'YZX')
    LAMPS.append(pn)
    C(ball(0.05, (1.70, 1.515, 0.25), None, scale=(1.25, 0.85, 1.0), seg=8, rings=5), 'duck')  # the co-pilot
    C(ball(0.032, (1.742, 1.575, 0.25), None, seg=8, rings=5), 'duck')
    C(box((0.034, 0.012, 0.028), (1.778, 1.57, 0.25), None), 'beak')
    for k, (dx, dy, dz, rz) in enumerate(((0.03, -0.27, 0.045, 0.5), (0.0, -0.33, -0.05, 1.1))):  # fuzzy dice off the centre post
        top = V3((0.99, TOP(0.99) - LT - 0.01, 0)); c = top + V3((dx, dy, dz))
        C(rod(tuple(top + V3((0, 0.03, 0))), tuple(c), 0.004, None, seg=3), 'white')
        C(box((0.085, 0.085, 0.085), tuple(c - V3((0, 0.03, 0))), None, bev=0.01, seg=1, rot=(0.3 * (1 - 2 * k), rz, 0.25)), 'dice')

    # ================================================== the cowl: gearbox + engine doghouse on the roof
    CXS = [0.44, 0.36, 0.25, 0.10, -0.10, -0.40, -0.80, -1.30, -1.70, -2.05, -2.35, -2.60]
    MC = 11
    rows = []
    for x in CXS:
        if x in (CXS[0], CXS[-1]): rows.append([V3((x, TOP(x) - 0.03, 0))] * MC)
        else: rows.append([V3((x,) + cowl_pt(x, math.pi * k / (MC - 1))) for k in range(MC)])
    CG = Grid(rows, cyclic=False)
    vent = lambda r, k, xa: CXS[r] == xa and k in (1, 2, MC - 4, MC - 3)
    yun = {}  # each cowl point's height on the paint map = its foot's height + the distance up the arch from there (the nearer foot)
    for row in CG.P:
        for k in range(MC):
            st_ = 1 if k <= MC // 2 else -1; k0 = 0 if st_ > 0 else MC - 1
            yun[tuple(round(c, 3) for c in row[k])] = row[0].y + sum((row[i + st_] - row[i]).length for i in range(k0, k, st_))
    def cowl_view(n, c, i, side):
        def f(q):
            k_ = tuple(round(c_, 3) for c_ in q)
            if k_ not in yun: k_ = min(yun, key=lambda t: (V3(t) - q).length)
            return PA.uv(side, V3((q.x, yun[k_], q.z)))
        return f
    S(PT(CG.mesh('cowl', lambda r, k: not vent(r, k, -0.10) and not vent(r, k, -1.70)), cowl_view))
    S(T(CG.mesh('intake', lambda r, k: vent(r, k, -0.10)), 'grille'))
    S(T(CG.mesh('louvre', lambda r, k: vent(r, k, -1.70)), 'louvre'))
    for xa in (-0.10, -1.70):  # a raised frame round each
        r0 = CXS.index(xa)
        for k0 in (1, MC - 4):
            loop = [(r0, k0), (r0, k0 + 1), (r0, k0 + 2), (r0 + 1, k0 + 2), (r0 + 1, k0 + 1), (r0 + 1, k0)]
            S(T(ribbon('ventframe', [CG.pt(*q) for q in loop], [CG.nrm(*q) for q in loop], hw=0.011, h=0.01, closed=True), 'steel' if xa > -1 else 'black'))
    for z in (0.14, -0.14):  # twin exhaust stacks, hollow, leaning back
        S(T(lathe([(0.0, 0.0), (0.078, 0.0), (0.078, 0.36), (0.07, 0.375), (0.06, 0.36), (0.06, 0.24), (0.0, 0.24)], (-1.42, 2.46, z), None, seg=12, axis='y', rot=(0, 0, 0.38)), 'burnt'))
    S(T(ball(0.07, (-0.95, CT(-0.95) - 0.005, 0), None, scale=(1, 0.42, 1), seg=10, rings=5), 'white'))  # gps puck
    xs = [-2.62, -3.2, -4.0, -4.8, -5.6, -6.2, -6.34]  # the tail rotor drive shaft's cover along the boom's back
    S(PT(sweep([(x, TOP(x) + 0.004, 0) for x in xs], [0.052] * 5 + [0.045, 0.02], None, seg=6, smooth_angle=70)))
    # mast boot + the fixed swashplate ring
    S(T(lathe([(0.15, 2.52), (0.155, 2.585), (0.12, 2.61), (0.145, 2.64), (0.11, 2.67), (0.13, 2.70), (0.095, 2.73), (0.095, 2.745), (0.0, 2.745)], (0, 0, 0), None, seg=12, axis='y', cap=False), 'rubber'))
    S(T(cyl(0.165, 0.028, (0, 2.757, 0), None, axis='y', seg=14), 'steel'))

    # ================================================== tail: fin, tail skid, gearbox, stabiliser
    FIN = [(-5.70, 1.12), (-5.80, 1.04), (-6.00, 1.04), (-6.63, 1.80), (-6.98, 2.92), (-6.92, 3.04), (-6.62, 3.06), (-6.00, 1.84)]
    S(PT(side_x(FIN, 0.07, (0, 0, 0.02), None, bev=0.026, seg=2, name='fin')))
    S(T(pipe([(-5.78, 1.10, 0.02), (-5.98, 0.90, 0.02), (-6.22, 0.80, 0.02)], 0.02), 'steel'))  # tail skid
    S(T(ball(0.034, (-6.23, 0.80, 0.02), None, seg=8, rings=5), 'rubber'))
    S(T(cyl(0.088, 0.25, (TRC[0], TRC[1], -0.125), None, axis='z', seg=12, bev=0.014), 'steel'))  # the 90 degree gearbox
    S(T(cyl(0.032, 0.09, (TRC[0], TRC[1], -0.26), None, axis='z', seg=8), 'chrome'))
    AF = [(0.22, 0.0), (0.16, 0.022), (0.03, 0.027), (-0.22, 0.005), (-0.22, -0.005), (0.03, -0.019), (0.16, -0.019)]  # upside-down aerofoil: it pushes the tail down
    sx, sy = -4.73, 1.752
    S(PS(side_x([(sx + a, sy + b) for a, b in AF], 2.0, (0, 0, 0), None, bev=0.004, seg=1, name='stab'), 'pink'))
    st = SHELL[-1]; uvd = uv_data(st); pts = wpts(st)  # its top: the NO STEP patch
    for p in st.data.polygons:
        if g_of(p.normal).y > 0.6:
            for li in p.loop_indices: uvd[li].uv = PA.uv('S', pts[st.data.loops[li].vertex_index])
    for sg in (1, -1):
        S(PS(side_x([(-4.47, 1.60), (-4.92, 1.60), (-5.05, 1.96), (-4.74, 1.96)], 0.035, (0, 0, sg * 1.0), None, bev=0.012, seg=2, name='endplate'), 'cyan'))
        L_ = ball(0.035, (-4.72, 1.80, sg * 1.02), None, scale=(1.6, 1, 0.8), seg=8, rings=5)
        LAMPS.append(GL(L_, 'green' if sg > 0 else 'red'))  # nav lights: green right, red left
    LAMPS.append(GL(ball(0.03, (XT - 0.004, CYL(XT), 0), None, seg=8, rings=5), 'strobe'))  # white tail light
    S(T(cyl(0.04, 0.03, (-6.77, 3.062, 0.02), None, axis='y', seg=10), 'black'))  # beacons: fin top (red), belly (white)
    BEACON.append(GL(ball(0.042, (-6.77, 3.09, 0.02), None, scale=(1, 1.15, 1), seg=8, rings=5), 'red'))
    pb = hp(-0.20, 0)
    S(T(cyl(0.045, 0.02, (pb.x, pb.y - 0.006, 0), None, axis='y', seg=10), 'black'))
    BEACON.append(GL(ball(0.038, (pb.x, pb.y - 0.022, 0), None, scale=(1, 0.9, 1), seg=8, rings=5), 'strobe'))

    # ================================================== skids: two tubes with upturned toes on two arched cross tubes
    for sg in (1, -1):
        z = sg * SKZ
        S(T(sweep([(-1.60, 0.045, z), (-0.6, 0.045, z), (0.6, 0.045, z), (1.50, 0.045, z), (1.76, 0.062, z), (1.95, 0.115, z), (2.08, 0.21, z), (2.14, 0.33, z)], 0.045, None, seg=8), 'cyan'))
        S(T(ball(0.047, (2.14, 0.335, z), None, seg=8, rings=5), 'black'))  # toe cap
        S(T(box((0.5, 0.012, 0.07), (0.1, 0.004 + 0.002, z), None), 'steel'))  # wear shoe
        S(T(box((0.52, 0.03, 0.15), (0.42, 0.335, sg * 0.955), None, bev=0.008, seg=1), 'hazard'))  # boarding step
        for x in (0.22, 0.62): S(T(rod((x, 0.07, z), (x, 0.325, sg * 0.955), 0.014, None, seg=6), 'steel'))
    for x in (1.00, -0.75):
        arch = [(-SKZ, 0.05), (-1.02, 0.17), (-0.93, 0.35), (-0.78, 0.505), (-0.58, 0.60), (-0.30, 0.648), (0.0, 0.66)]
        arch = arch + [(-z, y) for z, y in arch[-2::-1]]
        S(T(sweep([(x, y, z) for z, y in arch], 0.038, None, seg=8), 'cyan'))
        for sg in (1, -1):
            S(T(box((0.13, 0.085, 0.115), (x, 0.062, sg * SKZ), None, bev=0.012, seg=1), 'steel'))  # skid saddle
            S(T(box((0.15, 0.06, 0.13), (x, 0.618, sg * 0.44), None, bev=0.012, seg=1, rot=(sg * 0.2, 0, 0)), 'black'))  # where it goes into the belly

    # ================================================== the fiddly real bits
    for sg in (1, -1):
        for x in (-0.08, -0.225):  # door handles either side of the shut line (front doors hinge at the front, rear doors slide back)
            p = hp(x, sg * 83)
            S(T(box((0.11, 0.036, 0.03), (p.x, p.y, p.z + sg * 0.012), None, bev=0.008, seg=1), 'black'))
        for dg in (100, 132):  # front door hinges on the pillar
            p = hp(0.90, sg * dg, 0.008); up = (hp(0.90, sg * (dg + 4)) - hp(0.90, sg * (dg - 4))).normalized()
            S(T(rod(tuple(p - up * 0.032), tuple(p + up * 0.032), 0.013, None, seg=6), 'steel'))
        p = hp(2.53, sg * 52); n = hn(2.53, sg * 52)  # landing lights in the nose
        S(T(stud(p, n, 0.072, -0.03, 0.012, seg=12), 'chrome'))
        LAMPS.append(GL(stud(p, n, 0.056, 0.0, 0.019, seg=12), 'white'))
    p = hp(-1.45, 68); n = hn(-1.45, 68)
    S(T(stud(p, n, 0.055, -0.02, 0.008, seg=10), 'chrome'))  # fuel cap
    p0 = hp(2.50, 142); n0 = hn(2.50, 142)  # pitot tube
    S(T(pipe([tuple(p0 - n0 * 0.01), tuple(p0 + n0 * 0.075), tuple(p0 + n0 * 0.075 + V3((0.24, 0.0, 0)))], 0.011), 'chrome'))
    S(T(side_x([(1.00, 2.20), (0.60, 2.215), (0.64, 2.30), (1.04, 2.50), (1.075, 2.455)], 0.026, (0, 0, 0), None, bev=0.007, seg=1, name='cutter'), 'steel'))  # wire cutter
    S(T(side_x([(-0.50, 0.615), (-0.74, 0.615), (-0.82, 0.39), (-0.74, 0.39)], 0.014, (0, 0, 0), None, bev=0.004, seg=1, name='blade_ant'), 'white'))  # comm aerials
    S(T(side_x([(-3.10, 1.94), (-3.34, 1.94), (-3.43, 2.21), (-3.35, 2.21)], 0.014, (0, 0, 0), None, bev=0.004, seg=1, name='blade_ant'), 'white'))
    pr = hp(-3.30, 0)  # the microwave dish pod under the boom (it's a news ship)
    S(T(rod((pr.x, pr.y + 0.02, 0), (pr.x, pr.y - 0.11, 0), 0.03, None, seg=8), 'steel'))
    S(T(lathe([(0.0, -0.05), (0.13, -0.043), (0.21, -0.014), (0.21, 0.014), (0.13, 0.043), (0.0, 0.05)], (pr.x, pr.y - 0.14, 0), None, seg=12, axis='y'), 'white'))
    S(T(lathe([(0.212, -0.012), (0.218, 0.0), (0.212, 0.012)], (pr.x, pr.y - 0.14, 0), None, seg=12, axis='y', cap=False), 'cyan'))
    tr = [hp(x, 58, 0.075) for x in (-3.15, -3.85, -4.55, -5.25)]  # towel-rail aerial down the boom's right side
    S(T(pipe([tuple(hp(-3.07, 58, -0.005))] + [tuple(p) for p in tr] + [tuple(hp(-5.33, 58, -0.005))], 0.008, seg=5), 'alu'))
    for x in (-3.85, -4.55): S(T(rod(tuple(hp(x, 58, -0.005)), tuple(hp(x, 58, 0.075)), 0.007, None, seg=5), 'black'))

    # ================================================== the news camera: a gimbal ball in a yoke under the nose
    cb = V3(CAMC); bt = BOT(cb.x)
    S(T(cyl(0.105, bt + 0.04 - 0.655, (cb.x, (bt + 0.04 + 0.655) / 2, 0), None, axis='y', seg=14, bev=0.012), 'plastic'))
    S(T(box((0.10, 0.03, 0.40), (cb.x, 0.655, 0), None, bev=0.008, seg=1), 'plastic'))
    for sg in (1, -1): S(T(box((0.085, 0.20, 0.03), (cb.x, 0.565, sg * 0.187), None, bev=0.01, seg=1), 'plastic'))
    S(T(cyl(0.022, 0.40, (cb.x, cb.y, 0), None, axis='z', seg=8), 'chrome'))
    CAM.append(T(ball(0.16, CAMC, None, seg=12, rings=8), 'white'))
    CAM.append(T(cyl(0.085, 0.06, (cb.x + 0.135, cb.y - 0.015, 0), None, axis='x', seg=14, bev=0.008), 'black'))
    ln = cyl(0.068, 0.012, (0, 0, 0), None, axis='x', seg=14)
    done(ln, M['trim']); uv_decal(ln, TRIM['lens'][:4], TEX_TRIM, '+x'); ln.location = gv(cb.x + 0.168, cb.y - 0.015, 0)
    CAM.append(ln)
    CAM.append(T(cyl(0.032, 0.05, (cb.x + 0.13, cb.y + 0.075, 0.07), None, axis='x', seg=8, bev=0.004), 'black'))
    CAM.append(T(cyl(0.022, 0.008, (cb.x + 0.158, cb.y + 0.075, 0.07), None, axis='x', seg=8), 'cyan'))

    # ================================================== the searchlight under the belly
    sc = V3(SLC)
    S(T(rod((sc.x, 0.665, sc.z), (sc.x, 0.555, sc.z), 0.028, None, seg=8), 'steel'))
    S(T(box((0.05, 0.025, 0.31), (sc.x, 0.555, sc.z), None, bev=0.006, seg=1), 'steel'))
    for sg in (1, -1): S(T(box((0.045, 0.15, 0.022), (sc.x, 0.49, sc.z + sg * 0.139), None, bev=0.006, seg=1), 'steel'))
    SLITE.append(T(lathe([(0.0, -0.11), (0.07, -0.10), (0.105, -0.05), (0.115, 0.07), (0.115, 0.105), (0.10, 0.105), (0.095, 0.085), (0.0, 0.085)], tuple(sc), None, seg=14, axis='x'), 'black'))
    SLITE.append(T(lathe([(0.116, 0.074), (0.123, 0.09), (0.116, 0.106)], tuple(sc), None, seg=14, axis='x', cap=False), 'chrome'))
    SLITE.append(T(cyl(0.02, 0.316, tuple(sc), None, axis='z', seg=6), 'chrome'))
    SLITE.append(GL(cyl(0.094, 0.01, (sc.x + 0.086, sc.y, sc.z), None, axis='x', seg=14), 'white'))  # its lens glows (heli_glow)

    # ================================================== main rotor: mast, swashplate, 3 x (arm, grip, pitch link, blade)
    hub = V3(HUB)
    RM = RMAIN.append
    RM(T(cyl(0.045, 0.30, (0, 2.87, 0), None, axis='y', seg=10), 'chrome'))  # mast
    RM(T(cyl(0.175, 0.026, (0, 2.795, 0), None, axis='y', seg=14), 'alu'))  # the turning swashplate
    RM(T(cyl(0.135, 0.13, tuple(hub), None, axis='y', seg=14, bev=0.014), 'steel'))
    RM(T(lathe([(0.122, 3.04), (0.122, 3.085), (0.105, 3.13), (0.06, 3.162), (0.0, 3.172)], (0, 0, 0), None, seg=14, axis='y', cap=False), 'cyan'))  # the beanie
    SEC = [(-0.25, 0.0), (-0.17, 0.062), (0.10, 0.066), (0.75, 0.008), (0.75, -0.008), (0.10, -0.05), (-0.17, -0.052)]  # (chord, thickness) of a unit chord, leading edge first
    BR = [0.70, 0.93, 2.2, 3.4, 4.42, 4.76, 4.90]; BC = [0.15, 0.30, 0.30, 0.30, 0.30, 0.27, 0.17]
    def blade_ring(i, t):
        c = BC[i]; a = math.radians(8.0 - 6.0 * t); ca, sa = math.cos(a), math.sin(a)
        return [(v * c * ca - u * c * sa, u * c * ca + v * c * sa) for u, v in SEC]  # (up, side): leading edge toward -z, pitched nose up
    droop = lambda r: -0.13 * ((r - BR[0]) / (BR[-1] - BR[0])) ** 2  # parked blades hang a little
    for k, az in enumerate((180, 60, -60)):
        bl = loft([(r, hub.y + droop(r), 0.05 if i == len(BR) - 1 else 0.0) for i, r in enumerate(BR)], blade_ring, None, name='blade', up=(0, 1, 0), smooth_angle=50)
        n = len(SEC)
        def bkey(i, n=n, k=k):  # steel root, a bright abrasion strip down the leading edge, yellow tips (one got the wrong tin)
            st_, sl_ = divmod(i, n)
            if st_ >= 6: return 'blade'
            return 'steel' if st_ == 0 else ('pink' if k == 1 else 'yellow') if st_ >= 4 else 'alu' if sl_ in (0, n - 1) else 'blade'
        T(bl, 'blade', keyfn=bkey)
        grp = [bl,
               T(box((0.48, 0.05, 0.17), (0.32, hub.y, 0), None, bev=0.014, seg=1, taper=None), 'steel'),  # arm
               T(box((0.32, 0.085, 0.165), (0.63, hub.y, 0.005), None, bev=0.018, seg=1), 'alu'),  # grip
               T(cyl(0.024, 0.10, (0.56, hub.y, 0.005), None, axis='y', seg=6), 'chrome'), T(cyl(0.024, 0.10, (0.71, hub.y, 0.005), None, axis='y', seg=6), 'chrome'),
               T(box((0.05, 0.03, 0.13), (0.50, hub.y - 0.03, -0.14), None, bev=0.006, seg=1), 'steel'),  # pitch horn off the leading edge
               T(rod((0.16, 2.80, -0.07), (0.50, hub.y - 0.035, -0.19), 0.011, None, seg=5), 'chrome')]  # pitch link up from the swashplate
        for o in grp: RM(turn(o, 'y', az, (0, 0, 0)))

    # ================================================== tail rotor: two striped blades on the left of the fin
    tc = V3(TRC)
    RT = RTAIL.append
    RT(T(cyl(0.058, 0.095, tuple(tc), None, axis='z', seg=10, bev=0.01), 'steel'))
    RT(T(ball(0.04, (tc.x, tc.y, tc.z - 0.05), None, scale=(1, 1, 0.7), seg=8, rings=5), 'cyan'))
    TS = [(-0.5, 0.0), (-0.3, 0.5), (0.2, 0.5), (0.5, 0.0), (0.2, -0.5), (-0.3, -0.5)]  # (chord, thickness), unit size
    TR_ = [0.07, 0.15, 0.72, 0.80]; TCH = [0.06, 0.135, 0.135, 0.085]
    for az in (25, 205):
        tb = loft([(tc.x, tc.y + r, tc.z) for r in TR_], lambda i, t: [(v * 0.022, u * TCH[i]) for u, v in TS], None, name='tblade', up=(0, 0, 1), smooth_angle=50)
        T(tb, 'stripe')
        gp = T(box((0.075, 0.11, 0.04), (tc.x, tc.y + 0.115, tc.z), None, bev=0.008, seg=1), 'alu')
        for o in (tb, gp): RT(turn(o, 'z', az, tuple(tc)))

    # ================================================== lod1: the same curves, a handful of faces, the same four maps
    F = []
    LX = [2.70, 2.46, 1.75, 0.95, -0.25, -1.20, -1.95, -2.85, -6.42, -6.64]
    F.append(PT(Grid([[V3((x,) + ring_pt(x, 2 * math.pi * j / 8)) for j in range(8)] for x in LX]).mesh('far_hull')))
    LC = [0.44, 0.05, -0.60, -1.50, -2.20, -2.60]
    rows = []
    for x in LC:
        if x in (LC[0], LC[-1]): rows.append([V3((x, TOP(x) - 0.03, 0))] * 5)
        else: rows.append([V3((x,) + cowl_pt(x, math.pi * k / 4)) for k in range(5)])
    F.append(PT(Grid(rows, cyclic=False).mesh('far_cowl')))
    F.append(PT(side_x([FIN[0], FIN[2], FIN[3], FIN[4], FIN[6], FIN[7]], 0.06, (0, 0, 0.02), None, name='far_fin')))
    F.append(PS(box((0.44, 0.03, 2.0), (sx, sy, 0), None, name='far_stab'), 'pink'))
    for sg in (1, -1):
        F.append(PS(box((0.5, 0.36, 0.03), (-4.76, 1.78, sg * 1.0), None, name='far_plate'), 'cyan'))
        F.append(T(sweep([(-1.60, 0.05, sg * SKZ), (1.55, 0.05, sg * SKZ), (2.0, 0.14, sg * SKZ), (2.14, 0.33, sg * SKZ)], 0.05, None, seg=4), 'cyan'))
    for x in (1.00, -0.75):
        F.append(T(sweep([(x, 0.05, -SKZ), (x, 0.40, -0.90), (x, 0.64, -0.40), (x, 0.64, 0.40), (x, 0.40, 0.90), (x, 0.05, SKZ)], 0.045, None, seg=3), 'cyan'))
    F.append(T(ball(0.16, CAMC, None, seg=6, rings=3), 'white'))
    F.append(T(cyl(0.09, 0.36, (CAMC[0], 0.70, 0), None, axis='y', seg=4), 'plastic'))
    F.append(T(box((0.14, 0.14, 0.34), (tc.x, tc.y, -0.15), None), 'steel'))  # tail gearbox
    F.append(T(cyl(0.11, 0.42, (0, 2.78, 0), None, axis='y', seg=5), 'steel'))  # mast stub
    FM = [T(cyl(0.16, 0.14, tuple(hub), None, axis='y', seg=6), 'steel')]
    for k, az in enumerate((180, 60, -60)):
        bm = bmesh.new()
        q = [bm.verts.new(gv(x, hub.y + droop(max(x, BR[0])), z)) for x, z in ((0.08, -0.09), (4.9, -0.07), (4.9, 0.21), (0.08, 0.20))]
        bm.faces.new(q)
        b = _obj('far_blade', bm, None); _SM[b.name] = 30
        FM.append(turn(T(b, 'pink' if k == 1 else 'blade'), 'y', az))
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(gv(tc.x + a, tc.y + b, tc.z)) for a, b in ((-0.07, -0.8), (0.07, -0.8), (0.07, 0.8), (-0.07, 0.8))])
    b = _obj('far_tblade', bm, None); _SM[b.name] = 30
    FT = [turn(T(b, 'stripe'), 'z', 25, tuple(tc))]

    livery(H)
    return dict(shell=SHELL, glass=GLASS, cabin=CABIN, lamps=LAMPS, beacon=BEACON, rotor_main=RMAIN, rotor_tail=RTAIL, camera=CAM, searchlight=SLITE,
                far=F, far_main=FM, far_tail=FT)


# ------------------------------------------------------------ the paint job
def livery(H):
    P = PA; SD = P.SIDES
    P.px[:] = hexrgb(PINK)
    keel = [(H.P[r][3].x, H.P[r][3].y) for r in range(RI[2.40], RI[-2.55] + 1)]  # a dark keel, up to the loft's own line (the near model's keel faces are flat ink)
    P.poly(SD, [(2.75, keel[0][1])] + keel + [(-3.2, keel[-1][1] + 0.05), (-3.2, 0.4), (2.75, 0.4)], INK)
    sl = lambda y, d=0.0: -1.93 - 0.342 * (y - 0.5) - d  # the slash where the pod meets the boom (leaning like the fin)
    band = lambda d0, d1, col: P.poly(SD, [(sl(0.4, d0), 0.4), (sl(3.2, d0), 3.2), (sl(3.2, d1), 3.2), (sl(0.4, d1), 0.4)], col)
    band(0.34, 7.0, YEL); band(0.0, 0.06, INK); band(0.06, 0.28, CYAN); band(0.28, 0.34, INK)
    # the tail: pink fin behind a second, smaller slash; hazard stripes on the ventral fin; a bolt; a cyan cap
    fe = lambda y, d=0.0: (-6.00 - 0.51 * (y - 1.84) if y >= 1.84 else -6.00 + 0.42 * (1.84 - y)) + d
    tail = lambda d0, d1, col, **kw: P.poly(SD, [(fe(0.9, d0), 0.9), (fe(1.84, d0), 1.84), (fe(3.2, d0), 3.2), (fe(3.2, d1) if d1 > -1 else -7.05, 3.2), (fe(1.84, d1) if d1 > -1 else -7.05, 1.84), (fe(0.9, d1) if d1 > -1 else -7.05, 0.9)], col, **kw)
    tail(0.02, -9, PINK); tail(0.10, 0.05, CYAN); tail(0.05, 0.02, INK); tail(0.12, 0.10, INK)
    P.poly(SD, [(-5.3, 0.9), (-5.3, 1.55), (-7.05, 1.55), (-7.05, 0.9)], INK, hazard=YEL)
    P.poly(SD, [(-7.05, 2.90), (-6.2, 2.90), (-6.2, 3.2), (-7.05, 3.2)], CYAN); P.line(SD, [(-7.05, 2.89), (-6.2, 2.89)], INK, 1.0)
    xc = lambda y: -6.555 - 0.41 * (y - 2.40)
    bolt = [(0.03, 0.40), (-0.17, -0.02), (-0.04, -0.02), (-0.11, -0.40), (0.17, 0.06), (0.04, 0.06), (0.15, 0.40)]
    for dx, dy, col in ((0.03, -0.035, INK), (0.0, 0.0, YEL)): P.poly(SD, [(xc(2.40 + v) + u + dx, 2.40 + v + dy) for u, v in bolt], col)
    P.poly(SD, [(2.40, 0.4), (2.75, 0.4), (2.75, 3.0), (2.40, 3.0)], YEL); P.line(SD, [(2.395, 0.4), (2.395, 3.0)], INK, 1.0)  # yellow nose cap
    # the windows as the far model shows them (the near one has real glass over these)
    for nm, xa, xb, s0, s1 in WIN:
        if nm == 'sky': continue
        ra, rb, j0, j1 = RI[xa], RI[xb], s0, s1 + 1
        out = [H.P[r][j0] for r in range(ra, rb + 1)] + [H.P[rb][j] for j in range(j0 + 1, j1 + 1)] + [H.P[r][j1] for r in range(rb - 1, ra - 1, -1)] + [H.P[ra][j] for j in range(j1 - 1, j0, -1)]
        c = sum(out, V3()) / len(out)
        pts = [(c.x + (p.x - c.x) * 0.975, c.y + (p.y - c.y) * 0.975) for p in out]
        ycut = min(p[1] for p in pts) + 0.55 * (max(p[1] for p in pts) - min(p[1] for p in pts))
        for reg in SD:
            sub = P.sub(reg); ins = P.mask(reg, pts)
            row = P.pix(reg, 0, ycut)[1] - P.R[reg][1]
            yy = np.mgrid[0:sub.shape[0], 0:sub.shape[1]][0]
            sub[ins] = hexrgb(G_DARK); sub[ins & (yy < row)] = hexrgb(G_MID)
    # shut lines, inked like a comic: doors, cowl panels, boom joints
    P.line(SD, [(0.90, 2.115), (0.90, 0.80), (0.84, 0.735), (-0.09, 0.735), (-0.15, 0.80), (-0.15, 2.115), (0.90, 2.115)], INK)
    P.line(SD, [(-0.15, 0.80), (-0.21, 0.735), (-1.14, 0.735), (-1.20, 0.80), (-1.20, 2.03), (-0.15, 2.03)], INK)
    P.line(SD, [(0.05, 2.30), (0.05, 2.50)], INK); P.line(SD, [(-0.62, 2.26), (-0.62, 2.52)], INK); P.line(SD, [(-1.62, 2.26), (-1.62, 2.50)], INK)
    for x in (-3.02, -3.95, -4.42, -5.08):
        P.line(SD, [(x, 1.28), (x, 2.16)], 0x9c7c10)
        for d in (-0.05, 0.05): P.dots(SD, [(x + d, 1.28), (x + d, 2.16)], 0xb8921a)  # a rivet row either side of each boom joint
    for pts in ([(0.84, 2.06), (0.84, 0.80), (-0.09, 0.80), (-0.09, 2.06)], [(-0.21, 1.98), (-0.21, 0.80), (-1.14, 0.80), (-1.14, 1.98)],
                [(-1.28, 0.80), (-1.28, 2.16)], [(-0.02, 2.30), (-0.02, 2.50)], [(-0.55, 2.26), (-0.55, 2.52)], [(-1.69, 2.26), (-1.69, 2.48)]):
        P.dots(SD, pts, 0xc22a9a)
    # the writing
    P.text(SD, -0.15, 1.02, 'JANK NEWS', 2, YEL, shadow=INK, sh=2)
    P.text(SD, -1.02, 2.33, 'WE SAW THAT', 1, WHITE, shadow=INK)
    cx, cy = -1.80, 1.615  # channel 7 in a starburst on the rear panel
    star = lambda R_, r_, dx, dy: [(cx + dx + (R_ if i % 2 == 0 else r_) * math.cos(math.pi * i / 9 + 0.17), cy + dy + (R_ if i % 2 == 0 else r_) * math.sin(math.pi * i / 9 + 0.17)) for i in range(18)]
    P.poly(SD, star(0.40, 0.29, 0.035, -0.04), INK); P.poly(SD, star(0.40, 0.29, 0, 0), YEL)
    P.text(SD, cx, cy, '7', 3, INK)
    P.text(SD, -3.68, CYL(-3.68) + 0.005, 'J-ANKY', 2, INK)  # the registration
    P.text(SD, -5.38, CYL(-5.38), 'NO HUGS', 1, INK)  # by the spinny bit
    P.sub('U')[:] = hexrgb(INK); P.text(('U',), 0.20, 0.0, 'HI MOM', 2, WHITE, shadow=PINK, sh=1)
    P.sub('S')[:] = hexrgb(PINK)
    P.text(('S',), -0.56, -4.73, 'NO STEP', 1, WHITE, shadow=INK); P.text(('S',), 0.56, -4.73, 'OK STEP', 1, WHITE, shadow=INK)
    P.grain()
    for k, c in (('pink', PINK), ('yellow', YEL), ('cyan', CYAN), ('ink', INK), ('white', WHITE)): P.sub(k)[:] = hexrgb(c)
    P.write()


# ------------------------------------------------------------ finishing: joins, AO, QA, hierarchy, export
def tri_count(o):
    me = o.data; me.calc_loop_triangles()
    return len(me.loop_triangles)


def flat_ao(o, v=1.0):
    """a constant AO layer (glass and lamps stay as bright as the game makes them)"""
    me = o.data
    for c in list(me.color_attributes): me.color_attributes.remove(c)
    ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER'); me.color_attributes.active_color = ca
    for d in ca.data: d.color = (v, v, v, 1.0)
    return o


def bake_ao(objs, dist=0.6, samples=32, floor=True, lo=0.45, also=()):
    """ambient occlusion into a vertex colour layer 'AO' on each mesh (exported as COLOR_0: the game multiplies it in,
    like the maps' baked box AO), over a ground plane for the contact shade. Only objs + also are seen by the bake.
    Values run lo..1 (never pitch black). The same recipe as the round-4 map props."""
    import addon_utils
    addon_utils.enable('cycles')
    sc = bpy.context.scene
    prev = sc.render.engine
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    sc.world = sc.world or bpy.data.worlds.new('jf_world')
    sc.world.light_settings.distance = dist
    sc.render.bake.target = 'VERTEX_COLORS'
    objs = [o for o in objs if o is not None and o.type == 'MESH']
    hidden = [o for o in sc.objects if o.type == 'MESH' and o not in objs and o not in also and not o.hide_render]
    for o in hidden: o.hide_render = True
    ground = box((400, 0.02, 400), pos=(0, -0.0105, 0), name='jf_ao_floor') if floor else None
    for o in objs:
        me = o.data
        for c in list(me.color_attributes): me.color_attributes.remove(c)
        ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER'); me.color_attributes.active_color = ca
        for s in bpy.context.view_layer.objects.selected: s.select_set(False)
        o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.bake(type='AO', target='VERTEX_COLORS')
        for d in ca.data:
            v = lo + (1 - lo) * d.color[0]
            d.color = (v, v, v, 1.0)
    if ground: bpy.data.objects.remove(ground, do_unlink=True)
    for o in hidden: o.hide_render = False
    sc.render.engine = prev
    return objs


def qa(tag, objs, eps=0.0008, tol=0.003):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=eps, tol=tol)
    print('QA_PASS', tag, res.get('pass'), 'tris', sum(m['tris'] for m in res['objects'].values()))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], tag, e)
    for k in ('floating', 'enclosed'):
        for e in res.get(k, []): c = e['center']; print('QA_' + k.upper(), tag, e['object'], e['island_verts'], 'verts at game', [round(c[0], 3), round(c[2], 3), round(-c[1], 3)])
    if res.get('zfighting'): zf_where(objs, eps)
    return res


def zf_where(objs, eps=0.0008):
    """the QA gate only names the mesh that z-fights: this prints where (the middles of coplanar, same-facing,
    overlapping triangle pairs, game coordinates)"""
    from mathutils.bvhtree import BVHTree
    V, Tr, Nn = [], [], []
    for o in objs:
        me = o.data; me.calc_loop_triangles(); b = len(V); mw = o.matrix_world; rm = mw.to_3x3()
        V += [mw @ v.co for v in me.vertices]
        for t in me.loop_triangles: Tr.append(tuple(b + i for i in t.vertices)); Nn.append((rm @ t.normal).normalized())
    bvh = BVHTree.FromPolygons(V, Tr, epsilon=0.0); seen = set()
    for ti, t in enumerate(Tr):
        a, b, c = (V[i] for i in t); cen = (a + b + c) / 3
        for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
            for _, _, tj, _ in bvh.find_nearest_range(p, eps):
                if tj is None or tj == ti or set(t) & set(Tr[tj]) or Nn[ti].dot(Nn[tj]) < 0.999: continue
                a2, b2, c2 = (V[i] for i in Tr[tj]); n2 = Nn[tj]; q = p - n2 * n2.dot(p - a2)
                k = (min(ti, tj), max(ti, tj))
                if k not in seen and all((v - u).cross(q - u).dot(n2) >= -1e-9 for u, v in ((a2, b2), (b2, c2), (c2, a2))):
                    seen.add(k); print('QA_ZF_AT', [round(x, 3) for x in g_of(cen)], 'normal', [round(x, 2) for x in g_of(Nn[ti])])


def finish_heli(P):
    N = {}
    if arg('parts'):
        for k, objs in P.items():
            tally = {}
            dup = {}
            for o in objs:
                nm = o.name.split('.')[0]; tally[nm] = tally.get(nm, 0) + tri_count(o)
                kd = mathutils.kdtree.KDTree(len(o.data.vertices))
                for v in o.data.vertices: kd.insert(v.co, v.index)
                kd.balance(); d = sum(1 for v in o.data.vertices if len(kd.find_range(v.co, 1e-5)) > 1) // 2
                if d: dup[nm] = dup.get(nm, 0) + d
            print('JF_PARTS', k, sum(tally.values()), sorted(tally.items(), key=lambda kv: -kv[1]), 'doubled verts', dup)
    for k in ('shell', 'glass', 'cabin', 'lamps', 'beacon'): N[k] = join(P[k], k)
    for k, pv in (('rotor_main', HUB), ('rotor_tail', TRC), ('camera', CAMC), ('searchlight', SLC)): N[k] = part(P[k], k, pv)
    N['lod1_mesh'] = join(P['far'], 'lod1_mesh')
    N['lod1_rotor_main'] = part(P['far_main'], 'lod1_rotor_main', HUB); N['lod1_rotor_tail'] = part(P['far_tail'], 'lod1_rotor_tail', TRC)
    for k, o in N.items():
        if k in ('shell', 'glass', 'cabin', 'lamps', 'beacon', 'lod1_mesh'):  # (a join keeps its first part's origin: these sit on the root's)
            o.data.transform(Matrix.Translation(o.location)); o.location = (0, 0, 0)
        o.data.name = k  # (three.js names the pieces of a two-material mesh after the mesh)
        while len(o.data.uv_layers) > 1: o.data.uv_layers.remove(o.data.uv_layers[-1])
        o.data.validate(); o.data.update()
    bpy.context.view_layer.update()
    near = ['shell', 'glass', 'cabin', 'lamps', 'beacon', 'rotor_main', 'rotor_tail', 'camera', 'searchlight']
    far = ['lod1_mesh', 'lod1_rotor_main', 'lod1_rotor_tail']
    if arg('stats'):
        for k in near + far: print('JF_PART', k, tri_count(N[k]), [m.name for m in N[k].data.materials])
    for k in far: N[k].hide_render = True
    if not arg('no-ao'):
        N['glass'].hide_render = True  # (the cabin isn't in the dark: light comes in through the panes)
        bake_ao([N[k] for k in ('shell', 'cabin', 'camera', 'searchlight')], dist=0.6, also=[N['lamps'], N['beacon']])
        for k in ('rotor_main', 'rotor_tail'): bake_ao([N[k]], dist=0.25, floor=False, lo=0.55)  # (they turn: their own shade only)
        N['glass'].hide_render = False
        for k in near: N[k].hide_render = True
        for k in far: N[k].hide_render = False
        bake_ao([N['lod1_mesh']], dist=0.6, also=[N['lod1_rotor_main'], N['lod1_rotor_tail']])
        for k in far: N[k].hide_render = True
        for k in near: N[k].hide_render = False
    for k in near + far:
        if not N[k].data.color_attributes or k in ('glass', 'lamps', 'beacon', 'lod1_rotor_main', 'lod1_rotor_tail') or arg('no-ao'): flat_ao(N[k])
    res = {}
    if arg('qa'):
        res['body'] = qa('body', [N[k] for k in ('shell', 'glass', 'cabin', 'lamps', 'beacon')])
        for k in ('rotor_main', 'rotor_tail', 'camera', 'searchlight'): res[k] = qa(k, [N[k]])
        res['whole'] = qa('whole', [N[k] for k in near])
        res['lod1'] = qa('lod1', [N[k] for k in far], tol=0.02)
    body = _link(bpy.data.objects.new('body', None))
    for k in ('shell', 'glass', 'cabin', 'lamps', 'beacon'): N[k].parent = body
    t0 = sum(tri_count(N[k]) for k in near); t1 = sum(tri_count(N[k]) for k in far)
    r3 = lambda v: [round(x, 3) for x in v]
    meta = dict(kind='prop', id='heli', name='JANK NEWS 7', reg='J-ANKY', front='+x', lod=90, tris=[t0, t1],
                rotors=dict(main=dict(node='rotor_main', far='lod1_rotor_main', pivot=r3(HUB), axis=[0, 1, 0], r=4.9, blades=3),
                            tail=dict(node='rotor_tail', far='lod1_rotor_tail', pivot=r3(TRC), axis=[0, 0, 1], r=0.8, blades=2)),
                camera=dict(node='camera', pivot=r3(CAMC), looks='+x'), searchlight=dict(node='searchlight', pivot=r3(SLC), looks='+x'),
                blink=['beacon'], seats=[[0.5, 1.1, 0.36], [0.5, 1.1, -0.36]], skids=dict(track=SKZ * 2, x=[-1.6, 2.14]))
    root = finish(FID, [body] + [N[k] for k in ('rotor_main', 'rotor_tail', 'camera', 'searchlight')], meta)
    e = _link(bpy.data.objects.new('lod1', None)); e.parent = root
    for k in far: N[k].parent = e
    bpy.context.view_layer.update()
    lo = V3((1e9,) * 3); hi = V3((-1e9,) * 3)
    for k in near:
        for v in N[k].data.vertices:
            w = g_of(N[k].matrix_world @ v.co); lo = V3(map(min, lo, w)); hi = V3(map(max, hi, w))
    bl = V3((1e9,) * 3); bh = V3((-1e9,) * 3)
    for k in ('shell', 'glass'):
        for v in N[k].data.vertices:
            w = g_of(N[k].matrix_world @ v.co); bl = V3(map(min, bl, w)); bh = V3(map(max, bh, w))
    meta['size'] = r3(hi - lo); meta['box'] = [r3(bl), r3(bh)]  # everything / the airframe without the rotors
    root['jf'] = json.dumps(meta)
    print('JF_META', root['jf'])
    mats = sorted({m.name for k in near for m in N[k].data.materials})
    print(f'JF_PROP {FID}: lod0 {t0} tris, lod1 {t1} tris ({100 * t1 / t0:.1f}%), materials {mats}, size {meta["size"]}')
    return root, N, t0, t1, res


def export_glb(root, file_id):
    """lib.export, plus the AO vertex colours (blender 4.2+ only writes them when asked)"""
    os.makedirs(MODELS, exist_ok=True)
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    root.select_set(True)
    for c in root.children_recursive: c.select_set(True)
    path = os.path.join(MODELS, file_id + '.glb')
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_extras=True, export_yup=True, export_texcoords=True,
              export_normals=True, export_materials='EXPORT', export_image_format='AUTO', export_lights=False, export_cameras=False)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_vertex_color' in props: kw.update(export_vertex_color='ACTIVE', export_active_vertex_color_when_no_material=True, export_all_vertex_colors=False)
    bpy.ops.export_scene.gltf(**kw)
    print(f'JF_EXPORT {file_id}: {os.path.getsize(path) // 1024} KB')
    return path


# ------------------------------------------------------------ pictures
def ao_preview(on=True):
    """the sheets show the baked AO the way the game multiplies it in (only ever after the export)"""
    for k in ('paint', 'trim'):
        nt = M[k].node_tree; b = nt.nodes['Principled BSDF']; sock = b.inputs['Base Color']
        if not on or any(n.name == 'jf_ao' for n in nt.nodes): continue
        at = nt.nodes.new('ShaderNodeVertexColor'); at.layer_name = 'AO'
        mix = nt.nodes.new('ShaderNodeMix'); mix.name = 'jf_ao'; mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
        nt.links.new(sock.links[0].from_socket, mix.inputs[6]); nt.links.new(at.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], sock)


def clear_studio():
    for o in list(bpy.data.objects):
        if o.type in ('LIGHT', 'CAMERA') or o.name.startswith('jf_set'): bpy.data.objects.remove(o, do_unlink=True)


def eevee(samples=32):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'; ee = sc.eevee; ee.taa_render_samples = samples
    for k, v in (('use_gtao', True), ('use_ssr', True), ('use_bloom', True), ('use_soft_shadows', True), ('use_raytracing', True), ('use_shadows', True)):
        if hasattr(ee, k): setattr(ee, k, v)
    sc.view_settings.view_transform = 'Standard'
    return sc


VIEWS = {  # name: (camera, target) in game metres, lens
    'fl': ((11.5, 4.2, 9.0), (-1.2, 1.5, 0), 50), 'rr': ((-13.5, 4.6, -8.5), (-1.6, 1.5, 0), 50), 'side': ((-2.0, 1.7, 17.0), (-2.0, 1.7, 0), 50),
    'top': ((-2.2, 22.0, 0.01), (-2.2, 0, 0), 50), 'front': ((16.0, 1.6, 0.0), (0, 1.6, 0), 50), 'low': ((8.5, 0.5, 6.0), (0.2, 1.6, 0), 40),
    'cockpit': ((4.6, 2.0, 2.5), (1.0, 1.35, 0.0), 50), 'head': ((2.6, 3.75, 2.3), (-0.2, 2.75, 0), 55), 'tail': ((-9.2, 2.6, -3.0), (-6.0, 1.95, 0), 55),
    'belly': ((4.2, 0.12, 2.4), (0.9, 0.75, 0), 40), 'door': ((0.6, 1.5, 4.6), (-0.3, 1.4, 0), 50), 'cabin': ((1.9, 2.9, 1.9), (0.6, 1.2, 0), 35),
    'boom': ((-3.8, 2.3, 4.2), (-4.2, 1.8, 0), 50), 'left': ((-2.0, 1.7, -17.0), (-2.0, 1.7, 0), 50), 'under': ((0.4, -6.0, 0.01), (0.4, 1.0, 0), 35),
    'nose': ((5.2, 1.3, 1.6), (2.0, 1.1, 0), 50), 'far': ((30.0, 9.0, 24.0), (-1.2, 1.5, 0), 50),
}


def studio(size, c):
    def light(energy, loc, sz, col=(1, 1, 1)):
        L = bpy.data.lights.new('pl', 'AREA'); L.energy = energy * size * size; L.color = col; L.size = sz * size
        ob = _link(bpy.data.objects.new('pl', L)); ob.location = c + V3(loc) * size; lib._look_at(ob, c)
    light(200, (1.2, -1.4, 1.6), 1.2); light(70, (-1.6, -0.6, 0.6), 1.5, (0.85, 0.9, 1.0)); light(150, (-0.4, 1.8, 1.2), 0.6, (1.0, 0.8, 0.95)); light(40, (0.2, 0.2, -1.6), 1.5, (0.9, 0.85, 1.0))


def shoot(views, outdir, prefix, res=(960, 600), samples=16, exposure=-0.4):
    """named views with the sheet's studio lights -> pngs (quick looks, and the close-up strip)"""
    sc = eevee(samples)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.exposure = exposure
    w = bpy.data.worlds.new('pw'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(0x3a3346); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
    studio(13.0, gv(-2.0, 1.6, 0))
    cam = _link(bpy.data.objects.new('pc', bpy.data.cameras.new('pc'))); sc.camera = cam
    out = []
    os.makedirs(outdir, exist_ok=True)
    for v in views:
        loc, tgt, lens = VIEWS[v]
        cam.data.lens = lens; cam.data.clip_start = 0.05; cam.data.clip_end = 300
        cam.location = gv(*loc); lib._look_at(cam, gv(*tgt))
        p = os.path.join(outdir, f'{prefix}_{v}.png'); sc.render.filepath = p
        bpy.ops.render.render(write_still=True); out.append(p)
    clear_studio()
    print('JF_PREVIEW', ' '.join(out))
    return out


def strip(paths, dst, label):
    """tile pictures side by side under a label strip, like lib.sheet"""
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4); imgs.append(a); bpy.data.images.remove(im)
    Hh, Ww = imgs[0].shape[:2]
    canvas = np.zeros((Hh + 8, len(imgs) * (Ww + 4) + 4, 4), np.float32); canvas[:, :, 3] = 1; canvas[:, :, :3] = 0.08
    for k, a in enumerate(imgs): canvas[4:4 + Hh, 4 + k * (Ww + 4):4 + k * (Ww + 4) + Ww] = a
    lab = np.zeros((7 * 3 + 6, canvas.shape[1], 3), np.float32); text_px(lab, label.upper(), 6, 3, 3, 0xffe14d)
    full = np.concatenate([canvas, np.concatenate([lab[::-1], np.ones(lab.shape[:2] + (1,), np.float32)], axis=2)], axis=0)
    img = bpy.data.images.new('strip', full.shape[1], full.shape[0]); img.pixels.foreach_set(full.ravel())
    png = dst + '.png'; img.filepath_raw = png; img.file_format = 'PNG'; img.save()
    if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v 3 "{dst}.jpg"') == 0: os.remove(png)
    for p in paths: os.remove(p)
    print('JF_SHEET', dst + '.jpg')


def hero(path, samples=160, rotor=None):
    """one nicer picture: path traced, softboxes in the game's colours on a dark glossy floor"""
    import addon_utils
    addon_utils.enable('cycles')
    sc = bpy.context.scene
    den = getattr(bpy.app.build_options, 'openimagedenoise', False)  # (the apt blender 4.0 has no denoiser: more samples instead)
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples if den else samples * 3; sc.cycles.use_denoising = den
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.exposure = float(arg('hero-exposure', 0.0))
    sc.view_settings.view_transform = arg('hero-view', 'Standard')
    w = bpy.data.worlds.new('hero'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sp = nt.nodes.new('ShaderNodeSeparateXYZ'); rp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(tc.outputs['Generated'], sp.inputs[0]); nt.links.new(sp.outputs['Z'], rp.inputs[0]); nt.links.new(rp.outputs['Color'], bg.inputs['Color'])
    el = rp.color_ramp.elements; el[0].position = 0.0; el[0].color = srgb(0x2c1244); el[1].position = 0.22; el[1].color = srgb(0x0a0510)
    bg.inputs['Strength'].default_value = 1.0
    fm = bpy.data.materials.new('jf_set_floor'); fm.use_nodes = True
    b = fm.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = srgb(0x1a0f26); b.inputs['Roughness'].default_value = 0.42; b.inputs['Specular IOR Level'].default_value = 0.3
    box((240, 0.02, 240), pos=(0, -0.011, 0), m=fm, name='jf_set_floor')
    def light(energy, loc, sz, col=(1, 1, 1), at=(-1.0, 1.6, 0)):
        L = bpy.data.lights.new('hl', 'AREA'); L.energy = energy; L.color = col; L.size = sz
        ob = _link(bpy.data.objects.new('hl', L)); ob.location = gv(*loc); lib._look_at(ob, gv(*at))
    light(4200, (10.0, 8.5, 9.0), 7.0, (1.0, 0.98, 0.95))            # key: high, camera side
    light(1300, (13.0, 2.2, -6.0), 9.0, (0.8, 0.88, 1.0))            # fill off the nose
    light(3400, (-12.0, 6.0, -8.0), 4.5, (0.25, 0.8, 1.0))           # cyan rim from behind the tail
    light(1100, (-13.0, 5.0, 5.0), 3.5, (1.0, 0.22, 0.8))            # magenta rim from behind on the near side
    light(1500, (-3.0, 3.0, 14.0), 8.0, (1.0, 1.0, 1.0))             # a soft white card down the near side (the yellow stays yellow)
    light(1500, (-3.0, 11.0, -5.0), 9.0, (1.0, 1.0, 1.0))            # a top box, off to the far side: the streak along the roof and the blades
    cam = _link(bpy.data.objects.new('hc', bpy.data.cameras.new('hc'))); sc.camera = cam
    v = [float(x) for x in arg('hero-cam', '9.6,1.7,12.4,-0.75,1.6,-0.1,50').split(',')]  # (camera, target, lens: other angles while checking)
    cam.data.lens = v[6]; cam.data.clip_start = 0.1; cam.data.clip_end = 500
    cam.location = gv(*v[:3]); lib._look_at(cam, gv(*v[3:6]))
    if rotor is not None:  # swing the rotor (its own node) so one blade runs straight across the picture and none points at the lens
        rotor.rotation_euler = Euler((0, 0, -float(arg('hero-rotor', math.atan2(v[2], v[0]) - math.radians(30)))), 'XYZ')
    try:  # a little bloom on the lamps and the hot highlights (blender 5's compositor; skipped on older ones)
        if not hasattr(sc, 'compositing_node_group'): raise RuntimeError('no node group compositor')
        ng = bpy.data.node_groups.new('jf_bloom', 'CompositorNodeTree'); ng.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = ng.nodes.new('CompositorNodeRLayers'); gl = ng.nodes.new('CompositorNodeGlare'); out = ng.nodes.new('NodeGroupOutput')
        gl.inputs['Type'].default_value = 'Bloom'; gl.inputs['Threshold'].default_value = 1.6; gl.inputs['Strength'].default_value = 0.3; gl.inputs['Size'].default_value = 0.3
        ng.links.new(rl.outputs['Image'], gl.inputs['Image']); ng.links.new(gl.outputs['Image'], out.inputs['Image'])
        sc.compositing_node_group = ng; sc.render.use_compositing = True
    except Exception as e: print('JF_NO_BLOOM', repr(e))
    png = path + '.png'; sc.render.filepath = png
    bpy.ops.render.render(write_still=True)
    if hasattr(sc, 'compositing_node_group'): sc.compositing_node_group = None
    if rotor is not None: rotor.rotation_euler = Euler((0, 0, 0), 'XYZ')
    if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v 2 "{path}.jpg"') == 0: os.remove(png)
    clear_studio()
    print('JF_HERO', path + '.jpg')


def main():
    lib.reset(); lib._mats.clear()
    root, N, t0, t1, res = finish_heli(build())
    if not arg('no-export'): export_glb(root, FID)
    near = [N[k] for k in ('shell', 'glass', 'cabin', 'lamps', 'beacon', 'rotor_main', 'rotor_tail', 'camera', 'searchlight')]
    far = [N[k] for k in ('lod1_mesh', 'lod1_rotor_main', 'lod1_rotor_tail')]
    pdir = arg('preview')
    if isinstance(pdir, str):
        ao_preview()
        if arg('lod'):
            for o in near: o.hide_render = True
            for o in far: o.hide_render = False
        shoot(arg('views', 'fl,rr,side,top').split(','), pdir, FID, res=tuple(int(x) for x in arg('res', '960x600').split('x')), samples=int(arg('samples', 12)))
        return
    if not arg('no-hero'): hero(os.path.join(arg('hero-dir', SHEETS), 'heli_hero'), int(arg('hero-samples', 160)), N['rotor_main'])
    if arg('no-sheet'): return
    ao_preview(); eevee()
    sheet(root, FID, res=(800, 520), extra_note=f'LOD0 {t0} LOD1 {t1}', exposure=-0.5)
    clear_studio()
    for o in near: o.hide_render = True
    for o in far: o.hide_render = False
    sheet(root, FID + '_lod1', views=('persp', 'left', 'back_persp'), res=(480, 300), extra_note='FAR', exposure=-0.5)
    clear_studio()
    for o in near: o.hide_render = False
    for o in far: o.hide_render = True
    tmp = os.path.join(SHEETS, '_tmp')
    strip(shoot(['cockpit', 'head', 'tail', 'belly'], tmp, FID, res=(640, 420), samples=32), os.path.join(SHEETS, FID + '_detail'), f'{FID} close-ups: cockpit, rotor head, tail, belly')
    try: os.rmdir(tmp)
    except OSError: pass


main()
