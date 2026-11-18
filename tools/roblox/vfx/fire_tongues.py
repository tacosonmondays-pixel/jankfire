# The RANKED panel's fire, second drawing (18 Nov 2026; the owner on the Play menu's mode panel: "whya re the falmes like
# cut off or is ther blocky flames in the backl?"). fire_sheet.py's cells were each a full-width WALL of fire (a solid
# hot base across the cell, straight sides faded over only ~8 px, a fairly even top), so eight of them side by side at
# stepped heights read as rectangular blocks with flat tops. Here every cell is a small group of separate TONGUES:
# each a flame silhouette that is widest low down and tapers to a point, licked away by scrolling noise, its tip
# flickering; between the tongues the cell is clear; no full-width base (only a soft, broken ember band where the
# tongues root); the alpha fades over 28 % of the cell's width at each side, so neighbouring labels blend into one
# uneven row. 64 frames (8x8, 128 px cells), looping seamlessly (every noise scrolls whole periods; each tongue's sway
# and height breathe on whole cycles of the loop). Drawn from maths (numpy + Pillow; nothing downloaded or generated).
#   py -E -P tools/roblox/vfx/fire_tongues.py <out.png> [cell 128] [seed 5]
import sys
import numpy as np
from PIL import Image

out = sys.argv[1]
C = int(sys.argv[2]) if len(sys.argv) > 2 else 128
seed = int(sys.argv[3]) if len(sys.argv) > 3 else 5
G, N = 8, 64
rng = np.random.default_rng(seed)


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def field(h, w, beta, sx=1.0, sy=1.0):
    ky = np.fft.fftfreq(h) * h
    kx = np.fft.fftfreq(w) * w
    KY, KX = np.meshgrid(ky, kx, indexing='ij')
    K = np.sqrt((KX / sx) ** 2 + (KY / sy) ** 2 + 1.0)
    spec = (rng.normal(size=(h, w)) + 1j * rng.normal(size=(h, w))) / K ** beta
    n = np.real(np.fft.ifft2(spec))
    lo, hi = np.percentile(n, 1), np.percentile(n, 99)
    return np.clip((n - lo) / (hi - lo), 0, 1)


def sample(F, y, x):
    h, w = F.shape
    y0 = np.floor(y).astype(int); x0 = np.floor(x).astype(int)
    fy = y - y0; fx = x - x0
    y0 %= h; x0 %= w; y1 = (y0 + 1) % h; x1 = (x0 + 1) % w
    return (F[y0, x0] * (1 - fx) + F[y0, x1] * fx) * (1 - fy) + (F[y1, x0] * (1 - fx) + F[y1, x1] * fx) * fy


A = field(2 * C, C, 1.5, sx=1.0, sy=0.4)    # big licks, taller than wide
B = field(C, C, 1.2, sx=1.0, sy=0.7)        # fine flicker
Wn = field(2 * C, C, 2.2)                   # sway
yy, xx = np.mgrid[0:C, 0:C].astype(np.float64)
u = xx / (C - 1)
v = 1 - yy / (C - 1)
# the tongues: centre (0..1 across), half-width at the root, height (of the cell), phase; a big one in the middle, two
# smaller either side, slightly uneven
T = [(0.50, 0.24, 0.86, 0.0), (0.27, 0.19, 0.60, 0.35), (0.73, 0.2, 0.68, 0.7), (0.38, 0.13, 0.48, 0.2), (0.62, 0.13, 0.52, 0.85)]
ramp_t = np.array([0.0, 0.2, 0.45, 0.7, 0.88, 1.0])
ramp_c = np.array([(120, 16, 4), (204, 46, 10), (246, 108, 24), (255, 160, 42), (255, 208, 110), (255, 240, 190)], dtype=np.float64)
sheet = np.zeros((G * C, G * C, 4))
for i in range(N):
    p = i / N
    sw = (sample(Wn, yy + p * 2 * C, xx) - 0.5) * 0.12 * C * v
    a = sample(A, yy + p * 2 * C, xx + sw)
    b = sample(B, yy + p * 3 * C, xx + sw * 0.5)
    n = 0.65 * a + 0.35 * b
    env = np.zeros((C, C))
    for (cx, hw, ht, ph) in T:
        # each breathes and sways on whole loops (1 and 2 cycles), so frame 64 runs into frame 1
        h = ht * (1 + 0.12 * np.sin(2 * np.pi * (p + ph)) + 0.06 * np.sin(4 * np.pi * (p + ph * 1.7)))
        c = cx + 0.03 * np.sin(2 * np.pi * (p * 2 + ph)) * v
        t = np.clip(v / h, 0, 1)
        half = hw * (1 - t) ** 0.9 + 0.012
        d = np.abs(u - c) / half
        e = smooth(1.0, 0.0, d) * (1 - t) ** 0.5
        env = np.maximum(env, e)
    # the old drawing's fire (turbulence eating a hot base), the base now the tongues' shape instead of a wall
    f = env * 1.25 - n * (0.55 + 0.6 * v)
    heat = smooth(0.0, 0.8, f) ** 1.2 * 0.86
    ember = smooth(0.14, 0.0, v) * smooth(0.4, 0.75, sample(B, yy * 0.3 + p * C, xx)) * 0.5
    heat = np.maximum(heat, ember * smooth(0.0, 0.3, u) * smooth(0.0, 0.3, 1 - u))
    heat *= 1 - smooth(0.9, 0.98, v)
    heat[-2:, :] = 0
    col = np.stack([np.interp(heat, ramp_t, ramp_c[:, k]) for k in range(3)], -1)
    alpha = smooth(0.04, 0.42, heat) * smooth(0.0, 0.28, u) * smooth(0.0, 0.28, 1 - u)
    gy, gx = divmod(i, G)
    sheet[gy * C:(gy + 1) * C, gx * C:(gx + 1) * C, :3] = col
    sheet[gy * C:(gy + 1) * C, gx * C:(gx + 1) * C, 3] = alpha * 255
Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8), 'RGBA').save(out)
print('wrote', out, G * C, 'px,', N, 'frames of', C, 'px; mean alpha %.3f' % (sheet[..., 3].mean() / 255))
