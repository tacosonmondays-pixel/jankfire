"""Overlay pictures for the moving wraps (WRAP FLOW in client/WrapAnim, docs/WRAP-TEXTURES.md "Moving wraps").

A SurfaceAppearance cannot scroll, but a Texture can (OffsetStudsU/V at runtime) and, since Roblox's PBR decals, a
Texture can glow (EmissiveMaskContent + EmissiveStrength). So a moving wrap is its still picture plus one or two
see-through Textures laid over its pieces and slid along the gun by WrapAnim. These are those Textures' pictures:
shapes only (round dots, a soft band of light): no text, codes, logos.

  stars: round soft dots of many sizes, seamless both ways (Galaxy's owner rule: dots, never star shapes)
  glint: one soft slanted band of light across a long tile, fading to nothing at the tile's edges (a sweep along the
         gun every few seconds)
  round 2 (20 Nov): embers (rising specks), caustics (a water-light net), curtain (aurora rays), pulses (light dashes
  with tails), scan (one soft bar), rain (thin slanted streaks), petals (single cherry petals), grid (thin neon grid),
  blobs (soft round blobs)

Each kind is two images: <kind>_color.png (RGBA: white light, alpha = how much shows) and <kind>_emit.png (the same
light as a grey emissive mask). Usage: py tools/roblox/wrap_flow.py <out dir> [kinds...]
"""
import os, sys, math, random
import numpy as np
from PIL import Image


def stars(n=150, size=512, seed=7):
    rng = random.Random(seed)
    a = np.zeros((size, size), np.float64)
    tint = np.zeros((size, size, 3), np.float64)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64) + 0.5
    for i in range(n):
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        # many small, a few big (sizes in px of a 512 tile; radius of the core)
        r = 1.0 + 3.2 * rng.random() ** 3.2
        b = rng.uniform(0.55, 1.0)
        col = rng.choice([(1.0, 1.0, 1.0)] * 5 + [(0.82, 0.88, 1.0)] * 3 + [(1.0, 0.93, 0.84)] * 2)
        # seamless: the nearest copy of the centre over the tile's wrap
        dx = (xx - cx + size / 2) % size - size / 2
        dy = (yy - cy + size / 2) % size - size / 2
        d2 = dx * dx + dy * dy
        g = b * np.exp(-d2 / (2 * (r * 0.62) ** 2))
        # a soft halo on the bigger ones
        if r > 2.2:
            g = g + 0.18 * b * np.exp(-d2 / (2 * (r * 2.4) ** 2))
        g = np.where(d2 < (r * 6) ** 2, g, 0)
        new = np.maximum(a, g)
        w = (g >= a)[..., None]
        tint = np.where(w, np.array(col), tint)
        a = new
    a = np.clip(a, 0, 1)
    rgb = np.where(a[..., None] > 0.002, tint, 1.0)
    return rgb, a


def glint(w=512, h=128):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64) + 0.5
    # the band leans (its x moves with the height), centred in the tile
    cx = w * 0.5 + (yy - h / 2) * 0.55
    d = xx - cx
    core = np.exp(-(d / 9.0) ** 2)
    halo = 0.42 * np.exp(-(d / 34.0) ** 2)
    a = np.clip(core * 0.62 + halo, 0, 1)
    # fade to nothing at the left and right edges (the tile repeats along the gun) and soften top and bottom
    ex = np.clip(np.minimum(xx, w - xx) / (w * 0.18), 0, 1)
    ey = np.clip(np.minimum(yy, h - yy) / (h * 0.12), 0, 1)
    a = a * ex * ey
    rgb = np.ones((h, w, 3)) * np.array([1.0, 0.97, 0.9])
    return rgb, a


# ---- round 2 (20 Nov 2026, main: "the next batch of animated wraps"). Every picture is white light (the layer's tint
# colours it in the game) on transparent, seamless in the directions it moves.

def _grid(size_y, size_x):
    yy, xx = np.mgrid[0:size_y, 0:size_x].astype(np.float64) + 0.5
    return yy, xx


def _wrapd(d, n):
    return (d + n / 2) % n - n / 2


def embers(n=70, size=512, seed=11):
    """small glowing specks, a little drawn out upward (they rise), a few with a soft halo: Lava"""
    rng = random.Random(seed)
    yy, xx = _grid(size, size)
    a = np.zeros((size, size))
    for _ in range(n):
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        r = 1.1 + 2.2 * rng.random() ** 2.5
        b = rng.uniform(0.5, 1.0)
        dx, dy = _wrapd(xx - cx, size), _wrapd(yy - cy, size)
        d2 = dx * dx + (dy / 2.2) ** 2           # (taller than wide)
        g = b * np.exp(-d2 / (2 * (r * 0.6) ** 2))
        if r > 2.0:
            g = g + 0.16 * b * np.exp(-d2 / (2 * (r * 2.6) ** 2))
        a = np.maximum(a, g)
    return np.ones((size, size, 3)), np.clip(a, 0, 1)


def caustics(size=512, cells=7, seed=5):
    """water light: the thin bright net of a periodic Voronoi's edges, softened: Big Wave, Koi Pond"""
    rng = np.random.default_rng(seed)
    yy, xx = _grid(size, size)
    pts = rng.uniform(0, size, (cells * cells, 2))
    d1 = np.full((size, size), 1e9); d2 = np.full((size, size), 1e9)
    for px, py in pts:
        for ox in (-size, 0, size):
            for oy in (-size, 0, size):
                d = np.hypot(xx - px - ox, yy - py - oy)
                nd1 = np.minimum(d1, d)
                d2 = np.where(d < d1, d1, np.minimum(d2, d))
                d1 = nd1
    edge = d2 - d1                                    # 0 on the cell borders
    line = np.exp(-(edge / 5.0) ** 2) * 0.85 + np.exp(-(edge / 16.0) ** 2) * 0.2
    # brighter where three cells meet, a little uneven along each line
    wob = 0.75 + 0.25 * np.sin(xx / size * 2 * np.pi * 3 + np.sin(yy / size * 2 * np.pi * 2) * 1.5)
    return np.ones((size, size, 3)), np.clip(line * wob, 0, 1)


def curtain(size=512, seed=3):
    """soft vertical rays of an aurora curtain, uneven in strength along the gun, brighter low down: Aurora"""
    rng = random.Random(seed)
    yy, xx = _grid(size, size)
    a = np.zeros((size, size))
    for _ in range(14):
        cx = rng.uniform(0, size); w = rng.uniform(4, 22); b = rng.uniform(0.25, 0.8)
        a += b * np.exp(-(_wrapd(xx - cx, size) / w) ** 2)
    hem = 0.55 + 0.45 * np.cos((yy / size) * 2 * np.pi)       # (periodic up and down, so it tiles)
    a = a * hem
    a = a / a.max() * 0.75
    return np.ones((size, size, 3)), np.clip(a, 0, 1)


def pulses(w=1024, h=256, seed=9):
    """short bright dashes with fading tails in a few lanes along the gun: travelling light (Circuit, Neon Hex)"""
    rng = random.Random(seed)
    yy, xx = _grid(h, w)
    a = np.zeros((h, w))
    lanes = [h * (i + 0.5) / 6 for i in range(6)]
    for y0 in lanes:
        for _ in range(rng.choice([1, 1, 2])):
            hx = rng.uniform(0, w); L = rng.uniform(70, 170)
            dx = _wrapd(xx - hx, w)
            tail = np.where((dx <= 0) & (dx > -L), (1 + dx / L) ** 2, 0)      # (the head leads along +u)
            head = np.exp(-(dx / 3.5) ** 2)
            prof = np.exp(-((yy - y0) / 1.6) ** 2)
            a = np.maximum(a, (0.55 * tail + head) * prof)
    return np.ones((h, w, 3)), np.clip(a, 0, 1)


def scan(w=128, h=512):
    """one soft bright horizontal bar in a tall tile, faint below it: a CRT's rolling bar"""
    yy, xx = _grid(h, w)
    d = _wrapd(yy - h * 0.5, h)
    a = 0.55 * np.exp(-(d / 10.0) ** 2) + 0.18 * np.exp(-(d / 46.0) ** 2)
    return np.ones((h, w, 3)), np.clip(a, 0, 1)


def rain(size=512, n=60, seed=21):
    """thin falling streaks, all at one slight slant: Tokyo Night"""
    rng = random.Random(seed)
    yy, xx = _grid(size, size)
    a = np.zeros((size, size))
    slant = 0.18
    for _ in range(n):
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        L = rng.uniform(18, 52); b = rng.uniform(0.35, 0.8)
        dy = _wrapd(yy - cy, size)
        dx = _wrapd(xx - cx - dy * slant, size)
        along = np.clip(1 - np.abs(dy) / L, 0, 1)
        g = b * along ** 1.5 * np.exp(-(dx / 0.8) ** 2)
        a = np.maximum(a, g)
    return np.ones((size, size, 3)), np.clip(a, 0, 1)


def petals(size=512, n=14, seed=23):
    """single cherry petals: a soft oval, narrower at its base, with a small notch at its tip; several sizes and
    turns; a faint blush toward the base: Sakura Storm"""
    rng = random.Random(seed)
    yy, xx = _grid(size, size)
    a = np.zeros((size, size))
    rgb = np.ones((size, size, 3))
    for _ in range(n):
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        s = rng.uniform(13, 24); th = rng.uniform(0, np.pi * 2); b = rng.uniform(0.6, 0.95)
        dx, dy = _wrapd(xx - cx, size), _wrapd(yy - cy, size)
        u = (dx * np.cos(th) + dy * np.sin(th)) / s
        v = (-dx * np.sin(th) + dy * np.cos(th)) / s
        half = 0.62 * np.sqrt(np.clip(1 - u * u, 0, 1)) * (0.62 + 0.38 * np.clip((u + 1) / 2, 0, 1))
        inner = half - np.abs(v)
        notch = 0.16 - np.hypot(u - 1.0, v * 1.3)          # (a small bite out of the tip)
        sd = np.minimum(inner, -notch)
        g = b * np.clip(sd * s / 1.4, 0, 1)
        blush = np.clip((1 - u) / 2, 0, 1)
        tint = np.stack([np.ones_like(u), 1 - 0.16 * blush, 1 - 0.1 * blush], -1)
        rgb = np.where((g > a)[..., None], tint, rgb)
        a = np.maximum(a, g)
    return rgb, np.clip(a, 0, 1)


def grid(size=512, cells=6):
    """a thin neon grid, lines across and along the gun: Vaporwave's floor"""
    yy, xx = _grid(size, size)
    step = size / cells
    dx = np.abs(_wrapd(xx, step)); dy = np.abs(_wrapd(yy, step))
    a = np.maximum(np.exp(-(dx / 1.4) ** 2), np.exp(-(dy / 1.4) ** 2)) * 0.8
    a = np.maximum(a, 0.18 * np.maximum(np.exp(-(dx / 6) ** 2), np.exp(-(dy / 6) ** 2)))
    return np.ones((size, size, 3)), np.clip(a, 0, 1)


def blobs(size=512, n=6, seed=8):
    """soft round blobs of a few sizes, soft-edged, rising: Lava Lamp"""
    rng = random.Random(seed)
    yy, xx = _grid(size, size)
    a = np.zeros((size, size))
    for _ in range(n):
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        r = rng.uniform(26, 70); b = rng.uniform(0.3, 0.55)
        dx, dy = _wrapd(xx - cx, size), _wrapd(yy - cy, size) * 0.85
        d = np.hypot(dx, dy) / r
        g = b * np.exp(-(d / 0.62) ** 4) + 0.12 * b * np.exp(-(d / 1.1) ** 2)
        a = np.maximum(a, g)
    return np.ones((size, size, 3)), np.clip(a, 0, 1)


KINDS = {'stars': stars, 'glint': glint, 'embers': embers, 'caustics': caustics, 'curtain': curtain,
         'pulses': pulses, 'scan': scan, 'rain': rain, 'petals': petals, 'grid': grid, 'blobs': blobs}


def save(out, kind, rgb, a):
    col = np.concatenate([rgb, a[..., None]], -1)
    Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGBA').save(os.path.join(out, 'flow_%s_color.png' % kind))
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), 'L').save(os.path.join(out, 'flow_%s_emit.png' % kind))


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for k in (sys.argv[2:] or list(KINDS)):
        save(out, k, *KINDS[k]())
    print('wrote', [f for f in os.listdir(out) if f.startswith('flow_')])


if __name__ == '__main__':
    main()
