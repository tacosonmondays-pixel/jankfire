# Shared bits for the weather kits (tools/blender/weather/make_*.py): game space <-> blender, colours, an atlas painted
# in numpy, materials the glTF exporter keeps, meshes, LINEAR transform clips, and the export (with a plain rest pose).
# make_rain.py predates this file and keeps its own copies (its glb stays byte-for-byte what shipped).
import bpy, math, os, json, struct
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
FPS = 30


def gv(x, y, z): return Vector((x, -z, y))  # game (x right, y up, -z forward) -> blender (z up)


def lin(h):
    c = [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]


def srgb(h): return [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]


def mix(c0, c1, t):
    t = np.clip(t, 0, 1)[..., None]
    return np.array(srgb(c0), np.float32) * (1 - t) + np.array(srgb(c1), np.float32) * t


def solid(col, shape): return np.broadcast_to(np.array(srgb(col), np.float32), shape + (3,))


class Atlas:
    """one square texture, regions painted by fn(u, v, w, h) -> rgba (u, v 0..1, v up)"""
    def __init__(self, size, regions):
        self.S, self.R = size, regions
        self.A = np.zeros((size, size, 4), np.float32)

    def paint(self, name, fn):
        x0, y0, w, h = self.R[name]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        self.A[y0:y0 + h, x0:x0 + w] = fn((xx + 0.5) / w, (yy + 0.5) / h, w, h)

    def uv(self, name, u, v):
        x0, y0, w, h = self.R[name]
        return ((x0 + u * w) / self.S, (y0 + v * h) / self.S)

    def image(self, name):
        img = bpy.data.images.new(name, self.S, self.S, alpha=True)
        img.colorspace_settings.name = 'sRGB'
        img.pixels.foreach_set(self.A.ravel()); img.update(); img.pack(); img.alpha_mode = 'STRAIGHT'
        return img


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, 60
    return sc


def material(name, img=None, color=0xffffff, rough=0.5, metal=0.0, emit=0.0, clip=False, vcol=False, double=True):
    """principled: base = texture or vertex colour or flat colour; emit = that same colour glowing x emit; clip = alpha
    MASK (a Round node: the exporter's cutoff 0.5); double = both sides (single-sided for the inked hulls)"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = lin(color) + [1]
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.use_backface_culling = not double
    src = None
    if img is not None:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Linear'; src = t.outputs['Color']
        if clip:
            rd = nt.nodes.new('ShaderNodeMath'); rd.operation = 'ROUND'
            nt.links.new(t.outputs['Alpha'], rd.inputs[0]); nt.links.new(rd.outputs[0], b.inputs['Alpha'])
            m.surface_render_method = 'DITHERED'
    elif vcol:
        a = nt.nodes.new('ShaderNodeVertexColor'); a.layer_name = 'Col'; src = a.outputs['Color']
    if src is not None: nt.links.new(src, b.inputs['Base Color'])
    if emit:
        if src is not None: nt.links.new(src, b.inputs['Emission Color'])
        else: b.inputs['Emission Color'].default_value = lin(color) + [1]
        b.inputs['Emission Strength'].default_value = emit
    return m


def mesh_obj(sc, root, name, verts, faces, mat, uvs=None, cols=None, pcols=None, smooth=False):
    """verts: game-space Vectors; uvs: one (u, v) per vertex or None; cols: one 0xRRGGBB per face (flat) or None;
    pcols: one per vertex instead (smooth puffs: no split vertices, a quarter of the file)"""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(gv(*v)) for v in verts], [], faces)
    if uvs:  # (no texture, no uvs: the vertex-coloured puffs)
        uvl = me.uv_layers.new(name='UVMap')
        for f in me.polygons:
            for k in range(len(f.vertices)): uvl.data[f.loop_indices[k]].uv = uvs[faces[f.index][k]]
    if cols is not None:
        ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
        for f in me.polygons:
            c = srgb(cols[f.index]) + [1.0]
            for li in f.loop_indices: ca.data[li].color_srgb = c
    if pcols is not None:
        ca = me.color_attributes.new('Col', 'BYTE_COLOR', 'POINT')
        for i, c in enumerate(pcols): ca.data[i].color_srgb = srgb(c) + [1.0]
    me.materials.append(mat)
    me.validate(); me.update()
    for p in me.polygons: p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob); ob.parent = root
    return ob


def clip(ob, path, frames, name):
    """keys [(frame, value)] on ob.<path>, LINEAR between them, the action named `name` (= the glTF animation's name)"""
    from bpy_extras import anim_utils
    for f, val in frames:
        setattr(ob, path, val)
        ob.keyframe_insert(path, frame=f)
    ad = ob.animation_data
    ad.action.name = name
    cb = anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    for fc in cb.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'


def ico(r, sub=1):
    """unit icosphere (verts, tris), sub = subdivisions"""
    t = (1 + 5 ** 0.5) / 2
    V = [Vector(v).normalized() for v in ((-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1))]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(sub):
        mids, F1 = {}, []
        def mid(i, j):
            k = (min(i, j), max(i, j))
            if k not in mids: V.append((V[i] + V[j]).normalized()); mids[k] = len(V) - 1
            return mids[k]
        for (i, j, l) in F:
            a, b, c = mid(i, j), mid(j, l), mid(l, i); F1 += [(i, a, c), (j, b, a), (l, c, b), (a, b, c)]
        F = F1
    return [v * r for v in V], F


def export(sc, root, out, meta):
    """glb with every clip as its own animation; then every node's rest pose put back to plain (the exporter writes the
    pose at frame 0, which for a clip that starts hidden is scale 0)"""
    root['jf'] = json.dumps(meta)
    for ob in root.children:
        if ob.data: ob.data.name = ob.name
    sc.frame_set(0)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for o in bpy.context.view_layer.objects: o.select_set(o == root or o.parent == root)
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_apply=True, export_extras=True,
                              export_yup=True, export_texcoords=True, export_normals=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_lights=False, export_cameras=False, export_animations=True,
                              export_animation_mode='ACTIONS', export_force_sampling=False, export_frame_range=False,
                              export_anim_single_armature=False, export_def_bones=False, export_optimize_animation_size=False)
    with open(out, 'rb') as fh: raw = fh.read()
    jl = struct.unpack_from('<I', raw, 12)[0]
    gj = json.loads(raw[20:20 + jl])
    for nd in gj['nodes']:
        if nd.get('name') != root.name:
            for k in ('translation', 'rotation', 'scale'): nd.pop(k, None)
    js = json.dumps(gj, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
    rest = raw[20 + jl:]
    with open(out, 'wb') as fh:
        fh.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + len(rest)))
        fh.write(struct.pack('<II', len(js), 0x4E4F534A)); fh.write(js); fh.write(rest)
    tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in root.children if o.data}
    print('JF_EXPORT', os.path.basename(out), os.path.getsize(out) // 1024, 'KB', json.dumps(tris))
