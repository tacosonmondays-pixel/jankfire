# The anime SLASH, round 2: drawn flat in 2D (the VFX session, 26 Nov 2026). The Blender slash (slash_bl.py) passed the
# offline critic at 8, but in game (v1391, first person, a bright training range) it read 4/10: "four stacked,
# see-through pale arcs with soft, fading edges ... a ghostly wind smear, not an anime cut": its white core covered
# most of it, and its additive layers washed out on a bright scene. This one is built for a PAINTED blend (as the bullet
# pop, which held up in game): one opaque crescent, coloured as drawn.
#
# The layer breakdown, written before building:
#   The drawing's UP is the swing's direction; the arc bulges to the RIGHT of it (the --mirror copy bulges left).
#   The crescent: the outer, convex edge is the blade tip's path (a spiral: its radius grows 14 % from tail to head, never
#   a circle); the width is thickest a little ahead of the middle, a long thin taper to the tail and a shorter, concave,
#   needle-sharp head. Its ends are always points (a wiped tail tapers again, never a cut).
#     body  (white, tinted in game)  the whole crescent, plus ONE echo growing out of its inner edge (55-85 % of the arc)
#     core  (white)                  a band along the outer leading edge, ~30 % of the width
#     ink   (black)                  a thin line along the inner trailing edge, the middle 70 % of the crescent
#   16 frames over the slash's 0.42 s (26 ms each):
#     f0     the lead-in: a white sliver on the crescent's curve, the front 45 %, 40 % of its thickness, pointed
#     f1     the whole crescent, all white but a 3 px tinted outer rim
#     f2-4   the hold: tinted body, white leading band, the ink line, the echo arc; the arc pushes out 4 %
#     f5-7   the tail wipes towards the head (to 85 %), the width thins to half; the echo goes first (f5)
#     f8-10  the blade-light line: the head-most 30 % of the white edge alone, shrinking, overshooting the head by 10 %
#     f11-15 empty
#
#   py -3.12 -E -P slash2d.py <out dir> <name> [--arc 150] [--width 0.3] [--spiral 0.14] [--mirror] [--seed 3]
#   writes <out>/<name>_<body|core|ink>_<ff>.png at 512 px (sheet.py pack takes them to 256 cells)
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw


def opt(k, d):
    return type(d)(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else d


args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT, NAME = args[0], args[1]
ARC = math.radians(opt('--arc', 150.0))
WIDTH = opt('--width', 0.3)  # the crescent's thickest, in half-cells
SPIRAL = opt('--spiral', 0.14)
PEAK = opt('--peak', 0.62)  # where along the arc the crescent is thickest
MIRROR = '--mirror' in sys.argv
os.makedirs(OUT, exist_ok=True)
PX, SS = 512, 4
N = PX * SS
FR = 16
R0 = 0.78  # the outer radius at the tail (half-cells)


def P(u, v):
    u -= 0.32  # (the crescent's middle onto the cell's middle: the game places the slash by the cell's centre)
    if MIRROR: u = -u
    return ((u + 1) / 2 * N, (1 - (v + 1) / 2) * N)


def path(t, push=1.0):
    # the outer edge at t (0 = tail, bottom; 1 = head, top): a spiral round a centre left of the cell's middle
    phi = -ARC / 2 + ARC * t
    r = R0 * (1 + SPIRAL * t) * push
    cx = -R0 * (1 + SPIRAL * 0.5) * math.cos(ARC / 2) * 0.35 - 0.12
    return cx + r * math.cos(phi), r * math.sin(phi) * 0.98, phi


def prof(u):
    # thickness along the visible part (0..1): a long thin tail, thickest at 62 %, a concave needle head
    if u <= 0 or u >= 1: return 0.0
    return (u / PEAK) ** 1.5 if u < PEAK else (1 - (u - PEAK) / (1 - PEAK)) ** 1.35


def crescent(t0, t1, width, inner_from=0.0, inner_to=1.0, push=1.0, prof_t0=None, prof_t1=None):
    # the band between the fractions inner_from and inner_to of the thickness, measured inward from the outer edge
    a, b = (prof_t0 if prof_t0 is not None else t0), (prof_t1 if prof_t1 is not None else t1)
    outer, inner = [], []
    for i in range(81):
        t = t0 + (t1 - t0) * i / 80
        x, y, phi = path(t, push)
        nx, ny = math.cos(phi), math.sin(phi)  # (outward)
        w = width * prof((t - a) / max(b - a, 1e-4))
        outer.append(P(x - nx * w * inner_from, y - ny * w * inner_from))
        inner.append(P(x - nx * w * inner_to, y - ny * w * inner_to))
    return outer + inner[::-1]


def smooth(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def ink_line(t0, t1, push, wmain_t0, wmain_t1):
    # (round 2) the ink: a line along the inner edge, nothing at either end, thickest at 60 % of the arc (~3 % of the
    # radius), on the inside of the crescent's inner edge
    outer, inner = [], []
    for i in range(61):
        t = t0 + (t1 - t0) * i / 60
        x, y, phi = path(t, push)
        nx, ny = math.cos(phi), math.sin(phi)
        w = WIDTH_NOW[0] * prof((t - wmain_t0) / max(wmain_t1 - wmain_t0, 1e-4))
        u = (t - t0) / max(t1 - t0, 1e-4)
        k = math.sin(math.pi * min(1, u / 0.6 * 0.5) if u < 0.6 else math.pi * (0.5 + (u - 0.6) / 0.4 * 0.5)) ** 1.2
        th = 0.03 * R0 * k
        outer.append(P(x - nx * (w - th), y - ny * (w - th)))
        inner.append(P(x - nx * w, y - ny * w))
    return outer + inner[::-1]


def echo(push, wmain):
    # (round 3) the echo leaves the crescent's inner edge TANGENTIALLY (its rounded root hung below the edge as a hook: a
    # bird's wing): its centre line starts just inside the body and curves out as u^2, so its inner edge leaves the main
    # inner edge at under 15 degrees; it thins to a point at 85 % of the arc, the gap there 8 % of the radius
    top, bot = [], []
    for i in range(49):
        u = i / 48
        t = 0.5 + 0.35 * u
        x, y, phi = path(t, push)
        nx, ny = math.cos(phi), math.sin(phi)
        w_in = wmain * prof(t)
        c = w_in + 0.08 * R0 * u * u - 0.1 * wmain * (1 - u) ** 2
        we = 0.3 * wmain * (1 - u) ** 1.1 * min(1.0, 0.6 + u / 0.15 * 0.4)
        top.append(P(x - nx * (c - we / 2), y - ny * (c - we / 2)))
        bot.append(P(x - nx * (c + we / 2), y - ny * (c + we / 2)))
    return top + bot[::-1]


WIDTH_NOW = [WIDTH]


def frame(f):
    lay = {k: Image.new('L', (N, N), 0) for k in ('body', 'core', 'ink')}
    d = {k: ImageDraw.Draw(v) for k, v in lay.items()}
    W = WIDTH
    if f == 0:
        # (round 2: a white sliver on f1's own curve, the head 45 %, at most 40 % of f1's thickest, pointed both ends)
        d['core'].polygon(crescent(0.55, 1.0, W * 1.1 * 0.4), fill=255)
    elif f == 1:
        d['body'].polygon(crescent(0.0, 1.0, W * 1.1), fill=255)
        d['core'].polygon(crescent(0.0, 1.0, W * 1.1, inner_from=0.12), fill=255)  # (a thin tinted rim outside the white)
    elif 2 <= f <= 6:
        push = 1.0 + 0.04 * smooth((f - 2) / 2)
        t0 = 0.85 * smooth((f - 4.5) / 2.5) if f >= 5 else 0.0
        w = W * (1 - 0.5 * smooth((f - 4.5) / 2.5))
        WIDTH_NOW[0] = w
        d['body'].polygon(crescent(t0, 1.0, w, push=push), fill=255)
        d['core'].polygon(crescent(t0, 1.0, w, inner_from=0.0, inner_to=0.3, push=push), fill=255)
        if f <= 6:
            # (round 3: while the echo shows, the ink stops at 48 % of the arc, before the echo's root, on a smooth curve)
            a = t0 + (1 - t0) * 0.12
            b = 0.48 if f <= 4 else t0 + (1 - t0) * 0.88
            if b - a > 0.05: d['ink'].polygon(ink_line(a, b, push, t0, 1.0), fill=255)
        if f <= 4:
            d['body'].polygon(echo(push, w), fill=255)
    elif 7 <= f <= 10:
        # (round 2: f8 showed a full-length line again after f7's last wedge, a flicker: only the head-most part now,
        # shrinking each frame, overshooting the head by up to 10 %. Round 3: f7 joins them, a curved sliver on the arc,
        # white on its outer edge: its straight-sided wedge read as a paper plane)
        k = f - 7
        t0 = (0.7, 0.8, 0.87, 0.94)[k]
        t1 = (1.03, 1.06, 1.09, 1.1)[k]
        lw = W * (0.26, 0.2, 0.15, 0.1)[k]
        d['core'].polygon(crescent(t0, t1, lw, push=1.04), fill=255)
        d['body'].polygon(crescent(t0, t1, lw * 1.5, push=1.04), fill=255)
    out = {}
    for k, im in lay.items():
        a = np.asarray(im, np.float32).reshape(PX, SS, PX, SS).mean((1, 3)) / 255
        rgba = np.zeros((PX, PX, 4), np.uint8)
        rgba[..., :3] = 0 if k == 'ink' else 255
        rgba[..., 3] = (a * 255 + 0.5).astype(np.uint8)
        out[k] = rgba
    return out


worst = 0.0
for f in range(FR):
    lay = frame(f)
    for k, rgba in lay.items():
        Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, '%s_%s_%02d.png' % (NAME, k, f)))
        a = rgba[..., 3]
        m = 12
        worst = max(worst, max(a[:m].max(), a[-m:].max(), a[:, :m].max(), a[:, -m:].max()) / 255)
print('frames', OUT, NAME, 'edge alpha max %.3f (must be 0)' % worst)
