# cut the four old cabanas (and their daybeds) out of the web game's pool deck model, so the structure pass's new
# cabanas can stand there. then run export_models.py on the result (it becomes the arch_pooldeck template).
# run: blender -b --factory-startup -P tools/roblox/cut_cabanas.py -- public/models/arch/pooldeck.glb <out pooldeck.glb> [preview.jpg]
import bpy, bmesh, sys, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
src, dst = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
# the cabanas' boxes in the file's own frame (Blender: x right, y = -file z, z up), a little over 13.4 studs square
XS = [(-18.3, -13.7), (13.7, 18.3)]
YS = [(-11.3, -6.7), (-26.8, -22.2)]
ZMIN = -3.995  # (the deck's top is z -4.0)
PAD, HIGH = 0.55, -2.2   # the roofs overhang the posts: round each box, only what is high up goes
KEEP_HIGH = ('pd_alu', 'pd_lamp', 'pd_neon')   # the string lights and their poles pass close by
def inside(c, name):
    if c.z < ZMIN: return False
    if any(a <= c.x <= b for a, b in XS) and any(a <= c.y <= b for a, b in YS): return True
    if c.z < HIGH or any(k in name for k in KEEP_HIGH): return False
    return any(a - PAD <= c.x <= b + PAD for a, b in XS) and any(a - PAD <= c.y <= b + PAD for a, b in YS)
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH': continue
    bm = bmesh.new(); bm.from_mesh(o.data)
    mw = o.matrix_world
    kill = [f for f in bm.faces if inside(mw @ f.calc_center_median(), o.name)]
    n = len(bm.faces)
    if kill:
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        bm.to_mesh(o.data)
    print('CUT %s: %d of %d faces' % (o.name, len(kill), n))
    left = len(bm.faces)
    bm.free()
    if left == 0:
        print('EMPTY, removed', o.name); bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.export_scene.gltf(filepath=dst, export_format='GLB', use_selection=False, export_apply=False, export_animations=False, export_yup=True, export_extras=True)
print('WROTE', dst)
if len(argv) > 2:
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 30
    cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam)
    cam.location = (-2, -45, 12)
    d = Vector((-8, -17, -3)) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0
    so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), 0, math.radians(-30))
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.4, 0.45, 0.55, 1); sc.world = w
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1500, 800
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'JPEG'; sc.render.filepath = argv[2]
    bpy.ops.render.render(write_still=True)
