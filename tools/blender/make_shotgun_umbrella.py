# Brolly (shotgun_umbrella): a city gent's stick umbrella that pumps, about x1.15 a real one (a 0.95 m umbrella
# reaching the shotgun's 1.15 m): a long brass ferrule as the muzzle, the canopy furled tight in eight twisted folds
# with its strap and snap, the eight rib tips poking out at the bottom, a chrome shaft, the RUNNER (the collar that
# opens it) as the pump with its stretchers folded along the shaft, an auto-open button housing as the receiver (the
# button is the trigger), and a varnished malacca crook bent round into a pistol grip whose hook is the trigger
# guard, with a leather wrist cord. Made fun: hot-pink ☺ CORP print, a tag on the cord says IT NEVER RAINS INDOORS.
# The pump node 'pump_wzB' rides back along +z with the game's pump keys, like the shotgun's forend.
# run: blender -b --python tools/blender/make_shotgun_umbrella.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corp import *

BORE_Y, MUZ_Z = 0.025, -0.74
SG = Scale(1.05, BORE_Y, MUZ_Z)
SIGHT_Y, REAR_Z, FRONT_Z = SG.Y(44), SG.Z(668), -0.7
CAN0, CAN1 = -0.648, -0.17      # canopy: top notch .. rib tips
RUN_Z = -0.12                   # the runner's middle (the pump)


def build():
    def print_px(px):  # tiny yellow smileys on magenta
        px[:] = hexrgb(0xff1fb8)
        for yy in range(0, 64, 16):
            for xx in range(0, 64, 16):
                smiley_px(px, xx + (8 if (yy // 16) % 2 else 0) % 16 + 1, yy + 3, 1, 0xffe14d)
    canopy = mat('ub_canopy', 0xff1fb8, rough=0.38, clearcoat=0.5, tex=tex_canvas('ub_canopy_t', 64, 64, print_px))
    black = plastic('ub_black', 0x15151a, rough=0.4, cc=0.5, seed=501)
    wood = mat('ub_wood', 0xb8743a, rough=0.2, clearcoat=1.0, tex=tex_wood('ub_wood_t', 0xc07c3e, 0x6a3a18, size=64, seed=502, rings=9))
    node = mat('ub_node', 0x4a2a10, rough=0.45, clearcoat=0.3)
    chrome = mat('ub_chrome', 0xdde2ea, rough=0.12, metal=1.0)
    brass = mat('ub_brass', 0xe0ad3c, rough=0.2, metal=1.0)
    rubber = mat('ub_rubber', 0x202024, rough=0.85, tex=tex_noise('ub_rub_t', 0x222226, var=0.14, size=16, seed=503))
    leather = mat('ub_leather', 0x3a2012, rough=0.6, tex=tex_noise('ub_leather_t', 0x3e2214, var=0.14, size=16, seed=504))
    tipm = mat('ub_ribtip', 0xffe14d, rough=0.25, clearcoat=0.8)
    dot = mat('ub_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    tag = mat('ub_tag', 0xffffff, rough=0.4, tex=label_tex('ub_tag_t', 50, 30, [('IT NEVER', None), ('RAINS', None), ('INDOORS', None)], bg=0xffe14d, smile=False))
    parts, pump, decals = [], [], []
    A = parts.append

    # ---------------- ferrule (the muzzle), the top cup, the front sight on a little collar
    A(lathe([(0.0, -0.7405), (0.0045, -0.74), (0.0062, -0.735), (0.0075, -0.7), (0.0085, -0.672), (0.0105, -0.666), (0.0105, -0.656), (0.0085, -0.652)], (0, BORE_Y, 0), brass, seg=16))
    A(cyl(0.0035, 0.002, (0, BORE_Y, -0.7405), black, axis='z', seg=10))  # the bore
    A(lathe([(0.0085, -0.656), (0.0145, -0.648), (0.0165, -0.636), (0.0125, -0.63)], (0, BORE_Y, 0), black, seg=16))
    A(lathe([(0.009, FRONT_Z - 0.006), (0.0098, FRONT_Z - 0.004), (0.0098, FRONT_Z + 0.004), (0.009, FRONT_Z + 0.006)], (0, BORE_Y, 0), chrome, seg=14, cap=False))
    A(side([(FRONT_Z - 0.006, BORE_Y + 0.006), (FRONT_Z + 0.006, BORE_Y + 0.006), (FRONT_Z + 0.002, SIGHT_Y - 0.004), (FRONT_Z - 0.002, SIGHT_Y - 0.004)], 0.003, (0, 0, 0), chrome, bev=0.0006))
    A(ball(0.0042, (0, SIGHT_Y - 0.001, FRONT_Z), dot, seg=10, rings=6))

    # ---------------- the furled canopy: eight folds, twisted a quarter turn, fat toward the bottom
    N, K = 40, 32
    def R(t):  # radius along the canopy (t = 0 top .. 1 bottom)
        return 0.012 + 0.024 * math.sin(min(1, t * 1.25) * math.pi / 2) ** 1.4 - 0.012 * max(0, (t - 0.85) / 0.15) ** 2
    cs = [(0, BORE_Y, CAN0 + (CAN1 - CAN0) * i / (N - 1)) for i in range(N)]
    def ring(i, t):
        out = []
        for k in range(K):
            a = 2 * math.pi * k / K + t * 1.6
            r = R(t) * (1 + 0.13 * math.cos(8 * (a - t * 1.6) ) ** 3)
            out.append((math.sin(a) * r, math.cos(a) * r))
        return out
    cn = loft(cs, ring, canopy, name='canopy', smooth_angle=70)
    A(cn)
    # the strap round it + its snap button (on the right, where you see it)
    sz = -0.36
    A(lathe([(R((sz - CAN0) / (CAN1 - CAN0)) * 1.13, sz - 0.011), (R((sz - CAN0) / (CAN1 - CAN0)) * 1.13, sz + 0.011)], (0, BORE_Y, 0), black, seg=24, cap=False))
    rr = R((sz - CAN0) / (CAN1 - CAN0)) * 1.13
    A(box((0.004, 0.022, 0.05), (rr, BORE_Y, sz + 0.012), black, bev=0.003))
    A(cyl(0.0075, 0.005, (rr + 0.003, BORE_Y, sz + 0.022), chrome, axis='x', seg=14))
    # rib tips poking out round the bottom of the canopy
    for k in range(8):
        a = 2 * math.pi * k / 8 + 1.6 + 0.2
        r = R(1) * 1.05
        A(rod((math.sin(a) * r * 0.9, BORE_Y + math.cos(a) * r * 0.9, CAN1 - 0.012), (math.sin(a) * r * 0.75, BORE_Y + math.cos(a) * r * 0.75, CAN1 + 0.012), 0.0034, tipm, seg=8, r1=0.0024))

    # ---------------- the shaft, the runner (pump) with its stretchers + the top spring catch
    A(cyl(0.0058, 0.2, (0, BORE_Y, -0.08), chrome, axis='z', seg=12))
    A(box((0.003, 0.004, 0.012), (0, BORE_Y + 0.007, -0.03), brass, bev=0.001))  # the spring catch
    rn = lathe([(0.0068, RUN_Z - 0.06), (0.012, RUN_Z - 0.058), (0.0175, RUN_Z - 0.05)] + sum([[(0.019, RUN_Z - 0.044 + k * 0.012), (0.0172, RUN_Z - 0.04 + k * 0.012), (0.019, RUN_Z - 0.036 + k * 0.012)] for k in range(7)], []) +
               [(0.0175, RUN_Z + 0.044), (0.0125, RUN_Z + 0.05), (0.0068, RUN_Z + 0.052)], (0, BORE_Y, 0), rubber, seg=18)
    pump.append(rn)
    pump.append(lathe([(0.0185, RUN_Z - 0.06), (0.0185, RUN_Z - 0.052)], (0, BORE_Y, 0), chrome, seg=18, cap=False))
    for k in range(8):  # stretchers: from the runner forward, folded along the shaft into the canopy
        a = 2 * math.pi * k / 8 + 0.2
        pump.append(rod((math.sin(a) * 0.012, BORE_Y + math.cos(a) * 0.012, RUN_Z - 0.055), (math.sin(a) * 0.009, BORE_Y + math.cos(a) * 0.009, CAN1 - 0.04), 0.0016, chrome, seg=5))

    # ---------------- auto-open housing (the receiver), its button (the trigger), the rear sight on top
    hb = side([(-0.03, BORE_Y - 0.014), (-0.03, BORE_Y + 0.014), (-0.02, BORE_Y + 0.02), (0.05, BORE_Y + 0.02), (0.07, BORE_Y + 0.012), (0.07, BORE_Y - 0.024), (0.0, -0.016), (-0.022, -0.012)], 0.032, (0, 0, 0), black, bev=0.006, seg=2)
    A(hb)
    A(lathe([(0.0062, -0.04), (0.0105, -0.034), (0.0105, -0.026)], (0, BORE_Y, 0), chrome, seg=14))
    A(side([(-0.002, -0.012), (0.012, -0.012), (0.016, -0.028), (0.01, -0.044), (0.0, -0.04), (0.004, -0.028)], 0.012, (0, 0, 0), chrome, bev=0.002))  # the button you squeeze
    A(box((0.026, 0.006, 0.05), (0, BORE_Y + 0.023, REAR_Z + 0.006), black, bev=0.002))
    for sx in (-1, 1): A(side([(REAR_Z - 0.016, BORE_Y + 0.024), (REAR_Z + 0.02, BORE_Y + 0.024), (REAR_Z + 0.014, SIGHT_Y + 0.011), (REAR_Z - 0.01, SIGHT_Y + 0.011)], 0.003, (sx * 0.0105, 0, 0), black, bev=0.0008))
    A(box((0.003, SIGHT_Y - BORE_Y - 0.03, 0.004), (0, (SIGHT_Y + BORE_Y + 0.02) / 2 - 0.004, REAR_Z), chrome))
    gr = cyl(0.0079, 0.004, (0, SIGHT_Y, REAR_Z), chrome, axis='z', seg=18)
    cut(gr, cyl(0.0052, 0.02, (0, SIGHT_Y, REAR_Z), None, axis='z', seg=14))
    A(fixmats(gr))

    # ---------------- the crook: malacca cane out of the housing, bent down into a grip, its hook = the trigger guard
    hook = [(0.0, BORE_Y, 0.06), (0.0, BORE_Y + 0.001, 0.09), (0.0, BORE_Y - 0.004, 0.118), (0.0, BORE_Y - 0.022, 0.14), (0.0, -0.035, 0.15), (0.0, -0.075, 0.148),
            (0.0, -0.115, 0.14), (0.0, -0.15, 0.124), (0.0, -0.172, 0.096), (0.0, -0.178, 0.062), (0.0, -0.17, 0.028), (0.0, -0.15, 0.0), (0.0, -0.12, -0.018),
            (0.0, -0.088, -0.026), (0.0, -0.06, -0.026), (0.0, -0.036, -0.02)]
    rad = [0.016, 0.0165, 0.017, 0.0175, 0.0175, 0.0175, 0.017, 0.0165, 0.016, 0.0155, 0.015, 0.014, 0.013, 0.012, 0.011, 0.0095]
    A(sweep(hook, rad, wood, seg=14))
    A(ball(0.0098, (0.0, -0.034, -0.019), wood, seg=12, rings=8))
    for k in (2, 6, 10):  # the cane's growth nodes
        p, a, b = Vector(hook[k]), Vector(hook[k - 1]), Vector(hook[k + 1])
        A(sweep([tuple(p + (a - p) * 0.2), tuple(p), tuple(p + (b - p) * 0.2)], [rad[k] * 1.0, rad[k] * 1.08, rad[k] * 1.0], node, seg=14, cap=False))
    A(lathe([(0.0172, 0.052), (0.0172, 0.066)], (0, BORE_Y, 0), brass, seg=16, cap=False))  # the collar
    # wrist cord from the collar + the tag
    cord = [(0.018, BORE_Y - 0.005, 0.06), (0.024, BORE_Y - 0.03, 0.066), (0.026, -0.03, 0.074), (0.024, -0.07, 0.08), (0.02, -0.08, 0.07), (0.019, -0.06, 0.058), (0.018, BORE_Y - 0.01, 0.056)]
    A(tube(cord, 0.0022, leather, seg=6))
    A(tube([(0.024, -0.075, 0.078), (0.027, -0.09, 0.08)], 0.0012, brass, seg=4))
    tg = box((0.001, 0.03, 0.05), (0.028, -0.108, 0.082), tag, rot=(0.12, 0, 0)); A(tg); decals.append((tg, (0.05, 0.03), 'x'))

    for p in parts + pump: fixmats(p); uv_box(p, 0.04)
    uv_tube(cn, 0, BORE_Y, CAN0, CAN1, 6.0, 2.0)  # the print repeats along + round
    for o, sz_, ax in decals: decal(o, sz_, ax)
    WZ = {'ub_canopy': 'b', 'ub_brass': 'b', 'ub_ribtip': 'b', 'ub_chrome': 'b', 'ub_wood': 'a', 'ub_node': 'a', 'ub_black': 'a', 'ub_leather': 'a'}
    bodies = zone_join(parts, 'brolly', WZ, default='n', rule=lambda m, c: 'b' if m == 'ub_black' and c[2] < -0.2 else None)
    pnode = part(pump, 'pump_wzB', pivot=(0, BORE_Y, RUN_Z))
    meta = {'kind': 'weapon', 'id': 'shotgun', 'skin': 'shotgun_umbrella', 'paint': ['ub_canopy'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': SIGHT_Y, 'z': REAR_Z},
            'hatAt': [[0, BORE_Y + 0.036, -0.4], 0.11], 'pump': {'node': 'pump_wzB', 'travel': 0.1}}
    return finish('w_shotgun_umbrella', bodies + [pnode], meta)


main(build, 'w_shotgun_umbrella')
