# 16 different dense lumpy puffs (4x4, 256 px cells) for the frag's fireball and smoke and the smoke bomb (critic round
# 5: the fireball must be a crisp lumpy cauliflower, the web's 256 px boom sheet drawn 30 m across was a blur). Each
# particle holds one random cell (FlipbookStartRandom, framerate 0); its colour over life does the burning. Drawn from
# maths (numpy + Pillow; no image generator): a cluster of round lumps, a lumpy surface, a crisp edge (the falloff is
# under a tenth of the radius), lit from above (bright tops, grey undersides). Alpha is zero at every cell's border.
#   py tools/roblox/vfx/lumps_sheet.py <out.png> [cell 256]
import sys
import numpy as np
from PIL import Image

out = sys.argv[1]
C = int(sys.argv[2]) if len(sys.argv) > 2 else 256
G = 4
y, x = np.mgrid[0:C, 0:C].astype(np.float64)
r = np.hypot((x - (C - 1) / 2) / (C / 2), (y - (C - 1) / 2) / (C / 2))  # (the cell's own radius, for the border)
u = (x - (C - 1) / 2) / (C / 2) / 1.45  # (the lumps drawn 1.45x: the puff fills most of its cell)
v = (y - (C - 1) / 2) / (C / 2) / 1.45  # (down is +v)
sheet = np.zeros((G * C, G * C, 4))
for i in range(G * G):
    rng = np.random.default_rng(100 + i)
    lumps = [(rng.uniform(-0.08, 0.08), rng.uniform(-0.05, 0.08), rng.uniform(0.42, 0.52))]
    n = rng.integers(7, 11)
    for k in range(n):
        a = k / n * 2 * np.pi + rng.uniform(-0.35, 0.35)
        d = rng.uniform(0.3, 0.5)
        lumps.append((np.cos(a) * d, np.sin(a) * d * 0.9 - 0.04, rng.uniform(0.18, 0.3)))
    for k in range(rng.integers(3, 6)):  # small lumps on top: the cauliflower
        a = rng.uniform(np.pi * 1.1, np.pi * 1.9); d = rng.uniform(0.35, 0.6)
        lumps.append((np.cos(a) * d, np.sin(a) * d, rng.uniform(0.1, 0.17)))
    D = np.zeros_like(r)
    for (ox, oy, s) in lumps:
        D += np.exp(-((u - ox) ** 2 + (v - oy) ** 2) / s ** 2 * 1.4)
    f = np.zeros_like(r)
    for _ in range(14):
        kx, ky = rng.normal(0, 7, 2)
        f += np.sin(kx * u + ky * v + rng.uniform(0, 2 * np.pi))
    D += 0.15 * f / np.sqrt(14) * np.clip(D, 0, 1)
    a = np.clip((D - 0.3) / 0.16, 0, 1)        # a crisp edge
    a = a * a * (3 - 2 * a)
    a *= np.clip((0.97 - r) / 0.05, 0, 1)
    gy, gx = np.gradient(D)
    nz = 0.25
    nrm = np.sqrt(gx ** 2 + gy ** 2 + nz ** 2)
    lit = np.clip((gx * 0.3 + gy * 0.9 + nz * 0.35) / nrm, -1, 1)  # light from above, a little left
    grey = np.clip(0.76 + 0.34 * lit - 0.2 * np.clip(v + 0.1, 0, 1), 0.45, 1.0)
    gx0, gy0 = (i % G) * C, (i // G) * C
    sheet[gy0:gy0 + C, gx0:gx0 + C] = np.dstack([grey * 255, grey * 255, grey * 255, a * 255])
Image.fromarray(np.clip(sheet, 0, 255).astype(np.uint8), 'RGBA').save(out)
print('wrote', out)
