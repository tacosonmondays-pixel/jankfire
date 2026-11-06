# Number balls: glossy late-90s toy-CG balls, 1 m across, one per digit 0-9 (nodes n0..n9), each a candy colour
# with a white disc and its number on the front (+x) and two googly eyes looking at you. Upbeat and a bit creepy.
# run: blender -b --python tools/blender/make_numballs.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

COLS = [0xf4f4f4, 0xff2a3a, 0xff8a1a, 0xffe14d, 0x4fe04f, 0x2ad8e8, 0x2a6aff, 0x9a4aff, 0x2a2a30, 0xff4fd8]


def build():
    white = mat('nb_white', 0xffffff, rough=0.15, clearcoat=1.0)
    black = mat('nb_black', 0x050505, rough=0.1)
    nodes = []
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
    return finish('p_numball', nodes, {'kind': 'prop', 'id': 'numball', 'variants': [f'n{d}' for d in range(10)]})


main(build, 'p_numball', res=(900, 360))
