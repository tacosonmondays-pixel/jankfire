# School bus: a conventional (hood out front) full-size school bus: 11 m box + 1 m hood, 2.44 m wide, 3.1 m tall,
# nine windows a side, black rub rails, red + amber warning lights, a stop arm, dual rear wheels. Front = +x.
# Grimy school-bus yellow, a district that doesn't exist, a magenta tag on the back.
# Collision boxes: shared/props.js PROPS.bus.  run: blender -b --python tools/blender/make_bus.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *


def build():
    yel = mat('bus_yellow', 0xffb400, rough=0.3, clearcoat=0.5, tex=tex_noise('bus_yellow_t', 0xffb400, var=0.07, size=32, speck=0x8a6a20, speck_p=0.025, seed=31))
    black = mat('bus_black', 0x161618, rough=0.55)
    glass = mat('bus_glass', 0x1e2c3c, rough=0.06, metal=0.6)
    chrome = mat('bus_chrome', 0xd8dde6, rough=0.12, metal=1.0)
    tire = mat('bus_tire', 0x1c1c1e, rough=0.9)
    rim = mat('bus_rim', 0xd8d8d8, rough=0.35, metal=0.4)
    red = mat('bus_red', 0xff1a2a, rough=0.2, emit=0xff1020, strength=2.5)
    amber = mat('bus_amber', 0xffa020, rough=0.2, emit=0xff9010, strength=2.5)
    head = mat('bus_head', 0xfff4d0, rough=0.2, emit=0xfff0c0, strength=2.0)
    stopm = mat('bus_stop', 0xd01020, rough=0.3)
    def side_draw(px):
        px[:] = hexrgb(0xffb400)
        text_px(px, 'JANKFIRE CO SCHOOLS', 2, 2, 2, 0x111111)
    side_t = mat('bus_lettering', 0xffffff, rough=0.35, tex=tex_canvas('bus_side_t', 232, 18, side_draw))
    def sign_draw(px):
        px[:] = hexrgb(0xffb400)
        text_px(px, 'SCHOOL BUS', 2, 2, 2, 0x111111)
    sign = mat('bus_sign', 0xffffff, rough=0.35, tex=tex_canvas('bus_sign_t', 124, 18, sign_draw))
    def stop_draw(px):
        px[:] = hexrgb(0xd01020); text_px(px, 'STOP', 4, 10, 2, 0xffffff)
    stop_t = mat('bus_stop_t', 0xffffff, rough=0.35, tex=tex_canvas('bus_stopt', 56, 34, stop_draw))
    def tag_draw(px):
        px[:] = hexrgb(0xffb400)
        text_px(px, 'JANK!', 2, 4, 3, 0xff1ad0); text_px(px, 'JANK!', 3, 5, 3, 0x6a0060)
    tag = mat('bus_tag', 0xffffff, rough=0.4, tex=tex_canvas('bus_tag_t', 96, 30, tag_draw))
    P = []; A = P.append
    L, HW = 5.5, 1.22

    # ---------------- box body with a rounded roof, wheel arches cut in
    body = side_x([(-L, 0.48), (L, 0.48), (L, 3.08), (-L, 3.08)], HW * 2, (0, 0, 0), yel, bev=0.16, seg=4)
    for x, r in ((5.75, 0.58), (-2.6, 0.6)):
        for sz in (-1, 1): cut(body, cyl(r, 0.6, (x, 0.5, sz * HW), None, axis='z', seg=32))
    A(body)
    A(side_x([(L - 0.1, 0.5), (6.42, 0.5), (6.55, 0.72), (6.5, 1.42), (6.2, 1.72), (L - 0.1, 1.78)], 2.1, (0, 0, 0), yel, bev=0.1, seg=3))  # hood
    for x, r in ((5.75, 0.55), (-2.6, 0.57)): A(cyl(r, 2.3, (x, 0.52, 0), black, axis='z', seg=24))
    # ---------------- windows, rub rails, lettering
    for sz in (-1, 1):
        z = sz * (HW + 0.005)
        for k in range(9):
            x = -4.75 + k * 1.05
            A(box((0.86, 0.78, 0.03), (x, 2.24, z), glass, bev=0.02))
            A(box((0.86, 0.03, 0.04), (x, 2.3, z), black))  # sash
        for y in (0.78, 1.16, 1.66): A(box((2 * L - 0.2, 0.07, 0.04), (0, y, z), black, bev=0.012))
        A(box((7.2, 0.3, 0.012), (-0.6, 1.41, z + sz * 0.01), side_t, rot=(0, math.pi if sz < 0 else 0, 0)))
        A(box((0.2, 0.14, 0.32), (L + 0.2, 2.5, sz * 1.45), black, bev=0.03))  # mirror
        A(tube([(L - 0.05, 2.2, sz * 1.2), (L + 0.2, 2.45, sz * 1.42)], 0.025, chrome, seg=6))
    A(box((0.04, 0.9, 1.04), (L + 0.005, 2.33, -0.56), glass, bev=0.02))  # windshield
    A(box((0.04, 0.9, 1.04), (L + 0.005, 2.33, 0.56), glass, bev=0.02))
    A(box((0.85, 1.9, 0.04), (4.85, 1.5, HW + 0.01), glass))  # folding door (right side)
    A(box((0.04, 1.9, 0.05), (4.85, 1.5, HW + 0.025), black))
    A(box((0.02, 0.3, 1.6), (L + 0.02, 2.92, 0), sign))
    A(box((0.02, 0.3, 1.6), (-L - 0.02, 2.92, 0), sign, rot=(0, math.pi, 0)))
    A(box((0.02, 0.3, 0.92), (-L - 0.02, 1.4, 0.6), tag, rot=(0, math.pi, 0.08)))
    A(box((0.04, 1.4, 0.7), (-L - 0.005, 2.1, -0.5), glass, bev=0.02))  # rear emergency door window
    A(box((0.04, 1.4, 0.7), (-L - 0.005, 2.1, 0.5), glass, bev=0.02))
    # ---------------- lights, grille, bumpers, stop arm
    for sx, xx in ((1, L + 0.02), (-1, -L - 0.02)):
        for sz in (-1, 1):
            A(cyl(0.1, 0.06, (xx, 2.92, sz * 1.0), red, axis='x', seg=14))
            A(cyl(0.1, 0.06, (xx, 2.92, sz * 0.82), amber, axis='x', seg=14))
    for sz in (-1, 1):
        A(cyl(0.11, 0.06, (6.53, 1.08, sz * 0.72), head, axis='x', seg=16))
        A(cyl(0.12, 0.08, (-L - 0.02, 1.0, sz * 0.9), red, axis='x', seg=16))
    A(box((0.06, 0.6, 1.0), (6.55, 1.06, 0), black, bev=0.03))
    for k in range(6): A(box((0.03, 0.04, 0.96), (6.58, 0.84 + k * 0.09, 0), chrome))
    A(box((0.2, 0.3, 2.4), (6.62, 0.62, 0), black, bev=0.05))
    A(box((0.2, 0.3, 2.44), (-L - 0.08, 0.62, 0), black, bev=0.05))
    oc = cyl(0.24, 0.03, (3.9, 2.0, -HW - 0.12), stopm, axis='z', seg=8, rot=(0, 0, math.pi / 8))
    A(oc); A(box((0.4, 0.26, 0.01), (3.9, 2.0, -HW - 0.14), stop_t, rot=(0, math.pi, 0)))
    A(box((0.08, 0.08, 0.14), (3.9, 2.0, -HW - 0.05), black))
    # ---------------- wheels (dual rear)
    for sz in (-1, 1):
        P.extend(wheel(0.5, 0.3, (5.75, 0.5, sz * 1.06), tire, rim, spokes=8))
        P.extend(wheel(0.52, 0.28, (-2.6, 0.52, sz * 1.1), tire, rim, spokes=8))
        P.extend(wheel(0.52, 0.28, (-2.6, 0.52, sz * 0.8), tire, rim, spokes=8))
    for p in P: uv_box(p, 0.4)
    bus = join(P, 'bus')
    return finish('p_bus', [bus], {'kind': 'prop', 'id': 'bus'})


main(build, 'p_bus')
