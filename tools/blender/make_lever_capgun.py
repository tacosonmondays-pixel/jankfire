# Cap Gun (lever_capgun): a 1960s toy cowboy cap rifle as the Yeehaw, built on the Yeehaw's own Winchester layout
# (x1.24, so the lever pin, hammer pin, sight line and muzzle stay put) with toy proportions: a fat chrome-plastic
# barrel with the orange safety plug, a die-cast receiver with moulded scrollwork, the cap door on the right open on a
# roll of red paper caps (the strip feeds up over the anvil under the hammer), a moulded "wood" plastic stock and forend
# with a seam line, screws and a gold horse-head medallion, a chunky loop lever and a big hammer spur.
# Moving parts like the Yeehaw: 'lever' (origin on its front pin, +rotation.x throws it open) and 'lhammer' (origin on
# the hammer pin, +rotation.x cocks it back; it rests down). Made fun: ☺ CORP FRONTIER, CAPS ONLY, a BANG! sticker.
# run: blender -b --python tools/blender/make_lever_capgun.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corp import *

LV = Scale(1.24, 0.02, -0.71)
Z, Y, W, poly, S = LV.Z, LV.Y, LV.W, LV.poly, LV.S
BORE_Y, MUZ_Z = 0.02, -0.71
LEVER_PIV = (0, -0.04, -0.02)
HAMMER_PIV = (0, 0.03, 0.09)
LV_D, LV_H = (LEVER_PIV[2] - MUZ_Z) / S, (LEVER_PIV[1] - BORE_Y) / S
REAR_D = (-0.2 - MUZ_Z) / S
SIGHT_H = (0.06 - BORE_Y) / S
OPEN = '--open' in sys.argv


def build():
    def scroll_px(px):  # moulded scrollwork on the die-cast: swirls pressed into chrome
        h, w = px.shape[:2]
        px[:] = hexrgb(0xc8ccd6)
        yy, xx = np.mgrid[0:h, 0:w]
        for cx, cy, r in ((10, 10, 8), (30, 18, 9), (50, 9, 7), (18, 26, 6), (42, 28, 6)):
            d = np.hypot(xx - cx, yy - cy); a = np.arctan2(yy - cy, xx - cx)
            m = (np.abs(((d - a * 1.6) % 4) - 2) < 0.7) & (d < r)
            px[m] = hexrgb(0x7a7e8a)
    chromeplast = mat('cg_chrome', 0xc8ccd6, rough=0.18, metal=0.9, tex=tex_canvas('cg_scroll_t', 60, 34, scroll_px))
    barrelm = mat('cg_barrel', 0xb8bcc8, rough=0.14, metal=0.95)
    dark = mat('cg_dark', 0x2a2c34, rough=0.4, metal=0.6)
    fakewood = mat('cg_wood', 0xb8642a, rough=0.24, clearcoat=0.9, tex=tex_wood('cg_wood_t', 0xc0702e, 0x8a3e14, size=32, seed=1001, rings=2))
    orange = plastic('cg_orange', 0xff6a10, rough=0.3, cc=0.6, seed=1002)
    redcap = mat('cg_caps', 0xd81a1a, rough=0.6, tex=tex_noise('cg_caps_t', 0xd81a1a, var=0.1, size=16, seed=1003))
    capdot = mat('cg_capdot', 0x6a1010, rough=0.7)
    gold = mat('cg_gold', 0xffc83a, rough=0.18, metal=1.0)
    yellow = plastic('cg_yellow', 0xffe14d, rough=0.25, cc=0.9, seed=1004)
    black = mat('cg_black', 0x0a0a0a, rough=0.4)
    bead = mat('cg_bead', 0xffe14d, rough=0.2, emit=0xffd040, strength=1.8)
    def brand_px(px):
        px[:] = hexrgb(0x8a3e14); px[1:-1, 1:-1] = hexrgb(0xa8541e)
        smiley_px(px, 2, 3, 1, 0xffe14d); text_px(px, 'CORP FRONTIER', 12, 3, 1, 0xffe14d); text_px(px, 'CAPS ONLY', 12, 12, 1, 0xffe14d)
    brand = mat('cg_brand', 0xffffff, rough=0.3, clearcoat=0.8, tex=tex_canvas('cg_brand_t', 92, 21, brand_px))
    def bang_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xffe14d)
        for k in range(16):  # a starburst
            a = 2 * math.pi * k / 16
            px_line(px, w / 2, h / 2, w / 2 + math.cos(a) * w / 2, h / 2 + math.sin(a) * h / 2, 0xff2a1a if k % 2 else 0xffe14d, 3)
        px_disc(px, w / 2, h / 2, h * 0.34, 0xff2a1a)
        text_px(px, 'BANG!', int(w / 2) - 14, int(h / 2) - 3, 1, 0xffffff)
    bang = mat('cg_bang', 0xffffff, rough=0.3, tex=tex_canvas('cg_bang_t', 40, 28, bang_px))
    parts, lever, ham, decals = [], [], [], []
    A = parts.append

    # ---------------- fat toy barrel with the orange plug, a front sight with a gold bead, the moulded mag tube under it
    A(lathe([(W(4), Z(14)), (W(4), Z(0)), (W(10), Z(0)), (W(11.5), Z(1)), (W(11.5), Z(26))], (0, BORE_Y, 0), orange, seg=18))
    A(cyl(W(4.2), W(1), (0, BORE_Y, Z(0.2)), black, axis='z', seg=10))
    A(lathe([(W(10.5), Z(26)), (W(10.5), Z(300)), (W(11.5), Z(500))], (0, BORE_Y, 0), barrelm, seg=18, cap=False))
    A(side(poly([(36, 8), (60, 8), (58, 14), (40, 18), (36, 14)]), W(9), (0, 0, 0), barrelm, bev=W(1)))
    A(side(poly([(42, 16), (54, 16), (51, SIGHT_H - 3), (45, SIGHT_H - 3)]), W(3.5), (0, 0, 0), barrelm, bev=W(0.6)))
    A(ball(W(3), (0, Y(SIGHT_H - 2.5), Z(48)), bead, seg=10, rings=6))
    TB = -20
    A(lathe([(W(7.5), Z(40)), (W(7.5), Z(492))], (0, Y(TB), 0), barrelm, seg=14))
    A(lathe([(0, Z(32)), (W(6.5), Z(32)), (W(8), Z(34)), (W(8), Z(42))], (0, Y(TB), 0), orange, seg=14))
    for d in (80, 300): A(box((W(22), W(44), W(12)), (0, Y(-6), Z(d)), barrelm, bev=W(5), seg=2))
    # buckhorn rear sight, toy chunky
    A(box((W(14), W(6), W(18)), (0, Y(12), Z(REAR_D)), barrelm, bev=W(1)))
    A(side([(Z(REAR_D) - W(2), Y(12)), (Z(REAR_D) + W(2), Y(12)), (Z(REAR_D) + W(2), Y(SIGHT_H + 6)), (Z(REAR_D) - W(2), Y(SIGHT_H + 6))], W(36), (0, 0, 0), barrelm, bev=W(0.8),
           holes=[[(Z(REAR_D) - W(5), Y(SIGHT_H)), (Z(REAR_D) + W(5), Y(SIGHT_H)), (Z(REAR_D) + W(5), Y(SIGHT_H + 10)), (Z(REAR_D) - W(5), Y(SIGHT_H + 10))]]))

    # ---------------- forend: moulded fake wood with a seam line and grooves
    A(side(poly([(304, 4), (488, 6), (488, -34), (304, -32)]), W(34), (0, 0, 0), fakewood, bev=W(9), seg=2))
    A(box((W(36), W(1.5), W(180)), (0, Y(-14), Z(396)), black))  # the mould seam
    for k in range(3): A(box((W(36.2), W(2), W(14)), (0, Y(-22), Z(330 + k * 50)), dark, bev=W(0.6), seg=1))

    # ---------------- receiver: die-cast chrome with scrollwork, the cap door open on the right, the roll of caps, the anvil
    rc = side(poly([(490, -36), (490, 12), (497, 18), (640, 18), (654, 16), (664, 6), (664, -42), (656, -52), (500, -52), (490, -44)]), W(34), (0, 0, 0), chromeplast, bev=W(3))
    cut(rc, box((W(14), W(36), W(40)), (0, Y(18), Z(646)), None))  # hammer slot
    cut(rc, cyl(W(19), W(12), (W(17), Y(-16), Z(560)), None, axis='x', seg=20))  # the cap chamber (right)
    A(fixmats(rc))
    A(cyl(W(18.5), W(1.5), (W(11.5), Y(-16), Z(560)), dark, axis='x', seg=20))
    A(cyl(W(15), W(10), (W(13), Y(-16), Z(560)), redcap, axis='x', seg=20))  # the roll
    A(cyl(W(4), W(11), (W(13.5), Y(-16), Z(560)), dark, axis='x', seg=10))
    # the cap door: hinged at its front edge, swung open forward
    dr = side([(0, -W(14)), (0, W(14)), (W(40), W(14)), (W(40), -W(14))], W(2.5), (0, 0, 0), chromeplast, bev=W(0.8))
    dr.location = gv(W(18.8), Y(-16), Z(538)); dr.rotation_euler = (0, 0, math.radians(55))
    A(dr)
    A(cyl(W(2.5), W(30), (W(18), Y(-16), Z(538)), dark, axis='y', seg=8))
    # the strip of caps running up the right of the receiver into the anvil under the hammer
    strip = [(W(15), Y(2), Z(566)), (W(14), Y(14), Z(590)), (W(6), Y(19), Z(620)), (0, Y(19.5), Z(640))]
    st = sweep(strip, W(5), redcap, seg=4, squash=(0.12, 1.0), smooth_angle=20)
    A(st)
    for k in range(4):
        p = strip[min(k, 3)]
        A(ball(W(2.2), (p[0], p[1] + W(0.8), p[2]), capdot, seg=8, rings=5, scale=(1, 0.5, 1)))
    A(box((W(10), W(5), W(10)), (0, Y(17), Z(640)), dark, bev=W(1)))  # the anvil
    for d, h in ((520, -34), (616, -32), (646, -40), (600, -8)):
        for sx in (-1, 1): A(cyl(W(3), W(1.5), (sx * W(17.2), Y(h), Z(d)), gold, axis='x', seg=8))
    # tangs + trigger (gold, toy-chunky)
    A(side(poly([(652, 16), (734, 10), (738, 6), (664, 5)]), W(17), (0, 0, 0), chromeplast, bev=W(2)))
    A(side(poly([(662, -38), (740, -36), (742, -42), (662, -48)]), W(19), (0, 0, 0), chromeplast, bev=W(2)))
    A(side(poly([(682, -48), (690, -48), (693, -58), (689, -72), (683, -70), (685, -58)]), W(7), (0, 0, 0), gold, bev=W(1.2)))

    # ---------------- the stock: moulded fake wood, seam, butt plate, the horse-head medallion, brand plate, BANG!
    crest = [(954, -22), (947, -50), (944, -85), (946, -120), (954, -150)]
    stk = side(poly([(664, 5), (738, 6), (772, 2), (954, -22)] + crest[1:] + [(940, -152), (770, -52), (742, -42), (664, -38)]), W(40), (0, 0, 0), fakewood, bev=W(9), seg=2)
    A(stk)
    A(side(poly(crest + [(950, -156), (962, -160), (966, -151), (960, -120), (958, -85), (961, -50), (967, -24), (962, -16), (953, -17)]), W(40), (0, 0, 0), dark, bev=W(2)))
    A(side(poly([(770, 0), (954, -21), (954, -25), (770, -4)]), W(41), (0, 0, 0), black))  # seam along the top
    # the horse-head medallion on the left (a little relief: head + neck + ear + mane)
    hx = -W(20.8)
    A(cyl(W(20), W(2), (hx, Y(-62), Z(850)), gold, axis='x', seg=24, bev=W(0.6)))
    horse = side(poly([(842, -76), (838, -62), (840, -52), (848, -46), (852, -40), (856, -46), (862, -52), (866, -62), (862, -66), (856, -62), (852, -70), (852, -78)]), W(2), (hx - W(1.6), 0, 0), dark, bev=W(0.5))
    A(horse)
    bp = box((W(1), W(21), W(92)), (W(20.4), Y(-34), Z(840)), brand); A(bp); decals.append((bp, (W(92), W(21)), 'x'))
    bg = box((W(1), W(24), W(34)), (W(17.6), Y(-14), Z(440)), bang); A(bg); decals.append((bg, (W(34), W(24)), 'x'))

    # ---------------- the hammer (its own node), resting down, a big toy spur
    ham.append(side(poly([(634, -4), (654, -4), (656, 10), (653, 22), (658, 30), (674, 38), (686, 42), (688, 34), (670, 26), (648, 22), (640, 12)]), W(9), (0, 0, 0), barrelm, bev=W(1.2)))
    for k in range(4): ham.append(box((W(10), W(1.4), W(1.8)), (0, Y(32 + k * 2), Z(664 + k * 5)), dark, rot=(-0.35, 0, 0)))

    # ---------------- the loop lever (its own node, pivot on the front pin): chrome with a yellow plastic loop grip
    outer = [(546, -40), (556, -37), (660, -38), (690, -40), (706, -36.5), (716, -38), (720, -46), (728, -62), (740, -86), (744, -108), (738, -130), (720, -146), (690, -154), (650, -154), (612, -147), (588, -131), (576, -108), (572, -84), (566, -62), (556, -59), (546, -52)]
    hole = [(586, -60), (698, -56), (712, -64), (724, -86), (728, -106), (722, -126), (706, -138), (684, -144), (652, -144), (622, -138), (602, -124), (591, -106), (587, -84)]
    lever.append(side(poly(outer), W(10), (0, 0, 0), barrelm, bev=W(1.5), holes=[poly(hole)]))
    lever.append(cyl(W(5), W(13), (0, Y(LV_H), Z(LV_D)), gold, axis='x', seg=10))
    wrap = [(578, -92), (580, -110), (590, -128), (610, -142), (640, -150), (670, -150), (700, -146), (722, -136)]
    lever.append(sweep([(0, Y(h), Z(d)) for d, h in wrap], [W(r) for r in (6, 8, 8.6, 8.6, 8.6, 8.6, 8, 6)], yellow, seg=10, squash=(1.0, 0.9)))

    for p in parts + lever + ham: fixmats(p); uv_box(p, {fakewood: 0.09, chromeplast: 0.06}.get(p.data.materials[0] if p.data.materials else None, 0.035))
    for o, sz, ax in decals: decal(o, sz, ax)
    WZ = {'cg_wood': 'a', 'cg_chrome': 'a', 'cg_dark': 'a', 'cg_barrel': 'b', 'cg_orange': 'b', 'cg_black': 'b'}
    bodies = zone_join(parts, 'capgun_body', WZ, default='n')
    lv = moving(lever, 'lever', LEVER_PIV, {'cg_barrel': 'b', 'cg_yellow': 'a'}, default='n')
    hn = moving(ham, 'lhammer', HAMMER_PIV, {'cg_barrel': 'b', 'cg_dark': 'b'}, default='n')
    meta = {'kind': 'weapon', 'id': 'lever', 'skin': 'lever_capgun', 'paint': ['cg_wood'], 'muzzle': [0, BORE_Y, MUZ_Z], 'sight': {'y': Y(SIGHT_H), 'z': Z(REAR_D)},
            'hatAt': [[0, Y(19), Z(560)], 0.1], 'lever': {'node': 'lever'}, 'lhammer': {'node': 'lhammer'}}
    root = finish('w_lever_capgun', bodies + [lv, hn], meta)
    if OPEN:
        lv.rotation_euler.x = 0.95
        hn.rotation_euler.x = 0.75
    return root


if OPEN:
    reset(); r = build(); sheet(r, 'w_lever_capgun_open', extra_note='LEVER THROWN')
else:
    main(build, 'w_lever_capgun')
