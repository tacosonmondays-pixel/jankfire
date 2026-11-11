# A one-shot explosion flipbook from Blender, without the fluid solver: a ball of noise volume that bursts out white-hot,
# cools through yellow and orange to red, and is left as rolling dark smoke that rises and thins. Cycles, see-through
# film, 64 frames packed 8x8 into public/sprites/boom.png (premultiplied colour + alpha).
# Run: blender52 -b -P tools/sprites/blender/explosion_flipbook.py [-- <cell px> <samples>]
import bpy, sys, os, math, tempfile
import numpy as np
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CELL = int(args[0]) if args else 96; SAMPLES = int(args[1]) if len(args) > 1 else 32
ONLY = [int(x) for x in args[2].split(',')] if len(args) > 2 else None  # test: just these frames
N = 8; FR = N * N
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../public/sprites/boom.png')
tmp = tempfile.mkdtemp(prefix='jfboom')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, FR
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0)); box = bpy.context.object; box.scale = (2.4, 2.4, 2.4)
mat = bpy.data.materials.new('boom'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
N_ = nt.nodes.new; L = nt.links.new
def val(keys):  # a number that changes over the frames: [(frame, value), ...], straight lines between
    n = N_('ShaderNodeValue')
    for f, v in keys: n.outputs[0].default_value = v; n.outputs[0].keyframe_insert('default_value', frame=f)
    return n.outputs[0]
def m(op, a, b=None, vb=None):
    n = N_('ShaderNodeMath'); n.operation = op; L(a, n.inputs[0]) if not isinstance(a, float) else setattr(n.inputs[0], 'default_value', a)
    if b is not None: L(b, n.inputs[1])
    elif vb is not None: n.inputs[1].default_value = vb
    return n.outputs[0]
co = N_('ShaderNodeTexCoord')
# the cloud climbs a little as it cools
rise = val([(1, 0.0), (FR, -0.16)]); comb = N_('ShaderNodeCombineXYZ'); L(rise, comb.inputs['Z'])
pos = N_('ShaderNodeVectorMath'); pos.operation = 'ADD'; L(co.outputs['Object'], pos.inputs[0]); L(comb.outputs[0], pos.inputs[1])
# bend the space it lives in with slow noise, so the outline is never a ball and the smoke curls
nw = N_('ShaderNodeTexNoise'); nw.noise_dimensions = '4D'; L(pos.outputs[0], nw.inputs['Vector']); nw.inputs['Scale'].default_value = 1.9; nw.inputs['Detail'].default_value = 2.0
L(val([(1, 7.0), (FR, 7.7)]), nw.inputs['W'])
wsub = N_('ShaderNodeVectorMath'); wsub.operation = 'SUBTRACT'; L(nw.outputs['Color'], wsub.inputs[0]); wsub.inputs[1].default_value = (0.5, 0.5, 0.5)
wscale = N_('ShaderNodeVectorMath'); wscale.operation = 'SCALE'; L(wsub.outputs[0], wscale.inputs[0]); L(val([(1, 0.05), (8, 0.3), (FR, 0.5)]), wscale.inputs['Scale'])
warped = N_('ShaderNodeVectorMath'); warped.operation = 'ADD'; L(pos.outputs[0], warped.inputs[0]); L(wscale.outputs[0], warped.inputs[1])
pos = warped
length = N_('ShaderNodeVectorMath'); length.operation = 'LENGTH'; L(pos.outputs[0], length.inputs[0])
nz = N_('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; L(pos.outputs[0], nz.inputs['Vector']); nz.inputs['Scale'].default_value = 7.5; nz.inputs['Detail'].default_value = 9.0; nz.inputs['Roughness'].default_value = 0.72
L(val([(1, 0.0), (FR, 1.5)]), nz.inputs['W'])  # it boils
fine = nz.outputs['Fac'] if 'Fac' in nz.outputs else nz.outputs[0]
nb = N_('ShaderNodeTexNoise'); nb.noise_dimensions = '4D'; L(pos.outputs[0], nb.inputs['Vector']); nb.inputs['Scale'].default_value = 2.3; nb.inputs['Detail'].default_value = 2.0
L(val([(1, 3.0), (FR, 3.9)]), nb.inputs['W'])  # big slow lumps: it isn't a ball
big = nb.outputs['Fac'] if 'Fac' in nb.outputs else nb.outputs[0]
fac = m('ADD', m('MULTIPLY', big, vb=0.5), m('MULTIPLY', fine, vb=0.5))
R = val([(1, 0.03), (4, 0.15), (10, 0.23), (24, 0.27), (FR, 0.3)])                # bursts out, then creeps
lump = val([(1, 0.12), (6, 0.5), (20, 0.75), (FR, 0.95)])                                      # smooth at first, lumpier as it rolls
edge = m('ADD', m('SUBTRACT', R, length.outputs['Value']), m('MULTIPLY', m('SUBTRACT', fac, vb=0.5), lump))
eat = val([(1, 0.0), (30, 0.0), (FR, 0.21)])                                        # thins from the outside in at the end
body = N_('ShaderNodeMapRange'); L(m('SUBTRACT', edge, eat), body.inputs['Value']); body.inputs['From Min'].default_value = 0.0; body.inputs['From Max'].default_value = 0.09
heat = val([(1, 1.0), (5, 1.0), (11, 0.6), (20, 0.28), (38, 0.07), (54, 0.0), (FR, 0.0)])  # white-hot, then only pockets of it, then none
# colour by how deep in the ball and how hot it still is
hot = m('MULTIPLY', m('MULTIPLY', edge, vb=5.5), heat)
ramp = N_('ShaderNodeValToRGB'); rampfac = m('ADD', hot, m('MULTIPLY', heat, vb=0.3))
cr = ramp.color_ramp; cr.elements[0].position = 0.0; cr.elements[0].color = (0.0, 0.0, 0.0, 1); cr.elements[1].position = 1.0; cr.elements[1].color = (1.0, 0.95, 0.8, 1)
for p_, c_ in ((0.12, (0.35, 0.02, 0.0, 1)), (0.3, (1.0, 0.2, 0.0, 1)), (0.55, (1.0, 0.6, 0.08, 1))): e = cr.elements.new(p_); e.color = c_
vol = N_('ShaderNodeVolumePrincipled'); out = N_('ShaderNodeOutputMaterial')
vol.inputs['Color'].default_value = (0.07, 0.065, 0.062, 1)                        # the smoke it leaves: sooty, nearly black, soaking up the light
dens = val([(1, 3.0), (10, 9.0), (FR, 11.0)])
L(m('MULTIPLY', body.outputs[0], dens), vol.inputs['Density']); L(ramp.outputs['Color'], vol.inputs['Emission Color'])
# the fire shows through the smoke in pockets as it cools (all of it while it's hot)
pk = N_('ShaderNodeMapRange'); L(fine, pk.inputs['Value']); pk.inputs['From Min'].default_value = 0.56; pk.inputs['From Max'].default_value = 0.7
still = m('MINIMUM', m('MULTIPLY', heat, vb=7.0), vb=1.0)                          # pockets last until the heat is really gone
pock = m('MULTIPLY', m('MULTIPLY', pk.outputs[0], still), m('SUBTRACT', 1.0, heat))
L(m('ADD', rampfac, m('MULTIPLY', pock, vb=0.42)), ramp.inputs['Fac'])
glow = m('ADD', m('MULTIPLY', heat, heat), m('MULTIPLY', pock, vb=0.3))
L(m('MULTIPLY', m('MULTIPLY', body.outputs[0], glow), vb=30.0), vol.inputs['Emission Strength'])
L(vol.outputs['Volume'], out.inputs['Volume']); box.data.materials.append(mat)
for fc in (nt.animation_data.action.fcurves if nt.animation_data and hasattr(nt.animation_data.action, 'fcurves') else []):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0; so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(-30), math.radians(-20))
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.6, 0.62, 0.7, 1); world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = 2.4
cob = bpy.data.objects.new('cam', cam); sc.collection.objects.link(cob); sc.camera = cob; cob.location = (0, -8, 0.0); cob.rotation_euler = (math.radians(90), 0, 0)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True; sc.cycles.volume_bounces = 1; sc.cycles.max_bounces = 2
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception as e: print('no OIDN:', e); sc.cycles.use_denoising = False
sc.render.use_persistent_data = True; sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = CELL; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.view_settings.view_transform = 'Standard'
sheet = np.zeros((N * CELL, N * CELL, 4), dtype=np.float32)
edgefade = np.clip((0.5 - np.abs(np.linspace(-0.5, 0.5, CELL))) * 12, 0, 1); edgefade = edgefade[None, :] * edgefade[:, None]
for k in range(FR - 2):  # starts two frames in: the first two are an empty dot
    if ONLY and k not in ONLY: continue
    sc.frame_set(3 + k); path = os.path.join(tmp, f'f{k:02d}.png'); sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path); px = np.array(img.pixels[:], dtype=np.float32).reshape(CELL, CELL, 4) * edgefade[:, :, None]; bpy.data.images.remove(img)
    r_, c_ = k // N, k % N; sheet[(N - 1 - r_) * CELL:(N - r_) * CELL, c_ * CELL:(c_ + 1) * CELL] = px
    print('frame', k, 'cover', round(float((px[:, :, 3] > 0.05).mean()), 3), 'peak', round(float(px[:, :, :3].max()), 2), flush=True)
img = bpy.data.images.new('sheet', N * CELL, N * CELL, alpha=True); img.alpha_mode = 'PREMUL'
img.pixels[:] = np.clip(sheet, 0, 1).reshape(-1); img.filepath_raw = OUT; img.file_format = 'PNG'; img.save()
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'kB')
