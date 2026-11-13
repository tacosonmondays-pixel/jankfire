# THE HEADLINER's kit (make_cast_jester_lord.py): a mesh builder that works in GAME coordinates (x his right, y up,
# -z his front) and gives every face a material and a colour per corner, and every vertex its joints' weights, so the
# whole spider-jester is a couple of skinned meshes (a few draw calls). Shapes: tubes on parallel-transport frames,
# harlequin lattice tubes (the diamonds follow the triangle edges, so they are crisp at any distance), ellipsoids with
# colour by region, sleigh bells, frills, flat-ish decals that sit on a curved surface. Blender 5.2 (blender52).
import bpy, bmesh, math, os, sys, json
import numpy as np
from mathutils import Vector, Matrix

MAT = {'satin': 0, 'lacquer': 1, 'skin': 2, 'brass': 3}
G2B = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # game -> blender


def lin(h):
    """0xRRGGBB (sRGB, the game's colours) -> linear rgb (vertex colours are linear in glTF)"""
    c = [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c)


def mixc(a, b, t): return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
def ss(a, b, x): t = max(0.0, min(1.0, (x - a) / (b - a))) if b != a else float(x >= a); return t * t * (3 - 2 * t)
def V(*a): return Vector(a if len(a) == 3 else a[0])


class Build:
    """one mesh in game coordinates: faces carry a material index and a corner colour, verts carry joint weights"""
    def __init__(self, name, q=1.0):
        self.name = name
        self.q = q                 # (under 1: the far model: fewer segments, no lattice, no small details)
        self.lod = q < 1.0
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.col = self.bm.loops.layers.float_color.new('tint')
        self.dl = self.bm.verts.layers.deform.verify()
        self.groups = []
        self.pieces = []

    def tally(self):
        t = {}
        for tag, n in self.pieces: t[tag] = t.get(tag, 0) + n
        return sorted(t.items(), key=lambda e: -e[1])

    def gi(self, j):
        if j not in self.groups: self.groups.append(j)
        return self.groups.index(j)

    def v(self, p, w):
        v = self.bm.verts.new(Vector(p))
        if isinstance(w, str): w = {w: 1.0}
        elif callable(w): w = w(Vector(p))
        d = v[self.dl]
        for j, x in w.items():
            if x > 1e-4: d[self.gi(j)] = x
        return v

    def f(self, vs, mat, col):
        try: fc = self.bm.faces.new(vs)
        except ValueError: return None
        fc.material_index = MAT[mat] if isinstance(mat, str) else mat
        for l in fc.loops:
            c = col(l.vert.co) if callable(col) else col
            l[self.col] = (c[0], c[1], c[2], 1.0)
        return fc

    def piece(self, faces, tag=''):
        """a closed piece is done: wind it outward"""
        faces = [x for x in faces if x is not None]
        if faces: bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        # every closed island of the piece must face out (a thin shell can fool the recalc): flip any that encloses
        # a negative volume
        left = set(faces)
        while left:
            f0 = left.pop(); isl = [f0]; st = [f0]
            while st:
                f_ = st.pop()
                for e in f_.edges:
                    for g in e.link_faces:
                        if g in left: left.discard(g); isl.append(g); st.append(g)
            vol = 0.0
            for fc in isl:
                vs = [v.co for v in fc.verts]
                for i in range(1, len(vs) - 1): vol += vs[0].dot(vs[i].cross(vs[i + 1]))
            closed = all(len(e.link_faces) == 2 for fc in isl for e in fc.edges)
            if closed and vol < 0:
                bmesh.ops.reverse_faces(self.bm, faces=isl); self.flipped = getattr(self, 'flipped', []) + [tag]
        self.pieces.append((tag, sum(len(x.verts) - 2 for x in faces)))
        self.piece_faces = getattr(self, 'piece_faces', []) + [(tag, faces)]
        return faces

    # ------------------------------------------------------------------------------------------ shapes
    def frames(self, pts, up=None):
        P = [Vector(p) for p in pts]; n = len(P)
        T = [(P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized() for i in range(n)]
        u = Vector(up) if up else Vector((0, 1, 0))
        if abs(T[0].dot(u)) > 0.95: u = Vector((1, 0, 0)) if abs(T[0].x) < 0.9 else Vector((0, 0, 1))
        N = (u - T[0] * T[0].dot(u)).normalized(); out = []
        for i in range(n):
            N = (N - T[i] * T[i].dot(N)).normalized(); B = T[i].cross(N); out.append((P[i], T[i], N, B))
        return out

    def tube(self, pts, radii, seg, mat, col, w, cap=(True, True), squash=(1.0, 1.0), up=None, phase=0.0, face_col=None, tip=(False, False), lattice=None, wfn=None):
        """a tube through game points. col: colour or fn(point); face_col(i, k) -> colour for the quad (ring i, slot k)
        overrides. lattice = (n, colA, colB): harlequin diamonds n slots across, the triangles cut along the diamonds'
        edges. tip: close that end to a point instead of a flat fan. wfn(i, t) -> weights for ring i (t 0..1 along)"""
        if self.lod:
            seg = max(4, int(round(seg * self.q / 2)) * 2)
            n0 = len(pts); rr0 = list(radii) if isinstance(radii, (list, tuple)) else [radii] * n0
            keep = sorted(set([0, n0 - 1] + list(range(0, n0, 3 if n0 > 6 else 2))))
            if wfn: wfn = (lambda f, keep_: (lambda i, t: f(keep_[i], keep_[i] / (n0 - 1))))(wfn, keep)
            pts = [pts[i] for i in keep]; radii = [rr0[i] for i in keep]
            if lattice: col = mixc(lattice[1], lattice[2], 0.5); lattice = None
            face_col = None
        F = self.frames(pts, up); n = len(F)
        rr = list(radii) if isinstance(radii, (list, tuple)) else [radii] * n
        rings = []
        for i, (p, T, N, B) in enumerate(F):
            ww = wfn(i, i / (n - 1)) if wfn else w
            ring = []
            for k in range(seg):
                a = phase + 2 * math.pi * k / seg
                q = p + (N * math.cos(a) * squash[0] + B * math.sin(a) * squash[1]) * rr[i]
                ring.append(self.v(q, ww))
            rings.append(ring)
        out = []
        for i in range(n - 1):
            a, b = rings[i], rings[i + 1]
            for k in range(seg):
                k1 = (k + 1) % seg
                v00, v01, v10, v11 = a[k], a[k1], b[k], b[k1]
                if lattice:
                    m, cA, cB = lattice
                    if (k + i + 1) % m == 0: tris = ((v00, v01, v10, (k + 1 / 3, i + 1 / 3)), (v01, v11, v10, (k + 2 / 3, i + 2 / 3)))
                    else: tris = ((v00, v01, v11, (k + 2 / 3, i + 1 / 3)), (v00, v11, v10, (k + 1 / 3, i + 2 / 3)))
                    for x, y, z, (uu, ww_) in tris:
                        par = (math.floor((uu + ww_) / m) + math.floor((uu - ww_) / m)) % 2
                        out.append(self.f((x, y, z), mat, cA if par == 0 else cB))
                else:
                    c = face_col(i, k) if face_col else col
                    out.append(self.f((v00, v01, v11, v10), mat, c))
        for end, ring, i in ((0, rings[0], 0), (1, rings[-1], n - 1)):
            if not cap[end]: continue
            p = F[i][0] + (F[i][1] * (-1 if end == 0 else 1) * (rr[i] * 0.6 if tip[end] else 0.0))
            cv = self.v(p, wfn(i, i / (n - 1)) if wfn else w)
            cc = (face_col(min(i, n - 2), 0) if face_col else col) if not lattice else lattice[1]
            for k in range(seg):
                k1 = (k + 1) % seg
                out.append(self.f((ring[k1], ring[k], cv) if end == 0 else (ring[k], ring[k1], cv), mat, cc))
        return out

    def ellip(self, c, radii, seg, rings, mat, col, w, face_col=None, deform=None, axis=None):
        """an ellipsoid round c (poles on its y, or on `axis` = (X, Y, Z) unit vectors for its own frame). face_col(f
        centre in its own unit frame (x, y, z)) -> colour. deform(q unit point, p) -> new game point"""
        X, Y, Z = axis or (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        if self.lod: seg, rings = max(6, int(round(seg * self.q * 1.3))), max(4, int(round(rings * self.q * 1.3)))
        c = Vector(c); grid = []; units = []
        for j in range(1, rings):
            th = math.pi * j / rings; row = []; urow = []
            for k in range(seg):
                ph = 2 * math.pi * k / seg
                u = Vector((math.sin(th) * math.sin(ph), math.cos(th), -math.sin(th) * math.cos(ph)))   # (k 0 = front, -z)
                p = c + X * u.x * radii[0] + Y * u.y * radii[1] + Z * u.z * radii[2]
                if deform: p = deform(u, p)
                row.append(self.v(p, w)); urow.append(u)
            grid.append(row); units.append(urow)
        top = c + Y * radii[1]; bot = c - Y * radii[1]
        if deform: top = deform(Vector((0, 1, 0)), top); bot = deform(Vector((0, -1, 0)), bot)
        vt = self.v(top, w); vb = self.v(bot, w)
        out = []
        def fcol(us):
            if not face_col: return col
            m = sum(us, Vector()) / len(us); return face_col(m)
        for k in range(seg):
            k1 = (k + 1) % seg
            out.append(self.f((vt, grid[0][k1], grid[0][k]), mat, fcol([Vector((0, 1, 0)), units[0][k], units[0][k1]])))
            out.append(self.f((vb, grid[-1][k], grid[-1][k1]), mat, fcol([Vector((0, -1, 0)), units[-1][k], units[-1][k1]])))
            for j in range(rings - 2):
                out.append(self.f((grid[j][k], grid[j][k1], grid[j + 1][k1], grid[j + 1][k]), mat, fcol([units[j][k], units[j][k1], units[j + 1][k1], units[j + 1][k]])))
        return out

    def ball(self, c, r, mat, col, w, seg=10, rings=7, sq=(1, 1, 1)):
        return self.ellip(c, (r * sq[0], r * sq[1], r * sq[2]), seg, rings, mat, col, w)

    def torus(self, c, R, r, mat, col, w, seg=16, rseg=6, axis=(0, 1, 0), wave=None):
        """a ring round `axis` through c. wave(a) -> (radial push, push along the axis) for frills"""
        if self.lod: seg, rseg = max(6, int(round(seg * self.q))), 3
        ax = Vector(axis).normalized(); t = Vector((1, 0, 0)) if abs(ax.x) < 0.9 else Vector((0, 0, 1))
        X = (t - ax * ax.dot(t)).normalized(); Y = ax.cross(X)
        pts = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; dr, dy = wave(a) if wave else (0.0, 0.0)
            pts.append(Vector(c) + (X * math.cos(a) + Y * math.sin(a)) * (R + dr) + ax * dy)
        return self.loop(pts, r, rseg, mat, col, w)

    def loop(self, pts, r, rseg, mat, col, w, squash=(1.0, 1.0), lattice=None, face_col=None):
        """a closed tube round a loop of points (a ring, a band). squash = (along the loop's normal, sideways)"""
        n = len(pts); P = [Vector(p) for p in pts]
        cen = sum(P, Vector()) / n
        rings = []
        for i in range(n):
            T = (P[(i + 1) % n] - P[i - 1]).normalized()
            out_ = (P[i] - cen); out_ = (out_ - T * T.dot(out_)).normalized()
            B = T.cross(out_)
            ring = [self.v(P[i] + (out_ * math.cos(2 * math.pi * k / rseg) * squash[0] + B * math.sin(2 * math.pi * k / rseg) * squash[1]) * r, w) for k in range(rseg)]
            rings.append(ring)
        out = []
        for i in range(n):
            a, b = rings[i], rings[(i + 1) % n]
            for k in range(rseg):
                k1 = (k + 1) % rseg
                if lattice:
                    m, cA, cB = lattice
                    v00, v01, v10, v11 = a[k], a[k1], b[k], b[k1]
                    if (k + i + 1) % m == 0: tris = ((v00, v01, v10, (k + 1 / 3, i + 1 / 3)), (v01, v11, v10, (k + 2 / 3, i + 2 / 3)))
                    else: tris = ((v00, v01, v11, (k + 2 / 3, i + 1 / 3)), (v00, v11, v10, (k + 1 / 3, i + 2 / 3)))
                    for x, y, z, (uu, ww_) in tris:
                        par = (math.floor((uu + ww_) / m) + math.floor((uu - ww_) / m)) % 2
                        out.append(self.f((x, y, z), mat, cA if par == 0 else cB))
                else:
                    out.append(self.f((a[k], a[k1], b[k1], b[k]), mat, face_col(i, k) if face_col else col))
        return out

    def strip(self, rows, mat, w, thick=(0.004, -0.006), col=None, lattice=None, normals=None, closed=False):
        """a closed thin panel through a grid of game points rows[j][i] (j across, i along), pushed out along `normals`
        (same grid of unit vectors) by thick[0] for its face and thick[1] for its back. lattice = (colA, colB): one row of
        harlequin diamonds (rows must be 3: bottom, middle, top), the columns two to a diamond. closed: i wraps round
        (a band: give an even number of columns)"""
        if self.lod:
            if lattice: col = mixc(lattice[0], lattice[1], 0.5); lattice = None
            ni0 = len(rows[0]); st = 4 if ni0 > 40 else 2 if ni0 > 8 else 1
            keep = list(range(0, ni0, st)) if closed else sorted(set(list(range(0, ni0, st)) + [ni0 - 1]))
            rows = [[r[i] for i in keep] for r in rows]; normals = [[r[i] for i in keep] for r in normals]
        nj, ni = len(rows), len(rows[0])
        def at(j, i, s): return Vector(rows[j][i]) + Vector(normals[j][i]) * s
        fr = [[self.v(at(j, i, thick[0]), w) for i in range(ni)] for j in range(nj)]
        bk = [[self.v(at(j, i, thick[1]), w) for i in range(ni)] for j in range(nj)]
        out = []
        cA, cB = lattice if lattice else (col, col)
        for j in range(nj - 1):
            for i in range(ni if closed else ni - 1):
                i1 = (i + 1) % ni
                v00, v01, v10, v11 = fr[j][i], fr[j][i1], fr[j + 1][i], fr[j + 1][i1]
                if lattice:
                    # (columns i, rows j: diamonds of 2 x 2 cells, their edges on the cells' diagonals)
                    if (i + j + 1) % 2 == 0: tris = ((v00, v01, v10, (i + 1 / 3, j + 1 / 3)), (v01, v11, v10, (i + 2 / 3, j + 2 / 3)))
                    else: tris = ((v00, v01, v11, (i + 2 / 3, j + 1 / 3)), (v00, v11, v10, (i + 1 / 3, j + 2 / 3)))
                    for x, y, z, (uu, ww_) in tris:
                        par = (math.floor((uu + ww_) / 2) + math.floor((uu - ww_) / 2)) % 2
                        out.append(self.f((x, y, z), mat, cA if par == 0 else cB))
                else: out.append(self.f((v00, v01, v11, v10), mat, col))
                out.append(self.f((bk[j][i], bk[j + 1][i], bk[j + 1][i1], bk[j][i1]), mat, cB if lattice else col))
        if closed:
            for j in (0, nj - 1):
                for i in range(ni):
                    i1 = (i + 1) % ni; out.append(self.f((fr[j][i], fr[j][i1], bk[j][i1], bk[j][i]), mat, cB if lattice else col))
            return out
        edge = [(fr[0][i], bk[0][i]) for i in range(ni)] + [(fr[j][ni - 1], bk[j][ni - 1]) for j in range(1, nj)] + \
               [(fr[nj - 1][i], bk[nj - 1][i]) for i in range(ni - 2, -1, -1)] + [(fr[j][0], bk[j][0]) for j in range(nj - 2, 0, -1)]
        for a, b in zip(edge, edge[1:] + edge[:1]):
            out.append(self.f((a[0], b[0], b[1], a[1]), mat, cB if lattice else col))
        return out

    def bell(self, top, r, w, seg=8, rings=6, slot=True, loop=True, brass=None, dark=None):
        """a sleigh bell hanging from `top` (game point): a ball, a ridge round its middle, a slot across the bottom,
        a little loop on top"""
        brass = brass or (1.0, 1.0, 1.0); dark = dark or lin(0x2a1408)
        c = Vector(top) - Vector((0, r * 1.18, 0))
        if self.lod: return self.ellip(c + Vector((0, r * 0.15, 0)), (r * 1.15, r * 1.3, r * 1.15), 6, 4, 'brass', brass, w)
        def fc(u): return dark if (slot and u.y < -0.25 and abs(u.x) < 0.3) else brass
        out = self.ellip(c, (r, r, r), seg, rings, 'brass', brass, w, face_col=fc)
        if rings > 5: out += self.torus(c, r * 0.98, r * 0.09, 'brass', brass, w, seg=seg, rseg=3)
        if loop and r > 0.025: out += self.torus(Vector(top) - Vector((0, r * 0.12, 0)), r * 0.2, r * 0.07, 'brass', brass, w, seg=6, rseg=3, axis=(1, 0, 0))
        return out

    # ------------------------------------------------------------------------------------------ out
    def uv_box(self, tile=0.3):
        uvl = self.uv
        for fc in self.bm.faces:
            fc.normal_update(); a = max(range(3), key=lambda i: abs(fc.normal[i]))
            for l in fc.loops:
                c = l.vert.co; u, v = ((c.z, c.y), (c.x, c.z), (c.x, c.y))[a]
                l[uvl].uv = (u / tile, v / tile)

    def to_object(self, mats):
        self.bm.faces.index_update()
        self.face_tag = {}
        for tag, fs in getattr(self, 'piece_faces', []):
            for x in fs:
                if x.is_valid: self.face_tag[x.index] = tag
        self.uv_box()
        self.bm.transform(G2B)
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free()
        o = bpy.data.objects.new(self.name, me); bpy.context.scene.collection.objects.link(o)
        for m in mats: me.materials.append(m)
        for g in self.groups: o.vertex_groups.new(name=g)
        for p in me.polygons: p.use_smooth = True
        return o


def quantize_weights(path):
    """WEIGHTS_0 as normalised bytes (core glTF allows it, three reads it): a quarter of the float size
    (the same step as the hat lord's rebuild)"""
    import struct
    raw = open(path, 'rb').read()
    jl = struct.unpack('<I', raw[12:16])[0]; js = json.loads(raw[20:20 + jl]); bo = 20 + jl
    bl = struct.unpack('<I', raw[bo:bo + 4])[0]; blob = bytearray(raw[bo + 8:bo + 8 + bl])
    done = set()
    for m in js['meshes']:
        for p_ in m['primitives']:
            ai = p_['attributes'].get('WEIGHTS_0')
            if ai is None or ai in done: continue
            a = js['accessors'][ai]
            if a['componentType'] != 5126: continue
            bv = js['bufferViews'][a['bufferView']]; off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
            w = np.frombuffer(bytes(blob[off:off + a['count'] * 16]), np.float32).reshape(-1, 4)
            q = np.floor(w * 255 + 0.5).astype(np.int32)
            d = 255 - q.sum(1); k = q.argmax(1); q[np.arange(len(q)), k] += d
            new = np.clip(q, 0, 255).astype(np.uint8).tobytes()
            while len(blob) % 4: blob.append(0)
            nv = dict(buffer=0, byteOffset=len(blob), byteLength=len(new), target=34962); blob += new
            js['bufferViews'].append(nv); a['bufferView'] = len(js['bufferViews']) - 1; a.pop('byteOffset', None)
            a['componentType'] = 5121; a['normalized'] = True; done.add(ai)
    used = {a['bufferView'] for a in js['accessors'] if 'bufferView' in a} | {im['bufferView'] for im in js.get('images', [])}
    out = bytearray(); remap = {}; views = []
    for i, bv in enumerate(js['bufferViews']):
        if i not in used: continue
        while len(out) % 4: out.append(0)
        o0 = bv.get('byteOffset', 0); nb = dict(bv); nb['byteOffset'] = len(out); out += blob[o0:o0 + bv['byteLength']]
        remap[i] = len(views); views.append(nb)
    for a in js['accessors']:
        if 'bufferView' in a: a['bufferView'] = remap[a['bufferView']]
    for im in js.get('images', []): im['bufferView'] = remap[im['bufferView']]
    js['bufferViews'] = views
    while len(out) % 4: out.append(0)
    js['buffers'] = [dict(byteLength=len(out))]
    jb = json.dumps(js, separators=(',', ':')).encode()
    while len(jb) % 4: jb += b' '
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(jb) + 8 + len(out))); f.write(struct.pack('<II', len(jb), 0x4E4F534A)); f.write(jb)
        f.write(struct.pack('<II', len(out), 0x004E4942)); f.write(bytes(out))
    print('JF_WEIGHTS8', os.path.getsize(path) // 1024, 'KB')
