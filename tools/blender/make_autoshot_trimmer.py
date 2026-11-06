# Weed Whacker (autoshot_trimmer): a petrol string trimmer as the Lawn Mower's auto shotgun, in its own millimetres
# (x1.26): the bump-feed head on the muzzle (spool facing forward, two orange lines whipping out, the debris guard
# over it), the straight drive shaft as the barrel, the loop handle as the foregrip, the 2-stroke engine where the
# receiver is (shroud, air-filter cover with a primer bulb, muffler + heat guard, spark plug boot, the starter
# housing on the right), the rear throttle handle as the pistol grip (throttle trigger + lockout), a tube stock with
# a foam hip pad. Moving parts like the Lawn Mower: 'mag' = the see-through fuel tank (pink 50:1 mix, origin on its
# seat) and 'charge' = the pull-start T-handle (slides back, the cord with it).
# Made fun: ☺ CORP WEED-B-GONE, MIX 50:1, TRIM RESPONSIBLY.
# run: blender -b --python tools/blender/make_autoshot_trimmer.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corp import *

AS = Scale(1.26, 0.02, -0.76)
Z, Y, W, poly = AS.Z, AS.Y, AS.W, AS.poly
BORE_Y, MUZ_Z = 0.02, -0.76
SIGHT_H, REAR_D, FRONT_D = 68, 643, 126   # 22 mm over the Lawn Mower's: the engine is fat
MAG_D, MAG_H = 543, -52
CH = (W(21), Y(8), Z(575))


def build():
    orange = plastic('tr_orange', 0xff6a10, rough=0.18, cc=1.0, var=0.05, seed=1101, speck=0xff9a4a, speck_p=0.03)
    white = plastic('tr_white', 0xe8e6e0, rough=0.3, cc=0.6, seed=1102)
    black = plastic('tr_black', 0x1a1b1e, rough=0.55, cc=0.2, var=0.1, seed=1103)
    alu = mat('tr_alu', 0xb8bcc4, rough=0.25, metal=0.9, tex=tex_noise('tr_alu_t', 0xb8bcc4, var=0.05, size=16, seed=1104))
    steel = mat('tr_steel', 0x2a2c32, rough=0.4, metal=0.6)
    dark = mat('tr_dark', 0x121316, rough=0.5, metal=0.4)
    chrome = mat('tr_chrome', 0xdde2ea, rough=0.12, metal=1.0)
    line = mat('tr_line', 0xff8a1a, rough=0.4, clearcoat=0.5)
    rubber = mat('tr_rubber', 0x202124, rough=0.85, tex=tex_noise('tr_rub_t', 0x222326, var=0.14, size=16, seed=1105))
    foam = mat('tr_foam', 0x26272c, rough=0.95, tex=tex_noise('tr_foam_t', 0x26272c, var=0.2, size=16, speck=0x3a3b40, speck_p=0.3, seed=1106))
    tank = mat('tr_tank', 0xf2f0e6, rough=0.1, alpha=0.45)
    fuel = mat('tr_fuel', 0xff3fae, rough=0.05, emit=0x801050, strength=0.4)
    grass = mat('tr_grass', 0x39c22a, rough=0.6, tex=tex_noise('tr_grass_t', 0x3ab82a, var=0.2, size=8, speck=0x7dff4f, speck_p=0.1, seed=1107))
    dot = mat('tr_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    cordm = mat('tr_cord', 0xf2efe0, rough=0.8, tex=tex_stripes('tr_cord_t', 0xf2efe0, 0xd01c2a, size=8, width=2))
    logo = mat('tr_logo', 0xffffff, rough=0.25, clearcoat=0.8, tex=label_tex('tr_logo_t', 80, 20, [('CORP', 0xffffff), ('WEED-B-GONE', 0xffffff)], bg=0x1a1b1e, fg=0xffe14d, border=0xffe14d, smile_col=0xffe14d))
    mix = mat('tr_mix', 0xffffff, rough=0.4, tex=label_tex('tr_mix_t', 44, 20, [('MIX', None), ('50:1', 0xd01c2a)], bg=0xffe14d, smile=False))
    resp = mat('tr_resp', 0xffffff, rough=0.4, tex=label_tex('tr_resp_t', 86, 12, [('TRIM RESPONSIBLY', None)], bg=0xffffff, border=0xff6a10))
    parts, mag, chg, decals = [], [], [], []
    A = parts.append

    # ---------------- the head: bump knob (muzzle), spool with its two eyelets + line, the gearbox, the debris guard
    A(lathe([(0.0, Z(-1)), (W(10), Z(-0.5)), (W(16), Z(4)), (W(18), Z(12)), (W(18), Z(16))], (0, BORE_Y, 0), black, seg=18))
    A(cyl(W(6), W(1), (0, BORE_Y, Z(-1.2)), dark, axis='z', seg=10))  # the bore through the knob
    sp = lathe([(W(30), Z(16)), (W(40), Z(19)), (W(44), Z(26)), (W(44), Z(44)), (W(40), Z(50)), (W(26), Z(54))], (0, BORE_Y, 0), orange, seg=26)
    A(sp)
    A(lathe([(W(44.5), Z(28)), (W(44.5), Z(42))], (0, BORE_Y, 0), black, seg=26, cap=False))
    for sx in (-1, 1):  # eyelets + the line whipping out, a curl from the spin
        A(cyl(W(5), W(6), (sx * W(45), BORE_Y, Z(35)), chrome, axis='x', seg=10))
        pts = [(sx * W(46), BORE_Y, Z(35)), (sx * W(80), BORE_Y + W(6) * sx, Z(30)), (sx * W(120), BORE_Y + W(18) * sx, Z(36)), (sx * W(150), BORE_Y + W(36) * sx, Z(50))]
        A(sweep(pts, W(1.6), line, seg=6))
    A(lathe([(W(26), Z(54)), (W(24), Z(80)), (W(17), Z(96)), (W(12), Z(110))], (0, BORE_Y, 0), alu, seg=18))  # gearbox
    A(cyl(W(6), W(20), (0, BORE_Y + W(22), Z(82)), black, axis='y', seg=10))  # grease plug
    gd = lathe([(W(30), Z(74)), (W(78), Z(68)), (W(82), Z(72)), (W(82), Z(90)), (W(30), Z(96))], (0, BORE_Y, 0), orange, seg=28)
    cut(gd, box((W(220), W(120), W(80)), (0, BORE_Y + W(52), Z(84)), None))  # a half shield under the head: the sight line stays clear
    A(fixmats(gd))
    for i, (x, a) in enumerate(((-56, 0.4), (-30, -0.3), (40, 0.6), (64, -0.2))):  # clippings stuck to it
        A(cyl(W(2.6), W(24), (W(x), BORE_Y - W(40), Z(72)), grass, axis='y', seg=4, r2=W(0.4), rot=(0.4, 0, a)))
    gd_l = box((W(1), W(11), W(84)), (-W(66), BORE_Y + W(44), Z(83)), resp, rot=(0, math.pi / 2, 0))

    # ---------------- the drive shaft (barrel) with the front sight clamp and the loop handle
    A(lathe([(W(13), Z(110)), (W(13), Z(470))], (0, BORE_Y, 0), alu, seg=16, cap=False))
    A(lathe([(W(15.5), Z(FRONT_D - 10)), (W(15.5), Z(FRONT_D + 10))], (0, BORE_Y, 0), black, seg=16))
    A(side(poly([(FRONT_D - 9, 12), (FRONT_D + 9, 12), (FRONT_D + 5, 26), (FRONT_D - 5, 26)]), W(8), (0, 0, 0), black, bev=W(1)))
    for sx in (-1, 1): A(side(poly([(FRONT_D - 7, 20), (FRONT_D + 7, 20), (FRONT_D + 6, SIGHT_H + 4), (FRONT_D - 6, SIGHT_H + 4)]), W(2.4), (sx * W(7), 0, 0), black, bev=W(0.5)))
    A(box((W(3), W(SIGHT_H - 22), W(3.5)), (0, Y((SIGHT_H + 22) / 2 - 1), Z(FRONT_D)), dark))
    A(box((W(3.6), W(3.6), W(3.6)), (0, Y(SIGHT_H), Z(FRONT_D)), dot, bev=W(0.6)))
    # loop handle: a clamp on the shaft and a bent tube loop down under it, rubber on the bottom
    LZ = Z(330)
    A(side(poly([(312, -18), (350, -18), (350, 18), (312, 18)]), W(34), (0, 0, 0), black, bev=W(4)))
    loop = [(W(17), Y(-4), LZ), (W(36), Y(-30), LZ + W(4)), (W(30), Y(-86), LZ + W(10)), (0, Y(-104), LZ + W(12)), (-W(30), Y(-86), LZ + W(10)), (-W(36), Y(-30), LZ + W(4)), (-W(17), Y(-4), LZ)]
    A(sweep(loop, W(7), steel, seg=10))
    A(sweep(loop[2:5], W(10.5), rubber, seg=12))

    # ---------------- the engine (receiver): shroud, air filter + primer bulb, starter housing, muffler, plug boot, cooling fins
    A(side(poly([(410, -46), (440, -48), (740, -48), (744, -14), (726, -2), (680, 8), (640, 14), (520, 18), (470, 14), (430, 6), (410, -10)]), W(66), (0, 0, 0), orange, bev=W(12), seg=3))
    A(side(poly([(460, -50), (742, -50), (742, -64), (460, -64)]), W(70), (0, 0, 0), black, bev=W(4)))  # the crankcase / tank seat
    A(box((W(24), W(6), W(150)), (0, Y(19), Z(580)), black, bev=W(1)))  # the top rail (the sight sits on it)
    for k in range(5): A(box((W(68), W(3), W(6)), (0, Y(-14 + k * 6), Z(470 + k * 2)), black, bev=W(1)))  # cooling slots at the front
    # starter housing on the right (round, ribbed) + the cord hole
    A(cyl(W(44), W(10), (W(37), Y(-18), Z(620)), white, axis='x', seg=28, bev=W(3)))
    A(cyl(W(32), W(2), (W(42.5), Y(-18), Z(620)), black, axis='x', seg=24))
    A(cyl(W(27), W(2.4), (W(43), Y(-18), Z(620)), white, axis='x', seg=24, bev=W(1)))
    for k in range(3):
        a = k * 2 * math.pi / 3 + 0.5
        A(cyl(W(3.5), W(2), (W(44.5), Y(-18) + math.sin(a) * W(37), Z(620) + math.cos(a) * W(37)), chrome, axis='x', seg=8))
    A(cyl(W(8), W(6), (W(43), Y(4), Z(590)), black, axis='x', seg=12))
    lg = box((W(1), W(20), W(80)), (W(33.6), Y(-28), Z(530)), logo, rot=(0, 0, 0)); A(lg); decals.append((lg, (W(80), W(20)), 'x'))
    # air filter cover + primer bulb (left, where it would be on a real one) + choke lever
    A(side(poly([(500, -36), (600, -36), (606, 18), (500, 22)]), W(18), (-W(40), 0, 0), black, bev=W(5)))
    A(ball(W(10), (-W(49), Y(-6), Z(470)), mat('tr_bulb', 0xf2f0e6, rough=0.15, alpha=0.6), seg=14, rings=8))
    A(box((W(6), W(16), W(20)), (-W(52), Y(16), Z(560)), mat('tr_choke', 0xd01c2a, rough=0.3, clearcoat=0.8), bev=W(2)))
    # muffler + perforated heat guard on the left, tailpipe out the back
    A(side(poly([(620, -40), (730, -40), (730, 14), (620, 14)]), W(22), (-W(43), 0, 0), steel, bev=W(5)))
    for i in range(4):
        for j in range(3):
            A(cyl(W(3.5), W(2), (-W(54.5), Y(-26 + j * 16), Z(640 + i * 24)), dark, axis='x', seg=8))
    A(cyl(W(6), W(30), (-W(43), Y(-10), Z(744)), chrome, axis='z', seg=10))
    # spark plug boot on top behind the sight
    A(cyl(W(9), W(24), (-W(36), Y(2), Z(700)), black, axis="x", seg=12))  # spark plug boot, out the left
    A(tube([(-W(46), Y(2), Z(700)), (-W(50), Y(-6), Z(716)), (-W(44), Y(-20), Z(732))], W(3), black, seg=6))

    # ---------------- rear sight: a ghost ring on the top rail
    A(box((W(18), W(8), W(22)), (0, Y(24), Z(REAR_D)), dark, bev=W(1.2)))
    for sx in (-1, 1): A(side(poly([(REAR_D - 9, 26), (REAR_D + 9, 26), (REAR_D + 6, SIGHT_H + 5), (REAR_D - 6, SIGHT_H + 5)]), W(2.4), (sx * W(7.5), 0, 0), steel, bev=W(0.6)))
    ring = cyl(W(5.5), W(3), (0, Y(SIGHT_H), Z(REAR_D)), dark, axis='z', seg=16)
    cut(ring, cyl(W(3.4), W(10), (0, Y(SIGHT_H), Z(REAR_D)), None, axis='z', seg=12))
    A(fixmats(ring))

    # ---------------- pull-start T-handle (charge node) on the right, its cord into the starter
    chg.append(box((W(14), W(10), W(10)), (W(50), Y(8), Z(575)), black, bev=W(2)))
    chg.append(cyl(W(6.5), W(46), (W(56), Y(8), Z(575)), mat('tr_tgrip', 0xffe14d, rough=0.3, clearcoat=0.8), axis='y', seg=12, bev=W(2)))
    chg.append(tube([(W(44), Y(4), Z(590)), (W(48), Y(8), Z(580))], W(1.4), cordm, seg=6))

    # ---------------- throttle handle (pistol grip): throttle trigger, lockout on top, kill switch, the guard
    A(side(poly([(598, -62), (606, -62), (608, -84), (660, -86), (668, -62), (676, -62), (674, -94), (600, -92)]), W(12), (0, 0, 0), black, bev=W(1.5)))
    A(side(poly([(622, -62), (634, -62), (638, -72), (632, -84), (624, -82), (627, -72)]), W(7), (0, 0, 0), orange, bev=W(1.2)))  # throttle trigger
    A(side(poly([(668, -62), (722, -62), (758, -170), (752, -178), (722, -180), (712, -172), (700, -130), (704, -122), (694, -112), (696, -100), (686, -88)]),
           W(34), (0, 0, 0), black, bev=W(6), seg=2))
    A(side(poly([(684, -86), (700, -66), (722, -66), (754, -166), (726, -172), (712, -134)]), W(36), (0, 0, 0), rubber, bev=W(3)))
    A(side(poly([(676, -54), (720, -56), (722, -64), (680, -64)]), W(14), (0, 0, 0), orange, bev=W(2)))  # the lockout lever on top of the grip
    A(box((W(14), W(8), W(10)), (W(17), Y(-72), Z(690)), mat('tr_kill', 0xd01c2a, rough=0.3), bev=W(2)))  # kill switch

    # ---------------- tube stock + foam hip pad
    for sx in (-1, 1):
        A(sweep([(sx * W(16), Y(-20), Z(744)), (sx * W(16), Y(-10), Z(820)), (sx * W(18), Y(-18), Z(960)), (sx * W(18), Y(-40), Z(990))], W(6), alu, seg=10))
    A(sweep([(-W(18), Y(-40), Z(990)), (0, Y(-60), Z(995)), (W(18), Y(-40), Z(990))], W(6), alu, seg=10))
    A(rod((0, Y(-60), Z(995)), (0, Y(-150), Z(985)), W(7), alu, seg=10))
    A(side(poly([(980, 16), (1010, 16), (1010, -170), (980, -170)]), W(56), (0, 0, 0), foam, bev=W(10), seg=2))
    A(lathe([(W(9), Z(962)), (W(9), Z(980))], (0, Y(-45), 0), black, seg=12))

    # ---------------- the fuel tank (mag node, origin on its seat): see-through, pink mix inside, a black cap, a sticker
    mag.append(side(poly([(496, -60), (590, -60), (594, -78), (588, -150), (574, -164), (510, -164), (498, -150)]), W(56), (0, 0, 0), tank, bev=W(10), seg=2))
    mag.append(side(poly([(502, -96), (586, -96), (584, -148), (572, -158), (512, -158), (504, -148)]), W(48), (0, 0, 0), fuel, bev=W(8), seg=2))
    mag.append(cyl(W(16), W(16), (-W(16), Y(-90), Z(500)), black, axis='z', seg=16, bev=W(2), rot=(0, 0, 0)))
    for k in range(8):
        a = k * math.pi / 4
        mag.append(box((W(2.5), W(3), W(16)), (-W(16) + math.cos(a) * W(16), Y(-90) + math.sin(a) * W(16), Z(500)), black))
    mx = box((W(1), W(20), W(44)), (W(28.4), Y(-120), Z(545)), mix); mag.append(mx); decals.append((mx, (W(44), W(20)), 'x'))

    for p in parts + mag + chg: fixmats(p); uv_box(p, 0.04)
    gd_l.data.materials.clear(); gd_l.data.materials.append(resp)  # (not used: the guard's sticker sits better on the engine)
    bpy.data.objects.remove(gd_l, do_unlink=True)
    rs = box((W(1), W(12), W(86)), (-W(49.2), Y(-30), Z(560)), resp, rot=(0, math.pi, 0)); parts.append(rs); decals.append((rs, (W(86), W(12)), '-x'))
    for o, sz, ax in decals: decal(o, sz, ax)
    WZ = {'tr_orange': 'a', 'tr_black': 'a', 'tr_rubber': 'a', 'tr_foam': 'a', 'tr_white': 'a', 'tr_alu': 'b', 'tr_steel': 'b', 'tr_dark': 'b', 'tr_chrome': 'b'}
    bodies = zone_join(parts, 'trimmer_body', WZ, default='n', rule=lambda m, c: 'b' if m in ('tr_orange', 'tr_black') and c[2] < Z(300) else None)
    mn = moving(mag, 'mag', (0, Y(MAG_H), Z(MAG_D)), {'tr_tank': 'b', 'tr_black': 'b'}, default='n')
    cn = moving(chg, 'charge', CH, {'tr_black': 'b'}, default='n')
    meta = {'kind': 'weapon', 'id': 'autoshot', 'skin': 'autoshot_trimmer', 'paint': ['tr_orange'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': Y(SIGHT_H), 'z': Z(REAR_D) + 0.06}, 'hatAt': [[0, Y(22), Z(540)], 0.12],
            'mag': {'node': 'mag'}, 'charge': {'node': 'charge'}}
    return finish('w_autoshot_trimmer', bodies + [mn, cn], meta)


main(build, 'w_autoshot_trimmer')
