# UNPAID WAR-RIG (OVERDUE enemies.js `war_rig`, m02 on the Ring Road): a cubicle that drives. A scrap chassis (two
# steel rails, a plywood deck) on four car tyres at the back and two giant office-chair castors at the front (they
# swivel to steer); felt partition walls for armour, aluminium-capped, sprayed UNPAID and stuck with memos; a desk on
# its side bolted to the front as a ram (its drawers, steel corner guards, letter-opener spikes); the driver's office
# chair, a wall clock for a steering wheel, a monitor on the dash; a minigun on an upturned chair base on the back
# deck, fed from a water-cooler bottle; two chair-leg exhaust stacks; a tie flying from an aerial.
# About 4 m long, 2.2 m wide, 2.4 m tall. front = -z, the ground at y 0.
# nodes (for the game to drive): wheel_rl wheel_rr wheel_ml wheel_mr (axle pivots, spin round x); castor_l castor_r
# (steer round y at the swivel) > castor_l_spin castor_r_spin (spin round x); turret (yaw round y) > gun (pitch round x)
# > barrels (spin round z); markers: seat (where the driver sits), muzzle (the barrels' tip); lod (the whole thing,
# decimated, for far away). jf meta lists them. rig: everything but lod hangs off it (the clips move it).
# baked clips (glTF animations): drive (5 s loop = 13.19 m), ram_hit (0.8 s), die (2.4 s, hold the last frame).
# blender52 -b --python tools/blender/cast/make_cast_war_rig.py [-- --no-sheet]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from castlib import *  # noqa

ID = 'war_rig'
rng = random.Random(32)


def felt(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(3)
    px[:] = hexrgb(0x6a7a8c) * (0.9 + 0.1 * r.random((h, w, 1)))
    for _ in range(40): px_disc(px, r.integers(0, w), r.integers(0, h), 1, 0x5a6a7a)


def graffiti(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x6a7a8c)
    r = np.random.default_rng(4)
    px[:] = px * (0.9 + 0.1 * r.random((h, w, 1)))
    text_px(px, 'UNPAID', 8, h // 2 - 10, 3, 0xff4fd8)
    for x in range(4, w - 4, 2): px[min(h - 1, h // 2 + 14 + int(math.sin(x * 0.3) * 2)), x] = hexrgb(0xffe14d)  # an underline, a drip or two
    for x in (20, 47, 70): px_line(px, x, h // 2 + 8, x, h // 2 + 8 + int(r.integers(4, 12)), 0xff4fd8)


def memo(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffe14d)
    for y in (4, 8, 12): px_line(px, 2, y, w - 3 - (y % 5), y, 0x5a5a5a)


def woodgrain(px):
    h, w = px.shape[:2]
    for y in range(h):
        for x in range(w):
            g = 0.5 + 0.5 * math.sin(y * 0.6 + math.sin(x * 0.08) * 3)
            px[y, x] = hexrgb(0xb08050) * (0.85 + 0.15 * g)


def clockface(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf4f4f0)
    for k in range(12):
        a = k * math.pi / 6; px_disc(px, int(w / 2 + math.sin(a) * w * 0.38), int(h / 2 - math.cos(a) * h * 0.38), 1, 0x1a1a1a)
    px_line(px, w // 2, h // 2, w // 2, h // 2 - 9, 0x1a1a1a); px_line(px, w // 2, h // 2, w // 2 + 7, h // 2 + 2, 0x1a1a1a)


def tread(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x1e1e22)
    for x in range(0, w, 6): px[:, x:x + 2] = hexrgb(0x2e2e34)


def monitor(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0x0a2a12)
    text_px(px, 'RAM', 4, 4, 1, 0x39ff14); text_px(px, 'RAM', 4, 12, 1, 0x39ff14); text_px(px, 'RAM!', 4, 20, 1, 0x39ff14)


def decal(name, c, w, h, m, face='-z', tilt=0.0):
    """a printed sheet (graffiti, a memo, a screen): one quad facing `face` (-x, +x, -z, +z), reading the right way
    round from that side; tilt leans it back (round its horizontal axis)"""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    ax = {'-z': (Vector((1, 0, 0)), Vector((0, 0, -1))), '+z': (Vector((-1, 0, 0)), Vector((0, 0, 1))),
          '-x': (Vector((0, 0, -1)), Vector((-1, 0, 0))), '+x': (Vector((0, 0, 1)), Vector((1, 0, 0)))}[face]
    right, nrm = ax  # (seen from the front of the sheet, its right runs along -right: viewer's right)
    up = Vector((0, 1, 0))
    if tilt: up = (up * math.cos(tilt) - nrm * math.sin(tilt))
    C = Vector(c); R = -right * (w / 2); U = up * (h / 2)
    P = [C - R - U, C + R - U, C + R + U, C - R + U]
    vs = [bm.verts.new(gv(*p)) for p in P]
    f = bm.faces.new(vs)
    for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uvl].uv = uv
    bm.normal_update()
    o = lib_obj(name, bm, m); o['keep_uv'] = 1
    nn = o.data.polygons[0].normal; ng = Vector((nn.x, nn.z, -nn.y))
    if ng.dot(nrm) < 0: o.data.flip_normals()
    return o


def build():
    steel = mat('wr_steel', 0x5a5e66, metal=0.7, rough=0.4)
    rusty = mat('wr_rust', 0xffffff, rough=0.7, tex=tex_noise('wr_rustT', 0x8a5a3a, 0.18, 32, speck=0x5a3020, speck_p=0.15, seed=5))
    ply = mat('wr_ply', 0xc8a070, rough=0.7, tex=tex_noise('wr_plyT', 0xc8a070, 0.1, 32, seed=6))
    feltM = mat('wr_felt', 0xffffff, rough=0.9, tex=tex_canvas('wr_feltT', 32, 32, felt))
    graf = mat('wr_graffiti', 0xffffff, rough=0.85, tex=tex_canvas('wr_grafT', 128, 48, graffiti))
    alu = mat('wr_alu', 0xc8ccd2, metal=0.9, rough=0.25)
    wood = mat('wr_desk', 0xffffff, rough=0.45, clearcoat=0.4, tex=tex_canvas('wr_deskT', 32, 32, woodgrain))
    tyre = mat('wr_tyre', 0xffffff, rough=0.8, tex=tex_canvas('wr_treadT', 32, 8, tread))
    hub = mat('wr_hub', 0xd0d4dc, metal=1.0, rough=0.2)
    hubR = mat('wr_hubred', 0xd83030, rough=0.3, clearcoat=0.6)
    blackP = mat('wr_plastic', 0x1e1e22, rough=0.35, clearcoat=0.5)
    chrome = mat('wr_chrome', 0xd8dce4, metal=1.0, rough=0.15)
    gunM = mat('wr_gun', 0x2a2c30, metal=0.8, rough=0.35)
    brass = mat('wr_brass', 0xd8a840, metal=1.0, rough=0.3)
    water = mat('wr_water', 0x3a8ad8, rough=0.08, clearcoat=1.0)
    memoM = mat('wr_memo', 0xffffff, rough=0.6, tex=tex_canvas('wr_memoT', 16, 16, memo))
    clockM = mat('wr_clock', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('wr_clockT', 32, 32, clockface))
    mon = mat('wr_monitor', 0xffffff, rough=0.2, clearcoat=0.8, emit=0x39ff14, strength=0.6, tex=tex_canvas('wr_monT', 32, 30, monitor))
    seatF = mat('wr_seat', 0x2a2a34, rough=0.85)
    tie = mat('wr_tie', 0xd83030, rough=0.6)
    body = []

    # ---- the chassis: two steel rails, cross members, a plywood deck
    for sx in (-1, 1): body.append(box((0.12, 0.16, 3.9), (sx * 0.7, 0.42, 0.0), rusty, bev=0.01))
    for z in (-1.6, -0.6, 0.4, 1.4): body.append(box((1.48, 0.1, 0.1), (0, 0.42, z), steel, bev=0.008))  # (ends buried in the rails)
    body.append(box((2.1, 0.06, 3.5), (0, 0.53, 0.05), ply, bev=0.01))
    # the axles: the two rear ones (car tyres), the front beam (the castors hang from it)
    for z in (0.35, 1.3): body.append(rod((-1.0, 0.42, z), (1.0, 0.42, z), 0.04, steel, seg=8))
    body.append(box((1.8, 0.1, 0.14), (0, 0.62, -1.45), steel, bev=0.01))
    # ---- the partitions: felt walls with aluminium caps, the sides sprayed UNPAID, memos pinned up
    def partition(x0, z0, x1, z1, y0, y1, m=feltM, posts=(True, True)):
        L = math.hypot(x1 - x0, z1 - z0); cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; a = math.atan2(x1 - x0, z1 - z0)
        out = [box((0.05, y1 - y0, L), (cx, (y0 + y1) / 2, cz), m, bev=0.008, rot=(0, a, 0))]
        out.append(box((0.07, 0.03, L + 0.02), (cx, y1 + 0.015, cz), alu, bev=0.004, rot=(0, a, 0)))
        for t, keep in zip((0.0, 1.0), posts):
            if keep: px_, pz = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t; out.append(box((0.07, y1 - y0 + 0.02, 0.07), (px_, (y0 + y1) / 2, pz), alu, bev=0.006))
        return out
    for sx in (-1, 1):
        body += partition(sx * 1.05, -1.55, sx * 1.05, 1.7, 0.56, 1.95)
        body.append(decal('graffiti%d' % sx, (sx * 1.077, 1.25, 0.2), 1.9, 0.62, graf, face='+x' if sx > 0 else '-x'))
        for k in range(4):
            z = rng.uniform(-1.3, 1.4); y = rng.uniform(0.75, 1.75)
            body.append(decal('memo%d%d' % (sx, k), (sx * 1.0785, y, z), 0.09, 0.09, memoM, face='+x' if sx > 0 else '-x'))
            body.append(ball(0.012, (sx * 1.085, y + 0.035, z), mat('wr_pin', [0xff3030, 0x4fd8ff, 0xffe14d][k % 3], rough=0.3, clearcoat=0.6), seg=6, rings=4))
    body += partition(-1.05, 1.72, 1.05, 1.72, 0.56, 1.6, posts=(False, False))  # the back, lower (the gunner leans over it)
    body += partition(-1.05, -1.58, -0.35, -1.58, 0.56, 1.25, posts=(False, True)); body += partition(0.35, -1.58, 1.05, -1.58, 0.56, 1.25, posts=(True, False))  # the front, a gap to see out of
    # ---- the desk ram: a desk on its side bolted across the front, its drawers, steel corner guards, letter-opener spikes
    body.append(box((2.0, 0.85, 0.05), (0, 0.85, -2.0), wood, bev=0.01))
    body.append(box((0.5, 0.7, 0.42), (0.62, 0.8, -1.78), wood, bev=0.01))  # the drawer pedestal, sticking back
    for k, y in enumerate((1.05, 0.83, 0.61)):
        body.append(box((0.44, 0.19, 0.02), (0.62, y, -2.035), wood, bev=0.004))
        body.append(rod((0.55, y, -2.05), (0.69, y, -2.05), 0.008, chrome, seg=6))
    for sx in (-1, 1):
        for y in (0.45, 1.25): body.append(box((0.16, 0.06, 0.08), (sx * 0.95, y, -2.02), steel, bev=0.006))
    for k in range(5):
        x = -0.8 + k * 0.4
        body.append(rod((x, 0.95 - 0.12 * (k % 2), -2.03), (x, 0.95 - 0.12 * (k % 2), -2.4), 0.018, chrome, seg=6, r1=0.002))  # letter openers
    for sx in (-1, 1): body.append(rod((sx * 0.7, 0.5, -1.7), (sx * 0.7, 0.6, -1.98), 0.035, steel, seg=8))  # its brackets
    # ---- inside: the driver's chair, the clock wheel on its column, the monitor on the dash, a keyboard
    body.append(blob('seatpad', (0, 0.98, -0.55), (0.25, 0.06, 0.24), seatF))
    body.append(box((0.46, 0.55, 0.06), (0, 1.32, -0.3), seatF, bev=0.015))
    body.append(rod((0, 0.59, -0.55), (0, 0.92, -0.55), 0.04, chrome, seg=10))
    for i in range(5):
        a = i * 2 * math.pi / 5; t = (math.cos(a) * 0.3, 0.6, -0.55 + math.sin(a) * 0.3)
        body.append(rod((0, 0.6, -0.55), t, 0.02, blackP, seg=6))
    body.append(rod((0, 0.75, -1.4), (0, 1.15, -1.05), 0.035, steel, seg=8))  # the column
    body.append(cyl(0.2, 0.05, (0, 1.17, -1.03), blackP, axis='z', seg=16, rot=(0.55, 0, 0)))
    cf = cyl(0.17, 0.01, (0, 1.165, -1.06), clockM, axis='z', seg=16, rot=(0.55, 0, 0)); body.append(cf)
    body.append(box((0.5, 0.36, 0.05), (0.0, 1.45, -1.48), blackP, bev=0.01, rot=(-0.2, 0, 0)))
    body.append(decal('screen', (0.0, 1.45, -1.457), 0.44, 0.3, mon, face='+z', tilt=0.2))  # (facing the driver)
    body.append(box((0.45, 0.03, 0.15), (0, 1.0, -1.25), mat('wr_keys', 0xd8d8d0, rough=0.5), bev=0.006))
    # ---- the back: the water-cooler ammo drum, the exhaust stacks, the aerial with a tie on it
    body.append(lathe([(0.0, 0.0), (0.2, 0.02), (0.22, 0.12), (0.22, 0.4), (0.18, 0.5), (0.06, 0.56), (0.05, 0.62)], (0.55, 0.56, 1.25), water, seg=14, axis='y'))
    for sx in (-1, 1):
        body.append(tube([(sx * 0.85, 0.6, 1.55), (sx * 0.85, 1.9, 1.6), (sx * 0.85, 2.15, 1.75)], 0.045, chrome, name='stack%d' % sx))
        body.append(cyl(0.06, 0.08, (sx * 0.85, 2.18, 1.78), rusty, axis='y', seg=10))
    body.append(rod((-0.95, 1.95, 1.65), (-0.95, 2.9, 1.7), 0.008, steel, seg=4))
    body.append(tube([(-0.95, 2.85, 1.7), (-0.95, 2.75, 1.9), (-0.95, 2.62, 2.05), (-0.95, 2.5, 2.12)], 0.03, tie, name='tie'))
    root = finish('cast_' + ID, [], {})
    J = {}
    def node(name, pos, parent):
        e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
        e.parent = parent; e.location = gv(*pos) - (parent.matrix_world.translation if parent is not root else Vector((0, 0, 0)))
        bpy.context.view_layer.update(); J[name] = e; return e
    def under(objs, parent, name):
        if not objs: return None
        for x in objs:
            if not x.get('keep_uv'): apply_mods(x); uv_box(x, 0.25)
        o = join(objs, name); apply_mods(o); bpy.context.view_layer.update()
        o.data.transform(Matrix.Translation(o.location)); o.location = (0, 0, 0)  # (join keeps the first piece's origin)
        o.data.transform(Matrix.Translation(-parent.matrix_world.translation)); o.parent = parent; o.location = (0, 0, 0)
        return o
    R = node('rig', (0, 0, 0), root)  # (everything but the far copy hangs off this, so the clips can jolt and drop the lot)
    under(body, R, 'body')
    # ---- the wheels: four car tyres (one hubcap from something red), two giant chair castors that swivel
    for nm, x, z in (('wheel_rl', -1.0, 1.3), ('wheel_rr', 1.0, 1.3), ('wheel_ml', -1.0, 0.35), ('wheel_mr', 1.0, 0.35)):
        w = node(nm, (x, 0.42, z), R); sx = -1 if x < 0 else 1
        parts = [lathe([(0.22, -0.14), (0.38, -0.15), (0.42, -0.1), (0.42, 0.1), (0.38, 0.15), (0.22, 0.14)], (x, 0.42, z), tyre, seg=20, axis='x')]
        parts.append(lathe([(0.0, 0.0), (0.22, 0.0), (0.2, 0.04), (0.06, 0.07)], (x + sx * 0.13, 0.42, z), hubR if nm == 'wheel_mr' else hub, seg=14, axis='x', rot=(0, 0, math.pi) if sx < 0 else None))
        under(parts, w, nm + '_mesh')
    for nm, x in (('castor_l', -0.75), ('castor_r', 0.75)):
        c = node(nm, (x, 0.67, -1.45), R)
        cp = [rod((x, 0.655, -1.45), (x, 0.82, -1.45), 0.05, chrome, seg=10), box((0.36, 0.08, 0.5), (x, 0.595, -1.6), blackP, bev=0.03)]
        under(cp, c, nm + '_fork')
        sp = node(nm + '_spin', (x, 0.3, -1.65), c)
        wh = []
        for o in (-0.1, 0.1): wh.append(lathe([(0.12, -0.05), (0.28, -0.05), (0.3, 0.0), (0.28, 0.05), (0.12, 0.05)], (x + o, 0.3, -1.65), blackP, seg=18, axis='x'))
        wh.append(rod((x - 0.18, 0.3, -1.65), (x + 0.18, 0.3, -1.65), 0.04, chrome, seg=8))
        under(wh, sp, nm + '_wheels')
    # ---- the minigun: an upturned chair base on the back deck, a gas lift, the cradle, six barrels, the feed from the bottle
    T = node('turret', (0, 0.56, 1.0), R)
    tb = []
    for i in range(5):
        a = i * 2 * math.pi / 5; tip = (math.cos(a) * 0.32, 0.62, 1.0 + math.sin(a) * 0.32)
        tb.append(rod((0, 0.62, 1.0), tip, 0.025, blackP, seg=6)); tb.append(ball(0.04, (tip[0], 0.6, tip[2]), blackP, seg=8, rings=6))
    tb.append(rod((0, 0.6, 1.0), (0, 1.75, 1.0), 0.05, chrome, seg=10)); tb.append(cyl(0.09, 0.3, (0, 1.0, 1.0), blackP, axis='y', seg=12))
    tb.append(box((0.5, 0.06, 0.2), (0, 1.78, 1.0), steel, bev=0.01))
    for sx in (-1, 1): tb.append(box((0.04, 0.22, 0.16), (sx * 0.22, 1.9, 1.0), steel, bev=0.008))
    tb.append(tube([(0.5, 1.15, 1.25), (0.35, 1.6, 1.15), (0.15, 1.95, 1.05)], 0.035, brass, name='feed'))  # the feed, from the bottle up
    under(tb, T, 'turret_mesh')
    G = node('gun', (0, 1.95, 1.0), T)
    gp = [box((0.3, 0.26, 0.55), (0, 1.95, 1.05), gunM, bev=0.02), box((0.06, 0.18, 0.12), (0.0, 1.8, 1.32), blackP, bev=0.01)]
    gp.append(rod((0, 2.12, 1.25), (0, 2.12, 0.85), 0.012, steel, seg=6)); gp.append(box((0.08, 0.06, 0.08), (0, 2.13, 0.95), blackP))
    for sx in (-1, 1): gp.append(rod((sx * 0.15, 1.95, 1.0), (sx * 0.255, 1.95, 1.0), 0.04, steel, seg=8))
    under(gp, G, 'gun_mesh')
    Bz = node('barrels', (0, 1.95, 0.75), G)
    bp = []
    for i in range(6):
        a = i * math.pi / 3; bx, by = math.cos(a) * 0.075, math.sin(a) * 0.075
        bp.append(rod((bx, 1.95 + by, 0.78), (bx, 1.95 + by, -0.25), 0.024, gunM, seg=8))
    for z in (0.7, 0.2, -0.22): bp.append(cyl(0.11, 0.04, (0, 1.95, z), steel, axis='z', seg=12))
    under(bp, Bz, 'barrels_mesh')
    node('muzzle', (0, 1.95, -0.27), Bz)
    node('seat', (0, 0.98, -0.55), R)
    # ---- far away: everything as one decimated mesh
    bpy.context.view_layer.update()
    lod_src = [o for o in root.children_recursive if o.type == 'MESH']
    cps = []
    for o in lod_src:
        c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c); c.parent = None; c.matrix_world = o.matrix_world.copy(); cps.append(c)
    lod = join(cps, 'lod'); d = lod.modifiers.new('dec', 'DECIMATE'); d.ratio = 0.18; apply_mods(lod); lod.parent = root; lod.hide_render = True
    clips(J)
    root['jf'] = json.dumps({'kind': 'vehicle', 'id': ID, 'rig': 'rig', 'clips': {'drive': 5.0, 'ram_hit': 0.8, 'die': 2.4}, 'driveMetres': 13.19, 'wheels': ['wheel_rl', 'wheel_rr', 'wheel_ml', 'wheel_mr', 'castor_l_spin', 'castor_r_spin'], 'steer': ['castor_l', 'castor_r'],
                             'turret': 'turret', 'gun': 'gun', 'spin': 'barrels', 'muzzle': 'muzzle', 'seat': 'seat', 'lod': 'lod', 'size': [2.2, 2.4, 4.4], 'front': '-z'})
    return root


FPS = 30


def _fcurves(act):
    """the action's F-curves (blender 5: layers > strips > channelbags; older: act.fcurves)"""
    if hasattr(act, 'layers') and len(act.layers):
        out = []
        for ly in act.layers:
            for st in ly.strips:
                for cb in st.channelbags: out += list(cb.fcurves)
        return out
    return list(act.fcurves)


def clips(J):
    """baked clips as muted NLA tracks, one track name per clip on every node it moves (the glTF exporter merges them):
    drive (5 s loop: the tyres turn 5 times and the castors 7, so it loops clean over 13.19 m; the castors wobble like
    a shopping trolley, the rig rattles), ram_hit (0.8 s: shoved back nose-up, the turret swings loose), die (2.4 s,
    hold the end: two wheels come off, a castor folds, the cubicle drops and lists, the gun tips over the back and its
    barrels spin down). blender axes: rotation_euler x = game x, blender y = game -z, blender z = game y."""
    bpy.context.scene.render.fps = FPS
    F = lambda t: 1 + round(t * FPS)

    def key(o, clip, path, frames):
        ad = o.animation_data_create(); ad.action = None
        base = getattr(o, path).copy()
        for f, v in frames:
            setattr(o, path, v); o.keyframe_insert(path, frame=f)
        act = ad.action; act.name = clip + '_' + o.name
        for fc in _fcurves(act):
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        tr = ad.nla_tracks.new(); tr.name = clip; tr.strips.new(clip, 1, act); tr.mute = True; ad.action = None
        setattr(o, path, base)

    def curve(o, clip, path, base, pts, n=None):
        """pts: [(t, delta tuple)] smooth (eased) between, sampled every 2 frames; values are base + delta"""
        fr = []
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            steps = max(1, round((t1 - t0) * FPS / 2))
            for k in range(steps):
                u = k / steps; e = u * u * (3 - 2 * u)
                fr.append((F(t0 + (t1 - t0) * u), tuple(b + a + (c - a) * e for b, a, c in zip(base, v0, v1))))
        fr.append((F(pts[-1][0]), tuple(b + c for b, c in zip(base, pts[-1][1]))))
        key(o, clip, path, fr)
    loc = lambda o: tuple(o.location); Z3 = (0, 0, 0)
    rig, tur, gun, bar = J['rig'], J['turret'], J['gun'], J['barrels']
    # drive
    for nm in ('wheel_rl', 'wheel_rr', 'wheel_ml', 'wheel_mr'): key(J[nm], 'drive', 'rotation_euler', [(F(k * 5 / 40), (-2 * math.pi * 5 * k / 40, 0, 0)) for k in range(41)])
    for nm in ('castor_l_spin', 'castor_r_spin'): key(J[nm], 'drive', 'rotation_euler', [(F(k * 5 / 56), (-2 * math.pi * 7 * k / 56, 0, 0)) for k in range(57)])
    for k, nm in enumerate(('castor_l', 'castor_r')):
        key(J[nm], 'drive', 'rotation_euler', [(F(i * 5 / 60), (0, 0, 0.07 * math.sin(2 * math.pi * 4 * i / 60 + k * 1.3) + 0.04 * math.sin(2 * math.pi * 9 * i / 60))) for i in range(61)])
    key(rig, 'drive', 'location', [(F(i * 5 / 60), (0, 0, 0.012 * math.sin(2 * math.pi * 6 * i / 60) + 0.006 * math.sin(2 * math.pi * 13 * i / 60))) for i in range(61)])
    key(rig, 'drive', 'rotation_euler', [(F(i * 5 / 60), (0.008 * math.sin(2 * math.pi * 5 * i / 60), 0.012 * math.sin(2 * math.pi * 7 * i / 60 + 1.0), 0)) for i in range(61)])
    # ram_hit
    curve(rig, 'ram_hit', 'location', Z3, [(0, Z3), (0.08, (0, -0.2, 0.03)), (0.3, (0, -0.1, 0)), (0.55, (0, -0.02, 0.01)), (0.8, Z3)])
    curve(rig, 'ram_hit', 'rotation_euler', Z3, [(0, Z3), (0.08, (0.15, 0, 0)), (0.28, (-0.05, 0, 0)), (0.5, (0.03, 0, 0)), (0.8, Z3)])
    curve(tur, 'ram_hit', 'rotation_euler', Z3, [(0, Z3), (0.1, (0, 0, 0.4)), (0.3, (0, 0, -0.22)), (0.52, (0, 0, 0.1)), (0.8, Z3)])
    curve(gun, 'ram_hit', 'rotation_euler', Z3, [(0, Z3), (0.08, (-0.25, 0, 0)), (0.3, (0.12, 0, 0)), (0.8, Z3)])
    for k, nm in enumerate(('castor_l', 'castor_r')):
        curve(J[nm], 'ram_hit', 'rotation_euler', Z3, [(0, Z3), (0.1, (0, 0, (0.6, -0.5)[k])), (0.3, (0, 0, (-0.3, 0.35)[k])), (0.55, (0, 0, (0.12, -0.1)[k])), (0.8, Z3)])
    # die
    curve(rig, 'die', 'location', Z3, [(0, Z3), (0.15, (0, 0.02, 0.06)), (0.3, (0, -0.03, -0.02)), (0.7, (0, 0.05, -0.28)), (0.95, (0, 0.03, -0.22)), (1.3, (0, 0.06, -0.3)), (2.4, (0, 0.06, -0.3))])
    curve(rig, 'die', 'rotation_euler', Z3, [(0, Z3), (0.15, (0.05, 0.04, 0)), (0.3, (-0.04, -0.05, 0)), (0.7, (-0.1, -0.24, 0.05)), (0.95, (-0.06, -0.18, 0.04)), (1.3, (-0.09, -0.22, 0.06)), (2.4, (-0.09, -0.22, 0.06))])
    wl, wr = J['wheel_ml'], J['wheel_rr']
    curve(wl, 'die', 'location', loc(wl), [(0, Z3), (0.3, Z3), (0.55, (-0.9, 0.0, 0.25)), (0.8, (-1.5, 0.0, -0.13)), (1.05, (-1.8, 0.0, 0.05)), (1.35, (-2.0, 0.0, -0.27)), (2.4, (-2.0, 0.0, -0.27))])
    curve(wl, 'die', 'rotation_euler', Z3, [(0, Z3), (0.3, Z3), (0.8, (-4.0, 0.8, 0)), (1.35, (-6.0, math.pi / 2, 0.3)), (2.4, (-6.0, math.pi / 2, 0.3))])
    curve(wr, 'die', 'location', loc(wr), [(0, Z3), (0.45, Z3), (0.75, (0.7, -0.6, 0.35)), (1.1, (1.3, -1.4, -0.1)), (1.5, (1.6, -2.2, -0.27)), (2.4, (1.6, -2.2, -0.27))])
    curve(wr, 'die', 'rotation_euler', Z3, [(0, Z3), (0.45, Z3), (1.1, (-7.0, -0.6, 0)), (1.5, (-9.0, -math.pi / 2, -0.2)), (2.4, (-9.0, -math.pi / 2, -0.2))])
    curve(J['castor_r'], 'die', 'rotation_euler', Z3, [(0, Z3), (0.5, Z3), (0.75, (0.9, 0, 0.4)), (0.9, (0.7, 0, 0.5)), (2.4, (0.8, 0, 0.5))])
    curve(J['castor_l'], 'die', 'rotation_euler', Z3, [(0, Z3), (0.2, (0, 0, 0.5)), (0.4, (0, 0, -0.4)), (0.7, (0, 0, 0.9)), (2.4, (0, 0, 0.9))])
    curve(tur, 'die', 'rotation_euler', Z3, [(0, Z3), (0.6, (0.1, 0, 0.3)), (1.0, (0.5, 0, 0.5)), (1.4, (1.25, 0, 0.6)), (1.6, (1.1, 0, 0.6)), (1.75, (1.2, 0, 0.6)), (2.4, (1.2, 0, 0.6))])
    curve(gun, 'die', 'rotation_euler', Z3, [(0, Z3), (0.6, Z3), (1.4, (0.5, 0, 0)), (2.4, (0.55, 0, 0))])
    curve(bar, 'die', 'rotation_euler', Z3, [(0, Z3), (0.2, (0, -2.5, 0)), (1.0, (0, -9.0, 0)), (2.0, (0, -11.5, 0)), (2.4, (0, -11.6, 0))])
    bpy.context.scene.frame_set(1)


def export_anim(root, file_id):
    os.makedirs(MODELS, exist_ok=True)
    for s in bpy.context.view_layer.objects.selected: s.select_set(False)
    root.select_set(True)
    for c in root.children_recursive: c.select_set(True)
    path = os.path.join(MODELS, file_id + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True,
                              export_extras=True, export_yup=True, export_texcoords=True, export_normals=True,
                              export_materials='EXPORT', export_image_format='AUTO', export_lights=False, export_cameras=False,
                              export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True,
                              export_optimize_animation_size=False, export_optimize_animation_keep_anim_object=True)
    tris, lo, hi = stats(root)
    print(f'JF_EXPORT {file_id}: {os.path.getsize(path) // 1024} KB, {tris} tris')
    return path


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    reset()
    root = build()
    if '--no-export' not in argv: export_anim(root, 'cast/c_' + ID)
    if '--no-sheet' not in argv: sheet(root, 'c_' + ID, exposure=-0.3)


main()
