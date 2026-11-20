# VFX practice round 3 (20 Nov 2026): the round-2 critic's texture fixes. White on transparent; hard edges where the pack
# is hand-drawn. 4x4 flipbooks are 512 px (128 px cells).  py draw_r3.py <out dir>
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


def seg(x, y, x0, y0, x1, y1, w0, w1=None):  # 1 inside a tapered segment, hard edge
    w1 = w0 if w1 is None else w1
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy + 1e-9
    u = np.clip(((x - x0) * dx + (y - y0) * dy) / L2, 0, 1)
    d = np.hypot(x - (x0 + u * dx), y - (y0 + u * dy))
    return (d < (w0 + (w1 - w0) * u)).astype(np.float32)


def star4(x, y, Lx, Ly, w):  # a 4-point star, arms Lx sideways and Ly up/down, cel edge
    d1 = np.abs(x) / Lx + np.abs(y) / w
    d2 = np.abs(x) / w + np.abs(y) / Ly
    return (np.minimum(d1, d2) < 1).astype(np.float32)


# 1. hit star v4: frames 0-1 a wide 4-point star (side arms 1.3x the up/down ones); 2-5 a big ring of sparkles; 6-9 a thin
# ring with 7 hair ticks pointing out; 10-15 empty
def hit4(i, x, y):
    r = np.hypot(x, y)
    if i <= 1:
        return star4(x, y, 0.65 * 1.3 * (0.9 + 0.1 * i), 0.65 * (0.9 + 0.1 * i), 0.22)
    if i <= 9:
        k = (i - 2) / 7
        R = 0.45 + 0.45 * (1 - (1 - k) ** 2)
        a = (np.abs(r - R) < (0.018 * (1 - k) + 0.006)).astype(np.float32) * (1 - 0.5 * k)
        if i <= 5:
            for j in range(6):
                ang = j / 6 * 2 * math.pi + 0.3
                cx, cy = R * math.cos(ang), R * math.sin(ang)
                s = 0.1 * (1 - (i - 2) / 4) + 0.04
                c, sn = math.cos(ang), math.sin(ang)
                xr, yr = (x - cx) * c + (y - cy) * sn, -(x - cx) * sn + (y - cy) * c
                a = np.maximum(a, star4(xr, yr, s, s, s * 0.3))
        else:
            for j in range(7):
                ang = j / 7 * 2 * math.pi + 0.2 + 0.15 * math.sin(j * 3.1)
                a = np.maximum(a, seg(x, y, R * math.cos(ang), R * math.sin(ang), (R + 0.12) * math.cos(ang),
                                      (R + 0.12) * math.sin(ang), 0.012, 0.002) * (1 - 0.5 * k))
        return a
    return np.zeros_like(x)


# 2. guard-break burst v3: frames 0-1 a squat chunky body (a rounded square) with 4 big and 3 small fat short points at
# uneven angles; 2-5 three thin separate rings round a hole; 6-15 empty
ARMS = [(0.2, 0.62, 0.3), (1.75, 0.58, 0.28), (3.3, 0.66, 0.3), (4.75, 0.6, 0.27), (0.95, 0.46, 0.18), (2.55, 0.44, 0.17), (4.0, 0.48, 0.18)]


def gburst3(i, x, y):
    r = np.hypot(x, y)
    if i <= 1:
        k = 1 + 0.08 * i
        body = ((np.abs(x) ** 4 + np.abs(y) ** 4) ** 0.25 < 0.38 * k).astype(np.float32)
        for ang, L, w in ARMS:
            body = np.maximum(body, seg(x, y, 0, 0, L * k * math.cos(ang), L * k * math.sin(ang), w * 0.55, 0.01))
        return body
    if i <= 5:
        k = (i - 2) / 3
        a = np.zeros_like(x)
        for R in (0.25, 0.45, 0.62):
            a = np.maximum(a, (np.abs(r - R * (1 + 0.25 * k)) < 0.03 * (1 - 0.4 * k)).astype(np.float32))
        return a
    return np.zeros_like(x)


# 3. hair line v2: one 3 px line ACROSS the canvas (along u): Squash -1 widens a sprite, so the line goes sideways
def hairline2(n=256):
    x, y = grid(n * SS)
    u, v = x * n / 2, y * n / 2
    w = 1.5 * np.clip(1 - (np.abs(u) / 115) ** 2, 0, 1)
    a = (np.abs(u) < 115) * np.clip(1 - np.abs(v) / np.maximum(w, 0.3), 0, 1) * np.clip(w / 1.5 + 0.3, 0, 1)
    save_a(down(a, n), 'vfx_hairline2')


# 4. hair ring v2: one line, bright on one side and faint on the other
def hairring2(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y) * n / 2
    side = 0.25 + 0.75 * np.maximum(0, np.cos(np.arctan2(y, x) - 0.5)) ** 2
    save_a(down(np.clip(1 - np.abs(r - 122) / 1.5, 0, 1) * side, n), 'vfx_hairring2')


# 5. burst disc: 20 hard radial rays round a hot core (the slash's impact flash)
def burstdisc(n=256):
    x, y = grid(n * SS)
    a = (np.hypot(x, y) < 0.1).astype(np.float32)
    rr = np.random.default_rng(4)
    for j in range(20):
        ang = j / 20 * 2 * math.pi + rr.uniform(-0.1, 0.1)
        L = rr.uniform(0.5, 1.0)
        a = np.maximum(a, seg(x, y, 0, 0, L * math.cos(ang), L * math.sin(ang), 0.03, 0.002))
    save_a(down(a, n), 'vfx_burstdisc')


# 6. wind arc v2: one bright main stroke over about 100 degrees (0.03 wide, tapering) with 5 feathered lines round it
def windarc2(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    a = np.zeros_like(r)
    def stroke(R, mid, span, w, alpha):
        frac = np.clip(1 - np.abs(ang - mid) / (span / 2), 0, 1)
        return np.clip(1 - np.abs(r - R) / np.maximum(w * frac ** 0.6, 1e-4), 0, 1) * (frac > 0) * alpha
    a = np.maximum(a, stroke(0.72, 0.0, math.radians(100), 0.03, 1.0))
    rr = np.random.default_rng(8)
    for j, dR in enumerate((-0.12, -0.07, 0.06, 0.11, 0.16)):
        a = np.maximum(a, stroke(0.72 + dR, rr.uniform(-0.25, 0.25), math.radians(rr.uniform(50, 110)), rr.uniform(0.006, 0.012), rr.uniform(0.6, 0.9)))
    save_a(down(a, n), 'vfx_windarc2')


# 7. cracks v2: 10 thin main arms with many forks, full length from the first frame, no blotch in the middle; the frames
# only fade it (the pack's are full size from 0.05 s)
def crack_segs(seed=21):
    r = np.random.default_rng(seed)
    segs = []
    def walk(x, y, ang, length, width, depth):
        steps = int(length / 0.04)
        for s in range(steps):
            ang += r.normal(0, 0.17)
            nx, ny = x + math.cos(ang) * 0.04, y + math.sin(ang) * 0.04
            segs.append((x, y, nx, ny, width * (1 - s / steps * 0.6)))
            if depth < 2 and r.random() < 0.09:
                walk(nx, ny, ang + r.choice([-1, 1]) * r.uniform(0.4, 1.0), length * 0.4, width * 0.7, depth + 1)
            x, y = nx, ny
    for k in range(10):
        walk(0, 0, k / 10 * 2 * math.pi + r.uniform(-0.25, 0.25), r.uniform(0.65, 0.95), 0.012, 0)
    return segs


CSEGS = crack_segs()


def crack2_full(x, y):
    a = np.zeros_like(x)
    for x0, y0, x1, y1, w in CSEGS:
        a = np.maximum(a, seg(x, y, x0, y0, x1, y1, w + 0.004))
    return a


_CRACK = None


def crack2(i, x, y):
    global _CRACK
    if _CRACK is None:
        _CRACK = crack2_full(x, y)
    t = i / 15
    return _CRACK * (1 if t < 0.6 else max(0, 1 - (t - 0.6) / 0.4))


# 8. puff v2: lumpy cumulus swelling (frames 0-7), then shrinking to 0.6 and fading (8-15), no holes; grey underside
rng = np.random.default_rng(7)
BLOBS = [(rng.uniform(-0.35, 0.35), rng.uniform(-0.25, 0.3), rng.uniform(0.22, 0.38)) for _ in range(7)]


def puff2_frame(i):
    n = 128 * SS
    x, y = grid(n)
    t = i / 15
    s = (0.55 + 0.45 * min(1, t * 2.2)) if i <= 7 else 1 - 0.4 * (i - 7) / 8
    a = np.zeros_like(x)
    for bx, by, br in BLOBS:
        d = np.hypot(x - bx * s, y - by * s) / (br * s)
        a = np.maximum(a, np.clip((1 - d) * 6, 0, 1))
    fade = 1 if i <= 7 else 1 - (i - 7) / 8
    shade = np.clip(0.95 - np.clip(y * s - 0.05, 0, 1) * 0.55, 0.45, 1)
    return a * fade, shade


def puff2():
    cell = 128
    A = np.zeros((512, 512), np.float32)
    G = np.ones_like(A)
    for i in range(16):
        a, g = puff2_frame(i)
        r, c = divmod(i, 4)
        A[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = down(a, cell)
        G[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = down(g, cell)
    out = np.zeros((512, 512, 4), np.uint8)
    out[..., :3] = (np.clip(G, 0, 1) * 255).astype(np.uint8)[..., None]
    out[..., 3] = (np.clip(A, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, 'vfx_puff2_4x4.png'))
    print('vfx_puff2_4x4 512 512')


# 9. broken ring: a hard ring 0.06 thick with 3 gaps and tapered ends (the explosion's black swirl ring)
def brokenring(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y)
    ang = (np.arctan2(y, x) + math.pi) / (2 * math.pi)  # 0..1
    a = np.zeros_like(r)
    for a0, a1 in ((0.02, 0.27), (0.36, 0.62), (0.7, 0.95)):
        frac = np.clip((ang - a0) / (a1 - a0), 0, 1)
        on = (ang > a0) & (ang < a1)
        w = 0.03 * np.minimum(1, np.minimum(frac, 1 - frac) * 6)
        a = np.maximum(a, (on & (np.abs(r - 0.8) < w)).astype(np.float32))
    save_a(down(a, n), 'vfx_brokenring')


# 10. dagger: a hard blade 250 px long, widest (12 px) at 30% of its length
def dagger(n=256):
    x, y = grid(n * SS)
    u, v = x * n / 2, y * n / 2  # v from -125 (tip) to 125 (tail)
    t = (v + 125) / 250
    half = np.where(t < 0.3, 6 * (t / 0.3), 6 * np.clip(1 - (t - 0.3) / 0.7, 0, 1))
    save_a(down(((np.abs(u) < half) & (t >= 0) & (t <= 1)).astype(np.float32), n), 'vfx_dagger')


sheet(hit4, 'vfx_hitstar4_4x4')
sheet(gburst3, 'vfx_gburst3_4x4')
hairline2()
hairring2()
burstdisc()
windarc2()
sheet(crack2, 'vfx_crack2_4x4')
puff2()
brokenring()
dagger()
