# Minigun: an M134-pattern six-barrel 7.62 (559 mm barrels in a 90 mm circle, front + mid barrel clamps, rotor
# housing, drive motor, delinking feeder + chute), real millimetres x1.0, set up to be carried: a top handle, a front
# grip and a rear pistol grip. The barrels, clamps and rotor face are one node ('barrels') that the game spins.
# Made fun: a red-and-white pinwheel on the front clamp so you can SEE it spin up, a hazard ring, an open ammo can of
# brass, a battery meter on the motor and a sticker with good advice.
# run: blender -b --python tools/blender/make_minigun.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.0 / 1000
BORE_Y, MUZ_Z = 0.0, -0.75
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]


def pinwheel(px):
    h, w = px.shape[:2]; c = w / 2
    yy, xx = np.mgrid[0:h, 0:w]
    dx, dy = xx + 0.5 - c, yy + 0.5 - c
    ang = np.arctan2(dy, dx) + np.hypot(dx, dy) / c * 2.2  # a swirl: arms bend as they go out
    k = (np.floor(ang / (math.pi / 3)) % 2).astype(int)
    px[:] = np.where(k[:, :, None] == 0, hexrgb(0xff2a3a), hexrgb(0xf4f4f4))
    px_disc(px, c, c, c * 0.22, 0x1a1a1a)


def build():
    steel = mat('mg_barrel', 0xb8bcc4, rough=0.28, metal=0.9)
    gun = mat('mg_housing', 0x3a3e46, rough=0.38, metal=0.6, tex=tex_noise('mg_housing_t', 0x3c4048, var=0.08, size=16, seed=81))
    dark = mat('mg_dark', 0x16171a, rough=0.5, metal=0.4)
    black = mat('mg_black', 0x050505, rough=0.3)
    rubber = mat('mg_rubber', 0x1c1c1e, rough=0.85, tex=tex_noise('mg_rubber_t', 0x1e1e20, var=0.25, size=16, seed=82))
    haz = mat('mg_hazard', 0xffd21a, rough=0.4, tex=tex_stripes('mg_haz_t', 0xffd21a, 0x141414, size=32, width=4))
    pin = mat('mg_pinwheel', 0xffffff, rough=0.3, tex=tex_canvas('mg_pin_t', 64, 64, pinwheel))
    olive = mat('mg_can', 0x5a6634, rough=0.55, tex=tex_noise('mg_can_t', 0x5a6634, var=0.12, size=16, speck=0x3a4220, speck_p=0.05, seed=83))
    brass = mat('mg_brass', 0xe0ad3c, rough=0.25, metal=1.0)
    copper = mat('mg_copper', 0xc8683a, rough=0.3, metal=1.0)
    red = mat('mg_red', 0xe0202a, rough=0.3, clearcoat=0.6)
    led = mat('mg_led', 0x39ff14, rough=0.3, emit=0x39ff14, strength=4.0)
    def warn(px):
        px[:] = hexrgb(0xffe14d); px[:2] = px[-2:] = hexrgb(0x111111)
        text_px(px, 'DO NOT LICK', 3, 4, 1, 0x111111); text_px(px, 'WHILE', 3, 13, 1, 0xe0102a); text_px(px, 'SPINNING', 3, 22, 1, 0xe0102a)
    sticker = mat('mg_sticker', 0xffffff, rough=0.4, tex=tex_canvas('mg_sticker_t', 72, 32, warn))
    def stencil(px):
        px[:] = hexrgb(0x5a6634); text_px(px, '7.62 JANK', 3, 4, 1, 0xf0e6c8); text_px(px, '4000 RDS', 3, 13, 1, 0xf0e6c8)
    can_lbl = mat('mg_stencil', 0xffffff, rough=0.6, tex=tex_canvas('mg_stencil_t', 60, 22, stencil))
    parts, spin = [], []
    A = parts.append

    # ---------------- the spinning cluster: six barrels, two clamps, the rotor face
    for k in range(6):
        a = math.pi / 6 + k * math.pi / 3
        x, y = math.cos(a) * W(45), math.sin(a) * W(45)
        spin.append(lathe([(W(10.5), Z(0)), (W(10.5), Z(6)), (W(9.5), Z(8)), (W(9.5), Z(566))], (x, y, 0), steel, seg=12))
        spin.append(lathe([(0, Z(0.5)), (W(4.5), Z(0.5)), (W(4.5), Z(8))], (x, y, 0), black, seg=8))
    spin.append(cyl(W(60), W(24), (0, 0, Z(40)), gun, axis='z', seg=6, bev=W(3), rot=(0, 0, math.pi / 6)))
    fc = cyl(W(52), W(1.5), (0, 0, Z(27.4)), pin, axis='z', seg=28)  # pinwheel on the front of the clamp
    bc = cyl(W(52), W(1.5), (0, 0, Z(52.6)), pin, axis='z', seg=28)  # and on its back, where you look at it
    spin += [fc, bc]
    spin.append(cyl(W(57), W(24), (0, 0, Z(268)), gun, axis='z', seg=20, bev=W(3)))
    for k in range(6):
        a = k * math.pi / 3
        spin.append(cyl(W(4), W(30), (math.cos(a) * W(28), math.sin(a) * W(28), Z(268)), dark, axis='z', seg=6))
    spin.append(cyl(W(64), W(10), (0, 0, Z(560)), dark, axis='z', seg=24))
    spin.append(cyl(W(14), W(500), (0, 0, Z(300)), dark, axis='z', seg=10))  # centre spindle

    # ---------------- housing, hazard ring, rear cap, drive motor with a battery meter
    hs = lathe([(W(70), Z(562)), (W(76), Z(566)), (W(76), Z(584)), (W(72), Z(588)), (W(72), Z(766)), (W(66), Z(772)), (W(66), Z(800)), (W(40), Z(808)), (0, Z(810))], (0, 0, 0), gun, seg=28)
    for sx in (-1, 1):
        for k in range(4): cut(hs, box((W(30), W(12), W(28)), (sx * W(72), Y(-6 + k * 0), Z(615 + k * 38)), None, bev=W(3)))  # cooling slots
    A(hs)
    A(lathe([(W(76.6), Z(567)), (W(76.6), Z(583))], (0, 0, 0), haz, seg=28))
    mx, my = -W(64), Y(44)
    A(lathe([(W(30), Z(598)), (W(30), Z(756)), (W(24), Z(764)), (W(24), Z(772))], (mx, my, 0), dark, seg=18))
    for k in range(9): A(lathe([(W(32.5), Z(612 + k * 15)), (W(32.5), Z(618 + k * 15))], (mx, my, 0), gun, seg=18))
    for k in range(4): A(box((W(6), W(4), W(1.5)), (mx - W(10) + k * W(7), my, Z(772.5)), led if k < 3 else dark))
    A(sweep([(mx, my - W(20), Z(770)), (mx + W(10), Y(-20), Z(800)), (-W(20), Y(-62), Z(806))], W(4), black, seg=6))
    # ---------------- carry handle, front grip, rear pistol grip + trigger
    A(tube([(0, Y(68), Z(612)), (0, Y(122), Z(634)), (0, Y(122), Z(748)), (0, Y(68), Z(770))], W(10), dark, seg=10))
    A(cyl(W(14), W(92), (0, Y(122), Z(691)), rubber, axis='z', seg=14, bev=W(3)))
    A(side(poly([(590, -66), (628, -66), (628, -80), (590, -80)]), W(36), (0, 0, 0), dark, bev=W(2)))
    A(side(poly([(594, -78), (624, -78), (630, -150), (624, -168), (598, -168), (592, -150), (596, -138), (590, -124), (594, -112), (588, -98)]), W(34), (0, 0, 0), rubber, bev=W(6), seg=3))
    A(side(poly([(728, -56), (812, -56), (812, -72), (728, -72)]), W(42), (0, 0, 0), dark, bev=W(2.5)))
    A(side(poly([(735, -70), (745, -70), (748, -90), (774, -92), (776, -72), (782, -72), (780, -100), (740, -102), (735, -90)]), W(12), (0, 0, 0), dark, bev=W(1.8)))
    A(side(poly([(752, -70), (762, -70), (766, -80), (762, -90), (754, -88), (756, -80)]), W(8), (0, 0, 0), red, bev=W(1.5)))
    A(side(poly([(764, -70), (804, -70), (830, -160), (824, -172), (802, -176), (794, -166), (788, -140), (792, -128), (782, -112), (784, -98), (774, -86)]), W(32), (0, 0, 0), rubber, bev=W(6), seg=3))
    # ---------------- feeder + chute + an open can of linked brass (right side)
    A(side(poly([(612, -28), (722, -28), (722, 34), (630, 34), (612, 16)]), W(38), (W(80), 0, 0), dark, bev=W(3)))
    ch = []
    for k in range(9):
        t = k / 8
        ch.append((W(96) + W(34) * t, Y(-12) - W(22) * math.sin(t * math.pi * 0.8), Z(700) + W(105) * t))
    A(sweep(ch, W(26), gun, seg=8, squash=(0.45, 1.0)))
    for k in range(1, 8):
        p0, p1 = ch[k - 1], ch[k]
        mid = tuple((p0[i] + p1[i]) / 2 for i in range(3))
        A(sweep([tuple(mid[i] + (p0[i] - mid[i]) * 0.12 for i in range(3)), tuple(mid[i] + (p1[i] - mid[i]) * 0.12 for i in range(3))], W(27.5), dark, seg=8, squash=(0.47, 1.02)))  # chute ribs
    can_x, can_y, can_z = W(135), Y(-70), Z(865)
    can = box((W(100), W(120), W(150)), (can_x, can_y, can_z), olive, bev=W(4))
    cut(can, box((W(88), W(120), W(138)), (can_x, can_y + W(10), can_z), None))  # open top
    A(can)
    A(box((W(1), W(22), W(60)), (can_x - W(50.6), can_y + W(10), can_z), can_lbl, rot=(0, math.pi, 0)))
    A(tube([(can_x, can_y + W(60), can_z - W(40)), (can_x, can_y + W(82), can_z - W(30)), (can_x, can_y + W(82), can_z + W(30)), (can_x, can_y + W(60), can_z + W(40))], W(4), dark, seg=6))
    for row in range(2):
        for k in range(7):
            z = can_z - W(56) + k * W(18.5)
            y = can_y + W(48) - row * W(12)
            xo = can_x + (W(6) if row else -W(6))
            A(cyl(W(6), W(50), (xo - W(8), y, z), brass, axis='x', seg=10))
            A(cyl(W(5.6), W(18), (xo + W(25), y, z), copper, axis='x', seg=10, r2=W(1.8)))
            A(box((W(10), W(4), W(14)), (xo - W(28), y + W(5), z), dark))  # links
    # ---------------- sticker on the side you see
    A(box((W(1), W(32), W(72)), (-W(72.6), Y(-28), Z(690)), sticker, rot=(0, math.pi, 0)))

    for p in parts + spin: uv_box(p, 0.03)
    for p in (fc, bc): apply_mods(p); uv_planar(p, (0, 0, 0), W(104), 'z')
    for p in parts:
        if p.data.materials and p.data.materials[0] in (sticker, can_lbl):
            apply_mods(p); c = p.matrix_world.translation
            uv_planar(p, (c.x, c.z, -c.y), (W(72), W(32)) if p.data.materials[0] is sticker else (W(60), W(22)), '-x')
    body = join(parts, 'minigun_body')
    barrels = part(spin, 'barrels', pivot=(0, 0, Z(300)))
    meta = {'kind': 'weapon', 'id': 'minigun', 'paint': ['mg_housing'], 'muzzle': [0, BORE_Y, MUZ_Z], 'barrels': 'barrels',
            'hatAt': [[0, Y(136), Z(690)], 0.14]}
    return finish('w_minigun', [body, barrels], meta)


main(build, 'w_minigun')
