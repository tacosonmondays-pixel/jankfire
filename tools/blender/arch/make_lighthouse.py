# The Islands lighthouse (shared/map.js lighthouse()): drawn over its own boxes (tools/arch/dump.mjs), which stay what
# you bump into (an octagon in boxes: octoBoxes). An octagonal masonry tower, 6 m across its flats, tapering a little
# toward the top (its corners cut deeper as it rises), on a flared stone plinth; red and white bands with string
# courses between them, small framed windows climbing round it with the stair, a door at the foot; the iron stair
# once round the outside (the game's steps) to an octagonal gallery on long iron brackets with a baluster railing; the
# lantern room, an octagon of glowing glass behind diamond glazing bars, under a red domed cap with a vent ball and
# a lightning rod (the light inside is the game's). Islands S&D's has no stair and no gallery (lighthouse_sd).
# local frame = the map's (the tower over x 79..85, z -9..-3).
# run: node tools/arch/dump.mjs islands lighthouse tools/blender/arch/boxes/lighthouse.json
#      node tools/arch/dump.mjs islands_sd lighthouse_sd tools/blender/arch/boxes/lighthouse_sd.json
#      blender52 -b --python tools/blender/arch/make_lighthouse.py -- [lighthouse|lighthouse_sd]   (both by default)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmesh
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'lhwhite': ('trim', '#ffffff', {}), 'lhred': ('trim', '#f0302a', {}), 'course': ('trim', '#e2dccf', {}), 'plinth': ('concrete', '#c4bcae', {}),
    'iron': ('metalplate', '#3a3c44', {}), 'tread': ('metalplate', '#9a9ca6', {}), 'roof': ('trim', '#d8302a', {}), 'brass': ('metalplate', '#e0b040', {}),
    'pane': ('glass', '#283040', {}), 'door': ('planks', '#3a8ad8', {}), 'frame': ('trim', '#ffffff', {}), 'lamp': ('stucco', '#ffd98a', {'glow': True}),
})
NOCAST.update({'iron', 'brass', 'pane', 'frame', 'lamp'})
X0, X1, Z0, Z1, TOP = 79.0, 85.0, -9.0, -3.0, 18.0  # the tower's flats
CX, CZ = 82.0, -6.0


def octo(x0, z0, x1, z1, c, y, o=0.0):
    """the 8 corners of an octagon over a rectangle (flats on its sides, corners cut c), pushed out o, at height y,
    in order round it"""
    c = c + o * (2 - math.sqrt(2)); x0 -= o; z0 -= o; x1 += o; z1 += o
    return [Vector(p) for p in ((x0 + c, y, z0), (x1 - c, y, z0), (x1, y, z0 + c), (x1, y, z1 - c), (x1 - c, y, z1), (x0 + c, y, z1), (x0, y, z1 - c), (x0, y, z0 + c))]


def face_out(q, mat, centre=None, sub=None):
    """a quad (or tri) wound to face away from the centre line (or from centre)"""
    cen = sum(q, Vector()) / len(q); ref = Vector((CX, cen.y, CZ)) if centre is None else centre
    n = (q[1] - q[0]).cross(q[-1] - q[0])
    if n.dot(cen - ref) < 0: q = q[::-1]
    if len(q) == 3: K.tri(q, mat)
    else: K.quad(q, mat, sub=sub)


def band(A, B, mat, sub=1.5):
    """the skin between two rings of 8 (A below, B above)"""
    for i in range(8):
        j = (i + 1) % 8
        face_out([A[i], A[j], B[j], B[i]], mat, sub=sub)


def cap(R, mat, up=True):
    """an octagon's flat top (or underside): a fan round its middle"""
    c = sum(R, Vector()) / 8
    for i in range(8):
        t = [c, R[i], R[(i + 1) % 8]]
        n = (t[1] - t[0]).cross(t[2] - t[0])
        K.tri(t if (n.y > 0) == up else t[::-1], mat)


def taper(y):  # the tower's corner cut at height y: deeper toward the top (it narrows across the corners)
    return 1.62 + 0.4 * max(0.0, min(1.0, (y - 1.2) / (TOP - 1.4)))


def ring(y, o=0.03): return octo(X0, Z0, X1, Z1, taper(y), y, o)


def inside(p, poly):
    x, z = p[0], p[1]; n = len(poly); c = False
    for i in range(n):
        (ax, az), (bx, bz) = poly[i], poly[(i + 1) % n]
        if (az > z) != (bz > z) and x < ax + (z - az) * (bx - ax) / (bz - az): c = not c
    return c


def poly_fill(outer, holes, y, mat, up=True):
    """a flat floor: the outer outline (x, z) with holes cut out, triangulated, at height y"""
    bm = bmesh.new(); edges = []
    for pts in [outer] + holes:
        vs = [bm.verts.new((p[0], p[1], 0.0)) for p in pts]
        edges += [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    for f in [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]:
        cen = f.calc_center_median()
        if any(inside((cen.x, cen.y), h) for h in holes) or not inside((cen.x, cen.y), outer): continue
        t = [Vector((v.co.x, y, v.co.y)) for v in f.verts]
        n = (t[1] - t[0]).cross(t[2] - t[0])
        if n.length < 1e-4: continue  # (a sliver)
        K.tri(t if (n.y > 0) == up else t[::-1], mat)
    bm.free()


def window(face, y, h=1.1, w=0.7):
    """a small framed window on tower face `face` (0..7, the ring's edges) centred at height y"""
    A, B = ring(y - h / 2), ring(y + h / 2)
    a0, a1, b0, b1 = A[face], A[(face + 1) % 8], B[face], B[(face + 1) % 8]
    c = (a0 + a1 + b0 + b1) / 4; along = (a1 - a0).normalized(); up = ((b0 + b1) / 2 - (a0 + a1) / 2).normalized()
    out = along.cross(up).normalized()
    if out.dot(Vector((c.x - CX, 0, c.z - CZ))) < 0: out = -out
    def P(u, v, d): return c + along * u + up * v + out * d
    face_out([P(-w / 2 - 0.03, -h / 2 - 0.03, 0.03), P(w / 2 + 0.03, -h / 2 - 0.03, 0.03), P(w / 2 + 0.03, h / 2 + 0.03, 0.03), P(-w / 2 - 0.03, h / 2 + 0.03, 0.03)], 'pane', centre=c - out)  # (its edges under the frame)
    # the frame: one moulding round it (front, outer and inner edges back to the wall), no overlapping pieces
    o_, i_ = [(-w / 2 - 0.1, -h / 2 - 0.1), (w / 2 + 0.1, -h / 2 - 0.1), (w / 2 + 0.1, h / 2 + 0.1), (-w / 2 - 0.1, h / 2 + 0.1)], [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    for k in range(4):
        k2 = (k + 1) % 4
        face_out([P(*o_[k], 0.07), P(*o_[k2], 0.07), P(*i_[k2], 0.07), P(*i_[k], 0.07)], 'frame', centre=c - out * 2)
        em = (P(*o_[k], 0) + P(*o_[k2], 0)) / 2; face_out([P(*o_[k], 0.07), P(*o_[k2], 0.07), P(*o_[k2], 0.005), P(*o_[k], 0.005)], 'frame', centre=c)
        im = (P(*i_[k], 0) + P(*i_[k2], 0)) / 2; face_out([P(*i_[k], 0.07), P(*i_[k2], 0.07), P(*i_[k2], 0.015), P(*i_[k], 0.015)], 'frame', centre=im + (im - c).normalized() * 0.5)
    FL.bar(K, P(-w / 2 - 0.2, -h / 2 - 0.15, 0.09), P(w / 2 + 0.2, -h / 2 - 0.15, 0.09), 0.16, 'course', h=0.07)  # the sill


def build(kind):
    global K
    K = Kit(os.path.join(HERE, 'boxes', kind + '.json'), seed=3)
    K.ground = 0.0
    for b in K.boxes: b['_done'] = True
    # ---- the plinth: flared stone; the tower: bands, string courses, a cornice, its top
    P0, P1, P2 = octo(X0, Z0, X1, Z1, 1.62, 0.0, 0.55), octo(X0, Z0, X1, Z1, 1.62, 0.9, 0.2), octo(X0, Z0, X1, Z1, 1.62, 1.2, 0.2)
    band(P0, P1, 'plinth'); band(P1, P2, 'plinth'); cap(P2, 'plinth')
    ys = [1.2, 4.5, 9.0, 13.5, TOP - 0.3]
    for k in range(4): band(ring(ys[k]), ring(ys[k + 1]), 'lhred' if k % 2 else 'lhwhite', sub=1.2)
    for y in (4.5, 9.0, 13.5):  # string courses: proud rings where the colours change
        band(ring(y - 0.09, 0.11), ring(y + 0.09, 0.11), 'course', sub=None); cap(ring(y + 0.09, 0.11), 'course'); cap(ring(y - 0.09, 0.11), 'course', up=False)
    top = TOP - (0.02 if kind == 'lighthouse' else 0.0)
    band(ring(TOP - 0.3, 0.2), ring(top, 0.2), 'course', sub=None); cap(ring(TOP - 0.3, 0.2), 'course', up=False)
    if kind == 'lighthouse_sd': cap(ring(TOP + 0.005, 0.2), 'tread')
    else: cap(ring(18.005, 0.0), 'tread')  # (level with the gallery's floor round it)
    # windows climbing round with the stair, the door at the foot of the north face (face 0: z = Z0)
    for (face, y) in ((1, 2.8), (2, 5.4), (3, 7.8), (4, 10.4), (5, 12.0), (6, 14.6), (7, 11.2), (0, 15.4), (2, 15.8), (4, 3.2), (6, 6.6)):
        window(face, y)
    face_out([Vector((81.3, 1.2, Z0 - 0.06)), Vector((82.7, 1.2, Z0 - 0.06)), Vector((82.7, 3.4, Z0 - 0.06)), Vector((81.3, 3.4, Z0 - 0.06))], 'door')
    for (a, b, y0, y1) in ((81.1, 81.3, 1.2, 3.4), (82.7, 82.9, 1.2, 3.4), (81.1, 82.9, 3.4, 3.6)): FL.obox(K, (a, y0, Z0 - 0.2), (b, y1, Z0 - 0.031), 'frame')
    FL.tube(K, (82.5, 2.3, Z0 - 0.06), (82.5, 2.3, Z0 - 0.15), 0.05, 0.05, 'brass', n=6)
    FL.obox(K, (80.9, 0.0, Z0 - 1.5), (83.1, 0.4, Z0 - 0.9), 'plinth'); FL.obox(K, (80.92, 0.0, Z0 - 0.9), (83.08, 0.8, Z0 - 0.5), 'plinth')  # two stone steps up to it

    # ---- the lantern room: a low wall, glowing panes behind diamond glazing bars, mullions; the dome; the vent ball
    LC = 1.172
    band(octo(80, -8, 84, -4, LC, TOP, 0.04), octo(80, -8, 84, -4, LC, TOP + 0.84, 0.04), 'lhwhite')
    band(octo(80, -8, 84, -4, LC, TOP + 0.84, 0.12), octo(80, -8, 84, -4, LC, TOP + 0.9, 0.12), 'iron', sub=None)
    cap(octo(80, -8, 84, -4, LC, TOP + 0.84, 0.12), 'iron', up=False)
    G0, G1 = octo(80, -8, 84, -4, LC, TOP + 0.9, 0.0), octo(80, -8, 84, -4, LC, 20.86, 0.0)
    band(G0, G1, 'lamp', sub=None)
    for i in range(8):
        a0, a1, b0, b1 = G0[i], G0[(i + 1) % 8], G1[i], G1[(i + 1) % 8]
        a0, a1, b0, b1 = a0 + Vector((0, 0.02, 0)), a1 + Vector((0, 0.02, 0)), b0 - Vector((0, 0.02, 0)), b1 - Vector((0, 0.02, 0))  # (their ends tucked into the ledge and the head)
        out = Vector(((a0.x + a1.x) / 2 - CX, 0, (a0.z + a1.z) / 2 - CZ)).normalized() * 0.04
        FL.bar(K, a0 + out, b0 + out, 0.1, 'iron')  # the mullion at each corner
        for k in range(3):  # the diamond lattice: bars up across each pane both ways
            t0, t1 = k / 3, (k + 1) / 3
            FL.bar(K, a0.lerp(a1, t0) + out, b0.lerp(b1, t1) + out, 0.03, 'iron')
            FL.bar(K, a0.lerp(a1, t1) + out * 1.4, b0.lerp(b1, t0) + out * 1.4, 0.03, 'iron')
    band(octo(80, -8, 84, -4, LC, 20.86, 0.1), octo(80, -8, 84, -4, LC, 21.0, 0.1), 'iron', sub=None)
    cap(octo(80, -8, 84, -4, LC, 20.86, 0.1), 'iron', up=False)
    # the dome: from a rim over the roof's boxes up in a curve to a small cap
    prev = None
    for k in range(8):
        t = k / 7; y = 21.0 + 1.22 * math.sin(t * math.pi / 2); h = 2.44 * (1 - t ** 1.8) + 0.3 * t ** 1.8
        Rg = octo(CX - h, CZ - h, CX + h, CZ + h, h * 0.586, y)
        if prev: band(prev, Rg, 'roof', sub=None)
        else: cap(Rg, 'roof', up=False)
        prev = Rg
    cap(prev, 'roof')
    FL.tube(K, (CX, 22.2, CZ), (CX, 22.3, CZ), 0.14, 0.14, 'iron', n=8)
    vb = [[Vector((CX + 0.3 * math.cos(la) * math.cos(lo), 22.56 + 0.3 * math.sin(la), CZ + 0.3 * math.cos(la) * math.sin(lo))) for lo in [2 * math.pi * i / 10 for i in range(10)]] for la in [-math.pi / 2 + math.pi * j / 6 for j in range(7)]]
    for j in range(6):
        for i in range(10):
            a, b, c, d = vb[j][i], vb[j][(i + 1) % 10], vb[j + 1][(i + 1) % 10], vb[j + 1][i]
            vc = Vector((CX, 22.56, CZ))
            if j == 0: face_out([a, c, d], 'iron', centre=vc)
            elif j == 5: face_out([a, b, d], 'iron', centre=vc)
            else: face_out([a, b, c, d], 'iron', centre=vc)
    FL.tube(K, (CX, 22.84, CZ), (CX, 24.3, CZ), 0.04, 0.0, 'brass', n=6)

    if kind == 'lighthouse':
        # ---- the stair: each step is solid iron to the flight's foot (as its box is), a chequer tread on top; its rails
        rails, steps = [], []
        for b in K.boxes:
            (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
            if b['mat'] != 'metal' or y0 >= 17.55: continue
            if abs(y1 - y0 - 1.0) < 0.06 and min(x1 - x0, z1 - z0) <= 0.11: rails.append(b)
            else: steps.append(b)
        for b in steps: K.box(b['min'], b['max'], {'top': 'tread', 'px': 'iron', 'nx': 'iron', 'pz': 'iron', 'nz': 'iron', 'bottom': 'iron'}, cull=True)
        def mid(b): return Vector(((b['min'][0] + b['max'][0]) / 2, b['min'][1], (b['min'][2] + b['max'][2]) / 2))
        for b in rails:
            p = mid(b); FL.obox(K, (p.x - 0.03, p.y, p.z - 0.03), (p.x + 0.03, p.y + 1.0, p.z + 0.03), 'iron')
        srt = sorted(rails, key=lambda b: b['min'][1])
        for a, b in zip(srt, srt[1:]):
            pa, pb = mid(a), mid(b)
            if (pa - pb).length < 1.0: FL.bar(K, pa + Vector((0, 1.0, 0)), pb + Vector((0, 1.0, 0)), 0.06, 'iron')
        # ---- the gallery: an octagonal chequer floor round the top (open over the stair), its edge, its brackets
        GO = [(p.x, p.z) for p in octo(76, -12, 88, 0, 3.515, 0)]
        tower = [(p.x, p.z) for p in octo(X0, Z0, X1, Z1, taper(TOP), 0)]
        hole = [(77.5, -9.0), (79.0, -9.0), (79.0, -3.0), (77.5, -3.0)]
        poly_fill(GO, [tower, hole], 18.005, 'tread'); poly_fill(GO, [tower, hole], 17.6, 'iron', up=False)
        band(octo(76, -12, 88, 0, 3.515, 17.6), octo(76, -12, 88, 0, 3.515, 18.005), 'iron', sub=None)
        q = [Vector((77.5, 17.6, -9.0)), Vector((77.5, 17.6, -3.0)), Vector((77.5, 18.0, -3.0)), Vector((77.5, 18.0, -9.0))]  # the stair hole's edges
        K.quad(q if (q[1] - q[0]).cross(q[3] - q[0]).x > 0 else q[::-1], 'iron')
        for (z, s) in ((-9.0, 1), (-3.0, -1)):
            q = [Vector((77.5, 17.6, z)), Vector((79.0, 17.6, z)), Vector((79.0, 18.0, z)), Vector((77.5, 18.0, z))]
            K.quad(q if (q[1] - q[0]).cross(q[3] - q[0]).z * s > 0 else q[::-1], 'iron')
        TR = ring(15.0, 0.0)
        for i in range(8):  # brackets: a long strut from each tower corner and face out to under the gallery's edge
            for t in (0.0, 0.5):
                a = TR[i].lerp(TR[(i + 1) % 8], t)
                if a.x < X0 + 0.3: continue  # (the west face: the stair's last flight runs up it)
                d = Vector((a.x - CX, 0, a.z - CZ)).normalized(); e = a + d * 2.6; e.y = 17.58
                FL.bar(K, a, e, 0.12, 'iron'); FL.bar(K, Vector((a.x, 17.48, a.z)), Vector((e.x, 17.48, e.z)), 0.1, 'iron')
        # the railing: balusters all round (where the corners' close-set posts are), top and middle rails, a kick plate
        GP = octo(76, -12, 88, 0, 3.515, 18.0, -0.09)
        for i in range(8):
            a, b = GP[i], GP[(i + 1) % 8]; n = max(1, round((b - a).length / 0.32))
            for k in range(n): p = a.lerp(b, k / n); FL.bar(K, p + Vector((0, 0.13, 0)), p + Vector((0, 0.97, 0)), 0.04, 'iron')
            FL.bar(K, a + Vector((0, 1.0, 0)), b + Vector((0, 1.0, 0)), 0.08, 'iron', h=0.05)
            FL.bar(K, a + Vector((0, 0.5, 0)), b + Vector((0, 0.5, 0)), 0.035, 'iron')
            FL.bar(K, a + Vector((0, 0.07, 0)), b + Vector((0, 0.07, 0)), 0.025, 'iron', h=0.13)
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in ('lighthouse', 'lighthouse_sd')] or ['lighthouse', 'lighthouse_sd']):
    build(kind)
