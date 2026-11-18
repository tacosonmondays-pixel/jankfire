# The Blood Cross's X (18 Nov 2026; the owner: "blood cross looks bad compared to the web version, the cross is too
# rectangular, I wanted it to be like cool and vfx-ish"). Two sprites, drawn from maths (numpy + Pillow; nothing
# downloaded): an X - a SALTIRE, never an upright plus (that is the protected Red Cross emblem) - of two long blades,
# each a sharp lens: widest where they cross, tapering to needle points, a ridge down the middle so a tint reads as a
# lit edge; and its white-hot core: two thin tapered lines with a hot point where they cross, wrapped in a soft glow.
# Both greyscale (RGB = light, alpha = coverage): the particle's or label's colour tints them (blood red, Shadow purple).
#   vfx_xblade.png  256 x 256  the blades (alpha-bled for normal blending)
#   vfx_xcore.png   256 x 256  the core lines + glow (for additive layers)
#   py -E -P tools/roblox/vfx/xblade_sheet.py <out dir>
import sys, os
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bleed import bleed

out = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(out, exist_ok=True)
N, SS = 256, 4
M = N * SS
yy, xx = np.mgrid[0:M, 0:M].astype(np.float64)
u = (xx + 0.5) / M * 2 - 1     # -1..1 across
v = 1 - (yy + 0.5) / M * 2     # -1..1 up
REACH = 0.94                   # the tips stop short of the edge


def along(ang):
    c, s = np.cos(ang), np.sin(ang)
    return (u * c + v * s) / REACH, (-u * s + v * c)


def down(a):
    return a.reshape(N, SS, N, SS).mean(axis=(1, 3))


# ---- the blades: a lens per diagonal, half-width W0 at the cross, (1 - |t|)^0.85 toward the tips
W0 = 0.12
cov = np.zeros((M, M)); lit = np.zeros((M, M))
for ang in (np.pi / 4, -np.pi / 4):
    t, a = along(ang)
    half = W0 * np.clip(1 - np.abs(t), 0, 1) ** 0.85
    inside = (np.abs(a) < half) & (np.abs(t) < 1)
    e = np.abs(a) / np.maximum(half, 1e-6)
    ridge = 1 - 0.4 * np.clip(e, 0, 1) ** 1.5      # bright down the middle, a darker rim
    cov = np.maximum(cov, inside.astype(np.float64))
    lit = np.maximum(lit, np.where(inside, ridge, 0))
A = down(cov); Lb = down(lit)
G = np.where(A > 1e-4, Lb / np.maximum(A, 1e-4), 0)
img = np.dstack([G * 255, G * 255, G * 255, A * 255]).clip(0, 255).astype(np.uint8)
Image.fromarray(bleed(img), 'RGBA').save(os.path.join(out, 'vfx_xblade.png'))

# ---- the core: thin tapered lines (half-width 0.022 at the cross) + a hot point, wrapped in a soft glow (for additive)
lum = np.zeros((M, M))
for ang in (np.pi / 4, -np.pi / 4):
    t, a = along(ang)
    half = 0.022 * np.clip(1 - np.abs(t) * 1.04, 0, 1) ** 1.2
    line = np.clip(1 - np.abs(a) / np.maximum(half, 1e-6), 0, 1) * (np.abs(t) < 0.97)
    glow = np.exp(-(a / 0.06) ** 2) * np.clip(1 - np.abs(t), 0, 1) ** 1.5 * 0.35
    lum = np.maximum(lum, np.maximum(line, glow))
r = np.hypot(u, v)
lum = np.maximum(lum, np.exp(-(r / 0.07) ** 2)) # the hot point
lum = np.maximum(lum, np.exp(-(r / 0.22) ** 2) * 0.3)
Lc = down(lum)
img2 = np.dstack([np.full_like(Lc, 255), np.full_like(Lc, 255), np.full_like(Lc, 255), Lc * 255]).clip(0, 255).astype(np.uint8)
Image.fromarray(img2, 'RGBA').save(os.path.join(out, 'vfx_xcore.png'))
print('wrote vfx_xblade.png, vfx_xcore.png', N, 'px; blade cover %.3f' % A.mean())
