# Bullpup (ar_bullpup): an original 24in DMR-style bullpup (the action lives in the butt: pistol grip + full-hand
# trigger guard up front, the magazine BEHIND the grip, ejection port by your cheek), real millimetres x1.38 so the
# muzzle (-0.72) and the grip land where the game's AR has them. A carry-handle optic on top (thin walls, clear lenses,
# a lit ring reticle), three-prong flash hider, gas block, left-side charging handle, folding foregrip, rubber cheek
# riser and butt pad, a see-through smoke magazine with the brass showing. Glossy white polymer with orange bits.
# Made fun: bullpups always look like they're on backwards, so the stock says FRONT TOWARD ENEMY.
# run: blender -b --python tools/blender/make_ar_bullpup.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.38 / 1000
BORE_Y, MUZ_Z = 0.015, -0.72
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
OPT_H = 84            # optic axis = the sight line
EYEPIECE = 652        # back of the optic


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def stencil(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xe6eaee)
    text_px(px, 'FRONT TOWARD', 3, 2, 1, 0x16181c)
    text_px(px, 'ENEMY', 3, 12, 1, 0x16181c)
    for i in range(18):  # the arrow points at the muzzle (left, as you see it)
        px[15:17, 36 + i] = hexrgb(0xff5a10)
    for k in range(5): px[16 - k:17 + k, 34 - k] = hexrgb(0xff5a10)


def build():
    shell = mat('bp_shell', 0xe8ecef, rough=0.3, clearcoat=0.7, tex=tex_noise('bp_shell_t', 0xe8ecef, var=0.04, size=16, seed=161))
    panel = mat('bp_panel', 0x9aa2ac, rough=0.4, clearcoat=0.4, tex=tex_noise('bp_panel_t', 0x9aa2ac, var=0.06, size=16, seed=162))
    gun = mat('bp_gunmetal', 0x2a2e36, rough=0.34, metal=0.65)
    dark = mat('bp_dark', 0x141519, rough=0.45, metal=0.45)
    rubber = mat('bp_rubber', 0x1c1d20, rough=0.85, tex=tex_noise('bp_rubber_t', 0x1e1f22, var=0.2, size=16, seed=163))
    orange = mat('bp_orange', 0xff6a14, rough=0.25, clearcoat=0.8)
    smoke = mat('bp_mag', 0x3a4250, rough=0.1, alpha=0.55)
    brass = mat('bp_brass', 0xe0ad3c, rough=0.25, metal=1.0)
    copper = mat('bp_copper', 0xc8683a, rough=0.3, metal=1.0)
    lens = mat('bp_lens', 0x9fe8ff, rough=0.02, metal=0.3, alpha=0.18)
    ret = mat('bp_reticle', 0xff3a1a, rough=0.3, emit=0xff3a1a, strength=4.0)
    black = mat('bp_black', 0x050505, rough=0.3)
    sten = mat('bp_stencil', 0xffffff, rough=0.35, tex=tex_canvas('bp_stencil_t', 76, 22, stencil))
    parts, decals = [], []
    A = parts.append

    # ---------------- three-prong flash hider, heavy barrel, gas block + tube into the shell
    fh = lathe([(0, Z(-0.5)), (W(10), Z(-0.5)), (W(11), Z(2)), (W(11), Z(44)), (W(9.5), Z(48)), (W(9.5), Z(56))], (0, BORE_Y, 0), dark, seg=18)
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3
        cut(fh, box((W(5), W(30), W(34)), (math.cos(a) * W(10), BORE_Y + math.sin(a) * W(10), Z(17)), None, rot=(0, 0, a - math.pi / 2)))
    A(fixmats(fh))
    A(lathe([(0, Z(0.5)), (W(5), Z(0.5)), (W(5), Z(8))], (0, BORE_Y, 0), black, seg=10))
    A(lathe([(W(8.8), Z(54)), (W(9.2), Z(150)), (W(10), Z(280)), (W(10), Z(400))], (0, BORE_Y, 0), gun, seg=16))
    A(side(poly([(268, -12), (300, -12), (300, 22), (290, 26), (272, 26), (268, 18)]), W(26), (0, 0, 0), dark, bev=W(2)))
    A(lathe([(W(4.5), Z(296)), (W(4.5), Z(330))], (0, Y(18), 0), gun, seg=10, cap=False))
    # ---------------- the shell: one long polymer body from the handguard to the butt, grey side panels, M-LOK slots
    sh = side(poly([(318, 18), (322, 27), (700, 27), (714, 24), (846, 24), (858, 20), (861, 8), (861, -100), (855, -112), (838, -116), (782, -100), (702, -52),
                    (690, -46), (612, -46), (600, -42), (520, -36), (500, -32), (326, -30), (318, -22)]), W(60), (0, 0, 0), shell, bev=W(7), seg=2)
    for k in range(4):  # M-LOK slots both sides of the handguard
        for sx in (-1, 1): cut(sh, box((W(14), W(9), W(26)), (sx * W(30), Y(-6), Z(354 + k * 34)), None, bev=W(3)))
    cut(sh, box((W(16), W(22), W(62)), (W(30), Y(4), Z(646)), None, bev=W(2)))  # ejection port (right, by your cheek)
    cut(sh, box((W(14), W(7), W(130)), (-W(30), Y(16), Z(404)), None))  # charging handle slot (left)
    A(fixmats(sh))
    for k in range(4):
        for sx in (-1, 1): A(box((W(2), W(8), W(25)), (sx * W(27.5), Y(-6), Z(354 + k * 34)), dark))  # the slots' insides
    A(box((W(2), W(20), W(60)), (W(27.6), Y(4), Z(646)), dark))  # bolt face in the port
    A(box((W(2), W(6), W(128)), (-W(27.6), Y(16), Z(404)), dark))
    for sx in (-1, 1):
        A(side(poly([(705, 10), (842, 10), (850, 0), (850, -74), (838, -94), (790, -80), (712, -40), (705, -28)]), W(3), (sx * W(30.2), 0, 0), panel, bev=W(1.2)))
        A(side(poly([(520, -20), (590, -20), (594, -34), (520, -30)]), W(3), (sx * W(30.2), 0, 0), panel, bev=W(1)))
    # charging handle: a folding knob riding in the left slot, an orange tip
    A(box((W(14), W(10), W(16)), (-W(34), Y(16), Z(348)), dark, bev=W(2)))
    A(cyl(W(6), W(12), (-W(44), Y(16), Z(348)), orange, axis='x', seg=10, bev=W(1.5)))
    # ---------------- rubber cheek riser on top of the butt, butt pad, sling points
    A(side(poly([(726, 22), (838, 22), (840, 38), (826, 44), (738, 44), (726, 36)]), W(46), (0, 0, 0), rubber, bev=W(5), seg=2))
    A(side(poly([(858, 22), (874, 20), (876, 8), (876, -104), (870, -118), (856, -116)]), W(56), (0, 0, 0), rubber, bev=W(4), seg=2))
    for k in range(5): A(box((W(58), W(2.5), W(8)), (0, Y(-10 - k * 20), Z(872)), black))
    for d, h in ((330, -26), (832, -100)):
        lp = cyl(W(9), W(6), (-W(31), Y(h), Z(d)), orange, axis='x', seg=14)
        cut(lp, cyl(W(4.5), W(20), (-W(31), Y(h), Z(d)), None, axis='x', seg=10))
        A(fixmats(lp))
    # ---------------- folding foregrip (angled forward) under the handguard
    A(side(poly([(352, -30), (392, -30), (380, -60), (360, -120), (344, -128), (334, -122), (338, -110), (350, -62)]), W(30), (0, 0, 0), dark, bev=W(6), seg=2))
    A(cyl(W(6), W(34), (0, Y(-36), Z(372)), gun, axis='x', seg=12))  # its hinge
    # ---------------- pistol grip, full-hand trigger guard, trigger, selector, mag release
    A(side(poly([(544, -40), (590, -40), (614, -138), (610, -150), (590, -154), (580, -146), (572, -118), (576, -108), (566, -96), (560, -70)]), W(30), (0, 0, 0), shell, bev=W(6), seg=2))
    A(side(poly([(492, -30), (506, -30), (514, -72), (528, -120), (548, -140), (596, -152), (600, -162), (546, -162), (520, -146), (502, -110), (492, -64)]), W(18), (0, 0, 0), shell, bev=W(4)))
    A(side(poly([(528, -36), (535, -36), (539, -48), (535, -60), (529, -58), (531, -48)]), W(6), (0, 0, 0), orange, bev=W(1.2)))
    A(cyl(W(9), W(64), (0, Y(-20), Z(560)), dark, axis='x', seg=14))  # crossbolt safety
    A(cyl(W(9.5), W(3), (-W(32.5), Y(-20), Z(560)), orange, axis='x', seg=14))
    A(box((W(10), W(12), W(10)), (0, Y(-50), Z(700)), dark, bev=W(2)))  # mag release behind the well
    # ---------------- the magazine (behind the grip): smoke see-through, brass inside, floorplate, a lip on the well
    front = [(616, -44), (613, -100), (604, -150), (590, -198)]
    back = [(688, -44), (686, -100), (678, -150), (665, -202)]
    A(side(poly(front + back[::-1]), W(23), (0, 0, 0), smoke, bev=W(2.5)))
    A(side(poly([(584, -195), (670, -199), (668, -216), (580, -212)]), W(28), (0, 0, 0), dark, bev=W(3)))
    A(side(poly([(606, -40), (696, -40), (694, -52), (608, -52)]), W(36), (0, 0, 0), shell, bev=W(3)))
    for i in range(8):
        t = (i + 0.5) / 8
        k = min(len(front) - 2, int(t * (len(front) - 1)))
        u = t * (len(front) - 1) - k
        fd = front[k][0] + (front[k + 1][0] - front[k][0]) * u; fh_ = front[k][1] + (front[k + 1][1] - front[k][1]) * u
        bd = back[k][0] + (back[k + 1][0] - back[k][0]) * u
        ang = math.atan2(front[k + 1][0] - front[k][0], -(front[k + 1][1] - front[k][1]))
        x = W(4.2) * (1 if i % 2 else -1)
        dm = (fd + bd) / 2
        A(cyl(W(4.8), W(42), (x, Y(fh_ - 6), Z(dm + 7)), brass, axis='z', seg=10, rot=(-ang, 0, 0)))
        A(cyl(W(4.5), W(14), (x, Y(fh_ - 6), Z(dm - 21)), copper, axis='z', seg=10, r2=W(1.5), rot=(-ang, 0, 0)))
    # ---------------- carry-handle optic: two legs (open under the tube), a big objective bell, thin walls, clear
    # lenses, a lit ring reticle, a rubber eyecup, a backup notch on top
    A(side(poly([(470, 26), (512, 26), (506, OPT_H - 17), (476, OPT_H - 17)]), W(24), (0, 0, 0), shell, bev=W(3)))  # front leg
    A(side(poly([(556, 26), (590, 26), (586, OPT_H - 17), (560, OPT_H - 17)]), W(18), (0, 0, 0), shell, bev=W(3)))  # rear leg (forward, out of your eye)
    for d0, d1 in ((476, 506), (560, 586)):  # the clamps round the tube on each leg
        A(lathe([(W(22.6), Z(d0)), (W(22.6), Z(d1))], (0, Y(OPT_H), 0), shell, seg=26, cap=False))
    oy = Y(OPT_H)
    A(lathe([(W(28), Z(452)), (W(30), Z(456)), (W(30), Z(486)), (W(21.5), Z(500)), (W(21.5), Z(EYEPIECE)), (W(20.6), Z(EYEPIECE)),
             (W(20.6), Z(500)), (W(28.5), Z(486)), (W(28.5), Z(452))], (0, oy, 0), gun, seg=26, cap=False))  # thin walls: you look through it, not at it
    A(lathe([(W(22), Z(EYEPIECE - 12)), (W(22.4), Z(EYEPIECE + 3)), (W(20.8), Z(EYEPIECE + 3)), (W(20.8), Z(EYEPIECE - 12))], (0, oy, 0), rubber, seg=26, cap=False))
    A(lathe([(W(30.4), Z(460)), (W(30.4), Z(470))], (0, oy, 0), orange, seg=26, cap=False))  # orange ring round the bell
    A(cyl(W(27.4), W(1), (0, oy, Z(470)), lens, axis='z', seg=24))
    A(cyl(W(20.4), W(1), (0, oy, Z(640)), lens, axis='z', seg=24))
    rr = cyl(W(5), W(0.8), (0, oy, Z(471)), ret, axis='z', seg=16)
    cut(rr, cyl(W(3.6), W(3), (0, oy, Z(471)), None, axis='z', seg=12))
    A(fixmats(rr))
    A(cyl(W(0.9), W(0.8), (0, oy, Z(471)), ret, axis='z', seg=8))
    A(cyl(W(7), W(12), (W(24), oy, Z(530)), dark, axis='x', seg=14, bev=W(1.5)))  # windage turret
    for sx in (-1, 1): A(box((W(4), W(8), W(10)), (sx * W(5), oy + W(24), Z(540)), dark, bev=W(1)))  # backup notch
    # ---------------- the stencil (left side of the butt, the side you look at)
    st = box((W(1), W(36), W(124)), (-W(31.9), Y(-31), Z(776)), sten, rot=(0, math.pi, 0)); A(st); decals.append((st, (W(124), W(36))))

    for p in parts: fixmats(p); uv_box(p, 0.05)
    for o, sz in decals:
        apply_mods(o); c = o.matrix_world.translation; uv_planar(o, (c.x, c.z, -c.y), sz, '-x')
    WZ = {'bp_shell': 'a', 'bp_panel': 'a', 'bp_rubber': 'a', 'bp_gunmetal': 'b', 'bp_dark': 'b', 'bp_mag': 'b', 'bp_orange': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'bp_body', WZ, default='n', rule=lambda m, c: 'a' if m == 'bp_dark' and c[2] > Z(500) and c[1] > Y(-60) else None)
    meta = {'kind': 'weapon', 'id': 'ar', 'skin': 'ar_bullpup', 'paint': ['bp_shell'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(OPT_H), 'z': Z(EYEPIECE) + 0.1},
            'hatAt': [[0, Y(OPT_H + 30), Z(540)], 0.12]}
    return finish('w_ar_bullpup', bodies, meta)


main(build, 'w_ar_bullpup', exposure=-0.5)
