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

C = Vector((0.0, 5.6, 69.0))      # the skull's middle (its upper jaw stands on the sand)
RX, RY, RZ = 9.0, 6.6, 9.2        # half sizes of the cranium
NT, NP = 104, 52
P0, P1 = -1.05, math.pi / 2       # elevation: from under the sand to the crown


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
    r -= low * (0.2 * max(0.0, front) ** 0.6 + 0.16 * abs(math.sin(th)) ** 2 + 0.05 * max(0.0, -front))
    r += 0.06 * g(th, ph, 0, -0.44, 0.6, 0.08)                          # the upper jaw's ridge, where the teeth sit
    r += (hsh(round(th * 9), round(ph * 9)) - 0.5) * 0.02               # weathered, in facets
    return r, hole


PC = -0.5  # below this the skull is its upper jaw and the rock it stands on: straight down to the sand


def pt(th, ph):
    cp = math.cos(max(ph, PC)); r, hole = radius(th, max(ph, PC))
    y = C.y + math.sin(max(ph, PC)) * RY * r * (1.0 + 0.1 * max(0, math.sin(ph)))
    if ph < PC:
        t = (PC - ph) / (PC - P0)
        m = math.exp(-abs(th / 0.36) ** 4) * min(1.0, t * 5)  # the cave: between the teeth, down to the sand
        r = r * (1 - 0.07 * t + 0.05 * math.sin(th * 7 + 1) * t) - 0.55 * m; hole = m
        y = y + (-0.35 - y) * t
    # th 0 = the face = -z; +th turns toward +x
    return Vector((C.x + math.sin(th) * cp * RX * r, y, C.z - math.cos(th) * cp * RZ * r)), hole


G = [[pt(2 * math.pi * j / NT - math.pi, P0 + (P1 - P0) * i / NP) for j in range(NT)] for i in range(NP + 1)]


def tri(a, b, c, m):
    K.tri([a, b, c] if (b - a).cross(c - a).dot((a + b + c) / 3 - C) > 0 else [a, c, b], m)


CRACK = lambda th, ph: abs(ph - (0.95 + 0.16 * math.sin(th * 2.3 + 0.6) + 0.05 * math.sin(th * 9))) < 0.022 and abs(th) < 2.2  # the suture across the crown
for i in range(NP):
    ph = P0 + (P1 - P0) * (i + 0.5) / NP
    for j in range(NT):
        j2 = (j + 1) % NT; th = 2 * math.pi * (j + 0.5) / NT - math.pi
        (a, ha), (b, hb), (c, hc), (d, hd) = G[i][j], G[i][j2], G[i + 1][j2], G[i + 1][j]
        hole = (ha + hb + hc + hd) / 4
        nrm = (b - a).cross(d - a); ny = abs(nrm.normalized().y) if nrm.length > 1e-9 else 1; out_up = ((a + c) / 2 - C).y > 0
        if hole > 0.62: m = 'skhole'
        elif hole > 0.3: m = 'skdeep'
        elif CRACK(th, ph): m = 'skcrack'
        elif out_up and ny > 0.82 and ph > 0.9 and hsh(i // 2, j // 2, 3) < 0.75: m = 'skmoss'
        elif hole > 0.1 or (ph < PC and hsh(i, j // 4, 6) < 0.5): m = 'skshade'
        else: m = 'skbone'
        if i == NP - 1: tri(a, b, c, m)  # (the crown: the top row meets in a point)
        else: tri(a, b, c, m); tri(a, c, d, m)

# the teeth: a row of stone pegs along the upper jaw over the cave, a couple missing, one fallen on the sand
for k in range(-5, 6):
    if k in (-3, 2): continue
    th = k * 0.058; top, _ = pt(th, PC); w = 0.34 + 0.06 * hsh(k, 1); L = 1.25 + 0.5 * hsh(k, 2) - 0.18 * abs(k)
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
