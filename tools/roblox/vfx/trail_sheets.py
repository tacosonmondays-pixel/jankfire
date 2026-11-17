# The high-tier skins' bullet trails (17 Nov 2026, the owner: "make sure special weapons have custom bullet trails ...
# that match the style of the gun"): two sprites drawn from maths (numpy + Pillow; no text, no marks). Both additive and
# white (Fx tints them): RGB white everywhere, alpha the shape.
#   vfx_heart.png  a small rounded heart with a soft glow round it (Wish Duck's trail)
#   vfx_dash.png   a Beam strip: one bright dash and a gap along u (the beam's length), a soft core across v; with the
#                  Beam's TextureMode Wrap it repeats into a dashed rail (Streamliner)
#   py -E -P tools/roblox/vfx/trail_sheets.py <out dir>
import sys, os
import numpy as np
from PIL import Image

out = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(out, exist_ok=True)


def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def save(name, a):
    a = np.clip(a, 0, 1)
    img = np.dstack([np.full(a.shape + (3,), 255.0), a * 255]).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(os.path.join(out, name))
    print('wrote', name, img.shape[1], 'x', img.shape[0], 'peak %.2f mean %.3f' % (a.max(), a.mean()))


# ---- the heart (256 px): the implicit heart (x^2 + y^2 - 1)^3 - x^2 y^3 <= 0, scaled into the middle, a soft edge and
# a faint glow
N = 256
y, x = np.mgrid[0:N, 0:N].astype(np.float64)
X = (x - (N - 1) / 2) / (N * 0.3)
Y = -(y - (N - 1) / 2) / (N * 0.3) + 0.12                # (image y runs down; nudged so the heart sits centred)
f = (X * X + Y * Y - 1) ** 3 - X * X * Y ** 3
gy, gx = np.gradient(f)
d = f / np.maximum(np.hypot(gx, gy) * (N * 0.3), 1e-6)    # ~ the distance to the edge (heart units): crisp everywhere
inside = 1 - smooth(-0.015, 0.015, d)
glow = 0.3 * np.exp(-np.maximum(d, 0) / 0.07) * (1 - inside)
save('vfx_heart.png', np.clip(inside + glow, 0, 1) * (1 - smooth(N * 0.44, N * 0.5, np.hypot(x - (N - 1) / 2, y - (N - 1) / 2))))

# ---- the dash (256 x 64): u along the beam, v across. the dash runs u 0.06-0.6 with rounded ends; a soft core across
W, Hh = 256, 64
v, u = np.mgrid[0:Hh, 0:W].astype(np.float64)
u = u / (W - 1); v = (v - (Hh - 1) / 2) / ((Hh - 1) / 2)
along = smooth(0.04, 0.12, u) * (1 - smooth(0.52, 0.6, u))
across = np.exp(-(v / 0.38) ** 2) + 0.25 * np.exp(-(v / 0.8) ** 2)
save('vfx_dash.png', np.clip(along * across, 0, 1))
