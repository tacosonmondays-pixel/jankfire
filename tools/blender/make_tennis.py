# Tennis Ball Launcher: a garage-built pneumatic ball launcher, real millimetres x1.1. The barrel is a clear 3-ball
# can (PET tube, white snap lid with the middle cut out, the aluminium ring end where it meets the breech), three balls
# loaded in it. A grey 2in PVC tee is the breech, with a second can standing in its branch as the hopper. A 12 oz
# paintball CO2 bottle on hose clamps is the foregrip, a brass ball valve with a red lever is the trigger action, and the
# grip is a real tennis racket: the handle (octagonal, white overgrip, butt cap) as the pistol grip and its throat
# wrapped round the breech, with a cut-off piece of the head and its strings as the trigger guard.
# Made fun: a pink terry sweatband round the can, a line-judge yellow rear sight, and a can label in the game's voice.
# run: blender -b --python tools/blender/make_tennis.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.1 / 1000
BORE_Y, MUZ_Z = 0.03, -0.545
def Z(u): return MUZ_Z + u * S   # u: mm back from the muzzle
def Y(h): return BORE_Y + h * S  # h: mm up from the bore line
def W(mm): return mm * S
SIGHT_H = 104  # mm above the bore: the sight line over the rear notch + front bead


def fuzz_tex(px):
    h, w = px.shape[:2]
    rng = np.random.default_rng(7)
    base = hexrgb(0xd4ff3a)
    px[:] = base * (0.9 + 0.12 * rng.random((h, w, 1)))
    yy, xx = np.mgrid[0:h, 0:w] / w
    seam = np.abs(np.sin(xx * math.pi * 2) * 0.25 + 0.5 - yy) < 0.035  # one wavy seam line round the ball
    px[seam] = hexrgb(0xf4f4ea)


def build():
    pet = mat('tb_can', 0xdff4e8, rough=0.04, alpha=0.28)
    lid = mat('tb_lid', 0xf4f4f0, rough=0.35, clearcoat=0.4)
    alu = mat('tb_alu', 0xc0c6ce, rough=0.25, metal=0.95)
    felt = mat('tb_ball', 0xd4ff3a, rough=0.9, tex=tex_canvas('tb_ball_t', 32, 32, fuzz_tex))
    pvc = mat('tb_pvc', 0x6e737a, rough=0.45, tex=tex_noise('tb_pvc_t', 0x6e737a, var=0.07, size=32, speck=0x6a6e74, speck_p=0.04, seed=501))
    co2 = mat('tb_co2', 0x2a6aff, rough=0.2, metal=0.6, clearcoat=0.8)
    ano = mat('tb_ano', 0xff4fd8, rough=0.25, metal=0.7)
    clamp_m = mat('tb_clamp', 0xb8bec6, rough=0.3, metal=0.9)
    brass = mat('tb_brass', 0xe0ad3c, rough=0.22, metal=1.0)
    red = mat('tb_lever', 0xe0202a, rough=0.3, clearcoat=0.7)
    frame = mat('tb_frame', 0xd4ff3a, rough=0.15, clearcoat=1.0)  # the racket's paint (the gun's colour)
    frame_k = mat('tb_frame_k', 0x16161a, rough=0.3, clearcoat=0.8)
    strings = mat('tb_strings', 0xf4f4f0, rough=0.4)
    overgrip = mat('tb_overgrip', 0xf6f4ec, rough=0.7, tex=tex_stripes('tb_overgrip_t', 0xf8f6ee, 0xd6d2c6, size=16, width=3, diag=True))
    cap_k = mat('tb_butt', 0x16161a, rough=0.4)
    terry = mat('tb_terry', 0xff4fd8, rough=0.95, tex=tex_stripes('tb_terry_t', 0xff4fd8, 0xffffff, size=16, width=4, diag=False))
    yellow = mat('tb_line', 0xffe14d, rough=0.3, clearcoat=0.6)
    bead = mat('tb_bead', 0x7dff4f, rough=0.2, emit=0x7dff4f, strength=1.2)
    def lbl(px):
        px[:] = hexrgb(0x16161a); px[2:-2, 2:-2] = hexrgb(0xd4ff3a)
        text_px(px, 'FUZZ AND CO', 4, 3, 1, 0x16161a); text_px(px, 'EXTRA DUTY', 4, 12, 1, 0xff00dc); text_px(px, '3 BALLS 0 RULES', 4, 21, 1, 0x16161a)
    label = mat('tb_label', 0xffffff, rough=0.3, tex=tex_canvas('tb_label_t', 96, 31, lbl))
    parts, decals = [], []
    A = parts.append

    # ---------------- barrel: the clear can, its lid (mouth cut out), the ring end, three balls inside
    A(lathe([(W(35), Z(14)), (W(36.5), Z(14)), (W(36.5), Z(244)), (W(35), Z(244))], (0, BORE_Y, 0), pet, seg=28))
    A(lathe([(W(32), Z(-1)), (W(38.5), Z(-1)), (W(39.5), Z(2)), (W(39.5), Z(16)), (W(37), Z(18)), (W(36.6), Z(18)), (W(36.6), Z(3)), (W(32), Z(3))], (0, BORE_Y, 0), lid, seg=28))
    A(lathe([(W(36), Z(242)), (W(38.5), Z(243)), (W(38.5), Z(252)), (W(36), Z(254))], (0, BORE_Y, 0), alu, seg=28))
    for u in (52, 120, 188):
        A(ball(W(33), (0, BORE_Y, Z(u)), felt, seg=18, rings=12, rot=(u * 0.05, u * 0.11, 0)))
    # sweatband round the can near the muzzle
    A(lathe([(W(37), Z(30)), (W(42), Z(31)), (W(43), Z(40)), (W(42), Z(49)), (W(37), Z(50))], (0, BORE_Y, 0), terry, seg=28))
    lb = box((0.0008, W(34), W(100)), (W(-37.2), BORE_Y, Z(150)), label, rot=(0, math.pi, 0)); A(lb); decals.append((lb, (W(100), W(34)), '-x'))
    lb2 = box((0.0008, W(34), W(100)), (W(37.2), BORE_Y, Z(150)), label); A(lb2); decals.append((lb2, (W(100), W(34)), 'x'))
    # ---------------- breech: grey 2in PVC tee, the hopper can in its branch (two balls), reducer + brass ball valve
    A(lathe([(W(30), Z(250)), (W(43), Z(252)), (W(43), Z(338)), (W(30), Z(340))], (0, BORE_Y, 0), pvc, seg=28))
    A(lathe([(W(30), Z(338)), (W(30), Z(352)), (W(16), Z(366)), (W(16), Z(372))], (0, BORE_Y, 0), pvc, seg=24))
    hz, HT = Z(296), 0.95  # the hopper feeds from the left side, leaning out so it's off the sight line
    hx = lambda h: (-math.sin(HT) * W(h), BORE_Y + math.cos(HT) * W(h))
    A(lathe([(W(41), W(30)), (W(41), W(84))], (0, BORE_Y, hz), pvc, seg=28, axis='y', rot=(0, 0, HT)))  # the tee's branch socket
    A(lathe([(W(35), W(80)), (W(36.5), W(80)), (W(36.5), W(210)), (W(35), W(210))], (0, BORE_Y, hz), pet, seg=28, axis='y', rot=(0, 0, HT)))
    for hh in (112, 178): A(ball(W(33), (hx(hh)[0], hx(hh)[1], hz), felt, seg=18, rings=12, rot=(hh * 0.07, 0, hh * 0.13)))
    A(lathe([(W(30), W(206)), (W(38.5), W(206)), (W(39.5), W(209)), (W(39.5), W(222)), (W(0), W(224))], (0, BORE_Y, hz), lid, seg=28, axis='y', rot=(0, 0, HT)))
    A(box((W(34), W(22), W(30)), (0, BORE_Y, Z(392)), brass, bev=0.002))  # ball valve body
    A(cyl(W(15), W(14), (0, BORE_Y, Z(374)), brass, axis='z', seg=6))
    A(cyl(W(15), W(14), (0, BORE_Y, Z(410)), brass, axis='z', seg=6))
    A(cyl(W(6), W(14), (0, Y(16), Z(392)), brass, axis='y', seg=10))  # valve stem
    A(side([(Z(386), Y(26)), (Z(398), Y(26)), (Z(420), Y(-40)), (Z(410), Y(-44))], W(9), (0, 0, 0), red, bev=0.0015))  # the lever, down to the trigger
    # ---------------- CO2 bottle under the can (the foregrip), anodised adapter, hose clamps
    cy = Y(-70)
    A(lathe([(0, Z(70)), (W(18), Z(72)), (W(25), Z(84)), (W(26), Z(100)), (W(26), Z(282)), (W(14), Z(290))], (0, cy, 0), co2, seg=24))
    A(lathe([(W(14), Z(288)), (W(15), Z(290)), (W(15), Z(318)), (W(10), Z(322))], (0, cy, 0), ano, seg=16))
    A(rod((0, cy, Z(320)), (0, Y(-30), Z(334)), W(6), ano, seg=10))  # up into the reducer
    for u in (110, 230):  # hose clamps: one band round the can, one round the bottle, a screw housing
        A(lathe([(W(37.6), Z(u - 6)), (W(37.6), Z(u + 6))], (0, BORE_Y, 0), clamp_m, seg=28))
        A(lathe([(W(26.6), Z(u - 6)), (W(26.6), Z(u + 6))], (0, cy, 0), clamp_m, seg=24))
        for sx in (-1, 1): A(box((W(3), W(36), W(12)), (sx * W(22), Y(-36), Z(u)), clamp_m, rot=(0, 0, sx * 0.35)))
        A(box((W(12), W(10), W(16)), (W(30), Y(-58), Z(u)), clamp_m, bev=0.001))
    def co2l(px):
        px[:] = hexrgb(0xf4f4f0); text_px(px, 'CO2 12OZ', 3, 3, 1, 0x2a6aff)
    cl = mat('tb_co2label', 0xffffff, rough=0.35, tex=tex_canvas('tb_co2l_t', 52, 11, co2l))
    c2 = box((0.0008, W(13), W(60)), (W(-26.2), cy, Z(190)), cl, rot=(0, math.pi, 0)); A(c2); decals.append((c2, (W(60), W(13)), '-x'))
    # ---------------- the racket: handle (pistol grip), throat round the breech, a piece of the head as the trigger guard
    top = (Z(452), Y(-46)); bot = (Z(492), Y(-210))
    gdir = Vector((0, bot[1] - top[1], bot[0] - top[0])).normalized()
    g = cyl(W(15.5), W(172), (0, (top[1] + bot[1]) / 2, (top[0] + bot[0]) / 2), frame_k, axis='y', seg=8, rot=(-math.atan2(bot[0] - top[0], top[1] - bot[1]), 0, 0))
    A(g)
    og = cyl(W(17), W(140), (0, (top[1] + bot[1]) / 2 - W(10) * gdir.y, (top[0] + bot[0]) / 2 - W(10) * gdir.z), overgrip, axis='y', seg=8, rot=(-math.atan2(bot[0] - top[0], top[1] - bot[1]), 0, 0))
    A(og)
    A(cyl(W(19), W(12), (0, bot[1] - W(2), bot[0] + W(1)), cap_k, axis='y', seg=8, rot=(-math.atan2(bot[0] - top[0], top[1] - bot[1]), 0, 0), bev=0.001))
    A(cyl(W(9), W(13), (0, bot[1] - W(3), bot[0] + W(1)), ano, axis='y', seg=8, rot=(-math.atan2(bot[0] - top[0], top[1] - bot[1]), 0, 0)))  # logo plug
    # the throat: two oval beams from the top of the handle spreading forward round the tee
    for sx in (-1, 1):
        A(sweep([(0, top[1] + W(4), top[0] - W(4)), (sx * W(14), Y(-40), Z(430)), (sx * W(34), Y(-34), Z(380)), (sx * W(44), Y(-4), Z(336)), (sx * W(44), Y(10), Z(300))],
                [W(9), W(9.5), W(10), W(9.5), W(9)], frame, seg=10, squash=(1.0, 0.7)))
    A(sweep([(0, top[1] + W(8), top[0]), (0, top[1] - W(4), top[0] + W(8))], [W(16), W(16)], frame_k, seg=10))  # the throat's yoke
    # the head offcut under the breech: a frame arc with a little string bed = the trigger guard
    ring = [(0, Y(-46) + math.sin(a) * W(58), Z(412) + math.cos(a) * W(58)) for a in [math.radians(d) for d in range(200, 341, 10)]]
    A(sweep(ring, [W(7)] * len(ring), frame, seg=10, squash=(0.8, 1.0)))
    for k in range(-3, 4):  # mains and crosses inside the arc
        zz = Z(412) + k * W(13)
        A(rod((0, Y(-46), zz), (0, Y(-46) - math.sqrt(max(0, 54 ** 2 - (k * 13) ** 2)) * S, zz), W(1.1), strings, seg=4))
    for k in range(1, 4):
        yy = Y(-46) - k * W(13); half = math.sqrt(max(0, 54 ** 2 - (k * 13) ** 2)) * S
        A(rod((0, yy, Z(412) - half), (0, yy, Z(412) + half), W(1.1), strings, seg=4))
    A(side([(Z(432), Y(-40)), (Z(442), Y(-42)), (Z(446), Y(-74)), (Z(438), Y(-76)), (Z(434), Y(-56))], W(10), (0, 0, 0), red, bev=0.0012))  # trigger
    # ---------------- sights: line-judge yellow rear notch on the tee, a green bead on a post at the lid
    for sx in (-1, 1): A(box((W(8), W(16), W(10)), (sx * W(8), Y(SIGHT_H - 8), Z(330)), yellow, bev=0.0008))
    A(box((W(26), W(8), W(12)), (0, Y(SIGHT_H - 18), Z(330)), yellow, bev=0.0008))
    A(box((W(8), W(SIGHT_H - 60), W(10)), (0, Y((SIGHT_H + 20) / 2 - 2), Z(330)), frame_k, bev=0.0008))  # riser off the tee
    A(rod((0, Y(39), Z(8)), (0, Y(SIGHT_H - 3), Z(8)), W(2.6), frame_k, seg=6))
    A(box((W(5), W(30), W(14)), (0, Y(52), Z(8)), frame_k, bev=0.0006))  # its clamp on the lid
    A(ball(W(3.4), (0, Y(SIGHT_H - 3), Z(8)), bead, seg=10, rings=6))
    for p in parts: uv_box(p, 0.06)
    for o, sz, ax in decals:
        apply_mods(o); c = o.matrix_world.translation; uv_planar(o, (c.x, c.z, -c.y), sz, ax)
    WZ = {'tb_frame': 'a', 'tb_frame_k': 'a', 'tb_overgrip': 'a', 'tb_butt': 'a', 'tb_pvc': 'b', 'tb_co2': 'b', 'tb_alu': 'b', 'tb_lid': 'b', 'tb_clamp': 'b', 'tb_brass': 'b'}
    bodies = zone_join(parts, 'tennis_body', WZ, default='n')
    meta = {'kind': 'weapon', 'id': 'tennis', 'paint': ['tb_frame'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': Y(SIGHT_H), 'z': Z(330) + 0.2}, 'hatAt': [[hx(224)[0], hx(224)[1], hz], 0.08]}
    return finish('w_tennis', bodies, meta)


main(build, 'w_tennis')
