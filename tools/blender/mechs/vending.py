# VENDING MACHINE: the support hero (docs/mechs/ROSTER.md). An original JANKFIRE hero: a 5 m vending machine
# waddling on stubby legs. A glass door full of glowing drinks on shelves, a chrome coin panel for a face (two button
# eyes, the coin slot as its mouth, a keypad chin), a lit JANK COLA marquee for a hat, a delivery flap, short arms
# with mitten hands, heel jets, and an OUT OF ORDER sign stowed on its back that it slams down in front of itself.
# Clean look (the owner's references): glossy paint, pink trims, chrome, few strong glows.
# Game space: faces -z, its right is +x, feet on y = 0. Body joint at the cabinet's bottom middle.
from mechkit import *
import herokit

FID = 'mech_vending'
W, D = 1.10, 0.78  # cabinet half width, half depth
Y0, Y1 = 0.98, 4.56  # cabinet bottom, top
ZF = -D  # the front face
PAL_A = {  # "FIZZ": cyan cabinet, hot pink trims, white, chrome, warm drinks glow
    'paint': 0x27c6e6, 'paint2': 0xff4fbf, 'white': 0xf4f2ee, 'dark': 0x1a1a24, 'accent': 0xffd23a, 'frame': 0x40464f,
    'chrome': 0xd8dee6, 'rubber': 0x18181c, 'glass': 0x0c1222, 'glow': 0xfff1c8, 'glow2': 0x7df9ff, 'thrust': 0x7df9ff,
    'can_r': 0xe8202a, 'can_y': 0xffd23a, 'can_g': 0x39d353, 'can_b': 0x2f55e8, 'hazard': 0xffd23a,
}
PAL_B = {  # "DIET": pink cabinet, cyan trims, green glow
    'paint': 0xff4fbf, 'paint2': 0x27c6e6, 'white': 0xf4f0ec, 'dark': 0x1c1420, 'glow2': 0x7dff4f, 'thrust': 0x9dff6a,
}
for k in ('can_r', 'can_y', 'can_g', 'can_b'): ROLE_LOOK.setdefault(k, (0.28, 0.6, 0.6))
ROLE_LOOK.setdefault('hazard', (0.30, 0.0, 1.0))
NUMBER = '99P'

JT = {
    'hips': (0, 0.86, 0.0), 'body': (0, Y0, 0.0), 'marquee': (0, Y1, 0.0), 'door': (-1.00, 2.95, ZF - 0.02),
    'flap': (-0.32, 1.44, ZF - 0.02), 'sign': (0, 3.02, D + 0.06),
    'shoulder': (1.16, 3.34, 0.0), 'upperarm': (1.30, 3.30, 0.0), 'forearm': (1.40, 2.66, 0.02), 'hand': (1.44, 2.04, 0.0),
    'thigh': (0.56, 0.84, 0.0), 'shin': (0.58, 0.52, 0.02), 'foot': (0.60, 0.22, 0.04),
}


def J(n, s=1): return mx(JT[n], s)


# ------------------------------------------------------------ textures
def marquee_img():
    w, h = 256, 64; px = canvas(w, h, 0xff4fbf)
    fill(px, 6, 6, w - 6, h - 6, 0x2a0a22)
    text_c(px, 'JANK COLA', w // 2, 14, 4, 0xffe14d)
    for x in range(10, w - 10, 12): fill(px, x, 2, x + 6, 5, 0xffffff); fill(px, x, h - 5, x + 6, h - 2, 0xffffff)  # (chase lights)
    return image_rgba('vm_marquee', px)


def sign_img():
    w, h = 256, 160; px = canvas(w, h, 0xf6f4ee)
    stripes(px, 0, 0, w, 16, 0xffd23a, 0x111111, 12); stripes(px, 0, h - 16, w, h, 0xffd23a, 0x111111, 12)
    text_c(px, 'OUT OF', w // 2, 34, 6, 0x111111); text_c(px, 'ORDER', w // 2, 84, 6, 0xe8202a)
    text_c(px, 'SORRY :<', w // 2, 136, 2, 0x111111)
    return image_rgba('vm_sign', px)


def price_img():
    w, h = 64, 24; px = canvas(w, h, 0x0a1a10)
    text_c(px, '99P', w // 2, 5, 2, 0x7dff4f)
    return image_rgba('vm_price', px)


# ------------------------------------------------------------ build
def build():
    mk = Mech(FID, 'vm', PAL_A); M = mk.M
    mk.joint('root', (0, 0, 0)); mk.joint('hips', JT['hips'], 'root'); mk.joint('body', JT['body'], 'hips')
    for n in ('marquee', 'door', 'flap', 'sign'): mk.joint(n, JT[n], 'body')
    for s, L in ((1, 'R'), (-1, 'L')):
        mk.joint('shoulder_' + L, J('shoulder', s), 'body'); mk.joint('upperarm_' + L, J('upperarm', s), 'shoulder_' + L)
        mk.joint('forearm_' + L, J('forearm', s), 'upperarm_' + L); mk.joint('hand_' + L, J('hand', s), 'forearm_' + L)
        mk.joint('thigh_' + L, J('thigh', s), 'hips'); mk.joint('shin_' + L, J('shin', s), 'thigh_' + L); mk.joint('foot_' + L, J('foot', s), 'shin_' + L)
    T = {}
    cabinet(mk, M, T); face(mk, M, T); drinks(mk, M, T); door(mk, M, T); marquee(mk, M, T); sign(mk, M, T)
    for s, L in ((1, 'R'), (-1, 'L')): arm(mk, M, T, s, L); leg(mk, M, T, s, L)
    stickers(mk, M, T)
    mk.meta.update({'name': 'VENDING MACHINE', 'height': 5.02, 'phase': 'concept',
                    'palettes': {'A': {k: PAL_A[k] for k in ('paint', 'paint2', 'white', 'dark', 'glow2', 'thrust')},
                                 'B': {k: PAL_B[k] for k in ('paint', 'paint2', 'white', 'dark', 'glow2', 'thrust')}}})
    return mk


def box(x0, x1, y0, y1, z0, z1, m, bev=0.02, name='box'):
    return hull([(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], m, bev, 2, name)


def rbox(x0, x1, y0, y1, z0, z1, r, m, name='rbox'):
    """a box with round vertical edges (r): the cabinet's soft corners"""
    pts = []
    for (cx, cz) in ((x0 + r, z0 + r), (x1 - r, z0 + r), (x1 - r, z1 - r), (x0 + r, z1 - r)):
        for k in range(6):
            a = math.atan2(cz - (z0 + z1) / 2, cx - (x0 + x1) / 2) - math.pi / 4 + math.pi / 2 * k / 5
            for y in (y0, y1): pts.append((cx + math.cos(a) * r, y, cz + math.sin(a) * r))
    return hull(pts, m, 0.03, 2, name)


ZB = -0.42  # (the recessed face behind the door: the drinks sit between it and the door)


def cabinet(mk, M, T):
    B = [rbox(-W, W, Y0, Y1, ZB, D, 0.18, M['paint'], 'cabinet')]
    # the front: a frame round the drinks recess (left stile, the face column on the right, top and bottom rails)
    B.append(box(-W, -0.98, Y0, Y1, ZF, ZB + 0.02, M['paint'], 0.025, 'stile'))
    B.append(box(0.34, W, Y0, Y1, ZF, ZB + 0.02, M['paint'], 0.025, 'facecol'))
    B.append(box(-0.98, 0.34, 4.36, Y1, ZF, ZB + 0.02, M['paint'], 0.025, 'toprail'))
    B.append(box(-0.98, 0.34, Y0, 1.62, ZF, ZB + 0.02, M['paint'], 0.025, 'botrail'))
    # pink trims round the front and the back, chrome strips down the front corners
    B.append(box(-W - 0.02, W + 0.02, Y1 - 0.12, Y1 + 0.02, ZF - 0.03, ZF + 0.08, M['paint2'], 0.02, 'trim_top'))
    B.append(box(-W - 0.02, W + 0.02, Y0 - 0.02, Y0 + 0.14, ZF - 0.03, ZF + 0.08, M['paint2'], 0.02, 'trim_bot'))
    B.append(box(-W + 0.06, W - 0.06, Y1 - 0.12, Y1 + 0.02, D - 0.06, D + 0.03, M['paint2'], 0.02, 'trim_back'))
    for sx in (-1, 1):
        B.append(box(sx * W - 0.05, sx * W + 0.05, Y0 + 0.14, Y1 - 0.12, ZF - 0.02, ZF + 0.10, M['chrome'], 0.015, 'cornerstrip'))
        for k in range(5):  # side vents, low at the back
            y = Y0 + 0.30 + k * 0.12
            B.append(box(sx * W - 0.02, sx * W + 0.02, y, y + 0.05, 0.20, 0.62, M['dark'], 0.01, 'vent'))
    B.append(box(-0.96, 0.32, 1.04, 1.50, ZF - 0.04, ZF + 0.06, M['dark'], 0.02, 'bay'))  # (round the flap)
    mk.add('body', B); T['body'] = B
    H = [rbox(-W + 0.06, W - 0.06, JT['hips'][1] - 0.12, Y0 + 0.02, -D + 0.06, D - 0.06, 0.16, M['dark'], 'plinth')]
    for sx in (-1, 1): H.append(cyl((sx * 0.56, 0.74, -0.18), (sx * 0.56, 0.74, 0.18), 0.17, M['frame'], 12, name='hipjoint'))
    mk.add('hips', H); T['hips'] = H


def face(mk, M, T):
    """the right third of the front: a chrome panel with two button eyes, the coin slot (its mouth), coin return, keypad"""
    F = [box(0.44, 1.02, 2.30, 4.42, ZF - 0.06, ZF + 0.02, M['chrome'], 0.03, 'facepanel')]
    F.append(box(0.40, 1.06, 2.26, 4.46, ZF - 0.03, ZF + 0.03, M['paint2'], 0.02, 'faceborder'))  # (a pink frame round the face)
    for k, x in enumerate((0.60, 0.88)):  # the eyes: big glowing domed buttons in dark rings, and cheeky brows
        c = (x, 4.02, ZF - 0.06)
        F.append(frustum(c, add(c, (0, 0, -0.06)), 0.150, 0.135, M['dark'], 20, bev=0.01, name='eyering'))
        F.append(lathe_ax([(0.118, 0.0), (0.112, 0.05), (0.07, 0.09), (0.0, 0.105)], add(c, (0, 0, -0.05)), (0, 0, -1), M['glow2'], 20, 'eye'))
        tilt = 0.035 if k == 0 else -0.035
        F.append(hull([(x + dx, 4.24 + dy + tilt * dx / 0.12, z) for dx in (-0.12, 0.12) for dy in (0.0, 0.05) for z in (ZF - 0.11, ZF - 0.05)], M['dark'], 0.012, name='brow'))
    F.append(box(0.62, 0.86, 3.72, 3.80, ZF - 0.10, ZF - 0.04, M['dark'], 0.01, 'slotbezel'))  # the coin slot mouth
    F.append(box(0.65, 0.83, 3.745, 3.775, ZF - 0.112, ZF - 0.09, M['glow2'], 0.004, 'slotglow'))
    F.append(box(0.64, 0.84, 3.36, 3.54, ZF - 0.14, ZF - 0.04, M['dark'], 0.02, 'coinreturn'))
    F.append(box(0.62, 0.86, 3.35, 3.38, ZF - 0.16, ZF - 0.06, M['chrome'], 0.008, 'returnlip'))
    for i in range(3):  # the keypad chin
        for j in range(3):
            x, y = 0.60 + 0.12 * i, 2.62 + 0.13 * j
            F.append(box(x - 0.045, x + 0.045, y - 0.045, y + 0.045, ZF - 0.10, ZF - 0.05, M['white'], 0.012, 'key'))
    F.append(box(0.56, 0.92, 3.04, 3.20, ZF - 0.09, ZF - 0.05, M['dark'], 0.01, 'pricebox'))
    mk.add('body', F); T['face'] = F


CAN = {'can_r': None, 'can_y': None, 'can_g': None, 'can_b': None}


def drinks(mk, M, T):
    """four shelves of cans and bottles in the recess behind the door, a glowing back panel lighting them"""
    G = [box(-0.98, 0.34, 1.62, 4.36, ZB - 0.03, ZB + 0.01, M['glow'], 0.01, 'backlight')]
    roles = ['can_r', 'can_y', 'can_g', 'can_b']
    for r, y in enumerate((1.70, 2.36, 3.02, 3.68)):
        G.append(box(-0.97, 0.33, y - 0.035, y, ZF + 0.04, ZB - 0.01, M['chrome'], 0.008, 'shelf'))
        for k in range(5):
            x = -0.82 + k * 0.255; m = M[roles[(k + r) % 4]]; zc = (ZF + ZB) / 2
            if (k + r) % 3 == 0:  # a bottle
                G.append(lathe_ax([(0.085, 0.0), (0.09, 0.30), (0.05, 0.40), (0.035, 0.46), (0.038, 0.50)], (x, y, zc), (0, 1, 0), m, 12, 'bottle'))
            else:
                G.append(lathe_ax([(0.085, 0.0), (0.095, 0.03), (0.095, 0.30), (0.08, 0.34)], (x, y, zc), (0, 1, 0), m, 12, 'can'))
                G.append(cyl((x, y + 0.335, zc), (x, y + 0.355, zc), 0.075, M['chrome'], 12, name='lid'))
    mk.add('body', G); T['drinks'] = G


def door(mk, M, T):
    """the glass door, hinged on its left edge: a chrome frame, a long handle, thin tinted glass"""
    x0, x1, y0, y1, z = -1.02, 0.38, 1.58, 4.40, ZF - 0.02
    Dr = [box(x0, x1, y1 - 0.10, y1, z - 0.06, z + 0.02, M['chrome'], 0.02, 'door_top'), box(x0, x1, y0, y0 + 0.10, z - 0.06, z + 0.02, M['chrome'], 0.02, 'door_bot'),
          box(x0 - 0.01, x0 + 0.10, y0 + 0.05, y1 - 0.05, z - 0.07, z + 0.03, M['chrome'], 0.02, 'door_l'), box(x1 - 0.10, x1 + 0.01, y0 + 0.05, y1 - 0.05, z - 0.07, z + 0.03, M['chrome'], 0.02, 'door_r')]  # (sides a touch deeper: no coplanar corners)
    Dr.append(box(x1 - 0.20, x1 - 0.14, 2.30, 3.70, z - 0.14, z - 0.06, M['paint2'], 0.02, 'handle'))
    for y in (2.40, 3.60): Dr.append(box(x1 - 0.20, x1 - 0.14, y, y + 0.06, z - 0.08, z - 0.04, M['chrome'], 0.01, 'handlepost'))
    for y in (2.30, 2.96, 3.62):  # (no glass pane: in the game it reads as a black slab over the drinks; thin chrome cross rails instead)
        Dr.append(box(x0 + 0.06, x1 - 0.06, y - 0.015, y + 0.015, z - 0.05, z - 0.02, M['chrome'], 0.006, 'doorrail'))
    mk.add('door', Dr); T['door'] = Dr
    Fl = [box(-0.94, 0.30, 1.08, 1.42, ZF - 0.07, ZF - 0.02, M['dark'], 0.02, 'flap')]
    Fl.append(box(-0.50, -0.14, 1.12, 1.17, ZF - 0.12, ZF - 0.06, M['chrome'], 0.01, 'flaphandle'))
    Fl.append(box(-0.90, 0.26, 1.36, 1.41, ZF - 0.075, ZF - 0.06, M['paint2'], 0.006, 'flapstripe'))
    mk.add('flap', Fl); T['flap'] = Fl


def marquee(mk, M, T):
    """the lit sign box on top: a pink frame, the JANK COLA sign glowing on its front, chase-light bulbs"""
    Q = [rbox(-W - 0.04, W + 0.04, Y1, Y1 + 0.44, -D - 0.06, D - 0.10, 0.12, M['paint2'], 'marqueebox')]
    Q.append(box(-W + 0.06, W - 0.06, Y1 + 0.42, Y1 + 0.47, -D + 0.04, D - 0.20, M['white'], 0.008, 'marqueecap'))
    for k in range(9):
        x = -0.96 + k * 0.24
        Q.append(ball((x, Y1 + 0.46, -D - 0.02), 0.045, M['glow'], 10, 6, 'bulb'))
    mk.add('marquee', Q); T['marquee'] = Q
    sm = tex_mat('vm_marqueemat', marquee_img(), rough=0.3, emit=2.5, cc=0.4)
    o = decal(Q[:1], (0, Y1 + 0.22, -D - 0.07), (0, 0, -1), (0, 1, 0), 1.84, 0.34, sm, name='marquee_sign', reach=0.2)
    if o: mk.add('marquee', o)


def sign(mk, M, T):
    """OUT OF ORDER, stowed on the back (face out the back): a white board in a hazard frame, a carry handle on top"""
    c = JT['sign']
    S = [box(c[0] - 0.95, c[0] + 0.95, c[1] - 0.62, c[1] + 0.62, c[2] - 0.04, c[2] + 0.04, M['white'], 0.02, 'board')]
    for k, (a0, a1, b0, b1) in enumerate(((-0.99, 0.99, 0.58, 0.68), (-0.99, 0.99, -0.68, -0.58), (-1.00, -0.89, -0.63, 0.63), (0.89, 1.00, -0.63, 0.63))):
        e = 0.01 if k >= 2 else 0.0  # (the uprights a touch deeper: no coplanar corners)
        S.append(box(c[0] + a0, c[0] + a1, c[1] + b0, c[1] + b1, c[2] - 0.05 - e, c[2] + 0.06 + e, M['hazard'], 0.015, 'signframe'))
    S.append(tube([add(c, (-0.30, 0.68, 0.0)), add(c, (-0.26, 0.88, 0.0)), add(c, (0.26, 0.88, 0.0)), add(c, (0.30, 0.68, 0.0))], 0.04, M['dark'], 8, 'signhandle'))
    S.append(box(-0.30, 0.30, c[1] - 0.20, c[1] + 0.20, D - 0.01, c[2] - 0.03, M['frame'], 0.01, 'signclip'))  # (the clip holding it on)
    mk.add('sign', S); T['sign'] = S
    tm = tex_mat('vm_signmat', sign_img(), rough=0.45, cc=0.3)
    o = decal(S[:1], add(c, (0, 0.0, 0.05)), (0, 0, 1), (0, 1, 0), 1.74, 1.08, tm, name='sign_face', reach=0.1)
    if o: mk.add('sign', o)


def arm(mk, M, T, s, L):
    sh = J('shoulder', s); ua = J('upperarm', s); fa = J('forearm', s); ha = J('hand', s)
    mk.add('shoulder_' + L, [ball(add(sh, (s * 0.10, -0.04, 0)), 0.24, M['chrome'], 16, 10, 'shoulderball'),
                             frustum(add(sh, (s * 0.02, 0.0, 0)), add(sh, (s * 0.18, -0.02, 0)), 0.30, 0.26, M['paint2'], 16, bev=0.02, name='shouldercap')])
    mk.add('upperarm_' + L, [frustum(add(ua, (0, -0.05, 0)), add(fa, (0, 0.05, 0)), 0.17, 0.15, M['white'], 12, bev=0.02, name='upper'),
                             frustum(add(ua, (s * 0.01, -0.22, 0)), add(ua, (s * 0.01, -0.34, 0)), 0.20, 0.20, M['paint2'], 12, bev=0.015, name='armband')])
    mk.add('forearm_' + L, [ball(fa, 0.15, M['chrome'], 12, 8, 'elbow'),
                            frustum(add(fa, (0, -0.06, 0)), add(ha, (0, 0.08, 0)), 0.17, 0.20, M['paint'], 12, bev=0.02, name='fore'),
                            frustum(add(ha, (0, 0.10, 0)), add(ha, (0, 0.04, 0)), 0.22, 0.22, M['paint2'], 12, bev=0.015, name='cuff')])
    # a big mitten hand: a soft block with a thumb
    H = [hull([add(ha, (x, y, z)) for x in (-0.14, 0.14) for y in (0.04, -0.40) for z in (-0.17, 0.17)] + [add(ha, (x, -0.46, 0)) for x in (-0.08, 0.08)], M['white'], 0.035, name='mitten')]
    H.append(hull([add(ha, (s * x, y, z)) for x in (-0.06, 0.06) for (y, z) in ((-0.06, -0.16), (-0.24, -0.26), (-0.10, -0.12), (-0.22, -0.18))], M['white'], 0.012, name='thumb'))
    mk.add('hand_' + L, H)


def leg(mk, M, T, s, L):
    th, sn, ft = J('thigh', s), J('shin', s), J('foot', s)
    mk.add('thigh_' + L, [frustum(th, add(sn, (0, 0.04, 0)), 0.16, 0.15, M['frame'], 12, bev=0.015, name='thigh'),
                          cyl(add(th, (s * 0.04, 0.02, 0.10)), add(sn, (s * 0.04, 0.02, 0.12)), 0.05, M['chrome'], 8, name='piston')])
    mk.add('shin_' + L, [ball(sn, 0.15, M['chrome'], 12, 8, 'knee'), frustum(add(sn, (0, -0.02, 0)), add(ft, (0, 0.06, 0)), 0.19, 0.22, M['paint2'], 12, bev=0.02, name='shin')])
    F = [hull([add(ft, (x, y, z)) for x in (-0.24, 0.24) for (y, z) in ((-0.20, -0.52), (-0.20, 0.34), (0.04, -0.36), (0.10, 0.26), (-0.10, -0.56))], M['paint2'], 0.05, name='foot')]
    F.append(hull([add(ft, (x, y, z)) for x in (-0.25, 0.25) for (y, z) in ((-0.22, -0.54), (-0.22, 0.36), (-0.15, -0.54), (-0.15, 0.36))], M['rubber'], 0.02, name='sole'))
    F.append(hull([add(ft, (x, y, z)) for x in (-0.20, 0.20) for (y, z) in ((-0.10, -0.50), (0.0, -0.44), (-0.10, -0.62), (-0.04, -0.60))], M['white'], 0.03, name='toecap'))
    F += nozzle(add(ft, (0, -0.06, 0.36)), norm((0, -0.6, 0.8)), 0.10, 0.14, M, 'heeljet')
    mk.add('foot_' + L, F)


def stickers(mk, M, T):
    m = herokit.atlas_mat(mk, NUMBER)
    cab = [T['body'][0]]
    for s in (1, -1):  # the price as a unit number high on both sides
        o = herokit.stamp(cab, 'number', (s * W, 4.12, 0.12), (s, 0, 0), (0, 1, 0), 0.80, m)
        if o: mk.add('body', o)
    for cell, c, n, w in (('cola', (W, 2.08, 0.16), (1, 0, 0), 0.72), ('bread', (-W, 2.12, -0.12), (-1, 0, 0), 0.38),
                          ('tri', (-W, 2.12, 0.40), (-1, 0, 0), 0.24), ('washme', (0.0, 1.40, D), (0, 0, 1), 0.70),
                          ('piloting', (0.0, 4.20, D), (0, 0, 1), 0.80)):
        o = herokit.stamp(cab, cell, c, n, (0, 1, 0), w, m)
        if o: mk.add('body', o)
    pm = tex_mat('vm_pricemat', price_img(), rough=0.3, emit=1.6, cc=0.3)
    o = decal([T['face'][-1]], (0.74, 3.12, ZF - 0.095), (0, 0, -1), (0, 1, 0), 0.30, 0.12, pm, name='price', reach=0.1)
    if o: mk.add('body', o)
    mk.meta['spray'] = [{'name': 'spray_0', 'joint': 'body', 'at': [-W - 0.004, 3.18, 0.12], 'dir': [-1, 0, 0], 'up': [0, 1, 0], 'size': 0.80},
                        {'name': 'spray_1', 'joint': 'body', 'at': [W + 0.004, 3.18, 0.12], 'dir': [1, 0, 0], 'up': [0, 1, 0], 'size': 0.80}]


# ------------------------------------------------------------ markers
def marks(mk):
    m = {
        'mk_muzzle': {'joint': 'body', 'at': (0.74, 3.76, ZF - 0.16), 'dir': (0, 0, -1)},
        'mk_drop': {'joint': 'body', 'at': (-0.32, 1.20, ZF - 0.20), 'dir': norm((0, -0.3, -1))},
        'mk_sign': {'joint': 'hips', 'at': (0, 0.0, -2.40), 'dir': (0, 0, -1)},
        'mk_seat': {'joint': 'body', 'at': (-0.30, 2.30, 0.10), 'dir': (0, 0, -1)},
        'mk_eject': {'joint': 'body', 'at': (-0.30, 3.00, ZF - 0.30), 'dir': norm((0, 0.4, -1))},
        'mk_marquee': {'joint': 'marquee', 'at': (0, Y1 + 0.22, -D - 0.10), 'dir': (0, 0, -1)},
        'mk_mark': {'joint': 'marquee', 'at': (0, round(Y1 + 1.0, 3), 0.0), 'dir': (0, 1, 0)},
    }
    for s, L in ((1, 'R'), (-1, 'L')):
        ft = J('foot', s); ax = norm((0, -0.6, 0.8))
        m['mk_thrust_' + L] = {'joint': 'foot_' + L, 'at': add(add(ft, (0, -0.06, 0.36)), mul(ax, 0.16)), 'dir': ax}
        m['mk_hand_' + L] = {'joint': 'hand_' + L, 'at': add(J('hand', s), (0, -0.30, -0.10)), 'dir': (0, 0, -1)}
    for sl in mk.meta.get('spray', []):
        m['mk_' + sl['name']] = {'joint': sl['joint'], 'at': tuple(sl['at']), 'dir': tuple(sl['dir'])}
    return m


# ------------------------------------------------------------ clips
def clips():
    from clips import clip, ev_, M, both, side
    hp = lambda dy, r=(0, 0, 0): {'hips': {'r': r, 'p': (0, dy, 0)}}
    arms = lambda ua=(4, 0, 6), fa=(16, 0, 0): both('upperarm', ua) | both('forearm', fa)
    knees = lambda k: both('thigh', (10 * k, 0, 2)) | both('shin', (-20 * k, 0, 0)) | both('foot', (10 * k, 0, -2))
    st = M(hp(0.0), arms(), knees(0.6))
    out = []
    a = M(st, {'marquee': {'r': (0, 0, 0), 'p': (0, 0.0, 0)}})
    b = M(st, hp(-0.03), {'body': (1.5, 0, 0), 'marquee': {'r': (0, 0, 2), 'p': (0, 0.04, 0)}}, arms((7, 0, 8), (20, 0, 0)))
    out.append(clip('idle', 2.4, [(0, a), (1.2, b)], loop=True, note='a hum: the marquee bobs, the body breathes'))
    def step(s, k=1.0):  # s = +1: right foot forward (a waddle: the cabinet rocks onto the planted foot)
        return M(hp(-0.05 * k), side('thigh', (30 * k, 0, 2), s), side('thigh', (-22 * k, 0, 2), -s), side('shin', (-10, 0, 0), s), side('shin', (-26 * k, 0, 0), -s),
                 side('foot', (-12, 0, 0), s), side('foot', (16, 0, 0), -s), {'body': (0, -6 * s * k, 7 * s * k), 'marquee': (0, 0, -4 * s * k)},
                 side('upperarm', (-26 * k, 0, 8), s), side('upperarm', (24 * k, 0, 8), -s), both('forearm', (24, 0, 0)))
    def passing(s, k=1.0):
        return M(hp(0.06 * k), side('thigh', (2, 0, 2), s), side('thigh', (20 * k, 0, 2), -s), side('shin', (-6, 0, 0), s), side('shin', (-60 * k, 0, 0), -s),
                 side('foot', (4, 0, 0), s), side('foot', (24, 0, 0), -s), {'body': (0, 0, 9 * s * k), 'marquee': (0, 0, -6 * s * k)}, arms((2, 0, 8), (24, 0, 0)))
    out.append(clip('walk', 0.9, [(0, step(1)), (0.225, passing(1)), (0.45, step(-1)), (0.675, passing(-1))], loop=True, note='a stubby waddle: the cabinet rocks side to side'))
    run = lambda f: M(f, {'body': (-10, 0, 0)})
    rn = clip('run', 0.6, [(0, run(step(1, 1.4))), (0.15, run(passing(1, 1.4))), (0.3, run(step(-1, 1.4))), (0.45, run(passing(-1, 1.4)))], loop=True, note='a leaning trundle, everything rattling')
    rn['air'] = set(); out.append(rn)
    # coin turret: the coin slot spits coins; a small kick back each shot
    kick = M(st, {'body': (5, 0, 0)}, hp(-0.03))
    cf = clip('coin_fire', 0.24, [(0, st), (0.04, kick), (0.24, st)], loop=True, note='loop while firing: one coin per loop from mk_muzzle (9 dmg)')
    cf['snap'] = (1,); cf['events'] = [ev_(0.04, 'glint', 'mk_muzzle')]; out.append(cf)
    # dispense: the door swings, a can drops into the flap and pops out
    open_ = M(st, {'door': (0, 62, 0), 'body': (-4, 0, 0)}, side('upperarm', (30, 0, 8), 1), side('forearm', (60, 0, 0), 1))
    flap = M(open_, {'flap': (70, 0, 0)})
    dp = clip('dispense', 1.0, [(0, st), (0.18, open_), (0.34, flap), (0.5, M(flap, {'door': (0, 50, 0)})), (0.85, st)], note='door open, the cola pops out of the flap at 0.36 s (spawn it at mk_drop)')
    dp['snap'] = (2,); dp['events'] = [ev_(0.36, 'pop', 'mk_drop', 0.0), ev_(0.20, 'flare', 'mk_marquee')]; out.append(dp)
    # OUT OF ORDER: reach back, lift the sign over the head, slam it into the floor in front (the wall goes up there)
    c = JT['sign']
    reach = M(st, both('upperarm', (-40, 0, 40)), both('forearm', (80, 0, 0)), {'body': (6, 0, 0)}, hp(-0.08))
    lift = M(st, both('upperarm', (175, 0, 14)), both('forearm', (20, 0, 0)), {'body': (8, 0, 0), 'sign': {'r': (-90, 180, 0), 'p': (0, 2.30, -0.90)}})
    slam = M(st, both('upperarm', (60, 0, 12)), both('forearm', (10, 0, 0)), {'body': (-12, 0, 0)}, hp(-0.14), knees(1.6),
             {'sign': {'r': (12, 180, 0), 'p': (0, -2.06, -3.24)}})  # (rx counters the body's lean: the sign stands upright)
    held = M(slam, {'body': (-6, 0, 0), 'sign': {'r': (6, 180, 0), 'p': (0, -2.10, -3.30)}}, hp(-0.06), both('upperarm', (30, 0, 14)), both('forearm', (30, 0, 0)))
    oo = clip('out_of_order', 1.2, [(0, st), (0.18, reach), (0.40, lift), (0.56, slam), (0.80, held), (1.2, held)], hold=True,
              note='pulls the sign off its back, over its head, slams it down in front at 0.56 s (the 8 m wall goes up at mk_sign); held')
    oo['snap'] = (3,); oo['events'] = [ev_(0.56, 'slam', 'mk_sign', 0.3, True), ev_(0.56, 'dust', 'mk_sign', 0, True, 1.4)]; out.append(oo)
    # RESTOCK: arms flung up, door wide, the marquee jumps, everything glows
    up = M(st, both('upperarm', (150, 0, 40)), both('forearm', (20, 0, 0)), both('hand', (0, 0, 0)), hp(0.10), {'door': (0, 100, 0), 'flap': (60, 0, 0), 'marquee': {'r': (0, 0, 0), 'p': (0, 0.22, 0)}, 'body': (6, 0, 0)})
    rs = clip('restock', 1.6, [(0, st), (0.14, M(st, hp(-0.12), knees(1.4))), (0.30, up), (0.42, M(up, {'marquee': {'r': (0, 0, 4), 'p': (0, 0.14, 0)}})), (1.1, up), (1.6, st)],
              note='RESTOCK: everything flung open and lit at 0.3 s, held to 1.1 s')
    rs['snap'] = (2,); rs['events'] = [ev_(0.30, 'flare', 'mk_marquee', 0.2), ev_(0.30, 'pop', 'mk_drop'), ev_(0.32, 'glint', 'mk_hand_L'), ev_(0.32, 'glint', 'mk_hand_R'), ev_(0.30, 'vent', 'mk_thrust_L'), ev_(0.30, 'vent', 'mk_thrust_R')]
    out.append(rs)
    # stuck: a jammed rattle (loop) / kicked: an ally's kick jolts it, the flap pops, a can comes out
    j1 = M(st, {'body': (2, 0, 3), 'door': (0, 6, 0), 'marquee': (0, 0, -3)}, side('upperarm', (10, 0, 14), 1))
    j2 = M(st, {'body': (-1, 0, -3), 'door': (0, 0, 0), 'marquee': (0, 0, 3)}, side('upperarm', (10, 0, 14), -1))
    out.append(clip('stuck', 0.5, [(0, j1), (0.12, j2), (0.25, M(j1, {'body': (1, 0, 2)})), (0.37, j2)], loop=True, note='jammed: rattling and twitching (an ability got stuck)'))
    jolt = M(st, {'body': (8, 0, 12), 'marquee': (0, 0, -8), 'door': (0, 12, 0)}, hp(0.10), side('upperarm', (-20, 0, 40), 1), side('upperarm', (30, 0, 50), -1))
    kk = clip('kicked', 0.8, [(0, st), (0.06, jolt), (0.20, M(st, {'flap': (80, 0, 0), 'body': (-3, 0, -4)})), (0.45, M(st, {'flap': (30, 0, 0)})), (0.8, st)],
              note='an ally kicks it: jolts, the flap pops and a can shoots out at 0.22 s (unstuck)')
    kk['snap'] = (1,); kk['events'] = [ev_(0.06, 'spark', 'body', 0.15), ev_(0.22, 'pop', 'mk_drop')]; out.append(kk)
    # jump / land / hit
    jp = clip('jump', 0.6, [(0, st), (0.14, M(st, hp(-0.10), knees(2.4))), (0.26, M(st, hp(0.05), knees(0.2), both('upperarm', (60, 0, 30)))), (0.6, M(st, knees(1.6), both('upperarm', (30, 0, 30))))],
              hold=True, note='crouch, heel jets, tuck (held in the air)')
    jp['snap'] = (2,); jp['air'] = {2, 3}; jp['events'] = [ev_(0.26, 'burst', 'mk_thrust_L'), ev_(0.26, 'burst', 'mk_thrust_R')]; out.append(jp)
    ld = clip('land', 0.6, [(0, M(st, knees(1.6))), (0.06, M(st, knees(3.0), {'body': (-6, 0, 0), 'marquee': {'r': (0, 0, 0), 'p': (0, -0.10, 0)}}, both('upperarm', (20, 0, 40)))),
                            (0.24, M(st, knees(2.4))), (0.42, M(st, knees(0.4), {'marquee': {'r': (0, 0, 0), 'p': (0, 0.06, 0)}})), (0.6, st)], note='squash (the marquee keeps going), overshoot, settle')
    ld['snap'] = (1,); ld['air'] = {0}; ld['events'] = [ev_(0.06, 'step', 'foot_L', 0, True), ev_(0.06, 'step', 'foot_R', 0, True)]; out.append(ld)
    hr = clip('hit_react', 0.5, [(0, st), (0.05, M(st, {'body': (10, -10, 6), 'door': (0, 18, 0), 'marquee': (0, 0, 6)}, side('upperarm', (-20, 0, 40), 1))), (0.2, M(st, {'body': (-3, 3, -2)})), (0.5, st)],
              note='rocks back, the door swings open a crack')
    hr['snap'] = (1,); out.append(hr)
    # MECH DROP: fall, the landing, the show (a ta-da: door flung open, one arm offering a can, the other on its side)
    fa = M(st, both('upperarm', (160, 0, 30)), both('forearm', (20, 0, 0)), knees(1.2), {'door': (0, 30, 0)})
    fb = M(fa, both('upperarm', (140, 0, 44)), {'door': (0, 10, 0)})
    df = clip('drop_fall', 0.5, [(0, fa), (0.25, fb)], loop=True, note='the MECH DROP fall (loop): arms up, the door flapping')
    df['air'] = 'all'; out.append(df)
    imp = M(st, hp(-0.10), knees(3.2), {'body': (-14, 0, 4), 'marquee': {'r': (0, 0, 0), 'p': (0, -0.12, 0)}}, side('upperarm', (30, 0, 40), 1), side('forearm', (40, 0, 0), 1), side('upperarm', (60, 0, 10), -1))
    di = clip('drop_in', 1.3, [(0, fa), (0.30, fa), (0.36, imp), (0.7, M(st, knees(1.2))), (1.3, st)], hold=True, note='impact at 0.36 s; ends standing')
    di['snap'] = (2,); di['air'] = {0, 1}; di['events'] = [ev_(0.36, 'slam', 'hips', 0.4, True, 1.3)]; out.append(di)
    look = M(st, knees(2.0), {'body': (-6, 0, 2)}, hp(-0.04))
    coil = M(st, knees(2.6), {'body': (-10, -8, 0)}, side('upperarm', (-30, 0, 30), 1), side('forearm', (60, 0, 0), 1))
    tada = M(st, knees(0.4), {'body': (4, 10, -3), 'door': (0, 96, 0), 'marquee': {'r': (0, 0, -4), 'p': (0, 0.18, 0)}},
             side('upperarm', (78, -10, 24), 1), side('forearm', (14, 0, 0), 1), side('hand', (0, 0, 20), 1),
             side('upperarm', (-10, 0, 34), -1), side('forearm', (90, 0, -60), -1))
    sig = M(tada, {'door': (0, 84, 0), 'marquee': {'r': (0, 0, -2), 'p': (0, 0.06, 0)}}, side('upperarm', (70, -10, 22), 1))
    hi = clip('hero_intro', 1.7, [(0, imp), (0.18, M(st, knees(2.6), hp(-0.06))), (0.42, look), (0.62, look), (0.80, coil), (0.98, tada), (1.18, sig), (1.7, sig)], hold=True,
              note='the MECH DROP landing shot: from the impact, a ta-da by ~1.0 s (door flung open, offering a can); held')
    hi['snap'] = (5,); hi['events'] = [ev_(0, 'slam', 'hips', 0.4, True, 1.3), ev_(0.98, 'flare', 'mk_marquee', 0.1), ev_(0.98, 'pop', 'mk_drop'), ev_(1.0, 'glint', 'mk_hand_R')]
    out.append(hi)
    kn = M(st, knees(2.8), {'body': (-8, 0, 0)}, hp(-0.10))
    out.append(clip('pilot_in', 2.6, [(0, st), (0.5, kn), (0.8, M(kn, {'door': (0, 95, 0)})), (1.6, M(kn, {'door': (0, 95, 0)})), (2.0, kn), (2.6, st)], note='kneels, the door swings open (pilot climbs in 0.8 to 1.6 s), shuts'))
    ej = clip('eject', 0.7, [(0, st), (0.06, M(st, {'door': (0, 130, 0), 'body': (6, 0, 0)}, hp(0.06))), (0.25, M(st, {'door': (0, 110, 0)})), (0.7, M(st, {'door': (0, 100, 0)}))], hold=True,
              note='the door blows open (the pilot launches at 0.06 s); held')
    ej['snap'] = (1,); ej['events'] = [ev_(0.06, 'pop', 'mk_eject', 0.2)]; out.append(ej)
    dead = M(st, knees(3.0), hp(-0.12), {'body': (-30, 8, 14), 'door': (0, 120, 20), 'flap': (90, 0, 0), 'marquee': {'r': (20, 0, 30), 'p': (0.3, -0.10, -0.2)}, 'sign': {'r': (40, 0, -30), 'p': (0.4, -1.6, 0.6)}},
             both('upperarm', (-10, 0, 50)), both('forearm', (5, 0, 0)))
    ds = clip('destroy', 1.6, [(0, st), (0.12, M(st, {'body': (10, -14, 8), 'door': (0, 60, 0)})), (0.6, dead), (1.6, dead)], hold=True,
              note='hit, the door bursts, the marquee and sign come loose, it slumps forward; held')
    ds['snap'] = (1,); ds['events'] = [ev_(0.12, 'pop', 'mk_eject', 0.3), ev_(0.6, 'dust', 'hips', 0, True, 1.3)]; out.append(ds)
    return out
