# Anime hit burst flipbook, rendered in Blender (the VFX session, 26 Nov 2026; round 2 after the critic's 6/10;
# round 1 is burst_bl_r1.py).
#
# Flat geometry rebuilt every frame under an orthographic camera (no meshes go to Roblox: it all ends up in the sheet).
# The star's long axis is drawn LEVEL, so the game turns the burst along the slash that made it.
#   f0-1  a four-point star of concave needle arms (long axis 2.8x the short), held two frames (f1 at 65 %)
#   f1-2  three tinted shockwave crescents on different radii, tapered to points, white leading edges
#   f1-3  2-3 black radial wedges, longer than the shards (the two-tone accent, on its own)
#   f2-6  shards fly out and detach (two of the seven straight or curving the other way), a hard black stripe inside each
#   f7-11 the exit: shards wipe away from their base, never under half their size
#   f12-15 empty
# Layers: body (tinted, added + painted under it), core (white, added), ink (black, painted).
#
#   blender -b --factory-startup -P burst_bl.py -- <spec.json>
# spec: {"out": dir, "name": "burst_a", "px": 256, "ss": 2, "seed": 4, "samples": 48}
import json
import math
import os
import random
import sys

import bpy
import bmesh

spec = json.load(open(sys.argv[sys.argv.index('--') + 1], encoding='utf-8'))
OUT = spec['out']
NAME = spec.get('name', 'burst')
FR = 16
PX = int(spec.get('px', 256)) * int(spec.get('ss', 2))
rng = random.Random(int(spec.get('seed', 4)))
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
cam_d = bpy.data.cameras.new('cam')
cam_d.type = 'ORTHO'
cam_d.ortho_scale = 2.1 / 0.8  # (drawn at 80 %: nothing reaches the cell's edge; AnimeFx sizes it up by 1.25)
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


MAT = {'body': emissive('body', 0.65), 'core': emissive('core', 1.0), 'ink': emissive('ink', 0.0)}

# ---- the parts, fixed for the whole effect
AXIS = 0.0  # the star's long axis and the two long shards: level (the game turns it along the slash)
shards = []
for i in range(5):
    a = AXIS + math.pi / 2 + (i + rng.uniform(-0.3, 0.3)) / 5 * math.pi * 2 * 0.999
    shards.append(dict(a=a, L=rng.uniform(0.5, 0.8), w=rng.uniform(0.1, 0.14), lag=rng.uniform(0, 0.05), bend=1.0))
for a in (AXIS, AXIS + math.pi):
    shards.append(dict(a=a + rng.uniform(-0.06, 0.06), L=1.0, w=0.14, lag=0.0, bend=1.0))
straight = rng.sample(range(len(shards)), 2)  # two of seven straight or curving the other way
shards[straight[0]]['bend'] = 0.0
shards[straight[1]]['bend'] = -1.0
wedges = [dict(a=AXIS + math.radians(d + rng.uniform(-8, 8)), L=L, w=0.055) for d, L in ((70, 1.0), (196, 0.74), (305, 0.86))]  # (8:1 or longer)
c0 = rng.uniform(0, math.tau)
cresc = [dict(a=c0 + math.radians(d), span=math.radians(sp), r=r, th=rng.uniform(0.05, 0.07))
         for d, sp, r in ((0, 45, 0.6), (135, 60, 0.68), (250, 75, 0.54))]


def ease_out(x): return 1 - (1 - x) ** 3
def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def seg(t, a, b): return min(1, max(0, (t - a) / (b - a)))


def poly(bm, pts):
    if len(pts) < 3: return
    bm.faces.new([bm.verts.new((x, y, 0)) for x, y in pts])


def side_pts(a, r0, r1, half_w, bend, n=10):
    # the outline of a tapered stroke along angle a from r0 to r1; half_w(s) its half width at s (0 base .. 1 tip); bend
    # curves it sideways (a hand-drawn stroke)
    c, s_ = math.cos(a), math.sin(a)
    px, py = -s_, c
    left, right = [], []
    for i in range(n + 1):
        s = i / n
        r = r0 + (r1 - r0) * s
        off = bend * 0.08 * (r1 - r0) * math.sin(math.pi * s)
        hw = half_w(s)
        cx, cy = c * r + px * off, s_ * r + py * off
        left.append((cx + px * hw, cy + py * hw))
        right.append((cx - px * hw, cy - py * hw))
    return left + right[::-1]


def needle(bm, a, length, wb):
    # a concave needle arm from the centre: at half its length it is under 35 % of its base width
    poly(bm, side_pts(a, 0.0, length, lambda s: wb / 2 * (1 - s) ** 2.2, 0.0, n=14))


def sliver(s):
    # pointed at both ends: up over the first quarter, a long taper to the tip
    return (s / 0.25) ** 0.7 if s < 0.25 else ((1 - s) / 0.75) ** 0.9


def blade_w(s):
    # 0 at the base and the tip, widest at s = 0.72 (28 % back from the leading tip): a long straight taper behind
    return (s / 0.72) if s < 0.72 else ((1 - s) / 0.28) ** 0.8


PX_U = (2.1 / 0.8) / 256  # one pixel of the 256 px cell, in scene units


def shard(bm, sp, rb, rt, band=(0.0, 1.0), span=(0.0, 1.0), turn=0.0, wfrac=0.14, span_hi=None):
    # a blade sliver from rb to rt: its straight side on the stroke's line, its curved side out to blade_w; band picks
    # the strip across it to fill (0 = the straight side .. 1 = the curved edge), span the stretch along it (span_hi:
    # a different start for the band's outer edge, so the strip's end slants)
    L = rt - rb
    if L < 0.01: return
    W = max(wfrac * L, 4 * PX_U)
    a = sp['a'] + turn
    c, s_ = math.cos(a), math.sin(a)
    px, py = -s_, c
    side = 1 if sp['bend'] >= 0 else -1
    n = 14
    sh = span_hi or span

    def at(sp_, b, i):
        s = sp_[0] + (sp_[1] - sp_[0]) * i / n
        r = rb + L * s
        off = side * 0.06 * L * math.sin(math.pi * s) * abs(sp['bend'])  # (the straight side bows a touch on a bent one)
        w = W * blade_w(s)
        cx, cy = c * r + px * off, s_ * r + py * off
        return (cx + px * side * w * b, cy + py * side * w * b)
    lo = [at(span, band[0], i) for i in range(n + 1)]
    hi = [at(sh, band[1], i) for i in range(n + 1)]
    poly(bm, lo + hi[::-1])


def crescent(bm, cr, grow, part):
    # a shockwave crescent: thickest in its middle, tapering to points; part 'all' or 'edge' (its outer 30 %)
    r = cr['r'] * (0.85 + 0.35 * grow)
    th = cr['th'] * (1 - 0.4 * grow)
    ox, oy = math.cos(cr['a']) * 0.13 * cr['r'], math.sin(cr['a']) * 0.13 * cr['r']  # off the hit point
    n = 24
    outer, inner = [], []
    for i in range(n + 1):
        s = i / n
        a = cr['a'] - cr['span'] / 2 + cr['span'] * s
        k = math.sin(math.pi * s) ** 0.8
        t_in = th * k * (0.3 if part == 'edge' else 1.0)
        outer.append((ox + math.cos(a) * r, oy + math.sin(a) * r))
        inner.append((ox + math.cos(a) * (r - t_in), oy + math.sin(a) * (r - t_in)))
    poly(bm, outer + inner[::-1])


def obj(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(mat)
    scn.collection.objects.link(ob)
    return ob


def shard_span(sp, t):
    # where a shard is at time t (0..1 over frames 0-11): flies out, detaches, then wipes from its base
    k = max(0.0, t - sp['lag'])
    if k < 0.18: return None  # (from f2: the star's arms stay clean on f1)
    rt = sp['L'] * (0.35 + 0.65 * ease_out(seg(k, 0.09, 0.4)))
    rb = sp['L'] * (0.1 + 0.4 * smooth(seg(k, 0.15, 0.55)))
    # the exit (f7-11): the base runs to the tip, never leaving less than half the stroke until it goes
    ex = seg(t, 0.62, 0.95)
    if ex >= 1: return None
    rb = rb + (rt - rb) * 0.5 * ex
    # f4-11: still flying, another 35 % of its length out (the long pair 15 %: they'd leave the cell), easing off
    travel = (0.15 if sp['L'] >= 0.99 else 0.35) * sp['L'] * ease_out(seg(t, 0.33, 1.0))
    return rb + travel, rt + travel


def shard_w(sp, f):
    # the peak (f2-4) heavy: the long pair 20 % of their length, the others 18 % (6 px+); the exit thins back to 14 %
    peak = 0.2 if sp['L'] >= 0.99 else 0.18
    return peak if f <= 4 else peak + (0.14 - peak) * min(1.0, (f - 4) / 2.0)


def shard_turn(sp, t):
    return (1 if sp['bend'] >= 0 else -1) * math.radians(8) * seg(t, 0.33, 1.0)


def build(f, layer):
    for o in [o for o in bpy.data.objects if o.type == 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
    bm = bmesh.new()
    if f <= 11:
        t = f / 11.0
        # the star: f0 full, f1 at 65 % (body = a slightly bigger tinted rim under the white)
        if f <= 1 and layer in ('body', 'core'):
            k = 1.0 if f == 0 else 0.65
            grow = 1.08 if layer == 'body' else 1.0
            for i in range(4):
                L = (0.95 if i % 2 == 0 else 0.34) * k * grow
                needle(bm, AXIS + i * math.pi / 2, L, 0.2 * k * grow)
            poly(bm, [(math.cos(i / 12 * math.tau) * 0.07 * k * grow, math.sin(i / 12 * math.tau) * 0.07 * k * grow) for i in range(12)])
        # the shockwave crescents, f1-2
        if 1 <= f <= 2 and layer in ('body', 'core'):
            big = max(cresc, key=lambda c: c['span'] * c['r'])
            for cr in cresc:
                if f == 2 and cr is big: continue
                crescent(bm, cr, (f - 1) / 1.0, 'all' if layer == 'body' else 'edge')
        # the shards
        if layer in ('body', 'core'):
            for sp in shards:
                sp_ = shard_span(sp, t)
                if not sp_: continue
                rb, rt = sp_
                tn = shard_turn(sp, t)
                wf = shard_w(sp, f)
                if layer == 'body': shard(bm, sp, rb, rt, turn=tn, wfrac=wf)
                elif f <= 4: shard(bm, sp, rb, rt, band=(0.35, 1.0), span=(0.68, 1.0), span_hi=(0.5, 1.0), turn=tn, wfrac=wf)  # white tip, slanted edge
        if layer == 'ink':
            # a hard black stripe inside each shard, on its inner curve
            for sp in shards:
                sp_ = shard_span(sp, t)
                if not sp_ or t > 0.75: continue
                rb, rt = sp_
                shard(bm, sp, rb, rt, band=(0.0, 0.35), span=(0.0, 1.0), turn=shard_turn(sp, t), wfrac=shard_w(sp, f))  # the dark straight side
            # the black radial wedges, f1-3, longer than the shards
            if 1 <= f <= 3:
                for wd in wedges:
                    k = seg(f, 1, 3)
                    rt = wd['L'] * (0.75 + 0.3 * k)
                    rb = 0.2 + 0.45 * k
                    w = wd['w'] * (1 - 0.5 * k)
                    poly(bm, side_pts(wd['a'], rb, rt, lambda s, w=w: w / 2 * ((s / 0.3) ** 0.8 if s < 0.3 else ((1 - s) / 0.7) ** 1.1), 0.0))
    obj(layer, bm, MAT[layer])


for layer in ('body', 'core', 'ink'):
    for f in range(FR):
        build(f, layer)
        scn.render.filepath = os.path.join(OUT, '%s_%s_%02d.png' % (NAME, layer, f))
        bpy.ops.render.render(write_still=True)
print('done', NAME)
