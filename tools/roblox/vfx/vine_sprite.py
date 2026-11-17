# The angel rifle's coiling vines of light (17 Nov 2026, after the owner's reference clip: weapons wrapped in coiling
# ribbons of golden light): one sprite drawn from maths (numpy + Pillow; no text, no marks), white and additive (Fx
# tints it): RGB white everywhere, alpha the shape.
#   vfx_pulse.png  a Beam strip (256 x 64): one soft bright bead in the middle of u (the beam's length), nothing at
#                  either end so it wraps seamlessly; a tight core across v with a soft skirt. With TextureMode Wrap and
#                  TextureSpeed it runs along the vine as beads of light
#   py -E -P tools/roblox/vfx/vine_sprite.py <out dir>
import sys, os
import numpy as np
from PIL import Image

out = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(out, exist_ok=True)


def save(name, a):
    a = np.clip(a, 0, 1)
    img = np.dstack([np.full(a.shape + (3,), 255.0), a * 255]).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(os.path.join(out, name))
    print('wrote', name, img.shape[1], 'x', img.shape[0], 'peak %.2f mean %.3f' % (a.max(), a.mean()))


W, Hh = 256, 64
v, u = np.mgrid[0:Hh, 0:W].astype(np.float64)
u = u / (W - 1); v = (v - (Hh - 1) / 2) / ((Hh - 1) / 2)
# the bead: a hot middle and a longer soft glow either side, down to nothing by the ends (wraps without a seam)
along = 0.75 * np.exp(-((u - 0.5) / 0.07) ** 2) + 0.35 * np.exp(-((u - 0.5) / 0.17) ** 2)
along *= np.clip(np.minimum(u, 1 - u) / 0.08, 0, 1)
across = np.exp(-(v / 0.32) ** 2) + 0.3 * np.exp(-(v / 0.75) ** 2)
across *= np.clip((1 - np.abs(v)) / 0.08, 0, 1)
save('vfx_pulse.png', along * across)
