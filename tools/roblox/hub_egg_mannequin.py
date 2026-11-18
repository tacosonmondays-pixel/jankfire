# THE HUB EGG MANNEQUIN (18 Nov 2026): the web game's player, "with the exact crusty look" (the owner), hidden in Hub v3.
# The geometry is NOT redrawn here: tools/roblox/hub_egg_dump.mjs runs the web's own buildCharacter + clothes.js (default
# look: Sash + Shorts, the default skin, the first player colour, pink) and the character screen's plinth, and writes
# every triangle with its colour. This script only turns those triangles into an upload:
#   - 1 web metre (mannequin unit) = K studs; web (x, y, z) -> Blender (x, -z, y), then rbxglb.turn_for_roblox, so the
#     upload lands in Roblox with the web's own axes (front = -Z, the way the web's players face)
#   - flat shaded (the web's Lambert flatShading), each face its web colour as a baked vertex colour (rbxglb route for
#     models nobody repaints: Color white in Studio)
#   - three pieces: "egg_body" (the mannequin), "egg_stand" (the plinth) and "egg_shell", the outline everyone else saw
#     on a web player (remote.js: each body piece 1.12x about its middle, inside out, in the player's colour)
# Nothing is cleaned up: 6-sided limbs, 6x4 ball joints, the egg head with its mould seam, the price tag on the arm.
# run: blender -b --factory-startup -P tools/roblox/hub_egg_mannequin.py -- roblox/assets/hub-egg/mannequin.json <out_dir> [--preview]
import bpy, bmesh, sys, os, json, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxglb

K = 3.0  # studs per web metre: a 1.96 m mannequin -> 5.9 studs, about a Roblox player; the plinth adds 1.65

argv = sys.argv[sys.argv.index('--') + 1:]
src, out_dir = argv[0], argv[1]
preview = '--preview' in argv
os.makedirs(out_dir, exist_ok=True)
D = json.load(open(src))

bpy.ops.wm.read_factory_settings(use_empty=True)


def piece(name, tris):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    cols = []
    for t in tris:
        vs = [bm.verts.new(Vector((t[i] * K, -t[i + 2] * K, t[i + 1] * K))) for i in (0, 3, 6)]
        try:
            f = bm.faces.new(vs)
        except ValueError:
            continue
        f.smooth = False
        cols.append(t[9])
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons: p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    mat = bpy.data.materials.new(name + '_mat')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    vc = mat.node_tree.nodes.new('ShaderNodeVertexColor')
    vc.layer_name = 'Color'
    mat.node_tree.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.9
    me.materials.append(mat)
    rbxglb.bake_vertex_colours(ob, lambda p: cols[p.index])
    return ob


body = piece('egg_body', [t for t in D['tris'] if t[10] == 'body'])
stand = piece('egg_stand', [t for t in D['tris'] if t[10] == 'stand'])
shell = piece('egg_shell', [t for t in D['tris'] if t[10] == 'shell'])
objs = [body, stand, shell]
report = {}
for o in objs:
    lo = [min(v.co[i] for v in o.data.vertices) for i in range(3)]
    hi = [max(v.co[i] for v in o.data.vertices) for i in range(3)]
    # (Roblox frame: x = Blender x, y = Blender z, z = -Blender y)
    report[o.name] = {'tris': len(o.data.polygons), 'lo': [lo[0], lo[2], -hi[1]], 'hi': [hi[0], hi[2], -lo[1]]}

if preview:  # a Cycles still before the upload (the colours as Blender reads the vertex colours)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.device = 'CPU'
    try: sc.cycles.use_denoising = True
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = 900, 1100
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.32, 0.33, 0.36, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.6
    sc.world = w
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.2
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35)); sc.collection.objects.link(sun)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = 50
    # front three-quarter: the web's front is -Z (Roblox), = Blender +Y
    tgt = Vector((0, 0, 3.0)); eye = Vector((5.5, 13.5, 4.6))
    cam.location = eye
    cam.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(out_dir, 'egg_preview.png')
    bpy.ops.render.render(write_still=True)

rbxglb.turn_for_roblox(objs)
path = os.path.join(out_dir, 'hub_egg.glb')
size = rbxglb.export_glb(path, vertex_colours=True)
report['file'] = path; report['bytes'] = size; report['K'] = K
json.dump(report, open(os.path.join(out_dir, 'hub_egg.json'), 'w'), indent=1)
print('HUBEGG', json.dumps(report))
