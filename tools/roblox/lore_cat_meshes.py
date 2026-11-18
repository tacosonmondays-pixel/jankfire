# THE BOARD OF DIRECTORS -> uploads (the web's five hidden cats; lore_cat_dump.mjs wrote them). The owner's rule for
# creatures (chunky-model-style, 18 Nov): ONE cohesive mesh with real joins, never stacked primitives. So each moving
# piece's "solid" triangles (the web's own spheres and cones) are voxel-remeshed into one smooth skin, softened, thinned,
# and painted from the web's parts: the nearest "paint" part (stripes, the forehead M, calico patches) if one lies right
# on the fur there, else the nearest solid part. Eyes, nose and the executive touches (crown, glasses, tie, lanyard) stay
# as they were, on the surface. Gremlin's box stays a box. One .glb per cat, one mesh per joint, vertex colours.
# run: blender -b --factory-startup -P tools/roblox/lore_cat_meshes.py -- <dump_dir> <out_dir> [--preview]
import bpy, bmesh, sys, os, json, math, colorsys
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb

argv = sys.argv[sys.argv.index('--') + 1:]
src, out_dir = os.path.abspath(argv[0]), os.path.abspath(argv[1])
preview = '--preview' in argv
os.makedirs(out_dir, exist_ok=True)
VOXEL = {'body': 0.045, 'neck': 0.03, 'tailBase': 0.03}
FACES = {'body': 3200, 'neck': 2600, 'tailBase': 700}
PAINT_REACH = 0.09  # studs: a paint part this close to the skin colours it

def calm(h):
    r, g, b = rbxglb.hex_rgb(h)
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s > 0.55 and v > 0.35: s *= 0.78; v *= 0.93
    return rbxglb.rgb_hex(colorsys.hsv_to_rgb(hh, s, v))

def w2b(x, y, z): return Vector((x, -z, y))

def tris_obj(name, tris):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    for t in tris:
        vs = [bm.verts.new(w2b(t[i], t[i + 1], t[i + 2])) for i in (0, 3, 6)]
        try: bm.faces.new(vs)
        except ValueError: pass
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob

def bvh_of(tris):
    verts, polys = [], []
    for t in tris:
        b = len(verts)
        verts += [w2b(t[i], t[i + 1], t[i + 2]) for i in (0, 3, 6)]
        polys.append((b, b + 1, b + 2))
    return BVHTree.FromPolygons(verts, polys) if polys else None

def material(ob):
    mat = bpy.data.materials.new(ob.name + '_mat'); mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF'); vc = mat.node_tree.nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Color'
    mat.node_tree.links.new(vc.outputs['Color'], bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = 0.85
    ob.data.materials.append(mat)

def skin(name, solid, paint, joint):
    """one cohesive mesh from the solid parts, painted from the paint + solid parts"""
    ob = tris_obj(name, solid)
    bpy.context.view_layer.objects.active = ob
    m = ob.modifiers.new('remesh', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = VOXEL.get(joint, 0.04); m.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier='remesh')
    m = ob.modifiers.new('smooth', 'CORRECTIVE_SMOOTH'); m.iterations = 6; m.smooth_type = 'LENGTH_WEIGHTED'
    bpy.ops.object.modifier_apply(modifier='smooth')
    n = len(ob.data.polygons)
    if n > FACES.get(joint, 2000):
        m = ob.modifiers.new('dec', 'DECIMATE'); m.ratio = FACES.get(joint, 2000) / n
        bpy.ops.object.modifier_apply(modifier='dec')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(); bpy.ops.object.mode_set(mode='OBJECT')
    sb, pb = bvh_of(solid), bvh_of(paint)
    cols = []
    for p in ob.data.polygons:
        c = p.center
        col = None
        if pb:
            hit = pb.find_nearest(c)
            if hit[0] is not None and hit[3] < PAINT_REACH: col = paint[hit[2]][9]
        if col is None:
            hit = sb.find_nearest(c)
            col = solid[hit[2]][9] if hit[0] is not None else 'cccccc'
        cols.append(calm(col))
    for p in ob.data.polygons: p.use_smooth = True
    material(ob)
    rbxglb.bake_vertex_colours(ob, lambda p: cols[p.index])
    return ob

def plain(name, tris, smooth=False):
    ob = tris_obj(name, tris)
    cols = [calm(t[9]) for t in tris][:len(ob.data.polygons)]
    for p in ob.data.polygons: p.use_smooth = smooth
    material(ob)
    rbxglb.bake_vertex_colours(ob, lambda p: cols[p.index] if p.index < len(cols) else 'cccccc')
    return ob

def centre(ob):
    lo = [min(v.co[i] for v in ob.data.vertices) for i in range(3)]; hi = [max(v.co[i] for v in ob.data.vertices) for i in range(3)]
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    return [round(c[0], 4), round(c[2], 4), round(-c[1], 4)]

report = {}
for fn in sorted(os.listdir(src)):
    if not fn.endswith('.json'): continue
    D = json.load(open(os.path.join(src, fn))); nid = D['id']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs, info = [], {}
    for joint, tris in D['pieces'].items():
        name = f'{nid}_{joint}'
        solid = [t for t in tris if t[10] == 'solid']
        paint = [t for t in tris if t[10] == 'paint']
        detail = [t for t in tris if t[10] == 'detail']
        prop = [t for t in tris if t[10] == 'prop']
        parts = []
        if solid: parts.append(skin(name, solid, paint, joint))
        if detail: parts.append(plain(name + '_d', detail))
        if prop: parts.append(plain(name, prop))
        if not parts: continue
        if len(parts) > 1:  # one mesh per joint: the skin and its details together
            bpy.ops.object.select_all(action='DESELECT')
            for o in parts: o.select_set(True)
            bpy.context.view_layer.objects.active = parts[0]
            bpy.ops.object.join()
        ob = parts[0]; ob.name = name
        objs.append(ob)
        info[name] = {'joint': 'npc' if joint == 'box' else joint, 'centre': centre(ob), 'tris': len(ob.data.polygons)}
    if preview:
        J = {j['name']: j for j in D['joints']}; world = {}
        def wcf(n):
            if n in world: return world[n]
            j = J[n]; x, y, z, qx, qy, qz, qw = j['cf']
            m = Matrix.Translation(Vector((x, y, z))) @ Quaternion((qw, qx, qy, qz)).to_matrix().to_4x4()
            world[n] = (wcf(j['parent']) @ m) if j['parent'] else m
            return world[n]
        conv = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
        for ob in objs: ob.matrix_world = conv @ wcf(info[ob.name]['joint']) @ conv.inverted()
        bpy.context.view_layer.update()
        pts = [ob.matrix_world @ v.co for ob in objs for v in ob.data.vertices]
        lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
        mid = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)); size = max(hi[i] - lo[i] for i in range(3))
        sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 20; sc.cycles.device = 'CPU'
        sc.render.resolution_x, sc.render.resolution_y = 700, 600; sc.view_settings.view_transform = 'Standard'
        w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.3, 0.31, 0.34, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.7; sc.world = w
        sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(50), 0, math.radians(-30)); sc.collection.objects.link(sun)
        cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
        eye = mid + Vector((0.6, 1.0, 0.4)).normalized() * size * 1.9
        cam.location = eye; cam.rotation_euler = (mid - eye).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 50
        sc.render.filepath = os.path.join(out_dir, f'{nid}_preview.png'); bpy.ops.render.render(write_still=True)
        for ob in objs: ob.matrix_world = Matrix.Identity(4)
    report[nid] = info
    rbxglb.turn_for_roblox(objs)
    rbxglb.export_glb(os.path.join(out_dir, f'lore_{nid}.glb'), vertex_colours=True)
json.dump(report, open(os.path.join(out_dir, 'pieces.json'), 'w'), indent=1)
print('CATS', json.dumps({k: {n: v['tris'] for n, v in r.items()} for k, r in report.items()}))
