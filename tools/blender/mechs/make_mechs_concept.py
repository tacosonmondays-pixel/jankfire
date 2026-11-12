# The mech concept pass (phase 1): both frames built, checked, exported and drawn for the owner's look approval.
#   blender52 -b -P tools/blender/mechs/make_mechs_concept.py -- mech=paperplane   (or nightshift): the asset-QA gate,
#       docs/mechs/concept/<fid>_concept.glb + <fid>_poses.json (the stances as three.js quaternions per joint), the
#       turnaround panels and docs/mechs/concept/<name>_turnaround.jpg
#   blender52 -b -P tools/blender/mechs/make_mechs_concept.py -- stage=combine: both mechs + the Overdrive Rig + a
#       1.8 m mannequin: mechs_scale.jpg, mechs_silhouette_30m.jpg, mechs_colours.jpg, mechs_hero.jpg
#   flags: spp=<samples> (default 40), only=<panel,...>, no-qa, no-export
import os, sys, json, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mechkit import *

ARGS = dict(a.split('=', 1) if '=' in a else (a, '1') for a in (sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []))
OUT = os.path.join(ROOT, 'docs', 'mechs', 'concept')
TMP = os.path.join(OUT, '_tmp')
SPP = int(ARGS.get('spp', 40))
ONLY = set(ARGS['only'].split(',')) if 'only' in ARGS else None
os.makedirs(TMP, exist_ok=True)
NAMES = {'paperplane': 'PAPER PLANE', 'nightshift': 'NIGHT SHIFT'}
W, H = 640, 820


def want(k): return ONLY is None or k in ONLY


def qa_gate(mk, tag):
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    objs = [o.name for o in mk.root.children_recursive if o.type == 'MESH']
    res = qa_check.run(objects=objs, profile='game', eps=0.0008, tol=0.004)
    tris = sum(m['tris'] for m in res['objects'].values())
    print('QA_PASS', tag, res.get('pass'), 'tris', tris, 'errors', len(res.get('errors', [])), 'warnings', len(res.get('warnings', [])))
    for e in res.get('errors', []): print('QA_ERROR', tag, e)
    if 'zf' in ARGS: zf_where([o for o in mk.root.children_recursive if o.type == 'MESH'])
    for e in res.get('warnings', []): print('QA_WARNING', tag, e)
    return res


def zf_where(objs, eps=0.0008):
    """where the z-fighting is (the QA gate names only the meshes): middles of coplanar, same-facing, overlapping
    triangle pairs in game coordinates (from make_heli.py)"""
    Vv, Tr, Nn = [], [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for o in objs:
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); b = len(Vv); mw = o.matrix_world; rm = mw.to_3x3()
        Vv += [mw @ v.co for v in me.vertices]
        for t in me.loop_triangles: Tr.append(tuple(b + i for i in t.vertices)); Nn.append((rm @ t.normal).normalized())
        o.evaluated_get(dg).to_mesh_clear()
    bvh = BVHTree.FromPolygons(Vv, Tr, epsilon=0.0); seen = set(); n = 0
    for ti, t in enumerate(Tr):
        a, b, c = (Vv[i] for i in t); cen = (a + b + c) / 3
        for p in (cen, cen.lerp(a, .6), cen.lerp(b, .6), cen.lerp(c, .6)):
            for _, _, tj, _ in bvh.find_nearest_range(p, eps):
                if tj is None or tj == ti or set(t) & set(Tr[tj]) or Nn[ti].dot(Nn[tj]) < 0.999: continue
                a2, b2, c2 = (Vv[i] for i in Tr[tj]); n2 = Nn[tj]; q = p - n2 * n2.dot(p - a2)
                k = (min(ti, tj), max(ti, tj))
                if k not in seen and all((v - u).cross(q - u).dot(n2) >= -1e-9 for u, v in ((a2, b2), (b2, c2), (c2, a2))):
                    seen.add(k); n += 1
                    if n < 400: print('QA_ZF_AT', [round(x, 3) for x in g_of(cen)], 'normal', [round(x, 2) for x in g_of(Nn[ti])])


def neutral_lights(focus, size):
    """turnaround light: even, no coloured rims (whites stay white from every side)"""
    studio(focus, size, rim=False)
    f = gv(*focus); k = size / 6.0
    for loc in ((-6, 5, 9), (7, 5, 8)):
        L = bpy.data.lights.new('jf_l', 'AREA'); L.energy = 1600 * k * k; L.size = 6 * k
        ob = lib._link(bpy.data.objects.new('jf_l', L)); ob.location = f + gv(*loc) * k; lib._look_at(ob, f); SET.append(ob)


def panel_png(name): return os.path.join(TMP, name + '.png')


def mech_stage(which):
    lib.reset(); lib._mats.clear()
    mod = importlib.import_module(which)
    mk = mod.build(); mk.build_tree(merge='nomerge' not in ARGS)
    fid, h = mk.fid, mk.meta['height']
    if 'no-qa' not in ARGS: qa_gate(mk, fid)
    poses = {k: {} for k in mod.POSES}
    for k, fn in mod.POSES.items():
        P = fn(mk); mk.pose(P); poses[k] = {'joints': mk.game_quats(), 'root_at': list(P.get('root_at') or (0, 0, 0))}
    mk.pose({})
    if 'no-export' not in ARGS:
        mk.meta['poses'] = sorted(poses)
        mk.root['jf'] = json.dumps(mk.meta)
        mk.export(os.path.join(OUT, f'{fid}_concept.glb'))
        with open(os.path.join(OUT, f'{fid}_poses.json'), 'w') as f: json.dump({'id': fid, 'euler_order': 'XYZ', 'poses': poses}, f, indent=1)
    # turnaround: rest pose orthos (front, the right side, back), the stance in 3/4 in both colours, one extra
    cycles(SPP, (W, H)); sc = bpy.context.scene
    span = 6.9 if which == 'paperplane' else 7.4
    cells, caps = [], []
    if want('turn'):
        neutral_lights((0, h / 2, 0), h)
        cy = span / 2 - 0.25  # (feet near the bottom edge, the wing tips inside the top)
        for v, loc in (('front', (0, cy, -40)), ('side', (40, cy, 0)), ('back', (0, cy, 40))):
            camera(loc, (0, cy, 0), ortho=span * 1.0, clip=(1, 200))
            render(panel_png(f'{which}_{v}')); cells.append(panel_png(f'{which}_{v}')); caps.append({'front': 'front', 'side': 'side (its right)', 'back': 'back'}[v])
        clear_set()
    if not want('turn'): clear_set(); return  # (the QA gate / export only)
    studio((0, h / 2, 0), h)
    mk.pose(mod.POSES['ready'](mk))
    for col, pal in (('A', None), ('B', mod.PAL_B)):
        if pal: mk.M.recolour(pal)
        camera((-6.2, h * 0.58, -9.6), (0, h * 0.47, 0), 42)
        render(panel_png(f'{which}_q{col}')); cells.append(panel_png(f'{which}_q{col}'))
    pa = {k: mod.PAL_A[k] for k in mod.PAL_B}; mk.M.recolour(pa)
    caps += ['stance, colour A: ' + ('sky mail' if which == 'paperplane' else 'graveyard shift'), 'colour B: ' + ('pink slip' if which == 'paperplane' else 'overtime')]
    if which == 'paperplane':
        mk.pose(mod.POSES['jet'](mk))
        camera((-5.6, 4.9, -6.2), (0, 2.0, 0.2), 36)
        render(panel_png(f'{which}_jet')); cells.append(panel_png(f'{which}_jet')); caps.append('jet mode (wings swing down flat)')
    else:
        mk.pose({})
        camera((-1.6, 5.0, -3.6), (0.0, 4.95, -0.1), 45)
        render(panel_png(f'{which}_detail')); cells.append(panel_png(f'{which}_detail')); caps.append('helm, beacon, hi-vis')
    # hero (path traced, wider)
    if want('hero'):
        mk.pose(mod.POSES['ready'](mk)); sc.render.resolution_x, sc.render.resolution_y = 1280, 720; sc.cycles.samples = SPP * 2 if sc.cycles.use_denoising else SPP * 6
        camera((-6.2, h * 0.42, -10.4), (0.25, h * 0.55, 0), 32)
        render(panel_png(f'{which}_hero')); px = load_px(panel_png(f'{which}_hero'))
        save_jpg(np.concatenate([label_bar(1280, f'{NAMES[which]}  concept  {h:.1f} m  {mk.tris()} tris (blockout)'), px], 0), os.path.join(OUT, f'{which}_hero.jpg'), 2)
    clear_set()
    tile([load_px(p) for p in cells], 3, f'{NAMES[which]}  concept turnaround  ({h:.2f} m to the helmet, {mk.tris()} tris)', os.path.join(OUT, f'{which}_turnaround.jpg'), caps=caps)


# ------------------------------------------------------------ the combined sheets
def mannequin(x, z, m):
    """a 1.8 m stand-in for the game's mannequin (boxes and a ball, the same proportions)"""
    P = [hull([(x + a, y, z + c) for a in (-0.11, 0.11) for y in (0.0, 0.10) for c in (-0.16, 0.12)], m, 0.02, name='mq')]
    for s in (-1, 1):
        P.append(frustum((x + s * 0.11, 0.08, z), (x + s * 0.12, 0.92, z), 0.085, 0.10, m, 8, name='mq'))
        P.append(frustum((x + s * 0.30, 1.48, z), (x + s * 0.34, 0.80, z), 0.075, 0.06, m, 8, name='mq'))
    P.append(hull([(x + a, y, z + c) for (a, y) in ((-0.24, 0.92), (0.24, 0.92), (-0.30, 1.52), (0.30, 1.52)) for c in (-0.13, 0.13)], m, 0.03, name='mq'))
    P.append(frustum((x, 1.50, z), (x, 1.58, z), 0.06, 0.06, m, 8, name='mq'))
    P.append(ball((x, 1.69, z), 0.115, m, 16, 10, 'mq'))
    return P


def ruler(x, top, m_a, m_b):
    R = []
    for i in range(int(top)):
        R.append(hull([(x + a, y, c) for a in (-0.06, 0.06) for y in (i, i + 1) for c in (-0.06, 0.06)], m_a if i % 2 == 0 else m_b, 0.0, name='ruler'))
    return R


def combine():
    lib.reset(); lib._mats.clear()
    pp_mod, ns_mod = importlib.import_module('paperplane'), importlib.import_module('nightshift')
    pp = pp_mod.build(); pp.build_tree()
    ns = ns_mod.build(); ns.build_tree()
    grey = lib.mat('jf_mq', 0x9aa0aa, rough=0.5); grey2 = lib.mat('jf_mq2', 0xff4fd8, rough=0.5)
    ry, rb = lib.mat('jf_ruler_y', 0xffe14d, rough=0.5), lib.mat('jf_ruler_k', 0x202028, rough=0.5)
    bpy.ops.import_scene.gltf(filepath=os.path.join(lib.MODELS, 'x_rig.glb'))
    rig = [o for o in bpy.context.selected_objects]
    rig_root = next(o for o in rig if o.parent is None)
    MQ = mannequin(0, 0, grey)
    RU = ruler(0, 7, ry, rb)
    groups = {'mq': MQ, 'rig': rig, 'ruler': RU, 'pp': pp.objects(), 'ns': ns.objects()}
    def place(objs_or_mk, x, z=0.0, yaw=0.0):
        if isinstance(objs_or_mk, Mech): objs_or_mk.base = ((x, 0, z), yaw); return
        for o in objs_or_mk:
            if o.parent is None: o.location = o.location + gv(x, 0, z)
    def show(*keys):
        for k, objs in groups.items():
            for o in objs: o.hide_render = k not in keys
    sc = bpy.context.scene
    # 1) scale: front ortho line-up next to a ruler (1 m bands)
    if want('scale'):
        # (the camera looks from the front, so screen-right is -x: line them up toward -x to read left to right)
        place(RU, 1.7); place(MQ, 0.7); place(rig, -0.9); pp.base = ((-4.1, 0, 0), 0); ns.base = ((-8.6, 0, 0), 0)
        pp.pose({}); ns.pose({})
        show('mq', 'rig', 'ruler', 'pp', 'ns')
        cycles(SPP, (1920, 1000)); neutral_lights((-3.6, 3, 0), 7)
        camera((-4.05, 3.25, -60), (-4.05, 3.25, 0), ortho=14.4, clip=(1, 200))
        render(panel_png('scale_front'))
        pp.pose(pp_mod.POSES['ready'](pp)); ns.pose(ns_mod.POSES['ready'](ns))
        clear_set(); studio((-3.6, 3, 0), 7)
        camera((4.0, 3.4, -17.5), (-3.6, 2.6, 0), 32)
        render(panel_png('scale_q'))
        clear_set()
        a, b = load_px(panel_png('scale_front')), load_px(panel_png('scale_q'))
        cap = ['mannequin 1.8', 'overdrive rig 2.9', 'paper plane 4.9', 'night shift 5.7']
        sheet = np.concatenate([label_bar(1920, 'scale in m (ruler bands = 1 m): ' + ' / '.join(cap)), a, label_bar(1920, 'the same line-up in their stances', 0x4fd8ff), b], 0)
        save_jpg(sheet, os.path.join(OUT, 'mechs_scale.jpg'), 2)
    # 2) silhouettes at 30 m: flat black, the game's default view (95 degree vertical FOV, 1920x1080)
    if want('sil'):
        sc.render.engine = 'BLENDER_WORKBENCH'
        sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'SINGLE'; sh.single_color = (0, 0, 0)
        sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
        w = bpy.data.worlds.new('sil'); sc.world = w; w.color = (0.62, 0.66, 0.72)
        sc.view_settings.view_transform = 'Standard'
        cam = camera((0, 1.7, -30), (0, 2.6, 0), 50)
        cam.data.sensor_fit = 'VERTICAL'; cam.data.angle_y = math.radians(95)
        subjects = [('pp', 'rest', 0.0, 'paper plane front'), ('pp', 'ready', 0.6, 'paper plane 3/4'), ('pp', 'rest', math.pi / 2, 'paper plane side'),
                    ('pp', 'jet', 0.7, 'paper plane jet'), ('ns', 'rest', 0.0, 'night shift front'), ('ns', 'ready', 0.6, 'night shift 3/4'),
                    ('ns', 'rest', math.pi / 2, 'night shift side'), ('rig', None, 0.6, 'overdrive rig'), ('mq', None, 0.3, 'mannequin 1.8 m')]
        small, big, caps = [], [], []
        place(RU, 1.6); place(MQ, 0.6); place(rig, -1.0)  # (back to the middle)
        rr = rig_root.rotation_euler.copy()
        for k, pose, yaw, cap in subjects:
            show(k)
            for m_, mod_ in ((pp, pp_mod), (ns, ns_mod)):
                if (k == 'pp' and m_ is pp) or (k == 'ns' and m_ is ns):
                    m_.base = ((0, 0, 0), yaw); m_.pose(mod_.POSES[pose](m_))
            if k == 'rig': rig_root.rotation_euler = (rr[0], rr[1], rr[2] + yaw)
            if k == 'mq':
                for o in MQ: o.rotation_euler = (0, 0, yaw)
            p = panel_png(f'sil_{len(small)}'); render(p); px = load_px(p)
            cy, cx = 1080 // 2 - 22, 1920 // 2
            crop = px[cy - 80:cy + 80, cx - 80:cx + 80].copy()
            small.append(crop); caps.append(cap)
            big.append(np.kron(crop, np.ones((3, 3, 1), np.float32)))
        rig_root.rotation_euler = rr
        cell = canvas(480, 480, 0x9ea8b8)
        rows = []
        for c, b in zip(small, big):
            k = cell.copy(); k[:, :] = b[:480, :480]; k[8:168, 8:168] = c; border(k[8:168, 8:168], 1, 0xff4fd8)
            rows.append(k)
        tile(rows, 5, 'silhouettes at 30 m in the default view (fov 95, 1080p): inset = real pixels, big = 3x', os.path.join(OUT, 'mechs_silhouette_30m.jpg'), caps=caps)
        for o in MQ: o.rotation_euler = (0, 0, 0)
    # 3) colour options: the four stance renders from the per-mech stage
    if want('colours'):
        cells = [load_px(panel_png(n)) for n in ('paperplane_qA', 'paperplane_qB', 'nightshift_qA', 'nightshift_qB')]
        tile(cells, 4, 'colour options: paper plane (sky mail / pink slip), night shift (graveyard shift / overtime)', os.path.join(OUT, 'mechs_colours.jpg'),
             caps=['paper plane A sky mail', 'paper plane B pink slip', 'night shift A graveyard shift', 'night shift B overtime'])
    # 4) the two together
    if want('duo'):
        show('pp', 'ns'); pp.base = ((-2.4, 0, -0.4), 0.25); ns.base = ((2.6, 0, 0.5), -0.3)
        pp.pose(pp_mod.POSES['ready'](pp)); ns.pose(ns_mod.POSES['ready'](ns))
        cycles(SPP * 2, (1600, 900)); studio((0, 3, 0), 7)
        camera((-1.5, 3.2, -15.5), (0.2, 2.9, 0), 36)
        render(panel_png('duo')); px = load_px(panel_png('duo'))
        save_jpg(np.concatenate([label_bar(1600, 'PAPER PLANE + NIGHT SHIFT  concept (blockout + paint)'), px], 0), os.path.join(OUT, 'mechs_duo.jpg'), 2)


if __name__ == '__main__':
    st = ARGS.get('stage', 'mech')
    if st == 'combine': combine()
    else: mech_stage(ARGS.get('mech', 'paperplane'))
