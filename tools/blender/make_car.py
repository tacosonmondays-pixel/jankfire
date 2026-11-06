# Car: a chunky late-90s four-door (4.6 m long, 1.84 m wide, 2.8 m wheelbase, 0.66 m tyres), matching the boxes the
# maps already use for cars (shared/map.js car()). Front = +x. Candy clear-coat paint in a material called car_paint
# (the game repaints it per car), chrome bumpers, glowing lights, a magenta underglow and a bad bumper sticker.
# run: blender -b --python tools/blender/make_car.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *


def build():
    paint = mat('car_paint', 0xc8202c, rough=0.22, metal=0.25, clearcoat=1.0)
    glass = mat('car_glass', 0x1a2a3a, rough=0.06, metal=0.6)
    chrome = mat('car_chrome', 0xd8dde6, rough=0.12, metal=1.0)
    black = mat('car_trim', 0x141416, rough=0.6)
    tire = mat('car_tire', 0x1c1c1e, rough=0.9)
    head = mat('car_head', 0xfff4d0, rough=0.2, emit=0xfff0c0, strength=2.0)
    tail = mat('car_tail', 0xff1a2a, rough=0.2, emit=0xff1020, strength=2.5)
    amber = mat('car_amber', 0xffa020, rough=0.2, emit=0xff9010, strength=2.0)
    glow = mat('car_underglow', 0xff2ad4, rough=0.4, emit=0xff2ad4, strength=4.0)
    def plate_draw(px):
        px[:] = hexrgb(0xf2f2f2); px[:2] = px[-2:] = hexrgb(0x2050b0)
        text_px(px, 'JNK-420', 3, 4, 1, 0x111111)
    plate = mat('car_plate', 0xffffff, rough=0.4, tex=tex_canvas('car_plate_t', 48, 16, plate_draw))
    def stick_draw(px):
        px[:] = hexrgb(0x7dff4f); text_px(px, 'HONK IF', 3, 3, 1, 0x101010); text_px(px, 'U R JANK', 3, 12, 1, 0xff1aa0)
    sticker = mat('car_sticker', 0xffffff, rough=0.5, tex=tex_canvas('car_sticker_t', 56, 22, stick_draw))
    P = []
    A = P.append

    # ---------------- body shell: one rounded side profile, wheel arches cut into each flank
    body = side_x([(-2.26, 0.30), (2.24, 0.30), (2.3, 0.5), (2.22, 0.8), (1.15, 0.97), (-1.2, 1.0), (-2.16, 0.97), (-2.29, 0.74)], 1.82, (0, 0, 0), paint, bev=0.07, seg=3)
    for x in (-1.45, 1.35):
        for sz in (-1, 1):
            cut(body, cyl(0.41, 0.42, (x, 0.33, sz * 0.82), None, axis='z', seg=28))
    A(body)
    for x in (-1.45, 1.35):  # dark wheel wells
        A(cyl(0.39, 1.2, (x, 0.36, 0), black, axis='z', seg=24))
    # ---------------- greenhouse: glass block, roof, pillars
    A(side_x([(-1.22, 0.96), (1.13, 0.96), (0.6, 1.47), (-0.8, 1.49), (-1.08, 1.36)], 1.58, (0, 0, 0), glass, bev=0.05))
    A(side_x([(-0.86, 1.43), (0.62, 1.42), (0.56, 1.52), (-0.8, 1.54)], 1.62, (0, 0, 0), paint, bev=0.05))
    for sz in (-1, 1):
        z = sz * 0.79
        A(tube([(1.13, 0.97, z), (0.6, 1.47, z)], 0.045, paint, seg=8))   # A pillar
        A(tube([(-1.22, 0.97, z), (-0.85, 1.47, z)], 0.07, paint, seg=8))  # C pillar
        A(box((0.11, 0.5, 0.05), (-0.12, 1.22, z), black, bev=0.015))      # B pillar
        A(box((0.2, 0.1, 0.12), (0.98, 1.06, sz * 0.95), paint, bev=0.03))  # mirror
        A(box((0.03, 0.08, 0.1), (0.9, 1.06, sz * 0.95), glass))
        for x in (-0.12, 1.02):  # door seams
            A(box((0.012, 0.6, 0.012), (x, 0.66, sz * 0.912), black))
        for x in (0.62, -0.55):  # handles
            A(box((0.16, 0.03, 0.03), (x, 0.86, sz * 0.92), chrome, bev=0.01))
        A(box((4.2, 0.04, 0.02), (0, 0.42, sz * 0.915), black))  # rub strip
    # ---------------- nose + tail: bumpers, grille, lights, plates
    for sx in (-1, 1):
        A(box((0.16, 0.2, 1.8), (sx * 2.28, 0.42, 0), chrome, bev=0.06, seg=3))
    A(box((0.05, 0.16, 0.7), (2.27, 0.68, 0), black, bev=0.02))  # grille
    for k in range(5):
        A(box((0.02, 0.012, 0.66), (2.29, 0.62 + k * 0.03, 0), chrome))
    for sz in (-1, 1):
        A(box((0.06, 0.13, 0.32), (2.24, 0.7, sz * 0.62), head, bev=0.03))
        A(box((0.06, 0.06, 0.12), (2.24, 0.58, sz * 0.8), amber, bev=0.02))
        A(box((0.06, 0.16, 0.36), (-2.26, 0.75, sz * 0.62), tail, bev=0.03))
    A(box((0.02, 0.14, 0.42), (2.37, 0.42, 0), plate))
    A(box((0.02, 0.14, 0.42), (-2.37, 0.62, 0), plate, rot=(0, math.pi, 0)))
    A(box((0.02, 0.16, 0.4), (-2.2, 0.86, 0.38), sticker, rot=(0, math.pi, -0.18)))
    A(box((3.4, 0.03, 1.5), (0, 0.2, 0), glow))  # underglow
    for x in (-1.45, 1.35):
        for sz in (-1, 1):
            P.extend(wheel(0.33, 0.23, (x, 0.33, sz * 0.8), tire, chrome, spokes=5))
    for p in P: uv_box(p, 0.25)
    car = join(P, 'car')
    return finish('p_car', [car], {'kind': 'prop', 'id': 'car', 'paint': 'car_paint'})


main(build, 'p_car', res=(640, 420))
