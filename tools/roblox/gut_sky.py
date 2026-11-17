# THE GUT's sky (17 Nov 2026): three plain gradient pictures for a Roblox Sky (the owner's brief: "a warm red sky" with a
# pink haze). Side faces: a hot pink haze at the horizon going up to a deep warm red; the top face: the deep red,
# darkest overhead; the bottom face: the haze. Nothing drawn in them: no shapes, no text.
#   py tools/roblox/gut_sky.py <out_dir>    -> gut_sky_side.png, gut_sky_up.png, gut_sky_dn.png
import sys, os, math
from PIL import Image

out = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(out, exist_ok=True)
N = 512
# colour by elevation (degrees): the haze at the horizon, a warm coral low down, a deep red overhead
STOPS = [(0, (248, 208, 198)), (6, (242, 182, 172)), (18, (228, 146, 140)), (40, (200, 110, 112)), (90, (164, 82, 92))]   # (a dusty warm rose: the first, redder take flooded the arena with red light)
def col(e):
    e = max(0.0, min(90.0, e))
    for (a, ca), (b, cb) in zip(STOPS, STOPS[1:]):
        if e <= b:
            t = (e - a) / (b - a)
            t = t * t * (3 - 2 * t)
            return tuple(int(round(ca[k] + (cb[k] - ca[k]) * t)) for k in range(3))
    return STOPS[-1][1]
HAZE = STOPS[0][1]

side = Image.new('RGB', (N, N))
px = side.load()
for j in range(N):
    for i in range(N):
        # a cube face at distance 1: pixel (u, v) in -1..1; elevation from the face's direction
        u = (i + 0.5) / N * 2 - 1
        v = 1 - (j + 0.5) / N * 2
        e = math.degrees(math.atan2(v, math.hypot(1.0, u)))
        px[i, j] = col(e) if e >= 0 else HAZE
side.save(os.path.join(out, 'gut_sky_side.png'))
up = Image.new('RGB', (N, N))
px = up.load()
for j in range(N):
    for i in range(N):
        u = (i + 0.5) / N * 2 - 1
        v = (j + 0.5) / N * 2 - 1
        e = math.degrees(math.atan2(1.0, math.hypot(u, v)))
        px[i, j] = col(e)
up.save(os.path.join(out, 'gut_sky_up.png'))
Image.new('RGB', (64, 64), HAZE).save(os.path.join(out, 'gut_sky_dn.png'))
print('wrote', out)
