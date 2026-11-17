# The speed lines' wedge (17 Nov 2026, the web game's speedlines.js triangles): one white sprite, 512 x 32, its point at
# the left edge's middle and its base the whole right edge, edges anti-aliased. SpeedLines.client stretches and turns
# copies of it: the point toward where you're flying, the base off the screen's edge.
#   py -E -P tools/roblox/vfx/speedline_sprite.py <out.png>
import sys
import numpy as np
from PIL import Image

W, H = 512, 32
x = (np.arange(W) + 0.5)[None, :]
y = (np.arange(H) + 0.5)[:, None]
half = (H / 2) * (x / W)                       # the wedge's half height at x
d = half - np.abs(y - H / 2)                   # inside > 0, in pixels
a = np.clip(d + 0.5, 0, 1)                     # one-pixel edge
rgba = np.zeros((H, W, 4), np.uint8)
rgba[..., :3] = 255
rgba[..., 3] = (a * 255).astype(np.uint8)
Image.fromarray(rgba, 'RGBA').save(sys.argv[1])
print('wrote', sys.argv[1], 'mean alpha %.3f' % (a.mean()))
