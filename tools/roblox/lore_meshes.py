# THE HIDDEN NPCS -> uploads. lore_dump.mjs wrote each NPC's pieces in their joints' own frames (studs, web axes);
# this makes one .glb per NPC, one mesh per piece (a joint's solid parts; its glass apart), flat shaded, each face its
# web colour (a step calmer, the hub's quiet palette) as a baked vertex colour, and writes where each piece's middle sits
# in its joint's frame (a MeshPart lands at its mesh's middle).
# run: blender -b --factory-startup -P lore_meshes.py -- <dump_dir> <out_dir> [--preview]
import bpy, bmesh, sys, os, json, math, colorsys
from mathutils import Vector, Quaternion, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb

argv = sys.argv[sys.argv.index('--') + 1:]
src, out_dir = os.path.abspath(argv[0]), os.path.abspath(argv[1])
preview = '--preview' in argv
os.makedirs(out_dir, exist_ok=True)

def calm(h):
    # the web's loud colours a step quieter (less-colourful rule): very saturated ones lose a quarter of it
    r, g, b = rbxglb.hex_rgb(h)
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s > 0.55 and v > 0.35: s *= 0.78; v *= 0.93
    return rbxglb.rgb_hex(colorsys.hsv_to_rgb(hh, s, v))

def w2b(x, y, z): return Vector((x, -z, y))  # web (x, y, z) -> Blender (x, -z, y)

def make(name, tris):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); cols = []
    for t in tris:
        vs = [bm.verts.new(w2b(t[i], t[i + 1], t[i + 2])) for i in (0, 3, 6)]
        try: f = bm.faces.new(vs)
        except ValueError: continue
        cols.append(calm(t[9]))
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = False
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    mat = bpy.data.materials.new(name + '_mat'); mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF'); vc = mat.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
    mat.node_tree.links.new(vc.outputs['Color'], bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = 0.9
    me.materials.append(mat)
    rbxglb.bake_vertex_colours(ob, lambda p: cols[p.index])
    return ob

def centre(ob):
    lo = [min(v.co[i] for v in ob.data.vertices) for i in range(3)]; hi = [max(v.co[i] for v in ob.data.vertices) for i in range(3)]
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]; s = [hi[i] - lo[i] for i in range(3)]
    return [c[0], c[2], -c[1]], [s[0], s[2], s[1]]  # back to web axes

report = {}
for fn in sorted(os.listdir(src)):
    if not fn.endswith('.json'): continue
    D = json.load(open(os.path.join(src, fn))); nid = D['id']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs, info = [], {}
    for joint, tris in D['pieces'].items():
        for glass in (0, 1):
            ts = [t for t in tris if t[10] == glass]
            if not ts: continue
            name = f'{nid}_{joint}' + ('_glass' if glass else '')
            ob = make(name, ts); objs.append(ob)
            c, s = centre(ob)
            info[name] = {'joint': joint, 'centre': [round(v, 4) for v in c], 'size': [round(v, 4) for v in s], 'glass': glass, 'tris': len(ob.data.polygons)}
    if preview:
        # assemble at rest (joint chain) just for a look
        J = {j['name']: j for j in D['joints']}
        world = {}
        def wcf(n):
            if n in world: return world[n]
            j = J[n]; x, y, z, qx, qy, qz, qw = j['cf']
            m = Matrix.Translation(Vector((x, y, z))) @ Quaternion((qw, qx, qy, qz)).to_matrix().to_4x4()
            world[n] = (wcf(j['parent']) @ m) if j['parent'] else m
            return world[n]
        conv = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # web -> Blender
        for ob in objs:
            jm = wcf(info[ob.name]['joint'])
            ob.matrix_world = conv @ jm @ conv.inverted()
    report[nid] = info
    if preview:
        sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 20; sc.cycles.device = 'CPU'
        sc.render.resolution_x, sc.render.resolution_y = 700, 800; sc.view_settings.view_transform = 'Standard'
        w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.3, 0.31, 0.34, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.7; sc.world = w
        sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(50), 0, math.radians(-30)); sc.collection.objects.link(sun)
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
        bpy.context.view_layer.update()
        pts = [ob.matrix_world @ v.co for ob in objs for v in ob.data.vertices]
        lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
        mid = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)); size = max(hi[i] - lo[i] for i in range(3))
        eye = mid + Vector((0.45, 1.0, 0.35)).normalized() * size * 2.1
        cam.location = eye; cam.rotation_euler = (mid - eye).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 50
        sc.render.filepath = os.path.join(out_dir, f'{nid}_preview.png'); bpy.ops.render.render(write_still=True)
        for ob in objs: ob.matrix_world = Matrix.Identity(4)
    rbxglb.turn_for_roblox(objs)
    path = os.path.join(out_dir, f'lore_{nid}.glb'); rbxglb.export_glb(path, vertex_colours=True)
    report[nid]['_file'] = path
json.dump(report, open(os.path.join(out_dir, 'pieces.json'), 'w'), indent=1)
print('LORE', json.dumps({k: len(v) for k, v in report.items()}))
