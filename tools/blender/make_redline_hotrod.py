# Hot Rod (Redline skin): the Redline's PPS-43-pattern carbine (make_redline.py: vented jacket with a slot
# compensator, tall hot-rod sights, curved 35-round mag, skeleton stock) x1.18, customised: deep candy-cherry paint
# with a yellow-orange-red flame job pinstriped in cyan, a chrome jacket, chrome stock and tach bezel, white pearl grip,
# a chrome trigger guard. Made fun: zoomie headers, three chrome exhaust pipes out of each side of the jacket, whose
# throats glow from the same HP-hot material as the barrel (so they redline with you), and fuzzy dice hanging off it.
# Hooks exactly as the Redline's: the tachometer needle node 'needle_wzN' (driven by HP) and the material
# 'redline_vents' (the game recolours it from your HP).
# run: blender -b --python tools/blender/make_redline_hotrod.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.18 / 1000
BORE_Y, MUZ_Z = 0.01, -0.47
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
SIGHT_H = 54
DIAL = (-W(27), Y(15), Z(356))


def tach_face(px):  # same dial as the Redline (the red zone matches the game's needle angles)
    h, w = px.shape[:2]; c = w / 2
    px_disc(px, c, c, c - 0.5, 0x0d0d10)
    px_disc(px, c, c, c - 6, 0xe8281e, r_in=c - 11, a0=1.2, a1=2.3)
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


def flames_px(px, base=0x5a0410, seed=5):
    """a classic flame job: a solid front that splits into licking tongues with the dark candy between them, each
    tongue yellow at its core, orange, red at its edge, a cyan pinstripe round it. u (columns) runs from the front (0)
    back, v (rows, top = up)"""
    h, w = px.shape[:2]
    r = np.random.default_rng(seed)
    px[:] = hexrgb(base)[None, None] * (0.85 + 0.25 * r.random((h, w, 1)))  # candy with metal flake
    yy, xx = np.mgrid[0:h, 0:w]
    X = (xx + 0.5) / w; Yv = 1 - (yy + 0.5) / h
    core = np.full((h, w), 9.0)  # distance to the nearest tongue's centre line, in its own half-widths
    for c, L, a, ph, H in ((0.2, 0.62, 0.07, 0.3, 0.1), (0.46, 0.92, 0.09, 1.9, 0.115), (0.72, 0.74, 0.08, 3.4, 0.1), (0.93, 0.42, 0.04, 2.6, 0.07)):
        t = np.clip(X / L, 0, 1)
        yc = c + a * np.sin(math.pi * 1.5 * t + ph) * t + 0.05 * t * t
        hw = H * (1 - t) ** 0.65 * (1 + 0.9 * np.clip(1 - X / 0.14, 0, 1))  # the tongues swell together at the front
        d = np.where(X < L, np.abs(Yv - yc) / np.maximum(hw, 1e-4), 9.0)
        core = np.minimum(core, d)
    inside = (core < 1.0) | (X < 0.045)
    k = np.clip(core, 0, 1)[:, :, None]
    fl = hexrgb(0xfff07a) * np.clip(1 - k * 2.2, 0, 1) + hexrgb(0xffb020) * np.clip(1 - np.abs(k * 2.2 - 1.1), 0, 1) + hexrgb(0xff3a10) * np.clip(k * 2.2 - 1.1, 0, 1)
    fl = fl * (1 - 0.35 * np.clip(X / 0.9, 0, 1))[:, :, None]  # cooler toward the tips
    edge = np.zeros_like(inside)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)): edge |= np.roll(np.roll(inside, dx, 1), dy, 0)
    edge &= ~inside
    px[inside] = fl[inside]
    px[edge] = hexrgb(0x4fd8ff)


def dice_px(px):  # one die face: white fluff with a black pip pattern (u 0..1 maps to six faces via uv_box)
    h, w = px.shape[:2]
    r = np.random.default_rng(9)
    px[:] = hexrgb(0xf4f4f0)[None, None] * (0.85 + 0.15 * r.random((h, w, 1)))
    for cx, cy in ((4, 4), (12, 12), (8, 8), (4, 12), (12, 4)):
        px_disc(px, cx, cy, 1.8, 0x111111)


def build():
    paint_t = tex_canvas('rh_flames_t', 112, 32, flames_px)
    paint = mat('rh_flames', 0xffffff, rough=0.24, clearcoat=0.6, tex=paint_t)
    candy = mat('rh_candy', 0xffffff, rough=0.24, clearcoat=0.6, tex=tex_noise('rh_candy_t', 0x5a0410, var=0.12, size=16, seed=73))
    chrome = mat('rh_chrome', 0xc8ccd4, rough=0.2, metal=1.0)
    dark = mat('rh_dark', 0x121316, rough=0.5, metal=0.45)
    steel = mat('rh_steel', 0x2a2c32, rough=0.38, metal=0.6)
    hot = mat('redline_vents', 0x401010, rough=0.4, emit=0xff2a10, strength=0.6)  # the game drives this colour from your HP
    def pearl_draw(px):
        h, w = px.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        n = np.sin(xx * 0.7 + np.sin(yy * 0.35) * 3) * 0.5 + 0.5
        px[:] = hexrgb(0xf2eee6) * (0.86 + 0.14 * n[:, :, None])
    pearl = mat('rh_pearl', 0xffffff, rough=0.12, clearcoat=1.0, tex=tex_canvas('rh_pearl_t', 32, 32, pearl_draw))
    black = mat('rh_black', 0x050505, rough=0.15, clearcoat=1.0)
    white = mat('rh_white', 0xf4f4f4, rough=0.2)
    face = mat('rh_tach', 0xffffff, rough=0.3, tex=tex_canvas('rh_tach_t', 64, 64, tach_face))
    needle_m = mat('rh_needle', 0xff2a2a, rough=0.3, emit=0xff2a2a, strength=2.5)
    dot = mat('rh_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    fuzz = mat('rh_dice', 0xffffff, rough=0.95, tex=tex_canvas('rh_dice_t', 16, 16, dice_px))
    string = mat('rh_string', 0xff2fa0, rough=0.8)
    parts, needle = [], []
    A = parts.append

    # ---------------- chrome barrel jacket (hollow, side + top vents, slot compensator), the hot barrel inside
    jk = side(poly([(0, -17), (282, -17), (282, 21), (8, 21), (0, 14)]), W(34), (0, 0, 0), chrome, bev=W(2))
    cut(jk, side(poly([(4, -14), (290, -14), (290, 18), (4, 18)]), W(28), (0, 0, 0), None))
    for k in range(6): cut(jk, box((W(60), W(13), W(26)), (0, Y(3), Z(48 + k * 37)), None, bev=W(4)))
    for k in range(5): cut(jk, box((W(14), W(30), W(18)), (0, Y(21), Z(66 + k * 37)), None, bev=W(3)))
    cut(jk, box((W(12), W(30), W(16)), (0, Y(21), Z(14)), None))
    cut(jk, cyl(W(6), W(20), (0, Y(0), Z(2)), None, axis='z', seg=12))
    A(jk)
    A(lathe([(W(8), Z(22)), (W(8), Z(300))], (0, BORE_Y, 0), hot, seg=14))
    A(lathe([(0, Z(22)), (W(4), Z(22)), (W(4), Z(26))], (0, BORE_Y, 0), black, seg=10))
    A(box((W(2), W(1.2), W(240)), (0, Y(21.4), Z(150)), mat('rh_pin', 0x4fd8ff, rough=0.3)))  # a cyan pinstripe down the top
    # front sight tower + ears + the glowing post
    A(side(poly([(18, 21), (48, 21), (44, 34), (39, 42), (27, 42), (22, 34)]), W(9), (0, 0, 0), chrome, bev=W(1.2)))
    for sx in (-1, 1): A(side(poly([(22, 22), (44, 22), (42, SIGHT_H + 5), (25, SIGHT_H + 5)]), W(2.6), (sx * W(7), 0, 0), chrome, bev=W(0.7)))
    A(box((W(3), W(SIGHT_H - 42), W(4)), (0, Y((SIGHT_H + 42) / 2), Z(33)), dark))
    A(box((W(3.4), W(3.4), W(3.4)), (0, Y(SIGHT_H), Z(33)), dot, bev=W(0.6)))
    # ---------------- zoomie headers: three chrome pipes out of each side, up and back, their throats HP-hot
    for sx in (-1, 1):
        for k in range(3):
            d0 = 214 + k * 22
            p0 = (sx * W(14), Y(2 - k * 1.5), Z(d0))
            p1 = (sx * W(30 + k * 2), Y(14 + k * 3), Z(d0 + 16))
            p2 = (sx * W(36 + k * 2), Y(30 + k * 2), Z(d0 + 40))
            A(sweep([p0, p1, p2], W(6.2), chrome, seg=12, name='header', cap=False))
            A(sweep([p1, p2], W(5.0), hot, seg=12, name='throat', cap=False))  # the inside, glowing
            d = Vector(p2) - Vector(p1); d.normalize()
            A(sweep([tuple(Vector(p2) - d * W(3)), tuple(Vector(p2) + d * W(2.5))], [W(7.0), W(7.6)], chrome, seg=12, name='headertip', cap=False))
            A(sweep([tuple(Vector(p2) - d * W(4)), tuple(Vector(p2) - d * W(3.6))], [W(5.0), W(0.3)], hot, seg=12, name='throatback'))
    # ---------------- receiver in candy paint with the flames, ejection port, cocking slot, 8-ball knob
    rcv = side(poly([(276, -22), (522, -22), (522, 14), (512, 24), (282, 24), (276, 18)]), W(34), (0, 0, 0), paint, bev=W(2.5))
    cut(rcv, box((W(12), W(15), W(40)), (W(17), Y(10), Z(338)), None))
    cut(rcv, box((W(12), W(5), W(110)), (W(17), Y(0), Z(392)), None))
    rcv.data.materials.append(candy)
    for f in rcv.data.polygons:
        if abs(f.normal.x) < 0.5: f.material_index = 1  # plain candy, except the flames on the sides (and the top, below)
    uv_planar(rcv, (0, Y(1), Z(399)), (W(250), W(48)), '-x')
    me = rcv.data; uvl = me.uv_layers.active.data
    for f in me.polygons:  # the flames run over the top too (like a hood), seen from above
        if f.normal.z > 0.5:
            f.material_index = 0
            for li in f.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                uvl[li].uv = ((-v.y - Z(276)) / (Z(522) - Z(276)), 0.5 + 0.9 * v.x / W(34))
    A(rcv)
    A(box((W(1.5), W(13), W(36)), (W(15.5), Y(10), Z(338)), dark))
    # rear sight: the tall aperture on its bridge
    A(box((W(24), W(6), W(36)), (0, Y(27), Z(488)), chrome, bev=W(1.5)))
    for sx in (-1, 1): A(side(poly([(474, 28), (502, 28), (498, SIGHT_H + 6), (480, SIGHT_H + 6)]), W(3), (sx * W(8.5), 0, 0), chrome, bev=W(0.8)))
    A(box((W(4), W(SIGHT_H - 6 - 30), W(4)), (0, Y((SIGHT_H - 6 + 30) / 2), Z(488)), dark))
    ap = cyl(W(6), W(3.5), (0, Y(SIGHT_H), Z(488)), dark, axis='z', seg=16)
    cut(ap, cyl(W(2.6), W(10), (0, Y(SIGHT_H), Z(488)), None, axis='z', seg=10))
    A(ap)
    A(cyl(W(5), W(5), (W(12.5), Y(36), Z(488)), chrome, axis='x', seg=12))
    A(rod((W(16), Y(0), Z(340)), (W(34), Y(2), Z(340)), W(4), chrome, seg=8))
    A(ball(W(11), (W(44), Y(3), Z(340)), black, seg=18, rings=12))
    A(cyl(W(5.5), W(1.2), (W(54.6), Y(3), Z(340)), white, axis='x', seg=14))
    A(box((W(0.8), W(5), W(2.5)), (W(55.3), Y(3), Z(340)), black))
    A(cyl(W(5), W(36), (-W(0), Y(12), Z(516)), chrome, axis='x', seg=12))
    # ---------------- magwell (candy), curved mag (satin black), paddle release (chrome)
    A(side(poly([(300, -22), (348, -22), (348, -52), (300, -52)]), W(32), (0, 0, 0), candy, bev=W(2)))
    A(side(poly([(350, -34), (362, -34), (364, -58), (352, -58)]), W(16), (0, 0, 0), chrome, bev=W(1)))
    front = [(304, -50), (300, -100), (291, -150), (277, -200), (262, -232)]
    back = [(344, -50), (340, -100), (331, -150), (317, -200), (302, -238)]
    A(side(poly(front + back[::-1]), W(26), (0, 0, 0), dark, bev=W(2)))
    A(side(poly([(258, -228), (306, -236), (304, -248), (255, -240)]), W(30), (0, 0, 0), chrome, bev=W(2.5)))
    # ---------------- chrome trigger guard, red safety, chrome trigger, white pearl grip with a chrome back strap
    A(side(poly([(360, -22), (368, -22), (370, -50), (420, -52), (428, -30), (436, -22), (440, -26), (432, -58), (366, -60), (360, -50)]), W(12), (0, 0, 0), chrome, bev=W(1.8)))
    A(box((W(10), W(8), W(8)), (0, Y(-27), Z(372)), candy, bev=W(1)))
    A(side(poly([(392, -22), (398, -22), (402, -34), (398, -46), (392, -44), (394, -34)]), W(6), (0, 0, 0), chrome, bev=W(1)))
    A(side(poly([(428, -22), (472, -22), (506, -128), (502, -140), (480, -146), (468, -136), (462, -110), (450, -80)]), W(32), (0, 0, 0), pearl, bev=W(6), seg=3))
    A(side(poly([(466, -22), (474, -22), (508, -130), (500, -132)]), W(18), (0, 0, 0), chrome, bev=W(1.5)))
    # ---------------- chrome skeleton stock + a candy butt plate
    A(side(poly([(516, 18), (812, 10), (812, -2), (516, 6)]), W(14), (0, 0, 0), chrome, bev=W(2)))
    A(side(poly([(515, -14), (811, -106), (807, -120), (511, -28)]), W(14), (0, 0, 0), chrome, bev=W(2)))
    A(side(poly([(800, 14), (822, 12), (826, -20), (824, -110), (816, -124), (800, -120), (804, -60)]), W(30), (0, 0, 0), candy, bev=W(3)))
    # ---------------- the tachometer (chrome bezel), bolted to the left side
    A(cyl(W(30), W(10), DIAL, chrome, axis='x', seg=24, bev=W(1.5)))
    A(cyl(W(26), W(10.6), DIAL, dark, axis='x', seg=24))
    fc = cyl(W(25.5), W(1), (DIAL[0] - W(5.2), DIAL[1], DIAL[2]), face, axis='x', seg=24)
    A(fc)
    for dd in (-18, 18):
        A(cyl(W(3), W(6), (DIAL[0] + W(8), DIAL[1] + W(dd) * 0.7, DIAL[2] + W(dd)), chrome, axis='x', seg=8))
    needle.append(box((W(2), W(21), W(2.6)), (DIAL[0] - W(6.4), DIAL[1] + W(9), DIAL[2]), needle_m))
    needle.append(cyl(W(3.4), W(2.4), (DIAL[0] - W(6.4), DIAL[1], DIAL[2]), black, axis='x', seg=12))
    # ---------------- fuzzy dice on a pink string, hanging off a loop under the jacket (left)
    A(tube([(-W(16), Y(-14), Z(150)), (-W(20), Y(-18), Z(152)), (-W(16), Y(-22), Z(154))], W(1.6), chrome, seg=6, name='loop'))
    A(tube([(-W(20), Y(-19), Z(152)), (-W(21), Y(-40), Z(150)), (-W(22), Y(-58), Z(146))], W(0.8), string, seg=4, name='string'))
    A(tube([(-W(20), Y(-19), Z(152)), (-W(19), Y(-36), Z(160)), (-W(17), Y(-48), Z(170))], W(0.8), string, seg=4, name='string2'))
    for (pos, rot) in (((-W(22), Y(-70), Z(146)), (0.3, 0.5, 0.2)), ((-W(17), Y(-60), Z(172)), (-0.2, 0.9, -0.3))):
        dc = box((W(20), W(20), W(20)), pos, fuzz, bev=W(4), seg=2, rot=rot, name='die')
        A(jitter(dc, W(0.9), int(pos[2] * 1000) % 97))

    for p in parts + needle:
        if p.data.materials and p.data.materials[0].name != 'rh_flames': uv_box(p, 0.03)
    for p in parts:
        if p.name.startswith('die'): uv_box(p, W(20))
    apply_mods(fc); uv_planar(fc, (DIAL[0], DIAL[1], DIAL[2]), W(51), '-x')
    WZ = {'rh_flames': 'a', 'rh_candy': 'a', 'rh_pearl': 'a', 'rh_chrome': 'b', 'rh_dark': 'b', 'redline_vents': 'b', 'rh_black': 'b',
          'rh_dice': 'n', 'rh_string': 'n', 'rh_pin': 'n'}
    bodies = zone_join(parts, 'hotrod_body', WZ, default='n', rule=lambda m, c: 'a' if m == 'rh_chrome' and c[2] > Z(500) else None)  # the stock rides with the body
    nd = part(needle, 'needle_wzN', pivot=DIAL)
    meta = {'kind': 'weapon', 'id': 'redline', 'skin': 'redline_hotrod', 'paint': ['rh_candy'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SIGHT_H), 'z': Z(488)},
            'hatAt': [[0, Y(24), Z(440)], 0.1], 'needle': 'needle_wzN', 'vents': 'redline_vents'}
    return finish('w_redline_hotrod', bodies + [nd], meta)


main(build, 'w_redline_hotrod')
