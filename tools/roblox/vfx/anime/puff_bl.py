# Anime (cel-shaded) smoke puff flipbook, rendered in Blender (the VFX session, 26 Nov 2026). Metaballs under an
# orthographic camera, shaded in THREE hard bands from a fixed light (the normal's dot with it, through a constant ramp:
# no soft gradients), drawn as emission so the bands are exact. One layer, greyscale, painted (LightEmission 0) and
# tinted by the game: gun smoke, dust, a puff off an impact.
#   f0-4   the lumps swell out of a point (ease-out), drifting apart a little and rising
#   f5-15  each lump shrinks away at its own time (no fades: Cycles draws half-alpha as grain)
#
#   blender -b --factory-startup -P puff_bl.py -- <spec.json>
# spec: {"out": dir, "name": "puff_a", "px": 256, "ss": 2, "lumps": 8, "seed": 5}
import json
import math
import os
import random
import sys

import bpy

spec = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
OUT = spec['out']
NAME = spec.get('name', 'puff')
FR = 16
PX = int(spec.get('px', 256)) * int(spec.get('ss', 2))
rng = random.Random(int(spec.get('seed', 5)))
NL = int(spec.get('lumps', 12))
os.makedirs(OUT, exist_ok=True)

scn = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = 48
scn.cycles.use_denoising = False
scn.render.film_transparent = True
scn.render.resolution_x = scn.render.resolution_y = PX
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGBA'
scn.view_settings.view_transform = 'Standard'
scn.view_settings.look = 'None'
scn.world = bpy.data.worlds.new('w')
scn.world.color = (0, 0, 0)
cam_d = bpy.data.cameras.new('cam')
cam_d.type = 'ORTHO'
cam_d.ortho_scale = float(spec.get('frame', 1.6))  # (the puff fills ~70 % of the cell; margins checked after)
cam = bpy.data.objects.new('cam', cam_d)
scn.collection.objects.link(cam)
cam.location = (0, 0, 6)
scn.camera = cam

# the material: three hard bands from a light up and to the right, towards the viewer
mat = bpy.data.materials.new('toon')
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
geo = nt.nodes.new('ShaderNodeNewGeometry')
dot = nt.nodes.new('ShaderNodeVectorMath')
dot.operation = 'DOT_PRODUCT'
lx, ly, lz = 0.45, 0.65, 0.6
ln = math.sqrt(lx * lx + ly * ly + lz * lz)
dot.inputs[1].default_value = (lx / ln, ly / ln, lz / ln)
nt.links.new(geo.outputs['Normal'], dot.inputs[0])
ramp = nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.interpolation = 'CONSTANT'
els = ramp.color_ramp.elements
els[0].position = 0.0
els[0].color = (0.34, 0.34, 0.34, 1)
els[1].position = 0.26
els[1].color = (0.6, 0.6, 0.6, 1)
e3 = els.new(0.64)
e3.color = (0.86, 0.86, 0.86, 1)
nt.links.new(dot.outputs['Value'], ramp.inputs['Fac'])
em = nt.nodes.new('ShaderNodeEmission')
nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
out = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(em.outputs[0], out.inputs['Surface'])

mb = bpy.data.metaballs.new('puff')
mb.resolution = 0.025
mb.render_resolution = 0.012
mb.threshold = 0.6
mob = bpy.data.objects.new('puff', mb)
scn.collection.objects.link(mob)
mob.data.materials.append(mat)

lumps = []
for i in range(NL):
    a = rng.uniform(0, math.tau)
    d = 0.0 if i == 0 else rng.uniform(0.22, 0.5)
    lumps.append(dict(x=math.cos(a) * d, y=math.sin(a) * d * 0.8, z=rng.uniform(-0.1, 0.1), r=(0.42 if i == 0 else rng.uniform(0.18, 0.32)),
                      gone=rng.uniform(0.45, 0.95), drift=rng.uniform(0.1, 0.25)))
els_ = [mb.elements.new() for _ in lumps]


def ease_out(x): return 1 - (1 - x) ** 3
def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def seg(t, a, b): return min(1, max(0, (t - a) / (b - a)))


for f in range(FR):
    t = f / (FR - 1)
    grow = ease_out(seg(t, 0.0, 0.3))
    for L, e in zip(lumps, els_):
        out_k = 1 + L['drift'] * smooth(seg(t, 0.1, 1.0))
        e.co = (L['x'] * (0.35 + 0.65 * grow) * out_k, L['y'] * (0.35 + 0.65 * grow) * out_k + 0.18 * smooth(seg(t, 0.15, 1.0)), L['z'])
        shrink = 1 - smooth(seg(t, L['gone'] - 0.35, L['gone']))
        e.radius = max(0.0, L['r'] * (0.25 + 0.75 * grow) * shrink)
    scn.render.filepath = os.path.join(OUT, '%s_smoke_%02d.png' % (NAME, f))
    bpy.ops.render.render(write_still=True)
print('done', NAME)
