# JANKFIRE Platform: the process deck's kit, two props (both rig maps), built over the boxes of shared/map.js
# separator() and pipeRack() (the same numbers here). Visual only: their boxes stay what you bump into and stand on.
# p_separator: a horizontal three-phase separator, origin = the middle of its foot on the deck, its axis along x, the
#   level gauge on the -z side. A rolled shell with 2:1 dished heads, girth seams, two saddles (wear plate, web, ribs,
#   base plate, anchor bolts), three nozzles on top (two gate valves with handwheels, the relief valve in the middle
#   with its lever), the manway on the west head on its davit, the sight glass with the oil, water and gas in it, two
#   level transmitters, a drain under it, the tag (V-101) and DO NOT SHAKE. Candy teal, yellow saddles, red nozzles.
# p_piperack: the pipe rack along x, origin = its middle on the deck. Four portal frames (I-section legs, the beam, knee
#   braces, base plates), the grating walkway on top (3.6) between two bundles of pipe: on the north side process,
#   gas and an insulated line in its aluminium jacket, on the south seawater, gas and firewater, colour coded, with
#   flanges, shoes on every beam, a valve or two, blind flanges either side of the gap where the stair comes up; the
#   cable trays slung under the walkway (ladder trays, their cables in bundles).
# run: blender52 -b --python tools/blender/make_process.py -- [--only=separator,piperack] [--qa] [--stats] [--no-sheet]
#      [--no-export] [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, uv_fit, uv_trim, run_prop, tnoise, box_between, poly_obj, orient, opt, ONLY
from lib import *
import lib

V3 = Vector
TAU = 2 * math.pi


# ------------------------------------------------------------ the numbers (shared/map.js), in each prop's frame
def sep_boxes():
    """separator(B, D, -7, 7, 0, 0)"""
    out = []; L = lambda *b: out.append(b)
    x0, x1, c, r, k, y0 = -7.0, 7.0, 0.0, 1.7, 0.7, 0.6
    L(x0 + 0.6, y0, c - r + k, x1 - 0.6, y0 + 2 * r, c + r - k)
    L(x0 + 0.6, y0 + k, c - r, x1 - 0.6, y0 + 2 * r - k, c - r + k); L(x0 + 0.6, y0 + k, c + r - k, x1 - 0.6, y0 + 2 * r - k, c + r)
    L(x0, y0 + k, c - r + k, x0 + 0.6, y0 + 2 * r - k, c + r - k); L(x1 - 0.6, y0 + k, c - r + k, x1, y0 + 2 * r - k, c + r - k)
    for x in (x0 + 1.8, x1 - 1.8): L(x - 0.45, 0, c - 1.35, x + 0.45, y0 + 0.5, c + 1.35)
    L(x0 - 0.12, y0 + 1.1, c - 0.5, x0, y0 + 2.3, c + 0.5)
    for x in (x0 + 3.5, (x0 + x1) / 2, x1 - 3.5): L(x - 0.25, y0 + 2 * r, c - 0.25, x + 0.25, y0 + 2 * r + 0.5, c + 0.25); L(x - 0.4, y0 + 2 * r + 0.5, c - 0.06, x + 0.4, y0 + 2 * r + 0.56, c + 0.06)
    L(-1.4, y0 + 0.9, c - r - 0.08, 1.4, y0 + 1.3, c - r)
    return out


RX0, RX1, RY = -10.0, 10.0, 3.6        # the rack: pipeRack(B, D, -2, 18, 0, [4, 5.6]) moved to its middle (x - 8)
FRAMES = [-9.7, -4.7, 0.3, 5.3]          # x0 + 0.3, every 5 m
GAP = (-4.0, -2.4)                       # where the stair comes up through the south (+z) pipes
BUNDLE = [(1.2, 1.7), (1.8, 2.3), (2.4, 2.95)]


def rack_boxes():
    out = []; L = lambda *b: out.append(b)
    L(RX0, RY - 0.3, -1.1, RX1, RY, 1.1)
    for x in FRAMES: L(x - 0.18, 0, -3.05, x + 0.18, RY - 0.6, -2.7); L(x - 0.18, 0, 2.7, x + 0.18, RY - 0.6, 3.05); L(x - 0.18, RY - 0.6, -3.05, x + 0.18, RY - 0.3, 3.05)
    for s in (-1, 1):
        for q0, q1 in BUNDLE: L(RX0, RY - 0.3, min(s * q0, s * q1), RX1, RY + 0.25, max(s * q0, s * q1))
    for s in (-1, 1): L(RX0 + 0.5, RY - 1.15, min(s * 0.5, s * 1.0), RX1 - 0.5, RY - 1.05, max(s * 0.5, s * 1.0))
    return out


# ------------------------------------------------------------ the atlas (both props share one)
def _chipped(col, seed, rust=0x9a4a22, p=0.05, streaks=3):
    """candy paint, a little worn: specks of rust, a few runs down the part (v = up)"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        px[:] = hexrgb(col)[None, None] * (0.93 + 0.1 * r.random((h, w, 1)))
        m = (tnoise(w, h, 4, 4, r) + 0.35 * r.random((h, w))) > 1.12
        px[m] = hexrgb(rust) * (0.8 + 0.3 * r.random((int(m.sum()), 1)))
        for k in range(streaks):
            x = int(r.integers(0, w)); L = int(r.integers(h // 3, h))
            px[:L, x] = px[:L, x] * 0.55 + hexrgb(rust) * 0.45
    return d


def _label(lines, bg, fg, seed, scale=1):
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        px[:] = hexrgb(bg) * (0.92 + 0.1 * r.random((h, w, 1)))
        y = (h - 8 * scale * len(lines)) // 2 + scale
        for s in lines:
            tw = (len(s) * 6 - 1) * scale; text_px(px, s, max(0, (w - tw) // 2), y, scale, fg); y += 8 * scale
    return d


def _sight(px):  # the sight glass: gas on top, oil (amber), water (blue-green) at the bottom, the float lines
    h, w = px.shape[:2]
    px[:] = hexrgb(0xd8e8f0)
    px[h // 3:2 * h // 3] = hexrgb(0xff9a1a); px[2 * h // 3:] = hexrgb(0x2ab8a0)
    px[h // 3] = hexrgb(0x5a3a10); px[2 * h // 3] = hexrgb(0x104a40)
    px[:, ::6] *= 0.85


def _tray(px):  # a ladder cable tray seen from above: side rails, rungs, three bundles of cable on it
    h, w = px.shape[:2]; px[:] = hexrgb(0x2a2c32)
    px[:, ::4] = hexrgb(0xa8b0ba)
    px[:2] = px[-2:] = hexrgb(0xa8b0ba)
    for k, col in enumerate((0x1c1c22, 0xff5a1f, 0x2a6ad8)):
        y = 3 + k * (h - 6) // 3; px[y:y + max(1, (h - 6) // 3 - 1)] = hexrgb(col) * 0.95


def _jacket(px):  # an aluminium insulation jacket: overlapping sheets, a band every so often, a bit of grime
    h, w = px.shape[:2]; r = np.random.default_rng(31)
    px[:] = hexrgb(0xd8dce2) * (0.9 + 0.12 * r.random((h, w, 1)))
    px[:, ::16] = hexrgb(0x9aa0a8); px[:, 8::16] = hexrgb(0xeef0f4)
    px[-2:] *= 0.8


def atlas():
    A = Atlas('pr_atlas', 128, 160)
    A.band('jacket', 16, _jacket)
    A.band('tealband', 16, _chipped(0x14b8cc, 41, rust=0x7a4a2a, p=0.02, streaks=6))
    A.cell('teal', 32, 32, _chipped(0x14b8cc, 21, rust=0x7a4a2a, p=0.04, streaks=0))
    A.cell('yellow', 32, 32, _chipped(0xffd21a, 22, rust=0xa0782a, streaks=1))
    A.cell('red', 32, 32, _chipped(0xe8202a, 23))
    A.cell('steel', 32, 32, _chipped(0x8a96a6, 24, rust=0x8a4a22, streaks=3))
    A.cell('tag', 48, 16, _label(['V-101', 'SEPARATOR'], 0xf4f2ee, 0x1a1a1a, 25))
    A.cell('shake', 64, 10, _label(['DO NOT SHAKE'], 0xffe14d, 0xd81a26, 26))
    A.cell('sight', 16, 16, _sight)
    A.cell('tray', 32, 16, _tray)
    A.cell('pgrey', 16, 16, _chipped(0x9aa2ac, 27, streaks=1)); A.cell('pyellow', 16, 16, _chipped(0xffc21a, 28, streaks=1))
    A.cell('pgreen', 16, 16, _chipped(0x2ab84a, 29, streaks=1)); A.cell('pred', 16, 16, _chipped(0xe02a2a, 30, streaks=1))
    for k, c, v, sp in (('galv', 0xa8b0ba, 0.06, None), ('dark', 0x2a2c32, 0.05, None), ('grate', 0x5a6068, 0.1, 0x2a2c30),
                        ('brass', 0xe8b438, 0.06, None), ('white', 0xf4f2ee, 0.03, None), ('rubber', 0x1c1c22, 0.05, None),
                        ('pink', 0xff4fd8, 0.03, None), ('rust', 0x9a4a22, 0.14, 0x5a2a14)):
        A.swatch(k, c, v, 90 + len(A.r), w=8, h=8, speck=sp, p=0.2 if sp else 0.0)
    return A


def rodk(p0, p1, r, M, A, key, name, seg=8):
    o = rod(p0, p1, r, M, seg=seg, name=name); uv_fit(o, A, key); return o


def boxk(size, pos, M, A, key, name, bev=0.0, rot=None):
    o = box(size, pos, M, bev=bev, rot=rot, name=name); uv_fit(o, A, key); return o


def cylk(r, L, pos, M, A, key, name, axis='y', seg=12, bev=0.0):
    o = cyl(r, L, pos, M, axis=axis, seg=seg, name=name, bev=bev); uv_fit(o, A, key); return o


def handwheel(c, axis, r, M, A, P, name='pr_wheel', key='yellow'):
    """a handwheel round a game axis at c: rim (a ring), hub, four spokes"""
    rim = lathe([(r - 0.025, -0.02), (r + 0.015, -0.02), (r + 0.015, 0.02), (r - 0.025, 0.02), (r - 0.025, -0.02)], c, M, seg=12, axis=axis, name=name, cap=False); uv_fit(rim, A, key); P.append(rim)
    P.append(cylk(0.05, 0.08, c, M, A, 'dark', name + 'hub', axis=axis, seg=8))
    cv = V3(c)
    for k in range(4):
        a = TAU * k / 4 + 0.4
        d = V3((0, math.cos(a), math.sin(a))) if axis == 'x' else V3((math.cos(a), 0, math.sin(a))) if axis == 'y' else V3((math.cos(a), math.sin(a), 0))
        P.append(rodk(tuple(cv), tuple(cv + d * (r - 0.01)), 0.014, M, A, key, name + 'spoke', seg=4))


def flange(c, axis, r, t, M, A, key, P, studs=6, name='pr_flange'):
    """a pair of flanges (a joint) round a game axis at c, studs through them"""
    P.append(cylk(r, t, c, M, A, key, name, axis=axis, seg=12))
    cv = V3(c); i = 'xyz'.index(axis)
    for k in range(studs):
        a = TAU * (k + 0.5) / studs; o = [0, 0, 0]; j = [q for q in range(3) if q != i]
        o[j[0]] = math.cos(a) * (r - 0.04); o[j[1]] = math.sin(a) * (r - 0.04)
        P.append(cylk(0.02, t + 0.06, tuple(cv + V3(o)), M, A, 'galv', name + 'stud', axis=axis, seg=4))


# ============================================================ p_separator
R, YC, XS = 1.72, 0.6 + 1.7, 6.4  # the shell's radius, its axis's height, where the heads start


def build_separator():
    A = atlas()
    M = mat('pr_paint', 0xffffff, rough=0.28, metal=0.15, tex=A.image(), clearcoat=0.8)
    CH = mat('pr_chrome', 0xdfe3ea, rough=0.14, metal=0.95, clearcoat=0.3)
    GZ = mat('pr_glass', 0xd8eef8, rough=0.08, metal=0.1, alpha=0.45)
    P, Q = [], []
    # ---- the shell and its dished heads (2:1 ellipsoidal: the knuckle and crown in one curve), girth seams
    o = cyl(R, 2 * XS, (0, YC, 0), M, axis='x', seg=24, name='sp_shell', cap=False); uv_trim(o, A, 'tealband', upm=0.35, grain='x'); P.append(o)
    for s in (-1, 1):
        prof = [(R * math.cos(t), s * (XS + 0.6 * math.sin(t))) for t in [math.pi / 2 * i / 6 for i in range(7)]]
        prof = [(max(r_, 0.0), a) for r_, a in prof]
        o = lathe([(R, s * XS)] + prof[1:], (0, YC, 0), M, seg=24, axis='x', name='sp_head', cap=False); uv_trim(o, A, 'tealband', upm=0.35, grain='y'); P.append(o)
        P.append(cylk(R + 0.012, 0.05, (s * (XS - 0.02), YC, 0), M, A, 'teal', 'sp_headseam', axis='x', seg=24))
    for x in (-3.2, 0.0, 3.2):
        P.append(cylk(R + 0.01, 0.04, (x + 1.6 if x < 0 else x - 1.6 if x > 0 else x, YC, 0), M, A, 'white', 'sp_seam', axis='x', seg=24))
    # ---- the saddles: a wear plate hugging the shell, the web, ribs, the base plate, anchor bolts
    for x in (-5.2, 5.2):
        angs = [math.radians(-62 + 124 * i / 8) for i in range(9)]
        vs = [(x + dx, YC - rr * math.cos(a), rr * math.sin(a)) for rr in (R - 0.01, R + 0.03) for dx in (-0.42, 0.42) for a in angs]  # inner -x, inner +x, outer -x, outer +x
        I0, I1, O0, O1 = 0, 9, 18, 27; fs = []
        for i in range(8):
            fs += [(O0 + i, O0 + i + 1, O1 + i + 1, O1 + i), (I0 + i, I1 + i, I1 + i + 1, I0 + i + 1), (I0 + i, I0 + i + 1, O0 + i + 1, O0 + i), (I1 + i, O1 + i, O1 + i + 1, I1 + i + 1)]
        for e in (0, 8): fs.append((I0 + e, O0 + e, O1 + e, I1 + e))
        wp = poly_obj(vs, fs, M, 'sp_wear'); orient(wp, lambda g, x=x: g - V3((x, YC, 0))); uv_fit(wp, A, 'yellow'); P.append(wp)
        # the web: a plate from the base up to the arc (a polygon, extruded across x)
        web = [(-1.35, 0.06), (1.35, 0.06)] + [((R + 0.01) * math.sin(a), YC - (R + 0.01) * math.cos(a)) for a in [math.radians(62 - 124 * i / 8) for i in range(9)]]
        o = side([(z, y) for z, y in web], 0.06, (x, 0, 0), M, name='sp_web'); uv_fit(o, A, 'yellow'); P.append(o)
        for zz in (-1.0, -0.45, 0.45, 1.0):  # ribs either side of the web
            ytop = YC - math.sqrt(max(0.0, (R + 0.03) ** 2 - zz * zz))
            for dx in (-0.21, 0.21):
                P.append(boxk((0.34, ytop - 0.06, 0.05), (x + dx, 0.06 + (ytop - 0.06) / 2, zz), M, A, 'yellow', 'sp_rib'))
        P.append(boxk((0.9, 0.06, 2.7), (x, 0.03, 0), M, A, 'yellow', 'sp_base', bev=0.01))
        for dx in (-0.32, 0.32):
            for zz in (-1.15, 1.15):
                P.append(cylk(0.035, 0.1, (x + dx, 0.09, zz), M, A, 'galv', 'sp_anchor', seg=6))
    # ---- the nozzles on top: two gate valves with handwheels, the relief valve in the middle
    top = YC + R
    for x in (-3.5, 0.0, 3.5):
        P.append(cylk(0.2, 0.36, (x, top + 0.12, 0), M, A, 'red', 'sp_neck', seg=12))
        flange((x, top + 0.31, 0), 'y', 0.3, 0.06, M, A, 'red', P, name='sp_fl')
        if x:
            P.append(boxk((0.36, 0.22, 0.34), (x, top + 0.44, 0), M, A, 'red', 'sp_valve', bev=0.03))
            P.append(rod((x, top + 0.55, 0), (x, top + 0.66, 0), 0.025, CH, seg=6, name='sp_stem'))
            handwheel((x, top + 0.53, 0), 'y', 0.38, M, A, P, name='sp_wheel')
        else:  # the PSV: a bell bonnet, its cap, the lever, the outlet off the side
            P.append(lathe([(0.18, top + 0.34), (0.2, top + 0.42), (0.14, top + 0.62), (0.1, top + 0.78), (0.0, top + 0.8)], (0, 0, 0), M, seg=12, axis='y', name='sp_psv')); uv_fit(P[-1], A, 'red')
            P.append(cylk(0.06, 0.12, (0, top + 0.85, 0), M, A, 'yellow', 'sp_psvcap', seg=8))
            P.append(rodk((0.02, top + 0.86, 0), (0.32, top + 0.7, 0), 0.015, M, A, 'yellow', 'sp_lever', seg=4))
            P.append(cylk(0.1, 0.28, (0, top + 0.46, 0.22), M, A, 'red', 'sp_psvout', axis='z', seg=10))
    # ---- the manway on the west head: neck, blind flange with its bolts, the davit it swings on, a handle
    hx = -(XS + 0.6)
    P.append(cylk(0.42, 0.22, (hx + 0.02, YC, 0), M, A, 'teal', 'sp_mwneck', axis='x', seg=16))
    P.append(cylk(0.5, 0.06, (hx - 0.09, YC, 0), M, A, 'teal', 'sp_mwflange', axis='x', seg=16))
    flange((hx - 0.125, YC, 0), 'x', 0.52, 0.05, M, A, 'yellow', P, studs=10, name='sp_mwcover')
    P.append(rodk((hx - 0.15, YC + 0.1, 0.0), (hx - 0.24, YC + 0.1, 0.0), 0.02, M, A, 'dark', 'sp_mwhandle', seg=4))
    P.append(rodk((hx + 0.15, YC + 0.58, 0.0), (hx - 0.05, YC + 0.58, 0.0), 0.04, M, A, 'yellow', 'sp_davit', seg=6))
    P.append(rodk((hx - 0.05, YC + 0.58, 0.0), (hx - 0.15, YC + 0.5, 0.0), 0.04, M, A, 'yellow', 'sp_davit', seg=6))
    # ---- the sight glass on the -z side: a chrome frame, the glass, the levels behind it, brackets to the shell
    gz = -(R + 0.05)
    P.append(boxk((2.8, 0.4, 0.04), (0, 1.7, gz), M, A, 'sight', 'sp_sight'))
    for y in (1.48, 1.92): P.append(rod((-1.42, y, gz), (1.42, y, gz), 0.03, CH, seg=6, name='sp_sightframe'))
    for x in (-1.42, 1.42): P.append(rod((x, 1.48, gz), (x, 1.92, gz), 0.03, CH, seg=6, name='sp_sightframe'))
    o = box((2.76, 0.38, 0.01), (0, 1.7, gz - 0.024), GZ, name='sp_glass'); uv_fit(o, A, 'white'); P.append(o)
    for x in (-1.2, 1.2): P.append(rodk((x, 1.7, gz + 0.02), (x, 1.7, -R * 0.96), 0.03, M, A, 'galv', 'sp_sightarm'))
    for x in (-2.4, 2.4):  # the level transmitters: a box on a stalk, a cable down the shell
        P.append(rodk((x, 2.3, -R * 0.98), (x, 2.3, -(R + 0.18)), 0.03, M, A, 'galv', 'sp_txstalk'))
        P.append(boxk((0.18, 0.22, 0.12), (x, 2.3, -(R + 0.24)), M, A, 'dark', 'sp_tx', bev=0.02))
        P.append(boxk((0.08, 0.05, 0.004), (x, 2.33, -(R + 0.302)), M, A, 'pink', 'sp_txlcd'))
    # ---- the tag and the joke, the drain under it
    o = box((1.8, 0.6, 0.02), (-2.6, 2.6, R * 0.93), M, name='sp_tag'); uv_fit(o, A, 'tag'); P.append(o)
    o = box((2.4, 0.38, 0.02), (2.6, 2.0, R * 0.985), M, name='sp_shake'); uv_fit(o, A, 'shake'); P.append(o)
    P.append(rodk((1.0, YC - R + 0.02, 0), (1.0, 0.25, 0), 0.05, M, A, 'galv', 'sp_drain'))
    P.append(boxk((0.16, 0.14, 0.14), (1.0, 0.22, 0), M, A, 'red', 'sp_drainvalve', bev=0.02))
    # ---- lod1: an octagonal shell with its heads, the saddles, the nozzles
    o = cyl(R, 2 * XS, (0, YC, 0), M, axis='x', seg=8, name='sp1_shell'); uv_fit(o, A, 'teal'); Q.append(o)
    for s in (-1, 1):
        o = cyl(R * 0.85, 0.6, (s * (XS + 0.3), YC, 0), M, axis='x', seg=8, r2=R * 0.45, name='sp1_head', rot=(0, math.pi if s < 0 else 0, 0)); uv_fit(o, A, 'teal'); Q.append(o)
    for x in (-5.2, 5.2): Q.append(boxk((0.9, YC - R + 0.2, 2.7), (x, (YC - R + 0.2) / 2, 0), M, A, 'yellow', 'sp1_saddle'))
    for x in (-3.5, 0.0, 3.5): Q.append(boxk((0.4, 0.6, 0.4), (x, top + 0.25, 0), M, A, 'red', 'sp1_nozzle'))
    for p in P + Q:
        if p.type == 'MESH' and not p.data.uv_layers: uv_fit(p, A, 'galv')
    for p in P: lib.smooth(p, 35)
    stats(P)
    bx = sep_boxes(); lo = tuple(min(b[k] for b in bx) for k in range(3)); hi = tuple(max(b[k + 3] for b in bx) for k in range(3))
    return dict(lod0=P, lod1=Q, box=(lo, hi), ao=0.6, lod=60, meta={'kind': 'prop'},
                focus=[((-6.8, 2.3, 0), (-1, 0.3, 0.4), 4.0), ((0, 4.3, 0), (0.4, 0.8, 1), 4.0), ((0, 1.7, -1.8), (0.2, 0.2, -1), 3.5), ((5.2, 0.8, 0), (0.6, 0.3, 1), 3.5)])


# ============================================================ p_piperack
PIPES = {  # (side, slot) -> (key, radius): north (-z) and south (+z), inner to outer
    (-1, 0): ('pgrey', 0.24), (-1, 1): ('pyellow', 0.22), (-1, 2): ('jacket', 0.27),
    (1, 0): ('pgreen', 0.24), (1, 1): ('pyellow', 0.22), (1, 2): ('pred', 0.26),
}


def build_piperack():
    A = atlas()
    M = mat('pr_paint', 0xffffff, rough=0.28, metal=0.15, tex=A.image(), clearcoat=0.8)
    CH = mat('pr_chrome', 0xdfe3ea, rough=0.14, metal=0.95, clearcoat=0.3)
    P, Q = [], []
    # ---- the portal frames: two I-section legs, the beam across, knee braces, base plates
    for x in FRAMES:
        for s in (-1, 1):
            z = s * 2.875
            for dx in (-0.16, 0.16): P.append(boxk((0.04, RY - 0.64, 0.35), (x + dx, 0.04 + (RY - 0.64) / 2, z), M, A, 'steel', 'rk_flange'))  # the flanges
            P.append(boxk((0.28, RY - 0.64, 0.03), (x, 0.04 + (RY - 0.64) / 2, z), M, A, 'steel', 'rk_web'))  # the web
            P.append(boxk((0.5, 0.04, 0.5), (x, 0.02, z), M, A, 'steel', 'rk_basepl'))
            for dz in (-0.18, 0.18):
                P.append(cylk(0.03, 0.08, (x - 0.2, 0.06, z + dz), M, A, 'galv', 'rk_bolt', seg=4)); P.append(cylk(0.03, 0.08, (x + 0.2, 0.06, z + dz), M, A, 'galv', 'rk_bolt', seg=4))
            P.append(box_between((x, RY - 1.5, s * 2.72), (x, RY - 0.62, s * 1.9), 0.12, 0.1, M, 'rk_knee')); uv_fit(P[-1], A, 'steel')
        for dy in (-0.14, 0.14): P.append(boxk((0.36, 0.03, 6.1), (x, RY - 0.45 + dy, 0), M, A, 'steel', 'rk_beamfl'))
        P.append(boxk((0.03, 0.25, 6.1), (x, RY - 0.45, 0), M, A, 'steel', 'rk_beamweb'))
        Q.append(boxk((0.36, RY - 0.6, 0.35), (x, (RY - 0.6) / 2, -2.875), M, A, 'steel', 'rk1_leg')); Q.append(boxk((0.36, RY - 0.6, 0.35), (x, (RY - 0.6) / 2, 2.875), M, A, 'steel', 'rk1_leg'))
        Q.append(boxk((0.36, 0.3, 6.1), (x, RY - 0.45, 0), M, A, 'steel', 'rk1_beam'))
    # longitudinal ties between the frames, at the beams' ends
    for s in (-1, 1):
        P.append(boxk((RX1 - RX0 - 0.6, 0.16, 0.1), (0, RY - 0.66, s * 2.875), M, A, 'steel', 'rk_tie'))
    # ---- the walkway: grating on its stringers, toe boards along the pipes
    P.append(boxk((RX1 - RX0, 0.06, 2.2), (0, RY - 0.03, 0), M, A, 'grate', 'rk_grating'))
    for s in (-1, 1): P.append(boxk((RX1 - RX0, 0.24, 0.1), (0, RY - 0.18, s * 1.05), M, A, 'yellow', 'rk_stringer'))
    Q.append(boxk((RX1 - RX0, 0.3, 2.2), (0, RY - 0.15, 0), M, A, 'grate', 'rk1_walk'))
    # ---- the pipes: on shoes on every beam, flanged every so often, colour bands, the gap, a valve or two
    for (s, k), (key, r) in PIPES.items():
        q0, q1 = BUNDLE[k]; z = s * (q0 + q1) / 2; y = RY - 0.3 + r + 0.03
        runs = [(RX0, GAP[0]), (GAP[1], RX1)] if s > 0 else [(RX0, RX1)]
        for a, b in runs:
            o = cyl(r, b - a, ((a + b) / 2, y, z), M, axis='x', seg=12, name='rk_pipe', cap=False)
            (uv_trim(o, A, 'jacket', upm=1.0, grain='x') if key == 'jacket' else uv_fit(o, A, key)); P.append(o)
            for e, d in ((a, 1), (b, -1)):  # the ends: blind flanges (at the gap) or open into the next module (at the rack's ends)
                inner = (a, b) != (RX0, RX1) and ((d > 0 and e == GAP[1]) or (d < 0 and e == GAP[0]))
                P.append(cylk(r + 0.07, 0.07, (e + d * 0.035, y, z), M, A, 'red' if inner else key if key != 'jacket' else 'galv', 'rk_blind', axis='x', seg=10))
            Q.append(boxk((b - a, 2 * r, 2 * r), ((a + b) / 2, y - 0.03, z), M, A, 'galv' if key == 'jacket' else key, 'rk1_pipe'))
            # flanged joints every 6 m (not on the insulated line: it's jacketed over them, bands instead)
            x = a + 3.0
            while x < b - 1.0:
                if key == 'jacket': P.append(cylk(r + 0.01, 0.04, (x, y, z), M, A, 'galv', 'rk_band', axis='x', seg=12))
                else: flange((x, y, z), 'x', r + 0.08, 0.1, M, A, key, P, studs=4, name='rk_fl')
                x += 6.0
        for x in FRAMES:  # a shoe under it on each beam
            if s > 0 and GAP[0] - 0.2 < x < GAP[1] + 0.2: continue
            P.append(boxk((0.24, 0.05, 2 * r * 0.7), (x, RY - 0.3 + 0.03, z), M, A, 'galv', 'rk_shoe'))
    # gate valves on top of the gas lines, a pressure gauge, small bore along the outside
    for s, x in ((-1, 6.5), (1, -7.0)):
        z = s * (BUNDLE[1][0] + BUNDLE[1][1]) / 2; y = RY - 0.3 + 0.22 + 0.03
        P.append(boxk((0.5, 0.34, 0.4), (x, y, z), M, A, 'pyellow', 'rk_valve', bev=0.04))
        P.append(rod((x, y + 0.17, z), (x, y + 0.42, z), 0.025, CH, seg=6, name='rk_stem'))
        handwheel((x, y + 0.42, z), 'y', 0.22, M, A, P, name='rk_wheel', key='red')
    for s in (-1, 1):
        z = s * 3.1
        P.append(rodk((RX0 + 0.2, RY - 0.05, z), (RX1 - 0.2, RY - 0.05, z), 0.04, M, A, 'galv', 'rk_smallbore', seg=6))
        for x in FRAMES: P.append(boxk((0.06, 0.12, 0.12), (x, RY - 0.12, z), M, A, 'galv', 'rk_clip'))
    # ---- the cable trays under the walkway on drop rods
    for s in (-1, 1):
        z = s * 0.75
        P.append(boxk((RX1 - RX0 - 1.0, 0.1, 0.5), (0, RY - 1.1, z), M, A, 'tray', 'rk_tray'))
        for x in FRAMES:
            for dz in (-0.22, 0.22): P.append(rodk((x + 0.3, RY - 1.08, z + dz), (x + 0.3, RY - 0.6, z + dz), 0.015, M, A, 'galv', 'rk_drop', seg=4))
    Q.append(boxk((RX1 - RX0 - 1.0, 0.1, 1.5), (0, RY - 1.1, 0), M, A, 'tray', 'rk1_trays'))
    for x in FRAMES: Q.append(boxk((0.05, 0.52, 1.5), (x + 0.3, RY - 0.83, 0), M, A, 'galv', 'rk1_hanger'))
    for p in P + Q:
        if p.type == 'MESH' and not p.data.uv_layers: uv_fit(p, A, 'galv')
    for p in P: lib.smooth(p, 35)
    stats(P)
    bx = rack_boxes(); lo = tuple(min(b[k] for b in bx) for k in range(3)); hi = tuple(max(b[k + 3] for b in bx) for k in range(3))
    return dict(lod0=P, lod1=Q, box=(lo, hi), ao=0.6, lod=60, meta={'kind': 'prop'},
                focus=[((-3.2, 3.6, 2.0), (0.5, 0.8, 1), 4.0), ((0.3, 2.0, -2.9), (0.6, 0.2, -1), 4.0), ((6.5, 3.8, -2.0), (0.4, 0.6, -1), 2.5)])


def stats(P):
    if not opt('stats'): return
    import re, collections
    tot = collections.Counter()
    for p in P: tot[re.sub(r'\.\d+$', '', p.name)] += MK.tris_of([p])
    for k, v in tot.most_common(14): print('JF_STAT', k, v)


if __name__ == '__main__':
    for fid, fn in (('p_separator', build_separator), ('p_piperack', build_piperack)):
        if ONLY and fid[2:] not in ONLY: continue
        run_prop(fid, fn)
