# Skull Rock (Islands, Islands S&D; shared/map.js skullRock()): a sea rock the shape of a skull, and the spine you climb
# it by. the shape is the game's (shared/skullshape.js): the boxes you bump into are that shape, and this skins the very
# same grid of points (tools/arch/dumpskull.mjs -> boxes/skullrock_shape.json), so the look and the solid can't drift.
# what it is: a weathered stone skull half sunk in the beach, facing north at the volcano. a domed cranium (a crack
# across it, moss on top), a heavy brow, two deep eye sockets (a floor in each), the nose's hole, cheekbones, the upper
# jaw resting on the sand with a row of teeth over the cave mouth (the way in to the treasure). no lower jaw: the sea had it.
# skullspine.glb (Islands only): its neck bones, a steep stair of vertebrae out of the shallows up the back of its head.
# local frame: the skull's middle at x 0, z 69; it faces -z.
# run: node tools/arch/dumpskull.mjs tools/blender/arch/boxes/skullrock_shape.json
#      node tools/arch/dump.mjs islands skullrock tools/blender/arch/boxes/skullrock.json
#      node tools/arch/dump.mjs islands skullspine tools/blender/arch/boxes/skullspine.json
#      blender52 -b --python tools/blender/arch/make_skullrock.py -- [out dir]
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OD = argv[0] if argv else OUTDIR
OUT = os.path.join(OD, 'skullrock.glb')
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({'skbone': ('stucco', '#e2d8bc', {}), 'skshade': ('stucco', '#a89c7c', {}), 'skdeep': ('stucco', '#5c5244', {}), 'skhole': ('stucco', '#1c1820', {}),
             'skmoss': ('stucco', '#7c9450', {}), 'sktooth': ('stucco', '#f0ead6', {}), 'skcrack': ('stucco', '#3c3428', {})})
NOCAST.update({'skcrack'})
K = Kit(os.path.join(HERE, 'boxes', 'skullrock.json'), seed=3)
K.ground = -1e9

SH = json.load(open(os.path.join(HERE, 'boxes', 'skullrock_shape.json')))
C = Vector(SH['C'])               # the skull's middle (it is sunk in the beach to its upper teeth)
NT, NP, IC, JC = SH['NT'], SH['NP'], SH['IC'], SH['JC']  # columns round it, rows up it; the teeth's row; the cave mouth's half width in columns
P0, P1 = -1.0, math.pi / 2        # the rows' elevations: from under the sand to the crown
PC = P0 + (P1 - P0) * IC / NP     # the teeth line
G = [[(Vector(p[:3]), p[3]) for p in row] for row in SH['grid']]  # the skin: (point, how deep in a hollow)


def hsh(*a):
    x = 0.0
    for i, v in enumerate(a): x += math.sin(v * (12.9898 + i * 7.233) + i * 3.17) * 43758.5453
    return x - math.floor(x)


def on_row(i, th):  # a point of row i at azimuth th (0 = the face), between its columns
    f = (th + math.pi) / (2 * math.pi) * NT; j = math.floor(f); t = f - j
    return G[i][j % NT][0].lerp(G[i][(j + 1) % NT][0], t)


def tri(a, b, c, m):  # one of the skin's triangles. the skin's one sheet, so every cell winds the same way (a socket's level roof faces down: "away from the middle" would get it wrong)
    K.tri([a, c, b] if FLIP else [a, b, c], m)


_a, _b, _c = G[NP // 2][0][0], G[NP // 2][1][0], G[NP // 2 + 1][1][0]  # (which way: a cell on the back of the head, where out is plainly away from the middle)
FLIP = (_b - _a).cross(_c - _a).dot((_a + _b + _c) / 3 - C) < 0


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
        elif i >= NP - 6: m = 'skmoss'  # (the crown: all moss. patches of it up there are a pinwheel of slivers)
        elif out_up and ny > 0.82 and ph > 0.9 and hsh(i // 2, j // 2, 3) < 0.75: m = 'skmoss'
        elif hole > 0.1 or (ph < PC and hsh(i // 2, j // 5, 6) < 0.3): m = 'skshade'
        else: m = 'skbone'
        if i == NP - 1: tri(a, b, c, m)  # (the crown: the top row meets in a point)
        else: tri(a, b, c, m); tri(a, c, d, m)

# the cave: a real way in. its mouth is the hole left in the skin; from that edge a passage runs back into the skull,
# squaring off to the solid's 4 m x 3 m, darker the further in, to its back wall
j0, j1 = NT // 2 - JC, NT // 2 + JC
LOOP = [G[i][j0][0] for i in range(IC + 1)] + [G[IC][j][0] for j in range(j0 + 1, j1)] + [G[i][j1][0] for i in range(IC, -1, -1)]
HW, HT = SH['cave']['hw'] + 0.05, SH['cave']['top']  # (a hair outside the solid's cave: the boxes are what you touch)


def prof(v, k, n):  # where that point of the mouth's edge ends up on the passage's own outline
    ys = (HT - 0.25 + 0.35) / (LOOP[IC].y + 0.35)  # (the walls' rows squeezed under the passage's roof, none on top of another)
    if k <= IC: return (-HW, -0.35 + (v.y + 0.35) * ys)
    if k >= n - IC - 1: return (HW, -0.35 + (v.y + 0.35) * ys)
    x = max(-HW, min(HW, v.x * HW / abs(LOOP[IC].x))); return (x, HT - 0.25 + 0.3 * math.cos(math.pi / 2 * x / HW))


zf = max(v.z for v in LOOP); nL = len(LOOP); RINGS = [LOOP]
ZB = SH['cave']['back'] + 0.1
for d, w in ((1.0, 0.7), (3.0, 1.0), (7.0, 1.0), (ZB - zf, 1.0)):
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
for k in range(nL):  # its back wall (right round: the last one closes it along the sand)
    t3 = [ec, E[k], E[(k + 1) % nL]]
    if (t3[1] - t3[0]).cross(t3[2] - t3[0]).z > 0: t3 = t3[::-1]
    K.tri(t3, 'skhole')

# the teeth: a row of stone pegs along the upper jaw over the cave, a couple missing, one fallen on the sand
for k in range(-4, 5):
    if k in (-3, 2): continue
    th = k * 0.052; top = on_row(IC, th); w = 0.2 + 0.04 * hsh(k, 1); L = 0.75 + 0.3 * hsh(k, 2) - 0.08 * abs(k)
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

# ------------------------------------------------------------ the spine (skullspine.glb): its neck bones as a stair.
# each step of the game's flight is a vertebra (its top is the step: what you see is what you stand on), a wing either
# side, on a rib of darker rock that runs into the back of the skull
SPJ = os.path.join(HERE, 'boxes', 'skullspine.json')
if os.path.exists(SPJ):
    SP = json.load(open(SPJ))
    K2 = Kit(SP, seed=4); K2.ground = -1e9
    steps = sorted(SP['boxes'], key=lambda b: b['max'][1])  # the foot first
    HS = steps[0]['max'][0]; WT, WB, YB, DROP = 0.8, HS - 0.08, steps[0]['min'][1] - 0.07, 0.25  # the rib: half as wide under the bones, at its foot; how far down it goes; its top under each step's

    def face(p, m, out, kit=K2, sub=None):  # a quad wound to face along out
        p = [Vector(q) for q in p]
        if (p[1] - p[0]).cross(p[2] - p[0]).dot(Vector(out)) < 0: p = p[::-1]
        kit.quad(p, m, sub=sub)

    for i, b in enumerate(steps):
        za, zb, top = b['min'][2], b['max'][2], b['max'][1]
        zc = (za + zb) / 2; d = (zb - za) / 2 + 0.07; w = HS * (0.84 + 0.07 * hsh(i, 5)); ch = 0.17; th = 0.3
        K2.prism([(-w + ch, 0, zc - d), (w - ch, 0, zc - d), (w, 0, zc - d + ch), (w, 0, zc + d - ch), (w - ch, 0, zc + d), (-w + ch, 0, zc + d), (-w, 0, zc + d - ch), (-w, 0, zc - d + ch)], 1, top - th, top, 'sktooth')
        for s in (-1, 1):  # the wings
            x0 = s * (w - 0.03); tip = Vector((s * (w + 0.36 + 0.1 * hsh(i, s, 7)), top + 0.16 + 0.1 * hsh(i, s, 8), zc + 0.05))
            q = [Vector((x0, top - 0.27, zc - 0.11)), Vector((x0, top - 0.27, zc + 0.11)), Vector((x0, top - 0.03, zc + 0.11)), Vector((x0, top - 0.03, zc - 0.11))]
            cen = (sum(q, Vector()) / 4 + tip) / 2
            for c in range(4):
                t3 = [q[c], q[(c + 1) % 4], tip]
                if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot(sum(t3, Vector()) / 3 - cen) < 0: t3 = t3[::-1]
                K2.tri(t3, 'sktooth' if c != 0 else 'skshade')
        yt = top - DROP; m = 'skdeep' if hsh(i, 9) < 0.3 else 'skshade'
        for s in (-1, 1): face([(s * WB, YB, za), (s * WB, YB, zb), (s * WT, yt, zb), (s * WT, yt, za)], m, (s, 0, 0), sub=1.5)
        lo = steps[i - 1]['max'][1] - DROP if i else YB  # the riser between this step's rock and the one below's
        face([(-WT, lo, zb), (WT, lo, zb), (WT, yt, zb), (-WT, yt, zb)], 'skdeep', (0, 0, 1))
    zh, yh = steps[-1]['min'][2], steps[-1]['max'][1] - DROP  # its head: on into the back of the skull
    for s in (-1, 1): face([(s * WB, YB, zh - 0.9), (s * WB, YB, zh), (s * WT, yh, zh), (s * WT, yh, zh - 0.9)], 'skshade', (s, 0, 0), sub=1.5)
    face([(-WT, yh, zh - 0.9), (WT, yh, zh - 0.9), (WT, yh, zh), (-WT, yh, zh)], 'skshade', (0, 1, 0))
    for b in K2.boxes: b['_done'] = True
    K2.solids = []
    K2.finish(os.path.join(OD, 'skullspine.glb'))
