# The PS1 / grimy-corporate texture kit for map architecture (and anyone else who wants it: the props lane shares it).
# Plain python3 + numpy + Pillow, no Blender. Every texture is tiny (32-128 px), seamless, cut down to a 16-colour
# clut like a PS1 4-bit texture, snapped to 15-bit colour, with a 4x4 ordered dither between the clut colours.
# Painted surfaces (siding, shingles, stucco, trim, metal) are drawn in light greys so the game can tint them per house
# (colour x texture, like PS1 games did); brick, wood, concrete, glass and the decals keep their own colours.
# writes public/models/arch/kit/<name>.png + kit.json (metres per tile for each), and a contact sheet
# run: python3 tools/blender/arch/texkit.py [--sheet out.png]
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(ROOT, 'public', 'models', 'arch', 'kit')
R = np.random.default_rng(1997)

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0 - 0.5


# ------------------------------------------------------------ noise (all of it wraps, so every tile is seamless)
def vnoise(n, cells, seed=None, wrap=True):
    """value noise n x n with `cells` lattice cells per side, smooth (cosine), tileable"""
    rg = np.random.default_rng(seed) if seed is not None else R
    g = rg.random((cells, cells)).astype(np.float32)
    t = np.arange(n, dtype=np.float32) * cells / n
    i0 = np.floor(t).astype(int); f = t - i0; f = (1 - np.cos(f * np.pi)) / 2
    i1 = (i0 + 1) % cells; i0 %= cells
    a = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i1] * f[None, :]
    b = g[i1][:, i0] * (1 - f)[None, :] + g[i1][:, i1] * f[None, :]
    return a * (1 - f)[:, None] + b * f[:, None]


def fbm(n, base=4, oct=4, seed=None, gain=0.5):
    s, amp, tot = np.zeros((n, n), np.float32), 1.0, 0.0
    rg = np.random.default_rng(seed) if seed is not None else R
    for o in range(oct):
        c = min(n, base * 2 ** o)
        s += vnoise(n, c, int(rg.integers(1 << 30))) * amp; tot += amp; amp *= gain
    return s / tot


def speck(n, p, seed=None):  # sparse single-texel specks
    rg = np.random.default_rng(seed) if seed is not None else R
    return (rg.random((n, n)) < p).astype(np.float32)


def blobs(n, k, rmin, rmax, seed=None):
    """k soft round blobs (stains, mould), wrapped"""
    rg = np.random.default_rng(seed) if seed is not None else R
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    m = np.zeros((n, n), np.float32)
    for _ in range(k):
        cx, cy, r = rg.random() * n, rg.random() * n, rmin + rg.random() * (rmax - rmin)
        dx = np.minimum(abs(xx - cx), n - abs(xx - cx)); dy = np.minimum(abs(yy - cy), n - abs(yy - cy))
        m = np.maximum(m, np.clip(1 - np.hypot(dx, dy * 1.3) / r, 0, 1))
    return m


def streaks(n, k, seed=None, length=(0.3, 0.9), width=(1, 2)):
    """vertical drip streaks running down from random points (rust, water), wrapped. 1 at the top, fading down"""
    rg = np.random.default_rng(seed) if seed is not None else R
    m = np.zeros((n, n), np.float32)
    for _ in range(k):
        x, y0 = int(rg.integers(n)), int(rg.integers(n))
        L = int(n * (length[0] + rg.random() * (length[1] - length[0]))); w = int(rg.integers(width[0], width[1] + 1))
        for j in range(L):
            a = (1 - j / L) ** 1.5
            for dx in range(w):
                xx = (x + dx + (1 if rg.random() < 0.08 else 0)) % n
                m[(y0 + j) % n, xx] = max(m[(y0 + j) % n, xx], a)
    return m


def cracks(n, k, seed=None):
    rg = np.random.default_rng(seed) if seed is not None else R
    m = np.zeros((n, n), np.float32)
    for _ in range(k):
        x, y, a = rg.random() * n, rg.random() * n, rg.random() * math.tau
        for _ in range(int(n * (0.2 + rg.random() * 0.4))):
            m[int(y) % n, int(x) % n] = 1
            a += (rg.random() - 0.5) * 1.2; x += math.cos(a); y += math.sin(a)
            if rg.random() < 0.04: a += (rg.random() - 0.5) * 2.5
    return m


# ------------------------------------------------------------ colour
def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def ramp(v, stops):
    """v in [0,1] -> rgb along colour stops [(t, '#hex'), ...]"""
    ts = np.array([s[0] for s in stops], np.float32); cs = np.stack([hexc(s[1]) for s in stops])
    v = np.clip(v, 0, 1)
    out = np.empty(v.shape + (3,), np.float32)
    for c in range(3): out[..., c] = np.interp(v, ts, cs[:, c])
    return out


def mix(a, b, t): t = np.asarray(t, np.float32)[..., None] if np.ndim(t) else t; return a * (1 - t) + b * t


def shade(img, k): return np.clip(img * np.asarray(k, np.float32)[..., None], 0, 1)


def ps1(img, colors=16, dither=1.0):
    """the PS1 treatment: a `colors`-entry clut (k-means), ordered dither between neighbours, 15-bit colour"""
    h, w, _ = img.shape
    px = img.reshape(-1, 3)
    # k-means++ -ish clut
    rg = np.random.default_rng(7)
    cent = px[rg.choice(len(px), 1)]
    for _ in range(colors - 1):
        d = ((px[:, None, :] - cent[None]) ** 2).sum(-1).min(1)
        cent = np.vstack([cent, px[rg.choice(len(px), p=d / d.sum()) if d.sum() > 0 else rg.integers(len(px))]])
    for _ in range(12):
        lab = ((px[:, None, :] - cent[None]) ** 2).sum(-1).argmin(1)
        for k in range(len(cent)):
            sel = px[lab == k]
            if len(sel): cent[k] = sel.mean(0)
    cent = np.round(cent * 31) / 31  # 15-bit clut entries
    # ordered dither: nudge each pixel by the bayer threshold scaled to the clut's spacing, then pick the nearest entry
    sp = np.median(np.sqrt(((cent[:, None] - cent[None]) ** 2).sum(-1) + np.eye(len(cent)) * 9).min(1))
    by = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w].reshape(-1, 1)
    q = px + by * sp * dither
    lab = ((q[:, None, :] - cent[None]) ** 2).sum(-1).argmin(1)
    return cent[lab].reshape(h, w, 3)


def save(name, img, tile, alpha=None, colors=16, dither=1.0, note=''):
    out = ps1(img, colors, dither)
    a8 = None
    if alpha is not None: a8 = (np.clip(alpha, 0, 1) > 0.5).astype(np.uint8) * 255  # 1-bit alpha, like the PS1's
    arr = (out * 255 + 0.5).astype(np.uint8)
    im = Image.fromarray(np.dstack([arr, a8]) if a8 is not None else arr, 'RGBA' if a8 is not None else 'RGB')
    im.save(os.path.join(OUT, name + '.png'), optimize=True)
    KIT[name] = {'tile': tile, 'px': img.shape[1], 'alpha': a8 is not None, 'note': note}
    return out


KIT = {}
FAC_GLOW = {}  # lit windows: an emissive mask per facade


# ------------------------------------------------------------ surfaces
def siding(n=64):
    """lap siding, light grey (tinted per house): 8 boards a tile (2 m: 25 cm boards), a shadow under each lap, a lit
    lip on top, butt joints, faint grain, paint gone chalky in patches, grime"""
    y = np.arange(n) % 8
    lap = np.where(y == 7, 0.55, np.where(y == 0, 1.08, 1.0 - y * 0.012)).astype(np.float32)[:, None] * np.ones((1, n), np.float32)
    grain = vnoise(n, 32) * 0.06 - 0.03
    g = lap + grain
    for b in range(8):  # butt joints, a couple a board
        for _ in range(R.integers(0, 2) + (b % 2)):
            x = int(R.integers(n)); g[b * 8:b * 8 + 7, x] *= 0.7
    chalk = (fbm(n, 4, 3) > 0.62).astype(np.float32) * 0.07
    grime = fbm(n, 2, 4)
    g = g + chalk - (grime - 0.5) * 0.18
    base = ramp(np.clip(g * 0.85, 0, 1), [(0, '#3a3530'), (0.6, '#b7b2a8'), (0.85, '#e6e2d8'), (1, '#fbf8ee')])
    mould = blobs(n, 3, 3, 9) * (y < 3)[:, None]
    base = mix(base, base * hexc('#8fa05a') * 1.1, np.clip(mould * 0.5, 0, 1))  # greenish mildew under the laps
    return base


def brick(n=64):
    """running-bond brick, 16 x 6 px bricks (50 x 19 cm at 2 m a tile), dirty mortar, each brick its own colour, soot"""
    img = np.zeros((n, n, 3), np.float32)
    mortar = ramp(fbm(n, 4, 3) * 0.6 + 0.2, [(0, '#5c5249'), (1, '#a39883')])
    img[:] = mortar
    pal = ['#8e3a26', '#a14530', '#7a2f22', '#b0553a', '#6e3324', '#94402c', '#83402f']
    for row in range(n // 8):
        off = 0 if row % 2 == 0 else 8
        for col in range(-1, n // 16 + 1):
            x0, y0 = col * 16 + off, row * 8
            c = hexc(pal[int(R.integers(len(pal)))]) * (0.85 + R.random() * 0.3)
            if R.random() < 0.12: c = c * 0.55  # a sooty one
            for yy in range(y0, y0 + 7):
                for xx in range(x0, x0 + 15):
                    img[yy % n, xx % n] = c
    tex = fbm(n, 8, 3)
    img = shade(img, 0.82 + tex * 0.36)
    img = mix(img, img * hexc('#6b6f3a') * 1.4, blobs(n, 2, 6, 14) * 0.35)  # moss stain
    img = shade(img, 1 - streaks(n, 4) * 0.3)
    return img


def stucco(n=64):
    """stucco / render, light (tinted): blotchy, cracks, rain streaks"""
    g = 0.78 + (fbm(n, 4, 5) - 0.5) * 0.35 + (speck(n, 0.06) - speck(n, 0.06)) * 0.08
    g -= cracks(n, 3) * 0.3 + streaks(n, 6, width=(1, 3)) * 0.16
    return ramp(g, [(0, '#2f2c26'), (0.6, '#b9b4a6'), (0.85, '#e8e3d3'), (1, '#ffffff')])


def concrete(n=64):
    """cast concrete panels (2 m at 4 m a tile): seams, form-tie holes with rust running down, patchy"""
    g = 0.62 + (fbm(n, 4, 5) - 0.5) * 0.3
    img = ramp(g, [(0, '#3d3f3c'), (0.55, '#8d8f86'), (0.8, '#b3b3a6'), (1, '#d2d0c2')])
    seam = np.zeros((n, n), np.float32); seam[n // 2 - 1, :] = 1; seam[:, n // 2 - 1] = 1; seam[n - 1, :] = 1; seam[:, n - 1] = 1
    img = shade(img, 1 - seam * 0.35)
    rust = np.zeros((n, n), np.float32)
    for py in (8, 24, 40, 56):
        for px in (8, 24, 40, 56):
            img[py, px] = hexc('#2a2a28'); img[py, px + 1] = hexc('#3a3a36')
            if R.random() < 0.5:
                for j in range(1, int(4 + R.random() * 14)): rust[(py + j) % n, px] = max(rust[(py + j) % n, px], 1 - j / 18)
    img = mix(img, hexc('#7a4a22'), rust * 0.6)
    img = mix(img, img * 0.6, streaks(n, 5, width=(1, 3)) * 0.5)
    return img


def shingle(n=64):
    """asphalt shingles, grey (tinted): 8 px courses (25 cm) of 16 px tabs, half-offset, a hard shadow line under each
    course, the slot between tabs dark, granules, a few tabs gone (the black felt shows) or lifted"""
    rg = np.random.default_rng(3)
    y = np.arange(n)[:, None] % 8
    g = 0.74 + (rg.random((n, n)) - 0.5) * 0.12 + (fbm(n, 8, 2) - 0.5) * 0.12
    g = g * np.where(y == 7, 0.35, np.where(y == 6, 0.72, np.where(y == 0, 1.1, 1.0)))
    for row in range(n // 8):
        off = 0 if row % 2 == 0 else 8
        for x in range(off, n + off, 16):
            xx = x % n
            g[row * 8:row * 8 + 7, xx] *= 0.4
            tone = 0.9 + rg.random() * 0.2
            for k in range(1, 16): g[row * 8:row * 8 + 6, (xx + k) % n] *= tone
            if rg.random() < 0.06:
                for k in range(1, 16): g[row * 8:row * 8 + 7, (xx + k) % n] = 0.2
    g -= blobs(n, 3, 4, 10) * 0.12
    return ramp(g, [(0, '#151314'), (0.5, '#8a8682'), (0.8, '#cfcac2'), (1, '#efeae0')])


def corrugated(n=32):
    """corrugated sheet (1 m a tile), grey (tinted): sine ridges, rust coming through"""
    x = np.arange(n)[None, :]
    g = 0.7 + np.sin(x / n * math.tau * 4) * 0.18 + (fbm(n, 4, 3) - 0.5) * 0.15
    g = np.broadcast_to(g, (n, n)).copy()
    img = ramp(g, [(0, '#2a2a2c'), (0.6, '#a8aaa8'), (1, '#e6e6e0')])
    rust = np.clip((fbm(n, 2, 4) - 0.55) * 4, 0, 1) + streaks(n, 3) * 0.7
    return mix(img, hexc('#8a4a1e') * (0.7 + 0.5 * vnoise(n, 8)[..., None]), np.clip(rust, 0, 0.9))


def planks(n=64):
    """floorboards (2 m a tile): 4 boards across, grain, nail heads, dark gaps, scuffs. their own colour"""
    x = np.arange(n)[None, :] % 16
    grain = vnoise(n, 4) * 0.4 + np.sin((np.arange(n)[:, None] * 0.0 + np.arange(n)[None, :]) * 0.0) + fbm(n, 16, 2) * 0.3
    g = 0.55 + (grain - 0.4) * 0.5
    tone = np.repeat(R.random(n // 16) * 0.2 - 0.1, 16)[None, :]
    g = g + tone
    g = np.where(x == 15, 0.15, g)
    for b in range(4):  # end joints and nails
        yj = int(R.integers(n)); g[yj, b * 16:b * 16 + 15] = 0.2
        for yy in (yj + 2, (yj + 34) % n): g[yy % n, b * 16 + 3] = 0.25; g[yy % n, b * 16 + 12] = 0.25
    g -= blobs(n, 3, 4, 12) * 0.12
    return ramp(np.clip(g, 0, 1), [(0, '#21140c'), (0.4, '#6b4424'), (0.7, '#a0703c'), (1, '#c99858')])


def trim(n=32):
    """painted wood trim (1 m a tile), off-white (tinted): brush grain along it, chips, dirt"""
    g = 0.86 + (vnoise(n, 16) - 0.5) * 0.08 + (np.random.default_rng(5).random((n, n)) - 0.5) * 0.04
    g -= speck(n, 0.03) * 0.35 + (fbm(n, 2, 3) - 0.5) * 0.2
    return ramp(g, [(0, '#3a3024'), (0.7, '#cfc8b6'), (1, '#fffcf0')])


def lino(n=64):
    """sickly checkerboard lino (2 m a tile: 25 cm squares): cream and bile green, scuffs, a burn"""
    yy, xx = np.mgrid[0:n, 0:n]
    chk = ((yy // 8 + xx // 8) % 2).astype(np.float32)
    img = mix(hexc('#d9d2a8')[None, None] * np.ones((n, n, 1)), hexc('#7d9a3c')[None, None] * np.ones((n, n, 1)), chk)
    img = shade(img, 0.9 + (fbm(n, 4, 3) - 0.5) * 0.25)
    img = shade(img, 1 - cracks(n, 2) * 0.3 - blobs(n, 2, 2, 5) * 0.4)
    return img


def tar(n=64):
    """tar-and-gravel flat roof (4 m a tile): dark, pebbly, puddle stains"""
    rg = np.random.default_rng(11)
    g = 0.38 + (rg.random((n, n)) - 0.5) * 0.3 + (fbm(n, 4, 3) - 0.5) * 0.2
    g -= blobs(n, 3, 5, 14) * 0.12
    return ramp(g, [(0, '#151416'), (0.4, '#45423e'), (0.7, '#77736a'), (1, '#a8a296')])


def carpet(n=32):
    """rental carpet (1 m a tile): a dull teal-grey with fleck and a stain. its own colour"""
    rg = np.random.default_rng(13)
    g = 0.5 + (rg.random((n, n)) - 0.5) * 0.35 - blobs(n, 1, 4, 9) * 0.25
    return ramp(g, [(0, '#1b2624'), (0.5, '#4e6862'), (1, '#8eaaa0')])


def metalplate(n=32):
    """diamond plate / painted steel (1 m a tile), grey (tinted): a raised diamond pattern, scuffed"""
    yy, xx = np.mgrid[0:n, 0:n]
    d = (((xx + yy) % 8 == 0) | ((xx - yy) % 8 == 0)).astype(np.float32)
    g = 0.66 + d * 0.16 + (fbm(n, 4, 3) - 0.5) * 0.18 - speck(n, 0.03) * 0.2
    return ramp(g, [(0, '#25262a'), (0.6, '#9a9ea2'), (1, '#e4e6e6')])


def glass(n=32):
    """window glass, dark (sky reflection streak, grime round the edge). on panes that stay in, and the tower windows"""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    g = 0.25 + yy / n * 0.25 + np.clip(1 - abs((xx + yy * 0.6) % n - n * 0.45) / 3, 0, 1) * 0.35
    img = ramp(g, [(0, '#0b141e'), (0.4, '#24425a'), (0.7, '#4d7f98'), (1, '#b8e0ea')])
    return shade(img, 1 - (fbm(n, 2, 3) > 0.6) * 0.2)


def louvre(n=32):
    """shutter louvres (0.5 m a tile), light (tinted): slats every 4 px with a shadow under each, a frame line"""
    y = np.arange(n)[:, None] % 4
    g = np.where(y == 3, 0.45, np.where(y == 0, 1.0, 0.85)) * np.ones((1, n)) + (fbm(n, 4, 3) - 0.5) * 0.12
    g[:, :2] *= 0.8
    return ramp(g, [(0, '#2a2420'), (0.6, '#b8b0a0'), (1, '#f8f2e4')])


def picket(n=64):
    """a picket fence (1.3 m a tile, 1-bit alpha): 10 cm pickets with pointed tops, 6 cm gaps, two rails. white-ish
    (tinted), weathered at the feet"""
    a = np.zeros((n, n), np.float32); g = np.zeros((n, n), np.float32)
    yy, xx = np.mgrid[0:n, 0:n]
    yb = n - 1 - yy  # 0 at the bottom
    for x0 in range(0, n, 8):
        w = 5
        body = (xx >= x0) & (xx < x0 + w) & (yb < n - 6)
        tipy = n - 6 + (2 - np.abs(xx - (x0 + 2)))
        tip = (xx >= x0) & (xx < x0 + w) & (yb >= n - 6) & (yb <= tipy)
        a[body | tip] = 1; g[body | tip] = 0.92 - (xx[body | tip] == x0) * 0.15
    for ry in (int(0.3 / 1.3 * n), int(0.95 / 1.3 * n)):
        rows = (yb >= ry) & (yb < ry + 4); a[rows] = 1; g[rows] = 0.8; g[(yb == ry) & rows] = 0.55
    g = g - (yb < 6) * 0.25 * vnoise(n, 8) - speck(n, 0.04) * 0.2
    return ramp(g, [(0, '#2c2620'), (0.7, '#c9c2b0'), (1, '#fffaf0')]), a


# ------------------------------------------------------------ facades (for the tall bodies nobody walks in)
def facade_tenement(n=128):
    """2 bays x 2 floors of a grimy brick tenement (one tile = 7 m wide x 7 m tall): sash windows with sills, lintels,
    some lit, some boarded, a window AC unit dripping, curtains in sick colours, soot down the brick"""
    img = np.zeros((n, n, 3), np.float32); glow = np.zeros((n, n), np.float32)
    b = brick(64); img[:] = np.tile(b, (2, 2, 1))  # (tile 7 m: bricks a bit big up there, reads from far)
    img = shade(img, 0.92)
    rg = np.random.default_rng(21)
    for fy in range(2):
        for bx in range(2):
            x0, y0 = bx * 64 + 18, fy * 64 + 14
            w, h = 28, 36
            kind = rg.choice(['lit', 'dark', 'dark', 'curtain', 'board', 'lit'])
            img[y0 - 4:y0, x0 - 2:x0 + w + 2] = hexc('#b7ad94') * 0.9  # lintel
            img[y0 + h:y0 + h + 3, x0 - 3:x0 + w + 3] = hexc('#c8bea2')  # sill
            img[y0 + h + 3:y0 + h + 4, x0 - 3:x0 + w + 3] = hexc('#2a2420')
            img[y0:y0 + h, x0:x0 + w] = hexc('#e6dcc6')  # frame
            gl = glass(32)
            pane = np.array(Image.fromarray((gl * 255).astype(np.uint8)).resize((w - 4, h // 2 - 3), Image.NEAREST)) / 255.0
            for k in range(2):
                py = y0 + 2 + k * (h // 2)
                if kind == 'lit': img[py:py + h // 2 - 3, x0 + 2:x0 + w - 2] = hexc('#ffd86a') * (0.85 + 0.15 * k); glow[py:py + h // 2 - 3, x0 + 2:x0 + w - 2] = 1
                elif kind == 'board': img[py:py + h // 2 - 3, x0 + 2:x0 + w - 2] = planks(64)[:h // 2 - 3, :w - 4] * 1.1
                else: img[py:py + h // 2 - 3, x0 + 2:x0 + w - 2] = pane
            if kind == 'curtain':
                cc = hexc(rg.choice(['#b0306a', '#6a9a2a', '#c87a1a', '#4a3aa0']))
                img[y0 + 2:y0 + h - 2, x0 + 2:x0 + 9] = cc; img[y0 + 2:y0 + h - 2, x0 + w - 9:x0 + w - 2] = cc * 0.8
            if kind == 'lit' and rg.random() < 0.6:  # a silhouette at the window, or blinds
                img[y0 + 2:y0 + h // 2 - 1:2, x0 + 2:x0 + w - 2] *= 0.7
            if rg.random() < 0.45:  # an AC unit in the lower sash, dripping
                img[y0 + h - 12:y0 + h, x0 + 4:x0 + w - 4] = hexc('#cfd2c8'); img[y0 + h - 10:y0 + h - 2:2, x0 + 6:x0 + w - 6] = hexc('#6a6e68')
                for j in range(1, 20): img[min(n - 1, y0 + h + 3 + j), x0 + w // 2] = mix(img[min(n - 1, y0 + h + 3 + j), x0 + w // 2], hexc('#3a3a2a'), 0.6 * (1 - j / 20))
            soot = np.linspace(0.75, 1.0, 10)
            img[y0 - 12:y0 - 2, x0:x0 + w] = shade(img[y0 - 12:y0 - 2, x0:x0 + w], soot[::-1][:, None] * 0 + soot[:, None])  # soot over each window
    img[0:3, :] = hexc('#a49a84'); img[3, :] = hexc('#3a3028')  # a string course every floor pair
    img[64:66, :] = hexc('#a49a84')
    FAC_GLOW['fac_tenement'] = glow
    return img


def facade_office(n=128):
    """2 bays x 2 floors of a cheap 80s office block (7 m x 7 m a tile): ribbon windows in green-blue glass, beige
    spandrel panels, some blinds down, a lit cubicle, a dead monitor glow, staining"""
    img = np.zeros((n, n, 3), np.float32)
    rg = np.random.default_rng(31)
    span = ramp(0.6 + (fbm(n, 4, 4) - 0.5) * 0.3, [(0, '#3a3a34'), (0.6, '#b7ab8a'), (1, '#dccfa8')])
    img[:] = span
    for fy in range(2):
        y0 = fy * 64 + 22; h = 34
        img[y0 - 2:y0, :] = hexc('#4a4a44'); img[y0 + h:y0 + h + 2, :] = hexc('#6a6a60')
        for bx in range(4):
            x0 = bx * 32 + 1
            kind = rg.choice(['glass', 'glass', 'blind', 'lit', 'glass', 'monitor'])
            gl = np.array(Image.fromarray((glass(32) * 255).astype(np.uint8)).resize((30, h), Image.NEAREST)) / 255.0
            gl = gl * hexc('#7fd0b0') * 1.3
            if kind == 'blind': gl = np.tile(np.array([[hexc('#d8d2b8')], [hexc('#9a9480')]]), (h // 2 + 1, 30, 1))[:h]
            if kind == 'lit': gl = gl * 0.4 + hexc('#f2f0c8') * 0.7; FAC_GLOW.setdefault('fac_office', np.zeros((n, n), np.float32))[y0:y0 + h, x0:x0 + 30] = 1
            if kind == 'monitor': gl[h - 12:h - 6, 8:16] = hexc('#3affd0')
            img[y0:y0 + h, x0:x0 + 30] = np.clip(gl, 0, 1)
            img[y0:y0 + h, x0 + 30:x0 + 32] = hexc('#2c2e2c')  # mullion
    img = mix(img, img * 0.55, streaks(n, 10, length=(0.2, 0.5)) * 0.5)
    return img


def facade_glass(n=128):
    """1 floor x 2 bays of a blue glass curtain wall (4.4 m a tile: Skyline's Spire): the floor's spandrel at the top
    (navy panel, a chrome line), then the two panes: the dusk sky in them, bright at the top, a diagonal sheen, a
    window cleaner's streaks. (it tiles: the lit offices are the model's, scattered)"""
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    sky = ramp(np.clip(1 - yy / n * 1.1 + (fbm(n, 2, 3) - 0.5) * 0.25, 0, 1), [(0, '#1c3a7a'), (0.45, '#3f72c8'), (0.8, '#7ab4f0'), (1, '#c8ecff')])
    sheen = np.clip(1 - abs((xx * 0.9 + yy * 0.7) % n - n * 0.55) / 9, 0, 1) * 0.45
    img = mix(sky, hexc('#e6f6ff'), sheen)
    img = mix(img, img * 0.82, streaks(n, 6, length=(0.15, 0.4)) * 0.6)
    img[0:16, :] = ramp(0.5 + (fbm(n, 6, 2)[0:16] - 0.5) * 0.3, [(0, '#16203a'), (1, '#2e4470')])  # the spandrel
    img[14:16, :] = hexc('#dfe8f2')  # its chrome line
    img[16:18, :] = hexc('#0e1426')  # the pane's top shadow
    for x in (0, 1, 64, 65): img[:, x] = hexc('#c8d4e0')  # mullions (the model adds proud fins too)
    return img


# ------------------------------------------------------------ decals (one 256 px atlas, 1-bit alpha): ads, signs, grime
# a 3 x 5 pixel font (PS1 menus and shop signs were this chunky). lowercase draws as uppercase
GLYPHS = {
 'A': '010101111101101', 'B': '110101110101110', 'C': '011100100100011', 'D': '110101101101110', 'E': '111100110100111',
 'F': '111100110100100', 'G': '011100101101011', 'H': '101101111101101', 'I': '111010010010111', 'J': '001001001101010',
 'K': '101101110101101', 'L': '100100100100111', 'M': '101111111101101', 'N': '110101101101101', 'O': '010101101101010',
 'P': '110101110100100', 'Q': '010101101110011', 'R': '110101110101101', 'S': '011100010001110', 'T': '111010010010010',
 'U': '101101101101111', 'V': '101101101101010', 'W': '101101111111101', 'X': '101101010101101', 'Y': '101101010010010',
 'Z': '111001010100111', '0': '111101101101111', '1': '010110010010111', '2': '110001010100111', '3': '110001010001110',
 '4': '101101111001001', '5': '111100110001110', '6': '011100111101111', '7': '111001010010010', '8': '111101111101111',
 '9': '111101111001110', '&': '010101010101011', '!': '010010010000010', '?': '110001010000010', '-': '000000111000000',
 '/': '001001010100100', '#': '101111101111101', '=': '000111000111000', '<': '001010100010001', '.': '000000000000010',
 "'": '010010000000000', ' ': '000000000000000', '4': '101101111001001', '$': '011110010011110', '%': '101001010100101',
}


def text_img(s, scale, fg, bg=None, pad=1):
    """chunky pixel text in the 3 x 5 font, blown up with nearest neighbour"""
    s = s.upper()
    w = len(s) * 4 - 1 + pad * 2; h = 5 + pad * 2
    im = Image.new('RGBA', (max(1, w), h), bg or (0, 0, 0, 0))
    px = im.load()
    for i, ch in enumerate(s):
        g = GLYPHS.get(ch, GLYPHS['?'])
        for k, bit in enumerate(g):
            if bit == '1': px[pad + i * 4 + k % 3, pad + k // 3] = tuple(fg)
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def decals(n=256):
    """the decal atlas. cells are listed in kit.json with their uv rect, so Blender scripts place them by name"""
    A = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    D = ImageDraw.Draw(A)
    cells = {}

    def cell(name, x, y, w, h): cells[name] = [x / n, y / n, w / n, h / n]

    def board(x, y, w, h, bg, border, lines, name, fgs=None):
        D.rectangle([x, y, x + w - 1, y + h - 1], fill=border)
        D.rectangle([x + 2, y + 2, x + w - 3, y + h - 3], fill=bg)
        cy = y + 4
        for i, (s, sc) in enumerate(lines):
            im = text_img(s, sc, (fgs[i] if fgs else (20, 10, 20, 255)))
            A.alpha_composite(im, (x + (w - im.width) // 2, cy)); cy += im.height + 1
        cell(name, x, y, w, h)

    # row 1: ads for companies that don't exist (64 x 32 each)
    board(0, 0, 64, 32, (255, 225, 77, 255), (255, 79, 216, 255), [('GRISTLE', 1), ('& SONS', 1), ('meat 4 less', 1)], 'ad_gristle', [(150, 20, 30, 255), (150, 20, 30, 255), (20, 10, 20, 255)])
    board(64, 0, 64, 32, (40, 200, 120, 255), (10, 30, 20, 255), [('SMILE', 2), ('insurance', 1)], 'ad_smile', [(255, 255, 230, 255), (10, 40, 20, 255)])
    board(128, 0, 64, 32, (230, 230, 225, 255), (200, 30, 40, 255), [('WE BUY', 1), ('GOLD &', 1), ('TEETH', 1)], 'ad_teeth', [(200, 30, 40, 255)] * 3)
    board(192, 0, 64, 32, (20, 20, 40, 255), (79, 216, 255, 255), [('JANKCORP', 1), ('we own', 1), ('your house', 1)], 'ad_jankcorp', [(79, 216, 255, 255), (255, 255, 255, 255), (255, 79, 216, 255)])
    # row 2: signs (32 x 32)
    board(0, 32, 32, 32, (255, 255, 255, 255), (30, 30, 30, 255), [('FOR', 1), ('SALE', 1)], 'sign_sale', [(200, 30, 40, 255)] * 2)
    D.polygon([(48, 34), (62, 62), (34, 62)], fill=(20, 20, 20, 255)); D.polygon([(48, 38), (59, 60), (37, 60)], fill=(255, 210, 26, 255))
    A.alpha_composite(text_img('!', 2, (20, 20, 20, 255), pad=0), (45, 46)); cell('sign_warn', 32, 32, 32, 32)
    board(64, 32, 32, 32, (255, 210, 26, 255), (20, 20, 20, 255), [('NO', 1), ('LOITER', 1)], 'sign_loiter')
    board(96, 32, 32, 32, (30, 90, 200, 255), (255, 255, 255, 255), [('HOA', 1), ('IS', 1), ('WATCH', 1)], 'sign_hoa', [(255, 255, 255, 255)] * 3)
    # house numbers (16 x 16 each, 8 of them)
    for i, s in enumerate(['13', '66', '4B', '0', '7', '99', '1/2', '404']):
        x, y = 128 + (i % 8) * 16, 32 + (i // 8) * 16
        D.rectangle([x, y, x + 15, y + 11], fill=(30, 26, 22, 255)); im = text_img(s, 1, (230, 200, 120, 255)); A.alpha_composite(im, (x + (16 - im.width) // 2, y + 1)); cell('num_%d' % i, x, y, 16, 12)
    # stickers (16 x 16): a smiley, an eye, a skull-ish, a pink heart
    yy, xx = np.mgrid[0:16, 0:16]
    for i, (col, draw) in enumerate([((255, 225, 77), 'smile'), ((255, 79, 216), 'eye'), ((79, 216, 255), 'x'), ((57, 255, 20), 'heart')]):
        x, y = 128 + i * 16, 48
        D.ellipse([x + 1, y + 1, x + 14, y + 14], fill=col + (255,), outline=(20, 10, 20, 255))
        if draw == 'smile': D.point([(x + 5, y + 5), (x + 10, y + 5)], fill=(20, 10, 20, 255)); D.arc([x + 4, y + 5, x + 11, y + 11], 20, 160, fill=(20, 10, 20, 255))
        if draw == 'eye': D.ellipse([x + 5, y + 5, x + 10, y + 10], fill=(255, 255, 255, 255)); D.ellipse([x + 7, y + 7, x + 9, y + 9], fill=(20, 10, 20, 255))
        if draw == 'x': D.line([x + 4, y + 4, x + 11, y + 11], fill=(20, 10, 20, 255)); D.line([x + 11, y + 4, x + 4, y + 11], fill=(20, 10, 20, 255))
        if draw == 'heart': A.alpha_composite(text_img('<3', 1, (20, 10, 20, 255), pad=0), (x + 5, y + 5))
        cell('sticker_%d' % i, x, y, 16, 16)
    # row 3: graffiti tags (64 x 32): spray scribble letters in neon with a black outline
    tags = [('JANK', (255, 79, 216)), ('B0NK', (57, 255, 20)), ('ugh', (79, 216, 255)), ('HOA=OK', (255, 225, 77))]
    for i, (s, col) in enumerate(tags):
        x, y = i * 64, 64
        im = text_img(s, 2, col + (255,))
        ol = Image.new('RGBA', (im.width + 4, im.height + 4), (0, 0, 0, 0))
        sh = text_img(s, 2, (10, 5, 15, 255))
        for dx in (0, 2, 4):
            for dy in (0, 2, 4): ol.alpha_composite(sh, (dx, dy))
        ol.alpha_composite(im, (2, 2))
        ol = ol.rotate(int(R.integers(-8, 9)), resample=Image.NEAREST, expand=True)
        A.alpha_composite(ol.crop((0, 0, min(64, ol.width), min(32, ol.height))), (x + max(0, (64 - ol.width) // 2), y + max(0, (32 - ol.height) // 2)))
        for _ in range(6):  # drips
            dx, dy = x + int(R.integers(6, 58)), y + int(R.integers(16, 24))
            D.line([dx, dy, dx, dy + int(R.integers(3, 8))], fill=col + (255,))
        cell('tag_%d' % i, x, y, 64, 32)
    # row 4: grime (64 x 64 each): a water stain run, a mould bloom, a scorch, a crack web
    for i, kind in enumerate(['run', 'mould', 'scorch', 'crack']):
        x, y = i * 64, 96
        a = np.zeros((64, 64), np.float32)
        if kind == 'run': a = np.clip(streaks(64, 14, seed=40, length=(0.5, 1.0), width=(1, 3)) * 1.3, 0, 1); a[:, :8] = 0; a[:, 56:] = 0; col = (60, 50, 26)
        if kind == 'mould': a = np.clip(blobs(64, 9, 4, 14, seed=41) * (0.6 + fbm(64, 8, 3, seed=42)) - 0.35, 0, 1) * 2; col = (70, 90, 40)
        if kind == 'scorch': a = np.clip(blobs(64, 4, 10, 26, seed=43) * (0.5 + fbm(64, 8, 3, seed=44)) - 0.3, 0, 1) * 2; col = (20, 16, 14)
        if kind == 'crack': a = cracks(64, 4, seed=45); col = (30, 26, 22)
        a[0, :] = a[-1, :] = 0; a[:, 0] = a[:, -1] = 0
        by = np.tile(BAYER, (16, 16)) + 0.5
        on = (a > by).astype(np.uint8) * 255  # dithered 1-bit coverage: the stain fades in a checker
        im = Image.fromarray(np.dstack([np.full((64, 64), c, np.uint8) for c in col] + [on]), 'RGBA')
        A.alpha_composite(im, (x, y)); cell('grime_' + kind, x, y, 64, 64)
    # row 5: hardware (32 x 32): a vent grille, an electric meter, a junction box with stickers, a dryer vent
    D.rectangle([0, 160, 31, 191], fill=(150, 152, 148, 255)); [D.line([2, 163 + k * 3, 29, 163 + k * 3], fill=(50, 52, 50, 255)) for k in range(9)]; cell('vent', 0, 160, 32, 32)
    D.rectangle([32, 160, 63, 191], fill=(110, 116, 110, 255)); D.ellipse([38, 166, 57, 185], fill=(220, 225, 210, 255), outline=(30, 30, 30, 255)); D.line([47, 175, 52, 170], fill=(200, 30, 30, 255)); cell('meter', 32, 160, 32, 32)
    D.rectangle([64, 160, 95, 191], fill=(90, 100, 90, 255)); D.rectangle([66, 162, 93, 189], outline=(40, 44, 40, 255)); A.alpha_composite(text_img('HV', 2, (255, 210, 26, 255)), (67, 168)); cell('jbox', 64, 160, 32, 32)
    D.ellipse([98, 164, 125, 189], fill=(170, 170, 160, 255), outline=(40, 40, 40, 255)); D.ellipse([104, 170, 119, 183], fill=(30, 30, 30, 255)); cell('dryer', 96, 160, 32, 32)
    # the store's sign: a big lightbox name (128 x 32) for a corner store that isn't any real chain
    board(128, 160, 128, 32, (255, 255, 240, 255), (200, 30, 40, 255), [('KWIK-ISH', 2), ('open 25/8', 1)], 'sign_kwik', [(200, 30, 40, 255), (20, 60, 160, 255)])
    # row 6: posters (32 x 48): lost cat, a band, a missing person who is clearly a mannequin, a wanted bot
    for i, (title, sub, col) in enumerate([('LOST', 'cat?', (255, 255, 230)), ('LIVE', 'sludge', (255, 79, 216)), ('MISSING', 'gary', (255, 255, 230)), ('WANTED', 'bot #7', (230, 210, 160))]):
        x, y = 128 + i * 32, 192
        D.rectangle([x + 1, y + 1, x + 30, y + 46], fill=col + (255,), outline=(40, 30, 30, 255))
        im = text_img(title, 1, (20, 10, 20, 255)); A.alpha_composite(im, (x + (32 - im.width) // 2, y + 3))
        D.rectangle([x + 7, y + 14, x + 24, y + 33], fill=(90, 80, 70, 255)); D.ellipse([x + 11, y + 16, x + 20, y + 25], fill=(210, 170, 140, 255))
        im = text_img(sub, 1, (20, 10, 20, 255)); A.alpha_composite(im, (x + (32 - im.width) // 2, y + 36))
        cell('poster_%d' % i, x, y, 32, 48)
    # a sun-bleached HELP WANTED and an OPEN neon (they glow: emissive in the material by name)
    board(0, 192, 64, 24, (255, 255, 255, 255), (20, 20, 20, 255), [('HELP WANTED', 1), ('(no)', 1)], 'sign_help')
    D.rectangle([0, 224, 63, 255], fill=(25, 10, 30, 255)); im = text_img('OPEN', 2, (255, 79, 216, 255)); A.alpha_composite(im, ((64 - im.width) // 2, 226)); D.rectangle([2, 252, 61, 253], fill=(79, 216, 255, 255)); cell('neon_open', 0, 224, 64, 32)
    D.rectangle([64, 192, 127, 255], fill=(0, 0, 0, 0))
    # a cardboard window patch (taped over a broken pane) and a pizza-box
    D.rectangle([64, 200, 95, 231], fill=(170, 130, 80, 255)); D.line([64, 200, 95, 231], fill=(120, 90, 50, 255)); D.rectangle([64, 214, 95, 217], fill=(200, 190, 150, 255)); cell('cardboard', 64, 200, 32, 32)
    arr = np.asarray(A).astype(np.float32) / 255
    return arr[..., :3], arr[..., 3], cells


def stone(n=64):
    """coursed ashlar (tinted): courses of 8 or 10 px (25-31 cm at 2 m a tile), blocks 12-24 px long with the joints
    broken course to course, pale mortar, each block its own shade, chisel-dark edges, pits and a little lichen"""
    img = np.zeros((n, n, 3), np.float32)
    img[:] = ramp(fbm(n, 4, 3) * 0.5 + 0.45, [(0, '#8e877a'), (1, '#cfc8b6')])  # the mortar
    y = 0
    for h in (8, 10, 8, 10, 8, 10, 10):
        if y >= n: break
        h = min(h, n - y); x = int(R.integers(0, 12))
        while x < n + 12:
            w = int(R.integers(12, 25)); v = 0.72 + R.random() * 0.26
            for yy in range(y + 1, y + h):
                for xx in range(x + 1, x + w):
                    e = 0.9 if (yy == y + 1 or xx == x + 1) else 0.82 if (yy == y + h - 1 or xx == x + w - 1) else 1.0
                    img[yy % n, xx % n] = (v * e,) * 3
            x += w
        y += h
    img = shade(img, 0.86 + fbm(n, 8, 3) * 0.26)
    img = shade(img, 1 - speck(n, 0.05) * 0.25)
    img = mix(img, img * hexc('#7a8a52') * 1.3, blobs(n, 2, 4, 9) * 0.3)
    return img


def weather(n=64):
    """a cutout overlay for sea walls: moss rising from the foot (greens), salt bloom and white streaks running down
    (alpha: only where there's something)"""
    yy = np.arange(n)[:, None] / (n - 1)  # 0 at the top of the tile, 1 at the foot
    moss = np.clip((fbm(n, 4, 4) - 0.55 + yy * 0.6) * 3.0, 0, 1)
    salt = np.clip((fbm(n, 8, 3) - 0.62) * 4, 0, 1) * (1 - yy) + streaks(n, 7, length=(0.3, 0.7), width=(1, 2)) * 0.9
    img = ramp(fbm(n, 8, 3), [(0, '#3f5a26'), (0.5, '#5f7a32'), (1, '#8aa04a')])
    img = mix(img, hexc('#f2efe4'), np.clip(salt - moss, 0, 1))
    a = np.clip(np.maximum(moss, salt), 0, 1)
    return img, (a > 0.5).astype(np.float32)


def profile(n=32):
    """trapezoidal profiled steel sheet, the cladding on sheds and depots (1 m a tile, light grey: tinted). four ribs a
    tile (25 cm), each a lit crown with a shaded and a lit flank, wide flat pans between with a faint stiffening line,
    the odd dent and fixing screw, a little dirt; no rust (the old corrugated sheet is the rusty one)"""
    x = np.arange(n) % 8
    rib = np.select([x == 0, x == 1, x == 2, x == 7], [0.86, 1.1, 0.78, 0.93], 0.97).astype(np.float32)
    rib = np.where(x == 4, 0.94, rib)  # (the stiffener in the pan)
    g = rib[None, :] * np.ones((n, 1), np.float32) + (fbm(n, 4, 3) - 0.5) * 0.08 - speck(n, 0.015) * 0.18
    for _ in range(3):  # screws: a dark dot on a pan, in rows
        yy = int(R.integers(n)); g[yy, (np.arange(4) * 8 + 5) % n] *= 0.6
    img = ramp(np.clip(g * 0.82, 0, 1), [(0, '#2c2e32'), (0.6, '#a9adb2'), (0.82, '#d8dbde'), (1, '#f6f7f6')])
    return shade(img, 1 - np.clip((fbm(n, 2, 4) - 0.6) * 0.6, 0, 0.2))


def main():
    os.makedirs(OUT, exist_ok=True)
    sheet_path = sys.argv[sys.argv.index('--sheet') + 1] if '--sheet' in sys.argv else None
    out = {}
    out['siding'] = save('siding', siding(), 2.0, note='tint')
    out['brick'] = save('brick', brick(), 2.0)
    out['stucco'] = save('stucco', stucco(), 3.0, note='tint')
    out['concrete'] = save('concrete', concrete(), 4.0)
    out['shingle'] = save('shingle', shingle(), 2.0, note='tint')
    out['corrugated'] = save('corrugated', corrugated(), 1.0, note='tint')
    out['planks'] = save('planks', planks(), 2.0)
    out['trim'] = save('trim', trim(), 1.0, note='tint')
    out['lino'] = save('lino', lino(), 2.0)
    out['tar'] = save('tar', tar(), 4.0)
    out['carpet'] = save('carpet', carpet(), 1.0)
    out['metalplate'] = save('metalplate', metalplate(), 1.0, note='tint')
    out['glass'] = save('glass', glass(), 1.0)
    out['louvre'] = save('louvre', louvre(), 0.5, note='tint')
    pk, pa = picket(); out['picket'] = save('picket', pk, 1.3, alpha=pa, note='tint', colors=8, dither=0.5)
    out['fac_tenement'] = save('fac_tenement', facade_tenement(), 7.0, colors=24)
    out['fac_office'] = save('fac_office', facade_office(), 7.0, colors=24)
    out['fac_glass'] = save('fac_glass', facade_glass(), 4.4, colors=24)
    for k, g in FAC_GLOW.items():
        Image.fromarray((g * 255).astype(np.uint8), 'L').save(os.path.join(OUT, k + '_glow.png')); KIT[k]['glow'] = k + '_glow'
    rgb, a, cells = decals()
    out['decals'] = save('decals', rgb, 0, alpha=a, colors=48, dither=0.0)
    KIT['decals']['cells'] = cells
    out['stone'] = save('stone', stone(), 2.0, note='tint')  # (after the decals: the shared RNG leaves every older texture as it was)
    wi, wa = weather(); out['weather'] = save('weather', wi, 2.0, alpha=wa, colors=8, dither=0.5)
    out['profile'] = save('profile', profile(), 1.0, note='tint')  # (last: the shared RNG leaves every older texture as it was)
    json.dump(KIT, open(os.path.join(OUT, 'kit.json'), 'w'), indent=1)
    if sheet_path:  # a contact sheet: every texture blown up 4x, tiled 2x2 so the seams show
        tiles = []
        for k, v in out.items():
            im = Image.fromarray((v * 255).astype(np.uint8))
            if k != 'decals': im = Image.fromarray(np.tile(np.asarray(im), (2, 2, 1)))
            s = 256 / max(im.size)
            tiles.append(im.resize((int(im.width * s), int(im.height * s)), Image.NEAREST))
        W = 6; H = (len(tiles) + W - 1) // W
        sh = Image.new('RGB', (W * 260, H * 260), (18, 8, 24))
        for i, t in enumerate(tiles): sh.paste(t, ((i % W) * 260 + 2, (i // W) * 260 + 2))
        sh.save(sheet_path)
    print('kit:', ', '.join(KIT), '->', OUT)


if __name__ == '__main__':
    main()
