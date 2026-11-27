# The error number next to the critic's score (the VFX session, 26 Nov 2026; after AnyVFX's method, gokayfem, MIT:
# read on GitHub, nothing copied): the mean absolute difference per colour channel, 0-255, between a reference frame
# and our capture of the same moment, at full size and after an 8x downsample (which ignores fine texture that can
# never line up). Both are aligned first: each is cropped to the bounding box of whatever differs from its own
# background (sampled at the corners), then scaled to the same size.
#
#   py -3.12 -E -P mad.py <reference.png> <capture.png> [--size 256] [--pair out.png]
#   py -3.12 -E -P mad.py --strip <ref strip> <capture strip> <frames> [--size 256]     (two strips of N equal cells)
import sys

import numpy as np
from PIL import Image


def bbox(im, thr=18):
    a = im.astype(np.int32)
    corners = np.concatenate([a[:4, :4].reshape(-1, 3), a[:4, -4:].reshape(-1, 3), a[-4:, :4].reshape(-1, 3), a[-4:, -4:].reshape(-1, 3)])
    bg = np.median(corners, 0)
    m = np.abs(a - bg).max(-1) > thr
    if not m.any(): return None, bg
    ys, xs = np.where(m)
    return (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1), bg


def aligned(im, size):
    b, bg = bbox(im)
    h, w = im.shape[:2]
    if b is None: return np.full((size, size, 3), bg, np.float32)
    x0, y0, x1, y1 = b
    cx, cy, half = (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) / 2 + 2
    box = (int(cx - half), int(cy - half), int(cx + half), int(cy + half))
    pad = Image.new('RGB', (int(2 * half) + 1, int(2 * half) + 1), tuple(int(v) for v in bg))
    # (only the part inside the image: PIL fills a crop past the edge with black, which read as a huge error)
    ib = (max(box[0], 0), max(box[1], 0), min(box[2], w), min(box[3], h))
    pad.paste(Image.fromarray(im).crop(ib), (ib[0] - box[0], ib[1] - box[1]))
    return np.array(pad.resize((size, size), Image.LANCZOS)).astype(np.float32)


def mad(ref, cap, size=256):
    a, b = aligned(ref, size), aligned(cap, size)
    full = np.abs(a - b).mean((0, 1))
    k = size // 8
    da = a.reshape(k, 8, k, 8, 3).mean((1, 3))
    db = b.reshape(k, 8, k, 8, 3).mean((1, 3))
    low = np.abs(da - db).mean((0, 1))
    return full, low, a, b


def fmt(v): return '[%.1f, %.1f, %.1f] mean %.1f' % (v[0], v[1], v[2], v.mean())


if __name__ == '__main__':
    args = [x for x in sys.argv[1:] if not x.startswith('--')]
    size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 256
    if '--strip' in sys.argv:
        ref = np.array(Image.open(args[0]).convert('RGB'))
        cap = np.array(Image.open(args[1]).convert('RGB'))
        n = int(args[2])
        rw, cw = ref.shape[1] // n, cap.shape[1] // n
        for i in range(n):
            f, l, _, _ = mad(ref[:, i * rw:(i + 1) * rw], cap[:, i * cw:(i + 1) * cw], size)
            print('frame %d: full %s | 8x down %s' % (i, fmt(f), fmt(l)))
    else:
        ref = np.array(Image.open(args[0]).convert('RGB'))
        cap = np.array(Image.open(args[1]).convert('RGB'))
        f, l, a, b = mad(ref, cap, size)
        print('full %s | 8x down %s' % (fmt(f), fmt(l)))
        if '--pair' in sys.argv:
            Image.fromarray(np.concatenate([a, b], 1).astype(np.uint8)).save(sys.argv[sys.argv.index('--pair') + 1])
