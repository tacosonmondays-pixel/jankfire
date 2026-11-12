# JANKFIRE Platform: the pedestal cranes (both rig maps), built over shared/map.js pedCrane()'s boxes (same numbers here),
# origin = the middle of the pedestal on the deck, the boom along +x. Two props from one script: p_pedcrane (the 34 m boom
# that rests on the compressor house, with its boom rest) and p_pedcrane_short (the 22 m one swung out over the boat).
# An offshore pedestal crane: a round pedestal on its bolted flange with a caged ladder up to the slew deck, the slew
# ring, the machinery house (ribbed white cladding, louvres, the exhaust, a beacon and horn) with the operator's cab on
# the boom side (wrap-round glass, a wiper, the seat and levers inside), the counterweight stacked at the back
# (DO NOT RIDE THE BOOM), the A-frame gantry with pendant wires down to the boom tip, a box-girder boom (you can walk on
# it: a grating strip on top, hazard stripes on its edges, SWL 25 T on its side) on its heel pins, the sheave head and
# the whip line down to a red hook block with its hook. Visual only: the pedestal, the deck, the house, the boom and
# the rest are the map's boxes.
# run: blender52 -b --python tools/blender/make_pedcrane.py -- [--only=pedcrane,pedcrane_short] [--qa] [--stats] [--no-sheet]
#      [--no-export] [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, uv_fit, uv_trim, run_prop, tnoise, box_between, poly_obj, orient, opt, ONLY
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi
Y = 9.0  # the slew deck (pedCrane's y)


def crane_boxes(L, rest):
    """pedCrane(B, D, 0, 0, true, L, { rest }) in its own frame"""
    out = []; A_ = lambda *b: out.append(b)
    A_(-1.3, 0, -1.3, 1.3, Y, 1.3)
    for k in range(1, 9): A_(1.3, k, -0.3, 1.36, k + 0.06, 0.3)
    A_(-2.2, Y, -2.2, 2.2, Y + 0.3, 2.2)
    A_(-1.6, Y + 0.3, -1.1, 0.4, Y + 2.6, 1.1); A_(0.4, Y + 1.3, -0.9, 0.46, Y + 2.3, 0.9)
    A_(-2.2, Y + 0.3, -1.9, -1.6, Y + 1.6, 1.9)
    A_(0.4, Y + 1.4, -0.7, L, Y + 2.6, 0.7)
    A_(L - 0.06, Y - 2.5, -0.03, L, Y + 1.4, 0.03); A_(L - 0.4, Y - 3.4, -0.35, L + 0.3, Y - 2.5, 0.35)
    if rest: A_(rest - 0.4, 5.0, -0.4, rest + 0.4, Y + 1.4, 0.4)
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


def _label(lines, bg, fg, seed, scale=1, border=None):
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        px[:] = hexrgb(bg) * (0.92 + 0.1 * r.random((h, w, 1)))
        if border is not None: px[:1] = px[-1:] = hexrgb(border); px[:, :1] = px[:, -1:] = hexrgb(border)
        y = (h - 8 * scale * len(lines)) // 2 + scale
        for s in lines:
            tw = (len(s) * 6 - 1) * scale; text_px(px, s, max(0, (w - tw) // 2), y, scale, fg); y += 8 * scale
    return d


def _ribs(px):  # the house's cladding: white trapezoidal sheet, its ribs along v
    h, w = px.shape[:2]; r = np.random.default_rng(51)
    s = 0.88 + 0.14 * np.cos(np.arange(w) / w * TAU * 8)
    px[:] = hexrgb(0xf4f2ee)[None, None] * s[None, :, None] * (0.95 + 0.06 * r.random((h, w, 1)))
    px[-2:] *= 0.75
    for k in range(5): x, y = int(r.integers(0, w)), int(r.integers(h // 2, h)); px[y:, x] = px[y:, x] * 0.7 + hexrgb(0x9a5a30) * 0.3


def _hazard(px):
    h, w = px.shape[:2]; yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx + yy) // 4) % 2 == 0
    px[:] = np.where(m[:, :, None], hexrgb(0xffd21a)[None, None], hexrgb(0x1a1a1a)[None, None])


def _boomtop(px):  # the boom's top: a grating strip down the middle, plate either side
    h, w = px.shape[:2]; px[:] = hexrgb(0xffcf1a) * 0.95
    a, b = h // 4, 3 * h // 4
    px[a:b] = hexrgb(0x2a2c30); px[a:b, ::3] = hexrgb(0x9aa4ae)
    px[a - 1] = px[b] = hexrgb(0x1a1a1a)


def _louvre(px):
    h, w = px.shape[:2]; px[:] = hexrgb(0x8a929c)
    px[::3] = hexrgb(0x3a3e44)


def atlas():
    A = Atlas('cr_atlas', 128, 192)
    A.band('yband', 16, _chipped(0xffcf1a, 61, rust=0x9a6a2a, p=0.02, streaks=5))
    A.band('ribs', 16, _ribs)
    A.band('boomtop', 16, _boomtop)
    A.band('hazard', 8, _hazard)
    A.cell('yellow', 32, 32, _chipped(0xffcf1a, 62, rust=0x9a6a2a, streaks=1))
    A.cell('red', 32, 32, _chipped(0xe8202a, 63))
    A.cell('white', 32, 32, _chipped(0xf4f2ee, 64, rust=0xb07a4a, streaks=2))
    A.cell('concrete', 32, 32, _chipped(0xb8b2a6, 65, rust=0x6a645a, streaks=2))
    A.cell('swl', 64, 12, _label(['SWL 25 T'], 0x1a1a1a, 0xffe14d, 66, scale=1))
    A.cell('ride', 64, 18, _label(['DO NOT RIDE', 'THE BOOM'], 0xffe14d, 0x1a1a1a, 67, border=0x1a1a1a))
    A.cell('glug', 64, 14, _label(['GLUG CRANE'], 0xff4fd8, 0xffffff, 68))
    A.cell('louvre', 16, 16, _louvre)
    for k, c, v, sp in (('galv', 0xa8b0ba, 0.06, None), ('dark', 0x2a2c32, 0.05, None), ('grate', 0x5a6068, 0.1, 0x2a2c30),
                        ('glass', 0x28384a, 0.04, None), ('rubber', 0x1c1c22, 0.05, None), ('seat', 0x2a6ad8, 0.05, None),
                        ('steel', 0x6a707a, 0.08, None), ('cyan', 0x4fd8ff, 0.03, None)):
        A.swatch(k, c, v, 120 + len(A.r), w=8, h=8, speck=sp, p=0.2 if sp else 0.0)
    return A


def rodk(p0, p1, r, M, A, key, name, seg=8):
    o = rod(p0, p1, r, M, seg=seg, name=name); uv_fit(o, A, key); return o


def boxk(size, pos, M, A, key, name, bev=0.0, rot=None):
    o = box(size, pos, M, bev=bev, rot=rot, name=name); uv_fit(o, A, key); return o


def cylk(r, L, pos, M, A, key, name, axis='y', seg=12, bev=0.0, r2=None):
    o = cyl(r, L, pos, M, axis=axis, seg=seg, name=name, bev=bev, r2=r2); uv_fit(o, A, key); return o


def build(L, rest):
    A = atlas()
    M = mat('cr_paint', 0xffffff, rough=0.28, metal=0.15, tex=A.image(), clearcoat=0.8)
    CH = mat('cr_chrome', 0xdfe3ea, rough=0.14, metal=0.95, clearcoat=0.3)
    GZ = mat('cr_glass', 0x9fd0ea, rough=0.06, metal=0.1, alpha=0.5)
    GL = mat('cr_glow', 0xffa020, rough=0.5, emit=0xffa020, strength=2.5)
    P, Q = [], []
    # ---- the pedestal: its flange bolted to the deck, the column, the slew ring and its gear
    P.append(cylk(1.55, 0.14, (0, 0.07, 0), M, A, 'yellow', 'cr_baseflange', seg=20))
    for k in range(12):
        a = TAU * k / 12; P.append(cylk(0.045, 0.1, (math.cos(a) * 1.42, 0.17, math.sin(a) * 1.42), M, A, 'galv', 'cr_bolt', seg=6))
    o = cyl(1.26, Y - 0.6, (0, 0.14 + (Y - 0.74) / 2, 0), M, axis='y', seg=20, name='cr_column', cap=False); uv_trim(o, A, 'yband', upm=0.4, grain='y'); P.append(o)
    P.append(cylk(1.45, 0.2, (0, Y - 0.5, 0), M, A, 'yellow', 'cr_topflange', seg=20))
    P.append(cylk(1.6, 0.3, (0, Y - 0.25, 0), M, A, 'dark', 'cr_slewring', seg=24))
    # the ladder up its +x side (the box rungs' side) and its cage, a hatch through the deck
    for z in (-0.25, 0.25): P.append(rodk((1.45, 0.2, z), (1.45, Y, z), 0.025, M, A, 'galv', 'cr_ladrail', seg=4))
    for k in range(1, 26): P.append(rodk((1.45, k * 0.34, -0.25), (1.45, k * 0.34, 0.25), 0.015, M, A, 'galv', 'cr_rung', seg=4))
    for k in range(1, 6): P.append(rodk((1.45, 0.4 + k * 1.4, -0.25), (1.27, 0.4 + k * 1.4, -0.25), 0.015, M, A, 'galv', 'cr_ladarm', seg=4))
    hoop = [(1.45, 0, -0.25), (1.75, 0, -0.42), (2.05, 0, -0.2), (2.05, 0, 0.2), (1.75, 0, 0.42), (1.45, 0, 0.25)]
    for k in range(2, 7):
        y = k * 1.3; P.append(sweep([(x, y, z) for x, _, z in hoop], [0.018] * 6, M, seg=4, name='cr_hoop')); uv_fit(P[-1], A, 'galv')
    for q in (1, 2, 3, 4): P.append(rodk((hoop[q][0], 2.6, hoop[q][2]), (hoop[q][0], Y - 0.3, hoop[q][2]), 0.015, M, A, 'galv', 'cr_cagebar', seg=4))
    # ---- the slew deck: grating, its edge plate, a hatch
    P.append(boxk((4.4, 0.24, 4.4), (0, Y + 0.12, 0), M, A, 'yellow', 'cr_deckframe', bev=0.02))
    P.append(boxk((4.3, 0.04, 4.3), (0, Y + 0.26, 0), M, A, 'grate', 'cr_deck'))
    P.append(boxk((0.8, 0.02, 0.8), (1.5, Y + 0.29, 0), M, A, 'hazard', 'cr_hatch'))
    Q.append(cylk(1.3, Y, (0, Y / 2, 0), M, A, 'yellow', 'cr1_column', seg=8)); Q.append(boxk((4.4, 0.3, 4.4), (0, Y + 0.15, 0), M, A, 'yellow', 'cr1_deck'))
    # ---- the machinery house: ribbed cladding, a roof with its overhang, louvres, the exhaust, a beacon, the horn
    hx0, hx1, hz, hy0, hy1 = -1.6, 0.4, 1.1, Y + 0.3, Y + 2.6
    o = box((hx1 - hx0, hy1 - hy0, 2 * hz), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 0), M, bev=0.03, name='cr_house'); uv_trim(o, A, 'ribs', upm=0.5, grain='y'); P.append(o)
    P.append(boxk((hx1 - hx0 + 0.2, 0.1, 2 * hz + 0.2), ((hx0 + hx1) / 2, hy1 + 0.05, 0), M, A, 'white', 'cr_roof', bev=0.02))
    for z in (-hz - 0.005, hz + 0.005):
        o = box((1.0, 0.7, 0.02), (-0.9, hy0 + 1.4, z), M, name='cr_louvre'); uv_fit(o, A, 'louvre'); P.append(o)
    P.append(boxk((1.6, 0.36, 0.02), (-0.6, hy0 + 0.45, -hz - 0.005), M, A, 'glug', 'cr_glug'))  # (on the louvre side, under the louvre)
    P.append(cylk(0.12, 1.15, (-1.2, hy1 + 0.625, -0.7), M, A, 'dark', 'cr_exhaust', seg=8))
    P.append(cylk(0.15, 0.08, (-1.2, hy1 + 1.22, -0.7), M, A, 'rubber', 'cr_exhaustcap', seg=8))
    P.append(cylk(0.1, 0.12, (-0.2, hy1 + 0.16, 0.7), M, A, 'dark', 'cr_beaconbase', seg=8))
    P.append(ball(0.12, (-0.2, hy1 + 0.3, 0.7), GL, seg=8, rings=5, name='cr_beacon'))
    P.append(cylk(0.08, 0.3, (0.2, hy1 + 0.18, -0.6), M, A, 'red', 'cr_horn', axis='x', seg=8, r2=0.14))
    Q.append(boxk((hx1 - hx0, hy1 - hy0 + 0.1, 2 * hz), ((hx0 + hx1) / 2, (hy0 + hy1 + 0.1) / 2, 0), M, A, 'white', 'cr1_house'))
    # the operator's cab: glazed on the +z side of the house at its front (the boom's heel is across the front), a
    # wiper, the seat and the levers inside
    wx0, wx1, cy0, cy1 = -0.55, 0.32, Y + 1.25, Y + 2.35
    o = box((wx1 - wx0, cy1 - cy0, 0.03), ((wx0 + wx1) / 2, (cy0 + cy1) / 2, hz + 0.02), GZ, name='cr_windscreen'); uv_fit(o, A, 'glass'); P.append(o)
    for x in (wx0 - 0.03, wx1 + 0.03): P.append(boxk((0.06, cy1 - cy0 + 0.1, 0.09), (x, (cy0 + cy1) / 2, hz + 0.02), M, A, 'white', 'cr_pillar'))
    P.append(boxk(((wx1 - wx0) - 0.005, 0.06, 0.09), ((wx0 + wx1) / 2, cy1 + 0.03, hz + 0.02), M, A, 'white', 'cr_sill')); P.append(boxk(((wx1 - wx0) - 0.005, 0.06, 0.09), ((wx0 + wx1) / 2, cy0 - 0.03, hz + 0.02), M, A, 'white', 'cr_sill'))
    P.append(rodk((wx0 + 0.3, cy0 + 0.05, hz + 0.06), (wx0 + 0.6, cy0 + 0.75, hz + 0.06), 0.012, M, A, 'dark', 'cr_wiper', seg=4))
    P.append(boxk((0.5, 0.08, 0.5), (-0.1, Y + 0.95, hz - 0.45), M, A, 'seat', 'cr_seat')); P.append(boxk((0.5, 0.6, 0.08), (-0.1, Y + 1.25, hz - 0.72), M, A, 'seat', 'cr_seatback'))
    for x in (-0.45, 0.25): P.append(rodk((x, Y + 0.27, hz - 0.3), (x, Y + 1.25, hz - 0.2), 0.015, M, A, 'dark', 'cr_lever', seg=4))
    # ---- the counterweight: stacked concrete slabs in a yellow frame, the warning on its back
    for k in range(3):
        P.append(boxk((0.6, 0.42, 3.76), (-1.895, Y + 0.49 + k * 0.42, 0), M, A, 'concrete', 'cr_cwslab', bev=0.02))
    for z in (-1.91, 1.91): P.append(boxk((0.64, 1.3, 0.06), (-1.9, Y + 0.95, z), M, A, 'yellow', 'cr_cwframe'))
    P.append(boxk((0.02, 0.5, 1.6), (-2.2, Y + 0.95, 0), M, A, 'ride', 'cr_ride'))
    Q.append(boxk((0.6, 1.3, 3.8), (-1.9, Y + 0.95, 0), M, A, 'concrete', 'cr1_cw'))
    # ---- the A-frame gantry on the house, the pendant wires to the boom tip
    gx, gy = -1.0, Y + 5.2
    for z in (-0.9, 0.9):
        P.append(rodk((-1.5, hy1 + 0.1, z), (gx, gy, z * 0.3), 0.08, M, A, 'yellow', 'cr_gantry', seg=6))
        P.append(rodk((0.2, hy1 + 0.1, z), (gx, gy, z * 0.3), 0.08, M, A, 'yellow', 'cr_gantry', seg=6))
    P.append(rodk((gx, gy, -0.3), (gx, gy, 0.3), 0.1, M, A, 'yellow', 'cr_gantrytop', seg=8))
    tip = V3((L - 0.25, Y + 2.6, 0))
    for z in (-0.22, 0.22): P.append(rodk((gx, gy, z), (tip.x, tip.y + 0.05, z * 2), 0.022, M, A, 'dark', 'cr_pendant', seg=4))
    P.append(rodk((gx, gy, 0.0), (0.0, Y + 2.65, 0.0), 0.025, M, A, 'dark', 'cr_luffwire', seg=4))  # (the luffing wire back to its winch)
    Q.append(rodk((gx, gy, 0), (tip.x, tip.y, 0), 0.06, M, A, 'dark', 'cr1_pendant', seg=3)); Q.append(rodk((-0.6, hy1, 0), (gx, gy, 0), 0.12, M, A, 'yellow', 'cr1_gantry', seg=4))
    # ---- the boom: a box girder (its box: walk on it), plated, stiffeners down its sides, a grating strip on top,
    # hazard stripes along the top edges, SWL 25 T, the heel pins, the sheave head at the tip
    by0, by1, bz = Y + 1.4, Y + 2.6, 0.7
    o = box((L - 0.4, by1 - by0, 2 * bz), ((0.4 + L) / 2, (by0 + by1) / 2, 0), M, bev=0.04, name='cr_boom')
    uv_trim(o, A, 'yband', upm=0.3, grain='x', sel=lambda p, Pp: abs(MK._gn(p.normal).y) < 0.5)
    uv_trim(o, A, 'boomtop', upm=0.5, grain='x', sel=lambda p, Pp: MK._gn(p.normal).y >= 0.5)
    uv_fit(o, A, 'yellow', sel=lambda p, Pp: MK._gn(p.normal).y <= -0.5); P.append(o)
    x = 2.0
    while x < L - 0.8:  # side stiffeners
        for z in (-bz - 0.015, bz + 0.015): P.append(boxk((0.08, by1 - by0 - 0.12, 0.03), (x, (by0 + by1) / 2, z), M, A, 'yellow', 'cr_stiff'))
        x += 2.4
    for z in (-bz + 0.06, bz - 0.06): P.append(boxk((L - 1.0, 0.012, 0.1), ((0.4 + L) / 2 + 0.2, by1 + 0.006, z), M, A, 'hazard', 'cr_edge'))
    for s in (-1, 1): P.append(boxk((3.0, 0.4, 0.02), (L * 0.45, (by0 + by1) / 2, s * (bz + 0.03)), M, A, 'swl', 'cr_swl'))
    for z in (-0.5, 0.5): P.append(boxk((0.5, 0.7, 0.12), (0.8, by0 + 0.1, z), M, A, 'yellow', 'cr_heellug'))
    P.append(cylk(0.1, 1.3, (0.8, by0, 0), CH, A, 'galv', 'cr_heelpin', axis='z', seg=10))
    for z in (-0.3, 0.3): P.append(cylk(0.42, 0.06, (L - 0.2, Y + 2.0, z), M, A, 'yellow', 'cr_headplate', axis='z', seg=14))
    P.append(cylk(0.36, 0.3, (L - 0.2, Y + 2.0, 0), CH, A, 'galv', 'cr_sheave', axis='z', seg=14))
    Q.append(boxk((L - 0.4, by1 - by0, 2 * bz), ((0.4 + L) / 2, (by0 + by1) / 2, 0), M, A, 'yellow', 'cr1_boom'))
    # ---- the whip line and the hook block: red cheeks, a sheave, the swivel and the hook
    hx = L - 0.05
    P.append(rodk((hx, Y + 1.7, 0), (hx, Y - 2.45, 0), 0.025, M, A, 'dark', 'cr_whip', seg=4))
    P.append(boxk((0.6, 0.75, 0.14), (hx, Y - 2.95, -0.22), M, A, 'red', 'cr_cheek', bev=0.04)); P.append(boxk((0.6, 0.75, 0.14), (hx, Y - 2.95, 0.22), M, A, 'red', 'cr_cheek', bev=0.04))
    P.append(cylk(0.24, 0.3, (hx, Y - 2.8, 0), CH, A, 'galv', 'cr_blocksheave', axis='z', seg=12))
    P.append(boxk((0.5, 0.12, 0.6), (hx, Y - 2.52, 0), M, A, 'hazard', 'cr_blocktop'))
    P.append(cylk(0.08, 0.2, (hx, Y - 3.4, 0), M, A, 'galv', 'cr_swivel', seg=8))
    hook = [(hx, Y - 3.5, 0), (hx, Y - 3.75, 0), (hx + 0.06, Y - 3.95, 0), (hx + 0.24, Y - 4.0, 0), (hx + 0.34, Y - 3.86, 0), (hx + 0.32, Y - 3.7, 0)]
    o = sweep(hook, [0.07, 0.08, 0.08, 0.07, 0.06, 0.05], M, seg=8, name='cr_hook'); uv_fit(o, A, 'red'); P.append(o)
    Q.append(rodk((hx, Y + 1.4, 0), (hx, Y - 2.5, 0), 0.05, M, A, 'dark', 'cr1_whip', seg=3)); Q.append(boxk((0.6, 0.9, 0.6), (hx, Y - 2.95, 0), M, A, 'red', 'cr1_block'))
    # ---- the boom rest (the long crane's): a plated post on the compressor house's roof, a rubber-lined cradle
    if rest:
        P.append(boxk((0.8, 0.12, 0.8), (rest, 5.06, 0), M, A, 'yellow', 'cr_restbase'))
        P.append(boxk((0.5, Y + 1.0 - 5.1, 0.5), (rest, 5.1 + (Y + 1.0 - 5.1) / 2, 0), M, A, 'yellow', 'cr_restpost', bev=0.03))
        for s in (-1, 1):
            P.append(box_between((rest, Y + 0.95, 0), (rest, Y + 1.38, s * 0.75), 0.4, 0.08, M, 'cr_cradle')); uv_fit(P[-1], A, 'yellow')
        P.append(boxk((0.42, 0.06, 1.4), (rest, Y + 1.37, 0), M, A, 'rubber', 'cr_restpad'))
        P.append(boxk((0.02, 1.6, 0.5), (rest + 0.26, 7.0, 0), M, A, 'hazard', 'cr_resthz'))
        Q.append(boxk((0.8, Y + 1.4 - 5.0, 0.8), (rest, 5.0 + (Y + 1.4 - 5.0) / 2, 0), M, A, 'yellow', 'cr1_rest'))
    for p in P + Q:
        if p.type == 'MESH' and not p.data.uv_layers: uv_fit(p, A, 'galv')
    for p in P: lib.smooth(p, 35)
    if opt('stats'):
        import re, collections
        tot = collections.Counter()
        for p in P: tot[re.sub(r'\.\d+$', '', p.name)] += MK.tris_of([p])
        for k, v in tot.most_common(12): print('JF_STAT', k, v)
    bx = crane_boxes(L, rest); lo = tuple(min(b[k] for b in bx) for k in range(3)); hi = tuple(max(b[k + 3] for b in bx) for k in range(3))
    return dict(lod0=P, lod1=Q, box=(lo, hi), ao=0.7, lod=90, meta={'kind': 'prop'},
                focus=[((0, Y + 1.5, 0), (1.0, 0.4, 0.8), 6.5), ((L, Y - 1.5, 0), (0.6, 0.2, 1.0), 4.0), ((1.4, 4.5, 0), (1.0, 0.2, 0.4), 5.0)])


if __name__ == '__main__':
    for fid, L, rest in (('p_pedcrane', 34.0, 32.0), ('p_pedcrane_short', 22.0, None)):
        if ONLY and fid[2:] not in ONLY: continue
        run_prop(fid, lambda L=L, rest=rest: build(L, rest))
