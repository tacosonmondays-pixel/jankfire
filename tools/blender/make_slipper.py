# Slipper (+ the thrown homing one) and the Croc skin (+ its thrown one).
# Slipper: a fluffy closed-toe house slipper, real size (UK 6 / EU 39: 27 cm long, 10 cm across the ball): a foot-shaped
# sole (grey-pink rubber tread, foam midsole, plush footbed), a plush toe box with a rolled collar at the opening, a
# pom-pom. Made fun: a woven tag on the side that says MOM. It's thrown at x1.6 (the code's thrown slipper).
# Croc: a foam clog (EU 43: 30 cm x 12 cm, 10 cm toe box) in lime: ventilation holes on top and round the toe, a heel
# strap on two rivets, chunky tread. Made fun: three charms stuck in the holes (a banana, a duck, a skull).
# run: blender -b --python tools/blender/make_slipper.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj

SOLE_HW = [(-0.14, 0.0), (-0.135, 0.02), (-0.125, 0.033), (-0.1, 0.046), (-0.075, 0.052), (-0.045, 0.05), (-0.01, 0.044), (0.025, 0.04),
           (0.065, 0.042), (0.1, 0.041), (0.12, 0.036), (0.132, 0.026), (0.139, 0.012), (0.14, 0.0)]


def interp(tab, z):
    for (z0, a), (z1, b) in zip(tab, tab[1:]):
        if z0 <= z <= z1: return a + (b - a) * (z - z0) / (z1 - z0)
    return tab[0][1] if z < tab[0][0] else tab[-1][1]


def squircle(hw, y0, y1, K=20, p=0.35):
    """(up, side) points of a rounded box section from y0 (bottom) to y1 (top), half width hw"""
    yc, hh = (y0 + y1) / 2, (y1 - y0) / 2
    out = []
    for j in range(K):
        a = 2 * math.pi * j / K; c, s = math.cos(a), math.sin(a)
        out.append((yc + hh * math.copysign(abs(s) ** p, s), hw * math.copysign(abs(c) ** p, c)))
    return out


def arch(stations, hw_of, top_of, base_y, n=14, name='arch', m=None):
    """an open dome over a sole: rows of points from the right edge, over the top, to the left edge (no bottom)"""
    bm = bmesh.new(); rows = []; last = []
    for z in stations:
        hw, top = hw_of(z), top_of(z)
        last = [(hw * math.cos(math.pi * k / (n - 1)), base_y + (top - base_y) * math.sin(math.pi * k / (n - 1)), z) for k in range(n)]
        rows.append([bm.verts.new(gv(*p)) for p in last])
    for a, b in zip(rows, rows[1:]):
        for k in range(n - 1): bm.faces.new((a[k], a[k + 1], b[k + 1], b[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    for p in o.data.polygons: p.use_smooth = True
    return o, last  # the back row (game points): the opening


def fur_px(base, tip, seed):
    def draw(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(seed)
        n = r.random((h, w))
        px[:] = hexrgb(base)[None, None] * (0.86 + 0.18 * n[:, :, None])
        px[n > 0.84] = hexrgb(tip)
        for k in range(h * w // 10):  # little curls of fluff
            x, y = r.integers(0, w), r.integers(0, h); px[y, x] = hexrgb(tip); px[y, (x + 1) % w] = hexrgb(tip) * 0.96
    return draw


def tread_px(base, dark):
    def draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(base)
        for y in range(1, h, 4):
            for x in range(1 + (y // 4 % 2) * 2, w, 4): px[y:y + 2, x:x + 2] = hexrgb(dark)
    return draw


def slipper():
    plush = mat('sl_plush', 0xffffff, rough=0.95, tex=tex_canvas('sl_plush_t', 32, 32, fur_px(0xff9ad5, 0xffd2ec, 3)))
    collar = mat('sl_collar', 0xffffff, rough=0.95, tex=tex_canvas('sl_collar_t', 32, 32, fur_px(0xffc2e4, 0xfff0f8, 4)))
    bed = mat('sl_bed', 0xffffff, rough=0.9, tex=tex_canvas('sl_bed_t', 32, 32, fur_px(0xff8ccc, 0xffc8e6, 5)))
    foam = mat('sl_foam', 0xf29ac8, rough=0.55, clearcoat=0.2)
    rubber = mat('sl_rubber', 0xffffff, rough=0.7, tex=tex_canvas('sl_rubber_t', 16, 16, tread_px(0x8a5a76, 0x4a2a3c)))
    pom = mat('sl_pom', 0xffffff, rough=0.95, tex=tex_canvas('sl_pom_t', 32, 32, fur_px(0xfff0f8, 0xffffff, 6)))
    def tag_px(px):
        h, w = px.shape[:2]; px[:] = hexrgb(0xd01c2a); px[0] = px[-1] = hexrgb(0xffd23b)
        text_px(px, 'MOM', 2, 2, 1, 0xffffff)
    tagm = mat('sl_tag', 0xffffff, rough=0.6, tex=tex_canvas('sl_tag_t', 21, 11, tag_px))
    Y_BOT, Y_MID, Y_BED = -0.016, -0.007, 0.011
    zs = [-0.14 + 0.28 * i / 47 for i in range(48)]
    sole = loft([(0, 0, z) for z in zs], lambda i, t: squircle(max(interp(SOLE_HW, zs[i]), 0.0008), Y_BOT, Y_BED), m=foam, name='sole', close=(True, True), smooth_angle=40)
    for mm in (rubber, bed): sole.data.materials.append(mm)
    for f in sole.data.polygons:
        if f.normal.z > 0.7: f.material_index = 2  # the plush footbed (blender z = game up)
        elif f.center.z < Y_MID: f.material_index = 1
    uv_box(sole, 0.03)
    # the toe box: a plush dome over the front of the sole, open at the back where your foot goes in
    TOP = [(-0.14, Y_BED + 0.004), (-0.128, 0.03), (-0.11, 0.046), (-0.08, 0.06), (-0.04, 0.067), (-0.008, 0.07)]
    st = [-0.138 + (-0.008 + 0.138) * i / 21 for i in range(22)]
    up, path = arch(st, lambda z: max(interp(SOLE_HW, z) + 0.003, 0.006), lambda z: interp(TOP, z), Y_BED - 0.004, n=16, name='upper', m=plush)
    jitter(up, 0.0011, 7)
    md = up.modifiers.new('solid', 'SOLIDIFY'); md.thickness = 0.009; md.offset = 1.0
    apply_mods(up); smooth(up, 60); uv_box(up, 0.035)
    # rolled collar round the opening + the pom-pom on top
    col = sweep([(x * 1.06, y + 0.004, z + 0.002) for x, y, z in path], 0.0085, m=collar, seg=10, name='collar')
    jitter(col, 0.0009, 8); uv_box(col, 0.03)
    pp = bpy.data.objects.new('pom', bpy.data.meshes.new('pom'))
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.023); bm.to_mesh(pp.data); bm.free()
    bpy.context.scene.collection.objects.link(pp); pp.data.materials.append(pom); pp.location = gv(0, 0.082, -0.078)
    for p in pp.data.polygons: p.use_smooth = True
    jitter(pp, 0.004, 9); uv_box(pp, 0.03)
    tag = box((0.0014, 0.02, 0.04), (0.057, 0.032, -0.064), tagm, rot=(0, 0, -0.38), name='tag')
    apply_mods(tag); c = centre(tag)
    uv_planar(tag, c, (0.04, 0.02), 'x')
    WZ = {'sl_foam': 'a', 'sl_plush': 'b', 'sl_collar': 'b', 'sl_pom': 'b', 'sl_tag': 'n'}
    parts = zone_join([sole, up, col, pp, tag], 'slipper', WZ, default='b')
    return parts


def slipper_files():
    parts = slipper()
    meta = {'kind': 'weapon', 'id': 'slipper', 'paint': ['sl_plush'], 'muzzle': [0, 0, -0.15], 'hatAt': [[0, 0.077, -0.035], 0.07]}
    pj = clone_scaled(parts, 1.6, '_pj')
    root = finish('w_slipper', parts, meta)
    pjr = finish('pj_slipper', pj, {'kind': 'proj', 'id': 'slipper', 'hatAt': [[0, 0.123, -0.056], 0.11]})
    return [(root, 'w_slipper'), (pjr, 'pj_slipper')]


def croc():
    foam = mat('cr_foam', 0x7dff4f, rough=0.45, clearcoat=0.15)
    sole = mat('cr_sole', 0xffffff, rough=0.6, tex=tex_canvas('cr_sole_t', 16, 16, tread_px(0x5ad82e, 0x2e8a1a)))
    rivet = mat('cr_rivet', 0xf2fff0, rough=0.3, clearcoat=0.5)
    L0, L1 = -0.205, 0.11
    HW = [(L0, 0.0), (-0.2, 0.024), (-0.19, 0.04), (-0.17, 0.054), (-0.13, 0.061), (-0.08, 0.06), (-0.03, 0.054), (0.02, 0.05), (0.07, 0.052),
          (0.095, 0.046), (0.105, 0.034), (0.109, 0.018), (L1, 0.0)]
    TOPY = [(L0, -0.01), (-0.195, 0.03), (-0.17, 0.058), (-0.13, 0.07), (-0.09, 0.068), (-0.05, 0.055), (0.0, 0.04), (0.06, 0.035), (L1, 0.035)]
    zs = [L0 + (L1 - L0) * i / 55 for i in range(56)]
    body = loft([(0, 0, z) for z in zs], lambda i, t: squircle(max(interp(HW, zs[i]), 0.0008), -0.042, interp(TOPY, zs[i]), K=28, p=0.72),
                m=foam, name='clog', close=(True, True), smooth_angle=50)
    body.data.materials.append(sole)
    for f in body.data.polygons:
        if f.center.z < -0.03: f.material_index = 1
    uv_box(body, 0.03)
    # foot opening + the hollow inside
    op = ball(1.0, (0, 0.085, 0.05), scale=(0.05, 0.07, 0.115), seg=24, rings=14, name='open')
    cut(body, op)
    cav = ball(1.0, (0, 0.017, -0.035), scale=(0.046, 0.04, 0.128), seg=24, rings=14, name='cav')
    cut(body, cav)
    holes = []
    for row, (x0, n, z0, dz) in enumerate(((0.0, 4, -0.165, 0.028), (0.024, 4, -0.155, 0.028), (-0.024, 4, -0.155, 0.028))):
        for k in range(n): holes.append((x0, z0 + k * dz))
    for x, z in holes: cut(body, cyl(0.0058, 0.08, (x, 0.07, z), axis='y', seg=12, name='hole'))
    for sx in (1, -1):
        for k in range(3): cut(body, cyl(0.0052, 0.03, (sx * 0.058, 0.02, -0.16 + k * 0.03), axis='x', seg=12, name='side_hole'))
    smooth(body, 50)
    # heel strap on two rivets, round the back of the heel
    pts = []
    for k in range(17):
        a = math.pi * k / 16
        pts.append((0.0585 * math.cos(a), 0.024 - 0.012 * math.sin(a), 0.035 + 0.088 * math.sin(a)))
    strap = sweep(pts, 0.013, m=foam, seg=8, name='strap', squash=(1.0, 0.34))
    rivets = []
    for sx in (1, -1):
        rivets.append(cyl(0.0095, 0.006, (sx * 0.064, 0.024, 0.035), rivet, axis='x', seg=16, bev=0.0012, name='rivet'))
        rivets.append(cyl(0.004, 0.004, (sx * 0.0675, 0.024, 0.035), foam, axis='x', seg=10, name='rivet_dot'))
    # charms in three of the holes
    banana = sweep([(0.0 - 0.012 + 0.024 * t, 0.081 + 0.012 * math.sin(math.pi * t), -0.137 - 0.004 * t) for t in [i / 8 for i in range(9)]],
                   [0.0025, 0.004, 0.0048, 0.005, 0.005, 0.005, 0.0048, 0.004, 0.0022], m=mat('cr_banana', 0xffe135, rough=0.35, clearcoat=0.6), seg=6, name='ch_banana')
    duck = [ball(0.0075, (0.024, 0.083, -0.099), mat('cr_duck', 0xffd23b, rough=0.3, clearcoat=0.7), seg=12, rings=8, name='ch_duck'),
            ball(0.0048, (0.024, 0.093, -0.105), mat('cr_duck', 0xffd23b), seg=10, rings=6, name='ch_duckh'),
            box((0.004, 0.0018, 0.004), (0.024, 0.092, -0.11), mat('cr_beak', 0xff8a1a, rough=0.4), name='ch_beak')]
    skull = [ball(0.0075, (-0.024, 0.084, -0.127), mat('cr_bone', 0xf6f2e6, rough=0.4, clearcoat=0.4), seg=12, rings=8, name='ch_skull')]
    for ex in (-0.0028, 0.0028): skull.append(ball(0.0019, (-0.024 + ex, 0.0855, -0.1338), mat('cr_eye', 0x111111, rough=0.5), seg=8, rings=6, name='ch_eye'))
    WZ = {'cr_foam': 'b', 'cr_rivet': 'n', 'cr_banana': 'n', 'cr_duck': 'n', 'cr_beak': 'n', 'cr_bone': 'n', 'cr_eye': 'n'}
    parts = zone_join([body, strap] + rivets + [banana] + duck + skull, 'croc', WZ, default='b',
                      rule=lambda mn, c: 'a' if mn == 'cr_foam' and c[2] > 0.0 else None)
    return parts


def croc_files():
    parts = croc()
    meta = {'kind': 'weapon', 'id': 'slipper', 'skin': 'slipper_croc', 'paint': ['cr_foam'], 'muzzle': [0, 0, -0.15], 'hatAt': [[0, 0.07, -0.06], 0.07]}
    pj = clone_scaled(parts, 1.6, '_pj')
    root = finish('w_slipper_croc', parts, meta)
    pjr = finish('pj_slipper_croc', pj, {'kind': 'proj', 'id': 'slipper', 'skin': 'slipper_croc', 'hatAt': [[0, 0.112, -0.096], 0.11]})
    return [(root, 'w_slipper_croc'), (pjr, 'pj_slipper_croc')]


main_multi(lambda: slipper_files() + croc_files(), exposure=-0.4)
