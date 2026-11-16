# Z-fight fix for the Blender kits (rooftop2_models.py, rooftop3_models.py): run on PIECES just before flush().
# Two pieces of different looks whose faces lie in one plane (within TOL), face the same way and overlap flicker in
# Roblox: the GPU cannot tell which is in front. For each such pair the piece with the SMALLER face in that plane (the
# trim, the inlay, the tile, the band: the detail meant to be seen) has that face pushed out along its normal until it
# stands EPS proud of the other one. On faces pointing down (undersides) the smaller one steps back EPS behind the
# bigger one instead (16 Nov: the penthouse's tile bottoms had won over the grout slab and darkened a ceiling). Pieces only move by a few hundredths of a stud, so look and layout are unchanged;
# collision is not in the kit (hit boxes are separate parts), so nothing a player touches moves.
# Pieces of kind "water" never move (the v3 pool stays exactly as it is: memory keep-v3-pool-water).
#   group(model) -> a key: only models that stand in the same frame in Studio are compared with each other (v2's tower
#   designs r2_tw* are each placed on their own round the city, so each is its own group).
import math
from collections import defaultdict
from mathutils import Vector

EPS, TOL, MIN_AREA = 0.04, 0.02, 0.01

def _tris(PIECES, group):
    out = []  # (a, b, c, n, d, pid, mn, mx, area)
    pieces = []
    for (model, look), items in sorted(PIECES.items()):
        g = group(model)
        for bm, M in items:
            pid = len(pieces)
            pieces.append((model, look, bm, M, g))
            bm.verts.ensure_lookup_table()
            W = [M @ v.co for v in bm.verts]
            for lt in bm.calc_loop_triangles():
                a, b, c = W[lt[0].vert.index], W[lt[1].vert.index], W[lt[2].vert.index]
                cr = (b - a).cross(c - a)
                m = cr.length
                if m < MIN_AREA * 2:
                    continue
                n = cr / m
                out.append((a, b, c, n, n.dot(a), pid,
                            (min(a.x, b.x, c.x), min(a.y, b.y, c.y), min(a.z, b.z, c.z)),
                            (max(a.x, b.x, c.x), max(a.y, b.y, c.y), max(a.z, b.z, c.z)), m / 2))
    return pieces, out

def _overlap(A, B):
    o, n = A[0], A[3]
    u = (A[1] - o).normalized(); w = n.cross(u)
    pr = lambda p: (u.dot(p - o), w.dot(p - o))
    clip = [pr(A[0]), pr(A[1]), pr(A[2])]
    poly = [pr(B[0]), pr(B[1]), pr(B[2])]
    for i in range(3):
        p1, p2 = clip[i], clip[(i + 1) % 3]
        ex, ey = p2[0] - p1[0], p2[1] - p1[1]
        out = []
        for j in range(len(poly)):
            cur, nxt = poly[j], poly[(j + 1) % len(poly)]
            sc = ex * (cur[1] - p1[1]) - ey * (cur[0] - p1[0])
            sn = ex * (nxt[1] - p1[1]) - ey * (nxt[0] - p1[0])
            if sc >= -1e-7: out.append(cur)
            if (sc >= -1e-7) != (sn >= -1e-7):
                t = sc / (sc - sn)
                out.append((cur[0] + (nxt[0] - cur[0]) * t, cur[1] + (nxt[1] - cur[1]) * t))
        poly = out
        if not poly: return 0.0
    if len(poly) < 3: return 0.0
    ar = 0.0
    for j in range(len(poly)):
        p, q = poly[j], poly[(j + 1) % len(poly)]
        ar += p[0] * q[1] - q[0] * p[1]
    return abs(ar) / 2

def find(PIECES, group=lambda m: 'all'):
    """-> pieces, hits {(pid_a, pid_b, nkey): [area, n, d_a, d_b]}, plane areas {(pid, nkey, dkey): area}"""
    pieces, tris = _tris(PIECES, group)
    looks = [p[1] for p in pieces]
    groups = [p[4] for p in pieces]
    buckets = defaultdict(list)
    plane_area = defaultdict(float)
    for t in tris:
        n = t[3]
        nk = (round(n.x * 20), round(n.y * 20), round(n.z * 20))
        buckets[(groups[t[5]], nk, math.floor(t[4] / 0.1))].append(t)
        plane_area[(t[5], nk, round(t[4] / TOL))] += t[8]
    hits = {}
    def cmp(L1, L2, same):
        L = [(t, 1) for t in L1] + ([] if same else [(t, 2) for t in L2])
        if len({looks[t[5]] for t, _ in L}) < 2: return
        L.sort(key=lambda e: e[0][6][0])
        for i in range(len(L)):
            A, ta = L[i]
            ax = A[7][0] + TOL
            for j in range(i + 1, len(L)):
                B, tb = L[j]
                if B[6][0] > ax: break
                if B[5] == A[5] or looks[B[5]] == looks[A[5]] or (not same and ta == tb): continue
                if B[6][1] > A[7][1] + TOL or B[7][1] < A[6][1] - TOL or B[6][2] > A[7][2] + TOL or B[7][2] < A[6][2] - TOL: continue
                n = A[3]
                if n.dot(B[3]) <= 0.999: continue
                if max(abs(n.dot(B[k] - A[0])) for k in range(3)) > TOL: continue
                ar = _overlap(A, B)
                if ar <= 1e-4: continue
                nk = (round(n.x * 20), round(n.y * 20), round(n.z * 20))
                key = (A[5], B[5], nk) if A[5] < B[5] else (B[5], A[5], nk)
                r = hits.get(key)
                if not r:
                    da, db = (A[4], B[4]) if A[5] < B[5] else (B[4], A[4])
                    na, nb2 = (A[3], B[3]) if A[5] < B[5] else (B[3], A[3])
                    r = hits[key] = [0.0, n, da, db, na, nb2]
                r[0] += ar
    for (g, nk, dk), L in buckets.items():
        cmp(L, L, True)
        nb = buckets.get((g, nk, dk + 1))
        if nb: cmp(L, nb, False)
    hits = {k: v for k, v in hits.items() if v[0] >= MIN_AREA}
    return pieces, hits, plane_area

def fix(PIECES, group=lambda m: 'all', passes=10, log=print):
    total_moved = 0
    by_model = defaultdict(int)
    for ps in range(passes):
        pieces, hits, plane_area = find(PIECES, group)
        log('ZFIX pass %d: %d coplanar pairs of different looks (%.1f sq studs)' % (ps + 1, len(hits), sum(h[0] for h in hits.values())))
        if not hits:
            log('ZFIX faces pushed per model: ' + ', '.join('%s %d' % kv for kv in sorted(by_model.items())))
            return total_moved
        need = {}  # (pid, nkey, d) -> (n, push)
        for (pa, pb, nk), (ar, n, da, db, na, nb) in hits.items():
            sa = plane_area.get((pa, nk, round(da / TOL)), 0.0)
            sb = plane_area.get((pb, nk, round(db / TOL)), 0.0)
            wa = pieces[pa][1].startswith('water_'); wb = pieces[pb][1].startswith('water_')
            if wa and wb: continue
            win = pa if (wb or (not wa and (sa < sb or (sa == sb and pa < pb)))) else pb
            dw, do = (da, db) if win == pa else (db, da)
            nw = na if win == pa else nb   # the winner's own normal: its face is found by it
            # faces pointing DOWN are undersides (a floor's tiles over its grout slab, seen from the room below): there
            # the big face is the one meant to be seen, so the smaller one steps back behind it instead. a light (neon)
            # always stands out
            if n.y < -0.7 and not pieces[win][1].startswith('neon_'):
                push = (do - dw) - EPS
            else:
                push = (do - dw) + EPS
            key = (win, nk, round(dw / 0.005))
            if key not in need or need[key][1] < push:
                need[key] = (nw, push, dw)
        for (pid, nk, _), (n, push, dw) in need.items():
            model, look, bm, M, g = pieces[pid]
            by_model[model] += 1
            Minv = M.inverted().to_3x3()
            dl = Minv @ (n * push)
            for v in bm.verts:
                if abs(n.dot(M @ v.co) - dw) < 0.006:
                    v.co += dl
        total_moved += len(need)
        log('ZFIX pass %d: pushed %d faces out' % (ps + 1, len(need)))
    log('ZFIX faces pushed per model: ' + ', '.join('%s %d' % kv for kv in sorted(by_model.items())))
    pieces, hits, _ = find(PIECES, group)
    log('ZFIX left after %d passes: %d pairs (%.1f sq studs)' % (passes, len(hits), sum(h[0] for h in hits.values())))
    return total_moved
