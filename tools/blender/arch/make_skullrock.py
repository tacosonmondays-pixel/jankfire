# Skull Rock (Islands, shared/map.js skullRock()): a sea rock the shape of a skull, not two blocks with square holes.
# DESIGN PASS: look only, drawn over the old boxes (which still do the collisions until the shape is agreed).
# what it is: a weathered stone skull half sunk in the beach, facing north at the volcano. a domed cranium (a crack
# across it, moss on top), a heavy brow, two deep eye sockets, the nose's hole, cheekbones, the upper jaw resting on the
# sand with a row of teeth over the cave mouth (the way through to the treasure). no lower jaw: the sea had it.
# local frame: the skull's middle at x 0, z 69; it faces -z. about 19 m wide, 17 m deep, 11 m tall.
# run: blender52 -b --python tools/blender/arch/make_skullrock.py -- [out.glb]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(OUTDIR, 'skullrock.glb')
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({'skbone': ('stucco', '#e2d8bc', {}), 'skshade': ('stucco', '#a89c7c', {}), 'skdeep': ('stucco', '#5c5244', {}), 'skhole': ('stucco', '#1c1820', {}),
             'skmoss': ('stucco', '#7c9450', {}), 'sktooth': ('stucco', '#f0ead6', {}), 'skcrack': ('stucco', '#3c3428', {})})
NOCAST.update({'skcrack'})
K = Kit(os.path.join(HERE, 'boxes', 'skullrock.json'), seed=3)
K.ground = -1e9

C = Vector((0.0, 5.85, 69.0))     # the skull's middle (it is sunk in the beach to its upper teeth)
RX, RY, RZ = 9.0, 6.4, 9.2        # half sizes of the cranium
NT, NP = 104, 52
P0, P1 = -1.0, math.pi / 2        # elevation: from under the sand to the crown
IC = 12                           # the row of the teeth: below it the skull is jaw and cheek, straight down to the sand
JC = 4                            # the cave mouth: this many columns each side of the face's middle (about 4.2 m)


def hsh(*a):
    x = 0.0
    for i, v in enumerate(a): x += math.sin(v * (12.9898 + i * 7.233) + i * 3.17) * 43758.5453
    return x - math.floor(x)


def wrap(a): return (a + math.pi) % (2 * math.pi) - math.pi


def g(th, ph, t0, p0, wt, wp):  # a bump (or a hollow) on the skull at azimuth t0, elevation p0
    return math.exp(-(wrap(th - t0) * math.cos(ph) / wt) ** 2 - ((ph - p0) / wp) ** 2)


def sq(th, ph, t0, p0, wt, wp, k=4):  # the same with squarer shoulders (a socket, a cave mouth)
    return math.exp(-abs(wrap(th - t0) * math.cos(ph) / wt) ** k - abs((ph - p0) / wp) ** k)


def radius(th, ph):
    """how far out the surface is along (th azimuth from the face, ph elevation), as a share of the cranium; and how
    deep in a hollow that point is (0..1: the sockets, the nose, the mouth go dark)"""
    front = math.cos(th)  # 1 at the face, -1 at the back of the head
    r = 1.0
    r += 0.12 * g(th, ph, math.pi, 0.2, 1.0, 0.7)                       # the back of the head swells
    r += 0.05 * g(th, ph, 0, 0.75, 0.8, 0.25)                           # the forehead
    for s in (-1, 1):
        r += 0.13 * g(th, ph, s * 0.5, 0.42, 0.36, 0.075)               # the brow ridge, heavy, over each eye
        r += 0.11 * g(th, ph, s * 0.95, -0.12, 0.2, 0.16)               # cheekbones
        r -= 0.08 * g(th, ph, s * 1.45, 0.1, 0.28, 0.3)                 # temples, hollow
    hole = 0.0
    for s in (-1, 1):
        e = sq(th, ph, s * 0.5, 0.14, 0.27, 0.2, 3); r -= 0.42 * e; hole = max(hole, e)   # eye sockets: big, deep
    n = max(g(th, ph, 0, -0.2, 0.06, 0.13), g(th, ph, 0.07, -0.3, 0.07, 0.08), g(th, ph, -0.07, -0.3, 0.07, 0.08))  # the nose: a point over two lobes
    r -= 0.3 * n; hole = max(hole, n)
    # below the cheekbones the face narrows to the upper jaw; the back of the head tucks under too
    low = max(0.0, min(1.0, (-ph - 0.2) / 0.3))
    r -= low * (0.07 * max(0.0, front) ** 0.6 + 0.03 * abs(math.sin(th)) ** 2)  # (a little: an undercut below the cheekbones, no more)
    r += 0.06 * g(th, ph, 0, -0.44, 0.6, 0.08)                          # the upper jaw's ridge, where the teeth sit
    r += (hsh(round(th * 9), round(ph * 9)) - 0.5) * 0.02               # weathered, in facets
    return r, hole


PC = P0 + (P1 - P0) * IC / NP  # the teeth line


def sm(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def pt(th, ph):
    cp = math.cos(max(ph, PC)); r, hole = radius(th, max(ph, PC))
    y = C.y + math.sin(max(ph, PC)) * RY * r * (1.0 + 0.1 * max(0, math.sin(ph)))
    hr = cp * r  # how far out, level
    if ph < PC:
        # below the teeth the jaw and cheeks carry the skull's width down to the sand (no neck: it never looks like a
        # mushroom from the side), lumpy, the cheeks as buttresses
        t = (PC - ph) / (PC - P0)
        base = 1.02 + 0.045 * math.sin(th * 5 + 1) + 0.03 * math.sin(th * 11) + 0.07 * (g(th, 0, 1.15, 0, 0.3, 9) + g(th, 0, -1.15, 0, 0.3, 9)) - 0.04 * max(0.0, math.cos(th)) ** 3
        hr = hr + (base - hr) * sm(t * 1.7)
        y = y + (-0.35 - y) * t
    # th 0 = the face = -z; +th turns toward +x
    return Vector((C.x + math.sin(th) * RX * hr, y, C.z - math.cos(th) * RZ * hr)), hole


G = [[pt(2 * math.pi * j / NT - math.pi, P0 + (P1 - P0) * i / NP) for j in range(NT)] for i in range(NP + 1)]


def tri(a, b, c, m):
    K.tri([a, b, c] if (b - a).cross(c - a).dot((a + b + c) / 3 - C) > 0 else [a, c, b], m)


CRACK = lambda th, ph: abs(ph - (0.95 + 0.16 * math.sin(th * 2.3 + 0.6) + 0.05 * math.sin(th * 9))) < 0.022 and abs(th) < 2.2  # the suture across the crown
for i in range(NP):
    ph = P0 + (P1 - P0) * (i + 0.5) / NP
    for j in range(NT):
        j2 = (j + 1) % NT; th = 2 * math.pi * (j + 0.5) / NT - math.pi
        if i < IC and NT // 2 - JC <= j < NT // 2 + JC: continue  # the cave mouth: open (the way in is built below)
        (a, ha), (b, hb), (c, hc), (d, hd) = G[i][j], G[i][j2], G[i + 1][j2], G[i + 1][j]
        hole = (ha + hb + hc + hd) / 4
        nrm = (b - a).cross(d - a); ny = abs(nrm.normalized().y) if nrm.length > 1e-9 else 1; out_up = ((a + c) / 2 - C).y > 0
        if hole > 0.62: m = 'skhole'
        elif hole > 0.3: m = 'skdeep'
        elif CRACK(th, ph): m = 'skcrack'
        elif out_up and ny > 0.82 and ph > 0.9 and hsh(i // 2, j // 2, 3) < 0.75: m = 'skmoss'
        elif hole > 0.1 or (ph < PC and hsh(i // 2, j // 5, 6) < 0.3): m = 'skshade'
        else: m = 'skbone'
        if i == NP - 1: tri(a, b, c, m)  # (the crown: the top row meets in a point)
        else: tri(a, b, c, m); tri(a, c, d, m)

# the cave: a real way in. its mouth is the hole left in the skin; from that edge a passage runs back into the skull,
# squaring off to the 4 m x 3 m of the old cave, darker the further in, to a back wall at z 72.6
j0, j1 = NT // 2 - JC, NT // 2 + JC
LOOP = [G[i][j0][0] for i in range(IC + 1)] + [G[IC][j][0] for j in range(j0 + 1, j1)] + [G[i][j1][0] for i in range(IC, -1, -1)]
HW, HT = 2.05, 3.0


def prof(v, k, n):  # where that point of the mouth's edge ends up on the passage's own outline
    ys = (HT - 0.25 + 0.35) / (LOOP[IC].y + 0.35)  # (the walls' rows squeezed under the passage's roof, none on top of another)
    if k <= IC: return (-HW, -0.35 + (v.y + 0.35) * ys)
    if k >= n - IC - 1: return (HW, -0.35 + (v.y + 0.35) * ys)
    x = max(-HW, min(HW, v.x * HW / abs(LOOP[IC].x))); return (x, HT - 0.25 + 0.3 * math.cos(math.pi / 2 * x / HW))


zf = max(v.z for v in LOOP); nL = len(LOOP); RINGS = [LOOP]
for d, w in ((1.0, 0.7), (3.0, 1.0), (7.0, 1.0), (72.6 - zf, 1.0)):
    RINGS.append([Vector((v.x + (prof(v, k, nL)[0] - v.x) * w, v.y + (prof(v, k, nL)[1] - v.y) * w, zf + d + (hsh(k, d) - 0.5) * 0.12 * (d < 9))) for k, v in enumerate(LOOP)])
axis = lambda z: Vector((0, 1.4, z))
for ri in range(len(RINGS) - 1):
    A, B2 = RINGS[ri], RINGS[ri + 1]; m = ('skshade', 'skdeep', 'skdeep', 'skhole')[ri]
    for k in range(nL - 1):
        for t3 in ([A[k], A[k + 1], B2[k + 1]], [A[k], B2[k + 1], B2[k]]):
            cc = (t3[0] + t3[1] + t3[2]) / 3
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot(axis(cc.z) - cc) < 0: t3 = t3[::-1]
            K.tri(t3, m)
E = RINGS[-1]; ec = Vector((0, 1.3, E[0].z))
for k in range(nL - 1):  # its back wall
    t3 = [ec, E[k], E[k + 1]]
    if (t3[1] - t3[0]).cross(t3[2] - t3[0]).z > 0: t3 = t3[::-1]
    K.tri(t3, 'skhole')

# the teeth: a row of stone pegs along the upper jaw over the cave, a couple missing, one fallen on the sand
for k in range(-4, 5):
    if k in (-3, 2): continue
    th = k * 0.052; top, _ = pt(th, PC); w = 0.2 + 0.04 * hsh(k, 1); L = 0.75 + 0.3 * hsh(k, 2) - 0.08 * abs(k)
    ax = Vector((math.cos(th), 0, math.sin(th)))  # along the jaw
    o = Vector((top.x, top.y + 0.2, top.z - 0.1))
    q0 = [o - ax * w, o + ax * w, o + ax * w + Vector((0, 0, 0.55)), o - ax * w + Vector((0, 0, 0.55))]
    tip = [v + Vector((0, -L, 0)) + (o - v) * 0.35 for v in q0]
    cen = o + Vector((0, -L / 2, 0.27))
    for c in range(4):
        c2 = (c + 1) % 4
        for t3 in ([q0[c], q0[c2], tip[c2]], [q0[c], tip[c2], tip[c]]):
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - cen) < 0: t3 = t3[::-1]
            K.tri(t3, 'sktooth' if c != 2 else 'skshade')
    for t3 in ([tip[0], tip[1], tip[2]], [tip[0], tip[2], tip[3]]):
        if (t3[1] - t3[0]).cross(t3[2] - t3[0]).y > 0: t3 = t3[::-1]
        K.tri(t3, 'skshade')
ft = Vector((3.6, 0.0, 58.0))  # the fallen one
fb = [ft + Vector((dx, dy, dz)) for dx, dy, dz in ((-0.3, -0.05, -0.7), (0.3, -0.05, -0.6), (0.38, -0.05, 0.6), (-0.34, -0.05, 0.7))]
fu = [v + Vector((0, 0.5 - 0.12 * c, 0)) + (ft - v) * 0.2 for c, v in enumerate(fb)]
for c in range(4):
    c2 = (c + 1) % 4
    for t3 in ([fb[c], fb[c2], fu[c2]], [fb[c], fu[c2], fu[c]]):
        if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot((t3[0] + t3[1] + t3[2]) / 3 - (ft + Vector((0, 0.2, 0)))) < 0: t3 = t3[::-1]
        K.tri(t3, 'sktooth')
for t3 in ([fu[0], fu[1], fu[2]], [fu[0], fu[2], fu[3]]):
    if (t3[1] - t3[0]).cross(t3[2] - t3[0]).y < 0: t3 = t3[::-1]
    K.tri(t3, 'sktooth')

for b in K.boxes: b['_done'] = True
K.solids = []
K.finish(OUT)
