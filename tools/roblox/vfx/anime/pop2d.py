# The anime BULLET IMPACT pop (the VFX session, 26 Nov 2026): what a bullet hitting a wall flashes, drawn flat in 2D
# (numpy + PIL at 4x supersample, like puff2d.py: no meshes, no Cycles grain). The dust that follows is Fx's DUST, the
# chips Fx's Blender flakes.
#
# The layer breakdown, written before building (after AnyVFX's method), round 2 after the critic's 4/10 (round 1 read
# as a bird's foot or a sprouting plant: a stub into the wall as a stem, a "Y" of one spike and two arms, blunt
# even-width spikes, a cotton-ball core; its lines as a leaf fan; it filled 35 % of the cell and its chips were noise):
#   The drawing's +Y is the surface normal; the hit point sits 0.4 of a half-cell BELOW the cell's centre (the spray
#   only goes outward, so the room is above it: Fx lifts the particle along the normal to match). 16 frames over a
#   0.32 s life (20 ms a frame: a single frame can be skipped at 60 Hz, so the pop holds two):
#   f0   the star in PURE WHITE (core layer only), 90 %
#   f1   the star at 100 %, tinted (body), a white streak 75 % up each needle; 2-3 thin black wedges between needles
#        (ink, f0-f1 only, half a needle long); four lines leave from inside the star
#   f2   the star at 35 %; the lines at full length, tails at the star's edge (no gap)
#   f3   the lines wipe from the tail (the head creeps on a little)
#   f4-15 empty
#   The star: six needles at -7, +28, -41, +63, -84, +92 degrees from the normal (no stub into the wall), lengths 1.0,
#   0.7, 0.55, 0.4, 0.3, 0.22 of the longest; each 18 % as wide as long at the base, its two sides bowing in unequally
#   to a sharp tip; a jagged five-point core burst (radius 22 % of the longest). The lines: straight radial wedges (axis
#   through the hit point), a thin tail and a sharp head outward, at least 6 px wide at 256; four of them, of uneven
#   lengths and gaps (two within 15 degrees of each other).
#
#   py -3.12 -E -P pop2d.py <out dir> [name] [seed] [--mirror]
#   writes <out>/<name>_<body|core|ink>_<ff>.png at 512 px (2x; sheet.py pack/comp take them down to 256 cells)
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

args = [a for a in sys.argv[1:] if not a.startswith('--')]
MIRROR = '--mirror' in sys.argv
OUT = args[0]
NAME = args[1] if len(args) > 1 else 'pop_a'
rng = random.Random(int(args[2]) if len(args) > 2 else 5)
os.makedirs(OUT, exist_ok=True)
PX, SS = 512, 4
N = PX * SS
FR = 16
BODY_GREY = 0.62
V0 = -0.4  # the hit point (half-cell units, up = +)
LMAX = 0.86  # the longest needle at 100 %


def P(u, v):  # half-cell units (up = +v), measured from the hit point, to drawing pixels
    v = v + V0
    if MIRROR: u = -u
    return ((u + 1) / 2 * N, (1 - (v + 1) / 2) * N)


def needle(ang, L, base_hw, pa, pb, bend, upto=1.0, start=0.0, grow=0.0):
    # a concave spike from the hit point: half-width base_hw at the root, sides bowing in with unequal powers to a sharp
    # tip, the tip bent by `bend` radians; `upto` < 1 draws only the inner part (the white streak), `start` skips the root
    pts_a, pts_b = [], []
    Lg = L + grow * 1.6
    for i in range(29):
        s = start + (upto - start) * i / 28
        a = ang + bend * s * s
        cx, cy = math.sin(a) * Lg * s, math.cos(a) * Lg * s
        nx, ny = math.cos(a), -math.sin(a)
        wa = base_hw * (1 - s) ** pa + grow * (1 - 0.63 * s)
        wb = base_hw * (1 - s) ** pb + grow * (1 - 0.63 * s)
        if upto < 1 and i == 28: wa = wb = 0  # (the streak ends in a point too)
        pts_a.append(P(cx + nx * wa, cy + ny * wa)); pts_b.append(P(cx - nx * wb, cy - ny * wb))
    return pts_a + pts_b[::-1]


def burst(R, angs, ks):
    # a jagged five-point core: points at uneven angles and lengths, the valleys at half of R
    pts = []
    n = len(angs)
    for j in range(n):
        a, k = angs[j], ks[j]
        a2 = angs[(j + 1) % n] + (math.tau if j == n - 1 else 0)
        pts.append(P(math.sin(a) * R * k, math.cos(a) * R * k))
        am = (a + a2) / 2
        pts.append(P(math.sin(am) * R * 0.42, math.cos(am) * R * 0.42))
    return pts


def line(ang, r0, r1, hw):
    # a straight radial streak: a 1 px tail at r0, widest at 80 %, ONE sharp point, the head at r1 (round 3: no shape
    # pointed at both ends), one side a little fuller
    if r1 - r0 < 0.012: return None
    top, bot = [], []
    for i in range(25):
        s = i / 24
        r = r0 + (r1 - r0) * s
        cx, cy = math.sin(ang) * r, math.cos(ang) * r
        nx, ny = math.cos(ang), -math.sin(ang)
        prof = 0.04 + 0.96 * (s / 0.8) ** 1.3 if s < 0.8 else (1 - (s - 0.8) / 0.2) ** 0.8
        w = hw * prof
        top.append(P(cx + nx * w, cy + ny * w)); bot.append(P(cx - nx * w * 0.82, cy - ny * w * 0.82))
    return top + bot[::-1]


# ---- the plan
NEEDLES = []
# (round 3: with the side needles short every spike pointed up out of a square core: a potted plant. The needles along
# the wall are long now, so the star is a wide splash crown across 80 % of the cell; the sides bow in less)
for a, k in zip((-7, 28, -41, 63, -84, 92), (1.0, 0.62, 0.72, 0.5, 0.86, 0.66)):
    L = LMAX * k
    NEEDLES.append((math.radians(a + rng.uniform(-2, 2)), L, L * 0.12, rng.uniform(1.05, 1.25), rng.uniform(1.3, 1.6),
                    math.radians(rng.uniform(-5, 5))))
CORE_R = LMAX * 0.24
CORE_A = [math.radians(a) for a in (-8, 33, 71, 118, 160, 205, 252, 300)]  # (eight uneven points: a flash, not a box)
CORE_K = [1.0, 0.7, 0.82, 0.55, 0.62, 0.5, 0.78, 0.66]
# (round 3) the black: two real shards behind the white, based on the core's edge, in the needles' gaps:
# angle, base half-width, length as a share of LMAX
SHARDS = [(-62, 0.047, 0.45), (45, 0.027, 0.3)]
SHARDS = [(math.radians(a + rng.uniform(-3, 3)), hw, LMAX * k) for a, hw, k in SHARDS]
# (round 3) the lines continue straight out of four needles' tips: needle index, where the head is at full length
# (half-cells from the hit point), half-width (orange; the white is the middle 38 %)
# (polish after 8/10: the tails start at staggered radii so the rays don't pivot on one pixel, the +28 line is shorter,
# breaking the near-even fan)
LINES = [(0, 1.08, 0.03, 0.08), (1, 0.72, 0.024, 0.16), (2, 0.95, 0.027, 0.12), (3, 0.7, 0.021, 0.2)]
EDGE = {0: 0.062, 1: 0.024}  # (round 3) a deep orange outer edge on f0 (~8 px at a needle's base, ~3 at its tip) and f1


def shard(ang, r0, L, hw):
    pts_a, pts_b = [], []
    for i in range(17):
        s = i / 16
        r = r0 + L * s
        cx, cy = math.sin(ang) * r, math.cos(ang) * r
        nx, ny = math.cos(ang), -math.sin(ang)
        pts_a.append(P(cx + nx * hw * (1 - s) ** 1.15, cy + ny * hw * (1 - s) ** 1.15))
        pts_b.append(P(cx - nx * hw * 0.8 * (1 - s) ** 1.5, cy - ny * hw * 0.8 * (1 - s) ** 1.5))
    return pts_a + pts_b[::-1]


def frame(f):
    lay = {k: Image.new('L', (N, N), 0) for k in ('edge', 'body', 'core', 'ink')}
    d = {k: ImageDraw.Draw(v) for k, v in lay.items()}
    sk = {0: 0.9, 1: 1.0, 2: 0.35}.get(f)
    if sk:
        g = EDGE.get(f, 0.0)
        for ang, L, hw, pa, pb, bend in NEEDLES:
            if g: d['edge'].polygon(needle(ang, L * sk, hw * sk, pa, pb, bend, grow=g), fill=255)
            if f == 0:
                d['core'].polygon(needle(ang, L * sk, hw * sk, pa, pb, bend), fill=255)
            else:
                # (round 3: the white is the middle 38 % of the needle and stops 60 % up: about 55 % orange on f1)
                d['body'].polygon(needle(ang, L * sk, hw * sk, pa, pb, bend), fill=255)
                d['core'].polygon(needle(ang, L * sk, hw * sk * 0.38, pa, pb, bend, upto=0.6), fill=255)
        if g: d['edge'].polygon(burst(CORE_R * sk + g, CORE_A, CORE_K), fill=255)
        if f == 0:
            d['core'].polygon(burst(CORE_R * sk, CORE_A, CORE_K), fill=255)
        else:
            d['body'].polygon(burst(CORE_R * sk, CORE_A, CORE_K), fill=255)
            d['core'].polygon(burst(CORE_R * sk * 0.72, CORE_A, CORE_K), fill=255)
        if f < 2:
            for ang, hw, L in SHARDS:
                d['ink'].polygon(shard(ang, CORE_R * sk * 0.55, L * sk, hw * sk), fill=255)
    # the lines, out of the needles' tips: f1 the tip grows on; f2 full, the tail at the core; f3-4 the heads fly on
    # (+0.12, +0.10) as the lines shorten to 35 % and 12 %
    if 1 <= f <= 3:  # (f4's remnants were under a pixel at game size: gone)
        for ni, rf, hw, t0 in LINES:
            ang, L, _, _, _, bend = NEEDLES[ni]
            a = ang + bend  # (the tip's direction from the hit point: the line's axis passes through it)
            full = rf - t0
            if f == 1:
                r0, r1, w = L * 0.7, L + 0.25 * (rf - L), hw * 0.85
            elif f == 2:
                r0, r1, w = t0, rf, hw
            else:
                r1 = rf + 0.12
                r0, w = r1 - 0.35 * full, hw * 0.8
            b = line(a, r0, r1, w)
            c = line(a, r0 + (r1 - r0) * 0.15, r1 - 0.012, w * 0.38)
            if b: d['body'].polygon(b, fill=255)
            if c: d['core'].polygon(c, fill=255)
    out = {}
    for k, im in lay.items():
        a = np.asarray(im, np.float32).reshape(PX, SS, PX, SS).mean((1, 3)) / 255
        rgba = np.zeros((PX, PX, 4), np.uint8)
        rgba[..., :3] = int({'edge': BODY_GREY, 'body': BODY_GREY, 'core': 1.0, 'ink': 0.0}[k] * 255 + 0.5)
        rgba[..., 3] = (a * 255 + 0.5).astype(np.uint8)
        out[k] = rgba
    return out


worst = 0.0
for f in range(FR):
    lay = frame(f)
    for k, rgba in lay.items():
        Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, '%s_%s_%02d.png' % (NAME, k, f)))
        a = rgba[..., 3]
        m = 12  # (6 px at 256)
        worst = max(worst, max(a[:m].max(), a[-m:].max(), a[:, :m].max(), a[:, -m:].max()) / 255)
print('frames', OUT, NAME, 'mirror' if MIRROR else '', 'edge alpha max %.3f (must be 0)' % worst)
