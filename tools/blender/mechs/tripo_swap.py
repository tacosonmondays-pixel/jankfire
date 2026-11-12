# The owner's Tripo meshes onto the mech rig: a fused Tripo body is cut onto the joints, the moving parts (wings, crane
# drone, sword, shield) are fitted where the concept ones were, the paint areas keep taking the team colour, and the
# result is exported over public/models/x_mech_<name>.glb with every marker and clip from make_mechs_rig.py.
#   blender52 -b -P tools/blender/mechs/tripo_swap.py -- mech=paperplane [in=docs/mechs/tripo/in] [yaw=180]
#       [body_tris=45000] [lod_tris=7000] [no-export] [out=<path.glb>]
#   blender52 -b -P tools/blender/mechs/tripo_swap.py -- mech=nightshift make-standin=<dir>   (a fake Tripo input from the
#       concept model, to test the swap before the real files exist)
# Inputs (Tripo GLBs, named as in docs/mechs/tripo/TRIPO.md): <mech>_body.glb (required), paperplane_wings.glb,
# paperplane_drone.glb, nightshift_sword.glb, nightshift_shield.glb (each optional: a missing part keeps the concept one).
# No body file = nothing to do: the concept model stays (exit code 2, the existing glb is left alone).
# How the cut works: Tripo built the body from the A-pose pictures (make_tripo_refs.py), so the rig is put in that same
# A-pose, the Tripo mesh is fitted onto the posed concept body (height, feet on the floor, centred), and every Tripo face
# goes to the joint of the concept surface nearest to it. Each piece is moved into its joint's frame as posed, so at
# rest (arms down) it sits where the concept part did, and every clip plays on it unchanged.
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mechkit import *
import make_mechs_rig as R
import make_tripo_refs as REFS
from mathutils.kdtree import KDTree

ARGS = dict(a.split('=', 1) if '=' in a else (a, '1') for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))
MECH = ARGS.get('mech', 'paperplane')
IN = ARGS.get('in', os.path.join(ROOT, 'docs', 'mechs', 'tripo', 'in'))
PARTS = {'paperplane': {'wings': ['wing_L', 'wing_R'], 'drone': ['drone', 'drone_wing_L', 'drone_wing_R']}, 'nightshift': {'sword': ['sword'], 'shield': ['shield']}}
GLOW = ('glow', 'thrust', 'beacon', 'led')


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
    j = lib.join(meshes, 'tripo_' + os.path.basename(path)[:-4]) if len(meshes) > 1 else meshes[0]
    bpy.ops.object.select_all(action='DESELECT'); j.select_set(True); bpy.context.view_layer.objects.active = j
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return j


def world_verts(objs):
    out = []
    for o in objs:
        mw = o.matrix_world; out += [mw @ v.co for v in o.data.vertices]
    return out


def bbox_of(pts):
    lo = V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def fit_body(t, ref_objs, yaw):
    """Tripo -> the posed concept body: turn it (glTF fronts face +z; ours -z), scale to the same height, feet on the
    floor, centred over the concept body"""
    t.data.transform(Matrix.Rotation(math.radians(yaw), 4, 'Z'))
    lo, hi = bbox_of(world_verts([t])); rlo, rhi = bbox_of(world_verts(ref_objs))
    k = (rhi.z - rlo.z) / max(1e-6, hi.z - lo.z)
    t.data.transform(Matrix.Scale(k, 4))
    lo, hi = bbox_of(world_verts([t]))
    off = V(((rlo.x + rhi.x) / 2 - (lo.x + hi.x) / 2, (rlo.y + rhi.y) / 2 - (lo.y + hi.y) / 2, rlo.z - lo.z))
    t.data.transform(Matrix.Translation(off))
    return k


def fit_part(t, ref_objs):
    """a moving part: principal axes onto the concept part's, the sign flips that land it closest to the concept part
    (mean nearest distance), the same size along its long axis"""
    import itertools
    P = np.array([tuple(v) for v in world_verts([t])], np.float64); Q = np.array([tuple(v) for v in world_verts(ref_objs)], np.float64)
    cp, cq = P.mean(0), Q.mean(0)
    def axes(X, c):
        w, v = np.linalg.eigh(np.cov((X - c).T)); o = np.argsort(w)[::-1]; return v[:, o], np.sqrt(np.maximum(w[o], 1e-12))
    Ap, sp = axes(P, cp); Aq, sq = axes(Q, cq)
    k = sq[0] / sp[0]
    kd = KDTree(len(Q))
    for i, q in enumerate(Q): kd.insert(q, i)
    kd.balance()
    best = None
    sub = P[:: max(1, len(P) // 1500)]
    for sgn in itertools.product((1, -1), repeat=3):
        Rm = Aq @ np.diag(sgn) @ Ap.T
        if np.linalg.det(Rm) < 0: continue
        X = (sub - cp) @ Rm.T * k + cq
        err = float(np.mean([kd.find(x)[2] for x in X]))
        if best is None or err < best[0]: best = (err, Rm)
    Rm = best[1]
    M4 = Matrix.Translation(V(tuple(cq))) @ Matrix([list(r) + [0] for r in (Rm * k)] + [[0, 0, 0, 1]]) @ Matrix.Translation(V(tuple(-cp)))
    t.data.transform(M4)
    return best[0]


def role_of_mat(m):
    r = m.get('jf_role') if m else None
    if r: return r
    n = (m.name if m else '').split('_', 1)[-1]
    return n if n in ROLE_LOOK or n in GLOW else 'other'


def assign(t, ref_objs, ref_joint):
    """every Tripo face -> (joint, role) of the nearest concept face; a few rounds of neighbour voting clean the seams"""
    V_, T_, meta = [], [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in ref_objs:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); b = len(V_); mw = o.matrix_world
        V_ += [mw @ v.co for v in me.vertices]
        for tri in me.loop_triangles:
            T_.append(tuple(b + i for i in tri.vertices)); m = o.material_slots[tri.material_index].material if o.material_slots else None
            meta.append((ref_joint[o], role_of_mat(m)))
        o.evaluated_get(dg).to_mesh_clear()
    bvh = BVHTree.FromPolygons(V_, T_)
    bm = bmesh.new(); bm.from_mesh(t.data); bm.faces.ensure_lookup_table()
    lab = []
    for f in bm.faces:
        hit = bvh.find_nearest(f.calc_center_median())
        lab.append(meta[hit[2]] if hit[2] is not None else (None, 'other'))
    for _ in range(3):  # majority of the edge neighbours (stray faces near a seam follow their neighbours)
        new = list(lab)
        for f in bm.faces:
            votes = {}
            for e in f.edges:
                for g in e.link_faces:
                    if g is not f: votes[lab[g.index][0]] = votes.get(lab[g.index][0], 0) + 1
            if votes:
                j, c = max(votes.items(), key=lambda kv: kv[1])
                if c >= 2 and j != lab[f.index][0]: new[f.index] = (j, lab[f.index][1])
        lab = new
    bm.free()
    return lab


def paint_maps(t, M):
    """the team colour still works: paint faces get a grey copy of Tripo's texture (its light and dark kept, its colour
    dropped, scaled so the paint's middle tone is white) under the role colour; glow faces glow"""
    src = t.data.materials[0] if t.data.materials else None
    img = None
    if src and src.use_nodes:
        for n in src.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image: img = n.image; break
    out = {}
    for role in ('paint', 'paint2', 'white', 'accent'):
        if role not in M.pal: continue
        m = M[role]
        if img is None: out[role] = m; continue
        px = np.array(img.pixels[:], np.float32).reshape(img.size[1], img.size[0], 4)
        lum = px[:, :, :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        mid = float(np.median(lum[lum > 0.02])) if (lum > 0.02).any() else 1.0
        g = lum / max(1e-3, mid)  # (the paint's middle tone -> white; the team colour multiplies it)
        gi = bpy.data.images.new(f'{M.prefix}_{role}_grey', img.size[0], img.size[1]); gp = np.ones_like(px); gp[:, :, 0] = gp[:, :, 1] = gp[:, :, 2] = np.clip(g, 0, 1)
        gi.pixels.foreach_set(gp.ravel()); gi.pack()
        nt = m.node_tree; b = nt.nodes['Principled BSDF']; tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = gi; tx.interpolation = 'Closest'
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs['Factor'].default_value = 1.0
        mix.inputs['A'].default_value = srgb(M.pal[role]); nt.links.new(tx.outputs['Color'], mix.inputs['B']); nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
        out[role] = m
    return out, src


def split(t, lab, M, roles, src, name):
    """one mesh per joint, materials by role: paint roles get their own (tintable) material, glows the glow, the rest
    keep Tripo's textured material"""
    pieces = {}
    joints = sorted({j for j, _ in lab if j})
    for j in joints:
        bm = bmesh.new(); bm.from_mesh(t.data); bm.faces.ensure_lookup_table()
        kill = [f for f in bm.faces if lab[f.index][0] != j]
        bmesh.ops.delete(bm, geom=kill, context='FACES')
        me = bpy.data.meshes.new(f'{j}_tripo'); bm.to_mesh(me); bm.free()
        o = lib._link(bpy.data.objects.new(f'{j}_tripo', me)); o.matrix_world = t.matrix_world
        mats = [src] + [M[r] for r in ('paint', 'paint2', 'white', 'accent') if r in roles] + [M['glow']]
        me.materials.clear()
        for m in mats: me.materials.append(m)
        idx = {r: 1 + i for i, r in enumerate([r for r in ('paint', 'paint2', 'white', 'accent') if r in roles])}
        lab_j = [l for l in lab if l[0] == j]
        for p, l in zip(me.polygons, lab_j):
            r = l[1]
            p.material_index = idx.get(r, len(mats) - 1 if r in GLOW else 0)
        pieces[j] = o
    return pieces


def to_joint(mk, pieces, posed_world):
    """each piece into its joint's frame as posed (so at rest it lands where the concept part was), parented"""
    for j, o in pieces.items():
        o.data.transform(posed_world[j].inverted() @ o.matrix_world); o.matrix_world = Matrix.Identity(4)
        o.parent = mk.E[j]; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_basis = Matrix.Identity(4)
        o.name = f'{j}_mesh'


def decimate(objs, target):
    tris = lambda: sum(len(o.data.polygons) for o in objs)  # (after triangulate: faces = tris)
    for o in objs:
        md = o.modifiers.new('tri', 'TRIANGULATE'); lib.apply_mods(o)
    n = tris()
    if n > target:
        r = target / n
        for o in objs:
            md = o.modifiers.new('dec', 'DECIMATE'); md.ratio = r; md.use_collapse_triangulate = True; lib.apply_mods(o)
    return tris()


def lods(mk, ratio):
    """a far copy of every joint mesh (<joint>_lod1, a sibling: the game shows one or the other by distance)"""
    t = 0
    for n, e in mk.E.items():
        for c in list(e.children):
            if c.type == 'MESH' and c.name.endswith('_mesh'):
                d = c.copy(); d.data = c.data.copy(); lib._link(d); d.parent = e; d.matrix_basis = c.matrix_basis.copy(); d.name = n + '_lod1'
                md = d.modifiers.new('dec', 'DECIMATE'); md.ratio = ratio; md.use_collapse_triangulate = True; lib.apply_mods(d)
                t += len(d.data.polygons)
    return t


def main():
    body_f = os.path.join(IN, f'{MECH}_body.glb')
    if not os.path.exists(body_f):
        print(f'JF_TRIPO no {os.path.relpath(body_f, ROOT)}: the concept model stays'); sys.exit(2)
    lib.reset(); lib._mats.clear()
    mod = importlib.import_module(MECH)
    mk = mod.build(); mk.build_tree()
    kind = R.KIND[MECH]
    marks = R.add_marks(mk, R.pp_marks(mod, mk) if kind == 'pp' else R.ns_marks(mod, mk))
    parts = PARTS[MECH]
    moving = {k: [mk.meshes[n] for n in v if n in mk.meshes] for k, v in parts.items()}
    moving_objs = {o for v in moving.values() for o in v}
    body_ref = {mk.meshes[n]: n for n in mk.meshes if mk.meshes[n] not in moving_objs}
    # the body: in the reference pictures' A-pose
    mk.pose(REFS.APOSE)
    posed = {n: e.matrix_world.copy() for n, e in mk.E.items()}
    t = import_glb(body_f)
    k = fit_body(t, list(body_ref), float(ARGS.get('yaw', 180)))
    lab = assign(t, list(body_ref), body_ref)
    roles, src = paint_maps(t, mk.M)
    pieces = split(t, lab, mk.M, roles, src, 'body')
    bpy.data.objects.remove(t, do_unlink=True)
    for o in list(body_ref): bpy.data.objects.remove(o, do_unlink=True)
    to_joint(mk, pieces, posed)
    report = {'body_scale': round(k, 4), 'pieces': len(pieces)}
    # the moving parts, at rest
    mk.pose({}); posed_rest = {n: e.matrix_world.copy() for n, e in mk.E.items()}
    for part, joints in parts.items():
        f = os.path.join(IN, f'{MECH}_{part}.glb')
        if not os.path.exists(f): report[part] = 'concept'; continue
        p = import_glb(f); err = fit_part(p, moving[part])
        refs = {o: n for n in joints for o in [mk.meshes.get(n)] if o}
        lab = assign(p, list(refs), refs)
        pc = split(p, lab, mk.M, {}, p.data.materials[0] if p.data.materials else mk.M['white'], part)
        bpy.data.objects.remove(p, do_unlink=True)
        for o in refs: bpy.data.objects.remove(o, do_unlink=True)
        to_joint(mk, pc, posed_rest); report[part] = f'tripo (fit error {err:.3f} m)'
    near = [o for o in mk.root.children_recursive if o.type == 'MESH']
    report['lod0_tris'] = decimate(near, int(ARGS.get('body_tris', 45000)))
    report['lod1_tris'] = lods(mk, int(ARGS.get('lod_tris', 7000)) / max(1, report['lod0_tris']))
    clip_list = R.C.all_clips(kind, tuple(mk.meta.get('drone_axis', (0, 1, 0))))
    mk.meshes = {o.name[:-5]: o for o in mk.root.children_recursive if o.type == 'MESH' and o.name.endswith('_mesh')}  # (the ground solver reads the legs)
    R.key_clips(mk, mod, clip_list)
    meta = dict(mk.meta); meta.pop('marks', None); meta.pop('wing_layout', None)
    meta.update({'phase': 'tripo', 'fps': R.C.FPS, 'marks': marks, 'root_motion': False, 'tripo': report, 'lod': {'far_node_suffix': '_lod1'},
                 'clips': [{k2: cl[k2] for k2 in ('name', 'dur', 'loop', 'hold', 'partial', 'note')} for cl in clip_list]})
    mk.root['jf'] = json.dumps(meta)
    print('JF_TRIPO', MECH, json.dumps(report))
    if 'no-export' not in ARGS: R.export(mk, ARGS.get('out', os.path.join(lib.MODELS, f'x_mech_{MECH}.glb')))


def make_standin(out):
    """a test input that looks like Tripo's: the concept body in the A-pose fused into one mesh, turned to face +z,
    squashed to unit height and moved off the origin; a moving part fused, turned and shrunk the same way"""
    lib.reset(); lib._mats.clear()
    mod = importlib.import_module(MECH); mod.DECALS = False
    mk = mod.build(); mk.build_tree(); os.makedirs(out, exist_ok=True)
    def dump(objs, name, M4):
        cp = [o.copy() for o in objs]
        for c, o in zip(cp, objs): c.data = o.data.copy(); lib._link(c); c.parent = None; c.matrix_world = o.matrix_world.copy()
        j = lib.join(cp, name); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        j.data.transform(M4)
        bpy.ops.object.select_all(action='DESELECT'); j.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(out, name + '.glb'), export_format='GLB', use_selection=True, export_apply=True)
        bpy.data.objects.remove(j, do_unlink=True)
    moving = {o for v in PARTS[MECH].values() for n in v for o in [mk.meshes.get(n)] if o}
    mk.pose(REFS.APOSE)
    dump([o for o in mk.meshes.values() if o not in moving], f'{MECH}_body', Matrix.Translation((0.3, -0.2, 0.1)) @ Matrix.Scale(1 / 4.8, 4) @ Matrix.Rotation(math.pi, 4, 'Z'))
    mk.pose({})
    part, joints = next(iter(PARTS[MECH].items()))
    dump([mk.meshes[n] for n in joints if n in mk.meshes], f'{MECH}_{part}', Matrix.Scale(0.4, 4) @ Matrix.Rotation(1.1, 4, 'X') @ Matrix.Rotation(0.7, 4, 'Y'))
    print('JF_STANDIN', out)


if __name__ == '__main__':
    if 'make-standin' in ARGS: make_standin(ARGS['make-standin'])
    else: main()
