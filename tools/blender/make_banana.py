# Peel Shooter: an AKS-74U-pattern compact (gas block with the front sight, short handguards, stamped receiver with
# the rear sight on the top cover, big safety lever, stock folded along the left side), real millimetres x1.1 to the
# game's Peel Shooter. The joke is the AK nickname: its "banana mag" is a real banana (five-sided, speckled, with the
# 4011 sticker), and the muzzle device is a banana peel clamped on with a hose clamp, petals flaring like a flash
# hider. You aim through a banana-yellow collimator red dot on a side-rail mount (the real AK way to put an optic on),
# so the top cover stays down out of the way. run: blender -b --python tools/blender/make_banana.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.1 / 1000
BORE_Y, MUZ_Z = 0.0, -0.36
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SIGHT_H = 33   # the iron sights (low, under the red dot)
DOT_H = 62     # the red dot's sight line


def build():
    steel = mat('bn_steel', 0x1e1f23, rough=0.45, metal=0.55, tex=tex_noise('bn_steel_t', 0x222328, var=0.1, size=16, seed=121))
    dark = mat('bn_dark', 0x121316, rough=0.5, metal=0.4)
    wood = mat('bn_wood', 0x8a3a1a, rough=0.38, clearcoat=0.4, tex=tex_wood('bn_wood_t', 0x9a4420, 0x4e1a08, size=32, seed=122, rings=5))
    grip_w = mat('bn_grip', 0x5a3018, rough=0.45, tex=tex_wood('bn_grip_t', 0x6a3a1c, 0x2e1408, size=32, seed=123, rings=4))
    peel = mat('bn_peel', 0xffd23a, rough=0.35, clearcoat=0.3, tex=tex_noise('bn_peel_t', 0xffd23a, var=0.08, size=32, speck=0x6a4a18, speck_p=0.06, seed=124))
    brown = mat('bn_brown', 0x4a2a10, rough=0.6)
    stem = mat('bn_stem', 0x6a7a2a, rough=0.6)
    chrome = mat('bn_clamp', 0xc8ccd4, rough=0.2, metal=1.0)
    dot = mat('bn_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    black = mat('bn_black', 0x050505, rough=0.3)
    def stk(px):
        px[:] = hexrgb(0x2050b0); px[0] = px[-1] = hexrgb(0xffe14d)
        text_px(px, '4011', 2, 3, 1, 0xffffff)
    sticker = mat('bn_sticker', 0xffffff, rough=0.35, tex=tex_canvas('bn_sticker_t', 28, 13, stk))
    parts = []; A = parts.append

    # ---------------- the peel: a band of banana round the barrel, a hose clamp, four petals flaring out the front
    A(lathe([(W(9), Z(64)), (W(13.5), Z(60)), (W(13.5), Z(34)), (W(11), Z(30))], (0, BORE_Y, 0), peel, seg=16))
    A(lathe([(W(14.6), Z(42)), (W(14.6), Z(50))], (0, BORE_Y, 0), chrome, seg=16))
    A(box((W(6), W(5), W(9)), (W(13), Y(9), Z(46)), chrome, rot=(0, 0, -0.6)))
    outer = [(60, 13.5), (40, 13.5), (28, 17), (16, 23), (6, 29), (0, 33), (-2, 36)]
    inner = [(-2, 36), (-1, 31), (4, 27), (14, 21), (26, 15.5), (40, 11.5), (60, 11.5)]
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        pet = side(poly(outer + inner[1:]), W(15), (0, 0, 0), peel, bev=W(1.2), angle=50)
        pet.rotation_euler = Euler((0, math.pi / 2 - a, 0), 'XYZ')  # round the bore (blender y): the petal points at angle a
        A(pet)
        tip = ball(W(3), (math.cos(a) * W(35.5), Y(0) + math.sin(a) * W(35.5), Z(-2)), brown, seg=8, rings=6)
        A(tip)
    A(lathe([(0, Z(28)), (W(4.4), Z(28)), (W(4.4), Z(33))], (0, BORE_Y, 0), black, seg=10))
    # ---------------- barrel, gas block + front sight tower, gas tube under its upper handguard, lower handguard
    A(lathe([(W(8), Z(28)), (W(8), Z(130))], (0, BORE_Y, 0), dark, seg=14))
    A(side(poly([(118, -12), (168, -12), (168, 14), (150, 17), (134, 17), (118, 10)]), W(24), (0, 0, 0), steel, bev=W(2)))
    for sx in (-1, 1): A(side(poly([(124, 14), (144, 14), (142, 37), (128, 37)]), W(3), (sx * W(7.5), 0, 0), steel, bev=W(0.8)))
    A(box((W(2.6), W(16), W(3)), (0, Y(SIGHT_H - 9.5), Z(135)), dark))
    A(box((W(3), W(3), W(3)), (0, Y(SIGHT_H - 1.5), Z(135)), dot, bev=W(0.5)))
    A(lathe([(W(9), Z(166)), (W(12.5), Z(172)), (W(12.5), Z(246)), (W(10), Z(252))], (0, Y(20), 0), wood, seg=14))
    A(side(poly([(168, -10), (252, -10), (252, -30), (242, -37), (178, -37), (168, -28)]), W(36), (0, 0, 0), wood, bev=W(5), seg=3))
    for d in (190, 210, 230):
        for sx in (-1, 1): A(box((W(1), W(14), W(3)), (sx * W(18.1), Y(-24), Z(d)), brown))
    # ---------------- receiver, top cover with the rear sight, safety lever, charging handle, dimples
    A(side(poly([(250, -24), (522, -24), (522, 10), (250, 10)]), W(30), (0, 0, 0), steel, bev=W(2)))
    A(side(poly([(252, 8), (506, 8), (506, 16), (496, 22), (262, 22), (252, 16)]), W(28), (0, 0, 0), steel, bev=W(5), seg=3))
    for d in (330, 400, 470): A(box((W(29), W(1.5), W(5)), (0, Y(21.5), Z(d)), dark))
    A(side(poly([(256, 20), (290, 20), (290, 27), (256, 27)]), W(20), (0, 0, 0), steel, bev=W(1)))
    for sx in (-1, 1): A(side(poly([(264, 26), (280, 26), (279, 39), (266, 39)]), W(3.5), (sx * W(5.5), 0, 0), dark, bev=W(0.6)))
    A(box((W(7.5), W(6), W(12)), (0, Y(SIGHT_H - 3), Z(272)), dark))  # notch bottom = sight line
    A(side(poly([(300, -3), (420, 1), (424, 8), (300, 5), (296, 1)]), W(3), (W(16), 0, 0), dark, bev=W(0.8)))
    A(side(poly([(296, -8), (308, -8), (308, 6), (296, 6)]), W(4), (W(16.5), 0, 0), dark, bev=W(1)))
    A(rod((W(15), Y(4), Z(310)), (W(34), Y(6), Z(306)), W(3.8), steel, seg=8))
    A(ball(W(5.5), (W(36), Y(6), Z(306)), steel, seg=10, rings=6))
    for sx in (-1, 1): A(cyl(W(5), W(1.5), (sx * W(15.4), Y(-6), Z(296)), dark, axis='x', seg=10))
    # ---------------- side-rail mount + a banana-yellow collimator sight riding over the top cover
    optic = mat('bn_optic', 0xffd23a, rough=0.25, clearcoat=0.8)
    lens = mat('bn_lens', 0x9fe8ff, rough=0.02, metal=0.3, alpha=0.18)
    reticle = mat('bn_reticle', 0xff3a1a, rough=0.3, emit=0xff3a1a, strength=5.0)
    A(side(poly([(326, -3), (426, -3), (426, 9), (326, 9)]), W(3), (-W(16.4), 0, 0), dark, bev=W(0.6)))  # the AK side rail
    A(side(poly([(334, -6), (418, -6), (418, 38), (404, 46), (348, 46), (334, 38)]), W(4), (-W(18.8), 0, 0), dark, bev=W(1)))  # mount plate
    A(cyl(W(7), W(6), (-W(22.5), Y(4), Z(376)), dark, axis='x', seg=12))  # clamp knob
    A(box((W(22), W(6), W(70)), (-W(10), Y(43), Z(376)), dark, bev=W(1.5)))  # arm over the top cover
    A(box((W(18), W(10), W(56)), (0, Y(DOT_H - 20), Z(376)), dark, bev=W(1.5)))  # saddle under the tube
    A(lathe([(W(15), Z(400)), (W(17.5), Z(398)), (W(17.5), Z(336)), (W(19), Z(334)), (W(19), Z(326)), (W(16.5), Z(326)), (W(16.5), Z(334)), (W(15), Z(336)), (W(15), Z(398))],
            (0, Y(DOT_H), 0), optic, seg=24, cap=False))
    A(cyl(W(15), W(1), (0, Y(DOT_H), Z(338)), lens, axis='z', seg=24))
    A(cyl(W(1.5), W(1.2), (0, Y(DOT_H), Z(337.5)), reticle, axis='z', seg=10))  # the dot
    A(cyl(W(5), W(6), (0, Y(DOT_H + 19), Z(372)), dark, axis='y', seg=12))  # elevation turret
    A(cyl(W(5), W(6), (W(19.5), Y(DOT_H), Z(372)), dark, axis='x', seg=12))  # windage
    A(cyl(W(6), W(8), (-W(20), Y(DOT_H), Z(360)), dark, axis='x', seg=12))  # battery cap
    # ---------------- trigger guard, trigger, mag catch, grip
    A(side(poly([(330, -24), (338, -24), (340, -48), (390, -50), (396, -28), (404, -24), (408, -28), (400, -56), (336, -58), (330, -48)]), W(12), (0, 0, 0), steel, bev=W(1.8)))
    A(side(poly([(358, -24), (364, -24), (368, -34), (364, -46), (358, -44), (360, -34)]), W(6), (0, 0, 0), dark, bev=W(1)))
    A(side(poly([(306, -24), (316, -24), (318, -42), (308, -42)]), W(14), (0, 0, 0), dark, bev=W(1)))
    A(side(poly([(404, -24), (442, -24), (470, -120), (466, -130), (446, -134), (436, -124), (428, -90), (418, -60)]), W(30), (0, 0, 0), grip_w, bev=W(6), seg=3))
    # ---------------- rear trunnion + stock folded along the left side (struts + butt plate by the handguard)
    A(side(poly([(504, -24), (528, -24), (528, 10), (504, 10)]), W(32), (0, 0, 0), dark, bev=W(2)))
    A(cyl(W(6), W(30), (-W(19), Y(-6), Z(516)), dark, axis='y', seg=10))
    A(side(poly([(258, 6), (516, 6), (516, -4), (258, -4)]), W(4), (-W(23), 0, 0), steel, bev=W(1)))
    A(side(poly([(515, -12), (519, -24), (264, -96), (258, -84)]), W(4), (-W(23), 0, 0), steel, bev=W(1)))
    A(side(poly([(248, 12), (268, 12), (270, -96), (262, -104), (248, -98)]), W(26), (-W(30), 0, 0), steel, bev=W(2.5)))
    # ---------------- the banana mag: five-sided, speckled, curving forward like the real thing, stem in the receiver
    R = 240
    path, radii = [], []
    n = 14
    for i in range(n + 1):
        t = math.radians(48) * i / n
        d, h = 285 - R * (1 - math.cos(t)), -18 - R * math.sin(t)
        path.append((0, Y(h), Z(d)))
        u = i / n
        radii.append(W(10 + 9 * math.sin(min(1, u / 0.3) * math.pi / 2) - (0 if u < 0.7 else 12 * ((u - 0.7) / 0.3) ** 1.5)))
    A(sweep(path, radii, peel, seg=5, smooth_angle=30))
    A(cyl(W(6.5), W(26), (0, Y(-8), Z(285)), stem, axis='y', seg=8))
    A(ball(W(6), path[-1], brown, seg=8, rings=6))
    sp = path[5]
    stc = cyl(W(7.5), W(1), (sp[0] - W(16.2), sp[1], sp[2]), sticker, axis='x', seg=16)
    stc.scale = (1.0, 1.45, 1.0)  # blender y = game z: a wide oval across the banana, like the real stickers
    A(stc)

    for p in parts: uv_box(p, 0.03)
    apply_mods(stc)
    for o in bpy.context.view_layer.objects.selected: o.select_set(False)
    bpy.context.view_layer.objects.active = stc; stc.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    uv_planar(stc, (sp[0] - W(16.2), sp[1], sp[2]), (W(22), W(13)), '-x')
    WZ = {'bn_steel': 'a', 'bn_wood': 'a', 'bn_grip': 'a', 'bn_dark': 'b', 'bn_peel': 'b', 'bn_brown': 'b', 'bn_stem': 'b', 'bn_optic': 'a'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'banana_body', WZ, default='n', rule=None)
    meta = {'kind': 'weapon', 'id': 'banana', 'paint': ['bn_peel'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(DOT_H), 'z': Z(398)},
            'hatAt': [[0, Y(23), Z(420)], 0.1]}
    return finish('w_banana', bodies + [], meta)


main(build, 'w_banana')
