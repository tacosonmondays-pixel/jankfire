# Shotgun: an 870-pattern 12 gauge pump (18.5in barrel, tube mag under it, ribbed forend on twin action bars,
# milled receiver, walnut stock with a thick recoil pad), real millimetres scaled x1.05 to the game's shotgun.
# Made fun: a side saddle of glossy red shells, a vent rib with a big brass bead, crusty walnut.
# The forend is its own node ('pump') so the game can rack it.
# run: blender -b --python tools/blender/make_shotgun.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.05 / 1000
BORE_Y, MUZ_Z = 0.025, -0.74
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]


def build():
    blue = mat('sg_blued', 0x23262e, rough=0.3, metal=0.75)
    dark = mat('sg_dark', 0x121318, rough=0.5, metal=0.5)
    walnut = mat('sg_walnut', 0x8a5a2b, rough=0.35, tex=tex_wood('sg_walnut_t', 0x7a4520, 0x3a1a08, size=64, seed=11))
    fore = mat('sg_forend', 0x7a4a22, rough=0.4, tex=tex_wood('sg_forend_t', 0x7a4520, 0x3a1a08, size=32, seed=12, rings=4))
    rubber = mat('sg_rubber', 0x1a1a1c, rough=0.9)
    brass = mat('sg_brass', 0xe8b445, rough=0.2, metal=1.0)
    hull = mat('sg_hull', 0xe0202e, rough=0.18, clearcoat=1.0)
    nylon = mat('sg_saddle', 0x1f2226, rough=0.7, tex=tex_noise('sg_saddle_t', 0x24272c, var=0.2, size=16, seed=2))
    strap = mat('sg_strap', 0xff4fd8, rough=0.6, tex=tex_stripes('sg_strap_t', 0xff4fd8, 0xc0208e, size=16, width=2, diag=False))
    bead = mat('sg_bead', 0xffe14d, rough=0.2, metal=0.3, emit=0xffd040, strength=1.6)
    black = mat('sg_black', 0x050505, rough=0.3)
    parts, pump = [], []
    A = parts.append

    # ---------------- barrel, muzzle, vent rib + bead, mag tube, cap, barrel clamp ring
    A(lathe([(W(9.5), Z(0)), (W(11.5), Z(0)), (W(11.5), Z(3)), (W(11), Z(6)), (W(11), Z(470)), (W(13.5), Z(478)), (W(13.5), Z(500))], (0, BORE_Y, 0), blue, seg=20))
    A(lathe([(0, Z(1)), (W(9.5), Z(1)), (W(9.5), Z(10))], (0, BORE_Y, 0), black, seg=14))
    A(box((W(7), W(2.5), W(440)), (0, Y(14.5), Z(250)), blue, bev=W(0.6)))  # rib top
    for i in range(22):  # rib posts
        A(box((W(5), W(4), W(5)), (0, Y(11.5), Z(40 + i * 20)), blue))
    A(ball(W(3.6), (0, Y(19), Z(14)), bead, seg=12, rings=8))
    A(lathe([(W(10.5), Z(62)), (W(12.5), Z(66)), (W(12.5), Z(470))], (0, Y(-26), 0), blue, seg=18))  # mag tube
    A(lathe([(W(7), Z(36)), (W(12), Z(40)), (W(13), Z(48)), (W(13), Z(64)), (W(11), Z(68))], (0, Y(-26), 0), dark, seg=12))  # knurled mag cap
    A(side(poly([(70, 12), (96, 12), (96, -40), (70, -40)]), W(20), (0, 0, 0), blue, bev=W(3)))  # barrel ring / clamp
    A(tube([(0, Y(-38), Z(50)), (0, Y(-50), Z(54)), (0, Y(-50), Z(64)), (0, Y(-38), Z(66))], W(2.2), dark, seg=6))  # front swivel

    # ---------------- the pump: ribbed forend riding on the mag tube + twin action bars back into the receiver
    pd0, pd1 = 230, 420
    fe = lathe([(W(19), Z(pd0)), (W(23), Z(pd0 + 8))] + sum([[(W(23), Z(pd0 + 14 + k * 16)), (W(20.5), Z(pd0 + 18 + k * 16)), (W(20.5), Z(pd0 + 24 + k * 16)), (W(23), Z(pd0 + 28 + k * 16))] for k in range(10)], []) +
               [(W(23), Z(pd1 - 8)), (W(20), Z(pd1))], (0, Y(-24), 0), fore, seg=16)
    fe.scale = (1.0, 1.0, 1.12)  # a bit taller than wide (blender z = up)
    pump.append(fe)
    for sx in (-1, 1):
        pump.append(box((W(3), W(6), W(260)), (sx * W(13.5), Y(-16), Z(pd1 + 100)), dark, bev=W(0.5)))
    pump.append(lathe([(W(13), Z(pd1 - 2)), (W(13), Z(pd1 + 6))], (0, Y(-26), 0), dark, seg=14))

    # ---------------- receiver: milled block, ejection port, loading port, side saddle with six red shells
    rcv = side(poly([(470, 12), (700, 12), (708, 6), (708, -38), (612, -40), (600, -44), (476, -44), (470, -30)]), W(33), (0, 0, 0), blue, bev=W(2.5))
    cut(rcv, box((W(12), W(20), W(80)), (W(16.5), Y(-4), Z(548)), None))  # ejection port, right
    cut(rcv, box((W(22), W(14), W(95)), (0, Y(-46), Z(545)), None))  # loading port, underneath
    A(rcv)
    A(box((W(1.5), W(16), W(74)), (W(15.6), Y(-4), Z(548)), dark))  # bolt face in the port
    A(box((W(18), W(1.5), W(88)), (0, Y(-39), Z(545)), dark))  # shell lifter
    A(box((W(31), W(5), W(222)), (0, Y(12.5), Z(586)), blue, bev=W(2.4)))  # rounded top, level with the rib
    sx0 = -W(22)
    A(side(poly([(488, 10), (622, 10), (622, -34), (488, -34)]), W(9), (sx0, 0, 0), nylon, bev=W(2)))
    for i in range(6):
        d = 498 + i * 21.5
        A(cyl(W(10.4), W(46), (sx0 - W(4), Y(-12), Z(d)), hull, axis='y', seg=14, bev=W(0.6)))
        A(cyl(W(11.2), W(10), (sx0 - W(4), Y(-37), Z(d)), brass, axis='y', seg=14))
        A(box((W(10), W(6), W(9)), (sx0 - W(4), Y(-14), Z(d)), nylon, bev=W(1)))  # elastic loop over each shell

    # ---------------- trigger plate, guard, trigger, safety, slide release
    A(side(poly([(606, -40), (706, -40), (706, -58), (690, -62), (612, -54)]), W(26), (0, 0, 0), blue, bev=W(2)))
    A(side(poly([(612, -52), (622, -52), (626, -76), (668, -80), (686, -62), (694, -60), (694, -66), (676, -90), (626, -88), (612, -72)]), W(12), (0, 0, 0), blue, bev=W(2),
           holes=[]))
    A(side(poly([(646, -56), (652, -56), (656, -66), (652, -78), (647, -76), (649, -66)]), W(6), (0, 0, 0), dark, bev=W(1)))
    A(cyl(W(4.5), W(32), (0, Y(-48), Z(698)), dark, axis='x', seg=12))
    A(side(poly([(604, -58), (614, -56), (616, -68), (606, -72)]), W(4), (0, 0, 0), dark, bev=W(1)))

    # ---------------- walnut stock: wrist, comb, toe, thick ribbed recoil pad, sling swivel + strap
    st = side(poly([(704, 10), (742, 2), (790, 0), (1020, -18), (1062, -20), (1062, -150), (1040, -150), (860, -98), (780, -76), (730, -60), (704, -42)]), W(40), (0, 0, 0), walnut, bev=W(7), seg=3)
    A(st)
    pad = side(poly([(1062, -16), (1088, -14), (1092, -24), (1092, -146), (1086, -156), (1062, -154)]), W(44), (0, 0, 0), rubber, bev=W(4), seg=2)
    A(pad)
    for k in range(5):
        A(box((W(46), W(2), W(20)), (0, Y(-40 - k * 22), Z(1078)), rubber))
    A(tube([(0, Y(-118), Z(985)), (0, Y(-134), Z(990)), (0, Y(-132), Z(1004)), (0, Y(-114), Z(1000))], W(2.2), dark, seg=6))

    for p in parts + pump:
        uv_box(p, 0.03)
    body = join(parts, 'sg_body')
    pnode = part(pump, 'pump', pivot=(0, Y(-24), Z((pd0 + pd1) / 2)))
    meta = {'kind': 'weapon', 'id': 'shotgun', 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(21), 'z': Z(560) - 0.11},
            'hatAt': [[0, Y(15), Z(580)], 0.11], 'pump': {'node': 'pump', 'travel': W(95)}}
    return finish('w_shotgun', [body, pnode], meta)


main(build, 'w_shotgun')
