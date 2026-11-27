# Flipbook sheets from rendered frames, plus a preview strip (the VFX session, 26 Nov 2026).
#
#   py -E -P sheet.py pack <frames dir> <name> <layer> <grid> <out.png>     4x4 (or 8x8) sheet, each cell alpha-bled
#   py -E -P sheet.py preview <frames dir> <name> <frames> <out.jpg> [tint hex] [layers]
#       a strip of every frame composited the way Roblox will draw them: body tinted and added, core added, ink painted
#       over, on mid-grey (top row) and near-black (bottom row)
#   py -E -P sheet.py comp <frames dir> <name> <grid> <rim hex> <out.png> [edge hex]
#       ONE painted sheet of the layers, bottom to top: an optional edge (in the edge colour), the body (in the rim
#       colour), the black ink, the white core: for small effects Fx plays as a single painted particle (the bullet
#       pop), coloured as drawn
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from bleed import bleed  # noqa: E402


CELL = 256


def down(im):
    # a 2x render down to CELL px: premultiplied box filter (smooth edges, no dark or light fringe)
    h = im.shape[0]
    if h <= CELL: return im
    k = h // CELL
    f = im.astype(np.float32) / 255
    pm = np.concatenate([f[..., :3] * f[..., 3:4], f[..., 3:4]], -1)
    pm = pm.reshape(CELL, k, CELL, k, 4).mean((1, 3))
    a = pm[..., 3:4]
    rgb = np.where(a > 1e-4, pm[..., :3] / np.maximum(a, 1e-4), 0)
    return (np.concatenate([rgb, a], -1) * 255 + 0.5).clip(0, 255).astype(np.uint8)


def frames(d, name, layer):
    fs = sorted(f for f in os.listdir(d) if f.startswith('%s_%s_' % (name, layer)) and f.endswith('.png'))
    return [down(np.array(Image.open(os.path.join(d, f)).convert('RGBA'))) for f in fs]


def pack(d, name, layer, grid, out):
    fr = frames(d, name, layer)
    g = int(grid)
    h, w = fr[0].shape[:2]
    sheet = np.zeros((h * g, w * g, 4), np.uint8)
    for i, im in enumerate(fr[:g * g]):
        r, c = divmod(i, g)
        sheet[r * h:(r + 1) * h, c * w:(c + 1) * w] = bleed(im)
    Image.fromarray(sheet, 'RGBA').save(out)
    print('sheet', out, sheet.shape, len(fr), 'frames')


def over(dst, src_rgb, src_a, mode):
    a = src_a[..., None]
    if mode == 'add': return np.clip(dst + src_rgb * a, 0, 1)
    return dst * (1 - a) + src_rgb * a


def preview(d, name, n, out, tint='7fd8ff', layers='body,core,ink'):
    n = int(n)
    tc = np.array([int(tint[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
    lay = {k: frames(d, name, k) for k in layers.split(',')}
    h, w = next(iter(lay.values()))[0].shape[:2]
    rows = []
    for bg in (0.45, 0.07):
        row = []
        for f in range(n):
            img = np.full((h, w, 3), bg, np.float32)
            if 'body' in lay:
                b = lay['body'][f].astype(np.float32) / 255
                img = over(img, b[..., :3] * tc, b[..., 3] * 0.7, 'normal')  # the painted under-body (LightEmission 0)
                img = over(img, b[..., :3] * tc, b[..., 3] * (0.45 if tc[0] > tc[2] else 1.0), 'add')  # (warm tints: less added, or red clips first)
            if 'core' in lay:
                c = lay['core'][f].astype(np.float32) / 255
                img = over(img, c[..., :3], c[..., 3], 'add')
            if 'ink' in lay:
                k = lay['ink'][f].astype(np.float32) / 255
                img = over(img, k[..., :3], k[..., 3] * 0.9, 'normal')
            row.append(img)
        rows.append(np.concatenate(row, 1))
    im = (np.concatenate(rows, 0) * 255).astype(np.uint8)
    Image.fromarray(im).save(out, quality=88)
    print('preview', out, im.shape)


def comp(d, name, grid, rim, out, edge=None):
    rc = np.array([int(rim[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
    ec = np.array([int(edge[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32) if edge else None
    names = ('edge', 'body', 'ink', 'core') if edge else ('body', 'ink', 'core')
    lay = {k: frames(d, name, k) for k in names}
    g = int(grid)
    h, w = lay['body'][0].shape[:2]
    sheet = np.zeros((h * g, w * g, 4), np.uint8)
    for i in range(min(g * g, len(lay['body']))):
        rgb = np.zeros((h, w, 3), np.float32)
        a = np.zeros((h, w), np.float32)
        cols = {'edge': ec, 'body': rc, 'ink': np.zeros(3, np.float32), 'core': np.ones(3, np.float32)}
        for k in names:
            col = cols[k]
            la = lay[k][i][..., 3].astype(np.float32) / 255
            na = la + a * (1 - la)
            rgb = np.where(na[..., None] > 1e-4, (col * la[..., None] + rgb * (a * (1 - la))[..., None]) / np.maximum(na, 1e-4)[..., None], 0)
            a = na
        cell = (np.concatenate([rgb, a[..., None]], -1) * 255 + 0.5).clip(0, 255).astype(np.uint8)
        r, c = divmod(i, g)
        sheet[r * h:(r + 1) * h, c * w:(c + 1) * w] = bleed(cell)
    Image.fromarray(sheet, 'RGBA').save(out)
    print('comp', out, sheet.shape)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'pack': pack(*sys.argv[2:7])
    elif cmd == 'preview': preview(*sys.argv[2:])
    elif cmd == 'comp': comp(*sys.argv[2:8])
