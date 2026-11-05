# Marble Shotgun: an 18th-century flintlock blunderbuss pistol (brass barrel with a trumpet bell, octagonal breech,
# walnut full stock with a bird's-head butt and brass butt cap, flintlock with cock, flint, frizzen and pan, brass
# trigger guard + side plate, ramrod in brass pipes), real millimetres x1.1 to the game's Marble Shotgun.
# Made fun: it's fed from an upside-down aqua mason jar of marbles screwed into a brass funnel on the breech, with a
# label that says what it is, and a brass plaque on the butt.
# run: blender -b --python tools/blender/make_marbles.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.1 / 1000
BORE_Y, MUZ_Z = 0.012, -0.37
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
JAR_D = 200
MARBLE_COLS = [0x2f7bff, 0x19c37d, 0xff4f4f, 0xffd23b, 0xb07dff, 0xff8a1a, 0x37d6ff]


def build():
    brass = mat('mb_brass', 0xc8a050, rough=0.22, metal=1.0)
    walnut = mat('mb_walnut', 0x6b3a1a, rough=0.35, clearcoat=0.4, tex=tex_wood('mb_walnut_t', 0x7a4420, 0x3a1a08, size=64, seed=131, rings=6))
    steel = mat('mb_steel', 0x6a6e76, rough=0.32, metal=0.85)
    dark = mat('mb_dark', 0x2a2a2e, rough=0.5, metal=0.4)
    black = mat('mb_black', 0x050505, rough=0.4)
    flint = mat('mb_flint', 0x3a3a3c, rough=0.7)
    leather = mat('mb_leather', 0x5a3a20, rough=0.8)
    rodw = mat('mb_ramrod', 0xb8864a, rough=0.5)
    zinc = mat('mb_zinc', 0xb8bcc4, rough=0.3, metal=0.9)
    glass = mat('mb_jar', 0x7fd0ff, rough=0.05, alpha=0.32)
    def lbl(px):
        px[:] = hexrgb(0xf2e6c8); px[:1] = px[-1:] = hexrgb(0x8a1a1a)
        text_px(px, 'MARBLES', 4, 3, 1, 0x8a1a1a); text_px(px, 'DO NOT EAT', 2, 12, 1, 0x111111)
    label = mat('mb_label', 0xffffff, rough=0.6, tex=tex_canvas('mb_label_t', 64, 21, lbl))
    def plq(px):
        px[:] = hexrgb(0xc8a050); px[:1] = px[-1:] = hexrgb(0x6a5020)
        text_px(px, 'LOST MY', 6, 3, 1, 0x3a2a10); text_px(px, 'MARBLES', 6, 12, 1, 0x3a2a10)
    plaque = mat('mb_plaque', 0xffffff, rough=0.25, metal=0.6, tex=tex_canvas('mb_plaque_t', 54, 21, plq))
    parts = []; A = parts.append

    # ---------------- brass barrel: trumpet bell (hollow), ring mouldings, octagonal breech, deep dark bore
    A(lathe([(W(10.5), Z(42)), (W(20), Z(9)), (W(27), Z(1)), (W(29), Z(0)), (W(31), Z(2.5)), (W(27.5), Z(8)), (W(19), Z(20)), (W(19.5), Z(21)), (W(19.5), Z(24)),
             (W(17), Z(25)), (W(12.5), Z(95)), (W(14), Z(96)), (W(14), Z(99)), (W(13), Z(100)), (W(13), Z(140)), (W(15), Z(141)), (W(15), Z(146)), (W(14), Z(147))],
            (0, BORE_Y, 0), brass, seg=24, cap=False))
    A(lathe([(0, Z(40)), (W(10.6), Z(40)), (W(10.6), Z(30))], (0, BORE_Y, 0), black, seg=14))
    A(lathe([(W(14), Z(146)), (W(14), Z(226))], (0, BORE_Y, 0), brass, seg=8, rot=(0, 0, math.pi / 8)))
    A(lathe([(W(15.5), Z(200)), (W(15.5), Z(206))], (0, BORE_Y, 0), brass, seg=8, rot=(0, 0, math.pi / 8)))
    A(box((W(10), W(3), W(46)), (0, Y(14.5), Z(248)), steel, bev=W(1)))  # breech tang
    # ---------------- walnut full stock: forestock under the barrel, wrist, bird's-head butt; brass butt cap
    A(side(poly([(52, 2), (226, 2), (226, -26), (64, -24), (52, -16)]), W(28), (0, 0, 0), walnut, bev=W(4), seg=2))
    A(side(poly([(222, 12), (300, 15), (332, 10), (352, -8), (392, -40), (430, -92), (437, -110), (426, -124), (402, -128), (386, -116), (372, -88), (346, -52), (318, -34), (226, -30)]),
           W(30), (0, 0, 0), walnut, bev=W(7), seg=3))
    A(side(poly([(418, -104), (439, -108), (433, -128), (404, -135), (390, -126), (400, -121), (424, -119)]), W(33), (0, 0, 0), brass, bev=W(3)))
    A(cyl(W(11), W(1.2), (-W(15.4), Y(-92), Z(398)), plaque, axis='x', seg=20))
    plq_o = parts[-1]; plq_o.scale = (1, 1.5, 1)
    # ---------------- ramrod in two brass pipes
    A(rod((0, Y(-29), Z(64)), (0, Y(-29), Z(226)), W(3.4), rodw, seg=8))
    A(cyl(W(4.2), W(9), (0, Y(-29), Z(60)), brass, axis='z', seg=10))
    for d in (95, 175): A(lathe([(W(5.6), Z(d - 6)), (W(5.6), Z(d + 6))], (0, Y(-29), 0), brass, seg=12))
    # ---------------- flintlock (right side): lock plate, cock with jaws + flint, frizzen, pan, spring; side plate (left)
    A(side(poly([(232, 0), (260, 6), (318, 4), (332, -4), (318, -14), (262, -16), (236, -10)]), W(4), (W(16), 0, 0), steel, bev=W(1)))
    A(side(poly([(300, -6), (310, -2), (306, 10), (296, 22), (292, 32), (282, 36), (272, 33), (276, 26), (286, 22), (294, 10), (296, 0)]), W(6), (W(19), 0, 0), steel, bev=W(1.2)))
    A(box((W(6), W(4), W(11)), (W(19), Y(24.5), Z(276)), leather))
    A(box((W(5), W(8), W(10)), (W(19), Y(29.5), Z(271)), flint, rot=(0.15, 0, 0)))
    A(cyl(W(2.6), W(12), (W(19), Y(40), Z(283)), steel, axis='y', seg=8))
    A(side(poly([(250, 6), (262, 6), (262, 32), (257, 34), (250, 30)]), W(10), (W(18), 0, 0), steel, bev=W(1)))
    A(box((W(10), W(4), W(18)), (W(18.5), Y(4), Z(250)), brass, bev=W(1)))
    A(side(poly([(222, -2), (250, -6), (250, -2), (226, 2)]), W(3), (W(17.5), 0, 0), steel, bev=W(0.6)))
    A(side(poly([(240, -6), (262, -2), (290, -8), (318, -4), (332, -10), (316, -16), (290, -14), (262, -12), (244, -12)]), W(2), (-W(15.6), 0, 0), brass, bev=W(0.6)))
    for d in (262, 310): A(cyl(W(3), W(1.5), (-W(16.4), Y(-8), Z(d)), steel, axis='x', seg=10))
    # ---------------- trigger guard (brass, with the finger hole) + trigger
    A(side(poly([(296, -26), (356, -28), (368, -36), (360, -58), (318, -62), (298, -46)]), W(8), (0, 0, 0), brass, bev=W(1.5),
           holes=[poly([(312, -31), (348, -33), (352, -47), (322, -52), (310, -42)])]))
    A(side(poly([(330, -30), (336, -30), (340, -40), (336, -50), (330, -48), (332, -40)]), W(5), (0, 0, 0), steel, bev=W(1)))
    # ---------------- the hopper: brass funnel, zinc screw band, upside-down aqua mason jar, label, marbles
    A(lathe([(W(9), Y(12)), (W(9), Y(22)), (W(26), Y(40)), (W(31), Y(44))], (0, 0, Z(JAR_D)), brass, seg=24, axis='y', cap=False))
    A(lathe([(W(35), Y(42)), (W(35.5), Y(45)), (W(35), Y(48)), (W(35.5), Y(51)), (W(35), Y(55))], (0, 0, Z(JAR_D)), zinc, seg=28, axis='y'))
    A(lathe([(W(30), Y(54)), (W(31), Y(58)), (W(36), Y(70)), (W(37), Y(76)), (W(37), Y(132)), (W(34), Y(138)), (W(22), Y(141)), (0, Y(141.5))], (0, 0, Z(JAR_D)), glass, seg=28, axis='y'))
    lb = box((W(1), W(21), W(40)), (-W(37.6), Y(100), Z(JAR_D)), label, rot=(0, math.pi, 0)); A(lb)
    rng = random.Random(9)
    pts = []
    while len(pts) < 16:
        x, z = rng.uniform(-24, 24), rng.uniform(-24, 24)
        if x * x + z * z > 26 * 26: continue
        y = 64 + 12 * (len(pts) // 6) + rng.uniform(-3, 3)
        if any((x - a) ** 2 + (y - b) ** 2 + (z - c) ** 2 < 15 ** 2 for a, b, c in pts): continue
        pts.append((x, y, z))
    pts += [(0, 30, 0), (5, 38, -6)]  # a couple already on their way down the funnel
    for i, (x, y, z) in enumerate(pts):
        A(ball(W(8), (W(x), Y(y), Z(JAR_D) + W(z)), mat(f'mb_marble{i % len(MARBLE_COLS)}', MARBLE_COLS[i % len(MARBLE_COLS)], rough=0.05, clearcoat=1.0), seg=12, rings=8))

    for p in parts: uv_box(p, 0.03)
    apply_mods(lb); c = lb.matrix_world.translation; uv_planar(lb, (c.x, c.z, -c.y), (W(40), W(21)), '-x')
    for o in bpy.context.view_layer.objects.selected: o.select_set(False)
    bpy.context.view_layer.objects.active = plq_o; plq_o.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    uv_planar(plq_o, (-W(15.4), Y(-92), Z(398)), (W(33), W(22)), '-x')
    body = join(parts, 'marbles_body')
    meta = {'kind': 'weapon', 'id': 'marbles', 'paint': ['mb_jar'], 'muzzle': [0, BORE_Y, MUZ_Z], 'hatAt': [[0, Y(141), Z(JAR_D)], 0.07]}
    return finish('w_marbles', [body], meta)


main(build, 'w_marbles')
