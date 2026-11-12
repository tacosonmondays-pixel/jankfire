# JANKFIRE Battle Island: DEAD AIR, the island's landmark (p_deadair). Built over its boxes in shared/battleisland.js
# deadAir() (the DA table: same numbers here), origin = the mast's foot, y 0 = the summit, +z = south (toward the harbour).
# A guyed AM/FM broadcast mast like the real ones: a concrete pier, the mast standing on a ribbed porcelain base insulator
# (AM masts are insulated from the ground), a triangular lattice (legs, horizontals, zig-zag bracing) in seven bands of
# international orange and white, red obstruction lights at three levels and a flashing beacon on top, a lightning rod,
# four side-mounted FM loop antenna bays, two microwave drum dishes, the work platform at 50 m, a climbing ladder, the coax
# up one leg, nine guy wires with egg insulators down to three anchor blocks (turnbuckles, anchor plates), the coax ice
# bridge from the transmitter shack, the shack itself (corrugated, mint, an ON AIR lamp, DEAD AIR 0.0 FM: BROADCASTING
# NOTHING, LOUDLY). Visual only: the mast column, the platform, the shack and the anchors are the map's boxes.
# run: blender52 -b --python tools/blender/make_deadair.py -- [--qa] [--no-sheet] [--no-export] [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, paint_noise, paint_rope, uv_trim, uv_fit, run_prop, tnoise, box_between, poly_obj, orient
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi


def paint_text(lines, bg, fg, seed=0, border=None, scale=1):
    """a painted board: rows of 5x7 text centred on a worn flat colour"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        px[:] = hexrgb(bg)[None, None] * (0.9 + 0.12 * r.random((h, w, 1)))
        if border is not None:
            px[:2] = hexrgb(border); px[-2:] = hexrgb(border); px[:, :2] = hexrgb(border); px[:, -2:] = hexrgb(border)
        lh = 8 * scale; y0 = (h - lh * len(lines)) // 2 + scale
        for i, s in enumerate(lines):
            tw = (len(s) * 6 - 1) * scale
            buf = np.zeros_like(px); text_px(buf, s, max(0, (w - tw) // 2), y0 + i * lh, scale, fg)
            m = buf.sum(axis=2) > 0
            px[m] = hexrgb(fg) * (0.85 + 0.2 * r.random((int(m.sum()), 1)))
        # flaking: the board shows through
        m = (tnoise(w, h, 10, 4, r) + 0.3 * r.random((h, w))) > 1.05
        px[m] *= 0.72
        px[::-1][:1] *= 0.7
    return d


def paint_hazard(a, b, period=8):
    def d(px):
        h, w = px.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        m = ((xx + yy) // (period // 2)) % 2 == 0
        px[:] = np.where(m[:, :, None], hexrgb(a)[None, None], hexrgb(b)[None, None])
        px[:] *= 0.92 + 0.1 * np.random.default_rng(7).random((h, w, 1))
    return d


# shared/battleisland.js DA
DA = dict(plinth=2, top=70, deck=50, deckW=2.2, rail=1.1, anchors=[80, 200, 320], anchorR=18, anchorW=0.9, anchorH=0.9,
          fence=3.4, fenceH=2.0, gate=1.1, board=[18, 19.6, 2.3],
          shack=[-5.7, -12.4, 2.3, -7.4], shackH=3.6, wallT=0.2, door=[0.1, 1.3, 2.3], win=[-10.6, -9.2, 1.1, 2.1],
          racks=[[-4.9, -4.1], [-3.9, -3.1]], rackD=0.7, rackH=2.1, desk=[1.3, -11.7, 2.1, -9.1, 0.78])


def da_boxes():
    """the map's boxes (shared/battleisland.js deadAir()), in the mast's frame: [(x0, y0, z0, x1, y1, z1)]"""
    out = []; L = lambda *b: out.append(b)
    L(-DA['plinth'], 0, -DA['plinth'], DA['plinth'], 0.8, DA['plinth']); L(-0.9, 0.8, -0.9, 0.9, DA['top'], 0.9)
    W, R, D = DA['deckW'], 0.06, DA['deck']
    L(-W, D, -W, W, D + 0.25, W)
    for s in (-1, 1):
        L(-W, D + 0.25, s * W - (R if s > 0 else 0), W, D + 0.25 + DA['rail'], s * W + (R if s < 0 else 0))
        L(s * W - (R if s > 0 else 0), D + 0.25, -W + R, s * W + (R if s < 0 else 0), D + 0.25 + DA['rail'], W - R)
    b0, b1, bw = DA['board']; L(-bw, b0, 0.9, bw, b1, 1.05)
    F, g, fh = DA['fence'], DA['gate'], DA['fenceH']
    L(-F, 0, -F - 0.05, F, fh, -F + 0.05); L(-F - 0.05, 0, -F, -F + 0.05, fh, F); L(F - 0.05, 0, -F, F + 0.05, fh, F)
    L(-F, 0, F - 0.05, -g, fh, F + 0.05); L(g, 0, F - 0.05, F, fh, F + 0.05)
    for a in DA['anchors']:
        x, z = math.cos(math.radians(a)) * DA['anchorR'], math.sin(math.radians(a)) * DA['anchorR']; w = DA['anchorW']
        L(x - w, 0, z - w, x + w, DA['anchorH'], z + w)
    x0, z0, x1, z1 = DA['shack']; H = DA['shackH']; t = DA['wallT']; d0, d1, dt = DA['door']; w0, w1, wy0, wy1 = DA['win']; top = H - 0.3
    L(x0 - 0.15, top, z0 - 0.15, x1 + 0.15, H, z1 + 0.15)
    return out


INS0, INS1 = 0.8, 1.6     # the base insulator: on the pier, under the mast
M0 = 2.7                   # where the triangle reaches full width (the base pyramid below)
SIDE = 1.5                 # the lattice's face width (inside the 1.8 m column)
RC = SIDE / math.sqrt(3)   # the legs' radius from the axis
LEGA = [90, 210, 330]      # the legs' angles (one leg toward +z: the face with the ladder looks north)
BANDS = 7
GUYH = [22.5, 44.5, 66.5]  # where the guys come off the mast
LIGHTS = [23.5, 46.5]


def leg_xz(k, r=RC):
    a = math.radians(LEGA[k]); return math.cos(a) * r, math.sin(a) * r


def band_key(y):
    i = min(BANDS - 1, max(0, int((y - M0) / ((DA['top'] - M0) / BANDS))))
    return 'orange' if i % 2 == 0 else 'white'


def atlas():
    A = Atlas('da_atlas', 128, 256)
    A.band('ribs', 16, lambda px: _ribs(px, 0x74e8b8))
    A.band('grate', 16, _grate)
    A.cell('sign', 128, 32, paint_text(['DEAD AIR  0.0 FM', 'BROADCASTING', 'NOTHING, LOUDLY'], 0x1a1220, 0xffe14d, 31, border=0xff4fd8))
    A.cell('onair', 32, 12, paint_text(['ON AIR'], 0xd8202a, 0xffffff, 32))
    A.cell('keep', 48, 16, paint_text(['KEEP OUT', 'HIGH RF'], 0xffe14d, 0x1a1a1a, 33, border=0x1a1a1a))
    A.cell('hazard', 32, 8, paint_hazard(0xffe14d, 0x1a1a1a, 8))
    A.cell('board', 64, 24, paint_text(['DEAD AIR', '0.0 FM'], 0xf4f2ee, 0xd8202a, 34, border=0xff5a1f, scale=1))
    A.cell('poster', 32, 24, paint_text(['NOBODY', 'IS', 'LISTENING'], 0xff4fd8, 0x1a1220, 35))
    A.cell('volt', 48, 16, paint_text(['DANGER', 'HIGH VOLTAGE'], 0xffffff, 0xd8202a, 36, border=0xd8202a))
    A.cell('rack', 16, 32, _rack)
    A.cell('mixer', 32, 16, _mixer)
    A.cell('tiles', 16, 16, _tiles)
    A.cell('streak', 16, 16, _streak)
    for k, c, v, sp in (('orange', 0xff5a1f, 0.05, None), ('white', 0xf4f2ee, 0.04, None), ('concrete', 0xc8c2b6, 0.1, 0x8a8478),
                        ('galv', 0x9aa4ae, 0.08, None), ('porcelain', 0x8a3a22, 0.06, None), ('coax', 0x1c1c20, 0.08, None),
                        ('door', 0x2a8ad8, 0.06, None), ('trim', 0xffffff, 0.03, None), ('dish', 0xeceff2, 0.03, None),
                        ('rust', 0x9a5230, 0.12, 0x5a2a14), ('rubber', 0x2a2a2e, 0.05, None), ('brass', 0xe8b438, 0.06, None),
                        ('cream', 0xf2e6c8, 0.05, 0xd8c8a0), ('cabinet', 0x3a3f4a, 0.06, None), ('wood', 0x9a6a3a, 0.1, 0x6a4422), ('red', 0xe02a2a, 0.05, None),
                        ('black', 0x18181c, 0.05, None), ('mug', 0x4fd8ff, 0.04, None), ('twig', 0x8a6a40, 0.2, 0x4a3420), ('egg', 0xf2ecd8, 0.03, None)):
        A.swatch(k, c, v, 40 + len(A.r), w=8, h=8, speck=sp, p=0.08 if sp else 0.0)
    return A


def _rack(px):  # a transmitter rack's front: meters, rows of buttons, a vent grille at the bottom
    h, w = px.shape[:2]; r = np.random.default_rng(9)
    px[:] = hexrgb(0x2e323c)
    for y in range(2, h - 8, 5):
        px[y:y + 3, 2:w - 2] = hexrgb(0x1a1c22)
        for x in range(3, w - 3, 3): px[y + 1, x] = hexrgb((0x7dff4f, 0xffe14d, 0xff3030)[int(r.integers(0, 3))])
    px[3:6, 4:12] = hexrgb(0xe8e2c8); px[4, 4 + int(r.integers(0, 8))] = hexrgb(0x1a1a1a)  # a meter, its needle
    px[h - 7:h - 1:2, 2:w - 2] = hexrgb(0x15171c)


def _mixer(px):  # the broadcast desk's mixer: fader channels, knobs, a VU strip
    h, w = px.shape[:2]; px[:] = hexrgb(0x2a2c32)
    for x in range(2, w - 2, 4):
        px[3:h - 2, x] = hexrgb(0x111114); px[6 + (x * 7) % 6, x - 1:x + 2] = hexrgb(0xf4f2ee)
        px[1, x] = hexrgb(0xff4fd8)
    px[1, w - 8:w - 2] = hexrgb(0x7dff4f)


def _tiles(px):  # vinyl floor tiles, scuffed
    h, w = px.shape[:2]; r = np.random.default_rng(12)
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx // 8) + (yy // 8)) % 2 == 0
    px[:] = np.where(m[:, :, None], hexrgb(0xe8e2d0)[None, None], hexrgb(0x8a8a96)[None, None]) * (0.92 + 0.1 * r.random((h, w, 1)))


def _streak(px):  # weathered concrete: rust run-off streaks from the steel above
    h, w = px.shape[:2]; r = np.random.default_rng(14)
    px[:] = hexrgb(0xc8c2b6) * (0.9 + 0.12 * r.random((h, w, 1)))
    for k in range(4):
        x = int(r.integers(0, w)); L = int(r.integers(5, h))
        px[:L, x] = px[:L, x] * 0.5 + hexrgb(0x9a5230) * 0.5


def _ribs(px, col):  # corrugated metal: vertical ribs along u (tiles), light and shade
    h, w = px.shape[:2]
    xs = np.arange(w)
    s = 0.86 + 0.16 * np.cos(xs / w * TAU * 8)
    px[:] = hexrgb(col)[None, None] * s[None, :, None] * (0.94 + 0.08 * np.random.default_rng(3).random((h, w, 1)))
    px[-2:] *= 0.7  # grime at the bottom
    r = np.random.default_rng(5)
    for k in range(6):  # rust where the paint chipped
        x, y = int(r.integers(0, w)), int(r.integers(0, h)); px[y:y + 2, x:x + 1] = hexrgb(0x9a5230)


def _grate(px):  # bar grating
    h, w = px.shape[:2]; px[:] = hexrgb(0x2a2c30)
    px[:, ::3] = hexrgb(0x9aa4ae); px[::4] = hexrgb(0x7a828c)


def rodk(p0, p1, r, M, A, key, name, seg=4):
    o = rod(p0, p1, r, M, seg=seg, name=name); uv_fit(o, A, key); return o


def boxk(size, pos, M, A, key, name, bev=0.0, rot=None):
    o = box(size, pos, M, bev=bev, rot=rot, name=name); uv_fit(o, A, key); return o


def build_deadair():
    A = atlas()
    M = mat('da_paint', 0xffffff, rough=0.32, metal=0.25, tex=A.image(), clearcoat=0.6)
    GL = mat('glow', 0xff2a2a, rough=0.5, emit=0xff2a2a, strength=3.0)
    GZ = mat('da_glass', 0xb8d8e8, rough=0.15, metal=0.2, alpha=0.38)  # window glass, chain-link mesh (see-through)
    P, Q = [], []
    top = DA['top']
    # ---- the pier, the base insulator, the base pyramid
    P.append(boxk((2 * DA['plinth'], INS0, 2 * DA['plinth']), (0, INS0 / 2, 0), M, A, 'streak', 'da_pier', bev=0.04))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.append(cyl(0.035, 0.12, (sx * 1.6, INS0 + 0.06, sz * 1.6), M, axis='y', seg=6, name='da_bolt')); uv_fit(P[-1], A, 'galv')
    prof = [(0.0, INS0), (0.42, INS0), (0.42, INS0 + 0.08), (0.3, INS0 + 0.1)]
    y = INS0 + 0.1
    for k in range(5):  # the ribbed porcelain: sheds stacked up
        prof += [(0.36, y + 0.04), (0.24, y + 0.1), (0.24, y + 0.12)]
        y += 0.12
    prof += [(0.3, INS1 - 0.02), (0.34, INS1), (0.0, INS1)]
    o = lathe(prof, (0, 0, 0), M, seg=16, axis='y', name='da_insulator'); uv_fit(o, A, 'porcelain'); P.append(o)
    o = cyl(0.36, 0.08, (0, INS1 + 0.04, 0), M, axis='y', seg=12, name='da_cap'); uv_fit(o, A, 'galv'); P.append(o)
    for k in range(3):  # the pyramid: the three legs come together on the insulator's cap
        x, z = leg_xz(k); P.append(rodk((x * 0.08, INS1 + 0.08, z * 0.08), (x, M0, z), 0.06, M, A, 'orange', 'da_pyr', seg=6))
    # ---- the lattice: legs, horizontals, zig-zags, painted by band
    step = 1.35
    lv = [M0 + i * step for i in range(int((top - 0.6 - M0) / step) + 1)]
    for k in range(3):
        x, z = leg_xz(k)
        for b in range(BANDS):  # each leg in seven pieces (one per band: its own colour)
            y0 = M0 + b * (top - M0) / BANDS; y1 = M0 + (b + 1) * (top - M0) / BANDS
            P.append(rodk((x, y0, z), (x, y1, z), 0.085, M, A, band_key((y0 + y1) / 2), 'da_leg', seg=6))
    for i, y in enumerate(lv):
        for k in range(3):
            a = leg_xz(k); b = leg_xz((k + 1) % 3)
            P.append(rodk((a[0], y, a[1]), (b[0], y, b[1]), 0.04, M, A, band_key(y), 'da_h'))
            if i + 1 < len(lv):
                y1 = lv[i + 1]
                p0, p1 = (a, b) if i % 2 == 0 else (b, a)
                P.append(rodk((p0[0], y, p0[1]), (p1[0], y1, p1[1]), 0.032, M, A, band_key((y + y1) / 2), 'da_d'))
    # the ladder up the north face (between legs 1 and 2: the face toward -z), the coax up leg 0
    a, b = leg_xz(1), leg_xz(2)
    fx, fz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    for s in (-0.22, 0.22):
        P.append(rodk((fx + s, M0, fz - 0.05), (fx + s, DA['deck'], fz - 0.05), 0.018, M, A, 'galv', 'da_lrail'))
    for i in range(int((DA['deck'] - M0) / 0.45)):
        y = M0 + 0.2 + i * 0.45
        P.append(rodk((fx - 0.22, y, fz - 0.05), (fx + 0.22, y, fz - 0.05), 0.012, M, A, 'galv', 'da_rung'))
    x0, z0 = leg_xz(0, RC + 0.12)
    P.append(rodk((x0, 2.4, z0), (x0, 64, z0), 0.06, M, A, 'coax', 'da_coax', seg=6))
    for y in range(4, 64, 6):
        P.append(boxk((0.16, 0.04, 0.16), (x0 * 0.96, y, z0 * 0.96), M, A, 'galv', 'da_hanger'))
    # ---- the work platform at 50 m: frame, bar grating, a hazard kick plate, a hole for the mast
    D0, W = DA['deck'], DA['deckW']
    for sz in (-1, 1):
        P.append(boxk((2 * W, 0.12, 0.1), (0, D0 + 0.13, sz * (W - 0.05)), M, A, 'galv', 'da_frame'))
        P.append(boxk((0.1, 0.12, 2 * W - 0.2), (sz * (W - 0.05), D0 + 0.13, 0), M, A, 'galv', 'da_frame'))  # (butting between the others)
    for (cx, cz, w, d) in ((0, -(W + 1.0) / 2, 2 * W - 0.2, W - 1.1), (0, (W + 1.0) / 2, 2 * W - 0.2, W - 1.1), (-(W + 1.0) / 2, 0, W - 1.1, 1.8), ((W + 1.0) / 2, 0, W - 1.1, 1.8)):
        o = box((w, 0.06, d), (cx, D0 + 0.22, cz), M, name='da_grate'); uv_trim(o, A, 'grate', upm=1.2, grain='x'); P.append(o)
    for sz in (-1, 1):
        P.append(boxk((2 * W, 0.12, 0.03), (0, D0 + 0.31, sz * (W - 0.015)), M, A, 'hazard', 'da_kick'))  # (the long ones; the short ones sit between)
        P.append(boxk((0.03, 0.12, 2 * W - 0.06), (sz * (W - 0.015), D0 + 0.31, 0), M, A, 'hazard', 'da_kick'))
    for k in range(3):  # knee braces from the legs out under the frame
        x, z = leg_xz(k); P.append(rodk((x, D0 - 1.6, z), (x * 1.9, D0 + 0.02, z * 1.9), 0.04, M, A, 'galv', 'da_knee', seg=6))
    # the railing round the platform (its boxes are solid panels: posts, two rails and a mesh infill, so it reads solid)
    RH = D0 + 0.25 + DA['rail']
    seen = set()
    for sz in (-1, 1):
        for along in ('x', 'z'):
            for k in range(5):
                t = -W + 0.03 + k * (2 * W - 0.06) / 4
                pos = (t, (D0 + 0.37 + RH) / 2, sz * (W - 0.03)) if along == 'x' else (sz * (W - 0.03), (D0 + 0.37 + RH) / 2, t)
                key = (round(pos[0], 2), round(pos[2], 2))
                if key in seen: continue  # (a corner post: once)
                seen.add(key); P.append(boxk((0.05, DA['rail'] - 0.12, 0.05), pos, M, A, 'galv', 'da_rpost'))
            for y in (RH - 0.03, D0 + 0.25 + DA['rail'] * 0.5):
                P.append(boxk((2 * W - 0.1, 0.05, 0.04) if along == 'x' else (0.04, 0.05, 2 * W - 0.1), (0, y, sz * (W - 0.03)) if along == 'x' else (sz * (W - 0.03), y, 0), M, A, 'orange' if y > RH - 0.1 else 'galv', 'da_rrail'))
            o = box((2 * W - 0.12, DA['rail'] - 0.12, 0.01) if along == 'x' else (0.01, DA['rail'] - 0.12, 2 * W - 0.12), (0, D0 + 0.31 + (DA['rail'] - 0.12) / 2, sz * (W - 0.03)) if along == 'x' else (sz * (W - 0.03), D0 + 0.31 + (DA['rail'] - 0.12) / 2, 0), GZ, name='da_rmesh')
            uv_fit(o, A, 'white'); P.append(o)
    # a seagull's nest in the platform's corner (an egg in it: somebody's broadcasting)
    nest = lathe([(0.0, 0.0), (0.32, 0.02), (0.36, 0.12), (0.28, 0.16), (0.22, 0.08), (0.0, 0.06)], (W - 0.5, D0 + 0.25, -W + 0.5), M, seg=10, axis='y', name='da_nest'); uv_fit(nest, A, 'twig'); P.append(nest)
    o = ball(0.07, (W - 0.48, D0 + 0.37, -W + 0.5), M, scale=(1, 1.3, 1), seg=8, rings=5, name='da_eggshell'); uv_fit(o, A, 'egg'); P.append(o)
    # the DEAD AIR board on the south face (18 m up: the summit's name, readable from the harbour)
    b0, b1, bw = DA['board']
    bd = box((2 * bw, b1 - b0, 0.15), (0, (b0 + b1) / 2, 0.975), M, bev=0.02, name='da_board')
    uv_fit(bd, A, 'board', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5); uv_fit(bd, A, 'orange', sel=lambda p, Pp: MK._gn(p.normal).z <= 0.5); P.append(bd)
    for k in (1, 2):  # brackets from the board back to the legs
        for y in (b0 + 0.3, b1 - 0.3):
            x, z = leg_xz(0)
            P.append(rodk((x + (0.6 if k == 1 else -0.6), y, 0.95), (x * 0.3, y, z), 0.04, M, A, 'galv', 'da_bbracket', seg=6))
    # ---- the fence round the foot: galvanised posts, top rail, chain-link (see-through), barbed wire, the gate swung open
    F, g, fh = DA['fence'], DA['gate'], DA['fenceH']
    runs = [((-F, -F), (F, -F)), ((-F, -F), (-F, F)), ((F, -F), (F, F)), ((-F, F), (-g, F)), ((g, F), (F, F))]
    fseen = set()
    for (ax, az), (bx, bz) in runs:
        L = math.hypot(bx - ax, bz - az); n = max(1, round(L / 1.7))
        for k in range(n + 1):
            x, z = ax + (bx - ax) * k / n, az + (bz - az) * k / n
            if (round(x, 2), round(z, 2)) in fseen: continue  # (corner posts: once)
            fseen.add((round(x, 2), round(z, 2))); P.append(rodk((x, 0, z), (x, fh + 0.35, z), 0.04, M, A, 'galv', 'da_fpost', seg=6))
        P.append(rodk((ax, fh - 0.04, az), (bx, fh - 0.04, bz), 0.025, M, A, 'galv', 'da_frail', seg=6))
        for h in (fh + 0.15, fh + 0.3):
            P.append(rodk((ax, h, az), (bx, h, bz), 0.008, M, A, 'galv', 'da_barb', seg=3))
        cx_, cz_ = (ax + bx) / 2, (az + bz) / 2
        o = box((L, fh - 0.14, 0.012) if az == bz else (0.012, fh - 0.14, L), (cx_, (fh - 0.14) / 2 + 0.06, cz_), GZ, name='da_mesh'); uv_fit(o, A, 'white'); P.append(o)
    for sx in (-1, 1):  # the gate leaves, swung open outward
        hx = sx * g
        P.append(rodk((hx, 0.05, F), (hx + sx * 0.05, 0.05, F + 1.0), 0.02, M, A, 'galv', 'da_gate'))
        P.append(rodk((hx, fh - 0.1, F), (hx + sx * 0.05, fh - 0.1, F + 1.0), 0.02, M, A, 'galv', 'da_gate'))
        P.append(rodk((hx + sx * 0.05, 0.05, F + 1.0), (hx + sx * 0.05, fh - 0.1, F + 1.0), 0.02, M, A, 'galv', 'da_gate'))
        o = box((0.01, fh - 0.3, 0.95), (hx + sx * 0.025, fh / 2 - 0.02, F + 0.5), GZ, name='da_gatemesh'); uv_fit(o, A, 'white'); P.append(o)
    P.append(boxk((0.6, 0.4, 0.02), (-1.8, 1.4, F + 0.015), M, A, 'volt', 'da_volt'))  # (wired to the mesh)
    # ---- lights: red obstruction lamps on each leg at two levels, the beacon on top
    for y in LIGHTS:
        for k in range(3):
            x, z = leg_xz(k, RC + 0.1)
            P.append(boxk((0.1, 0.08, 0.1), (x, y - 0.12, z), M, A, 'galv', 'da_lampbase'))
            o = ball(0.11, (x, y - 0.03, z), GL, seg=8, rings=5, name='da_lamp'); uv_fit(o, A, 'white'); P.append(o)
    P.append(cyl(0.34, 0.2, (0, top + 0.1, 0), M, axis='y', seg=10, name='da_topcap')); uv_fit(P[-1], A, 'galv')
    o = lathe([(0.0, 0.0), (0.22, 0.0), (0.24, 0.16), (0.18, 0.42), (0.0, 0.5)], (0, top + 0.2, 0), GL, seg=10, axis='y', name='da_beacon'); uv_fit(o, A, 'white'); P.append(o)
    P.append(rodk((0.29, top + 0.18, 0), (0.29, top + 3.2, 0), 0.02, M, A, 'brass', 'da_rod'))  # lightning rod
    P.append(rodk((-0.25, top + 0.2, 0.1), (-0.25, top + 2.4, 0.1), 0.012, M, A, 'galv', 'da_whip'))
    # ---- the FM antenna: four bays of circular loops on arms off the south face, a feed pipe joining them
    sx, sz = leg_xz(0, RC)
    for i in range(4):
        y = 56 + i * 2.6
        out = V3((sx, 0, sz)).normalized()
        c = V3((sx, y, sz)) + out * 0.9
        P.append(rodk((sx, y, sz), tuple(c - out * 0.44), 0.03, M, A, 'galv', 'da_arm'))
        loop = [tuple(c + out * (math.cos(t) * 0.42) + V3((0, math.sin(t) * 0.42, 0))) for t in [j * TAU / 14 for j in range(15)]]  # (in the plane of the arm: the arm meets it)
        o = sweep(loop, 0.035, M, seg=6, name='da_loop', cap=False); uv_fit(o, A, 'brass'); P.append(o)
    c0 = V3((sx, 56, sz)) + V3((sx, 0, sz)).normalized() * 0.55
    P.append(rodk(tuple(c0), tuple(c0 + V3((0, 7.8, 0))), 0.04, M, A, 'galv', 'da_feed', seg=6))
    # ---- microwave drum dishes: one looking south (the harbour), one west (the farm)
    for y, ang in ((31, 90), (40, 180)):
        d = V3((math.cos(math.radians(ang)), 0, math.sin(math.radians(ang))))
        c = d * (RC + 0.9) + V3((0, y, 0))
        side = d.cross(V3((0, 1, 0))).normalized()
        P.append(rodk(tuple(c - d * 0.3 + side * 0.5), tuple(c - d * (0.9 + RC * 0.4) + side * 0.4), 0.035, M, A, 'galv', 'da_mount'))
        P.append(rodk(tuple(c - d * 0.3 - side * 0.5), tuple(c - d * (0.9 + RC * 0.4) - side * 0.4), 0.035, M, A, 'galv', 'da_mount'))
        drum = lathe([(0.0, -0.32), (0.86, -0.32), (0.92, -0.28), (0.92, 0.24), (0.98, 0.28), (0.98, 0.32), (0.0, 0.32)], (0, 0, 0), M, seg=20, axis='z', name='da_drum')
        uv_fit(drum, A, 'dish')
        R = V3((0, 0, -1)).rotation_difference(d).to_matrix().to_4x4()  # its face (local -z) looks out along d
        G = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0))).to_4x4()
        drum.data.transform(G @ R @ G.inverted()); drum.data.transform(Matrix.Translation(gv(*c)))
        P.append(drum)
    # ---- the guy wires: three heights to each of three anchors, egg insulators near the top, the anchor blocks
    for a in DA['anchors']:
        ax, az = math.cos(math.radians(a)) * DA['anchorR'], math.sin(math.radians(a)) * DA['anchorR']
        A0 = V3((ax, DA['anchorH'], az))
        P.append(boxk((2 * DA['anchorW'], DA['anchorH'], 2 * DA['anchorW']), (ax, DA['anchorH'] / 2, az), M, A, 'streak', 'da_anchor', bev=0.05))
        tow = V3((-ax, 0, -az)).normalized()
        P.append(boxk((0.5, 0.5, 0.06), tuple(A0 + V3((0, 0.2, 0)) + tow * 0.25), M, A, 'galv', 'da_plate', rot=(0, -math.radians(a) + math.pi / 2, 0)))
        for i, gh in enumerate(GUYH):
            x, z = leg_xz(DA['anchors'].index(a))  # (onto the leg nearest the anchor)
            T0 = V3((x, gh, z)); B0 = A0 + V3((0, 0.45, 0)) + tow * (0.15 + i * 0.12)
            d = (T0 - B0); L = d.length; d.normalize()
            ins = T0 - d * 3.0
            P.append(rodk(tuple(B0), tuple(B0 + d * 0.9), 0.04, M, A, 'brass', 'da_turnbuckle', seg=6))
            P.append(rodk(tuple(B0 + d * 0.85), tuple(ins + d * 0.06), 0.016, M, A, 'galv', 'da_guy'))
            o = ball(0.11, tuple(ins + d * 0.11), M, scale=(1, 1, 1), seg=8, rings=5, name='da_egg'); uv_fit(o, A, 'porcelain'); P.append(o)
            P.append(rodk(tuple(ins + d * 0.16), tuple(T0), 0.016, M, A, 'galv', 'da_guy'))
        kc = V3((ax, 0.5, az)) + tow * (DA['anchorW'] + 0.005)
        P.append(boxk((0.36, 0.28, 0.03), tuple(kc), M, A, 'keep', 'da_keep', rot=(0, -math.radians(a) + math.pi / 2, 0)))
    # ---- the transmitter shack: you can walk in. corrugated mint outside, cream inside, white trim, a door toward the mast
    # (swung open in against the east wall), a window west, the studio inside: two transmitter racks, the broadcast desk
    sx0, sz0, sx1, sz1 = DA['shack']; H = DA['shackH']; t = DA['wallT']; d0, d1, dt = DA['door']; w0, w1, wy0, wy1 = DA['win']; stop = H - 0.3  # (the walls' top: the mast's `top` stays the mast's)
    cxs, czs, ws, ds = (sx0 + sx1) / 2, (sz0 + sz1) / 2, sx1 - sx0, sz1 - sz0
    C = V3((cxs, 1.5, czs))
    def wall(x0, y0, z0, x1, y1, z1, name):  # outside faces ribbed mint, inside cream, the cut edges trim
        o = box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), M, name=name)
        Pp = MK._gp(o); cen = V3(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        def side(p):
            n = MK._gn(p.normal)
            if abs(n.y) > 0.5: return 'trim'
            fc = sum((Pp[k] for k in p.vertices), V3()) / len(p.vertices)
            dx, dz = fc.x - C.x, fc.z - C.z
            outward = n.x * dx + n.z * dz > 0
            thin = (abs(n.x) > 0.5 and x1 - x0 > 0.5) or (abs(n.z) > 0.5 and z1 - z0 > 0.5)  # (a jamb: the wall's cut edge)
            return 'trim' if thin else ('ribs' if outward else 'cream')
        for key in ('ribs', 'cream', 'trim'):
            sel = (lambda p, P_, key=key: side(p) == key)
            if key == 'ribs': uv_trim(o, A, 'ribs', upm=0.6, grain='y' if False else None, sel=sel)
            else: uv_fit(o, A, key, sel=sel)
        P.append(o); return o
    wall(sx0, 0.15, sz0, sx1, stop, sz0 + t, 'da_wn')
    wall(sx1 - t, 0.15, sz0 + t, sx1, stop, sz1 - t, 'da_we')
    wall(sx0, 0.15, sz1 - t, d0, stop, sz1, 'da_ws'); wall(d1, 0.15, sz1 - t, sx1, stop, sz1, 'da_ws'); wall(d0, dt, sz1 - t, d1, stop, sz1, 'da_wsl')
    wall(sx0, 0.15, sz0 + t, sx0 + t, stop, w0, 'da_ww'); wall(sx0, 0.15, w1, sx0 + t, stop, sz1 - t, 'da_ww'); wall(sx0, 0.15, w0, sx0 + t, wy0, w1, 'da_ww'); wall(sx0, wy1, w0, sx0 + t, stop, w1, 'da_ww')
    fl = box((ws, 0.15, ds), (cxs, 0.075, czs), M, name='da_floor')
    uv_fit(fl, A, 'streak', sel=lambda p, Pp: MK._gn(p.normal).y < 0.5); uv_trim(fl, A, 'tiles', upm=0.5, sel=lambda p, Pp: MK._gn(p.normal).y >= 0.5); P.append(fl)
    roof = box((ws + 0.3, 0.3, ds + 0.3), (cxs, H - 0.15, czs), M, bev=0.03, name='da_roof'); uv_fit(roof, A, 'trim'); P.append(roof)
    P.append(boxk((ws + 0.36, 0.08, 0.06), (cxs, H - 0.3, sz1 + 0.17), M, A, 'mug', 'da_fascia'))  # (a cyan fascia under the roof's south edge)
    for sxx in (sx0, sx1):  # corner trims
        for szz in (sz0, sz1):
            P.append(boxk((0.12, stop - 0.17, 0.12), (sxx + (0.05 if sxx == sx0 else -0.05), 0.16 + (stop - 0.17) / 2, szz + (0.05 if szz == sz0 else -0.05)), M, A, 'trim', 'da_corner'))
    # the door: a frame round the opening, the leaf swung open inward against the east side of the opening
    Zo = sz1  # the south wall's outer face
    for x in (d0 - 0.06, d1 + 0.06):
        P.append(boxk((0.12, dt - 0.15, 0.04), (x, 0.15 + (dt - 0.15) / 2, Zo + 0.02), M, A, 'trim', 'da_jamb'))
    P.append(boxk((d1 - d0 + 0.24, 0.12, 0.04), ((d0 + d1) / 2, dt + 0.06, Zo + 0.02), M, A, 'trim', 'da_head'))
    leaf = boxk((0.05, dt - 0.2, d1 - d0 - 0.06), (d1 - 0.05, 0.15 + (dt - 0.2) / 2 + 0.02, sz1 - t - (d1 - d0 - 0.06) / 2 + 0.005), M, A, 'door', 'da_door'); P.append(leaf)  # (its hinge edge against the wall)
    P.append(boxk((0.06, 0.16, 0.06), (d1 - 0.1, 1.1, sz1 - t - (d1 - d0) + 0.16), M, A, 'brass', 'da_knob'))
    P.append(boxk((0.9, 0.34, 0.06), ((d0 + d1) / 2, dt + 0.36, Zo + 0.03), M, A, 'onair', 'da_onair'))
    o = ball(0.09, (d1 + 0.18, dt + 0.36, Zo + 0.05), GL, seg=8, rings=5, name='da_onlamp'); uv_fit(o, A, 'white'); P.append(o)
    sg = box((4.4, 1.1, 0.06), (cxs - 1.1, 1.85, Zo + 0.03), M, name='da_sign')
    uv_fit(sg, A, 'sign', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5); uv_fit(sg, A, 'trim', sel=lambda p, Pp: MK._gn(p.normal).z <= 0.5); P.append(sg)
    # the window (west): frame, glass, a sill
    xw = sx0 + t / 2
    for z in (w0, w1):
        P.append(boxk((t + 0.06, wy1 - wy0, 0.06), (xw, (wy0 + wy1) / 2, z + (0.03 if z == w0 else -0.03)), M, A, 'trim', 'da_wframe'))
    for y in (wy0, wy1):
        P.append(boxk((t + 0.06, 0.06, w1 - w0 - 0.12), (xw, y + (0.03 if y == wy0 else -0.03), (w0 + w1) / 2), M, A, 'trim', 'da_wframe'))  # (between the uprights)
    o = box((0.01, wy1 - wy0 - 0.1, w1 - w0 - 0.1), (xw, (wy0 + wy1) / 2, (w0 + w1) / 2), GZ, name='da_pane'); uv_fit(o, A, 'white'); P.append(o)
    P.append(boxk((0.16, 0.05, w1 - w0 + 0.2), (sx0 - 0.06, wy0 - 0.02, (w0 + w1) / 2), M, A, 'trim', 'da_sill'))
    # inside: the transmitter racks (meters, buttons, a glowing status strip), cable ladder over them
    for r0, r1 in DA['racks']:
        rz0 = sz0 + t; rz1 = rz0 + DA['rackD']; rc = ((r0 + r1) / 2, 0.15 + DA['rackH'] / 2, (rz0 + rz1) / 2)
        rk = box((r1 - r0, DA['rackH'], DA['rackD']), rc, M, bev=0.015, name='da_rack')
        uv_fit(rk, A, 'rack', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5); uv_fit(rk, A, 'cabinet', sel=lambda p, Pp: MK._gn(p.normal).z <= 0.5); P.append(rk)
        o = box((r1 - r0 - 0.2, 0.03, 0.02), ((r0 + r1) / 2, 0.15 + DA['rackH'] - 0.12, rz1 + 0.005), GL, name='da_rackled'); uv_fit(o, A, 'white'); P.append(o)
    P.append(boxk((2.2, 0.04, 0.3), (-4.0, stop - 0.3, sz0 + t + 0.15), M, A, 'galv', 'da_cladder'))
    # the broadcast desk (a solid console: its box), the mixer, the mic on its boom, headphones, a mug, records, a chair
    k0, kz0, k1, kz1, kh = DA['desk']
    dk = box((k1 - k0, kh - 0.15, kz1 - kz0), ((k0 + k1) / 2, 0.15 + (kh - 0.15) / 2, (kz0 + kz1) / 2), M, bev=0.02, name='da_desk')
    uv_fit(dk, A, 'wood', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5); uv_fit(dk, A, 'cabinet', sel=lambda p, Pp: MK._gn(p.normal).y <= 0.5); P.append(dk)
    mx = box((0.5, 0.05, 0.9), (k0 + 0.3, kh + 0.02, (kz0 + kz1) / 2), M, name='da_mixer'); uv_fit(mx, A, 'mixer', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5); uv_fit(mx, A, 'black', sel=lambda p, Pp: MK._gn(p.normal).y <= 0.5); P.append(mx)
    base = V3((k1 - 0.1, kh, kz0 + 0.4))
    P.append(rodk(tuple(base), tuple(base + V3((0, 0.35, 0))), 0.02, M, A, 'black', 'da_boom', seg=6))
    elbow = base + V3((-0.35, 0.55, 0.15)); P.append(rodk(tuple(base + V3((0, 0.35, 0))), tuple(elbow), 0.015, M, A, 'black', 'da_boom', seg=6))
    mic = base + V3((-0.6, 0.3, 0.25)); P.append(rodk(tuple(elbow), tuple(mic), 0.015, M, A, 'black', 'da_boom', seg=6))
    o = cyl(0.045, 0.18, tuple(mic + V3((0, -0.06, 0))), M, axis='y', seg=10, name='da_mic'); uv_fit(o, A, 'galv'); P.append(o)
    o = sweep([(k0 + 0.62, kh + 0.02, kz1 - 0.3), (k0 + 0.62, kh + 0.14, kz1 - 0.42), (k0 + 0.62, kh + 0.02, kz1 - 0.54)], 0.02, M, seg=6, name='da_phones'); uv_fit(o, A, 'black'); P.append(o)
    o = cyl(0.045, 0.1, (k0 + 0.65, kh + 0.05, kz0 + 0.25), M, axis='y', seg=10, name='da_mug'); uv_fit(o, A, 'mug'); P.append(o)
    for i in range(4):
        P.append(boxk((0.32, 0.012, 0.32), (k0 + 0.25, kh + 0.006 + i * 0.012, kz1 - 0.95), M, A, 'black', 'da_record'))
    cx_, cz_ = k0 - 0.55, (kz0 + kz1) / 2  # the chair (decor: small, no box)
    P.append(boxk((0.45, 0.07, 0.45), (cx_, 0.6, cz_), M, A, 'red', 'da_seat'))
    P.append(boxk((0.06, 0.55, 0.45), (cx_ - 0.24, 0.9, cz_), M, A, 'red', 'da_back'))
    P.append(rodk((cx_, 0.18, cz_), (cx_, 0.57, cz_), 0.03, M, A, 'galv', 'da_chairpost', seg=6))
    for k in range(5):
        a = TAU * k / 5; P.append(rodk((cx_, 0.18, cz_), (cx_ + math.cos(a) * 0.3, 0.17, cz_ + math.sin(a) * 0.3), 0.02, M, A, 'black', 'da_chairleg', seg=4))
    # the walls: NOBODY IS LISTENING, a clock, the fire extinguisher, the inside ON AIR lamp, a ceiling lamp
    P.append(boxk((0.7, 0.55, 0.02), (-1.6, 2.0, sz0 + t + 0.011), M, A, 'poster', 'da_poster'))
    o = cyl(0.17, 0.04, (0.2, 2.6, sz0 + t + 0.02), M, axis='z', seg=14, name='da_clock'); uv_fit(o, A, 'white'); P.append(o)
    P.append(boxk((0.012, 0.18, 0.012), (0.2, 2.66, sz0 + t + 0.045), M, A, 'black', 'da_hand'))
    o = cyl(0.08, 0.5, (sx0 + t + 0.075, 0.395, sz1 - t - 0.4), M, axis='y', seg=10, name='da_extinguisher'); uv_fit(o, A, 'red'); P.append(o)
    o = ball(0.07, (k1 - 0.05, 2.35, kz0 + 0.6), GL, seg=8, rings=5, name='da_onlamp2'); uv_fit(o, A, 'white'); P.append(o)
    o = box((0.9, 0.06, 0.2), (cxs, stop - 0.03, czs), GL, name='da_ceiling'); uv_fit(o, A, 'white'); P.append(o)
    # outside: the AC unit on the north wall, a vent hood, a satellite dish on the roof
    P.append(boxk((0.9, 0.6, 0.14), (cxs + 1.5, 2.2, sz0 - 0.07), M, A, 'galv', 'da_ac'))
    P.append(boxk((0.6, 0.3, 0.6), (sx0 + 1.2, H + 0.15, czs - 1.0), M, A, 'galv', 'da_vent'))
    dsh = lathe([(0.0, 0.0), (0.4, 0.06), (0.62, 0.2), (0.6, 0.22), (0.0, 0.05)], (0, 0, 0), M, seg=14, axis='z', name='da_sat'); uv_fit(dsh, A, 'dish')
    dsh.data.transform(Matrix.Rotation(math.radians(-35), 4, 'X')); dsh.data.transform(Matrix.Translation(gv(sx0 + 2.6, H + 0.9, czs + 0.6))); P.append(dsh)
    P.append(rodk((sx0 + 2.6, H - 0.02, czs + 0.6), (sx0 + 2.6, H + 0.97, czs + 0.6), 0.04, M, A, 'galv', 'da_satpole'))
    bz = sz1 + 0.6
    for z in (bz, bz + 2.4, bz + 4.6):  # ice bridge posts (out of the door's way, over head height)
        P.append(rodk((sx1 - 0.4, 0, z), (sx1 - 0.4, 2.53, z), 0.045, M, A, 'galv', 'da_post', seg=6))
        P.append(boxk((0.62, 0.06, 0.08), (sx1 - 0.4, 2.52, z), M, A, 'galv', 'da_postbar'))
    for s in (-0.25, 0.25):
        P.append(rodk((sx1 - 0.4 + s, 2.55, sz1 - 0.1), (sx1 - 0.4 + s * 0.2, 2.55, -RC - 0.1), 0.03, M, A, 'galv', 'da_tray'))
    for i in range(10):
        z = sz1 + i * (-RC - sz1) / 10
        P.append(boxk((0.55, 0.03, 0.05), (sx1 - 0.4, 2.53, z), M, A, 'galv', 'da_traybar'))
    P.append(rodk((sx1 - 0.4, 2.62, sz1 - 0.1), (sx1 - 0.4, 2.62, -RC - 0.05), 0.05, M, A, 'coax', 'da_coaxrun', seg=6))
    for p in P: lib.smooth(p, 35)
    # ---- lod1: three banded legs, a ring per band, the deck, the shack, the anchors, the guys as thin strips
    for k in range(3):
        x, z = leg_xz(k)
        for b in range(BANDS):
            y0 = M0 + b * (top - M0) / BANDS; y1 = y0 + (top - M0) / BANDS
            Q.append(boxk((0.28, y1 - y0, 0.28), (x, (y0 + y1) / 2, z), M, A, band_key((y0 + y1) / 2), 'da1_leg'))  # (fat: far away it's the island's landmark)
    for b in range(BANDS):  # a banded triangular shell between the legs (far away the lattice reads as a solid striped mast)
        y0 = M0 + b * (top - M0) / BANDS; y1 = y0 + (top - M0) / BANDS
        for k in range(3):
            a, c = leg_xz(k, RC * 0.96), leg_xz((k + 1) % 3, RC * 0.96)
            o = poly_obj([(a[0], y0, a[1]), (c[0], y0, c[1]), (c[0], y1, c[1]), (a[0], y1, a[1])], [(0, 1, 2, 3)], M, 'da1_face')
            orient(o, lambda cc: V3((cc.x, 0, cc.z))); uv_fit(o, A, band_key((y0 + y1) / 2)); Q.append(o)
    Q.append(boxk((2 * DA['plinth'], 1.6, 2 * DA['plinth']), (0, 0.8, 0), M, A, 'concrete', 'da1_pier'))  # (its top inside the insulator)
    Q.append(boxk((2 * W, 0.3, 2 * W), (0, D0 + 0.15, 0), M, A, 'galv', 'da1_deck'))
    Q.append(boxk((ws, H, ds), (cxs, H / 2, czs), M, A, 'mug', 'da1_shack'))
    Q.append(boxk((2 * bw, b1 - b0, 0.15), (0, (b0 + b1) / 2, 0.975), M, A, 'board', 'da1_board'))
    Q.append(boxk((2 * RC + 0.2, 0.2, 2 * RC + 0.2), (0, top + 0.1, 0), M, A, 'galv', 'da1_cap'))
    o = ball(0.6, (0, top + 0.7, 0), GL, seg=6, rings=4, name='da1_beacon'); uv_fit(o, A, 'white'); Q.append(o)
    Q.append(boxk((0.6, M0 - 1.5, 0.6), (0, 1.5 + (M0 - 1.5) / 2, 0), M, A, 'porcelain', 'da1_ins'))  # (the insulator: pier to legs)
    Q.append(boxk((0.6, 0.1, -RC - DA['shack'][3] + 0.2), (DA['shack'][2] - 0.4, 2.55, (DA['shack'][3] - RC) / 2), M, A, 'galv', 'da1_bridge'))
    for a in DA['anchors']:
        ax, az = math.cos(math.radians(a)) * DA['anchorR'], math.sin(math.radians(a)) * DA['anchorR']
        Q.append(boxk((2 * DA['anchorW'], DA['anchorH'], 2 * DA['anchorW']), (ax, DA['anchorH'] / 2, az), M, A, 'concrete', 'da1_anchor'))
        Q.append(rodk((ax, DA['anchorH'], az), (math.cos(math.radians(a)) * RC, GUYH[-1], math.sin(math.radians(a)) * RC), 0.05, M, A, 'galv', 'da1_guy', seg=3))
    # meta.box = the box version's extent (shared/battleisland.js deadAir(): da_boxes() mirrors it)
    bx = da_boxes(); lo = tuple(min(b[k] for b in bx) for k in range(3)); hi = tuple(max(b[k + 3] for b in bx) for k in range(3))
    return dict(lod0=P, lod1=Q, box=(lo, hi), ao=0.9, lod=90, meta={'kind': 'prop'},
                focus=[((0, 2.0, 0), (0.7, 0.3, 1.0), 6.0), ((0, 60, 0), (0.6, 0.1, 1.0), 9.0), ((-1.7, 2.0, -9.9), (0.2, 0.3, 1.0), 9.0), ((0, 50.5, 0), (1, 0.6, 1), 7.0)])


if __name__ == '__main__':
    run_prop('p_deadair', build_deadair)
