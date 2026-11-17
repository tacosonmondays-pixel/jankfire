# ROPE TEXTURES for the grapple skins (17 Nov 2026): the Beam pictures that a plain colour can't do. Drawn from maths
# (numpy, 4x supersampled), alpha-bled for upload (tools/roblox/vfx/bleed.py), no text, no symbols, nothing that reads
# as a code. Beam pictures run ALONG the rope in x (u) and ACROSS it in y (v); every one tiles in u, so the Beam uses
# TextureMode Wrap with TextureLength = the studs one picture covers (GrappleLook.LOOKS has the numbers).
#   twist   128x32  grey rope strands on a round shade (tinted by Beam.Color: brown rope, cream plunger cord)
#   chain   128x64  grey links: a face-on oval ring, then an edge-on link through the rings' holes (cut out)
#   candy   64x32   red and cream diagonal stripes on a round shade (its own colours: Beam.Color white)
#   vine    256x128 a green stem with a leaf each side per picture (cut out, its own colours)
#   glow    128x32  a hot core in a soft halo, one soft brighter band per picture (tinted: the laser's cyan; scrolls)
#   ribbon  128x32  a soft-edged ribbon with faint band lines (tinted by the rainbow's moving colours)
# run: py -E -P tools/roblox/grapple_ropes.py <out_dir>
import os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vfx'))
from bleed import bleed

SS = 4  # supersampling


def grid(w, h):
    """u, v at every (supersampled) pixel centre: u 0..1 along, v -1..1 across"""
    W, H = w * SS, h * SS
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H * 2 - 1
    return np.meshgrid(u, v)


def finish(rgb, a, w, h):
    """downsample the supersampled picture (premultiplied, so edges don't darken), back to straight alpha"""
    rgb = np.clip(rgb, 0, 1); a = np.clip(a, 0, 1)
    pm = rgb * a[..., None]
    pm = pm.reshape(h, SS, w, SS, 3).mean(axis=(1, 3))
    aa = a.reshape(h, SS, w, SS).mean(axis=(1, 3))
    col = np.where(aa[..., None] > 1e-4, pm / np.maximum(aa[..., None], 1e-4), 0)
    out = np.concatenate([col, aa[..., None]], axis=2)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def hexc(h): return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def round_shade(v, lo=0.62):
    return lo + (1 - lo) * np.sqrt(np.clip(1 - v * v, 0, 1))


def twist():
    w, h = 128, 32
    u, v = grid(w, h)
    a = 1 - smoothstep(0.84, 1.0, np.abs(v))
    s = u * 3 + v * 0.45                          # three strands per picture, wound round the rope
    g = s - np.floor(s)
    bump = 0.7 + 0.3 * np.sin(np.pi * g) ** 0.6   # dark grooves between strands
    val = round_shade(v) * bump
    return finish(np.repeat(val[..., None], 3, 2), a, w, h)


def chain():
    w, h = 128, 64
    W, H = w * SS, h * SS
    x = (np.arange(W) + 0.5) / SS; y = (np.arange(H) + 0.5) / SS
    X, Y = np.meshgrid(x, y)
    dy = Y - 32
    val = np.zeros_like(X); a = np.zeros_like(X)
    # the face-on link: an oval ring round x 32
    dx = X - 32
    eo = (dx / 31) ** 2 + (dy / 24) ** 2
    ei = (dx / 18) ** 2 + (dy / 10) ** 2
    ring = (eo <= 1) & (ei >= 1)
    em = np.sqrt((dx / 24.5) ** 2 + (dy / 17) ** 2)
    sh = 0.5 + 0.5 * np.clip(1 - ((em - 1) / 0.3) ** 2, 0, 1)
    val = np.where(ring, sh, val); a = np.where(ring, 1.0, a)
    # the edge-on link over it: a rounded bar on the middle line whose ends hook into the two rings' holes (it runs
    # from a third of the way into this ring's hole to a third into the next one's, wrapping round the picture's edge)
    for off in (0, -128):
        bx = X - off
        cx = np.clip(bx, 46.5, 145.5)
        d = np.sqrt((bx - cx) ** 2 + dy ** 2)
        m = d <= 6.5
        bsh = 0.55 + 0.45 * (1 - (dy / 6.5) ** 2)
        val = np.where(m, bsh, val); a = np.where(m, 1.0, a)
    return finish(np.repeat(val[..., None], 3, 2), a, w, h)


def candy():
    w, h = 64, 32
    u, v = grid(w, h)
    a = 1 - smoothstep(0.84, 1.0, np.abs(v))
    s = u * 2 + v * 0.5
    g = s - np.floor(s)
    band = smoothstep(0.0, 0.04, g) * (1 - smoothstep(0.38, 0.42, g))   # red over a bit more than a third
    R, C = hexc('b8443f'), hexc('e7e1d7')
    rgb = C[None, None, :] * (1 - band[..., None]) + R[None, None, :] * band[..., None]
    rgb = rgb * round_shade(v, 0.7)[..., None]
    return finish(rgb, a, w, h)


def vine():
    w, h = 256, 128
    W, H = w * SS, h * SS
    x = (np.arange(W) + 0.5) / SS; y = (np.arange(H) + 0.5) / SS
    X, Y = np.meshgrid(x, y)
    STEM, STEM_L, LEAF, RIB = hexc('4e6b3a'), hexc('6a8a4c'), hexc('6f914e'), hexc('587a3e')
    rgb = np.zeros(X.shape + (3,)); a = np.zeros_like(X)
    # leaves first, the stem over their bases. a leaf: a pointed blade from the stem, leaning forward along the vine
    for (bu, up) in ((64, 1), (192, -1)):
        for wrap in (-256, 0, 256):
            ang = np.radians(48)
            dxu, dyu = np.cos(ang), -np.sin(ang) * up            # (image y runs down)
            px, py = X - (bu + wrap), Y - 64
            t = px * dxu + py * dyu                               # along the blade
            n = -px * dyu + py * dxu                              # across it
            L, Wd = 72.0, 34.0
            k = np.clip(t / L, 0, 1)
            half = Wd / 2 * np.sin(np.pi * k) ** 0.8
            m = (t >= 0) & (t <= L) & (np.abs(n) <= half)
            shade = 0.85 + 0.15 * (1 - np.abs(n) / np.maximum(half, 1e-3))
            col = LEAF[None, None, :] * shade[..., None]
            rib = m & (np.abs(n) < 1.6) & (k < 0.85)
            col = np.where(rib[..., None], RIB[None, None, :], col)
            rgb = np.where(m[..., None], col, rgb); a = np.where(m, 1.0, a)
    yc = 64 + 3 * np.sin(2 * np.pi * X / 128)
    d = np.abs(Y - yc)
    stem = d <= 11
    sh = 0.7 + 0.3 * np.clip(1 - (d / 11) ** 2, 0, 1)
    col = STEM[None, None, :] * sh[..., None]
    col = np.where((np.abs(Y - yc + 4) < 2.0)[..., None], STEM_L[None, None, :], col)
    rgb = np.where(stem[..., None], col, rgb); a = np.where(stem, 1.0, a)
    return finish(rgb, a, w, h)


def glow():
    w, h = 128, 32
    u, v = grid(w, h)
    core = np.exp(-(v / 0.2) ** 2)
    halo = np.exp(-(v / 0.55) ** 2) * 0.6
    a = np.clip(core + halo, 0, 1) * (1 - smoothstep(0.9, 1.0, np.abs(v)))
    band = 0.82 + 0.18 * (0.5 + 0.5 * np.cos(2 * np.pi * u))
    val = (0.6 + 0.4 * core / (core + halo + 1e-6)) * band
    return finish(np.repeat(val[..., None], 3, 2), a, w, h)


def ribbon():
    w, h = 128, 32
    u, v = grid(w, h)
    av = np.abs(v)
    body = 1 - smoothstep(0.56, 0.66, av)
    glow_ = (1 - smoothstep(0.62, 1.0, av)) * 0.45
    a = np.maximum(body, glow_)
    lines = 1 - 0.1 * (np.exp(-((av - 0.21) / 0.03) ** 2))     # two faint band lines
    val = (0.86 + 0.14 * (1 - av / 0.62)) * lines
    val = np.where(body > 0.5, val, 0.9)
    return finish(np.repeat(val[..., None], 3, 2), a, w, h)


TEX = {'twist': twist, 'chain': chain, 'candy': candy, 'vine': vine, 'glow': glow, 'ribbon': ribbon}

if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for k, fn in TEX.items():
        im = bleed(fn(), rounds=256)
        p = os.path.join(out, 'grap_rope_%s.png' % k)
        Image.fromarray(im, 'RGBA').save(p)
        print('WROTE', p, im.shape[1], 'x', im.shape[0])
