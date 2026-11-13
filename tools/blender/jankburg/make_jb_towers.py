# JANKBURG's firewall towers (shared/jankburg.js cityWall()): p_jb_tower (the 16 guard towers on the wall, every 60 m),
# p_jb_cornertower (the 4 fat towers on the chamfered corners) and p_jb_chamfer (the stepped piers of the chamfers).
# Same precast concrete as the wall modules (jbkit.concrete): a guard tower is a 9 m concrete shaft with corner ribs,
# glowing slit windows, a big ☺ CORP roundel outside and a STAFF ONLY door inside, a watch crown on top (the pink neon
# band, a ribbon of dark glass, the roof slab you land on from the jump pad, a parapet with a steel cap), floodlights on
# the outside corners and a radio mast with a red beacon. The corner bastions are the same idea fatter, the roof flat and
# open; the chamfer piers are 4.6 m wall piers with the neon channel on every face.
# Frames: centred on the boxes' footprint, y up from the ground, the outside at -z.
#   tower:  x / z -4.5..4.5 (roof + parapet -5..5), y 0..23.4
#   corner: x / z -5.5..5.5 (roof -5.8..5.8), y 0..24.4
#   pier:   x / z -2.3..2.3, y 0..14
# Look only: the boxes stay the collision (the jump pad at the tower's foot is the map's, untouched).
# run: blender52 -b --python tools/blender/jankburg/make_jb_towers.py -- [--qa] [--no-sheet] [--no-export] [--only=tower,corner,pier]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
import jbkit as K
from jbkit import ARGV, Atlas, boxa, fill_uv, mesh, noise, concrete, stencil, CONC
import lib
from lib import mat, text_px, hexrgb, px_disc, rod

ONLY = set(next((a.split('=', 1)[1] for a in ARGV if a.startswith('--only=')), '').split(',')) - {''}
rng = np.random.default_rng(60)


# ------------------------------------------------------------ the atlas
def slits(v, cols, y0, y1, ppm=7.2):
    """tall slit windows: dark glass with a pink glow low down in them (someone's in there)"""
    h, w = v.shape[:2]
    for cx in cols:
        a, b = int(cx * w) - 2, int(cx * w) + 2
        r0, r1 = h - int(y1 * ppm), h - int(y0 * ppm)
        v[r0 - 1:r1 + 1, a - 1:b + 1] = hexrgb(0x3a3d4a)
        g = np.linspace(0, 1, r1 - r0)[:, None, None]
        v[r0:r1, a:b] = hexrgb(0x1a1424) * (1 - g) + hexrgb(0xb02a9a) * g


def roundel(v, cx, cy, R):
    px_disc(v, cx, cy, R, 0xff4fd8); px_disc(v, cx, cy, R - 2, 0xffe14d)
    px_disc(v, cx - R * 0.35, cy - R * 0.25, max(1.5, R * 0.12), 0x111018); px_disc(v, cx + R * 0.35, cy - R * 0.25, max(1.5, R * 0.12), 0x111018)
    px_disc(v, cx, cy + R * 0.05, R * 0.55, 0x111018, r_in=R * 0.42, a0=math.pi * 0.6, a1=math.pi * 1.4)


A = Atlas('jbt_atlas', 512, 256, CONC)
TW, TH = 64, 136  # tower shaft faces: 9 m x 19 m
v = A.add('T_out', 0, 0, TW, TH); concrete(v, 61, ppm=7.2); roundel(v, 32, 40, 17); slits(v, (0.25, 0.5, 0.75), 3.0, 9.5)
text_px(v, 'JANKCORP', 9, 62, 1, 0xffe0f4)
v = A.add('T_in', 64, 0, TW, TH); concrete(v, 62, ppm=7.2); slits(v, (0.3, 0.7), 6.0, 15.0)
v[TH - 22:TH - 11, 16:48] = hexrgb(0x111018); v[TH - 21:TH - 12, 17:47] = hexrgb(0xffe14d)  # STAFF ONLY over the door
text_px(v, 'STAFF', 18, TH - 20, 1, 0x111018)
v = A.add('T_side', 128, 0, TW, TH); concrete(v, 63, ppm=7.2); slits(v, (0.35, 0.65), 4.0, 16.0)
CW, CH_ = 78, 150  # corner bastion faces: 11 m x 21 m
v = A.add('C_face', 192, 0, CW, CH_); concrete(v, 64, ppm=7.1); roundel(v, 39, 46, 22); slits(v, (0.2, 0.8), 3.0, 12.0)
stencil(v, 'SECURITY', 76, 1, 0xffe0f4, wear=0.1, seed=5)
PW, PH = 33, 100  # chamfer piers: 4.6 m x 14 m
v = A.add('P_face', 272, 0, PW, PH); concrete(v, 65, ppm=7.1)
v = A.add('ribbon', 320, 0, 64, 16); v[:] = hexrgb(0x1c1830); v[::4] = hexrgb(0x5a5f6e); v[:, ::8] = hexrgb(0x5a5f6e)
v[6:12] += np.array([0.25, 0.05, 0.2]) * rng.random((6, 64, 1))  # lights behind the glass
v = A.add('walk', 320, 16, 64, 64); v[:] = hexrgb(0x6a6e7a) * (0.88 + 0.16 * noise(64, 64, rng, 4, 0.6)[..., None]); v[::4, ::4] *= 0.8
px_disc(v, 32, 32, 22, 0xff4fd8, r_in=19); text_px(v, 'PAD', 24, 29, 1, 0xff4fd8)
v = A.add('walk2', 384, 16, 64, 64); v[:] = hexrgb(0x6a6e7a) * (0.88 + 0.16 * noise(64, 64, rng, 4, 0.6)[..., None]); v[::4, ::4] *= 0.8
v[:3] = v[-3:] = v[:, :3] = v[:, -3:] = hexrgb(0xffe14d)
v = A.add('plinth', 320, 80, 64, 10); concrete(v, 66, lifts=False); v[:] *= 0.82
for k in range(-4, 64, 8): v[:3, max(0, k):max(0, k + 4)] = hexrgb(0xffe14d)
v[:3][v[:3].sum(2) < 1.5] = hexrgb(0x111018)
v = A.add('rib', 384, 80, 16, 64); concrete(v, 67, lifts=False); v[:] *= 1.08
for key, x, c in (('conc', 448, CONC), ('metal', 464, 0x5a5f6e), ('dark', 480, 0x24222c), ('yellow', 496, 0xffe14d), ('white', 448, 0xeeeeee), ('fascia', 464, 0x3a3e4c)):
    y = 16 if key in ('conc', 'metal', 'dark', 'yellow') else 32
    v = A.add(key, x, y, 16, 16); v[:] = hexrgb(c) * (0.92 + 0.1 * rng.random((16, 16, 1)))


def mats():
    lib.reset(); lib._mats.clear()
    return (mat('jbt_tower', 0xffffff, rough=0.62, tex=A.image()), mat('glow', 0xff4fd8, rough=0.3, emit=0xff4fd8, strength=2.0),
            mat('glow_lamp', 0xfff2c8, rough=0.3, emit=0xfff2c8, strength=1.5), mat('glass', 0x2a2440, rough=0.08, metal=0.3, clearcoat=1.0))


def ring_boxes(name, h0, h1, y0, y1, M, cells):
    """a square ring: outer half-size h0, inner h1 (four boxes, mitre-free: the x ones run full length)"""
    return [boxa(name, (-h0, y0, -h0), (h0, y1, -h1), M, A, cells), boxa(name, (-h0, y0, h1), (h0, y1, h0), M, A, cells),
            boxa(name, (-h0, y0, -h1 + 0.001), (-h1, y1, h1 - 0.001), M, A, {k: c for k, c in cells.items() if k not in ('-z', '+z')}),
            boxa(name, (h1, y0, -h1 + 0.001), (h0, y1, h1 - 0.001), M, A, {k: c for k, c in cells.items() if k not in ('-z', '+z')})]


# ------------------------------------------------------------ the guard tower
def tower():
    M, GLOW, LAMP, GLASS = mats()
    P, Q = [], []
    S = 4.5
    P.append(boxa('t_shaft', (-S, 1.2, -S), (S, 19.0, S), M, A, {'-z': 'T_out', '+z': 'T_in', '-x': 'T_side', '+x': 'T_side'}))
    P.append(boxa('t_plinth', (-S - 0.15, 0, -S - 0.15), (S + 0.15, 1.2, S + 0.15), M, A, {'-z': 'plinth', '+z': 'plinth', '-x': 'plinth', '+x': 'plinth', '+y': 'conc'}))
    P.append(boxa('t_doorframe', (-0.9, 0, S - 0.01), (0.9, 2.75, S + 0.24), M, A, {'+z': 'metal', '-x': 'metal', '+x': 'metal', '+y': 'metal'}))
    P.append(boxa('t_door', (-0.72, 0, S + 0.24), (0.72, 2.55, S + 0.27), M, A, {'+z': 'dark', '-x': 'dark', '+x': 'dark', '+y': 'dark'}))
    P.append(boxa('t_handle', (0.45, 1.1, S + 0.27), (0.6, 1.16, S + 0.33), M, A, {'all': 'yellow'}))
    for sx in (-1, 1):  # corner ribs
        for sz in (-1, 1):
            x0, x1 = sorted((sx * (S - 0.45), sx * (S + 0.15))); z0, z1 = sorted((sz * (S - 0.45), sz * (S + 0.15)))
            P.append(boxa('t_rib', (x0, 1.2, z0), (x1, 19.0, z1), M, A, {'-z': 'rib', '+z': 'rib', '-x': 'rib', '+x': 'rib'}))
    # the crown: neon band, the ribbon window, the roof slab's fascia, the parapet with its cap
    P.append(boxa('t_neon', (-S - 0.1, 19.0, -S - 0.1), (S + 0.1, 19.6, S + 0.1), GLOW, A, {'-z': 'conc', '+z': 'conc', '-x': 'conc', '+x': 'conc', '-y': 'conc'}))
    P.append(boxa('t_ribbon', (-S - 0.05, 19.6, -S - 0.05), (S + 0.05, 21.9, S + 0.05), GLASS, A, {'-z': 'ribbon', '+z': 'ribbon', '-x': 'ribbon', '+x': 'ribbon'}))
    for k in range(-4, 5, 2):  # mullions
        for s in (-1, 1):
            P.append(boxa('t_mull', (k * 1.0 - 0.06, 19.6, s * (S + 0.05) - 0.08 * (s < 0)), (k * 1.0 + 0.06, 21.9, s * (S + 0.05) + 0.08 * (s > 0)), M, A, {'all': 'metal'}))
            P.append(boxa('t_mull', (s * (S + 0.05) - 0.08 * (s < 0), 19.6, k * 1.0 - 0.06), (s * (S + 0.05) + 0.08 * (s > 0), 21.9, k * 1.0 + 0.06), M, A, {'all': 'metal'}))
    P.append(boxa('t_roof', (-5, 21.9, -5), (5, 22.4, 5), M, A, {'-z': 'fascia', '+z': 'fascia', '-x': 'fascia', '+x': 'fascia', '-y': 'conc'}))
    P.append(boxa('t_deck', (-4.6, 22.4, -4.6), (4.6, 22.401, 4.6), M, A, {'+y': 'walk'}))
    P += ring_boxes('t_parapet', 5, 4.6, 22.4, 23.3, M, {'-z': 'conc', '+z': 'conc', '-x': 'conc', '+x': 'conc'})
    P += ring_boxes('t_cap', 5.05, 4.55, 23.3, 23.4, M, {'-z': 'metal', '+z': 'metal', '-x': 'metal', '+x': 'metal', '+y': 'metal', '-y': 'metal'})
    # floodlights on the outside corners, a mast with a beacon on the inside corner
    for sx in (-1, 1):
        x = sx * 4.3
        P.append(boxa('t_flood_arm', (x - 0.06, 23.4, -4.9), (x + 0.06, 23.9, -4.7), M, A, {'all': 'metal'}))
        P.append(boxa('t_flood', (x - 0.35, 23.9, -5.3), (x + 0.35, 24.3, -4.6), M, A, {'all': 'dark'}))
        P.append(boxa('t_flood_lens', (x - 0.3, 23.95, -5.32), (x + 0.3, 24.25, -5.29), LAMP, A, {'all': 'white'}))
    P.append(fill_uv(rod((3.9, 22.4, 3.9), (3.9, 28.0, 3.9), 0.06, M, seg=6, name='t_mast'), A, 'metal'))
    P.append(fill_uv(rod((3.9, 25.0, 3.9), (3.9, 25.0, 3.0), 0.03, M, seg=6, name='t_mast_arm'), A, 'metal'))
    b = K.lathe_closed('t_beacon', [(0.02, 0.0), (0.14, 0.0), (0.14, 0.2), (0.02, 0.3)], (3.9, 28.0, 3.9), GLOW, seg=8); fill_uv(b, A, 'conc'); P.append(b)
    # far: the shaft, the crown, the roof (no parapet detail)
    Q.append(boxa('t1_shaft', (-S, 0, -S), (S, 19.0, S), M, A, {'-z': 'T_out', '+z': 'T_in', '-x': 'T_side', '+x': 'T_side'}))
    Q.append(boxa('t1_neon', (-S - 0.05, 19.0, -S - 0.05), (S + 0.05, 19.6, S + 0.05), GLOW, A, {'all': 'conc'}))
    Q.append(boxa('t1_crown', (-S, 19.6, -S), (S, 21.9, S), GLASS, A, {'-z': 'ribbon', '+z': 'ribbon', '-x': 'ribbon', '+x': 'ribbon'}))
    Q.append(boxa('t1_top', (-5, 21.9, -5), (5, 23.4, 5), M, A, {'-z': 'fascia', '+z': 'fascia', '-x': 'fascia', '+x': 'fascia', '+y': 'walk', '-y': 'conc'}))
    return P, Q, ((-5, 0, -5), (5, 23.4, 5))


# ------------------------------------------------------------ the corner bastion
def corner():
    M, GLOW, LAMP, GLASS = mats()
    P, Q = [], []
    S = 5.5
    P.append(boxa('c_shaft', (-S, 1.2, -S), (S, 21.0, S), M, A, {'-z': 'C_face', '+z': 'C_face', '-x': 'C_face', '+x': 'C_face'}))
    P.append(boxa('c_plinth', (-S - 0.15, 0, -S - 0.15), (S + 0.15, 1.2, S + 0.15), M, A, {'-z': 'plinth', '+z': 'plinth', '-x': 'plinth', '+x': 'plinth', '+y': 'conc'}))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * (S - 0.55), sx * (S + 0.18))); z0, z1 = sorted((sz * (S - 0.55), sz * (S + 0.18)))
            P.append(boxa('c_rib', (x0, 1.2, z0), (x1, 21.0, z1), M, A, {'-z': 'rib', '+z': 'rib', '-x': 'rib', '+x': 'rib'}))
    P.append(boxa('c_neon', (-S - 0.1, 21.0, -S - 0.1), (S + 0.1, 21.6, S + 0.1), GLOW, A, {'-z': 'conc', '+z': 'conc', '-x': 'conc', '+x': 'conc', '-y': 'conc'}))
    P.append(boxa('c_ribbon', (-S - 0.05, 21.6, -S - 0.05), (S + 0.05, 23.9, S + 0.05), GLASS, A, {'-z': 'ribbon', '+z': 'ribbon', '-x': 'ribbon', '+x': 'ribbon'}))
    for k in range(-5, 6, 2):
        for s in (-1, 1):
            P.append(boxa('c_mull', (k * 1.0 - 0.06, 21.6, s * (S + 0.05) - 0.08 * (s < 0)), (k * 1.0 + 0.06, 23.9, s * (S + 0.05) + 0.08 * (s > 0)), M, A, {'all': 'metal'}))
            P.append(boxa('c_mull', (s * (S + 0.05) - 0.08 * (s < 0), 21.6, k * 1.0 - 0.06), (s * (S + 0.05) + 0.08 * (s > 0), 23.9, k * 1.0 + 0.06), M, A, {'all': 'metal'}))
    P.append(boxa('c_roof', (-5.8, 23.9, -5.8), (5.8, 24.4, 5.8), M, A, {'-z': 'fascia', '+z': 'fascia', '-x': 'fascia', '+x': 'fascia', '-y': 'conc', '+y': 'walk2'}))
    for sx in (-1, 1):
        for sz in (-1, 1):  # beacons on the roof corners (flush studs: nothing to trip on)
            P.append(boxa('c_stud', (sx * 5.45 - 0.12, 24.4, sz * 5.45 - 0.12), (sx * 5.45 + 0.12, 24.48, sz * 5.45 + 0.12), GLOW, A, {'all': 'conc'}))
    Q.append(boxa('c1_shaft', (-S, 0, -S), (S, 21.0, S), M, A, {'-z': 'C_face', '+z': 'C_face', '-x': 'C_face', '+x': 'C_face'}))
    Q.append(boxa('c1_neon', (-S - 0.05, 21.0, -S - 0.05), (S + 0.05, 21.6, S + 0.05), GLOW, A, {'all': 'conc'}))
    Q.append(boxa('c1_crown', (-S, 21.6, -S), (S, 23.9, S), GLASS, A, {'-z': 'ribbon', '+z': 'ribbon', '-x': 'ribbon', '+x': 'ribbon'}))
    Q.append(boxa('c1_top', (-5.8, 23.9, -5.8), (5.8, 24.4, 5.8), M, A, {'-z': 'fascia', '+z': 'fascia', '-x': 'fascia', '+x': 'fascia', '+y': 'walk2', '-y': 'conc'}))
    return P, Q, ((-5.8, 0, -5.8), (5.8, 24.4, 5.8))


# ------------------------------------------------------------ the chamfer pier
def pier():
    M, GLOW, LAMP, GLASS = mats()
    S = 2.3
    P = [boxa('p_body', (-S, 0.8, -S), (S, 13.7, S), M, A, {'-z': 'P_face', '+z': 'P_face', '-x': 'P_face', '+x': 'P_face'}),
         boxa('p_plinth', (-S - 0.12, 0, -S - 0.12), (S + 0.12, 0.8, S + 0.12), M, A, {'-z': 'plinth', '+z': 'plinth', '-x': 'plinth', '+x': 'plinth', '+y': 'conc'}),
         boxa('p_cap', (-S - 0.12, 13.7, -S - 0.12), (S + 0.12, 14.0, S + 0.12), M, A, {'-z': 'metal', '+z': 'metal', '-x': 'metal', '+x': 'metal', '+y': 'walk2', '-y': 'conc'}),
         boxa('p_neon', (-S - 0.08, 11.8, -S - 0.08), (S + 0.08, 12.4, S + 0.08), GLOW, A, {'-z': 'conc', '+z': 'conc', '-x': 'conc', '+x': 'conc', '-y': 'conc', '+y': 'conc'})]
    Q = [boxa('p1', (-S, 0, -S), (S, 14.0, S), M, A, {'-z': 'P_face', '+z': 'P_face', '-x': 'P_face', '+x': 'P_face', '+y': 'walk2'})]
    return P, Q, ((-S, 0, -S), (S, 14.0, S))


def build(fid, fn, lod, note):
    P, Q, box = fn()
    m0 = K.joined(P, fid + '_lod0'); m1 = K.joined(Q, fid + '_lod1')
    if '--qa' in ARGV: K.qa([m0], fid + ' lod0'); K.qa([m1], fid + ' lod1')
    lib.bake_ao([m0], dist=0.8); lib.bake_ao([m1], dist=0.8)
    root = lib.prop_finish(fid, [m0], [m1], {'id': fid[2:], 'kind': 'prop', 'lod': lod, 'tint': False, 'box': [list(box[0]), list(box[1])]})
    lib.prop_stats(root)
    if '--no-export' not in ARGV: lib.export(root, fid)
    if '--no-sheet' not in ARGV:
        e = next(c for c in root.children if c.name.startswith('lod1')); e.parent = None; m1.hide_render = True
        lib.sheet(root, fid, extra_note=note, exposure=-0.2)


for key, fid, fn, lod, note in (('tower', 'p_jb_tower', tower, 140, 'FIREWALL TOWER'), ('corner', 'p_jb_cornertower', corner, 160, 'FIREWALL CORNER'), ('pier', 'p_jb_chamfer', pier, 90, 'CHAMFER PIER')):
    if not ONLY or key in ONLY: build(fid, fn, lod, note)
