# The keeper's cottage on Lighthouse Point (shared/map.js cottage(): Islands, and Islands S&D's site B, where it's cover),
# drawn over its own boxes as one model per map (cottage, cottage_sd), which stay what you bump into.
# Whitewashed rubble walls on a cyan-painted plinth, yellow surrounds round the door and windows, stone sills, louvred
# shutters folded back (mint on the north window, lilac on the east), window boxes full of flowers. A hot-pink pantile
# hip roof: steep round the eaves, nearly flat on top (the top is where you'd stand, so it stays where the boxes are),
# hip and ridge rolls, a cyan fascia, a yellow gutter whose downpipe swan-necks down the wall into a teal water butt. A
# whitewashed chimney with two pots and a puff of smoke. The door: a bright blue stable door (a brass porthole, a knocker,
# black strap hinges) folded right back against the wall, a lantern and a horseshoe over it, a doormat that says GO AWAY.
# A life ring on the south wall. Inside (you see it through the door and the windows): floorboards, a pink rag rug, a
# beamed ceiling, the pink iron bed with a quilt, the table with a teapot, a mug and the keeper's telescope, a pot-bellied
# stove under the chimney. North of it a washing line on two T-posts with a prop: polka-dot bloomers, a cyan T-shirt, a
# striped towel and one huge sock.
# local frame = the Islands one (placement 0,0,0 on Islands; S&D's is the same model moved, the ground's flat round it on both).
# run: node tools/arch/dump.mjs islands cottage tools/blender/arch/boxes/cottage.json --deco
#      node tools/arch/dump.mjs islands_sd cottage_sd tools/blender/arch/boxes/cottage_sd.json --deco
#      blender52 -b --python tools/blender/arch/make_cottage.py -- [cottage|cottage_sd]   (both by default)
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import archkit
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'cwash': ('limewash', '#fff3e0', {}), 'cwashin': ('limewash', '#ffd2ea', {}), 'cplinth': ('stucco', '#22c8ec', {'gloss': 0.35}),
    'cband': ('trim', '#ffe14d', {'gloss': 0.35}), 'csill': ('stone', '#f6f2ea', {}),
    'croof': ('pantile', '#ff3ea8', {'gloss': 0.35}), 'croll': ('trim', '#ff2a90', {'gloss': 0.55}), 'cfascia': ('timber', '#30d8f0', {'gloss': 0.3}),
    'csoffit': ('timber', '#fff2dc', {}), 'cbeam': ('timber', '#b0835c', {}), 'cgutter': ('trim', '#ffe14d', {'gloss': 0.6}),
    'cdoor': ('grain', '#1e78ff', {'gloss': 0.4}), 'ciron': ('metalplate', '#26222c', {'gloss': 0.5}), 'cbrass': ('metalplate', '#ffcc33', {'gloss': 0.8, 'metal': 1}),
    'cglass': ('trim', '#1a3a5a', {'gloss': 0.9}), 'cshutg': ('louvre', '#2ee8a0', {'gloss': 0.3}), 'cshutl': ('louvre', '#b47cff', {'gloss': 0.3}),
    'cbox': ('grain', '#22c8ec', {'gloss': 0.3}), 'csoil': ('tar', '#4a3226', {}), 'cleaf': ('stucco', '#36c83a', {}),
    'cfl1': ('trim', '#ff3ac8', {'gloss': 0.4}), 'cfl2': ('trim', '#ffe14d', {'gloss': 0.4}), 'cfl3': ('trim', '#ff3030', {'gloss': 0.4}), 'cfl4': ('trim', '#fff8f0', {'gloss': 0.4}),
    'cchim': ('limewash', '#fff3e0', {}), 'cchimb': ('trim', '#ff3ea8', {'gloss': 0.4}), 'cpot': ('stucco', '#ff7a30', {'gloss': 0.4}), 'cdark': ('tar', '#1a141c', {}),
    'csmoke': ('stucco', '#f4eef8', {'fade': 0.6}),
    'cfloor': ('planks', '#ffe0c0', {}), 'crug': ('weave', '#ff6ac8', {}), 'cmat': ('doormat', '#ffffff', {}),
    'cbed': ('metalplate', '#ff4fd8', {'gloss': 0.6}), 'csheet': ('stucco', '#fbf8ff', {}), 'cquilt': ('weave', '#5ad8ff', {}),
    'cwood': ('grain', '#d0905a', {}), 'ctea': ('trim', '#ff4fd8', {'gloss': 0.7}), 'cmug': ('trim', '#ffe14d', {'gloss': 0.6}),
    'cstove': ('metalplate', '#2a2630', {'gloss': 0.5}), 'cfire': ('trim', '#ffb040', {'glow': True, 'glowcol': '#ff8a20'}),
    'clamp': ('trim', '#fff0a0', {'glow': True, 'glowcol': '#ffd860'}), 'cring': ('trim', '#ff3040', {'gloss': 0.5}), 'cringw': ('trim', '#fff8f0', {'gloss': 0.5}),
    'cbutt': ('grain', '#18c8b4', {'gloss': 0.35}), 'clid': ('grain', '#ffe14d', {'gloss': 0.3}),
    'cpost': ('timber', '#ffe0b8', {}), 'cblade': ('timber', '#ff3ea8', {'gloss': 0.3}), 'cline': ('rope', '#fff4e0', {}), 'cpolka': ('polka', '#ffffff', {}), 'cstripe': ('hammock', '#ffffff', {}),
    'cshirt': ('stucco', '#36d8ff', {}), 'cheart': ('trim', '#ff2a8a', {}), 'cpeg': ('trim', '#ff4fd8', {'gloss': 0.4}), 'cpeg2': ('trim', '#ffe14d', {'gloss': 0.4}),
})
NOCAST.update({'cband', 'csill', 'croll', 'cfascia', 'cgutter', 'ciron', 'cbrass', 'cglass', 'cshutg', 'cshutl', 'cbox', 'csoil', 'cleaf', 'cfl1', 'cfl2', 'cfl3', 'cfl4',
               'cchimb', 'cpot', 'cdark', 'csmoke', 'crug', 'cmat', 'ctea', 'cmug', 'cfire', 'clamp', 'cring', 'cringw', 'cline', 'cpeg', 'cpeg2', 'cheart', 'cplinth'})

# the boxes (map.js cottage()): walls 3 m high, 0.25 thick; the roof slabs over them
OX0, OX1, OZ0, OZ1 = 67.475, 74.525, 6.375, 11.625  # the walls' outside faces
IX0, IX1, IZ0, IZ1 = 67.725, 74.275, 6.625, 11.375  # inside
WH = 3.0
L0 = (67.1, 5.9, 74.9, 12.1, 3.3)  # the lower roof slab: x0 z0 x1 z1, its top
L1 = (68.0, 6.8, 74.0, 11.2, 3.8)  # the upper one
RIDGE = (70.2, 71.8, 9.0, 3.96)  # the hip roof's ridge: x0 x1 z, y (16 cm over the top slab: you stand on it, not in it)
OV = 0.12  # how far the tiles run past the lower slab
DOOR = (8.3, 9.7, 2.2)  # z0 z1 top, in the west wall
WN = (70.2, 71.8, 1.1, 2.1)  # the north window: x0 x1 y0 y1
WE = (8.2, 9.8, 1.1, 2.1)  # the east window: z0 z1 y0 y1
LINE = (68.0, 73.9, 3.5, 2.06)  # the washing line: x0 x1 z, y at the posts


# ------------------------------------------------------------ geometry helpers (game space, y up)
def Q(p, mat, uv=None, out=None):
    """a quad; out: a direction it must face (it's flipped if it doesn't)"""
    p = [Vector(q) for q in p]
    if out is not None:
        n = (p[1] - p[0]).cross(p[2] - p[0])
        if n.length < 1e-12: n = (p[2] - p[0]).cross(p[3] - p[0])
        if n.dot(Vector(out)) < 0: p = p[::-1]; uv = uv[::-1] if uv else None
    K.quad(p, mat, uv=uv)


def T3(p, mat, out=None, uv=None):
    """a triangle; uv: its own uvs (else the kit maps it)"""
    p = [Vector(q) for q in p]
    if out is not None and (p[1] - p[0]).cross(p[2] - p[0]).dot(Vector(out)) < 0: p = p[::-1]; uv = uv[::-1] if uv else None
    if uv is None: K.tri(p, mat); return
    g = K._bucket(mat, ''); b = len(g['v'])
    for q, t in zip(p, uv): g['v'].append(tuple(q)); g['uv'].append(tuple(t))
    g['f'].append((b, b + 1, b + 2))


def basis(d):
    d = Vector(d).normalized()
    up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    u = d.cross(up).normalized(); v = u.cross(d).normalized()
    return u, v


def pole(a, b, r, mat, n=8, caps=(True, True), r1=None, rot=0.0, vt=1.0):
    """a round pole from a to b: uvs once round it and along it"""
    a, b = Vector(a), Vector(b); d = b - a; L = d.length
    if L < 1e-5: return
    u, v = basis(d); r1 = r if r1 is None else r1
    ring = lambda c, rr: [c + (u * math.cos(rot + k * math.tau / n) + v * math.sin(rot + k * math.tau / n)) * rr for k in range(n)]
    A, Bb = ring(a, r), ring(b, r1)
    for k in range(n):
        j = (k + 1) % n; mid = (A[k] + A[j] + Bb[k] + Bb[j]) / 4
        out = mid - (a + d * ((mid - a).dot(d) / L / L))
        Q([A[k], A[j], Bb[j], Bb[k]], mat, uv=[(k / n, 0), ((k + 1) / n, 0), ((k + 1) / n, L / vt), (k / n, L / vt)], out=out)
    if caps[0] and r > 1e-4:
        for k in range(1, n - 1): T3([A[0], A[k], A[k + 1]], mat, out=-d)
    if caps[1] and r1 > 1e-4:
        for k in range(1, n - 1): T3([Bb[0], Bb[k], Bb[k + 1]], mat, out=d)


def lathe(c, prof, mat, n=8, rot=0.0, axis=(0, 1, 0), scale=(1, 1)):
    """a turned shape round an axis at c: prof [(radius, height)] bottom to top; a radius of 0 closes it. mat: one
    material, or a function (ring index) -> material (bands)"""
    c = Vector(c); ax = Vector(axis).normalized(); u, v = basis(ax)
    rings = [[c + ax * h + (u * math.cos(rot + k * math.tau / n) * scale[0] + v * math.sin(rot + k * math.tau / n) * scale[1]) * r for k in range(n)] for r, h in prof]
    s = 0.0
    for i in range(len(prof) - 1):
        (r0, h0), (r1, h1) = prof[i], prof[i + 1]; L = math.hypot(r1 - r0, h1 - h0); A, Bb = rings[i], rings[i + 1]
        m = mat(i) if callable(mat) else mat
        for k in range(n):
            j = (k + 1) % n; mid = (A[k] + A[j] + Bb[k] + Bb[j]) / 4
            ctr = c + ax * ((mid - c).dot(ax)); out = mid - ctr
            if out.length < 1e-6 or abs(h1 - h0) < 1e-6: out = ax * (1 if r1 < r0 else -1) if abs(h1 - h0) < 1e-6 else ax * (1 if h1 > h0 else -1)
            uv = [(k / n, s), ((k + 1) / n, s), ((k + 1) / n, s + L), (k / n, s + L)]
            if r0 < 1e-5: T3([A[k], Bb[j], Bb[k]], m, out=out)
            elif r1 < 1e-5: T3([A[k], A[j], Bb[k]], m, out=out)
            else: Q([A[k], A[j], Bb[j], Bb[k]], m, uv=uv, out=out)
        s += L


def torus(c, axis, R, r, mat, n=8, m=4, rot=0.0, tiles=4, boff=0.35):
    """a ring round axis at c (the life ring): R to the tube's middle, r the tube. mat: one, or (segment) -> mat"""
    c = Vector(c); ax = Vector(axis).normalized(); u, v = basis(ax)
    def P(i, j):
        a = rot + i * math.tau / n; b = j * math.tau / m + boff
        rd = u * math.cos(a) + v * math.sin(a)
        return c + rd * (R + r * math.cos(b)) + ax * (r * math.sin(b))
    for i in range(n):
        mm = mat(i) if callable(mat) else mat
        for j in range(m):
            p = [P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)]
            a = rot + (i + 0.5) * math.tau / n; rd = u * math.cos(a) + v * math.sin(a)
            mid = sum(p, Vector()) / 4; out = mid - (c + rd * R)
            Q(p, mm, uv=[(i / n * tiles, j / m), ((i + 1) / n * tiles, j / m), ((i + 1) / n * tiles, (j + 1) / m), (i / n * tiles, (j + 1) / m)], out=out)


def cbox(mn, mx, mat, bev=0.0, skip=(), mats=None):
    """a box with its edges chamfered by bev (the glossy bevelled look: every edge catches a highlight). skip: faces
    left out ('px','nx','py','ny','pz','nz'), with their chamfers. mats: {face: material} overrides. a face resting on
    the ground (y 0) is never drawn"""
    (x0, y0, z0), (x1, y1, z1) = mn, mx
    if y0 <= 1e-4 and 'ny' not in skip: skip = tuple(skip) + ('ny',)
    M = lambda f: (mats or {}).get(f, mat)
    c = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    b = min(bev, (x1 - x0) / 2.01, (y1 - y0) / 2.01, (z1 - z0) / 2.01)
    if b <= 1e-4:
        F = {'px': [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], 'nx': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
             'py': [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], 'ny': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
             'pz': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], 'nz': [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)]}
        for f, q in F.items():
            if f not in skip: Q(q, M(f), out=Vector({'p': 1, 'n': -1}[f[0]] * Vector([1 if f[1] == a else 0 for a in 'xyz'])))
        return
    X, Y, Z = (x0, x1), (y0, y1), (z0, z1)
    I = lambda v, s: v[0] + b if s == 0 else v[1] - b
    def V(sx, sy, sz, ax):  # the corner (sx, sy, sz)'s vertex on the face across axis ax
        return Vector((X[sx] if ax == 0 else I(X, sx), Y[sy] if ax == 1 else I(Y, sy), Z[sz] if ax == 2 else I(Z, sz)))
    fn = lambda ax, s: ('p' if s else 'n') + 'xyz'[ax]
    for ax in range(3):  # the faces
        for s in (0, 1):
            if fn(ax, s) in skip: continue
            q = [(sx, sy, sz) for sx in (0, 1) for sy in (0, 1) for sz in (0, 1) if (sx, sy, sz)[ax] == s]
            q = [q[0], q[1], q[3], q[2]]
            Q([V(*k, ax) for k in q], M(fn(ax, s)), out=Vector([(1 if s else -1) if i == ax else 0 for i in range(3)]))
    for ax in range(3):  # the chamfers along each edge (along axis ax)
        o = [i for i in range(3) if i != ax]
        for s1 in (0, 1):
            for s2 in (0, 1):
                if fn(o[0], s1) in skip or fn(o[1], s2) in skip: continue
                k0 = [0, 0, 0]; k0[o[0]] = s1; k0[o[1]] = s2; k1 = list(k0); k1[ax] = 1
                p = [V(*k0, o[0]), V(*k1, o[0]), V(*k1, o[1]), V(*k0, o[1])]
                Q(p, M(fn(o[0], s1)), out=sum(p, Vector()) / 4 - c)
    for sx in (0, 1):  # the corners
        for sy in (0, 1):
            for sz in (0, 1):
                if fn(0, sx) in skip or fn(1, sy) in skip or fn(2, sz) in skip: continue
                p = [V(sx, sy, sz, 0), V(sx, sy, sz, 1), V(sx, sy, sz, 2)]
                T3(p, M(fn(1, sy)), out=sum(p, Vector()) / 3 - c)


def earclip(poly):
    """triangles of a simple polygon (either winding), by clipping ears"""
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    idx = list(range(len(poly))) if area > 0 else list(range(len(poly)))[::-1]
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    out = []
    while len(idx) > 3:
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            A, Bp, C = poly[i0], poly[i1], poly[i2]
            if cr(A, Bp, C) <= 1e-9: continue
            if any(cr(A, Bp, poly[j]) >= 0 and cr(Bp, C, poly[j]) >= 0 and cr(C, A, poly[j]) >= 0 for j in idx if j not in (i0, i1, i2)): continue
            out.append((i0, i1, i2)); idx.pop(k); break
        else: raise ValueError('not a simple polygon')
    out.append(tuple(idx))
    return out


def flat(poly, P0, U, V, mat, th=0.01, uvs=1.0, uvf=None):
    """a flat cut-out shape (a sock, bloomers): poly [(u, v)] round its outline, laid out from P0 along U and V (unit
    vectors), th thick, closed. uvs: metres a tile, or uvf(u, v) -> uv"""
    P0, U, V = Vector(P0), Vector(U), Vector(V); N = U.cross(V).normalized()
    W = lambda q, s: P0 + U * q[0] + V * q[1] + N * (s * th / 2)
    uvq = uvf or (lambda u, v: (u / uvs, v / uvs))
    for s in (1, -1):
        for t in earclip(poly):
            T3([W(poly[i], s) for i in t], mat, out=N * s, uv=[uvq(*poly[i]) for i in t])
    n = len(poly); cu = sum(q[0] for q in poly) / n; cv = sum(q[1] for q in poly) / n
    for k in range(n):
        a, bb = poly[k], poly[(k + 1) % n]
        mid = Vector(((a[0] + bb[0]) / 2 - cu, (a[1] + bb[1]) / 2 - cv))
        L = math.hypot(bb[0] - a[0], bb[1] - a[1]); u0 = uvq(*a)
        Q([W(a, 1), W(bb, 1), W(bb, -1), W(a, -1)], mat, out=U * mid.x + V * mid.y, uv=[u0, (u0[0] + L, u0[1]), (u0[0] + L, u0[1] + th), (u0[0], u0[1] + th)])


def sag(a, b, dip, k=6):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / k) - Vector((0, dip * 4 * (i / k) * (1 - i / k), 0)) for i in range(k + 1)]


# ------------------------------------------------------------ the walls
def walls():
    """the wall boxes' faces: limewash outside and in the reveals, pink inside; tops under the roof culled"""
    def pick(f, q):
        c = [sum(v[i] for v in q) / 4 for i in range(3)]
        if f == 'ny': return None
        if f == 'py' and c[1] > WH - 0.01: return None  # (under the roof slab)
        inner = (f == 'px' and abs(c[0] - IX0) < 1e-3) or (f == 'nx' and abs(c[0] - IX1) < 1e-3) or (f == 'pz' and abs(c[2] - IZ0) < 1e-3) or (f == 'nz' and abs(c[2] - IZ1) < 1e-3)
        if inner: return 'cwashin'
        if f == 'py' and c[1] < 1.2 and abs(c[1] - 1.1) < 1e-3: return 'csill'  # (the window's inside sill)
        return 'cwash'
    for b in K.take(lambda b: b['mat'] == 'plaster'):
        K.box(b['min'], b['max'], {'all': pick}, sub=1.5)
    # the plinth: a cyan band round the outside foot, 4 cm proud, 40 cm high (not across the door)
    p, h = 0.04, 0.4
    cbox((OX0 - p, 0, OZ0 - p), (OX1 + p, h, OZ0), 'cplinth', bev=0.012, skip=('pz',))
    cbox((OX0 - p, 0, OZ1), (OX1 + p, h, OZ1 + p), 'cplinth', bev=0.012, skip=('nz',))
    cbox((OX1, 0, OZ0), (OX1 + p, h, OZ1), 'cplinth', bev=0.012, skip=('nx', 'nz', 'pz'))
    cbox((OX0 - p, 0, OZ0), (OX0, h, DOOR[0] - 0.12), 'cplinth', bev=0.012, skip=('px', 'nz'))
    cbox((OX0 - p, 0, DOOR[1] + 0.12), (OX0, h, OZ1), 'cplinth', bev=0.012, skip=('px', 'pz'))
    # the windows: yellow surrounds, a stone sill, shutters folded back, a window box of flowers
    window('z', OZ0, -1, WN[0], WN[1], 'cshutg')
    window('x', OX1, 1, WE[0], WE[1], 'cshutl')


def window(axis, c, s, a0, a1, shut):
    """a window in the wall at (axis 'z': x along it, z = c), facing s (+1 / -1), opening a0..a1 along, y 1.1..2.1"""
    def P(a, y, o): return (a, y, c + s * o) if axis == 'z' else (c + s * o, y, a)
    def box(a0_, a1_, y0, y1, o0, o1, m, bev=0.0, skip=()):
        p0, p1 = P(a0_, y0, o0), P(a1_, y1, o1)
        cbox(tuple(min(p0[i], p1[i]) for i in range(3)), tuple(max(p0[i], p1[i]) for i in range(3)), m, bev=bev, skip=skip)
    back = {'nz': 'pz', 'pz': 'nz', 'nx': 'px', 'px': 'nx'}[('nz' if s < 0 else 'pz') if axis == 'z' else ('nx' if s < 0 else 'px')]
    y0, y1, w = 1.1, 2.1, 0.12
    box(a0 - w, a0, 1.04, y1 + w, 0, 0.025, 'cband', skip=(back,)); box(a1, a1 + w, 1.04, y1 + w, 0, 0.025, 'cband', skip=(back,))
    box(a0, a1, y1, y1 + w, 0, 0.025, 'cband', skip=(back,))
    box(a0 - 0.16, a1 + 0.16, 0.98, 1.1, 0, 0.1, 'csill', bev=0.015, skip=(back,))  # the sill, under the surround's feet
    # the shutters: louvred, hinged at the surround, folded flat to the wall either side
    for (b0, b1) in ((a0 - w - 0.8, a0 - w - 0.01), (a1 + w + 0.01, a1 + w + 0.8)):
        box(b0, b1, 1.06, y1 + 0.06, 0.004, 0.05, shut, bev=0.012, skip=(back,))
    # the window box: under the sill, soil, flowers in the game's colours, a few leaves
    box(a0 + 0.04, a1 - 0.04, 0.72, 0.97, 0.0, 0.26, 'cbox', skip=(back,))
    box(a0 + 0.07, a1 - 0.07, 0.94, 0.95, 0.03, 0.23, 'csoil')
    rr = K.rng; cols = ['cfl1', 'cfl2', 'cfl3', 'cfl4', 'cfl1']
    for k in range(5):
        a = a0 + 0.2 + k * (a1 - a0 - 0.4) / 4 + (rr.random() - 0.5) * 0.06; o = 0.1 + rr.random() * 0.06; hy = 1.1 + rr.random() * 0.1
        lathe(P(a, 0.95, o), [(0.0, 0.0), (0.1, 0.07), (0.0, 0.14)], 'cleaf', n=4, rot=rr.random())  # a clump of leaves
        lathe(P(a, hy, o), [(0.0, -0.05), (0.085, 0.0), (0.0, 0.05)], cols[k], n=5, rot=rr.random())  # a big blossom over it


# ------------------------------------------------------------ the door
def door():
    z0, z1, top = DOOR
    x = OX0
    # the yellow surround (proud 3 cm) and a stone threshold
    cbox((x - 0.03, 0, z0 - 0.14), (x, top + 0.14, z0), 'cband', skip=('px',))
    cbox((x - 0.03, 0, z1), (x, top + 0.14, z1 + 0.14), 'cband', skip=('px',))
    cbox((x - 0.03, top, z0), (x, top + 0.14, z1), 'cband', skip=('px', 'nz', 'pz'))
    cbox((x - 0.06, 0, z0), (IX0, 0.045, z1), 'csill', skip=('nz', 'pz'))
    # the stable door: two leaves, folded right back against the wall north of the opening (it opens out)
    dz0, dz1, dx0, dx1 = z0 - 0.15 - 1.32, z0 - 0.15, x - 0.105, x - 0.045  # (clear of the plinth)
    for (y0, y1) in ((0.06, 1.06), (1.09, 2.17)):
        cbox((dx0, y0, dz0), (dx1, y1, dz1), 'cdoor', bev=0.015)
        # its planks: three grooves, and a Z of braces on the lower leaf / a porthole in the upper
        for k in (1, 2):
            zz = dz0 + k * (dz1 - dz0) / 3
            cbox((dx0 - 0.004, y0 + 0.03, zz - 0.012), (dx0, y1 - 0.03, zz + 0.012), 'ciron', skip=('px',))
        for yy in (y0 + 0.16, y1 - 0.16): cbox((dx0 - 0.016, yy - 0.03, dz1 - 0.55), (dx0 - 0.004, yy + 0.03, dz1 - 0.02), 'ciron', skip=('px',))  # strap hinges (on the hinge side)
    c = Vector((dx0 - 0.004, 1.68, (dz0 + dz1) / 2))
    torus(c, (1, 0, 0), 0.19, 0.035, 'cbrass', n=8, m=3, rot=0.39)
    lathe(c + Vector((0.02, 0, 0)), [(0.17, 0.0), (0.0, 0.0)], 'cglass', n=8, axis=(-1, 0, 0), rot=0.39)
    pole(c + Vector((0, -0.42, 0)), c + Vector((-0.04, -0.42, 0)), 0.04, 'cbrass', n=5, caps=(False, True))  # the knocker's boss
    torus(c + Vector((-0.05, -0.5, 0)), (1, 0, 0), 0.07, 0.015, 'cbrass', n=6, m=3)
    lathe((dx0, 1.02, dz0 + 0.12), [(0.0, 0.0), (0.035, -0.02), (0.03, -0.06), (0.0, -0.065)], 'cbrass', n=6, axis=(-1, 0, 0))  # the knob
    # over the door: a horseshoe (upside down: the luck ran out) and a lantern on a bracket
    hc = Vector((x - 0.03, top + 0.36, (z0 + z1) / 2))
    for k in range(4):
        a0, a1 = math.pi * (0.1 + 0.8 * k / 4), math.pi * (0.1 + 0.8 * (k + 1) / 4)
        pa = hc + Vector((0, -math.sin(a0) * 0.1, math.cos(a0) * 0.1)); pb = hc + Vector((0, -math.sin(a1) * 0.1, math.cos(a1) * 0.1))
        pole(pa, pb, 0.018, 'ciron', n=3, caps=(k == 0, k == 3), rot=0.3)  # (rot: no two segments share a face plane)
    lz = z1 + 0.42
    cbox((x - 0.02, 2.0, lz - 0.05), (x, 2.24, lz + 0.05), 'ciron')
    pole((x - 0.01, 2.2, lz), (x - 0.24, 2.2, lz), 0.014, 'ciron', n=4)
    lc = Vector((x - 0.24, 1.86, lz))
    lathe(lc, [(0.0, -0.04), (0.07, -0.02), (0.07, 0.0)], 'cbrass', n=6)
    lathe(lc, [(0.06, 0.0), (0.075, 0.2)], 'clamp', n=6)
    lathe(lc + Vector((0, 0.2, 0)), [(0.09, 0.0), (0.05, 0.08), (0.0, 0.1)], 'cbrass', n=6)
    pole(lc + Vector((0, 0.29, 0)), (x - 0.24, 2.2, lz), 0.008, 'ciron', n=3, caps=(False, False))
    # the doormat
    Q([(x - 0.78, 0.05, z0 + 0.12), (x - 0.78, 0.05, z1 - 0.12), (x - 0.06, 0.05, z1 - 0.12), (x - 0.06, 0.05, z0 + 0.12)], 'cmat', out=(0, 1, 0),
      uv=[(0, 1), (1, 1), (1, 0), (0, 0)])  # (the game reads the kit with v down: the words' tops toward the door)
    for (a, b_) in (((x - 0.78, z0 + 0.12), (x - 0.78, z1 - 0.12)), ((x - 0.06, z1 - 0.12), (x - 0.06, z0 + 0.12)), ((x - 0.78, z1 - 0.12), (x - 0.06, z1 - 0.12)), ((x - 0.06, z0 + 0.12), (x - 0.78, z0 + 0.12))):
        Q([(a[0], 0.02, a[1]), (b_[0], 0.02, b_[1]), (b_[0], 0.05, b_[1]), (a[0], 0.05, a[1])], 'cmat', out=(a[0] + b_[0] - 2 * (x - 0.42), 0, a[1] + b_[1] - 2 * 9.0), uv=[(0, 0), (1, 0), (1, 0.03), (0, 0.03)])


# ------------------------------------------------------------ the roof
def roof():
    """a hip roof of pantiles: steep from the eaves up to the top slab's edge, then gently up to a short ridge. the
    surface sits on the boxes' tops along their edges, so where you can stand is where it looks like you can"""
    ax0, az0, ax1, az1, ay = L0; bx0, bz0, bx1, bz1, by = L1; rx0, rx1, rz, ry = RIDGE
    k = (by - ay) / (bx0 - ax0)  # the steep part's rise per metre
    E = (ax0 - OV, az0 - OV, ax1 + OV, az1 + OV); ey = ay - OV * k  # the eave line
    def C(r, y): return {'nw': Vector((r[0], y, r[1])), 'ne': Vector((r[2], y, r[1])), 'se': Vector((r[2], y, r[3])), 'sw': Vector((r[0], y, r[3]))}
    Eo, In = C(E, ey), C((bx0, bz0, bx1, bz1), by)
    Rw, Re = Vector((rx0, ry, rz)), Vector((rx1, ry, rz))
    top = {'nw': Rw, 'sw': Rw, 'ne': Re, 'se': Re}
    sides = {'n': ('nw', 'ne', (0, 1, -1), 0, 2), 'e': ('ne', 'se', (1, 1, 0), 2, 0), 's': ('se', 'sw', (0, 1, 1), 0, 2), 'w': ('sw', 'nw', (-1, 1, 0), 2, 0)}
    for s, (a, b, o, ua, va) in sides.items():
        sl = math.hypot(In[a][va] - Eo[a][va], by - ey)  # the steep part's slope length
        def U(p, v): return (p[ua] if s in "ne" else -p[ua], v)  # (u along the eave, v up the slope)
        Q([Eo[a], Eo[b], In[b], In[a]], 'croof', out=o, uv=[U(Eo[a], 0), U(Eo[b], 0), U(In[b], sl), U(In[a], sl)])
        tl = math.hypot(rz - In[a][2] if s in 'ns' else rx0 - In[a][0] if s == 'w' else In[a][0] - rx1, ry - by)
        if s in 'ns':
            Q([In[a], In[b], top[b], top[a]], 'croof', out=o, uv=[U(In[a], sl), U(In[b], sl), U(top[b], sl + tl), U(top[a], sl + tl)])
        else:
            T3([In[a], In[b], top[a]], 'croof', out=o, uv=[U(In[a], sl), U(In[b], sl), U(top[a], sl + tl)])
        # the fascia (cyan) from the eave down to the soffit, and the soffit back to the wall
        Q([Eo[a], Eo[b], Eo[b] - Vector((0, ey - WH, 0)), Eo[a] - Vector((0, ey - WH, 0))], 'cfascia', out=(o[0], 0, o[2]),
          uv=[(Eo[a][ua], 0), (Eo[b][ua], 0), (Eo[b][ua], ey - WH), (Eo[a][ua], ey - WH)])
    # the soffit: a frame under the eaves from the fascia in to the walls
    for (x0, z0, x1, z1) in ((E[0], E[1], E[2], OZ0), (E[0], OZ1, E[2], E[3]), (E[0], OZ0, OX0, OZ1), (OX1, OZ0, E[2], OZ1)):
        Q([(x0, WH, z0), (x1, WH, z0), (x1, WH, z1), (x0, WH, z1)], 'csoffit', out=(0, -1, 0))
    # the rolls: along the hips (eave corner to the top slab's corner to the ridge's end) and the ridge
    lift = Vector((0, 0.035, 0))
    for c in ('nw', 'ne', 'se', 'sw'):
        pole(Eo[c] + lift, In[c] + lift, 0.06, 'croll', n=4, caps=(True, False), rot=0.78)
        pole(In[c] + lift, top[c] + lift, 0.06, 'croll', n=4, caps=(False, False), rot=0.78)
    pole(Rw + lift - Vector((0.08, 0, 0)), Re + lift + Vector((0.08, 0, 0)), 0.075, 'croll', n=6, rot=0.2)
    # the gutters: yellow half-rounds along the north and south eaves, stop ends, the downpipe at the north-east into the butt
    for (z, s) in ((E[1], -1), (E[3], 1)):
        gz0, gz1 = (z - 0.13, z) if s < 0 else (z, z + 0.13)
        cbox((E[0] - 0.03, ey - 0.16, gz0), (E[2] + 0.03, ey - 0.13, gz1), 'cgutter')  # its floor
        cbox((E[0] - 0.03, ey - 0.13, (gz0 if s < 0 else gz1 - 0.02)), (E[2] + 0.03, ey - 0.03, (gz0 + 0.02 if s < 0 else gz1)), 'cgutter', skip=('ny',))  # its lip
    px, pz = BUTT[0], E[1] - 0.065
    pts = [Vector((px, ey - 0.14, pz)), Vector((px, ey - 0.3, pz)), Vector((px, 2.82, OZ0 - 0.06)), Vector((px, 1.32, OZ0 - 0.06)), Vector((px, 1.12, BUTT[1] - 0.12))]
    for i in range(len(pts) - 1): pole(pts[i], pts[i + 1], 0.045, 'cgutter', n=5, caps=(False, False), rot=0.4)
    for y in (2.4, 1.6): cbox((px - 0.06, y - 0.02, OZ0 - 0.11), (px + 0.06, y + 0.02, OZ0), 'ciron')  # its brackets
    chimney()


def roof_y(x, z):
    """the roof's height at (x, z) on the top slab (for the chimney's foot)"""
    rx0, rx1, rz, ry = RIDGE; bx0, bz0, bx1, bz1, by = L1
    dz = abs(z - rz); dx = rx0 - x if x < rx0 else x - rx1 if x > rx1 else 0.0
    return ry - (ry - by) * max(dz, dx) / (rz - bz0)


def chimney():
    """whitewashed, a pink band, a stone cap, two pots, smoke"""
    x0, x1, z0, z1 = 68.4, 69.1, 10.35, 11.05
    foot = min(roof_y(x, z) for x in (x0, x1) for z in (z0, z1)) - 0.06
    cbox((x0, foot, z0), (x1, 4.86, z1), 'cchim', bev=0.025, skip=('ny',))
    cbox((x0 - 0.015, 4.62, z0 - 0.015), (x1 + 0.015, 4.72, z1 + 0.015), 'cchimb')
    cbox((x0 - 0.05, 4.86, z0 - 0.05), (x1 + 0.05, 4.94, z1 + 0.05), 'csill', bev=0.015)
    for (cx, h, lean) in ((68.72, 0.3, 0.0), (69.06, 0.24, 0.03)):
        c = Vector((cx - 0.15, 4.94, (z0 + z1) / 2))
        lathe(c, [(0.1, 0.0), (0.075, h - 0.04), (0.095, h), (0.07, h), (0.065, h - 0.06)], 'cpot', n=6)
        lathe(c + Vector((0, h - 0.06, 0)), [(0.065, 0.0), (0.0, 0.0)], 'cdark', n=6)  # (down inside it: the flue, dark)
    # a puff of smoke drifting off the tall pot (see-through, never hides anyone)
    for (dx, dy, dz, r) in ((0.0, 0.42, 0.02, 0.13), (0.12, 0.66, 0.1, 0.17), (0.3, 0.94, 0.2, 0.22)):
        lathe((68.57 + dx, 4.94 + 0.3 + dy - r, 10.7 + dz), [(0.0, 0.0), (r, r * 0.6), (r * 0.85, r * 1.5), (0.0, r * 2.0)], 'csmoke', n=6, rot=dx * 3)


# ------------------------------------------------------------ outside: the water butt, the life ring, the washing line
BUTT = (73.9, 5.95)


def butt():
    x, z = BUTT
    lathe((x, 0, z), [(0.3, 0.0), (0.345, 0.25), (0.36, 0.48), (0.345, 0.72), (0.31, 0.96), (0.0, 0.96)], 'cbutt', n=8, rot=0.2)
    for (y0, y1, r0, r1) in ((0.1, 0.16, 0.328, 0.34), (0.8, 0.86, 0.335, 0.322)):
        lathe((x, 0, z), [(r0 + 0.012, y0), (r1 + 0.012, y1)], 'ciron', n=8, rot=0.2)
    lathe((x, 0.96, z), [(0.33, 0.0), (0.33, 0.04), (0.0, 0.04)], 'clid', n=8, rot=0.2)  # the lid
    cbox((x - 0.03, 1.0, z - 0.2), (x + 0.03, 1.04, z + 0.2), 'cwood')  # its handle
    t = Vector((x + 0.28, 0.2, z - 0.16))  # the tap
    pole(t, t + Vector((0.08, 0, -0.05)), 0.022, 'cbrass', n=4, caps=(False, False))
    pole(t + Vector((0.08, 0.02, -0.05)), t + Vector((0.08, -0.07, -0.05)), 0.018, 'cbrass', n=4, caps=(False, True))


def life_ring():
    c = Vector((68.7, 1.75, OZ1 + 0.075))
    torus(c, (0, 0, 1), 0.27, 0.07, lambda i: 'cring' if (i // 2) % 2 == 0 else 'cringw', n=12, m=3, rot=0.26, tiles=3)
    cbox((c.x - 0.03, c.y + 0.25, OZ1), (c.x + 0.03, c.y + 0.33, OZ1 + 0.06), 'ciron')  # its hook


def oars():
    """two oars crossed on the south wall (the boat's long gone), on a hook"""
    z = OZ1 + 0.035
    for (p0, p1) in (((72.35, 0.75), (73.95, 2.45)), ((73.95, 0.75), (72.35, 2.45))):  # (east of S&D's site board, x 70.2..71.8)
        a, b = Vector((p0[0], p0[1], z)), Vector((p1[0], p1[1], z)); d = (b - a).normalized(); u = Vector((-d.y, d.x, 0))
        z = z + 0.045  # (the second one over the first)
        pole(a, a + d * 1.75, 0.03, 'cpost', n=4, caps=(True, False), rot=0.78)
        bl = [a + d * 1.6 + u * 0.05, a + d * 1.6 - u * 0.05, a + d * 2.35 - u * 0.09, a + d * 2.35 + u * 0.09]
        for (o, s) in ((0.012, 1), (-0.012, -1)): Q([q + Vector((0, 0, o)) for q in bl], 'cblade', out=(0, 0, s))
        for (i, j) in ((0, 1), (1, 2), (2, 3), (3, 0)): Q([bl[i] + Vector((0, 0, 0.012)), bl[j] + Vector((0, 0, 0.012)), bl[j] - Vector((0, 0, 0.012)), bl[i] - Vector((0, 0, 0.012))], 'cblade', out=(bl[i] + bl[j]) / 2 - (bl[0] + bl[2]) / 2)
    cbox((73.11, 1.56, OZ1), (73.19, 1.66, OZ1 + 0.12), 'ciron')


def washing():
    """two T-posts, a sagging line with a prop under it, pegs, and the laundry"""
    x0, x1, z, yl = LINE
    for x in (x0, x1):
        cbox((x - 0.05, 0, z - 0.05), (x + 0.05, yl + 0.04, z + 0.05), 'cpost', bev=0.012, skip=('py',))
        cbox((x - 0.045, yl - 0.02, z - 0.42), (x + 0.045, yl + 0.06, z + 0.42), 'cpost')
        for s in (-1, 1): pole((x, yl - 0.36, z), (x, yl - 0.01, z + s * 0.32), 0.022, 'cpost', n=3, caps=(False, False))  # its braces
    L = sag((x0, yl + 0.065, z), (x1, yl + 0.065, z), 0.2, k=8)
    mid = (L[4] + L[5]) / 2
    L[4] = L[4] + Vector((0, 0.08, 0)); L[5] = L[5] + Vector((0, 0.08, 0))  # (the prop lifts it there)
    for a, b in zip(L, L[1:]): pole(a, b, 0.009, 'cline', n=3, caps=(False, False), vt=0.25)
    pole((mid.x + 0.25, 0.0, z + 0.55), mid + Vector((0, 0.06, 0)), 0.022, 'cpost', n=4, caps=(False, True))  # the prop, leaning in
    def y_at(x):  # the line's height at x
        for a, b in zip(L, L[1:]):
            if a.x <= x <= b.x: t = (x - a.x) / (b.x - a.x); return a.y + (b.y - a.y) * t
        return yl
    tilt = lambda deg: (Vector((1, 0, 0)), Vector((0, -math.cos(math.radians(deg)), math.sin(math.radians(deg)))))
    def peg(x, m):
        y = y_at(x); cbox((x - 0.014, y - 0.07, z - 0.014), (x + 0.014, y + 0.03, z + 0.014), m)
    # polka-dot bloomers (frilly legs), hung by the waistband
    bx = 68.55; by = y_at(bx + 0.45) - 0.01
    U, V = tilt(6)
    bl = [(0.0, 0.0), (0.9, 0.0), (0.92, 0.25), (0.96, 0.62), (0.58, 0.66), (0.45, 0.36), (0.32, 0.66), (-0.06, 0.62), (-0.02, 0.25)]
    flat(bl, (bx, by, z + 0.02), U, V, 'cpolka', uvs=0.42)
    for (fx, fw) in ((-0.07, 0.4), (0.57, 0.4)):  # the frills
        flat([(0, 0), (fw, 0), (fw + 0.03, 0.07), (-0.03, 0.07)], Vector((bx, by, z + 0.02)) + U * fx + V * (0.6 + (0.02 if fx > 0 else 0.0)), U, V, 'cringw', th=0.016)
    peg(bx + 0.06, 'cpeg'); peg(bx + 0.84, 'cpeg2')
    # a cyan T-shirt with a pink heart on it
    tx = 69.75; ty = y_at(tx + 0.4) - 0.02
    U, V = tilt(-4)
    sh = [(0.0, 0.0), (0.26, 0.04), (0.54, 0.04), (0.8, 0.0), (0.98, 0.26), (0.84, 0.36), (0.68, 0.22), (0.66, 0.8), (0.14, 0.8), (0.12, 0.22), (-0.04, 0.36), (-0.18, 0.26)]
    flat(sh, (tx, ty, z - 0.02), U, V, 'cshirt', uvs=1.0)
    hc = Vector((tx, ty, z - 0.02)) + U * 0.4 + V * 0.36
    N = U.cross(V).normalized()
    heart = [(0.0, 0.0), (0.07, 0.06), (0.1, 0.11), (0.06, 0.15), (0.0, 0.12), (-0.06, 0.15), (-0.1, 0.11), (-0.07, 0.06)]
    flat([(x, 0.15 - y) for (x, y) in heart], hc, U, V, 'cheart', th=0.022)  # (through it: it shows both sides)
    peg(tx + 0.02, 'cpeg2'); peg(tx + 0.78, 'cpeg')
    # ONE huge sock (where's the other one), striped, hung by its cuff, its foot kicked out sideways
    sx = 71.15; sy = y_at(sx + 0.2) - 0.01
    U, V = tilt(3)
    so = [(0.0, 0.0), (0.42, 0.0), (0.44, 1.05), (0.47, 1.22), (1.1, 1.24), (1.18, 1.32), (1.16, 1.48), (1.0, 1.56), (0.22, 1.58), (0.06, 1.48), (-0.02, 1.22), (0.0, 1.0)]
    flat(so, (sx, sy, z + 0.01), U, V, 'cstripe', th=0.03, uvf=lambda u, v: (0.12 + 0.72 * min(1.0, v / 1.6), u))
    flat([(0.0, -0.01), (0.46, -0.01), (0.46, 0.14), (0.0, 0.14)], Vector((sx - 0.02, sy, z + 0.01)), U, V, 'cringw', th=0.05)  # its cuff
    peg(sx + 0.05, 'cpeg'); peg(sx + 0.38, 'cpeg2')
    # a striped towel folded over the line
    wx = 72.65; wy = y_at(wx + 0.35)
    for s in (-1, 1):
        a = Vector((wx, wy + 0.01, z)); P0 = a + Vector((0, 0, s * 0.012))
        flat([(0.0, 0.0), (0.68, 0.0), (0.68, 0.62 if s > 0 else 0.48), (0.0, 0.62 if s > 0 else 0.48)], P0, Vector((1, 0, 0)), Vector((0, -1, s * 0.06)).normalized(), 'cstripe', th=0.012,
             uvf=lambda u, v: (0.12 + 0.76 * u / 0.68, v))
    peg(wx + 0.1, 'cpeg'); peg(wx + 0.58, 'cpeg2')


# ------------------------------------------------------------ inside
def inside():
    rr = K.rng
    # the floorboards, the rug, the ceiling and its beams
    Q([(IX0, 0.05, IZ0), (IX0, 0.05, IZ1), (IX1, 0.05, IZ1), (IX1, 0.05, IZ0)], 'cfloor', out=(0, 1, 0))
    Q([(IX0, WH, IZ0), (IX1, WH, IZ0), (IX1, WH, IZ1), (IX0, WH, IZ1)], 'csoffit', out=(0, -1, 0))
    for x in (69.9, 72.1): cbox((x - 0.08, WH - 0.18, IZ0), (x + 0.08, WH, IZ1), 'cbeam', bev=0.015, skip=('py', 'nz', 'pz'))
    lathe((71.0, 0.05, 9.15), [(1.0, 0.0), (0.96, 0.014), (0.0, 0.014)], 'crug', n=12, scale=(1.0, 0.64))  # (lying on the boards)
    # the bed (its box: 72.6..74.1, 0..0.55, 9.6..11.2): a pink iron bedstead, the mattress, the quilt, a pillow
    bed = next(b for b in K.boxes if b['mat'] == 'bedsheet'); (x0, _, z0), (x1, yt, z1) = bed['min'], bed['max']
    for (x, z, h) in ((x0 + 0.04, z1 - 0.04, 1.08), (x1 - 0.04, z1 - 0.04, 1.08), (x0 + 0.04, z0 + 0.04, 0.8), (x1 - 0.04, z0 + 0.04, 0.8)):
        pole((x, 0, z), (x, h, z), 0.028, 'cbed', n=5, caps=(False, False))
        lathe((x, h, z), [(0.028, 0.0), (0.05, 0.035), (0.0, 0.08)], 'cbrass', n=5)
    for (z, ys) in ((z1 - 0.04, (0.62, 0.98)), (z0 + 0.04, (0.62, 0.72))):
        for y in ys: pole((x0 + 0.04, y, z), (x1 - 0.04, y, z), 0.02, 'cbed', n=4, caps=(False, False))
        for k in range(1, 3):
            xx = x0 + 0.04 + k * (x1 - x0 - 0.08) / 3
            pole((xx, ys[0], z), (xx, ys[1], z), 0.012, 'cbed', n=4, caps=(False, False))
    for x in (x0 + 0.04, x1 - 0.04): pole((x, 0.28, z0 + 0.04), (x, 0.28, z1 - 0.04), 0.022, 'cbed', n=4, caps=(False, False))
    cbox((x0 + 0.06, 0.3, z0 + 0.08), (x1 - 0.06, yt - 0.03, z1 - 0.08), 'csheet', bev=0.04)
    # the quilt over the foot two thirds, hanging down the open sides
    qz = z0 + 1.02
    cbox((x0 + 0.02, yt - 0.04, z0 + 0.03), (x1 - 0.02, yt + 0.02, qz), 'cquilt', bev=0.02)
    cbox((x0 + 0.02, 0.24, z0 + 0.03), (x0 + 0.06, yt - 0.04, qz), 'cquilt', skip=('py', 'px'))
    lathe((72.95 + 0.4, yt + 0.02, z1 - 0.32), [(0.0, -0.02), (0.38, 0.05), (0.28, 0.13), (0.0, 0.14)], 'csheet', n=6, scale=(1.0, 0.45), rot=0.0)  # the pillow
    # the table (its box: 69.4..70.8, 0..0.8, 7..8.2): a top, legs, a teapot, a mug, the keeper's telescope
    tb = next(b for b in K.boxes if b['mat'] == 'wood'); (x0, _, z0), (x1, yt, z1) = tb['min'], tb['max']
    cbox((x0, yt - 0.06, z0), (x1, yt, z1), 'cwood', bev=0.015)
    for (x, z) in ((x0 + 0.08, z0 + 0.08), (x1 - 0.08, z0 + 0.08), (x0 + 0.08, z1 - 0.08), (x1 - 0.08, z1 - 0.08)):
        cbox((x - 0.035, 0, z - 0.035), (x + 0.035, yt - 0.06, z + 0.035), 'cwood', skip=('py',))
    cbox((x0 + 0.06, yt - 0.16, z0 + 0.06), (x1 - 0.06, yt - 0.06, z0 + 0.09), 'cwood')  # an apron rail
    tp = Vector((x0 + 0.42, yt, z0 + 0.55))
    lathe(tp, [(0.09, 0.0), (0.12, 0.08), (0.08, 0.17), (0.0, 0.22)], 'ctea', n=6)
    pole(tp + Vector((0.09, 0.08, 0)), tp + Vector((0.2, 0.17, 0)), 0.018, 'ctea', n=4, r1=0.012)  # its spout
    pole(tp + Vector((-0.1, 0.15, 0)), tp + Vector((-0.17, 0.1, 0)), 0.014, 'ctea', n=3); pole(tp + Vector((-0.17, 0.1, 0)), tp + Vector((-0.1, 0.04, 0)), 0.014, 'ctea', n=3)  # its handle
    lathe((x0 + 0.85, yt, z0 + 0.4), [(0.0, 0.0), (0.045, 0.0), (0.045, 0.1), (0.0, 0.1)], 'cmug', n=7)
    pole((x0 + 0.62, yt + 0.045, z0 + 0.95), (x1 - 0.1, yt + 0.06, z0 + 0.82), 0.045, 'cbrass', n=7, r1=0.035)  # the telescope
    # the stove under the chimney: a pot-belly, its door glowing, a pipe up to the ceiling
    s = Vector((68.3, 0.05, 10.8))  # (in the corner, out of the way of the door)
    lathe(s, [(0.2, 0.0), (0.27, 0.36), (0.22, 0.64), (0.08, 0.76)], 'cstove', n=7, rot=0.2)
    Q([s + Vector((0.225, 0.22, -0.1)), s + Vector((0.225, 0.22, 0.1)), s + Vector((0.225, 0.42, 0.1)), s + Vector((0.225, 0.42, -0.1))], 'cfire', out=(1, 0, 0))  # (into the belly a touch)
    pole(s + Vector((0, 0.74, 0)), (s.x, WH, s.z), 0.075, 'cstove', n=6, caps=(False, False))


# ------------------------------------------------------------ build
_bake = archkit.bake_ao
LIGHT_AO = {'cwash', 'cchim', 'cplinth', 'cband'}  # (whitewash in the shade went grey: half the AO on the outside paint, so it reads white)


def bake_ao(objs, solids, **kw):
    _bake(objs, solids, **kw)
    for ob in objs:
        if ob.data.materials and ob.data.materials[0].name in LIGHT_AO and ob.data.color_attributes:
            for d in ob.data.color_attributes[0].data: a = 0.5 + 0.5 * d.color[0]; d.color = (a, a, a, 1)


archkit.bake_ao = bake_ao


def build(kind):
    global K
    d = json.load(open(os.path.join(HERE, 'boxes', kind + '.json')))
    K = Kit(d, seed=71)
    K.ground = 0.0
    K.solids = [(b['min'], b['max']) for b in d['boxes']]
    def tris(): return sum(2 if len(f) == 4 else 1 for g in K.geo.values() for f in g['f'])
    stats = []; mark = lambda name: stats.append((name, tris()))
    walls(); mark('walls, windows'); door(); mark('door'); roof(); mark('roof, chimney, gutters'); butt(); life_ring(); oars(); mark('water butt, life ring, oars')
    washing(); mark('washing line'); inside(); mark('inside')
    if os.environ.get('CT_MATS'): print('tris by material:', sorted(((sum(2 if len(f) == 4 else 1 for f in g['f']), m) for (m, _), g in K.geo.items()), reverse=True))
    print('tris by piece:', ', '.join(f'{n} {t - (stats[i - 1][1] if i else 0)}' for i, (n, t) in enumerate(stats)), '| all', stats[-1][1])
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in ('cottage', 'cottage_sd')] or ['cottage', 'cottage_sd']):
    build(kind)
