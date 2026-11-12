# PAPER PLANE: the light flyer (about 5 m to the helmet, the wing tips at 5.7 m). An original JANKFIRE frame built
# like folded paper: every armour plate is a crisp origami facet, the chest is a paper plane's nose with the canopy on
# its keel, the wings are two folded paper halves on hinges at the shoulder blades (stowed up and out like a V; they
# swing down and back flat for jet mode), the missile pods are full of homing pencils (pink erasers out the back), a
# paperclip for an antenna, notebook paper under the wings. Concept pass (phase 1): blockout + paint, joints ready to pose.
# Game space: the mech faces -z, its right is +x, feet on y = 0.
from mechkit import *

DECALS = True  # (off for the Tripo reference pictures: no text or stickers)

FID = 'mech_paperplane'
PAL_A = {  # "SKY MAIL": sky blue + white + yellow on a navy frame, a yellow shutter visor, cyan thrust
    'paint': 0x2fb8ff, 'white': 0xf3f0e8, 'dark': 0x1d2747, 'accent': 0xffd23a, 'frame': 0x3a4152, 'chrome': 0xd2d9e2,
    'rubber': 0x17171c, 'glass': 0x12384f, 'glow': 0xffe14d, 'thrust': 0x5fe4ff, 'brass': 0xd9a640,
    'pencil': 0xffc21a, 'wood': 0xe8bf8a, 'eraser': 0xff8fb4, 'lead': 0x2a2a30, 'paper': 0xf7f4ec, 'cup': 0xfafafa,
}
PAL_B = {  # "PINK SLIP": hot pink + white + yellow on plum, a cyan shutter visor, pink thrust
    'paint': 0xff3fcf, 'white': 0xf6f0f2, 'dark': 0x2c1446, 'accent': 0xffe14d, 'frame': 0x40384e, 'glass': 0x2a1240,
    'glow': 0x4fe8ff, 'thrust': 0xff6ae0,
}
for k in ('pencil', 'wood', 'eraser', 'lead', 'paper', 'cup'): ROLE_LOOK.setdefault(k, (0.4, 0.0, 0.6))
ROLE_LOOK['lead'] = (0.3, 0.6, 0.0)

# the joints (rest pose), right side; the left is the mirror
JT = {
    'hips': (0, 2.62, 0.0), 'waist': (0, 2.98, 0.04), 'chest': (0, 3.22, 0.04), 'neck': (0, 4.06, -0.02), 'head': (0, 4.22, -0.03),
    'shoulder': (0.56, 3.92, 0.08), 'upperarm': (0.98, 3.86, 0.08), 'forearm': (1.06, 3.04, 0.10), 'hand': (1.11, 2.26, 0.05),
    'thigh': (0.40, 2.55, 0.0), 'shin': (0.44, 1.52, -0.06), 'foot': (0.46, 0.50, 0.06), 'toe': (0.46, 0.13, -0.40),
    'skirt': (0.50, 2.84, 0.0), 'pod': (0.99, 4.24, 0.12), 'backpack': (0, 3.62, 0.50), 'wing': (0.30, 4.02, 0.86),
    'hatch': (0, 4.02, -0.40),
}
WING_PHI, WING_PSI = math.radians(100), math.radians(-18)  # the stow: swung up about the back normal, tilted back
CRANE_AT = (-0.66, 3.30, 0.935)  # the crane drone's seat on the left wing, in the wing's jet layout (on its top face)


def J(n, s=1): return mx(JT[n], s)


# ------------------------------------------------------------ paint jobs (textures)
def notebook_img():
    """the wings' undersides: ruled notebook paper, a red margin, a doodle and a tag"""
    W, H = 256, 256; px = canvas(W, H, 0xf7f4ec)
    for y in range(22, H, 12): fill(px, 0, y, W, y + 1, 0x8fc6ef)
    fill(px, 40, 0, 42, H, 0xf06a7a)
    text(px, 'JANK', 60, 50, 3, 0x3a4a9a); text(px, 'AIR', 62, 76, 3, 0x3a4a9a)
    for (x, y) in ((150, 120), (190, 160), (130, 190)):  # a smiley doodle and stars in biro
        lib.px_disc(px[:, :, :3], x, y, 9, 0x3a4a9a, r_in=7.5); px[y - 9:y + 10, x - 9:x + 10, 3] = 1
    text(px, '80 GSM', 120, 220, 2, 0x8a8a9a)
    crust(px, 0.03, 3, 0.004)
    return image_rgba('pp_notebook', px)


def sticker_img(name, lines, bg, fg, w=160, h=56, sc=2, bd=0x111111):
    px = canvas(w, h, bg); border(px, 3, bd)
    y = (h - len(lines) * 9 * sc) // 2 + 1
    for i, s in enumerate(lines): text_c(px, s, w / 2, y + i * 9 * sc, sc, fg)
    crust(px, 0.03, len(name), 0.003)
    return image_rgba(name, px)


def stencil_img(name, s, col, w=96, h=40, sc=4):
    px = canvas(w, h); text_c(px, s, w / 2, (h - 7 * sc) // 2, sc, col)
    return image_rgba(name, px)


def fold_img():
    """FOLD HERE: a dashed line and a pair of scissors (alpha everywhere else)"""
    ink = np.zeros((32, 256, 3), np.float32)
    for xx in range(34, 256, 18): ink[14:18, xx:xx + 10] = 1
    lib.px_disc(ink, 8, 9, 6, 0xffffff, r_in=3.5); lib.px_disc(ink, 8, 23, 6, 0xffffff, r_in=3.5)
    lib.px_line(ink, 12, 12, 28, 19, 0xffffff, 2); lib.px_line(ink, 12, 20, 28, 13, 0xffffff, 2)
    text_px(ink, 'FOLD HERE', 150, 3, 1, 0xffffff)
    px = canvas(256, 32); m = ink[:, :, 0] > 0.5
    px[m, :3] = hexrgb(0x262a40); px[m, 3] = 1
    return image_rgba('pp_fold', px)


def hazard_img(a=0xffd23a, b=0x16161c):
    px = canvas(64, 16); stripes(px, 0, 0, 64, 16, a, b, 5)
    return image_rgba('pp_hazard', px)


# ------------------------------------------------------------ build
def build():
    mk = Mech(FID, 'pp', PAL_A); M = mk.M
    mk.joint('root', (0, 0, 0)); mk.joint('hips', JT['hips'], 'root'); mk.joint('waist', JT['waist'], 'hips')
    mk.joint('chest', JT['chest'], 'waist'); mk.joint('neck', JT['neck'], 'chest'); mk.joint('head', JT['head'], 'neck')
    mk.joint('hatch', JT['hatch'], 'chest'); mk.joint('backpack', JT['backpack'], 'chest')
    for s, L in ((1, 'R'), (-1, 'L')):
        mk.joint('shoulder_' + L, J('shoulder', s), 'chest'); mk.joint('pod_' + L, J('pod', s), 'shoulder_' + L)
        mk.joint('upperarm_' + L, J('upperarm', s), 'shoulder_' + L); mk.joint('forearm_' + L, J('forearm', s), 'upperarm_' + L)
        mk.joint('hand_' + L, J('hand', s), 'forearm_' + L); mk.joint('cannon_' + L, (s * 1.12, 2.45, -0.10), 'forearm_' + L)
        mk.joint('thigh_' + L, J('thigh', s), 'hips'); mk.joint('shin_' + L, J('shin', s), 'thigh_' + L)
        mk.joint('foot_' + L, J('foot', s), 'shin_' + L); mk.joint('toe_' + L, J('toe', s), 'foot_' + L)
        mk.joint('skirt_' + L, J('skirt', s), 'hips'); mk.joint('wing_' + L, J('wing', s), 'backpack')
    mk.joint('drone', g_of(wing_stow(-1) @ gv(*CRANE_AT)), 'wing_L')  # (the origami crane drone)
    for L in ('L', 'R'): mk.joint('drone_wing_' + L, g_of(wing_stow(-1) @ gv(*add(CRANE_AT, (0, 0, 0.07)))), 'drone')
    T = {}  # decal targets per joint
    head(mk, M, T); torso(mk, M, T)
    for s, L in ((1, 'R'), (-1, 'L')):
        leg(mk, M, T, s, L); arm(mk, M, T, s, L); cannon(mk, M, T, s, L); wing(mk, M, T, s, L); skirt(mk, M, T, s, L)
    crane(mk, M, T)
    if DECALS: decals(mk, M, T)
    mk.meta.update({'name': 'PAPER PLANE', 'height': 4.85, 'phase': 'concept',
                    'palettes': {'A': {k: PAL_A[k] for k in ('paint', 'white', 'dark', 'accent', 'glow', 'thrust')},
                                 'B': {k: PAL_B[k] for k in ('paint', 'white', 'dark', 'accent', 'glow', 'thrust')}},
                    'wing_stow': {'phi': WING_PHI, 'psi': WING_PSI}})
    return mk


HS = 1.2  # the head is drawn in its own space (y 0 = the neck top) and scaled up


def hp(x, y, z): return add(JT['head'], (x * HS, y * HS, z * HS))


def head(mk, M, T):
    H = []
    P = lambda pts: [hp(*p) for p in pts]
    H.append(hull(P([(sx * 0.16, y, z) for sx in (-1, 1) for y in (0.0, 0.30) for z in (-0.15, 0.20)]), M['frame'], 0.015, name='skull'))
    # helmet: a folded brow that points forward like a paper plane's nose
    top = [(0, 0.455, -0.08), (0, 0.435, 0.22), (0, 0.26, -0.345)]
    for s in (-1, 1):
        top += [(s * 0.19, 0.39, -0.13), (s * 0.18, 0.39, 0.21), (s * 0.275, 0.225, -0.195), (s * 0.285, 0.21, 0.06),
                (s * 0.245, 0.10, 0.25), (s * 0.20, 0.23, 0.31)]
    top += [(0, 0.09, 0.335), (0, 0.25, 0.35)]
    H.append(hull(P(top), M['white'], 0.016, name='helm'))
    # face mask under the visor (paint), with a chin
    face = [(0, 0.105, -0.335), (0, -0.075, -0.285), (0, -0.01, -0.10)]
    for s in (-1, 1): face += [(s * 0.21, 0.105, -0.21), (s * 0.10, -0.05, -0.24), (s * 0.20, -0.01, 0.0), (s * 0.22, 0.11, 0.0)]
    H.append(hull(P(face), M['dark'], 0.012, name='face'))
    for s in (-1, 1):  # jaw guards (paint) sweep forward to a point beside the chin
        H.append(hull(P([(s * 0.29, 0.20, -0.10), (s * 0.29, 0.20, 0.10), (s * 0.235, 0.20, -0.14), (s * 0.235, 0.20, 0.10),
                         (s * 0.27, -0.02, 0.06), (s * 0.22, -0.02, 0.06), (s * 0.20, -0.04, -0.20), (s * 0.235, 0.02, -0.21)]), M['paint'], 0.01, name='jaw'))
        H.append(hull(P([(s * 0.236, 0.07, -0.18), (s * 0.236, 0.10, -0.21), (s * 0.26, 0.09, -0.15), (s * 0.12, 0.045, -0.262), (s * 0.13, 0.075, -0.275)]), M['dark'], 0.004, name='cheekline'))
    # visor (dark glass): a V across the face behind a split shutter: glowing slats either side of the keel
    # (deliberately not a pair of eyes)
    vis = [(0, 0.235, -0.352), (0, 0.09, -0.342), (0, 0.23, -0.20), (0, 0.09, -0.20)]
    for s in (-1, 1): vis += [(s * 0.262, 0.215, -0.208), (s * 0.252, 0.095, -0.186), (s * 0.20, 0.22, -0.06), (s * 0.20, 0.09, -0.06)]
    H.append(hull(P(vis), M['glass'], 0.005, name='visor'))
    for s in (-1, 1):
        n = norm((s * 0.454, 0, -0.891))
        for k, yc in enumerate((0.200, 0.163, 0.126)):  # three slats, the top one widest
            x1 = 0.235 - 0.02 * k
            a, b = (s * 0.03, yc + 0.012, -0.343), (s * x1, yc + 0.012, -0.343 + x1 * 0.48)
            c, d = (s * x1, yc - 0.012, -0.343 + x1 * 0.48), (s * 0.03, yc - 0.012, -0.343)
            H.append(hull([hp(*add(p, mul(n, 0.012))) for p in (a, b, c, d)] + [hp(*add(p, mul(n, -0.01))) for p in (a, b, c, d)], M['glow'], 0.003, name='shutter'))
    H.append(hull(P([(x, y, z) for x in (-0.022, 0.022) for (y, z) in ((0.24, -0.37), (0.085, -0.36), (0.24, -0.30), (0.085, -0.30))]), M['white'], 0.004, name='shutter_split'))
    for s in (-1, 1):
        H.append(tri_plate(hp(s * 0.27, 0.26, -0.06), hp(s * 0.27, 0.06, 0.10), hp(s * 0.33, 0.39, 0.40), 0.035 * HS, M['white'], name='ear'))
        H.append(tri_plate(hp(s * 0.285, 0.31, 0.12), hp(s * 0.29, 0.24, 0.17), hp(s * 0.336, 0.395, 0.405), 0.045 * HS, M['paint'], name='ear_tip'))
    H.append(hull(P([(0, 0.22, -0.365), (0, 0.525, -0.02), (0, 0.505, 0.20), (0, 0.37, 0.37), (0.04, 0.26, -0.32), (-0.04, 0.26, -0.32),
                     (0.05, 0.41, 0.0), (-0.05, 0.41, 0.0), (0.045, 0.38, 0.30), (-0.045, 0.38, 0.30)]), M['paint'], 0.01, name='crest'))
    # the paperclip antenna, clipped onto the left ear
    a0 = hp(-0.30, 0.19, 0.10); up = norm((-0.25, 1, 0.55)); side = norm(cross(up, (1, 0, 0)))
    def Q(v, u): return add(a0, add(mul(side, v * HS), mul(up, u * HS)))
    clip = []
    def arc(cv, cu, r, a1, a2, n=6):
        for i in range(n + 1):
            t = math.radians(a1 + (a2 - a1) * i / n); clip.append(Q(cv + r * math.cos(t), cu + r * math.sin(t)))
    clip.append(Q(0.018, 0.10)); clip.append(Q(0.018, 0.33)); arc(0, 0.33, 0.018, 0, 180)
    clip.append(Q(-0.018, 0.06)); arc(0.008, 0.06, 0.026, 180, 360); clip.append(Q(0.034, 0.37)); arc(0.0, 0.37, 0.034, 0, 180)
    clip.append(Q(-0.034, 0.16))
    H.append(tube(clip, 0.0085, M['chrome'], 6, 'paperclip'))
    mk.add('head', H); T['head'] = H
    N = [frustum((0, 4.02, 0.0), (0, 4.30, -0.03), 0.13, 0.11, M['frame'], 8, name='neckcol')]
    for s in (-1, 1): N.append(tube([(s * 0.10, 4.06, 0.10), (s * 0.15, 4.16, 0.12), (s * 0.12, 4.28, 0.06)], 0.025, M['rubber'], 8, 'hose'))
    mk.add('neck', N)


def torso(mk, M, T):
    C = []
    C.append(hull([(sx * x, y, z) for sx in (-1, 1) for (x, y) in ((0.46, 3.20), (0.56, 3.99)) for z in (-0.32, 0.40)], M['frame'], 0.025, name='core'))
    # the nose: two big facets that meet on the keel (paint)
    nose = [(0, 4.02, -0.50), (0, 3.62, -0.67), (0, 3.30, -0.50), (0, 4.02, -0.20), (0, 3.30, -0.22)]
    for s in (-1, 1): nose += [(s * 0.70, 4.04, -0.28), (s * 0.74, 3.70, -0.30), (s * 0.48, 3.32, -0.31), (s * 0.64, 4.04, -0.08), (s * 0.44, 3.32, -0.10)]
    hatch = [hull(nose, M['paint'], 0.02, name='nose')]
    # the canopy on the keel (glass) in a white frame, a white strip down the fold: laid onto the nose
    nb = bvh_of(hatch)
    fwd = (0, 0, 1)
    hatch.append(skin(nb, [(0, 4.035, -1), (0.31, 4.035, -1), (-0.31, 4.035, -1), (0.27, 3.90, -1), (-0.27, 3.90, -1), (0, 3.64, -1)], fwd, 0.008, 0.03, M['white'], 0.006, 'canopy_frame'))
    hatch.append(skin(nb, [(0, 4.005, -1), (0.255, 4.005, -1), (-0.255, 4.005, -1), (0.215, 3.915, -1), (-0.215, 3.915, -1), (0, 3.70, -1)], fwd, 0.016, 0.03, M['glass'], 0.005, 'canopy'))
    hatch.append(skin(nb, [(0.04, 3.62, -1), (-0.04, 3.62, -1), (0.05, 3.32, -1), (-0.05, 3.32, -1), (0, 3.30, -1)], fwd, 0.008, 0.02, M['white'], 0.004, 'keelstrip'))
    hatch.append(skin(nb, [(0.30, 3.40, -1), (-0.30, 3.40, -1), (0.40, 3.47, -1), (-0.40, 3.47, -1), (0, 3.31, -1), (0, 3.37, -1)], fwd, 0.007, 0.02, M['accent'], 0.003, 'chinstripe'))
    mk.add('hatch', hatch); T['hatch'] = hatch
    for s in (-1, 1):
        # yoke over the shoulders (white), side plates under the arms (white), the waist plate (dark)
        C.append(plate([(s * 0.22, 4.15, -0.22), (s * 0.76, 4.04, -0.20), (s * 0.78, 4.02, 0.34), (s * 0.22, 4.15, 0.36), (s * 0.50, 4.11, -0.30)], 0.09, (s * 0.18, 1, 0), M['white'], 0.012, name='yoke'))
        C.append(hull([(s * x, y, z) for x in (0.52, 0.72) for y in (3.36, 3.96) for z in (-0.22, 0.34)] + [(s * 0.76, 3.70, 0.06)], M['white'], 0.02, name='flank'))
        C.append(hull([(s * 0.50, 3.33, -0.30), (s * 0.12, 3.24, -0.40), (s * 0.48, 3.30, 0.30), (s * 0.12, 3.22, 0.34), (s * 0.40, 3.42, 0.0), (s * 0.12, 3.44, -0.3)], M['dark'], 0.015, name='rib'))
        # vents on the flanks (dark slats)
        for k in range(3):
            y = 3.50 + k * 0.12
            C.append(hull([(s * 0.735, y, -0.12), (s * 0.735, y, 0.22), (s * 0.735, y + 0.06, -0.12), (s * 0.735, y + 0.06, 0.22),
                           (s * 0.70, y, -0.12), (s * 0.70, y, 0.22), (s * 0.70, y + 0.06, -0.12), (s * 0.70, y + 0.06, 0.22)], M['dark'], 0.006, name='slat'))
    C.append(hull([(sx * 0.54, y, z) for sx in (-1, 1) for y in (3.30, 4.02) for z in (0.30, 0.46)], M['white'], 0.02, name='backplate'))
    mk.add('chest', C); T['chest'] = C + hatch
    # backpack: a wedge (white) with a dark spine, two big thrusters, the wing hinges
    B = [hull([(0, 3.70, 0.84)] + [(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.38, 3.22, 0.40), (0.42, 4.02, 0.40), (0.30, 4.06, 0.72), (0.24, 3.26, 0.74))],
              M['white'], 0.025, name='pack')]
    B.append(hull([(s * 0.12, y, z) for s in (-1, 1) for (y, z) in ((3.30, 0.76), (3.98, 0.73), (3.30, 0.86), (3.98, 0.84))], M['dark'], 0.012, name='spine'))
    for s in (-1, 1):
        B += nozzle((s * 0.22, 3.30, 0.64), (0, -1, 0.35), 0.15, 0.30, M, 'main')
        B.append(cyl((s * 0.30, 4.02, 0.66), (s * 0.30, 4.02, 0.90), 0.10, M['frame'], 16, name='hinge'))
        B.append(cyl((s * 0.30, 4.02, 0.88), (s * 0.30, 4.02, 0.93), 0.065, M['accent'], 16, name='hinge_cap'))
    mk.add('backpack', B); T['backpack'] = B
    # waist: spine discs (frame), pistons (chrome in frame sleeves), two folded ab plates (white)
    W = [cyl((0, 2.78, 0.04), (0, 3.30, 0.04), 0.20, M['frame'], 12, name='spine')]
    for y in (2.92, 3.06, 3.20): W.append(cyl((0, y - 0.03, 0.04), (0, y + 0.03, 0.04), 0.24, M['dark'], 12, name='disc'))
    for s in (-1, 1):
        W.append(cyl((s * 0.30, 2.80, -0.10), (s * 0.34, 3.08, -0.14), 0.05, M['frame'], 10, name='sleeve'))
        W.append(cyl((s * 0.34, 3.02, -0.14), (s * 0.37, 3.36, -0.17), 0.03, M['chrome'], 10, name='rod'))
    for (y0, y1, w, z) in ((2.86, 3.03, 0.22, -0.33), (3.05, 3.24, 0.26, -0.35)):
        W.append(hull([(0, y0, z - 0.05), (0, y1, z - 0.07)] + [(s * w, y, z) for s in (-1, 1) for y in (y0, y1)] + [(s * w * 0.8, y, z + 0.18) for s in (-1, 1) for y in (y0, y1)],
                      M['white'], 0.012, name='ab'))
    mk.add('waist', W); T['waist'] = W
    # pelvis: frame block, the paint chevron in front, a back plate
    P = [hull([(sx * x, y, z) for sx in (-1, 1) for (x, y) in ((0.30, 2.40), (0.42, 2.84)) for z in (-0.28, 0.30)], M['frame'], 0.025, name='pelvis')]
    P.append(hull([(0, 2.27, -0.44), (0, 2.86, -0.45), (0, 2.30, -0.24), (0, 2.86, -0.24)] + [(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.28, 2.86, -0.38), (0.22, 2.60, -0.40), (0.26, 2.86, -0.22), (0.18, 2.55, -0.24))],
                  M['paint'], 0.015, name='codpiece'))
    P.append(hull([(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.32, 2.86, 0.28), (0.26, 2.40, 0.36), (0.32, 2.86, 0.44), (0.24, 2.44, 0.46))], M['white'], 0.015, name='rear'))
    mk.add('hips', P); T['hips'] = P


def skirt(mk, M, T, s, L):
    S = [plate([(s * 0.47, 2.90, -0.29), (s * 0.49, 2.90, 0.27), (s * 0.70, 2.30, 0.25), (s * 0.68, 2.25, -0.33)], 0.07, (s * 1, -0.33, 0), M['white'], 0.012, name='skirt')]
    S.append(plate([(s * 0.668, 2.36, -0.31), (s * 0.69, 2.39, 0.24), (s * 0.71, 2.29, 0.26), (s * 0.69, 2.23, -0.345)], 0.085, (s * 1, -0.33, 0), M['paint'], 0.008, name='skirt_edge'))
    S.append(cyl((s * 0.40, 2.84, 0.0), (s * 0.55, 2.84, 0.0), 0.07, M['frame'], 12, name='skirt_pin'))
    if s > 0:  # the cup holder: a chrome ring off the skirt and a paper coffee cup with a lid
        c0 = (0.74, 2.50, -0.05)
        S.append(tube([(0.68, 2.50, -0.05), (0.735, 2.50, -0.05)], 0.012, M['chrome'], 6, 'holder_arm'))
        S.append(lathe_ax([(0.066, 0), (0.072, 0.012), (0.066, 0.024)], add(c0, (0.05, -0.012, 0)), (0, 1, 0), M['chrome'], 16, 'holder_ring', cap=False))
        S.append(lathe_ax([(0.055, -0.07), (0.075, 0.10), (0.077, 0.11), (0.06, 0.13), (0.0, 0.13)], add(c0, (0.05, 0, 0)), (0, 1, 0), M['cup'], 16, 'cup'))
        S.append(lathe_ax([(0.068, 0.0), (0.071, 0.06)], add(c0, (0.05, 0.0, 0)), (0, 1, 0), M['wood'], 16, 'sleeve', cap=False))
    mk.add('skirt_' + L, S); T['skirt_' + L] = S


def leg(mk, M, T, s, L):
    x = lambda v: s * v
    TH = [ball(J('thigh', s), 0.17, M['frame'], name='hipball'),
          frustum((x(0.40), 2.50, 0.0), (x(0.44), 1.62, -0.04), 0.17, 0.15, M['frame'], 8, name='femur')]
    TH.append(hull([(x(0.41), 2.42, -0.33), (x(0.435), 1.74, -0.27)] + [(x(a), y, z) for (a, y, z) in ((0.22, 2.40, -0.20), (0.60, 2.40, -0.18), (0.30, 1.76, -0.17), (0.57, 1.76, -0.16),
                   (0.22, 2.34, 0.0), (0.60, 2.34, 0.0), (0.30, 1.80, -0.02), (0.57, 1.80, -0.02))], M['white'], 0.016, name='thighplate'))
    TH.append(plate([(x(0.62), 2.34, -0.16), (x(0.62), 2.34, 0.16), (x(0.60), 1.84, 0.14), (x(0.60), 1.84, -0.14)], 0.07, (s, 0, 0), M['paint'], 0.012, name='thighside'))
    TH.append(cyl((x(0.42), 2.30, 0.12), (x(0.43), 2.00, 0.13), 0.05, M['frame'], 10, name='t_sleeve'))
    TH.append(cyl((x(0.43), 2.04, 0.13), (x(0.44), 1.70, 0.12), 0.028, M['chrome'], 10, name='t_rod'))
    mk.add('thigh_' + L, TH); T['thigh_' + L] = TH
    SH = [cyl((x(0.27), 1.52, -0.06), (x(0.61), 1.52, -0.06), 0.13, M['frame'], 16, name='knee')]
    SH.append(cyl((x(0.25), 1.52, -0.06), (x(0.63), 1.52, -0.06), 0.07, M['accent'], 12, name='knee_cap_pin'))
    SH.append(hull([(x(0.44), 1.82, -0.26), (x(0.44), 1.40, -0.39), (x(0.44), 1.44, -0.16)] + [(x(a), y, z) for a in (0.29, 0.59) for (y, z) in ((1.70, -0.21), (1.40, -0.25), (1.72, -0.10))],
                   M['paint'], 0.014, name='kneecap'))
    SH.append(frustum((x(0.44), 1.45, -0.04), (x(0.45), 0.62, 0.04), 0.12, 0.11, M['frame'], 8, name='tibia'))
    shin = hull([(x(0.44), 1.38, -0.27), (x(0.44), 0.64, -0.45)] + [(x(a), y, z) for (a, y, z) in ((0.32, 1.40, -0.21), (0.56, 1.40, -0.21), (0.22, 0.66, -0.30), (0.66, 0.66, -0.30),
                   (0.28, 1.38, 0.02), (0.60, 1.38, 0.02), (0.22, 0.66, 0.04), (0.66, 0.66, 0.04))], M['white'], 0.016, name='shinplate')
    SH.append(shin); sb = bvh_of([shin])
    for sd in (-1, 1):  # a paint chevron on the shin's fold
        SH.append(skin(sb, [(x(0.44), 0.95, 0), (x(0.44 + sd * 0.17), 0.80, 0), (x(0.44 + sd * 0.17), 0.72, 0), (x(0.44), 0.87, 0)], (0, 0, 1), 0.0075 + 0.004 * (sd > 0), 0.02, M['paint'], 0.003, 'shinchev'))
    SH.append(hull([(x(a), y, z) for (a, y, z) in ((0.28, 1.36, -0.02), (0.60, 1.36, -0.02), (0.30, 1.28, 0.22), (0.58, 1.28, 0.22), (0.29, 0.82, 0.30), (0.59, 0.82, 0.30),
                   (0.27, 0.66, 0.0), (0.61, 0.66, 0.0), (0.44, 1.05, 0.34))], M['paint'], 0.016, name='calf'))
    # calf thruster: a dark vent with a glowing slit
    SH.append(hull([(x(a), y, z) for a in (0.37, 0.51) for (y, z) in ((1.20, 0.30), (0.88, 0.335), (1.20, 0.25), (0.88, 0.28))], M['dark'], 0.008, name='calfvent'))
    SH.append(hull([(x(a), y, z) for a in (0.40, 0.48) for (y, z) in ((1.16, 0.31), (0.92, 0.343), (1.16, 0.28), (0.92, 0.31))], M['thrust'], 0.004, name='calfglow'))
    mk.add('shin_' + L, SH); T['shin_' + L] = SH
    F = [ball(J('foot', s), 0.13, M['frame'], name='ankle')]
    F.append(hull([(x(a), y, z) for (a, y, z) in ((0.30, 0.04, 0.36), (0.62, 0.04, 0.36), (0.33, 0.34, 0.32), (0.59, 0.34, 0.32), (0.35, 0.44, 0.02), (0.57, 0.44, 0.02),
                   (0.28, 0.04, -0.41), (0.64, 0.04, -0.41), (0.32, 0.26, -0.40), (0.60, 0.26, -0.40))], M['paint'], 0.018, name='foot'))
    F.append(hull([(x(a), y, z) for (a, y, z) in ((0.27, 0.0, 0.37), (0.65, 0.0, 0.37), (0.27, 0.0, -0.41), (0.65, 0.0, -0.41), (0.28, 0.06, 0.37), (0.64, 0.06, 0.37), (0.28, 0.06, -0.41), (0.64, 0.06, -0.41))],
                  M['rubber'], 0.008, name='sole'))
    for sx in (0.29, 0.63):  # ankle guards (white)
        F.append(plate([(x(sx), 0.62, -0.10), (x(sx), 0.62, 0.20), (x(sx), 0.34, 0.24), (x(sx), 0.30, -0.14)], 0.06, (s * (1 if sx > 0.46 else -1), 0, 0), M['white'], 0.01, name='ankleguard'))
    F += nozzle((x(0.46), 0.22, 0.36), (0, -0.35, 1), 0.10, 0.16, M, 'heel')
    mk.add('foot_' + L, F); T['foot_' + L] = F
    TO = [hull([(x(a), y, z) for (a, y, z) in ((0.29, 0.03, -0.37), (0.63, 0.03, -0.37), (0.32, 0.25, -0.37), (0.60, 0.25, -0.37), (0.46, 0.03, -0.80), (0.46, 0.10, -0.80), (0.38, 0.18, -0.62), (0.54, 0.18, -0.62))],
               M['white'], 0.015, name='toe')]
    TO.append(hull([(x(a), y, z) for (a, y, z) in ((0.285, 0.0, -0.37), (0.635, 0.0, -0.37), (0.46, 0.0, -0.81), (0.29, 0.05, -0.37), (0.63, 0.05, -0.37), (0.46, 0.05, -0.80))], M['rubber'], 0.006, name='toesole'))
    TO.append(cyl((x(0.30), 0.13, -0.40), (x(0.62), 0.13, -0.40), 0.06, M['frame'], 12, name='toepin'))
    mk.add('toe_' + L, TO); T['toe_' + L] = TO


def cannon(mk, M, T, s, L):
    """twin highlighter cannons under the forearm (MECH DROP fires them from mk_muzzle_*, just past the tips): a pencil
    case clamped on below the cuff, two fat highlighters poking out the front, chisel tips in the team colour"""
    x = lambda v: s * v
    C = [hull([(x(a), y, z) for a in (1.00, 1.24) for y in (2.33, 2.57) for z in (-0.12, -0.44)], M['dark'], 0.03, name='case')]
    C.append(quad_slab([(x(1.02), 2.58, -0.15), (x(1.22), 2.58, -0.15), (x(1.22), 2.58, -0.41), (x(1.02), 2.58, -0.41)], 0.04, M['white'], name='case_lid'))
    C.append(frustum((x(1.09), 2.47, 0.08), (x(1.09), 2.55, 0.08), 0.25, 0.25, M['frame'], 10, squash=(0.95, 1.1), bev=0.01, ref=(1, 0, 0), name='clamp'))
    for dx in (-0.056, 0.056):
        cx = x(1.14) + dx
        C.append(frustum((cx, 2.40, -0.25), (cx, 2.40, -0.62), 0.052, 0.052, M['accent'], 6, bev=0.006, ref=(0, 1, 0), rot=0, name='highlighter'))
        C.append(cyl((cx, 2.40, -0.60), (cx, 2.40, -0.665), 0.058, M['frame'], 12, name='cap_ring'))
        C.append(hull([(cx + a, 2.40 + b, -0.66) for a in (-0.032, 0.032) for b in (-0.03, 0.03)] + [(cx + a, 2.40 + b, -0.75) for a in (-0.03, 0.03) for b in (-0.008, 0.012)], M['paint'], 0.006, name='chisel_tip'))
    mk.add('cannon_' + L, C); T['cannon_' + L] = C


def arm(mk, M, T, s, L):
    x = lambda v: s * v
    SH = [hull([(x(a), y, z) for a in (0.50, 0.86) for y in (3.765, 4.02) for z in (-0.10, 0.26)], M['frame'], 0.02, name='clavicle')]
    pd = [(x(0.70), 4.27, -0.25), (x(0.72), 4.25, 0.37), (x(1.31), 3.92, 0.39), (x(1.30), 3.93, -0.30), (x(1.03), 4.04, -0.40)]
    SH.append(plate(pd, 0.08, (s * 0.45, 0.89, 0), M['paint'], 0.014, name='pauldron'))
    SH.append(plate([(x(1.29), 3.93, -0.29), (x(1.31), 3.92, 0.38), (x(1.33), 3.70, 0.34), (x(1.31), 3.71, -0.24)], 0.06, (s, 0.15, 0), M['white'], 0.01, name='pauldron_lip'))
    mk.add('shoulder_' + L, SH); T['shoulder_' + L] = SH
    # the missile pod: a white wedge of homing pencils (sharpened ends out the front, pink erasers out the back)
    PD = [hull([(x(a), y, z) for a in (0.80, 1.20) for (y, z) in ((4.13, -0.16), (4.13, 0.40), (4.38, -0.20), (4.42, 0.36))] + [(x(1.0), 4.46, 0.10)], M['white'], 0.022, name='pod')]
    PD.append(hull([(x(a), y, z) for a in (0.79, 1.21) for (y, z) in ((4.12, 0.06), (4.12, 0.16), (4.43, 0.06), (4.43, 0.16))], M['paint'], 0.008, name='pod_band'))
    for cx, cy in [(cx, cy) for cy in (4.335, 4.21) for cx in (0.87, 1.0, 1.13)]:  # 2 x 3: six homing pencils a side
        c = (x(cx), cy, 0.0)
        PD.append(frustum(add(c, (0, 0, -0.10)), add(c, (0, 0, -0.30)), 0.056, 0.056, M['pencil'], 6, bev=0.004, ref=(0, 1, 0), rot=0, name='pencil'))
        PD.append(lathe_ax([(0.054, 0.0), (0.012, 0.13)], add(c, (0, 0, -0.298)), (0, 0, -1), M['wood'], 6, 'tip'))
        PD.append(lathe_ax([(0.0135, 0.0), (0.0, 0.035)], add(c, (0, 0, -0.426)), (0, 0, -1), M['lead'], 6, 'lead'))
        PD.append(cyl(add(c, (0, 0, 0.34)), add(c, (0, 0, 0.42)), 0.058, M['chrome'], 10, name='ferrule'))
        PD.append(cyl(add(c, (0, 0, 0.41)), add(c, (0, 0, 0.50)), 0.056, M['eraser'], 10, bev=0.014, name='eraser'))
    mk.add('pod_' + L, PD); T['pod_' + L] = PD
    UA = [ball(J('upperarm', s), 0.17, M['frame'], name='shoulderball'),
          frustum((x(0.99), 3.80, 0.08), (x(1.05), 3.08, 0.10), 0.12, 0.11, M['frame'], 8, name='humerus')]
    UA.append(frustum((x(1.00), 3.64, 0.085), (x(1.04), 3.22, 0.095), 0.175, 0.16, M['white'], 8, name='bicep'))
    UA.append(plate([(x(1.22), 3.86, -0.17), (x(1.25), 3.86, 0.29), (x(1.23), 3.50, 0.25), (x(1.19), 3.50, -0.13)], 0.10, (s, 0.12, 0), M['white'], 0.012, name='delt'))
    mk.add('upperarm_' + L, UA); T['upperarm_' + L] = UA
    FA = [cyl((x(0.93), 3.04, 0.10), (x(1.19), 3.04, 0.10), 0.12, M['frame'], 16, name='elbow'),
          hull([(x(a), y, z) for a in (0.97, 1.15) for (y, z) in ((3.16, 0.12), (2.90, 0.14), (3.16, 0.24), (2.92, 0.26))] + [(x(1.06), 3.03, 0.37)], M['paint'], 0.012, name='elbowcap')]
    FA.append(frustum((x(1.07), 2.96, 0.10), (x(1.11), 2.32, 0.06), 0.15, 0.205, M['paint'], 8, squash=(1.0, 1.15), bev=0.016, ref=(1, 0, 0), name='vambrace'))
    FA.append(frustum((x(1.08), 2.80, 0.095), (x(1.11), 2.44, 0.07), 0.20, 0.215, M['dark'], 8, squash=(0.92, 1.08), bev=0.008, ref=(1, 0, 0), name='cuff'))
    FA.append(tri_plate((x(1.24), 2.95, -0.02), (x(1.28), 2.40, 0.02), (x(1.42), 2.50, 0.40), 0.035, M['white'], name='fin'))
    FA.append(tri_plate((x(1.355), 2.53, 0.24), (x(1.39), 2.47, 0.30), (x(1.425), 2.495, 0.405), 0.045, M['accent'], name='fin_tip'))
    mk.add('forearm_' + L, FA); T['forearm_' + L] = FA
    hd = J('hand', s)
    HA = [ball(hd, 0.09, M['frame'], name='wrist')]
    HA.append(hull([(x(a), y, z) for a in (1.03, 1.20) for (y, z) in ((2.24, -0.13), (2.24, 0.17), (1.95, -0.14), (1.95, 0.16))], M['dark'], 0.014, name='palm'))
    HA.append(plate([(x(1.20), 2.24, -0.11), (x(1.20), 2.24, 0.15), (x(1.21), 2.00, 0.14), (x(1.21), 2.00, -0.12)], 0.05, (s, 0, 0), M['white'], 0.01, name='knuckleguard'))
    for k, z in enumerate((-0.085, -0.01, 0.06, 0.125)):  # fingers, curled a little toward the palm
        p0 = (x(1.12), 1.99 + 0.006 * k, z); p1 = (x(1.08), 1.84 + 0.01 * (k == 3), z); p2 = (x(1.03), 1.74 + 0.03 * (k == 3), z + 0.005)
        HA.append(frustum(p0, p1, 0.042, 0.038, M['frame'], 6, bev=0.006, name='finger'))
        HA.append(frustum(p1, p2, 0.038, 0.033, M['dark'], 6, bev=0.006, name='fingertip'))
    HA.append(frustum((x(1.08), 2.14, -0.12), (x(1.05), 2.00, -0.21), 0.042, 0.036, M['frame'], 6, bev=0.006, name='thumb'))
    HA.append(frustum((x(1.05), 2.00, -0.21), (x(1.02), 1.90, -0.23), 0.036, 0.03, M['dark'], 6, bev=0.006, name='thumbtip'))
    mk.add('hand_' + L, HA); T['hand_' + L] = HA


def wing_stow(s):
    """the robot-mode stow of a wing built flat in its jet layout: up and out about the back normal through the
    hinge, then tilted back"""
    h = J('wing', s)
    return g_rot((0, 1, 0), s * WING_PSI, h) @ g_rot((0, 0, 1), s * WING_PHI, h)


def wing(mk, M, T, s, L):
    """a folded paper half: built flat on the back in its jet layout (R1 the hinge at the shoulder blade, R2 the
    root's far end, Wt the tip), creased from the hinge to the middle of the trailing edge, then stowed"""
    z = 0.90
    R1, R2, Wt = (s * 0.30, 4.02, z), (s * 0.30, 2.77, z), (s * 1.86, 2.64, z)
    Cm = lerp(R2, Wt, 0.5); C = add(Cm, (0, 0, 0.07))  # the fold stands proud of the back
    t2 = 0.0225  # one solid: a flat underside, the top creased into a ridge
    Wg = [hull([R1, R2, Wt, add(C, (0, 0, t2)), add(R1, (0, 0, t2)), add(R2, (0, 0, t2)), add(Wt, (0, 0, t2)), add(R1, (0, 0, -t2)), add(R2, (0, 0, -t2)), add(Wt, (0, 0, -t2))],
               M['white'], 0.008, name='wing')]
    # the leading edge (R1 - Wt) wrapped in paint (standing 4 mm past the edge), the tip in yellow
    out = norm(cross((0, 0, 1), sub(Wt, R1)))  # in the wing's plane, away from the root
    if dot(out, sub(R2, R1)) > 0: out = mul(out, -1)
    eR1, eWt = add(lerp(R1, Wt, 0.03), mul(out, 0.004)), add(lerp(R1, Wt, 0.86), mul(out, 0.004))
    le = [eR1, eWt, add(lerp(eWt, C, 0.13), (0, 0, 0.012)), add(lerp(eR1, C, 0.10), (0, 0, 0.004))]
    Wg.append(quad_slab(le, 0.058, M['paint'], 0.006, 'leading'))
    tip = [add(Wt, mul(out, 0.006)), lerp(Wt, R2, 0.17), add(lerp(Wt, C, 0.30), (0, 0, 0.02)), add(lerp(Wt, R1, 0.15), mul(out, 0.006))]
    Wg.append(quad_slab(tip, 0.07, M['accent'], 0.005, 'wingtip'))
    # trailing edge vents (dark with a glow line) near the root
    te = norm(cross(sub(Wt, R2), (0, 0, 1)))  # in the plane, out past the trailing edge
    if dot(te, sub(R1, R2)) > 0: te = mul(te, -1)
    for t0 in (0.10, 0.28):
        a = add(lerp(R2, Wt, t0), mul(te, 0.004)); b = add(lerp(R2, Wt, t0 + 0.12), mul(te, 0.004))
        Wg.append(quad_slab([a, b, add(b, (0, 0.10, 0)), add(a, (0, 0.10, 0))], 0.07, M['dark'], 0.004, 'vent'))
        Wg.append(quad_slab([add(lerp(a, b, 0.1), (0, 0.012, 0)), add(lerp(a, b, 0.9), (0, 0.012, 0)), add(lerp(a, b, 0.9), (0, 0.045, 0)), add(lerp(a, b, 0.1), (0, 0.045, 0))], 0.076, M['thrust'], 0.002, 'vent_glow'))
    Wg.append(cyl(add(R1, (0, 0, -0.06)), add(R1, (0, 0, 0.05)), 0.085, M['frame'], 16, name='wing_root'))
    Mx = wing_stow(s)
    for o in Wg: xform(o, Mx)
    mk.add('wing_' + L, Wg); T['wing_' + L] = Wg
    mk.meta.setdefault('wing_layout', {})[L] = {'R1': R1, 'R2': R2, 'tip': Wt, 'fold': C}


def crane(mk, M, T):
    """the wing drone: a little origami crane (0.7 m across) docked on the left wing's top face. It peels off, pecks
    the target and comes back (its own joint, 'drone', with 'drone_wing_L|R' to flap). Built in the wing's flat jet layout,
    stowed with the wing"""
    c0 = CRANE_AT; F, U, R = (0, 1, 0), (0, 0, 1), (1, 0, 0)  # forward = toward the hinge, up = off the wing
    def Q(f, u, r): return add(c0, add(mul(F, f), add(mul(U, u), mul(R, r))))
    C = [hull([Q(-0.16, 0.02, 0), Q(0.16, 0.02, 0), Q(0, 0.13, 0), Q(0, 0.03, 0.075), Q(0, 0.03, -0.075), Q(0, -0.012, 0)], M['paper'], 0.006, name='crane_body')]
    C.append(tri_plate(Q(0.08, 0.03, 0), Q(0.15, 0.02, 0), Q(0.31, 0.24, 0), 0.016, M['paper'], 0.0, name='crane_neck'))
    C.append(tri_plate(Q(0.29, 0.235, 0), Q(0.31, 0.215, 0), Q(0.39, 0.19, 0), 0.02, M['paint'], 0.0, name='crane_head'))
    C.append(tri_plate(Q(-0.08, 0.03, 0), Q(-0.15, 0.02, 0), Q(-0.30, 0.22, 0), 0.016, M['paper'], 0.0, name='crane_tail'))
    W = {'L': [], 'R': []}
    for sd, L in ((-1, 'L'), (1, 'R')):  # (the crane faces +y here, so its right is +x)
        W[L].append(tri_plate(Q(-0.08, 0.07, 0), Q(0.08, 0.07, 0), Q(-0.03, 0.17, sd * 0.35), 0.014, M['paper'], 0.0, name='crane_wing'))
        W[L].append(tri_plate(Q(-0.045, 0.155, sd * 0.29), Q(-0.02, 0.16, sd * 0.29), Q(-0.03, 0.17, sd * 0.35), 0.02, M['paint'], 0.0, name='crane_wingtip'))
    C.append(hull([Q(0.33, 0.215 + dy, dr) for dy in (-0.012, 0.012) for dr in (-0.012, 0.012)] + [Q(0.35, 0.21, 0)], M['thrust'], 0.002, name='crane_eye'))
    C.append(hull([Q(f, u, r) for f in (-0.05, 0.05) for u in (-0.03, 0.005) for r in (-0.03, 0.03)], M['frame'], 0.006, name='crane_dock'))
    Mx = wing_stow(-1)
    for o in C + W['L'] + W['R']: xform(o, Mx)
    mk.add('drone', C); mk.add('drone_wing_L', W['L']); mk.add('drone_wing_R', W['R']); T['drone'] = C + W['L'] + W['R']
    mk.meta['drone_axis'] = [round(v, 5) for v in g_of(Mx.to_3x3() @ gv(0, 1, 0))]  # the crane's nose / its wings' flap axis


def crane_img():
    """a folded-crane emblem (the frame's mark), white on a dark disc"""
    px = canvas(96, 96)
    lib.px_disc(px[:, :, :3], 48, 48, 46, 0x1d2747); yy, xx = np.mgrid[0:96, 0:96]; px[(xx - 48) ** 2 + (yy - 48) ** 2 <= 46 * 46, 3] = 1
    for pts, col in ((((20, 30), (48, 52), (76, 30), (48, 44)), 0xf7f4ec), (((48, 44), (40, 62), (48, 72), (56, 62)), 0xf7f4ec),
                     (((44, 62), (20, 70), (14, 46)), 0xe8e4da), (((52, 62), (78, 66), (84, 50), (88, 54)), 0xe8e4da), (((84, 50), (90, 52), (88, 58)), 0xff4fd8)):
        poly(px, pts, col)
    return image_rgba('pp_crane', px)


def decals(mk, M, T):
    D = []
    nb = tex_mat('pp_notebook', notebook_img(), rough=0.5, cc=0.3)
    st = tex_mat('pp_sticker', sticker_img('pp_howsmy', ["HOW'S MY", 'PILOTING?'], 0xffe14d, 0x111111, 160, 48), 0.4)
    pk = tex_mat('pp_permit', sticker_img('pp_permitimg', ['PERMIT', '0451'], 0xf6f2ea, 0x2a6a3a, 96, 56, 2, 0x2a6a3a), 0.4)
    a4 = tex_mat('pp_a4', stencil_img('pp_a4img', 'A4', 0x16161c), 0.35, clip=True)
    fo = tex_mat('pp_foldmat', fold_img(), 0.4, clip=True)
    hz = tex_mat('pp_hazardmat', hazard_img(), 0.4)
    num = tex_mat('pp_07', stencil_img('pp_07img', '07', 0x16161c, 80, 40, 4), 0.35, clip=True)
    cr = tex_mat('pp_cranemat', crane_img(), 0.35, clip=True)
    mk.add('hatch', decal(T['hatch'], (-0.40, 3.58, -0.55), (-0.42, 0.25, -0.87), (0, 1, 0), 0.20, 0.20, cr, name='crane_mark'))
    for s, L in ((1, 'R'), (-1, 'L')):
        # notebook paper on each wing's underside (the face toward the mech's back = down in jet mode)
        Mx = wing_stow(s); lay = mk.meta['wing_layout'][L]
        R1, R2, Wt, C = (V(gv(*p)) for p in (lay['R1'], lay['R2'], lay['tip'], lay['fold']))
        cen = (R1 + R2 * 1.4 + Wt * 1.3) / 3.7
        cen_g = g_of(Mx @ cen); n_g = g_of((Mx.to_3x3() @ gv(0, 0, -1)).normalized()); up_g = g_of((Mx.to_3x3() @ (R1 - cen)).normalized())
        d = decal(T['wing_' + L], cen_g, n_g, up_g, 0.5, 0.5, nb, name='notebook')
        mk.add('wing_' + L, d)
        # FOLD HERE along the crease, on top
        fc = Mx @ ((R1 + C) / 2); fdir = (Mx.to_3x3() @ (C - R1)).normalized(); nn = (Mx.to_3x3() @ gv(0, 0, 1)).normalized()
        up2 = fdir.cross(nn)
        mk.add('wing_' + L, decal(T['wing_' + L], g_of(fc), g_of(nn), g_of(up2), 1.05, 0.13, fo, name='foldhere'))
        # hazard band on the pod and the backpack hinge side
        mk.add('pod_' + L, decal(T['pod_' + L], (s * 1.19, 4.30, 0.12), (s, 0, 0), (0, 1, 0), 0.26, 0.06, hz, name='podhaz'))
    mk.add('pod_R', decal(T['pod_R'], (0.99, 4.43, 0.10), (0, 1, 0), (0, 0, -1), 0.22, 0.11, a4, name='a4'))
    mk.add('backpack', decal(T['backpack'], (0, 3.46, 0.80), (0, -0.1, 1), (0, 1, 0), 0.30, 0.09, st, name='howsmy'))
    mk.add('shin_R', decal(T['shin_R'], (0.53, 0.86, -0.34), (0, 0, -1), (0, 1, 0), 0.10, 0.06, pk, name='permit'))
    mk.add('thigh_L', decal(T['thigh_L'], (-0.63, 2.10, 0.0), (-1, 0, 0), (0, 1, 0), 0.18, 0.09, num, name='num'))
    mk.add('thigh_R', decal(T['thigh_R'], (0.63, 2.10, 0.0), (1, 0, 0), (0, 1, 0), 0.18, 0.09, num, name='num'))


# ------------------------------------------------------------ poses (three.js XYZ euler per joint, radians; or a matrix)
def pose_ready(mk):
    r = math.radians
    return {
        'hips': (0, r(-8), 0), 'chest': (r(-3), r(10), 0), 'head': (r(-6), r(-10), r(-4)),
        'upperarm_R': (r(-6), 0, r(14)), 'forearm_R': (r(28), r(-20), 0), 'hand_R': (r(-6), 0, r(6)),
        'upperarm_L': (r(14), 0, r(-16)), 'forearm_L': (r(20), r(10), 0), 'hand_L': (r(-10), 0, 0),
        'thigh_R': (r(12), 0, r(8)), 'shin_R': (r(-16), 0, 0), 'foot_R': (r(4), 0, r(-4)),
        'thigh_L': (r(-14), 0, r(-6)), 'shin_L': (r(-8), 0, 0), 'foot_L': (r(18), 0, r(4)),
        'skirt_R': (0, 0, r(6)), 'skirt_L': (0, 0, r(-6)),
    }


def pose_jet(mk):
    """jet mode: pitched forward flat, legs together and pointed, arms tucked, head up to look ahead, the pods
    pointing forward, the wings swung down flat into their jet layout (a paper plane)"""
    r = math.radians
    P = {'root_at': (0, -0.55, 0), 'hips': (r(-90), 0, 0), 'head': (r(78), 0, 0), 'neck': (r(10), 0, 0),
         'pod_R': (r(90), 0, 0), 'pod_L': (r(90), 0, 0)}
    for s, L in ((1, 'R'), (-1, 'L')):
        P['upperarm_' + L] = (r(-4), 0, r(s * 6)); P['forearm_' + L] = (0, 0, 0); P['hand_' + L] = (r(-10), 0, 0)
        P['thigh_' + L] = (0, 0, r(-s * 3)); P['shin_' + L] = (0, 0, 0); P['foot_' + L] = (r(-75), 0, 0); P['toe_' + L] = (r(-10), 0, 0)
        P['skirt_' + L] = (0, 0, r(s * 4))
        h = J('wing', s)
        Rz = Matrix.Rotation(-s * WING_PHI, 4, gv(0, 0, 1)); Ry = Matrix.Rotation(-s * WING_PSI, 4, gv(0, 1, 0))
        dih = Matrix.Rotation(s * math.radians(-8), 4, gv(0, 1, 0))  # a little dihedral (tips up in flight)
        P['wing_' + L] = (dih @ Rz @ Ry).to_3x3()
    return P


POSES = {'ready': pose_ready, 'jet': pose_jet, 'rest': lambda mk: {}}
