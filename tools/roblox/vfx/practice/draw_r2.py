# VFX practice round 2 (20 Nov 2026): textures the round-1 review showed missing. White shapes on transparent (the
# emitter's Color tints them) except the puff, which carries its own grey shading. 4x4 flipbooks are 512 px (128 cells).
#   py draw_r2.py <out dir>
import sys, os, math
import numpy as np
from PIL import Image

OUT = sys.argv[1]
SS = 2
rng = np.random.default_rng(7)


def grid(n):
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    return (x - c) / (n / 2), (y - c) / (n / 2)


def save_a(alpha, name, rgb=None):
    h, w = alpha.shape
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = 255 if rgb is None else (np.clip(rgb, 0, 1) * 255).astype(np.uint8)[..., None] if rgb.ndim == 2 else (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    out[..., 3] = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, name + '.png'))
    print(name, w, h)


def down(a, n):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((n, n), Image.LANCZOS), np.float32) / 255


def sheet(fn, name, cells=4, cell=128, shade=False):
    A = np.zeros((cells * cell, cells * cell), np.float32)
    G = np.ones_like(A)
    for i in range(cells * cells):
        t = i / (cells * cells - 1)
        x, y = grid(cell * SS)
        res = fn(t, x, y, i)
        a, g = res if shade else (res, None)
        r, c = divmod(i, cells)
        A[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = down(a, cell)
        if shade:
            G[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = down(g, cell)
    save_a(A, name, G if shade else None)


# 1. a thin crisp ring (dash circles): a 2.5%-wide line, a little brighter on one side
def thin_ring(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y)
    a = np.clip(1 - np.abs(r - 0.86) / 0.025, 0, 1)
    side = 0.65 + 0.35 * np.cos(np.arctan2(y, x) - 0.6)
    save_a(down(a * side, n), 'vfx_thinring')


# 2. ground cracks growing out from the middle (16 frames): branching jagged lines, wider near the centre
def crack_paths(seed, n_main=7):
    r = np.random.default_rng(seed)
    segs = []  # (x0, y0, x1, y1, width, start_frac)
    def walk(x, y, ang, length, width, start, depth):
        steps = int(length / 0.05)
        for s in range(steps):
            ang += r.normal(0, 0.35)
            nx, ny = x + math.cos(ang) * 0.05, y + math.sin(ang) * 0.05
            f = start + (s / steps) * (1 - start) * 0.8
            segs.append((x, y, nx, ny, width * (1 - s / steps * 0.7), f))
            if depth < 2 and r.random() < 0.12:
                walk(nx, ny, ang + r.choice([-1, 1]) * r.uniform(0.5, 1.1), length * 0.45, width * 0.6, f, depth + 1)
            x, y = nx, ny
    for k in range(n_main):
        a0 = k / n_main * 2 * math.pi + r.uniform(-0.3, 0.3)
        walk(0.0, 0.0, a0, r.uniform(0.6, 0.9), 0.035, 0.0, 0)
    return segs


SEGS = crack_paths(11)


def crack(t, x, y, i):
    grow = min(1.0, t * 2.2)  # spreads in the first half, then holds and fades
    a = np.zeros_like(x)
    for x0, y0, x1, y1, w, f in SEGS:
        if f > grow:
            continue
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy + 1e-9
        u = np.clip(((x - x0) * dx + (y - y0) * dy) / L2, 0, 1)
        d = np.hypot(x - (x0 + u * dx), y - (y0 + u * dy))
        a = np.maximum(a, np.clip(1 - d / w, 0, 1))
    centre = np.exp(-(np.hypot(x, y) / 0.12) ** 2) * 0.6
    fade = 1 - max(0, (t - 0.55) / 0.45) ** 1.5
    return np.clip(np.maximum(a, centre) * fade, 0, 1)


# 3. a cartoon puff (dust/cloud), 16 frames: a lumpy cumulus that swells, then thins and breaks up; white body with a
# grey lower rim (its own shading, so it reads on a pale floor)
BLOBS = [(rng.uniform(-0.35, 0.35), rng.uniform(-0.25, 0.3), rng.uniform(0.22, 0.38)) for _ in range(7)]
HOLES = [(rng.uniform(-0.75, 0.75), rng.uniform(-0.65, 0.7), rng.uniform(0.08, 0.22)) for _ in range(14)]


def puff(t, x, y, i):
    s = 0.55 + 0.45 * min(1, t * 2.5)
    a = np.zeros_like(x)
    for bx, by, br in BLOBS:
        d = np.hypot(x - bx * s, y - by * s) / (br * s)
        a = np.maximum(a, np.clip((1 - d) * 6, 0, 1))
    # break up late: random holes that grow and join (eaten from the edges first)
    if t > 0.45:
        k = (t - 0.45) / 0.55
        eat = np.zeros_like(x)
        for hx, hy, hr in HOLES:
            d = np.hypot(x - hx * s, y - hy * s) / (hr * k * 1.6 + 1e-3)
            eat = np.maximum(eat, np.clip((1 - d) * 5, 0, 1))
        a = a * (1 - eat)
    shade = np.clip(0.95 - np.clip(y * s - 0.05, 0, 1) * 0.55, 0.45, 1)  # greyer underneath
    return a * (1 - max(0, t - 0.8) * 3), shade


# 4. an ink shard splat, 16 frames: a long jagged spike with smaller side spikes; stretches then thins away
def ink(t, x, y, i):
    k = t
    a = np.zeros_like(x)
    r = np.random.default_rng(3)
    spikes = [(0.0, 0.95, 0.16)] + [(r.uniform(-2.6, 2.6), r.uniform(0.25, 0.55), r.uniform(0.05, 0.1)) for _ in range(6)]
    for ang0, L, w in spikes:
        ang = ang0 - math.pi / 2  # main spike points up (along the particle's motion when VelocityParallel)
        L = L * (0.6 + 0.4 * min(1, k * 3))
        ux, uy = math.cos(ang), math.sin(ang)
        along = x * ux + y * uy
        across = np.abs(-x * uy + y * ux)
        width = w * np.clip(1 - along / L, 0, 1) * (1 - k * 0.7)
        a = np.maximum(a, ((along > -0.05) & (along < L) & (across < width)).astype(np.float32))
    core = (np.hypot(x, y) < 0.14 * (1 - k * 0.8)).astype(np.float32)
    return np.clip(np.maximum(a, core) * (1 if k < 0.75 else (1 - k) / 0.25), 0, 1)


# 5. a chunkier hit star, 16 frames: frames 0-3 a fat 4-point star with a cut-out middle; 4-9 it bursts into a ring of
# fat sparkles; 10-15 a thin ring breaking up fast (gone by the last frames)
def star4(x, y, L, w, rot=0.0):
    c, s = math.cos(rot), math.sin(rot)
    xr, yr = x * c + y * s, -x * s + y * c
    d = np.abs(xr) / L + np.abs(yr) / w
    d2 = np.abs(xr) / w + np.abs(yr) / L
    return np.clip((1 - np.minimum(d, d2)) * 8, 0, 1)


def hit2(t, x, y, i):
    a = np.zeros_like(x)
    r = np.hypot(x, y)
    if i <= 4:
        k = i / 4
        a = np.maximum(a, star4(x, y, 0.55 + 0.3 * k, 0.2 + 0.05 * k, rot=math.pi / 4))
        a = a * np.clip((r - 0.06 - 0.12 * k) / 0.04, 0, 1)  # the cut-out middle opening up
    if 3 <= i <= 11:
        k = (i - 3) / 8
        R = 0.25 + 0.55 * (1 - (1 - k) ** 2)
        for j in range(6):
            ang = j / 6 * 2 * math.pi + 0.5
            cx, cy = R * math.cos(ang), R * math.sin(ang)
            sz = 0.2 * (1 - k) + 0.05
            a = np.maximum(a, star4(x - cx, y - cy, sz, sz * 0.32, rot=ang) * (1 - k * 0.6))
        a = np.maximum(a, np.clip(1 - np.abs(r - R) / (0.03 * (1 - k) + 0.008), 0, 1) * (1 - k) * 0.8)
    if i >= 10:
        k = (i - 10) / 5
        R = 0.8 + 0.1 * k
        brk = np.clip(0.5 + 0.5 * np.cos(np.arctan2(y, x) * 6) - k, 0, 1)
        a = np.maximum(a, np.clip(1 - np.abs(r - R) / 0.012, 0, 1) * brk * (1 - k))
    return a


thin_ring()
sheet(crack, 'vfx_crack_4x4')
sheet(puff, 'vfx_puff_4x4', shade=True)
sheet(ink, 'vfx_inkshard_4x4')
sheet(hit2, 'vfx_hitstar2_4x4')
