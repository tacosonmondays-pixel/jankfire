# Helicopter: JANK NEWS 7, an original light single-turbine news / utility helicopter (nobody's real one), real size:
# 9.1 m fuselage, 9.8 m two-blade teetering rotor with a stabiliser bar, 1.46 m wide cabin, 3.1 m tall. Front = +x
# (like the car), skids on y = 0, the rotor mast on x = 0.
#   real parts   bubble canopy (windscreen halves either side of a centre post, chin windows, skylights, four door
#                windows, all see-through, set in rubber gaskets in a 35 mm shell), a cabin you can see into (seats,
#                bench, instrument binnacle, cyclics, collective, fuzzy dice), engine cowl with intakes and an exhaust
#                stack, mast, swashplate, pitch links, blade grips, stabiliser bar, tail boom with the drive-shaft
#                cover, tail rotor + gearbox, swept fin, ventral fin with a tail skid (the rotor guard), horizontal
#                stabiliser with end plates, skids on two bowed cross tubes with steps, wire cutter, pitot, antennas,
#                nav / tail / landing lights, the beacon, and the news gear: a gimbal camera ball under the chin and a
#                downlink dome under the belly
#   made fun     candy hot pink over purple-black, a yellow belt that says JANK NEWS and slashes up over the cowl,
#                cyan pinstripe, J-FIRE on the boom, tail-rotor hazard stripes, a 7 on the fin, a HOW'S MY FLYING?
#                sticker, cyan vinyl seats
# Nodes (all under the root p_heli):
#   body        everything that stays put (paint = heli_paint: one 512 x 256 livery picture, the side view painted
#               once per side so the lettering reads on both; flat colours are swatches of the same picture)
#   glass       the windows (their own node: see-through, draws after the body)
#   rotor       hub, grips, blades, stabiliser bar, pitch links. origin on the mast top, spins about y
#   tailrotor   origin on its hub, spins about z
#   beacon      the red anti-collision light on the fin (the game can blink it)
#   lod1        empty: body_lod1 (one material) + rotor_lod1 + tailrotor_lod1 (same origins), ~300 triangles
# Baked AO in the vertex colours (COLOR_0, the game multiplies it in). The body is one loft along x (a superellipse
# section per station: tumblehome above the belt, a tub below, round by the boom), so the pod runs into the boom in
# one skin; window cells are left out of it, their edges closed with gaskets to a lining 35 mm inside.
# run: blender52 -b -P tools/blender/make_heli.py -- [--qa] [--no-export] [--no-sheet] [--no-hero] [--no-ao]
#      [--out=<dir>]  (glb + pictures into a scratch folder)
#      [--preview=<dir>] [--views=persp,left,right,top,front,back_persp,cabin,tail,lod1] [--samples=12]
#                     (a quick look: a few small renders into <dir>, no AO, nothing else written)
# -> public/models/p_heli.glb, tools/blender/sheets/p_heli.jpg (the turnaround, ~4 min of software GL) and
#    tools/blender/sheets/heli_hero.jpg. Not placed on a map or wired into the game yet.
# Written for Blender 5.2 (blender52): the shims below keep lib.py (a 4.0 kit) working there. It builds on 4.0 too
# (same mesh, QA passes), but the pictures come out hotter there, so make the sheets with blender52.
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link
import lib
from bisect import bisect_right

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
V3 = Vector
FID = 'p_heli'


def arg(k, d=None):
    for a in ARGV:
        if a.startswith('--' + k + '='): return a.split('=', 1)[1]
        if a == '--' + k: return True
    return d


# ------------------------------------------------------------ blender 4.1+ shims (lib.py was written on 4.0)
if not hasattr(bpy.types.Mesh, 'use_auto_smooth'):
    def smooth(o, angle=35):  # no auto smooth any more: mark the edges past the angle sharp instead
        me = o.data
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        lim = math.radians(angle)
        bm = bmesh.new(); bm.from_mesh(me)
        for e in bm.edges: e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > lim)
        bm.to_mesh(me); bm.free()
        return o
    lib.smooth = smooth


def glass_mat(name, color, alpha, rough=0.05):
    """see-through glass (lib.mat's alpha path sets a 4.0-only property)"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(color); b.inputs['Roughness'].default_value = rough
    b.inputs['Alpha'].default_value = alpha
    for k, v in (('blend_method', 'BLEND'), ('shadow_method', 'NONE')):
        try: setattr(m, k, v)
        except Exception: pass
    m['jf_color'] = color
    return m


# ------------------------------------------------------------ the fuselage's shape
def curve(pts):
    """smooth monotone curve through [(x, y)] (Fritsch-Carlson: no overshoot), clamped at the ends"""
    pts = sorted(pts)
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


NOSE, LN, TAIL = 2.30, 0.80, -6.25   # nose tip, how far back the nose's ellipse runs, the boom's end
_YC = curve([(2.3, 1.06), (1.6, 1.10), (0.8, 1.12), (-0.6, 1.14), (-1.2, 1.26), (-1.7, 1.45), (-2.15, 1.64), (TAIL, 1.80)])  # widest point's height
_UP = curve([(2.3, 0.64), (1.9, 0.82), (1.5, 0.92), (1.02, 0.97), (0.5, 0.98), (-0.6, 0.95), (-1.2, 0.76), (-1.7, 0.48), (-2.15, 0.22), (TAIL, 0.105)])  # roof above it
_LO = curve([(2.3, 0.42), (1.8, 0.53), (1.2, 0.58), (0.0, 0.60), (-0.6, 0.58), (-1.2, 0.52), (-1.7, 0.38), (-2.15, 0.22), (TAIL, 0.105)])  # belly below it
_HW = curve([(2.3, 0.54), (1.8, 0.67), (1.2, 0.72), (0.2, 0.73), (-0.6, 0.70), (-1.2, 0.56), (-1.7, 0.38), (-2.15, 0.22), (TAIL, 0.105)])  # half width
_EX = curve([(-2.15, 2.0), (-0.9, 2.5)])  # superellipse power: a soft box for the cabin, a circle for the boom


def sec(x):
    """the section at x: (widest point's height, roof above, belly below, half width, exponent)"""
    d = NOSE - x
    k = 1.0 if d >= LN else math.sqrt(max(0.0, 1 - (1 - d / LN) ** 2))  # the nose closes like an egg
    return _YC(x), _UP(x) * k, _LO(x) * k, _HW(x) * k, 2.0 / _EX(x)


def pt(x, t, sd=1):
    """a point on the skin: t = degrees round the section from the widest point (-90 keel, 90 crown), sd = side"""
    yc, up, lo, hw, e = sec(x)
    c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
    z = hw * abs(c) ** e
    y = yc + up * s ** e if s >= 0 else yc - lo * (-s) ** e
    return V3((x, y, z * sd))


def nrm(x, t, sd=1):
    """outward normal of the skin there"""
    tt = max(-89.0, min(89.0, t))
    a = pt(x, tt + 1, sd) - pt(x, tt - 1, sd)
    x1 = min(x, NOSE - 0.012)
    b = pt(x1 + 0.01, tt, sd) - pt(x1 - 0.01, tt, sd)
    n = a.cross(b)
    if n.length < 1e-9: n = V3((0, 1 if t > 0 else -1, 0))
    n.normalize()
    p = pt(x, tt, sd); out = V3((0, p.y - sec(x)[0], p.z))   # a section is star-shaped round its widest line
    if out.length < 1e-6: out = V3((1, 0, 0))
    return n if n.dot(out) > 0 else -n


def surf(x, t, sd=1, off=0.0):
    return pt(x, t, sd) + nrm(x, t, sd) * off


def top(x): yc, up, _, _, _ = sec(x); return yc + up
def bot(x): yc, _, lo, _, _ = sec(x); return yc - lo


def half_at(x, y):
    """the skin's half width at height y"""
    yc, up, lo, hw, e = sec(x)
    s = (y - yc) / up if y >= yc else (yc - y) / lo
    s = max(0.0, min(1.0, s)) ** (1 / e)
    return hw * max(0.0, 1 - s * s) ** (e / 2)


# ring: degrees round one side, keel to crown. slots between them: 0-1 belly, 2-3 chin windows, 4 the belt (the yellow
# band), 5-6 the side windows, 7 the door heads, 8-9 the skylights, 10 roof, 11 the centre post
T = [-90, -70, -52, -32, -12, 8, 26, 44, 53, 66, 78, 87.8, 90]
NS = len(T) - 1; NK = 2 * NS
XS = [NOSE, 2.286, 2.25, 2.19, 2.08, 1.96, 1.80, 1.60, 1.40, 1.20, 1.02, 0.94, 0.70, 0.45, 0.20, -0.08, -0.16, -0.38, -0.60, -0.82,
      -0.90, -1.15, -1.40, -1.65, -1.90, -2.15, -2.60, -3.20, -3.90, -4.60, -5.30, -5.90, TAIL]
CAB = (2.19, -0.90)   # the lined cabin: nose bulkhead .. rear bulkhead
TH, GD = 0.035, 0.014  # shell thickness, how deep the glass sits in it


def is_glass(xm, j):
    if 1.02 < xm < 2.19 and 5 <= j <= 10: return True    # windscreen (one bubble each side of the post)
    if 1.20 < xm < 1.96 and 2 <= j <= 3: return True     # chin windows
    if -0.08 < xm < 0.94 and 5 <= j <= 6: return True    # front doors
    if 0.20 < xm < 0.94 and 8 <= j <= 9: return True     # skylights
    if -0.82 < xm < -0.16 and 5 <= j <= 6: return True   # rear doors
    return False


class Mesh_:
    """a bmesh in game coordinates: welded verts, faces wound to face a given way"""
    def __init__(s): s.bm = bmesh.new(); s.c = {}

    def v(s, p):
        k = (round(p.x, 5), round(p.y, 5), round(p.z, 5))
        if k not in s.c: s.c[k] = s.bm.verts.new(gv(*p))
        return s.c[k]

    def f(s, pts, want, mi=0):
        vs = []
        for p in pts:
            q = s.v(p)
            if q not in vs: vs.append(q)
        if len(vs) < 3: return None
        n = V3()
        for a, b in zip(vs, vs[1:] + vs[:1]): n += a.co.cross(b.co)  # (newell: fine for bent quads)
        if n.dot(gv(*want)) < 0: vs.reverse()
        try: f = s.bm.faces.new(vs)
        except ValueError: return None
        f.material_index = mi; f.smooth = True
        return f

    def obj(s, name, mats, angle=40):
        o = _obj(name, s.bm, None)
        for m in mats: o.data.materials.append(m)
        smooth(o, angle)
        return o


def build_shell(M):
    """the skin (paint), the cabin lining 35 mm inside it, rubber gaskets round every window opening, and the glass"""
    S, G = Mesh_(), Mesh_()
    ring = lambda k: (T[k], 1) if k <= NS else (T[NK - k], -1)
    O, I, GL = [], [], []
    for x in XS:
        ro, ri, rg = [], [], []
        for k in range(NK):
            t, sd = ring(k)
            p = pt(x, t, sd); n = nrm(x, t, sd)
            ro.append(p); ri.append(p - n * TH); rg.append(p - n * GD)
        O.append(ro); I.append(ri); GL.append(rg)
    lined = lambda i: CAB[1] - 1e-6 <= XS[i] <= CAB[0] + 1e-6
    glass = lambda i, s: 0 <= i < len(XS) - 1 and is_glass((XS[i] + XS[i + 1]) / 2, s % NK if s % NK < NS else NK - 1 - s % NK)
    for i in range(len(XS) - 1):
        xm = (XS[i] + XS[i + 1]) / 2
        yca = sec(xm)[0]
        for s in range(NK):
            s1 = (s + 1) % NK
            cell = [(i, s), (i, s1), (i + 1, s1), (i + 1, s)]
            po = [O[a][b] for a, b in cell]
            cen = sum(po, V3()) / 4
            out = V3((0.02, cen.y - yca, cen.z))
            if glass(i, s):
                G.f([GL[a][b] for a, b in cell], out)
                for (a0, b0), (a1, b1), nb in ((cell[0], cell[1], (i - 1, s)), (cell[2], cell[3], (i + 1, s)), (cell[1], cell[2], (i, s + 1)), (cell[3], cell[0], (i, s - 1))):
                    if glass(*nb): continue
                    mid = (O[a0][b0] + O[a1][b1]) / 2
                    S.f([O[a0][b0], O[a1][b1], I[a1][b1], I[a0][b0]], cen - mid, 2)  # the gasket
            else:
                S.f(po, out, 0)
                if lined(i) and lined(i + 1): S.f([I[a][b] for a, b in cell], -out, 1)
    for i, x in enumerate(XS):  # the lining's two bulkheads, the boom's end
        if abs(x - CAB[0]) < 1e-6 or abs(x - CAB[1]) < 1e-6:
            c = V3((x, sec(x)[0], 0)); w = V3((-1, 0, 0)) if x > 0 else V3((1, 0, 0))
            for s in range(NK): S.f([I[i][s], I[i][(s + 1) % NK], c], w, 1)
    c = V3((TAIL, sec(TAIL)[0], 0))
    for s in range(NK): S.f([O[-1][s], O[-1][(s + 1) % NK], c], V3((-1, 0, 0)), 0)
    return S.obj('shell', [M['paint'], M['cabin'], M['trim']]), G.obj('glass_panes', [M['glass']])


def skin(name, rings, mats, closed=True, caps=(True, True), mfn=None, angle=40):
    """a loft through rings of game points (same count each); faces point away from the rings' middles"""
    S = Mesh_()
    n = len(rings[0])
    cs = [sum(r, V3()) / n for r in rings]
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        mid = (cs[i] + cs[i + 1]) / 2
        for j in range(n if closed else n - 1):
            jj = (j + 1) % n
            q = [a[j], a[jj], b[jj], b[j]]
            S.f(q, sum(q, V3()) / 4 - mid, mfn(i, j) if mfn else 0)
    for end, on in ((0, caps[0]), (-1, caps[1])):
        if not on: continue
        r = rings[end]; w = cs[end] - cs[1 if end == 0 else -2]
        for j in range(n if closed else n - 1): S.f([r[j], r[(j + 1) % n], cs[end]], w, mfn(end, j) if mfn else 0)
    return S.obj(name, mats, angle)


# ------------------------------------------------------------ the livery picture + UVs
X0, X1, Y0, Y1 = -6.9, 2.5, 0.35, 3.15   # the side view the picture covers (metres)
AW, AH = 512, 128                        # one side's half of the picture (the +z side on top, the -z side below it)
PINK, YEL, CYAN, DARK, BLACK = 0xf01cc8, 0xffe14d, 0x4fd8ff, 0x1e0f2a, 0x141416
SW = {k: (72 + 12 * i, 100, 12, 12) for i, k in enumerate(('pink', 'yellow', 'cyan', 'dark', 'glass', 'black', 'grey', 'white'))}
SWC = {'pink': PINK, 'yellow': YEL, 'cyan': CYAN, 'dark': DARK, 'glass': 0x1a2a3a, 'black': BLACK, 'grey': 0x8a8f98, 'white': 0xf2f2f2}
R_DICE, R_STICK = (72, 114, 8, 8), (172, 100, 64, 20)
col_of = lambda x: (x - X0) / (X1 - X0) * AW
row_of = lambda y: (Y1 - y) / (Y1 - Y0) * AH


def livery(px):
    W, H = AW, AH
    xs = X0 + (np.arange(W) + 0.5) / W * (X1 - X0); ys = Y1 - (np.arange(H) + 0.5) / H * (Y1 - Y0)
    Xg, Yg = np.meshgrid(xs, ys)
    ix, iy = np.meshgrid(np.arange(W), np.arange(H))
    bc = np.array([sec(x)[0] for x in xs])[None, :] + 0 * Yg                       # the belt follows the widest line
    bw = np.clip(0.235 * np.array([sec(x)[3] for x in xs]), 0.05, 0.17)[None, :] + 0 * Yg
    s = (-0.95 - Xg) - 0.55 * (Yg - 1.29)                                          # > 0: behind the slash line
    a = np.empty((H, W, 3), dtype=np.float32); a[:] = hexrgb(PINK)
    up = Yg >= bc - bw - 0.05
    a[~up] = hexrgb(DARK)
    a[up & (Yg <= bc - bw)] = hexrgb(CYAN)
    a[(Xg > 2.185) & up] = hexrgb(DARK)                                            # the radome: a dark nose cap
    a[np.abs(Yg - bc) < bw] = hexrgb(YEL)
    a[up & (s > 0) & (s < 0.30)] = hexrgb(YEL)
    a[up & (s >= 0.30) & (s < 0.37)] = hexrgb(CYAN)
    dz = up & (s >= 0.37) & (s < 0.50)
    a[dz & ((ix + iy) % 2 == 0)] = hexrgb(CYAN); a[dz & ((ix + iy) % 2 == 1)] = hexrgb(DARK)  # comic halftone
    a[s >= 0.50] = hexrgb(DARK)
    hz = (Xg < -5.0) & (Xg > -5.75)                                               # tail rotor danger stripes
    k = np.floor((Xg + Yg) / 0.13).astype(int) % 2
    a[hz & (k == 0)] = hexrgb(YEL); a[hz & (k == 1)] = hexrgb(BLACK)
    fin = Xg <= -5.75
    a[fin] = hexrgb(PINK); a[fin & (Yg > 2.72)] = hexrgb(YEL); a[fin & (Yg < 1.60)] = hexrgb(YEL)
    r = np.hypot(Xg + 6.29, Yg - 2.34)
    a[r < 0.225] = hexrgb(BLACK); a[r < 0.185] = hexrgb(YEL)
    seam = np.zeros((H, W), bool)                                                  # door + cowl seams, louvres
    r0, r1 = int(row_of(1.93)), int(row_of(0.72))
    for x in (0.98, -0.12, -0.86): seam[r0:r1 + 1, int(col_of(x))] = True
    seam[r0, int(col_of(-0.86)):int(col_of(0.98)) + 1] = True; seam[r1, int(col_of(-0.86)):int(col_of(0.98)) + 1] = True
    for y in (2.19, 2.235, 2.28, 2.325): seam[int(row_of(y)), int(col_of(-1.30)):int(col_of(-0.62))] = True
    for x in (-0.25, -1.45): seam[int(row_of(2.6)):int(row_of(2.14)), int(col_of(x))] = True
    a[seam] *= 0.42
    px[:H] = a; px[H:] = a[:, ::-1]
    def put(txt, xc, yc, sc, col):
        w = len(txt) * 6 * sc - sc; h = 7 * sc
        r_ = int(round(row_of(yc) - h / 2))
        text_px(px, txt, int(round(col_of(xc) - w / 2)), r_, sc, col)
        text_px(px, txt, int(round(AW - col_of(xc) - w / 2)), H + r_, sc, col)
    put('JANK NEWS', 0.35, 1.115, 2, BLACK)
    put('J-FIRE', -2.98, _YC(-2.98), 2, YEL)
    put('7', -6.29, 2.34, 2, BLACK)
    px[99:127, 70:268] = hexrgb(DARK)                                              # the free block under the boom
    for k_, (x, y, w, h) in SW.items(): px[y:y + h, x:x + w] = hexrgb(SWC[k_])
    x, y, w, h = R_DICE
    px[y:y + h, x:x + w] = hexrgb(0xffffff)
    for dx, dy in ((1, 1), (5, 1), (3, 3), (1, 5), (5, 5)): px[y + dy:y + dy + 2, x + dx:x + dx + 2] = hexrgb(0x111111)
    x, y, w, h = R_STICK
    px[y:y + h, x:x + w] = hexrgb(0x7dff4f)
    text_px(px, "HOW'S MY", x + 8, y + 2, 1, 0x101010); text_px(px, 'FLYING? NO', x + 2, y + 11, 1, 0xff1aa0)


def _uvl(o):
    apply_mods(o); bpy.context.view_layer.update()
    me = o.data
    return me, (me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')).data, o.matrix_world


def uv_side(o):
    """the livery: a straight side-on projection onto that side's half of the picture (a faint shear with z, so faces
    seen edge-on from the side still get a sliver of it and not a zero-area UV)"""
    me, uv, mw = _uvl(o)
    r3 = mw.to_3x3()
    for p in me.polygons:
        c = mw @ p.center; n = r3 @ p.normal
        b_side = (-c.y < -1e-4) or (abs(c.y) <= 1e-4 and -n.y < 0)
        for li in p.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            u = (gx - X0) / (X1 - X0) + 0.003 * gz
            w = min(0.998, max(0.002, (gy - Y0) / (Y1 - Y0) + 0.004 * gz))
            uv[li].uv = ((1 - u) if b_side else u, (0.0 if b_side else 0.5) + 0.5 * w)
    return o


def uv_rect(o, rect):
    """a flat colour (or a small picture) from the livery: every face inside one pixel rect of it"""
    me, uv, mw = _uvl(o)
    x, y, w, h = rect
    pts = [mw @ v.co for v in me.vertices]
    lo = V3(map(min, *pts)) if len(pts) > 1 else pts[0]; hi = V3(map(max, *pts)) if len(pts) > 1 else pts[0]
    ext = V3([max(hi[k] - lo[k], 1e-6) for k in range(3)])
    r3 = mw.to_3x3()
    for p in me.polygons:
        n = r3 @ p.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        i, j = [k for k in range(3) if k != ax]
        for li in p.loop_indices:
            v = pts[me.loops[li].vertex_index]
            a = (v[i] - lo[i]) / ext[i]; b = (v[j] - lo[j]) / ext[j]
            uv[li].uv = ((x + 1.5 + a * (w - 3)) / AW, 1 - (y + 1.5 + b * (h - 3)) / (2 * AH))
    return o


def sw(o, name): return uv_rect(o, SW[name])
def ub(o, size=0.5): uv_box(o, size); return o


def decal(xs, ts, sd, rect, m, off=0.003, name='decal'):
    """a picture stuck on the skin: on the skin's own cells (xs = stations, ts = ring degrees, so it lies flat on the
    facets, off above them), the rect of the livery across it (reads from outside)"""
    S = Mesh_(); uvl = S.bm.loops.layers.uv.new('UVMap')
    x, y, w, h = rect
    def at(i, j):
        fx = (xs[i] - xs[0]) / (xs[-1] - xs[0]); ft = (ts[j] - ts[0]) / (ts[-1] - ts[0])
        fu = fx if sd > 0 else 1 - fx  # (+z side: +x is the viewer's right)
        return surf(xs[i], ts[j], sd, off), ((x + 0.5 + fu * (w - 1)) / AW, 1 - (y + h - 0.5 - ft * (h - 1)) / (2 * AH))
    for i in range(len(xs) - 1):
        for j in range(len(ts) - 1):
            q = [at(i, j), at(i + 1, j), at(i + 1, j + 1), at(i, j + 1)]
            f = S.f([p for p, _ in q], nrm((xs[i] + xs[i + 1]) / 2, (ts[j] + ts[j + 1]) / 2, sd))
            for lp in f.loops:
                for p, u in q:
                    if (lp.vert.co - gv(*p)).length < 1e-6: lp[uvl].uv = u
    return S.obj(name, [m])


# ------------------------------------------------------------ build
def materials():
    M = {}
    M['paint'] = mat('heli_paint', 0xffffff, rough=0.22, metal=0.25, clearcoat=1.0, tex=tex_canvas('heli_livery', AW, 2 * AH, livery))
    M['paint']['jf_color'] = PINK
    M['glass'] = glass_mat('heli_glass', 0x12303c, 0.46)
    M['trim'] = mat('heli_trim', 0x141416, rough=0.6)
    M['chrome'] = mat('heli_chrome', 0xd8dde6, rough=0.12, metal=1.0)
    M['steel'] = mat('heli_steel', 0x5c6068, rough=0.42, metal=0.8)
    M['cabin'] = mat('heli_cabin', 0x4a4254, rough=0.85)
    def blade_draw(px):
        px[:] = hexrgb(0x2a2a31)
        px[:, 54:] = hexrgb(YEL); px[:, 57:59] = hexrgb(BLACK); px[:, 61:] = hexrgb(0xf2f2f2)   # the tip: yellow, a black band, white
        px[:, 6:8] = hexrgb(0xf2f2f2)                                                        # the root's track mark
        px[0] *= 0.55                                                                        # leading-edge strip
    M['blade'] = mat('heli_blade', 0xffffff, rough=0.9, tex=tex_canvas('heli_blade_t', 64, 4, blade_draw))
    def panel_draw(px):
        px[:] = hexrgb(0x101014)
        for k, (cx, c) in enumerate(((7, 0x39ff14), (19, 0x4fd8ff), (31, 0xffe14d), (43, 0xff3030))):
            px_disc(px, cx, 7, 5.2, 0x2a2a33); px_disc(px, cx, 7, 5.2, c, r_in=4.2)
            px_line(px, cx, 7, cx + (3, -3, 2, -1)[k], 7 + (-3, -2, 3, -4)[k], 0xffffff)
        px[15:19, 3:47] = hexrgb(0x08080a)
        for k in range(10): px[16:18, 5 + k * 4:7 + k * 4] = hexrgb((0xff3030, 0x39ff14, 0xffe14d)[k % 3])
    M['panel'] = mat('heli_panel', 0xffffff, rough=0.4, emit=0xffffff, strength=1.4, tex=tex_canvas('heli_panel_t', 50, 22, panel_draw), emit_tex=True)
    M['red'] = mat('heli_red', 0xff1a2a, rough=0.2, emit=0xff1020, strength=2.5)
    M['green'] = mat('heli_green', 0x39ff14, rough=0.2, emit=0x39ff14, strength=2.5)
    M['white'] = mat('heli_lamp', 0xfff4d0, rough=0.2, emit=0xfff0c0, strength=2.5)
    M['lens'] = mat('heli_lens', 0x4fd8ff, rough=0.1, emit=0x4fd8ff, strength=2.0)
    M['beacon'] = mat('heli_beacon', 0xff1a2a, rough=0.2, emit=0xff1020, strength=3.0)
    return M


RP = (0.0, 2.93, 0.0)       # the rotor's pivot (the teeter bolt)
TP = (-6.22, 1.80, -0.30)   # the tail rotor's hub
RR, TR_R = 4.9, 0.72        # rotor radii


def build_body(M):
    """-> (static parts, glass parts)"""
    B = []; A = B.append
    pa, tr, ch, st, cb = M['paint'], M['trim'], M['chrome'], M['steel'], M['cabin']
    shell, panes = build_shell(M)
    A(uv_side(shell)); uv_side(panes)

    # ---------------- engine cowl (the doghouse) on the roof, intakes, exhaust, mast
    ct = curve([(0.80, 2.11), (0.55, 2.28), (0.2, 2.41), (-0.6, 2.46), (-1.4, 2.40), (-2.0, 2.22), (-2.5, 1.93)])
    cw = curve([(0.80, 0.07), (0.55, 0.25), (0.2, 0.34), (-0.6, 0.38), (-1.4, 0.34), (-2.0, 0.24), (-2.5, 0.08)])
    def cowl_ring(x, n=11):
        yt, w = ct(x), cw(x); yb = top(x) - 0.2
        out = []
        for k in range(n):
            a = math.pi * k / (n - 1); c, s = math.cos(a), math.sin(a)
            out.append(V3((x, yb + (yt - yb) * s ** 0.6, w * abs(c) ** 0.6 * (1 if c >= 0 else -1))))
        return out
    A(uv_side(skin('cowl', [cowl_ring(x) for x in (0.80, 0.68, 0.5, 0.3, 0.0, -0.4, -0.9, -1.4, -1.8, -2.15, -2.5)], [pa], closed=False)))
    for sz in (-1, 1):
        A(uv_side(rod((0.36, 2.25, sz * 0.30), (-0.25, 2.25, sz * 0.30), 0.118, pa, seg=14, r1=0.09)))   # intake cheek
        A(ub(rod((0.40, 2.25, sz * 0.30), (0.33, 2.25, sz * 0.30), 0.128, ch, seg=14, bev=0.008)))        # chrome lip
        A(ub(rod((0.405, 2.25, sz * 0.30), (0.30, 2.25, sz * 0.30), 0.1, tr, seg=14)))                     # the hole
        for k in range(3): A(ub(box((0.012, 0.19, 0.012), (0.408, 2.25, sz * (0.30 + (k - 1) * 0.055)), ch)))  # inlet bars
    ex0, ex1 = V3((-1.50, 2.30, 0)), V3((-2.06, 2.60, 0)); exd = (ex1 - ex0).normalized()
    A(ub(rod(ex0, ex1, 0.095, st, seg=14, bev=0.008)))                                                    # exhaust stack
    A(ub(rod(ex0 + exd * 0.3, ex1 + exd * 0.003, 0.078, tr, seg=14)))
    A(ub(rod(ex1 - exd * 0.07, ex1 - exd * 0.02, 0.103, ch, seg=14, bev=0.006)))                          # its clamp band
    A(ub(lathe([(0.14, 2.38), (0.13, 2.46), (0.075, 2.53), (0.06, 2.58)], (0, 0, 0), st, seg=14, axis='y')))  # mast boot
    A(ub(cyl(0.042, 0.62, (0, 2.66, 0), ch, axis='y', seg=12)))                                           # mast
    A(ub(cyl(0.16, 0.035, (0, 2.625, 0), st, axis='y', seg=16, bev=0.006)))                               # swashplate (the still half)
    for a in (0.6, 2.7, 4.8): A(ub(rod((math.cos(a) * 0.13, 2.62, math.sin(a) * 0.13), (math.cos(a) * 0.10, 2.42, math.sin(a) * 0.10), 0.012, ch, seg=6)))  # control rods

    # ---------------- tail: drive-shaft cover, fin, ventral fin + skid, stabiliser, gearbox
    dx = [-2.3, -2.6, -3.0, -3.45, -3.9, -4.35, -4.8, -5.2, -5.6, -6.12]
    A(uv_side(sweep([(x, top(x) - 0.008, 0) for x in dx], [0.05 - 0.012 * k / (len(dx) - 1) for k in range(len(dx))], pa, seg=10)))
    for x in (-3.0, -3.9, -4.8, -5.6): A(ub(cyl(0.058, 0.04, (x, top(x) - 0.008, 0), ch, axis='x', seg=10)))  # its clamps
    A(uv_side(side_x([(-5.62, 1.84), (-6.26, 2.98), (-6.72, 2.98), (-6.56, 1.86), (-6.2, 1.70)], 0.07, (0, 0, 0), pa, bev=0.022, seg=2)))
    A(uv_side(side_x([(-5.80, 1.78), (-6.44, 1.80), (-6.68, 1.05), (-6.44, 1.05)], 0.06, (0, 0, 0), pa, bev=0.02, seg=2)))
    A(ub(sweep([(-6.30, 1.22, 0), (-6.46, 1.02, 0), (-6.60, 0.95, 0), (-6.76, 0.97, 0)], 0.022, ch, seg=8)))          # tail skid
    A(sw(box((0.46, 0.05, 2.02), (-4.45, _YC(-4.45) + 0.02, 0), pa, bev=0.018, seg=2), 'pink'))                       # stabiliser
    for sz in (-1, 1):
        A(sw(side_x([(-4.16, 1.52), (-4.66, 1.48), (-4.78, 2.02), (-4.42, 2.02)], 0.04, (0, 0, sz * 1.01), pa, bev=0.013, seg=2), 'cyan'))  # end plates
        A(ub(rod((-4.45, 1.74, sz * 1.02), (-4.45, 1.74, sz * 1.055), 0.035, M['green' if sz > 0 else 'red'], seg=10)))                # nav lights
        A(ub(rod((-4.45, 1.74, sz * 1.015), (-4.45, 1.74, sz * 1.04), 0.045, ch, seg=10)))
    A(ub(cyl(0.09, 0.27, (TP[0], TP[1], -0.11), st, axis='z', seg=14, bev=0.012)))                                    # tail gearbox
    A(ub(cyl(0.028, 0.12, (TP[0], TP[1], -0.27), ch, axis='z', seg=8)))                                               # output shaft
    A(ub(ball(0.04, (-6.585, 1.90, 0), M['white'], seg=10, rings=6)))                                                 # tail light
    A(ub(cyl(0.045, 0.05, (-6.50, 2.99, 0), ch, axis='y', seg=10)))                                                   # beacon base
    A(ub(rod((-3.3, top(-3.3) - 0.01, 0.05), (-3.62, 2.52, 0.05), 0.008, tr, seg=6)))                                 # whip antenna
    A(ub(ball(0.018, (-3.62, 2.52, 0.05), tr, seg=8, rings=5)))

    # ---------------- landing gear: skids on two bowed cross tubes, steps, saddles
    for sz in (-1, 1):
        z = sz * 0.98
        A(ub(sweep([(1.82, 0.40, z), (1.73, 0.25, z), (1.58, 0.135, z), (1.36, 0.078, z), (1.1, 0.066, z), (-1.45, 0.066, z), (-1.64, 0.082, z)], 0.05, ch, seg=10)))
        A(ub(box((0.56, 0.028, 0.17), (0.38, 0.124, z), st, bev=0.008)))                                              # step
        for k in range(4): A(sw(box((0.03, 0.012, 0.15), (0.20 + k * 0.12, 0.139, z), pa), 'yellow'))                 # grip strips
        for x in (0.95, -0.75): A(ub(cyl(0.066, 0.17, (x, 0.066, z), tr, axis='x', seg=12, bev=0.006)))               # saddles
    for x in (0.95, -0.75):
        yb = bot(x)
        half = [(x, 0.09, 0.98), (x, 0.19, 0.955), (x, 0.31, 0.89), (x, 0.42, 0.79), (x, 0.51, 0.64), (x, yb + 0.04, 0.46), (x, yb + 0.07, 0.22), (x, yb + 0.075, 0.0)]
        A(ub(sweep([(p[0], p[1], -p[2]) for p in half] + half[-2::-1], 0.044, ch, seg=8)))

    # ---------------- the news gear: gimbal camera under the chin, downlink dome, blade antenna
    cy = bot(1.62)
    A(ub(cyl(0.045, 0.2, (1.62, cy - 0.06, 0), st, axis='y', seg=10)))
    A(ub(box((0.07, 0.07, 0.44), (1.62, cy - 0.075, 0), st, bev=0.02)))                                               # yoke
    for sz in (-1, 1): A(ub(box((0.05, 0.2, 0.035), (1.62, cy - 0.16, sz * 0.19), st, bev=0.012)))
    A(ub(ball(0.165, (1.62, cy - 0.215, 0), tr, seg=16, rings=10)))                                                   # the ball
    A(ub(rod((1.70, cy - 0.235, 0), (1.80, cy - 0.26, 0), 0.085, st, seg=12, bev=0.008)))                             # lens barrel
    A(ub(rod((1.74, cy - 0.245, 0), (1.803, cy - 0.261, 0), 0.066, M['lens'], seg=12)))
    A(sw(ball(0.15, (-0.35, bot(-0.35) + 0.01, 0), pa, scale=(1.25, 0.55, 1.0), seg=14, rings=8), 'white'))           # downlink dome
    A(ub(side_x([(0.52, bot(0.4) + 0.03), (0.22, bot(0.4) + 0.03), (0.16, bot(0.4) - 0.17), (0.28, bot(0.4) - 0.17)], 0.022, (0, 0, 0.2), tr, bev=0.006)))
    # ---------------- nose: landing light, pitot, wire cutter
    p = pt(2.14, -90); n = nrm(2.14, -90); n.z = 0; n.normalize()
    A(ub(rod(p - n * 0.05, p + n * 0.035, 0.075, ch, seg=12, bev=0.008)))
    A(ub(rod(p - n * 0.02, p + n * 0.039, 0.06, M['white'], seg=12)))
    q = surf(2.13, -38, 1, -0.03)
    A(ub(rod(q, q + V3((0.36, -0.01, 0.01)), 0.012, ch, seg=6)))
    A(ub(side_x([(0.84, 2.02), (1.03, 2.02), (1.31, 2.47), (1.25, 2.49)], 0.028, (0, 0, 0), st, bev=0.006)))

    # ---------------- doors: handles, hinges, fuel cap, the sticker
    for sz in (-1, 1):
        for x in (0.0, -0.24):
            A(ub(box((0.15, 0.036, 0.034), tuple(surf(x, -19, sz, 0.012)), ch, bev=0.01)))                            # handles
            for dx in (-0.05, 0.05): A(ub(box((0.022, 0.02, 0.034), tuple(surf(x + dx, -19, sz, 0.0)), ch)))
        for x in (0.98, -0.86):
            for t in (-24, 40): A(ub(box((0.07, 0.04, 0.03), tuple(surf(x, t, sz, 0.005)), ch, bev=0.008)))           # hinges
    c = surf(-1.25, -26, 1, 0.0); n = nrm(-1.25, -26, 1)
    A(ub(rod(c - n * 0.02, c + n * 0.012, 0.055, ch, seg=12, bev=0.005)))                                             # fuel cap
    A(decal((-2.15, -1.9, -1.65), (8, 26), 1, R_STICK, pa))

    # ---------------- cabin: floor, seats, bench, binnacle, sticks, dice
    YF = 0.66
    F = Mesh_()
    fx = [x for x in XS if CAB[1] - 1e-6 <= x <= 1.45] + [CAB[1] - 0.02]
    fx = sorted(set(fx), reverse=True)
    for xa, xb in zip(fx, fx[1:]):
        wa, wb = half_at(max(xa, CAB[1]), YF) - 0.02, half_at(max(xb, CAB[1]), YF) - 0.02
        F.f([V3((xa, YF, wa)), V3((xa, YF, -wa)), V3((xb, YF, -wb)), V3((xb, YF, wb))], V3((0, 1, 0)))
        F.f([V3((xa, YF - 0.03, wa)), V3((xa, YF - 0.03, -wa)), V3((xb, YF - 0.03, -wb)), V3((xb, YF - 0.03, wb))], V3((0, -1, 0)))
    w0 = half_at(fx[0], YF) - 0.02
    F.f([V3((fx[0], YF, w0)), V3((fx[0], YF, -w0)), V3((fx[0], YF - 0.03, -w0)), V3((fx[0], YF - 0.03, w0))], V3((1, 0, 0)))
    A(ub(F.obj('floor', [cb])))
    for sz in (-1, 1):
        z = sz * 0.275
        A(sw(box((0.46, 0.27, 0.36), (0.50, 0.775, z), pa, bev=0.045, seg=3), 'cyan'))
        A(sw(box((0.11, 0.64, 0.40), (0.245, 1.19, z), pa, bev=0.045, seg=3, rot=(0, 0, 0.14)), 'cyan'))
        A(sw(box((0.08, 0.17, 0.25), (0.16, 1.585, z), pa, bev=0.03, seg=2, rot=(0, 0, 0.14)), 'yellow'))
        A(ub(sweep([(0.84, YF - 0.01, z), (0.83, 0.90, z), (0.74, 1.04, z)], 0.014, ch, seg=6)))                      # cyclic
        A(ub(ball(0.034, (0.73, 1.055, z), tr, seg=8, rings=5)))
    A(ub(box((0.36, 0.13, 0.56), (-0.52, 0.71, 0), tr, bev=0.02)))                                                    # the bench's plinth
    A(sw(box((0.44, 0.17, 0.84), (-0.52, 0.835, 0), pa, bev=0.045, seg=3), 'cyan'))
    A(sw(box((0.11, 0.60, 0.94), (-0.79, 1.19, 0), pa, bev=0.045, seg=3, rot=(0, 0, 0.1)), 'cyan'))
    A(ub(rod((0.36, YF - 0.01, 0.03), (0.66, 0.90, 0.03), 0.016, ch, seg=6)))                                         # collective
    A(ub(rod((0.62, 0.874, 0.03), (0.70, 0.928, 0.03), 0.028, tr, seg=8)))
    A(ub(box((0.30, 0.55, 0.24), (1.42, 0.92, 0), tr, bev=0.03)))                                                     # pedestal
    A(ub(box((0.15, 0.36, 0.66), (1.52, 1.22, 0), tr, bev=0.03, rot=(0, 0, -0.22))))                                  # binnacle
    A(ub(box((0.26, 0.03, 0.72), (1.53, 1.415, 0), tr, bev=0.012, rot=(0, 0, -0.1))))                                 # glareshield
    pn = box((0.03, 0.29, 0.6), (1.44, 1.238, 0), M['panel'], rot=(0, 0, -0.22))                                      # the dials (lit)
    me, uv, mw = _uvl(pn)
    for li, lp in enumerate(me.loops):
        v = mw @ me.vertices[lp.vertex_index].co; k = 0.3 * (v.x - 1.44)
        uv[li].uv = (0.5 + (-v.y) / 0.6 * 0.96 + k, 0.5 + (v.z - 1.238) / 0.29 * 0.9 + k)
    A(pn)
    for k, (dx, dy, dz, r) in enumerate(((1.30, 1.70, 0.035, (0.3, 0.5, 0.2)), (1.325, 1.63, -0.04, (0.7, 0.2, 0.5)))):  # fuzzy dice
        A(uv_rect(box((0.075, 0.075, 0.075), (dx, dy, dz), pa, bev=0.012, rot=r), R_DICE))
        A(ub(rod((dx, dy + 0.02, dz), (1.30, top(1.30) - 0.02, 0.0), 0.004, tr, seg=4)))
    return B, [panes]


def build_rotor(M):
    R = []; A = R.append
    ch, st, tr = M['chrome'], M['steel'], M['trim']
    y = RP[1]
    def blade(sx):
        rs = [0.42, 0.56, 0.80, 1.6, 2.6, 3.6, 4.4, RR]
        cs = [0.13, 0.17, 0.26, 0.26, 0.26, 0.26, 0.26, 0.22]
        path = [(sx * r, y - 0.17 * ((r - 0.42) / (RR - 0.42)) ** 2, 0.0) for r in rs]   # parked: the tips droop
        def ring(i, t):
            c = cs[i]; th = 0.034 if i > 1 else 0.05
            return [(0.0, -0.34 * c), (th / 2, -0.20 * c), (th * 0.42, 0.12 * c), (0.004, 0.66 * c), (-0.004, 0.66 * c), (-th * 0.3, 0.12 * c), (-th / 2, -0.20 * c)]
        o = loft(path, ring, M['blade'], name='blade', smooth_angle=50)
        me, uv, mw = _uvl(o)
        for p in me.polygons:
            for li in p.loop_indices:
                v = mw @ me.vertices[me.loops[li].vertex_index].co
                r = abs(v.x); q = -v.y * sx                                   # along the span, across the chord (leading edge first)
                yl = v.z - (y - 0.17 * ((r - 0.42) / (RR - 0.42)) ** 2)      # height off the blade's own line
                uv[li].uv = (0.03 + 0.94 * (r - 0.42) / (RR - 0.42) + 0.05 * yl, min(0.98, max(0.02, 0.9 - (q + 0.09) / 0.26 * 0.8 + 2 * yl)))
        return o
    for sx in (-1, 1):
        A(blade(sx))
        A(ub(box((0.30, 0.085, 0.19), (sx * 0.47, y, 0), st, bev=0.02)))                       # blade grip
        for dz in (-0.05, 0.05): A(ub(cyl(0.022, 0.1, (sx * 0.53, y, dz), ch, axis='y', seg=8)))   # its bolts
        A(ub(box((0.05, 0.04, 0.2), (sx * 0.40, y - 0.02, sx * 0.13), st, bev=0.01)))          # pitch horn
        A(ub(rod((sx * 0.40, y - 0.03, sx * 0.2), (sx * 0.12, 2.665, sx * 0.1), 0.012, ch, seg=6)))  # pitch link
    A(ub(box((0.66, 0.075, 0.14), (0, y, 0), st, bev=0.02)))                                   # yoke
    A(ub(cyl(0.06, 0.27, (0, y, 0), ch, axis='z', seg=12, bev=0.01)))                          # teeter bolt
    A(ub(cyl(0.075, 0.11, (0, y + 0.06, 0), ch, axis='y', seg=12, bev=0.012)))                 # mast nut
    A(sw(ball(0.062, (0, y + 0.115, 0), M['paint'], scale=(1, 0.7, 1), seg=12, rings=6), 'yellow'))
    A(ub(cyl(0.15, 0.03, (0, 2.665, 0), ch, axis='y', seg=16, bev=0.006)))                     # swashplate (the turning half)
    A(ub(box((0.12, 0.07, 0.16), (0, 2.80, 0), st, bev=0.015)))                                # stabiliser bar: frame, bar, weights
    A(ub(rod((0, 2.80, -0.92), (0, 2.80, 0.92), 0.016, ch, seg=8)))
    for sz in (-1, 1):
        A(sw(lathe([(0.0, -0.11), (0.035, -0.09), (0.05, -0.03), (0.05, 0.03), (0.035, 0.09), (0.0, 0.11)], (0, 2.80, sz * 0.92), M['paint'], seg=10, axis='z'), 'yellow'))
        A(ub(rod((0, 2.80, sz * 0.08), (0, y - 0.02, sz * 0.05), 0.01, ch, seg=6)))
    return R


def build_tailrotor(M):
    Tt = []; A = Tt.append
    x, y, z = TP
    A(ub(cyl(0.055, 0.1, (x, y, z), M['steel'], axis='z', seg=10, bev=0.008)))
    A(ub(cyl(0.03, 0.03, (x, y, z - 0.06), M['chrome'], axis='z', seg=8)))
    for s in (-1, 1):
        o = box((0.14, 0.60, 0.022), (x, y + s * 0.42, z), M['blade'], bev=0.009, seg=2)
        me, uv, mw = _uvl(o)
        for p in me.polygons:
            for li in p.loop_indices:
                v = mw @ me.vertices[me.loops[li].vertex_index].co
                gz = -v.y - z
                uv[li].uv = (0.03 + 0.94 * (abs(v.z - y) - 0.1) / 0.62 + 0.3 * gz, 0.5 + (v.x - x) * 3.0 + 2.0 * gz)
        A(o)
        A(ub(box((0.07, 0.16, 0.036), (x, y + s * 0.11, z), M['steel'], bev=0.008)))
    j = join(Tt, 'tailrotor')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    c = gv(*TP)
    j.data.transform(Matrix.Translation(c) @ Matrix.Rotation(math.radians(24), 4, 'Y') @ Matrix.Translation(-c))  # parked a bit off upright
    return [j]


def build_lod1(M):
    """the far one: a coarse skin with the windows as dark swatches, slabs for the rest. all heli_paint"""
    pa = M['paint']
    Tl = [-90, -45, 8, 50, 90]; nl = len(Tl) - 1
    xl = [NOSE, 2.10, 1.02, -0.9, -2.15, TAIL]
    ring = lambda x: [pt(x, t, 1) for t in Tl] + [pt(x, t, -1) for t in Tl[-2:0:-1]]
    def gl(i, j):
        j = j if j < nl else 2 * nl - 1 - j
        return 1 if (i == 1 and j >= 2) or (i == 2 and j == 2) else 0
    hull = skin('lod_hull', [ring(x) for x in xl], [pa, pa], caps=(False, True), mfn=lambda i, j: gl(i, j) if i >= 0 else 0)
    uv_side(hull)
    me, uv, mw = _uvl(hull)   # the window cells (slot 1) take the glass swatch, then it's one material
    gx, gy, gw, gh = SW['glass']
    for p in me.polygons:
        if p.material_index == 1:
            for k, li in enumerate(p.loop_indices): uv[li].uv = ((gx + (2, 9, 9, 2)[k % 4]) / AW, 1 - (gy + (2, 2, 9, 9)[k % 4]) / (2 * AH))
            p.material_index = 0
    while len(me.materials) > 1: me.materials.pop(index=1)
    L = [hull]; A = L.append
    A(uv_side(side_x([(0.7, 2.0), (0.3, 2.42), (-1.5, 2.40), (-2.4, 1.85)], 0.56, (0, 0, 0), pa)))
    A(uv_side(side_x([(-5.62, 1.84), (-6.26, 2.98), (-6.72, 2.98), (-6.56, 1.80)], 0.06, (0, 0, 0), pa)))
    A(uv_side(side_x([(-5.80, 1.78), (-6.44, 1.80), (-6.68, 1.05), (-6.44, 1.05)], 0.05, (0, 0, 0), pa)))
    A(sw(box((0.46, 0.05, 2.02), (-4.45, _YC(-4.45) + 0.02, 0), pa), 'pink'))
    for sz in (-1, 1):
        A(sw(box((3.3, 0.1, 0.1), (-0.05, 0.05, sz * 0.98), pa), 'grey'))
        for x in (0.95, -0.75): A(sw(rod((x, 0.06, sz * 0.98), (x, bot(x) + 0.06, sz * 0.36), 0.04, pa, seg=3), 'grey'))
    A(sw(rod((0, 2.38, 0), (0, 2.95, 0), 0.06, pa, seg=4), 'grey'))
    A(sw(box((0.3, 0.5, 0.3), (1.62, 0.47, 0), pa), 'black'))
    A(sw(rod((-1.50, 2.30, 0), (-2.06, 2.60, 0), 0.09, pa, seg=4), 'grey'))
    rot = [sw(box((2 * RR, 0.03, 0.26), (0, RP[1] - 0.04, 0), pa), 'black'), sw(box((0.5, 0.12, 0.2), (0, RP[1], 0), pa), 'grey'),
           sw(box((0.03, 0.03, 1.84), (0, 2.80, 0), pa), 'grey')]
    tro = [sw(box((0.14, 2 * TR_R, 0.025), TP, pa, rot=(0, 0, math.radians(-24))), 'black'), sw(box((0.1, 0.1, 0.34), (TP[0], TP[1], -0.15), pa), 'grey')]
    return L, rot, tro


def tris_of(o):
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)


def tidy(o, ngons=True):
    """triangulate the flat caps (no n-gons in the file), drop anything collapsed"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges[:])
    if ngons:
        big = [f for f in bm.faces if len(f.verts) > 4]
        if big: bmesh.ops.triangulate(bm, faces=big)
    bm.to_mesh(o.data); bm.free()
    return o


GLOW = ('heli_red', 'heli_green', 'heli_lamp', 'heli_lens', 'heli_beacon', 'heli_panel')


def bake_ao(targets, dist=0.6, lo=0.45, samples=24, floor=True):
    """ambient occlusion into a vertex colour layer 'AO' (COLOR_0 in the glb: the game multiplies it in). like the map
    props' lib.bake_ao on the pipeline branch: each target is baked on its own with a ground plane under it"""
    sc = bpy.context.scene
    prev, prev_t = sc.render.engine, sc.render.bake.target
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    sc.world = sc.world or bpy.data.worlds.new('jf_world')
    sc.world.light_settings.distance = dist
    sc.render.bake.target = 'VERTEX_COLORS'
    meshes = [o for o in sc.objects if o.type == 'MESH']
    was = {o: o.hide_render for o in meshes}
    ground = box((400, 0.02, 400), pos=(0, -0.0105, 0), m=mat('jf_ao_floor', 0x808080), name='jf_ao_floor') if floor else None
    for t in targets:
        for o in meshes: o.hide_render = o is not t
        me = t.data
        for c in list(me.color_attributes): me.color_attributes.remove(c)
        ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER'); me.color_attributes.active_color = ca
        for s in bpy.context.view_layer.objects.selected: s.select_set(False)
        t.select_set(True); bpy.context.view_layer.objects.active = t
        bpy.ops.object.bake(type='AO', target='VERTEX_COLORS')
        ca = me.color_attributes['AO']
        glow = [m is not None and m.name in GLOW for m in me.materials]   # lamps stay bright
        for p in me.polygons:
            for li in p.loop_indices:
                v = 1.0 if glow[p.material_index] else lo + (1 - lo) * ca.data[li].color[0]
                ca.data[li].color = (v, v, v, 1.0)
    if ground: bpy.data.objects.remove(ground, do_unlink=True)
    for o, h in was.items(): o.hide_render = h
    sc.render.engine, sc.render.bake.target = prev, prev_t


def white_ao(o):
    me = o.data
    for c in list(me.color_attributes): me.color_attributes.remove(c)
    ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER'); me.color_attributes.active_color = ca
    for d in ca.data: d.color = (1, 1, 1, 1)


def qa(objs, tag, eps=0.001, tol=0.004):
    sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=eps, tol=tol)
    print('QA_PASS', tag, res.get('pass'), 'ground', res.get('ground_z'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], tag, e)
    for e in res.get('enclosed', []): print('QA_ENCLOSED', tag, e)
    for n, m in res.get('objects', {}).items():
        bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts', 'ngons', 'uv_zero_area_faces', 'boundary_edges') and v}
        print('QA_PART', tag, n, m.get('tris'), 'tris', m.get('materials'), 'mats', bad)
    return res


def build():
    M = materials()
    B, GLS = build_body(M)
    R = build_rotor(M)
    TRt = build_tailrotor(M)
    L1, R1, T1 = build_lod1(M)
    dome = ub(ball(0.058, (-6.50, 3.035, 0), M['beacon'], scale=(1, 1.25, 1), seg=10, rings=6))
    body = tidy(join(B, 'body'))
    glass = tidy(join(GLS, 'glass'))
    rotor = tidy(part(R, 'rotor', RP))
    tailrotor = tidy(part(TRt, 'tailrotor', TP))
    beacon = tidy(part([dome], 'beacon', (-6.50, 3.035, 0)))
    l_body = tidy(join(L1, 'body_lod1')); smooth(l_body, 40)
    l_rot = tidy(part(R1, 'rotor_lod1', RP)); l_tr = tidy(part(T1, 'tailrotor_lod1', TP))
    lod0, lod1 = [body, glass, rotor, tailrotor, beacon], [l_body, l_rot, l_tr]
    for o in lod0 + lod1:
        o.data.name = o.name
        bpy.context.view_layer.objects.active = o
        for s in bpy.context.view_layer.objects.selected: s.select_set(False)
        o.select_set(True); bpy.ops.object.material_slot_remove_unused()
        while len(o.data.uv_layers) > 1: o.data.uv_layers.remove(o.data.uv_layers[-1])
    if not arg('no-ao') and not arg('preview'):
        bake_ao([body, rotor, tailrotor], dist=0.6)
        bake_ao(lod1, dist=0.6, lo=0.55)
    else:
        for o in (body, rotor, tailrotor) + tuple(lod1): white_ao(o)
    white_ao(glass); white_ao(beacon)
    if arg('qa'):
        qa(lod0, 'lod0'); qa(lod1, 'lod1', tol=0.01)
    t0, t1 = sum(tris_of(o) for o in lod0), sum(tris_of(o) for o in lod1)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ V3(c) for o in lod0 for c in o.bound_box]
    lo = V3(map(min, *pts)); hi = V3(map(max, *pts))
    meta = {'kind': 'prop', 'id': 'heli', 'paint': 'heli_paint', 'front': '+x',
            'size': [round(hi.x - lo.x, 2), round(hi.z - lo.z, 2), round(hi.y - lo.y, 2)],   # long, tall, wide
            'rotor': {'node': 'rotor', 'pivot': list(RP), 'axis': 'y', 'r': RR},
            'tailrotor': {'node': 'tailrotor', 'pivot': list(TP), 'axis': 'z', 'r': TR_R},
            'beacon': 'beacon', 'glass': 'glass', 'lod': 70, 'tris': [t0, t1]}
    root = finish(FID, lod0, meta)
    e = _link(bpy.data.objects.new('lod1', None)); e.parent = root
    for o in lod1: apply_mods(o); o.parent = e
    mats0 = sorted({m.name for o in lod0 for m in o.data.materials}); mats1 = sorted({m.name for o in lod1 for m in o.data.materials})
    print(f'JF_PROP {FID}: lod0 {t0} tris {len(mats0)} mats, lod1 {t1} tris {len(mats1)} mats, size {meta["size"]}')
    print('JF_PARTS', {o.name: tris_of(o) for o in lod0 + lod1})
    return root, lod0, lod1, (t0, t1, len(mats0), len(mats1), meta['size'])


def export_glb(root, file_id):
    os.makedirs(lib.MODELS, exist_ok=True)
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    root.select_set(True)
    for c in root.children_recursive: c.select_set(True)
    path = os.path.join(lib.MODELS, file_id + '.glb')
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_extras=True, export_yup=True,
              export_texcoords=True, export_normals=True, export_materials='EXPORT', export_image_format='AUTO', export_lights=False, export_cameras=False)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_vertex_color' in props: kw['export_vertex_color'] = 'ACTIVE'   # (4.2+: the AO goes out as COLOR_0 whatever the material uses)
    if 'export_all_vertex_colors' in props: kw['export_all_vertex_colors'] = False
    if 'export_active_vertex_color_when_no_material' in props: kw['export_active_vertex_color_when_no_material'] = True
    bpy.ops.export_scene.gltf(**kw)
    print(f'JF_EXPORT {file_id}: {os.path.getsize(path) // 1024} KB')
    return path


# ------------------------------------------------------------ review renders
def ao_into_materials(objs):
    """the game multiplies the baked AO in: show it in the review renders too (after the export, the glb is untouched)"""
    done = set()
    for o in objs:
        for m in o.data.materials:
            if m is None or m.name in done or m.name in ('heli_glass',): continue
            done.add(m.name)
            nt = m.node_tree; b = nt.nodes['Principled BSDF']
            ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'AO'
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
            src = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].links else None
            if src is not None: nt.links.new(src, mix.inputs[6])
            else: mix.inputs[6].default_value = b.inputs['Base Color'].default_value
            nt.links.new(ca.outputs['Color'], mix.inputs[7])
            nt.links.new(mix.outputs[2], b.inputs['Base Color'])


def _blur(a, r):
    for ax in (0, 1):
        c = np.cumsum(np.concatenate([np.zeros_like(np.take(a, [0], axis=ax)), a], axis=ax), axis=ax)
        n = a.shape[ax]
        i0 = np.clip(np.arange(n) - r, 0, n); i1 = np.clip(np.arange(n) + r + 1, 0, n)
        a = (np.take(c, i1, axis=ax) - np.take(c, i0, axis=ax)) / (2 * r + 1)
    return a


def bloom(img, k=1.0):
    """the glow the 4.0 sheets got from EEVEE's bloom (gone in 4.2+): bright bits bleed"""
    b = np.clip((img.max(axis=2, keepdims=True) - 0.86) / 0.14, 0, 1) * img
    out = img + k * (0.30 * _blur(_blur(b, 5), 5) + 0.28 * _blur(_blur(b, 16), 16))
    return np.clip(out, 0, 1)


class Studio:
    def __init__(s, lo, hi, bg=0x3a3346, bg_k=0.55, samples=32, exposure=0.0):
        sc = bpy.context.scene
        for e in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
            try: sc.render.engine = e; break
            except TypeError: pass
        ee = sc.eevee; ee.taa_render_samples = samples
        for k, v in (('use_gtao', True), ('use_ssr', True), ('use_bloom', False), ('use_soft_shadows', True), ('use_raytracing', True)):
            if hasattr(ee, k): setattr(ee, k, v)
        sc.render.film_transparent = False
        sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = exposure
        w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
        w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(bg)
        w.node_tree.nodes['Background'].inputs['Strength'].default_value = bg_k
        s.lo, s.hi = V3(lo), V3(hi)   # game coords
        s.c = (s.lo + s.hi) / 2; s.size = (s.hi - s.lo).length
        s.made = []
        s.cam = _link(bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))); sc.camera = s.cam

    def light(s, energy, loc, sz=1.0, col=(1, 1, 1), about=None, size=None):
        """an area light at about + loc * size (loc in blender axes, like lib.sheet's rig), aimed at about"""
        size = size or s.size; c = gv(*(about if about is not None else s.c))
        L = bpy.data.lights.new('AREA', 'AREA'); L.energy = energy * size * size; L.color = col; L.size = sz * size
        o = _link(bpy.data.objects.new('AREA', L)); o.location = c + V3(loc) * size
        o.rotation_euler = (c - o.location).to_track_quat('-Z', 'Y').to_euler()
        s.made.append(o)
        return o

    def clear(s):
        for o in s.made: bpy.data.objects.remove(o, do_unlink=True)
        s.made = []

    def rig(s, about=None, size=None):
        s.clear()
        s.light(200, (1.2, -1.4, 1.6), 1.2, about=about, size=size)
        s.light(70, (-1.6, -0.6, 0.6), 1.5, (0.85, 0.9, 1.0), about, size)
        s.light(150, (-0.4, 1.8, 1.2), 0.6, (1.0, 0.8, 0.95), about, size)
        s.light(40, (0.2, 0.2, -1.6), 1.5, (0.9, 0.85, 1.0), about, size)

    def shoot(s, path, res, d, target=None, dist=None, lens=50, ortho=None, roll=None):
        """d = the direction from the target to the camera (game coords). ortho = the view's width in metres"""
        sc = bpy.context.scene
        sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
        t = gv(*(target if target is not None else s.c)); dv = gv(*d).normalized()
        cd = s.cam.data
        if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho; s.cam.location = t + dv * s.size * 3
        else: cd.type = 'PERSP'; cd.lens = lens; s.cam.location = t + dv * dist
        s.cam.rotation_euler = (t - s.cam.location).to_track_quat('-Z', 'Y').to_euler()
        if roll is not None: s.cam.rotation_euler = Euler(roll)
        cd.clip_start = 0.05; cd.clip_end = s.size * 30
        sc.render.filepath = path; sc.render.image_settings.file_format = 'PNG'
        bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(path)
        a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[::-1, :, :3].copy()
        bpy.data.images.remove(im); os.remove(path)
        return a


def save_img(a, path, q=3):
    """a = h x w x 3 top-down floats -> jpg (png without ffmpeg)"""
    h, w = a.shape[:2]
    rgba = np.ones((h, w, 4), np.float32); rgba[:, :, :3] = a[::-1]
    img = bpy.data.images.new('out', w, h); img.pixels.foreach_set(rgba.ravel())
    png = os.path.splitext(path)[0] + '_tmp.png'
    img.filepath_raw = png; img.file_format = 'PNG'; img.save(); bpy.data.images.remove(img)
    if path.endswith('.jpg') and os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v {q} "{path}"') == 0: os.remove(png)
    else: path = os.path.splitext(path)[0] + '.png'; os.replace(png, path)
    print('JF_SHEET', path)
    return path


def show(objs, on):
    for o in objs: o.hide_render = not on


def bounds(objs):
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ V3(c) for o in objs for c in o.bound_box]
    lo = V3(map(min, *pts)); hi = V3(map(max, *pts))
    return V3((lo.x, lo.z, -hi.y)), V3((hi.x, hi.z, -lo.y))   # game axes


def sheet9(lod0, lod1, info, out_dir, name=FID, res=(760, 420), samples=32, only=None):
    """the turnaround: 3/4, both sides, top, front, rear 3/4, two close-ups and the far LOD, tiled 3 x 3"""
    t0, t1, m0, m1, size = info
    lo, hi = bounds(lod0)
    S = Studio(lo, hi, samples=samples, exposure=-0.3)
    c = S.c; L, H, W = hi.x - lo.x, hi.y - lo.y, hi.z - lo.z
    asp = res[0] / res[1]
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, '_heli_tmp.png')
    side_w = max(L, H * asp) * 1.06
    views = [
        ('persp', dict(d=(1.0, 0.52, 1.15), dist=S.size * 1.32, target=c + V3((0.3, -0.25, 0)))),
        ('left', dict(d=(0, 0, -1), ortho=side_w)),
        ('right', dict(d=(0, 0, 1), ortho=side_w)),
        ('top', dict(d=(0, 1, 0), ortho=side_w, roll=(0, 0, 0))),
        ('front', dict(d=(1, 0, 0), ortho=max(W, H * asp) * 1.16)),
        ('back_persp', dict(d=(-1.0, 0.62, -1.2), dist=S.size * 1.32, target=c + V3((0.3, -0.25, 0)))),
        ('cabin', dict(d=(1.0, 0.16, -0.8), dist=8.0, target=V3((0.6, 1.4, 0)))),
        ('tail', dict(d=(-0.75, 0.3, -1.0), dist=6.4, target=V3((-5.3, 1.85, 0)))),
        ('lod1', dict(d=(1.0, 0.52, 1.15), dist=S.size * 1.32, target=c + V3((0.3, -0.25, 0)))),
    ]
    tiles = []
    for k, kw in views:
        if only and k not in only: continue
        kw = dict(kw); rg = kw.pop('rig', None)
        S.rig(*(rg or (None, None)))
        show(lod0, k != 'lod1'); show(lod1, k == 'lod1')
        a = bloom(S.shoot(tmp, res, **kw))
        if k == 'lod1': text_px(a, 'LOD1 FAR', 8, 8, 2, 0x4fd8ff)
        if k == 'cabin': text_px(a, 'CABIN', 8, 8, 2, 0x4fd8ff)
        if k == 'tail': text_px(a, 'TAIL', 8, 8, 2, 0x4fd8ff)
        tiles.append(a)
    show(lod0, True); show(lod1, False)
    S.clear()
    cols = min(3, len(tiles)); rows = (len(tiles) + cols - 1) // cols
    Hh, Ww = res[1], res[0]
    lab = np.zeros((27, cols * Ww + 4 * (cols + 1), 3), np.float32)
    txt = f'{name}  LOD0 {t0} TRIS {m0} MATS  LOD1 {t1} TRIS {m1} MATS  {size[0]:.2f}M LONG {size[1]:.2f}M TALL {size[2]:.2f}M WIDE'.upper().replace('_', ' ')
    text_px(lab, txt, 6, 3, 3, 0xffe14d)
    canvas = np.full((rows * Hh + 4 * (rows + 1), lab.shape[1], 3), 0.08, np.float32)
    for i, a in enumerate(tiles):
        r, cc = divmod(i, cols)
        y0 = 4 + r * (Hh + 4); x0 = 4 + cc * (Ww + 4)
        canvas[y0:y0 + Hh, x0:x0 + Ww] = a
    return save_img(np.concatenate([lab, canvas], axis=0), os.path.join(out_dir, name + '.jpg'))


def hero(lod0, rotor, out, res=(1280, 720), samples=48):
    """one nicer 3/4 picture: a dark floor, the game's pink and cyan as rim lights, the rotor turned off the axis"""
    lo, hi = bounds(lod0)
    S = Studio(lo, hi, bg=0x241a34, bg_k=0.45, samples=samples, exposure=-0.25)
    fm = mat('heli_hero_floor', 0x241a30, rough=0.6, metal=0.0)
    floor = cyl(80, 0.02, (0, -0.011, 0), fm, axis='y', seg=64, name='hero_floor')
    rot0 = rotor.rotation_euler.copy()
    rotor.rotation_euler = Euler((0, 0, math.radians(18)))   # (blender z = the game's y)
    about = V3((-0.6, 1.5, 0)); sz = 9.0
    S.light(120, (1.3, -1.5, 1.5), 1.3, (1.0, 0.97, 0.94), about, sz)           # key: front right, high
    S.light(45, (-0.2, 0.2, 2.2), 2.2, (1.0, 1.0, 1.0), about, sz)              # a big soft box overhead (the clear coat's highlight)
    S.light(80, (-1.9, 1.3, 0.9), 0.8, (1.0, 0.25, 0.85), about, sz)           # magenta rim from behind
    S.light(70, (1.4, 1.9, 0.8), 0.8, (0.3, 0.85, 1.0), about, sz)              # cyan rim from the far side
    S.light(22, (1.8, -0.4, 0.15), 1.6, (0.9, 0.9, 1.0), about, sz)             # low fill on the nose
    a = S.shoot(os.path.splitext(out)[0] + '_r.png', res, d=(1.0, 0.2, 0.86), dist=17.0, lens=52, target=V3((-0.55, 1.45, 0.0)))
    a = bloom(a, 0.7)
    rotor.rotation_euler = rot0
    bpy.data.objects.remove(floor, do_unlink=True)
    S.clear()
    return save_img(a, out, q=2)


def main():
    lib.reset(); lib._mats.clear()
    if isinstance(arg('out'), str): lib.MODELS = lib.SHEETS = arg('out')   # (a scratch folder, for trying things)
    root, lod0, lod1, info = build()
    pv = arg('preview')
    if isinstance(pv, str):
        ao_into_materials(lod0 + lod1)
        only = arg('views').split(',') if isinstance(arg('views'), str) else ['persp', 'right']
        sheet9(lod0, lod1, info, pv, name='heli_preview', res=(960, 540), samples=int(arg('samples', 12)), only=only)
        return
    if not arg('no-export'): export_glb(root, FID)
    if not arg('no-sheet') or not arg('no-hero'): ao_into_materials(lod0 + lod1)
    if not arg('no-sheet'): sheet9(lod0, lod1, info, lib.SHEETS)
    if not arg('no-hero'):
        show(lod1, False)
        hero(lod0, lod0[2], os.path.join(lib.SHEETS, 'heli_hero.jpg'), samples=int(arg('samples', 48)))


main()
