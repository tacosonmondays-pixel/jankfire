# Slipper skin "Flip-Flop" (w_slipper_flipflop) + the thrown one (pj_slipper_flipflop, x1.6 like the other slippers).
# A beach flip-flop, real size (EU 42: 28 cm x 10.5 cm across the ball, 6 cm at the arch): a two-layer EVA sole (an 8 mm
# footbed over a 10 mm treaded bottom), a toe-grip ridge, a Y strap of 16 mm PVC from the toe post between the first
# two toes back to plugs in the sole either side of the arch.
# Made fun: the footbed is worn dark where a foot has been (toes, ball, heel), a SALE tag still on the strap, and
# a pink wad of gum stuck underneath. Same spots as the slipper: toe to -z, centred, muzzle at the toe.
# run: blender -b --python tools/blender/make_slipper_flipflop.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *

# half width along the sole (z: -0.14 toe .. +0.14 heel), a right foot: the big toe side (-x) runs further forward
HW = [(-0.14, 0.0), (-0.137, 0.022), (-0.13, 0.035), (-0.115, 0.046), (-0.09, 0.052), (-0.06, 0.0525), (-0.03, 0.048), (0.0, 0.039),
      (0.03, 0.033), (0.06, 0.034), (0.09, 0.037), (0.115, 0.035), (0.13, 0.027), (0.138, 0.015), (0.14, 0.0)]
SKEW = [(-0.14, -0.012), (-0.1, -0.007), (-0.05, 0.0), (0.0, 0.004), (0.14, 0.0)]  # the toe end leans to the big toe
Y0, Y1, Y2 = -0.009, 0.001, 0.009   # bottom, the layer line, the footbed
POST = (-0.012, -0.088)              # toe post (x, z)
PLUGS = [(0.036, 0.004), (-0.04, 0.01)]  # strap plugs (x, z) on the outer / inner side


def interp(tab, z):
    for (z0, a), (z1, b) in zip(tab, tab[1:]):
        if z0 <= z <= z1: return a + (b - a) * (z - z0) / (z1 - z0)
    return tab[0][1] if z < tab[0][0] else tab[-1][1]


def squircle(hw, y0, y1, K=20, p=0.3):
    yc, hh = (y0 + y1) / 2, (y1 - y0) / 2
    out = []
    for j in range(K):
        a = 2 * math.pi * j / K; c, s = math.cos(a), math.sin(a)
        out.append((yc + hh * math.copysign(abs(s) ** p, s), hw * math.copysign(abs(c) ** p, c)))
    return out


def tread_px(base, dark):
    def draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(base)
        for y in range(0, h, 4):
            for x in range((y // 4 % 2) * 2, w, 4): px[y:y + 2, x:x + 2] = hexrgb(dark)
    return draw


def footbed_px(px):
    h, w = px.shape[:2]  # row 0 = the toe end, col 0 = -x (the big toe side)
    r = np.random.default_rng(71)
    px[:] = hexrgb(0xff7ad8) * (0.95 + 0.06 * r.random((h, w, 1)))
    worn = 0xd8409e
    # x (m) -> col, z (m) -> row
    C = lambda x: (x + 0.06) / 0.12 * w
    Rw = lambda z: (z + 0.15) / 0.30 * h
    for x, z, rad in ((-0.03, -0.122, 0.013), (-0.006, -0.124, 0.0075), (0.01, -0.118, 0.0068), (0.024, -0.11, 0.006), (0.036, -0.1, 0.0055)):
        px_disc(px, C(x), Rw(z), rad / 0.12 * w, worn)  # toes
    for k in range(10):  # the ball and the heel: a smudge of overlapping discs
        t = k / 9
        px_disc(px, C(-0.012 + 0.03 * t), Rw(-0.07 + 0.01 * math.sin(t * 3)), 0.02 / 0.12 * w, worn)
        px_disc(px, C(0.002 + 0.004 * math.sin(t * 6)), Rw(0.085 + 0.03 * t), 0.022 / 0.12 * w, worn)
    n = r.random((h, w)); px[n > 0.93] = hexrgb(0xf2e2b0)  # sand
    px[:] *= (0.93 + 0.08 * r.random((h, w, 1)))


def tag_px(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xfffbe8); px[0] = px[-1] = hexrgb(0xff3030); px[:, 0] = px[:, -1] = hexrgb(0xff3030)
    text_px(px, 'SALE', 2, 2, 1, 0xff3030)


def flipflop():
    bed = mat('ff_bed', 0xffffff, rough=0.6, tex=tex_canvas('ff_bed_t', 48, 112, footbed_px))
    foam = mat('ff_foam', 0xff7ad8, rough=0.55, clearcoat=0.1)
    base = mat('ff_base', 0xffffff, rough=0.65, tex=tex_canvas('ff_base_t', 16, 16, tread_px(0xffe14d, 0xd8b020)))
    strap = mat('ff_strap', 0x4fd8ff, rough=0.25, clearcoat=0.7)
    plug = mat('ff_plug', 0x2aa8d8, rough=0.3, clearcoat=0.5)
    tagm = mat('ff_tag', 0xffffff, rough=0.6, tex=tex_canvas('ff_tag_t', 27, 11, tag_px))
    gum = mat('ff_gum', 0xff8ad0, rough=0.35, clearcoat=0.4)
    zs = [-0.14 + 0.28 * i / 47 for i in range(48)]
    cen = [(interp(SKEW, z), 0, z) for z in zs]
    top = loft(cen, lambda i, t: squircle(max(interp(HW, zs[i]), 0.0008), Y1 - 0.0005, Y2, K=24, p=0.22), m=foam, name='top', close=(True, True), smooth_angle=40)
    top.data.materials.append(bed)
    for f in top.data.polygons:
        if f.normal.z > 0.8: f.material_index = 1  # the footbed (blender z = game up)
    bpy.context.view_layer.update()
    uv_planar(top, (0, 0, -0.0), (0.12, 0.30), 'y')
    bot = loft(cen, lambda i, t: squircle(max(interp(HW, zs[i]) - 0.0006, 0.0008), Y0, Y1, K=24, p=0.25), m=base, name='bot', close=(True, True), smooth_angle=40)
    uv_box(bot, 0.03)
    # toe-grip ridge across the front of the footbed
    ridge = sweep([(interp(SKEW, -0.105) + x, Y2 + 0.0006, -0.105 + 0.006 * (x / 0.04) ** 2) for x in [-0.04 + 0.08 * k / 8 for k in range(9)]], 0.0016, foam, seg=6, name='ridge', squash=(0.6, 1.0))
    uv_box(ridge, 0.03)
    # ---- the Y strap: from the top of the post, out and back over the instep to the plugs either side
    px_, pz_ = POST
    ptop = (px_, Y2 + 0.026, pz_ + 0.004)
    post = rod((px_, Y2 - 0.001, pz_), ptop, 0.0042, strap, seg=10, name='post', r1=0.0034)
    knob = ball(0.0068, ptop, strap, scale=(1, 0.75, 1.15), seg=12, rings=8, name='knob')
    arms = []
    for k, (x1, z1) in enumerate(PLUGS):
        sx = 1 if x1 > px_ else -1
        pts = []
        for i in range(13):
            t = i / 12
            x = ptop[0] + (x1 - ptop[0]) * (1 - (1 - t) ** 1.4)
            z = ptop[2] + (z1 - ptop[2]) * t
            y = ptop[1] + (Y2 + 0.002 - ptop[1]) * t ** 1.8 + 0.014 * math.sin(math.pi * t) * (1 - t)
            pts.append((x, y, z))
        arms.append(sweep(pts, 0.0082, strap, seg=10, name='arm', squash=(0.28, 1.0)))
        arms.append(cyl(0.0058, 0.0035, (x1, Y2 + 0.0012, z1), plug, axis='y', seg=12, bev=0.0008, name='plug'))
        arms.append(cyl(0.0052, 0.003, (x1, Y0 - 0.0006, z1), plug, axis='y', seg=12, bev=0.0008, name='plug_under'))
    for o in [post, knob] + arms: uv_box(o, 0.03)
    # the SALE tag on a loop of plastic thread off the outer strap
    tz = 0.5 * (ptop[2] + PLUGS[0][1]); tx = 0.5 * (ptop[0] + PLUGS[0][0]) + 0.006
    thread = sweep([(tx, Y2 + 0.022, tz), (tx + 0.008, Y2 + 0.02, tz + 0.004), (tx + 0.014, Y2 + 0.012, tz + 0.006)], 0.0006, plug, seg=4, name='thread')
    tag = box((0.0012, 0.012, 0.03), (tx + 0.016, Y2 + 0.004, tz + 0.012), tagm, rot=(0.0, -0.5, 0.25), name='tag')
    apply_mods(tag)
    # decal UVs: face it toward +x (the side that's outward)
    me = tag.data; uvl = (me.uv_layers.active or me.uv_layers.new()).data
    c = centre(tag)
    for f in me.polygons:
        fl = 1 if (tag.matrix_world.to_3x3() @ f.normal).x >= 0 else -1  # each side reads the right way round
        for li in f.loop_indices:
            v = tag.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            uvl[li].uv = (0.5 - fl * (-v.y - c[2]) / 0.03, (v.z - c[1]) / 0.012 + 0.5)
    # gum under the heel
    g = ball(0.012, (0.008, Y0 - 0.0028, 0.075), gum, scale=(1.0, 0.3, 1.25), seg=12, rings=6, name='gum')
    jitter(g, 0.0012, 72); uv_box(g, 0.02)
    WZ = {'ff_foam': 'a', 'ff_base': 'a', 'ff_bed': 'b', 'ff_strap': 'b', 'ff_plug': 'b', 'ff_tag': 'n', 'ff_gum': 'n'}
    return zone_join([top, bot, ridge, post, knob, thread, tag, g] + arms, 'flipflop', WZ, default='b')


def files():
    parts = flipflop()
    meta = {'kind': 'weapon', 'id': 'slipper', 'skin': 'slipper_flipflop', 'paint': ['ff_foam'], 'muzzle': [0, 0, -0.15], 'hatAt': [[POST[0], Y2 + 0.032, POST[1] + 0.004], 0.06]}
    pj = clone_scaled(parts, 1.6, '_pj')
    root = finish('w_slipper_flipflop', parts, meta)
    pjr = finish('pj_slipper_flipflop', pj, {'kind': 'proj', 'id': 'slipper', 'skin': 'slipper_flipflop', 'hatAt': [[POST[0] * 1.6, (Y2 + 0.032) * 1.6, (POST[1] + 0.004) * 1.6], 0.1]})
    return [(root, 'w_slipper_flipflop'), (pjr, 'pj_slipper_flipflop')]


main_multi(files, exposure=-0.4)
