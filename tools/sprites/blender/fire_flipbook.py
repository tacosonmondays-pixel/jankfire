# Proof: a looping fire flipbook from Blender WITHOUT the fluid solver (Mantaflow does not start in our headless builds).
# A box of volume whose density and glow come from 4D noise sliding upward through a flame-shaped mask; rendered in
# Cycles on a see-through background and packed 6x6. The last frames are cross-faded into the first, so it loops.
# Run: blender52 -b -P tools/sprites/blender/fire_flipbook.py [-- <cell px> <samples>]
import bpy, sys, os, math, tempfile
import numpy as np
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
CELL = int(args[0]) if args else 96; SAMPLES = int(args[1]) if len(args) > 1 else 40
N, EXTRA = 6, 6  # 36 frames in the sheet + 6 rendered past the end for the loop cross-fade
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../public/sprites/fire.png')
tmp = tempfile.mkdtemp(prefix='jffire')
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1)); box = bpy.context.object; box.scale = (1.5, 1.5, 2.0)
mat = bpy.data.materials.new('fire'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
N_ = nt.nodes.new; L = nt.links.new
co = N_('ShaderNodeTexCoord'); sep = N_('ShaderNodeSeparateXYZ'); L(co.outputs['Object'], sep.inputs[0])  # object space: -0.5..0.5
# the noise slides up (and boils through W)
mp = N_('ShaderNodeMapping'); L(co.outputs['Object'], mp.inputs['Vector']); mp.inputs['Scale'].default_value = (4.2, 4.2, 2.3)
nz = N_('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; L(mp.outputs[0], nz.inputs['Vector']); nz.inputs['Scale'].default_value = 1.0; nz.inputs['Detail'].default_value = 5.0; nz.inputs['Roughness'].default_value = 0.62
for i, (f, z, w) in enumerate([(1, 0.0, 0.0), (43, -5.6, 2.6)]):  # ~0.13 units of climb a frame
    mp.inputs['Location'].default_value = (0, 0, z); mp.inputs['Location'].keyframe_insert('default_value', frame=f)
    nz.inputs['W'].default_value = w; nz.inputs['W'].keyframe_insert('default_value', frame=f)
for fc in nt.animation_data.action.fcurves if hasattr(nt.animation_data.action, 'fcurves') else []:
    for k in fc.keyframe_points: k.interpolation = 'LINEAR'
# the flame mask: wide at the bottom, a point at the top, the noise bends the edge
def math_(op, a=None, b=None, va=None, vb=None):
    n = N_('ShaderNodeMath'); n.operation = op
    if a is not None: L(a, n.inputs[0])
    elif va is not None: n.inputs[0].default_value = va
    if b is not None: L(b, n.inputs[1])
    elif vb is not None: n.inputs[1].default_value = vb
    return n.outputs[0]
h = math_('ADD', sep.outputs['Z'], vb=0.5)                                   # 0 bottom .. 1 top
r = math_('SQRT', math_('ADD', math_('POWER', sep.outputs['X'], vb=2.0), math_('POWER', sep.outputs['Y'], vb=2.0)))
wide = math_('MULTIPLY', math_('POWER', math_('SUBTRACT', va=1.0, b=h), vb=0.6), vb=0.4)   # radius allowed at this height
edge = math_('ADD', math_('SUBTRACT', wide, r), math_('MULTIPLY', math_('SUBTRACT', nz.outputs['Fac'] if 'Fac' in nz.outputs else nz.outputs[0], vb=0.5), vb=0.85))
dens = N_('ShaderNodeMapRange'); L(edge, dens.inputs['Value']); dens.inputs['From Min'].default_value = 0.0; dens.inputs['From Max'].default_value = 0.12
fade = N_('ShaderNodeMapRange'); L(h, fade.inputs['Value']); fade.inputs['From Min'].default_value = 0.0; fade.inputs['From Max'].default_value = 0.14  # no hard cut at the floor
d = math_('MULTIPLY', dens.outputs[0], fade.outputs[0])
# colour by how deep in the flame: white-hot core, yellow, orange, dark red skin
ramp = N_('ShaderNodeValToRGB'); L(edge, ramp.inputs['Fac'])
cr = ramp.color_ramp; cr.elements[0].position = 0.0; cr.elements[0].color = (0.5, 0.02, 0.0, 1); cr.elements[1].position = 0.46; cr.elements[1].color = (1.0, 0.95, 0.75, 1)
for pos, col in ((0.1, (1.0, 0.12, 0.0, 1)), (0.24, (1.0, 0.5, 0.03, 1)), (0.34, (1.0, 0.85, 0.2, 1))): e = cr.elements.new(pos); e.color = col
vol = N_('ShaderNodeVolumePrincipled'); out = N_('ShaderNodeOutputMaterial')
vol.inputs['Color'].default_value = (0.05, 0.02, 0.01, 1)
L(math_('MULTIPLY', d, vb=5.0), vol.inputs['Density']); L(ramp.outputs['Color'], vol.inputs['Emission Color']); L(math_('MULTIPLY', d, vb=5.0), vol.inputs['Emission Strength'])
L(vol.outputs['Volume'], out.inputs['Volume']); box.data.materials.append(mat)
cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = 2.05
cob = bpy.data.objects.new('cam', cam); sc.collection.objects.link(cob); sc.camera = cob; cob.location = (0, -8, 1.0); cob.rotation_euler = (math.radians(90), 0, 0)
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True; sc.cycles.volume_bounces = 0; sc.cycles.max_bounces = 1
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception as e: print('no OIDN:', e); sc.cycles.use_denoising = False
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = CELL; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'; sc.view_settings.view_transform = 'Standard'
frames = []
for k in range(N * N + EXTRA):
    sc.frame_set(1 + k); path = os.path.join(tmp, f'f{k:02d}.png'); sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path); frames.append(np.array(img.pixels[:], dtype=np.float32).reshape(CELL, CELL, 4)); bpy.data.images.remove(img)
    print('frame', k, 'cover', float((frames[-1][:, :, 3] > 0.05).mean()), flush=True)
for k in range(EXTRA):  # the loop: frame k becomes a blend of itself and the frame one loop later
    t = (k + 1) / (EXTRA + 1); frames[k] = frames[k] * t + frames[N * N + k] * (1 - t)
sheet = np.zeros((N * CELL, N * CELL, 4), dtype=np.float32)
for k in range(N * N):
    r_, c_ = k // N, k % N; sheet[(N - 1 - r_) * CELL:(N - r_) * CELL, c_ * CELL:(c_ + 1) * CELL] = frames[k]
img = bpy.data.images.new('sheet', N * CELL, N * CELL, alpha=True); img.alpha_mode = 'PREMUL'
img.pixels[:] = np.clip(sheet, 0, 1).reshape(-1); img.filepath_raw = OUT; img.file_format = 'PNG'; img.save()
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'kB')
