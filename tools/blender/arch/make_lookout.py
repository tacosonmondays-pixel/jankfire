# The Scary Forest's fire lookout (shared/map.js forest(), `the fire lookout tower`): drawn over its own boxes
# (tools/arch/dump.mjs), which stay what you bump into and climb. A US Forest Service style timber lookout: four heavy
# posts on concrete piers with steel post shoes, girts at every flight, X-braced bays (one brace runs through, the other
# butts into it under a steel gusset plate, a bolted plate over every node), knee braces in the open bottom bay; the
# switchback stair inside: plank treads with nosings on the game's step tops, risers, closed stringers boarded down to
# the flat underside the step boxes have, newel posts and two-rail handrails, landings on joists hung from the girts
# and on steel hanger rods. Up top an L-4 style live-in cab on a beam-and-joist platform: cream lap siding, green trim,
# wraparound windows (open: no glass, the sashes swung out on stays, a shard left here and there), board-and-batten
# storm shutters propped out as awnings (one has slipped), a hip roof with hip caps and a lightning rod with a glass
# ball, its copper down-lead running to a ground rod. Inside: the Osborne fire finder (a round map under a brass ring and
# its sights) on a map cabinet, the glass-footed lightning stool, a cot with a red wool blanket, a lantern still lit,
# the trapdoor hatch stood open. Look only: the walk graph, the physics and the spawn on top are the game's.
# No catwalk: the boxes have no floor round the cab, and a drawn one would be a floor you fall through.
# local frame = the tower's (TWR = 24, -50; the placement rides the forest floor's pad: shared/map.js sets its y).
# run: node tools/arch/dump.mjs forest lookout tools/blender/arch/boxes/lookout.json
#      blender52 -b --python tools/blender/arch/make_lookout.py
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST, KIT
from mathutils import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'lktimber': ('timber', '#b08a62', {}), 'lkdeck': ('planks', '#e6dccc', {}), 'lksteel': ('trim', '#8e939c', {}),
    'lkconc': ('concrete', '#c8c2b6', {}), 'lksiding': ('siding', '#f4ead2', {}), 'lktrim': ('trim', '#3f8c56', {}),
    'lkshut': ('siding', '#469a5e', {}), 'lkroof': ('shingle', '#b44a38', {}), 'lkglass': ('glass', '#ffffff', {}),
    'lklamp': ('stucco', '#ffd27a', {'glow': True, 'glowcol': '#ffbe5a'}), 'lkbrass': ('metalplate', '#e8a850', {}), 'lkmap': ('trim', '#e6dab6', {}),
    'lkcloth': ('stucco', '#b0382e', {}),
})
NOCAST.update({'lksteel', 'lkglass', 'lklamp', 'lkbrass', 'lkmap', 'lkcloth'})
Y = V((0, 1, 0))
TILE = {'lkdeck': 1.0, 'lkroof': 1.0}  # (floorboards 25 cm wide, not the kit's 50; shingles at half size)
HO, HY, SANG = 3.379, 15.62, math.radians(19)  # the storm shutters' hinge line (out, up) and how far below level they're propped
P, PO = 3.1, 3.27            # the posts' centre lines, their outer faces
TOP = 13.2                   # the cab floor
GZ = [2.41, 5.05, 7.69, 10.33, 12.86]   # girt centres on the +-z faces (the last: the cab's x beams)
GX = [2.11, 4.75, 7.39, 10.03, 12.89]   # on the +-x faces (the last: the z beams)


# ------------------------------------------------------------ low level
def newell(pts):
    n = V((0, 0, 0))
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        n += V(((a.y - b.y) * (a.z + b.z), (a.z - b.z) * (a.x + b.x), (a.x - b.x) * (a.y + b.y)))
    return n


def tri_uv(p, mat, uv):
    g = K._bucket(mat); b = len(g['v'])
    for q, t in zip(p, uv): g['v'].append(tuple(q)); g['uv'].append(tuple(t))
    g['f'].append((b, b + 1, b + 2))


def emit(pts, mat, out, along=None, off=(0.0, 0.0), sub=None, tile=None):
    """a flat convex polygon facing `out`; uvs run along `along` (world scale in the kit's tile), or the kit's planar"""
    pts = [V(p) for p in pts]
    n = newell(pts)
    if n.length < 1e-10: return
    if n.dot(out) < 0: pts = pts[::-1]; n = -n
    n.normalize()
    uv = None
    if along is not None:
        al = V(along) - n * V(along).dot(n)
        if al.length > 1e-3 * V(along).length:  # (an end cap square to the member: the kit's planar uvs instead)
            al.normalize(); c = n.cross(al); T = tile or TILE.get(mat) or KIT[MATS[mat][0]]['tile'] or 1.0
            uv = [(p.dot(c) / T + off[0], p.dot(al) / T + off[1]) for p in pts]
    if len(pts) == 4: K.quad(pts, mat, uv=uv, sub=sub, tile=tile or TILE.get(mat))
    elif uv:
        for i in range(1, len(pts) - 1): tri_uv([pts[0], pts[i], pts[i + 1]], mat, [uv[0], uv[i], uv[i + 1]])
    else:
        for i in range(1, len(pts) - 1): K.tri([pts[0], pts[i], pts[i + 1]], mat)


def prism(poly, d, mat, along=None, skip=(), seg=1, cap_mat=None, off=None):
    """a convex polygon (3d, planar) pushed by vector d: its sides (split in seg along d) and two caps. skip: 'a' (the
    cap at poly), 'b' (the far cap), or side indices i (the side from poly[i] to poly[i+1])"""
    poly = [V(p) for p in poly]; d = V(d); n = len(poly)
    C = sum(poly, V()) / n + d / 2
    off = off if off is not None else (K.rng.random(), K.rng.random())
    for i in range(n):
        if i in skip: continue
        a, b = poly[i], poly[(i + 1) % n]
        for k in range(seg):
            t0, t1 = k / seg, (k + 1) / seg
            q = [a + d * t0, b + d * t0, b + d * t1, a + d * t1]
            emit(q, mat, sum(q, V()) / 4 - C, along=along if along is not None else d, off=off)
    if 'a' not in skip: emit(poly, cap_mat or mat, -d, along=along, off=off)
    if 'b' not in skip: emit([p + d for p in poly], cap_mat or mat, d, along=along, off=off)


def member(a, b, w, h, mat, side=None, ch=0.0, skip=(), seg=1):
    """a timber from a to b (its centre line): w across (along `side`, horizontal by default), h the other way,
    edges chamfered ch. uvs along it, so the grain runs down every member"""
    a, b = V(a), V(b); d = b - a
    if d.length < 1e-5: return
    u = d.normalized()
    s = V(side) if side is not None else (u.cross(Y) if abs(u.y) < 0.95 else V((1, 0, 0)))
    s = (s - u * s.dot(u)).normalized(); t = u.cross(s).normalized()
    hw, hh = w / 2, h / 2
    if ch > 0: prof = [(hw - ch, hh), (hw, hh - ch), (hw, -hh + ch), (hw - ch, -hh), (-hw + ch, -hh), (-hw, -hh + ch), (-hw, hh - ch), (-hw + ch, hh)]
    else: prof = [(hw, hh), (hw, -hh), (-hw, -hh), (-hw, hh)]
    prism([a + s * x + t * y for (x, y) in prof], d, mat, along=d, skip=skip, seg=seg)


def bolt(p, n, a, s=0.045, h=0.024, mat='lksteel'):
    """a bolt head on a surface (outward n, edges along a): a low square dome, four triangles"""
    p, n, a = V(p), V(n).normalized(), V(a)
    a = (a - n * a.dot(n)).normalized(); b = n.cross(a)
    base = [p - n * 0.001 + (a * x + b * y) * (s / 2) for (x, y) in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
    tip = p + n * h
    for i in range(4): emit([base[i], base[(i + 1) % 4], tip], mat, (base[i] + base[(i + 1) % 4]) / 2 + n * (h / 3) - p)


def rod(a, b, r0, r1, mat, n=6):
    """a six-sided rod (r1 = 0: a point), uvs along it"""
    a, b = V(a), V(b); d = (b - a).normalized()
    u = d.cross(Y if abs(d.y) < 0.9 else V((1, 0, 0))).normalized(); w = d.cross(u)
    R = lambda c, r: [c + (u * math.cos(math.tau * i / n) + w * math.sin(math.tau * i / n)) * r for i in range(n)]
    A, B = R(a, r0), R(b, r1)
    for i in range(n):
        j = (i + 1) % n; o = (A[i] + A[j]) / 2 - a
        if r1 > 1e-5: emit([A[i], A[j], B[j], B[i]], mat, o, along=d)
        else: emit([A[i], A[j], b], mat, o, along=d)


def clip(poly, planes):
    """a convex 2d polygon [(x, y)] cut by half-planes (a, b, c): keeps a*x + b*y <= c"""
    for (a, b, c) in planes:
        out = []
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
            if fp <= 0: out.append(p)
            if (fp < 0 < fq) or (fq < 0 < fp):
                t = fp / (fp - fq); out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        poly = out
        if len(poly) < 3: return []
    return poly


def band(p0, p1, w):
    """a long 2d strip w wide along the line p0 -> p1 (past both ends), and its unit direction and normal"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L; nx, ny = -uy, ux
    e = 3.0
    pts = [(p0[0] - ux * e + nx * w / 2, p0[1] - uy * e + ny * w / 2), (p1[0] + ux * e + nx * w / 2, p1[1] + uy * e + ny * w / 2),
           (p1[0] + ux * e - nx * w / 2, p1[1] + uy * e - ny * w / 2), (p0[0] - ux * e - nx * w / 2, p0[1] - uy * e - ny * w / 2)]
    return pts, (ux, uy), (nx, ny)


# ------------------------------------------------------------ the tower's faces: n out, a along it
FACES = [(V((0, 0, 1)), V((1, 0, 0)), GZ), (V((0, 0, -1)), V((1, 0, 0)), GZ), (V((1, 0, 0)), V((0, 0, 1)), GX), (V((-1, 0, 0)), V((0, 0, 1)), GX)]


def FP(n, a, s, y, o): return a * s + Y * y + n * o


def face_piece(n, a, poly2, o0, o1, mat, along2=None, skip=()):
    """a 2d polygon on a tower face (s along it, y up) as a plate from o0 to o1 out"""
    pts = [FP(n, a, s, y, o0) for (s, y) in poly2]
    al = None if along2 is None else a * along2[0] + Y * along2[1]
    prism(pts, n * (o1 - o0), mat, along=al, skip=skip)


def bracing():
    BW, BT, G = 0.16, 0.06, 0.003   # brace width, thickness, the gap where they butt
    o0, o1 = PO + 0.001, PO + 0.001 + BT
    for fi, (n, a, L) in enumerate(FACES):
        for i in range(4):
            y0, y1 = L[i], L[i + 1]
            # the through brace: from the foot of one post to the head of the other, plumb cut short of the posts' edges,
            # cut level at the girt lines (the next bay's braces butt it there)
            c1 = ((-P, y0), (P, y1)) if (fi + i) % 2 == 0 else ((P, y0), (-P, y1))
            c2 = ((c1[0][0] * -1, y0), (c1[1][0] * -1, y1))
            lim = [(1, 0, 3.22), (-1, 0, 3.22), (0, -1, -(y0 + G)), (0, 1, y1 - G)]
            b1, u1, n1 = band(c1[0], c1[1], BW)
            poly = clip(b1, lim)
            face_piece(n, a, poly, o0, o1, 'lktimber', along2=u1)
            # the other: two halves butting into it
            b2, u2, n2 = band(c2[0], c2[1], BW)
            mx, my = (c1[0][0] + c1[1][0]) / 2, (y0 + y1) / 2
            k = n1[0] * mx + n1[1] * my
            for sg in (1, -1):  # keep the side of the through brace: n1 . p >= k + BW/2 + G (or <= k - ...)
                h = (-sg * n1[0], -sg * n1[1], -sg * k - BW / 2 - G)
                poly2 = clip(b2, lim + [h])
                if poly2: face_piece(n, a, poly2, o0, o1, 'lktimber', along2=u2)
            # the gusset plate over the crossing, a bolt through it
            q = [(mx - 0.13, my - 0.13), (mx + 0.13, my - 0.13), (mx + 0.13, my + 0.13), (mx - 0.13, my + 0.13)]
            face_piece(n, a, q, o1, o1 + 0.012, 'lksteel', skip=('a',))
            bolt(FP(n, a, mx, my, o1 + 0.012), n, Y, s=0.06, h=0.03)
        # a steel plate over every node where braces meet a post, two bolts up it
        for s in (-P, P):
            for j, y in enumerate(L):
                h0, h1 = (y - 0.24, y + 0.24) if 0 < j < 4 else ((y, y + 0.34) if j == 0 else (y - 0.34, y))
                q = [(s - 0.14, h0), (s + 0.14, h0), (s + 0.14, h1), (s - 0.14, h1)]
                face_piece(n, a, q, o1, o1 + 0.012, 'lksteel', skip=('a',))
                for by in ((h0 + 0.09, h1 - 0.09) if j in (0, 4) else (y - 0.15, y + 0.15)): bolt(FP(n, a, s, by, o1 + 0.012), n, Y)
        # the open bottom bay: knee braces in the girts' plane, from each post up under the girt
        g0 = L[0] - 0.07
        for sg in (-1, 1):
            pa, pb = (sg * 2.93, g0 - 0.62), (sg * 2.31, g0)
            b3, u3, _ = band(pa, pb, 0.11)
            poly = clip(b3, [(sg, 0, 2.93), (0, 1, g0)])  # (cut against the post's face and the girt's underside)
            face_piece(n, a, poly, P - 0.06, P + 0.06, 'lktimber', along2=u3)
            bolt(FP(n, a, pa[0] - sg * 0.12, pa[1] + 0.1, P + 0.06), n, Y, s=0.035, h=0.016)


def posts():
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * P, sz * P
            # the pier: a concrete block down into the ground, a sloped wash on top
            K.box((cx - 0.33, -0.7, cz - 0.33), (cx + 0.33, 0.26, cz + 0.33), {'side': 'lkconc'}, cull=False)
            r0, r1 = 0.33, 0.27
            ring0 = [V((cx + x * r0, 0.26, cz + z * r0)) for (x, z) in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
            ring1 = [V((cx + x * r1, 0.33, cz + z * r1)) for (x, z) in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
            for i in range(4):
                q = [ring0[i], ring0[(i + 1) % 4], ring1[(i + 1) % 4], ring1[i]]
                emit(q, 'lkconc', sum(q, V()) / 4 - V((cx, 0.2, cz)))
            emit(ring1, 'lkconc', Y)
            # the steel shoe: a base plate on four anchor nuts, a sleeve up the post, bolts through it
            FL.obox(K, (cx - 0.24, 0.33, cz - 0.24), (cx + 0.24, 0.355, cz + 0.24), 'lksteel')
            for (x, z) in ((1, 1), (1, -1), (-1, -1), (-1, 1)): bolt((cx + x * 0.19, 0.355, cz + z * 0.19), Y, V((1, 0, 0)), s=0.05, h=0.03)
            FL.obox(K, (cx - 0.19, 0.355, cz - 0.19), (cx + 0.19, 0.78, cz + 0.19), 'lksteel')
            for (nx, nz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                bolt((cx + nx * 0.19, 0.57, cz + nz * 0.19), V((nx, 0, nz)), Y, s=0.05, h=0.025)
            # the post: 34 cm square, chamfered, from the shoe to under the cab's beams
            member((cx, 0.77, cz), (cx, 12.72, cz), 0.34, 0.34, 'lktimber', side=V((1, 0, 0)), ch=0.035, skip=('a', 'b'), seg=6)
    # the fire danger board on the south-west leg, facing the trail in: the five colours of the dial, the needle bent
    # right past the red
    bx, by, bz = -3.1, 1.5, PO + 0.001
    prism([V((bx - 0.36, by - 0.36, bz)), V((bx + 0.36, by - 0.36, bz)), V((bx + 0.36, by + 0.3, bz)), V((bx - 0.36, by + 0.3, bz))], V((0, 0, 0.035)), 'lktimber', along=V((1, 0, 0)), skip=('a',))
    fz = bz + 0.035
    prism([V((bx - 0.33, by - 0.33, fz - 0.001)), V((bx + 0.33, by - 0.33, fz - 0.001)), V((bx + 0.33, by + 0.27, fz - 0.001)), V((bx - 0.33, by + 0.27, fz - 0.001))], V((0, 0, 0.005)), 'lksiding', skip=('a',))
    cy0, R0 = by - 0.2, 0.27
    for k, m in enumerate(('lktrim', 'lkglass', 'lkbrass', 'lkroof', 'lkcloth')):
        a0, a1 = math.pi * (1 - k / 5), math.pi * (1 - (k + 1) / 5)
        pts = [V((bx, cy0, fz + 0.003))] + [V((bx + R0 * math.cos(a0 + (a1 - a0) * t), cy0 + R0 * math.sin(a0 + (a1 - a0) * t), fz + 0.003)) for t in (0, 0.5, 1)]
        prism(pts, V((0, 0, 0.004 + 0.0006 * k)), m, along=V((0, 1, 0)), skip=('a',))  # (each a hair proud of the last: they meet edge to edge)
    member(V((bx, cy0, fz + 0.012)), V((bx + 0.3 * math.cos(-0.32), cy0 + 0.3 * math.sin(-0.32), fz + 0.012)), 0.022, 0.006, 'lksteel')
    bolt((bx, cy0, fz + 0.015), V((0, 0, 1)), Y, s=0.05, h=0.02)
    member(V((bx - 0.41, by + 0.33, bz + 0.05)), V((bx + 0.41, by + 0.33, bz + 0.05)), 0.12, 0.05, 'lktrim', side=V((0, 0, 1)))  # (its little roof)
    # the copper ground rod by the south-east pier, its lead coming down the post's outer corner
    FL.tube(K, (3.62, -0.2, 3.62), (3.62, 0.12, 3.62), 0.022, 0.022, 'lkbrass', n=6)


def girts():
    for (n, a, L) in FACES:
        for y in L[:4]:
            member(FP(n, a, -2.93, y, P), FP(n, a, 2.93, y, P), 0.16, 0.14, 'lktimber', side=n, ch=0.02, skip=('a', 'b'))


def platform():
    """the cab's platform: beams on the posts, joists across, a plank floor with the stairwell, a fascia round it"""
    for sz in (-1, 1): member((-3.4, 12.86, sz * P), (3.4, 12.86, sz * P), 0.34, 0.28, 'lktimber', side=V((0, 0, 1)), ch=0.02, skip=('a', 'b'))
    for sx in (-1, 1): member((sx * P, 12.89, -2.93), (sx * P, 12.89, 2.93), 0.3, 0.22, 'lktimber', side=V((1, 0, 0)), ch=0.02, skip=('a', 'b'))
    for x in (-1.33, -0.45, 0.45, 1.35, 2.25): member((x, 12.91, -2.93), (x, 12.91, 2.93), 0.08, 0.18, 'lktimber', side=V((1, 0, 0)), skip=('a', 'b'))
    for (z0, z1) in ((-2.93, -1.6), (1.55, 2.93)): member((-2.2, 12.91, z0), (-2.2, 12.91, z1), 0.08, 0.18, 'lktimber', side=V((1, 0, 0)), skip=('a' if z0 < -2 else 'b',))
    for b in K.take(lambda b: abs(b['min'][1] - 13.0) < 1e-3 and abs(b['max'][1] - TOP) < 1e-3):
        def side(f, q, b=b):
            c = [sum(v[i] for v in q) / 4 for i in range(3)]
            return None if max(abs(c[0]), abs(c[2])) > 3.39 else 'lktimber'
        K.box(b['min'], b['max'], {'top': 'lkdeck', 'bottom': 'lkdeck', 'side': side}, sub=1.7, tile=1.0)
    # the fascia board round the platform (over the beam ends and the floor's edge)
    for sz in (-1, 1): FL.obox(K, (-3.44, 12.7, min(sz * 3.4, sz * 3.44)), (3.44, 13.22, max(sz * 3.4, sz * 3.44)), 'lktimber')
    for sx in (-1, 1): FL.obox(K, (min(sx * 3.4, sx * 3.44), 12.7, -3.4), (max(sx * 3.4, sx * 3.44), 13.22, 3.4), 'lktimber')


# ------------------------------------------------------------ the stair
def flights():
    steps = K.take(lambda b: b['mat'] == 'towerwood' and abs(b['max'][0] - b['min'][0] - 1.4) < 0.02 and abs(b['max'][2] - b['min'][2] - 0.5) < 1e-3)
    runs = {}
    for b in steps: runs.setdefault((b['min'][0], b['min'][1]), []).append(b)
    out = []
    for (x0, ya), bs in sorted(runs.items(), key=lambda kv: kv[0][1]):
        bs.sort(key=lambda b: b['max'][1])
        d = 1 if bs[-1]['min'][2] > bs[0]['min'][2] else -1
        out.append((bs, d))
    return out


def flight(bs, d, k, worn):
    x0, x1, ya = bs[0]['min'][0], bs[0]['max'][0], bs[0]['min'][1]
    zf = lambda b: b['min'][2] if d > 0 else b['max'][2]
    zb = lambda b: b['max'][2] if d > 0 else b['min'][2]
    run = 0.5; h = bs[1]['max'][1] - bs[0]['max'][1]; NO = 0.03
    Z = V((0, 0, d))
    prev = ya
    for i, b in enumerate(bs):
        t = b['max'][1]; f, e = zf(b), zb(b)
        m = 'lktrim' if i == worn else 'lkdeck'  # (one tread is a leftover board somebody painted green)
        # the tread: on the step's top, its nosing over the riser below
        emit([(x0, t + 0.003, f - d * NO), (x1, t + 0.003, f - d * NO), (x1, t + 0.003, e), (x0, t + 0.003, e)], m, Y, along=V((1, 0, 0)))
        emit([(x0, t - 0.045, f - d * NO), (x1, t - 0.045, f - d * NO), (x1, t + 0.003, f - d * NO), (x0, t + 0.003, f - d * NO)], m, -Z, along=V((1, 0, 0)))
        emit([(x0, t - 0.045, f - d * NO), (x1, t - 0.045, f - d * NO), (x1, t - 0.045, f), (x0, t - 0.045, f)], m, -Y, along=V((1, 0, 0)))
        # the riser, set back under it
        emit([(x0, prev, f), (x1, prev, f), (x1, t - 0.045, f), (x0, t - 0.045, f)], 'lkdeck', -Z, along=V((1, 0, 0)))
        prev = t
    if ya > 0.01:  # the flat underside the step boxes have: boarded
        emit([(x0, ya, zf(bs[0])), (x1, ya, zf(bs[0])), (x1, ya, zb(bs[-1])), (x0, ya, zb(bs[-1]))], 'lkdeck', -Y, along=V((0, 0, 1)))
    # the closed stringers: a boarded side from the underside up past the nosings, a timber stringer along its top
    za, zl = zf(bs[0]) - d * NO, zb(bs[-1])
    t0 = bs[0]['max'][1]
    line = lambda z: t0 + (z - za) * d * h / run
    zt = zf(bs[-1]) - d * NO  # (the last nosing: the line stops climbing there)
    for (xs, xo) in ((x0, -1), (x1, 1)):
        thick = 0.022 if abs(xs + 1.5) < 0.01 or abs(xs + 1.45) < 0.01 else 0.04  # (between the two flights there's only a 5 cm gap)
        X0, X1 = (xs - thick, xs) if xo < 0 else (xs, xs + thick)
        top_a, top_t, SD = line(za) + 0.06, line(zt) + 0.06, 0.34
        P3 = lambda prof: [V((X0, y, z)) for (z, y) in prof]
        prism(P3([(za, ya), (za, top_a - SD), (zt, top_t - SD), (zl, top_t - SD), (zl, ya)]), V((X1 - X0, 0, 0)), 'lkdeck', along=V((0, 1, 0)), skip=(1, 2))
        slope = V((0, top_t - top_a, zt - za))
        prism(P3([(za, top_a - SD), (za, top_a), (zt, top_t), (zt, top_t - SD)]), V((X1 - X0, 0, 0)), 'lktimber', along=slope, skip=(2, 3))
        prism(P3([(zt, top_t - SD), (zt, top_t), (zl, top_t), (zl, top_t - SD)]), V((X1 - X0, 0, 0)), 'lktimber', along=V((0, 0, 1)), skip=(0, 3))
    # the handrails: a newel at each end and one in the middle, a top rail and a middle rail, both sides
    zA, zB = zf(bs[0]) + d * 0.06, zl - d * 0.06  # newels on the first tread and the last
    yA, yB = t0 + 1.0, bs[-1]['max'][1] + 1.0
    railY = lambda z: yA + (yB - yA) * ((z - zA) / (zB - zA))
    for xo in (-1, 1):
        px = x0 + 0.035 if xo < 0 else x1 - 0.035
        for z in (zA, (zA + zB) / 2, zB):
            ib = min(len(bs) - 1, max(0, int(((z - zf(bs[0])) * d) / run)))
            member((px, bs[ib]['max'][1] + 0.003, z), (px, railY(z), z), 0.07, 0.07, 'lktimber', side=V((1, 0, 0)), skip=('a',))
        member((px, yA + 0.03, zA - d * 0.06), (px, yB + 0.03, zB + d * 0.06), 0.08, 0.06, 'lktimber', side=V((1, 0, 0)))
        member((px, yA - 0.47, zA + d * 0.035), (px, yB - 0.47, zB - d * 0.035), 0.045, 0.06, 'lktimber', side=V((1, 0, 0)), skip=('a', 'b'))


def landings():
    for b in K.take(lambda b: b['mat'] == 'towerwood' and abs(b['max'][1] - b['min'][1] - 0.22) < 1e-3):
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        sz = 1 if z0 > 0 else -1
        zo, zi = (z1, z0) if sz > 0 else (z0, z1)  # the face side, the inner side (where the flights come and go)
        emit([(x0, y1 + 0.003, z0), (x1, y1 + 0.003, z0), (x1, y1 + 0.003, z1), (x0, y1 + 0.003, z1)], 'lkdeck', Y, along=V((1, 0, 0)), sub=1.5)
        emit([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], 'lkdeck', -Y, along=V((1, 0, 0)))
        for (p, n) in (((x1, 0, 0), V((1, 0, 0))), ((x0, 0, 0), V((-1, 0, 0))), ((0, 0, zo), V((0, 0, sz)))):
            if n.x: q = [(p[0], y0, z0), (p[0], y0, z1), (p[0], y1 + 0.003, z1), (p[0], y1 + 0.003, z0)]
            else: q = [(x0, y0, p[2]), (x1, y0, p[2]), (x1, y1 + 0.003, p[2]), (x0, y1 + 0.003, p[2])]
            emit(q, 'lktimber', n, along=V((1, 0, 0)) if n.z else V((0, 0, 1)))
        # the ledger it bears on, bolted to the girt's inner face
        g = 3.02 * sz
        FL.obox(K, (x0, y0 - 0.14, min(zo, g)), (x1, y0, max(zo, g)), 'lktimber')
        for x in (x0 + 0.5, (x0 + x1) / 2, x1 - 0.5): bolt((x, y0 - 0.07, g + sz * 0.16), V((0, 0, sz)), Y, s=0.04, h=0.02)
        # rails on its three open sides
        xe, xw, zr, zn = x1 - 0.035, x0 + 0.035, zo - sz * 0.035, zi + sz * 0.05
        for (px, pz) in ((xe, zn), (xe, zr), (xw, zr), (xw, zn)): member((px, y1 + 0.003, pz), (px, y1 + 1.0, pz), 0.07, 0.07, 'lktimber', side=V((1, 0, 0)), skip=('a',))
        for yy, w, hh in ((1.03, 0.08, 0.06), (0.53, 0.045, 0.06)):  # the rail along the face side runs through, the two ends stop against it
            member(V((xw - 0.05, y1 + yy, zr)), V((xe + 0.05, y1 + yy, zr)), w, hh, 'lktimber')
            for px in (xe, xw): member(V((px, y1 + yy, zn - sz * 0.04)), V((px, y1 + yy, zr - sz * w / 2)), w, hh, 'lktimber', skip=('b',))
    # steel hanger rods from the cab's joists down through the landings' loose ends
    for sz in (-1, 1):
        y0, y2 = (2.42, 7.70) if sz > 0 else (5.06, 10.34)  # (the landing it carries, the one above it threads through)
        for z in (1.62 * sz, 2.78 * sz):
            member((-0.14, y0 - 0.04, z), (-0.14, 13.0, z), 0.03, 0.03, 'lksteel', side=V((1, 0, 0)), skip=('b',))
            for yy in (y0, y2): bolt((-0.14, yy, z), -Y, V((1, 0, 0)), s=0.06, h=0.03)


# ------------------------------------------------------------ the cab
def cab():
    walls = K.take(lambda b: b['mat'] == 'towerwood' and b['min'][1] >= TOP - 1e-3)
    for b in walls:
        thin = 2 if (b['max'][2] - b['min'][2]) < (b['max'][0] - b['min'][0]) else 0
        def pick(f, q, thin=thin):
            c = [sum(v[i] for v in q) / 4 for i in range(3)]
            if f in ('py', 'ny'): return 'lktrim'  # (the sills' tops, the heads' undersides)
            ax = 0 if f in ('px', 'nx') else 2
            if ax != thin: return 'lksiding' if abs(c[ax]) > 3.39 else 'lktrim'  # (a window jamb; or a wall's end at the corner)
            return 'lksiding' if (c[ax] > 0) == (f[0] == 'p') and abs(c[ax]) > 3.3 else 'lkdeck'  # (outside: siding. inside: boards)
        K.box(b['min'], b['max'], {'all': pick}, sub=1.4)
    WIN0, WIN1 = 14.15, 15.35
    for (n, a) in ((V((0, 0, 1)), V((1, 0, 0))), (V((0, 0, -1)), V((1, 0, 0))), (V((1, 0, 0)), V((0, 0, 1))), (V((-1, 0, 0)), V((0, 0, 1)))):
        W = 3.1 if n.z else 2.92  # the window runs -W..W along this wall
        def WP(s, y, o): return a * s + Y * y + n * o
        def wbox(s0, s1, y0, y1, o0, o1, mat):
            p, q = WP(s0, y0, o0), WP(s1, y1, o1)
            FL.obox(K, tuple(min(p[i], q[i]) for i in range(3)), tuple(max(p[i], q[i]) for i in range(3)), mat)
        # the window: three mullions (four bays), a sill board outside, a stool inside, the head casing
        bays = [(-W + i * 2 * W / 4, -W + (i + 1) * 2 * W / 4) for i in range(4)]
        for i in (1, 2, 3):
            s = -W + i * 2 * W / 4
            p, q = WP(s - 0.04, WIN0, 3.22), WP(s + 0.04, WIN1, 3.38)
            K.box(tuple(min(p[j], q[j]) for j in range(3)), tuple(max(p[j], q[j]) for j in range(3)), {'all': 'lktrim'})
        wbox(-3.24, 3.24, WIN0 - 0.05, WIN0 + 0.015, 3.38, 3.46, 'lktrim')
        wbox(-W, W, WIN0 - 0.03, WIN0 + 0.03, 3.12, 3.24, 'lktrim')
        wbox(-3.24, 3.24, WIN1, WIN1 + 0.1, 3.38, 3.405, 'lktrim')
        wbox(-3.24, 3.24, 13.2, 13.36, 3.38, 3.41, 'lktrim')  # (a skirting board where the cab meets the platform)
        for bi, (s0, s1) in enumerate(bays):
            crooked = n.z < 0 and bi == 1  # (the north side, facing the ranger lot: one hinge pulled out)
            if not crooked: sash(WP, n, a, s0 + 0.05, s1 - 0.05, WIN1, 0.25 + 0.03 * ((bi * 7 + int(n.x * 3 + n.z)) % 3), shards=(bi * 3 + int(2 * n.x + n.z + 2)) % 4 == 0)
            shutter(WP, n, a, s0 + (0.06 if crooked else 0.02), s1 - (0.06 if crooked else 0.02), crooked)
        up = Y * math.cos(SANG) + n * math.sin(SANG)
        for s in [b[0] for b in bays] + [W]:  # prop poles at the mullions and corners (between the sashes), sill to the shutters' edges
            sc = max(-W + 0.06, min(W - 0.06, s))
            tip = WP(sc, HY - 1.2 * math.sin(SANG), HO + 1.2 * math.cos(SANG)) + up * 0.004
            member(WP(sc, WIN0 + 0.015, 3.43), tip, 0.045, 0.045, 'lktimber')
    # the corner boards
    for sx in (-1, 1):
        for sz in (-1, 1):
            FL.obox(K, (min(sx * 3.24, sx * 3.425), TOP, min(sz * 3.24, sz * 3.405)), (max(sx * 3.24, sx * 3.425), 15.7, max(sz * 3.24, sz * 3.405)), 'lktrim')


def sash(WP, n, a, s0, s1, yh, tilt, shards=False):
    """a top-hung window sash swung out on a stay (glass long gone): stiles, rails, a muntin"""
    H, FW, FT = 1.1, 0.06, 0.035
    th = math.radians(40 + tilt * 20)  # (out from the wall, a little different on each)
    dn = (-Y * math.cos(th) + n * math.sin(th))  # down the sash
    nn = a.cross(dn).normalized()
    if nn.dot(n) < 0: nn = -nn  # (its outside face)
    o = 3.38 + FT / 2 + 0.001
    def S(s, t, e=0.0): return WP(s, yh, o) + dn * t + nn * e
    def bar(sa, sb, ta, tb, skip=()):
        pts = [S(sa, ta, -FT / 2), S(sb, ta, -FT / 2), S(sb, tb, -FT / 2), S(sa, tb, -FT / 2)]
        prism(pts, nn * FT, 'lktrim', along=dn, skip=skip)
    bar(s0, s0 + FW, 0, H); bar(s1 - FW, s1, 0, H)
    bar(s0 + FW, s1 - FW, 0, FW, skip=(1, 3)); bar(s0 + FW, s1 - FW, H - FW, H, skip=(1, 3))
    m = (s0 + s1) / 2
    bar(m - 0.018, m + 0.018, FW, H - FW, skip=(0, 2))
    if shards:  # a pane's last corner
        for (sa, ta, ds, dt) in ((s0 + FW, FW, 1, 1), (s1 - FW, H - FW, -1, -1)):
            p = [S(sa, ta), S(sa + ds * 0.24, ta), S(sa, ta + dt * 0.2)]
            tri_uv(p, 'lkglass', [(0, 0), (0.24, 0), (0, 0.2)]); tri_uv(p[::-1], 'lkglass', [(0, 0.2), (0.24, 0), (0, 0)])
    # the stay: a rod from the bottom rail back to the sill
    sb = s1 - 0.14
    member(S(sb, H - 0.03, -FT / 2), WP(sb, 14.165, 3.40), 0.022, 0.022, 'lksteel')


def shutter(WP, n, a, s0, s1, crooked=False):
    """a board-and-batten storm shutter hung from the header, propped out as an awning (the poles at the bays' edges: cab()).
    crooked: one hinge pulled out, its pole slipped down the sill: it hangs steep and skewed"""
    Ls, T = 1.32, 0.035
    ang = SANG
    if crooked:
        hA, hB = WP(s0, HY, HO), WP(s1, HY - 0.2, HO)
        ang = math.radians(50)
    else: hA, hB = WP(s0, HY, HO), WP(s1, HY, HO)
    al = (hB - hA).normalized()
    e = (n * math.cos(ang) - Y * math.sin(ang))
    e = (e - al * e.dot(al)).normalized()  # (down the shutter from the hinge)
    up = al.cross(e).normalized()
    if up.y < 0: up = -up
    pts = [hA, hB, hB + e * Ls, hA + e * Ls]
    prism(pts, up * T, 'lkshut', along=al, skip=())
    # battens under it: two across, a brace between (the Z)
    W = (hB - hA).length
    def B(sa, sb, ta, tb, th=0.03, mat='lktimber'):
        q = [hA + al * sa + e * ta, hA + al * sb + e * ta, hA + al * sb + e * tb, hA + al * sa + e * tb]
        prism(q, -up * th, mat, along=al, skip=())
    B(0.06, W - 0.06, 0.16, 0.28); B(0.06, W - 0.06, Ls - 0.3, Ls - 0.18)
    c0, c1 = hA + al * 0.12 + e * 0.29, hA + al * (W - 0.12) + e * (Ls - 0.31)
    member(c0 - up * 0.0125, c1 - up * 0.0125, 0.09, 0.027, 'lktimber', side=up.cross((c1 - c0).normalized()))
    if crooked:  # its pole: slid down to the sill, leaning on the shutter's edge
        foot = WP(s0 + 0.3, 14.165, 3.42); hit = hA + al * 0.06 + e * 0.9 - up * 0.01
        member(foot, hit, 0.045, 0.045, 'lktimber')


def roof():
    # the ceiling / soffit: the slab's underside, then fascia boards round its edge
    for b in K.take(lambda b: b['mat'] in ('cabinroof', 'cabinroof2')):
        if abs(b['min'][1] - 15.7) < 1e-3:
            K.box(b['min'], b['max'], {'bottom': 'lkdeck'}, sub=1.6, tile=1.0)
    for sz in (-1, 1): FL.obox(K, (-3.735, 15.66, min(sz * 3.70, sz * 3.735)), (3.735, 15.94, max(sz * 3.70, sz * 3.735)), 'lktrim')
    for sx in (-1, 1): FL.obox(K, (min(sx * 3.70, sx * 3.735), 15.66, -3.70), (max(sx * 3.70, sx * 3.735), 15.94, 3.70), 'lktrim')
    # the hip roof: four faces from the eaves (on the fascia) up to the peak, laid off the slabs' steps
    E, YE, AP = 3.735, 15.94, 16.87
    C = [V((E, YE, E)), V((E, YE, -E)), V((-E, YE, -E)), V((-E, YE, E))]
    top = V((0, AP, 0))
    for i in range(4):
        a, b = C[i], C[(i + 1) % 4]
        al = (b - a).normalized()
        mid = (a + b) / 2; out = V((mid.x, 0, mid.z)).normalized()
        upd = (top - mid).normalized()
        rows = 3
        for r in range(rows):
            t0, t1 = r / rows, (r + 1) / rows
            A0, B0, A1, B1 = a.lerp(top, t0), b.lerp(top, t0), a.lerp(top, t1), b.lerp(top, t1)
            if r < rows - 1: emit([A0, B0, B1, A1], 'lkroof', out + Y, along=upd)
            else: emit([A0, B0, top], 'lkroof', out + Y, along=upd)
        # the hip cap over the corner: a board each side of the hip line
    for i in range(4):
        c = C[i]; d = (top - c)
        member(c + V((0, 0.01, 0)) - V((c.x, 0, c.z)).normalized() * 0.02, top + V((0, 0.01, 0)), 0.12, 0.05, 'lkroof', side=V((-c.z, 0, c.x)).normalized(), ch=0.015)
    FL.tube(K, (0, AP - 0.06, 0), (0, AP + 0.08, 0), 0.11, 0.05, 'lksteel', n=8)  # (the lead cap over the peak)
    # the lightning rod: copper, a glass ball on it (the collision is a 10 cm post: it's in there)
    bend = V((0.045, 17.44, 0.012))  # (its top bent a little by something big. inside the game's 10 cm post still)
    rod(V((0, AP + 0.06, 0)), V((0, 17.22, 0)), 0.022, 0.02, 'lkbrass')
    rod(V((0, 17.22, 0)), bend, 0.02, 0.016, 'lkbrass')
    rod(bend, bend + (bend - V((0, 17.22, 0))).normalized() * 0.07, 0.016, 0.0, 'lkbrass')
    ball = [[V((0.07 * math.cos(la) * math.cos(lo), 17.12 + 0.07 * math.sin(la), 0.07 * math.cos(la) * math.sin(lo))) for lo in [math.tau * i / 8 for i in range(8)]] for la in [-math.pi / 2 + math.pi * j / 4 for j in range(5)]]
    for j in range(4):
        for i in range(8):
            a, b, c, d = ball[j][i], ball[j][(i + 1) % 8], ball[j + 1][(i + 1) % 8], ball[j + 1][i]
            out = (a + b + c + d) / 4 - V((0, 17.12, 0))
            if j == 0: emit([a, c, d], 'lkglass', out)
            elif j == 3: emit([a, b, d], 'lkglass', out)
            else: emit([a, b, c, d], 'lkglass', out)
    # its down-lead: copper cable down the south-east hip, the corner of the cab, the platform and the post to the ground rod
    hp = top.lerp(C[0], 0.985) + V((0, 0.05, 0))
    lead = [V((0.03, AP + 0.04, 0.03)), hp, V((3.743, 15.95, 3.743)), V((3.743, 15.69, 3.743)), V((3.432, 15.69, 3.412)), V((3.432, 13.24, 3.412)),
            V((3.447, 13.23, 3.447)), V((3.447, 12.69, 3.447)), V((3.262, 12.69, 3.262)), V((3.262, 0.8, 3.262)), V((3.3, 0.78, 3.3)), V((3.3, 0.365, 3.3)),
            V((3.43, 0.28, 3.43)), V((3.45, 0.0, 3.45)), V((3.62, 0.0, 3.62))]
    for p0, p1 in zip(lead, lead[1:]):
        member(p0, p1, 0.022, 0.022, 'lkbrass')


def inside():
    # the fire finder's cabinet (the game's table box) and the finder on it
    tb = K.take(lambda b: b['mat'] == 'planks')[0]
    (x0, y0, z0), (x1, y1, z1) = tb['min'], tb['max']
    for (x, z) in ((x0, z0), (x0, z1), (x1, z0), (x1, z1)):
        sx, sz = (1 if x == x0 else -1), (1 if z == z0 else -1)
        FL.obox(K, (min(x, x + sx * 0.07), y0, min(z, z + sz * 0.07)), (max(x, x + sx * 0.07), y1 - 0.04, max(z, z + sz * 0.07)), 'lktimber')
    K.box((x0 + 0.01, y0, z0 + 0.01), (x1 - 0.01, y1 - 0.05, z1 - 0.01), {'side': 'lkdeck'}, cull=False)  # (its panels, set in a hair between the legs)
    FL.obox(K, (x0 - 0.02, y1 - 0.04, z0 - 0.02), (x1 + 0.02, y1, z1 + 0.02), 'lktimber')
    for (za, zb) in ((z0 + 0.12, -0.03), (0.03, z1 - 0.12)):  # two drawers on the side toward the stair, brass pulls
        FL.obox(K, (x0 - 0.008, y1 - 0.3, za), (x0 + 0.02, y1 - 0.08, zb), 'lktrim')
        bolt((x0 - 0.008, y1 - 0.19, (za + zb) / 2), V((-1, 0, 0)), Y, s=0.04, h=0.03, mat='lkbrass')
    ms = K.take(lambda b: b['mat'] == 'mapsheet')[0]
    cx, cz = (ms['min'][0] + ms['max'][0]) / 2, (ms['min'][2] + ms['max'][2]) / 2; yt = ms['max'][1]
    FL.tube(K, (cx, y1, cz), (cx, yt, cz), 0.39, 0.39, 'lkmap', n=20, caps=(False, True))
    ring_o = [V((cx + 0.445 * math.cos(math.tau * i / 20), 0, cz + 0.445 * math.sin(math.tau * i / 20))) for i in range(20)]
    ring_i = [V((cx + 0.39 * math.cos(math.tau * i / 20), 0, cz + 0.39 * math.sin(math.tau * i / 20))) for i in range(20)]
    for i in range(20):
        j = (i + 1) % 20
        emit([ring_o[i] + V((0, yt + 0.02, 0)), ring_o[j] + V((0, yt + 0.02, 0)), ring_i[j] + V((0, yt + 0.02, 0)), ring_i[i] + V((0, yt + 0.02, 0))], 'lkbrass', Y)
        emit([ring_o[i] + V((0, y1, 0)), ring_o[j] + V((0, y1, 0)), ring_o[j] + V((0, yt + 0.02, 0)), ring_o[i] + V((0, yt + 0.02, 0))], 'lkbrass', ring_o[i] + ring_o[j] - V((2 * cx, 0, 2 * cz)))
        emit([ring_i[i] + V((0, yt, 0)), ring_i[j] + V((0, yt, 0)), ring_i[j] + V((0, yt + 0.02, 0)), ring_i[i] + V((0, yt + 0.02, 0))], 'lkbrass', V((2 * cx, 0, 2 * cz)) - ring_i[i] - ring_i[j])
    # the map: the lake (glass blue), the trails (deck), the tower's red dot
    lake = [(0.2, 0.05), (0.33, -0.02), (0.3, 0.2), (0.16, 0.26)]
    prism([V((cx + x, yt - 0.001, cz + z)) for (x, z) in lake], V((0, 0.004, 0)), 'lkglass', skip=('a',))
    prism([V((cx - 0.02, yt - 0.001, cz - 0.02)), V((cx + 0.02, yt - 0.001, cz - 0.02)), V((cx + 0.02, yt - 0.001, cz + 0.02)), V((cx - 0.02, yt - 0.001, cz + 0.02))], V((0, 0.005, 0)), 'lkcloth', skip=('a',))
    # the alidade: a brass bar across on the ring, a sight frame with its hair at one end, a slotted peep at the other
    th = 2.3; ux, uz = math.cos(th), math.sin(th)
    A, Bq = V((cx - ux * 0.44, yt + 0.028, cz - uz * 0.44)), V((cx + ux * 0.44, yt + 0.028, cz + uz * 0.44))
    member(A, Bq, 0.04, 0.016, 'lkbrass')
    side = V((-uz, 0, ux))
    for sgn in (-1, 1): member(Bq + side * sgn * 0.035 - V((ux, 0, uz)) * 0.03 + V((0, 0.008, 0)), Bq + side * sgn * 0.035 - V((ux, 0, uz)) * 0.03 + V((0, 0.17, 0)), 0.012, 0.012, 'lkbrass', side=side)
    member(Bq + side * -0.041 - V((ux, 0, uz)) * 0.03 + V((0, 0.176, 0)), Bq + side * 0.041 - V((ux, 0, uz)) * 0.03 + V((0, 0.176, 0)), 0.012, 0.012, 'lkbrass')  # (on the posts' tops)
    member(Bq - V((ux, 0, uz)) * 0.03 + V((0, 0.014, 0)), Bq - V((ux, 0, uz)) * 0.03 + V((0, 0.17, 0)), 0.003, 0.003, 'lksteel', side=side)
    member(A + V((ux, 0, uz)) * 0.03 + V((0, 0.008, 0)), A + V((ux, 0, uz)) * 0.03 + V((0, 0.12, 0)), 0.06, 0.006, 'lkbrass', side=side)
    # the lightning stool: a plank seat on four legs, each foot in a glass insulator
    sx, sz, sy = 0.35, -1.05, TOP
    FL.obox(K, (sx - 0.18, sy + 0.48, sz - 0.18), (sx + 0.18, sy + 0.52, sz + 0.18), 'lktimber')
    for (dx, dz) in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
        fx, fz = sx + dx * 0.17, sz + dz * 0.17
        FL.tube(K, (fx, sy, fz), (fx, sy + 0.05, fz), 0.05, 0.046, 'lkglass', n=8, caps=(False, False))
        FL.tube(K, (fx, sy + 0.05, fz), (fx, sy + 0.095, fz), 0.046, 0.026, 'lkglass', n=8, caps=(False, True))
        member((fx, sy + 0.09, fz), (sx + dx * 0.13, sy + 0.485, sz + dz * 0.13), 0.035, 0.035, 'lktimber', skip=('a', 'b'))
    # the cot along the east wall: a steel frame, a mattress under a red wool blanket, a pillow
    c0, c1, cz0, cz1, cy = 2.52, 3.14, 0.8, 2.72, TOP + 0.38
    for (x, z) in ((c0, cz0), (c0, cz1), (c1, cz0), (c1, cz1)): member((x, TOP, z), (x, cy, z), 0.03, 0.03, 'lksteel', side=V((1, 0, 0)), skip=('a',))
    for x in (c0, c1): member((x, cy, cz0 - 0.025), (x, cy, cz1 + 0.025), 0.035, 0.035, 'lksteel', side=V((1, 0, 0)))
    for z in (cz0, cz1): member((c0 + 0.0175, cy, z), (c1 - 0.0175, cy, z), 0.035, 0.035, 'lksteel', skip=('a', 'b'))
    FL.obox(K, (c0 + 0.02, cy + 0.0175, cz0 + 0.02), (c1 - 0.02, cy + 0.12, cz1 - 0.02), 'lkmap')
    FL.obox(K, (c0 - 0.03, cy + 0.06, cz0 + 0.3), (c1 + 0.0, cy + 0.14, cz1 - 0.35), 'lkcloth')
    FL.obox(K, (c0 + 0.08, cy + 0.115, cz1 - 0.32), (c1 - 0.08, cy + 0.2, cz1 - 0.06), 'lkmap')
    # the lantern, still lit, on a wire from the ceiling
    lx, lz = 0.25, -0.35
    member((lx, 15.7, lz), (lx, 15.33, lz), 0.012, 0.012, 'lksteel', side=V((1, 0, 0)))
    FL.tube(K, (lx, 15.06, lz), (lx, 15.11, lz), 0.075, 0.075, 'lksteel', n=8)
    FL.tube(K, (lx, 15.11, lz), (lx, 15.17, lz), 0.05, 0.068, 'lklamp', n=8, caps=(False, False))
    FL.tube(K, (lx, 15.17, lz), (lx, 15.24, lz), 0.068, 0.045, 'lklamp', n=8, caps=(False, False))
    FL.tube(K, (lx, 15.24, lz), (lx, 15.3, lz), 0.07, 0.02, 'lksteel', n=8)
    FL.tube(K, (lx, 15.29, lz), (lx, 15.335, lz), 0.012, 0.012, 'lksteel', n=4)
    for s in (-1, 1): member((lx + s * 0.07, 15.11, lz), (lx + s * 0.07, 15.25, lz), 0.012, 0.012, 'lksteel', side=V((1, 0, 0)))
    # the trapdoor, stood open against the stairwell's north edge
    hz = -1.55
    hp = [V((-2.92, TOP, hz)), V((-1.48, TOP, hz)), V((-1.48, TOP + 1.42, hz - 0.22)), V((-2.92, TOP + 1.42, hz - 0.22))]
    prism(hp, V((0, 0, -0.05)), 'lkdeck', along=V((0, 1, 0)))
    for t in (0.14, 0.78):  # two battens across its underside, short of its edges
        q = [hp[0].lerp(hp[3], t) + V((0.03, 0, 0)), hp[1].lerp(hp[2], t) - V((0.03, 0, 0)), hp[1].lerp(hp[2], t + 0.08) - V((0.03, 0, 0)), hp[0].lerp(hp[3], t + 0.08) + V((0.03, 0, 0))]
        prism([p - V((0, 0, 0.001)) for p in q], V((0, 0, 0.03)), 'lktimber', along=V((1, 0, 0)), skip=('a',))


def build():
    global K
    K = Kit(os.path.join(HERE, 'boxes', 'lookout.json'), seed=7)
    K.ground = 0.0
    for b in K.boxes: b['_done'] = True if b['mat'] in ('metal',) else b.get('_done')
    K.take(lambda b: b['mat'] == 'towerwood' and b['max'][1] - b['min'][1] > 10)   # the legs: posts()
    K.take(lambda b: b['mat'] == 'towerwood' and abs(b['max'][1] - b['min'][1] - 0.14) < 1e-3)  # the girts: girts()
    posts(); girts(); bracing(); platform()
    fl = flights()
    for k, (bs, d) in enumerate(fl): flight(bs, d, k, worn=(3 if k == 1 else -1))
    landings(); cab(); roof(); inside()
    left = [b for b in K.boxes if not b.get('_done')]
    if left: print('LEFT OVER', len(left), [(b['mat'], b['min'], b['max']) for b in left][:8])
    K.finish(os.path.join(OUTDIR, 'lookout.glb'))
    n = sum(len(g['f']) for g in K.geo.values())
    print('faces', n, {k[0]: len(g['f']) for k, g in K.geo.items()})


build()
