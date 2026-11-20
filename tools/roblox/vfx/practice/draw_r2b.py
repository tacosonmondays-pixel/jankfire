# VFX practice round 2, part b (20 Nov 2026): the round-1 critic's texture fixes. White on transparent, hard (cel) edges
# where the pack is hand-drawn. 4x4 flipbooks are 512 px (128 px cells).  py draw_r2b.py <out dir>
import sys, os, math
import numpy as np
from PIL import Image

OUT = sys.argv[1]
SS = 2


def grid(n):
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    return (x - c) / (n / 2), (y - c) / (n / 2)


def down(a, n):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((n, n), Image.LANCZOS), np.float32) / 255


def save_a(alpha, name):
    h, w = alpha.shape
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = 255
    out[..., 3] = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, name + '.png'))
    print(name, w, h)


def sheet(fn, name, cells=4, cell=128):
    A = np.zeros((cells * cell, cells * cell), np.float32)
    for i in range(cells * cells):
        x, y = grid(cell * SS)
        r, c = divmod(i, cells)
        A[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = down(fn(i, x, y), cell)
    save_a(A, name)


def hard(a, edge=0.5, soft=0.08):  # a cel edge: alpha snaps from 0 to 1 around `edge`
    return np.clip((a - edge) / soft + 0.5, 0, 1)


def nstar(x, y, n, L, w, rot=0.0):  # an n-point star with straight tapering arms (distance field, 1 inside)
    r = np.hypot(x, y) + 1e-6
    a = np.arctan2(y, x) - rot
    seg = (a % (2 * math.pi / n)) - math.pi / n
    half = w / 2 * np.clip(1 - r / L, 0, 1)
    return (np.abs(np.sin(seg)) * r < half).astype(np.float32)


def line(x, y, x0, y0, x1, y1, w0, w1=None):
    w1 = w0 if w1 is None else w1
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy + 1e-9
    u = np.clip(((x - x0) * dx + (y - y0) * dy) / L2, 0, 1)
    d = np.hypot(x - (x0 + u * dx), y - (y0 + u * dy))
    w = w0 + (w1 - w0) * u
    return np.clip(1 - d / np.maximum(w, 1e-4), 0, 1)


# 1. hit star v3: frames 0-2 a small fat cel-edged 4-point star; 3-10 a sparse ring of small sparkles on one thin line,
# radius at most 0.6; 11-15 empty
def hit3(i, x, y):
    if i <= 2:
        k = i / 2
        return nstar(x, y, 4, 0.4 + 0.08 * k, 0.6 - 0.1 * k, rot=math.pi / 4) * 1.0
    if i <= 10:
        k = (i - 3) / 7
        R = 0.22 + 0.38 * (1 - (1 - k) ** 2)
        r = np.hypot(x, y)
        a = np.clip(1 - np.abs(r - R) / (0.02 * (1 - k) + 0.006), 0, 1) * (1 - k * 0.7)
        for j in range(6):
            ang = j / 6 * 2 * math.pi + 0.3
            cx, cy = R * math.cos(ang), R * math.sin(ang)
            a = np.maximum(a, nstar(x - cx, y - cy, 4, 0.09 * (1 - k * 0.6) + 0.02, 0.06, rot=ang))
        return a * np.clip(1 - (k - 0.6) / 0.4, 0, 1) if k > 0.6 else a
    return np.zeros_like(x)


# 2. guard-break burst v2: frames 0-3 a 6-point star with a solid hard core; 3-7 two thick concentric rings round a hole
# with shards flying out; 8-15 empty
def gburst2(i, x, y):
    r = np.hypot(x, y)
    if i <= 3:
        k = i / 3
        # (a jagged 7-armed burst with uneven arms: an abstract spark, not a regular star shape)
        s = np.zeros_like(x)
        for j, (L, w) in enumerate([(0.9, 0.5), (0.7, 0.42), (0.95, 0.55), (0.62, 0.38), (0.85, 0.5), (0.72, 0.44), (0.8, 0.48)]):
            ang = j / 7 * 2 * math.pi + 0.3 + 0.12 * math.sin(j * 2.3)
            s = np.maximum(s, (line(x, y, 0, 0, (L + 0.1 * k) * math.cos(ang), (L + 0.1 * k) * math.sin(ang), w * 0.32, 0.004) > 0.5).astype(np.float32))
        core = (r < 0.3 + 0.05 * k).astype(np.float32)
        hole = (r > 0.1 * k).astype(np.float32) if i == 3 else 1
        return np.maximum(s, core) * hole
    if i <= 7:
        k = (i - 4) / 3
        a = np.zeros_like(x)
        for R in (0.3 + 0.15 * k, 0.5 + 0.2 * k):
            a = np.maximum(a, (np.abs(r - R) < 0.07 * (1 - 0.6 * k)).astype(np.float32))
        for j in range(7):
            ang = j / 7 * 2 * math.pi + 0.5 + (j % 2) * 0.2
            r0 = 0.62 + 0.2 * k
            a = np.maximum(a, line(x, y, r0 * math.cos(ang), r0 * math.sin(ang), (r0 + 0.18) * math.cos(ang),
                                   (r0 + 0.18) * math.sin(ang), 0.035 * (1 - k * 0.5), 0.004))
        return a
    return np.zeros_like(x)


# 3. guard-break ring v2: a ring thinning as it widens; 10-12 uneven radial streaks outside it in frames 3-9; the
# inner ring only until frame 5
STREAKS = [(a + 0.25 * math.sin(a * 7), 0.12 + 0.06 * ((k * 37) % 5) / 4) for k, a in
           enumerate(np.linspace(0, 2 * math.pi, 11, endpoint=False))]


def gring2(i, x, y):
    t = i / 15
    r = np.hypot(x, y)
    R = 0.15 + 0.72 * (1 - (1 - t) ** 2.5)
    thick = 0.1 * (1 - t) ** 1.5 + 0.012
    a = np.clip(1 - np.abs(r - R) / thick, 0, 1) ** 0.6
    if i <= 5:
        a = np.maximum(a, np.clip(1 - np.abs(r - R * 0.75) / (thick * 0.5), 0, 1) * 0.7)
    if 3 <= i <= 9:
        k = (i - 3) / 6
        for ang, L in STREAKS:
            r0 = R + 0.05
            a = np.maximum(a, line(x, y, r0 * math.cos(ang), r0 * math.sin(ang), (r0 + L) * math.cos(ang),
                                   (r0 + L) * math.sin(ang), 0.018 * (1 - k), 0.003) * (1 - k * 0.5))
    return a * (1 - t ** 4)


# 4. hair ring: a 3 px line on 256 px and a fainter one 6 px inside it
def hairring(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y) * n / 2  # in pixels
    a = np.clip(1 - np.abs(r - 122) / 1.5, 0, 1) + 0.45 * np.clip(1 - np.abs(r - 116) / 1.2, 0, 1)
    save_a(down(a, n), 'vfx_hairring')


# 5. hair line: one 3 px line about 230 px long down the middle of a square canvas (along v, the way a VelocityParallel
# particle points), tapered at both ends
def hairline(n=256):
    x, y = grid(n * SS)
    v = y * n / 2
    u = x * n / 2
    w = 1.5 * np.clip(1 - (np.abs(v) / 115) ** 2, 0, 1)
    a = (np.abs(v) < 115) * np.clip(1 - np.abs(u) / np.maximum(w, 0.3), 0, 1) * np.clip(w / 1.5 + 0.3, 0, 1)
    save_a(down(a, n), 'vfx_hairline')


# 6. a small soft dot (16 px across on 64)
def dot(n=64):
    x, y = grid(n * SS)
    r = np.hypot(x, y) * n / 2
    save_a(down(np.clip(1 - r / 8, 0, 1) ** 1.5, n), 'vfx_dot')


# 7. a wind arc: 7 thin parallel streak lines over about 140 degrees, broken lengths, each tapering at both ends; no body
def windarc(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    a = np.zeros_like(r)
    rr = np.random.default_rng(5)
    for j in range(7):
        R = 0.55 + j * 0.055
        a0 = math.radians(-70) + rr.uniform(-0.3, 0.3)
        span = math.radians(rr.uniform(60, 140))
        mid = a0 + span / 2
        frac = np.clip(1 - np.abs(ang - mid) / (span / 2), 0, 1)
        w = rr.uniform(0.006, 0.015) * frac ** 0.6
        a = np.maximum(a, np.clip(1 - np.abs(r - R) / np.maximum(w, 1e-4), 0, 1) * (frac > 0) * rr.uniform(0.4, 0.8))
    save_a(down(a, n), 'vfx_windarc')


# 8. a needle: a hard-edged lens 8 px wide and 240 px tall
def needle(n=256):
    x, y = grid(n * SS)
    u, v = np.abs(x * n / 2), np.abs(y * n / 2)
    half = 4 * np.clip(1 - (v / 120) ** 2, 0, 1)
    save_a(down(((u < half) & (v < 120)).astype(np.float32), n), 'vfx_needle')


# 9. an ink splat, 16 frames: a hard-edged blob with 12 tapering dagger spikes; it breaks into fragments over frames 6-15
SPIKES = [(a + np.random.default_rng(9).uniform(-0.15, 0.15), L) for a, L in
          zip(np.linspace(0, 2 * math.pi, 12, endpoint=False), np.random.default_rng(10).uniform(0.45, 0.95, 12))]
_fr = np.random.default_rng(21)
FRAGS = [(_fr.uniform(-0.6, 0.6, 2), _fr.uniform(0.08, 0.16)) for k in range(7)]


def splat(i, x, y):
    t = i / 15
    r = np.hypot(x, y)
    if i <= 6:
        k = i / 6
        a = (r < 0.32 * (1 - 0.3 * k)).astype(np.float32)
        for ang, L in SPIKES:
            Lk = L * (0.7 + 0.3 * k)
            a = np.maximum(a, (line(x, y, 0.2 * math.cos(ang), 0.2 * math.sin(ang), Lk * math.cos(ang), Lk * math.sin(ang), 0.1, 0.004) > 0.5).astype(np.float32))
        return a
    k = (i - 7) / 8
    a = np.zeros_like(x)
    for (fx, fy), fr in FRAGS:
        cx, cy = fx * (1 + k * 0.5), fy * (1 + k * 0.5)
        rad = fr * (1 - k * 0.8)
        a = np.maximum(a, (np.hypot(x - cx, y - cy) < rad).astype(np.float32))
        a = np.maximum(a, (line(x, y, cx, cy, cx * 1.35, cy * 1.35, rad * 0.6, 0.003) > 0.5).astype(np.float32))
    return a


sheet(hit3, 'vfx_hitstar3_4x4')
sheet(gburst2, 'vfx_gburst2_4x4')
sheet(gring2, 'vfx_gring2_4x4')
hairring()
hairline()
dot()
windarc()
needle()
sheet(splat, 'vfx_splat_4x4')
