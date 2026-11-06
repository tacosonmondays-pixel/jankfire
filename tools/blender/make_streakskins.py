# Killstreak skins (shared/cosmetics.js STREAK_SKINS): other bodies for the streaks, all original, chunky low-poly,
# each its own small lazy file (x_<skin>.glb, fetched the first time someone shows it).
# Wrecking Ball shells (wreck.js keeps the Blender ball's chain stub, viewing slot and face, and swaps the shell): radius
# exactly 1.1 round the origin (physics + outline), an opening cut where the slot sits (latitude 0.42 at the front):
#   x_wreck_disco     a mirror-tiled disco ball, the tiles tinted pink / cyan / gold here and there
#   x_wreck_meatball  a lumpy meatball, sauce running down it, a basil leaf stuck on top
#   x_wreck_bowling   a glossy marbled purple bowling ball with three finger holes and a gold 16 LB stamp
# Giant Duck (the duck that orbits the black hole, ~1.6 m long, faces -z):
#   x_duck_robot      a boxy chrome robo duck, a red visor eye, bolts, an antenna
#   x_duck_flamingo   an inflatable pink pool flamingo ring (the duck stand-in floats round the hole)
# Chicken Strike (what rains down, nose to -z like the chicken projectile, ~0.7 m):
#   x_strike_pigeon   a grey city pigeon dive-bombing, wings swept back, a breadcrumb in its beak
#   x_strike_drone    a quadcopter with four rotors, a blinking light and a bomb slung under it
# Moon Boots (icons + HUD; they don't show on the body):
#   x_moon_heelys     a pair of chunky skate sneakers with a wheel in each heel
#   x_moon_rocket     high-tops with a rocket nozzle on each heel and fins
#   x_moon_clown      huge red clown shoes with yellow laces
# Spinbot (icons + HUD):
#   x_spin_halo       the cheater shades under a golden halo
#   x_spin_aura       the shades in a spiky anime power aura
# Spy Satellite (icons + HUD):
#   x_sat_pizza       a pizza used as the dish on a little relay box
#   x_sat_blimp       a CCTV blimp: a fat blimp with a camera pod and fins
# run: blender -b --python tools/blender/make_streakskins.py   (-- --no-sheet)
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link

R, LAT = 1.1, 0.42


def uvs(parts, size=0.15):
    for o in parts:
        if o.type == 'MESH' and not o.data.uv_layers: uv_box(o, size)
    return parts


def flat(pts, depth, pos=(0, 0, 0), m=None, bev=0.0, name='flat', rot=None):
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new(gv(x, y, depth / 2)) for x, y in pts])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=gv(0, 0, -depth), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m); o.location = gv(*pos)
    if rot: o.rotation_euler = Euler((rot[0], -rot[2], rot[1]), 'YZX')
    smooth(o, 30); bevel(o, bev, 2, 30)
    return o


def ring(r, t, pos=(0, 0, 0), m=None, n=24, name='ring', rot=None):
    o = tube([(math.cos(2 * math.pi * i / n) * r, 0, math.sin(2 * math.pi * i / n) * r) for i in range(n)], t, m, seg=8, name=name, closed=True)
    o.location = gv(*pos)
    if rot: o.rotation_euler = Euler((rot[0], -rot[2], rot[1]), 'YZX')
    return o


def slot_cut(o):
    """cut the viewing slot's opening out of a shell (the game's frame + face sit in it)"""
    c = box((0.7, 0.24, 0.9), (0, math.sin(LAT) * R, -math.cos(LAT) * R), None, rot=(LAT, 0, 0), name='slotcut')
    cut(o, c)
    return o


def shell(name, m, seg=24, rings=14, lump=0.0, seed=1):
    o = ball(R, (0, 0, 0), m, seg=seg, rings=rings, name=name)
    if lump: jitter(o, lump, seed=seed)
    slot_cut(o)
    return o


def root(fid, parts, meta=None):
    return (finish(fid, parts, dict({'kind': 'streakskin', 'id': fid}, **(meta or {}))), fid)


# ------------------------------------------------------------ wrecking ball shells
def disco():
    def tiles(px):
        r = np.random.default_rng(4)
        for y in range(32):
            for x in range(32):
                g = 0.55 + 0.45 * r.random()
                px[y, x] = (g, g, g * 1.02)
                if r.random() < 0.08: px[y, x] = hexrgb([0xff4fd8, 0x4fd8ff, 0xffe14d][int(r.random() * 3)])
                if x % 4 == 0 or y % 4 == 0: px[y, x] = (0.15, 0.15, 0.18)
    m = mat('wd_mirror', 0xd8dce4, rough=0.12, metal=1.0, tex=tex_canvas('wd_tiles', 32, 32, tiles))
    o = shell('ball_shell', m, seg=20, rings=12)
    for p in o.data.polygons: p.use_smooth = False  # faceted: every face a mirror
    uv_box(o, 0.55)
    return root('x_wreck_disco', [o], {'streak': 'wreckingball'})


def meatball():
    meat = mat('wm_meat', 0x7a4228, rough=0.7, tex=tex_noise('wm_meat_t', 0x7a4228, 0.25, 32, speck=0xc89060, speck_p=0.12, seed=7))
    sauce = mat('wm_sauce', 0xc8201a, rough=0.25, clearcoat=0.8)
    basil = mat('wm_basil', 0x2a8a2a, rough=0.5, clearcoat=0.3)
    o = shell('ball_shell', meat, seg=20, rings=12, lump=0.07, seed=5)
    uv_box(o, 0.4)
    p = [o]
    for i, a in enumerate((0.3, 1.4, 2.6, 3.9, 5.1)):  # sauce drips down from the top
        pts = [(math.cos(a) * (R + 0.01) * math.cos(t), (R + 0.01) * math.sin(t), math.sin(a) * (R + 0.01) * math.cos(t)) for t in [1.45 - 0.12 * k for k in range(6 + i % 3)]]
        p.append(tube(pts, 0.07 - 0.008 * (i % 2), sauce, seg=6, name='sauce'))
    p.append(ball(0.42, (0, R - 0.18, 0.1), sauce, scale=(1, 0.35, 1), seg=12, rings=6, name='sauce_cap'))
    leaf = flat([(0, 0), (0.12, 0.08), (0.2, 0.25), (0.1, 0.4), (0, 0.45), (-0.1, 0.4), (-0.2, 0.25), (-0.12, 0.08)], 0.03, (0.25, R + 0.05, 0.3), basil, bev=0.008, name='basil', rot=(-1.3, 0.6, 0))
    p.append(leaf)
    return root('x_wreck_meatball', [join(uvs(p), 'ball_shell')], {'streak': 'wreckingball'})


def bowling():
    def swirl(px):
        for y in range(32):
            for x in range(32):
                k = 0.5 + 0.5 * math.sin(x * 0.35 + 3 * math.sin(y * 0.2))
                px[y, x] = hexrgb(0x5a1a9a) * (0.6 + 0.4 * k) + hexrgb(0xff4fd8) * (0.35 * (1 - k))
    m = mat('wbw_resin', 0x6a2aa8, rough=0.12, clearcoat=1.0, tex=tex_canvas('wbw_swirl', 32, 32, swirl))
    o = shell('ball_shell', m, seg=24, rings=14)
    uv_box(o, 0.7)
    for (lat, az, r) in ((1.05, 0.5, 0.11), (1.15, 1.2, 0.11), (0.75, 0.9, 0.13)):  # three finger holes on the back-top
        c = cyl(r, 0.8, (R * math.cos(lat) * math.cos(az), R * math.sin(lat), R * math.cos(lat) * math.sin(az)), None, axis='y', seg=10, name='hole')
        c.rotation_euler = (Vector((R * math.cos(lat) * math.cos(az), -R * math.cos(lat) * math.sin(az), R * math.sin(lat))).to_track_quat('Z', 'Y').to_euler())
        cut(o, c)
    gold = mat('wbw_gold', 0xffc83a, rough=0.2, metal=1.0)
    def stamp(px):
        px[:, :] = hexrgb(0x5a1a9a); text_px(px, '16 LB', 2, 2, 1, 0xffc83a)
    st = box((0.42, 0.13, 0.02), (0.55, 0.15, 0.95), mat('wbw_stamp', 0xffc83a, rough=0.3, metal=0.6, tex=tex_canvas('wbw_stamp_t', 34, 11, stamp)), rot=(0, 2.6, 0), name='stamp')
    apply_mods(st); me = st.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = ((v.x + 0.21) / 0.42, (v.z + 0.065) / 0.13)
    return root('x_wreck_bowling', [join([o, st], 'ball_shell')], {'streak': 'wreckingball'})


# ------------------------------------------------------------ giant duck stand-ins
def robo_duck():
    chrome = mat('dr_chrome', 0xc8ccd4, rough=0.2, metal=0.95)
    dark = mat('dr_dark', 0x2a2a34, rough=0.4, metal=0.6)
    eye = mat('dr_eye', 0xff2020, emit=0xff2020, strength=1.2)
    beak = mat('dr_beak', 0xffa020, rough=0.3, metal=0.7)
    p = [box((0.9, 0.62, 1.2), (0, 0.31, 0.1), chrome, bev=0.12, seg=2, name='body'),
         box((0.62, 0.56, 0.6), (0, 0.9, -0.3), chrome, bev=0.1, seg=2, name='head'),
         box((0.5, 0.14, 0.5), (0, 0.84, -0.82), beak, bev=0.05, taper=(0.7, 0.8), name='beak'),
         box((0.58, 0.12, 0.06), (0, 1.0, -0.62), eye, name='visor'),
         box((0.2, 0.45, 0.6), (0.52, 0.36, 0.2), dark, bev=0.05, name='wing_r'), box((0.2, 0.45, 0.6), (-0.52, 0.36, 0.2), dark, bev=0.05, name='wing_l'),
         box((0.3, 0.3, 0.3), (0, 0.55, 0.78), chrome, bev=0.06, taper=(0.5, 0.6), rot=(-0.6, 0, 0), name='tail'),
         rod((0, 1.17, -0.3), (0.05, 1.45, -0.25), 0.02, dark, name='antenna'), ball(0.05, (0.05, 1.47, -0.25), eye, seg=8, rings=6, name='antenna_tip')]
    for x in (-0.3, 0.3):
        for z in (-0.3, 0.5): p.append(cyl(0.035, 0.03, (x * 1.55, 0.45, z), dark, axis='x', seg=6, name='bolt'))
    return root('x_duck_robot', [join(uvs(p), 'duck')], {'streak': 'giantduck'})


def flamingo():
    pink = mat('df_vinyl', 0xff6bb8, rough=0.25, clearcoat=0.9, tex=tex_noise('df_vinyl_t', 0xff6bb8, 0.05, 16, seed=2))
    beak = mat('df_beak', 0x222222, rough=0.3, clearcoat=0.6)
    white = mat('df_white', 0xf6f0f4, rough=0.3, clearcoat=0.6)
    p = [ring(0.55, 0.26, (0, 0.26, 0.15), pink, n=20, name='float')]
    neck = [(0, 0.4, -0.4), (0, 0.8, -0.5), (0, 1.15, -0.35), (0, 1.3, -0.55)]
    p.append(sweep(neck, [0.13, 0.11, 0.1, 0.1], pink, seg=10, name='neck'))
    p.append(ball(0.17, (0, 1.32, -0.6), pink, seg=12, rings=8, name='head'))
    p.append(rod((0, 1.3, -0.72), (0, 1.16, -0.92), 0.06, white, r1=0.03, name='beak'))
    p.append(rod((0, 1.17, -0.9), (0, 1.08, -0.98), 0.03, beak, r1=0.01, name='beak_tip'))
    for s in (-1, 1): p.append(ball(0.03, (s * 0.12, 1.37, -0.68), beak, seg=6, rings=4, name='eye'))
    p.append(box((0.5, 0.3, 0.1), (0, 0.5, 0.65), pink, bev=0.05, taper=(0.4, 0.5), rot=(0.6, 0, 0), name='tail'))
    return root('x_duck_flamingo', [join(uvs(p), 'duck')], {'streak': 'giantduck'})


# ------------------------------------------------------------ chicken strike
def pigeon():
    grey = mat('sp_grey', 0x8a8e9a, rough=0.6, tex=tex_noise('sp_grey_t', 0x8a8e9a, 0.12, 16, seed=3))
    neck = mat('sp_neck', 0x4a8a7a, rough=0.3, metal=0.5, clearcoat=0.6)
    dark = mat('sp_dark', 0x3a3c44, rough=0.6)
    beak = mat('sp_beak', 0xd8c8a8, rough=0.5)
    eye = mat('sp_eye', 0xff8a20, emit=0xff6a10, strength=0.6)
    bread = mat('sp_bread', 0xe8b860, rough=0.7)
    p = [ball(0.18, (0, 0, 0.05), grey, scale=(1, 0.9, 1.6), seg=12, rings=8, name='body'),
         ball(0.12, (0, 0.06, -0.26), neck, seg=10, rings=6, name='neck'),
         ball(0.09, (0, 0.1, -0.38), grey, seg=10, rings=6, name='head'),
         rod((0, 0.1, -0.45), (0, 0.08, -0.53), 0.025, beak, r1=0.008, name='beak'),
         box((0.06, 0.04, 0.05), (0, 0.07, -0.56), bread, bev=0.01, name='crumb')]
    for s in (-1, 1):
        p.append(ball(0.02, (s * 0.06, 0.13, -0.41), eye, seg=6, rings=4, name='eye'))
        p.append(flat([(0, 0), (0.45, 0.05), (0.5, 0.12), (0.3, 0.16), (0, 0.12)], 0.025, (s * 0.12, 0.08, 0.05), grey, bev=0.006, name='wing', rot=(0, s * -1.25, s * 0.25)))
    p.append(flat([(-0.1, 0), (0.1, 0), (0.14, 0.2), (-0.14, 0.2)], 0.02, (0, 0.02, 0.33), dark, name='tail', rot=(-1.4, 0, 0)))
    return root('x_strike_pigeon', [join(uvs(p), 'bird')], {'streak': 'chickenstrike'})


def drone():
    body = mat('sd_body', 0x22242c, rough=0.3, clearcoat=0.7)
    arm = mat('sd_arm', 0x3a3c48, rough=0.4, metal=0.5)
    prop = mat('sd_prop', 0xff4fd8, rough=0.3, clearcoat=0.6)
    led = mat('sd_led', 0x4fd8ff, emit=0x4fd8ff, strength=1.2)
    bomb = mat('sd_bomb', 0x4a5a2a, rough=0.5)
    stripe = mat('sd_stripe', 0xffe14d, rough=0.4)
    p = [box((0.22, 0.08, 0.3), (0, 0, 0), body, bev=0.03, name='hull'), box((0.08, 0.03, 0.04), (0, 0.02, -0.16), led, name='light')]
    for sx in (-1, 1):
        for sz in (-1, 1):
            p.append(rod((0, 0, 0), (sx * 0.24, 0.02, sz * 0.24), 0.018, arm, name='arm'))
            p.append(cyl(0.03, 0.05, (sx * 0.24, 0.04, sz * 0.24), arm, axis='y', seg=8, name='motor'))
            p.append(box((0.26, 0.008, 0.035), (sx * 0.24, 0.075, sz * 0.24), prop, rot=(0, sx * sz * 0.6, 0), name='prop'))
    p.append(cyl(0.06, 0.2, (0, -0.13, 0.02), bomb, axis='z', seg=10, bev=0.02, name='bomb'))
    p.append(cyl(0.062, 0.03, (0, -0.13, -0.04), stripe, axis='z', seg=10, name='stripe'))
    p.append(cyl(0.04, 0.06, (0, -0.13, 0.15), bomb, axis='z', seg=4, r2=0.07, name='fins'))
    return root('x_strike_drone', [join(uvs(p), 'drone')], {'streak': 'chickenstrike'})


# ------------------------------------------------------------ moon boots
def sneaker(x, M, kind):
    p = [box((0.12, 0.04, 0.3), (x, 0.02, 0), M['sole'], bev=0.012, name='sole'),
         box((0.12, 0.1, 0.27), (x, 0.08, 0.01), M['upper'], bev=0.04, name='upper'),
         box((0.11, 0.06, 0.1), (x, 0.08, -0.12), M['toe'], bev=0.03, name='toe')]
    if kind != 'clown': p.append(box((0.11, 0.16, 0.13), (x, 0.17, 0.07), M['upper'], bev=0.04, name='ankle'))
    for i in range(3): p.append(rod((x - 0.04, 0.12 + i * 0.025, -0.04 + i * 0.03), (x + 0.04, 0.12 + i * 0.025, -0.04 + i * 0.03), 0.006, M['lace'], seg=4, name='lace'))
    if kind == 'heelys': p.append(cyl(0.035, 0.03, (x, 0.0, 0.11), M['wheel'], axis='x', seg=10, name='wheel'))
    if kind == 'rocket':
        p.append(cyl(0.04, 0.08, (x, 0.08, 0.19), M['nozzle'], axis='z', r2=0.025, seg=10, name='nozzle'))
        p.append(cyl(0.03, 0.02, (x, 0.08, 0.235), M['flame'], axis='z', seg=10, name='flame'))
        for s in (-1, 1): p.append(box((0.006, 0.06, 0.06), (x + s * 0.062, 0.1, 0.14), M['fin'], taper=(1, 0.3), name='fin'))
    return p


def boots(kind, fid, cols):
    M = {k: mat(f'{fid}_{k}', c[0], rough=c[1], metal=c[2] if len(c) > 2 else 0.0, clearcoat=0.4, **({'emit': c[0], 'strength': 1.2} if k == 'flame' else {})) for k, c in cols.items()}
    a = join(uvs(sneaker(0.0, M, kind)), 'boot_l')
    if kind == 'clown':
        for v in a.data.vertices: v.co.y *= 1.8 if v.co.y > 0 else 1.0; v.co.x *= 1.25  # (blender +y = the toe)
    b = a.copy(); b.name = 'boot_r'; _link(b)
    a.location = gv(-0.08, 0, -0.02); b.location = gv(0.1, 0, 0.06); b.rotation_euler = Euler((0, 0, math.radians(-14)), 'XYZ')
    return root(fid, [a, b], {'streak': 'moonboots'})


def heelys(): return boots('heelys', 'x_moon_heelys', {'sole': (0xf2f2f2, 0.5), 'upper': (0x4fd8ff, 0.4), 'toe': (0xf2f2f2, 0.4), 'lace': (0xffe14d, 0.5), 'wheel': (0x39ff14, 0.3)})
def rocket(): return boots('rocket', 'x_moon_rocket', {'sole': (0x2a2a34, 0.5), 'upper': (0xff3030, 0.35), 'toe': (0xf2f2f2, 0.4), 'lace': (0xf2f2f2, 0.5), 'nozzle': (0xc8ccd4, 0.2, 0.9), 'flame': (0xffa020, 0.3), 'fin': (0xffe14d, 0.4)})
def clown(): return boots('clown', 'x_moon_clown', {'sole': (0x2a2a34, 0.6), 'upper': (0xff2a2a, 0.25), 'toe': (0xff2a2a, 0.25), 'lace': (0xffe14d, 0.5)})


# ------------------------------------------------------------ spinbot
def shades(glass, frame):
    lens = [(2 * x, 2 * y) for x, y in [(-0.005, 0.02), (-0.075, 0.03), (-0.088, -0.005), (-0.07, -0.03), (-0.02, -0.032), (-0.006, -0.012)]]
    p = []
    for s in (-1, 1):
        pts = [(s * (x - 0.005), y) for x, y in lens]
        p.append(flat(pts if s < 0 else pts[::-1], 0.016, (0, 0, 0), glass, bev=0.004, name='lens'))
    p.append(box((0.38, 0.024, 0.024), (0, 0.052, 0.002), frame, bev=0.006, name='brow'))
    p.append(box((0.04, 0.016, 0.02), (0, 0.012, 0.002), frame, bev=0.004, name='bridge'))
    for s in (-1, 1): p.append(box((0.016, 0.018, 0.09), (s * 0.186, 0.046, 0.045), frame, bev=0.004, rot=(0, -s * 0.12, 0), name='temple'))
    return p


def halo():
    glass = mat('sh_glass', 0x3a1460, rough=0.12, metal=0.55, clearcoat=1.0); frame = mat('sh_frame', 0xf2f2f2, rough=0.3, clearcoat=0.7)
    gold = mat('sh_gold', 0xffd24a, rough=0.15, metal=1.0, emit=0xffc020, strength=0.5)
    p = shades(glass, frame) + [ring(0.16, 0.022, (0, 0.2, 0.02), gold, n=24, name='halo')]
    for i in range(6):
        a = i * math.pi / 3
        p.append(flat([(0, 0.0), (0.012, 0.03), (0, 0.06), (-0.012, 0.03)], 0.006, (math.cos(a) * 0.26, 0.05 + math.sin(a) * 0.2, 0), gold, name='ray'))
    return root('x_spin_halo', [join(p, 'shades')], {'streak': 'spinbot'})


def aura():
    glass = mat('sa_glass', 0x101018, rough=0.08, metal=0.6, clearcoat=1.0); frame = mat('sa_frame', 0xffe14d, rough=0.3, metal=0.6)
    fire = mat('sa_fire', 0xffe14d, emit=0xffc020, strength=1.0, alpha=0.75)
    fire2 = mat('sa_fire2', 0x4fd8ff, emit=0x4fd8ff, strength=1.0, alpha=0.6)
    p = shades(glass, frame)
    spikes = []
    for i in range(11):
        a = math.pi * (0.1 + 0.8 * i / 10)
        r0, r1 = 0.24, 0.42 + 0.08 * ((i * 7) % 3)
        c, s = math.cos(a), math.sin(a)
        spikes.append(flat([(c * r0 - s * 0.05, s * r0 + c * 0.05 - 0.1), (c * r1, s * r1 - 0.1), (c * r0 + s * 0.05, s * r0 - c * 0.05 - 0.1)], 0.02, (0, 0, 0.06), fire if i % 2 else fire2, name='spike'))
    return root('x_spin_aura', [join(p, 'shades'), join(spikes, 'aura')], {'streak': 'spinbot'})


# ------------------------------------------------------------ satellite
def pizza_sat():
    crust = mat('sz_crust', 0xd8a050, rough=0.6, tex=tex_noise('sz_crust_t', 0xd8a050, 0.15, 16, seed=6))
    sauce = mat('sz_cheese', 0xffd24a, rough=0.35, clearcoat=0.4, tex=tex_noise('sz_cheese_t', 0xffd24a, 0.12, 16, speck=0xff9a30, speck_p=0.15, seed=8))
    pep = mat('sz_pep', 0xc82020, rough=0.4, clearcoat=0.5)
    box_m = mat('sz_box', 0xf2f2f2, rough=0.4, clearcoat=0.5)
    steel = mat('sz_steel', 0xc8ccd4, rough=0.3, metal=0.8)
    eye = mat('sz_eye', 0xff2020, emit=0xff2020, strength=1.2)
    dish = lathe([(0.0, 0.0), (0.3, 0.05), (0.34, 0.08), (0.3, 0.07), (0.0, 0.03)], (0, 0, 0), crust, seg=16, axis='y', name='crust')
    top = lathe([(0.0, 0.035), (0.29, 0.06), (0.0, 0.05)], (0, 0, 0), sauce, seg=16, axis='y', name='cheese')
    parts = [dish, top]
    for i, (r, a) in enumerate(((0.15, 0.3), (0.2, 2.1), (0.1, 3.8), (0.22, 4.9), (0.05, 1.2))):
        parts.append(cyl(0.045, 0.015, (math.cos(a) * r, 0.065 + 0.01 * r, math.sin(a) * r), pep, axis='y', seg=8, name='pep'))
    pz = join(uvs(parts), 'pizza'); pz.rotation_euler = Euler((math.radians(-35), 0, 0), 'XYZ'); pz.location = gv(0, 0.18, -0.05)
    p = [box((0.24, 0.24, 0.24), (0, -0.05, 0.05), box_m, bev=0.02, name='relay'), rod((0, 0.07, 0.0), (0, 0.17, -0.04), 0.012, steel, name='mast'),
         rod((0.1, 0.07, 0.12), (0.14, 0.32, 0.18), 0.004, steel, name='whip'), ball(0.016, (0.14, 0.32, 0.18), eye, seg=8, rings=6, name='tip')]
    return root('x_sat_pizza', [join(uvs(p) + [pz], 'sat')], {'streak': 'satellite'})


def blimp():
    skin = mat('sb_skin', 0xc8ccd4, rough=0.35, metal=0.3, clearcoat=0.6)
    stripe = mat('sb_stripe', 0xff4fd8, rough=0.3, clearcoat=0.6)
    dark = mat('sb_dark', 0x22242c, rough=0.4)
    lens = mat('sb_lens', 0xff2020, emit=0xff2020, strength=1.2)
    prof = [(0.0, 0.62), (0.12, 0.58), (0.2, 0.45), (0.24, 0.2), (0.24, -0.1), (0.2, -0.35), (0.12, -0.52), (0.0, -0.6)]
    p = [lathe(prof, (0, 0, 0), skin, seg=14, axis='z', name='envelope'), cyl(0.245, 0.06, (0, 0, 0.05), stripe, axis='z', seg=14, name='band')]
    for a in range(4): p.append(box((0.02, 0.16, 0.16), (0, 0, 0.52), dark, taper=(1, 0.3), rot=(0, 0, a * math.pi / 2), name='fin'))
    p += [box((0.1, 0.07, 0.2), (0, -0.27, 0.0), dark, bev=0.02, name='gondola'), ball(0.05, (0, -0.33, -0.08), dark, seg=10, rings=6, name='cam'), ball(0.025, (0, -0.34, -0.12), lens, seg=8, rings=6, name='lens')]
    return root('x_sat_blimp', [join(uvs(p), 'blimp')], {'streak': 'satellite'})


def build():
    return [f() for f in (disco, meatball, bowling, robo_duck, flamingo, pigeon, drone, heelys, rocket, clown, halo, aura, pizza_sat, blimp)]


main_multi(build, res=(420, 300), exposure=-0.8)
