# THE TRAIN SET of OVERDUE's Act I boss fight (m06 TICKETS, PLEASE): Dale's works train, the Under-Hill Loop's tunnel,
# the dead commuter train on the next track, the tunnel mouth. Everything original, from real kinds of thing (see the
# notes at the top of rptrain_cars.py, rptunnel.py, rpcommuter.py). Built to THE TABLE in shared/story/train.js.
#
# Arena space = game metres: x across, y up from the track bed, z from the back of the train (0) to the loco.
#
# rp_train.glb
#   car_wagon   wagon_body · wagon_tail (the lamp's lit lens) · wagon_coupling (bar, fall plate, chains: goes with it)
#               · cover_wagon_0 / _1 · wagon_lod (hidden)
#   car_flat    flat_body · flat_end (its back, whole) · flat_end_bitten (hidden: after the first lunge) ·
#               flat_van_coupling · cover_flat_0..3 (the fridge is one) · flat_lod (hidden)
#   car_van     van_body · van_lamp (the flood's lit head, the lantern) · van_loco_coupling · cover_van_0 / _1 · van_lod
#   car_loco    loco_body · loco_glass · loco_headlamp (the one that works) · loco_lod (hidden)
#   every cover_* has its origin in the middle of its foot: put it at its COVER line's (x, deck, z)
# rp_tunnel.glb / rp_commuter.glb: see rptunnel.py and rpcommuter.py. rp_train.parts.json: boxes and markers.
#
# run: blender52 -b -P tools/blender/make_rp_train.py
#      flags after '--': --only=train,tunnel,commuter --no-export --no-sheet --no-ao --qa --stats
#      --preview=<dir> --views=turn,wagon,... (quick looks)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trainkit import *
from lib import _link, _image
import rptrain_tex as TX
from rptrain_tex import M, AT

OUT = os.path.join(MODELS, 'story')
ONLY = set(arg('only').split(',')) if isinstance(arg('only'), str) else None
def want(k): return ONLY is None or k in ONLY


def mk(kit, name, parent, pivot=None, hide=False, sharp=50):
    if not kit.F: return None
    o = kit.obj(sharp=sharp); apply_mods(o)
    return node(o, name, pivot, parent, hide)


def build_train(N):
    import rptrain_cars as RC
    root = empty('rp_train'); N['rp_train'] = root
    cars = {k: empty('car_' + k, root) for k in ('wagon', 'flat', 'van', 'loco')}
    for k, e in cars.items(): N['car_' + k] = e
    for car, fn in (('wagon', RC.wagon_bits), ('flat', RC.flat_bits), ('van', RC.van_bits), ('loco', RC.loco_bits)):
        for name, kit in fn().items():
            o = mk(kit, name, cars[car], hide=name.endswith('_bitten'))
            if o: N[name] = o
    for name, car, kit, pivot in RC.build_covers():
        N[name] = mk(kit, name, cars[car], pivot)
    if not arg('no-lod'):
        for car, kit in RC.lod_bits().items(): N[car + '_lod'] = mk(kit, car + '_lod', cars[car], hide=True)
    return root, RC


# ------------------------------------------------------------ pictures
def studio(key=9000, amb=0.5, c=(0, 2, 16), span=20):
    world(0x1a1220, amb)
    area(key, (c[0] + span * 0.6, c[1] + span * 0.7, c[2] - span * 0.5), c, span * 0.6, (1.0, 0.97, 0.92))
    area(key / 3, (c[0] - span * 0.7, c[1] + span * 0.3, c[2] + span * 0.4), c, span * 0.7, (0.8, 0.88, 1.0))
    area(key / 3.4, (c[0] - span * 0.2, c[1] + span * 0.8, c[2] + span * 0.6), c, span * 0.5, (1.0, 0.8, 0.9))
    area(key / 6, (c[0], c[1] - 2, c[2] - span), c, span * 0.5, (1.0, 0.9, 0.8))


SET = []
def scale_set(on=True, ring_z=-0.6, man_at=(0.9, 1.0, 1.2), floor=True):
    """the pictures' scale: a ring the size of the bore, the track bed, a 1.8 m figure"""
    import rptrain_cars as RC
    for o in SET:
        try: bpy.data.objects.remove(o, do_unlink=True)
        except ReferenceError: pass
    SET.clear()
    if not on: return
    m = mat('jf_set_ring', 0xff4fd8, rough=0.6, emit=0xff4fd8, strength=0.6); m2 = mat('jf_set_floor', 0x2a2228, rough=0.9); m3 = mat('jf_set_man', 0x4fd8ff, rough=0.6, emit=0x4fd8ff, strength=0.25)
    b = TBuf('jf_set_ring'); k = 64; R_ = RC.BORE_R; cy = RC.CY
    R = [[V3((math.cos(2 * math.pi * j / k) * r_, cy + math.sin(2 * math.pi * j / k) * r_, ring_z + z)) for j in range(k)] for r_, z in ((R_, -0.06), (R_ + 0.12, -0.06), (R_ + 0.12, 0.06), (R_, 0.06), (R_, -0.06))]
    b.add(p_loft(R), m, ('tile', 1.0)); SET.append(b.obj(wn=False))
    if floor:
        b = TBuf('jf_set_floor'); hw = math.sqrt(R_ ** 2 - cy ** 2)
        b.add(bx(-hw, -0.08, -4, hw, 0.0, 37), m2, ('tile', 1.0)); SET.append(b.obj(wn=False))
    if man_at:
        b = TBuf('jf_set_man'); figure(b, m3, man_at, 1.8, math.pi); SET.append(b.obj(wn=False))
    for o in SET: flat_ao(o); final_colour(o)


VIEWS = {  # name: (camera, target, lens or ('o', ortho scale), exposure)
    'turn_q': ((21, 11, -12), (0, 1.2, 15.5), 35, 0.0), 'turn_side': ((60, 2.2, 16.3), (0, 2.2, 16.3), ('o', 37), 0.0), 'turn_back': ((-9, 6, -11), (0, 1.5, 8), 32, 0.0), 'turn_front': ((10, 5, 44), (0, 1.8, 26), 32, 0.0),
    'turn_top': ((0.01, 60, 16.3), (0, 0, 16.3), ('o', 37), 0.0),
    'wagon': ((8.5, 5.2, -5.5), (0, 1.1, 4.7), 35, 0.0), 'wagon_in': ((0.3, 2.7, 8.6), (0.2, 1.2, 0.5), 22, 0.2), 'rail': ((3.4, 2.6, -2.6), (0.6, 1.5, 0.4), 40, 0.2),
    'flat': ((9.5, 6, 6.5), (0, 1.5, 14.8), 35, 0.0), 'flat_in': ((0.2, 3.0, 20.4), (-0.3, 1.6, 13.0), 22, 0.2), 'fridge': ((1.6, 2.8, 14.2), (-1.2, 2.2, 16.4), 35, 0.2),
    'van': ((9, 5.5, 16.5), (0, 2.3, 23.9), 35, 0.0), 'van_under': ((0.4, 2.9, 22.3), (0.0, 2.3, 26.5), 16, 0.5), 'van_roof': ((1.2, 5.3, 28.6), (0, 3.2, 20.5), 20, 0.1), 'van_steps': ((1.7, 3.0, 19.2), (-1.4, 2.4, 21.8), 28, 0.2),
    'van_board': ((0.6, 2.6, 25.6), (-1.5, 2.4, 22.8), 30, 0.6),
    'loco': ((9, 4.6, 37.5), (0, 1.8, 30.5), 35, 0.0), 'loco_back': ((3.6, 3.4, 23.2), (0, 2.1, 28.3), 30, 0.2), 'cab': ((0.9, 2.75, 28.0), (0.3, 2.2, 30.4), 20, 0.7), 'cab2': ((-1.9, 2.9, 27.2), (0.6, 2.0, 30.2), 30, 0.7),
    'loco_front': ((-4.5, 2.6, 38.0), (0, 1.6, 32.0), 35, 0.0), 'loco_side': ((60, 2.0, 30.5), (0, 2.0, 30.5), ('o', 7.5), 0.0), 'under': ((7.5, 0.9, 5.0), (0, 0.8, 9.5), 28, 0.6),
    'bitten': ((4.5, 4.2, 4.6), (0, 1.1, 10.2), 35, 0.2), 'bitten2': ((-1.0, 2.6, 13.4), (0.1, 1.0, 9.6), 24, 0.3),
    'covers': ((60, 1.0, 0), (0, 1.0, 0), ('o', 12), 0.0),
}


def rig(cam, tgt, key=1.0, amb=0.55):
    """lights hung round the camera for one picture: a key over its left shoulder, a cool fill from its right, a warm rim
    from behind the thing, a low bounce"""
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o, do_unlink=True)
    world(0x1a1220, amb); bpy.context.scene.eevee.light_threshold = 0.0006
    c, t = V3(cam), V3(tgt); v = t - c; D = max(4.0, v.length); f = v.normalized(); up = V3((0, 1, 0)); rt = f.cross(up).normalized(); E = 26.0 * D * D * key
    area(E, tuple(t - f * D * 0.55 + up * D * 0.75 - rt * D * 0.55), tuple(t), D * 0.5, (1.0, 0.97, 0.92))
    area(E / 3.2, tuple(t - f * D * 0.4 + up * D * 0.15 + rt * D * 0.9), tuple(t), D * 0.6, (0.8, 0.88, 1.0))
    area(E / 3.0, tuple(t + f * D * 0.7 + up * D * 0.7 + rt * D * 0.2), tuple(t), D * 0.5, (1.0, 0.8, 0.9))
    area(E / 7, tuple(t - f * D * 0.5 - up * D * 0.25), tuple(t), D * 0.5, (1.0, 0.9, 0.8))


def shoot(name, path, res=(960, 600), samples=12, ex=None, key=1.0):
    loc, tgt, lens, e = VIEWS[name] if isinstance(name, str) else name
    rig(loc, tgt, key * float(arg('key', 1.0))); ex = (e if ex is None else ex) + float(arg('ex', -1.0))
    if isinstance(lens, tuple): shot(path, loc, tgt, res=res, ortho=lens[1], exposure=ex, samples=samples)
    else: shot(path, loc, tgt, lens, res=res, exposure=ex, samples=samples)
    return path


def set_state(N, bitten=False, lod=False):
    for k, o in N.items():
        if o is None or o.type != 'MESH': continue
        hide = bool(o.get('jf_hidden'))
        if k.endswith('_lod'): hide = not lod
        elif lod and k.startswith(('wagon', 'flat', 'van', 'loco', 'cover')): hide = True
        elif k == 'flat_end_bitten': hide = not bitten
        elif k == 'flat_end': hide = bitten
        if bitten and o.parent and o.parent.name == 'car_wagon': hide = True
        o.hide_render = hide


def preview(N, pdir, views, bitten=False, res=(960, 600)):
    os.makedirs(pdir, exist_ok=True); colour_preview([m for m in M.values()])
    set_state(N, bitten, bool(arg('lod'))); scale_set(not arg('no-set')); out = []
    for v in views: out.append(shoot(v, os.path.join(pdir, f'tr_{v}{"_b" if bitten else ""}.png'), res, int(arg('samples', 10))))
    clear_studio(); scale_set(False); set_state(N)
    print('JF_PREVIEW', ' '.join(out))


# ------------------------------------------------------------ finishing
def bake_groups(N):
    meshes = {k: o for k, o in N.items() if o is not None and o.type == 'MESH'}
    for o in meshes.values(): o.hide_render = True
    for car in ('wagon', 'flat', 'van', 'loco'):
        grp = [o for k, o in meshes.items() if o.parent and o.parent.name == 'car_' + car and not o.get('jf_hidden')]
        solid = [o for o in grp if not o.name.endswith(('_glass', '_tail', '_lamp', '_headlamp'))]
        for o in grp: o.hide_render = False
        for o in grp:
            if o not in solid: o.hide_render = True
        if solid: bake_ao(solid, dist=0.5, samples=int(arg('ao', 20)), lo=0.34)
        for o in grp: o.hide_render = True
    if 'flat_end_bitten' in meshes:
        also = [meshes[k] for k in ('flat_body',) if k in meshes]
        for o in also: o.hide_render = False
        meshes['flat_end_bitten'].hide_render = False
        bake_ao([meshes['flat_end_bitten']], dist=0.4, samples=int(arg('ao', 20)), lo=0.4, also=also)
    for k, o in meshes.items():
        if k.endswith('_lod'): flat_ao(o)
    for o in meshes.values(): o.hide_render = False


def finish(N):
    meshes = [o for o in N.values() if o is not None and o.type == 'MESH']
    for o in meshes: o.data.validate(); o.data.update()
    bpy.context.view_layer.update()
    if not arg('no-ao'): bake_groups(N)
    for o in meshes:
        if 'AO' not in o.data.color_attributes: flat_ao(o)
        final_colour(o)


def parts_json(N, RC, tris):
    parts = []; bpy.context.view_layer.update()
    for k in sorted(N):
        o = N[k]
        if o is None or o.type != 'MESH': continue
        lo, hi = bounds([o])
        d = dict(name=k, centre=r3((lo + hi) / 2), half=r3((hi - lo) / 2), group=o.parent.name if o.parent else None, tris=tri_count(o), materials=[m.name for m in o.data.materials])
        if o.get('jf_hidden'): d['hidden'] = True
        if o.location.length > 1e-6: d['pivot'] = r3(g_of(o.matrix_world.translation))
        if k in RC.COVER_KIND: d.update(cover=RC.COVER_KIND[k]['i'], kind=RC.COVER_KIND[k]['kind'], box=RC.COVER_KIND[k]['box'])
        parts.append(d)
    I = RC.INFO
    meta = dict(
        id='rp_train', name="DALE'S WORKS TRAIN", units='metres, arena space: x across, y up from the track bed, z from the back of the train (0) to the loco',
        table=dict(HW=RC.HW, cars=RC.TB['CARS'], cover=RC.TB['COVER'], rail_y=RC.RAIL_Y, gauge=2 * RC.GAUGE, plank=RC.PL, note='the sizes this was built to (shared/story/train.js when it was built)'),
        cars={c: dict(node='car_' + c, body=c + '_body', lod=c + '_lod', z=[RC.CARS[c]['z0'], RC.CARS[c]['z1']], deck=RC.CARS[c]['deck']) for c in ('wagon', 'flat', 'van', 'loco')},
        tris=tris,
        states=dict(bitten=dict(hide=['car_wagon', 'flat_end'], show=['flat_end_bitten'], note='the first lunge: the wagon (its covers and coupling with it) goes, the flatbed shows its torn end')),
        markers=dict(
            crew=[dict(id=c['id'], pos=c['p']) for c in RC.TB['CREW']], back_rail=I.get('back_rail'), rail_sides=I.get('rail_sides'), couplings=I.get('couplings'),
            cab_seat=I.get('cab_seat'), brake_handle=I.get('brake_handle'), flask=I.get('flask'), kettle=I.get('kettle'), headlamp=I.get('headlamp'), headlamp_dead=I.get('headlamp_dead'),
            tail_lamp=I.get('tail_lamp'), work_lamp=I.get('work_lamp'), van_lantern=I.get('van_lantern'), fridge=I.get('fridge'), handtruck=I.get('handtruck'),
            van_roof=dict(y=RC.VAN.roof, x=[-RC.HW, RC.HW], z=[RC.VAN.roofZ0, RC.VAN.z1]), van_steps=dict(x=[-RC.HW, -RC.HW + RC.VAN.stairW], z=[RC.VAN.z0, RC.VAN.roofZ0], n=RC.VAN.stairs)),
        materials=dict(tr_atlas='everything painted, planked and steel (one 512 px atlas with a roughness / metal map)', tr_glass='the cab windows (blended)', tr_headlamp='the working head lamp (emissive)',
                       tr_tail='the tail lamp (emissive)', tr_worklamp='the flood on the van roof and the lantern under it (emissive)'),
        parts=parts)
    return meta


def sheet_train(N, tris):
    colour_preview([m for m in M.values()]); tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True); S = int(arg('samples', 12))
    want_ = arg('sheet'); want_ = set(want_.split(',')) if isinstance(want_, str) else None
    def sheet(tag, label, views, cols, res=(900, 560), bitten=False, lod=False, labels=None, ring=True, man=(0.9, 1.0, 1.2)):
        if want_ is not None and tag not in want_: return
        set_state(N, bitten, lod); scale_set(ring, man_at=man); out = []
        for v in views: out.append(shoot(v, os.path.join(tmp, f'{tag}_{len(out)}.png'), res, S))
        contact(out, os.path.join(SHEETS, 'rp_train_' + tag), label, cols=cols, labels=labels or [v.replace('_', ' ') if isinstance(v, str) else '' for v in views])
    sheet('turnaround', f"DALE'S WORKS TRAIN  {tris['whole']} TRIS  WAGON {tris['wagon']}  FLATBED {tris['flat']}  TOOL VAN {tris['van']}  LOCO {tris['loco']}  RING = THE 9.2 M BORE  FIGURE = 1.8 M",
          ['turn_q', 'turn_front', 'turn_side', 'turn_top'], 2, (1100, 560), labels=['from behind (the boss\'s side)', 'from the front', 'side', 'plan'])
    sheet('cars', 'THE FOUR CARS', ['wagon', 'flat', 'van', 'loco'], 2, labels=['rear wagon: drop sides, the rail', 'flatbed: crates, the fridge chained down', 'tool van: steps to a flat roof, open sides', 'the loco: more of a tractor'])
    scale_set(False); set_state(N); clear_studio()
    try: os.rmdir(tmp)
    except OSError: pass


def tri_stats(N):
    def grp(car, pred): return sum(tri_count(o) for k, o in N.items() if o is not None and o.type == 'MESH' and o.parent and o.parent.name == 'car_' + car and pred(k, o))
    t = {}
    for car in ('wagon', 'flat', 'van', 'loco'):
        t[car] = grp(car, lambda k, o: not o.get('jf_hidden') and not k.endswith('_lod')); t[car + '_lod'] = grp(car, lambda k, o: k.endswith('_lod'))
    t['whole'] = sum(t[c] for c in ('wagon', 'flat', 'van', 'loco')); t['bitten_end'] = tri_count(N['flat_end_bitten']) if N.get('flat_end_bitten') else 0
    t['covers'] = sum(tri_count(o) for k, o in N.items() if k.startswith('cover_'))
    return t


def main():
    lib.reset(); lib._mats.clear()
    N = {}; RC = None
    if want('train'):
        TX.train_materials(); root, RC = build_train(N)
    bpy.context.view_layer.update()
    finish(N)
    tris = tri_stats(N) if RC else {}
    print('JF_TRIS', json.dumps(tris))
    if arg('stats'):
        for k, o in sorted(N.items()):
            if o is not None and o.type == 'MESH': print('JF_PART', k, tri_count(o), len(o.data.vertices), [m.name for m in o.data.materials])
    if RC:
        meta = parts_json(N, RC, tris)
        small = {k: v for k, v in meta.items() if k not in ('parts',)}; small['parts_file'] = 'rp_train.parts.json'; small['kind'] = 'story'
        small['hidden'] = sorted(k for k, o in N.items() if o is not None and o.type == 'MESH' and o.get('jf_hidden'))
        N['rp_train']['jf'] = json.dumps(small)
        if not arg('no-export'):
            os.makedirs(OUT, exist_ok=True)
            with open(os.path.join(OUT, 'rp_train.parts.json'), 'w') as f: json.dump(meta, f, separators=(',', ':'))
            compact_glb(export_glb(N['rp_train'], os.path.join(OUT, 'rp_train.glb')))
            print('JF_GLB', glb_summary(os.path.join(OUT, 'rp_train.glb')))
    pdir = arg('preview')
    if isinstance(pdir, str):
        preview(N, pdir, arg('views', 'turn_q').split(','), bool(arg('bitten')), res=tuple(int(x) for x in arg('res', '960x600').split('x')))
        return
    if RC and not arg('no-sheet'): sheet_train(N, tris)


main()
