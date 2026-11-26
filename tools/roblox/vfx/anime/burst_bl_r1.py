# Anime hit burst flipbook, rendered in Blender (the VFX session, 26 Nov 2026).
#
# Flat geometry rebuilt every frame under an orthographic camera (no meshes go to Roblox: it all ends up in the sheet):
#   body  sharp tapered spikes shooting out of the hit and detaching from it (tinted per weapon, additive)
#   core  a white flash disc that hollows into a widening ring, and the hot inner half of each spike (additive)
#   ink   short black spikes between the coloured ones (normal blend: the two-tone accent)
# 16 frames at 30 fps; the burst is done by frame ~9, the rest are its last specks.
#
#   blender -b --factory-startup -P burst_bl.py -- <spec.json>
# spec: {"out": dir, "name": "burst_a", "frames": 16, "px": 256, "spikes": 11, "minor": 9, "seed": 4, "samples": 12}
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
FR = int(spec.get('frames', 16))
PX = int(spec.get('px', 256)) * int(spec.get('ss', 2))
NS = int(spec.get('spikes', 5))
NM = int(spec.get('minor', 4))
rng = random.Random(int(spec.get('seed', 4)))
os.makedirs(OUT, exist_ok=True)

scn = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
scn.render.engine = 'CYCLES'
scn.cycles.device = 'CPU'
scn.cycles.samples = int(spec.get('samples', 12))
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
cam_d.ortho_scale = 2.1
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


MAT = {'body': emissive('body', 0.65), 'body_dim': emissive('body_dim', 0.62), 'core': emissive('core', 1.0), 'ink': emissive('ink', 0.0)}

# the spikes: main ones (coloured) and minor ones (black, between them), each with its own angle, length and width
main = []
axis = rng.uniform(0, math.pi)
for i in range(NS):
    a = (i + rng.uniform(-0.35, 0.35)) / NS * math.tau
    main.append(dict(a=a, L=rng.uniform(0.45, 0.8), w=rng.uniform(0.09, 0.14), lag=rng.uniform(0, 0.06)))
# two long ones on one axis: the emphasis an anime hit draws through its middle
for a in (axis, axis + math.pi):
    main.append(dict(a=a + rng.uniform(-0.08, 0.08), L=1.0, w=0.13, lag=0.0))
minor = []
for i in range(NM):
    a = (i + 0.5 + rng.uniform(-0.25, 0.25)) / NM * math.tau
    minor.append(dict(a=a, L=rng.uniform(0.38, 0.66), w=rng.uniform(0.08, 0.14), lag=rng.uniform(0, 0.05)))
# the flash: a four-point star, long points 4x the short ones (the critic's), turned a little off square
STAR = []
tw = rng.uniform(-0.25, 0.25)
for i in range(8):
    r = (1.0 if i % 2 == 0 else 0.16) * (rng.uniform(0.9, 1.1) if i % 2 == 0 else 1.0)
    if i in (2, 6): r *= 0.62  # the cross arms shorter than the main pair: long:short points about 1.6, points:waist 4+
    STAR.append((tw + i / 8 * math.tau, r))
# the ring breaks into arcs with gaps
GAPS = sorted(rng.uniform(0, math.tau) for _ in range(5))


def ease_out(x): return 1 - (1 - x) ** 3
def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def seg(t, a, b): return min(1, max(0, (t - a) / (b - a)))


def spike(bm, a, rb, rt, wb):
    # a tapered spike from radius rb to its tip at rt, wb wide at the base, slightly curved (a hand-drawn stroke)
    if rt - rb < 0.01 or wb < 0.002: return
    c, s = math.cos(a), math.sin(a)
    px, py = -s, c
    bend = 0.06 * (rt - rb)
    pts = [(c * rb + px * wb / 2, s * rb + py * wb / 2), (c * (rb + rt) / 2 + px * (wb * 0.32 + bend), s * (rb + rt) / 2 + py * (wb * 0.32 + bend)),
           (c * rt + px * bend * 0.5, s * rt + py * bend * 0.5), (c * (rb + rt) / 2 - px * (wb * 0.32 - bend), s * (rb + rt) / 2 - py * (wb * 0.32 - bend)),
           (c * rb - px * wb / 2, s * rb - py * wb / 2)]
    vs = [bm.verts.new((x, y, 0)) for x, y in pts]
    bm.faces.new(vs)


def ring(bm, r0, r1, n=72):
    if r1 - r0 < 0.004: return
    outer = [bm.verts.new((math.cos(i / n * math.tau) * r1, math.sin(i / n * math.tau) * r1, 0)) for i in range(n)]
    if r0 <= 0.001:
        bm.faces.new(outer)
        return
    inner = [bm.verts.new((math.cos(i / n * math.tau) * r0, math.sin(i / n * math.tau) * r0, 0)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((inner[i], inner[j], outer[j], outer[i]))


def star(bm, R):
    vs = [bm.verts.new((math.cos(a) * r * R, math.sin(a) * r * R, 0)) for a, r in STAR]
    bm.faces.new(vs)


def broken_ring(bm, r0, r1, n=96):
    if r1 - r0 < 0.004: return
    keep = [not any(abs(((i / n * math.tau) - g + math.pi) % math.tau - math.pi) < 0.22 for g in GAPS) for i in range(n)]
    for i in range(n):
        if not (keep[i] and keep[(i + 1) % n]): continue
        a0, a1 = i / n * math.tau, (i + 1) / n * math.tau
        v = [bm.verts.new((math.cos(a) * r, math.sin(a) * r, 0)) for a, r in ((a0, r0), (a1, r0), (a1, r1), (a0, r1))]
        bm.faces.new(v)


def obj(name, bm, mat, z):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location.z = z
    ob.data.materials.append(mat)
    scn.collection.objects.link(ob)
    return ob


def build(f, layer):
    for o in [o for o in bpy.data.objects if o.type == 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
    t = min(1.0, f / 7.0)  # the burst is done in 8 frames; the rest of the sheet stays empty
    bm = bmesh.new()
    if f > 7:
        obj('empty', bm, MAT['core'], 0)
        return
    if layer == 'body':
        for sp in main:
            k = max(0.0, t - sp['lag'])
            rt = sp['L'] * (0.45 + 0.55 * ease_out(seg(k, 0, 0.2))) * (1 + 0.15 * seg(k, 0.2, 0.6))
            rb = sp['L'] * (0.12 + 0.78 * smooth(seg(k, 0.08, 0.55)))
            wb = sp['w'] * (1 - 0.75 * smooth(seg(k, 0.05, 0.55)))
            if k < 0.62: spike(bm, sp['a'], rb, rt, wb)
        obj('body', bm, MAT['body'], 0)
    elif layer == 'core':
        # the flash: a jagged star for two frames, then a thin broken ring that widens and goes by frame 5
        if t < 0.1: star(bm, 0.95)
        elif t < 0.2: star(bm, 0.55)
        if 0.1 <= t < 0.45:
            r1 = 0.45 + 0.4 * ease_out(seg(t, 0.1, 0.45))
            broken_ring(bm, r1 - 0.06 * (1 - seg(t, 0.1, 0.45)) - 0.014, r1)
        # the hot inner part of each spike, shorter and narrower
        for sp in main:
            k = max(0.0, t - sp['lag'])
            rt = sp['L'] * (0.45 + 0.55 * ease_out(seg(k, 0, 0.2))) * (1 + 0.15 * seg(k, 0.2, 0.6))
            rb = sp['L'] * (0.12 + 0.78 * smooth(seg(k, 0.08, 0.55)))
            wb = sp['w'] * 0.45 * (1 - 0.75 * smooth(seg(k, 0.05, 0.55)))
            if k < 0.45: spike(bm, sp['a'], rb, rb + (rt - rb) * 0.7, wb)
        obj('core', bm, MAT['core'], 0.01)
    elif layer == 'ink':
        for sp in main:
            k = max(0.0, t - sp['lag'])
            if k < 0.12 or k > 0.6: continue
            rt = sp['L'] * (0.45 + 0.55 * ease_out(seg(k, 0, 0.2))) * (1 + 0.15 * seg(k, 0.2, 0.6))
            rb = sp['L'] * (0.12 + 0.78 * smooth(seg(k, 0.08, 0.55)))
            wb = sp['w'] * 0.32 * (1 - 0.75 * smooth(seg(k, 0.05, 0.55)))
            spike(bm, sp['a'], rb + (rt - rb) * 0.25, rb + (rt - rb) * 0.8, wb)
        for sp in minor:
            k = max(0.0, t - sp['lag'])
            if k > 0.45: continue
            rt = sp['L'] * (0.5 + 0.5 * ease_out(seg(k, 0, 0.2)))
            rb = sp['L'] * (0.25 + 0.65 * smooth(seg(k, 0.1, 0.5)))
            spike(bm, sp['a'], rb, rt, sp['w'] * (1 - 0.6 * smooth(seg(k, 0.1, 0.5))))
        obj('ink', bm, MAT['ink'], 0.02)


for layer in ('body', 'core', 'ink'):
    for f in range(FR):
        build(f, layer)
        scn.render.filepath = os.path.join(OUT, '%s_%s_%02d.png' % (NAME, layer, f))
        bpy.ops.render.render(write_still=True)
print('done', NAME)
