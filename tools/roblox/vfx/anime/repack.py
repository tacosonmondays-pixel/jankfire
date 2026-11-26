# Repack a flipbook for Roblox (the VFX session, 26 Nov 2026), following game-vfx's make_flipbook steps (Patch's MIT
# skill, read in the vault: third-party/game-vfx) without its ffmpeg front end: frames in, then
#   live    keep only the frames where the effect is alive (above 2 % of the brightest frame's energy)
#   from    skip a burst's first white frames (game-vfx: start at frame 3-4)
#   ease    pick the kept frames on an eased clock (game-vfx: 0.55-0.7, so it opens in a blink and lingers)
#   crop    one square crop round everything the effect ever touches (+ a margin), the same for every frame
#   alpha   'add' sheets keep their alpha; 'black' lifts black to alpha (alpha = the brightest channel)
#   edges   every cell's border fades over 4 % (no quad ever shows a hard square)
#   pack    Roblox grids: 4x4 of 256 px or 8x8 of 128 px (an upload is at most 1024 px)
#
#   py -3.12 -E -P repack.py <in sheet (webp/png)> <in grid, e.g. 8> <out.png> <out grid 4|8> [--from N] [--ease K]
#                            [--black] [--frames N]       (N frames of the source, default all of its grid)
#   py -3.12 -E -P repack.py dir <frames dir> <prefix> <out.png> <out grid> [...]   (loose frames, e.g. Blender's)
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from bleed import bleed  # noqa: E402


def opts(argv):
    o = {'from': 0, 'ease': 1.0, 'black': False, 'frames': None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--from': o['from'] = int(argv[i + 1]); i += 2
        elif a == '--ease': o['ease'] = float(argv[i + 1]); i += 2
        elif a == '--frames': o['frames'] = int(argv[i + 1]); i += 2
        elif a == '--black': o['black'] = True; i += 1
        else: i += 1
    return o


def from_sheet(path, grid, n=None):
    im = np.array(Image.open(path).convert('RGBA'))
    h, w = im.shape[:2]
    ch, cw = h // grid, w // grid
    out = [im[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] for r in range(grid) for c in range(grid)]
    return out[:n] if n else out


def from_dir(d, prefix):
    fs = sorted(f for f in os.listdir(d) if f.startswith(prefix) and f.endswith('.png'))
    return [np.array(Image.open(os.path.join(d, f)).convert('RGBA')) for f in fs]


def repack(frames, out, grid, o):
    if o['black']:
        for f in frames: f[..., 3] = f[..., :3].max(-1)
    # live: drop dead frames at both ends
    energy = [float((f[..., :3].astype(np.float32).max(-1) * f[..., 3] / 255).sum()) for f in frames]
    peak = max(energy) or 1
    live = [i for i, e in enumerate(energy) if e > 0.02 * peak]
    a, b = max(live[0], o['from']), live[-1]
    src = frames[a:b + 1]
    n = grid * grid
    # eased pick of n frames
    idx = [min(len(src) - 1, round((k / (n - 1)) ** (1 / o['ease']) * (len(src) - 1))) if o['ease'] != 1 else round(k / (n - 1) * (len(src) - 1)) for k in range(n)]
    # one crop for all: the union of where any frame is visible, squared, plus 4 %
    acc = np.zeros(src[0].shape[:2], bool)
    for f in src: acc |= f[..., 3] > 6
    ys, xs = np.where(acc)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    half = max(ys.max() - ys.min(), xs.max() - xs.min()) / 2 * 1.04 + 2
    H, Wd = src[0].shape[:2]
    y0, x0 = int(max(0, cy - half)), int(max(0, cx - half))
    y1, x1 = int(min(H, cy + half)), int(min(Wd, cx + half))
    cell = 1024 // grid
    sheet = np.zeros((cell * grid, cell * grid, 4), np.uint8)
    ramp = np.minimum(1, np.minimum(np.arange(cell), np.arange(cell)[::-1]) / max(1, cell * 0.04))
    edge = np.minimum(ramp[:, None], ramp[None, :])
    for k, i in enumerate(idx):
        fr = Image.fromarray(src[i][y0:y1, x0:x1])
        # premultiplied resize (no fringe)
        f = np.array(fr).astype(np.float32) / 255
        pm = np.concatenate([f[..., :3] * f[..., 3:4], f[..., 3:4]], -1)
        pm = np.array(Image.fromarray((pm * 255).astype(np.uint8), 'RGBA').resize((cell, cell), Image.LANCZOS)).astype(np.float32) / 255
        al = pm[..., 3:4]
        rgb = np.where(al > 1e-4, pm[..., :3] / np.maximum(al, 1e-4), 0)
        al = al[..., 0] * edge
        c = (np.concatenate([np.clip(rgb, 0, 1), al[..., None]], -1) * 255 + 0.5).astype(np.uint8)
        r, cc = divmod(k, grid)
        sheet[r * cell:(r + 1) * cell, cc * cell:(cc + 1) * cell] = bleed(c)
    Image.fromarray(sheet, 'RGBA').save(out)
    print('repacked', out, '%dx%d of %d px' % (grid, grid, cell), 'source frames %d-%d of %d' % (a, b, len(frames)))


if __name__ == '__main__':
    if sys.argv[1] == 'dir':
        _, _, d, prefix, out, grid, *rest = sys.argv
        repack(from_dir(d, prefix), out, int(grid), opts(rest))
    else:
        _, src, g, out, grid, *rest = sys.argv
        o = opts(rest)
        repack(from_sheet(src, int(g), o['frames']), out, int(grid), o)
