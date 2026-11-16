# A thick, lumpy smoke puff for the Smoke Bomb's cloud (critic round 2: the web's wispy puffsoft frames read as thin
# steam; the web's cloud is a solid white mass): drawn from maths (numpy + Pillow; no image generator).
# Each frame: a cluster of soft round lumps (fixed seeds, so frames follow on), swelling out over the life, lit from
# above (brighter top, greyer underside), its edge lumpy; it thins away over the last third. Alpha is zero at every
# cell's border. RGB = the shading everywhere (normal blend; the particle's Color tints it), so no bleed is needed.
#   py tools/roblox/vfx/cotton_sheet.py <out.png> [grid 8] [cell 128]
import sys
import numpy as np
from PIL import Image

out = sys.argv[1]
G = int(sys.argv[2]) if len(sys.argv) > 2 else 8
C = int(sys.argv[3]) if len(sys.argv) > 3 else 128
rng = np.random.default_rng(11)
y, x = np.mgrid[0:C, 0:C].astype(np.float64)
u = (x - (C - 1) / 2) / (C / 2)
v = (y - (C - 1) / 2) / (C / 2)  # (down is +v)
r = np.hypot(u, v)

# the lumps: offsets (in units of the puff's radius) and sizes; a big middle and a ring of smaller ones, a few on top
lumps = [(0.0, 0.0, 0.62)]
for k in range(7):
    a = k / 7 * 2 * np.pi + rng.uniform(-0.3, 0.3)
    d = rng.uniform(0.38, 0.55)
    lumps.append((np.cos(a) * d, np.sin(a) * d * 0.85, rng.uniform(0.3, 0.42)))
for k in range(5):
    a = rng.uniform(0, 2 * np.pi); d = rng.uniform(0.15, 0.5)
    lumps.append((np.cos(a) * d, np.sin(a) * d - 0.12, rng.uniform(0.2, 0.3)))
# fine noise for the lumpy edge (a few octaves of smooth random waves, fixed)
def waves(n, scale):
    f = np.zeros_like(r)
    for _ in range(n):
        kx, ky = rng.normal(0, scale, 2); ph = rng.uniform(0, 2 * np.pi)
        f += np.sin(kx * u + ky * v + ph)
    return f / np.sqrt(n)
noise = 0.6 * waves(12, 6) + 0.4 * waves(16, 14)

sheet = np.zeros((G * C, G * C, 4))
N = G * G
for i in range(N):
    t = i / (N - 1)
    R = 0.58 + 0.3 * np.sqrt(t)              # the lump cluster's radius in the cell (it swells; soft edges reach ~0.95)
    D = np.zeros_like(r)
    for (ox, oy, s) in lumps:
        d2 = ((u - ox * R) ** 2 + (v - oy * R) ** 2) / (s * R) ** 2
        D += np.exp(-d2 * 0.75)
    D += 0.38 * noise * np.clip(D, 0, 1)     # lumps on the surface
    thin = 0.22 + 0.75 * np.clip((t - 0.5) / 0.5, 0, 1) ** 1.4   # the threshold rises: it thins out over the last half
    a = np.clip((D - thin) / 0.45, 0, 1)        # (round 3: a defined bumpy edge, not a long fringe)
    a = a * a * (3 - 2 * a)
    a *= 1 - np.clip((t - 0.8) / 0.2, 0, 1) ** 1.5   # gone by the last frame
    a *= np.clip((0.98 - r) / 0.1, 0, 1)       # zero at the cell's border
    # light from above and a little left: the density's slope as a normal
    gy, gx = np.gradient(D)
    nz = 0.35
    nrm = np.sqrt(gx ** 2 + gy ** 2 + nz ** 2)
    lit = np.clip((-gx * -0.35 + -gy * -0.85 + nz * 0.4) / nrm, -1, 1)
    grey = np.clip(0.82 + 0.2 * lit - 0.12 * np.clip(v, 0, 1), 0.55, 1.0)
    cell = np.dstack([grey * 255, grey * 255, grey * 255, a * 255])
    gx0, gy0 = (i % G) * C, (i // G) * C
    sheet[gy0:gy0 + C, gx0:gx0 + C] = cell
Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8), 'RGBA').save(out)
print('wrote', out, G, 'x', G, C, 'px cells')
