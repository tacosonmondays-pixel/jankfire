# A one-shot explosion flipbook from Blender, without the fluid solver: a lumpy ball of noise volume that bursts out
# yellow-white, then dark sooty billows roll over it with the fire still showing in the cracks, and it ends as smoke that
# rises and thins. Cycles, see-through film, 64 frames packed 8x8 into public/sprites/boom.png (premultiplied colour + alpha).
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
def noise(vec, scale, detail, w, rough=0.6):
    n = N_('ShaderNodeTexNoise'); n.noise_dimensions = '4D'; L(vec, n.inputs['Vector']); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough; L(w, n.inputs['W']); return n
def vmath(op, a, b=None, vb=None, scale=None):
    n = N_('ShaderNodeVectorMath'); n.operation = op; L(a, n.inputs[0])
    if b is not None: L(b, n.inputs[1])
    if vb is not None: n.inputs[1].default_value = vb
    if scale is not None: L(scale, n.inputs['Scale'])
    return n
def mrange(v, lo, hi):
    n = N_('ShaderNodeMapRange'); L(v, n.inputs['Value']); n.inputs['From Min'].default_value = lo; n.inputs['From Max'].default_value = hi; return n.outputs[0]
# the cloud climbs as it cools
comb = N_('ShaderNodeCombineXYZ'); L(val([(1, 0.0), (FR, -0.09)]), comb.inputs['Z'])
pos = vmath('ADD', co.outputs['Object'], comb.outputs[0])
# bend the space with slow noise, so the outline is never a ball and the smoke curls
nw = noise(pos.outputs[0], 1.8, 2.0, val([(1, 7.0), (FR, 7.6)]))
pos = vmath('ADD', pos.outputs[0], vmath('SCALE', vmath('SUBTRACT', nw.outputs['Color'], vb=(0.5, 0.5, 0.5)).outputs[0], scale=val([(1, 0.03), (8, 0.2), (FR, 0.34)])).outputs[0])
dist = vmath('LENGTH', pos.outputs[0]).outputs['Value']
# billows: round lumps packed together (the cauliflower look), boiling slowly, with smaller lumps on the big ones
def billow(scale, w):  # folded noise: round tops, sharp creases (4D cell noise does it better but takes minutes a frame)
    n = noise(pos.outputs[0], scale, 1.0, w, 0.5).outputs[0]
    return m('MINIMUM', m('MULTIPLY', m('ABSOLUTE', m('SUBTRACT', n, vb=0.5)), vb=4.0), vb=1.0)
big = billow(2.6, val([(1, 0.0), (FR, 0.55)])); small = billow(6.5, val([(1, 3.0), (FR, 3.9)]))
fine = noise(pos.outputs[0], 9.0, 5.0, val([(1, 0.0), (FR, 1.3)]), 0.7).outputs[0]
lumps = m('ADD', m('ADD', m('MULTIPLY', big, vb=0.62), m('MULTIPLY', small, vb=0.26)), m('MULTIPLY', fine, vb=0.2))  # about 0.2 .. 1
R = val([(1, 0.1), (4, 0.23), (10, 0.3), (24, 0.33), (FR, 0.35)])                    # bursts out, then creeps
amp = val([(1, 0.05), (5, 0.16), (14, 0.24), (FR, 0.3)])                              # smooth flash first, lumpier as it rolls
edge = m('ADD', m('SUBTRACT', R, dist), m('MULTIPLY', m('SUBTRACT', lumps, vb=0.6), amp))
eat = val([(1, 0.0), (34, 0.0), (FR, 0.2)])                                           # thins from the outside in at the end
body = mrange(m('SUBTRACT', edge, eat), 0.0, 0.05)
# heat lives in a ball in the middle that shrinks: the lumps that stick out past it go dark, the cracks between them
# still reach the fire and glow
hotR = val([(1, 0.2), (4, 0.36), (8, 0.37), (16, 0.31), (28, 0.24), (42, 0.13), (54, -0.1), (FR, -0.2)])
T = mrange(m('ADD', m('ADD', m('SUBTRACT', hotR, dist), m('MULTIPLY', m('SUBTRACT', fine, vb=0.5), vb=0.22)), m('MULTIPLY', m('SUBTRACT', 0.6, lumps), vb=0.12)), 0.0, 0.22)
ramp = N_('ShaderNodeValToRGB'); L(T, ramp.inputs['Fac'])
cr = ramp.color_ramp; cr.elements[0].position = 0.0; cr.elements[0].color = (0.0, 0.0, 0.0, 1); cr.elements[1].position = 1.0; cr.elements[1].color = (1.0, 0.82, 0.4, 1)
for p_, c_ in ((0.1, (0.3, 0.012, 0.0, 1)), (0.32, (1.0, 0.16, 0.0, 1)), (0.62, (1.0, 0.5, 0.04, 1))): e = cr.elements.new(p_); e.color = c_
vol = N_('ShaderNodeVolumePrincipled'); out = N_('ShaderNodeOutputMaterial')
vol.inputs['Color'].default_value = (0.13, 0.12, 0.115, 1)                            # sooty, but light enough to show its lumps in the sun
dens = val([(1, 5.0), (8, 15.0), (20, 22.0), (44, 18.0), (FR, 9.0)])                  # the flash is thin fire, the smoke is thick
L(m('MULTIPLY', body, dens), vol.inputs['Density']); L(ramp.outputs['Color'], vol.inputs['Emission Color'])
L(m('MULTIPLY', m('MULTIPLY', body, m('MULTIPLY', T, T)), val([(1, 10.0), (6, 12.0), (12, 24.0), (FR, 28.0)])), vol.inputs['Emission Strength'])
L(vol.outputs['Volume'], out.inputs['Volume']); box.data.materials.append(mat)
for fc in (nt.animation_data.action.fcurves if nt.animation_data and hasattr(nt.animation_data.action, 'fcurves') else []):
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.0; so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(-30), math.radians(-20))
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
for k in range(FR):
    if ONLY and k not in ONLY: continue
    sc.frame_set(1 + k); path = os.path.join(tmp, f'f{k:02d}.png'); sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path); px = np.array(img.pixels[:], dtype=np.float32).reshape(CELL, CELL, 4) * edgefade[:, :, None]; bpy.data.images.remove(img)
    r_, c_ = k // N, k % N; sheet[(N - 1 - r_) * CELL:(N - r_) * CELL, c_ * CELL:(c_ + 1) * CELL] = px
    print('frame', k, 'cover', round(float((px[:, :, 3] > 0.05).mean()), 3), 'peak', round(float(px[:, :, :3].max()), 2), flush=True)
img = bpy.data.images.new('sheet', N * CELL, N * CELL, alpha=True); img.alpha_mode = 'PREMUL'
img.pixels[:] = np.clip(sheet, 0, 1).reshape(-1); img.filepath_raw = OUT; img.file_format = 'PNG'; img.save()
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'kB')
