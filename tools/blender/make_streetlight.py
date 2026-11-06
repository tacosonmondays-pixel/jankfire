# Street light: a 6 m tapered octagonal pole on a bolted base, an arm swooping out 1.6 m to a cobra-head lamp,
# matching the map streetlight() boxes. Arm points +x. Cyberpunk city furniture: a neon ring, a junction box covered
# in flyers, and a security camera with googly eyes (it is watching you, but badly).
# run: blender -b --python tools/blender/make_streetlight.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *


def build():
    pole = mat('sl_pole', 0x3a4048, rough=0.35, metal=0.6, tex=tex_noise('sl_pole_t', 0x3a4048, var=0.12, size=16, speck=0x6a4a30, speck_p=0.05, seed=51))
    dark = mat('sl_dark', 0x1e2024, rough=0.5, metal=0.4)
    concrete = mat('sl_concrete', 0x8a8a86, rough=0.9, tex=tex_noise('sl_conc_t', 0x8a8a86, var=0.15, size=16, seed=52))
    lens = mat('sl_lens', 0xffe6f4, rough=0.2, emit=0xffd8ee, strength=4.0)
    neon = mat('sl_neon', 0xff2ad4, rough=0.3, emit=0xff2ad4, strength=4.0)
    white = mat('sl_white', 0xffffff, rough=0.2)
    black = mat('sl_black', 0x050505, rough=0.2)
    red = mat('sl_rec', 0xff1a1a, rough=0.2, emit=0xff1010, strength=3.0)
    def flyers(px):
        rng = np.random.default_rng(9)
        px[:] = hexrgb(0x3a4048)
        cols = [0xff4fd8, 0xffe14d, 0x7dff4f, 0x4fd8ff, 0xffffff, 0xff7a1a]
        for k in range(9):
            x, y = rng.integers(0, 40), rng.integers(0, 50)
            px[y:y + 14, x:x + 12] = hexrgb(cols[k % len(cols)])
        text_px(px, 'LOST', 4, 4, 1, 0x111111); text_px(px, 'CAT', 30, 30, 1, 0x111111); text_px(px, 'RENT', 8, 46, 1, 0xe0102a)
    fly = mat('sl_flyers', 0xffffff, rough=0.6, tex=tex_canvas('sl_fly_t', 56, 64, flyers))
    P = []; A = P.append
    A(box((0.5, 0.12, 0.5), (0, 0.06, 0), concrete, bev=0.02))
    A(lathe([(0.2, 0.12), (0.2, 0.2), (0.14, 0.42), (0.125, 0.5)], (0, 0, 0), pole, seg=8, axis='y'))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        A(cyl(0.025, 0.05, (math.cos(a) * 0.18, 0.15, math.sin(a) * 0.18), dark, axis='y', seg=6))
    A(lathe([(0.125, 0.5), (0.072, 5.85), (0.06, 5.95)], (0, 0, 0), pole, seg=8, axis='y'))
    A(lathe([(0.122, 2.9), (0.115, 3.0)], (0, 0, 0), neon, seg=12, axis='y'))
    A(lathe([(0.113, 3.08), (0.108, 3.18)], (0, 0, 0), neon, seg=12, axis='y'))
    A(box((0.18, 0.4, 0.22), (0, 1.25, -0.14), dark, bev=0.02))  # junction box
    A(box((0.19, 0.38, 0.005), (0, 1.25, -0.252), fly, rot=(0, math.pi, 0)))
    A(lathe([(0.118, 1.6), (0.114, 2.2)], (0, 0, 0), fly, seg=8, axis='y'))
    # arm: rises off the top then swoops out to the head
    pts = [(0, 5.6, 0), (0.05, 5.82, 0), (0.25, 5.95, 0), (0.7, 6.0, 0), (1.25, 5.98, 0), (1.45, 5.94, 0)]
    A(tube(pts, 0.045, pole, seg=8))
    head = ball(0.32, (1.62, 5.86, 0), pole, scale=(1.0, 0.32, 0.6), seg=16, rings=10)
    A(head)
    A(ball(0.25, (1.66, 5.8, 0), lens, scale=(1.0, 0.16, 0.5), seg=16, rings=8))
    # googly security camera on a little bracket
    A(box((0.04, 0.2, 0.04), (0.12, 4.55, 0), dark))
    cam = box((0.16, 0.12, 0.3), (0.2, 4.48, -0.12), mat('sl_cam', 0xe8e8e8, rough=0.3), bev=0.03, rot=(0.25, 0.4, 0))
    A(cam)
    A(cyl(0.045, 0.04, (0.27, 4.43, -0.27), black, axis='z', seg=12, rot=(0.25, 0.4, 0)))
    A(ball(0.015, (0.14, 4.55, -0.22), red, seg=8, rings=6))
    for ex in (-1, 1):
        A(ball(0.04, (0.2 + ex * 0.05, 4.58, -0.2), white, seg=12, rings=8))
        A(ball(0.018, (0.2 + ex * 0.05 + 0.01, 4.575, -0.235), black, seg=8, rings=6))
    for p in P: uv_box(p, 0.3)
    sl = join(P, 'streetlight')
    return finish('p_streetlight', [sl], {'kind': 'prop', 'id': 'streetlight'})


main(build, 'p_streetlight')
