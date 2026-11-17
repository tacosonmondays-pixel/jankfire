# A UI fire flipbook (17 Nov 2026, the owner on the RANKED switch: "can the flames be actual flames?"): 64 frames (8x8,
# 128 px cells) of a ragged row of fire rising from a cell's bottom edge, looping seamlessly. Drawn from maths (numpy +
# Pillow; no image generator, nothing downloaded): turbulent noise scrolling up through a flame-shaped falloff, the
# classic shader fire. Every noise field is periodic and scrolls a whole number of periods over the 64 frames, so frame
# 64 runs straight into frame 1. Coloured as drawn (UI images have no additive blend): deep red at the ragged edges,
# orange, amber, a pale core only where it's hottest; alpha follows the heat, so the thin tips are see-through. The
# sides fade (alpha only, the colour kept) over 14 % of the cell so neighbouring labels overlap without a seam; the top rows and the cell's bottom 2 px are
# clear (no bleed between cells when a label shows one cell).
#   py -E -P tools/roblox/vfx/fire_sheet.py <out.png> [cell 128] [seed 3]
import sys
import numpy as np
from PIL import Image

out = sys.argv[1]
C = int(sys.argv[2]) if len(sys.argv) > 2 else 128
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 3
G, N = 8, 64
rng = np.random.default_rng(seed)


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def field(h, w, beta, sx=1.0, sy=1.0):
    # pink noise periodic in both directions (h rows x w cols), 0..1 by its 1st-99th percentile; sx/sy stretch features
    ky = np.fft.fftfreq(h) * h
    kx = np.fft.fftfreq(w) * w
    KY, KX = np.meshgrid(ky, kx, indexing='ij')
    K = np.sqrt((KX / sx) ** 2 + (KY / sy) ** 2 + 1.0)
    spec = (rng.normal(size=(h, w)) + 1j * rng.normal(size=(h, w))) / K ** beta
    n = np.real(np.fft.ifft2(spec))
    lo, hi = np.percentile(n, 1), np.percentile(n, 99)
    return np.clip((n - lo) / (hi - lo), 0, 1)


def sample(F, y, x):
    # bilinear, wrapping (F periodic)
    h, w = F.shape
    y0 = np.floor(y).astype(int); x0 = np.floor(x).astype(int)
    fy = y - y0; fx = x - x0
    y0 %= h; x0 %= w; y1 = (y0 + 1) % h; x1 = (x0 + 1) % w
    return (F[y0, x0] * (1 - fx) + F[y0, x1] * fx) * (1 - fy) + (F[y1, x0] * (1 - fx) + F[y1, x1] * fx) * fy


# noise in "cell pixels": A big licks (period 2 cells tall), B fine flicker (period 1 cell), Wn the sway
A = field(2 * C, C, 1.5, sx=1.0, sy=0.45)     # (sy < 1: features taller than wide: tongues)
B = field(C, C, 1.2, sx=1.0, sy=0.7)
Wn = field(2 * C, C, 2.2)
yy, xx = np.mgrid[0:C, 0:C].astype(np.float64)
u = xx / (C - 1)                                # 0..1 across
v = 1 - yy / (C - 1)                            # 0 at the bottom .. 1 at the top
sheet = np.zeros((G * C, G * C, 4))
ramp_t = np.array([0.0, 0.2, 0.45, 0.7, 0.88, 1.0])
ramp_c = np.array([(120, 16, 4), (204, 46, 10), (246, 108, 24), (255, 160, 42), (255, 208, 110), (255, 240, 190)], dtype=np.float64)
for i in range(N):
    p = i / N                                   # 0..1 over the loop
    # scrolled up: A one period (2 cells) per loop, B three periods, the sway one period
    sw = (sample(Wn, yy + p * 2 * C, xx) - 0.5) * 0.16 * C * v
    a = sample(A, yy + p * 2 * C, xx + sw)
    b = sample(B, yy + p * 3 * C, xx + sw * 0.5)
    n = 0.68 * a + 0.32 * b
    base = (1 - v) ** 0.9                       # hot at the bottom, cooling upward
    f = base * 1.12 - n * (0.62 + 0.6 * v)
    heat = smooth(0.0, 0.75, f) ** 1.15
    heat *= 1 - smooth(0.86, 0.97, v)                           # nothing at the very top
    heat[-2:, :] = 0                                            # (the bottom 2 px clear: no bleed into the next row)
    col = np.stack([np.interp(heat, ramp_t, ramp_c[:, k]) for k in range(3)], -1)
    alpha = smooth(0.03, 0.4, heat) * smooth(0.0, 0.14, u) * smooth(0.0, 0.14, 1 - u)   # (the sides fade in alpha only: overlapping labels, no seam)
    gy, gx = divmod(i, G)
    sheet[gy * C:(gy + 1) * C, gx * C:(gx + 1) * C, :3] = col
    sheet[gy * C:(gy + 1) * C, gx * C:(gx + 1) * C, 3] = alpha * 255
Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8), 'RGBA').save(out)
print('wrote', out, G * C, 'px,', N, 'frames of', C, 'px; mean alpha %.3f' % (sheet[..., 3].mean() / 255))
