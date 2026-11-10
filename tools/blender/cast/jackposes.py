# PALLET JACK posed in Blender with the game's own clip numbers (pj_clips.py): the scale line-up, the pose sheet and the
# per-clip contact sheets. make_cast_pallet_jack.py calls run() for --sheet=scale,poses,clips.
# The model is hung on one empty per joint (the game's joint tree); the moving pieces turn and slide about their pivots
# the way public/js/story/palletjack.js moves them; the stand-in face is rebuilt for the face each clip asks for.
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jackrig import *  # noqa
import pj_clips

FACES = {'neutral': dict(lid=1, jaw=0, st=1, smile=0.2, by=0, bt=0), 'grin': dict(lid=0.75, jaw=0.3, st=1.85, smile=1, by=0.02, bt=-0.12), 'squint': dict(lid=0.32, jaw=0, st=0.9, smile=0, by=-0.012, bt=0.28),
         'sad': dict(lid=0.65, jaw=0.05, st=0.85, smile=-0.8, by=0.01, bt=-0.5), 'shock': dict(lid=1.25, jaw=0.9, st=0.75, smile=0, by=0.035, bt=-0.1), 'angry': dict(lid=0.62, jaw=0.1, st=1.1, smile=-0.6, by=-0.015, bt=0.55),
         'jack': dict(lid=0.7, jaw=0, st=1.05, smile=0.5, by=-0.003, bt=-0.3), 'jack_hurt': dict(lid=0.5, jaw=0.16, st=0.95, smile=-0.25, by=0.004, bt=-0.55), 'jack_gone': dict(lid=0.06, jaw=0.12, st=0.95, smile=0.1, by=0, bt=-0.2)}
POSES = [('pj_idle', 1.0, 35, 'fresh', True), ('pj_idle_eating', 1.85, 40, 'fresh', False), ('pj_walk_load', 1.0, 35, 'fresh', False), ('pj_kneel_vest', 3.7, 50, 'fresh', True), ('pj_rig_up', 2.12, 35, 'fresh', False),
         ('pj_rocket_punch', 0.44, 60, 'fresh', False), ('pj_rocket_punch', 0.56, 60, 'fresh', False), ('pj_block', 0.4, 35, 'fresh', False), ('pj_stagger', 0.3, 60, 'fresh', False), ('pj_impaled', 1.2, 60, 'run_through', False),
         ('pj_impaled', 3.6, 40, 'run_through', False), ('pj_break_it', 2.95, 40, 'run_through', False), ('pj_land_kneel', 0.6, 50, 'run_through', False), ('pj_stand_anyway', 3.3, 35, 'run_through', False),
         ('pj_fight_idle_hurt', 1.0, 35, 'run_through', False), ('pj_armour_break_fall', 0.2, 60, 'armour_broken', False), ('pj_armour_break_fall', 2.2, 50, 'armour_broken', False), ('pj_dying_talk', 4.6, 45, 'armour_broken', False),
         ('pj_last_breath', 3.6, 45, 'armour_broken', False), ('pj_carried', 0.0, 60, 'marrow_taken', False)]


def pose_of(name, t):
    """clip channels -> {joint: {r, p}} on top of the standing pose the game gives him, and the machine's 0..1 values"""
    ch = pj_clips.evaluate(name, t) if name else dict(pj_clips.REST)
    hunch = JOINTS[ID]['hunch']
    R = {j: [0.0, 0.0, 0.0] for j, _ in ORDER}; Pp = {j: [0.0, 0.0, 0.0] for j, _ in ORDER}
    R['spine'][0] = hunch
    for k, v in pj_clips.REST.items():
        j, a = k.split('.'); R[j]['xyz'.index(a)] = v
    x = {}
    for k, v in ch.items():
        j, a = k.split('.')
        if j == 'x': x[a] = v; continue
        if len(a) == 2: Pp[j]['xyz'.index(a[1])] += v; continue
        i = 'xyz'.index(a)
        if any(k.startswith(p) for p in pj_clips.ABS): R[j][i] = v
        else: R[j][i] += v
    return {j: {'r': R[j], 'p': Pp[j]} for j, _ in ORDER}, x


class Posed:
    def __init__(s, root, G):
        s.root = root; s.G = G
        s.face = []
        s.E = pose_rig(ID, root)
        s.E['root'].scale = (G['SCALE'],) * 3
        s.mov = {}
        for o in [c for k, e in s.E.items() if k not in ('rest', 'root') for c in e.children]:
            if o.type != 'MESH': continue
            t = G['tag_of'](o)
            if t in ('stackL', 'stackR', 'flapL', 'flapR', 'lockL', 'lockR', 'cock', 'needle'): s.mov[t] = (o, o.matrix_local.copy())
        s.marks = G['J'].marks; s.vals = G['J'].vals

    def set_face(s, name):
        for o in s.face: bpy.data.objects.remove(o, do_unlink=True)
        s.face = standin_face(ID, s.G['FACE_OPTS'], FACES.get(name, FACES['jack']))
        bpy.context.view_layer.update()
        # built at the rest pose in root space: hang them on the head joint as it is at rest
        rest_head = castlib.joint_matrix(ID, 'head')
        for o in s.face:
            apply_mods(o)
            o.parent = s.E['head']; o.matrix_parent_inverse = rest_head.inverted()
        return s.face

    def machine(s, x):
        def axis_obj(tag):
            jn, pv, ax = s.marks[tag][0], s.marks[tag][1], s.marks[tag][2]
            return (castlib.joint_matrix(ID, jn).to_3x3() @ gv(*ax)).normalized()
        seg = lambda t, a, b: smooth01(t, a, b)
        rig = x.get('rig', 0.0); flap = x.get('flap', 0.0); cock = x.get('cock', 0.0)
        for tag, (o, m0) in s.mov.items():
            D = Matrix.Identity(4)
            if tag in ('lockL', 'lockR'):
                D = Matrix.Rotation(s.vals[tag]['shut'] * (seg(rig, 0.02, 0.35) if tag == 'lockL' else seg(rig, 0.36, 0.7)), 4, axis_obj(tag))
            elif tag in ('stackL', 'stackR'): D = Matrix.Translation(axis_obj(tag) * (STACK_RISE * seg(rig, 0.7, 1.0)))
            elif tag in ('flapL', 'flapR'):
                D = Matrix.Translation(axis_obj('stack' + tag[-1]) * (STACK_RISE * seg(rig, 0.7, 1.0))) @ Matrix.Rotation(1.2 * flap, 4, axis_obj(tag))
            elif tag == 'cock': D = Matrix.Translation(axis_obj(tag) * (COCK_PULL * cock))
            o.matrix_local = m0 @ D

    def pose(s, name, t, state='fresh', vest=False, face=None):
        P_, x = pose_of(name, t)
        apply_pose(s.E, P_)
        s.machine(x)
        st = s.G['STATES'][state]
        fc = face
        if not fc and name:
            fc = 'jack'
            for ft, fn in pj_clips.CLIPS[name]['face']:
                if t >= ft: fc = fn
        s.set_face(fc or 'jack')
        # show_only works on root.children; the parts hang on the joint empties now
        for e in s.E.values():
            if not hasattr(e, 'children'): continue
            for o in e.children:
                if o.type != 'MESH' or o.get('standin'): continue
                tg = s.G['tag_of'](o)
                if tg == 'lod' or tg.endswith('Far'): vis = False
                elif tg.startswith('dmg'): vis = tg in st['on']
                elif tg == 'vest': vis = vest
                else: vis = tg not in st['off']
                o.hide_render = not vis; o.hide_viewport = not vis
        bpy.context.view_layer.update()
        return x

    def hips(s):
        w = s.E['spine'].matrix_world.translation
        return (w.x, w.z, -w.y)


def import_cast(cid, x):
    """another cast model beside him at its own size, for scale"""
    path = os.path.join(MODELS, 'cast', 'c_%s.glb' % cid)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    top = [o for o in new if o.parent is None]
    sc = JOINTS[cid]['scale']
    for o in top:
        o.scale = (o.scale.x * sc, o.scale.y * sc, o.scale.z * sc); o.location = o.location + gv(x, 0, 0)
    for o in new:
        if o.type == 'MESH' and ('__lod' in o.name or '__dmg' in o.name): o.hide_render = True
    return new


def workbench(res):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_shadows = True; sh.show_cavity = True; sh.show_object_outline = True
    sc.display.render_aa = '5'
    sc.render.resolution_x, sc.render.resolution_y = res
    return sc


def wb_shot(path, target, deg, dist, lens=60, up=0.1, res=(300, 340)):
    sc = workbench(res)
    a = math.radians(deg)
    d = Vector((math.sin(a), math.cos(a), up)).normalized(); t = gv(*target); pos = t + d * dist
    cam = bpy.data.objects.new('pc', bpy.data.cameras.new('pc')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = lens; cam.data.clip_start = 0.05; cam.data.clip_end = 200
    cam.location = pos; cam.rotation_euler = (t - pos).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    return path


def run(J, root, fo, sheets, SHEET_DIR, TMP, G):
    os.makedirs(TMP, exist_ok=True)
    G = dict(G); G['J'] = J
    for o in fo: bpy.data.objects.remove(o, do_unlink=True)
    PD = Posed(root, G)
    S = G['SCALE']
    if 'scale' in sheets:
        PD.pose('pj_idle', 1.0, 'fresh', vest=True)
        import_cast('mannequin', -1.75); import_cast('lumps', 2.0)
        tr = None
        tp = os.path.join(MODELS, 'story', 's_handtruck.glb')
        if os.path.exists(tp):
            before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=tp)
            tr = [o for o in bpy.data.objects if o not in before and o.parent is None]
            mw = PD.E['handL'].matrix_world @ Matrix.Translation(gv(0, -0.1, 0.042))
            for o in tr: o.location = Vector((mw.translation.x, mw.translation.y + 0.05, 0))
        studio(2.3, gv(0.1, 1.1, 0), key=1.0); floor_disc(4.0)
        ps = [cam_shot(os.path.join(TMP, 'pj_s%d.png' % i), (0.1, 1.1, 0), deg, 9.6, lens=60, res=(640, 400), samples=10) for i, deg in enumerate((0, 35, 180, 215))]
        rpkit.contact(ps, os.path.join(SHEET_DIR, 'c_pallet_jack_scale'), 'the mannequin (the player\'s size)   PALLET JACK, a hand on his truck   LUMPS      at their sizes in the game', cols=2,
                      labels=['front', 'three quarter', 'back', 'three quarter back'])
        for o in bpy.data.objects:
            if o.name.startswith('cast_') and o is not root and o.name not in ('cast_' + ID,): pass
    if 'poses' in sheets:
        studio(2.0, gv(0, 1.0, 0), key=1.0); floor_disc(4.0)
        ps = []; labs = []
        for i, (name, t, deg, state, vest) in enumerate(POSES):
            PD.pose(name, t, state, vest)
            h = PD.hips()
            ps.append(cam_shot(os.path.join(TMP, 'pj_q%d.png' % i), (h[0], max(0.8, h[1] * 0.75 + 0.3), h[2]), deg, 8.6, lens=60, res=(300, 340), samples=8, up=0.1))
            labs.append('%s %.2f' % (name[3:], t))
        rpkit.contact(ps, os.path.join(SHEET_DIR, 'c_pallet_jack_poses'), 'PALLET JACK  pose sheet: one key pose a clip (the game plays these same numbers)', cols=5, labels=labs)
    if 'clips' in sheets:
        only = arg('clip')
        for name in pj_clips.CLIPS:
            if only and name not in only.split(','): continue
            C = pj_clips.CLIPS[name]; ln = pj_clips.duration(name) or 1.0; N = 8
            ts = [ln * i / (N - 1) for i in range(N)]
            state = dict((p[0], p[3]) for p in POSES).get(name, 'fresh')
            ps = []; labs = []
            for i, t in enumerate(ts):
                st = state
                if 'impaled' in name: st = 'run_through' if t >= 0.05 else 'fresh'
                if 'armour_break' in name: st = 'armour_broken' if t >= 0.06 else 'run_through'
                PD.pose(name, t, st, vest=(name in ('pj_idle', 'pj_walk_load') or (name == 'pj_kneel_vest' and t < 1.75)))
                ps.append(wb_shot(os.path.join(TMP, 'pj_c%d.png' % i), (0, 1.0, 0.1), 55 if any(k in name for k in ('eating', 'kneel', 'dying', 'last', 'carried', 'fall')) else 40, 9.6, res=(300, 330)))
                mk = ' '.join(m for mt, m in C['marks'] if abs(mt - t) < ln / (N - 1) / 2)
                labs.append('%.2f %s' % (t, mk))
            rpkit.contact(ps, os.path.join(SHEET_DIR, 'c_pallet_jack_clip_' + name[3:]), 'PALLET JACK  %s   %s' % (name, C['note'][:90]), cols=4, labels=labs)
