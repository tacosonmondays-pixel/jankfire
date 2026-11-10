# OVERDUE, The Bottom: dressing for the Long Stairs (shared/city/bottom.js, x -48..-40: 8 m wide, steps about 1.27 m
# deep and 0.27 m high, a stepped solid rail each side, poles with neon). Like the cube kit, every piece sits ON the
# collision boxes at scale 1, so the stairs you see are the stairs you stand on. The stair climbs toward -z.
#   longstep_a / _b  a worn stone nosing for one step, 8 m wide: a rounded, chipped lip, a drain groove behind it, a
#                    patch where somebody repaired it. origin: the step top's front (downhill) edge, middle of the
#                    stair. the riser's pastel paint stays the map's (it is repainted every week)
#   longrail         a coping for one block of the stepped rail (0.3 thick, 2 steps = ~2.55 m long): a rounded stone cap
#                    2.62 long (open ended, they overlap), a welded pipe handrail climbing 0.54 to the next block, a
#                    bracket. origin: the rail block's TOP, at its downhill end, middle of its thickness
#   longpole         a lamp post 6.5 m tall for the neon: a tapered pole on a bolted foot, a 1.9 m arm with a stay, a sign
#                    frame for the map's neon box (y 5.2-5.9), a cable. origin: its foot. the arm reaches toward -x
#   longplaque_a / _b  a settler's name plaque set in a step, 0.62 x 0.36: bone tablet, a carved name, a jam jar of
#                    flowers. origin: on the step top, its middle
# -> public/models/story/s_<id>.glb + tools/blender/sheets/story/s_<id>.jpg
# run: blender -b --python tools/blender/make_story_longstairs.py [-- --only longrail] [--no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bottom_kit import *

INK = 0x141018
PINK, YEL, CYAN, GREEN, RED = 0xff4fd8, 0xffe14d, 0x4fd8ff, 0x39ff14, 0xff3030
W = 8.0


def plain(name, col, rough=0.5, metal=0.0, cc=0.0, var=0.08, speck=None, p=0.0, seed=1, size=16):
    return mat(name, col, rough=rough, metal=metal, clearcoat=cc, tex=tex_noise(name + '_t', col, var=var, size=size, speck=speck, speck_p=p, seed=seed))


def tiled(objs, m, size=0.3):
    for o in objs:
        if o.data.materials and o.data.materials[0] == m: uv_tile(o, size)


def stone_m(tag, seed): return plain(tag + '_stone', 0xe8ded4, rough=0.8, var=0.1, speck=0xa89a8c, p=0.1, seed=seed, size=32)


def nosing(seed, chips, patch_x):
    st = stone_m('ls%d' % seed, 310 + seed)
    dark = plain('ls%d_dark' % seed, 0x6a5e58, rough=0.9, var=0.1, seed=320 + seed)
    patch = plain('ls%d_patch' % seed, 0xb8b0a8, rough=0.7, var=0.06, seed=330 + seed)
    O = []
    # the lip in lengths, a gap where a piece has gone
    x = -W / 2; k = 0
    while x < W / 2 - 0.01:
        L = min(W / 2 - x, 0.9 + ((k * 37 + seed * 11) % 5) * 0.22)
        if k not in chips:
            O.append(cyl(0.035, L - 0.05, (x + L / 2, -0.012, -0.004 + 0.006 * ((k + seed) % 3 - 1)), st, axis='x', seg=6))
            O.append(box((L - 0.012, 0.012, 0.16), (x + L / 2, 0.006, -0.08), st))
        else:
            O.append(box((L * 0.5, 0.01, 0.1), (x + L * 0.3, 0.005, -0.06), dark))  # the scar
            O.append(box((0.16, 0.05, 0.1), (x + L * 0.6, 0.025, 0.12), st, rot=(0.2, 0.7, 0.1), bev=0.01, seg=1))  # the bit, lying on the step below
        x += L; k += 1
    O.append(box((W - 0.3, 0.004, 0.03), (0, 0.002, -0.2), dark))  # drain groove
    O.append(box((0.9, 0.008, 0.5), (patch_x, 0.004, -0.5), patch, rot=(0, 0.08, 0)))  # a repair
    tiled(O, st, 0.6)
    return O


def build_longstep_a(): return nosing(1, (3,), -1.6), {'origin': "the step top's downhill edge, middle of the stair; climbs -z", 'width': W}
def build_longstep_b(): return nosing(2, (1, 6), 2.2), {'origin': "the step top's downhill edge, middle of the stair; climbs -z", 'width': W}


def build_longrail():
    """one block's coping and its handrail"""
    st = stone_m('lr', 341)
    pipe = plain('lr_paint', 0xffffff, rough=0.4, cc=0.4, var=0.08, speck=0x9a5a3a, p=0.1, seed=342)  # the rail takes the variant's colour
    rs = plain('lr_rust', 0x9a5a3a, rough=0.8, var=0.16, speck=0x5a2a18, p=0.12, seed=343, size=32)
    L = 2.62
    O = []
    O.append(box((0.38, 0.06, L), (0, 0.03, -L / 2 + 0.03), st))  # the cap slab (no bevel, no end worth seeing: they overlap)
    O.append(cyl(0.05, L - 0.03, (-0.19, 0.035, -L / 2 + 0.03), st, axis='z', seg=6)); O.append(cyl(0.05, L - 0.03, (0.19, 0.035, -L / 2 + 0.03), st, axis='z', seg=6))
    for z in (-0.25, -1.5): O.append(box((0.05, 0.36, 0.05), (0, 0.24, z), rs))  # two posts
    O.append(rod((0, 0.42, 0.1), (0, 0.42 + 0.54, -2.65), 0.03, pipe, seg=6))  # the handrail, climbing to the next block
    O.append(rod((0, 0.42 + 0.05, -0.25), (0, 0.42 + 0.3, -1.5), 0.012, rs, seg=4))  # a stay
    O.append(ball(0.045, (0, 0.42, 0.1), pipe, seg=6, rings=4))  # the end knob (buried in the block below's rail)
    tiled(O, st, 0.6)
    return O, {'paint': ['lr_paint'], 'origin': "the rail block's top at its downhill end, middle of its 0.3 thickness; climbs -z", 'length': L, 'open_ends': True}


def build_longpole():
    steel = plain('lp2_steel', 0x6a707a, rough=0.5, metal=0.6, var=0.1, speck=0x9a5a3a, p=0.1, seed=351, size=32)
    rs = plain('lp2_rust', 0x9a5a3a, rough=0.8, var=0.16, speck=0x5a2a18, p=0.12, seed=352, size=32)
    dark = plain('lp2_dark', 0x18181c, rough=0.7, seed=353)
    D = Atlas('lp2_decal_t', 48, 32); s = D.sub(0, 0, 24, 24); s[:] = hexrgb(YEL); smiley(s, 12, 12, 9, face=YEL, ink=INK)
    t = D.sub(24, 0, 24, 32); crust(t, 0xfff6e0, 0.04, seed=2); write(t, 'lost', 2, 3, 1, RED, bold=True); write(t, 'cat', 4, 13, 1, INK); write(t, 'no', 6, 22, 1, INK)
    decal = mat('lp2_decal', 0xffffff, rough=0.6, tex=D.image())
    O = []
    O.append(box((0.34, 0.03, 0.34), (0, 0.015, 0), steel, bev=0.006, seg=1))
    for sx in (-1, 1):
        for sz in (-1, 1): O.append(cyl(0.02, 0.03, (sx * 0.12, 0.04, sz * 0.12), dark, axis='y', seg=6))
    O.append(cyl(0.1, 6.45, (0, 3.25, 0), steel, axis='y', seg=8, r2=0.065))
    O.append(cyl(0.12, 0.5, (0, 0.28, 0), steel, axis='y', seg=8))  # the access box at its foot
    O.append(box((0.1, 0.18, 0.012), (0, 0.3, -0.118), dark))
    O.append(rod((0, 5.95, 0), (-1.9, 6.05, 0), 0.035, steel, seg=6))  # the arm
    O.append(rod((0, 5.2, 0), (-1.2, 6.0, 0), 0.016, rs, seg=5))  # its stay
    for (x0, x1) in ((-1.9, -0.25),):  # the sign frame the map's neon box sits in (y 5.2 - 5.9)
        for y in (5.16, 5.94): O.append(rod((x0, y, 0.0), (x1, y, 0.0), 0.014, rs, seg=4))
        for x in (x0, x1): O.append(rod((x, 5.16, 0.0), (x, 6.02, 0.0), 0.014, rs, seg=4))
    O.append(sweep([(0, 6.45, 0), (0.3, 6.3, 0.2), (1.4, 5.9, 0.5), (2.6, 6.1, 0.7)], 0.012, dark, seg=4, name='cable'))
    O.append(uv_fit(box((0.14, 0.14, 0.003), (0.02, 1.5, -0.094), decal, rot=(0, 0, 0.15)), D.rect(0, 0, 24, 24)))
    O.append(uv_fit(box((0.16, 0.22, 0.003), (-0.01, 1.15, -0.098), decal, rot=(0, 0, -0.08)), D.rect(24, 0, 24, 32)))
    tiled(O, steel, 0.5)
    return O, {'origin': 'its foot; the arm reaches toward -x', 'h': 6.5, 'arm': 1.9}


def plaque(seed, name, flowers):
    bone = plain('pq%d_bone' % seed, 0xf4ecd8, rough=0.5, cc=0.3, var=0.06, speck=0xc8b89a, p=0.08, seed=360 + seed, size=32)
    D = Atlas('pq%d_t' % seed, 64, 32); px = D.sub(0, 0, 64, 32); crust(px, 0xf4ecd8, 0.04, seed=seed)
    write(px, name, max(2, (64 - tw(name)) // 2), 8, 1, 0x6a5e58, bold=True); write(px, 'still here', 6, 20, 1, 0xa89a8c)
    face = mat('pq%d_face' % seed, 0xffffff, rough=0.5, tex=D.image())
    O = []
    O.append(box((0.62, 0.03, 0.36), (0, 0.015, 0), bone, bev=0.006, seg=1))
    O.append(uv_fit(box((0.56, 0.003, 0.3), (0, 0.0315, 0), face), D.rect(0, 0, 64, 32), mode='top') if False else uv_fit(box((0.56, 0.003, 0.3), (0, 0.0315, 0), face), D.rect(0, 0, 64, 32)))
    if flowers:
        O.append(cyl(0.04, 0.1, (0.24, 0.0845, -0.1), mat('pq%d_jar' % seed, 0xd8f4ff, rough=0.06, clearcoat=1.0), axis='y', seg=8))
        for k, c in enumerate((PINK, YEL, 0xffffff)):
            a = k * 2.1
            O.append(rod((0.24, 0.1, -0.1), (0.24 + math.cos(a) * 0.05, 0.26 + k * 0.02, -0.1 + math.sin(a) * 0.05), 0.005, plain('pq%d_stem' % seed, 0x4f9a3a, rough=0.6, seed=370 + seed), seg=4))
            O.append(ball(0.025, (0.24 + math.cos(a) * 0.05, 0.27 + k * 0.02, -0.1 + math.sin(a) * 0.05), plain('pq%d_f%d' % (seed, k), c, rough=0.5, seed=380 + k), seg=6, rings=4))
    else:
        O.append(cyl(0.03, 0.012, (-0.2, 0.0405, 0.1), plain('pq%d_coin' % seed, 0xd8a840, rough=0.2, metal=1.0, seed=390), axis='y', seg=8))  # a coin somebody left
    return O


def build_longplaque_a(): return plaque(1, 'doris', True), {'origin': 'on the step top, its middle', 'size': [0.62, 0.36]}
def build_longplaque_b(): return plaque(2, 'big len', False), {'origin': 'on the step top, its middle', 'size': [0.62, 0.36]}


BUILDERS = [('longstep_a', build_longstep_a), ('longstep_b', build_longstep_b), ('longrail', build_longrail), ('longpole', build_longpole),
            ('longplaque_a', build_longplaque_a), ('longplaque_b', build_longplaque_b)]
run(BUILDERS)
