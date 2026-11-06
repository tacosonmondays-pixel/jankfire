# Knife skin "Pizza Cutter" (w_knife_pizza).
# A restaurant pizza wheel at life size: a 100 mm stainless wheel (1.2 mm at the hub, ground to an edge), riveted
# hub caps, a stamped stainless fork with a cheek plate either side of the wheel, a curved thumb guard over the back of
# the wheel, a 135 mm candy-red handle (oval, a swell for the palm, finger grooves underneath, a hang hole).
# Held like every knife: the handle runs along the grip axis (y = 0) under the hand (z -0.036 .. +0.08), the wheel in
# front where the blade goes (its plane = the blade's flat, edge down). muzzle = the wheel's front edge.
# Made fun: a pepperoni slice stuck to the wheel, a string of cheese hanging off it, NOT A KNIFE printed on the handle.
# run: blender -b --python tools/blender/make_knife_pizza.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

WC = (0.0, -0.012, -0.141)   # wheel centre (game)
WR = 0.05                     # wheel radius
Z_F0, Z_F1, Z_END = -0.046, -0.036, 0.094  # ferrule front / back, handle end


def smooth01(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


def label_px(text, w, h, base, ink):
    def draw(px):
        px[:] = hexrgb(base)
        text_px(px, text, 2, (h - 7) // 2, 1, ink)
    return draw


def pepperoni_px(px):
    h, w = px.shape[:2]
    r = np.random.default_rng(9)
    px[:] = hexrgb(0xb8241a) * (0.9 + 0.15 * r.random((h, w, 1)))
    for _ in range(9): px_disc(px, r.uniform(2, w - 2), r.uniform(2, h - 2), r.uniform(0.8, 1.6), 0xf2c8a0)  # fat
    px_disc(px, w / 2, h / 2, w / 2, 0x7a1208, r_in=w / 2 - 1.2)  # the curled darker rim


def build():
    steel = mat('pz_steel', 0xe4e8ee, rough=0.14, metal=1.0)
    satin = mat('pz_satin', 0xc4cad2, rough=0.28, metal=1.0)
    chrome = mat('pz_chrome', 0xf2f4f8, rough=0.05, metal=1.0)
    red = mat('pz_red', 0xffffff, rough=0.3, clearcoat=0.7, tex=tex_noise('pz_red_t', 0xe0262a, var=0.06, size=16, seed=31))
    grip = mat('pz_grip', 0xffffff, rough=0.75, tex=tex_noise('pz_grip_t', 0x2a1416, var=0.1, size=16, seed=32))
    label = mat('pz_label', 0xffffff, rough=0.35, clearcoat=0.5, tex=tex_canvas('pz_label_t', 70, 9, label_px('NOT A KNIFE', 70, 9, 0xe0262a, 0xffe14d)))
    pep = mat('pz_pep', 0xffffff, rough=0.25, clearcoat=0.7, tex=tex_canvas('pz_pep_t', 16, 16, pepperoni_px))
    cheese = mat('pz_cheese', 0xffd84a, rough=0.3, clearcoat=0.5)

    # ---- the wheel: a thin disc ground to an edge, a centre boss, riveted hub caps either side
    wheel = lathe([(0.0, 0.0006), (0.012, 0.0006), (0.043, 0.0005), (WR - 0.0015, 0.00035), (WR, 0.00008), (WR, -0.00008),
                   (WR - 0.0015, -0.00035), (0.043, -0.0005), (0.012, -0.0006), (0.0, -0.0006)], WC, steel, seg=56, axis='x', name='wheel')
    hub = [lathe([(0.0, 0.0042), (0.0045, 0.0041), (0.0082, 0.0032), (0.0095, 0.0018), (0.0095, 0.0006)], WC, chrome, seg=24, axis='x', name='hubR'),
           lathe([(0.0, -0.0042), (0.0045, -0.0041), (0.0082, -0.0032), (0.0095, -0.0018), (0.0095, -0.0006)], WC, chrome, seg=24, axis='x', name='hubL')]
    for o in [wheel] + hub: uv_box(o, 0.05)

    # ---- the fork: one stamped cheek plate either side of the wheel, from the axle back up into the shank
    def cheek(sx):
        # around the hub's back half, then back along the shank (top edge) and forward again (bottom edge)
        poly = [(WC[2] + 0.011 * math.cos(math.radians(a)), WC[1] + 0.011 * math.sin(math.radians(a))) for a in range(-150, 151, 25)]
        poly += [(-0.104, 0.0025), (-0.078, 0.0055), (-0.058, 0.0058), (-0.058, -0.0052), (-0.08, -0.0068), (-0.108, -0.0115)]
        o = side(list(reversed(poly)), 0.0016, (sx * 0.0024, 0, 0), satin, bev=0.0005, name='cheek')
        return o
    fork = [cheek(1), cheek(-1)]
    # the shank: the two cheeks meet and run back into the ferrule
    fork.append(box((0.0068, 0.0104, 0.03), (0, 0.0, -0.06), satin, bev=0.0012, name='shank'))  # runs into the ferrule
    # the thumb guard: a curved hood over the back-top of the wheel, a flat pad to push down on
    hood = []
    for k in range(9):
        a = math.radians(70 + 12 * k)
        hood.append((0.0, WC[1] + (WR + 0.006) * math.sin(a), WC[2] + (WR + 0.006) * math.cos(a)))
    hood = [p for p in hood if p[2] > WC[2] - 0.02]
    fork.append(sweep(hood, 0.0042, satin, seg=10, name='hood', squash=(0.38, 1.0)))
    fork.append(rod((0, WC[1] + (WR + 0.006) * math.sin(math.radians(70)), WC[2] + (WR + 0.006) * math.cos(math.radians(70))), (0, 0.003, -0.07), 0.0028, satin, seg=8, name='strut'))
    pad = ball(1.0, (0, 0.0095, -0.072), satin, scale=(0.012, 0.0028, 0.016), seg=16, rings=8, name='pad')
    fork.append(pad)
    for o in fork: uv_box(o, 0.05)

    # ---- ferrule + the handle
    ferrule = lathe([(0.0068, Z_F0), (0.0092, Z_F0 + 0.0012), (0.0102, Z_F0 + 0.004), (0.0108, Z_F1 - 0.001), (0.0102, Z_F1)], (0, 0, 0), chrome, seg=20, axis='z', name='ferrule')
    uv_box(ferrule, 0.05)
    N, K = 34, 20
    zs = [Z_F1 - 0.002 + (Z_END - Z_F1 + 0.002) * i / (N - 1) for i in range(N)]
    def hw(z):  # half width (x) and half heights (top, bottom)
        t = (z - Z_F1) / (Z_END - Z_F1)
        swell = 0.0018 * math.sin(math.pi * min(1.0, max(0.0, (t - 0.2) / 0.75)))
        end = math.sqrt(max(0.0, 1 - max(0.0, (z - (Z_END - 0.012)) / 0.012) ** 2))
        return (0.0098 + swell) * end, (0.0118 + swell * 1.3) * end, (0.0112 + swell) * end
    def groove(z):  # three finger grooves under the front half
        if z > 0.045: return 0.0
        return 0.0016 * max(0.0, math.sin((z - Z_F1) / 0.081 * 3 * math.pi)) ** 2
    def ring(i, t):
        z = zs[i]; a, bt, bb = hw(z); out = []
        for j in range(K):
            th = 2 * math.pi * j / K; c, s = math.cos(th), math.sin(th)
            up = (bt if s >= 0 else bb - groove(z)) * math.copysign(abs(s) ** 0.8, s)
            out.append((up, a * math.copysign(abs(c) ** 0.8, c)))
        return out
    handle = loft([(0, 0, z) for z in zs], ring, m=red, name='handle', close=(False, True), smooth_angle=60)
    for mm in (grip, label): handle.data.materials.append(mm)
    me = handle.data
    for f in me.polygons:  # the grip strip underneath, the label on the camera side (-x)
        gz = -f.center.y
        if f.normal.z < -0.75 and gz < 0.07: f.material_index = 1
        elif f.normal.x < -0.8 and -0.02 < gz < 0.07: f.material_index = 2
    uv_box(handle, 0.05)
    uvl = me.uv_layers.active.data
    for f in me.polygons:
        if f.material_index != 2: continue
        for li in f.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uvl[li].uv = (((-v.y) - (-0.02)) / 0.09, (v.z + 0.0065) / 0.013)
    # hang hole through the end
    cut(handle, cyl(0.0042, 0.05, (0, 0.0, Z_END - 0.014), axis='x', seg=14, name='hole'))
    # ---- the fun: a pepperoni stuck to the wheel's left face, a string of cheese hanging off the edge
    pz = cyl(0.0125, 0.0018, (-0.0016, WC[1] + 0.02, WC[2] - 0.016), pep, axis='x', seg=18, bev=0.0006, name='pepperoni')
    pz.rotation_euler = (0.25, 0, 0.12)
    apply_mods(pz); bpy.context.view_layer.update()
    uv_planar(pz, (-0.0016, WC[1] + 0.02, WC[2] - 0.016), (0.026, 0.026), '-x')
    a0 = math.radians(-120)
    p0 = (0.0, WC[1] + WR * math.sin(a0), WC[2] + WR * math.cos(a0))
    chs = [p0, (0.0012, p0[1] - 0.008, p0[2] + 0.002), (0.002, p0[1] - 0.018, p0[2] + 0.001), (0.0016, p0[1] - 0.026, p0[2] - 0.002)]
    ch = sweep(chs, [0.0016, 0.0011, 0.0013, 0.0024], cheese, seg=7, name='cheese')
    blob = ball(0.0036, chs[-1], cheese, scale=(1, 1.25, 1), seg=10, rings=6, name='drip')
    WZ = {'pz_red': 'a', 'pz_grip': 'a', 'pz_chrome': 'b', 'pz_steel': 'b', 'pz_satin': 'b', 'pz_pep': 'n', 'pz_cheese': 'n', 'pz_label': 'n'}
    parts = zone_join([handle, ferrule, wheel] + hub + fork + [pz, ch, blob], 'pizza', WZ, default='b')
    meta = {'kind': 'weapon', 'id': 'knife', 'skin': 'knife_pizza', 'paint': ['pz_red'], 'muzzle': [0, WC[1], WC[2] - WR], 'hatAt': [[0, 0.0136, 0.03], 0.05]}
    return finish('w_knife_pizza', parts, meta)


main(build, 'w_knife_pizza', exposure=-0.4)
