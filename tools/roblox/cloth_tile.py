# A seamless cloth picture for a gadget skin's fabric (the Bento Box's furoshiki, 18 Nov 2026): indigo crepe with a
# quiet wave-scale print (seigaiha: rows of fans of rings), 512 px = one wrap tile (gun_uvs.TILE_M / item UV_SCALE, about
# 18 cm of cloth), so it sits on the same UVs a wrap picture uses. Writes <out>/cloth_tile_color.png (sRGB) and
# cloth_tile_normal.png (tangent space, OpenGL +Y). Plain Python 3 with numpy + Pillow.
#
#   python tools/roblox/cloth_tile.py <out_dir> [--base 465a7c] [--line 56698c] [--fans 8]
#
# Upload rules: nothing here is text, a code or a mosaic; the print is low contrast. Look at both files anyway.
import argparse, os, math
import numpy as np
from PIL import Image

N = 512


def hexrgb(h): return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def crepe(seed=7):
    """a periodic crinkle height field (sums of whole-tile waves, so it tiles)"""
    rng = np.random.default_rng(seed)
    v, u = np.mgrid[0:N, 0:N].astype(np.float32)
    v = (N - 1) - v   # (rows run down the file; v runs up the tile)
    h = np.zeros((N, N), np.float32)
    for _ in range(70):
        kx, ky = rng.integers(-20, 21, 2)
        if abs(kx) + abs(ky) < 7: continue
        f = math.hypot(kx, ky)
        h += np.sin(2 * math.pi * (kx * u + ky * v) / N + rng.uniform(0, 2 * math.pi)) / f
    h /= np.abs(h).max()
    return u, v, h


def seigaiha(u, v, fans):
    """distance to the nearest ring line of the wave-scale print, in pixels"""
    R = N / fans / 2
    best_d = np.full(u.shape, 1e9, np.float32)
    seen = np.zeros(u.shape, bool)
    j0 = np.floor(v / (R / 2)).astype(np.int64)
    for dj in range(-2, 3):          # (the lowest circle that holds a point is the fan on top there)
        j = j0 + dj
        ox = (j % 2) * R
        du = np.mod(u - ox + R, 2 * R) - R
        dv = v - j * (R / 2)
        r = np.hypot(du, dv)
        hold = (r < R) & ~seen
        ring = np.min(np.stack([np.abs(r - R * k) for k in (0.32, 0.56, 0.79, 1.0)]), axis=0)
        best_d = np.where(hold, ring, best_d)
        seen |= hold
    return best_d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--base', default='465a7c')
    ap.add_argument('--line', default='5b6f94')
    ap.add_argument('--fans', type=int, default=8)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    u, v, h = crepe()
    d = seigaiha(u, v, a.fans)
    line = np.clip(1.2 - d / 1.1, 0, 1)[..., None]
    base, ln = hexrgb(a.base), hexrgb(a.line)
    col = base * (1 - line) + ln * line
    col *= (1 + 0.035 * h)[..., None]
    Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).save(os.path.join(a.out, 'cloth_tile_color.png'))
    # normals from the crinkle (periodic differences, so the edges still meet)
    s = 0.7
    dhu = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) / 2
    dhv = -(np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) / 2   # (v runs up: the row above is +v)
    n = np.stack([-dhu * s, -dhv * s, np.ones_like(h)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    Image.fromarray(np.clip((n * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)).save(os.path.join(a.out, 'cloth_tile_normal.png'))
    print('wrote', os.path.join(a.out, 'cloth_tile_color.png'), os.path.join(a.out, 'cloth_tile_normal.png'))


if __name__ == '__main__':
    main()
