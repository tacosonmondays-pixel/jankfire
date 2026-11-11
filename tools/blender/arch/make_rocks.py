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
         'forest': ('#7c8088', '#5c6068', '#6a8a4a', '#70747a'),  # (the forest's tops are mossy)
         'islands': ('#8f887a', '#6c665c', '#a8a08c', '#7e786c')}
BASALT = ('#75687f', '#4e4358', '#85788c', '#62566c')  # volcano rock (boxes of 'basalt'): its own four, names with a b
c = STONE.get(MAP.replace('_sd', ''), STONE['desert'])
for pre, cc in (('', c), ('b', BASALT)):
    MATS.update({pre + 'rock': ('stucco', cc[0], {}), pre + 'rockband': ('stucco', cc[1], {}), pre + 'rocktop': ('stucco', cc[2], {}), pre + 'scree': ('stucco', cc[3], {})})
    NOCAST.add(pre + 'scree')
MATS['bcrack'] = ('stucco', '#ff7a30', {}); NOCAST.add('bcrack')  # the cracks still warm
import json
AVOID = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boxes', 'rocks_%s.json' % MAP))).get('avoid', [])

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


def held(sx, sz, s, y):
    """is there a rock top at height y under the whole of a stone here? (stones on a terrace: none hanging off its edge or over the throat)"""
    return any(abs(o['max'][1] - y) < 0.01 and o['min'][0] < sx - s and sx + s < o['max'][0] and o['min'][2] < sz - s and sz + s < o['max'][2] for o in K.boxes)


def lava(px, pz):
    return any(a['min'][0] - 0.7 < px < a['max'][0] + 0.7 and a['min'][2] - 0.7 < pz < a['max'][2] + 0.7 for a in AVOID)


def terrace(gi, g, tops):
    """a slab of four boxes round a hole (the volcano's terraces), as one piece: its top edge stays exactly on the boxes'
    (you walk to it, stairs meet it), its faces are cut back a hand in strata, a skirt of fallen rock at its foot, flat
    where lava runs down it. its top is open under the terrace above; the throat's walls are flat (the lava fits them)"""
    P = 'b' if g[0]['mat'] == 'basalt' else ''
    x0 = min(b['min'][0] for b in g); x1 = max(b['max'][0] for b in g); z0 = min(b['min'][2] for b in g); z1 = max(b['max'][2] for b in g)
    y0, y1 = g[0]['min'][1], g[0]['max'][1]; w, d, h = x1 - x0, z1 - z0, y1 - y0; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    xs = sorted({v for b in g for v in (b['min'][0], b['max'][0])}); zs = sorted({v for b in g for v in (b['min'][2], b['max'][2])})
    gap = [(xs[i], zs[j], xs[i + 1], zs[j + 1]) for i in range(len(xs) - 1) for j in range(len(zs) - 1)
           if not any(b['min'][0] <= xs[i] and xs[i + 1] <= b['max'][0] and b['min'][2] <= zs[j] and zs[j + 1] <= b['max'][2] for b in g)]
    hole = (min(q[0] for q in gap), min(q[1] for q in gap), max(q[2] for q in gap), max(q[3] for q in gap)) if gap else None
    n = max(16, int(2 * (w + d) / 1.5)); R = ring(cx, cz, w / 2, d / 2, 0.6, n)
    lv = [(0.0, -0.45), (0.1, -0.28), (0.28, -0.05), (0.33, 0.07), (0.6, 0.03), (0.64, 0.13), (0.9, 0.06), (0.95, 0.0), (1.0, 0.0)]
    rings = []
    for li, (t, e0) in enumerate(lv):
        pts = []
        for i, ((px, pz), (nx, nz)) in enumerate(R):
            if li == len(lv) - 1: e = 0.0
            else:
                e = e0 + (hsh(gi, i, 7) - 0.5) * 0.14 + (hsh(gi, i, li, 8) - 0.5) * 0.1
                e = min(e, -0.02) if e0 < 0 else min(max(e, 0.0), 0.25)
                if li == len(lv) - 2: e = min(e, 0.06)
                if lava(px, pz): e = min(max(e, 0.0), 0.02)
            y = y0 - 0.02 if li == 0 else y0 + h * t + (0 if li >= len(lv) - 2 else (hsh(gi, i, li, 3) - 0.5) * 0.14)
            pts.append(Vector((px - nx * e, y, pz - nz * e)))
        rings.append(pts)
    cen = Vector((cx, (y0 + y1) / 2, cz))

    def tq(q, m):  # a side quad as two triangles, facing out
        if (q[1] - q[0]).cross(q[2] - q[0]).dot((q[0] + q[2]) / 2 - cen) < 0: q = q[::-1]
        face([q[0], q[1], q[2]], m); face([q[0], q[2], q[3]], m)
    for li in range(len(rings) - 1):
        A, B2 = rings[li], rings[li + 1]
        for i in range(n):
            j = (i + 1) % n; m = P + ('rockband' if li in (3, 6) else 'rock')
            if P and li in (2, 3, 4, 5) and hsh(gi, i, li, 40) < 0.22:  # a crack still warm: a sliver cut into the face
                s0 = 0.25 + 0.5 * hsh(gi, i, li, 41); s1 = min(0.9, max(0.1, s0 + (hsh(gi, i, li, 42) - 0.5) * 0.5)); dw = 0.035 / max(0.3, (A[j] - A[i]).length)
                a0, a1, b0, b1 = A[i].lerp(A[j], s0 - dw), A[i].lerp(A[j], s0 + dw), B2[i].lerp(B2[j], s1 - dw), B2[i].lerp(B2[j], s1 + dw)
                tq([A[i], a0, b0, B2[i]], m); tq([a0, a1, b1, b0], 'bcrack'); tq([a1, A[j], B2[j], b1], m)
            else: tq([A[i], A[j], B2[j], B2[i]], m)
    # the top: from its edge in to the terrace above (a bit under it), or to the throat
    up = [o for o in tops if abs(o[4] - y1) < 0.01 and x0 < o[0] and o[2] < x1 and z0 < o[1] and o[3] < z1]
    inner = (up[0][0] + 0.3, up[0][1] + 0.3, up[0][2] - 0.3, up[0][3] - 0.3) if up else hole

    def loop(rct, y, step=1.5):
        a0, c0, a1, c1 = rct; out = []
        for (p, q) in (((a1, c1), (a0, c1)), ((a0, c1), (a0, c0)), ((a0, c0), (a1, c0)), ((a1, c0), (a1, c1))):
            k = max(1, int(math.hypot(q[0] - p[0], q[1] - p[1]) / step))
            out += [Vector((p[0] + (q[0] - p[0]) * i / k, y, p[1] + (q[1] - p[1]) * i / k)) for i in range(k)]
        return out
    if inner:
        ic = ((inner[0] + inner[2]) / 2, (inner[1] + inner[3]) / 2); ang = lambda v: math.atan2(v.z - ic[1], v.x - ic[0])
        O = sorted(rings[-1], key=ang); I = sorted(loop(inner, y1), key=ang); no, ni = len(O), len(I)
        k0 = max([k for k in range(ni) if ang(I[k]) <= ang(O[0])] or [ni - 1]); I = I[k0:] + I[:k0]  # start the inner loop just behind the outer's first point
        ao = [ang(v) for v in O]; ai = []
        for v in I:
            t = ang(v)
            while ai and t < ai[-1]: t += 2 * math.pi
            ai.append(t)
        if ai[0] > ao[0]: ai = [t - 2 * math.pi for t in ai]
        ao.append(ao[0] + 2 * math.pi); ai.append(ai[0] + 2 * math.pi)
        i = j = 0; ck = 0
        while i < no or j < ni:
            if j >= ni or (i < no and ao[i + 1] <= ai[j + 1]): t3 = [O[i % no], O[(i + 1) % no], I[j % ni]]; i += 1; outer = True
            else: t3 = [O[i % no], I[(j + 1) % ni], I[j % ni]]; j += 1; outer = False
            def up3(t, m):
                nyy = (t[1] - t[0]).cross(t[2] - t[0]).y
                if (t[1] - t[0]).cross(t[2] - t[0]).y < 0: t = t[::-1]
                face(t, m)
            ck += 1
            if P and outer and hsh(gi, ck, 50) < 0.3 and not lava(t3[0].x, t3[0].z):  # a crack in the top, from its edge inward
                v0, v1, v2 = t3; s0 = 0.3 + 0.4 * hsh(gi, ck, 51); dw = 0.04 / max(0.3, (v1 - v0).length)
                pa, pb = v0.lerp(v1, s0 - dw), v0.lerp(v1, s0 + dw); tip = v0.lerp(v1, 0.2 + 0.6 * hsh(gi, ck, 52)).lerp(v2, 0.12 + 0.2 * hsh(gi, ck, 53))
                up3([v0, pa, tip], P + 'rocktop'); up3([pa, pb, tip], 'bcrack'); up3([pb, v1, tip], P + 'rocktop'); up3([v0, tip, v2], P + 'rocktop'); up3([tip, v1, v2], P + 'rocktop')
            else: up3(t3, P + 'rocktop')
    if hole:  # the throat's walls
        hc = Vector(((hole[0] + hole[2]) / 2, 0, (hole[1] + hole[3]) / 2)); L = loop(hole, 0, step=9)
        for k in range(len(L)):
            a, b2 = L[k], L[(k + 1) % len(L)]
            for (ya, yb, m) in ((y0, y0 + h * 0.45, 'rockband'), (y0 + h * 0.45, y1, 'rock')):
                q = [Vector((a.x, ya, a.z)), Vector((b2.x, ya, b2.z)), Vector((b2.x, yb, b2.z)), Vector((a.x, yb, a.z))]
                if (q[1] - q[0]).cross(q[2] - q[0]).dot(hc - Vector(((a.x + b2.x) / 2, 0, (a.z + b2.z) / 2))) < 0: q = q[::-1]
                face(q, P + m)


def sats(bi, b):
    """smaller rocks lying by a boulder, mostly to one side, from a fist to a seat: so a beach isn't six of the same rock"""
    x0, y0, z0 = b['min']; x1, y1, z1 = b['max']; w, d = x1 - x0, z1 - z0; cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; m = min(w, d)
    a0 = hsh(bi, 80) * 6.283
    for k in range(int(2 + 5 * hsh(bi, 81))):
        a = a0 + (hsh(bi, k, 82) - 0.5) * 2.6; s = min(1.0, m / 2) * (0.1 + 0.5 * hsh(bi, k, 83) ** 2.2); rr = 0.6 + 0.2 * k * hsh(bi, k, 84) + s
        sx, sz = cx + math.cos(a) * (w / 2 * 1.05 + rr * 0.5), cz + math.sin(a) * (d / 2 * 1.05 + rr * 0.5)
        if x0 - s < sx < x1 + s and z0 - s * 0.8 < sz < z1 + s * 0.8: continue
        if y0 > 0.5 and not held(sx, sz, s, y0): continue
        if any((sx - px) ** 2 + (sz - pz) ** 2 < (s + ps) ** 2 for px, pz, ps in STONES): continue
        STONES.append((sx, sz, s)); sq = 0.7 + 0.25 * hsh(bi, k, 85)
        rock(bi * 31 + k + 5, {'min': [sx - s, y0 - 0.06 - 0.003 * (k % 5), sz - s * sq], 'max': [sx + s, y0 + s * (0.8 + 0.7 * hsh(bi, k, 86)), sz + s * sq], 'mat': b['mat'], '_sub': 1})


def rock(bi, b):
    P = 'b' if b['mat'] == 'basalt' else ''
    x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
    w, d, h = x1 - x0, z1 - z0, y1 - y0; m = min(w, d); cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    big = m > 5
    step = 4.6 if big else 0.6
    n = max(8, min(22, int(2 * (w + d) / step)))
    rc = m * (0.22 if big else 0.34)
    sub = b.get('_sub'); nat = not big and max(w, d) <= 2.5 * m  # an ordinary boulder: no two alike
    kind = int(hsh(bi, 70) * 10)  # 0-3 a lump, 4-6 a big one with a shoulder against it, 7-9 a leaning slab
    if nat and not sub and kind in (4, 5, 6) and m > 0.9:
        f = 0.6 + 0.12 * hsh(bi, 73); lo = hsh(bi, 74) < 0.5; hs = h * (0.38 + 0.25 * hsh(bi, 75)); k2 = 0.12 + 0.12 * hsh(bi, 76)
        if w >= d:
            xa, xb = (x0, x0 + w * f) if lo else (x1 - w * f, x1); sa, sb = (x0 + w * (f - 0.16), x1) if lo else (x0, x1 - w * (f - 0.16))
            rock(bi * 7 + 1, {'min': [xa, y0, z0], 'max': [xb, y1, z1], 'mat': b['mat'], '_sub': 1})
            rock(bi * 7 + 2, {'min': [sa, y0, z0 + d * k2], 'max': [sb, y0 + hs, z1 - d * (0.24 - k2)], 'mat': b['mat'], '_sub': 1})
        else:
            za, zb = (z0, z0 + d * f) if lo else (z1 - d * f, z1); sa, sb = (z0 + d * (f - 0.16), z1) if lo else (z0, z1 - d * (f - 0.16))
            rock(bi * 7 + 1, {'min': [x0, y0, za], 'max': [x1, y1, zb], 'mat': b['mat'], '_sub': 1})
            rock(bi * 7 + 2, {'min': [x0 + w * k2, y0, sa], 'max': [x1 - w * (0.24 - k2), y0 + hs, sb], 'mat': b['mat'], '_sub': 1})
        sats(bi, b); return
    la = hsh(bi, 77) * 6.283; ll = m * ((0.2 if kind >= 7 else 0.08) if nat else 0.0); lx, lz = math.cos(la) * ll, math.sin(la) * ll  # which way it leans, how far
    p1, p2 = hsh(bi, 71) * 6.283, hsh(bi, 72) * 6.283
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
            if nat and li:  # an uneven outline: two or three lobes, never a rounded box
                ang = 6.283 * i / n; e += m * (0.09 * math.sin(2 * ang + p1) + 0.06 * math.sin(3 * ang + p2)) * (0.0 if top else 1.0) + (m * 0.05 if top and kind >= 7 else 0)
                e = min(e, 0.95 * rc)  # (never cut back past its rounded corners: the ring would fold)
            if not top and li: e = max(e, -0.04 * m)
            if li == 0: e = min(e, 0.0)  # the foot only ever spreads
            if max(w, d) > 2.5 * m: e = min(e, 0.7 * rc)  # (a long thin one, a rim or a lip: never cut back past its rounded ends, the top would fold)
            y = y0 + h * t + (0 if (top or li == 0) else (hsh(bi, i, li, 3) - 0.5) * h * (0.02 if big else 0.05))
            sh = t ** 1.5 * min(1.0, max(0.0, e) / ll) if ll > 1e-6 else 0.0  # (it leans only as far as it's cut back: it stays inside its box)
            pts.append((Vector((px - nx * e, min(y, y1), pz - nz * e)), sh))
        st = min(q[1] for q in pts)  # (the top moves over as one piece, or its fan folds)
        pts = [v + Vector((lx, 0, lz)) * (st if top else q) for v, q in pts]
        rings.append(pts)
    cen = Vector((cx, (y0 + y1) / 2, cz))
    for li in range(len(rings) - 1):
        A, B2 = rings[li], rings[li + 1]
        band = P + 'rockband' if (big and (li // 2) % 2 == 1) or (not big and li == 1 and hsh(bi, 4) < 0.5) else P + 'rock'
        for i in range(n):
            j = (i + 1) % n
            q = [A[i], A[j], B2[j], B2[i]]
            nrm = (q[1] - q[0]).cross(q[2] - q[0])
            if nrm.dot((q[0] + q[2]) / 2 - cen) < 0: q = q[::-1]
            if big: face(q, band)
            else: face([q[0], q[1], q[2]], band); face([q[0], q[2], q[3]], band)  # (a boulder's faces as triangles: they twist)
    T = rings[-1]; tc = Vector((sum(v.x for v in T) / n, y1, sum(v.z for v in T) / n))
    for i in range(n):
        t3 = [tc, T[i], T[(i + 1) % n]]
        if (t3[1] - t3[0]).cross(t3[2] - t3[0]).y < 0: t3 = t3[::-1]
        face(t3, P + 'rocktop')
    if sub: return
    if nat: sats(bi, b); return
    # loose stones round the foot: little wedges, more round a mesa
    for k in range(int(5 + 6 * hsh(bi, 20)) if big else int(1 + 3 * hsh(bi, 21))):
        a = hsh(bi, k, 30) * math.pi * 2; rr = (0.9 + 0.5 * hsh(bi, k, 31)) if big else (0.55 + 0.35 * hsh(bi, k, 31))
        sx, sz = cx + math.cos(a) * w * rr * 0.62, cz + math.sin(a) * d * rr * 0.62
        if x0 - 0.02 < sx < x1 + 0.02 and z0 - 0.02 < sz < z1 + 0.02: continue
        s = (0.6 + 1.6 * hsh(bi, k, 32)) if big else (0.1 + 0.16 * hsh(bi, k, 32))
        if y0 > 0.5 and not held(sx, sz, s, y0): continue
        if any((sx - px) ** 2 + (sz - pz) ** 2 < (s + ps) ** 2 for px, pz, ps in STONES): continue  # (no two stones through each other)
        STONES.append((sx, sz, s))
        yaw = hsh(bi, k, 33) * 6.28
        base = [Vector((sx + math.cos(yaw + q * 2.1 + 0.3 * hsh(bi, k, q)) * s, y0 - 0.03 + 0.004 * k + 0.002 * (bi % 7), sz + math.sin(yaw + q * 2.1 + 0.3 * hsh(bi, k, q)) * s * 0.8)) for q in range(3)]  # (each stone's foot at its own height: two that overlap never share a plane)
        apex = Vector((sx + (hsh(bi, k, 34) - 0.5) * s * 0.5, y0 + s * (0.5 + 0.4 * hsh(bi, k, 35)), sz + (hsh(bi, k, 36) - 0.5) * s * 0.5))
        for q in range(3):
            t3 = [base[q], base[(q + 1) % 3], apex]
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot(apex + Vector((0, -s, 0)) - Vector((sx, y0, sz))) > 0: t3 = t3[::-1]
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - Vector((sx, y0 + s * 0.2, sz))) < 0: t3 = t3[::-1]
            face(t3, P + 'scree')


# slabs first: four boxes of one height round a hole are one terrace
groups = {}
for b in K.boxes: groups.setdefault((b['mat'], b['min'][1], b['max'][1]), []).append(b)
TER = []
for key, g in groups.items():
    left = list(g)
    while left:
        grp = [left.pop()]; grew = True
        while grew:
            grew = False
            for o in left[:]:
                if any(o['min'][0] <= q['max'][0] + 1e-3 and q['min'][0] <= o['max'][0] + 1e-3 and o['min'][2] <= q['max'][2] + 1e-3 and q['min'][2] <= o['max'][2] + 1e-3 for q in grp): grp.append(o); left.remove(o); grew = True
        bx = (min(q['min'][0] for q in grp), min(q['min'][2] for q in grp), max(q['max'][0] for q in grp), max(q['max'][2] for q in grp))
        if len(grp) == 4 and min(bx[2] - bx[0], bx[3] - bx[1]) > 8 and key[2] - key[1] > 2: TER.append((grp, bx + (key[1],)))
for gi, (grp, bx) in enumerate(TER):
    for b in grp: b['_ter'] = True
    terrace(gi + 100, grp, [t[1] for t in TER])
for bi, b in enumerate(K.boxes):
    b['_done'] = True
    if not b.get('_ter'): rock(bi, b)
K.solids = []  # (the boxes aren't drawn: nothing to cull against, and the AO is the rock's own)
K.finish(OUT)
