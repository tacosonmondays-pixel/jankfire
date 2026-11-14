# JANKFIRE Battle Island: PORT JANKTON's pub and harbour master (shared/battleisland.js pjPub(), the PJP table: same
# numbers here). Each building is built over its own boxes from its c (origin = c at the town's level, 1.6 m; x east,
# z south) and carries meta.box = those boxes' extent. Visual only: the boxes collide. The island's clean resort look:
# smooth glossy paint, crisp trims and signs, saturated colours, hardly any wear.
#   p_pj_pub      THE SINKING FEELING, a seaside pub: a glossy navy pub front (pilasters with gold capitals, the name in
#                 gold on the fascia, stained-glass top lights, double doors with portholes, carriage lamps, window boxes,
#                 hanging baskets, a hanging sign of a ship going down), white render above, the roof terrace's parapet
#                 (ROOF BEER GARDEN (NO GARDEN)), a white stair up the south side (TOP DECK / MIND THE BOAT). Inside:
#                 the pub carpet, dark panelling, beams; the bar (panelled, a brass foot rail, hand pumps, a tap tower,
#                 pints), the back bar (bottles, NO SWIMMING IN THE BEER), red stools, two booths back to back, the snug
#                 screen, the dartboard (AIM FOR THE BOARD (NOT DAVE), darts in the wall), a jukebox, a ship's-wheel
#                 light, and the bow of a boat coming down through the ceiling. On the roof: decking, festoon lights,
#                 parasols over picnic tables, kegs, the chimney, and that boat, LAST ORDERS, an open launch with an
#                 outboard, sinking stern-up into the terrace. Out front: picnic tables, the quiz board (EVERY ANSWER IS
#                 FISH)
#   p_pj_harbour  THE HARBOUR MASTER: a white office with red trims at the east pier's root (HARBOUR MASTER, HONK FOR
#                 SERVICE, the chalkboard: WIND: YES), a white stair up its front onto the roof, a flight up the roof to
#                 the gallery round the red lookout on its tower (open windows all round, a telescope), a red pyramid
#                 roof with a gold weathervane, the foghorn, a signal mast with flags, life rings, and the tide dial on
#                 the tower (TIDE: YES). Inside: the counter, the chart table, the radio desk, a filing cabinet
# run: blender52 -b --python tools/blender/make_pjpub.py -- [--only=pub,harbour] [--qa] [--no-sheet] [--no-export]
#      [--preview=<dir>]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_market as MK
from make_market import Atlas, uv_trim, uv_fit, box_between
from make_portjankton import swatches, box_at, ring
import make_pjstreet as PS
from make_pjstreet import pix, bake_loc, _face_fit, PER
import make_bipark as BP
from make_bipark import run_bi, tri_ngons
from lib import *
from lib import _obj
import lib
TR = BP.TR

V3 = Vector
TAU = 2 * math.pi
ONLY = MK.ONLY
UPM = 20 / 256   # wall bands: 20 px a metre along them as up them (16 px = one 0.8 m strip)

# shared/battleisland.js PJP
PJP = dict(
    pub=dict(c=[6, 94], w=12, d=16, h=4.2, t=0.25, roof=0.3, par=1.0, pt=0.2, door=[0.9, 2.6], back=[4.6, 6.0, 2.4],
             wins=[[-6.6, -2.0], [2.0, 6.6]], sill=0.9, head=2.9, nwin=[-1.2, 2.8], swin=[-4.2, -1.4],
             stair=dict(x0=5.6, n=12, run=0.34, z0=8, z1=9.3, land=0.2),
             inside=[[-5.75, -7.75, -5.3, 3.2, 2.2], [-3.4, -7.75, -2.6, 2.6, 1.1],
                     [-1.6, -7.75, -1.48, -5.95, 1.2], [-1.48, -7.75, -1.05, -5.95, 0.45], [-0.85, -7.75, 0.05, -5.95, 0.75], [0.25, -7.75, 0.68, -5.95, 0.45], [0.68, -7.75, 0.92, -5.95, 1.2],
                     [0.92, -7.75, 1.35, -5.95, 0.45], [1.55, -7.75, 2.45, -5.95, 0.75], [2.65, -7.75, 3.08, -5.95, 0.45], [3.08, -7.75, 3.2, -5.95, 1.2],
                     [-1.0, 3.0, 2.6, 3.15, 2.0], [4.4, 7.1, 5.3, 7.75, 1.55], [3.2, -3.6, 4.0, -2.8, 0.75], [3.6, 4.4, 4.4, 5.2, 0.75]],
             stools=[-6, -4.2, -2.4, -0.6, 1.2], stool=[-2.46, -2.04, 0.21, 0.75],
             deck=[[0.0, -6.8, 1.1, -4.4, 1.8], [1.1, -6.8, 2.2, -4.4, 4.2], [2.2, -6.8, 3.35, -4.4, 3.3], [-5.8, 6.2, -4.8, 7.6, 2.2],
                   [1.6, 2.4, 3.4, 4.0, 0.78], [-2.6, 2.4, -0.8, 4.0, 0.78], [-5.6, -7.6, -4.5, -6.3, 1.0]],
             out=[[7.0, -6.6, 8.6, -4.8, 0.78], [7.0, 4.8, 8.6, 6.6, 0.78], [6.6, -2.1, 7.1, -1.5, 1.0]]),
    hm=dict(c=[82, 137.5], w=8, d=6.2, h=3.4, t=0.25, roof=0.3, par=0.6, pt=0.2,
            door=[-1.6, -0.4, 2.3], win=[-3.4, -2.0], side=[-1.8, 1.8], back=[2.2, 3.2], sill=1.0, head=2.5,
            stair=dict(x0=4.6, n=11, run=0.32, z0=3.1, z1=4.3, land=0.6), gap=[0.6, 1.8],
            tower=[-4, -3.1, -0.4, 0.5], top=7.4, gal=1.0, rail=1.05, flight=dict(z0=2.8, n=11, run=0.318, land=1.1),
            room=2.5, wt=0.15, post=0.45, rsill=1.0, rhead=2.1, rdoor=[-1.8, -0.7], cap=0.25, peak=[[1.3, 0, 0.42, 3], [0.58, 0.42, 0.84, 1]],
            inside=[[-3.75, 0.4, 0.6, 1.0, 1.1], [-1.8, -2.1, -0.2, -0.9, 0.95], [-3.75, -2.85, -3.1, -0.6, 0.8], [3.15, 1.5, 3.75, 2.6, 1.4]]))
PROPS = []
def prop(fid):
    def reg(fn): PROPS.append((fid, fn)); return fn
    return reg


# ------------------------------------------------------------ the boxes, exactly as pjPub() adds them (lo, hi) in each building's frame
def pub_boxes():
    P = PJP['pub']; hw, hd, t, H = P['w'] / 2, P['d'] / 2, P['t'], P['h']; rt = H + P['roof']; pt = P['pt']
    out = []
    def A(x0, y0, z0, x1, y1, z1): out.append(((x0, y0, z0), (x1, y1, z1)))
    fx0 = hw - t; dw, dh = P['door']; (a0, a1), (b0, b1) = P['wins']; sl, hh = P['sill'], P['head']; k0, k1, kh = P['back']
    A(fx0, 0, -hd, hw, H, a0); A(fx0, 0, a0, hw, sl, a1); A(fx0, hh, a0, hw, H, a1)
    A(fx0, 0, a1, hw, H, -dw); A(fx0, dh, -dw, hw, H, dw); A(fx0, 0, dw, hw, H, b0)
    A(fx0, 0, b0, hw, sl, b1); A(fx0, hh, b0, hw, H, b1); A(fx0, 0, b1, hw, H, hd)
    A(-hw, 0, -hd, -hw + t, H, k0); A(-hw, 0, k1, -hw + t, H, hd); A(-hw, kh, k0, -hw + t, H, k1)
    for z0, (w0, w1) in ((-hd, P['nwin']), (hd - t, P['swin'])):
        A(-hw + t, 0, z0, w0, H, z0 + t); A(w0, 0, z0, w1, sl, z0 + t); A(w0, hh, z0, w1, H, z0 + t); A(w1, 0, z0, fx0, H, z0 + t)
    for x0, z0, x1, z1, h in P['inside']: A(x0, 0, z0, x1, h, z1)
    s0, s1, sz, sh = P['stool']
    for z in P['stools']: A(s0, 0, z - sz, s1, sh, z + sz)
    St = P['stair']; top = rt + P['par']; lx = St['x0'] - St['n'] * St['run']; r = rt / St['n']
    A(-hw, H, -hd, hw, rt, hd)
    A(hw - pt, rt, -hd, hw, top, hd); A(-hw, rt, -hd, -hw + pt, top, hd); A(-hw + pt, rt, -hd, hw - pt, top, -hd + pt)
    A(-hw + pt, rt, hd - pt, St['land'], top, hd); A(lx, rt, hd - pt, hw - pt, top, hd)
    for i in range(St['n']): A(St['x0'] - (i + 1) * St['run'], 0, St['z0'], St['x0'] - i * St['run'], (i + 1) * r, St['z1'])
    A(St['land'], H, St['z0'], lx, rt, St['z1'])
    for x0, z0, x1, z1, h in P['deck']: A(x0, rt, z0, x1, rt + h, z1)
    for x0, z0, x1, z1, h in P['out']: A(x0, 0, z0, x1, h, z1)
    return out


def hm_boxes():
    P = PJP['hm']; hw, hd, t, H = P['w'] / 2, P['d'] / 2, P['t'], P['h']; rt = H + P['roof']; pt = P['pt']
    out = []
    def A(x0, y0, z0, x1, y1, z1): out.append(((x0, y0, z0), (x1, y1, z1)))
    d0, d1, dh = P['door']; w0, w1 = P['win']; s0, s1 = P['side']; k0, k1 = P['back']; sl, hh = P['sill'], P['head']
    A(-hw, 0, hd - t, w0, H, hd); A(w0, 0, hd - t, w1, sl, hd); A(w0, hh, hd - t, w1, H, hd)
    A(w1, 0, hd - t, d0, H, hd); A(d0, dh, hd - t, d1, H, hd); A(d1, 0, hd - t, hw, H, hd)
    A(-hw, 0, -hd, k0, H, -hd + t); A(k0, dh, -hd, k1, H, -hd + t); A(k1, 0, -hd, hw, H, -hd + t)
    A(-hw, 0, -hd + t, -hw + t, H, s0); A(-hw, 0, s0, -hw + t, sl, s1); A(-hw, hh, s0, -hw + t, H, s1); A(-hw, 0, s1, -hw + t, H, hd - t)
    A(hw - t, 0, -hd + t, hw, H, hd - t)
    for x0, z0, x1, z1, h in P['inside']: A(x0, 0, z0, x1, h, z1)
    g0, g1 = P['gap']; tx0, tz0, tx1, tz1 = P['tower']; pp = rt + P['par']
    A(-hw, H, -hd, hw, rt, hd)
    A(-hw, rt, hd - pt, g0, pp, hd); A(g1, rt, hd - pt, hw, pp, hd); A(tx1, rt, -hd, hw, pp, -hd + pt)
    A(-hw, rt, tz1, -hw + pt, pp, hd - pt); A(hw - pt, rt, -hd + pt, hw, pp, hd - pt)
    A(tx0, rt, tz0, tx1, P['top'], tz1)
    St = P['stair']; r = rt / St['n']
    for i in range(St['n']): A(St['land'] if i == St['n'] - 1 else St['x0'] - (i + 1) * St['run'], 0, St['z0'], St['x0'] - i * St['run'], (i + 1) * r, St['z1'])
    F = P['flight']; T = P['top']; fr = (T - rt) / F['n']; fz = F['z0'] - F['n'] * F['run']
    for i in range(F['n']): A(g0, rt, F['z0'] - (i + 1) * F['run'], g1, rt + (i + 1) * fr, F['z0'] - i * F['run'])
    gl = P['gal']; gx0, gx1, gz0, gz1 = tx0 - gl, tx1 + gl, tz0 - gl, tz1 + gl; R = 0.06; rh = T + P['rail']; lz = fz - F['land']
    A(gx0, T - 0.15, gz0, gx1, T, tz0); A(gx0, T - 0.15, tz1, gx1, T, gz1); A(gx0, T - 0.15, tz0, tx0, T, tz1); A(tx1, T - 0.15, tz0, gx1, T, tz1)
    A(g0, T - 0.15, lz, g1, T, fz)
    A(gx0, T, gz0, gx1, rh, gz0 + R); A(gx0, T, gz1 - R, gx1, rh, gz1); A(gx0, T, gz0 + R, gx0 + R, rh, gz1 - R)
    A(gx1 - R, T, gz0 + R, gx1, rh, lz); A(gx1 - R, T, fz, gx1, rh, gz1 - R)
    A(g0, T, lz, g1, rh, lz + R); A(g1 - R, T, lz + R, g1, rh, fz)
    wt, po = P['wt'], P['post']; ws, wh, rtop = T + P['rsill'], T + P['rhead'], T + P['room']; r0, r1 = P['rdoor']
    for z0, z1 in ((tz0, tz0 + wt), (tz1 - wt, tz1)):
        A(tx0, T, z0, tx1, ws, z1); A(tx0, wh, z0, tx1, rtop, z1); A(tx0, ws, z0, tx0 + po, wh, z1); A(tx1 - po, ws, z0, tx1, wh, z1)
    A(tx0, T, tz0 + wt, tx0 + wt, ws, tz1 - wt); A(tx0, wh, tz0 + wt, tx0 + wt, rtop, tz1 - wt); A(tx0, ws, tz0 + wt, tx0 + wt, wh, tz0 + po); A(tx0, ws, tz1 - po, tx0 + wt, wh, tz1 - wt)
    A(tx1 - wt, T, tz0 + wt, tx1, rtop, r0); A(tx1 - wt, T, r1, tx1, rtop, tz1 - wt); A(tx1 - wt, wh, r0, tx1, rtop, r1)
    cx0 = tx0 - 0.3; cw = (tx1 - tx0 + 0.6) / 4; mx, mz = (tx0 + tx1) / 2, (tz0 + tz1) / 2; ct = rtop + P['cap']
    for i in range(4): A(cx0 + i * cw, rtop, tz0 - 0.3, cx0 + (i + 1) * cw, ct, tz1 + 0.3)
    for hs, y0, y1, n in P['peak']:
        for i in range(n): A(mx - hs + i * 2 * hs / n, ct + y0, mz - hs, mx - hs + (i + 1) * 2 * hs / n, ct + y1, mz + hs)
    return out


def extent(bx):
    return tuple(min(b[0][i] for b in bx) for i in range(3)), tuple(max(b[1][i] for b in bx) for i in range(3))


# ------------------------------------------------------------ painting (rows top-down; clean: flat colour, a whisper of grain)
def grain(px, col, var=0.025, seed=1):
    h, w = px.shape[:2]; r = np.random.default_rng(seed)
    px[:] = hexrgb(col)[None, None] * (1 - var + 2 * var * r.random((h, w, 1)))


def flat_c(col, var=0.025, seed=1):
    return lambda px: grain(px, col, var, seed)


def paint_plinth(base, band, line, frac=0.45):  # a wall's bottom strip: the render above, a painted plinth below, a line on it
    def d(px):
        h = px.shape[0]; grain(px, base, 0.02, 3); k = int(round(h * frac))
        px[k:] = hexrgb(band) * (0.98 + 0.03 * np.random.default_rng(5).random((h - k, px.shape[1], 1)))
        px[k] = hexrgb(line); px[-1] *= 0.8
    return d


def paint_boards(col, gap, seed, rows=4, vert=False, nails=False):  # planks in rows (or columns), each its own tone, clean gaps
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        if vert:
            for x in range(0, w, rows): px[:, x:x + rows] = hexrgb(col) * r.uniform(0.9, 1.06)
            px[:, ::rows] = hexrgb(gap)
        else:
            for y in range(0, h, rows):
                x = 0
                while x < w:
                    L = int(r.integers(24, 64)); px[y:y + rows, x:x + L] = hexrgb(col) * r.uniform(0.9, 1.06)
                    px[y:y + rows, x] = hexrgb(gap); x += L
            px[::rows] = hexrgb(gap)
            if nails:
                for y in range(1, h, rows):
                    for x in range(5, w, 32): px[y, x] = hexrgb(gap) * 1.3
        px[:] *= 0.985 + 0.03 * r.random((h, w, 1))
    return d


def paint_panelling(top=False, bottom=False):  # dark tongue and groove; the dado rail on top / the skirting below
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(71 + top + 2 * bottom)
        for x in range(0, w, 6): px[:, x:x + 6] = hexrgb(0x6a3420) * r.uniform(0.9, 1.08)
        px[:, ::6] = hexrgb(0x3a1a10)
        px[:, 1::6] *= 1.12
        if top: px[:3] = hexrgb(0x8a4a28); px[0] = hexrgb(0xb06a38); px[3] = hexrgb(0x2a120a)
        if bottom: px[-3:] = hexrgb(0x3a1a10); px[-3] = hexrgb(0x8a4a28)
    return d


def paint_carpet(px):  # a proper pub carpet: navy, gold diamonds with red hearts, a half-drop repeat
    h, w = px.shape[:2]
    px[:] = hexrgb(0x1e2d6e)
    m = ['...G....', '..GRG...', '.GRYRG..', 'GRYRYRG.', '.GRYRG..', '..GRG...', '...G....', '........']
    for y0 in range(0, h, 8):
        off = 4 if (y0 // 8) % 2 else 0
        for x0 in range(0, w, 8):
            for j, row in enumerate(m):
                for i, ch in enumerate(row):
                    if ch != '.': px[y0 + j, (x0 + i + off) % w] = hexrgb({'G': 0xffc83a, 'R': 0xc8283a, 'Y': 0xff7a3a}[ch])
    px[:] *= 0.97 + 0.04 * np.random.default_rng(73).random((h, w, 1))


def paint_hull(px):  # the launch's side, top (the gunwale) to bottom (the keel): navy rubbing strake, white clinker
    h, w = px.shape[:2]  # planks, a sky-blue boot stripe, red antifouling
    rows = [0x1f3a8a, 0x1f3a8a, 0xfbf8f0, 0xfbf8f0, 0xe6e2da, 0xfbf8f0, 0xfbf8f0, 0xe6e2da, 0xfbf8f0, 0xfbf8f0, 0x3fb8e8, 0x3fb8e8,
            0xfbf8f0, 0xd8283a, 0xd8283a, 0xc01e30]
    for j in range(h): px[j] = hexrgb(rows[min(j * len(rows) // h, len(rows) - 1)])
    px[:] *= 0.985 + 0.03 * np.random.default_rng(75).random((h, w, 1))


def paint_stripes_v(a, b, n=8):  # parasol canvas: n stripes round it (u)
    def d(px):
        h, w = px.shape[:2]
        for i in range(n): px[:, i * w // n:(i + 1) * w // n] = hexrgb(a if i % 2 == 0 else b)
        px[-1] *= 0.85
    return d


def paint_board(lines, bg, fg, border=None, scale=1, shadow=None, cols=None, bw=1):
    """a crisp sign: flat colour, a border, centred 5x7 text (cols: a colour per line), an optional drop shadow"""
    def d(px):
        h, w = px.shape[:2]; px[:] = hexrgb(bg)
        if border is not None: px[:bw] = hexrgb(border); px[-bw:] = hexrgb(border); px[:, :bw] = hexrgb(border); px[:, -bw:] = hexrgb(border)
        lh = 8 * scale; y0 = (h - lh * len(lines)) // 2 + scale // 2
        for i, s in enumerate(lines):
            x = max(0, (w - (len(s) * 6 - 1) * scale) // 2)
            if shadow is not None: text_px(px, s, x + max(1, scale // 2), y0 + i * lh + max(1, scale // 2), scale, shadow)
            text_px(px, s, x, y0 + i * lh, scale, cols[i] if cols else fg)
    return d


def paint_hang(px):  # the hanging sign: a little boat going down stern-up in a blue sea, the name under it
    h, w = px.shape[:2]
    px[:] = hexrgb(0x1f3a8a)
    px[2:30, 2:w - 2] = hexrgb(0x8ad8ff); px[18:30, 2:w - 2] = hexrgb(0x1f6ad8)
    for x in range(3, w - 3, 6): px[18, x:x + 3] = hexrgb(0xf4fbff)
    px[4:8, 34:40] = hexrgb(0xffe14d); px[5:7, 33:41] = hexrgb(0xffe14d)  # the sun
    boat = ['.....P.......', '.....PP......', '.....P.......', '..RRRRW......', '...RWWWWW....', '....RWWWWWW..', '.....RRWWWWWB',
            '.......RRWWBB', '.........RRBB']
    pix(px, boat, 8, 7, 2, {'R': 0xd8283a, 'W': 0xfbf8f0, 'B': 0x1f6ad8, 'P': 0xff4fd8})
    px[23:24, 4:w - 4] = hexrgb(0x1f6ad8)
    for i, s in enumerate(('THE', 'SINKING', 'FEELING')): text_px(px, s, (w - (len(s) * 6 - 1)) // 2, 32 + i * 9, 1, 0xffc83a)
    px[:1] = px[-1:] = hexrgb(0xffc83a); px[:, :1] = px[:, -1:] = hexrgb(0xffc83a)
    px[30:31, 2:w - 2] = hexrgb(0xffc83a)


def paint_dartboard(px):  # a dartboard: black ring, twenty black / cream sectors, red and green doubles and trebles, the bull
    h, w = px.shape[:2]; c = w / 2
    px_disc(px, c, c, c, 0x1c1c22)
    for k in range(20):
        a0 = (k - 0.5) * TAU / 20; a1 = a0 + TAU / 20
        if a0 > math.pi: a0 -= TAU; a1 -= TAU
        spans = [(a0, min(a1, math.pi)), (-math.pi, a1 - TAU)] if a1 > math.pi else [(a0, a1)]
        for b0, b1 in spans:
            px_disc(px, c, c, c * 0.8, 0x1c1c22 if k % 2 else 0xf2e6c8, a0=b0, a1=b1)
            px_disc(px, c, c, c * 0.8, 0xd8283a if k % 2 else 0x2a9a4a, r_in=c * 0.72, a0=b0, a1=b1)
            px_disc(px, c, c, c * 0.5, 0xd8283a if k % 2 else 0x2a9a4a, r_in=c * 0.43, a0=b0, a1=b1)
    px_disc(px, c, c, c * 0.14, 0x2a9a4a); px_disc(px, c, c, c * 0.07, 0xd8283a)
    for k in range(20):  # the numbers ring: white ticks
        a = k * TAU / 20; x, y = c + math.sin(a) * c * 0.9, c - math.cos(a) * c * 0.9
        px[int(y), int(x)] = hexrgb(0xf4f2ee)


def paint_bottles(px):  # two shelves of bottles in front of a mirror: greens, ambers, clears, a blue gin, lit edges
    h, w = px.shape[:2]; r = np.random.default_rng(81)
    px[:] = hexrgb(0x6a8a9a)
    px[:, :] *= np.linspace(1.15, 0.85, w)[None, :, None]
    cols = [0x2a8a3a, 0xc87a1a, 0xe8f0f4, 0x1f6ad8, 0x8a2a1a, 0xffc83a, 0x2aa59a]
    for y0 in (0, h // 2):
        x = 1
        while x < w - 3:
            bw = int(r.integers(3, 5)); c = hexrgb(cols[int(r.integers(0, len(cols)))]); top = y0 + int(r.integers(2, 6))
            px[top + 3:y0 + h // 2 - 2, x:x + bw] = c; px[top:top + 3, x + bw // 2:x + bw // 2 + 1] = c
            px[top + 3:y0 + h // 2 - 2, x] = c * 1.4; px[top + 6:top + 9, x:x + bw] = hexrgb(0xf4f2ee)
            x += bw + 1
        px[y0 + h // 2 - 2:y0 + h // 2] = hexrgb(0x5a2a18)


def paint_juke(px):  # the jukebox's face: a window with a record spinning in it, the buttons, a grille
    h, w = px.shape[:2]
    px[:] = hexrgb(0x8a1a2a)
    px[1:12, 2:w - 2] = hexrgb(0x1a2a5a); px_disc(px, w / 2, 7, 4.5, 0x1c1c22); px_disc(px, w / 2, 7, 1.5, 0xffc83a)
    for i in range(5): px[13:15, 2 + i * 4:4 + i * 4] = hexrgb(0xf4f2ee if i % 2 else 0xff4fd8)
    for y in range(17, h - 2, 2): px[y, 3:w - 3] = hexrgb(0xd8dee6)
    px[:, :1] = px[:, -1:] = hexrgb(0xd8dee6)


def paint_stained(px):  # leaded top lights: lozenges of sea-glass colours in lead
    h, w = px.shape[:2]
    cols = [0x2aa59a, 0x4fd8ff, 0xffe14d, 0xff4fd8, 0x1f6ad8]
    for j in range(h):
        for i in range(w):
            k = ((i + j) // 4 + (i - j + 64) // 4) % len(cols); px[j, i] = hexrgb(cols[k])
    for j in range(h):
        for i in range(w):
            if (i + j) % 4 == 0 or (i - j) % 4 == 0: px[j, i] = hexrgb(0x2a2a30)
    px[:1] = px[-1:] = hexrgb(0x2a2a30)


def paint_barfront(px):  # a mahogany bar front: raised panels, lit top edges
    h, w = px.shape[:2]
    grain(px, 0x5a2a18, 0.03, 83)
    for x0 in range(2, w - 2, 8):
        px[2:h - 2, x0:x0 + 6] = hexrgb(0x7a3a20); px[2, x0:x0 + 6] = hexrgb(0xa85a30); px[2:h - 2, x0] = hexrgb(0x9a4a28)
        px[h - 3, x0:x0 + 6] = hexrgb(0x3a1a10)


def paint_chalk(lines, cols=None):  # a blackboard in a wooden frame, chalk letters
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(85)
        grain(px, 0x1e2a26, 0.06, 85)
        lh = 8; y0 = (h - lh * len(lines)) // 2
        for i, s in enumerate(lines): text_px(px, s, max(1, (w - (len(s) * 6 - 1)) // 2), y0 + i * lh, 1, (cols or [0xf4f2ee] * 9)[i])
        px[:2] = px[-2:] = hexrgb(0x9a6a3a); px[:, :2] = px[:, -2:] = hexrgb(0x9a6a3a)
    return d


def paint_cola(px):  # the back wall's painted ad: JANK COLA (the island drinks it too), IT'S FINE
    h, w = px.shape[:2]; px[:] = hexrgb(0xe0302a)
    px[:2] = px[-2:] = hexrgb(0xfbf8f0); px[:, :2] = px[:, -2:] = hexrgb(0xfbf8f0)
    text_px(px, 'JANK COLA', (w - 106) // 2 + 1, 4, 2, 0x8a1420); text_px(px, 'JANK COLA', (w - 106) // 2, 3, 2, 0xfbf8f0)
    px[19:21, 12:w - 12] = hexrgb(0xffe14d); text_px(px, "IT'S FINE", (w - 53) // 2, 22, 1, 0xfbf8f0)


def paint_facade_pub(px):  # the far LOD's front: navy ground floor, the windows, the gold sign, the white parapet
    h, w = px.shape[:2]; Hm, Wm = 5.5, 16.0
    def Y(y): return int(round((1 - y / Hm) * h))
    def Z(z): return int(round((z / Wm + 0.5) * w))
    px[:] = hexrgb(0x1f3a8a)
    for z0, z1 in PJP['pub']['wins']: px[Y(2.9):Y(0.9), Z(z0):Z(z1)] = hexrgb(0x2a2026); px[Y(2.9):Y(2.36), Z(z0):Z(z1)] = hexrgb(0x4fd8ff)
    px[Y(2.6):, Z(-0.9):Z(0.9)] = hexrgb(0x1a1418)
    px[Y(3.84):Y(2.98), Z(-7.9):Z(7.9)] = hexrgb(0xffc83a); px[Y(3.6):Y(3.2), Z(-6):Z(6)] = hexrgb(0x1f3a8a)
    px[:Y(4.5)] = hexrgb(0xfbf8f0); px[Y(5.25):Y(4.75), Z(-5):Z(5)] = hexrgb(0x1f3a8a)


# ------------------------------------------------------------ geometry helpers
def crisp(o, ang=35):
    """smooth shading with the hard edges kept hard (sharp by angle: boxes stay boxes)"""
    me = o.data
    for p in me.polygons: p.use_smooth = True
    if hasattr(me, 'set_sharp_from_angle'): me.set_sharp_from_angle(angle=math.radians(ang))
    return o


def gx(o, fn):
    """move a part's vertices with fn(game point) -> game point (its placement baked in first)"""
    bake_loc(o)
    for v in o.data.vertices: g = fn(V3((v.co.x, v.co.z, -v.co.y))); v.co = gv(*g)
    o.data.update()
    return o


def clip(o, lo=None, hi=None):
    """cut a part at game heights: keep lo <= y <= hi (open cuts: the deck or the ceiling hides them)"""
    bake_loc(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    if lo is not None: bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, lo), plane_no=(0, 0, 1), clear_inner=True)
    if hi is not None: bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, hi), plane_no=(0, 0, 1), clear_outer=True)
    bm.to_mesh(o.data); bm.free(); o.data.update()
    return o


def wall_uv2(o, A, cen, k, outer, inner, edge, upm, ctr):
    """make_pjstreet's wall_uv, the outside told from the inside by the building's own middle (ctr)"""
    apply_mods(o)
    me = o.data; uv = MK._uvl(o); P = MK._gp(o); lo, hi = MK._bb(P); ext = hi - lo
    thin = 0 if ext[0] < ext[2] else 2
    for poly in me.polygons:
        n = MK._gn(poly.normal)
        fc = sum((P[v] for v in poly.vertices), V3()) / len(poly.vertices) + cen
        if abs(n[thin]) > 0.5: key = outer(k) if n[thin] * (fc[thin] - ctr[thin]) > 0 else inner(k)
        else: key = edge
        x0, y0, x1, y1 = A.r[key]; rect = A.uvrect(key)
        if x1 - x0 == A.w and abs(n[thin]) > 0.5:
            ha = 2 if thin == 0 else 0; u0, v0, u1, v1 = rect
            for li in poly.loop_indices:
                p = P[me.loops[li].vertex_index] + cen
                t = min(1.0, max(0.0, (p.y - k * PER) / PER))
                uv[li].uv = (p[ha] * upm, v0 + (v1 - v0) * t)
        else: _face_fit(me, uv, poly, P, cen, rect)


class Kit:
    """one building's parts: lod0 (P), lod1 (Q), its atlas and materials"""
    def __init__(self, fid, A, M, GL):
        self.fid, self.A, self.M, self.GL = fid, A, M, GL
        self.P, self.Q = [], []

    def bk(self, lo, hi, key, name, bev=0.0, m=None, far=False):
        o = box(tuple(hi[i] - lo[i] for i in range(3)), tuple((hi[i] + lo[i]) / 2 for i in range(3)), m or self.M, bev=bev, name=self.fid + '_' + name, seg=1)
        uv_fit(o, self.A, key); (self.Q if far else self.P).append(o); return o

    def rod(self, a, b, r, key, name, seg=6, m=None):
        o = rod(a, b, r, m or self.M, seg=seg, name=self.fid + '_' + name); uv_fit(o, self.A, key); self.P.append(o); return o

    def add(self, o, key=None, far=False):
        if key: uv_fit(o, self.A, key)
        (self.Q if far else self.P).append(o); return o

    def wall(self, lo, hi, name, outer, inner, edge, upm=UPM, ctr=(0, 0, 0), bot=None, cap=True):
        """a wall piece cut into 0.8 m strips (the boards and bands run on across every piece), no faces between them.
        bot / cap: keep its underside (default: unless it stands on the floor or the roof) / its top (not under a slab)"""
        ctr = V3(ctr)
        if bot is None: bot = lo[1] > 0.01
        for k in range(int(lo[1] // PER + 1e-6), int(math.ceil(hi[1] / PER - 1e-6))):
            y0, y1 = max(lo[1], k * PER), min(hi[1], (k + 1) * PER)
            if y1 - y0 < 0.005: continue
            c = V3(((lo[0] + hi[0]) / 2, (y0 + y1) / 2, (lo[2] + hi[2]) / 2))
            o = box((hi[0] - lo[0], y1 - y0, hi[2] - lo[2]), tuple(c), self.M, name=self.fid + '_' + name)
            bm = bmesh.new(); bm.from_mesh(o.data)
            cut = [fc for fc in bm.faces if abs(fc.normal.z) > 0.5 and ((fc.normal.z < 0 and (y0 > lo[1] + 1e-4 or not bot)) or (fc.normal.z > 0 and (y1 < hi[1] - 1e-4 or not cap)))]
            bmesh.ops.delete(bm, geom=cut, context='FACES'); bm.to_mesh(o.data); bm.free(); o.data.update()
            wall_uv2(o, self.A, c, k, outer, inner, edge, upm, ctr); self.P.append(o)

    def floor(self, x0, x1, z0, z1, key, per, upm, y=0.0, top=0.02, edge='pwhite'):
        """a floor in strips along z (v across each strip, u along x): its top at y + top"""
        for k in range(int(math.floor(z0 / per)), int(math.ceil(z1 / per))):
            a, b = max(z0, k * per), min(z1, (k + 1) * per)
            if b - a < 0.005: continue
            c = V3(((x0 + x1) / 2, y + (top - 0.04) / 2, (a + b) / 2))
            o = box((x1 - x0, top + 0.04, b - a), tuple(c), self.M, name=self.fid + '_floor')
            PS.floor_uv(o, self.A, c, k, key, per, upm, edge)
            TR.kill_faces(TR.bake_tf(o), lambda g, n: n.y < 0.5)  # (only its top shows)
            self.P.append(o)


def stepped(name, M, A, prof, z0, z1, tread, riser, side, kill=None, fan=None):
    """a solid stair: the side outline prof [(x, y)] (closed) extruded from z0 to z1; treads (up faces) and risers
    (x faces) from their swatches, the sides from theirs. kill(centre, normal): faces nobody sees (on the ground, on a wall)"""
    bm = bmesh.new()
    F = [bm.verts.new(gv(x, y, z0)) for x, y in prof]; B_ = [bm.verts.new(gv(x, y, z1)) for x, y in prof]
    n = len(prof)
    bm.faces.new(F); bm.faces.new(B_[::-1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((F[i], F[j], B_[j], B_[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ng = [f for f in bm.faces if len(f.verts) > 4]
    if fan is None: bmesh.ops.triangulate(bm, faces=ng, quad_method='BEAUTY', ngon_method='EAR_CLIP')
    else:  # (a fan from one corner: ear clipping makes slivers along the steps' nosing line, where three corners line up)
        for f in ng:
            vs = list(f.verts); nrm = f.normal.copy(); k = [i for i, v in enumerate(vs) if v in (F[fan], B_[fan])][0]; vs = vs[k:] + vs[:k]
            bm.faces.remove(f)
            for i in range(1, len(vs) - 1):
                t_ = bm.faces.new((vs[0], vs[i], vs[i + 1]))
                if t_.normal.dot(nrm) < 0: t_.normal_flip()
    o = _obj(name, bm, M)
    TR.kill_faces(o, kill or (lambda g, nn: nn.y < -0.5 and g.y < 0.01))  # (the underside: on the ground)
    uv_fit(o, A, side, sel=lambda p, Pp: abs(MK._gn(p.normal).z) > 0.5, box=MK._bb(MK._gp(o)))
    uv_fit(o, A, tread, sel=lambda p, Pp: MK._gn(p.normal).y > 0.5)
    uv_fit(o, A, riser, sel=lambda p, Pp: abs(MK._gn(p.normal).x) > 0.5)
    if os.environ.get('JF_DEBUG'): print('JF_STAIR', name, sorted(round(MK._gn(p.normal).x) for p in o.data.polygons if abs(MK._gn(p.normal).x) > 0.5))
    return o


def stair_prof(x0, n, run, rise, dirx, land=None, y0=0.0):
    """the outline of a straight stair: its foot at x0 (y0), n steps going dirx (+1 / -1), the top one stretched to
    land when given. counter-clockwise seen from +z"""
    pts = [(x0, y0)]
    for i in range(n):
        xa = x0 + dirx * i * run; xb = x0 + dirx * (i + 1) * run
        if land is not None and i == n - 1: xb = land
        pts += [(xa, y0 + (i + 1) * rise), (xb, y0 + (i + 1) * rise)]
    pts.append((pts[-1][0], y0))
    return pts


def picnic(K, x0, z0, x1, z1, y, h, key_top='oak', key_leg='oak', along='x'):
    """a picnic table with its benches in one: the top (h), two benches (0.45), A-frame legs. its long side along x"""
    zm = (z0 + z1) / 2; L = x1 - x0
    K.bk((x0 + 0.02, y + h - 0.06, zm - 0.38), (x1 - 0.02, y + h, zm + 0.38), key_top, 'ptop')
    for s in (-1, 1):
        K.bk((x0 + 0.05, y + 0.4, zm + s * 0.62 - 0.14), (x1 - 0.05, y + 0.45, zm + s * 0.62 + 0.14), key_top, 'pbench')
    for xx in (x0 + 0.28, x1 - 0.28):
        for s in (-1, 1):
            o = box_between((xx, y + 0.02, zm + s * 0.72), (xx, y + h - 0.06, zm + s * 0.12), 0.07, 0.05, K.M, K.fid + '_pleg'); uv_fit(o, K.A, key_leg); K.P.append(o)
        K.bk((xx - 0.03, y + 0.36, zm - 0.74), (xx + 0.03, y + 0.42, zm + 0.74), key_leg, 'prail')


def parasol(K, x, z, y, h, key, r=1.25, tilt=0.0):
    """a market parasol through a table: the pole, the striped canopy (8 panels), its ribs' tips, a finial"""
    K.rod((x, y + 0.02, z), (x, y + h + 0.34, z), 0.025, 'pwhite', 'ppole', seg=6)
    o = lathe([(0.03, h + 0.32), (r * 0.55, h + 0.12), (r, h - 0.12), (r, h - 0.16), (0.0, h - 0.0)], (x, y, z), K.M, seg=8, axis='y', name=K.fid + '_canopy', cap=False)
    MK.uv_cyl(o, K.A, key, h - 0.2, h + 0.35, turns=1); K.P.append(o)
    o = ball(0.05, (x, y + h + 0.36, z), K.M, seg=5, rings=3, name=K.fid + '_finial'); K.add(o, 'gold')


def lantern(K, at, arm, GLm):
    """a brass carriage lamp on a gooseneck arm off the wall (arm = the wall's outward direction)"""
    x, y, z = at; ax, az = arm
    K.rod((x, y - 0.2, z), (x + ax * 0.32, y + 0.05, z + az * 0.32), 0.016, 'iron', 'lampgoose', seg=5)
    K.bk((x - 0.02 if ax else x - 0.08, y - 0.28, z - 0.08 if ax else z - 0.02), (x + 0.03 if ax else x + 0.08, y - 0.12, z + 0.08 if ax else z + 0.03), 'iron', 'lampplate')
    c = (x + ax * 0.36, y - 0.12, z + az * 0.36)
    o = lathe([(0.0, 0.0), (0.07, 0.02), (0.09, 0.08), (0.09, 0.3), (0.06, 0.32)], c, K.M, seg=6, axis='y', name=K.fid + '_lampbody', cap=False); K.add(o, 'brass')
    o = lathe([(0.05, 0.05), (0.075, 0.08), (0.075, 0.28), (0.0, 0.29)], c, GLm, seg=6, axis='y', name=K.fid + '_lampglass'); K.add(o, 'bulbw')
    o = lathe([(0.0, 0.42), (0.13, 0.32), (0.06, 0.3)], c, K.M, seg=6, axis='y', name=K.fid + '_lamptop'); K.add(o, 'brass')


def flowerbox(K, x0, x1, z0, z1, y, cols, seed, axis='z'):
    """a window box of flowers: the box, the soil, a bank of leaves along it, blooms dotted over it"""
    K.bk((x0, y, z0), (x1, y + 0.26, z1), 'pwhite', 'wbox')
    K.bk((x0 + 0.03, y + 0.26, z0 + 0.03), (x1 - 0.03, y + 0.275, z1 - 0.03), 'soil', 'wsoil')
    r = random.Random(seed)
    L = (z1 - z0) if axis == 'z' else (x1 - x0); n = max(2, int((L - 0.2) / 0.3))
    c = ((x0 + x1) / 2, y + 0.33, (z0 + z1) / 2)
    o = ball(0.17, c, K.M, scale=((L / 2 - 0.02) / 0.17, 0.75, 1.0) if axis == 'x' else (1.0, 0.75, (L / 2 - 0.02) / 0.17), seg=8, rings=4, name=K.fid + '_leaf', rot=(0, 0.13, 0))
    K.add(o, 'leaf')  # (turned a little: no face square to the box's)
    for i in range(n):
        t = 0.15 + 0.7 * (i + 0.5) / n; dz = r.uniform(-0.05, 0.05); yb = y + 0.37 + r.uniform(-0.015, 0.015)
        q = (c[0] + dz, yb, z0 + (z1 - z0) * t) if axis == 'z' else (x0 + (x1 - x0) * t, yb, c[2] + dz)
        o = ball(0.085, q, K.M, seg=4, rings=2, name=K.fid + '_bloom', rot=(0, 0.4 + r.random(), 0)); K.add(o, cols[i % len(cols)])


def foam(K, c):
    """a pint's head: a disc of foam on the glass (inside its rim, its underside gone)"""
    o = cyl(0.035, 0.03, c, K.M, axis='y', seg=6, name=K.fid + '_head'); K.add(o, 'foam')
    TR.kill_faces(TR.bake_tf(o), lambda g, n: n.y < -0.5); return o


def lifering(K, c, axis, name, r=0.3, tube=0.08):
    """a red and white life ring facing along axis ('x' or 'z'): four red quarters (the band's stripes round it)"""
    o = ring(c, r, tube, K.M, K.A, 'pwhite', K.fid + '_' + name, axis=axis, n=12)
    me = o.data; uv = MK._uvl(o); P = MK._gp(o); u0, v0, u1, v1 = K.A.uvrect('ringband')
    for poly in me.polygons:
        ls = []
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; p = P[vi]; a_ = (p.z - c[2]) if axis == 'x' else (p.x - c[0]); b_ = p.y - c[1]
            ls.append([li, math.atan2(b_, a_) / TAU, v0 + (v1 - v0) * (0.1 + 0.8 * (vi % 6) / 5)])  # (v round the tube: sweep makes ring after ring of 6)
        ref = ls[0][1]
        for e in ls:
            while e[1] - ref > 0.5: e[1] -= 1
            while e[1] - ref < -0.5: e[1] += 1
        for li, a_, v in ls: uv[li].uv = (a_, v)
    K.P.append(o); return o


# ============================================================ p_pj_pub: THE SINKING FEELING
def pub_atlas(fid):
    A = Atlas(fid + '_atlas', 256, 512)
    A.band('render', 16, flat_c(0xfbf8f0, 0.02, 11)); A.band('plinth', 16, paint_plinth(0xfbf8f0, 0x1f3a8a, 0xffc83a))
    A.band('fnavy', 16, flat_c(0x1f3a8a, 0.025, 13)); A.band('fnavy0', 16, paint_plinth(0x1f3a8a, 0x152a6a, 0xffc83a, frac=0.55))
    A.band('wains0', 16, paint_panelling(bottom=True)); A.band('wains', 16, paint_panelling(top=True)); A.band('inwall', 16, flat_c(0xf6e8c8, 0.02, 17))
    A.band('carpet', 16, paint_carpet); A.band('boards', 16, paint_boards(0xb07a48, 0x4a2a18, 19)); A.band('deck', 16, paint_boards(0xd8a868, 0x6a4a2a, 21, nails=True))
    A.band('hull', 16, paint_hull); A.band('barfront', 16, lambda px: paint_barfront(px)); A.band('bottles', 32, paint_bottles)
    A.band('stripeN', 8, paint_stripes_v(0x1f3a8a, 0xfbf8f0)); A.band('stripeY', 8, paint_stripes_v(0xffd21a, 0xfbf8f0)); A.band('ringband', 8, paint_stripes_v(0xe0302a, 0xfbf8f0, 8))
    A.cell('sign', 256, 18, paint_board(['THE SINKING FEELING'], 0x1f3a8a, 0xffc83a, scale=2, shadow=0x0e1a40))
    A.cell('roofsign', 176, 10, paint_board(['ROOF BEER GARDEN (NO GARDEN)'], 0xfbf8f0, 0x1f3a8a))
    A.cell('transom', 40, 18, paint_board(['LAST', 'ORDERS'], 0xfbf8f0, 0x1f3a8a, cols=[0x1f3a8a, 0xd8283a]))
    A.cell('hang', 48, 60, paint_hang)
    A.cell('quiz', 48, 44, paint_chalk(['QUIZ', 'NIGHT', 'EVERY', 'ANSWER', 'IS FISH'], [0xffe14d, 0xffe14d, 0xf4f2ee, 0xf4f2ee, 0xff4fd8]))
    A.cell('darts', 104, 20, paint_board(['AIM FOR THE BOARD', '(NOT DAVE)'], 0xfff2d8, 0x1f3a8a, border=0x1f3a8a, cols=[0x1f3a8a, 0xd8283a]))
    A.cell('dboard', 32, 32, paint_dartboard)
    A.cell('mirror', 72, 20, paint_board(['NO SWIMMING', 'IN THE BEER'], 0x8ab8c8, 0xffc83a, border=0xffc83a, shadow=0x3a5a6a))
    A.cell('stairs', 80, 20, paint_board(['TOP DECK', 'MIND THE BOAT'], 0x1f3a8a, 0xfbf8f0, border=0xffc83a, cols=[0xffc83a, 0xfbf8f0]))
    A.cell('juke', 24, 32, paint_juke)
    A.cell('facade1', 64, 32, paint_facade_pub)
    A.cell('stained', 32, 8, paint_stained)
    A.cell('chalk', 32, 36, paint_chalk(['DAVE', '0', 'ME', '501'], [0xffe14d, 0xf4f2ee, 0xffe14d, 0xf4f2ee]))
    A.cell('cola', 112, 31, paint_cola)
    A.cell('mural', 80, 28, paint_board(['COLD BEER', 'WARM WELCOME', 'DAMP FLOOR'], 0x2a8ad8, 0xfbf8f0, border=0xfbf8f0, cols=[0xffe14d, 0xfbf8f0, 0xffe14d]))
    swatches(A, (('pwhite', 0xfbf8f0, 0.02, None), ('cream', 0xfff2d8, 0.02, None), ('pnavy', 0x1f3a8a, 0.02, None), ('navyd', 0x152a6a, 0.02, None),
                 ('gold', 0xffc83a, 0.03, None), ('chrome', 0xdde3ea, 0.03, None), ('vinyl', 0xc8283a, 0.03, None), ('pwood', 0x6a3420, 0.05, None),
                 ('woodtop', 0x8a4a28, 0.04, None), ('oak', 0xc89058, 0.05, None), ('ceiling', 0xf8f0de, 0.015, None), ('tile', 0xe07848, 0.03, None),
                 ('terra', 0xc85a32, 0.04, None), ('keg', 0xc8ccd4, 0.03, None), ('beer', 0xf0a020, 0.03, None), ('foam', 0xfff8e8, 0.02, None),
                 ('leaf', 0x3fae3a, 0.06, None), ('flowerp', 0xff4fd8, 0.03, None), ('flowery', 0xffe14d, 0.03, None), ('flowerw', 0xfdf6fa, 0.02, None),
                 ('soil', 0x5a3e2c, 0.08, None), ('iron', 0x24242c, 0.04, None), ('bulbw', 0xfff0b0, 0.0, None), ('glowp', 0xff4fd8, 0.0, None),
                 ('glowc', 0x4fd8ff, 0.0, None), ('glowa', 0xffb030, 0.0, None), ('port', 0x8ad0ff, 0.02, None), ('hullred', 0xd8283a, 0.03, None),
                 ('boatin', 0x6ac0e8, 0.03, None), ('motor', 0xe8302a, 0.03, None), ('motorg', 0x3a3a44, 0.04, None), ('splinter', 0xe8c890, 0.06, None),
                 ('chalkb', 0x1e2a26, 0.05, None), ('side1', 0xfbf8f0, 0.02, None), ('deck1', 0xd8a868, 0.03, None), ('bricktop', 0xc0604a, 0.05, None),
                 ('sky', 0x8ad8ff, 0.0, None)))
    return A


def boat(K, rt, H):
    """LAST ORDERS: an open launch, built upright in its own frame (x aft, its bow toward -x, y up from the keel, z
    across), then tipped bow-down by th and set so its transom's foot is at (KU, KY): the part above the terrace and
    the bow that comes down through the ceiling (the slab in between hides the rest)"""
    th = math.radians(62); ct, st_ = math.cos(th), math.sin(th)
    KU, KY, ZC, L = 3.0, 7.4, -5.6, 4.8  # (near the front: her name and outboard face the street)
    def place(g): return V3((KU + g.x * ct - g.y * st_, KY + g.x * st_ + g.y * ct, ZC + g.z))
    def beam(s): return 1.15 * (0.82 + 0.18 * min(1, s / 1.4) * (2 - min(1, s / 1.4)) if s <= 1.4 else max(0.0, 1.0 - ((s - 1.4) / (L - 1.4)) ** 2))
    def depth(s): return 1.15 + 0.3 * (s / L) ** 2
    def keel(s): return 0.35 * ((s - 2.0) / (L - 2.0)) ** 2 if s > 2.0 else 0.0
    rel = [(0.0, 0.0), (0.48, 0.05), (0.8, 0.18), (0.96, 0.45), (1.0, 0.75), (1.02, 1.0)]
    U = [(-w, h) for w, h in rel[::-1]] + [(w, h) for w, h in rel[1:]]  # port gunwale -> keel -> starboard gunwale
    def ringpts(s, inset=0.0):
        b, D, k = beam(s), depth(s), keel(s)
        return [V3((-s, k + (D - k) * h + (inset if h < 0.99 else 0.0), max(0.0, b * abs(w) - inset) * (1 if w >= 0 else -1))) for w, h in U]
    def shell(name, ss, inset, key, hull_uv, flip=False):
        bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); u0, v0, u1, v1 = K.A.uvrect(key)
        R = [[bm.verts.new(gv(*p)) for p in ringpts(s, inset)] for s in ss]
        for i in range(len(ss) - 1):
            for j in range(len(U) - 1):
                q = [R[i][j], R[i][j + 1], R[i + 1][j + 1], R[i + 1][j]]
                if len({id(v) for v in q}) < 4: continue
                try: f = bm.faces.new(q[::-1] if flip else q)
                except ValueError: continue
                for lp, (ii, jj) in zip(f.loops, ([(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)][::-1] if flip else [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)])):
                    hh = U[jj][1]
                    lp[uvl].uv = (ss[ii] * 0.12, v0 + (v1 - v0) * hh) if hull_uv else (u0 + (u1 - u0) * (0.2 + 0.6 * (jj / (len(U) - 1))), v0 + (v1 - v0) * (0.2 + 0.6 * ii / (len(ss) - 1)))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        return _obj(K.fid + '_' + name, bm, K.M)
    up_ss = [0.0, 0.35, 0.8, 1.3, 1.8, 2.3, 2.8, 3.3]
    outer = shell('hull', up_ss, 0.0, 'hull', True)
    inner = shell('hullin', up_ss, 0.05, 'boatin', False, flip=True)
    parts = [outer, inner]
    # the transom: a board closing the stern, its name aft; the gunwales' rubbing strakes; the thwarts; the outboard
    tp = ringpts(0.0)
    bm = bmesh.new(); fa = [bm.verts.new(gv(0.0, p.y, p.z)) for p in tp]; fb = [bm.verts.new(gv(-0.05, p.y, p.z)) for p in tp]
    f1 = bm.faces.new(fa); f2 = bm.faces.new(fb)  # (its two faces only: the edge between them is the hull's own)
    f1.normal_update(); f2.normal_update()
    if MK._gn(f1.normal).x < 0: f1.normal_flip()
    if MK._gn(f2.normal).x > 0: f2.normal_flip()
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    tr = _obj(K.fid + '_transom', bm, K.M); uv_fit(tr, K.A, 'pwhite'); parts.append(tr)
    o = box((0.03, 0.5, 1.1), (0.015, 0.62, -0.38), K.M, name=K.fid + '_name'); uv_fit(o, K.A, 'pwhite'); uv_fit(o, K.A, 'transom', sel=lambda p, Pp: MK._gn(p.normal).x > 0.5); parts.append(o)
    for side_ in (-1, 1):
        pts = [(-s, depth(s) + 0.01, side_ * beam(s) * 1.02) for s in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.4)]
        o = sweep(pts, 0.05, K.M, seg=6, name=K.fid + '_gunwale', cap=True); uv_fit(o, K.A, 'pnavy'); parts.append(o)
    o = rod((0.01, 1.16, -0.92), (0.01, 1.16, 0.92), 0.045, K.M, seg=6, name=K.fid + '_transomcap'); uv_fit(o, K.A, 'pnavy'); parts.append(o)
    for s, hh in ((0.25, 0.62), (1.0, 0.58), (2.0, 0.6)):
        w = beam(s) * 0.97; o = box((0.26, 0.05, 2 * w), (-s, hh, 0), K.M, name=K.fid + '_thwart'); uv_fit(o, K.A, 'oak'); parts.append(o)
    mo, mz = [], 0.52  # the outboard (a big one), clamped on the transom off to starboard: bracket, cowl, leg, plate, gearcase, prop, tiller
    mo.append(boxk((0.14, 0.3, 0.22), (0.07, 1.07, mz), K.M, K.A, 'motorg', K.fid + '_obracket'))
    mo.append(boxk((0.5, 0.52, 0.38), (0.33, 1.43, mz), K.M, K.A, 'motor', K.fid + '_ocowl', bev=0.08))
    mo.append(boxk((0.52, 0.06, 0.4), (0.33, 1.22, mz), K.M, K.A, 'pwhite', K.fid + '_ostripe'))
    mo.append(boxk((0.16, 1.45, 0.12), (0.26, 0.45, mz), K.M, K.A, 'motorg', K.fid + '_oleg'))
    mo.append(boxk((0.42, 0.03, 0.26), (0.3, -0.13, mz), K.M, K.A, 'motorg', K.fid + '_oplate'))
    o = cyl(0.075, 0.36, (0.3, -0.3, mz), K.M, axis='x', seg=8, name=K.fid + '_ogear'); uv_fit(o, K.A, 'motorg'); mo.append(o)
    o = cyl(0.04, 0.08, (0.51, -0.3, mz), K.M, axis='x', seg=8, name=K.fid + '_ohub'); uv_fit(o, K.A, 'gold'); mo.append(o)
    for k in range(3):
        a = TAU * k / 3 + 0.3
        o = box((0.03, 0.22, 0.1), (0.53, -0.3 + math.cos(a) * 0.13, mz + math.sin(a) * 0.13), K.M, rot=(a, 0, 0.35), name=K.fid + '_oblade'); uv_fit(o, K.A, 'gold'); mo.append(o)
    o = rod((0.12, 1.28, mz), (-0.55, 1.36, mz), 0.03, K.M, seg=6, name=K.fid + '_otiller'); uv_fit(o, K.A, 'motorg'); mo.append(o)
    o = rod((-0.4, 1.35, mz), (-0.62, 1.37, mz), 0.045, K.M, seg=6, name=K.fid + '_ogrip'); uv_fit(o, K.A, 'motor'); mo.append(o)
    parts += mo
    # her flag, still flying, on a staff at the transom's corner
    o = rod((-0.06, 1.1, -0.85), (-0.06, 1.95, -0.85), 0.018, K.M, seg=5, name=K.fid + '_flagstaff'); uv_fit(o, K.A, 'pwhite'); parts.append(o)
    o = side([(0.0, 1.93), (-0.0, 1.6), (0.5, 1.765)], 0.015, (-0.06, 0, -0.85), K.M, name=K.fid + '_flag'); uv_fit(o, K.A, 'flowerp')
    o.data.transform(Matrix.Rotation(math.pi / 2, 4, 'Z')); parts.append(o)  # (side() draws in z, y: turn it to stream aft along x)
    for o in parts: gx(o, place)
    keep = []
    for o in parts:
        clip(o, lo=rt + 0.005)
        if len(o.data.polygons): keep.append(o)
        else: bpy.data.objects.remove(o, do_unlink=True)
    # the bow, down through the ceiling over the bar: the hull's front, cut at the ceiling
    bow = shell('bow', [2.3, 2.8, 3.3, 3.8, 4.2, 4.5, L], 0.0, 'hull', True)
    gx(bow, place); clip(bow, hi=H - 0.005); keep.append(bow)
    # splinters: broken deck boards round the hole it made, and broken ceiling round it underneath
    r = random.Random(17)
    for i in range(9):
        a = TAU * i / 9 + r.uniform(-0.2, 0.2); cx_, cz_ = KU - 2.25 + math.cos(a) * 0.75, ZC + math.sin(a) * 1.3
        o = box_between((cx_, rt + 0.02, cz_), (cx_ + math.cos(a) * 0.45, rt + 0.12 + r.uniform(0.0, 0.18), cz_ + math.sin(a) * 0.45), 0.11, 0.03, K.M, K.fid + '_splinter')
        uv_fit(o, K.A, 'splinter'); keep.append(o)
        o = box_between((cx_ + 0.2, H - 0.01, cz_), (cx_ + 0.2 + math.cos(a) * 0.35, H - 0.12 - r.uniform(0.0, 0.12), cz_ + math.sin(a) * 0.35), 0.13, 0.03, K.M, K.fid + '_plaster')
        uv_fit(o, K.A, 'ceiling'); keep.append(o)
    K.P += keep
    if os.environ.get('JF_DEBUG'):  # the boat above the deck, per metre along x: how high it gets (its boxes follow)
        for u0 in [x * 0.5 for x in range(-12, 8)]:
            ys = [(v.co).z for o in keep if o is not bow for v in o.data.vertices if u0 <= (v.co).x < u0 + 0.5]
            zs = [-(v.co).y for o in keep if o is not bow for v in o.data.vertices if u0 <= (v.co).x < u0 + 0.5]
            if ys: print('JF_BOAT', u0, round(max(ys) - rt, 2), round(min(zs), 2), round(max(zs), 2))
        print('JF_BOW', [round(f(((v.co).x for v in bow.data.vertices)), 2) for f in (min, max)], [round(f(((v.co).z for v in bow.data.vertices)), 2) for f in (min, max)])
    # far LOD: the hull as a wedge, its stern up
    q = box_between((KU - 2.3, rt - 0.1, ZC), (KU - 1.0, 8.4, ZC), 2.2, 1.0, K.M, K.fid + '1_boat'); uv_fit(q, K.A, 'hullred'); K.Q.append(q)


def boxk(size, pos, M, A, key, name, bev=0.0, rot=None):
    o = box(size, pos, M, bev=bev, rot=rot, name=name); uv_fit(o, A, key); return o


@prop('p_pj_pub')
def build_pub():
    fid = 'pjp'; P = PJP['pub']
    hw, hd, t, H = P['w'] / 2, P['d'] / 2, P['t'], P['h']; rt = H + P['roof']; pt = P['pt']; ptop = rt + P['par']; fx0 = hw - t
    dw, dh = P['door']; (a0, a1), (b0, b1) = P['wins']; sl, hh = P['sill'], P['head']; k0, k1, kh = P['back']
    St = P['stair']; lx = St['x0'] - St['n'] * St['run']; srise = rt / St['n']
    A = pub_atlas(fid); img = A.image()
    M = mat(fid, 0xffffff, rough=0.38, tex=img, clearcoat=0.45)
    GL = mat('glow', 0xffffff, emit=0xffffff, strength=2.2, tex=img, emit_tex=True)
    K = Kit(fid, A, M, GL)
    # ---- the walls (the boxes' pieces exactly): the navy pub front, white render round the sides and back, panelling in
    FR = lambda k: 'fnavy0' if k == 0 else 'fnavy'
    SD = lambda k: 'plinth' if k == 0 else 'render'
    IN = lambda k: 'wains0' if k == 0 else 'wains' if k == 1 else 'inwall'
    RN = lambda k: 'render'
    for lo, hi in (((fx0, 0, -hd), (hw, H, a0)), ((fx0, 0, a0), (hw, sl, a1)), ((fx0, hh, a0), (hw, H, a1)), ((fx0, 0, a1), (hw, H, -dw)),
                   ((fx0, dh, -dw), (hw, H, dw)), ((fx0, 0, dw), (hw, H, b0)), ((fx0, 0, b0), (hw, sl, b1)), ((fx0, hh, b0), (hw, H, b1)), ((fx0, 0, b1), (hw, H, hd))):
        K.wall(lo, hi, 'front', FR, IN, 'cream', cap=False)
    for lo, hi in (((-hw, 0, -hd), (-hw + t, H, k0)), ((-hw, 0, k1), (-hw + t, H, hd)), ((-hw, kh, k0), (-hw + t, H, k1))):
        K.wall(lo, hi, 'back', SD, IN, 'pwhite', cap=False)
    for z0, (w0, w1) in ((-hd, P['nwin']), (hd - t, P['swin'])):
        for lo, hi in (((-hw + t, 0, z0), (w0, H, z0 + t)), ((w0, 0, z0), (w1, sl, z0 + t)), ((w0, hh, z0), (w1, H, z0 + t)), ((w1, 0, z0), (fx0, H, z0 + t))):
            K.wall(lo, hi, 'side', SD, IN, 'pwhite', cap=False)
    for lo, hi in (((hw - pt, rt, -hd), (hw, ptop, hd)), ((-hw, rt, -hd), (-hw + pt, ptop, hd)), ((-hw + pt, rt, -hd), (hw - pt, ptop, -hd + pt)),
                   ((-hw + pt, rt, hd - pt), (St['land'], ptop, hd)), ((lx, rt, hd - pt), (hw - pt, ptop, hd))):
        K.wall(lo, hi, 'parapet', RN, RN, 'pwhite', cap=False)
    # the roof slab (the ceiling under it), the decking on it; floors: the carpet, boards behind the bar; beams
    ro = K.bk((-hw, H, -hd), (hw, rt, hd), 'pwhite', 'roof'); uv_fit(ro, A, 'ceiling', sel=lambda p, Pp: MK._gn(p.normal).y < -0.5)
    TR.kill_faces(TR.bake_tf(ro), lambda g, n: n.y > 0.5)
    K.floor(-hw + 0.1, hw - 0.1, -hd + 0.1, hd - 0.1, 'deck', 0.8, UPM, y=rt)
    K.floor(-3.4, hw - 0.1, -hd + 0.1, hd - 0.1, 'carpet', 0.8, UPM)
    K.floor(-hw + 0.1, -3.4, -hd + 0.1, hd - 0.1, 'boards', 0.8, UPM)
    for z in (-3.6, -0.6, 2.4, 5.4): K.bk((-hw + 0.1, H - 0.24, z - 0.1), (hw - 0.1, H + 0.05, z + 0.1), 'pwood', 'beam')
    # ---- the pub front: pilasters (gold capitals), the fascia with the name, the cornice, the roof line, the parapet's caps
    for z0, z1 in ((-hd, a0), (a1, -dw), (dw, b0), (b1, hd)):
        m0, m1 = z0 + 0.06, z1 - 0.06
        K.bk((hw - 0.02, 0.26, m0), (hw + 0.08, 2.86, m1), 'pnavy', 'pilaster', bev=0.012)
        K.bk((hw - 0.02, 0.0, m0 - 0.03), (hw + 0.12, 0.26, m1 + 0.03), 'navyd', 'pbase')
        K.bk((hw - 0.02, 2.86, m0 - 0.04), (hw + 0.14, 2.98, m1 + 0.04), 'gold', 'capital')
    sg = K.bk((hw - 0.02, 2.98, -hd + 0.02), (hw + 0.12, 3.84, hd - 0.02), 'pnavy', 'fascia', bev=0.01)
    uv_fit(sg, A, 'sign', sel=lambda p, Pp: MK._gn(p.normal).x > 0.5)
    for y0, y1 in ((2.97, 3.02), (3.8, 3.85)): K.bk((hw + 0.1, y0, -hd + 0.03), (hw + 0.15, y1, hd - 0.03), 'gold', 'fmould')
    for z in (-hd, hd): K.bk((hw - 0.03, 2.9, z - 0.1), (hw + 0.2, 3.9, z + 0.1), 'pnavy', 'console', bev=0.03)
    K.bk((hw - 0.02, 3.9, -hd - 0.08), (hw + 0.24, 4.06, hd + 0.08), 'cream', 'cornice', bev=0.02)
    K.bk((hw - 0.02, 4.06, -hd - 0.04), (hw + 0.1, 4.52, hd + 0.04), 'pnavy', 'roofline')
    cap = lambda lo, hi: K.bk(lo, hi, 'pnavy', 'pcap')
    cap((hw - pt - 0.03, ptop, -hd - 0.04), (hw + 0.05, ptop + 0.07, hd + 0.04)); cap((-hw - 0.05, ptop, -hd - 0.04), (-hw + pt + 0.03, ptop + 0.07, hd + 0.04))
    cap((-hw + pt + 0.03, ptop, -hd - 0.04), (hw - pt - 0.03, ptop + 0.07, -hd + pt + 0.03))
    cap((-hw + pt + 0.03, ptop, hd - pt - 0.03), (St['land'], ptop + 0.07, hd + 0.04)); cap((lx, ptop, hd - pt - 0.03), (hw - pt - 0.03, ptop + 0.07, hd + 0.04))
    o = K.bk((hw - 0.01, 4.72, -5.0), (hw + 0.03, 5.28, 5.0), 'pwhite', 'roofsign'); uv_fit(o, A, 'roofsign', sel=lambda p, Pp: MK._gn(p.normal).x > 0.5)
    # the windows: cream frames, sills, a transom bar, stained-glass top lights with mullions, window boxes
    for z0, z1, seed in ((a0, a1, 1), (b0, b1, 2)):
        K.bk((fx0 - 0.04, sl - 0.05, z0 - 0.1), (hw + 0.16, sl + 0.04, z1 + 0.1), 'cream', 'sill')
        for z, s_ in ((z0, 1), (z1, -1)): K.bk((fx0 - 0.02, sl + 0.04, min(z, z + s_ * 0.1)), (hw + 0.07, hh, max(z, z + s_ * 0.1)), 'cream', 'jamb')
        K.bk((fx0 - 0.02, hh - 0.06, z0 + 0.1), (hw + 0.07, hh, z1 - 0.1), 'cream', 'whead')
        K.bk((hw - 0.14, 2.3, z0 + 0.1), (hw - 0.04, 2.37, z1 - 0.1), 'cream', 'transombar')
        K.bk((hw - 0.11, 2.37, z0 + 0.1), (hw - 0.07, hh - 0.06, z1 - 0.1), 'stained', 'toplight')
        for k in (1, 2):
            zm = z0 + 0.1 + (z1 - z0 - 0.2) * k / 3
            K.bk((hw - 0.13, 2.36, zm - 0.03), (hw - 0.05, hh - 0.05, zm + 0.03), 'cream', 'mullion')
        flowerbox(K, hw + 0.03, hw + 0.33, z0 + 0.15, z1 - 0.15, sl - 0.36, ['flowerp', 'flowery', 'flowerw'], seed)
    for (w0, w1), zf, s_ in ((P['nwin'], -hd, -1), (P['swin'], hd, 1)):  # the side windows
        K.bk((w0 - 0.1, sl - 0.05, min(zf, zf + s_ * 0.16)), (w1 + 0.1, sl + 0.04, max(zf, zf + s_ * 0.16)), 'cream', 'sill')
        K.bk((w0, hh - 0.06, min(zf, zf - s_ * 0.27)), (w1, hh, max(zf, zf - s_ * 0.27)), 'cream', 'whead')
        for x, d_ in ((w0, 1), (w1, -1)): K.bk((min(x, x + d_ * 0.09), sl + 0.04, min(zf, zf - s_ * 0.27)), (max(x, x + d_ * 0.09), hh - 0.06, max(zf, zf - s_ * 0.27)), 'cream', 'jamb')
        flowerbox(K, w0 + 0.15, w1 - 0.15, min(zf + s_ * 0.03, zf + s_ * 0.33), max(zf + s_ * 0.03, zf + s_ * 0.33), sl - 0.36, ['flowerp', 'flowery', 'flowerw'], 3 + s_, axis='x')
    # the double doors, swung in: navy, a porthole in each, brass kick plates; the brass threshold; lamps either side
    for s_ in (-1, 1):
        z0_ = s_ * dw + (0.01 if s_ > 0 else -0.06); z1_ = z0_ + 0.05
        K.bk((fx0 - 0.88, 0.04, z0_), (fx0 - 0.01, dh - 0.06, z1_), 'pnavy', 'door')
        K.bk((fx0 - 0.85, 0.06, z0_ - 0.01), (fx0 - 0.04, 0.32, z1_ + 0.01), 'brass', 'kick')
        o = cyl(0.16, 0.07, (fx0 - 0.45, 1.65, (z0_ + z1_) / 2), M, axis='z', seg=8, name=fid + '_porthole'); K.add(o, 'brass')
        o = cyl(0.12, 0.08, (fx0 - 0.45, 1.65, (z0_ + z1_) / 2), M, axis='z', seg=8, name=fid + '_portglass'); K.add(o, 'port')
    K.bk((fx0 - 0.05, 0.0, -dw), (hw + 0.1, 0.035, dw), 'brass', 'thresh')
    for z in (-1.45, 1.45): lantern(K, (hw + 0.02, 2.62, z), (1, 0), GL)
    # hanging baskets on the corner piers; the hanging sign on its bracket off the north corner
    for z in (-7.3, 7.3):
        K.rod((hw + 0.06, 2.92, z), (hw + 0.62, 2.92, z), 0.018, 'iron', 'hbracket', seg=5)
        K.rod((hw + 0.06, 2.62, z), (hw + 0.4, 2.92, z), 0.012, 'iron', 'hstay', seg=4)
        K.rod((hw + 0.56, 2.92, z), (hw + 0.56, 2.62, z), 0.008, 'iron', 'hchain', seg=4)
        o = lathe([(0.0, 2.3), (0.17, 2.32), (0.25, 2.45), (0.27, 2.56)], (hw + 0.56, 0, z), M, seg=8, axis='y', name=fid + '_basket', cap=False); K.add(o, 'iron')
        o = ball(0.27, (hw + 0.56, 2.58, z), M, scale=(1.0, 0.55, 1.0), seg=8, rings=4, name=fid + '_bushy'); K.add(o, 'leaf')
        r = random.Random(int(z * 10))
        for i in range(5):
            a = TAU * i / 5
            o = ball(0.08, (hw + 0.56 + math.cos(a) * 0.22, 2.62 + r.uniform(-0.04, 0.06), z + math.sin(a) * 0.22), M, seg=6, rings=3, name=fid + '_bloom')
            K.add(o, ['flowerp', 'flowery', 'flowerw', 'flowerp'][i % 4])
        for i in range(2):
            a = TAU * i / 2 + 0.5
            o = ball(0.09, (hw + 0.56 + math.cos(a) * 0.24, 2.32, z + math.sin(a) * 0.24), M, scale=(0.8, 1.6, 0.8), seg=5, rings=3, name=fid + '_trail'); K.add(o, 'leaf')
    zs = -hd - 0.12
    K.rod((hw + 0.02, 3.97, zs), (hw + 1.4, 3.97, zs), 0.022, 'iron', 'sbracket', seg=6)
    K.rod((hw + 0.02, 3.35, zs), (hw + 0.8, 3.97, zs), 0.016, 'iron', 'sstay', seg=5)
    for x in (hw + 0.38, hw + 1.22): K.rod((x, 3.97, zs), (x, 3.85, zs), 0.008, 'iron', 'schain', seg=4)
    o = ball(0.05, (hw + 1.42, 3.97, zs), M, seg=6, rings=4, name=fid + '_sknob'); K.add(o, 'gold')
    o = K.bk((hw + 0.25, 2.72, zs - 0.03), (hw + 1.35, 3.85, zs + 0.03), 'gold', 'hangsign', bev=0.008)
    uv_fit(o, A, 'hang', sel=lambda p, Pp: abs(MK._gn(p.normal).z) > 0.5)
    # the mural on the north side; downpipes off the terrace at the back corners; the back door, a lamp over it
    o = K.bk((-5.5, 1.2, -hd - 0.03), (-1.7, 2.6, -hd + 0.02), 'pwhite', 'mural'); uv_fit(o, A, 'mural', sel=lambda p, Pp: MK._gn(p.normal).z < -0.5)
    o = K.bk((-hw - 0.03, 1.0, -6.6), (-hw + 0.02, 3.2, 1.4), 'pwhite', 'cola'); uv_fit(o, A, 'cola', sel=lambda p, Pp: MK._gn(p.normal).x < -0.5)
    for z in (-hd + 0.45, hd - 0.45):
        o = cyl(0.06, ptop - 0.5, (-hw - 0.12, (ptop - 0.5) / 2 + 0.1, z), M, axis='y', seg=8, name=fid + '_pipe'); K.add(o, 'pwhite')
        K.bk((-hw - 0.2, ptop - 0.48, z - 0.08), (-hw + 0.02, ptop - 0.36, z + 0.08), 'pwhite', 'scupper')
        K.bk((-hw - 0.22, 0.02, z - 0.08), (-hw - 0.04, 0.14, z + 0.08), 'pwhite', 'shoe')
    K.bk((-hw + t - 0.01, 0.04, k1 + 0.0), (-hw + t + 1.3, kh - 0.08, k1 + 0.05), 'pnavy', 'bdoor')
    for z, s_ in ((k0, 1), (k1, -1)): K.bk((-hw - 0.06, 0.03, min(z, z + s_ * 0.08)), (-hw + t + 0.02, kh, max(z, z + s_ * 0.08)), 'cream', 'bjamb')
    K.bk((-hw - 0.06, kh - 0.01, k0 - 0.08), (-hw + t + 0.02, kh + 0.1, k1 + 0.08), 'cream', 'bhead')
    o = box((0.12, 0.16, 0.3), (-hw - 0.06, kh + 0.35, (k0 + k1) / 2), GL, name=fid + '_bulkhead'); K.add(o, 'bulbw')
    # ---- the stair up the south side to the terrace: white render, terracotta treads, a navy rail; the landing on struts
    prof = stair_prof(St['x0'], St['n'], St['run'], srise, -1)
    o = stepped(fid + '_stair', M, A, prof, St['z0'], St['z1'], 'tile', 'pwhite', 'pwhite', kill=lambda g, n: (n.y < -0.5 and g.y < 0.01) or n.z < -0.5, fan=len(prof) - 1)
    K.P.append(o)
    o = K.bk((St['land'], H, St['z0']), (lx - 0.002, rt, St['z1']), 'pwhite', 'landing'); uv_fit(o, A, 'tile', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5)
    TR.kill_faces(TR.bake_tf(o), lambda g, n: n.z < -0.5 or n.x > 0.5)
    zr = St['z1'] - 0.06
    for i in range(0, St['n'], 3):
        x = St['x0'] - (i + 0.5) * St['run']; K.rod((x, (i + 1) * srise, zr), (x, (i + 1) * srise + 0.95, zr), 0.022, 'pnavy', 'spost', seg=6)
    K.rod((St['x0'] - 0.5 * St['run'], srise + 0.95, zr), (lx, rt + 0.95, zr), 0.03, 'pnavy', 'srail', seg=6)
    for a_, b_ in (((lx, rt + 0.95, zr), (St['land'] + 0.06, rt + 0.95, zr)), ((St['land'] + 0.06, rt + 0.95, zr), (St['land'] + 0.06, rt + 0.95, St['z0'] + 0.06))):
        K.rod(a_, b_, 0.03, 'pnavy', 'lrail', seg=6)
    for x_, z_ in ((St['land'] + 0.06, zr), (St['land'] + 0.06, St['z0'] + 0.06), (lx - 0.05, zr)): K.rod((x_, rt, z_), (x_, rt + 0.95, z_), 0.022, 'pnavy', 'lpost', seg=6)
    for x in (St['land'] + 0.25, lx - 0.25):
        o = box_between((x, 2.9, St['z0'] + 0.02), (x, H - 0.02, St['z1'] - 0.15), 0.08, 0.08, M, fid + '_strut'); K.add(o, 'pnavy')
    o = K.bk((2.2, 0.5, St['z1'] - 0.01), (4.2, 1.0, St['z1'] + 0.03), 'pnavy', 'stairsign'); uv_fit(o, A, 'stairs', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5)
    # ---- inside: the bar (panelled, a polished top, a brass foot rail), hand pumps, the tap tower, pints, the till
    c0, cz0, c1, cz1, ch = P['inside'][1]
    o = K.bk((c0 + 0.05, 0.0, cz0 + 0.01), (c1 - 0.02, ch - 0.06, cz1), 'pwood', 'counter')
    uv_trim(o, A, 'barfront', upm=UPM, grain='z', sel=lambda p, Pp: MK._gn(p.normal).x > 0.5); TR.kill_faces(o, lambda g, n: n.y < -0.5)
    K.bk((c0 - 0.04, ch - 0.06, cz0 + 0.01), (c1 + 0.08, ch, cz1 + 0.08), 'woodtop', 'bartop', bev=0.02)
    K.rod((c1 + 0.16, 0.22, cz0 + 0.15), (c1 + 0.16, 0.22, cz1 - 0.05), 0.025, 'brass', 'footrail', seg=8)
    for z in (cz0 + 0.6, -3.6, -0.6, cz1 - 0.3): K.rod((c1 - 0.03, 0.22, z), (c1 + 0.16, 0.22, z), 0.014, 'brass', 'railbk', seg=5)
    for z in (-1.7, -1.3, -0.9):
        K.bk((-3.06, ch, z - 0.05), (-2.94, ch + 0.06, z + 0.05), 'chrome', 'pumpbase')
        o = lathe([(0.03, 0.0), (0.036, 0.05), (0.024, 0.09), (0.032, 0.32), (0.02, 0.36), (0.0, 0.37)], (-3.0, ch + 0.06, z), M, seg=6, axis='y', name=fid + '_pump'); K.add(o, 'pwood')
        o = cyl(0.034, 0.03, (-3.0, ch + 0.2, z), M, axis='y', seg=6, name=fid + '_pumpband'); K.add(o, 'gold')
    K.rod((-3.0, ch + 0.01, -4.2), (-3.0, ch + 0.38, -4.2), 0.03, 'chrome', 'tower', seg=8)
    K.rod((-3.0, ch + 0.38, -4.55), (-3.0, ch + 0.38, -3.85), 0.035, 'chrome', 'tbar', seg=8)
    for z, key in ((-4.45, 'glowa'), (-4.2, 'glowp'), (-3.95, 'glowc')):
        K.rod((-2.96, ch + 0.38, z), (-2.88, ch + 0.26, z), 0.012, 'chrome', 'tap', seg=5)
        o = box((0.03, 0.12, 0.09), (-3.0, ch + 0.465, z), GL, name=fid + '_badge'); K.add(o, key)
    K.bk((-3.1, ch, -4.6), (-2.85, ch + 0.02, -3.8), 'chrome', 'drip')
    for z in (-3.1, -2.7, 0.4, 1.6):
        o = lathe([(0.0, 0.0), (0.036, 0.0), (0.042, 0.14), (0.0, 0.14)], (-2.85, ch, z), M, seg=6, axis='y', name=fid + '_pint'); K.add(o, 'beer')
        o = foam(K, (-2.85, ch + 0.155, z))
    K.bk((-3.25, ch, -6.9), (-2.85, ch + 0.2, -6.4), 'brass', 'till')
    K.bk((-3.25, ch + 0.2, -6.85), (-3.05, ch + 0.38, -6.45), 'brass', 'tilltop')
    # the back bar: cupboards, the bottle shelves, the mirror (NO SWIMMING IN THE BEER), a cornice; two pendant lamps
    b0_, bz0, b1_, bz1, bh_ = P['inside'][0]
    o = K.bk((b0_ + 0.01, 0.0, bz0 + 0.01), (b1_, 0.95, bz1), 'pwood', 'cupboard')
    uv_trim(o, A, 'barfront', upm=UPM, grain='z', sel=lambda p, Pp: MK._gn(p.normal).x > 0.5); TR.kill_faces(o, lambda g, n: n.y < -0.5)
    K.bk((b0_ + 0.01, 0.95, bz0 + 0.01), (b1_ + 0.05, 1.0, bz1 + 0.04), 'woodtop', 'bbtop')
    o = K.bk((b0_ + 0.01, 1.0, bz0 + 0.01), (b0_ + 0.14, bh_ - 0.08, bz1), 'pwood', 'shelves')
    uv_trim(o, A, 'bottles', upm=0.156, grain='z', sel=lambda p, Pp: MK._gn(p.normal).x > 0.5)
    K.bk((b0_ + 0.14, 1.58, bz0 + 0.01), (b1_ + 0.02, 1.63, bz1), 'woodtop', 'shelf')
    K.bk((b0_ + 0.01, bh_ - 0.08, bz0 + 0.01), (b1_ + 0.06, bh_, bz1 + 0.05), 'pwood', 'bbcornice')
    o = K.bk((b0_ + 0.14, 1.12, -2.6), (b0_ + 0.18, 1.52, -0.2), 'gold', 'mirror'); uv_fit(o, A, 'mirror', sel=lambda p, Pp: MK._gn(p.normal).x > 0.5)
    for z in (-2.6, 0.9):
        K.rod((-4.3, H + 0.01, z), (-4.3, H - 1.0, z), 0.01, 'iron', 'wire', seg=4)
        o = lathe([(0.03, 0.0), (0.26, -0.18), (0.28, -0.22), (0.0, -0.08)], (-4.3, H - 1.0, z), M, seg=10, axis='y', name=fid + '_shade'); K.add(o, 'gold')
        o = ball(0.08, (-4.3, H - 1.14, z), GL, seg=6, rings=4, name=fid + '_bulb'); K.add(o, 'bulbw')
    # stools along the bar: chrome, red seats
    s0, s1, sz, sh = P['stool']; sx = (s0 + s1) / 2
    for z in P['stools']:
        o = lathe([(0.19, 0.0), (0.19, 0.025), (0.05, 0.05), (0.035, 0.1), (0.035, sh - 0.1), (0.0, sh - 0.1)], (sx, 0, z), M, seg=8, axis='y', name=fid + '_stool'); K.add(o, 'chrome')
        o = lathe([(0.0, sh - 0.11), (0.18, sh - 0.105), (0.205, sh - 0.06), (0.195, sh - 0.005), (0.0, sh)], (sx, 0, z), M, seg=8, axis='y', name=fid + '_seat'); K.add(o, 'vinyl')
    # the booths on the north wall: red buttoned benches, high backs, wood tables, a candle and a pint each
    for x0, z0, x1, z1, h in P['inside'][2:11]:
        z0 += 0.01
        if h > 1.0:
            K.bk((x0, 0.0, z0), (x1, h - 0.06, z1), 'vinyl', 'bback', bev=0.02); K.bk((x0 - 0.02, h - 0.06, z0), (x1 + 0.02, h, z1 + 0.02), 'pwood', 'bcap')
        elif h < 0.5:
            K.bk((x0, 0.0, z0), (x1, h - 0.14, z1), 'pwood', 'bseatbase'); K.bk((x0 - 0.01, h - 0.14, z0), (x1 + 0.01, h, z1 + 0.01), 'vinyl', 'bseat', bev=0.03)
        else:
            xm = (x0 + x1) / 2
            K.rod((xm, 0.02, (z0 + z1) / 2), (xm, h - 0.03, (z0 + z1) / 2), 0.04, 'iron', 'tleg', seg=6)
            K.bk((xm - 0.25, 0.0, (z0 + z1) / 2 - 0.3), (xm + 0.25, 0.04, (z0 + z1) / 2 + 0.3), 'iron', 'tfoot')
            K.bk((x0, h - 0.04, z0), (x1, h, z1), 'woodtop', 'btable')
            o = lathe([(0.0, 0.0), (0.03, 0.0), (0.032, 0.12), (0.012, 0.16), (0.012, 0.2), (0.0, 0.2)], (xm, h, z1 - 0.4), M, seg=6, axis='y', name=fid + '_candlebottle'); K.add(o, 'leaf')
            o = ball(0.025, (xm, h + 0.215, z1 - 0.4), GL, seg=5, rings=3, name=fid + '_flame'); K.add(o, 'glowa')
            o = lathe([(0.0, 0.0), (0.036, 0.0), (0.042, 0.14), (0.0, 0.14)], (xm + 0.15, h, z1 - 0.9), M, seg=6, axis='y', name=fid + '_pint'); K.add(o, 'beer')
            o = foam(K, (xm + 0.15, h + 0.155, z1 - 0.9))
    # the snug screen: panelled, a shelf on top with pints on it
    x0, z0, x1, z1, h = P['inside'][11]
    o = K.bk((x0, 0.0, z0), (x1, h - 0.05, z1), 'pwood', 'snug'); uv_trim(o, A, 'barfront', upm=UPM, grain='x', sel=lambda p, Pp: abs(MK._gn(p.normal).z) > 0.5)
    TR.kill_faces(o, lambda g, n: n.y < -0.5)
    K.bk((x0 - 0.03, h - 0.05, z0 - 0.08), (x1 + 0.03, h, z1 + 0.08), 'woodtop', 'snugtop')
    for x in (x0 + 0.5, x1 - 0.7):
        o = lathe([(0.0, 0.0), (0.036, 0.0), (0.042, 0.14), (0.0, 0.14)], (x, h, (z0 + z1) / 2), M, seg=6, axis='y', name=fid + '_pint'); K.add(o, 'beer')
        o = foam(K, (x, h + 0.155, (z0 + z1) / 2))
    # the darts corner on the south wall: the board in its cabinet (doors open: the scores on one), the sign, the oche,
    # and darts in the wall nowhere near the board
    zw = hd - t - 0.002; dx, dy = 1.5, 1.73
    K.bk((dx - 0.42, dy - 0.42, zw - 0.06), (dx + 0.42, dy + 0.42, zw), 'pwood', 'dcab')
    o = K.bk((dx - 0.88, dy - 0.42, zw - 0.03), (dx - 0.44, dy + 0.42, zw), 'chalkb', 'ddoor'); uv_fit(o, A, 'chalk', sel=lambda p, Pp: MK._gn(p.normal).z < -0.5)
    K.bk((dx + 0.44, dy - 0.42, zw - 0.03), (dx + 0.88, dy + 0.42, zw), 'pwood', 'ddoor')
    o = cyl(0.23, 0.04, (dx, dy, zw - 0.08), M, axis='z', seg=16, name=fid + '_dartboard'); uv_fit(o, A, 'iron'); uv_fit(o, A, 'dboard', sel=lambda p, Pp: MK._gn(p.normal).z < -0.5); K.P.append(o)
    o = K.bk((dx - 0.6, 2.32, zw - 0.025), (dx + 0.6, 2.55, zw), 'cream', 'dsign'); uv_fit(o, A, 'darts', sel=lambda p, Pp: MK._gn(p.normal).z < -0.5)
    K.bk((dx - 0.6, 0.02, zw - 2.39), (dx + 0.6, 0.035, zw - 2.35), 'brass', 'oche')
    for (x, y, z, key) in ((dx + 0.05, dy + 0.08, zw - 0.1, 'glowp'), (dx - 1.25, 2.85, zw, 'flowery'), (dx + 1.35, 1.05, zw, 'glowc'), (dx + 0.9, 3.4, zw, 'flowerp')):
        K.rod((x, y, z), (x, y, z - 0.13), 0.009, 'chrome', 'dart', seg=4)
        for a in (0, math.pi / 2):
            o = box((0.06 * abs(math.cos(a)) + 0.004, 0.06 * abs(math.sin(a)) + 0.004, 0.05), (x, y, z - 0.15), M, name=fid + '_flight'); K.add(o, key)
    # the jukebox by the south window: red, an arched chrome top with a glowing rim, glowing side tubes
    j0, jz0, j1, jz1, jh = P['inside'][12]; jm = (j0 + j1) / 2; jr = (j1 - j0) / 2 - 0.02
    o = K.bk((j0 + 0.02, 0.0, jz0 + 0.02), (j1 - 0.02, jh - jr, jz1 - 0.01), 'motor', 'juke', bev=0.02); uv_fit(o, A, 'juke', sel=lambda p, Pp: MK._gn(p.normal).z < -0.5)
    o = cyl(jr, jz1 - jz0 - 0.04, (jm, jh - jr, (jz0 + jz1) / 2 + 0.005), M, axis='z', seg=14, name=fid + '_jtop'); clip(o, lo=jh - jr + 0.001); K.add(o, 'chrome')
    pts = [(jm + math.cos(a) * (jr + 0.02), jh - jr + math.sin(a) * (jr + 0.02), jz0 + 0.02) for a in [math.pi * i / 10 for i in range(11)]]
    o = sweep(pts, 0.03, GL, seg=5, name=fid + '_jrim', cap=True); K.add(o, 'glowp')
    for x in (j0 + 0.04, j1 - 0.04):
        o = rod((x, 0.12, jz0 + 0.02), (x, jh - jr, jz0 + 0.02), 0.028, GL, seg=5, name=fid + '_jtube'); K.add(o, 'glowc')
    # two round tables: cast iron, oak tops, pints
    for x0, z0, x1, z1, h in P['inside'][13:15]:
        xm, zm = (x0 + x1) / 2, (z0 + z1) / 2
        o = lathe([(0.3, 0.0), (0.3, 0.03), (0.07, 0.06), (0.045, 0.12), (0.045, h - 0.04), (0.0, h - 0.04)], (xm, 0, zm), M, seg=8, axis='y', name=fid + '_tbase'); K.add(o, 'iron')
        o = cyl(0.4, 0.04, (xm, h - 0.02, zm), M, axis='y', seg=14, name=fid + '_ttop'); K.add(o, 'woodtop')
        o = lathe([(0.0, 0.0), (0.036, 0.0), (0.042, 0.14), (0.0, 0.14)], (xm + 0.12, h, zm - 0.1), M, seg=6, axis='y', name=fid + '_pint'); K.add(o, 'beer')
        o = foam(K, (xm + 0.12, h + 0.155, zm - 0.1))
    # the ship's-wheel light over the room; a life ring on the north wall
    wx, wz, wy = 1.6, -0.8, H - 0.9
    K.rod((wx, H + 0.01, wz), (wx, wy + 0.04, wz), 0.01, 'iron', 'wchain', seg=4)
    o = ring((wx, wy, wz), 0.55, 0.035, M, A, 'pwood', fid + '_wheel', axis='y', n=12); K.P.append(o)
    for k in range(8):
        a = TAU * k / 8
        K.rod((wx, wy, wz), (wx + math.cos(a) * 0.72, wy, wz + math.sin(a) * 0.72), 0.022, 'pwood', 'spoke', seg=5)
        if k % 2 == 0:
            o = ball(0.07, (wx + math.cos(a) * 0.4, wy + 0.08, wz + math.sin(a) * 0.4), GL, seg=6, rings=4, name=fid + '_wbulb'); K.add(o, 'bulbw')
    o = cyl(0.08, 0.1, (wx, wy, wz), M, axis='y', seg=8, name=fid + '_hub'); K.add(o, 'brass')
    lifering(K, (4.6, 2.2, -hd + t + 0.06), 'z', 'ring')
    # ---- the terrace: the chimney, kegs, picnic tables under parasols, festoon lights; out front: picnic tables, the quiz board
    x0, z0, x1, z1, h = P['deck'][3]
    K.bk((x0 - 0.02, rt, z0), (x1, rt + h - 0.3, z1), 'pwhite', 'chimney', bev=0.02)
    K.bk((x0 - 0.04, rt + h - 0.3, z0 - 0.04), (x1 + 0.04, rt + h - 0.1, z1 + 0.04), 'bricktop', 'chimband')
    K.bk((x0 - 0.07, rt + h - 0.1, z0 - 0.07), (x1 + 0.07, rt + h, z1 + 0.07), 'pwhite', 'chimcap')
    for zz in (z0 + 0.4, z1 - 0.4):
        o = lathe([(0.15, 0.0), (0.12, 0.3), (0.15, 0.36), (0.13, 0.44)], ((x0 + x1) / 2, rt + h, zz), M, seg=8, axis='y', name=fid + '_pot', cap=False); K.add(o, 'terra')
    x0, z0, x1, z1, h = P['deck'][6]
    for (x, z, y) in ((x0 + 0.28, z0 + 0.28, rt), (x0 + 0.28, z0 + 0.8, rt), (x1 - 0.27, z0 + 0.3, rt)):
        o = lathe([(0.2, 0.0), (0.24, 0.04), (0.24, 0.56), (0.2, 0.6), (0.06, 0.62), (0.06, 0.66), (0.0, 0.66)], (x, y, z), M, seg=8, axis='y', name=fid + '_keg'); K.add(o, 'keg')
    o = cyl(0.24, 0.62, (x0 + 0.28, rt + 0.64 + 0.24, z0 + 0.54), M, axis='z', seg=8, name=fid + '_kegside'); K.add(o, 'keg')
    for (x0, z0, x1, z1, h), key in ((P['deck'][4], 'stripeN'), (P['deck'][5], 'stripeY')):
        picnic(K, x0, z0, x1, z1, rt, h); parasol(K, (x0 + x1) / 2, (z0 + z1) / 2, rt, 2.3, key)
    for (x0, z0, x1, z1, h), key in ((P['out'][0], 'stripeY'), (P['out'][1], 'stripeN')):
        picnic(K, x0, z0, x1, z1, 0.0, h); parasol(K, (x0 + x1) / 2, (z0 + z1) / 2, 0.0, 2.3, key)
    x0, z0, x1, z1, h = P['out'][2]; xm = (x0 + x1) / 2
    for s_ in (-1, 1):
        o = box_between((xm + s_ * 0.22, 0.0, (z0 + z1) / 2), (xm + s_ * 0.005, h, (z0 + z1) / 2), z1 - z0, 0.04, M, fid + '_aboard'); K.add(o, 'pwood')
        uv_fit(o, A, 'quiz', sel=lambda p, Pp, s_=s_: MK._gn(p.normal).x * s_ > 0.5)
    K.rod((xm, h - 0.04, z0 + 0.02), (xm, h - 0.04, z1 - 0.02), 0.025, 'iron', 'hinge', seg=5)
    poles = [(hw - 0.35, -hd + 0.35), (-hw + 0.35, -hd + 0.35), (hw - 0.35, hd - 0.35), (-hw + 0.35, hd - 0.35)]
    for x, z in poles: K.rod((x, rt, z), (x, rt + 2.7, z), 0.03, 'pnavy', 'fpole', seg=6)
    for (pa, pb) in ((poles[0], poles[1]), (poles[2], poles[3]), (poles[0], poles[3])):
        n = 9; pts = []
        for i in range(n + 1):
            u = i / n; pts.append((pa[0] + (pb[0] - pa[0]) * u, rt + 2.65 - 0.55 * math.sin(math.pi * u), pa[1] + (pb[1] - pa[1]) * u))
        o = sweep(pts, 0.008, M, seg=3, name=fid + '_flex', cap=False); K.add(o, 'iron')
        for i in range(1, n):
            p = pts[i]; o = ball(0.055, (p[0], p[1] - 0.05, p[2]), GL, seg=4, rings=3, name=fid + '_festoon'); K.add(o, ['bulbw', 'glowp', 'bulbw', 'glowc'][i % 4])
    # ---- the boat
    boat(K, rt, H)
    for p in K.P + K.Q: crisp(p)
    # ---- far LOD: the shell as boxes with the front painted on, the stair, the chimney, the boat, the parasols
    o = K.bk((fx0, 0, -hd), (hw + 0.1, ptop, hd), 'side1', '1_front', far=True); uv_fit(o, A, 'facade1', sel=lambda p, Pp: MK._gn(p.normal).x > 0.5)
    for lo, hi in (((-hw, 0, -hd), (-hw + t, ptop, hd)), ((-hw + t, 0, -hd), (fx0, ptop, -hd + t)), ((-hw + t, 0, hd - t), (fx0, ptop, hd))):
        K.bk(lo, hi, 'side1', '1_wall', far=True)
    K.bk((-hw + t, H, -hd + t), (fx0, rt, hd - t), 'deck1', '1_roof', far=True)
    o = stepped(fid + '1_stair', M, A, [(St['x0'], 0.0), (lx, rt), (lx, 0.0)], St['z0'], St['z1'], 'tile', 'pwhite', 'pwhite',
                kill=lambda g, n: (n.y < -0.5 and g.y < 0.01) or n.z < -0.5); K.Q.append(o)
    o = K.bk((St['land'], H, St['z0']), (lx - 0.002, rt, St['z1']), 'tile', '1_landing', far=True)
    x0, z0, x1, z1, h = P['deck'][3]; K.bk((x0, rt, z0), (x1, rt + h, z1), 'pwhite', '1_chim', far=True)
    for (x0, z0, x1, z1, h), y, key in ((P['deck'][4], rt, 'stripeN'), (P['deck'][5], rt, 'stripeY'), (P['out'][0], 0.0, 'stripeY'), (P['out'][1], 0.0, 'stripeN')):
        o = lathe([(0.0, 2.6), (1.25, 2.15)], ((x0 + x1) / 2, y, (z0 + z1) / 2), M, seg=6, axis='y', name=fid + '1_para', cap=False)
        MK.uv_cyl(o, A, key, 2.0, 2.7, turns=1); K.Q.append(o)
        o = rod(((x0 + x1) / 2, y, (z0 + z1) / 2), ((x0 + x1) / 2, y + 2.62, (z0 + z1) / 2), 0.03, M, seg=3, name=fid + '1_pole'); uv_fit(o, A, 'pwhite'); K.Q.append(o)
    for p in K.P + K.Q: tri_ngons(p)
    lo, hi = extent(pub_boxes())
    return dict(lod0=K.P, lod1=K.Q, box=(lo, hi), ao=0.8, aolo=0.5, lod=130, eps=0.001, sheet=dict(exposure=-1.0),
                focus=[((hw, 2.8, 0), (1.0, 0.3, 0.35), 14.0), ((-1.0, 1.6, -2.0), (1.0, 0.25, 0.45), 7.0), ((-3.0, rt + 1.5, -4.0), (1.0, 0.45, 0.6), 7.0),
                       ((1.5, 1.6, 6.5), (0.1, 0.1, -1.0), 3.0), ((-4.5, 3.5, -5.5), (1.0, -0.4, 0.3), 3.5), ((3.5, 2.2, 8.6), (0.5, 0.2, 1.0), 9.0)])


# ============================================================ p_pj_harbour: THE HARBOUR MASTER
def paint_dial(px):  # the tide dial: a white face in a navy ring, TIDE over it, IN / OUT / YES round it, ticks
    h, w = px.shape[:2]; c = w / 2
    px[:] = hexrgb(0x1f3a8a); px_disc(px, c, c, c - 0.5, 0x1f3a8a); px_disc(px, c, c, c - 4, 0xfbf8f0)
    for k in range(24):
        a = k * TAU / 24; r0, r1 = c - 6, c - (9 if k % 6 == 0 else 7.5)
        px_line(px, c + math.sin(a) * r0, c - math.cos(a) * r0, c + math.sin(a) * r1, c - math.cos(a) * r1, 0x1f3a8a, 1.0)
    px_disc(px, c, c, c - 10, 0xe8f6fb, a0=math.pi * 0.75, a1=math.pi)  # (the YES side, a little bluer)
    px_disc(px, c, c, c - 10, 0xe8f6fb, a0=-math.pi, a1=-math.pi * 0.75)
    for s_, x, y, col in (('TIDE', c - 11.5, 12, 0x1f3a8a), ('IN', 11, c - 3, 0x1f3a8a), ('OUT', w - 28, c - 3, 0x1f3a8a), ('YES', c - 8.5, c + 15, 0xe0302a)):
        text_px(px, s_, int(x), int(y), 1, col)


def paint_cabinet(px):  # a grey steel filing cabinet's front: three drawers, handles, label slots
    h, w = px.shape[:2]; grain(px, 0x9aa8b4, 0.02, 91)
    for k in range(3):
        y0 = k * h // 3; px[y0] = hexrgb(0x5a6670); px[y0 + 2:y0 + 4, w // 2 - 4:w // 2 + 4] = hexrgb(0xf4f2ee); px[y0 + 6:y0 + 7, w // 2 - 5:w // 2 + 5] = hexrgb(0x3a3a44)


def paint_radio(px):  # the VHF set: dark face, a green display, dials, a red knob
    h, w = px.shape[:2]; px[:] = hexrgb(0x2a2e36)
    px[2:7, 2:16] = hexrgb(0x39ff14) * 0.85; text_px(px, '16', 4, 1, 1, 0x1a3a1a) if False else None
    for x in (20, 26): px_disc(px, x, 5, 2.5, 0xb8c0c8)
    px_disc(px, 28, 12, 2, 0xe0302a); px[10:14, 2:18] = hexrgb(0x5a606a)


def paint_chart(px):  # a sea chart: blue water, a yellow island, depth lines, a red course
    h, w = px.shape[:2]; r = np.random.default_rng(93)
    px[:] = hexrgb(0xb8e4f4); yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot((xx - w * 0.45) / 1.3, yy - h * 0.55)
    px[d < 9] = hexrgb(0xf2d88a); px[(d >= 12) & (d < 12.6)] = hexrgb(0x6ab0d8); px[(d >= 17) & (d < 17.6)] = hexrgb(0x6ab0d8)
    px[d < 4] = hexrgb(0x7ac860)
    for x in range(4, w - 4): px[int(5 + x * 0.35) % h, x] = hexrgb(0xe0302a)
    px[:1] = px[-1:] = hexrgb(0xfbf8f0); px[:, :1] = px[:, -1:] = hexrgb(0xfbf8f0)


def paint_facade_hm(px):  # the far LOD's front: white, the blue plinth, the window, the door, the sign
    h, w = px.shape[:2]; Hm, Wm = 4.3, 8.0
    def Y(y): return int(round((1 - y / Hm) * h))
    def X(x): return int(round((x / Wm + 0.5) * w))
    px[:] = hexrgb(0xfbf8f0); px[Y(0.45):] = hexrgb(0x2a8ad8)
    px[Y(2.5):Y(1.0), X(-3.4):X(-2.0)] = hexrgb(0x2a2026); px[Y(2.3):, X(-1.6):X(-0.4)] = hexrgb(0xe0302a)
    px[Y(3.13):Y(2.68), X(-3.9):X(0.4)] = hexrgb(0x1f3a8a); px[:Y(3.7)] = hexrgb(0xe0302a)


def hm_atlas(fid):
    A = Atlas(fid + '_atlas', 256, 512)
    A.band('render', 16, flat_c(0xfbf8f0, 0.02, 31)); A.band('plinth', 16, paint_plinth(0xfbf8f0, 0x2a8ad8, 0xfbf8f0, frac=0.5))
    A.band('redb', 16, paint_boards(0xe0302a, 0xa8202a, 33, rows=6, vert=True))
    A.band('redband', 16, lambda px: (px.__setitem__(slice(None), hexrgb(0xe0302a)), px.__setitem__(slice(0, 2), hexrgb(0xfbf8f0)), px.__setitem__(slice(-2, None), hexrgb(0xfbf8f0))))
    A.band('inwall', 16, flat_c(0xdaf2ee, 0.02, 35)); A.band('inplinth', 16, paint_plinth(0xdaf2ee, 0x4a6a7a, 0xfbf8f0, frac=0.72))
    A.band('inwhite', 16, flat_c(0xf6f4ee, 0.02, 37))
    A.band('vinyl', 16, lambda px: px.__setitem__(slice(None), np.where((((np.mgrid[0:px.shape[0], 0:px.shape[1]][1] // 8) + (np.mgrid[0:px.shape[0], 0:px.shape[1]][0] // 8)) % 2 == 0)[:, :, None], hexrgb(0xa8bccc)[None, None], hexrgb(0xdae4ec)[None, None])))
    A.band('roofdeck', 16, flat_c(0x8aa4b4, 0.03, 39)); A.band('deck', 16, paint_boards(0xd8a868, 0x6a4a2a, 41))
    A.band('ringband', 8, paint_stripes_v(0xe0302a, 0xfbf8f0, 8))
    A.band('counterf', 16, lambda px: (grain(px, 0xfbf8f0, 0.02, 43), [px.__setitem__((slice(2, -2), slice(x, x + 1)), hexrgb(0x2a8ad8)) for x in range(0, px.shape[1], 12)], px.__setitem__(slice(2, 3), hexrgb(0x2a8ad8)), px.__setitem__(slice(-3, -2), hexrgb(0x2a8ad8))))
    A.cell('fascia', 176, 18, paint_board(['HARBOUR MASTER'], 0xfbf8f0, 0x1f3a8a, border=0xe0302a, scale=2, bw=2))
    A.cell('dial', 64, 64, paint_dial)
    A.cell('honk', 56, 20, paint_board(['HONK FOR', 'SERVICE'], 0xffd21a, 0x1c1c22, border=0x1c1c22))
    A.cell('chalk', 88, 40, paint_chalk(['FORECAST', 'WIND: YES', 'FISH: PROBABLY', 'BOATS: SOME'], [0xffe14d, 0xf4f2ee, 0xf4f2ee, 0x4fd8ff]))
    A.cell('notice', 64, 36, paint_board(['LOST:', 'ONE BOAT', 'LAST SEEN:', 'THE PUB'], 0xfff2d8, 0x1c1c22, border=0xe0302a, cols=[0xe0302a, 0x1c1c22, 0xe0302a, 0x1c1c22]))
    A.cell('chart', 48, 32, paint_chart); A.cell('radio', 32, 16, paint_radio); A.cell('cabinet', 24, 36, paint_cabinet)
    A.cell('facade1', 64, 32, paint_facade_hm)
    A.cell('bulwark', 16, 16, lambda px: (px.__setitem__(slice(None), hexrgb(0xfbf8f0)), px.__setitem__(slice(3, 5), hexrgb(0x2a8ad8))))
    swatches(A, (('pwhite', 0xfbf8f0, 0.02, None), ('hred', 0xe0302a, 0.02, None), ('hblue', 0x2a8ad8, 0.02, None), ('pnavy', 0x1f3a8a, 0.02, None),
                 ('gold', 0xffc83a, 0.03, None), ('horn', 0xffd21a, 0.03, None), ('steel', 0x9aa8b4, 0.03, None), ('ceiling', 0xf8f4ea, 0.015, None),
                 ('tread', 0x2a8ad8, 0.04, 0x8ad0ff), ('oak', 0xc89058, 0.05, None), ('leaf', 0x3fae3a, 0.06, None), ('flowerr', 0xe0302a, 0.03, None),
                 ('soil', 0x5a3e2c, 0.08, None), ('iron', 0x24242c, 0.04, None), ('bulbw', 0xfff0b0, 0.0, None), ('deckb', 0x9ab0c0, 0.03, None),
                 ('side1', 0xfbf8f0, 0.02, None), ('flagy', 0xffe14d, 0.0, None), ('flagb', 0x1f6ad8, 0.0, None), ('flagp', 0xff4fd8, 0.0, None),
                 ('flagg', 0x39ff14, 0.0, None), ('glass', 0x8ad0ff, 0.02, None), ('chalkb', 0x1e2a26, 0.05, None)))
    return A


def bounce(o, k=0.55, warm=(1.0, 0.95, 0.86)):
    """the sunny quay's bounce light on the south faces (the front, the tower's dial side: away from the north-east
    sun all day), painted into the AO colours: lifted toward white and warmed"""
    me = o.data; ca = me.color_attributes.get('AO')
    for p in me.polygons:
        n = MK._gn(p.normal)
        if n.z < 0.3: continue
        f = k * min(1.0, (n.z - 0.3) / 0.4)
        for li in p.loop_indices:
            c = ca.data[li].color
            ca.data[li].color = tuple(min(1.0, (c[i] + (1 - c[i]) * f) * (1 - f * (1 - warm[i])) ) for i in range(3)) + (1.0,)


@prop('p_pj_harbour')
def build_harbour():
    fid = 'pjh'; P = PJP['hm']
    hw, hd, t, H = P['w'] / 2, P['d'] / 2, P['t'], P['h']; rt = H + P['roof']; pt = P['pt']; pp = rt + P['par']
    d0, d1, dh = P['door']; w0, w1 = P['win']; s0, s1 = P['side']; k0, k1 = P['back']; sl, hh = P['sill'], P['head']
    g0, g1 = P['gap']; tx0, tz0, tx1, tz1 = P['tower']; T = P['top']; St = P['stair']; F = P['flight']
    fr = (T - rt) / F['n']; fz = F['z0'] - F['n'] * F['run']; lz = fz - F['land']
    gl = P['gal']; gx0, gx1, gz0, gz1 = tx0 - gl, tx1 + gl, tz0 - gl, tz1 + gl; R = 0.06; rh = T + P['rail']
    wt, po = P['wt'], P['post']; ws, wh, rtop = T + P['rsill'], T + P['rhead'], T + P['room']; r0, r1 = P['rdoor']
    A = hm_atlas(fid); img = A.image()
    M = mat(fid, 0xffffff, rough=0.38, tex=img, clearcoat=0.45)
    GL = mat('glow', 0xffffff, emit=0xffffff, strength=2.2, tex=img, emit_tex=True)
    K = Kit(fid, A, M, GL)
    tc = ((tx0 + tx1) / 2, 0, (tz0 + tz1) / 2)
    # ---- the office's walls (the boxes' pieces exactly), its roof and parapet with red caps
    OUT = lambda k: 'plinth' if k == 0 else 'render'
    IN = lambda k: 'inplinth' if k == 0 else 'inwall'
    for lo, hi in (((-hw, 0, hd - t), (w0, H, hd)), ((w0, 0, hd - t), (w1, sl, hd)), ((w0, hh, hd - t), (w1, H, hd)), ((w1, 0, hd - t), (d0, H, hd)),
                   ((d0, dh, hd - t), (d1, H, hd)), ((d1, 0, hd - t), (hw, H, hd)),
                   ((-hw, 0, -hd), (k0, H, -hd + t)), ((k0, dh, -hd), (k1, H, -hd + t)), ((k1, 0, -hd), (hw, H, -hd + t)),
                   ((-hw, 0, -hd + t), (-hw + t, H, s0)), ((-hw, 0, s0), (-hw + t, sl, s1)), ((-hw, hh, s0), (-hw + t, H, s1)), ((-hw, 0, s1), (-hw + t, H, hd - t)),
                   ((hw - t, 0, -hd + t), (hw, H, hd - t))):
        K.wall(lo, hi, 'wall', OUT, IN, 'pwhite', cap=False)
    RN = lambda k: 'render'
    for lo, hi in (((-hw, rt, hd - pt), (g0, pp, hd)), ((g1, rt, hd - pt), (hw, pp, hd)), ((tx1, rt, -hd), (hw, pp, -hd + pt)),
                   ((-hw, rt, tz1), (-hw + pt, pp, hd - pt)), ((hw - pt, rt, -hd + pt), (hw, pp, hd - pt))):
        K.wall(lo, hi, 'parapet', RN, RN, 'pwhite', cap=False, bot=False)
    for lo, hi in (((-hw - 0.03, pp, hd - pt - 0.03), (g0, pp + 0.07, hd + 0.03)), ((g1, pp, hd - pt - 0.03), (hw + 0.03, pp + 0.07, hd + 0.03)),
                   ((tx1, pp, -hd - 0.03), (hw - pt - 0.03, pp + 0.07, -hd + pt + 0.03)), ((-hw - 0.03, pp, tz1), (-hw + pt + 0.03, pp + 0.07, hd - pt - 0.03)),
                   ((hw - pt - 0.03, pp, -hd - 0.03), (hw + 0.03, pp + 0.07, hd - pt - 0.03))):
        K.bk(lo, hi, 'hred', 'pcap')
    ro = K.bk((-hw, H, -hd), (hw, rt, hd), 'pwhite', 'roof'); uv_fit(ro, A, 'ceiling', sel=lambda p, Pp: MK._gn(p.normal).y < -0.5)
    TR.kill_faces(TR.bake_tf(ro), lambda g, n: n.y > 0.5)
    K.floor(-hw + 0.1, hw - 0.1, -hd + 0.1, hd - 0.1, 'roofdeck', 0.8, UPM, y=rt)
    K.floor(-hw + 0.1, hw - 0.1, -hd + 0.1, hd - 0.1, 'vinyl', 0.8, UPM)
    # ---- the tower on the roof: white render, a red band under the gallery; the tide dial on its south face
    TB = lambda k: 'redband' if k == 8 else 'render'
    for lo, hi in (((tx0, rt, tz0), (tx0 + t, T - 0.15, tz1)), ((tx1 - t, rt, tz0), (tx1, T - 0.15, tz1)), ((tx0 + t, rt, tz0), (tx1 - t, T - 0.15, tz0 + t)), ((tx0 + t, rt, tz1 - t), (tx1 - t, T - 0.15, tz1))):
        K.wall(lo, hi, 'tower', TB, RN, 'pwhite', ctr=tc, bot=False, cap=False)
    dx_, dy_, dz_ = (tx0 + tx1) / 2, 5.3, tz1
    o = cyl(0.95, 0.06, (dx_, dy_, dz_ + 0.025), GL, axis='z', seg=20, name=fid + '_dial'); uv_fit(o, A, 'pnavy'); uv_fit(o, A, 'dial', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5); K.P.append(o)  # (backlit: it faces away from the sun)
    o = lathe([(0.9, 0.005), (1.02, 0.005), (1.02, 0.1), (0.9, 0.1), (0.9, 0.005)], (dx_, dy_, dz_), M, seg=20, axis='z', name=fid + '_dialrim', cap=False); K.add(o, 'hred')  # (a closed bezel: no seam)
    o = box_between((dx_, dy_, dz_ + 0.075), (dx_, dy_ - 0.36, dz_ + 0.075), 0.07, 0.025, M, fid + '_hand'); K.add(o, 'hred')  # (the hand stops short of YES: it points, it doesn't hide it)
    o = box_between((dx_ - 0.09, dy_ - 0.3, dz_ + 0.075), (dx_, dy_ - 0.42, dz_ + 0.075), 0.055, 0.025, M, fid + '_head1'); K.add(o, 'hred')
    o = box_between((dx_ + 0.09, dy_ - 0.3, dz_ + 0.075), (dx_, dy_ - 0.42, dz_ + 0.075), 0.055, 0.025, M, fid + '_head2'); K.add(o, 'hred')
    o = cyl(0.09, 0.06, (dx_, dy_, dz_ + 0.08), M, axis='z', seg=8, name=fid + '_boss'); K.add(o, 'gold')
    for (cx_, cz_), ax_ in (((tx0, (tz0 + tz1) / 2), 'x'), ((dx_, tz0), 'z'), ((tx1, (tz0 + tz1) / 2), 'x')):  # little windows up the tower's other faces
        sx_ = -1 if (ax_ == 'x' and cx_ < dx_) or (ax_ == 'z' and cz_ < (tz0 + tz1) / 2) else 1
        if ax_ == 'x':
            K.bk((min(cx_ - sx_ * 0.01, cx_ + sx_ * 0.05), 4.9, cz_ - 0.42), (max(cx_ - sx_ * 0.01, cx_ + sx_ * 0.05), 6.0, cz_ + 0.42), 'hred', 'twin')
            K.bk((min(cx_, cx_ + sx_ * 0.07), 5.02, cz_ - 0.3), (max(cx_, cx_ + sx_ * 0.07), 5.88, cz_ + 0.3), 'glass', 'tglass')
        else:
            K.bk((cx_ - 0.42, 4.9, min(cz_ - sx_ * 0.01, cz_ + sx_ * 0.05)), (cx_ + 0.42, 6.0, max(cz_ - sx_ * 0.01, cz_ + sx_ * 0.05)), 'hred', 'twin')
            K.bk((cx_ - 0.3, 5.02, min(cz_, cz_ + sx_ * 0.07)), (cx_ + 0.3, 5.88, max(cz_, cz_ + sx_ * 0.07)), 'glass', 'tglass')
    # ---- the gallery: a steel deck on brackets round the tower, a solid white bulwark with a red rail, the landing
    for lo, hi in (((gx0, T - 0.15, gz0), (gx1, T, tz0)), ((gx0, T - 0.15, tz1), (gx1, T, gz1)), ((gx0, T - 0.15, tz0), (tx0, T, tz1)), ((tx1, T - 0.15, tz0), (gx1, T, tz1))):
        o = K.bk(lo, hi, 'steel', 'gallery'); uv_fit(o, A, 'deckb', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5)
    o = K.bk((g0 + 0.002, T - 0.15, lz), (g1, T, fz - 0.002), 'steel', 'landing'); uv_fit(o, A, 'deckb', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5)
    for (x, z), (dx, dz) in (((tx0, tz0), (-1, -1)), ((tx1, tz0), (1, -1)), ((tx0, tz1), (-1, 1)), ((tx1, tz1), (1, 1)), ((dx_, tz0), (0, -1)), ((dx_, tz1), (0, 1)), ((tx0, (tz0 + tz1) / 2), (-1, 0))):
        o = box_between((x - dx * 0.0, T - 1.05, z), (x + dx * (gl - 0.1) * 0.7, T - 0.16, z + dz * (gl - 0.1) * 0.7), 0.08, 0.08, M, fid + '_bracket'); K.add(o, 'pwhite')
    rails = (((gx0, T, gz0), (gx1, rh, gz0 + R)), ((gx0, T, gz1 - R), (gx1, rh, gz1)), ((gx0, T, gz0 + R), (gx0 + R, rh, gz1 - R)),
             ((gx1 - R, T, gz0 + R), (gx1, rh, lz)), ((gx1 - R, T, fz), (gx1, rh, gz1 - R)), ((g0, T, lz), (g1, rh, lz + R)), ((g1 - R, T, lz + R), (g1, rh, fz)))
    for lo, hi in rails:
        o = K.bk(lo, (hi[0], hi[1] - 0.04, hi[2]), 'pwhite', 'bulwark'); uv_fit(o, A, 'bulwark', sel=lambda p, Pp: abs(MK._gn(p.normal).y) < 0.5)
        along = 0 if hi[0] - lo[0] > hi[2] - lo[2] else 2; m_ = [(lo[i] + hi[i]) / 2 for i in range(3)]
        a_ = list(m_); b_ = list(m_); a_[along] = lo[along] - 0.03; b_[along] = hi[along] + 0.03; a_[1] = b_[1] = hi[1] - 0.03
        K.rod(tuple(a_), tuple(b_), 0.045, 'hred', 'railcap', seg=6)
    # ---- the lookout: red boarded walls (white inside), white corner posts, open windows all round, the door east
    LO = lambda k: 'redb'
    LI = lambda k: 'inwhite'
    for z0_, z1_ in ((tz0, tz0 + wt), (tz1 - wt, tz1)):
        K.wall((tx0, T, z0_), (tx1, ws, z1_), 'look', LO, LI, 'pwhite', ctr=tc, bot=False); K.wall((tx0, wh, z0_), (tx1, rtop, z1_), 'look', LO, LI, 'pwhite', ctr=tc, cap=False)
        K.wall((tx0, ws, z0_), (tx0 + po, wh, z1_), 'post', RN, LI, 'pwhite', ctr=tc, bot=False, cap=False); K.wall((tx1 - po, ws, z0_), (tx1, wh, z1_), 'post', RN, LI, 'pwhite', ctr=tc, bot=False, cap=False)
    K.wall((tx0, T, tz0 + wt), (tx0 + wt, ws, tz1 - wt), 'look', LO, LI, 'pwhite', ctr=tc, bot=False); K.wall((tx0, wh, tz0 + wt), (tx0 + wt, rtop, tz1 - wt), 'look', LO, LI, 'pwhite', ctr=tc, cap=False)
    K.wall((tx0, ws, tz0 + wt), (tx0 + wt, wh, tz0 + po), 'post', RN, LI, 'pwhite', ctr=tc, bot=False, cap=False); K.wall((tx0, ws, tz1 - po), (tx0 + wt, wh, tz1 - wt), 'post', RN, LI, 'pwhite', ctr=tc, bot=False, cap=False)
    K.wall((tx1 - wt, T, tz0 + wt), (tx1, rtop, r0), 'look', LO, LI, 'pwhite', ctr=tc, bot=False, cap=False); K.wall((tx1 - wt, T, r1), (tx1, rtop, tz1 - wt), 'look', LO, LI, 'pwhite', ctr=tc, bot=False, cap=False)
    K.wall((tx1 - wt, wh, r0), (tx1, rtop, r1), 'look', LO, LI, 'pwhite', ctr=tc, cap=False)
    for (a_, b_), axis in ((((tx0, tz0 - 0.06), (tx1, tz0 + wt + 0.04)), 'z'), (((tx0, tz1 - wt - 0.04), (tx1, tz1 + 0.06)), 'z'), (((tx0 - 0.06, tz0 + wt), (tx0 + wt + 0.04, tz1 - wt)), 'x')):
        K.bk((a_[0] + (po - 0.04 if axis == 'z' else 0), ws - 0.04, a_[1] + (0 if axis == 'z' else po - 0.04)), (b_[0] - (po - 0.04 if axis == 'z' else 0), ws + 0.03, b_[1] - (0 if axis == 'z' else po - 0.04)), 'pwhite', 'lsill')
    K.floor(tx0 + wt - 0.05, tx1 - wt + 0.05, tz0 + wt - 0.05, tz1 - wt + 0.05, 'deck', 0.8, UPM, y=T - 0.02)
    # its roof: a slab, a red pyramid, the gold weathervane (a cod on an arrow), the foghorn, a lamp inside
    K.bk((tx0 - 0.3, rtop, tz0 - 0.3), (tx1 + 0.3, rtop + P['cap'], tz1 + 0.3), 'pwhite', 'lroof')
    pc = ((tx0 + tx1) / 2, rtop + P['cap'], (tz0 + tz1) / 2); ph = 1.2; ry_ = (tx1 - tx0) / 2 + 0.25
    o = lathe([(ry_ * math.sqrt(2), 0.0), (0.0, ph)], pc, M, seg=4, axis='y', name=fid + '_pyramid', cap=False)
    TR.bake_tf(o); o.data.transform(Matrix.Translation(-gv(*pc))); o.data.transform(Matrix.Rotation(math.pi / 4, 4, 'Z')); o.data.transform(Matrix.Translation(gv(*pc))); o.data.update()
    K.add(o, 'hred')
    vx, vy, vz = pc[0], pc[1] + ph, pc[2]
    K.rod((vx, vy - 0.1, vz), (vx, vy + 1.4, vz), 0.025, 'gold', 'vrod', seg=6)
    o = ball(0.08, (vx, vy + 0.05, vz), M, seg=6, rings=4, name=fid + '_vball'); K.add(o, 'gold')
    for a in (0, math.pi / 2):
        K.rod((vx - math.cos(a) * 0.45, vy + 0.5, vz - math.sin(a) * 0.45), (vx + math.cos(a) * 0.45, vy + 0.5, vz + math.sin(a) * 0.45), 0.015, 'gold', 'varm', seg=4)
    for a in range(4):
        o = ball(0.04, (vx + math.cos(a * math.pi / 2) * 0.47, vy + 0.5, vz + math.sin(a * math.pi / 2) * 0.47), M, seg=5, rings=3, name=fid + '_vtip'); K.add(o, 'gold')
    o = lathe([(0.0, -0.45), (0.1, -0.32), (0.16, -0.05), (0.13, 0.2), (0.05, 0.38), (0.0, 0.42)], (vx, vy + 1.05, vz), M, seg=8, axis='z', name=fid + '_vfish')
    TR.bake_tf(o); o.data.transform(Matrix.Translation(-gv(vx, vy + 1.05, vz))); o.data.transform(Matrix.Diagonal((0.35, 1.0, 1.0, 1.0))); o.data.transform(Matrix.Translation(gv(vx, vy + 1.05, vz))); o.data.update()
    K.add(o, 'gold')
    o = side([(0.38, 1.05), (0.62, 1.22), (0.58, 1.05), (0.62, 0.88)], 0.02, (vx, vy, vz), M, name=fid + '_vtail'); K.add(o, 'gold')
    o = side([(-0.38, 1.05), (-0.75, 1.13), (-0.75, 0.97)], 0.02, (vx, vy, vz), M, name=fid + '_vnose'); K.add(o, 'gold')
    hx, hy, hz = tx0 - 0.15, rtop + 0.35, tz1 + 0.15  # the foghorn: twin trumpets on a bracket off the roof's south-west corner, aimed at the sea
    K.bk((hx - 0.15, rtop + P['cap'], hz - 0.15), (hx + 0.35, rtop + P['cap'] + 0.22, hz + 0.15), 'steel', 'hornbox')
    for k, (ang, ln) in enumerate(((0.45, 1.1), (0.15, 0.85))):
        dirv = V3((-math.sin(ang), -0.12, math.cos(ang))).normalized(); base = V3((hx + 0.1, hy + 0.06 + k * 0.12, hz))
        o = lathe([(0.06, 0.0), (0.07, ln * 0.55), (0.14, ln * 0.85), (0.3 - k * 0.06, ln)], (0, 0, 0), M, seg=10, axis='z', name=fid + '_horn', cap=False)
        TR.bake_tf(o); q = V3((0, 0, 1)).rotation_difference(dirv)
        for v in o.data.vertices:
            g = V3((v.co.x, v.co.z, -v.co.y)); g = q @ g + base; v.co = gv(*g)
        o.data.update(); K.add(o, 'horn')
    o = ball(0.13, (-1.6, rtop - 0.42, -1.3), GL, seg=6, rings=4, name=fid + '_llamp'); K.add(o, 'bulbw')
    K.rod((-1.6, rtop, -1.3), (-1.6, rtop - 0.3, -1.3), 0.01, 'iron', 'lwire', seg=4)
    # a searchlight on the gallery's north-west corner; a life ring on the south bulwark
    sx_, sz_ = gx0 + 0.3, gz0 + 0.3
    K.rod((sx_, T, sz_), (sx_, rh + 0.25, sz_), 0.05, 'steel', 'slpost', seg=6)
    K.bk((sx_ - 0.24, rh + 0.25, sz_ - 0.03), (sx_ + 0.24, rh + 0.33, sz_ + 0.03), 'steel', 'slyoke')
    for s_ in (-1, 1): K.bk((sx_ + s_ * 0.24 - 0.03, rh + 0.33, sz_ - 0.03), (sx_ + s_ * 0.24 + 0.03, rh + 0.62, sz_ + 0.03), 'steel', 'slyoke')
    o = cyl(0.2, 0.42, (sx_, rh + 0.55, sz_), M, axis='z', seg=10, name=fid + '_sldrum'); TR.bake_tf(o)
    o.data.transform(Matrix.Translation(-gv(sx_, rh + 0.55, sz_))); o.data.transform(Matrix.Rotation(0.6, 4, 'Z')); o.data.transform(Matrix.Rotation(0.2, 4, 'X')); o.data.transform(Matrix.Translation(gv(sx_, rh + 0.55, sz_))); o.data.update(); K.add(o, 'hred')
    o = cyl(0.17, 0.44, (sx_, rh + 0.55, sz_), GL, axis='z', seg=10, name=fid + '_sllens'); TR.bake_tf(o)
    o.data.transform(Matrix.Translation(-gv(sx_, rh + 0.55, sz_))); o.data.transform(Matrix.Rotation(0.6, 4, 'Z')); o.data.transform(Matrix.Rotation(0.2, 4, 'X')); o.data.transform(Matrix.Translation(gv(sx_, rh + 0.55, sz_))); o.data.update(); K.add(o, 'bulbw')
    lifering(K, (tx0 + 0.9, T + 0.55, gz1 + 0.06), 'z', 'gring')
    # the signal mast at the gallery's south-east corner, a yard, a string of flags down to the bulwark
    mx, mz = gx1 - 0.25, gz1 - 0.25
    K.rod((mx, T, mz), (mx, T + 4.1, mz), 0.05, 'pwhite', 'mast', seg=6)
    K.rod((mx - 1.1, T + 3.4, mz), (mx + 1.1, T + 3.4, mz), 0.03, 'pwhite', 'yard', seg=5)
    o = ball(0.07, (mx, T + 4.15, mz), M, seg=6, rings=4, name=fid + '_truck'); K.add(o, 'gold')
    a_, b_ = V3((mx + 1.08, T + 3.38, mz)), V3((gx1 - 0.03, rh, gz0 + 0.6))
    K.rod(tuple(a_), tuple(b_), 0.006, 'iron', 'halyard', seg=3)
    for i, key in enumerate(('flagy', 'hred', 'flagb', 'flagp', 'flagg', 'flagy', 'hblue')):
        u = (i + 0.6) / 7.6; p0 = a_.lerp(b_, u); p1 = a_.lerp(b_, u + 0.1)
        o = box_between(tuple(p0), tuple(V3((p1.x, p1.y, p1.z))), 0.025, 0.02, M, fid + '_fl') if False else None
        dv = (b_ - a_).normalized(); dn = V3((0, -1, 0)) - dv * dv.y; dn.normalize()
        pts = [p0, p1, (p0 + p1) / 2 + dn * 0.32] if i % 2 else [p0, p1, p1 + dn * 0.28, p0 + dn * 0.28]
        bm = bmesh.new(); vs = [bm.verts.new(gv(*p)) for p in pts]; f = bm.faces.new(vs)
        o = _obj(fid + '_flag', bm, M); o.data.materials.clear(); o.data.materials.append(M)
        bm2 = bmesh.new(); bm2.from_mesh(o.data); bmesh.ops.solidify(bm2, geom=bm2.faces[:], thickness=0.015); bm2.to_mesh(o.data); bm2.free(); o.data.update()
        K.add(o, key)
    # ---- the front stair (solid, blue treads) and its rail; the flight up the roof to the gallery, its rail
    prof = stair_prof(St['x0'], St['n'], St['run'], rt / St['n'], -1, land=St['land'])
    o = stepped(fid + '_stair', M, A, prof, St['z0'], St['z1'], 'tread', 'pwhite', 'pwhite', kill=lambda g, n: (n.y < -0.5 and g.y < 0.01) or n.z < -0.5, fan=len(prof) - 1); K.P.append(o)
    zr = St['z1'] - 0.06; sr = rt / St['n']
    for i in range(0, St['n'] - 1, 3):
        x = St['x0'] - (i + 0.5) * St['run']; K.rod((x, (i + 1) * sr, zr), (x, (i + 1) * sr + 0.95, zr), 0.022, 'hred', 'spost', seg=6)
    K.rod((St['x0'] - 0.5 * St['run'], sr + 0.95, zr), (St['land'] + 0.8, rt + 0.95, zr), 0.03, 'hred', 'srail', seg=6)
    K.rod((St['land'] + 0.8, rt, zr), (St['land'] + 0.8, rt + 0.95, zr), 0.022, 'hred', 'spost', seg=6)
    fprof = stair_prof(-F['z0'], F['n'], F['run'], fr, 1, y0=rt)
    o = stepped(fid + '_flight', M, A, fprof, g0, g1, 'tread', 'pwhite', 'pwhite', kill=lambda g, n: n.y < -0.5 and g.y < rt + 0.01, fan=len(fprof) - 1)
    TR.bake_tf(o)
    for v in o.data.vertices: g = V3((v.co.x, v.co.z, -v.co.y)); v.co = gv(g.z, g.y, -g.x)  # (built along x: turned to climb north, over the gap)
    o.data.update(); uv_fit(o, A, 'tread', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5); uv_fit(o, A, 'pwhite', sel=lambda p, Pp: abs(MK._gn(p.normal).y) <= 0.5)
    K.P.append(o)
    for i in range(1, F['n'], 3):
        z = F['z0'] - (i + 0.5) * F['run']; K.rod((g1 - 0.06, rt + (i + 1) * fr, z), (g1 - 0.06, rt + (i + 1) * fr + 0.95, z), 0.022, 'hred', 'fpost', seg=6)
    K.rod((g1 - 0.06, rt + fr + 0.95, F['z0'] - 0.5 * F['run']), (g1 - 0.06, T + 0.95, fz + 0.02), 0.03, 'hred', 'frail', seg=6)
    # ---- the front: the sign, the door (red, swung in, a porthole), HONK FOR SERVICE and its pull, the window's frame, a lamp
    o = K.bk((-hw + 0.1, 2.68, hd - 0.02), (g0 - 0.2, 3.13, hd + 0.06), 'pwhite', 'fascia', m=GL); uv_fit(o, A, 'fascia', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5)  # (a lit sign box: the front's in shade all day)
    K.bk((d0 + 0.01, 0.04, hd - t - 0.06), (d0 + 0.06, dh - 0.06, hd - t - 0.06 - 0.95), 'hred', 'door') if False else None
    K.bk((d0 - 0.06, 0.04, hd - t - 1.0), (d0 - 0.01, dh - 0.06, hd - t - 0.002), 'hred', 'door')
    o = cyl(0.14, 0.07, (d0 - 0.035, 1.6, hd - t - 0.5), M, axis='x', seg=8, name=fid + '_porthole'); K.add(o, 'gold')
    o = cyl(0.1, 0.08, (d0 - 0.035, 1.6, hd - t - 0.5), M, axis='x', seg=8, name=fid + '_portglass'); K.add(o, 'glass')
    for x, s_ in ((d0, 1), (d1, -1)): K.bk((min(x, x + s_ * 0.08), 0.02, hd - 0.04), (max(x, x + s_ * 0.08), dh, hd + 0.05), 'hred', 'djamb')
    K.bk((d0 - 0.08, dh - 0.01, hd - 0.04), (d1 + 0.08, dh + 0.1, hd + 0.05), 'hred', 'dhead')
    K.bk((d0 + 0.02, 0.0, hd - t - 0.02), (d1 - 0.02, 0.03, hd + 0.04), 'gold', 'thresh')
    o = K.bk((g0 - 0.03, 1.35, St['z0'] + 0.2), (g0 + 0.002, 1.8, St['z1'] - 0.2), 'horn', 'honksign'); uv_fit(o, A, 'honk', sel=lambda p, Pp: MK._gn(p.normal).x < -0.5)
    K.rod((d1 + 0.25, 1.35, hd + 0.04), (d1 + 0.25, rt + 0.3, hd + 0.04), 0.008, 'iron', 'cord', seg=4)
    o = ball(0.06, (d1 + 0.25, 1.32, hd + 0.04), M, scale=(1, 1.6, 1), seg=6, rings=4, name=fid + '_pull'); K.add(o, 'hred')
    for z_, s_ in ((w0, 1), (w1, -1)): K.bk((min(z_, z_ + s_ * 0.08), sl, hd - 0.04), (max(z_, z_ + s_ * 0.08), hh, hd + 0.05), 'hred', 'wjamb')
    K.bk((w0 - 0.1, sl - 0.05, hd - 0.04), (w1 + 0.1, sl + 0.03, hd + 0.14), 'pwhite', 'wsill'); K.bk((w0 - 0.08, hh - 0.01, hd - 0.04), (w1 + 0.08, hh + 0.08, hd + 0.05), 'hred', 'whead')
    o = box((0.3, 0.14, 0.12), ((d0 + d1) / 2, dh + 0.3, hd + 0.06), GL, name=fid + '_doorlamp'); K.add(o, 'bulbw')
    for x in (d0 - 0.2, d1 + 0.3): lantern(K, (x, 2.45, hd + 0.02), (0, 1), GL)  # (a carriage lamp each side of the door)
    # the west side (to the piers): the big window's frame, a window box of red flowers, a life ring, the forecast board
    for z_, s_ in ((s0, 1), (s1, -1)): K.bk((-hw - 0.05, sl, min(z_, z_ + s_ * 0.08)), (-hw + 0.04, hh, max(z_, z_ + s_ * 0.08)), 'hred', 'wjamb')
    K.bk((-hw - 0.14, sl - 0.05, s0 - 0.1), (-hw + 0.04, sl + 0.03, s1 + 0.1), 'pwhite', 'wsill'); K.bk((-hw - 0.05, hh - 0.01, s0 - 0.08), (-hw + 0.04, hh + 0.08, s1 + 0.08), 'hred', 'whead')
    flowerbox(K, -hw - 0.33, -hw - 0.03, s0 + 0.15, s1 - 0.15, sl - 0.36, ['flowerr', 'pwhite', 'flowerr'], 9)
    lifering(K, (-hw - 0.06, 1.55, -2.35), 'x', 'ring')
    o = K.bk((1.5, 0.5, St['z1'] - 0.002), (3.0, 1.18, St['z1'] + 0.04), 'chalkb', 'forecast'); uv_fit(o, A, 'chalk', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5)
    for z in (-hd + 0.4,):
        o = cyl(0.06, pp - 0.5, (hw + 0.1, (pp - 0.5) / 2 + 0.1, z), M, axis='y', seg=8, name=fid + '_pipe'); K.add(o, 'pwhite')
        K.bk((hw - 0.02, pp - 0.48, z - 0.08), (hw + 0.18, pp - 0.36, z + 0.08), 'pwhite', 'scupper'); K.bk((hw + 0.04, 0.02, z - 0.08), (hw + 0.2, 0.14, z + 0.08), 'pwhite', 'shoe')
    # the back door, swung in
    K.bk((k1 + 0.002, 0.04, -hd + t), (k1 + 0.05, dh - 0.06, -hd + t + 0.95), 'hblue', 'bdoor')
    for x, s_ in ((k0, 1), (k1, -1)): K.bk((min(x, x + s_ * 0.08), 0.02, -hd - 0.05), (max(x, x + s_ * 0.08), dh, -hd + 0.04), 'pwhite', 'bjamb')
    # ---- inside: the counter (a bicycle horn on it: honk), the chart table, the radio desk, the filing cabinet,
    # LOST: ONE BOAT on the notice board, a ship's wheel on the wall, a lamp
    c0, cz0, c1, cz1, ch = P['inside'][0]
    o = K.bk((c0 + 0.002, 0.0, cz0), (c1, ch - 0.05, cz1), 'pwhite', 'counter')
    uv_trim(o, A, 'counterf', upm=UPM, grain='x', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5); TR.kill_faces(o, lambda g, n: n.y < -0.5)
    K.bk((c0 + 0.002, ch - 0.05, cz0 - 0.04), (c1 + 0.05, ch, cz1 + 0.06), 'hred', 'ctop')
    o = ball(0.07, (-1.0, ch + 0.06, 0.7), M, seg=6, rings=4, name=fid + '_bulb'); K.add(o, 'hred')
    o = lathe([(0.02, 0.0), (0.02, 0.18), (0.06, 0.24), (0.07, 0.25)], (-0.93, ch + 0.06, 0.7), M, seg=8, axis='x', name=fid + '_trumpet', cap=False); K.add(o, 'gold')
    K.bk((-2.6, ch, 0.5), (-2.2, ch + 0.04, 0.8), 'pnavy', 'book')
    x0, z0, x1, z1, h = P['inside'][1]
    for xx in (x0 + 0.08, x1 - 0.08):
        for zz in (z0 + 0.08, z1 - 0.08): K.rod((xx, 0.0, zz), (xx, h - 0.04, zz), 0.035, 'oak', 'cleg', seg=6)
    o = K.bk((x0, h - 0.04, z0), (x1, h, z1), 'oak', 'ctable'); uv_fit(o, A, 'chart', sel=lambda p, Pp: MK._gn(p.normal).y > 0.5)
    x0, z0, x1, z1, h = P['inside'][2]
    K.bk((x0 + 0.002, h - 0.05, z0 + 0.002), (x1, h, z1), 'oak', 'rdesk')
    K.bk((x0 + 0.002, 0.0, z0 + 0.002), (x1, h - 0.05, z0 + 0.5), 'steel', 'rped'); K.bk((x0 + 0.002, 0.0, z1 - 0.5), (x1, h - 0.05, z1), 'steel', 'rped')
    o = K.bk((x0 + 0.05, h, z0 + 0.4), (x1 - 0.1, h + 0.28, z0 + 1.2), 'iron', 'radio'); uv_fit(o, A, 'radio', sel=lambda p, Pp: MK._gn(p.normal).x > 0.5)
    K.rod((x1 - 0.2, h, z0 + 1.5), (x1 - 0.2, h + 0.2, z0 + 1.5), 0.012, 'iron', 'mic', seg=5)
    o = ball(0.035, (x1 - 0.2, h + 0.23, z0 + 1.5), M, seg=6, rings=4, name=fid + '_micball'); K.add(o, 'iron')
    x0, z0, x1, z1, h = P['inside'][3]
    o = K.bk((x0, 0.0, z0), (x1 - 0.002, h, z1), 'steel', 'cabinet'); uv_fit(o, A, 'cabinet', sel=lambda p, Pp: MK._gn(p.normal).x < -0.5)
    o = K.bk((0.2, 1.3, -hd + t + 0.002), (1.6, 2.1, -hd + t + 0.03), 'oak', 'notice'); uv_fit(o, A, 'notice', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5)
    wx, wy, wz = hw - t - 0.06, 1.9, -1.4
    o = ring((wx, wy, wz), 0.42, 0.03, M, A, 'oak', fid + '_wheel', axis='x', n=12); K.P.append(o)
    for k in range(8):
        a = TAU * k / 8; K.rod((wx, wy, wz), (wx, wy + math.sin(a) * 0.56, wz + math.cos(a) * 0.56), 0.02, 'oak', 'spoke', seg=5)
    o = cyl(0.07, 0.12, (wx, wy, wz), M, axis='x', seg=8, name=fid + '_hub'); K.add(o, 'gold')
    K.bk((wx + 0.02, wy - 0.08, wz - 0.08), (hw - t + 0.002, wy + 0.08, wz + 0.08), 'oak', 'wmount')
    K.rod((0.0, H + 0.01, 0.0), (0.0, H - 0.6, 0.0), 0.01, 'iron', 'owire', seg=4)
    o = lathe([(0.03, 0.0), (0.3, -0.2), (0.32, -0.24), (0.0, -0.1)], (0.0, H - 0.6, 0.0), M, seg=10, axis='y', name=fid + '_shade'); K.add(o, 'hred')
    o = ball(0.08, (0.0, H - 0.74, 0.0), GL, seg=6, rings=4, name=fid + '_obulb'); K.add(o, 'bulbw')
    # in the lookout: a brass telescope on a tripod, aimed out the south window at the piers
    tx_, tz_ = -2.0, -0.4
    for a in (0.3, 2.4, 4.5): K.rod((tx_, T + 1.05, tz_), (tx_ + math.cos(a) * 0.35, T + 0.01, tz_ + math.sin(a) * 0.35), 0.015, 'iron', 'tripod', seg=4)
    o = cyl(0.06, 0.9, (tx_, T + 1.15, tz_ + 0.05), M, axis='z', seg=8, r2=0.045, name=fid + '_scope'); TR.bake_tf(o)
    o.data.transform(Matrix.Translation(-gv(tx_, T + 1.15, tz_))); o.data.transform(Matrix.Rotation(0.12, 4, 'X')); o.data.transform(Matrix.Translation(gv(tx_, T + 1.1, tz_ + 0.05))); o.data.update(); K.add(o, 'gold')
    for p in K.P: crisp(p)
    # ---- far LOD: the office with its front painted on, the stair, the tower, the lookout, the pyramid
    o = K.bk((-hw, 0, -hd), (hw, pp, hd), 'side1', '1_office', far=True); uv_fit(o, A, 'facade1', sel=lambda p, Pp: MK._gn(p.normal).z > 0.5)
    TR.kill_faces(TR.bake_tf(o), lambda g, n: n.y < -0.5)
    o = stepped(fid + '1_stair', M, A, [(St['x0'], 0.0), (St['land'], rt), (St['land'], 0.0)], St['z0'], St['z1'], 'tread', 'pwhite', 'pwhite', kill=lambda g, n: (n.y < -0.5 and g.y < 0.01) or n.z < -0.5)
    K.Q.append(o)
    K.bk((tx0, pp, tz0), (tx1, T, tz1), 'pwhite', '1_tower', far=True)
    K.bk((gx0, T - 0.15, gz0), (gx1, rh, gz1), 'pwhite', '1_gallery', far=True)
    o = K.bk((tx0, rh, tz0), (tx1, rtop, tz1), 'hred', '1_look', far=True)
    K.bk((tx0 - 0.3, rtop, tz0 - 0.3), (tx1 + 0.3, rtop + P['cap'], tz1 + 0.3), 'pwhite', '1_lroof', far=True)
    o = lathe([(ry_ * math.sqrt(2), 0.0), (0.0, ph)], pc, M, seg=4, axis='y', name=fid + '1_pyramid', cap=False)
    TR.bake_tf(o); o.data.transform(Matrix.Translation(-gv(*pc))); o.data.transform(Matrix.Rotation(math.pi / 4, 4, 'Z')); o.data.transform(Matrix.Translation(gv(*pc))); o.data.update(); K.add(o, 'hred', far=True)
    for p in K.Q: crisp(p)
    for p in K.P + K.Q: tri_ngons(p)
    lo, hi = extent(hm_boxes())
    return dict(lod0=K.P, lod1=K.Q, box=(lo, hi), ao=0.8, aolo=0.5, lod=130, eps=0.001, sheet=dict(exposure=-1.0), post=lambda l0, l1: [bounce(o) for o in (l0, l1)],
                focus=[((-1.5, 2.0, hd), (-0.4, 0.15, 1.0), 9.0), ((-2.2, 5.3, tz1), (0.0, 0.05, 1.0), 4.5), ((-2.2, T + 1.2, -1.3), (0.6, 0.5, 1.0), 6.5),
                       ((-1.0, 1.4, 0.0), (0.3, 0.6, 1.0), 4.5), ((-2.2, rtop + 1.5, -1.3), (-0.7, 0.3, 1.0), 4.5), ((1.2, 5.5, 1.0), (1.0, 0.3, 0.5), 8.0)])


# ------------------------------------------------------------ main
if __name__ == '__main__':
    todo = [(f, fn) for f, fn in PROPS if not ONLY or f[5:] in ONLY or f[2:] in ONLY or f in ONLY]
    for fid, fn in todo:
        run_bi(fid, fn)
