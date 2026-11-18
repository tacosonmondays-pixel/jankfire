# The legendary gadget skins' paper bits (18 Nov 2026, main's ask for the Paper Lantern frag and the Origami Duck): four
# small folded-paper scraps on one 2x2 sheet, drawn from maths (numpy + Pillow; no text, no marks). Each scrap has two
# faces on either side of its fold, one a shade darker, and a thin darker rim so it reads small; RGB is grey shading,
# so a particle's Color tints it (cream, red, gold).
#   vfx_paper.png  256 x 256: a folded triangle, a rhombus folded on its long diagonal, a square with a folded-down
#                  corner, a narrow twisted strip
#   py -E -P tools/roblox/vfx/paper_sheet.py <out dir>
import sys, os
import numpy as np
from PIL import Image

out = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(out, exist_ok=True)

N, SS = 256, 4            # the sheet, the supersampling
C = N // 2                # one cell
rgb = np.zeros((N * SS, N * SS)); alpha = np.zeros((N * SS, N * SS))
yy, xx = np.mgrid[0:N * SS, 0:N * SS].astype(np.float64) / SS + 0.5 / SS


def inside(poly, x, y):
    # even-odd fill of a convex or concave polygon (cell pixels)
    res = np.zeros(x.shape, bool)
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % n]
        cond = ((y0 > y) != (y1 > y))
        xi = (x1 - x0) * (y - y0) / ((y1 - y0) + 1e-12) + x0
        res ^= cond & (x < xi)
    return res


def edge_dist(poly, x, y):
    d = np.full(x.shape, 1e9)
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]; bx, by = poly[(i + 1) % n]
        vx, vy = bx - ax, by - ay
        t = np.clip(((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        d = np.minimum(d, np.hypot(x - (ax + t * vx), y - (ay + t * vy)))
    return d


def scrap(cell, faces):
    # faces: [(polygon in cell units 0..1, shade 0..1)], painted in order; a 2.5 px darker rim round each face
    cx, cy = (cell % 2) * C, (cell // 2) * C
    x = xx - cx; y = yy - cy
    m = (x >= 0) & (x < C) & (y >= 0) & (y < C)
    for poly, shade in faces:
        P = [(px * C, py * C) for px, py in poly]
        f = inside(P, x, y) & m
        rim = edge_dist(P, x, y) < 2.5
        rgb[f] = np.where(rim[f], shade * 0.68, shade)
        alpha[f] = 1


# 1: a triangle folded down the middle
scrap(0, [([(0.18, 0.78), (0.5, 0.2), (0.5, 0.82)], 1.0), ([(0.5, 0.2), (0.84, 0.74), (0.5, 0.82)], 0.82)])
# 2: a rhombus folded on its long diagonal
scrap(1, [([(0.14, 0.5), (0.52, 0.22), (0.88, 0.48)], 1.0), ([(0.14, 0.5), (0.88, 0.48), (0.48, 0.8)], 0.8)])
# 3: a square with one corner folded down
scrap(2, [([(0.2, 0.22), (0.8, 0.22), (0.8, 0.56), (0.54, 0.8), (0.2, 0.8)], 1.0),
          ([(0.8, 0.56), (0.54, 0.8), (0.58, 0.58)], 0.78)])
# 4: a narrow strip with a twist in it
scrap(3, [([(0.12, 0.62), (0.46, 0.4), (0.52, 0.5), (0.18, 0.72)], 1.0),
          ([(0.46, 0.4), (0.86, 0.3), (0.88, 0.4), (0.52, 0.5)], 0.8)])

# down to the sheet (box filter)
def down(a):
    return a.reshape(N, SS, N, SS).mean(axis=(1, 3))
A = down(alpha)
G = np.where(A > 0, down(rgb * alpha) / np.maximum(A, 1e-6), 1.0)
img = np.dstack([G * 255, G * 255, G * 255, A * 255]).clip(0, 255).astype(np.uint8)
Image.fromarray(img, 'RGBA').save(os.path.join(out, 'vfx_paper.png'))
print('wrote vfx_paper.png', N, 'x', N, 'cover %.3f' % A.mean())
