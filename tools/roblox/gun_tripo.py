# TRIPO TRIAL (17 Nov 2026): can AI-generated decoration meshes (Tripo) fit the Blender-artist gun kit? The owner approved
# five Tripo pieces (vault Assets/tripo-17nov: bow, teddy_charm, crystal_cluster, duck_head; ducky_smg is a reference
# only) and wants to judge whether AI pieces can match our style. This file does two things:
#   1. CLEAN: each raw Tripo mesh (~40k triangles, one fused piece, no usable UVs) is cleaned the way an artist would
#      (weld, loose bits out, holes filled, a light voxel remesh where the surface is torn, a Collapse decimate to
#      1.5-2.5k triangles, normals out) and split into colour regions by face selection (seeds grown up to concave
#      creases, planes, spheres). The result goes to <vault>/tripo-17nov/clean/<piece>.blend (one mesh, a material per
#      region role), a .glb copy to look at, and <piece>.json with the numbers. NOTHING derived from the Tripo files goes
#      into git: only this code.
#        blender -b --factory-startup -P tools/roblox/gun_tripo.py -- clean [bow teddy crystals duck]
#   2. BUILD (NOT WRITTEN: on hold since the owner, 17 Nov 2026: "wait with concept skins, tripo does a really good
#      job"). The plan was four concept skins wearing the cleaned pieces through gun_set.py (JF_EXTRA=gun_tripo): the
#      Sweet Shop v3 rifle with the Tripo bow, Glasswing v3 with the Tripo crystals, Velvet v3 with the teddy as the
#      Plush take's hero, and the Duckling SMG with the Tripo duck head (bill cut away, the shared duck_bill fitted),
#      each with Route S shade shells as the Ducklings have. Each would load its piece from the vault by absolute path and
#      skip itself when the file is not there. Until then SKINS is empty, so JF_EXTRA=gun_tripo builds nothing.
# Frame of a cleaned piece: Blender's import frame (X its right, -Y its front, Z up; about a unit tall). The kit's frame
# is metres, x right, y up, z back, the muzzle at -z.
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

VAULT = r'C:\Users\soup2\Documents\JANKFIRE Vault\Assets\tripo-17nov'
CLEAN = os.path.join(VAULT, 'clean')
RAD = math.radians
SKINS = {}  # (gun_set.py's import loop reads it; the BUILD half is on hold, see the header)


# ================================================================================================ 1. the cleanup
def _load_raw(fname):
    """the raw Tripo glb as one mesh object, its transforms applied (nothing else in the scene)"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(VAULT, fname))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    o = meshes[0]
    for m in meshes[1:]:  # (each Tripo file is one mesh; join any extra just in case)
        bm = bmesh.new(); bm.from_mesh(o.data); bm2 = bmesh.new(); bm2.from_mesh(m.data)
        bm2.transform(o.matrix_world.inverted() @ m.matrix_world); bm2.to_mesh(m.data); bm2.free()
        bm.from_mesh(m.data); bm.to_mesh(o.data); bm.free()
    o.data.transform(o.matrix_world)
    for x in [x for x in bpy.context.scene.objects if x is not o]: bpy.data.objects.remove(x, do_unlink=True)
    o.parent = None; o.matrix_world = Matrix.Identity(4)
    o.data.materials.clear()
    return o


def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def _components(bm):
    bm.verts.index_update()
    par = list(range(len(bm.verts)))
    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for e in bm.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b: par[a] = b
    out = {}
    for v in bm.verts: out.setdefault(find(v.index), []).append(v)
    return sorted(out.values(), key=len, reverse=True)


def base_clean(o, weld=1e-4, fill=64):
    """merge by distance, delete loose bits (everything but the biggest connected part), fill the small holes (boundary
       loops up to `fill` edges), normals out. returns the numbers"""
    bm = bmesh.new(); bm.from_mesh(o.data)
    raw = len(bm.faces)
    v0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=weld)
    welded = v0 - len(bm.verts)
    comps = _components(bm)
    gone = [v for c in comps[1:] for v in c]
    if gone: bmesh.ops.delete(bm, geom=gone, context='VERTS')
    bnd = [e for e in bm.edges if e.is_boundary]
    r = bmesh.ops.holes_fill(bm, edges=bnd, sides=fill)
    if r['faces']: bmesh.ops.triangulate(bm, faces=r['faces'])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    left = sum(1 for e in bm.edges if not e.is_manifold)
    bm.to_mesh(o.data); bm.free()
    return dict(raw_tris=raw, welded_verts=welded, loose_parts=len(comps) - 1, loose_verts=len(gone),
                holes_filled=len(r['faces']), nonmanifold_left=left, after_clean_tris=tri_count(o.data))


def _apply(o, kind, **kw):
    m = o.modifiers.new(kind.lower(), kind)
    for k, v in kw.items(): setattr(m, k, v)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=m.name)


def remesh(o, voxel):
    _apply(o, 'REMESH', mode='VOXEL', voxel_size=voxel, adaptivity=0.0)
    return tri_count(o.data)


def _group(o, name, weight):
    """a vertex group: weight(co) (0..1) on every vertex"""
    vg = o.vertex_groups.get(name) or o.vertex_groups.new(name=name)
    for v in o.data.vertices: vg.add([v.index], max(0.0, min(1.0, weight(v.co))), 'REPLACE')
    return vg.name


def smooth(o, factor, iterations, weight=None):
    """the Smooth modifier (fur lumps out); weight(co): where it acts (1) and where not (0: the features)"""
    kw = dict(factor=factor, iterations=iterations)
    if weight: kw['vertex_group'] = _group(o, 'smooth', weight)
    _apply(o, 'SMOOTH', **kw)


def decimate(o, target, keep=None, first=2.2):
    """the Collapse decimate down to `target` triangles. keep(co) (0..1): the features to keep detail on (eyes, nose):
       then it runs twice, first everything down to first x target, then again with the features held (the modifier's
       vertex group; in Blender 5.3 a vertex at weight 0 is not collapsed at all, whatever the group factor), so the
       features keep about twice the plain surface's density and the plain fur gives up the rest"""
    def run(t, group=None):
        kw = dict(decimate_type='COLLAPSE', ratio=min(1.0, t / max(tri_count(o.data), 1)), use_collapse_triangulate=True)
        if group: kw['vertex_group'] = group
        _apply(o, 'DECIMATE', **kw)
    if keep:
        run(target * first)
        run(target, _group(o, 'free', lambda co: 0.0 if keep(co) > 0.5 else 1.0))
    else:
        run(target)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-6)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(o.data); bm.free()
    for vg in list(o.vertex_groups): o.vertex_groups.remove(vg)
    return tri_count(o.data)


def blob_weight(spots):
    """1 inside any of the ellipsoids [(centre, half sizes)], falling to 0 at twice their size"""
    def w(co):
        best = 0.0
        for c, r in spots:
            d = math.sqrt(sum(((co[i] - c[i]) / r[i]) ** 2 for i in range(3)))
            best = max(best, 1.0 if d < 1 else max(0.0, 2.0 - d))
        return best
    return w


# ---- region tools (on the decimated mesh: a face's region is its material index)
def concave(e, deg):
    """an edge between two faces folding INWARD by more than deg degrees (a crease's valley)"""
    fs = e.link_faces
    if len(fs) != 2: return True
    a, b = fs
    if a.normal.angle(b.normal, 0.0) < RAD(deg): return False
    return (b.calc_center_median() - a.calc_center_median()).dot(a.normal) > 0


def grow(bm, seeds, deg, keep=lambda f: True, within=None):
    """the faces reached from the seed faces without crossing a concave crease sharper than deg (and, with within =
       (centre, radius), not leaving that ball; keep(f) limits it further)"""
    seen = set(seeds); todo = list(seeds)
    while todo:
        f = todo.pop()
        for e in f.edges:
            if concave(e, deg): continue
            for g in e.link_faces:
                if g in seen or not keep(g): continue
                if within and (g.calc_center_median() - Vector(within[0])).length > within[1]: continue
                seen.add(g); todo.append(g)
    return seen


def nearest_face(bm, p):
    p = Vector(p)
    return min(bm.faces, key=lambda f: (f.calc_center_median() - p).length)


def smooth_regions(bm, idx, passes=2, fixed=()):
    """a face whose neighbours (across its edges) mostly carry another region joins it: no single-triangle teeth on a
       region's border (fixed: regions that never change)"""
    for _ in range(passes):
        change = {}
        for f in bm.faces:
            if idx[f] in fixed: continue
            nb = [idx[g] for e in f.edges for g in e.link_faces if g is not f]
            if not nb: continue
            best = max(set(nb), key=nb.count)
            if best != idx[f] and nb.count(best) >= 2 and best not in fixed: change[f] = best
        for f, k in change.items(): idx[f] = k


def bisect(bm, co, no):
    """cut the mesh along a plane (new edges where it crosses): region borders that follow a straight line"""
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Vector(co), plane_no=Vector(no), dist=1e-5)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])


# ---- the four pieces: what was done to each, region by region
def seg_bow(bm):
    """THE BOW: the knot (grown from its front over the knot's round face up to the creases where the loops and the
       tails tuck in, kept inside |x| < 0.12) and the rest (loops and tails, one ribbon)"""
    seed = nearest_face(bm, (0.0, -0.2, 0.53))
    knot = grow(bm, [seed], 28.0, keep=lambda f: abs(f.calc_center_median().x) < 0.115 and 0.36 < f.calc_center_median().z < 0.72)
    idx = {f: (1 if f in knot else 0) for f in bm.faces}
    smooth_regions(bm, idx)
    return ['ribbon', 'knot'], idx


def seg_teddy(bm):
    """THE TEDDY: body (fur), the snout, the inner ears, the paw pads, the bow tie, eyes and nose, the hanging ring.
       Its fur surface is too lumpy for crease growing, so the regions are balls and ovals round the features (found on a
       depth map of the raw mesh), on faces that look the right way, then tidied (no single-triangle teeth)"""
    C = lambda f: f.calc_center_median()
    idx = {f: 0 for f in bm.faces}
    roles = ['fur', 'snout', 'ear', 'pad', 'tie', 'dark', 'ring']
    def ell(c, p, r): return sum(((c[i] - p[i]) / r[i]) ** 2 for i in range(3))
    for f in bm.faces:
        c, n = C(f), f.normal
        if c.z > 0.905: idx[f] = 6                                                       # the ring
        elif ell(c, (0.0, -0.292, 0.586), (0.036, 0.04, 0.027)) < 1 and n.y < 0.1: idx[f] = 5   # the nose
        elif min(ell(c, (sx * 0.104, -0.235, 0.645), (0.026, 0.04, 0.024)) for sx in (-1, 1)) < 1 and n.y < 0.0: idx[f] = 5  # eyes
        elif ell(c, (0.0, -0.26, 0.556), (0.098, 0.08, 0.072)) < 1 and n.y < 0.35: idx[f] = 1     # the snout
        elif min(ell(c, (sx * 0.268, 0.03, 0.785), (0.062, 0.09, 0.055)) for sx in (-1, 1)) < 1 and n.y < -0.35: idx[f] = 2  # inner ears
        elif 0.345 < c.z < 0.44 and abs(c.x) < 0.135 and c.y < -0.16 and n.y < -0.1: idx[f] = 4  # the bow tie
        elif c.z < 0.25 and abs(c.x) > 0.17 and c.y < -0.28 and n.y < -0.55: idx[f] = 3     # paw pads (the soles)
    smooth_regions(bm, idx, fixed=(5, 6))
    return roles, idx


def seg_crystals(bm):
    """THE CRYSTAL CLUSTER: the rock base, the crystals (grown down from their upper parts to the creases where they go
       into the rock), each crystal its own region index so the builder can light two of them"""
    C = lambda f: f.calc_center_median()
    top = [f for f in bm.faces if C(f).z > 0.2]
    cr = grow(bm, top, 25.0, keep=lambda f: C(f).z > 0.06)
    idx = {f: 0 for f in bm.faces}
    for f in cr: idx[f] = 1
    smooth_regions(bm, idx)
    # the crystals one by one: grown from the highest crystal face left over, stopping at the creases where two
    # crystals meet; crumbs (under 12 triangles) join the crystal beside them
    left = {f for f in bm.faces if idx[f] == 1}
    groups = []
    while left:
        s0 = max(left, key=lambda f: C(f).z)
        g = grow(bm, [s0], 14.0, keep=lambda f: f in left)
        left -= g; groups.append(g)
    big = [g for g in groups if sum(len(f.verts) - 2 for f in g) >= 12]
    owner = {f: i for i, g in enumerate(big) for f in g}
    for g in groups:
        if g in big: continue
        for f in g:
            nb = [owner[h] for e in f.edges for h in e.link_faces if h in owner]
            if nb: owner[f] = max(set(nb), key=nb.count)
            else: owner[f] = 0
    roles = ['rock'] + ['crystal%d' % i for i in range(len(big))]
    for f, i in owner.items(): idx[f] = i + 1
    return roles, idx


def duck_prep(o):
    """THE DUCK HEAD's open bill out: everything below the eyes in front (z < 0.47, y < 0.06) and the bill's curled-up
       tip (y < -0.15) is deleted, the head round the cut is eased onto the head's own fitted ellipsoid (a band 0.09
       wide, so no lip is left), and the hole is closed with a patch laid on that ellipsoid (rings from the cut's edge to
       the cap's middle); the voxel remesh after it fuses the patch in. Returns the fitted ellipsoid (raw frame)"""
    import numpy as np
    co = np.array([v.co[:] for v in o.data.vertices])
    back = co[co[:, 1] > 0.0]
    x, y, z = back[:, 0], back[:, 1], back[:, 2]
    A = np.stack([x * x, y * y, z * z, x, y, z], axis=1)
    a, b, c, d, e, f = np.linalg.lstsq(A, np.ones(len(x)), rcond=None)[0]
    Cc = Vector((-d / (2 * a), -e / (2 * b), -f / (2 * c)))
    k = 1 + d * d / (4 * a) + e * e / (4 * b) + f * f / (4 * c)
    R = Vector((math.sqrt(k / a), math.sqrt(k / b), math.sqrt(k / c)))
    def nrm(p): return Vector(((p.x - Cc.x) / R.x, (p.y - Cc.y) / R.y, (p.z - Cc.z) / R.z))
    def onell(dv):
        dv = dv.normalized()
        return Cc + Vector((R.x * dv.x, R.y * dv.y, R.z * dv.z))
    bm = bmesh.new(); bm.from_mesh(o.data)
    def mouth(p): return (p.z < 0.47 and p.y < 0.06) or (p.y < -0.15 and p.z < 0.64)
    gone = [f for f in bm.faces if mouth(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=gone, context='FACES')
    comps = _components(bm)
    if len(comps) > 1: bmesh.ops.delete(bm, geom=[v for cc in comps[1:] for v in cc], context='VERTS')
    bnd_v = [v for v in bm.verts if any(e.is_boundary for e in v.link_edges)]
    tree = BVHTree.FromPolygons([v.co.copy() for v in bnd_v], [[i, i, i] for i in range(len(bnd_v))])
    B = 0.09
    for v in bm.verts:   # ease the band round the cut onto the ellipsoid (the cut's edge right on it)
        hit = tree.find_nearest(v.co)
        dd = hit[3]
        if dd is None or dd > B: continue
        w = (1 - dd / B) ** 1.5
        v.co = v.co.lerp(onell(nrm(v.co)), w)
    bnd = {e for e in bm.edges if e.is_boundary}
    loops = []
    while bnd:
        e0 = bnd.pop(); loop = [e0.verts[0], e0.verts[1]]
        while True:
            nxt = [e for e in loop[-1].link_edges if e in bnd]
            if not nxt: break
            e = nxt[0]; bnd.discard(e)
            vv = e.other_vert(loop[-1])
            if vv is loop[0]: break
            loop.append(vv)
        loops.append(loop)
    for loop in loops:
        dirs = [nrm(v.co).normalized() for v in loop]
        m = sum(dirs, Vector()).normalized()
        K = 14
        rings = [loop]
        for kk in range(1, K):
            t = kk / K
            rings.append([bm.verts.new(onell(d0.slerp(m, t))) for d0 in dirs])
        tip = bm.verts.new(onell(m))
        n = len(loop)
        for kk in range(K - 1):
            A0, B0 = rings[kk], rings[kk + 1]
            for i in range(n):
                j = (i + 1) % n
                try: bm.faces.new([A0[i], A0[j], B0[j], B0[i]])
                except ValueError: pass
        for i in range(n):
            try: bm.faces.new([rings[-1][i], rings[-1][(i + 1) % n], tip])
            except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(o.data); bm.free()
    return dict(ellipsoid_c=[round(x, 4) for x in Cc], ellipsoid_r=[round(x, 4) for x in R], bill_faces_cut=len(gone),
                patch_loops=len(loops))


def seg_duck(bm):
    """THE DUCK HEAD: the head (yellow) and the two eyes (the oval inside each raised rim, black)"""
    idx = {f: 0 for f in bm.faces}
    for f in bm.faces:
        c = f.calc_center_median()
        if min(((c.x - sx * 0.209) / 0.042) ** 2 + ((c.z - 0.548) / 0.052) ** 2 for sx in (-1, 1)) < 1 and c.y < 0.0 and f.normal.y < -0.2:
            idx[f] = 1
    smooth_regions(bm, idx)
    return ['head', 'eye'], idx


# the features each piece keeps its detail on (raw frame): the teddy's eyes, nose, snout, bow tie, ear cups and ring;
# the duck's eyes
TEDDY_KEEP = [((-0.104, -0.235, 0.645), (0.035, 0.05, 0.033)), ((0.104, -0.235, 0.645), (0.035, 0.05, 0.033)),
              ((0.0, -0.27, 0.565), (0.1, 0.08, 0.08)), ((0.0, -0.25, 0.40), (0.14, 0.09, 0.05)),
              ((-0.268, 0.03, 0.79), (0.08, 0.1, 0.07)), ((0.268, 0.03, 0.79), (0.08, 0.1, 0.07)), ((0.0, 0.0, 0.94), (0.06, 0.04, 0.045))]
DUCK_KEEP = [((-0.209, -0.095, 0.548), (0.075, 0.08, 0.085)), ((0.209, -0.095, 0.548), (0.075, 0.08, 0.085))]

PIECES = {
    'bow': dict(src='bow.glb', target=1500, seg=seg_bow),
    'teddy': dict(src='teddy_charm.glb', target=2400, seg=seg_teddy, keep=TEDDY_KEEP, smooth=(0.6, 6)),
    'crystals': dict(src='crystal_cluster.glb', target=1500, seg=seg_crystals),
    'duck': dict(src='duck_head.glb', target=1700, prep=duck_prep, voxel=0.005, seg=seg_duck, keep=DUCK_KEEP),
}


def clean_piece(name):
    """the whole recipe for one piece (PIECES[name]): writes clean/<name>.blend, .glb and .json"""
    cfg = PIECES[name]
    os.makedirs(CLEAN, exist_ok=True)
    o = _load_raw(cfg['src'])
    info = {'piece': name, 'src': cfg['src']}
    info.update(base_clean(o))
    if cfg.get('prep'): info.update(cfg['prep'](o))
    if cfg.get('voxel'):
        info['voxel'] = cfg['voxel']; info['after_remesh_tris'] = remesh(o, cfg['voxel'])
    keep = blob_weight(cfg['keep']) if cfg.get('keep') else None
    if cfg.get('smooth'):
        info['smooth'] = cfg['smooth']
        smooth(o, cfg['smooth'][0], cfg['smooth'][1], weight=(lambda co: 1.0 - keep(co)) if keep else None)
    info['decimate'] = 'COLLAPSE' + (' (features kept: vertex group)' if keep else '')
    info['final_tris'] = decimate(o, cfg['target'], keep=keep)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table(); bm.normal_update()
    roles, idx = cfg['seg'](bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces: f.material_index = idx[f]; f.smooth = True
    info['final_tris'] = sum(len(f.verts) - 2 for f in bm.faces)
    info['regions'] = {r: sum(len(f.verts) - 2 for f in bm.faces if idx[f] == i) for i, r in enumerate(roles)}
    o.data.materials.clear()   # (the slots first: to_mesh keeps only the indices of slots that exist)
    for r in roles:
        m = bpy.data.materials.new(r); o.data.materials.append(m)
    bm.to_mesh(o.data); bm.free()
    o.name = o.data.name = name
    lo = [min(v.co[i] for v in o.data.vertices) for i in range(3)]; hi = [max(v.co[i] for v in o.data.vertices) for i in range(3)]
    info['lo'] = [round(x, 4) for x in lo]; info['hi'] = [round(x, 4) for x in hi]
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CLEAN, name + '.blend'), check_existing=False, compress=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(CLEAN, name + '.glb'), export_format='GLB', use_selection=False)
    with open(os.path.join(CLEAN, name + '.json'), 'w') as fh: json.dump(info, fh, indent=1)
    print('CLEANED', name, json.dumps(info))
    return info


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if argv and argv[0] == 'clean':
        for n in (argv[1:] or list(PIECES)): clean_piece(n)
