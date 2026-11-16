# Alpha-bleed a sheet before upload: every transparent pixel takes the colour of the nearest visible one (Roblox filters
# textures with straight alpha, so the black Blender leaves in clear pixels creeps into soft edges as a dark fringe).
# Alpha is untouched. Each flipbook cell bleeds on its own so neighbours don't leak into each other.
#
#   py tools/roblox/vfx/bleed.py <in.png> <out.png> [cells per side, default 1]
import sys
import numpy as np
from PIL import Image


def bleed(rgba: np.ndarray, rounds: int = 64) -> np.ndarray:
    a = rgba[..., 3] > 4
    rgb = rgba[..., :3].astype(np.float32)
    filled = a.copy()
    for _ in range(rounds):
        if filled.all(): break
        acc = np.zeros_like(rgb); cnt = np.zeros(filled.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            src = np.roll(np.roll(filled, dy, 0), dx, 1)
            col = np.roll(np.roll(rgb, dy, 0), dx, 1)
            acc += col * src[..., None]; cnt += src
        grow = (~filled) & (cnt > 0)
        rgb[grow] = acc[grow] / cnt[grow][:, None]
        filled |= grow
    out = rgba.copy()
    out[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return out


def main():
    src, dst = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    im = np.array(Image.open(src).convert('RGBA'))
    h, w = im.shape[:2]
    ch, cw = h // n, w // n
    for r in range(n):
        for c in range(n):
            im[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] = bleed(im[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw])
    Image.fromarray(im, 'RGBA').save(dst)
    print('bled', dst)


if __name__ == '__main__':
    main()
