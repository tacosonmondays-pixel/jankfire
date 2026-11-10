# Real rock for a map's blocky "natural" boxes (boulders, rock formations): one mesh over the boxes the map tags
# { av: 'rocks_<map>' } (tools/arch/dumpworld.mjs writes them, in world coordinates, collision and look-only alike).
# Every box becomes a lump of rock that keeps the box's size: its top is flat at the box's top (what you stand on stays
# where it was), its sides are eroded INWARD in horizontal strata with rounded corners, its foot spreads a hand's width
# into scree. Big ones are banded mesas with ledges; small ones are boulders. Loose stones lie round their feet.
# Look only: the game keeps the boxes for collisions (tools/arch/gamehash.mjs before / after must match).
# run: blender52 -b --python tools/blender/arch/make_rocks.py -- <map> [out.glb]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAP = argv[0] if argv else 'desert'
OUT = argv[1] if len(argv) > 1 else os.path.join(OUTDIR, 'rocks_%s.glb' % MAP)
HERE = os.path.dirname(os.path.abspath(__file__))
# the stone, per map: sides, the darker strata, the sun-bleached tops, the scree
STONE = {'desert': ('#c8743e', '#9c4f2c', '#dda066', '#b8683a'), 'bazaar': ('#d0a070', '#a87848', '#e6c890', '#c09060'),
         'forest': ('#7c8088', '#5c6068', '#6a8a4a', '#70747a')}  # (the forest's tops are mossy)
c = STONE.get(MAP.replace('_sd', ''), STONE['desert'])
MATS.update({'rock': ('stucco', c[0], {}), 'rockband': ('stucco', c[1], {}), 'rocktop': ('stucco', c[2], {}), 'scree': ('stucco', c[3], {})})
NOCAST.add('scree')

K = Kit(os.path.join(HERE, 'boxes', 'rocks_%s.json' % MAP), seed=5)
K.ground = -1e9


def hsh(*a):  # a steady 0..1 from a few numbers (the same rock every build)
    x = 0.0
    for i, v in enumerate(a): x += math.sin(v * (12.9898 + i * 7.233) + i * 3.17) * 43758.5453
    return x - math.floor(x)


def ring(cx, cz, hw, hd, rc, n):
    """n points round a rounded rectangle (half sizes hw, hd, corner radius rc), counter-clockwise seen from above,
    each with its outward direction"""
    rc = min(rc, hw * 0.98, hd * 0.98)
    segs = [(2 * (hw - rc), (hw - rc, hd), (-1, 0), (0, 1)), (math.pi / 2 * rc, (-(hw - rc), hd - rc), None, (math.pi / 2, math.pi)),
            (2 * (hd - rc), (-hw, hd - rc), (0, -1), (-1, 0)), (math.pi / 2 * rc, (-(hw - rc), -(hd - rc)), None, (math.pi, 1.5 * math.pi)),
            (2 * (hw - rc), (-(hw - rc), -hd), (1, 0), (0, -1)), (math.pi / 2 * rc, (hw - rc, -(hd - rc)), None, (1.5 * math.pi, 2 * math.pi)),
            (2 * (hd - rc), (hw, -(hd - rc)), (0, 1), (1, 0)), (math.pi / 2 * rc, (hw - rc, hd - rc), None, (0, math.pi / 2))]
    per = sum(s[0] for s in segs); out = []
    for i in range(n):
        t = per * i / n
        for L, p0, dr, nrm in segs:
            if t <= L or (L, p0, dr, nrm) is segs[-1]:
                if dr: out.append(((p0[0] + dr[0] * t, p0[1] + dr[1] * t), nrm))
                else:
                    a = nrm[0] + (nrm[1] - nrm[0]) * (t / L if L else 0)
                    out.append(((p0[0] + math.cos(a) * rc, p0[1] + math.sin(a) * rc), (math.cos(a), math.sin(a))))
                break
            t -= L
    return [((cx + p[0], cz + p[1]), nr) for p, nr in out]


def face(pts, mat):
    K.quad(pts, mat, sub=None) if len(pts) == 4 else K.tri(pts, mat)


STONES = []


def rock(bi, b):
    x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
    w, d, h = x1 - x0, z1 - z0, y1 - y0; m = min(w, d); cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    big = m > 5
    step = 4.6 if big else 0.6
    n = max(8, min(22, int(2 * (w + d) / step)))
    rc = m * (0.22 if big else 0.34)
    # the levels: (height 0..1, inset as a share of m: negative = out). a mesa steps in ledges; a boulder is a rounded lump
    if big:
        nl = max(4, min(7, int(h / 3.5))); lv = [(0.0, -0.035), (0.05, 0.0)]
        for k in range(1, nl):
            t = k / nl; ins = 0.012 + 0.05 * t + (0.03 if k % 2 else 0.0)
            lv += [(t - 0.012, ins - (0.02 if k % 2 else -0.012)), (t + 0.012, ins)]  # a ledge: the band above sits back (or juts)
        lv += [(0.975, 0.075 + 0.03 * hsh(bi, 9)), (1.0, 0.11 + 0.04 * hsh(bi, 9))]
    else:
        lv = [(0.0, -0.05), (0.14, -0.01), (0.5, 0.05), (0.84, 0.13), (1.0, 0.27)]
    rings = []
    for li, (t, ins) in enumerate(lv):
        top = li == len(lv) - 1
        pts = []
        for i, ((px, pz), (nx, nz)) in enumerate(ring(cx, cz, w / 2, d / 2, rc, n)):
            j = (hsh(bi, i, li // 2) - 0.5) * (0.035 if big else 0.07) + (hsh(bi, i) - 0.5) * (0.03 if big else 0.06)  # a face's own bulge + this band's
            e = (ins + j) * m
            if not top and li: e = max(e, -0.04 * m)
            if li == 0: e = min(e, 0.0)  # the foot only ever spreads
            y = y0 + h * t + (0 if (top or li == 0) else (hsh(bi, i, li, 3) - 0.5) * h * (0.02 if big else 0.05))
            pts.append(Vector((px - nx * e, min(y, y1), pz - nz * e)))
        rings.append(pts)
    cen = Vector((cx, (y0 + y1) / 2, cz))
    for li in range(len(rings) - 1):
        A, B2 = rings[li], rings[li + 1]
        band = 'rockband' if (big and (li // 2) % 2 == 1) or (not big and li == 1 and hsh(bi, 4) < 0.5) else 'rock'
        for i in range(n):
            j = (i + 1) % n
            q = [A[i], A[j], B2[j], B2[i]]
            nrm = (q[1] - q[0]).cross(q[2] - q[0])
            if nrm.dot((q[0] + q[2]) / 2 - cen) < 0: q = q[::-1]
            face(q, band)
    T = rings[-1]; tc = Vector((cx, y1, cz))
    for i in range(n):
        t3 = [tc, T[i], T[(i + 1) % n]]
        if (t3[1] - t3[0]).cross(t3[2] - t3[0]).y < 0: t3 = t3[::-1]
        face(t3, 'rocktop')
    # loose stones round the foot: little wedges, more round a mesa
    for k in range(int(5 + 6 * hsh(bi, 20)) if big else int(1 + 3 * hsh(bi, 21))):
        a = hsh(bi, k, 30) * math.pi * 2; rr = (0.9 + 0.5 * hsh(bi, k, 31)) if big else (0.55 + 0.35 * hsh(bi, k, 31))
        sx, sz = cx + math.cos(a) * w * rr * 0.62, cz + math.sin(a) * d * rr * 0.62
        if x0 - 0.02 < sx < x1 + 0.02 and z0 - 0.02 < sz < z1 + 0.02: continue
        s = (0.6 + 1.6 * hsh(bi, k, 32)) if big else (0.1 + 0.16 * hsh(bi, k, 32))
        if any((sx - px) ** 2 + (sz - pz) ** 2 < (s + ps) ** 2 for px, pz, ps in STONES): continue  # (no two stones through each other)
        STONES.append((sx, sz, s))
        yaw = hsh(bi, k, 33) * 6.28
        base = [Vector((sx + math.cos(yaw + q * 2.1 + 0.3 * hsh(bi, k, q)) * s, y0 - 0.03 + 0.004 * k + 0.002 * (bi % 7), sz + math.sin(yaw + q * 2.1 + 0.3 * hsh(bi, k, q)) * s * 0.8)) for q in range(3)]  # (each stone's foot at its own height: two that overlap never share a plane)
        apex = Vector((sx + (hsh(bi, k, 34) - 0.5) * s * 0.5, y0 + s * (0.5 + 0.4 * hsh(bi, k, 35)), sz + (hsh(bi, k, 36) - 0.5) * s * 0.5))
        for q in range(3):
            t3 = [base[q], base[(q + 1) % 3], apex]
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot(apex + Vector((0, -s, 0)) - Vector((sx, y0, sz))) > 0: t3 = t3[::-1]
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - Vector((sx, y0 + s * 0.2, sz))) < 0: t3 = t3[::-1]
            face(t3, 'scree')


for bi, b in enumerate(K.boxes):
    b['_done'] = True
    rock(bi, b)
K.solids = []  # (the boxes aren't drawn: nothing to cull against, and the AO is the rock's own)
K.finish(OUT)
