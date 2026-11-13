# PAPER PLANE MK2: the anime-mecha restyle (the owner, 2026-11-13: "I want the mechs to be cooler different style from
# base game like gundam"; the rules are in docs/mechs/STYLE.md). Same frame, same joints, markers, clips and spray slots
# as the MK1 file, so the game binds it unchanged; all new armour: pearl-white plates over a gunmetal frame that shows
# at every joint, the team colour on the chest, forearms, knees, calves and feet, one yellow accent, cyan glow lines
# in dark channels, yellow eyes under a sharp visor. The silhouette idea: two big folded delta wings in a high V (a paper
# dart), and a little paper dart for a crest (a keel and two swept wings, not a V-fin). The joke stays, built for real:
# origami folds as crisp creased armour, the homing pencils as hex missile tubes with sharpened warheads, the
# highlighters as twin beam barrels with chisel-cut muzzles, the origami crane drone as a faceted recon bit. The one
# jank detail: a paperclip for an antenna.
#   blender52 -b -P tools/blender/mechs/make_hero.py -- hero=paperplane_mk2 [qa]   -> public/models/x_mech_paperplane.glb
# Game space: the mech faces -z, its right is +x, feet on y = 0.
from mechkit import *
import mechkit as MK
import clips as C
from detailkit import *
from paperplane import JT, J, WING_PHI, WING_PSI, CRANE_AT, wing_stow, pose_ready, pose_jet

FID = 'mech_paperplane'
GLB = 'x_mech_paperplane'  # (make_hero writes this file: it replaces MK1 in the game)
SKIN = True  # (one rigid-skinned mesh per LOD: skin_glb.py)
PHASE = 'mk2 (anime-mecha restyle, docs/mechs/STYLE.md)'
ROLE_LOOK.setdefault('hazard', (0.30, 0.0, 1.0))  # (the yellow accent is paint, not gold)
PAL_A = {  # "SKY MAIL": pearl white, sky blue team colour, navy + gunmetal frame, yellow accent, yellow eyes, cyan lines
    'paint': 0x2fb8ff, 'white': 0xf2f1ec, 'dark': 0x1d2747, 'frame': 0x3a4152, 'hazard': 0xffd23a, 'chrome': 0xd2d9e2,
    'rubber': 0x17171c, 'glass': 0x0c1e30, 'glow': 0xffe14d, 'thrust': 0x4fe8ff,
}
PAL_B = {  # "PINK SLIP": pink team colour on plum, cyan eyes, pink lines
    'paint': 0xff3fcf, 'white': 0xf6f0f2, 'dark': 0x2c1446, 'frame': 0x40384e, 'hazard': 0xffe14d, 'glass': 0x2a1240,
    'glow': 0x4fe8ff, 'thrust': 0xff6ae0,
}
NUMBER = '07'
# the markers exactly where MK1 had them (the game, its clips and its effects bind to these)
MARKS = {
    'mk_drone': ('drone', (-0.4677, 4.4318, 1.1931), (0.9366, -0.1736, -0.3043)),
    'mk_eject': ('chest', (0, 4.15, -0.75), (0.0, 0.7071, -0.7071)), 'mk_mark': ('head', (0, 5.376, -0.03), (0, 1, 0)),
    'mk_seat': ('chest', (0, 3.62, -0.05), (0, 0, -1)),
}
for _s, _L in ((1, 'R'), (-1, 'L')):
    for _i, (_cx, _cy) in enumerate([(cx, cy) for cy in (4.335, 4.21) for cx in (0.87, 1.0, 1.13)]):
        MARKS[f'mk_missile_{_L}{_i}'] = ('pod_' + _L, (_s * _cx, _cy, -0.47), (0, 0, -1))
    MARKS[f'mk_muzzle_{_L}'] = ('forearm_' + _L, (_s * 1.14, 2.40, -0.76), (0, 0, -1))
    MARKS[f'mk_thrust_back_{_L}'] = ('backpack', (_s * 0.22, 3.0168, 0.7391), (0.0, -0.9439, 0.3304))
    MARKS[f'mk_thrust_heel_{_L}'] = ('foot_' + _L, (_s * 0.46, 0.1671, 0.511), (0.0, -0.3304, 0.9439))
DRONE_AXIS = [0.93661, -0.17365, -0.30432]


def hp(x, y, z): return add(JT['head'], (x, y, z))


def P3(pts): return [hp(*p) for p in pts]


# ------------------------------------------------------------ small parts
def gline(a, b, n, M, w=0.024, h=0.010, name='gline', detail=False, glow='thrust'):
    """a glowing edge line on a flat face (normal n) from a to b: a dark channel with a glow strip standing in it
    (every face > 4 mm from its neighbours: the QA gate)"""
    n = norm(n); d = norm(sub(b, a)); u = norm(cross(n, d))
    o = [hull([add(add(p, mul(u, sx * (w / 2 + 0.009))), mul(n, z)) for p in (a, b) for sx in (-1, 1) for z in (-0.016, h)], M['dark'], 0.0, 1, name + '_ch')]
    a2, b2 = add(a, mul(d, 0.009)), add(b, mul(d, -0.009))
    o.append(hull([add(add(p, mul(u, sx * w / 2)), mul(n, z)) for p in (a2, b2) for sx in (-1, 1) for z in (0.005, h + 0.006)], M[glow], 0.0, 1, name))
    return dt(o) if detail else o


# ------------------------------------------------------------ the sticker sheet (one alpha-tested material)
AW, AH = 1024, 512
CELLS = {'num': (0, 0, 256, 128), 'aero': (256, 0, 384, 64), 'aero_w': (256, 64, 384, 64), 'emblem': (640, 0, 128, 128),
         'tri': (768, 0, 128, 128), 'rescue': (896, 0, 128, 128), 'nostep': (0, 128, 256, 64), 'serial': (0, 192, 256, 64),
         'fold': (256, 128, 512, 48), 'works': (256, 176, 512, 48), 'chev': (256, 224, 512, 32), 'eject': (768, 128, 256, 128)}


def sheet():
    px = canvas(AW, AH)
    def cell(k): x, y, w, h = CELLS[k]; return px[y:y + h, x:x + w], w, h
    sub_, w, h = cell('num')  # the unit number: a big stencil, bridges cut through it
    sc = 14; text_c(sub_, NUMBER, w // 2, (h - 7 * sc) // 2, sc, 0xf2f1ec)
    for gx in range(0, w, sc * 6): sub_[:, gx + sc * 2:gx + sc * 2 + 3, 3] = 0
    for k, col in (('aero', 0x1d2747), ('aero_w', 0xf2f1ec)):
        sub_, w, h = cell(k); text_c(sub_, 'JANK AERO', w // 2, (h - 42) // 2, 6, col)
    sub_, w, h = cell('emblem')  # the frame's mark: a white paper dart on a navy disc, a yellow ring
    yy, xx = np.mgrid[0:h, 0:w]; r = ((xx - w / 2) ** 2 + (yy - h / 2) ** 2) ** 0.5
    sub_[r < 62, :3] = hexrgb(0xffd23a); sub_[r < 62, 3] = 1; sub_[r < 54, :3] = hexrgb(0x1d2747)
    poly(sub_, [(22, 70), (106, 40), (64, 64)], 0xf2f1ec); poly(sub_, [(22, 70), (64, 64), (58, 94)], 0xc9ccd6)
    sub_, w, h = cell('tri')
    poly(sub_, [(w / 2, 8), (w - 8, h - 12), (8, h - 12)], 0x111111); poly(sub_, [(w / 2, 24), (w - 22, h - 20), (22, h - 20)], 0xffd23a)
    text_c(sub_, '!', w // 2, 46, 7, 0x111111)
    sub_, w, h = cell('rescue')  # a rescue arrow (pointing up at the hatch)
    poly(sub_, [(64, 6), (118, 60), (88, 60), (88, 122), (40, 122), (40, 60), (10, 60)], 0xff3030)
    poly(sub_, [(64, 20), (102, 54), (80, 54), (80, 114), (48, 114), (48, 54), (26, 54)], 0xffd23a)
    sub_, w, h = cell('nostep'); fill(sub_, 4, 4, w - 4, h - 4, 0xffd23a); border(sub_, 4, 0x111111); text_c(sub_, 'NO STEP', w // 2, 15, 5, 0x111111)
    sub_, w, h = cell('serial'); fill(sub_, 2, 2, w - 2, h - 2, 0x1b1b22); border(sub_, 2, 0x8a8a90)
    text_c(sub_, f'PP-{NUMBER} LOT 404', w // 2, 12, 3, 0xd8d8d8); text_c(sub_, 'PAPERWORKS DIV.', w // 2, 38, 2, 0x8a8a90)
    sub_, w, h = cell('fold')  # FOLD HERE: a dashed line and scissors
    for xx_ in range(70, w - 150, 26): fill(sub_, xx_, 22, xx_ + 14, 27, 0x1d2747)
    lib.px_disc(sub_[:, :, :3], 14, 14, 9, 0x1d2747, r_in=5); lib.px_disc(sub_[:, :, :3], 14, 34, 9, 0x1d2747, r_in=5)
    sub_[2:46, 2:26, 3] = np.maximum(sub_[2:46, 2:26, 3], (np.abs(sub_[2:46, 2:26, :3] - hexrgb(0x1d2747)).sum(-1) < 0.05) * 1.0)
    for t in range(0, 34): sub_[12 + t // 2:15 + t // 2, 22 + t, :3] = hexrgb(0x1d2747); sub_[12 + t // 2:15 + t // 2, 22 + t, 3] = 1; sub_[34 - t // 2:37 - t // 2, 22 + t, :3] = hexrgb(0x1d2747); sub_[34 - t // 2:37 - t // 2, 22 + t, 3] = 1
    text(sub_, 'FOLD HERE', w - 140, 14, 3, 0x1d2747)
    sub_, w, h = cell('works'); text_c(sub_, 'PAPERWORKS MK2', w // 2, 10, 4, 0x1d2747)
    x, y, w, h = CELLS['chev']; stripes(px, x, y + 4, x + w, y + h - 4, 0xffd23a, 0x111111, 14)
    sub_, w, h = cell('eject')  # the eject triangle: red, white text
    poly(sub_, [(w / 2, 6), (w - 10, h - 8), (10, h - 8)], 0xff3030); text_c(sub_, 'EJECT', w // 2, 70, 5, 0xffffff)
    return px


def stamp(targets, cell, c, n, up, w, m, reach=0.3, off=0.0035):
    """one sticker from the sheet cast onto targets at c facing n (w = its width in metres)"""
    x, y, cw, ch = CELLS[cell]
    d = decal(targets, c, n, up, w, w * ch / cw, m, name=f'dc_{cell}', reach=reach, off=off)
    if d is None: print('JF_DECAL_MISS', cell, c); return None
    for l in d.data.uv_layers['UVMap'].data: l.uv = ((x + l.uv[0] * cw) / AW, 1 - (y + (1 - l.uv[1]) * ch) / AH)
    return d


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
    mk.joint('drone', g_of(wing_stow(-1) @ gv(*CRANE_AT)), 'wing_L')
    for L in ('L', 'R'): mk.joint('drone_wing_' + L, g_of(wing_stow(-1) @ gv(*add(CRANE_AT, (0, 0, 0.07)))), 'drone')
    T = {}
    head(mk, M, T); neck(mk, M, T); chest(mk, M, T); hatch(mk, M, T); backpack(mk, M, T); waist(mk, M, T); hips(mk, M, T)
    for s, L in ((1, 'R'), (-1, 'L')):
        shoulder(mk, M, T, s, L); pod(mk, M, T, s, L); upperarm(mk, M, T, s, L); forearm(mk, M, T, s, L); cannon(mk, M, T, s, L)
        hand(mk, M, T, s, L); skirt(mk, M, T, s, L); thigh(mk, M, T, s, L); shin(mk, M, T, s, L); foot(mk, M, T, s, L); toe(mk, M, T, s, L)
        wing(mk, M, T, s, L)
    crane(mk, M, T)
    decals(mk, M, T)
    mk.meta.update({'name': 'PAPER PLANE', 'height': 4.85, 'style': 'mk2', 'drone_axis': DRONE_AXIS,
                    'palettes': {'A': {k: PAL_A[k] for k in ('paint', 'white', 'dark', 'glow', 'thrust')} | {'accent': PAL_A['hazard']},
                                 'B': {k: PAL_B[k] for k in ('paint', 'white', 'dark', 'glow', 'thrust')} | {'accent': PAL_B['hazard']}},
                    'wing_stow': {'phi': WING_PHI, 'psi': WING_PSI}})
    return mk


# ------------------------------------------------------------ head: a tight helmet, a sharp visor, a paper-dart crest
def head(mk, M, T):
    H = [hull(P3([(sx * 0.14, y, z) for sx in (-1, 1) for y in (-0.02, 0.28) for z in (-0.13, 0.16)]), M['frame'], 0.015, name='skull')]
    # the helmet shell: its brow comes down to a point between the eyes (a frown), a ridge down the middle
    top = [(0, 0.428, -0.05), (0, 0.405, 0.17), (0, 0.236, -0.262), (0, 0.22, 0.242)]
    for s in (-1, 1):
        top += [(s * 0.11, 0.262, -0.222), (s * 0.20, 0.288, -0.158), (s * 0.214, 0.33, 0.06), (s * 0.15, 0.41, -0.05), (s * 0.15, 0.395, 0.15), (s * 0.15, 0.20, 0.218), (s * 0.212, 0.27, 0.15)]
    H.append(hull(P3(top), M['white'], 0.012, seg=3, name='helm'))
    for s in (-1, 1):  # side plates over the ears, tucked under the shell (a seam), cheek guards framing the face
        H.append(hull(P3([(s * 0.19, 0.275, -0.12), (s * 0.226, 0.265, -0.05), (s * 0.232, 0.255, 0.15), (s * 0.205, 0.03, 0.155), (s * 0.214, 0.02, -0.02), (s * 0.175, 0.06, -0.12),
                          (s * 0.14, 0.26, -0.10), (s * 0.14, 0.03, -0.08), (s * 0.14, 0.25, 0.15), (s * 0.14, 0.03, 0.15)]), M['white'], 0.01, seg=3, name='helm_side'))
        H.append(hull(P3([(s * 0.125, 0.165, -0.19), (s * 0.20, 0.17, -0.115), (s * 0.198, 0.03, -0.075), (s * 0.115, 0.03, -0.165), (s * 0.12, 0.165, -0.12), (s * 0.12, 0.03, -0.11), (s * 0.17, 0.10, -0.165)]),
                      M['white'], 0.006, name='cheek'))
    # the visor: a dark glass V under the brow; two sharp eyes on it (outer ends up, following the brow)
    vis = [(0, 0.228, -0.252), (0, 0.168, -0.236), (0, 0.228, -0.12), (0, 0.168, -0.12)]
    for s in (-1, 1): vis += [(s * 0.17, 0.272, -0.163), (s * 0.176, 0.208, -0.148), (s * 0.15, 0.27, -0.09), (s * 0.15, 0.20, -0.09)]
    H.append(hull(P3(vis), M['glass'], 0.004, name='visor'))
    for s in (-1, 1):
        A, B, Cc, D = (0, 0.228, -0.252), (s * 0.17, 0.272, -0.163), (s * 0.176, 0.208, -0.148), (0, 0.168, -0.236)
        n = norm(cross(sub(B, A), sub(D, A)))
        if n[2] > 0: n = mul(n, -1)
        def Pv(u, v): return lerp(lerp(A, B, u), lerp(D, Cc, u), v)
        eye = [Pv(0.16, 0.30), Pv(0.86, 0.16), Pv(0.80, 0.36), Pv(0.20, 0.62)]
        H.append(hull(P3([add(p, mul(n, k)) for p in eye for k in (-0.007, 0.0065)]), M['glow'], 0.0, 1, name='eye'))
    # the face: a dark mouth plate with two slats, a pointed team-colour chin
    H.append(hull(P3([(0, 0.172, -0.226), (0, 0.03, -0.20)] + [(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.125, 0.18, -0.15), (0.105, 0.04, -0.14), (0.125, 0.18, -0.06), (0.105, 0.03, -0.06))]),
                  M['frame'], 0.006, name='mouth'))
    H += dt([hull(P3([(sx * 0.05, y + dy, -0.226 + 0.033 * abs(sx) + 0.012 * (0.17 - y)) for sx in (-1, 1) for dy in (0, 0.011)] + [(sx * 0.05, y + dy, -0.19) for sx in (-1, 1) for dy in (0, 0.011)]), M['dark'], 0.0, 1, 'slat') for y in (0.135, 0.112)])
    H.append(hull(P3([(0, 0.075, -0.232), (0, -0.012, -0.20), (0, 0.06, -0.13)] + [(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.06, 0.072, -0.19), (0.04, 0.008, -0.17), (0.06, 0.06, -0.12))]),
                  M['paint'], 0.006, name='chin'))
    # the crest: a little paper dart lying on the helmet (a white keel, two swept team-colour wings, a yellow nose)
    H.append(hull(P3([(sx * 0.014, y, z) for sx in (-1, 1) for (y, z) in ((0.232, -0.268), (0.282, -0.375), (0.43, -0.05), (0.44, 0.06), (0.30, -0.20))]), M['white'], 0.005, name='crest_keel'))
    for s in (-1, 1):
        a, b, c = (s * 0.012, 0.30, -0.33), (s * 0.012, 0.442, 0.05), (s * 0.12, 0.462, 0.12)
        nn = norm(cross(sub(b, a), sub(c, a)))
        if nn[1] < 0: nn = mul(nn, -1)
        H.append(hull(P3([add(p, mul(nn, k)) for p in (a, b, c) for k in (0.0, 0.02)]), M['paint'], 0.005, name='crest_wing'))
    H.append(hull(P3([(0, 0.27, -0.40), (0.02, 0.286, -0.35), (-0.02, 0.286, -0.35), (0, 0.31, -0.35), (0, 0.265, -0.35)]), M['hazard'], 0.003, name='crest_nose'))
    for s in (-1, 1):  # side sensors: gunmetal pods, a glowing lens
        c = hp(s * 0.25, 0.15, 0.03)
        H.append(frustum(add(c, (s * -0.03, 0, 0)), add(c, (s * 0.045, 0, 0)), 0.075, 0.062, M['frame'], 6, bev=0.006, ref=(0, 1, 0), name='ear'))
        H.append(cyl(add(c, (s * 0.03, 0.0, -0.05)), add(c, (s * 0.03, 0.0, -0.085)), 0.02, M['thrust'], 10, bev=0.0, name='ear_lens'))
    H += louvres(hp(0, 0.19, 0.248), norm((0, 0.15, 1)), (0, 1, 0), 0.16, 0.12, 3, M, 0.02, bar=0.018, name='helm_vent')
    # the jank detail: a paperclip for an antenna, clipped onto the left sensor
    a0 = hp(-0.275, 0.20, 0.05); up = norm((-0.22, 1, 0.5)); side_ = norm(cross(up, (1, 0, 0)))
    def Q(v, u): return add(a0, add(mul(side_, v), mul(up, u)))
    clip = []
    def arc(cv, cu, r, a1, a2, n=6):
        for i in range(n + 1):
            t = math.radians(a1 + (a2 - a1) * i / n); clip.append(Q(cv + r * math.cos(t), cu + r * math.sin(t)))
    clip.append(Q(0.015, 0.0)); clip.append(Q(0.015, 0.27)); arc(0, 0.27, 0.015, 0, 180)
    clip.append(Q(-0.015, 0.04)); arc(0.007, 0.04, 0.022, 180, 360); clip.append(Q(0.029, 0.30)); arc(0.0, 0.30, 0.029, 0, 180)
    clip.append(Q(-0.029, 0.12))
    H.append(tube(clip, 0.0075, M['chrome'], 6, 'paperclip'))
    mk.add('head', H); T['head'] = H


def neck(mk, M, T):
    N = [frustum((0, 4.00, 0.0), (0, 4.30, -0.03), 0.115, 0.10, M['frame'], 8, name='neckcol')]
    N += dt([cyl((0, y - 0.018, -0.01), (0, y + 0.018, -0.01), 0.13, M['dark'], 12, bev=0.004, name='neck_ring') for y in (4.10, 4.18)])
    for s in (-1, 1): N += hose([(s * 0.10, 4.06, 0.10), (s * 0.15, 4.16, 0.12), (s * 0.12, 4.27, 0.05)], 0.022, M)
    mk.add('neck', N)


# ------------------------------------------------------------ torso
def zp(x): return -0.445 + 0.33 * (abs(x) - 0.30)  # the chest plates' face (z at |x|)
def pec_pt(x, y, k=0.0): return add((x, y, zp(x)), mul(norm((math.copysign(0.33, x), 0, -1)), k))


def pec_of(s):
    """a chest plate (team colour), folded across the middle: its outline and fold, game points"""
    o = [(0.27, 4.045), (0.72, 4.005), (0.80, 3.78), (0.58, 3.43), (0.30, 3.49)]
    return [pec_pt(s * x, y) for (x, y) in o]


def chest(mk, M, T):
    C = [hull([(sx * x, y, z) for sx in (-1, 1) for (x, y) in ((0.34, 3.22), (0.56, 3.99)) for z in (-0.30, 0.40)], M['frame'], 0.025, name='core')]
    for s in (-1, 1):
        n = norm((s * 0.33, 0, -1)); o = pec_of(s)
        fold = [pec_pt(s * x, 3.80, 0.055) for x in (0.31, 0.74)]  # (the fold stands 55 mm proud)
        C.append(hull(o + fold + [add(p, mul(n, -0.13)) for p in o], M['paint'], 0.014, seg=3, name='pec'))
        C += gline(pec_pt(s * 0.36, 3.80, 0.05), pec_pt(s * 0.69, 3.80, 0.05), n, M, w=0.016, name='pec_line')  # (the fold glows)
        C += bolts([pec_pt(s * x, y, 0.004) for (x, y) in ((0.34, 3.99), (0.68, 3.96), (0.58, 3.50), (0.34, 3.53))], n, M['frame'], 0.016, 0.012)
        yk = [(s * 0.20, 4.16, -0.27), (s * 0.50, 4.13, -0.33), (s * 0.72, 4.06, -0.29), (s * 0.77, 4.04, 0.34), (s * 0.20, 4.17, 0.37)]
        if s < 0: yk = yk[::-1]
        C.append(plate(yk, 0.11, (s * 0.12, 1, 0), M['white'], 0.014, 3, name='yoke'))
        C.append(hull([(s * x, y, z) for (x, y) in ((0.58, 3.40), (0.60, 3.98), (0.78, 3.98), (0.70, 3.40)) for z in (-0.22, 0.36)] + [(s * 0.795, 3.70, 0.07)], M['white'], 0.02, name='flank'))
        C += louvres((s * 0.79, 3.60, 0.07), (s, 0, 0), (0, 1, 0), 0.34, 0.26, 4, M, 0.03, name='flank_vent')
        C.append(hull([(s * 0.40, 3.33, -0.30), (s * 0.10, 3.26, -0.40), (s * 0.38, 3.30, 0.30), (s * 0.10, 3.22, 0.34), (s * 0.36, 3.46, 0.0), (s * 0.10, 3.46, -0.3)], M['dark'], 0.015, name='rib'))
    C.append(hull([(sx * 0.21, y, z) for sx in (-1, 1) for (y, z) in ((4.10, 0.10), (4.12, 0.34), (4.36, 0.16), (4.32, 0.30))], M['white'], 0.014, name='collar'))
    C.append(hull([(sx * x, y, z) for sx in (-1, 1) for (x, y) in ((0.40, 3.30), (0.54, 4.04)) for z in (0.30, 0.46)], M['white'], 0.02, name='backplate'))
    C += dt([lbox((0, 3.70, -0.30), fr((0, 0, -1)), 0.30, 0.40, 0.0, 0.035, M['dark'], 0.008, 'seat'), lbox((0, 3.96, -0.30), fr((0, 0, -1)), 0.16, 0.08, 0.0, 0.05, M['dark'], 0.008, 'headrest'),
             lbox((0, 3.44, -0.30), fr((0, 0, -1)), 0.30, 0.05, 0.0, 0.02, M['glow'], 0.0, 'console')])
    mk.add('chest', C); T['chest'] = C


def hatch(mk, M, T):
    """the cockpit hatch: the paper plane's nose seen from above, a creased breastplate pointing down the middle of the
    chest (it lifts at its top edge)"""
    pts = [(0, 4.06, -0.50), (0, 3.41, -0.585), (0, 4.06, -0.30), (0, 3.44, -0.36)]
    for s in (-1, 1): pts += [(s * 0.31, 4.05, -0.405), (s * 0.30, 4.05, -0.30), (s * 0.12, 3.62, -0.47), (s * 0.12, 3.62, -0.34)]
    Hc = [hull(pts, M['white'], 0.014, seg=3, name='breastplate')]
    bv = bvh_of(Hc); fwd = (0, 0, 1)
    Hc.append(MK.skin(bv, [(0.026, 4.00, -1), (-0.026, 4.00, -1), (0.026, 3.56, -1), (-0.026, 3.56, -1), (0, 3.50, -1)], fwd, 0.008, 0.02, M['paint'], 0.003, 'keel'))
    for s in (-1, 1):
        Hc.append(MK.skin(bv, [(s * 0.07, 3.99, -1), (s * 0.26, 3.985, -1), (s * 0.22, 3.92, -1), (s * 0.07, 3.92, -1)], fwd, 0.007, 0.02, M['dark'], 0.003, 'hatch_vent'))
        Hc += dt([MK.skin(bv, [(s * 0.09, 3.97, -1), (s * 0.23, 3.966, -1), (s * 0.21, 3.94, -1), (s * 0.09, 3.94, -1)], fwd, 0.014, 0.02, M['thrust'], 0.0, 'hatch_glow')])
    Hc += knuckles((-0.26, 4.06, -0.33), (0.26, 4.06, -0.33), 0.032, M['frame'], 5, 0)
    mk.add('hatch', Hc); T['hatch'] = Hc


def backpack(mk, M, T):
    B = [hull([(0, 3.72, 0.86)] + [(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.40, 3.20, 0.40), (0.44, 4.04, 0.40), (0.32, 4.08, 0.74), (0.26, 3.28, 0.76))],
              M['white'], 0.022, seg=3, name='pack')]
    sp = [(s * 0.12, y, z) for s in (-1, 1) for (y, z) in ((3.30, 0.76), (3.98, 0.73), (3.30, 0.86), (3.98, 0.84))]
    B.append(hull(sp, M['dark'], 0.01, name='spine'))
    B += gline((0, 3.40, 0.86 - 0.10 * 0.0294 + 0.0), (0, 3.90, 0.86 - 0.60 * 0.0294), (0, 0.0294, 1), M, w=0.03, name='spine_line')
    for s in (-1, 1):
        c = (s * 0.22, 3.30, 0.64); ax = norm((0, -1, 0.35))
        B += nozzle(c, ax, 0.15, 0.30, M, 'main')
        B += ribs(add(c, mul(ax, 0.05)), ax, 0.135, 0.15, 3, 0.20, M['frame'])
        B.append(hull([add(c, add(mul(basis(ax)[1], sx * 0.17), add(mul(basis(ax)[2], sy * 0.17), mul(ax, d)))) for sx in (-1, 1) for sy in (-1, 1) for d in (-0.10, -0.012)], M['frame'], 0.012, name='nozzle_mount'))
        B.append(cyl((s * 0.30, 4.02, 0.66), (s * 0.30, 4.02, 0.90), 0.10, M['frame'], 16, name='hinge'))
        B.append(cyl((s * 0.30, 4.02, 0.885), (s * 0.30, 4.02, 0.935), 0.065, M['hazard'], 16, name='hinge_cap'))
        B += dt(nozzle((s * 0.34, 4.06, 0.66), norm((s * 0.3, 1, 0.5)), 0.05, 0.09, M, 'vernier'))
        B += louvres((s * 0.443, 3.60, 0.58), norm((s, 0, 0.2)), (0, 1, 0), 0.22, 0.40, 5, M, 0.025, name='pack_vent')
        B += hose([(s * 0.36, 3.30, 0.70), (s * 0.44, 3.62, 0.76), (s * 0.40, 3.92, 0.80), (s * 0.31, 4.00, 0.82)], 0.024, M)
    mk.add('backpack', B); T['backpack'] = B


def waist(mk, M, T):
    W = [cyl((0, 2.78, 0.04), (0, 3.30, 0.04), 0.20, M['frame'], 12, name='spine')]
    for y in (2.92, 3.06, 3.20): W.append(cyl((0, y - 0.03, 0.04), (0, y + 0.03, 0.04), 0.24, M['dark'], 12, name='disc'))
    for s in (-1, 1):
        W.append(hull([(s * x, y, z) for x in (0.18, 0.36) for y in (2.86, 3.26) for z in (-0.22, 0.26)], M['dark'], 0.02, name='oblique'))
        W += dt([cyl((s * 0.30, 2.80, -0.10), (s * 0.34, 3.08, -0.14), 0.05, M['frame'], 10, name='sleeve'), cyl((s * 0.34, 3.02, -0.14), (s * 0.37, 3.36, -0.17), 0.03, M['chrome'], 10, name='rod')])
        for (y0, y1, w, z) in ((2.86, 3.03, 0.22, -0.33), (3.05, 3.24, 0.26, -0.35)):  # the abs: four folded plates
            W.append(hull([(s * 0.018, y0, z - 0.05), (s * 0.018, y1, z - 0.07), (s * 0.018, y0, z + 0.12), (s * 0.018, y1, z + 0.12)] + [(s * w, y, z) for y in (y0, y1)] + [(s * w * 0.8, y, z + 0.18) for y in (y0, y1)],
                          M['white'], 0.012, name='ab'))
    mk.add('waist', W); T['waist'] = W


def hips(mk, M, T):
    P = [hull([(sx * x, y, z) for sx in (-1, 1) for (x, y) in ((0.30, 2.40), (0.42, 2.84)) for z in (-0.28, 0.30)], M['frame'], 0.025, name='pelvis')]
    cp = [(0, 2.30, -0.42), (0, 2.80, -0.44), (0, 2.32, -0.26), (0, 2.82, -0.26)] + [(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.19, 2.80, -0.38), (0.13, 2.56, -0.38), (0.19, 2.82, -0.24), (0.11, 2.50, -0.26))]
    P.append(hull(cp, M['white'], 0.014, seg=3, name='codpiece'))
    P.append(hull([(sx * 0.21, y, z) for sx in (-1, 1) for (y, z) in ((2.80, -0.46), (2.92, -0.44), (2.80, -0.28), (2.92, -0.28))], M['frame'], 0.012, name='buckle'))
    bv = bvh_of(P[-2:-1])
    P.append(MK.skin(bv, [(0.022, 2.76, -1), (-0.022, 2.76, -1), (0.022, 2.45, -1), (-0.022, 2.45, -1), (0, 2.40, -1)], (0, 0, 1), 0.007, 0.02, M['paint'], 0.003, 'cod_keel'))
    P.append(hull([(s * x, y, z) for s in (-1, 1) for (x, y, z) in ((0.32, 2.86, 0.28), (0.26, 2.40, 0.36), (0.32, 2.86, 0.44), (0.24, 2.44, 0.46))], M['white'], 0.015, name='rear'))
    mk.add('hips', P); T['hips'] = P


def skirt(mk, M, T, s, L):
    n = (s * 0.944, 0.329, 0)
    o_ = [(s * 0.47, 2.92, -0.30), (s * 0.49, 2.92, 0.28), (s * 0.72, 2.28, 0.26), (s * 0.70, 2.22, -0.34)]  # top front, top back, bottom back, bottom front
    fl = lambda pts: pts if s > 0 else pts[::-1]  # (outlines wind outward on both sides)
    mid = lambda u: lerp(lerp(o_[0], o_[1], 0.5), lerp(o_[3], o_[2], 0.5), u)
    cz = 0.03  # (a crease down the middle: the plate folds out)
    cen = mul(tuple(sum(p[i] for p in o_) for i in range(3)), 0.25)
    S = [hull(o_ + [add(mid(-0.02), mul(n, cz)), add(mid(1.02), mul(n, cz))] + [add(lerp(cen, p, 0.85), mul(n, -0.07)) for p in o_], M['white'], 0.014, 3, name='skirt')]
    up_ = [lerp(o_[0], o_[3], -0.02), lerp(o_[1], o_[2], -0.02), lerp(o_[1], o_[2], 0.42), lerp(o_[0], o_[3], 0.42)]
    S.append(plate(fl([add(p, mul(n, 0.035)) for p in up_]), 0.05, n, M['white'], 0.012, 3, name='skirt_top'))
    band = [(s * 0.715, 2.30, 0.28), (s * 0.695, 2.25, -0.36), (s * 0.73, 2.16, -0.37), (s * 0.75, 2.22, 0.29)]
    S.append(hull(band + [add(p, mul(n, -0.07)) for p in band], M['paint'], 0.008, name='skirt_edge'))
    S += gline(add(mid(0.50), mul(n, cz)), add(mid(0.86), mul(n, cz)), n, M, w=0.018, name='skirt_line')
    S.append(cyl((s * 0.40, 2.84, 0.0), (s * 0.55, 2.84, 0.0), 0.07, M['frame'], 12, name='skirt_pin'))
    S += bolts([add(lerp(lerp(o_[0], o_[3], t), lerp(o_[1], o_[2], t), u), mul(n, cz * 0.24)) for t in (0.52, 0.88) for u in (0.12, 0.88)], n, M['frame'], 0.015, 0.012)
    mk.add('skirt_' + L, S); T['skirt_' + L] = S


# ------------------------------------------------------------ legs: long, layered, big feet
def thigh(mk, M, T, s, L):
    x = lambda v: s * v
    TH = [ball(J('thigh', s), 0.17, M['frame'], name='hipball'), frustum((x(0.40), 2.50, 0.0), (x(0.44), 1.62, -0.04), 0.17, 0.15, M['frame'], 8, name='femur')]
    fr_ = [(x(0.41), 2.42, -0.31), (x(0.42), 2.12, -0.34), (x(0.43), 1.80, -0.275)]  # the front: one plate creased down the middle
    for (y, w0, w1, z) in ((2.42, 0.20, 0.21, -0.20), (2.12, 0.19, 0.19, -0.22), (1.80, 0.16, 0.16, -0.18)):
        fr_ += [(x(0.41 - w0), y, z), (x(0.41 + w1), y, z + 0.01), (x(0.41 - w0 + 0.02), y, 0.0), (x(0.41 + w1 - 0.01), y, 0.0)]
    TH.append(hull(fr_, M['white'], 0.016, seg=3, name='thighplate'))
    side_ = [(x(0.625), 2.36, -0.17), (x(0.625), 2.36, 0.15), (x(0.60), 1.86, 0.11), (x(0.60), 1.86, -0.13)]
    if s < 0: side_ = side_[::-1]
    TH.append(plate(side_, 0.07, (s, 0.05, 0), M['paint'], 0.012, 3, name='thighside'))
    TH += gline((x(0.624), 2.28, -0.01), (x(0.605), 1.94, -0.01), (s, 0.05, 0), M, name='thigh_line')
    TH += ram((x(0.42), 2.32, 0.14), (x(0.44), 1.72, 0.13), 0.045, M)
    mk.add('thigh_' + L, TH); T['thigh_' + L] = TH


def shin(mk, M, T, s, L):
    x = lambda v: s * v
    SH = [cyl((x(0.27), 1.52, -0.06), (x(0.61), 1.52, -0.06), 0.13, M['frame'], 16, name='knee'),
          cyl((x(0.25), 1.52, -0.06), (x(0.63), 1.52, -0.06), 0.07, M['hazard'], 12, name='knee_pin')]
    SH += bolt_ring((x(0.61), 1.52, -0.06), (s, 0, 0), 0.10, 6, M['chrome'], 0.013, 0.01, a0=0.5, up=(0, 1, 0))
    SH.append(hull([(x(0.44), 1.90, -0.27), (x(0.44), 1.40, -0.46), (x(0.44), 1.44, -0.17)] + [(x(a), y, z) for a in (0.27, 0.61) for (y, z) in ((1.72, -0.21), (1.40, -0.27), (1.72, -0.10))],
                   M['paint'], 0.014, seg=3, name='kneecap'))
    SH.append(frustum((x(0.44), 1.45, -0.04), (x(0.45), 0.62, 0.04), 0.12, 0.11, M['frame'], 8, name='tibia'))
    # two creased shin plates, the upper one lapping over the lower (layered), flaring out toward the ankle
    for (rows, nm) in ((((1.38, 0.13, -0.30, -0.21), (0.96, 0.185, -0.415, -0.28)), 'shin_hi'), (((1.02, 0.17, -0.385, -0.26), (0.64, 0.225, -0.45, -0.31)), 'shin_lo')):
        pts = []
        for (y, w, kz, ez) in rows: pts += [(x(0.44), y, kz), (x(0.44 - w), y, ez), (x(0.44 + w), y, ez), (x(0.44 - w + 0.03), y, 0.02), (x(0.44 + w - 0.03), y, 0.02)]
        SH.append(hull(pts, M['white'], 0.016, seg=3, name=nm))
    sb = bvh_of(SH[-1:])
    for sd in (-1, 1):  # a team-colour chevron on the lower plate's fold
        SH.append(MK.skin(sb, [(x(0.44), 0.90, 0), (x(0.44 + sd * 0.17), 0.77, 0), (x(0.44 + sd * 0.17), 0.69, 0), (x(0.44), 0.82, 0)], (0, 0, 1), 0.0075 + 0.004 * (sd > 0), 0.02, M['paint'], 0.003, 'shinchev'))
    calf = [(x(a), y, z) for (a, y, z) in ((0.28, 1.36, -0.02), (0.60, 1.36, -0.02), (0.29, 1.28, 0.22), (0.59, 1.28, 0.22), (0.26, 0.84, 0.31), (0.62, 0.84, 0.31),
                                            (0.25, 0.66, 0.02), (0.63, 0.66, 0.02), (0.44, 1.05, 0.355))]
    SH.append(hull(calf, M['paint'], 0.016, seg=3, name='calf'))
    SH.append(hull([(x(a), y, z) for a in (0.37, 0.51) for (y, z) in ((1.20, 0.30), (0.88, 0.345), (1.20, 0.25), (0.88, 0.29))], M['dark'], 0.008, name='calfvent'))
    SH.append(hull([(x(a), y, z) for a in (0.40, 0.48) for (y, z) in ((1.16, 0.31), (0.92, 0.353), (1.16, 0.28), (0.92, 0.32))], M['thrust'], 0.004, name='calfglow'))
    SH += dt([hull([(x(a), y + dy, z + dz) for a in (0.375, 0.505) for (dy, dz) in ((0, 0.0), (0.012, -0.002))] + [(x(a), y + dy, z - 0.03) for a in (0.375, 0.505) for dy in (0, 0.012)], M['frame'], 0.0, 1, 'calfslat')
              for (y, z) in ((1.10, 0.322), (1.04, 0.328), (0.98, 0.334))])
    SH.append(tri_plate((x(0.625), 1.02, 0.06), (x(0.635), 0.70, 0.10), (x(0.71), 0.80, 0.36), 0.03, M['white'], 0.006, name='calf_fin'))
    SH += ram((x(0.44), 1.38, 0.08), (x(0.45), 0.78, 0.12), 0.04, M)
    mk.add('shin_' + L, SH); T['shin_' + L] = SH


def foot(mk, M, T, s, L):
    x = lambda v: s * v
    F = [ball(J('foot', s), 0.13, M['frame'], name='ankle')]
    F.append(hull([(x(a), y, z) for (a, y, z) in ((0.30, 0.04, 0.36), (0.62, 0.04, 0.36), (0.33, 0.34, 0.32), (0.59, 0.34, 0.32), (0.35, 0.44, 0.02), (0.57, 0.44, 0.02),
                   (0.28, 0.04, -0.41), (0.64, 0.04, -0.41), (0.32, 0.26, -0.40), (0.60, 0.26, -0.40))], M['paint'], 0.018, seg=3, name='foot'))
    ins = [(x(0.36), 0.40, -0.06), (x(0.56), 0.40, -0.06), (x(0.585), 0.285, -0.36), (x(0.335), 0.285, -0.36)]
    if s < 0: ins = ins[::-1]
    F.append(plate(ins, 0.06, (0, 0.94, -0.34), M['white'], 0.01, 2, name='instep'))
    F.append(hull([(x(a), y, z) for (a, y, z) in ((0.27, 0.0, 0.37), (0.65, 0.0, 0.37), (0.27, 0.0, -0.41), (0.65, 0.0, -0.41), (0.28, 0.06, 0.37), (0.64, 0.06, 0.37), (0.28, 0.06, -0.41), (0.64, 0.06, -0.41))],
                  M['rubber'], 0.008, name='sole'))
    for sx in (0.29, 0.63):  # ankle guards (white), a seam of frame between them and the foot
        o = s * (1 if sx > 0.46 else -1)
        ag = [(x(sx), 0.64, -0.12), (x(sx), 0.64, 0.20), (x(sx), 0.34, 0.25), (x(sx), 0.30, -0.15)]
        if o < 0: ag = ag[::-1]
        F.append(plate(ag, 0.06, (o, 0, 0), M['white'], 0.012, 2, name='ankleguard'))
        F += bolts([(x(sx) + o * 0.003, 0.56, 0.12), (x(sx) + o * 0.003, 0.40, -0.06)], (o, 0, 0), M['frame'], 0.015, 0.01)
    F += nozzle((x(0.46), 0.22, 0.36), (0, -0.35, 1), 0.10, 0.16, M, 'heel')
    F.append(hull([(x(a), y, z) for a in (0.34, 0.58) for (y, z) in ((0.36, 0.26), (0.40, 0.42), (0.30, 0.40))], M['white'], 0.012, name='heel_guard'))
    mk.add('foot_' + L, F); T['foot_' + L] = F


def toe(mk, M, T, s, L):
    x = lambda v: s * v
    TO = [hull([(x(a), y, z) for (a, y, z) in ((0.29, 0.03, -0.37), (0.63, 0.03, -0.37), (0.32, 0.25, -0.37), (0.60, 0.25, -0.37), (0.46, 0.03, -0.82), (0.46, 0.10, -0.82), (0.38, 0.19, -0.62), (0.54, 0.19, -0.62), (0.46, 0.22, -0.58))],
               M['white'], 0.015, seg=3, name='toe')]
    TO.append(hull([(x(a), y, z) for (a, y, z) in ((0.285, 0.0, -0.37), (0.635, 0.0, -0.37), (0.46, 0.0, -0.83), (0.29, 0.05, -0.37), (0.63, 0.05, -0.37), (0.46, 0.05, -0.82))], M['rubber'], 0.006, name='toesole'))
    TO.append(cyl((x(0.30), 0.13, -0.40), (x(0.62), 0.13, -0.40), 0.06, M['frame'], 12, name='toepin'))
    mk.add('toe_' + L, TO); T['toe_' + L] = TO


# ------------------------------------------------------------ shoulders, pods, arms, hands, cannons
def ytop(x): return 4.15 - 0.19 * (abs(x) - 0.68)  # the pauldron's top face


def shoulder(mk, M, T, s, L):
    x = lambda v: s * v
    SH = [hull([(x(a), y, z) for a in (0.50, 0.86) for y in (3.765, 4.02) for z in (-0.10, 0.26)], M['frame'], 0.02, name='clavicle')]
    nt = norm((s * 0.19, 1, 0))
    top = [(x(a), ytop(a), z) for (a, z) in ((0.68, -0.30), (1.06, -0.36), (1.32, -0.28), (1.34, 0.36), (0.70, 0.40))]
    if s < 0: top = top[::-1]
    SH.append(plate(top, 0.08, nt, M['white'], 0.016, 3, name='pauldron'))
    nw = norm((s * 0.984, 0.183, 0))
    wall = [(x(1.32), 4.05, -0.30), (x(1.32), 4.05, 0.36), (x(1.385), 3.70, 0.31), (x(1.385), 3.70, -0.25)]
    if s < 0: wall = wall[::-1]
    wc = lambda yy, zz: (x(1.32 + (4.05 - yy) / 0.35 * 0.065), yy, zz)  # (on the wall's face)
    cw = 0.04; crease = [add(wc(3.88, z), mul(nw, cw)) for z in (-0.285, 0.345)]  # (the wall folds out across the middle)
    wcen = mul(tuple(sum(p[i] for p in wall) for i in range(3)), 0.25)
    SH.append(hull(wall + crease + [add(lerp(wcen, p, 0.85), mul(nw, -0.07)) for p in wall], M['white'], 0.014, 3, name='pauldron_wall'))
    band = [(x(1.397), 3.72, -0.25), (x(1.397), 3.72, 0.31), (x(1.425), 3.57, 0.30), (x(1.425), 3.57, -0.24)]
    if s < 0: band = band[::-1]
    SH.append(plate(band, 0.07, nw, M['paint'], 0.01, 2, name='pauldron_band'))
    SH += gline(add(wc(3.88, -0.20), mul(nw, cw)), add(wc(3.88, 0.27), mul(nw, cw)), nw, M, w=0.018, name='pauldron_line')
    SH += bolts([add((x(a), ytop(a), z), mul(nt, 0.0)) for (a, z) in ((0.76, -0.26), (1.26, -0.26), (1.28, 0.32), (0.78, 0.35))], nt, M['frame'], 0.016, 0.012)
    fp = [(x(0.70), 4.16, -0.29), (x(1.33), 4.06, -0.27), (x(1.40), 3.96, -0.34), (x(1.36), 3.86, -0.30), (x(0.86), 3.98, -0.39)]
    SH.append(hull(fp + [add(p, (0, 0.0, 0.10)) for p in fp], M['white'], 0.012, seg=3, name='pauldron_front'))
    SH.append(hull([(x(a), y, z) for a in (0.86, 1.12) for y in (4.06, 4.155) for z in (-0.10, 0.30)], M['frame'], 0.012, name='pod_mount'))
    SH += ram((x(0.70), 3.84, 0.30), (x(1.18), 3.98, 0.32), 0.03, M)
    mk.add('shoulder_' + L, SH); T['shoulder_' + L] = SH


def pod(mk, M, T, s, L):
    """the missile pod: a gunmetal launcher of six hex tubes (warheads sharpened like pencils) under a white hooded shell,
    team-colour armour on its outer side"""
    x = lambda v: s * v
    PD = [hull([(x(a), y, z) for a in (0.81, 1.19) for (y, z) in ((4.13, -0.40), (4.42, -0.40), (4.42, 0.36), (4.13, 0.38))], M['frame'], 0.012, name='pod')]
    PD.append(hull([(x(a), y, z) for a in (0.812, 1.188) for y in (4.142, 4.40) for z in (-0.452, -0.39)], M['dark'], 0.008, name='pod_face'))
    # the hood: a white shell over the top, its front edge raked forward past the tubes (they stay at z -0.47)
    hood = [(x(a), y, z) for a in (0.795, 1.205) for (y, z) in ((4.405, -0.53), (4.47, -0.52), (4.495, -0.20), (4.48, 0.30), (4.415, 0.34), (4.405, -0.20))]
    hood += [(x(1.0), 4.505, -0.535), (x(1.0), 4.53, -0.20), (x(1.0), 4.515, 0.30)]  # (a ridge down the middle: a folded roof)
    PD.append(hull(hood, M['white'], 0.012, seg=3, name='pod_hood'))
    for sd in (-1, 1):  # the hood's cheeks come down the sides, cut on a rake
        xx = 0.80 if sd < 0 else 1.20; o = 0.02 if sd > 0 else -0.02
        ch = [(x(xx + o * 0.5), y, z) for (y, z) in ((4.42, -0.52), (4.42, 0.30), (4.20, 0.34), (4.13, 0.20), (4.13, -0.32), (4.30, -0.50))]
        PD.append(hull(ch + [(x(xx - o * 0.6), y, z) for (_, y, z) in ch], M['paint'] if sd > 0 else M['white'], 0.01, name='pod_cheek'))
    for i, (cx, cy) in enumerate([(cx, cy) for cy in (4.335, 4.21) for cx in (0.87, 1.0, 1.13)]):
        c = (x(cx), cy, 0.0)
        PD.append(frustum(add(c, (0, 0, -0.43)), add(c, (0, 0, -0.47)), 0.054, 0.054, M['frame'], 6, bev=0.004, ref=(0, 1, 0), rot=0, name='tube'))
        PD.append(frustum(add(c, (0, 0, -0.40)), add(c, (0, 0, -0.44)), 0.040, 0.040, M['white'], 6, bev=0.0, ref=(0, 1, 0), rot=0, name='missile'))
        PD += dt([lathe_ax([(0.040, 0.0), (0.010, 0.026)], add(c, (0, 0, -0.438)), (0, 0, -1), M['hazard'], 6, 'warhead'),
                  lathe_ax([(0.0105, 0.0), (0.0, 0.009)], add(c, (0, 0, -0.4635)), (0, 0, -1), M['dark'], 6, 'warhead_tip')])
    PD += gline((x(1.222), 4.33, -0.22), (x(1.222), 4.33, 0.22), (s, 0, 0), M, name='pod_line')
    PD += louvres((x(1.0), 4.27, 0.382), norm((0, 0.0, 1)), (0, 1, 0), 0.30, 0.20, 4, M, 0.025, name='pod_vent')
    PD.append(cyl((x(0.84), 4.24, 0.12), (x(1.14), 4.24, 0.12), 0.06, M['frame'], 12, name='pod_pivot'))
    mk.add('pod_' + L, PD); T['pod_' + L] = PD


def upperarm(mk, M, T, s, L):
    x = lambda v: s * v
    UA = [ball(J('upperarm', s), 0.16, M['frame'], name='shoulderball'),
          frustum((x(0.99), 3.80, 0.08), (x(1.05), 3.08, 0.10), 0.11, 0.10, M['frame'], 8, name='humerus')]
    UA.append(frustum((x(0.995), 3.70, 0.083), (x(1.035), 3.24, 0.093), 0.172, 0.158, M['white'], 8, squash=(1.0, 1.12), bev=0.016, ref=(1, 0, 0), name='bicep'))
    UA.append(frustum((x(1.012), 3.47, 0.088), (x(1.017), 3.43, 0.089), 0.172, 0.17, M['frame'], 8, squash=(1.0, 1.12), bev=0.004, ref=(1, 0, 0), name='bicep_band'))
    UA += ram((x(1.00), 3.62, 0.29), (x(1.04), 3.24, 0.28), 0.035, M)
    mk.add('upperarm_' + L, UA); T['upperarm_' + L] = UA


def forearm(mk, M, T, s, L):
    x = lambda v: s * v
    FA = [cyl((x(0.93), 3.04, 0.10), (x(1.19), 3.04, 0.10), 0.12, M['frame'], 16, name='elbow'),
          hull([(x(a), y, z) for a in (0.96, 1.16) for (y, z) in ((3.18, 0.12), (2.90, 0.14), (3.18, 0.25), (2.92, 0.27))] + [(x(1.06), 3.04, 0.39)], M['white'], 0.012, seg=3, name='elbowguard')]
    FA.append(frustum((x(1.07), 2.96, 0.10), (x(1.11), 2.40, 0.07), 0.155, 0.215, M['paint'], 8, squash=(1.0, 1.15), bev=0.016, ref=(1, 0, 0), name='vambrace'))
    FA.append(frustum((x(1.08), 2.44, 0.075), (x(1.115), 2.30, 0.065), 0.19, 0.19, M['dark'], 8, squash=(0.92, 1.08), bev=0.008, ref=(1, 0, 0), name='cuff'))
    # the outer plate (white) on the vambrace, a glow line down it, a swept fin off the back
    op = [(x(1.27), 2.92, -0.06), (x(1.27), 2.92, 0.20), (x(1.33), 2.46, 0.24), (x(1.33), 2.46, -0.10)]
    if s < 0: op = op[::-1]
    on = norm((s * 0.992, 0.13, 0))
    FA.append(plate(op, 0.08, on, M['white'], 0.012, 3, name='vamb_plate'))
    FA += gline((x(1.278), 2.86, 0.07), (x(1.318), 2.55, 0.07), on, M, name='vamb_line')
    FA.append(tri_plate((x(1.24), 2.95, 0.06), (x(1.28), 2.48, 0.12), (x(1.40), 2.56, 0.46), 0.035, M['white'], name='fin'))
    FA.append(tri_plate((x(1.35), 2.59, 0.33), (x(1.385), 2.53, 0.38), (x(1.405), 2.555, 0.465), 0.045, M['paint'], name='fin_tip'))
    FA += bolts([(x(1.272 + 0.0), 2.86, -0.02), (x(1.272), 2.86, 0.16)], (s, 0.13, 0), M['frame'], 0.015, 0.01)
    FA += louvres((x(0.93), 2.66, 0.10), norm((-s, 0.036, 0)), (0, 1, 0), 0.20, 0.30, 4, M, 0.022, bar=0.022, name='vamb_vent')
    mk.add('forearm_' + L, FA); T['forearm_' + L] = FA


def cannon(mk, M, T, s, L):
    """twin beam barrels under the forearm, chisel-cut muzzles in the team colour (MECH DROP fires them from mk_muzzle_*)"""
    x = lambda v: s * v
    C = [hull([(x(a), y, z) for a in (1.00, 1.26) for y in (2.31, 2.58) for z in (-0.12, -0.46)], M['dark'], 0.03, seg=3, name='housing')]
    lid = [(x(1.02), 2.585, -0.14), (x(1.24), 2.585, -0.14), (x(1.24), 2.585, -0.44), (x(1.02), 2.585, -0.44)]
    C.append(quad_slab(lid, 0.05, M['white'], 0.01, name='lid'))
    C.append(frustum((x(1.09), 2.47, 0.08), (x(1.09), 2.55, 0.08), 0.25, 0.25, M['frame'], 10, squash=(0.95, 1.1), bev=0.01, ref=(1, 0, 0), name='clamp'))
    for dx in (-0.056, 0.056):
        cx = x(1.14) + dx
        C.append(frustum((cx, 2.40, -0.40), (cx, 2.40, -0.62), 0.052, 0.050, M['white'], 6, bev=0.006, ref=(0, 1, 0), rot=0, name='shroud'))
        C.append(cyl((cx, 2.40, -0.60), (cx, 2.40, -0.67), 0.036, M['frame'], 12, name='barrel'))
        C.append(hull([(cx + a, 2.40 + b, -0.655) for a in (-0.034, 0.034) for b in (-0.032, 0.032)] + [(cx + a, 2.40 + b, -0.75) for a in (-0.03, 0.03) for b in (-0.008, 0.014)], M['paint'], 0.006, name='muzzle'))
        C += ribs((cx, 2.40, -0.46), (0, 0, -1), 0.056, 0.056, 3, 0.12, M['frame'])
    C += gline((x(1.261), 2.445, -0.16), (x(1.261), 2.445, -0.42), (s, 0, 0), M, name='cannon_line')
    mk.add('cannon_' + L, C); T['cannon_' + L] = C


def hand(mk, M, T, s, L):
    x = lambda v: s * v
    hd = J('hand', s)
    HA = [ball(hd, 0.095, M['frame'], name='wrist')]
    HA.append(hull([(x(a), y, z) for a in (1.02, 1.21) for (y, z) in ((2.24, -0.14), (2.24, 0.18), (1.94, -0.15), (1.94, 0.17))], M['dark'], 0.016, name='palm'))
    bp = [(x(1.215), 2.23, -0.12), (x(1.215), 2.23, 0.16), (x(1.225), 1.98, 0.15), (x(1.225), 1.98, -0.13)]
    if s < 0: bp = bp[::-1]
    HA.append(plate(bp, 0.05, (s, 0, 0), M['white'], 0.012, 2, name='handplate'))
    HA.append(cyl((x(1.115), 1.965, -0.13), (x(1.115), 1.965, 0.15), 0.05, M['frame'], 10, name='knucklebar'))
    for k, z in enumerate((-0.095, -0.015, 0.065, 0.14)):  # four chunky fingers, curled a little
        p0 = (x(1.12), 1.97 + 0.006 * k, z); p1 = (x(1.085), 1.82 + 0.01 * (k == 3), z); p2 = (x(1.035), 1.71 + 0.03 * (k == 3), z + 0.005)
        HA.append(frustum(p0, p1, 0.045, 0.041, M['frame'], 6, bev=0.006, name='finger'))
        HA.append(frustum(p1, p2, 0.041, 0.035, M['dark'], 6, bev=0.006, name='fingertip'))
        HA += dt([hull([add(p0, (x(dx), dy, dz)) for dx in (0.03, 0.058) for dy in (-0.02, -0.10) for dz in (-0.028, 0.028)], M['white'], 0.004, name='knuckleplate')])
    HA.append(frustum((x(1.08), 2.14, -0.13), (x(1.05), 2.00, -0.22), 0.046, 0.04, M['frame'], 6, bev=0.006, name='thumb'))
    HA.append(frustum((x(1.05), 2.00, -0.22), (x(1.02), 1.89, -0.24), 0.04, 0.034, M['dark'], 6, bev=0.006, name='thumbtip'))
    mk.add('hand_' + L, HA); T['hand_' + L] = HA


# ------------------------------------------------------------ wings: folded delta binders (built flat in their jet layout, then stowed)
def wing(mk, M, T, s, L):
    def W2(px, py, z): return (s * px, py, z)  # (in the plane: px out from the middle, py up)
    R1, R2, Wt = (0.30, 4.02), (0.30, 2.77), (1.86, 2.64)
    Cm = ((R2[0] + Wt[0]) / 2, (R2[1] + Wt[1]) / 2)
    def L2(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    def N2(a, b, toward, k):  # move the segment a-b k metres sideways (toward a point)
        dx, dy = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dy); nx, ny = -dy / l, dx / l
        if (toward[0] - a[0]) * nx + (toward[1] - a[1]) * ny < 0: nx, ny = -nx, -ny
        return (a[0] + nx * k, a[1] + ny * k), (b[0] + nx * k, b[1] + ny * k)
    def isect(p1, p2, p3, p4):
        x1, y1 = p1; x2, y2 = p2; x3, y3 = p3; x4, y4 = p4
        d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4); t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    Wg = []
    zb, zc = 0.85, 0.905  # the core (dark): its underside and its top
    Wg.append(hull([W2(*p, z) for p in (R1, R2, Wt) for z in (zb, zc)], M['dark'], 0.012, name='wing_core'))
    # the leading edge band (team colour) wraps the edge; a glow line in the gap behind it
    le_in = N2(R1, Wt, R2, 0.085)
    a0, a1 = L2(R1, Wt, 0.05), L2(R1, Wt, 0.80); b0, b1 = L2(le_in[0], le_in[1], 0.05), L2(le_in[0], le_in[1], 0.80)
    o0, o1 = N2(a0, a1, R2, -0.006)
    Wg.append(hull([W2(*p, z) for p in (o0, o1, b0, b1) for z in (zb - 0.008, zc + 0.022)], M['paint'], 0.01, name='leading'))
    gl0, gl1 = N2(R1, Wt, R2, 0.112)
    Wg += gline(W2(*L2(gl0, gl1, 0.08), zc), W2(*L2(gl0, gl1, 0.78), zc), (0, 0, 1), M, w=0.016, name='wing_line')
    # two top plates (white) creased along R1 - Cm: the inner one rises to the crease, the outer one too (a mountain fold)
    def facet(pts, zlo, zhi_of):
        return hull([W2(*p, 0.895) for p in pts] + [W2(*p, zhi_of(p)) for p in pts], M['white'], 0.012, seg=3, name='facet')
    def h_of(p):  # the fold's height at a point (0 at the outline, up toward the crease line)
        dx, dy = Cm[0] - R1[0], Cm[1] - R1[1]; l = math.hypot(dx, dy)
        dist = abs((p[0] - R1[0]) * dy - (p[1] - R1[1]) * dx) / l
        along = ((p[0] - R1[0]) * dx + (p[1] - R1[1]) * dy) / l / l
        return 0.922 + 0.03 * along + max(0.0, 0.035 - dist * 0.07)
    ci0, ci1 = N2(R1, Cm, R2, 0.022)  # (the crease gap: 44 mm, a dark spine and a glow strip in it)
    co0, co1 = N2(R1, Cm, Wt, 0.022)
    root_in = N2(R1, R2, Wt, 0.13)  # (the root block covers the first 13 cm)
    te_in = N2(R2, Wt, R1, 0.03)
    p_a = isect(ci0, ci1, *root_in); p_b = isect(*root_in, *te_in); p_c = isect(*te_in, ci0, ci1)
    cut = N2(R2, Wt, R1, 0.52); cut_a, cut_b = N2(*cut, R1, 0.012), N2(*cut, R2, 0.012)  # (a seam across both plates)
    Wg.append(facet([p_a, isect(*root_in, *cut_a), isect(*cut_a, ci0, ci1)], 0.895, h_of))
    Wg.append(facet([isect(*cut_b, ci0, ci1), isect(*root_in, *cut_b), p_b, p_c], 0.895, h_of))
    lef = N2(R1, Wt, R2, 0.14)  # (the outer plate starts behind the glow line)
    seam = (L2(R1, Wt, 0.74), L2(Cm, Wt, 0.52))  # (the tip plate beyond this seam)
    seam_in = N2(seam[0], seam[1], R1, 0.018); seam_out = N2(seam[0], seam[1], Wt, 0.018)
    q_a = isect(co0, co1, *lef); q_b = isect(*lef, *seam_in); q_c = isect(*seam_in, *te_in); q_d = isect(*te_in, co0, co1)
    Wg.append(facet([q_a, isect(*lef, *cut_a), isect(*cut_a, co0, co1)], 0.895, h_of))
    Wg.append(facet([isect(*cut_b, co0, co1), isect(*cut_b, *lef), q_b, q_c, q_d], 0.895, h_of))
    q_e = isect(*seam_out, *lef); q_f = isect(*seam_out, *te_in)
    tip = [q_e, L2(lef[0], lef[1], 1.0), q_f]
    Wg.append(hull([W2(*p, z) for p in tip for z in (0.895, 0.934)], M['hazard'], 0.01, name='wingtip'))
    # the crease spine (dark) and its glow
    sp0, sp1 = L2(R1, Cm, 0.10), L2(R1, Cm, 0.97)
    nsp = N2(sp0, sp1, R2, 0.016); fsp = N2(sp0, sp1, Wt, 0.016)
    zs = lambda t: 0.94 + 0.03 * t
    Wg.append(hull([W2(*p, z) for p, t in ((nsp[0], 0.10), (nsp[1], 0.97), (fsp[0], 0.10), (fsp[1], 0.97)) for z in (0.90, zs(t))], M['dark'], 0.0, 1, 'crease'))
    g0, g1 = L2(sp0, sp1, 0.02), L2(sp0, sp1, 0.98); ng = N2(g0, g1, R2, 0.008); fg = N2(g0, g1, Wt, 0.008)
    Wg.append(hull([W2(*p, z) for p, t in ((ng[0], 0.12), (ng[1], 0.95), (fg[0], 0.12), (fg[1], 0.95)) for z in (zs(t) - 0.01, zs(t) + 0.006)], M['thrust'], 0.0, 1, 'crease_glow'))
    # the root block (gunmetal) over the hinge end, bolted
    Wg.append(hull([W2(px, py, z) for px in (0.22, 0.42) for py in (2.84, 4.10) for z in (0.83, 0.955)], M['frame'], 0.016, seg=3, name='wing_root'))
    Wg += bolts([W2(0.36, py, 0.955) for py in (3.0, 3.3, 3.6, 3.9)], (0, 0, 1), M['chrome'], 0.016, 0.01)
    # the underside (seen from the front when stowed): a glowing outline loop, a gunmetal panel, team-colour stripes
    lei, tei, rti = N2(R1, Wt, R2, 0.18), N2(R2, Wt, R1, 0.14), N2(R1, R2, Wt, 0.22)
    k1, k2, k3 = isect(*lei, *rti), isect(*rti, *tei), isect(*tei, *lei)
    for (a_, b_) in ((k1, k3), (k2, k3), (k1, k2)):
        Wg += gline(W2(*L2(a_, b_, 0.07), zb), W2(*L2(a_, b_, 0.93), zb), (0, 0, -1), M, w=0.016, name='under_line')
    pin = [N2(R1, Wt, R2, 0.26), N2(R2, Wt, R1, 0.22), N2(R1, R2, Wt, 0.30)]
    pk = [isect(*pin[0], *pin[2]), isect(*pin[2], *pin[1]), isect(*pin[1], *pin[0])]
    Wg.append(hull([W2(*p, z) for p in pk for z in (zb + 0.01, zb - 0.014)], M['frame'], 0.006, name='under_panel'))
    for k in range(2):  # two team-colour stripes along the leading edge, on the panel
        sa = N2(R1, Wt, R2, 0.33 + 0.07 * k); p0, p1 = L2(sa[0], sa[1], 0.30 + 0.05 * k), L2(sa[0], sa[1], 0.56)
        sb_ = N2(p0, p1, R2, 0.035)
        Wg.append(hull([W2(*p, z) for p in (p0, p1, sb_[1], sb_[0]) for z in (zb - 0.010, zb - 0.022)], M['paint'], 0.0, 1, name='stripe'))
    # trailing edge flaps (dark) with glow slits, near the root
    te = N2(R2, Wt, R1, -0.004)
    for t0_ in (0.16, 0.36):
        a, b = L2(te[0], te[1], t0_), L2(te[0], te[1], t0_ + 0.14)
        fl = [a, b, (b[0], b[1] + 0.10), (a[0], a[1] + 0.10)]
        Wg += dt([hull([W2(*p, z) for p in fl for z in (zb + 0.012, zc + 0.03)], M['frame'], 0.004, name='flap')])
    Mx = wing_stow(s)
    for o in Wg: xform(o, Mx)
    mk.add('wing_' + L, Wg); T['wing_' + L] = Wg
    mk.meta.setdefault('wing_layout', {})[L] = {'R1': R1, 'R2': R2, 'tip': Wt, 'crease': Cm}
    if L == 'L': mk.meta['_facet_h'] = h_of


# ------------------------------------------------------------ the crane drone: a faceted recon bit docked on the left wing
def crane(mk, M, T):
    c0 = CRANE_AT; F, U, R = (0, 1, 0), (0, 0, 1), (1, 0, 0)  # forward = toward the hinge, up = off the wing
    hb = mk.meta.pop('_facet_h')((-c0[0], c0[1])) - c0[2] + 0.004  # (the plate's face under the dock)
    def Q(f, u, r): return add(c0, add(mul(F, f), add(mul(U, u + hb), mul(R, r))))
    D = [hull([Q(f, u, r) for f in (-0.07, 0.07) for u in (-0.03, 0.035) for r in (-0.05, 0.05)], M['frame'], 0.008, name='dock')]
    D.append(hull([Q(-0.17, 0.06, 0), Q(0.16, 0.07, 0), Q(0.0, 0.165, 0), Q(-0.02, 0.08, 0.085), Q(-0.02, 0.08, -0.085), Q(0.02, 0.03, 0), Q(-0.10, 0.12, 0.04), Q(-0.10, 0.12, -0.04)],
                  M['white'], 0.008, name='crane_body'))
    D.append(hull([Q(f, u, r) for f in (-0.10, 0.10) for u in (0.026, 0.05) for r in (-0.044, 0.044)], M['dark'], 0.004, name='crane_belly'))
    D.append(tri_plate(Q(0.07, 0.09, 0), Q(0.15, 0.07, 0), Q(0.31, 0.215, 0), 0.03, M['white'], 0.004, name='crane_neck'))
    D.append(hull([Q(0.29, 0.20, 0), Q(0.31, 0.225, 0), Q(0.40, 0.19, 0), Q(0.31, 0.195, 0.026), Q(0.31, 0.195, -0.026), Q(0.32, 0.17, 0)], M['paint'], 0.004, name='crane_head'))
    D.append(hull([Q(0.355, 0.20, r) for r in (-0.03, 0.03)] + [Q(0.335, 0.21, r) for r in (-0.026, 0.026)] + [Q(0.35, 0.183, 0)], M['thrust'], 0.002, name='crane_eye'))
    D.append(hull([Q(0.385, 0.19, 0), Q(0.405, 0.19, 0), Q(0.39, 0.20, 0), Q(0.39, 0.186, 0.008), Q(0.39, 0.186, -0.008)], M['hazard'], 0.0, name='crane_beak'))
    D.append(tri_plate(Q(-0.08, 0.10, 0), Q(-0.16, 0.07, 0), Q(-0.32, 0.23, 0), 0.03, M['white'], 0.004, name='crane_tail'))
    D += dt(nozzle(Q(-0.17, 0.08, 0), norm(sub(Q(-0.3, 0.06, 0), Q(-0.17, 0.08, 0))), 0.028, 0.05, M, 'crane_jet'))
    Wn = {'L': [], 'R': []}
    for sd, L in ((-1, 'L'), (1, 'R')):  # (the crane faces +y here, so its right is +x)
        root = [Q(-0.08, 0.075, sd * 0.02), Q(0.08, 0.075, sd * 0.02)]
        tip = Q(-0.03, 0.17, sd * 0.36)
        Wn[L].append(hull([add(p, (0, 0, dz)) for p in root + [tip, Q(0.03, 0.14, sd * 0.24)] for dz in (-0.008, 0.008)], M['white'], 0.004, name='crane_wing'))
        Wn[L].append(hull([add(p, (0, 0, dz)) for p in (Q(-0.05, 0.155, sd * 0.29), Q(-0.015, 0.16, sd * 0.29), tip) for dz in (-0.0105, 0.0105)], M['paint'], 0.002, name='crane_wingtip'))
        Wn[L].append(hull([add(p, (0, 0, dz)) for p in (Q(-0.04, 0.10, sd * 0.07), Q(0.02, 0.10, sd * 0.07), Q(-0.025, 0.145, sd * 0.22)) for dz in (-0.004, 0.0115)], M['thrust'], 0.0, 1, name='crane_wingglow'))
    Mx = wing_stow(-1)
    for o in D + Wn['L'] + Wn['R']: xform(o, Mx)
    mk.add('drone', D); mk.add('drone_wing_L', Wn['L']); mk.add('drone_wing_R', Wn['R']); T['drone'] = D + Wn['L'] + Wn['R']


# ------------------------------------------------------------ stickers and the spray slots
def decals(mk, M, T):
    m = tex_mat('pp_decalmat', image_rgba('pp_decals', sheet()), rough=0.42, clip=True, cc=0.5)
    mk.add('shoulder_L', stamp(T['shoulder_L'], 'num', (-1.36, 3.90, 0.04), (-0.984, 0.183, 0), (0, 1, 0), 0.40, m))
    mk.add('shoulder_R', stamp(T['shoulder_R'], 'tri', (1.37, 3.93, 0.24), (0.984, 0.183, 0), (0, 1, 0), 0.10, m))
    mk.add('hatch', stamp(T['hatch'], 'rescue', (0.20, 3.62, -0.62), norm((0.55, 0, -0.83)), (0, 1, 0), 0.11, m))
    mk.add('hatch', stamp(T['hatch'], 'eject', (-0.20, 3.62, -0.62), norm((-0.55, 0, -0.83)), (0, 1, 0), 0.13, m))
    mk.add('forearm_R', stamp(T['forearm_R'], 'serial', (1.31, 2.62, 0.10), norm((0.992, 0.13, 0)), (0, 1, 0), 0.20, m))
    mk.add('backpack', stamp(T['backpack'], 'works', (0, 3.62, 0.85), norm((0, 0.03, 1)), (0, 1, 0), 0.26, m))
    for s, L in ((1, 'R'), (-1, 'L')):
        mk.add('pod_' + L, stamp(T['pod_' + L], 'aero', (s * 1.205, 4.37, 0.02), (s, 0, 0), (0, 1, 0), 0.30, m))
        mk.add('pod_' + L, stamp(T['pod_' + L], 'chev', (s * 1.0, 4.464, 0.26), (0, 1, 0), (0, 0, -1), 0.26, m))
        mk.add('thigh_' + L, stamp(T['thigh_' + L], 'nostep', (s * 0.43, 2.27, -0.33), norm((0, 0.05, -1)), (0, 1, 0), 0.16, m))
        # on the wings (placed in the flat jet layout, then stowed): FOLD HERE along the crease, JANK AERO, the emblem under
        Mx = wing_stow(s); R3 = Mx.to_3x3()
        def wd(cell, px, py, h, nz, up, w):
            return stamp(T['wing_' + L], cell, g_of(Mx @ gv(s * px, py, h)), g_of((R3 @ gv(0, 0, nz)).normalized()), g_of((R3 @ gv(*up)).normalized()), w, m, reach=0.2)
        cr = (s * 0.86, 0.51, 0)  # (across the crease, in the plane: the text runs along it)
        mk.add('wing_' + L, wd('fold', 0.988, 3.095, 0.97, 1, cr, 0.50))
        if s > 0: mk.add('wing_' + L, wd('aero', 0.72, 3.04, 0.97, 1, cr, 0.30))
        mk.add('wing_' + L, wd('emblem', 0.90, 3.05, 0.85, -1, (0, 1, 0), 0.24))
    # the spray slots: the left chest plate and the right pauldron's wall
    n0 = norm((-0.33, 0, -1)); c0 = pec_pt(-0.53, 3.70, 0.0)
    nw = norm((0.984, 0.183, 0)); c1 = (1.3555, 3.90, 0.04)
    mk.meta['spray'] = [{'name': 'spray_0', 'joint': 'chest', 'at': [round(v, 4) for v in c0], 'dir': [round(v, 4) for v in n0], 'up': [0, 1, 0], 'size': 0.6},
                        {'name': 'spray_1', 'joint': 'shoulder_R', 'at': [round(v, 4) for v in c1], 'dir': [round(v, 4) for v in nw], 'up': [round(v, 4) for v in norm(sub((0, 1, 0), mul(nw, nw[1])))], 'size': 0.37}]


# ------------------------------------------------------------ markers, clips, poses (make_hero.py)
def marks(mk):
    m = {k: {'joint': j, 'at': at, 'dir': d} for k, (j, at, d) in MARKS.items()}
    for sl in mk.meta.get('spray', []):
        m['mk_' + sl['name']] = {'joint': sl['joint'], 'at': tuple(sl['at']), 'dir': tuple(sl['dir'])}
    return m


def clips():
    return C.all_clips('pp', tuple(DRONE_AXIS))


POSES = {'ready': pose_ready, 'jet': pose_jet, 'rest': lambda mk: {}}
