# SMG: an MP5A3-pattern 9 mm (three-lug muzzle, hooded front post on the cocking tube, stamped receiver, curved
# 30-round mag, polymer trigger pack + grip, rotary drum rear sight, retractable stock pulled out), real millimetres
# x1.0: the game's SMG is already true to size. Made fun: a glossy teal flashlight forend that glows, a teal pull tab
# on the mag and a cheap air freshener ("NEW GUN SMELL") hanging off the sling loop.
# run: blender -b --python tools/blender/make_smg.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.0 / 1000
BORE_Y, MUZ_Z = 0.01, -0.37
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SIGHT_H = 44


def build():
    steel = mat('smg_steel', 0x25272c, rough=0.42, metal=0.55, tex=tex_noise('smg_steel_t', 0x2a2c32, var=0.08, size=16, seed=61))
    dark = mat('smg_dark', 0x121316, rough=0.5, metal=0.45)
    poly_m = mat('smg_polymer', 0x18191c, rough=0.62, tex=tex_noise('smg_poly_t', 0x1c1d21, var=0.18, size=16, seed=62))
    teal = mat('smg_teal', 0x2fc8b8, rough=0.25, clearcoat=0.8)
    lens = mat('smg_lens', 0xe8fffc, rough=0.1, emit=0xc8fff6, strength=3.5)
    rubber = mat('smg_rubber', 0x1a1a1c, rough=0.9)
    dot = mat('smg_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    black = mat('smg_black', 0x050505, rough=0.3)
    def tree_draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0x2fc8b8)
        text_px(px, 'NEW', 5, 10, 1, 0x101010); text_px(px, 'GUN', 5, 19, 1, 0x101010); text_px(px, 'SMELL', 2, 28, 1, 0xff2a8a)
    tree_t = mat('smg_freshener', 0xffffff, rough=0.7, tex=tex_canvas('smg_tree_t', 34, 44, tree_draw))
    string = mat('smg_string', 0xf2f2f2, rough=0.8)
    parts = []; A = parts.append

    # ---------------- three-lug muzzle + barrel stub
    A(lathe([(0, Z(-0.5)), (W(10.5), Z(-0.5)), (W(10.5), Z(26)), (W(8), Z(28))], (0, BORE_Y, 0), dark, seg=16))
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        A(box((W(5), W(3), W(8)), (math.cos(a) * W(11.5), Y(0) + math.sin(a) * W(11.5), Z(20)), dark, rot=(0, 0, a - math.pi / 2)))
    A(lathe([(0, Z(0)), (W(4.6), Z(0)), (W(4.6), Z(6))], (0, BORE_Y, 0), black, seg=10))
    A(lathe([(W(8), Z(26)), (W(8), Z(125))], (0, BORE_Y, 0), dark, seg=14))
    # ---------------- cocking tube + front sight (post in a ring hood) + cocking lever
    A(cyl(W(13), W(40), (0, Y(20), Z(105)), steel, axis='z', seg=18, bev=W(1)))
    A(cyl(W(14), W(8), (0, Y(20), Z(86)), dark, axis='z', seg=18, bev=W(1.2)))
    A(side(poly([(92, 28), (124, 28), (124, 36), (118, 40), (98, 40), (92, 36)]), W(18), (0, 0, 0), steel, bev=W(1.2)))
    hood = cyl(W(15), W(12), (0, Y(SIGHT_H - 1), Z(106)), steel, axis='z', seg=20, bev=W(1))
    cut(hood, cyl(W(10.5), W(30), (0, Y(SIGHT_H - 1), Z(106)), None, axis='z', seg=16))
    A(hood)
    A(box((W(2.6), W(8), W(3)), (0, Y(SIGHT_H - 5.5), Z(106)), dark))
    A(box((W(3.2), W(3), W(3.2)), (0, Y(SIGHT_H - 1.5), Z(106)), dot, bev=W(0.6)))
    A(rod((-W(13), Y(20), Z(104)), (-W(32), Y(27), Z(96)), W(3.5), dark, seg=8))
    A(ball(W(6), (-W(33), Y(27.5), Z(95.5)), dark, seg=10, rings=8))
    # ---------------- receiver: stamped, pressed ribs, slot, ejection port, end cap
    rcv = side(poly([(120, -14), (470, -14), (470, 26), (462, 33), (130, 33), (120, 26)]), W(36), (0, 0, 0), steel, bev=W(2.5))
    cut(rcv, box((W(10), W(17), W(42)), (W(18), Y(10), Z(318)), None))  # ejection port (right)
    A(rcv)
    A(box((W(1.2), W(15), W(38)), (W(17), Y(10), Z(318)), dark))  # bolt face in the port
    for sx in (-1, 1):
        for h in (6, 21):
            A(box((W(1.2), W(3.5), W(300)), (sx * W(18.2), Y(h), Z(295)), steel, bev=W(0.5)))
        for d in (140, 250, 345, 455):
            A(cyl(W(2.2), W(1.2), (sx * W(18.4), Y(-8), Z(d)), dark, axis='x', seg=8))
    A(box((W(1.2), W(3), W(100)), (-W(18.6), Y(14), Z(175)), black))  # cocking slot (left)
    A(side(poly([(470, -12), (488, -12), (490, 24), (476, 30), (470, 30)]), W(38), (0, 0, 0), dark, bev=W(2)))
    # claw-mount dimples on the top
    for d in (160, 230, 300, 370):
        A(box((W(20), W(1), W(10)), (0, Y(33.4), Z(d)), dark))
    # ---------------- rotary drum rear sight on its base (aperture on the sight line)
    A(box((W(22), W(4), W(34)), (0, Y(35), Z(452)), steel, bev=W(1)))
    drum = cyl(W(10), W(22), (0, Y(SIGHT_H), Z(452)), dark, axis='x', seg=18, bev=W(1))
    cut(drum, cyl(W(2.4), W(40), (0, Y(SIGHT_H), Z(452)), None, axis='z', seg=10))
    A(drum)
    A(cyl(W(4), W(3), (W(12.5), Y(SIGHT_H), Z(452)), steel, axis='x', seg=10))
    # ---------------- teal flashlight forend, glowing lens, pressure pads
    A(side(poly([(112, -12), (246, -12), (246, -40), (238, -48), (122, -48), (112, -40)]), W(56), (0, 0, 0), teal, bev=W(7), seg=3))
    A(cyl(W(20), W(5), (0, Y(-30), Z(111)), dark, axis='z', seg=20, bev=W(1)))
    A(cyl(W(16.5), W(3), (0, Y(-30), Z(108.5)), lens, axis='z', seg=20))
    for sx in (-1, 1):
        A(box((W(2), W(13), W(70)), (sx * W(28.3), Y(-30), Z(185)), rubber, bev=W(1)))
    # ---------------- magwell + curved 30-round mag with a teal pull tab
    A(side(poly([(250, -14), (318, -14), (316, -60), (252, -60)]), W(31), (0, 0, 0), steel, bev=W(2)))
    A(side(poly([(318, -48), (328, -48), (328, -64), (318, -60)]), W(20), (0, 0, 0), dark, bev=W(1)))  # paddle release
    front = [(255, -58), (252, -100), (244, -150), (231, -200)]
    back = [(312, -58), (309, -100), (300, -150), (287, -202)]
    A(side(poly(front + back[::-1]), W(22), (0, 0, 0), dark, bev=W(2)))
    A(side(poly([(226, -196), (292, -198), (291, -211), (224, -209)]), W(26), (0, 0, 0), dark, bev=W(2.5)))
    A(side(poly([(244, -210), (270, -210), (268, -232), (246, -232)]), W(4), (0, 0, 0), teal, bev=W(1)))
    for sx in (-1, 1):  # the stamped rib down each side of the mag
        A(side(poly([(270, -60), (276, -60), (264, -190), (258, -190)]), W(1.2), (sx * W(11.4), 0, 0), dark))
    # ---------------- trigger pack, guard, trigger, selector, grip
    A(side(poly([(322, -14), (460, -14), (460, -30), (448, -42), (330, -42), (322, -34)]), W(30), (0, 0, 0), poly_m, bev=W(2)))
    A(side(poly([(330, -40), (342, -40), (344, -62), (392, -64), (396, -42), (404, -42), (402, -70), (336, -72), (330, -62)]), W(13), (0, 0, 0), poly_m, bev=W(1.8)))
    A(side(poly([(366, -42), (372, -42), (375, -52), (371, -62), (366, -60), (368, -52)]), W(6), (0, 0, 0), dark, bev=W(1)))
    A(side(poly([(404, -27), (440, -22), (442, -28), (406, -33)]), W(3), (-W(16), 0, 0), dark, bev=W(0.8)))
    A(cyl(W(2), W(1), (-W(17.6), Y(-26), Z(432)), teal, axis='x', seg=8))
    A(side(poly([(408, -40), (452, -40), (482, -128), (480, -142), (468, -150), (445, -150), (440, -140), (430, -118), (434, -108), (425, -96), (428, -84), (418, -72)]), W(32), (0, 0, 0), poly_m, bev=W(7), seg=3))
    # ---------------- A3 stock, pulled out: two side rails + butt plate with a rubber pad
    for sx in (-1, 1):
        A(box((W(6), W(9), W(195)), (sx * W(17.5), Y(6), Z(568)), dark, bev=W(1.5)))
    A(side(poly([(660, 30), (676, 30), (680, 18), (680, -84), (672, -96), (660, -96), (660, -84), (666, -10), (660, 18)]), W(42), (0, 0, 0), dark, bev=W(3)))
    A(side(poly([(678, 28), (690, 26), (692, -86), (680, -94)]), W(44), (0, 0, 0), rubber, bev=W(3)))
    A(side(poly([(486, -16), (520, -16), (520, -24), (490, -24)]), W(20), (0, 0, 0), dark, bev=W(1)))  # stock release lever
    # ---------------- sling loop + air freshener hanging off it (left side, where you can see it)
    A(tube([(-W(19), Y(20), Z(478)), (-W(26), Y(14), Z(481)), (-W(26), Y(4), Z(481)), (-W(19), Y(-2), Z(478))], W(2), dark, seg=6))
    A(tube([(-W(26), Y(4), Z(482)), (-W(28), Y(-30), Z(484)), (-W(29), Y(-55), Z(486))], W(0.7), string, seg=4))
    A(side(poly([(486, -56), (473, -71), (479, -71), (466, -87), (473, -87), (461, -101), (482, -101), (482, -107), (490, -107),
                 (490, -101), (511, -101), (499, -87), (506, -87), (493, -71), (499, -71)]), W(1.2), (-W(29.5), 0, 0), tree_t))  # the freshener (a pine tree, obviously)

    for p in parts: uv_box(p, 0.03)
    for p in parts:
        if p.data.materials and p.data.materials[0] is tree_t:
            apply_mods(p); uv_planar(p, (-W(29.5), Y(-81), Z(486)), W(52), '-x')
    WZ = {'smg_steel': 'a', 'smg_polymer': 'a', 'smg_teal': 'a', 'smg_rubber': 'a', 'smg_dark': 'b', 'smg_black': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'smg_body', WZ, default='n', rule=lambda m, c: 'b' if m == 'smg_steel' and c[2] < Z(120) else 'a' if m == 'smg_dark' and c[2] > Z(468) else None)  # sight hood with the barrel, stock with the body
    meta = {'kind': 'weapon', 'id': 'smg', 'paint': ['smg_teal'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SIGHT_H), 'z': Z(452) - 0.04},
            'hatAt': [[0, Y(34), Z(300)], 0.1]}
    return finish('w_smg', bodies + [], meta)


main(build, 'w_smg')
