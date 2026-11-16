# The soft smoke flipbook for Roblox, from the web game's own Blender-baked sheet (public/sprites/puffsoft.png, made by
# tools/sprites/smoke_sim.py: a Mantaflow smoke burst, 36 frames packed 6x6, R = shading, A = thickness).
# Roblox flipbooks are 2x2 / 4x4 / 8x8 only and do not blend between frames, so this makes an 8x8 sheet (64 frames,
# 128 px) whose in-between frames are cross-fades of the baked ones, the way the web's "soft" mode melts frame into
# frame (flipbook.js). Colour: the web's lit shading, grey = 0.42 + 0.66 * R; alpha = A. The particle's Color tints it.
#
#   py tools/roblox/vfx/smoke_sheet.py <out.png> [<puffsoft.png>]
import sys, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else os.path.join(HERE, '..', '..', '..', 'public', 'sprites', 'puffsoft.png')
out = sys.argv[1]
# --grid N --cell C: a smaller sheet for short-lived puffs (a one-shot flipbook plays at most 30 frames a second, so a
# 0.7 s puff needs 16 frames, not 64)
N1 = int(sys.argv[sys.argv.index('--grid') + 1]) if '--grid' in sys.argv else 8
C1 = int(sys.argv[sys.argv.index('--cell') + 1]) if '--cell' in sys.argv else 128
if '--grid' in sys.argv or '--cell' in sys.argv: src = os.path.join(HERE, '..', '..', '..', 'public', 'sprites', 'puffsoft.png')
a = np.asarray(Image.open(src).convert('RGBA')).astype(np.float32) / 255
N0, C0 = 6, a.shape[0] // 6
frames = [a[(k // N0) * C0:(k // N0 + 1) * C0, (k % N0) * C0:(k % N0 + 1) * C0] for k in range(N0 * N0)]
sheet = np.zeros((N1 * C1, N1 * C1, 4), np.float32)
for k in range(N1 * N1):
    f = k / (N1 * N1 - 1) * (N0 * N0 - 1)
    i = int(f); u = f - i
    fa, fb = frames[i], frames[min(i + 1, N0 * N0 - 1)]
    # premultiplied mix, so a frame fading in doesn't bring a grey fringe
    pa = np.concatenate([fa[..., :1] * fa[..., 3:], fa[..., 3:]], -1); pb = np.concatenate([fb[..., :1] * fb[..., 3:], fb[..., 3:]], -1)
    p = pa * (1 - u) + pb * u
    alpha = p[..., 1]
    r = np.where(alpha > 1e-4, p[..., 0] / np.maximum(alpha, 1e-4), 0)
    grey = np.clip(0.42 + 0.66 * r, 0, 1)
    cell = np.stack([grey, grey, grey, alpha], -1)
    im = Image.fromarray((cell * 255 + 0.5).astype(np.uint8), 'RGBA').resize((C1, C1), Image.LANCZOS)
    sheet[(k // N1) * C1:(k // N1 + 1) * C1, (k % N1) * C1:(k % N1 + 1) * C1] = np.asarray(im).astype(np.float32) / 255
Image.fromarray((sheet * 255 + 0.5).astype(np.uint8), 'RGBA').save(out)
print('smoke sheet', out, sheet.shape, 'cover %.3f' % float((sheet[..., 3] > 0.05).mean()))
