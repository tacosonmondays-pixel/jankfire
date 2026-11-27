# The BLADE SWEEP's cross-section textures (the VFX session, 27 Nov 2026). The owner: "make sure the effects follow
# the plane of the weapon and katana for example, are attached along the side of the blade". AnimeFx.sweep lays a
# chain of flat Beams through the blade's sampled path (its Mid point and tip, every frame of the swing), so the ribbon
# lies in the plane the blade swept. A Beam (seen in Studio on a test beam, 27 Nov) runs the image's ROWS along its
# length and its COLUMNS across its width, the left column on its attachments' +Y edge, so these textures are the
# ribbon's CROSS-SECTION from left to right, the same in every row: the left is the OUTER edge (the tip's path), the
# right the inner edge. The along-the-swing shape (the thinning tail, the fade) is AnimeFx's per-beam width and
# transparency.
#
# The layer breakdown, written before building (V below = across the ribbon, outer edge 0):
#   body  (white, tinted in game)  the whole band, V 0.01-0.985, its inner edge (V 0.875 on) a black ink line: black
#                                  stays black under the tint, so body and ink are one texture and can never slip apart
#   core  (white)                  the outer band, V 0.035-0.34: a thin tinted rim stays outside it on the very edge
#   Edges are 2-row ramps (no hard aliasing at 256 rows).
#
#   py -3.12 -E -P sweep2d.py <out base>     writes <out base>_body.png and <out base>_core.png (256 wide x 16 tall)
import sys

import numpy as np
from PIL import Image

out = sys.argv[1]
W, Hh = 16, 256
v = (np.arange(Hh) + 0.5) / Hh


def band(a, b, soft=2.0 / Hh):
    lo = np.clip((v - a) / soft + 0.5, 0, 1)
    hi = np.clip((b - v) / soft + 0.5, 0, 1)
    return lo * hi


body_a = band(0.01, 0.985)
ink = band(0.875, 1.02)  # (the ink runs out to the inner edge: no tinted sliver beyond it)
rgb_body = (1 - ink) * 1.0  # white where the body is, black on the ink line
core_a = band(0.035, 0.34)
for name, rgb, a in (('body', rgb_body, body_a), ('core', np.ones(Hh), core_a)):
    img = np.zeros((Hh, W, 4), np.uint8)
    img[..., :3] = (rgb[:, None, None] * 255 + 0.5).astype(np.uint8)
    img[..., 3] = (a[:, None] * 255 + 0.5).astype(np.uint8)
    Image.fromarray(img, 'RGBA').transpose(Image.Transpose.TRANSPOSE).save('%s_%s.png' % (out, name))
print('sweep textures', out, 'body rows', int((body_a > 0.5).sum()), 'core rows', int((core_a > 0.5).sum()), 'ink rows', int((ink > 0.5).sum()))
