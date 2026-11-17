# The owner's sheet for the Gut arena's heart tower (17 Nov 2026): three takes on the stylised heart, on the same tower,
# side by side (gut_heart.py): A candy (a puffy glossy coral heart with a cream piping), B gem (a cut see-through ruby
# with a glowing heart inside), C lantern (the coral heart banded by glowing seams, a rose-gold hoop round it).
#
# run: blender -b --factory-startup -P tools/roblox/gut_takes.py -- <out_dir>
#   writes <out_dir>/take_wide.jpg, take_<x>_close.jpg, take_<x>_eye.jpg (then gut_sheet.py tiles them)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import arenakit as K
import gut_heart as G

OUT = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_gut_takes')
os.makedirs(OUT, exist_ok=True)
ANAT = '--anat' in K.FLAGS        # the anatomical takes (the owner's second word: "We can do an actual heart")
TAKES = [('chunky', -100.0), ('vessels', 0.0), ('grand', 100.0)] if ANAT else [('candy', -100.0), ('gem', 0.0), ('lantern', 100.0)]
PRE = 'anat_' if ANAT else 'take_'

for take, tx in TAKES:
    G.tower('gt_' + take, take, x=tx)
    # a 5-stud figure at the foot for scale
    K.B('gt_fig', '37d6ff', tx + 26, 0, 24, tx + 28, 3.2, 25, bev=0.2)
    K.B('gt_fig', '37d6ff', tx + 26.3, 3.3, 24.1, tx + 27.7, 4.7, 24.9, bev=0.3)
# the ground: a pale pink plaza
K.B('gt_ground', 'dcb2aa', -600, -2, -600, 600, 0, 600, bev=0.0)
K.flush()

sc = bpy.context.scene
cam_data = bpy.data.cameras.new('cam'); cam_data.clip_end = 8000
cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.0; sun.angle = 0.2; sun.color = (1.0, 0.86, 0.80)
so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(55), 0, math.radians(-150))
for take, tx in TAKES:   # the heart's own light (in the game: a PointLight that beats)
    pl = bpy.data.lights.new('hl', 'POINT'); pl.energy = 60000; pl.color = (1.0, 0.45, 0.5); pl.shadow_soft_size = 6
    po = bpy.data.objects.new('hl', pl); sc.collection.objects.link(po)
    po.location = (K.P @ Vector((tx, G.HEART_Y, 24, 1))).xyz
# a warm red sky: hot pink haze at the horizon going to a dark plum overhead
w = bpy.data.worlds.new('w'); w.use_nodes = True; sc.world = w
nt = w.node_tree
bg = nt.nodes['Background']; bg.inputs['Strength'].default_value = 1.0
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); ramp = nt.nodes.new('ShaderNodeValToRGB')
nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
el = ramp.color_ramp.elements
el[0].position = 0.0; el[0].color = (0.95, 0.46, 0.42, 1)
el[1].position = 0.5; el[1].color = (0.20, 0.03, 0.04, 1)
mid = el.new(0.08); mid.color = (0.62, 0.14, 0.12, 1)

sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'JPEG'

def shot(name, cp, tp, lens, res):
    sc.render.resolution_x, sc.render.resolution_y = res
    c = K.P @ Vector((cp[0], cp[1], cp[2], 1)); t = K.P @ Vector((tp[0], tp[1], tp[2], 1))
    cam.location = c.xyz
    cam.rotation_euler = (t.xyz - c.xyz).to_track_quat('-Z', 'Y').to_euler()
    cam_data.lens = lens
    sc.render.filepath = os.path.join(OUT, name + '.jpg')
    bpy.ops.render.render(write_still=True)
    print('RENDERED', sc.render.filepath)

if ANAT:
    shot(PRE + 'wide', (0, 74, 390), (0, 92, 0), 26, (1800, 780))
else:
    shot(PRE + 'wide', (0, 58, 345), (0, 80, 0), 26, (1800, 780))
for take, tx in TAKES:
    if ANAT:
        shot(PRE + '%s_close' % take, (tx + 26, 140, 74), (tx, 142, 0), 40, (600, 600))
        shot(PRE + '%s_back' % take, (tx - 30, 146, -70), (tx, 143, 0), 40, (600, 600))
    else:
        shot(PRE + '%s_close' % take, (tx + 30, 128, 76), (tx, 128, 0), 44, (600, 600))
        shot(PRE + '%s_eye' % take, (tx + 34, 5.5, 74), (tx, 70, 0), 22, (600, 600))
