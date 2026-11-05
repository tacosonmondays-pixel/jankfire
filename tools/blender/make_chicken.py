# Chicken Rocket: a Carl Gustaf M3-pattern 84 mm recoilless rifle (rubber muzzle bumper, wrapped barrel, front grip,
# firing mechanism + pistol grip, shoulder rest, optic on the left, carry handle, venturi breech), real millimetres
# x1.05 so the grip lands under the hand. Loaded with a rubber chicken: head, neck and wing tips sticking out of the
# muzzle, beak open mid-scream, googly eyes (it's the same yellow as the chicken that flies out).
# run: blender -b --python tools/blender/make_chicken.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.05 / 1000
AXIS_Y, TUBE_Z = 0.0, -0.50    # distances d are measured back from the front of the tube
def P(d, h): return (TUBE_Z + d * S, AXIS_Y + h * S)
def Z(d): return TUBE_Z + d * S
def Y(h): return AXIS_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]


def build():
    olive = mat('ck_tube', 0x4a6a2a, rough=0.35, clearcoat=0.5, tex=tex_noise('ck_tube_t', 0x4a6a2a, var=0.1, size=32, speck=0x2e4418, speck_p=0.05, seed=101))
    rubber = mat('ck_rubber', 0x1c1c1e, rough=0.85, tex=tex_noise('ck_rubber_t', 0x1e1e20, var=0.2, size=16, seed=102))
    steel = mat('ck_steel', 0x3a3d44, rough=0.4, metal=0.7)
    dark = mat('ck_dark', 0x141416, rough=0.5, metal=0.3)
    inside = mat('ck_inside', 0x0a0a0c, rough=0.9)
    red = mat('ck_red', 0xe0202a, rough=0.3, clearcoat=0.6)
    lens = mat('ck_lens', 0xff4fd8, rough=0.05, emit=0xff4fd8, strength=1.5)
    yel = mat('ck_chicken', 0xffe14d, rough=0.28, clearcoat=0.6)
    beak = mat('ck_beak', 0xff8a00, rough=0.3, clearcoat=0.5)
    comb = mat('ck_comb', 0xff2222, rough=0.3, clearcoat=0.5)
    mouth = mat('ck_mouth', 0x8a1020, rough=0.5)
    white = mat('ck_white', 0xffffff, rough=0.2)
    black = mat('ck_black', 0x050505, rough=0.2)
    def stencil(px):
        px[:] = hexrgb(0xffe14d); px[:2] = px[-2:] = hexrgb(0x111111)
        text_px(px, 'CHKN', 3, 5, 2, 0x111111)
    band = mat('ck_stencil', 0xffffff, rough=0.4, tex=tex_canvas('ck_stencil_t', 54, 24, stencil))
    def warn(px):
        px[:] = hexrgb(0xffffff); px[:2] = px[-2:] = hexrgb(0xe0102a)
        text_px(px, 'BACKBLAST', 3, 4, 1, 0xe0102a); text_px(px, 'AREA: CLUCK', 3, 13, 1, 0x111111)
    warn_t = mat('ck_warn', 0xffffff, rough=0.4, tex=tex_canvas('ck_warn_t', 72, 22, warn))
    parts = []; A = parts.append

    # ---------------- tube: rubber bumper, hollow mouth with a dark lining, wrapped barrel, bands, stencils
    A(lathe([(W(44), Z(40)), (W(44), Z(-2)), (W(56), Z(-4)), (W(59), Z(4)), (W(59), Z(40)), (W(53), Z(48))], (0, AXIS_Y, 0), rubber, seg=28, cap=False))
    A(lathe([(0, Z(130)), (W(43.6), Z(130)), (W(43.6), Z(0))], (0, AXIS_Y, 0), inside, seg=24, cap=False))
    A(lathe([(W(52), Z(46)), (W(52), Z(882))], (0, AXIS_Y, 0), olive, seg=28))
    for d in (120, 440, 790): A(lathe([(W(54), Z(d - 8)), (W(54), Z(d + 8))], (0, AXIS_Y, 0), dark, seg=28))
    A(box((W(1), W(26), W(58)), (-W(52.4), Y(6), Z(190)), band, rot=(0, math.pi, 0)))
    A(box((W(1), W(22), W(72)), (-W(52.4), Y(12), Z(840)), warn_t, rot=(0, math.pi, 0)))
    # ---------------- front grip on a clamp
    A(lathe([(W(54.5), Z(254)), (W(54.5), Z(292))], (0, AXIS_Y, 0), dark, seg=28))
    A(side(poly([(252, -52), (292, -52), (296, -140), (290, -150), (256, -150), (250, -140), (254, -128), (248, -114), (252, -102), (246, -88)]), W(32), (0, 0, 0), rubber, bev=W(6), seg=3))
    # ---------------- firing mechanism, trigger guard, red trigger, pistol grip
    A(side(poly([(470, -46), (592, -46), (592, -66), (572, -76), (480, -76), (470, -64)]), W(40), (0, 0, 0), dark, bev=W(3)))
    A(side(poly([(486, -74), (496, -74), (498, -94), (528, -96), (530, -76), (536, -76), (534, -104), (492, -106), (486, -94)]), W(12), (0, 0, 0), dark, bev=W(2)))
    A(side(poly([(506, -76), (514, -76), (518, -86), (514, -96), (508, -94), (510, -86)]), W(8), (0, 0, 0), red, bev=W(1.5)))
    A(side(poly([(532, -74), (574, -74), (600, -172), (594, -184), (570, -188), (562, -178), (556, -152), (560, -140), (550, -124), (552, -110), (542, -96)]), W(32), (0, 0, 0), rubber, bev=W(6), seg=3))
    # ---------------- shoulder rest
    A(side(poly([(618, -50), (792, -50), (792, -86), (772, -100), (640, -100), (618, -86)]), W(48), (0, 0, 0), rubber, bev=W(8), seg=3))
    for d in (640, 770): A(lathe([(W(54.5), Z(d - 6)), (W(54.5), Z(d + 6))], (0, AXIS_Y, 0), dark, seg=28))
    # ---------------- optic on the left (glowing lens), carry handle on top
    A(rod((-W(30), Y(42), Z(445)), (-W(62), Y(58), Z(445)), W(8), dark, seg=8))
    A(box((W(44), W(46), W(104)), (-W(74), Y(66), Z(445)), dark, bev=W(6), seg=3))
    A(cyl(W(17), W(3), (-W(74), Y(68), Z(392)), lens, axis='z', seg=20))
    A(cyl(W(15), W(3), (-W(74), Y(68), Z(498)), black, axis='z', seg=20))
    A(lathe([(W(21), Z(380)), (W(21), Z(394))], (-W(74), Y(68), 0), dark, seg=20))
    A(tube([(0, Y(50), Z(392)), (0, Y(100), Z(418)), (0, Y(100), Z(568)), (0, Y(50), Z(594))], W(9), dark, seg=10))
    A(cyl(W(12), W(120), (0, Y(100), Z(493)), rubber, axis='z', seg=14, bev=W(2)))
    # ---------------- venturi breech: lock ring, flared cone (dark inside), lever
    A(lathe([(W(57), Z(878)), (W(60), Z(884)), (W(60), Z(906)), (W(55), Z(912))], (0, AXIS_Y, 0), steel, seg=28))
    A(lathe([(W(46), Z(930)), (W(62), Z(1020)), (W(72), Z(1066)), (W(77), Z(1066)), (W(70), Z(1030)), (W(60), Z(960)), (W(54), Z(906))], (0, AXIS_Y, 0), steel, seg=28, cap=False))
    A(lathe([(0, Z(925)), (W(46), Z(930)), (W(62), Z(1018)), (W(70.5), Z(1062))], (0, AXIS_Y, 0), inside, seg=24, cap=False))
    A(rod((W(56), Y(4), Z(896)), (W(80), Y(-30), Z(900)), W(5), steel, seg=8))
    A(ball(W(9), (W(82), Y(-33), Z(900)), red, seg=12, rings=8))

    # ---------------- the rubber chicken: body stuffed in the tube, neck + head out the front, wing tips at the mouth
    A(ball(W(43), (0, Y(4), Z(64)), yel, scale=(1, 1, 1.5), seg=20, rings=12))
    neck = [(0, Y(18), Z(30)), (0, Y(28), Z(0)), (0, Y(40), Z(-38)), (0, Y(42), Z(-72)), (0, Y(34), Z(-98))]
    A(sweep(neck, [W(19), W(17), W(15), W(14), W(13)], yel, seg=12))
    hx, hy, hz = 0, Y(34), Z(-112)
    A(ball(W(26), (hx, hy, hz), yel, scale=(0.85, 0.95, 1.15), seg=18, rings=12))
    A(cyl(W(10), W(40), (0, Y(38), Z(-146)), beak, axis='z', r2=W(2), seg=10, rot=(0.25, 0, 0)))  # upper beak, tilted up
    A(cyl(W(8), W(32), (0, Y(22), Z(-142)), beak, axis='z', r2=W(2), seg=10, rot=(-0.45, 0, 0)))  # lower beak, hanging open
    A(ball(W(9), (0, Y(30), Z(-132)), mouth, seg=10, rings=6))
    for k, (d, h, r) in enumerate(((-100, 58, 9), (-112, 61, 10.5), (-124, 57, 8.5))):
        A(ball(W(r), (0, Y(h), Z(d)), comb, scale=(0.5, 1, 1), seg=12, rings=8))
    A(ball(W(9), (0, Y(10), Z(-134)), comb, scale=(0.55, 1.4, 0.8), seg=12, rings=8))  # wattle
    for sx in (-1, 1):
        A(ball(W(9), (sx * W(17), Y(42), Z(-120)), white, scale=(0.6, 1, 1), seg=12, rings=8))
        A(ball(W(4), (sx * W(21.5), Y(40), Z(-123)), black, scale=(0.6, 1, 1), seg=8, rings=6))
        A(ball(W(14), (sx * W(34), Y(-6), Z(2)), yel, scale=(0.45, 0.85, 1.5), seg=12, rings=8))  # wing tips

    for p in parts: uv_box(p, 0.04)
    for p in parts:
        if p.data.materials and p.data.materials[0] in (band, warn_t):
            apply_mods(p); c = p.matrix_world.translation
            uv_planar(p, (c.x, c.z, -c.y), (W(58), W(26)) if p.data.materials[0] is band else (W(72), W(22)), '-x')
    WZ = {'ck_tube': 'a', 'ck_rubber': 'b', 'ck_steel': 'b', 'ck_dark': 'b', 'ck_chicken': 'b', 'ck_beak': 'b', 'ck_comb': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'chicken_body', WZ, default='n', rule=None)
    meta = {'kind': 'weapon', 'id': 'chicken', 'paint': ['ck_chicken'], 'muzzle': [0, 0, -0.62], 'hatAt': [[0, Y(60), Z(-114)], 0.09]}
    return finish('w_chicken', bodies + [], meta)


main(build, 'w_chicken')
