# JANKFIRE Blender kit: build a model from code, export a .glb for the game, render a model sheet to review it.
# Everything here takes GAME coordinates (three.js: x right, y up, -z forward, metres), so numbers can be copied
# straight from public/js/models.js. Blender itself is z-up: gv() converts, and the glTF exporter converts back.
import bpy, bmesh, math, json, os, sys, random
from mathutils import Vector, Matrix, Euler
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
MODELS = os.path.join(ROOT, 'public', 'models')
SHEETS = os.path.join(HERE, 'sheets')


def gv(x, y, z):  # game (three) -> blender
    return Vector((x, -z, y))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.scale_length = 1.0
    random.seed(7)


# ------------------------------------------------------------ materials
def srgb(h):  # 0xRRGGBB (what the game code uses) -> linear rgba for blender
    c = [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


_mats = {}
def mat(name, color=0x808080, rough=0.5, metal=0.0, emit=None, strength=1.0, alpha=None, tex=None, clearcoat=0.0, emit_tex=False):
    """principled material. tex = an image from the tex_* helpers (its colours already baked in, nearest filtered).
    emit_tex = the texture glows too (embers, screens). the glTF exporter keeps: base colour/texture, roughness, metallic,
    emission, alpha."""
    if name in _mats: return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(color)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if clearcoat: b.inputs['Coat Weight'].default_value = clearcoat
    if emit is not None:
        b.inputs['Emission Color'].default_value = srgb(emit)
        b.inputs['Emission Strength'].default_value = strength
    if alpha is not None:
        b.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
        m.shadow_method = 'HASHED'
    if tex is not None:
        n = m.node_tree.nodes.new('ShaderNodeTexImage')
        n.image = tex
        n.interpolation = 'Closest'
        m.node_tree.links.new(n.outputs['Color'], b.inputs['Base Color'])
        if emit_tex: m.node_tree.links.new(n.outputs['Color'], b.inputs['Emission Color'])
    m['jf_color'] = color
    _mats[name] = m
    return m


def _image(name, px):  # px: h x w x 3 floats 0..1 (srgb) -> packed blender image
    h, w = px.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=False)
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = px[::-1]  # blender rows go bottom up
    img.pixels.foreach_set(rgba.ravel())
    img.file_format = 'PNG'
    img.pack()
    return img


def hexrgb(h): return np.array([((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255], dtype=np.float32)


def tex_noise(name, base, var=0.12, size=32, speck=None, speck_p=0.0, seed=1):
    """crusty value noise over a base colour (cruelty-squad grime). speck = a second colour sprinkled in."""
    r = np.random.default_rng(seed)
    lo = r.random((size // 4, size // 4))
    big = np.kron(lo, np.ones((4, 4)))[:size, :size]
    n = 0.6 * big + 0.4 * r.random((size, size))
    px = hexrgb(base)[None, None, :] * (1 - var + 2 * var * n[:, :, None])
    if speck is not None:
        mask = r.random((size, size)) < speck_p
        px[mask] = hexrgb(speck)
    return _image(name, np.clip(px, 0, 1))


def tex_stripes(name, a, b, size=32, width=4, diag=True):
    y, x = np.mgrid[0:size, 0:size]
    k = ((x + y) if diag else x) // width % 2
    px = np.where(k[:, :, None] == 0, hexrgb(a), hexrgb(b))
    return _image(name, px.astype(np.float32))


def tex_camo(name, cols, size=64, seed=3):
    """blotchy camo / leopard-ish patches from a list of colours (ugly on purpose)."""
    r = np.random.default_rng(seed)
    n = np.zeros((size, size))
    for octv, w in ((8, 0.6), (16, 0.3), (32, 0.1)):
        lo = r.random((octv, octv))
        n += w * np.kron(lo, np.ones((size // octv, size // octv)))
    q = np.clip((n - n.min()) / (np.ptp(n) + 1e-6) * len(cols), 0, len(cols) - 1e-3).astype(int)
    px = np.stack([hexrgb(c) for c in cols])[q]
    return _image(name, px.astype(np.float32))


def tex_canvas(name, w, h, draw):
    """draw(px) gets an h x w x 3 array to paint into (numbers on balls, stickers, labels)."""
    px = np.zeros((h, w, 3), dtype=np.float32)
    draw(px)
    return _image(name, np.clip(px, 0, 1))


# 5x7 bitmap digits/letters for painted numbers and stickers
FONT = {
    '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'], '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    '2': ['01110', '10001', '00001', '00010', '00100', '01000', '11111'], '3': ['11110', '00001', '00001', '01110', '00001', '00001', '11110'],
    '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'], '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
    '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'], '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
    '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'], '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
    'J': ['00111', '00010', '00010', '00010', '10010', '10010', '01100'], 'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
    'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'], 'K': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],
    'F': ['11111', '10000', '10000', '11110', '10000', '10000', '10000'], 'I': ['01110', '00100', '00100', '00100', '00100', '00100', '01110'],
    'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'], 'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
    'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'], 'C': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'],
    'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'], 'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'], 'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
    'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'], 'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'], 'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],
    'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'], 'G': ['01110', '10001', '10000', '10111', '10001', '10001', '01111'],
    'M': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'], 'W': ['10001', '10001', '10001', '10101', '10101', '11011', '10001'],
    'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'], 'V': ['10001', '10001', '10001', '10001', '01010', '01010', '00100'],
    '!': ['00100', '00100', '00100', '00100', '00100', '00000', '00100'], ' ': ['00000'] * 7, '-': ['00000', '00000', '00000', '11111', '00000', '00000', '00000'],
    '.': ['00000'] * 6 + ['00100'], '#': ['01010', '11111', '01010', '01010', '01010', '11111', '01010'],
    'Q': ['01110', '10001', '10001', '10001', '10101', '10010', '01101'], 'Z': ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
    ':': ['00000', '00100', '00000', '00000', '00000', '00100', '00000'], '?': ['01110', '10001', '00001', '00010', '00100', '00000', '00100'],
    '/': ['00001', '00010', '00010', '00100', '01000', '01000', '10000'], '+': ['00000', '00100', '00100', '11111', '00100', '00100', '00000'],
    "'": ['00100', '00100', '01000', '00000', '00000', '00000', '00000'], '&': ['01100', '10010', '10100', '01000', '10101', '10010', '01101'],
    '<': ['00000', '01010', '11111', '11111', '01110', '00100', '00000'],  # a heart
}


def text_px(px, s, x0, y0, scale, color):
    """paint text s into px at (x0, y0) top-left, each font pixel scale x scale."""
    c = hexrgb(color)
    for i, ch in enumerate(s):
        g = FONT.get(ch.upper(), FONT[' '])
        for ry, row in enumerate(g):
            for rx, bit in enumerate(row):
                if bit == '1':
                    y, x = y0 + ry * scale, x0 + (i * 6 + rx) * scale
                    px[y:y + scale, x:x + scale] = c


# ------------------------------------------------------------ objects
def _link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def _obj(name, bm, material):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = _link(bpy.data.objects.new(name, me))
    if material is not None: me.materials.append(material)
    return o


def _place(o, pos, rot):
    o.location = gv(*pos)
    if rot: o.rotation_euler = Euler((rot[0], -rot[2], rot[1]), 'YZX')  # three's XYZ euler in blender axes
    return o


def bevel(o, w=0.004, seg=2, angle=40, harden=True):
    if w <= 0: return o
    m = o.modifiers.new('bevel', 'BEVEL')
    m.width = w; m.segments = seg; m.limit_method = 'ANGLE'; m.angle_limit = math.radians(angle)
    m.harden_normals = harden; m.miter_outer = 'MITER_ARC'
    return o


def smooth(o, angle=35):
    me = o.data
    for p in me.polygons: p.use_smooth = True
    if hasattr(me, 'use_auto_smooth'):
        me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(angle)
    return o


def box(size, pos=(0, 0, 0), m=None, bev=0.0, rot=None, name='box', seg=2, taper=None):
    """size = (w, h, d) along game x, y, z. taper = (sx, sy) scale of the -z (front) face, for wedges."""
    w, h, d = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        x, y, z = v.co.x * w, v.co.z * h, -v.co.y * d  # blender cube corner -> game axes
        if taper and z < 0: x *= taper[0]; y *= taper[1]
        v.co = gv(x, y, z)
    o = _obj(name, bm, m)
    _place(o, pos, rot)
    smooth(o); bevel(o, bev, seg)
    return o


def cyl(r, length, pos=(0, 0, 0), m=None, axis='z', seg=16, r2=None, bev=0.0, rot=None, name='cyl', cap=True):
    """cylinder (or cone with r2) along a game axis, centred on pos."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=length)
    # created along blender z (r2 at +z). turn it onto the game axis: r2 ends up at -z (front), +y (top) or +x
    R = {'z': Matrix.Rotation(-math.pi / 2, 4, 'X'), 'y': Matrix.Identity(4), 'x': Matrix.Rotation(math.pi / 2, 4, 'Y')}[axis]
    bmesh.ops.transform(bm, matrix=R, verts=bm.verts)
    o = _obj(name, bm, m)
    _place(o, pos, rot)
    smooth(o, 50); bevel(o, bev, 2, 50)
    return o


def ball(r, pos=(0, 0, 0), m=None, scale=(1, 1, 1), seg=16, rings=10, name='ball', rot=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for v in bm.verts: v.co = Vector((v.co.x * scale[0], v.co.y * scale[2], v.co.z * scale[1]))
    o = _obj(name, bm, m)
    _place(o, pos, rot)
    for p in o.data.polygons: p.use_smooth = True
    return o


def lathe(profile, pos=(0, 0, 0), m=None, seg=16, axis='z', name='lathe', rot=None, cap=True):
    """profile = [(radius, along)] revolved round a game axis (along = game z for axis z, so negative = forward)."""
    bm = bmesh.new()
    rings = []
    for r, a in profile:
        ring = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            c, s = math.cos(t) * r, math.sin(t) * r
            p = {'z': (c, s, a), 'y': (c, a, s), 'x': (a, c, s)}[axis]
            ring.append(bm.verts.new(gv(*p)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            try: bm.faces.new((a[i], a[j], b[j], b[i]))
            except ValueError: pass
    for ring, r in ((rings[0], profile[0][0]), (rings[-1], profile[-1][0])):
        if r > 1e-5 and cap:
            try: bm.faces.new(ring)
            except ValueError: pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    _place(o, pos, rot)
    smooth(o, 50)
    return o


def side(poly, thick, pos=(0, 0, 0), m=None, bev=0.0, seg=2, name='side', holes=(), rot=None, angle=40):
    """a side-view outline extruded across the gun: poly = [(z, y)] in game coords (z forward is negative), thick
    along x, centred. holes = more outlines cut through (trigger guards, thumbholes, lightening cuts)."""
    def slab(pts, t, nm):
        bm = bmesh.new()
        vs = [bm.verts.new(gv(-t / 2, y, z)) for z, y in pts]
        f = bm.faces.new(vs)
        bmesh.ops.recalc_face_normals(bm, faces=[f])
        r = bmesh.ops.extrude_face_region(bm, geom=[f])
        nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((t, 0, 0)), verts=nv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return _obj(nm, bm, None)
    o = slab(poly, thick, name)
    if m is not None: o.data.materials.append(m)
    for h in holes:
        cut = slab(h, thick * 3, name + '_cut')
        md = o.modifiers.new('cut', 'BOOLEAN'); md.object = cut; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
        apply_mods(o); bpy.data.objects.remove(cut, do_unlink=True)  # (no bevel yet at this point)
    _place(o, pos, rot)
    smooth(o, angle); bevel(o, bev, seg, angle)
    return o


def tube(points, r, m=None, seg=8, name='tube', closed=False):
    """a round tube along a path of game points (cables, grab handles, trigger guards, bars)."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(points) - 1)
    for p, q in zip(sp.points, points): p.co = (*gv(*q), 1)
    sp.use_cyclic_u = closed
    cu.bevel_depth = r; cu.bevel_resolution = max(1, seg // 4 - 1); cu.use_fill_caps = True
    o = _link(bpy.data.objects.new(name, cu))
    if m is not None: cu.materials.append(m)
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True)
    bpy.ops.object.convert(target='MESH')
    o = bpy.context.view_layer.objects.active
    smooth(o, 60)
    return o


def bend_path(p0, p1, sag, n=8):  # a sagging cable between two game points
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(tuple(p0[k] + (p1[k] - p0[k]) * t - (sag * 4 * t * (1 - t) if k == 1 else 0) for k in range(3)))
    return out


def arc(cx, cy, r, a0, a1, n=10):  # points on a side-view arc (z, y), angles in degrees, 0 = toward +z (back)
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def mirror_x(o):
    m = o.modifiers.new('mx', 'MIRROR'); m.use_axis[0] = True; m.use_clip = False
    return o


def array(o, count, offset):  # offset in game coords
    m = o.modifiers.new('arr', 'ARRAY'); m.count = count; m.use_relative_offset = False; m.use_constant_offset = True
    m.constant_offset_displace = gv(*offset)
    return o


def apply_mods(o):
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True)
    for md in list(o.modifiers):
        try: bpy.ops.object.modifier_apply(modifier=md.name)
        except RuntimeError as e: print('modifier failed', o.name, md.name, e); o.modifiers.remove(md)


def dup(o, pos=None, rot=None, name=None):
    n = o.copy(); n.data = o.data.copy()
    for md in o.modifiers: pass  # copy() keeps modifiers
    _link(n)
    if name: n.name = name
    if pos is not None: n.location = gv(*pos)
    if rot is not None: n.rotation_euler = Euler((rot[0], -rot[2], rot[1]), 'YZX')
    return n


def uv_box(o, size=0.25):
    """cube-project UVs (in world metres / size) so tiling textures land at a steady pixel density."""
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=size, correct_aspect=False, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')


def join(objs, name):
    objs = [o for o in objs if o is not None]
    for o in objs: apply_mods(o)
    bpy.context.view_layer.objects.active = objs[0]
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    for o in objs: o.select_set(True)
    if len(objs) > 1: bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    j.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return j


def part(objs, name, pivot=None):
    """join objs into one named node (something the game can move: a pump, a cylinder, a wheel) with its origin at
    pivot (game coords)."""
    o = join(objs, name)
    if pivot is not None:
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        p = gv(*pivot)
        o.data.transform(Matrix.Translation(-p))
        o.location = p
    return o


def finish(root_name, parts, meta, uv=None):
    """parent every part under one root empty that carries the game metadata (exported as glTF extras -> three's
    userData.jf), apply everything, return the root. meta: muzzle, sight, hatAt, kind..."""
    root = _link(bpy.data.objects.new(root_name, None))
    root['jf'] = json.dumps(meta)
    for p in parts:
        apply_mods(p)
        p.parent = root
    return root


def stats(root):
    tris = 0
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    dg = bpy.context.evaluated_depsgraph_get()
    for o in root.children_recursive:
        if o.type != 'MESH': continue
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles(); tris += len(me.loop_triangles)
        for v in me.vertices:
            w = o.matrix_world @ v.co
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
        o.evaluated_get(dg).to_mesh_clear()
    # back to game axes: x, y(up)=blender z, z = -blender y
    g_lo = (lo.x, lo.z, -hi.y); g_hi = (hi.x, hi.z, -lo.y)
    return tris, g_lo, g_hi


def export(root, file_id):
    os.makedirs(MODELS, exist_ok=True)
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    root.select_set(True)
    for c in root.children_recursive: c.select_set(True)
    path = os.path.join(MODELS, file_id + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                              export_extras=True, export_yup=True, export_texcoords=True, export_normals=True,
                              export_materials='EXPORT', export_image_format='AUTO', export_lights=False, export_cameras=False)
    tris, lo, hi = stats(root)
    print(f'JF_EXPORT {file_id}: {os.path.getsize(path) // 1024} KB, {tris} tris, '
          f'x {lo[0]:.3f}..{hi[0]:.3f} y {lo[1]:.3f}..{hi[1]:.3f} z {lo[2]:.3f}..{hi[2]:.3f}')
    return path


# ------------------------------------------------------------ model sheet (turnaround) for review
def _look_at(cam, target):
    d = target - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def sheet(root, file_id, views=('persp', 'left', 'right', 'top', 'front', 'back_persp'), res=(640, 420), bg=0x3a3346, extra_note='', exposure=0.0):
    """renders the model from several sides with a studio rig and tiles them into tools/blender/sheets/<id>.png
    (exposure < 0 for white things: paper, cards, snow, so they don't blow out)"""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    ee = sc.eevee
    ee.taa_render_samples = 32
    for k, v in (('use_gtao', True), ('use_ssr', True), ('use_bloom', True), ('use_soft_shadows', True)):
        if hasattr(ee, k): setattr(ee, k, v)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.exposure = exposure
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = srgb(bg)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
    tris, lo, hi = stats(root)
    lo_b, hi_b = gv(lo[0], lo[1], hi[2]), gv(hi[0], hi[1], lo[2])
    c = (lo_b + hi_b) / 2
    size = max((hi_b - lo_b).length, 0.05)
    # studio lights scaled to the model
    def light(kind, energy, loc, sz=1.0, col=(1, 1, 1)):
        L = bpy.data.lights.new(kind, kind); L.energy = energy * size * size; L.color = col
        if kind == 'AREA': L.size = sz * size
        o = _link(bpy.data.objects.new(kind, L)); o.location = c + Vector(loc) * size; _look_at(o, c)
        return o
    light('AREA', 200, (1.2, -1.4, 1.6), 1.2)
    light('AREA', 70, (-1.6, -0.6, 0.6), 1.5, (0.85, 0.9, 1.0))
    light('AREA', 150, (-0.4, 1.8, 1.2), 0.6, (1.0, 0.8, 0.95))
    light('AREA', 40, (0.2, 0.2, -1.6), 1.5, (0.9, 0.85, 1.0))
    cam = _link(bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))); sc.camera = cam
    # a floor tile under it so shapes read
    tiles = []
    out = []
    os.makedirs(SHEETS, exist_ok=True)
    tmp = os.path.join(SHEETS, '_tmp')
    os.makedirs(tmp, exist_ok=True)
    dims = hi_b - lo_b
    for i, v in enumerate(views):
        cd = cam.data
        if v in ('persp', 'back_persp'):
            cd.type = 'PERSP'; cd.lens = 50
            dirv = Vector((1.0, -1.15, 0.6)) if v == 'persp' else Vector((-1.0, 1.2, 0.75))
            cam.location = c + dirv.normalized() * size * 1.85
            _look_at(cam, c)
        else:
            cd.type = 'ORTHO'
            # side views look across the long horizontal axis (a gun's z, a car's x), front views along it
            ylong = dims.y >= dims.x
            side_d, end_d = (Vector((1, 0, 0)), Vector((0, 1, 0))) if ylong else (Vector((0, -1, 0)), Vector((1, 0, 0)))
            d = {'left': -side_d, 'right': side_d, 'top': Vector((0, 0, 1)), 'front': end_d, 'back': -end_d}[v]
            cam.location = c + d * size * 3
            _look_at(cam, c)
            if v == 'top': cam.rotation_euler = Euler((0, 0, math.pi / 2 if ylong else 0))
            L_, Wd = (dims.y, dims.x) if ylong else (dims.x, dims.y)
            ext = {'left': (L_, dims.z), 'right': (L_, dims.z), 'top': (L_, Wd), 'front': (Wd, dims.z), 'back': (Wd, dims.z)}[v]
            cd.ortho_scale = max(ext[0], ext[1] * res[0] / res[1]) * 1.12
        cd.clip_start = size * 0.01; cd.clip_end = size * 20
        p = os.path.join(tmp, f'{file_id}_{i}.png')
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        out.append(p)
    # tile 3 x 2 with numpy
    imgs = []
    for p in out:
        im = bpy.data.images.load(p)
        a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
        imgs.append(a); bpy.data.images.remove(im)
    cols = 3; rows = (len(imgs) + cols - 1) // cols
    H, W = res[1], res[0]
    canvas = np.zeros((rows * H + 4 * (rows + 1), cols * W + 4 * (cols + 1), 4), dtype=np.float32); canvas[:, :, 3] = 1
    canvas[:, :, :3] = 0.08
    for k, a in enumerate(imgs):
        r, cc = divmod(k, cols)
        y0 = canvas.shape[0] - (r + 1) * (H + 4); x0 = 4 + cc * (W + 4)
        canvas[y0:y0 + H, x0:x0 + W] = a
    # label strip (top-left) in the bitmap font
    lab = np.zeros((7 * 3 + 6, canvas.shape[1], 3), dtype=np.float32)
    txt = f'{file_id}  {tris} TRIS  {max(dims.x, dims.y):.2f}M LONG {dims.z:.2f}M TALL {min(dims.x, dims.y):.2f}M WIDE {extra_note}'.upper().replace('_', ' ')
    text_px(lab, txt, 6, 3, 3, 0xffe14d)
    full = np.concatenate([canvas, np.concatenate([lab[::-1], np.ones(lab.shape[:2] + (1,), np.float32)], axis=2)], axis=0)
    img = bpy.data.images.new('sheet', full.shape[1], full.shape[0])
    img.pixels.foreach_set(full.ravel())
    png = os.path.join(tmp, file_id + '_sheet.png')
    img.filepath_raw = png; img.file_format = 'PNG'; img.save()
    dst = os.path.join(SHEETS, file_id + '.jpg')  # jpg keeps the repo small; fall back to png without ffmpeg
    if os.system(f'ffmpeg -loglevel error -y -i "{png}" -q:v 3 "{dst}"') != 0:
        dst = os.path.join(SHEETS, file_id + '.png'); os.replace(png, dst)
    for p in out + [png]:
        if os.path.exists(p): os.remove(p)
    try: os.rmdir(tmp)
    except OSError: pass
    print('JF_SHEET', dst)
    return dst


def main(build, file_id, **sheet_kw):
    """run a build function: build() returns the root. flags after '--': --no-sheet, --no-export"""
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    reset()
    root = build()
    if '--no-export' not in argv: export(root, file_id)
    if '--no-sheet' not in argv: sheet(root, file_id, **sheet_kw)


def cut(o, cutter, op='DIFFERENCE', keep=False):
    """boolean the cutter out of o (or UNION / INTERSECT), apply it, delete the cutter."""
    apply_mods(cutter)
    md = o.modifiers.new('bool', 'BOOLEAN'); md.object = cutter; md.operation = op; md.solver = 'EXACT'
    bpy.context.view_layer.objects.active = o
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    o.select_set(True)
    bpy.ops.object.modifier_move_to_index(modifier=md.name, index=0)  # cut first, so a bevel still rounds the cut edges
    bpy.ops.object.modifier_apply(modifier=md.name)
    if not keep: bpy.data.objects.remove(cutter, do_unlink=True)
    return o


def tex_wood(name, base=0x8a5a2b, dark=0x5a3417, size=64, seed=5, rings=7.0):
    """long wavy grain (u runs along the grain) with knots: walnut stocks, pallets, crates."""
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size] / size
    warp = np.zeros_like(x)
    for f, a in ((1, 0.08), (3, 0.03), (7, 0.012)):
        warp += a * np.sin(2 * math.pi * (f * x + r.random())) * np.cos(2 * math.pi * (f * 0.5 * y + r.random()))
    g = 0.5 + 0.5 * np.sin(2 * math.pi * rings * (y + warp))
    g = g ** 2.2 * 0.75 + 0.25 * r.random((size, size)) * 0.6
    px = hexrgb(base)[None, None] * (1 - g[:, :, None]) + hexrgb(dark)[None, None] * g[:, :, None]
    return _image(name, np.clip(px, 0, 1).astype(np.float32))


def side_x(poly, thick, pos=(0, 0, 0), m=None, bev=0.0, seg=2, name='sidex', holes=(), angle=40):
    """like side() but the outline is in the (x, y) plane (a vehicle seen from its side, front = +x), extruded along z."""
    o = side([(x, y) for x, y in poly], thick, (0, 0, 0), m, 0, seg, name, [[(x, y) for x, y in h] for h in holes], angle=angle)
    # side() made it in the (z, y) plane: turn z onto x (three: rotation.y = +90deg maps z -> x)
    o.data.transform(Matrix.Rotation(-math.pi / 2, 4, 'Z') @ Matrix.Scale(-1, 4, Vector((0, 1, 0))))  # (bx, by) -> (-by, -bx)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()  # it was a mirror
    o.location = gv(*pos)
    smooth(o, angle); bevel(o, bev, seg, angle)
    return o


def wheel(r, width, pos, tire, hub, spokes=5, hub_r=0.6, name='wheel', axis='z'):
    """a tyre (rounded lathe) + a hub with spokes, axle along game z (car wheels) or x."""
    rr = r * 0.72
    prof = [(rr, -width / 2), (r * 0.93, -width / 2), (r, -width * 0.32), (r, width * 0.32), (r * 0.93, width / 2), (rr, width / 2)]
    t = lathe(prof, pos, tire, seg=24, axis='z', name=name + '_tire')
    h = [t, cyl(rr, width * 0.9, pos, hub, axis='z', seg=20, bev=r * 0.03)]
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        h.append(box((r * 0.16, rr * 0.9, width * 0.12), (pos[0] + math.cos(a) * rr * 0.45, pos[1] + math.sin(a) * rr * 0.45, pos[2] + width * 0.47 * (1 if pos[2] >= 0 else -1)), hub, bev=r * 0.02, rot=(0, 0, a - math.pi / 2)))
    h.append(cyl(rr * 0.25, width * 1.02, pos, hub, axis='z', seg=12, bev=r * 0.02))
    if axis == 'x':
        for o in h: o.rotation_euler.rotate_axis('Z', math.pi / 2)
    return h


def main_multi(build, **sheet_kw):
    """build() returns [(root, file_id)]: each is exported and gets its own sheet"""
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    reset()
    roots = build()
    for root, fid in roots:
        for r2, _ in roots: r2.hide_render = r2 is not root; [setattr(c, 'hide_render', r2 is not root) for c in r2.children_recursive]
        if '--no-export' not in argv: export(root, fid)
        if '--no-sheet' not in argv: sheet(root, fid, **sheet_kw)


def uv_planar(o, center, size, axis='x'):
    """straight-on UVs for a decal face seen from +axis (numbers, stickers): the image's right is the viewer's right."""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y  # back to game axes
            if axis == 'x': u, w = -(gz - center[2]), gy - center[1]
            elif axis == '-x': u, w = gz - center[2], gy - center[1]  # seen from -x (a gun's left side)
            elif axis == 'z': u, w = gx - center[0], gy - center[1]
            else: u, w = gx - center[0], -(gz - center[2])
            su, sv = size if isinstance(size, (tuple, list)) else (size, size)
            uv[li].uv = (u / su + 0.5, w / sv + 0.5)


def sweep(points, radii, m=None, seg=8, name='sweep', cap=True, squash=(1.0, 1.0), smooth_angle=60):
    """a tube along a path of game points with a radius per point (bananas, necks, hoses, belts). squash scales the
    cross-section (first = towards the path's 'up', second = sideways) for flat straps or 5-sided bananas (seg=5)."""
    pts = [gv(*p) for p in points]
    n = len(pts)
    rr = list(radii) if isinstance(radii, (list, tuple)) else [radii] * n
    T = []
    for i in range(n):
        t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        T.append(t.normalized())
    up = Vector((0, 0, 1))
    if abs(T[0].dot(up)) > 0.9: up = Vector((1, 0, 0))
    N = (up - T[0] * T[0].dot(up)).normalized()
    bm = bmesh.new(); rings = []
    for i, p in enumerate(pts):
        N = (N - T[i] * T[i].dot(N)).normalized()  # parallel transport: no twisting
        B = T[i].cross(N)
        ring = [bm.verts.new(p + (N * math.cos(2 * math.pi * k / seg) * squash[0] + B * math.sin(2 * math.pi * k / seg) * squash[1]) * rr[i]) for k in range(seg)]
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            j = (k + 1) % seg
            try: bm.faces.new((a[k], a[j], b[j], b[k]))
            except ValueError: pass
    if cap:
        for ring, r in ((rings[0], rr[0]), (rings[-1], rr[-1])):
            if r > 1e-5:
                try: bm.faces.new(ring)
                except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, smooth_angle)
    return o


def rod(p0, p1, r, m=None, seg=8, name='rod', r1=None, bev=0.0):
    """a cylinder (or cone, with r1) from game point p0 to p1: struts, pins, levers, stock frames."""
    a, b = gv(*p0), gv(*p1)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r1 is None else r1, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.transform(bm, matrix=q.to_matrix().to_4x4(), verts=bm.verts)
    o = _obj(name, bm, m)
    o.location = (a + b) / 2
    smooth(o, 50); bevel(o, bev, 2, 50)
    return o


def path_arc(c, r, a0, a1, n=12, plane='zy', x=0.0):
    """points on an arc in a game plane: 'zy' = side view (angles from +z towards +y), centre c = (z, y)."""
    out = []
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n)
        if plane == 'zy': out.append((x, c[1] + r * math.sin(t), c[0] + r * math.cos(t)))
    return out


# ------------------------------------------------------------ painting helpers for dials and decals (px = h x w x 3)
def px_line(px, x0, y0, x1, y1, color, w=1.0):
    h, wd = px.shape[:2]; c = hexrgb(color)
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 2
    for i in range(n + 1):
        t = i / n; x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
        r = max(0.5, w / 2)
        for yy in range(int(y - r), int(y + r) + 1):
            for xx in range(int(x - r), int(x + r) + 1):
                if 0 <= xx < wd and 0 <= yy < h and (xx - x) ** 2 + (yy - y) ** 2 <= r * r + 0.25: px[yy, xx] = c


def px_disc(px, cx, cy, r, color, r_in=0.0, a0=None, a1=None):
    """filled disc / ring, optionally only between angles a0..a1 (radians, 0 = up, clockwise as you look at it)."""
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    d = np.hypot(dx, dy)
    mask = (d <= r) & (d >= r_in)
    if a0 is not None:
        ang = np.arctan2(dx, -dy)  # 0 at the top, + clockwise
        mask &= (ang >= a0) & (ang <= a1)
    px[mask] = hexrgb(color)


def centre(o):
    """bounding-box centre of an object in game coordinates"""
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    c = sum(pts, Vector()) / 8
    return (c.x, c.z, -c.y)


def zone_join(parts, name, zones, default='b', rule=None):
    """join parts into one node per wrap zone (public/js/wrapzones.js reads the name suffix): <name>_wzA = the handle
    side (grip, stock, body, furniture), _wzB = the business end (barrel, slide, mag, metal bits), _wzN = decals and
    trims that keep their own look unless the wrap is FULL, _wzAB = both. zones = {material name: 'a'|'b'|'n'|'ab'},
    rule(material name, game centre) can override it per part (return None to use the table)."""
    groups = {}
    for p in parts:
        apply_mods(p)
        mn = p.data.materials[0].name if len(p.data.materials) else ''
        z = (rule(mn, centre(p)) if rule else None) or zones.get(mn, default)
        groups.setdefault(z.upper(), []).append(p)
    return [join(objs, f'{name}_wz{k}') for k, objs in sorted(groups.items())]


def uv_cyl(o, axis='z', a0=0.0, a1=1.0, turn=0.0):
    """wrap-around UVs for labels on round things (cigarettes, cans, bottles): u runs along the game axis from a0 (u=0)
    to a1 (u=1), v goes once round (from angle `turn`, radians, measured from game +x toward +y for axis z, from +x
    toward -z for axis y). Faces never straddle the seam."""
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    for poly in me.polygons:
        ls = []
        for li in poly.loop_indices:
            v = mw @ me.vertices[me.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            a, t = {'z': (math.atan2(gy, gx), gz), 'y': (math.atan2(-gz, gx), gy), 'x': (math.atan2(gy, -gz), gx)}[axis]
            ls.append([li, (t - a0) / (a1 - a0), (a - turn) / (2 * math.pi)])
        ref = ls[0][2]
        for e in ls:
            while e[2] - ref > 0.5: e[2] -= 1
            while e[2] - ref < -0.5: e[2] += 1
        for li, u, w in ls: uv[li].uv = (u, w)


def jitter(o, amount, seed=1, along_normal=True):
    """push every vertex in or out a random bit (fur, ash, crumbs, knobbly snow). apply modifiers first."""
    apply_mods(o)
    r = random.Random(seed)
    me = o.data
    for v in me.vertices:
        k = (r.random() * 2 - 1) * amount
        v.co += (v.normal * k) if along_normal else Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1))) * amount
    me.update()
    return o


def loft(centres, ring, m=None, name='loft', cap=True, up=(0, 1, 0), smooth_angle=60, close=(False, False)):
    """a skin through cross-sections along a path of game points (loaves, croissants, slippers, ducks). ring(i, t) returns
    the i-th section as a list of (up, side) offsets (game metres) in the frame at that point: up = the game `up`
    vector made square to the path, side = path x up. t = 0..1 along the path. close = (start, end): pinch that end to
    a point instead of a flat cap. Every section must have the same number of points. Returns the object; its faces
    know their station and slot (face index = station * n + slot) for per-face materials."""
    P = [Vector(c) for c in centres]
    n_s = len(P)
    U = Vector(up)
    rings = []
    bm = bmesh.new()
    for i, c in enumerate(P):
        t = (P[min(i + 1, n_s - 1)] - P[max(i - 1, 0)]).normalized()
        N = (U - t * t.dot(U)).normalized()
        B = t.cross(N)
        sec = ring(i, i / (n_s - 1))
        rings.append([bm.verts.new(gv(*(c + N * a + B * b))) for a, b in sec])
    k = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for j in range(k):
            jj = (j + 1) % k
            bm.faces.new((a[j], a[jj], b[jj], b[j]))
    for end, ring_v, i in ((0, rings[0], 0), (1, rings[-1], n_s - 1)):
        if close[end]:
            tip = bm.verts.new(gv(*P[i]))
            for j in range(k):
                jj = (j + 1) % k
                bm.faces.new((ring_v[j], ring_v[jj], tip) if end else (ring_v[jj], ring_v[j], tip))
        elif cap:
            bm.faces.new(ring_v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    smooth(o, smooth_angle)
    return o


def clone_scaled(objs, k, suffix='_s'):
    """copies of objects (own mesh data) scaled by k about the game origin: a thrown slipper is the held one x1.6"""
    out = []
    for o in objs:
        apply_mods(o)
        c = o.copy(); c.data = o.data.copy(); c.name = o.name + suffix
        _link(c)
        c.data.transform(o.matrix_world); c.matrix_world = Matrix.Identity(4)
        c.data.transform(Matrix.Scale(k, 4))
        c.parent = None
        out.append(c)
    return out
