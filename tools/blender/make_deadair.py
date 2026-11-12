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
from make_market import Atlas, paint_noise, paint_rope, uv_trim, uv_fit, run_prop, tnoise, box_between
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
DA = dict(plinth=2, top=70, deck=50, deckW=2.2, anchors=[80, 200, 320], anchorR=18, anchorW=0.9, anchorH=0.9, shack=[-5.7, -12.4, 2.3, -7.4], shackH=3.6)
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
    A = Atlas('da_atlas', 128, 128)
    A.band('ribs', 16, lambda px: _ribs(px, 0x74e8b8))
    A.band('grate', 16, _grate)
    A.cell('sign', 128, 32, paint_text(['DEAD AIR  0.0 FM', 'BROADCASTING', 'NOTHING, LOUDLY'], 0x1a1220, 0xffe14d, 31, border=0xff4fd8))
    A.cell('onair', 32, 12, paint_text(['ON AIR'], 0xd8202a, 0xffffff, 32))
    A.cell('keep', 48, 16, paint_text(['KEEP OUT', 'HIGH RF'], 0xffe14d, 0x1a1a1a, 33, border=0x1a1a1a))
    A.cell('hazard', 32, 8, paint_hazard(0xffe14d, 0x1a1a1a, 8))
    for k, c, v, sp in (('orange', 0xff5a1f, 0.05, None), ('white', 0xf4f2ee, 0.04, None), ('concrete', 0xc8c2b6, 0.1, 0x8a8478),
                        ('galv', 0x9aa4ae, 0.08, None), ('porcelain', 0x8a3a22, 0.06, None), ('coax', 0x1c1c20, 0.08, None),
                        ('door', 0x2a8ad8, 0.06, None), ('trim', 0xffffff, 0.03, None), ('dish', 0xeceff2, 0.03, None),
                        ('rust', 0x9a5230, 0.12, 0x5a2a14), ('rubber', 0x2a2a2e, 0.05, None), ('brass', 0xe8b438, 0.06, None)):
        A.swatch(k, c, v, 40 + len(A.r), w=8, h=8, speck=sp, p=0.08 if sp else 0.0)
    return A


def _ribs(px, col):  # corrugated metal: vertical ribs along u (tiles), light and shade
    h, w = px.shape[:2]
    xs = np.arange(w)
    s = 0.86 + 0.16 * np.cos(xs / w * TAU * 8)
    px[:] = hexrgb(col)[None, None] * s[None, :, None] * (0.94 + 0.08 * np.random.default_rng(3).random((h, w, 1)))
    px[-2:] *= 0.7  # grime at the bottom


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
    P, Q = [], []
    top = DA['top']
    # ---- the pier, the base insulator, the base pyramid
    P.append(boxk((2 * DA['plinth'], INS0, 2 * DA['plinth']), (0, INS0 / 2, 0), M, A, 'concrete', 'da_pier', bev=0.04))
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
        P.append(boxk((2 * DA['anchorW'], DA['anchorH'], 2 * DA['anchorW']), (ax, DA['anchorH'] / 2, az), M, A, 'concrete', 'da_anchor', bev=0.05))
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
    # ---- the transmitter shack: corrugated walls (mint), white trim, a door toward the mast, ON AIR, the big sign
    sx0, sz0, sx1, sz1 = DA['shack']; H = DA['shackH']
    cxs, czs, ws, ds = (sx0 + sx1) / 2, (sz0 + sz1) / 2, sx1 - sx0, sz1 - sz0
    walls = box((ws - 0.06, H - 0.3, ds - 0.06), (cxs, (H - 0.3) / 2 + 0.03, czs), M, name='da_walls')
    uv_trim(walls, A, 'ribs', upm=0.6, grain='x', sel=lambda p, Pp: abs(MK._gn(p.normal).y) < 0.5)
    uv_fit(walls, A, 'trim', sel=lambda p, Pp: abs(MK._gn(p.normal).y) >= 0.5); P.append(walls)
    roof = box((ws + 0.3, 0.3, ds + 0.3), (cxs, H - 0.15, czs), M, bev=0.03, name='da_roof'); uv_fit(roof, A, 'trim'); P.append(roof)
    P.append(boxk((ws + 0.02, 0.16, ds + 0.02), (cxs, 0.08, czs), M, A, 'concrete', 'da_slab'))
    for sxx in (sx0, sx1):  # corner trims
        for szz in (sz0, sz1):
            P.append(boxk((0.12, H - 0.46, 0.12), (sxx + (0.03 if sxx == sx0 else -0.03), 0.16 + (H - 0.46) / 2, szz + (0.03 if szz == sz0 else -0.03)), M, A, 'trim', 'da_corner'))
    Zf = sz1 - 0.03  # the south wall's face
    P.append(boxk((1.1, 2.15, 0.05), (sx1 - 1.6, 1.24, Zf + 0.02), M, A, 'door', 'da_door'))
    P.append(boxk((1.3, 2.3, 0.04), (sx1 - 1.6, 1.22, Zf + 0.01), M, A, 'trim', 'da_doorframe'))
    P.append(boxk((0.06, 0.16, 0.06), (sx1 - 2.0, 1.15, Zf + 0.06), M, A, 'brass', 'da_knob'))
    P.append(boxk((0.9, 0.34, 0.06), (sx1 - 1.6, 2.6, Zf + 0.02), M, A, 'onair', 'da_onair'))
    o = ball(0.09, (sx1 - 1.0, 2.6, Zf + 0.06), GL, seg=8, rings=5, name='da_onlamp'); uv_fit(o, A, 'white'); P.append(o)
    sg = box((4.4, 1.1, 0.06), (cxs - 1.1, 1.85, Zf + 0.02), M, name='da_sign')
    uv_fit(sg, A, 'sign', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5); uv_fit(sg, A, 'trim', sel=lambda p, Pp: MK._gn(p.normal).z <= 0.5); P.append(sg)
    # the AC unit through the west wall, a vent hood, a satellite dish on the roof, the ice bridge to the mast
    P.append(boxk((0.12, 0.6, 0.8), (sx0 - 0.02, 2.2, czs), M, A, 'galv', 'da_ac'))
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
    for b in range(BANDS + 1):
        y = M0 + b * (top - M0) / BANDS
        for k in range(3):
            a, c = leg_xz(k), leg_xz((k + 1) % 3)
            Q.append(rodk((a[0], y, a[1]), (c[0], y, c[1]), 0.1, M, A, band_key(min(y, top - 1)), 'da1_h', seg=3))
    Q.append(boxk((2 * DA['plinth'], 1.6, 2 * DA['plinth']), (0, 0.8, 0), M, A, 'concrete', 'da1_pier'))  # (its top inside the insulator)
    Q.append(boxk((2 * W, 0.3, 2 * W), (0, D0 + 0.15, 0), M, A, 'galv', 'da1_deck'))
    Q.append(boxk((ws, H, ds), (cxs, H / 2, czs), M, A, 'white', 'da1_shack'))
    Q.append(boxk((2 * RC + 0.2, 0.2, 2 * RC + 0.2), (0, top + 0.1, 0), M, A, 'galv', 'da1_cap'))
    o = ball(0.6, (0, top + 0.7, 0), GL, seg=6, rings=4, name='da1_beacon'); uv_fit(o, A, 'white'); Q.append(o)
    Q.append(boxk((0.6, M0 - 1.5, 0.6), (0, 1.5 + (M0 - 1.5) / 2, 0), M, A, 'porcelain', 'da1_ins'))  # (the insulator: pier to legs)
    Q.append(boxk((0.6, 0.1, -RC - DA['shack'][3] + 0.2), (DA['shack'][2] - 0.4, 2.55, (DA['shack'][3] - RC) / 2), M, A, 'galv', 'da1_bridge'))
    for a in DA['anchors']:
        ax, az = math.cos(math.radians(a)) * DA['anchorR'], math.sin(math.radians(a)) * DA['anchorR']
        Q.append(boxk((2 * DA['anchorW'], DA['anchorH'], 2 * DA['anchorW']), (ax, DA['anchorH'] / 2, az), M, A, 'concrete', 'da1_anchor'))
        Q.append(rodk((ax, DA['anchorH'], az), (math.cos(math.radians(a)) * RC, GUYH[-1], math.sin(math.radians(a)) * RC), 0.05, M, A, 'galv', 'da1_guy', seg=3))
    # meta.box = the box version's extent (shared/battleisland.js deadAir(), the same numbers)
    xs = [-DA['plinth'], DA['plinth'], DA['shack'][0], DA['shack'][2]]; zs = [-DA['plinth'], DA['plinth'], DA['shack'][1], DA['shack'][3]]
    for a in DA['anchors']:
        ax, az = math.cos(math.radians(a)) * DA['anchorR'], math.sin(math.radians(a)) * DA['anchorR']
        xs += [ax - DA['anchorW'], ax + DA['anchorW']]; zs += [az - DA['anchorW'], az + DA['anchorW']]
    lo, hi = (min(xs), 0.0, min(zs)), (max(xs), float(top), max(zs))
    return dict(lod0=P, lod1=Q, box=(lo, hi), ao=0.9, lod=90, meta={'kind': 'prop'},
                focus=[((0, 2.0, 0), (0.7, 0.3, 1.0), 6.0), ((0, 60, 0), (0.6, 0.1, 1.0), 9.0), ((-1.7, 2.0, -9.9), (0.2, 0.3, 1.0), 9.0), ((0, 50.5, 0), (1, 0.6, 1), 7.0)])


if __name__ == '__main__':
    run_prop('p_deadair', build_deadair)
