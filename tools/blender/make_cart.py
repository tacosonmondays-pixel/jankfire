# Shopping Cart Cannon + the shopping cart it fires.
# p_cart: a real supermarket cart, real metres: ~95 cm long, 60 wide, 1 m to the handle. Tapered chrome wire basket
#   (it nests), hinged back gate, folding child-seat flap, red plastic handle with an ad panel, a chassis of two chrome
#   rails, a wire bottom tray, four 125 mm swivel castors (nodes wheel_*, the game spins them), plastic corner bumpers.
#   Feet at y 0, centred, the nose (front of the basket) at -z.
# w_cart: a 6in PVC air cannon, painted, with a cart's wire basket cut off and wrapped round the barrel as a heat
#   shield, a cart's red handle as the foregrip, the coin lock on its chain, a swivel castor as a monopod, a red air
#   tank with a gauge, a sprinkler valve and a doorbell trigger. Muzzle and grip on the code model's spots.
# run: blender -b --python tools/blender/make_cart.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

lerp = lambda a, b, t: a + (b - a) * t


_MATS = {}
def materials():
    if _MATS: return _MATS
    M = _MATS
    M['chrome'] = mat('ct_chrome', 0xd8dde4, rough=0.12, metal=1.0)
    M['wire'] = mat('ct_wire', 0xc8ced6, rough=0.18, metal=1.0, tex=tex_noise('ct_wire_t', 0xc8ced6, var=0.12, size=16, speck=0x8a7a5a, speck_p=0.05, seed=601))
    M['red'] = mat('ct_handle', 0xe0202a, rough=0.25, clearcoat=0.8)
    M['paint'] = mat('ct_paint', 0x9b5cff, rough=0.18, clearcoat=1.0)  # the store colour (the gun's colour)
    M['rubber'] = mat('ct_tyre', 0x2a2a2e, rough=0.8, tex=tex_noise('ct_tyre_t', 0x2a2a2e, var=0.15, size=16, seed=602))
    M['hub'] = mat('ct_hub', 0x8a9098, rough=0.4, metal=0.5)
    M['black'] = mat('ct_black', 0x18181c, rough=0.45)
    M['yellow'] = mat('ct_lock', 0xffe14d, rough=0.25, clearcoat=0.7)
    return M


def cart_parts(M, wheels_out):
    P = []; A = P.append
    rw, rr = 0.0042, 0.008  # grid wire, rim radius
    def sz(s, t): return lerp(lerp(0.355, 0.395, t), lerp(-0.355, -0.455, t), s)  # s: 0 back .. 1 front, t: 0 bottom .. 1 top
    def hx(s, t): return lerp(lerp(0.235, 0.285, t), lerp(0.195, 0.24, t), s)
    def yy(t): return lerp(0.46, 0.92, t)
    def pt(s, t, side): return (side * hx(s, t), yy(t), sz(s, t))
    W = lambda a, b, r=rw: A(rod(a, b, r, M['wire'], seg=5))
    # rims (top + bottom) and the corner posts
    for t, r in ((1.0, rr), (0.0, 0.006)):
        for sd in (-1, 1): W(pt(0, t, sd), pt(1, t, sd), r)
        W(pt(1, t, -1), pt(1, t, 1), r)
        W(pt(0, t, -1), pt(0, t, 1), r)
    for s in (0, 1):
        for sd in (-1, 1): W(pt(s, 0, sd), pt(s, 1, sd), 0.006)
    # side walls: verticals + horizontals
    for i in range(1, 16):
        for sd in (-1, 1): W(pt(i / 16, 0, sd), pt(i / 16, 1, sd))
    for t in (0.2, 0.4, 0.6, 0.8):
        for sd in (-1, 1): W(pt(0, t, sd), pt(1, t, sd))
        W(pt(1, t, -1), pt(1, t, 1))
    # front wall verticals
    for i in range(1, 9):
        u = -1 + i / 4.5
        a = (u * hx(1, 0), yy(0), sz(1, 0)); b = (u * hx(1, 1), yy(1), sz(1, 1))
        if abs(u) < 1: W(a, b)
    # bottom grid
    for i in range(1, 8):
        u = -1 + i / 4
        W((u * hx(0, 0), yy(0), sz(0, 0)), (u * hx(1, 0), yy(0), sz(1, 0)))
    for i in range(1, 10): s = i / 10; W(pt(s, 0, -1), pt(s, 0, 1))
    # back gate: hangs from the top rim, swings in so carts nest
    gz = sz(0, 1) - 0.01
    for i in range(0, 11):
        u = -1 + i / 5
        W((u * hx(0, 1) * 0.96, yy(1) - 0.01, gz), (u * hx(0, 0) * 0.96, yy(0) + 0.03, gz - 0.035))
    for t in (0.33, 0.66): W((-hx(0, t) * 0.96, yy(t), gz - 0.035 * (1 - t)), (hx(0, t) * 0.96, yy(t), gz - 0.035 * (1 - t)))
    A(cyl(0.007, hx(0, 1) * 2 + 0.02, (0, yy(1) - 0.005, gz), M['chrome'], axis='x', seg=8))  # gate hinge bar
    # child seat flap folded up against the gate: purple plastic with two leg holes
    seat = box((0.42, 0.2, 0.012), (0, 0.8, gz - 0.035), M['paint'], bev=0.004, rot=(-0.12, 0, 0))
    for sx in (-1, 1): cut(seat, cyl(0.045, 0.06, (sx * 0.1, 0.77, gz - 0.035), None, axis='z', seg=16, rot=(-0.12, 0, 0)))
    A(seat)
    # handle: frame tubes up from the basket back + the red plastic bar + the ad panel
    hzz = sz(0, 1) + 0.1
    for sd in (-1, 1): A(rod((sd * hx(0, 1), yy(1), sz(0, 1)), (sd * (hx(0, 1) - 0.015), 1.0, hzz), 0.011, M['chrome'], seg=8))
    A(cyl(0.022, hx(0, 1) * 2 + 0.05, (0, 1.0, hzz), M['red'], axis='x', seg=12, bev=0.003))
    for sd in (-1, 1): A(cyl(0.025, 0.03, (sd * (hx(0, 1) + 0.02), 1.0, hzz), M['red'], axis='x', seg=12, bev=0.003))
    def ad(px):
        px[:] = hexrgb(0xffe14d); px[:2] = px[-2:] = hexrgb(0xe0202a)
        text_px(px, 'CLEAN UP', 5, 3, 1, 0xe0202a); text_px(px, 'AISLE 5', 8, 12, 1, 0x18181c)
    adm = mat('ct_ad', 0xffffff, rough=0.3, clearcoat=0.5, tex=tex_canvas('ct_ad_t', 56, 21, ad))
    adp = box((0.2, 0.075, 0.006), (0, 1.0 - 0.06, hzz - 0.02), adm, rot=(-0.35, 0, 0)); A(adp)
    apply_mods(adp); uv_planar(adp, (0, 0.94, hzz - 0.02), (0.2, 0.075 * 0.94), 'z')
    # the coin lock on the handle + its chain hanging down
    A(box((0.06, 0.05, 0.045), (0.16, 1.0 - 0.005, hzz + 0.03), M['yellow'], bev=0.004))
    for k in range(6): A(lathe([(0.006, -0.004), (0.006, 0.004)], (0.16, 0.96 - k * 0.018, hzz + 0.03), M['chrome'], seg=8, axis='y', rot=(0, k * 1.57, 0)))
    # chassis: two rails, rear legs up to the basket, front struts, the wire tray
    for sd in (-1, 1):
        A(rod((sd * 0.225, 0.125, 0.34), (sd * 0.19, 0.125, -0.36), 0.012, M['chrome'], seg=8))
        A(rod((sd * 0.225, 0.125, 0.34), (sd * hx(0, 0), yy(0), sz(0, 0)), 0.012, M['chrome'], seg=8))
        A(rod((sd * 0.19, 0.125, -0.36), (sd * hx(1, 0), yy(0), sz(1, 0) + 0.04), 0.009, M['chrome'], seg=8))
    A(rod((-0.225, 0.125, 0.34), (0.225, 0.125, 0.34), 0.011, M['chrome'], seg=8))
    A(rod((-0.19, 0.125, -0.36), (0.19, 0.125, -0.36), 0.011, M['chrome'], seg=8))
    for i in range(7):
        x = -0.18 + i * 0.06
        W((x, 0.2, 0.26), (x * 0.93, 0.2, -0.3))
    for z in (0.26, 0.05, -0.15, -0.3): W((-0.2, 0.2, z), (0.2, 0.2, z), 0.005)
    for sd in (-1, 1):
        for z in (0.26, -0.3): A(rod((sd * 0.2, 0.2, z), (sd * 0.2, 0.125, z), 0.006, M['wire'], seg=5))
    # castors: plate, swivel, fork, tyre + hub (each wheel its own node, pivot on its axle)
    for name, x, z in (('wheel_rl', -0.225, 0.34), ('wheel_rr', 0.225, 0.34), ('wheel_fl', -0.19, -0.36), ('wheel_fr', 0.19, -0.36)):
        A(box((0.06, 0.008, 0.07), (x, 0.112, z), M['chrome'], bev=0.002))
        A(cyl(0.016, 0.016, (x, 0.1, z), M['chrome'], axis='y', seg=10))
        for sx in (-1, 1): A(box((0.004, 0.06, 0.03), (x + sx * 0.022, 0.07, z + 0.012), M['chrome'], bev=0.001))
        tyre = lathe([(0.03, -0.014), (0.056, -0.015), (0.0625, -0.01), (0.0625, 0.01), (0.056, 0.015), (0.03, 0.014)], (x, 0.0625, z + 0.012), M['rubber'], seg=18, axis='x')
        hub = cyl(0.03, 0.03, (x, 0.0625, z + 0.012), M['hub'], axis='x', seg=12)
        axle = cyl(0.005, 0.05, (x, 0.0625, z + 0.012), M['chrome'], axis='x', seg=6)
        wheels_out.append(part([tyre, hub, axle], name, pivot=(x, 0.0625, z + 0.012)))
    # plastic corner bumpers on the front top corners + a front bumper strip
    for sd in (-1, 1): A(box((0.05, 0.06, 0.05), (sd * hx(1, 1), yy(1) - 0.02, sz(1, 1) + 0.005), M['paint'], bev=0.01))
    A(box((hx(1, 1) * 2 - 0.04, 0.035, 0.02), (0, yy(1) - 0.01, sz(1, 1) - 0.005), M['paint'], bev=0.006))
    return P


def build_cart():
    M = materials()
    wheels = []
    P = cart_parts(M, wheels)
    for p in P: uv_box(p, 0.08)
    body = join(P, 'cart')
    return finish('p_cart', [body] + wheels, {'kind': 'prop', 'id': 'cart', 'paint': ['ct_paint']})


# ---------------------------------------------------------------- the cannon
S = 1.0 / 1000
BORE_Y, MUZ_Z = 0.02, -0.71
def Z(u): return MUZ_Z + u * S
def Y(h): return BORE_Y + h * S
def Wd(mm): return mm * S


def build_cannon():
    M = materials()
    pvc = mat('cc_pvc', 0x6a34d8, rough=0.25, clearcoat=0.8, tex=tex_noise('cc_pvc_t', 0x6a34d8, var=0.06, size=32, speck=0x4a1ab0, speck_p=0.03, seed=611))
    inner = mat('cc_inner', 0x1c1c22, rough=0.8)
    tank = mat('cc_tank', 0xe0202a, rough=0.2, clearcoat=0.9)
    valve = mat('cc_valve', 0x2a8a3a, rough=0.35)
    brass = mat('cc_brass', 0xe0ad3c, rough=0.22, metal=1.0)
    grip = mat('cc_grip', 0x22222a, rough=0.6, tex=tex_noise('cc_grip_t', 0x22222a, var=0.15, size=16, seed=612))
    def gauge(px):
        h, w = px.shape[:2]; c = w / 2
        px_disc(px, c, c, c - 0.5, 0xf4f4f0)
        px_disc(px, c, c, c - 4, 0xe8281e, r_in=c - 9, a0=1.0, a1=2.3)
        for i in range(9):
            th = -2.3 + 4.6 * i / 8
            px_line(px, c + math.sin(th) * (c - 3), c - math.cos(th) * (c - 3), c + math.sin(th) * (c - 10), c - math.cos(th) * (c - 10), 0x111111, 1.3)
        px_line(px, c, c, c + math.sin(2.1) * (c - 7), c - math.cos(2.1) * (c - 7), 0xe0102a, 2.2)
        px_disc(px, c, c, 3, 0x111111)
    gface = mat('cc_gauge', 0xffffff, rough=0.2, tex=tex_canvas('cc_gauge_t', 40, 40, gauge))
    def sign(px):
        px[:] = hexrgb(0x1f5aff); px[1:-1, 1:-1] = hexrgb(0x2a6aff)
        text_px(px, 'PLEASE', 4, 3, 1, 0xffffff); text_px(px, 'RETURN', 4, 11, 1, 0xffffff); text_px(px, 'CARTS HERE', 4, 19, 1, 0xffe14d)
    signm = mat('cc_sign', 0xffffff, rough=0.3, tex=tex_canvas('cc_sign_t', 66, 29, sign))
    def coin(px):
        px[:] = hexrgb(0xffe14d); text_px(px, '25C', 3, 2, 1, 0x18181c)
    coinm = mat('cc_coin', 0xffffff, rough=0.3, tex=tex_canvas('cc_coin_t', 22, 10, coin))
    P, decals = [], []; A = P.append
    R = 84  # 6in schedule 40: 168 mm outside
    # ---------------- barrel: flared mouth with a chrome lip, the long tube, couplings, the domed back cap
    A(lathe([(Wd(R - 8), Z(70)), (Wd(R - 8), Z(4)), (Wd(122), Z(-2)), (Wd(130), Z(0)), (Wd(128), Z(8)), (Wd(110), Z(22)), (Wd(R + 4), Z(70)), (Wd(R + 4), Z(84))], (0, BORE_Y, 0), pvc, seg=32))
    A(lathe([(Wd(126), Z(-4)), (Wd(133), Z(-2)), (Wd(133), Z(4)), (Wd(126), Z(6))], (0, BORE_Y, 0), M['chrome'], seg=32))
    A(lathe([(Wd(R - 9), Z(2)), (Wd(R - 9), Z(400))], (0, BORE_Y, 0), inner, seg=32))
    A(lathe([(Wd(R), Z(80)), (Wd(R), Z(740))], (0, BORE_Y, 0), pvc, seg=32))
    for u in (300, 560): A(lathe([(Wd(R), Z(u - 22)), (Wd(R + 7), Z(u - 20)), (Wd(R + 7), Z(u + 20)), (Wd(R), Z(u + 22))], (0, BORE_Y, 0), pvc, seg=32))
    A(lathe([(Wd(R), Z(736)), (Wd(R + 7), Z(738)), (Wd(R + 7), Z(770)), (Wd(R - 10), Z(790)), (Wd(40), Z(806)), (0, Z(810))], (0, BORE_Y, 0), pvc, seg=32))
    # ---------------- the cart basket sleeve: chrome wires along the barrel, hoops round it
    for i in range(14):
        a = 2 * math.pi * i / 14
        x, y = math.cos(a) * Wd(R + 14), math.sin(a) * Wd(R + 14)
        if y < -Wd(40): continue  # open at the bottom where the handle and the castor go
        A(rod((x, BORE_Y + y, Z(110)), (x, BORE_Y + y, Z(470)), Wd(3.2), M['wire'], seg=5))
    for u in range(110, 471, 45):
        ring = [(math.cos(a) * Wd(R + 14), BORE_Y + math.sin(a) * Wd(R + 14), Z(u)) for a in [math.radians(d) for d in range(-28, 209, 12)]]
        A(sweep(ring, [Wd(3.6)] * len(ring), M['wire'], seg=5))
    for u in (110, 470):  # the cut ends, crimped onto the tube with plastic bumpers
        for sx in (-1, 1): A(box((Wd(26), Wd(30), Wd(26)), (sx * Wd(R + 10), Y(-30), Z(u)), M['paint'], bev=0.005))
    # ---------------- the cart handle as the foregrip (red bar on two chrome posts), with its little ad board
    for sx in (-1, 1): A(rod((sx * Wd(60), Y(-R + 6), Z(330)), (sx * Wd(64), Y(-R - 70), Z(345)), Wd(8), M['chrome'], seg=8))
    A(cyl(Wd(17), Wd(160), (0, Y(-R - 74), Z(346)), M['red'], axis='x', seg=12, bev=0.003))
    for sx in (-1, 1): A(cyl(Wd(20), Wd(18), (sx * Wd(86), Y(-R - 74), Z(346)), M['red'], axis='x', seg=12, bev=0.003))
    # ---------------- swivel castor under the muzzle (a monopod you can roll it on)
    A(box((Wd(60), Wd(8), Wd(60)), (0, Y(-R - 2), Z(150)), M['chrome'], bev=0.002))
    A(cyl(Wd(15), Wd(16), (0, Y(-R - 14), Z(150)), M['chrome'], axis='y', seg=10))
    for sx in (-1, 1): A(box((Wd(4), Wd(60), Wd(30)), (sx * Wd(22), Y(-R - 46), Z(160)), M['chrome'], bev=0.001))
    A(lathe([(Wd(30), -Wd(14)), (Wd(56), -Wd(15)), (Wd(62), -Wd(10)), (Wd(62), Wd(10)), (Wd(56), Wd(15)), (Wd(30), Wd(14))], (0, Y(-R - 70), Z(160)), M['rubber'], seg=18, axis='x'))
    A(cyl(Wd(30), Wd(30), (0, Y(-R - 70), Z(160)), M['hub'], axis='x', seg=12))
    # ---------------- coin lock + chain on the left, sign on the right
    A(box((Wd(36), Wd(60), Wd(90)), (Wd(-R - 18), Y(10), Z(600)), M['yellow'], bev=0.005))
    cn = box((0.0008, Wd(16), Wd(36)), (Wd(-R - 36.5), Y(26), Z(600)), coinm, rot=(0, math.pi, 0)); A(cn); decals.append((cn, (Wd(36), Wd(16)), '-x'))
    A(box((Wd(6), Wd(18), Wd(4)), (Wd(-R - 37), Y(0), Z(600)), M['black']))  # the coin slot
    chain = bend_path((Wd(-R - 30), Y(-20), Z(630)), (Wd(-R - 12), Y(-60), Z(470)), 0.07, n=9)
    for k, c in enumerate(chain): A(lathe([(Wd(6), -Wd(4)), (Wd(6), Wd(4))], c, M['chrome'], seg=8, axis='y' if k % 2 else 'z'))
    A(box((Wd(14), Wd(24), Wd(30)), (Wd(-R - 12), Y(-70), Z(470)), M['red'], bev=0.003))  # the key tag at the end of the chain
    sg = box((0.0008, Wd(64), Wd(130)), (Wd(R + 8), Y(10), Z(640)), signm); A(sg); decals.append((sg, (Wd(130), Wd(64)), 'x'))
    A(box((Wd(4), Wd(70), Wd(136)), (Wd(R + 5), Y(10), Z(640)), M['chrome'], bev=0.001))
    # ---------------- air: red tank under the back, gauge, sprinkler valve, pistol grip + doorbell trigger
    ty = Y(-R - 60)
    A(lathe([(0, Z(470)), (Wd(40), Z(474)), (Wd(56), Z(500)), (Wd(58), Z(520)), (Wd(58), Z(700)), (Wd(52), Z(720)), (Wd(20), Z(734)), (0, Z(735))], (0, ty, 0), tank, seg=24))
    for u in (530, 690):
        A(lathe([(Wd(59), Z(u - 10)), (Wd(59), Z(u + 10))], (0, ty, 0), M['black'], seg=24))
        for sx in (-1, 1): A(box((Wd(4), Wd(70), Wd(20)), (sx * Wd(56), Y(-R - 22), Z(u)), M['black'], rot=(0, 0, sx * 0.25)))
    gb = cyl(Wd(30), Wd(18), (0, 0, 0), brass, axis='z', seg=22, bev=0.002)
    gf = cyl(Wd(26), Wd(2), (0, 0, Wd(10)), gface, axis='z', seg=22)
    apply_mods(gf); uv_planar(gf, (0, 0, Wd(10)), Wd(52), 'z')
    gg = join([gb, gf], 'gauge'); gg.location = gv(Wd(48), ty + Wd(30), Z(740)); gg.rotation_euler = Euler((-0.3, 0, 0.6), 'XYZ'); A(gg)
    A(rod((0, ty + Wd(20), Z(735)), (Wd(40), ty + Wd(28), Z(742)), Wd(5), brass, seg=8))
    A(box((Wd(60), Wd(50), Wd(60)), (0, Y(-R - 10), Z(770)), valve, bev=0.008))  # sprinkler valve
    A(cyl(Wd(16), Wd(30), (0, Y(-R + 22), Z(770)), M['black'], axis='y', seg=14, bev=0.003))
    A(side([(Z(790), Y(-R - 30)), (Z(860), Y(-R - 30)), (Z(890), Y(-R - 180)), (Z(884), Y(-R - 196)), (Z(846), Y(-R - 198)), (Z(836), Y(-R - 184)), (Z(822), Y(-R - 120)), (Z(800), Y(-R - 70))], Wd(38), (0, 0, 0), grip, bev=0.006, seg=3))
    A(cyl(Wd(13), Wd(12), (0, Y(-R - 62), Z(796)), M['red'], axis='z', seg=14, bev=0.003, rot=(0.25, 0, 0)))  # doorbell trigger
    A(cyl(Wd(18), Wd(8), (0, Y(-R - 62), Z(802)), M['black'], axis='z', seg=14, rot=(0.25, 0, 0)))
    for p in P: uv_box(p, 0.08)
    for o, sz, ax in decals:
        apply_mods(o); c = o.matrix_world.translation; uv_planar(o, (c.x, c.z, -c.y), sz, ax)
    WZ = {'cc_pvc': 'b', 'ct_wire': 'b', 'ct_chrome': 'b', 'cc_tank': 'a', 'cc_grip': 'a', 'ct_handle': 'a', 'cc_valve': 'a', 'ct_black': 'a'}
    bodies = zone_join(P, 'cart_body', WZ, default='n')
    meta = {'kind': 'weapon', 'id': 'cart', 'paint': ['cc_pvc'], 'muzzle': [0, BORE_Y, MUZ_Z], 'hatAt': [[0, Y(R + 18), Z(560)], 0.14],
            'ads': [0.22, -0.27, -0.44]}  # no sights: aiming tucks the big tube down and right
    return finish('w_cart', bodies, meta)


def build():
    return [(build_cart(), 'p_cart'), (build_cannon(), 'w_cart')]


main_multi(build)
