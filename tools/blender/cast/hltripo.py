# MADAM CHAIR from the owner's Tripo model (docs/story/cast_refs/hat_lord_tripo_owner.glb): the mesh surgery kit for
# rebuild_hat_lord_tripo.py. Plain bmesh + numpy. Everything is in blender axes = gv(game): x = HER right, -y = her
# front, z up, metres, root space at rest (feet at z 0).
#  · tripo_import(): the main mesh only (no Mixamo rig, no clips, no stray Icosphere), scaled so the top of her head is
#    2.96 m, turned to face the game's front, split into its islands and sorted by what they are
#  · loops, caps, domes and rings on bmesh boundaries (every hole the surgery makes gets closed)
import os, sys, math, json
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, kdtree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
SRC = os.path.join(ROOT, 'docs', 'story', 'cast_refs', 'hat_lord_tripo_owner.glb')

# where her head stops (tripo units, z up, she faces -y there) and how we turn tripo into the game
T_CX, T_CY = -0.0644, -0.1855        # her centre line (between the hips), tripo x / y
T_CUT = 0.774                        # the head meets the brim's underside just above this: the hat comes off here
T_TOP = 0.792                        # the top of her skull, once the head is closed
K = 2.96 / T_TOP                     # metres per tripo unit: 2.96 m to the top of her head


def t2b(p):
    """a tripo point -> blender (game) space"""
    return Vector((-K * (p[0] - T_CX), -K * (p[1] - T_CY), K * p[2]))


def link(o):
    bpy.context.scene.collection.objects.link(o); return o


def obj_from_bm(name, bm, mats=()):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); me.update()
    o = link(bpy.data.objects.new(name, me))
    for m in mats: me.materials.append(m)
    return o


# ------------------------------------------------------------------------------------------------ import
def tripo_import(path=SRC):
    """-> dict name -> bmesh (blender space). names: main (hat + head + body + legs), cape, bands (the hat's fingers
    over her eyes), socket (the chest ring), lips, stars (2, the collar's brooches), blobs (the crown's eye blobs),
    and what was dropped (junk: stray triangles)"""
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=path)
    src = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('tripo_node')][0]
    bm = bmesh.new(); bm.from_mesh(src.data)   # the REST mesh (the armature modifier is not applied: Tripo's A-pose)
    M = Matrix.Translation((K * T_CX, K * T_CY, 0)) @ Matrix.Scale(K, 4) @ Matrix.Rotation(math.pi, 4, 'Z')
    bm.transform(M)
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for a in list(bpy.data.actions): bpy.data.actions.remove(a)
    for m in list(bpy.data.meshes):
        if m.users == 0: bpy.data.meshes.remove(m)
    # vertex groups (Mixamo weights) go with the rig
    dl = bm.verts.layers.deform.active
    if dl: bm.verts.layers.deform.remove(dl)
    isl = islands(bm)          # (islands of the mesh as Tripo wrote it: welding first glues the lips and a stray quad on)
    out = {'blobs': [], 'stars': [], 'lips': [], 'junk': []}
    isl.sort(key=lambda fs: -len(fs))
    def sub(fs):
        b2 = bmesh.new(); vm = {}
        for f in fs:
            vs = []
            for v in f.verts:
                if v not in vm: vm[v] = b2.verts.new(v.co)
                vs.append(vm[v])
            try: b2.faces.new(vs)
            except ValueError: pass
        bmesh.ops.remove_doubles(b2, verts=b2.verts, dist=1e-5 * K)
        b2.normal_update(); return b2
    for i, fs in enumerate(isl):
        vs = {v for f in fs for v in f.verts}
        lo = Vector((min(v.co.x for v in vs), min(v.co.y for v in vs), min(v.co.z for v in vs)))
        hi = Vector((max(v.co.x for v in vs), max(v.co.y for v in vs), max(v.co.z for v in vs)))
        c = (lo + hi) / 2; n = len(fs)
        if i == 0: out['main'] = sub(fs)
        elif i == 1: out['cape'] = sub(fs)
        elif n > 400 and c.z > 2.6: out['bands'] = sub(fs)
        elif n > 150 and 2.0 < c.z < 2.6: out['socket'] = sub(fs)
        elif n > 60 and 2.35 < c.z < 2.55 and abs(c.x) > 0.1: out['stars'].append(sub(fs))
        elif c.z > 2.98 and n >= 30: out['blobs'].append(sub(fs))
        elif 2.65 < c.z < 2.78 and abs(c.x) < 0.06 and n >= 20: out['lips'].append(sub(fs))
        else: out['junk'].append((n, tuple(round(x, 3) for x in c)))
    bm.free()
    return out


def islands(bm):
    seen = set(); out = []
    for f in bm.faces:
        if f.index in seen: continue
        st = [f]; seen.add(f.index); fs = []
        while st:
            x = st.pop(); fs.append(x)
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in seen: seen.add(y.index); st.append(y)
        out.append(fs)
    return out


# ------------------------------------------------------------------------------------------------ boundaries
def boundary_loops(bm, verts=None):
    """ordered loops of boundary vertices (each a list of BMVert)"""
    edges = [e for e in bm.edges if e.is_boundary and (verts is None or (e.verts[0] in verts and e.verts[1] in verts))]
    nb = {}
    for e in edges:
        a, b = e.verts
        nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
    seen = set(); loops = []
    for start in nb:
        if start in seen: continue
        lp = [start]; seen.add(start); prev = None; cur = start
        while True:
            nxt = [v for v in nb[cur] if v is not prev and v not in seen]
            if not nxt: break
            prev, cur = cur, nxt[0]; lp.append(cur); seen.add(cur)
        loops.append(lp)
    return loops


def loop_frame(lp):
    """centre, normal (by the loop's winding), mean radius"""
    P = [v.co for v in lp]; c = sum(P, Vector()) / len(P)
    n = Vector()
    for i in range(len(P)): n += (P[i] - c).cross(P[(i + 1) % len(P)] - c)
    r = sum((p - c).length for p in P) / len(P)
    return c, n.normalized(), r


def dome_cap(bm, lp, up, height, rings=4, mat=0, shape=1.0, apex_shift=Vector(), smooth=True):
    """close a boundary loop with a dome: rings drawn in toward the loop's centre and lifted along `up` (a unit vector,
    the side the dome bulges to). height may be negative (a hollow). returns the new faces"""
    c, _, r = loop_frame(lp)
    up = up.normalized(); n = len(lp)
    prev = lp; faces = []
    base = [v.co.copy() for v in lp]
    for k in range(1, rings + 1):
        t = k / (rings + 1)                    # 0 at the rim .. 1 at the apex
        h = height * math.sin(t * math.pi / 2) ** shape
        ring = [bm.verts.new(c + apex_shift * t + (p - c) * math.cos(t * math.pi / 2) + up * h) for p in base]
        for i in range(n):
            j = (i + 1) % n
            try: f = bm.faces.new((prev[i], prev[j], ring[j], ring[i])); f.material_index = mat; f.smooth = smooth; faces.append(f)
            except ValueError: pass
        prev = ring
    apex = bm.verts.new(c + apex_shift + up * height)
    for i in range(n):
        j = (i + 1) % n
        try: f = bm.faces.new((prev[i], prev[j], apex)); f.material_index = mat; f.smooth = smooth; faces.append(f)
        except ValueError: pass
    return faces, apex


def fix_winding(bm, faces, outward_from):
    """faces whose normal points toward `outward_from` get flipped (a cap must face out of the closed shape)"""
    bm.normal_update()
    for f in faces:
        if f.normal.dot(f.calc_center_median() - outward_from) < 0: f.normal_flip()


def cut_split(bm, plane_co, plane_no, face_filter, seed_co):
    """bisect the faces that pass face_filter with a plane, then split the mesh along the cut: returns (A, B) face
    sets, A = the side connected to the face nearest seed_co. the cut edges are split so A and B share nothing"""
    faces = [f for f in bm.faces if face_filter(f)]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=plane_co, plane_no=plane_no, dist=1e-6)
    cut = [g for g in res['geom_cut'] if isinstance(g, bmesh.types.BMEdge)]
    cutset = set(cut)
    bm.faces.ensure_lookup_table()
    seed = min(bm.faces, key=lambda f: (f.calc_center_median() - seed_co).length)
    A = {seed}; st = [seed]
    while st:
        x = st.pop()
        for e in x.edges:
            if e in cutset: continue
            for y in e.link_faces:
                if y not in A: A.add(y); st.append(y)
    B = set(bm.faces) - A
    if cut: bmesh.ops.split_edges(bm, edges=[e for e in cut if e.is_valid and len(e.link_faces) == 2 and ((e.link_faces[0] in A) != (e.link_faces[1] in A))])
    return A, B, cut


def extract(bm, faces):
    """a new bmesh with only these faces"""
    b2 = bmesh.new(); vm = {}
    for f in faces:
        vs = []
        for v in f.verts:
            if v not in vm: vm[v] = b2.verts.new(v.co)
            vs.append(vm[v])
        try:
            nf = b2.faces.new(vs); nf.smooth = f.smooth; nf.material_index = f.material_index
        except ValueError: pass
    b2.normal_update(); return b2


def clean(bm, merge=1e-4):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
    bmesh.ops.dissolve_degenerate(bm, dist=merge * 0.5, edges=bm.edges)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
    le = [e for e in bm.edges if not e.link_faces]
    if le: bmesh.ops.delete(bm, geom=le, context='EDGES')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def stats(bm):
    nm = sum(1 for e in bm.edges if len(e.link_faces) > 2); bd = sum(1 for e in bm.edges if e.is_boundary)
    return dict(verts=len(bm.verts), faces=len(bm.faces), tris=sum(len(f.verts) - 2 for f in bm.faces), nonmanifold=nm, boundary=bd)


# ------------------------------------------------------------------------------------------------ cutting along a field
def field_cut(bm, fn, seed_co, faces=None, separate=True):
    """split the mesh where fn(co) (a scalar, continuous) crosses zero: crossing edges are split, crossed faces
    are split between their two new verts, then the side holding the face nearest seed_co (A) is torn from the rest
    (B). returns (A, B, cut_edges). faces: only these are cut (None = all)"""
    fs = set(bm.faces if faces is None else faces)
    val = {v: fn(v.co) for f in fs for v in f.verts}
    new = {}
    for e in list({e for f in fs for e in f.edges}):
        a, b = e.verts; fa, fb = val[a], val[b]
        if (fa > 0) == (fb > 0) or abs(fa - fb) < 1e-12: continue
        t = fa / (fa - fb)
        if t < 1e-4: val[a] = -1e-9 if fa > 0 else 1e-9; continue   # (a crossing right on a vertex: nudge it)
        if t > 1 - 1e-4: val[b] = -1e-9 if fb > 0 else 1e-9; continue
        ne, nv = bmesh.utils.edge_split(e, a, t); val[nv] = 0.0; new[nv] = True
    cut = []
    for f in [f for f in bm.faces if f.is_valid]:
        nv = [v for v in f.verts if v in new]
        if len(nv) == 2 and not any(e for e in f.edges if set(e.verts) == set(nv)):
            try:
                res = bmesh.utils.face_split(f, nv[0], nv[1]); cut.append(res[1].edge if res[1] is not None else None)
            except Exception: pass
        elif len(nv) == 2:
            cut += [e for e in f.edges if set(e.verts) == set(nv)]
    cut = list({e for e in cut if e is not None and e.is_valid})
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    if not separate: return None, None, cut      # (only draw the line into the mesh: a clean edge for a material change)
    cutset = set(cut)
    seed = min(bm.faces, key=lambda f: (f.calc_center_median() - seed_co).length)
    A = {seed}; st = [seed]
    while st:
        x = st.pop()
        for e in x.edges:
            if e in cutset: continue
            for y in e.link_faces:
                if y not in A: A.add(y); st.append(y)
    B = set(bm.faces) - A
    sp = [e for e in cut if e.is_valid and len(e.link_faces) == 2 and ((e.link_faces[0] in A) != (e.link_faces[1] in A))]
    if sp: bmesh.ops.split_edges(bm, edges=sp)
    return A, B, cut


def zip_bridge(bm, la, lb, mat=0, smooth=True):
    """triangles between two closed loops of any counts (both ordered the same way round): walk both by arc length"""
    def arcs(l):
        P = [v.co for v in l]; d = [0.0]
        for i in range(1, len(P) + 1): d.append(d[-1] + (P[i % len(P)] - P[i - 1]).length)
        return [x / d[-1] for x in d[:-1]]
    # start lb at its vertex nearest la[0]
    k = min(range(len(lb)), key=lambda i: (lb[i].co - la[0].co).length); lb = lb[k:] + lb[:k]
    ua, ub = arcs(la), arcs(lb); i = j = 0; na, nb = len(la), len(lb); faces = []
    while i < na or j < nb:
        a0, b0 = la[i % na], lb[j % nb]
        na_t = ua[i + 1] if i + 1 < na else 1.0; nb_t = ub[j + 1] if j + 1 < nb else 1.0
        if (na_t <= nb_t and i < na) or j >= nb:
            tri = (a0, la[(i + 1) % na], b0); i += 1
        else:
            tri = (a0, lb[(j + 1) % nb], b0); j += 1
        try: f = bm.faces.new(tri); f.material_index = mat; f.smooth = smooth; faces.append(f)
        except ValueError: pass
    return faces


def ring_from(bm, lp, fn):
    """a new loop: fn(vertex co) -> new co, for every vertex of lp"""
    return [bm.verts.new(fn(v.co)) for v in lp]


def quads(bm, la, lb, mat=0, smooth=True):
    n = len(la); out = []
    for i in range(n):
        j = (i + 1) % n
        try: f = bm.faces.new((la[i], la[j], lb[j], lb[i])); f.material_index = mat; f.smooth = smooth; out.append(f)
        except ValueError: pass
    return out


def fan(bm, lp, apex_co, mat=0, smooth=True):
    a = bm.verts.new(apex_co); out = []
    for i in range(len(lp)):
        try: f = bm.faces.new((lp[i], lp[(i + 1) % len(lp)], a)); f.material_index = mat; f.smooth = smooth; out.append(f)
        except ValueError: pass
    return out, a


def orient_loop(lp, up):
    """the loop's winding counter-clockwise seen from +up"""
    c, n, r = loop_frame(lp)
    return lp if n.dot(up) > 0 else lp[::-1]
