# The Gut heart's kit (OVERDUE, the landmark in the Gut): a mesh buffer that takes thousands of small primitives without
# a Blender object for each (the heart is ~1,500 fused hearts), with two things per vertex the game needs for the
# ripple: a PHASE and a pulse WEIGHT (they leave as TEXCOORD_1 = (phase, weight)), a tint that is multiplied with a
# ray-cast ambient occlusion into COLOR_0, tubes / lofts with shared vertices (flesh is all smooth: the game pushes
# verts along the normal, split normals would tear), pixel-rect atlases, the glb export + a compactor, the asset-QA
# gate and the studio pictures. Everything takes GAME coordinates (three.js: x right, y up, z toward the viewer of the
# heart's front), like lib.py. Blender 5.2 (blender52).
import os, sys, struct; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _link, _image, _look_at
from mathutils import noise as mnoise
from mathutils.bvhtree import BVHTree

V3 = Vector
ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(k, d=None):
    for a in ARGV:
        if a.startswith('--' + k + '='): return a.split('=', 1)[1]
        if a == '--' + k: return True
    return d


def g_of(v): return V3((v.x, v.z, -v.y))  # blender -> game
def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def sstep(a, b, x): t = clamp((x - a) / (b - a)) if b != a else float(x >= a); return t * t * (3 - 2 * t)
def r3(v, n=3): return [round(float(x), n) for x in v]


class Rnd:
    """a small seeded generator (its own stream per thing, so adding a part doesn't reshuffle the others)"""
    def __init__(s, seed): s.r = random.Random(seed)
    def u(s, a=0.0, b=1.0): return s.r.uniform(a, b)
    def g(s, m=0.0, sd=1.0): return s.r.gauss(m, sd)
    def pick(s, seq): return seq[s.r.randrange(len(seq))]
    def chance(s, p): return s.r.random() < p
    def i(s, a, b): return s.r.randint(a, b)
    def sign(s): return 1 if s.r.random() < 0.5 else -1


def fbm(p, f=1.0, oct=3):
    v = 0.0; a = 0.5; q = V3(p) * f
    for _ in range(oct):
        v += a * mnoise.noise(q); a *= 0.5; q = q * 2.03 + V3((7.3, 1.7, 4.1))
    return v  # about -0.6 .. 0.6


# ------------------------------------------------------------ paths, tubes, lofts (shared vertices)
def frames(pts, up=None):
    """tangent / normal / binormal along a path (parallel transport: no twisting)"""
    n = len(pts); Tn = []
    for i in range(n):
        t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        Tn.append(t.normalized() if t.length > 1e-9 else V3((0, 1, 0)))
    u = V3(up) if up is not None else V3((0, 1, 0))
    if abs(Tn[0].dot(u)) > 0.95: u = V3((1, 0, 0)) if abs(Tn[0].x) < 0.9 else V3((0, 0, 1))
    N = (u - Tn[0] * Tn[0].dot(u)).normalized(); out = []
    for i in range(n):
        N = N - Tn[i] * Tn[i].dot(N)
        N = N.normalized() if N.length > 1e-9 else Tn[i].orthogonal().normalized()
        out.append((Tn[i], N, Tn[i].cross(N)))
    return out


def smooth_path(pts, n=4):
    """a Catmull-Rom curve through game points, n pieces per span"""
    P = [V3(p) for p in pts]; out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-1])
    return out


class Prim:
    """V = game points, F = index tuples, ST = per face a list of (s, t): s 0..1 round (mirrored, so a swatch needs no
    seam), t = the ring number (or 0..1 for caps); ring[i] / along[i] = each vertex's ring and its 0..1 place along"""
    def __init__(s, V, F, ST, ring=None, along=None): s.V, s.F, s.ST = V, F, ST; s.ring = ring or [0] * len(V); s.along = along or [0.0] * len(V)
    def xf(s, M): return Prim([M @ v for v in s.V], s.F, s.ST, s.ring, s.along)
    def tris(s): return sum(len(f) - 2 for f in s.F)
    def only(s, keep):
        """the faces whose flag in keep is true (hidden ones culled); the vertices stay, Buf.prune drops the unused"""
        return Prim(s.V, [f for f, k in zip(s.F, keep) if k], [t for t, k in zip(s.ST, keep) if k], s.ring, s.along)


def loft(rings, tip0=None, tip1=None, cap0=False, cap1=False):
    """skin through rings (each wound counter-clockwise about the path direction). tip = a point, cap = a flat fan"""
    k = len(rings[0]); n = len(rings); V = []; F = []; ST = []; ring = []; along = []
    L = [0.0]
    for a, b in zip(rings, rings[1:]): L.append(L[-1] + (sum(b, V3()) / k - sum(a, V3()) / k).length)
    tot = L[-1] or 1.0
    for i, r in enumerate(rings): V.extend(r); ring += [i] * k; along += [L[i] / tot] * k
    sm = lambda j: j / k
    for i in range(n - 1):
        for j in range(k):
            jj = (j + 1) % k
            F.append((i * k + j, i * k + jj, (i + 1) * k + jj, (i + 1) * k + j))
            ST.append([(sm(j), i), (sm(j + 1), i), (sm(j + 1), i + 1), (sm(j), i + 1)])
    def fan(ri, pt, flip, tt):
        c = pt if pt is not None else sum(rings[ri], V3()) / k
        V.append(V3(c)); ci = len(V) - 1; ring.append(ri + (-1 if flip else 1)); along.append(0.0 if flip else 1.0)
        for j in range(k):
            jj = (j + 1) % k; a, b = ri * k + j, ri * k + jj
            F.append((b, a, ci) if flip else (a, b, ci))
            ST.append([(sm(j + 1), ri), (sm(j), ri), (sm(j + 0.5), tt)] if flip else [(sm(j), ri), (sm(j + 1), ri), (sm(j + 0.5), tt)])
    if cap0 or tip0 is not None: fan(0, tip0, True, -1)
    if cap1 or tip1 is not None: fan(n - 1, tip1, False, n)
    return Prim(V, F, ST, ring, along)


def ring_of(c, N, B, ra, rb, k, phase=0.0, fn=None):
    out = []
    for j in range(k):
        t = phase + 2 * math.pi * j / k; s = fn(j, t) if fn else 1.0
        out.append(c + N * (math.cos(t) * ra * s) + B * (math.sin(t) * rb * s))
    return out


def tube(pts, radii, k=4, squash=1.0, up=None, tip0=False, tip1=False, cap0=False, cap1=False, phase=0.0, twist=0.0, fn=None, tiplen=0.6):
    """a tube along game points with a radius per point. squash = the binormal radius / the normal one (a number or
    one per point). tip = a rounded point past the end (tiplen x the end radius)"""
    pts = [V3(p) for p in pts]
    rr = list(radii) if isinstance(radii, (list, tuple)) else [radii] * len(pts)
    fr = frames(pts, up)
    sq = list(squash) if isinstance(squash, (list, tuple)) else [squash] * len(pts)
    rings = [ring_of(p, N, B, r, r * sq[i], k, phase + twist * i, (lambda j, t, i=i: fn(i, j, t)) if fn else None) for i, (p, r, (Tt, N, B)) in enumerate(zip(pts, rr, fr))]
    t0 = pts[0] - fr[0][0] * rr[0] * tiplen if tip0 else None
    t1 = pts[-1] + fr[-1][0] * rr[-1] * tiplen if tip1 else None
    return loft(rings, t0, t1, cap0, cap1)


def merge(*prims):
    V = []; F = []; ST = []; ring = []; along = []
    for p in prims:
        b = len(V); V.extend(p.V); F.extend(tuple(b + i for i in f) for f in p.F); ST.extend(p.ST); ring += p.ring; along += p.along
    return Prim(V, F, ST, ring, along)


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


def frame(y_axis, z_hint=(0, 0, 1), pos=(0, 0, 0)):
    """a matrix whose local +y points along y_axis and whose +z leans toward z_hint (game space)"""
    y = V3(y_axis).normalized(); z = V3(z_hint)
    if abs(y.dot(z.normalized())) > 0.995: z = V3((1, 0, 0)) if abs(y.x) < 0.9 else V3((0, 0, 1))
    x = y.cross(z).normalized(); z = x.cross(y)
    m = Matrix.Identity(4)
    for i in range(3): m[i][0], m[i][1], m[i][2], m[i][3] = x[i], y[i], z[i], pos[i]
    return m


# ------------------------------------------------------------ atlases (pixel rects)
def px_uv(rect, tex, s, t, m=0.5):
    """(s, t) in 0..1 inside a pixel rect (x, y from the top, w, h) of a tex (w, h) -> blender uv, m px inside"""
    x, y, w, h = rect[:4]
    return ((x + m + s * (w - 2 * m)) / tex[0], 1 - (y + m + (1 - t) * (h - 2 * m)) / tex[1])


class Atlas:
    def __init__(s, name, w, h): s.name = name; s.w, s.h = w, h; s.px = np.zeros((h, w, 3), np.float32); s.R = {}; s.tex = (w, h)
    def cell(s, key, x, y, w, h, col=None, var=0.0, seed=1):
        s.R[key] = (x, y, w, h)
        if col is not None:
            r = np.random.default_rng(seed); n = r.random((h, w, 1)) if var else 0.5
            s.px[y:y + h, x:x + w] = hexrgb(col)[None, None] * (1 - var + 2 * var * n)
        return s.px[y:y + h, x:x + w]
    def sub(s, key): x, y, w, h = s.R[key]; return s.px[y:y + h, x:x + w]
    def image(s): return _image(s.name + '_t', np.clip(s.px, 0, 1))


# ------------------------------------------------------------ the buffer
class Buf:
    """collects primitives for one mesh. per vertex: phase, weight (the ripple) and a tint; per face corner: uv."""
    def __init__(s, name): s.name = name; s.V = []; s.PH = []; s.W = []; s.TI = []; s.F = []; s.UV = []; s.MI = []; s.mats = []; s.AO = None

    def mi(s, m):
        if m not in s.mats: s.mats.append(m)
        return s.mats.index(m)

    def add(s, prim, m, style, ph=0.0, w=0.0, tint=1.0, M=None, flip=False, orient=True):
        """style = ('alt', rect, tex[, m]) (tubes: across the swatch round, mirrored back and forth along) |
        ('fit', rect, tex[, m]) (the whole length on the swatch) | ('quad', rect, tex[, m]) (every face the whole swatch)
        | ('fn', f) (f(game vertex, index) -> uv) | ('uv', list) (ready per-face uvs). ph / w / tint = one value, a list
        per vertex, or f(game vertex, index)"""
        V = [M @ v for v in prim.V] if M is not None else list(prim.V)
        b = len(s.V); n = len(V); mi = s.mi(m)
        if orient and prim.F:   # every solid looks out: a part wound inside out (or mirrored by M) is turned here
            c = sum(V, V3()) / n; vol = 0.0
            for f in prim.F:
                a0 = V[f[0]] - c
                for q in range(1, len(f) - 1): vol += a0.dot((V[f[q]] - c).cross(V[f[q + 1]] - c))
            flip = vol < 0
        def per(x):
            if callable(x): return [x(v, i) for i, v in enumerate(V)]
            if isinstance(x, (list, np.ndarray)): assert len(x) == n, (len(x), n); return [float(q) for q in x]
            return [float(x)] * n
        PH = per(ph); W = per(w)
        if callable(tint): TI = [tint(v, i) for i, v in enumerate(V)]   # a tuple = one rgb for all, a list = one per vertex
        elif isinstance(tint, (int, float)): TI = [(tint, tint, tint)] * n
        elif isinstance(tint, tuple): TI = [tint] * n
        else: assert len(tint) == n; TI = list(tint)
        TI = [(t, t, t) if isinstance(t, (int, float)) else tuple(t) for t in TI]
        s.V.extend(V); s.PH.extend(PH); s.W.extend(W); s.TI.extend(TI)
        kind = style[0]
        if kind in ('alt', 'fit', 'quad'):
            rect, tex = style[1], style[2]; mg = style[3] if len(style) > 3 else 0.5
            nr = max(max(t for _, t in f) for f in prim.ST) if kind == 'fit' else 1
            n0 = min(min(t for _, t in f) for f in prim.ST) if kind == 'fit' else 0
            Q4 = ((0, 0), (1, 0), (1, 1), (0, 1)); Q3 = ((0, 0), (1, 0), (0.5, 1))
            def uvf(fi, ci):
                if kind == 'quad':
                    q = (Q4 if len(prim.F[fi]) == 4 else Q3)[ci % len(prim.F[fi]) if len(prim.F[fi]) in (3, 4) else 0]
                    return px_uv(rect, tex, q[0], q[1], mg)
                a, t = prim.ST[fi][ci]
                if kind == 'alt': a = 1 - abs(2 * a - 1); t = float(t % 2)   # round: there and back (no seam); along: mirrored ring to ring
                else: t = (t - n0) / ((nr - n0) or 1)
                return px_uv(rect, tex, a, t, mg)
        elif kind == 'uv':
            lst = style[1]
            def uvf(fi, ci): return lst[fi][ci]
        else:
            fn = style[1]
            def uvf(fi, ci): return fn(V[prim.F[fi][ci]], prim.F[fi][ci])
        for fi, f in enumerate(prim.F):
            idx = list(range(len(f)))
            if flip: idx = idx[::-1]
            s.F.append(tuple(b + f[c] for c in idx)); s.UV.append([uvf(fi, c) for c in idx]); s.MI.append(mi)
        return b

    def verts(s, V, ph=0.0, w=0.0, tint=1.0):
        """bare vertices (a welded shell built by hand) -> the index of the first; faces() then takes absolute indices"""
        b = len(s.V); n = len(V)
        per = lambda x: [float(q) for q in x] if isinstance(x, (list, np.ndarray)) else [float(x)] * n
        s.V.extend(V3(v) for v in V); s.PH.extend(per(ph)); s.W.extend(per(w))
        s.TI.extend([(tint, tint, tint)] * n if isinstance(tint, (int, float)) else [tint] * n if isinstance(tint, tuple) else [(t, t, t) if isinstance(t, (int, float)) else tuple(t) for t in tint])
        return b

    def faces(s, F, UV, m):
        mi = s.mi(m)
        for f, uv in zip(F, UV): s.F.append(tuple(f)); s.UV.append(list(uv)); s.MI.append(mi)

    def prune(s):
        """drop vertices no face uses (culled faces leave them behind)"""
        used = sorted({i for f in s.F for i in f})
        if len(used) == len(s.V): return s
        mp = {o: k for k, o in enumerate(used)}
        s.V = [s.V[i] for i in used]; s.PH = [s.PH[i] for i in used]; s.W = [s.W[i] for i in used]; s.TI = [s.TI[i] for i in used]
        s.F = [tuple(mp[i] for i in f) for f in s.F]
        if s.AO is not None: s.AO = s.AO[used]
        return s

    def tris(s): return sum(len(f) - 2 for f in s.F)

    def tri_arrays(s):
        P = np.array([tuple(v) for v in s.V], np.float64).reshape(-1, 3); T_ = []
        for f in s.F:
            for k in range(1, len(f) - 1): T_.append((f[0], f[k], f[k + 1]))
        return P, np.array(T_, np.int64).reshape(-1, 3)

    def normals(s):
        P, Tr = s.tri_arrays(); N = np.zeros_like(P)
        if len(Tr):
            fn = np.cross(P[Tr[:, 1]] - P[Tr[:, 0]], P[Tr[:, 2]] - P[Tr[:, 0]])
            for k in range(3): np.add.at(N, Tr[:, k], fn)
        ln = np.linalg.norm(N, axis=1, keepdims=True); ln[ln < 1e-12] = 1
        return P, N / ln

    def obj(s, sharp=None):
        s.prune()
        me = bpy.data.meshes.new(s.name)
        me.from_pydata([tuple(gv(*v)) for v in s.V], [], s.F)
        uv = me.uv_layers.new(name='UVMap'); uv.data.foreach_set('uv', [c for f in s.UV for p in f for c in p])
        # the ripple: u = phase, v = weight. the glTF exporter writes v as 1 - v, so it is stored flipped here
        pu = me.uv_layers.new(name='pulse'); pu.data.foreach_set('uv', [c for f in s.F for i in f for c in (s.PH[i], 1.0 - s.W[i])])
        me.uv_layers.active = uv; uv.active_render = True
        me.polygons.foreach_set('material_index', s.MI)
        for m in s.mats: me.materials.append(m)
        ao = s.AO if s.AO is not None else np.ones(len(s.V))
        ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
        ca.data.foreach_set('color', [c for f in s.F for i in f for c in (min(1.0, s.TI[i][0] * ao[i]), min(1.0, s.TI[i][1] * ao[i]), min(1.0, s.TI[i][2] * ao[i]), 1.0)])
        me.color_attributes.active_color = ca
        try: me.color_attributes.render_color_index = 0
        except Exception: pass
        me.polygons.foreach_set('use_smooth', [True] * len(s.F))
        me.update()
        o = _link(bpy.data.objects.new(s.name, me))
        if sharp is not None: me.set_sharp_from_angle(angle=math.radians(sharp))
        return o


def bake_ao(bufs, dist=3.0, k=14, lo=0.28, gain=1.0, extra=None, seed=3):
    """ambient occlusion per vertex by ray casting against everything in bufs (+ extra (P, T) arrays): cheap, the same
    every run, no cycles. far hits count less. sets b.AO (multiplied into COLOR_0 by obj())."""
    Pa = []; Ta = []; b0 = 0
    for b in bufs:
        P, Tr = b.tri_arrays(); Pa.append(P); Ta.append(Tr + b0); b0 += len(P)
    for P, Tr in (extra or []): Pa.append(P); Ta.append(Tr + b0); b0 += len(P)
    P = np.concatenate(Pa); Tr = np.concatenate(Ta)
    bvh = BVHTree.FromPolygons([V3(p) for p in P], [tuple(int(i) for i in t) for t in Tr], all_triangles=True, epsilon=0.0)
    rn = np.random.default_rng(seed); dirs = []
    for i in range(k):   # cosine-weighted directions about +z (a spiral: even cover)
        u = (i + 0.5) / k; r = math.sqrt(u); a = i * 2.39996 + 0.3
        dirs.append((r * math.cos(a), r * math.sin(a), math.sqrt(1 - u)))
    for b in bufs:
        Pv, Nv = b.normals(); ao = np.ones(len(Pv))
        for i in range(len(Pv)):
            n = V3(Nv[i])
            if n.length < 0.5: continue
            t1 = n.orthogonal().normalized(); t2 = n.cross(t1); o = V3(Pv[i]) + n * 0.02; occ = 0.0
            rot = rn.random() * 6.283; cr, sr = math.cos(rot), math.sin(rot)
            for dx, dy, dz in dirs:
                d = t1 * (dx * cr - dy * sr) + t2 * (dx * sr + dy * cr) + n * dz
                hit = bvh.ray_cast(o, d, dist)
                if hit[0] is not None: occ += 1.0 - 0.6 * (hit[3] / dist)
            ao[i] = occ / k
        b.AO = np.clip(lo + (1 - lo) * (1 - np.clip(ao * gain, 0, 1)), 0, 1)
    return bufs


# ------------------------------------------------------------ export, compacting, counting, QA
def tri_count(o):
    me = o.data; me.calc_loop_triangles()
    return len(me.loop_triangles)


def export_glb(root, path):
    """lib.export, plus the vertex colours (blender 4.2+ only writes them when asked), both uv sets and any folder"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    for c in [root] + list(root.children_recursive):
        c.hide_set(False); c.hide_viewport = False; c.select_set(True)
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_extras=True, export_yup=True, export_texcoords=True,
              export_normals=True, export_materials='EXPORT', export_image_format='AUTO', export_lights=False, export_cameras=False)
    props = bpy.ops.export_scene.gltf.get_rna_type().properties
    if 'export_vertex_color' in props: kw.update(export_vertex_color='ACTIVE', export_active_vertex_color_when_no_material=True, export_all_vertex_colors=False)
    bpy.ops.export_scene.gltf(**kw)
    print(f'JF_EXPORT {os.path.basename(path)}: {os.path.getsize(path) // 1024} KB')
    return path


def compact_glb(path):
    """shrink an exported .glb without touching what the game reads: normals as signed bytes, vertex colours as bytes,
    TEXCOORD_0 as 16 bit where it stays inside 0..1 (KHR_mesh_quantization, which three.js reads natively). Positions and
    TEXCOORD_1 (the ripple's phase and weight) stay floats."""
    raw = open(path, 'rb').read()
    jl = struct.unpack('<I', raw[12:16])[0]; js = json.loads(raw[20:20 + jl]); bo = 20 + jl
    bl = struct.unpack('<I', raw[bo:bo + 4])[0]; blob = raw[bo + 8:bo + 8 + bl]
    CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}; NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
    def read(ai):
        a = js['accessors'][ai]; bv = js['bufferViews'][a['bufferView']]; n = NC[a['type']]; dt = np.dtype(CT[a['componentType']])
        off = bv.get('byteOffset', 0) + a.get('byteOffset', 0); st = bv.get('byteStride', 0)
        if st and st != dt.itemsize * n:
            arr = np.frombuffer(blob, np.uint8, a['count'] * st, off).reshape(a['count'], st)[:, :dt.itemsize * n].copy().view(dt).reshape(a['count'], n)
        else: arr = np.frombuffer(blob, dt, a['count'] * n, off).reshape(a['count'], n)
        if a.get('normalized'): arr = arr.astype(np.float32) / np.iinfo(dt).max
        return arr.astype(np.float32)
    new = {}   # accessor -> (bytes, componentType, stride)
    for m in js['meshes']:
        for p in m['primitives']:
            at = p['attributes']
            for key in ('NORMAL', 'COLOR_0', 'TEXCOORD_0'):
                ai = at.get(key)
                if ai is None or ai in new: continue
                d = read(ai)
                if key == 'NORMAL':
                    q = np.zeros((len(d), 4), np.int8); q[:, :3] = np.clip(np.round(d * 127), -127, 127); new[ai] = (q.tobytes(), 5120, 4)
                elif key == 'COLOR_0':
                    if d.shape[1] == 3: d = np.concatenate([d, np.ones((len(d), 1), np.float32)], axis=1); js['accessors'][ai]['type'] = 'VEC4'
                    new[ai] = (np.clip(np.round(d * 255), 0, 255).astype(np.uint8).tobytes(), 5121, 0)
                elif d.min() >= 0.0 and d.max() <= 1.0:
                    new[ai] = (np.clip(np.round(d * 65535), 0, 65535).astype(np.uint16).tobytes(), 5123, 0)
    out = bytearray(); views = []; used = {}
    for ai, a in enumerate(js['accessors']):
        if ai in new: continue
        used.setdefault(a['bufferView'], None)
    for img in js.get('images', []): used.setdefault(img['bufferView'], None)
    remap = {}
    for bi_, bv in enumerate(js['bufferViews']):
        if bi_ not in used: continue
        while len(out) % 4: out.append(0)
        nb = dict(bv); o0 = bv.get('byteOffset', 0); nb['byteOffset'] = len(out); out += blob[o0:o0 + bv['byteLength']]
        remap[bi_] = len(views); views.append(nb)
    for ai, (data, ct, st) in new.items():
        while len(out) % 4: out.append(0)
        nb = dict(buffer=0, byteOffset=len(out), byteLength=len(data), target=34962)
        if st: nb['byteStride'] = st
        out += data
        a = js['accessors'][ai]; a['bufferView'] = len(views); a['componentType'] = ct; a['normalized'] = True; a.pop('byteOffset', None); a.pop('min', None); a.pop('max', None)
        views.append(nb)
    for ai, a in enumerate(js['accessors']):
        if ai not in new: a['bufferView'] = remap[a['bufferView']]
    for img in js.get('images', []): img['bufferView'] = remap[img['bufferView']]
    js['bufferViews'] = views
    while len(out) % 4: out.append(0)
    js['buffers'] = [dict(byteLength=len(out))]
    for k in ('extensionsUsed', 'extensionsRequired'):
        if 'KHR_mesh_quantization' not in js.setdefault(k, []): js[k].append('KHR_mesh_quantization')
    jb = json.dumps(js, separators=(',', ':')).encode()
    while len(jb) % 4: jb += b' '
    total = 12 + 8 + len(jb) + 8 + len(out)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total)); f.write(struct.pack('<II', len(jb), 0x4E4F534A)); f.write(jb)
        f.write(struct.pack('<II', len(out), 0x004E4942)); f.write(bytes(out))
    print(f'JF_COMPACT {os.path.basename(path)}: {len(raw) // 1024} KB -> {total // 1024} KB')


def qa(tag, objs, eps=0.0008, tol=0.01, quiet=False):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=eps, tol=tol)
    print('QA_PASS', tag, res.get('pass'), 'tris', sum(m['tris'] for m in res['objects'].values()))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []):
            if not (quiet and k == 'warnings'): print('QA_' + k.upper()[:-1], tag, e)
    for k in ('floating', 'enclosed'):
        for e in res.get(k, [])[:40]: c = e['center']; print('QA_' + k.upper(), tag, e['object'], e['island_verts'], 'verts at game', [round(c[0], 3), round(c[2], 3), round(-c[1], 3)])
    return res


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


def sun(strength, direction, col=(1, 1, 1), angle=0.05):
    L = bpy.data.lights.new('ps', 'SUN'); L.energy = strength; L.color = col; L.angle = angle
    ob = _link(bpy.data.objects.new('ps', L)); ob.location = gv(*direction) * 100; _look_at(ob, V3((0, 0, 0)))
    return ob


def world(col=0x120a18, strength=1.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.new('pw'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(col); w.node_tree.nodes['Background'].inputs['Strength'].default_value = strength


def shot(path, cam_pos, target, lens=50, res=(960, 600), ortho=None, exposure=0.0, samples=16, far=900):
    sc = eevee(samples)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.exposure = exposure
    cam = _link(bpy.data.objects.new('pc', bpy.data.cameras.new('pc'))); sc.camera = cam
    cd = cam.data; cd.clip_start = 0.1; cd.clip_end = far
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.lens = lens
    cam.location = gv(*cam_pos); _look_at(cam, gv(*target))
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    return path


def colour_preview(mats, on=True):
    """the pictures show COLOR_0 the way the game multiplies it in. on = False takes the nodes out again (the export
    wants the plain material)"""
    for m in mats:
        nt = m.node_tree; b = nt.nodes['Principled BSDF']; sock = b.inputs['Base Color']
        has = [n for n in nt.nodes if n.name in ('jf_col', 'jf_colat')]
        if not on:
            if has:
                mix = nt.nodes['jf_col']; src = mix.inputs[6].links[0].from_socket
                nt.links.new(src, sock)
                for n in has: nt.nodes.remove(n)
            continue
        if not sock.links or has: continue
        at = nt.nodes.new('ShaderNodeVertexColor'); at.layer_name = 'Col'; at.name = 'jf_colat'
        mix = nt.nodes.new('ShaderNodeMix'); mix.name = 'jf_col'; mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
        nt.links.new(sock.links[0].from_socket, mix.inputs[6]); nt.links.new(at.outputs['Color'], mix.inputs[7]); nt.links.new(mix.outputs[2], sock)


def contact(paths, dst, label, cols=None, labels=None, quality=3, keep=False):
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
            a = a.copy(); band = a[:cap.shape[0], :, :3]; msk = cap[::-1].sum(axis=2) > 0; band[:] = band * 0.35; band[msk] = cap[::-1][msk]
        canvas[y0:y0 + Hh, x0:x0 + Ww] = a
    lab = np.zeros((7 * 3 + 6, canvas.shape[1], 3), np.float32); text_px(lab, label.upper(), 6, 3, 3, 0xffe14d)
    full = np.concatenate([canvas, np.concatenate([lab[::-1], np.ones(lab.shape[:2] + (1,), np.float32)], axis=2)], axis=0)
    img = bpy.data.images.new('strip', full.shape[1], full.shape[0]); img.pixels.foreach_set(full.ravel())
    png = dst + '.png'; img.filepath_raw = png; img.file_format = 'PNG'; img.save()
    if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v {quality} "{dst}.jpg"') == 0: os.remove(png)
    if not keep:
        for p in paths:
            if os.path.exists(p): os.remove(p)
    print('JF_SHEET', dst + '.jpg')
    return dst + '.jpg'
