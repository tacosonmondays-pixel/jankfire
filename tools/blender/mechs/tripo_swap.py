# The owner's Tripo meshes onto the mech rig: a fused Tripo body is cut onto the joints, the moving parts (wings, crane
# drone, sword, shield) are fitted where the concept ones were, the paint areas keep taking the team colour, and the
# result is exported over public/models/x_mech_<name>.glb with every marker and clip from make_mechs_rig.py.
#   blender52 -b -P tools/blender/mechs/tripo_swap.py -- mech=paperplane [body=paperplane_body_a] [in=docs/mechs/tripo/in]
#       [yaw=180] [keep=hand_L,hand_R] [concept=drone] [hull=shin_L,shin_R] [rods=drop] [body_tris=45000]
#       [lod_tris=7000: also far copies <joint>_lod1, off by default] [qa] [no-export] [out=<path.glb>] [dump=<path.npz>]
#   blender52 -b -P tools/blender/mechs/tripo_swap.py -- mech=nightshift make-standin=<dir>   (a fake Tripo input from the
#       concept model, to test the swap before the real files exist)
# Inputs (Tripo GLBs, named as in docs/mechs/tripo/TRIPO.md): <mech>_body.glb (required; BODY below and body= pick others),
# paperplane_wings.glb, paperplane_drone.glb, nightshift_sword.glb, nightshift_shield.glb (each optional: a missing part,
# or one named in concept=, keeps the concept one). No body file = nothing to do: the concept model stays (exit code 2).
# How the cut works:
# - Tripo's auto-rigged GLBs (a humanoid skeleton + skin weights) give the cut directly: every face goes to the joint its
#   bones map to, and the rig's joints move onto Tripo's own pivots (its lengths, the concept's arms-down rest), so
#   elbows and knees bend where Tripo's do. Unrigged GLBs: the concept is posed to match (a small search over the arm
#   and leg angles) and every face goes to the nearest concept part.
# - Tripo builds a body out of separate plates (shells): a shell that mostly belongs to one joint goes to it whole.
# - The Tripo look stays as it is (the owner's call, 2026-11-12: heads, V horns, faces). The concept parts in keep= (the
#   gameplay add-ons, NIGHT SHIFT's hands that grip the sword) go on with it, replacing only what was melted.
# - Untextured Tripo meshes take their paint from the nearest concept surface, voted per flat panel (team colour, white,
#   frame, glow); textured ones keep Tripo's texture, its paint areas tinted by the team colour.
# - Each piece is moved into its joint's frame as posed, so at rest (arms down) it hangs where it should and every clip
#   plays on it unchanged.
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mechkit import *
import make_mechs_rig as R
import make_tripo_refs as REFS
from mathutils.kdtree import KDTree
from mathutils import geometry

ARGS = dict(a.split('=', 1) if '=' in a else (a, '1') for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))
MECH = ARGS.get('mech', 'paperplane')
IN = ARGS.get('in', os.path.join(ROOT, 'docs', 'mechs', 'tripo', 'in'))
PARTS = {'paperplane': {'wings': ['wing_L', 'wing_R'], 'drone': ['drone', 'drone_wing_L', 'drone_wing_R']}, 'nightshift': {'sword': ['sword'], 'shield': ['shield']}}
# concept parts kept on the Tripo body (the owner's call, 2026-11-12: the Tripo look stays as it is, heads and horns too):
# the gameplay add-ons, and NIGHT SHIFT's hands (Tripo's came out melted, and these grip the sword)
KEEP = {'paperplane': ['pod_L', 'pod_R', 'cannon_L', 'cannon_R'], 'nightshift': ['hand_L', 'hand_R']}
ATTACH = {'pod_L', 'pod_R', 'cannon_L', 'cannon_R', 'beacon'}  # (add-ons: no Tripo face is ever cut onto these)
GLOW = ('glow', 'thrust', 'beacon', 'led')
PAINT = ('paint', 'paint2', 'white', 'accent')
# untextured Tripo plates take one of the concept's main paints (glass, glows and small trims on a Tripo plate would
# read as noise: the kept concept head and parts carry those)
ROLE_MAP = {'glass': 'dark', 'chrome': 'frame', 'brass': 'accent', 'rubber': 'dark', 'glow': 'dark', 'glow2': 'dark', 'thrust': 'dark', 'other': 'white'}
# plates that come out lumpy are rebuilt as their convex hull (clean flat facets, like the concept's plates)
HULL = {'paperplane': [], 'nightshift': ['shin_L', 'shin_R']}
# the owner's first batch (2026-11-12): two PAPER PLANE tries (A reads as its own design, B too close to a famous one),
# and a crane drone that came out a winged helmet (the concept crane stays until Tripo makes a crane)
BODY = {'paperplane': ['paperplane_body', 'paperplane_body_a'], 'nightshift': ['nightshift_body']}
CONCEPT_PARTS = {'paperplane': ['drone'], 'nightshift': []}
PAPER = {'paperplane': ('wing_L', 'wing_R', 'drone', 'drone_wing_L', 'drone_wing_R')}  # (stay paper in the metal look)
BEVEL = {'paperplane': 0.008, 'nightshift': 0.014}  # (metres: edge chamfers on the Tripo plates)
NUMBER = {'paperplane': '07', 'nightshift': '24/7'}  # (the unit number stencil on the shoulder: herokit.py)
# hand-placed paint per Tripo body, over the automatic pass (later lines win): the faces of joint j inside the box lo..hi
# (game metres, the cut pose; mirror: |x|), optionally only those facing a way, or whole plates mostly inside (shell).
# The heads: white or team-colour helmets, accent V horns, team-colour forehead and chin, glowing eyes
_ALL = ((-9, -9, -9), (9, 9, 9))
PAINT_SPEC = {
    'paperplane_body_a': [
        dict(j='head', box=_ALL, role='white'),
        dict(j='head', box=((0.06, 4.44, -1), (0.6, 5.1, 1)), role='accent', shell=True, mirror=True),
        dict(j='head', box=((0, 4.45, -1), (0.06, 4.75, 0.02)), role='paint', mirror=True),
        dict(j='head', box=((0, 4.07, -1), (0.06, 4.2, 0.02)), role='paint', mirror=True),
        dict(j='head', box=((0.02, 4.29, -1), (0.15, 4.37, 0.05)), role='thrust', facing=(0, 0, -1), mirror=True),
        dict(j=None, box=((-0.16, 3.12, 0.05), (0.16, 3.4, 0.7)), role='thrust', facing=(0, -1, 0))],  # (the backpack can's exhaust)
    'paperplane_body_b': [
        dict(j='head', box=_ALL, role='white'),
        dict(j='head', box=((0.06, 4.42, -1), (0.6, 5.1, 1)), role='accent', shell=True, mirror=True),
        dict(j='head', box=((0, 4.36, -1), (0.07, 4.62, 0.02)), role='paint', mirror=True),
        dict(j='head', box=((0, 4.08, -1), (0.05, 4.2, 0.02)), role='paint', mirror=True),
        dict(j='head', box=((0.03, 4.27, -1), (0.18, 4.36, 0.05)), role='thrust', facing=(0, 0, -1), mirror=True),
        dict(j=None, box=((-0.13, 3.82, 0.1), (0.13, 4.08, 0.9)), role='thrust', facing=(0, 0, 1))],  # (the round back nozzle)
    'nightshift_body': [
        dict(j='head', box=_ALL, role='paint'),
        dict(j='head', box=((-0.25, 4.76, -1), (0.35, 5.06, 0.05)), role='white', facing=(0, 0, -1)),
        dict(j='head', box=((0.12, 5.12, -1), (0.7, 5.9, 1)), role='accent', shell=True, mirror=True),
        dict(j='head', box=((-0.04, 5.07, -1), (0.23, 5.36, 0.05)), role='glow', facing=(0, 0, -1))],  # (the headlamp)
}
# Tripo's auto-rig (mixamo-style names) -> our joints. "Left" is the mech's own left (_L, game -x)
MIX = {'Hips': 'hips', 'Spine': 'waist', 'Spine1': 'chest', 'Spine2': 'chest', 'Neck': 'neck', 'Head': 'head', 'HeadTop_End': 'head'}
for _l, _s in (('Left', 'L'), ('Right', 'R')):
    MIX.update({f'{_l}Shoulder': f'shoulder_{_s}', f'{_l}Arm': f'upperarm_{_s}', f'{_l}ForeArm': f'forearm_{_s}', f'{_l}Hand': f'hand_{_s}',
                f'{_l}UpLeg': f'thigh_{_s}', f'{_l}Leg': f'shin_{_s}', f'{_l}Foot': f'foot_{_s}', f'{_l}ToeBase': f'toe_{_s}', f'{_l}Toe_End': f'toe_{_s}'})
# a weight-mapped joint can still be one of these (nearest concept part decides): plates on the chest are the hatch or
# the backpack, plates on the hips the skirts, the big plates over the shoulder the pauldron
SUB = {'chest': ['chest', 'hatch', 'backpack'], 'hips': ['hips', 'skirt_L', 'skirt_R']}
for _s in 'LR': SUB[f'upperarm_{_s}'] = SUB[f'shoulder_{_s}'] = [f'shoulder_{_s}', f'upperarm_{_s}']


def bone_joint(b):
    b = b.split(':')[-1]
    if b in MIX: return MIX[b]
    for side in ('Left', 'Right'):
        if b.startswith(side + 'Hand'): return MIX[side + 'Hand']
    return None


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


def fix_winding(bm):
    """two faces running along the same edge in the same direction (a folded-over or doubled triangle, often on a
    3-face edge) can't both be wound right: the smaller one goes"""
    for _ in range(3):
        by = {}
        for f in bm.faces:
            for l in f.loops: by.setdefault((l.vert.index, l.link_loop_next.vert.index), []).append(f)
        bad = {min(fs, key=lambda f: f.calc_area()) for fs in by.values() if len(fs) > 1}
        if not bad: return
        bmesh.ops.delete(bm, geom=list(bad), context='FACES'); bm.verts.index_update(); bm.faces.index_update()


def import_tripo(path):
    """a Tripo GLB -> one welded mesh (its auto-rig, if it has one, applied: the pose it was modelled in), the rig's
    bone heads (blender space) and, per vertex, the skin weights summed onto our joints (attributes w_<joint>)"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    arm = next((o for o in new if o.type == 'ARMATURE'), None)
    shapes = {pb.custom_shape for pb in arm.pose.bones if pb.custom_shape} if arm else set()
    meshes = [o for o in new if o.type == 'MESH' and o not in shapes and len(o.data.polygons) and (o.parent or len(o.data.materials))]
    bones = {pb.name.split(':')[-1]: (arm.matrix_world @ pb.head).copy() for pb in arm.pose.bones} if arm else {}
    dg = bpy.context.evaluated_depsgraph_get(); outs = []
    for o in meshes:
        gj = {g.index: bone_joint(g.name) for g in o.vertex_groups}
        W = {}
        for v in o.data.vertices:
            for g in v.groups:
                j = gj.get(g.group)
                if j: W.setdefault(j, np.zeros(len(o.data.vertices), np.float32))[v.index] += g.weight
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)  # (deformed: the pose Tripo modelled)
        me.transform(o.matrix_world)
        for j, w in W.items(): me.attributes.new('w_' + j, 'FLOAT', 'POINT').data.foreach_set('value', w)
        outs.append(lib._link(bpy.data.objects.new('tripo_part', me)))
    for o in new: bpy.data.objects.remove(o, do_unlink=True)
    t = lib.join(outs, 'tripo_' + os.path.basename(path)[:-4]) if len(outs) > 1 else outs[0]
    t.name = 'tripo_' + os.path.basename(path)[:-4]
    bm = bmesh.new(); bm.from_mesh(t.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)  # (Tripo ships every triangle loose)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 1e-12], context='FACES')
    seen, dup = set(), []
    for f in bm.faces:  # (the same triangle twice z-fights)
        k = tuple(sorted(v.index for v in f.verts))
        if k in seen: dup.append(f)
        seen.add(k)
    bmesh.ops.delete(bm, geom=dup, context='FACES')
    bm.faces.ensure_lookup_table()
    sh, _ = shells(bm)
    for mem in sh:  # a shell with a face wound the wrong way round: its normals made consistent
        fs = [bm.faces[i] for i in mem]
        if any(len(e.link_faces) == 2 and not e.is_contiguous for f in fs for e in f.edges): bmesh.ops.recalc_face_normals(bm, faces=fs)
    fix_winding(bm)
    bm.to_mesh(t.data); bm.free()
    if t.data.has_custom_normals:
        bpy.ops.object.select_all(action='DESELECT'); t.select_set(True); bpy.context.view_layer.objects.active = t
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    for p in t.data.polygons: p.use_smooth = True
    t.data.set_sharp_from_angle(angle=math.radians(34))  # (the concept's faceted, hard-edged look)
    return t, bones


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


def fit_rigged(t, bones, mk, yaw):
    """a rigged Tripo body -> game scale: turned to face the mech's front, its head pivot at the concept's head height (the
    concept head goes on there, so the mech keeps its height and hitbox), its hips over the root, feet on the floor"""
    Rz = Matrix.Rotation(math.radians(yaw), 4, 'Z')
    t.data.transform(Rz); B = {k: Rz @ v for k, v in bones.items()}
    z0 = min(v.co.z for v in t.data.vertices)
    k = mk.J['head'][1] / max(1e-6, B['Head'].z - z0)
    M4 = Matrix.Scale(k, 4) @ Matrix.Translation(V((-B['Hips'].x, -B['Hips'].y, -z0)))
    t.data.transform(M4)
    return k, {n: M4 @ v for n, v in B.items()}


def retarget(mk, TB):
    """the rig's joints onto Tripo's pivots (TB: its bone heads, blender space): the spine where Tripo's is, each limb with
    Tripo's lengths but the concept's rest direction (arms down, legs straight: what the clips were written for), and
    everything else (hatch, backpack, pods, wings, sword...) at the concept's offset from its parent. Left and right are
    averaged so the rig stays symmetric. Returns the old joint positions"""
    J0 = {n: np.array(mk.J[n], float) for n in mk.order}
    G = {k: np.array(g_of(v), float) for k, v in TB.items()}
    for a, b in [(f'Left{s}', f'Right{s}') for s in ('Shoulder', 'Arm', 'ForeArm', 'Hand', 'UpLeg', 'Leg', 'Foot', 'ToeBase')]:
        if a in G and b in G:
            m = (G[a] * (-1, 1, 1) + G[b]) / 2; G[b] = m; G[a] = m * (-1, 1, 1)
    for s in ('Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head'):
        if s in G: G[s][0] = 0.0
    direct = {'hips': 'Hips', 'waist': 'Spine', 'chest': 'Spine1', 'neck': 'Neck', 'head': 'Head'}
    chain, shoulder = {}, {}
    for side, S in (('Left', 'L'), ('Right', 'R')):
        direct[f'upperarm_{S}'] = f'{side}Arm'; direct[f'thigh_{S}'] = f'{side}UpLeg'
        shoulder[f'shoulder_{S}'] = (f'{side}Shoulder', f'{side}Arm')
        chain.update({f'forearm_{S}': (f'{side}Arm', f'{side}ForeArm'), f'hand_{S}': (f'{side}ForeArm', f'{side}Hand'),
                      f'shin_{S}': (f'{side}UpLeg', f'{side}Leg'), f'foot_{S}': (f'{side}Leg', f'{side}Foot'), f'toe_{S}': (f'{side}Foot', f'{side}ToeBase')})
    J = {}
    for n in mk.order:  # (parents come first)
        p = mk.par[n]
        if n in direct and direct[n] in G: J[n] = G[direct[n]]
        elif n in shoulder and all(b in G for b in shoulder[n]): J[n] = (G[shoulder[n][0]] + G[shoulder[n][1]]) / 2
        elif n in chain and all(b in G for b in chain[n]):
            d = J0[n] - J0[p]; J[n] = J[p] + np.linalg.norm(G[chain[n][1]] - G[chain[n][0]]) * d / np.linalg.norm(d)
        elif p is None: J[n] = J0[n]
        else: J[n] = J[p] + J0[n] - J0[p]
    for n in mk.order:
        mk.J[n] = tuple(round(float(x), 4) for x in J[n])
    for n in mk.order:
        p = mk.par[n]; mk.E[n].location = gv(*mk.J[n]) - (gv(*mk.J[p]) if p else V((0, 0, 0)))
    mk.meta['joints'] = {n: {'at': list(mk.J[n]), 'parent': mk.par[n]} for n in mk.order}
    bpy.context.view_layer.update()
    return {n: tuple(J0[n]) for n in mk.order}


def match_pose(mk, TB):
    """the rig posed like the Tripo body: every limb segment turned onto Tripo's (the pose the cut happens in)"""
    seg = {}
    for side, S in (('Left', 'L'), ('Right', 'R')):
        seg.update({f'upperarm_{S}': (f'forearm_{S}', f'{side}Arm', f'{side}ForeArm'), f'forearm_{S}': (f'hand_{S}', f'{side}ForeArm', f'{side}Hand'),
                    f'thigh_{S}': (f'shin_{S}', f'{side}UpLeg', f'{side}Leg'), f'shin_{S}': (f'foot_{S}', f'{side}Leg', f'{side}Foot'),
                    f'foot_{S}': (f'toe_{S}', f'{side}Foot', f'{side}ToeBase')})
    Rw, P = {}, {}
    for n in mk.order:
        p = mk.par[n]; rp = Rw.get(p, Matrix.Identity(3))
        if n in seg and all(b in TB for b in seg[n][1:]):
            c, a, b = seg[n]
            rest = gv(*mk.J[c]) - gv(*mk.J[n]); want = TB[b] - TB[a]
            Rw[n] = rest.rotation_difference(want).to_matrix()
            P[n] = rp.inverted() @ Rw[n]
        else: Rw[n] = rp
    mk.pose(P)
    return P


def search_pose(mk, t, joints_sets):
    """unrigged Tripo: the concept limbs turned to sit inside the Tripo mesh (mean distance from the concept limb to the
    nearest Tripo vertex, a coarse-to-fine search over a few angles per side)"""
    co = [v.co.copy() for v in t.data.vertices]
    kd = KDTree(len(co))
    for i, c in enumerate(co): kd.insert(c, i)
    kd.balance()
    P = {}
    def cost(P, names):
        mk.pose(P); s, n = 0.0, 0
        for nm in names:
            o = mk.meshes.get(nm)
            if o is None: continue
            mw = o.matrix_world; vs = o.data.vertices
            for i in range(0, len(vs), max(1, len(vs) // 150)):
                s += kd.find(mw @ vs[i].co)[2]; n += 1
        return s / max(1, n)
    for S, sgn in (('R', 1), ('L', -1)):
        ua, fa = f'upperarm_{S}', f'forearm_{S}'
        names = [ua, fa]
        best = (1e9, None)
        for step, rng in ((15, None), (5, 1), (2, 1)):
            cands = []
            if rng is None:
                for z in range(0, 106, step):
                    for x in range(-30, 61, step):
                        for fz in (0, 20, 40): cands.append((x, z, fz))
            else:
                bx, bz, bf = best[1]
                for dx in (-step, 0, step):
                    for dz in (-step, 0, step):
                        for df in (-step, 0, step): cands.append((bx + dx, bz + dz, bf + df))
            for x, z, fz in cands:
                Q = dict(P); Q[ua] = (math.radians(x), 0, math.radians(sgn * z)); Q[fa] = (0, 0, math.radians(sgn * fz))
                c = cost(Q, names)
                if c < best[0]: best = (c, (x, z, fz))
        x, z, fz = best[1]
        P[ua] = (math.radians(x), 0, math.radians(sgn * z)); P[fa] = (0, 0, math.radians(sgn * fz))
        print(f'JF_TRIPO pose {S}: upperarm x {x} z {sgn * z}, forearm z {sgn * fz} (mean gap {best[0]:.3f} m)')
    mk.pose(P)
    return P


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


def concept_bvh(objs_by_joint):
    """the (posed) concept parts as one BVH per joint, with each triangle's paint role (decals and screens left out:
    their roles come from the plate under them)"""
    dg = bpy.context.evaluated_depsgraph_get(); out = {}
    for n, objs in objs_by_joint.items():
        Vs, Ts, roles, areas = [], [], [], []
        for o in objs:
            me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); mw = o.matrix_world; b = len(Vs)
            Vs += [mw @ v.co for v in me.vertices]
            for tri in me.loop_triangles:
                r = role_of_mat(o.material_slots[tri.material_index].material if o.material_slots else None)
                if r == 'other': continue
                Ts.append(tuple(b + i for i in tri.vertices)); roles.append(r); areas.append(tri.area)
            o.evaluated_get(dg).to_mesh_clear()
        if Ts: out[n] = (BVHTree.FromPolygons(Vs, Ts), roles, areas)
    return out


def nearest(bvh, names, p):
    best = (None, 'other', 1e9)
    for n in names:
        if n not in bvh: continue
        hit = bvh[n][0].find_nearest(p)
        if hit[0] is not None and hit[3] < best[2]: best = (n, bvh[n][1][hit[2]], hit[3])
    return best


def shells(bm):
    """connected face islands (Tripo's separate plates)"""
    sid = [-1] * len(bm.faces); out = []
    for f in bm.faces:
        if sid[f.index] >= 0: continue
        k = len(out); sid[f.index] = k; st = [f]; mem = []
        while st:
            a = st.pop(); mem.append(a.index)
            for e in a.edges:
                for g in e.link_faces:
                    if sid[g.index] < 0: sid[g.index] = k; st.append(g)
        out.append(mem)
    return out, sid


def plate_role(r):
    """a concept role -> one a Tripo plate may take (the team paint, white, dark, metal frame or the accent)"""
    r = ROLE_MAP.get(r, r)
    return r if r in ('paint', 'paint2', 'white', 'dark', 'frame', 'accent') else 'white'


def balance(units, lab, area, bvh):
    """each plate (unit) gets one paint: its own vote (the nearest concept surfaces), nudged so every joint ends up with
    about the concept part's mix of paints (a big Tripo chest still reads team-colour-and-white like the concept's)"""
    want = {}
    for j, (tree, roles, areas) in bvh.items():  # the concept part's paint mix, by area
        c = {}
        for r, a in zip(roles, areas): r = plate_role(r); c[r] = c.get(r, 0) + a
        n = sum(c.values()) or 1.0; want[j] = {r: k / n for r, k in c.items() if k / n > 0.04}
    byj = {}
    for k, idx in units.items():
        if idx: byj.setdefault(lab[idx[0]][0], []).append(idx)
    for j, us in byj.items():
        w = want.get(j)
        tot = sum(area[i] for idx in us for i in idx) or 1.0; got = {}
        for idx in sorted(us, key=lambda idx: -sum(area[i] for i in idx)):
            a = sum(area[i] for i in idx) or 1e-9; vote = {}
            for i in idx: vote[lab[i][1]] = vote.get(lab[i][1], 0) + area[i] / a
            if w:
                r = max(set(w) | set(vote), key=lambda r: vote.get(r, 0) + 1.6 * (w.get(r, 0) - got.get(r, 0) / tot))
            else: r = max(vote, key=vote.get)
            got[r] = got.get(r, 0) + a
            for i in idx: lab[i][1] = r
        if os.environ.get('JF_DEBUG'): print('JF_BAL', j, 'want', {k: round(v, 2) for k, v in (w or {}).items()}, 'got', {k: round(v / tot, 2) for k, v in got.items()}, 'units', len(us))


def assign(t, bvh, joints, rigged, textured=False):
    """every Tripo face -> (joint, role). Rigged: the joint its skin weights mostly point at (hatch, backpack, skirts and
    pauldrons sorted out by the nearest concept part among those), unrigged: the nearest concept part. A shell that is
    mostly one joint goes to it whole; mixed shells are cut per face, with a few rounds of neighbour voting. Paint is
    voted per flat panel (faces of one shell and joint joined across soft edges) so plates read as one colour"""
    bm = bmesh.new(); bm.from_mesh(t.data); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    lw = {k[2:]: bm.verts.layers.float[k] for k in bm.verts.layers.float.keys() if k.startswith('w_')} if rigged else {}
    area = [f.calc_area() for f in bm.faces]
    lab = []
    for f in bm.faces:
        c = f.calc_center_median()
        if lw:
            w = {j: sum(v[l] for v in f.verts) for j, l in lw.items()}
            base = max(w, key=w.get)
            cands = SUB.get(base, [base])
            j = nearest(bvh, cands, c)[0] if len(cands) > 1 else base
            j = j or base
            role = nearest(bvh, [j], c)[1] if j in bvh else nearest(bvh, joints, c)[1]
            if role == 'other': role = nearest(bvh, joints, c)[1]
        else:
            j, role, _ = nearest(bvh, joints, c)
        lab.append([j, role if textured else plate_role(role)])
    sh, sid = shells(bm)
    for mem in sh:  # whole plates
        tot = {}
        for i in mem: tot[lab[i][0]] = tot.get(lab[i][0], 0) + area[i]
        j, a = max(tot.items(), key=lambda kv: kv[1])
        if a >= 0.6 * sum(tot.values()):
            for i in mem: lab[i][0] = j
    for _ in range(3):  # stray faces near a seam follow their neighbours
        new = [l[0] for l in lab]
        for f in bm.faces:
            votes = {}
            for e in f.edges:
                for g in e.link_faces:
                    if g is not f: votes[lab[g.index][0]] = votes.get(lab[g.index][0], 0) + 1
            if votes:
                j, c = max(votes.items(), key=lambda kv: kv[1])
                if c >= 2 and j != lab[f.index][0]: new[f.index] = j
        for i, j in enumerate(new): lab[i][0] = j
    seen = [False] * len(bm.faces)
    if not textured:  # one paint per plate (a toy's colour separation), balanced to the concept part's own mix
        units = {}
        for mem in sh:
            if len(mem) > 250: continue
            for i in mem: units.setdefault((sid[i], lab[i][0]), []).append(i)
        big = [mem for mem in sh if len(mem) > 250]
        for mem in big:
            ms = set(mem)
            for i in mem:
                if seen[i]: continue
                seen[i] = True; st = [bm.faces[i]]; grp = []
                while st:
                    a = st.pop(); grp.append(a.index)
                    for e in a.edges:
                        if len(e.link_faces) != 2 or e.calc_face_angle(9) > math.radians(34): continue
                        for g in e.link_faces:
                            if g.index in ms and not seen[g.index] and lab[g.index][0] == lab[a.index][0]: seen[g.index] = True; st.append(g)
                units[('p', i)] = grp
        balance(units, lab, area, bvh)
        seen = [True] * len(bm.faces)
    for f in bm.faces:  # big plates: paint voted per flat panel
        if seen[f.index]: continue
        seen[f.index] = True; st = [f]; mem = []
        while st:
            a = st.pop(); mem.append(a.index)
            for e in a.edges:
                if len(e.link_faces) != 2 or e.calc_face_angle(9) > math.radians(34): continue
                for g in e.link_faces:
                    if not seen[g.index] and lab[g.index][0] == lab[a.index][0]: seen[g.index] = True; st.append(g)
        tot = {}
        for i in mem: tot[lab[i][1]] = tot.get(lab[i][1], 0) + area[i]
        r = max(tot.items(), key=lambda kv: kv[1])[0]
        for i in mem: lab[i][1] = r
    bm.free()
    return [tuple(l) for l in lab], sid


def paint_maps(t, M):
    """the team colour still works: paint faces get a grey copy of Tripo's texture (its light and dark kept, its colour
    dropped, scaled so the paint's middle tone is white) under the role colour; glow faces glow. No texture: every role
    simply uses the concept's material for it"""
    src = t.data.materials[0] if t.data.materials else None
    img = None
    if src and src.use_nodes:
        for n in src.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image: img = n.image; break
    if img is None: return None
    out = {}
    for role in PAINT:
        if role not in M.pal: continue
        m = M[role]
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
    return src


def split(t, lab, M, src, drop=()):
    """one mesh per joint (faces of the joints in drop are thrown away: those parts stay concept). Materials by role:
    textured Tripo meshes keep their own material except on paint and glow faces; untextured ones use the concept's"""
    pieces = {}
    for j in sorted({l[0] for l in lab if l[0] and l[0] not in drop}):
        bm = bmesh.new(); bm.from_mesh(t.data); bm.faces.ensure_lookup_table()
        keep = [lab[f.index][1] for f in bm.faces if lab[f.index][0] == j]
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if lab[f.index][0] != j], context='FACES')
        me = bpy.data.meshes.new(f'{j}_tripo'); bm.to_mesh(me); bm.free()
        for a in [a.name for a in me.attributes if a.name.startswith('w_')]: me.attributes.remove(me.attributes[a])
        o = lib._link(bpy.data.objects.new(f'{j}_tripo', me)); o.matrix_world = t.matrix_world
        def mat_of(r):
            if src is not None: return M[r] if r in PAINT and r in M.pal else (M['glow'] if r in GLOW else src)
            return M[r] if r in M.pal else M['white']
        me.materials.clear(); idx = {}
        for p, r in zip(me.polygons, keep):
            m = mat_of(r)
            if m.name not in idx: idx[m.name] = len(me.materials); me.materials.append(m)
            p.material_index = idx[m.name]
        pieces[j] = o
    return pieces


def tidy_piece(o, hull=False, drop_rods=True, side_mat=None, bev=0.0):
    """a cut piece tidied: thin rods dropped (sabre hilts, whip antennas, crest spikes: shells far longer than they are
    thick), and with hull=True every sizeable plate rebuilt as its convex hull with its near-flat facets merged (lumpy
    Tripo plates -> clean chunky armour). Then the concept's hard edges and box UVs. Returns (rods dropped, plates hulled)"""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    sh, _ = shells(bm); kill, todo, nrod = [], [], 0
    for mem in sh:
        fs = [bm.faces[i] for i in mem]; P = np.array([v.co[:] for v in {v for f in fs for v in f.verts}])
        if len(P) >= 4:
            c = P.mean(0); w, A = np.linalg.eigh(np.cov((P - c).T)); A = A[:, np.argsort(w)[::-1]]
            X = (P - c) @ A; ext = X.max(0) - X.min(0)
            if drop_rods and len(mem) < 400 and ext[0] > 5 * ext[1] and ext[1] < 0.08 and ext[0] > 0.25:  # (thin both ways: fins and blades stay)
                kill += fs; nrod += 1; print(f'JF_TRIPO rod dropped from {o.name}: {ext[0]:.2f} m long, {ext[1]:.2f} m thick at {tuple(round(x, 2) for x in c)}'); continue
        if hull and len(mem) >= 30:
            ar = {}
            for f in fs: ar[f.material_index] = ar.get(f.material_index, 0) + f.calc_area()
            todo.append((fs, [V(p) for p in P], max(ar, key=ar.get)))
    bmesh.ops.delete(bm, geom=list(set(kill + [f for fs, _, _ in todo for f in fs])), context='FACES')
    for f in bm.faces: f.tag = True
    for _, pts, mi in todo:
        vs = [bm.verts.new(p) for p in pts]
        res = bmesh.ops.convex_hull(bm, input=vs)
        bmesh.ops.delete(bm, geom=list({g for g in res['geom_interior'] + res['geom_unused'] if isinstance(g, bmesh.types.BMVert) and g.is_valid}), context='VERTS')
        new = [f for f in bm.faces if not f.tag]
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(7), verts=list({v for f in new for v in f.verts}), edges=list({e for f in new for e in f.edges}))
        new = [f for f in bm.faces if not f.tag]
        c = sum(pts, V((0, 0, 0))) / len(pts)  # (a convex hull: every face looks away from its middle)
        bmesh.ops.reverse_faces(bm, faces=[f for f in new if (f.calc_center_median() - c).dot(f.normal) < 0])
        for f in new:  # (two-tone like the concept's plates: the side facets take the team paint)
            f.material_index = side_mat if side_mat is not None and abs(f.normal.x) > 0.75 else mi; f.tag = True
    fix_winding(bm)
    if bev: bmesh.ops.dissolve_degenerate(bm, dist=bev * 0.45, edges=bm.edges[:])  # (edges shorter than the chamfer collapse into slivers)
    bm.to_mesh(o.data); bm.free()
    finish_obj(o, bev=bev, seg=1, angle=34)  # (a small chamfer on the plate edges: the light catches them, metal not plastic)
    if bev:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bad = [f for f in bm.faces if f.calc_area() < 1e-8]
        if bad: bmesh.ops.delete(bm, geom=bad, context='FACES'); bm.to_mesh(o.data)
        bm.free()
    return nrod, len(todo)


def paint_spec(t, lab, sid, spec):
    """the hand-placed paint (PAINT_SPEC) over the automatic one"""
    if not spec: return lab
    lab = [list(l) for l in lab]
    mw = t.matrix_world; nm = mw.to_3x3()
    C = [g_of(mw @ p.center) for p in t.data.polygons]; N = [g_of((nm @ p.normal).normalized()) for p in t.data.polygons]
    A = [p.area for p in t.data.polygons]
    for e in spec:
        lo, hi = e['box']
        def inside(c):
            x = abs(c[0]) if e.get('mirror') else c[0]
            return lo[0] <= x <= hi[0] and lo[1] <= c[1] <= hi[1] and lo[2] <= c[2] <= hi[2]
        fac = e.get('facing')
        mine = lambda i: e['j'] is None or lab[i][0] == e['j']  # (j=None: any joint)
        hit = [i for i in range(len(lab)) if mine(i) and inside(C[i]) and (fac is None or sum(a * b for a, b in zip(N[i], fac)) >= 0.4)]
        if e.get('shell'):  # whole plates that are mostly inside
            ins, tot = {}, {}
            for i in range(len(lab)):
                if mine(i): tot[sid[i]] = tot.get(sid[i], 0) + A[i]
            for i in hit: ins[sid[i]] = ins.get(sid[i], 0) + A[i]
            keep = {k for k, a in ins.items() if a >= 0.5 * tot[k]}
            hit = [i for i in range(len(lab)) if mine(i) and sid[i] in keep]
        for i in hit: lab[i][1] = e['role']
    return [tuple(l) for l in lab]


def drop_floaters(tripo, everything, tol=0.004, max_verts=400):
    """at rest (arms down), a Tripo chip that touches no other part is dropped (the asset gate's own rule: a floating
    chip reads as a bug). Repeated, since a chip may only have touched another chip that went"""
    n = 0
    for _ in range(3):
        dg = bpy.context.evaluated_depsgraph_get(); Vs, Ts, own, isl_of = [], [], [], {}
        for oi, o in enumerate(everything):
            me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); mw = o.matrix_world; b = len(Vs)
            Vs += [mw @ v.co for v in me.vertices]; isl = mesh_islands(me); isl_of[oi] = isl
            for tri in me.loop_triangles: Ts.append(tuple(b + i for i in tri.vertices)); own.append((oi, isl[tri.vertices[0]]))
            o.evaluated_get(dg).to_mesh_clear()
        tree = BVHTree.FromPolygons(Vs, Ts, epsilon=0.0); dropped = 0
        for o in tripo:
            oi = everything.index(o); isl = mesh_islands(o.data); mw = o.matrix_world; groups = {}
            for v in o.data.vertices: groups.setdefault(isl[v.index], []).append(v.index)
            kill = set()
            for k, vs in groups.items():
                if len(vs) > max_verts: continue
                if any(own[h[2]] != (oi, k) for vi in vs[::max(1, len(vs) // 200)] for h in tree.find_nearest_range(mw @ o.data.vertices[vi].co, tol)): continue
                tris = [t for t, ow in zip(Ts, own) if ow == (oi, k)]
                if tris and any(own[j] != (oi, k) for _, j in BVHTree.FromPolygons(Vs, tris, epsilon=0.0).overlap(tree)): continue
                kill.add(k)
            if kill:
                bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
                bmesh.ops.delete(bm, geom=[v for v in bm.verts if isl[v.index] in kill], context='VERTS'); bm.to_mesh(o.data); bm.free(); dropped += len(kill)
        n += dropped
        if not dropped: break
    return n


def drop_zfights(tripo, everything, eps=0.0008):
    """two facing-the-same-way triangles overlapping within eps flicker (z-fight): the Tripo one goes (the smaller, when
    both are Tripo's). The asset gate's own test"""
    dg = bpy.context.evaluated_depsgraph_get(); Vs, Ts, own = [], [], []
    for oi, o in enumerate(everything):
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); mw = o.matrix_world; b = len(Vs)
        Vs += [mw @ v.co for v in me.vertices]
        for tri in me.loop_triangles: Ts.append(tuple(b + i for i in tri.vertices)); own.append((oi, tri.polygon_index))
        o.evaluated_get(dg).to_mesh_clear()
    tree = BVHTree.FromPolygons(Vs, Ts, epsilon=0.0); tidx = {everything.index(o) for o in tripo}; kill = {}
    nrm = [(Vs[t[1]] - Vs[t[0]]).cross(Vs[t[2]] - Vs[t[0]]) for t in Ts]
    for ti, t in enumerate(Ts):
        if nrm[ti].length < 1e-12: continue
        a, b, c = (Vs[i] for i in t); n = nrm[ti].normalized(); cen = (a + b + c) / 3
        for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
            for _, _, tj, _ in tree.find_nearest_range(p, eps):
                if tj is None or tj == ti or set(t) & set(Ts[tj]) or nrm[tj].length < 1e-12: continue
                n2 = nrm[tj].normalized()
                if n.dot(n2) < 0.999: continue
                a2, b2, c2 = (Vs[i] for i in Ts[tj]); q = p - n2 * n2.dot(p - a2)
                if not geometry.intersect_point_tri(q, a2, b2, c2): continue
                if own[ti][0] not in tidx and own[tj][0] not in tidx: continue
                if own[ti][0] in tidx and own[tj][0] in tidx: loser = ti if nrm[ti].length <= nrm[tj].length else tj
                else: loser = ti if own[ti][0] in tidx else tj
                kill.setdefault(own[loser][0], set()).add(own[loser][1])
    for oi, polys in kill.items():
        o = everything[oi]; bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.faces[i] for i in polys], context='FACES'); bm.to_mesh(o.data); bm.free()
    return sum(len(v) for v in kill.values())


def mesh_islands(me):
    """vertex -> island index (connected by edges)"""
    par = list(range(len(me.vertices)))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1])
        if a != b: par[a] = b
    return [f(i) for i in range(len(me.vertices))]


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
                md = d.modifiers.new('dec', 'DECIMATE'); md.ratio = min(1.0, ratio); md.use_collapse_triangulate = True; lib.apply_mods(d)
                t += len(d.data.polygons)
    return t


def dump_points(path, mk, t, lab):
    """an npz of the cut (Tripo face centres + joint, posed concept vertices + joint) for quick overlay plots"""
    js = sorted({l[0] or '' for l in lab} | set(mk.meshes))
    F = np.array([tuple(t.matrix_world @ p.center) for p in t.data.polygons]); fl = np.array([js.index(l[0] or '') for l in lab])
    C, cl = [], []
    for n, o in mk.meshes.items():
        mw = o.matrix_world
        for v in list(o.data.vertices)[::3]: C.append(tuple(mw @ v.co)); cl.append(js.index(n))
    np.savez(path, F=F, fl=fl, C=np.array(C), cl=np.array(cl), names=np.array(js), roles=np.array([l[1] for l in lab]))


def main():
    cands = [ARGS['body']] if 'body' in ARGS else BODY[MECH]
    body_f = next((os.path.join(IN, c + '.glb') for c in cands if os.path.exists(os.path.join(IN, c + '.glb'))), os.path.join(IN, cands[0] + '.glb'))
    if not os.path.exists(body_f):
        print(f'JF_TRIPO no {os.path.relpath(body_f, ROOT)}: the concept model stays'); sys.exit(2)
    lib.reset(); lib._mats.clear()
    mod = importlib.import_module(MECH)
    mk = mod.build(); mk.build_tree()
    kind = R.KIND[MECH]
    marks = R.pp_marks(mod, mk) if kind == 'pp' else R.ns_marks(mod, mk)
    keep = ARGS['keep'].split(',') if 'keep' in ARGS else KEEP[MECH]
    keep = [n for n in keep if n in mk.E]
    parts = PARTS[MECH]
    moving = {k: [mk.meshes[n] for n in v if n in mk.meshes] for k, v in parts.items()}
    moving_objs = {o for v in moving.values() for o in v}
    body_j = [n for n in mk.meshes if mk.meshes[n] not in moving_objs]
    cut_j = [n for n in body_j if n not in ATTACH]
    t, bones = import_tripo(body_f)
    rigged = all(b in bones for b in ('Hips', 'Head', 'LeftArm', 'RightArm', 'LeftUpLeg', 'RightUpLeg'))
    yaw = float(ARGS.get('yaw', 180))
    report = {'body': os.path.basename(body_f), 'rigged': rigged}
    if rigged:
        k, TB = fit_rigged(t, bones, mk, yaw)
        J0 = retarget(mk, TB)
        for m in marks.values():  # (a marker rides with its joint)
            d = sub(mk.J[m['joint']], J0[m['joint']]); m['at'] = add(m['at'], d)
        marks = R.add_marks(mk, marks)
        match_pose(mk, TB)
    else:
        marks = R.add_marks(mk, marks)
        mk.pose(REFS.APOSE)
        k = fit_body(t, [mk.meshes[n] for n in body_j], yaw)
        search_pose(mk, t, None)
    posed = {n: e.matrix_world.copy() for n, e in mk.E.items()}
    bvh = concept_bvh({n: [mk.meshes[n]] for n in cut_j})
    src = paint_maps(t, mk.M)
    lab, sid = assign(t, bvh, cut_j, rigged, textured=src is not None)
    lab = paint_spec(t, lab, sid, PAINT_SPEC.get(os.path.basename(body_f)[:-4], []))
    if 'dump' in ARGS: dump_points(ARGS['dump'], mk, t, lab)
    if 'dump_mesh' in ARGS:  # (the fitted Tripo mesh in the cut pose, for picking PAINT_SPEC spots)
        bpy.ops.object.select_all(action='DESELECT'); t.select_set(True)
        bpy.ops.export_scene.gltf(filepath=ARGS['dump_mesh'], export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
    pieces = split(t, lab, mk.M, src, drop=keep)
    hull = ARGS['hull'].split(',') if 'hull' in ARGS else HULL[MECH]
    nrod = nhull = 0
    for j, o in pieces.items():
        sm = None
        if j in hull and src is None:
            if mk.M['paint'].name not in o.data.materials: o.data.materials.append(mk.M['paint'])
            sm = list(o.data.materials).index(mk.M['paint'])
        a, b = tidy_piece(o, hull=j in hull, drop_rods=ARGS.get('rods', 'keep') == 'drop', side_mat=sm, bev=float(ARGS.get('bevel', BEVEL[MECH]))); nrod += a; nhull += b
    ndec, slots = 0, []
    if 'flat' not in ARGS and 'no-decals' not in ARGS:  # (the hero kit's decals and spray slots)
        import herokit; ndec, slots = herokit.decorate(mk, pieces, posed, number=ARGS.get('number', NUMBER.get(MECH, '00')))
    bpy.data.objects.remove(t, do_unlink=True)
    for n in body_j:
        if n not in keep: bpy.data.objects.remove(mk.meshes.pop(n), do_unlink=True)
    to_joint(mk, pieces, posed)
    report.update({'body_scale': round(k, 4), 'pieces': len(pieces), 'concept_kept': keep, 'rods_dropped': nrod, 'plates_hulled': nhull})
    # the moving parts, at rest
    mk.pose({}); posed_rest = {n: e.matrix_world.copy() for n, e in mk.E.items()}
    decal_slots, spray = [], {}
    for sl in slots:  # (the spray / skin slots, from the cut pose to rest)
        j = sl['joint']; M4 = posed_rest[j] @ posed[j].inverted(); R3 = M4.to_3x3()
        at, d, u = g_of(M4 @ gv(*sl['at'])), g_of(R3 @ gv(*sl['dir'])), g_of(R3 @ gv(*sl['up']))
        spray['mk_' + sl['name']] = {'joint': j, 'at': at, 'dir': d}
        decal_slots.append({'name': sl['name'], 'joint': j, 'at': [round(x, 4) for x in at], 'dir': [round(x, 4) for x in norm(d)], 'up': [round(x, 4) for x in norm(u)], 'size': sl['size']})
    if spray: marks.update(R.add_marks(mk, spray))
    report['decals'] = ndec
    concept_only = ARGS['concept'].split(',') if 'concept' in ARGS else CONCEPT_PARTS[MECH]
    for part, joints in parts.items():
        f = os.path.join(IN, f'{MECH}_{part}.glb')
        if not os.path.exists(f) or part in concept_only: report[part] = 'concept'; continue
        p = import_glb(f); err = fit_part(p, moving[part])
        refs = {n: [mk.meshes[n]] for n in joints if n in mk.meshes}
        pb = concept_bvh(refs)
        psrc = paint_maps(p, mk.M)
        lab, _ = assign(p, pb, list(refs), False, textured=psrc is not None)
        pc = split(p, lab, mk.M, psrc)
        for o in pc.values(): tidy_piece(o, drop_rods=False)
        bpy.data.objects.remove(p, do_unlink=True)
        for n in refs: bpy.data.objects.remove(mk.meshes.pop(n), do_unlink=True)
        to_joint(mk, pc, posed_rest); report[part] = f'tripo (fit error {err:.3f} m)'
    near = [o for o in mk.root.children_recursive if o.type == 'MESH']
    tripo_objs = [o for o in near if o.data.name.endswith('_tripo')]
    report['lod0_tris'] = decimate(near, int(ARGS.get('body_tris', 45000)))
    for o in tripo_objs:  # (after triangulating: welds the chamfer's micro-edges, drops zero-area triangles)
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])  # (collapses only too-short edges: no welding across plates)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area() < 1e-8], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        fix_winding(bm)
        bm.to_mesh(o.data); bm.free()
    report['zfight_tris_dropped'] = drop_zfights(tripo_objs, near)
    report['floaters_dropped'] = drop_floaters(tripo_objs, near)
    report['lod0_tris'] = sum(len(o.data.polygons) for o in near)
    if 'flat' not in ARGS:  # (painted metal: the owner, 2026-11-12, "they look like plastic toys")
        import metalkit; report['metal_look'] = metalkit.apply(mk, bake='no-bake' not in ARGS, skip=PAPER.get(MECH, ()))
    if 'qa' in ARGS:
        sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts')); import qa_check
        res = qa_check.run(objects=[o.name for o in near], profile='game', eps=0.0008, tol=0.004)
        print('QA_PASS', MECH, res['pass'], 'errors', len(res['errors'])); [print('QA_ERROR', e) for e in res['errors'][:40]]
    if int(ARGS.get('lod_tris', 0)):  # (off by default: MECH DROP draws every mesh in the file)
        report['lod1_tris'] = lods(mk, int(ARGS['lod_tris']) / max(1, report['lod0_tris']))
    clip_list = R.C.all_clips(kind, tuple(mk.meta.get('drone_axis', (0, 1, 0))))
    mk.meshes = {o.name[:-5]: o for o in mk.root.children_recursive if o.type == 'MESH' and o.name.endswith('_mesh')}  # (the ground solver reads the legs)
    R.key_clips(mk, mod, clip_list)
    meta = dict(mk.meta); meta.pop('marks', None); meta.pop('wing_layout', None)
    meta.update({'phase': 'tripo', 'fps': R.C.FPS, 'marks': marks, 'root_motion': False, 'tripo': report, 'decal_slots': decal_slots,
                 'clips': [R.clip_meta(cl) for cl in clip_list]})
    mk.root['jf'] = json.dumps(meta)
    print('JF_TRIPO', MECH, json.dumps(report))
    if 'no-export' not in ARGS: R.export(mk, ARGS.get('out', os.path.join(lib.MODELS, f'x_mech_{MECH}.glb')), export_vertex_color='ACTIVE')
    return mk


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
