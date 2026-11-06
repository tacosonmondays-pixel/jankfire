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
T.TEX_TRIM = (256, 128)
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
    'louvre': (128, 64, 32, 32, 0x18181c, 0.55, 0.2),   # engine louvres
    'slats': (160, 64, 32, 32, 0xc8ccd2, 0.4, 0.5),     # roller door slats
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
    for y in range(32): lv[y, :] = hexrgb(0x2c2c32) if y % 4 == 0 else (hexrgb(0x08080a) if y % 4 == 3 else hexrgb(0x18181c))
    sl = cell('slats')
    for y in range(32): sl[y, :] = hexrgb(0xd4d8de) * (0.96 + 0.05 * r.random()) if y % 4 else hexrgb(0x8c9098)
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
    j0 = join(B.l0, fid[2:] + '_lod0'); T.weld(j0, 1e-6)
    j1 = join(B.l1, fid[2:] + '_lod1') if B.l1 else None
    if j1: T.weld(j1, 1e-6)
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
    if arg('zfdebug'): zf_where(j0)
    if arg('qa'):
        Y.qa([j0], fid + ':lod0', eps=0.0008, tol=0.003)
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


# ------------------------------------------------------------ driver
BUILDERS = {'transitbus': build_transitbus}
EXPO = {'transitbus': -0.5, 'boxtruck': -0.6, 'semi': -0.9, 'semitrailer': -1.2}
VIEWS = {  # close-ups (prop frame, game coords: eye, target, lens), the inside ones at a player's eye
    'transitbus': [('front', (17, 2.4, -4.5), (9, 1.4, 1.3), 30), ('door', (10.5, 1.7, 6.5), (10.3, 1.4, 2.0), 30),
                   ('back', (-5.5, 2.6, 5.5), (1, 1.5, 1.3), 30), ('in_back', (10.6, 2.5, 1.7), (0.5, 1.6, 1.0), 40),
                   ('in_front', (2.0, 2.5, 1.9), (11.5, 1.9, 0.9), 40), ('in_door', (8.6, 2.5, 0.9), (10.6, 1.3, 2.6), 45),
                   ('far0', (55, 30, -60), (6, 1.5, 1.3), 50), ('far1', (55, 30, -60), (6, 1.5, 1.3), 50)],
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
