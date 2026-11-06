# Bow, the Compound skin and the flying arrow.
# Bow: a 62" takedown recurve (23" laminated hardwood riser with a deflexed profile, a leather grip, an arrow shelf
# with a stick-on rest, limb pockets with brass knurled bolts, short glass-and-maple limbs with candy tip overlays,
# a Dacron string with servings, a brass nock set and yarn puff silencers), x0.5 so it's the code bow's 0.8 m.
# Cross-sections are 1.4x real so it reads at that size. A nocked cedar arrow (shield-cut feathers, a printed
# wrap, a 3-blade broadhead). The game draws it: the arrow node slides back, the limbs flex, the string bends to the
# nock (meta.bow, glbkit.js bowRig).
# Made fun: the limbs are labelled THIS END UP and THIS END ALSO UP, and the arrow wrap says SORRY.
# run: blender -b --python tools/blender/make_bow.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _obj, _link

R_STR = 0.0017          # string radius
ARROW_R = 0.0034        # held arrow shaft radius


# ------------------------------------------------------------ shared helpers
def section(w, h, k=14, ex=0.42):
    """a rounded-rectangle section: (a = across x, b = along the path's side vector) points"""
    out = []
    for j in range(k):
        th = 2 * math.pi * j / k
        c, s = math.cos(th), math.sin(th)
        out.append((w / 2 * math.copysign(abs(c) ** ex, c), h / 2 * math.copysign(abs(s) ** ex, s)))
    return out


LIMB_K = 22
LIMB_SLOTS = ['core'] + ['glass'] * 3 + ['top'] * 4 + ['glass'] * 3 + ['core'] + ['glass'] * 3 + ['bot'] * 4 + ['glass'] * 3


def limb_section(w, h):
    """a limb's section: glass faces (top = the side vector's + side, bot = - side), rounded corners and a maple core
    stripe up each edge. 22 points; LIMB_SLOTS says what each face slot is."""
    rc = 0.28 * h; e = 0.22 * h; fx = w / 2 - rc
    pts = [(w / 2, -e), (w / 2, e)]
    pts += [(fx + rc * math.cos(math.radians(a)), (h / 2 - rc) + rc * math.sin(math.radians(a))) for a in (30, 60)]
    pts += [(fx - 2 * fx * k / 4, h / 2) for k in range(4)]
    pts += [(-fx - rc * math.sin(math.radians(a)), (h / 2 - rc) + rc * math.cos(math.radians(a))) for a in (0, 30, 60)]
    pts += [(-w / 2, e), (-w / 2, -e)]
    pts += [(-fx - rc * math.cos(math.radians(a)), -(h / 2 - rc) - rc * math.sin(math.radians(a))) for a in (30, 60)]
    pts += [(-fx + 2 * fx * k / 4, -h / 2) for k in range(4)]
    pts += [(fx + rc * math.sin(math.radians(a)), -(h / 2 - rc) - rc * math.cos(math.radians(a))) for a in (0, 30, 60)]
    return pts


def limb_path(p0, L, a0, a_mid, u_mid, a_tip, sign=1, n=36):
    """centre line of a braced recurve limb from its pivot p0 = (y, z): the angle (degrees from vertical, + = back
    toward the archer) runs a0 -> a_mid to u_mid, then curls forward to a_tip. sign = +1 top limb, -1 bottom."""
    pts = [(0.0, p0[0], p0[1])]
    y, z = p0
    for i in range(n):
        u = (i + 0.5) / n
        a = a0 + (a_mid - a0) * u / u_mid if u < u_mid else a_mid + (a_tip - a_mid) * ((u - u_mid) / (1 - u_mid)) ** 1.5
        y += sign * L / n * math.cos(math.radians(a)); z += L / n * math.sin(math.radians(a))
        pts.append((0.0, y, z))
    return pts


def frame(path, i):
    """tangent t and side vector B (= t x game x) of a path in the yz plane at point i (game coords)"""
    P = [Vector(p) for p in path]
    t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized()
    return t, t.cross(Vector((1, 0, 0)))


def knurl(r, h, pos, m, axis_dir, seg=24, name='knurl'):
    """a knurled knob: a short cylinder with ridged sides, its axis along axis_dir (game vector)"""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x)
        if abs(v.co.z) < h / 2 + 1e-6 and int(round(a / (2 * math.pi / seg))) % 2: v.co.x *= 0.86; v.co.y *= 0.86
    d = gv(*axis_dir).normalized()
    q = Vector((0, 0, 1)).rotation_difference(d)
    bmesh.ops.transform(bm, matrix=q.to_matrix().to_4x4(), verts=bm.verts)
    o = _obj(name, bm, m); o.location = gv(*pos)
    for p in o.data.polygons: p.use_smooth = False
    return o


def pom(r, pos, m, seed):
    """a yarn puff silencer: a fuzzy lumpy ball"""
    b = ball(r, pos, m, seg=12, rings=8)
    return jitter(b, r * 0.28, seed)


def ring_patch(z0, z1, r0, r1, a0, a1, m, name, nu=8, na=12, pos=(0, 0, 0), axis_flip=False):
    """a curved decal on a round thing lying along game z: the part of the cone/cylinder r0 at z0 .. r1 at z1 between
    angles a0..a1 (radians from +x toward +y). uv: u along z (z0 -> z1), v across the angles (a0 -> a1)."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new()
    grid = []
    for i in range(nu + 1):
        t = i / nu; z = z0 + (z1 - z0) * t; r = r0 + (r1 - r0) * t
        row = []
        for j in range(na + 1):
            a = a0 + (a1 - a0) * j / na
            row.append(bm.verts.new(gv(pos[0] + math.cos(a) * r, pos[1] + math.sin(a) * r, pos[2] + z)))
        grid.append(row)
    for i in range(nu):
        for j in range(na):
            vs = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
            f = bm.faces.new(vs)
            for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                lp[uvl].uv = (ii / nu, jj / na)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _obj(name, bm, m)
    # outward normals: recalc may point them in, check one face against the radial direction
    f = o.data.polygons[0]; c = f.center
    if Vector((c.x - gv(*pos).x, c.y - gv(*pos).y, 0)).dot(Vector((f.normal.x, f.normal.y, 0))) < 0:
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.reverse_faces(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    for p in o.data.polygons: p.use_smooth = True
    return o


def string_rod(p0, p1, r, m, name, seg=8):
    return rod(p0, p1, r, m, seg=seg, name=name)


def lerp3(a, b, t): return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))


# ------------------------------------------------------------ textures
def lam_px(px):  # laminated riser: maple, walnut and purpleheart lams, with grain running along the riser
    h, w = px.shape[:2]
    r = np.random.default_rng(31)
    bands = [(0xe8c48a, 9), (0x5a3418, 4), (0xd9b076, 7), (0xb0306e, 3), (0xe2bc84, 10), (0x4a2a12, 5), (0xd8a86a, 8), (0xb0306e, 3), (0xe8c48a, 9), (0x5a3418, 6)]
    x = 0
    for c, bw in bands: px[:, x:x + bw] = hexrgb(c); x += bw
    streak = np.kron(r.random((h // 8, w)), np.ones((8, 1)))[:h, :w]
    px[:] *= (0.86 + 0.16 * (0.6 * streak + 0.4 * r.random((h, w))))[:, :, None]


def limb_label(text, arrow=True):
    def draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0x121216)
        px[0, :] = px[-1, :] = hexrgb(0xff4fd8)
        text_px(px, text, 3, 2, 1, 0xf6f4ee)
        if arrow:
            x0 = 3 + len(text) * 6 + 2
            for k in range(5): px[2 + k, x0 + 4 - k:x0 + 5 + k] = hexrgb(0xffe14d) if k < 4 else hexrgb(0xffe14d)
            px[6:9, x0 + 3:x0 + 6] = hexrgb(0xffe14d)
    return draw


def feather_px(base, edge):
    def draw(px):
        h, w = px.shape[:2]
        r = np.random.default_rng(base & 255)
        px[:] = hexrgb(base) * (0.9 + 0.1 * r.random((h, w, 1)))
        yy, xx = np.mgrid[0:h, 0:w]
        px[((xx + 2 * yy) % 5) == 0] = hexrgb(edge)  # the barbs
    return draw


def wrap_px(text, bg, fg, band):
    def draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(bg)
        px[:, :3] = hexrgb(band); px[:, -3:] = hexrgb(band)
        t = np.zeros((9, len(text) * 6 + 1, 3), np.float32); t[:] = hexrgb(bg)
        text_px(t, text, 1, 1, 1, fg)
        x0 = (w - t.shape[1]) // 2
        px[h // 4 * 3 - 4:h // 4 * 3 + 5, x0:x0 + t.shape[1]] = t           # faces +x (v = 0.25)
        px[h // 4 - 4:h // 4 + 5, x0:x0 + t.shape[1]] = t[::-1, ::-1]        # faces -x, turned so it reads from there
    return draw


# ------------------------------------------------------------ the arrow (held + flying share the design)
def arrow_parts(pre, z_back, length, r, mats, fl_len, fl_h, wrap_len, head_len, head_r, cock_dir=0.0, n_fl=3, nock_len=None):
    """an arrow along game z, its back end at z_back, nose to -z. returns (body parts, head parts).
    mats: shaft, nock, feather, cock, wrap, head"""
    shaft_m, nock_m, fea_m, cock_m, wrap_m, head_m = mats
    body, head = [], []
    z_tip = z_back - length
    nl = nock_len or r * 3.2
    z_nf = z_back - nl                 # the nock's front
    z_hb = z_tip + head_len * 1.05     # where the broadhead ferrule starts
    sh = lathe([(r, z_nf + 0.0005), (r, z_hb)], (0, 0, 0), shaft_m, seg=10, name=pre + '_shaft')
    uv_box(sh, 0.05); body.append(sh)
    # nock: a plastic plug with the string slot (two prongs, the slot runs up-down so the string sits in it)
    body.append(lathe([(r * 0.9, z_nf), (r * 1.15, z_nf + nl * 0.25), (r * 1.15, z_back - nl * 0.55)], (0, 0, 0), nock_m, seg=10, name=pre + '_nock'))
    for sx in (-1, 1):
        body.append(box((r * 0.75, r * 2.1, nl * 0.6), (sx * r * 0.62, 0, z_back - nl * 0.3), nock_m, bev=r * 0.2, name=pre + '_prong'))
    # printed wrap under the fletching
    wz0, wz1 = z_nf - r * 0.6, z_nf - r * 0.6 - wrap_len
    wp = lathe([(r * 1.06, wz0), (r * 1.06, wz1)], (0, 0, 0), wrap_m, seg=16, cap=False, name=pre + '_wrap')
    uv_cyl(wp, 'z', wz0, wz1, turn=-math.pi / 2); body.append(wp)
    # fletching: shield-cut feathers, the cock feather (other colour) points away from the riser
    fz1 = z_nf - r * 1.5; fz0 = fz1 - fl_len   # front (more -z) .. back
    prof = []
    for k in range(9):
        u = k / 8
        prof.append((fz0 + fl_len * u, r * 0.9 + fl_h * (u ** 0.55) * (1 if u < 0.78 else 1 - 0.5 * (u - 0.78) / 0.22)))
    prof += [(fz1, r * 0.9 + fl_h * 0.55), (fz1, r * 0.9)]
    for k in range(n_fl):
        a = cock_dir + 2 * math.pi * k / n_fl
        f = side([(z, y) for z, y in prof], r * 0.28, (0, 0, 0), cock_m if k == 0 else fea_m, name=pre + '_feather', rot=(0, 0, a - math.pi / 2))
        uv_box(f, 0.02); body.append(f)
    # 3-blade broadhead (one mesh, one material: the game paints it the arrow type's colour)
    head.append(lathe([(r * 1.05, z_hb), (r * 1.25, z_hb - head_len * 0.15), (r * 1.2, z_tip + head_len * 0.25), (r * 0.5, z_tip + head_len * 0.06), (0.0, z_tip)], (0, 0, 0), head_m, seg=10, name=pre + '_ferrule'))
    for k in range(3):
        a = cock_dir + math.pi / 3 + 2 * math.pi * k / 3
        blade = side([(z_tip + head_len * 0.06, r * 0.5), (z_hb - head_len * 0.12, head_r), (z_hb - head_len * 0.02, head_r * 0.55), (z_hb - head_len * 0.02, r * 0.6)],
                     max(0.0006, r * 0.22), (0, 0, 0), head_m, name=pre + '_blade', rot=(0, 0, a - math.pi / 2))
        head.append(blade)
    return body, head


def arrow_mats(pre, shaft_col, shaft_dark, nock_col, fea_col, cock_col, wrap_text, wrap_cols, carbon=False):
    if carbon:
        shaft = mat(pre + '_shaft', shaft_col, rough=0.25, clearcoat=0.8, tex=tex_stripes(pre + '_shaft_t', shaft_col, shaft_dark, size=16, width=2, diag=True))
    else:
        shaft = mat(pre + '_shaft', shaft_col, rough=0.4, clearcoat=0.5, tex=tex_wood(pre + '_shaft_t', shaft_col, shaft_dark, size=32, seed=17, rings=3))
    nock = mat(pre + '_nock', nock_col, rough=0.18, clearcoat=1.0)
    fea = mat(pre + '_feather', 0xffffff, rough=0.6, tex=tex_canvas(pre + '_feather_t', 16, 16, feather_px(fea_col, 0xffffff)))
    cock = mat(pre + '_cock', 0xffffff, rough=0.6, tex=tex_canvas(pre + '_cock_t', 16, 16, feather_px(cock_col, 0xffffff)))
    wrap = mat(pre + '_wrap', 0xffffff, rough=0.3, clearcoat=0.8, tex=tex_canvas(pre + '_wrap_t', 48, 32, wrap_px(wrap_text, *wrap_cols)))
    head = mat(pre + '_head', 0xd8dde6, rough=0.18, metal=1.0)
    return shaft, nock, fea, cock, wrap, head


# ------------------------------------------------------------ the recurve
Y_END = 0.142           # riser ends
LIMB_H0 = 0.0076        # limb thickness at the pocket
LIMB_W0 = 0.025         # limb width at the pocket
X_R = -0.0025           # riser centre (x): the riser sits a hair left, the arrow passes on its right
W_R = 0.024             # riser width
X_WIN = -0.0045         # sight window face (the arrow at x = 0 just clears it)


def riser_c(y): return -0.004 + 0.55 * y * y                    # centre line of the deflexed riser (z)
def riser_d(y): return 0.0245 - 0.22 * y * y                    # its depth front to back
def grip_bulge(y):  # the grip swells out the back below the shelf (the throat where the hand pushes is at y = -0.012)
    if not -0.098 < y < -0.006: return 0.0
    t = (y + 0.006) / -0.092
    return 0.0165 * math.sin(math.pi * t) ** 0.8 * (1 - 0.35 * t)


def limb_dir0(sign): return (math.cos(math.radians(10)) * sign, math.sin(math.radians(10)))


def recurve():
    lam = mat('bw_riser', 0xffffff, rough=0.28, clearcoat=0.9, tex=tex_canvas('bw_riser_t', 64, 64, lam_px))
    grip_m = mat('bw_grip', 0xffffff, rough=0.75, tex=tex_noise('bw_grip_t', 0x4a2614, var=0.22, size=32, speck=0x6a3a1e, speck_p=0.14, seed=33))
    glass = mat('bw_glass', 0x101014, rough=0.14, clearcoat=1.0)
    core = mat('bw_core', 0xffffff, rough=0.35, clearcoat=0.7, tex=tex_wood('bw_core_t', 0xe8c890, 0xb08a50, size=32, seed=34, rings=5))
    tipm = mat('bw_tip', 0xff4fd8, rough=0.18, clearcoat=1.0)
    lab_top = mat('bw_label_top', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_canvas('bw_label_top_t', 96, 11, limb_label('THIS END UP')))
    lab_bot = mat('bw_label_bot', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_canvas('bw_label_bot_t', 112, 11, limb_label('THIS END ALSO UP')))
    brass = mat('bw_brass', 0xe0b050, rough=0.2, metal=1.0)
    strm = mat('bw_string', 0xf4f0e4, rough=0.55)
    serv = mat('bw_serving', 0x1c1c22, rough=0.45)
    pom_p = mat('bw_pom_p', 0xff4fd8, rough=0.95)
    pom_y = mat('bw_pom_y', 0xffe14d, rough=0.95)
    rest_m = mat('bw_rest', 0x18181c, rough=0.4, clearcoat=0.5)
    felt = mat('bw_felt', 0x2a2a30, rough=0.95)
    def medal_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xe0b050)
        px_disc(px, w / 2, h / 2, w / 2 - 1, 0xff4fd8); px_disc(px, w / 2, h / 2, w / 2 - 3, 0x121216)
        text_px(px, 'JF', w // 2 - 5, h // 2 - 3, 1, 0xffe14d)
    medal = mat('bw_medal', 0xffffff, rough=0.25, metal=0.5, tex=tex_canvas('bw_medal_t', 16, 16, medal_px))
    body = []; A = body.append

    # ---------------- riser: deflexed side profile, limb pockets cut into the back at both ends, grip swell
    ys = [Y_END - (2 * Y_END) * i / 44 for i in range(45)]
    def back_z(y):
        z = riser_c(y) + riser_d(y) / 2 + grip_bulge(y)
        if abs(y) > Y_END - 0.031:  # the pocket: the riser's back is cut down to where the limb butt sits
            sgn = 1 if y > 0 else -1
            dy, dz = limb_dir0(sgn)
            k = (Y_END - abs(y)) / 0.031
            pz_front = pivot(sgn)[1] - LIMB_H0 / 2 - (Y_END - abs(y)) * math.tan(math.radians(10))
            z = min(z, pz_front + 0.0002)
        return z
    front = [(riser_c(y) - riser_d(y) / 2, y) for y in ys]
    back = [(back_z(y), y) for y in ys[::-1]]
    riser = side(front + back, W_R, (X_R, 0, 0), lam, bev=0.0018, seg=2, name='bw_riser', angle=50)
    # the sight window on the right: the arrow runs past it, resting on the shelf
    win = side_x([(X_WIN, -0.006), (0.03, -0.006), (0.03, 0.132), (0.013, 0.128), (0.005, 0.12), (0.0, 0.111), (-0.003, 0.1), (X_WIN, 0.088)], 0.12, (0, 0, 0), None, name='bw_win')
    cut(riser, win)
    uv_box(riser, 0.03); A(riser)
    # leather grip over the swell
    gys = [-0.007 - 0.09 * i / 24 for i in range(25)]
    gp = [(riser_c(y) - riser_d(y) / 2 - 0.0007, y) for y in gys] + [(riser_c(y) + riser_d(y) / 2 + grip_bulge(y) + 0.0007, y) for y in gys[::-1]]
    g = side(gp, W_R + 0.0016, (X_R, 0, 0), grip_m, bev=0.0035, seg=3, name='bw_grip', angle=60)
    uv_box(g, 0.02); A(g)
    # stick-on arrow rest + felt strike plate on the window face, brass inserts, the medallion
    A(box((0.0062, 0.0012, 0.009), (X_WIN + 0.0031, -0.0043, riser_c(0) - 0.001), rest_m, bev=0.0004, name='bw_rest'))
    A(box((0.0014, 0.0016, 0.012), (X_WIN + 0.0007, -0.0052, riser_c(0) - 0.001), rest_m, name='bw_rest_base'))
    A(box((0.0006, 0.009, 0.014), (X_WIN + 0.0003, 0.0035, riser_c(0) - 0.001), felt, name='bw_plate'))
    A(cyl(0.0045, 0.002, (X_R, -0.105, riser_c(-0.105) - riser_d(-0.105) / 2 - 0.0006), brass, axis='z', seg=14, name='bw_stab_insert'))
    for y in (0.035, 0.07): A(cyl(0.0022, 0.0012, (X_WIN + 0.0002, y, riser_c(y) + 0.002), brass, axis='x', seg=10, name='bw_sight_insert'))
    md = cyl(0.0062, 0.001, (X_R + W_R / 2 + 0.0004, -0.118, riser_c(-0.118)), medal, axis='x', seg=16, name='bw_medal')
    A(md)
    # limb butts in the pockets (they don't flex) + their brass knurled bolts
    for sgn in (1, -1):
        pv = pivot(sgn); d = limb_dir0(sgn)
        p0 = (0.0, pv[0] - d[0] * 0.031, pv[1] - d[1] * 0.031)
        bpath = [lerp3(p0, (0.0, pv[0], pv[1]), t / 4) for t in range(5)]
        butt = loft(bpath, lambda i, t: limb_section(LIMB_W0, LIMB_H0), m=glass, name='bw_butt', up=(1, 0, 0), smooth_angle=50)
        butt.data.materials.append(core)
        for f in butt.data.polygons:
            if f.index < 4 * LIMB_K and LIMB_SLOTS[f.index % LIMB_K] == 'core': f.material_index = 1
        uv_box(butt, 0.03); A(butt)
        bc = lerp3(p0, (0.0, pv[0], pv[1]), 0.45)
        nrm = (0.0, -d[1] * sgn, d[0] * sgn)  # the butt's belly normal (toward the archer)
        A(knurl(0.0068, 0.006, (0.0, bc[1] + nrm[1] * (LIMB_H0 / 2 + 0.003), bc[2] + nrm[2] * (LIMB_H0 / 2 + 0.003)), brass, nrm, name='bw_bolt'))
        A(cyl(0.0085, 0.0012, (0.0, bc[1] + nrm[1] * (LIMB_H0 / 2 + 0.0004), bc[2] + nrm[2] * (LIMB_H0 / 2 + 0.0004)), brass, axis='z', seg=16, name='bw_washer',
              rot=(math.atan2(nrm[1], nrm[2]) * -1, 0, 0)))

    # ---------------- limbs (they flex about their pivots) with the string's loop + the bit lying on the recurve
    nock_z = 0.122
    nodes = []; tips = []; limbs = []
    for sgn, lab, nm in ((1, lab_top, 'bw_limb_top_wzB'), (-1, lab_bot, 'bw_limb_bot_wzB')):
        pv = pivot(sgn)
        path = limb_path(pv, 0.27, 10, 4, 0.7, -55, sign=sgn)
        n_s = len(path); K = LIMB_K
        wf = lambda t: LIMB_W0 - 0.0125 * t ** 0.9
        hf = lambda t: LIMB_H0 - 0.0034 * t
        lb = loft(path, lambda i, t: limb_section(wf(t), hf(t)), m=glass, name=nm, up=(1, 0, 0), smooth_angle=40)
        lb.data.materials.append(core); lb.data.materials.append(lab)
        uv_box(lb, 0.03)
        belly = -1 if sgn > 0 else 1   # which side of the section (b) faces the archer
        bslot = 'bot' if sgn > 0 else 'top'
        s0, s1 = 3, 3 + int(n_s * 0.42)
        uvl = lb.data.uv_layers.active.data
        me = lb.data
        for f in me.polygons:
            if f.index >= (n_s - 1) * K: continue
            st, sl = divmod(f.index, K)
            if LIMB_SLOTS[sl] == 'core': f.material_index = 1
            if s0 <= st < s1 and LIMB_SLOTS[sl] == bslot:
                f.material_index = 2
                for li in f.loop_indices:
                    vi = me.loops[li].vertex_index; i, j = divmod(vi, K)
                    v = me.vertices[vi].co
                    u = (i - s0) / (s1 - s0)
                    if sgn < 0: u = 1 - u
                    tt_ = i / (n_s - 1)
                    w = wf(tt_) - 2 * 0.28 * hf(tt_)
                    uvl[li].uv = (u, 0.5 - v.x / w)
        parts = [lb]
        # candy tip overlay with the string grooves, the string loop round it, the string lying along the recurve
        t_ov = n_s - 6
        ov = loft(path[t_ov:] + [tuple(Vector(path[-1]) + (Vector(path[-1]) - Vector(path[-2])) * 2.2)],
                  lambda i, t: section((wf(1.0) + 0.0016) * (1 - 0.55 * t ** 3), (hf(1.0) + 0.0026) * (1 - 0.45 * t ** 3), 16),
                  m=tipm, name='bw_overlay', up=(1, 0, 0), close=(False, True), smooth_angle=50)
        parts.append(ov)
        il = n_s - 3
        tt, BB = frame(path, il)
        c = Vector(path[il])
        loop = []
        for a, b in section(wf(1.0) + 0.0042, hf(1.0) + 0.0048, 12, 0.6):
            loop.append(tuple(c + Vector((1, 0, 0)) * a + BB * b))
        parts.append(tube(loop, R_STR * 1.05, serv, seg=6, name='bw_loop', closed=True))
        # where the string leaves the limb: the belly point the line from the nock just touches
        nock = Vector((0, 0, nock_z))
        best, bi = -9, None
        for i in range(n_s // 2, n_s - 2):
            t_, B_ = frame(path, i)
            p = Vector(path[i]) + B_ * belly * (hf(i / (n_s - 1)) / 2 + R_STR)
            ang = math.atan2(p.z - nock.z, abs(p.y - nock.y))
            if ang > best: best, bi = ang, i
        lay = []
        for i in range(bi, il + 1):
            t_, B_ = frame(path, i)
            lay.append(tuple(Vector(path[i]) + B_ * belly * (hf(i / (n_s - 1)) / 2 + R_STR * 0.9)))
        parts.append(sweep(lay, R_STR, serv, seg=6, name='bw_lay'))
        tip = lay[0]
        tips.append([0.0, round(tip[1], 5), round(tip[2], 5)])
        limbs.append(part(parts, nm, pivot=(0.0, pv[0], pv[1])))

    # ---------------- the string: two halves from where it leaves each limb to the nock (the game bends them)
    halves = []
    nockp = (0.0, 0.0, nock_z)
    for k, (T, nm) in enumerate(zip(tips, ('bw_string_top_wzN', 'bw_string_bot_wzN'))):
        T = tuple(T); hp = []
        hp.append(string_rod(T, nockp, R_STR, strm, 'bw_str'))
        hp.append(string_rod(lerp3(nockp, T, 0.11), nockp, R_STR * 1.3, serv, 'bw_center_serving'))
        hp.append(string_rod(T, lerp3(T, nockp, 0.06), R_STR * 1.25, serv, 'bw_end_serving'))
        hp.append(pom(0.0085, lerp3(T, nockp, 0.2), pom_p if k == 0 else pom_y, 41 + k))
        if k == 0:  # brass nock set, just above the arrow
            hp.append(cyl(R_STR * 2.2, 0.0045, lerp3(nockp, T, 0.0115), brass, axis='y', seg=10, name='bw_nockset'))
        halves.append(part(hp, nm))

    # ---------------- the nocked arrow (its node sits at the origin: the game slides it back as you draw)
    am = arrow_mats('bw_ar', 0xd8a868, 0xa8743c, 0xff4fd8, 0xff4fd8, 0xffe14d, 'SORRY', (0xf6f4ee, 0xe0202a, 0xff4fd8))
    ab, ah = arrow_parts('bw_ar', nock_z + 0.004, 0.40, ARROW_R, am, 0.05, 0.0092, 0.06, 0.034, 0.0105, cock_dir=0.0, nock_len=0.011)
    arrow = part(ab, 'bow_arrow_wzA', pivot=(0, 0, 0))
    head = part(ah, 'bow_arrowtip_wzN', pivot=(0, 0, nock_z + 0.004 - 0.40 + 0.017))
    head.parent = arrow

    uvp = md.matrix_world.translation
    apply_mods(md); uv_planar(md, (uvp.x, uvp.z, -uvp.y), 0.0124, 'x')
    WZ = {'bw_riser': 'a', 'bw_grip': 'a', 'bw_glass': 'b', 'bw_core': 'b', 'bw_brass': 'b'}
    bodies = zone_join(body, 'bow_body', WZ, default='n')
    meta = {'kind': 'weapon', 'id': 'bow', 'paint': ['bw_riser'], 'muzzle': [0, 0, -0.6], 'hatAt': [[X_R, Y_END + 0.004, riser_c(Y_END) - 0.003], 0.07],
            'bow': {'string': ['bw_string_top_wzN', 'bw_string_bot_wzN'], 'tips': tips, 'nock': [0, 0, nock_z],
                    'limbs': ['bw_limb_top_wzB', 'bw_limb_bot_wzB'], 'flex': 0.1, 'draw': 0.16, 'arrow': 'bow_arrow_wzA', 'arrowTip': 'bow_arrowtip_wzN'}}
    print('JF_BOW tips', tips, 'nock', nock_z)
    return finish('w_bow', bodies + limbs + halves + [arrow], meta)


def pivot(sgn):
    """where a limb leaves the riser (y, z): on the riser's end, the limb butt's centre line"""
    y = sgn * Y_END
    return (y, riser_c(y) + riser_d(y) / 2 - LIMB_H0 / 2 + 0.0006)


# ------------------------------------------------------------ the flying arrow: 0.9 m, centred, nose to -z
def flying():
    am = arrow_mats('pa', 0xd8a868, 0xa8743c, 0xff4fd8, 0xff4fd8, 0xffe14d, 'SORRY', (0xf6f4ee, 0xe0202a, 0xff4fd8))
    ab, ah = arrow_parts('pa', 0.45, 0.98, 0.0105, am, 0.13, 0.03, 0.12, 0.1, 0.034, cock_dir=0.0, nock_len=0.03)
    WZ = {'pa_shaft': 'a', 'pa_nock': 'n', 'pa_feather': 'n', 'pa_cock': 'n', 'pa_wrap': 'n'}
    bodies = zone_join(ab, 'arrow_body', WZ, default='n')
    head = part(ah, 'arrowhead_wzN', pivot=(0, 0, 0.45 - 0.98 + 0.05))
    return finish('pj_bow', bodies + [head], {'kind': 'proj', 'id': 'bow', 'tip': 'arrowhead_wzN'})


main_multi(lambda: [(recurve(), 'w_bow'), (flying(), 'pj_bow')], exposure=-0.3)
