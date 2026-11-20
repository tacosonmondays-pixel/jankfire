# VFX practice round 4 (20 Nov 2026): the round-3 critic's texture fixes. White on transparent, hard edges where the pack
# is hand-drawn. 4x4 flipbooks are 512 px (128 px cells).  py draw_r4.py <out dir>
import sys, os, math
import numpy as np
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
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


def seg(x, y, x0, y0, x1, y1, w0, w1=None, soft=0.0):
    w1 = w0 if w1 is None else w1
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy + 1e-9
    u = np.clip(((x - x0) * dx + (y - y0) * dy) / L2, 0, 1)
    d = np.hypot(x - (x0 + u * dx), y - (y0 + u * dy))
    w = w0 + (w1 - w0) * u
    if soft <= 0:
        return (d < w).astype(np.float32)
    return np.clip((w - d) / soft + 0.5, 0, 1)


def star4(x, y, Lx, Ly, w):
    d1 = np.abs(x) / Lx + np.abs(y) / w
    d2 = np.abs(x) / w + np.abs(y) / Ly
    return (np.minimum(d1, d2) < 1).astype(np.float32)


def arcs(x, y, R, w, n, gap_deg, phase=0.0, alpha=1.0):  # a ring broken into n arcs with gaps
    r = np.hypot(x, y)
    ang = (np.arctan2(y, x) - phase) % (2 * math.pi)
    per = 2 * math.pi / n
    inside = (ang % per) > math.radians(gap_deg)
    return ((np.abs(r - R) < w) & inside).astype(np.float32) * alpha


# 1. hit star v5: frames 0-1 a smaller fat 4-point star with 4 small holes on the diagonals; 2-5 a ring of 8 chunky
# sparkles with soft halos, starting wide (0.6); 6-9 the ring broken into 5 arcs (40-degree gaps) at half alpha with long
# ticks; 10-15 empty
def hit5(i, x, y):
    r = np.hypot(x, y)
    if i <= 1:
        a = star4(x, y, 0.6, 0.45, 0.26)
        for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            a = a * (np.hypot(x - sx * 0.07, y - sy * 0.07) > 0.05)
        return a
    if i <= 5:
        k = (i - 2) / 3
        R = 0.6 + 0.15 * k
        a = (np.abs(r - R) < 0.012).astype(np.float32) * 0.8
        for j in range(8):
            ang = j / 8 * 2 * math.pi + 0.2
            cx, cy = R * math.cos(ang), R * math.sin(ang)
            c, sn = math.cos(ang), math.sin(ang)
            xr, yr = (x - cx) * c + (y - cy) * sn, -(x - cx) * sn + (y - cy) * c
            s = 0.22 * (1 - 0.35 * k)
            a = np.maximum(a, star4(xr, yr, s, s, s * 0.3))
            a = np.maximum(a, np.exp(-(np.hypot(x - cx, y - cy) / (s * 0.45)) ** 2) * 0.5)
        return a
    if i <= 9:
        k = (i - 6) / 3
        R = 0.8 + 0.08 * k
        a = arcs(x, y, R, 0.01, 5, 40, phase=0.3, alpha=0.5 * (1 - 0.5 * k))
        for j in range(7):
            ang = j / 7 * 2 * math.pi + 0.15
            a = np.maximum(a, seg(x, y, R * math.cos(ang), R * math.sin(ang), (R + 0.2) * math.cos(ang),
                                  (R + 0.2) * math.sin(ang), 0.012, 0.002) * 0.6 * (1 - 0.5 * k))
        return a
    return np.zeros_like(x)


# 2. guard-break burst v4: frames 0-1 a small body (r 0.22) with 4 long jagged arms (0.85) and 4 shorter ones, notch
# spikes on the outline; 2-5 two rings broken into arcs with 9 tapered shards flying out between 0.55 and 0.9; 6-15 empty
def gburst4(i, x, y):
    r = np.hypot(x, y)
    if i <= 1:
        k = 1 + 0.08 * i
        a = (r < 0.22 * k).astype(np.float32)
        for j, (ang, L, w) in enumerate([(0.25, 0.85, 0.2), (1.85, 0.8, 0.19), (3.35, 0.88, 0.2), (4.85, 0.82, 0.19),
                                         (1.05, 0.5, 0.12), (2.6, 0.46, 0.11), (4.1, 0.52, 0.12), (5.6, 0.44, 0.11)]):
            a = np.maximum(a, seg(x, y, 0, 0, L * k * math.cos(ang), L * k * math.sin(ang), w, 0.004))
        for j in range(7):  # notch spikes on the outline
            ang = j / 7 * 2 * math.pi + 0.6
            a = np.maximum(a, seg(x, y, 0.2 * math.cos(ang), 0.2 * math.sin(ang), 0.36 * math.cos(ang), 0.36 * math.sin(ang), 0.05, 0.003))
        return a
    if i <= 5:
        k = (i - 2) / 3
        a = np.maximum(arcs(x, y, 0.3 + 0.1 * k, 0.03, 3, 35, phase=0.4), arcs(x, y, 0.5 + 0.12 * k, 0.03, 4, 30, phase=1.1))
        rr = np.random.default_rng(31)
        for j in range(9):
            ang = j / 9 * 2 * math.pi + rr.uniform(-0.25, 0.25)
            r0 = 0.55 + 0.15 * k + rr.uniform(0, 0.1)
            a = np.maximum(a, seg(x, y, r0 * math.cos(ang), r0 * math.sin(ang), (r0 + 0.2) * math.cos(ang), (r0 + 0.2) * math.sin(ang), 0.03, 0.003))
        return a
    return np.zeros_like(x)


# 3. guard-break ring v3: thinner from the start (0.05), the inner ring only to frame 3, streaks as v2
STREAKS = [(a + 0.25 * math.sin(a * 7), 0.12 + 0.06 * ((k * 37) % 5) / 4) for k, a in
           enumerate(np.linspace(0, 2 * math.pi, 11, endpoint=False))]


def gring3(i, x, y):
    t = i / 15
    r = np.hypot(x, y)
    R = 0.15 + 0.72 * (1 - (1 - t) ** 2.5)
    thick = 0.05 * (1 - t) ** 1.5 + 0.01
    a = np.clip(1 - np.abs(r - R) / thick, 0, 1) ** 0.6
    if i <= 3:
        a = np.maximum(a, np.clip(1 - np.abs(r - R * 0.75) / (thick * 0.5), 0, 1) * 0.7)
    if 3 <= i <= 9:
        k = (i - 3) / 6
        for ang, L in STREAKS:
            r0 = R + 0.05
            a = np.maximum(a, seg(x, y, r0 * math.cos(ang), r0 * math.sin(ang), (r0 + L) * math.cos(ang), (r0 + L) * math.sin(ang), 0.018 * (1 - k), 0.003) * (1 - k * 0.5))
    return a * (1 - t ** 4)


# 4. hair ring v3: one line, 3 px on its bright side tapering to 1 px on the faint side, brightness cos^4
def hairring3(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y) * n / 2
    c = np.maximum(0, np.cos(np.arctan2(y, x) - 0.5))
    width = 0.5 + 1.0 * c ** 2  # half-width in px: 1.5 px bright side, 0.5 px faint side
    a = np.clip(1 - np.abs(r - 122) / width, 0, 1) * (0.2 + 0.8 * c ** 4)
    save_a(down(a, n), 'vfx_hairring3')


# 5. burst disc v2: 32 hard rays (0.75-1.0 long, 0.02 wide at the base) over a soft lens fill
def burstdisc2(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y)
    a = 0.5 * np.clip(1 - r ** 2, 0, 1)
    a = np.maximum(a, (r < 0.08).astype(np.float32))
    rr = np.random.default_rng(6)
    for j in range(32):
        ang = j / 32 * 2 * math.pi + rr.uniform(-0.06, 0.06)
        L = rr.uniform(0.75, 1.0)
        a = np.maximum(a, seg(x, y, 0, 0, L * math.cos(ang), L * math.sin(ang), 0.02, 0.002))
    save_a(down(a, n), 'vfx_burstdisc2')


# 6. wind arc v3: a broader soft main stroke (0.045, soft edge, alpha 0.8) and 8 feathered lines (alpha 0.5-0.8)
def windarc3(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    def stroke(R, mid, span, w, alpha, soft=False):
        frac = np.clip(1 - np.abs(ang - mid) / (span / 2), 0, 1)
        ww = np.maximum(w * frac ** 0.6, 1e-4)
        d = np.clip(1 - np.abs(r - R) / ww, 0, 1)
        return (d ** 0.5 if soft else d) * (frac > 0) * alpha
    a = stroke(0.72, 0.0, math.radians(110), 0.045, 0.8, soft=True)
    rr = np.random.default_rng(12)
    for dR in (-0.16, -0.12, -0.08, -0.05, 0.05, 0.09, 0.13, 0.17):
        a = np.maximum(a, stroke(0.72 + dR, rr.uniform(-0.3, 0.3), math.radians(rr.uniform(50, 120)), rr.uniform(0.006, 0.012), rr.uniform(0.5, 0.8)))
    save_a(down(a, n), 'vfx_windarc3')


# 7. cracks v3: one 1024 px image (not a flipbook), 10 radiating arms with a few forks, lines 3 px tapering to 1 px
def crack3(n=1024):
    x, y = grid(n)
    rr = np.random.default_rng(21)
    a = np.zeros_like(x)
    px = 2.0 / n  # one pixel in grid units
    def walk(x0, y0, ang, length, w0, depth):
        nonlocal a
        steps = int(length / 0.03)
        for s in range(steps):
            ang += rr.normal(0, 0.15)
            x1, y1 = x0 + math.cos(ang) * 0.03, y0 + math.sin(ang) * 0.03
            w = max(0.5, w0 * (1 - s / steps)) * px
            lo_x, hi_x = int((min(x0, x1) + 1) / 2 * n) - 4, int((max(x0, x1) + 1) / 2 * n) + 4
            lo_y, hi_y = int((min(y0, y1) + 1) / 2 * n) - 4, int((max(y0, y1) + 1) / 2 * n) + 4
            lo_x, lo_y = max(lo_x, 0), max(lo_y, 0)
            hi_x, hi_y = min(hi_x, n), min(hi_y, n)
            if hi_x > lo_x and hi_y > lo_y:
                sub = a[lo_y:hi_y, lo_x:hi_x]
                a[lo_y:hi_y, lo_x:hi_x] = np.maximum(sub, seg(x[lo_y:hi_y, lo_x:hi_x], y[lo_y:hi_y, lo_x:hi_x], x0, y0, x1, y1, w, soft=px))
            if depth < 2 and rr.random() < 0.08:
                walk(x1, y1, ang + rr.choice([-1, 1]) * rr.uniform(0.4, 1.0), length * 0.4, w0 * 0.7, depth + 1)
            x0, y0 = x1, y1
    for k in range(10):
        walk(0.0, 0.0, k / 10 * 2 * math.pi + rr.uniform(-0.25, 0.25), rr.uniform(0.6, 0.92), 1.5, 0)
    save_a(a, 'vfx_crack3')


# 8. a fat teardrop flick: hard edge, 30% as wide as long, round end down, point up (along v)
def teardrop(n=256):
    x, y = grid(n * SS)
    # point at y = -0.95, round end centred at y = 0.55 with radius 0.3
    t = np.clip((y + 0.95) / 1.5, 0, 1)
    half = 0.3 * np.sqrt(np.clip(t, 0, 1)) * np.where(y > 0.55, np.sqrt(np.clip(1 - ((y - 0.55) / 0.3) ** 2, 0, 1)), 1)
    a = ((np.abs(x) < half) & (y > -0.95) & (y < 0.85)).astype(np.float32)
    save_a(down(a, n), 'vfx_teardrop')


if __name__ == '__main__':
    sheet(hit5, 'vfx_hitstar5_4x4')
    sheet(gburst4, 'vfx_gburst4_4x4')
    sheet(gring3, 'vfx_gring3_4x4')
    hairring3()
    burstdisc2()
    windarc3()
    crack3()
    teardrop()
