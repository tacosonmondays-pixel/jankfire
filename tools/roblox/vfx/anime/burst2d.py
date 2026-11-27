# The anime melee HIT BURST, round 2: drawn flat in 2D (the VFX session, 27 Nov 2026). The Blender burst (burst_bl.py)
# passed offline, but in game (v1409, a katana hit on the training dummy) the critic gave it 4/10: "a soft, translucent
# swirl of white-blue arcs ... washes out on the tan dummy and reads as ghostly feathers". Its additive layers washed
# out as the Blender slash's did. This one is built for the PAINTED blend (one opaque cel shape, coloured as drawn), as
# the 2D slash (slash2d.py) and the bullet pop (pop2d.py) are.
#
# The layer breakdown, written before building:
#   The hit point is the cell's centre; the burst has no up (AnimeFx turns each hit at random). 16 frames over the
#   burst's 0.34 s (21 ms a frame); live f0-f8, f9-f15 empty.
#     body  (white, tinted in game)  the star's needles and its jagged core, then the shock arcs, then the flying shards
#     core  (white)                  f0 the whole star; then a white streak up each needle and a shrinking white core
#     ink   (black)                  three thin wedges in the star's three widest gaps (f1-f4), flying out and thinning
#   The star: five concave needles at uneven angles (10, 72, 158, 205, 290 degrees) and lengths (1.0, 0.62, 0.85, 0.48,
#   0.74 of the longest), each 20 % as wide as long at the root, its two sides bowing in unequally to a sharp tip, round
#   a jagged seven-point core. The shock: three arc pieces of uneven spans (70, 48, 32 degrees) and places, each
#   pointed at both ends, thickest at a different point along each (all at a third turned the three into a pinwheel),
#   never a ring. Round 1 of the drawing was spindly (needles 14 % wide, a small core) and its ink wedges read as a
#   second, black star: the needles are 20 % wide now, the core bigger, the ink shorter and fatter, two arcs not three.
#     f0     the star at 80 %, ALL WHITE (core only): the flash
#     f1-2   the star at 100-104 %, tinted; the white streaks and core; the ink wedges; the arcs appear on f2
#     f3-4   the core shrinks away; the star breaks into shards (darts: one sharp point leading, a tail thinning
#            behind); the arcs fly out and thin
#     f5-8   the shards fly on, shortening and thinning; the arcs gone by f6
#   Round 2 after the critic's 6/10 on the drawing: the shards flew at even angles and one speed, a ring of petals (a
#   daisy, a firework) pointed at both ends; and the ink wedges floated in the gaps ("flies or dirt"). Now each shard
#   has its own speed (the two longest fly furthest), one needle splits into two shards 17 degrees apart and the
#   shortest drops out, each shard is a dart; the ink is rooted on the core's edge, 0.4 of a needle long, f1-f2 only.
#
#   py -3.12 -E -P burst2d.py <out dir> [name] [seed]
#   writes <out>/<name>_<body|core|ink>_<ff>.png at 512 px (sheet.py pack takes them to 256 cells)
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
NAME = args[1] if len(args) > 1 else 'burst_p'
rng = random.Random(int(args[2]) if len(args) > 2 else 7)
os.makedirs(OUT, exist_ok=True)
PX, SS = 512, 4
N = PX * SS
FR = 16
LMAX = 0.68  # the longest needle at 100 % (half-cells): with the shards' flight (0.18) it ends inside 0.9


def P(u, v):
    return ((u + 1) / 2 * N, (1 - (v + 1) / 2) * N)


def needle(ang, L, base_hw, pa, pb, bend, s0=0.0, s1=1.0, shift=0.0, wf=1.0):
    # a concave spike from the centre along `ang` (0 = up, clockwise): half-width base_hw at the root, its sides bowing
    # in with unequal powers to a sharp tip; s0..s1 draws a part of it (a shard: the root wiped), moved out by `shift`;
    # a wiped root still tapers to a point (never a cut)
    pts_a, pts_b = [], []
    for i in range(33):
        s = s0 + (s1 - s0) * i / 32
        a = ang + bend * s * s
        r = L * s + shift
        cx, cy = math.sin(a) * r, math.cos(a) * r
        nx, ny = math.cos(a), -math.sin(a)
        root = min(1.0, (s - s0) / 0.12) if s0 > 0 else 1.0
        wa = base_hw * wf * (1 - s) ** pa * root
        wb = base_hw * wf * (1 - s) ** pb * root
        if s1 < 1 and i == 32: wa = wb = 0
        pts_a.append(P(cx + nx * wa, cy + ny * wa)); pts_b.append(P(cx - nx * wb, cy - ny * wb))
    return pts_a + pts_b[::-1]


def jag(R, angs, ks):
    pts = []
    n = len(angs)
    for j in range(n):
        a, k = angs[j], ks[j]
        a2 = angs[(j + 1) % n] + (math.tau if j == n - 1 else 0)
        pts.append(P(math.sin(a) * R * k, math.cos(a) * R * k))
        am = (a + a2) / 2
        pts.append(P(math.sin(am) * R * 0.45, math.cos(am) * R * 0.45))
    return pts


def wedge(ang, r0, L, hw):
    # a thin black stroke out from r0: widest at its root, one side fuller, a sharp tip outward
    pts_a, pts_b = [], []
    for i in range(17):
        s = i / 16
        r = r0 + L * s
        cx, cy = math.sin(ang) * r, math.cos(ang) * r
        nx, ny = math.cos(ang), -math.sin(ang)
        k = min(1.0, s / 0.15) * (1 - s) ** 1.2
        pts_a.append(P(cx + nx * hw * k, cy + ny * hw * k)); pts_b.append(P(cx - nx * hw * 0.7 * k, cy - ny * hw * 0.7 * k))
    return pts_a + pts_b[::-1]


def dart(ang, r_tail, r_head, W):
    # a shard flying out along `ang`: its sharp point leading (outward), widest at 70 %, a tail thinning behind it to
    # a tenth of that (never a cut, never a second point)
    pts_a, pts_b = [], []
    for i in range(25):
        s = i / 24
        r = r_tail + (r_head - r_tail) * s
        cx, cy = math.sin(ang) * r, math.cos(ang) * r
        nx, ny = math.cos(ang), -math.sin(ang)
        k = 0.1 + 0.9 * (s / 0.7) ** 1.1 if s < 0.7 else max(0.0, 1 - (s - 0.7) / 0.3) ** 0.85
        pts_a.append(P(cx + nx * W * k, cy + ny * W * k)); pts_b.append(P(cx - nx * W * 0.8 * k, cy - ny * W * 0.8 * k))
    return pts_a + pts_b[::-1]


def jag_r(R, angs, ks, ang):
    # the jagged core's edge radius in direction `ang` (its outline is straight between point and valley)
    pts = []
    n = len(angs)
    for j in range(n):
        a2 = angs[(j + 1) % n] + (math.tau if j == n - 1 else 0)
        pts.append((angs[j], R * ks[j])); pts.append(((angs[j] + a2) / 2, R * 0.45))
    pts.append((pts[0][0] + math.tau, pts[0][1]))
    ang = ang % math.tau
    if ang < pts[0][0]: ang += math.tau
    for (a0, r0), (a1, r1) in zip(pts, pts[1:]):
        if a0 <= ang <= a1:
            x0, y0, x1, y1 = math.sin(a0) * r0, math.cos(a0) * r0, math.sin(a1) * r1, math.cos(a1) * r1
            dx, dy = math.sin(ang), math.cos(ang)
            ex, ey = x1 - x0, y1 - y0
            den = dx * ey - dy * ex
            return (x0 * ey - y0 * ex) / den if abs(den) > 1e-9 else r0
    return R * 0.45


def arc(mid, span, r, th, pk):
    # a piece of the shock: from mid - span/2 to mid + span/2 at radius r, pointed both ends, thickest at pk of its
    # length (clockwise), its outer edge on r
    outer, inner = [], []
    for i in range(41):
        s = i / 40
        a = mid - span / 2 + span * s
        k = (s / pk) ** 0.9 if s < pk else (1 - (s - pk) / (1 - pk)) ** 1.1
        t = th * k
        outer.append(P(math.sin(a) * r, math.cos(a) * r))
        inner.append(P(math.sin(a) * (r - t), math.cos(a) * (r - t)))
    return outer + inner[::-1]


# ---- the plan
NEEDLES = []
for a, k in zip((10, 72, 158, 205, 290), (1.0, 0.62, 0.85, 0.48, 0.74)):
    L = LMAX * k
    NEEDLES.append((math.radians(a + rng.uniform(-3, 3)), L, L * 0.2, rng.uniform(1.0, 1.2), rng.uniform(1.3, 1.6),
                    math.radians(rng.uniform(-6, 6))))
CORE_R = LMAX * 0.36
CORE_A = [math.radians(a) for a in (4, 50, 101, 139, 186, 238, 301)]
CORE_K = [0.9, 0.62, 1.0, 0.55, 0.8, 0.6, 0.72]
INK = [(math.radians(121), 0.4 * LMAX * 0.74, 0.046), (math.radians(240), 0.4 * LMAX * 0.6, 0.04), (math.radians(334), 0.4 * LMAX * 0.87, 0.034)]
# the shards (f3 on): needle index, angle offset (degrees), length and width as shares of the needle's, flight (half-
# cells by f8). Needle 2 splits in two 17 degrees apart; needle 3 (the shortest) drops out
SHARDS = [(0, 0, 1.0, 1.0, 0.2), (1, 0, 1.0, 1.0, 0.1), (2, -8, 0.85, 0.72, 0.17), (2, 9, 0.62, 0.62, 0.11),
          (4, 0, 1.0, 1.0, 0.07)]
FLIGHT = {3: 0.3, 4: 0.5, 5: 0.68, 6: 0.82, 7: 0.93, 8: 1.0}
# (round 3, the in-game critic on v1423: the two shock arcs read as strays, "a blue headband" across the target's eyes and
# "a loose sliver" under the slash: cut. They were (40, 64, 0.33) and (222, 42, 0.66): mid, span, thickest point)
ARCS = []

# per frame: star scale, the needles' visible part from s0 and their flight out, width; the white core's and the
# body's core scale; the white streak's width and reach; the ink (start radius, length factor, width factor); the
# arcs (radius, thickness, span factor)
PLAN = {
    0: dict(sk=0.9, s0=0.0, sh=0.0, wf=1.0, white=True),
    1: dict(sk=1.0, s0=0.0, sh=0.0, wf=1.0, bc=1.0, cc=0.72, st=(0.45, 0.55), ink=(1.0, 1.0)),
    2: dict(sk=1.04, s0=0.0, sh=0.0, wf=1.0, bc=1.0, cc=0.58, st=(0.4, 0.5), ink=(0.9, 0.85), arcs=(0.52, 0.06, 1.0)),
    3: dict(sk=1.04, s0=0.22, sh=0.05, wf=0.95, bc=0.6, cc=0.3, st=(0.35, 0.45), arcs=(0.62, 0.05, 0.85)),
    4: dict(sk=1.04, s0=0.42, sh=0.09, wf=0.85, st=(0.3, 0.3), arcs=(0.7, 0.04, 0.65)),
    5: dict(sk=1.04, s0=0.5, sh=0.12, wf=0.55, arcs=(0.76, 0.03, 0.45)),
    6: dict(sk=1.04, s0=0.6, sh=0.15, wf=0.4),
    7: dict(sk=1.04, s0=0.7, sh=0.17, wf=0.28),
    8: dict(sk=1.04, s0=0.8, sh=0.18, wf=0.18),
}


def frame(f):
    lay = {k: Image.new('L', (N, N), 0) for k in ('body', 'core', 'ink')}
    d = {k: ImageDraw.Draw(v) for k, v in lay.items()}
    q = PLAN.get(f)
    if q:
        sk = q['sk']
        if f < 3:
            for ang, L, hw, pa, pb, bend in NEEDLES:
                poly = needle(ang, L * sk, hw * sk, pa, pb, bend)
                d['core' if q.get('white') else 'body'].polygon(poly, fill=255)
                if q.get('st'):
                    w, up = q['st']
                    d['core'].polygon(needle(ang, L * sk, hw * sk * w, pa, pb, bend, s1=up), fill=255)
        else:
            for ni, da, lk, wk, fl in SHARDS:
                ang, L, hw, pa, pb, bend = NEEDLES[ni]
                a = ang + bend + math.radians(da)
                head = L * sk * lk + fl * FLIGHT[f]
                ln = L * sk * lk * (1 - q['s0'])
                W = hw * sk * wk * q['wf'] * 0.8
                d['body'].polygon(dart(a, head - ln, head, W), fill=255)
                if q.get('st'):
                    w, _ = q['st']
                    d['core'].polygon(dart(a, head - ln * 0.75, head - ln * 0.12, W * w), fill=255)
        if q.get('white'):
            d['core'].polygon(jag(CORE_R * sk, CORE_A, CORE_K), fill=255)
        if q.get('bc'):
            d['body'].polygon(jag(CORE_R * sk * q['bc'], CORE_A, CORE_K), fill=255)
        if q.get('cc'):
            d['core'].polygon(jag(CORE_R * sk * q['cc'], CORE_A, CORE_K), fill=255)
        if q.get('ink'):
            lk, wk = q['ink']
            for ang, L, hw in INK:
                # (rooted just inside the tinted core's edge, so it grows out of the core)
                r0 = jag_r(CORE_R * sk * q.get('bc', 1.0), CORE_A, CORE_K, ang) - 0.012
                d['ink'].polygon(wedge(ang, r0, L * lk, hw * wk), fill=255)
        if q.get('arcs'):
            r, th, spk = q['arcs']
            for mid, span, pk in ARCS:
                d['body'].polygon(arc(mid, span * spk, r, th, pk), fill=255)
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
