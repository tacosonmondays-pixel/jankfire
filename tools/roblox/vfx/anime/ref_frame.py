# The reference frame for mad.py (the VFX session, 26 Nov 2026): one cell of a flipbook sheet composited the way the
# game draws it, on the background colour sampled from a Studio capture, turned by the particle's Rotation, so the
# error number compares our design with what Roblox actually shows at the same moment.
#
#   py -3.12 -E -P ref_frame.py <sheet.png> <grid> <frame> <bg hex> <rotation deg> <out.png> [--add]
#   painted (LightEmission 0, as the bullet pop and the puff) unless --add (an additive layer, as a glow)
#   a particle's positive Rotation turns it ANTICLOCKWISE on screen (seen in Studio 27 Nov), as PIL's rotate does
import sys

import numpy as np
from PIL import Image

args = [a for a in sys.argv[1:] if not a.startswith('--')]
sheet, grid, fr, bg, rot, out = args[0], int(args[1]), int(args[2]), args[3], float(args[4]), args[5]
add = '--add' in sys.argv
im = Image.open(sheet).convert('RGBA')
C = im.width // grid
r, c = divmod(fr, grid)
cell = im.crop((c * C, r * C, (c + 1) * C, (r + 1) * C)).rotate(rot, resample=Image.BICUBIC)
a = np.asarray(cell, np.float32) / 255
b = np.array([int(bg[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)
img = np.broadcast_to(b, (C, C, 3)).copy()
if add: img = np.clip(img + a[..., :3] * a[..., 3:4], 0, 1)
else: img = img * (1 - a[..., 3:4]) + a[..., :3] * a[..., 3:4]
Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(out)
print('ref', out, C)
