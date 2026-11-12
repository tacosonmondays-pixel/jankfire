# The mechs as game files: the concept models on their joint tree, gameplay markers, every clip from clips.py keyed on
# the joints and exported as glTF animations (three.js AnimationMixer plays them by name). No skinning: each joint is
# a node with its rigid parts under it (a Tripo mesh cut at the joints drops into the same nodes: tripo_swap.py).
#   blender52 -b -P tools/blender/mechs/make_mechs_rig.py -- [mech=paperplane|nightshift] [no-export] [qa]
#   -> public/models/x_mech_<name>.glb (root meta jf: joints, clips {name, dur, loop, hold, partial, note},
#      marks {name: {joint, at, dir}}, palettes). The root never moves in a clip.
import os, sys, json, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mechkit import *
import clips as C

ARGS = dict(a.split('=', 1) if '=' in a else (a, '1') for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))
KIND = {'paperplane': 'pp', 'nightshift': 'ns'}


def pp_marks(mod, mk):
    m = {}
    for s, L in ((1, 'R'), (-1, 'L')):
        for i, (cx, cy) in enumerate([(cx, cy) for cy in (4.335, 4.21) for cx in (0.87, 1.0, 1.13)]):
            m[f'mk_missile_{L}{i}'] = {'joint': 'pod_' + L, 'at': (s * cx, cy, -0.47), 'dir': (0, 0, -1)}
        ax = norm((0, -1, 0.35)); m[f'mk_thrust_back_{L}'] = {'joint': 'backpack', 'at': add((s * 0.22, 3.30, 0.64), mul(ax, 0.30)), 'dir': ax}
        ax = norm((0, -0.35, 1)); m[f'mk_thrust_heel_{L}'] = {'joint': 'foot_' + L, 'at': add((s * 0.46, 0.22, 0.36), mul(ax, 0.16)), 'dir': ax}
    Mx = mod.wing_stow(-1); beak = g_of(Mx @ gv(*add(mod.CRANE_AT, (0, 0.39, 0.19))))
    m['mk_drone'] = {'joint': 'drone', 'at': beak, 'dir': list(mk.meta['drone_axis'])}
    m['mk_seat'] = {'joint': 'chest', 'at': (0, 3.62, -0.05), 'dir': (0, 0, -1)}
    m['mk_eject'] = {'joint': 'chest', 'at': (0, 4.15, -0.75), 'dir': (0, 0.7, -0.7)}
    return m


def ns_marks(mod, mk):
    m = dict(mk.meta.get('marks', {}))
    for s, L in ((1, 'R'), (-1, 'L')):
        ax = norm((0, -1, 0.45)); m[f'mk_thrust_back_{L}'] = {'joint': 'backpack', 'at': add((s * 0.32, 3.64, 0.86), mul(ax, 0.40)), 'dir': ax}
    m['mk_beacon'] = {'joint': 'beacon', 'at': add(mod.hp(0, 0.66, 0), (0, 0.16, 0)), 'dir': (0, 1, 0)}
    m['mk_seat'] = {'joint': 'chest', 'at': (0, 4.15, -0.20), 'dir': (0, 0, -1)}
    m['mk_eject'] = {'joint': 'chest', 'at': (0, 4.60, -0.98), 'dir': (0, 0.7, -0.7)}
    return m


def add_marks(mk, marks):
    out = {}
    for n, v in sorted(marks.items()):
        e = lib._link(bpy.data.objects.new(n, None)); e.empty_display_size = 0.08
        par = mk.E[v['joint']]; e.parent = par
        e.matrix_world = Matrix.Translation(gv(*v['at']))
        out[n] = {'joint': v['joint'], 'at': [round(x, 4) for x in v['at']], 'dir': [round(x, 4) for x in norm(v['dir'])]}
    bpy.context.view_layer.update()
    return out


def quat_of(mod, mk, joint, val):
    """a clip value -> the joint's local rotation (blender quaternion)"""
    if isinstance(val, dict): val = val.get('r', (0, 0, 0))
    if val == 'jet':
        return mod.pose_jet(mk)[joint].to_quaternion()
    if isinstance(val, tuple) and val and val[0] == 'axis':
        return Quaternion(V(gv(*val[1])).normalized(), math.radians(val[2]))
    rx, ry, rz = (math.radians(a) for a in val)
    return Euler((rx, -rz, ry), 'YZX').to_quaternion()


def legs_min_y(mk):
    """the lowest point of the legs (game y) in the current pose"""
    lo = 1e9
    for n in ('shin_L', 'shin_R', 'foot_L', 'foot_R', 'toe_L', 'toe_R'):
        o = mk.meshes.get(n)
        if o is None: continue
        me = o.data; co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3); Mw = np.array(o.matrix_world, np.float32)
        z = co @ Mw[2, :3] + Mw[2, 3]
        lo = min(lo, float(z.min()))
    return lo


def solve_ground(mk, mod, clip_list, joints, rest_loc):
    """feet on the floor: for every grounded key, pose it, find the legs' lowest point and move the hips up or down by
    that much (airborne keys, clips.AIR, keep the hips height they were written with)"""
    out = {}
    for cl in clip_list:
        if cl['partial']: continue
        air = C.AIR.get(cl['name'], set())
        for i, (t, P) in enumerate(cl['keys']):
            if air == 'all' or i in air: continue
            for n in joints:
                e = mk.E[n]; e.rotation_mode = 'QUATERNION'; v = P.get(n, (0, 0, 0))
                e.rotation_quaternion = quat_of(mod, mk, n, v)
                d = v.get('p', (0, 0, 0)) if isinstance(v, dict) else (0, 0, 0)
                e.location = rest_loc[n] + gv(*d)
            bpy.context.view_layer.update()
            hv = P.get('hips'); dy = hv.get('p', (0, 0, 0))[1] if isinstance(hv, dict) else 0.0
            out[(cl['name'], round(t, 4))] = dy - legs_min_y(mk)
    for n in joints: mk.E[n].rotation_quaternion = (1, 0, 0, 0); mk.E[n].location = rest_loc[n]
    bpy.context.view_layer.update()
    return out


def key_clips(mk, mod, clip_list):
    """one action per clip (a slot per joint), pushed into a muted NLA track per joint named after the clip: the glTF
    exporter's NLA_TRACKS mode merges same-named tracks into one animation"""
    sc = bpy.context.scene; sc.render.fps = C.FPS
    joints = [n for n in mk.order if n != 'root']
    moved = {n for cl in clip_list for _, P in cl['keys'] for n, v in P.items() if isinstance(v, dict) and 'p' in v}
    rest_loc = {n: mk.E[n].location.copy() for n in joints}
    tracks = {n: [] for n in joints}
    ground = solve_ground(mk, mod, clip_list, joints, rest_loc)
    for cl in clip_list:
        act = bpy.data.actions.new(cl['name']); act.use_fake_user = True
        names = joints if not cl['partial'] else sorted({n for _, P in cl['keys'] for n in P})
        for n in names:
            e = mk.E[n]; e.animation_data_create(); e.animation_data.action = act; e.rotation_mode = 'QUATERNION'
            prev = None
            for t, P in cl['keys']:
                f = round(t * C.FPS)  # (on the frame grid: loops close exactly)
                q = quat_of(mod, mk, n, P.get(n, (0, 0, 0)))
                if prev is not None and prev.dot(q) < 0: q = -q
                prev = q
                e.rotation_quaternion = q; e.keyframe_insert('rotation_quaternion', frame=f)
                if n in moved:
                    v = P.get(n); d = v.get('p', (0, 0, 0)) if isinstance(v, dict) else (0, 0, 0)
                    if n == 'hips' and (cl['name'], round(t, 4)) in ground: d = (d[0], ground[(cl['name'], round(t, 4))], d[2])
                    e.location = rest_loc[n] + gv(*d); e.keyframe_insert('location', frame=f)
            tracks[n].append((cl['name'], act, e.animation_data.action_slot))
    for n in joints:
        e = mk.E[n]
        if not e.animation_data: continue
        e.animation_data.action = None
        for name, act, slot in tracks[n]:
            tr = e.animation_data.nla_tracks.new(); tr.name = name
            st = tr.strips.new(name, 0, act); st.action_slot = slot; tr.mute = True
        e.rotation_quaternion = (1, 0, 0, 0); e.location = rest_loc[n]
    bpy.context.view_layer.update()


def export(mk, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in [mk.root] + list(mk.root.children_recursive): o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_extras=True, export_yup=True,
                              export_texcoords=True, export_normals=True, export_materials='EXPORT', export_image_format='AUTO',
                              export_lights=False, export_cameras=False, export_animations=True, export_animation_mode='NLA_TRACKS',
                              export_merge_animation='NLA_TRACK', export_force_sampling=True, export_frame_step=1, export_optimize_animation_size=True,
                              export_optimize_animation_keep_anim_object=True)  # (keep still channels: a joint a clip doesn't move is reset by it)
    print(f'JF_EXPORT {os.path.relpath(path, ROOT)}: {os.path.getsize(path) // 1024} KB, {mk.tris()} tris')


def main(which):
    lib.reset(); lib._mats.clear()
    mod = importlib.import_module(which)
    mk = mod.build(); mk.build_tree()
    kind = KIND[which]
    marks = add_marks(mk, pp_marks(mod, mk) if kind == 'pp' else ns_marks(mod, mk))
    clip_list = C.all_clips(kind, tuple(mk.meta.get('drone_axis', (0, 1, 0))))
    if 'qa' in ARGS:
        sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts')); import qa_check
        res = qa_check.run(objects=[o.name for o in mk.root.children_recursive if o.type == 'MESH'], profile='game', eps=0.0008, tol=0.004)
        print('QA_PASS', which, res['pass'], 'errors', len(res['errors'])); [print('QA_ERROR', e) for e in res['errors']]
    key_clips(mk, mod, clip_list)
    meta = dict(mk.meta); meta.pop('marks', None); meta.pop('wing_layout', None)
    meta.update({'phase': 'rig (concept meshes, Tripo meshes swap in)', 'fps': C.FPS, 'marks': marks, 'root_motion': False,
                 'clips': [{k: cl[k] for k in ('name', 'dur', 'loop', 'hold', 'partial', 'note')} for cl in clip_list]})
    mk.root['jf'] = json.dumps(meta)
    print('JF_CLIPS', which, len(clip_list), ' '.join(cl['name'] for cl in clip_list))
    if 'no-export' not in ARGS: export(mk, os.path.join(lib.MODELS, f'x_mech_{which}.glb'))
    return mk


if __name__ == '__main__':
    for m in ([ARGS['mech']] if 'mech' in ARGS else ['paperplane', 'nightshift']): main(m)
