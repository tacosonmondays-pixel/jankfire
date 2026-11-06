# Revolver: a 6in double-action .357 (full underlug, vent rib, ramp front sight, adjustable rear, six-shot fluted
# cylinder, spur hammer, finger-groove target grips), real millimetres scaled x1.5 so the trigger guard sits on the
# game's twirl pivot (0, -0.02, 0.02). Made fun: mirror chrome, gold hammer + trigger + screws, bubblegum pearl
# grips with a gold J medallion, copper bullet noses showing in the chambers.
# 'cylinder' and 'hammer' are their own nodes so the game can spin and cock them.
# run: blender -b --python tools/blender/make_revolver.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.5 / 1000
BORE_Y, MUZ_Z = 0.03, -0.29
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
CYL_H = -14  # the cylinder turns round an axis under the bore: the top chamber lines up with the barrel


def build():
    chrome = mat('rv_chrome', 0xc4cad4, rough=0.2, metal=1.0)
    satin = mat('rv_satin', 0xa8aeb8, rough=0.32, metal=1.0)
    dark = mat('rv_dark', 0x18191d, rough=0.45, metal=0.4)
    gold = mat('rv_gold', 0xffc83a, rough=0.18, metal=1.0)
    copper = mat('rv_copper', 0xd0703a, rough=0.25, metal=1.0)
    def pearl_draw(px):
        h, w = px.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        n = np.sin(xx * 0.7 + np.sin(yy * 0.35) * 3) * 0.5 + 0.5
        n2 = np.sin(yy * 0.45 + np.cos(xx * 0.3) * 2.5) * 0.5 + 0.5
        px[:] = hexrgb(0xff8ad0) * (0.82 + 0.18 * n[:, :, None]) + hexrgb(0xffffff) * (0.12 * n2[:, :, None])
    pearl = mat('rv_pearl', 0xff8ad0, rough=0.12, clearcoat=1.0, tex=tex_canvas('rv_pearl_t', 32, 32, pearl_draw))
    orange = mat('rv_insert', 0xff5a1a, rough=0.3, emit=0xff5a1a, strength=2.5)
    black = mat('rv_black', 0x050505, rough=0.3)
    parts, cylp, ham = [], [], []
    A = parts.append

    # ---------------- barrel with full underlug, vent rib, ramp front sight, ejector shroud
    br = side(poly([(0, 9), (150, 9), (150, -9), (0, -9)]), W(18), (0, 0, 0), chrome, bev=W(4), seg=3)
    A(br)
    A(side(poly([(2, -6), (150, -6), (150, -28), (16, -28), (4, -24)]), W(16), (0, 0, 0), chrome, bev=W(3.5), seg=3))  # underlug + ejector shroud
    A(lathe([(0, Z(-0.5)), (W(4.6), Z(-0.5)), (W(4.6), Z(8))], (0, BORE_Y, 0), black, seg=12))
    rib = side(poly([(4, 8), (150, 8), (150, 15), (4, 15)]), W(9), (0, 0, 0), chrome, bev=W(1.5),
               holes=[poly([(30 + k * 20, 9.5), (42 + k * 20, 9.5), (42 + k * 20, 13.5), (30 + k * 20, 13.5)]) for k in range(6)])
    A(rib)
    A(side(poly([(4, 14), (28, 14), (12, 33), (6, 33)]), W(4), (0, 0, 0), chrome, bev=W(0.8)))  # front ramp
    A(box((W(4.4), W(5), W(4.5)), (0, Y(33.5), Z(8.5)), orange, bev=W(0.6)))  # orange insert, its top is the sight line
    for d in (60, 120):
        A(cyl(W(2), W(18), (0, Y(-20), Z(d)), gold, axis='x', seg=8))  # lug pins, gold because why not

    # ---------------- frame: window round the cylinder, top strap, recoil shield, hammer housing, grip frame
    fr = side(poly([(146, 15), (150, 22), (205, 22), (222, 20), (238, 14), (246, -2), (250, -34), (240, -52), (214, -46), (206, -38), (146, -38)]), W(26), (0, 0, 0), chrome, bev=W(2.5),
              holes=[poly([(154, 9), (196, 9), (196, -36), (154, -36)])])
    A(fr)
    A(box((W(28), W(9), W(48)), (0, Y(-38), Z(176)), chrome, bev=W(2.5)))  # bottom of the window (crane)
    A(side(poly([(200, 28), (222, 28), (222, 22), (200, 22)]), W(16), (0, 0, 0), dark, bev=W(1)))  # rear sight body
    for sx in (-1, 1):
        A(box((W(5.5), W(14), W(9)), (sx * W(5.2), Y(34), Z(212)), dark, bev=W(0.6)))  # notch ears
    A(box((W(3), W(3), W(3)), (W(9), Y(28), Z(205)), gold))  # windage screw
    A(side(poly([(198, -2), (212, -2), (212, 8), (198, 8)]), W(5), (-W(14.5), 0, 0), satin, bev=W(1.2)))  # cylinder release latch (left)
    for d, h in ((180, -28), (226, -10), (232, -40)):
        A(cyl(W(3), W(2), (-W(13.6), Y(h), Z(d)), gold, axis='x', seg=10))
        A(cyl(W(3), W(2), (W(13.6), Y(h), Z(d)), gold, axis='x', seg=10))

    # ---------------- trigger guard + trigger (gold), grip frame, pearl finger-groove grips + medallion
    A(side(poly([(196, -38), (204, -38), (204, -58), (228, -62), (238, -48), (244, -50), (234, -70), (200, -68), (192, -56)]), W(10), (0, 0, 0), chrome, bev=W(2)))
    A(side(poly([(208, -38), (214, -38), (218, -46), (214, -58), (209, -56), (211, -46)]), W(7), (0, 0, 0), gold, bev=W(1.2)))
    grip = side(poly([(226, -44), (248, -36), (258, -40), (296, -128), (296, -146), (282, -156), (248, -154), (240, -140), (244, -128), (236, -118), (238, -104), (230, -94), (232, -80), (226, -70)]), W(36), (0, 0, 0), pearl, bev=W(8), seg=3)
    A(grip)
    for sx in (-1, 1):
        A(cyl(W(5.5), W(2), (sx * W(17.6), Y(-96), Z(262)), gold, axis='x', seg=14))
        A(box((W(1.5), W(5), W(1.6)), (sx * W(18.7), Y(-96), Z(262)), black))  # a tiny J (well, a bar)

    # ---------------- cylinder: six chambers, flutes, ratchet star, copper noses peeking out the front
    cyl_axis_y = Y(CYL_H)
    c = cyl(W(20), W(41), (0, cyl_axis_y, Z(174)), satin, axis='z', seg=36, bev=W(2.5))
    for k in range(6):
        a = math.pi / 2 + k * math.pi / 3
        fl = cyl(W(5), W(26), (math.cos(a + math.pi / 6) * W(22.5), cyl_axis_y + math.sin(a + math.pi / 6) * W(22.5), Z(178)), None, axis='z', seg=12)
        cut(c, fl)
    for k in range(6):
        a = math.pi / 2 + k * math.pi / 3
        x, y = math.cos(a) * W(14), cyl_axis_y + math.sin(a) * W(14)
        cut(c, cyl(W(5.2), W(12), (x, y, Z(156)), None, axis='z', seg=12))
        cylp.append(cyl(W(4.6), W(10), (x, y, Z(161)), copper, axis='z', seg=10, r2=W(2.6)))
    cylp.insert(0, c)
    cylp.append(cyl(W(6), W(6), (0, cyl_axis_y, Z(196)), dark, axis='z', seg=6))  # ratchet
    cylp.append(cyl(W(3.2), W(56), (0, cyl_axis_y, Z(124)), satin, axis='z', seg=10))  # ejector rod
    cylp.append(cyl(W(4.4), W(5), (0, cyl_axis_y, Z(98)), satin, axis='z', seg=12, bev=W(1)))

    # ---------------- hammer: gold spur, its own node, pivot low in the frame
    ham.append(side(poly([(222, 2), (234, 2), (240, 12), (251, 19), (259, 23), (258, 29), (246, 28), (232, 25), (222, 21)]), W(8), (0, 0, 0), gold, bev=W(1.4)))
    for k in range(4):
        ham.append(box((W(9), W(1.2), W(2.5)), (0, Y(28.6 - k * 0.8), Z(246 + k * 3.2)), dark))

    for p in parts + cylp + ham:
        uv_box(p, 0.02)
    WZ = {'rv_pearl': 'a', 'rv_chrome': 'a', 'rv_satin': 'b', 'rv_dark': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'rv_body', WZ, default='n', rule=lambda m, c: 'b' if m == 'rv_chrome' and c[2] < Z(146) else None)  # frame + grip vs barrel + cylinder, like the code model
    cnode = part(cylp, 'cylinder_wzB', pivot=(0, cyl_axis_y, Z(174)))
    hnode = part(ham, 'hammer_wzN', pivot=(0, Y(2), Z(228)))
    meta = {'kind': 'weapon', 'id': 'revolver', 'paint': ['rv_pearl'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(35.5), 'z': Z(212) + 0.14},
            'hatAt': [[0, Y(24), Z(178)], 0.08], 'cylinder': {'node': 'cylinder_wzB', 'step': math.pi / 3}, 'hammer': {'node': 'hammer_wzN'}}
    return finish('w_revolver', bodies + [cnode, hnode], meta)


main(build, 'w_revolver')
