# THE STORY CAST, the meshes half: imports each cast member's own Blender model (public/models/cast/c_<id>.glb, the
# web's), takes every part_<joint> mesh (not its lod or damage copies) into that joint's frame from cast_dump.mjs, gives
# each face one colour (its material's picture sampled at the face's middle, or its plain colour: an upload can't carry
# the pictures, and a face-sized sample keeps a pattern's look without any writing), adds the code meshes the web keeps
# (the face rig), and writes a dump in lore_dump's shape for lore_meshes.py.
# run: blender -b --factory-startup -P tools/roblox/lore_cast_meshes.py -- <cast_dump_dir> <out_dump_dir> ids...
# (then lore_meshes.py on <out_dump_dir> makes the uploads; the order of the whole pipeline: roblox/docs/LORE.md)
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Quaternion, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
src, out = os.path.abspath(argv[0]), os.path.abspath(argv[1])
ids = argv[2:]
os.makedirs(out, exist_ok=True)
GLB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'public', 'models', 'cast', 'c_%s.glb')

def lin2srgb(c): return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
def hexc(rgb): return ''.join('%02x' % max(0, min(255, round(v * 255))) for v in rgb[:3])

def mat_sampler(mat):
    """-> f(uv) -> 'rrggbb' (sRGB)"""
    base = (0.8, 0.8, 0.8)
    img = None
    if mat and mat.use_nodes:
        bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf:
            inp = bsdf.inputs['Base Color']
            base = tuple(lin2srgb(v) for v in inp.default_value[:3])
            if inp.is_linked:
                n = inp.links[0].from_node
                while n and n.type != 'TEX_IMAGE' and n.inputs and any(i.is_linked for i in n.inputs):
                    n = next(i for i in n.inputs if i.is_linked).links[0].from_node
                if n and n.type == 'TEX_IMAGE' and n.image: img = n.image
    if img is None:
        h = hexc(base)
        return lambda uv: h
    w, hgt = img.size
    px = list(img.pixels)  # RGBA floats, as stored (sRGB for these pictures)
    n = max(1, w * hgt)
    avg = [sum(px[i::4][:n]) / n for i in range(3)]
    def f(uv):
        u, v = uv[0] % 1.0, uv[1] % 1.0
        x, y = min(w - 1, int(u * w)), min(hgt - 1, int(v * hgt))
        i = (y * w + x) * 4
        # (a pattern sampled face by face, softened toward the picture's own average: the look without the noise)
        return hexc([px[i + c] * 0.55 + avg[c] * 0.45 for c in range(3)])
    return f

report = {}
for nid in ids:
    D = json.load(open(os.path.join(src, nid + '.json')))
    K, s = D['K'], D['scale']
    J = {j['name']: j for j in D['joints']}
    inv = {}
    for name, j in J.items():
        w = j['world']
        q = Quaternion((w[6], w[3], w[4], w[5]))
        inv[name] = (Vector(w[:3]), q.inverted())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=GLB % nid)
    pieces = {k: list(v) for k, v in D['pieces'].items()}
    for ob in list(bpy.context.scene.objects):
        if ob.type != 'MESH': continue
        p = ob
        while p and not p.name.startswith('part_'): p = p.parent
        if not p: continue
        nm = p.name[5:]
        joint = nm.split('__')[0].split('.')[0]
        tag = nm.split('__')[1] if '__' in nm else ''
        if tag.startswith('lod') or tag.startswith('dmg'): continue
        if joint not in J: continue
        dg = bpy.context.evaluated_depsgraph_get()
        eo = ob.evaluated_get(dg)
        me = eo.to_mesh()
        me.calc_loop_triangles()
        uvl = me.uv_layers.active
        samplers = [mat_sampler(m) for m in me.materials] or [lambda uv: 'cccccc']
        mw = ob.matrix_world
        jp, jq = inv[joint]
        lst = pieces.setdefault(joint, [])
        for tri in me.loop_triangles:
            vs = []
            for li in tri.loops:
                v = mw @ me.vertices[me.loops[li].vertex_index].co
                web = Vector((v.x, v.z, -v.y))  # Blender -> web (glTF) axes
                loc = jq @ (web - jp)
                vs.append(loc * (K * s))
            if uvl:
                uv = [0.0, 0.0]
                for li in tri.loops: uv[0] += uvl.data[li].uv[0] / 3; uv[1] += uvl.data[li].uv[1] / 3
            else: uv = (0.5, 0.5)
            mi = min(tri.material_index, len(samplers) - 1)
            col = samplers[mi](uv)
            lst.append([round(c, 4) for v in vs for c in (v.x, v.y, v.z)] + [col, 0])
        eo.to_mesh_clear()
    # the web's joint data in lore_dump's shape
    joints = [{ 'name': j['name'], 'parent': j['parent'], 'cf': j['cf'], 'pos': j['pos'], 'rot': j['rot'], 'order': j['order'], 'posScale': j['posScale'], 'moves': True } for j in D['joints']]
    allv = [c for t in (x for v in pieces.values() for x in v) for c in (t[1], )]
    ys = [t[i] for v in pieces.values() for t in v for i in (1, 4, 7)]
    data = { 'id': nid, 'name': nid, 'K': K, 'scale': s, 'tilt': D['tilt'], 'joints': joints, 'pieces': pieces, 'box': [[0, min(ys), 0], [0, max(ys), 0]] }
    json.dump(data, open(os.path.join(out, nid + '.json'), 'w'))
    report[nid] = { k: len(v) for k, v in pieces.items() }
print('CAST', json.dumps(report))
