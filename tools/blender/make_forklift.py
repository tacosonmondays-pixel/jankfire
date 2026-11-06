# Forklift: a 3-tonne sit-down counterbalance truck (2.4 m body, big rounded counterweight, overhead guard, two-stage
# mast, carriage + load backrest, 1.2 m forks), matching the Warehouse forklift boxes. Front (forks) = +x.
# Grimy safety yellow, hazard-striped counterweight, an amber beacon, a sticker that lies.
# run: blender -b --python tools/blender/make_forklift.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *


def build():
    yel = mat('fk_yellow', 0xf2b705, rough=0.3, clearcoat=0.6, tex=tex_noise('fk_yellow_t', 0xf2b705, var=0.08, size=32, speck=0x6a5a20, speck_p=0.03, seed=21))
    cw = mat('fk_counter', 0x2a2c30, rough=0.45, metal=0.3)
    haz = mat('fk_hazard', 0xffd21a, rough=0.4, tex=tex_stripes('fk_haz_t', 0xffd21a, 0x141414, size=32, width=4))
    steel = mat('fk_steel', 0x3a3d44, rough=0.4, metal=0.7)
    chrome = mat('fk_chrome', 0xd8dde6, rough=0.12, metal=1.0)
    black = mat('fk_black', 0x141416, rough=0.7)
    tire = mat('fk_tire', 0x1c1c1e, rough=0.9)
    seat = mat('fk_seat', 0x202024, rough=0.55, tex=tex_noise('fk_seat_t', 0x26262b, var=0.2, size=16, seed=3))
    amber = mat('fk_beacon', 0xffa020, rough=0.15, emit=0xff8a10, strength=3.0, alpha=0.85)
    lamp = mat('fk_lamp', 0xfff4d0, rough=0.2, emit=0xfff0c0, strength=2.0)
    def stick_draw(px):
        px[:] = hexrgb(0xffffff); px[:3] = px[-3:] = hexrgb(0xe0102a)
        text_px(px, 'SAFETY IS', 4, 5, 1, 0x111111); text_px(px, 'OPTIONAL', 4, 14, 1, 0xe0102a)
    sticker = mat('fk_sticker', 0xffffff, rough=0.4, tex=tex_canvas('fk_sticker_t', 64, 24, stick_draw))
    P = []; A = P.append

    # ---------------- chassis: low front step, engine hood under the seat, counterweight hump at the back
    ch = side_x([(-1.18, 0.16), (1.12, 0.16), (1.2, 0.3), (1.2, 0.88), (1.0, 1.02), (0.62, 1.0), (0.48, 0.9), (-0.42, 0.9), (-0.52, 1.02)], 1.2, (0, 0, 0), yel, bev=0.05, seg=2)
    for x, r in ((0.72, 0.36), (-0.78, 0.29)):
        for sz in (-1, 1): cut(ch, cyl(r + 0.03, 0.34, (x, r - 0.01, sz * 0.5), None, axis='z', seg=24))
    A(ch)
    cwt = side_x([(-1.34, 0.22), (-0.48, 0.22), (-0.48, 1.06), (-0.62, 1.2), (-0.98, 1.3), (-1.24, 1.24), (-1.36, 1.0)], 1.36, (0, 0, 0), cw, bev=0.09, seg=3)
    for sz in (-1, 1): cut(cwt, cyl(0.32, 0.4, (-0.78, 0.28, sz * 0.6), None, axis='z', seg=24))
    A(cwt)
    A(box((0.02, 0.5, 1.1), (-1.37, 0.72, 0), haz, rot=(0, 0, 0.08)))
    A(box((0.02, 0.18, 0.5), (-1.35, 1.12, 0), sticker, rot=(0, math.pi, -0.25)))
    for x in (0.72, -0.78): A(cyl(0.34 if x > 0 else 0.27, 1.0, (x, 0.35 if x > 0 else 0.28, 0), black, axis='z', seg=20))  # wheel wells
    # ---------------- seat, dash, steering wheel, levers
    A(box((0.46, 0.12, 0.5), (-0.18, 0.98, 0), seat, bev=0.04))
    A(box((0.1, 0.5, 0.48), (-0.42, 1.28, 0), seat, bev=0.04, rot=(0, 0, 0.18)))
    A(box((0.3, 0.16, 0.9), (0.86, 1.08, 0), yel, bev=0.04))
    A(cyl(0.03, 0.42, (0.68, 1.22, 0), steel, axis='y', rot=(0, 0, 0.5)))
    sw = lathe([(0.15, -0.015), (0.17, 0), (0.15, 0.015)], (0.58, 1.42, 0), black, seg=20, axis='y')
    sw.rotation_euler = Euler((0, math.radians(-30), 0)); A(sw)
    for k in range(3): A(cyl(0.012, 0.22, (0.98, 1.24, -0.12 + k * 0.08), black, axis='y', rot=(0, 0, -0.3)))
    for k in range(3): A(ball(0.025, (0.95, 1.35, -0.12 + k * 0.08), mat('fk_knob%d' % k, (0xff2a2a, 0x2a8aff, 0xffe14d)[k], rough=0.2), seg=10, rings=6))
    # ---------------- overhead guard: four posts, roof frame + slats, beacon, work lights
    for sz in (-1, 1):
        A(tube([(0.98, 1.0, sz * 0.52), (0.86, 2.3, sz * 0.54)], 0.04, steel, seg=8))
        A(tube([(-0.95, 1.2, sz * 0.54), (-0.95, 2.3, sz * 0.54)], 0.045, steel, seg=8))
        A(box((1.96, 0.07, 0.08), (-0.04, 2.33, sz * 0.54), steel, bev=0.015))
        A(box((0.12, 0.1, 0.12), (0.88, 2.18, sz * 0.62), steel, bev=0.02))
        A(box((0.03, 0.08, 0.1), (0.95, 2.18, sz * 0.62), lamp, bev=0.01))
    for k in range(7): A(box((0.05, 0.04, 1.08), (-0.86 + k * 0.29, 2.36, 0), steel))
    A(cyl(0.06, 0.06, (-0.8, 2.42, 0.36), black, axis='y', seg=12))
    A(lathe([(0.065, 0), (0.065, 0.09), (0.04, 0.14), (0, 0.15)], (-0.8, 2.45, 0.36), amber, seg=14, axis='y'))
    # ---------------- mast: two channels, cross ties, lift cylinder, chains; carriage + backrest; forks
    for sz in (-1, 1):
        A(box((0.1, 2.9, 0.08), (1.3, 1.6, sz * 0.42), steel, bev=0.01))
        A(box((0.06, 2.8, 0.05), (1.34, 1.55, sz * 0.35), steel, bev=0.008))
        A(box((0.03, 2.4, 0.03), (1.38, 1.5, sz * 0.18), black))  # chain
    for y in (0.34, 1.7, 2.98): A(box((0.1, 0.1, 0.92), (1.3, y, 0), steel, bev=0.015))
    A(cyl(0.05, 1.9, (1.24, 1.1, 0), steel, axis='y', seg=14))
    A(cyl(0.025, 0.9, (1.24, 2.4, 0), chrome, axis='y', seg=12))
    A(box((0.06, 0.6, 1.1), (1.42, 0.56, 0), steel, bev=0.02))
    for k in range(7): A(box((0.03, 0.6, 0.03), (1.44, 1.15, -0.45 + k * 0.15), steel))
    A(box((0.04, 0.04, 1.1), (1.44, 1.45, 0), steel))
    for sz in (-1, 1):
        A(box((0.05, 0.85, 0.12), (1.47, 0.48, sz * 0.3), steel, bev=0.01))
        A(box((1.16, 0.06, 0.12), (2.03, 0.08, sz * 0.3), steel, bev=0.01))
    for x, r, w in ((0.72, 0.33, 0.24), (-0.78, 0.26, 0.2)):
        for sz in (-1, 1): P.extend(wheel(r, w, (x, r, sz * 0.66), tire, mat('fk_rim', 0xe8e8e8, rough=0.35, metal=0.3), spokes=6))
    for p in P: uv_box(p, 0.25)
    fk = join(P, 'forklift')
    return finish('p_forklift', [fk], {'kind': 'prop', 'id': 'forklift'})


main(build, 'p_forklift')
