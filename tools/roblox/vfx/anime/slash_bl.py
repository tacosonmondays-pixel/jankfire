# Anime slash flipbooks, rendered in Blender (the VFX session, 26 Nov 2026; round 2 after the critic's 4/10;
# round 1 is slash_bl_r1.py).
#
# Ribbons on a plane; ALL the animation is in their shaders, set frame by frame from Python. Rendered at 2x and
# downsampled by sheet.py (smooth 1-1.5 px edges on a hard cel look).
#   main   a SPIRAL arc (tail radius 0.75 of the head's), widest at 70 % of the way to the head, a pointed tip flicked
#          outward, a long tail that splits into strands, sawtooth notches cut into the outer edge of its back half
#   streak a short secondary streak on its own radius, both ends tapered, gone by frame 4
#   line   the blade-light line left behind: one crisp thin arc on the outer rim that overshoots the head
# Layers (same timing, so they stay in step in Roblox):
#   body  greyscale 0.55-0.7, tinted per weapon (drawn twice in Roblox: added, and painted under it so the colour
#         survives on bright floors)
#   core  white-hot: the whole head, a rim along the outer edge towards the tail (a smooth diagonal cel boundary)
#   ink   2-4 bold tapered black blades inside the body (painted, normal blend)
# The 16 frames (timed by the critic): f0 lead-in at 40 % of the arc, already fat; f1 the flash (mostly white);
# f2-4 hold, the white pulls back to the rim; f5-8 the tail wipes towards the head while the band thins from the inside
# and the notches deepen; f9-12 the blade-light line overshoots, then fades; f13-15 empty.
#
#   blender -b --factory-startup -P slash_bl.py -- <spec.json>
# spec: {"out": dir, "name": "slash_a", "px": 256, "ss": 2, "tilt": [x, y, z], "arc": 165, "width": 0.47,
#        "mirror": false, "seed": 3, "samples": 10, "layers": ["body", "core", "ink"], "fit": 0.88}
# writes <out>/<name>_<layer>_<ff>.png at px*ss
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
FR = 16
PX = int(spec.get('px', 256)) * int(spec.get('ss', 2))
TILT = spec.get('tilt', [0, 0, 0])
ARC = math.radians(spec.get('arc', 165))
W = float(spec.get('width', 0.47))
SEED = float(spec.get('seed', 3))
SPIRAL = float(spec.get('spiral', 0.75))  # the tail's radius as a share of the head's
TEETH = float(spec.get('teeth', 0.1))  # tooth depth, share of the band
LINE_PEAK = float(spec.get('linepeak', 0.6))  # where along it the blade-light line is thickest
LAYERS = spec.get('layers', ['body', 'core', 'ink'])
os.makedirs(OUT, exist_ok=True)

scn = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = int(spec.get('samples', 48))
scn.cycles.use_denoising = False
scn.render.film_transparent = True
scn.render.resolution_x = scn.render.resolution_y = PX
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_mode = 'RGBA'
scn.view_settings.view_transform = 'Standard'
scn.view_settings.look = 'None'
scn.world = bpy.data.worlds.new('w')
scn.world.color = (0, 0, 0)


def ribbon(name, radius, prof, a0, a1):
    # u along the arc 0..1 (a0 -> a1, radians), v across 0 inner .. 1 outer; radius(u) and prof(u) (the width) are functions
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    NU, NV = 200, 12
    uvl = bm.loops.layers.uv.new('UVMap')
    vs = []
    for i in range(NU + 1):
        u = i / NU
        th = a0 + (a1 - a0) * u
        R, w = radius(u), max(prof(u), 0.0005)
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


class Shader:
    def __init__(self, name):
        self.mat = bpy.data.materials.new(name)
        self.mat.use_nodes = True
        nt = self.mat.node_tree
        for n in list(nt.nodes): nt.nodes.remove(n)
        self.N, self.L = nt.nodes, nt.links
        tc = self.node('ShaderNodeTexCoord')
        sep = self.node('ShaderNodeSeparateXYZ')
        self.L.new(tc.outputs['UV'], sep.inputs[0])
        self.U, self.V = sep.outputs[0], sep.outputs[1]
        self.P = {}

    def node(self, kind, **kw):
        n = self.N.new(kind)
        for k, v in kw.items(): setattr(n, k, v)
        return n

    def m(self, op, a, b=None, c=None, clamp=False):
        n = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for idx, x in enumerate((a, b, c)):
            if x is None: continue
            if isinstance(x, (int, float)): n.inputs[idx].default_value = x
            else: self.L.new(x, n.inputs[idx])
        return n.outputs[0]

    def p(self, k):
        if k not in self.P:
            n = self.node('ShaderNodeValue')
            n.outputs[0].default_value = 0.0
            self.P[k] = n
        return self.P[k].outputs[0]

    def smoothstep(self, x, a, b):
        t = self.m('DIVIDE', self.m('SUBTRACT', x, a), b - a, clamp=True)
        return self.m('MULTIPLY', self.m('MULTIPLY', t, t), self.m('SUBTRACT', 3.0, self.m('MULTIPLY', t, 2.0)))

    def finish(self, alpha_by_layer, grey_by_layer):
        # alpha = sum(layer_k * alpha_k); colour grey = sum(layer_k * grey_k)
        a = None
        g = None
        for lay, al in alpha_by_layer.items():
            t = self.m('MULTIPLY', al, self.p('layer_' + lay))
            a = t if a is None else self.m('ADD', a, t)
        for lay, gv in grey_by_layer.items():
            t = self.m('MULTIPLY', self.p('layer_' + lay), gv)
            g = t if g is None else self.m('ADD', g, t)
        comb = self.node('ShaderNodeCombineXYZ')
        for i in range(3): self.L.new(g, comb.inputs[i])
        em = self.node('ShaderNodeEmission')
        self.L.new(comb.outputs[0], em.inputs['Color'])
        tr = self.node('ShaderNodeBsdfTransparent')
        mix = self.node('ShaderNodeMixShader')
        self.L.new(self.m('MINIMUM', a, 1.0), mix.inputs['Fac'])
        self.L.new(tr.outputs[0], mix.inputs[1])
        self.L.new(em.outputs[0], mix.inputs[2])
        out = self.node('ShaderNodeOutputMaterial')
        self.L.new(mix.outputs[0], out.inputs['Surface'])


def rnd(i): return (math.sin(i * 12.9898 + SEED * 78.233) * 43758.5453) % 1.0


# ---------------------------------------------------------------- the main arc
def main_radius(u): return 1.0 * (SPIRAL + (1 - SPIRAL) * u) + 0.05 * max(0.0, (u - 0.9) / 0.1) ** 2  # spiral, tip flicked out


def main_prof(u):
    return W * math.sin(math.pi * min(1.0, max(0.0, u)) ** 1.943) ** 0.8  # (u^1.943 = 0.5 at u = 0.7: the widest point)


A0 = -ARC / 2
main = ribbon('main', main_radius, main_prof, A0, A0 + ARC)
S = Shader('main')
U, V = S.U, S.V
# the head runs along the arc with its OUTER edge leading (a blade's front, not a chord cut)
head_ok = S.m('LESS_THAN', S.m('ADD', U, S.m('MULTIPLY', S.m('ABSOLUTE', S.m('SUBTRACT', V, 0.82)), 0.16)), S.p('head'))
# the tail: four strands, each ending at its own point once 'strand' opens them, with thin gaps between them in the tail
sv = S.m('MULTIPLY', V, 4.0)
sidx = S.m('FLOOR', sv)
shash = S.m('FRACT', S.m('MULTIPLY', S.m('SINE', S.m('ADD', S.m('MULTIPLY', sidx, 12.9898), SEED * 7.1)), 43758.5453))
tail_s = S.m('ADD', S.p('tail'), S.m('MULTIPLY', S.m('SUBTRACT', shash, 0.35), S.m('MULTIPLY', S.p('strand'), 0.3)))
tip_d = S.m('MULTIPLY', S.m('ABSOLUTE', S.m('SUBTRACT', S.m('FRACT', sv), 0.5)), 2.0)  # 0 at a strand's middle .. 1 at its edges
tail_s = S.m('ADD', tail_s, S.m('MULTIPLY', tip_d, S.m('ADD', 0.02, S.m('MULTIPLY', S.p('strand'), 0.1))))
tail_ok = S.m('GREATER_THAN', U, tail_s)
gap = S.m('GREATER_THAN', S.m('ABSOLUTE', S.m('SUBTRACT', S.m('FRACT', sv), 0.5)), 0.43)
in_tail = S.m('LESS_THAN', U, S.m('ADD', S.p('tail'), 0.35))
strand_cut = S.m('MULTIPLY', S.m('MULTIPLY', gap, in_tail), S.m('GREATER_THAN', S.p('strand'), 0.05))
# the band thins from its inner edge
vcut = S.m('SUBTRACT', 1.0, S.p('ws'))
across = S.m('GREATER_THAN', V, vcut)
vb = S.m('DIVIDE', S.m('SUBTRACT', V, vcut), S.m('MAXIMUM', S.p('ws'), 0.001), clamp=True)
# sawtooth notches cut into the outer edge of the back half, leaning along the swing
sx = S.m('FRACT', S.m('ADD', S.m('MULTIPLY', U, 9.0), SEED * 0.37))
saw = S.m('MINIMUM', S.m('DIVIDE', sx, 0.8), S.m('DIVIDE', S.m('SUBTRACT', 1.0, sx), 0.2))  # up over 80 %, down over 20 %
back = S.m('SUBTRACT', 1.0, S.smoothstep(U, 0.42, 0.62))
depth = S.m('MULTIPLY', S.m('MULTIPLY', S.p('notch'), TEETH), back)
notch_ok = S.m('LESS_THAN', vb, S.m('SUBTRACT', 1.0, S.m('MULTIPLY', depth, saw)))
vis = S.m('MULTIPLY', S.m('MULTIPLY', head_ok, tail_ok), S.m('MULTIPLY', across, notch_ok))
vis = S.m('MULTIPLY', vis, S.m('SUBTRACT', 1.0, strand_cut))
a_main = S.m('MULTIPLY', vis, S.p('fade'))
# core: the head all white, a rim along the outer edge towards the tail; core_k scales it (smooth in u: no steps)
cst = S.p('cstart')
ck = S.m('DIVIDE', S.m('SUBTRACT', U, cst), S.m('SUBTRACT', 0.97, cst), clamp=True)
cw = S.m('MULTIPLY', S.m('POWER', ck, 0.75), S.p('core'))
core_m = S.m('MULTIPLY', S.m('GREATER_THAN', vb, S.m('SUBTRACT', 0.94, cw)), S.m('LESS_THAN', vb, 0.94))
# ink: a long blade raked across the band, a short one near the head breaking the white edge, one running into the strands
ink = None
for (a, L_, c0, c1, h) in ((0.3 + 0.04 * rnd(1), 0.38, 0.25, 0.62, 0.11), (0.74 + 0.03 * rnd(2), 0.15, 0.8, 0.9, 0.09),
                           (0.1 + 0.03 * rnd(3), 0.26, 0.5, 0.42, 0.09)):
    a_t = S.m('ADD', a, S.m('MULTIPLY', S.p('peel'), 0.3))
    x = S.m('DIVIDE', S.m('SUBTRACT', U, a_t), L_)
    inside = S.m('MULTIPLY', S.m('GREATER_THAN', x, 0.0), S.m('LESS_THAN', x, 1.0))
    xc = S.m('POWER', S.m('MINIMUM', S.m('MAXIMUM', x, 0.0), 1.0), 2.41)  # (x^2.41 = 0.5 at x = 0.75)
    prof = S.m('POWER', S.m('SINE', S.m('MULTIPLY', xc, math.pi)), 0.9)
    c = S.m('ADD', c0, S.m('MULTIPLY', S.m('MINIMUM', S.m('MAXIMUM', x, 0.0), 1.0), c1 - c0))  # raked across the band
    d = S.m('ABSOLUTE', S.m('SUBTRACT', vb, c))
    blade = S.m('MULTIPLY', inside, S.m('LESS_THAN', d, S.m('MULTIPLY', S.m('MULTIPLY', prof, h), S.p('ink'))))
    ink = blade if ink is None else S.m('MAXIMUM', ink, blade)
ink = ink  # (the short blade crosses the white on purpose)
body_grey = S.m('ADD', 0.55, S.m('MULTIPLY', vb, 0.15))
S.finish({'body': a_main, 'core': S.m('MULTIPLY', a_main, core_m), 'ink': S.m('MULTIPLY', a_main, ink)},
         {'body': body_grey, 'core': 1.0})
main.data.materials.append(S.mat)


# ---------------------------------------------------------------- the short secondary streak and the blade-light line
def simple(name, radius, prof, a0, a1, grey_body):
    ob = ribbon(name, radius, prof, a0, a1)
    sh = Shader(name)
    uu = sh.U
    ok = sh.m('MULTIPLY', sh.m('GREATER_THAN', uu, sh.p('tail')), sh.m('LESS_THAN', uu, sh.p('head')))
    al = sh.m('MULTIPLY', ok, sh.p('fade'))
    sh.finish({'body': al, 'core': al, 'ink': sh.m('MULTIPLY', al, 0.0)}, {'body': grey_body, 'core': 1.0})
    ob.data.materials.append(sh.mat)
    return ob, sh


st_a0 = A0 + ARC * 0.45
streak, SS = simple('streak', lambda u: 0.84 * (0.75 + 0.25 * (0.45 + 0.4 * u)), lambda u: 0.05 * math.sin(math.pi * u) ** 0.8,
                    st_a0, st_a0 + ARC * 0.36, 0.65)
line, LS = simple('line', lambda u: SPIRAL + (1 - SPIRAL) * (0.45 + 0.67 * u) + 0.004,
                  lambda u: 0.036 * math.sin(math.pi * min(1.0, max(0.0, u)) ** (math.log(0.5) / math.log(LINE_PEAK))) ** 0.9, A0 + ARC * 0.45, A0 + ARC * 1.12, 0.7)

pivot = bpy.data.objects.new('pivot', None)
scn.collection.objects.link(pivot)
for ob in (main, streak, line): ob.parent = pivot
streak.location.z = 0.02  # (off the main arc's plane: coplanar transparent ribbons speckle in Cycles)
line.location.z = 0.04
pivot.rotation_euler = tuple(math.radians(a) for a in TILT)
if spec.get('mirror'): pivot.scale.x = -1
bpy.context.view_layer.update()
cam_d = bpy.data.cameras.new('cam')
cam_d.type = 'ORTHO'
cam = bpy.data.objects.new('cam', cam_d)
scn.collection.objects.link(cam)
pts = [ob.matrix_world @ v.co for ob in (main, line) for v in ob.data.vertices]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
pivot.location = -(lo + hi) / 2
span = max(hi.x - lo.x, hi.y - lo.y)
cam_d.ortho_scale = span / float(spec.get('fit', 0.9))
cam.location = (0, 0, 10)
scn.camera = cam

# ---------------------------------------------------------------- the timeline, one row per frame (the critic's)
#     head  tail  ws    core  notch strand ink  peel  fade | streak fade | line head tail fade
#     head  tail  ws    core cstart notch strand ink  peel | streak head tail | line head tail
TL = [
    (0.55, 0.0, 1.0, 1.0, 0.3, 0.3, 0.0, 0.6, 0.0, 0.0, 0.0, 0.0, 0.0),
    (1.15, 0.0, 1.0, 1.6, 0.2, 0.3, 0.0, 1.0, 0.0, 1.01, 0.0, 0.0, 0.0),
    (1.15, 0.0, 1.0, 1.0, 0.45, 0.35, 0.3, 1.0, 0.0, 1.01, 0.0, 0.0, 0.0),
    (1.15, 0.0, 1.0, 1.0, 0.55, 0.55, 0.5, 1.0, 0.05, 1.01, 0.45, 0.0, 0.0),
    (1.15, 0.05, 0.95, 1.0, 0.6, 0.75, 0.7, 0.85, 0.15, 1.01, 1.01, 0.0, 0.0),
    (1.15, 0.2, 0.88, 1.0, 0.62, 1.0, 0.85, 0.65, 0.3, 0.0, 0.0, 0.0, 0.0),
    (1.15, 0.36, 0.78, 1.0, 0.66, 1.0, 1.0, 0.45, 0.45, 0.0, 0.0, 0.0, 0.0),
    (1.15, 0.52, 0.64, 1.0, 0.7, 1.0, 1.0, 0.25, 0.6, 0.0, 0.0, 0.5, 0.06),
    (1.15, 1.2, 0.5, 1.0, 0.76, 1.0, 1.0, 0.0, 0.7, 0.0, 0.0, 0.8, 0.1),
    (1.15, 1.2, 0.4, 1.0, 0.8, 1.0, 1.0, 0.0, 0.7, 0.0, 0.0, 1.01, 0.16),
    (1.15, 1.2, 0.4, 1.0, 0.8, 1.0, 1.0, 0.0, 0.7, 0.0, 0.0, 1.01, 0.3),
    (1.15, 1.2, 0.4, 1.0, 0.8, 1.0, 1.0, 0.0, 0.7, 0.0, 0.0, 1.01, 0.48),
    (1.15, 1.2, 0.4, 1.0, 0.8, 1.0, 1.0, 0.0, 0.7, 0.0, 0.0, 1.01, 0.68),
    (1.15, 1.2, 0.4, 1.0, 0.8, 1.0, 1.0, 0.0, 0.7, 0.0, 0.0, 1.01, 0.88),
    (1.15, 1.2, 0.4, 1.0, 0.8, 1.0, 1.0, 0.0, 0.7, 0.0, 0.0, 0.0, 0.0),
    (1.15, 1.2, 0.4, 1.0, 0.8, 1.0, 1.0, 0.0, 0.7, 0.0, 0.0, 0.0, 0.0),
]
for layer in LAYERS:
    for f in range(FR):
        hd, tl, ws, co, cs, no, st, ik, pe, sh_, stl, lh, lt = TL[f]
        for k, v in dict(head=hd, tail=tl, ws=ws, core=co, cstart=cs, notch=no, strand=st, ink=ik, peel=pe, fade=1.0).items():
            S.P[k].outputs[0].default_value = v
        for k, v in dict(head=sh_, tail=stl, fade=1.0).items(): SS.P[k].outputs[0].default_value = v
        for k, v in dict(head=lh, tail=lt, fade=1.0).items(): LS.P[k].outputs[0].default_value = v
        for sh in (S, SS, LS):
            for lay in ('body', 'core', 'ink'):
                if 'layer_' + lay in sh.P: sh.P['layer_' + lay].outputs[0].default_value = 1.0 if lay == layer else 0.0
        scn.render.filepath = os.path.join(OUT, '%s_%s_%02d.png' % (NAME, layer, f))
        bpy.ops.render.render(write_still=True)
print('done', NAME)
