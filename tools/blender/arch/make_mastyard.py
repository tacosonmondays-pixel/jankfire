# Scary Forest's radio mast and its fenced yard, bomb site B (shared/map.js forest(), "the radio mast yard"): drawn over
# its own boxes (tools/arch/dump.mjs), which stay what you bump into. The game keeps drawing the red lights (they
# blink: public/js/forest.js), the radio's picture and the gravel; the guy wires stay its lines (forest.js wires()).
#   - the mast: a guyed lattice tower like a big Rohn: tubular legs with flanged joints every 6 m, zig-zag lacing up all
#     four faces, the game's rungs as its horizontals; painted aviation orange and white in seven bands (orange top and
#     bottom, FAA style); a guy ring at 24 and 44 m with lugs and grips where the wires start; obstruction lights in
#     guarded housings on brackets (the game's red cubes are their lenses), a beacon on the top pole with a lightning
#     rod; a caged ladder up the north face; cellular panels on pipe mounts, a microwave dish, three FM bays (K-JANK);
#     the coax run up the west face; a grated top platform; on a concrete pier with base plates, a copper ground ring.
#   - the guy anchors 22 m out (where wires() ends): concrete deadmen, anchor rods, an equaliser plate, turnbuckles,
#     yellow guy guards.
#   - the yard: a galvanised chain-link fence (cutout fabric, top rail, tension wire, barbed wire on arms, gates swung
#     back against it, one hanging off a hinge, signs), a ribbed steel equipment shelter (double doors swung back, a
#     drip hood and a lamp, a wall-pack A/C, the cable port and the ice bridge to the mast, a ground bar, the meter),
#     inside: the console under the radio's picture, a chair, a cable tray; a towable yellow genset on its trailer with
#     its cable to the shelter; two wooden cable reels.
# Everything is chunky low poly with chamfered edges; the paint, zinc, chrome and plastic carry a shine (archfield.js
# `shine`) so flashlights and the moon glint off them. local frame = the map's.
# run: node tools/arch/dump.mjs forest mastyard tools/blender/arch/boxes/mastyard.json
#      (its own kit textures: texkit.py chainlink(), galv(), barbwire(), mastsigns(), on their own seeds; the shelter is
#      clad in the kit's `profile`)
#      blender52 -b --python tools/blender/arch/make_mastyard.py
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import flair as FL
import archkit as AK
from archkit import Kit, OUTDIR, MATS, NOCAST, KIT
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({  # (19 materials = 19 draw calls for the lot)
    'mastorange': ('trim', '#ff5a1c', {}), 'mastwhite2': ('trim', '#f4f2ec', {}), 'mastgalv': ('galv', '#c6ced4', {}), 'mastgalvdk': ('galv', '#7c858c', {}),
    'mastchain': ('chainlink', '#d6dce0', {'alpha': True}), 'mastbarb': ('barbwire', '#c8ced2', {'alpha': True}), 'mastconc': ('concrete', '#c9c5bd', {}),
    'mastshell': ('profile', '#d8d3bf', {}), 'mastint': ('stucco', '#e6eae6', {}), 'mastdoor': ('trim', '#2f7ad8', {}), 'mastlouvre': ('louvre', '#b8b4a2', {}),
    'mastgen': ('trim', '#ffc414', {}), 'mastblack': ('trim', '#2c2e34', {}), 'mastwood': ('planks', '#d29c6a', {}), 'mastcopper': ('trim', '#d8803e', {}),
    'mastradome': ('trim', '#ecebe4', {}), 'mastsign': ('mastsigns', '#ffffff', {'alpha': True}), 'mastlamp': ('stucco', '#ffe2a0', {'glow': True, 'glowcol': '#ffd080'}),
})
NOCAST.update({'mastgalvdk', 'mastchain', 'mastbarb', 'mastcopper', 'mastsign', 'mastlamp', 'mastlouvre'})
# the shine (archfield.js: Phong instead of Lambert): (shininess, specular level)
GLOSS = {'mastorange': (40, 0.32), 'mastwhite2': (40, 0.3), 'mastgalv': (60, 0.5), 'mastgalvdk': (40, 0.3), 'mastchain': (60, 0.5), 'mastbarb': (60, 0.5),
         'mastshell': (24, 0.16), 'mastdoor': (45, 0.4), 'mastgen': (50, 0.42), 'mastblack': (40, 0.3), 'mastcopper': (70, 0.6), 'mastradome': (40, 0.3)}
NOMIP = {'mastchain', 'mastbarb'}  # (see-through wire: no mipmaps, or it melts into a sheet / vanishes far off)

CX, CZ = 56.0, 8.0                        # the mast's middle (forest.js wires(): top = [56, 8])
LEGS = [(55.0, 7.0), (57.0, 7.0), (57.0, 9.0), (55.0, 9.0)]  # SW, SE, NE, NW (z = 7 is "south" here)
TOP = 48.0                                # the platform
BANDS = [0.0, 6.5, 13.5, 20.5, 27.5, 34.5, 41.5, 48.0]  # seven bands, orange top and bottom; the edges fall between lacing nodes
GUY_Y = (24.0, 44.0)
ANCH = [(CX + math.cos(0.6 + i / 3 * math.tau) * 22, CZ + math.sin(0.6 + i / 3 * math.tau) * 22, 0.6 + i / 3 * math.tau) for i in range(3)]
V = Vector


def paint(y): return 'mastorange' if sum(1 for b in BANDS[1:-1] if y >= b) % 2 == 0 else 'mastwhite2'


# ------------------------------------------------------------ shapes (all quads / tris into the kit's buckets)
def face_out(q, mat, centre, uv=None):
    """a quad (or tri) wound to face away from centre"""
    q = [V(p) for p in q]
    cen = sum(q, V()) / len(q); n = (q[1] - q[0]).cross(q[-1] - q[0])
    if n.dot(cen - V(centre)) < 0: q = q[::-1]; uv = uv[::-1] if uv else None
    if len(q) == 3: K.tri(q, mat)
    else: K.quad(q, mat, uv=uv)


def plate(q, mat, depth, uv=None):
    """a flat overlay (a label, a grille, a seam) a few mm proud of a surface, with its edges run back to it so it sits
    on it (no gap for the light to show, nothing floating)"""
    q = [V(p) for p in q]; n = (q[1] - q[0]).cross(q[3] - q[0]).normalized(); c = sum(q, V()) / 4 - n * depth / 2
    K.quad(q, mat, uv=uv)
    uc = (sum(u[0] for u in uv) / 4, sum(u[1] for u in uv) / 4) if uv else None
    inn = (lambda u: (u[0] + (uc[0] - u[0]) * 0.04, u[1] + (uc[1] - u[1]) * 0.04)) if uv else None  # (the edges' uvs: a sliver of the border, not zero)
    for i in range(4):
        j = (i + 1) % 4
        face_out([q[i], q[j], q[j] - n * depth, q[i] - n * depth], mat, c, uv=[uv[i], uv[j], inn(uv[j]), inn(uv[i])] if uv else None)


def frame(d):
    """two unit vectors across direction d"""
    d = V(d).normalized(); up = V((0, 1, 0)) if abs(d.y) < 0.9 else V((1, 0, 0))
    u = d.cross(up).normalized(); return u, u.cross(d).normalized()


def prism(a, b, prof, mat, side=None, caps=(False, False), closed=True):
    """a convex profile [(x, y)] swept straight from a to b. side: the profile's x direction. closed=False: no face
    from the last point back to the first (a rib standing on a wall)"""
    a, b = V(a), V(b); d = (b - a).normalized()
    if side is None: side, upv = frame(d)
    else: side = V(side).normalized(); upv = side.cross(d).normalized()
    A = [a + side * x + upv * y for x, y in prof]; Bq = [b + side * x + upv * y for x, y in prof]
    n = len(prof); pc = sum(A, V()) / n
    for i in range(n if closed else n - 1):
        j = (i + 1) % n; fc = (A[i] + A[j] + Bq[i] + Bq[j]) / 4
        face_out([A[i], A[j], Bq[j], Bq[i]], mat, pc + d * (fc - pc).dot(d))
    ca = sum(A, V()) / n; cb = sum(Bq, V()) / n
    if caps[0]:
        for i in range(1, n - 1): face_out([A[0], A[i], A[i + 1]], mat, ca + d)
    if caps[1]:
        for i in range(1, n - 1): face_out([Bq[0], Bq[i], Bq[i + 1]], mat, cb - d)


def rod(a, b, r, mat, n=6, caps=(False, False)):
    prism(a, b, [(math.cos(k * math.tau / n) * r, math.sin(k * math.tau / n) * r) for k in range(n)], mat, caps=caps)


def flat(a, b, w, t, mat, side):
    """a flat bar from a to b, w wide (along side), t thick, no end caps"""
    prism(a, b, [(-w / 2, -t / 2), (w / 2, -t / 2), (w / 2, t / 2), (-w / 2, t / 2)], mat, side=side)


def cyl(c, axis, r, h, mat, n=12, caps=(True, True), r1=None):
    """a cylinder (or cone, r1) from c along axis h long"""
    c = V(c); ax = V(axis).normalized()
    FL.tube(K, c, c + ax * h, r, r if r1 is None else r1, mat, n=n, caps=caps)


def poly(pts, r, mat, n=5):
    """a bent rod / cable through the points"""
    for p, q in zip(pts, pts[1:]): rod(p, q, r, mat, n=n)


def cbox(mn, mx, mat, c=0.03, mats=None, skip=()):
    """a box with every edge chamfered c (the house's bevelled look). mats: per face ('px', 'nx', 'py', 'ny', 'pz', 'nz')"""
    mn, mx = V(mn), V(mx); cen = (mn + mx) / 2; h = (mx - mn) / 2
    c = min(c, h.x * 0.45, h.y * 0.45, h.z * 0.45)
    get = lambda f: (mats or {}).get(f, mat)
    def P(sx, sy, sz, ex, ey, ez):  # a corner (signs), pulled in c along the axes flagged e
        return V((cen.x + sx * (h.x - ex * c), cen.y + sy * (h.y - ey * c), cen.z + sz * (h.z - ez * c)))
    for ax in range(3):  # the six faces
        for s in (-1, 1):
            f = ('nx', 'px', 'ny', 'py', 'nz', 'pz')[ax * 2 + (s > 0)]
            if f in skip: continue
            o = [i for i in range(3) if i != ax]; q = []
            for (u, v) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                sg = [0, 0, 0]; e = [0, 0, 0]; sg[ax] = s; sg[o[0]] = u; sg[o[1]] = v; e[o[0]] = e[o[1]] = 1
                q.append(P(*sg, *e))
            face_out(q, get(f), cen)
    for ax in range(3):  # the twelve edges (along axis ax)
        o = [i for i in range(3) if i != ax]
        for s0 in (-1, 1):
            for s1 in (-1, 1):
                q = []
                for t in (-1, 1):
                    for (e0, e1) in ((1, 0), (0, 1)) if t < 0 else ((0, 1), (1, 0)):
                        sg = [0, 0, 0]; e = [0, 0, 0]; sg[ax] = t; e[ax] = 1; sg[o[0]] = s0; sg[o[1]] = s1; e[o[0]] = e0; e[o[1]] = e1
                        q.append(P(*sg, *e))
                f = ('nx', 'px', 'ny', 'py', 'nz', 'pz')[o[1] * 2 + (s1 > 0)]
                face_out(q, get(f), cen)
    for sx in (-1, 1):  # the eight corners
        for sy in (-1, 1):
            for sz in (-1, 1):
                face_out([P(sx, sy, sz, 1, 1, 0), P(sx, sy, sz, 1, 0, 1), P(sx, sy, sz, 0, 1, 1)], get('py' if sy > 0 else 'ny'), cen)


def box(mn, mx, mat, skip=()):
    """a plain box (small hardware: a chamfer there is lost at any distance and costs 32 tris)"""
    K.box(mn, mx, dict({'all': mat}, **{f: None for f in skip}), cull=False)


def ring(c, axis, R, r, mat, seg=12, n=4, a0=0.0, a1=math.tau):
    """a hoop of rod round c in the plane across axis"""
    u, v = frame(axis); c = V(c)
    pts = [c + (u * math.cos(a0 + (a1 - a0) * k / seg) + v * math.sin(a0 + (a1 - a0) * k / seg)) * R for k in range(seg + 1)]
    poly(pts, r, mat, n=n)


def sign(cell, c, normal, w, h, along=None, ties=0.0):
    """a sign plate (a cell of the mastsigns atlas) on a thin galvanised backing, facing normal. ties: wired back
    that far to what it hangs on (the fence's fabric)"""
    nrm = V(normal).normalized(); c = V(c)
    side = V(along).normalized() if along else V((0, 1, 0)).cross(nrm).normalized()
    up = nrm.cross(side).normalized()
    u0, v0, du, dv = KIT['mastsigns']['cells'][cell]; v0 = 1 - v0 - dv
    q = [c + nrm * 0.008 - side * w / 2 - up * h / 2, c + nrm * 0.008 + side * w / 2 - up * h / 2, c + nrm * 0.008 + side * w / 2 + up * h / 2, c + nrm * 0.008 - side * w / 2 + up * h / 2]
    face_out(q, 'mastsign', c - nrm, uv=[(u0, v0), (u0 + du, v0), (u0 + du, v0 + dv), (u0, v0 + dv)])
    prism(c - nrm * 0.004, c + nrm * 0.008, [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], 'mastgalv', side=side, caps=(True, False))  # (its edges, the plate's face is the sign)
    for sx in ((-1, 1) if ties else ()):
        t0 = c - nrm * 0.004 + side * sx * (w / 2 - 0.04) + up * (h / 2 - 0.03); rod(t0, t0 - nrm * ties, 0.006, 'mastgalvdk', n=3)


def decal(cell, c, normal, w, h, along=None):
    """a cell of the kit's decal atlas, a hair off a surface"""
    nrm = V(normal).normalized(); c = V(c) + nrm * 0.006
    side = V(along).normalized() if along else V((0, 1, 0)).cross(nrm).normalized()
    up = nrm.cross(side).normalized()
    u0, v0, du, dv = KIT['decals']['cells'][cell]; v0 = 1 - v0 - dv
    q = [c - side * w / 2 - up * h / 2, c + side * w / 2 - up * h / 2, c + side * w / 2 + up * h / 2, c - side * w / 2 + up * h / 2]
    if (q[1] - q[0]).cross(q[3] - q[0]).dot(nrm) < 0: q = [q[1], q[0], q[3], q[2]]; uv = [(u0 + du, v0), (u0, v0), (u0, v0 + dv), (u0 + du, v0 + dv)]
    else: uv = [(u0, v0), (u0 + du, v0), (u0 + du, v0 + dv), (u0, v0 + dv)]
    plate(q, 'decal', 0.006, uv=uv)


# ------------------------------------------------------------ the mast
def mast():
    # the pier: a concrete block with a chamfered top, base plates and anchor bolts under each leg
    cbox((54.4, 0.0, 6.4), (57.6, 0.35, 9.6), 'mastconc', c=0.05, skip=('ny',))
    for (x, z) in LEGS:
        box((x - 0.19, 0.35, z - 0.19), (x + 0.19, 0.38, z + 0.19), 'mastgalv', skip=('ny',))
        for (dx, dz) in ((-0.13, -0.13), (0.13, -0.13), (0.13, 0.13), (-0.13, 0.13)):
            cyl((x + dx, 0.38, z + dz), (0, 1, 0), 0.026, 0.035, 'mastgalvdk', n=3, caps=(False, True))
        # the leg: a tube in the band colours, flanged every 6 m
        for k in range(len(BANDS) - 1):
            y0, y1 = max(0.38, BANDS[k]), BANDS[k + 1]
            cyl((x, y0, z), (0, 1, 0), 0.095, y1 - y0, paint(y0 + 0.1), n=10, caps=(False, k == len(BANDS) - 2))
        for y in range(6, 48, 6):
            cyl((x, y - 0.035, z), (0, 1, 0), 0.155, 0.07, paint(y), n=6)
    # the horizontals: the game's rungs, as chamfered bars (they're what you climb on)
    for b in K.boxes:
        if b['mat'] != 'metal' or not (1.0 < b['min'][1] < TOP) or not (54.8 < b['min'][0] < 57.2): continue
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        along_x = (x1 - x0) > (z1 - z0); w = (z1 - z0) if along_x else (x1 - x0); h = y1 - y0; c = 0.022
        prof = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2 - c), (w / 2 - c, h / 2), (-w / 2 + c, h / 2), (-w / 2, h / 2 - c)] if y0 < 12 else \
            [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]  # (chamfered where you see them close)
        cy, cz_, cx_ = (y0 + y1) / 2, (z0 + z1) / 2, (x0 + x1) / 2
        if along_x: prism((x0, cy, cz_), (x1, cy, cz_), prof, paint(y0), side=(0, 0, 1))
        else: prism((cx_, cy, z0), (cx_, cy, z1), prof, paint(y0), side=(-1, 0, 0))
    # zig-zag lacing up every face: node every metre, alternating legs, spiralling round so the legs' nodes interleave
    faces = [((55.0, 7.0), (57.0, 7.0)), ((57.0, 7.0), (57.0, 9.0)), ((57.0, 9.0), (55.0, 9.0)), ((55.0, 9.0), (55.0, 7.0))]
    for fi, (pa, pb) in enumerate(faces):
        # S face: its first leg (SW) has nodes at 1.5, 3.5...; the next face on that leg (W) at 2.5, 4.5...
        for k in range(47):
            y = 0.5 + k
            first = (k % 2 == 1)  # node at the face's first leg at 1.5, 3.5, ...
            p, q = (pa, pb) if first else (pb, pa)
            rod((p[0], y, p[1]), (q[0], y + 1, q[1]), 0.026, paint(y + 0.5), n=3)
    # guy rings at 24 and 44: a ring of tube round the middle, struts to the legs, a lug and a grip where each wire starts
    for gy in GUY_Y:
        ring((CX, gy, CZ), (0, 1, 0), 1.0, 0.035, paint(gy), seg=12, n=3)
        for (x, z) in LEGS:
            d = V((x - CX, 0, z - CZ)).normalized()
            rod(V((CX, gy, CZ)) + d * 0.98, (x, gy, z), 0.04, paint(gy), n=3)
        for (ax_, az_, a) in ANCH:
            for s in (-1, 1):
                p = V((CX + s * math.sin(a), gy, CZ - s * math.cos(a)))
                to = V((ax_, 0.3, az_)) - p; to.normalize()
                outw = V((math.cos(a), 0, math.sin(a)))
                rod(p + V((0, 0.03, 0)), p - V((0, 0.08, 0)), 0.03, 'mastgalv', n=3)  # the lug
                rod(p, p + to * 0.12, 0.02, 'mastgalvdk', n=3)  # the shackle
                rod(p + to * 0.12, p + to * 0.95, 0.014, 'mastblack', n=3)  # the preformed grip
    # the platform: a grated deck on a channel frame, knee braces under it, the low pipe-mount rails (the game's bars)
    cbox((54.6, TOP, 6.6), (57.4, TOP + 0.2, 9.4), 'mastgalv', c=0.025, mats={'ny': 'mastgalvdk'})
    for (x, z) in LEGS:
        cx_, cz_ = (54.66 if x < CX else 57.34), (6.66 if z < CZ else 9.34)
        rod((x, TOP - 1.3, z), (cx_, TOP - 0.01, cz_), 0.04, 'mastgalv', n=4)
        rod((x, TOP - 0.02, z), (cx_, TOP - 0.02, cz_), 0.035, 'mastgalvdk', n=4)
    for b in K.boxes:
        if b['mat'] == 'metal' and b['min'][1] > TOP + 0.3 and b['max'][1] < TOP + 0.7:  # (at 48.5: two bars across the deck)
            (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']; x = (x0 + x1) / 2
            prism((x, (y0 + y1) / 2, z0), (x, (y0 + y1) / 2, z1), [(-0.08, -0.04), (0.08, -0.04), (0.08, 0.02), (0.06, 0.04), (-0.06, 0.04), (-0.08, 0.02)], 'mastgalv', side=(-1, 0, 0), caps=(True, True))
            for z in (z0 + 0.2, z1 - 0.2): rod((x, TOP + 0.2, z), (x, y0 + 0.005, z), 0.03, 'mastgalvdk', n=6)
    # kick plate round the deck's edge
    for (a, b2) in (((54.6, 6.6), (57.4, 6.6)), ((57.4, 6.6), (57.4, 9.4)), ((57.4, 9.4), (54.6, 9.4)), ((54.6, 9.4), (54.6, 6.6))):
        d = V((b2[0] - a[0], 0, b2[1] - a[1])).normalized(); n = V((d.z, 0, -d.x))
        flat(V((a[0], TOP + 0.26, a[1])) - n * 0.008, V((b2[0], TOP + 0.26, b2[1])) - n * 0.008, 0.12, 0.012, 'mastorange', side=(0, 1, 0))
    # the top pole and its beacon (the game's red cube is the lens): a base, guard bars, a hood, the lightning rod
    cyl((CX, TOP + 0.2, CZ), (0, 1, 0), 0.1, 2.3, 'mastgalv', n=10, caps=(False, False))
    cyl((CX, 50.43, CZ), (0, 1, 0), 0.32, 0.12, 'mastblack', n=12, r1=0.3)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        rod((CX + math.cos(a) * 0.37, 50.53, CZ + math.sin(a) * 0.37), (CX + math.cos(a) * 0.37, 51.08, CZ + math.sin(a) * 0.37), 0.016, 'mastblack', n=4)
    cyl((CX, 51.06, CZ), (0, 1, 0), 0.39, 0.07, 'mastblack', n=12, caps=(True, False))
    cyl((CX, 51.13, CZ), (0, 1, 0), 0.39, 0.1, 'mastblack', n=12, r1=0.1, caps=(False, True))
    cyl((CX, 51.23, CZ), (0, 1, 0), 0.025, 1.5, 'mastcopper', n=4, r1=0.006, caps=(False, False))
    # the side lights (L-810s round the game's cubes): a cup under, guard bars, a hood, on a bracket across the face
    for (lx, y) in ((54.8, 16.0), (57.2, 16.0), (54.8, 32.0), (57.2, 32.0)):
        fx = 55.0 if lx < CX else 57.0
        cyl((lx, y - 0.22, CZ), (0, 1, 0), 0.13, 0.07, 'mastblack', n=6, r1=0.17)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            rod((lx + math.cos(a) * 0.235, y - 0.15, CZ + math.sin(a) * 0.235), (lx + math.cos(a) * 0.235, y + 0.17, CZ + math.sin(a) * 0.235), 0.011, 'mastblack', n=3)
        cyl((lx, y + 0.152, CZ), (0, 1, 0), 0.25, 0.04, 'mastblack', n=6, r1=0.2)
        rod((lx, y - 0.25, CZ), (fx, y - 0.25, CZ), 0.03, 'mastgalv', n=4)
        rod((fx, y - 0.25, 7.0), (fx, y - 0.25, 9.0), 0.032, 'mastgalv', n=4)
    # conduit for the lights: down the NW leg (beacon + west lights) and the NE leg (east lights) to a box on the pier
    rod((55.12, 0.4, 9.12), (55.12, TOP, 9.12), 0.018, 'mastblack', n=4)
    rod((55.12, TOP, 9.12), (CX + 0.11, TOP + 0.2, CZ + 0.11), 0.018, 'mastblack', n=4)
    rod((CX + 0.11, TOP + 0.2, CZ + 0.11), (CX + 0.11, 50.43, CZ + 0.11), 0.018, 'mastblack', n=4)
    rod((56.88, 0.4, 9.12), (56.88, 32.0, 9.12), 0.018, 'mastblack', n=4)
    cbox((55.25, 0.35, 9.2), (55.65, 0.7, 9.45), 'mastgalvdk', c=0.02, skip=('ny',))
    # cellular panels on pipe mounts below the deck (S, E, N faces), each with its radio box and a jumper
    for (nrm, cen) in (((0, -1), (CX, 7.0)), ((1, 0), (57.0, CZ)), ((0, 1), (CX, 9.0))):
        n = V((nrm[0], 0, nrm[1])); t = V((-nrm[1], 0, nrm[0]))
        for s in (-0.62, 0.62):
            base = V((cen[0], 0, cen[1])) + n * 0.85 + t * s
            cbox(base + V((0, 45.9, 0)) - t * 0.16 - n * 0.06, base + V((0, 47.7, 0)) + t * 0.16 + n * 0.06, 'mastradome', c=0.035)
            pipe = base - n * 0.2
            rod(pipe + V((0, 45.6, 0)), pipe + V((0, 47.98, 0)), 0.035, 'mastgalv', n=4)
            for y in (46.2, 47.4): rod(pipe + V((0, y, 0)), base + V((0, y, 0)) - n * 0.06, 0.025, 'mastgalvdk', n=4)
            leg = min(LEGS, key=lambda L: (L[0] - pipe.x) ** 2 + (L[1] - pipe.z) ** 2)
            rod(pipe + V((0, 46.8, 0)), (leg[0], 46.8, leg[1]), 0.03, 'mastgalv', n=4)
            rr = pipe - n * 0.1
            p0, p1 = rr + V((0, 46.5, 0)) - t * 0.13 - n * 0.07, rr + V((0, 46.95, 0)) + t * 0.13 + n * 0.07
            box([min(p0[i], p1[i]) for i in range(3)], [max(p0[i], p1[i]) for i in range(3)], 'mastblack')
            poly([base + V((0, 45.9, 0)), base + V((0, 45.75, 0)) - n * 0.2, rr + V((0, 46.5, 0))], 0.014, 'mastblack', n=4)
    # the microwave dish on the west face, aimed at the clearing-ish: a drum with a radome, on two arms to the legs
    dc = V((54.2, 40.5, CZ))
    cyl(dc + V((0.32, 0, 0)), (-1, 0, 0), 0.5, 0.32, 'mastgalv', n=16, caps=(True, False))
    cyl(dc, (-1, 0, 0), 0.5, 0.06, 'mastradome', n=16, r1=0.42, caps=(False, True))
    for z in (7.0, 9.0):
        rod(dc + V((0.32, 0.25, (z - CZ) * 0.35)), (55.0, 40.75, z), 0.03, 'mastgalvdk', n=4)
        rod(dc + V((0.32, -0.25, (z - CZ) * 0.35)), (55.0, 40.25, z), 0.03, 'mastgalvdk', n=4)
    # K-JANK's FM bays on the east face: ring dipoles on booms, a rigid feed line joining them
    for y in (35.5, 38.5, 41.5):
        rod((57.0, y, CZ), (57.73, y, CZ), 0.03, 'mastgalv', n=4)
        ring((58.05, y, CZ), (0.0, 0.6, 0.8), 0.32, 0.022, 'mastgalv', seg=8, n=3)
    rod((57.18, 35.0, CZ - 0.2), (57.18, 42.0, CZ - 0.2), 0.045, 'mastgalvdk', n=6)
    for y in (35.5, 38.5, 41.5): rod((57.18, y, CZ - 0.2), (57.5, y, CZ), 0.02, 'mastgalvdk', n=4)
    # the coax: up the inside of the west face from the ice bridge to the panels
    for k, dz in enumerate((-0.08, 0.0, 0.08)):
        rod((55.22, 2.83, 7.45 + dz), (55.22, 45.7, 7.45 + dz), 0.022, 'mastblack', n=4)
    # the caged ladder up the north face, out past the deck's edge: stiles, rungs, standoffs, hoops, straps
    LZ = 9.55; XL, XR = 55.72, 56.28
    for x in (XL, XR):
        flat((x, 0.35, LZ), (x, TOP + 1.1, LZ), 0.06, 0.014, 'mastgalv', side=(0, 0, 1))
    y = 0.65
    while y < TOP + 1.0:
        if abs(y - TOP - 0.1) > 0.12: rod((XL, y, LZ), (XR, y, LZ), 0.017, 'mastgalv', n=3)
        y += 0.34
    for y in range(3, 48, 6):
        for x in (XL, XR): rod((x, y, LZ - 0.01), (x, y, 9.08), 0.02, 'mastgalvdk', n=4)
    hz = LZ + 0.38
    def hoop(t):
        a = math.pi * t; return V((CX - math.cos(a) * 0.38, 0, hz + math.sin(a) * 0.38))
    hp = [V((XL, 0, LZ))] + [hoop(k / 4) for k in range(5)] + [V((XR, 0, LZ))]
    for y in [2.4 + k * 3.0 for k in range(16)]:
        if y > TOP - 0.35: break
        for p, q in zip(hp, hp[1:]): flat(p + V((0, y, 0)), q + V((0, y, 0)), 0.05, 0.01, 'mastgalv', side=(0, 1, 0))
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        p = hoop(t); p = V((CX + (p.x - CX) * 0.96, 0, hz + (p.z - hz) * 0.96))
        side = V((p.z - hz, 0, -(p.x - CX))).normalized()
        flat(p + V((0, 2.4, 0)), p + V((0, 47.4, 0)), 0.045, 0.01, 'mastgalv', side=side)
    # the ground ring: bare copper round the pier, a lead up to each leg's plate
    rp = [(54.0, 6.0), (58.0, 6.0), (58.0, 10.0), (54.0, 10.0), (54.0, 6.0)]
    for (a, b2) in zip(rp, rp[1:]): rod((a[0], 0.055, a[1]), (b2[0], 0.055, b2[1]), 0.012, 'mastcopper', n=4)
    for (x, z) in LEGS:
        ox, oz = (54.0 if x < CX else 58.0), (6.0 if z < CZ else 10.0)
        poly([V((ox, 0.055, oz)), V((x + (ox - x) * 0.55, 0.055, z + (oz - z) * 0.55)), V((x + (ox - x) * 0.4, 0.36, z + (oz - z) * 0.4)), V((x + (ox - x) * 0.17, 0.39, z + (oz - z) * 0.17))], 0.012, 'mastcopper', n=4)
        cyl((ox, 0.04, oz), (0, 1, 0), 0.03, 0.08, 'mastcopper', n=6, caps=(False, True))


# ------------------------------------------------------------ the guy anchors (where forest.js wires() ends them)
def anchors():
    for (ax_, az_, a) in ANCH:
        tow = V((CX - ax_, 0, CZ - az_)).normalized(); side = V((tow.z, 0, -tow.x)); P = V((ax_, 0.3, az_))
        g = -0.22 if ax_ > 72 else 0.0  # (the east one stands in the lake shore's mud)
        c = V((ax_, 0, az_)) - tow * 0.55
        # the deadman's top: a chamfered concrete block, its long side across the pull
        pts = [c + side * 0.75 + tow * 0.45, c - side * 0.75 + tow * 0.45, c - side * 0.75 - tow * 0.45, c + side * 0.75 - tow * 0.45]
        lo, hi = g - 0.15, 0.12
        for i in range(4):
            p, q = pts[i], pts[(i + 1) % 4]
            face_out([V((p.x, lo, p.z)), V((q.x, lo, q.z)), V((q.x, hi - 0.04, q.z)), V((p.x, hi - 0.04, p.z))], 'mastconc', V((c.x, 0, c.z)))
            pi, qi = p + (c - p).normalized() * 0.06, q + (c - q).normalized() * 0.06
            face_out([V((p.x, hi - 0.04, p.z)), V((q.x, hi - 0.04, q.z)), V((qi.x, hi, qi.z)), V((pi.x, hi, pi.z))], 'mastconc', V((c.x, -1, c.z)))
        ins = [p + (c - p).normalized() * 0.06 for p in pts]
        face_out([V((p.x, hi, p.z)) for p in ins], 'mastconc', V((c.x, -1, c.z)))
        # the anchor rod up out of it to the equaliser plate, a nut on its collar
        r0 = V((ax_, hi, az_)) - tow * 0.24
        rod(r0, P, 0.035, 'mastgalv', n=6)
        cyl(r0, (0, 1, 0), 0.07, 0.04, 'mastgalvdk', n=6, caps=(False, True))
        pl = [P - tow * 0.06 + V((0, -0.08, 0)), P + tow * 0.16 + V((0, -0.02, 0)), P + tow * 0.12 + V((0, 0.12, 0)), P - tow * 0.04 + V((0, 0.08, 0))]
        prism(P - side * 0.012, P + side * 0.012, [((p - P).dot(tow), p.y - P.y) for p in pl], 'mastgalv', side=tow, caps=(True, True))
        # each of its four wires: a shackle, a turnbuckle, a grip, the yellow guard
        for gy in GUY_Y:
            for s in (-1, 1):
                top = V((CX + s * math.sin(a), gy, CZ - s * math.cos(a))); d = (top - P).normalized()
                o = P + side * (0.03 * s + (0.014 if gy > 30 else -0.014)) + d * 0.04  # (each its own line: no two share a face)
                rod(o, o + d * 0.1, 0.016, 'mastgalvdk', n=3)
                rod(o + d * 0.1, o + d * 0.18, 0.009, 'mastgalv', n=3)
                rod(o + d * 0.18, o + d * 0.48, 0.022, 'mastgalv', n=4, caps=(True, True))
                rod(o + d * 0.48, o + d * 0.58, 0.009, 'mastgalv', n=3)
                rod(o + d * 0.58, P + d * 1.5, 0.012, 'mastblack', n=3)
                rod(P + d * 1.4, P + d * 3.8, 0.032, 'mastgen', n=5, caps=(True, True))


# ------------------------------------------------------------ the fence
def fence():
    posts, runs = [], []
    for b in K.boxes:
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        if b['mat'] == 'metal' and y0 == 0 and abs(y1 - 1.45) < 1e-3: posts.append(((x0 + x1) / 2, (z0 + z1) / 2))
        if b['mat'] == 'chainlink':
            if (x1 - x0) > (z1 - z0): runs.append(('x', (z0 + z1) / 2, x0, x1))
            else: runs.append(('z', (x0 + x1) / 2, z0, z1))
    merged = []  # (the corners have two posts side by side: one fat one)
    for p in posts:
        for m in merged:
            if math.hypot(m[0] - p[0], m[1] - p[1]) < 0.16: m[2].append(p); break
        else: merged.append([p[0], p[1], [p]])
    def outw(x, z):
        o = []
        if abs(x - 42) < 0.1: o.append(V((-1, 0, 0)))
        if abs(x - 62) < 0.1: o.append(V((1, 0, 0)))
        if abs(z + 5) < 0.1: o.append(V((0, 0, -1)))
        if abs(z - 13) < 0.1: o.append(V((0, 0, 1)))
        return o
    ends = set()
    for (ax, c, s0, s1) in runs:
        for s in (s0, s1): ends.add((round(s if ax == 'x' else c, 1), round(c if ax == 'x' else s, 1)))
    for m in merged:
        x = sum(p[0] for p in m[2]) / len(m[2]); z = sum(p[1] for p in m[2]) / len(m[2])
        term = len(m[2]) > 1 or any(math.hypot(x - e[0], z - e[1]) < 0.12 for e in ends)
        r = 0.072 if term else 0.055
        cyl((x, 0.0, z), (0, 1, 0), r, 1.38, 'mastgalv', n=6, caps=(False, False))
        if term:
            cyl((x, 1.38, z), (0, 1, 0), r + 0.012, 0.05, 'mastgalv', n=6, caps=(False, True), r1=r * 0.7)
            cyl((x, 0.0, z), (0, 1, 0), 0.14, 0.07, 'mastconc', n=6, caps=(False, True), r1=0.12)
        else: cyl((x, 1.38, z), (0, 1, 0), r, 0.06, 'mastgalv', n=6, caps=(False, True), r1=r * 0.6)
        for o in outw(x, z):  # the barbed wire arm, 45 degrees out over the outside
            rod((x, 1.36, z), V((x, 1.36, z)) + o * 0.28 + V((0, 0.28, 0)), 0.018, 'mastgalv', n=4)
    for (ax, c, s0, s1) in runs:
        P = (lambda s, y, o=0.0: V((s, y, c + o))) if ax == 'x' else (lambda s, y, o=0.0: V((c + o, y, s)))
        o = outw(*((s0 + 0.5, c) if ax == 'x' else (c, s0 + 0.5)))[0]
        oo = o.x if ax == 'z' else o.z
        # the fabric: one cutout sheet down the middle (the south-east run's middle panel has lost a tie wire and sags)
        if ax == 'x' and abs(c + 5) < 0.1 and s0 > 50:
            for (a, b2, ta, tb) in ((s0, 57.0, 1.222, 1.222), (57.0, 58.25, 1.222, 1.13), (58.25, 59.5, 1.13, 1.222), (59.5, s1, 1.222, 1.222)):
                K.quad([P(a, 0.05), P(b2, 0.05), P(b2, tb), P(a, ta)], 'mastchain')
        else: K.quad([P(s0, 0.05), P(s1, 0.05), P(s1, 1.222), P(s0, 1.222)], 'mastchain')  # (one sheet: cutouts draw both sides)
        rod(P(s0, 1.235), P(s1, 1.235), 0.022, 'mastgalv', n=6)  # the top rail
        rod(P(s0, 0.09), P(s1, 0.09), 0.007, 'mastgalvdk', n=3)  # the tension wire
        # three strands of barbed wire along the arms' tips
        for t in (0.36, 0.68, 1.0):
            y = 1.36 + 0.28 * t; off = oo * 0.28 * t; L = abs(s1 - s0)
            q = [P(s0, y - 0.024, off), P(s1, y - 0.024, off), P(s1, y + 0.024, off), P(s0, y + 0.024, off)]
            K.quad(q, 'mastbarb', uv=[(0, 0), (L / 0.25, 0), (L / 0.25, 1), (0, 1)])
    # the gates: frames of tube with fabric in them, swung right back flat against the outside of the fence
    for (ax, c, hinge, d, w, sag) in (('z', 42.0, 2.0, -1, 1.94, 0), ('z', 42.0, 6.0, 1, 1.94, 1), ('x', -5.0, 48.0, -1, 1.94, 0), ('x', -5.0, 52.0, 1, 1.94, 0),
                                      ('x', 13.0, 50.0, -1, 1.94, 0), ('x', 13.0, 54.0, 1, 1.94, 0), ('z', 62.0, -1.0, -1, 1.44, 0), ('z', 62.0, 2.0, 1, 1.44, 0)):
        oo = (-1 if c in (42.0, -5.0) else 1) * 0.15
        P = (lambda s, y: V((s, y, c + oo))) if ax == 'x' else (lambda s, y: V((c + oo, y, s)))
        s_a, s_b = hinge + d * 0.09, hinge + d * (0.09 + w)
        y0, y1 = 0.1, 1.24
        tilt = (lambda s, y: y - 0.12 * abs(s - s_a) / w * (1 - (y - y0) / (y1 - y0) * 0.2)) if sag else (lambda s, y: y)  # (off its top hinge: the free end's dropped)
        Q = lambda s, y: P(s, tilt(s, y))
        corners = [Q(s_a, y0), Q(s_b, y0), Q(s_b, y1), Q(s_a, y1)]
        for i in range(4): rod(corners[i], corners[(i + 1) % 4], 0.022, 'mastgalv', n=4)
        rod(Q(s_a, y0), Q(s_b, y1), 0.016, 'mastgalv', n=3)
        K.quad([Q(s_a + d * 0.02, y0 + 0.02), Q(s_b - d * 0.02, y0 + 0.02), Q(s_b - d * 0.02, y1 - 0.02), Q(s_a + d * 0.02, y1 - 0.02)], 'mastchain')
        hp = V((hinge, 0, c)) if ax == 'x' else V((c, 0, hinge))
        for y in ((0.3, 1.1) if not sag else (0.3,)):
            box(hp + V((-0.09, y - 0.04, -0.09)), hp + V((0.09, y + 0.04, 0.09)), 'mastgalvdk')
            rod(V((hp.x, y, hp.z)), Q(s_a, y), 0.016, 'mastgalvdk', n=3)
        if sag:  # the top hinge strap, snapped, hanging off the post
            rod(V((hp.x, 1.1, hp.z)) + (V((0, 0, d * 0.09)) if ax == 'z' else V((d * 0.09, 0, 0))), V((hp.x, 0.86, hp.z)) + (V((0.05, 0, d * 0.12)) if ax == 'z' else V((d * 0.12, 0, 0.05))), 0.016, 'mastgalvdk', n=4)
    # a padlock on a cut chain, hanging off the west gate's post (KEEP OUT, they said)
    lp = V((41.92, 0.95, 6.0))
    poly([lp + V((0, 0.12, 0)), lp + V((-0.03, 0.05, 0.02)), lp + V((-0.02, -0.04, 0.0)), lp + V((-0.04, -0.12, 0.02))], 0.012, 'mastgalvdk', n=4)
    cbox(lp + V((-0.08, -0.26, -0.03)), lp + V((0.0, -0.15, 0.04)), 'mastgen', c=0.012)
    ring(lp + V((-0.04, -0.13, 0.005)), (1, 0, 0), 0.03, 0.007, 'mastgalv', seg=6, n=4, a0=0.0, a1=math.pi)
    # signs on the fabric, facing out
    for (cell, c, n, w, h) in (('rf', (41.94, 0.95, -1.6), (-1, 0, 0), 0.32, 0.4), ('keep', (44.6, 0.95, -5.04), (0, 0, -1), 0.48, 0.24),
                               ('rf', (57.4, 0.95, -5.04), (0, 0, -1), 0.32, 0.4), ('asr', (46.4, 0.95, 13.04), (0, 0, 1), 0.48, 0.24),
                               ('keep', (58.6, 0.95, 13.04), (0, 0, 1), 0.48, 0.24), ('rf', (62.06, 0.95, 6.6), (1, 0, 0), 0.32, 0.4)):
        sign(cell, c, n, w, h, ties=0.062)


# ------------------------------------------------------------ the equipment shelter
SX0, SX1, SZ0, SZ1 = 44.4, 49.6, 0.9, 5.1   # outside of the walls
def shelter():
    K.inside = [((44.6, 0.2, 1.1), (49.4, 2.9, 4.9))]
    walls = [b for b in K.boxes if b['mat'] == 'shedmetal']
    for k, bs in K.walls(walls).items():
        K.wall_plane(k[0], k[1], k[2], bs, 'mastshell', 'mastint', trim='mastgalv', sub=1.0, doors=False, shards=False, sill=False)
    box((45.27, 1.04, SZ1), (47.13, 1.1, SZ1 + 0.09), 'mastgalv', skip=('nz',))  # the window's sill
    # the floor: sealed concrete inside, a steel threshold, a steel skid round the slab's foot
    K.quad([(44.6, 0.2, 4.9), (49.4, 0.2, 4.9), (49.4, 0.2, 1.1), (44.6, 0.2, 1.1)], 'mastconc', sub=1.0)
    K.quad([(44.4, 0.2, 4.0), (44.6, 0.2, 4.0), (44.6, 0.2, 2.0), (44.4, 0.2, 2.0)], 'mastgalvdk')
    for (mn, mx) in (((44.4, 0.02, 0.9), (49.6, 0.2, 1.0)), ((44.4, 0.02, 5.0), (49.6, 0.2, 5.1)), ((44.4, 0.02, 1.0), (44.5, 0.2, 5.0)), ((49.5, 0.02, 1.0), (49.6, 0.2, 5.0))):
        K.box(mn, mx, {'all': 'mastgalvdk', 'top': None}, cull=False)
    # the roof: a steel deck with a drip edge round it, the ceiling and the soffit under
    rf = next(b for b in K.boxes if b['mat'] == 'roofg')
    (x0, y0, z0), (x1, y1, z1) = rf['min'], rf['max']; rc = V(((x0 + x1) / 2, 3.0, (z0 + z1) / 2))
    K.quad([(x0 + 0.03, y1, z1 - 0.03), (x1 - 0.03, y1, z1 - 0.03), (x1 - 0.03, y1, z0 + 0.03), (x0 + 0.03, y1, z0 + 0.03)], 'mastgalvdk', sub=1.5)
    E = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]; I_ = [(x0 + 0.03, z0 + 0.03), (x1 - 0.03, z0 + 0.03), (x1 - 0.03, z1 - 0.03), (x0 + 0.03, z1 - 0.03)]
    for i in range(4):
        (p, q), (pi, qi) = (E[i], E[(i + 1) % 4]), (I_[i], I_[(i + 1) % 4])
        face_out([(p[0], y0 - 0.03, p[1]), (q[0], y0 - 0.03, q[1]), (q[0], y1 + 0.02, q[1]), (p[0], y1 + 0.02, p[1])], 'mastgalv', rc)  # the drip edge
        face_out([(p[0], y1 + 0.02, p[1]), (q[0], y1 + 0.02, q[1]), (qi[0], y1 + 0.02, qi[1]), (pi[0], y1 + 0.02, pi[1])], 'mastgalv', rc - V((0, 1, 0)))
        face_out([(pi[0], y1, pi[1]), (qi[0], y1, qi[1]), (qi[0], y1 + 0.02, qi[1]), (pi[0], y1 + 0.02, pi[1])], 'mastgalv', V((rc.x + (rc.x - (pi[0] + qi[0]) / 2) * 9, 3.0, rc.z + (rc.z - (pi[1] + qi[1]) / 2) * 9)))
    face_out([(44.6, y0, 1.1), (49.4, y0, 1.1), (49.4, y0, 4.9), (44.6, y0, 4.9)], 'mastint', (47, 4, 3))
    for (a, b2) in (((x0, z0), (x1, 1.1)), ((x0, 4.9), (x1, z1)), ((x0, 1.1), (44.6, 4.9)), ((49.4, 1.1), (x1, 4.9))):
        face_out([(a[0], y0, a[1]), (b2[0], y0, a[1]), (b2[0], y0, b2[1]), (a[0], y0, b2[1])], 'mastgalvdk', (47, 4, 3))
    for (cx_, cz_) in ((45.2, 1.6),):  # a vent cap and a GPS puck on the roof
        cyl((cx_, y1, cz_), (0, 1, 0), 0.09, 0.22, 'mastgalv', n=8, caps=(False, False)); cyl((cx_, y1 + 0.22, cz_), (0, 1, 0), 0.16, 0.06, 'mastgalv', n=8, r1=0.03, caps=(True, True))
    cyl((47.6, y1, 4.6), (0, 1, 0), 0.07, 0.05, 'mastradome', n=8, r1=0.05)
    # ribs: proud vertical trapezoids every 0.5 m (the panels' major ribs), not over openings or what's hung on the wall
    rib = [(0.04, 0.0), (0.016, 0.034), (-0.016, 0.034), (-0.04, 0.0)]
    def ribs(axis, face, nrm, a0, a1, skip):
        n = V(nrm); side = V((0, 1, 0)).cross(n); a = a0 + 0.25
        while a < a1 - 0.2:
            if not any(s0 - 0.06 <= a <= s1 + 0.06 for (s0, s1) in skip):
                p = V((a, 0.21, face)) if axis == 'x' else V((face, 0.21, a))
                prism(p, p + V((0, 2.66, 0)), rib, 'mastshell', side=side, closed=False)
            a += 0.5
    ribs('x', SZ0, (0, 0, -1), SX0, SX1, [(45.2, 45.8), (46.6, 49.3)])   # the meter wall
    ribs('x', SZ1, (0, 0, 1), SX0, SX1, [(45.3, 47.1), (47.35, 48.55)])  # the window, the A/C
    ribs('z', SX0, (-1, 0, 0), SZ0, SZ1, [(1.9, 4.1)])                   # the door wall
    ribs('z', SX1, (1, 0, 0), SZ0, SZ1, [(3.4, 4.6)])                    # the port
    # corner trims: an L of angle up each corner (the walls meet there with a notch)
    for (x, z, sx, sz) in ((SX0, SZ0, -1, -1), (SX1, SZ0, 1, -1), (SX1, SZ1, 1, 1), (SX0, SZ1, -1, 1)):
        box((min(x + sx * 0.04, x - sx * 0.12), 0.2, min(z, z + sz * 0.04)), (max(x + sx * 0.04, x - sx * 0.12), 2.9, max(z, z + sz * 0.04)), 'mastgalv', skip=('py',))
        box((min(x, x + sx * 0.04), 0.2, min(z, z - sz * 0.12)), (max(x, x + sx * 0.04), 2.9, max(z, z - sz * 0.12)), 'mastgalv', skip=('py',))
    # the double doors, swung right back against the wall outside on wide-throw hinges; their inside faces show:
    # crash bars, the closer, a kick plate, the spec plate and somebody's smiley sticker
    for (hz, d) in ((2.0, -1), (4.0, 1)):
        z0_, z1_ = sorted((hz + d * 0.03, hz + d * 0.97)); zm = (z0_ + z1_) / 2
        cbox((44.21, 0.24, z0_), (44.26, 2.36, z1_), 'mastdoor', c=0.012)
        box((44.185, 0.26, z0_ + 0.05), (44.215, 0.5, z1_ - 0.05), 'mastgalv', skip=('px',))
        box((44.13, 1.0, z0_ + 0.1), (44.19, 1.07, z1_ - 0.1), 'mastgalv')
        for zz in (z0_ + 0.12, z1_ - 0.12): box((44.15, 0.96, zz - 0.04), (44.215, 1.1, zz + 0.04), 'mastblack', skip=('px',))
        for y in (0.5, 1.3, 2.1): box((44.24, y - 0.07, hz - 0.05), (44.42, y + 0.07, hz + 0.05), 'mastgalvdk')
        box((44.17, 2.2, zm - 0.25), (44.215, 2.28, zm + 0.25), 'mastblack', skip=('px',))
    sign('spec', (44.2, 1.6, 4.5), (-1, 0, 0), 0.4, 0.15)
    decal('sticker_0', (44.205, 1.45, 1.35), (-1, 0, 0), 0.16, 0.16)
    decal('sticker_1', (44.205, 0.75, 4.75), (-1, 0, 0), 0.11, 0.11)
    # a drip hood over the door on two brackets, the lamp over that
    prism((44.4, 2.52, 1.75), (44.4, 2.52, 4.25), [(-0.006, 0.0), (0.34, -0.06), (0.36, 0.0), (-0.006, 0.14)], 'mastgalv', side=(-1, 0, 0), caps=(True, True))
    for z in (1.85, 4.15): prism((44.4, 2.37, z - 0.01), (44.4, 2.37, z + 0.01), [(-0.006, 0.0), (-0.006, 0.15), (0.28, 0.13)], 'mastgalvdk', side=(-1, 0, 0), caps=(True, True))
    box((44.24, 2.68, 2.85), (44.4, 2.86, 3.15), 'mastblack', skip=('px',))
    box((44.27, 2.655, 2.9), (44.37, 2.69, 3.1), 'mastlamp', skip=('py',))
    sign('station', (45.5, 1.75, SZ0 - 0.045), (0, 0, -1), 0.6, 0.225)
    # the wall-pack A/C on the back wall: a beige cabinet, louvred grilles, a drip tray, its power whip
    ac0, ac1 = (47.4, 0.45, SZ1 + 0.035), (48.5, 2.25, SZ1 + 0.3)
    cbox(ac0, ac1, 'mastradome', c=0.03)
    for (y0_, y1_) in ((0.6, 1.25), (1.45, 2.1)):
        plate([(47.5, y0_, ac1[2] + 0.004), (48.4, y0_, ac1[2] + 0.004), (48.4, y1_, ac1[2] + 0.004), (47.5, y1_, ac1[2] + 0.004)], 'mastlouvre', 0.004)
    plate([(ac0[0] - 0.003, 0.7, 5.33), (ac0[0] - 0.003, 0.7, 5.18), (ac0[0] - 0.003, 1.9, 5.18), (ac0[0] - 0.003, 1.9, 5.33)], 'mastlouvre', 0.003)
    plate([(ac1[0] + 0.003, 0.7, 5.18), (ac1[0] + 0.003, 0.7, 5.33), (ac1[0] + 0.003, 1.9, 5.33), (ac1[0] + 0.003, 1.9, 5.18)], 'mastlouvre', 0.003)
    box((47.45, 0.38, SZ1 + 0.04), (48.45, 0.445, SZ1 + 0.32), 'mastgalvdk', skip=('nz',))
    poly([V((48.42, 2.0, SZ1 + 0.3)), V((48.62, 2.1, SZ1 + 0.1)), V((48.62, 2.5, SZ1 + 0.05))], 0.02, 'mastblack', n=4)
    decal('grime_run', (47.95, 0.95, ac1[2] + 0.004), (0, 0, 1), 0.7, 0.5)
    # the cable port on the east wall (the ice bridge comes in here), the ground bar under it and its lead to the ring
    box((SX1, 2.25, 3.5), (SX1 + 0.05, 2.7, 4.5), 'mastgalv', skip=('nx',))
    for (y, z) in ((2.36, 3.75), (2.36, 4.0), (2.36, 4.25), (2.58, 3.75), (2.58, 4.0), (2.58, 4.25)):
        cyl((SX1 + 0.05, y, z), (1, 0, 0), 0.05, 0.07, 'mastblack', n=5, caps=(False, True), r1=0.035)
    box((SX1 + 0.04, 1.86, 3.55), (SX1 + 0.065, 1.94, 4.45), 'mastcopper', skip=('nx',))
    for z in (3.65, 3.85, 4.05, 4.25): cyl((SX1 + 0.065, 1.9, z), (1, 0, 0), 0.015, 0.02, 'mastcopper', n=4)
    poly([V((SX1 + 0.08, 1.9, 4.42)), V((SX1 + 0.12, 1.2, 4.5)), V((SX1 + 0.14, 0.06, 4.7)), V((51.5, 0.055, 5.6)), V((54.0, 0.055, 6.0))], 0.012, 'mastcopper', n=4)
    # the meter, the disconnect and the generator plug on the meter wall; the plug's cable off across the gravel
    box((48.75, 0.8, SZ0 - 0.16), (49.25, 1.3, SZ0 - 0.035), 'mastgalv', skip=('pz',))
    box((48.88, 0.95, SZ0 - 0.2), (49.12, 1.15, SZ0 - 0.159), 'mastblack', skip=('pz',))
    box((47.7, 1.3, SZ0 - 0.15), (48.3, 2.0, SZ0 - 0.035), 'mastgalv', skip=('pz',))
    decal('jbox', (48.0, 1.65, SZ0 - 0.15), (0, 0, -1), 0.4, 0.4)
    box((46.6, 1.4, SZ0 - 0.12), (47.2, 1.95, SZ0 - 0.035), 'mastgalv', skip=('pz',))
    decal('meter', (46.9, 1.67, SZ0 - 0.12), (0, 0, -1), 0.42, 0.42)
    poly([V((49.0, 0.95, SZ0 - 0.2)), V((49.05, 0.25, SZ0 - 0.3)), V((49.4, 0.065, SZ0 - 0.6)), V((51.0, 0.065, -1.0)), V((53.2, 0.065, -2.2)), V((56.0, 0.065, -2.5)),
          V((58.0, 0.065, -3.0)), V((58.95, 0.3, -3.3))], 0.025, 'mastblack', n=5)
    # inside: the console under the radio's picture (a rack bezel round it, knobs, a mic, a mug, a smooth jazz record),
    # the chair, a cable tray from the port, the battery cabinet against the wall, the extinguisher, a poster
    dk = next(b for b in K.boxes if b['mat'] == 'metal' and b['max'][1] < 1.05 and b['min'][1] > 0.1)
    (x0, y0, z0), (x1, y1, z1) = dk['min'], dk['max']
    cbox((x0, y0, z0), (x1, y1, z1), 'mastgalvdk', c=0.025, skip=('ny',), mats={'py': 'mastblack'})
    for (a, b2) in (((47.73, 1.0), (47.79, 1.84)), ((49.21, 1.0), (49.27, 1.84))): box((a[0], a[1], 1.13), (b2[0], b2[1], 1.33), 'mastgalvdk', skip=('ny', 'py'))
    box((47.73, 1.84, 1.13), (49.27, 1.88, 1.33), 'mastgalvdk')
    for x in (47.9, 48.15, 48.4, 48.65, 48.9, 49.15): cyl((x, 0.8, z1), (0, 0, 1), 0.035, 0.03, 'mastgalv', n=4, caps=(False, True))
    poly([V((48.0, y1, 1.6)), V((48.02, 1.3, 1.62)), V((48.15, 1.42, 1.78))], 0.008, 'mastblack', n=4)
    box((48.12, 1.4, 1.74), (48.2, 1.48, 1.86), 'mastblack')
    cyl((48.8, y1, 1.9), (0, 1, 0), 0.04, 0.1, 'mastdoor', n=8, caps=(False, True))
    cyl((48.45, y1, 1.75), (0, 1, 0), 0.17, 0.006, 'mastblack', n=10, caps=(False, True))
    cyl((48.45, y1 + 0.006, 1.75), (0, 1, 0), 0.06, 0.004, 'mastgen', n=8, caps=(False, True))
    ch = next(b for b in K.boxes if b['mat'] == 'officechair')
    (x0, y0, z0), (x1, y1, z1) = ch['min'], ch['max']; cc = V(((x0 + x1) / 2, 0, (z0 + z1) / 2))
    for k in range(5):
        a = k * math.tau / 5 + 0.3; e = cc + V((math.cos(a) * 0.33, 0.22, math.sin(a) * 0.33))
        rod(cc + V((0, 0.29, 0)), e, 0.025, 'mastblack', n=3)
    cyl(cc + V((0, 0.27, 0)), (0, 1, 0), 0.03, 0.3, 'mastgalv', n=4, caps=(False, False))
    cbox((x0 + 0.02, 0.57, z0 + 0.02), (x1 - 0.02, y1, z1 - 0.02), 'mastblack', c=0.04)
    rod(cc + V((0, 0.6, 0.3)), cc + V((0, 0.85, 0.36)), 0.025, 'mastblack', n=3)
    cbox(cc + V((-0.24, 0.85, 0.3)), cc + V((0.24, 1.35, 0.4)), 'mastblack', c=0.04)
    tr = 2.72
    for z in (3.85, 4.15): rod((49.4, tr, z), (47.9, tr, z), 0.012, 'mastgalvdk', n=3)
    for x in (49.2, 48.8, 48.4, 48.0): rod((x, tr, 3.85), (x, tr, 4.15), 0.01, 'mastgalvdk', n=3)
    rod((49.4, tr + 0.04, 4.0), (48.0, tr + 0.04, 4.0), 0.03, 'mastblack', n=4)
    poly([V((48.0, tr + 0.04, 4.0)), V((47.8, 2.0, 3.0)), V((48.3, 1.6, 1.4))], 0.025, 'mastblack', n=4)
    box((45.2, 0.2, 1.1), (46.6, 1.4, 1.36), 'mastgalvdk', skip=('ny', 'nz'))
    for x in (45.55, 46.25): box((x - 0.3, 0.32, 1.36), (x + 0.3, 1.28, 1.38), 'mastgalv', skip=('nz',))
    cyl((49.25, 0.45, 4.7), (0, 1, 0), 0.08, 0.45, 'mastorange', n=8, caps=(False, True), r1=0.07)
    decal('poster_1', (48.3, 1.7, 4.9), (0, 0, -1), 0.32, 0.48)


# ------------------------------------------------------------ the towable generator (the game's yellow box) and its trailer
def generator():
    g = next(b for b in K.boxes if b['mat'] == 'generator')
    (x0, y0, z0), (x1, y1, z1) = g['min'], g['max']; zm = (z0 + z1) / 2
    # the enclosure: candy yellow, chamfered, on the trailer; doors down both sides, louvres at the radiator end
    cbox((x0, 0.5, z0), (x1, y1 - 0.06, z1), 'mastgen', c=0.05, mats={'ny': 'mastblack'})
    cbox((x0 + 0.06, y1 - 0.08, z0 + 0.06), (x1 - 0.06, y1, z1 - 0.06), 'mastgen', c=0.03, skip=('ny',))
    for z, s in ((z0, -1), (z1, 1)):
        for xa, xb in ((x0 + 0.12, x0 + 1.12), (x0 + 1.22, x1 - 0.5)):
            for x in (xa - 0.012, xb + 0.012):
                plate([(x - 0.006, 0.56, z + s * 0.005), (x + 0.006, 0.56, z + s * 0.005), (x + 0.006, 1.17, z + s * 0.005), (x - 0.006, 1.17, z + s * 0.005)][::(1 if s > 0 else -1)], 'mastblack', 0.005)
            box((xb - 0.14, 0.82, z - 0.02), (xb - 0.06, 0.9, z + 0.02), 'mastgalv')
        plate([(x1 - 0.42, 0.62, z + s * 0.005), (x1 - 0.08, 0.62, z + s * 0.005), (x1 - 0.08, 1.12, z + s * 0.005), (x1 - 0.42, 1.12, z + s * 0.005)][::(1 if s > 0 else -1)], 'mastlouvre', 0.005)
    plate([(x1 + 0.005, 0.62, z0 + 0.12), (x1 + 0.005, 0.62, z1 - 0.12), (x1 + 0.005, 1.14, z1 - 0.12), (x1 + 0.005, 1.14, z0 + 0.12)][::-1], 'mastlouvre', 0.005)
    sign('brand', (x0 + 0.62, 1.0, z1), (0, 0, 1), 0.48, 0.16)
    sign('diesel', (x0 + 1.5, 0.72, z1), (0, 0, 1), 0.3, 0.1)
    sign('brand', (x0 + 0.62, 1.0, z0), (0, 0, -1), 0.48, 0.16)
    sign('panel', (x0, 0.92, zm), (-1, 0, 0), 0.56, 0.28)
    cyl((x0 + 1.5, 0.9, z1), (0, 0, 1), 0.06, 0.03, 'mastblack', n=8, caps=(False, True))
    cbox((x0 + 1.05, y1 - 0.02, zm - 0.05), (x0 + 1.35, y1 + 0.02, zm + 0.05), 'mastgalvdk', c=0.01, skip=('ny',))  # the lifting eye's plate
    ring((x0 + 1.2, y1 + 0.09, zm), (0, 0, 1), 0.07, 0.016, 'mastgalvdk', seg=8, n=4)
    # the exhaust (the game's pipe box): a stack with a sooty rain flap propped open
    ex = next(b for b in K.boxes if b['mat'] == 'metal' and b['min'][1] > 1.2 and b['max'][1] < 2.2)
    exc = V(((ex['min'][0] + ex['max'][0]) / 2, 0, (ex['min'][2] + ex['max'][2]) / 2))
    cyl(exc + V((0, y1 - 0.02, 0)), (0, 1, 0), 0.13, 0.08, 'mastgalvdk', n=8)
    cyl(exc + V((0, y1 + 0.06, 0)), (0, 1, 0), 0.1, 0.66, 'mastgalvdk', n=8, caps=(False, False))
    prism(exc + V((-0.1, 2.06, -0.11)), exc + V((-0.1, 2.06, 0.11)), [(0.0, 0.0), (0.2, -0.15), (0.22, -0.13), (0.02, 0.02)], 'mastblack', side=(1, 0, 0), caps=(True, True))
    decal('grime_scorch', (exc.x + 0.12, y1, exc.z), (0, 1, 0), 0.6, 0.6, along=(1, 0, 0))
    # the trailer: frame rails, the axle, two wheels tucked under, the A-frame drawbar with a jockey wheel and chains
    for z in (z0 + 0.22, z1 - 0.22):
        cbox((x0 + 0.05, 0.38, z - 0.04), (x1 + 0.02, 0.5, z + 0.04), 'mastblack', c=0.012, skip=('py',))
    xa = (x0 + x1) / 2
    rod((xa, 0.27, z0 + 0.12), (xa, 0.27, z1 - 0.12), 0.035, 'mastblack', n=6)
    for (za, zb, out) in ((z0 + 0.03, z0 + 0.22, -1), (z1 - 0.22, z1 - 0.03, 1)):
        cyl((xa, 0.27, za), (0, 0, 1), 0.27, zb - za, 'mastblack', n=12)
        cyl((xa, 0.27, za if out < 0 else zb), (0, 0, out), 0.16, 0.006, 'mastgalv', n=8, caps=(False, True))
    for z in (z0 + 0.22, z1 - 0.22): rod((x1, 0.44, z), (x1 + 0.45, 0.42, zm), 0.04, 'mastblack', n=4)
    cbox((x1 + 0.4, 0.36, zm - 0.06), (x1 + 0.52, 0.47, zm + 0.06), 'mastblack', c=0.015)
    cyl((x1 + 0.3, 0.12, zm + 0.08), (0, 1, 0), 0.03, 0.34, 'mastgalv', n=6, caps=(False, True))
    cyl((x1 + 0.3, 0.06, zm + 0.05), (0, 0, 1), 0.06, 0.06, 'mastblack', n=8)
    for z in (zm - 0.05, zm + 0.05): poly([V((x1 + 0.38, 0.4, z)), V((x1 + 0.42, 0.12, z + (z - zm) * 2)), V((x1 + 0.46, 0.06, z + (z - zm) * 3))], 0.008, 'mastgalvdk', n=3)
    u0, v0, du, dv = KIT['mastsigns']['cells']['hazard']; v0 = 1 - v0 - dv
    plate([(x1 + 0.4, 0.476, zm + 0.06), (x1 + 0.52, 0.476, zm + 0.06), (x1 + 0.52, 0.476, zm - 0.06), (x1 + 0.4, 0.476, zm - 0.06)], 'mastsign', 0.006, uv=[(u0, v0), (u0 + du * 0.25, v0), (u0 + du * 0.25, v0 + dv * 0.5), (u0, v0 + dv * 0.5)])


# ------------------------------------------------------------ the wooden cable reels (the game's three boxes each)
def reels():
    for b in [b for b in K.boxes if b['mat'] == 'cable']:
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']; cx = (x0 + x1) / 2; cy = (y0 + y1) / 2
        fl = [f for f in K.boxes if f['mat'] == 'logend' and abs((f['min'][0] + f['max'][0]) / 2 - cx) < 0.1 and min(abs(f['max'][2] - z0), abs(f['min'][2] - z1)) < 0.01]
        for f in fl:  # the flanges: plank discs, a steel arbor plate, tie-rod nuts on the outer face
            fz0, fz1 = f['min'][2], f['max'][2]; out = -1 if fz1 <= z0 + 0.01 else 1; zf = fz0 if out < 0 else fz1
            cyl((cx, 0.7, fz0), (0, 0, 1), 0.7, fz1 - fz0, 'mastwood', n=14)
            box((cx - 0.16, 0.54, zf - 0.012), (cx + 0.16, 0.86, zf + 0.012), 'mastgalvdk')
            cyl((cx, 0.7, zf + out * 0.012), (0, 0, out), 0.06, 0.004, 'mastblack', n=6, caps=(False, True))
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2
                cyl((cx + math.cos(a) * 0.36, 0.7 + math.sin(a) * 0.36, zf), (0, 0, out), 0.035, 0.03, 'mastgalvdk', n=3, caps=(False, True))
        # the cable wound on its drum (wraps standing proud), its loose end trailing off over the gravel
        cyl((cx, cy, z0), (0, 0, 1), 0.4, z1 - z0, 'mastblack', n=14, caps=(False, False))
        for z in (z0 + 0.25, z0 + 0.6): cyl((cx, cy, z), (0, 0, 1), 0.415, 0.035, 'mastblack', n=14, caps=(False, False))
        zt = z0 + 0.6; tail = 1 if cx < 50 else -1
        poly([V((cx + tail * 0.4, cy, zt)), V((cx + tail * 0.62, 0.45, zt + 0.1)), V((cx + tail * 0.85, 0.075, zt + 0.3)), V((cx + tail * 1.6, 0.075, zt + 0.55)), V((cx + tail * 2.3, 0.075, zt + 0.35))], 0.03, 'mastblack', n=5)
        zo = max(f['max'][2] for f in fl)
        u0, v0, du, dv = KIT['mastsigns']['cells']['stencil']; v0 = 1 - v0 - dv
        plate([(cx - 0.5, 0.97, zo + 0.006), (cx + 0.5, 0.97, zo + 0.006), (cx + 0.5, 1.22, zo + 0.006), (cx - 0.5, 1.22, zo + 0.006)], 'mastsign', 0.006, uv=[(u0, v0), (u0 + du, v0), (u0 + du, v0 + dv), (u0, v0 + dv)])


# ------------------------------------------------------------ the ice bridge: a cable ladder from the shelter's port to the mast
def bridge():
    a, b = V((SX1 + 0.06, 2.75, 4.0)), V((54.86, 2.75, 7.45))
    d = (b - a); L = d.length; d.normalize(); s = V((d.z, 0, -d.x))
    for o in (-0.22, 0.22):
        prism(a + s * o, b + s * o, [(-0.02, -0.05), (0.02, -0.05), (0.02, 0.05), (-0.02, 0.05)], 'mastgalv', side=s, caps=(True, True))
    n = int(L / 0.4)
    for k in range(1, n + 1):
        p = a + d * (k * L / (n + 1)); rod(p - s * 0.2 - V((0, 0.03, 0)), p + s * 0.2 - V((0, 0.03, 0)), 0.012, 'mastgalvdk', n=4)
    for k, o in enumerate((-0.1, 0.0, 0.1)):  # the coax across it, out of the port and on up the mast
        st = V((SX1 + 0.12, 2.36 + 0.22 * (k % 2), 3.75 + 0.25 * k))
        poly([st, a + s * o + V((0, 0.03, 0)), b + s * o + V((0, 0.03, 0)), V((55.22, 2.83, 7.45 + (k - 1) * 0.08))], 0.022, 'mastblack', n=4)
    rod((SX1, 2.2, 4.0), a + V((0, -0.05, 0)) + d * 0.5, 0.03, 'mastgalvdk', n=4)  # its wall bracket
    rod(b - d * 0.05 + V((0, -0.05, 0)), (55.0, 2.7, 7.0), 0.03, 'mastgalvdk', n=4)  # clamped to the leg


def post_process(objs):
    """after the kit's AO: the shine and no-mip flags on the materials (archfield.js reads them), smooth round things"""
    for m in bpy.data.materials:
        if m.name in GLOSS: m['shine'], m['spec'] = GLOSS[m.name]
        if m.name in NOMIP: m['nomip'] = 1
    for ob in objs:
        me = ob.data
        for p in me.polygons: p.use_smooth = True
        try: me.set_sharp_from_angle(angle=math.radians(38))
        except Exception as e: print('smooth by angle failed', e)


def build():
    global K
    K = Kit(os.path.join(HERE, 'boxes', 'mastyard.json'), seed=13)
    K.ground = 0.04
    for b in K.boxes: b['_done'] = True
    K.extra_occ = [((30.0, -1.0, -20.0), (80.0, 0.04, 30.0))]  # the ground, for the AO
    mast(); anchors(); fence(); shelter(); generator(); reels(); bridge()
    objs = K.finish(None)
    post_process(objs)
    AK.export_glb(objs, os.path.join(OUTDIR, 'mastyard.glb'))
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    print('MASTYARD tris', tris, 'objects', len(objs), 'materials', len({o.data.materials[0].name for o in objs}))


build()
