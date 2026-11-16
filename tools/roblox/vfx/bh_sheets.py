# The Rubber Duck's black hole: two sprites drawn from maths (numpy + Pillow; no image generator, no text or marks).
#   vfx_bhdisk.png  the accretion disk seen from above (a flat particle lying in the disk's plane): a hot thin inner
#                   edge, falling off outward, wound with spiral streaks; clear in the middle (the horizon is a mesh)
#   vfx_bhhalo.png  the lensing halo (a camera-facing particle): the thin photon ring hugging the horizon, the disk's
#                   far side bent up over the top and under the bottom (the arcs), a faint warped glow round it all
# Both are additive (LightEmission 1): RGB is the colour at full strength everywhere, alpha the brightness, so the
# soft edges never go dark (no bleed needed).
#   py tools/roblox/vfx/bh_sheets.py <out dir> [size]
import sys, os
import numpy as np
from PIL import Image

out = sys.argv[1] if len(sys.argv) > 1 else '.'
N = int(sys.argv[2]) if len(sys.argv) > 2 else 512
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(7)

y, x = np.mgrid[0:N, 0:N].astype(np.float64)
c = (N - 1) / 2
dx, dy = (x - c) / (N / 2), (y - c) / (N / 2)
r = np.hypot(dx, dy)
th = np.arctan2(dy, dx)

def smooth(e0, e1, v):
    t = np.clip((v - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def ramp(stops, v):
    # stops: [(t, (r,g,b))...] -> an (N,N,3) colour by v
    ts = np.array([s[0] for s in stops]); cols = np.array([s[1] for s in stops], dtype=np.float64)
    o = np.zeros(v.shape + (3,))
    for k in range(3): o[..., k] = np.interp(v, ts, cols[:, k])
    return o

def save(name, rgb, a):
    a = np.clip(a, 0, 1)
    img = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(os.path.join(out, name))
    print('wrote', name, N, 'px, peak alpha %.2f' % a.max())

# ---- the disk: inner edge at 0.38 of the radius (the horizon sits inside it), out to 0.97
RIN, ROUT = 0.38, 0.97
u = np.clip((r - RIN) / (ROUT - RIN), 0, 1)                 # 0 at the inner edge .. 1 at the rim
prof = (RIN / np.maximum(r, RIN)) ** 2.4                    # bright near the middle, falling off outward
edge_in = smooth(RIN - 0.012, RIN + 0.018, r)               # a crisp but smooth inner edge
edge_out = 1 - smooth(ROUT - 0.32, ROUT, r)                 # a long soft fade at the rim
# spiral streaks: bands wound along a log spiral (the gas sheared as it circles), several scales, random phases
wind = th + 2.2 * np.log(np.maximum(r, 1e-3))
st = np.zeros_like(r)
for k, amp in [(5, 0.35), (9, 0.25), (17, 0.18), (31, 0.12), (47, 0.08)]:
    st += amp * np.sin(k * wind + rng.uniform(0, 2 * np.pi)) * np.sin(max(1, k // 2) * th + rng.uniform(0, 2 * np.pi))
streak = np.clip(0.78 + st, 0.25, 1.4)
# a hot ring right at the inner edge (the brightest thing in the effect)
hot = np.exp(-((r - (RIN + 0.03)) / 0.025) ** 2)
a_disk = np.clip((prof * streak * 0.95 + hot * 0.9) * edge_in * edge_out, 0, 1)
col_disk = ramp([(0.0, (255, 250, 255)), (0.12, (238, 222, 255)), (0.4, (190, 160, 245)), (1.0, (112, 78, 190))], u)
save('vfx_bhdisk.png', col_disk, a_disk)

# ---- the halo. the horizon's edge sits at 0.40 of the radius: the photon ring just outside it, slightly warped
RH = 0.40
warp = 1 + 0.025 * np.sin(2 * th + 0.7) + 0.015 * np.sin(3 * th + 2.1) + 0.01 * np.sin(5 * th + 0.3)
rr = r / warp                                                # (the glow and arcs warp; the ring stays nearly round)
rr0 = r / (1 + 0.006 * np.sin(2 * th + 0.7))
ring = np.exp(-((rr0 - (RH + 0.022)) / 0.012) ** 2)         # the thin photon ring
# the disk's far side, bent over the top and under the bottom: a thicker arc band whose strength follows |sin|
arcs_w = np.abs(np.sin(th)) ** 2.5
arcs = np.exp(-((rr - (RH + 0.1)) / 0.05) ** 2) * arcs_w
arcs *= 1 - 0.35 * (dy > 0)                                  # (the lower arc fainter: the disk is tilted)
# the glow round it all, fading out to the sprite's edge
glow = np.exp(-np.maximum(rr - RH, 0) / 0.16) * smooth(RH - 0.005, RH + 0.03, rr) * (1 - smooth(0.75, 0.98, r))
a_halo = np.clip(ring * 1.0 + arcs * 1.0 + glow * 0.35, 0, 1) * (r < 0.995)
col_halo = ramp([(0.0, (250, 244, 255)), (0.5, (214, 196, 255)), (1.0, (140, 104, 220))],
                np.clip((rr - RH) / 0.45, 0, 1))
save('vfx_bhhalo.png', col_halo, a_halo)
