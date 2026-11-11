# Round 4, batch B: the street. Map props the game instances (one draw call per material per prop type), each built
# exactly over its box version in shared/map.js / shared/jankburg.js at the reference parameters (rot 0, the kit
# function's (x, z) at the origin, y = 0 the ground), so the game can fit it onto every copy's boxes (meta.box):
#   p_streetlight  streetlight() map.js:168     cobra-head street light: galvanised tapered pole on an octagonal cast
#                                                shroud, truss arm, die-cast head with a sag lens (glow), photocell, a
#                                                LOST CAT flyer. ~1,400 copies, mostly seen from the roofs: far away the
#                                                whole head glows, like the box version's lamp
#   p_acunit       acUnit() map.js:174          rooftop condensing unit (BRRR) on sleepers: coil guards, service end with
#                                                the line set + disconnect, the fan in its orifice under a wire guard
#   p_watertower   waterTower() map.js:175      the city rooftop tank: cedar staves, iron hoops (closer at the bottom,
#                                                where the pressure is), cone roof + hatch, red-oxide stand, X rods, ladder
#   p_billboard    billboard() map.js:181       the face only: a frame lip over the picture's edge, catwalk, rail, four
#                  + adBoard() map.js:1004      gooseneck lamps (glow). the picture stays the game's box
#   p_billboard_post                            one billboard leg (each post box fits its own): pipe column, base plate
#   p_barrier      barrier() map.js:1661        New Jersey profile, forklift slots, red/white band, NO VAULTING stencil
#   p_cone         cones() map.js:1525          traffic cone on its square rubber base, raised reflective collar
#   p_vending      vending() jankburg.js:505    JANK COLA machine: lit front + selection buttons (glow), coin plate,
#                                                bill slot, delivery flap, KICK HERE. cabinet = tint (the panel colour)
#   p_generator    generatorTower() map.js:1511 DAY MAKER towable light tower: enclosure on a trailer, outrigger jacks,
#                                                telescopic mast with its winch, four LED floods (glow)
# Every file: lod0 under the root, the far one under `lod1`, baked AO in the vertex colours, <= 3 materials.
# run: blender -b --python tools/blender/make_street.py -- [--only=streetlight,cone] [--qa] [--no-sheet] [--no-export]
#      [--lod1-sheet] (lod1 alone, to the scratch folder) [--qa-pairs] (names the parts that z-fight / float)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link, _image
import lib

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = set(next((a.split('=', 1)[1] for a in ARGV if a.startswith('--only=')), '').split(',')) - {''}
SCRATCH = '/tmp/claude-0/-workspace-jankfire/86957797-7d93-5698-a006-852e0a15c9f9/scratchpad/agents/r4_street'
EXPO = -0.45  # the review renders a touch darker: pale paint and concrete blow out under the studio rig
V3 = Vector


# ------------------------------------------------------------ texture atlas (one small image per material)
class Atlas:
    """an h x w srgb canvas cut into named pixel rects (top-left origin, like tex_canvas)"""
    def __init__(self, name, w, h, bg=0x808080):
        self.name, self.w, self.h, self.R = name, w, h, {}
        self.px = np.zeros((h, w, 3), np.float32); self.px[:] = hexrgb(bg)

    def add(self, key, x, y, w, h, paint=None):
        self.R[key] = (x, y, w, h)
        if paint is not None: paint(self.px[y:y + h, x:x + w])
        return key

    def rect(self, key, inset=0.5):  # -> (u0, v0, u1, v1), v up
        x, y, w, h = self.R[key]
        return ((x + inset) / self.w, 1 - (y + h - inset) / self.h, (x + w - inset) / self.w, 1 - (y + inset) / self.h)

    def image(self):
        return _image(self.name, np.clip(self.px, 0, 1))


def tnoise(h, w, cells, rng):  # smooth value noise, tiles
    lat = rng.random((cells, cells))
    def axis(n):
        t = np.arange(n) * cells / n; i0 = np.floor(t).astype(int) % cells
        f = t - np.floor(t); return i0, (i0 + 1) % cells, f * f * (3 - 2 * f)
    y0, y1, fy = axis(h); x0, x1, fx = axis(w)
    a = lat[y0][:, x0] * (1 - fx)[None] + lat[y0][:, x1] * fx[None]
    b = lat[y1][:, x0] * (1 - fx)[None] + lat[y1][:, x1] * fx[None]
    return a * (1 - fy)[:, None] + b * fy[:, None]


def p_noise(base, var=0.1, seed=1, cells=4, speck=None, speck_p=0.0, fine=0.35):
    """crusty paint: soft mottling + per-pixel grain round a base colour, a few specks"""
    def draw(v):
        h, w = v.shape[:2]; r = np.random.default_rng(seed)
        n = (1 - fine) * tnoise(h, w, max(1, cells), r) + fine * r.random((h, w))
        v[:] = hexrgb(base)[None, None] * (1 - var + 2 * var * n[:, :, None])
        if speck is not None: v[r.random((h, w)) < speck_p] = hexrgb(speck)
    return draw


def p_flat(c):
    def draw(v): v[:] = hexrgb(c)
    return draw


def p_text(v, s, x, y, scale, color, bold=False):
    text_px(v, s, x, y, scale, color)
    if bold: text_px(v, s, x + 1, y, scale, color)


def twidth(s, scale=1): return (len(s) * 6 - 1) * scale


# ------------------------------------------------------------ uv mapping into atlas rects
def _gp(mw, co):  # local blender co -> game world point
    w = mw @ co
    return (w.x, w.z, -w.y)


def _gn(nm, n):  # local blender normal -> game world normal
    w = nm @ n
    return (w.x, w.z, -w.y)


def uv_fit(o, rect, axis=None, keep_aspect=True):
    """every face projected from its dominant axis (or `axis`), the whole object scaled to fit `rect` (crusty paint,
    flat colours: density doesn't matter there). faces never get zero area"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_basis.copy(); nm = mw.to_3x3().inverted().transposed()
    st = []
    for p in me.polygons:
        gn = _gn(nm, p.normal)
        ax = axis or 'xyz'[max(range(3), key=lambda i: abs(gn[i]))]
        for li in p.loop_indices:
            g = _gp(mw, me.vertices[me.loops[li].vertex_index].co)
            s, t = {'x': (-g[2] if gn[0] >= 0 else g[2], g[1]), 'y': (g[0], -g[2] if gn[1] >= 0 else g[2]),
                    'z': (g[0] if gn[2] >= 0 else -g[0], g[1])}[ax]
            st.append((li, s, t))
    s0, s1 = min(e[1] for e in st), max(e[1] for e in st)
    t0, t1 = min(e[2] for e in st), max(e[2] for e in st)
    u0, v0, u1, v1 = rect
    ks, kt = (u1 - u0) / max(s1 - s0, 1e-6), (v1 - v0) / max(t1 - t0, 1e-6)
    if keep_aspect: ks = kt = min(ks, kt)
    for li, s, t in st: uv[li].uv = (u0 + (s - s0) * ks, v0 + (t - t0) * kt)
    return o


def uv_decal(o, rect, c, size, view='-z'):
    """straight-on mapping of a game-space rectangle (centre c, size (w, h)) seen from `view` ('-z' = from the front,
    '+x' = from the right...): the image's right is the viewer's right"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_basis.copy()
    u0, v0, u1, v1 = rect
    for p in me.polygons:
        for li in p.loop_indices:
            g = _gp(mw, me.vertices[me.loops[li].vertex_index].co)
            d = (g[0] - c[0], g[1] - c[1], g[2] - c[2])
            a, b = {'-z': (-d[0], d[1]), '+z': (d[0], d[1]), '+x': (-d[2], d[1]), '-x': (d[2], d[1]), '+y': (d[0], -d[2])}[view]
            uv[li].uv = (u0 + (a / size[0] + 0.5) * (u1 - u0), v0 + (b / size[1] + 0.5) * (v1 - v0))
    return o


def uv_lathe(o, rect, y0, y1, cx=0.0, cz=0.0, turn=0.0, a0=None, a1=None):
    """round things on a vertical axis through (cx, cz): v = height (y0 -> v0, y1 -> v1, so bands painted across the
    rect land at their height), u = the angle round the axis (from +x towards +z). a0/a1 (radians) = only that arc maps
    across the rect, a0 at u0 (labels on a pole)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_basis.copy()
    u0, v0, u1, v1 = rect
    for p in me.polygons:
        ls = []
        for li in p.loop_indices:
            g = _gp(mw, me.vertices[me.loops[li].vertex_index].co)
            ls.append([li, g[1], math.atan2(g[2] - cz, g[0] - cx) - turn])
        if a0 is None:
            ref = ls[0][2] % (2 * math.pi)
            for e in ls:
                a = e[2] % (2 * math.pi)
                while a - ref > math.pi: a -= 2 * math.pi
                while a - ref < -math.pi: a += 2 * math.pi
                e[2] = a / (2 * math.pi)
        for li, h, a in ls:
            uu = (a - a0) / (a1 - a0) if a0 is not None else a
            vv = (h - y0) / (y1 - y0)
            uv[li].uv = (u0 + min(max(uu, 0.0), 1.0) * (u1 - u0), v0 + min(max(vv, 0.0), 1.0) * (v1 - v0))
    return o


def uv_unzero(o, eps=0.0015):
    """faces whose uvs collapsed (thin edges seen side-on) get a tiny spread, so no face has zero uv area"""
    me = o.data
    if not me.uv_layers: return o
    uv = me.uv_layers.active.data
    for p in me.polygons:
        pts = [uv[li].uv.copy() for li in p.loop_indices]
        a2 = sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))
        if abs(a2) < 1e-9:
            c = sum(pts, Vector((0, 0))) / len(pts)
            for k, li in enumerate(p.loop_indices):
                a = 2 * math.pi * k / len(pts)
                uv[li].uv = (c.x + eps * math.cos(a), c.y + eps * math.sin(a))
    return o


# ------------------------------------------------------------ geometry helpers
def join_all(objs, name):
    """join parts into one mesh in root space (transforms applied, custom normals kept), zero-area uvs spread"""
    objs = [o for o in objs if o is not None]
    if '--qa-pairs' in ARGV:  # all the parts as separate objects: the report names which two z-fight
        for o in objs: apply_mods(o)
        res = qa(objs, 'pairs ' + name)
        for z in res.get('zfighting', []): print('QA_ZF', name, z)
        for z in res.get('floating', []): print('QA_FL', name, z)
    for o in objs:
        apply_mods(o)
        if not o.data.uv_layers: uv_fit(o, (0.0, 0.0, 0.02, 0.02))  # (flat-colour parts: any uvs, but not zero area)
        uv_unzero(o)
    for s_ in bpy.context.view_layer.objects.selected: s_.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    j.name = name; j.data.name = name
    return j


def weld(o, dist=1e-5):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bm.to_mesh(o.data); bm.free()
    return o


def mesh_from(name, verts, faces, m, smooth_angle=None):
    """a mesh from game-space verts + faces (vertex index lists)"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(*p)) for p in verts]
    for f in faces:
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    if smooth_angle: smooth(o, smooth_angle)
    return o


def prism(name, outline, y0, y1, m, smooth_angle=None):
    """a vertical prism over a plan outline [(x, z)] from y0 to y1 (caps included)"""
    n = len(outline)
    verts = [(x, y0, z) for x, z in outline] + [(x, y1, z) for x, z in outline]
    faces = [list(range(n))[::-1], list(range(n, 2 * n))] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    return mesh_from(name, verts, faces, m, smooth_angle)


def ring_strip(name, r, y0, y1, a0, a1, n, m, depth=0.004):
    """a curved sheet hugging a round pole (a flyer, a tag): radius r on the outside, `depth` thick inward"""
    verts, faces = [], []
    for rr in (r, r - depth):
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            verts += [(math.cos(a) * rr, y0, math.sin(a) * rr), (math.cos(a) * rr, y1, math.sin(a) * rr)]
    k = 2 * (n + 1)
    for i in range(n):
        a, b = 2 * i, 2 * i + 2
        faces.append([a, b, b + 1, a + 1]); faces.append([k + a + 1, k + b + 1, k + b, k + a])
        faces.append([a + 1, b + 1, k + b + 1, k + a + 1]); faces.append([a, k + a, k + b, b])
    faces.append([0, 1, k + 1, k]); faces.append([2 * n, k + 2 * n, k + 2 * n + 1, 2 * n + 1])
    return mesh_from(name, verts, faces, m, 30)


def bbox(objs):
    lo = [1e9] * 3; hi = [-1e9] * 3
    for o in objs:
        mw = o.matrix_world
        for v in o.data.vertices:
            g = _gp(mw, v.co)
            for k in range(3): lo[k] = min(lo[k], g[k]); hi[k] = max(hi[k], g[k])
    return lo, hi


def check_env(tag, objs, lo, hi, tol=0.004):
    """the model has to fill the box version's extent exactly: the game fits its bounding box onto the boxes"""
    a, b = bbox(objs)
    bad = [k for k in range(3) if abs(a[k] - lo[k]) > tol or abs(b[k] - hi[k]) > tol]
    print(f'JF_ENV {tag}: x {a[0]:.3f}..{b[0]:.3f} y {a[1]:.3f}..{b[1]:.3f} z {a[2]:.3f}..{b[2]:.3f}'
          f' (box x {lo[0]}..{hi[0]} y {lo[1]}..{hi[1]} z {lo[2]}..{hi[2]}) {"OK" if not bad else "OFF " + "xyz"[bad[0]]}')
    return not bad


def uv_faces(o, pick):
    """per-face mapping: pick(game normal, game face centre) -> a key; keys map with KEYS[key] = (rect, mode, *args):
    ('decal', c, size, view) straight-on, or ('fit',) the group's faces fitted into the rect together"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_basis.copy(); nm = mw.to_3x3().inverted().transposed()
    groups = {}
    for p in me.polygons:
        gn = _gn(nm, p.normal); gc = _gp(mw, p.center)
        k = pick(gn, gc)
        if k is not None: groups.setdefault(k, []).append((p, gn))
    return groups, uv, mw


def map_groups(o, pick, spec):
    """spec[key] = (rect, 'decal', centre, size, view) | (rect, 'fit')"""
    groups, uv, mw = uv_faces(o, pick)
    me = o.data
    for k, faces in groups.items():
        sp = spec[k]; rect = sp[0]; u0, v0, u1, v1 = rect
        if sp[1] == 'decal':
            c, size, view = sp[2], sp[3], sp[4]
            for p, gn in faces:
                for li in p.loop_indices:
                    g = _gp(mw, me.vertices[me.loops[li].vertex_index].co)
                    d = (g[0] - c[0], g[1] - c[1], g[2] - c[2])
                    a, b = {'-z': (-d[0], d[1]), '+z': (d[0], d[1]), '+x': (-d[2], d[1]), '-x': (d[2], d[1]), '+y': (d[0], -d[2]), '-y': (d[0], d[2])}[view]
                    uv[li].uv = (u0 + (a / size[0] + 0.5) * (u1 - u0), v0 + (b / size[1] + 0.5) * (v1 - v0))
        else:
            st = []
            for p, gn in faces:
                ax = max(range(3), key=lambda i: abs(gn[i]))
                for li in p.loop_indices:
                    g = _gp(mw, me.vertices[me.loops[li].vertex_index].co)
                    st.append((li,) + ((g[2], g[1]), (g[0], g[2]), (g[0], g[1]))[ax])
            s0, s1 = min(e[1] for e in st), max(e[1] for e in st); t0, t1 = min(e[2] for e in st), max(e[2] for e in st)
            kk = min((u1 - u0) / max(s1 - s0, 1e-6), (v1 - v0) / max(t1 - t0, 1e-6))
            for li, a, b in st: uv[li].uv = (u0 + (a - s0) * kk, v0 + (b - t0) * kk)
    return o


def side_of(gn, thr=0.6):
    """which way a face looks: '+x' '-x' '+y' '-y' '+z' '-z' (or None if it's slanted)"""
    ax = max(range(3), key=lambda i: abs(gn[i]))
    if abs(gn[ax]) < thr: return None
    return ('+' if gn[ax] > 0 else '-') + 'xyz'[ax]


def frame_ring(name, outer, inner, z0, z1, m):
    """a rectangular ring in the x-y plane (outer / inner = (x0, y0, x1, y1)) from z0 to z1: picture frames, bezels"""
    def rect(r, z): x0, y0, x1, y1 = r; return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    verts = rect(outer, z0) + rect(inner, z0) + rect(inner, z1) + rect(outer, z1)
    faces = []
    for i in range(4):
        j = (i + 1) % 4
        faces += [[i, j, 4 + j, 4 + i], [4 + i, 4 + j, 8 + j, 8 + i], [8 + i, 8 + j, 12 + j, 12 + i], [12 + i, 12 + j, j, i]]
    return mesh_from(name, verts, faces, m, 30)


def turn_obj(o, axis, ang, pivot):
    """rotate an object's mesh about a game-space pivot (axis 'x' 'y' 'z' in game axes)"""
    apply_mods(o)
    ba = {'x': V3((1, 0, 0)), 'y': V3((0, 0, 1)), 'z': V3((0, -1, 0))}[axis]
    pv = gv(*pivot)
    M = Matrix.Translation(pv) @ Matrix.Rotation(ang, 4, ba) @ Matrix.Translation(-pv)
    o.data.transform(o.matrix_basis.inverted() @ M @ o.matrix_basis)
    return o


def count_tris(o):
    o.data.calc_loop_triangles(); return len(o.data.loop_triangles)


# ------------------------------------------------------------ finishing: AO, QA, metadata, sheet
def qa(objs, tag):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=0.0008, tol=0.002)
    print('QA_PASS', tag, res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], tag, e)
    for e in res.get('enclosed', []): print('QA_ENCLOSED', tag, e)  # (where: hidden parts are wasted tris)
    for n, m in res.get('objects', {}).items():
        bad = {k: v for k, v in m.items() if k in ('degenerate_faces', 'zero_length_edges', 'nonmanifold_edges', 'inconsistent_normals_edges', 'inside_out_islands', 'duplicate_verts', 'ngons', 'uv_zero_area_faces') and v}
        print('QA_PART', tag, n, m.get('tris'), 'tris', m.get('materials'), 'mats', bad)
    return res


def ao_for_sheet(objs):
    """the game multiplies the baked AO in: show it in the review renders too (after export, so the glb is untouched)"""
    done = set()
    for o in objs:
        for m in o.data.materials:
            if m is None or m.name in done or m.name == 'glow': continue
            done.add(m.name)
            nt = m.node_tree; b = nt.nodes['Principled BSDF']
            ca = nt.nodes.new('ShaderNodeVertexColor'); ca.layer_name = 'AO'
            mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs['Fac'].default_value = 1.0
            src = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].links else None
            if src is not None: nt.links.new(src, mix.inputs['Color1'])
            else: mix.inputs['Color1'].default_value = b.inputs['Base Color'].default_value
            nt.links.new(ca.outputs['Color'], mix.inputs['Color2'])
            if m.name == 'tint':  # preview what a copy looks like: the map's neonpink panel colour, as Neon Market gets it
                tm = nt.nodes.new('ShaderNodeMixRGB'); tm.blend_type = 'MULTIPLY'; tm.inputs['Fac'].default_value = 1.0
                tm.inputs['Color2'].default_value = srgb(0xff2ad4)
                nt.links.new(mix.outputs['Color'], tm.inputs['Color1']); mix = tm
            nt.links.new(mix.outputs['Color'], b.inputs['Base Color'])


def finish_prop(fid, lod0, lod1, meta, env, ao_dist=0.3, sheet_kw=None):
    """lod0 / lod1 = lists of finished parts (each joined into one mesh per lod). env = the box version's extent"""
    m0 = join_all(lod0, f"{meta['id']}_lod0"); weld(m0)
    m1 = join_all(lod1, f"{meta['id']}_lod1"); weld(m1)
    for o in (m0, m1):
        if len(o.data.materials) > 3: print('JF_WARN too many materials', o.name, [m.name for m in o.data.materials])
    ok0 = check_env(fid + ' lod0', [m0], *env); ok1 = check_env(fid + ' lod1', [m1], *env)
    if '--qa' in ARGV:
        qa([m0], fid + ' lod0'); qa([m1], fid + ' lod1')
    lib.bake_ao([m0], dist=ao_dist); lib.bake_ao([m1], dist=ao_dist)
    meta = dict(meta); meta.setdefault('box', [list(env[0]), list(env[1])])
    root = lib.prop_finish(fid, [m0], [m1], meta)
    t0, t1 = lib.prop_stats(root)
    print(f'JF_MATS {fid}: lod0 {[m.name for m in m0.data.materials]} lod1 {[m.name for m in m1.data.materials]} env {"OK" if ok0 and ok1 else "OFF"}')
    return root, m0, m1, t0, t1


def lod_sheet(root, m0, m1, fid, t1, **kw):
    """the repo sheet shows lod0 (lod1 hidden and unparented meanwhile); a scratch sheet shows lod1 alone"""
    e = next(c for c in root.children if c.name == 'lod1')
    ao_for_sheet([m0, m1])
    e.parent = None; m1.hide_render = True
    sheet(root, fid, extra_note=f'LOD1 {t1}', exposure=EXPO, **kw)
    if '--lod1-sheet' not in ARGV: return
    m1.hide_render = False; m0.hide_render = True
    m1.parent = None
    tmp_root = _link(bpy.data.objects.new(fid + '_l1', None)); m1.parent = tmp_root
    old = lib.SHEETS; lib.SHEETS = os.path.join(SCRATCH, 'lod1'); os.makedirs(lib.SHEETS, exist_ok=True)
    try: sheet(tmp_root, fid + '_lod1', extra_note='LOD1', exposure=EXPO, **kw)
    finally: lib.SHEETS = old
    m0.hide_render = False


def close_shots(root, views, tag):
    for a in ARGV:
        if a.startswith('--close='):
            sys.path.insert(0, SCRATCH)
            import closeup
            far = [c for c in root.children_recursive if c.type == 'MESH' and c.parent is not None and c.parent.name == 'lod1']
            for c in far: c.hide_render = True  # (lod1 sits inside lod0: the game draws one or the other)
            closeup.shots(root, views, a.split('=', 1)[1], tag, exposure=EXPO)
            for c in far: c.hide_render = False


# ------------------------------------------------------------ p_streetlight
def build_streetlight():
    """streetlight() map.js:168: pole 0.25 x 6, arm x 0..1.6 at y 5.8..6.0, lamp 0.6 x 0.25 x 0.4 at x 1.6, y 5.8"""
    A = Atlas('sl_atlas', 64, 128)
    POLE_Y0, POLE_Y1 = 0.0, 6.0
    def pole_paint(v):  # galvanised zinc: pale grey, spangle mottling, a yellow reflective band at 0.95-1.1 m
        p_noise(0x8a9199, 0.1, 11, cells=6, fine=0.5)(v)
        h = v.shape[0]
        for y0, y1, c in ((0.95, 1.1, 0xffd21a), (1.0, 1.05, 0xe8a80c)):
            r0, r1 = int(h * (1 - y1 / POLE_Y1)), int(h * (1 - y0 / POLE_Y1))
            v[r0:r1] = hexrgb(c) * (0.94 + 0.06 * np.random.default_rng(3).random((r1 - r0, v.shape[1], 1)))
        v[int(h * (1 - 0.45 / POLE_Y1)):] *= 0.9  # a little grime at the bottom
    A.add('pole', 0, 0, 16, 128, pole_paint)
    A.add('base', 16, 0, 16, 32, p_noise(0x50565e, 0.12, 12, cells=4, speck=0x6e747a, speck_p=0.06))
    A.add('arm', 16, 32, 16, 32, p_noise(0x848c94, 0.08, 13, cells=4))
    A.add('head', 32, 0, 32, 32, p_noise(0x9ea4aa, 0.06, 14, cells=4))
    A.add('dark', 32, 32, 16, 16, p_noise(0x2a2e34, 0.1, 15))
    def flyer(v):  # a LOST CAT flyer: neon pink paper, black print, a cat
        v[:] = hexrgb(0xff6fd8) * (0.93 + 0.07 * np.random.default_rng(5).random(v.shape[:2] + (1,)))
        p_text(v, 'LOST', 2, 2, 1, 0x1a0a1a); p_text(v, 'CAT', 4, 11, 1, 0x1a0a1a)
        c = hexrgb(0x1a0a1a)
        v[21:27, 6:13] = c; v[19:21, 6] = c; v[19:21, 12] = c  # the cat's head and ears
        v[23, 8] = hexrgb(0xffe14d); v[23, 10] = hexrgb(0xffe14d)  # its eyes
        p_text(v, 'JANK', 2, 30, 1, 0x1a0a1a)
        for x in range(2, 26, 4): v[40:44, x:x + 2] = c  # tear-off tabs
    A.add('flyer', 32, 48, 28, 46, flyer)
    def tag(v):  # the pole number plate
        v[:] = hexrgb(0x1f4fc8); v[1:-1, 1:-1] = hexrgb(0x2a66e8)
        p_text(v, '13', 3, 3, 1, 0xffffff, bold=True)
    A.add('tag', 48, 32, 16, 13, tag)
    steel = mat('sl_steel', 0xffffff, rough=0.42, metal=0.3, clearcoat=0.3, tex=A.image())
    G = Atlas('glow_atlas', 16, 16)
    def leds(v):  # warm white sag lens with a grid of brighter LED dots
        v[:] = hexrgb(0xffe9a8)
        for y in range(1, 16, 3):
            for x in range(1 + (y // 3) % 2, 16, 3): v[y, x] = hexrgb(0xfffbe8)
    G.add('lens', 0, 0, 16, 16, leds)
    glow = mat('glow', 0xffffff, rough=0.3, emit=0xffffff, strength=1.0, tex=G.image(), emit_tex=True)
    P = []
    # pole: cast base shroud -> tapered galvanised shaft -> domed cap (12 sides, a vertex on +-x keeps x min = -0.125)
    shroud = lathe([(0.125, 0.0), (0.125, 0.055), (0.106, 0.1), (0.096, 0.36), (0.086, 0.43)], m=steel, seg=8, axis='y', name='sl_shroud', cap=False)
    smooth(shroud, 30)  # an octagonal casting: crisp facets
    uv_lathe(shroud, A.rect('base'), 0.0, 0.43); P.append(shroud)
    shaft = lathe([(0.084, 0.4), (0.063, 5.84), (0.067, 5.845), (0.067, 5.88), (0.045, 5.925), (0.0, 5.94)], m=steel, seg=12, axis='y', name='sl_shaft', cap=False)
    uv_lathe(shaft, A.rect('pole'), POLE_Y0, POLE_Y1); P.append(shaft)
    hh = box((0.024, 0.15, 0.075), (-0.081, 0.66, 0), steel, bev=0.006, seg=1, name='sl_handhole')
    apply_mods(hh); uv_fit(hh, A.rect('base')); P.append(hh)
    pr = lambda y: 0.084 + (0.063 - 0.084) * (y - 0.4) / 5.44  # the shaft's radius at a height (its 12-gon's corners)
    fl = ring_strip('sl_flyer', pr(1.545) + 0.002, 1.45, 1.64, math.radians(55), math.radians(125), 4, steel, depth=0.006)
    uv_lathe(fl, A.rect('flyer'), 1.45, 1.64, a0=math.radians(125), a1=math.radians(55)); P.append(fl)
    tg = ring_strip('sl_tag', pr(2.59) + 0.002, 2.55, 2.63, math.radians(-110), math.radians(-70), 2, steel, depth=0.006)
    uv_lathe(tg, A.rect('tag'), 2.55, 2.63, a0=math.radians(-70), a1=math.radians(-110)); P.append(tg)
    # the arm: a mounting collar, the arm sweeping up and out to the head's slip fitter, a truss brace under it
    col = cyl(0.074, 0.2, (0, 5.5, 0), steel, axis='y', seg=12, bev=0.008, name='sl_collar')
    apply_mods(col); uv_fit(col, A.rect('arm')); P.append(col)
    path = [(0.0, 5.5, 0), (0.06, 5.66, 0), (0.19, 5.83, 0), (0.42, 5.925, 0), (0.78, 5.952, 0), (1.12, 5.944, 0), (1.29, 5.905, 0), (1.38, 5.845, 0)]
    arm = sweep(path, [0.05, 0.049, 0.047, 0.045, 0.043, 0.041, 0.04, 0.04], steel, seg=8, name='sl_arm')  # (its end in the head's slip fitter)
    uv_fit(arm, A.rect('arm')); P.append(arm)
    br = rod((0.05, 5.12, 0), (0.62, 5.935, 0), 0.02, steel, seg=6, name='sl_brace')
    uv_fit(br, A.rect('arm')); P.append(br)
    # the head: die-cast cobra housing lofted along x (plan teardrop, domed top, flat underside), sag lens, photocell
    st = [(1.30, 0.062, 5.742, 5.858), (1.345, 0.11, 5.712, 5.886), (1.43, 0.165, 5.70, 5.912), (1.55, 0.198, 5.70, 5.925),
          (1.68, 0.192, 5.70, 5.918), (1.79, 0.15, 5.70, 5.888), (1.865, 0.085, 5.708, 5.845), (1.9, 0.0, 5.75, 5.78)]
    def sec(i, t):
        x, w, yb, yt = st[i]
        w = max(w, 0.004); h = yt - yb; yc = 5.8
        pts = [(yb - yc, -0.82 * w), (yb - yc, 0.82 * w)]
        for k in range(7):
            a = math.pi * k / 6
            pts.append((yb + 0.012 + (h - 0.012) * math.sin(a) - yc, w * math.cos(a)))
        return pts
    head = loft([(x, 5.8, 0.0) for x, *_ in st], sec, steel, name='sl_head', cap=True, up=(0, 1, 0), smooth_angle=55)
    uv_fit(head, A.rect('head')); P.append(head)
    lens_pts = []
    for k in range(12):
        a = 2 * math.pi * k / 12
        lens_pts.append((1.645 + 0.205 * math.cos(a), 0.158 * math.sin(a)))
    verts = [(x, 5.704, z) for x, z in lens_pts] + [(1.645 + 0.6 * (x - 1.645), 5.686, 0.6 * z) for x, z in lens_pts] + [(1.645, 5.675, 0.0)]
    faces = [[(k + 1) % 12, k, 12 + k, 12 + (k + 1) % 12] for k in range(12)] + [[12 + (k + 1) % 12, 12 + k, 24] for k in range(12)]  # (its top is inside the housing: no cap)
    lens = mesh_from('sl_lens', verts, faces, glow, 50)
    uv_decal(lens, G.rect('lens'), (1.645, 5.68, 0), (0.42, 0.33), '+y'); P.append(lens)
    pc = lathe([(0.034, 5.885), (0.034, 5.965), (0.024, 5.992), (0.0, 6.0)], (1.47, 0, 0), steel, seg=8, axis='y', name='sl_photocell', cap=True)
    uv_fit(pc, A.rect('dark')); P.append(pc)
    latch = box((0.05, 0.03, 0.09), (1.335, 5.875, 0), steel, bev=0.006, seg=1, name='sl_latch')
    apply_mods(latch); uv_fit(latch, A.rect('dark')); P.append(latch)
    # lod1: 6-sided pole, a 4-sided arm, a wedge head + its lens (one quad)
    Q = []
    lp = lathe([(0.125, 0.0), (0.09, 0.42), (0.064, 5.86), (0.0, 5.93)], m=steel, seg=6, axis='y', name='sl1_pole', cap=False)
    uv_lathe(lp, A.rect('pole'), 0, 6); Q.append(lp)
    la = sweep([(0.0, 5.5, 0), (0.2, 5.86, 0), (0.6, 5.956, 0), (1.2, 5.93, 0), (1.42, 5.82, 0)], [0.05, 0.047, 0.044, 0.041, 0.04], steel, seg=4, name='sl1_arm')
    uv_fit(la, A.rect('arm')); Q.append(la)
    hv = [(1.3, 5.735, -0.06), (1.3, 5.735, 0.06), (1.3, 5.86, 0.06), (1.3, 5.86, -0.06),
          (1.56, 5.70, -0.2), (1.56, 5.70, 0.2), (1.56, 5.925, 0.2), (1.56, 5.925, -0.2),
          (1.9, 5.73, -0.04), (1.9, 5.73, 0.04), (1.9, 5.79, 0.04), (1.9, 5.79, -0.04)]
    hf = [[0, 1, 2, 3], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0], [4, 8, 9, 5], [5, 9, 10, 6], [6, 10, 11, 7], [7, 11, 8, 4], [8, 11, 10, 9]]
    lh = mesh_from('sl1_head', hv, hf, glow, 40)  # (far away the whole head glows, like the box version's lamp: the
    uv_fit(lh, G.rect('lens')); Q.append(lh)      #  streets still sparkle when you look down on them from the roofs)
    env = ((-0.125, 0.0, -0.2), (1.9, 6.0, 0.2))
    meta = {'id': 'streetlight', 'lod': 60, 'tint': False}
    return finish_prop('p_streetlight', P, Q, meta, env, ao_dist=0.25), [
        ('base', (0.9, 1.2, -1.6), (0, 0.6, 0), 35), ('head', (2.4, 5.2, -1.4), (1.3, 5.8, 0), 35),
        ('head_low', (1.2, 4.6, -1.2), (1.4, 5.75, 0), 30), ('whole', (5.5, 3.5, -7.0), (0.8, 3.0, 0), 35)]


# ------------------------------------------------------------ p_acunit
def build_acunit():
    """acUnit() map.js:174: cabinet 2 x 1.4 x 1.4, grille 1.2 x 0.1 x 1.2 on top. a 5-ton rooftop condenser on sleepers:
    coil guards on three sides, the service end at +x (badge, line set, disconnect), the fan in its orifice on top"""
    A = Atlas('ac_paint_atlas', 128, 160)
    def coil(w_, h_):  # aluminium fins behind a wire guard: fine vertical fins, a square wire grid, dark gaps
        def draw(v):
            h, w = v.shape[:2]; r = np.random.default_rng(w_ * 7 + h_)
            v[:] = hexrgb(0x8c9296)
            v[:, ::2] = hexrgb(0x6a7074)
            v[:] *= (0.92 + 0.08 * r.random((h, w, 1)))
            for y in range(2, h, 6): v[y, :] = hexrgb(0x3a3e42)
            for x in range(3, w, 6): v[:, x] = hexrgb(0x3a3e42)
            v[:2] = hexrgb(0xd6d2c8); v[-2:] = hexrgb(0xd6d2c8)  # the frame lips
        return draw
    A.add('coil_long', 0, 0, 96, 40, coil(96, 40))
    A.add('coil_end', 0, 40, 64, 40, coil(64, 40))
    A.add('paint', 96, 0, 32, 32, p_noise(0xd6d2c8, 0.05, 21, cells=4))  # warm putty enamel
    def service(v):  # the service end: two panels, screws, the badge, a warning sticker
        h, w = v.shape[:2]
        p_noise(0xd6d2c8, 0.05, 22, cells=4)(v)
        v[:, w // 2] = hexrgb(0x9a968c); v[1, :] = hexrgb(0x9a968c); v[-2, :] = hexrgb(0x9a968c)
        for x in (2, w // 2 - 3, w // 2 + 3, w - 3):
            for y in (3, h - 4): v[y, x] = hexrgb(0x5a5850)
        v[8:20, 4:31] = hexrgb(0x1f4fc8); v[9:19, 5:30] = hexrgb(0x2a66e8)  # the BRRR badge
        p_text(v, 'BRRR', 6, 11, 1, 0xffffff)
        v[23:35, 44:58] = hexrgb(0xffd21a); v[23, 44:58] = hexrgb(0x111111); v[34, 44:58] = hexrgb(0x111111)  # HIGH VOLTAGE
        for k, (x0, x1) in enumerate(((52, 54), (51, 53), (50, 52), (49, 54), (51, 53), (50, 52), (49, 51), (48, 50))):
            v[25 + k, x0:x1] = hexrgb(0x111111)  # a zap
    A.add('service', 64, 40, 64, 40, service)
    A.add('dark', 96, 32, 32, 8, p_noise(0x1c1e22, 0.1, 23))  # (the core's top + bottom, hidden)
    def toplbl(v):  # the lid seen from above (2 x 1.4 m): the fan's dark floor in the middle, HOT AIR UP stencilled beside it
        p_noise(0xd6d2c8, 0.05, 24, cells=4)(v)
        h, w = v.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]; d = np.hypot((xx + 0.5 - w / 2) * 2.0 / w, (yy + 0.5 - h / 2) * 1.4 / h)
        v[d < 0.56] = hexrgb(0x1c1e22); v[(d > 0.2) & (d < 0.23)] = hexrgb(0x2c3034)
        for k, t in enumerate(('HOT', 'AIR', 'UP')): p_text(v, t, 2 + (17 - twidth(t)) // 2, 14 + 9 * k, 1, 0x7a2a1a)  # (in the strip left of the fan)
        for k in range(5): v[46 - k, 10 - k:11 + k] = hexrgb(0x7a2a1a)
    A.add('lid', 0, 80, 96, 67, toplbl)  # (2 x 1.4 m at 2 cm a pixel)
    paint = mat('ac_paint', 0xffffff, rough=0.38, clearcoat=0.45, tex=A.image())
    M = Atlas('ac_metal_atlas', 32, 32)
    M.add('steel', 0, 0, 16, 16, p_noise(0x9aa2aa, 0.1, 25, cells=4))
    M.add('black', 16, 0, 16, 16, p_noise(0x22262a, 0.12, 26))
    M.add('copper', 0, 16, 16, 16, p_noise(0xc87a3a, 0.1, 27, cells=4))
    M.add('foam', 16, 16, 16, 16, p_noise(0x18181a, 0.15, 28))
    metal = mat('ac_metal', 0xffffff, rough=0.35, metal=0.6, clearcoat=0.2, tex=M.image())
    P = []
    TOP, R0, n = 1.34, 0.54, 16  # lid underside, the orifice's inner radius, its sides
    for z in (-0.48, 0.48):  # galvanised sleepers
        o = box((2.0, 0.08, 0.12), (0, 0.04, z), metal, name='ac_sleeper'); uv_fit(o, M.rect('steel')); P.append(o)
    o = box((1.9, 0.07, 1.3), (0, 0.105, 0), metal, name='ac_pan'); uv_fit(o, M.rect('steel')); P.append(o)
    core = box((1.86, 1.22, 1.26), (0, 0.13 + 0.61, 0), paint, name='ac_core')  # the coil faces, guard printed on
    map_groups(core, lambda gn, gc: side_of(gn), {
        '-z': (A.rect('coil_long'), 'decal', (0, 0.74, -0.63), (1.86, 1.22), '-z'), '+z': (A.rect('coil_long'), 'decal', (0, 0.74, 0.63), (1.86, 1.22), '+z'),
        '-x': (A.rect('coil_end'), 'decal', (-0.93, 0.74, 0), (1.26, 1.22), '-x'), '+x': (A.rect('service'), 'decal', (0.93, 0.74, 0), (1.26, 1.22), '+x'),
        '+y': (A.rect('dark'), 'fit'), '-y': (A.rect('dark'), 'fit')}); P.append(core)
    for sx in (-1, 1):  # corner posts (they hold the lid)
        for sz in (-1, 1):
            o = box((0.08, 1.24, 0.08), (sx * 0.955, 0.12 + 0.62, sz * 0.655), paint, name='ac_post'); uv_fit(o, A.rect('paint')); P.append(o)  # (ends buried in the pan + lid)
    lid = box((2.0, 0.07, 1.4), (0, TOP + 0.035, 0), paint, bev=0.014, seg=1, name='ac_lid')  # the fan's dark floor is printed on
    apply_mods(lid)
    map_groups(lid, lambda gn, gc: 'top' if gn[1] > 0.9 else 'edge', {'top': (A.rect('lid'), 'decal', (0, 0, 0), (2.0, 1.4), '+y'), 'edge': (A.rect('paint'), 'fit')})
    P.append(lid)
    LT = TOP + 0.07
    ori = lathe([(R0 + 0.035, LT - 0.01), (R0 + 0.035, LT + 0.06), (R0 - 0.004, LT + 0.074), (R0 - 0.004, LT - 0.005)], m=paint, seg=n, axis='y', name='ac_orifice', cap=False)
    uv_fit(ori, A.rect('paint')); P.append(ori)
    mot = lathe([(0.1, LT - 0.01), (0.1, LT + 0.025), (0.0, LT + 0.032)], m=metal, seg=8, axis='y', name='ac_motor', cap=False)
    uv_fit(mot, M.rect('black')); P.append(mot)
    for k in range(3):  # three swept blades, pitched, off the motor's hub
        a = 2 * math.pi * k / 3 + 0.4
        bl = []
        for (rr, da, dy) in ((0.07, -0.2, -0.008), (0.07, 0.2, 0.008), (0.5, 0.3, 0.016), (0.5, -0.1, -0.016)):
            bl.append((math.cos(a + da) * rr, LT + 0.024 + dy, math.sin(a + da) * rr))
        verts = bl + [(x, y - 0.01, z) for x, y, z in bl]
        bo = mesh_from(f'ac_blade{k}', verts, [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]], metal, 30)
        uv_fit(bo, M.rect('steel')); P.append(bo)  # (galvanised blades: they read against the dark floor)
    # the guard on the orifice lip: two flat wire rings, two crossed bars, the centre plate (black wire)
    GY = LT + 0.075  # (on the lip; the hub's top is the box version's 1.5)
    for rr, w_ in ((R0 + 0.01, 0.03), (0.3, 0.022)):
        g = lathe([(rr + w_ / 2, GY), (rr - w_ / 2, GY)], m=metal, seg=n, axis='y', name='ac_guardring', cap=False)
        uv_fit(g, M.rect('black')); P.append(g)
    for k in range(2):
        a = math.pi / 4 + k * math.pi / 2
        g = box((2 * R0 + 0.04, 0.012, 0.018), (0, GY - 0.004 - 0.003 * k, 0), metal, rot=(0, -a, 0), name='ac_bar')  # (one under the other)
        uv_fit(g, M.rect('black')); P.append(g)
    hub = cyl(0.07, 0.02, (0, 1.49, 0), metal, axis='y', seg=8, name='ac_hub'); uv_fit(hub, M.rect('black')); P.append(hub)
    # the service end: line set out of the corner (insulated suction line + bare liquid line), down into the roof
    for zz, rr, reg in ((0.36, 0.03, 'foam'), (0.48, 0.013, 'copper')):
        xo = 0.968 - rr  # out of the panel, a rounded elbow, down into the roof
        pth = [(0.88, 0.4, zz), (xo - 0.07, 0.4, zz), (xo - 0.02, 0.385, zz), (xo, 0.335, zz), (xo, 0.002, zz)]  # (bend wider than the foam)
        o = sweep(pth, rr, metal, seg=6, name='ac_line'); uv_fit(o, M.rect(reg)); P.append(o)
    o = box((0.07, 0.24, 0.18), (0.955, 0.84, -0.4), metal, name='ac_disconnect'); uv_fit(o, M.rect('steel')); P.append(o)
    o = box((0.025, 0.1, 0.03), (0.985, 0.86, -0.4), metal, rot=(0.5, 0, 0), name='ac_lever'); uv_fit(o, M.rect('black')); P.append(o)
    o = sweep([(0.955, 0.72, -0.4), (0.955, 0.36, -0.36), (0.92, 0.3, -0.3)], 0.012, metal, seg=6, name='ac_conduit'); uv_fit(o, M.rect('steel')); P.append(o)
    # lod1: the cabinet box (coil + service faces printed), the lid, the dark fan disc with its guard printed on
    Q = []
    c1 = box((2.0, 1.44, 1.4), (0, 0.72, 0), paint, name='ac1_body')
    def lid1(v):
        p_noise(0xd6d2c8, 0.05, 29)(v)
        h, w = v.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]; d = np.hypot((xx + 0.5 - w / 2) / (w / 2) * 1.0, (yy + 0.5 - h / 2) / (h / 2) * 0.7)
        v[d < 0.78] = hexrgb(0x1c1e22); v[(d > 0.5) & (d < 0.56)] = hexrgb(0x55595e); v[(d > 0.25) & (d < 0.3)] = hexrgb(0x55595e)
    A2 = None
    map_groups(c1, lambda gn, gc: side_of(gn), {
        '-z': (A.rect('coil_long'), 'decal', (0, 0.72, -0.7), (2.0, 1.44), '-z'), '+z': (A.rect('coil_long'), 'decal', (0, 0.72, 0.7), (2.0, 1.44), '+z'),
        '-x': (A.rect('coil_end'), 'decal', (-1, 0.72, 0), (1.4, 1.44), '-x'), '+x': (A.rect('service'), 'decal', (1, 0.72, 0), (1.4, 1.44), '+x'),
        '+y': (A.rect('lid'), 'decal', (0, 0, 0), (2.0, 1.4), '+y'), '-y': (A.rect('paint'), 'fit')}); Q.append(c1)
    fan = lathe([(0.56, 1.43), (0.56, 1.5), (0.0, 1.5)], m=paint, seg=8, axis='y', name='ac1_fan', cap=False)
    uv_fit(fan, A.rect('dark')); Q.append(fan)
    env = ((-1.0, 0.0, -0.7), (1.0, 1.5, 0.7))
    return finish_prop('p_acunit', P, Q, {'id': 'acunit', 'lod': 45, 'tint': False}, env, ao_dist=0.25), [
        ('front', (1.2, 1.9, -2.6), (0, 0.8, 0), 35), ('service', (2.6, 1.3, 0.8), (0.9, 0.6, 0), 35),
        ('top', (0.4, 3.0, -1.0), (0, 1.4, 0), 35), ('lines', (1.8, 0.6, -0.4), (0.95, 0.4, 0.2), 35)]


# ------------------------------------------------------------ p_cone
def build_cone():
    """cones() map.js:1525: base 0.6 x 0.12 x 0.6, cone 0.38 x 0.7 up to y 0.8, white band 0.43-0.57"""
    A = Atlas('cn_atlas', 64, 64)
    H = 0.8
    def body(v):  # by height: orange, the reflective collar (white, a faint prism grid), orange to the tip
        h, w = v.shape[:2]; r = np.random.default_rng(31)
        v[:] = hexrgb(0xff6a12) * (0.95 + 0.05 * r.random((h, w, 1)))
        r0, r1 = int(h * (1 - 0.57 / H)), int(h * (1 - 0.43 / H))
        v[r0:r1] = hexrgb(0xf2f4f6); v[r0:r1:2, ::2] = hexrgb(0xdadfe6)
        v[int(h * (1 - 0.12 / H)):] *= 0.85
    A.add('body', 0, 0, 32, 64, body)
    A.add('rubber', 32, 0, 32, 16, p_noise(0x26282c, 0.12, 32, cells=4))
    plastic = mat('cn_plastic', 0xffffff, rough=0.32, clearcoat=0.5, tex=A.image())
    P = []
    c = 0.05  # the base's cut corners
    out = [(0.3, -0.3 + c), (0.3, 0.3 - c), (0.3 - c, 0.3), (-0.3 + c, 0.3), (-0.3, 0.3 - c), (-0.3, -0.3 + c), (-0.3 + c, -0.3), (0.3 - c, -0.3)]
    base = prism('cn_base', out, 0.0, 0.038, plastic, 30)
    uv_fit(base, A.rect('rubber'))
    P.append(base)
    boss = lathe([(0.25, 0.03), (0.248, 0.058), (0.212, 0.088), (0.196, 0.11)], m=plastic, seg=16, axis='y', name='cn_boss', cap=False)
    uv_fit(boss, A.rect('rubber')); P.append(boss)
    rr = lambda y: 0.19 + (0.042 - 0.19) * (y - 0.105) / (0.775 - 0.105)
    prof = [(0.199, 0.1), (0.19, 0.105), (rr(0.43), 0.43), (rr(0.43) + 0.003, 0.4305), (rr(0.57) + 0.003, 0.5695), (rr(0.57), 0.57), (0.042, 0.775), (0.03, 0.792), (0.0, H)]
    cone = lathe(prof, m=plastic, seg=16, axis='y', name='cn_cone', cap=False)
    uv_lathe(cone, A.rect('body'), 0.0, H); P.append(cone)
    Q = []
    b1 = box((0.6, 0.06, 0.6), (0, 0.03, 0), plastic, name='cn1_base')
    uv_fit(b1, A.rect('rubber')); Q.append(b1)
    c1 = lathe([(0.2, 0.05), (rr(0.43), 0.43), (rr(0.57), 0.57), (0.0, H)], m=plastic, seg=6, axis='y', name='cn1_cone', cap=False)
    uv_lathe(c1, A.rect('body'), 0.0, H); Q.append(c1)
    env = ((-0.3, 0.0, -0.3), (0.3, H, 0.3))
    return finish_prop('p_cone', P, Q, {'id': 'cone', 'lod': 35, 'tint': False}, env, ao_dist=0.15), [
        ('three', (0.9, 0.9, -1.2), (0, 0.35, 0), 35), ('top', (0.2, 1.6, -0.5), (0, 0.4, 0), 35), ('low', (0.8, 0.12, -0.9), (0, 0.3, 0), 35)]


# ------------------------------------------------------------ p_barrier
def build_barrier():
    """barrier() map.js:1661 (+ Jankburg's jersey blocks): 3 x 1.05 x 0.7 along x. the New Jersey profile (vertical
    lip, 55 degree slope, 84 degree face) scaled to the box, two forklift slots through the foot, a red/white band
    near the top on both faces, steel connector plates cast into the ends, a stencil"""
    A = Atlas('jb_atlas', 128, 128)
    L, H, HW = 3.0, 1.05, 0.35
    BAND = (0.66, 0.86)
    def face(text):
        def draw(v):
            h, w = v.shape[:2]; r = np.random.default_rng(len(text) + 41)
            p_noise(0xa3a19b, 0.09, 41 + len(text), cells=8, speck=0x7e7c76, speck_p=0.05)(v)
            y0, y1 = int(h * (1 - BAND[1] / H)), int(h * (1 - BAND[0] / H))
            yy, xx = np.mgrid[y0:y1, 0:w]
            v[y0:y1] = np.where((((xx + (yy - y0)) // 6) % 2 == 0)[:, :, None], hexrgb(0xe8202a), hexrgb(0xf4f2ee))
            v[y0:y1] *= (0.92 + 0.08 * r.random((y1 - y0, w, 1)))
            for k in range(14):  # chips and scuffs
                cx, cy = r.integers(0, w), r.integers(0, h)
                v[cy:cy + 2, cx:cx + r.integers(1, 4)] = hexrgb(0x8a8882)
            if text:
                tx = (w - twidth(text)) // 2; ty = int(h * (1 - 0.6 / H))
                p_text(v, text, tx, ty, 1, 0x1a1a1c)
                for k in range(6):  # spray drips under some letters
                    dx = tx + r.integers(0, twidth(text)); v[ty + 7:ty + 7 + r.integers(1, 4), dx] = hexrgb(0x2a2a2c)
            v[int(h * (1 - 0.098 / H)):] *= 0.9  # the foot, scuffed darker
        return draw
    A.add('front', 0, 0, 128, 48, face('NO VAULTING'))
    A.add('back', 0, 48, 128, 48, face('JNK-DOT 042'))
    def end(v):
        p_noise(0xa3a19b, 0.09, 45, cells=4, speck=0x7e7c76, speck_p=0.05)(v)
        h, w = v.shape[:2]
        v[h // 4:h - 4, w // 2 - 3:w // 2 + 3] = hexrgb(0x4a4e54)  # the cast-in connector plate
        v[h // 4 + 2:h - 6, w // 2 - 1:w // 2 + 1] = hexrgb(0x2a2c30)
    A.add('end', 0, 96, 32, 32, end)
    def top(v):
        p_noise(0x9e9c96, 0.09, 46, cells=4)(v)
        h, w = v.shape[:2]
        for x in (w // 4, 3 * w // 4): v[h // 2 - 2:h // 2 + 2, x - 2:x + 2] = hexrgb(0x3a3c40)  # lifting anchors
    A.add('top', 32, 96, 64, 16, top)
    A.add('dark', 96, 96, 32, 32, p_noise(0x6a6862, 0.1, 47))
    conc = mat('jb_concrete', 0xffffff, rough=0.62, clearcoat=0.08, tex=A.image())
    prof = [(HW, 0.0), (HW, 0.098), (0.146, 0.426), (0.098, 1.0), (0.072, H)]
    sec = [(-z, y) for z, y in prof] + [(z, y) for z, y in prof[::-1]]  # (z, y) round the section
    sec = [(-HW, 0.0)] + [(-z, y) for z, y in prof[1:]] + [(z, y) for z, y in prof[::-1][:-1]] + [(HW, 0.0)]
    def slab(name, x0, x1, chamfer=0.03):
        verts = []
        for x in (x0, x1):
            verts += [(x, y, z) for z, y in sec]
        n = len(sec)
        faces = [list(range(n))[::-1], list(range(n, 2 * n))] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
        return mesh_from(name, verts, faces, conc, 25)
    body = slab('jb_body', -L / 2, L / 2)
    for sx in (-1, 1):  # forklift slots through the foot
        cutter = box((0.36, 0.08, 1.0), (sx * 0.72, 0.03, 0), conc, name='jb_slot')  # (top at 0.07: a clean lip above it)
        cut(body, cutter)
    for f in body.data.polygons: f.material_index = 0
    while len(body.data.materials) > 1: body.data.materials.pop(index=len(body.data.materials) - 1)
    bev = body.modifiers.new('bev', 'BEVEL'); bev.width = 0.01; bev.segments = 1; bev.limit_method = 'ANGLE'; bev.angle_limit = math.radians(30); bev.harden_normals = True
    apply_mods(body)
    def pick(gn, gc):
        if abs(gn[0]) > 0.7: return 'endR' if gn[0] > 0 else 'endL'
        if gn[1] > 0.8 and gc[1] > H - 0.01: return 'top'
        if gn[1] < -0.5: return 'dark'
        if gc[1] < 0.105 and abs(gn[2]) < 0.6: return 'dark'
        return 'front' if gc[2] < 0 else 'back'
    map_groups(body, pick, {'front': (A.rect('front'), 'decal', (0, H / 2, 0), (L, H), '-z'), 'back': (A.rect('back'), 'decal', (0, H / 2, 0), (L, H), '+z'),
                            'endR': (A.rect('end'), 'decal', (L / 2, H / 2, 0), (2 * HW, H), '+x'), 'endL': (A.rect('end'), 'decal', (-L / 2, H / 2, 0), (2 * HW, H), '-x'),
                            'end': (A.rect('end'), 'fit'), 'top': (A.rect('top'), 'decal', (0, H, 0), (L, 0.15), '+y'), 'dark': (A.rect('dark'), 'fit')})
    P = [body]
    Q = []
    sec1 = [(-HW, 0.0), (-HW, 0.098), (-0.12, 0.45), (-0.072, H), (0.072, H), (0.12, 0.45), (HW, 0.098), (HW, 0.0)]
    verts = [(x, y, z) for x in (-L / 2, L / 2) for z, y in sec1]
    n = len(sec1)
    faces = [list(range(n))[::-1], list(range(n, 2 * n))] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
    b1 = mesh_from('jb1_body', verts, faces, conc, 25)
    map_groups(b1, pick, {'front': (A.rect('front'), 'decal', (0, H / 2, 0), (L, H), '-z'), 'back': (A.rect('back'), 'decal', (0, H / 2, 0), (L, H), '+z'),
                            'endR': (A.rect('end'), 'decal', (L / 2, H / 2, 0), (2 * HW, H), '+x'), 'endL': (A.rect('end'), 'decal', (-L / 2, H / 2, 0), (2 * HW, H), '-x'),
                          'end': (A.rect('end'), 'fit'), 'top': (A.rect('top'), 'decal', (0, H, 0), (L, 0.15), '+y'), 'dark': (A.rect('dark'), 'fit')})
    Q.append(b1)
    env = ((-L / 2, 0.0, -HW), (L / 2, H, HW))
    return finish_prop('p_barrier', P, Q, {'id': 'barrier', 'lod': 50, 'tint': False}, env, ao_dist=0.2), [
        ('front', (1.6, 1.2, -2.6), (0, 0.5, 0), 35), ('end', (2.6, 0.8, -1.2), (1.3, 0.45, 0), 35), ('low', (0.9, 0.25, -1.6), (0.7, 0.1, 0), 35)]


# ------------------------------------------------------------ p_watertower
def build_watertower():
    """waterTower() map.js:175: legs 0.3 x 5 at (+-1.3, +-1.3), deck 3.6 x 0.3 at 5.2, tank 3.2 x 3.4 at 7, roof 2.4 x 0.4
    at 8.9. the city rooftop tank: cedar staves held by iron hoops (closer at the bottom, where the pressure is), a
    shallow cone roof with a hatch and a finial, a red-oxide steel stand with X rods, a ladder up the +x side"""
    T0, T1 = 5.35, 8.7
    rt = lambda y: 1.6 + (1.555 - 1.6) * (y - T0) / (T1 - T0)  # the tank tapers a little (staves are pulled in at the top)
    HOOPS = [5.48, 5.74, 6.04, 6.38, 6.78, 7.24, 7.78, 8.4]
    A = Atlas('wt_wood_atlas', 256, 128)
    def staves(v):  # u = round the tank (2 px a stave), v = up it: grain, joints, iron hoops, water streaks
        h, w = v.shape[:2]; r = np.random.default_rng(51)
        for x in range(0, w, 2): v[:, x:x + 2] = hexrgb(0xb0703e) * (0.86 + 0.22 * r.random())
        v[:, ::2] *= 0.8
        v[:] *= (0.93 + 0.07 * r.random((h, w, 1)))
        for k in range(10):  # rusty water streaks running down from the hoops
            x = r.integers(0, w); y0 = r.integers(0, h // 2)
            v[y0:y0 + r.integers(6, 20), x] *= 0.75
        for hy in HOOPS:
            row = int(round(h * (1 - (hy - T0) / (T1 - T0))))
            v[max(0, row - 1):row + 1] = hexrgb(0x2a2a2e); v[max(0, row - 2)] = hexrgb(0x5c5e64)
        v[:2] = hexrgb(0x2a2a2e)
        # NOT A HOT TUB, sprayed on between two hoops at the front (u runs leftwards as you face it: paint it mirrored)
        t = 'NOT A HOT TUB'; tw = twidth(t)
        buf = np.zeros((7, tw, 3), np.float32); text_px(buf, t, 0, 0, 1, 0xffffff)
        mask = buf.sum(axis=2)[:, ::-1] > 0
        x0 = int(w * 0.75) - tw // 2; r0 = int(round(h * (1 - (7.19 - T0) / (T1 - T0))))
        sub = v[r0:r0 + 7, x0:x0 + tw]; sub[mask] = hexrgb(0xf2efe6) * (0.9 + 0.1 * r.random((int(mask.sum()), 1)))
    A.add('staves', 0, 0, 256, 64, staves)
    def deck(v):  # planks across x, gaps, a few nail heads
        h, w = v.shape[:2]; r = np.random.default_rng(52)
        for y in range(0, h, 4): v[y:y + 4] = hexrgb(0x8a6440) * (0.85 + 0.2 * r.random())
        v[::4] = hexrgb(0x3a2a1c)
        v[:] *= (0.92 + 0.08 * r.random((h, w, 1)))
    A.add('deck', 0, 64, 64, 64, deck)
    def roof(v):  # tar paper laps round the cone (by height: the v of a lathe), a little moss green
        h, w = v.shape[:2]; r = np.random.default_rng(53)
        p_noise(0x3e4a44, 0.12, 53, cells=6)(v)
        for y in range(2, h, 5): v[y] *= 0.7
    A.add('roof', 64, 64, 32, 32, roof)
    A.add('wood', 96, 64, 32, 32, p_noise(0x7a5838, 0.1, 55, cells=4))
    wood = mat('wt_wood', 0xffffff, rough=0.5, clearcoat=0.25, tex=A.image())
    S = Atlas('wt_steel_atlas', 32, 32)
    S.add('oxide', 0, 0, 16, 16, p_noise(0x9a3422, 0.1, 56, cells=4, speck=0x5a1e14, speck_p=0.06))
    S.add('galv', 16, 0, 16, 16, p_noise(0x8a9199, 0.1, 57, cells=4))
    S.add('iron', 0, 16, 16, 16, p_noise(0x2c2c30, 0.12, 58))
    S.add('pipe', 16, 16, 16, 16, p_noise(0x5a6068, 0.1, 59))
    steel = mat('wt_steel', 0xffffff, rough=0.38, metal=0.35, clearcoat=0.35, tex=S.image())
    P = []
    # the stand: four legs on base plates, X rods on every side, two beams under the deck
    for sx in (-1, 1):
        for sz in (-1, 1):
            o = box((0.24, 5.07, 0.24), (sx * 1.3, 2.545, sz * 1.3), steel, name='wt_leg'); uv_fit(o, S.rect('oxide')); P.append(o)
            o = box((0.38, 0.03, 0.38), (sx * 1.3, 0.015, sz * 1.3), steel, name='wt_plate'); uv_fit(o, S.rect('oxide')); P.append(o)
    for side in range(4):  # rods corner to corner on each face, from gusset height to under the beams
        for d in (1, -1):
            if side < 2:
                z = (-1.3, 1.3)[side]; a, b = (-1.3 * d, 0.45, z), (1.3 * d, 4.78, z)
            else:
                x = (-1.3, 1.3)[side - 2]; a, b = (x, 0.45, -1.3 * d), (x, 4.78, 1.3 * d)
            o = rod(a, b, 0.022, steel, seg=6, name='wt_rod'); uv_fit(o, S.rect('iron')); P.append(o)
    for sz in (-1, 1):
        o = box((3.54, 0.16, 0.2), (-0.03, 5.14, sz * 1.3), steel, name='wt_beam'); uv_fit(o, S.rect('oxide')); P.append(o)
    dk = box((3.54, 0.14, 3.6), (-0.03, 5.28, 0), wood, bev=0.02, seg=1, name='wt_deck')  # x -1.8..1.74 (the ladder passes the +x edge)
    apply_mods(dk)
    map_groups(dk, lambda gn, gc: 'top' if abs(gn[1]) > 0.9 else 'edge', {'top': (A.rect('deck'), 'decal', (-0.03, 0, 0), (3.54, 3.6), '+y'), 'edge': (A.rect('wood'), 'fit')})
    P.append(dk)
    # the tank: staves (20 sides, the hoops painted on), cast lugs where each hoop is drawn tight
    tank = lathe([(1.6, T0 - 0.02), (rt(T1 - 0.06), T1 - 0.06), (rt(T1) - 0.01, T1 + 0.01)], m=wood, seg=20, axis='y', name='wt_tank', cap=False)
    uv_lathe(tank, A.rect('staves'), T0, T1); P.append(tank)
    for i, hy in enumerate(HOOPS):
        a = math.radians(200 + 47 * i)  # (staggered round the tank, the way coopers do it)
        rr = rt(hy) - 0.004  # (deep enough to reach the 20-gon's flat facets)
        o = box((0.07, 0.07, 0.12), (math.cos(a) * rr, hy, math.sin(a) * rr), steel, rot=(0, -a, 0), name='wt_lug'); uv_fit(o, S.rect('iron')); P.append(o)
    # the roof: a shallow cone of tar paper, a hatch by the ladder, the finial
    roof = lathe([(1.64, T1 - 0.05), (1.655, T1 + 0.01), (0.15, 9.03), (0.08, 9.05), (0.0, 9.1)], m=wood, seg=20, axis='y', name='wt_roof', cap=True)
    uv_lathe(roof, A.rect('roof'), T1 - 0.05, 9.1); P.append(roof)
    hy_ = T1 + 0.01 + (1.655 - 1.0) / (1.655 - 0.15) * (9.03 - T1 - 0.01)
    o = box((0.42, 0.12, 0.4), (1.0, hy_ + 0.0, 0.0), wood, rot=(0, 0, -math.atan2(9.03 - T1 - 0.01, 1.505)), name='wt_hatch'); uv_fit(o, A.rect('wood')); P.append(o)
    # the ladder up the +x side (rails 1.76..1.8: the box version's edge), rungs every 0.4 m, brackets to a leg and the tank
    for sz in (-1, 1):
        o = box((0.04, 8.82, 0.03), (1.78, 4.41, sz * 0.2), steel, name='wt_rail'); uv_fit(o, S.rect('galv')); P.append(o)
    for i in range(22):
        y = 0.3 + 0.4 * i
        o = box((0.03, 0.03, 0.4), (1.78, y, 0), steel, name='wt_rung'); uv_fit(o, S.rect('galv')); P.append(o)
    for y, x0 in ((1.6, 1.42), (4.2, 1.42), (6.3, rt(6.3) - 0.02), (8.1, rt(8.1) - 0.02)):
        o = box((1.77 - x0, 0.04, 0.04), ((x0 + 1.77) / 2, y, 0.2 if y < 5 else -0.2), steel, name='wt_bracket'); uv_fit(o, S.rect('galv')); P.append(o)
    # pipes: the overflow down the front, the feed down through the deck into the roof
    o = sweep([(0.3, 8.35, -rt(8.35) + 0.09), (0.3, 8.35, -rt(8.35) - 0.08), (0.3, 8.22, -rt(8.35) - 0.12), (0.3, 5.32, -rt(8.35) - 0.12)], 0.045, steel, seg=6, name='wt_overflow')
    uv_fit(o, S.rect('pipe')); P.append(o)
    o = cyl(0.08, 5.26, (0.55, 2.67, 0.45), steel, axis='y', seg=8, name='wt_feed'); uv_fit(o, S.rect('pipe')); P.append(o)  # (its foot inside the boot)
    o = lathe([(0.15, 0.0), (0.15, 0.025), (0.086, 0.1), (0.068, 0.17)], (0.55, 0, 0.45), steel, seg=8, axis='y', name='wt_boot', cap=False)  # the roof boot hugs the pipe
    uv_fit(o, S.rect('iron')); P.append(o)
    # lod1: an 8-sided tank + cone, the deck, the legs, the ladder rails
    Q = []
    o = lathe([(1.6, T0 - 0.02), (1.555, T1 + 0.01)], m=wood, seg=8, axis='y', name='wt1_tank', cap=False); uv_lathe(o, A.rect('staves'), T0, T1); Q.append(o)
    o = lathe([(1.655, T1 - 0.02), (0.0, 9.1)], m=wood, seg=8, axis='y', name='wt1_roof', cap=True); uv_lathe(o, A.rect('roof'), T1 - 0.05, 9.1); Q.append(o)
    o = box((3.54, 0.3, 3.6), (-0.03, 5.2, 0), wood, name='wt1_deck')
    map_groups(o, lambda gn, gc: 'top' if abs(gn[1]) > 0.9 else 'edge', {'top': (A.rect('deck'), 'decal', (-0.03, 0, 0), (3.54, 3.6), '+y'), 'edge': (A.rect('wood'), 'fit')}); Q.append(o)
    for sx in (-1, 1):
        for sz in (-1, 1):
            o = box((0.26, 5.1, 0.26), (sx * 1.3, 2.55, sz * 1.3), steel, name='wt1_leg'); uv_fit(o, S.rect('oxide')); Q.append(o)
    o = box((0.04, 8.82, 0.43), (1.78, 4.41, 0), steel, name='wt1_ladder'); uv_fit(o, S.rect('galv')); Q.append(o)
    env = ((-1.8, 0.0, -1.8), (1.8, 9.1, 1.8))
    return finish_prop('p_watertower', P, Q, {'id': 'watertower', 'lod': 80, 'tint': False}, env, ao_dist=0.5), [
        ('whole', (7.5, 6.5, -9.0), (0, 4.6, 0), 35), ('tank', (3.8, 8.4, -4.2), (0, 7.2, 0), 35),
        ('stand', (3.5, 2.0, -4.5), (0, 2.6, 0), 35), ('ladder', (4.2, 5.6, 1.6), (1.6, 5.5, 0), 35)]


# ------------------------------------------------------------ p_billboard + p_billboard_post
def bb_atlas():
    A = Atlas('bb_atlas', 128, 80)  # (no two rects overlap: a painter only touches its own)
    A.add('frame', 0, 0, 32, 32, p_noise(0x26304a, 0.08, 61, cells=4))  # navy enamel
    def grate(v):  # catwalk grating seen from above: bars across, a stringer every few
        h, w = v.shape[:2]
        v[:] = hexrgb(0x2a2e34); v[:, ::2] = hexrgb(0x6a7078); v[::4] = hexrgb(0x7a8088)
    A.add('grate', 0, 32, 128, 10, grate)
    A.add('yellow', 32, 0, 16, 16, p_noise(0xffc21a, 0.06, 62))
    A.add('steel', 32, 16, 16, 16, p_noise(0x8a9199, 0.1, 63))
    A.add('lamp', 48, 16, 16, 16, p_noise(0x3a3e44, 0.1, 64))
    def plate(v):  # the operator's plate on the frame
        v[:] = hexrgb(0xf2f0ea); v[0] = v[-1] = hexrgb(0x26304a)
        p_text(v, 'JANK OUTDOOR', 2, 2, 1, 0x26304a)
    A.add('plate', 48, 0, 80, 11, plate)
    def bill(v):  # a POST NO BILLS stencil, with a bill posted right over it (his name is Bill)
        h, w = v.shape[:2]
        p_noise(0x26304a, 0.08, 61, cells=4)(v)  # (the post's own navy: the stencil is sprayed on it)
        p_text(v, 'POST', 2, 2, 1, 0xe8e4da); p_text(v, 'NO', 2, 11, 1, 0xe8e4da)
        v[8:30, 15:31] = hexrgb(0xf4f0e4)
        v[12:16, 20:26] = hexrgb(0x141414); v[13, 21] = v[13, 24] = hexrgb(0xf4f0e4)  # Bill's face, cheerful
        v[17, 20:26] = hexrgb(0x141414); v[16, 20] = v[16, 25] = hexrgb(0x141414)
        v[21:23, 17:29] = hexrgb(0xd0102a); v[25:27, 17:29] = hexrgb(0x2a66e8)
    A.add('bill', 0, 44, 32, 32, bill)
    return A


def build_billboard():
    """the face of billboard() map.js:181 (and adBoard() map.js:1004): the picture stays the game's box (x +-6,
    y 5..10, z +-0.2 at the reference), the model frames it. a navy frame lip over the picture's edge, the catwalk
    (grating, toe board, outriggers back under the picture), a safety-yellow rail, four gooseneck lamps (glow) aimed
    at the picture. the posts are p_billboard_post (each post box fits its own)"""
    A = bb_atlas()
    steel = mat('bb_steel', 0xffffff, rough=0.38, metal=0.3, clearcoat=0.35, tex=A.image())
    glow = mat('glow', 0xfff2c8, rough=0.3, emit=0xfff2c8, strength=1.0)
    P = []
    lip = frame_ring('bb_lip', (-6, 5.0, 6, 10.0), (-5.75, 5.14, 5.75, 9.75), -0.3, -0.19, steel)
    bevel(lip, 0.02, 1, 40); apply_mods(lip); uv_fit(lip, A.rect('frame')); P.append(lip)
    o = box((1.0, 0.09, 0.016), (0, 5.07, -0.304), steel, name='bb_plate'); uv_decal(o, A.rect('plate'), (0, 5.07, 0), (1.0, 0.09), '-z'); P.append(o)
    deck = box((12.0, 0.1, 0.86), (0, 4.85, -0.67), steel, name='bb_deck')
    map_groups(deck, lambda gn, gc: 'grate' if abs(gn[1]) > 0.9 else 'edge', {'grate': (A.rect('grate'), 'decal', (0, 0, -0.67), (12.0, 0.86), '+y'), 'edge': (A.rect('steel'), 'fit')})
    P.append(deck)
    o = box((11.99, 0.1, 0.02), (0, 4.945, -1.042), steel, name='bb_toe'); uv_fit(o, A.rect('yellow')); P.append(o)  # (just behind the rail posts)
    LX = (-4.5, -1.5, 1.5, 4.5)
    for x in LX:  # outriggers: from the catwalk's front back under the picture (they carry it)
        o = box((0.08, 0.16, 1.295), (x, 4.885, -0.4475), steel, name='bb_outrigger'); uv_fit(o, A.rect('steel')); P.append(o)
    RZ = -1.075
    for x in (-5.965, -4.0, -2.0, 0.0, 2.0, 4.0, 5.965):
        o = box((0.045, 1.0, 0.045), (x, 5.4, RZ), steel, name='bb_post'); uv_fit(o, A.rect('yellow')); P.append(o)
    for y, t in ((5.9, 0.05), (5.42, 0.04)):
        o = box((11.995, t, t), (0, y, RZ), steel, name='bb_rail'); uv_fit(o, A.rect('yellow')); P.append(o)
        for sx in (-1, 1):
            o = box((t * 0.8, t * 0.8, 0.8), (sx * 5.965, y, -0.69), steel, name='bb_endrail'); uv_fit(o, A.rect('yellow')); P.append(o)
    for sx in (-1, 1):
        o = box((0.045, 1.0, 0.045), (sx * 5.965, 5.4, -0.3), steel, name='bb_endpost'); uv_fit(o, A.rect('yellow')); P.append(o)
    for x in LX:  # goosenecks up off the outriggers, the lamp heads aimed back and up at the picture
        o = sweep([(x, 4.9, -1.0), (x, 5.55, -1.03), (x, 6.0, -0.94), (x, 6.16, -0.8)], 0.024, steel, seg=4, name='bb_neck'); uv_fit(o, A.rect('lamp')); P.append(o)
        hc = (x, 6.22, -0.7)
        hs = box((0.36, 0.11, 0.26), hc, steel, name='bb_lamp'); uv_fit(hs, A.rect('lamp'))
        ln = box((0.3, 0.075, 0.012), (x, 6.22, -0.7 + 0.134), glow, name='bb_lens')
        for o in (hs, ln): turn_obj(o, 'x', -0.7, hc); P.append(o)
    Q = []
    o = frame_ring('bb1_lip', (-6, 5.0, 6, 10.0), (-5.75, 5.14, 5.75, 9.75), -0.3, -0.19, steel); uv_fit(o, A.rect('frame')); Q.append(o)
    o = box((12.0, 0.1, 0.86), (0, 4.85, -0.67), steel, name='bb1_deck')
    map_groups(o, lambda gn, gc: 'grate' if abs(gn[1]) > 0.9 else 'edge', {'grate': (A.rect('grate'), 'decal', (0, 0, -0.67), (12.0, 0.86), '+y'), 'edge': (A.rect('steel'), 'fit')}); Q.append(o)
    o = box((11.99, 1.0, 0.04), (0, 5.405, -1.07), steel, name='bb1_rail'); uv_fit(o, A.rect('yellow')); Q.append(o)
    o = box((0.08, 0.16, 1.295), (0, 4.885, -0.4475), steel, name='bb1_outrigger'); uv_fit(o, A.rect('steel')); Q.append(o)
    # (no lamps far away: a pixel or two at 90 m, and one material fewer for every far copy)
    env = ((-6.0, 4.8, -1.1), (6.0, 10.0, 0.2))
    return finish_prop('p_billboard', P, Q, {'id': 'billboard', 'lod': 90, 'tint': False, 'picture': [[-6, 5, -0.2], [6, 10, 0.2]]}, env, ao_dist=0.4), [
        ('whole', (9.0, 9.5, -14.0), (0, 7.2, 0), 35), ('catwalk', (3.5, 6.8, -3.4), (2.0, 5.4, -0.6), 35),
        ('lamp', (-2.6, 6.9, -2.0), (-1.5, 6.1, -0.7), 35), ('end', (8.0, 6.0, -2.0), (5.8, 6.5, -0.5), 35)]


def build_billboard_post():
    """one billboard leg (billboard() posts 0.3 x 6, adBoard() 0.4 x 6): a steel pipe column on a bolted base plate
    with gussets. the top goes up into the frame / picture. a POST NO BILLS stencil, with a bill posted on it"""
    A = bb_atlas()
    steel = mat('bb_steel', 0xffffff, rough=0.38, metal=0.3, clearcoat=0.35, tex=A.image())
    P = []
    o = box((0.3, 0.03, 0.3), (0, 0.015, 0), steel, bev=0.004, seg=1, name='bp_plate'); apply_mods(o); uv_fit(o, A.rect('frame')); P.append(o)
    for sx in (-1, 1):
        for sz in (-1, 1):
            o = box((0.035, 0.03, 0.035), (sx * 0.112, 0.04, sz * 0.112), steel, name='bp_nut'); uv_fit(o, A.rect('lamp')); P.append(o)
    col = lathe([(0.105, 0.02), (0.105, 6.0)], m=steel, seg=12, axis='y', name='bp_column', cap=False)
    uv_fit(col, A.rect('frame')); P.append(col)
    for k in range(4):  # gussets on the four sides (they stay inside the plate)
        a = k * math.pi / 2
        tri = [(0.098, 0.028), (0.148, 0.028), (0.098, 0.14)]
        o = side([(-r_, y) for r_, y in tri], 0.012, (0, 0, 0), steel, name='bp_gusset')
        apply_mods(o); o.data.transform(Matrix.Rotation(-math.pi / 2 - a, 4, 'Z')); uv_fit(o, A.rect('frame')); P.append(o)
    b = ring_strip('bp_bill', 0.107, 1.5, 1.82, math.radians(-140), math.radians(-40), 4, steel, depth=0.006)
    uv_lathe(b, A.rect('bill'), 1.5, 1.82, a0=math.radians(-40), a1=math.radians(-140)); P.append(b)
    Q = []
    o = lathe([(0.108, 0.0), (0.108, 6.0)], m=steel, seg=6, axis='y', name='bp1_column', cap=False); uv_fit(o, A.rect('frame')); Q.append(o)
    o = box((0.3, 0.05, 0.3), (0, 0.025, 0), steel, name='bp1_plate'); uv_fit(o, A.rect('frame')); Q.append(o)
    env = ((-0.15, 0.0, -0.15), (0.15, 6.0, 0.15))
    return finish_prop('p_billboard_post', P, Q, {'id': 'billboard_post', 'lod': 60, 'tint': False}, env, ao_dist=0.2), [
        ('base', (0.7, 0.6, -0.9), (0, 0.15, 0), 35), ('bill', (0.25, 1.7, -0.8), (0, 1.66, 0), 35)]


# ------------------------------------------------------------ p_vending
def tint_faces(o, size, centre):
    """tint parts: every face side gets the whole 0..1 square straight-on (a picture tint like the FUN ZONE ad then
    lands whole on each side of the machine)"""
    cx, cy, cz = centre; w, h, d = size
    spec = {'-z': ((0, 0, 1, 1), 'decal', centre, (w, h), '-z'), '+z': ((0, 0, 1, 1), 'decal', centre, (w, h), '+z'),
            '-x': ((0, 0, 1, 1), 'decal', centre, (d, h), '-x'), '+x': ((0, 0, 1, 1), 'decal', centre, (d, h), '+x'),
            '+y': ((0, 0, 1, 1), 'decal', centre, (w, d), '+y'), '-y': ((0, 0, 1, 1), 'decal', centre, (w, d), '-y'), None: ((0.4, 0.4, 0.6, 0.6), 'fit')}
    return map_groups(o, lambda gn, gc: side_of(gn, 0.5), spec)


def build_vending():
    """vending() jankburg.js:505: cabinet 1.2 x 2 x 0.9 (front -z), lit panel 0.9 x 1.3 x 0.05 at y 1.25 sticking out
    to z -0.485. a 90s drinks machine for JANK COLA (the city's own soda, off the billboards): bulged lit front, a column
    of lit selection buttons, coin plate, bill slot, coin cup, the delivery flap, KICK HERE (it's how Neon Market
    machines pay out), a NO TILT warning on the side. the cabinet is `tint`: each machine gets its panel's colour"""
    T = Atlas('vd_tint_atlas', 32, 32)
    T.add('paint', 0, 0, 32, 32, p_noise(0xf6f6f6, 0.035, 71, cells=4))
    tint = mat('tint', 0xffffff, rough=0.3, clearcoat=0.6, tex=T.image())
    G = Atlas('vd_glow_atlas', 128, 160)
    def front_art(v):  # 96 x 160 px for 0.76 x 1.28 m: JANK / the bottle / COLA / ICE COLD on cherry red, a zigzag
        h, w = v.shape[:2]; r = np.random.default_rng(72)
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.hypot((xx - w / 2) / (w / 2), (yy - h * 0.48) / (h / 2))
        v[:] = hexrgb(0xb80c24)[None, None] * (0.72 + 0.4 * np.clip(1 - d, 0, 1))[:, :, None]
        for k in range(70):  # bubbles
            v[r.integers(0, h), r.integers(0, w)] = hexrgb(0xff8a9a)
        for x in range(w):  # the jank zigzag behind the bottle
            t = (x % 16) / 16; y0 = int(h * 0.56 + 9 * (abs(t - 0.5) * 4 - 1))
            v[y0:y0 + 6, x] = hexrgb(0xfff4f4); v[y0 + 6:y0 + 8, x] = hexrgb(0xff4fd8)
        cx = w // 2  # the bottle: cap, neck, shoulders, body, label
        prof = [(36, 5), (39, 4), (54, 4), (58, 7), (62, 11), (66, 13), (88, 13), (92, 11), (98, 13), (114, 13), (118, 11)]
        def hw_at(y):
            for (y0, a), (y1, b) in zip(prof, prof[1:]):
                if y0 <= y <= y1: return a + (b - a) * (y - y0) / max(1, y1 - y0)
            return None
        for y in range(36, 119):
            hw = hw_at(y)
            if hw is None: continue
            x0, x1 = int(cx - hw), int(cx + hw) + 1
            v[y, x0:x1] = hexrgb(0x3a120a); v[y, x0] = v[y, x1 - 1] = hexrgb(0x1a0604)
            v[y, x0 + 3:x0 + 5] = hexrgb(0x8a4a2a)  # the glint down its side
        v[33:37, cx - 5:cx + 6] = hexrgb(0xd8dce2); v[33, cx - 5:cx + 6] = hexrgb(0xffffff)  # the cap
        v[76:90, cx - 13:cx + 14] = hexrgb(0xfff4f4); v[76, cx - 13:cx + 14] = v[89, cx - 13:cx + 14] = hexrgb(0xd0102a)
        p_text(v, 'JANK', cx - 11, 79, 1, 0xd0102a, bold=False)
        for dx, dy, c in ((2, 2, 0x5a0410), (0, 0, 0xffffff)):  # JANK on top, COLA under, comic drop shadows
            p_text(v, 'JANK', (w - twidth('JANK', 3)) // 2 + dx, 6 + dy, 3, c)
            p_text(v, 'COLA', (w - twidth('COLA', 3)) // 2 + dx, 122 + dy, 3, c)
        p_text(v, 'ICE COLD', (w - twidth('ICE COLD')) // 2, 150, 1, 0xffe14d)
    G.add('front', 0, 0, 96, 160, front_art)
    BUT = [('COLA', 0xd0102a, 0xffffff), ('DIET', 0xd8dce2, 0xd0102a), ('LIME', 0x22c43a, 0xffffff), ('GRAPE', 0x8a2ad4, 0xffffff),
           ('???', 0x18141c, 0xffe14d), ('SOLD OUT', 0x241014, 0xff3030)]
    for i, (t, bg, fg) in enumerate(BUT):
        def btn(v, t=t, bg=bg, fg=fg):
            v[:] = hexrgb(bg); v[0] = v[-1] = hexrgb(bg) * 0.6; v[:, 0] = v[:, -1] = hexrgb(bg) * 0.6
            if ' ' in t:
                a, b = t.split(' '); p_text(v, a, (32 - twidth(a)) // 2, 1, 1, fg); p_text(v, b, (32 - twidth(b)) // 2, 8, 1, fg)
            else: p_text(v, t, (32 - twidth(t)) // 2, 4, 1, fg)
        G.add(f'b{i}', 96, 16 * i, 32, 16, btn)
    G.add('edge', 96, 96, 32, 16, p_noise(0x8a0818, 0.08, 73))
    G.add('bcol', 96, 0, 32, 96)  # (all six buttons, for the far one)
    glow = mat('glow', 0xffffff, rough=0.3, emit=0xffffff, strength=1.0, tex=G.image(), emit_tex=True)
    K = Atlas('vd_trim_atlas', 64, 128)
    def chrome(v):  # the coin plate: brushed chrome, the slot, COIN, the return button
        h, w = v.shape[:2]; r = np.random.default_rng(74)
        v[:] = hexrgb(0xc4cad0) * (0.9 + 0.1 * r.random((h, 1, 1)))
        p_text(v, 'COIN', (w - twidth('COIN')) // 2, 3, 1, 0x30343a)
        v[12:24, 14:18] = hexrgb(0x101214); v[12:24, 13] = hexrgb(0xe8ecf0)
        px_disc(v, 25, 27, 3.2, 0x30343a); px_disc(v, 25, 27, 2.2, 0xe8202a)
    K.add('chrome', 0, 0, 32, 32, chrome)
    K.add('dark', 32, 0, 16, 16, p_noise(0x2a2c30, 0.08, 75))
    K.add('black', 48, 0, 16, 16, p_noise(0x141416, 0.1, 76))
    def bill(v):
        v[:] = hexrgb(0x26282c); v[6:9, 4:28] = hexrgb(0x08090a); v[7, 4:28] = hexrgb(0x3a3e44)
        v[11:13, 24:28] = hexrgb(0x39ff14)  # (the ready light)
    K.add('bill', 32, 16, 32, 16, bill)
    def flap(v):  # the delivery flap: smoked plastic, a highlight, PUSH
        h, w = v.shape[:2]
        v[:] = hexrgb(0x2e3238); v[1] = hexrgb(0x5a6068); v[-2:] = hexrgb(0x16181a)
        p_text(v, 'PUSH', (w - twidth('PUSH')) // 2, (h - 7) // 2, 1, 0xe8ecf0)
    K.add('flap', 0, 32, 64, 24, flap)
    def kick(v):  # KICK HERE (with the dent where everyone does)
        h, w = v.shape[:2]
        v[:] = hexrgb(0xffe14d); v[0] = v[-1] = hexrgb(0x141414); v[:, 0] = v[:, -1] = hexrgb(0x141414)
        p_text(v, 'KICK', (w - twidth('KICK')) // 2, 2, 1, 0x141414); p_text(v, 'HERE', (w - twidth('HERE')) // 2, 11, 1, 0xff00dc)
    K.add('kick', 0, 56, 32, 20, kick)
    def warn(v):  # the classic warning: a machine tipping onto a stick figure. NO TILT
        h, w = v.shape[:2]
        v[:] = hexrgb(0xf4f2ea); v[:9] = hexrgb(0xe8202a)
        p_text(v, 'NO', (w - twidth('NO')) // 2, 1, 1, 0xffffff)
        for k in range(14):  # the machine, tipping right
            x0 = 6 + k // 3; v[12 + k, x0:x0 + 8] = hexrgb(0x2a66e8)
        c = hexrgb(0x141414)
        px_disc(v, 22, 24, 2.0, 0x141414); v[26:32, 22] = c; v[28, 19:26] = c; v[32:34, 20] = c; v[32:34, 24] = c  # the victim
        p_text(v, 'TILT', (w - twidth('TILT')) // 2, h - 8, 1, 0x141414)
    K.add('warn', 32, 56, 32, 40, warn)
    def plate(v):  # the maker's plate on the back
        h, w = v.shape[:2]
        v[:] = hexrgb(0xdcdad2); v[0] = v[-1] = hexrgb(0x8a8c90); v[:, 0] = v[:, -1] = hexrgb(0x8a8c90)
        p_text(v, 'JANK COLA', (w - twidth('JANK COLA')) // 2, 2, 1, 0xd8101a, bold=True)
        p_text(v, 'NO REFUNDS', (w - twidth('NO REFUNDS')) // 2, 11, 1, 0x2a2c30)
    K.add('plate', 0, 96, 64, 20, plate)
    def vent(v):  # the fridge deck's vent: louvres, dust caught on them
        h, w = v.shape[:2]; r = np.random.default_rng(77)
        v[:] = hexrgb(0x1c1e22)
        for y in range(1, h - 1, 3): v[y] = hexrgb(0x50545c); v[y + 1] = hexrgb(0x0c0d0f)
        v[0] = v[-1] = hexrgb(0x3a3e44); v[:, 0] = v[:, -1] = hexrgb(0x3a3e44)
        v[r.random((h, w)) < 0.05] = hexrgb(0x6a6458)
    K.add('vent', 0, 116, 32, 12, vent)
    trim = mat('vd_trim', 0xffffff, rough=0.3, metal=0.3, clearcoat=0.5, tex=K.image())
    P = []
    cab = box((1.2, 1.94, 0.85), (0, 1.03, 0.025), tint, bev=0.015, seg=1, name='vd_cabinet')  # x +-0.6, y 0.06..2.0, z -0.4..0.45
    apply_mods(cab); tint_faces(cab, (1.2, 1.94, 0.85), (0, 1.03, 0.025)); P.append(cab)
    o = box((1.16, 0.065, 0.8), (0, 0.0325, 0.03), trim, name='vd_plinth'); uv_fit(o, K.rect('black')); P.append(o)
    door = box((1.16, 1.9, 0.045), (0, 1.03, -0.42), tint, bev=0.01, seg=1, name='vd_door')
    apply_mods(door); tint_faces(door, (1.16, 1.9, 0.045), (0, 1.03, -0.42)); P.append(door)
    X0, X1, Y0, Y1 = -0.24, 0.52, 0.62, 1.9  # (+x is the viewer's left: lit front left, buttons right, like the real ones)
    xc, hw = (X0 + X1) / 2, (X1 - X0) / 2
    nx = 6
    zf = lambda x: -0.452 - 0.033 * (1 - ((x - xc) / hw) ** 2)
    xs = [X0 + (X1 - X0) * i / nx for i in range(nx + 1)]
    verts = [(x, Y0, zf(x)) for x in xs] + [(x, Y1, zf(x)) for x in xs] + [(x, Y0, -0.43) for x in xs] + [(x, Y1, -0.43) for x in xs]
    n1 = nx + 1
    faces = []
    for i in range(nx):
        faces += [[i, i + 1, n1 + i + 1, n1 + i], [n1 + i, n1 + i + 1, 3 * n1 + i + 1, 3 * n1 + i], [2 * n1 + i, 2 * n1 + i + 1, i + 1, i]]
    faces += [[0, n1, 3 * n1, 2 * n1], [nx, 2 * n1 + nx, 3 * n1 + nx, n1 + nx]]
    lit = mesh_from('vd_lit', verts, faces, glow, 40)
    map_groups(lit, lambda gn, gc: 'front' if gn[2] < -0.8 else 'edge', {'front': (G.rect('front'), 'decal', (xc, (Y0 + Y1) / 2, 0), (X1 - X0, Y1 - Y0), '-z'), 'edge': (G.rect('edge'), 'fit')})
    P.append(lit)
    o = frame_ring('vd_bezel', (X0 - 0.03, Y0 - 0.03, X1 + 0.03, Y1 + 0.03), (X0 + 0.006, Y0 + 0.006, X1 - 0.006, Y1 - 0.006), -0.462, -0.43, trim)
    uv_fit(o, K.rect('dark')); P.append(o)
    o = box((0.25, 0.75, 0.012), (-0.41, 1.548, -0.444), trim, name='vd_btnplate'); uv_fit(o, K.rect('dark')); P.append(o)
    for i in range(6):
        y = 1.845 - i * 0.118
        b = box((0.2, 0.094, 0.02), (-0.41, y, -0.447), glow, name='vd_button')
        map_groups(b, lambda gn, gc: 'f' if gn[2] < -0.8 else 'e', {'f': (G.rect(f'b{i}'), 'decal', (-0.41, y, 0), (0.2, 0.094), '-z'), 'e': (G.rect(f'b{i}', inset=3), 'fit')})
        P.append(b)
    for nm, sz_, c_, reg in (('vd_coin', (0.2, 0.2, 0.016), (-0.41, 1.03, -0.448), 'chrome'), ('vd_bill', (0.17, 0.1, 0.03), (-0.41, 0.81, -0.452), 'bill'),
                             ('vd_cup', (0.13, 0.08, 0.05), (-0.41, 0.67, -0.455), 'black'), ('vd_kick', (0.17, 0.11, 0.008), (-0.41, 0.3, -0.444), 'kick')):
        o = box(sz_, c_, trim, name=nm)
        map_groups(o, lambda gn, gc: 'f' if gn[2] < -0.8 else 'e', {'f': (K.rect(reg), 'decal', c_, sz_[:2], '-z'), 'e': (K.rect('dark'), 'fit')})
        P.append(o)
    o = frame_ring('vd_port', (-0.2, 0.14, 0.47, 0.46), (-0.16, 0.18, 0.43, 0.42), -0.468, -0.43, trim); uv_fit(o, K.rect('dark')); P.append(o)
    o = box((0.59, 0.24, 0.01), (0.135, 0.3, -0.446), trim, rot=(-0.06, 0, 0), name='vd_flap')
    map_groups(o, lambda gn, gc: 'f' if gn[2] < -0.8 else 'e', {'f': (K.rect('flap'), 'decal', (0.135, 0.3, 0), (0.59, 0.24), '-z'), 'e': (K.rect('dark'), 'fit')}); P.append(o)
    o = box((0.006, 0.34, 0.24), (0.6, 1.36, 0.06), trim, name='vd_warn')
    map_groups(o, lambda gn, gc: 'f' if gn[0] > 0.8 else 'e', {'f': (K.rect('warn'), 'decal', (0.6, 1.36, 0.06), (0.24, 0.34), '+x'), 'e': (K.rect('dark'), 'fit')}); P.append(o)
    # the back (the free-standing ones get walked round): the fridge deck's vent and the maker's plate, 3 mm proud
    o = box((0.9, 0.3, 0.006), (0, 0.32, 0.45), trim, name='vd_vent')
    map_groups(o, lambda gn, gc: 'f' if gn[2] > 0.8 else 'e', {'f': (K.rect('vent'), 'decal', (0, 0.32, 0.45), (0.9, 0.3), '+z'), 'e': (K.rect('dark'), 'fit')}); P.append(o)
    o = box((0.32, 0.1, 0.006), (-0.3, 1.72, 0.45), trim, name='vd_plate')
    map_groups(o, lambda gn, gc: 'f' if gn[2] > 0.8 else 'e', {'f': (K.rect('plate'), 'decal', (-0.3, 1.72, 0.45), (0.32, 0.1), '+z'), 'e': (K.rect('dark'), 'fit')}); P.append(o)
    Q = []
    o = box((1.2, 2.0, 0.9), (0, 1.0, 0.0), tint, name='vd1_cabinet'); tint_faces(o, (1.2, 2.0, 0.9), (0, 1.0, 0.0)); Q.append(o)
    o = box((X1 - X0, Y1 - Y0, 0.035), (xc, (Y0 + Y1) / 2, -0.4675), glow, name='vd1_lit')
    map_groups(o, lambda gn, gc: 'front' if gn[2] < -0.8 else 'edge', {'front': (G.rect('front'), 'decal', (xc, (Y0 + Y1) / 2, 0), (X1 - X0, Y1 - Y0), '-z'), 'edge': (G.rect('edge'), 'fit')}); Q.append(o)
    o = box((0.22, 0.7, 0.012), (-0.41, 1.55, -0.455), glow, name='vd1_buttons')
    map_groups(o, lambda gn, gc: 'f' if gn[2] < -0.8 else 'e', {'f': (G.rect('bcol'), 'decal', (-0.41, 1.55, 0), (0.22, 0.7), '-z'), 'e': (G.rect('edge'), 'fit')}); Q.append(o)
    env = ((-0.6, 0.0, -0.485), (0.6, 2.0, 0.45))
    return finish_prop('p_vending', P, Q, {'id': 'vending', 'lod': 45, 'tint': True}, env, ao_dist=0.25), [
        ('front', (0.6, 1.3, -2.6), (0, 1.1, 0), 35), ('buttons', (-0.15, 1.2, -1.2), (-0.3, 1.0, -0.45), 35),
        ('side', (2.2, 1.5, -0.8), (0.4, 1.1, 0), 35), ('back', (-0.8, 1.5, 3.3), (0, 1.05, 0.45), 35)]


# ------------------------------------------------------------ p_generator
def build_generator():
    """generatorTower() map.js:1511 (rot 0): body 2.2 x 1.55 x 3.2 (y 0.35..1.9), louvred sides, exhaust at x 0.55 z 0.75,
    tyres at x +-0.75, the mast at z -1.18 up to 8.5, a lamp bar 2.4 x 0.8 at 8.5..9.3 facing -z. a towable light tower:
    the generator enclosure on a single-axle trailer with a tow eye and four outrigger jacks, a three-stage telescopic
    mast on its pivot with the winch, four LED floods (glow) on the crossbar, tipped down a little"""
    A = Atlas('gt_paint_atlas', 128, 128)
    YEL = 0xf5b81a
    A.add('yellow', 0, 0, 32, 32, p_noise(YEL, 0.06, 81, cells=4))
    def side(v):  # a louvred door (64 x 32 for 2.4 x 0.7 m): slats, hinges, the TOO BRIGHT sticker
        h, w = v.shape[:2]
        p_noise(YEL, 0.06, 82, cells=4)(v)
        for y in range(4, h - 3, 3):
            v[y, 4:w - 18] = hexrgb(0x5a3e08); v[y + 1, 4:w - 18] = hexrgb(0xffe07a)
        v[0] = v[-1] = hexrgb(0xb07e10); v[:, 0] = v[:, -1] = hexrgb(0xb07e10)
        for y in (5, h - 7): v[y:y + 3, 1:3] = hexrgb(0x4a4e54)  # hinges
        v[6:26, w - 16:w - 3] = hexrgb(0xffffff); v[6, w - 16:w - 3] = v[25, w - 16:w - 3] = hexrgb(0x141414)
        px_disc(v, w - 9.5, 14, 5.2, 0xffe14d)  # a smiley in shades: this lamp is too bright, even for it
        v[12:14, w - 14:w - 5] = hexrgb(0x141414); v[13, w - 10:w - 9] = hexrgb(0x141414)
        v[17, w - 12:w - 7] = hexrgb(0x141414); v[16, w - 13] = v[16, w - 7] = hexrgb(0x141414)
    A.add('side', 0, 32, 64, 32, side)
    def front(v):  # the front end (64 x 32 for 2.2 x 1.16 m): hazard band along the bottom, DAY MAKER, a vent
        h, w = v.shape[:2]
        p_noise(YEL, 0.06, 83, cells=4)(v)
        yy, xx = np.mgrid[0:6, 0:w]
        v[h - 6:] = np.where((((xx + yy) // 4) % 2 == 0)[:, :, None], hexrgb(0x141414), hexrgb(YEL))
        t = 'DAY MAKER'; p_text(v, t, (w - twidth(t)) // 2, 4, 1, 0x141414)  # (the brand: it turns night into day)
        for y in range(15, 23, 2): v[y, 20:44] = hexrgb(0x5a3e08)
    A.add('front', 64, 0, 64, 32, front)
    def panel(v):  # the control panel: dark, two gauges, toggles, an hour meter, LIGHTS
        h, w = v.shape[:2]
        v[:] = hexrgb(0x2a2c30); v[0] = v[-1] = hexrgb(0x4a4e54)
        for cx_ in (10, 26):
            px_disc(v, cx_, 12, 6, 0xe8ecf0); px_disc(v, cx_, 12, 5, 0x141414); px_line(v, cx_, 12, cx_ + 3, 8, 0xff3030, 1.0)
        for k in range(4): v[8:14, 38 + k * 6:40 + k * 6] = hexrgb(0xd8dce2); v[8, 38 + k * 6:40 + k * 6] = hexrgb(0x39ff14)
        v[19:28, 2:28] = hexrgb(0x101214); p_text(v, '9999', 3, 20, 1, 0x39ff14)  # the hour meter (it has seen things)
        p_text(v, 'LIGHTS', 29, 20, 1, 0xe8ecf0)
    A.add('panel', 64, 32, 64, 32, panel)
    A.add('grey', 32, 0, 16, 16, p_noise(0x8a9199, 0.1, 85))
    A.add('black', 48, 0, 16, 16, p_noise(0x1c1c20, 0.1, 86))
    A.add('dark', 32, 16, 16, 16, p_noise(0x3a3e44, 0.1, 84))
    paint = mat('gt_paint', 0xffffff, rough=0.32, clearcoat=0.6, tex=A.image())
    S = Atlas('gt_steel_atlas', 64, 32)
    S.add('galv', 0, 0, 16, 16, p_noise(0x9aa2aa, 0.1, 87, cells=4))
    def tyre(v):
        v[:] = hexrgb(0x1c1c20); v[:, ::3] = hexrgb(0x2c2c32)
    S.add('tyre', 16, 0, 16, 16, tyre)
    def hub(v):  # the wheel from the side: a grey steel rim, five lug nuts
        h, w = v.shape[:2]
        v[:] = hexrgb(0x2a2a30); px_disc(v, w / 2, h / 2, 7.5, 0x9aa2aa); px_disc(v, w / 2, h / 2, 2.5, 0x5a6068)
        for k in range(5):
            a = 2 * math.pi * k / 5; px_disc(v, w / 2 + math.cos(a) * 4.5, h / 2 + math.sin(a) * 4.5, 1.0, 0xd8dde2)
    S.add('hub', 32, 0, 16, 16, hub)
    S.add('chrome', 48, 0, 16, 16, p_noise(0xd8dde2, 0.06, 88))
    S.add('housing', 0, 16, 16, 16, p_noise(0x3a3e44, 0.1, 89))
    S.add('red', 16, 16, 16, 16, p_noise(0xe8202a, 0.05, 90))
    steel = mat('gt_steel', 0xffffff, rough=0.35, metal=0.45, clearcoat=0.3, tex=S.image())
    L = Atlas('gt_glow_atlas', 16, 16)
    def leds(v):  # a 4 x 4 LED flood face
        v[:] = hexrgb(0xffe9a8)
        for y in range(2, 16, 4):
            for x in range(2, 16, 4): v[y:y + 2, x:x + 2] = hexrgb(0xfffbe8)
    L.add('lens', 0, 0, 16, 16, leds)
    glow = mat('glow', 0xffffff, rough=0.3, emit=0xffffff, strength=1.0, tex=L.image(), emit_tex=True)
    P = []
    def add(o, reg, atl=S): uv_fit(o, atl.rect(reg)); P.append(o); return o
    # the trailer: rails, cross members, tow eye, axle on its springs, two wheels, four outrigger jacks
    for sx in (-1, 1): add(box((0.1, 0.14, 3.05), (sx * 0.45, 0.59, 0.025), steel, name='gt_rail'), 'galv')
    for z in (-1.42, 0.0, 1.47): add(box((0.92, 0.1, 0.08), (0, 0.59, z), steel, name='gt_cross'), 'galv')
    add(box((0.12, 0.09, 0.08), (0, 0.59, -1.44), steel, name='gt_tongue'), 'galv')  # (thinner than the cross member it runs into)
    eye = lathe([(0.04, 0.565), (0.07, 0.59), (0.04, 0.615), (0.025, 0.59), (0.04, 0.565)], (0, 0, -1.53), steel, seg=8, axis='y', name='gt_eye', cap=False)
    add(eye, 'galv')
    add(box((1.36, 0.07, 0.07), (0, 0.35, 0), steel, name='gt_axle'), 'galv')
    for sx in (-1, 1): add(box((0.07, 0.17, 0.7), (sx * 0.45, 0.445, 0), steel, name='gt_spring'), 'galv')
    for sx in (-1, 1):
        t = lathe([(0.19, -0.15), (0.33, -0.15), (0.35, -0.115), (0.35, 0.115), (0.33, 0.15), (0.19, 0.15)], (sx * 0.75, 0.35, 0), steel, seg=8, axis='x', name='gt_tyre', cap=False)
        add(t, 'tyre')
        hb = cyl(0.215, 0.32, (sx * 0.75, 0.35, 0), steel, axis='x', seg=8, name='gt_hub')  # (1 cm proud of the tyre walls, through them: the tyre sits on it)
        map_groups(hb, lambda gn, gc: 'f' if abs(gn[0]) > 0.8 else 'e', {'f': (S.rect('hub'), 'decal', (sx * 0.75, 0.35, 0), (0.43, 0.43), '+x' if sx > 0 else '-x'), 'e': (S.rect('galv'), 'fit')})
        P.append(hb)
    for sx in (-1, 1):
        for sz in (-1, 1):
            add(box((0.64, 0.08, 0.08), (sx * 0.8, 0.6, sz * 1.35), steel, name='gt_outrigger'), 'galv')
            add(box((0.08, 0.72, 0.08), (sx * 1.12, 0.38, sz * 1.35), steel, name='gt_jack'), 'galv')
            add(box((0.16, 0.03, 0.16), (sx * 1.12, 0.015, sz * 1.35), steel, name='gt_pad'), 'housing')
    # the enclosure: louvred doors both sides, handles, the control panel + E-stop at the back, lifting eye, exhaust, fuel
    enc = box((2.2, 1.16, 3.03), (0, 1.32, 0.065), paint, bev=0.03, seg=1, name='gt_enclosure')
    apply_mods(enc)
    map_groups(enc, lambda gn, gc: side_of(gn), {'-z': (A.rect('front'), 'decal', (0, 1.32, 0), (2.2, 1.16), '-z'), '+z': (A.rect('yellow'), 'fit'),
               '-x': (A.rect('yellow'), 'fit'), '+x': (A.rect('yellow'), 'fit'), '+y': (A.rect('yellow'), 'fit'), '-y': (A.rect('black'), 'fit'), None: (A.rect('yellow'), 'fit')})
    P.append(enc)
    for sx in (-1, 1):
        d = box((0.03, 0.7, 2.4), (sx * 1.105, 1.27, 0), paint, name='gt_door')
        map_groups(d, lambda gn, gc: 'f' if abs(gn[0]) > 0.8 else 'e', {'f': (A.rect('side'), 'decal', (sx * 1.105, 1.27, 0), (2.4, 0.7), '+x' if sx > 0 else '-x'), 'e': (A.rect('yellow'), 'fit')})
        P.append(d)
        for z in (-0.6, 0.6): add(box((0.03, 0.1, 0.05), (sx * 1.13, 1.27, z), steel, name='gt_handle'), 'chrome')
    pn = box((1.0, 0.55, 0.04), (0, 1.3, 1.57), paint, name='gt_panel')
    map_groups(pn, lambda gn, gc: 'f' if gn[2] > 0.8 else 'e', {'f': (A.rect('panel'), 'decal', (0, 1.3, 1.57), (1.0, 0.55), '+z'), 'e': (A.rect('dark'), 'fit')}); P.append(pn)
    es = lathe([(0.03, 0.0), (0.03, 0.004), (0.045, 0.006), (0.045, 0.01), (0.0, 0.012)], (0.36, 1.12, 1.588), steel, seg=8, axis='z', name='gt_estop', cap=False)
    add(es, 'red')
    add(frame_ring('gt_lifteye', (-0.08, 1.88, 0.08, 2.04), (-0.04, 1.93, 0.04, 2.0), 0.085, 0.115, steel), 'galv')
    add(cyl(0.065, 0.66, (0.55, 2.2, 0.75), steel, axis='y', seg=8, name='gt_exhaust'), 'chrome')
    rc = cyl(0.075, 0.012, (0.55, 2.536, 0.74), steel, axis='y', seg=8, name='gt_raincap')
    turn_obj(rc, 'x', 0.6, (0.55, 2.53, 0.815)); add(rc, 'chrome')  # (the flapper blown open, hinged on the back of the rim)
    add(cyl(0.06, 0.05, (-0.65, 1.91, 1.1), steel, axis='y', seg=8, name='gt_fuelcap'), 'chrome')
    # the mast: pivot bracket + pin, three telescoping stages with collars, the winch
    for sx in (-1, 1): add(box((0.03, 0.34, 0.36), (sx * 0.15, 2.05, -1.18), steel, name='gt_bracket'), 'galv')
    add(cyl(0.035, 0.36, (0, 2.08, -1.18), steel, axis='x', seg=8, name='gt_pin'), 'chrome')
    for w_, y0, y1 in ((0.24, 1.95, 4.45), (0.19, 4.3, 6.6), (0.14, 6.45, 8.6)):
        o = box((w_, y1 - y0, w_), (0, (y0 + y1) / 2, -1.18), steel, bev=0.01, seg=1, name='gt_mast'); apply_mods(o); add(o, 'galv')
    for w_, y in ((0.28, 4.41), (0.23, 6.565)): add(box((w_, 0.075, w_), (0, y, -1.18), steel, name='gt_collar'), 'housing')
    add(cyl(0.055, 0.14, (0.19, 2.6, -1.18), steel, axis='x', seg=8, name='gt_winch'), 'housing')
    add(box((0.02, 0.15, 0.02), (0.27, 2.55, -1.18), steel, name='gt_crank'), 'red')
    # the crossbar and four floods, tipped 10 degrees down
    add(box((2.3, 0.08, 0.08), (0, 8.64, -1.18), steel, name='gt_bar'), 'galv')
    add(box((0.26, 0.05, 0.26), (0, 8.62, -1.18), steel, name='gt_cap'), 'galv')
    lamp_parts = []
    for x in (-0.86, -0.29, 0.29, 0.86):
        hs = box((0.5, 0.48, 0.16), (x, 9.0, -1.29), steel, bev=0.012, seg=1, name='gt_flood'); apply_mods(hs); uv_fit(hs, S.rect('housing'))
        ln = box((0.44, 0.42, 0.012), (x, 9.0, -1.373), glow, name='gt_lens')
        map_groups(ln, lambda gn, gc: 'f' if gn[2] < -0.8 else 'e', {'f': (L.rect('lens'), 'decal', (x, 9.0, -1.38), (0.44, 0.42), '-z'), 'e': (L.rect('lens'), 'fit')})
        vs_ = box((0.5, 0.012, 0.12), (x, 9.242, -1.42), steel, name='gt_visor'); uv_fit(vs_, S.rect('housing'))
        for o in (hs, ln, vs_): turn_obj(o, 'x', -0.17, (x, 8.76, -1.21)); lamp_parts.append(o)
    top = bbox(lamp_parts)[1][1]
    for o in lamp_parts: o.data.transform(Matrix.Translation(gv(0, 9.3 - top, 0)))
    for x in (-0.86, -0.29, 0.29, 0.86):
        add(box((0.06, 0.2 + (9.3 - top), 0.06), (x, 8.68 + (0.2 + (9.3 - top)) / 2 - 0.02, -1.21), steel, name='gt_yoke'), 'galv')
    P += lamp_parts
    # lod1: the enclosure + chassis + wheels, the jack pads (they set the width), the mast, the lamp bar and four lit faces
    Q = []
    o = box((2.2, 1.16, 3.2), (0, 1.32, 0.0), paint, name='gt1_body')
    map_groups(o, lambda gn, gc: side_of(gn), {'-z': (A.rect('front'), 'decal', (0, 1.32, 0), (2.2, 1.16), '-z'), '+z': (A.rect('panel'), 'decal', (0, 1.32, 0), (2.2, 1.16), '+z'),
               '-x': (A.rect('side'), 'decal', (0, 1.32, 0), (3.2, 1.16), '-x'), '+x': (A.rect('side'), 'decal', (0, 1.32, 0), (3.2, 1.16), '+x'),
               '+y': (A.rect('yellow'), 'fit'), '-y': (A.rect('black'), 'fit')}); Q.append(o)
    o = box((1.2, 0.5, 3.0), (0, 0.49, 0.0), paint, name='gt1_chassis'); uv_fit(o, A.rect('grey')); Q.append(o)  # (as wide as the wheels' inner faces)
    for sx in (-1, 1):
        o = lathe([(0.35, -0.15), (0.35, 0.15)], (sx * 0.75, 0.35, 0), paint, seg=6, axis='x', name='gt1_wheel', cap=False); uv_fit(o, A.rect('black')); Q.append(o)
    for sz in (-1, 1):
        o = box((2.4, 0.08, 0.1), (0, 0.6, sz * 1.35), paint, name='gt1_outriggers'); uv_fit(o, A.rect('grey')); Q.append(o)  # (they set the width)
    o = box((0.22, 6.72, 0.22), (0, 5.24, -1.18), paint, name='gt1_mast'); uv_fit(o, A.rect('grey')); Q.append(o)
    o = box((2.3, 0.62, 0.2), (0, 8.99, -1.29), paint, name='gt1_lamps'); uv_fit(o, A.rect('dark')); Q.append(o)
    for x in (-0.86, -0.29, 0.29, 0.86):
        o = box((0.44, 0.42, 0.012), (x, 8.99, -1.393), glow, name='gt1_lens')
        map_groups(o, lambda gn, gc: 'f' if gn[2] < -0.8 else 'e', {'f': (L.rect('lens'), 'decal', (x, 8.99, -1.4), (0.44, 0.42), '-z'), 'e': (L.rect('lens'), 'fit')}); Q.append(o)
    env = ((-1.2, 0.0, -1.6), (1.2, 9.3, 1.6))
    return finish_prop('p_generator', P, Q, {'id': 'generator', 'lod': 70, 'tint': False}, env, ao_dist=0.4), [
        ('whole', (6.0, 5.5, -7.5), (0, 4.4, 0), 35), ('trailer', (3.2, 1.6, -3.6), (0, 0.9, 0), 35),
        ('lamps', (1.8, 9.6, -3.6), (0, 9.0, -1.3), 35), ('back', (-2.4, 1.8, 3.6), (0, 1.2, 1.2), 35)]


# ------------------------------------------------------------ driver: one fresh scene per prop (exact material names)
PROPS = [('streetlight', build_streetlight), ('acunit', build_acunit), ('cone', build_cone), ('barrier', build_barrier),
         ('watertower', build_watertower), ('billboard', build_billboard), ('billboard_post', build_billboard_post),
         ('vending', build_vending), ('generator', build_generator)]


def run():
    for pid, fn in PROPS:
        if ONLY and pid not in ONLY: continue
        reset(); lib._mats.clear()
        (root, m0, m1, t0, t1), views = fn()
        fid = root.name
        if '--no-export' not in ARGV: export(root, fid)
        close_shots(root, views, pid)
        if '--no-sheet' not in ARGV: lod_sheet(root, m0, m1, fid, t1)


run()
