# Hand Cannon (bowling_cannon): a pirate hand mortar, built like the real bronze guns: a cast barrel with a muzzle
# swell, astragals and fillets, a chase girdle, two reinforces with their rings, a base ring and a cascabel button,
# trunnions with rimbases, the vent field + touch hole with a slow-match fuse (glowing ember, sparks), strapped with
# iron bands onto an oak bed that ends in a grip and a tiller butt. Old bronze: crusty with green patina. Loaded with
# a swirly bowling ball, finger holes up. Game metres, the code model's size. No sights: it carries an 'ads' pose
# like the bowling launcher (tucked down and right). Made fun: real bronze cannons have two cast lifting handles on
# top called dolphins. These ones are bowling pins.
# run: blender -b --python tools/blender/make_bowling_cannon.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

MUZ = -0.6
BORE = 0.124


def fixmats(o):  # boolean cuts give the new faces an empty material slot: give them the object's own
    me = o.data
    if len(me.materials) < 2: return o
    for p in me.polygons:
        if me.materials[p.material_index] is None: p.material_index = 0
    while len(me.materials) > 1 and me.materials[-1] is None: me.materials.pop()
    return o


def tex_walnut(name, base, dark, size=64, seed=5, lines=6):  # long thin grain lines, gentle wobble, tiles both ways
    r = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size] / size
    warp = np.zeros_like(x)
    for f, a in ((1, 0.03), (2, 0.015), (4, 0.006)):
        warp += a * np.sin(2 * math.pi * (f * x + r.random())) * np.cos(2 * math.pi * (f * y + r.random()))
    g = 0.5 + 0.5 * np.sin(2 * math.pi * lines * (y + warp))
    t = np.clip((g > 0.86) * 0.65 + 0.25 * g ** 3 + 0.1 * r.random((size, size)), 0, 1)
    px = hexrgb(base)[None, None] * (1 - t[:, :, None]) + hexrgb(dark)[None, None] * t[:, :, None]
    return tex_canvas(name, size, size, lambda p: p.__setitem__(slice(None), px))


def swirl(px):  # the bowling ball (same swirl as the launcher's)
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w] / w
    v = np.sin(6 * xx + 3 * np.sin(5 * yy + 2 * np.sin(4 * xx))) + np.sin(7 * yy + 2 * np.cos(6 * xx))
    t = (v - v.min()) / (np.ptp(v) + 1e-6)
    a, b, c = hexrgb(0x2a3aa8), hexrgb(0x6b7bff), hexrgb(0xb070ff)
    px[:] = np.where(t[:, :, None] < 0.5, a + (b - a) * (t[:, :, None] * 2), b + (c - b) * ((t[:, :, None] - 0.5) * 2))


def build():
    def patina(px):  # old bronze: warm metal with darker tarnish, verdigris gathering in organic clumps
        h, w = px.shape[:2]
        r = np.random.default_rng(201)
        def smooth(octs):
            f = np.zeros((h, w))
            for o, wt in octs:
                g = r.random((o, o)); t = np.arange(w) * o / w
                i0 = np.floor(t).astype(int); fr = t - i0; i1 = (i0 + 1) % o; fr = fr * fr * (3 - 2 * fr)
                rows = g[i0] * (1 - fr)[:, None] + g[i1] * fr[:, None]
                f += wt * (rows[:, i0] * (1 - fr)[None, :] + rows[:, i1] * fr[None, :])
            return (f - f.min()) / (np.ptp(f) + 1e-6)
        tarn, verd = smooth(((4, 0.6), (8, 0.4))), smooth(((3, 0.5), (6, 0.3), (12, 0.2)))
        px[:] = hexrgb(0xc08040) * (1.05 - 0.4 * tarn[:, :, None]) * (0.9 + 0.2 * r.random((h, w)))[:, :, None]
        px[verd > 0.72] = hexrgb(0x4a9a78) * 0.95; px[verd > 0.84] = hexrgb(0x6ac0a0)
    bronze = mat('hc_bronze', 0xffffff, rough=0.38, metal=0.9, tex=tex_canvas('hc_bronze_t', 32, 32, patina))
    polish = mat('hc_polish', 0xe0a050, rough=0.18, metal=1.0)
    iron = mat('hc_iron', 0x2a2a2e, rough=0.55, metal=0.6, tex=tex_noise('hc_iron_t', 0x2c2c30, var=0.15, size=16, speck=0x6a3a1a, speck_p=0.08, seed=202))
    oak = mat('hc_oak', 0x6a4220, rough=0.45, clearcoat=0.3, tex=tex_walnut('hc_oak_t', 0x74461e, 0x3a2008, seed=203))
    inside = mat('hc_bore', 0x120c08, rough=0.8)
    ballm = mat('hc_ball', 0x6b7bff, rough=0.08, clearcoat=1.0, tex=tex_canvas('hc_ball_t', 64, 64, swirl))
    hole = mat('hc_hole', 0x05050a, rough=0.6)
    pin_w = mat('hc_pin', 0xf8f8f8, rough=0.2, clearcoat=1.0)
    pin_r = mat('hc_pin_r', 0xe0202a, rough=0.2, clearcoat=1.0)
    match = mat('hc_match', 0x8a6a3a, rough=0.9, tex=tex_stripes('hc_match_t', 0x9a7a44, 0x6a4a24, size=8, width=2))
    ember = mat('hc_ember', 0xff5a10, rough=0.6, emit=0xff6a10, strength=6.0)
    spark = mat('hc_spark', 0xffe14d, rough=0.6, emit=0xffd040, strength=8.0)
    parts = []
    A = parts.append

    # ---------------- the barrel, one lathe from the muzzle lip back to the cascabel neck (r, z)
    prof = [(BORE, MUZ), (0.172, MUZ), (0.178, MUZ + 0.006), (0.178, MUZ + 0.016), (0.172, MUZ + 0.02), (0.184, MUZ + 0.03), (0.186, MUZ + 0.042), (0.181, MUZ + 0.052),
            (0.17, MUZ + 0.058), (0.154, MUZ + 0.084), (0.145, MUZ + 0.12), (0.148, -0.33), (0.156, -0.326), (0.161, -0.316), (0.156, -0.306), (0.152, -0.302),
            (0.156, -0.29), (0.161, -0.13), (0.17, -0.126), (0.174, -0.118), (0.17, -0.11), (0.168, -0.106), (0.172, 0.02), (0.178, 0.024), (0.184, 0.034),
            (0.184, 0.05), (0.174, 0.056), (0.16, 0.072), (0.13, 0.1), (0.09, 0.122), (0.05, 0.136), (0.036, 0.142)]
    A(lathe(prof, (0, 0, 0), bronze, seg=32, cap=False))
    A(lathe([(BORE - 0.0005, MUZ + 0.001), (BORE - 0.0005, -0.25), (0.0, -0.25)], (0, 0, 0), inside, seg=28, cap=False))
    A(lathe([(0.036, 0.14), (0.045, 0.146), (0.062, 0.166), (0.066, 0.184), (0.058, 0.2), (0.036, 0.21), (0.0, 0.212)], (0, 0, 0), polish, seg=20))  # cascabel button
    for z0, z1, r in ((MUZ + 0.028, MUZ + 0.046, 0.1875), (-0.322, -0.31, 0.1625), (-0.122, -0.112, 0.1755), (0.026, 0.048, 0.1855)):  # the polished bands
        A(lathe([(r, z0), (r, z1)], (0, 0, 0), polish, seg=32, cap=False))
    # trunnions + rimbases, at the balance point
    for sx in (-1, 1):
        A(lathe([(0.05, sx * 0.14), (0.05, sx * 0.172), (0.036, sx * 0.176), (0.036, sx * 0.226), (0.032, sx * 0.23)], (0, -0.02, -0.2), bronze, seg=16, axis='x'))
    # the dolphins (lifting handles): two bowling pins cast on top, lying along the barrel
    for sx in (-1, 1):
        pp = [(0.0, 0.0), (0.015, 0.001), (0.0225, 0.025), (0.0175, 0.056), (0.01, 0.072), (0.0131, 0.093), (0.0106, 0.109), (0.0, 0.113)]
        pin = lathe(pp, (0, 0, 0), pin_w, seg=12, axis='y')
        bands = [lathe([(0.0114, y0), (0.0112, y0 + 0.005)], (0, 0, 0), pin_r, seg=12, axis='y', cap=False) for y0 in (0.062, 0.071)]
        pj = join([pin] + bands, f'pin{sx}')
        pj.rotation_euler = Euler((-math.pi / 2 + 0.1, 0, 0), 'XYZ')  # lie it down, head toward the muzzle
        pj.location = gv(sx * 0.056, 0.168, -0.155)
        A(pj)
        A(cyl(0.009, 0.03, (sx * 0.056, 0.157, -0.175), bronze, axis='y', seg=8))  # the cast feet they stand on
        A(cyl(0.009, 0.03, (sx * 0.056, 0.157, -0.085), bronze, axis='y', seg=8))
    # vent field + touch hole + the slow match: a cord out of the vent, the ember on the end, sparks
    A(box((0.05, 0.012, 0.06), (0, 0.164, 0.0), polish, bev=0.004))
    A(cyl(0.006, 0.01, (0, 0.171, 0.0), inside, axis='y', seg=8))
    fz = [(0, 0.17, 0.0), (0.004, 0.19, 0.01), (0.014, 0.214, 0.028), (0.03, 0.232, 0.05), (0.05, 0.24, 0.07)]
    A(sweep(fz, 0.0055, match, seg=6))
    A(ball(0.009, (0.054, 0.241, 0.074), ember, seg=10, rings=6, scale=(1, 0.9, 1.2)))
    rng = random.Random(3)
    for k in range(6):
        d = (rng.uniform(-1, 1), rng.uniform(0.3, 1), rng.uniform(-1, 1))
        l = math.sqrt(sum(v * v for v in d)); d = [v / l for v in d]
        r = rng.uniform(0.016, 0.03)
        A(box((0.005, 0.005, 0.005), (0.054 + d[0] * r, 0.241 + d[1] * r, 0.074 + d[2] * r), spark, rot=(rng.random() * 3, rng.random() * 3, 0)))

    # ---------------- the oak bed the barrel sits in, iron bands, the grip and the tiller butt
    A(side([(-0.37, -0.13), (-0.37, -0.19), (-0.35, -0.215), (0.06, -0.215), (0.12, -0.19), (0.12, -0.13)], 0.124, (0, 0, 0), oak, bev=0.012, seg=2))
    A(side([(0.0, -0.21), (0.08, -0.21), (0.11, -0.31), (0.102, -0.326), (0.074, -0.33), (0.062, -0.318), (0.054, -0.29), (0.058, -0.278), (0.048, -0.264),
            (0.03, -0.24)], 0.054, (0, 0, 0), oak, bev=0.012, seg=2))  # the grip
    A(side([(0.1, -0.14), (0.13, -0.14), (0.33, -0.18), (0.342, -0.196), (0.342, -0.27), (0.33, -0.28), (0.31, -0.272), (0.15, -0.215), (0.1, -0.205)], 0.064, (0, 0, 0), oak, bev=0.012, seg=2))  # tiller butt
    A(side([(0.336, -0.176), (0.354, -0.18), (0.356, -0.276), (0.34, -0.284)], 0.068, (0, 0, 0), iron, bev=0.005))  # iron butt cap
    for z in (-0.3, 0.0):  # bands over the barrel, down the bed's sides and under it
        r0 = 0.157 if z < -0.2 else 0.168
        A(lathe([(r0, z - 0.016), (r0 + 0.004, z - 0.012), (r0 + 0.004, z + 0.012), (r0, z + 0.016)], (0, 0, 0), iron, seg=32, cap=False))
        for sx in (-1, 1):
            A(box((0.008, 0.09, 0.026), (sx * 0.066, -0.17, z), iron, bev=0.002))
            A(cyl(0.007, 0.005, (sx * 0.071, -0.19, z), iron, axis='x', seg=8))  # bolt heads
        A(box((0.14, 0.008, 0.026), (0, -0.219, z), iron, bev=0.002))

    # ---------------- the ball: swirly, three finger holes facing up at you, sitting in the muzzle
    bc = (0, 0.004, -0.497)
    ball_o = ball(0.118, bc, ballm, seg=28, rings=18)
    for dvec, r in (((-0.25, 0.85, 0.45), 0.011), ((0.25, 0.85, 0.45), 0.011), ((0.0, 0.62, 0.78), 0.013)):
        l = math.sqrt(sum(v * v for v in dvec)); dvec = [v / l for v in dvec]
        cut(ball_o, rod(tuple(bc[i] + dvec[i] * 0.14 for i in range(3)), tuple(bc[i] + dvec[i] * 0.08 for i in range(3)), r, None, seg=12))
    A(fixmats(ball_o))

    for p in parts: fixmats(p); uv_box(p, 0.08)
    WZ = {'hc_oak': 'a', 'hc_iron': 'a', 'hc_bronze': 'b', 'hc_polish': 'b', 'hc_ball': 'b'}  # wrap zones (wrapzones.js): a = handle side, b = business end, everything else keeps its look
    bodies = zone_join(parts, 'cannon_body', WZ, default='n', rule=None)
    meta = {'kind': 'weapon', 'id': 'bowling', 'skin': 'bowling_cannon', 'paint': ['hc_bronze'], 'muzzle': [0, 0, MUZ], 'hatAt': [[0, 0.17, -0.05], 0.15],
            'ads': [0.2, -0.24, -0.42]}  # no sights: aiming tucks the big barrel down and right so the middle of the screen stays clear
    return finish('w_bowling_cannon', bodies, meta)


main(build, 'w_bowling_cannon')
