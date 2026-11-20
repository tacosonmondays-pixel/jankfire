# VFX practice round 6 (20 Nov 2026, the last round): the round-5 critic's texture fixes for the guard break, the ground
# impact and the explosion.  py draw_r6.py <out dir>
import sys, os, math
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draw_r4  # noqa: E402  (its drawing runs only as a script)
from draw_r4 import grid, down, seg, arcs  # noqa: E402

OUT = sys.argv[1]
SS = 2
draw_r4.OUT = OUT
save_a, sheet = draw_r4.save_a, draw_r4.sheet
LONG = (0.25, 1.85, 3.35, 4.85)


# 1. guard-break burst v6: frames 0-1 the squat star with a ragged body (+-10%), 2-3 side spikes on each long arm, thin short
# arms; 2-5 three thicker rings (0.045) with the long arms surviving as 4 blade clusters over them; 6-15 empty
def gburst6(i, x, y):
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    if i <= 1:
        k = 1 + 0.06 * i
        body = 0.32 * k * (1 + 0.1 * np.sin(ang * 9 + 1.3) * np.cos(ang * 4))
        a = (r < body).astype(np.float32)
        for la in LONG:
            a = np.maximum(a, seg(x, y, 0, 0, 0.6 * k * math.cos(la), 0.6 * k * math.sin(la), 0.3, 0.01))
            for side, t in ((1, 0.45), (-1, 0.62), (1, 0.75)):  # small side spikes along the arm
                bx, by = t * 0.6 * k * math.cos(la), t * 0.6 * k * math.sin(la)
                sa = la + side * 0.9
                a = np.maximum(a, seg(x, y, bx, by, bx + 0.12 * math.cos(sa), by + 0.12 * math.sin(sa), 0.035, 0.003))
        for sa in (1.05, 2.6, 4.1, 5.6):
            a = np.maximum(a, seg(x, y, 0, 0, 0.35 * k * math.cos(sa), 0.35 * k * math.sin(sa), 0.08, 0.004))
        return a
    if i <= 5:
        k = (i - 2) / 3
        a = np.maximum(np.maximum(arcs(x, y, 0.3 + 0.08 * k, 0.045, 3, 12, phase=0.4), arcs(x, y, 0.5 + 0.1 * k, 0.045, 4, 14, phase=1.1)),
                       arcs(x, y, 0.65 + 0.12 * k, 0.035, 3, 12, phase=2.0))
        rr = np.random.default_rng(41)
        for la in LONG:
            for b in range(3):
                ba = la + rr.uniform(-0.18, 0.18)
                L = rr.uniform(0.3, 0.45)
                r0 = 0.35 + 0.1 * k + rr.uniform(0, 0.1)
                a = np.maximum(a, seg(x, y, r0 * math.cos(ba), r0 * math.sin(ba), min(0.95, r0 + L) * math.cos(ba), min(0.95, r0 + L) * math.sin(ba), 0.05, 0.004))
        return a
    return np.zeros_like(x)


# 2. guard-break ring v5: the hard thin ring, two 35-degree inner arcs hugging it at 0.93 R, 8 uneven streaks (0.08-0.3)
_sr = np.random.default_rng(17)
STREAKS = sorted([(_sr.uniform(0, 2 * math.pi), _sr.uniform(0.08, 0.3)) for _ in range(8)])


def gring5(i, x, y):
    t = i / 15
    r = np.hypot(x, y)
    ang = (np.arctan2(y, x)) % (2 * math.pi)
    R = 0.15 + 0.72 * (1 - (1 - t) ** 2.5)
    a = (np.abs(r - R) < 0.02).astype(np.float32)
    for a0 in (0.6, 3.5):
        on = (ang > a0) & (ang < a0 + math.radians(35))
        a = np.maximum(a, ((np.abs(r - 0.93 * R) < 0.012) & on).astype(np.float32) * 0.8)
    if 3 <= i <= 9:
        k = (i - 3) / 6
        for sa, L in STREAKS:
            r0 = R + 0.05
            a = np.maximum(a, seg(x, y, r0 * math.cos(sa), r0 * math.sin(sa), (r0 + L) * math.cos(sa), (r0 + L) * math.sin(sa), 0.018 * (1 - k), 0.003) * (1 - k * 0.5))
    return a * (1 - t ** 4)


# 3. puff v4: the same full cumulus with softer rims (edge ramp 2.5 instead of 6), shrinking late
BLOBS = [(-0.5, 0.12, 0.42), (0.0, -0.3, 0.48), (0.5, 0.08, 0.42), (-0.24, 0.38, 0.4), (0.26, 0.4, 0.4), (0.0, 0.1, 0.52),
         (-0.42, -0.2, 0.34), (0.44, -0.22, 0.34)]


def puff4():
    cell = 128
    A = np.zeros((512, 512), np.float32)
    G = np.ones_like(A)
    for i in range(16):
        x, y = grid(cell * SS)
        s = (0.85 + 0.15 * min(1, i / 6)) if i <= 7 else 1 - 0.45 * (i - 7) / 8
        a = np.zeros_like(x)
        for bx, by, br in BLOBS:
            dd = np.hypot(x - bx * s, y - by * s) / (br * s)
            a = np.maximum(a, np.clip((1 - dd) * 2.5, 0, 1))
        shade = np.clip(0.97 - np.clip(y * s - 0.05, 0, 1) * 0.5, 0.5, 1)
        r_, c_ = divmod(i, 4)
        A[r_ * cell:(r_ + 1) * cell, c_ * cell:(c_ + 1) * cell] = down(a, cell)
        G[r_ * cell:(r_ + 1) * cell, c_ * cell:(c_ + 1) * cell] = down(shade, cell)
    out = np.zeros((512, 512, 4), np.uint8)
    out[..., :3] = (np.clip(G, 0, 1) * 255).astype(np.uint8)[..., None]
    out[..., 3] = (np.clip(A, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(out, 'RGBA').save(os.path.join(OUT, 'vfx_puff4_4x4.png'))
    print('vfx_puff4_4x4 512 512')


# 4. cracks v5 (1024 px): smoother (turn noise 0.08) and 1.5x thicker, sharper forks, the crater and wedges as v4
def crack5(n=1024):
    x, y = grid(n)
    rr = np.random.default_rng(21)
    a = np.zeros_like(x)
    px = 2.0 / n

    def stamp(x0, y0, x1, y1, w):
        nonlocal a
        lo_x = max(int((min(x0, x1) + 1) / 2 * n) - 8, 0); hi_x = min(int((max(x0, x1) + 1) / 2 * n) + 8, n)
        lo_y = max(int((min(y0, y1) + 1) / 2 * n) - 8, 0); hi_y = min(int((max(y0, y1) + 1) / 2 * n) + 8, n)
        if hi_x > lo_x and hi_y > lo_y:
            a[lo_y:hi_y, lo_x:hi_x] = np.maximum(a[lo_y:hi_y, lo_x:hi_x], seg(x[lo_y:hi_y, lo_x:hi_x], y[lo_y:hi_y, lo_x:hi_x], x0, y0, x1, y1, w, soft=px))

    def walk(x0, y0, ang, length, w0, depth):
        steps = int(length / 0.03)
        for s in range(steps):
            ang += rr.normal(0, 0.08)
            x1, y1 = x0 + math.cos(ang) * 0.03, y0 + math.sin(ang) * 0.03
            stamp(x0, y0, x1, y1, max(0.75, (w0 * (1 - s / steps) + 0.5 * s / steps) * 1.5) * px)
            if depth < 2 and rr.random() < 0.08:
                walk(x1, y1, ang + rr.choice([-1, 1]) * rr.uniform(0.6, 1.1), length * 0.4, w0 * 0.6, depth + 1)
            x0, y0 = x1, y1
    for k in range(10):
        walk(0.0, 0.0, k / 10 * 2 * math.pi + rr.uniform(-0.25, 0.25), rr.uniform(0.6, 0.92), 2.0, 0)
    for k in range(7):
        ang = k / 7 * 2 * math.pi + 0.4
        stamp(0.06 * math.cos(ang), 0.06 * math.sin(ang), 0.21 * math.cos(ang), 0.21 * math.sin(ang), 4.5 * px)
    crater = 0.6 * np.clip(1 - np.hypot(x, y) / 0.08, 0, 1) ** 0.7
    save_a(np.maximum(a, crater), 'vfx_crack5')


# 5. ink blob v2: a smaller core (0.2), the tail along u and the side spikes 1.3x longer: mostly daggers
def inkblob2(n=256):
    x, y = grid(n * SS)
    r = np.hypot(x, y)
    ang = np.arctan2(y, x)
    edge = 0.2 * (1 + 0.12 * np.sin(ang * 7 + 0.5) + 0.06 * np.sin(ang * 13))
    a = (r < edge).astype(np.float32)
    a = np.maximum(a, seg(x, y, 0.12, 0, 0.98, 0.03, 0.13, 0.004))
    for sa, L in ((1.7, 0.72), (2.6, 0.65), (3.7, 0.68), (4.6, 0.62)):
        a = np.maximum(a, seg(x, y, 0.12 * math.cos(sa), 0.12 * math.sin(sa), L * math.cos(sa), L * math.sin(sa), 0.08, 0.004))
    save_a(down(a, n), 'vfx_inkblob2')


if __name__ == '__main__':
    sheet(gburst6, 'vfx_gburst6_4x4')
    sheet(gring5, 'vfx_gring5_4x4')
    puff4()
    crack5()
    inkblob2()
