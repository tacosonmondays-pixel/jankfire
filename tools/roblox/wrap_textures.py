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
# since 27 Nov 2026 0.6 m (was 0.25 m), 1 cm = 17 px. First person shows a rifle at roughly 1,500 screen pixels a
# metre, so a tile is still a little finer than the screen needs. A design is laid out across the gun: no grids,
# scattered motifs of varied size, areas of rest, and few round motifs (they fold over edges: keep them small).
#
# THE LOOK (owner, 16 Nov 2026; vault Principles/Design principles.md): serious and polished, in the class of RIVALS,
# never noisy. Wraps are cosmetics, so colour is allowed, but each must be deliberate: clean shapes, a few flat colours
# with smooth tonal shifts, real shapes for details (notched petals, tapered stripes), no pixel specks, no grain.
# Stars: any star you notice at first-person distance is a real star shape (five points, or a four-point sparkle),
# never a square (owner, 16 Nov 2026); faint background stars are round dots (StarLight below). Galaxy alone is all
# dots, the owner's own call for it: "get rid of the stars and just keep them like dots, I want it to look like an
# actual galaxy".
# Warm colours and purples come out brighter under the halls' lamps: they are picked a step darker.
import sys, os, json, math, zlib
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wraplib import *

TILE_M = 0.6    # metres of gun per tile (must match gun_uvs.TILE_M; 0.25 before 27 Nov 2026)
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
STAR_COLOURS = (('ffffff', 0.50), ('d6e2ff', 0.27), ('fff1d8', 0.15), ('ffd2a6', 0.08))  # white, blue, warm, orange


class StarLight:
    """light added over a picture (screen blend): round stars as dots with a soft glow, never a pointed star shape
       (owner, 16 Nov 2026: "get rid of the stars and just keep them like dots, I want it to look like an actual
       galaxy")"""
    def __init__(self, t: Tex):
        self.t = t
        self.L = np.zeros((t.n, t.n, 3), np.float32)

    def dot(self, x, y, r, amp, col, glow=0.0, glow_r=None):
        """a round star: a crisp disc of radius r (anti-aliased, Gaussian-soft at its rim) and an optional wide halo"""
        gr = glow_r or r * 3.0
        ext = max(r * 2.5, gr * 3.0 if glow else 0) + 2
        X, Y, idx = self.t.box(x - ext, y - ext, x + ext, y + ext)
        d = np.hypot(X - x, Y - y)
        core = np.exp(-0.5 * (d / max(r * 0.75, 0.6)) ** 2)
        a = amp * core
        if glow: a = a + glow * np.exp(-0.5 * (d / gr) ** 2)
        c = hexrgb(col) if isinstance(col, str) else np.asarray(col, np.float32)
        self.L[idx] += a[..., None] * c

    def add(self, a, col):
        self.L += np.asarray(a, np.float32)[..., None] * hexrgb(col)

    def done(self, emit=0.9, rough=0.22):
        t = self.t
        L = np.clip(self.L, 0, 1)
        t.rgb[:] = 1 - (1 - t.rgb) * (1 - L)
        lum = L.max(-1)
        t.emit[:] = np.maximum(t.emit, np.clip(lum * emit, 0, 1))
        t.rough[:] = t.rough * (1 - lum) + rough * lum


def star_colour(r):
    k = r.uniform(); s = 0.0
    for c, p in STAR_COLOURS:
        s += p
        if k < s: return c
    return 'ffffff'


def spiral_galaxy(S: StarLight, cx, cy, R, tilt, rot, pitch=0.5, turn=1, arm_col='bccbff', core_col='fff0d6', amp=1.0,
                  seed=1):
    """a small spiral galaxy seen at a slant: a warm bulge, a bar of haze, and two blue-white arms winding out with
       clumps of young stars along them (light only)"""
    t = S.t
    X, Y, idx = t.box(cx - R * 1.25, cy - R * 1.25, cx + R * 1.25, cy + R * 1.25)
    dx, dy = X - cx, Y - cy
    c, s = math.cos(rot), math.sin(rot)
    a, b = dx * c + dy * s, (-dx * s + dy * c) / tilt
    r = np.hypot(a, b) / R + 1e-4
    th = np.arctan2(b, a)
    ph = th - turn * np.log(r) / math.tan(pitch)
    arm = (0.5 + 0.5 * np.cos(2 * ph)) ** 3
    clump = 0.6 + 0.4 * smoothstep(0.1, 0.6, Perlin(8, seed)(ph / TAU, r * 3))
    disc = np.exp(-r / 0.32) * smoothstep(1.05, 0.5, r)
    bulge = np.exp(-0.5 * (r / 0.07) ** 2)
    haze = np.exp(-r / 0.14) * 0.35
    ca, cc = hexrgb(arm_col), hexrgb(core_col)
    S.L[idx] += (disc * (0.12 + 0.88 * arm * clump) * 1.2 * amp)[..., None] * ca
    S.L[idx] += ((bulge * 1.0 + haze) * amp)[..., None] * cc


@design('galaxy')
def galaxy(t: Tex):
    """an actual galaxy, up close: violet and blue star clouds over near-black space, dark dust lanes winding through
       them, thousands of round stars (dots of every size, white, blue-white and warm, thickest in the clouds), a few
       bright ones with a soft round glow, and two small spiral galaxies far off. No pointed star shapes."""
    n, U, V = t.n, t.U, t.V
    wu, wv = U + 0.07 * FBM([2, 4], 11)(U, V), V + 0.07 * FBM([2, 4], 12)(U, V)
    neb = FBM([2, 4, 8, 16], 13, 0.55)(wu, wv)           # how bright the star clouds are
    m = smoothstep(-0.25, 0.6, neb)
    m2 = smoothstep(0.0, 0.65, FBM([3, 6, 12], 14, 0.5)(wu + 0.3, wv))
    pink = smoothstep(0.35, 0.75, FBM([6, 12], 16)(wu, wv)) * m
    ridge = 1 - np.abs(FBM([3, 6, 12], 15, 0.55)(wu * 1.0 + 0.11, wv))
    # dust: soft, thin, and only through the heart of a cloud (at its rim it read as a crack round every cloud)
    lane = blur_wrap(smoothstep(0.88, 0.985, ridge), 6) * smoothstep(0.05, 0.5, neb)
    t.rgb[:] = mix('03030e', '0c0b28', smoothstep(-0.7, 0.3, neb))   # near-black navy (round 2)
    t.fill(m * 0.6, '322f88')
    t.fill(m * m * 0.6, '6a4fc2')
    t.fill(m * m * m * 0.35, 'b8a2d8')                    # the thick of the clouds goes pale, as a real star cloud
    t.fill(m2 * (1 - m) * 0.35, '1c3a78')                 # deep blue where the violet thins
    t.fill(pink * 0.42, '9a3f86')                         # a few pink gas knots
    t.rgb[:] = t.rgb * (1 - 0.55 * lane)[..., None]
    t.emit[:] = (m * 0.10 + m ** 3 * 0.10) * (1 - lane)
    t.rough[:] = 0.3
    r = t.rng
    S = StarLight(t)
    # two far-off spiral galaxies, in the darker parts of the tile (placed first: no bright star lands on one)
    spots = []
    for _ in range(600):
        x, y = r.uniform(0, n), r.uniform(0, n)
        if m[int(y), int(x)] < 0.2 and all(min(abs(x - a), n - abs(x - a)) ** 2 + min(abs(y - b), n - abs(y - b)) ** 2 > 400 ** 2 for a, b in spots):
            spots.append((x, y))
        if len(spots) == 2: break
    gal = [(x, y, 120 if i == 0 else 64) for i, (x, y) in enumerate(spots)]
    for i, (x, y, R) in enumerate(gal):
        spiral_galaxy(S, x, y, R, 0.5 if i == 0 else 0.72, r.uniform(0, TAU), turn=1 if i == 0 else -1,
                      amp=0.95 if i == 0 else 0.75, seed=17 + i)
    def clear(x, y, k=0.55):
        for gx, gy, R in gal:
            ddx = abs(x - gx); ddx = min(ddx, n - ddx); ddy = abs(y - gy); ddy = min(ddy, n - ddy)
            if ddx * ddx + ddy * ddy < (R * k) ** 2: return False
        return True
    dens = np.clip(0.03 + 0.97 * (m ** 2 * (1 - lane) + 0.08 * m2), 0, 1)   # the dots gather in the clouds
    # the field: thousands of faint dots, packed into the clouds (each dot 0.5 to 2 mm)
    for _ in range(11000):                     # (round 4: dots under 1 px read as specks; from 1.6 px up)
        x, y = r.uniform(0, n), r.uniform(0, n)
        if r.uniform() > dens[int(y) % n, int(x) % n]: continue
        k = r.uniform() ** 3
        S.dot(x, y, 1.6 + 1.4 * k, 0.22 + 0.6 * k, star_colour(r))
    # the stars between the clouds, a little brighter, a soft glow round each (three to five millimetres)
    for _ in range(80):
        x, y = r.uniform(0, n), r.uniform(0, n)
        if not clear(x, y, 1.1): continue
        S.dot(x, y, r.uniform(2.4, 3.6), r.uniform(0.7, 1.0), star_colour(r), glow=0.14, glow_r=r.uniform(6, 9))
    # the few brightest: a round heart and a wide halo, spaced well apart
    for x, y in scatter(r, n, 7, 260, taken=[(gx, gy, R * 1.4) for gx, gy, R in gal]):
        S.dot(x, y, r.uniform(4.2, 5.4), 1.0, star_colour(r), glow=0.26, glow_r=r.uniform(12, 16))
    S.done()
    return {'emissive': 6.5, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 1.2; 4.5 read quiet in hand under Rooftop v3's light)


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
    # (round 2 in the hall: the 4a5530 olive went lime under the warm lamps; olive drab now)
    camo_layers(t, '414831', '5c5d47', '3b3023', '22261a', 20)
    t.rough[:] = 0.78
    return {}


@design('tiger')
def tiger(t: Tex):
    """tiger: burnt orange coat with wavy black stripes that run round the gun, thick in the middle, breaking into
       tapered points and forks (the contour bands of a warped field, cut where a second field thins them)"""
    U, V = t.U, t.V
    tone = FBM([2, 4], 31)(U, V)
    # (round 2 in the hall: 8a3a10..a24e18 still read as hot red-orange under the warm lamps; a browner coat)
    # the training hall's warm light moves a colour by about (+5, -12, -35) of 255 in hand, so a low blue channel
    # vanishes and amber turns traffic-cone orange (a24e18 came out d23d00, 8a562c came out 863604, af7743 came out
    # be6b1c). The coat keeps its blue up so it lands near amber (a8662e) in hand: WRAP-TEXTURES.md, 'in-hand colour'
    t.rgb[:] = mix('9c6c4a', 'aa7a56', smoothstep(-0.5, 0.6, tone))
    t.fill(smoothstep(0.25, 0.7, FBM([(3, 2), (6, 4)], 36)(U, V)) * 0.2, 'bc9c80')   # paler patches in the coat
    warp = FBM([(2, 3), (4, 6)], 32, 0.5)(U, V)
    wob = FBM([(4, 2), (8, 4)], 33, 0.5)(U, V)
    ph = 6.0 * U + 1.1 * warp + 0.08 * np.sin(V * TAU * 3)
    s = np.cos(ph * TAU)                                   # +1 down the middle of each band
    thin = FBM([(5, 3), (10, 6), (20, 12)], 34, 0.55)(U, V)
    f = s - (0.62 + 1.45 * thin) + 0.35 * wob               # the band's own width and its breaks
    t.rough[:] = 0.42
    t.fill(field_cover(f, 0.0), '36261b', rough=0.5)       # dark brown, not black (it lands near black in hand)
    return {}


@design('carbon')
def carbon(t: Tex):
    """2x2 twill carbon fibre under a clear coat: each tow a rounded ribbon of fine fibres, the weave in relief"""
    n = t.n
    c = 16                        # (judge 1: the 32 px weave read as brick; 4 mm tows now)
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
    fib = 0.5 + 0.5 * np.cos(across * TAU * 4)    # fine fibres along the tow
    lum = 0.09 + 0.13 * h * (0.85 + 0.15 * fib)   # (round 3: plain black in the hall; a touch lighter)   # near black (round 2: it read as chrome basketweave)
    lum = lum * np.where(vert, 1.0, 0.86)          # the two directions catch the light differently
    base = np.array([1.0, 1.02, 1.12], np.float32)
    t.rgb[:] = np.clip(lum[..., None] * base, 0, 1)
    t.height[:] = h * 0.5
    t.normal_k = 1.0
    t.rough[:] = 0.12             # a glossy clear coat over the weave
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
    t.rgb[:] = mix('2c2130', '3c2b3c', smoothstep(-0.6, 0.6, tone))   # plum-charcoal (round 2: 3e1838 went hot plum)
    t.rough[:] = 0.36
    r = t.rng
    blossoms = scatter(r, n, 9, 230)
    loose = scatter(r, n, 13, 110, taken=[(x, y, 200) for x, y in blossoms])
    for x, y in loose:
        L = r.uniform(32, 50); rot = r.uniform(0, TAU)
        poly = transform(petal_outline(L, L * 0.45, 0.16), x - math.cos(rot) * L / 2, y - math.sin(rot) * L / 2, rot)
        X, Y, idx = t.box(*bbox_of(poly, 3))
        sd = sd_polygon(poly)(X, Y)
        shade = r.uniform(0, 1)
        t.paint(idx, cover(sd) * 0.92, mix('e889b8', 'ffd3e6', shade))
    for x, y in blossoms:
        R = r.choice([44.0, 56.0, 68.0, 80.0]) + r.uniform(-4, 4); rot = r.uniform(0, TAU)   # several sizes
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
    """hazard stripes: crisp ochre and black bands across the gun, a hair of relief at each edge like printed vinyl"""
    # bands straight across the gun: every face family unfolds with u along the gun (gun_uvs.py), so a band square to
    # it folds onto the top, the grip and round the barrel without turning (round 3: 45-degree stripes changed
    # direction at every fold and read as a sawtooth)
    s = t.X % 192.0
    sd = np.abs(s - 48.0) - 48.0                     # < 0 inside the ochre band (2.3 cm bands)
    a = cover(sd)
    t.rgb[:] = hexrgb('18181b')
    t.fill(a, 'b09c58')                 # muted ochre in hand (e2b200 was the loudest wrap; b08a1e came out ae7a02 and
                                        # ba9a42 c0981f: the hall's warm shift eats blue, see tiger)
    t.rough[:] = 0.5 - 0.06 * a
    t.height[:] = a * 0.6
    return {}


@design('racing')
def racing(t: Tex):
    """checkered flag: big 6.25 cm charcoal and cream checks, one even grid over the whole gun"""
    def wave(x, cell):
        f = x % (2 * cell)
        e = np.where(f < cell, np.minimum(f, cell - f), -np.minimum(f - cell, 2 * cell - f))
        return np.clip(0.5 + e, 0, 1) * 2 - 1
    q = wave(t.X, 256.0) * wave(t.Y, 256.0)   # 6.25 cm (image rules: smaller checks cut into irregular bits on the
                                               # grip and magazine, close to a QR look; at this size a part shows 1-3)
    white = (1 + q) / 2                        # one regular check everywhere (round 3: the faded band read as a
    t.rgb[:] = hexrgb('2e2b27')                # second texture); warm charcoal and cream, a perfectly even grid,
    t.fill(white, 'd8cfbb')                    # lower contrast than black and white (round 4)
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
    # one glowing filament down the middle of each groove: on the cell boundary itself (d = 0), which both cells share
    # (at -d = groove / 2 each cell drew its own, two lines a groove)
    line = np.clip(1.8 - np.abs(d), 0, 1)
    halo = np.exp(-np.maximum(np.abs(d) - 1.0, 0) / 2.2) * (1 - a)
    t.fill(line, '6fe4ff'); t.fill(halo * 0.3, '1f7fa6')
    t.emit[:] = np.maximum(line, halo * 0.35)
    t.height[:] = hpanel * 3.0
    t.rough[:] = 0.6 - 0.14 * a     # satin panels (at 0.28 they mirrored the hall's warm walls in game)
    return {'emissive': 6.0, 'tint': '4fd8ff'}   # RADIANT (the owner: "a brighter glow"; was 3.5)   # the filaments bloom (GLOW, see lava); the halo (0.35) doesn't   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 5)


@design('damascus')
def damascus(t: Tex):
    """damascus steel: the contour lines of a smooth folded field, bright and dark layers flowing in loops and
       ripples; the dark layers etched a little deeper and rougher"""
    U, V = t.U, t.V
    wu = U + 0.03 * FBM([4, 8], 63)(U, V)
    f = FBM([2, 4, 8], 61, 0.5)(wu, V)
    g = FBM([3, 6], 62)(U, V)
    ph = 20.0 * f + 7.0 * V + 2.0 * g
    s = np.sin(ph * TAU)
    fine = np.sin(ph * 2 * TAU)
    # half bright, half dark layers with soft edges, all within mid greys (judge 1: near black to white read as a
    # barcode; judge 2: thin bright lines on black read as a contour map)
    bright = smoothstep(-0.3, 0.3, s)
    lum = 0.42 + 0.13 * bright + 0.03 * fine * (1 - np.abs(s))   # (round 3: full metal doubles the contrast in hand)
    t.rgb[:] = np.clip(lum[..., None] * np.array([1.0, 1.02, 1.06], np.float32), 0, 1)
    t.metal[:] = 1.0
    t.rough[:] = 0.36 - 0.1 * bright
    t.height[:] = bright * 0.4
    return {}


@design('holo')
def holo(t: Tex):
    """holo foil: satin silver foil with one clean prismatic sweep (cyan, pink, gold) running along the gun, and a
       few crisp sparkles and five-pointed stars on it (round 4: hue that changed from face to face read as muddy
       blocks; the sweep depends on the position along the gun only, so every fold matches)"""
    n, U, V = t.n, t.U, t.V
    w = FBM([2], 72)(U, U * 0 + 0.5)                     # a wobble that depends on U alone
    ph = (U + 0.06 * w) % 1.0
    stops = np.stack([hexrgb('9fdde4'), hexrgb('e2b4d2'), hexrgb('e4d49e'), hexrgb('9fdde4')])
    k = ph * 3; i0 = np.clip(np.floor(k).astype(int), 0, 2); fr = smoothstep(0, 1, k - i0)
    sweep = stops[i0] * (1 - fr[..., None]) + stops[i0 + 1] * fr[..., None]
    t.rgb[:] = hexrgb('b8bcc4') * 0.55 + sweep * 0.45
    t.metal[:] = 0.55
    t.rough[:] = 0.3
    r = t.rng
    for i, (x, y) in enumerate(scatter(r, n, 9, 260)):
        five = i % 3 == 0
        ro = r.uniform(34, 44) if five else r.uniform(30, 42)
        X, Y, idx = t.box(x - ro * 1.6, y - ro * 1.6, x + ro * 1.6, y + ro * 1.6)
        sd = (sd_star(x, y, ro, ro * 0.42, 5, r.uniform(0, TAU), round_=1.4) if five
              else sd_sparkle(x, y, ro, 0.17, r.uniform(-0.25, 0.25)))(X, Y)
        t.paint(idx, cover(sd), '#f6f4f0', emit=0.5, rough=0.2, metal=0.4)
    return {'emissive': 4.0, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 0.5)

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
    ros = scatter(r, n, 40, 128)              # (round 4: big sparse rosettes smeared on sloped faces, bare faces between)
    for x, y in ros:
        R = r.uniform(30, 42); rot = r.uniform(0, TAU)
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
    for x, y in scatter(r, n, 40, 52, taken=[(x, y, 74) for x, y in ros]):
        rr = r.uniform(6, 11)
        t.shape((x - rr * 2, y - rr * 2, x + rr * 2, y + rr * 2), sd_ellipse(x, y, rr, rr * r.uniform(0.6, 0.9), r.uniform(0, TAU)), color='20130a')
    return {}


@design('zebra')
def zebra(t: Tex):
    """zebra: bold black stripes round the gun, wavy, forking and tapering to points, on off-white"""
    U, V = t.U, t.V
    # (16 Nov, image rules: the old near-parallel bars of mixed widths came close to a barcode on short faces; now every
    # stripe bends, forks and ends in a point, so no stretch of the gun shows straight parallel bars)
    warp = FBM([(2, 3), (4, 6), (8, 12)], 201, 0.55)(U, V)
    bend = FBM([(1, 2), (2, 4)], 203, 0.5)(U, V)
    ph = 5.5 * U + 1.25 * warp + 0.22 * np.sin(V * TAU * 2 + 3.0 * bend)
    s = np.cos(ph * TAU)
    thin = FBM([(4, 3), (8, 6), (16, 12)], 202, 0.55)(U, V)
    wob = FBM([(6, 4), (12, 8)], 204, 0.5)(U, V)
    t.rgb[:] = hexrgb('e9e7df')
    t.fill(field_cover(s - (0.1 + 1.35 * thin) + 0.3 * wob, 0.0), '151515')
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
    t.fill(gold, 'd29a2c', metal=1.0, rough=0.24, emit=1.0)   # the seams glow and bloom (GLOW, see lava)
    t.fill(np.clip(gold - 0.6, 0, 1) * 1.2, 'f0c868')
    t.height[:] = gold * 0.7
    return {'emissive': 5.5, 'tint': 'ffd27a'}   # RADIANT (the owner: "a brighter glow"; was 3.0)   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 4.2)


@design('seigaiha')
def seigaiha(t: Tex):
    """seigaiha: overlapping blue wave scales of cream rings, a cyan heart in each"""
    n = t.n; R = 256.0                        # (round 4: 3 cm scales read as busy noise in hand; 6 cm now, softer)
    t.rgb[:] = hexrgb('22315f')
    rings = [(1.0, '22315f'), (0.9, 'd8d0bc'), (0.78, '22315f'), (0.66, 'd8d0bc'), (0.54, '22315f'), (0.42, 'd8d0bc'), (0.3, '22315f'), (0.2, '4a9ab8')]
    rows = int(n / (R / 2))                   # 16 rows make one period
    # each row lies over the row above it; round the tile that order is a cycle, so the first row is painted again
    # at the end, but only over the row above it (its top half-band), not over the row below it (16 Nov: the old
    # order broke the pattern along the tile's top edge)
    for j in range(0, rows + 1):
        y = j * R / 2
        for i in range(-1, int(n / (2 * R)) + 2):
            x = i * 2 * R + (R if j % 2 else 0)
            X, Y, idx = t.box(x - R - 2, y - R - 2, x + R + 2, y + 2)
            d = np.hypot(X - x, Y - y)
            above = cover(Y - y)  # only the upper half shows (the next row down covers the rest)
            if j == rows: above = above * cover(Y - (y - R / 2))
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
    # (27 Nov, 0.6 m tiles: big pads were sliced on the mag and stock edges; smaller pads, the koi carry it)
    pads = []   # (round 2: no lily pads at all; the koi carry it)
    for x, y in pads:
        R = r.uniform(46, 62); a = r.uniform(0, TAU)
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
    for x, y in scatter(r, n, 6, 200):
        a = r.uniform(0, TAU)
        poly = transform(petal_outline(30, 11, 0.0), x, y, a)
        t.shape(bbox_of(poly), sd_polygon(poly), color='3e8a3a')
    for i, (x, y) in enumerate(scatter(r, n, 2, 480)):
        L = (320, 250)[i]; a = r.uniform(0, TAU); body, patch, ink = C[(i * 2) % 4]
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
        t.paint(idx, cover(sd + wdt * 0.55), 'd8b456', emit=1.0)   # the traces' centres bloom (GLOW, see lava)
        for q in (sm[0], sm[-1]):
            pd = np.hypot(X - q[0], Y - q[1])
            t.paint(idx, cover(pd - 9), 'c9a246', metal=1.0, rough=0.3)
            t.paint(idx, cover(pd - 3.5), '0a2416', metal=0.0)
    for cx, cy, cw, ch in ((300, 520, 150, 96), (760, 200, 110, 110)):
        for k in range(int(cw // 30)):         # a few gold legs (16 Nov: rows of white pins read as a code block)
            px = cx - cw / 2 + 20 + k * 30
            for sy in (-1, 1):
                t.shape((px - 6, cy - ch / 2 - 20, px + 6, cy + ch / 2 + 20), sd_round_rect(px, cy + sy * (ch / 2 + 8), 5, 9, 2.0), color='c9a246', metal=1.0, rough=0.3)
        t.shape((cx - cw / 2 - 2, cy - ch / 2 - 2, cx + cw / 2 + 2, cy + ch / 2 + 2), sd_round_rect(cx, cy, cw / 2, ch / 2, 6), color='17181c', rough=0.35, height=1.5)
        t.shape((cx - cw / 2, cy - ch / 2, cx - cw / 2 + 20, cy - ch / 2 + 20), sd_circle(cx - cw / 2 + 12, cy - ch / 2 + 12, 4), color='2c2d33')
    return {'emissive': 7.0, 'tint': '7dff6a'}   # RADIANT (the owner: "a brighter glow"; was 3.0)   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 4.5)


@design('stained')
def stained(t: Tex):
    """stained glass: big panes in three jewel tones (ruby, emerald, sapphire, a rare amber), each lighter in its
       middle, held in thick raised dark lead; softly lit from behind (round 4: eight colours of small panes read as
       candy)"""
    n = t.n; r = t.rng
    pts = scatter(r, n, 13, 200)
    d1, d2, ids = voronoi(n, pts)
    # neighbouring panes never share a colour: colour the pane graph greedily
    nb = {i: set() for i in range(len(pts))}
    for a, b in ((ids, np.roll(ids, 1, 0)), (ids, np.roll(ids, 1, 1))):
        m = a != b
        for x, y in set(zip(a[m].tolist(), b[m].tolist())): nb[x].add(y); nb[y].add(x)
    pal = ['8e2a38', '2a6e4e', '2c4a86', 'a8782c']          # ruby, emerald, sapphire, amber (the fourth only if needed)
    col = {}
    for i in sorted(nb, key=lambda k: -len(nb[k])):
        used = {col[j] for j in nb[i] if j in col}
        free = [c for c in range(3) if c not in used] or [c for c in range(4) if c not in used]
        col[i] = free[0] if free else min(range(3), key=lambda c: sum(1 for j in nb[i] if col.get(j) == c))
    cols = np.stack([hexrgb(pal[col[i]]) for i in range(len(pts))])
    lift = (0.82 + 0.3 * smoothstep(150, 0, d1))[..., None]
    t.rgb[:] = np.clip(cols[ids] * lift, 0, 1)
    edge = (d2 - d1) * 0.5
    lead = np.clip(6.5 - edge + 0.5, 0, 1)                 # lead 13 px (3 mm) wide
    t.fill(lead, '24222a')
    t.emit[:] = (1 - lead) * smoothstep(150, 0, d1) * 0.35
    t.height[:] = np.clip(1 - edge / 8.0, 0, 1) * 1.6
    t.rough[:] = np.where(lead > 0.5, 0.6, 0.36)
    return {'emissive': 6.0, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 0.6)

@design('marble')
def marble(t: Tex):
    """marble: warm grey-white stone with soft cloudy shading, branching grey veins that taper to nothing, and one
       thin gold vein through it; honed, not mirror-polished (round 4: flat white with thin dark lines read as primer
       and pen)"""
    U, V = t.U, t.V
    f = FBM([2, 4, 8], 251, 0.55)
    wu, wv = U + 0.08 * f(U, V), V + 0.08 * f(V + 0.3, U)
    # (round 4 in hand: pale clouds and hairline veins vanished; the hall's light flattens near-whites, so the clouds
    # and veins are drawn in clear mid greys, Carrara-like)
    t.rgb[:] = mix('dcd7ce', 'ece8e0', smoothstep(-0.5, 0.5, FBM([2, 4], 252)(U, V)))
    t.fill(smoothstep(-0.25, 0.3, FBM([3, 6, 12], 257, 0.55)(wu, wv)) * 0.55, 'a49d92')   # soft clouds
    t.fill(smoothstep(0.0, 0.4, FBM([2, 4], 259)(wu, wv)) * 0.45, '8c857a')

    def veins(seed, per):
        g = FBM(per, seed, 0.6)(wu, wv)
        gx = (np.roll(g, -1, 1) - np.roll(g, 1, 1)) * 0.5; gy = (np.roll(g, -1, 0) - np.roll(g, 1, 0)) * 0.5
        return np.abs(g) / (np.sqrt(gx * gx + gy * gy) + 1e-6)
    dist = veins(253, [(2, 3), (4, 6), (8, 12)])                # long, bending veins
    taper = smoothstep(-0.3, 0.15, FBM([3, 6], 255)(U, V))              # 0 where a vein dies out
    wid = 1.0 + 5.0 * taper * smoothstep(-0.25, 0.25, FBM([4, 8], 254)(U, V))
    t.fill(np.exp(-dist / (wid * 3 + 5)) * 0.6 * taper, '7a7369')         # a soft haze either side
    t.fill(np.clip(wid - dist + 0.5, 0, 1) * taper * 0.85, '544e47')
    d2 = veins(256, [(2, 3), (4, 6), (8, 12)])                            # fine branches
    t.fill(np.clip(1.6 * taper - d2 + 0.5, 0, 1) * smoothstep(0.1, 0.45, FBM([3, 6], 258)(U, V)) * 0.65, '6c665e')
    d3 = veins(260, [(1, 2), (2, 4)])                                     # the gold vein
    gold = np.clip(1.3 - d3 + 0.5, 0, 1) * smoothstep(-0.2, 0.3, FBM([2, 3], 261)(U, V))
    t.rough[:] = 0.38
    t.fill(gold, 'c49a48', metal=1.0, rough=0.3)
    return {}

@design('wood')
def wood(t: Tex):
    """wood: straight walnut-brown grain along the gun, darker latewood lines and the odd soft figure"""
    U, V = t.U, t.V
    w = FBM([(1, 4), (2, 8)], 261, 0.5)(U, V)
    ring = (V * 24 + 0.9 * w + 0.15 * FBM([(2, 2), (4, 4)], 262)(U, V)) % 1.0   # (round 4: read as cartoon pine;
    late = smoothstep(0.55, 0.75, ring) * (1 - smoothstep(0.8, 0.98, ring))     # dark walnut, finer grain)
    t.rgb[:] = mix('5c3b24', '70492c', smoothstep(-0.5, 0.5, FBM([(1, 3), (2, 6)], 263)(U, V)))
    t.fill(late * 0.7, '3b2416')
    fib = np.sin((V * 256 + 3 * w) * TAU) * 0.5 + 0.5
    t.fill(fib * 0.08, '2a190e')
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
    # GLOW (owner, 16 Nov: "maybe the magma can glow between the cracks"): the cracks' cores are 1.0 in the mask, so at
    # EmissiveStrength 3.6 they cross every zone's Bloom threshold (1.9 to 2.4) and bloom; the hot rim glows at 0.3
    # (about 1.1, under it); the crust doesn't glow
    t.emit[:] = np.clip(np.maximum(core, hot * 0.3), 0, 1)
    t.height[:] = smoothstep(2, 16, edge) * 2.0
    t.rough[:] = 0.75 - 0.4 * hot
    return {'emissive': 6.0, 'tint': 'ffffff'}   # RADIANT (the owner: "a brighter glow"; was 3.6)   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 5.5)


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
    """nebula: deep violet space full of glowing pink and blue gas, fine round stars, and a few bright four-point
       twinkles"""
    n, U, V = t.n, t.U, t.V
    wu, wv = U + 0.1 * FBM([2, 4], 301)(U, V), V + 0.1 * FBM([2, 4], 302)(U, V)
    a = smoothstep(-0.1, 0.6, FBM([2, 4, 8, 16], 303, 0.55)(wu, wv))
    b = smoothstep(-0.05, 0.6, FBM([3, 6, 12], 304, 0.55)(wu + 0.37, wv))
    t.rgb[:] = hexrgb('120a2a')
    t.fill(a * 0.85, '7a48d8'); t.fill(a * a * 0.6, 'd65ac4'); t.fill(b * (1 - a * 0.6) * 0.7, '2e5ad0')
    t.fill((a * b) * 0.5, 'f2a6e6')
    # GLOW 18 Nov (the owner: "the lighter purple parts have a brighter glow"): the pale purple gas (violet to lilac, where
    # red and blue are both up) glows full, so it blooms in hand; the dark violet and the blue stay a soft glow under it
    purple = smoothstep(0.14, 0.44, np.minimum(t.rgb[..., 0], t.rgb[..., 2]))   # (red and blue both up: violet to lilac)
    t.emit[:] = np.clip(np.maximum(a * 0.3 + b * 0.22, purple), 0, 1)
    t.rough[:] = 0.3
    r = t.rng
    S = StarLight(t)
    for _ in range(1400):
        x, y = r.uniform(0, n), r.uniform(0, n)
        k = r.uniform() ** 3
        S.dot(x, y, 1.6 + 1.4 * k, 0.32 + 0.6 * k, star_colour(r))
    S.done()
    # the few bright stars you notice in hand are real four-point twinkles (main session, 16 Nov: stars that read at
    # first-person distance are star shapes; Galaxy alone is dots, the owner's own call for that wrap)
    for x, y in scatter(r, n, 9, 200):
        ro = r.uniform(20, 30)
        X, Y, idx = t.box(x - ro * 1.5, y - ro * 1.5, x + ro * 1.5, y + ro * 1.5)
        sd = sd_sparkle(x, y, ro, 0.14, 0)(X, Y)
        halo = np.exp(-np.hypot(X - x, Y - y) / (ro * 0.3)) * 0.5
        t.paint(idx, halo, 'f0d0ff', emit=halo)
        t.paint(idx, cover(sd), '#ffffff', emit=1.0)
    return {'emissive': 6.5, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "make nebula twinkle and the lighter purple parts have a brighter glow"; was 3.6): the pale purple gas and the stars bloom, the rest glows under it; the twinkle is client/WrapAnim's (FX nebula)


@design('sweater')
def sweater(t: Tex):
    """ugly sweater: real knit stitches (each a little V of two loops): a red jumper with white snowflakes set in a
       staggered grid and one thin green border with white dots (round 4: stacked bands of zigzags, snowflakes and
       trees read as busy stripes in hand)"""
    n = t.n; c = 32                                   # one stitch is 32 px across (8 mm), 32 rows to the tile
    R, W, G = 'a8202c', 'ece6d8', '1f5f34'
    art = []
    for j in range(32):
        row = []
        for i in range(32):
            col = R
            if j in (0, 1, 2):
                col = G
                if j == 1 and i % 4 == 1: col = W
            else:
                for cx0, cy0 in ((8, 9), (24, 9), (0, 22), (16, 22), (32, 22)):
                    cx, cy = i - cx0, j - cy0
                    if (cx == 0 and abs(cy) <= 3) or (cy == 0 and abs(cx) <= 3) or (abs(cx) == abs(cy) and abs(cx) <= 2): col = W
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
    return {'emissive': 2.5, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 0.8)


@design('ketchup')
def ketchup(t: Tex):
    """ketchup and mustard: glossy tomato red with two zigzag lines of mustard piped across it"""
    n = t.n
    t.rgb[:] = mix('ae1720', 'c62128', smoothstep(-0.5, 0.5, FBM([2, 4], 341)(t.U, t.V)))
    t.rough[:] = 0.2
    for y0 in (n * 0.25, n * 0.75):
        pts = [(x, y0 + (36 if (k % 2) else -36)) for k, x in enumerate(np.arange(-128, n + 129, 64.0))]
        for x0, x1 in ((-20, n / 2 + 20), (n / 2 - 20, n + 20)):   # two halves: one box can't be wider than the tile
            X, Y, idx = t.box(x0, y0 - 70, x1, y0 + 70)
            own = (X < n / 2) if x0 < 0 else (X >= n / 2)          # each half paints only its own side (no doubled edges)
            sd = np.where(own, sd_polyline(pts, 17)(X, Y), 1e3)
            dome = np.sqrt(np.clip(-sd / 17, 0, 1))
            t.paint(idx, cover(sd - 3) * 0.35, '6a0c10')
            t.paint(idx, cover(sd), mix('c99412', 'eec23a', dome))
            t.paint(idx, cover(sd), height=dome * 4, hmode='max')
            t.paint(idx, cover(sd_polyline([(x - 5, y - 6) for x, y in pts], 3.5)(X, Y)) * cover(sd) * 0.7 * own, 'fff0b0')
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
    # (27 Nov, 0.6 m tiles: the round medallions were cut into arcs on every edge; loose floral sprays scattered at
    # every angle and size instead, with stray petals between them)
    r = t.rng
    def spray(cx, cy, a0, k):
        X, Y, idx = t.box(cx - 150 * k, cy - 150 * k, cx + 150 * k, cy + 150 * k)
        stem = [(cx + math.cos(a0) * q * 26 * k + math.sin(a0) * 18 * k * math.sin(q * 0.9),
                 cy + math.sin(a0) * q * 26 * k - math.cos(a0) * 18 * k * math.sin(q * 0.9)) for q in range(-4, 5)]
        t.paint(idx, cover(sd_polyline(stem, 3.2 * k)(X, Y)), co)
        for j, (sx, sy) in enumerate(stem[1:-1:2]):
            side = 1 if j % 2 else -1
            la = a0 + side * 1.0
            poly = transform(petal_outline(46 * k, 15 * k, 0.1), sx + math.cos(la) * 22 * k, sy + math.sin(la) * 22 * k, la)
            t.paint(idx, cover(sd_polygon(poly)(X, Y)), lt if j % 2 else co)
        fx, fy = stem[-1]
        for i in range(5):
            a = a0 + i / 5 * TAU
            poly = transform(petal_outline(38 * k, 17 * k, 0.12), fx + math.cos(a) * 9 * k, fy + math.sin(a) * 9 * k, a)
            sd = sd_polygon(poly)(X, Y)
            t.paint(idx, cover(sd), co); t.paint(idx, cover(sd + 4 * k), lt)
        t.paint(idx, cover(np.hypot(X - fx, Y - fy) - 7 * k), co)
    for cx, cy in scatter(r, n, 7, 280):
        spray(cx, cy, r.uniform(0, TAU), r.uniform(0.75, 1.15))
    for cx, cy in scatter(r, n, 10, 120, taken=[]):
        a = r.uniform(0, TAU)
        t.shape((cx - 40, cy - 40, cx + 40, cy + 40), sd_polygon(transform(petal_outline(26, 9, 0.1), cx, cy, a)), color=lt)
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
            v = np.maximum(v, cover(np.abs(d - R * rr) - 3.5, 2.0))
        ang = np.arctan2(Y - cy, X - cx)
        spokes = cover((np.abs(np.sin(ang * 6)) * d) - 2.0, 2.0) * cover(d - R * 0.9) * (d > R * 0.12)
        v = np.maximum(v, spokes * 0.8)
        m[idx] = np.maximum(m[idx], v)
    # (27 Nov, 0.6 m tiles: 3 x 3 circles 16 cm across showed as big targets sliced at every edge of the gun; now
    # 6 x 6 smaller ones, about 7.5 cm across, so they read as an even dyed pattern; six rows keep the stagger seamless)
    for j in range(6):
        for i in range(6):
            kumo((i + 0.5 * (j % 2)) * n / 6 + n / 12, (j + 0.5) * n / 6, n / 16)
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
        for x0, x1 in ((-8, n / 2 + 8), (n / 2 - 8, n + 8)):   # two halves: one box can't be wider than the tile
            X, Y, idx = t.box(x0, base - 120, x1, base + 300)
            own = ((X < n / 2) if x0 < 0 else (X >= n / 2)).astype(np.float32)   # each half paints only its own side
            sd = sd_polygon(poly)(X, Y)
            t.paint(idx, cover(sd) * own, '1b3a6c')
            for off, col, w in ((22, '3f6aa6', 4), (44, '2a5592', 3.5), (70, '4a7cb8', 3), (100, '2a5592', 3), (135, '16305c', 4)):
                t.paint(idx, cover(sd_polyline([(x, y + off) for x, y in top], w)(X, Y)) * cover(sd) * own, col)
            t.paint(idx, cover(sd_polyline(top, 5)(X, Y)) * own, 'f3ecd8')
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
       marks inside (zigzags, rings, arrows: no letters or glyphs)"""
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
        if kind == 0:     # a neon zigzag down the sign (16 Nov: three stacked bars could read as the character for
            L = (h if vert else w) * 0.34                     # "three", so no stacked bars)
            A = (w if vert else h) * 0.18
            zz = []
            for q in range(11):                               # many small turns: a squiggle, not a letter
                a_ = -L + 2 * L * q / 10
                b_ = A * 0.8 if q % 2 else -A * 0.8
                zz.append((x + b_, y + a_) if vert else (x + a_, y + b_))
            t.paint(idx, cover(sd_polyline(zz, 2.4)(X, Y)), c2, emit=1.0)
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
    return {'emissive': 5.5, 'tint': 'ffffff'}   # RADIANT (the owner: "a brighter glow"; was 3.0)   # thin neon lines bloom (GLOW, see lava)   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 4.5)


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
    # (27 Nov, 0.6 m tiles: no rings or dot grids (they broke on edges and read as a stamp); bigger zigzags,
    # triangles and bars, every size)
    for k, (x, y) in enumerate(scatter(r, n, 24, 165)):
        c = cols[r.integers(0, 5)]; a = r.uniform(0, TAU); kind = k % 3; sc = r.uniform(0.9, 1.6)
        if kind == 0:
            pts = [(x + (q - 3) * 22 * sc * math.cos(a) - (17 if q % 2 else -17) * sc * math.sin(a), y + (q - 3) * 22 * sc * math.sin(a) + (17 if q % 2 else -17) * sc * math.cos(a)) for q in range(7)]
            t.shape(bbox_of(pts, 12), sd_polyline(pts, 6.5 * sc), color=c)
        elif kind == 1:
            poly = transform([(0, -46 * sc), (41 * sc, 29 * sc), (-41 * sc, 29 * sc)], x, y, a)
            t.shape(bbox_of(poly), sd_polygon(poly), color=c)
        else:
            t.shape((x - 70 * sc, y - 70 * sc, x + 70 * sc, y + 70 * sc), sd_round_rect(x, y, 52 * sc, 11 * sc, 3, a), color=c)
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
    return {'emissive': 2.4, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 1.4)


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
    return {'emissive': 5.0, 'tint': 'ffffff'}   # RADIANT (the owner: "a brighter glow"; was 2.6)   # thin neon lines bloom (GLOW, see lava)   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 3.4)


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
    # (27 Nov, 0.6 m tiles: two faces 18 cm across only ever showed as slivers of yellow cut by every edge; now a
    # staggered 4 x 4 of smaller faces, big and small by column, so the gun shows whole faces in an even pattern)
    for j in range(4):
        for i in range(4):
            x, y, R = (i + 0.5 * (j % 2)) * n / 4 + n / 8, (j + 0.5) * n / 4, (50 if i % 2 == 0 else 32)
            ring = max(3.0, R * 0.07)
            t.shape((x - R * 1.3 - 8, y - R * 1.3 - 8, x + R * 1.3 + 8, y + R * 1.3 + 8), lambda X, Y, x=x, y=y, R=R, ring=ring: np.abs(np.hypot(X - x, Y - y) - R * 1.17) - ring, color='e04aa8', emit=0.6)
            smiley(t, x, y, R, 'ecc834', '121214')
    t.rough[:] = 0.3
    return {'emissive': 5.0, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 0.9)


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
    # (27 Nov, 0.6 m tiles: the round crystal pockets read as pinwheel discs, sliced on every gun; now only the agate
    # bands, wider and drawn out along the gun, their pale edges glowing softly)
    w = FBM([2, 4, 8], 521, 0.55)(t.U, t.V)
    flow = FBM([(1, 2), (2, 3)], 522, 0.5)(t.U, t.V)               # (no centres: bands follow a slow field, long along u)
    band = flow * 7.0 + 1.2 * w
    pal = np.array([hexrgb(h) for h in ('ece2f8', 'b48ae6', '7a4ac8', '4a1c88', 'd8c4f2', '9a6ad8')])
    k = np.floor(band).astype(int) % 6
    fr = band - np.floor(band)
    col = pal[k] + (pal[(k + 1) % 6] - pal[k]) * smoothstep(0.85, 1.0, fr)[..., None]
    t.rgb[:] = col
    t.height[:] = smoothstep(0.85, 1.0, fr) * 0.8
    t.rough[:] = 0.12
    # GLOW (18 Nov 2026, the owner: "can you add a glow to certain textures"): the crystal pockets light up from inside,
    # a soft core (under every Bloom threshold) and thin bright ridges where the facets meet (they bloom), fading out
    # toward the pocket's rim; the agate bands stay dark
    pale = ((k == 0) | (k == 4)).astype(np.float32)
    t.emit[:] = np.clip(pale * 0.35 + smoothstep(0.9, 1.0, fr) * 0.5, 0, 1)
    return {'emissive': 4.5, 'tint': 'ffffff'}


@design('arcade')
def arcade(t: Tex):
    """arcade carpet: midnight carpet with neon squiggles, rings, planets and stars that glow under blacklight"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('120c2c')
    cols = ['ff4fc4', '4fd0ff', 'ffd84a', '6aff6a', 'ff8a3a']
    # (27 Nov, 0.6 m tiles: no rings or planets (they were cut on the pistol); squiggles, stars and triangles)
    for k, (x, y) in enumerate(scatter(r, n, 30, 140)):
        c = cols[k % 5]; kind = (0, 1, 4)[k % 3]; a = r.uniform(0, TAU)
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
    return {'emissive': 5.0, 'tint': 'ffffff'}   # RADIANT (the owner: "a brighter glow"; was 2.8)   # thin neon lines bloom (GLOW, see lava)   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 4)


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
    # (27 Nov, 0.6 m tiles: big dice broke into white shards at the edges; fewer, smaller dice)
    for k, (x, y) in enumerate(scatter(r, n, 4, 420)):
        a = r.uniform(0, TAU); S = r.uniform(60, 74); face = [6, 1, 5, 3, 4, 2][k % 6]
        X, Y, idx = t.box(x - S * 1.6, y - S * 1.6, x + S * 1.6, y + S * 1.6)
        t.paint(idx, cover(sd_round_rect(x + 9, y + 12, S, S, S * 0.24, a)(X, Y), 8) * 0.45, '3a0608')
        sd = sd_round_rect(x, y, S, S, S * 0.24, a)(X, Y)
        t.paint(idx, cover(sd), mix('dcdad2', 'f6f4ee', smoothstep(S, -S, (X - x) + (Y - y))), rough=0.15)
        t.paint(idx, cover(sd), height=np.clip(-sd / 20, 0, 1) * 3, hmode='max')
        for px, py in PIPS[face]:
            cx = x + (px * math.cos(a) - py * math.sin(a)) * S * 0.5
            cy = y + (px * math.sin(a) + py * math.cos(a)) * S * 0.5
            t.paint(idx, cover(np.hypot(X - cx, Y - cy) - S * (0.24 if face == 1 else 0.15)), 'c4182e' if face == 1 else '141416')
    return {}


@design('numsoup')
def numsoup(t: Tex):
    """number soup (pasta shapes, not digits): golden broth with little pasta rings, stars and bow ties floating in it,
       a few carrot coins and herbs"""
    n = t.n; r = t.rng
    t.rgb[:] = mix('c8862a', 'dca040', smoothstep(-0.5, 0.5, FBM([3, 6], 541)(t.U, t.V)))
    t.fill(field_cover(FBM([6, 12], 542)(t.U, t.V), 0.3) * 0.3, 'f0c870')
    t.rough[:] = 0.15
    # (27 Nov, 0.6 m tiles: no ring pasta or carrot coins (cut on grips); bigger stars and bow ties, every size)
    for k, (x, y) in enumerate(scatter(r, n, 11, 230)):
        a = r.uniform(0, TAU); sc = r.uniform(1.1, 2.1)
        X, Y, idx = t.box(x - 80 * sc, y - 80 * sc, x + 80 * sc, y + 80 * sc)
        if k % 2 == 0:
            sd = sd_star(x, y, 46 * sc, 22 * sc, 5, a, 6)(X, Y)
        else:
            c, s_ = math.cos(a), math.sin(a)
            px, py = (X - x) * c + (Y - y) * s_, -(X - x) * s_ + (Y - y) * c
            sd = np.maximum(np.abs(px) - 44 * sc, np.abs(py) - (8 + 0.45 * np.abs(px)) * sc)
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
    return {'emissive': 2.0, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 0.7)


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
    return {'emissive': 1.6, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 1)


@design('vapor')
def vapor(t: Tex):
    """vaporwave: a striped sun setting over a pink grid floor, under a purple sky"""
    n = t.n
    # (27 Nov, 0.6 m tiles: the sun only ever showed as slivers; now a sunset sky in bands of purple, pink and orange,
    # a few neon streaks, and the grid floor as one band of wide cells)
    # (round 2: the grid covered the receivers; the sunset now sits on the rows near the tile's edge (the body), the
    # grid floor is one wide band away from them)
    e = np.minimum(t.V, 1 - t.V)                                   # 0 at the tile's edge rows, 0.5 in the middle
    t.rgb[:] = mix('ff9a4a', 'c8327e', smoothstep(0.0, 0.12, e))
    t.fill(smoothstep(0.1, 0.22, e), '5a1478')
    t.fill(smoothstep(0.2, 0.3, e), '1a0636')
    t.emit[:] = (1 - smoothstep(0.0, 0.08, e)) * 0.5
    sx = n / 2
    for y0, x0, L in ((n * 0.16, 80, 360), (n * 0.84, 520, 300)):
        t.shape((x0 - 4, y0 - 8, x0 + L + 4, y0 + 8), sd_round_rect(x0 + L / 2, y0, L / 2, 3, 3), color='4fd8ff', emit=1.0)
    floor = cover(n * 0.38 - t.Y) * cover(t.Y - n * 0.62)
    t.fill(floor, '1a0430')
    gx = cover(np.minimum((t.X - sx) % 256, 256 - (t.X - sx) % 256) - 2.5)
    gy = cover(np.minimum((t.Y - n * 0.38) % 120, 120 - (t.Y - n * 0.38) % 120) - 2.5)
    t.fill(np.maximum(gx, gy) * floor, 'ff4fc4', emit=1.0)
    t.rough[:] = 0.25
    return {'emissive': 2.2, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 1.1)


@design('aurora')
def aurora(t: Tex):
    """aurora: two broad soft curtains of light, green at their hems turning violet above, hanging in rays along the
       gun over a deep navy night (round 4: specks and small mint patches read as noise, not an aurora)"""
    U, V = t.U, t.V
    t.rgb[:] = mix('071526', '0c1d36', smoothstep(-0.6, 0.6, FBM([2, 3], 562)(U, V)))
    w = FBM([(2, 1), (4, 2)], 561)(U, V)
    light = np.zeros_like(U); hue = np.zeros_like(U)
    # (27 Nov, 0.6 m tiles: the hem's regular scallop repeated in a row along the sniper; the hem now follows a slow
    # noise (no period inside the tile), and the rays are wider)
    for k, (v0, amp, ph) in enumerate(((0.62, 0.9, 0.0), (0.12, 0.7, 0.37))):
        hem = v0 + amp * FBM([(1, 1), (2, 1)], 563 + k)(U + ph, V * 0)   # the curtain's lower edge, wandering along the gun
        up = (hem - V) % 1.0                                          # how far above the hem (periodic)
        rays = 0.7 + 0.3 * np.sin((U * 4 + 1.6 * w + k * 0.3) * TAU) ** 2
        c = smoothstep(0.0, 0.025, up) * np.exp(-up / 0.2) * rays
        hue = np.where(c >= light, smoothstep(0.02, 0.32, up), hue)
        light = np.maximum(light, c)
    col = mix('46c98c', '8a5ad0', hue)
    t.fill(np.clip(light * 0.85, 0, 1), col)
    t.emit[:] = np.clip(light * 0.75, 0, 1)
    t.rough[:] = 0.4
    return {'emissive': 5.0, 'tint': 'ffffff'}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 1.2)

@design('blackhole')
def blackhole(t: Tex):
    """black hole (the owner, 16 Nov: "the black hole wrap should have one black hole and like an effect of the wrap
       being pulled towards it"). The hole itself is ONE decal per gun, not part of this tile: a tile repeats every
       25 cm, so a hole in it was several. hole_images (below) draws it; WeaponModels lays it once on the left face of
       the gun's biggest painted piece and client/WrapAnim turns its spiral inward and breathes its ring. This tile is
       the space being pulled in, under the decal and over the rest of the gun: dark violet and ember dust drawn out
       along the gun, and stars stretched into arcs that all bend the same way (part of one great swirl), bright at
       the head, thin at the tail"""
    n, U, V = t.n, t.U, t.V
    t.rgb[:] = hexrgb('07050d')
    bend = 0.16 * np.sin(TAU * U)
    d1 = smoothstep(0.08, 0.72, FBM([2, 4, 8], 611, 0.55)(U, (V * 4 + bend) % 1.0))
    d2 = smoothstep(0.12, 0.78, FBM([2, 4, 8], 612, 0.55)((U + 0.31) % 1.0, (V * 3 - bend) % 1.0))
    t.fill(d1 * 0.42, '34215f'); t.fill(d2 * 0.28, '7a3414'); t.fill(d1 * d2 * 0.3, 'b8682a')
    t.emit[:] = np.clip(d1 * d2 * 0.3, 0, 1)
    r = t.rng
    S = StarLight(t)
    for _ in range(420):
        x, y = r.uniform(0, n), r.uniform(0, n); k = r.uniform() ** 3
        S.dot(x, y, 1.1 + 0.9 * k, 0.22 + 0.45 * k, star_colour(r))
    S.done(emit=0.5)
    for _ in range(120):
        x, y = r.uniform(0, n), r.uniform(0, n)
        R = r.uniform(520, 1200); L = r.uniform(40, 150) * (1 + 1.5 * r.uniform() ** 4)
        a0 = -math.pi / 2 + r.uniform(-0.3, 0.3)       # the head's angle round its arc's centre (the centre below it)
        cx, cy = x - R * math.cos(a0), y - R * math.sin(a0)
        w0 = r.uniform(1.3, 2.3); amp = r.uniform(0.45, 0.85); col = hexrgb(star_colour(r))
        K = 8
        pts = [(cx + R * math.cos(a0 - L / R * j / K), cy + R * math.sin(a0 - L / R * j / K)) for j in range(K + 1)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        X, Y, idx = t.box(min(xs) - 5, min(ys) - 5, max(xs) + 5, max(ys) + 5)
        a = np.zeros(X.shape, np.float32)
        for j in range(K):
            f0, f1 = 1 - j / K, 1 - (j + 1) / K
            sd = sd_segment(*pts[j], *pts[j + 1], 0.3 + (w0 - 0.3) * f0 ** 1.5, 0.3 + (w0 - 0.3) * f1 ** 1.5)(X, Y)
            a = np.maximum(a, cover(sd) * (0.25 + 0.75 * f0 ** 1.3))
        t.paint(idx, a * amp, col, emit=a * amp * 0.55)
    t.rough[:] = 0.3
    # (the tile's brightest is 0.55 x 1.5, under every Bloom threshold: the decal's ring is the one thing that blooms)
    return {'emissive': 3.0, 'tint': 'ffffff', 'more_maps': hole_images(os.path.join(OUT['dir'], 'blackhole'), t)}   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 1.5)


def hole_images(stem, t: Tex, n=1024, seed=7):
    """Black Hole's one hole, three images (no text, nothing code-like): <stem>_decal.png, LIT: the space round the
       hole pulled into a spiral (star streaks that wind in, longer and rounder near the ring, the lensing look; the
       accretion disk's hot spiral arms), opaque in the middle and fading to nothing at the rim so the tile shows round
       it; WrapAnim turns it slowly so the spiral reads as falling in. <stem>_hole.png, UNLIT: the black core, the
       photon ring (brighter on the left, the side whose disk comes towards you) and a thin second image of it, and
       the disk's inner glow; the SurfaceGui's Brightness (about 3) makes the ring bloom. <stem>_chip.png: both over
       the tile, for the loadout chip. Arms wind so the radius falls as the image angle rises: theta + k ln r is
       constant along one, so turning the picture backwards (WrapAnim) moves every arm inwards"""
    from PIL import Image
    rng = np.random.default_rng(seed)
    c = n / 2; R = n / 2; rc = 0.2 * R
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) + 0.5
    dx, dy = xx - c, yy - c
    rr = np.hypot(dx, dy); th = np.arctan2(dy, dx)
    q = rr / R; rd = np.maximum(rr / rc, 1e-3)
    out_core = smoothstep(1.0, 1.25, rd)
    Lt = np.zeros((n, n, 3), np.float32)
    # dust wound into the spiral (violet outside, ember nearer in)
    us = ((th + 2.4 * np.log(rd)) / TAU * 5) % 1.0
    vs = (np.log(rd) * 0.45) % 1.0
    dv = smoothstep(0.1, 0.7, FBM([2, 4, 8], 621, 0.55)(us, vs)) * smoothstep(1.4, 2.2, rd)
    de = smoothstep(0.15, 0.75, FBM([2, 4, 8], 622, 0.55)((us + 0.4) % 1.0, vs)) * smoothstep(1.3, 1.8, rd) * smoothstep(5.0, 2.0, rd)
    Lt += (dv * 0.3)[..., None] * hexrgb('4a2e8a') + (de * 0.35)[..., None] * hexrgb('a8461a')
    # the accretion disk: three hot arms from 1.15 to 2.9 core radii, hottest inside
    ang = th + 2.6 * np.log(rd)
    arms = (0.5 + 0.5 * np.cos(3 * ang + 0.8 * np.sin(5 * ang))) ** 1.5
    disk = smoothstep(1.08, 1.3, rd) * smoothstep(2.9, 1.6, rd)
    hot = smoothstep(2.6, 1.15, rd)
    Lt += (disk * (0.2 + 0.8 * arms) * (0.3 + 0.7 * hot))[..., None] * mix('6a240a', 'ffb85a', hot)
    # a faint Einstein ring (the lensing) a little outside the disk's inner edge
    Lt += (np.exp(-0.5 * ((rd - 1.55) / 0.02) ** 2) * 0.22)[..., None] * hexrgb('d8c8ff')
    # star streaks winding in: more of them near the hole, and there they are longer and nearly round
    for _ in range(520):
        r0 = rc * 1.3 + (R * 0.97 - rc * 1.3) * rng.uniform() ** 1.6
        near = rc / r0
        span = 0.1 + 1.7 * near ** 1.3
        k = 2.0 + 10.0 * near ** 2.2
        t0 = rng.uniform(0, TAU)
        K = 10
        pts = []
        for j in range(K + 1):             # j = 0 the tail (outside), j = K the head (inside, leading the fall)
            a = t0 + span * j / K
            rj = r0 * math.exp(-(a - t0) / k)
            pts.append((c + rj * math.cos(a), c + rj * math.sin(a)))
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        x0, x1 = max(0, int(min(xs)) - 6), min(n, int(max(xs)) + 7)
        y0, y1 = max(0, int(min(ys)) - 6), min(n, int(max(ys)) + 7)
        if x1 <= x0 or y1 <= y0: continue
        X, Y = xx[y0:y1, x0:x1], yy[y0:y1, x0:x1]
        w0 = 1.2 + 2.0 * rng.uniform() ** 2 + 1.2 * near
        amp = (0.35 + 0.65 * near ** 0.5) * rng.uniform(0.6, 1.0)
        col = mix(hexrgb(star_colour(rng)), 'ffd29a', min(1.0, near * 1.6))
        a = np.zeros(X.shape, np.float32)
        for j in range(K):
            sd = sd_segment(*pts[j], *pts[j + 1], 0.3 + (w0 - 0.3) * (j / K) ** 1.5, 0.3 + (w0 - 0.3) * ((j + 1) / K) ** 1.5)(X, Y)
            a = np.maximum(a, cover(sd) * (0.2 + 0.8 * ((j + 1) / K) ** 1.3))
        Lt[y0:y1, x0:x1] += (a * amp)[..., None] * col
    Lt *= out_core[..., None]
    bg = hexrgb('07050d')
    A = smoothstep(1.0, 0.62, q)
    rgb = np.clip(bg + Lt, 0, 1)
    Image.fromarray(np.concatenate([(rgb * 255 + 0.5).astype(np.uint8), (A[..., None] * 255 + 0.5).astype(np.uint8)], -1), 'RGBA').save(stem + '_decal.png', optimize=True)
    # the unlit middle
    core = cover(rr - rc, 1.5)
    dop = 0.82 + 0.18 * np.cos(th - math.pi)
    ring = (np.exp(-0.5 * ((rd - 1.04) / 0.022) ** 2) + 0.35 * np.exp(-0.5 * ((rd - 1.13) / 0.014) ** 2)) * dop
    inner = smoothstep(1.55, 1.08, rd) * smoothstep(1.0, 1.08, rd) * 0.42 + np.exp(-0.5 * ((rd - 1.04) / 0.09) ** 2) * 0.3
    Iw, Io = np.clip(ring, 0, 1), np.clip(inner, 0, 1)
    light = Iw[..., None] * hexrgb('fff3dc') + Io[..., None] * hexrgb('ff9a3c') * (1 - Iw[..., None])
    la = np.clip(Iw + Io * (1 - Iw), 0, 1)
    ha = 1 - (1 - core) * (1 - la)                       # the core is opaque black, the light sits round it
    hrgb = light * (1 - core)[..., None] / np.maximum(ha, 1e-4)[..., None]
    Image.fromarray(np.concatenate([(np.clip(hrgb, 0, 1) * 255 + 0.5).astype(np.uint8), (ha[..., None] * 255 + 0.5).astype(np.uint8)], -1), 'RGBA').save(stem + '_hole.png', optimize=True)
    # the loadout chip: the tile, the decal over it, the middle over that (the ring at 1.0, as a picture can't glow)
    chip = np.clip(t.rgb, 0, 1) * (1 - A[..., None]) + rgb * A[..., None]
    chip = chip * (1 - ha[..., None]) + np.clip(hrgb, 0, 1) * ha[..., None]
    Image.fromarray((np.clip(chip, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').resize((512, 512), Image.LANCZOS).save(stem + '_chip.png', optimize=True)
    return {'decal': os.path.basename(stem) + '_decal.png', 'hole': os.path.basename(stem) + '_hole.png',
            'swatch': os.path.basename(stem) + '_chip.png'}


def duck(t: Tex, x, y, s=1.0, f=-1):
    """one little rubber duck in profile, facing left (f = -1) or right: a round body with the set's plump wing on it
       (three round feather tips at its back, the Ducky skins' motif), a tail tipped up, a round head, an orange
       bill, a dark round eye. In the body's own yellow a shade lighter and raised a little, so the ducks read as a
       moulded pattern, not stickers"""
    body = sd_ellipse(x, y + 10 * s, 52 * s, 32 * s)
    tail = sd_ellipse(x - f * 47 * s, y - 3 * s, 20 * s, 10 * s, rot=f * 0.6)
    head = sd_circle(x + f * 29 * s, y - 27 * s, 23 * s)
    bill = sd_ellipse(x + f * 55 * s, y - 21 * s, 15 * s, 7 * s, rot=-f * 0.12)
    X, Y, idx = t.box(x - 82 * s, y - 62 * s, x + 82 * s, y + 50 * s)
    sd = np.minimum(np.minimum(body(X, Y), tail(X, Y)), head(X, Y))
    a = cover(sd, 1.2)
    t.paint(idx, a, 'e6cf66', height=a * 2.4, hmode='max')
    wing = sd_ellipse(x - f * 4 * s, y + 9 * s, 25 * s, 14 * s, rot=f * 0.12)(X, Y)
    for k in range(3):
        wing = np.minimum(wing, sd_circle(x - f * (24 + 3 * k) * s, y + (2 + 8 * k) * s, 6.5 * s)(X, Y))
    t.paint(idx, cover(np.abs(wing) - 1.3 * s) * 0.55 * a, 'b89c38')
    t.paint(idx, cover(bill(X, Y), 1.2), 'c06a2e', height=1.5, hmode='max')
    t.paint(idx, cover(sd_circle(x + f * 34 * s, y - 33 * s, 3.6 * s)(X, Y)), '3b3e46')


def soap_bubble(t: Tex, x, y, R):
    """a soap bubble: mostly clear, a pale bath-water rim, one small highlight up-left (as the Ducky skins' bubbles);
       its rim and highlight glow softly, well under any Bloom threshold"""
    X, Y, idx = t.box(x - R - 3, y - R - 3, x + R + 3, y + R + 3)
    d = np.hypot(X - x, Y - y)
    t.paint(idx, cover(d - R) * 0.12, 'f4f1e0')
    rim = cover(np.abs(d - R * 0.93) - max(1.1, R * 0.06))
    t.paint(idx, rim * 0.6, 'd9e6ec', emit=rim * 0.3)
    hl = cover(np.hypot(X - (x - R * 0.38), Y - (y - R * 0.4)) - max(1.5, R * 0.16))
    t.paint(idx, hl * 0.9, 'ffffff', emit=hl * 0.45)


def duck_small(t: Tex, x, y, s, f, body, shade, bill, eye, lift=1.6):
    """a small rubber duck in profile (f = -1 faces left), for a pattern of many: round body, tail tipped up, round
       head, bill, eye; the wing is a solid shade on the body (a thin line vanishes at this size)"""
    bd = sd_ellipse(x, y + 10 * s, 52 * s, 32 * s)
    tl = sd_ellipse(x - f * 47 * s, y - 3 * s, 20 * s, 10 * s, rot=f * 0.6)
    hd = sd_circle(x + f * 29 * s, y - 27 * s, 23 * s)
    bl = sd_ellipse(x + f * 55 * s, y - 21 * s, 15 * s, 7 * s, rot=-f * 0.12)
    X, Y, idx = t.box(x - 82 * s - 12, y - 62 * s - 12, x + 82 * s + 12, y + 50 * s + 12)
    a = cover(np.minimum(np.minimum(bd(X, Y), tl(X, Y)), hd(X, Y)), 1.0)
    t.paint(idx, a, body, height=a * lift, hmode='max')
    t.paint(idx, cover(sd_ellipse(x - f * 6 * s, y + 12 * s, 26 * s, 15 * s, rot=f * 0.15)(X, Y), 1.0) * a, shade)
    t.paint(idx, cover(bl(X, Y), 1.0), bill, height=lift * 0.8, hmode='max')
    t.paint(idx, cover(sd_circle(x + f * 33 * s, y - 32 * s, max(4.0 * s, 2.2))(X, Y), 0.8), eye)


@design('ducky')
def ducky(t: Tex):
    """Ducky (VIP; redrawn 27 Nov 2026 for the 0.6 m tile, the owner's yes): deep bath water, a dark muted teal with
       soft wave lines running along the gun, and small yellow rubber ducks (about 3.5 cm long) bobbing on every other
       wave in a half-drop, rows facing alternately; the yellow is the one accent, the bills a touch of orange. Picked
       from four takes; two blind critics both ranked it first. (The 16 Nov Ducky, a yellow gun with big tone-on-tone
       ducks, showed as a plain yellow gun with cut-off ghost ducks on the new UVs.) No text, no logos"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('35505a')
    t.fill(smoothstep(-0.5, 0.6, FBM([2, 4], 714, 0.5)(t.U, t.V)) * 0.25, '3f5c66')
    rows = 8
    k = TAU * 5 / n                      # (5 swells a tile, so the ducks, 8 a row, ride them at different heights)
    for j in range(rows * 2):            # wave lines, every other one under a row of ducks (stronger than the take,
        y0 = (j + 0.5) * n / (rows * 2) + 22     # a critic: "the waves fade to nothing at range")
        f = y0 + 7 * np.sin(k * t.X + j * 1.3)
        d = np.abs(((t.Y - f) + n / 2) % n - n / 2) / np.sqrt(1 + (7 * k * np.cos(k * t.X + j * 1.3)) ** 2)
        t.fill(np.clip(0.5 + (2.1 - d), 0, 1) * (0.7 if j % 2 == 0 else 0.4), '62838c')
    for j in range(rows):
        for i in range(8):
            x = (i + 0.5 + 0.5 * (j % 2)) * n / 8
            y = (j + 0.5) * n / rows + 7 * math.sin(k * x + j * 2.6)   # riding its wave: a gentle bob (less rigid rows)
            duck_small(t, x, y, 0.42, -1 if j % 2 == 0 else 1, 'e1c24a', 'c9a73a', 'd07a2e', '22262c')
    t.rough[:] = 0.38
    return {'emissive': 1.0, 'tint': 'ffffff', 'accent': 'e1c24a'}



# ---------------------------------------------------------------------------------------------------------- TRIANGULUM
# Triangulum (VIP daily reward only, 17 Nov 2026; the skin concepts session's brief triangulum-vip-brief.md and its
# draft tri_wrap.py, folded in here): a star chart of the night sky, and the Triangulum mark (the real constellation,
# a long thin triangle of three stars) laid ONCE per gun like Black Hole's hole. NOT vip = true: the VIP pack would hand
# it to every VIP; the reward table's VipDailyData.EXCLUSIVE is its daily-only mark.
TRI_GOLD = 'c4a25a'
TRI_GOLD_LIGHT = 'f1d996'


def tri_curve(t, axis, c0, amp, phase, w, periods=1):
    """a soft sine line across the whole tile (it wraps): axis 'h' = y = c0 + amp sin(...x), 'v' = x = c0 + ..."""
    n = t.n
    A, B = (t.X, t.Y) if axis == 'h' else (t.Y, t.X)
    k = TAU * periods / n
    f = c0 + amp * np.sin(k * A + phase)
    d = np.abs(((B - f) + n / 2) % n - n / 2) / np.sqrt(1 + (amp * k * np.cos(k * A + phase)) ** 2)
    return np.clip(0.5 + (w / 2 - d), 0, 1), A


def tri_line(t, a, b, w, gap_a, gap_b, amp=0.6):
    """a thin gold line from star a to star b, stopping short of both (star-chart style)"""
    ax, ay = a; bx, by = b
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    p, q = (ax + ux * gap_a, ay + uy * gap_a), (bx - ux * gap_b, by - uy * gap_b)
    X, Y, idx = t.box(min(p[0], q[0]) - 6, min(p[1], q[1]) - 6, max(p[0], q[0]) + 6, max(p[1], q[1]) + 6)
    a_ = cover(sd_segment(p[0], p[1], q[0], q[1], w / 2)(X, Y))
    t.paint(idx, a_ * amp, TRI_GOLD, metal=0.9 * a_, rough=0.3)


def tri_star(t, S, x, y, r, rot=0.0):
    """a constellation star: a four-point star of light with a soft glow round it"""
    X, Y, idx = t.box(x - r - 3, y - r - 3, x + r + 3, y + r + 3)
    a = cover(sd_sparkle(x, y, r, w=0.2, rot=rot)(X, Y))
    t.paint(idx, a, 'fff4d6', emit=a)
    S.dot(x, y, r * 0.18, 0.0, 'ffe7b0', glow=0.35, glow_r=r * 0.55)


TRI_FIGURES = {
    # (stars as (x, y, size 0..1), edges): invented figures, nothing letter-like: a dipper, a kite with a tail, a chain
    'dipper': ([(0, 0, .7), (78, -12, 1), (88, 52, .6), (8, 62, .5), (150, -40, .8), (212, -36, .55), (262, -70, .9)],
               [(0, 1), (1, 2), (2, 3), (3, 0), (1, 4), (4, 5), (5, 6)]),
    'kite': ([(0, 0, .6), (64, -54, 1), (128, -4, .7), (66, 40, .55), (196, 30, .5), (262, 4, .75)],
             [(0, 1), (1, 2), (2, 3), (3, 0), (2, 4), (4, 5)]),
    'chain': ([(0, 0, .8), (70, 22, .5), (150, 18, 1), (214, 52, .6), (296, 50, .7)],
              [(0, 1), (1, 2), (2, 3), (3, 4)]),
}
TRI_GRATICULE = 0.14   # the chart lines' strength (the brief: fade, or drop the upright ones, if they read as cells)
TRI_UPRIGHT = False    # the upright chart lines: off (17 Nov: at first-person scale the two ways together read as a grid of cells)


@design('triangulum')
def triangulum(t: Tex):
    """Triangulum: a star chart of the night sky. Deep midnight with a slow faint cloudiness; a faint gold graticule
       (curved chart lines, four each way) and one dashed gold arc; about 800 round dot stars (background stars are
       never pointed); three invented constellation figures a tile, four-point stars joined by thin gold lines that stop
       short of each star, a thin gold ring round each figure's brightest star, as old charts draw them. No figure reads
       as a letter or digit"""
    n, U, V = t.n, t.U, t.V
    cl = smoothstep(0.25, 0.85, FBM([1, 2, 4], 901, 0.5)(U, V))
    t.rgb[:] = mix('0d1330', '1a2650', cl * 0.85)
    t.rough[:] = 0.42
    for k in range(4):
        a, _ = tri_curve(t, 'h', 128 + 256 * k, 26, 0.9 * k, 1.5)
        t.fill(a * TRI_GRATICULE, TRI_GOLD, metal=a * 0.6)
        if TRI_UPRIGHT:
            a, _ = tri_curve(t, 'v', 128 + 256 * k, 20, 1.7 + 0.8 * k, 1.5)
            t.fill(a * TRI_GRATICULE, TRI_GOLD, metal=a * 0.6)
    a, A = tri_curve(t, 'h', 470, 95, 0.7, 2.2)
    dash = ((A / 22.0) % 1.0 < 0.55).astype(np.float32)
    t.fill(a * dash * 0.32, TRI_GOLD, metal=a * dash * 0.7)
    r = t.rng
    S = StarLight(t)
    for _ in range(760):
        x, y = r.uniform(0, n), r.uniform(0, n); k = r.uniform() ** 3
        S.dot(x, y, 0.8 + 1.1 * k, 0.16 + 0.5 * k, r.choice(['ffffff', 'fff1d8', 'ffe2b0', 'dbe6ff'], p=[.4, .3, .18, .12]))
    for _ in range(46):
        x, y = r.uniform(0, n), r.uniform(0, n)
        S.dot(x, y, r.uniform(1.6, 2.4), 0.75, r.choice(['ffffff', 'fff1d8', 'ffe2b0']), glow=0.08, glow_r=7)
    for name, (cx, cy, rot, s) in (('dipper', (120, 260, 0.18, 1.0)), ('kite', (640, 150, -0.2, 1.0)),
                                   ('chain', (470, 720, 0.12, 1.05))):
        stars, edges = TRI_FIGURES[name]
        c, sn = math.cos(rot), math.sin(rot)
        P = [(cx + (x * c - y * sn) * s, cy + (x * sn + y * c) * s, m) for x, y, m in stars]
        rs = [9 + 11 * m for _, _, m in P]
        for i, j in edges:
            tri_line(t, P[i][:2], P[j][:2], 2.0, rs[i] + 7, rs[j] + 7)
        for (x, y, m), rr in zip(P, rs):
            tri_star(t, S, x, y, rr, rot=0.0)
            if m >= 0.95:
                X, Y, idx = t.box(x - rr - 12, y - rr - 12, x + rr + 12, y + rr + 12)
                ring = cover(np.abs(np.hypot(X - x, Y - y) - (rr + 6)) - 0.9)
                t.paint(idx, ring * 0.55, TRI_GOLD, metal=ring * 0.9)
    S.done(emit=0.7, rough=0.3)
    more, stars = tri_mark_images(os.path.join(OUT['dir'], 'triangulum'), t)
    # (the tile's stars at 0.7 to 1.0 x 2: they bloom a little; the mark's stars, in the glow decal, bloom the most)
    return {'emissive': 4.0, 'tint': 'ffffff', 'accent': 'ffe7a6', 'more_maps': more, 'decal_style': 'mark', 'decal_aspect': 2,   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 2)
            'decal_stars': stars}


# the mark in its own 2:1 picture (1024 x 512): apex alpha forward (the picture's left: on the gun's left face the
# canvas's +x runs to the back, so the apex points at the muzzle), the base stars beta (top) and gamma at the back. A
# long thin triangle, as the real constellation. Wide, so on a receiver only a third of a stud tall the mark still runs
# about 15 cm along the gun
TRI_MARK = {'a': (150, 292, 67), 'b': (876, 151, 74), 'g': (842, 398, 52)}


def tri_mark_images(stem, t: Tex, w=1024, h=512):
    """<stem>_decal.png (LIT): a soft deep-midnight calm round the mark so the busy chart quiets under it, and the three
       gold lines (a lighter bead down each, stopping short of the stars); <stem>_glow.png (UNLIT, blooms): the three
       four-point stars and their glow; <stem>_chip.png: both over the tile, for the loadout chip. Returns the maps and
       the stars as "x,y,r;..." in the picture's pixels (WeaponModels gives each star its own label, so WrapAnim can
       breathe them one after another)"""
    from PIL import Image
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    pts = [TRI_MARK[k][:2] for k in 'abg']
    tri = sd_polygon(pts)(xx, yy)
    A = np.clip(0.62 * smoothstep(105, 15, tri), 0, 1)
    rgb = np.zeros((h, w, 3), np.float32) + hexrgb('0b1029')
    la = np.zeros((h, w), np.float32)
    for (i, j) in ((0, 1), (1, 2), (2, 0)):
        (ax, ay, ra), (bx, by, rb) = TRI_MARK['abg'[i]], TRI_MARK['abg'[j]]
        L = math.hypot(bx - ax, by - ay); ux, uy = (bx - ax) / L, (by - ay) / L
        p = (ax + ux * (ra * 0.55 + 18), ay + uy * (ra * 0.55 + 18)); q = (bx - ux * (rb * 0.55 + 18), by - uy * (rb * 0.55 + 18))
        d = sd_segment(p[0], p[1], q[0], q[1], 6.0)(xx, yy)
        cov = cover(d, 1.2)
        bead = np.clip(1 - np.abs(d + 6.0) / 6.0, 0, 1) ** 1.5
        col = mix(TRI_GOLD, TRI_GOLD_LIGHT, bead * 0.8)
        rgb = rgb * (1 - cov[..., None]) + col * cov[..., None]
        la = np.maximum(la, cov)
    A = np.maximum(A, la)
    Image.fromarray(np.concatenate([(np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8), (A[..., None] * 255 + 0.5).astype(np.uint8)], -1), 'RGBA').save(stem + '_decal.png', optimize=True)
    G = np.zeros((h, w), np.float32); H = np.zeros((h, w), np.float32)
    for k in 'abg':
        x, y, r = TRI_MARK[k]
        G = np.maximum(G, cover(sd_sparkle(x, y, r, w=0.17)(xx, yy), 1.5))
        H = np.maximum(H, np.exp(-0.5 * (np.hypot(xx - x, yy - y) / (r * 0.42)) ** 2) * 0.75)
    ga = np.clip(G + H * (1 - G), 0, 1)
    grgb = (G[..., None] * hexrgb('fff8e6') + (H * (1 - G))[..., None] * hexrgb('ffd889')) / np.maximum(ga, 1e-4)[..., None]
    Image.fromarray(np.concatenate([(np.clip(grgb, 0, 1) * 255 + 0.5).astype(np.uint8), (ga[..., None] * 255 + 0.5).astype(np.uint8)], -1), 'RGBA').save(stem + '_glow.png', optimize=True)
    # the chip: a square from the middle of the tile with the mark scaled to fit across it
    tile = Image.fromarray((np.clip(t.rgb, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB').resize((512, 512), Image.LANCZOS)
    def scaled(img_rgb, alpha):
        im = Image.fromarray(np.concatenate([(np.clip(img_rgb, 0, 1) * 255 + 0.5).astype(np.uint8), (alpha[..., None] * 255 + 0.5).astype(np.uint8)], -1), 'RGBA')
        return im.resize((512, 256), Image.LANCZOS)
    chip = tile.convert('RGBA')
    chip.alpha_composite(scaled(rgb, A), (0, 128))
    chip.alpha_composite(scaled(grgb, ga), (0, 128))
    chip.convert('RGB').save(stem + '_chip.png', optimize=True)
    stars = ';'.join('%d,%d,%d' % TRI_MARK[k] for k in 'abg')
    return {'decal': os.path.basename(stem) + '_decal.png', 'hole': os.path.basename(stem) + '_glow.png',
            'swatch': os.path.basename(stem) + '_chip.png'}, stars


@design('stonks')
def stonks(t: Tex):
    """market crash: a trading terminal on its worst day, a red line diving through candlesticks, lit ticker bars
       (no words or numbers)"""
    n = t.n; r = t.rng
    t.rgb[:] = hexrgb('05080a')
    t.fill(cover(np.minimum(t.X % 128, 128 - t.X % 128) - 1) * 0.8, '102016')
    t.fill(cover(np.minimum(t.Y % 128, 128 - t.Y % 128) - 1) * 0.8, '102016')
    # (27 Nov, 0.6 m tiles: the chart landed as stray dashes; ONE bold line now runs through the rows near the tile's
    # edge, where the gun's body sits, diving and recovering along the gun)
    pts = []; y = 70.0
    for x in np.arange(0, n + 1, 32.0):
        pts.append((x, y)); y = min(190, max(-90, y + r.uniform(-40, 46)))
    pts[-1] = (pts[-1][0], 70.0)
    pts = [(x, y if y >= 0 else y) for x, y in pts]
    for i in range(5, len(pts) - 2, 7):
        x, yy = pts[i]; up = r.uniform() < 0.35
        c = '3aff5a' if up else 'ff3a3a'
        t.shape((x - 14, yy - 70, x + 14, yy + 70), sd_round_rect(x, yy, 8, 34, 2), color=c, emit=0.8)
        t.shape((x - 4, yy - 70, x + 4, yy + 70), sd_segment(x, yy - 56, x, yy + 56, 1.5), color=c, emit=0.8)
    half = len(pts) // 2   # (two halves, each its own box: one box can't be wider than the tile)
    for seg in (pts[:half + 1], pts[half:]):
        X, Y, idx = t.box(*bbox_of(seg, 12))
        t.paint(idx, cover(sd_polyline(seg, 13)(X, Y)), 'ff3a3a', emit=1.0)
        segw = [(x, y + n) for x, y in seg]
        X, Y, idx = t.box(*bbox_of(segw, 16))
        t.paint(idx, cover(sd_polyline(segw, 13)(X, Y)), 'ff3a3a', emit=1.0)
    t.rough[:] = 0.2
    return {'emissive': 5.0, 'tint': 'ffffff'}   # RADIANT (the owner: "a brighter glow"; was 3.0)   # thin neon lines bloom (GLOW, see lava)   # GLOW 18 Nov (the owner: "a brighter glow ... I can't see it"; was 4)


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


# ====================================================================== the mastery camos
# WEAPON MASTERY (18 Nov 2026, the owner: "level up weapons to unlock gold, damascus, diamond and galaxy camo for their
# respective guns"): four wraps earned per gun by levelling it (the weapon-mastery session's unlocks), never sold and
# never in a container. A prestige ladder, each a clear step up: polished gold, then pattern-welded steel, then a
# faceted crystal that sparkles and glows, then Dark Matter, a deep space camo that moves (client/WrapAnim). Our own
# art, drawn here like every wrap; the upload rules hold (no code-like stripes, no text, no logos).

@design('mastery_gold')
def mastery_gold(t: Tex):
    """mastery gold: polished warm gold, rich and pale in broad soft swathes like light rolling over a curved surface,
       a fine engine-turned brushing along the gun, and a few small glints that swell and fade (WrapAnim: glint)"""
    n, U, V = t.n, t.U, t.V
    r = t.rng
    sw = FBM([(1, 2), (2, 3)], 901, 0.5)(U, V)             # broad soft swathes (the polish catching the light)
    t.rgb[:] = mix('a8752a', 'e6bc5a', smoothstep(-0.5, 0.5, sw))
    t.fill(smoothstep(0.3, 0.7, sw) * 0.7, 'f6dc94')    # pale highlights where the swathe is brightest
    t.metal[:] = 1.0
    t.rough[:] = 0.2 - 0.06 * smoothstep(0.2, 0.7, sw)
    # a fine brushing along the gun (u): long soft grooves a few pixels apart, faint in the normal map only
    br = FBM([(64, 2), (128, 4)], 902, 0.6)(U, V)
    t.height[:] = 0.18 * br
    # the glints: a few small four-point sparkles (they bloom at the swell) and a soft sheen round each
    for x, y in scatter(r, n, 7, 260):
        ro = r.uniform(9, 14)
        X, Y, idx = t.box(x - ro * 3, y - ro * 3, x + ro * 3, y + ro * 3)
        halo = np.exp(-np.hypot(X - x, Y - y) / (ro * 0.6)) * 0.35
        t.paint(idx, halo, 'fff1c8', emit=halo)
        t.paint(idx, cover(sd_sparkle(x, y, ro, 0.12, 0)(X, Y)), '#fff8e6', emit=1.0)
    return {'emissive': 3.0, 'tint': 'ffe2a0', 'accent': 'f3c862'}


@design('mastery_damascus')
def mastery_damascus(t: Tex):
    """mastery damascus: pattern-welded steel, wide flowing layers folded into ripples and drops (the ladder and
       raindrop forge patterns), bright and dark steel greys with a faint warm temper in the dark layers; the dark
       layers etched a little deeper and duller"""
    U, V = t.U, t.V
    wu = U + 0.06 * FBM([2, 4], 911)(U, V)
    wv = V + 0.06 * FBM([2, 4], 912)(U, V)
    f = FBM([(2, 2), (4, 4)], 913, 0.55)(wu, wv)
    # raindrops: a few soft rings the layers bend round
    drops = np.zeros_like(U)
    r = t.rng
    for x, y in scatter(r, t.n, 6, 300):
        dx = np.abs(t.X - x); dx = np.minimum(dx, t.n - dx)
        dy = np.abs(t.Y - y); dy = np.minimum(dy, t.n - dy)
        drops += np.exp(-np.hypot(dx, dy) / 70.0)
    ph = 13.0 * f + 5.0 * wv + 3.2 * drops                   # (6.5 was zebra-bold: real pattern welds are many fine layers)
    s = np.sin(ph * TAU)
    bright = smoothstep(-0.45, 0.45, s)
    edge = 1 - np.abs(s)                                      # (a thin lighter seam where two layers meet)
    lum = 0.43 + 0.12 * bright + 0.04 * smoothstep(0.8, 1.0, edge)
    steel = lum[..., None] * np.array([1.0, 1.01, 1.04], np.float32)
    temper = lum[..., None] * hexrgb('c9a77a') * 1.05          # the faint warm temper in the dark layers
    t.rgb[:] = np.clip(steel + (temper - steel) * ((1 - bright) * 0.28)[..., None], 0, 1)
    t.metal[:] = 1.0
    t.rough[:] = 0.42 - 0.18 * bright
    t.height[:] = bright * 0.9
    return {'accent': 'd9c3a0'}


@design('mastery_diamond')
def mastery_diamond(t: Tex):
    """mastery diamond: faceted crystal, pale ice-white facets each turned a little differently (the normal map),
       a faint prismatic tint that differs facet to facet, bright fine edges where facets meet, and small sparkles at
       a few corners that bloom; the tint sweeps through the spectrum in hand (WrapAnim: iris)"""
    n = t.n
    r = t.rng
    pts = scatter(r, n, 34, 110)
    d1, d2, ids = voronoi(n, pts)
    k = len(pts)
    hue = np.array([r.uniform(0, 1) for _ in range(k)], np.float32)
    tilt = np.array([[r.uniform(-0.32, 0.32), r.uniform(-0.32, 0.32)] for _ in range(k)], np.float32)
    px = np.array([p[0] for p in pts], np.float32); py = np.array([p[1] for p in pts], np.float32)
    # each facet a flat plane at its own tilt (relief in pixels: the normal map turns it into the facet's light)
    dx = t.X - px[ids]; dx = (dx + n / 2) % n - n / 2
    dy = t.Y - py[ids]; dy = (dy + n / 2) % n - n / 2
    t.height[:] = dx * tilt[ids, 0] + dy * tilt[ids, 1]
    # pale ice with a faint prismatic tint per facet (hue -> rgb at low saturation), lighter toward each facet's middle
    h6 = hue[ids] * 6.0
    prism = np.stack([np.clip(np.abs(h6 - 3) - 1, 0, 1), np.clip(2 - np.abs(h6 - 2), 0, 1), np.clip(2 - np.abs(h6 - 4), 0, 1)], -1)
    # each facet lit as a cut face: brighter the more its tilt faces a light from the upper left, a few dark ones
    lit = 0.8 + 1.1 * (-tilt[:, 0] * 0.7 - tilt[:, 1] * 0.7)
    shade = np.clip(lit + np.array([r.uniform(-0.06, 0.06) for _ in range(k)], np.float32), 0.5, 1.0)
    base = hexrgb('eef3fa')
    t.rgb[:] = (base + (prism - 0.5) * 0.07) * shade[ids][..., None] + (smoothstep(60, 0, d1) * 0.04)[..., None]
    edge = smoothstep(2.5, 0.6, (d2 - d1) * 0.5)
    t.fill(edge, 'ffffff', emit=0.32)                          # the fine bright edges (glow, under every Bloom)
    t.metal[:] = 0.6                                           # (over 0.5: no satin floor, so it stays glassy)
    t.rough[:] = 0.1
    for x, y in scatter(r, n, 6, 300):                          # sparkles at a few corners: they bloom
        ro = r.uniform(10, 15)
        X, Y, idx = t.box(x - ro * 3, y - ro * 3, x + ro * 3, y + ro * 3)
        halo = np.exp(-np.hypot(X - x, Y - y) / (ro * 0.5)) * 0.3
        t.paint(idx, halo, 'f4f8ff', emit=halo)
        t.paint(idx, cover(sd_sparkle(x, y, ro, 0.12, math.radians(r.uniform(-15, 15)))(X, Y)), '#ffffff', emit=1.0)
    t.normal_k = 0.9
    return {'emissive': 4.0, 'tint': 'f2f6ff', 'accent': 'cfe4ff'}


@design('mastery_galaxy')
def mastery_galaxy(t: Tex):
    """mastery galaxy, DARK MATTER: the top tier, a space camo. Big organic camo shapes cut a deep blue-black field;
       inside the shapes, space: violet and teal gas glowing round fine round stars and a few bright twinkles; a thin
       glowing rim where each shape meets the dark. In hand it moves (client/WrapAnim: the gas drifts violet to teal,
       stars twinkle)"""
    n, U, V = t.n, t.U, t.V
    r = t.rng
    wu = U + 0.045 * FBM([3, 6], 921)(U, V)
    wv = V + 0.045 * FBM([3, 6], 922)(U, V)
    f = FBM([(2, 3), (4, 6), (8, 12)], 923, 0.45)(wu, wv)
    shape = field_cover(f, 0.0)                                # the camo shapes (about half the tile)
    t.rgb[:] = hexrgb('07080f')
    g1 = smoothstep(-0.1, 0.6, FBM([2, 4, 8], 924, 0.55)(wu, wv))
    g2 = smoothstep(-0.05, 0.6, FBM([3, 6, 12], 925, 0.55)(wu + 0.31, wv))
    space = hexrgb('0d0a22') + g1[..., None] * (hexrgb('6a3cc8') - hexrgb('0d0a22')) * 0.8
    space = space + (g2 * (1 - g1 * 0.5))[..., None] * (hexrgb('1fa8b8') - space) * 0.55
    t.rgb[:] = t.rgb * (1 - shape[..., None]) + space * shape[..., None]
    gas = np.clip(g1 * 0.55 + g2 * 0.45, 0, 1)
    t.emit[:] = gas * shape * 0.55                              # the gas glows inside the shapes
    # the rim: a thin glowing line along each shape's edge
    eb = blur_wrap(shape, 3)                                   # (the shape's edge widened to a few pixels)
    rim = smoothstep(0.12, 0.45, eb) * smoothstep(0.88, 0.55, eb)
    t.fill(rim * 0.8, 'b7a4ff', emit=0.9)
    t.rough[:] = 0.3
    S = StarLight(t)
    for _ in range(900):
        x, y = r.uniform(0, n), r.uniform(0, n)
        k = r.uniform() ** 3
        S.dot(x, y, 1.5 + 1.3 * k, (0.3 + 0.6 * k) * float(shape[int(y) % n, int(x) % n] * 0.85 + 0.15), star_colour(r))
    S.done()
    for x, y in scatter(r, n, 6, 260):                          # a few bright twinkles inside the shapes
        if shape[int(y) % n, int(x) % n] < 0.5: continue
        ro = r.uniform(16, 24)
        X, Y, idx = t.box(x - ro * 1.5, y - ro * 1.5, x + ro * 1.5, y + ro * 1.5)
        halo = np.exp(-np.hypot(X - x, Y - y) / (ro * 0.3)) * 0.5
        t.paint(idx, halo, 'e4dcff', emit=halo)
        t.paint(idx, cover(sd_sparkle(x, y, ro, 0.14, 0)(X, Y)), '#ffffff', emit=1.0)
    return {'emissive': 5.5, 'tint': 'ffffff', 'accent': 'a78bff'}


# ====================================================================== the run
# IN-HAND COLOUR. In the training hall a held gun's colours come out with more contrast and less blue than the map:
# measured over three Play rounds on Tiger, Hazard, Sakura, Carbon (16 Nov 2026), red and green land near
# 1.2 x map - 33 and blue near 1.05 x map - 35 (0..255). A low blue channel goes to nothing, so warm colours turn hot
# and darks crush. Every wrap's colour map is drawn as intended and then moved most of the way towards the inverse,
# so it lands near the intended colour in hand. The wraps tuned by hand in the hall (HALL_TUNED) skip it.
HALL_A = np.array([1.2, 1.2, 1.05], np.float32)
HALL_B = np.array([-33, -33, -35], np.float32) / 255.0
HALL_K = 0.7          # how far towards the full inverse (not all the way: other zones light the guns more neutrally)
HALL_TUNED = {'galaxy', 'nebula', 'camo', 'hex', 'tiger', 'sakura', 'carbon', 'hazard', 'damascus', 'mastery_damascus', 'mastery_galaxy'}
# SATIN: a non-metal wrap is never glossier than this: up-facing faces of glossy wraps mirrored the hall's ceiling
# lights as pale blank slabs (round 4: Kintsugi, Galaxy, Nebula)
ROUGH_MIN = 0.36


def hall_comp(rgb):
    inv = (rgb - HALL_B) / HALL_A
    return np.clip(rgb + HALL_K * (inv - rgb), 0.0, 1.0)


# RELIEF (the owner, 16 Nov evening: "maybe even height maps on some"). A SurfaceAppearance takes no real height map,
# only a normal map, which fakes the relief with the light. Most designs raised their shapes by a step one pixel wide:
# that lights a one-pixel rim, lost to the mipmaps a metre from the eye. These wraps' heights are widened into bevels
# (blur, pixels) and deepened (gain); lum raises the light parts of a design that drew no height (its lines and
# blossoms read as carved). Heights are in pixels of relief (1 cm = 41 px)
RELIEF = {
    'lava': {'blur': 1, 'gain': 3.0},        # crust plates domed up from deep cracks
    'hex': {'blur': 2, 'gain': 2.5},         # raised hex panels, bevelled, the glowing grooves sunk between
    'circuit': {'lum': 5.0, 'blur': 1.5, 'gain': 2.0},   # the gold traces (light) and the chips stand proud of the board
    'kintsugi': {'blur': 2, 'gain': 4.0},    # the gold seams a raised bead
    'bubblewrap': {'blur': 1, 'gain': 1.6},  # rounder, higher domes
    'carbon': {'blur': 1, 'gain': 1.5},      # the weave's tows
    'wood': {'blur': 1, 'gain': 2.0},        # the grain
    'seigaiha': {'lum': 4.0, 'blur': 2},     # the wave lines carved (light lines raised)
    'sakura': {'lum': 3.0, 'blur': 2},       # the blossoms raised
}
OUT = {'dir': '.'}   # where build() is writing (a design that draws extra images, such as Black Hole's decal, saves there)


def build(wid, out_dir):
    t = Tex(seed=seed_of(wid))
    OUT['dir'] = out_dir
    extra = DESIGNS[wid](t) or {}
    more = extra.pop('more_maps', {})   # (extra images: decal, hole, swatch; WrapBook sets them as attributes)
    rl = RELIEF.get(wid)
    if rl:
        h = t.height + (np.dot(t.rgb, np.array([0.3, 0.59, 0.11], np.float32)) * rl['lum'] if rl.get('lum') else 0)
        t.height[:] = blur_wrap(h, rl.get('blur', 0)) * rl.get('gain', 1.0)
    if wid not in HALL_TUNED: t.rgb[:] = hall_comp(t.rgb)
    t.rough[:] = np.where(t.metal < 0.5, np.maximum(t.rough, ROUGH_MIN), t.rough)
    maps = t.save(os.path.join(out_dir, wid))
    rel = {k: (os.path.basename(v) if isinstance(v, str) else v) for k, v in maps.items()}
    rel.update(more)
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
