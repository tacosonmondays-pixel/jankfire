# Sniper: an AWM-pattern long-range bolt action (.338-class: 686 mm barrel, big muzzle brake, round action on a
# chassis, thumbhole stock with a raised cheek piece, monopod, folded bipod, 3-12x50 scope on a rail), real
# millimetres x1.67 so it's as long as the game's sniper and the grip sits under the hand.
# The bolt is its own node ('bolt'): it lifts, runs back and slams home with the game's bolt animation.
# Made fun: candy-pink chassis (the sniper's colour), a gold trigger, a SCOPE OPTIONAL sticker for the no-scopers,
# pixel shades hanging off the stock.
# run: blender -b --python tools/blender/make_sniper.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.67 / 1000
BORE_Y, MUZ_Z = 0.02, -1.48
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SCOPE_H = 62


def build():
    pink = mat('sn_pink', 0xff4fd8, rough=0.22, clearcoat=1.0, tex=tex_noise('sn_pink_t', 0xff4fd8, var=0.06, size=16, speck=0xffa8ee, speck_p=0.04, seed=91))
    steel = mat('sn_steel', 0x2a2d33, rough=0.32, metal=0.75)
    dark = mat('sn_dark', 0x141416, rough=0.5, metal=0.35)
    scope_m = mat('sn_scope', 0x18191c, rough=0.55, metal=0.2, tex=tex_noise('sn_scope_t', 0x1a1b1e, var=0.1, size=16, seed=92))
    rubber = mat('sn_rubber', 0x1c1c1e, rough=0.9)
    gold = mat('sn_gold', 0xffc83a, rough=0.18, metal=1.0)
    glass = mat('sn_lens', 0xb070ff, rough=0.04, metal=0.4, emit=0x8a40ff, strength=0.6)
    ocular = mat('sn_ocular', 0x101018, rough=0.05, metal=0.5)
    black = mat('sn_black', 0x050505, rough=0.25)
    white = mat('sn_white', 0xffffff, rough=0.3)
    def stick(px):
        px[:] = hexrgb(0xffe14d); px[:1] = px[-1:] = hexrgb(0x111111)
        text_px(px, 'SCOPE OPTIONAL', 2, 3, 1, 0x111111)
    sticker = mat('sn_sticker', 0xffffff, rough=0.4, tex=tex_canvas('sn_sticker_t', 88, 13, stick))
    parts, bolt = [], []
    A = parts.append

    # ---------------- muzzle brake with three pairs of side ports, barrel
    mb = lathe([(0, Z(0)), (W(15), Z(0)), (W(16), Z(3)), (W(16), Z(84)), (W(14), Z(88))], (0, BORE_Y, 0), steel, seg=18)
    for d in (14, 34, 54): cut(mb, box((W(50), W(15), W(13)), (0, Y(0), Z(d)), None, bev=W(2)))
    A(mb)
    A(lathe([(0, Z(0.5)), (W(5), Z(0.5)), (W(5), Z(9))], (0, BORE_Y, 0), black, seg=10))
    A(lathe([(W(12), Z(86)), (W(12.5), Z(100)), (W(14), Z(400)), (W(15.5), Z(600)), (W(16.5), Z(694))], (0, BORE_Y, 0), steel, seg=18))
    A(lathe([(W(18), Z(682)), (W(18), Z(696))], (0, BORE_Y, 0), dark, seg=18))  # barrel nut
    # ---------------- action + rail + ejection port + bolt-handle cut
    rc = cyl(W(20), W(215), (0, BORE_Y, Z(797)), steel, axis='z', seg=22, bev=W(1.5))
    cut(rc, box((W(16), W(18), W(84)), (W(19), Y(3), Z(788)), None, bev=W(2)))
    cut(rc, box((W(16), W(26), W(48)), (W(19), Y(6), Z(886)), None))
    A(rc)
    A(box((W(22), W(10), W(268)), (0, Y(25), Z(772)), dark, bev=W(1)))
    for k in range(26): A(box((W(22), W(5), W(5.5)), (0, Y(32), Z(644 + k * 10)), dark, bev=W(0.7)))
    # ---------------- the bolt: body, shroud, handle, big knob (its own node)
    bolt.append(cyl(W(11), W(180), (0, BORE_Y, Z(812)), mat('sn_bolt', 0xd8dde6, rough=0.18, metal=1.0), axis='z', seg=16))
    bolt.append(lathe([(W(16), Z(902)), (W(16), Z(918)), (W(12), Z(930)), (0, Z(932))], (0, BORE_Y, 0), steel, seg=16))
    bolt.append(rod((W(8), Y(0), Z(890)), (W(46), Y(-22), Z(898)), W(5.5), steel, seg=10))
    bolt.append(ball(W(12.5), (W(52), Y(-26), Z(899)), black, seg=16, rings=10))
    # ---------------- chassis: forend with vents, action bed, mag, trigger guard + gold trigger
    fe = side(poly([(395, -16), (705, -16), (705, -64), (420, -64), (397, -50)]), W(64), (0, 0, 0), pink, bev=W(8), seg=3)
    for k in range(4): cut(fe, box((W(90), W(11), W(34)), (0, Y(-40), Z(470 + k * 52)), None, bev=W(5)))
    A(fe)
    A(side(poly([(700, -16), (906, -16), (906, -64), (700, -64)]), W(52), (0, 0, 0), pink, bev=W(5)))
    A(side(poly([(752, -62), (818, -62), (816, -112), (756, -112)]), W(26), (0, 0, 0), dark, bev=W(2)))
    A(side(poly([(748, -108), (822, -108), (820, -118), (750, -118)]), W(30), (0, 0, 0), dark, bev=W(2)))
    A(side(poly([(840, -64), (852, -64), (856, -84), (892, -86), (898, -64), (908, -64), (906, -96), (846, -98), (840, -84)]), W(14), (0, 0, 0), pink, bev=W(2)))
    A(side(poly([(866, -64), (873, -64), (877, -74), (873, -84), (867, -82), (869, -74)]), W(7), (0, 0, 0), gold, bev=W(1.2)))
    # ---------------- thumbhole stock, raised cheek piece, butt pad + spacers, monopod
    A(side(poly([(903, -16), (955, 6), (1190, 8), (1216, 12), (1220, -128), (1200, -138), (1020, -132), (962, -150), (930, -150), (918, -124), (921, -100), (911, -86), (906, -64)]),
           W(44), (0, 0, 0), pink, bev=W(7), seg=3,
           holes=[poly([(972, -34), (1036, -28), (1054, -42), (1056, -88), (1040, -106), (992, -112), (976, -96)])]))
    A(side(poly([(1000, 14), (1168, 14), (1172, 34), (1160, 40), (1012, 40), (1000, 32)]), W(40), (0, 0, 0), pink, bev=W(5), seg=3))
    for d in (1030, 1140): A(cyl(W(4), W(10), (0, Y(10), Z(d)), steel, axis='y', seg=8))
    A(side(poly([(1212, 13), (1218, 13), (1222, -132), (1216, -136)]), W(46), (0, 0, 0), dark))
    A(side(poly([(1218, 14), (1242, 12), (1244, -128), (1224, -142)]), W(46), (0, 0, 0), rubber, bev=W(4)))
    A(cyl(W(5), W(40), (0, Y(-152), Z(1150)), steel, axis='y', seg=10))
    A(cyl(W(12), W(8), (0, Y(-146), Z(1150)), dark, axis='y', seg=16))
    A(cyl(W(10), W(5), (0, Y(-172), Z(1150)), rubber, axis='y', seg=14))
    # ---------------- folded bipod under the forend tip
    A(side(poly([(412, -62), (452, -62), (452, -76), (412, -76)]), W(40), (0, 0, 0), dark, bev=W(2)))
    for sx in (-1, 1):
        A(rod((sx * W(15), Y(-74), Z(440)), (sx * W(15), Y(-80), Z(262)), W(5), dark, seg=8))
        A(ball(W(7), (sx * W(15), Y(-80), Z(256)), rubber, seg=10, rings=6))
    # ---------------- scope: objective bell, tube, saddle + turrets, power ring, eyepiece, lenses, rings on the rail
    sy = Y(SCOPE_H)
    A(lathe([(W(26.5), Z(557)), (W(29), Z(556)), (W(30), Z(560)), (W(30), Z(608)), (W(26), Z(624)), (W(17.5), Z(646)), (W(17.5), Z(862)),
             (W(20), Z(873)), (W(23), Z(890)), (W(23), Z(936)), (W(21.5), Z(948))], (0, sy, 0), scope_m, seg=28))
    A(cyl(W(26.5), W(2), (0, sy, Z(560)), glass, axis='z', seg=28))
    A(cyl(W(20), W(2), (0, sy, Z(946)), ocular, axis='z', seg=24))
    A(box((W(44), W(32), W(72)), (0, sy, Z(755)), scope_m, bev=W(5), seg=3))
    A(cyl(W(17), W(26), (0, sy + W(29), Z(755)), scope_m, axis='y', seg=24, bev=W(2)))
    for k in range(12):
        a = k * math.pi / 6
        A(box((W(3), W(18), W(3)), (math.cos(a) * W(17), sy + W(30), Z(755) + math.sin(a) * W(17)), dark))
    A(cyl(W(15), W(24), (W(32), sy, Z(755)), scope_m, axis='x', seg=22, bev=W(2)))
    A(cyl(W(21), W(16), (-W(30), sy, Z(755)), scope_m, axis='x', seg=24, bev=W(2)))
    A(cyl(W(27), W(4), (-W(40), sy, Z(755)), dark, axis='x', seg=24, bev=W(1)))  # side focus wheel
    A(lathe([(W(24.5), Z(880)), (W(24.5), Z(896))], (0, sy, 0), dark, seg=24))
    A(box((W(5), W(10), W(10)), (W(26), sy + W(6), Z(888)), dark))
    for d in (686, 832):
        A(cyl(W(21.5), W(18), (0, sy, Z(d)), dark, axis='z', seg=24, bev=W(2)))
        A(box((W(32), W(18), W(18)), (0, Y(39), Z(d)), dark, bev=W(1.5)))
        A(cyl(W(3), W(40), (0, Y(36), Z(d)), steel, axis='x', seg=8))
    A(box((W(1), W(11), W(68)), (-W(17.8), sy + W(4), Z(690)), sticker, rot=(0, math.pi, 0)))
    # ---------------- sling studs + pixel shades hanging off the left one
    for d in (500, 1150):
        A(cyl(W(6), W(8), (-W(23), Y(-40), Z(d)), steel, axis='x', seg=10))
    A(tube([(-W(28), Y(-40), Z(1150)), (-W(28), Y(-56), Z(1150)), (-W(28), Y(-70), Z(1152))], W(1.2), gold, seg=6))
    px0, py0, pz0 = -W(29), Y(-74), Z(1152)
    shade = [(0, 0, 13, 1), (0, 1, 6, 1), (7, 1, 6, 1), (1, 2, 5, 1), (8, 2, 5, 1), (2, 3, 3, 1), (9, 3, 3, 1)]  # (col, row, width) blocks
    for cx, rw, wd, _ in shade:
        A(box((W(2), W(4), W(4 * wd)), (px0, py0 - W(4 * rw), pz0 - W(26) + W(4 * cx + 2 * wd)), black))
    for cx, rw in ((2, 1), (9, 1)):
        A(box((W(2.4), W(4), W(4)), (px0 - W(0.3), py0 - W(4 * rw), pz0 - W(26) + W(4 * cx + 2)), white))

    for p in parts + bolt: uv_box(p, 0.04)
    for p in parts:
        if p.data.materials and p.data.materials[0] is sticker:
            apply_mods(p); c = p.matrix_world.translation; uv_planar(p, (c.x, c.z, -c.y), (W(68), W(11)), '-x')
    body = join(parts, 'sniper_body')
    bn = part(bolt, 'bolt', pivot=(0, BORE_Y, Z(812)))
    meta = {'kind': 'weapon', 'id': 'sniper', 'paint': ['sn_pink'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SCOPE_H), 'z': Z(948)},
            'hatAt': [[0, Y(SCOPE_H + 20), Z(655)], 0.13], 'bolt': {'node': 'bolt', 'lift': 1.05, 'travel': W(84)}}
    return finish('w_sniper', [body, bn], meta)


main(build, 'w_sniper')
