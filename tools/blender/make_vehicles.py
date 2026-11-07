# Round 4, the last box-built vehicles: Suburb's walk-in shuttle bus, the parked box truck (Suburb and Suburb S&D),
# the Warehouse semi (trailer + tractor) and the same trailer on its own (Warehouse S&D), as glossy Blender models.
# Every copy of these has the same boxes (shared/map.js busBoxes / truckBoxes / semiBoxes), so each file is drawn as
# built: scale 1, origin = the kit function's anchor, the prop's own frame (three.js axes: the bus and the truck run
# along +x, front at +x; the semi runs along +z, the trailer's back at z 0).
#   p_transitbus   12 m high-floor city bus that has seen things: candy busyellow, black rubber gaskets round seven
#                  open windows a side ("the windows are long gone": a few shards still in the seals), the door gap
#                  with its frame and grab rail (the doors went too), the step, the emergency window out at the back.
#                  Inside: ribbed-rubber floor with the yellow nosing and STAND BEHIND THE LINE, wheel-arch humps,
#                  six moquette double seats on the boxes, grab rails and poles, the dash and a steering wheel (the
#                  driver's seat is gone), engine louvres, a 69 NOWHERE destination sign, rabbit-ear mirrors
#   p_boxtruck     26 ft box truck: red short-nose cab (painted cab glass: seats, dash, wheel), white box with corner
#                  posts and rails, the roller door rolled up on its drum, a varnished plank floor, E-track and scuff
#                  boards inside, tail lights on the posts, three axles of steel disc wheels, mud flaps, a fuel tank
#   p_semi         the trailer below + a red short-nose day-cab tractor: chrome grille and bumper, twin stacks, fuel
#                  tanks, steps, mirrors, fifth wheel under the trailer, air lines, painted cab glass
#   p_semitrailer  12.5 m tandem-axle box trailer on its landing legs (the yard's p_trailer, make_yard.py, with this
#                  layout's axles and the rear light bar): white riveted panels, swing doors, conspicuity tape
# The boxes stay the collision. Walls, floors, roofs, seats and steps sit on their boxes' faces (inside surfaces never
# stand proud of them), door and window gaps stay open where the boxes leave them open, the livery pictures (thin `fit`
# boxes) stay map boxes on flat outer faces. 'light' / 'tail' boxes are `glow` lamps. Built in a "car frame" (front
# +z, left +x, like make_traffic.py's cars, so its trim atlas, wheels and painted cab glass work as they are), then
# turned into the prop frame. Baked AO in the vertex colours, a ~250-triangle `lod1` each.
# run: blender -b --python tools/blender/make_vehicles.py -- [--only=transitbus,boxtruck,semi,semitrailer] [--qa]
#      [--fit] [--no-sheet] [--no-export] [--views=<dir>]   (--fit: the model against its boxes, numbers;
#      --views: close-ups from outside and inside, into <dir>)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link, _image
import lib
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
V3 = Vector
clamp = lambda v, a, b: max(a, min(b, v))
lerp = lambda a, b, t: a + (b - a) * t


def arg(k, d=None):
    for a in ARGV:
        if a.startswith('--' + k + '='): return a.split('=', 1)[1]
        if a == '--' + k: return True
    return d


class _Mod:  # another builder's script as a module (its functions keep looking things up in its own globals)
    def __init__(s, d): object.__setattr__(s, 'd', d)
    def __getattr__(s, k): return s.d[k]
    def __setattr__(s, k, v): s.d[k] = v


def _load(fn, last):
    """make_traffic.py / make_yard.py end by building their own models: load everything but that last call"""
    p = os.path.join(HERE, fn)
    src = open(p).read()
    src = src[:src.rindex('\n' + last)]
    ns = {'__file__': p, '__name__': fn[:-3], '__builtins__': __builtins__}
    exec(compile(src, p, 'exec'), ns)
    return _Mod(ns)


T = _load('make_traffic.py', 'main()')    # the traffic cars: trim atlas, wheels, painted cab glass, lofts
Y = _load('make_yard.py', 'main_yard()')  # the yard: the trailer's look, prisms, the review sheet with its lod1 tile
g2b, b2g = T.g2b, T.b2g


# ------------------------------------------------------------ the trim atlas: the traffic one + this batch's cells
T.TEX_TRIM = (256, 192)
EXTRA = {  # name: (x, y, w, h, colour, roughness, metallic) in the right half
    'glassw': (128, 0, 32, 32, 0x1c2c44, 0.06, 0.6),   # windscreens: dark glass with streaks
    'diamond': (160, 0, 32, 32, 0x8a9098, 0.32, 0.85),  # diamond plate (steps, humps, sills)
    'moq': (192, 0, 32, 32, 0x168c84, 0.9, 0.0),        # bus moquette (the 'seat' teal), confetti squiggles
    'moq2': (224, 0, 32, 32, 0x0f5f5a, 0.9, 0.0),       # the backs of the seats
    'shell': (128, 32, 16, 16, 0x34363e, 0.45, 0.0),    # seat shells, dash plastic
    'cream': (144, 32, 16, 16, 0xe6dcc4, 0.5, 0.0),     # interior panels
    'lens': (160, 32, 16, 16, 0xf2f4f6, 0.18, 0.0),     # light diffusers
    'redl': (176, 32, 16, 16, 0xb01018, 0.15, 0.0),     # lamp lenses that aren't lit
    'ambl': (192, 32, 16, 16, 0xe8820e, 0.15, 0.0),
    'paintr': (208, 32, 16, 16, 0xd81e30, 0.25, 0.1),   # cab red for small parts
    'paintw': (224, 32, 16, 16, 0xf0f0f2, 0.3, 0.05),   # box white for small parts
    'paintb': (240, 32, 16, 16, 0xffc418, 0.25, 0.1),   # busyellow for small parts
    'dest': (128, 48, 64, 16, 0x0c0c0e, 0.3, 0.0),      # the destination sign
    'gauge': (192, 48, 64, 16, 0x101014, 0.35, 0.0),    # a dash: dials, warning lights
    'louvre': (128, 64, 32, 16, 0x18181c, 0.55, 0.2),   # engine louvres
    'slats': (160, 64, 32, 16, 0xc8ccd2, 0.4, 0.5),     # roller door slats
    'etrack': (192, 64, 64, 8, 0x9ca2aa, 0.35, 0.8),    # E-track logistic rail
    'nosing': (192, 72, 32, 8, 0xffd21a, 0.5, 0.0),     # step nosing
    'scuff': (224, 72, 32, 8, 0x8a6a42, 0.6, 0.0),      # scuff boards
    'sgn_exit': (192, 80, 32, 16, 0x1aa04a, 0.3, 0.0),
    'sgn_smoke': (224, 80, 32, 16, 0xffffff, 0.3, 0.0),
    'sgn_bell': (128, 96, 32, 16, 0xffe14d, 0.3, 0.0),
    'sgn_line': (160, 96, 32, 16, 0xffffff, 0.3, 0.0),
    'badge': (192, 96, 64, 16, 0x18181c, 0.2, 0.6),     # a grille badge
    'sticker3': (128, 112, 64, 16, 0xff4fd8, 0.4, 0.0),
    'plate2': (192, 112, 48, 16, 0xf4f1e4, 0.35, 0.0),
    'stop': (240, 112, 16, 16, 0xe02020, 0.25, 0.0),    # stop buttons
    'grille2': (128, 80, 32, 16, 0x101012, 0.4, 0.6),   # chrome bar grille
    'tread2': (160, 80, 32, 16, 0x141416, 0.85, 0.0),   # rubber floor ribs (bus steps)
    # the bottom band (y 128..192): the trucks'
    'dottape': (0, 128, 64, 8, 0xd8202a, 0.35, 0.0),     # red / white conspicuity tape
    'alum': (64, 128, 16, 16, 0xc2c6cc, 0.3, 0.85),     # brushed aluminium (posts, rails, tanks)
    'chromeb': (80, 128, 16, 16, 0xe8ecf2, 0.08, 1.0),   # bumper chrome
    'grille3': (96, 128, 32, 32, 0x0c0c0e, 0.2, 0.9),   # a truck's chrome bar grille
    'tank': (128, 128, 32, 16, 0xc8ccd2, 0.22, 0.9),    # a fuel tank's polished skin
    'mudflap': (160, 128, 32, 32, 0x121214, 0.85, 0.0), # mud flaps (a pink JANK on them)
    'tapew': (192, 128, 32, 8, 0xf2f2f2, 0.3, 0.0),     # white reflective tape
    'cabtrim': (224, 128, 16, 16, 0x141418, 0.35, 0.0), # cab rubber + black trim
    'stencil': (0, 136, 64, 16, 0xf0f0f2, 0.35, 0.05),  # NO RIDERS
    'boxlogo': (0, 152, 96, 16, 0xf0f0f2, 0.3, 0.05),   # the box's front: CB&C LOGISTICS
    'sticker4': (96, 160, 64, 16, 0xffe14d, 0.4, 0.0),  # back of the truck
    'reflect': (160, 160, 16, 16, 0xff2a1a, 0.15, 0.0), # red reflectors
    'reflecta': (176, 160, 16, 16, 0xff9a1a, 0.15, 0.0),
}
for k, v in EXTRA.items(): T.TRIM.setdefault(k, v)


def paint_extra(px, cell, plate='JNK 69', sticker=('HOW IS MY', 'DRIVING? NO')):
    """the cells' pictures (the traffic atlas painter first: plates, stickers)"""
    T.atlas(plate, sticker, 0xffe14d, (0x101010, 0xe8323c))(px, cell)
    r = np.random.default_rng(17)
    g = cell('glassw'); h, w = g.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    g[:] = hexrgb(0x16243a) * (0.9 + 0.2 * (yy / h))[:, :, None]
    band = (xx + yy * 0.9) % 22
    g[(band > 2) & (band < 6)] = g[(band > 2) & (band < 6)] * 0.35 + hexrgb(0x7aa0c8) * 0.65
    g[(band >= 6) & (band < 7)] = g[(band >= 6) & (band < 7)] * 0.5 + hexrgb(0x5b7da6) * 0.5
    d = cell('diamond'); d[:] = hexrgb(0x7c828a) * (0.92 + 0.1 * r.random((32, 32, 1)))
    for y in range(0, 32, 4):
        for x in range(0, 32, 4):
            o = 2 if (y // 4) % 2 else 0
            xx_ = (x + o) % 32
            d[y, xx_] = hexrgb(0xc8ccd2); d[(y + 1) % 32, (xx_ + 1) % 32] = hexrgb(0x4a4e56)
    for key, base in (('moq', 0x168c84), ('moq2', 0x0f5f5a)):
        m = cell(key); m[:] = hexrgb(base) * (0.9 + 0.12 * r.random((32, 32, 1)))
        for _ in range(26 if key == 'moq' else 12):  # transit moquette: confetti squiggles (hides everything)
            y, x = r.integers(0, 31, 2); c = hexrgb(int(r.choice([0xff4fd8, 0xffe14d, 0xf4f4f0, 0x2a2a6a])))
            m[y, x] = c; m[y, (x + 1) % 32] = c; m[(y + 1) % 32, (x + 1) % 32] = c
    s = cell('dest'); s[:] = hexrgb(0x0a0a0c)
    text_px(s, '69 NOWHERE', 3, 4, 1, 0xffae1a)
    gg = cell('gauge'); gg[:] = hexrgb(0x121216)
    for cx_, col in ((8, 0xe8e8e8), (22, 0xe8e8e8), (36, 0x4fd8ff)):
        px_disc(gg, cx_, 8, 6, 0x2a2a30); px_disc(gg, cx_, 8, 5, 0x0a0a0c); px_line(gg, cx_, 8, cx_ + 3, 4, col, 1.0)
    for i, col in enumerate((0xe02020, 0xffae1a, 0x39ff14, 0x2a6cff)): gg[11:13, 46 + i * 4:48 + i * 4] = hexrgb(col)
    gg[4:6, 46:62] = hexrgb(0x3a3a44)
    lv = cell('louvre')
    for y in range(lv.shape[0]): lv[y, :] = hexrgb(0x2c2c32) if y % 4 == 0 else (hexrgb(0x08080a) if y % 4 == 3 else hexrgb(0x18181c))
    sl = cell('slats')
    for y in range(sl.shape[0]): sl[y, :] = hexrgb(0xd4d8de) * (0.96 + 0.05 * r.random()) if y % 4 else hexrgb(0x8c9098)
    et = cell('etrack'); et[:] = hexrgb(0x9ca2aa); et[2:6, 1::4] = hexrgb(0x2a2c30); et[2:6, 2::4] = hexrgb(0x2a2c30)
    no = cell('nosing'); no[:] = hexrgb(0xffd21a); no[2:6, ::3] = hexrgb(0x1a1a1a)
    sc = cell('scuff'); sc[:] = hexrgb(0x8a6a42) * (0.9 + 0.15 * r.random((8, 32, 1))); sc[0, :] = sc[-1, :] = hexrgb(0x5a4026)
    e = cell('sgn_exit'); e[:] = hexrgb(0x1aa04a); text_px(e, 'EXIT', 4, 4, 1, 0xffffff)
    sm = cell('sgn_smoke'); sm[:] = hexrgb(0xffffff); px_disc(sm, 8, 8, 6.5, 0xe02020); px_disc(sm, 8, 8, 4.5, 0xffffff)
    px_line(sm, 4.5, 11.5, 11.5, 4.5, 0xe02020, 1.5); text_px(sm, 'NO', 17, 1, 1, 0x101010); text_px(sm, 'U', 19, 9, 1, 0x101010)
    b = cell('sgn_bell'); b[:] = hexrgb(0xffe14d); text_px(b, 'DING', 4, 1, 1, 0x101010); text_px(b, 'BUS', 7, 9, 1, 0xe02020)
    ln = cell('sgn_line'); ln[:] = hexrgb(0xffffff); ln[0:2, :] = ln[-2:, :] = hexrgb(0xffd21a); text_px(ln, 'STAND', 1, 4, 1, 0x101010)
    bd = cell('badge'); bd[:] = hexrgb(0x18181c); bd[0, :] = bd[-1, :] = hexrgb(0xc8ccd2); text_px(bd, 'JANK', 21, 5, 1, 0xdde2ea)
    st = cell('sticker3'); st[:] = hexrgb(0xff4fd8); text_px(st, 'THIS BUS', 8, 1, 1, 0xffffff); text_px(st, 'STOPS 4 NOBODY', 3 - 1, 9, 1, 0x2a0a26)
    pl = cell('plate2'); pl[:] = hexrgb(0xf4f1e4); pl[0, :] = pl[-1, :] = hexrgb(0x2a2a40); pl[:, 0] = pl[:, -1] = hexrgb(0x2a2a40)
    text_px(pl, plate, (48 - (len(plate) * 6 - 1)) // 2, 5, 1, 0x1a1a3a)
    sp = cell('stop'); sp[:] = hexrgb(0xd01818); px_disc(sp, 8, 8, 5, 0xff4a4a); px_disc(sp, 7, 7, 2, 0xffb0b0)
    gr = cell('grille2'); gr[:] = hexrgb(0x0c0c0e)
    for y in range(1, 16, 3): gr[y, :] = hexrgb(0xdde2ea); gr[y + 1 if y + 1 < 16 else y, :] = hexrgb(0x7a808a)
    tr = cell('tread2')
    for x in range(32): tr[:, x] = hexrgb(0x2a2a2e) if x % 3 == 0 else hexrgb(0x141416)
    dt = cell('dottape')
    for x in range(0, 64, 8): dt[:, x:x + 4] = hexrgb(0xd8202a); dt[:, x + 4:x + 8] = hexrgb(0xf4f4f4)
    al = cell('alum'); al[:] = hexrgb(0xc2c6cc) * (0.95 + 0.08 * r.random((16, 16, 1)))
    for y in range(0, 16, 2): al[y, :] *= 0.97
    g3 = cell('grille3'); g3[:] = hexrgb(0x0a0a0c)
    for x in range(1, 32, 4): g3[2:30, x:x + 2] = hexrgb(0xdde2ea); g3[2:30, x + 2:x + 3] = hexrgb(0x8a909a)
    g3[0:2, :] = g3[30:32, :] = hexrgb(0xe8ecf2); g3[:, 0] = g3[:, 31] = hexrgb(0xe8ecf2)
    tk = cell('tank'); tk[:] = hexrgb(0xd0d4da) * (0.92 + 0.1 * r.random((16, 32, 1))); tk[:, 7:9] = hexrgb(0x2a2c30); tk[:, 23:25] = hexrgb(0x2a2c30)
    mf = cell('mudflap'); mf[:] = hexrgb(0x121214); text_px(mf, 'JANK', 4, 12, 1, 0xff4fd8); mf[26:28, 2:30] = hexrgb(0xd8d8dc)
    tw = cell('tapew'); tw[:] = hexrgb(0xf2f2f2); tw[:, ::6] = hexrgb(0xc8c8cc)
    st = cell('stencil'); st[:] = hexrgb(0xf0f0f2); text_px(st, 'NO RIDERS', 5, 5, 1, 0x2a2a30)
    bl = cell('boxlogo'); bl[:] = hexrgb(0xf0f0f2); text_px(bl, 'CB&C', 3, 4, 1, 0x19a04a); text_px(bl, 'LOGISTICS', 34, 4, 1, 0x2a2a30)
    s4 = cell('sticker4'); s4[:] = hexrgb(0xffe14d); s4[0, :] = s4[-1, :] = hexrgb(0x101010)
    text_px(s4, 'IF U CAN', 8, 1, 1, 0x101010); text_px(s4, 'READ THIS', 5, 8, 1, 0xd8202a)
    rf = cell('reflect'); rf[:] = hexrgb(0xc81810); px_disc(rf, 8, 8, 6, 0xff3a2a); px_disc(rf, 6, 6, 2, 0xffb0a0)
    ra = cell('reflecta'); ra[:] = hexrgb(0xd87a10); px_disc(ra, 8, 8, 6, 0xffa22a); px_disc(ra, 6, 6, 2, 0xffe0a0)


# ------------------------------------------------------------ painted atlases with world-space views
KINDS = {  # a face seen from outside along its normal: (across = the viewer's right, up)
    'L': (lambda p: -p[2], lambda p: p[1]), 'R': (lambda p: p[2], lambda p: p[1]),
    'F': (lambda p: p[0], lambda p: p[1]), 'B': (lambda p: -p[0], lambda p: p[1]),
    'T': (lambda p: p[2], lambda p: p[0]), 'U': (lambda p: p[2], lambda p: -p[0])}


def kind_of(n):
    ax = max(range(3), key=lambda i: abs(n[i]))
    return [('L', 'R'), ('T', 'U'), ('F', 'B')][ax][0 if n[ax] > 0 else 1]


class Atlas:
    """one painted texture: named regions, each a pixel rect showing a view of the vehicle (a world box seen from
    one side) or a plain cell, so the painting and the UVs both work in world (game, car-frame) coordinates"""
    def __init__(s, name, W, H, base=0xffffff):
        s.name, s.W, s.H = name, W, H
        s.px = np.zeros((H, W, 3), np.float32); s.px[:] = hexrgb(base)
        s.R = {}
        s.img = bpy.data.images.new(name, W, H, alpha=False)

    def view(s, key, rect, kind, lo, hi):
        a, b = KINDS[kind]
        cs = [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
        A_ = [a(c) for c in cs]; B_ = [b(c) for c in cs]
        s.R[key] = (rect, kind, (min(A_), max(A_), min(B_), max(B_)))

    def cell(s, key, rect): s.R[key] = (rect, None, None)

    def st(s, key, p):
        rect, kind, (a0, a1, b0, b1) = s.R[key]
        a, b = KINDS[kind]
        return (a(p) - a0) / (a1 - a0), (b(p) - b0) / (b1 - b0)

    def uv(s, key, p, m=0.6):
        rect = s.R[key][0]
        u, v = s.st(key, p)
        return T.uv_px(rect, (s.W, s.H), clamp(u, 0, 1), clamp(v, 0, 1), m)

    def pix(s, key, p):
        rect = s.R[key][0]; u, v = s.st(key, p)
        return rect[0] + u * rect[2], rect[1] + (1 - v) * rect[3]

    def sub(s, key):
        x, y, w, h = s.R[key][0]
        return s.px[y:y + h, x:x + w]

    def world(s, key):
        """per pixel of a view region: the world coordinates its centre stands for -> dict of 2D arrays (x, y, z; the
        one the view looks along is missing)"""
        (x, y, w, h), kind, (a0, a1, b0, b1) = s.R[key]
        yy, xx = np.mgrid[0:h, 0:w] + 0.5
        A_ = a0 + xx / w * (a1 - a0); B_ = b0 + (1 - yy / h) * (b1 - b0)
        return {'L': {'z': -A_, 'y': B_}, 'R': {'z': A_, 'y': B_}, 'F': {'x': A_, 'y': B_}, 'B': {'x': -A_, 'y': B_},
                'T': {'z': A_, 'x': B_}, 'U': {'z': A_, 'x': -B_}}[kind]

    # painting, in world coordinates of a region
    def fill(s, key, col, var=0.03, seed=1):
        sb = s.sub(key); h, w = sb.shape[:2]
        n = Y.vnoise(h, w, seed)
        sb[:] = hexrgb(col)[None, None] * (1 - var + 2 * var * n[:, :, None])

    def mask(s, key, fn):
        """pixels whose world point passes fn(dict of arrays) -> bool array"""
        return fn(s.world(key))

    def put(s, key, m, col, k=1.0):
        sb = s.sub(key)
        sb[m] = sb[m] * (1 - k) + hexrgb(col) * k

    def mul(s, key, fn):
        """multiply each pixel by fn(world dict) (an array of factors: painted AO, grime)"""
        sb = s.sub(key); f = fn(s.world(key))
        sb *= np.clip(f, 0, 2)[:, :, None]

    def rect(s, key, p0, p1, col):
        (x0, y0), (x1, y1) = s.pix(key, p0), s.pix(key, p1)
        xa, xb = sorted((int(round(x0)), int(round(x1)))); ya, yb = sorted((int(round(y0)), int(round(y1))))
        X, Y_, W_, H_ = s.R[key][0]
        xa, xb = max(xa, X), min(xb, X + W_); ya, yb = max(ya, Y_), min(yb, Y_ + H_)
        if xb > xa and yb > ya: s.px[ya:yb, xa:xb] = hexrgb(col)

    def poly(s, key, pts, col):
        q = [s.pix(key, p) for p in pts]
        X, Y_, W_, H_ = s.R[key][0]
        yy, xx = np.mgrid[Y_:Y_ + H_, X:X + W_] + 0.5
        inside = np.zeros(yy.shape, bool)
        for i in range(len(q)):
            (x0, y0), (x1, y1) = q[i], q[(i + 1) % len(q)]
            inside ^= ((y0 > yy) != (y1 > yy)) & (xx < (x1 - x0) * (yy - y0) / ((y1 - y0) or 1e-9) + x0)
        s.px[Y_:Y_ + H_, X:X + W_][inside] = hexrgb(col)

    def text(s, key, p, txt, scale, col, shadow=None, anchor='c'):
        x, y = s.pix(key, p)
        w = len(txt) * 6 * scale - scale; h = 7 * scale
        x0 = int(round(x - (w / 2 if anchor == 'c' else 0))); y0 = int(round(y - h / 2))
        if shadow is not None: text_px(s.px, txt, x0 + max(1, scale // 2), y0 + max(1, scale // 2), scale, shadow)
        text_px(s.px, txt, x0, y0, scale, col)

    def line(s, key, pts, col, w=1.0):
        q = [s.pix(key, p) for p in pts]
        for (x0, y0), (x1, y1) in zip(q, q[1:]): px_line(s.px, x0, y0, x1, y1, col, w)

    def write(s):
        a = np.ones((s.H, s.W, 4), np.float32); a[:, :, :3] = np.clip(s.px, 0, 1)[::-1]
        s.img.pixels.foreach_set(a.ravel()); s.img.file_format = 'PNG'; s.img.pack()
        if isinstance(arg('dump'), str):
            os.makedirs(arg('dump'), exist_ok=True)
            im = bpy.data.images.new('dump_' + s.name, s.W, s.H, alpha=False); im.pixels.foreach_set(a.ravel())
            im.filepath_raw = os.path.join(arg('dump'), s.name + '.png'); im.file_format = 'PNG'; im.save()


class Cells:
    """the trim atlas as an Atlas-like thing (its cells only)"""
    def __init__(s): s.W, s.H = T.TEX_TRIM; s.R = {k: (v[:4], None, None) for k, v in T.TRIM.items()}


def uvmap(o, mats, atl, rule):
    """materials + UVs face by face: rule(game normal, game centre) -> (material index, region key). View regions
    project the face in world space; cells take a box projection of the face over the object's size"""
    bpy.context.view_layer.update(); apply_mods(o)
    me = o.data
    me.materials.clear()
    for m in mats: me.materials.append(m)
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    pts = [b2g(mw @ v.co) for v in me.vertices]
    lo = V3([min(p[i] for p in pts) for i in range(3)]); ext = V3([max(p[i] for p in pts) for i in range(3)]) - lo
    for p in me.polygons:
        n = b2g(mw.to_3x3() @ p.normal).normalized(); c = b2g(mw @ p.center)
        mi, key = rule(n, c)
        p.material_index = mi
        A = atl[mi]
        rect, kind, _ = A.R[key]
        qs = [pts[me.loops[li].vertex_index] for li in p.loop_indices]
        if kind is not None:
            out = [A.uv(key, q) for q in qs]
            if T._area2(out) < 1e-8:  # (edge-on to its view, or off its edge: a sliver of the region at its middle; UVs are float32)
                cu = sum(u for u, v in out) / len(out); cv = sum(v for u, v in out) / len(out)
                out = [(cu + 0.002 * math.cos(2 * math.pi * k / len(out)), cv + 0.002 * math.sin(2 * math.pi * k / len(out))) for k in range(len(out))]
        else:
            out = None
            for ax in sorted(range(3), key=lambda i: -abs(n[i])):
                a_, b_ = [(2, 1), (0, 2), (0, 1)][ax]
                fl = (ax == 0 and n.x > 0) or (ax == 2 and n.z < 0) or (ax == 1 and n.y > 0)  # (so a cell's writing reads right from in front)
                su = lambda q: (q[a_] - lo[a_]) / (ext[a_] or 1)
                out = [T.uv_px(rect, (A.W, A.H), 1 - su(q) if fl else su(q), (q[b_] - lo[b_]) / (ext[b_] or 1), 1.0) for q in qs]
                if T._area2(out) > 1e-8: break
        if abs(T._area2(out)) < 1e-8:  # (still nothing: a sliver round its middle, real area for QA and bakes)
            cu = sum(u for u, v in out) / len(out); cv = sum(v for u, v in out) / len(out)
            out = [(cu + 0.003 * math.cos(2 * math.pi * k / len(out)), cv + 0.003 * math.sin(2 * math.pi * k / len(out))) for k in range(len(out))]
        for li, u in zip(p.loop_indices, out): uv[li].uv = u
        if arg('uvdebug') and abs(T._area2(out)) < 1e-11: print('JF_UV0', o.name, tuple(round(v, 3) for v in c), tuple(round(v, 2) for v in n), key, len(out), p.area)
    if arg('uvdebug'):
        for p in me.polygons:
            q = [uv[li].uv for li in p.loop_indices]
            a2 = sum(q[i].x * q[(i + 1) % len(q)].y - q[(i + 1) % len(q)].x * q[i].y for i in range(len(q)))
            if abs(a2) < 1e-12: print('JF_UVA', o.name, p.index, len(q), [tuple(round(c, 4) for c in v) for v in q][:6], tuple(round(v, 3) for v in b2g(mw @ p.center)))
    return o


def one(o, mi, key, mats, atl):
    """a part all in one region"""
    return uvmap(o, mats, atl, lambda n, c: (mi, key))


# ------------------------------------------------------------ parts
def cb(lo, hi, name='b', bev=0.0, seg=1):
    """a box between two game corners (the boxes' numbers straight in, either way round)"""
    lo, hi = [min(a, b) for a, b in zip(lo, hi)], [max(a, b) for a, b in zip(lo, hi)]
    return box(tuple(h - l for l, h in zip(lo, hi)), tuple((l + h) / 2 for l, h in zip(lo, hi)), None, bev=bev, seg=seg, name=name)


def xprism(name, zy, x0, x1, bev=0.0, seg=1, angle=40):
    """an outline in the (z, y) plane (a side view) extruded across x from x0 to x1"""
    return side([(z, y) for z, y in zy], x1 - x0, ((x0 + x1) / 2, 0, 0), None, bev=bev, seg=seg, name=name, angle=angle)


def yprism(name, xz, y0, y1, bev=0.0, seg=1, angle=40):
    """a plan outline [(x, z)] extruded up from y0 to y1"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(x, y0, z)) for x, z in xz]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=gv(0, y1 - y0, 0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, None)
    smooth(o, angle); bevel(o, bev, seg, angle)
    return o


def zprism(name, xy, z0, z1, bev=0.0, seg=1, angle=40):
    """an outline in the (x, y) plane (a front view) extruded along z"""
    bm = bmesh.new()
    vs = [bm.verts.new(gv(x, y, z0)) for x, y in xy]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=gv(0, 0, z1 - z0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, None)
    smooth(o, angle); bevel(o, bev, seg, angle)
    return o


def rrect(x0, x1, z0, z1, r, n=4, corners=(1, 1, 1, 1)):
    """a rounded rectangle in plan [(x, z)], counter-clockwise from the +x/+z corner; corners = which are round
    (+x+z, -x+z, -x-z, +x-z)"""
    out = []
    for k, (cx, cz, a0) in enumerate(((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270))):
        if not corners[k]:
            out.append(((x1, x0, x0, x1)[k], (z1, z1, z0, z0)[k])); continue
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n); out.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return out


def rounded_zy(z0, z1, y0, y1, r, n=4):
    """a (z, y) rectangle with its two top corners rounded (radius r): arch cutters, door shapes"""
    pts = [(z0, y0), (z1, y0)]
    for i in range(n + 1):
        a = math.radians(90 * i / n); pts.append((z1 - r + r * math.cos(a), y1 - r + r * math.sin(a)))
    for i in range(n + 1):
        a = math.radians(90 + 90 * i / n); pts.append((z0 + r + r * math.cos(a), y1 - r + r * math.sin(a)))
    return pts


def rslab(name, x0, x1, z0, z1, y0, y1, rp, rt, n=4, nt=3):
    """a slab with a rounded plan (corner radius rp) and its top edge rolled over (radius rt): roofs"""
    bm = bmesh.new()
    hs = [(0.0, y0)] + [((1 - math.cos(math.radians(90 * k / nt))) * rt, y1 - rt + math.sin(math.radians(90 * k / nt)) * rt) for k in range(nt + 1)]
    rings = []
    for inset, y in hs:
        pts = rrect(x0 + inset, x1 - inset, z0 + inset, z1 - inset, max(rp - inset, 0.012), n)
        rings.append([bm.verts.new(gv(x, y, z)) for x, z in pts])
    for a, b in zip(rings, rings[1:]):
        for j in range(len(a)):
            jj = (j + 1) % len(a); bm.faces.new((a[j], a[jj], b[jj], b[j]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, None); smooth(o, 35)
    return o


def ring_frame(name, u0, u1, v0, v1, w, d0, d1, plane):
    """a gasket round an opening u0..u1 x v0..v1: one closed rectangular ring (its inner faces on the opening's
    edges), w wide, d0..d1 deep. plane 'x': in a wall across x (u = z, v = y); 'z': in a wall across z (u = x, v = y)"""
    P = (lambda u, v, d: (d, v, u)) if plane == 'x' else (lambda u, v, d: (u, v, d))
    rings = []
    for d in (d0, d1):
        rings.append([P(u, v, d) for u, v in ((u0 - w, v0 - w), (u1 + w, v0 - w), (u1 + w, v1 + w), (u0 - w, v1 + w))] +
                     [P(u, v, d) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))])
    verts = rings[0] + rings[1]
    faces = []
    for k in range(4):
        kk = (k + 1) % 4
        faces.append((k, kk, 4 + kk, 4 + k))                    # the d0 face
        faces.append((8 + k, 12 + k, 12 + kk, 8 + kk))          # the d1 face
        faces.append((k, 8 + k, 8 + kk, kk))                    # outside
        faces.append((4 + k, 4 + kk, 12 + kk, 12 + k))          # inside (the opening's edge)
    bm = bmesh.new()
    vs = [bm.verts.new(gv(*p)) for p in verts]
    for f in faces: bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, None); smooth(o, 30)
    return [o]


def tube_rod(p0, p1, r, name='rod', seg=8):
    return rod(p0, p1, r, None, seg=seg, name=name)


def glow_mat(col, name='glow'):
    """an unlit lamp: the game draws `glow` materials with their emission colour (always bright)"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb(col)
    b.inputs['Emission Color'].default_value = srgb(col); b.inputs['Emission Strength'].default_value = 1.0
    b.inputs['Roughness'].default_value = 0.2
    m['jf_color'] = col
    return m


# ------------------------------------------------------------ AO, frames, checks
def bake(targets, see, dist=0.6, lo=0.45, samples=24, floor=True):
    """lib.bake_ao, but only targets are baked; see = everything else the rays may hit (the bus's walls when its
    insides are baked with a longer reach)"""
    sc = bpy.context.scene
    prev, prev_t = sc.render.engine, sc.render.bake.target
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples
    sc.world = sc.world or bpy.data.worlds.new('jf_world')
    sc.world.light_settings.distance = dist
    sc.render.bake.target = 'VERTEX_COLORS'
    vis = set(targets) | set(see)
    hidden = [o for o in sc.objects if o.type == 'MESH' and o not in vis and not o.hide_render]
    for o in hidden: o.hide_render = True
    ground = box((400, 0.02, 400), pos=(0, -0.0105, 0), m=mat('jf_ao_floor', 0x808080), name='jf_ao_floor') if floor else None
    for o in targets:
        apply_mods(o)
        me = o.data
        for c in list(me.color_attributes): me.color_attributes.remove(c)
        ca = me.color_attributes.new('AO', 'BYTE_COLOR', 'CORNER'); me.color_attributes.active_color = ca
        for s in bpy.context.view_layer.objects.selected: s.select_set(False)
        o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.object.bake(type='AO', target='VERTEX_COLORS')
        for d in ca.data:
            v = lo + (1 - lo) * d.color[0]; d.color = (v, v, v, 1.0)
    if ground: bpy.data.objects.remove(ground, do_unlink=True)
    for o in hidden: o.hide_render = False
    sc.render.engine, sc.render.bake.target = prev, prev_t


def zf_where(o, eps=0.0008):
    """where a mesh's z-fighting triangle pairs are (the QA's own test; it only counts them): game coords"""
    sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    me = o.data; me.calc_loop_triangles()
    vs = [o.matrix_world @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    nrm = [((vs[t[1]] - vs[t[0]]).cross(vs[t[2]] - vs[t[0]])).normalized() for t in tris]
    bvh = BVHTree.FromPolygons(vs, tris, epsilon=0.0)
    out = set()
    for ti, t in enumerate(tris):
        a, b, c = (vs[i] for i in t); n = nrm[ti]
        if n.length < 0.5: continue
        cen = (a + b + c) / 3
        for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
            for _, _, tj, _ in bvh.find_nearest_range(p, eps):
                if tj is None or tj == ti or set(t) & set(tris[tj]): continue
                n2 = nrm[tj]
                if n.dot(n2) < 0.999: continue
                a2, b2, c2 = (vs[i] for i in tris[tj])
                q = p - n2 * n2.dot(p - a2)
                if qa_check._point_in_tri(q, a2, b2, c2, n2): out.add(tuple(round(v, 3) for v in b2g(cen)))
    print('JF_ZF', o.name, len(out), sorted(out)[:16])
    import bmesh as _bm
    bm = _bm.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    from collections import Counter as _C
    d = _C((l.vert.index, l.link_loop_next.vert.index) for f in bm.faces for l in f.loops)
    bad = [k for k, c in d.items() if c > 1]
    print('JF_WIND', o.name, len(bad), [tuple(round(v, 3) for v in b2g(o.matrix_world @ bm.verts[k[0]].co)) for k in bad[:8]] if bad else '')
    bm.free()


def to_frame(objs, yaw, shift):
    """car frame -> the prop's frame: a turn about y (three's rotation.y) then a shift (game coords)"""
    M = Matrix.Translation(gv(*shift)) @ Matrix.Rotation(yaw, 4, 'Z')
    for o in objs:
        apply_mods(o)
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        o.data.transform(M)
        o.data.update()


def faces_tagged(o, mats_names):
    return [p for p in o.data.polygons if o.data.materials[p.material_index].name in mats_names]


def fit_check(fid, objs, boxes, air, ok_names=(), tol=0.02):
    """the model against its boxes (prop frame): (1) model points standing in the open air the players walk in (the
    insides: air = AABBs, minus every box grown by tol); (2) box faces players can see that the model leaves open
    (rays from just outside each exposed face: the model must be hit within 6 cm of it)"""
    solid = [(V3(lo), V3(hi), m, st) for lo, hi, m, st in boxes]
    inbox = lambda p, g=tol: any(all(lo[i] - g <= p[i] <= hi[i] + g for i in range(3)) for lo, hi, m, st in solid if not st)
    inair = lambda p: any(all(a[0][i] < p[i] < a[1][i] for i in range(3)) for a in air)
    dg = bpy.context.evaluated_depsgraph_get()
    verts, tris, owner = [], [], []
    report = {}
    for o in objs:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles()
        base = len(verts)
        for v in me.vertices: verts.append(b2g(o.matrix_world @ v.co))
        for t in me.loop_triangles: tris.append(tuple(base + i for i in t.vertices)); owner.append(o.name)
        o.evaluated_get(dg).to_mesh_clear()
    # (1) proud: triangle centres and corners in the air
    proud = {}
    for t, nm in zip(tris, owner):
        for p in [verts[t[0]], verts[t[1]], verts[t[2]], (verts[t[0]] + verts[t[1]] + verts[t[2]]) / 3]:
            if inair(p) and not inbox(p):
                proud.setdefault(nm, []).append(p)
    bvh = BVHTree.FromPolygons([g2b(v) for v in verts], tris, epsilon=0.0)
    # (2) open: every face of every solid box, sampled on a grid where no other box covers it
    gaps = []
    for bi, (lo, hi, m, st) in enumerate(solid):
        if st: continue
        for ax in range(3):
            for sg in (-1, 1):
                a_, b_ = [i for i in range(3) if i != ax]
                fpos = hi[ax] if sg > 0 else lo[ax]
                n_a = max(2, int((hi[a_] - lo[a_]) / 0.12)); n_b = max(2, int((hi[b_] - lo[b_]) / 0.12))
                bad = tot = 0
                for i in range(n_a):
                    for j in range(n_b):
                        p = V3((0, 0, 0)); p[ax] = fpos
                        p[a_] = lo[a_] + (i + 0.5) / n_a * (hi[a_] - lo[a_]); p[b_] = lo[b_] + (j + 0.5) / n_b * (hi[b_] - lo[b_])
                        out = p.copy(); out[ax] += sg * 0.012
                        if inbox(out, 0.0) or out[1] < 0.01: continue  # (covered by a neighbour, or the ground)
                        tot += 1
                        d = V3((0, 0, 0)); d[ax] = -sg
                        org = p.copy(); org[ax] += sg * 0.3
                        if inbox(org, 0.0):  # (something solid in front: start just outside the face)
                            org = p.copy(); org[ax] += sg * 0.02
                        hit = bvh.ray_cast(g2b(org), g2b(d).normalized(), 2.0)
                        depth = (org - b2g(hit[0])).length - (org - p).length if hit[0] is not None else 9
                        if depth > 0.06: bad += 1
                if tot and bad:
                    gaps.append((bi, m, 'xyz'[ax] + ('+' if sg > 0 else '-'), bad, tot, tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi)))
    print(f'JF_FIT {fid}: {len(tris)} tris checked')
    for nm, ps in sorted(proud.items(), key=lambda kv: -len(kv[1])):
        lo_ = V3([min(p[i] for p in ps) for i in range(3)]); hi_ = V3([max(p[i] for p in ps) for i in range(3)])
        flag = 'ok (meant)' if any(nm.startswith(k) for k in ok_names) else 'PROUD'
        print(f'JF_FIT {fid} {flag}: {nm} {len(ps)} pts in the air, {tuple(round(v, 2) for v in lo_)}..{tuple(round(v, 2) for v in hi_)}')
    for g in gaps:
        print(f'JF_FIT {fid} OPEN: box {g[0]} {g[1]} face {g[2]}: {g[3]}/{g[4]} samples see through, box {g[5]}..{g[6]}')
    return proud, gaps




class Build:
    """one vehicle's parts: each gets its materials and UVs as it's added (rule(n, c) -> (material, region))"""
    def __init__(s, fid, mats, atl):
        s.fid, s.mats, s.atl = fid, mats, atl
        s.l0, s.l1 = [], []
        s.n = 0

    def nm(s, k):
        s.n += 1
        return f'{s.fid}_{k}_{s.n}'

    def add(s, o, rule, far=False):
        r = rule if callable(rule) else (lambda n, c, rr=rule: rr)
        uvmap(o, s.mats, s.atl, r)
        (s.l1 if far else s.l0).append(o)
        return o

    def box(s, lo, hi, rule, bev=0.0, seg=1, far=False, k='b'):
        return s.add(cb(lo, hi, s.nm(k), bev, seg), rule, far)

    def rod(s, p0, p1, r, rule, seg=8, k='rod', far=False):
        return s.add(rod(p0, p1, r, None, seg=seg, name=s.nm(k)), rule, far)

    def keep(s, o, far=False):
        """a part with its own materials + UVs already (the traffic wheels): baked into world space"""
        apply_mods(o); bpy.context.view_layer.update()
        o.data.transform(o.matrix_world); o.matrix_world = Matrix.Identity(4)
        (s.l1 if far else s.l0).append(o)
        return o


def finish(B, meta, yaw, shift, boxes, air, ok=(), interior=None, ao=0.6):
    """into the prop frame, the fit check (parts by name), join each LOD, bake the AO (interior(game point, normal,
    material, baked) -> an AO that overrides the bake, or None), QA, prop_finish"""
    fid = B.fid
    for o in B.l0 + B.l1: apply_mods(o)
    to_frame(B.l0 + B.l1, yaw, shift)
    bpy.context.view_layer.update()
    if arg('fit'): fit_check(fid, B.l0, boxes, air, ok)
    if arg('parts'):  # triangles per kind of part
        tally = {}
        for o in B.l0:
            o.data.calc_loop_triangles(); k = o.name[len(fid) + 1:].rsplit('_', 1)[0].split('_')[0]
            tally[k] = tally.get(k, 0) + len(o.data.loop_triangles)
        print('JF_PARTS', fid, sorted(tally.items(), key=lambda kv: -kv[1]))
    if arg('uvdebug'):
        for o in B.l0:
            me = o.data
            for L in me.uv_layers:
                for p in me.polygons:
                    q = [L.data[li].uv for li in p.loop_indices]
                    a2 = sum(q[i].x * q[(i + 1) % len(q)].y - q[(i + 1) % len(q)].x * q[i].y for i in range(len(q)))
                    if abs(a2) < 1e-12: print('JF_UVZ', o.name, L.name, len(me.uv_layers), len(q), round(p.area, 6), [tuple(round(c, 4) for c in v) for v in q][:6])
    if arg('qaparts'): Y.qa(B.l0, fid + ':parts', eps=0.0008, tol=0.003)
    j0 = join(B.l0, fid[2:] + '_lod0')  # (no weld across parts: touching parts' corners would merge into bad edges)
    j1 = join(B.l1, fid[2:] + '_lod1') if B.l1 else None
    for j in (j0, j1):
        if j is None: continue
        bpy.context.view_layer.objects.active = j
        for s_ in bpy.context.view_layer.objects.selected: s_.select_set(False)
        j.select_set(True); bpy.ops.object.material_slot_remove_unused()
        smooth(j, 40)
    if not arg('no-ao'):
        bake([j0], [j0], dist=ao)
        if j1: bake([j1], [j1], dist=ao, lo=0.55)
        for j, fn in ((j0, interior), (j1, None)):
            if j is None: continue
            me = j.data; ca = me.color_attributes.get('AO')
            for p in me.polygons:
                mn = me.materials[p.material_index].name
                gn = b2g(p.normal)
                for li in p.loop_indices:
                    if mn.startswith('glow'): v = 1.0
                    elif fn: v = fn(b2g(me.vertices[me.loops[li].vertex_index].co), gn, mn, ca.data[li].color[0])
                    else: v = None
                    if v is not None: ca.data[li].color = (v, v, v, 1.0)
    if arg('zfdebug'):
        zf_where(j0)
        if j1: zf_where(j1)
    if arg('qa'):
        Y.qa([j0], fid + ':lod0', eps=0.0008, tol=0.004 if 'semi' in fid else 0.003)
        if j1: Y.qa([j1], fid + ':lod1', eps=0.0008, tol=0.01)
    root = prop_finish(fid, [j0], [j1] if j1 else [], meta)
    Y.report(root, fid)
    return root


# ============================================================ p_transitbus
def bus_boxes():
    """shared/map.js busBoxes(B, 0, 0), in the prop frame: [(lo, hi, mat, stays)]"""
    out = []
    def A(x0, y0, z0, x1, y1, z1, m, st=False): out.append(((x0, y0, z0), (x1, y1, z1), m, st))
    z0, z1, X = 0.0, 2.6, 12.0
    for wx in (2.2, 9.4):
        for a, b in ((z0 - 0.08, z0 + 0.4), (z1 - 0.4, z1 + 0.08)): A(wx - 0.55, 0, a, wx + 0.55, 1.1, b, 'tire')
    A(0, 0.45, z0, X, 0.9, z1, 'busyellow')
    A(0, 0.9, z0, X - 0.15, 1.7, z0 + 0.15, 'busyellow')
    A(0, 0.9, z1 - 0.15, 9.8, 1.7, z1, 'busyellow'); A(11.1, 0.9, z1 - 0.15, X - 0.15, 1.7, z1, 'busyellow')
    x = 0.0
    while x < 11.5:
        A(x, 1.7, z0, x + 0.22, 2.8, z0 + 0.15, 'busyellow')
        if x + 0.22 < 9.8 or x > 11.1: A(x, 1.7, z1 - 0.15, x + 0.22, 2.8, z1, 'busyellow')
        x += 1.55
    A(9.8, 1.7, z1 - 0.15, 9.95, 2.8, z1, 'busyellow'); A(11.1, 1.7, z1 - 0.15, 11.3, 2.8, z1, 'busyellow')
    A(0, 0.9, z0 + 0.15, 0.15, 1.75, z1 - 0.15, 'busyellow'); A(0, 2.45, z0 + 0.15, 0.15, 2.8, z1 - 0.15, 'busyellow')
    A(X - 0.15, 0.9, z0, X, 1.7, z1, 'busyellow'); A(X - 0.12, 1.7, z0 + 0.15, X - 0.02, 2.8, z1 - 0.15, 'glass')
    A(-0.06, 2.8, z0 - 0.06, X + 0.06, 3.1, z1 + 0.06, 'busyellow')
    A(1.5, 1.0, z0 - 0.03, 9.5, 1.6, z0, 'adbus', True)
    A(X, 0.6, z0 + 0.2, X + 0.05, 0.85, z0 + 0.6, 'light'); A(X, 0.6, z1 - 0.6, X + 0.05, 0.85, z1 - 0.2, 'light')
    A(-0.05, 1.0, z0 + 0.2, 0, 1.3, z0 + 0.5, 'tail'); A(-0.05, 1.0, z1 - 0.5, 0, 1.3, z1 - 0.2, 'tail')
    A(9.85, 0.2, z1, 11.05, 0.45, z1 + 0.5, 'metal')
    for i in range(6):
        x = 1 + i * 1.5
        A(x, 0.9, z0 + 0.15, x + 0.9, 1.35, z0 + 1.05, 'seat'); A(x + 0.8, 1.35, z0 + 0.15, x + 0.95, 2.0, z0 + 1.05, 'seat')
    return out


def bus_paint(PA, CA, win_l, win_r):
    """the bus's two pictures: the outside (busyellow, the pink pinstripe, JANK TRANSIT, fleet numbers, grime, a tag,
    the roof) and the inside (rubber floor + nosing + the line, cream panels, the ceiling, the dash), the insides with
    their shade painted in (big faces: vertex AO can't draw it)"""
    yel, ink, pink, blk = 0xffc418, 0x1a1016, 0xff2fa8, 0x16161a
    for k, sd in (('L', 1), ('R', 2), ('F', 3), ('B', 4)): PA.fill(k, yel, var=0.035, seed=sd)
    PA.fill('T', 0xeeeee8, var=0.04, seed=5); PA.fill('U', 0x2a2a2e, var=0.05, seed=6)
    for k, col in (('K', blk), ('D', 0x101012), ('W', 0xeeeee8), ('Y', yel)): PA.fill(k, col, var=0.03, seed=7)
    grime = lambda w: 1 - 0.28 * np.clip((0.95 - w['y']) / 0.5, 0, 1) ** 1.5
    for k in ('L', 'R', 'F', 'B'): PA.mul(k, grime)
    for k in ('L', 'R'): PA.line(k, [(0, 2.83, -6.1), (0, 2.83, 6.1)], 0x9a7410, 1.0)
    for k in ('F', 'B'): PA.line(k, [(-2, 2.83, 0), (2, 2.83, 0)], 0x9a7410, 1.0)
    r = np.random.default_rng(9)
    for k, wins in (('L', win_l), ('R', win_r)):  # rust run down from a few sills
        for (a, b) in wins[::2]:
            zc = a + (b - a) * r.uniform(0.2, 0.8)
            PA.poly(k, [(0, 1.69, zc - 0.05), (0, 1.69, zc + 0.04), (0, 1.3 + r.uniform(0, 0.2), zc + 0.01)], 0xa8641c)
    for k in ('L', 'R'):
        PA.rect(k, (0, 1.625, -6.1), (0, 1.675, 6.1), pink)  # the pinstripe over the livery
    PA.rect('F', (-1.4, 1.625, 0), (1.4, 1.675, 0), pink); PA.rect('B', (-1.4, 1.625, 0), (1.4, 1.675, 0), pink)
    PA.rect('F', (-1.4, 1.5, 0), (1.4, 1.625, 0), blk)  # the black band under the screen
    PA.text('R', (0, 1.36, -1.9), 'JANK TRANSIT', 2, ink, shadow=pink)
    PA.text('R', (0, 1.08, -1.9), 'WE GO PLACES. EVENTUALLY.', 1, ink)
    for k, z in (('L', 4.6), ('R', 5.55), ('L', -5.3), ('R', -5.3)): PA.text(k, (0, 1.32, z), '420', 1, ink)
    PA.text('F', (0.65, 1.3, 0), '69', 2, ink); PA.text('F', (-0.6, 1.3, 0), 'JANK', 1, ink)
    PA.text('B', (0, 2.63, 0), 'EMERGENCY EXIT', 1, 0xd01818)
    PA.text('B', (-0.55, 1.68, 0), '420', 1, ink)
    PA.text('B', (-0.68, 1.4, 0), 'JANK!', 1, 0xff4fd8, shadow=0x4a0a3a)  # somebody's tags
    PA.text('R', (0, 0.72, -4.9), 'JANK!', 1, 0xff4fd8, shadow=0x4a0a3a)
    PA.text('L', (0, 0.78, -5.05), 'GO TOUCH', 1, 0x2a6cff); PA.text('L', (0, 0.6, -5.05), 'GRASS', 1, 0x2a6cff)
    PA.mul('T', lambda w: 1 - 0.12 * np.exp(-(w['x'] / 0.5) ** 2) - 0.08 * (np.sin(w['z'] * 2.3) > 0.7))
    for zc in (-2.0, 2.0): PA.rect('T', (-0.42, 0, zc - 0.42), (0.42, 0, zc + 0.42), 0x9a7a5a)  # rust round the hatches
    # far LOD: the sides with the window band painted in (dark openings, the seat tops), the door, the screen
    for k, wins in (('lL', win_l), ('lR', win_r)):
        PA.fill(k, yel, var=0.035, seed=11); PA.mul(k, grime)
        PA.rect(k, (0, 1.625, -6.1), (0, 1.675, 6.1), pink)
        PA.rect(k, (0, 0.93, -6.1), (0, 0.99, 6.1), blk)
        for a, b in wins: PA.rect(k, (0, 1.7, a), (0, 2.8, b), 0x161a22); PA.rect(k, (0, 1.7, a), (0, 1.84, b), 0x0e5a54)
        for az in (-3.8, 3.4): PA.rect(k, (0, 0.0, az - 0.62), (0, 0.92, az + 0.62), 0x0e0e10)
    PA.rect('lR', (0, 0.9, 3.8), (0, 2.8, 5.1), 0x10141a)
    PA.text('lR', (0, 1.36, -1.9), 'JANK TRANSIT', 1, ink, shadow=pink)
    PA.fill('lF', yel, seed=12); PA.rect('lF', (-1.15, 1.7, 0), (1.15, 2.8, 0), 0x22344c); PA.rect('lF', (-1.3, 0.42, 0), (1.3, 0.59, 0), blk)
    PA.rect('lF', (-0.9, 2.84, 0), (0.9, 3.05, 0), 0x0a0a0c)
    for s in (1, -1): PA.rect('lF', (s * 0.7, 0.6, 0), (s * 1.1, 0.85, 0), 0xfff2b0)
    PA.fill('lB', yel, seed=13); PA.rect('lB', (-1.15, 1.75, 0), (1.15, 2.45, 0), 0x161a22); PA.rect('lB', (-0.7, 0.62, 0), (0.7, 1.55, 0), 0x18181c)
    for s in (1, -1): PA.rect('lB', (s * 0.8, 1.0, 0), (s * 1.1, 1.3, 0), 0xff2a2a)
    # ---- the inside
    grey, cream, kick = 0x3e4048, 0xe2d6bc, 0x4a4c54
    CA.fill('iT', grey, var=0.06, seed=21)
    sb = CA.sub('iT'); fl = r.random(sb.shape[:2]) < 0.06; sb[fl] = sb[fl] * 1.35  # anti-slip flecks
    W = CA.world('iT')
    sb *= (1 + 0.12 * np.exp(-((W['x'] + 0.45) / 0.35) ** 2) * (np.abs(W['z']) < 5.6))[:, :, None]  # the worn aisle
    CA.rect('iT', (-1.3, 0, 3.8), (-1.15, 0, 5.1), 0xffd21a)  # the door's nosing, the yellow line
    CA.rect('iT', (-1.15, 0, 3.8), (-1.1, 0, 5.1), 0x1a1a1a)
    CA.rect('iT', (-1.15, 0, 4.52), (0.24, 0, 4.6), 0xffd21a)
    CA.rect('iT', (0.42, 0, 4.78), (0.88, 0, 5.22), 0x585a62)  # where the driver's seat was (cleaner)
    for _ in range(14):  # gum
        zc, xc = r.uniform(-5.5, 5.5), r.uniform(-1.1, 0.2)
        CA.rect('iT', (xc, 0, zc), (xc + 0.05, 0, zc + 0.05), 0x8a8c94)
    CA.fill('iU', 0xe6e4da, var=0.03, seed=22)
    for zc in (-2.0, 2.0): CA.rect('iU', (-0.4, 0, zc - 0.4), (0.4, 0, zc + 0.4), 0xb8b6ae); CA.rect('iU', (-0.35, 0, zc - 0.35), (0.35, 0, zc + 0.35), 0xd0cec6)
    CA.poly('iU', [(-0.9, 0, -4.3), (-0.5, 0, -4.0), (-0.7, 0, -3.5), (-1.0, 0, -3.8)], 0xc2b89a)  # a leak
    for k in ('iR', 'iL'):
        CA.fill(k, cream, var=0.03, seed=23)
        CA.rect(k, (0, 0.86, -6), (0, 1.05, 6), kick)
        CA.rect(k, (0, 1.6, -6), (0, 1.7, 6), 0xc8bca2)
        for zc in (-5.89, -4.34, -2.79, -1.24, 0.31, 1.86, 3.41, 4.96): CA.line(k, [(0, 1.05, zc), (0, 1.6, zc)], 0xb4a88e, 1.0)
    CA.fill('iF', cream, var=0.03, seed=24); CA.rect('iF', (-1.2, 0.86, 0), (1.2, 1.05, 0), kick)
    CA.rect('iF', (-0.7, 1.1, 0), (0.7, 1.6, 0), 0xc8bca2)
    CA.line('iF', [(-0.7, 1.1, 0), (0.7, 1.1, 0), (0.7, 1.6, 0), (-0.7, 1.6, 0), (-0.7, 1.1, 0)], 0x8a806a, 1.0)  # the engine hatch
    CA.fill('iB', 0x26262c, var=0.04, seed=25); CA.rect('iB', (-1.2, 0.86, 0), (1.2, 1.05, 0), kick)
    CA.fill('iX', cream, seed=26); CA.fill('iK', kick, seed=27)
    wall_ao = lambda w: (1 - 0.32 * np.exp(-(w['y'] - 0.88) / 0.12)) * (1 - 0.18 * np.exp(-(2.8 - w['y']) / 0.1))
    for k in ('iR', 'iL', 'iF', 'iB'): CA.mul(k, wall_ao)
    def floor_ao(w):
        x, z = w['x'], w['z']
        edge = np.minimum(np.minimum(1.15 - x, x + 1.15), np.minimum(5.85 - z, z + 5.85))
        seat = np.zeros_like(x)
        for i in range(6):
            z0_ = -5 + 1.5 * i
            dz = np.maximum(np.maximum(z0_ - z, z - (z0_ + 0.95)), 0); dx = np.maximum(0.25 - x, 0)
            seat = np.maximum(seat, np.exp(-np.hypot(dx, dz) / 0.12) * (x > 0.1))
        return (1 - 0.35 * np.exp(-np.clip(edge, 0, 9) / 0.15) * (x > -1.16)) * (1 - 0.35 * seat)
    CA.mul('iT', floor_ao)
    CA.mul('iU', lambda w: 1 - 0.3 * np.exp(-np.clip(np.minimum(1.15 - np.abs(w['x']), 5.85 - np.abs(w['z'])), 0, 9) / 0.15))


def build_transitbus():
    fid = 'p_transitbus'
    PA = Atlas('bus_paint_t', 512, 448, 0xffc418)
    CA = Atlas('bus_cabin_t', 256, 256, 0x808080)
    lo, hi = (-1.36, 0.0, -6.06), (1.36, 3.1, 6.06)  # (car frame: front +z, left +x)
    PA.view('L', (0, 0, 512, 96), 'L', lo, hi); PA.view('R', (0, 96, 512, 96), 'R', lo, hi)
    PA.view('T', (0, 192, 512, 48), 'T', lo, hi); PA.view('F', (0, 240, 128, 96), 'F', lo, hi)
    PA.view('B', (128, 240, 128, 96), 'B', lo, hi); PA.view('U', (256, 240, 128, 48), 'U', lo, hi)
    for i, k in enumerate(('K', 'D', 'W', 'Y')): PA.cell(k, (384 + 16 * i, 240, 16, 16))
    PA.view('lF', (256, 288, 64, 48), 'F', lo, hi); PA.view('lB', (320, 288, 64, 48), 'B', lo, hi)
    PA.view('lL', (0, 336, 256, 48), 'L', lo, hi); PA.view('lR', (256, 336, 256, 48), 'R', lo, hi)
    ilo, ihi = (-1.3, 0.86, -5.85), (1.15, 2.82, 5.85)
    CA.view('iT', (0, 0, 256, 56), 'T', ilo, ihi); CA.view('iU', (0, 56, 256, 52), 'U', (-1.15, 0.86, -5.85), ihi)
    CA.view('iR', (0, 108, 256, 44), 'R', ilo, ihi); CA.view('iL', (0, 152, 256, 44), 'L', ilo, ihi)
    CA.view('iF', (0, 196, 64, 48), 'F', (-1.15, 0.86, -5.85), ihi); CA.view('iB', (64, 196, 64, 48), 'B', (-1.15, 0.86, -5.85), ihi)
    CA.cell('iX', (128, 196, 16, 16)); CA.cell('iK', (144, 196, 16, 16))
    paint = mat('paint', 0xffffff, rough=0.26, metal=0.08, clearcoat=1.0, tex=PA.img)
    cabin = mat('cabin', 0xffffff, rough=0.75, metal=0.0, tex=CA.img)
    trim = T.mat_trim('trim', lambda px, cell: paint_extra(px, cell, 'JNK 69', ('HOW IS MY', 'DRIVING? NO')))
    gh, gt = glow_mat(0xfff2b0), glow_mat(0xff2a2a)
    CE = Cells()
    B = Build(fid, [paint, cabin, trim, gh, gt], [PA, CA, CE, CE, CE])
    P_, C_, TR, GH, GT = 0, 1, 2, 3, 4
    tr = lambda k: (TR, k)
    HW, IN, FL, SL, CL, RF, BOT = 1.3, 1.15, 0.9, 1.7, 2.8, 3.1, 0.45
    AR, AF, RW = -3.8, 3.4, 0.55  # rear / front axle (car z), wheel radius
    inside = lambda c: abs(c.x) < IN + 0.025 and abs(c.z) < 5.875 and FL - 0.025 < c.y < CL + 0.025

    def shell(n, c):  # outside -> the paint views, inside -> the cabin views, floor-like tops low down -> the floor
        k = kind_of(n)
        if n.y > 0.7 and c.y < 1.2 and abs(c.z) < 5.9: return (C_, 'iT')
        if inside(c): return (C_, 'i' + k)
        return (P_, k)

    def side_part(n, c):  # side panels / pillars: faces across the length are in arches and openings: dark
        if abs(n.z) > 0.7 and abs(c.z) < 5.8: return (P_, 'D')
        return shell(n, c)

    # ---------------- the sides below the windows (skirt + wall, arches and the door cut out), the pillars, gaskets
    XS = [0.0, 1.55, 3.1, 4.65, 6.2, 7.75, 9.3, 10.85]  # busBoxes' pillar loop (prop x)
    win_l, win_r = [], []
    for s in (1, -1):
        xo, xi = s * HW, s * IN
        pan = cb((xo, BOT, -5.862), (xi, SL - 0.003, 5.862), B.nm('panel'), bev=0.012)  # (its top 3 mm under the sill gaskets)
        for az in (AR, AF):
            cut(pan, xprism(B.nm('archc'), rounded_zy(az - 0.62, az + 0.62, 0.2, 0.92, 0.2, 5), min(s * 0.9, s * 1.6), max(s * 0.9, s * 1.6)))
        if s < 0: cut(pan, cb((-1.6, 0.88, 3.798), (-0.9, 1.9, 5.102), B.nm('doorc')))
        B.add(pan, side_part)
        pz = [(x - 6.0, x + 0.22 - 6.0) for x in XS if s > 0 or (x + 0.22 < 9.8 or x > 11.1)]
        if s < 0: pz += [(3.8, 3.95), (5.1, 5.3)]
        pz.sort()
        for a, b in pz[1:]:  # (the first is the back corner column; their faces 2 mm inside the gaskets')
            B.box((xo - s * 0.002, SL - 0.005, a + 0.002), (xi + s * 0.002, CL + 0.015, b - 0.002), side_part, bev=0.01, k='pillar')
        edges = [v for ab in pz for v in ab] + [5.85]
        wins = [(edges[i], edges[i + 1]) for i in range(1, len(edges) - 1, 2)]
        wins = [w for w in wins if not (s < 0 and abs(w[0] - 3.95) < 1e-6)]  # (the door)
        (win_l if s > 0 else win_r).extend(wins)
        d0, d1 = sorted((xi - s * 0.015, xo + s * 0.02))
        for a, b in wins:
            for o in ring_frame(B.nm('gasket'), a, b, SL, CL, 0.04, d0, d1, 'x'): B.add(o, tr('rubber'))
    # ---------------- front + back caps (round corners), the corner columns, the screen, the sign
    def cap_plan(zi, zo, r=0.15):
        sg = 1 if zo > zi else -1
        arc = [(IN + r * math.cos(math.radians(90 * k / 5)), zi + sg * r * math.sin(math.radians(90 * k / 5))) for k in range(6)]
        return arc + [(-x, z) for x, z in reversed(arc)]
    B.add(yprism(B.nm('fcap'), cap_plan(5.85, 6.0), BOT, SL, bev=0.012), shell)
    B.add(yprism(B.nm('bcap'), cap_plan(-5.85, -6.0), BOT, 1.747, bev=0.012), shell)
    for s in (1, -1):
        q = [(s * IN, 5.852)] + [(s * (IN + 0.146 * math.cos(math.radians(90 * k / 5))), 5.852 + 0.146 * math.sin(math.radians(90 * k / 5))) for k in range(6)]
        B.add(yprism(B.nm('acol'), q, SL - 0.005, CL + 0.015, bev=0.008), side_part)  # (no box here: the screen's frame)
        q = [(s * (IN + 0.002), -5.782), (s * (HW - 0.002), -5.782)] + \
            [(s * (IN + 0.002 + 0.146 * math.cos(math.radians(90 * k / 5))), -5.85 - 0.146 * math.sin(math.radians(90 * k / 5))) for k in range(6)]
        B.add(yprism(B.nm('bcol'), q, SL - 0.005, CL + 0.015, bev=0.008), side_part)
    B.box((-IN + 0.001, 2.453, -5.995), (IN - 0.001, CL + 0.015, -5.852), shell, bev=0.01, k='bupper')
    B.box((-1.148, 1.695, 5.882), (1.148, 2.805, 5.978), tr('glassw'), k='screen')
    for o in ring_frame(B.nm('sgask'), -1.11, 1.11, 1.735, 2.765, 0.045, 5.865, 5.996, 'z'): B.add(o, tr('rubber'))
    B.box((-0.025, 1.73, 5.872), (0.025, 2.77, 5.99), tr('rubber'), k='divider')
    for s in (1, -1):  # wipers parked on the screen
        B.rod((s * 0.06, 1.8, 5.995), (s * 0.9, 2.08, 5.995), 0.011, tr('black'), seg=5, k='wiper')
        B.box((s * 0.03, 1.76, 5.975), (s * 0.1, 1.84, 6.005), tr('black'), k='wpiv')
    B.box((-0.92, 2.83, 6.03), (0.92, 3.055, 6.075), tr('black'), bev=0.012, k='signbox')
    B.box((-0.86, 2.855, 6.07), (0.86, 3.03, 6.082), tr('dest'), k='sign')
    # ---------------- roof (rolled edges), the ceiling inside, hatches
    B.add(rslab(B.nm('roof'), -1.36, 1.36, -6.06, 6.06, CL + 0.003, RF, 0.2, 0.12, 4, 3), shell)  # (3 mm over the gaskets' tops)
    B.box((-1.149, 2.79, -5.849), (1.149, 2.81, 5.849), (C_, 'iU'), k='ceiling')
    for zc in (-2.0, 2.0): B.box((-0.36, 3.085, zc - 0.36), (0.36, 3.125, zc + 0.36), tr('plastic'), bev=0.012, k='hatch')
    # ---------------- floor (+ the door's threshold), the dark underbody, the wheel humps inside
    B.add(yprism(B.nm('floor'), [(1.148, -5.848), (1.148, 5.848), (-1.148, 5.848), (-1.148, 5.1), (-1.298, 5.1), (-1.298, 3.8), (-1.148, 3.8), (-1.148, -5.848)], 0.86, FL), shell)
    B.box((-1.147, 0.47, -5.847), (1.147, 0.87, 5.847), tr('dark'), k='under')
    for s in (1, -1):
        for az in (AR, AF):
            xo = -1.285 if (s < 0 and az == AF) else s * 1.2
            B.box((xo, 0.892, az - 0.55), (s * 0.9, 1.105, az + 0.55), tr('diamond'), bev=0.03, k='hump')
    # ---------------- seats on their boxes (plinth, cushion, back, a grab handle), poles, rails, light diffusers
    for i in range(6):
        z0 = -5 + 1.5 * i; zk = z0 + 0.8
        B.box((0.258, 0.895, z0 + 0.004), (1.146, 1.2, z0 + 0.896), tr('shell'), bev=0.015, k='plinth')
        B.box((0.252, 1.19, z0), (1.148, 1.35, z0 + 0.9), lambda n, c: tr('moq') if n.y > 0.5 or abs(n.x) > 0.5 else tr('moq2'), bev=0.04, k='cushion')
        B.box((0.252, 1.345, zk), (1.148, 2.0, zk + 0.15), lambda n, c: tr('moq') if n.z < -0.6 else (tr('shell') if n.z > 0.6 else tr('moq2')), bev=0.03, k='back')
        for x in (0.34, 1.06): B.rod((x, 1.97, zk + 0.075), (x, 2.045, zk + 0.075), 0.014, tr('chrome'), seg=4, k='hpost')
        B.rod((0.32, 2.04, zk + 0.075), (1.08, 2.04, zk + 0.075), 0.016, tr('chrome'), seg=6, k='handle')
        if i % 2:
            B.rod((0.32, 1.99, zk + 0.075), (0.32, 2.8, zk + 0.075), 0.02, tr('chrome'), seg=8, k='pole')
            B.box((0.29, 2.2, zk + 0.045), (0.35, 2.26, zk + 0.105), tr('stop'), k='stopb')
    for x, z0_, z1_ in ((0.32, -5.6, 5.3), (-0.95, -5.6, 3.6)):
        B.rod((x, 2.745, z0_), (x, 2.745, z1_), 0.016, tr('chrome'), seg=8, k='rail')
        z = z0_
        while z <= z1_ + 1e-6:
            B.rod((x, 2.735, z), (x, 2.8, z), 0.01, tr('chrome'), seg=4, k='rbrk'); z += (z1_ - z0_) / 4
    for s in (1, -1): B.box((s * 0.45, 2.772, -5.4), (s * 0.75, 2.795, 5.2), tr('lens'), bev=0.006, k='diffuser')
    # ---------------- the door: gasket round the gap (the leaves are gone), grab rails, hinge stubs, the step
    for lo_, hi_ in (((-1.322, 1.1, 3.76), (-1.133, 1.72, 3.8)), ((-1.324, 1.705, 3.91), (-1.131, 2.83, 3.95)),
                     ((-1.318, 1.70, 3.78), (-1.137, 1.74, 3.93)), ((-1.322, 0.895, 5.1), (-1.133, 2.835, 5.14)),
                     ((-1.316, 2.8, 3.93), (-1.139, 2.84, 5.12))):  # (no two of them, or the windows' rings, share a plane)
        B.box(lo_, hi_, tr('rubber'), k='dgask')
    B.rod((-1.08, 1.095, 3.875), (-1.08, 2.6, 3.875), 0.018, tr('chrome'), seg=8, k='drail')
    B.rod((-1.152, 2.45, 3.875), (-1.08, 2.45, 3.875), 0.012, tr('chrome'), seg=6, k='dbrk')
    B.rod((-1.08, 0.9, 5.2), (-1.08, 2.6, 5.2), 0.018, tr('chrome'), seg=8, k='drail')
    for y in (1.05, 2.45): B.rod((-1.152, y, 5.2), (-1.08, y, 5.2), 0.012, tr('chrome'), seg=6, k='dbrk')
    for y in (1.25, 2.35): B.box((-1.34, y, 5.104), (-1.298, y + 0.12, 5.16), tr('metal'), k='hinge')
    B.box((-1.8, 0.2, 3.85), (-1.29, 0.45, 5.05), lambda n, c: tr('diamond') if n.y > 0.5 else tr('metal'), bev=0.012, k='step')
    B.box((-1.802, 0.437, 3.86), (-1.74, 0.452, 5.04), tr('nosing'), k='stepnose')
    for z in (4.0, 4.83): B.box((-1.72, 0.14, z), (-1.29, 0.205, z + 0.07), tr('metal'), k='stepbr')
    # ---------------- outside trim: rub rails, skirts, lamps, bumpers, louvres, plate, mirrors
    for s in (1, -1):
        xo = s * HW
        for a, b in ([(-5.84, 5.84)] if s > 0 else [(-5.84, 3.78), (5.12, 5.84)]):
            B.box((xo - s * 0.002, 0.93, a), (xo + s * 0.022, 0.99, b), tr('rubber'), bev=0.008, k='rub')
        for a, b in ((-5.84, AR - 0.63), (AR + 0.63, AF - 0.63), (AF + 0.63, 5.84)):
            B.box((xo - s * 0.004, 0.44, a), (xo + s * 0.012, 0.5, b), tr('rubber'), k='skirt')
        B.box((s * 0.68, 0.585, 5.992), (s * 1.12, 0.865, 6.03), tr('black'), bev=0.012, k='hbez')
        for xc in (0.8, 1.0):
            B.add(lathe([(0.095, 6.025), (0.095, 6.042), (0.0, 6.052)], (s * xc, 0.725, 0), None, seg=10, axis='z', name=B.nm('head')), (GH, 'lens'))
        B.box((s * 1.13, 0.66, 5.95), (s * 1.245, 0.79, 5.995), tr('ambl'), bev=0.01, k='ind')
        B.box((s * 0.78, 0.84, -6.03), (s * 1.12, 1.32, -5.992), tr('black'), bev=0.015, k='tbez')
        B.box((s * 0.8, 1.0, -6.05), (s * 1.1, 1.3, -6.028), (GT, 'lens'), bev=0.008, k='tail')
        B.box((s * 0.8, 0.86, -6.045), (s * 1.1, 0.98, -6.028), tr('ambl'), bev=0.006, k='tind')
        p0, p1, p2 = (s * 1.22, 3.0, 5.98), (s * 1.47, 2.92, 6.2), (s * 1.5, 2.62, 6.3)
        B.rod(p0, p1, 0.022, tr('black'), seg=6, k='stalk'); B.rod(p1, p2, 0.022, tr('black'), seg=6, k='stalk')
        B.box((s * 1.44, 2.18, 6.26), (s * 1.56, 2.64, 6.34), tr('black'), bev=0.02, k='mirror')
        B.box((s * 1.452, 2.2, 6.252), (s * 1.548, 2.62, 6.262), tr('glassw'), k='mglass')
    B.box((-1.24, 0.42, 5.955), (1.24, 0.59, 6.045), tr('rubber'), bev=0.035, seg=2, k='fbump')
    B.box((-1.24, 0.42, -6.045), (1.24, 0.59, -5.955), tr('rubber'), bev=0.035, seg=2, k='rbump')
    B.box((-0.24, 0.45, -6.058), (0.24, 0.555, -6.04), tr('plate2'), k='plate')
    B.box((-0.7, 0.62, -6.016), (0.7, 1.55, -5.994), tr('louvre'), bev=0.006, k='louvre')
    B.box((-0.6, 1.0, 5.994), (0.6, 1.14, 6.012), tr('grille2'), bev=0.004, k='fvent')
    B.box((-0.2, 1.2, 5.994), (0.2, 1.26, 6.008), tr('badge'), k='badge')
    B.box((0.25, 1.58, -6.006), (0.73, 1.64, -5.996), tr('sticker3'), k='stk')
    for o in ring_frame(B.nm('egask'), -1.15, 1.15, 1.75, 2.45, 0.04, -6.018, -5.832, 'z'): B.add(o, tr('rubber'))
    B.box((-0.2, 2.47, -5.846), (0.2, 2.53, -5.83), tr('redl'), k='ehandle')
    # ---------------- the driver's end: dials on the dash, the steering wheel, the seat's stub (the seat is gone)
    B.box((0.35, 1.38, 5.836), (1.0, 1.62, 5.851), tr('gauge'), k='dials')
    wc, ww, wn = V3((0.66, 1.74, 5.7)), V3((0, 0.866, 0.5)), V3((0, -0.5, 0.866))  # hub, the wheel's up, its axis
    B.rod(tuple(wc), tuple(wc + wn * 0.18), 0.035, tr('shell'), seg=8, k='column')
    ring = [tuple(wc + V3((1, 0, 0)) * 0.2 * math.cos(a) + ww * 0.2 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 17)[:-1]]
    B.add(tube(ring, 0.017, None, seg=6, name=B.nm('steer'), closed=True), tr('black'))
    for a in (-90, 30, 150):
        a = math.radians(a); B.rod(tuple(wc), tuple(wc + V3((1, 0, 0)) * 0.19 * math.cos(a) + ww * 0.19 * math.sin(a)), 0.012, tr('black'), seg=5, k='spoke')
    B.add(cyl(0.05, 0.1, (0.65, 0.94, 5.0), None, axis='y', seg=8, name=B.nm('stub')), tr('metal'))
    B.box((0.5, 0.899, 4.85), (0.8, 0.905, 5.15), tr('metal'), k='stubplate')
    # signs inside: NO SMOKING, the bell, EXIT over the back window, STAND on the floor
    B.box((1.144, 1.4, -0.95), (1.1495, 1.56, -0.65), tr('sgn_smoke'), k='sign')
    B.box((-1.1495, 1.36, 0.6), (-1.144, 1.52, 0.9), tr('sgn_bell'), k='sign')
    B.box((-0.16, 2.58, -5.851), (0.16, 2.7, -5.846), tr('sgn_exit'), k='sign')
    B.box((-0.55, 0.899, 4.36), (-0.25, 0.902, 4.5), tr('sgn_line'), k='sign')
    # ---------------- broken glass left in a few seals (the windows are long gone)
    for s, (a, b), corner in ((1, win_l[1], 0), (1, win_l[4], 3), (-1, win_r[2], 1), (-1, win_r[5], 2)):
        zc = a if corner in (0, 2) else b; yc = SL if corner in (0, 1) else CL
        du = 1 if corner in (0, 2) else -1; dv = 1 if corner in (0, 1) else -1
        pts = [(zc - du * 0.01, yc - dv * 0.01), (zc + du * 0.14, yc - dv * 0.01), (zc + du * 0.02, yc + dv * 0.09)]
        B.add(xprism(B.nm('shard'), pts, s * 1.215 - 0.005, s * 1.215 + 0.005), tr('glassw'))
    # ---------------- wheels: steel discs, singles in front, duals behind (in the tyre boxes, tucked under the skirts)
    rr = RW / math.cos(math.pi / 14)
    for s in (1, -1):
        for az, w, dual in ((AF, 0.3, 0.0), (AR, 0.165, 0.185)):
            o = T.wheel_mesh(B.nm('wheel'), rr, w, 'truck', trim, seg=14, dual=dual, side=s)
            o.location = gv(s * (1.27 - w / 2), RW, az)
            B.keep(o)
    # ---------------- far LOD: the closed body with its window band painted on, the roof, the wheels
    def far(n, c):
        k = kind_of(n)
        return (P_, {'L': 'lL', 'R': 'lR', 'F': 'lF', 'B': 'lB'}.get(k, k))
    B.box((-HW, BOT, -6.0), (HW, CL, 6.0), far, far=True, k='l1body')
    B.add(rslab(B.nm('l1roof'), -1.36, 1.36, -6.06, 6.06, CL - 0.01, RF, 0.2, 0.1, 1, 1), far, far=True)
    B.box((-1.24, 0.42, 5.96), (1.24, 0.59, 6.04), tr('rubber'), far=True, k='l1fb')
    B.box((-1.24, 0.42, -6.04), (1.24, 0.59, -5.96), tr('rubber'), far=True, k='l1rb')
    for s in (1, -1):
        for az in (AR, AF):
            r8 = RW / math.cos(math.pi / 8)
            o = T.lathe_x(B.nm('l1w'), [(r8, -0.17), (r8, 0.17), (0.0, 0.17)], 8, trim, T.band_cells(['rubber', 'steel']), phase=0.5)
            if s < 0: o.data.transform(Matrix.Scale(-1, 4, V3((1, 0, 0)))); o.data.flip_normals()
            o.data.transform(Matrix.Translation(gv(s * 1.1, RW, az)))
            B.keep(o, far=True)
    bus_paint(PA, CA, win_l, win_r)
    PA.write(); CA.write()
    ok = tuple(fid + '_' + k for k in ('rail', 'rbrk', 'pole', 'stopb', 'steer', 'column', 'spoke', 'drail', 'dbrk', 'diffuser', 'stub', 'handle', 'hpost', 'dials', 'ehandle'))
    return finish(B, {'id': 'transitbus', 'lod': 80, 'tint': False}, math.pi / 2, (6.0, 0.0, 1.3), bus_boxes(),
                  [((0.16, 0.9, 0.16), (11.84, 2.79, 2.44))], ok, interior=lambda g, n, mn, v: 0.86 if mn == 'cabin' else None)


# ============================================================ p_boxtruck
def truck_boxes():
    """shared/map.js truckBoxes(B, 0, 0, livery, true), in the prop frame (the step crate is p_crate's: it stays)"""
    out = []
    def A(x0, y0, z0, x1, y1, z1, m, st=False): out.append(((x0, y0, z0), (x1, y1, z1), m, st))
    z0, z1 = 0.0, 2.5
    for wx in (1.4, 5.6, 8.9):
        for a, b in ((z0 - 0.08, z0 + 0.4), (z1 - 0.4, z1 + 0.08)): A(wx - 0.5, 0, a, wx + 0.5, 1.0, b, 'tire')
    A(0.3, 0.5, 0.3, 9.9, 0.95, 2.2, 'metal')
    A(0, 0.95, 0, 7.4, 1.1, 2.5, 'wood')
    A(0, 1.1, 0, 7.4, 3.8, 0.12, 'truckbox'); A(0, 1.1, 2.38, 7.4, 3.8, 2.5, 'truckbox')
    A(7.28, 1.1, 0.12, 7.4, 3.8, 2.38, 'truckbox')
    A(0, 3.8, 0, 7.4, 3.95, 2.5, 'truckbox')
    A(0.05, 3.3, 0.12, 0.3, 3.8, 2.38, 'metal')
    A(1, 1.15, -0.03, 6.6, 3.3, 0, 'adtruck2', True); A(1, 1.15, 2.5, 6.6, 3.3, 2.53, 'adtruck2', True)
    A(-1.1, 0, 0.5, 0, 0.55, 2.0, 'crate', True)
    A(7.5, 0.95, 0, 10, 2.0, 2.5, 'carred')
    A(7.6, 2.0, 0.1, 9.4, 2.9, 2.4, 'glass'); A(7.5, 2.9, 0, 9.5, 3.05, 2.5, 'carred')
    A(10, 1.2, 0.2, 10.05, 1.5, 0.6, 'light'); A(10, 1.2, 1.9, 10.05, 1.5, 2.3, 'light')
    return out


class _CabGlass:
    """what make_traffic's glass_paint needs: the parts with glass faces, the glass material + its image, the cabin"""
    def __init__(s, cid, body, glass, img, cabin): s.id, s.body, s.glass, s.gimg, s.cabin = cid, body, glass, img, cabin


def truck_paint(PA, CA):
    red, white, ink, green = 0xd81e30, 0xf0f0f2, 0x2a2a30, 0x19a04a
    for k, sd in (('L', 31), ('R', 32)): PA.fill(k, white, var=0.025, seed=sd)
    PA.fill('T', white, var=0.035, seed=33); PA.fill('F', white, var=0.03, seed=34); PA.fill('B', white, var=0.03, seed=35)
    PA.fill('U', 0x2a2a2e, var=0.05, seed=36)
    for k, col in (('K', 0x141418), ('D', 0x0e0e10), ('W', white), ('Rd', red)): PA.fill(k, col, var=0.03, seed=37)
    for k in ('L', 'R'):  # the cab red, the box's dirty bottom, rivet rows, door seams, the name on the door
        PA.put(k, PA.mask(k, lambda w: w['z'] > 2.45), red)
        PA.mul(k, lambda w: np.where(w['z'] < 2.45, 1 - 0.22 * np.clip((1.45 - w['y']) / 0.35, 0, 1), 1.0))
        for zc in np.arange(-4.9, 2.4, 0.61):
            for y in np.arange(1.2, 3.75, 0.09): PA.rect(k, (0, y, zc - 0.01), (0, y + 0.03, zc + 0.01), 0xc4c6cc)
        PA.line(k, [(0, 0.98, 2.8), (0, 1.99, 2.8)], 0x7a0c16, 1.0); PA.line(k, [(0, 0.98, 4.15), (0, 1.6, 4.2), (0, 1.99, 4.22)], 0x7a0c16, 1.0)
        PA.line(k, [(0, 1.55, 3.55), (0, 1.55, 3.7)], 0x2a0408, 1.5)  # the door handle's shadow
        PA.text(k, (0, 1.35, 3.48), 'CB&C', 1, 0xffffff)
        PA.rect(k, (0, 1.0, 2.5), (0, 1.06, 5.1), 0x1a1a1e)  # the black rocker strip
    PA.put('T', PA.mask('T', lambda w: w['z'] > 2.45), red)
    PA.mul('T', lambda w: np.where(w['z'] < 2.45, 1 - 0.1 * (np.sin(w['z'] * 1.7 + w['x']) > 0.6), 1.0))
    for zc in np.arange(-4.8, 2.4, 0.6): PA.line('T', [(-1.2, 0, zc), (1.2, 0, zc)], 0xd0d2d6, 1.0)  # roof bows showing through
    PA.put('F', PA.mask('F', lambda w: w['y'] < 2.95), red)
    PA.put('B', PA.mask('B', lambda w: w['y'] < 2.95), white)
    PA.mul('B', lambda w: 1 - 0.25 * np.clip((1.4 - w['y']) / 0.4, 0, 1))
    # far LOD: the open back as a picture (floor, the dark inside, the rolled door at the top)
    PA.fill('lB', 0x1c1a18, var=0.05, seed=38)
    PA.rect('lB', (-1.3, 0.0, 0), (1.3, 1.1, 0), 0x2a2a2e); PA.rect('lB', (-1.13, 1.1, 0), (1.13, 1.4, 0), 0x6a4a2a)
    PA.rect('lB', (-1.13, 3.3, 0), (1.13, 3.8, 0), 0xb8bcc2)
    for k in ('lB',):
        PA.rect(k, (-1.3, 1.1, 0), (-1.13, 3.95, 0), 0xc2c6cc); PA.rect(k, (1.13, 1.1, 0), (1.3, 3.95, 0), 0xc2c6cc); PA.rect(k, (-1.3, 3.8, 0), (1.3, 3.95, 0), 0xc2c6cc)
    # ---- the box inside: plank floor, scuff boards + panels, the translucent roof with its bows
    CA.fill('iT', 0x9a6a3a, var=0.05, seed=41)
    W = CA.world('iT'); sb = CA.sub('iT')
    gap = (np.abs(((W['x'] + 1.13) % 0.142) - 0.071) > 0.064)
    sb[gap] = hexrgb(0x4a3018)
    r = np.random.default_rng(43)
    for i, x0 in enumerate(np.arange(-1.13, 1.13, 0.142)):
        sb *= np.where((W['x'] >= x0) & (W['x'] < x0 + 0.142), 0.92 + 0.12 * r.random(), 1.0)[:, :, None]
        zj = -5 + r.uniform(1, 5)
        CA.rect('iT', (x0, 0, zj), (x0 + 0.142, 0, zj + 0.02), 0x4a3018)
    for zc in np.arange(-4.6, 2.2, 0.9):
        for s in (1, -1): CA.rect('iT', (s * 1.02, 0, zc), (s * 1.1, 0, zc + 0.08), 0x2a2a2e)  # tie-down rings
    CA.mul('iT', lambda w: (1 - 0.3 * np.exp(-(1.13 - np.abs(w['x'])) / 0.12)) * (1 - 0.25 * np.exp(-(2.28 - w['z']) / 0.2)) * (1 - 0.06 * (np.sin(w['z'] * 3.1) > 0.8)))
    for k in ('iR', 'iL', 'iB'):
        CA.fill(k, 0xdcdde0, var=0.02, seed=44)
        CA.put(k, CA.mask(k, lambda w: w['y'] < 1.56), 0xa87e4e)
        CA.rect(k, (-2, 1.55, -6) if k == 'iB' else (0, 1.55, -6), (2, 1.57, 3) if k == 'iB' else (0, 1.57, 3), 0x6a4a2a)
        CA.mul(k, lambda w: (1 - 0.3 * np.exp(-(w['y'] - 1.1) / 0.15)) * (1 - 0.2 * np.exp(-(3.8 - w['y']) / 0.15)))
    for k in ('iR', 'iL'):
        for zc in np.arange(-5.0, 2.3, 1.22): CA.line(k, [(0, 1.57, zc), (0, 3.8, zc)], 0xb0b2b8, 1.0)
    CA.fill('iU', 0xe6ecee, var=0.03, seed=45)
    for zc in np.arange(-4.8, 2.3, 0.6): CA.rect('iU', (-1.13, 0, zc), (1.13, 0, zc + 0.05), 0xa8acb2)
    CA.mul('iU', lambda w: 1 - 0.25 * np.exp(-(1.13 - np.abs(w['x'])) / 0.15))
    CA.fill('iX', 0xdcdde0, seed=46); CA.fill('iK', 0x2a2a2e, seed=47)


def build_boxtruck():
    fid = 'p_boxtruck'
    PA = Atlas('truck_paint_t', 512, 384, 0xf0f0f2)
    CA = Atlas('truck_cabin_t', 256, 256, 0xd0d0d4)
    lo, hi = (-1.3, 0.0, -5.05), (1.3, 3.97, 5.1)  # (car frame: front +z, left +x)
    PA.view('L', (0, 0, 512, 128), 'L', lo, hi); PA.view('R', (0, 128, 512, 128), 'R', lo, hi)
    PA.view('T', (0, 256, 512, 64), 'T', lo, hi); PA.view('F', (0, 320, 64, 64), 'F', lo, hi)
    PA.view('B', (64, 320, 64, 64), 'B', lo, hi); PA.view('U', (128, 320, 128, 32), 'U', lo, hi)
    PA.view('lB', (256, 320, 64, 64), 'B', lo, hi)
    for i, k in enumerate(('K', 'D', 'W', 'Rd')): PA.cell(k, (336 + 16 * i, 320, 16, 16))
    ilo, ihi = (-1.13, 1.1, -5.0), (1.13, 3.8, 2.28)
    CA.view('iT', (0, 0, 256, 64), 'T', ilo, ihi); CA.view('iU', (0, 64, 256, 64), 'U', ilo, ihi)
    CA.view('iR', (0, 128, 256, 48), 'R', ilo, ihi); CA.view('iL', (0, 176, 256, 48), 'L', ilo, ihi)
    CA.view('iB', (0, 224, 64, 32), 'B', ilo, ihi); CA.view('iF', (64, 224, 64, 32), 'F', ilo, ihi)
    CA.cell('iX', (128, 224, 16, 16)); CA.cell('iK', (144, 224, 16, 16))
    paint = mat('paint', 0xffffff, rough=0.26, metal=0.08, clearcoat=1.0, tex=PA.img)
    cabin = mat('cabin', 0xffffff, rough=0.7, metal=0.0, tex=CA.img)
    trim = T.mat_trim('trim', lambda px, cell: paint_extra(px, cell, 'CB 8C', ('HOW IS MY', 'DRIVING? NO')))
    gimg = bpy.data.images.new('glass_boxtruck', 4, 4, alpha=False)
    glass = T.mat_glass('glass', gimg)
    gh = glow_mat(0xfff2b0)
    CE = Cells()
    B = Build(fid, [paint, cabin, trim, glass, gh], [PA, CA, CE, CE, CE])
    P_, C_, TR, GL, GH = 0, 1, 2, 3, 4
    tr = lambda k: (TR, k)
    HW, IN = 1.25, 1.13
    Z0, Z1, ZF = -5.0, 2.4, 2.28
    FB, FT, RB, RT = 0.95, 1.1, 3.8, 3.95
    A1, A2, A3, RW = -3.6, 0.6, 3.9, 0.5

    def body(n, c):  # the box: outside -> paint views, inside -> cabin views; the cab's back / the box's front low down: dark
        k = kind_of(n)
        if abs(c.x) < IN + 0.02 and Z0 - 0.02 < c.z < ZF + 0.02 and FT - 0.02 < c.y < RB + 0.02: return (C_, 'i' + k)
        if k == 'B' and c.z > 2.0: return (P_, 'D')
        if k == 'F' and c.z < 2.45 and c.y < 3.0: return (P_, 'D')
        return (P_, k)

    # ---------------- the box: plank floor, walls, front wall, roof
    B.box((-1.228, FB, Z0 + 0.008), (1.228, FT, Z1 - 0.004), body, bev=0.006, k='floor')
    for s in (1, -1): B.box((s * IN, FT - 0.01, Z0), (s * HW, RB + 0.01, Z1), body, bev=0.008, k='wall')
    B.box((-IN + 0.002, FT - 0.01, ZF), (IN - 0.002, RB + 0.01, Z1 - 0.002), body, k='fwall')
    B.box((-HW + 0.002, RB, Z0 + 0.002), (HW - 0.002, RT, Z1 - 0.002), body, bev=0.01, k='roof')
    # rails, corner posts, the rear frame (sill, header, the door's tracks), the rolled-up door on its drum
    for s in (1, -1):
        B.box((s * 1.23, 0.94, Z0 + 0.004), (s * 1.262, 1.13, Z1 - 0.004), tr('alum'), bev=0.006, k='brail')
        B.box((s * 1.23, 3.72, Z0 + 0.004), (s * 1.262, 3.962, Z1 - 0.004), tr('alum'), bev=0.006, k='trail')
        for z0_, z1_ in ((Z0 - 0.018, Z0 + 0.075), (Z1 - 0.075, Z1 + 0.018)):
            B.box((s * 1.115, 0.935, z0_), (s * 1.268, 3.966, z1_), tr('alum'), bev=0.008, k='post')
        B.box((s * 1.096, FT, Z0 + 0.02), (s * 1.131, 3.315, Z0 + 0.09), tr('alum'), k='track')
        for k_ in range(6):  # conspicuity tape along the bottom rail (red / white every 15 cm)
            z_ = Z0 + 0.15 + k_ * 1.2
            B.box((s * 1.262, 0.99, z_), (s * 1.266, 1.03, z_ + 1.1), tr('dottape'), k='tape')
        for z_ in (-4.4, -1.2, 1.9): B.box((s * 1.262, 1.04, z_ - 0.05), (s * 1.272, 1.09, z_ + 0.05), tr('ambl'), k='marker')
    B.box((-1.2, 0.93, Z0 - 0.012), (1.2, 1.104, Z0 + 0.06), lambda n, c: tr('diamond') if n.y > 0.5 else tr('alum'), k='sill')
    for k_ in range(2): B.box((-1.1 + k_ * 1.105, 0.95, Z0 - 0.016), (-0.005 + k_ * 1.105, 1.0, Z0 - 0.012), tr('dottape'), k='stape')
    B.box((-IN, 3.6, Z0 - 0.015), (IN, 3.962, Z0 + 0.048), tr('alum'), bev=0.006, k='header')
    B.add(xprism(B.nm('coil'), rrect(-4.948, -4.702, 3.302, 3.798, 0.11, 3), -1.128, 1.128), tr('slats'))
    for s in (1, -1): B.box((s * 1.104, 3.48, -4.9), (s * 1.13, 3.8, -4.74), tr('alum'), k='coilbrk')
    B.box((-1.1, 3.29, -4.965), (1.1, 3.35, -4.93), tr('alum'), k='doorbar')
    B.box((-0.12, 3.245, -4.972), (0.12, 3.29, -4.952), tr('black'), k='doorhdl')
    B.rod((0.0, 3.25, -4.962), (0.04, 3.02, -4.985), 0.011, tr('black'), seg=4, k='strap')
    for x in (-0.3, 0.0, 0.3): B.box((x - 0.05, 3.83, Z0 - 0.022), (x + 0.05, 3.88, Z0 - 0.012), tr('redl'), k='clear')
    B.box((-0.62, 3.64, Z0 - 0.02), (-0.02, 3.74, Z0 - 0.0145), tr('sticker4'), k='sticker')
    # inside: E-track, the dome light, the stencil
    for s in (1, -1):
        for y in (1.85, 2.75): B.box((s * 1.116, y, -4.85), (s * 1.131, y + 0.05, 2.15), tr('etrack'), k='etrack')
    B.box((-0.2, 3.775, -1.5), (0.2, 3.805, -1.1), tr('lens'), bev=0.008, k='dome')
    B.box((-0.42, 2.45, ZF - 0.004), (0.42, 2.62, ZF + 0.002), tr('stencil'), k='stencil')
    B.box((-0.8, 3.3, Z1 - 0.004), (0.8, 3.57, Z1 + 0.006), tr('boxlogo'), k='boxlogo')
    # ---------------- under the box: frame rails, axles, equipment between the wheels, guards, mud flaps, the ICC bar
    for s in (1, -1): B.box((s * 0.38, 0.5, -4.7), (s * 0.5, 0.82, 4.9), tr('dark'), k='frame')
    for az in (A1, A2): B.add(cyl(0.07, 1.7, (0, RW, az), None, axis='x', seg=8, name=B.nm('axle')), tr('dark'))
    B.add(cyl(0.07, 1.6, (0, RW, A3), None, axis='x', seg=8, name=B.nm('axle')), tr('dark'))
    for az in (A1, A2): B.add(ball(0.17, (0, RW, az), None, seg=8, rings=5, name=B.nm('diff')), tr('dark'))
    B.add(cyl(0.26, 1.1, (0.98, 0.69, 1.8), None, axis='z', seg=12, name=B.nm('tank')), tr('tank'))
    for z_ in (1.45, 2.15): B.box((0.7, 0.41, z_), (1.26, 0.97, z_ + 0.05), tr('black'), k='tstrap')
    B.box((-1.2, 0.5, 1.3), (-0.7, 0.94, 2.3), tr('cabtrim'), bev=0.015, k='batt')
    B.box((-1.205, 0.92, 1.28), (-0.69, 0.96, 2.32), tr('alum'), k='battlid')
    B.add(cyl(0.15, 1.5, (0.82, 0.72, -2.1), None, axis='z', seg=10, name=B.nm('airtank')), tr('alum'))
    B.box((0.66, 0.5, -1.15), (1.18, 0.94, -0.25), tr('alum'), bev=0.015, k='toolbox')
    B.box((-1.18, 0.5, -2.85), (-0.66, 0.94, -1.55), tr('alum'), bev=0.015, k='toolbox')
    B.add(cyl(0.15, 1.2, (-0.82, 0.72, -0.85), None, axis='z', seg=10, name=B.nm('airtank')), tr('alum'))
    for s in (1, -1):
        for y in (0.55, 0.8): B.box((s * 1.19, y, -3.0), (s * 1.225, y + 0.06, -0.02), tr('alum'), k='guard')
        for z_ in (-2.9, -1.5, -0.1): B.box((s * 1.18, 0.52, z_ - 0.025), (s * 1.226, 0.9, z_ + 0.025), tr('alum'), k='gpost')
        for az in (A1, A2):
            B.box((s * 0.95, 0.18, az - 0.562), (s * 1.3, 0.825, az - 0.548), tr('mudflap'), k='flap')
            B.box((s * 0.925, 0.82, az - 0.575), (s * 1.27, 0.9, az - 0.538), tr('black'), k='flapbar')
    B.box((-1.15, 0.505, -4.76), (1.15, 0.63, -4.64), lambda n, c: tr('dottape') if n.z < -0.5 else tr('alum'), k='icc')
    # the chassis box is solid: dark fairings along its sides between the wheels, its ends and the top in the cab gap
    gaps = sorted([(az - 0.56, az + 0.56) for az in (A1, A2, A3)])
    edges = [-4.69] + [v for g in gaps for v in g] + [4.875]
    for s in (1, -1):
        for i in range(0, len(edges), 2):
            if edges[i + 1] - edges[i] > 0.05: B.box((s * 0.93, 0.52, edges[i]), (s * 0.948, 0.932, edges[i + 1]), tr('dark'), k='fairing')
    B.box((-0.948, 0.52, -4.72), (0.948, 0.93, -4.69), tr('dark'), k='rearend')
    B.box((-0.944, 0.52, 4.86), (0.944, 0.938, 4.92), tr('dark'), k='valance')
    B.box((-0.948, 0.93, 2.39), (0.948, 0.952, 2.51), tr('diamond'), k='deck')
    for x in (-0.7, 0.7): B.box((x - 0.04, 0.6, -4.715), (x + 0.04, 0.96, -4.66), tr('alum'), k='iccpost')
    B.box((-0.24, 0.515, -4.777), (0.24, 0.62, -4.762), tr('plate2'), k='plate')
    # ---------------- the cab: a lofted lower body (round nose, the front arch), the glass house, the roof
    CZ0, CZ1 = 2.5, 5.0
    arches = [(A3, RW, 0.6)]
    def chw(z, r=0.16): return HW if z < CZ1 - r else (HW - r) + math.sqrt(max(r * r - (z - (CZ1 - r)) ** 2, 0))
    def ctop(z, r=0.12): return 2.0 if z < CZ1 - r else (2.0 - r) + math.sqrt(max(r * r - (z - (CZ1 - r)) ** 2, 0))
    def chalf(z):
        b, t, H = T.arch_floor(z, arches, FB), ctop(z), chw(z)
        return [(H - 0.03, b), (H, min(b + 0.04, t - 0.1)), (H, t - 0.07), (H - 0.025, t - 0.018), (H - 0.07, t - 0.002), (0.0, t)]
    zs = T.stations(CZ0, CZ1, 0.25, arches, extra=[CZ0 + 0.03, CZ1 - 0.16, CZ1 - 0.12, CZ1 - 0.08, CZ1 - 0.045, CZ1 - 0.015], arch_n=7, sill=FB)
    cab = T.zloft(B.nm('cab'), zs, chalf)
    B.add(cab, body)
    for s in (1, -1):  # the glass house's pillars, the frame round the screen, the back wall with its little window
        B.box((s * 1.03, 1.995, 4.29), (s * 1.15, 2.905, 4.4), body, bev=0.012, k='apil')
        B.box((s * 1.0, 1.995, 2.6), (s * 1.15, 2.905, 2.75), body, bev=0.012, k='bpil')
        B.box((s * 1.132, 2.03, 2.75), (s * 1.149, 2.875, 4.29), (GL, 'glass'), k='sideglass')
        B.box((s * 1.14, 1.995, 2.75), (s * 1.152, 2.035, 4.29), tr('cabtrim'), k='beltseal')
    B.box((-1.03, 2.84, 4.31), (1.03, 2.905, 4.4), body, k='screentop')
    B.box((-1.03, 1.995, 4.29), (1.03, 2.065, 4.4), body, k='cowl')
    B.box((-1.0, 2.065, 4.372), (1.0, 2.84, 4.398), (GL, 'glass'), k='screen')
    B.box((-1.0, 1.995, 2.6), (1.0, 2.905, 2.65), body, k='cabback')
    B.box((-0.6, 2.2, 2.594), (0.6, 2.7, 2.61), (GL, 'glass'), k='backglass')
    B.add(rslab(B.nm('croof'), -HW, HW, CZ0, 4.5, 2.9, 3.05, 0.12, 0.06, 4, 2), body)
    for x in (-0.45, 0.0, 0.45): B.box((x - 0.06, 3.0, 4.47), (x + 0.06, 3.045, 4.505), tr('ambl'), k='roofmk')
    for s in (1, -1):
        B.rod((s * 0.08, 2.09, 4.402), (s * 0.88, 2.34, 4.402), 0.011, tr('black'), seg=4, k='wiper')
        # west coast mirrors on arms off the A pillars, a spotter under each
        B.rod((s * 1.15, 2.5, 4.33), (s * 1.42, 2.52, 4.28), 0.016, tr('chromeb'), seg=6, k='marm')
        B.rod((s * 1.15, 2.12, 4.33), (s * 1.42, 2.1, 4.28), 0.016, tr('chromeb'), seg=6, k='marm')
        B.box((s * 1.385, 2.06, 4.19), (s * 1.465, 2.58, 4.3), tr('cabtrim'), bev=0.015, k='mirror')
        B.box((s * 1.395, 2.08, 4.182), (s * 1.455, 2.56, 4.192), tr('glassw'), k='mglass')
        B.box((s * 0.96, 0.55, 2.95), (s * 1.27, 0.6, 3.3), tr('diamond'), k='cstep')
        for z_ in (2.98, 3.27): B.rod((s * 1.1, 0.575, z_), (s * 1.1, 0.97, z_), 0.018, tr('black'), seg=4, k='cstepb')
        # the front: headlamps (the 'light' boxes) in chrome bezels, indicators, the fender lip over the arch
        B.box((s * 0.63, 1.18, 4.985), (s * 1.07, 1.52, 5.03), tr('chromeb'), bev=0.01, k='hbez')
        B.box((s * 0.66, 1.21, 5.02), (s * 1.04, 1.49, 5.05), (GH, 'lens'), bev=0.008, k='head')
        B.box((s * 0.9, 1.55, 4.96), (s * 1.06, 1.63, 5.004), tr('ambl'), bev=0.006, k='ind')
        B.box((s * 1.24, 1.5, 4.7), (s * 1.258, 1.6, 4.82), tr('ambl'), k='sidemk')
        pts = [(s * 1.262, RW + 0.64 * math.sin(math.radians(a)), A3 + 0.64 * math.cos(math.radians(a))) for a in range(15, 166, 15)]
        B.add(sweep(pts, 0.035, None, seg=5, name=B.nm('flare'), squash=(1.0, 0.55)), tr('cabtrim'))
        B.box((s * 0.86, 0.94, 2.52), (s * 1.24, 0.99, 3.28), tr('cabtrim'), k='cabmount')
    B.box((-0.6, 1.1, 4.995), (0.6, 1.86, 5.032), tr('grille3'), k='grille')
    B.box((-0.65, 1.07, 4.99), (0.65, 1.89, 5.02), tr('chromeb'), bev=0.012, k='gframe')
    B.box((-0.22, 1.9, 4.97), (0.22, 1.95, 5.005), tr('badge'), k='badge')
    B.box((-1.24, 0.94, 4.96), (1.24, 1.15, 5.07), tr('chromeb'), bev=0.03, k='bumper')
    B.box((-0.24, 0.98, 5.068), (0.24, 1.09, 5.078), tr('plate2'), k='fplate')
    # the stack behind the cab (in the gap between box and cab)
    B.rod((-1.1, 0.97, 2.45), (-1.1, 3.35, 2.45), 0.058, tr('chromeb'), seg=10, k='stack')
    B.rod((-1.1, 3.35, 2.45), (-1.1, 3.46, 2.39), 0.058, tr('chromeb'), seg=10, k='stack')
    B.add(cyl(0.075, 0.9, (-1.1, 2.3, 2.45), None, axis='y', seg=10, name=B.nm('shield')), tr('grille2'))
    # ---------------- wheels: three axles of steel discs (duals on the back two), inside the tyre boxes
    rr = RW / math.cos(math.pi / 14)
    for s in (1, -1):
        for az, w, dual, xo in ((A3, 0.3, 0.0, 1.33), (A2, 0.19, 0.23, 1.27), (A1, 0.19, 0.23, 1.27)):
            o = T.wheel_mesh(B.nm('wheel'), rr, w, 'truck', trim, seg=14, dual=dual, side=s)
            o.location = gv(s * (xo - w / 2), RW, az)
            B.keep(o)
    # ---------------- far LOD: the box (its open back as a picture), the cab in three blocks, the wheels
    def far(n, c):
        k = kind_of(n)
        if k == 'B' and c.z < -4.9: return (P_, 'lB')
        return body(n, c) if body(n, c)[0] == P_ else (P_, k)
    B.box((-HW, FB, Z0), (HW, RT, Z1), far, far=True, k='l1box')
    B.box((-HW, FB, CZ0), (HW, 2.0, CZ1), far, far=True, k='l1cab')
    B.box((-1.15, 2.0, 2.6), (1.15, 2.9, 4.4), (GL, 'glass'), far=True, k='l1glass')
    B.box((-HW, 2.895, CZ0), (HW, 3.05, 4.5), far, far=True, k='l1roof')
    B.box((-1.24, 0.94, 4.98), (1.24, 1.15, 5.06), tr('chromeb'), far=True, k='l1bump')
    B.box((-0.95, 0.5, -4.7), (0.95, 0.95, 4.9), tr('dark'), far=True, k='l1frame')
    r8 = RW / math.cos(math.pi / 8)
    for s in (1, -1):
        for az, xo in ((A1, 1.27), (A2, 1.27), (A3, 1.33)):
            o = T.lathe_x(B.nm('l1w'), [(r8, -0.2), (r8, 0.2), (0.0, 0.2)], 8, trim, T.band_cells(['rubber', 'steel']), phase=0.5)
            if s < 0: o.data.transform(Matrix.Scale(-1, 4, V3((1, 0, 0)))); o.data.flip_normals()
            o.data.transform(Matrix.Translation(gv(s * (xo - 0.2), RW, az)))
            B.keep(o, far=True)
    truck_paint(PA, CA)
    PA.write(); CA.write()
    T.glass_paint(_CabGlass('boxtruck', B.l0, glass, gimg, dict(belt=2.03, top=2.88, rows=[(3.3, 2.62, 0.55)], dash=2.18, wheel=(0.55, 2.3, 0.2, 0.06), far=0x26354a)))
    ok = tuple(fid + '_' + k for k in ('marm', 'mirror', 'mglass', 'cstep', 'cstepb', 'stack', 'shield', 'strap', 'dome', 'etrack', 'track', 'post'))
    return finish(B, {'id': 'boxtruck', 'lod': 80, 'tint': False}, math.pi / 2, (5.0, 0.0, 1.25), truck_boxes(),
                  [((0.02, 1.1, 0.14), (7.26, 3.79, 2.36))], ok, interior=lambda g, n, mn, v: 0.84 if mn == 'cabin' else None)


# ============================================================ the trailer (p_semitrailer, the back of p_semi)
def yard_trailer(AX=(1.2, 2.4), glow=None):
    """make_yard.py's p_trailer (its parts, built the same way, in its frame: rear at x 0, the kingpin end at +x, z 0..2.6
    across) with the semi layout's axles at AX and a light bar across the back on glow lenses (the 'tail' box). Returns
    (lod0 parts, lod1 parts, the materials + atlas rects for parts added to it)"""
    canvas, grey_noise, rect, shade, ctext, ellipse, tmat, R = Y.canvas, Y.grey_noise, Y.rect, Y.shade, Y.ctext, Y.ellipse, Y.tmat, Y.R
    mesh_from, uv_proj, prism, chrect, grid_quad, quad, uv_fill = Y.mesh_from, Y.uv_proj, Y.prism, Y.chrect, Y.grid_quad, Y.quad, Y.uv_fill
    weld, fix_zero_uv, uv_tread, uv_planar_xy, gnorm, gpt, uvl = Y.weld, Y.fix_zero_uv, Y.uv_tread, Y.uv_planar_xy, Y.gnorm, Y.gpt, Y.uvl
    TL, TWD, Y0, Y1 = 12.5, 2.6, 1.3, 4.1  # trailer() map.js, drawn as built at (x0, z0): rear at x 0, kingpin end at +x
    # ---------------- body atlas (white glossy panels) 256 x 256
    bp = canvas(256, 256, 0xeeeef2)
    rng = np.random.default_rng(91)
    grey_noise(bp, 0, 0, 256, 48, 0.94, 0.02, 92)  # SIDE: 12.5 x 2.8 m
    for k in range(21):
        x = int(round(k * 0.6 / TL * 256)) + 2
        for y in range(2, 47, 3): bp[y, x] = (0.74, 0.75, 0.78)
        bp[0:48, x + 1] *= 0.985
    for y in range(40, 48): bp[y, :] *= 0.97 - 0.012 * (y - 40)
    for k in range(16): shade(bp, int(rng.integers(0, 250)), 1, 1, int(rng.integers(4, 16)), 0.93)
    bp[48:56, :] = hexrgb(0xf0f0f4)  # RAIL: the bottom rail's face, conspicuity tape along it (red / white every 0.3 m)
    for k in range(0, 256, 12): rect(bp, k, 50, 6, 4, 0xd8202a); rect(bp, k + 6, 50, 6, 4, 0xf8f8f8)
    grey_noise(bp, 0, 56, 256, 40, 0.92, 0.02, 93)  # ROOF
    for k in range(21): bp[56:96, int(round(k * 0.6 / TL * 256)) + 1] *= 0.92
    for k in range(10): shade(bp, int(rng.integers(0, 240)), int(rng.integers(58, 92)), int(rng.integers(4, 14)), int(rng.integers(2, 5)), 0.9)
    # DOORS (rear, seen from behind: the viewer's right = +z), 2.36 x 2.41 m in 64 x 64
    dx0, dy0 = 0, 96
    grey_noise(bp, dx0, dy0, 64, 64, 0.94, 0.02, 94)
    bp[dy0:dy0 + 64, dx0 + 31:dx0 + 33] = (0.25, 0.25, 0.27)  # the seam between the leaves
    for y in (dy0 + 16, dy0 + 37, dy0 + 55): bp[y, dx0:dx0 + 64] *= 0.86
    for x in (dx0, dx0 + 63): bp[dy0:dy0 + 64, x] = (0.3, 0.3, 0.32)
    bp[dy0, dx0:dx0 + 64] = (0.3, 0.3, 0.32); bp[dy0 + 63, dx0:dx0 + 64] = (0.3, 0.3, 0.32)
    for y in range(dy0 + 56, dy0 + 64): bp[y, dx0:dx0 + 64] *= 0.97 - 0.012 * (y - dy0 - 56)  # road grime
    # FRONT (2.4 x 2.8 m in 64 x 64): rivet columns, a junction box, NO STEP
    fx0, fy0 = 64, 96
    grey_noise(bp, fx0, fy0, 64, 64, 0.93, 0.02, 95)
    for k in range(1, 8):
        x = fx0 + k * 8
        for y in range(fy0 + 2, fy0 + 62, 3): bp[y, x] = (0.74, 0.75, 0.78)
    rect(bp, fx0 + 27, fy0 + 47, 10, 8, 0x2a2c30); rect(bp, fx0 + 28, fy0 + 48, 8, 6, 0x44474e)
    # the bumper sticker (its own quad on the right leaf): 0.64 x 0.32 m, 1 cm a pixel
    kx, ky = 128, 96
    rect(bp, kx, ky, 64, 32, 0x111111); rect(bp, kx + 1, ky + 1, 62, 30, 0xffe14d)
    ctext(bp, "HOW'S MY", kx + 32, ky + 3, 1, 0x111111); ctext(bp, 'DRIVING?', kx + 32, ky + 12, 1, 0x111111)
    rect(bp, kx + 4, ky + 21, 56, 1, 0x111111); ctext(bp, "DON'T CALL", kx + 32, ky + 23, 1, 0xd8202a)
    bp[96:128, 192:224] = hexrgb(0xeeeef2); grey_noise(bp, 192, 96, 32, 32, 0.93, 0.02, 96)  # PLAIN
    # LAMPS (tail cluster: black housing, red / amber / white lenses), markers, tape
    rect(bp, 128, 128, 64, 32, 0x141416)
    for i, c in enumerate((0xd8101a, 0xd8101a, 0xff8a10, 0xf4f4f0, 0xd8101a)):
        px_disc(bp, 134 + i * 12.5, 144, 5.2, c); px_disc(bp, 133 + i * 12.5, 142.5, 1.6, 0xffffff)
    rect(bp, 224, 96, 16, 16, 0xff8a10); px_disc(bp, 230, 102, 2.5, 0xffd080)
    rect(bp, 240, 96, 16, 16, 0xd8101a); px_disc(bp, 246, 102, 2.5, 0xff8080)
    for k in range(0, 32, 8): rect(bp, 224 + k, 112, 4, 16, 0xd8202a); rect(bp, 228 + k, 112, 4, 16, 0xf8f8f8)
    rect(bp, 192, 128, 64, 16, 0x141416)  # CLEAR: three clearance lights on a strip
    for i in range(3): px_disc(bp, 202 + i * 22, 136, 5, 0xd8101a); px_disc(bp, 201 + i * 22, 134.5, 1.4, 0xff9090)
    # lod1 pictures
    grey_noise(bp, 0, 192, 256, 32, 0.93, 0.02, 97)
    shade(bp, 0, 192, 256, 1, 0.8); bp[220:224, :] *= 0.9; bp[221:223, ::5] = (0.85, 0.12, 0.16)
    for k in range(21): bp[192:220, int(round(k * 0.6 / TL * 256)) + 1] *= 0.95
    bp[160:192, 0:32] = bp[96:160:2, 0:64:2]  # rear (the doors, small)
    bp[160:192, 32:64] = bp[96:160:2, 64:128:2]
    grey_noise(bp, 0, 224, 256, 32, 0.92, 0.02, 98)
    body = tmat('tr_body', bp, rough=0.3, clearcoat=0.4)
    SIDE, RAIL, ROOF = R(0, 0, 256, 48, 256, 256), R(0, 48, 256, 8, 256, 256), R(0, 56, 256, 40, 256, 256)
    DOORS, FRONT, PLAIN, STICK = R(0, 96, 64, 64, 256, 256, 0), R(64, 96, 64, 64, 256, 256, 0), R(194, 98, 28, 28, 256, 256), R(128, 96, 64, 32, 256, 256, 0)
    LAMPS, MARKA, MARKR, TAPE, CLEAR = R(128, 128, 64, 32, 256, 256), R(225, 97, 14, 14, 256, 256), R(241, 97, 14, 14, 256, 256), R(224, 112, 32, 16, 256, 256), R(192, 128, 64, 16, 256, 256)
    L1S, L1R, L1F, L1T = R(0, 192, 256, 32, 256, 256), R(0, 160, 32, 32, 256, 256), R(32, 160, 32, 32, 256, 256), R(0, 224, 256, 32, 256, 256)
    # ---------------- dark atlas (tyres, chassis, rubber) 128 x 128
    kp = canvas(128, 128, 0x1c1c1e)
    grey_noise(kp, 0, 0, 64, 32, 0.1, 0.012, 101)  # TREAD (u round, v across both duals)
    for v in (4, 9, 14, 22, 27): kp[v:v + 1, 0:64] = (0.05, 0.05, 0.055)
    kp[15:17, 0:64] = (0.02, 0.02, 0.02)  # the gap between the duals
    for u in range(0, 64, 4): kp[0:3, u:u + 2] *= 0.6; kp[29:32, u:u + 2] *= 0.6
    grey_noise(kp, 64, 0, 64, 64, 0.1, 0.012, 102)  # SIDEWALL (seen straight on, the wheel's r 0.5 = 32 px)
    yy, xx = np.mgrid[0:64, 0:64] + 0.5; rr_ = np.hypot(xx - 32, yy - 32)
    kp[0:64, 64:128][(rr_ > 26) & (rr_ < 27.2)] = (0.16, 0.16, 0.17)
    kp[0:64, 64:128][(rr_ > 30.5)] = (0.13, 0.13, 0.14)
    grey_noise(kp, 0, 32, 32, 32, 0.2, 0.025, 103)  # STEELD (chassis, legs)
    grey_noise(kp, 32, 32, 32, 32, 0.08, 0.01, 104)  # RUB
    grey_noise(kp, 0, 64, 128, 32, 0.15, 0.02, 105)  # UNDER: the floor's cross members, every 0.3 m
    for k in range(0, 128, 3): kp[64:96, k] = (0.07, 0.07, 0.075)
    grey_noise(kp, 0, 96, 96, 16, 0.16, 0.02, 106)  # XEND: cross-member ends seen from the side
    for k in range(0, 96, 2): kp[96:112, k] = (0.05, 0.05, 0.055); kp[97, k] = kp[110, k] = (0.22, 0.22, 0.24)
    grey_noise(kp, 0, 112, 32, 16, 0.07, 0.01, 107)  # FLAP
    for y in (114, 125): kp[y, 2:30] = (0.75, 0.75, 0.78)
    kp[96:128, 96:128] = kp[0:64:2, 64:128:2]  # WHEEL1: the far wheel's face (tyre + a grey rim)
    yy, xx = np.mgrid[0:32, 0:32] + 0.5; r2 = np.hypot(xx - 16, yy - 16)
    kp[96:128, 96:128][r2 < 9.6] = (0.62, 0.64, 0.68); kp[96:128, 96:128][r2 < 3] = (0.3, 0.3, 0.32)
    dark = tmat('tr_dark', kp, rough=0.7, metal=0.1)
    TREAD, SIDEW, STEELD, RUB = R(0, 0, 64, 32, 128, 128, 0), R(64, 0, 64, 64, 128, 128, 0), R(2, 34, 28, 28, 128, 128), R(34, 34, 28, 28, 128, 128)
    UNDER, XEND, FLAP, WHEEL1 = R(0, 64, 128, 32, 128, 128), R(0, 96, 96, 16, 128, 128), R(0, 112, 32, 16, 128, 128), R(96, 96, 32, 32, 128, 128, 0)
    # ---------------- steel atlas (disc wheels, rods, hinges) 128 x 64
    sp = canvas(128, 64, 0xb8bcc4)
    yy, xx = np.mgrid[0:64, 0:64] + 0.5; rr_ = np.hypot(xx - 32, yy - 32); ang = np.arctan2(yy - 32, xx - 32)
    disc = sp[:, 0:64]
    disc[:] = (0.74, 0.76, 0.8)
    disc[rr_ > 28] = (0.88, 0.9, 0.93); disc[(rr_ > 26.5) & (rr_ < 28)] = (0.5, 0.52, 0.56)
    for k in range(10):  # hand holes + lug nuts
        a = 2 * math.pi * k / 10
        ellipse(disc, 32 + 19 * math.cos(a), 32 + 19 * math.sin(a), 3.2, 3.2, (0.12, 0.12, 0.13))
        rect(disc, int(32 + 11.5 * math.cos(a + 0.31)) - 1, int(32 + 11.5 * math.sin(a + 0.31)) - 1, 3, 3, (0.95, 0.95, 0.97))
    disc[rr_ < 8] = (0.55, 0.57, 0.6); disc[rr_ < 4.5] = (0.85, 0.87, 0.9)
    grey_noise(sp, 64, 0, 32, 32, 0.72, 0.04, 108)  # GALV
    grey_noise(sp, 96, 0, 32, 32, 0.86, 0.03, 109)  # CHROME
    grey_noise(sp, 64, 32, 32, 32, 0.32, 0.03, 110)  # DARKSTEEL
    steel = tmat('tr_steel', sp, rough=0.25, metal=0.9)
    RIM, GALV, CHROME, DSTEEL = R(0, 0, 64, 64, 128, 64, 0), R(66, 2, 28, 28, 128, 64), R(98, 2, 28, 28, 128, 64), R(66, 34, 28, 28, 128, 64)

    P = []; A = P.append
    def U(o, rect_): uv_fill(o, rect_); return o
    # ---------------- the box: skins, rails, roof, the rounded front, the rear frame + doors
    for zs, out in ((0.004, -1), (TWD - 0.004, 1)):
        o = mesh_from('tr_skin', [(x, y, zs) for y in (1.44, 1.5, 3.9, 3.98) for x in (0.11, 1.0, 11.5, 12.41)],
                      [(j * 4 + i, j * 4 + i + 1, (j + 1) * 4 + i + 1, (j + 1) * 4 + i) for j in range(3) for i in range(3)], body, out=(0, 0, out))
        uv_proj(o, {'+z': (SIDE, (0, Y0, 0), (1, 0, 0), (0, 1, 0), TL, Y1 - Y0), '-z': (SIDE, (0, Y0, 0), (1, 0, 0), (0, 1, 0), TL, Y1 - Y0)}); A(o)
    for zc in (0.03, TWD - 0.03):
        A(prism('tr_toprail', chrect(4.035, zc, 0.065, 0.03, 0.012), 0.12, 12.4, 'x', body))
    for zc in (0.04, TWD - 0.04):
        o = prism('tr_botrail', chrect(1.375, zc, 0.075, 0.04, 0.012), 0.12, 12.4, 'x', body); A(o)
    roof = grid_quad('tr_roof', (0.12, 4.088, 0.06), (12.28, 0, 0), (0, 0, TWD - 0.12), 4, 1, body, out=(0, 1, 0))
    uv_proj(roof, {'+y': (ROOF, (0, 0, 0), (1, 0, 0), (0, 0, 1), TL, TWD)}); A(roof)
    for (cz, a0, a1) in ((0.1, -90, 0), (TWD - 0.1, 0, 90)):  # rounded front corners
        sec = [(12.4 + 0.1 * math.cos(math.radians(a0 + (a1 - a0) * i / 4)), cz + 0.1 * math.sin(math.radians(a0 + (a1 - a0) * i / 4))) for i in range(5)]
        A(prism('tr_corner', [(x, z) for x, z in sec], Y0, Y1, 'y', body, closed=False))
    fw = grid_quad('tr_front', (TL, Y0, 0.1), (0, 0, TWD - 0.2), (0, Y1 - Y0, 0), 2, 2, body, out=(1, 0, 0))
    uv_proj(fw, {'+x': (FRONT, (TL, Y0, TWD - 0.1), (0, 0, -1), (0, 1, 0), TWD - 0.2, Y1 - Y0)}); A(fw)
    for (y, h, c) in ((1.62, 0.07, MARKR), (1.62, 0.07, MARKA)):
        pass
    for zc, rr2 in ((1.05, MARKR), (1.55, MARKA)):  # glad hands (red / blue-ish) + the light socket on the front
        o = box((0.05, 0.07, 0.11), (TL + 0.025, 1.62, zc), steel if rr2 is None else body, name='tr_gladhand'); U(o, rr2); A(o)
    o = box((0.06, 0.1, 0.1), (TL + 0.03, 1.66, 1.3), dark, name='tr_socket'); U(o, RUB); A(o)
    for zc in (0.06, TWD - 0.06):  # rear corner posts
        A(prism('tr_rpost', chrect(0.06, zc, 0.06, 0.06, 0.012), Y0, Y1, 'y', body))
    A(prism('tr_header', chrect(0.06, 3.98, 0.06, 0.12, 0.012), 0.12, TWD - 0.12, 'z', body))
    A(prism('tr_sill', chrect(0.07, 1.375, 0.07, 0.075, 0.012), 0.12, TWD - 0.12, 'z', body))
    for o in P:
        if o.name.startswith(('tr_toprail', 'tr_corner', 'tr_rpost', 'tr_header', 'tr_sill')): U(o, PLAIN)
    for o in P:
        if o.name.startswith('tr_botrail'):  # the conspicuity tape on its outer face
            apply_mods(o); me = o.data; uv = uvl(o)
            for p in me.polygons:
                gn = gnorm(o, p.normal); outer = abs(gn.z) > 0.9 and ((gn.z < 0) == (lib.centre(o)[2] < 1.3))
                pts = [gpt(o, me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
                for li, q in zip(p.loop_indices, pts):
                    if outer: uv[li].uv = (RAIL[0] + q.x / TL * (RAIL[2] - RAIL[0]), RAIL[1] + (q.y - 1.3) / 0.15 * (RAIL[3] - RAIL[1]))
                    else: uv[li].uv = (PLAIN[0] + 0.5 * (PLAIN[2] - PLAIN[0]) + (q.x / TL - 0.5) * 0.02, PLAIN[1] + 0.5 * (PLAIN[3] - PLAIN[1]) + (q.y + q.z) * 0.005)
    # rear doors: two leaves 5 cm in (the locking gear sits in front), the picture across both
    for (za, zb) in ((0.12, 1.298), (1.302, TWD - 0.12)):
        o = prism('tr_leaf', [(0.09, za), (0.056, za), (0.05, za + 0.006), (0.05, zb - 0.006), (0.056, zb), (0.09, zb)], 1.45, 3.86, 'y', body, closed=False)
        uv_proj(o, {'-x': (DOORS, (0, 1.45, 0.12), (0, 0, 1), (0, 1, 0), TWD - 0.24, 2.41)}, default=(PLAIN, (0, 0, 0), (0, 0, 1), (0, 1, 0), 40, 40)); A(o)
    o = quad('tr_sticker', (0.047, 2.25, 1.89), (0, 0, 1), (0, 1, 0), 0.5, 0.25, body, STICK); A(o)  # HOW'S MY DRIVING? on the right leaf
    steelp = []
    def S(o, rect_=GALV): A(o); steelp.append((o, rect_)); return o
    for zr in (0.42, 1.0, 1.6, 2.18):  # lock rods, keepers, guides, handles
        S(cyl(0.018, 2.56, (0.03, 1.38 + 1.28, zr), steel, axis='y', seg=6, name='tr_rod', cap=False))
        for y in (1.39, 3.93): S(box((0.05, 0.07, 0.08), (0.02, y, zr), steel, name='tr_keeper'))
        hz = zr + (0.17 if zr in (0.42, 1.6) else -0.17)
        S(box((0.022, 0.045, 0.36), (0.008, 1.85, (zr + hz) / 2), steel, name='tr_handle'))
    for zc in (0.115, TWD - 0.115):  # hinges on the posts
        for y in (1.75, 2.65, 3.55):
            S(cyl(0.022, 0.12, (0.035, y, zc), steel, axis='y', seg=6, name='tr_hinge'), DSTEEL)
            S(box((0.014, 0.1, 0.13), (0.043, y, zc + (0.07 if zc < 1 else -0.07)), steel, name='tr_hstrap'), DSTEEL)
    # tail lights on the sill, clearance lights on the header, side markers on the bottom rails
    # the light bar across the back (the semi's 'tail' box: x -0.05..0, y 1.25..1.35 the whole width): red glow lenses
    o = box((0.055, 0.11, 2.5), (-0.022, 1.3, TWD / 2), dark, name='tr_tailbar'); U(o, STEELD); A(o)
    for k in range(6):
        o = box((0.012, 0.07, 0.26), (-0.053, 1.3, 0.3 + k * 0.4), glow or body, name='tr_tail'); A(o)
        if glow is None: U(o, MARKR)
        else: uv_fill(o, PLAIN)
    for zc in (0.08, TWD - 0.08):
        o = box((0.012, 0.07, 0.07), (-0.053, 1.3, zc), body, name='tr_tailamb'); U(o, MARKA); A(o)
    o = mesh_from('tr_clear', [(-0.002, 3.95, 1.0), (-0.002, 3.95, 1.6), (-0.002, 4.01, 1.6), (-0.002, 4.01, 1.0)], [(0, 1, 2, 3)], body, out=(-1, 0, 0))
    uv_proj(o, {'-x': (CLEAR, (0, 3.95, 1.0), (0, 0, 1), (0, 1, 0), 0.6, 0.06)}); A(o)
    for zs in (-0.015, TWD + 0.015):
        for x, mk in ((0.35, MARKR), (6.25, MARKA), (12.2, MARKA)):
            o = box((0.09, 0.05, 0.03), (x, 1.375, zs), body, name='tr_marker'); U(o, mk); A(o)
    # ---------------- chassis: main beams, floor underside, cross-member ends, slider, axles, air ride, landing gear
    for zc in (0.75, 1.85):
        sec = [(1.0, zc - 0.06), (1.0, zc + 0.06), (1.022, zc + 0.06), (1.022, zc + 0.006), (1.278, zc + 0.006), (1.278, zc + 0.06), (1.3, zc + 0.06), (1.3, zc - 0.06),
               (1.278, zc - 0.06), (1.278, zc - 0.006), (1.022, zc - 0.006), (1.022, zc - 0.06)]
        o = prism('tr_beam', sec, 2.7, 12.2, 'x', dark, caps=(True, True), concave=True, soft=False); U(o, STEELD); A(o)
    fl = grid_quad('tr_floor', (0.14, 1.299, 0.08), (12.26, 0, 0), (0, 0, TWD - 0.16), 3, 1, dark, out=(0, -1, 0))
    uv_proj(fl, {'-y': (UNDER, (0, 0, 0), (1, 0, 0), (0, 0, 1), TL, TWD)}); A(fl)
    for zs, out in ((0.09, -1), (TWD - 0.09, 1)):
        o = grid_quad('tr_xend', (2.7, 1.19, zs), (9.6, 0, 0), (0, 0.11, 0), 1, 1, dark, out=(0, 0, out))
        uv_proj(o, {'-z': (XEND, (2.7, 1.19, 0), (1, 0, 0), (0, 1, 0), 9.6, 0.11), '+z': (XEND, (2.7, 1.19, 0), (1, 0, 0), (0, 1, 0), 9.6, 0.11)}); A(o)
    for zc in (0.6, 2.0):
        o = prism('tr_slider', chrect(1.125, zc, 0.175, 0.05, 0.01), AX[0] - 0.6, AX[1] + 0.55, 'x', dark, caps=(True, True)); U(o, STEELD); A(o)
        for ax_ in AX:
            o = box((0.12, 0.32, 0.08), (ax_ + 0.45, 0.8, zc), dark, name='tr_hanger'); U(o, STEELD); A(o)
            o = box((0.92, 0.1, 0.09), (ax_ + 0.03, 0.61, zc), dark, name='tr_arm'); U(o, STEELD); A(o)
            o = cyl(0.11, 0.3, (ax_ - 0.34, 0.66 + 0.15, zc), dark, axis='y', seg=8, name='tr_airbag', cap=False); U(o, RUB); A(o)
    for ax_ in AX:
        o = cyl(0.065, 1.64, (ax_, 0.5, TWD / 2), dark, axis='z', seg=8, name='tr_axle', cap=False); U(o, STEELD); A(o)
    for zc in (0.3, TWD - 0.3):  # (this layout's axle box is solid: the slider's side rails close it, above the tyres)
        o = box((AX[1] - AX[0] + 1.19, 0.27, 0.02), ((AX[0] + AX[1]) / 2, 1.14, zc + (0.01 if zc < 1 else -0.01)), dark, name='tr_sliderside'); U(o, STEELD); A(o)
    for x_ in (AX[0] - 0.6, AX[1] + 0.6):
        o = box((0.02, 0.31, 1.98), (x_, 1.125, TWD / 2), dark, name='tr_sliderend'); U(o, STEELD); A(o)
    for zc in (0.4, 2.2):  # landing gear
        o = prism('tr_leg', chrect(9.5, zc, 0.07, 0.07, 0.01), 0.58, Y0, 'y', dark, caps=(True, False)); U(o, STEELD); A(o)
        o = prism('tr_legin', chrect(9.5, zc, 0.052, 0.052, 0.008), 0.07, 0.6, 'y', dark); U(o, DSTEEL); A(o)
        o = box((0.26, 0.05, 0.22), (9.5, 0.025, zc), dark, name='tr_foot'); U(o, STEELD); A(o)
        o = box((0.12, 0.05, 0.12), (9.5, 0.07, zc), dark, name='tr_pivot'); U(o, STEELD); A(o)
        o = rod((9.5, 0.78, zc), (10.35, 1.27, zc + (0.35 if zc < 1 else -0.35)), 0.028, dark, seg=6, name='tr_brace'); U(o, STEELD); A(o)
    o = rod((9.5, 0.82, 0.47), (9.5, 0.82, 2.13), 0.032, dark, seg=6, name='tr_cross'); U(o, STEELD); A(o)
    o = rod((9.5, 1.05, 0.47), (9.5, 1.05, 2.13), 0.018, steel, seg=6, name='tr_shaft'); S(o, DSTEEL)
    P.remove(o) if False else None
    o = box((0.15, 0.2, 0.1), (9.5, 1.05, 2.32), dark, name='tr_gearbox'); U(o, STEELD); A(o)
    S(rod((9.5, 0.98, 2.37), (9.5, 0.98, 2.48), 0.016, steel, seg=6, name='tr_crank'), DSTEEL)
    S(rod((9.5, 0.98, 2.48), (9.12, 0.98, 2.48), 0.016, steel, seg=6, name='tr_crank2'), DSTEEL)
    o = cyl(0.024, 0.12, (9.12, 0.92, 2.48), dark, axis='y', seg=6, name='tr_grip'); U(o, RUB); A(o)
    o = box((1.4, 0.05, 1.8), (11.7, 1.275, TWD / 2), dark, name='tr_coupler'); U(o, STEELD); A(o)
    S(cyl(0.045, 0.1, (11.6, 1.2, TWD / 2), steel, axis='y', seg=8, name='tr_kingpin'), DSTEEL)
    # ---------------- the rear: underride bumper (conspicuity tape on it), mud flaps
    S(prism('tr_bumper', chrect(0.08, 0.54, 0.06, 0.06, 0.012), 0.3, TWD - 0.3, 'z', steel, caps=(True, True)), DSTEEL)
    o = mesh_from('tr_btape', [(0.018, 0.5, 0.32), (0.018, 0.5, TWD - 0.32), (0.018, 0.58, TWD - 0.32), (0.018, 0.58, 0.32)], [(0, 1, 2, 3)], body, out=(-1, 0, 0))
    uv_proj(o, {'-x': (TAPE, (0, 0.5, 0.32), (0, 0, 1), (0, 1, 0), 0.35, 0.08)}); A(o)
    for zc in (0.5, TWD - 0.5):
        S(prism('tr_strut', chrect(0.09, zc, 0.04, 0.035, 0.008), 0.6, Y0, 'y', steel), DSTEEL)
    for zc in (0.3, TWD - 0.3):
        o = box((0.012, 0.62, 0.44), (AX[0] - 0.6, 0.6, zc), dark, name='tr_flap'); A(o)
        uv_proj(o, {'-x': (FLAP, (0, 0.29, zc - 0.22), (0, 0, 1), (0, 1, 0), 0.44, 0.62), '+x': (FLAP, (0, 0.29, zc - 0.22), (0, 0, 1), (0, 1, 0), 0.44, 0.62)}, default=(RUB, (0, 0, 0), (1, 0, 0), (0, 1, 0), 9, 9))
        zr_ = 0.6 if zc < 1 else 2.0  # a bar from the slider rail out over the flap
        o = box((0.18, 0.04, abs(zc - zr_) + 0.3), (AX[0] - 0.51, 0.93, (zc + zr_) / 2 + (-0.08 if zc < 1 else 0.08)), dark, name='tr_flapbar'); U(o, STEELD); A(o)
    # ---------------- wheels: four sets of duals (the boxes' 1.0 m tyres, 0.4 wide a side)
    for ax_ in AX:
        for (zi, zo) in ((0.5, 0.1), (2.1, 2.5)):
            sg = 1 if zo > zi else -1  # outward
            prof = [(0.44, zi), (0.5, zi + sg * 0.04), (0.5, zo - sg * 0.04), (0.488, zo - sg * 0.015), (0.44, zo), (0.3, zo)]
            ty_ = lathe(prof, (ax_, 0.5, 0), dark, seg=14, axis='z', name='tr_tyre', cap=False)
            apply_mods(ty_)
            uv_tread(ty_, TREAD, ax_, 0.5, min(zi, zo) + 0.0, max(zi, zo), sel=lambda n: abs(n.z) < 0.7)
            uv_planar_xy(ty_, SIDEW, ax_, 0.5, 0.5, sel=lambda n: abs(n.z) >= 0.7)
            A(ty_)
            rim = lathe([(0.3, zo), (0.27, zo - sg * 0.012), (0.13, zo - sg * 0.012), (0.06, zo + sg * 0.012), (0.0, zo + sg * 0.012)], (ax_, 0.5, 0), steel, seg=10, axis='z', name='tr_rim', cap=False)
            apply_mods(rim); uv_planar_xy(rim, RIM, ax_, 0.5, 0.3); A(rim)
            inner = lathe([(0.445, zi - sg * 0.006), (0.0, zi - sg * 0.006)], (ax_, 0.5, 0), dark, seg=10, axis='z', name='tr_inner', cap=False)
            U(inner, RUB); A(inner)
    for o, rect_ in steelp: uv_fill(o, rect_)
    for o in P: weld(o); fix_zero_uv(o)
    # ---------------- lod1: the box with pictures, the wheels as octagons, chassis + legs as blocks (2 materials)
    lb = box((TL, Y1 - Y0, TWD), (TL / 2, (Y0 + Y1) / 2, TWD / 2), body, name='tr_farbox')
    uv_proj(lb, {'+z': (L1S, (0, Y0, 0), (1, 0, 0), (0, 1, 0), TL, Y1 - Y0), '-z': (L1S, (TL, Y0, 0), (-1, 0, 0), (0, 1, 0), TL, Y1 - Y0),
                 '-x': (L1R, (0, Y0, 0), (0, 0, 1), (0, 1, 0), TWD, Y1 - Y0), '+x': (L1F, (0, Y0, TWD), (0, 0, -1), (0, 1, 0), TWD, Y1 - Y0),
                 '+y': (L1T, (0, 0, 0), (1, 0, 0), (0, 0, 1), TL, TWD), '-y': (L1T, (0, 0, 0), (1, 0, 0), (0, 0, 1), TL, TWD)})
    far = [lb]
    for ax_ in AX:
        for (z0, z1) in ((0.1, 0.5), (2.1, 2.5)):
            w = lathe([(0.0, z0), (0.5, z0), (0.5, z1), (0.0, z1)], (ax_, 0.5, 0), dark, seg=8, axis='z', name='tr_farwheel', cap=False)
            apply_mods(w); uv_tread(w, TREAD, ax_, 0.5, z0, z1, sel=lambda n: abs(n.z) < 0.7); uv_planar_xy(w, WHEEL1, ax_, 0.5, 0.5, sel=lambda n: abs(n.z) >= 0.7)
            far.append(w)
    for (sz, pos, nm) in (((11.9, 0.35, 1.5), (6.35, 1.125, 1.3), 'tr_farchassis'), ((AX[1] - AX[0] + 1.15, 0.5, 1.6), ((AX[0] + AX[1]) / 2 + 0.025, 0.7, 1.3), 'tr_farslider'),
                          ((0.14, Y0, 0.14), (9.5, Y0 / 2, 0.4), 'tr_farleg'), ((0.14, Y0, 0.14), (9.5, Y0 / 2, 2.2), 'tr_farleg')):
        o = box(sz, pos, dark, name=nm); U(o, STEELD); far.append(o)
    rects = dict(SIDE=SIDE, RAIL=RAIL, ROOF=ROOF, PLAIN=PLAIN, MARKA=MARKA, MARKR=MARKR, TAPE=TAPE, CLEAR=CLEAR, TREAD=TREAD, SIDEW=SIDEW,
                 STEELD=STEELD, RUB=RUB, UNDER=UNDER, FLAP=FLAP, WHEEL1=WHEEL1, RIM=RIM, GALV=GALV, CHROME=CHROME, DSTEEL=DSTEEL)
    return P, far, dict(body=body, dark=dark, steel=steel, R=rects)


def semi_boxes(cab=True):
    """shared/map.js semiBoxes(L, livery, cab), in its own frame (the trailer's back at z 0, the cab toward +z)"""
    out = []
    def A(x0, y0, z0, x1, y1, z1, m, st=False): out.append(((x0, y0, z0), (x1, y1, z1), m, st))
    A(-1.3, 1.3, 0, 1.3, 4.1, 12.5, 'truckbox')
    A(-1.33, 1.5, 1, -1.3, 3.9, 11.5, 'adtruck', True); A(1.3, 1.5, 1, 1.33, 3.9, 11.5, 'adtruck', True)
    A(-1.25, 1.25, -0.05, 1.25, 1.35, 0, 'tail')
    for wz in (1.2, 2.4):
        for a, b in ((-1.2, -0.8), (0.8, 1.2)): A(a, 0, wz - 0.5, b, 1.0, wz + 0.5, 'tire')
    A(-1.0, 0.95, 0.6, 1.0, 1.3, 3.0, 'metal')
    for px in (-1.0, 0.8): A(px, 0, 9.4, px + 0.2, 1.3, 9.6, 'metal')
    if not cab: return out
    A(-1.25, 0.6, 12.7, 1.25, 1.08, 16.6, 'metal')
    A(-1.25, 1.1, 13.6, 1.25, 3.3, 16.4, 'carred'); A(-1.15, 2.2, 16.4, 1.15, 3.1, 16.45, 'glass')
    A(-1.2, 1.1, 16.4, 1.2, 2.2, 16.9, 'carred'); A(-1.0, 1.4, 16.9, 1.0, 2.0, 16.95, 'chrome')
    A(-1.27, 2.3, 14.2, -1.25, 3.0, 15.9, 'glass'); A(1.25, 2.3, 14.2, 1.27, 3.0, 15.9, 'glass')
    for px in (-1.1, 0.95): A(px, 3.3, 13.6, px + 0.15, 4.6, 13.75, 'chrome')
    for wz in (13.4, 16):
        for a, b in ((-1.3, -0.85), (0.85, 1.3)): A(a, 0, wz - 0.55, b, 1.1, wz + 0.55, 'tire')
    A(-1.25, 1.6, 16.95, -0.8, 1.9, 17, 'light'); A(0.8, 1.6, 16.95, 1.25, 1.9, 17, 'light')
    return out


class _UVCells:
    """a yard atlas (its rects in UV units) as an Atlas-like thing for uvmap"""
    def __init__(s, rects):
        s.W = s.H = 1024
        s.R = {k: ((r[0] * 1024, (1 - r[3]) * 1024, (r[2] - r[0]) * 1024, (r[3] - r[1]) * 1024), None, None) for k, r in rects.items()}


def yard_tyre(name, X, zi, zo, r, M, P):
    """make_yard's trailer tyre (tread + sidewall pictures, the steel disc, the inner face), axle across at (X, r)"""
    R_ = M['R']; sg = 1 if zo > zi else -1
    prof = [(r * 0.88, zi), (r, zi + sg * 0.04), (r, zo - sg * 0.04), (r * 0.976, zo - sg * 0.015), (r * 0.88, zo), (r * 0.6, zo)]
    ty_ = lathe(prof, (X, r, 0), M['dark'], seg=14, axis='z', name=name + '_tyre', cap=False); apply_mods(ty_)
    Y.uv_tread(ty_, R_['TREAD'], X, r, min(zi, zo), max(zi, zo), sel=lambda n: abs(n.z) < 0.7)
    Y.uv_planar_xy(ty_, R_['SIDEW'], X, r, r, sel=lambda n: abs(n.z) >= 0.7)
    rim = lathe([(r * 0.6, zo), (r * 0.54, zo - sg * 0.012), (r * 0.26, zo - sg * 0.012), (r * 0.12, zo + sg * 0.012), (0.0, zo + sg * 0.012)], (X, r, 0), M['steel'], seg=10, axis='z', name=name + '_rim', cap=False)
    apply_mods(rim); Y.uv_planar_xy(rim, R_['RIM'], X, r, r * 0.6)
    inner = lathe([(r * 0.89, zi - sg * 0.006), (0.0, zi - sg * 0.006)], (X, r, 0), M['dark'], seg=10, axis='z', name=name + '_inner', cap=False)
    Y.uv_fill(inner, R_['RUB'])
    for o in (ty_, rim, inner): Y.weld(o); Y.fix_zero_uv(o); P.append(o)


def build_semitrailer():
    fid = 'p_semitrailer'
    P, far, M = yard_trailer((1.2, 2.4), glow_mat(0xff2a2a))
    B = Build(fid, [], [])
    for o in P: B.keep(o)
    for o in far: B.keep(o, far=True)
    to_frame(B.l0 + B.l1, -math.pi / 2, (1.3, 0.0, 0.0))  # (the yard's frame -> this one: back at z 0, along +z, across x)
    return finish(B, {'id': 'semitrailer', 'lod': 80, 'tint': False}, 0.0, (0.0, 0.0, 0.0), semi_boxes(False), [], ())


def semi_paint(PA):
    red, ink, chrome = 0xd81e30, 0x1a1016, 0xdde2ea
    for k, sd in (('L', 51), ('R', 52), ('F', 53), ('B', 54), ('T', 55)): PA.fill(k, red, var=0.03, seed=sd)
    PA.fill('U', 0x2a2a2e, var=0.05, seed=56)
    for k, col in (('K', 0x141418), ('D', 0x0e0e10), ('W', 0xf0f0f2), ('Gl', 0x1c2c44)): PA.fill(k, col, var=0.03, seed=57)
    for k in ('L', 'R'):
        PA.mul(k, lambda w: 1 - 0.2 * np.clip((1.5 - w['y']) / 0.4, 0, 1))
        PA.line(k, [(0, 1.15, 14.1), (0, 3.05, 14.1)], 0x6a0a14, 1.0); PA.line(k, [(0, 1.15, 16.0), (0, 3.05, 16.0)], 0x6a0a14, 1.0)  # the door
        PA.line(k, [(0, 3.05, 14.1), (0, 3.05, 16.0)], 0x6a0a14, 1.0)
        PA.rect(k, (0, 2.25, 15.75), (0, 2.31, 15.9), 0x2a0408)  # the handle's recess
        PA.rect(k, (0, 1.88, 13.6), (0, 1.96, 16.9), 0xf0f0f2)  # a white pinstripe, the name on the door
        PA.text(k, (0, 1.62, 15.05), 'JANK HAUL', 1, 0xffffff, shadow=0x5a0810)
        PA.text(k, (0, 1.32, 15.05), 'DOT 420 69', 1, 0xf0d0d4)
    PA.rect('F', (-1.3, 1.38, 0), (1.3, 2.02, 0), 0x0c0c0e)  # behind the grille
    PA.text('F', (0, 2.78, 0), 'JANK', 1, 0xffffff)


def build_semi():
    fid = 'p_semi'
    gt = glow_mat(0xff2a2a); gh = glow_mat(0xfff2b0)
    TP, TF, M = yard_trailer((1.2, 2.4), gt)
    # the tractor's wheels, made like the trailer's (in the yard frame: x along -> our z, z across = 1.3 - our x)
    for X, w, nm in ((16.0, 0.32, 'tf'), (13.4, 0.44, 'tr')):
        yard_tyre(nm + 'l', X, w, 0.0, 0.55, M, TP)
        yard_tyre(nm + 'r', X, 2.6 - w, 2.6, 0.55, M, TP)
    for X in (13.4, 16.0):
        for (z0, z1) in ((0.0, 0.32), (2.28, 2.6)):
            o = lathe([(0.0, z0), (0.55, z0), (0.55, z1), (0.0, z1)], (X, 0.55, 0), M['dark'], seg=8, axis='z', name='sm_farwheel', cap=False)  # (a corner on the ground, like the trailer's)
            apply_mods(o); Y.uv_tread(o, M['R']['TREAD'], X, 0.55, z0, z1, sel=lambda n: abs(n.z) < 0.7)
            Y.uv_planar_xy(o, M['R']['WHEEL1'], X, 0.55, 0.55, sel=lambda n: abs(n.z) >= 0.7); TF.append(o)
    PA = Atlas('semi_paint_t', 256, 256, 0xd81e30)
    lo, hi = (-1.3, 0.0, 11.2), (1.3, 4.62, 17.05)
    PA.view('L', (0, 0, 256, 96), 'L', lo, hi); PA.view('R', (0, 96, 256, 96), 'R', lo, hi)
    PA.view('T', (0, 192, 128, 64), 'T', lo, hi); PA.view('F', (128, 192, 64, 64), 'F', lo, hi)
    PA.view('B', (192, 192, 32, 32), 'B', lo, hi); PA.view('U', (192, 224, 32, 32), 'U', lo, hi)
    for i, k in enumerate(('K', 'D', 'W', 'Gl')): PA.cell(k, (224 + 16 * (i % 2), 192 + 16 * (i // 2), 16, 16))
    paint = mat('paint', 0xffffff, rough=0.24, metal=0.1, clearcoat=1.0, tex=PA.img)
    gimg = bpy.data.images.new('glass_semi', 4, 4, alpha=False)
    glass = T.mat_glass('glass', gimg)
    YB, YD, YS = _UVCells(M['R']), _UVCells(M['R']), _UVCells(M['R'])
    B = Build(fid, [paint, glass, gh, M['body'], M['dark'], M['steel']], [PA, PA, PA, YB, YD, YS])
    P_, GL, GH, BO, DK, ST = 0, 1, 2, 3, 4, 5
    for o in TP: B.keep(o)
    for o in TF: B.keep(o, far=True)
    to_frame(B.l0 + B.l1, -math.pi / 2, (1.3, 0.0, 0.0))
    nt = len(B.l0)
    body = lambda n, c: (P_, kind_of(n))
    chrome, steel, black, plain = (ST, 'CHROME'), (ST, 'DSTEEL'), (DK, 'RUB'), (DK, 'STEELD')
    # ---------------- chassis: frame rails out under the trailer, the fifth wheel on its kingpin, the deck, the ends
    for s in (1, -1): B.box((s * 0.42, 0.68, 11.2), (s * 0.54, 1.0, 16.62), plain, k='rail')
    B.add(cyl(0.56, 0.07, (0, 1.205, 11.7), None, axis='y', seg=14, name=B.nm('fifth')), steel)
    for s in (1, -1): B.box((s * 0.3, 0.995, 11.35), (s * 0.58, 1.18, 12.05), plain, k='fwmount')
    B.box((-0.56, 0.995, 12.55), (0.56, 1.09, 13.598), (ST, 'GALV'), k='deck')
    for az in (13.4, 16.0): B.add(cyl(0.07, 2.62, (0, 0.55, az), None, axis='x', seg=8, name=B.nm('axle')), plain)  # (through the hubs)
    B.add(ball(0.18, (0, 0.55, 13.4), None, seg=8, rings=5, name=B.nm('diff')), plain)
    B.box((-0.9, 0.65, 12.7), (0.9, 1.05, 12.74), plain, k='xmember')
    B.box((-1.2, 0.62, 16.6), (1.2, 1.102, 16.655), black, k='airdam')
    for s in (1, -1): B.box((s * 0.55, 0.7, 16.62), (s * 0.75, 0.82, 16.7), (BO, 'MARKR'), k='towhook')
    # fuel tanks (polished, strapped, a step plate on top), battery box under the cab's back corner
    for s in (1, -1):
        B.add(cyl(0.235, 1.44, (s * 1.012, 0.84, 14.7), None, axis='z', seg=14, name=B.nm('tank')), chrome)
        for z_ in (14.2, 15.2): B.box((s * 0.76, 0.598, z_), (s * 1.252, 1.082, z_ + 0.04), plain, k='strap')
        B.box((s * 0.86, 1.074, 14.3), (s * 1.24, 1.094, 15.1), (ST, 'GALV'), k='tstep')
        # fenders: quarter ones over the steer wheels, halves over the drives, mud flaps behind
        pts = [(s * 1.075, 0.55 + 0.6 * math.sin(math.radians(a)), 16.0 + 0.6 * math.cos(math.radians(a))) for a in range(20, 161, 20)]
        B.add(sweep(pts, 0.24, None, seg=6, name=B.nm('fender'), squash=(0.12, 1.0)), black)
        pts = [(s * 1.075, 0.55 + 0.6 * math.sin(math.radians(a)), 13.4 + 0.6 * math.cos(math.radians(a))) for a in range(40, 141, 20)]
        B.add(sweep(pts, 0.24, None, seg=6, name=B.nm('fender'), squash=(0.12, 1.0)), black)
        B.box((s * 0.84, 0.18, 12.76), (s * 1.3, 0.86, 12.774), (DK, 'FLAP'), k='flap')
        B.box((s * 0.52, 0.84, 12.75), (s * 1.28, 0.9, 12.79), plain, k='flapbar')
    # ---------------- the cab: a lofted day cab (rolled roof edges, round corners), the nose, the glass, the trim
    CZ0, CZ1 = 13.6, 16.4
    def plan(z, r0=0.09, r1=0.14):
        if z < CZ0 + r0: return 1.25 - r0 + math.sqrt(max(r0 * r0 - (CZ0 + r0 - z) ** 2, 0))
        if z > CZ1 - r1: return 1.25 - r1 + math.sqrt(max(r1 * r1 - (z - (CZ1 - r1)) ** 2, 0))
        return 1.25
    def chalf(z):
        H = plan(z)
        return [(H - 0.03, 1.1), (H, 1.14), (H, 3.04), (H - 0.045, 3.2), (H - 0.16, 3.28), (0.62, 3.3), (0.0, 3.3)]
    zs = sorted(set([CZ0, CZ0 + 0.02, CZ0 + 0.045, CZ0 + 0.07, CZ0 + 0.09] + [CZ0 + 0.09 + k * (CZ1 - CZ0 - 0.23) / 8 for k in range(9)] + [CZ1 - 0.14, CZ1 - 0.1, CZ1 - 0.065, CZ1 - 0.03, CZ1]))
    B.add(T.zloft(B.nm('cab'), zs, chalf), body)
    def nhalf(z, r=0.12):
        H = 1.2 if z < 16.9 - r else (1.2 - r) + math.sqrt(max(r * r - (z - (16.9 - r)) ** 2, 0))
        t = 2.2 if z < 16.9 - 0.1 else 2.1 + math.sqrt(max(0.01 - (z - 16.8) ** 2, 0))
        return [(H - 0.02, 1.102), (H, 1.13), (H, t - 0.08), (H - 0.05, t - 0.01), (0.0, t)]
    B.add(T.zloft(B.nm('nose'), [16.38, 16.6, 16.78, 16.82, 16.86, 16.885, 16.9], nhalf), body)
    # windscreen (the glass box on the cab's face) in its gasket, a divider, wipers, the visor + roof lights
    B.box((-1.148, 2.202, 16.402), (1.148, 3.098, 16.448), (GL, 'Gl'), k='screen')
    for o in ring_frame(B.nm('sgask'), -1.11, 1.11, 2.24, 3.06, 0.04, 16.39, 16.452, 'z'): B.add(o, black)
    B.box((-0.02, 2.24, 16.396), (0.02, 3.06, 16.456), black, k='divider')
    for s in (1, -1):
        B.rod((s * 0.08, 2.3, 16.458), (s * 0.95, 2.55, 16.458), 0.011, black, seg=4, k='wiper')
    B.box((-1.18, 3.14, 16.3), (1.18, 3.2, 16.62), black, bev=0.01, k='visor')
    for x in (-0.6, -0.3, 0.0, 0.3, 0.6): B.box((x - 0.05, 3.2, 16.55), (x + 0.05, 3.235, 16.6), (BO, 'MARKA'), k='roofmk')
    # side windows on the doors (the glass boxes), a vent divider, mirrors, steps, handles, grab rails
    for s in (1, -1):
        B.box((s * 1.249, 2.302, 14.202), (s * 1.268, 2.998, 15.898), (GL, 'Gl'), k='sideglass')
        for o in ring_frame(B.nm('wgask'), 14.24, 15.86, 2.34, 2.96, 0.035, s * 1.245, s * 1.272, 'x'): B.add(o, black)
        B.box((s * 1.244, 2.34, 15.55), (s * 1.273, 2.96, 15.585), black, k='vent')
        B.box((s * 1.25, 2.26, 15.7), (s * 1.275, 2.3, 15.86), chrome, k='handle')
        B.rod((s * 1.27, 1.4, 14.12), (s * 1.27, 2.6, 14.12), 0.018, chrome, seg=6, k='grab')
        for y in (1.42, 2.58): B.rod((s * 1.235, y, 14.12), (s * 1.27, y, 14.12), 0.012, chrome, seg=4, k='grabb')
        B.rod((s * 1.25, 2.8, 16.3), (s * 1.48, 2.82, 16.22), 0.016, chrome, seg=6, k='marm')
        B.rod((s * 1.25, 2.3, 16.3), (s * 1.48, 2.28, 16.22), 0.016, chrome, seg=6, k='marm')
        B.box((s * 1.44, 2.22, 16.12), (s * 1.52, 2.86, 16.24), black, bev=0.015, k='mirror')
        B.box((s * 1.45, 2.24, 16.11), (s * 1.51, 2.84, 16.121), chrome, k='mglass')
        # the nose: headlamps (the 'light' boxes) in chrome pods, indicators, the bumper, the grille + its bars
        B.box((s * 0.78, 1.58, 16.88), (s * 1.255, 1.92, 16.96), chrome, bev=0.02, k='hpod')
        B.box((s * 0.81, 1.61, 16.95), (s * 1.24, 1.89, 16.998), (GH, 'K'), bev=0.008, k='head')
        B.box((s * 0.9, 1.45, 16.86), (s * 1.18, 1.55, 16.936), (BO, 'MARKA'), k='ind')
        B.box((s * 1.19, 1.95, 16.6), (s * 1.215, 2.05, 16.75), (BO, 'MARKA'), k='sidemk')
    B.box((-1.24, 1.096, 16.84), (1.24, 1.38, 17.0), chrome, bev=0.03, seg=2, k='bumper')
    B.box((-1.02, 1.38, 16.89), (1.02, 2.02, 16.93), chrome, bev=0.015, k='gframe')
    B.box((-0.96, 1.43, 16.925), (0.96, 1.97, 16.932), black, k='gback')
    for k_ in range(13): x = -0.9 + k_ * 0.15; B.box((x - 0.022, 1.44, 16.93), (x + 0.022, 1.96, 16.95), chrome, k='gbar')
    B.box((-0.25, 1.98, 16.92), (0.25, 2.03, 16.955), (BO, 'MARKA'), k='badge')
    # behind the cab: the stacks (chrome, heat shields), the back window, air lines + the light cord to the trailer
    for s in (1, -1):
        x = s * 1.025
        B.rod((x, 1.0, 13.6), (x, 4.52, 13.6), 0.07, chrome, seg=10, k='stack')  # (on the cab's back, half in its box)
        B.add(cyl(0.088, 1.2, (x, 2.8, 13.6), None, axis='y', seg=10, name=B.nm('shield')), (ST, 'GALV'))
        B.rod((x, 4.52, 13.6), (x, 4.6, 13.585), 0.07, chrome, seg=10, k='stacktip')
        for y in (1.9, 3.15): B.box((s * 0.9, y, 13.5), (s * 0.97, y + 0.06, 13.62), plain, k='stackbr')
    B.box((-0.55, 2.4, 13.594), (0.55, 2.9, 13.602), (GL, 'Gl'), k='backglass')
    for x, col in ((0.25, (BO, 'MARKR')), (-0.25, (BO, 'MARKA')), (0.0, black)):
        pts = [(x * 0.6, 1.75, 13.598)] + [(x * (0.6 + 0.4 * t), 1.75 - 0.25 * math.sin(math.pi * t) - 0.1 * t, 13.598 - 1.07 * t) for t in (0.25, 0.5, 0.75)] + [(x * 1.0 + (0.02 if x == 0 else 0), 1.64, 12.52)]
        B.add(sweep(pts, 0.016, None, seg=6, name=B.nm('airline')), col)
    # ---------------- far LOD: the cab and nose as blocks, glass in the paint, the stacks
    def far(n, c):
        k = kind_of(n)
        if 2.25 < c.y < 3.05 and (k in ('L', 'R') and 14.2 < c.z < 15.9 or k == 'F' and c.z > 16.3): return (P_, 'Gl')
        return (P_, k)
    B.box((-1.25, 1.1, 13.6), (1.25, 3.3, 16.4), far, far=True, k='l1cab')
    B.box((-1.15, 2.203, 16.39), (1.15, 3.1, 16.45), (P_, 'Gl'), far=True, k='l1screen')
    B.box((-1.2, 1.102, 16.395), (1.2, 2.2, 16.9), far, far=True, k='l1nose')
    B.box((-1.24, 1.098, 16.88), (1.24, 1.38, 17.0), chrome, far=True, k='l1bump')
    B.box((-1.25, 0.6, 12.7), (1.25, 1.08, 16.6), plain, far=True, k='l1chassis')
    for s in (1, -1): B.box((s * 0.955, 1.07, 13.53), (s * 1.095, 4.6, 13.67), chrome, far=True, k='l1stack')
    semi_paint(PA)
    PA.write()
    T.glass_paint(_CabGlass('semi', B.l0[nt:], glass, gimg, dict(belt=2.3, top=3.0, rows=[(15.05, 2.95, 0.55)], dash=2.45, wheel=(0.55, 2.55, 0.22, 0.06), far=0x26354a)))
    ok = tuple(fid + '_' + k for k in ('fifth', 'fwmount', 'rail', 'airline', 'stack', 'shield', 'stacktip', 'stackbr', 'marm', 'mirror', 'mglass', 'grab', 'grabb', 'flap', 'flapbar', 'fender'))
    return finish(B, {'id': 'semi', 'lod': 80, 'tint': False}, 0.0, (0.0, 0.0, 0.0), semi_boxes(True), [], ok)


# ------------------------------------------------------------ driver
BUILDERS = {'transitbus': build_transitbus, 'boxtruck': build_boxtruck, 'semi': build_semi, 'semitrailer': build_semitrailer}
EXPO = {'transitbus': -0.5, 'boxtruck': -0.6, 'semi': -0.9, 'semitrailer': -1.2}
VIEWS = {  # close-ups (prop frame, game coords: eye, target, lens), the inside ones at a player's eye
    'transitbus': [('front', (17, 2.4, -4.5), (9, 1.4, 1.3), 30), ('door', (10.5, 1.7, 6.5), (10.3, 1.4, 2.0), 30),
                   ('back', (-5.5, 2.6, 5.5), (1, 1.5, 1.3), 30), ('in_back', (10.6, 2.5, 1.7), (0.5, 1.6, 1.0), 40),
                   ('in_front', (2.0, 2.5, 1.9), (11.5, 1.9, 0.9), 40), ('in_door', (8.6, 2.5, 0.9), (10.6, 1.3, 2.6), 45),
                   ('far0', (55, 30, -60), (6, 1.5, 1.3), 50), ('far1', (55, 30, -60), (6, 1.5, 1.3), 50)],
    'boxtruck': [('front', (15.5, 2.6, -4.0), (8.0, 1.6, 1.25), 30), ('back', (-5.2, 2.4, 4.8), (1.0, 2.0, 1.25), 30),
                 ('side', (5.0, 1.7, -7.5), (5.0, 1.8, 1.25), 34), ('in_back', (0.8, 2.7, 1.25), (7.2, 2.0, 1.25), 45),
                 ('in_front', (6.6, 2.7, 1.6), (0.0, 2.6, 0.9), 45), ('wheel', (2.8, 0.9, -2.6), (1.4, 0.6, 0.2), 35),
                 ('far0', (45, 25, -50), (5, 1.8, 1.25), 50), ('far1', (45, 25, -50), (5, 1.8, 1.25), 50)],
    'semi': [('front', (6.5, 2.6, 24.0), (0.0, 2.0, 15.0), 32), ('side', (-9.5, 2.0, 14.0), (0.0, 1.8, 13.5), 32),
             ('gap', (-5.0, 3.2, 10.5), (0.0, 1.6, 13.0), 32), ('rear', (-4.5, 2.4, -6.5), (0.0, 1.6, 2.0), 30),
             ('far0', (-50, 30, 60), (0, 2, 8.5), 50), ('far1', (-50, 30, 60), (0, 2, 8.5), 50)],
    'semitrailer': [('rear', (-4.5, 2.4, -6.5), (0.0, 1.6, 2.0), 30), ('side', (-9.0, 1.4, 6.0), (0.0, 1.4, 5.0), 32),
                    ('far0', (-45, 25, 50), (0, 2, 6.2), 50), ('far1', (-45, 25, 50), (0, 2, 6.2), 50)],
}


def main():
    only = arg('only')
    ids = only.split(',') if isinstance(only, str) else list(BUILDERS)
    for k in ids:
        lib.reset(); lib._mats.clear()
        root = BUILDERS[k]()
        if not arg('no-export'): lib.export(root, root.name)
        if not arg('no-sheet'): Y.sheet4(root, root.name, exposure=EXPO.get(k, 0.0))
        if isinstance(arg('views'), str) and k in VIEWS:
            Y.SCRATCH = arg('views')
            Y.closeups(root, root.name, VIEWS[k])


main()
