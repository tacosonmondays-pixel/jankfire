# The anime SPARK streak (the VFX session, 26 Nov 2026), after the in-game critic: the old soft stadium sparks read as
# "white leaves, rice grains or feathers". One hard-edged comet, drawn VERTICALLY with its sharp head at the TOP: a
# 1 px tail at the bottom, widest at 75 %, a short sharp head; a white core down the middle 40 % of the width from 15 %
# to 85 % of the length, the rest a greyscale rim (0.6) that the particle's Color tints. 256 px, 4x supersampled.
#
# Round 3 (27 Nov 2026, the in-game critic on v1409: 6/10, "thin, pale, see-through hairs that blur into the burst,
# scratches more than hot sparks"): two PAINTED textures that AnimeFx plays as two emitters with the same motion, one
# spark at a time: the RIM (the whole shard, tinted with the weapon's colour) and the CORE (white, 50 % of the width,
# inside it, so ~2 px of colour shows each side at game size). The shard: straight, its head about twice the tail's
# width (the tail is 40 % of the widest at a fifth of the way along), widest at 78 %, a short sharp point at the head
# and a short point at the tail too (never a cut).
#
#   py -3.12 -E -P spark2d.py <out base>      writes <out base>_rim.png and <out base>_core.png (256 px)
import sys

import numpy as np
from PIL import Image, ImageDraw

out = sys.argv[1]
if out.endswith('.png'): out = out[:-4]
PX, SS = 256, 4
N = PX * SS


def shard(hw, s0, s1):
    top, bot = [], []
    for i in range(49):
        s = s0 + (s1 - s0) * i / 48  # 0 = the tail (bottom), 1 = the head (top)
        u = (s - s0) / (s1 - s0)
        prof = 0.15 + 0.85 * (u / 0.78) ** 0.9 if u < 0.78 else (1 - (u - 0.78) / 0.22) ** 0.75
        if u < 0.08: prof *= u / 0.08
        y = (1 - (0.06 + 0.88 * s)) * N
        w = hw * prof * N
        top.append((N / 2 + w, y)); bot.append((N / 2 - w * 0.9, y))
    return top + bot[::-1]


def layer(poly):
    im = Image.new('L', (N, N), 0)
    ImageDraw.Draw(im).polygon(poly, fill=255)
    return np.asarray(im, np.float32).reshape(PX, SS, PX, SS).mean((1, 3)) / 255


sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..'))
from bleed import bleed  # noqa: E402
for name, a in (('rim', layer(shard(0.075, 0.0, 1.0))), ('core', layer(shard(0.0375, 0.1, 0.93)))):
    rgba = np.zeros((PX, PX, 4), np.uint8)
    rgba[..., :3] = 255
    rgba[..., 3] = (a * 255 + 0.5).astype(np.uint8)
    Image.fromarray(bleed(rgba), 'RGBA').save('%s_%s.png' % (out, name))
    print('spark', name, 'alpha rows', int((a.max(1) > 0.1).sum()), 'max width px', int((a > 0.5).sum(1).max()))
