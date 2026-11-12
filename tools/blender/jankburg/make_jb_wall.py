# JANKBURG's firewall (shared/jankburg.js cityWall()): the 6 m wall module p_jb_wall and the merlon p_jb_merlon.
# The firewall is a 14 m precast concrete city wall: board-formed panels with tie holes and lift lines, a plinth with a
# hazard band, pilasters on every joint (half on each module, so modules butt into whole ones), a steel channel near
# the top on both faces with the pink neon tube in it, a coping you can run along (anti-slip, a yellow edge line on the
# city side), CCTV and conduit outside, wall-pack lamps and a cable run inside, grime streaking down from the top.
# Four art variants (nodes v0..v3): v1 / v2 say FIRE / WALL in big stencil on the outside (the map puts them next to
# each other, so it reads FIREWALL from out in the sprawl), v3 has a YOU ARE NOW LEAVING THE PRODUCT plate outside,
# v2 a ☺ STAY INSIDE poster and a tag on the city side.
# Module frame: x along the wall (-3..3), y up (0..14), outside at -z (the wall is z -2..2). The map fits a module onto
# each full-height piece of the wall boxes, stretched to whole modules. Look only: the boxes stay the collision.
# Merlon frame: x along (-0.7..0.7), y 0..1.2 from the walkway, z -0.4..0.4, outside at -z.
# run: blender52 -b --python tools/blender/jankburg/make_jb_wall.py -- [--qa] [--no-sheet] [--no-export] [--only=wall,merlon]
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector
import jbkit as K
from jbkit import ARGV, Atlas, boxa, fill_uv, mesh, face_dir, lathe_closed, noise, concrete, stencil, CONC
import lib
from lib import mat, text_px, hexrgb, px_disc, px_line, rod

ONLY = set(next((a.split('=', 1)[1] for a in ARGV if a.startswith('--only=')), '').split(',')) - {''}
rng = np.random.default_rng(180)
HW, WH, T = 3.0, 14.0, 2.0  # half a module, wall height, half its thickness


# ------------------------------------------------------------ the atlas (shared look for both files)
A = Atlas('jbw_atlas', 512, 256, 0x7d8294)
FW, FH = 80, 150  # a face cell: 6 m x 12.9 m
for i in range(4):
    v = A.add(f'O{i}', i * FW, 0, FW, FH); concrete(v, 10 + i)
stencil(A.add('O1', 80, 0, FW, FH), 'FIRE', 62, 3, 0xffd8f0, seed=3)
stencil(A.add('O2', 160, 0, FW, FH), 'WALL', 62, 3, 0xffd8f0, seed=4)
v = A.add('O3', 240, 0, FW, FH)  # the plate: YOU ARE NOW LEAVING THE PRODUCT
v[52:92, 6:74] = hexrgb(0x111018); v[54:90, 8:72] = hexrgb(0xffe14d)
for k in range(0, 64, 6): v[54:57, 8 + k:11 + k] = hexrgb(0x111018); v[87:90, 11 + k:14 + k] = hexrgb(0x111018)
for txt, row in (('YOU ARE NOW', 59), ('LEAVING THE', 68), ('PRODUCT', 77)):
    tw = len(txt) * 6 - 1; text_px(v, txt, 40 - tw // 2, row, 1, 0x111018)
v[92:110, 20] *= 0.6; v[92:104, 61] *= 0.6  # rust runs off its bolts
for i, key in enumerate(('I0', 'I1')):
    v = A.add(key, 320 + i * FW, 0, FW, FH); concrete(v, 30 + i)
v = A.add('I1', 400, 0, FW, FH)  # ☺ STAY INSIDE poster, a tag
v[40:104, 18:62] = hexrgb(0xff4fd8) * (0.9 + 0.1 * rng.random((64, 44, 1)))
px_disc(v, 40, 62, 15, 0xffe14d); px_disc(v, 34, 57, 2.5, 0x111018); px_disc(v, 46, 57, 2.5, 0x111018)
px_disc(v, 40, 63, 9, 0x111018, r_in=7.4, a0=math.pi * 0.6, a1=math.pi * 1.4)
text_px(v, 'STAY', 28, 82, 1, 0xffffff); text_px(v, 'INSIDE', 22, 91, 1, 0xffffff)
v[40:104:9, 18:62] *= 0.93  # fold lines
v[95:104, 50:62] = hexrgb(CONC) * 0.95  # torn corner
stencil(v, 'JANK', 116, 2, 0x39ff14, wear=0.05, seed=9)
for c in (26, 33, 47, 55): v[130:130 + int(4 + 8 * rng.random()), c] = hexrgb(0x39ff14)  # drips
v = A.add('pil', 480, 0, 16, FH); concrete(v, 41, lifts=False); v[:, :2] *= 1.12; v[:, -2:] *= 0.8
v[70:78, 5:11] = hexrgb(0xff4fd8)  # a reflector
v = A.add('walk', 80, 160, 80, 48); v[:] = hexrgb(0x6a6e7a) * (0.88 + 0.16 * noise(48, 80, rng, 4, 0.6)[..., None])
v[::4, ::4] *= 0.8; v[41:45] = hexrgb(0xffe14d); v[3:5] = hexrgb(0x55596a)
v = A.add('plinth', 0, 160, 80, 14); concrete(v, 50, lifts=False); v[:] *= 0.82
for k in range(-4, 80, 8): v[:3, max(0, k):max(0, k + 4)] = hexrgb(0xffe14d)
v[:3][v[:3].sum(2) < 1.5] = hexrgb(0x111018)
v = A.add('coping', 0, 176, 80, 8); concrete(v, 51, lifts=False); v[:] *= 1.12
for key, x, c in (('conc', 160, CONC), ('metal', 176, 0x5a5f6e), ('dark', 192, 0x24222c), ('yellow', 208, 0xffe14d), ('red', 224, 0xff3030), ('white', 240, 0xeeeeee)):
    v = A.add(key, x, 160, 16, 16); v[:] = hexrgb(c) * (0.92 + 0.1 * rng.random((16, 16, 1)))
M = mat('jbw_wall', 0xffffff, rough=0.62, tex=A.image())
GLOW = mat('glow', 0xff4fd8, rough=0.3, emit=0xff4fd8, strength=2.0)
LAMP = mat('glow_lamp', 0xfff2c8, rough=0.3, emit=0xfff2c8, strength=1.5)  # (its own name: the game's 'glow' is one colour)


# ------------------------------------------------------------ the wall module
def module(v):
    """lod0 parts, lod1 parts for variant v"""
    P, Q = [], []
    O, I = f'O{v}', ('I1' if v == 2 else 'I0')
    P.append(boxa(f'w{v}_core', (-HW + 0.35, 0.8, -T), (HW - 0.35, 13.7, T), M, A, {'-z': O, '+z': I}))
    P.append(boxa(f'w{v}_plinth', (-HW, 0, -T - 0.15), (HW, 0.8, T + 0.15), M, A, {'-z': 'plinth', '+z': 'plinth', '+y': 'conc', '-x': 'conc', '+x': 'conc'}))
    P.append(boxa(f'w{v}_coping', (-HW, 13.7, -T - 0.15), (HW, WH, T + 0.15), M, A, {'-z': 'coping', '+z': 'coping', '+y': 'walk', '-y': 'conc', '-x': 'conc', '+x': 'conc'}))
    for ex in (-1, 1):  # half pilasters on the joints (the core runs under them)
        x0, x1 = sorted((ex * HW, ex * (HW - 0.35)))
        P.append(boxa(f'w{v}_pil', (x0, 0.8, -T - 0.2), (x1, 13.7, T + 0.2), M, A, {'-z': 'pil', '+z': 'pil', '-x': 'conc', '+x': 'conc', '-y': 'conc'}))
    for s in (-1, 1):  # the neon channel, both faces: lips, the tube
        f = s * T
        for y0, y1 in ((11.7, 11.8), (12.4, 12.5)):
            lo, hi = (-HW + 0.351, y0, min(f, f + s * 0.2)), (HW - 0.351, y1, max(f, f + s * 0.2))
            cells = {'+y': 'metal', '-y': 'metal', ('-z' if s < 0 else '+z'): 'metal'}
            P.append(boxa(f'w{v}_lip', lo, hi, M, A, cells))
        P.append(fill_uv(rod((-HW + 0.351, 12.1, f + s * 0.1), (HW - 0.351, 12.1, f + s * 0.1), 0.11, GLOW, seg=8, name=f'w{v}_tube'), A, 'conc'))
        Q.append(boxa(f'w{v}_l1tube', (-HW, 11.9, min(f, f + s * 0.06)), (HW, 12.3, max(f, f + s * 0.06)), GLOW, A, {('-z' if s < 0 else '+z'): 'conc', '+y': 'conc', '-y': 'conc'}))
    # outside: conduit with junction boxes; CCTV on v0 / v2
    P.append(rod((-HW + 0.351, 10.9, -T - 0.09), (HW - 0.351, 10.9, -T - 0.09), 0.07, M, seg=8, name=f'w{v}_conduit')); fill_uv(P[-1], A, 'metal')
    for x in (-1.6, 1.4):
        P.append(boxa(f'w{v}_jbox', (x - 0.18, 10.72, -T - 0.2), (x + 0.18, 11.1, -T + 0.01), M, A, {'all': 'dark'}))
    if v in (0, 2):
        cx = 1.9 if v == 0 else -1.9
        P.append(boxa(f'w{v}_cam_arm', (cx - 0.06, 13.04, -T - 0.7), (cx + 0.06, 13.16, -T + 0.01), M, A, {'all': 'metal'}))
        P.append(boxa(f'w{v}_cam', (cx - 0.15, 12.68, -T - 0.98), (cx + 0.15, 13.0, -T - 0.42), M, A, {'all': 'white'}))
        P.append(boxa(f'w{v}_cam_hood', (cx - 0.18, 13.0, -T - 1.04), (cx + 0.18, 13.04, -T - 0.4), M, A, {'all': 'dark'}))
        P.append(boxa(f'w{v}_cam_led', (cx + 0.06, 12.76, -T - 0.995), (cx + 0.12, 12.82, -T - 0.96), GLOW, A, {'all': 'red'}))
    # inside: a cable tray low down and a wall-pack lamp
    P.append(boxa(f'w{v}_tray', (-HW + 0.351, 3.0, T - 0.01), (HW - 0.351, 3.12, T + 0.32), M, A, {'all': 'metal'}))
    P.append(boxa(f'w{v}_tray_lip', (-HW + 0.351, 2.99, T + 0.32), (HW - 0.351, 3.3, T + 0.34), M, A, {'all': 'metal'}))
    P.append(boxa(f'w{v}_lamp', (-0.28, 9.3, T - 0.01), (0.28, 9.72, T + 0.28), M, A, {'all': 'dark'}))
    P.append(boxa(f'w{v}_lamp_lens', (-0.22, 9.299, T + 0.04), (0.22, 9.3, T + 0.24), LAMP, A, {'-y': 'white'}))
    # lod1: one box with the face art, the coping walk on top, the neon strips (above)
    Q.append(boxa(f'w{v}_l1', (-HW, 0, -T), (HW, WH, T), M, A, {'-z': O, '+z': I, '+y': 'walk', '-x': 'conc', '+x': 'conc'}))
    return P, Q


def merlon():
    P = [boxa('m_block', (-0.7, 0, -0.4), (0.7, 1.02, 0.4), M, A, {'-z': 'coping', '+z': 'coping', '-x': 'conc', '+x': 'conc'})]
    # a cap sloping out (rain off the walkway), a pink LED strip outside
    v = [(-0.75, 1.0, -0.45), (0.75, 1.0, -0.45), (0.75, 1.0, 0.45), (-0.75, 1.0, 0.45), (-0.75, 1.12, -0.45), (0.75, 1.12, -0.45), (0.75, 1.2, 0.45), (-0.75, 1.2, 0.45)]
    f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    cap = K.outward(mesh('m_cap', v, f, M)); fill_uv(cap, A, 'conc'); P.append(cap)
    P.append(boxa('m_led', (-0.5, 0.7, -0.42), (0.5, 0.78, -0.399), GLOW, A, {'-z': 'conc', '+y': 'conc', '-y': 'conc', '-x': 'conc', '+x': 'conc'}))
    Q = [boxa('m1', (-0.7, 0, -0.4), (0.7, 1.2, 0.4), M, A, {'-z': 'coping', '+z': 'coping', '-x': 'conc', '+x': 'conc', '+y': 'conc'})]
    return P, Q


# ------------------------------------------------------------ build + export
def variant_node(name, P, Q, qa_tag):
    m0 = K.joined(P, name + '_lod0'); m1 = K.joined(Q, name + '_lod1')
    if '--qa' in ARGV: K.qa([m0], qa_tag + ' lod0'); K.qa([m1], qa_tag + ' lod1')
    lib.bake_ao([m0], dist=0.8); lib.bake_ao([m1], dist=0.8)
    e = lib._link(bpy.data.objects.new(name, None))
    l1 = lib._link(bpy.data.objects.new('lod1', None)); l1.parent = e
    m0.parent = e; m1.parent = l1
    print(f'JF_PART {name}: lod0 {K.tris(m0)} tris, lod1 {K.tris(m1)} tris, extent {K.extent([m0])}')
    return e, m0, m1


def build_wall():
    lib.reset(); lib._mats.clear()
    globals().update(M=mat('jbw_wall', 0xffffff, rough=0.62, tex=A.image()), GLOW=mat('glow', 0xff4fd8, rough=0.3, emit=0xff4fd8, strength=2.0),
                     LAMP=mat('glow_lamp', 0xfff2c8, rough=0.3, emit=0xfff2c8, strength=1.5))
    nodes = []
    for v in range(4):
        P, Q = module(v); nodes.append(variant_node(f'v{v}', P, Q, f'wall v{v}'))
    root = lib.finish('p_jb_wall', [n[0] for n in nodes], {'id': 'jb_wall', 'kind': 'prop', 'lod': 110, 'tint': False, 'box': [[-HW, 0, -T], [HW, WH, T]]})
    if '--no-export' not in ARGV: lib.export(root, 'p_jb_wall')
    if '--no-sheet' not in ARGV:  # the sheet: the four variants side by side, near LOD
        for i, (e, m0, m1) in enumerate(nodes):
            e.location = lib.gv((i - 1.5) * 6.0, 0, 0); m1.hide_render = True
        lib.sheet(root, 'p_jb_wall', extra_note='FIREWALL MODULES V0-V3', exposure=-0.2)


def build_merlon():
    lib.reset(); lib._mats.clear()
    globals().update(M=mat('jbw_wall', 0xffffff, rough=0.62, tex=A.image()), GLOW=mat('glow', 0xff4fd8, rough=0.3, emit=0xff4fd8, strength=2.0))
    P, Q = merlon()
    m0 = K.joined(P, 'merlon_lod0'); m1 = K.joined(Q, 'merlon_lod1')
    if '--qa' in ARGV: K.qa([m0], 'merlon lod0'); K.qa([m1], 'merlon lod1')
    lib.bake_ao([m0], dist=0.3); lib.bake_ao([m1], dist=0.3)
    root = lib.prop_finish('p_jb_merlon', [m0], [m1], {'id': 'jb_merlon', 'kind': 'prop', 'lod': 60, 'tint': False, 'box': [[-0.7, 0, -0.4], [0.7, 1.2, 0.4]]})
    lib.prop_stats(root)
    if '--no-export' not in ARGV: lib.export(root, 'p_jb_merlon')
    if '--no-sheet' not in ARGV:
        e = next(c for c in root.children if c.name.startswith('lod1')); e.parent = None; m1.hide_render = True
        lib.sheet(root, 'p_jb_merlon', extra_note='FIREWALL MERLON', exposure=-0.2)


if not ONLY or 'wall' in ONLY: build_wall()
if not ONLY or 'merlon' in ONLY: build_merlon()
