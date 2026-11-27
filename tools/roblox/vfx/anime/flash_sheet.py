# The anime muzzle flash as Fx plays it (the VFX session, 26 Nov 2026): Fx shows ONE random cell of a 2x2 sheet per
# shot from a single emitter (front) or a single image (side), so the body and core layers mflash_bl.py renders are
# composited into one picture per drawing, in two copies:
#   warm  coloured as drawn (white core, a warm body, the deeper rim): TEX.mflash / TEX.mside
#   n     greyscale (the core white, the body and rim grey): TEX.mflashN / TEX.msideN, which a skin's flash colour tints
# It also measures where the side drawings' flame shows (alpha over 0.2), for Fx's SIDE_X0, SIDE_X1 and SIDE_TH.
#
#   py -3.12 -E -P flash_sheet.py <frames dir> <out dir> [warm hex, default ffb050]
import os
import sys

import numpy as np
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
warm = sys.argv[3] if len(sys.argv) > 3 else 'ffb050'
tc = np.array([int(warm[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
os.makedirs(out, exist_ok=True)


def down(im, k=2):
    f = im.astype(np.float32) / 255
    h = f.shape[0] // k
    pm = np.concatenate([f[..., :3] * f[..., 3:4], f[..., 3:4]], -1).reshape(h, k, h, k, 4).mean((1, 3))
    a = pm[..., 3:4]
    rgb = np.where(a > 1e-4, pm[..., :3] / np.maximum(a, 1e-4), 0)
    return np.concatenate([rgb, a], -1)


def cell(view, v, tinted):
    b = down(np.array(Image.open(os.path.join(src, 'mflash_%s_body_%02d.png' % (view, v)))))
    c = down(np.array(Image.open(os.path.join(src, 'mflash_%s_core_%02d.png' % (view, v)))))
    body_rgb = b[..., :3] * (tc if tinted else 1.0)
    # the core over the body (straight alpha)
    a = c[..., 3:4] + b[..., 3:4] * (1 - c[..., 3:4])
    rgb = np.where(a > 1e-4, (c[..., :3] * c[..., 3:4] + body_rgb * b[..., 3:4] * (1 - c[..., 3:4])) / np.maximum(a, 1e-4), 0)
    return np.concatenate([rgb, a], -1)


sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from bleed import bleed  # noqa: E402

for view in ('front', 'side'):
    for name, tinted in (('warm', True), ('n', False)):
        cells = [cell(view, v, tinted) for v in range(4)]
        h = cells[0].shape[0]
        sheet = np.zeros((h * 2, h * 2, 4), np.uint8)
        for i, cc in enumerate(cells):
            r, k = divmod(i, 2)
            sheet[r * h:(r + 1) * h, k * h:(k + 1) * h] = bleed((np.clip(cc, 0, 1) * 255 + 0.5).astype(np.uint8))
        fn = os.path.join(out, 'mflash_anime_%s_%s.png' % (view, name))
        Image.fromarray(sheet, 'RGBA').save(fn)
        print('sheet', fn, sheet.shape)
    if view == 'side':
        x0s, x1s, ths = [], [], []
        for v in range(4):
            a = cell(view, v, False)[..., 3]
            ys, xs = np.where(a > 0.2)
            x0s.append(xs.min() / a.shape[1]); x1s.append((xs.max() + 1) / a.shape[1])
            col = a[:, int(a.shape[1] * 0.3)]  # the thickness at the bloom
            ths.append((col > 0.2).sum() / a.shape[0])
        print('SIDE_X0 %.3f SIDE_X1 %.3f SIDE_TH %.3f (means over the four)' % (np.mean(x0s), np.mean(x1s), np.mean(ths)))
