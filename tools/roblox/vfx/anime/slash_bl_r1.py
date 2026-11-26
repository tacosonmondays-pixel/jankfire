# Anime slash flipbooks, rendered in Blender (the VFX session, 26 Nov 2026).
#
# A crescent ribbon on a plane; ALL the animation is in its shader, set frame by frame from Python: the sweep (the head
# runs along the arc), the eat (the tail chases the head), the thin-out (the band shrinks to its outer rim, so the smear
# ends as a thin blade-light line), and a streaky break-up (noise stretched along the arc, hard threshold). Edges are hard
# (cel look, no soft blur). A thin ECHO arc just inside the main one trails it by a frame (the afterimage line).
# Three layers render from the same timing so they stay in step in Roblox:
#   body  greyscale, brighter to the outer rim: tinted per weapon (additive)
#   core  white-hot outer rim and head (additive, untinted)
#   ink   black inner edge and black streaks along the arc (normal blend: the two-tone anime accent)
# A tilt turns both ribbons in 3D under a perspective camera, so a swing can sweep towards or away from the viewer.
#
#   blender -b --factory-startup -P slash_bl.py -- <spec.json>
# spec: {"out": dir, "name": "slash_a", "frames": 16, "px": 256, "tilt": [x_deg, y_deg, z_deg], "arc": 200,
#        "width": 0.42, "echo": true, "samples": 12, "layers": ["body", "core", "ink"], "seed": 3, "fit": 0.86}
# writes <out>/<name>_<layer>_<ff>.png
import json
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

spec = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
OUT = spec['out']
NAME = spec.get('name', 'slash')
FR = int(spec.get('frames', 16))
PX = int(spec.get('px', 256))
TILT = spec.get('tilt', [0, 0, 0])
ARC = math.radians(spec.get('arc', 200))
W = float(spec.get('width', 0.42))
SAMPLES = int(spec.get('samples', 12))
LAYERS = spec.get('layers', ['body', 'core', 'ink'])
SEED = float(spec.get('seed', 3))
ECHO = bool(spec.get('echo', True))
os.makedirs(OUT, exist_ok=True)

scn = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = SAMPLES
scn.cycles.use_denoising = False
scn.render.film_transparent = True
scn.render.resolution_x = scn.render.resolution_y = PX
scn.render.resolution_percentage = 100
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGBA'
scn.view_settings.view_transform = 'Standard'
scn.view_settings.look = 'None'
scn.world = bpy.data.worlds.new('w')
scn.world.color = (0, 0, 0)


# ---- a ribbon: u along the arc (0 tail .. 1 head), v across (0 inner .. 1 outer); its width follows `profile`
def build_ribbon(name, R, wmax, arc, profile):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    NU, NV = 160, 10
    a0 = -arc / 2
    uvl = bm.loops.layers.uv.new('UVMap')
    kmax = max(profile(i / 400) for i in range(401)) or 1
    vs = []
    for i in range(NU + 1):
        u = i / NU
        th = a0 + arc * u
        w = wmax * profile(u) / kmax
        vs.append([bm.verts.new((math.cos(th) * (R - w * (1 - j / NV)), math.sin(th) * (R - w * (1 - j / NV)), 0)) for j in range(NV + 1)])
    for i in range(NU):
        for j in range(NV):
            f = bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
            for lp, uv in zip(f.loops, ((i / NU, j / NV), ((i + 1) / NU, j / NV), ((i + 1) / NU, (j + 1) / NV), (i / NU, (j + 1) / NV))):
                lp[uvl].uv = uv
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    scn.collection.objects.link(ob)
    return ob


# ---- its shader: returns the per-frame inputs
def build_material(name, echo=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    N, L = nt.nodes, nt.links

    def node(kind, **kw):
        n = N.new(kind)
        for k, v in kw.items(): setattr(n, k, v)
        return n

    def m(op, a, b=None, clamp=False):
        n = node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for idx, x in enumerate((a, b)):
            if x is None: continue
            if isinstance(x, (int, float)): n.inputs[idx].default_value = x
            else: L.new(x, n.inputs[idx])
        return n.outputs[0]

    def val():
        n = node('ShaderNodeValue')
        n.outputs[0].default_value = 0.0
        return n

    tc = node('ShaderNodeTexCoord')
    sep = node('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['UV'], sep.inputs[0])
    U, V = sep.outputs[0], sep.outputs[1]
    P = {k: val() for k in ('head', 'tail', 'ws', 'dis', 'fade', 'hair', 'layer_core', 'layer_ink', 'layer_body')}
    o = {k: P[k].outputs[0] for k in P}

    # hairs: the band splits into fine lines along the arc (noise fast across it), each with its own tail end, so the
    # smear dissipates into streaks of different lengths ('hair' 0 = solid band .. 0.6 = mostly gaps)
    mph = node('ShaderNodeMapping')
    mph.inputs['Scale'].default_value = (0.45, 15.0, 1.0)
    mph.inputs['Location'].default_value = (SEED * 0.9 + (3 if echo else 0), SEED * 1.3, 0)
    L.new(tc.outputs['UV'], mph.inputs['Vector'])
    nh = node('ShaderNodeTexNoise', noise_dimensions='2D')
    nh.inputs['Scale'].default_value = 1.0
    nh.inputs['Detail'].default_value = 1.0
    L.new(mph.outputs['Vector'], nh.inputs['Vector'])
    mpt = node('ShaderNodeMapping')
    mpt.inputs['Scale'].default_value = (0.0, 15.0, 1.0)
    mpt.inputs['Location'].default_value = (0, SEED * 2.7, 0)
    L.new(tc.outputs['UV'], mpt.inputs['Vector'])
    nt2 = node('ShaderNodeTexNoise', noise_dimensions='2D')
    nt2.inputs['Scale'].default_value = 1.0
    L.new(mpt.outputs['Vector'], nt2.inputs['Vector'])
    tail_v = m('ADD', o['tail'], m('MULTIPLY', m('SUBTRACT', nt2.outputs['Fac'], 0.5), m('MULTIPLY', o['hair'], 0.9)))
    hairs = m('GREATER_THAN', nh.outputs['Fac'], m('ADD', 0.5, m('MULTIPLY', o['hair'], 0.25))) if not echo else None
    hair_keep = m('MAXIMUM', hairs, m('LESS_THAN', o['hair'], 0.02)) if not echo else None
    along = m('MULTIPLY', m('GREATER_THAN', U, tail_v), m('LESS_THAN', U, o['head']))
    if hair_keep is not None: along = m('MULTIPLY', along, hair_keep)
    vcut = m('SUBTRACT', 1.0, o['ws'])
    across = m('GREATER_THAN', V, vcut)
    vb = m('DIVIDE', m('SUBTRACT', V, vcut), m('MAXIMUM', o['ws'], 0.001), clamp=True)
    # streaky break-up: noise slow along the arc, fast across it, hard threshold rising with 'dis'
    mp = node('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1.4, 7.0, 1.0)
    mp.inputs['Location'].default_value = (SEED * 1.37 + (5 if echo else 0), SEED * 0.71, 0)
    L.new(tc.outputs['UV'], mp.inputs['Vector'])
    nz = node('ShaderNodeTexNoise', noise_dimensions='2D')
    nz.inputs['Scale'].default_value = 2.2
    nz.inputs['Detail'].default_value = 3.0
    nz.inputs['Roughness'].default_value = 0.55
    L.new(mp.outputs['Vector'], nz.inputs['Vector'])
    vis = m('MULTIPLY', m('MULTIPLY', along, across), m('GREATER_THAN', nz.outputs['Fac'], o['dis']))
    span = m('MAXIMUM', m('SUBTRACT', o['head'], o['tail']), 0.001)
    ut = m('DIVIDE', m('SUBTRACT', U, o['tail']), span, clamp=True)
    alpha_base = m('MULTIPLY', m('MULTIPLY', vis, m('MINIMUM', m('DIVIDE', ut, 0.15), 1.0)), o['fade'])
    if echo:
        core_mask = 1.0  # the echo is all core: a thin white line
        ink_mask = 0.0
    else:
        core_mask = m('MAXIMUM', m('GREATER_THAN', vb, 0.72), m('MULTIPLY', m('GREATER_THAN', ut, 0.9), m('GREATER_THAN', vb, 0.35)))
        mp2 = node('ShaderNodeMapping')
        mp2.inputs['Scale'].default_value = (2.0, 11.0, 1.0)
        mp2.inputs['Location'].default_value = (SEED * 2.1, 0.3, 0)
        L.new(tc.outputs['UV'], mp2.inputs['Vector'])
        nz2 = node('ShaderNodeTexNoise', noise_dimensions='2D')
        nz2.inputs['Scale'].default_value = 3.0
        L.new(mp2.outputs['Vector'], nz2.inputs['Vector'])
        ink_mask = m('MAXIMUM', m('LESS_THAN', vb, 0.13), m('MULTIPLY', m('GREATER_THAN', nz2.outputs['Fac'], 0.6), m('LESS_THAN', vb, 0.6)))
    a_core = m('MULTIPLY', alpha_base, core_mask) if not isinstance(core_mask, float) else alpha_base
    a_ink = m('MULTIPLY', alpha_base, ink_mask) if not isinstance(ink_mask, float) else None
    alpha = m('ADD', m('MULTIPLY', a_core, o['layer_core']), m('MULTIPLY', alpha_base, o['layer_body']))
    if a_ink is not None: alpha = m('ADD', alpha, m('MULTIPLY', a_ink, o['layer_ink']))
    body_val = m('ADD', 0.55, m('MULTIPLY', vb, 0.45)) if not echo else 1.0
    col_v = m('ADD', m('MULTIPLY', body_val, o['layer_body']), o['layer_core'])
    comb = node('ShaderNodeCombineXYZ')
    for i in range(3): L.new(col_v, comb.inputs[i])
    em = node('ShaderNodeEmission')
    L.new(comb.outputs[0], em.inputs['Color'])
    tr = node('ShaderNodeBsdfTransparent')
    mix = node('ShaderNodeMixShader')
    L.new(alpha, mix.inputs['Fac'])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    out = node('ShaderNodeOutputMaterial')
    L.new(mix.outputs[0], out.inputs['Surface'])
    return mat, P


def crescent(u): return (u ** 1.6) * ((1 - u) ** 0.32)
def thin(u): return (u ** 0.5) * ((1 - u) ** 0.3)


pivot = bpy.data.objects.new('pivot', None)
scn.collection.objects.link(pivot)
rib = build_ribbon('rib', 1.0, W, ARC, crescent)
mat, P = build_material('slash')
rib.data.materials.append(mat)
rib.parent = pivot
ribbons = [(rib, P, 'main')]
if ECHO:
    ech = build_ribbon('echo', 1.0 - W * 0.62, 0.024, ARC * 0.85, thin)
    emat, EP = build_material('echo', echo=True)
    ech.data.materials.append(emat)
    ech.parent = pivot
    ribbons.append((ech, EP, 'echo'))
pivot.rotation_euler = tuple(math.radians(a) for a in TILT)
bpy.context.view_layer.update()

cam_d = bpy.data.cameras.new('cam')
cam_d.lens = 50
cam = bpy.data.objects.new('cam', cam_d)
scn.collection.objects.link(cam)
# fit the camera to the ribbons as tilted: centre them, and make their larger side fill FIT of the frame
pts = [ob.matrix_world @ v.co for ob, _, _ in ribbons for v in ob.data.vertices]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
pivot.location = -(lo + hi) / 2
FIT = float(spec.get('fit', 0.86))
span = max(hi.x - lo.x, hi.y - lo.y)
cam.location = (0, 0, max(1.5, span / FIT * cam_d.lens / cam_d.sensor_width + (hi.z - lo.z)))
scn.camera = cam


def ease_out(x): return 1 - (1 - x) ** 3
def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def seg(t, a, b): return min(1, max(0, (t - a) / (b - a)))


# the timing (16 frames at 30 fps = 0.53 s): the smear in 3 frames, then the tail chases the head, the band thins to a
# line on the rim, and it breaks up into streaks and goes. The echo runs a frame behind, as a thin line, and goes first
def params(f, kind):
    t = f / (FR - 1)
    if kind == 'echo':
        t2 = max(0.0, t - 1.0 / (FR - 1))
        return dict(head=0.25 + 0.75 * ease_out(seg(t2, 0, 0.16)) + 0.002, tail=0.75 * smooth(seg(t, 0.12, 0.7)), ws=1.0, hair=0.0,
                    dis=-0.1 + 0.9 * smooth(seg(t, 0.3, 0.6)), fade=(1.0 if t > 0 else 0.0) * (1.0 - smooth(seg(t, 0.4, 0.6))))
    head = 0.3 + 0.7 * ease_out(seg(t, 0, 0.14))
    return dict(head=head + 0.002, tail=0.62 * smooth(seg(t, 0.1, 1.0)), ws=1.0 - 0.62 * ease_out(seg(t, 0.12, 0.55)),
                dis=-0.1 + 0.75 * smooth(seg(t, 0.55, 1.0)), fade=1.0 - smooth(seg(t, 0.82, 1.0)),
                hair=0.0 if t < 0.19 else 0.12 + 0.4 * smooth(seg(t, 0.19, 0.65)))


for layer in LAYERS:
    for f in range(FR):
        for ob, PP, kind in ribbons:
            for k, v in params(f, kind).items(): PP[k].outputs[0].default_value = v
            for k in ('layer_core', 'layer_ink', 'layer_body'): PP[k].outputs[0].default_value = 0.0
            PP['layer_' + layer].outputs[0].default_value = 1.0
        scn.render.filepath = os.path.join(OUT, '%s_%s_%02d.png' % (NAME, layer, f))
        bpy.ops.render.render(write_still=True)
print('done', NAME)
