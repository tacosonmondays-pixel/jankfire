# Anime muzzle flashes, rendered in Blender (the VFX session, 26 Nov 2026). A flash shows ONE random cell of a 2x2 sheet
# for a few hundredths of a second (Fx: StartRandom, Framerate 0), so each cell is a complete drawing:
#   front  seen down the barrel: an uneven star of concave needle points round a white-hot core, short black needles
#          between them (the two-tone)
#   side   seen from the side: needle tongues jetting forward (+X, the root at the left edge's middle), a white root,
#          black slivers along the tongues
# Layers (as the slashes): body (tinted, added + painted under), core (white, added), ink (black, painted).
#
#   blender -b --factory-startup -P mflash_bl.py -- <spec.json>
# spec: {"out": dir, "view": "front"|"side", "px": 512, "ss": 2, "seed": 9, "variants": 4}
# writes <out>/mflash_<view>_<layer>_<v>.png
import json
import math
import os
import random
import sys

import bpy
import bmesh

spec = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
OUT = spec['out']
VIEW = spec.get('view', 'front')
PX = int(spec.get('px', 512)) * int(spec.get('ss', 2))
NV = int(spec.get('variants', 4))
rng = random.Random(int(spec.get('seed', 9)))
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
cam_d.ortho_scale = 2.0 / 0.86  # (everything inside 86 % of the cell: clean margins)
cam = bpy.data.objects.new('cam', cam_d)
scn.collection.objects.link(cam)
cam.location = (0, 0, 5)
scn.camera = cam


def emissive(name, grey):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (grey, grey, grey, 1)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


MAT = {'body': emissive('body', 0.68), 'core': emissive('core', 1.0), 'ink': emissive('ink', 0.0)}


def poly(bm, pts):
    if len(pts) >= 3: bm.faces.new([bm.verts.new((x, y, 0)) for x, y in pts])


def needle(bm, ox, oy, a, r0, r1, wb, bend=0.0, peak=0.0, n=14):
    # a stroke from radius r0 to r1 along angle a about (ox, oy): concave sides (a needle) when peak = 0, else widest at
    # `peak` of its length and pointed at both ends
    c, s_ = math.cos(a), math.sin(a)
    px, py = -s_, c
    L, R = [], []
    for i in range(n + 1):
        s = i / n
        r = r0 + (r1 - r0) * s
        if peak <= 0: hw = wb / 2 * (1 - s) ** 2.0
        else: hw = wb / 2 * ((s / peak) ** 0.8 if s < peak else ((1 - s) / (1 - peak)) ** 1.3)
        off = bend * (r1 - r0) * math.sin(math.pi * s)
        cx, cy = ox + c * r + px * off, oy + s_ * r + py * off
        L.append((cx + px * hw, cy + py * hw)); R.append((cx - px * hw, cy - py * hw))
    poly(bm, L + R[::-1])


def blob(bm, ox, oy, R, n=10, jag=0.3):
    # a jagged hot core: an irregular star-ish polygon
    pts = []
    for i in range(n * 2):
        r = R * (1.0 if i % 2 == 0 else 1 - jag) * rng.uniform(0.85, 1.1)
        a = (i + rng.uniform(-0.2, 0.2)) / (n * 2) * math.tau
        pts.append((ox + math.cos(a) * r, oy + math.sin(a) * r))
    poly(bm, pts)


def front(v):
    # one drawing: 7-9 points, two long ones roughly opposite (a flash is wider than tall), the rest uneven
    n = rng.randint(7, 9)
    tilt = rng.uniform(-0.25, 0.25)
    pts = []
    for i in range(n):
        a = tilt + (i + rng.uniform(-0.25, 0.25)) / n * math.tau
        L = rng.uniform(0.45, 0.78)
        if i == 0 or i == n // 2: L = rng.uniform(0.9, 1.0)
        pts.append((a, L, rng.uniform(0.16, 0.24)))
    core_R = rng.uniform(0.2, 0.26)
    inks = [((p[0] + q[0]) / 2 + (math.pi if abs(p[0] - q[0]) > math.pi else 0), rng.uniform(0.3, 0.5)) for p, q in zip(pts, pts[1:] + pts[:1])]
    out = {}
    for layer in ('body', 'core', 'ink'):
        bm = bmesh.new()
        if layer == 'body':
            for a, L, w in pts: needle(bm, 0, 0, a, 0.0, L, w)
            blob(bm, 0, 0, core_R * 1.25, n=9, jag=0.25)
        elif layer == 'core':
            for a, L, w in pts: needle(bm, 0, 0, a, 0.0, L * 0.55, w * 0.55)
            blob(bm, 0, 0, core_R, n=9, jag=0.3)
        else:
            for a, L in inks[::2]: needle(bm, 0, 0, a, core_R * 0.9, core_R * 0.9 + L, 0.07, peak=0.3)
        out[layer] = bm
    return out


def side(v):
    # one drawing: the root at the left edge's middle (x = -1), 3-4 needle tongues forward, the middle one longest
    n = rng.randint(3, 4)
    ox, oy = -0.92, 0.0
    tongues = []
    for i in range(n):
        a = rng.uniform(-0.32, 0.32) * (0.4 if i == 0 else 1)
        L = rng.uniform(1.35, 1.8) if i == 0 else rng.uniform(0.7, 1.25)
        tongues.append((a, L, rng.uniform(0.2, 0.3) if i == 0 else rng.uniform(0.12, 0.2), rng.uniform(-0.05, 0.05)))
    out = {}
    for layer in ('body', 'core', 'ink'):
        bm = bmesh.new()
        if layer == 'body':
            for a, L, w, b in tongues: needle(bm, ox, oy, a, 0.0, L, w, bend=b)
            blob(bm, ox + 0.08, oy, 0.24, n=8, jag=0.3)
        elif layer == 'core':
            for a, L, w, b in tongues: needle(bm, ox, oy, a, 0.0, L * 0.45, w * 0.5, bend=b)
            blob(bm, ox + 0.08, oy, 0.17, n=8, jag=0.3)
        else:
            for a, L, w, b in tongues[1:]: needle(bm, ox, oy, a + rng.choice((-1, 1)) * 0.05, L * 0.35, L * 0.85, 0.05, bend=b, peak=0.3)
        out[layer] = bm
    return out


for v in range(NV):
    parts = front(v) if VIEW == 'front' else side(v)
    for layer, bm in parts.items():
        for o in [o for o in bpy.data.objects if o.type == 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
        me = bpy.data.meshes.new(layer)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(layer, me)
        ob.data.materials.append(MAT[layer])
        scn.collection.objects.link(ob)
        scn.render.filepath = os.path.join(OUT, 'mflash_%s_%s_%02d.png' % (VIEW, layer, v))
        bpy.ops.render.render(write_still=True)
print('done', VIEW)
