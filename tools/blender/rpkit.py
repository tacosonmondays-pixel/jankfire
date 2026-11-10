# REVENUE PROTECTION's kit (OVERDUE, the train boss): a mesh buffer that takes thousands of small primitives without
# making a Blender object for each (the mass is ~150 fused commuters), low-poly people parts (heads, torsos, limbs with a
# two-bone reach, flat / gripping hands), atlases with a metal / roughness map, vertex-colour tint x baked AO (COLOR_0),
# the asset-QA gate, the glb export and the studio pictures. Everything takes GAME coordinates (three.js: x right, y up,
# z toward the viewer of the mask), like lib.py. Blender 5.2 (blender52).
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _link, _image, _look_at
import lib
from mathutils import noise as mnoise

V3 = Vector
ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(k, d=None):
    for a in ARGV:
        if a.startswith('--' + k + '='): return a.split('=', 1)[1]
        if a == '--' + k: return True
    return d


def g_of(v): return V3((v.x, v.z, -v.y))  # blender -> game


def lerp(a, b, t): return a + (b - a) * t


class Rnd:
    """a small seeded generator (its own stream per thing, so adding a figure doesn't reshuffle the others)"""
    def __init__(s, seed): s.r = random.Random(seed)
    def u(s, a=0.0, b=1.0): return s.r.uniform(a, b)
    def pick(s, seq): return seq[s.r.randrange(len(seq))]
    def chance(s, p): return s.r.random() < p
    def i(s, a, b): return s.r.randint(a, b)
    def sign(s): return 1 if s.r.random() < 0.5 else -1


def fbm(x, y, z=0.0, oct=3):
    v = 0.0; a = 0.5; f = 1.0
    for _ in range(oct):
        v += a * mnoise.noise(V3((x * f, y * f, z * f + 7.3))); a *= 0.5; f *= 2.03
    return v  # about -0.6 .. 0.6


# ------------------------------------------------------------ game-space matrices
def T(x, y=None, z=None):
    if y is None: x, y, z = x
    return Matrix.Translation(V3((x, y, z)))


def RX(a): return Matrix.Rotation(a, 4, 'X')
def RY(a): return Matrix.Rotation(a, 4, 'Y')
def RZ(a): return Matrix.Rotation(a, 4, 'Z')
def SC(x, y=None, z=None):
    if y is None: y = z = x
    m = Matrix.Identity(4); m[0][0], m[1][1], m[2][2] = x, y, z
    return m


def frame(z_axis, y_hint=(0, 1, 0), pos=(0, 0, 0)):
    """a matrix whose local +z points along z_axis and whose +y leans toward y_hint (game space)"""
    z = V3(z_axis).normalized(); y = V3(y_hint)
    if abs(z.dot(y.normalized())) > 0.995: y = V3((1, 0, 0)) if abs(z.x) < 0.9 else V3((0, 0, 1))
    x = y.cross(z).normalized(); y = z.cross(x)
    m = Matrix.Identity(4)
    for i in range(3): m[i][0], m[i][1], m[i][2], m[i][3] = x[i], y[i], z[i], pos[i]
    return m


C_B2G = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))  # blender (x, y, z) -> game (x, z, -y)
C_G2B = C_B2G.inverted()


def set_game_matrix(o, M):
    """give a blender object the transform that exports as game-space matrix M (meshes are authored through gv())"""
    o.matrix_basis = C_G2B @ M @ C_B2G


# ------------------------------------------------------------ primitives: (verts, faces, uvs[, tags]) in game metres
# uvs are an unwrap in metres (one list of (u, v) per face); Buf.add turns them into a tile or fits them in a swatch.
def p_box(sx, sy, sz, taper=1.0, top=True, bottom=True, shear=(0.0, 0.0)):
    """centred box. taper scales the +z face (x and y); shear moves it sideways"""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    tx, ty = (taper, taper) if not isinstance(taper, (tuple, list)) else taper
    V = [V3((-hx, -hy, -hz)), V3((hx, -hy, -hz)), V3((hx, hy, -hz)), V3((-hx, hy, -hz)),
         V3((-hx * tx + shear[0], -hy * ty + shear[1], hz)), V3((hx * tx + shear[0], -hy * ty + shear[1], hz)),
         V3((hx * tx + shear[0], hy * ty + shear[1], hz)), V3((-hx * tx + shear[0], hy * ty + shear[1], hz))]
    F = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    UV = [[(0, 0), (sx, 0), (sx, sz), (0, sz)], [(sx, 0), (sx + sy, 0), (sx + sy, sz), (sx, sz)],
          [(sx + sy, 0), (2 * sx + sy, 0), (2 * sx + sy, sz), (sx + sy, sz)], [(2 * sx + sy, 0), (2 * sx + 2 * sy, 0), (2 * sx + 2 * sy, sz), (2 * sx + sy, sz)]]
    if top: F.append((4, 5, 6, 7)); UV.append([(0, sz), (sx, sz), (sx, sz + sy), (0, sz + sy)])
    if bottom: F.append((3, 2, 1, 0)); UV.append([(sx, sz), (2 * sx, sz), (2 * sx, sz + sy), (sx, sz + sy)])
    return V, F, UV


def ring(c, N, B, ra, rb, k, phase=0.0, fn=None):
    out = []
    for j in range(k):
        t = phase + 2 * math.pi * j / k
        s = fn(j, t) if fn else 1.0
        out.append(c + N * (math.cos(t) * ra * s) + B * (math.sin(t) * rb * s))
    return out


def p_loft(rings, cap0=False, cap1=False, tip0=None, tip1=None, vscale=1.0):
    """skin through rings (each wound counter-clockwise about the path direction). cap = a flat fan, tip = a point"""
    k = len(rings[0]); V = []; F = []; UV = []
    for r in rings: V.extend(r)
    per = [0.0]
    for j in range(k): per.append(per[-1] + (rings[0][(j + 1) % k] - rings[0][j]).length)
    L = [0.0]
    for a, b in zip(rings, rings[1:]): L.append(L[-1] + (sum(b, V3()) / k - sum(a, V3()) / k).length * vscale)
    for i in range(len(rings) - 1):
        for j in range(k):
            jj = (j + 1) % k
            F.append((i * k + j, i * k + jj, (i + 1) * k + jj, (i + 1) * k + j))
            UV.append([(per[j], L[i]), (per[j + 1], L[i]), (per[j + 1], L[i + 1]), (per[j], L[i + 1])])
    def fan(ri, pt, flip):
        c = pt if pt is not None else sum(rings[ri], V3()) / k
        V.append(c); ci = len(V) - 1
        rad = max((p - c).length for p in rings[ri])
        for j in range(k):
            jj = (j + 1) % k
            a, b = ri * k + j, ri * k + jj
            F.append((b, a, ci) if flip else (a, b, ci))
            u0, u1 = per[j], per[j + 1]; v0 = L[ri]; dv = -rad if flip else rad
            UV.append([(u1, v0), (u0, v0), ((u0 + u1) / 2, v0 + dv)] if flip else [(u0, v0), (u1, v0), ((u0 + u1) / 2, v0 + dv)])
    if cap0 or tip0 is not None: fan(0, tip0, True)
    if cap1 or tip1 is not None: fan(len(rings) - 1, tip1, False)
    return V, F, UV


def path_frames(pts, up=None):
    """tangent / normal / binormal along a path (parallel transport: no twisting)"""
    n = len(pts); Tn = []
    for i in range(n):
        t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        Tn.append(t.normalized() if t.length > 1e-9 else V3((0, 0, 1)))
    u = V3(up) if up is not None else V3((0, 1, 0))
    if abs(Tn[0].dot(u)) > 0.95: u = V3((1, 0, 0)) if abs(Tn[0].x) < 0.9 else V3((0, 0, 1))
    N = (u - Tn[0] * Tn[0].dot(u)).normalized(); out = []
    for i in range(n):
        N = (N - Tn[i] * Tn[i].dot(N))
        N = N.normalized() if N.length > 1e-9 else Tn[i].orthogonal().normalized()
        out.append((Tn[i], N, Tn[i].cross(N)))
    return out


def p_tube(pts, radii, k=6, squash=1.0, up=None, cap0=False, cap1=False, tip0=None, tip1=None, phase=0.0, twist=0.0, fn=None):
    """a tube along game points with a radius per point. squash = the binormal radius / the normal one"""
    pts = [V3(p) for p in pts]
    rr = list(radii) if isinstance(radii, (list, tuple)) else [radii] * len(pts)
    fr = path_frames(pts, up)
    rings = [ring(p, N, B, r, r * squash, k, phase + twist * i, (lambda j, t, i=i: fn(i, j, t)) if fn else None) for i, (p, r, (Tt, N, B)) in enumerate(zip(pts, rr, fr))]
    return p_loft(rings, cap0, cap1, tip0, tip1)


def p_prism(n, r, h, r1=None, top=True, bottom=False, phase=0.0, dome=0.0):
    """an n-sided prism / frustum along +z from z = 0 to h (bolt heads, studs, cans)"""
    r1 = r if r1 is None else r1
    a = [V3((math.cos(phase + 2 * math.pi * j / n) * r, math.sin(phase + 2 * math.pi * j / n) * r, 0)) for j in range(n)]
    b = [V3((math.cos(phase + 2 * math.pi * j / n) * r1, math.sin(phase + 2 * math.pi * j / n) * r1, h)) for j in range(n)]
    return p_loft([a, b], cap0=bottom, cap1=False, tip1=V3((0, 0, h + dome)) if top else None)


def p_quad(a, b, c, d):
    a, b, c, d = V3(a), V3(b), V3(c), V3(d)
    w = (b - a).length; h = (d - a).length
    return [a, b, c, d], [(0, 1, 2, 3)], [[(0, 0), (w, 0), (w, h), (0, h)]]


def p_grid(P, flip=False):
    """a sheet through rows of points (cloth scraps, dents): P[i][j]"""
    n, k = len(P), len(P[0]); V = [V3(p) for row in P for p in row]; F = []; UV = []
    for i in range(n - 1):
        for j in range(k - 1):
            q = (i * k + j, i * k + j + 1, (i + 1) * k + j + 1, (i + 1) * k + j)
            F.append(q[::-1] if flip else q)
            uv = [(j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1)]
            UV.append(uv[::-1] if flip else uv)
    return V, F, UV


def p_ellipsoid(rx, ry, rz, k=8, rings_n=5, y0=-1.0, y1=1.0):
    """a faceted egg, poles on y. y0 / y1 cut it short of a pole (an open neck, a flat back)"""
    R = []; tips = [None, None]
    for i in range(rings_n + 1):
        t = lerp(-math.pi / 2, math.pi / 2, i / rings_n); yy = math.sin(t); rr = math.cos(t)
        yy = max(y0, min(y1, yy))
        if rr < 1e-4: tips[0 if i == 0 else 1] = V3((0, yy * ry, 0)); continue
        R.append([V3((math.sin(2 * math.pi * j / k) * rx * rr, yy * ry, math.cos(2 * math.pi * j / k) * rz * rr)) for j in range(k)])
    return p_loft(R, tip0=tips[0], tip1=tips[1])


def xf(prim, M):
    return [M @ v for v in prim[0]], prim[1], prim[2]


def merge(*prims):
    V = []; F = []; UV = []
    for p in prims:
        b = len(V); V.extend(p[0]); F.extend(tuple(b + i for i in f) for f in p[1]); UV.extend(p[2])
    return V, F, UV


# ------------------------------------------------------------ the buffer
class Buf:
    """collects primitives for one mesh. style = ('tile', metres per repeat) | ('fit', rect, tex[, margin px]) (the
    primitive's whole unwrap into a pixel rect) | ('face', rect, tex, axis) (seen straight on along a local axis: decals)
    | ('fn', f) (f(game vertex) -> uv). tint multiplies the texture (vertex colours)."""
    def __init__(s, name): s.name = name; s.V = []; s.F = []; s.UV = []; s.MI = []; s.TI = []; s.mats = []

    def mi(s, m):
        if m not in s.mats: s.mats.append(m)
        return s.mats.index(m)

    def add(s, prim, m, style=('tile', 0.5), M=None, tint=(1, 1, 1), flip=False, jit=0.0, jf=6.0):
        """jit = push every vertex about by this much (metres) with a smooth noise of its place: nothing stays a clean prism"""
        V, F, UV = prim[:3]
        if isinstance(tint, (int, float)): tint = (tint, tint, tint)
        b = len(s.V); mi = s.mi(m)
        det = M.to_3x3().determinant() if M is not None else 1.0
        flip = flip != (det < 0)
        Vw = [M @ v for v in V] if M is not None else list(V)
        if jit: Vw = [v + V3((mnoise.noise(v * jf), mnoise.noise(v * jf + V3((31.7, 0, 0))), mnoise.noise(v * jf + V3((0, 47.1, 0))))) * (jit * 2) for v in Vw]
        s.V.extend(Vw)
        kind = style[0]
        if kind == 'fit':
            us = [u for f in UV for u, v in f]; vs = [v for f in UV for u, v in f]
            u0, v0 = min(us), min(vs); du = (max(us) - u0) or 1.0; dv = (max(vs) - v0) or 1.0
            rect, tex = style[1], style[2]; mg = style[3] if len(style) > 3 else 0.5
            def uvf(fi, ci, vi): u, v = UV[fi][ci]; return px_uv(rect, tex, (u - u0) / du, (v - v0) / dv, mg)
        elif kind == 'tile':
            k = style[1]; ou, ov = (style[2], style[3]) if len(style) > 3 else (0.0, 0.0)
            def uvf(fi, ci, vi): u, v = UV[fi][ci]; return (u / k + ou, v / k + ov)
        elif kind == 'face':
            rect, tex, ax = style[1], style[2], style[3]; mg = style[4] if len(style) > 4 else 0.5
            a, bb = {'z': (0, 1), '-z': (0, 1), 'y': (0, 2), 'x': (2, 1)}[ax]
            lo = [min(v[i] for v in V) for i in range(3)]; ex = [(max(v[i] for v in V) - lo[i]) or 1.0 for i in range(3)]
            def uvf(fi, ci, vi):
                p = V[vi]; su = (p[a] - lo[a]) / ex[a]; sv = (p[bb] - lo[bb]) / ex[bb]
                if ax in ('-z', 'x'): su = 1 - su
                return px_uv(rect, tex, su, sv, mg)
        elif kind == 'quad':  # every face on the whole swatch (crust at one pixel size whatever the part's size)
            rect, tex = style[1], style[2]; mg = style[3] if len(style) > 3 else 0.5
            Q4 = ((0, 0), (1, 0), (1, 1), (0, 1)); Q3 = ((0, 0), (1, 0), (0.5, 1))
            def uvf(fi, ci, vi):
                n = len(F[fi]); q = (Q4 if n == 4 else Q3)[(ci + fi) % n] if n in (3, 4) else (0.5 + 0.5 * math.cos(6.283 * ci / n), 0.5 + 0.5 * math.sin(6.283 * ci / n))
                return px_uv(rect, tex, q[0], q[1], mg)
        else:
            fn = style[1]
            def uvf(fi, ci, vi): return fn(Vw[vi])
        for fi, f in enumerate(F):
            idx = list(range(len(f)))
            if flip: idx = idx[::-1]
            s.F.append(tuple(b + f[c] for c in idx))
            s.UV.append([uvf(fi, c, f[c]) for c in idx])
            s.MI.append(mi); s.TI.append(tint)
        return s

    def tris(s): return sum(len(f) - 2 for f in s.F)

    def obj(s, sharp=42, weld=0.0):
        me = bpy.data.meshes.new(s.name)
        me.from_pydata([tuple(gv(*v)) for v in s.V], [], s.F)
        uv = me.uv_layers.new(name='UVMap')
        flat = [c for f in s.UV for p in f for c in p]
        uv.data.foreach_set('uv', flat)
        me.polygons.foreach_set('material_index', s.MI)
        for m in s.mats: me.materials.append(m)
        ca = me.color_attributes.new('tint', 'BYTE_COLOR', 'CORNER')
        cols = [c for f, t in zip(s.F, s.TI) for _ in f for c in (t[0], t[1], t[2], 1.0)]
        ca.data.foreach_set('color', cols)
        me.polygons.foreach_set('use_smooth', [True] * len(s.F))
        me.update(); me.validate()
        o = _link(bpy.data.objects.new(s.name, me))
        if weld > 0:
            bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld); bm.to_mesh(me); bm.free()
        fix_uv(o)
        me.set_sharp_from_angle(angle=math.radians(sharp))
        return o


def px_uv(rect, tex, s, t, m=0.5):
    """(s, t) in 0..1 inside a pixel rect (x, y from the top, w, h) of a tex (w, h) -> blender uv, m px inside"""
    x, y, w, h = rect[:4]
    return ((x + m + s * (w - 2 * m)) / tex[0], 1 - (y + m + (1 - t) * (h - 2 * m)) / tex[1])


def fix_uv(o):
    """faces whose UVs collapsed to a line get a tiny triangle round their own middle (nothing with zero UV area)"""
    me = o.data; uv = me.uv_layers.active.data
    for pg in me.polygons:
        L_ = list(pg.loop_indices); P = [V3((uv[i].uv[0], uv[i].uv[1], 0)) for i in L_]
        ar = sum(P[k].x * P[(k + 1) % len(P)].y - P[(k + 1) % len(P)].x * P[k].y for k in range(len(P))) / 2
        if abs(ar) > 1e-9: continue
        c = sum(P, V3()) / len(P)
        for k, i in enumerate(L_):
            t = 2 * math.pi * k / len(L_); uv[i].uv = (c.x + 0.0008 * math.cos(t), c.y + 0.0008 * math.sin(t))
    return o


# ------------------------------------------------------------ atlases: colour + (occlusion, roughness, metal)
class Atlas:
    """a small texture with named pixel rects, and a matching roughness / metal map when asked"""
    def __init__(s, name, w, h, rough=0.6, metal=0.0):
        s.name = name; s.w, s.h = w, h; s.px = np.zeros((h, w, 3), np.float32)
        s.orm = np.ones((h, w, 3), np.float32); s.orm[:, :, 1] = rough; s.orm[:, :, 2] = metal
        s.R = {}; s.tex = (w, h)

    def cell(s, key, x, y, w, h, col=None, rough=None, metal=None, var=0.0, seed=1, speck=None, speck_p=0.0):
        s.R[key] = (x, y, w, h)
        if col is not None:
            r = np.random.default_rng(seed)
            n = r.random((h, w, 1)) if var else 0.5
            s.px[y:y + h, x:x + w] = hexrgb(col)[None, None] * (1 - var + 2 * var * n)
            if speck is not None: sub = s.px[y:y + h, x:x + w]; sub[r.random((h, w)) < speck_p] = hexrgb(speck)
        if rough is not None: s.orm[y:y + h, x:x + w, 1] = rough
        if metal is not None: s.orm[y:y + h, x:x + w, 2] = metal
        return s.px[y:y + h, x:x + w]

    def sub(s, key): x, y, w, h = s.R[key]; return s.px[y:y + h, x:x + w]
    def sub_orm(s, key): x, y, w, h = s.R[key]; return s.orm[y:y + h, x:x + w]
    def fit(s, key, m=0.5): return ('fit', s.R[key], s.tex, m)
    def quad(s, key, m=0.5): return ('quad', s.R[key], s.tex, m)
    def face(s, key, ax='z', m=0.5): return ('face', s.R[key], s.tex, ax, m)

    def material(s, mname, rough=0.6, metal=0.0, use_orm=False, emit=None, strength=1.0, emit_px=None):
        img = _image(s.name + '_t', np.clip(s.px, 0, 1))
        m = mat(mname, 0xffffff, rough=rough, metal=metal, tex=img)
        nt = m.node_tree; b = nt.nodes['Principled BSDF']
        if use_orm:
            im2 = bpy.data.images.new(s.name + '_mr', s.w, s.h, alpha=False)
            a = np.ones((s.h, s.w, 4), np.float32); a[:, :, :3] = s.orm[::-1]
            im2.pixels.foreach_set(a.ravel()); im2.colorspace_settings.is_data = True; im2.file_format = 'PNG'; im2.pack()
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = im2; t.interpolation = 'Closest'
            sp = nt.nodes.new('ShaderNodeSeparateColor')
            nt.links.new(t.outputs['Color'], sp.inputs['Color'])
            nt.links.new(sp.outputs['Green'], b.inputs['Roughness']); nt.links.new(sp.outputs['Blue'], b.inputs['Metallic'])
        if emit_px is not None:
            im3 = _image(s.name + '_e', np.clip(emit_px, 0, 1))
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = im3; t.interpolation = 'Closest'
            nt.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = strength
        elif emit is not None:
            b.inputs['Emission Color'].default_value = srgb(emit); b.inputs['Emission Strength'].default_value = strength
        return m


def blob_mask(h, w, cx, cy, r, seed, rough=0.35, yy=None, xx=None):
    """an irregular blob (a chip, a stain): a disc whose radius wobbles with the angle"""
    if yy is None: yy, xx = np.mgrid[0:h, 0:w]
    rr = np.random.default_rng(seed)
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    a = np.arctan2(dy, dx); d = np.hypot(dx, dy)
    wob = 1.0
    for f in (2, 3, 5): wob = wob + rough * (rr.random() - 0.3) * np.sin(f * a + rr.random() * 6.28)
    return d <= r * wob


# ------------------------------------------------------------ vertex colours: tint x baked AO -> COLOR_0
def bake_ao(objs, dist=0.6, samples=24, lo=0.4, also=(), gain=1.0):
    """ambient occlusion into a corner colour layer 'AO' on each mesh (cycles, cpu). only objs + also are seen."""
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
    for o in objs:
        me = o.data
        if 'AO' in me.color_attributes: me.color_attributes.remove(me.color_attributes['AO'])
        ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER'); me.color_attributes.active_color = ca
        for s in bpy.context.view_layer.objects.selected: s.select_set(False)
        o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.bake(type='AO', target='VERTEX_COLORS')
        n = len(ca.data); buf = np.empty(n * 4, np.float32); ca.data.foreach_get('color', buf)
        buf = buf.reshape(n, 4); v = np.clip(lo + (1 - lo) * np.clip(buf[:, 0] * gain, 0, 1), 0, 1)
        vi = np.empty(n, np.int32); me.loops.foreach_get('vertex_index', vi)   # one value per vertex: corners that share a vertex stay one vertex in the file
        acc = np.zeros(len(me.vertices)); cnt = np.zeros(len(me.vertices)); np.add.at(acc, vi, v); np.add.at(cnt, vi, 1)
        v = (acc / np.maximum(cnt, 1))[vi]
        buf[:, 0] = buf[:, 1] = buf[:, 2] = v; buf[:, 3] = 1
        ca.data.foreach_set('color', buf.ravel())
    for o in hidden: o.hide_render = False
    sc.render.engine = prev
    return objs


def final_colour(o):
    """COLOR_0 = tint x AO, the only colour layer left (the game multiplies it into the texture)"""
    me = o.data; n = len(me.loops)
    def get(k):
        if k not in me.color_attributes: return np.ones((n, 4), np.float32)
        b = np.empty(n * 4, np.float32); me.color_attributes[k].data.foreach_get('color', b); return b.reshape(n, 4)
    c = get('tint') * get('AO'); c[:, 3] = 1
    for a in list(me.color_attributes): me.color_attributes.remove(a)
    ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER'); ca.data.foreach_set('color', c.ravel())
    me.color_attributes.active_color = ca
    try: me.color_attributes.render_color_index = 0
    except Exception: pass
    return o


def colour_preview(mats):
    """the pictures show COLOR_0 the way the game multiplies it in (added only after the export)"""
    for m in mats:
        nt = m.node_tree; b = nt.nodes['Principled BSDF']; sock = b.inputs['Base Color']
        if not sock.links or any(n.name == 'jf_col' for n in nt.nodes): continue
        at = nt.nodes.new('ShaderNodeVertexColor'); at.layer_name = 'Col'
        mix = nt.nodes.new('ShaderNodeMix'); mix.name = 'jf_col'; mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
        nt.links.new(sock.links[0].from_socket, mix.inputs[6]); nt.links.new(at.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], sock)


# ------------------------------------------------------------ QA, counting, export
def tri_count(o):
    me = o.data; me.calc_loop_triangles()
    return len(me.loop_triangles)


def qa(tag, objs, eps=0.0008, tol=0.004, quiet=False):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=eps, tol=tol)
    print('QA_PASS', tag, res.get('pass'), 'tris', sum(m['tris'] for m in res['objects'].values()))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []):
            if not (quiet and k == 'warnings'): print('QA_' + k.upper()[:-1], tag, e)
    for k in ('floating', 'enclosed'):
        for e in res.get(k, [])[:40]: c = e['center']; print('QA_' + k.upper(), tag, e['object'], e['island_verts'], 'verts at game', [round(c[0], 3), round(c[2], 3), round(-c[1], 3)])
    if res.get('zfighting'): zf_where(objs, eps)
    return res


def zf_where(objs, eps=0.0008, limit=30):
    """where it z-fights (the middles of coplanar, same-facing, overlapping triangle pairs, game coordinates)"""
    from mathutils.bvhtree import BVHTree
    Vv, Tr, Nn = [], [], []
    for o in objs:
        me = o.data; me.calc_loop_triangles(); b = len(Vv); mw = o.matrix_world; rm = mw.to_3x3()
        Vv += [mw @ v.co for v in me.vertices]
        for t in me.loop_triangles: Tr.append(tuple(b + i for i in t.vertices)); Nn.append((rm @ t.normal).normalized())
    bvh = BVHTree.FromPolygons(Vv, Tr, epsilon=0.0); seen = set()
    for ti, t in enumerate(Tr):
        a, b, c = (Vv[i] for i in t); cen = (a + b + c) / 3
        for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
            for _, _, tj, _ in bvh.find_nearest_range(p, eps):
                if tj is None or tj == ti or set(t) & set(Tr[tj]) or Nn[ti].dot(Nn[tj]) < 0.999: continue
                a2, b2, c2 = (Vv[i] for i in Tr[tj]); n2 = Nn[tj]; q = p - n2 * n2.dot(p - a2)
                k = (min(ti, tj), max(ti, tj))
                if k not in seen and all((v - u).cross(q - u).dot(n2) >= -1e-9 for u, v in ((a2, b2), (b2, c2), (c2, a2))):
                    seen.add(k)
                    if len(seen) <= limit: print('QA_ZF_AT', [round(x, 3) for x in g_of(cen)], 'normal', [round(x, 2) for x in g_of(Nn[ti])])


def export_glb(root, path):
    """lib.export, plus the vertex colours (blender 4.2+ only writes them when asked) and any folder"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    hid = []
    for c in [root] + list(root.children_recursive):
        if c.hide_viewport or c.hide_get(): hid.append(c); c.hide_set(False); c.hide_viewport = False
        c.select_set(True)
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_extras=True, export_yup=True, export_texcoords=True,
              export_normals=True, export_materials='EXPORT', export_image_format='AUTO', export_lights=False, export_cameras=False)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_vertex_color' in props: kw.update(export_vertex_color='ACTIVE', export_active_vertex_color_when_no_material=True, export_all_vertex_colors=False)
    bpy.ops.export_scene.gltf(**kw)
    print(f'JF_EXPORT {os.path.basename(path)}: {os.path.getsize(path) // 1024} KB')
    return path


def bounds(objs):
    """game-space box of some objects: (lo, hi)"""
    lo = V3((1e9,) * 3); hi = V3((-1e9,) * 3)
    for o in objs:
        mw = o.matrix_world
        for v in o.data.vertices:
            w = g_of(mw @ v.co); lo = V3(map(min, lo, w)); hi = V3(map(max, hi, w))
    return lo, hi


def r3(v, n=3): return [round(float(x), n) for x in v]


# ------------------------------------------------------------ pictures
def clear_studio():
    for o in list(bpy.data.objects):
        if o.type in ('LIGHT', 'CAMERA') or o.name.startswith('jf_set'): bpy.data.objects.remove(o, do_unlink=True)


def eevee(samples=16):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'; ee = sc.eevee; ee.taa_render_samples = samples
    for k, v in (('use_gtao', True), ('use_ssr', True), ('use_bloom', True), ('use_soft_shadows', True), ('use_raytracing', False), ('use_shadows', True)):
        if hasattr(ee, k): setattr(ee, k, v)
    sc.view_settings.view_transform = 'Standard'
    return sc


def area(energy, loc, at, sz, col=(1, 1, 1)):
    L = bpy.data.lights.new('pl', 'AREA'); L.energy = energy; L.color = col; L.size = sz
    ob = _link(bpy.data.objects.new('pl', L)); ob.location = gv(*loc); _look_at(ob, gv(*at))
    return ob


def point(energy, loc, col=(1, 1, 1), r=0.3):
    L = bpy.data.lights.new('pl', 'POINT'); L.energy = energy; L.color = col; L.shadow_soft_size = r
    ob = _link(bpy.data.objects.new('pl', L)); ob.location = gv(*loc)
    return ob


def world(col=0x120a18, strength=1.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('pw'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(col); w.node_tree.nodes['Background'].inputs['Strength'].default_value = strength


def shot(path, cam_pos, target, lens=50, res=(960, 600), ortho=None, exposure=0.0, samples=16, roll=0.0):
    sc = eevee(samples)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.exposure = exposure
    cam = _link(bpy.data.objects.new('pc', bpy.data.cameras.new('pc'))); sc.camera = cam
    cd = cam.data; cd.clip_start = 0.05; cd.clip_end = 400
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.lens = lens
    cam.location = gv(*cam_pos); _look_at(cam, gv(*target))
    if roll: cam.rotation_euler.rotate_axis('Z', roll)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    return path


def contact(paths, dst, label, cols=None, labels=None, quality=3):
    """tile pictures (same size) in a grid under a label strip, like lib.sheet; small yellow captions per tile"""
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p); a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4); imgs.append(a); bpy.data.images.remove(im)
    Hh, Ww = imgs[0].shape[:2]
    cols = cols or len(imgs); rows = (len(imgs) + cols - 1) // cols
    canvas = np.zeros((rows * (Hh + 4) + 4, cols * (Ww + 4) + 4, 4), np.float32); canvas[:, :, 3] = 1; canvas[:, :, :3] = 0.06
    for k, a in enumerate(imgs):
        r, c = divmod(k, cols)
        y0 = canvas.shape[0] - (r + 1) * (Hh + 4); x0 = 4 + c * (Ww + 4)
        if labels and labels[k]:
            cap = np.zeros((7 * 2 + 4, Ww, 3), np.float32); text_px(cap, labels[k].upper(), 4, 2, 2, 0xffe14d)
            a = a.copy(); band = a[Hh - cap.shape[0]:Hh, :, :3]; msk = cap[::-1].sum(axis=2) > 0; band[:] = band * 0.35; band[msk] = cap[::-1][msk]
        canvas[y0:y0 + Hh, x0:x0 + Ww] = a
    lab = np.zeros((7 * 3 + 6, canvas.shape[1], 3), np.float32); text_px(lab, label.upper(), 6, 3, 3, 0xffe14d)
    full = np.concatenate([canvas, np.concatenate([lab[::-1], np.ones(lab.shape[:2] + (1,), np.float32)], axis=2)], axis=0)
    img = bpy.data.images.new('strip', full.shape[1], full.shape[0]); img.pixels.foreach_set(full.ravel())
    png = dst + '.png'; img.filepath_raw = png; img.file_format = 'PNG'; img.save()
    if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v {quality} "{dst}.jpg"') == 0: os.remove(png)
    for p in paths:
        if os.path.exists(p): os.remove(p)
    print('JF_SHEET', dst + '.jpg')
    return dst + '.jpg'


# ------------------------------------------------------------ people, in chunky low-poly
# A figure's own space: the origin between the shoulders, +y up to the head, +z out of the chest. Real sizes (a 1.8 m
# adult), hands and heads a little big so they read from the back of a train.
def superring(y, hx, hz, k=8, n=2.6, zoff=0.0, phase=0.0):
    out = []
    for j in range(k):
        t = phase + 2 * math.pi * j / k; c, s = math.cos(t), math.sin(t)
        out.append(V3((hx * math.copysign(abs(s) ** (2 / n), s), y, zoff + hz * math.copysign(abs(c) ** (2 / n), c))))
    return out


def head_prims(k=6, jaw=0.0, long=1.0):
    """-> (face, skull): the front columns (they take a face decal seen from +z) and the rest. Centred on the head,
    0.25 tall; jaw 0..1 drops the chin (a scream)."""
    j_ = jaw * 0.05
    rows = [(-0.118 - j_, 0.036, 0.034, 0.02, 0.05 - jaw * 0.012), (-0.07 - j_ * 0.7, 0.068, 0.066, 0.05, 0.024), (-0.02, 0.085, 0.108, 0.086, 0.006),
            (0.045, 0.09, 0.09, 0.099, 0.0), (0.108, 0.064, 0.068, 0.074, -0.006)]
    if k >= 8: rows.insert(4, (0.085, 0.082, 0.088, 0.093, -0.004)); rows[-1] = (0.122, 0.047, 0.05, 0.056, -0.008)
    else: rows[0:2] = [(-0.086 - j_, 0.058, 0.062, 0.042, 0.03)]   # (the far ones: chin and jaw are one row)
    R = []
    for y, rx, rzf, rzb, zo in rows:
        ring_ = []
        for j in range(k):
            t = 2 * math.pi * j / k; s, c = math.sin(t), math.cos(t)
            z = zo + (rzf if c > 0 else rzb) * c
            if abs(s) < 1e-6 and c > 0 and abs(y - (-0.02)) > 1e-6: z -= 0.012   # the nose stands out of the middle row
            ring_.append(V3((rx * s, y * long, z)))
        R.append(ring_)
    tip0 = V3((0, (-0.128 - j_) * long, 0.045)); tip1 = V3((0, 0.136 * long, -0.008))
    front = set(); nf = max(1, k // 6)
    for j in range(k):
        if j < nf or j >= k - nf: front.add(j)
    Vf, Ff, UVf, Vs, Fs, UVs = [], [], [], [], [], []
    def add(V_, F_, UV_, pts):
        b = len(V_); V_.extend(pts); F_.append(tuple(range(b, b + len(pts)))); UV_.append([(p.x, p.y) for p in pts])
    for i in range(len(R) - 1):
        for j in range(k):
            jj = (j + 1) % k
            pts = [R[i][j], R[i][jj], R[i + 1][jj], R[i + 1][j]]
            add(*((Vf, Ff, UVf) if j in front else (Vs, Fs, UVs)), pts)
    for j in range(k):
        jj = (j + 1) % k
        add(*((Vf, Ff, UVf) if j in front else (Vs, Fs, UVs)), [R[0][jj], R[0][j], tip0])
        add(Vs, Fs, UVs, [R[-1][j], R[-1][jj], tip1])
    return (Vf, Ff, UVf), (Vs, Fs, UVs)


def torso_prim(k=8, wide=1.0, deep=1.0, length=0.5, neck=True):
    """shoulders at y = 0, open at the hips (it is sunk into something) and at the neck (the head sits there)"""
    rows = [(-length, 0.15, 0.1, 0.0), (-0.12, 0.19, 0.125, 0.01), (-0.005, 0.215, 0.105, 0.0)]
    if length > 0.52: rows.insert(1, (-length * 0.62, 0.145, 0.095, 0.0)); rows[0] = (-length, 0.165, 0.105, 0.0)
    if neck: rows += [(0.04, 0.078, 0.072, 0.0), (0.095, 0.056, 0.058, 0.004)]
    return p_loft([superring(y, hx * wide, hz * deep, k, 2.7, zo) for y, hx, hz, zo in rows])


def chest_patch(wide=1.0, deep=1.0, y0=-0.3, y1=-0.02, half=0.13, off=0.007):
    """a scrap of shirt front lying on the chest (3 x 3 points, its top edge tucked into the collar)"""
    P = []
    for i in range(3):
        y = lerp(y0, y1, i / 2); row = []
        for j in range(3):
            x = lerp(-half, half, j / 2) * wide
            hz = (0.1 + 0.035 * (1 - abs((y + 0.12) / 0.2))) * deep
            z = hz * (1 - abs(x / (0.215 * wide)) ** 2.7) ** (1 / 2.7) + off - (0.03 if i == 2 else 0.0)
            row.append((x, y, z))
        P.append(row)
    return p_grid(P)


def ik2(p0, p2, l1, l2, pole):
    """the elbow of a two-bone arm from p0 reaching p2 (bent toward pole); p2 is pulled in if it is out of reach"""
    p0, p2 = V3(p0), V3(p2); d = p2 - p0; L = d.length
    mx = (l1 + l2) * 0.985
    if L > mx: p2 = p0 + d * (mx / L); d = p2 - p0; L = mx
    L = max(L, abs(l1 - l2) + 1e-4)
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L); h = math.sqrt(max(0.0, l1 * l1 - a * a))
    u = d.normalized(); pv = V3(pole); pv = pv - u * pv.dot(u)
    pv = pv.normalized() if pv.length > 1e-6 else u.orthogonal().normalized()
    return p0 + u * a + pv * h, p2


def limb_prim(p0, p1, p2, r0, r1, r2, k=5, knob=1.12, fine=False, cap=False):
    """a bent limb through three points. fine = two more rings (a real elbow, a swell above it)"""
    p0, p1, p2 = V3(p0), V3(p1), V3(p2)
    if fine:
        pts = [p0, p0.lerp(p1, 0.42), p1.lerp(p0, 0.1), p1.lerp(p2, 0.12), p2.lerp(p1, 0.35), p2]
        rr = [r0, r0 * 1.08, r1 * knob, r1 * 1.02, lerp(r1, r2, 0.45) * 1.08, r2]
    else:
        pts = [p0, p1, p2]; rr = [r0, r1 * knob, r2]
    return p_tube(pts, rr, k, cap1=cap)


def hand_flat(spread=1.0, side=1, k_tris=True):
    """an open hand: wrist at the origin, fingers along +z, the palm faces -y, thumb on +x * side. 0.19 m long"""
    pr = [xf(p_box(0.086, 0.027, 0.098, taper=(1.05, 0.9)), T(0, 0, 0.047))]
    for i, (x, ln, a) in enumerate(((-0.033, 0.066, -0.2), (-0.011, 0.08, -0.06), (0.011, 0.084, 0.06), (0.033, 0.074, 0.2))):
        Mx = T(x * side, 0, 0.094) @ RY(a * spread * side) @ T(0, 0, ln / 2)
        pr.append(xf(p_box(0.02, 0.018, ln, taper=0.72, bottom=False), Mx))
    Mx = T(0.04 * side, -0.004, 0.022) @ RY(0.95 * side * (0.6 + 0.4 * spread)) @ T(0, 0, 0.036)
    pr.append(xf(p_box(0.024, 0.021, 0.074, taper=0.72, bottom=False), Mx))
    return merge(*pr)


def hand_grip(curl=1.0, side=1):
    """a hand closed round something: the palm (-y side) wraps toward -y"""
    pr = [xf(p_box(0.086, 0.027, 0.09, taper=(1.02, 0.9)), T(0, 0, 0.045))]
    Mx = T(0, 0, 0.088) @ RX(0.95 * curl); pr.append(xf(p_box(0.082, 0.021, 0.05, bottom=False), Mx @ T(0, 0, 0.023)))
    Mx = Mx @ T(0, 0, 0.046) @ RX(1.1 * curl); pr.append(xf(p_box(0.078, 0.019, 0.05, taper=0.85, bottom=False), Mx @ T(0, 0, 0.022)))
    Mt = T(0.042 * side, -0.012, 0.03) @ RY(0.5 * side) @ RX(0.9 * curl); pr.append(xf(p_box(0.024, 0.021, 0.07, taper=0.75, bottom=False), Mt @ T(0, 0, 0.034)))
    return merge(*pr)


def hand_mitt(side=1, droop=0.3):
    """a cheap hand (far ones, limp ones): the palm and one wedge of fingers"""
    pr = [xf(p_box(0.086, 0.028, 0.095, bottom=False), T(0, 0, 0.046)),
          xf(p_box(0.082, 0.022, 0.09, taper=(0.8, 0.6), bottom=False), T(0, 0, 0.09) @ RX(droop) @ T(0, 0, 0.042))]
    return merge(*pr)


def hand_claw(side=1, curl=0.55):
    """an open hand with every finger hooked at the knuckle (reaching, clawing)"""
    pr = [xf(p_box(0.086, 0.027, 0.098, taper=(1.05, 0.9)), T(0, 0, 0.047))]
    for i, (x, ln, a) in enumerate(((-0.033, 0.07, -0.3), (-0.011, 0.082, -0.1), (0.011, 0.086, 0.1), (0.033, 0.076, 0.3))):
        Mx = T(x * side, 0, 0.094) @ RY(a * side) @ RX(curl * (1.0 + 0.3 * math.sin(i * 2.1))) @ T(0, 0, ln / 2)
        pr.append(xf(p_box(0.02, 0.018, ln, taper=0.7, bottom=False), Mx))
    Mx = T(0.04 * side, -0.004, 0.022) @ RY(1.0 * side) @ RX(curl * 0.5) @ T(0, 0, 0.036)
    pr.append(xf(p_box(0.024, 0.021, 0.074, taper=0.72, bottom=False), Mx))
    return merge(*pr)


def mound(rx, ry, rz, k=6):
    """half an egg lying on a surface (a back, a shoulder, the back of a head): the flat side is open, on z = 0"""
    R = [[V3((math.cos(2 * math.pi * j / k) * rx * c, math.sin(2 * math.pi * j / k) * ry * c, rz * s_)) for j in range(k)] for c, s_ in ((1.0, -0.15), (0.92, 0.45), (0.55, 0.88))]
    return p_loft(R, tip1=V3((0, 0, rz)))


def shoe_prim(heel=False):
    """a shoe: the ankle at the origin, the toe along +z, the sole on -y"""
    pr = [xf(p_box(0.1, 0.075, 0.27, taper=(0.75, 0.6), shear=(0, -0.012)), T(0, -0.05, 0.075))]
    if heel: pr.append(xf(p_box(0.03, 0.09, 0.03, taper=0.6), T(0, -0.12, -0.045) @ RX(math.pi / 2) @ T(0, 0, 0.0)))
    else: pr.append(xf(p_box(0.1, 0.022, 0.085), T(0, -0.097, -0.02)))
    return merge(*pr)
