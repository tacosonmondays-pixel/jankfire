# JANKFIRE's loadout wraps as real textures for the Roblox guns (SurfaceAppearance maps), drawn fresh from each wrap's
#
# RULES FOR EVERY IMAGE (16 Nov 2026: the owner's Roblox account was moderated over a wrap image that looked like a QR
# code, reason "Directing Users Off-Platform"). Every map this script draws is uploaded to Roblox, so:
#   - no QR-like or barcode-like patterns, nothing a scanner or a person could take for a code ("QR Code" and
#     "Barcode" are plain colour wraps: their designs are unregistered and wrap_upload.py refuses them);
#   - no URLs, handles, @names, social or site logos;
#   - no readable text at all, words or numbers: writing is drawn as rounded grey bars (ink_lines), a number as a blank
#     panel, a stamp as an outline;
#   - no 69 / 420 / 666 jokes, nothing sexual or about drugs, no blood, gore, body parts or raw flesh.
# Look at every map at full size before an upload batch.
#
# idea and palette in the web game (public/js/wrappack.js, public/js/skins.js, shared/cosmetics.js).
#
#   py tools/roblox/wrap_textures.py <out_dir> [wrap ids ...]      (no ids = every wrap that has a design)
#   py tools/roblox/wrap_textures.py <out_dir> --sheet [ids ...]   also a contact sheet of the colour maps
#
# Writes <out_dir>/<id>_color.png (+ _normal, _rough, _metal, _emit when they vary) and merges <out_dir>/wraps.json:
# per wrap the map files (or a number for a flat map) and the SurfaceAppearance settings. The PNGs are not kept in git
# (about 1.5 MB each): this script makes them again, the same every time (each wrap's dice are seeded by its id).
#
# THE SCALE. One tile (1024 px) covers TILE_M metres of gun (the UVs, tools/roblox/gun_uvs.py, use the same number):
# 1 cm = 41 px. First person shows a rifle at roughly 1,500 screen pixels a metre, so a tile is drawn about 2.7 times
# finer than the screen needs (crisp, and the mipmaps keep it calm further away).
#
# THE LOOK (owner, 16 Nov 2026; vault Principles/Design principles.md): serious and polished, in the class of RIVALS,
# never noisy. Wraps are cosmetics, so colour is allowed, but each must be deliberate: clean shapes, a few flat colours
# with smooth tonal shifts, real shapes for details (five-pointed stars, notched petals, tapered stripes), no pixel
# specks, no grain. Warm colours and purples come out brighter under the halls' lamps: they are picked a step darker.
import sys, os, json, math, zlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wraplib import *

TILE_M = 0.25   # metres of gun per tile (must match gun_uvs.TILE_M)
N = 1024
PX_CM = N / (TILE_M * 100)  # pixels per centimetre


def seed_of(wid): return zlib.crc32(wid.encode()) & 0x7fffffff


def scatter(rng, n, count, min_d, tries=4000, taken=None):
    """points spread over the torus with at least min_d px between them (and from `taken`)"""
    pts = list(taken or [])
    out = []
    for _ in range(tries):
        if len(out) >= count: break
        x, y = rng.uniform(0, n), rng.uniform(0, n)
        ok = True
        for (px, py, *rest) in pts:
            dx = abs(x - px); dx = min(dx, n - dx)
            dy = abs(y - py); dy = min(dy, n - dy)
            md = rest[0] if rest else min_d
            if dx * dx + dy * dy < max(md, min_d) ** 2: ok = False; break
        if ok:
            out.append((x, y)); pts.append((x, y, min_d))
    return out


def field_cover(f, thr):
    """anti-aliased coverage of {f > thr} for a smooth full-tile field f (its pixel gradient sets the edge width)"""
    gx = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) * 0.5
    gy = (np.roll(f, -1, 0) - np.roll(f, 1, 0)) * 0.5
    g = np.sqrt(gx * gx + gy * gy) + 1e-6
    return np.clip(0.5 + (f - thr) / g, 0, 1)


DESIGNS = {}
def design(wid):
    def reg(fn): DESIGNS[wid] = fn; return fn
    return reg


# ====================================================================== batch 1: the hardest ten
@design('galaxy')
def galaxy(t: Tex):
    """deep space: smooth violet nebulae over indigo, crisp five-pointed stars, twinkles and star dust that glow"""
    n, U, V = t.n, t.U, t.V
    w1, w2 = FBM([2, 4], 11), FBM([2, 4], 12)
    wu, wv = U + 0.08 * w1(U, V), V + 0.08 * w2(U, V)
    neb = FBM([2, 4, 8], 13)(wu, wv)
    neb2 = FBM([3, 6], 14)(wu + 0.3, wv)
    m = smoothstep(-0.15, 0.55, neb)
    m2 = smoothstep(0.1, 0.7, neb2)
    base = mix('100828', '24154f', smoothstep(-0.6, 0.4, neb))[..., :]
    t.rgb[:] = base
    t.fill(m * 0.75, '5a36a8')
    t.fill(m * m * 0.55, '9a6ae0')
    t.fill(m2 * (1 - m) * 0.35, '2c3a8a')   # a little deep blue where the violet thins
    t.emit[:] = m * 0.12
    t.rough[:] = 0.3
    r = t.rng
    # dust: small round points, more of them in the clouds
    for _ in range(700):
        x, y = r.uniform(0, n), r.uniform(0, n)
        k = float(m[int(y) % n, int(x) % n])
        if r.uniform() > 0.35 + 0.65 * k: continue
        rad = r.uniform(1.1, 2.4)
        col = '#ffffff' if r.uniform() < 0.7 else '#d8c4ff'
        t.shape((x - 4, y - 4, x + 4, y + 4), sd_circle(x, y, rad), color=col, emit=0.55 + 0.4 * r.uniform())
    big = scatter(r, n, 4, 300)
    mid = scatter(r, n, 9, 170, taken=[(x, y, 260) for x, y in big])
    for i, (x, y) in enumerate(big + mid):
        hero = i < len(big)
        ro = r.uniform(40, 54) if hero else r.uniform(15, 30)
        rot = r.uniform(0, TAU)
        # a soft halo, then the star, then a brighter heart
        X, Y, idx = t.box(x - ro * 2.4, y - ro * 2.4, x + ro * 2.4, y + ro * 2.4)
        sd = sd_star(x, y, ro, ro * 0.42, 5, rot, round_=ro * 0.06)(X, Y)
        halo = np.exp(-np.maximum(sd, 0) / (ro * 0.45)) * (0.35 if hero else 0.22)
        t.paint(idx, halo, '8f66ff', emit=halo * 1.5)
        t.paint(idx, cover(sd), 'efe4ff', emit=1.0, rough=0.2)
        sd2 = sd_star(x, y, ro * 0.55, ro * 0.55 * 0.42, 5, rot, round_=ro * 0.04)(X, Y)
        t.paint(idx, cover(sd2) * 0.85, '#ffffff')
    for x, y in scatter(r, n, 12, 90, taken=[(x, y, 120) for x, y in big + mid]):
        ro = r.uniform(9, 18)
        X, Y, idx = t.box(x - ro, y - ro, x + ro, y + ro)
        sd = sd_sparkle(x, y, ro, 0.16, r.uniform(-0.2, 0.2))(X, Y)
        t.paint(idx, cover(sd), '#f6f0ff', emit=0.9)
    return {'emissive': 1.2, 'tint': 'ffffff'}


def camo_layers(t: Tex, base, light, mid, dark, seed, cut=(0.02, 0.12, 0.2), stretch=1.0):
    """four flat colours in big organic shapes, stretched a little along the gun, clean edges"""
    U, V = t.U, t.V
    wu = U + 0.04 * FBM([3, 6], seed + 1)(U, V)
    wv = V + 0.04 * FBM([3, 6], seed + 2)(U, V)
    t.rgb[:] = hexrgb(base)
    f1 = FBM([(2, 3), (4, 6), (8, 12)], seed + 3, 0.45)(wu, wv)
    f2 = FBM([(3, 4), (6, 8), (12, 16)], seed + 4, 0.45)(wu, wv)
    f3 = FBM([(3, 5), (6, 10), (12, 20)], seed + 5, 0.5)(wu, wv)
    t.fill(field_cover(f1, cut[0]), light)
    t.fill(field_cover(f2, cut[1]), mid)
    t.fill(field_cover(f3, cut[2]), dark)
    return f1, f2, f3


@design('camo')
def camo(t: Tex):
    """woodland camo: olive, khaki sage, bark brown and near-black green"""
    camo_layers(t, '4a5530', '7b7f55', '3d3122', '22261a', 20)
    t.rough[:] = 0.78
    return {}


@design('tiger')
def tiger(t: Tex):
    """tiger: burnt orange coat with wavy black stripes that run round the gun, thick in the middle, breaking into
       tapered points and forks (the contour bands of a warped field, cut where a second field thins them)"""
    U, V = t.U, t.V
    tone = FBM([2, 4], 31)(U, V)
    t.rgb[:] = mix('a14a14', 'b8601e', smoothstep(-0.5, 0.6, tone))
    t.fill(smoothstep(0.25, 0.7, FBM([(3, 2), (6, 4)], 36)(U, V)) * 0.35, 'c88a48')   # paler patches in the coat
    warp = FBM([(2, 3), (4, 6)], 32, 0.5)(U, V)
    wob = FBM([(4, 2), (8, 4)], 33, 0.5)(U, V)
    ph = 6.0 * U + 0.8 * warp + 0.08 * np.sin(V * TAU * 3)
    s = np.cos(ph * TAU)                                   # +1 down the middle of each band
    thin = FBM([(5, 3), (10, 6), (20, 12)], 34, 0.55)(U, V)
    f = s - (0.66 + 1.15 * thin) + 0.25 * wob               # the band's own width and its breaks
    t.rough[:] = 0.42
    t.fill(field_cover(f, 0.0), '18110c', rough=0.5)
    return {}


@design('carbon')
def carbon(t: Tex):
    """2x2 twill carbon fibre under a clear coat: each tow a rounded ribbon of fine fibres, the weave in relief"""
    n = t.n
    c = 32
    X, Y = t.X, t.Y
    i, j = np.floor(X / c).astype(int), np.floor(Y / c).astype(int)
    fx, fy = (X % c) / c, (Y % c) / c
    vert = ((i - j) % 4) < 2      # the tow seen in this cell runs up and down
    across = np.where(vert, fx, fy)
    along = np.where(vert, fy, fx)
    # where along its float of two cells the tow is: it dives under at both ends of the float
    m4 = (i - j) % 4
    k = np.where(vert, 1 - m4, m4 - 2)   # first or second cell of its float of two
    f2 = (along + k) / 2.0       # 0..1 along the float
    bulge = np.sqrt(np.clip(1 - (2 * across - 1) ** 2, 0, 1))
    dive = 1 - (np.abs(2 * f2 - 1) ** 6)
    h = bulge * (0.35 + 0.65 * dive)
    fib = 0.5 + 0.5 * np.cos(across * TAU * 6)    # fine fibres along the tow
    lum = 0.11 + 0.17 * h * (0.75 + 0.25 * fib)
    lum = lum * np.where(vert, 1.0, 0.82)          # the two directions catch the light differently
    base = np.array([1.0, 1.02, 1.12], np.float32)
    t.rgb[:] = np.clip(lum[..., None] * base, 0, 1)
    t.height[:] = h * 2.2
    t.normal_k = 1.0
    t.rough[:] = 0.2
    return {}


def petal_outline(L, W, notch=0.14):
    left = bezier((0, 0), (L * 0.3, W * 0.95), (L * 0.85, W * 1.05), (L, W * 0.42))
    right = bezier((L, -W * 0.42), (L * 0.85, -W * 1.05), (L * 0.3, -W * 0.95), (0, 0))
    return left + [(L * (1 - notch), 0)] + right[:-1]


@design('sakura')
def sakura(t: Tex):
    """sakura storm: pale five-petal blossoms with notched petals and stamens, loose petals drifting, on deep plum"""
    n, U, V = t.n, t.U, t.V
    tone = FBM([2, 3], 41)(U, V)
    t.rgb[:] = mix('241024', '3b1438', smoothstep(-0.6, 0.6, tone))
    t.rough[:] = 0.36
    r = t.rng
    blossoms = scatter(r, n, 5, 330)
    loose = scatter(r, n, 13, 110, taken=[(x, y, 200) for x, y in blossoms])
    for x, y in loose:
        L = r.uniform(32, 50); rot = r.uniform(0, TAU)
        poly = transform(petal_outline(L, L * 0.45, 0.16), x - math.cos(rot) * L / 2, y - math.sin(rot) * L / 2, rot)
        X, Y, idx = t.box(*bbox_of(poly, 3))
        sd = sd_polygon(poly)(X, Y)
        shade = r.uniform(0, 1)
        t.paint(idx, cover(sd) * 0.92, mix('e889b8', 'ffd3e6', shade))
    for x, y in blossoms:
        R = r.uniform(72, 96); rot = r.uniform(0, TAU)
        X, Y, idx = t.box(x - R - 4, y - R - 4, x + R + 4, y + R + 4)
        d = np.hypot(X - x, Y - y)
        grad = mix('ff86b9', 'ffe6f0', smoothstep(R * 0.15, R * 0.95, d)[..., None] * np.ones(3, np.float32))
        for k in range(5):
            a = rot + k * TAU / 5
            poly = transform(petal_outline(R * 0.95, R * 0.42), x + math.cos(a) * R * 0.05, y + math.sin(a) * R * 0.05, a)
            sd = sd_polygon(poly)(X, Y)
            t.paint(idx, cover(sd + 1.2) * 0.55, 'c25a8c')        # a thin darker edge between the petals
            t.paint(idx, cover(sd + 1.2), grad)
        t.paint(idx, cover(d - R * 0.17), 'e8538f')
        for k in range(7):
            a = rot + 0.45 + k * TAU / 7
            ex, ey = x + math.cos(a) * R * 0.36, y + math.sin(a) * R * 0.36
            t.paint(idx, cover(sd_segment(x, y, ex, ey, 0.9, 0.7)(X, Y)), 'f3a0c4')
            t.paint(idx, cover(np.hypot(X - ex, Y - ey) - R * 0.045), 'ffe07a')
    return {}


@design('hazard')
def hazard(t: Tex):
    """hazard stripes: crisp 45-degree yellow and black bands, a hair of relief at each edge like printed vinyl"""
    s = (t.X + t.Y) % 256.0
    sd = (np.abs(s - 64.0) - 64.0) / math.sqrt(2)    # < 0 inside the yellow band
    a = cover(sd)
    t.rgb[:] = hexrgb('18181b')
    t.fill(a, 'e2b200')
    t.rough[:] = 0.42 - 0.08 * a
    t.height[:] = a * 0.6
    return {}


@design('racing')
def racing(t: Tex):
    """checkered flag: bold crisp checks, slightly warm white and deep black, gloss lacquer"""
    def wave(x, cell):
        f = x % (2 * cell)
        e = np.where(f < cell, np.minimum(f, cell - f), -np.minimum(f - cell, 2 * cell - f))
        return np.clip(0.5 + e, 0, 1) * 2 - 1
    q = wave(t.X, 128.0) * wave(t.Y, 128.0)
    white = (1 + q) / 2
    t.rgb[:] = hexrgb('141416')
    t.fill(white, 'ecebe6')
    t.rough[:] = 0.26 + 0.06 * white
    return {}


@design('hex')
def neon_hex(t: Tex):
    """neon hex: raised dark navy hex panels with bevelled edges; the grooves between them glow cyan"""
    n = t.n
    dx = n / 7.0                      # 7 hexes across, 4 double rows down: tiles with 1% stretch
    s = dx / math.sqrt(3)
    sy = (n / 8.0) / 1.5
    X, Y = t.X, t.Y * (s / sy)
    ri = s * math.sqrt(3) / 2         # inradius
    best, cid = None, None
    for ox, oy in ((0.0, 0.0), (dx / 2, 1.5 * s)):
        lx = (X - ox) % dx - dx / 2
        ly = (Y - oy) % (3 * s) - 1.5 * s
        qx, qy = np.abs(lx), np.abs(ly)
        d = np.maximum(qx, qx * 0.5 + qy * (math.sqrt(3) / 2)) - ri   # pointy-top hex: <0 inside
        ci = np.floor((X - ox) / dx).astype(int) * 2 + (0 if ox == 0 else 1)
        cj = np.floor((Y - oy) / (3 * s)).astype(int)
        cell = (ci * 73 + cj * 151) % 997
        if best is None: best, cid = d, cell
        else:
            closer = d < best
            best = np.where(closer, d, best); cid = np.where(closer, cell, cid)
    d = best                           # distance to the own cell's edge (negative inside)
    groove = 7.0
    inner = -d - groove                # >0 on the panel
    bev = 7.0
    hpanel = np.clip(inner / bev, 0, 1)
    hpanel = hpanel * hpanel * (3 - 2 * hpanel)
    var = ((cid * 37) % 11) / 10.0
    panel = mix('0b1522', '112033', var[..., None] * np.ones(3, np.float32) * 0.8)
    t.rgb[:] = hexrgb('05080d')
    a = np.clip(inner + 0.5, 0, 1)
    t.rgb[:] = t.rgb * (1 - a[..., None]) + panel * a[..., None]
    # a lighter top bevel catches the lamps
    topb = np.clip(1 - inner / bev, 0, 1) * a
    t.rgb[:] = t.rgb + (hexrgb('1c3048') - t.rgb) * (topb * 0.35)[..., None]
    line = np.clip(1.6 - np.abs(-d - groove * 0.5), 0, 1)       # the glowing filament in the groove
    halo = np.exp(-np.maximum(np.abs(-d - groove * 0.5) - 1.0, 0) / 3.0) * (1 - a)
    t.fill(line, '6fe4ff'); t.fill(halo * 0.45, '1f7fa6')
    t.emit[:] = np.maximum(line, halo * 0.6)
    t.height[:] = hpanel * 3.0
    t.rough[:] = 0.55 - 0.27 * a
    return {'emissive': 2.0, 'tint': '4fd8ff'}


@design('damascus')
def damascus(t: Tex):
    """damascus steel: the contour lines of a smooth folded field, bright and dark layers flowing in loops and
       ripples; the dark layers etched a little deeper and rougher"""
    U, V = t.U, t.V
    wu = U + 0.03 * FBM([4, 8], 63)(U, V)
    f = FBM([2, 4, 8], 61, 0.5)(wu, V)
    g = FBM([3, 6], 62)(U, V)
    ph = 13.0 * f + 5.0 * V + 2.0 * g
    s = np.sin(ph * TAU)
    fine = np.sin(ph * 2 * TAU)
    bright = smoothstep(-0.35, 0.35, s)
    lum = 0.42 + 0.26 * bright + 0.04 * fine * (1 - np.abs(s))
    t.rgb[:] = np.clip(lum[..., None] * np.array([1.0, 1.02, 1.06], np.float32), 0, 1)
    t.metal[:] = 1.0
    t.rough[:] = 0.42 - 0.18 * bright
    t.height[:] = bright * 0.8
    return {}


@design('holo')
def holo(t: Tex):
    """holo foil: silver foil with a soft prismatic sheen and crisp sparkling stars, each in its own hue"""
    n, U, V = t.n, t.U, t.V
    w = FBM([2, 4], 71)(U, V)
    hue = ((U + V) * 2 + 0.35 * w) % 1.0
    def hsv(h, s, v):
        k = lambda m: (m + h * 6) % 6
        f = lambda m: v - v * s * np.clip(np.minimum(k(m), 4 - k(m)), 0, 1)
        return np.stack([f(5), f(3), f(1)], -1)
    t.rgb[:] = hsv(hue, 0.16, 0.9)
    t.metal[:] = 0.8
    t.rough[:] = 0.22
    r = t.rng
    stars = scatter(r, n, 26, 110)
    for i, (x, y) in enumerate(stars):
        five = i % 3 == 0
        ro = r.uniform(16, 30) if five else r.uniform(10, 24)
        X, Y, idx = t.box(x - ro * 1.6, y - ro * 1.6, x + ro * 1.6, y + ro * 1.6)
        sd = (sd_star(x, y, ro, ro * 0.42, 5, r.uniform(0, TAU), round_=1.2) if five else sd_sparkle(x, y, ro, 0.17, r.uniform(-0.25, 0.25)))(X, Y)
        hh = (float(hue[int(y) % n, int(x) % n]) + 0.5) % 1.0
        col = hsv(np.float32(hh), np.float32(0.45), np.float32(1.0))
        glow = np.exp(-np.maximum(sd, 0) / 5.0) * 0.4
        t.paint(idx, glow, col, emit=glow)
        t.paint(idx, cover(sd), col, emit=0.9, rough=0.08, metal=0.6)
        t.paint(idx, cover(sd + ro * 0.22), '#ffffff')
    return {'emissive': 0.9, 'tint': 'ffffff'}


# ====================================================================== batch 2
@design('urban')
def urban(t: Tex):
    """urban camo: concrete greys, one cool light and two charcoals"""
    camo_layers(t, '6f737a', 'a9adb3', '474b52', '25272c', 120)
    t.rough[:] = 0.72
    return {}


@design('arctic')
def arctic(t: Tex):
    """arctic camo: snow white with blue-grey drifts (kept a step under white: the lamps would blow it out)"""
    camo_layers(t, 'd9dfe5', 'eef2f5', 'a9b6c2', '76869a', 140, cut=(0.05, 0.16, 0.26))
    t.rough[:] = 0.7
    return {}


@design('desert')
def desert(t: Tex):
    """desert camo: sand, pale dune, tan and a dry brown"""
    camo_layers(t, 'b89c6a', 'd8c496', '927247', '5f4529', 160, cut=(0.04, 0.14, 0.24))
    t.rough[:] = 0.75
    return {}


@design('digital')
def digital(t: Tex):
    """digital camo: the same organic blobs snapped to a crisp 16 px grid (4 mm), four olive drab tones"""
    n = t.n; c = 16
    U = (np.floor(t.X / c) + 0.5) * c / n; V = (np.floor(t.Y / c) + 0.5) * c / n
    a = FBM([(3, 4), (6, 8), (12, 16)], 181, 0.5)(U, V)
    b = FBM([(4, 4), (8, 8)], 182, 0.5)(U + 0.3, V)
    cols = [hexrgb(h) for h in ('5d6a42', '343c29', '7d7152', '98a07a')]
    idx = np.where(a > 0.17, 1, np.where(b > 0.15, 2, np.where(a < -0.17, 3, 0)))
    t.rgb[:] = np.stack(cols)[idx]
    t.rough[:] = 0.74
    return {}


@design('leopard')
def leopard(t: Tex):
    """leopard: broken rosettes of dark crescents round a warmer centre, small solid spots between, on golden tan"""
    n, U, V = t.n, t.U, t.V
    t.rgb[:] = mix('b9853f', 'cf9c52', smoothstep(-0.5, 0.5, FBM([2, 4], 191)(U, V)))
    t.rough[:] = 0.6
    r = t.rng
    ros = scatter(r, n, 18, 190)
    for x, y in ros:
        R = r.uniform(50, 66); rot = r.uniform(0, TAU)
        X, Y, idx = t.box(x - R * 1.5, y - R * 1.5, x + R * 1.5, y + R * 1.5)
        cx, cy = x + r.uniform(-4, 4), y + r.uniform(-4, 4)
        t.paint(idx, cover(sd_ellipse(cx, cy, R * 0.82, R * 0.68, rot)(X, Y)), '9a5d25')
        k = r.integers(3, 6)
        for j in range(k):
            a0 = rot + j * TAU / k + r.uniform(-0.2, 0.2)
            span = TAU / k * r.uniform(0.5, 0.78)
            pts = [(cx + math.cos(a0 + span * q / 8) * R * (0.95 + 0.08 * math.sin(q)), cy + math.sin(a0 + span * q / 8) * R * 0.86) for q in range(9)]
            w = R * r.uniform(0.16, 0.24)
            rad = [w * (0.35 + 0.65 * math.sin(math.pi * q / 8)) for q in range(9)]
            t.paint(idx, cover(sd_polyline(pts, rad)(X, Y)), '20130a')
    for x, y in scatter(r, n, 22, 70, taken=[(x, y, 110) for x, y in ros]):
        rr = r.uniform(8, 15)
        t.shape((x - rr * 2, y - rr * 2, x + rr * 2, y + rr * 2), sd_ellipse(x, y, rr, rr * r.uniform(0.6, 0.9), r.uniform(0, TAU)), color='20130a')
    return {}


@design('zebra')
def zebra(t: Tex):
    """zebra: bold black stripes round the gun, wavy, forking and tapering to points, on off-white"""
    U, V = t.U, t.V
    warp = FBM([(2, 3), (4, 6)], 201, 0.5)(U, V)
    ph = 7.0 * U + 0.65 * warp + 0.05 * np.sin(V * TAU * 2)
    s = np.cos(ph * TAU)
    thin = FBM([(4, 3), (8, 6)], 202, 0.5)(U, V)
    t.rgb[:] = hexrgb('e9e7df')
    t.fill(field_cover(s - (0.05 + 0.9 * thin), 0.0), '151515')
    t.rough[:] = 0.5
    return {}


@design('plaid')
def plaid(t: Tex):
    """dad plaid: a red tartan with green, navy, white and yellow lines, woven in a fine 2/2 twill where they cross"""
    n = t.n
    sett = [('9e1c26', 64), ('1d3a26', 56), ('9e1c26', 12), ('1c2450', 40), ('9e1c26', 30), ('d6b840', 6), ('9e1c26', 30),
            ('e8e2d2', 6), ('9e1c26', 12), ('1d3a26', 56), ('9e1c26', 64), ('1c2450', 40), ('9e1c26', 32)]
    total = sum(w for _, w in sett)
    scale = (n / 2) / total
    lut = np.zeros((n, 3), np.float32)
    pos = 0.0
    for col, w in sett * 2:
        a, b = int(round(pos)), int(round(pos + w * scale))
        lut[a:min(b, n)] = hexrgb(col); pos += w * scale
    lut[int(round(pos)):] = lut[int(round(pos)) - 1]
    xi, yi = t.X.astype(int) - 0, t.Y.astype(int)
    xi = np.clip(xi, 0, n - 1); yi = np.clip(yi, 0, n - 1)
    warp, weft = lut[xi], lut[yi]
    tw = ((t.X + t.Y) // 6) % 2                       # the twill: diagonal steps, 6 px each
    soft = np.clip(np.abs(((t.X + t.Y) % 6) - 3) - 0.5, 0, 1)
    k = (tw * 0.8 + 0.1)[..., None]
    t.rgb[:] = warp * k + weft * (1 - k)
    t.height[:] = 0.6 * soft
    t.normal_k = 0.6
    t.rough[:] = 0.85
    return {}


@design('kintsugi')
def kintsugi(t: Tex):
    """kintsugi: glossy black glaze, its cracks mended in gold that catches the light"""
    n, U, V = t.n, t.U, t.V
    r = t.rng
    t.rgb[:] = mix('17171b', '24242a', smoothstep(-0.4, 0.6, FBM([2, 4], 211)(U, V)))
    t.rough[:] = 0.16
    pts = [(r.uniform(0, n), r.uniform(0, n)) for _ in range(13)]
    d1, d2, _ = voronoi(n, pts)
    edge = (d2 - d1) * 0.5
    wv = FBM([(6, 6), (12, 12)], 212)(U, V)
    width = 2.6 + 1.8 * wv
    main = np.clip(width - edge + 0.5, 0, 1) * smoothstep(-0.55, -0.25, wv)
    pts2 = [(r.uniform(0, n), r.uniform(0, n)) for _ in range(40)]
    e1, e2, _ = voronoi(n, pts2)
    fine = np.clip(1.4 - (e2 - e1) * 0.5 + 0.5, 0, 1) * smoothstep(0.15, 0.4, FBM([3, 6], 213)(U, V))
    gold = np.maximum(main, fine * 0.9)
    t.fill(gold, 'd29a2c', metal=1.0, rough=0.24, emit=0.35)
    t.fill(np.clip(gold - 0.6, 0, 1) * 1.2, 'f0c868')
    t.height[:] = gold * 0.7
    return {'emissive': 0.6, 'tint': 'ffd27a'}


@design('seigaiha')
def seigaiha(t: Tex):
    """seigaiha: overlapping blue wave scales of cream rings, a cyan heart in each"""
    n = t.n; R = 128.0
    t.rgb[:] = hexrgb('1b2a63')
    rings = [(1.0, '1b2a63'), (0.9, 'efe8d6'), (0.78, '1b2a63'), (0.66, 'efe8d6'), (0.54, '1b2a63'), (0.42, 'efe8d6'), (0.3, '1b2a63'), (0.2, '3fb8d8')]
    rows = int(n / (R / 2)) + 3
    for j in range(-2, rows):
        y = j * R / 2
        for i in range(-1, int(n / (2 * R)) + 2):
            x = i * 2 * R + (R if j % 2 else 0)
            X, Y, idx = t.box(x - R - 2, y - R - 2, x + R + 2, y + 2)
            d = np.hypot(X - x, Y - y)
            above = cover(Y - y)  # only the upper half shows (the next row down covers the rest)
            for k, col in rings:
                t.paint(idx, cover(d - R * k) * above, col)
    t.rough[:] = 0.4
    return {}


@design('koi')
def koi(t: Tex):
    """koi pond: deep teal water with soft ripples, lily pads with a pink flower, and koi in orange, white and black"""
    n, U, V = t.n, t.U, t.V
    w = FBM([2, 4, 8], 231)(U, V)
    t.rgb[:] = mix('0b4652', '13677a', smoothstep(-0.6, 0.6, w))
    rip = np.abs(np.sin((FBM([2, 4], 232)(U, V) * 4) * TAU))
    t.fill(smoothstep(0.95, 1.0, rip) * 0.08, '7fd6e0')
    t.rough[:] = 0.2
    r = t.rng
    pads = scatter(r, n, 2, 450)
    for x, y in pads:
        R = r.uniform(95, 120); a = r.uniform(0, TAU)
        X, Y, idx = t.box(x - R - 8, y - R - 8, x + R + 8, y + R + 8)
        d = np.hypot(X - x, Y - y)
        ang = (np.arctan2(Y - y, X - x) - a) % TAU
        notch = (ang < 0.5) & (d < R + 2)
        sd = np.where(notch, 2.0, d - R)
        t.paint(idx, cover(np.hypot(X - x - 5, Y - y - 7) - R) * 0.35, '06262c')
        t.paint(idx, cover(sd), '3e8a3a', rough=0.45)
        t.paint(idx, cover(sd + 6) * 0.35, '55a64a')
        for k in range(7):
            va = a + 0.25 + k * (TAU - 0.5) / 6.5
            t.paint(idx, cover(sd_segment(x, y, x + math.cos(va) * R * 0.9, y + math.sin(va) * R * 0.9, 1.0)(X, Y)) * cover(sd) * 0.4, '2c6a2a')
        if r.uniform() < 0.7:
            fx, fy = x + R * 0.25, y - R * 0.2
            for k in range(8):
                pa = k * TAU / 8 + 0.2
                poly = transform(petal_outline(R * 0.42, R * 0.16, 0.0), fx, fy, pa)
                t.shape(bbox_of(poly), sd_polygon(poly), color=mix('f07aa8', 'ffd9e8', (k % 2) * 0.6))
            t.shape((fx - 10, fy - 10, fx + 10, fy + 10), sd_circle(fx, fy, R * 0.09), color='ffd24a')
    C = [('f1ece2', 'e2541a', '151515'), ('e8631f', 'f3eee4', None), ('f1ece2', 'cf2a1e', None), ('e8631f', '151515', None)]
    for i, (x, y) in enumerate(scatter(r, n, 3, 380, taken=[(x, y, 220) for x, y in pads])):
        L = r.uniform(230, 290); a = r.uniform(0, TAU); body, patch, ink = C[i % 4]
        def P(px, py): return (x + math.cos(a) * px - math.sin(a) * py, y + math.sin(a) * px + math.cos(a) * py)
        outline = [P(L * 0.5 * math.cos(q / 20 * TAU), L * 0.13 * math.sin(q / 20 * TAU) * (1.0 if math.cos(q / 20 * TAU) > 0 else 0.75)) for q in range(20)]
        tail = [P(-L * 0.42, 0), P(-L * 0.62, L * 0.14), P(-L * 0.56, 0), P(-L * 0.62, -L * 0.14)]
        fins = [[P(L * 0.12, L * 0.1), P(-L * 0.02, L * 0.24), P(L * 0.02, L * 0.1)], [P(L * 0.12, -L * 0.1), P(-L * 0.02, -L * 0.24), P(L * 0.02, -L * 0.1)]]
        bb = bbox_of(outline + tail + fins[0] + fins[1], 12)
        X, Y, idx = t.box(*bb)
        sd = sd_polygon(outline)(X, Y)
        t.paint(idx, cover(sd_polygon([(p[0] + 6, p[1] + 8) for p in outline])(X, Y), 6) * 0.3, '05232a')
        for poly in [tail] + fins:
            t.paint(idx, cover(sd_polygon(poly)(X, Y)) * 0.92, mix(body, patch, 0.35))
        t.paint(idx, cover(sd), body)
        for pa, pb, ps in ((0.15, 0.02, 0.28), (-0.12, -0.03, 0.22)):
            cx, cy = P(L * pa, L * pb)
            t.paint(idx, cover(sd_ellipse(cx, cy, L * ps * 0.5, L * 0.09, a)(X, Y)) * cover(sd), patch)
        if ink:
            cx, cy = P(-L * 0.05, L * 0.03)
            t.paint(idx, cover(sd_ellipse(cx, cy, L * 0.06, L * 0.04, a + 0.5)(X, Y)) * cover(sd), ink)
        for side in (1, -1):
            ex, ey = P(L * 0.38, side * L * 0.06)
            t.paint(idx, cover(np.hypot(X - ex, Y - ey) - 2.2), '111111')
    return {}


@design('circuit')
def circuit(t: Tex):
    """circuit board: deep green board, gold traces routed at 45 degrees ending in pads and vias, two chips; the traces
       glow green faintly"""
    n = t.n
    t.rgb[:] = mix('0c3a22', '0f4428', smoothstep(-0.5, 0.5, FBM([2, 4], 241)(t.U, t.V)))
    t.rough[:] = 0.45
    r = t.rng
    g = 32.0
    for i in range(26):
        x, y = r.integers(0, n // 32) * g, r.integers(0, n // 32) * g
        pts = [(x, y)]
        d = r.integers(0, 4)
        for k in range(r.integers(3, 6)):
            L = r.integers(2, 6) * g
            dx, dy = [(1, 0), (0, 1), (-1, 0), (0, -1)][d]
            x, y = x + dx * L, y + dy * L; pts.append((x, y))
            d = (d + (1 if r.uniform() < 0.5 else 3)) % 4
        # 45-degree corners: cut every corner
        sm = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            sm += [(b[0] + (a[0] - b[0]) * 0.3 / max(1, abs(a[0] - b[0]) + abs(a[1] - b[1])) * g, b[1] + (a[1] - b[1]) * 0.3 / max(1, abs(a[0] - b[0]) + abs(a[1] - b[1])) * g),
                   (b[0] + (c[0] - b[0]) * 0.3 / max(1, abs(c[0] - b[0]) + abs(c[1] - b[1])) * g, b[1] + (c[1] - b[1]) * 0.3 / max(1, abs(c[0] - b[0]) + abs(c[1] - b[1])) * g)]
        sm.append(pts[-1])
        wdt = 3.2 if i % 3 else 5.0
        X, Y, idx = t.box(*bbox_of(sm, 16))
        sd = sd_polyline(sm, wdt)(X, Y)
        t.paint(idx, cover(sd), 'b8933a', metal=1.0, rough=0.3, emit=0.0)
        t.paint(idx, cover(sd + wdt * 0.55), 'd8b456', emit=0.7)
        for q in (sm[0], sm[-1]):
            pd = np.hypot(X - q[0], Y - q[1])
            t.paint(idx, cover(pd - 9), 'c9a246', metal=1.0, rough=0.3)
            t.paint(idx, cover(pd - 3.5), '0a2416', metal=0.0)
    for cx, cy, cw, ch in ((300, 520, 150, 96), (760, 200, 110, 110)):
        for k in range(int(cw // 20)):
            px = cx - cw / 2 + 14 + k * 20
            for sy in (-1, 1):
                t.shape((px - 5, cy - ch / 2 - 20, px + 5, cy + ch / 2 + 20), sd_round_rect(px, cy + sy * (ch / 2 + 8), 4, 9, 1.5), color='c8ccd4', metal=1.0, rough=0.25)
        t.shape((cx - cw / 2 - 2, cy - ch / 2 - 2, cx + cw / 2 + 2, cy + ch / 2 + 2), sd_round_rect(cx, cy, cw / 2, ch / 2, 6), color='17181c', rough=0.35, height=1.5)
        t.shape((cx - cw / 2, cy - ch / 2, cx - cw / 2 + 20, cy - ch / 2 + 20), sd_circle(cx - cw / 2 + 12, cy - ch / 2 + 12, 4), color='2c2d33')
    return {'emissive': 1.1, 'tint': '7dff6a'}


@design('stained')
def stained(t: Tex):
    """stained glass: jewel-coloured panes, each a little lighter in its middle, held in raised dark lead; lit from
       behind"""
    n = t.n; r = t.rng
    pts = [(r.uniform(0, n), r.uniform(0, n)) for _ in range(22)]
    d1, d2, ids = voronoi(n, pts)
    pal = [hexrgb(h) for h in ('b8338f', '2f8fb0', 'c9a22e', '3a9a3c', 'b42a2a', '6a3fb8', '2a50b0', 'c8721c')]
    order = r.permutation(len(pts))
    cols = np.stack([pal[order[i] % len(pal)] for i in range(len(pts))])
    base = cols[ids]
    lift = (0.9 + 0.14 * smoothstep(90, 0, d1))[..., None]
    t.rgb[:] = np.clip(base * lift, 0, 1)
    edge = (d2 - d1) * 0.5
    lead = np.clip(3.2 - edge + 0.5, 0, 1)
    t.fill(lead, '1c1a20', rough=0.55)
    t.emit[:] = (1 - lead) * 0.45
    t.height[:] = np.clip(1 - edge / 4.5, 0, 1) * 1.2
    t.rough[:] = np.where(lead > 0.5, 0.55, 0.12)
    return {'emissive': 0.8, 'tint': 'ffffff'}


@design('marble')
def marble(t: Tex):
    """white marble: soft grey clouds and a few branching veins of varying width with a faint haze, polished"""
    U, V = t.U, t.V
    f = FBM([2, 4, 8], 251, 0.55)
    wu, wv = U + 0.08 * f(U, V), V + 0.08 * f(V + 0.3, U)
    t.rgb[:] = mix('dedfdb', 'f1f0ec', smoothstep(-0.5, 0.5, FBM([2, 4], 252)(U, V)))
    t.fill(smoothstep(0.2, 0.6, FBM([3, 6], 257)(wu, wv)) * 0.25, 'c3c4c6')
    g = FBM([(2, 3), (4, 6), (8, 12)], 253, 0.6)(wu, wv)
    gx = (np.roll(g, -1, 1) - np.roll(g, 1, 1)) * 0.5; gy = (np.roll(g, -1, 0) - np.roll(g, 1, 0)) * 0.5
    dist = np.abs(g) / (np.sqrt(gx * gx + gy * gy) + 1e-6)          # pixels to the vein's centre line
    wid = 1.2 + 2.6 * smoothstep(-0.3, 0.6, FBM([4, 8], 254)(U, V))
    keep = smoothstep(-0.45, -0.1, FBM([3, 6], 255)(U, V))           # some veins fade out
    t.fill(np.exp(-dist / (wid * 4)) * 0.22 * keep, 'a7a8ae')
    t.fill(np.clip(wid - dist + 0.5, 0, 1) * keep * 0.85, '62636d')
    g2 = FBM([(4, 4), (8, 8), (16, 16)], 256, 0.6)(wu, wv)
    gx = (np.roll(g2, -1, 1) - np.roll(g2, 1, 1)) * 0.5; gy = (np.roll(g2, -1, 0) - np.roll(g2, 1, 0)) * 0.5
    d2 = np.abs(g2) / (np.sqrt(gx * gx + gy * gy) + 1e-6)
    t.fill(np.clip(0.9 - d2 + 0.5, 0, 1) * smoothstep(0.1, 0.45, FBM([3, 6], 258)(U, V)) * 0.5, '8e8f99')
    t.rough[:] = 0.14
    return {}


@design('wood')
def wood(t: Tex):
    """wood: straight walnut-brown grain along the gun, darker latewood lines and the odd soft figure"""
    U, V = t.U, t.V
    w = FBM([(1, 4), (2, 8)], 261, 0.5)(U, V)
    ring = (V * 14 + 0.9 * w + 0.15 * FBM([(2, 2), (4, 4)], 262)(U, V)) % 1.0
    late = smoothstep(0.55, 0.75, ring) * (1 - smoothstep(0.8, 0.98, ring))
    t.rgb[:] = mix('8a5a32', 'a26c3e', smoothstep(-0.5, 0.5, FBM([(1, 3), (2, 6)], 263)(U, V)))
    t.fill(late * 0.75, '5e3a1f')
    fib = np.sin((V * 160 + 3 * w) * TAU) * 0.5 + 0.5
    t.fill(fib * 0.06, '3a2412')
    t.height[:] = -late * 0.5
    t.normal_k = 0.8
    t.rough[:] = 0.58 + 0.1 * late
    return {}


@design('lava')
def lava(t: Tex):
    """lava: black basalt plates floating on glowing rock, the cracks white-hot in the middle"""
    n = t.n; r = t.rng
    pts = [(r.uniform(0, n), r.uniform(0, n)) for _ in range(30)]
    d1, d2, ids = voronoi(n, pts)
    edge = (d2 - d1) * 0.5 + 6 * FBM([6, 12], 271)(t.U, t.V)
    crust = mix('1c0e0b', '33190f', smoothstep(-0.5, 0.5, FBM([4, 8], 272)(t.U, t.V)))
    t.rgb[:] = crust
    hot = 1 - smoothstep(0, 14, edge)
    core = 1 - smoothstep(0, 5, edge)
    t.fill(hot, 'a8240a'); t.fill(hot * hot, 'ff6a12'); t.fill(core, 'ffd24a')
    t.emit[:] = np.clip(hot * 0.9 + core * 0.4, 0, 1)
    t.height[:] = smoothstep(2, 16, edge) * 2.0
    t.rough[:] = 0.75 - 0.4 * hot
    return {'emissive': 2.2, 'tint': 'ffffff'}


@design('brushed')
def brushed(t: Tex):
    """brushed steel: long fine streaks running along the gun"""
    n = t.n
    r = t.rng
    rows = r.normal(0, 1, n).astype(np.float32)
    rows = blur_wrap(np.tile(rows[:, None], (1, 8)), 1)[:, 0]
    rows2 = np.repeat(r.normal(0, 1, n // 8).astype(np.float32), 8)
    along = FBM([(8, 1), (16, 2)], 281)(t.U, t.V)
    lum = 0.7 + 0.05 * rows[:, None] + 0.035 * rows2[:, None] + 0.03 * along
    t.rgb[:] = np.clip(lum[..., None] * np.array([0.98, 1.0, 1.04], np.float32), 0, 1)
    t.metal[:] = 1.0
    t.rough[:] = 0.3 + 0.06 * np.abs(rows)[:, None]
    return {}


@design('copper')
def copper(t: Tex):
    """verdigris: polished copper going green, the patina in soft-edged patches that are matte where the copper shines"""
    U, V = t.U, t.V
    f = FBM([(2, 3), (4, 6), (8, 12)], 291, 0.5)(U, V)
    g = FBM([8, 16], 292, 0.5)(U, V)
    pat = smoothstep(0.02, 0.12, f + 0.25 * g)
    t.rgb[:] = mix('a65a33', 'c47a4a', smoothstep(-0.5, 0.5, FBM([3, 6], 293)(U, V)))
    t.fill(pat, mix('3f8c74', '5fae92', smoothstep(-0.3, 0.4, g)))
    t.fill(pat * (1 - smoothstep(0.12, 0.3, f + 0.25 * g)) * 0.5, '2f6a58')
    t.metal[:] = 1 - pat
    t.rough[:] = 0.28 + 0.5 * pat
    t.height[:] = pat * 0.8
    return {}


@design('bubblewrap')
def bubblewrap(t: Tex):
    """bubble wrap: a pale blue sheet of round bubbles in a hex grid, each a glossy dome with a highlight; a few popped"""
    n = t.n
    dx = n / 16.0; dy = n / 18.0
    t.rgb[:] = hexrgb('b9d6e2')
    r = t.rng
    for j in range(18):
        for i in range(16):
            x = i * dx + (dx / 2 if j % 2 else 0); y = j * dy + dy / 2
            R = dy * 0.48
            X, Y, idx = t.box(x - R - 2, y - R - 2, x + R + 2, y + R + 2)
            d = np.hypot(X - x, Y - y)
            if r.uniform() < 0.07:
                t.paint(idx, cover(d - R * 0.85) * 0.5, 'a3c4d2'); continue
            dome = np.sqrt(np.clip(1 - (d / R) ** 2, 0, 1))
            t.paint(idx, cover(d - R), mix('a9cad8', 'd8eef6', dome))
            t.paint(idx, cover(np.hypot(X - x + R * 0.35, Y - y + R * 0.38) - R * 0.16), 'ffffff')
            t.paint(idx, cover(d - R), height=dome * 3.0, hmode='max')
    t.rough[:] = 0.12
    return {}


@design('nebula')
def nebula(t: Tex):
    """nebula: deep violet space full of glowing pink and blue gas, fine round stars and a few four-point twinkles"""
    n, U, V = t.n, t.U, t.V
    wu, wv = U + 0.1 * FBM([2, 4], 301)(U, V), V + 0.1 * FBM([2, 4], 302)(U, V)
    a = smoothstep(-0.1, 0.6, FBM([2, 4, 8, 16], 303, 0.55)(wu, wv))
    b = smoothstep(-0.05, 0.6, FBM([3, 6, 12], 304, 0.55)(wu + 0.37, wv))
    t.rgb[:] = hexrgb('120a2a')
    t.fill(a * 0.85, '7a48d8'); t.fill(a * a * 0.6, 'd65ac4'); t.fill(b * (1 - a * 0.6) * 0.7, '2e5ad0')
    t.fill((a * b) * 0.5, 'f2a6e6')
    t.emit[:] = np.clip(a * 0.35 + b * 0.25, 0, 1)
    t.rough[:] = 0.3
    r = t.rng
    for _ in range(500):
        x, y = r.uniform(0, n), r.uniform(0, n)
        rad = r.uniform(1.0, 2.2)
        t.shape((x - 4, y - 4, x + 4, y + 4), sd_circle(x, y, rad), color='ffffff', emit=0.9)
    for x, y in scatter(r, n, 9, 200):
        ro = r.uniform(14, 26)
        X, Y, idx = t.box(x - ro * 1.5, y - ro * 1.5, x + ro * 1.5, y + ro * 1.5)
        sd = sd_sparkle(x, y, ro, 0.14, 0)(X, Y)
        halo = np.exp(-np.maximum(np.hypot(X - x, Y - y), 0) / (ro * 0.3)) * 0.5
        t.paint(idx, halo, 'f0d0ff', emit=halo)
        t.paint(idx, cover(sd), '#ffffff', emit=1.0)
    return {'emissive': 1.3, 'tint': 'ffffff'}


@design('sweater')
def sweater(t: Tex):
    """ugly sweater: real knit stitches (each a little V of two loops) in red, white and green: a zigzag band,
       snowflakes, and a row of fir trees"""
    n = t.n; c = 32                                   # one stitch is 32 px across (8 mm), 32 rows to the tile
    R, W, G = 'a8202c', 'ece6d8', '1f5f34'
    art = []
    for j in range(32):
        row = []
        for i in range(32):
            col = R
            if j < 5:
                col = G
                if 1 <= j <= 4 and j - 1 == abs((i % 6) - 3): col = W
            elif 7 <= j <= 15:
                cx, cy = (i % 16) - 8, j - 11
                if (cx == 0 and abs(cy) <= 4) or (cy == 0 and abs(cx) <= 4) or (abs(cx) == abs(cy) and abs(cx) <= 3): col = W
            elif j == 17 or j == 30: col = W if i % 2 == 0 else G
            elif 19 <= j <= 28:
                cx = (i % 11) - 5; h = j - 19
                if h < 8 and abs(cx) <= h // 2 + (1 if h % 2 else 0) // 2: col = G
                if h >= 8 and cx == 0: col = '5a3a22'
            row.append(col)
        art.append(row)
    X, Y = t.X, t.Y
    i, j = (X // c).astype(int) % 32, (Y // c).astype(int) % 32
    fx, fy = (X % c) / c, (Y % c) / c
    cols = {k: hexrgb(k) for k in {x for row in art for x in row}}
    lut = np.zeros((32, 32, 3), np.float32)
    for jj in range(32):
        for ii in range(32): lut[jj, ii] = cols[art[jj][ii]]
    base = lut[j, i]
    # a stitch: two slanted loops meeting at the bottom middle, rounded in relief
    def loop(cx):
        ax, ay = cx, 0.08; bx, by = 0.5, 0.95
        ex, ey = bx - ax, by - ay
        tt = np.clip(((fx - ax) * ex + (fy - ay) * ey) / (ex * ex + ey * ey), 0, 1)
        return np.hypot(fx - ax - ex * tt, fy - ay - ey * tt)
    d = np.minimum(loop(0.12), loop(0.88))
    h = np.clip(1 - d / 0.26, 0, 1)
    h = np.sqrt(h)
    t.rgb[:] = base * (0.55 + 0.45 * h)[..., None]
    t.height[:] = h * 4.0
    t.normal_k = 0.7
    t.rough[:] = 0.95
    return {}


@design('titanium')
def titanium(t: Tex):
    """anodized titanium: heat-tint bands flowing from gold through purple and blue to teal, on bright metal"""
    U, V = t.U, t.V
    w = FBM([2, 4], 311, 0.5)(U, V)
    tt = ((U * 2 + V * 1) + 0.55 * w) % 1.0
    stops = np.array([[0.82, 0.64, 0.26], [0.66, 0.32, 0.66], [0.38, 0.28, 0.78], [0.2, 0.5, 0.86], [0.22, 0.72, 0.7], [0.82, 0.64, 0.26]], np.float32)
    f = tt * 5; i = np.floor(f).astype(int); u = (f - i)[..., None]
    u = u * u * (3 - 2 * u)
    t.rgb[:] = stops[i] + (stops[np.minimum(i + 1, 5)] - stops[i]) * u
    t.metal[:] = 1.0
    t.rough[:] = 0.22
    return {}


@design('hivis')
def hivis(t: Tex):
    """hi-vis: safety orange fabric with a silver reflective band edged in yellow-green, stitched along both edges"""
    n = t.n
    t.rgb[:] = hexrgb('e2611a')
    weave = (np.sin(t.X * TAU / 6) * np.sin(t.Y * TAU / 6))
    t.height[:] = weave * 0.25
    y0 = n * 0.38
    for a, b, col in ((y0 - 70, y0 + 230, 'c9e23a'), (y0 - 40, y0 + 200, 'b9bec6')):
        t.fill(cover(np.maximum(a - t.Y, t.Y - b)), col)
    band = cover(np.maximum((y0 - 40) - t.Y, t.Y - (y0 + 200)))
    sheen = 0.06 * np.sin(t.Y * TAU / 12)
    t.rgb[:] = t.rgb + (band * sheen)[..., None]
    t.metal[:] = band * 0.6
    t.rough[:] = 0.85 - 0.55 * band
    for yy in (y0 - 56, y0 + 216):
        for x in range(0, n, 24):
            t.shape((x - 2, yy - 4, x + 14, yy + 4), sd_segment(x + 2, yy, x + 12, yy, 1.6), color='2a2a2a')
    t.normal_k = 0.8
    return {}


# ====================================================================== batch 3
def tri(x):
    """a smooth triangle wave of period 1, 0..1..0"""
    f = x % 1.0
    v = 1 - np.abs(2 * f - 1)
    return v * v * (3 - 2 * v)


def hsv(h, s, v):
    k = lambda m: (m + h * 6) % 6
    f = lambda m: v - v * s * np.clip(np.minimum(k(m), 4 - k(m)), 0, 1)
    return np.stack([f(5), f(3), f(1)], -1)


@design('fade')
def fade(t: Tex):
    """fade: hot pink melting into cyan on a long diagonal, with a soft pearl sheen where they meet"""
    k = tri(t.V + 0.08 * np.sin(t.U * TAU) + 0.06 * FBM([2], 321)(t.U, t.V))
    t.rgb[:] = mix('d8509f', '36a8d6', k)
    t.fill(np.exp(-((k - 0.5) / 0.12) ** 2) * 0.18, 'f4e8ff')
    t.rough[:] = 0.22
    return {}


@design('rainbow')
def rainbow(t: Tex):
    """rainbow: the full spectrum in broad, smooth diagonal bands, deep enough to read under the lamps"""
    h = (t.V + 0.06 * np.sin(t.U * TAU) + 0.04 * FBM([2], 331)(t.U, t.V)) % 1.0
    t.rgb[:] = hsv(h, 0.72, 0.86)
    t.rough[:] = 0.24
    return {}


@design('missing')
def missing(t: Tex):
    """missing texture: the magenta and black checks, crisp, the magenta lit from inside like an engine fallback"""
    def wave(x, cell):
        f = x % (2 * cell)
        e = np.where(f < cell, np.minimum(f, cell - f), -np.minimum(f - cell, 2 * cell - f))
        return np.clip(0.5 + e, 0, 1) * 2 - 1
    q = (1 + wave(t.X, 128.0) * wave(t.Y, 128.0)) / 2
    t.rgb[:] = hexrgb('0b0b0d')
    t.fill(q, 'd400b8', emit=0.55)
    t.rough[:] = 0.4
    return {'emissive': 0.8, 'tint': 'ffffff'}


@design('ketchup')
def ketchup(t: Tex):
    """ketchup and mustard: glossy tomato red with two zigzag lines of mustard piped across it"""
    n = t.n
    t.rgb[:] = mix('ae1720', 'c62128', smoothstep(-0.5, 0.5, FBM([2, 4], 341)(t.U, t.V)))
    t.rough[:] = 0.2
    for y0 in (n * 0.25, n * 0.75):
        pts = [(x, y0 + (36 if (k % 2) else -36)) for k, x in enumerate(np.arange(-128, n + 129, 64.0))]
        X, Y, idx = t.box(-140, y0 - 70, n + 140, y0 + 70)
        sd = sd_polyline(pts, 17)(X, Y)
        dome = np.sqrt(np.clip(-sd / 17, 0, 1))
        t.paint(idx, cover(sd - 3) * 0.35, '6a0c10')
        t.paint(idx, cover(sd), mix('c99412', 'eec23a', dome))
        t.paint(idx, cover(sd), height=dome * 4, hmode='max')
        t.paint(idx, cover(sd_polyline([(x - 5, y - 6) for x, y in pts], 3.5)(X, Y)) * cover(sd) * 0.7, 'fff0b0')
    return {}


@design('creamsicle')
def creamsicle(t: Tex):
    """creamsicle: orange sherbet swirled with vanilla cream, a thin peach line where they fold"""
    U, V = t.U, t.V
    w = FBM([2, 4], 351)(U, V)
    s = np.sin((V * 3 + 0.35 * np.sin(U * TAU * 1 + 1.3) + 0.5 * w) * TAU)
    t.rgb[:] = hexrgb('e2701e')
    t.fill(field_cover(s, 0.1), 'f6c690')
    t.fill(field_cover(s, 0.28), 'f2e6cc')
    t.rough[:] = 0.3
    return {}


@design('bubblegum')
def bubblegum(t: Tex):
    """bubblegum: soft pink with pale blue bubbles of every size, each with a rim and a window highlight"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('d97aa8', 'e88cb8', smoothstep(-0.5, 0.5, FBM([2, 4], 361)(t.U, t.V)))
    t.rough[:] = 0.25
    for x, y in scatter(r, n, 26, 95):
        R = r.uniform(18, 54)
        X, Y, idx = t.box(x - R - 3, y - R - 3, x + R + 3, y + R + 3)
        d = np.hypot(X - x, Y - y)
        t.paint(idx, cover(d - R), mix('8fd0ec', 'b8e4f4', smoothstep(R, 0, d)))
        t.paint(idx, cover(np.abs(d - R + 1.5) - 1.5) * 0.8, '5ea8cc')
        t.paint(idx, cover(sd_ellipse(x - R * 0.38, y - R * 0.4, R * 0.24, R * 0.12, -0.7)(X, Y)), 'ffffff')
        t.paint(idx, cover(d - R), height=np.sqrt(np.clip(1 - (d / R) ** 2, 0, 1)) * 3, hmode='max')
    return {}


@design('china')
def china(t: Tex):
    """grandma's china: glossy white porcelain with cobalt medallions of rings, petals and dots, and little sprigs"""
    n = t.n
    t.rgb[:] = hexrgb('eef1f6')
    t.rough[:] = 0.1
    co, lt = '1f43a0', '6f8fd6'
    def medal(cx, cy, s=1.0):
        X, Y, idx = t.box(cx - 140 * s, cy - 140 * s, cx + 140 * s, cy + 140 * s)
        d = np.hypot(X - cx, Y - cy)
        t.paint(idx, cover(np.abs(d - 118 * s) - 6 * s), co)
        t.paint(idx, cover(np.abs(d - 100 * s) - 2.5 * s), lt)
        for i in range(20):
            a = i / 20 * TAU
            t.paint(idx, cover(np.hypot(X - cx - math.cos(a) * 109 * s, Y - cy - math.sin(a) * 109 * s) - 3.5 * s), co)
        for i in range(8):
            a = i / 8 * TAU
            poly = transform(petal_outline(64 * s, 24 * s, 0.12), cx + math.cos(a) * 12 * s, cy + math.sin(a) * 12 * s, a)
            sd = sd_polygon(poly)(X, Y)
            t.paint(idx, cover(sd), co)
            t.paint(idx, cover(sd + 6 * s), lt)
        for i in range(8):
            a = (i + 0.5) / 8 * TAU
            t.paint(idx, cover(sd_ellipse(cx + math.cos(a) * 64 * s, cy + math.sin(a) * 64 * s, 12 * s, 5 * s, a)(X, Y)), lt)
        t.paint(idx, cover(d - 16 * s), co); t.paint(idx, cover(d - 7 * s), 'eef1f6')
    def sprig(cx, cy):
        X, Y, idx = t.box(cx - 130, cy - 130, cx + 130, cy + 130)
        for i in range(4):
            a = i / 4 * TAU + 0.4
            t.paint(idx, cover(sd_segment(cx, cy, cx + math.cos(a) * 100, cy + math.sin(a) * 100, 3.5)(X, Y)), co)
            poly = transform(petal_outline(64, 24, 0.0), cx + math.cos(a) * 30, cy + math.sin(a) * 30, a)
            t.paint(idx, cover(sd_polygon(poly)(X, Y)), lt)
            for b in (-0.5, 0.5):
                ex, ey = cx + math.cos(a + b) * 96, cy + math.sin(a + b) * 96
                t.paint(idx, cover(np.hypot(X - ex, Y - ey) - 8), co)
        t.paint(idx, cover(np.hypot(X - cx, Y - cy) - 16), co)
    for cx, cy in ((n * 0.25, n * 0.25), (n * 0.75, n * 0.75)): medal(cx, cy, 1.75)
    for cx, cy in ((n * 0.75, n * 0.25), (n * 0.25, n * 0.75)): sprig(cx, cy)
    return {}


@design('asanoha')
def asanoha(t: Tex):
    """asanoha: the hemp-leaf star lattice in fine pale lines on a deep rose ground"""
    n = t.n
    a = n / 7.0; h = n / 8.0                      # 7 triangles across, 8 rows down (1% off equilateral)
    t.rgb[:] = hexrgb('a8244f')
    t.rough[:] = 0.4
    def P(i, j): return ((i + (j % 2) * 0.5) * a, j * h)
    X, Y = t.X, t.Y
    d = np.full(X.shape, 1e9, np.float32)
    segs = []
    for j in range(-1, 10):
        for i in range(-2, 9):
            for A, B, C in ((P(i, j), P(i + 1, j), P(i + (j % 2), j + 1)), (P(i, j + 1), P(i + 1, j + 1), P(i + ((j + 1) % 2), j))):
                G = ((A[0] + B[0] + C[0]) / 3, (A[1] + B[1] + C[1]) / 3)
                segs += [(A, B, 2.6), (B, C, 2.6), (C, A, 2.6), (A, G, 1.6), (B, G, 1.6), (C, G, 1.6)]
    for (ax, ay), (bx, by), w in segs:
        x0, x1 = min(ax, bx) - 4, max(ax, bx) + 4; y0, y1 = min(ay, by) - 4, max(ay, by) + 4
        if x1 < -8 or x0 > n + 8 or y1 < -8 or y0 > n + 8: continue
        Xb, Yb, idx = t.box(x0, y0, x1, y1)
        sd = sd_segment(ax, ay, bx, by, w)(Xb, Yb)
        t.paint(idx, cover(sd), 'f6dbe6' if w > 2 else 'e9b4c8')
    return {}


@design('shibori')
def shibori(t: Tex):
    """shibori: indigo-dyed cloth with soft-edged white spider-web circles where the cloth was bound"""
    n = t.n
    m = np.zeros((n, n), np.float32)
    def kumo(cx, cy, R):
        X, Y, idx = t.box(cx - R - 8, cy - R - 8, cx + R + 8, cy + R + 8)
        d = np.hypot(X - cx, Y - cy)
        v = np.zeros(X.shape, np.float32)
        for rr in (0.22, 0.52, 0.82):
            v = np.maximum(v, cover(np.abs(d - R * rr) - 5, 2.0))
        ang = np.arctan2(Y - cy, X - cx)
        spokes = cover((np.abs(np.sin(ang * 6)) * d) - 2.5, 2.0) * cover(d - R * 0.9) * (d > R * 0.12)
        v = np.maximum(v, spokes * 0.8)
        m[idx] = np.maximum(m[idx], v)
    for j in range(3):
        for i in range(3):
            kumo((i + 0.5 * (j % 2)) * n / 3 + n / 6, (j + 0.5) * n / 3, n / 7.5)
    m = blur_wrap(m, 2)
    t.rgb[:] = mix('1b2656', '25336e', smoothstep(-0.5, 0.5, FBM([3, 6], 371)(t.U, t.V)))
    t.fill(np.clip(m * 1.15, 0, 1), 'c9d4ee')
    t.rough[:] = 0.85
    return {}


@design('washi')
def washi(t: Tex):
    """washi paper: warm cream paper with long fibres laid in it, and a few pressed petals and a leaf"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('e9dcc0', 'f2e7d0', smoothstep(-0.5, 0.5, FBM([3, 6], 381)(t.U, t.V)))
    t.rough[:] = 0.9
    for k in range(70):
        x, y, a = r.uniform(0, n), r.uniform(0, n), r.uniform(0, TAU)
        L = r.uniform(40, 120); bend = r.uniform(-0.6, 0.6)
        pts = [(x + math.cos(a + bend * q / 6) * L * q / 6, y + math.sin(a + bend * q / 6) * L * q / 6) for q in range(7)]
        col = 'c2a985' if k % 5 else 'fbf6ea'
        t.shape(bbox_of(pts, 4), sd_polyline(pts, 0.9), color=col)
    for i, (x, y) in enumerate(scatter(r, n, 5, 300)):
        a = r.uniform(0, TAU)
        if i == 2:
            poly = transform(petal_outline(70, 26, 0.0), x, y, a)
            t.shape(bbox_of(poly), sd_polygon(poly), color='8aa868')
            t.shape(bbox_of(poly), sd_segment(x, y, x + math.cos(a) * 66, y + math.sin(a) * 66, 1.2), color='6a8a4c')
        else:
            for k in range(5):
                pa = a + k * TAU / 5
                poly = transform(petal_outline(26, 11, 0.16), x, y, pa)
                t.shape(bbox_of(poly), sd_polygon(poly), color=mix('e88aa8', 'f2b8c8', (k % 2) * 0.6))
            t.shape((x - 6, y - 6, x + 6, y + 6), sd_circle(x, y, 3.5), color='e8b440')
    return {}


@design('bigwave')
def bigwave(t: Tex):
    """big wave: navy waves with lighter lines and cream foam curling off the crests, over warm paper, a red sun"""
    n = t.n
    t.rgb[:] = hexrgb('e3d3ac')
    t.rough[:] = 0.6
    t.shape((n * 0.72, n * 0.08, n * 0.92, n * 0.28), sd_circle(n * 0.82, n * 0.18, n * 0.075), color='c43a34')
    for base, ph in ((n * 0.36, 0.4), (n * 0.86, 2.6)):
        def yf(x): return base + 26 * math.sin(TAU * x / 256 + ph) - 70 * max(0.0, math.sin(TAU * x / 512 + ph)) ** 3
        xs = np.arange(-16, n + 17, 4.0)
        top = [(x, yf(x)) for x in xs]
        poly = top + [(n + 16, base + 300), (-16, base + 300)]
        X, Y, idx = t.box(-16, base - 120, n + 16, base + 300)
        sd = sd_polygon(poly)(X, Y)
        t.paint(idx, cover(sd), '1b3a6c')
        for off, col, w in ((22, '3f6aa6', 4), (44, '2a5592', 3.5), (70, '4a7cb8', 3), (100, '2a5592', 3), (135, '16305c', 4)):
            t.paint(idx, cover(sd_polyline([(x, y + off) for x, y in top], w)(X, Y)) * cover(sd), col)
        t.paint(idx, cover(sd_polyline(top, 5)(X, Y)), 'f3ecd8')
        for x in range(0, n, 24):
            k = max(0.0, math.sin(TAU * x / 512 + ph)) ** 3
            if k > 0.3:
                cx, cy = x - 4, yf(x) - 10
                R = 9 + 10 * k
                Xb, Yb, idb = t.box(cx - R - 4, cy - R - 4, cx + R + 4, cy + R + 4)
                d = np.hypot(Xb - cx, Yb - cy)
                ang = np.arctan2(Yb - cy, Xb - cx)
                arc = cover(np.abs(d - R) - 3) * ((ang > -2.8) & (ang < 0.6))
                t.paint(idb, arc, 'f3ecd8')
    return {}


@design('urushi')
def urushi(t: Tex):
    """urushi maki-e: deep black lacquer, a red lacquer sash across it, gold vines and plum blossoms"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('0d0708')
    s = (t.X + t.Y) % n
    sash = cover(np.abs(s - n * 0.68) - n * 0.13)
    t.fill(sash, '7e1018')
    t.fill(cover(np.abs(np.abs(s - n * 0.68) - n * 0.13) - 2.5), 'b88a34', metal=1.0)
    t.rough[:] = 0.08
    x, y, a = n * 0.15, n * 0.3, 0.3
    for vine in range(4):
        if vine == 2: x, y, a = n * 0.35, n * 0.55, 1.9
        if vine == 3: x, y, a = n * 0.85, n * 0.1, 2.6
        for k in range(7):
            r0 = r.uniform(50, 80)
            ax, ay = x + math.cos(a) * r0, y + math.sin(a) * r0
            pts = [(ax + math.cos(a + math.pi + q / 8 * 2.2) * r0, ay + math.sin(a + math.pi + q / 8 * 2.2) * r0) for q in range(9)]
            t.shape(bbox_of(pts, 8), sd_polyline(pts, [4.2 - q * 0.3 for q in range(9)]), color='d4a443', metal=1.0, rough=0.2)
            lx, ly = ax + math.cos(a + 1.2) * r0, ay + math.sin(a + 1.2) * r0
            poly = transform(petal_outline(40, 16, 0.0), lx, ly, a + 1.2)
            t.shape(bbox_of(poly), sd_polygon(poly), color='e8c068', metal=1.0, rough=0.2)
            x, y = ax + math.cos(a + 2.2) * r0, ay + math.sin(a + 2.2) * r0
            a += 2.2 - math.pi + r.uniform(-0.5, 0.5)
        x, y, a = n * 0.6, n * 0.85, -1.3
    for px, py in scatter(r, n, 7, 240):
        for k in range(5):
            pa = k * TAU / 5
            t.shape((px - 60, py - 60, px + 60, py + 60), sd_circle(px + math.cos(pa) * 22, py + math.sin(pa) * 22, 19), color='d9aa48', metal=1.0, rough=0.2)
        t.shape((px - 14, py - 14, px + 14, py + 14), sd_circle(px, py, 9), color='9e1620', metal=0.0)
    return {}


@design('tokyo')
def tokyo(t: Tex):
    """tokyo night: a dark city of lit windows behind neon signs that glow, each sign an outlined box with simple neon
       marks inside (bars, rings, arrows: no letters or glyphs)"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('0a0816')
    for k in range(40):
        x, y = r.uniform(0, n), r.uniform(0, n)
        w, h = r.uniform(60, 160), r.uniform(150, 400)
        t.shape((x - w / 2, y - h / 2, x + w / 2, y + h / 2), sd_round_rect(x, y, w / 2, h / 2, 3), color=mix('141028', '1d1838', r.uniform()))
    for k in range(260):
        x, y = r.uniform(0, n), r.uniform(0, n)
        t.shape((x - 6, y - 6, x + 6, y + 6), sd_round_rect(x, y, 3, 4, 1), color='e8c870' if r.uniform() < 0.6 else '7ab4e8', emit=0.5)
    cols = ['ff4fc4', '4fd0ff', 'ffd84a', '5aff7a', 'ff5a4a', 'ff9a3a']
    for x, y in scatter(r, n, 11, 210):
        vert = r.uniform() < 0.5
        w, h = (r.uniform(46, 64), r.uniform(150, 230)) if vert else (r.uniform(150, 230), r.uniform(46, 64))
        c1, c2 = cols[r.integers(0, 6)], cols[r.integers(0, 6)]
        X, Y, idx = t.box(x - w / 2 - 14, y - h / 2 - 14, x + w / 2 + 14, y + h / 2 + 14)
        sd = sd_round_rect(x, y, w / 2, h / 2, 6)(X, Y)
        t.paint(idx, cover(sd), '120c22')
        ring = cover(np.abs(sd + 4) - 2.2)
        halo = np.exp(-np.abs(sd + 4) / 7) * 0.45
        t.paint(idx, halo, c1, emit=halo)
        t.paint(idx, ring, c1, emit=1.0)
        kind = r.integers(0, 3)
        if kind == 0:     # stacked neon bars
            for q in range(3):
                f = (q - 1) * 0.28
                ax, ay = (x - w * 0.28, y + f * h) if vert else (x - w * 0.36, y + f * h * 0.9)
                bx, by = (x + w * 0.28, y + f * h) if vert else (x + w * (0.1 + 0.25 * r.uniform()), y + f * h * 0.9)
                if not vert: ay = by = y + (q - 1) * h * 0.25
                t.paint(idx, cover(sd_segment(ax, ay, bx, by, 2.4)(X, Y)), c2, emit=1.0)
        elif kind == 1:   # a ring and a dot
            rr = min(w, h) * 0.26
            t.paint(idx, cover(np.abs(np.hypot(X - x, Y - y) - rr) - 2.4), c2, emit=1.0)
            t.paint(idx, cover(np.hypot(X - x, Y - y) - rr * 0.3), c2, emit=1.0)
        else:             # an arrow
            L = (h if vert else w) * 0.3
            ang = math.pi / 2 if vert else 0.0
            ax, ay = x - math.cos(ang) * L, y - math.sin(ang) * L
            bx, by = x + math.cos(ang) * L, y + math.sin(ang) * L
            t.paint(idx, cover(sd_segment(ax, ay, bx, by, 2.4)(X, Y)), c2, emit=1.0)
            for s_ in (-1, 1):
                hx, hy = bx - math.cos(ang + s_ * 0.6) * L * 0.4, by - math.sin(ang + s_ * 0.6) * L * 0.4
                t.paint(idx, cover(sd_segment(bx, by, hx, hy, 2.4)(X, Y)), c2, emit=1.0)
    t.rough[:] = 0.25
    return {'emissive': 1.6, 'tint': 'ffffff'}


@design('cheese')
def cheese(t: Tex):
    """swiss cheese: buttery yellow with round holes of every size, each a shaded hollow"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('dfa828', 'ecbc3c', smoothstep(-0.5, 0.5, FBM([2, 4], 391)(t.U, t.V)))
    t.rough[:] = 0.5
    for x, y in scatter(r, n, 24, 110):
        R = r.uniform(12, 50)
        X, Y, idx = t.box(x - R - 6, y - R - 6, x + R + 6, y + R + 6)
        d = np.hypot(X - x, Y - y)
        t.paint(idx, cover(d - R - 3) * 0.6, 'c88f1a')
        inner = np.clip(np.hypot(X - x - R * 0.25, Y - y - R * 0.3) / R, 0, 1)
        t.paint(idx, cover(d - R), mix('8e5a0c', 'd29a24', inner))
        t.paint(idx, cover(d - R), height=-(1 - (d / R) ** 2) * 6, hmode='mix')
    return {}


@design('pizza')
def pizza(t: Tex):
    """pizza: golden melted cheese with lighter pools, pepperoni slices, basil leaves and the odd olive ring"""
    n = t.n; r = t.rng
    U, V = t.U, t.V
    t.rgb[:] = mix('d79a26', 'eab43e', smoothstep(-0.4, 0.6, FBM([3, 6, 12], 401)(U, V)))
    t.fill(field_cover(FBM([4, 8], 402)(U, V), 0.25) * 0.6, 'f4d06a')
    t.rough[:] = 0.4
    pep = scatter(r, n, 9, 230)
    for x, y in pep:
        R = r.uniform(54, 66)
        X, Y, idx = t.box(x - R - 8, y - R - 8, x + R + 8, y + R + 8)
        d = np.hypot(X - x, Y - y)
        t.paint(idx, cover(d - R - 4, 3) * 0.4, '7a3a06')
        t.paint(idx, cover(d - R), '8e1a14')
        t.paint(idx, cover(d - R + 5), 'b0261c')
        for k in range(7):
            sx, sy = x + r.uniform(-0.6, 0.6) * R, y + r.uniform(-0.6, 0.6) * R
            t.paint(idx, cover(np.hypot(X - sx, Y - sy) - r.uniform(3, 6)) * cover(d - R + 6), '7a1410')
        t.paint(idx, cover(sd_ellipse(x - R * 0.35, y - R * 0.38, R * 0.22, R * 0.09, -0.7)(X, Y)) * 0.5, 'ffb8a0')
        t.paint(idx, cover(d - R), height=2.5, hmode='max')
    for x, y in scatter(r, n, 6, 150, taken=[(x, y, 120) for x, y in pep]):
        a = r.uniform(0, TAU)
        poly = transform(petal_outline(56, 24, 0.0), x, y, a)
        t.shape(bbox_of(poly), sd_polygon(poly), color='2f7a2a')
        t.shape(bbox_of(poly), sd_segment(x, y, x + math.cos(a) * 52, y + math.sin(a) * 52, 1.4), color='4a9a3a')
    for x, y in scatter(r, n, 5, 150, taken=[(x, y, 110) for x, y in pep]):
        t.shape((x - 20, y - 20, x + 20, y + 20), lambda X, Y, x=x, y=y: np.abs(np.hypot(X - x, Y - y) - 11) - 5, color='1c1814')
    return {}


@design('sprinkles')
def sprinkles(t: Tex):
    """sprinkles: pink frosting covered in rounded rod sprinkles in six candy colours, every one at its own angle"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('d97aa6', 'e58bb4', smoothstep(-0.5, 0.5, FBM([2, 4], 411)(t.U, t.V)))
    t.rough[:] = 0.35
    cols = ['f2d040', '4ab8e0', '6ad050', 'f6f2ea', 'e04848', '9a6ae0']
    for x, y in scatter(r, n, 220, 34):
        a = r.uniform(0, TAU); L = r.uniform(11, 15)
        ax, ay, bx, by = x - math.cos(a) * L, y - math.sin(a) * L, x + math.cos(a) * L, y + math.sin(a) * L
        X, Y, idx = t.box(min(ax, bx) - 8, min(ay, by) - 8, max(ax, bx) + 8, max(ay, by) + 8)
        sd = sd_segment(ax, ay, bx, by, 5.0)(X, Y)
        c = cols[r.integers(0, 6)]
        t.paint(idx, cover(sd - 1.5, 2) * 0.25, '7a3050')
        t.paint(idx, cover(sd), c)
        t.paint(idx, cover(sd_segment(ax - 1.5, ay - 1.5, bx - 1.5, by - 1.5, 1.5)(X, Y)) * cover(sd) * 0.4, 'ffffff')
        t.paint(idx, cover(sd), height=np.sqrt(np.clip(-sd / 5, 0, 1)) * 2.5, hmode='max')
    return {}


@design('watermelon')
def watermelon(t: Tex):
    """watermelon: juicy red flesh with black teardrop seeds, a rind band of pale and striped green"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('c83850', 'dc4a62', smoothstep(-0.5, 0.5, FBM([2, 4], 421)(t.U, t.V)))
    t.rough[:] = 0.35
    y0 = n * 0.8
    t.fill(cover(np.maximum(y0 - t.Y, t.Y - (y0 + 30))), 'ecebc8')
    t.fill(cover(np.maximum((y0 + 30) - t.Y, t.Y - (y0 + 52))), '8cc85a')
    t.fill(cover(np.maximum((y0 + 52) - t.Y, t.Y - n)), '2f6a2a')
    stripes = np.sin((t.X / n * 12 + 0.6 * FBM([(4, 2)], 422)(t.U, t.V)) * TAU)
    t.fill(field_cover(stripes, 0.3) * cover(np.maximum((y0 + 54) - t.Y, t.Y - n)), '1c4a1c')
    for x, y in scatter(r, n, 18, 120):
        if y > y0 - 40: continue
        a = r.uniform(-0.5, 0.5) + math.pi / 2
        pts = [(x + math.cos(a) * 18, y + math.sin(a) * 18), (x - math.cos(a) * 6, y - math.sin(a) * 6)]
        t.shape((x - 26, y - 26, x + 26, y + 26), sd_segment(pts[1][0], pts[1][1], pts[0][0], pts[0][1], 4.0, 9.0), color='17110f')
        t.shape((x - 10, y - 10, x + 10, y + 10), sd_ellipse(x - 2, y - 1, 2.0, 4.0, a), color='6a5a58')
    return {}


@design('candycorn')
def candycorn(t: Tex):
    """candy corn: rows of rounded kernels, yellow at the base, orange, a white tip, on dark chocolate"""
    n = t.n
    t.rgb[:] = hexrgb('2b170b')
    t.rough[:] = 0.45
    W, H = 64.0, 92.0
    rows = int(n / 128)
    for j in range(rows):
        for i in range(-1, int(n / W) + 1):
            cx = i * W + (W / 2 if j % 2 else 0) + W / 2
            yb = j * 128 + 110
            tri_ = [(cx - W * 0.42, yb), (cx + W * 0.42, yb), (cx, yb - H)]
            X, Y, idx = t.box(cx - W * 0.5, yb - H - 4, cx + W * 0.5, yb + 4)
            g = sd_polygon(tri_)
            sd = g(X, Y) - 0
            sd = sd_polygon([(cx - W * 0.36, yb - 6), (cx + W * 0.36, yb - 6), (cx, yb - H + 10)])(X, Y) - 6
            frac = np.clip((yb - Y) / H, 0, 1)
            col = np.where((frac < 0.42)[..., None], hexrgb('f0c632'), np.where((frac < 0.78)[..., None], hexrgb('e8741a'), hexrgb('f4ecdc')))
            t.paint(idx, cover(sd), col)
            t.paint(idx, cover(sd), height=np.clip(-sd / 6, 0, 1) * 2, hmode='max')
    return {}


@design('memphis')
def memphis(t: Tex):
    """memphis 90s: off-white ground scattered with squiggles, triangles, rings and dot grids in pink, yellow, cyan and black"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('f2ece0')
    t.rough[:] = 0.5
    cols = ['e64aa8', 'f0c832', '3ab8d8', '18181a', '58c048']
    for k, (x, y) in enumerate(scatter(r, n, 30, 150)):
        c = cols[r.integers(0, 5)]; a = r.uniform(0, TAU); kind = k % 4
        if kind == 0:
            pts = [(x + (q - 3) * 18 * math.cos(a) - (14 if q % 2 else -14) * math.sin(a), y + (q - 3) * 18 * math.sin(a) + (14 if q % 2 else -14) * math.cos(a)) for q in range(7)]
            t.shape(bbox_of(pts, 10), sd_polyline(pts, 5.5), color=c)
        elif kind == 1:
            poly = transform([(0, -38), (34, 24), (-34, 24)], x, y, a)
            t.shape(bbox_of(poly), sd_polygon(poly), color=c)
        elif kind == 2:
            t.shape((x - 40, y - 40, x + 40, y + 40), lambda X, Y, x=x, y=y: np.abs(np.hypot(X - x, Y - y) - 27) - 6, color=c)
        else:
            for qi in range(4):
                for qj in range(4):
                    px, py = x + (qi - 1.5) * 18, y + (qj - 1.5) * 18
                    t.shape((px - 6, py - 6, px + 6, py + 6), sd_circle(px, py, 4.2), color=c)
    return {}


@design('denim')
def denim(t: Tex):
    """denim: indigo twill with its fine diagonal ribs, faded a little in soft patches, and a gold double stitch"""
    n = t.n
    rib = np.sin((t.X - t.Y) * TAU / 10)
    fadep = smoothstep(0.1, 0.6, FBM([2, 4, 8], 431)(t.U, t.V))
    t.rgb[:] = mix('22386e', '2c4682', (rib * 0.5 + 0.5))
    t.fill(fadep * 0.35, '6f86b8')
    t.height[:] = (rib * 0.5 + 0.5) * 0.8
    t.normal_k = 0.8
    t.rough[:] = 0.88
    y0 = n * 0.62
    t.fill(cover(np.abs(t.Y - y0 - 14) - 1.5) * 0.5, '101c3a')
    for yy in (y0, y0 + 28):
        for x in range(0, n, 20):
            t.shape((x - 2, yy - 5, x + 16, yy + 5), sd_segment(x + 2, yy, x + 12, yy, 2.0), color='d29a3a')
    return {}


@design('granite')
def granite(t: Tex):
    """kitchen granite: polished grey stone full of angular flecks of black, white and rose"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('6a686e', '7a787e', smoothstep(-0.5, 0.5, FBM([3, 6], 441)(t.U, t.V)))
    t.rough[:] = 0.16
    cols = [('1a1a1e', 0.42), ('e2ded8', 0.22), ('a87878', 0.14), ('3a3a40', 0.12), ('9a9aa2', 0.1)]
    for k in range(1700):
        x, y = r.uniform(0, n), r.uniform(0, n)
        R = r.uniform(3, 9) * (1.6 if r.uniform() < 0.1 else 1)
        m = r.integers(5, 8)
        poly = [(x + math.cos(q / m * TAU + r.uniform(-0.3, 0.3)) * R * r.uniform(0.6, 1.0), y + math.sin(q / m * TAU + r.uniform(-0.3, 0.3)) * R * r.uniform(0.6, 1.0)) for q in range(m)]
        u = r.uniform(); acc = 0
        for c, p in cols:
            acc += p
            if u <= acc: break
        t.shape(bbox_of(poly), sd_polygon(poly), color=c)
    return {}


@design('jade')
def jade(t: Tex):
    """jade: deep green stone with paler milky veins drifting through it, polished to a soft glow"""
    U, V = t.U, t.V
    w = FBM([2, 4], 451)(U, V)
    f = FBM([2, 4, 8], 452, 0.55)(U + 0.12 * w, V)
    t.rgb[:] = mix('1f6a40', '2f8a56', smoothstep(-0.5, 0.5, f))
    t.fill(smoothstep(0.25, 0.6, f) * 0.6, '7cc496')
    g = FBM([(3, 4), (6, 8)], 453)(U + 0.1 * w, V)
    gx = (np.roll(g, -1, 1) - np.roll(g, 1, 1)) * 0.5; gy = (np.roll(g, -1, 0) - np.roll(g, 1, 0)) * 0.5
    dist = np.abs(g) / (np.sqrt(gx * gx + gy * gy) + 1e-6)
    t.fill(np.exp(-dist / 10) * 0.3, 'a8dcb8')
    t.rough[:] = 0.1
    return {}


@design('burl')
def burl(t: Tex):
    """wood burl: honey-brown figure swirling round dark little eyes, the grain rippling between them"""
    n = t.n; r = t.rng
    knots = [(r.uniform(0, n), r.uniform(0, n)) for _ in range(9)]
    d1, _, _ = voronoi(n, knots)
    w = FBM([3, 6, 12], 461, 0.55)(t.U, t.V)
    ring = np.sin((d1 / 20 + 4.0 * w) * TAU)
    t.rgb[:] = mix('8a4e22', 'b2703a', smoothstep(-0.6, 0.6, ring))
    t.fill(smoothstep(0.6, 0.95, ring) * 0.35, 'c88a4a')
    t.fill(1 - smoothstep(4, 9, d1), '3a1c0c')
    t.height[:] = ring * 0.3
    t.rough[:] = 0.3
    return {}


@design('moss')
def moss(t: Tex):
    """moss: soft rounded cushions of green, sunlit on their crowns, shadowed where they meet"""
    U, V = t.U, t.V
    h = FBM([8, 16, 32], 481, 0.55)(U, V)
    big = FBM([3, 6], 482)(U, V)
    crown = smoothstep(-0.35, 0.45, h + 0.25 * big)
    t.rgb[:] = mix('22381a', '4e7428', crown)
    t.fill(smoothstep(0.55, 0.95, crown) * 0.5, '86a83e')
    t.fill(smoothstep(-0.2, 0.5, big) * 0.2, '6a7a2a')
    t.height[:] = crown * 5
    t.normal_k = 0.6
    t.rough[:] = 0.95
    return {}


@design('crackle')
def crackle(t: Tex):
    """crackle glaze: pale celadon under a glassy glaze, crazed with fine grey-green lines at two scales"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('acc8b2', 'bcd6c2', smoothstep(-0.5, 0.5, FBM([2, 4], 471)(t.U, t.V)))
    big = voronoi(n, [(r.uniform(0, n), r.uniform(0, n)) for _ in range(18)])
    small = voronoi(n, [(r.uniform(0, n), r.uniform(0, n)) for _ in range(70)])
    e1 = (big[1] - big[0]) * 0.5; e2 = (small[1] - small[0]) * 0.5
    t.fill(np.clip(1.6 - e1 + 0.5, 0, 1) * 0.85, '4a5a48')
    t.fill(np.clip(0.8 - e2 + 0.5, 0, 1) * 0.45, '7a8c78')
    t.rough[:] = 0.08
    return {}


# ====================================================================== batch 4
FONTS = {'bold': 'C:/Windows/Fonts/arialbd.ttf', 'reg': 'C:/Windows/Fonts/arial.ttf', 'black': 'C:/Windows/Fonts/ariblk.ttf',
         'mono': 'C:/Windows/Fonts/consola.ttf', 'monob': 'C:/Windows/Fonts/consolab.ttf', 'din': 'C:/Windows/Fonts/bahnschrift.ttf'}


def text_cover(n, items):  # NOT used by any registered wrap: no readable text may be drawn (the rules at the top)
    """anti-aliased coverage of text: items = (text, x, y, size px, font key, anchor 'lt'|'mm'|..., rotation degrees).
       drawn at the tile's wrap-round copies too, so a word across an edge comes back on the other side"""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('L', (n, n), 0)
    for text, x, y, size, font, anchor, rot in items:
        f = ImageFont.truetype(FONTS[font], int(size))
        if not rot:
            d = ImageDraw.Draw(img)
            for ox in (-n, 0, n):
                for oy in (-n, 0, n):
                    d.text((x + ox, y + oy), text, fill=255, font=f, anchor=anchor)
        else:
            w = int(size * (len(text) + 2)); h = int(size * 2.4)
            tmp = Image.new('L', (w, h), 0)
            ImageDraw.Draw(tmp).text((w / 2, h / 2), text, fill=255, font=f, anchor='mm')
            tmp = tmp.rotate(rot, resample=Image.BICUBIC, expand=True)
            for ox in (-n, 0, n):
                for oy in (-n, 0, n):
                    img.paste(255, (int(x - tmp.width / 2 + ox), int(y - tmp.height / 2 + oy)), tmp)
    return np.asarray(img, np.float32) / 255.0


@design('tape')
def tape(t: Tex):
    """duct tape: overlapping strips of silver cloth tape round the gun, each lapping over the last with a soft shadow"""
    n = t.n; r = t.rng
    weave = (np.sin(t.X * TAU / 8) * 0.5 + 0.5) * (np.sin(t.Y * TAU / 8) * 0.5 + 0.5)
    t.rgb[:] = hexrgb('8e9298')
    y = 0.0
    for k in range(6):
        h = n / 6 + r.uniform(-10, 10) if k < 5 else n - y + 30
        y0 = y
        g = r.uniform(0.0, 1.0)
        col = mix('9a9ea4', 'b6bac0', g)
        band = cover(np.maximum(y0 - t.Y, t.Y - (y0 + h)))
        t.fill(band, col)
        t.fill(band * np.exp(-np.clip(t.Y - (y0 + h - 10), 0, None) / 6) * 0, '000000')
        t.fill(cover(np.abs(t.Y - y0) - 2.5, 2) * 0.35, '4a4c50')
        y += h - 18
    t.rgb[:] = t.rgb * (0.94 + 0.08 * weave)[..., None]
    t.height[:] = weave * 0.5
    t.metal[:] = 0.35
    t.rough[:] = 0.5
    return {}


def ink_lines(t: Tex, x0, y0, rows, lh, h, col, r, x1=None):
    """lines of 'writing' drawn as rounded grey bars of varied length (never letters): rows = how many, lh = line
       pitch, h = bar height; x1 = the right margin"""
    x1 = x1 or t.n - x0
    for i in range(rows):
        x = x0
        while x < x1 - 20:
            L = r.uniform(30, 150)
            e = min(x + L, x1)
            y = y0 + i * lh
            t.shape((x - 2, y - h, e + 2, y + h), sd_round_rect((x + e) / 2, y, (e - x) / 2, h / 2, h / 2), color=col)
            x = e + r.uniform(14, 26)


@design('receipt')
def receipt(t: Tex):
    """receipt: a till receipt on thermal paper, its lines of print drawn as grey bars (no letters or digits), a dashed
       tear line between the items and the total"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('e9e6dc', 'f3f0e8', smoothstep(-0.5, 0.5, FBM([2, 4], 491)(t.U, t.V)))
    t.rough[:] = 0.7
    t.shape((n * 0.3, 40, n * 0.7, 90), sd_round_rect(n / 2, 64, n * 0.18, 16, 16), color='34343a')
    ink_lines(t, 60, 150, 7, 64, 14, '5a5a62', r)
    for x in range(40, n - 40, 36):
        t.shape((x - 2, 600, x + 22, 616), sd_round_rect(x + 10, 608, 10, 3, 3), color='8a8a90')
    ink_lines(t, 60, 680, 2, 64, 18, '34343a', r)
    ink_lines(t, 60, 830, 3, 56, 12, '8a8a90', r)
    return {}


@design('crt')
def crt(t: Tex):
    """CRT: dark glass over glowing phosphor stripes, red green blue, showing broad colour bars; scanline gaps"""
    n = t.n
    trip = (t.X % 24) // 8
    gap = (t.Y % 24) > 19
    bars = np.floor(t.U * 7) / 7
    img = hsv(bars, 0.75, 1.0)
    chan = np.stack([(trip == 0), (trip == 1), (trip == 2)], -1).astype(np.float32)
    on = img * chan
    soft = np.clip(1 - np.abs((t.X % 8) - 4) / 4.5, 0, 1)[..., None]
    lit = on * soft * (~gap)[..., None]
    t.rgb[:] = 0.04 + lit * 0.85
    t.emit[:] = np.clip(lit.max(-1), 0, 1)
    t.rough[:] = 0.08
    return {'emissive': 1.4, 'tint': 'ffffff'}


@design('sheet')
def sheet(t: Tex):
    """spreadsheet: white cells and grey gridlines under a green header row, each cell's value a short grey bar (no
       letters or digits), a few highlighted cells and one selected"""
    n = t.n; r = t.rng
    cw, ch = 128, 64
    t.rgb[:] = hexrgb('f6f6f2')
    t.fill(cover(np.maximum(-t.Y, t.Y - ch)), '3f9a4a')
    hi = {(3, 3): 'f6dc5a', (5, 6): 'f2a8c8', (2, 10): 'f6dc5a', (6, 13): 'a8d8f0', (4, 5): 'f6b8b0'}
    for (i, j), c in hi.items():
        t.fill(cover(np.maximum(np.maximum(i * cw - t.X, t.X - (i + 1) * cw), np.maximum(j * ch - t.Y, t.Y - (j + 1) * ch))), c)
    t.fill(cover(np.minimum(np.abs(t.X % cw), np.abs(cw - t.X % cw)) - 1.0), 'b8bab4')
    t.fill(cover(np.minimum(np.abs(t.Y % ch), np.abs(ch - t.Y % ch)) - 1.0), 'b8bab4')
    for i in range(8):
        cx = i * cw + cw / 2
        t.shape((cx - 30, ch / 2 - 10, cx + 30, ch / 2 + 10), sd_round_rect(cx, ch / 2, 14, 6, 6), color='d8eed8')
    for j in range(1, 16):
        for i in range(8):
            if r.uniform() < 0.25: continue
            L = r.uniform(20, 70); x1 = i * cw + cw - 16; y = j * ch + ch / 2
            t.shape((x1 - L - 4, y - 10, x1 + 4, y + 10), sd_round_rect(x1 - L / 2, y, L / 2, 6, 6), color='c03030' if (i, j) == (4, 5) else '4a4a50')
    sx, sy = 3 * cw, 7 * ch
    t.fill(cover(np.abs(np.maximum(np.abs(t.X - sx - cw / 2) - cw / 2, np.abs(t.Y - sy - ch / 2) - ch / 2)) - 2.5), '1f7a2c')
    t.rough[:] = 0.5
    return {}


@design('memo')
def memo(t: Tex):
    """corporate memo: an office memo, its heading a thick black bar under a rule, its lines grey bars (no words), a red
       stamp outline askew and a coffee ring"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('ebe8de', 'f4f2ea', smoothstep(-0.5, 0.5, FBM([2, 4], 501)(t.U, t.V)))
    t.rough[:] = 0.75
    t.shape((30, 40, 420, 150), sd_round_rect(220, 95, 180, 42, 8), color='18181c')
    t.fill(cover(np.maximum(np.abs(t.Y - 178) - 5, np.maximum(40 - t.X, t.X - 984))), '18181c')
    ink_lines(t, 44, 225, 3, 50, 14, '4a4a52', r, x1=600)
    ink_lines(t, 44, 410, 8, 56, 14, 'a4a4aa', r)
    sx, sy = 650, 770
    rot = math.radians(-16)
    c, s_ = math.cos(rot), math.sin(rot)
    px, py = (t.X - sx) * c + (t.Y - sy) * s_, -(t.X - sx) * s_ + (t.Y - sy) * c
    stamp = cover(np.abs(np.maximum(np.abs(px) - 230, np.abs(py) - 70)) - 7)
    bars = np.maximum(cover(np.maximum(np.abs(px) - 170, np.abs(py + 18) - 12)), cover(np.maximum(np.abs(px + 40) - 130, np.abs(py - 26) - 10)))
    t.fill(np.maximum(stamp, bars) * 0.85, 'c41c26')
    d = np.hypot(t.X - 210, t.Y - 860)
    t.fill(cover(np.abs(d - 95) - 9, 3) * 0.3, '7a4a22')
    t.fill(cover(np.abs(d - 80) - 3, 2) * 0.18, '7a4a22')
    return {}


@design('glitch')
def glitch(t: Tex):
    """datamosh: a corrupted frame, long slices of a gradient shoved sideways, colour channels torn apart along them"""
    n = t.n; r = t.rng
    t.rgb[:] = hsv((t.U * 0.6 + 0.75) % 1.0, 0.55, 0.32)
    y = 0.0
    while y < n:
        h = r.integers(1, 7) * 16
        shift = r.uniform(-0.4, 0.4)
        band = cover(np.maximum(y - t.Y, t.Y - (y + h)))
        hue = ((t.U + shift) * 1.5 + r.uniform()) % 1.0
        val = 0.25 + 0.6 * ((t.U + shift) % 1.0)
        col = hsv(hue, 0.85, val)
        t.rgb[:] = t.rgb * (1 - band[..., None] * 0.85) + col * band[..., None] * 0.85
        if r.uniform() < 0.35:
            line = cover(np.abs(t.Y - y - h * r.uniform(0.2, 0.8)) - 2)
            t.fill(line, 'ff2ad8' if r.uniform() < 0.5 else '2affe0', emit=1.0)
        y += h
    t.rough[:] = 0.3
    return {'emissive': 1.2, 'tint': 'ffffff'}


@design('meat')
def meat(t: Tex):
    """meat suit, as cured salami: deep red slices flecked with round white fat and black pepper, clearly food (no
       raw flesh)"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('7a1c22', '92262a', smoothstep(-0.5, 0.5, FBM([3, 6], 511)(t.U, t.V)))
    t.rough[:] = 0.4
    for x, y in scatter(r, n, 140, 52):
        R = r.uniform(5, 14)
        t.shape((x - R - 3, y - R - 3, x + R + 3, y + R + 3), sd_ellipse(x, y, R, R * r.uniform(0.7, 1.0), r.uniform(0, TAU)), color=mix('ecd6cc', 'f6e8e0', r.uniform()))
    for x, y in scatter(r, n, 60, 60, taken=[]):
        t.shape((x - 6, y - 6, x + 6, y + 6), sd_circle(x, y, r.uniform(2.5, 4.0)), color='241414')
    return {}


def smiley(t: Tex, x, y, R, face, ink):
    X, Y, idx = t.box(x - R - 2, y - R - 2, x + R + 2, y + R + 2)
    d = np.hypot(X - x, Y - y)
    t.paint(idx, cover(d - R), face)
    for sx in (-1, 1):
        t.paint(idx, cover(sd_ellipse(x + sx * R * 0.34, y - R * 0.24, R * 0.11, R * 0.2)(X, Y)), ink)
    ang = np.arctan2(Y - y, X - x)
    arc = cover(np.abs(d - R * 0.56) - R * 0.07) * ((ang > 0.55) & (ang < math.pi - 0.55))
    t.paint(idx, arc, ink)


@design('corp')
def corp(t: Tex):
    """☺ CORP: black with faint diagonal stripes, big yellow smiley faces ringed in pink (no lettering)"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('121214')
    t.fill(cover(np.abs(((t.X - t.Y) % 64) - 32) - 10) * 0.5, '1c1c20')
    for x, y, R in ((n * 0.25, n * 0.25, 150), (n * 0.75, n * 0.75, 150), (n * 0.78, n * 0.22, 70), (n * 0.2, n * 0.8, 70)):
        t.shape((x - R - 30, y - R - 30, x + R + 30, y + R + 30), lambda X, Y, x=x, y=y, R=R: np.abs(np.hypot(X - x, Y - y) - R - 16) - 6, color='e04aa8', emit=0.6)
        smiley(t, x, y, R, 'ecc834', '121214')
    t.rough[:] = 0.3
    return {'emissive': 0.9, 'tint': 'ffffff'}


@design('jersey')
def jersey(t: Tex):
    """jersey: team red with white and navy hoops and a blank white number panel, in a fine sports mesh (no digits)"""
    n = t.n
    t.rgb[:] = hexrgb('b81c26')
    y0 = n * 0.12
    for a, b, col in ((y0, y0 + 60, 'efece4'), (y0 + 60, y0 + 140, '1c2a5e'), (y0 + 140, y0 + 200, 'efece4')):
        t.fill(cover(np.maximum(a - t.Y, t.Y - b)), col)
    t.shape((n * 0.25, n * 0.42, n * 0.75, n * 0.88), sd_round_rect(n / 2, n * 0.65, n * 0.2, n * 0.19, 26), color='1c2a5e')
    t.shape((n * 0.25, n * 0.42, n * 0.75, n * 0.88), sd_round_rect(n / 2, n * 0.65, n * 0.2 - 12, n * 0.19 - 12, 18), color='efece4')
    holes = (np.sin(t.X * TAU / 10) * np.sin(t.Y * TAU / 10))
    t.height[:] = -np.clip(holes, 0, 1) * 0.6
    t.rgb[:] = t.rgb * (1 - 0.06 * np.clip(holes, 0, 1))[..., None]
    t.rough[:] = 0.75
    return {}


@design('sushi')
def sushi(t: Tex):
    """sushi: maki rolls seen from above on a bamboo mat, nori, rice, salmon and cucumber; a slice of salmon nigiri"""
    n = t.n; r = t.rng
    slat = (t.X % 48) / 48
    t.rgb[:] = mix('a8904e', 'c8b070', smoothstep(0, 0.2, slat) * smoothstep(1, 0.8, slat))
    t.fill(cover(np.minimum(t.X % 48, 48 - t.X % 48) - 1.5) * 0.6, '6a5a2a')
    t.rough[:] = 0.5
    def maki(x, y, R=120):
        X, Y, idx = t.box(x - R - 12, y - R - 12, x + R + 12, y + R + 12)
        d = np.hypot(X - x, Y - y)
        t.paint(idx, cover(np.hypot(X - x - 8, Y - y - 10) - R, 6) * 0.4, '3a2a10')
        t.paint(idx, cover(d - R), '141c16')
        t.paint(idx, cover(d - R * 0.88), 'f2efe6')
        for k in range(60):
            a = r.uniform(0, TAU); rr = r.uniform(R * 0.4, R * 0.82)
            t.paint(idx, cover(sd_ellipse(x + math.cos(a) * rr, y + math.sin(a) * rr, 9, 4.5, a + r.uniform(-1, 1))(X, Y)) * 0.6, 'dcd8ca')
        t.paint(idx, cover(sd_ellipse(x - 8, y, R * 0.34, R * 0.28, 0.3)(X, Y)), 'e8724a')
        for k in range(4):
            t.paint(idx, cover(sd_segment(x - R * 0.3, y - R * 0.2 + k * 14, x + R * 0.2, y - R * 0.05 + k * 14, 1.6)(X, Y)) * cover(sd_ellipse(x - 8, y, R * 0.34, R * 0.28, 0.3)(X, Y)), 'f6c0a8')
        t.paint(idx, cover(np.hypot(X - x - R * 0.3, Y - y + R * 0.22) - R * 0.14), '6abf4a')
    maki(n * 0.25, n * 0.27); maki(n * 0.75, n * 0.73)
    x, y, a = n * 0.74, n * 0.24, 0.35
    X, Y, idx = t.box(x - 190, y - 120, x + 190, y + 120)
    sd = sd_ellipse(x, y, 170, 82, a)(X, Y)
    t.paint(idx, cover(sd), 'ec7a4c')
    for k in range(-4, 5):
        cx, cy = x + math.cos(a) * k * 36, y + math.sin(a) * k * 36
        t.paint(idx, cover(sd_ellipse(cx, cy, 6, 70, a + 0.5)(X, Y)) * cover(sd) * 0.7, 'f8cdb4')
    return {}


# NOT a texture wrap (16 Nov 2026, after the account moderation): nothing that reads as a code is drawn. "Barcode" is a
# colour wrap. Kept unregistered. Never register it again.
def barcode(t: Tex):
    """barcode: white labels of crisp black bars with their digits under them"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('f2f2ec')
    t.rough[:] = 0.5
    for y0, digits in ((40, '4 01234 56789 3'), (552, '7 00000 00001 2')):
        x = 90.0
        while x < 930:
            bw = int(r.integers(1, 4)) * 8
            t.fill(cover(np.maximum(np.maximum(x - t.X, t.X - (x + bw)), np.maximum(y0 - t.Y, t.Y - (y0 + 360)))), '121214')
            x += bw + int(r.integers(1, 3)) * 8
        t.fill(text_cover(n, [(digits, n / 2, y0 + 410, 60, 'monob', 'mm', 0)]), '121214')
    return {}


@design('geode')
def geode(t: Tex):
    """amethyst geode: agate bands of lilac and violet circling crystal pockets lined with faceted points"""
    n = t.n; r = t.rng
    pk = [(r.uniform(0, n), r.uniform(0, n)) for _ in range(5)]
    d1, _, ids = voronoi(n, pk)
    w = FBM([3, 6, 12], 521, 0.55)(t.U, t.V)
    band = d1 * 0.03 + 1.8 * w
    pal = np.array([hexrgb(h) for h in ('ece2f8', 'b48ae6', '7a4ac8', '4a1c88', 'd8c4f2', '9a6ad8')])
    k = np.floor(band).astype(int) % 6
    fr = band - np.floor(band)
    col = pal[k] + (pal[(k + 1) % 6] - pal[k]) * smoothstep(0.85, 1.0, fr)[..., None]
    t.rgb[:] = col
    pocket = 1 - smoothstep(70, 80, d1)
    ang = np.arctan2(t.Y - np.array([p[1] for p in pk])[ids], t.X - np.array([p[0] for p in pk])[ids])
    facet = (np.floor((ang + math.pi) / TAU * 18) % 2)
    fc = mix('caa8f4', '8a5ad8', facet * 0.8 + smoothstep(70, 0, d1) * 0.2)
    t.rgb[:] = t.rgb * (1 - pocket[..., None]) + fc * pocket[..., None]
    t.height[:] = pocket * facet * 1.5
    t.rough[:] = 0.12
    return {}


@design('arcade')
def arcade(t: Tex):
    """arcade carpet: midnight carpet with neon squiggles, rings, planets and stars that glow under blacklight"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('120c2c')
    cols = ['ff4fc4', '4fd0ff', 'ffd84a', '6aff6a', 'ff8a3a']
    for k, (x, y) in enumerate(scatter(r, n, 34, 130)):
        c = cols[k % 5]; kind = k % 5; a = r.uniform(0, TAU)
        if kind == 0:
            pts = [(x + (q - 4) * 14 * math.cos(a) + 12 * math.sin(q * 1.2) * -math.sin(a), y + (q - 4) * 14 * math.sin(a) + 12 * math.sin(q * 1.2) * math.cos(a)) for q in range(9)]
            t.shape(bbox_of(pts, 8), sd_polyline(pts, 5), color=c, emit=1.0)
        elif kind == 1:
            t.shape((x - 40, y - 40, x + 40, y + 40), sd_star(x, y, 32, 14, 5, a, 2), color=c, emit=1.0)
        elif kind == 2:
            t.shape((x - 30, y - 30, x + 30, y + 30), sd_circle(x, y, 20), color=c, emit=0.8)
            t.shape((x - 50, y - 30, x + 50, y + 30), lambda X, Y, x=x, y=y: np.abs(np.hypot((X - x) * 0.5, Y - y) - 18) - 2.5, color=cols[(k + 2) % 5], emit=1.0)
        elif kind == 3:
            t.shape((x - 34, y - 34, x + 34, y + 34), lambda X, Y, x=x, y=y: np.abs(np.hypot(X - x, Y - y) - 24) - 4, color=c, emit=1.0)
        else:
            poly = transform([(0, -26), (24, 16), (-24, 16)], x, y, a)
            t.shape(bbox_of(poly), sd_polygon(poly), color=c, emit=1.0)
    t.rough[:] = 0.9
    return {'emissive': 1.1, 'tint': 'ffffff'}


# NOT a texture wrap: on 16 Nov 2026 the owner's Roblox account was moderated over this wrap's first upload, which
# looked like a QR code (finder squares); Roblox does not allow QR codes in images. "QR Code" stays a colour wrap.
# Kept here unregistered, as a mosaic with no finder squares, only so the history is clear. Never register it again.
def qr(t: Tex):
    """QR code, as a data mosaic: black modules on white round a smiley; deliberately no finder squares (Roblox does not
       allow QR codes in images, and this must not read as one to a scanner)"""
    n = t.n; r = t.rng
    m = 32
    t.rgb[:] = hexrgb('f4f4f0')
    cells = (r.uniform(size=(32, 32)) < 0.47)
    cells[12:20, 12:20] = False
    mask = cells[(t.Y // m).astype(int) % 32, (t.X // m).astype(int) % 32].astype(np.float32)
    t.fill(mask, '141416')
    # (no finder squares at all: Roblox does not allow QR codes in images, so this is a data mosaic round a smiley)
    smiley(t, 16 * m, 16 * m, 112, 'ecc834', '141416')
    t.rough[:] = 0.45
    return {}


@design('organ')
def organ(t: Tex):
    """organ donor: a pink ☺ CORP donor card with a heart, its small print as grey bars, and a green stamp outline
       (no words, no body parts, no blood)"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('f6e6ea')
    t.fill(cover(np.maximum(-t.Y, t.Y - 170)), 'd8405e')
    t.fill(cover(t.Y - 940) * cover(n - t.Y), 'd8405e')
    t.shape((n * 0.25, 60, n * 0.75, 115), sd_round_rect(n / 2, 86, n * 0.22, 18, 18), color='fbeef0')
    hx, hy, s = 230, 520, 150
    heart = [(hx, hy + s * 0.9)] + bezier((hx, hy + s * 0.9), (hx - s * 1.4, hy - s * 0.1), (hx - s * 0.6, hy - s * 1.1), (hx, hy - s * 0.35)) + \
        bezier((hx, hy - s * 0.35), (hx + s * 0.6, hy - s * 1.1), (hx + s * 1.4, hy - s * 0.1), (hx, hy + s * 0.9))
    t.shape(bbox_of(heart), sd_polygon(heart), color='d03050')
    t.shape((hx - 90, hy - 100, hx, hy - 20), sd_ellipse(hx - 48, hy - 60, 32, 17, -0.6), color='f08aa0')
    ink_lines(t, 420, 270, 4, 110, 16, '5a5a62', r, x1=960)
    rot = math.radians(-17)
    c, s_ = math.cos(rot), math.sin(rot)
    px, py = (t.X - 760) * c + (t.Y - 810) * s_, -(t.X - 760) * s_ + (t.Y - 810) * c
    stamp = cover(np.abs(np.maximum(np.abs(px) - 210, np.abs(py) - 60)) - 6)
    bar = cover(np.maximum(np.abs(px) - 150, np.abs(py) - 14))
    t.fill(np.maximum(stamp, bar) * 0.85, '1f8a44')
    t.rough[:] = 0.45
    return {}


@design('dice')
def dice(t: Tex):
    """loaded dice: glossy white dice with black pips (the one pip red) tumbling on red casino felt"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('8e1420', 'a81a28', smoothstep(-0.5, 0.5, FBM([4, 8], 531)(t.U, t.V)))
    t.rough[:] = 0.9
    PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
            5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}
    for k, (x, y) in enumerate(scatter(r, n, 6, 330)):
        a = r.uniform(0, TAU); S = 100; face = [6, 1, 5, 3, 4, 2][k % 6]
        X, Y, idx = t.box(x - S * 1.6, y - S * 1.6, x + S * 1.6, y + S * 1.6)
        t.paint(idx, cover(sd_round_rect(x + 14, y + 18, S, S, 24, a)(X, Y), 10) * 0.45, '3a0608')
        sd = sd_round_rect(x, y, S, S, 24, a)(X, Y)
        t.paint(idx, cover(sd), mix('dcdad2', 'f6f4ee', smoothstep(S, -S, (X - x) + (Y - y))), rough=0.15)
        t.paint(idx, cover(sd), height=np.clip(-sd / 20, 0, 1) * 3, hmode='max')
        for px, py in PIPS[face]:
            cx = x + (px * math.cos(a) - py * math.sin(a)) * S * 0.5
            cy = y + (px * math.sin(a) + py * math.cos(a)) * S * 0.5
            t.paint(idx, cover(np.hypot(X - cx, Y - cy) - (24 if face == 1 else 15)), 'c4182e' if face == 1 else '141416')
    return {}


@design('numsoup')
def numsoup(t: Tex):
    """number soup (pasta shapes, not digits): golden broth with little pasta rings, stars and bow ties floating in it,
       a few carrot coins and herbs"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('c8862a', 'dca040', smoothstep(-0.5, 0.5, FBM([3, 6], 541)(t.U, t.V)))
    t.fill(field_cover(FBM([6, 12], 542)(t.U, t.V), 0.3) * 0.3, 'f0c870')
    t.rough[:] = 0.15
    for x, y in scatter(r, n, 6, 200):
        t.shape((x - 40, y - 40, x + 40, y + 40), sd_circle(x, y, 30), color='e2661e')
        t.shape((x - 40, y - 40, x + 40, y + 40), lambda X, Y, x=x, y=y: np.abs(np.hypot(X - x, Y - y) - 18) - 2, color='f0943e')
    for k, (x, y) in enumerate(scatter(r, n, 22, 140)):
        a = r.uniform(0, TAU)
        X, Y, idx = t.box(x - 60, y - 60, x + 60, y + 60)
        if k % 3 == 0:
            sd = np.abs(np.hypot(X - x, Y - y) - 30) - 11
        elif k % 3 == 1:
            sd = sd_star(x, y, 46, 22, 5, a, 6)(X, Y)
        else:
            c, s_ = math.cos(a), math.sin(a)
            px, py = (X - x) * c + (Y - y) * s_, -(X - x) * s_ + (Y - y) * c
            sd = np.maximum(np.abs(px) - 44, np.abs(py) - (8 + 0.45 * np.abs(px)))
        t.paint(idx, cover(sd - 5, 4) * 0.45, '7a4a14')
        t.paint(idx, cover(sd), 'f4e2a8')
        t.paint(idx, cover(sd), height=np.clip(-sd / 8, 0, 1) * 3, hmode='max')
    for x, y in scatter(r, n, 10, 120):
        a = r.uniform(0, TAU)
        poly = transform(petal_outline(22, 9, 0.0), x, y, a)
        t.shape(bbox_of(poly), sd_polygon(poly), color='3a7a2a')
    return {}


@design('opal')
def opal(t: Tex):
    """opal: milky blue-white stone with flowing patches of play-of-colour fire that glow softly"""
    U, V = t.U, t.V
    t.rgb[:] = mix('b4c4d4', 'dce6ee', smoothstep(-0.5, 0.5, FBM([2, 4], 551)(U, V)))
    w = FBM([3, 6], 553)(U, V)
    hue = (FBM([2, 4, 8], 554, 0.55)(U + 0.1 * w, V) * 1.6 + 0.5) % 1.0
    show = smoothstep(0.02, 0.3, FBM([(3, 4), (6, 8), (12, 16)], 552, 0.55)(U, V + 0.05 * w))
    fire = hsv(hue, 0.6, 1.0)
    t.rgb[:] = t.rgb * (1 - show[..., None] * 0.75) + fire * show[..., None] * 0.75
    t.emit[:] = show * 0.6
    t.rough[:] = 0.08
    return {'emissive': 0.7, 'tint': 'ffffff'}


@design('lavalamp')
def lavalamp(t: Tex):
    """lava lamp: dark purple glass with soft glowing blobs of orange and pink wax, merging where they meet"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('180a20')
    for cols, seeds in ((('ff7a20', 'ffc04a'), 0), (('ff3a7a', 'ff9ad0'), 1)):
        field = np.zeros((n, n), np.float32)
        for x, y in scatter(r, n, 6, 200):
            R = r.uniform(50, 110)
            dx = np.abs(t.X - x); dx = np.minimum(dx, n - dx)
            dy = np.abs(t.Y - y) * 0.75; dy = np.minimum(dy, n - dy)
            field += (R * R) / (dx * dx + dy * dy + 1)
        m = field_cover(field, 1.0)
        inner = smoothstep(1.0, 3.0, field)
        t.fill(m, mix(cols[0], cols[1], inner), emit=1.0)
    t.rough[:] = 0.1
    return {'emissive': 1.0, 'tint': 'ffffff'}


@design('vapor')
def vapor(t: Tex):
    """vaporwave: a striped sun setting over a pink grid floor, under a purple sky"""
    n = t.n
    t.rgb[:] = mix('1a0636', '5a1478', smoothstep(0, 0.6, t.V))
    sx, sy, R = n / 2, n * 0.42, 230
    d = np.hypot(t.X - sx, t.Y - sy)
    sun = cover(d - R) * cover(t.Y - n * 0.66)
    cut = np.zeros_like(sun)
    for i in range(6):
        y0 = sy + 20 + i * 32
        cut = np.maximum(cut, cover(np.abs(t.Y - y0) - (2 + i * 2.2)))
    sun = sun * (1 - cut)
    t.fill(sun, mix('ffd84a', 'ff3a8a', smoothstep(sy - R, sy + R, t.Y)), emit=1.0)
    floor = cover(n * 0.66 - t.Y)
    t.fill(floor, '1a0430')
    gx = cover(np.minimum((t.X - sx) % 128, 128 - (t.X - sx) % 128) - 2)
    gy = cover(np.minimum((t.Y - n * 0.66) % 64, 64 - (t.Y - n * 0.66) % 64) - 2)
    t.fill(np.maximum(gx, gy) * floor, 'ff4fc4', emit=1.0)
    t.fill(cover(np.abs(t.Y - n * 0.66) - 3), '4fd8ff', emit=1.0)
    t.rough[:] = 0.25
    return {'emissive': 1.1, 'tint': 'ffffff'}


@design('aurora')
def aurora(t: Tex):
    """aurora: green and violet light hanging in soft curtains over a dark night sky with a few stars"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('03101a', '06182a', t.V)
    for _ in range(160):
        x, y = r.uniform(0, n), r.uniform(0, n)
        t.shape((x - 4, y - 4, x + 4, y + 4), sd_circle(x, y, r.uniform(0.9, 1.8)), color='cfe8f4', emit=0.6)
    w = FBM([(2, 1), (4, 2)], 561)(t.U, t.V)
    base = 0.55 + 0.18 * np.sin((t.U + 0.4 * w) * TAU * 2)
    above = np.clip((base - t.V) / 0.45, 0, 1)
    below = smoothstep(0.03, 0.0, t.V - base)
    rays = 0.6 + 0.4 * np.sin((t.U * 24 + 3 * w) * TAU) ** 2
    a = above * below * rays
    a = np.where(t.V < base, np.exp(-(base - t.V) / 0.18) * rays, 0) * 0.95
    col = mix('2aff8a', 'b04aff', smoothstep(0.0, 0.35, base - t.V))
    t.fill(np.clip(a, 0, 1), col, emit=1.0)
    t.emit[:] = np.maximum(t.emit, np.clip(a, 0, 1))
    t.rough[:] = 0.3
    return {'emissive': 1.4, 'tint': 'ffffff'}


@design('blackhole')
def blackhole(t: Tex):
    """black hole: a field of stars bent round a black disc, ringed by a swirling orange accretion disk"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('06040c')
    for _ in range(260):
        x, y = r.uniform(0, n), r.uniform(0, n)
        t.shape((x - 4, y - 4, x + 4, y + 4), sd_circle(x, y, r.uniform(0.9, 2.0)), color=['ffffff', 'ffd8a8', 'a8c8ff'][r.integers(0, 3)], emit=0.7)
    for cx, cy in ((n * 0.3, n * 0.35), (n * 0.78, n * 0.8)):
        dx = t.X - cx; dx = (dx + n / 2) % n - n / 2
        dy = t.Y - cy; dy = (dy + n / 2) % n - n / 2
        rr = np.hypot(dx, dy * 2.4) / 240
        ang = np.arctan2(dy * 2.4, dx) - 2.2 / (rr + 0.15)
        arms = 0.5 + 0.5 * np.sin(ang * 3 + rr * 22)
        disk = smoothstep(1.0, 0.45, rr) * smoothstep(0.32, 0.42, rr)
        col = mix('ff5a10', 'ffd88a', arms * smoothstep(0.9, 0.4, rr))
        t.fill(disk * (0.35 + 0.65 * arms), col, emit=1.0)
        hole = cover(np.hypot(dx, dy) - 70)
        t.fill(hole, '000000', emit=0.0)
        t.emit[:] = t.emit * (1 - hole)
        ringd = np.abs(np.hypot(dx, dy) - 76)
        t.fill(cover(ringd - 2.5) * 0.9, 'fff0d0', emit=1.0)
    t.rough[:] = 0.25
    return {'emissive': 1.6, 'tint': 'ffffff'}


@design('stonks')
def stonks(t: Tex):
    """market crash: a trading terminal on its worst day, a red line diving through candlesticks, lit ticker bars
       (no words or numbers)"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('05080a')
    t.fill(cover(np.minimum(t.X % 128, 128 - t.X % 128) - 1) * 0.8, '102016')
    t.fill(cover(np.minimum(t.Y % 128, 128 - t.Y % 128) - 1) * 0.8, '102016')
    pts = []; y = 260.0
    for x in np.arange(0, n + 1, 32.0):
        pts.append((x, y)); y = min(880, max(220, y + r.uniform(-30, 64)))
    pts[-1] = (pts[-1][0], 260.0)
    for i in range(2, len(pts) - 2, 2):
        x, yy = pts[i]; up = r.uniform() < 0.35
        c = '3aff5a' if up else 'ff3a3a'
        t.shape((x - 14, yy - 70, x + 14, yy + 70), sd_round_rect(x, yy, 8, 34, 2), color=c, emit=0.8)
        t.shape((x - 4, yy - 70, x + 4, yy + 70), sd_segment(x, yy - 56, x, yy + 56, 1.5), color=c, emit=0.8)
    X, Y, idx = t.box(-40, 150, n + 40, 960)
    t.paint(idx, cover(sd_polyline(pts, 5)(X, Y)), 'ff3a3a', emit=1.0)
    for x0, y0, L, c in ((40, 70, 220, 'ffd84a'), (600, 70, 180, '3aff5a'), (40, 940, 300, 'ff3a3a')):
        t.shape((x0 - 4, y0 - 20, x0 + L + 4, y0 + 20), sd_round_rect(x0 + L / 2, y0, L / 2, 12, 4), color=c, emit=1.0)
    t.rough[:] = 0.2
    return {'emissive': 1.3, 'tint': 'ffffff'}


@design('bowling')
def bowling(t: Tex):
    """bowling alley: glossy maple lane boards along the gun, fine grain, and the lane's aiming arrows and dots"""
    n = t.n; r = t.rng
    bw = n / 8
    board = (t.Y // bw).astype(int)
    tone = r.uniform(-1, 1, 8)[board % 8]
    grain = FBM([(2, 16), (4, 32)], 571, 0.5)(t.U, t.V)
    t.rgb[:] = mix('c89a5e', 'deb47a', np.clip(0.5 + 0.25 * tone + 0.35 * grain, 0, 1))
    t.fill(cover(np.minimum(t.Y % bw, bw - t.Y % bw) - 1.2) * 0.7, '7a5228')
    for x, y in ((n * 0.25, n * 0.25), (n * 0.75, n * 0.75)):
        poly = [(x + 70, y), (x - 50, y - 36), (x - 50, y + 36)]
        t.shape(bbox_of(poly), sd_polygon(poly), color='4a2410')
    for x, y in ((n * 0.6, n * 0.4), (n * 0.1, n * 0.9), (n * 0.85, n * 0.06)):
        t.shape((x - 20, y - 20, x + 20, y + 20), sd_circle(x, y, 13), color='4a2410')
    t.rough[:] = 0.12
    return {}


# ====================================================================== the run
def build(wid, out_dir):
    t = Tex(seed=seed_of(wid))
    extra = DESIGNS[wid](t) or {}
    maps = t.save(os.path.join(out_dir, wid))
    rel = {k: (os.path.basename(v) if isinstance(v, str) else v) for k, v in maps.items()}
    return {'maps': rel, **extra}


def sheet(out_dir, ids, cols=5, px=256):
    from PIL import Image, ImageDraw
    rows = (len(ids) + cols - 1) // cols
    img = Image.new('RGB', (cols * (px * 2 + 12) + 12, rows * (px + 34) + 12), (24, 24, 28))
    d = ImageDraw.Draw(img)
    for k, wid in enumerate(ids):
        c = Image.open(os.path.join(out_dir, wid + '_color.png'))
        x, y = 12 + (k % cols) * (px * 2 + 12), 12 + (k // cols) * (px + 34)
        img.paste(c.resize((px, px), Image.LANCZOS), (x, y))                    # the whole tile
        img.paste(c.crop((0, 0, 256, 256)).resize((px, px), Image.LANCZOS), (x + px, y))  # a quarter, 1:1 at 4x
        d.text((x, y + px + 6), wid, fill=(230, 230, 230))
    p = os.path.join(out_dir, 'sheet.png'); img.save(p); return p


if __name__ == '__main__':
    argv = sys.argv[1:]
    out_dir = argv[0]; rest = argv[1:]
    want_sheet = '--sheet' in rest
    ids = [a for a in rest if not a.startswith('--')] or list(DESIGNS)
    os.makedirs(out_dir, exist_ok=True)
    spec_p = os.path.join(out_dir, 'wraps.json')
    spec = json.load(open(spec_p)) if os.path.exists(spec_p) else {}
    for wid in ids:
        if wid not in DESIGNS: print('no design for', wid); continue
        spec[wid] = build(wid, out_dir)
        print('WRAP', wid, json.dumps(spec[wid]['maps']))
    spec = {k: spec[k] for k in sorted(spec)}
    with open(spec_p, 'w') as fh: json.dump(spec, fh, indent=1)
    if want_sheet: print('SHEET', sheet(out_dir, ids))
