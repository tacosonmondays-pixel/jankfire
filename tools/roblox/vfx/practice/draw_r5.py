# VFX practice round 5 (20 Nov 2026): the round-4 critic's texture fixes. White on transparent unless noted.
#   py draw_r5.py <out dir>
import sys, os, math
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draw_r4  # noqa: E402  (its drawing runs only as a script)
from draw_r4 import grid, down, seg, star4, arcs  # noqa: E402

OUT = sys.argv[1]
SS = 2
draw_r4.OUT = OUT
save_a, sheet = draw_r4.save_a, draw_r4.sheet


# 1. hit star v6: star frames 0-1; frames 2-4 five uneven chunky sparkles (sizes x0.6-1.2, halos stretched along the
# ring) on a faint ring line; frames 5-9 the broken arcs with ticks; 10-15 empty
SPARK = [(0.2, 1.0), (1.4, 0.7), (2.2, 1.2), (3.9, 0.6), (5.0, 0.9)]


def hit6(i, x, y):
    r = np.hypot(x, y)
    if i <= 1:
        a = star4(x, y, 0.6, 0.45, 0.26)
        for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            a = a * (np.hypot(x - sx * 0.07, y - sy * 0.07) > 0.05)
        return a
    if i <= 4:
        k = (i - 2) / 2
        R = 0.6 + 0.15 * k
        a = (np.abs(r - R) < 0.012).astype(np.float32) * 0.4
        for ang, sc in SPARK:
            cx, cy = R * math.cos(ang), R * math.sin(ang)
            c, sn = math.cos(ang), math.sin(ang)
            xr, yr = (x - cx) * c + (y - cy) * sn, -(x - cx) * sn + (y - cy) * c
            s = 0.22 * sc * (1 - 0.35 * k)
            a = np.maximum(a, star4(xr, yr, s, s, s * 0.3))
            a = np.maximum(a, np.exp(-((xr / (s * 0.45)) ** 2 + (yr / (s * 0.9)) ** 2)) * 0.5)  # halo 2:1 along the ring
        return a
    if i <= 9:
        k = (i - 5) / 4
        R = 0.8 + 0.08 * k
        a = arcs(x, y, R, 0.01, 5, 40, phase=0.3, alpha=0.5 * (1 - 0.5 * k))
        for j in range(7):
            ang = j / 7 * 2 * math.pi + 0.15
            a = np.maximum(a, seg(x, y, R * math.cos(ang), R * math.sin(ang), (R + 0.2) * math.cos(ang),
                                  (R + 0.2) * math.sin(ang), 0.012, 0.002) * 0.6 * (1 - 0.5 * k))
        return a
    return np.zeros_like(x)


# 2. guard-break burst v5: frames 0-1 a squat chunky star (body r 0.32, long arms 0.6 x 0.3, short arms 0.35, 10 small
# notches round the outline); 2-5 three nearly whole rings (10-15 degree breaks) with shards; 6-15 empty
def gburst5(i, x, y):
    r = np.hypot(x, y)
    if i <= 1:
        k = 1 + 0.06 * i
        a = (r < 0.32 * k).astype(np.float32)
        for ang, L, w in [(0.25, 0.6, 0.3), (1.85, 0.58, 0.3), (3.35, 0.62, 0.3), (4.85, 0.6, 0.3),
                          (1.05, 0.35, 0.18), (2.6, 0.33, 0.17), (4.1, 0.36, 0.18), (5.6, 0.34, 0.17)]:
            a = np.maximum(a, seg(x, y, 0, 0, L * k * math.cos(ang), L * k * math.sin(ang), w, 0.01))
        for j in range(10):
            ang = j / 10 * 2 * math.pi + 0.33
            a = np.maximum(a, seg(x, y, 0.3 * math.cos(ang), 0.3 * math.sin(ang), 0.42 * math.cos(ang), 0.42 * math.sin(ang), 0.04, 0.003))
        return a
    if i <= 5:
        k = (i - 2) / 3
        a = np.maximum(np.maximum(arcs(x, y, 0.3 + 0.08 * k, 0.03, 3, 12, phase=0.4), arcs(x, y, 0.5 + 0.1 * k, 0.03, 4, 14, phase=1.1)),
                       arcs(x, y, 0.65 + 0.12 * k, 0.025, 3, 12, phase=2.0))
        rr = np.random.default_rng(31)
        for j in range(9):
            ang = j / 9 * 2 * math.pi + rr.uniform(-0.25, 0.25)
            r0 = 0.7 + 0.15 * k + rr.uniform(0, 0.08)
            a = np.maximum(a, seg(x, y, r0 * math.cos(ang), r0 * math.sin(ang), (r0 + 0.2) * math.cos(ang), (r0 + 0.2) * math.sin(ang), 0.03, 0.003))
        return a
    return np.zeros_like(x)


# 3. guard-break ring v4: a hard thin ring (0.02 constant), 2-3 broken inner arcs at 0.85 R, the streaks as before
STREAKS = [(a + 0.25 * math.sin(a * 7), 0.12 + 0.06 * ((k * 37) % 5) / 4) for k, a in
           enumerate(np.linspace(0, 2 * math.pi, 11, endpoint=False))]


def gring4(i, x, y):
    t = i / 15
    r = np.hypot(x, y)
    R = 0.15 + 0.72 * (1 - (1 - t) ** 2.5)
    a = (np.abs(r - R) < 0.02).astype(np.float32)
    a = np.maximum(a, arcs(x, y, R * 0.85, 0.012, 3, 70, phase=0.7, alpha=0.8))
    if 3 <= i <= 9:
        k = (i - 3) / 6
        for ang, L in STREAKS:
            r0 = R + 0.05
            a = np.maximum(a, seg(x, y, r0 * math.cos(ang), r0 * math.sin(ang), (r0 + L) * math.cos(ang), (r0 + L) * math.sin(ang), 0.018 * (1 - k), 0.003) * (1 - k * 0.5))
    return a * (1 - t ** 4)


# 4. puff v3: a lumpy cumulus filling ~90% of the cell from the first frame, shrinking (no fade) late; grey underside
rng = np.random.default_rng(7)
BLOBS = [(-0.5, 0.12, 0.42), (0.0, -0.3, 0.48), (0.5, 0.08, 0.42), (-0.24, 0.38, 0.4), (0.26, 0.4, 0.4), (0.0, 0.1, 0.52), (-0.42, -0.2, 0.34), (0.44, -0.22, 0.34)]  # (fills ~90% of the cell)


def puff3():
    cell = 128
    A = np.zeros((512, 512), np.float32)
    G = np.ones_like(A)
    for i in range(16):
        x, y = grid(cell * SS)
        s = (0.85 + 0.15 * min(1, i / 6)) if i <= 7 else 1 - 0.45 * (i - 7) / 8
        a = np.zeros_like(x)
        for bx, by, br in BLOBS:
            d = np.hypot(x - bx * s, y - by * s) / (br * s)
            a = np.maximum(a, np.clip((1 - d) * 6, 0, 1))
        shade = np.clip(0.97 - np.clip(y * s - 0.05, 0, 1) * 0.5, 0.5, 1)
        r_, c_ = divmod(i, 4)
        A[r_ * cell:(r_ + 1) * cell, c_ * cell:(c_ + 1) * cell] = down(a, cell)
        G[r_ * cell:(r_ + 1) * cell, c_ * cell:(c_ + 1) * cell] = down(shade, cell)
    out = np.zeros((512, 512, 4), np.uint8)
    out[..., :3] = (np.clip(G, 0, 1) * 255).astype(np.uint8)[..., None]
    out[..., 3] = (np.clip(A, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, 'vfx_puff3_4x4.png'))
    print('vfx_puff3_4x4 512 512')


# 5. cracks v4 (1024 px): arms 4 px wide at the centre tapering to 1 px, a soft dark crater (r 0.08, alpha 0.6) and 7 short
# wedge cracks round it
def crack4(n=1024):
    x, y = grid(n)
    rr = np.random.default_rng(21)
    a = np.zeros_like(x)
    px = 2.0 / n

    def stamp(x0, y0, x1, y1, w):
        nonlocal a
        lo_x = max(int((min(x0, x1) + 1) / 2 * n) - 6, 0); hi_x = min(int((max(x0, x1) + 1) / 2 * n) + 6, n)
        lo_y = max(int((min(y0, y1) + 1) / 2 * n) - 6, 0); hi_y = min(int((max(y0, y1) + 1) / 2 * n) + 6, n)
        if hi_x > lo_x and hi_y > lo_y:
            a[lo_y:hi_y, lo_x:hi_x] = np.maximum(a[lo_y:hi_y, lo_x:hi_x], seg(x[lo_y:hi_y, lo_x:hi_x], y[lo_y:hi_y, lo_x:hi_x], x0, y0, x1, y1, w, soft=px))

    def walk(x0, y0, ang, length, w0, depth):
        steps = int(length / 0.03)
        for s in range(steps):
            ang += rr.normal(0, 0.15)
            x1, y1 = x0 + math.cos(ang) * 0.03, y0 + math.sin(ang) * 0.03
            stamp(x0, y0, x1, y1, max(0.5, w0 * (1 - s / steps) + 0.5 * s / steps) * px)
            if depth < 2 and rr.random() < 0.08:
                walk(x1, y1, ang + rr.choice([-1, 1]) * rr.uniform(0.4, 1.0), length * 0.4, w0 * 0.6, depth + 1)
            x0, y0 = x1, y1
    for k in range(10):
        walk(0.0, 0.0, k / 10 * 2 * math.pi + rr.uniform(-0.25, 0.25), rr.uniform(0.6, 0.92), 2.0, 0)
    for k in range(7):  # short wedges round the crater
        ang = k / 7 * 2 * math.pi + 0.4
        stamp(0.06 * math.cos(ang), 0.06 * math.sin(ang), 0.21 * math.cos(ang), 0.21 * math.sin(ang), 3 * px)
    crater = 0.6 * np.clip(1 - np.hypot(x, y) / 0.08, 0, 1) ** 0.7
    save_a(np.maximum(a, crater), 'vfx_crack4')


# 6. ink blob: a jagged hard blob (core r 0.3) with one long tail along u (to the right) and 4 short spikes
def inkblob(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    edge = 0.3 * (1 + 0.12 * np.sin(ang * 7 + 0.5) + 0.06 * np.sin(ang * 13))
    a = (r < edge).astype(np.float32)
    a = np.maximum(a, seg(x, y, 0.2, 0, 0.98, 0.03, 0.16, 0.004))  # the long tail along u
    for sa, L in ((1.7, 0.55), (2.6, 0.5), (3.7, 0.52), (4.6, 0.48)):
        a = np.maximum(a, seg(x, y, 0.2 * math.cos(sa), 0.2 * math.sin(sa), L * math.cos(sa), L * math.sin(sa), 0.09, 0.004))
    save_a(down(a, n), 'vfx_inkblob')


sheet(hit6, 'vfx_hitstar6_4x4')
sheet(gburst5, 'vfx_gburst5_4x4')
sheet(gring4, 'vfx_gring4_4x4')
puff3()
crack4()
inkblob()
