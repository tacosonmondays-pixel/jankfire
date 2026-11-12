# Jankburg's Blender kit: small helpers shared by the map's prop scripts (tools/blender/jankburg/make_jb_*.py).
# Everything in game coordinates (x right, y up, -z forward, metres) like lib.py; faces get explicit UVs into an atlas
# (cells by pixel rect), so one textured material can carry a whole prop and the game draws it in one call per copy.
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
import lib
from lib import gv, _obj, _image, hexrgb, apply_mods, join, smooth, text_px

ARGV = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


class Atlas:
    """an h x w srgb canvas (numpy, row 0 at the top) cut into named pixel rects"""
    def __init__(self, name, w, h, bg=0x808080):
        self.name, self.w, self.h, self.R = name, w, h, {}
        self.px = np.zeros((h, w, 3), np.float32); self.px[:] = hexrgb(bg)

    def add(self, key, x, y, w, h):
        self.R[key] = (x, y, w, h); return self.px[y:y + h, x:x + w]

    def uv(self, key, s, t, inset=0.5):
        """(s, t) in 0..1 across the cell (t = 0 at its bottom) -> atlas uv (v up)"""
        x, y, w, h = self.R[key]
        return ((x + inset + s * (w - 2 * inset)) / self.w, 1 - (y + inset + (1 - t) * (h - 2 * inset)) / self.h)

    def image(self): return _image(self.name, np.clip(self.px, 0, 1))


def noise(h, w, rng, cells=8, fine=0.35):
    lo = rng.random((max(1, h // cells) + 1, max(1, w // cells) + 1))
    big = np.kron(lo, np.ones((cells, cells)))[:h, :w]
    return (1 - fine) * big + fine * rng.random((h, w))


def mesh(name, verts, faces, m, uvs=None, smooth_ang=None):
    """verts in game coords; uvs = per face list of (u, v) per corner"""
    bm = bmesh.new(); vs = [bm.verts.new(gv(*p)) for p in verts]
    lay = bm.loops.layers.uv.new('UVMap')
    for fi, f in enumerate(faces):
        try: F = bm.faces.new([vs[i] for i in f])
        except ValueError: continue
        if uvs:
            for lp, uv in zip(F.loops, uvs[fi]): lp[lay].uv = uv
    o = _obj(name, bm, m)
    if smooth_ang: smooth(o, smooth_ang)
    return o


SIDES = ('-z', '+z', '-x', '+x', '+y', '-y')


def boxa(name, lo, hi, m, A, cells, flip_u=()):
    """an axis box from game corner lo to hi, each face mapped whole onto an atlas cell. cells: {side: key} or {'all': key}
    (side = which way the face looks; a missing side gets no face). u runs to the right of whoever looks at that face,
    v up (for +y / -y faces: v toward -z)."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    F = {  # corners in order bottom-left, bottom-right, top-right, top-left as seen from outside
        '-z': [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
        '+z': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        '-x': [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
        '+x': [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
        '+y': [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
        '-y': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
    }
    verts, faces, uvs = [], [], []
    for s in SIDES:
        key = cells.get(s, cells.get('all'))
        if key is None: continue
        i = len(verts); verts += F[s]; faces.append((i, i + 1, i + 2, i + 3))
        st = [(0, 0), (1, 0), (1, 1), (0, 1)]
        if s in flip_u: st = [(1 - a, b) for a, b in st]
        uvs.append([A.uv(key, a, b) for a, b in st])
    o = mesh(name, verts, faces, m, uvs)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(o.data); bm.free()
    return o


def fill_uv(o, A, key):
    """every face of o box-projected into one atlas cell (small parts in one flat colour)"""
    me = o.data
    if not me.uv_layers: me.uv_layers.new(name='UVMap')
    lay = me.uv_layers[0].data; co = [v.co for v in me.vertices]
    lo = [min(c[k] for c in co) for k in range(3)]; ext = [max(max(c[k] for c in co) - lo[k], 1e-6) for k in range(3)]
    for p in me.polygons:
        n = p.normal; ax = max(range(3), key=lambda k: abs(n[k])); a, b = [k for k in range(3) if k != ax]
        for li in p.loop_indices:
            c = co[me.loops[li].vertex_index]
            lay[li].uv = A.uv(key, (c[a] - lo[a]) / ext[a], (c[b] - lo[b]) / ext[b], inset=1.0)
    return o


def face_dir(o, want):
    w = gv(*want) - gv(0, 0, 0)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bad = [f for f in bm.faces if f.normal.dot(w) < 0]
    if bad: bmesh.ops.reverse_faces(bm, faces=bad)
    bm.to_mesh(o.data); bm.free()
    return o


def outward(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    return o


def lathe_closed(name, prof, c, m, seg=16, axis='y'):
    """a closed profile [(r, along)] revolved round an axis through c ('y' up, or 'x' / 'z')"""
    verts, faces = [], []
    for r, y in prof:
        for i in range(seg):
            a = 2 * math.pi * i / seg; ca, sa = math.cos(a) * r, math.sin(a) * r
            p = {'y': (ca, y, sa), 'x': (y, ca, sa), 'z': (ca, sa, y)}[axis]
            verts.append((c[0] + p[0], c[1] + p[1], c[2] + p[2]))
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n
        for k in range(seg):
            k2 = (k + 1) % seg; faces.append((i * seg + k, i * seg + k2, j * seg + k2, j * seg + k))
    o = outward(mesh(name, verts, faces, m)); smooth(o, 40)
    return o


def qa(objs, tag):
    sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    res = qa_check.run(objects=[o.name for o in objs], profile='game', eps=0.0008, tol=0.002)
    print('QA_PASS', tag, res.get('pass'))
    for k in ('errors', 'warnings'):
        for e in res.get(k, []): print('QA_' + k.upper()[:-1], tag, str(e)[:300])
    return res


def joined(parts, name):
    for o in parts: apply_mods(o)
    j = join(parts, name)
    bm = bmesh.new(); bm.from_mesh(j.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(j.data); bm.free()
    return j


def extent(objs):
    lo = [1e9] * 3; hi = [-1e9] * 3
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co; g = (w.x, w.z, -w.y)
            for k in range(3): lo[k] = min(lo[k], g[k]); hi[k] = max(hi[k], g[k])
    return lo, hi


def tris(o):
    o.data.calc_loop_triangles(); return len(o.data.loop_triangles)


# ------------------------------------------------------------ painters (the firewall's precast concrete)
CONC = 0x6c7186


def concrete(v, seed, ppm=11.6, lifts=True, base=CONC):
    h, w = v.shape[:2]; r = np.random.default_rng(seed)
    n = noise(h, w, r, 6, 0.4)
    v[:] = hexrgb(base)[None, None] * (0.86 + 0.2 * n[..., None])
    if lifts:
        for k in range(1, 4): v[max(0, h - int(k * 3.4 * ppm)) - 1:max(0, h - int(k * 3.4 * ppm)) + 1] *= 0.72  # lift lines
        v[4::9, 3::8] = hexrgb(0x4a4e5c)  # form-tie holes
        v[5::9, 3::8] *= 0.85
    for c in r.choice(w, w // 12, replace=False):  # grime streaking down from the top
        ln = int(h * (0.2 + 0.6 * r.random())); v[:ln, c] *= np.linspace(0.78, 1.0, ln)[:, None]
    v[int(h * 0.88):] *= np.linspace(1.0, 0.7, h - int(h * 0.88))[:, None, None] * np.array([1.0, 0.95, 0.88])  # splash dirt


def stencil(v, txt, row, scale, col, wear=0.18, seed=1):
    r = np.random.default_rng(seed); h, w = v.shape[:2]
    t = np.zeros_like(v); tw = (len(txt) * 6 - 1) * scale
    text_px(t, txt, (w - tw) // 2, row, scale, 0xffffff)
    m = (t.sum(2) > 0) & (r.random((h, w)) > wear)
    v[m] = v[m] * 0.15 + hexrgb(col) * 0.85
