# AR: an M4-pattern carbine (14.5in barrel, flat-top upper, A-frame front sight, 6-position stock, curved 30-round
# mag), real millimetres scaled x1.54 so the muzzle (-0.72) and the pistol grip land where the game's AR has them.
# Made fun: a see-through bubblegum mag full of brass, hazard tape on the handguard, a glossy googly charm, a sticker.
# run: blender -b --python tools/blender/make_ar.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

S = 1.54 / 1000         # real mm -> game metres
BORE_Y, MUZ_Z = 0.015, -0.72
def P(d, h): return (MUZ_Z + d * S, BORE_Y + h * S)   # (distance back from the muzzle, height above the bore) in mm
def Z(d): return MUZ_Z + d * S
def Y(h): return BORE_Y + h * S
def W(mm): return mm * S
def poly(pts): return [P(d, h) for d, h in pts]


def build():
    gun = mat('ar_gunmetal', 0x2c3036, rough=0.34, metal=0.6)
    dark = mat('ar_dark', 0x141519, rough=0.45, metal=0.5)
    olive = mat('ar_olive', 0x5d7340, rough=0.42, tex=tex_noise('ar_olive_t', 0x5d7340, var=0.1, speck=0x3e4d2a, speck_p=0.06, seed=4))
    grip_m = mat('ar_grip', 0x4f6236, rough=0.6, tex=tex_noise('ar_grip_t', 0x4f6236, var=0.25, size=32, seed=9))
    mag_m = mat('ar_mag', 0xff3fae, rough=0.12, alpha=0.62)
    mag_base = mat('ar_magbase', 0xd81f8c, rough=0.25)
    brass = mat('ar_brass', 0xe0ad3c, rough=0.25, metal=1.0)
    copper = mat('ar_copper', 0xc8683a, rough=0.3, metal=1.0)
    rubber = mat('ar_rubber', 0x1c1c1e, rough=0.85)
    tape = mat('ar_tape', 0xffd21a, rough=0.5, tex=tex_stripes('ar_tape_t', 0xffd21a, 0x141414, size=16, width=4))
    dot = mat('ar_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    neon = mat('ar_neon', 0x3ff4ff, rough=0.3, emit=0x3ff4ff, strength=3.0)
    pink = mat('ar_charm', 0xff4fd8, rough=0.12, clearcoat=1.0)
    white = mat('ar_white', 0xffffff, rough=0.2)
    black = mat('ar_black', 0x050505, rough=0.2)

    def sticker_draw(px):
        px[:] = hexrgb(0xff2a8a)
        px[2:-2, 2:-2] = hexrgb(0xffe14d)
        text_px(px, 'JANK', 4, 4, 2, 0x111111)
    sticker = mat('ar_sticker', 0xffffff, rough=0.35, tex=tex_canvas('ar_sticker_t', 56, 22, sticker_draw))

    parts = []
    A = parts.append

    # ---------------- barrel + birdcage flash hider
    fh = lathe([(0.0, Z(-1)), (W(9), Z(-1)), (W(11), Z(2)), (W(11), Z(48)), (W(9.5), Z(52)), (W(9.5), Z(62))], (0, BORE_Y, 0), dark, seg=16)
    for k in range(4):  # the slots (closed bottom, like the A2 birdcage)
        if k == 2: continue
        a = k * math.pi / 2 + math.pi / 4
        c = box((W(4), W(30), W(30)), (math.cos(a) * W(11), BORE_Y + math.sin(a) * W(11), Z(24)), None, rot=(0, 0, a - math.pi / 2))
        cut(fh, c)
    A(fh)
    A(lathe([(W(7.6), Z(60)), (W(7.6), Z(165)), (W(8.8), Z(168)), (W(8.8), Z(372))], (0, BORE_Y, 0), dark, seg=16))
    A(lathe([(0, Z(0.5)), (W(3), Z(0.5)), (W(3), Z(6))], (0, BORE_Y, 0), black, seg=10))  # dark bore so the muzzle reads hollow

    # ---------------- front sight base: the A-frame, gas block, bayonet lug, sling swivel
    fsb = side(poly([(178, -13), (214, -13), (214, 12), (211, 18), (206, 52), (199, 52), (190, 18), (178, 12)]), W(17), (0, 0, 0), gun, bev=W(1.6),
               holes=[poly([(195, 21), (209, 21), (204.5, 44), (200.5, 44)])])
    A(fsb)
    A(cyl(W(15), W(34), (0, BORE_Y, Z(196)), gun, seg=18, bev=W(1)))
    A(box((W(10), W(16), W(30)), (0, Y(-19), Z(196)), gun, bev=W(1.5)))  # bayonet lug block
    A(box((W(3.2), W(20), W(3.2)), (0, Y(56), Z(202.5)), dark, bev=W(0.6)))  # front post
    A(box((W(4.2), W(4.2), W(4.2)), (0, Y(64), Z(202.5)), dot, bev=W(0.8)))   # glowing tip
    A(tube([(-W(6), Y(-26), Z(186)), (-W(6), Y(-36), Z(190)), (W(6), Y(-36), Z(190)), (W(6), Y(-26), Z(186))], W(1.6), dark, seg=6))

    # ---------------- handguard: ribbed two-piece carbine guard, end cap, delta ring, hazard tape
    hg = lathe([(W(16), Z(220)), (W(19.5), Z(226)), (W(20.5), Z(240)), (W(20.5), Z(350)), (W(19.5), Z(356))], (0, BORE_Y, 0), olive, seg=14)
    for i in range(6):  # vent holes on both sides, top and bottom rows
        for sx in (-1, 1):
            for hy in (9, -9):
                cut(hg, box((W(30), W(7), W(9)), (sx * W(19), Y(hy), Z(262 + i * 15)), None, bev=0))
    A(hg)
    A(lathe([(W(17), Z(214)), (W(17), Z(222))], (0, BORE_Y, 0), gun, seg=14))  # end cap
    A(lathe([(W(20), Z(352)), (W(23.5), Z(356)), (W(23.5), Z(366)), (W(17), Z(370))], (0, BORE_Y, 0), gun, seg=18))  # delta ring
    A(lathe([(W(21.2), Z(286)), (W(21.2), Z(318))], (0, BORE_Y, 0), tape, seg=14))
    A(box((W(3), W(3), W(110)), (0, Y(20.5), Z(295)), neon, bev=W(0.6)))  # a neon strip along the top of the guard

    # ---------------- upper receiver + flat-top rail + charging handle + ejection port + forward assist
    up = side(poly([(368, -14), (566, -14), (566, 12), (560, 22), (372, 22), (368, 16)]), W(29), (0, 0, 0), gun, bev=W(2))
    cut(up, box((W(10), W(15), W(58)), (W(14.5), Y(1), Z(462)), None))  # ejection port (right side)
    A(up)
    A(box((W(1.5), W(14), W(56)), (W(14.3), Y(1), Z(462)), dark, bev=W(0.3)))  # bolt carrier seen through the port
    A(side(poly([(520, -2), (540, -2), (548, 8), (530, 14), (520, 10)]), W(8), (W(16), 0, 0), gun, bev=W(1.5)))  # brass deflector bump
    A(cyl(W(6.5), W(22), (W(19), Y(2), Z(548)), gun, axis='z', seg=12, bev=W(1), rot=(0, 0.25, 0)))  # forward assist
    A(cyl(W(7.5), W(4), (W(20.6), Y(2), Z(559)), dark, axis='z', seg=12, rot=(0, 0.25, 0)))
    A(box((W(21), W(6), W(196)), (0, Y(25), Z(468)), gun, bev=W(0.8)))  # rail base
    for i in range(18):  # picatinny teeth
        A(box((W(21), W(5), W(6)), (0, Y(30), Z(378 + i * 10.5)), dark, bev=W(0.7)))
    A(box((W(52), W(7), W(14)), (0, Y(17), Z(574)), dark, bev=W(2)))  # charging handle T
    A(box((W(12), W(6), W(20)), (0, Y(17), Z(564)), dark, bev=W(1)))
    A(box((W(3), W(3), W(16)), (W(14.6), Y(-8), Z(400)), neon, bev=W(0.5)))  # status LED on the side (it's 2077 somewhere)

    # ---------------- rear flip-up sight on the rail (aperture on the sight line)
    sight_h = 64
    A(box((W(20), W(7), W(24)), (0, Y(36), Z(548)), gun, bev=W(1.5)))
    for sx in (-1, 1):
        A(side(poly([(541, 38), (555, 38), (551, 70), (545, 70)]), W(3), (sx * W(8), 0, 0), gun, bev=W(0.8)))
    ring = cyl(W(5), W(3), (0, Y(sight_h), Z(548)), dark, axis='z', seg=14)
    cut(ring, cyl(W(2.6), W(10), (0, Y(sight_h), Z(548)), None, axis='z', seg=10))
    A(ring)
    A(box((W(3), W(8), W(3)), (0, Y(sight_h - 8), Z(548)), dark))

    # ---------------- lower receiver: magwell, pins, controls
    low = side(poly([(370, -14), (566, -14), (566, -36), (546, -46), (470, -46), (463, -40), (461, -82), (372, -82), (366, -66), (366, -24)]), W(31), (0, 0, 0), gun, bev=W(2.2))
    A(low)
    A(side(poly([(366, -74), (463, -74), (465, -86), (364, -86)]), W(35), (0, 0, 0), gun, bev=W(2)))  # flared magwell lip
    for d in (380, 552):
        A(cyl(W(4), W(34), (0, Y(-22 if d == 380 else -24), Z(d)), dark, axis='x', seg=10))
    A(side(poly([(510, -26), (532, -24), (534, -32), (512, -34)]), W(3), (-W(17), 0, 0), dark, bev=W(0.8)))  # selector
    A(cyl(W(5), W(4), (W(17), Y(-40), Z(453)), dark, axis='x', seg=12))  # mag release
    A(side(poly([(461, -24), (475, -24), (475, -40), (461, -36)]), W(3), (-W(16.5), 0, 0), dark, bev=W(0.8)))  # bolt catch

    # ---------------- trigger guard + trigger
    A(side(poly([(461, -46), (468, -46), (468, -70), (505, -70), (512, -50), (518, -46), (522, -50), (512, -77), (461, -77)]), W(11), (0, 0, 0), gun, bev=W(1.6)))
    A(side(poly([(486, -46), (491, -46), (493, -56), (490, -66), (486, -64), (488, -56)]), W(5), (0, 0, 0), dark, bev=W(1)))

    # ---------------- A2 pistol grip with finger nub, stippled
    A(side(poly([(510, -46), (552, -46), (582, -150), (578, -159), (548, -162), (540, -154), (531, -116), (535, -106), (526, -96), (514, -68)]), W(30), (0, 0, 0), grip_m, bev=W(6), seg=3))

    # ---------------- buffer tube, castle nut, 6-position stock, butt pad, QD sling loop
    A(cyl(W(15), W(70), (0, Y(2), Z(600)), dark, axis='z', seg=16))
    A(lathe([(W(17.5), Z(564)), (W(17.5), Z(572))], (0, Y(2), 0), gun, seg=10))
    A(side(poly([(612, 22), (754, 24), (762, 18), (762, -120), (750, -122), (690, -62), (640, -34), (612, -24)]), W(38), (0, 0, 0), olive, bev=W(5), seg=3))
    A(side(poly([(762, 24), (772, 22), (772, -124), (762, -124)]), W(43), (0, 0, 0), rubber, bev=W(2.5)))
    A(side(poly([(640, -24), (680, -30), (683, -40), (642, -34)]), W(10), (0, 0, 0), dark, bev=W(1.2)))  # adjust lever
    A(box((W(1), W(28), W(66)), (W(20.6), Y(-28), Z(700)), sticker, rot=(0.12, 0, 0)))  # JANK sticker on the right cheek
    loop = tube([(0, Y(-112), Z(742)), (0, Y(-128), Z(744)), (0, Y(-130), Z(732)), (0, Y(-118), Z(726))], W(2), dark, seg=6)
    A(loop)

    # ---------------- curved 30-round mag: see-through bubblegum plastic, brass inside, chunky floorplate
    front = [(374, -76), (371, -120), (363, -165), (350, -210), (338, -246)]
    back = [(457, -76), (455, -120), (448, -168), (437, -214), (426, -250)]
    A(side(poly(front + back[::-1]), W(23), (0, 0, 0), mag_m, bev=W(2.5)))
    A(side(poly([(334, -244), (428, -248), (426, -266), (330, -262)]), W(28), (0, 0, 0), mag_base, bev=W(3)))
    rib = side(poly([(352, -150), (354, -140), (445, -142), (443, -152)]), W(25), (0, 0, 0), mag_base, bev=W(1.5))
    A(rib)
    for i in range(9):  # staggered rounds, following the curve
        t = (i + 0.5) / 9
        k = min(len(front) - 2, int(t * (len(front) - 1)))
        u = t * (len(front) - 1) - k
        fd = front[k][0] + (front[k + 1][0] - front[k][0]) * u; fh_ = front[k][1] + (front[k + 1][1] - front[k][1]) * u
        bd = back[k][0] + (back[k + 1][0] - back[k][0]) * u
        dmid = (fd + bd) / 2
        ang = math.atan2(front[k + 1][0] - front[k][0], -(front[k + 1][1] - front[k][1]))
        x = W(4.2) * (1 if i % 2 else -1)
        h = fh_ - 6
        case = cyl(W(4.8), W(44), (x, Y(h), Z(dmid + 6)), brass, axis='z', seg=10, rot=(-ang, 0, 0))
        tip = cyl(W(4.5), W(14), (x, Y(h), Z(dmid - 23)), copper, axis='z', seg=10, r2=W(1.5), rot=(-ang, 0, 0))
        A(case); A(tip)

    # ---------------- glossy toy charm hanging off the sling loop: a pink blob with googly eyes
    cx, cy, cz = 0, Y(-160), Z(736)
    A(tube([(0, Y(-128), Z(736)), (0, Y(-140), Z(737)), (0, Y(-150), Z(736))], W(1.3), brass, seg=6))
    A(ball(W(15), (cx, cy, cz), pink, scale=(1, 1.05, 1), seg=18, rings=12))
    for ex in (-1, 1):
        A(ball(W(5.5), (ex * W(6), cy + W(4), cz - W(12.5)), white, seg=12, rings=8, scale=(1, 1, 0.6)))
        A(ball(W(2.6), (ex * W(6) + ex * W(1.2), cy + W(2.5), cz - W(15.5)), black, seg=8, rings=6, scale=(1, 1, 0.6)))

    for p in parts:
        uv_box(p, 0.03)
    WZ = {'ar_olive': 'a', 'ar_grip': 'a', 'ar_rubber': 'a', 'ar_gunmetal': 'a', 'ar_dark': 'b', 'ar_mag': 'b', 'ar_magbase': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'ar_body', WZ, default='n', rule=lambda m, c: 'b' if m == 'ar_gunmetal' and c[2] < Z(350) else None)  # the front sight base + delta ring ride with the barrel
    meta = {'kind': 'weapon', 'id': 'ar', 'paint': ['ar_olive', 'ar_grip'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(sight_h), 'z': Z(548) + 0.11},
            'hatAt': [[0, Y(33), Z(440)], 0.12], 'tip': None}
    return finish('w_ar', bodies + [], meta)


main(build, 'w_ar')
