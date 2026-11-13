# The Cathedral of Shareholder Value (shared/jankburg.js cathedral(), Corp Hill, facing the plaza): p_jb_cathedral.
# A corporate megachurch in limestone ashlar: walls built from the map's own wall boxes (every door, window and the rose
# window exactly where the boxes leave them open), pilasters between the tall windows with pinnacles over the roof
# line, moulded surrounds and pointed hood moulds round the windows (the stock-ticker stained glass is the map's
# pictures), a gothic portal with clustered jambs and a gold ☺ in the tympanum, the rose window's ring; inside, a
# marble floor with a pink aisle runner, the ticker neon round the nave, wooden pews with carved ends, a gold altar,
# the organ: seven server racks with blinking LEDs under chrome pipes with glowing mouths. The bell tower: ashlar
# with a ☺ clock on three faces, the belfry's four marble columns under pointed arches, a real bell on its yoke, a gold
# cap and a spire with a weathervane.
# Frame: the cathedral's own (x -12.3..12.3 across, the front with the steps at -z, y up), as cathedral()'s local()
# builds it. Look only: the boxes stay the collision; the pictures stay the map's.
# needs tools/blender/jankburg/cathedral.json (the boxes in this frame): node tools/blender/jankburg/dump_cathedral.mjs
# run: blender52 -b --python tools/blender/jankburg/make_jb_cathedral.py -- [--qa] [--qa-parts] [--no-sheet] [--no-export]
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Vector, Matrix
import jbkit as K
from jbkit import ARGV, Atlas, boxa, fill_uv, mesh, noise, concrete
import lib
from lib import mat, text_px, hexrgb, px_disc, rod, _image, uv_box, apply_mods

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'cathedral.json')))
BOX = [b for b in D['boxes'] if b['k'] == 'B']
rng = np.random.default_rng(1720)
TX, TZ = 7.5, -13.5  # the bell tower's middle


# ------------------------------------------------------------ textures (tiling ones get their own material)
def ashlar(S=64):
    v = np.zeros((S, S, 3), np.float32); r = np.random.default_rng(5)
    base = hexrgb(0xd8d0dc)
    for row in range(4):
        off = 8 * (row % 2)
        for col in range(-1, 3):
            x0, x1 = col * 32 + off, col * 32 + off + 32
            tint = 0.88 + 0.16 * r.random()
            for x in range(max(0, x0), min(S, x1)): v[row * 16:row * 16 + 16, x] = base * tint
    v *= (0.92 + 0.1 * noise(S, S, r, 4, 0.5)[..., None])
    v[::16] = hexrgb(0x9a90a2); v[:, 0] *= 1.0
    for row in range(4):
        off = 8 * (row % 2)
        for col in range(3): x = (col * 32 + off) % S; v[row * 16:row * 16 + 16, x] = hexrgb(0x9a90a2)
    m = r.random((S, S)) < 0.03; v[m] *= 0.8
    return _image('jbc_ashlar', np.clip(v, 0, 1))


def marble_tex(S=64):
    y, x = np.mgrid[0:S, 0:S] / S * 2 * math.pi
    vv = np.sin(x + 2.2 * np.sin(y + 1.3 * np.sin(2 * x)) + y)
    c = hexrgb(0xf4eef4)[None, None] * (0.95 + 0.05 * rng.random((S, S, 1)))
    vein = np.clip(1 - np.abs(vv) * 7, 0, 1)[..., None]
    c = c * (1 - 0.4 * vein) + hexrgb(0xb98fd8) * 0.4 * vein
    c[::32] *= 0.85; c[:, ::32] *= 0.85  # slab joints
    return _image('jbc_marble', np.clip(c, 0, 1))


def wood_tex(S=32):
    y, x = np.mgrid[0:S, 0:S]
    g = 0.5 + 0.5 * np.sin(y * 0.9 + 2 * np.sin(x * 0.2))
    c = hexrgb(0x8a4a24)[None, None] * (0.8 + 0.25 * g[..., None]); c[::8] *= 0.8
    return _image('jbc_wood', np.clip(c, 0, 1))


def roof_tex(S=32):
    c = hexrgb(0x4a8a7a)[None, None] * (0.85 + 0.2 * noise(S, S, rng, 4, 0.5)[..., None])  # weathered copper
    c[::8] = hexrgb(0x36685c); return _image('jbc_roof', np.clip(c, 0, 1))


A = Atlas('jbc_atlas', 256, 256, 0xd8d0dc)
for key, x, y, c in (('gold', 0, 0, 0xe8b83a), ('metal', 16, 0, 0x5a5f6e), ('dark', 32, 0, 0x24222c), ('white', 48, 0, 0xeeeeee),
                     ('pink', 64, 0, 0xff4fd8), ('bronze', 80, 0, 0xb07a30), ('chrome', 96, 0, 0xd8e0e8), ('stone', 112, 0, 0xd0c8d4)):
    v = A.add(key, x, y, 16, 16); v[:] = hexrgb(c) * (0.92 + 0.1 * rng.random((16, 16, 1)))
v = A.add('carpet', 0, 16, 32, 64); v[:] = hexrgb(0xd0306a) * (0.9 + 0.1 * rng.random((64, 32, 1))); v[:, :3] = v[:, -3:] = hexrgb(0xffd24a)
v = A.add('rack', 32, 16, 32, 96); v[:] = hexrgb(0x1a1a22)  # a server rack's door: units, LEDs, a vent
for k in range(0, 96, 6): v[k] = hexrgb(0x3a3a46)
for k in range(2, 96, 6):
    for j in range(4, 28, 4): v[k:k + 2, j:j + 2] = hexrgb([0x39ff14, 0x4fd8ff, 0xff4fd8, 0xffe14d, 0x39ff14][(j + k) % 5]) if rng.random() < 0.6 else hexrgb(0x2a2a30)
v = A.add('clock', 64, 16, 48, 48); v[:] = hexrgb(0x16101e)
px_disc(v, 24, 24, 23, 0xe8b83a); px_disc(v, 24, 24, 20, 0xfff4d8)
for k in range(12):
    a = k * math.pi / 6; px_disc(v, 24 + 17 * math.sin(a), 24 - 17 * math.cos(a), 1.5, 0x16101e)
px_disc(v, 18, 19, 2.5, 0x16101e); px_disc(v, 30, 19, 2.5, 0x16101e); px_disc(v, 24, 25, 9, 0x16101e, r_in=7.5, a0=math.pi * 0.6, a1=math.pi * 1.4)
v = A.add('tympanum', 112, 16, 64, 32); v[:] = hexrgb(0xd0c8d4) * (0.92 + 0.08 * rng.random((32, 64, 1)))
px_disc(v, 32, 18, 13, 0xe8b83a); px_disc(v, 32, 18, 11, 0xffd24a); px_disc(v, 27, 14, 1.8, 0x16101e); px_disc(v, 37, 14, 1.8, 0x16101e)
px_disc(v, 32, 19, 6, 0x16101e, r_in=4.6, a0=math.pi * 0.6, a1=math.pi * 1.4)
for k in range(10): px_disc(v, 32 + 18 * math.sin(-1.2 + k * 0.27), 18 - 18 * math.cos(-1.2 + k * 0.27), 1.2, 0xe8b83a)  # rays
v = A.add('plaque', 112, 48, 96, 16); v[:] = hexrgb(0xe8b83a); v[1] = v[-2] = hexrgb(0x6a4a10)
text_px(v, 'BLESSED ARE', 15, 1, 1, 0x4a2a08); text_px(v, 'THE SHAREHOLDERS', 0, 8, 1, 0x4a2a08)


# ------------------------------------------------------------ helpers
def touching(b, axis, side):
    """does another wall box sit flush against this face? (then the face gets inset a hair: no coincident corners)"""
    c = b['max'][axis] if side > 0 else b['min'][axis]
    o1, o2 = [k for k in range(3) if k != axis]
    for q in BOX:
        if q is b: continue
        qc = q['min'][axis] if side > 0 else q['max'][axis]
        if abs(qc - c) > 1e-4: continue
        if q['min'][o1] < b['max'][o1] - 1e-4 and q['max'][o1] > b['min'][o1] + 1e-4 and q['min'][o2] < b['max'][o2] - 1e-4 and q['max'][o2] > b['min'][o2] + 1e-4: return True
    return False


def solid(name, b, m, tile, faces=None, inset=True):
    """a map box as a textured box (world-scale tiling UVs), faces flush against a neighbour pulled in 0.5 mm"""
    lo, hi = list(b['min']), list(b['max'])
    if inset:
        for ax in range(3):
            if touching(b, ax, -1): lo[ax] += 0.0005
            if touching(b, ax, 1): hi[ax] -= 0.0005
    cells = {s: 'stone' for s in (faces or K.SIDES) if not (s == '-y' and b['min'][1] < 0.01)}  # (nobody sees under the ground)
    o = boxa(name, tuple(lo), tuple(hi), m, A, cells)
    uv_box(o, tile)
    return o


def tiled(o, tile): uv_box(o, tile); return o


def rot_y(o, ang, about=(0, 0, 0)):
    o.data.transform(Matrix.Translation(lib.gv(*about)) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Translation(-lib.gv(*about)))
    return o


def pointed_arch(name, cx, y0, span, rise, z0, z1, m, w=0.18, n=8, axis='x'):
    """a pointed (two-centred) arch rib: two quarter-ish arcs meeting at the top, a band w thick, depth z0..z1"""
    R = span * 0.85; hx = span / 2
    # the left arc is centred on the springing line at (cx - hx + R, y0), the right one mirrored
    ca = cx - hx + R; amax = math.acos((ca - cx) / R) if R > 0 else 0
    left = [(ca - R * math.cos(a), y0 + R * math.sin(a)) for a in np.linspace(0, amax, n + 1)]
    right = [(2 * cx - x, y) for x, y in reversed(left)]
    curve = left + right[1:]
    scale = rise / max(1e-3, max(y for _, y in curve) - y0)
    curve = [(x, y0 + (y - y0) * scale) for x, y in curve]
    verts, faces = [], []
    # extrude a band: inner curve and an outer curve offset by w (outward from the arch centre)
    inner = curve
    outer = []
    for i, (x, y) in enumerate(curve):
        p0 = curve[max(0, i - 1)]; p1 = curve[min(len(curve) - 1, i + 1)]
        tx, ty = p1[0] - p0[0], p1[1] - p0[1]; l = math.hypot(tx, ty) or 1
        nx, ny = -ty / l, tx / l
        if ny < 0 or (abs(ny) < 1e-6 and nx * (x - cx) < 0): nx, ny = -nx, -ny
        if (x - cx) * nx < 0 and abs(x - cx) > 1e-3: nx = -nx
        outer.append((x + nx * w, y + ny * w))
    def P(x, y, z): return (x, y, z) if axis == 'x' else (z, y, x)
    N = len(curve)
    for (xi, yi), (xo, yo) in zip(inner, outer):
        verts += [P(xi, yi, z0), P(xo, yo, z0), P(xo, yo, z1), P(xi, yi, z1)]
    for i in range(N - 1):
        a, b = i * 4, (i + 1) * 4
        for k in range(4):
            k2 = (k + 1) % 4; faces.append((a + k, a + k2, b + k2, b + k))
    faces.append((0, 1, 2, 3)); faces.append(((N - 1) * 4 + 3, (N - 1) * 4 + 2, (N - 1) * 4 + 1, (N - 1) * 4))
    o = K.outward(mesh(name, verts, faces, m)); lib.smooth(o, 35)
    return o


# ------------------------------------------------------------ the build
def build():
    lib.reset(); lib._mats.clear()
    STONE = mat('jbc_stone', 0xffffff, rough=0.7, tex=ashlar())
    MARB = mat('jbc_marble', 0xffffff, rough=0.25, clearcoat=0.6, tex=marble_tex())
    WOOD = mat('jbc_wood', 0xffffff, rough=0.45, clearcoat=0.4, tex=wood_tex())
    ROOF = mat('jbc_roof', 0xffffff, rough=0.55, metal=0.3, tex=roof_tex())
    TRIM = mat('jbc_trim', 0xffffff, rough=0.3, metal=0.2, clearcoat=0.6, tex=A.image())
    LED = mat('jbc_led', 0xffffff, rough=0.4, emit=0xffffff, strength=1.0, tex=A.image(), emit_tex=True)
    GLOW = mat('glow', 0x4fd8ff, rough=0.3, emit=0x4fd8ff, strength=2.0)
    GREEN = mat('glow_green', 0x39ff14, rough=0.3, emit=0x39ff14, strength=2.0)
    RED = mat('glow_red', 0xff3030, rough=0.3, emit=0xff3030, strength=2.0)
    P, Q = [], []
    walls = [b for b in BOX if b['mat'] == 'stone']
    for i, b in enumerate(walls):
        P.append(solid(f'c_wall{i}', b, STONE, 2.0))
    for b in walls:  # the far LOD: the same boxes, plain
        Q.append(tiled(boxa('c1_wall', tuple(b['min']), tuple(b['max']), STONE, A, {s: 'stone' for s in K.SIDES if s != '-y'}), 2.0))
    # the floor: marble with a pink runner up the aisle (its top in three strips; sides and bottom as the box)
    fb = next(b for b in BOX if b['mat'] == 'marble' and b['max'][1] < 0.2 and b['max'][0] - b['min'][0] > 20)
    x0, y0, z0 = fb['min']; x1, y1, z1 = fb['max']
    for a, b_, m in ((x0, -1.6, MARB), (-1.6, 1.6, TRIM), (1.6, x1, MARB)):
        o = boxa('c_floor', (a + (0.0005 if a != x0 else 0), y0, z0), (b_ - (0.0005 if b_ != x1 else 0), y1, z1), m, A,
                 {'+y': 'carpet' if m is TRIM else 'stone', '-z': 'stone', '+z': 'stone', **({'-x': 'stone'} if a == x0 else {}), **({'+x': 'stone'} if b_ == x1 else {})})
        if m is MARB: uv_box(o, 3.0)
        P.append(o)
    Q.append(tiled(boxa('c1_floor', (x0, y0, z0), (x1, y1, z1), MARB, A, {'+y': 'stone'}), 3.0))
    for b in BOX:  # the front steps (marble), the roof (copper), the altar (gold), the tower's roof + cap
        if b['mat'] == 'marble' and b is not fb and b['max'][1] < 3:
            P.append(solid('c_step', b, MARB, 2.0)); Q.append(tiled(boxa('c1_step', tuple(b['min']), tuple(b['max']), MARB, A, {s: 'stone' for s in K.SIDES if s != '-y'}), 2.0))
    roof = next(b for b in BOX if b['mat'] == 'roofg' and b['max'][1] < 15)
    P.append(tiled(boxa('c_roof', tuple(roof['min']), tuple(roof['max']), ROOF, A, {s: 'stone' for s in K.SIDES}), 2.0))
    Q.append(tiled(boxa('c1_roof', tuple(roof['min']), tuple(roof['max']), ROOF, A, {s: 'stone' for s in K.SIDES}), 2.0))
    # pilasters between the side windows (outside), pinnacles over the roof edge on each
    for s in (-1, 1):
        for zc in (-11.0, -5.0, 1.0, 7.0, 13.0, 16.6):
            a, b_ = sorted((s * 12.3, s * 12.55))
            P.append(tiled(boxa('c_pilaster', (a, 0, zc - 0.55), (b_, 14.0, zc + 0.55), STONE, A, {('-x' if s < 0 else '+x'): 'stone', '-z': 'stone', '+z': 'stone', '+y': 'stone'}), 2.0))
            c, d = sorted((s * 12.05, s * 12.5))
            P.append(tiled(boxa('c_pinnacle_base', (c, 14.6, zc - 0.22), (d, 15.4, zc + 0.22), STONE, A, {k: 'stone' for k in K.SIDES if k != '-y'}), 1.0))
            pk = K.lathe_closed('c_pinnacle', [(0.02, 15.4), (0.2, 15.4), (0.02, 17.2)], ((c + d) / 2, 0, zc), STONE, seg=4); fill_uv(pk, A, 'stone'); P.append(pk)
            P.append(K.lathe_closed('c_finial', [(0.02, 17.15), (0.08, 17.25), (0.02, 17.4)], ((c + d) / 2, 0, zc), TRIM, seg=6)); fill_uv(P[-1], A, 'gold')
    # window surrounds + pointed hood moulds over each tall window (both sides), outside
    for s in (-1, 1):
        for zc in (-14.0, -8.0, -2.0, 4.0, 10.0):
            a, b_ = sorted((s * 12.3, s * 12.42))
            for z_ in (zc - 1.12, zc + 1.0):  # jambs
                P.append(tiled(boxa('c_jamb', (a, 3.0, z_), (b_, 10.5, z_ + 0.12), STONE, A, {k: 'stone' for k in K.SIDES}), 1.0))
            P.append(tiled(boxa('c_sill', (a - (0.06 if s < 0 else 0), 2.86, zc - 1.2), (b_ + (0.06 if s > 0 else 0), 3.0, zc + 1.2), STONE, A, {k: 'stone' for k in K.SIDES}), 1.0))
            arch = pointed_arch('c_hood', zc, 10.5, 2.24, 1.1, 0, 0.12, STONE, w=0.16, axis='z')
            arch.data.transform(Matrix.Translation(lib.gv(a, 0, 0))); fill_uv(arch, A, 'stone'); P.append(arch)
    # the portal: clustered jamb columns, a pointed arch over the door, the gold ☺ in the tympanum, a plaque
    for xs in (-3.0, 3.0):
        for k, r in enumerate((0.22, 0.18, 0.15)):
            xx = xs + (-1 if xs < 0 else 1) * (0.25 + k * 0.3)
            e = 0.012 * k  # (staggered caps: the cluster's shafts overlap)
            col = K.lathe_closed('c_portal_col', [(r * 0.6, 0.15 + e), (r, 0.15 + e), (r, 6.3 - e), (r * 1.2, 6.5 - e), (r * 0.6, 6.5 - e)], (xx, 0, -18.3 - r - 0.02), STONE, seg=8)
            fill_uv(col, A, 'stone'); P.append(col)
    for k, (span, rise, w) in enumerate(((6.4, 1.9, 0.22), (7.0, 2.1, 0.2), (7.6, 2.3, 0.2))):
        arch = pointed_arch('c_portal_arch', 0, 6.5, span, rise, -18.3 - 0.06 - k * 0.08, -18.3 + 0.02, STONE, w=w, axis='x')
        fill_uv(arch, A, 'stone'); P.append(arch)
    tym = boxa('c_tympanum', (-1.95, 6.55, -18.33), (1.95, 8.35, -18.29), TRIM, A, {'-z': 'tympanum', '+y': 'stone', '-x': 'stone', '+x': 'stone', '-y': 'stone'}); P.append(tym)
    P.append(boxa('c_plaque', (-3.6, 4.6, -18.45), (-3.0, 5.2, -18.3), TRIM, A, {'all': 'gold'}))
    # the rose window ring
    ring = K.lathe_closed('c_rose', [(2.15, -0.12), (2.45, -0.12), (2.45, 0.06), (2.15, 0.06)], (0, 0, 0), STONE, seg=24, axis='z')
    ring.data.transform(Matrix.Translation(lib.gv(0, 10.25, -18.3))); fill_uv(ring, A, 'stone'); P.append(ring)
    # inside: the ticker neon round the nave (as the box version: green, a red one every 6 m)
    for s in (-1, 1):
        for a_ in np.arange(-17, 17, 3):
            m = RED if (int(a_) % 6 == 0) else GREEN
            x0_, x1_ = sorted((s * 11.7, s * 11.66))
            P.append(boxa('c_ticker', (x0_, 11.3, a_), (x1_, 11.9, a_ + 2.6), m, A, {k: 'pink' for k in K.SIDES}))
    # pews: seat + back exactly over the boxes, carved end panels
    for b in BOX:
        if b['mat'] != 'wood': continue
        P.append(tiled(solid('c_pew', b, WOOD, 1.0, inset=False), 1.0))
        if b['max'][1] < 0.7:  # a seat: its two ends
            for xe in (b['min'][0] - 0.06, b['max'][0]):
                end = boxa('c_pew_end', (xe, 0.15, b['min'][2] - 0.02), (xe + 0.06, 1.32, b['max'][2] + 0.1), WOOD, A, {k: 'stone' for k in K.SIDES})
                uv_box(end, 1.0); P.append(end)
    # the altar: gold, a frontal of panels, the plaque over the organ
    alt = next(b for b in BOX if b['mat'] == 'gold' and b['max'][1] < 2)
    P.append(boxa('c_altar', tuple(alt['min']), tuple(alt['max']), TRIM, A, {k: 'gold' for k in K.SIDES}))
    for k in range(5):
        x = -2.6 + k * 1.3
        P.append(boxa('c_altar_panel', (x, 0.35, alt['min'][2] - 0.05), (x + 0.9, 1.15, alt['min'][2] + 0.01), TRIM, A, {k2: 'white' for k2 in K.SIDES}))
    P.append(boxa('c_motto', (-3.0, 10.6, 17.66), (3.0, 11.6, 17.7), TRIM, A, {'-z': 'plaque', '-x': 'gold', '+x': 'gold', '+y': 'gold', '-y': 'gold'}))
    # the organ: server racks (exactly the boxes), chrome pipes with glowing mouths above them
    for b in BOX:
        if b['mat'] != 'shelfstock': continue
        x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
        P.append(boxa('c_rack', (x0, y0, z0), (x1, y1, z1), TRIM, A, {'+y': 'dark', '-x': 'dark', '+x': 'dark', '-z': 'dark'}))
        P.append(boxa('c_rack_door', (x0 + 0.05, y0 + 0.1, z0 - 0.03), (x1 - 0.05, y1 - 0.1, z0 + 0.001), LED, A, {'-z': 'rack', '-x': 'dark', '+x': 'dark', '+y': 'dark', '-y': 'dark'}))
        cx = (x0 + x1) / 2
        for j, h in enumerate((3.0, 4.5, 6.0)):
            hh = h + 1.5 * ((round(cx) // 3) % 3)
            px_ = cx - 0.45 + j * 0.45
            pipe = K.lathe_closed('c_pipe', [(0.1, y1), (0.16, y1), (0.16, y1 + hh), (0.1, y1 + hh)], (px_, 0, 16.5), TRIM, seg=10)
            fill_uv(pipe, A, 'chrome'); P.append(pipe)
            mouth = boxa('c_pipe_mouth', (px_ - 0.1, y1 + 0.5, 16.32), (px_ + 0.1, y1 + 0.75, 16.4), GLOW, A, {k: 'white' for k in K.SIDES}); P.append(mouth)
    for b in BOX:
        if b['mat'] == 'shelfstock': Q.append(boxa('c1_rack', tuple(b['min']), tuple(b['max']), TRIM, A, {'-z': 'rack', '+y': 'dark'}))
    # the bell tower: a ☺ clock on the three faces you can see, the belfry's columns + arches, the bell, the cap, a spire
    for face, (lo, hi, side) in {'front': ((TX - 1.2, 27.6, TZ - 4.06), (TX + 1.2, 30.0, TZ - 4.0), '-z'),
                                 'side': ((TX + 4.0, 27.6, TZ - 1.2), (TX + 4.06, 30.0, TZ + 1.2), '+x'),
                                 'back': ((TX - 1.2, 27.6, TZ + 4.0), (TX + 1.2, 30.0, TZ + 4.06), '+z')}.items():
        P.append(boxa('c_clock', lo, hi, TRIM, A, {k: ('clock' if k == side else 'gold') for k in K.SIDES}))
    for b in BOX:
        if b['mat'] == 'marble' and b['min'][1] > 30:  # the belfry columns: shaft, base and capital
            cx, cz = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2
            col = K.lathe_closed('c_bcol', [(0.3, 34.0), (0.42, 34.0), (0.42, 34.25), (0.33, 34.4), (0.33, 39.4), (0.42, 39.6), (0.42, 40.0), (0.3, 40.0)], (cx, 0, cz), MARB, seg=12)
            uv_box(col, 1.0); P.append(col)
            Q.append(boxa('c1_bcol', tuple(b['min']), tuple(b['max']), MARB, A, {k: 'stone' for k in K.SIDES}))
    for side in range(4):  # pointed arches between the belfry columns, high up (the belfry stays open below)
        arch = pointed_arch('c_belfry_arch', 0, 38.3, 6.4, 1.6, -3.95, -3.55, STONE, w=0.2, axis='x')
        rot_y(arch, side * math.pi / 2); arch.data.transform(Matrix.Translation(lib.gv(TX, 0, TZ))); fill_uv(arch, A, 'stone'); P.append(arch)
    for b in BOX:
        if b['mat'] == 'roofg' and b['min'][1] > 30:
            P.append(tiled(boxa('c_troof', tuple(b['min']), tuple(b['max']), ROOF, A, {k: 'stone' for k in K.SIDES}), 2.0))
            Q.append(tiled(boxa('c1_troof', tuple(b['min']), tuple(b['max']), ROOF, A, {k: 'stone' for k in K.SIDES}), 2.0))
        if b['mat'] == 'gold' and b['min'][1] > 30:
            P.append(boxa('c_cap', tuple(b['min']), tuple(b['max']), TRIM, A, {k: 'gold' for k in K.SIDES if k != '-y'}))
            Q.append(boxa('c1_cap', tuple(b['min']), tuple(b['max']), TRIM, A, {k: 'gold' for k in K.SIDES if k != '-y'}))
    spire = K.lathe_closed('c_spire', [(0.05, 42.0), (1.6, 42.0), (0.05, 48.0)], (TX, 0, TZ), TRIM, seg=4); fill_uv(spire, A, 'gold'); rot_y(spire, math.pi / 4, (TX, 0, TZ)); P.append(spire)
    P.append(fill_uv(rod((TX, 47.8, TZ), (TX, 50.5, TZ), 0.05, TRIM, seg=6, name='c_vane_rod'), A, 'metal'))
    P.append(boxa('c_vane', (TX - 0.9, 49.6, TZ - 0.02), (TX + 0.9, 50.0, TZ + 0.02), TRIM, A, {k: 'gold' for k in K.SIDES}))
    sm = K.lathe_closed('c_vane_smile', [(0.02, -0.025), (0.34, -0.025), (0.34, 0.025), (0.02, 0.025)], (0, 0, 0), TRIM, seg=12, axis='z')
    sm.data.transform(Matrix.Translation(lib.gv(TX + 1.1, 49.95, TZ))); fill_uv(sm, A, 'gold'); P.append(sm)
    Q.append(K.lathe_closed('c1_spire', [(0.05, 42.0), (1.6, 42.0), (0.05, 48.0)], (TX, 0, TZ), TRIM, seg=4)); fill_uv(Q[-1], A, 'gold')
    # the bell: bronze, on a yoke beam under the tower roof
    bell = K.lathe_closed('c_bell', [(0.06, 38.0), (0.5, 38.0), (0.62, 37.6), (0.7, 36.8), (0.86, 36.1), (1.08, 35.6), (1.0, 35.55), (0.72, 36.0), (0.55, 36.9), (0.4, 37.7), (0.06, 37.8)], (TX, 0, TZ), TRIM, seg=16)
    fill_uv(bell, A, 'bronze'); P.append(bell)
    P.append(boxa('c_yoke', (TX - 2.6, 38.0, TZ - 0.18), (TX + 2.6, 38.36, TZ + 0.18), WOOD, A, {k: 'stone' for k in K.SIDES})); uv_box(P[-1], 1.0)
    for xs in (-2.6, 2.6):
        P.append(boxa('c_yoke_hang', (TX + xs - 0.1, 38.36, TZ - 0.1), (TX + xs + 0.1, 40.0, TZ + 0.1), TRIM, A, {k: 'metal' for k in K.SIDES}))
    P.append(boxa('c_clapper', (TX - 0.08, 35.7, TZ - 0.08), (TX + 0.08, 37.9, TZ + 0.08), TRIM, A, {k: 'metal' for k in K.SIDES}))
    return P, Q


def main():
    P, Q = build()
    for o in P + Q: apply_mods(o)
    if '--qa-parts' in ARGV:
        sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
        import qa_check
        res = qa_check.run(objects=[o.name for o in P], profile='game', eps=0.0008, tol=0.002)
        for e in res.get('errors', []): print('QAP', str(e)[:220])
        return
    # joined without welding: each piece is closed on its own, and welding the corners where wall pieces meet flips
    # windings (the walls are the map's boxes, butted together)
    m0 = lib.join(P, 'jb_cathedral_lod0'); m1 = lib.join(Q, 'jb_cathedral_lod1')
    if '--qa' in ARGV: K.qa([m0], 'cathedral lod0'); K.qa([m1], 'cathedral lod1')
    lib.bake_ao([m0], dist=1.2); lib.bake_ao([m1], dist=1.2)
    p = D['placement']
    root = lib.prop_finish('p_jb_cathedral', [m0], [m1], {'id': 'jb_cathedral', 'kind': 'prop', 'lod': 180, 'tint': False, 'box': [p['lo'], p['hi']]})
    lib.prop_stats(root); print('JF_EXTENT', K.extent([m0]))
    if '--no-export' not in ARGV: lib.export(root, 'p_jb_cathedral')
    if '--no-sheet' not in ARGV:
        e = next(c for c in root.children if c.name.startswith('lod1')); e.parent = None; m1.hide_render = True
        lib.sheet(root, 'p_jb_cathedral', extra_note='CATHEDRAL OF SHAREHOLDER VALUE', exposure=-0.3)


main()
