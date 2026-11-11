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

# the cave: a throat in under the teeth to a chamber round the chest (the solid's shape: shared/skullshape.js
# caveProfile / caveBack). its mouth is the hole left in the skin; rings of rough rock run back from that edge, walls
# standing to the arch's spring, the arch over, bone-pale ribs across the roof every metre and a half (proud only above
# head height), widening past the chest into a rounded chamber, darker the further in
CV = SH['cave']
def csm(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def cprof(z):
    t = csm((z - CV['from']) / CV['len']); w = CV['hw'] + (CV['wide'] - CV['hw']) * t; h = CV['top'] + (CV['high'] - CV['top']) * t
    return w, h * 0.55, h
def cback(x): return CV['back'] + 0.7 * math.sqrt(max(0.0, 1 - (x / CV['wide']) ** 2))
j0, j1 = NT // 2 - JC, NT // 2 + JC
LOOP = [G[i][j0][0] for i in range(IC + 1)] + [G[IC][j][0] for j in range(j0 + 1, j1)] + [G[i][j1][0] for i in range(IC, -1, -1)]
nL = len(LOOP); zf = max(v.z for v in LOOP)
RIBS = [zf + 1.4 + 1.5 * k for k in range(8)]
def rib(z): return max(math.exp(-((z - r) / 0.28) ** 2) for r in RIBS)
def cpt(sv, z, out=0.06):
    """the cave's outline at z, sv 0..1 round it (left floor, up the wall, over the arch, down to the right floor);
    out: how far outside the solid's surface (rough: more on the walls, ribs proud inward up the arch)"""
    w, hs, h = cprof(z)
    rough = (hsh(round(sv * 23), round(z * 2.1)) - 0.5) * 0.12 + 0.06 * math.sin(z * 2.3 + sv * 9)
    if sv < 0.25: x, y, nx, ny = -w, hs * sv / 0.25, -1, 0
    elif sv > 0.75: x, y, nx, ny = w, hs * (1 - sv) / 0.25, 1, 0
    else:
        a = math.pi * (1 - (sv - 0.25) / 0.5); x, y = w * math.cos(a), hs + (h - hs) * math.sin(a)
        nx, ny = math.cos(a) / w, math.sin(a) / max(0.01, h - hs); L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
    d = out + max(0.0, rough) - (0.16 * rib(z) if y > 2.1 else 0.0)
    return Vector((x + nx * d, max(-0.3, y + ny * d), z))
NS = nL  # (one ring point per point of the mouth's edge)
SV = [k / (NS - 1) for k in range(NS)]
ZS = [zf + 0.6]
while ZS[-1] < CV['back'] - 0.2: ZS.append(ZS[-1] + 0.25)
RINGS = [LOOP] + [[cpt(sv, z) for sv in SV] for z in ZS]
RINGS[1] = [LOOP[k].lerp(RINGS[1][k], 0.85) for k in range(NS)]  # (the first ring eases off the mouth's edge)
axis = lambda z: Vector((0, 1.4, z))
for ri in range(len(RINGS) - 1):
    A, B2 = RINGS[ri], RINGS[ri + 1]; zc = (A[NS // 2].z + B2[NS // 2].z) / 2
    for k in range(NS - 1):
        hy = (A[k].y + A[k + 1].y) / 2
        m = 'skbone' if (rib(zc) > 0.45 and hy > 2.0) else ('skshade' if zc < zf + 2.5 else 'skdeep')
        for t3 in ([A[k], A[k + 1], B2[k + 1]], [A[k], B2[k + 1], B2[k]]):
            cc = (t3[0] + t3[1] + t3[2]) / 3
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot(axis(cc.z) - cc) < 0: t3 = t3[::-1]
            K.tri(t3, m)
# the chamber's back: the last ring closed with a rounded wall, out to caveBack in the middle
E = RINGS[-1]; NB = 4
BACK = [E] + [[Vector((p.x * (1 - (b / NB) ** 2 * 0.85), p.y * (1 - (b / NB) ** 2 * 0.6) + 0.4 * (b / NB) ** 2, p.z + (cback(p.x) + 0.08 - p.z) * math.sin(b / NB * math.pi / 2))) for p in E] for b in range(1, NB + 1)]
for bi in range(NB):
    A, B2 = BACK[bi], BACK[bi + 1]
    for k in range(NS - 1):
        for t3 in ([A[k], A[k + 1], B2[k + 1]], [A[k], B2[k + 1], B2[k]]):
            cc = (t3[0] + t3[1] + t3[2]) / 3
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).dot(Vector((0, 1.4, cc.z - 1.0)) - cc) < 0: t3 = t3[::-1]
            if (t3[1] - t3[0]).cross(t3[2] - t3[0]).length > 1e-9: K.tri(t3, 'skdeep')
F = BACK[-1]; fc = sum(F, Vector()) / len(F)
for k in range(NS):
    t3 = [fc, F[k], F[(k + 1) % NS]]
    if (t3[1] - t3[0]).cross(t3[2] - t3[0]).z > 0: t3 = t3[::-1]
    if (t3[1] - t3[0]).cross(t3[2] - t3[0]).length > 1e-9: K.tri(t3, 'skdeep')

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

    def vert_ring(zc, top, w, hgt, ch):  # a vertebra body's cross-section (x, y): flat on top (the step), rounded under
        return [(-w + ch, top), (w - ch, top), (w, top - ch), (w, top - hgt + ch * 1.6), (w - ch * 1.6, top - hgt), (-w + ch * 1.6, top - hgt), (-w, top - hgt + ch * 1.6), (-w, top - ch)]

    def prism_z(sec, z0, z1, m, kit=K2):  # a cross-section in x, y run along z from z0 to z1, closed at both ends
        n = len(sec); cen = Vector((sum(p[0] for p in sec) / n, sum(p[1] for p in sec) / n, (z0 + z1) / 2))
        for k in range(n):
            a, b2 = sec[k], sec[(k + 1) % n]
            face([(a[0], a[1], z0), (b2[0], b2[1], z0), (b2[0], b2[1], z1), (a[0], a[1], z1)], m, Vector(((a[0] + b2[0]) / 2, (a[1] + b2[1]) / 2, (z0 + z1) / 2)) - cen, kit=kit)
        for (zz, sz) in ((z0, -1), (z1, 1)):
            for k in range(1, n - 1):
                t3 = [Vector((sec[0][0], sec[0][1], zz)), Vector((sec[k][0], sec[k][1], zz)), Vector((sec[k + 1][0], sec[k + 1][1], zz))]
                if (t3[1] - t3[0]).cross(t3[2] - t3[0]).z * sz < 0: t3 = t3[::-1]
                kit.tri(t3, m)

    for i, b in enumerate(steps):
        za, zb, top = b['min'][2], b['max'][2], b['max'][1]
        w = HS * (0.9 + 0.05 * hsh(i, 5)); g = 0.035  # (a disc between each body and the next: the step's edge)
        prism_z(vert_ring(0, top, w, 0.62, 0.2), za + g, zb - g, 'sktooth')
        prism_z(vert_ring(0, top - 0.06, w - 0.08, 0.5, 0.16), za - g - 0.025, za + g + 0.025, 'skdeep')  # (its ends well inside the bodies either side)
        for s in (-1, 1):  # the transverse processes: big flat bony wings out and down, a knob on the end
            zc = (za + zb) / 2 + 0.02 * (hsh(i, s) - 0.5)
            root = Vector((s * (w - 0.05), top - 0.26, zc)); tip = Vector((s * (w + 1.15 + 0.2 * hsh(i, s, 7)), top - 0.3 - 0.35 * hsh(i, s, 8), zc + 0.08))  # (long: the spine's outline from the side)
            up = Vector((0, 1, 0)); d = (tip - root).normalized(); side = d.cross(up).normalized()
            hw0, hw1, th0, th1 = 0.1, 0.07, 0.12, 0.08  # (narrower than the body's depth: its sides never lie on the body's ends)
            A = [root + side * hw0 + up * th0, root - side * hw0 + up * th0, root - side * hw0 - up * th0, root + side * hw0 - up * th0]
            B3 = [tip + side * hw1 + up * th1, tip - side * hw1 + up * th1, tip - side * hw1 - up * th1, tip + side * hw1 - up * th1]
            mid = (root + tip) / 2
            for k in range(4): face([A[k], A[(k + 1) % 4], B3[(k + 1) % 4], B3[k]], 'sktooth', (A[k] + B3[(k + 1) % 4]) / 2 - mid)
            face([B3[0], B3[1], B3[2], B3[3]], 'sktooth', d)
    for b in K2.boxes: b['_done'] = True
    K2.solids = []
    K2.finish(os.path.join(OD, 'skullspine.glb'))
