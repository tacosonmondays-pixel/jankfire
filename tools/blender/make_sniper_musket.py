# Musket (sniper_musket): an India Pattern Brown Bess, real millimetres x1.38 so the muzzle (-1.48), the trigger and
# the butt land where the code skin has them: a bright 39in .75 barrel with its bayonet lug, a walnut full stock
# (lofted: thin forestock, lock panels, slim wrist, the long dropped butt), brass butt plate with its tang, long
# trigger guard, serpentine side plate, nose cap and ramrod pipes, a steel ramrod, a flintlock (cock + flint in leather,
# frizzen, pan, spring) and a 15in socket bayonet fixed. Made fun: the sniper scopes in, so somebody lashed a brass
# pirate spyglass on top with twine. The spyglass is the sight line (the gun hides when you're fully scoped).
# run: blender -b --python tools/blender/make_sniper_musket.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.38 / 1000
BORE_Y, MUZ_Z = 0.04, -1.48
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]
BREECH = 991    # 39in barrel
SPY_H = 56      # the spyglass axis: the sight line
EYE_D = 1004    # the spyglass eyepiece


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def leather(px):  # brown leather with a stitched seam
    h, w = px.shape[:2]
    r = np.random.default_rng(9)
    px[:] = hexrgb(0x5a3418) * (0.85 + 0.3 * r.random((h, w)))[:, :, None]
    for x in range(0, w, 3): px[h // 2, x] = hexrgb(0xe8d8a8)


def rope(px):  # twisted twine
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    px[:] = np.where(((xx + yy) // 2 % 2)[:, :, None] == 0, hexrgb(0xd8c08a), hexrgb(0xa8905a))


def tex_walnut(name, base, dark, size=64, seed=5, lines=6):  # long thin grain lines, gentle wobble, tiles both ways
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size] / size
    warp = np.zeros_like(x)
    for f, a in ((1, 0.03), (2, 0.015), (4, 0.006)):
        warp += a * np.sin(2 * math.pi * (f * x + r.random())) * np.cos(2 * math.pi * (f * y + r.random()))
    g = 0.5 + 0.5 * np.sin(2 * math.pi * lines * (y + warp))
    t = np.clip((g > 0.86) * 0.65 + 0.25 * g ** 3 + 0.1 * r.random((size, size)), 0, 1)
    px = hexrgb(base)[None, None] * (1 - t[:, :, None]) + hexrgb(dark)[None, None] * t[:, :, None]
    return tex_canvas(name, size, size, lambda p: p.__setitem__(slice(None), px))


def build():
    steel = mat('mk_steel', 0xc4c8d0, rough=0.24, metal=1.0, tex=tex_noise('mk_steel_t', 0xc4c8d0, var=0.05, size=16, seed=191))
    walnut = mat('mk_walnut', 0x7a3a1a, rough=0.32, clearcoat=0.55, tex=tex_walnut('mk_walnut_t', 0x8a4420, 0x4a1a08, seed=192, lines=7))
    brass = mat('mk_brass', 0xe2b24a, rough=0.22, metal=1.0, tex=tex_noise('mk_brass_t', 0xe2b24a, var=0.05, size=16, seed=193))
    dark = mat('mk_dark', 0x2a2b30, rough=0.4, metal=0.7)
    flint = mat('mk_flint', 0x3a3a40, rough=0.6)
    hide = mat('mk_leather', 0x5a3418, rough=0.75, tex=tex_canvas('mk_leather_t', 16, 16, leather))
    twine = mat('mk_twine', 0xd8c08a, rough=0.85, tex=tex_canvas('mk_twine_t', 8, 8, rope))
    glass = mat('mk_lens', 0x9fd8ff, rough=0.03, metal=0.3, emit=0x6ab8ff, strength=0.5)
    black = mat('mk_black', 0x050505, rough=0.35)
    parts = []
    A = parts.append

    # ---------------- the barrel: bright, tapering, a dark bore, the bayonet lug on top, the breech tang
    A(lathe([(W(10.2), Z(0)), (W(12.8), Z(0)), (W(12.8), Z(3)), (W(13.2), Z(200)), (W(14.2), Z(600)), (W(15.6), Z(900)), (W(16.2), Z(950)), (W(16.2), Z(BREECH))],
            (0, BORE_Y, 0), steel, seg=18))
    A(lathe([(0, Z(1)), (W(9.6), Z(1)), (W(9.6), Z(16))], (0, BORE_Y, 0), black, seg=12))
    A(box((W(5), W(5), W(10)), (0, Y(14), Z(58)), steel, bev=W(1)))  # bayonet lug / front sight
    A(side(poly([(BREECH - 6, 10), (BREECH + 62, 6), (BREECH + 64, 2), (BREECH - 6, 2)]), W(12), (0, 0, 0), steel, bev=W(1.5)))  # tang
    for d in (180, 520, 760):  # the pins through the stock that hold the barrel
        A(cyl(W(2.2), W(36), (0, Y(-8), Z(d)), brass, axis='x', seg=6))

    # ---------------- walnut full stock, lofted
    st = [(96, -2, -24, 28), (110, 0, -25, 30), (400, 1, -26, 31), (700, 2, -28, 33), (880, 4, -32, 36), (920, 6, -38, 44), (1000, 7, -40, 45), (1060, 6, -44, 44),
          (1100, 0, -46, 36), (1140, -8, -50, 33), (1180, -18, -62, 34), (1220, -26, -82, 37), (1300, -34, -118, 40), (1380, -44, -152, 42), (1440, -52, -178, 42)]
    def ring(i, t):
        d, top, bot, wd = st[i]
        hh, hw = W(top - bot) / 2, W(wd) / 2
        out = []
        for k in range(16):
            a = 2 * math.pi * k / 16
            c, s_ = math.cos(a), math.sin(a)
            out.append((hh * math.copysign(abs(s_) ** 0.7, s_), hw * math.copysign(abs(c) ** 0.7, c)))
        return out
    A(loft([(0, Y((top + bot) / 2), Z(d)) for d, top, bot, wd in st], ring, walnut, name='stock'))
    # ---------------- brass furniture: nose cap, ramrod pipes + tail pipe, butt plate + tang, guard, side plate, thumb piece
    A(side(poly([(90, 2), (104, 2), (104, -26), (96, -28), (90, -22)]), W(31), (0, 0, 0), brass, bev=W(2)))
    for d in (260, 470, 660):
        A(lathe([(W(6.2), Z(d - 14)), (W(7.4), Z(d - 10)), (W(7.4), Z(d + 10)), (W(6.2), Z(d + 14))], (0, Y(-22), 0), brass, seg=10, cap=False))
    A(lathe([(W(6.2), Z(740)), (W(8.6), Z(752)), (W(8.6), Z(800)), (W(6), Z(820))], (0, Y(-23), 0), brass, seg=10))
    A(rod((0, Y(-22), Z(20)), (0, Y(-22), Z(760)), W(4.8), steel, seg=8))  # ramrod
    A(lathe([(0, Z(12)), (W(6), Z(14)), (W(6.6), Z(22)), (W(5), Z(28))], (0, Y(-22), 0), steel, seg=10))  # its button head
    A(side(poly([(1436, -48), (1452, -50), (1456, -60), (1456, -176), (1450, -184), (1436, -180)]), W(44), (0, 0, 0), brass, bev=W(2.5)))
    A(side(poly([(1370, -41), (1440, -49), (1440, -55), (1372, -46)]), W(14), (0, 0, 0), brass, bev=W(1.5)))  # tang over the comb
    A(side(poly([(1010, -40), (1180, -64), (1182, -70), (1150, -70), (1118, -88), (1096, -94), (1068, -88), (1054, -74), (1012, -46)]), W(10), (0, 0, 0), brass, bev=W(1.5),
           holes=[poly([(1062, -54), (1112, -62), (1110, -78), (1094, -86), (1072, -82), (1064, -70)])]))
    A(side(poly([(1074, -44), (1080, -44), (1084, -56), (1080, -68), (1074, -66), (1076, -56)]), W(6), (0, 0, 0), steel, bev=W(1)))  # trigger
    A(side(poly([(945, -10), (968, -4), (1000, -8), (1030, -2), (1066, -10), (1070, -18), (1040, -22), (1000, -26), (960, -24), (944, -18)]), W(2.5), (-W(22.6), 0, 0), brass, bev=W(0.8)))
    for d in (968, 1040): A(cyl(W(3.4), W(1.5), (-W(24), Y(-14), Z(d)), steel, axis='x', seg=10))  # lock screws
    esc = cyl(W(8), W(1.5), (0, Y(-3.6), Z(1122)), brass, axis='y', seg=14); esc.scale = (0.7, 1.0, 1.0); A(esc)  # thumb piece
    for d, h in ((340, -30), (1046, -48)):  # sling swivels
        A(tube([(0, Y(h), Z(d - 10)), (0, Y(h - 12), Z(d - 8)), (0, Y(h - 14), Z(d + 2)), (0, Y(h - 4), Z(d + 10))], W(1.8), brass, seg=6))
    # ---------------- the flintlock (right side): lock plate, cock with jaws + flint in leather, frizzen + pan, spring
    A(side(poly([(924, 4), (960, 8), (1030, 8), (1076, 0), (1084, -6), (1070, -14), (1000, -18), (940, -14), (922, -6)]), W(3), (W(22.8), 0, 0), steel, bev=W(0.8)))
    A(side(poly([(1030, 4), (1044, 6), (1040, 20), (1028, 34), (1022, 44), (1010, 46), (1000, 42), (1006, 36), (1016, 32), (1024, 20), (1026, 8)]), W(6), (W(26), 0, 0), steel, bev=W(1.2)))
    A(box((W(7), W(6), W(14)), (W(26), Y(44), Z(1004)), hide))
    A(box((W(6), W(9), W(12)), (W(26), Y(48), Z(998)), flint, rot=(0.25, 0, 0)))
    A(cyl(W(3), W(14), (W(26), Y(55), Z(1010)), steel, axis='y', seg=8))  # the jaw screw
    A(side(poly([(976, 6), (992, 6), (994, 34), (988, 38), (980, 34)]), W(12), (W(24), 0, 0), steel, bev=W(1.2)))  # frizzen
    A(box((W(14), W(5), W(22)), (W(24), Y(6), Z(986)), brass, bev=W(1)))  # the pan
    A(side(poly([(946, -6), (976, -2), (978, 4), (946, 0)]), W(3), (W(25), 0, 0), steel, bev=W(0.6)))  # frizzen spring
    # ---------------- socket bayonet: the socket over the muzzle, the bent neck, a 15in triangular blade on the right
    A(lathe([(W(13.6), Z(-14)), (W(16.6), Z(-12)), (W(16.6), Z(84)), (W(13.6), Z(86))], (0, BORE_Y, 0), steel, seg=16, cap=False))
    A(lathe([(W(17.4), Z(-14)), (W(17.4), Z(-4))], (0, BORE_Y, 0), steel, seg=16, cap=False))  # the socket's front ring
    A(sweep([(W(14), Y(-4), Z(-8)), (W(22), Y(-6), Z(-14)), (W(26), Y(-7), Z(-26)), (W(26), Y(-7), Z(-40))], W(4.5), steel, seg=8))
    # triangular section, tapering to the point
    blade = loft([(W(26), Y(-7), Z(-38 - t * 381)) for t in [i / 10 for i in range(11)]],
                 lambda i, t: [(W(5) * (1 - t * 0.92) + W(0.3), 0), (-W(4) * (1 - t * 0.92) - W(0.2), W(9) * (1 - t * 0.95) + W(0.3)), (-W(4) * (1 - t * 0.92) - W(0.2), -W(9) * (1 - t * 0.95) - W(0.3))],
                 steel, name='blade', close=(False, True), smooth_angle=20)
    A(blade)
    # ---------------- the spyglass: leather-covered main barrel, brass ends, three brass draws, lens + eyepiece
    sy = Y(SPY_H)
    A(lathe([(W(21), Z(600)), (W(25), Z(602)), (W(25), Z(640)), (W(22.5), Z(646))], (0, sy, 0), brass, seg=20, cap=False))  # objective cell
    A(lathe([(W(21.6), Z(644)), (W(21.6), Z(826))], (0, sy, 0), hide, seg=20, cap=False))
    A(lathe([(W(22.8), Z(822)), (W(22.8), Z(846)), (W(20), Z(850))], (0, sy, 0), brass, seg=20, cap=False))
    for k, (r, d0, d1) in enumerate(((17.5, 846, 900), (15, 896, 950), (12.5, 946, EYE_D - 10))):
        A(lathe([(W(r), Z(d0)), (W(r), Z(d1))], (0, sy, 0), brass, seg=18, cap=False))
        A(lathe([(W(r + 1.4), Z(d1 - 8)), (W(r + 1.4), Z(d1))], (0, sy, 0), brass, seg=18, cap=False))
    A(lathe([(W(9), Z(EYE_D - 10)), (W(13), Z(EYE_D - 6)), (W(13), Z(EYE_D)), (W(7), Z(EYE_D))], (0, sy, 0), brass, seg=16, cap=False))  # eyepiece cup
    A(cyl(W(21), W(1), (0, sy, Z(603)), glass, axis='z', seg=20))
    A(cyl(W(7.5), W(1), (0, sy, Z(EYE_D - 3)), black, axis='z', seg=12))
    # wooden wedges + twine lashings tying it to the barrel at two points
    for d in (690, 800):
        A(box((W(18), W(23), W(24)), (0, Y(24.5), Z(d)), walnut, bev=W(2)))
        for k in range(4):
            dz = d - 9 + k * 6
            cx_top, cx_bot = SPY_H, 0
            pts = []
            for i in range(16):
                a = 2 * math.pi * (i + 0.5) / 16
                rtop, rbot = 23.5, 17.0
                # a stadium round both tubes: upper half round the spyglass, lower half round the barrel
                if math.sin(a) >= 0: pts.append((math.cos(a) * W(rtop), Y(cx_top + math.sin(a) * rtop), Z(dz)))
                else: pts.append((math.cos(a) * W(rbot), Y(cx_bot + math.sin(a) * rbot), Z(dz)))
            A(tube(pts, W(1.5), twine, seg=4, closed=True))

    for p in parts: fixmats(p); uv_box(p, 0.05)
    WZ = {'mk_walnut': 'a', 'mk_brass': 'a', 'mk_steel': 'b', 'mk_dark': 'b', 'mk_leather': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'musket_body', WZ, default='n', rule=lambda m, c: 'a' if m == 'mk_steel' and c[2] > Z(BREECH - 80) else None)
    meta = {'kind': 'weapon', 'id': 'sniper', 'skin': 'sniper_musket', 'paint': ['mk_walnut'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': sy, 'z': Z(EYE_D)},
            'hatAt': [[0, sy + W(23), Z(740)], 0.13]}
    return finish('w_sniper_musket', bodies, meta)


main(build, 'w_sniper_musket')
