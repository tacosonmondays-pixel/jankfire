# JANKFIRE Platform: the drilling side under and around the derrick (both rig maps), two props built over
# shared/map.js drillSide()'s boxes (the same numbers here):
# p_substructure: under the drill floor, origin = the derrick's middle on the main deck (world -24, 0, 0 on Platform).
#   The substructure's six box columns on their base plates, the girders round it at 3.3 m, the floor's beams (the deck
#   plate stays the game's), knee braces up under the floor. The BOP stack: wellhead connector, two double ram
#   preventers (their bonnets and hydraulic cylinders out each side), the drilling spool with the choke and kill valves,
#   the annular on top, the riser up through the floor, the wellhead and casing spools on down through the main deck to
#   the cellar deck (BLOWOUT PREVENTER, prevents blowouts. mostly.). The mud tanks (three compartments, agitators on top,
#   suction pipes, MUD. JUST MUD.), the two triplex mud pumps (power end, fluid end with its three caps, the motor, the
#   belt guard, the pulsation dampener on its discharge, the skid).
# p_drillfloor: on the drill floor, origin = the rotary table (world -24, 7.2, 0). The rotary table (master bushing,
#   slips), the drawworks (the drum with its wraps, brake discs, gearbox, two motors on the skid, the guards; the fast line
#   leaves its drum where the derrick's comes down), the doghouse (the driller's cabin: blue cladding, its window onto
#   the rotary, the door, an A/C unit, the sign: DOGHOUSE (NO DOGS), a dog bowl anyway).
# Visual only: the columns, the BOP, the tanks, the pumps, the drawworks and the doghouse are the map's solid boxes.
# run: blender52 -b --python tools/blender/make_drillfloor.py -- [--only=substructure,drillfloor] [--qa] [--stats]
#      [--no-sheet] [--no-export] [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, uv_fit, uv_trim, run_prop, tnoise, box_between, poly_obj, orient, opt, ONLY
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi
FY = 6.8  # the drill floor's underside (its deck plate: 6.8..7.2)
CD = -7.2


def sub_boxes():
    out = []; L = lambda *b: out.append(b)
    for x in (-10, -0.5, 9):
        for z in (-10, 9): L(x, 0, z, x + 1, FY, z + 1)
    for z in (-9.7, 9.3): L(-9, 3.3, z, 9, 3.7, z + 0.4)
    for x in (-9.7, 9.3): L(x, 3.3, -9, x + 0.4, 3.7, 9)
    L(-1.3, 0, -1.3, 1.3, 4.6, 1.3); L(-0.7, 4.6, -0.7, 0.7, FY, 0.7); L(-0.9, CD, -0.9, 0.9, -0.5, 0.9)
    for s in (-1, 1): L(-1.36, 1.2 + s * 0.6 + 0.6, -1.36, 1.36, 1.6 + s * 0.6 + 0.6, 1.36)
    L(1.36, 2.6, -1.0, 1.42, 3.5, 1.0)
    L(-9.8, 0, -8, -7.4, 3.2, 8); L(-7.4, 1.8, -2, -7.34, 2.8, 2)
    for s in (-1, 1): L(2, 0, s * 6.5 - 1, 6, 2.2, s * 6.5 + 1); L(2.4, 2.2, s * 6.5 - 0.5, 5.6, 2.6, s * 6.5 + 0.5)
    return out


def floor_boxes():
    out = []; L = lambda *b: out.append(b)
    L(-1, 0, -1, 1, 0.05, 1)
    L(-7.4, 0, -2, -4.8, 1.6, 2); L(-7.2, 1.6, -1.6, -5, 2.0, 1.6)
    L(5.5, 0, 5.6, 9.7, 2.8, 9.7); L(5.44, 1.2, 6.2, 5.5, 2.2, 9.1); L(6.2, 2.8, 6.2, 9.0, 3.0, 9.1)
    return out


# ------------------------------------------------------------ the atlas
def _chipped(col, seed, rust=0x9a4a22, p=0.05, streaks=3):
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        px[:] = hexrgb(col)[None, None] * (0.93 + 0.1 * r.random((h, w, 1)))
        m = (tnoise(w, h, 4, 4, r) + 0.35 * r.random((h, w))) > 1.12
        px[m] = hexrgb(rust) * (0.8 + 0.3 * r.random((int(m.sum()), 1)))
        for k in range(streaks):
            x = int(r.integers(0, w)); L = int(r.integers(h // 3, h))
            px[:L, x] = px[:L, x] * 0.55 + hexrgb(rust) * 0.45
    return d


def _label(lines, bg, fg, seed, scale=1, border=None, small=None):
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        px[:] = hexrgb(bg) * (0.92 + 0.1 * r.random((h, w, 1)))
        if border is not None: px[:1] = px[-1:] = hexrgb(border); px[:, :1] = px[:, -1:] = hexrgb(border)
        y = (h - 8 * scale * len(lines)) // 2 + scale
        for i, s in enumerate(lines):
            c = small if (small is not None and i > 0) else fg
            tw = (len(s) * 6 - 1) * scale; text_px(px, s, max(0, (w - tw) // 2), y, scale, c); y += 8 * scale
    return d


def _ribs(col, seed):
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        s = 0.86 + 0.16 * np.cos(np.arange(w) / w * TAU * 8)
        px[:] = hexrgb(col)[None, None] * s[None, :, None] * (0.95 + 0.06 * r.random((h, w, 1)))
        px[-2:] *= 0.7
        for k in range(5): x, y = int(r.integers(0, w)), int(r.integers(h // 2, h)); px[y:, x] = px[y:, x] * 0.7 + hexrgb(0x9a5a30) * 0.3
    return d


def _wraps(px):  # the drum's wire: wraps across u, dark with a shine
    h, w = px.shape[:2]; px[:] = hexrgb(0x3a3c42)
    px[:, ::2] = hexrgb(0x7a808a); px[::3] *= 0.8


def _fins(px):  # a motor's cooling fins along v
    h, w = px.shape[:2]; px[:] = hexrgb(0x2a6ad8)
    px[:, ::3] = hexrgb(0x1a4aa0)


def atlas():
    A = Atlas('df_atlas', 128, 224)
    A.band('redband', 16, _chipped(0xd8202a, 71, p=0.03, streaks=6))
    A.band('blueribs', 16, _ribs(0x2a6ad8, 72))
    A.band('mudband', 16, _chipped(0x2a6ad8, 73, rust=0x6a4a2a, p=0.03, streaks=8))
    A.band('wraps', 8, _wraps)
    A.cell('red', 32, 32, _chipped(0xe8202a, 74))
    A.cell('yellow', 32, 32, _chipped(0xffd21a, 75, rust=0xa0782a, streaks=1))
    A.cell('blue', 32, 32, _chipped(0x2a6ad8, 76, rust=0x6a4a2a, streaks=2))
    A.cell('steel', 32, 32, _chipped(0x8a96a6, 77, rust=0x8a4a22, streaks=2))
    A.cell('bop', 64, 16, _label(['BLOWOUT PREVENTER', 'prevents blowouts. mostly.'], 0xc81a2a, 0xffffff, 78, small=0xffe14d))
    A.cell('mud', 48, 16, _label(['MUD.', 'JUST MUD.'], 0x5a3a20, 0xffe14d, 79))
    A.cell('dog', 64, 16, _label(['DOGHOUSE', '(NO DOGS)'], 0xffe14d, 0x1a1a1a, 80, border=0x1a1a1a))
    A.cell('fins', 16, 16, _fins)
    for k, c, v, sp in (('galv', 0xa8b0ba, 0.06, None), ('dark', 0x2a2c32, 0.05, None), ('grate', 0x5a6068, 0.1, 0x2a2c30),
                        ('glass', 0x28384a, 0.04, None), ('rubber', 0x1c1c22, 0.05, None), ('mudbrown', 0x6a4a2a, 0.12, 0x4a3018),
                        ('white', 0xf4f2ee, 0.03, None), ('pink', 0xff4fd8, 0.03, None), ('hazard', 0xffd21a, 0.02, 0x1a1a1a),
                        ('orange', 0xff7a1a, 0.04, None), ('brass', 0xe8b438, 0.06, None)):
        A.swatch(k, c, v, 140 + len(A.r), w=8, h=8, speck=sp, p=0.25 if sp else 0.0)
    return A


def rodk(p0, p1, r, M, A, key, name, seg=8):
    o = rod(p0, p1, r, M, seg=seg, name=name); uv_fit(o, A, key); return o


def boxk(size, pos, M, A, key, name, bev=0.0, rot=None):
    o = box(size, pos, M, bev=bev, rot=rot, name=name); uv_fit(o, A, key); return o


def cylk(r, L, pos, M, A, key, name, axis='y', seg=12, bev=0.0, r2=None, cap=True):
    o = cyl(r, L, pos, M, axis=axis, seg=seg, name=name, bev=bev, r2=r2, cap=cap); uv_fit(o, A, key); return o


def handwheel(c, axis, r, M, A, P, name='df_wheel', key='yellow'):
    rim = lathe([(r - 0.025, -0.02), (r + 0.015, -0.02), (r + 0.015, 0.02), (r - 0.025, 0.02), (r - 0.025, -0.02)], c, M, seg=12, axis=axis, name=name, cap=False); uv_fit(rim, A, key); P.append(rim)
    P.append(cylk(0.04, 0.08, c, M, A, 'dark', name + 'hub', axis=axis, seg=6))
    cv = V3(c)
    for k in range(3):
        a = TAU * k / 3 + 0.4
        d = V3((0, math.cos(a), math.sin(a))) if axis == 'x' else V3((math.cos(a), 0, math.sin(a))) if axis == 'y' else V3((math.cos(a), math.sin(a), 0))
        P.append(rodk(tuple(cv), tuple(cv + d * (r - 0.01)), 0.012, M, A, key, name + 'spoke', seg=4))


def mats(A):
    M = mat('df_paint', 0xffffff, rough=0.28, metal=0.15, tex=A.image(), clearcoat=0.8)
    CH = mat('df_chrome', 0xdfe3ea, rough=0.14, metal=0.95, clearcoat=0.3)
    return M, CH


def finish(P, Q, A, bx, focus, lod=70):
    for p in P + Q:
        if p.type == 'MESH' and not p.data.uv_layers: uv_fit(p, A, 'galv')
    for p in P: lib.smooth(p, 35)
    if opt('stats'):
        import re, collections
        tot = collections.Counter()
        for p in P: tot[re.sub(r'\.\d+$', '', p.name)] += MK.tris_of([p])
        for k, v in tot.most_common(12): print('JF_STAT', k, v)
    lo = tuple(min(b[k] for b in bx) for k in range(3)); hi = tuple(max(b[k + 3] for b in bx) for k in range(3))
    return dict(lod0=P, lod1=Q, box=(lo, hi), ao=0.8, lod=lod, meta={'kind': 'prop'}, focus=focus)


# ============================================================ p_substructure
def build_substructure():
    A = atlas(); M, CH = mats(A)
    P, Q = [], []
    # ---- the columns: box sections on base plates, plated, stiffener ribs, knee braces up under the floor
    for x in (-10, -0.5, 9):
        for z in (-10, 9):
            cx, cz = x + 0.5, z + 0.5
            o = box((1.0, FY - 0.06, 1.0), (cx, 0.06 + (FY - 0.06) / 2, cz), M, bev=0.04, name='df_col'); uv_trim(o, A, 'redband', upm=0.5, grain='y'); P.append(o)
            P.append(boxk((1.4, 0.06, 1.4), (cx, 0.03, cz), M, A, 'steel', 'df_colbase'))
            for bx_, bz_ in ((-0.6, -0.6), (0.6, -0.6), (-0.6, 0.6), (0.6, 0.6)):
                P.append(cylk(0.04, 0.08, (cx + bx_, 0.1, cz + bz_), M, A, 'galv', 'df_bolt', seg=4))
            for k in range(2):  # stiffeners on the two faces you see
                P.append(boxk((0.06, 0.8, 0.3), (cx + (0.53 if x < 0 else -0.53), 0.46, cz + (k - 0.5) * 0.5), M, A, 'red', 'df_stiff'))
            sz = -1 if cz > 0 else 1  # a knee brace in toward the middle, up under the floor
            P.append(box_between((cx, FY - 1.8, cz + sz * 0.5), (cx, FY - 0.35, cz + sz * 1.9), 0.18, 0.16, M, 'df_knee')); uv_fit(P[-1], A, 'red')
            Q.append(boxk((1.0, FY, 1.0), (cx, FY / 2, cz), M, A, 'red', 'df1_col'))
    # ---- the girders round it (their boxes), I-sections; the floor's beams under the deck plate
    for z in (-9.5, 9.5):
        for dy in (-0.17, 0.17): P.append(boxk((18.0, 0.06, 0.4), (0, 3.5 + dy, z), M, A, 'red', 'df_girdfl'))
        P.append(boxk((18.0, 0.28, 0.06), (0, 3.5, z), M, A, 'red', 'df_girdweb'))
        Q.append(boxk((18.0, 0.4, 0.4), (0, 3.5, z), M, A, 'red', 'df1_gird'))
    for x in (-9.5, 9.5):
        for dy in (-0.17, 0.17): P.append(boxk((0.4, 0.06, 18.0), (x, 3.5 + dy, 0), M, A, 'red', 'df_girdfl'))
        P.append(boxk((0.06, 0.28, 18.0), (x, 3.5, 0), M, A, 'red', 'df_girdweb'))
        Q.append(boxk((0.4, 0.4, 18.0), (x, 3.5, 0), M, A, 'red', 'df1_gird'))
    for x in (-7.5, -5.0, -2.5, 2.5, 5.0, 7.5):  # the floor's beams (the middle bay is the BOP's)
        P.append(boxk((0.3, 0.05, 19.0), (x, FY - 0.025, 0), M, A, 'red', 'df_beamfl')); P.append(boxk((0.05, 0.45, 19.0), (x, FY - 0.27, 0), M, A, 'red', 'df_beamweb'))
        P.append(boxk((0.3, 0.05, 19.0), (x, FY - 0.52, 0), M, A, 'red', 'df_beamfl'))
    for z in (-9.5, 9.5):
        P.append(boxk((19.96, 0.49, 0.5), (0, FY - 0.255, z), M, A, 'red', 'df_maingird', bev=0.02))
    # ---- the BOP stack on the main deck: connector, lower double ram, spool, upper double ram, annular; the riser
    P.append(cylk(0.75, 0.42, (0, 0.21, 0), M, A, 'dark', 'df_conn', seg=16, bev=0.02))
    for k in range(8):
        a = TAU * (k + 0.5) / 8; P.append(cylk(0.07, 0.3, (math.cos(a) * 0.8, 0.25, math.sin(a) * 0.8), M, A, 'yellow', 'df_connclamp', seg=6))
    for i, (y0, y1) in enumerate(((0.42, 1.48), (2.08, 3.12))):  # the double rams (their ring boxes are the yellow bands)
        ym = (y0 + y1) / 2
        o = box((1.3, y1 - y0, 1.15), (0, ym, 0), M, bev=0.06, name='df_ram'); uv_fit(o, A, 'red'); P.append(o)
        for s in (-1, 1):
            for yy in (ym - 0.25, ym + 0.25):  # bonnets and their hydraulic cylinders out each side (along z)
                P.append(cylk(0.24, 0.3, (0, yy, s * 0.71), M, A, 'yellow', 'df_bonnet', axis='z', seg=12))
                P.append(cylk(0.17, 0.42, (0, yy, s * 1.07), M, A, 'red', 'df_rcyl', axis='z', seg=10))
                P.append(cylk(0.2, 0.05, (0, yy, s * 1.3), M, A, 'yellow', 'df_rcap', axis='z', seg=10))
        for dy in (-0.02, y1 - y0 + 0.02):
            P.append(cylk(0.7, 0.06, (0, y0 + dy, 0), M, A, 'red', 'df_ramfl', seg=16))
    o = cylk(0.62, 0.6, (0, 1.78, 0), M, A, 'red', 'df_spool', seg=16); P.append(o)
    for s in (-1, 1):  # the choke and kill lines' valves off the spool (along x)
        P.append(cylk(0.13, 0.5, (s * 0.85, 1.78, 0), M, A, 'red', 'df_klpipe', axis='x', seg=10))
        P.append(boxk((0.34, 0.3, 0.3), (s * 1.12, 1.78, 0), M, A, 'red', 'df_klvalve', bev=0.03))
        handwheel((s * 1.12, 2.02, 0), 'y', 0.2, M, A, P, name='df_klwheel')
    prof = [(0.0, 3.14), (0.95, 3.14), (1.08, 3.3), (1.08, 3.75), (0.9, 4.15), (0.55, 4.45), (0.5, 4.6), (0.0, 4.6)]
    o = lathe(prof, (0, 0, 0), M, seg=20, axis='y', name='df_annular'); uv_fit(o, A, 'red'); P.append(o)
    for k in range(12):
        a = TAU * k / 12; P.append(boxk((0.06, 0.4, 0.06), (math.cos(a) * 1.09, 3.5, math.sin(a) * 1.09), M, A, 'dark', 'df_annstud'))
    P.append(boxk((0.04, 0.85, 1.9), (1.39, 3.05, 0), M, A, 'bop', 'df_bopsign'))
    P.append(boxk((0.18, 0.5, 0.12), (1.29, 3.05, -0.8), M, A, 'steel', 'df_signarm')); P.append(boxk((0.18, 0.5, 0.12), (1.29, 3.05, 0.8), M, A, 'steel', 'df_signarm'))
    P.append(cylk(0.5, FY - 4.65, (0, 4.6 + (FY - 4.65) / 2, 0), M, A, 'steel', 'df_riser', seg=14))
    P.append(cylk(0.66, 0.3, (0, 5.2, 0), M, A, 'dark', 'df_flexjoint', seg=14))
    P.append(cylk(0.7, 0.2, (0, FY - 0.1, 0), M, A, 'red', 'df_bellnipple', seg=14))
    for s in (-1, 1):  # the hydraulic hoses from the BOP up to the floor (control lines), a bundle each side
        P.append(sweep([(s * 0.4, 3.9, 0.95), (s * 0.45, 4.4, 1.05), (s * 0.4, 4.9, 0.85), (s * 0.3, 5.2, 0.62)], [0.04] * 4, M, seg=6, name='df_hose')); uv_fit(P[-1], A, 'rubber')
    Q.append(boxk((2.4, 4.6, 2.4), (0, 2.3, 0), M, A, 'red', 'df1_bop')); Q.append(cylk(0.6, FY - 4.6, (0, 4.6 + (FY - 4.6) / 2, 0), M, A, 'steel', 'df1_riser', seg=8))
    # ---- down through the main deck to the cellar deck: the casing spools and the wellhead, its side valves
    o = cyl(0.7, -0.5 - CD, (0, (CD - 0.5) / 2, 0), M, axis='y', seg=16, name='df_wellhead'); uv_fit(o, A, 'red'); P.append(o)
    for y in (CD + 0.3, CD + 2.4, CD + 4.6):
        P.append(cylk(0.9, 0.12, (0, y, 0), M, A, 'red', 'df_whfl', seg=16))
    for s in (-1, 1):
        P.append(cylk(0.1, 0.5, (s * 0.9, CD + 1.4, 0), M, A, 'red', 'df_whside', axis='x', seg=8))
        P.append(boxk((0.3, 0.28, 0.28), (s * 1.15, CD + 1.4, 0), M, A, 'red', 'df_whvalve', bev=0.03))
        handwheel((s * 1.15, CD + 1.62, 0), 'y', 0.18, M, A, P, name='df_whwheel')
    Q.append(cylk(0.9, -CD, (0, CD / 2, 0), M, A, 'red', 'df1_wellhead', seg=8))
    # ---- the mud tanks: three compartments along z, ribbed, agitators on top, the suction line along the bottom
    tx0, tx1, tz = -9.8, -7.4, 8.0
    o = box((tx1 - tx0, 3.2, 2 * tz), ((tx0 + tx1) / 2, 1.6, 0), M, bev=0.04, name='df_tank'); uv_trim(o, A, 'mudband', upm=0.4, grain='z'); P.append(o)
    for z in (-tz + 0.02, -2.67, 2.67, tz - 0.02):  # the ribs between the compartments and round the ends
        P.append(boxk((tx1 - tx0 + 0.1, 3.22, 0.12), ((tx0 + tx1) / 2, 1.63, z), M, A, 'blue', 'df_tankrib'))
    for z in (-5.33, 0.0, 5.33):  # an agitator on each: gearbox, motor, a hatch beside it
        P.append(boxk((0.8, 0.5, 0.8), (-8.6, 3.45, z), M, A, 'yellow', 'df_agbox', bev=0.04))
        P.append(cylk(0.25, 0.7, (-8.6, 4.05, z), M, A, 'fins', 'df_agmotor', seg=10))
        P.append(cylk(0.27, 0.06, (-8.6, 4.43, z), M, A, 'dark', 'df_agcap', seg=10))
        P.append(boxk((0.7, 0.04, 0.7), (-8.6, 3.22, z + 1.3), M, A, 'hazard', 'df_hatch'))
    P.append(cylk(0.16, 2 * tz - 0.6, (tx1 + 0.18, 0.4, 0), M, A, 'red', 'df_suction', axis='z', seg=10))
    for z in (-5.33, 0.0, 5.33): P.append(boxk((0.22, 0.2, 0.22), (tx1 + 0.1, 0.4, z), M, A, 'steel', 'df_suctbr'))
    P.append(boxk((0.03, 1.0, 4.0), (tx1 + 0.015, 2.3, 0), M, A, 'mud', 'df_mudsign'))
    Q.append(boxk((tx1 - tx0, 3.32, 2 * tz), ((tx0 + tx1) / 2, 1.66, 0), M, A, 'blue', 'df1_tank'))
    for s in (-1, 1): Q.append(boxk((2.1 - tx1, 0.24, 0.24), ((tx1 + 2.1) / 2, 0.4, s * 6.5), M, A, 'red', 'df1_suction'))  # (far away: the pumps' suction lines join them to the tanks)
    # ---- the mud pumps: a skid, the power end, the fluid end (three caps) toward +x, the motor on top, the belt guard,
    # the pulsation dampener on the discharge
    for s in (-1, 1):
        zc = s * 6.5
        P.append(boxk((4.0, 0.2, 2.0), (4.0, 0.1, zc), M, A, 'steel', 'df_skid'))
        o = box((2.0, 1.5, 1.8), (3.2, 0.95, zc), M, bev=0.12, name='df_power'); uv_fit(o, A, 'red'); P.append(o)
        P.append(boxk((1.0, 1.0, 1.6), (4.7, 0.7, zc), M, A, 'red', 'df_fluid', bev=0.05))
        for k in (-1, 0, 1):
            P.append(cylk(0.2, 0.3, (5.35, 0.75, zc + k * 0.5), M, A, 'steel', 'df_cap', axis='x', seg=10))
            P.append(cylk(0.24, 0.06, (5.2, 0.75, zc + k * 0.5), M, A, 'dark', 'df_capring', axis='x', seg=10))
        mo = cylk(0.42, 1.6, (3.0, 2.12, zc - s * 0.25), M, A, 'fins', 'df_motor', axis='x', seg=12); P.append(mo)
        P.append(cylk(0.44, 0.12, (2.15, 2.12, zc - s * 0.25), M, A, 'dark', 'df_fancover', axis='x', seg=12))
        P.append(boxk((0.9, 0.12, 0.7), (3.0, 1.76, zc - s * 0.25), M, A, 'steel', 'df_motorfoot'))
        P.append(boxk((0.25, 1.4, 1.3), (4.05, 1.55, zc - s * 0.05), M, A, 'hazard', 'df_beltguard', bev=0.03))
        P.append(rodk((4.95, 1.2, zc), (4.95, 1.85, zc), 0.08, M, A, 'red', 'df_discharge'))
        P.append(ball(0.32, (4.95, 2.1, zc), M, seg=12, rings=8, name='df_damper')); uv_fit(P[-1], A, 'red')
        P.append(cylk(0.12, 0.12, (4.95, 2.45, zc), M, A, 'dark', 'df_dampercap', seg=8))
        Q.append(boxk((4.0, 2.2, 2.0), (4.0, 1.1, zc), M, A, 'red', 'df1_pump'))
    return finish(P, Q, A, sub_boxes(), [((0, 2.5, 0), (1, 0.3, 0.6), 5.0), ((-8.6, 2.5, 0), (1, 0.4, 0.3), 6.0), ((4, 1.2, 6.5), (1, 0.4, -0.6), 4.5), ((0, -4, 0), (1, 0.2, 0.5), 5.0)])


# ============================================================ p_drillfloor
def build_drillfloor():
    A = atlas(); M, CH = mats(A)
    P, Q = [], []
    # ---- the rotary table, flush with the floor: its ring, the master bushing, a pair of slips parked beside it
    P.append(cylk(0.95, 0.05, (0, 0.025, 0), M, A, 'steel', 'df_rotary', seg=20))
    P.append(boxk((0.9, 0.03, 0.9), (0, 0.065, 0), M, A, 'dark', 'df_bushing'))
    P.append(cylk(0.2, 0.04, (0, 0.085, 0), M, A, 'rubber', 'df_hole', seg=10))
    P.append(boxk((0.5, 0.03, 0.12), (0.65, 0.065, 0.62), M, A, 'hazard', 'df_slipsign'))
    # ---- the drawworks: on a skid, the drum (its wraps) between two brake discs, the gearbox, two motors, guards
    dx0, dx1, dz = -7.4, -4.8, 2.0
    P.append(boxk((dx1 - dx0, 0.3, 2 * dz), ((dx0 + dx1) / 2, 0.15, 0), M, A, 'steel', 'df_dwskid', bev=0.02))
    for s in (-1, 1): P.append(boxk((dx1 - dx0, 1.3, 0.12), ((dx0 + dx1) / 2, 0.95, s * (dz - 0.06)), M, A, 'red', 'df_dwside', bev=0.02))
    o = cyl(0.5, 3.0, (-6.1, 1.5, 0), M, axis='z', seg=18, name='df_drum', cap=False); uv_trim(o, A, 'wraps', upm=3.0, grain='z'); P.append(o)
    for s in (-1, 1):
        P.append(cylk(0.62, 0.08, (-6.1, 1.5, s * 1.5), M, A, 'red', 'df_drumflange', axis='z', seg=18))
        P.append(cylk(0.78, 0.06, (-6.1, 1.5, s * 1.72), CH, A, 'galv', 'df_brakedisc', axis='z', seg=18))
        P.append(boxk((0.3, 0.42, 0.3), (-5.35, 1.95, s * 1.72), M, A, 'yellow', 'df_caliper', bev=0.03))
    P.append(cylk(0.12, 3.9, (-6.1, 1.5, 0), CH, A, 'galv', 'df_drumshaft', axis='z', seg=8))
    for s in (-1, 1):  # two motors on the back (-x) end, their fins and fan covers
        P.append(cylk(0.4, 1.0, (-7.0, 0.75, s * 0.85), M, A, 'fins', 'df_dwmotor', axis='z', seg=12))
        P.append(cylk(0.42, 0.1, (-7.0, 0.75, s * 1.4), M, A, 'dark', 'df_dwfan', axis='z', seg=12))
    P.append(boxk((0.8, 0.5, 0.6), (-7.0, 1.4, 0), M, A, 'red', 'df_dwgearbox', bev=0.05))
    # the guard over the drum's front, the driller's brake handle
    gd = lathe([(0.66, -1.42), (0.66, 1.42)], (-6.1, 1.5, 0), M, seg=18, axis='z', name='df_drumguard', cap=False)
    bm = bmesh.new(); bm.from_mesh(gd.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x > 0.05 or v.co.z < -0.1], context='VERTS')  # (a quarter over the back and top: the fast line leaves the front)
    bm.to_mesh(gd.data); bm.free(); uv_fit(gd, A, 'hazard'); P.append(gd)
    Q.append(boxk((dx1 - dx0, 1.6, 2 * dz), ((dx0 + dx1) / 2, 0.8, 0), M, A, 'red', 'df1_dw')); Q.append(cylk(0.5, 3.2, (-6.1, 1.8, 0), M, A, 'dark', 'df1_drum', axis='z', seg=8))
    # ---- the doghouse: ribbed blue cladding, its window onto the rotary, the door, the roof, an A/C unit, the sign,
    # a dog bowl outside (no dogs)
    hx0, hx1, hz0, hz1, hh = 5.5, 9.7, 5.6, 9.7, 2.8
    o = box((hx1 - hx0, hh, hz1 - hz0), ((hx0 + hx1) / 2, hh / 2, (hz0 + hz1) / 2), M, bev=0.04, name='df_dog'); uv_trim(o, A, 'blueribs', upm=0.5, grain='y'); P.append(o)
    P.append(boxk((hx1 - hx0 + 0.2, 0.12, hz1 - hz0 + 0.2), ((hx0 + hx1) / 2, hh + 0.06, (hz0 + hz1) / 2), M, A, 'white', 'df_dogroof', bev=0.02))
    gl = mat('df_glass', 0x9fd0ea, rough=0.06, metal=0.1, alpha=0.5)
    o = box((0.03, 1.0, 2.9), (hx0 - 0.03, 1.7, 7.65), gl, name='df_window'); uv_fit(o, A, 'glass'); P.append(o)
    P.append(boxk((0.02, 0.98, 2.88), (hx0 + 0.005, 1.7, 7.65), M, A, 'dark', 'df_inside'))  # (the cabin's dark inside, behind the glass)
    for z in (6.17, 9.13): P.append(boxk((0.1, 1.12, 0.06), (hx0 - 0.03, 1.7, z), M, A, 'white', 'df_wframe'))
    for y in (1.17, 2.23): P.append(boxk((0.1, 0.06, 2.9), (hx0 - 0.03, y, 7.65), M, A, 'white', 'df_wframe'))
    P.append(boxk((0.9, 2.0, 0.04), (8.6, 1.0, hz1 + 0.02), M, A, 'white', 'df_door', bev=0.01))
    P.append(cylk(0.035, 0.12, (8.3, 1.0, hz1 + 0.08), M, A, 'galv', 'df_handle', axis='z', seg=6))
    P.append(boxk((1.1, 0.6, 0.7), (8.4, hh + 0.42, 7.0), M, A, 'galv', 'df_ac', bev=0.04))
    P.append(cylk(0.25, 0.04, (8.4, hh + 0.74, 7.0), M, A, 'dark', 'df_acfan', seg=12))
    P.append(boxk((1.6, 0.4, 0.03), (6.6, 2.35, hz1 + 0.016), M, A, 'dog', 'df_dogsign'))
    P.append(lathe([(0.0, 0.0), (0.14, 0.0), (0.18, 0.08), (0.15, 0.08), (0.12, 0.03), (0.0, 0.03)], (7.4, 0, hz1 + 0.4), M, seg=12, axis='y', name='df_bowl')); uv_fit(P[-1], A, 'pink')
    Q.append(boxk((hx1 - hx0, hh + 0.12, hz1 - hz0), ((hx0 + hx1) / 2, (hh + 0.12) / 2, (hz0 + hz1) / 2), M, A, 'blue', 'df1_dog'))
    return finish(P, Q, A, floor_boxes(), [((-6.1, 1.5, 0), (1, 0.5, 0.7), 4.5), ((7.6, 1.5, 7.6), (-1, 0.3, 0.6), 6.0), ((0, 0.1, 0), (0.6, 1, 0.6), 3.0)])


if __name__ == '__main__':
    for fid, fn in (('p_substructure', build_substructure), ('p_drillfloor', build_drillfloor)):
        if ONLY and fid[2:] not in ONLY: continue
        run_prop(fid, fn)
