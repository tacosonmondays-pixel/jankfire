# Take A Number (burst_ticket): the deli counter's red ticket dispenser as the Hat Trick's bullpup, in the Hat
# Trick's own millimetres (x1.6): the dispenser's rounded red shell is the whole bullpup body (the ticket roll lives
# behind the grip, like a bullpup's mag), a ticket hanging out of the mouth on top, a queue stanchion as the barrel
# (polished chrome post, the belt cassette head as the handguard with a stub of QUEUE HERE belt), and the carry
# handle is the NOW SERVING sign with its glowing red digits, the sights inside it like the FAMAS. Moving parts:
# 'mag' = a fresh roll of numbered tickets (origin on its seat) and 'charge' = the yellow PULL tab (slides back).
# Made fun: ☺ CORP DELI, PLEASE WAIT, and every ticket says 3 (it fires in threes).
# run: blender -b --python tools/blender/make_burst_ticket.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corp import *

BU = Scale(1.6, 0.012, -0.67)
Z, Y, W, poly = BU.Z, BU.Y, BU.W, BU.poly
BORE_Y, MUZ_Z = 0.012, -0.67
SIGHT_H = 83
REAR_D, FRONT_D = 494, 228
MAG_D, MAG_H = 463, -46
CH_D, CH_H = 356, 33


def build():
    red = plastic('tk_red', 0xd8182a, rough=0.16, cc=1.0, var=0.04, seed=701, speck=0xff5060, speck_p=0.03)
    white = plastic('tk_white', 0xf2f0ea, rough=0.3, cc=0.6, seed=702)
    black = plastic('tk_black', 0x15151a, rough=0.45, cc=0.4, seed=703)
    chrome = mat('tk_chrome', 0xe2e6ee, rough=0.1, metal=1.0)
    dark = mat('tk_dark', 0x101014, rough=0.5, metal=0.3)
    yellow = plastic('tk_yellow', 0xffe14d, rough=0.22, cc=1.0, seed=704)
    paper = mat('tk_paper', 0xf6eedc, rough=0.8, tex=tex_noise('tk_paper_t', 0xf6eedc, var=0.05, size=16, seed=705))
    velvet = mat('tk_belt', 0x8a1a3a, rough=0.7, tex=tex_stripes('tk_belt_t', 0x8a1a3a, 0x6a1028, size=16, width=2, diag=False))
    dot = mat('tk_dot', 0x7dff4f, rough=0.4, emit=0x7dff4f, strength=4.0)
    led_off = mat('tk_ledoff', 0x2a0808, rough=0.3)
    def seg7(px, x0, y0, digit, on, off, s=2):  # a 7-segment digit, s px thick
        segs = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcfgd'}[digit]
        L = 5 * s
        geo = {'a': (x0 + s, y0, L, s), 'g': (x0 + s, y0 + L + s, L, s), 'd': (x0 + s, y0 + 2 * L + 2 * s, L, s),
               'f': (x0, y0 + s, s, L), 'b': (x0 + L + s, y0 + s, s, L), 'e': (x0, y0 + L + 2 * s, s, L), 'c': (x0 + L + s, y0 + L + 2 * s, s, L)}
        for k, (x, y, w, h) in geo.items(): px[y:y + h, x:x + w] = hexrgb(on if k in segs else off)
    def sign(px):
        px[:] = hexrgb(0x120606)
        text_px(px, 'NOW SERVING', 3, 2, 1, 0xffe14d)
        seg7(px, 18, 12, '0', 0xff2a1a, 0x3a0c0c); seg7(px, 34, 12, '3', 0xff2a1a, 0x3a0c0c)
    signm = mat('tk_sign', 0xffffff, rough=0.2, tex=tex_canvas('tk_sign_t', 70, 40, sign), emit=0xffffff, strength=1.6, emit_tex=True)
    def logo(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xd8182a)
        text_px(px, 'TAKE A', 16, 2, 2, 0xffffff); text_px(px, 'NUMBER', 16, 18, 2, 0xffffff)
        smiley_px(px, 1, 9, 2, 0xffe14d)
        text_px(px, 'CORP DELI', 18, 35, 1, 0xffe14d)
    logom = mat('tk_logo', 0xffffff, rough=0.16, clearcoat=1.0, tex=tex_canvas('tk_logo_t', 92, 44, logo))
    def ticket(px):
        px[:] = hexrgb(0xf6eedc); px[:, :1] = px[:, -1:] = hexrgb(0xd8182a)
        text_px(px, '3', 4, 3, 2, 0xd8182a)
    ticketm = mat('tk_ticket', 0xffffff, rough=0.7, tex=tex_canvas('tk_ticket_t', 18, 20, ticket))
    def roll_edge(px):  # the roll's face: rings of tickets with red edges
        h, w = px.shape[:2]
        px[:] = hexrgb(0xf6eedc)
        for r in range(3, w // 2, 3): px_disc(px, w / 2, h / 2, r + 0.6, 0xe8c8b8, r_in=r)
        px_disc(px, w / 2, h / 2, 7, 0x15151a)
    rollm = mat('tk_rollface', 0xffffff, rough=0.8, tex=tex_canvas('tk_roll_t', 40, 40, roll_edge))
    wait = mat('tk_wait', 0xffffff, rough=0.3, tex=label_tex('tk_wait_t', 76, 14, [('PLEASE WAIT', None)], bg=0xffe14d))
    parts, mag, chg, decals = [], [], [], []
    A = parts.append

    # ---------------- the barrel: a queue stanchion post (chrome), a domed top as the muzzle, the base ring at the guard
    A(lathe([(0.0, Z(-1)), (W(9), Z(-1)), (W(17), Z(1)), (W(22), Z(7)), (W(23), Z(14)), (W(20), Z(22)), (W(14), Z(28))], (0, BORE_Y, 0), chrome, seg=22))  # the post's dome
    A(cyl(W(6), W(1), (0, BORE_Y, Z(-1.2)), dark, axis='z', seg=10))
    A(lathe([(W(14), Z(28)), (W(14), Z(176))], (0, BORE_Y, 0), chrome, seg=20, cap=False))
    A(lathe([(W(14.5), Z(66)), (W(17), Z(70)), (W(17), Z(80)), (W(14.5), Z(84))], (0, BORE_Y, 0), black, seg=20))
    # the belt cassette head = the handguard: a chrome drum, black caps, the belt slot with a stub of belt, finger ribs
    hg = lathe([(W(18), Z(176)), (W(26), Z(182)), (W(28), Z(192)), (W(28), Z(290)), (W(26), Z(298)), (W(18), Z(304))], (0, BORE_Y - W(4), 0), chrome, seg=24)
    hg.scale = (1.0, 1.0, 1.15)
    A(hg)
    for d in (184, 296): A(lathe([(W(28.6), Z(d - 5)), (W(28.6), Z(d + 5))], (0, BORE_Y - W(4), 0), black, seg=24, cap=False))
    A(box((W(4), W(40), W(8)), (W(28), Y(-4), Z(240)), dark))
    A(box((W(4), W(42), W(12)), (W(31), Y(-4), Z(240)), velvet))
    bpts = [(W(31), Y(-4), Z(240)), (W(46), Y(-6), Z(248)), (W(54), Y(-16), Z(262)), (W(56), Y(-34), Z(268))]
    A(sweep(bpts, W(19), velvet, seg=4, squash=(1.0, 0.1), smooth_angle=20))
    A(box((W(10), W(30), W(5)), (W(56), Y(-40), Z(268)), chrome, bev=W(1)))  # the belt's clip end
    for k in range(5): A(box((W(46), W(3), W(5)), (0, Y(-40), Z(206 + k * 18)), black, bev=W(1)))

    # ---------------- the dispenser shell = the body: rounded red, the ticket mouth on top, a black sole
    body = side(poly([(292, 22), (548, 24), (566, 34), (600, 46), (700, 48), (738, 36), (752, 10), (754, -60), (742, -92), (716, -110), (690, -104),
                      (560, -64), (500, -44), (420, -44), (292, -40)]), W(64), (0, 0, 0), red, bev=W(14), seg=3)
    A(body)
    A(side(poly([(506, -48), (560, -66), (690, -106), (716, -112), (740, -94), (748, -84), (712, -98), (690, -94), (560, -54), (508, -38)]), W(66), (0, 0, 0), black, bev=W(3)))
    A(side(poly([(752, 8), (760, 6), (760, -62), (752, -64)]), W(50), (0, 0, 0), black, bev=W(3)))  # butt pad
    for sx in (-1, 1):  # TAKE A NUMBER panels on both sides
        lg = box((W(1), W(44), W(92)), (sx * W(32.2), Y(-6), Z(640)), logom, rot=(0, 0 if sx > 0 else math.pi, 0)); A(lg); decals.append((lg, (W(92), W(44)), 'x' if sx > 0 else '-x'))
    # the ticket mouth (on the right, where you see it) and a ticket hanging out of it, curling down
    A(side(poly([(318, -18), (392, -18), (392, 8), (318, 8)]), W(8), (W(31), 0, 0), black, bev=W(2)))
    A(box((W(2), W(4), W(54)), (W(35.2), Y(-5), Z(355)), dark))
    tk = sweep([(W(35), Y(-5), Z(355)), (W(44), Y(-6), Z(355)), (W(52), Y(-14), Z(355)), (W(56), Y(-30), Z(355)), (W(56), Y(-44), Z(355))], W(22), ticketm, seg=4, squash=(0.06, 1.0), smooth_angle=20)
    A(tk)
    # ---------------- NOW SERVING sign = the carry handle: two legs, the sign box with digits both sides, sights inside
    ch = side(poly([(212, 18), (250, 18), (262, 46), (580, 46), (604, 40), (640, 40), (640, 62), (214, 62), (210, 50)]), W(24), (0, 0, 0), black, bev=W(3), seg=2,
              holes=[poly([(262, 30), (268, 46), (560, 46), (590, 40), (592, 30)])])
    A(ch)
    for sx in (-1, 1):  # the sign is two panels, one each side, with the sight tunnel between them
        A(side(poly([(276, 60), (470, 60), (470, 96), (276, 96)]), W(7), (sx * W(13), 0, 0), red, bev=W(2)))
        sg = box((W(1), W(30), W(184)), (sx * W(16.6), Y(78), Z(373)), signm, rot=(0, 0 if sx > 0 else math.pi, 0)); A(sg); decals.append((sg, (W(184), W(30)), 'x' if sx > 0 else '-x'))
        A(box((W(3), W(30), W(184)), (sx * W(9.8), Y(78), Z(373)), dark))  # the dark inside of the tunnel
    for sx in (-1, 1):  # front sight wings, post, dot (in front of the sign)
        A(side(poly([(218, 62), (240, 62), (238, 90), (226, 90)]), W(4), (sx * W(9), 0, 0), chrome, bev=W(1)))
    A(box((W(2.6), W(20), W(2.4)), (0, Y(SIGHT_H - 11), Z(FRONT_D)), dark))
    A(box((W(4.4), W(4.2), W(4.2)), (0, Y(SIGHT_H - 0.5), Z(FRONT_D)), dot, bev=W(0.6)))
    A(side(poly([(480, 62), (510, 62), (508, 68), (482, 68)]), W(17), (0, 0, 0), chrome, bev=W(1.5)))
    for sx in (-1, 1): A(side(poly([(486, 66), (502, 66), (500, 90), (490, 90)]), W(2.6), (sx * W(8), 0, 0), chrome, bev=W(0.7)))
    ring = cyl(W(6), W(3), (0, Y(SIGHT_H), Z(REAR_D)), dark, axis='z', seg=16)
    cut(ring, cyl(W(3.4), W(10), (0, Y(SIGHT_H), Z(REAR_D)), None, axis='z', seg=12))
    A(fixmats(ring))
    A(box((W(3), W(11), W(1.6)), (0, Y(SIGHT_H - 11), Z(REAR_D)), dark))
    # the slot the PULL tab runs in
    A(box((W(10), W(1.2), W(110)), (0, Y(22.3), Z(392)), dark))

    # ---------------- the PULL tab (charge node, slides back along +z)
    chg.append(box((W(7), W(16), W(14)), (0, Y(28), Z(CH_D)), chrome, bev=W(1.2)))
    chg.append(box((W(36), W(10), W(16)), (0, Y(38), Z(CH_D)), yellow, bev=W(3), seg=2))
    pl = box((W(30), W(1), W(12)), (0, Y(43.1), Z(CH_D)), mat('tk_pull', 0xffffff, rough=0.3, tex=label_tex('tk_pull_t', 26, 11, [('PULL', None)], bg=0xffe14d, smile=False)))
    chg.append(pl)

    # ---------------- full-hand trigger guard, trigger, pistol grip (white handle, like the counter's)
    A(side(poly([(266, -32), (424, -32), (424, -56), (414, -150), (398, -162), (300, -162), (280, -150), (266, -62)]), W(16), (0, 0, 0), black, bev=W(3),
           holes=[poly([(282, -44), (404, -44), (398, -148), (298, -148), (284, -136)])]))
    A(side(poly([(306, -36), (314, -36), (318, -50), (313, -64), (306, -62), (310, -50)]), W(6), (0, 0, 0), yellow, bev=W(1)))
    A(side(poly([(334, -38), (388, -38), (402, -148), (396, -150), (352, -150), (348, -136), (342, -112), (346, -102), (338, -88), (342, -76), (334, -62)]),
           W(32), (0, 0, 0), white, bev=W(6), seg=3))
    wt = box((W(1), W(14), W(76)), (W(32.3), Y(4), Z(470)), wait); A(wt); decals.append((wt, (W(76), W(14)), 'x'))

    # ---------------- the mag: a fresh roll of tickets in a black yoke, its tongue running up into the seat
    A(side(poly([(424, -36), (500, -36), (500, -50), (424, -50)]), W(38), (0, 0, 0), black, bev=W(2)))
    RZ, RY, RR = Z(468), Y(-120), W(44)
    mag.append(cyl(RR, W(30), (0, RY, RZ), paper, axis='x', seg=26))
    for sx in (-1, 1):
        f = cyl(RR - W(0.5), W(0.6), (sx * W(15.3), RY, RZ), rollm, axis='x', seg=26); mag.append(f)
        mag.append(side(poly([(446, -48), (482, -48), (488, -120), (476, -132), (456, -132), (444, -120)]), W(3), (sx * W(18), 0, 0), black, bev=W(1)))
    mag.append(cyl(W(6), W(42), (0, RY, RZ), chrome, axis='x', seg=12))
    tongue = sweep([(0, RY + RR - W(1), RZ - W(6)), (0, Y(-60), Z(466)), (0, Y(-46), Z(464))], W(14), ticketm, seg=4, squash=(1.0, 0.08), smooth_angle=20)
    mag.append(tongue)
    mag.append(box((W(32), W(6), W(40)), (0, Y(-48), Z(463)), black, bev=W(1.5)))

    for p in parts + mag + chg: fixmats(p); uv_box(p, 0.04)
    for o, sz, ax in decals: decal(o, sz, ax)
    decal(pl, (W(30), W(12)), 'y')
    for f in mag:
        if f.data.materials and f.data.materials[0] is rollm: decal(f, (2 * RR, 2 * RR), 'x')
    for o, n in ((tk, W(56)), (tongue, W(60))):
        me = o.data
        if o is tk:  # the hanging ticket: seen from the right, u along z, v down the drop
            for poly_ in me.polygons:
                for li in poly_.loop_indices:
                    v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
                    gx, gy, gz = v.x, v.z, -v.y
                    me.uv_layers.active.data[li].uv = (0.5 - (gz - Z(355)) / W(44), 1 + (gy - Y(-5) - (gx - W(35))) / W(50))
            continue
        for poly_ in me.polygons:
            for li in poly_.loop_indices:
                v = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
                gx, gy, gz = v.x, v.z, -v.y
                me.uv_layers.active.data[li].uv = (0.5 + gx / W(17), (gy + gz) / W(20))
    WZ = {'tk_red': 'a', 'tk_white': 'a', 'tk_black': 'a', 'tk_chrome': 'b', 'tk_dark': 'b', 'tk_belt': 'b'}
    bodies = zone_join(parts, 'ticket_body', WZ, default='n', rule=lambda m, c: 'b' if m == 'tk_black' and c[2] < Z(310) else None)
    mn = moving(mag, 'mag', (0, Y(MAG_H), Z(MAG_D)), {'tk_paper': 'b', 'tk_black': 'b', 'tk_chrome': 'b'}, default='n')
    cn = moving(chg, 'charge', (0, Y(CH_H), Z(CH_D)), {'tk_chrome': 'b', 'tk_yellow': 'b'}, default='n')
    meta = {'kind': 'weapon', 'id': 'burst', 'skin': 'burst_ticket', 'paint': ['tk_red'], 'muzzle': [0, BORE_Y, MUZ_Z],
            'sight': {'y': Y(SIGHT_H), 'z': Z(REAR_D)}, 'hatAt': [[0, Y(64), Z(560)], 0.12],
            'mag': {'node': 'mag'}, 'charge': {'node': 'charge'}}
    return finish('w_burst_ticket', bodies + [mn, cn], meta)


main(build, 'w_burst_ticket')
