# The architecture kit: builds a Blender building over a map's own collision boxes (tools/arch/dump.mjs writes them, in
# the building's local frame) so every wall, floor, step and roof sits exactly where the physics has it, then dresses
# it: trims and frames round every opening the walls have, sills, broken panes, doors swung open, skirting, fascia,
# corner boards, drainpipes, real stairs (treads, risers, stringers, balusters, a handrail), grime and signs from the
# decal atlas, vertex AO. Visual only: the game keeps the boxes for collisions.
# Everything is built as quads in game space (x, y up, z; local -z is the front) and goes into one mesh per material, so
# a building is ~15 draw calls however many pieces it has. Texture UVs are world-scale (like the game's boxes), so the
# shared 64 px kit tiles line up across pieces.
# use from a make_<building>.py: K = Kit(boxes_json); ...; K.finish(out_glb)
import os, sys, json, math, random
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
KITDIR = os.path.join(ROOT, 'public', 'models', 'arch', 'kit')
OUTDIR = os.path.join(ROOT, 'public', 'models', 'arch')
KIT = json.load(open(os.path.join(KITDIR, 'kit.json')))

# material name -> (kit texture, colour factor, extra). names ending in a paint slot ('@siding', '@roof', '@trim') are
# repainted per placement by the game (public/js/archfield.js): their factor is white here and the paint goes on top
MATS = {
    'siding@siding': ('siding', '#ffffff', {}), 'shingle@roof': ('shingle', '#ffffff', {}), 'shutter@roof': ('trim', '#ffffff', {}),
    'trim': ('trim', '#f2ecd8', {}), 'trimdark': ('trim', '#4a3f38', {}), 'wallint': ('stucco', '#d9cf9a', {}), 'wallint2': ('stucco', '#a9c4b0', {}),
    'ceiling': ('stucco', '#eae4cc', {}), 'floorwood': ('planks', '#ffffff', {}), 'brick': ('brick', '#ffffff', {}), 'brickpaint': ('brick', '#ffffff', {}),
    'concrete': ('concrete', '#ffffff', {}), 'tar': ('tar', '#ffffff', {}), 'glass': ('glass', '#ffffff', {}), 'metal': ('metalplate', '#a7aaa6', {}),
    'metaldark': ('metalplate', '#4b4e52', {}), 'lino': ('lino', '#ffffff', {}), 'carpet': ('carpet', '#ffffff', {}), 'stucco': ('stucco', '#ffffff', {}),
    'corrugated': ('corrugated', '#ffffff', {}), 'decal': ('decals', '#ffffff', {'alpha': True}), 'decalglow': ('decals', '#ffffff', {'alpha': True, 'glow': True}),
    'fac_tenement': ('fac_tenement', '#ffffff', {}), 'fac_office': ('fac_office', '#ffffff', {}), 'picket@trim': ('picket', '#ffffff', {'alpha': True}), 'louvre@roof': ('louvre', '#ffffff', {}), 'door': ('planks', '#c86a8a', {}),
    'brass': ('metalplate', '#d8b040', {}), 'rubber': ('tar', '#55504a', {}),
}


# small detail (frames, trims, signs, glass, louvres, rails): drawn, but no sun shadow (the shadow pass is the expensive one)
NOCAST = {'trim', 'trimdark', 'decal', 'decalglow', 'glass', 'shutter', 'louvre', 'brass', 'rubber', 'metal', 'metaldark', 'door'}


def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def B(x, y, z): return (x, -z, y)  # game (y up) -> blender (z up)


class Kit:
    def __init__(self, boxes_json, seed=1):
        d = json.load(open(boxes_json)) if isinstance(boxes_json, str) else boxes_json
        self.boxes = d['boxes']
        self.places = d.get('places', [])
        self.name = d['id']
        self.rng = random.Random(seed)
        self.geo = {}  # material -> {'v': [], 'f': [], 'uv': [], 'node': name}
        self.solids = [(b['min'], b['max']) for b in self.boxes]  # what's really there (face culling, AO)
        self.extra_occ = []  # more occluders for AO (visual solids)
        self.ground = 0.0  # local y of the ground (faces down onto it are dropped)
        self.inside = []  # interior volumes [(min, max)]: a face whose front is in one is an inside face

    # ------------------------------------------------------------ low level: quads into the per-material buckets
    def _bucket(self, mat, node=''):
        k = (mat, node)
        if k not in self.geo: self.geo[k] = {'v': [], 'f': [], 'uv': []}
        return self.geo[k]

    def quad(self, p, mat, uv=None, tile=None, sub=None, node='', flip=False):
        """p: 4 corners (game space, counter-clockwise seen from the front). uv: 4 uvs, or None = world-scale planar.
        sub: split into cells no bigger than this (metres) so the vertex AO has somewhere to live"""
        p = [Vector(q) for q in p]
        if flip: p = p[::-1]; uv = uv[::-1] if uv else None
        n = (p[1] - p[0]).cross(p[2] - p[0])
        if n.length < 1e-9: return
        n.normalize()
        tex = MATS[mat][0]
        t = tile or (KIT[tex]['tile'] or 1.0)
        def wuv(q):
            ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
            if ax > 0.5 and ax >= az: return (q.z / t, q.y / t) if n.x < 0 else (-q.z / t, q.y / t)
            if ay > 0.5: return (q.x / t, -q.z / t)
            return (q.x / t, q.y / t) if n.z > 0 else (-q.x / t, q.y / t)
        nu = nv = 1
        if sub:  # (a thin face, a wall's top or a jamb, gets no cuts: its AO hardly changes across it)
            lu, lv = (p[1] - p[0]).length, (p[3] - p[0]).length
            if min(lu, lv) > 0.6: nu = max(1, math.ceil(lu / sub)); nv = max(1, math.ceil(lv / sub))
        g = self._bucket(mat, node)
        if abs(abs(n.x) + abs(n.y) + abs(n.z) - 1) < 1e-6:  # axis-aligned: remember it for the z-fight check
            ax = 0 if abs(n.x) > 0.5 else 1 if abs(n.y) > 0.5 else 2
            o = [i for i in range(3) if i != ax]
            r = (min(q[o[0]] for q in p), min(q[o[1]] for q in p), max(q[o[0]] for q in p), max(q[o[1]] for q in p))
            self.__dict__.setdefault('_planes', {}).setdefault((ax, round(p[0][ax], 4), n[ax] > 0), []).append((r, mat, tuple(round(v, 3) for v in p[0])))
        base = len(g['v'])
        for j in range(nv + 1):
            for i in range(nu + 1):
                s, tt = i / nu, j / nv
                q = p[0].lerp(p[1], s).lerp(p[3].lerp(p[2], s), tt)
                g['v'].append(tuple(q))
                if uv:
                    a = Vector(uv[0]).lerp(Vector(uv[1]), s).lerp(Vector(uv[3]).lerp(Vector(uv[2]), s), tt)
                    g['uv'].append((a.x, a.y))
                else: g['uv'].append(wuv(q))
        for j in range(nv):
            for i in range(nu):
                a = base + j * (nu + 1) + i
                g['f'].append((a, a + 1, a + nu + 2, a + nu + 1))

    def tri(self, p, mat, node=''):
        g = self._bucket(mat, node); b = len(g['v'])
        n = (Vector(p[1]) - Vector(p[0])).cross(Vector(p[2]) - Vector(p[0]))
        t = KIT[MATS[mat][0]]['tile'] or 1.0
        nn = n.normalized() if n.length > 1e-12 else n
        if n.length > 1e-12 and abs(abs(nn.x) + abs(nn.y) + abs(nn.z) - 1) < 1e-6:
            ax = 0 if abs(nn.x) > 0.5 else 1 if abs(nn.y) > 0.5 else 2
            o = [i for i in range(3) if i != ax]
            r = (min(q[o[0]] for q in p), min(q[o[1]] for q in p), max(q[o[0]] for q in p), max(q[o[1]] for q in p))
            self.__dict__.setdefault('_planes', {}).setdefault((ax, round(p[0][ax], 4), nn[ax] > 0), []).append((r, mat + '(tri)', tuple(round(v, 3) for v in p[0])))
        for q in p:
            g['v'].append(tuple(q)); g['uv'].append((q[0] / t, q[2] / t) if abs(nn.y) > 0.7 else (q[0] / t + q[2] / t * 0.5, q[1] / t))  # (a flat cap: mapped from above, or its uvs have no area)
        g['f'].append((b, b + 1, b + 2))

    # a box. faces: dict face -> material ('px','nx','py','ny','pz','nz', or 'side' / 'top' / 'bottom' / 'all'), None = skip.
    # cull: skip a face that's flush against a real solid (it can't be seen)
    def box(self, mn, mx, mats, sub=None, cull=True, node='', tile=None):
        x0, y0, z0 = mn; x1, y1, z1 = mx
        if x1 - x0 < 1e-4 or y1 - y0 < 1e-4 or z1 - z0 < 1e-4: return
        get = lambda f: mats.get(f, mats.get('top' if f == 'py' else 'bottom' if f == 'ny' else 'side', mats.get('all')))
        F = {
            'px': [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], 'nx': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
            'py': [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)], 'ny': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            'pz': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], 'nz': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
        }
        for f, q in F.items():
            m = get(f)
            if callable(m): m = m(f, q)
            if not m: continue
            if f == 'ny' and y0 <= self.ground + 1e-3: continue  # resting on the ground: never seen
            if cull and self.hidden(f, q): continue
            self.quad(q, m, sub=sub, node=node, tile=tile)

    def hidden(self, f, q):
        """is this face flush against a solid box (inside a wall, on the floor under another box)?"""
        nrm = {'px': (1, 0, 0), 'nx': (-1, 0, 0), 'py': (0, 1, 0), 'ny': (0, -1, 0), 'pz': (0, 0, 1), 'nz': (0, 0, -1)}[f]
        c = [sum(v[i] for v in q) / 4 for i in range(3)]
        pts = [c] + [[c[i] * 0.15 + v[i] * 0.85 for i in range(3)] for v in q]
        for pt in pts:
            pt = [pt[i] + nrm[i] * 0.004 for i in range(3)]
            if not any(all(mn[i] - 1e-4 <= pt[i] <= mx[i] + 1e-4 for i in range(3)) for mn, mx in self.solids): return False
        return True

    def is_inside(self, pt):
        return any(all(mn[i] <= pt[i] <= mx[i] for i in range(3)) for mn, mx in self.inside)

    # ------------------------------------------------------------ reading the boxes
    def take(self, pred):
        """boxes matching pred, removed from the to-do list (whatever is left at the end is drawn plain)"""
        out = [b for b in self.boxes if pred(b) and not b.get('_done')]
        for b in out: b['_done'] = True
        return out

    def walls(self, boxes, tmax=0.36):
        """group thin upright boxes into wall planes: (axis, centre, thickness, [boxes]). axis 'x' = runs along x"""
        planes = {}
        for b in boxes:
            sx, sy, sz = (b['max'][i] - b['min'][i] for i in range(3))
            if sz <= tmax and sx > sz: k = ('x', round((b['min'][2] + b['max'][2]) / 2, 3), round(sz, 3), b['mat'])
            elif sx <= tmax and sz > sx: k = ('z', round((b['min'][0] + b['max'][0]) / 2, 3), round(sx, 3), b['mat'])
            else: continue
            planes.setdefault(k, []).append(b)
        # (the material is in the key: the garage's brick front is in line with the house's siding one)
        return {k[:3] + (i,): v for i, (k, v) in enumerate(planes.items())}

    @staticmethod
    def openings(axis, bs):
        """the holes in one wall plane: rectangles (a0, a1, y0, y1) with wall on the left, right and top (doors: and
        nothing below). a = along the wall"""
        ia = 0 if axis == 'x' else 2
        rects = [(b['min'][ia], b['max'][ia], b['min'][1], b['max'][1]) for b in bs]
        A = sorted(set(v for r in rects for v in r[:2])); Y = sorted(set(v for r in rects for v in r[2:]))
        cov = lambda a, y: any(r[0] - 1e-4 <= a <= r[1] + 1e-4 and r[2] - 1e-4 <= y <= r[3] + 1e-4 for r in rects)
        holes = set()
        for i in range(len(A) - 1):
            for j in range(len(Y) - 1):
                if not cov((A[i] + A[i + 1]) / 2, (Y[j] + Y[j + 1]) / 2): holes.add((i, j))
        out, seen = [], set()
        for h in sorted(holes):
            if h in seen: continue
            stack, comp = [h], []
            while stack:
                c = stack.pop()
                if c in seen or c not in holes: continue
                seen.add(c); comp.append(c)
                i, j = c; stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
            i0 = min(c[0] for c in comp); i1 = max(c[0] for c in comp) + 1; j0 = min(c[1] for c in comp); j1 = max(c[1] for c in comp) + 1
            a0, a1, y0, y1 = A[i0], A[i1], Y[j0], Y[j1]
            if i0 == 0 or i1 == len(A) - 1 or j1 == len(Y) - 1: continue  # open to the side or the top: not a hole
            out.append((a0, a1, y0, y1, j0 == 0))
        return out

    def stair_runs(self, boxes):
        """solid stairs (shared/map.js stairs()): boxes with the same cross-section, one after another along x or z, all
        from the same floor, each a step higher. returns [(boxes in order low->high, axis, dir)]"""
        groups = {}
        for b in boxes:
            for ax, cross in (('z', 0), ('x', 2)):
                k = (ax, round(b['min'][cross], 3), round(b['max'][cross], 3), round(b['min'][1], 3))
                groups.setdefault(k, []).append(b)
        runs, used = [], set()
        for (ax, c0, c1, y0), bs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            ia = 2 if ax == 'z' else 0
            bs = [b for b in bs if id(b) not in used]
            bs.sort(key=lambda b: b['min'][ia])
            seq = []
            for b in bs:
                if seq and abs(b['min'][ia] - seq[-1]['max'][ia]) < 1e-3 and abs((b['max'][1] - seq[-1]['max'][1])) > 0.05: seq.append(b)
                else:
                    if len(seq) >= 3: break
                    seq = [b]
            if len(seq) >= 3:
                up = seq[-1]['max'][1] > seq[0]['max'][1]
                if not up: seq = seq[::-1]
                for b in seq: used.add(id(b))
                runs.append((seq, ax, 1 if up else -1))
        return runs

    # ------------------------------------------------------------ the dressing
    def wall_plane(self, axis, c, t, bs, ext, intm, trim='trim', sub=1.0, frames=True, sill=True, shards=True, skirt=None, doors=True):
        """draw a wall plane: its boxes (outside faces in ext, inside in intm, chosen per face by the interior volumes),
        then dress every opening. ext/intm may be the same"""
        ia = 0 if axis == 'x' else 2
        def pick(f, q):
            c3 = [sum(v[i] for v in q) / 4 for i in range(3)]
            nrm = {'px': (1, 0, 0), 'nx': (-1, 0, 0), 'py': (0, 1, 0), 'ny': (0, -1, 0), 'pz': (0, 0, 1), 'nz': (0, 0, -1)}[f]
            if f in ('py', 'ny'): return trim if f == 'py' else trim
            front = [c3[i] + nrm[i] * 0.06 for i in range(3)]
            along = (axis == 'x' and f in ('px', 'nx')) or (axis == 'z' and f in ('pz', 'nz'))
            if along: return trim  # the cut ends (window jambs, the wall's end)
            return intm if self.is_inside(front) else ext
        for b in bs: self.box(b['min'], b['max'], {'all': pick}, sub=sub)
        ops = self.openings(axis, bs)
        for a0, a1, y0, y1, door in ops:
            self.dress_opening(axis, c, t, a0, a1, y0, y1, door, trim, frames, sill, shards, doors)
        return ops

    def _P(self, axis, c, a, y, o):
        """a point on a wall: along a, height y, o metres off its centre plane (+ = toward +z / +x)"""
        return (a, y, c + o) if axis == 'x' else (c + o, y, a)

    def wbox(self, axis, c, a0, a1, y0, y1, o0, o1, mats, sub=None, cull=True):
        p, q = self._P(axis, c, a0, y0, o0), self._P(axis, c, a1, y1, o1)
        self.box([min(p[i], q[i]) for i in range(3)], [max(p[i], q[i]) for i in range(3)], mats, sub=sub, cull=cull)

    def outward(self, axis, c, a0, a1, y0, y1, t):
        """which side of the wall is outside: +1 / -1 (or 0 both inside / both outside)"""
        am, ym = (a0 + a1) / 2, (y0 + y1) / 2
        pi = self.is_inside(self._P(axis, c, am, ym, t / 2 + 0.3)); ni = self.is_inside(self._P(axis, c, am, ym, -t / 2 - 0.3))
        return 0 if pi == ni else (-1 if pi else 1)

    def dress_opening(self, axis, c, t, a0, a1, y0, y1, door, trim, frames, sill, shards, doors):
        r = self.rng
        side = self.outward(axis, c, a0, a1, y0, y1, t)
        sides = [side] if side else [1, -1]
        cw, cd = 0.09, 0.035  # casing width, how proud
        for s in ([1, -1] if side else [1, -1]):
            o0, o1 = (t / 2, t / 2 + cd) if s > 0 else (-t / 2 - cd, -t / 2)
            if frames:
                self.wbox(axis, c, a0 - cw, a0, y0 if door else y0 - 0.02, y1 + cw, o0, o1, {'all': trim})
                self.wbox(axis, c, a1, a1 + cw, y0 if door else y0 - 0.02, y1 + cw, o0, o1, {'all': trim})
                self.wbox(axis, c, a0 - cw - 0.02, a1 + cw + 0.02, y1, y1 + cw + 0.03, o0 - (0.02 if s < 0 else 0), o1 + (0.02 if s > 0 else 0), {'all': trim})
            if not door and sill and s == (side or 1):  # the sill sticks out under the window, outside
                so0, so1 = (t / 2, t / 2 + 0.09) if s > 0 else (-t / 2 - 0.09, -t / 2)
                self.wbox(axis, c, a0 - cw - 0.04, a1 + cw + 0.04, y0 - 0.05, y0, so0, so1, {'all': trim})
                if r.random() < 0.5: self.decal_on(axis, c, s, t / 2 + 0.006, (a0 + a1) / 2, y0 - 0.06, 'grime_run', w=(a1 - a0) * 0.9, h=min(1.0, y0 - 0.1), anchor='top')
        if not door and shards:  # broken panes: shards left in the corners of the frame (the hole stays a hole)
            for (ca, cy, da, dy) in ((a0, y0, 1, 1), (a1, y0, -1, 1), (a0, y1, 1, -1), (a1, y1, -1, -1)):
                if r.random() < 0.55:
                    L1, L2 = 0.12 + r.random() * 0.22, 0.1 + r.random() * 0.25
                    o = 0.0
                    pA = self._P(axis, c, ca, cy, o); pB = self._P(axis, c, ca + da * L1, cy, o); pC = self._P(axis, c, ca, cy + dy * L2, o)
                    self.tri([pA, pB, pC], 'glass'); self.tri([pA, pC, pB], 'glass')
        if door and doors and t >= 0.15:  # a door leaf, swung open against the inside of the wall
            w = a1 - a0
            leaves = [(a0, 1)] if w < 1.3 else [(a0, 1), (a1, -1)]
            lw = w / len(leaves)
            s_in = -side if side else 1
            for hinge, d in leaves:
                o = s_in * (t / 2 + 0.02)
                # the leaf stands out from the wall at 100 degrees: mostly flat against it, a hair open
                for k in range(1):
                    p0 = self._P(axis, c, hinge, y0 + 0.02, o); far = self._P(axis, c, hinge - d * lw * 0.98, y0 + 0.02, o + s_in * 0.12)
                    self.slab_between(p0, far, min(2.2, y1 - y0 - 0.06), 0.045, 'door')

    def slab_between(self, p0, p1, h, th, mat):
        """a thin upright slab from p0 to p1 (bottoms), h tall, th thick: doors, signs"""
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0; d.y = 0; L = d.length
        if L < 1e-4: return
        d.normalize(); n = Vector((-d.z, 0, d.x)) * (th / 2); up = Vector((0, h, 0))
        a, b2 = p0 + n, p1 + n; c2, e = p1 - n, p0 - n
        self.quad([a, b2, b2 + up, a + up], mat); self.quad([c2, e, e + up, c2 + up], mat)
        self.quad([e, a, a + up, e + up], mat); self.quad([b2, c2, c2 + up, b2 + up], mat)
        self.quad([a + up, b2 + up, c2 + up, e + up], mat)

    def decal_on(self, axis, c, s, off, a, y, cell, w=1.0, h=1.0, anchor='centre', glow=False):
        """a decal from the atlas on a wall face: s = which side (+1/-1), off = distance from the wall's centre plane"""
        u0, v0, du, dv = KIT['decals']['cells'][cell]
        v0 = 1 - v0 - dv  # atlas rows count from the top, uv from the bottom
        self._nd = getattr(self, '_nd', 0) + 1; off += 0.0015 * (self._nd % 6)  # stacked decals never share a plane
        ya, yb = (y - h, y) if anchor == 'top' else (y - h / 2, y + h / 2) if anchor == 'centre' else (y, y + h)
        aa, ab = a - w / 2, a + w / 2
        if (axis == 'x' and s > 0) or (axis == 'z' and s < 0): pts = [(aa, ya), (ab, ya), (ab, yb), (aa, yb)]
        else: pts = [(ab, ya), (aa, ya), (aa, yb), (ab, yb)]
        P = [self._P(axis, c, p[0], p[1], s * off) for p in pts]
        uv = [(u0, v0), (u0 + du, v0), (u0 + du, v0 + dv), (u0, v0 + dv)]
        self.quad(P, 'decalglow' if glow else 'decal', uv=uv)

    def decal_floor(self, x0, z0, x1, z1, y, cell, glow=False):
        u0, v0, du, dv = KIT['decals']['cells'][cell]; v0 = 1 - v0 - dv
        self.quad([(x0, y, z1), (x1, y, z1), (x1, y, z0), (x0, y, z0)], 'decalglow' if glow else 'decal', uv=[(u0, v0), (u0 + du, v0), (u0 + du, v0 + dv), (u0, v0 + dv)])

    def stairs(self, seq, ax, d, tread='floorwood', riser='trim', stringer='trim', rail_side=None, rail='trim', balusters=True, nosing=0.03, node=''):
        """real stairs over a run of solid step boxes: a tread with a nosing on each, a riser, a closed stringer that
        follows the steps on the rail side (with the cupboard-ish panel under it), balusters and a sloped handrail.
        rail_side: +1 / -1 = which edge across the run (+x/+z side) gets the rail, None = both closed"""
        ia, ic = (2, 0) if ax == 'z' else (0, 2)
        c0, c1 = seq[0]['min'][ic], seq[0]['max'][ic]
        ybase = seq[0]['min'][1]
        def P(a, y, cc): return (cc, y, a) if ax == 'z' else (a, y, cc)
        prev_top = ybase
        noses = []
        for k, b in enumerate(seq):
            a0, a1 = (b['min'][ia], b['max'][ia]) if d > 0 else (b['max'][ia], b['min'][ia])
            top = b['max'][1]
            # tread: a slab on top, 4 cm thick, sticking out over the riser below by the nosing
            an = a0 - d * nosing
            lo, hi = (min(an, a1), max(an, a1))
            mn = [0, top - 0.04, 0]; mx = [0, top + 0.002, 0]
            mn[ia], mx[ia] = lo, hi; mn[ic], mx[ic] = c0, c1
            self.box(mn, mx, {'all': tread}, cull=False)
            # riser: the step's front face, set back under the nosing
            q = [P(a0, prev_top, c1), P(a0, prev_top, c0), P(a0, top - 0.04, c0), P(a0, top - 0.04, c1)]
            if (ax == 'x') == (d > 0): q = q[::-1]  # (face down the stairs)
            self.quad(q, riser)
            # the step's two sides (the panel under the stairs, the side by the wall): culled where something's flush
            smn = list(b['min']); smx = list(b['max']); smx[1] = top - 0.04
            self.box(smn, smx, {'px' if ax == 'z' else 'pz': stringer, 'nx' if ax == 'z' else 'nz': stringer}, sub=1.0)
            noses.append((an, top))
            prev_top = top
        # stringers: a sloped board along each side, from the floor at the bottom to the last step's top
        (aS, yS), (aE, yE) = noses[0], noses[-1]
        run = (aE - aS); rise = yE - yS
        for side in (-1, 1):
            cc = (c1 if side > 0 else c0)
            o0, o1 = (cc, cc + 0.05) if side > 0 else (cc - 0.05, cc)
            # the stringer: a parallelogram band 0.28 deep under the nosing line, 0.06 above it
            pts = [(aS - d * 0.15, ybase), (aE + d * 0.2, yE - 0.28 * 0 + 0.06), (aE + d * 0.2, yE - 0.32), (aS - d * 0.15, ybase)]
            for (oa, ob) in ((o0, o1),):
                A0 = P(aS - d * 0.05, ybase, oa); A1 = P(aE, yE + 0.06, oa); A2 = P(aE, yE - 0.3, oa)
                self.prism([P(aS - d * 0.05, ybase, 0), P(aS - d * 0.05, yS + 0.06, 0), P(aE, yE + 0.06, 0), P(aE, yE - 0.3, 0), P(aS + d * 0.6, ybase, 0)], ic, oa, ob, stringer, skip_y=ybase)
        if rail_side:
            cc = c1 if rail_side > 0 else c0
            o0 = cc - 0.06 if rail_side > 0 else cc + 0.02
            o1 = o0 + 0.04
            H = 0.9
            # newel posts at both ends, balusters every other step, the rail on top
            for (a, y) in (noses[0], noses[-1]):
                mn = [0, y - 0.03 if (a, y) != noses[0] else ybase, 0]; mx = [0, y + H + 0.12, 0]
                mn[ia], mx[ia] = a + d * 0.03 - 0.06, a + d * 0.03 + 0.06; mn[ic], mx[ic] = o0 - 0.04, o1 + 0.04
                self.box(mn, mx, {'all': rail}, cull=False)
            if balusters:
                for k, (a, y) in enumerate(noses[1:-1]):
                    mn = [0, y, 0]; mx = [0, y + H, 0]
                    mn[ia], mx[ia] = a + d * 0.2 - 0.018, a + d * 0.2 + 0.018; mn[ic], mx[ic] = o0, o1
                    self.box(mn, mx, {'all': rail}, cull=False)
            # handrail: a sloped bar along the nosing line + H
            self.bar([P(noses[0][0] + d * 0.03, noses[0][1] + H, (o0 + o1) / 2), P(noses[-1][0] + d * 0.03, noses[-1][1] + H, (o0 + o1) / 2)], 0.07, 0.05, 'trimdark')

    def prism(self, poly, axis_idx, o0, o1, mat, skip_y=None):
        """extrude a flat convex polygon (its across-coordinate ignored) between o0 and o1 across. one-sided, wound
        outward; sides lying on y = skip_y (a floor it stands on) are left out"""
        def at(p, o):
            q = list(p); q[axis_idx] = o; return Vector(q)
        n = len(poly)
        cen = sum((Vector(p) for p in poly), Vector()) / n; cen[axis_idx] = (o0 + o1) / 2
        def out(q):
            nn = (q[1] - q[0]).cross(q[2] - q[0])
            fc = sum(q, Vector()) / len(q)
            return q if nn.dot(fc - cen) > 0 else q[::-1]
        for k in range(1, n - 1):
            for o in (o0, o1): self.tri(out([at(poly[0], o), at(poly[k], o), at(poly[k + 1], o)]), mat)
        for k in range(n):
            a, b2 = poly[k], poly[(k + 1) % n]
            if skip_y is not None and abs(a[1] - skip_y) < 1e-4 and abs(b2[1] - skip_y) < 1e-4: continue
            q = out([at(a, o0), at(b2, o0), at(b2, o1), at(a, o1)])
            if (q[0] - q[1]).length < 1e-5 or (q[1] - q[2]).length < 1e-5: continue
            self.quad(q, mat)

    def bar(self, ends, w, h, mat):
        """a square bar between two points (any slope): handrails, pipes, wires"""
        a, b2 = Vector(ends[0]), Vector(ends[1])
        d = (b2 - a); L = d.length
        if L < 1e-4: return
        d.normalize()
        up = Vector((0, 1, 0)) if abs(d.y) < 0.95 else Vector((1, 0, 0))
        sx = d.cross(up).normalized() * (w / 2); sy = sx.cross(d).normalized() * (h / 2)
        c = [-sx - sy, sx - sy, sx + sy, -sx + sy]
        for k in range(4):
            p, q = c[k], c[(k + 1) % 4]
            self.quad([a + p, b2 + p, b2 + q, a + q], mat)
        self.quad([a + c[3], a + c[2], a + c[1], a + c[0]], mat); self.quad([b2 + c[0], b2 + c[1], b2 + c[2], b2 + c[3]], mat)

    # ------------------------------------------------------------ out
    def plain(self, b, mats, sub=1.0):
        self.box(b['min'], b['max'], mats, sub=sub)

    def zcheck(self, limit=12):
        """coplanar faces facing the same way that overlap (they'd flicker): printed, and counted"""
        bad = 0
        for k, lst in getattr(self, '_planes', {}).items():
            for i in range(len(lst)):
                for j in range(i + 1, len(lst)):
                    a, b = lst[i][0], lst[j][0]
                    ox = min(a[2], b[2]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[1], b[1])
                    if ox > 0.002 and oy > 0.002:
                        if 'decal' in lst[i][1] and 'decal' in lst[j][1]: continue
                        if lst[i][1] == lst[j][1] and 'fac_' not in lst[i][1]: continue  # same material, same world-scale UVs: the same pixels, nothing to flicker (bars meeting at a corner)
                        if '(tri)' in lst[i][1] and '(tri)' in lst[j][1]: continue  # (fan triangles of one cap: bboxes overlap, the tris don't)
                        ax, c, pos = k; o = [q for q in range(3) if q != ax]
                        pt = [0, 0, 0]; pt[ax] = c + (0.004 if pos else -0.004)
                        pt[o[0]] = (max(a[0], b[0]) + min(a[2], b[2])) / 2; pt[o[1]] = (max(a[1], b[1]) + min(a[3], b[3])) / 2
                        if any(all(mn[q] - 1e-4 <= pt[q] <= mx[q] + 1e-4 for q in range(3)) for mn, mx in self.solids): continue
                        bad += 1
                        if bad <= limit: print('ZFIGHT', 'xyz'[k[0]], k[1], lst[i][1], lst[i][2], '<->', lst[j][1], lst[j][2])
        print('zfight pairs:', bad)
        return bad

    def finish(self, out=None, ao=True, sheet=None, nodes_keep=()):
        """make the objects (one per material per node), bake vertex AO, export the glb"""
        self.zcheck()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mats = {}
        for (mname, node), g in self.geo.items():
            if mname not in mats: mats[mname] = make_material(mname)
        objs = []
        for (mname, node), g in sorted(self.geo.items()):
            if not g['f']: continue
            me = bpy.data.meshes.new(f'{node or "main"}_{mname}')
            me.from_pydata([B(*v) for v in g['v']], [], g['f'])
            uvl = me.uv_layers.new(name='UVMap')
            for poly in me.polygons:
                for li in poly.loop_indices:
                    uvl.data[li].uv = g['uv'][me.loops[li].vertex_index]
            me.materials.append(mats[mname])
            me.validate(); me.update()
            ob = bpy.data.objects.new(f'{node or "main"}|{mname}', me)
            bpy.context.scene.collection.objects.link(ob)
            ob['node'] = node
            objs.append(ob)
        # merge duplicate verts per object (the quads are made one by one) so it shades and stays small
        for ob in objs:
            bm = bmesh.new(); bm.from_mesh(ob.data)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
            bm.to_mesh(ob.data); bm.free()
        if ao: bake_ao(objs, self.solids + self.extra_occ)
        if out:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            export_glb(objs, out)
        return objs


def make_material(name):
    tex, col, ex = MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; bs = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    im = nt.nodes.new('ShaderNodeTexImage')
    path = os.path.join(KITDIR, tex + '.png')
    img = bpy.data.images.load(path, check_existing=True)
    im.image = img; im.interpolation = 'Closest'
    nt.links.new(im.outputs['Color'], bs.inputs['Base Color'])
    c = hexc(col)
    # the colour factor: a mix node (glTF exports base colour factor x texture when it's a multiply after the texture)
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
    mul.inputs[7].default_value = (*[v ** 2.2 for v in c], 1)
    nt.links.new(im.outputs['Color'], mul.inputs[6]); nt.links.new(mul.outputs[2], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 1.0; bs.inputs['Metallic'].default_value = 0.0
    if 'Specular IOR Level' in bs.inputs: bs.inputs['Specular IOR Level'].default_value = 0.0
    if ex.get('alpha'):
        nt.links.new(im.outputs['Alpha'], bs.inputs['Alpha'])
        try: m.blend_method = 'CLIP'
        except Exception: pass
        m.alpha_threshold = 0.5 if hasattr(m, 'alpha_threshold') else None
    if ex.get('glow'):
        nt.links.new(im.outputs['Color'], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = 1.0
    m['tex'] = tex; m['tile'] = KIT[tex]['tile']; m['col'] = col
    if KIT[tex].get('glow'): m['glowmap'] = KIT[tex]['glow']
    if ex.get('alpha'): m['alpha'] = 1
    if ex.get('glow'): m['glow'] = 1
    if ex.get('glowcol'): m['glowcol'] = ex['glowcol']  # (what colour it glows; white if unset)
    if '@' in name: m['paint'] = name.split('@')[1]
    if name.split('@')[0] in NOCAST: m['nocast'] = 1
    return m


def bake_ao(objs, solids, rays=24, dist=1.6, floor=0.38):
    """vertex AO by ray casting (no Cycles): every vertex fires rays over its hemisphere at everything in the building
    plus the collision boxes, darker the more that's close. written as COLOR_0 (the game multiplies it in), with a
    touch of grime: a bit darker low down near the ground"""
    import numpy as np
    dg = bpy.context.evaluated_depsgraph_get()
    vs, fs = [], []
    for ob in objs:
        if ob.data.materials and ob.data.materials[0].name.startswith('decal'): continue
        base = len(vs)
        vs += [ob.matrix_world @ v.co for v in ob.data.vertices]
        fs += [[base + i for i in p.vertices] for p in ob.data.polygons]
    for mn, mx in solids:  # the boxes themselves occlude too (they're what the visual mesh wraps)
        x0, y0, z0 = mn; x1, y1, z1 = mx
        base = len(vs)
        for (x, y, z) in [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]:
            vs.append(Vector(B(x, y, z)))
        fs += [[base + i for i in f] for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0))]
    bvh = BVHTree.FromPolygons(vs, fs, epsilon=0.0)
    rng = np.random.default_rng(5)
    # a fixed cosine-weighted hemisphere set
    u = rng.random((rays, 2)); r = np.sqrt(u[:, 0]); th = u[:, 1] * math.tau
    H = [Vector((r[i] * math.cos(th[i]), r[i] * math.sin(th[i]), math.sqrt(max(0, 1 - u[i, 0])))) for i in range(rays)]
    for ob in objs:
        me = ob.data
        attr = me.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
        is_decal = me.materials and me.materials[0].name.startswith('decal')
        me.calc_normals_split() if hasattr(me, 'calc_normals_split') else None
        nr = [v.normal.copy() for v in me.vertices]
        for i, v in enumerate(me.vertices):
            p = ob.matrix_world @ v.co
            n = nr[i]
            if n.length < 0.5: n = Vector((0, 0, 1))
            t = n.orthogonal().normalized(); bt = n.cross(t)
            hit = 0.0
            o = p + n * 0.012
            for h in H:
                d = t * h.x + bt * h.y + n * h.z
                loc, nn, idx, dd = bvh.ray_cast(o, d, dist)
                if loc is not None: hit += (1 - dd / dist) ** 0.7
            a = 1 - hit / rays * 1.25
            a = max(floor, min(1.0, a))
            gz = p.z  # blender z = game y
            if gz < 0.5: a *= 0.86 + 0.28 * max(0, gz)  # ground grime
            if is_decal: a = max(a, 0.75)
            attr.data[i].color = (a, a, a, 1)
        me.color_attributes.active_color = attr


def export_glb(objs, out):
    for o in bpy.context.scene.objects: o.select_set(o in objs)
    kw = dict(filepath=out, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
              export_texcoords=True, export_normals=True, export_materials='EXPORT', export_image_format='NONE', export_extras=True)
    try: bpy.ops.export_scene.gltf(**kw, export_vertex_color='ACTIVE', export_all_vertex_colors=False)
    except TypeError:
        try: bpy.ops.export_scene.gltf(**kw, export_colors=True)
        except TypeError: bpy.ops.export_scene.gltf(**kw)
    print('wrote', out, os.path.getsize(out) // 1024, 'KB')


# ------------------------------------------------------------ a whole shell() building (shared/map.js shell()), dressed
def dress_shell(K, w, d, floors, F, ext, intm='wallint', floor='floorwood', roof='tar', cap='metal', band='concrete', course='trim',
                corners=None, rail_side=1, wall_mat=None, sub=1.6):
    """everything shell() makes, in its local frame (footprint x +-w/2, z +-d/2, front door at -z): the stairs, the
    railings round the holes, the floors, the roof slab, the walls with their openings dressed, the parapet with a cap,
    a foundation band, a course at every floor, corner boards. wall_mat: the box material of the walls"""
    hw, hd, t = w / 2, d / 2, 0.3
    eq = lambda a, b: abs(a - b) < 1e-3
    K.inside.append(((-hw + t / 2, 0, -hd + t / 2), (hw - t / 2, floors * F, hd - t / 2)))
    inb = lambda b: b['min'][0] >= -hw - 0.16 and b['max'][0] <= hw + 0.16 and b['min'][2] >= -hd - 0.16 and b['max'][2] <= hd + 0.16
    steps = K.take(lambda b: inb(b) and b['max'][0] - b['min'][0] <= 1.51 and b['max'][2] - b['min'][2] <= 0.6 and b['max'][1] - b['min'][1] > 0.3 and b['mat'] != wall_mat)
    for seq, ax, dd in K.stair_runs(steps):
        K.stairs(seq, ax, dd, tread=floor, riser='trim', stringer='trim', rail_side=rail_side)
        for b in seq: b['_stair'] = True
    for b in steps:
        if not b.get('_stair'): K.plain(b, {'top': floor, 'side': 'trim'})
    for b in K.take(lambda b: inb(b) and b['max'][0] - b['min'][0] <= 0.11 and b['max'][1] - b['min'][1] > 0.9 and b['mat'] != wall_mat):
        K.plain(b, {'all': 'trim'})
        x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
        K.box((x0 - 0.03, y1, z0 - 0.03), (x1 + 0.03, y1 + 0.05, z1 + 0.03), {'all': 'trimdark'}, cull=False)
    top = floors * F
    for b in K.take(lambda b: inb(b) and b['max'][1] - b['min'][1] <= 0.31 and b['mat'] != wall_mat and (b['max'][0] - b['min'][0]) > 0.15 and (b['max'][2] - b['min'][2]) > 0.15):
        isroof = b['min'][1] >= top - 0.01
        K.plain(b, {'top': roof if isroof else floor, 'bottom': 'ceiling' if b['min'][1] > 0.05 else None, 'side': course}, sub=1.5)
    walls = K.take(lambda b: inb(b) and b['mat'] == wall_mat)
    for (axis, c, tt, _), bs in K.walls(walls).items():
        parapet = all(b['min'][1] >= top + 0.29 for b in bs)
        ops = K.wall_plane(axis, c, tt, bs, ext, intm, sub=sub, frames=not parapet)
        if parapet:
            for b in bs: globals()['cap'](K, b, cap)
            continue
        out = K.outward(axis, c, -0.5, 0.5, 1, 2, tt)
        if not out: continue
        ia = 0 if axis == 'x' else 2
        o0, o1 = (tt / 2, tt / 2 + 0.03) if out > 0 else (-tt / 2 - 0.03, -tt / 2)
        rows = [(0.0, 0.3, band)] + [(f * F - 0.02, f * F + 0.2, course) for f in range(1, floors)] + [(top - 0.05, top + 0.3, course)]
        bands(K, axis, c, bs, rows, o0, o1 + (0.01 if out > 0 else -0.01))
    cm = corners or course
    corner_boards(K, hw + t / 2, hd + t / 2, 0.3, top + 0.3, cm)


def cap(K, b, mat, h=0.06, o=0.04):
    """a coping cap on a wall box: wider than it across; along x it runs past the ends, along z it stops short of
    them, so where two walls meet at a corner the caps butt instead of overlapping (no flicker)"""
    x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
    if x1 - x0 >= z1 - z0: K.box((x0 - o, y1, z0 - o), (x1 + o, y1 + h, z1 + o), {'all': mat}, cull=False)
    else: K.box((x0 - o, y1, z0 + o), (x1 + o, y1 + h, z1 - o), {'all': mat}, cull=False)


def bands(K, axis, c, bs, rows, o0, o1):
    """horizontal bands on a wall face (foundation, floor courses, fascia): rows [(y0, y1, mat)], over every stretch
    of wall that covers that height, merged across the wall's pieces and stopping a hair short of openings (inside the
    frames there)"""
    ia = 0 if axis == 'x' else 2
    for (y0, y1, mat) in rows:
        segs = sorted((b['min'][ia], b['max'][ia]) for b in bs if b['min'][1] <= y0 + 0.01 and b['max'][1] >= y1 - 0.01)
        run = []
        for a0, a1 in segs:
            if run and a0 <= run[-1][1] + 1e-3: run[-1][1] = max(run[-1][1], a1)
            else: run.append([a0, a1])
        for a0, a1 in run: K.wbox(axis, c, a0 + 0.005, a1 - 0.005, y0, y1, o0, o1, {'all': mat})


def corner_boards(K, ex, ez, y0, y1, mat, w=0.16, p=0.04):
    """a board up each outside corner of a box ex / ez from its centre, standing p proud of both faces"""
    for sx in (-1, 1):
        for sz in (-1, 1):
            xa, xb = sorted((sx * (ex - w + p), sx * (ex + p))); za, zb = sorted((sz * (ez - w + p), sz * (ez + p)))
            K.box((xa, y0, za), (xb, y1, zb), {'all': mat}, cull=False)
