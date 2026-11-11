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


def build_tunnel(N):
    import rptunnel as RT
    RT.tunnel_materials(); root = empty('rp_tunnel'); N['rp_tunnel'] = root
    N['tk_lining'] = mk(RT.lining('tk_lining'), 'tk_lining', root); N['tk_niche'] = mk(RT.lining('tk_niche', True, 4.0), 'tk_niche', root); N['tk_lining_b'] = mk(RT.lining('tk_lining_b', False, 9.0, True), 'tk_lining_b', root)
    N['tk_track'] = mk(RT.track(), 'tk_track', root); N['tk_track_far'] = mk(RT.track_far(), 'tk_track_far', root); N['tk_cables'] = mk(RT.cables(), 'tk_cables', root, sharp=70)
    for kit in RT.bulbs(): N[kit.name] = mk(kit, kit.name, root, sharp=62)
    N['tk_phone'] = mk(RT.phone_alone(), 'tk_phone', root); N['tk_marker'] = mk(RT.marker(), 'tk_marker', root); N['tk_signal'] = mk(RT.signal(), 'tk_signal', root)
    N['tp_portal'] = mk(RT.portal(), 'tp_portal', root)
    return root, RT


def build_commuter(N):
    import rpcommuter as CM
    CM.commuter_materials(); root = empty('rp_commuter'); N['rp_commuter'] = root
    for name, kit in CM.carriage().items(): N[name] = mk(kit, name, root)
    N['cm_end_torn'] = mk(CM.torn_end(), 'cm_end_torn', root, hide=True); N['cm_lod'] = mk(CM.far(), 'cm_lod', root, hide=True)
    return root, CM


def bake_commuter(N):
    S = int(arg('ao', 20)); ms = {k: N[k] for k in N if k.startswith('cm_') and N[k] is not None}
    for o in N.values():
        if o is not None and o.type == 'MESH': o.hide_render = True
    for k in ('cm_car', 'cm_end'): ms[k].hide_render = False
    bake_ao([ms['cm_car'], ms['cm_end']], dist=0.5, samples=S, lo=0.36)
    ms['cm_end'].hide_render = True; ms['cm_end_torn'].hide_render = False
    bake_ao([ms['cm_end_torn']], dist=0.4, samples=S, lo=0.45, also=[ms['cm_car']])
    flat_ao(ms['cm_lod']); flat_ao(ms['cm_glass'])
    for o in N.values():
        if o is not None and o.type == 'MESH': o.hide_render = False


TILES = dict(tk_lining=6.0, tk_lining_b=6.0, tk_niche=6.0, tk_track=6.0, tk_track_far=6.0, tk_cables=6.0, tk_bulbs=12.0)


def bake_tunnel(N):
    """AO for the kit. a piece that tiles is baked between two copies of itself (and of the floor / the wall), so its
    ends are as dark as its middle and no seam shows every six metres"""
    names = [k for k in N if k.startswith(('tk_', 'tp_')) and N[k] is not None]; S = int(arg('ao', 20))
    for k in N:
        if N[k] is not None and N[k].type == 'MESH': N[k].hide_render = True
    def ghosts(k, L, n=1):
        out = []
        for i in list(range(-n, 0)) + list(range(1, n + 1)):
            o = N[k].copy(); _link(o); o.name = f'jf_set_{k}_{i}'; o.location = N[k].location + gv(0, 0, i * L); o.hide_render = False; out.append(o)
        return out
    for k in names:
        o = N[k]
        if k in ('tk_bulb_lit', 'tk_bulb_dead'): flat_ao(o); continue
        L = TILES.get(k); also = []
        if L:
            also += ghosts(k, L)
            for q in ('tk_track', 'tk_lining'):
                if q != k and q in N and k != 'tk_bulbs' and not (k in ('tk_niche', 'tk_lining_b') and q == 'tk_lining') and not (k == 'tk_track_far' and q == 'tk_track'): N[q].hide_render = False; also += [N[q]] + ghosts(q, 6.0)
        o.hide_render = False; bpy.context.view_layer.update()
        bake_ao([o], dist=0.45, samples=S, lo=0.4, also=also)
        for q in also:
            if q.name.startswith('jf_set_'): bpy.data.objects.remove(q, do_unlink=True)
            else: q.hide_render = True
        o.hide_render = True
    for k in N:
        if N[k] is not None and N[k].type == 'MESH': N[k].hide_render = False


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
    'bitten': ((4.5, 4.2, 4.6), (0, 1.1, 10.2), 35, 0.2), 'bitten2': ((1.1, 2.5, 12.9), (0.2, 1.0, 9.5), 24, 0.3),
    'covers': ((60, 1.0, 0), (0, 1.0, 0), ('o', 12), 0.0),
}


def rig(cam, tgt, key=1.0, amb=0.55):
    """lights hung round the camera for one picture: a key over its left shoulder, a cool fill from its right, a warm rim
    from behind the thing, a low bounce"""
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT': bpy.data.objects.remove(o, do_unlink=True)
    world(0x1a1220, amb); bpy.context.scene.eevee.light_threshold = 0.0006
    c, t = V3(cam), V3(tgt); v = t - c; D = max(4.0, v.length); f = v.normalized(); up = V3((0, 1, 0)); rt = f.cross(up).normalized(); E = 17.0 * D * D * key
    area(E, tuple(t - f * D * 0.55 + up * D * 0.75 - rt * D * 0.55), tuple(t), D * 0.5, (1.0, 0.97, 0.92))
    area(E / 3.2, tuple(t - f * D * 0.4 + up * D * 0.15 + rt * D * 0.9), tuple(t), D * 0.6, (0.8, 0.88, 1.0))
    area(E / 3.0, tuple(t + f * D * 0.7 + up * D * 0.7 + rt * D * 0.2), tuple(t), D * 0.5, (1.0, 0.8, 0.9))
    area(E / 7, tuple(t - f * D * 0.5 - up * D * 0.25), tuple(t), D * 0.5, (1.0, 0.9, 0.8))


def shoot(name, path, res=(960, 600), samples=12, ex=None, key=1.0):
    loc, tgt, lens, e = VIEWS[name] if isinstance(name, str) else name
    rig(loc, tgt, key * float(arg('key', 1.0))); ex = (e if ex is None else ex) + float(arg('ex', -1.0))
    if isinstance(lens, tuple): shot(path, loc, tgt, res=res, ortho=lens[1], exposure=ex, samples=samples, roll=math.pi / 2 if loc[1] > 40 else 0.0)
    else: shot(path, loc, tgt, lens, res=res, exposure=ex, samples=samples)
    return path


LAID = []
def lay_tunnel(N, RT, z0=-12.0, n=10, lit=2, on=True, props=True):
    """the kit put down for a picture: n six-metre lengths from z0, every fourth with the refuge, the string of bulbs (the
    first `lit` of them lit, counted from the far end: the rest are out), the phone's niche, a marker, the signal"""
    for o in LAID:
        try: bpy.data.objects.remove(o, do_unlink=True)
        except ReferenceError: pass
    LAID.clear()
    for k in N:
        if k.startswith(('tk_', 'tp_')) and N[k] is not None: N[k].hide_render = True
    if not on: return
    def put(k, z, x=0.0, ry=0.0):
        o = N[k].copy(); _link(o); o.name = f'jf_set_lay_{k}_{len(LAID)}'; o.parent = None; set_game_matrix(o, T(x, 0, z) @ RY(ry)); o.hide_render = False; LAID.append(o); return o
    for i in range(n):
        z = z0 + i * 6.0
        put('tk_niche' if i % 4 == 1 else 'tk_lining_b' if i % 4 == 3 else 'tk_lining', z); put('tk_track', z); put('tk_cables', z)
    nb = int(n * 6.0 / 12.0)
    for i in range(nb):
        z = z0 + 3.0 + i * 12.0; put('tk_bulbs', z); put('tk_bulb_lit' if i >= nb - lit else 'tk_bulb_dead', z)
    if props:
        xc = math.sqrt(RT.R ** 2 - RT.CY ** 2) - 0.55
        put('tk_marker', z0 + 15.0, -xc, math.pi / 2); put('tk_signal', z0 + 27.0, xc - 0.1, 0.0)
    bpy.context.view_layer.update()


TVIEWS = {'in': ((0.9, 2.2, -11.0), (0.2, 2.6, 20), 16, 0.6), 'in_back': ((-0.6, 2.4, 44.0), (0, 2.6, 0), 16, 0.6), 'cut': ((16, 9, -22), (0, 2.5, 14), 30, 0.2), 'niche': ((1.2, 1.9, -8.2), (-4.2, 1.4, -2.9), 24, 0.8),
          'track': ((2.8, 1.9, -9.0), (-1.2, 0.0, -4.5), 28, 0.6), 'wall': ((-1.8, 2.6, -10.0), (4.3, 3.6, -2.0), 22, 0.6), 'signal': ((-0.5, 2.0, 9.5), (2.7, 2.6, 15.0), 28, 0.8), 'bulb': ((0.8, 5.2, -11.5), (2.2, 6.6, -9.0), 35, 0.6),
          'portal': ((7, 4.2, 15), (0, 3.6, 0), 24, 0.0), 'portal_f': ((0, 5.0, 60), (0, 5.0, 0), ('o', 19), 0.0)}


def preview_tunnel(N, RT, pdir, views, res=(960, 600)):
    os.makedirs(pdir, exist_ok=True); colour_preview([m for m in RT.MT.values()]); out = []
    for v in views:
        if v.startswith('portal'):
            lay_tunnel(N, RT, on=False); N['tp_portal'].hide_render = False
        else: lay_tunnel(N, RT, n=int(arg('n', 10)), lit=int(arg('lit', 2)))
        loc, tgt, lens, e = TVIEWS[v]
        out.append(shoot((loc, tgt, lens, e), os.path.join(pdir, f'tk_{v}.png'), res, int(arg('samples', 10))))
    lay_tunnel(N, RT, on=False); clear_studio()
    for k in N:
        if N[k] is not None and N[k].type == 'MESH': N[k].hide_render = False
    print('JF_PREVIEW', ' '.join(out))


CVIEWS = {'q': ((9, 4.5, -19), (0, 2.0, -2), 28, 0.0), 'side': ((60, 2.2, 0), (0, 2.2, 0), ('o', 23), 0.0), 'in': ((0.2, 2.75, -8.6), (0.1, 2.2, 6), 16, 0.8), 'door': ((4.2, 2.4, -7.5), (1.3, 2.0, -3.6), 35, 0.2),
          'torn': ((4.0, 3.5, 15.0), (0, 2.4, 9.7), 30, 0.2), 'torn_f': ((0.4, 2.6, 14.6), (0, 2.5, 9.6), 30, 0.4), 'coffee': ((-0.3, 2.5, 0.4), (-1.2, 1.95, 0.0), 35, 1.0), 'row': ((14, 6, -40), (0, 2.0, 30), 28, 0.0)}


def preview_commuter(N, CM, pdir, views, res=(960, 600)):
    os.makedirs(pdir, exist_ok=True); colour_preview([m for m in CM.MC.values()]); out = []
    for v in views:
        torn = v.startswith('torn'); lod = bool(arg('lod'))
        for k in N:
            if k.startswith('cm_') and N[k] is not None: N[k].hide_render = (k == 'cm_lod') != lod if k in ('cm_lod', 'cm_car', 'cm_glass') else (lod or (k == 'cm_end_torn') != torn)
        loc, tgt, lens, e = CVIEWS[v]
        out.append(shoot((loc, tgt, lens, e), os.path.join(pdir, f'cm_{v}.png'), res, int(arg('samples', 10))))
    clear_studio()
    for k in N:
        if N[k] is not None and N[k].type == 'MESH': N[k].hide_render = False
    print('JF_PREVIEW', ' '.join(out))


def set_state(N, bitten=False, lod=False):
    for k, o in N.items():
        if o is None or o.type != 'MESH' or not (o.parent and o.parent.name.startswith('car_')): continue   # the train's own parts only
        hide = bool(o.get('jf_hidden'))
        if k.endswith('_lod'): hide = not lod
        elif lod and k.startswith(('wagon', 'flat', 'van', 'loco', 'cover')): hide = True
        elif k == 'flat_end_bitten': hide = not bitten
        elif k == 'flat_end': hide = bitten
        if bitten and o.parent and o.parent.name == 'car_wagon': hide = True
        o.hide_render = hide


def preview(N, pdir, views, bitten=False, res=(960, 600)):
    os.makedirs(pdir, exist_ok=True); colour_preview([m for m in M.values()])
    rest = [o for k, o in N.items() if o is not None and o.type == 'MESH' and not (o.parent and o.parent.name.startswith('car_'))]   # the kit and the carriage are built at the origin too
    for o in rest: o.hide_render = True
    set_state(N, bitten, bool(arg('lod'))); scale_set(not arg('no-set')); out = []
    for v in views: out.append(shoot(v, os.path.join(pdir, f'tr_{v}{"_b" if bitten else ""}.png'), res, int(arg('samples', 10))))
    clear_studio(); scale_set(False); set_state(N)
    for o in rest: o.hide_render = False
    print('JF_PREVIEW', ' '.join(out))


# ------------------------------------------------------------ finishing
def bake_groups(N):
    meshes = {k: o for k, o in N.items() if o is not None and o.type == 'MESH'}
    for o in meshes.values(): o.hide_render = True
    for car in ('wagon', 'flat', 'van', 'loco'):
        grp = [o for k, o in meshes.items() if o.parent and o.parent.name == 'car_' + car and not o.get('jf_hidden')]
        solid = [o for o in grp if not o.name.endswith(('_glass', '_tail', '_lamp', '_headlamp', '_cablamp'))]
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
    if not arg('no-ao'):
        if 'rp_train' in N: bake_groups(N)
        if 'rp_tunnel' in N: bake_tunnel(N)
        if 'rp_commuter' in N: bake_commuter(N)
    for o in meshes:
        if 'AO' not in o.data.color_attributes: flat_ao(o)
        final_colour(o)


def part_list(N, pred):
    out = []
    for k in sorted(N):
        o = N[k]
        if o is None or o.type != 'MESH' or not pred(k, o): continue
        lo, hi = bounds([o]); d = dict(name=k, centre=r3((lo + hi) / 2), half=r3((hi - lo) / 2), tris=tri_count(o), materials=[m.name for m in o.data.materials])
        if o.get('jf_hidden'): d['hidden'] = True
        out.append(d)
    return out


def parts_json(N, RC, tris, RT=None, CM=None):
    parts = []; bpy.context.view_layer.update()
    for k in sorted(N):
        o = N[k]
        if o is None or o.type != 'MESH' or not (o.parent and o.parent.name.startswith('car_')): continue
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
            tail_lamp=I.get('tail_lamp'), work_lamp=I.get('work_lamp'), cab_lamp=I.get('cab_lamp'), van_lantern=I.get('van_lantern'), fridge=I.get('fridge'), handtruck=I.get('handtruck'),
            van_roof=dict(y=RC.VAN.roof, x=[-RC.HW, RC.HW], z=[RC.VAN.roofZ0, RC.VAN.z1]), van_steps=dict(x=[-RC.HW, -RC.HW + RC.VAN.stairW], z=[RC.VAN.z0, RC.VAN.roofZ0], n=RC.VAN.stairs)),
        materials=dict(tr_atlas='everything painted, planked and steel (one 512 px atlas with a roughness / metal map)', tr_glass='the cab windows (blended)', tr_headlamp='the working head lamp (emissive)',
                       tr_tail='the tail lamp (emissive)', tr_worklamp='the flood on the van roof and the lantern under it (emissive)'),
        parts=parts)
    if RT: meta['tunnel'] = dict(file='rp_tunnel.glb', tiles=TILES, bore_r=RT.R, axis_y=RT.CY, info=RT.INFO, parts=part_list(N, lambda k, o: k.startswith(('tk_', 'tp_'))),
                                 materials=dict(tk_brick='the lining (a 128 px tile: 1.5 m along, 14 times round)', tk_atlas='everything else', tk_bulb_on='a lit bulb (emissive)', tk_bulb_off='a dead one'))
    if CM: meta['commuter'] = dict(file='rp_commuter.glb', info=CM.INFO, parts=part_list(N, lambda k, o: k.startswith('cm_')), materials=dict(cm_atlas='the carriage', cm_glass='its panes (blended)'))
    return meta


def sheets(N, tris, RC=None, RT=None, CM=None):
    """the review sheets (tools/blender/sheets/rp_train_*.jpg, rp_tunnel_kit.jpg, rp_commuter.jpg): --sheet=a,b picks some"""
    mats = [m for m in M.values()] + ([m for m in RT.MT.values()] if RT else []) + ([m for m in CM.MC.values()] if CM else [])
    colour_preview(mats); tmp = os.path.join(SHEETS, '_tmp'); os.makedirs(tmp, exist_ok=True); S = int(arg('samples', 12))
    want_ = arg('sheet'); want_ = set(want_.split(',')) if isinstance(want_, str) else None
    def only(pred):
        for k, o in N.items():
            if o is not None and o.type == 'MESH': o.hide_render = not pred(k, o)
    def train(on, bitten=False, lod=False):
        if not RC: return
        set_state(N, bitten, lod)
        if not on:
            for k, o in N.items():
                if o is not None and o.type == 'MESH' and o.parent and o.parent.name.startswith('car_'): o.hide_render = True
    def others(on=False):
        for k, o in N.items():
            if o is not None and o.type == 'MESH' and k.startswith(('tk_', 'tp_', 'cm_')): o.hide_render = not on
    def sheet(tag, label, shots, cols, res=(900, 560)):
        """shots: [(view | (cam, target, lens, exposure), caption, setup())]"""
        if want_ is not None and tag not in want_: return
        out = []
        for i, (v, cap, setup) in enumerate(shots):
            setup(); bpy.context.view_layer.update(); out.append(shoot(v, os.path.join(tmp, f'{tag}_{i}.png'), res, S))
        contact(out, os.path.join(SHEETS, tag), label, cols=cols, labels=[c for _, c, _ in shots])
    if RC:
        whole = lambda: (others(), train(True), scale_set(True))
        sheet('rp_train_turnaround', f"DALE'S WORKS TRAIN  {tris['whole']} TRIS  WAGON {tris['wagon']}  FLATBED {tris['flat']}  TOOL VAN {tris['van']}  LOCO {tris['loco']}  RING = THE 9.2 M BORE  FIGURE = 1.8 M",
              [('turn_q', "from behind (the boss's side)", whole), ('turn_front', 'from the front', whole), ('turn_side', 'side: 9 m / 10 m / 7 m / 5 m', whole), ('turn_top', 'plan: 4.2 m wide, the middle lane clear', whole)], 2, (1100, 560))
        sheet('rp_train_cars', 'THE FOUR CARS', [('wagon', 'rear wagon: drop sides, the rail', whole), ('flat', 'flatbed: crates, the fridge chained down', whole), ('van', 'tool van: steps to a flat roof, open sides', whole), ('loco', 'the loco: more of a tractor', whole),
              ('loco_side', 'the loco, side on', whole), ('turn_side', 'the far versions (%d tris for all four)' % sum(tris[c + '_lod'] for c in ('wagon', 'flat', 'van', 'loco')), lambda: (others(), train(True, lod=True), scale_set(True)))], 3)
        bare = lambda: (others(), train(True), scale_set(False))
        def lineup():   # the cover pieces stood in a row off the train
            others(); train(False); scale_set(False); cs = sorted(k for k in N if k.startswith('cover_'))
            for i, k in enumerate(cs): o = N[k]; o.hide_render = False; o['jf_keep'] = list(o.location); o.location = gv(-6.3 + i * 1.8, 0.0, -30.0)
            b = TBuf('jf_set_floor'); b.add(bx(-8.5, -0.06, -32, 8.5, 0.0, -28), mat('jf_set_floor', 0x2a2228, rough=0.9), ('tile', 1.0)); o = b.obj(wn=False); flat_ao(o); final_colour(o); SET.append(o)
        def unline():
            for k in N:
                if k.startswith('cover_') and N[k] is not None and 'jf_keep' in N[k]: N[k].location = N[k]['jf_keep']; del N[k]['jf_keep']
        sheet('rp_train_detail', 'THE CAB  THE VAN  THE COVER PIECES  THE BITTEN END', [
            ('cab', 'the cab from the van: seat, brake, flask, kettle', bare), ('loco_back', "the loco's back", bare), ('van_under', "under the van's roof: 2 m, the lane clear", bare), ('van_roof', "on the van's roof", bare),
            ('van_board', 'the tool board behind the steps', bare), ('rail', 'the back rail, the tail lamp', lambda: (others(), train(True), scale_set(True))),
            (((0.0, 2.4, -22.5), (0.0, 0.85, -30.0), 34, 0.0), 'the eight cover pieces (crates, the fridge, the bench, the cable drum)', lineup),
            ('bitten', 'after the first lunge: the wagon gone', lambda: (unline(), others(), train(True, bitten=True), scale_set(False))), ('bitten2', 'the torn end from the flatbed', lambda: (others(), train(True, bitten=True), scale_set(False)))], 3)
        unline(); scale_set(False); set_state(N)
    if RT:
        def tun(lit, with_train=False, n=10):
            others(); train(bool(with_train) and bool(RC)); scale_set(False); lay_tunnel(N, RT, z0=-24.0, n=n, lit=lit)
        sheet('rp_tunnel_kit', 'THE UNDER-HILL LOOP  THE KIT TILED FOR 60 M  %s' % '  '.join(f'{k[3:].upper()} {tri_count(N[k])}' for k in ('tk_lining', 'tk_niche', 'tk_track', 'tk_cables', 'tk_bulbs') if N.get(k)), [
            (((0.9, 2.4, -22.5), (0.2, 2.6, 20), 16, 0.6), 'every bulb lit', lambda: tun(5)), (((0.9, 2.4, -22.5), (0.2, 2.6, 20), 16, 0.6), 'the far ones out: three dead, two lit', lambda: tun(2)),
            (((1.4, 1.9, -20.4), (-4.2, 1.4, -15.2), 24, 0.8), 'the refuge: a phone, the notice', lambda: tun(5)), (((2.8, 1.9, -21.0), (-1.2, 0.0, -16.5), 28, 0.6), 'ballast, sleepers, baseplates, troughing', lambda: tun(5)),
            (((-1.8, 2.6, -22.0), (4.3, 3.6, -14.0), 22, 0.6), 'cables on brackets, the bulb string', lambda: tun(5)), (((26, 13, -42), (0, 2.5, 4), 30, 0.2), 'the same 60 m from outside', lambda: tun(5))], 3)
        lay_tunnel(N, RT, on=False)
        def portal(): others(); train(False); scale_set(False); N['tp_portal'].hide_render = False
        psh = [(TVIEWS['portal'], 'the tunnel mouth, the viaduct\'s first span', portal), (TVIEWS['portal_f'], 'face on', portal)]
    else: psh = []
    if CM:
        def car(torn=False, lod=False):
            others(); train(False); scale_set(False)
            for k in ('cm_car', 'cm_glass'): N[k].hide_render = lod
            N['cm_end'].hide_render = lod or torn; N['cm_end_torn'].hide_render = lod or not torn; N['cm_lod'].hide_render = not lod
        sheet('rp_commuter', 'THE DEAD COMMUTER TRAIN  ONE CARRIAGE %d TRIS  FAR %d  ·  THE TUNNEL MOUTH' % (tri_count(N['cm_car']) + tri_count(N['cm_end']) + tri_count(N['cm_glass']), tri_count(N['cm_lod'])), [
            (((9.5, 4.6, -18.5), (0, 2.0, -1.5), 34, 0.0), 'a ☺ on every door, every door open', car), (CVIEWS['in'], 'every seat empty, coats on the hooks', car), (CVIEWS['coffee'], 'a coffee on a table, grown over', car),
            (CVIEWS['torn'], 'the last carriage: its end wall bent outward', lambda: car(True)), (((9.5, 4.6, -18.5), (0, 2.0, -1.5), 34, 0.0), 'the far version', lambda: car(lod=True))] + psh, 4)
    scale_set(False); clear_studio()
    for k, o in N.items():
        if o is not None and o.type == 'MESH': o.hide_render = False
    try: os.rmdir(tmp)
    except OSError: pass


def run_qa(N):
    """the asset-QA gate (.claude/skills/blender-asset-qa) on every group that is shown together: each car with what
    stands on it, the torn end with the flatbed, each far version, each kit piece, the carriage with either end"""
    res = {}; quiet = not arg('qa-warn'); tol = float(arg('qa-tol', 0.012)); zf = int(arg('zf', 30)); only = arg('qa'); only = set(only.split(',')) if isinstance(only, str) else None
    G = lambda pred: [o for k, o in N.items() if o is not None and o.type == 'MESH' and pred(k, o)]
    def run(tag, objs, tol_=tol):
        if only is None or tag in only: res[tag] = qa_gate(tag, objs, tol=tol_, quiet=quiet, zf=zf)
    for car in ('wagon', 'flat', 'van', 'loco'):
        if 'car_' + car not in N: continue
        run(car, G(lambda k, o: o.parent and o.parent.name == 'car_' + car and not o.get('jf_hidden'))); run(car + '_lod', [N[car + '_lod']])
    if N.get('flat_end_bitten'): run('flat_bitten', [N['flat_end_bitten'], N['flat_body']], 0.03)
    for k in sorted(N):
        if k.startswith(('tk_', 'tp_')) and N[k] is not None and k not in ('tk_bulb_lit', 'tk_bulb_dead'): run(k, [N[k]] + ([N['tk_bulb_lit']] if k == 'tk_bulbs' else []), 0.03)
    if N.get('cm_car'):
        run('cm_car', [N['cm_car'], N['cm_end'], N['cm_glass']], 0.03); run('cm_last', [N['cm_car'], N['cm_end_torn']], 0.05); run('cm_lod', [N['cm_lod']], 0.03)
    print('QA_SUMMARY', json.dumps({k: bool(v.get('pass')) for k, v in res.items()}))
    return res


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
    N = {}; RC = None; RT = None
    if want('train'):
        TX.train_materials(); root, RC = build_train(N)
    if want('tunnel'): troot, RT = build_tunnel(N)
    CM = None
    if want('commuter'): croot, CM = build_commuter(N)
    bpy.context.view_layer.update()
    finish(N)
    tris = tri_stats(N) if RC else {}
    print('JF_TRIS', json.dumps(tris))
    if arg('stats'):
        for k, o in sorted(N.items()):
            if o is not None and o.type == 'MESH': print('JF_PART', k, tri_count(o), len(o.data.vertices), [m.name for m in o.data.materials])
    if RC:
        meta = parts_json(N, RC, tris, RT, CM)
        small = {k: v for k, v in meta.items() if k not in ('parts',)}; small['parts_file'] = 'rp_train.parts.json'; small['kind'] = 'story'
        small['hidden'] = sorted(k for k, o in N.items() if o is not None and o.type == 'MESH' and o.get('jf_hidden'))
        N['rp_train']['jf'] = json.dumps(small)
        if not arg('no-export'):
            os.makedirs(OUT, exist_ok=True)
            with open(os.path.join(OUT, 'rp_train.parts.json'), 'w') as f: json.dump(meta, f, separators=(',', ':'))
            compact_glb(export_glb(N['rp_train'], os.path.join(OUT, 'rp_train.glb')))
            print('JF_GLB', glb_summary(os.path.join(OUT, 'rp_train.glb')))
    if RT:
        for k in sorted(N):
            if k.startswith(('tk_', 'tp_')) and N[k] is not None: print('JF_PART', k, tri_count(N[k]), len(N[k].data.vertices), [m.name for m in N[k].data.materials])
        N['rp_tunnel']['jf'] = json.dumps(dict(id='rp_tunnel', kind='story', tiles=TILES, info=RT.INFO))
        if not arg('no-export'):
            compact_glb(export_glb(N['rp_tunnel'], os.path.join(OUT, 'rp_tunnel.glb'))); print('JF_GLB', glb_summary(os.path.join(OUT, 'rp_tunnel.glb')))
    if CM:
        for k in sorted(N):
            if k.startswith('cm_') and N[k] is not None: print('JF_PART', k, tri_count(N[k]), len(N[k].data.vertices), [m.name for m in N[k].data.materials])
        N['rp_commuter']['jf'] = json.dumps(dict(id='rp_commuter', kind='story', hidden=['cm_end_torn', 'cm_lod'], info=CM.INFO))
        if not arg('no-export'):
            compact_glb(export_glb(N['rp_commuter'], os.path.join(OUT, 'rp_commuter.glb'))); print('JF_GLB', glb_summary(os.path.join(OUT, 'rp_commuter.glb')))
    if arg('qa'): run_qa(N)
    pdir = arg('preview')
    if isinstance(pdir, str):
        if CM and not RC and not RT: return preview_commuter(N, CM, pdir, arg('views', 'q').split(','), res=tuple(int(x) for x in arg('res', '960x600').split('x')))
        if RT and not RC: return preview_tunnel(N, RT, pdir, arg('views', 'in').split(','), res=tuple(int(x) for x in arg('res', '960x600').split('x')))
        preview(N, pdir, arg('views', 'turn_q').split(','), bool(arg('bitten')), res=tuple(int(x) for x in arg('res', '960x600').split('x')))
        return
    if not arg('no-sheet'): sheets(N, tris, RC, RT, CM)


main()
