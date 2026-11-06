# The things round-1 guns and the items throw, at the code's sizes (centred, nose to -z):
#   pj_chicken: the Chicken Rocket's rubber chicken (same yellow as the one in the launcher), neck out, beak open, googly
#     eyes, legs trailing, with a firework rocket strapped to its back (the exhaust glows).
#   pj_bowling: the giant bowling ball (0.9 m): a reactive-resin swirl, three drilled holes.
#   pj_banana: the Peel Shooter's banana: five-sided, speckled, the stem and the black tip, its 4011 sticker.
#   pj_peel: the peel a miss leaves on the floor (0.7 m across, feet on the floor): four flaps flopped open, the stem up.
#   pj_frag: a pineapple frag (Mk 2 pattern: cast segments, fuse, spoon, ring + pin) with a PULL ME tag on the ring.
#   pj_smokegren: a canister smoke grenade (M18 pattern): emission holes, fuse, spoon, ring, SMOKE / DO NOT INHALE.
# run: blender -b --python tools/blender/make_projectiles.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj


def chicken():
    yel = mat('pc_chicken', 0xffe14d, rough=0.28, clearcoat=0.6)
    beak = mat('pc_beak', 0xff8a1a, rough=0.35, clearcoat=0.4)
    comb = mat('pc_comb', 0xe8202a, rough=0.35, clearcoat=0.5)
    mouth = mat('pc_mouth', 0x5a0a14, rough=0.6)
    white = mat('pc_white', 0xffffff, rough=0.2, clearcoat=0.8)
    black = mat('pc_black', 0x0a0a0a, rough=0.3)
    rk = mat('pc_rocket', 0xffffff, rough=0.35, clearcoat=0.5, tex=tex_stripes('pc_rocket_t', 0xe8202a, 0xf6f2e6, size=16, width=4, diag=True))
    cone = mat('pc_cone', 0xffd23b, rough=0.35, clearcoat=0.5)
    flame = mat('pc_flame', 0xff7a1a, rough=0.8, emit=0xff8a1a, strength=4.0)
    strap = mat('pc_strap', 0x2a2a30, rough=0.6)
    P = []; A = P.append
    A(ball(0.165, (0, 0, 0.03), yel, scale=(1.0, 0.9, 1.45), seg=24, rings=14))
    A(sweep([(0, 0.06, -0.17), (0, 0.11, -0.24), (0, 0.16, -0.3), (0, 0.19, -0.34)], [0.07, 0.058, 0.05, 0.046], yel, seg=14))
    A(ball(0.08, (0, 0.205, -0.375), yel, scale=(0.85, 0.95, 1.15), seg=18, rings=12))
    A(cyl(0.032, 0.09, (0, 0.215, -0.47), beak, axis='z', r2=0.005, seg=10, rot=(0.2, 0, 0)))
    A(cyl(0.025, 0.07, (0, 0.175, -0.455), beak, axis='z', r2=0.005, seg=10, rot=(-0.45, 0, 0)))
    A(ball(0.026, (0, 0.195, -0.44), mouth, seg=10, rings=6))
    for d, h, r in ((-0.33, 0.28, 0.028), (-0.365, 0.292, 0.033), (-0.4, 0.278, 0.026)): A(ball(r, (0, h, d), comb, scale=(0.5, 1, 1), seg=12, rings=8))
    A(ball(0.026, (0, 0.13, -0.45), comb, scale=(0.55, 1.4, 0.8), seg=12, rings=8))
    for sx in (-1, 1):
        A(ball(0.028, (sx * 0.052, 0.235, -0.39), white, scale=(0.55, 1, 1), seg=14, rings=8))
        A(ball(0.012, (sx * 0.066, 0.226, -0.398), black, scale=(0.6, 1, 1), seg=8, rings=6))
        A(ball(0.075, (sx * 0.15, 0.02, 0.08), yel, scale=(0.35, 0.6, 1.6), seg=14, rings=8, rot=(0.1, sx * 0.25, sx * 0.3)))  # wings swept back
        leg = [(sx * 0.06, -0.11, 0.12), (sx * 0.065, -0.15, 0.2), (sx * 0.07, -0.17, 0.27)]
        A(sweep(leg, [0.016, 0.013, 0.011], beak, seg=8))
        for k in (-1, 0, 1): A(box((0.008, 0.006, 0.05), (sx * 0.07 + k * 0.015, -0.172, 0.295), beak, rot=(0, k * 0.4, 0), bev=0.002))
    # the firework rocket strapped on its back
    A(cyl(0.042, 0.24, (0, 0.165, 0.06), rk, axis='z', seg=16, bev=0.004))
    A(cyl(0.042, 0.07, (0, 0.165, -0.095), cone, axis='z', r2=0.002, seg=16))
    A(cyl(0.03, 0.04, (0, 0.165, 0.2), strap, axis='z', r2=0.038, seg=14))
    A(cyl(0.026, 0.07, (0, 0.165, 0.25), flame, axis='z', r2=0.002, seg=12, rot=(math.pi, 0, 0)))
    for k in range(3):
        a = 2 * math.pi * k / 3
        A(box((0.004, 0.05, 0.06), (math.cos(a) * 0.05, 0.165 + math.sin(a) * 0.05, 0.155), cone, rot=(0, 0, a - math.pi / 2), bev=0.002))
    for z in (-0.01, 0.12): A(box((0.2, 0.012, 0.03), (0, 0.13, z), strap, bev=0.004))
    for p in P: uv_box(p, 0.04)
    WZ = {'pc_chicken': 'b', 'pc_rocket': 'a', 'pc_cone': 'a', 'pc_strap': 'a'}
    meta = {'kind': 'proj', 'id': 'chicken', 'hatAt': [[0, 0.29, -0.36], 0.15]}
    return finish('pj_chicken', zone_join(P, 'pchicken', WZ, default='n'), meta)


def bowling():
    R = 0.45
    def swirl(px):
        h, w = px.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
        k = np.sin(2 * math.pi * (xx * 2 + 0.6 * np.sin(2 * math.pi * yy * 1.5 + 3 * xx))) + 0.6 * np.sin(2 * math.pi * (yy * 3 + xx))
        q = np.clip((k + 1.6) / 3.2, 0, 0.999)
        cols = np.stack([hexrgb(c) for c in (0x1a1a7a, 0x2a3aa8, 0x6a2ab8, 0xff4fd8, 0x4fd8ff)])
        px[:] = cols[(q * len(cols)).astype(int)]
    resin = mat('pb_resin', 0xffffff, rough=0.08, clearcoat=1.0, tex=tex_canvas('pb_resin_t', 128, 64, swirl))
    hole = mat('pb_hole', 0x0a0a14, rough=0.6)
    b = ball(R, (0, 0, 0), resin, seg=40, rings=24, name='ball')
    uv_cyl(b, 'y', -R, R)
    holes = [(-0.25 * R, 0.5 * R, 0.042), (0.25 * R, 0.5 * R, 0.042), (0, 0.18 * R, 0.05)]
    for x, y, r in holes:
        c = cyl(r, 0.25, (x, y, -R), hole, axis='z', seg=18, name='hole')
        cut(b, c)
    b.data.materials.append(hole)
    for f in b.data.polygons:  # the inside of the holes: dark
        cx, cy, cz = f.center.x, f.center.z, -f.center.y
        if math.sqrt(cx * cx + cy * cy + cz * cz) < R * 0.985: f.material_index = 1
    smooth(b, 40)
    meta = {'kind': 'proj', 'id': 'bowling', 'hatAt': [[0, R, 0], 0.3]}
    return finish('pj_bowling', zone_join([b], 'pbowling', {'pb_resin': 'ab'}), meta)


def banana():
    peel = mat('pn_peel', 0xffd23a, rough=0.35, clearcoat=0.3, tex=tex_noise('pn_peel_t', 0xffd23a, var=0.08, size=32, speck=0x6a4a18, speck_p=0.06, seed=124))
    brown = mat('pn_brown', 0x2a1808, rough=0.6)
    stem = mat('pn_stem', 0x6a7a2a, rough=0.6)
    def stk(px):
        px[:] = hexrgb(0x2050b0); px[0] = px[-1] = hexrgb(0xffe14d)
        text_px(px, '4011', 2, 3, 1, 0xffffff)
    sticker = mat('pn_sticker', 0xffffff, rough=0.35, tex=tex_canvas('pn_sticker_t', 28, 13, stk))
    Rr, n = 0.2, 16
    path, radii = [], []
    for i in range(n + 1):
        a = math.radians(-60 + 120 * i / n)
        path.append((0, Rr * math.cos(a) - Rr * 0.75, Rr * math.sin(a)))
        u = i / n
        radii.append(0.022 + 0.022 * math.sin(min(1, u / 0.3) * math.pi / 2) - (0 if u < 0.7 else 0.03 * ((u - 0.7) / 0.3) ** 1.5))
    P = [sweep(path, radii, peel, seg=5, smooth_angle=30, name='banana')]
    P.append(rod(path[0], (0, path[0][1] - 0.012, path[0][2] + 0.03), 0.009, stem, seg=8))
    P.append(ball(0.008, path[-1], brown, seg=8, rings=6))
    sp = path[6]
    stc = cyl(0.016, 0.002, (sp[0] + 0.041, sp[1], sp[2]), sticker, axis='x', seg=16, name='sticker')
    stc.scale = (1.0, 1.45, 1.0); apply_mods(stc)
    for o in bpy.context.view_layer.objects.selected: o.select_set(False)
    bpy.context.view_layer.objects.active = stc; stc.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for p in P: uv_box(p, 0.03)
    uv_planar(stc, (sp[0] + 0.041, sp[1], sp[2]), (0.046, 0.032), 'x')
    P.append(stc)
    meta = {'kind': 'proj', 'id': 'banana', 'hatAt': [[0, 0.06, 0], 0.12]}
    return finish('pj_banana', zone_join(P, 'pbanana', {'pn_peel': 'b', 'pn_stem': 'b', 'pn_brown': 'b', 'pn_sticker': 'n'}), meta)


def peel():
    outer = mat('pp_outer', 0xffd23a, rough=0.4, clearcoat=0.3, tex=tex_noise('pp_outer_t', 0xffd23a, var=0.08, size=32, speck=0x6a4a18, speck_p=0.08, seed=41))
    inner = mat('pp_inner', 0xffffff, rough=0.7, tex=tex_noise('pp_inner_t', 0xf6ecc8, var=0.06, size=16, speck=0xe0d098, speck_p=0.2, seed=42))
    stem = mat('pp_stem', 0x6a7a2a, rough=0.6)
    brown = mat('pp_brown', 0x3a2410, rough=0.6)
    P = []
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        dx, dz = math.cos(a), math.sin(a)
        L = 0.3 + 0.03 * (k % 2)
        pts, rr = [], []
        for i in range(12):
            t = i / 11
            r = 0.02 + L * t
            y = 0.1 * (1 - t) ** 2 + 0.012 + (0.03 * max(0, t - 0.8) / 0.2) ** 1.0 * (t > 0.8)
            pts.append((dx * r, y, dz * r)); rr.append(0.012 + 0.04 * math.sin(math.pi * min(1, t * 1.08)) ** 0.7)
        f = sweep(pts, rr, outer, seg=10, squash=(0.18, 1.0), name=f'flap{k}', smooth_angle=50)
        f.data.materials.append(inner)
        for pf in f.data.polygons:
            if pf.normal.z > 0.3: pf.material_index = 1  # flopped open: the pale inside faces up
        P.append(f)
    P.append(ball(0.045, (0, 0.1, 0), outer, scale=(1, 0.9, 1), seg=14, rings=8))
    P.append(rod((0, 0.13, 0), (0.01, 0.19, 0.02), 0.012, stem, seg=8))
    P.append(ball(0.011, (0.01, 0.195, 0.02), brown, seg=8, rings=6))
    for p in P: uv_box(p, 0.04)
    meta = {'kind': 'peel', 'id': 'peel'}
    return finish('pj_peel', zone_join(P, 'ppeel', {'pp_outer': 'b', 'pp_stem': 'b', 'pp_brown': 'b'}), meta)


def fuse_top(y0, steel, ring_m, dark, tag_m=None, spoon_r=0.06, side=1.0):
    """a grenade fuse: the threaded neck, the striker housing, the spoon down the side, the pull ring + pin"""
    P = []
    P.append(cyl(0.024, 0.022, (0, y0 + 0.011, 0), steel, axis='y', seg=16, bev=0.002))
    P.append(box((0.034, 0.03, 0.05), (0, y0 + 0.035, 0), steel, bev=0.004))
    sp = [(0, y0 + 0.052, -0.01), (0, y0 + 0.056, 0.03), (0, y0 + 0.03, 0.055), (0, y0 - 0.02, spoon_r), (0, y0 - 0.07, spoon_r - 0.008)]
    P.append(sweep(sp, 0.012, steel, seg=8, squash=(0.25, 1.0), name='spoon'))
    P.append(rod((-0.02, y0 + 0.035, 0.005), (0.02, y0 + 0.035, 0.005), 0.003, dark, seg=8, name='pin'))
    ring = []
    for k in range(17):
        a = 2 * math.pi * k / 16
        ring.append((side * (0.024 + 0.0), y0 + 0.035 + 0.022 * math.sin(a), 0.005 - 0.022 * math.cos(a) - 0.025))
    P.append(sweep([(side * 0.03, p[1], p[2]) for p in ring], 0.0032, ring_m, seg=8, name='ring'))
    if tag_m is not None:
        t = box((0.002, 0.03, 0.05), (side * 0.032, y0 + 0.005, -0.06), tag_m, rot=(0.3, 0, 0), name='tag')
        apply_mods(t); P.append(t)
    return P


def frag():
    od = mat('pf_od', 0xffffff, rough=0.55, tex=tex_noise('pf_od_t', 0x56662a, var=0.12, size=32, speck=0x3a4418, speck_p=0.1, seed=51))
    steel = mat('pf_steel', 0xa8ae9a, rough=0.35, metal=0.8)
    ringm = mat('pf_ring', 0xd8dce2, rough=0.2, metal=1.0)
    dark = mat('pf_dark', 0x3a3a3a, rough=0.4, metal=0.6)
    def tagp(px):
        px[:] = hexrgb(0xff4fd8); px[0] = px[-1] = hexrgb(0x111111)
        text_px(px, 'PULL', 4, 2, 1, 0xffffff); text_px(px, 'ME', 10, 11, 1, 0xffe14d)
    tag = mat('pf_tag', 0xffffff, rough=0.6, tex=tex_canvas('pf_tag_t', 32, 20, tagp))
    # the pineapple: an egg of cast segments (6 rows x 8 columns, deep grooves between)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=30, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co.x, v.co.z, -v.co.y
        th = math.atan2(z, x); ph = math.acos(max(-1, min(1, y)))
        g1 = abs(math.sin(8 * th / 2)); g2 = abs(math.sin(6 * ph))
        d = 1.0 - 0.07 * (1 - min(1, min(g1, g2) / 0.22)) if 0.25 < ph < math.pi - 0.2 else 1.0
        v.co = gv(x * 0.1 * d, y * 0.118 * d, z * 0.1 * d)
    body = _obj('frag', bm, od)
    for p in body.data.polygons: p.use_smooth = True
    uv_box(body, 0.04)
    P = [body, cyl(0.03, 0.02, (0, 0.118, 0), od, axis='y', seg=16)]
    P += fuse_top(0.128, steel, ringm, dark, tag, spoon_r=0.07)
    for p in P[2:]: uv_box(p, 0.03)
    tg = [p for p in P if p.name.startswith('tag')][0]
    uv_planar(tg, centre(tg), (0.05, 0.03), 'x')
    meta = {'kind': 'proj', 'id': 'frag', 'hatAt': [[0, 0.2, 0], 0.08]}
    return finish('pj_frag', zone_join(P, 'pfrag', {'pf_od': 'b', 'pf_steel': 'a', 'pf_ring': 'a', 'pf_dark': 'a', 'pf_tag': 'n'}), meta)


def smoke():
    def can(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(61)
        px[:] = hexrgb(0x6a7064) * (0.92 + 0.1 * r.random((h, w, 1)))
        px[int(h * 0.12):int(h * 0.22)] = hexrgb(0xb07dff)  # the smoke colour band
        text_px(px, 'SMOKE', 6, int(h * 0.36), 2, 0xf2f0e6)
        text_px(px, 'DO NOT INHALE', 3, int(h * 0.72), 1, 0xffe14d)
    canm = mat('ps_can', 0xffffff, rough=0.45, metal=0.3, tex=tex_canvas('ps_can_t', 84, 40, can))
    steel = mat('ps_steel', 0xa8ae9a, rough=0.35, metal=0.8)
    ringm = mat('ps_ring', 0xd8dce2, rough=0.2, metal=1.0)
    dark = mat('ps_dark', 0x222226, rough=0.5)
    body = lathe([(0.066, -0.11), (0.07, -0.105), (0.07, 0.1), (0.066, 0.108), (0.04, 0.112)], (0, 0, 0), canm, seg=28, axis='y', name='can')
    uv_cyl(body, 'y', 0.105, -0.105, turn=0.4)
    me = body.data; uvl = me.uv_layers.active.data
    for poly in me.polygons:  # labels run round the can: u round, v up
        for li in poly.loop_indices: u, v = uvl[li].uv; uvl[li].uv = (v, 1 - u)
    P = [body]
    for k in range(4):  # emission holes in the top
        a = 2 * math.pi * k / 4 + 0.4
        P.append(cyl(0.008, 0.004, (math.cos(a) * 0.045, 0.111, math.sin(a) * 0.045), dark, axis='y', seg=10))
    P += fuse_top(0.112, steel, ringm, dark, None, spoon_r=0.076)
    for p in P[1:]: uv_box(p, 0.03)
    meta = {'kind': 'proj', 'id': 'smokegren', 'hatAt': [[0, 0.18, 0], 0.08]}
    return finish('pj_smokegren', zone_join(P, 'psmoke', {'ps_can': 'b', 'ps_steel': 'a', 'ps_ring': 'a', 'ps_dark': 'n'}), meta)


main_multi(lambda: [(chicken(), 'pj_chicken'), (bowling(), 'pj_bowling'), (banana(), 'pj_banana'), (peel(), 'pj_peel'), (frag(), 'pj_frag'), (smoke(), 'pj_smokegren')], exposure=-0.8)
