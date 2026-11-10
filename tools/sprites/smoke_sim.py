# Bakes a real smoke simulation (Blender Mantaflow) into the soft smoke flipbook: public/sprites/puffsoft.png
# Run: blender52 -b -P tools/sprites/smoke_sim.py [-- <res> <samples>]
# A burst of smoke from a ball, stirred by turbulence, rising, thinning and dissolving. 36 frames, rendered side-on with
# a see-through background (Cycles, lit from the top left like the comic sheets), packed 6x6: R = shading, A = how thick.
import bpy, sys, os, math, tempfile
import numpy as np

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
RES = int(args[0]) if len(args) > 0 else 56
SAMPLES = int(args[1]) if len(args) > 1 else 24
N, CELL, STEP, START = 6, 96, 2, 3  # 6x6 frames of 96 px; every 2nd sim frame from frame 3
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../public/sprites/puffsoft.png')
tmp = tempfile.mkdtemp(prefix='jfsmoke')

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, START + N * N * STEP

# the box the smoke lives in
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 2.1)); dom = bpy.context.object; dom.scale = (4.6, 4.6, 4.6)
dm = dom.modifiers.new('fluid', 'FLUID'); dm.fluid_type = 'DOMAIN'
D = dm.domain_settings
D.domain_type = 'GAS'; D.resolution_max = RES; D.cache_type = 'REPLAY'; D.cache_directory = os.path.join(tmp, 'cache')
D.vorticity = 0.35; D.alpha = 0.35; D.beta = 0.6  # a little buoyancy: it lifts, it doesn't rocket
D.use_dissolve_smoke = True; D.dissolve_speed = 46; D.use_dissolve_smoke_log = False
D.use_adaptive_domain = False
for a in ('use_collision_border_front', 'use_collision_border_back', 'use_collision_border_left', 'use_collision_border_right', 'use_collision_border_top'):
    if hasattr(D, a): setattr(D, a, False)  # smoke leaves through the walls instead of piling up on them

# where it comes from: a ball that puffs for a few frames
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.55, subdivisions=2, location=(0, 0, 1.0)); src = bpy.context.object
fm = src.modifiers.new('fluid', 'FLUID'); fm.fluid_type = 'FLOW'
F = fm.flow_settings
F.flow_type = 'SMOKE'; F.flow_behavior = 'INFLOW'; F.density = 1.6; F.temperature = 0.6
F.use_initial_velocity = True; F.velocity_normal = 2.6; F.velocity_random = 0.8 if hasattr(F, 'velocity_random') else 0
F.use_inflow = True; F.keyframe_insert('use_inflow', frame=1)
F.use_inflow = False; F.keyframe_insert('use_inflow', frame=9)
src.hide_render = True

# something to stir it
bpy.ops.object.effector_add(type='TURBULENCE', location=(0, 0, 2)); tb = bpy.context.object
tb.field.strength = 2.2; tb.field.size = 0.9; tb.field.flow = 0.4; tb.field.noise = 1.0

# how it looks: white smoke
mat = bpy.data.materials.new('smoke'); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
vol = nt.nodes.new('ShaderNodeVolumePrincipled'); out = nt.nodes.new('ShaderNodeOutputMaterial')
vol.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1); vol.inputs['Density'].default_value = 9.0
if 'Anisotropy' in vol.inputs: vol.inputs['Anisotropy'].default_value = 0.2
nt.links.new(vol.outputs['Volume'], out.inputs['Volume'])
dom.data.materials.append(mat)

# light from the top left (towards the camera a bit), a soft fill so the shade isn't black
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 5.0; so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so)
so.rotation_euler = (math.radians(50), math.radians(-30), math.radians(-20))
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.6, 0.7, 1); world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55

cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = 4.7
co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
co.location = (0, -12, 2.15); co.rotation_euler = (math.radians(90), 0, 0)

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = False
sc.cycles.volume_step_rate = 1.0; sc.cycles.volume_bounces = 1; sc.cycles.max_bounces = 2
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = CELL; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'Standard'

sheet = np.zeros((N * CELL, N * CELL, 4), dtype=np.float32)
k = 0
for f in range(1, sc.frame_end + 1):
    sc.frame_set(f)  # (replay cache: stepping through the frames in order is the bake)
    if f < START or (f - START) % STEP or k >= N * N: continue
    path = os.path.join(tmp, f'f{k:02d}.png'); sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path); px = np.array(img.pixels[:], dtype=np.float32).reshape(CELL, CELL, 4); bpy.data.images.remove(img)
    a = px[:, :, 3]
    lum = np.where(a > 0.003, (px[:, :, 0] * 0.3 + px[:, :, 1] * 0.59 + px[:, :, 2] * 0.11) / np.maximum(a, 0.003), 0)  # (the render is premultiplied)
    edge = np.clip((0.5 - np.abs(np.linspace(-0.5, 0.5, CELL))) * 10, 0, 1); a = a * edge[None, :] * edge[:, None]  # nothing touches the frame's edge
    cell = np.zeros((CELL, CELL, 4), dtype=np.float32); cell[:, :, 0] = np.clip(lum, 0, 1); cell[:, :, 3] = np.clip(a * 1.15, 0, 1)
    r, c = k // N, k % N
    sheet[(N - 1 - r) * CELL:(N - r) * CELL, c * CELL:(c + 1) * CELL] = cell  # (image rows run bottom-up)
    print(f'frame {f} -> cell {k}, cover {float((a > 0.05).mean()):.2f}', flush=True)
    k += 1
img = bpy.data.images.new('sheet', N * CELL, N * CELL, alpha=True); img.alpha_mode = 'STRAIGHT'
img.pixels[:] = sheet.reshape(-1); img.filepath_raw = OUT; img.file_format = 'PNG'; img.save()
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'kB')
