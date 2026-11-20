# VFX practice round 1 (20 Nov 2026): our own textures for rebuilding the pack teachers (no seller images). White on
# transparent: the colour comes from the emitter, the alpha is the shape. Flipbooks are 4x4 (512 px, 128 px cells), played
# OneShot across a particle's life.  py -I draw_r1.py <out dir>
import sys, os, math
import numpy as np
from PIL import Image

OUT = sys.argv[1]
SS = 2  # supersampling


def grid(n):
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    return (x - c) / (n / 2), (y - c) / (n / 2)  # -1..1


def star(x, y, arms, length, width, rot=0.0, core=0.12):
    # an n-armed star: rays that thin to points + a soft hot core
    r = np.hypot(x, y) + 1e-6
    a = np.arctan2(y, x) - rot
    ang = np.abs(((a * arms / (2 * math.pi)) % 1.0) - 0.5) * 2  # 1 on a ray, 0 between
    ray_w = width * np.clip(1 - r / length, 0, 1)  # thins toward the tip
    d = (1 - ang) * r * math.pi * 2 / arms  # distance from the ray's centre line (approx)
    rays = np.clip(1 - d / np.maximum(ray_w, 1e-4), 0, 1) * (r < length)
    glow = np.exp(-(r / core) ** 2)
    return np.clip(np.maximum(rays, glow), 0, 1)


def ring(x, y, radius, thick, soft=0.5):
    r = np.hypot(x, y)
    return np.clip(1 - np.abs(r - radius) / thick, 0, 1) ** (1 / max(soft, 0.05))


def sheet(frames_fn, name, cells=4, cell=128):
    n = cell * SS
    out = np.zeros((cells * cell, cells * cell), np.float32)
    for i in range(cells * cells):
        t = i / (cells * cells - 1)
        x, y = grid(n)
        a = frames_fn(t, x, y)
        im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((cell, cell), Image.LANCZOS)
        r, c = divmod(i, cells)
        out[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = np.asarray(im, np.float32) / 255
    save(out, name)


def save(alpha, name):
    h, w = alpha.shape
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, name + '.png'))
    print(name, w, h)


# 1. hit star: a big 4-point star (frames 0-3) bursting into a ring of small sparkles joined by a thin ring (3-10) that
# thins and breaks up (10-15)
def hit(t, x, y):
    a = np.zeros_like(x)
    if t < 0.3:
        k = t / 0.3
        a = np.maximum(a, star(x, y, 4, 0.55 + 0.35 * k, 0.16 * (1 - 0.5 * k), rot=math.pi / 4 * 0, core=0.16 * (1 - k) + 0.04) * (1 - 0.6 * k))
    if t > 0.12:
        k = (t - 0.12) / 0.88
        R = 0.18 + 0.62 * (1 - (1 - k) ** 2.2)
        thick = 0.05 * (1 - k) + 0.008
        breakup = 0.5 + 0.5 * np.cos(np.arctan2(y, x) * 7 + 1.3)
        a = np.maximum(a, ring(x, y, R, thick) * (1 - k) ** 0.8 * np.clip(breakup + (1 - k) * 1.5, 0, 1))
        for j in range(7):
            ang = j / 7 * 2 * math.pi + 0.4
            cx, cy = R * math.cos(ang), R * math.sin(ang)
            s = (0.22 * (1 - k) ** 1.3 + 0.03) * (0.8 + 0.4 * ((j * 37) % 5) / 4)
            a = np.maximum(a, star(x - cx, y - cy, 4, s, 0.06 * (1 - k) + 0.02, rot=ang, core=0.03) * (1 - k ** 3))
    return a


# 2. guard-break ring: a fat bright ring that thins as it widens, spikes kicking outward, breaking into arcs at the end
def gring(t, x, y):
    R = 0.15 + 0.72 * (1 - (1 - t) ** 2.5)
    thick = 0.12 * (1 - t) ** 1.5 + 0.012
    ang = np.arctan2(y, x)
    arcs = np.clip(0.5 + 0.5 * np.cos(ang * 5 + 2 * t) + (1 - t) * 1.2, 0, 1)
    a = ring(x, y, R, thick) * arcs
    inner = ring(x, y, R * 0.78, thick * 0.5) * (1 - t) * 0.7
    r = np.hypot(x, y)
    spikes = np.clip(1 - np.abs(((ang * 12 / (2 * math.pi)) % 1) - 0.5) * 12, 0, 1) * np.clip(1 - np.abs(r - R - 0.06) / 0.07, 0, 1) * (1 - t) * 0.9
    return np.clip(np.maximum(np.maximum(a, inner), spikes) * (1 - t ** 4), 0, 1)


# 3. guard-break burst: an 8-point jagged star with a hot core, its rays stretching then breaking into shards
def gburst(t, x, y):
    k = t
    a = star(x, y, 8, 0.55 + 0.35 * min(1, k * 3), 0.2 * (1 - k) + 0.03, rot=0.2, core=0.25 * (1 - k) + 0.05)
    a2 = star(x, y, 8, 0.4 + 0.2 * k, 0.12 * (1 - k) + 0.02, rot=0.2 + math.pi / 8, core=0.0)
    shard = np.clip(0.5 + 0.5 * np.sin(np.hypot(x, y) * 40 - k * 20), 0, 1) if k > 0.4 else 1
    return np.clip(np.maximum(a, a2 * 0.8) * (1 - k ** 2.5) * (shard if k > 0.4 else 1), 0, 1)


# 4. a slash arc: a crescent, thick and bright in the middle, tapering to points, with a few streak lines along it
def arc_img(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    span = (ang + math.pi) / (2 * math.pi)  # 0..1 around
    on = np.clip(1 - np.abs(span - 0.5) / 0.32, 0, 1)  # an arc over ~230 degrees, strongest at the middle
    R, thick = 0.72, 0.13 * on ** 0.8
    body = np.clip(1 - np.abs(r - R + 0.03 * on) / np.maximum(thick, 1e-3), 0, 1) * (on > 0)
    lines = np.zeros_like(r)
    for j, (dr, w) in enumerate([(-0.17, 0.012), (0.12, 0.01), (-0.26, 0.008)]):
        o2 = np.clip(1 - np.abs(span - 0.5 - 0.05 * (j - 1)) / 0.24, 0, 1)
        lines = np.maximum(lines, np.clip(1 - np.abs(r - R - dr) / w, 0, 1) * o2 * 0.7)
    a = np.maximum(body ** 0.7, lines)
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((n, n), Image.LANCZOS)
    save(np.asarray(im, np.float32) / 255, 'vfx_arc')


sheet(hit, 'vfx_hitstar_4x4')
sheet(gring, 'vfx_gbreak_ring_4x4')
sheet(gburst, 'vfx_gbreak_burst_4x4')
arc_img()
