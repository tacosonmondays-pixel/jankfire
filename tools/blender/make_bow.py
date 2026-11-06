# Bow, the Compound skin and the flying arrow.
# Bow: a 62" takedown recurve (23" laminated hardwood riser with a deflexed profile, a leather grip, an arrow shelf
# with a stick-on rest, limb pockets with brass knurled bolts, short glass-and-maple limbs with candy tip overlays,
# a Dacron string with servings, a brass nock set and yarn puff silencers), x0.5 so it's the code bow's 0.8 m.
# Cross-sections are ~1.7x real so it reads at that size. A nocked cedar arrow (shield-cut feathers, a printed
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


def limb_section(w, h, ef=0.22):
    """a limb's section: glass faces (top = the side vector's + side, bot = - side), rounded corners and a maple core
    stripe up each edge (ef x the thickness each side of the middle). 22 points; LIMB_SLOTS says what each face slot is."""
    rc = (0.5 - ef) * h; e = ef * h; fx = w / 2 - rc
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


def limb_label(text, arrow=True, edge=0xff4fd8):
    def draw(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0x121216)
        px[0, :] = px[-1, :] = hexrgb(edge)
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
LIMB_H0 = 0.0095        # limb thickness at the pocket
LIMB_W0 = 0.028         # limb width at the pocket
X_R = -0.004            # riser centre (x): the riser sits a hair left, the arrow passes on its right
W_R = 0.027             # riser width
X_WIN = -0.0045         # sight window face (the arrow at x = 0 just clears it)


def riser_c(y): return -0.004 + 0.55 * y * y                    # centre line of the deflexed riser (z)
def riser_d(y): return 0.034 - 0.38 * y * y                     # its depth front to back
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
    def rring(w, b0, b1, k=20, ex=0.36):  # rounded rectangle: a across x, b from b0 to b1 (front to back)
        out = []
        for j in range(k):
            th = 2 * math.pi * j / k; c_, s_ = math.cos(th), math.sin(th)
            out.append((w / 2 * math.copysign(abs(c_) ** ex, c_), (b0 + b1) / 2 + (b1 - b0) / 2 * math.copysign(abs(s_) ** ex, s_)))
        return out
    rpath = [(X_R, y, riser_c(y)) for y in ys]   # top to bottom: the loft's side vector is +z
    riser = loft(rpath, lambda i, t: rring(W_R, -riser_d(ys[i]) / 2, back_z(ys[i]) - riser_c(ys[i])), m=lam, name='bw_riser', up=(1, 0, 0), smooth_angle=50)
    # the sight window on the right: the arrow runs past it, resting on the shelf
    win = side_x([(X_WIN, -0.006), (0.03, -0.006), (0.03, 0.132), (0.013, 0.128), (0.005, 0.12), (0.0, 0.111), (-0.003, 0.1), (X_WIN, 0.088)], 0.12, (0, 0, 0), None, name='bw_win')
    cut(riser, win)
    bevel(riser, 0.0012, 2, 50)
    uv_box(riser, 0.03); A(riser)
    # leather grip: a sleeve over the swell
    gys = [-0.0055 - 0.095 * i / 15 for i in range(16)]
    gpath = [(X_R, y, riser_c(y)) for y in gys]
    g = loft(gpath, lambda i, t: rring(W_R + 0.0026, -riser_d(gys[i]) / 2 - 0.0009, back_z(gys[i]) - riser_c(gys[i]) + 0.0009, 16, 0.55), m=grip_m, name='bw_grip', up=(1, 0, 0), smooth_angle=60)
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
    tips = []; limbs = []
    for sgn, lab, nm in ((1, lab_top, 'bw_limb_top_wzB'), (-1, lab_bot, 'bw_limb_bot_wzB')):
        pv = pivot(sgn)
        path = limb_path(pv, 0.27, 10, 4, 0.7, -55, sign=sgn, n=28)
        n_s = len(path); K = LIMB_K
        wf = lambda t: LIMB_W0 - 0.014 * t ** 0.9
        hf = lambda t: LIMB_H0 - 0.004 * t
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
                    w = wf(tt_) - 2 * (0.5 - 0.22) * hf(tt_)
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


# ------------------------------------------------------------ the compound (skin bow_compound)
# A 32" axle-to-axle single-riser compound with split limbs and twin cams, 6.5" brace, x0.9 so it's the code compound's
# size: a machined black riser (truss cutouts, the window section offset left of the arrow, a wood grip), green
# anodized limb pockets, short split limbs past 45 degrees, chrome cams with green modules, two buss cables through a
# slide on the cable guard, a string stop, a whisker-biscuit rest, a 3-pin fibre sight (the pins glow), a stabilizer
# with a damper, a peep in the string, a D-loop on the nock, a carbon arrow with a lighted nock.
# Made fun: the limbs say COMPOUND and INTEREST, the sight's yardage tape says 20 30 YOLO.
CY = 0.366               # cam axles
CZ = 0.131
CR = 0.034               # string track radius: the string leaves the cam's back at z = CZ + CR, straight down to the nock
C_NOCK = CZ + CR
CPZ = 0.004              # limb pivots (z) at the riser ends
CPY = 0.255
C_FLEX = 0.06


def c_riser_c(y): return -0.012 + 0.22 * y * y
def c_riser_d(y): return 0.046 - 0.12 * y * y
def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t)
def c_xoff(y):  # the riser jogs left of the arrow through the sight window, back to the middle at the pockets
    win = smoothstep(-0.03, 0.0, y) * (1 - smoothstep(0.12, 0.17, y))
    lo = smoothstep(-0.17, -0.12, y) * (1 - smoothstep(-0.03, 0.0, y))
    return -0.027 * win - 0.012 * lo


def cam_outline(cy, cz, sgn, n=28):
    """an eccentric cam round its axle (y, z): the string track circle and the cable lobe, as one (z, y) outline"""
    circles = [((cy + sgn * 0.003, cz + 0.0015), CR + 0.0022), ((cy - sgn * 0.012, cz - 0.009), 0.027)]
    out = []
    for k in range(n):
        th = 2 * math.pi * k / n
        dy, dz = math.sin(th), math.cos(th)
        best = 0.0
        for (yc, zc), r in circles:
            oy, oz = yc - cy, zc - cz
            b = oy * dy + oz * dz; c = oy * oy + oz * oz - r * r
            disc = b * b - c
            if disc >= 0: best = max(best, b + math.sqrt(disc))
        out.append((cz + dz * best, cy + dy * best))
    return out


def compound():
    blk = mat('bc_riser', 0x18181e, rough=0.22, metal=0.6, clearcoat=0.6, tex=tex_noise('bc_riser_t', 0x1a1a20, var=0.08, size=16, seed=51))
    green = mat('bc_green', 0x5cff2a, rough=0.2, metal=0.5, clearcoat=0.8)
    wood = mat('bc_grip', 0xffffff, rough=0.4, clearcoat=0.6, tex=tex_wood('bc_grip_t', 0x7a3a1c, 0x3a1808, size=32, seed=52, rings=6))
    glass = mat('bc_limb', 0x0e0e12, rough=0.16, clearcoat=1.0)
    chrome = mat('bc_chrome', 0xd8dde6, rough=0.12, metal=1.0)
    steel = mat('bc_steel', 0x5a5e66, rough=0.3, metal=0.9)
    dark = mat('bc_dark', 0x0a0a0c, rough=0.5)
    cable_m = mat('bc_cable', 0x46d41e, rough=0.45, clearcoat=0.4)
    strm = mat('bc_string', 0x3ac4e8, rough=0.45, clearcoat=0.4)
    serv = mat('bc_serving', 0x101012, rough=0.4)
    rubber = mat('bc_rubber', 0x5cff2a, rough=0.85)
    carbon = mat('bc_carbon', 0xffffff, rough=0.3, clearcoat=0.7, tex=tex_stripes('bc_carbon_t', 0x1a1a1e, 0x2e2e34, size=8, width=2, diag=True))
    bristle = mat('bc_bristle', 0x111114, rough=1.0, tex=tex_noise('bc_bristle_t', 0x141418, var=0.4, size=16, speck=0x3a3a40, speck_p=0.3, seed=53))
    orange = mat('bc_dloop', 0xff7a1a, rough=0.6)
    pins = [mat('bc_pin_g', 0x7dff4f, emit=0x7dff4f, strength=4.0), mat('bc_pin_y', 0xffe14d, emit=0xffe14d, strength=4.0), mat('bc_pin_r', 0xff3030, emit=0xff3030, strength=4.0)]
    vial = mat('bc_vial', 0x9affd0, rough=0.05, alpha=0.5)
    bub = mat('bc_bubble', 0x7dff4f, emit=0x7dff4f, strength=1.5)
    def blade_label(word):  # the word in the middle of a long thin strip (the blade's face is 0.16 x 0.009 m), dashes either side
        def draw(px):
            h, w = px.shape[:2]
            px[:] = hexrgb(0x121216); px[0, :] = px[-1, :] = hexrgb(0x5cff2a)
            tw = len(word) * 6 - 1
            text_px(px, word, (w - tw) // 2, 2, 1, 0xf6f4ee)
            for x in list(range(8, (w - tw) // 2 - 6, 8)) + list(range((w + tw) // 2 + 6, w - 8, 8)): px[5, x:x + 4] = hexrgb(0x5cff2a)
        return draw
    lab_top = mat('bc_label_top', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_canvas('bc_label_top_t', 200, 11, blade_label('COMPOUND')))
    lab_bot = mat('bc_label_bot', 0xffffff, rough=0.2, clearcoat=1.0, tex=tex_canvas('bc_label_bot_t', 200, 11, blade_label('INTEREST')))
    def tape_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xf6f4ee)
        for k, (t, c) in enumerate((('20', 0x111111), ('30', 0x111111), ('YOLO', 0xe0202a))):
            text_px(px, t, 2, 2 + k * 10, 1, c)
    tape = mat('bc_tape', 0xffffff, rough=0.4, tex=tex_canvas('bc_tape_t', 28, 32, tape_px))
    body = []; A = body.append

    # ---------------- riser: a loft through the jog, truss cutouts, green pockets, wood grip
    ys = [0.268 - 0.536 * i / 40 for i in range(41)]
    def rr(w, b0, b1, k=16, ex=0.34):
        out = []
        for j in range(k):
            th = 2 * math.pi * j / k; c_, s_ = math.cos(th), math.sin(th)
            out.append((w / 2 * math.copysign(abs(c_) ** ex, c_), (b0 + b1) / 2 + (b1 - b0) / 2 * math.copysign(abs(s_) ** ex, s_)))
        return out
    def cw(y): return 0.021 + 0.008 * smoothstep(0.2, 0.25, abs(y))
    rpath = [(c_xoff(y), y, c_riser_c(y)) for y in ys]
    riser = loft(rpath, lambda i, t: rr(cw(ys[i]), -c_riser_d(ys[i]) / 2, c_riser_d(ys[i]) / 2), m=blk, name='bc_riser', up=(1, 0, 0), smooth_angle=45)
    for sg in (1, -1):  # truss cutouts through the beams: a long teardrop and a small one each end
        for (ya, yb, dz, kz) in ((0.135, 0.19, -0.002, 0.29), (0.198, 0.232, 0.001, 0.25)):
            ym = sg * (ya + yb) / 2; hz = kz * c_riser_d(ym)
            hole = cyl(0.5, 0.2, (c_xoff(ym), ym, c_riser_c(ym) + dz), None, axis='x', seg=16)
            hole.scale = (1.0, hz / 0.5, (yb - ya) / 2 / 0.5)
            cut(riser, hole)
    bevel(riser, 0.0012, 1, 70)
    uv_box(riser, 0.04); A(riser)
    # wood grip under the arrow (the riser's middle runs through it)
    gys = [-0.006 - 0.1 * i / 15 for i in range(16)]
    def gb(y):
        t = (y + 0.006) / -0.1
        return 0.019 * math.sin(math.pi * t) ** 0.7 * (1 - 0.3 * t)
    gpath = [(-0.002, y, c_riser_c(y)) for y in gys]
    g = loft(gpath, lambda i, t: rr(0.028, -c_riser_d(gys[i]) / 2 - 0.001, c_riser_d(gys[i]) / 2 + gb(gys[i]), 16, 0.55), m=wood, name='bc_grip', up=(1, 0, 0), smooth_angle=60)
    uv_box(g, 0.03); A(g)
    # limb pockets (green), their bolts
    for sg in (1, -1):
        py = sg * 0.258
        A(box((0.032, 0.03, 0.05), (0, py, c_riser_c(py) + 0.006), green, bev=0.004, seg=2, rot=(-sg * 0.5, 0, 0), name='bc_pocket'))
        A(cyl(0.0055, 0.008, (0, sg * 0.243, c_riser_c(0.243) + 0.022), steel, axis='z', seg=6, rot=(-sg * 0.35, 0, 0), name='bc_limbbolt'))
    # string stop: a rod off the back with a green rubber bumper just in front of the string
    A(rod((-0.004, -0.115, c_riser_c(-0.115) + 0.012), (-0.004, -0.115, C_NOCK - 0.018), 0.0035, carbon, seg=10, name='bc_stop_rod'))
    A(cyl(0.009, 0.012, (-0.004, -0.115, C_NOCK - 0.009), rubber, axis='z', seg=14, bev=0.002, name='bc_stop'))
    # cable guard rod + slide
    gz0 = c_riser_c(0.05) + c_riser_d(0.05) / 2
    A(rod((c_xoff(0.05), 0.05, gz0 - 0.004), (-0.016, 0.05, 0.12), 0.0032, carbon, seg=10, name='bc_guard'))
    A(box((0.008, 0.014, 0.012), (-0.014, 0.05, 0.108), dark, bev=0.002, name='bc_slide'))
    # whisker biscuit rest round the arrow
    A(lathe([(0.0125, -0.009), (0.0165, -0.009), (0.0165, -0.002), (0.0125, -0.002), (0.0125, -0.009)], (0, 0, 0), green, seg=24, name='bc_biscuit_ring', cap=False))
    bis = lathe([(0.0037, -0.0075), (0.0126, -0.008), (0.0126, -0.0035), (0.0037, -0.004), (0.0037, -0.0075)], (0, 0, 0), bristle, seg=20, name='bc_bristles', cap=False)
    jitter(bis, 0.0006, 7); uv_box(bis, 0.01); A(bis)
    A(box((0.006, 0.01, 0.006), (-0.018, -0.002, -0.0055), dark, bev=0.001, name='bc_biscuit_arm'))
    # sight: bracket on the window face, an extension bar, the round pin guard, 3 glowing pins + their fibres, a level
    sx0 = c_xoff(0.07) + 0.0095
    A(box((0.006, 0.04, 0.03), (sx0 + 0.003, 0.072, c_riser_c(0.07) - 0.004), dark, bev=0.002, name='bc_sight_plate'))
    A(box((0.009, 0.012, 0.075), (sx0 + 0.009, 0.074, c_riser_c(0.07) - 0.046), blk, bev=0.002, name='bc_sight_bar'))
    SC = (0.0, 0.078, -0.098)
    A(lathe([(0.0205, SC[2] + 0.007), (0.0255, SC[2] + 0.007), (0.0255, SC[2] - 0.007), (0.0205, SC[2] - 0.007), (0.0205, SC[2] + 0.007)], (SC[0], SC[1], 0), blk, seg=28, name='bc_pinguard', cap=False))
    A(box((0.012, 0.03, 0.016), (SC[0] + 0.027, SC[1], SC[2]), blk, bev=0.002, name='bc_pinblock'))
    tp = box((0.0008, 0.024, 0.012), (SC[0] + 0.0334, SC[1], SC[2] + 0.003), tape, name='bc_tape'); A(tp)
    for k, (dy, pm) in enumerate(((0.008, pins[0]), (0.0, pins[1]), (-0.008, pins[2]))):
        A(rod((SC[0] + 0.0215, SC[1] + dy, SC[2]), (SC[0] + 0.002, SC[1] + dy, SC[2]), 0.0009, steel, seg=6, name='bc_pin'))
        A(ball(0.0019, (SC[0] + 0.0015, SC[1] + dy, SC[2]), pm, seg=8, rings=6, name='bc_pinhead'))
        coil = [(SC[0] + 0.0268 * math.cos(a), SC[1] + 0.0268 * math.sin(a), SC[2] - 0.0045 + 0.0045 * k + 0.0008 * math.sin(3 * a)) for a in [math.radians(-60 + i * 22) for i in range(12)]]
        A(tube(coil, 0.0011, pm, seg=4, name='bc_fibre'))
    A(cyl(0.0025, 0.012, (SC[0], SC[1] - 0.0165, SC[2]), vial, axis='x', seg=10, name='bc_vial'))
    A(ball(0.0013, (SC[0] + 0.001, SC[1] - 0.0158, SC[2]), bub, seg=8, rings=6, name='bc_bub'))
    # stabilizer + damper + weights, and a wrist sling off its mount
    sy, sz0 = -0.04, c_riser_c(-0.04) - c_riser_d(-0.04) / 2
    A(cyl(0.0085, 0.012, (-0.002, sy, sz0 - 0.006), blk, axis='z', seg=16, bev=0.0015, name='bc_stab_mount'))
    A(cyl(0.0072, 0.17, (-0.002, sy, sz0 - 0.1), carbon, axis='z', seg=14, name='bc_stab'))
    A(lathe([(0.008, sz0 - 0.014), (0.011, sz0 - 0.02), (0.011, sz0 - 0.03), (0.008, sz0 - 0.036)], (-0.002, sy, 0), rubber, seg=16, name='bc_damper'))
    for k in range(2): A(cyl(0.0125, 0.009, (-0.002, sy, sz0 - 0.19 - k * 0.0095), chrome, axis='z', seg=16, bev=0.0012, name='bc_weight'))
    sling = [(-0.002 + 0.008 * math.sin(a), sy - 0.012 - 0.045 * (1 - math.cos(a)) / 2, sz0 - 0.014 + 0.012 * math.sin(a * 0.5)) for a in [i * 2 * math.pi / 16 for i in range(17)]]
    A(tube(sling, 0.0022, rubber, seg=6, name='bc_sling'))

    # ---------------- limbs: split blades to the axles, the cams and their string track (they flex with the limb)
    tips = []; limbs = []
    for sgn, lab, nm in ((1, lab_top, 'bc_limb_top_wzB'), (-1, lab_bot, 'bc_limb_bot_wzB')):
        pv = (sgn * CPY, c_riser_c(CPY) + CPZ)
        ax = (sgn * CY, CZ)
        d = Vector((0, ax[0] - pv[0], ax[1] - pv[1])); L = d.length; d.normalize()
        parts = []
        for bx in (-0.0105, 0.0105):
            p0 = Vector((bx, pv[0], pv[1])) - d * 0.035
            p1 = Vector((bx, ax[0], ax[1])) + d * 0.014
            path = [tuple(p0 + (p1 - p0) * (k / 8) + Vector((0, 0, 0.004 * math.sin(math.pi * k / 8)))) for k in range(9)]
            n_s = len(path)
            wf = lambda t: 0.0095 - 0.0015 * t
            hf = lambda t: 0.0125 - 0.004 * t
            lb = loft(path, lambda i, t: limb_section(wf(t), hf(t), 0.36), m=glass, name='bc_blade', up=(1, 0, 0), smooth_angle=40)
            lb.data.materials.append(green); lb.data.materials.append(lab)
            uv_box(lb, 0.03)
            # the label runs along each blade's outer face (its edge slot): reads from that side, upright
            oslot = 0 if bx > 0 else 11
            s0, s1 = 1, 7
            me = lb.data; uvl = me.uv_layers.active.data
            for f in me.polygons:
                if f.index >= (n_s - 1) * LIMB_K: continue
                st, sl = divmod(f.index, LIMB_K)
                if sl == oslot and s0 <= st < s1:
                    f.material_index = 2
                    for li in f.loop_indices:
                        vi = me.loops[li].vertex_index; i, j = divmod(vi, LIMB_K)
                        fr = (i - s0) / (s1 - s0)
                        u = 1 - fr if bx > 0 else fr
                        v = {0: 0.0, 1: 1.0, 11: 1.0, 12: 0.0}[j]
                        uvl[li].uv = (u, v)
            parts.append(lb)
        # cam: two chrome flanges + the string track between them, lightening holes, a green module, the axle
        outl = cam_outline(ax[0], ax[1], sgn)
        holes = []
        for (hy, hz, hr) in ((0.012, 0.006, 0.007), (-0.01, 0.011, 0.006), (-0.004, -0.014, 0.0055)):
            holes.append([(ax[1] + hz + hr * math.cos(a), ax[0] + sgn * hy + hr * math.sin(a)) for a in [k * 2 * math.pi / 10 for k in range(10)]])
        for fx in (-0.0042, 0.0042):
            parts.append(side(outl, 0.0026, (fx, 0, 0), chrome, name='bc_cam', holes=holes))
        track = [(ax[1] + (z - ax[1]) * 0.93, ax[0] + (y - ax[0]) * 0.93) for z, y in outl]
        parts.append(side(track, 0.0064, (0, 0, 0), steel, name='bc_track', holes=holes))
        parts.append(side([(ax[1] - 0.02, ax[0] - sgn * 0.004), (ax[1] - 0.006, ax[0] - sgn * 0.018), (ax[1] + 0.004, ax[0] - sgn * 0.024), (ax[1] - 0.012, ax[0] - sgn * 0.03), (ax[1] - 0.026, ax[0] - sgn * 0.016)],
                          0.0098, (0, 0, 0), green, bev=0.001, name='bc_module'))
        parts.append(cyl(0.0032, 0.03, (0, ax[0], ax[1]), steel, axis='x', seg=10, name='bc_axle'))
        for fx in (-0.0152, 0.0152): parts.append(cyl(0.0048, 0.0016, (fx, ax[0], ax[1]), chrome, axis='x', seg=12, name='bc_clip'))
        # the string wraps the back of the track from where it leaves (straight down to the nock) over the top
        arcp = [(0, ax[0] + sgn * (CR) * math.sin(a), ax[1] + CR * math.cos(a)) for a in [k * math.radians(130) / 10 for k in range(11)]]
        parts.append(tube(arcp, R_STR * 1.2, strm, seg=6, name='bc_wrap'))
        # cables: from the cam's cable lobe down to the junction at the pivot height (the rest is on the riser)
        for cx in (-0.0035, 0.0035):
            c0 = (cx, ax[0] - sgn * 0.022, ax[1] - 0.018)
            c1 = (cx * 0.5 - 0.004, pv[0] - sgn * 0.002, 0.11)
            parts.append(rod(c0, c1, 0.0013, cable_m, seg=6, name='bc_cable'))
        tips.append([0.0, round(sgn * CY, 5), round(C_NOCK, 5)])
        limbs.append(part(parts, nm, pivot=(0.0, pv[0], pv[1])))
    # the middle of the cables, through the slide (static)
    for cx in (-0.0035, 0.0035):
        top = (cx * 0.5 - 0.004, CPY - 0.002, 0.11); bot = (cx * 0.5 - 0.004, -CPY + 0.002, 0.11)
        sl = (-0.014 + cx * 0.4, 0.05, 0.108)
        A(rod(top, sl, 0.0013, cable_m, seg=6, name='bc_cable_mid'))
        A(rod(sl, bot, 0.0013, cable_m, seg=6, name='bc_cable_mid'))

    # ---------------- string halves: cam to nock, a peep in the top one
    halves = []
    nockp = (0.0, 0.0, C_NOCK)
    for k, (T, nm) in enumerate(zip(tips, ('bc_string_top_wzN', 'bc_string_bot_wzN'))):
        T = tuple(T); hp = []
        if k == 0:
            py = 0.078; pf = py / CY
            pc = lerp3(nockp, T, pf)
            hp.append(rod(T, (0, pc[1] + 0.0065, C_NOCK), R_STR, strm, name='bc_str'))
            hp.append(rod((0, pc[1] - 0.0065, C_NOCK), nockp, R_STR, strm, name='bc_str'))
            for sx in (-1, 1): hp.append(tube([(0, pc[1] + 0.0065, C_NOCK), (sx * 0.0052, pc[1] + 0.003, C_NOCK), (sx * 0.0052, pc[1] - 0.003, C_NOCK), (0, pc[1] - 0.0065, C_NOCK)], R_STR * 0.75, strm, seg=4, name='bc_strand'))
            pe = lathe([(0.0026, C_NOCK - 0.0022), (0.0048, C_NOCK - 0.0022), (0.0052, C_NOCK), (0.0048, C_NOCK + 0.0022), (0.0026, C_NOCK + 0.0022), (0.0026, C_NOCK - 0.0022)], (0, pc[1], 0), green, seg=16, name='bc_peep', cap=False)
            hp.append(pe)
        else:
            hp.append(rod(T, nockp, R_STR, strm, name='bc_str'))
        hp.append(rod(lerp3(nockp, T, 0.07), nockp, R_STR * 1.35, serv, name='bc_center_serving'))
        halves.append(part(hp, nm))

    # ---------------- the arrow: carbon, cyan vanes, a lighted nock, a D-loop round the nock (moves with it)
    am = arrow_mats('bc_ar', 0x1a1a1e, 0x2e2e34, 0x4fd8ff, 0x4fd8ff, 0xf6f4ee, 'JANK', (0x1a1a1e, 0x4fd8ff, 0x4fd8ff), carbon=True)
    am = (am[0], mat('bc_ar_lit', 0x4fd8ff, rough=0.2, emit=0x4fd8ff, strength=2.5)) + am[2:]
    ab, ah = arrow_parts('bc_ar', C_NOCK + 0.004, 0.42, ARROW_R * 0.92, am, 0.042, 0.0075, 0.05, 0.03, 0.0095, cock_dir=0.0, nock_len=0.011)
    dl = [(0, 0.0065, C_NOCK), (0, 0.0055, C_NOCK + 0.011), (0, 0.0, C_NOCK + 0.016), (0, -0.0055, C_NOCK + 0.011), (0, -0.0065, C_NOCK)]
    ab.append(tube(dl, 0.0014, orange, seg=6, name='bc_dloop'))
    for yy in (0.0065, -0.0065): ab.append(ball(0.0024, (0, yy, C_NOCK), orange, seg=8, rings=6, name='bc_knot'))
    arrow = part(ab, 'bowc_arrow_wzA', pivot=(0, 0, 0))
    head = part(ah, 'bowc_arrowtip_wzN', pivot=(0, 0, C_NOCK + 0.004 - 0.42 + 0.015))
    head.parent = arrow

    apply_mods(tp); uv_planar(tp, (SC[0] + 0.0334, SC[1], SC[2] + 0.003), (0.012, 0.024), 'x')
    WZ = {'bc_riser': 'a', 'bc_grip': 'a', 'bc_green': 'b', 'bc_steel': 'b', 'bc_chrome': 'b', 'bc_limb': 'b'}
    bodies = zone_join(body, 'bowc_body', WZ, default='n')
    meta = {'kind': 'weapon', 'id': 'bow', 'skin': 'bow_compound', 'paint': ['bc_riser'], 'muzzle': [0, 0, -0.6],
            'hatAt': [[0, 0.258 + 0.02, c_riser_c(0.258) + 0.004], 0.07],
            'bow': {'string': ['bc_string_top_wzN', 'bc_string_bot_wzN'], 'tips': tips, 'nock': [0, 0, C_NOCK],
                    'limbs': ['bc_limb_top_wzB', 'bc_limb_bot_wzB'], 'flex': C_FLEX, 'draw': 0.16, 'arrow': 'bowc_arrow_wzA', 'arrowTip': 'bowc_arrowtip_wzN'}}
    print('JF_BOWC tips', tips, 'nock', C_NOCK)
    return finish('w_bow_compound', bodies + limbs + halves + [arrow], meta)


# ------------------------------------------------------------ the flying arrow: 0.9 m, centred, nose to -z
def flying():
    am = arrow_mats('pa', 0xd8a868, 0xa8743c, 0xff4fd8, 0xff4fd8, 0xffe14d, 'SORRY', (0xf6f4ee, 0xe0202a, 0xff4fd8))
    ab, ah = arrow_parts('pa', 0.45, 0.98, 0.0105, am, 0.13, 0.03, 0.12, 0.1, 0.034, cock_dir=0.0, nock_len=0.03)
    WZ = {'pa_shaft': 'a', 'pa_nock': 'n', 'pa_feather': 'n', 'pa_cock': 'n', 'pa_wrap': 'n'}
    bodies = zone_join(ab, 'arrow_body', WZ, default='n')
    head = part(ah, 'arrowhead_wzN', pivot=(0, 0, 0.45 - 0.98 + 0.05))
    return finish('pj_bow', bodies + [head], {'kind': 'proj', 'id': 'bow', 'tip': 'arrowhead_wzN'})


main_multi(lambda: [(recurve(), 'w_bow'), (compound(), 'w_bow_compound'), (flying(), 'pj_bow')], exposure=-0.8)
