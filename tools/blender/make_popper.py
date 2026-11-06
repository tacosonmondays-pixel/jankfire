# Party Popper + the Champagne skin.
# Party Popper: a real party popper (a 75 mm foil-wrapped cone, tissue cap over the mouth, a plastic base plug, the
# pull string out of the narrow end with a ring on it) x3.2 so it fills the code popper: wide open end forward (the
# muzzle, where the confetti comes out), the string back toward your hand.
# Made fun: the warning sticker is the opposite of the real one: POINT AT FACE.
# Champagne: a 750 ml bottle (300 x 89 mm, deep punt, shoulder, bague lip) x1.02, lying along the aim with the cork
# forward: dark green glass, gold foil torn off the top, the mushroom cork in its wire cage with the plaque on top,
# the twisted wire loop. Made fun: the label says BRUT FORCE.
# Both are items: they pop into your left hand (weapons.js POP) and shove everyone in front.
# run: blender -b --python tools/blender/make_popper.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link



def band_patch(zf, zb, rfun, half_h, m, name, nu=10, nv=6, out=0.0007, a_mid=0.0):
    """a decal of constant height (2 x half_h of arc) wrapped on a round thing lying along game z, centred on the
    angle a_mid (0 = facing +x). rfun(z) = the surface radius. uv: u from zb (u=0) to zf (u=1), v up."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    grid = []
    for i in range(nu + 1):
        z = zb + (zf - zb) * i / nu; r = rfun(z) + out
        row = []
        for j in range(nv + 1):
            a = a_mid + (j / nv - 0.5) * 2 * half_h / r
            row.append(bm.verts.new(gv(math.cos(a) * r, math.sin(a) * r, z)))
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                lp[uvl].uv = (ii / nu, jj / nv)
    o = _obj(name, bm, m)
    # face it outward
    p = o.data.polygons[0]
    if Vector((p.center.x, p.center.y, 0)).dot(Vector((p.normal.x, p.normal.y, 0))) < 0:
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    return o


# ------------------------------------------------------------ party popper
ZM, RM = -0.2, 0.05       # mouth (front)
ZB, RB = 0.035, 0.017     # narrow end
def cone_r(z): return RB + (RM - RB) * (ZB - z) / (ZB - ZM)


def popper():
    def foil_px(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(141)
        yy, xx = np.mgrid[0:h, 0:w]
        px[:] = hexrgb(0xff4fc8) * (0.9 + 0.12 * r.random((h, w, 1)))
        px[((xx + yy) % 16) < 2] = hexrgb(0xffe14d)
        px[((xx + yy + 8) % 16) < 1] = hexrgb(0x4fd8ff)
        for k in range(10):
            cx, cy = r.integers(2, w - 2), r.integers(2, h - 2)
            px[cy, cx - 1:cx + 2] = hexrgb(0xffffff); px[cy - 1:cy + 2, cx] = hexrgb(0xffffff)
    foil = mat('pp_foil', 0xffffff, rough=0.22, metal=0.85, tex=tex_canvas('pp_foil_t', 32, 32, foil_px))
    gold = mat('pp_gold', 0xffd23b, rough=0.25, metal=1.0)
    def tissue_px(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(142)
        px[:] = hexrgb(0xffe14d) * (0.93 + 0.08 * r.random((h, w, 1)))
        for k in range(26):
            c = [0xff4fd8, 0x4fd8ff, 0x7dff4f, 0xff7a1a][k % 4]
            px_disc(px, r.uniform(1, w - 1), r.uniform(1, h - 1), 1.3, c)
    tissue = mat('pp_tissue', 0xffffff, rough=0.92, tex=tex_canvas('pp_tissue_t', 32, 32, tissue_px))
    plastic = mat('pp_plastic', 0xf6f4ee, rough=0.3, clearcoat=0.6)
    string = mat('pp_string', 0xf2f2f2, rough=0.7)
    ringm = mat('pp_ring', 0x4fd8ff, rough=0.2, clearcoat=1.0)
    def stick_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xf6f4ee); px[:1] = px[-1:] = hexrgb(0xe0202a)
        text_px(px, 'POINT AT FACE', 3, 3, 1, 0xe0202a)
    sticker = mat('pp_sticker', 0xffffff, rough=0.45, clearcoat=0.3, tex=tex_canvas('pp_sticker_t', 84, 13, stick_px))
    parts = []; A = parts.append

    prof = [(RB, ZB)]
    for k in range(1, 9):
        z = ZB + (ZM - ZB) * k / 8
        prof.append((cone_r(z) * (1 + 0.025 * math.sin(math.pi * k / 8)), z))
    body = lathe(prof, (0, 0, 0), foil, seg=28, cap=False, name='pp_cone')
    jitter(body, 0.0005, 3)   # crinkled foil
    uv_cyl(body, 'z', ZB, ZM); A(body)
    A(tube([(math.cos(a) * (RM + 0.001), math.sin(a) * (RM + 0.001), ZM + 0.002) for a in [k * 2 * math.pi / 28 for k in range(28)]], 0.0028, gold, seg=8, name='pp_rim', closed=True))
    cap = lathe([(0.0, ZM - 0.013), (0.02, ZM - 0.012), (0.036, ZM - 0.0085), (0.0485, ZM - 0.003), (RM + 0.0028, ZM + 0.003), (RM + 0.003, ZM + 0.012), (RM + 0.0012, ZM + 0.016)],
                (0, 0, 0), tissue, seg=28, cap=False, name='pp_cap')
    jitter(cap, 0.0011, 5)
    uv_box(cap, 0.06); A(cap)
    A(lathe([(RB - 0.0005, ZB - 0.004), (RB + 0.0018, ZB - 0.001), (RB + 0.0018, ZB + 0.008), (RB - 0.001, ZB + 0.012), (0.006, ZB + 0.013), (0.0, ZB + 0.013)], (0, 0, 0), plastic, seg=20, name='pp_base'))
    sp = [(0, 0, ZB + 0.012), (0, -0.003, ZB + 0.035), (0, -0.01, ZB + 0.06), (0, -0.016, ZB + 0.078)]
    A(sweep(sp, 0.0016, string, seg=6, name='pp_string'))
    rc = (0, -0.022, ZB + 0.093)
    A(tube([(0, rc[1] + 0.015 * math.sin(a), rc[2] + 0.015 * math.cos(a)) for a in [k * 2 * math.pi / 20 for k in range(20)]], 0.0028, ringm, seg=8, name='pp_ringtube', closed=True))
    A(band_patch(-0.185, -0.055, lambda z: cone_r(z) * (1 + 0.025 * math.sin(math.pi * (ZB - z) / (ZB - ZM))), 0.0102, sticker, 'pp_sticker', a_mid=0.25))
    WZ = {'pp_foil': 'a', 'pp_gold': 'b', 'pp_tissue': 'b', 'pp_plastic': 'b'}
    bodies = zone_join(parts, 'popper_body', WZ, default='n')
    meta = {'kind': 'weapon', 'id': 'popper', 'paint': ['pp_foil'], 'muzzle': [0, 0, -0.21], 'hatAt': [[0, cone_r(-0.11) + 0.002, -0.11], 0.06]}
    return finish('w_popper', bodies, meta)


# ------------------------------------------------------------ champagne
def bottle():
    glass = mat('pb_glass', 0x174222, rough=0.05, metal=0.15, clearcoat=1.0)
    def foil_px(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(151)
        px[:] = hexrgb(0xe8b83a) * (0.85 + 0.25 * r.random((h, w, 1)))
        px[r.random((h, w)) < 0.08] = hexrgb(0xfff0a0)
        px[:, 1:3] = hexrgb(0xc81e2c)
    foil = mat('pb_foil', 0xffffff, rough=0.3, metal=1.0, tex=tex_canvas('pb_foil_t', 32, 16, foil_px))
    cork = mat('pb_cork', 0xffffff, rough=0.85, tex=tex_noise('pb_cork_t', 0xc8a070, var=0.15, size=16, speck=0x7a5a30, speck_p=0.22, seed=152))
    wire = mat('pb_wire', 0xc8ccd4, rough=0.25, metal=1.0)
    def plaque_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xe8b83a)
        px_disc(px, w / 2, h / 2, w / 2 - 1, 0xc81e2c, r_in=w / 2 - 2.2)
        for k, (x, y) in enumerate(((5, 10), (8, 6), (11, 10))): px_disc(px, x, y, 1.4, 0xc81e2c)
        px[10:12, 5:12] = hexrgb(0xc81e2c)
    plaque = mat('pb_plaque', 0xffffff, rough=0.2, metal=0.9, tex=tex_canvas('pb_plaque_t', 16, 16, plaque_px))
    def label_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xf4ead0)
        px[1:2, 1:w - 1] = px[h - 2:h - 1, 1:w - 1] = hexrgb(0xc8a040); px[1:h - 1, 1:2] = px[1:h - 1, w - 2:w - 1] = hexrgb(0xc8a040)
        # a little pink crown
        cx = w // 2
        for k, dx in enumerate((-6, 0, 6)): px_disc(px, cx + dx, 5, 1.6, 0xff4fd8)
        px[6:9, cx - 7:cx + 8] = hexrgb(0xff4fd8)
        text_px(px, 'BRUT', (w - 47) // 2, 11, 2, 0x1a1a1a)
        text_px(px, 'FORCE', (w - 29) // 2, 28, 1, 0xc81e2c)
    label = mat('pb_label', 0xffffff, rough=0.5, clearcoat=0.3, tex=tex_canvas('pb_label_t', 64, 38, label_px))
    parts = []; A = parts.append
    prof = [(0.0, 0.07), (0.012, 0.0745), (0.024, 0.088), (0.034, 0.0955), (0.04, 0.0985), (0.0452, 0.096), (0.0466, 0.088), (0.0466, -0.04),
            (0.0458, -0.054), (0.0405, -0.074), (0.031, -0.092), (0.0222, -0.107), (0.0166, -0.12), (0.0155, -0.168), (0.0157, -0.1735),
            (0.0178, -0.1755), (0.0178, -0.1815), (0.0148, -0.1835)]
    A(lathe(prof, (0, 0, 0), glass, seg=32, name='pb_bottle'))
    fo = lathe([(0.0225, -0.106), (0.0175, -0.12), (0.0165, -0.16), (0.0166, -0.171), (0.0171, -0.1745)], (0, 0, 0), foil, seg=28, cap=False, name='pb_foil')
    me = fo.data   # torn: the top edge of the foil is ragged
    rng = random.Random(6)
    for v in me.vertices:
        if -v.co.y < -0.1744: v.co.y -= rng.uniform(0.0, 0.006)   # blender -y = game +z: pull some back down the neck
    me.update()
    jitter(fo, 0.0004, 8)
    uv_cyl(fo, 'z', -0.106, -0.1745); A(fo)
    A(lathe([(0.0148, -0.1825), (0.0158, -0.19), (0.0169, -0.198), (0.0167, -0.2045), (0.0146, -0.208), (0.008, -0.2094), (0.0, -0.2097)], (0, 0, 0), cork, seg=24, name='pb_cork'))
    pq = cyl(0.0136, 0.0014, (0, 0, -0.2103), plaque, axis='z', seg=24, bev=0.0004, name='pb_plaque'); A(pq)
    A(tube([(math.cos(a) * 0.0181, math.sin(a) * 0.0181, -0.1838) for a in [k * 2 * math.pi / 24 for k in range(24)]], 0.0007, wire, seg=5, name='pb_wirering', closed=True))
    for k in range(4):  # the cage's legs, plaque edge -> over the cork -> the ring
        a = math.pi / 4 + k * math.pi / 2
        pts = [(math.cos(a) * rr, math.sin(a) * rr, z) for rr, z in ((0.0132, -0.2098), (0.0166, -0.2046), (0.0177, -0.197), (0.0168, -0.19), (0.0182, -0.1838))]
        A(tube(pts, 0.00065, wire, seg=5, name='pb_wireleg'))
    A(tube([(0.0182, 0.0, -0.1838), (0.024, 0.002, -0.182), (0.028, -0.002, -0.179), (0.029, 0.003, -0.176), (0.026, 0.0, -0.1745)], 0.0007, wire, seg=5, name='pb_twist'))
    lb = band_patch(-0.036, 0.07, lambda z: 0.0466, 0.0278, label, 'pb_label', nu=8, nv=8, out=0.0006, a_mid=0.25); A(lb)
    for p in parts:
        if p.data.materials and p.data.materials[0] in (glass, cork): uv_box(p, 0.05)
    apply_mods(pq); uv_planar(pq, (0, 0, -0.2103), 0.0272, 'z')
    WZ = {'pb_glass': 'a', 'pb_foil': 'b', 'pb_cork': 'b', 'pb_wire': 'b', 'pb_plaque': 'b'}
    bodies = zone_join(parts, 'bottle_body', WZ, default='n')
    meta = {'kind': 'weapon', 'id': 'popper', 'skin': 'popper_bottle', 'paint': ['pb_glass'], 'muzzle': [0, 0, -0.21], 'hatAt': [[0, 0.0466, 0.035], 0.06]}
    return finish('w_popper_bottle', bodies, meta)


main_multi(lambda: [(popper(), 'w_popper'), (bottle(), 'w_popper_bottle')], exposure=-0.6)
