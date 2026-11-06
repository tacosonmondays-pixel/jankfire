# Pallets: a standard 1200 x 800 x 144 mm four-way block pallet (5 top boards, 3 stringer boards, 9 blocks, 3 bottom
# boards) in crusty pine, and the same pallet loaded with three layers of shrink-wrapped cardboard boxes.
# p_pallet + p_pallet_load. Collision boxes: shared/props.js.  run: blender -b --python tools/blender/make_pallet.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *


def pallet(pine, block, ox=0):
    P = []
    for z, w in ((-0.3275, 0.145), (-0.1588, 0.1), (0, 0.145), (0.1588, 0.1), (0.3275, 0.145)):  # top boards
        P.append(box((1.2, 0.022, w), (ox, 0.133, z), pine, bev=0.004))
    for x in (-0.5275, 0, 0.5275):  # stringer boards
        P.append(box((0.145, 0.022, 0.8), (ox + x, 0.111, 0), pine, bev=0.003))
        for z in (-0.35, 0, 0.35):
            P.append(box((0.145, 0.078, 0.1 if z else 0.145), (ox + x, 0.061, z), block, bev=0.004))
    for z in (-0.3275, 0, 0.3275):  # bottom boards
        P.append(box((1.2, 0.022, 0.145 if z else 0.145), (ox, 0.011, z), pine, bev=0.003))
    for n in (8, 9):
        P.append(cyl(0.004, 0.006, (ox - 0.52 + (n - 8) * 1.04, 0.145, 0.33), mat('pl_nail', 0x8a8a90, rough=0.3, metal=1.0), axis='y', seg=6))
    return P


def build():
    pine = mat('pl_pine', 0xd2a868, rough=0.75, tex=tex_wood('pl_pine_t', 0xdcb070, 0x9a6a30, size=32, seed=41, rings=5))
    def stamp(px):
        px[:] = hexrgb(0xc89a5a); text_px(px, 'JF', 3, 3, 2, 0x3a1a08)
    block = mat('pl_block', 0xc89a5a, rough=0.8, tex=tex_canvas('pl_block_t', 28, 20, stamp))
    card = mat('pl_card', 0xb8874e, rough=0.85, tex=tex_noise('pl_card_t', 0xb8874e, var=0.08, size=16, seed=5))
    tape = mat('pl_tape', 0xc9a060, rough=0.3)
    def label(px):
        px[:] = hexrgb(0xf4f4f0); px[:3] = hexrgb(0xe0102a)
        text_px(px, 'FRAGILE', 3, 6, 1, 0xe0102a); text_px(px, 'MAYBE', 3, 15, 1, 0x111111)
    lab = mat('pl_label', 0xffffff, rough=0.5, tex=tex_canvas('pl_label_t', 48, 24, label))
    wrap = mat('pl_wrap', 0xdfeeff, rough=0.3, alpha=0.2)
    out = []
    a = pallet(pine, block)
    for p in a: uv_box(p, 0.2)
    out.append((finish('p_pallet', [join(a, 'pallet')], {'kind': 'prop', 'id': 'pallet'}), 'p_pallet'))
    b = pallet(pine, block, ox=0)
    rnd = random.Random(4)
    for layer in range(3):
        for ix in (-1, 1):
            for iz in (-1, 1):
                h = 0.37
                y = 0.144 + layer * 0.38 + h / 2
                x, z = ix * 0.29, iz * 0.19
                bx_ = box((0.56, h, 0.36), (x, y, z), card, bev=0.012, rot=(0, rnd.uniform(-0.03, 0.03), 0))
                b.append(bx_)
                b.append(box((0.565, 0.05, 0.08), (x, y + h / 2 - 0.02, z), tape))
                if layer < 2 and ix == 1 and iz == -1:
                    b.append(box((0.18, 0.1, 0.005), (x + 0.12, y, z - 0.181), lab))
    b.append(box((1.19, 1.17, 0.79), (0, 0.144 + 1.17 / 2, 0), wrap))
    for p in b: uv_box(p, 0.2)
    out.append((finish('p_pallet_load', [join(b, 'pallet_load')], {'kind': 'prop', 'id': 'pallet_load'}), 'p_pallet_load'))
    return out


main_multi(build)
