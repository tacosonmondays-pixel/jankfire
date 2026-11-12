# NIGHT SHIFT: the heavy knight (about 5.6 m to the helmet, 6 m to the top of its beacon). An original JANKFIRE frame:
# a night-shift security guard built like a knight. A great helm with one glowing visor slit and a spinning amber
# security beacon on top, a barrel breastplate with hi-vis reflective bands and a NIGHT SHIFT badge (the breastplate
# is the cockpit hatch: it drops open like a drawbridge), layered pauldrons with a torch on the right one, a belt with a
# giant keyring and a coffee thermos, a snap-off blade sword (a box cutter the size of a car, energy edges) and a tower
# shield with a PLEASE HOLD display. Concept pass (phase 1): blockout + paint, joints ready to pose.
# Game space: the mech faces -z, its right is +x, feet on y = 0.
from mechkit import *

DECALS = True  # (off for the Tripo reference pictures: no text or stickers)

FID = 'mech_nightshift'
PAL_A = {  # "GRAVEYARD SHIFT": royal blue + white + hi-vis yellow on navy, amber visor and edges
    'paint': 0x2f55e8, 'white': 0xf2f0ea, 'dark': 0x161c36, 'accent': 0xffd23a, 'frame': 0x3a3f4e, 'chrome': 0xd2d9e2,
    'rubber': 0x18181c, 'glass': 0x0c1222, 'glow': 0xffa424, 'thrust': 0xffb84a, 'brass': 0xd9a640, 'reflect': 0xc9d2dc,
    'blade': 0x262c3c, 'beacon': 0xffa020, 'coffee': 0xd8382f, 'led': 0xffb020, 'card': 0xf4f4f4,
}
PAL_B = {  # "OVERTIME": red + white + gold on near-black, cyan visor and edges
    'paint': 0xff3a3a, 'white': 0xf4f0ec, 'dark': 0x221620, 'accent': 0xffc83d, 'frame': 0x3e3840, 'glass': 0x14101a,
    'glow': 0x4fe8ff, 'thrust': 0x6af0ff, 'blade': 0x2a2430, 'beacon': 0x40e0ff, 'coffee': 0x2f55e8, 'led': 0x4fe8ff,
}
for k, v in (('reflect', (0.22, 0.65, 0.3)), ('blade', (0.28, 0.5, 0.6)), ('coffee', (0.3, 0.0, 1.0)), ('card', (0.4, 0.0, 0.6))):
    ROLE_LOOK.setdefault(k, v)
ROLE_LOOK['beacon'] = None; ROLE_LOOK['led'] = None  # (glows)

JT = {
    'hips': (0, 2.80, 0.0), 'waist': (0, 3.18, 0.04), 'chest': (0, 3.42, 0.04), 'neck': (0, 4.78, 0.02), 'head': (0, 4.90, 0.0),
    'shoulder': (0.80, 4.56, 0.06), 'upperarm': (1.42, 4.40, 0.06), 'forearm': (1.52, 3.40, 0.10), 'hand': (1.56, 2.44, 0.04),
    'thigh': (0.56, 2.70, 0.0), 'shin': (0.62, 1.64, -0.08), 'foot': (0.64, 0.58, 0.08), 'toe': (0.64, 0.17, -0.52),
    'skirt': (0.66, 3.02, 0.0), 'backpack': (0, 4.10, 0.62), 'beacon': (0, 5.56, 0.0), 'hatch': (0, 3.64, -0.62),
    'sword': (1.58, 2.20, 0.0), 'shield': (-1.54, 2.92, 0.07),
}
GRIP = norm((0.04, -0.50, -0.86))  # the sword's grip axis in the rest pose (down and forward out of the fist)


def J(n, s=1): return mx(JT[n], s)


# ------------------------------------------------------------ paint jobs
def led_img():
    """the shield's display: PLEASE HOLD in LED dots, a hold-music note, a progress bar that never fills"""
    W, H = 192, 96; px = canvas(W, H, 0x06070c)
    dots = np.zeros((H, W, 3), np.float32)
    text_px(dots, 'PLEASE', 34, 10, 4, 0xffffff); text_px(dots, 'HOLD', 50, 46, 4, 0xffffff)
    m = dots[:, :, 0] > 0.5
    yy, xx = np.mgrid[0:H, 0:W]; grid = ((xx % 4) < 3) & ((yy % 4) < 3)  # LED pixels with dark gaps
    px[m & grid, :3] = 1.0; px[m & ~grid, :3] = 0.25
    px[84:90, 20:172, :3] = 0.18; px[84:90, 20:58, :3] = 1.0  # the progress bar (stuck at 25%)
    for (x, y) in ((176, 30), (176, 62)): px[y - 3:y + 3, x - 4:x + 4, :3] = 0.9  # two notes
    px[14:62, 182:185, :3] = 0.9
    return image_rgba('ns_led', px)


def sticker_img(name, lines, bg, fg, w=160, h=56, sc=2, bd=0x111111):
    px = canvas(w, h, bg); border(px, 3, bd)
    y = (h - len(lines) * 9 * sc) // 2 + 1
    for i, s in enumerate(lines): text_c(px, s, w / 2, y + i * 9 * sc, sc, fg)
    crust(px, 0.03, len(name), 0.003)
    return image_rgba(name, px)


def stencil_img(name, s, col, w=96, h=40, sc=4):
    px = canvas(w, h); text_c(px, s, w / 2, (h - 7 * sc) // 2, sc, col)
    return image_rgba(name, px)


def hazard_img(a=0xffd23a, b=0x16161c):
    px = canvas(96, 16); stripes(px, 0, 0, 96, 16, a, b, 6)
    return image_rgba('ns_hazard', px)


def timecard_img():
    """the timecard: TIMECARD, punched rows, an OVERTIME stamp"""
    px = canvas(64, 96, 0xf4f0e2); border(px, 2, 0x8a6a3a)
    text_c(px, 'TIME', 32, 5, 1, 0x2a1a08); text_c(px, 'CARD', 32, 14, 1, 0x2a1a08)
    for k in range(6): fill(px, 6, 26 + k * 10, 58, 27 + k * 10, 0xb8a888)
    for k in range(4): text(px, 'IN', 8, 29 + k * 10, 1, 0x3a3a3a); text(px, '9', 40, 29 + k * 10, 1, 0x3a3a3a)
    fill(px, 6, 80, 58, 91, 0xd02a2a); text_c(px, 'OVERTIME', 32, 82, 1, 0xf4f0e2)
    return image_rgba('ns_timecard', px)


def breaths_img():
    px = canvas(64, 64)
    for r in range(4):
        for c in range(4 - (r % 2)):
            x, y = 10 + c * 14 + (r % 2) * 7, 10 + r * 14
            yy, xx = np.mgrid[0:64, 0:64]; d = (xx - x) ** 2 + (yy - y) ** 2 <= 16
            px[d, :3] = hexrgb(0x05060a); px[d, 3] = 1
    return image_rgba('ns_breaths', px)


def snap_img():
    """the snap-off lines across the blade (alpha everywhere else): the long side of the image runs along the blade"""
    px = canvas(64, 256)
    for k in range(7):
        y0 = 16 + k * 34
        for xx in range(64):
            y = int(y0 + xx * 0.45)
            if y + 2 < 256: px[y:y + 2, xx, :3] = hexrgb(0x0a0c14); px[y:y + 2, xx, 3] = 1
    return image_rgba('ns_snap', px)


# ------------------------------------------------------------ build
def build():
    mk = Mech(FID, 'ns', PAL_A); M = mk.M
    mk.joint('root', (0, 0, 0)); mk.joint('hips', JT['hips'], 'root'); mk.joint('waist', JT['waist'], 'hips')
    mk.joint('chest', JT['chest'], 'waist'); mk.joint('neck', JT['neck'], 'chest'); mk.joint('head', JT['head'], 'neck')
    mk.joint('beacon', hp(0, 0.66, 0), 'head'); mk.joint('hatch', JT['hatch'], 'chest'); mk.joint('backpack', JT['backpack'], 'chest')
    for s, L in ((1, 'R'), (-1, 'L')):
        mk.joint('shoulder_' + L, J('shoulder', s), 'chest'); mk.joint('upperarm_' + L, J('upperarm', s), 'shoulder_' + L)
        mk.joint('forearm_' + L, J('forearm', s), 'upperarm_' + L); mk.joint('hand_' + L, J('hand', s), 'forearm_' + L)
        mk.joint('thigh_' + L, J('thigh', s), 'hips'); mk.joint('shin_' + L, J('shin', s), 'thigh_' + L)
        mk.joint('foot_' + L, J('foot', s), 'shin_' + L); mk.joint('toe_' + L, J('toe', s), 'foot_' + L)
        mk.joint('skirt_' + L, J('skirt', s), 'hips')
    mk.joint('sword', JT['sword'], 'hand_R'); mk.joint('shield', JT['shield'], 'forearm_L')
    T = {}
    head(mk, M, T); torso(mk, M, T); belt(mk, M, T)
    for s, L in ((1, 'R'), (-1, 'L')):
        leg(mk, M, T, s, L); arm(mk, M, T, s, L); tasset(mk, M, T, s, L)
    sword(mk, M, T); shield(mk, M, T)
    if DECALS: decals(mk, M, T)
    mk.meta.update({'name': 'NIGHT SHIFT', 'height': 5.70, 'phase': 'concept', 'grip': GRIP,
                    'palettes': {'A': {k: PAL_A[k] for k in ('paint', 'white', 'dark', 'accent', 'glow', 'thrust')},
                                 'B': {k: PAL_B[k] for k in ('paint', 'white', 'dark', 'accent', 'glow', 'thrust')}}})
    return mk


HS = 1.1
def hp(x, y, z): return add(JT['head'], (x * HS, y * HS, z * HS))


def head(mk, M, T):
    H = []
    H.append(hull([hp(sx * 0.24, y, z) for sx in (-1, 1) for y in (0.02, 0.50) for z in (-0.22, 0.26)], M['frame'], 0.02, name='skull'))
    # the great helm: an octagonal barrel with a ridge down the front
    pts = []
    for (y, rx, rz) in ((0.0, 0.31, 0.33), (0.20, 0.36, 0.38), (0.48, 0.36, 0.38), (0.62, 0.27, 0.29), (0.68, 0.14, 0.15)):
        pts += [hp(*p) for p in ring_pts((0, y, 0.02), (0, 1, 0), 1.0, 8, (rx, rz), rot=math.pi / 8, ref=(1, 0, 0))]
    pts += [hp(0, 0.04, -0.40), hp(0, 0.44, -0.44), hp(0, 0.58, -0.36)]
    helm = hull(pts, M['paint'], 0.03, 3, name='helm'); H.append(helm)
    hb = bvh_of([helm])
    # visor: a white surround, a dark slit, the glowing line in it
    def band(y0, y1, half, out, depth, m, nm):
        P = []
        for k in range(9):
            x = -half + 2 * half * k / 8
            for y in (y0, y1): P.append((x, y, 0))
        return skin(hb, [hp(x, y, -1.2) for (x, y, _) in P], (0, 0, 1), out, depth, m, 0.004, nm)
    H.append(band(0.24, 0.42, 0.33, 0.010, 0.03, M['white'], 'visor_frame'))
    H.append(band(0.285, 0.375, 0.30, 0.018, 0.03, M['glass'], 'visor'))
    H.append(band(0.318, 0.342, 0.27, 0.024, 0.03, M['glow'], 'visor_glow'))
    # a white ridge up the forehead to the crown, cheek plates (white), a chin guard (dark)
    # the hard hat: a ridge over the crown (hi-vis yellow) and a short peak above the visor
    H.append(skin(hb, [hp(x, 2.0, z) for x in (-0.042, 0.042) for z in (-0.30, -0.15, 0.0, 0.15, 0.30)], (0, -1, 0), 0.032, 0.03, M['accent'], 0.008, 'hardhat_ridge'))
    H.append(skin(hb, [hp(x, y, -1.2) for x in (-0.042, 0.042) for y in (0.45, 0.62)], (0, 0, 1), 0.037, 0.03, M['accent'], 0.008, 'hardhat_ridge_f'))
    H.append(hull([hp(sx * x, y, z) for sx in (-1, 1) for (x, z) in ((0.27, -0.28), (0.22, -0.50)) for y in (0.435, 0.468)] + [hp(0, y, -0.565) for y in (0.44, 0.472)],
                  M['accent'], 0.012, name='hardhat_peak'))
    for s in (-1, 1):
        H.append(skin(hb, [hp(s * 1.2, y, z) for (y, z) in ((0.22, -0.18), (0.22, 0.12), (0.02, -0.16), (0.02, 0.14), (0.10, -0.22))], (-s, 0, 0), 0.014, 0.03, M['white'], 0.006, 'cheek'))
    H.append(hull([hp(x, y, z) for x in (-0.26, 0.26) for (y, z) in ((-0.06, -0.20), (-0.06, 0.12), (0.10, -0.30), (0.10, 0.10))] + [hp(0, 0.0, -0.38), hp(0, 0.12, -0.40)], M['dark'], 0.02, name='chin'))
    # the walkie-talkie antenna on the left side
    H.append(cyl(hp(-0.37, 0.30, 0.10), hp(-0.42, 0.34, 0.10), 0.05, M['rubber'], 12, name='ant_base'))
    H.append(cyl(hp(-0.41, 0.33, 0.10), hp(-0.44, 0.78, 0.14), 0.022, M['rubber'], 8, r1=0.016, name='antenna'))
    H.append(ball(hp(-0.44, 0.79, 0.14), 0.03, M['rubber'], 8, 6, 'ant_tip'))
    mk.add('head', H); T['head'] = H
    # the beacon: a dark base, an amber dome, a wire cage
    bc = hp(0, 0.66, 0)
    B = [cyl(add(bc, (0, -0.06, 0)), add(bc, (0, 0.06, 0)), 0.16, M['dark'], 16, name='bc_base')]
    B.append(lathe_ax([(0.125, 0.0), (0.125, 0.10), (0.10, 0.17), (0.05, 0.205), (0.0, 0.215)], add(bc, (0, 0.055, 0)), (0, 1, 0), M['beacon'], 16, 'bc_dome'))
    for k in range(4):
        a = math.radians(45 + 90 * k); d = (math.cos(a), 0, math.sin(a))
        B.append(tube([add(bc, add(mul(d, r), (0, y, 0))) for (r, y) in ((0.15, 0.04), (0.15, 0.17), (0.11, 0.25), (0.0, 0.29))], 0.012, M['chrome'], 6, 'bc_bar'))
    mk.add('beacon', B); T['beacon'] = B
    N = [frustum((0, 4.70, 0.02), (0, 4.98, 0.0), 0.20, 0.18, M['frame'], 8, name='neckcol')]
    N.append(frustum((0, 4.74, 0.02), (0, 4.88, 0.02), 0.40, 0.36, M['white'], 10, bev=0.02, name='gorget'))
    mk.add('neck', N); T['neck'] = N


def torso(mk, M, T):
    C = [hull([(sx * x, y, z) for sx in (-1, 1) for (x, y) in ((0.58, 3.40), (0.74, 4.72)) for z in (-0.46, 0.55)], M['frame'], 0.03, name='core')]
    # the breastplate (paint): rounded, a ridge down the middle. it's the cockpit hatch
    bp = []
    for (y, hw, zc, zm, ze) in ((3.62, 0.60, -0.64, -0.52, -0.30), (3.90, 0.80, -0.80, -0.68, -0.38), (4.20, 0.88, -0.86, -0.74, -0.40),
                                (4.50, 0.86, -0.80, -0.68, -0.36), (4.70, 0.72, -0.62, -0.54, -0.30)):
        bp += [(0, y, zc - 0.03)] + [(s * x, y, z) for s in (-1, 1) for (x, z) in ((hw * 0.45, zm), (hw * 0.82, (zm + ze) / 2), (hw, ze))]
        bp += [(s * hw * 0.9, y, -0.15) for s in (-1, 1)]
    plate_ = hull(bp, M['paint'], 0.035, 3, name='breastplate')
    hatch = [plate_]
    pb = bvh_of([plate_])
    fwd = (0, 0, 1)
    def strip(y0, y1, half, out, m, nm):
        P = [(x, y, -2) for k in range(11) for x in (-half + 2 * half * k / 10,) for y in (y0, y1)]
        return skin(pb, P, fwd, out, 0.03, m, 0.004, nm)
    for (y0, y1) in ((3.97, 4.13), (4.27, 4.43)):  # hi-vis bands: yellow borders, a reflective silver middle
        hatch.append(strip(y0, y1, 0.80, 0.010, M['accent'], 'hivis_y'))
        hatch.append(strip(y0 + 0.035, y1 - 0.035, 0.79, 0.016, M['reflect'], 'hivis_s'))
    # the badge (brass) on the left of the chest
    bc = (-0.42, 4.56)
    hatch.append(skin(pb, [(bc[0] + dx, bc[1] + dy, -2) for (dx, dy) in ((-0.13, 0.11), (0.13, 0.11), (0.15, 0.0), (0.10, -0.12), (0, -0.18), (-0.10, -0.12), (-0.15, 0.0))], fwd, 0.022, 0.03, M['brass'], 0.006, 'badge'))
    # the timecard slot on the right of the chest, a card stuck in it (clocked in, never out)
    q, n = proj(pb, (0.44, 4.50, -2), fwd)
    r_ = norm(sub((1, 0, 0), mul(n, dot((1, 0, 0), n)))); u_ = norm(cross(n, r_))
    if u_[1] < 0: u_ = mul(u_, -1)
    def S_(a, b, c): return add(q, add(mul(r_, a), add(mul(u_, b), mul(n, c))))
    hatch.append(hull([S_(a, b, c) for a in (-0.14, 0.14) for b in (-0.05, 0.05) for c in (-0.03, 0.045)], M['dark'], 0.01, name='timeslot'))
    card = hull([S_(a, b, c) for a in (-0.10, 0.10) for b in (-0.02, 0.30) for c in (0.008, 0.02)], M['card'], 0.004, name='timecard')
    hatch.append(card); T['timecard'] = (card, S_(0, 0.17, 0.02), n, u_)
    mk.add('hatch', hatch); T['hatch'] = hatch
    for s in (-1, 1):
        # high collar plates (white) either side of the neck, side plates under the arms (white)
        C.append(hull([(s * x, y, z) for (x, y, z) in ((0.30, 4.62, -0.34), (0.66, 4.60, -0.30), (0.34, 4.98, -0.20), (0.62, 4.90, -0.16),
                       (0.30, 4.62, 0.36), (0.66, 4.60, 0.36), (0.34, 4.96, 0.30), (0.62, 4.88, 0.30))], M['white'], 0.025, name='collar'))
        C.append(hull([(s * x, y, z) for x in (0.70, 0.84) for y in (3.62, 4.44) for z in (-0.36, 0.44)] + [(s * 0.88, 4.0, 0.04)], M['white'], 0.03, name='flank'))
        C.append(hull([(s * x, y, z) for (x, y, z) in ((0.66, 3.46, -0.42), (0.20, 3.38, -0.52), (0.62, 3.44, 0.42), (0.20, 3.36, 0.46), (0.56, 3.62, 0.0), (0.20, 3.64, -0.5))], M['dark'], 0.02, name='rib'))
    C.append(hull([(sx * x, y, z) for sx in (-1, 1) for (x, y) in ((0.62, 3.48), (0.74, 4.66)) for z in (0.42, 0.62)], M['white'], 0.03, name='backplate'))
    mk.add('chest', C); T['chest'] = C + hatch
    # backpack: a heavy block (dark + white) with two big round thrusters
    B = [hull([(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.56, 3.56, 0.56), (0.62, 4.62, 0.56), (0.50, 4.66, 1.02), (0.46, 3.64, 1.06))], M['dark'], 0.03, name='pack')]
    B.append(hull([(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.40, 4.20, 1.02), (0.44, 4.60, 1.0), (0.40, 4.64, 1.10), (0.36, 4.24, 1.12))], M['white'], 0.02, name='packlid'))
    for s in (-1, 1):
        B += nozzle((s * 0.32, 3.64, 0.86), (0, -1, 0.45), 0.22, 0.40, M, 'main')
        B.append(hull([(s * x, y, z) for x in (0.60, 0.70) for y in (3.80, 4.50) for z in (0.62, 0.96)], M['paint'], 0.015, name='packside'))
    mk.add('backpack', B); T['backpack'] = B
    W = [cyl((0, 2.98, 0.04), (0, 3.58, 0.04), 0.30, M['frame'], 12, name='spine')]
    for k, y in enumerate((3.26, 3.40, 3.54)):
        w = 0.42 + 0.06 * k
        W.append(hull([(0, y - 0.07, -0.50 - 0.02 * k), (0, y + 0.08, -0.52 - 0.02 * k)] + [(s * w, yy, -0.40 - 0.02 * k) for s in (-1, 1) for yy in (y - 0.07, y + 0.08)] +
                      [(s * w * 0.85, yy, -0.10) for s in (-1, 1) for yy in (y - 0.07, y + 0.08)], M['white'], 0.016, name='ab'))
    for s in (-1, 1):
        W.append(cyl((s * 0.42, 3.02, -0.18), (s * 0.46, 3.30, -0.22), 0.07, M['frame'], 10, name='sleeve'))
        W.append(cyl((s * 0.46, 3.24, -0.22), (s * 0.50, 3.62, -0.26), 0.042, M['chrome'], 10, name='rod'))
    mk.add('waist', W); T['waist'] = W


def belt(mk, M, T):
    P = [hull([(sx * x, y, z) for sx in (-1, 1) for (x, y) in ((0.40, 2.52), (0.56, 3.02)) for z in (-0.36, 0.40)], M['frame'], 0.03, name='pelvis')]
    P.append(frustum((0, 2.92, 0.02), (0, 3.14, 0.02), 0.66, 0.64, M['dark'], 12, squash=(1.0, 0.82), bev=0.02, ref=(1, 0, 0), name='belt'))
    P.append(hull([(x, y, z) for x in (-0.20, 0.20) for y in (2.90, 3.16) for z in (-0.60, -0.50)], M['brass'], 0.02, name='buckle'))
    P.append(hull([(x, y, z) for x in (-0.12, 0.12) for y in (2.96, 3.10) for z in (-0.64, -0.55)], M['dark'], 0.01, name='buckle_in'))
    # front faulds (paint), two layered lames
    for k, (y0, y1, z) in enumerate(((2.94, 2.58, -0.56), (2.66, 2.30, -0.50))):
        P.append(hull([(s * x, y, zz) for s in (-1, 1) for (x, y, zz) in ((0.30, y0, z), (0.24, y1, z + 0.02), (0.30, y0, z + 0.14), (0.24, y1, z + 0.16))] + [(0, y1 - 0.06, z - 0.02), (0, y0, z - 0.04)],
                      M['paint'] if k == 0 else M['white'], 0.016, name='fauld'))
    P.append(hull([(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.40, 2.98, 0.40), (0.32, 2.40, 0.48), (0.40, 2.98, 0.54), (0.30, 2.44, 0.60))], M['white'], 0.02, name='rear'))
    # the keyring (right hip): a big ring, three keys
    kr = (0.66, 2.84, -0.36)
    P.append(lathe_ax([(0.13, -0.012), (0.14, 0.0), (0.13, 0.012), (0.12, 0.0)], kr, (0, 0, 1), M['chrome'], 20, 'keyring', cap=False))
    P.append(tube([(0.62, 3.02, -0.40), (0.66, 2.97, -0.37)], 0.02, M['chrome'], 6, 'key_hook'))
    for k, ang in enumerate((-30, 5, 35)):
        a = math.radians(ang); d = (math.sin(a), -math.cos(a), 0)
        base = add(kr, mul(d, 0.13))
        P.append(lathe_ax([(0.07, -0.012), (0.07, 0.012)], add(add(base, mul(d, 0.06)), (0, 0, (k - 1) * 0.007)), (0, 0, 1), M['brass'] if k == 1 else M['chrome'], 12, 'key_bow'))
        tip = add(base, mul(d, 0.42))
        zk = (k - 1) * 0.007  # (each key on its own plane)
        P.append(hull([add(base, mul(d, 0.10))] + [add(p, (0, 0, dz + zk)) for p in (add(base, mul(d, 0.10)), tip) for dz in (-0.012, 0.012)] +
                      [add(add(tip, mul(d, -0.12 + 0.04 * j)), add(mul((d[1], -d[0], 0), 0.05), (0, 0, zk))) for j in range(3)], M['brass'] if k == 1 else M['chrome'], 0.004, name='key'))
    # the coffee thermos (left hip) with its cup for a lid
    th = (-0.74, 2.66, -0.12)
    P.append(lathe_ax([(0.0, -0.30), (0.12, -0.30), (0.13, -0.26), (0.13, 0.20), (0.11, 0.24), (0.0, 0.24)], th, (0, 1, 0), M['coffee'], 16, 'thermos'))
    P.append(lathe_ax([(0.0, 0.24), (0.125, 0.24), (0.135, 0.38), (0.0, 0.38)], th, (0, 1, 0), M['chrome'], 16, 'thermos_cup'))
    P.append(hull([(x, y, z) for x in (-0.64, -0.60) for y in (2.50, 2.86) for z in (-0.16, -0.08)], M['dark'], 0.01, name='thermos_strap'))
    mk.add('hips', P); T['hips'] = P


def tasset(mk, M, T, s, L):
    S = []
    c = J('skirt', s)
    for k, (y0, y1, r) in enumerate(((3.04, 2.66, 0.40), (2.74, 2.38, 0.42), (2.46, 2.12, 0.44))):
        S.append(lame((c[0] - s * 0.10, y0, 0.02), (c[0] - s * 0.04, y1, 0.02), r - 0.03, r + 0.02, -70, 70, 0.05,
                      M['white'] if k != 1 else M['paint'], 7, (1.0, 1.15), 0.012, 'tasset', s))
    S.append(cyl(mx((0.56, 3.00, 0.02), s), mx((0.74, 3.00, 0.02), s), 0.08, M['frame'], 12, name='tasset_pin'))
    mk.add('skirt_' + L, S); T['skirt_' + L] = S


def leg(mk, M, T, s, L):
    x = lambda v: s * v
    TH = [ball(J('thigh', s), 0.22, M['frame'], name='hipball'), frustum((x(0.56), 2.62, 0.0), (x(0.61), 1.74, -0.06), 0.22, 0.19, M['frame'], 8, name='femur')]
    TH.append(hull([(x(0.58), 2.50, -0.38), (x(0.61), 1.84, -0.34)] + [(x(a), y, z) for (a, y, z) in ((0.34, 2.48, -0.26), (0.82, 2.48, -0.24), (0.40, 1.86, -0.22), (0.80, 1.86, -0.20),
                   (0.34, 2.44, 0.18), (0.82, 2.44, 0.18), (0.40, 1.90, 0.12), (0.80, 1.90, 0.12))], M['paint'], 0.035, 3, name='cuisse'))
    TH.append(plate([(x(0.84), 2.42, -0.20), (x(0.84), 2.42, 0.18), (x(0.81), 1.94, 0.14), (x(0.81), 1.94, -0.18)], 0.08, (s, 0, 0), M['white'], 0.014, name='thighside'))
    mk.add('thigh_' + L, TH); T['thigh_' + L] = TH
    SH = [cyl((x(0.40), 1.64, -0.08), (x(0.84), 1.64, -0.08), 0.17, M['frame'], 16, name='knee')]
    # the poleyn: a round white disc with a pointed paint cap, little fan wings either side
    SH.append(lathe_ax([(0.0, 0.0), (0.22, 0.0), (0.24, 0.05), (0.18, 0.12), (0.0, 0.14)], (x(0.62), 1.66, -0.26), (0, 0.1, -1), M['white'], 16, 'poleyn'))
    SH.append(hull([(x(0.62), 1.92, -0.36), (x(0.62), 1.56, -0.50), (x(0.62), 1.66, -0.32), (x(0.50), 1.78, -0.36), (x(0.74), 1.78, -0.36), (x(0.52), 1.58, -0.38), (x(0.72), 1.58, -0.38)], M['paint'], 0.012, name='poleyn_cap'))
    for sd in (-1, 1):
        SH.append(tri_plate((x(0.62 + sd * 0.18), 1.82, -0.24), (x(0.62 + sd * 0.18), 1.50, -0.24), (x(0.62 + sd * 0.30), 1.68, -0.02), 0.04, M['white'], name='fan'))
    SH.append(frustum((x(0.62), 1.56, -0.06), (x(0.64), 0.66, 0.06), 0.16, 0.15, M['frame'], 8, name='tibia'))
    gr = hull([(x(0.62), 1.46, -0.34), (x(0.64), 0.66, -0.50)] + [(x(a), y, z) for (a, y, z) in ((0.44, 1.48, -0.26), (0.80, 1.48, -0.26), (0.36, 0.68, -0.34), (0.92, 0.68, -0.34),
              (0.42, 1.44, 0.20), (0.82, 1.44, 0.20), (0.36, 0.68, 0.30), (0.92, 0.68, 0.30))], M['white'], 0.035, 3, name='greave')
    SH.append(gr); gb = bvh_of([gr])
    SH.append(skin(gb, [(x(0.60), 1.40, -2), (x(0.66), 1.40, -2), (x(0.58), 0.70, -2), (x(0.70), 0.70, -2)], (0, 0, 1), 0.012, 0.03, M['paint'], 0.004, 'greave_ridge'))
    for y in (0.86, 1.10):  # calf vents
        SH.append(skin(gb, [(x(a), yy, 2) for a in (0.52, 0.76) for yy in (y, y + 0.14)], (0, 0, -1), 0.012, 0.03, M['dark'], 0.004, 'calfvent'))
        SH.append(skin(gb, [(x(a), yy, 2) for a in (0.55, 0.73) for yy in (y + 0.05, y + 0.09)], (0, 0, -1), 0.02, 0.03, M['thrust'], 0.002, 'calfglow'))
    for xa in (0.54, 0.74):  # leg boosters (verniers) low on the calf, pointing out and down
        q, n = proj(gb, (x(xa), 0.76, 2), (0, 0, -1))
        if q:
            ax = norm(add(n, (0, -0.7, 0))); SH += nozzle(add(q, mul(n, -0.015)), ax, 0.075, 0.15, M, 'calfnozzle')
            mk.meta.setdefault('marks', {})[f'mk_thrust_calf_{L}{int(xa > 0.6)}'] = {'joint': 'shin_' + L, 'at': add(add(q, mul(n, -0.015)), mul(ax, 0.15)), 'dir': ax}
    mk.add('shin_' + L, SH); T['shin_' + L] = SH
    F = [ball(J('foot', s), 0.17, M['frame'], name='ankle')]
    for sd in (-1, 1):
        F.append(lathe_ax([(0.0, -0.03), (0.17, -0.03), (0.17, 0.03), (0.0, 0.05)], (x(0.64 + sd * 0.21), 0.50, 0.08), (s * sd, 0, 0), M['paint'], 16, 'ankledisc'))
    F.append(hull([(x(a), y, z) for (a, y, z) in ((0.38, 0.04, 0.46), (0.90, 0.04, 0.46), (0.42, 0.40, 0.40), (0.86, 0.40, 0.40), (0.46, 0.52, 0.0), (0.82, 0.52, 0.0),
                   (0.36, 0.04, -0.50), (0.92, 0.04, -0.50), (0.42, 0.34, -0.50), (0.86, 0.34, -0.50))], M['white'], 0.03, name='foot'))
    F.append(hull([(x(a), y, z) for (a, y, z) in ((0.34, 0.0, 0.48), (0.94, 0.0, 0.48), (0.34, 0.0, -0.52), (0.94, 0.0, -0.52), (0.35, 0.07, 0.48), (0.93, 0.07, 0.48), (0.35, 0.07, -0.52), (0.93, 0.07, -0.52))],
                  M['rubber'], 0.01, name='sole'))
    F.append(hull([(x(a), y, z) for (a, y, z) in ((0.52, 0.04, 0.44), (0.76, 0.04, 0.44), (0.64, 0.04, 0.66), (0.56, 0.30, 0.40), (0.72, 0.30, 0.40), (0.64, 0.12, 0.62))], M['paint'], 0.012, name='spur'))
    mk.add('foot_' + L, F); T['foot_' + L] = F
    TO = []
    for k, (z0, z1, y) in enumerate(((-0.48, -0.70, 0.34), (-0.64, -0.86, 0.27), (-0.80, -0.98, 0.19))):
        TO.append(hull([(x(a), yy, z) for a in (0.38 + 0.03 * k, 0.90 - 0.03 * k) for (yy, z) in ((0.04 + 0.006 * k, z0), (0.04 + 0.006 * k, z1), (y, z0 + 0.04), (y - 0.06, z1))] + [(x(0.64), y + 0.02, (z0 + z1) / 2)],
                       M['paint'] if k != 1 else M['white'], 0.016, name='sabaton'))
    TO.append(hull([(x(a), y, z) for a in (0.37, 0.91) for (y, z) in ((0.0, -0.46), (0.0, -0.99), (0.06, -0.46), (0.06, -0.99))], M['rubber'], 0.008, name='toesole'))
    TO.append(cyl((x(0.405), 0.17, -0.50), (x(0.875), 0.17, -0.50), 0.08, M['frame'], 12, name='toepin'))
    mk.add('toe_' + L, TO); T['toe_' + L] = TO


def arm(mk, M, T, s, L):
    x = lambda v: s * v
    sh = J('upperarm', s)
    SH = [hull([(x(a), y, z) for a in (0.725, 1.20) for y in (4.30, 4.70) for z in (-0.20, 0.32)], M['frame'], 0.03, name='clavicle')]
    # three lames: paint dome, white middle, paint bottom with a hazard edge
    # a rounded dome in two bands (a cone read as a lampshade), then the white and paint lames under it
    SH.append(lame((1.24, 5.08, 0.06), (1.30, 4.96, 0.06), 0.24, 0.50, -140, 140, 0.07, M['paint'], 12, (1.0, 1.0), 0.02, 'pauldron_top', s, 3))
    SH.append(lame((1.30, 4.985, 0.06), (1.37, 4.66, 0.06), 0.48, 0.63, -140, 140, 0.07, M['paint'], 12, (1.0, 1.0), 0.02, 'pauldron', s, 3))
    SH.append(lame((1.38, 4.70, 0.06), (1.46, 4.44, 0.06), 0.60, 0.64, -120, 120, 0.06, M['white'], 12, (1.0, 1.0), 0.015, 'pauldron2', s))
    SH.append(lame((1.48, 4.48, 0.06), (1.54, 4.24, 0.06), 0.62, 0.64, -105, 105, 0.06, M['paint'], 12, (1.0, 1.0), 0.015, 'pauldron3', s))
    SH.append(hull([mx(p, s) for p in ring_pts((1.22, 5.06, 0.06), (0, 1, 0), 0.25, 10) + ring_pts((1.22, 5.13, 0.06), (0, 1, 0), 0.13, 10)], M['white'], 0.012, name='pauldron_cap'))
    if s > 0:  # the torch on the right pauldron, pointing forward
        tc = (1.22, 5.06, -0.10)
        SH.append(lathe_ax([(0.0, 0.30), (0.075, 0.30), (0.075, -0.12), (0.12, -0.24), (0.12, -0.34), (0.0, -0.34)], tc, (0, 0, 1), M['rubber'], 16, 'torch'))
        SH.append(lathe_ax([(0.105, -0.34), (0.0, -0.355)], tc, (0, 0, 1), M['glow'], 16, 'torch_lens'))
        SH.append(lathe_ax([(0.125, -0.24), (0.13, -0.30), (0.125, -0.345), (0.115, -0.30)], tc, (0, 0, 1), M['chrome'], 16, 'torch_bezel', cap=False))
        SH.append(hull([(a, y, z) for a in (1.16, 1.28) for y in (4.86, 5.0) for z in (-0.12, 0.10)], M['frame'], 0.01, name='torch_mount'))
    mk.add('shoulder_' + L, SH); T['shoulder_' + L] = SH
    UA = [ball(sh, 0.22, M['frame'], name='shoulderball'), frustum((x(1.43), 4.34, 0.06), (x(1.51), 3.52, 0.10), 0.17, 0.15, M['frame'], 8, name='humerus')]
    UA.append(frustum((x(1.44), 4.22, 0.065), (x(1.50), 3.60, 0.09), 0.28, 0.25, M['white'], 10, bev=0.02, name='rerebrace'))
    mk.add('upperarm_' + L, UA); T['upperarm_' + L] = UA
    FA = [cyl((x(1.34), 3.40, 0.10), (x(1.70), 3.40, 0.10), 0.16, M['frame'], 16, name='elbow')]
    FA.append(hull([(x(a), y, z) for a in (1.36, 1.68) for (y, z) in ((3.58, 0.14), (3.24, 0.18), (3.56, 0.30), (3.26, 0.34))] + [(x(1.52), 3.40, 0.52), (x(1.52), 3.70, 0.30)], M['paint'], 0.02, name='couter'))
    FA.append(frustum((x(1.52), 3.30, 0.10), (x(1.56), 2.56, 0.05), 0.22, 0.27, M['paint'], 8, squash=(1.0, 1.1), bev=0.025, ref=(1, 0, 0), name='vambrace'))
    FA.append(frustum((x(1.53), 3.06, 0.09), (x(1.56), 2.70, 0.06), 0.27, 0.285, M['dark'], 8, squash=(0.95, 1.05), bev=0.01, ref=(1, 0, 0), name='cuff'))
    mk.add('forearm_' + L, FA); T['forearm_' + L] = FA
    # gauntlet: a closed fist (it holds the sword grip / the shield's handle)
    hd = J('hand', s)
    HA = [ball(hd, 0.12, M['frame'], name='wrist')]
    HA.append(hull([(x(a), y, z) for a in (1.44, 1.70) for (y, z) in ((2.44, -0.16), (2.44, 0.20), (2.06, -0.18), (2.06, 0.20))], M['dark'], 0.025, name='fist'))
    HA.append(plate([(x(1.71), 2.42, -0.16), (x(1.71), 2.42, 0.20), (x(1.73), 2.08, 0.19), (x(1.73), 2.08, -0.17)], 0.07, (s, 0, 0), M['paint'], 0.014, name='gauntlet'))
    for k, z in enumerate((-0.125, -0.03, 0.065, 0.15)):  # four curled fingers across the palm side
        HA.append(hull([(x(a), y, zz) for a in (1.42, 1.56) for y in (2.04, 2.20) for zz in (z - 0.045, z + 0.045)], M['frame'], 0.012, name='finger'))
        HA.append(hull([(x(a), y, zz) for a in (1.40, 1.48) for y in (2.18, 2.30) for zz in (z - 0.04, z + 0.04)], M['dark'], 0.01, name='fingertip'))
    HA.append(hull([(x(a), y, z) for a in (1.46, 1.58) for (y, z) in ((2.36, -0.14), (2.26, -0.25), (2.18, -0.21), (2.30, -0.12))], M['frame'], 0.012, name='thumb'))
    mk.add('hand_' + L, HA); T['hand_' + L] = HA


def sword(mk, M, T):
    """the snap-off blade: a box cutter the size of a car. grip through the right fist, blade forward and down"""
    G = JT['sword']; d = GRIP
    w = norm(cross(d, (1, 0, 0)))  # edge to edge, in the plane of the swing (the angled tip's long edge is +w)
    t = norm(cross(d, w))  # the flats face +-t
    P = lambda a, b, c: add(G, add(mul(d, a), add(mul(w, b), mul(t, c))))
    S = []
    S.append(frustum(P(-0.34, 0, 0), P(0.24, 0, 0), 0.075, 0.075, M['rubber'], 8, bev=0.01, ref=w, name='grip'))
    for a in (-0.22, -0.06, 0.10):
        S.append(frustum(P(a, 0, 0), P(a + 0.04, 0, 0), 0.085, 0.085, M['paint'], 8, bev=0.006, ref=w, name='grip_ring'))
    S.append(hull([P(a, b, c) for a in (-0.50, -0.34) for b in (-0.12, 0.12) for c in (-0.11, 0.11)] + [P(-0.56, 0, 0)], M['paint'], 0.02, name='pommel'))
    # the slider housing (like a cutter's body) and a chunky guard
    S.append(hull([P(a, b, c) for a in (0.22, 0.62) for b in (-0.30, 0.34) for c in (-0.13, 0.13)] + [P(0.70, 0.30, 0), P(0.66, -0.26, 0)], M['white'], 0.025, name='housing'))
    S.append(hull([P(a, b, c) for a in (0.24, 0.38) for b in (-0.56, 0.58) for c in (-0.10, 0.10)], M['frame'], 0.02, name='guard'))
    S.append(hull([P(a, b, c) for a in (0.27, 0.35) for b in (-0.60, -0.50) for c in (-0.11, 0.11)], M['accent'], 0.01, name='guard_cap'))
    S.append(hull([P(a, b, c) for a in (0.27, 0.35) for b in (0.52, 0.62) for c in (-0.11, 0.11)], M['accent'], 0.01, name='guard_cap'))
    S.append(hull([P(a, b, c) for a in (0.30, 0.52) for b in (0.20, 0.30) for c in (-0.145, 0.145)], M['chrome'], 0.008, name='slider'))
    # the blade: a diamond section, an angled tip (snap-off blades are cut on the diagonal)
    L0, L1, hw = 0.60, 3.30, 0.24
    bl = []
    for a, half in ((L0, hw), (L1 - 0.45, hw * 0.92)):
        bl += [P(a, half, 0), P(a, -half, 0), P(a, 0, 0.06), P(a, 0, -0.06), P(a, half * 0.6, 0.035), P(a, -half * 0.6, 0.035), P(a, half * 0.6, -0.035), P(a, -half * 0.6, -0.035)]
    bl += [P(L1, -hw * 0.92, 0), P(L1 - 0.08, -hw * 0.5, 0.02), P(L1 - 0.08, -hw * 0.5, -0.02)]
    blade = hull(bl, M['blade'], 0.01, name='blade'); S.append(blade); T['blade'] = blade
    # energy edges: glowing strips along both edges and round the tip
    for sd in (-1, 1):
        a0, a1 = L0 + 0.02, (L1 - 0.47 if sd > 0 else L1 - 0.02)
        S.append(hull([P(a, sd * (hw - 0.005), c) for a in (a0, a1) for c in (-0.012, 0.012)] + [P(a, sd * (hw + 0.035), 0) for a in (a0, a1)], M['glow'], 0.004, name='edge'))
    S.append(hull([P(L1 - 0.47, hw * 0.92 - 0.005, c) for c in (-0.012, 0.012)] + [P(L1 - 0.02, -hw * 0.92 + 0.005, c) for c in (-0.012, 0.012)] +
                  [P(L1 - 0.47 + 0.02, hw * 0.92 + 0.03, 0), P(L1 + 0.02, -hw * 0.92 - 0.02, 0)], M['glow'], 0.004, name='edge_tip'))
    mk.add('sword', S); T['sword'] = S
    T['sword_frame'] = (G, d, w, t, L0, L1, hw)
    mk.meta.setdefault('marks', {}).update({'mk_sword_base': {'joint': 'sword', 'at': P(L0, 0, 0), 'dir': d}, 'mk_sword_tip': {'joint': 'sword', 'at': P(L1, 0, 0), 'dir': d}})


def shield(mk, M, T):
    """the tower shield on the outside of the left forearm (rest pose: long side along the arm, face out -x)"""
    c = (-1.88, 2.92, 0.07)
    hw, hh, th = 0.68, 1.30, 0.16
    def Q(u, v, n): return add(c, (-n, v, u))  # u = across the face (z), v = along the arm (y), n = out of the face (-x)
    S = []
    oc = [(-hw, -hh + 0.22), (-hw + 0.22, -hh), (hw - 0.22, -hh), (hw, -hh + 0.22), (hw, hh - 0.22), (hw - 0.22, hh), (-hw + 0.22, hh), (-hw, hh - 0.22)]
    body = hull([Q(u, v, n) for (u, v) in oc for n in (-th / 2, th / 2)] + [Q(0, v, th / 2 + 0.06) for v in (-hh + 0.1, hh - 0.1)], M['paint'], 0.03, 2, name='shield')
    S.append(body)
    sb = bvh_of([body])
    out = (-1, 0, 0)
    def face(pts, o, m, nm): return skin(sb, [Q(u, v, 1.0) for (u, v) in pts], (1, 0, 0), o, 0.03, m, 0.005, nm)
    fi = 0.10
    S.append(face([(-hw + fi, -hh + 0.22 + fi * 0.4), (-hw + 0.22 + fi * 0.4, -hh + fi), (hw - 0.22 - fi * 0.4, -hh + fi), (hw - fi, -hh + 0.22 + fi * 0.4),
                   (hw - fi, hh - 0.22 - fi * 0.4), (hw - 0.22 - fi * 0.4, hh - fi), (-hw + 0.22 + fi * 0.4, hh - fi), (-hw + fi, hh - 0.22 - fi * 0.4)], 0.010, M['white'], 'field'))
    S.append(face([(-0.46, 0.0), (0.46, 0.0), (-0.46, -0.50), (0.46, -0.50)], 0.022, M['dark'], 'screen_bezel'))
    S.append(face([(-0.41, -0.04), (0.41, -0.04), (-0.41, -0.46), (0.41, -0.46)], 0.030, M['glass'], 'screen'))
    # rivets round the field, a handle bar on the back
    for (u, v) in [(-hw + 0.06, y) for y in (-0.7, 0, 0.7)] + [(hw - 0.06, y) for y in (-0.7, 0, 0.7)] + [(x, -hh + 0.06) for x in (-0.3, 0.3)] + [(x, hh - 0.06) for x in (-0.3, 0.3)]:
        q, n = proj(sb, Q(u, v, 1.0), (1, 0, 0))
        if q: S.append(ball(add(q, mul(n, 0.004)), 0.03, M['chrome'], 8, 6, 'rivet'))
    S.append(hull([add(c, (dx, y, z)) for dx in (0.06, 0.16) for y in (2.74 - 2.92, 3.10 - 2.92) for z in (-0.10, 0.22)], M['frame'], 0.015, name='shield_mount'))
    mk.add('shield', S); T['shield'] = S
    T['shield_frame'] = (c, hw, hh, th)
    mk.meta.setdefault('marks', {})['mk_shield_face'] = {'joint': 'shield', 'at': Q(0, 0, th / 2 + 0.07), 'dir': (-1, 0, 0)}


def decals(mk, M, T):
    led = tex_mat('ns_ledmat', led_img(), 0.2, emit=2.5, cc=1.0)
    hz = tex_mat('ns_hazardmat', hazard_img(), 0.4)
    st = tex_mat('ns_sticker', sticker_img('ns_howsmy', ["HOW'S MY PILOTING?", 'CALL 1-800-JANK'], 0xffe14d, 0x111111, 192, 44, 1), 0.4)
    pk = tex_mat('ns_park', sticker_img('ns_parkimg', ['STAFF', 'PARKING', 'ONLY'], 0xf4f2ec, 0xc02020, 72, 72, 2, 0xc02020), 0.4)
    bd = tex_mat('ns_badge', stencil_img('ns_badgeimg', 'NIGHT', 0x2a1a08, 72, 20, 2), 0.3, clip=True)
    bd2 = tex_mat('ns_badge2', stencil_img('ns_badgeimg2', 'SHIFT', 0x2a1a08, 72, 20, 2), 0.3, clip=True)
    num = tex_mat('ns_247', stencil_img('ns_247img', '24/7', 0xffe14d, 104, 40, 4), 0.35, clip=True)
    br = tex_mat('ns_breathmat', breaths_img(), 0.3, clip=True)
    sn = tex_mat('ns_snapmat', snap_img(), 0.3, clip=True)
    tc = tex_mat('ns_timecardmat', timecard_img(), 0.45, cc=0.2)
    card, tc_c, tc_n, tc_u = T['timecard']
    mk.add('hatch', decal([card], tc_c, tc_n, tc_u, 0.18, 0.27, tc, name='timecard_face', reach=0.2))
    cf = tex_mat('ns_coffee', sticker_img('ns_coffeeimg', ['JANK', 'COFFEE'], 0xf6f0e4, 0x5a3010, 72, 44, 2, 0x5a3010), 0.4)
    # the PLEASE HOLD screen, facing out of the shield
    c, hw, hh, th = T['shield_frame']
    mk.add('shield', decal(T['shield'], add(c, (-th / 2 - 0.06, -0.25, 0.0)), (-1, 0, 0), (0, -1, 0), 0.80, 0.40, led, name='hold', reach=0.4))  # (reads upright with the shield up)
    for v in (-hh + 0.10, hh - 0.10):
        mk.add('shield', decal(T['shield'], add(c, (-0.2, v, 0.0)), (-1, 0, 0), (0, 0, 1) if False else (0, 1, 0), 1.0, 0.09, hz, name='shieldhaz', reach=0.5))
    mk.add('shield', decal(T['shield'], add(c, (0.2, -0.4, 0.2)), (1, 0, 0), (0, 1, 0), 0.30, 0.30, pk, name='park', reach=0.5))
    mk.add('backpack', decal(T['backpack'], (0, 3.98, 1.10), (0, 0, 1), (0, 1, 0), 0.56, 0.13, st, name='howsmy'))
    mk.add('hatch', decal(T['hatch'], (-0.42, 4.60, -0.75), (0, 0, -1), (0, 1, 0), 0.18, 0.05, bd, name='badge_t', reach=0.5))
    mk.add('hatch', decal(T['hatch'], (-0.42, 4.53, -0.75), (0, 0, -1), (0, 1, 0), 0.18, 0.05, bd2, name='badge_t2', reach=0.5))
    for s, L in ((1, 'R'), (-1, 'L')):
        mk.add('shoulder_' + L, decal(T['shoulder_' + L], (s * 1.80, 4.60, 0.06), (s, 0.15, 0), (0, 1, 0), 0.40, 0.15, num, name='num'))
        mk.add('shoulder_' + L, decal(T['shoulder_' + L], (s * 1.90, 4.33, 0.06), (s, 0.05, 0), (0, 1, 0), 0.50, 0.08, hz, name='paulhaz'))
    mk.add('head', decal(T['head'], add(JT['head'], (0.16, 0.12, -0.36)), (0.35, 0, -1), (0, 1, 0), 0.13, 0.13, br, name='breaths'))
    G, d, w, t, L0, L1, hw = T['sword_frame']
    a0, a1 = L0 + 0.12, L1 - 0.55
    for sd in (-1, 1):  # the snap-off lines, both flats, on the blade only
        mid = add(G, mul(d, (a0 + a1) / 2))
        mk.add('sword', decal([T['blade']], add(mid, mul(t, sd * 0.1)), mul(t, sd), d, 0.40, a1 - a0, sn, name='snap', reach=0.3))
    mk.add('hips', decal(T['hips'], (-0.74, 2.64, -0.27), (0, 0, -1), (0, 1, 0), 0.16, 0.10, cf, name='coffee'))


# ------------------------------------------------------------ poses (three.js XYZ euler per joint, radians)
def pose_ready(mk):
    """shield up (forearm vertical, twisted so the face looks forward), sword low and forward: the concept stance"""
    r = math.radians
    return {
        'hips': (0, r(10), 0), 'chest': (0, r(-12), 0), 'head': (r(-4), r(8), 0),
        'upperarm_L': (r(38), r(-10), r(-14)), 'forearm_L': (r(132), r(90), 0), 'hand_L': (0, 0, 0),
        'upperarm_R': (r(12), r(0), r(10)), 'forearm_R': (r(18), r(-35), 0), 'hand_R': (r(-38), 0, 0),
        'thigh_L': (r(16), 0, r(-4)), 'shin_L': (r(-20), 0, 0), 'foot_L': (r(4), 0, 0),
        'thigh_R': (r(-12), 0, r(7)), 'shin_R': (r(-8), 0, 0), 'foot_R': (r(20), 0, 0),
    }


POSES = {'ready': pose_ready, 'rest': lambda mk: {}}
