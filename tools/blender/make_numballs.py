# Number balls: glossy late-90s toy-CG balls, 1 m across, one per digit 0-9 (nodes n0..n9), each a candy colour
# with a white disc and its number on the front (+x) and two googly eyes looking at you. Upbeat and a bit creepy.
# Far LOD (lod1, from 40 m): far() below, one under each ball. farlod.main keeps the shipped lod0 byte for byte and adds
# them (--fresh: all new). NB the game must read lod1 names as Blender wrote them: three renames lod1.001 to lod1001
# (propfield.js isLod1 checks o.name; userData.name keeps the original), else balls 1-9 draw their far ball up close too.
# run: blender -b --python tools/blender/make_numballs.py -- [--qa] [--no-sheet] [--fresh]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import farlod

COLS = [0xf4f4f4, 0xff2a3a, 0xff8a1a, 0xffe14d, 0x4fe04f, 0x2ad8e8, 0x2a6aff, 0x9a4aff, 0x2a2a30, 0xff4fd8]


def build():
    white = mat('nb_white', 0xffffff, rough=0.15, clearcoat=1.0)
    black = mat('nb_black', 0x050505, rough=0.1)
    nodes, fars = [], []
    R = 0.5
    for d in range(10):
        ox = d * 1.25
        shell = mat(f'nb_shell{d}', COLS[d], rough=0.08, clearcoat=1.0, metal=0.05)
        ink = 0x111111 if d != 8 else 0xffffff
        def draw(px, d=d, ink=ink):
            px[:] = hexrgb(0xffffff if d != 8 else 0x2a2a30)
            # big centred digit: 5x7 font at scale 4 = 20 x 28
            text_px(px, str(d), 6, 2, 4, ink if d != 0 else 0xff2a3a)  # 5x7 at x4 = 20 x 28, centred
        face = mat(f'nb_face{d}', 0xffffff, rough=0.15, clearcoat=1.0, tex=tex_canvas(f'nb_face{d}_t', 32, 32, draw))
        P = [ball(R, (ox, R, 0), shell, seg=28, rings=18)]
        # the number disc, pushed into the front of the ball (front = +x)
        disc = cyl(0.27, 0.06, (ox + R - 0.005, R - 0.04, 0), face, axis='x', seg=28, bev=0.015)
        P.append(disc)
        for ez in (-1, 1):  # googly eyes up top, looking out the front
            P.append(ball(0.12, (ox + 0.33, R + 0.34, ez * 0.15), white, scale=(0.6, 1, 1), seg=16, rings=10))
            P.append(ball(0.055, (ox + 0.41, R + 0.31 + (0.02 if d % 2 else -0.01), ez * 0.15 + (0.03 if d % 3 else -0.02)), black, scale=(0.5, 1, 1), seg=12, rings=8))
        for p in P[:1] + P[2:]: uv_box(p, 0.6)
        apply_mods(disc); uv_planar(disc, (ox + R, R - 0.04, 0), 0.54, 'x')
        n = part(P, f'n{d}', pivot=(ox, 0, 0))  # origin on the floor under the ball: the game drops each variant at its spot
        nodes.append(n)
        fars.append((n, far(d, ox, shell, face, white, black)))
    root = finish('p_numball', nodes, {'kind': 'prop', 'id': 'numball', 'variants': [f'n{d}' for d in range(10)], 'lod': 40})
    for n, F in fars: farlod.attach_far(n, [join(F, n.name + '_far')])  # (each ball's own: the game draws a variant's subtree)
    return root


def far(d, ox, shell, face, white, black):
    """lod1 of one ball, from 40 m on (~290 tris, the same paints): a 12-sided ball, the number disc, the googly eyes"""
    R = 0.5
    F = [ball(R, (ox, R, 0), shell, seg=12, rings=7, name=f'n{d}_far_ball')]
    for ez in (-1, 1):
        F.append(ball(0.12, (ox + 0.33, R + 0.34, ez * 0.15), white, scale=(0.6, 1, 1), seg=6, rings=4, name=f'n{d}_far_eye'))
        F.append(ball(0.055, (ox + 0.41, R + 0.31 + (0.02 if d % 2 else -0.01), ez * 0.15 + (0.03 if d % 3 else -0.02)), black, scale=(0.5, 1, 1), seg=6, rings=3, name=f'n{d}_far_pupil'))
    for p in F: uv_box(p, 0.6)
    disc = cyl(0.27, 0.125, (ox + 0.4625, R - 0.04, 0), face, axis='x', seg=8, name=f'n{d}_far_disc')  # (its back sunk in the ball: no gap round it)
    apply_mods(disc); uv_planar(disc, (ox + R, R - 0.04, 0), 0.54, 'x')
    uv = disc.data.uv_layers.active.data
    for poly in disc.data.polygons:  # the rim: a patch of the picture's corner (its background), not a zero-area line
        if abs(poly.normal.x) > 0.9: continue
        for k, li in enumerate(poly.loop_indices): uv[li].uv = ((0.03, 0.03), (0.09, 0.03), (0.09, 0.09), (0.03, 0.09))[k % 4]
    return F + [disc]


farlod.main(build, 'p_numball', res=(900, 360))
