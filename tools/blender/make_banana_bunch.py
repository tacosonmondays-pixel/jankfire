# Bunch Blaster (banana_bunch): the Peel Shooter's AKS-74U pattern (make_banana.py: gas block with the front sight,
# short handguards, stamped receiver, top cover with the rear sight, big safety lever, the side-rail red dot you aim
# through), real millimetres x1.1 so the muzzle (-0.36) matches, re-dressed in the AK-74's real "plum" polymer
# furniture and the AKS-74U's own expansion-chamber flash hider. The Peel Shooter's banana-mag joke, escalated: the
# magazine is a whole hand of four ripe bananas: the crown jammed in the magwell, the fingers curving forward and up
# round both sides of the handguard, the way bananas grow (so you can see them from behind the gun).
# Made fun: the crown wears the supermarket's printed tape band, and it says PRODUCE OF JANK.
# run: blender -b --python tools/blender/make_banana_bunch.py
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


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def band(px):  # the supermarket tape round the crown
    h, w = px.shape[:2]
    px[:] = hexrgb(0x1f4fd8); px[0] = px[-1] = hexrgb(0xffe14d)
    text_px(px, 'PRODUCE OF JANK', 3, 2, 1, 0xffffff)


def ripe(px):  # a ripe banana: yellow, sugar spots, a greener stalk end (u runs along the banana)
    h, w = px.shape[:2]
    r = np.random.default_rng(231)
    px[:] = hexrgb(0xffd23a) * (0.92 + 0.12 * r.random((h, w)))[:, :, None]
    spots = r.random((h, w)) < 0.06
    px[spots] = hexrgb(0x6a4a18)
    px[(r.random((h, w)) < 0.05) & ~spots] = hexrgb(0x9a7a28)


def build():
    steel = mat('bb_steel', 0x1e1f23, rough=0.45, metal=0.55, tex=tex_noise('bb_steel_t', 0x222328, var=0.1, size=16, seed=221))
    dark = mat('bb_dark', 0x121316, rough=0.5, metal=0.4)
    plum = mat('bb_plum', 0x5a1a48, rough=0.4, clearcoat=0.45, tex=tex_noise('bb_plum_t', 0x5a1a48, var=0.08, size=16, speck=0x3e1030, speck_p=0.06, seed=222))
    peel = mat('bb_peel', 0xffffff, rough=0.35, clearcoat=0.3, tex=tex_canvas('bb_peel_t', 32, 32, ripe))
    crown_m = mat('bb_crown', 0x7a8a3a, rough=0.6, tex=tex_noise('bb_crown_t', 0x7a8a3a, var=0.15, size=16, speck=0x4a4a1a, speck_p=0.08, seed=223))
    brown = mat('bb_brown', 0x3a2410, rough=0.6)
    tape = mat('bb_band', 0xffffff, rough=0.4, tex=tex_canvas('bb_band_t', 94, 11, band))
    dot = mat('bb_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    black = mat('bb_black', 0x050505, rough=0.3)
    optic = mat('bb_optic', 0x5a1a48, rough=0.25, clearcoat=0.8)
    lens = mat('bb_lens', 0x9fe8ff, rough=0.02, metal=0.3, alpha=0.18)
    reticle = mat('bb_reticle', 0xff3a1a, rough=0.3, emit=0xff3a1a, strength=5.0)
    parts = []; A = parts.append

    # ---------------- the AKS-74U flash hider: an expansion chamber with a bell, on the barrel stub
    A(lathe([(W(8.6), Z(0)), (W(13), Z(0)), (W(15.5), Z(6)), (W(15.5), Z(12)), (W(13.5), Z(16)), (W(13.5), Z(58)), (W(11), Z(62))], (0, BORE_Y, 0), dark, seg=18, cap=False))
    A(lathe([(0, Z(14)), (W(8.6), Z(12)), (W(8.6), Z(1))], (0, BORE_Y, 0), black, seg=12, cap=False))
    for k in range(6): A(box((W(2), W(3), W(36)), (math.cos(k * math.pi / 3) * W(13.5), BORE_Y + math.sin(k * math.pi / 3) * W(13.5), Z(38)), steel, rot=(0, 0, k * math.pi / 3)))
    # ---------------- barrel, gas block + front sight tower, gas tube under the upper handguard, lower handguard (plum)
    A(lathe([(W(8), Z(56)), (W(8), Z(130))], (0, BORE_Y, 0), dark, seg=14, cap=False))
    A(side(poly([(118, -12), (168, -12), (168, 14), (150, 17), (134, 17), (118, 10)]), W(24), (0, 0, 0), steel, bev=W(2)))
    for sx in (-1, 1): A(side(poly([(124, 14), (144, 14), (142, 37), (128, 37)]), W(3), (sx * W(7.5), 0, 0), steel, bev=W(0.8)))
    A(box((W(2.6), W(16), W(3)), (0, Y(SIGHT_H - 9.5), Z(135)), dark))
    A(box((W(3), W(3), W(3)), (0, Y(SIGHT_H - 1.5), Z(135)), dot, bev=W(0.5)))
    A(lathe([(W(9), Z(166)), (W(12.5), Z(172)), (W(12.5), Z(246)), (W(10), Z(252))], (0, Y(20), 0), plum, seg=14))
    A(side(poly([(168, -10), (252, -10), (252, -30), (242, -37), (178, -37), (168, -28)]), W(36), (0, 0, 0), plum, bev=W(5), seg=3))
    for d in (190, 210, 230):
        for sx in (-1, 1): A(box((W(1), W(14), W(3)), (sx * W(18.1), Y(-24), Z(d)), dark))
    # ---------------- receiver, top cover with the rear sight, safety lever, charging handle, dimples
    A(side(poly([(250, -24), (522, -24), (522, 10), (250, 10)]), W(30), (0, 0, 0), steel, bev=W(2)))
    A(side(poly([(252, 8), (506, 8), (506, 16), (496, 22), (262, 22), (252, 16)]), W(28), (0, 0, 0), steel, bev=W(5), seg=3))
    for d in (330, 400, 470): A(box((W(29), W(1.5), W(5)), (0, Y(21.5), Z(d)), dark))
    A(side(poly([(256, 20), (290, 20), (290, 27), (256, 27)]), W(20), (0, 0, 0), steel, bev=W(1)))
    for sx in (-1, 1): A(side(poly([(264, 26), (280, 26), (279, 39), (266, 39)]), W(3.5), (sx * W(5.5), 0, 0), dark, bev=W(0.6)))
    A(box((W(7.5), W(6), W(12)), (0, Y(SIGHT_H - 3), Z(272)), dark))
    A(side(poly([(300, -3), (420, 1), (424, 8), (300, 5), (296, 1)]), W(3), (W(16), 0, 0), dark, bev=W(0.8)))
    A(side(poly([(296, -8), (308, -8), (308, 6), (296, 6)]), W(4), (W(16.5), 0, 0), dark, bev=W(1)))
    A(rod((W(15), Y(4), Z(310)), (W(34), Y(6), Z(306)), W(3.8), steel, seg=8))
    A(ball(W(5.5), (W(36), Y(6), Z(306)), steel, seg=10, rings=6))
    for sx in (-1, 1): A(cyl(W(5), W(1.5), (sx * W(15.4), Y(-6), Z(296)), dark, axis='x', seg=10))
    # ---------------- side-rail mount + a plum collimator sight riding over the top cover (the sight line)
    A(side(poly([(326, -3), (426, -3), (426, 9), (326, 9)]), W(3), (-W(16.4), 0, 0), dark, bev=W(0.6)))
    A(side(poly([(334, -6), (418, -6), (418, 38), (404, 46), (348, 46), (334, 38)]), W(4), (-W(18.8), 0, 0), dark, bev=W(1)))
    A(cyl(W(7), W(6), (-W(22.5), Y(4), Z(376)), dark, axis='x', seg=12))
    A(box((W(22), W(6), W(70)), (-W(10), Y(43), Z(376)), dark, bev=W(1.5)))
    A(box((W(18), W(10), W(56)), (0, Y(DOT_H - 20), Z(376)), dark, bev=W(1.5)))
    A(lathe([(W(15), Z(400)), (W(17.5), Z(398)), (W(17.5), Z(336)), (W(19), Z(334)), (W(19), Z(326)), (W(16.5), Z(326)), (W(16.5), Z(334)), (W(15), Z(336)), (W(15), Z(398))],
            (0, Y(DOT_H), 0), optic, seg=24, cap=False))
    A(cyl(W(15), W(1), (0, Y(DOT_H), Z(338)), lens, axis='z', seg=24))
    A(cyl(W(1.5), W(1.2), (0, Y(DOT_H), Z(337.5)), reticle, axis='z', seg=10))
    A(cyl(W(5), W(6), (0, Y(DOT_H + 19), Z(372)), dark, axis='y', seg=12))
    A(cyl(W(5), W(6), (W(19.5), Y(DOT_H), Z(372)), dark, axis='x', seg=12))
    A(cyl(W(6), W(8), (-W(20), Y(DOT_H), Z(360)), dark, axis='x', seg=12))
    # ---------------- trigger guard, trigger, mag catch, plum grip, rear trunnion + the stock hinge (stock removed)
    A(side(poly([(330, -24), (338, -24), (340, -48), (390, -50), (396, -28), (404, -24), (408, -28), (400, -56), (336, -58), (330, -48)]), W(12), (0, 0, 0), steel, bev=W(1.8)))
    A(side(poly([(358, -24), (364, -24), (368, -34), (364, -46), (358, -44), (360, -34)]), W(6), (0, 0, 0), dark, bev=W(1)))
    A(side(poly([(306, -24), (316, -24), (318, -42), (308, -42)]), W(14), (0, 0, 0), dark, bev=W(1)))
    A(side(poly([(404, -24), (442, -24), (470, -120), (466, -130), (446, -134), (436, -124), (428, -90), (418, -60)]), W(30), (0, 0, 0), plum, bev=W(6), seg=3))
    for k in range(5): A(box((W(31), W(2), W(14)), (0, Y(-50 - k * 15), Z(431 + k * 4.2)), dark, rot=(0.29, 0, 0)))  # grip grooves
    A(side(poly([(504, -24), (528, -24), (528, 10), (504, 10)]), W(32), (0, 0, 0), dark, bev=W(2)))
    A(cyl(W(6), W(30), (-W(19), Y(-6), Z(516)), dark, axis='y', seg=10))
    # ---------------- the magazine: a hand of four ripe bananas fanned out of one crown in the magwell
    A(side(poly([(262, -22), (308, -22), (306, -34), (264, -34)]), W(34), (0, 0, 0), steel, bev=W(2)))  # magwell lip
    cz, ch = 286, -40
    A(cyl(W(13), W(34), (0, Y(ch + 4), Z(cz)), crown_m, axis='y', seg=12, bev=W(2)))  # the crown
    bd = lathe([(W(13.6), Y(ch - 6)), (W(13.6), Y(ch + 6))], (0, 0, Z(cz)), tape, seg=24, axis='y', cap=False)
    A(bd)
    def bez(p0, p1, p2, p3, t):
        return tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))
    n = 16
    # four fingers out of the crown, curving forward and UP round both sides of the handguard (bananas grow that way)
    for sx in (-1, 1):
        for k, (xs, lift) in enumerate(((10, 0), (24, 8))):
            c0 = (sx * xs * 0.4, ch - 6, cz - 4)
            c1 = (sx * (xs + 14), ch - 58 - lift * 0.5, cz - 34)
            c2 = (sx * (xs + 22), ch - 52 - lift, cz - 120)
            c3 = (sx * (xs + 24), ch + 12 - lift, cz - 176 + k * 8)
            path, radii = [], []
            for i in range(n + 1):
                u = i / n
                x, h, d = bez(c0, c1, c2, c3, u)
                path.append((W(x), Y(h), Z(d)))
                radii.append(W(8.5 + 9.5 * math.sin(min(1, u / 0.3) * math.pi / 2) - (0 if u < 0.72 else 11 * ((u - 0.72) / 0.28) ** 1.5)))
            A(sweep(path, radii, peel, seg=5, smooth_angle=30))
            A(ball(W(5.5), path[-1], brown, seg=8, rings=6))  # the black tip
            A(rod((W(sx * xs * 0.3), Y(ch - 2), Z(cz)), path[1], W(5.5), crown_m, seg=6))  # its stalk into the crown

    for p in parts: fixmats(p); uv_box(p, 0.03)
    apply_mods(bd)
    uvd = bd.data.uv_layers.active.data
    for pl in bd.data.polygons:  # the band's text runs round the crown, 'JANK' facing left (the side you see)
        ls = []
        for li in pl.loop_indices:
            v = bd.matrix_world @ bd.data.vertices[bd.data.loops[li].vertex_index].co
            gx, gy, gz = v.x, v.z, -v.y
            ang = math.atan2(gz - Z(cz), gx)  # round y, from +x toward +z (back)
            ls.append([li, (ang - math.radians(120)) / (2 * math.pi), (gy - Y(ch - 6)) / W(12)])
        ref = ls[0][1]
        for e in ls:
            while e[1] - ref > 0.5: e[1] -= 1
            while e[1] - ref < -0.5: e[1] += 1
        for li, u, w in ls: uvd[li].uv = (u, w)
    WZ = {'bb_steel': 'a', 'bb_plum': 'a', 'bb_optic': 'a', 'bb_dark': 'b', 'bb_peel': 'b', 'bb_brown': 'b', 'bb_crown': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'bunch_body', WZ, default='n', rule=None)
    meta = {'kind': 'weapon', 'id': 'banana', 'skin': 'banana_bunch', 'paint': ['bb_plum'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(DOT_H), 'z': Z(398)},
            'hatAt': [[0, Y(23), Z(440)], 0.1]}
    return finish('w_banana_bunch', bodies, meta)


main(build, 'w_banana_bunch')
