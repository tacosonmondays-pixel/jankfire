# preview renders of a hub kit .glb before it is uploaded (Cycles CPU): the kit painted from its piece names, turned
# back from rbxglb's pre-turn, a low warm sun from the south-west and a dusk sky; cameras in the SITE frame
# (x east, y up, z south). blender -b --factory-startup -P still_preview.py -- <kit.glb> <out_dir> [shot ...]
import bpy, sys, os, math
from mathutils import Vector, Matrix
args = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = args[0], args[1]
WANT = args[2:]
os.makedirs(OUT, exist_ok=True)
SHOTS = {
    'spawn': ((0, 5.6, 27), (0, 13, -40), 30),
    'g_spawn': ((0, 5.4, 27), (0, 13, -40), -70),
    'g_west': ((-26, 6, 18), (34, 10, -16), -70),
    'g_gym': ((60, 8.4, 30), (110, 12, -10), -70),
    'g_well': ((0, 5.4, -40), (0, 12, -116), -70),
    'g_br_spawn': ((0, 5.4, 106), (0, 14, 0), -70),
    'g_br_w': ((14, 5.4, 82), (-60, 10, 66), -70),
    'g_br_e': ((-14, 5.4, 82), (60, 10, 66), -70),
    'g_br_up': ((0, 4, 96), (0, 30, 77), -70),
    'g_br_n': ((0, 5.4, 46), (0, 12, 110), -70),
    'g_well_w': ((14, 5.4, -58), (-60, 10, -84), -70),
    'g_well_e': ((-14, 5.4, -58), (60, 10, -84), -70),
    'g_well_up': ((0, 4, -50), (0, 40, -70), -70),
    'g_well_back': ((0, 5.4, -100), (0, 14, 0), -70),
    'g_cy_lounge': ((-13, 3, 4), (-13, 1, -60), -70),
    'g_cy_armory': ((13, 3, 4), (13, 2, -70), -70),
    'g_cy_face': ((-12, 14, 44), (4, 30, -4), -70),
    'aerial': ((95, 95, 110), (0, 8, -30), 26),
    'bore': ((0, 6.5, -32), (0, 8, -140), 22),
    'back': ((-6, 6, -120), (0, 16, 0), 24),
    'west': ((-26, 6, 18), (34, 10, -16), 24),
    'gymdoor': ((-14, 6, 6), (50, 8, 0), 24),
    'cy_spawn': ((0, 5.6, 118), (0, 16, 0), 30),
    'cy_transept': ((0, 6, 36), (0, 32, 0), 22),
    'cy_aerial': ((90, 100, 110), (0, 20, 10), 26),
    'cy_face': ((-12, 14, 44), (4, 30, -4), 24),
}
def V(x, y, z): return Vector((x, -z, y))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        o.matrix_world = Matrix.Rotation(math.pi, 4, 'Z') @ o.matrix_world
def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
mats = {}
for o in bpy.context.scene.objects:
    if o.type != 'MESH': continue
    name = o.data.name if '__' in o.data.name else o.name
    try:
        kind, hexc = name.split('__')[1].split('_')[:2]
        hexc = hexc[:6]
    except Exception:
        kind, hexc = 'plastic', 'a3a2a5'
    key = kind + hexc
    if key not in mats:
        m = bpy.data.materials.new(key); m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']
        c = [lin(int(hexc[i:i + 2], 16) / 255) for i in (0, 2, 4)]
        b.inputs['Base Color'].default_value = (c[0], c[1], c[2], 1)
        b.inputs['Roughness'].default_value = 0.8 if kind in ('slate', 'concrete') else 0.55
        if kind == 'neon':
            b.inputs['Emission Color'].default_value = (c[0], c[1], c[2], 1); b.inputs['Emission Strength'].default_value = 6
        if kind == 'metal':
            b.inputs['Metallic'].default_value = 0.85; b.inputs['Roughness'].default_value = 0.38
        if kind == 'glass':
            b.inputs['Alpha'].default_value = 0.35; b.inputs['Roughness'].default_value = 0.1
        mats[key] = m
    o.data.materials.clear(); o.data.materials.append(mats[key])
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
nt = w.node_tree; sky = nt.nodes.new('ShaderNodeTexSky')
try:
    sky.sky_type = 'NISHITA'
except Exception:
    pass
try:
    sky.sun_elevation = math.radians(16); sky.sun_rotation = math.radians(225)
except Exception:
    pass
nt.links.new(sky.outputs['Color'], nt.nodes['Background'].inputs['Color'])
nt.nodes['Background'].inputs['Strength'].default_value = 0.35
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0; sun.angle = math.radians(1.5); sun.color = (1.0, 0.86, 0.7)
so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so)
# light from the south-west (site), 18 deg up: a vector pointing FROM the scene TO the sun, then the lamp points back
d = V(-math.cos(math.radians(18)) * 0.6, math.sin(math.radians(18)), math.cos(math.radians(18)) * 0.8).normalized()
so.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
fill = bpy.data.lights.new('fill', 'SUN'); fill.energy = 0.35; fill.color = (0.7, 0.8, 1.0)
fo = bpy.data.objects.new('fill', fill); sc.collection.objects.link(fo); fo.rotation_euler = (math.radians(20), 0, math.radians(30))
cd = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cd); sc.collection.objects.link(co); sc.camera = co
cd.clip_end = 3000
for name, (eye, look, lens) in SHOTS.items():
    if WANT and name not in WANT: continue
    if lens < 0:  # (a game camera: vertical FOV in degrees, Roblox's 4:3 photo)
        cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(-lens); sc.render.resolution_x, sc.render.resolution_y = 1000, 750
    else:
        cd.sensor_fit = 'AUTO'; cd.lens = lens; sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    co.location = V(*eye)
    co.rotation_euler = (V(*look) - V(*eye)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, 'pv_' + name + '.png')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', name)
