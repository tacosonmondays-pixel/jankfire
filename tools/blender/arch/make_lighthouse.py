# The Islands lighthouse (shared/map.js lighthouse()): drawn over its own boxes (tools/arch/dump.mjs), which stay what
# you bump into. a square tower in red and white bands on a stone plinth, string courses between the bands, white corner
# pilasters, small windows, a door at the foot; an iron stair once round the outside to a gallery on brackets with a
# railing; the lantern room (an iron frame round the light, a brass lens stand; the light itself is the game's, it
# glows), a red domed roof, a vent ball and a lightning rod. Islands S&D's has no stair and no gallery (lighthouse_sd).
# local frame = the map's (the tower at x 79..85, z -9..-3).
# run: node tools/arch/dump.mjs islands lighthouse tools/blender/arch/boxes/lighthouse.json
#      node tools/arch/dump.mjs islands_sd lighthouse_sd tools/blender/arch/boxes/lighthouse_sd.json
#      blender52 -b --python tools/blender/arch/make_lighthouse.py -- [lighthouse|lighthouse_sd]   (both by default)
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'lhwhite': ('trim', '#ffffff', {}), 'lhred': ('trim', '#f0302a', {}), 'course': ('trim', '#e2dccf', {}), 'plinth': ('concrete', '#c4bcae', {}),
    'iron': ('metalplate', '#3a3c44', {}), 'tread': ('metalplate', '#9a9ca6', {}), 'roof': ('stucco', '#d8302a', {}), 'brass': ('metalplate', '#e0b040', {}),
    'pane': ('glass', '#283040', {}), 'door': ('planks', '#3a8ad8', {}), 'frame': ('trim', '#ffffff', {}),
})
NOCAST.update({'iron', 'brass', 'pane', 'frame'})
X0, X1, Z0, Z1, TOP = 79.0, 85.0, -9.0, -3.0, 18.0  # the tower
CX, CZ = 82.0, -6.0
O = 0.03  # the skin off the boxes


def face_quad(axis, c, s, a0, a1, y0, y1, m, o=O, uv=None):
    """a flat quad on a face of the tower: axis 'x' = at x = c (runs along z), 'z' = at z = c (runs along x); s: facing"""
    if axis == 'z': q = [Vector((a0, y0, c + s * o)), Vector((a1, y0, c + s * o)), Vector((a1, y1, c + s * o)), Vector((a0, y1, c + s * o))]
    else: q = [Vector((c + s * o, y0, a0)), Vector((c + s * o, y0, a1)), Vector((c + s * o, y1, a1)), Vector((c + s * o, y1, a0))]
    n = (q[1] - q[0]).cross(q[3] - q[0]); want = Vector((0, 0, s)) if axis == 'z' else Vector((s, 0, 0))
    K.quad(q if n.dot(want) > 0 else q[::-1], m, sub=1.5)


FACES = [('z', Z0, -1, X0, X1), ('z', Z1, 1, X0, X1), ('x', X0, -1, Z0, Z1), ('x', X1, 1, Z0, Z1)]


def build(kind):
    global K
    K = Kit(os.path.join(HERE, 'boxes', kind + '.json'), seed=3)
    K.ground = 0.0
    for b in K.boxes: b['_done'] = True
    R = random.Random(3)
    # ---- the tower: bands, string courses, pilasters, the plinth
    for (axis, c, s, a0, a1) in FACES:
        for k, (y0, y1) in enumerate(((1.0, 4.5), (4.5, 9.0), (9.0, 13.5), (13.5, TOP))):
            face_quad(axis, c, s, a0 + 0.3, a1 - 0.3, y0, y1, 'lhred' if k % 2 else 'lhwhite')
    for y in (4.5, 9.0, 13.5):  # string courses: a proud band round the tower at each change of colour
        FL.obox(K, (X0 - 0.09, y - 0.09, Z0 - 0.09), (X1 + 0.09, y + 0.09, Z1 + 0.09), 'course')
    FL.obox(K, (X0 - 0.16, TOP - 0.3, Z0 - 0.16), (X1 + 0.16, TOP - (0.02 if kind == 'lighthouse' else 0), Z1 + 0.16), 'course')  # the cornice under the top (under the gallery's floor)
    for (x, z) in ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1)):  # corner pilasters, white, full height
        FL.obox(K, (x - 0.32, 1.12, z - 0.32), (x + 0.32, TOP - 0.3, z + 0.32), 'lhwhite')
    FL.obox(K, (X0 - 0.22, 0.0, Z0 - 0.22), (X1 + 0.22, 1.0, Z1 + 0.22), 'plinth')
    FL.obox(K, (X0 - 0.12, 1.0, Z0 - 0.12), (X1 + 0.12, 1.12, Z1 + 0.12), 'plinth')
    # windows: small and deep, a white frame and sill, a dark pane; staggered up the faces (each sits in a band)
    for (axis, c, s, a0, a1), ys in zip(FACES, ((6.2, 15.4), (10.6,), (7.4, 15.2), (11.4,))):
        for y in ys:
            m = (a0 + a1) / 2 + R.uniform(-0.8, 0.8)
            face_quad(axis, c, s, m - 0.35, m + 0.35, y, y + 1.1, 'pane', o=O + 0.002)
            for (b0, b1, z0, z1, t) in ((m - 0.47, m + 0.47, y - 0.16, y, 0.1), (m - 0.47, m + 0.47, y + 1.1, y + 1.22, 0.1), (m - 0.46, m - 0.35, y - 0.01, y + 1.11, 0.095), (m + 0.35, m + 0.46, y - 0.01, y + 1.11, 0.095)):
                if axis == 'z': FL.obox(K, (b0, z0, min(c + s * 0.021, c + s * t)), (b1, z1, max(c + s * 0.021, c + s * t)), 'frame')  # (the sides overlap the head and sill a hair: no shared corners)
                else: FL.obox(K, (min(c + s * 0.021, c + s * t), z0, b0), (max(c + s * 0.021, c + s * t), z1, b1), 'frame')
            if axis == 'z': FL.obox(K, (m - 0.55, y - 0.24, min(c + s * 0.02, c + s * 0.18)), (m + 0.55, y - 0.16, max(c + s * 0.02, c + s * 0.18)), 'course')
            else: FL.obox(K, (min(c + s * 0.02, c + s * 0.18), y - 0.24, m - 0.55), (max(c + s * 0.02, c + s * 0.18), y - 0.16, m + 0.55), 'course')
    # the door: on the north face at the foot, blue, in a white frame, a stone step
    face_quad('z', Z0, -1, 81.25, 82.75, 1.12, 3.3, 'door', o=0.24)
    for (b0, b1, y0, y1, t) in ((81.06, 81.25, 1.12, 3.49, 0.29), (82.75, 82.94, 1.12, 3.49, 0.29), (81.05, 82.95, 3.3, 3.5, 0.3)): FL.obox(K, (b0, y0, Z0 - t), (b1, y1, Z0 - 0.02), 'frame')
    FL.tube(K, (82.5, 2.2, Z0 - 0.24), (82.5, 2.2, Z0 - 0.34), 0.05, 0.05, 'brass', n=6)
    FL.obox(K, (80.85, 0.0, Z0 - 0.75), (83.15, 0.2, Z0 - 0.22), 'plinth')

    # ---- the top: the roof round the lantern room (S&D) or the gallery (Islands), the lantern room, the dome
    if kind == 'lighthouse_sd':
        K.quad([Vector((X0 - 0.16, TOP + 0.005, Z1 + 0.16)), Vector((X1 + 0.16, TOP + 0.005, Z1 + 0.16)), Vector((X1 + 0.16, TOP + 0.005, Z0 - 0.16)), Vector((X0 - 0.16, TOP + 0.005, Z0 - 0.16))], 'tread', sub=2)
        for (x0, z0, x1, z1) in ((X0 - 0.16, Z0 - 0.16, X1 + 0.16, Z0 - 0.04), (X0 - 0.16, Z1 + 0.04, X1 + 0.16, Z1 + 0.16), (X0 - 0.16, Z0 - 0.04, X0 - 0.04, Z1 + 0.04), (X1 + 0.04, Z0 - 0.04, X1 + 0.16, Z1 + 0.04)):
            FL.obox(K, (x0, TOP, z0), (x1, TOP + 0.5, z1), 'iron')  # a low iron kerb round the roof
    lr = (80.0, 84.0, -8.0, -4.0)  # the lantern room's glass box
    FL.obox(K, (lr[0] - 0.04, TOP, lr[2] - 0.04), (lr[1] + 0.04, TOP + 0.9, lr[3] + 0.04), 'lhwhite')  # its low wall
    FL.obox(K, (lr[0] - 0.1, TOP + 0.9, lr[2] - 0.1), (lr[1] + 0.1, TOP + 1.0, lr[3] + 0.1), 'iron')
    for (x, z) in ((lr[0], lr[2]), (lr[1], lr[2]), (lr[0], lr[3]), (lr[1], lr[3]), (82.0, lr[2]), (82.0, lr[3]), (lr[0], -6.0), (lr[1], -6.0)):
        FL.obox(K, (x - 0.07, TOP + 1.0, z - 0.07), (x + 0.07, 20.99, z + 0.07), 'iron')  # mullions (the glass between them is clear)
    FL.obox(K, (lr[0] - 0.085, 20.0, lr[2] - 0.085), (lr[1] + 0.085, 20.06, lr[3] + 0.085), 'iron')
    for (x0, z0, x1, z1) in ((lr[0] - 0.1, lr[2] - 0.1, lr[1] + 0.1, lr[2] - 0.04), (lr[0] - 0.1, lr[3] + 0.04, lr[1] + 0.1, lr[3] + 0.1),
                             (lr[0] - 0.1, lr[2] - 0.04, lr[0] - 0.04, lr[3] + 0.04), (lr[1] + 0.04, lr[2] - 0.04, lr[1] + 0.1, lr[3] + 0.04)):
        FL.obox(K, (x0, 20.86, z0), (x1, 21.0, z1), 'iron')  # the head of the frame
    FL.tube(K, (CX, TOP + 0.9, CZ), (CX, 18.58, CZ), 0.55, 0.42, 'brass', n=10, caps=(False, True))  # the lens stand (the light sits on it)
    # the roof: a red dome on the slab, its rim, the cap, the vent ball, the lightning rod
    FL.obox(K, (79.55, 21.0, -8.45), (84.45, 21.18, -3.55), 'roof')
    n = 6
    for k in range(n):  # four curved faces, square at the foot, rising to the cap
        t0, t1 = k / n, (k + 1) / n
        def ring(t): h = 2.4 * (1 - (1 - t) ** 2) ** 0.5 * 0 + 0; s = 2.42 * (1 - t ** 1.6); return s, 21.18 + 1.25 * math.sin(t * math.pi / 2)
        s0, y0 = ring(t0); s1, y1 = ring(t1)
        s1 = max(s1, 0.32)
        for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            q = [Vector((CX + a[0] * s0, y0, CZ + a[1] * s0)), Vector((CX + b[0] * s0, y0, CZ + b[1] * s0)), Vector((CX + b[0] * s1, y1, CZ + b[1] * s1)), Vector((CX + a[0] * s1, y1, CZ + a[1] * s1))]
            nn = (q[1] - q[0]).cross(q[3] - q[0]); c = sum(q, Vector()) / 4
            K.quad(q if nn.dot(c - Vector((CX, 21, CZ))) > 0 else q[::-1], 'roof')
    FL.tube(K, (CX, 22.43, CZ), (CX, 22.55, CZ), 0.45, 0.45, 'iron', n=10)
    pts = []
    for j in range(7):  # the vent ball
        la = -math.pi / 2 + math.pi * j / 6; pts.append([Vector((CX + 0.32 * math.cos(la) * math.cos(2 * math.pi * i / 10), 22.86 + 0.32 * math.sin(la), CZ + 0.32 * math.cos(la) * math.sin(2 * math.pi * i / 10))) for i in range(10)])
    for j in range(6):
        for i in range(10):
            a, b, c, d = pts[j][i], pts[j][(i + 1) % 10], pts[j + 1][(i + 1) % 10], pts[j + 1][i]
            if j == 0: K.tri([a, c, d], 'iron')
            elif j == 5: K.tri([a, b, d], 'iron')
            else: K.quad([a, b, c, d], 'iron')
    FL.tube(K, (CX, 23.15, CZ), (CX, 24.4, CZ), 0.04, 0.0, 'brass', n=6)

    if kind == 'lighthouse':
        # ---- the stair: each step is solid iron to the flight's foot (as its box is), a chequer tread on top
        rails, steps, gal = [], [], []
        for b in K.boxes:
            (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
            if b['mat'] != 'metal': continue
            if abs(y1 - y0 - 1.0) < 0.06 and min(x1 - x0, z1 - z0) <= 0.11: rails.append(b)
            elif abs(y0 - 17.6) < 1e-3: gal.append(b)
            else: steps.append(b)
        for b in steps: K.box(b['min'], b['max'], {'top': 'tread', 'px': 'iron', 'nx': 'iron', 'pz': 'iron', 'nz': 'iron', 'bottom': 'iron'}, cull=True)
        # the stair's handrails: a post at each step's rail, a rail along their tops
        stair_rails = [b for b in rails if b['min'][1] < 17.9]
        def mid(b): return Vector(((b['min'][0] + b['max'][0]) / 2, b['min'][1], (b['min'][2] + b['max'][2]) / 2))
        for b in stair_rails:
            p = mid(b); FL.obox(K, (p.x - 0.03, p.y, p.z - 0.03), (p.x + 0.03, p.y + 1.0, p.z + 0.03), 'iron')
        srt = sorted(stair_rails, key=lambda b: b['min'][1])
        for a, b in zip(srt, srt[1:]):
            pa, pb = mid(a), mid(b)
            if (pa - pb).length < 1.0: FL.bar(K, pa + Vector((0, 1.0, 0)), pb + Vector((0, 1.0, 0)), 0.06, 'iron')
        # the gallery: a chequer floor, its edge, brackets under it, a railing on top of the rail boxes
        for b in gal:
            (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
            K.box((x0, y0, z0), (x1, y1, z1), {'top': 'tread', 'px': 'iron', 'nx': 'iron', 'pz': 'iron', 'nz': 'iron', 'bottom': 'iron'}, cull=True)
        for (axis, c, s, a0, a1) in FACES:  # brackets: struts from the tower out under the gallery's edge (not the west: the stair)
            if axis == 'x' and s < 0: continue
            a = a0 + 0.6
            while a < a1 - 0.5:
                out = 2.75 if not (axis == 'x' and s < 0) else 1.35  # (the west side: the stair's hole)
                if axis == 'z': FL.bar(K, (a, 15.3, c + s * 0.05), (a, 17.58, c + s * out), 0.12, 'iron'); FL.bar(K, (a, 17.5, c + s * 0.05), (a, 17.5, c + s * out), 0.1, 'iron')
                else: FL.bar(K, (c + s * 0.05, 15.3, a), (c + s * out, 17.58, a), 0.12, 'iron'); FL.bar(K, (c + s * 0.05, 17.5, a), (c + s * out, 17.5, a), 0.1, 'iron')
                a += 1.2
        for b in [b for b in rails if b['min'][1] >= 17.9]:  # the gallery's railing: posts, a top rail, a middle rail, a kick plate
            (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
            alongx = (x1 - x0) > (z1 - z0); L = (x1 - x0) if alongx else (z1 - z0); n = max(1, round(L / 1.2))
            for k in range(n + 1):
                if not alongx and k in (0, n): continue  # (the corners' posts are the long sides')
                t = k / n
                x = x0 + (x1 - x0) * t if alongx else (x0 + x1) / 2; z = (z0 + z1) / 2 if alongx else z0 + (z1 - z0) * t
                FL.obox(K, (x - 0.035, y0 + 0.004, z - 0.035), (x + 0.035, y1 - 0.004, z + 0.035), 'iron')  # (ends inside the rails)
            for (ya, yb) in ((y1 - 0.06, y1), (y0 + 0.48, y0 + 0.53), (y0, y0 + 0.12)):
                FL.obox(K, (x0 + (0.01 if not alongx else 0), ya, z0 + (0.01 if alongx else 0)), (x1 - (0.01 if not alongx else 0), yb, z1 - (0.01 if alongx else 0)), 'iron')
    else:
        for b in K.boxes: pass
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in ('lighthouse', 'lighthouse_sd')] or ['lighthouse', 'lighthouse_sd']):
    build(kind)
