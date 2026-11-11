# the train set's kit (OVERDUE, m06: Dale's works train, the Under-Hill Loop's tunnel, the dead 17:32's sister train).
# on top of rpkit.py (the boss's kit): an atlas that packs its own cells and paints wear into them, a buffer with a
# colour per vertex and weighted normals (a chamfered box costs no more vertices than a plain one), railway pieces
# (wheelsets, leaf springs, buffers, chains, rails, planks). everything in GAME metres: x right, y up, z = along the
# train from its back (0) to the loco. Blender 5.2 (blender52).
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rpkit import *
from lib import _link, _image
import rpkit, lib
from mathutils.geometry import tessellate_polygon


def c3(t): return (t, t, t) if isinstance(t, (int, float)) else tuple(t)[:3]


def lin(h):
    """0xRRGGBB -> a linear tint (vertex colours multiply the texture in linear space)"""
    return tuple(srgb(h)[:3])


# ------------------------------------------------------------ the atlas: cells place themselves, and take wear
class Pack(Atlas):
    def __init__(s, name, w, h, rough=0.6, metal=0.0):
        super().__init__(name, w, h, rough, metal); s.cx = 0; s.cy = 0; s.rowh = 0

    def put(s, key, w, h, col=None, **kw):
        if s.cx + w > s.w: s.cx = 0; s.cy += s.rowh; s.rowh = 0
        assert s.cy + h <= s.h, f'atlas {s.name} is full at {key}'
        a = s.cell(key, s.cx, s.cy, w, h, col, **kw); s.cx += w; s.rowh = max(s.rowh, h)
        return a

    def material(s, mname, rough=0.6, metal=0.0, use_orm=False, metal_map=True):
        """as Atlas.material, but the roughness / metal map keeps its pixels: blender 5.2 wipes a generated image when
        its colour space is changed after they are set (rpkit's does that, and its maps come out black: roughness 0)"""
        img = _image(s.name + '_t', np.clip(s.px, 0, 1)); m = mat(mname, 0xffffff, rough=rough, metal=metal, tex=img)
        if use_orm:
            nt = m.node_tree; b = nt.nodes['Principled BSDF']
            im2 = bpy.data.images.new(s.name + '_mr', s.w, s.h, alpha=False); im2.colorspace_settings.is_data = True
            a = np.ones((s.h, s.w, 4), np.float32); a[:, :, :3] = np.clip(s.orm[::-1], 0, 1)
            im2.pixels.foreach_set(a.ravel()); im2.file_format = 'PNG'; im2.pack()
            chk = np.empty(s.h * s.w * 4, np.float32); im2.pixels.foreach_get(chk); assert chk.reshape(-1, 4)[:, 1].max() > 0.05, 'the roughness map came out black'
            t = nt.nodes.new('ShaderNodeTexImage'); t.image = im2; t.interpolation = 'Closest'
            sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(t.outputs['Color'], sp.inputs['Color']); nt.links.new(sp.outputs['Green'], b.inputs['Roughness'])
            if metal_map: nt.links.new(sp.outputs['Blue'], b.inputs['Metallic'])
        return m

    def rm(s, key, rough=None, metal=None, mask=None):
        """roughness / metal of a cell, or of the pixels of it a mask picks"""
        o = s.sub_orm(key)
        if mask is None: mask = np.ones(o.shape[:2], bool)
        if rough is not None: o[:, :, 1][mask] = rough
        if metal is not None: o[:, :, 2][mask] = metal


def rng(seed): return np.random.default_rng(seed)


def streaks(px, seed, n, col, length=(6, 20), alpha=0.5, width=1):
    """runs of rust / damp down a panel from random spots (each fades as it falls)"""
    r = rng(seed); h, w = px.shape[:2]; c = hexrgb(col)
    for _ in range(n):
        x = int(r.integers(0, w)); y = int(r.integers(0, max(1, h - 2))); L = int(r.integers(length[0], length[1]))
        for k in range(L):
            yy = y + k
            if yy >= h: break
            a = alpha * (1 - k / L)
            for dx in range(width):
                xx = min(w - 1, x + dx); px[yy, xx] = px[yy, xx] * (1 - a) + c * a
    return px


def chips(px, seed, n, col, r=(1.0, 3.0), orm=None, rough=None, metal=None, edge=None):
    """paint knocked off: irregular blobs of what is under it (edge = a darker ring round each, like rust creeping)"""
    rr = rng(seed); h, w = px.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
    for k in range(n):
        cx, cy = rr.random() * w, rr.random() * h; rad = r[0] + (r[1] - r[0]) * rr.random() ** 2
        if edge is not None:
            m2 = blob_mask(h, w, cx, cy, rad + 1.0, seed * 131 + k, 0.5, yy, xx); px[m2] = px[m2] * 0.5 + hexrgb(edge) * 0.5
        m = blob_mask(h, w, cx, cy, rad, seed * 131 + k, 0.5, yy, xx); px[m] = hexrgb(col) * (0.85 + 0.3 * rr.random())
        if orm is not None:
            if rough is not None: orm[:, :, 1][m] = rough
            if metal is not None: orm[:, :, 2][m] = metal
    return px


def grime(px, seed, amount=0.25, col=0x1a1410, bottom=True):
    """dirt that gathers low down (or everywhere), blotchy"""
    r = rng(seed); h, w = px.shape[:2]; c = hexrgb(col)
    n = r.random((max(2, h // 4), max(2, w // 4))); n = np.kron(n, np.ones((4, 4)))[:h, :w]
    if n.shape != (h, w): n = np.pad(n, ((0, h - n.shape[0]), (0, w - n.shape[1])), mode='edge')
    g = (np.linspace(0, 1, h)[:, None] ** 2 if bottom else np.ones((h, 1))) * amount * (0.5 + n)
    px[:] = px * (1 - g[:, :, None]) + c[None, None] * g[:, :, None]
    return px


def frame_px(px, col, t=1):
    c = hexrgb(col); px[:t] = c; px[-t:] = c; px[:, :t] = c; px[:, -t:] = c
    return px


def hand_num(px, s, x0, y0, hgt, col, w=2.0, seed=1):
    """a number painted by hand with a flat brush: strokes, not a font (a little crooked, with a run or two)"""
    r = rng(seed); wd = hgt * 0.55
    S = {'0': [(0, 0, 1, 0), (1, 0, 1, 1), (1, 1, 0, 1), (0, 1, 0, 0)], '1': [(0.5, 0, 0.5, 1), (0.2, 0.25, 0.5, 0)], '2': [(0, 0.1, 0.9, 0), (0.9, 0, 1, 0.45), (1, 0.45, 0, 1), (0, 1, 1, 1)],
         '3': [(0, 0, 1, 0), (1, 0, 0.4, 0.45), (0.4, 0.45, 1, 0.6), (1, 0.6, 0.9, 1), (0.9, 1, 0, 1)], '4': [(0.75, 0, 0, 0.65), (0, 0.65, 1, 0.65), (0.75, 0, 0.75, 1)],
         '5': [(1, 0, 0, 0), (0, 0, 0, 0.45), (0, 0.45, 1, 0.5), (1, 0.5, 1, 1), (1, 1, 0, 1)], '6': [(1, 0, 0, 0.5), (0, 0.5, 0, 1), (0, 1, 1, 1), (1, 1, 1, 0.5), (1, 0.5, 0, 0.5)],
         '7': [(0, 0, 1, 0), (1, 0, 0.35, 1)], '8': [(0, 0, 1, 0), (1, 0, 0, 1), (0, 1, 1, 1), (1, 1, 0, 0)], '9': [(1, 0.5, 0, 0.5), (0, 0.5, 0, 0), (0, 0, 1, 0), (1, 0, 1, 1)]}
    x = x0
    for ch in s:
        for (a, b, c_, d) in S.get(ch, []):
            j = lambda: (r.random() - 0.5) * 0.08
            px_line(px, x + (a + j()) * wd, y0 + (b + j()) * hgt, x + (c_ + j()) * wd, y0 + (d + j()) * hgt, col, w)
        if ch in S and r.random() < 0.6:   # a run
            rx = int(x + r.random() * wd); ry = int(y0 + hgt)
            for k in range(int(2 + r.random() * 4)):
                if 0 <= ry + k < px.shape[0] and 0 <= rx < px.shape[1]: px[ry + k, rx] = hexrgb(col)
        x += wd * 1.45
    return px


# ------------------------------------------------------------ primitives (V, F, UV) in game metres
def p_cbox(sx, sy, sz, c=0.02, bottom=True):
    """a box with every edge chamfered by c (with weighted normals it shades as a rounded edge and exports with the
    same 24 vertices as a plain box)"""
    hx, hy, hz = sx / 2, sy / 2, sz / 2; c = min(c, hx * 0.45, hy * 0.45, hz * 0.45)
    V = []; idx = {}
    for sxn in (-1, 1):
        for syn in (-1, 1):
            for szn in (-1, 1):
                idx[(sxn, syn, szn, 0)] = len(V); V.append(V3((sxn * hx, syn * (hy - c), szn * (hz - c))))
                idx[(sxn, syn, szn, 1)] = len(V); V.append(V3((sxn * (hx - c), syn * hy, szn * (hz - c))))
                idx[(sxn, syn, szn, 2)] = len(V); V.append(V3((sxn * (hx - c), syn * (hy - c), szn * hz)))
    F = []; UV = []; dims = (sx, sy, sz)
    def quad(a, b, c_, d, w, h): F.append((a, b, c_, d)); UV.append([(0, 0), (w, 0), (w, h), (0, h)])
    for ax in range(3):       # the six big faces
        o1, o2 = [(1, 2), (0, 2), (0, 1)][ax]
        for sg in (-1, 1):
            if ax == 1 and sg < 0 and not bottom: continue
            def key(s1, s2):
                k = [0, 0, 0]; k[ax] = sg; k[o1] = s1; k[o2] = s2; return idx[(k[0], k[1], k[2], ax)]
            quad(key(-1, -1), key(1, -1), key(1, 1), key(-1, 1), dims[o1], dims[o2])
    for ax in range(3):       # twelve edges: the chamfer between two faces, running along ax
        o1, o2 = [(1, 2), (0, 2), (0, 1)][ax]
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                def key(sa, face):
                    k = [0, 0, 0]; k[ax] = sa; k[o1] = s1; k[o2] = s2; return idx[(k[0], k[1], k[2], face)]
                quad(key(-1, o1), key(1, o1), key(1, o2), key(-1, o2), dims[ax], c * 1.4)
    for sxn in (-1, 1):       # eight corners
        for syn in (-1, 1):
            for szn in (-1, 1):
                F.append((idx[(sxn, syn, szn, 0)], idx[(sxn, syn, szn, 1)], idx[(sxn, syn, szn, 2)])); UV.append([(0, 0), (c, 0), (c / 2, c)])
    return orient_from((V, F, UV), (0, 0, 0))


def p_extrude(poly, z0, z1, cap0=True, cap1=True):
    """a 2D outline (x, y) pushed along z from z0 to z1. any simple polygon; the caps are triangulated"""
    P = [(float(x), float(y)) for x, y in poly]
    ar = sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))
    if ar < 0: P = P[::-1]
    n = len(P); V = [V3((x, y, z0)) for x, y in P] + [V3((x, y, z1)) for x, y in P]; F = []; UV = []
    per = [0.0]
    for i in range(n): per.append(per[-1] + math.hypot(P[(i + 1) % n][0] - P[i][0], P[(i + 1) % n][1] - P[i][1]))
    for i in range(n):
        j = (i + 1) % n; F.append((i, j, n + j, n + i)); UV.append([(per[i], 0), (per[i + 1], 0), (per[i + 1], z1 - z0), (per[i], z1 - z0)])
    tris = tessellate_polygon([[V3((x, y, 0)) for x, y in P]])
    for a, b, c in tris:
        # tessellate_polygon keeps no promise about winding: check each against +z
        ccw = (P[b][0] - P[a][0]) * (P[c][1] - P[a][1]) - (P[b][1] - P[a][1]) * (P[c][0] - P[a][0]) > 0
        t1 = (a, b, c) if ccw else (a, c, b)
        if cap1: F.append(tuple(n + i for i in t1)); UV.append([P[i] for i in t1])
        if cap0: F.append(tuple(t1[::-1])); UV.append([P[i] for i in t1[::-1]])
    return V, F, UV


def p_lathe_x(profile, k=12, cap0=True, cap1=True, phase=0.0):
    """rings round the x axis: profile = [(x, radius), ...] in order of rising x"""
    R = [[V3((x, r * math.cos(phase + 2 * math.pi * j / k), r * math.sin(phase + 2 * math.pi * j / k))) for j in range(k)] for x, r in profile]
    return p_loft(R, cap0=cap0, cap1=cap1)


def p_cyl(r, h, k=10, r1=None, cap0=True, cap1=True):
    """a cylinder / cone along +y from y = 0 to h"""
    r1 = r if r1 is None else r1
    a = [V3((math.sin(2 * math.pi * j / k) * r, 0, math.cos(2 * math.pi * j / k) * r)) for j in range(k)]
    b = [V3((math.sin(2 * math.pi * j / k) * r1, h, math.cos(2 * math.pi * j / k) * r1)) for j in range(k)]
    return p_loft([a, b], cap0=cap0, cap1=cap1)


def p_ring_loop(pts, r, k=4, phase=math.pi / 4):
    """a closed tube through points (a chain link, a lashing ring)"""
    pts = [V3(p) for p in pts]; n = len(pts); rings = []
    c = sum(pts, V3()) / n
    nrm = V3()
    for i in range(n): nrm += (pts[i] - c).cross(pts[(i + 1) % n] - c)
    nrm = nrm.normalized() if nrm.length > 1e-9 else V3((0, 1, 0))
    for i in range(n):
        t = (pts[(i + 1) % n] - pts[i - 1]).normalized(); out = t.cross(nrm).normalized()
        rings.append(ring(pts[i], out, nrm, r, r, k, phase))
    return p_loft(rings + [rings[0]])


def p_link(L, W, r, k=4):
    """one chain link lying in the x-z plane, long along z"""
    hw = W / 2 - r; hl = L / 2 - r
    return p_ring_loop([(-hw, 0, -hl * 0.6), (-hw, 0, hl * 0.6), (0, 0, hl), (hw, 0, hl * 0.6), (hw, 0, -hl * 0.6), (0, 0, -hl)], r, k)


def chain_prims(pts, pitch=0.11, W=0.07, r=0.012, sag=0.0, cheap=True):
    """links along a polyline, every other one turned a quarter. cheap = flat plates (they read as chain from 2 m)"""
    pts = [V3(p) for p in pts]; out = []; d = [0.0]
    for a, b in zip(pts, pts[1:]): d.append(d[-1] + (b - a).length)
    n = max(1, int(d[-1] / pitch)); step = d[-1] / n
    def at(s):
        i = 1
        while i < len(d) - 1 and d[i] < s: i += 1
        t = (s - d[i - 1]) / max(1e-9, d[i] - d[i - 1]); p = pts[i - 1].lerp(pts[i], t)
        if sag: p = p + V3((0, -sag * math.sin(math.pi * s / d[-1]), 0))
        return p
    for i in range(n):
        a, b = at(i * step), at((i + 1) * step); mid = (a + b) / 2; dz = (b - a)
        up = V3((0, 1, 0)) if abs(dz.normalized().y) < 0.9 else V3((1, 0, 0))
        Mx = frame(dz, up, mid) @ RZ(math.pi / 2 * (i % 2))
        if cheap: out.append(xf(p_box(W, r * 2.2, step * 1.25), Mx))
        else: out.append(xf(xf(p_link(step * 1.35, W, r), RX(0)), Mx))
    return out


def wheel_prim(r, w=0.13, k=14, flange=0.03, inner=True):
    """a rail wheel on the x axis, tread r, centred on x = 0 with the flange on -x (the inside). dished, with a hub"""
    prof = [(-w / 2 - 0.012, r * 0.55), (-w / 2 - 0.012, r + flange), (-w / 2 + 0.014, r + flange), (-w / 2 + 0.03, r + 0.004), (w / 2, r - 0.004), (w / 2, r * 0.82), (w / 2 - 0.035, r * 0.74), (w / 2 - 0.035, r * 0.36), (w / 2 + 0.03, r * 0.3), (w / 2 + 0.03, r * 0.12)]
    return p_lathe_x(prof, k, cap0=inner, cap1=True)


def leaf_spring(L, n=5, t=0.016, w=0.085, drop=0.07):
    """a leaf spring along z, its middle on the origin (the buckle), the eyes up at the ends. -> prims"""
    out = []
    for i in range(n):
        Li = L * (1 - 0.17 * i); segs = 4
        for s in range(segs):
            z0 = -Li / 2 + Li * s / segs; z1 = z0 + Li / segs
            y = lambda z: drop * (2 * z / L) ** 2 - i * t
            a = V3((0, y(z0), z0)); b = V3((0, y(z1), z1))
            out.append(xf(p_box(w, t * 0.92, (b - a).length), frame(b - a, (0, 1, 0), (a + b) / 2)))
    out.append(xf(p_box(w + 0.03, n * t + 0.03, 0.09), T(0, -(n - 1) * t / 2, 0)))
    return out


def spring_pack(L, n=5, t=0.016, w=0.085, drop=0.07):
    """a leaf spring as one solid along z: n leaves thick at the buckle, one at the eyes, bowed up to them. the top of its
    middle is the origin. -> prims (the pack, its buckle)"""
    st = 6; rings = []
    for i in range(st + 1):
        z = -L / 2 + L * i / st; u = abs(2 * z / L); yt = drop * u * u; th = t * (1 + (n - 1) * max(0.0, 1 - u) ** 0.8)
        rings.append([V3((-w / 2, yt - th, z)), V3((w / 2, yt - th, z)), V3((w / 2, yt, z)), V3((-w / 2, yt, z))])
    return [p_loft(rings, cap0=True, cap1=True), cbx(-w / 2 - 0.014, -n * t - 0.014, -0.045, w / 2 + 0.014, 0.014, 0.045, 0.008)]


def rail_profile(top=0.215, foot_y=0.085, head_w=0.115, web_w=0.106, foot_w=0.2):
    hh = 0.048; hw = head_w / 2; ww = web_w / 2; fw = foot_w / 2
    return [(-fw, foot_y), (fw, foot_y), (fw, foot_y + 0.016), (ww, foot_y + 0.03), (ww, top - hh - 0.008), (hw, top - hh), (hw, top - 0.008), (hw - 0.012, top), (-hw + 0.012, top), (-hw, top - 0.008), (-hw, top - hh), (-ww, top - hh - 0.008), (-ww, foot_y + 0.03), (-fw, foot_y + 0.016)]


# ------------------------------------------------------------ the buffer: a colour per vertex, weighted normals
class TBuf(Buf):
    def add(s, prim, m, style=('tile', 0.5), M=None, tint=(1, 1, 1), vt=None, **kw):
        """vt = f(game vertex) -> a colour (or a grey) multiplied in per vertex: soot up a wall, damp down it"""
        n0 = len(s.F)
        super().add(prim, m, style, M, tint, **kw)
        if vt is not None:
            for fi in range(n0, len(s.F)):
                base = c3(s.TI[fi]); s.TI[fi] = [tuple(a * b for a, b in zip(base, c3(vt(s.V[i])))) for i in s.F[fi]]
        return s

    def obj(s, sharp=50, weld=0.0, wn=True):
        me = bpy.data.meshes.new(s.name)
        me.from_pydata([tuple(gv(*v)) for v in s.V], [], s.F)
        uv = me.uv_layers.new(name='UVMap')
        uv.data.foreach_set('uv', [c for f in s.UV for p in f for c in p])
        me.polygons.foreach_set('material_index', s.MI)
        for m in s.mats: me.materials.append(m)
        ca = me.color_attributes.new('tint', 'BYTE_COLOR', 'CORNER'); cols = []
        for f, t in zip(s.F, s.TI):
            if isinstance(t, list):
                for q in t: cols.extend((q[0], q[1], q[2], 1.0))
            else:
                t = c3(t)
                for _ in f: cols.extend((t[0], t[1], t[2], 1.0))
        ca.data.foreach_set('color', cols)
        me.polygons.foreach_set('use_smooth', [True] * len(s.F))
        me.update(); me.validate()
        o = _link(bpy.data.objects.new(s.name, me))
        if weld > 0:
            bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld); bm.to_mesh(me); bm.free()
        fix_uv(o)
        me.set_sharp_from_angle(angle=math.radians(sharp))
        if wn:   # big faces keep their own normal, chamfers blend between them
            md = o.modifiers.new('wn', 'WEIGHTED_NORMAL'); md.mode = 'FACE_AREA'; md.weight = 90; md.keep_sharp = True
        return o


def apply_mods(o):
    """bake the modifier stack into the mesh (the AO bake and the counts want the real thing)"""
    if not o.modifiers: return o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    for md in list(o.modifiers):
        try: bpy.ops.object.modifier_apply(modifier=md.name)
        except Exception as e: print('JF_WARN modifier', o.name, md.name, e); o.modifiers.remove(md)
    return o


def node(o, name, pivot=None, parent=None, hide=False):
    """name a mesh (built in root space), put its origin at pivot (game), parent it"""
    o.name = name; o.data.name = name
    if pivot is not None:
        p = gv(*pivot); o.data.transform(Matrix.Translation(-p)); o.location = p
    if parent is not None: o.parent = parent
    if hide: o['jf_hidden'] = 1
    return o


def empty(name, parent=None, pos=None):
    e = _link(bpy.data.objects.new(name, None))
    if pos is not None: e.location = gv(*pos)
    if parent is not None: e.parent = parent
    return e


def flat_ao(o, v=1.0):
    me = o.data
    if 'AO' in me.color_attributes: me.color_attributes.remove(me.color_attributes['AO'])
    ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER'); ca.data.foreach_set('color', [v, v, v, 1.0] * len(me.loops))


def glb_summary(path):
    """what is in an exported file: node names, triangles per mesh, materials, images (read back from the bytes)"""
    import struct
    raw = open(path, 'rb').read(); jl = struct.unpack('<I', raw[12:16])[0]; js = json.loads(raw[20:20 + jl])
    tris = 0
    for m in js.get('meshes', []):
        for p in m['primitives']: tris += js['accessors'][p['indices']]['count'] // 3
    return dict(kb=len(raw) // 1024, nodes=len(js.get('nodes', [])), meshes=len(js.get('meshes', [])), prims=sum(len(m['primitives']) for m in js.get('meshes', [])),
                tris=tris, materials=[m['name'] for m in js.get('materials', [])], images=len(js.get('images', [])))


# ------------------------------------------------------------ boxes by their corners (arena space), a face at a time
FACES = ('+x', '-x', '+y', '-y', '+z', '-z')


def face_quad(x0, y0, z0, x1, y1, z1, f):
    """one face of a box as a quad wound to look out, its unwrap in metres with u to the right and v up as you look
    at it from outside (the top's v runs toward +z)"""
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    P, w, h = {'+z': ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], dx, dy), '-z': ([(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)], dx, dy),
               '+x': ([(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], dz, dy), '-x': ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], dz, dy),
               '+y': ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], dx, dz), '-y': ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], dx, dz)}[f]
    return [V3(p) for p in P], [(0, 1, 2, 3)], [[(0, 0), (w, 0), (w, h), (0, h)]]


def bx(x0, y0, z0, x1, y1, z1, omit=(), only=None):
    """a plain box from corner to corner (any order), every face with its own upright unwrap"""
    x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1); z0, z1 = min(z0, z1), max(z0, z1)
    return merge(*[face_quad(x0, y0, z0, x1, y1, z1, f) for f in (only or FACES) if f not in omit])


def cbx(x0, y0, z0, x1, y1, z1, c=0.02, bottom=True):
    """a chamfered box from corner to corner"""
    x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1); z0, z1 = min(z0, z1), max(z0, z1)
    return xf(p_cbox(x1 - x0, y1 - y0, z1 - z0, c, bottom), T((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


M_ZX = Matrix(((0, 0, 1, 0), (0, 1, 0, 0), (1, 0, 0, 0), (0, 0, 0, 1)))   # local (x, y, z) -> arena (z, y, x): a mirror, pass it as M so the faces are turned


def ext_x(poly_zy, x0, x1):
    """an outline drawn in the z-y plane (side view), pushed along x. -> (prim, M): add it with M"""
    return p_extrude([(z, y) for z, y in poly_zy], x0, x1), M_ZX


def ext_y(poly_xz, y0, y1):
    """an outline drawn in plan (x, z), pushed up along y. -> (prim, M)"""
    Mx = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # local (x, y, z) -> arena (x, z, y)
    return p_extrude([(x, z) for x, z in poly_xz], y0, y1), Mx


def rod(p0, p1, r, k=6, cap=True, phase=None):
    """a straight bar between two points"""
    return p_tube([p0, p1], r, k, cap0=cap, cap1=cap, phase=math.pi / k if phase is None else phase)


def pipe(pts, r, k=6, cap=True, up=None):
    return p_tube(pts, r, k, cap0=cap, cap1=cap, up=up, phase=math.pi / k)


def fillet(pts, rad, n=3):
    """round the corners of a polyline (handrails): each inner point becomes a short arc"""
    P = [V3(p) for p in pts]; out = [P[0]]
    for a, b, c in zip(P, P[1:], P[2:]):
        d0 = (a - b); d1 = (c - b); r = min(rad, d0.length * 0.45, d1.length * 0.45)
        p0 = b + d0.normalized() * r; p1 = b + d1.normalized() * r
        for i in range(n + 1):
            t = i / n; out.append((p0.lerp(b, t)).lerp(b.lerp(p1, t), t))
    out.append(P[-1])
    return out


def bolt(p, n, r=0.022, h=0.014, k=6):
    """a bolt head at p, standing out along n. -> (prim, M)"""
    return p_prism(k, r, h, r1=r * 0.86, dome=h * 0.3), frame(n, (0, 1, 0), p)


class Kit(TBuf):
    """a TBuf that knows its atlas: cells by name. b.q = every face the whole cell (noise), b.f = the prim's unwrap
    fitted in the cell (bigger faces get more of it), b.e = each face the whole cell, upright (panels, labels)"""
    AT = None; MAT = None

    def __init__(s, name, at=None, mat_=None):
        super().__init__(name)
        if at is not None: s.AT = at
        if mat_ is not None: s.MAT = mat_

    def put(s, prim, key, tint=1.0, how='q', M=None, mat_=None, mg=0.5, **kw):
        at = s.AT; rect = at.R[key]
        if how == 'e':   # each face on the whole cell, the way face_quad lays it. a face much longer or squatter than the cell
            V, F, UV = prim[:3]; U2 = []; cw, ch_ = rect[2] - 2 * mg, rect[3] - 2 * mg     # takes a strip of it instead (stretched paint looks like wood grain)
            for f, uv in zip(F, UV):
                us = [u for u, v in uv]; vs = [v for u, v in uv]; u0, v0 = min(us), min(vs); du = (max(us) - u0) or 1e-6; dv = (max(vs) - v0) or 1e-6
                k = (du / dv) / (cw / ch_)
                if 1 / 2.6 <= k <= 2.6: U2.append([px_uv(rect, at.tex, (u - u0) / du, (v - v0) / dv, mg) for u, v in uv]); continue
                sc = min(cw / du, ch_ / dv); c0 = sum((V[i] for i in f), V3()) / len(f)
                ou = (math.sin(c0.x * 12.9898 + c0.y * 78.233 + c0.z * 37.719) * 43758.5453) % 1.0 * (cw - du * sc); ov = (math.sin(c0.x * 39.3468 + c0.y * 11.135 + c0.z * 83.155) * 24634.6345) % 1.0 * (ch_ - dv * sc)
                U2.append([px_uv(rect, at.tex, (ou + (u - u0) * sc) / cw, (ov + (v - v0) * sc) / ch_, mg) for u, v in uv])
            return s.add((V, F, U2), mat_ or s.MAT, ('tile', 1.0), M, tint, **kw)
        if how == 'u':   # each face at one size of pixel (no stretch): it takes the strip of the cell it covers, somewhere in it
            V, F, UV = prim[:3]; U2 = []; cw, ch_ = rect[2] - 2 * mg, rect[3] - 2 * mg
            for f, uv in zip(F, UV):
                us = [u for u, v in uv]; vs = [v for u, v in uv]; u0, v0 = min(us), min(vs); du = (max(us) - u0) or 1e-6; dv = (max(vs) - v0) or 1e-6
                sc = min(cw / du, ch_ / dv); c0 = sum((V[i] for i in f), V3()) / len(f)
                ou = (math.sin(c0.x * 12.9898 + c0.y * 78.233 + c0.z * 37.719) * 43758.5453) % 1.0 * (cw - du * sc); ov = (math.sin(c0.x * 39.3468 + c0.y * 11.135 + c0.z * 83.155) * 24634.6345) % 1.0 * (ch_ - dv * sc)
                U2.append([px_uv(rect, at.tex, (ou + (u - u0) * sc) / cw, (ov + (v - v0) * sc) / ch_, mg) for u, v in uv])
            return s.add((V, F, U2), mat_ or s.MAT, ('tile', 1.0), M, tint, **kw)
        st = at.quad(key, mg) if how == 'q' else at.fit(key, mg) if how == 'f' else at.face(key, how, mg)
        return s.add(prim, mat_ or s.MAT, st, M, tint, **kw)

    def box(s, x0, y0, z0, x1, y1, z1, key, tint=1.0, how='q', c=0.0, omit=(), faces=None, only=None, seg=0.0, vary=0.06, **kw):
        """a box. c = chamfer. faces = {'+x': key or (key, how)}: those faces take another cell (upright)"""
        if seg:   # cut it into lengths along its longer horizontal side, so a cell is not stretched over metres
            ax = 0 if abs(x1 - x0) >= abs(z1 - z0) else 2; lo = [min(x0, x1), min(y0, y1), min(z0, z1)]; hi = [max(x0, x1), max(y0, y1), max(z0, z1)]
            n = max(1, round((hi[ax] - lo[ax]) / seg)); st = (hi[ax] - lo[ax]) / n; inner = ('+x', '-x') if ax == 0 else ('+z', '-z')
            for i in range(n):
                a = list(lo); d = list(hi); a[ax] = lo[ax] + i * st; d[ax] = lo[ax] + (i + 1) * st
                om = tuple(omit) + ((inner[1],) if i > 0 else ()) + ((inner[0],) if i < n - 1 else ())
                tn = tint * (1 + vary * math.sin(i * 12.9898 + lo[ax] * 3.1)) if isinstance(tint, (int, float)) else tint
                s.box(a[0], a[1], a[2], d[0], d[1], d[2], key, tn, how, 0.0, om, faces, only, **kw)
            return s
        if c: return s.put(cbx(x0, y0, z0, x1, y1, z1, c), key, tint, how, **kw)
        faces = faces or {}
        rest = [f for f in (only or FACES) if f not in omit and f not in faces]
        if rest: s.put(bx(x0, y0, z0, x1, y1, z1, only=rest), key, tint, how, **kw)
        for f, k2 in faces.items():
            if f in omit or (only and f not in only): continue
            k2, h2 = k2 if isinstance(k2, tuple) else (k2, 'e')
            s.put(bx(x0, y0, z0, x1, y1, z1, only=(f,)), k2, tint, h2, **kw)
        return s

    def rod(s, p0, p1, r, key, tint=1.0, k=6, cap=True, **kw): return s.put(rod(p0, p1, r, k, cap), key, tint, **kw)
    def pipe(s, pts, r, key, tint=1.0, k=6, cap=True, **kw): return s.put(pipe(pts, r, k, cap), key, tint, **kw)

    def bolt(s, p, n, key='bolt', r=0.022, h=0.014, tint=1.0, k=6):
        pr, Mx = bolt(p, n, r, h, k); return s.put(pr, key, tint, M=Mx)

    def ext_x(s, poly_zy, x0, x1, key, tint=1.0, how='q', **kw):
        pr, Mx = ext_x(poly_zy, min(x0, x1), max(x0, x1)); return s.put(pr, key, tint, how, M=Mx, **kw)

    def ext_y(s, poly_xz, y0, y1, key, tint=1.0, how='q', **kw):
        pr, Mx = ext_y(poly_xz, min(y0, y1), max(y0, y1)); return s.put(pr, key, tint, how, M=Mx, **kw)

    def ext_z(s, poly_xy, z0, z1, key, tint=1.0, how='q', **kw):
        return s.put(p_extrude(poly_xy, min(z0, z1), max(z0, z1)), key, tint, how, **kw)

    def chain(s, pts, key='chain', tint=1.0, pitch=0.11, W=0.07, r=0.012, sag=0.0):
        """links along a polyline as flat open-ended plates, every other one turned a quarter (8 triangles a link)"""
        P = [V3(p) for p in pts]; d = [0.0]
        for a, b in zip(P, P[1:]): d.append(d[-1] + (b - a).length)
        n = max(1, int(d[-1] / pitch)); step = d[-1] / n
        def at(q):
            i = 1
            while i < len(d) - 1 and d[i] < q: i += 1
            t = (q - d[i - 1]) / max(1e-9, d[i] - d[i - 1]); p = P[i - 1].lerp(P[i], t)
            return p + V3((0, -sag * math.sin(math.pi * q / d[-1]), 0)) if sag else p
        for i in range(n):
            a, b = at(i * step), at((i + 1) * step); dz = b - a
            up = V3((0, 1, 0)) if abs(dz.normalized().y) < 0.9 else V3((1, 0, 0)); L = step * 1.22
            s.put(xf(bx(-W / 2, -r * 1.1, -L / 2, W / 2, r * 1.1, L / 2, omit=('+z', '-z')), frame(dz, up, (a + b) / 2) @ RZ(math.pi / 2 * (i % 2))), key, tint * (0.85 + 0.3 * (i % 2)))
        return s


def figure(b, key, at, h=1.8, yaw=0.0):
    """the pictures' 1.8 m figure, feet at `at`"""
    Mx = T(*at) @ RY(yaw) @ SC(h / 1.8)
    for sz, p in (((0.2, 0.84, 0.2), (-0.12, 0.42, 0)), ((0.2, 0.84, 0.2), (0.12, 0.42, 0)), ((0.5, 0.62, 0.26), (0, 1.15, 0)), ((0.14, 0.62, 0.16), (-0.33, 1.15, 0)), ((0.14, 0.62, 0.16), (0.33, 1.15, 0)), ((0.24, 0.28, 0.24), (0, 1.66, 0))):
        b.add(bx(p[0] - sz[0] / 2, p[1] - sz[1] / 2, p[2] - sz[2] / 2, p[0] + sz[0] / 2, p[1] + sz[1] / 2, p[2] + sz[2] / 2), key, ('tile', 1.0), Mx)
    return b
