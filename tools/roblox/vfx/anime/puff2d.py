# Anime smoke puff flipbook, drawn in 2D (the VFX session, 26 Nov 2026; round 3 after the critic's 6/10. Round 1 was the
# Blender metaball puff, puff_bl.py, which read as clay and pearls). Cel smoke is a 2D design, so it is drawn as one:
#   shape   an untidy heap of round bumps, taller than a cloud icon (height about 0.8 of its width): one dominant bump a
#           third of the way across, smaller ones trailing off to one side (a drift direction), a scalloped bottom;
#           their UNION is the silhouette, so bumps meet at sharp inward cusps. 1-3 small satellite puffs off the edge
#           on f3-8
#   tones   two flat tones (light 0.88, shadow 0.6): each bump's shadow crescent on the side away from the light, thick
#           on the lower and outer bumps, thin or none on the top ones, and an occlusion shadow on a back bump along
#           the edge of the front bump that covers it (form, not a drop shadow)
#   motion  f0-4 swells out of a point (ease-out); f4-8 keeps growing another 20 %, rising and drifting a little;
#           f8-11 it splits into 3 fragments that drift apart, each shrinking as a little cloud (its bumps close in, at
#           least 3 each) to 40 % with a shallow notch at most a quarter of its width; f12 they are gone. No fades
# One layer, greyscale: painted (LightEmission 0) and tinted by the game (gun smoke, dust). Rendered at 4x and
# box-downsampled.
#
#   py -3.12 -E -P puff2d.py <out dir> <name> [--seed 5] [--px 256]
#   writes <out>/<name>_smoke_<ff>.png (and _body_/_core_/_ink_ copies so sheet.py's previews and packs work)
import math
import os
import random
import sys

import numpy as np
from PIL import Image

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT, NAME = args[0], args[1]
opt = lambda k, d: type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d
SEED, PX = opt('--seed', 5), opt('--px', 256)
SS = 4
N = PX * SS
rng = random.Random(SEED)
os.makedirs(OUT, exist_ok=True)
LIGHT = np.array([0.6, 0.8])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
LIGHT_C, SHADE_C = 0.88, 0.6

# the heap (units: the heap's own; it is scaled into the cell per frame)
bumps = []
bumps.append(dict(x=-0.18, y=0.1, r=0.36))                       # the dominant one, a third of the way across
bumps.append(dict(x=-0.42, y=-0.12, r=0.22))                     # its left shoulder
bumps.append(dict(x=0.12, y=0.02, r=0.27))                       # trailing off to the right, smaller and smaller
bumps.append(dict(x=0.36, y=-0.06, r=0.2))
bumps.append(dict(x=0.54, y=-0.16, r=0.14))
bumps.append(dict(x=-0.05, y=0.42, r=0.2))                       # the crown
bumps.append(dict(x=0.2, y=0.3, r=0.17))
for x, r in ((-0.38, 0.14), (-0.15, 0.23), (0.08, 0.15), (0.29, 0.2)):  # a scalloped bottom, uneven (not a row of pearls)
    bumps.append(dict(x=x + rng.uniform(-0.03, 0.03), y=-0.3 + rng.uniform(-0.03, 0.03), r=r))
for b in bumps:
    b['x'] += rng.uniform(-0.03, 0.03); b['y'] += rng.uniform(-0.03, 0.03); b['r'] *= rng.uniform(0.93, 1.07)
NB = len(bumps)
assert max(b['r'] for b in bumps) / min(b['r'] for b in bumps) <= 3.0
cx0 = sum(b['x'] for b in bumps) / NB
cy0 = sum(b['y'] for b in bumps) / NB
for b in bumps:
    b['x'] -= cx0; b['y'] -= cy0
    # crescent thickness: thick on the lower and outer bumps, thin or none on the top ones
    # (a shadow MASS: the lower third in shadow. The crescent's width is about this share of the radius)
    low = min(1.0, max(0.0, (0.15 - b['y']) / 0.45))
    outer_left = min(1.0, max(0.0, (-b['x'] - 0.2) / 0.3))
    b['shade'] = 0.07 + 0.42 * max(low, outer_left)
# satellites: small detached puffs near the edge, f3-8
# (each a mini-cluster of 2-3 bumps, 12+ px across, at different heights and distances)
sats = [dict(parts=((0.0, 0.0, 0.075), (0.07, 0.03, 0.055), (0.03, -0.05, 0.045)), x=0.8, y=0.12, a=3, b=8),
        dict(parts=((0.0, 0.0, 0.06), (-0.06, 0.02, 0.045)), x=-0.7, y=-0.06, a=4, b=8)]
# three fragments for the exit: contiguous sectors round the middle, at least 3 bumps each
order = sorted(range(NB), key=lambda i: math.atan2(bumps[i]['y'], bumps[i]['x']))
NC = 3
groups = [order[k * NB // NC:(k + 1) * NB // NC] for k in range(NC)]
for g, members in enumerate(groups):
    assert len(members) >= 3
    for i in members: bumps[i]['g'] = g
cents = []
for g in range(NC):
    ms = [bumps[i] for i in range(NB) if bumps[i]['g'] == g]
    cx, cy = sum(b['x'] for b in ms) / len(ms), sum(b['y'] for b in ms) / len(ms)
    cents.append((cx, cy, max(math.hypot(b['x'] - cx, b['y'] - cy) + b['r'] for b in ms)))
# draw order, back to front: the top and small bumps behind, the big and low ones in front
draw = sorted(range(NB), key=lambda i: (-bumps[i]['y'] * 0.6 + bumps[i]['r']))

ys, xs = np.mgrid[0:N, 0:N]
U = (xs + 0.5) / N * 2 - 1
V = 1 - (ys + 0.5) / N * 2
FRAME = 0.86


def ease_out(x): return 1 - (1 - x) ** 3
def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def seg(t, a, b): return min(1, max(0, (t - a) / (b - a)))


def frame(f):
    t = f / 15.0
    img = np.zeros((N, N), np.float32)
    alpha = np.zeros((N, N), bool)
    if f >= 12: return img, alpha
    grow = (0.3 + 0.7 * ease_out(seg(t, 0.0, 4 / 15))) * (1 + 0.2 * ease_out(seg(t, 4 / 15, 8 / 15)))
    rise = 0.13 * smooth(seg(t, 0.05, 11 / 15))
    drift = 0.05 * smooth(seg(t, 0.1, 11 / 15))
    split = seg(t, 8 / 15, 11 / 15)
    S = 0.78 * FRAME * grow

    def place(b):
        g = b['g']
        cx, cy, cr = cents[g]
        top_g = max(range(NC), key=lambda gg: cents[gg][1])
        if g == top_g and t >= 10 / 15: return (0, 0, 0, 0, (cx, cy, cr))  # (the top one goes first, at f10)
        k = 1 - 0.6 * split  # each fragment shrinks to 40 %...
        kp = k ** 1.8  # ...its bumps closing in faster, so it stays one little cloud
        ox, oy = cx * 0.8 * split, cy * 0.8 * split  # the fragments drift apart
        if g == (top_g + 1) % NC: oy += 0.13 * split  # (one of the lower ones lifts: no symmetric triangle)
        return ((cx + (b['x'] - cx) * kp + ox) * S + drift, (cy + (b['y'] - cy) * kp + oy) * S + rise, b['r'] * S * k, k, (cx + ox, cy + oy, cr))

    for i in draw:
        b = bumps[i]
        x, y, r, k, (fx, fy, fr) = place(b)
        if r <= 0: continue
        disc = (U - x) ** 2 + (V - y) ** 2 <= r * r
        if split > 0:
            # a shallow notch from the fragment's shadow side: at most a quarter of its width
            nx, ny = (fx - LIGHT[0] * fr * 0.95 * k) * S + drift, (fy - LIGHT[1] * fr * 0.95 * k) * S + rise
            nr = fr * 0.3 * k * min(1.0, split * 3) * S
            disc &= (U - nx) ** 2 + (V - ny) ** 2 > nr * nr
        # an occlusion shadow on what's behind, along this bump's edge
        rim = ((U - (x - LIGHT[0] * r * 0.12)) ** 2 + (V - (y - LIGHT[1] * r * 0.12)) ** 2 <= (r * 1.14) ** 2) & ~disc & alpha
        img[rim] = SHADE_C
        # the bump: light, with its shadow crescent (thickness by where the bump sits)
        sh = b['shade']
        lit = (U - (x + LIGHT[0] * r * sh)) ** 2 + (V - (y + LIGHT[1] * r * sh)) ** 2 <= (r * 0.985) ** 2 if sh > 0.03 else disc
        img[disc] = np.where(lit[disc], LIGHT_C, SHADE_C)
        alpha |= disc
    for s_ in sats:
        if not (s_['a'] <= f <= s_['b']): continue
        k = max(0.7, smooth(seg(f, s_['a'], s_['a'] + 1.5)) * (1 - smooth(seg(f, s_['b'] - 1.5, s_['b'])) * 0.4))
        sx, sy = s_['x'] * S * (1 + 0.3 * seg(t, 3 / 15, 8 / 15)) + drift, s_['y'] * S + rise
        for px_, py_, pr in s_['parts']:
            x, y, r = sx + px_ * S * k, sy + py_ * S * k, max(pr * S, 0.04) * k
            disc = (U - x) ** 2 + (V - y) ** 2 <= r * r
            lit = (U - (x + LIGHT[0] * r * 0.3)) ** 2 + (V - (y + LIGHT[1] * r * 0.3)) ** 2 <= (r * 0.985) ** 2
            img[disc] = np.where(lit[disc], LIGHT_C, SHADE_C)
            alpha |= disc
    return img, alpha


def down(a): return a.reshape(PX, SS, PX, SS).mean((1, 3))


def open_light(img, alpha, k=6):
    # light areas thinner than ~2 px at the final size become shadow (no glints inside a shadow crescent)
    light = (img > 0.7) & alpha
    m = light.copy()
    for _ in range(k):
        m = m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
    for _ in range(k):
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
    m &= light
    img[light & ~m] = SHADE_C
    return img


def drop_light_islands(rgba, min_area=40):
    # a light patch smaller than min_area px (at the final size) inside the shadow reads as an eye or a glint: shadow it
    from collections import deque
    light = (rgba[..., 0] > 200) & (rgba[..., 3] > 128)
    seen = np.zeros_like(light)
    H, W = light.shape
    for y0 in range(H):
        for x0 in range(W):
            if not light[y0, x0] or seen[y0, x0]: continue
            q = deque([(y0, x0)]); seen[y0, x0] = True; comp = [(y0, x0)]
            while q:
                y, x = q.popleft()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and light[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; q.append((ny, nx)); comp.append((ny, nx))
            if len(comp) < min_area:
                for y, x in comp:
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < H and 0 <= xx < W and rgba[yy, xx, 0] > 160: rgba[yy, xx, :3] = int(SHADE_C * 255)
    return rgba


for f in range(16):
    img, alpha = frame(f)
    img = open_light(img, alpha)
    a = down(alpha.astype(np.float32))
    pm = down(img * alpha)
    rgb = np.where(a > 1e-4, pm / np.maximum(a, 1e-4), 0)
    rgba = np.zeros((PX, PX, 4), np.uint8)
    rgba[..., 0] = rgba[..., 1] = rgba[..., 2] = np.clip(rgb * 255, 0, 255)
    rgba[..., 3] = np.clip(a * 255, 0, 255)
    rgba = drop_light_islands(rgba)
    for lay in ('body', 'smoke'):
        Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, '%s_%s_%02d.png' % (NAME, lay, f)))
    empty = np.zeros((PX, PX, 4), np.uint8)
    for lay in ('core', 'ink'):
        Image.fromarray(empty, 'RGBA').save(os.path.join(OUT, '%s_%s_%02d.png' % (NAME, lay, f)))
print('done', NAME)
