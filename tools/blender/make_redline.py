# Redline: a PPS-43-pattern stamped carbine (vented barrel jacket with a slot compensator, tall hot-rod sights, curved
# 35-round mag, folding skeleton stock pulled out), real millimetres x1.18 so the grip sits under the game's hand.
# The Redline's gimmick stays: a tachometer bolted to the left side whose needle climbs as your HP drops (node
# 'needle'), and the barrel inside the jacket glows red-hot through the vents (material 'redline_vents').
# Made fun: hot-rod bits: an 8-ball shift knob for a cocking handle, a racing stripe, a red tape cheek wrap.
# run: blender -b --python tools/blender/make_redline.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.18 / 1000
BORE_Y, MUZ_Z = 0.01, -0.47
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SIGHT_H = 54  # a tall hot-rod sight line: Lyman-style aperture on the receiver, a tower up front
DIAL = (-W(27), Y(15), Z(356))  # tachometer centre (left side of the receiver, over the magwell)


def tach_face(px):
    h, w = px.shape[:2]; c = w / 2
    px_disc(px, c, c, c - 0.5, 0x0d0d10)
    px_disc(px, c, c, c - 6, 0xe8281e, r_in=c - 11, a0=1.2, a1=2.3)  # the red zone (same angles as the game's needle)
    for i in range(11):
        th = -2.3 + 4.6 * i / 10
        r0, r1 = c - 4, c - (10 if i % 2 == 0 else 7)
        col = 0xff6a5a if th > 1.15 else 0xf2f2f2
        px_line(px, c + math.sin(th) * r0, c - math.cos(th) * r0, c + math.sin(th) * r1, c - math.cos(th) * r1, col, 2.2 if i % 2 == 0 else 1.2)
    for i, n in enumerate('02468'):
        th = -2.3 + 4.6 * (i * 2) / 10
        rx, ry = c + math.sin(th) * (c - 17) - 2, c - math.cos(th) * (c - 17) - 3
        text_px(px, n, int(rx), int(ry), 1, 0xff6a5a if th > 1.15 else 0xf2f2f2)
    text_px(px, 'RPM', int(c - 8), int(c + 12), 1, 0xf2f2f2)


def build():
    steel = mat('rl_steel', 0x23252b, rough=0.4, metal=0.6, tex=tex_noise('rl_steel_t', 0x26282e, var=0.1, size=16, seed=71))
    dark = mat('rl_dark', 0x121316, rough=0.5, metal=0.45)
    red = mat('rl_red', 0xe0202a, rough=0.25, clearcoat=0.8)
    hot = mat('redline_vents', 0x401010, rough=0.4, emit=0xff2a10, strength=0.6)  # the game drives this colour from your HP
    wood = mat('rl_grip', 0x4a2a14, rough=0.45, tex=tex_wood('rl_grip_t', 0x5a3218, 0x2e160a, size=32, seed=72, rings=4))
    chrome = mat('rl_chrome', 0xd8dde6, rough=0.12, metal=1.0)
    tape = mat('rl_tape', 0xd81e28, rough=0.6, tex=tex_stripes('rl_tape_t', 0xd81e28, 0x9a1018, size=16, width=3, diag=True))
    black = mat('rl_black', 0x050505, rough=0.15, clearcoat=1.0)
    white = mat('rl_white', 0xf4f4f4, rough=0.2)
    face = mat('rl_tach', 0xffffff, rough=0.3, tex=tex_canvas('rl_tach_t', 64, 64, tach_face))
    needle_m = mat('rl_needle', 0xff2a2a, rough=0.3, emit=0xff2a2a, strength=2.5)
    dot = mat('rl_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    parts, needle = [], []
    A = parts.append

    # ---------------- barrel jacket: a hollow stamped shroud with big side vents, top vents and a slot compensator
    jk = side(poly([(0, -17), (282, -17), (282, 21), (8, 21), (0, 14)]), W(34), (0, 0, 0), steel, bev=W(2))
    cut(jk, side(poly([(4, -14), (290, -14), (290, 18), (4, 18)]), W(28), (0, 0, 0), None))  # hollow it out
    for k in range(6):  # side vents, right through both walls
        cut(jk, box((W(60), W(13), W(26)), (0, Y(3), Z(48 + k * 37)), None, bev=W(4)))
    for k in range(5):  # top vents
        cut(jk, box((W(14), W(30), W(18)), (0, Y(21), Z(66 + k * 37)), None, bev=W(3)))
    cut(jk, box((W(12), W(30), W(16)), (0, Y(21), Z(14)), None))  # compensator slot (gas goes up, the muzzle stays down)
    cut(jk, cyl(W(6), W(20), (0, Y(0), Z(2)), None, axis='z', seg=12))  # the bullet's way out of the front plate
    A(jk)
    A(lathe([(W(8), Z(22)), (W(8), Z(300))], (0, BORE_Y, 0), hot, seg=14))  # the barrel: glows red-hot through the vents
    A(lathe([(0, Z(22)), (W(4), Z(22)), (W(4), Z(26))], (0, BORE_Y, 0), black, seg=10))
    A(box((W(6), W(1.5), W(250)), (0, Y(21.6), Z(150)), red))  # racing stripe
    # front sight: a tall tower on the jacket front with protective ears, the post's glowing dot on the sight line
    A(side(poly([(18, 21), (48, 21), (44, 34), (39, 42), (27, 42), (22, 34)]), W(9), (0, 0, 0), steel, bev=W(1.2)))
    for sx in (-1, 1): A(side(poly([(22, 22), (44, 22), (42, SIGHT_H + 5), (25, SIGHT_H + 5)]), W(2.6), (sx * W(7), 0, 0), steel, bev=W(0.7)))
    A(box((W(3), W(SIGHT_H - 42), W(4)), (0, Y((SIGHT_H + 42) / 2), Z(33)), dark))
    A(box((W(3.4), W(3.4), W(3.4)), (0, Y(SIGHT_H), Z(33)), dot, bev=W(0.6)))
    # ---------------- receiver, flip rear sight, ejection port, 8-ball cocking knob
    rcv = side(poly([(276, -22), (522, -22), (522, 14), (512, 24), (282, 24), (276, 18)]), W(34), (0, 0, 0), steel, bev=W(2.5))
    cut(rcv, box((W(12), W(15), W(40)), (W(17), Y(10), Z(338)), None))
    cut(rcv, box((W(12), W(5), W(110)), (W(17), Y(0), Z(392)), None))  # bolt handle slot
    A(rcv)
    A(box((W(1.5), W(13), W(36)), (W(15.5), Y(10), Z(338)), dark))
    # rear sight: a tall Lyman-style aperture on a bridge at the back of the receiver (the Thompson had one like it)
    A(box((W(24), W(6), W(36)), (0, Y(27), Z(488)), steel, bev=W(1.5)))
    for sx in (-1, 1): A(side(poly([(474, 28), (502, 28), (498, SIGHT_H + 6), (480, SIGHT_H + 6)]), W(3), (sx * W(8.5), 0, 0), steel, bev=W(0.8)))
    A(box((W(4), W(SIGHT_H - 6 - 30), W(4)), (0, Y((SIGHT_H - 6 + 30) / 2), Z(488)), dark))
    ap = cyl(W(6), W(3.5), (0, Y(SIGHT_H), Z(488)), dark, axis='z', seg=16)
    cut(ap, cyl(W(2.6), W(10), (0, Y(SIGHT_H), Z(488)), None, axis='z', seg=10))
    A(ap)
    A(cyl(W(5), W(5), (W(12.5), Y(36), Z(488)), chrome, axis='x', seg=12))  # elevation knob
    A(rod((W(16), Y(0), Z(340)), (W(34), Y(2), Z(340)), W(4), chrome, seg=8))
    A(ball(W(11), (W(44), Y(3), Z(340)), black, seg=18, rings=12))
    A(cyl(W(5.5), W(1.2), (W(54.6), Y(3), Z(340)), white, axis='x', seg=14))
    A(box((W(0.8), W(5), W(2.5)), (W(55.3), Y(3), Z(340)), black))  # the 8 (well, a slash of it)
    A(cyl(W(5), W(36), (-W(0), Y(12), Z(516)), dark, axis='x', seg=12))  # stock hinge
    # ---------------- magwell + curved 35-round mag + paddle release
    A(side(poly([(300, -22), (348, -22), (348, -52), (300, -52)]), W(32), (0, 0, 0), steel, bev=W(2)))
    A(side(poly([(350, -34), (362, -34), (364, -58), (352, -58)]), W(16), (0, 0, 0), dark, bev=W(1)))
    front = [(304, -50), (300, -100), (291, -150), (277, -200), (262, -232)]
    back = [(344, -50), (340, -100), (331, -150), (317, -200), (302, -238)]
    A(side(poly(front + back[::-1]), W(26), (0, 0, 0), dark, bev=W(2)))
    A(side(poly([(258, -228), (306, -236), (304, -248), (255, -240)]), W(30), (0, 0, 0), dark, bev=W(2.5)))
    # ---------------- trigger guard, safety, trigger, grip
    A(side(poly([(360, -22), (368, -22), (370, -50), (420, -52), (428, -30), (436, -22), (440, -26), (432, -58), (366, -60), (360, -50)]), W(12), (0, 0, 0), steel, bev=W(1.8)))
    A(box((W(10), W(8), W(8)), (0, Y(-27), Z(372)), red, bev=W(1)))  # safety catch
    A(side(poly([(392, -22), (398, -22), (402, -34), (398, -46), (392, -44), (394, -34)]), W(6), (0, 0, 0), red, bev=W(1)))
    A(side(poly([(428, -22), (472, -22), (506, -128), (502, -140), (480, -146), (468, -136), (462, -110), (450, -80)]), W(32), (0, 0, 0), wood, bev=W(6), seg=3))
    A(side(poly([(466, -22), (474, -22), (508, -130), (500, -132)]), W(18), (0, 0, 0), steel, bev=W(1.5)))  # back strap
    # ---------------- skeleton stock, pulled out: top + bottom struts, curved butt plate, red tape cheek wrap
    A(side(poly([(516, 18), (812, 10), (812, -2), (516, 6)]), W(14), (0, 0, 0), steel, bev=W(2)))
    A(side(poly([(515, -14), (811, -106), (807, -120), (511, -28)]), W(14), (0, 0, 0), steel, bev=W(2)))
    A(side(poly([(800, 14), (822, 12), (826, -20), (824, -110), (816, -124), (800, -120), (804, -60)]), W(30), (0, 0, 0), steel, bev=W(3)))
    A(side(poly([(600, 15), (720, 12), (720, -4), (600, -1)]), W(16), (0, 0, 0), tape, bev=W(2)))
    # ---------------- the tachometer, bolted to the left side, facing you
    A(cyl(W(30), W(10), DIAL, chrome, axis='x', seg=24, bev=W(1.5)))
    A(cyl(W(26), W(10.6), DIAL, dark, axis='x', seg=24))
    fc = cyl(W(25.5), W(1), (DIAL[0] - W(5.2), DIAL[1], DIAL[2]), face, axis='x', seg=24)
    A(fc)
    for dd in (-18, 18):
        A(cyl(W(3), W(6), (DIAL[0] + W(8), DIAL[1] + W(dd) * 0.7, DIAL[2] + W(dd)), chrome, axis='x', seg=8))  # bolts into the receiver
    needle.append(box((W(2), W(21), W(2.6)), (DIAL[0] - W(6.4), DIAL[1] + W(9), DIAL[2]), needle_m))
    needle.append(cyl(W(3.4), W(2.4), (DIAL[0] - W(6.4), DIAL[1], DIAL[2]), black, axis='x', seg=12))

    for p in parts + needle: uv_box(p, 0.03)
    apply_mods(fc); uv_planar(fc, (DIAL[0], DIAL[1], DIAL[2]), W(51), '-x')
    WZ = {'rl_steel': 'a', 'rl_grip': 'a', 'rl_dark': 'a', 'redline_vents': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'redline_body', WZ, default='n', rule=lambda m, c: 'b' if (m in ('rl_steel', 'rl_dark', 'rl_red') and c[2] < Z(276)) or (m == 'rl_dark' and c[1] < Y(-60)) else None)  # jacket, sights, racing stripe + mag
    nd = part(needle, 'needle_wzN', pivot=DIAL)
    meta = {'kind': 'weapon', 'id': 'redline', 'paint': ['rl_red'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SIGHT_H), 'z': Z(488)},
            'hatAt': [[0, Y(24), Z(440)], 0.1], 'needle': 'needle_wzN', 'vents': 'redline_vents'}
    return finish('w_redline', bodies + [nd], meta)


main(build, 'w_redline')
