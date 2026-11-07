# The Cheat Machine (zombies): a cyberpunk vending / slot cabinet you pay for a random short power-up. Nubby's-style
# garish numbers and dice on candy paint, Cruelty Squad grime and meat, chrome everywhere. Real-size cabinet: 1.04 m
# between the side panels (1.1 with the marquee), 0.82 deep, 2.22 tall to the top of the beacon, feet at y 0, front +z.
#   marquee   CHEAT in pink neon tube (real tubes on stand-offs), MACHINE backlit in cyan under it, neon dice either
#             side, chrome frame, candy-striped box, two fat glossy dice and the beacon on top
#   screen    a 0.78 x 0.52 recess in the bezel with black glass at the back (the game draws its own animated canvas on
#             it: meta screen = the glass's centre + the canvas size), 14 chase bulbs in chrome sockets round it
#   deck      a big pink DON'T button (a PRESS sticker points at it), two small ones, 1 PAY 2 PULL 3 CHEAT on the front
#   door      a big ? (mystery prize), the coin door (glowing coin entry, bill slot, INSERT CASH plate), a ticket slot
#             spitting a strip of tickets, the prize bay with its flap shoved open by a tongue, a dented steel kick plate
#   sides     side art (a giant 7, tumbling dice, numbers), glowing cyan edge strips; on the right the slot machine
#             lever, on the left a crooked dented service panel (WARRANTY VOID IF OPENED) with wires spilling out and a
#             loop of meat growing out of the cabinet; on the back DO NOT TIP (IT TIPS BACK) and the serial plate
# Nodes: `lever` (origin = its pivot, modelled up; the game turns it about local x, + = the knob swings forward),
# `lamp_wzN` (the beacon dome, origin at its centre, material zm_lamp). zm_neon = everything that's lit by the
# machine's power (the neon, the chase bulbs, the coin entry, the edge strips): its glow is its own texture, so with
# the emission turned down it's dead glass. meta: screen {c, w, h}, lever {pivot, axis, pull}.
# run: blender -b --python tools/blender/make_zmmachine.py   (-- --no-sheet  -- --no-export  -- --qa)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib
from bottom_kit import Atlas, grime, crust, uv_fit, xform, dent, uv_remap
from sidekit import bake_normals, text_c, quad
from corp import smiley_px
from zmkit import slab_xy, unzero, seg_dist, poly_fill, qa, glow_mat, dcut, plane_tube, rrect_pts, grid_plate

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
for k, g in {'$': ['00100', '01111', '10100', '01110', '00101', '11110', '00100'], '%': ['11000', '11001', '00010', '00100', '01000', '10011', '00011'],
             '?': ['01110', '10001', '00001', '00110', '00100', '00000', '00100']}.items(): FONT.setdefault(k, g)

XO, XI, FW = 0.52, 0.485, 0.486            # side panels' outer / inner face, the front panels' half width
SIDE = [(-0.40, 0.06), (0.30, 0.06), (0.30, 0.93), (0.42, 1.0), (0.42, 1.1), (0.31, 1.24), (0.31, 1.885), (-0.36, 1.885), (-0.40, 1.845)]  # (z, y)
DECK = [(0.29, 0.925), (0.42, 1.0), (0.42, 1.1), (0.31, 1.24), (0.29, 1.24)]
SLOPE = ((0.42, 1.1), (0.31, 1.24))       # the deck's top slope (z, y)
BEZ = (1.235, 1.885)                      # bezel bottom / top (y), front face z 0.31, 6 cm thick
SCR, SCR_W, SCR_H = (0.0, 1.58), 0.76, 0.50
OPN_W, OPN_H, OPN_R = 0.78, 0.52, 0.035
Z_BEZ, Z_GLASS = 0.31, 0.256
MQ = (1.88, 2.10, 0.36)                   # marquee bottom, top, front face z
BACK = (-0.53, 1.90, 0.53, 2.085)         # the neon backing quad (x0, y0, x1, y1)
Z_TUBE = 0.3785
PIVOT = (0.565, 1.05, -0.02)
LAMP_C = (0.0, 2.172, 0.0)


# ------------------------------------------------------------ painting helpers
def big_text(px, s, x0, y0, sc, fill, line=0x111111, shadow=None, ol=2, sh=(3, 3)):
    """chunky comic numbers: a hard offset shadow, a fat outline, the fill"""
    if shadow is not None:
        for dx in range(-ol, ol + 1):
            for dy in range(-ol, ol + 1): text_px(px, s, x0 + sh[0] + dx, y0 + sh[1] + dy, sc, shadow)
    for dx in range(-ol, ol + 1):
        for dy in range(-ol, ol + 1): text_px(px, s, x0 + dx, y0 + dy, sc, line)
    text_px(px, s, x0, y0, sc, fill)


def pips(n):
    g = {1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)], 4: [(0, 0), (2, 0), (0, 2), (2, 2)], 5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
         6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)]}
    return g[n]


def die_px(px, cx, cy, s, ang, n, face=0xffffff, pip=0x111111, line=0x111111):
    """a tumbling die painted flat: a turned square with an outline and n pips"""
    c, si = math.cos(ang), math.sin(ang)
    sq = lambda k: [(cx + (x * c - y * si) * k, cy + (x * si + y * c) * k) for x, y in ((-s / 2, -s / 2), (s / 2, -s / 2), (s / 2, s / 2), (-s / 2, s / 2))]
    poly_fill(px, sq(1.12), line); poly_fill(px, sq(1.0), face)
    for gx, gy in pips(n):
        x, y = (gx - 1) * s * 0.3, (gy - 1) * s * 0.3
        px_disc(px, cx + x * c - y * si, cy + x * si + y * c, max(1.2, s * 0.1), pip)


def stripes_px(px, cols, w, slope=1):
    h, wd = px.shape[:2]; y, x = np.mgrid[0:h, 0:wd]
    k = ((x + slope * y) // w) % len(cols)
    px[:] = np.stack([hexrgb(c) for c in cols])[k]


# ------------------------------------------------------------ the neon: CHEAT as real tubes (unit cells, y up)
def arcpts(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


NEON = {
    'C': ([arcpts(0.36, 0.5, 0.36, 0.5, 46, 314, 8)], 0.68),
    'H': ([[(0, 0), (0, 1)], [(0.64, 0), (0.64, 1)], [(0, 0.53), (0.64, 0.53)]], 0.64),
    'E': ([[(0.6, 1), (0, 1), (0, 0), (0.6, 0)], [(0, 0.53), (0.46, 0.53)]], 0.6),
    'A': ([[(0, 0), (0.34, 1), (0.68, 0)], [(0.15, 0.4), (0.53, 0.4)]], 0.68),
    'T': ([[(0, 1), (0.66, 1)], [(0.33, 1), (0.33, 0)]], 0.66),
}


def chamfer(pts, r=0.09):
    """round a polyline's corners off (neon is bent glass: no sharp corners)"""
    if len(pts) < 3: return pts
    out = [pts[0]]
    for a, p, b in zip(pts, pts[1:], pts[2:]):
        p, a, b = Vector(p), Vector(a), Vector(b)
        ka, kb = min(r / (a - p).length, 0.4), min(r / (b - p).length, 0.4)
        out += [tuple(p + (a - p) * ka), tuple(p + (p - p) + ((a - p) * ka + (b - p) * kb) * 0.22), tuple(p + (b - p) * kb)]
    return out + [pts[-1]]


def neon_strokes(word, x_mid, y0, hn, slant=0.16, gap=0.27):
    """the word's strokes in game metres [(x, y)], centred on x_mid, baseline y0, cap height hn"""
    w = sum(NEON[c][1] for c in word) + gap * (len(word) - 1)
    x = -w / 2; out = []
    for c in word:
        strokes, adv = NEON[c]
        for st in strokes:
            st = st if c == 'C' else chamfer(st)
            out.append([(x_mid + (x + sx + slant * sy) * hn - slant * hn / 2, y0 + sy * hn) for sx, sy in st])
        x += adv + gap
    return out


CHEAT = neon_strokes('CHEAT', 0.0, 1.972, 0.1)
DICE_C = [(-0.405, 1.993, 5), (0.405, 1.993, 6)]  # the neon dice either side: centre, pips
DIE_LOOP = lambda cx, cy: rrect_pts(cx, cy, 0.124, 0.124, 0.024, 1)


# ------------------------------------------------------------ materials
PA = {'side': (0, 0, 120, 256), 'door': (120, 0, 136, 112), 'bezel': (120, 112, 136, 96), 'mside': (120, 208, 136, 48)}
DA = {'norefunds': (0, 0, 64, 16), 'legit': (64, 0, 88, 16), 'nokick': (152, 0, 64, 16), 'corp': (216, 0, 40, 16),
      'warranty': (0, 16, 96, 16), 'luck': (96, 16, 96, 16), 'price': (192, 16, 64, 16), 'steps': (0, 32, 160, 16), 'take': (160, 32, 96, 16),
      'serial': (0, 48, 104, 40), 'vents': (104, 48, 64, 40), 'flap': (168, 48, 48, 24), 'ticket': (144, 88, 112, 16), 'press': (216, 48, 40, 12), 'tip': (0, 136, 112, 32)}
NEON_W, NEON_H = 256, 64
DH = 168  # the decal atlas' height
SW = {k: (i * 32, 48, 32, 16) for i, k in enumerate(('pink', 'cyan', 'bulb', 'red', 'green', 'white', 'led', 'hot'))}
BA = {'dont': (0, 0, 32, 32), 'red': (32, 0, 16, 16), 'yellow': (48, 0, 16, 16), 'cyan': (32, 16, 16, 16), 'pink': (48, 16, 16, 16)}
WA = {k: (i * 8, 0, 8, 8) for i, k in enumerate(('red', 'yellow', 'green', 'blue', 'copper'))}


def rect(W, h, r):  # pixel box -> uv rect in a W x h image (top-left origin), half a texel in
    x, y, w, hh = r
    return ((x + 0.5) / W, 1 - (y + hh - 0.5) / h, (x + w - 0.5) / W, 1 - (y + 0.5) / h)


def bpx(x, y):  # the neon backing's pixel for a game point (x, y) on it
    return (x - BACK[0]) / (BACK[2] - BACK[0]) * NEON_W, (BACK[3] - y) / (BACK[3] - BACK[1]) * 48


def materials():
    M = {}
    # ---------------- candy paint atlas: side art, the door, the bezel, the marquee's stripes
    P = Atlas('zm_paint_t', 256, 256)
    s = P.sub(*PA['side']); crust(s, 0x1d0e2a, 0.12, seed=101)
    poly_fill(s, [(0, 214), (120, 112), (120, 146), (0, 248)], 0xff4fd8)  # a pink band climbing to the back
    px_line(s, 0, 211, 120, 109, 0xffe14d, 2.2); px_line(s, 0, 251, 120, 149, 0xffe14d, 2.2)
    for k in range(0, 9, 3): px_line(s, 0, 222 + k * 3, 120, 120 + k * 3, 0xff7ae4, 0.6)
    big_text(s, '7', 36, 30, 10, 0xffe14d, 0x111111, shadow=0x4fd8ff, ol=2, sh=(5, 5))
    die_px(s, 86, 132, 26, 0.45, 5); die_px(s, 40, 168, 20, -0.3, 3, face=0xffe14d); die_px(s, 96, 214, 16, 0.9, 2, face=0x4fd8ff)
    for t, x, y, c, sc in (('X2', 66, 14, 0x39ff14, 2), ('%', 98, 100, 0x4fd8ff, 2), ('+1', 24, 112, 0xff4fd8, 2), ('9', 100, 176, 0xffe14d, 2), ('3', 30, 226, 0x39ff14, 2),
                           ('$', 104, 40, 0xffe14d, 2)):
        big_text(s, t, x, y, sc, c, 0x111111, ol=1)
    rng = np.random.default_rng(102)
    for k in range(70):  # confetti
        x, y = rng.integers(18, 118), rng.integers(4, 250)
        s[y:y + 2, x:x + 2] = hexrgb([0xff4fd8, 0xffe14d, 0x4fd8ff, 0x39ff14][k % 4])
    gy = np.linspace(0, 1, 60)[:, None, None]
    s[196:] = s[196:] * (1 - 0.45 * gy) + hexrgb(0x120a08) * 0.45 * gy  # grime toward the floor
    grime(s, 0x0a0608, p=0.12, seed=103, blob=3)
    for k in range(14):  # scratches through the paint
        x, y = rng.uniform(18, 118), rng.uniform(10, 250); a = rng.uniform(-0.6, 0.6)
        px_line(s, x, y, x + 14 * math.cos(a), y + 14 * math.sin(a), 0x8a7a9a, 0.6)
    d = P.sub(*PA['door']); crust(d, 0x190c24, 0.1, seed=111)
    y_, x_ = np.mgrid[0:112, 0:136]
    d[((x_ + y_) // 7) % 2 == 0] *= 1.25  # faint candy stripes
    d[3:5, 3:-3] = d[-5:-3, 3:-3] = hexrgb(0xff4fd8); d[3:-3, 3:5] = d[3:-3, -5:-3] = hexrgb(0xff4fd8)
    big_text(d, '?', 52, 16, 6, 0xffe14d, 0x111111, shadow=0xff4fd8, ol=2, sh=(4, 4))
    for t, x, y, c in (('7', 14, 44, 0x4fd8ff), ('X2', 98, 62, 0x39ff14), ('+', 26, 64, 0xff4fd8)):
        big_text(d, t, x, y, 2, c, 0x111111, ol=1)
    for x0 in (30, 33, 104, 107):  # toxic ooze running down from under the prize bay
        L = int(rng.integers(4, 9)); d[103:min(112, 103 + L), x0:x0 + 2] = hexrgb(0x7dff4f); d[min(111, 103 + L), x0 - 1:x0 + 3] = hexrgb(0x39c41a)
    d[98:] = d[98:] * 0.75
    grime(d, 0x08040a, p=0.1, seed=112, blob=3)
    b = P.sub(*PA['bezel']); crust(b, 0x150a1e, 0.08, seed=121)
    b[1:3, 10:126] = hexrgb(0xff4fd8)  # a pink rule along the top border
    for x, y in bulb_spots():  # dark sockets with a chrome rim under the bulbs
        u, v = (x + FW) / (2 * FW) * 136, (BEZ[1] - y) / (BEZ[1] - BEZ[0]) * 96
        px_disc(b, u, v, 3.0, 0x0a0608)
    grime(b, 0x08040a, p=0.06, seed=122, blob=3)
    ms = P.sub(*PA['mside']); stripes_px(ms, [0xff4fd8, 0xff4fd8, 0x1a0a20, 0xffe14d, 0xffe14d, 0x1a0a20], 3)
    grime(ms, 0x1a0a14, p=0.1, seed=131, blob=3)
    M['P'] = P
    M['paint'] = mat('zm_paint', 0xffffff, rough=0.24, clearcoat=1.0, tex=P.image())
    M['black'] = mat('zm_black', 0x1a1a20, rough=0.3, clearcoat=0.7, tex=tex_noise('zm_black_t', 0x1c1c24, var=0.1, size=16, speck=0x3a3440, speck_p=0.06, seed=141))
    M['chrome'] = mat('zm_chrome', 0xd8dde4, rough=0.12, metal=1.0, tex=tex_noise('zm_chrome_t', 0xd8dde4, var=0.06, size=16, speck=0x7a6a50, speck_p=0.05, seed=142))
    M['dark'] = mat('zm_dark', 0x09070c, rough=0.7)
    def steel(px):  # brushed steel with scuffs and a little rust
        r_ = np.random.default_rng(171); rows = np.convolve(r_.random(36), np.ones(3) / 3, 'same')[2:34]
        px[:] = hexrgb(0x7c848e)[None, None] * (0.88 + 0.12 * rows[:, None, None] + 0.06 * r_.random((32, 32, 1)))
        for k in range(10): x, y = r_.uniform(0, 32), r_.uniform(0, 32); px_line(px, x, y, x + r_.uniform(-6, 6), y + r_.uniform(-2, 2), 0x5a6068, 0.6)
        px[r_.random((32, 32)) < 0.03] = hexrgb(0x8a5a3a)
    M['steel'] = mat('zm_steel', 0xffffff, rough=0.36, metal=0.65, tex=tex_canvas('zm_steel_t', 32, 32, steel))
    M['glass'] = mat('zm_glass', 0x04050a, rough=0.04, clearcoat=1.0)
    M['rubber'] = mat('zm_rubber', 0x18181c, rough=0.85, tex=tex_noise('zm_rubber_t', 0x1a1a1e, var=0.15, size=8, seed=143))
    def meat(px):
        r_ = np.random.default_rng(144); n = np.zeros((64, 64))
        for o_, w_ in ((4, 0.5), (8, 0.3), (16, 0.2)): n += w_ * np.kron(r_.random((o_, o_)), np.ones((64 // o_, 64 // o_)))
        n = (n - n.min()) / (np.ptp(n) + 1e-6); t = np.clip((n - 0.45) / 0.35, 0, 1)[:, :, None]
        px[:] = hexrgb(0xf05a78)[None, None] * (1 - t) + hexrgb(0x8a1838)[None, None] * t
        hl = np.clip((0.3 - n) / 0.2, 0, 1)[:, :, None] * 0.7; px[:] = px * (1 - hl) + hexrgb(0xffb4c4)[None, None] * hl
        for k in range(7):  # veins wandering along the tube
            x, y = r_.uniform(0, 64), r_.uniform(0, 64); a = r_.uniform(0, 6.3)
            for st in range(9):
                a += r_.uniform(-0.7, 0.7); nx, ny = x + 3.5 * math.cos(a), y + 3.5 * math.sin(a)
                px_line(px, x, y, nx, ny, 0x5a1a6a if st < 6 else 0x7a2a7a, 1.4 if st < 4 else 0.9); x, y = nx % 64, ny % 64
        px[r_.random((64, 64)) < 0.025] = hexrgb(0xffe08a)
    M['meat'] = mat('zm_meat', 0xffffff, rough=0.16, clearcoat=1.0, tex=tex_canvas('zm_meat_t', 64, 64, meat))
    # ---------------- the neon: one texture for the unlit look (dead glass, a dark backing), one for the glow
    base = np.zeros((NEON_H, NEON_W, 3), np.float32); emit = np.zeros_like(base)
    bk = base[:48]; crust(bk, 0x120a1e, 0.1, seed=151)
    for x in range(0, NEON_W, 8): bk[:, x] = bk[:, x] * 0.7 + hexrgb(0x2a1a3e) * 0.3  # a faint grid behind the glass
    for y in range(0, 48, 8): bk[y, :] = bk[y, :] * 0.7 + hexrgb(0x2a1a3e) * 0.3
    segs = []
    for st in CHEAT: segs += [(bpx(*a), bpx(*b)) for a, b in zip(st, st[1:])]
    dsegs = []
    for cx, cy, n in DICE_C:
        lp = DIE_LOOP(cx, cy); dsegs += [(bpx(*a), bpx(*b)) for a, b in zip(lp, lp[1:] + lp[:1])]
    dc = seg_dist(48, NEON_W, segs); dd = seg_dist(48, NEON_W, dsegs)
    em = emit[:48]
    em += hexrgb(0xff4fd8)[None, None] * (0.5 * np.exp(-dc / 4.0))[:, :, None]
    em += hexrgb(0x4fd8ff)[None, None] * (0.42 * np.exp(-dd / 3.5))[:, :, None]
    bk[:] = bk * (1 - 0.35 * np.exp(-dc / 2.0))[:, :, None]  # the unlit tubes' shadows on the backing
    mach = np.zeros((48, NEON_W, 3), np.float32); text_c(mach, 'MACHINE', 128, 32, 2, 0xffffff)
    mk = mach.sum(2) > 0
    glow = mk.astype(np.float32)
    for k in range(3): glow = np.maximum(glow, 0.55 * (np.roll(glow, 1, 0) + np.roll(glow, -1, 0) + np.roll(glow, 1, 1) + np.roll(glow, -1, 1)) / 2)
    em += hexrgb(0x4fd8ff)[None, None] * (0.45 * glow)[:, :, None]
    em[mk] = hexrgb(0x8af0ff); bk[mk] = hexrgb(0x9ab8c8)
    for cx, cy, n in DICE_C:  # the dice's pips: little pink lamps
        for gx, gy in pips(n):
            u, v = bpx(cx + (gx - 1) * 0.036, cy - (gy - 1) * 0.036)
            px_disc(em, u, v, 3.4, 0x6a1050); px_disc(em, u, v, 2.4, 0xff6ae0); px_disc(bk, u, v, 2.4, 0xc898b8)
    for k, (cb, ce) in {'pink': (0xf0c0e0, 0xff4fd8), 'cyan': (0xc0e4f0, 0x4fd8ff), 'bulb': (0xf2ead0, 0xffe14d), 'red': (0x8a2a34, 0xff3030),
                        'green': (0x4a7a4a, 0x39ff14), 'white': (0xe8e8e8, 0xffffff), 'led': (0x5a8a9a, 0x4fd8ff), 'hot': (0x8a4a7a, 0xff4fd8)}.items():
        x, y, w, h = SW[k]; base[y:y + h, x:x + w] = hexrgb(cb); emit[y:y + h, x:x + w] = hexrgb(ce)
    M['neon'] = glow_mat('zm_neon', base, emit, strength=2.2, rough=0.12, clearcoat=1.0)
    # ---------------- the beacon dome: u = up, v = round (uv_cyl); a hot beam on one side so you can see it spin
    lb = np.zeros((32, 8, 3), np.float32); le = np.zeros_like(lb)
    lb[:] = hexrgb(0xc89a1c); le[:] = hexrgb(0xb08a10)
    for r in range(0, 32, 4): lb[r] *= 0.82; le[r] *= 0.8  # moulded ribs
    le[2:9] = hexrgb(0xfff2a0); le[4:7] = hexrgb(0xffffff); lb[2:9] = hexrgb(0xe8c040)
    le[:, 7] *= 0.6; lb[:, 7] *= 0.8
    M['lamp'] = glow_mat('zm_lamp', lb, le, strength=2.5, rough=0.12, clearcoat=1.0)
    # ---------------- stickers, plates, dice faces, tickets
    D = Atlas('zm_decal_t', 256, DH)
    def sticker(k, bg, lines, fg=0x111111, border=0x111111, sc=1, smile=False):
        r_ = D.sub(*DA[k]); r_[:] = hexrgb(border); r_[1:-1, 1:-1] = hexrgb(bg)
        h, w = r_.shape[:2]; x = 4
        if smile: smiley_px(r_, 3, (h - 8) // 2, 1, fg); x = 13
        y = (h - len(lines) * 8 + 1) // 2
        for t in lines:
            text_px(r_, t, x if smile else int((w - (len(t) * 6 - 1) * sc) / 2), y, sc, fg); y += 8
    sticker('norefunds', 0xe0202a, ['NO REFUNDS'], 0xffffff, 0xffffff)
    sticker('legit', 0xffe14d, ['TOTALLY LEGIT'], smile=True)
    sticker('nokick', 0xf4f4f0, ['DO NOT KICK'], 0xe0202a, 0xe0202a)
    sticker('corp', 0xffe14d, ['CORP'], smile=True)
    sticker('warranty', 0xc8ccd6, ['WARRANTY VOID', 'IF OPENED'], 0x1a1c28, 0x6a6e7a)
    sticker('luck', 0x4fd8ff, ['LUCK IS A SKILL'], 0x111111)
    sticker('price', 0xb8bcc6, ['INSERT', 'CASH'], 0x1a1c28, 0x5a5e6a)
    sticker('steps', 0x111111, ['1 PAY  2 PULL  3 CHEAT'], 0xffe14d, 0xff4fd8)
    sticker('take', 0x111111, ['TAKE YOUR CHEAT'], 0x7dff4f, 0x7dff4f)
    tp = D.sub(*DA['tip']); tp[:] = hexrgb(0xffe14d); tp[0] = tp[-1] = tp[:, 0] = tp[:, -1] = hexrgb(0x111111)
    tp[1, :] = tp[-2, :] = hexrgb(0x111111)
    poly_fill(tp, [(8, 27), (14, 27), (14, 19), (8, 19)], 0x111111); px_disc(tp, 11, 15, 2.6, 0x111111)  # a little person...
    poly_fill(tp, [(13, 26), (30, 10), (25, 5), (8, 21)], 0x111111); poly_fill(tp, [(15, 24), (28, 11), (25, 8), (11, 21)], 0xff4fd8)  # ...and the machine coming down
    px_line(tp, 18, 4, 22, 8, 0x111111, 1); px_line(tp, 21, 2, 24, 5, 0x111111, 1)
    text_px(tp, 'DO NOT TIP', 36, 7, 1, 0x111111); text_px(tp, 'IT TIPS BACK', 36, 18, 1, 0xe0102a)
    pz = D.sub(*DA['press']); pz[:] = hexrgb(0xffe14d); pz[0] = pz[-1] = hexrgb(0x111111); text_px(pz, 'PRESS', 2, 3, 1, 0x111111)
    for k in range(4): pz[6 - k:6 + k + 1, 34 + k] = hexrgb(0xe0102a)  # an arrow at the DON'T button
    sr = D.sub(*DA['serial']); sr[:] = hexrgb(0xb0b4bc); sr[0] = sr[-1] = hexrgb(0x5a5e66)
    for i, t in enumerate(('CHEAT MACHINE', 'MODEL CM-777', 'SERIAL 0000001', 'MADE IN JANK', 'DO NOT FEED')):
        text_px(sr, t, 3, (1, 9, 16, 24, 32)[i], 1, 0x1a1c28 if i != 4 else 0xc0102a)
    vt = D.sub(*DA['vents']); vt[:] = hexrgb(0x1c1c22)
    for k in range(6): vt[4 + k * 6:8 + k * 6, 4:60] = hexrgb(0x050507)
    fl = D.sub(*DA['flap']); crust(fl, 0x2a2232, 0.08, seed=161); fl[:2] = hexrgb(0x5a4a66); text_c(fl, 'PUSH', 24, 9, 1, 0xff4fd8)
    tk = D.sub(*DA['ticket']); tk[:] = hexrgb(0xff8ad8)
    for i in range(5):
        tk[:, i * 22] = hexrgb(0x9a2a7a)
        tk[3:13, i * 22 + 4:i * 22 + 18] = hexrgb(0xffd0f0); text_px(tk, str((i * 3 + 1) % 10), i * 22 + 9, 4, 1, 0x3a0a2a)
    for row, (fc, pc) in enumerate(((0xff4fd8, 0xffffff), (0xffe14d, 0x111111))):
        for n in range(1, 7):
            c_ = D.sub((n - 1) * 24, 88 + row * 24, 24, 24) if row == 0 else D.sub((n - 1) * 24, 112, 24, 24)
            c_[:] = hexrgb(fc); c_[0] = c_[-1] = c_[:, 0] = c_[:, -1] = hexrgb(0x8a1a6a if row == 0 else 0xb89a20)
            for gx, gy in pips(n): px_disc(c_, 6 + gx * 6, 6 + gy * 6, 2.6, pc)
    M['D'] = D
    M['decal'] = mat('zm_decal', 0xffffff, rough=0.32, clearcoat=0.5, tex=D.image())
    # ---------------- buttons + the lever knob
    def btn(px):
        px[:, :32] = hexrgb(0xff3fcf); px_disc(px, 16, 16, 15.5, 0xd0209a, r_in=13.5)
        text_c(px[:, :32], "DON'T", 16, 12, 1, 0xffffff)
        px[0:16, 32:48] = hexrgb(0xe8182a); px[0:16, 48:64] = hexrgb(0xffe14d); px[16:32, 32:48] = hexrgb(0x4fd8ff); px[16:32, 48:64] = hexrgb(0xff4fd8)
    M['button'] = mat('zm_button', 0xffffff, rough=0.12, clearcoat=1.0, tex=tex_canvas('zm_button_t', 64, 32, btn))
    def wires(px):
        for k, c in zip(WA, (0xe0202a, 0xffd21a, 0x2ab83a, 0x2a6aff, 0xd08040)): x = WA[k][0]; px[:, x:x + 8] = hexrgb(c)
    M['wire'] = mat('zm_wire', 0xffffff, rough=0.35, clearcoat=0.6, tex=tex_canvas('zm_wire_t', 40, 8, wires))
    return M


def bulb_spots():
    out = [(sx * 0.438, 1.39 + 0.127 * i) for sx in (-1, 1) for i in range(4)]
    return out + [(-0.33 + 0.132 * i, 1.278) for i in range(6)]


# ------------------------------------------------------------ build
def onto(o, k, M):  # an object's uvs into a swatch / region of its material's atlas
    tbl = {'paint': (PA, 256, 256), 'decal': (DA, 256, DH), 'neon': (SW, NEON_W, NEON_H), 'button': (BA, 64, 32), 'wire': (WA, 40, 8)}
    mname = next(n for n, m in M.items() if m == o.data.materials[0])
    regions, W, H = tbl[mname]
    uv_fit(o, rect(W, H, regions[k]))
    return unzero(o)


def sticker_q(c, w, h, k, M, axis='z', sx=1, ang=0.0):
    q = quad(c, w, h, M['decal'], axis=axis, sx=sx, name='sticker_' + k)
    uv_remap(q, rect(256, DH, DA[k]))
    if ang: xform([q], rot=(ang, 0, 0) if axis == 'x' else (0, 0, ang), pivot=c)
    return q


def zy_strip(pts, x0, x1, d0, d1, m, ref=(0.0, 1.0), name='strip'):
    """a flat strip along a side-view path [(z, y)] (an edge of the cabinet), from x0 to x1 across, d0..d1 out from the
    path (away from ref): the glowing edge trim"""
    n = len(pts); P = [Vector(p) for p in pts]; R = Vector(ref)
    bm = bmesh.new(); rings = []
    for i in range(n):
        if 0 < i < n - 1:
            t1 = (P[i] - P[i - 1]).normalized(); t2 = (P[i + 1] - P[i]).normalized(); t = (t1 + t2).normalized(); k = 1 / max(0.45, t1.dot(t))
        else: t = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized(); k = 1.0
        nr = Vector((-t.y, t.x))
        if nr.dot(P[i] - R) < 0: nr = -nr
        rings.append([bm.verts.new(gv(x, (P[i] + nr * dd * k).y, (P[i] + nr * dd * k).x)) for x, dd in ((x0, d0), (x1, d0), (x1, d1), (x0, d1))])
    for i in range(n - 1):
        for j in range(4):
            jj = (j + 1) % 4
            bm.faces.new((rings[i][j], rings[i][jj], rings[i + 1][jj], rings[i + 1][j]))
    bm.faces.new(rings[0]); bm.faces.new(rings[-1][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = lib._obj(name, bm, m); smooth(o, 30)
    return o


def hit_x(objs, y, z, default=-XO):
    """where a ray along +x from outside the left side first hits objs (game x)"""
    from mathutils.bvhtree import BVHTree
    vs, fs = [], []
    for o in objs:
        apply_mods(o); me = o.data; mw = o.matrix_world; b = len(vs)
        vs += [mw @ v.co for v in me.vertices]; fs += [[b + i for i in p.vertices] for p in me.polygons]
    h = BVHTree.FromPolygons(vs, fs).ray_cast(gv(-1.0, y, z), Vector((1, 0, 0)))
    return h[0].x if h[0] is not None else default


def die3d(size, pos, ang, row, nums, M):
    """a fat glossy die: nums = the pips facing (+y, -y, +z, -z, +x, -x)"""
    o = box((size, size, size), (0, 0, 0), M['decal'], bev=size * 0.14, seg=2, name='die')
    apply_mods(o)
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data; h = size / 2
    for pg in me.polygons:
        n = pg.normal; g = (n.x, n.z, -n.y); ax = max(range(3), key=lambda i: abs(g[i]))
        key = {(1, 1): 0, (1, -1): 1, (2, 1): 2, (2, -1): 3, (0, 1): 4, (0, -1): 5}[(ax, 1 if g[ax] > 0 else -1)]
        cell = ((nums[key] - 1) * 24, 88 + row * 24, 24, 24)
        r_ = rect(256, DH, cell)
        for li in pg.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co; x, y, z = v.x, v.z, -v.y
            u, w = {0: (-z if g[0] > 0 else z, y), 1: (x, -z if g[1] > 0 else z), 2: (x if g[2] > 0 else -x, y)}[ax]
            u, w = (u + h) / size, (w + h) / size
            uv[li].uv = (r_[0] + u * (r_[2] - r_[0]), r_[1] + w * (r_[3] - r_[1]))
    xform([o], rot=(0, ang, 0), move=pos)
    return o


def build():
    M = materials()
    P = []; A = P.append
    # ---------------- cabinet: side panels with their glowing edge strips, back, plinth, feet
    for sx in (-1, 1):
        sp = side(SIDE, XO - XI, (sx * (XO + XI) / 2, 0, 0), M['paint'], bev=0.006, seg=1, name='side')
        onto(sp, 'side', M); A(sp)
        front = [(0.30, 0.06), (0.30, 0.925), (0.42, 1.0), (0.42, 1.1), (0.31, 1.24), (0.31, 1.885)]
        led = zy_strip(front, sx * (XO - 0.019), sx * XO + sx * 0.002, -0.001, 0.0055, M['neon'], ref=(0.0, 1.0), name='led')
        onto(led, 'led', M); A(led)
    A(box((2 * FW, 1.825, 0.02), (0, 0.9725, -0.39), M['black'], bev=0.003, seg=1, name='back'))
    A(sticker_q((0, 1.6, -0.4015), 0.4, 0.25, 'vents', M, axis='z', sx=-1))
    A(sticker_q((0.22, 0.9, -0.4015), 0.26, 0.1, 'serial', M, axis='z', sx=-1))
    A(sticker_q((-0.16, 1.22, -0.4015), 0.36, 0.103, 'tip', M, axis='z', sx=-1, ang=0.03))
    A(box((0.94, 0.06, 0.62), (0, 0.05, -0.06), M['black'], name='plinth'))
    for x in (-0.47, 0.47):
        for z in (-0.33, 0.23):
            A(lathe([(0.032, 0.0), (0.028, 0.014), (0.012, 0.018), (0.016, 0.064)], (x, 0, z), M['chrome'], seg=6, axis='y', name='foot'))
    # ---------------- kick plate (chrome, kicked in) and the door: the big ?, the prize bay, the coin door, tickets
    kp = grid_plate(2 * FW, 0.1, 0.012, 12, 3, M['steel'], 'kick')
    xform([kp], move=(0, 0.11, 0.306))
    dent(kp, (-0.3, 0.1, 0.312), 0.085, 0.009, axis=(0, 0, -1)); dent(kp, (-0.18, 0.13, 0.312), 0.05, 0.005, axis=(0, 0, -1))
    uv_box(kp, 0.4); A(kp)
    door = box((2 * FW, 0.77, 0.02), (0, 0.545, 0.29), M['paint'], name='door')
    onto(door, 'door', M)
    cutter = box((0.5, 0.2, 0.1), (0, 0.32, 0.29), M['dark']); uv_fit(cutter, (0, 0, 0.02, 0.02))
    dcut(door, cutter); A(door)
    tub = box((0.52, 0.22, 0.13), (0, 0.32, 0.215), M['dark'], name='tub')
    bm = bmesh.new(); bm.from_mesh(tub.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.y < -0.9], context='FACES')  # open to the front
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(tub.data); bm.free(); A(tub)
    A(plane_tube(rrect_pts(0, 0.32, 0.512, 0.212, 0.012, 1), 0.302, 0.006, M['chrome'], seg=4, closed=True, name='bay_trim'))
    fl = box((0.48, 0.17, 0.008), (0, 0.0, 0.0), M['decal'], bev=0.002, seg=1, name='flap')
    onto(fl, 'flap', M); xform([fl], rot=(-0.38, 0, 0), move=(0, 0.415 - 0.085, 0.29), pivot=(0, 0.085, 0)); A(fl)
    A(cyl(0.006, 0.5, (0, 0.415, 0.29), M['chrome'], axis='x', seg=6, name='hinge'))
    tongue = [(0.0, 0.228, 0.17), (0.008, 0.228, 0.24), (0.0, 0.239, 0.295), (-0.012, 0.226, 0.325), (-0.02, 0.185, 0.335), (-0.026, 0.13, 0.334), (-0.022, 0.09, 0.33), (-0.01, 0.072, 0.338)]
    tg = sweep(tongue, [0.04, 0.05, 0.054, 0.056, 0.053, 0.047, 0.036, 0.02], M['meat'], seg=8, squash=(0.36, 1.0), name='tongue')
    uv_box(tg, 0.06); A(tg)
    A(sticker_q((0, 0.472, 0.3015), 0.3, 0.05, 'take', M))
    A(sticker_q((-0.37, 0.2, 0.3015), 0.14, 0.036, 'nokick', M, ang=0.12))
    A(sticker_q((0.38, 0.195, 0.3015), 0.09, 0.036, 'corp', M, ang=-0.06))
    A(sticker_q((-0.36, 0.5, 0.3015), 0.17, 0.042, 'norefunds', M, ang=-0.1))
    # coin door: chrome plate, the glowing coin entry, a bill slot with a green arrow, coin return, lock, price plate
    A(box((0.24, 0.3, 0.008), (0.26, 0.7, 0.304), M['chrome'], bev=0.0025, seg=1, name='coin_door'))
    ce = box((0.036, 0.052, 0.006), (0.2, 0.79, 0.31), M['neon'], bev=0.002, seg=1, name='coin_lit'); onto(ce, 'red', M); A(ce)
    A(box((0.006, 0.034, 0.004), (0.2, 0.79, 0.3135), M['dark'], name='coin_slot'))
    A(box((0.1, 0.042, 0.022), (0.29, 0.68, 0.316), M['black'], bev=0.004, seg=1, name='bill'))
    A(box((0.08, 0.006, 0.004), (0.29, 0.686, 0.3275), M['dark'], name='bill_slot'))
    ar = box((0.03, 0.01, 0.004), (0.29, 0.669, 0.3265), M['neon'], name='bill_arrow'); onto(ar, 'green', M); A(ar)
    A(cyl(0.017, 0.012, (0.2, 0.705, 0.313), M['chrome'], axis='z', seg=10, name='coin_return'))
    A(cyl(0.011, 0.008, (0.34, 0.8, 0.311), M['dark'], axis='z', seg=8, name='lock'))
    A(sticker_q((0.26, 0.6, 0.3095), 0.12, 0.048, 'price', M))
    # ticket slot + a strip of tickets curling out of it
    A(box((0.16, 0.036, 0.022), (-0.26, 0.8, 0.31), M['black'], bev=0.004, seg=1, name='ticket_box'))
    A(box((0.12, 0.006, 0.004), (-0.26, 0.8, 0.3215), M['dark'], name='ticket_slot'))
    tpath = [(-0.26, 0.8, 0.318), (-0.26, 0.8, 0.336), (-0.258, 0.79, 0.352), (-0.255, 0.765, 0.36), (-0.25, 0.72, 0.358), (-0.247, 0.67, 0.35), (-0.245, 0.63, 0.347),
             (-0.243, 0.6, 0.352), (-0.242, 0.585, 0.366)]
    tk = sweep(tpath, 0.026, M['decal'], seg=4, squash=(0.03, 1.0), name='tickets')
    me = tk.data; me.uv_layers.new(name='UVMap'); uv = me.uv_layers.active.data; tr = rect(256, DH, DA['ticket'])
    for pg in me.polygons:
        for li in pg.loop_indices:
            vi = me.loops[li].vertex_index; ring, k = divmod(vi, 4)
            u = ring / (len(tpath) - 1); w = {0: 0.5, 1: 1.0, 2: 0.5, 3: 0.0}[k]
            uv[li].uv = (tr[0] + u * (tr[2] - tr[0]), tr[1] + w * (tr[3] - tr[1]))
    unzero(tk); A(tk)
    # ---------------- the deck: DON'T button, two small ones, the steps
    sz, sy = SLOPE[0]; ez, ey = SLOPE[1]
    deck = side(DECK, 2 * FW, (0, 0, 0), M['black'], bev=0.005, seg=2, name='deck'); uv_box(deck, 0.1); A(deck)
    A(sticker_q((0, 1.05, 0.4215), 0.62, 0.045, 'steps', M))
    th = math.atan2(ey - sy, sz - ez)  # the slope's normal, tipped forward from straight up
    def on_slope(t, x):
        return (x, sy + (ey - sy) * t, sz + (ez - sz) * t)
    def button(c, r, k, name, seg=12):
        rim = lathe([(r + 0.016, -0.002), (r + 0.016, 0.01), (r + 0.008, 0.018), (r + 0.002, 0.016)], (0, 0, 0), M['chrome'], seg=seg, axis='y', name=name + '_rim', cap=False)
        cap_ = lathe([(r, 0.0), (r, 0.024), (r * 0.9, 0.036), (r * 0.6, 0.045), (0.0, 0.048)], (0, 0, 0), M['button'], seg=seg, axis='y', name=name)
        me = cap_.data; me.uv_layers.new(name='UVMap'); uv = me.uv_layers.active.data; br = rect(64, 32, BA[k])
        for pg in me.polygons:
            for li in pg.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                u, w = v.x / (2 * r) + 0.5, v.y / (2 * r) + 0.5  # (blender y = game -z: the print's top faces the screen)
                uv[li].uv = (br[0] + u * (br[2] - br[0]), br[1] + w * (br[3] - br[1]))
        unzero(cap_)
        uv_box(rim, 0.05)
        xform([rim, cap_], rot=(th, 0, 0), move=c)
        return [rim, cap_]
    P += button(on_slope(0.5, 0.0), 0.068, 'dont', 'big_button')
    pr = sticker_q(on_slope(0.5, -0.16), 0.085, 0.026, 'press', M); xform([pr], rot=(th - math.pi / 2, 0, 0), pivot=on_slope(0.5, -0.16))
    xform([pr], move=(0, math.cos(th) * 0.0015, math.sin(th) * 0.0015)); A(pr)
    P += button(on_slope(0.52, -0.28), 0.03, 'yellow', 'btn_y', seg=8)
    P += button(on_slope(0.52, 0.28), 0.03, 'cyan', 'btn_c', seg=8)
    # ---------------- the bezel: the screen recess, black glass at the back, a chrome lip, chase bulbs
    bz = box((2 * FW, BEZ[1] - BEZ[0], 0.06), (0, (BEZ[0] + BEZ[1]) / 2, 0.28), M['paint'], name='bezel')
    onto(bz, 'bezel', M)
    cut_ = slab_xy(rrect_pts(SCR[0], SCR[1], OPN_W, OPN_H, OPN_R, 3), 0.2, 0.4, M['dark'], 'cut'); uv_fit(cut_, (0, 0, 0.02, 0.02))
    dcut(bz, cut_); A(bz)
    gl = quad((SCR[0], SCR[1], Z_GLASS), OPN_W + 0.01, OPN_H + 0.01, M['glass'], axis='z', name='glass'); A(gl)
    A(plane_tube(rrect_pts(SCR[0], SCR[1], OPN_W + 0.012, OPN_H + 0.012, OPN_R + 0.006, 2), Z_BEZ + 0.001, 0.0065, M['chrome'], seg=5, closed=True, name='lip'))
    for x, y in bulb_spots():
        bl = lathe([(0.0145, 0.309), (0.014, 0.32), (0.009, 0.329), (0.0, 0.3315)], (x, y, 0), M['neon'], seg=6, axis='z', name='bulb', cap=False)
        A(lathe([(0.0205, 0.309), (0.0205, 0.3145), (0.0165, 0.3165)], (x, y, 0), M['chrome'], seg=6, axis='z', name='socket', cap=False))
        onto(bl, 'bulb', M); A(bl)
    # ---------------- marquee: striped box, chrome frame, the backing, CHEAT in tube, neon dice, dice + beacon on top
    mq = box((1.1, MQ[1] - MQ[0], 0.72), (0, (MQ[0] + MQ[1]) / 2, 0.0), M['paint'], bev=0.008, seg=2, name='marquee'); onto(mq, 'mside', M); A(mq)
    me = mq.data; uv = me.uv_layers.active.data; dk = rect(256, 256, (160, 140, 40, 30))
    for pg in me.polygons:  # (blender z = game up, blender y = game -z)
        if pg.normal.z > 0.7 or pg.normal.z < -0.7 or pg.normal.y > 0.7:
            for li in pg.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                w = (v.y / 0.72 + 0.5) if abs(pg.normal.z) > 0.7 else (v.z / 0.22 + 0.5)
                uv[li].uv = (dk[0] + (v.x / 1.1 + 0.5) * (dk[2] - dk[0]), dk[1] + w * (dk[3] - dk[1]))
    unzero(mq)
    for (w, h), (x, y) in (((1.1, 0.022), (0, MQ[1] - 0.011)), ((1.1, 0.022), (0, MQ[0] + 0.011)), ((0.022, 0.172), (-0.539, 1.99)), ((0.022, 0.172), (0.539, 1.99))):
        A(box((w, h, 0.03), (x, y, MQ[2] + 0.01), M['chrome'], bev=0.004, seg=1, name='mq_frame'))
    bq = quad(((BACK[0] + BACK[2]) / 2, (BACK[1] + BACK[3]) / 2, MQ[2] + 0.0015), BACK[2] - BACK[0], BACK[3] - BACK[1], M['neon'], axis='z', name='backing')
    uv_remap(bq, rect(NEON_W, NEON_H, (0, 0, 256, 48))); A(bq)
    for st in CHEAT:
        t = plane_tube(st, Z_TUBE, 0.0065, M['neon'], seg=6, name='neon'); onto(t, 'pink', M); A(t)
    for st in CHEAT[::3]:  # glass stand-offs holding the tubes off the backing
        x, y = st[len(st) // 2]
        A(cyl(0.0028, Z_TUBE - MQ[2] - 0.002, (x, y, (Z_TUBE + MQ[2]) / 2), M['chrome'], axis='z', seg=4, name='standoff'))
    for cx, cy, n in DICE_C:
        t = plane_tube(DIE_LOOP(cx, cy), Z_TUBE - 0.002, 0.0055, M['neon'], seg=6, closed=True, name='neon_die'); onto(t, 'cyan', M); A(t)
        for sy in (-1, 1): A(cyl(0.0028, Z_TUBE - MQ[2] - 0.004, (cx, cy + sy * 0.062, (Z_TUBE - 0.002 + MQ[2]) / 2), M['chrome'], axis='z', seg=4, name='standoff'))
    A(die3d(0.11, (-0.43, MQ[1] + 0.055 - 0.001, 0.13), 0.42, 0, (5, 2, 6, 1, 3, 4), M))
    A(die3d(0.1, (0.44, MQ[1] + 0.05 - 0.001, 0.15), -0.3, 1, (6, 1, 4, 3, 2, 5), M))
    A(sticker_q((0.5515, 1.99, 0.08), 0.18, 0.033, 'legit', M, axis='x', sx=1, ang=0.06))
    # the beacon: chrome base, a wire guard over the dome (the dome is its own node)
    A(lathe([(0.074, MQ[1] - 0.002), (0.074, 2.112), (0.068, 2.12), (0.062, 2.128), (0.0, 2.129)], (LAMP_C[0], 0, LAMP_C[2]), M['chrome'], seg=12, axis='y', name='beacon_base'))
    for a in (0.0, math.pi / 2):
        arc_ = [(LAMP_C[0] + math.cos(a) * 0.068 * math.cos(t), 2.124 + 0.104 * math.sin(t), LAMP_C[2] + math.sin(a) * 0.068 * math.cos(t)) for t in [math.pi * i / 6 for i in range(7)]]
        g = sweep(arc_, 0.0032, M['chrome'], seg=4, name='guard'); uv_box(g, 0.05); A(g)
    dome = lathe([(0.06, 2.127), (0.06, 2.158), (0.055, 2.188), (0.042, 2.208), (0.022, 2.219), (0.0, 2.222)], (LAMP_C[0], 0, LAMP_C[2]), M['lamp'], seg=12, axis='y', name='dome')
    uv_cyl(dome, axis='y', a0=2.127, a1=2.222); unzero(dome)
    # ---------------- right side: the lever's escutcheon + hub (static), LUCK IS A SKILL
    A(lathe([(0.0, XO - 0.001), (0.08, XO - 0.001), (0.08, XO + 0.004), (0.064, XO + 0.01), (0.058, 0.552), (0.048, 0.562), (0.0, 0.5625)], (0, PIVOT[1], PIVOT[2]), M['chrome'], seg=12, axis='x', name='hub'))
    A(sticker_q((XO + 0.0015, 0.74, 0.12), 0.2, 0.034, 'luck', M, axis='x', sx=1, ang=-0.12))
    # the lever: collar on the shaft, the arm raked back a touch, a chrome ferrule, the red ball
    L = [lathe([(0.036, 0.5615), (0.042, 0.566), (0.042, 0.584), (0.034, 0.592)], (0, PIVOT[1], PIVOT[2]), M['chrome'], seg=12, axis='x', name='collar', cap=False)]
    L.append(box((0.032, 0.07, 0.04), (0.6, PIVOT[1] + 0.012, PIVOT[2]), M['chrome'], bev=0.006, seg=1, name='boss'))
    L.append(rod((0.602, PIVOT[1] + 0.02, PIVOT[2]), (0.616, 1.465, PIVOT[2] - 0.03), 0.015, M['chrome'], seg=8, name='arm'))
    L.append(rod((0.615, 1.432, PIVOT[2] - 0.028), (0.617, 1.474, PIVOT[2] - 0.031), 0.021, M['chrome'], seg=8, name='ferrule'))
    kn = ball(0.052, (0.618, 1.52, PIVOT[2] - 0.034), M['button'], seg=12, rings=7, name='knob'); onto(kn, 'red', M); L.append(kn)
    for o in L:
        if not o.data.uv_layers: uv_box(o, 0.05)
    # ---------------- left side: the crooked dented service panel, wires out of it, a loop of meat out of the cabinet
    sp = grid_plate(0.36, 0.44, 0.006, 6, 8, M['steel'], 'service')
    xform([sp], rot=(0, -math.pi / 2, 0))
    xform([sp], rot=(0.1, 0, 0)); xform([sp], rot=(0, 0, -0.06), pivot=(0, 0.2, 0))
    xform([sp], move=(-XO - 0.004, 0.63, -0.06))
    dent(sp, (-XO - 0.02, 0.56, -0.02), 0.14, 0.02, axis=(1, 0, 0)); dent(sp, (-XO - 0.02, 0.49, -0.14), 0.07, 0.008, axis=(1, 0, 0))
    uv_box(sp, 0.4); A(sp)
    for y, z in ((0.82, -0.205), (0.845, 0.085), (0.44, 0.08)):  # three screws (the fourth went missing), sat on the panel
        A(cyl(0.008, 0.005, (hit_x([sp], y, z) - 0.0015, y, z), M['chrome'], axis='x', seg=6, name='screw'))
    A(sticker_q((hit_x([sp], 0.745, -0.06) - 0.0025, 0.745, -0.06), 0.2, 0.034, 'warranty', M, axis='x', sx=-1, ang=0.1))
    for k, (pts, r) in enumerate((
            ([(-0.521, 0.43, -0.16), (-0.545, 0.4, -0.17), (-0.565, 0.33, -0.16), (-0.56, 0.27, -0.12), (-0.54, 0.3, -0.07), (-0.525, 0.4, -0.05)], 0.0055),
            ([(-0.521, 0.43, -0.1), (-0.55, 0.38, -0.1), (-0.572, 0.3, -0.09), (-0.57, 0.22, -0.06), (-0.555, 0.2, -0.02), (-0.535, 0.24, 0.02), (-0.524, 0.4, 0.04)], 0.005),
            ([(-0.521, 0.42, -0.03), (-0.55, 0.36, -0.03), (-0.566, 0.27, -0.02), (-0.562, 0.2, 0.0), (-0.556, 0.17, 0.01)], 0.0045),
            ([(-0.521, 0.42, 0.06), (-0.548, 0.37, 0.07), (-0.56, 0.31, 0.09), (-0.552, 0.26, 0.11)], 0.0045))):
        w = sweep(pts, r, M['wire'], seg=4, name='wire'); onto(w, ('red', 'yellow', 'green', 'blue')[k], M); A(w)
    for p in ((-0.556, 0.17, 0.01), (-0.552, 0.26, 0.11)):  # the cut ends: bare copper
        c_ = ball(0.0045, p, M['wire'], seg=6, rings=4, name='copper'); onto(c_, 'copper', M); A(c_)
    loop = [(-0.512, 1.62, -0.24), (-0.55, 1.61, -0.25), (-0.585, 1.53, -0.27), (-0.598, 1.42, -0.285), (-0.592, 1.3, -0.3), (-0.57, 1.21, -0.305), (-0.54, 1.155, -0.3),
            (-0.512, 1.135, -0.29)]
    mt = sweep(loop, [0.024, 0.031, 0.037, 0.03, 0.039, 0.034, 0.028, 0.023], M['meat'], seg=8, name='meat'); uv_box(mt, 0.06); A(mt)
    for (dx, y, z, r) in ((-0.01, 1.675, -0.2, 0.026), (-0.014, 1.66, -0.17, 0.018), (-0.006, 1.69, -0.175, 0.014)):  # a growth spreading off it
        g_ = ball(r, (-XO + dx, y, z), M['meat'], scale=(0.7, 1, 1), seg=8, rings=5, name='growth'); uv_box(g_, 0.06); A(g_)
    for (y, z) in ((1.62, -0.24), (1.135, -0.29)):  # fleshy lips where it grows out of the panel
        lp = lathe([(0.022, -XO + 0.002), (0.042, -XO - 0.003), (0.04, -XO - 0.012), (0.022, -XO - 0.014)], (0, y, z), M['meat'], seg=8, axis='x', name='lips', cap=False)
        uv_box(lp, 0.06); A(lp)
    # ---------------- every part gets uvs, then the nodes
    for o in P + L + [dome]:
        apply_mods(o)
        if not o.data.uv_layers: uv_box(o, 0.08)
    if '--qa' in ARGV: qa(P + L + [dome], eps=0.0006, tol=0.002)
    bake_normals(P + L + [dome])
    body = part(P, 'zmm_body', pivot=(0, 0, 0))
    lever = part(L, 'lever', pivot=PIVOT)
    lamp = part([dome], 'lamp_wzN', pivot=LAMP_C)
    meta = {'kind': 'prop', 'id': 'zmmachine', 'screen': {'c': [SCR[0], SCR[1], Z_GLASS], 'w': SCR_W, 'h': SCR_H},
            'lever': {'pivot': list(PIVOT), 'axis': [1, 0, 0], 'pull': 1.2}, 'lamp': 'lamp_wzN', 'neon': 'zm_neon', 'lampMat': 'zm_lamp'}
    return finish('x_zmmachine', [body, lever, lamp], meta)


if __name__ == '__main__':
    main(build, 'x_zmmachine', exposure=-0.3)
