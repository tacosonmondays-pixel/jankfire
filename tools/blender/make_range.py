# JANKFIRE map pass, Range (Training): the firing line. Map props the game fits onto their boxes (shared/map.js range(),
# the props lane: make_market.py's flow, its helpers imported). Each is built at its box version's size, long along x,
# y 0 = the ground, the shooters' side +z; meta.box = the box version's extent. lod0 under the root, lod1 under `lod1`.
#   p_rangebench  the 40 m shooting bench you spawn behind (one 40 x 0.8 x 1 box): a plank counter on a skirt of
#                 safety-yellow boards, magenta lane posts every 5 m, red lane plates 1-8 on the shooters' side, a
#                 hazard kick plate; on top, per lane: a green rubber mat, spent brass, ear defenders, ammo cans, a mug
#   p_sandbags    one 3 m section of the sandbag wall in front of it (3 x 0.8 x 1): four courses of tied hessian bags,
#                 two deep, offset like real ones, the top course stepped in; a pink one says SAND (PROBABLY)
#   p_rangemark   the distance boards down the left of the lanes (4 x 1.2 x 0.4): posts, white boards in a red frame,
#                 the distance from the bench in big black numbers on both faces. variants v15 / v30 / v55 / v105
# run: blender52 -b --python tools/blender/make_range.py -- [--only=rangebench,sandbags] [--no-sheet] [--no-export] [--qa]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib
from lib import _link
import make_market as MK
from make_market import Atlas, paint_wood, paint_noise, uv_trim, uv_fit, poly_obj, outward, sweep, opt, V3, TAU

ONLY = [s for s in (opt('only', '') or '').split(',') if s]
PROPS = []
def prop(fid):
    def reg(fn): PROPS.append((fid, fn)); return fn
    return reg


# ------------------------------------------------------------ painting
def paint_vboards(col, seam, board=16, seed=0):
    """painted boards standing up (the bench skirt): vertical seams every `board` px, faint grain, scuffs low down"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:h, 0:w]
        g = 0.5 + 0.5 * np.sin(TAU * (xx + 0.7 * np.sin(TAU * yy / h * 2)) / board * 3)
        px[:] = hexrgb(col)[None, None] * (0.9 + 0.07 * g[:, :, None] + 0.06 * r.random((h, w, 1)))
        for x in range(0, w, board):
            px[:, x] = hexrgb(seam); px[:, (x + 1) % w] *= 0.8; px[:, (x - 1) % w] *= 1.05
        scuff = (MK.tnoise(w, h, 16, 4, r) + 0.4 * r.random((h, w))) * (yy / h) > 0.95
        px[scuff] = px[scuff] * 0.55 + hexrgb(0x6a5a3a) * 0.45
    return d


def paint_hazard(px):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx + yy) // 8) % 2 == 0
    px[:] = hexrgb(0x1a1a1e); px[m] = hexrgb(0xffd21a)
    px[0] *= 0.6; px[-1] *= 0.6


def paint_mat(px):  # ribbed rubber mat
    h, w = px.shape[:2]; r = np.random.default_rng(3)
    yy, xx = np.mgrid[0:h, 0:w]
    px[:] = hexrgb(0x2e9a52) * (0.85 + 0.15 * ((xx // 2) % 2))[:, :, None] * (0.95 + 0.08 * r.random((h, w, 1)))
    px[0] = px[-1] = hexrgb(0x1c6a36); px[:, 0] = px[:, -1] = hexrgb(0x1c6a36)


def plate(txt, bg, fg, border=None, scale=2):
    def d(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(bg)
        if border is not None:
            px[:2] = px[-2:] = hexrgb(border); px[:, :2] = px[:, -2:] = hexrgb(border)
        tw = len(txt) * 6 * scale - scale
        text_px(px, txt, max(0, (w - tw) // 2), max(0, (h - 7 * scale) // 2), scale, fg)
    return d


def paint_hessian(col, seed=0, stencil=None):
    """woven sacking: a coarse weave, darker specks, the odd loose thread; stencil = (text, colour) across the middle"""
    def d(px):
        h, w = px.shape[:2]; r = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:h, 0:w]
        weave = ((xx // 2 + yy // 2) % 2) * 0.12 + (xx % 2) * 0.05 + (yy % 2) * 0.04
        px[:] = hexrgb(col)[None, None] * (0.86 + weave[:, :, None] + 0.1 * MK.tnoise(w, h, 8, 4, r)[:, :, None])
        px[r.random((h, w)) < 0.03] *= 0.7
        for _ in range(4):
            y = r.integers(0, h); x0 = r.integers(0, w)
            for x in range(x0, x0 + 10): px[y, x % w] = hexrgb(col) * 1.15
        if stencil:
            s, c = stencil
            tw = len(s) * 6 - 1
            text_px(px, s, (w - tw) // 2, (h - 7) // 2, 1, c)
    return d


# ------------------------------------------------------------ p_rangebench
L_BENCH, H_BENCH, D_BENCH = 40.0, 0.8, 1.0

@prop('p_rangebench')
def build_bench():
    A = Atlas('rb_atlas', 128, 128)
    A.band('top', 16, paint_wood(0xe0a868, 0x9a5e2c, 11, edge=0.6, knots=3))
    A.band('skirt', 32, paint_vboards(0xffd22e, 0x8a6a10, 16, 12))
    A.band('hazard', 8, paint_hazard)
    A.cell('mat', 16, 16, paint_mat)
    for k in range(8): A.cell(f'n{k + 1}', 16, 16, plate(str(k + 1), 0xe8202a, 0xffffff, 0xffffff, 1))
    A.swatch('pink', 0xff4fd8, 0.05, 1).swatch('black', 0x222226, 0.05, 2).swatch('cup', 0xff3a2a, 0.05, 3)
    A.swatch('band', 0x2a2a30, 0.05, 4).swatch('olive', 0x5a6a2a, 0.08, 5).swatch('mug', 0x4fd8ff, 0.04, 6)
    A.cell('ammo', 32, 16, plate('JANK', 0x56662a, 0xffe14d, None, 1))
    M = mat('rb_paint', 0xffffff, rough=0.42, tex=A.image(), clearcoat=0.45)
    Mb = mat('rb_brass', 0xd8a838, rough=0.28, metal=1.0)
    hx, hz = L_BENCH / 2, D_BENCH / 2
    T = 0.07  # the counter top's thickness
    parts, far = [], []
    # the counter: three boards, a hair apart, flush with the box (it's what you lean on)
    bw = (D_BENCH - 0.012) / 3
    for k in range(3):
        z = -hz + bw / 2 + k * (bw + 0.006)
        b = box((L_BENCH, T, bw), (0, H_BENCH - T / 2, z), M, bev=0.012, name=f'rb_top{k}')
        uv_trim(b, A, 'top', upm=0.35, grain='x', uoff=k * 0.31); parts.append(b)
    # the skirt under it, set back 5 cm, and the kick plate
    sk = box((L_BENCH - 0.1, H_BENCH - T, D_BENCH - 0.1), (0, (H_BENCH - T) / 2, 0), M, bev=0.01, name='rb_skirt')
    uv_trim(sk, A, 'skirt', upm=0.69, grain='x'); parts.append(sk)
    for s in (-1, 1):
        kp = box((L_BENCH - 0.06, 0.14, 0.03), (0, 0.07, s * (hz - 0.045)), M, bev=0.006, name=f'rb_kick{s}')
        uv_trim(kp, A, 'hazard', upm=1.0, grain='x'); parts.append(kp)
    # lane posts every 5 m, both faces and the ends; red lane plates on the shooters' side
    for i in range(9):
        x = -hx + 0.08 + i * (L_BENCH - 0.16) / 8
        for s in (-1, 1):
            p = box((0.14, H_BENCH - T - 0.01, 0.046), (x, (H_BENCH - T) / 2, s * (hz - 0.033)), M, bev=0.012, name=f'rb_post{i}{s}')
            uv_fit(p, A, 'pink'); parts.append(p)
    for k in range(8):
        x = -hx + 2.5 + k * 5
        pl = box((0.3, 0.3, 0.02), (x, 0.42, hz - 0.03), M, bev=0.006, name=f'rb_plate{k}')
        uv_fit(pl, A, f'n{k + 1}'); parts.append(pl)
        for bx in (-0.12, 0.12):  # its screws
            sc = cyl(0.012, 0.012, (x + bx, 0.54, hz - 0.016), Mb, axis='z', seg=6, name=f'rb_screw{k}{bx}'); uv_box(sc, 0.05); parts.append(sc)
    # on top: a rubber mat per lane, spent brass, and whatever people left
    rng = random.Random(4)
    for k in range(8):
        x = -hx + 2.5 + k * 5
        mt = box((1.3, 0.012, 0.62), (x + rng.uniform(-0.3, 0.3), H_BENCH + 0.006, 0.05), M, bev=0.004, rot=(0, rng.uniform(-0.06, 0.06), 0), name=f'rb_mat{k}')
        uv_fit(mt, A, 'mat'); parts.append(mt)
        for j in range(5):  # cases lying on their side
            cx, cz = x + rng.uniform(-1.6, 1.6), rng.uniform(-0.35, 0.4)
            c = cyl(0.011, 0.05, (cx, H_BENCH + 0.011, cz), Mb, axis='x', seg=6, rot=(0, rng.uniform(0, 3.1), 0), name=f'rb_case{k}_{j}')
            uv_box(c, 0.05); parts.append(c)
        if k in (1, 4, 6):  # ear defenders: two cups on a band, lying down
            ex, ez = x - 1.2, -0.2
            for s in (-1, 1):
                cu = lathe([(0.0, 0.0), (0.05, 0.0), (0.055, 0.02), (0.05, 0.05), (0.0, 0.055)], (ex + s * 0.1, H_BENCH, ez), M, seg=10, axis='y', name=f'rb_cup{k}{s}')
                uv_fit(cu, A, 'cup'); parts.append(cu)
            hb = sweep([(ex - 0.1, H_BENCH + 0.03, ez), (ex - 0.07, H_BENCH + 0.03, ez + 0.09), (ex, H_BENCH + 0.03, ez + 0.12), (ex + 0.07, H_BENCH + 0.03, ez + 0.09), (ex + 0.1, H_BENCH + 0.03, ez)], 0.012, M, seg=5, name=f'rb_band{k}', squash=(0.6, 1.4))
            uv_fit(hb, A, 'band'); parts.append(hb)
        if k in (0, 3, 7):  # an ammo can
            ax_ = x + 1.5
            ac = box((0.28, 0.18, 0.14), (ax_, H_BENCH + 0.09, -0.25), M, bev=0.01, name=f'rb_can{k}')
            uv_fit(ac, A, 'ammo'); parts.append(ac)
            lid = box((0.29, 0.02, 0.15), (ax_, H_BENCH + 0.19, -0.25), M, bev=0.005, name=f'rb_lid{k}'); uv_fit(lid, A, 'olive'); parts.append(lid)
            hd = sweep([(ax_ - 0.06, H_BENCH + 0.2, -0.25), (ax_ - 0.05, H_BENCH + 0.23, -0.25), (ax_ + 0.05, H_BENCH + 0.23, -0.25), (ax_ + 0.06, H_BENCH + 0.2, -0.25)], 0.008, M, seg=5, name=f'rb_hdl{k}')
            uv_fit(hd, A, 'black'); parts.append(hd)
        if k == 5:  # somebody's coffee
            mg = lathe([(0.0, 0.0), (0.045, 0.0), (0.047, 0.1), (0.04, 0.1), (0.038, 0.012), (0.0, 0.012)], (x + 1.3, H_BENCH, 0.3), M, seg=12, axis='y', name='rb_mug')
            uv_fit(mg, A, 'mug'); parts.append(mg)
            hm = sweep([(x + 1.345, H_BENCH + 0.08, 0.3), (x + 1.38, H_BENCH + 0.07, 0.3), (x + 1.385, H_BENCH + 0.04, 0.3), (x + 1.345, H_BENCH + 0.025, 0.3)], 0.008, M, seg=5, name='rb_mugh')
            uv_fit(hm, A, 'mug'); parts.append(hm)
    # lod1: the counter, the skirt, the posts and plates as one painted block each
    t1 = box((L_BENCH, T, D_BENCH), (0, H_BENCH - T / 2, 0), M, name='rb_far_top'); uv_trim(t1, A, 'top', upm=0.35, grain='x'); far.append(t1)
    s1 = box((L_BENCH - 0.1, H_BENCH - T, D_BENCH - 0.1), (0, (H_BENCH - T) / 2, 0), M, name='rb_far_skirt'); uv_trim(s1, A, 'skirt', upm=0.69, grain='x'); far.append(s1)
    for k in range(8):
        pl = box((0.3, 0.3, 0.01), (-hx + 2.5 + k * 5, 0.42, hz - 0.045), M, name=f'rb_far_plate{k}'); uv_fit(pl, A, f'n{k + 1}'); far.append(pl)
    return dict(lod0=parts, lod1=far, box=((-hx, 0, -hz), (hx, H_BENCH, hz)), ao=0.35, lod=90,
                sheet=dict(res=(900, 420)))


# ------------------------------------------------------------ p_sandbags
def bag(L, W, H, M, name, neck=1, sag=0.0, rng=None, floor=0.0):
    """one filled sandbag along x, centred, bottom on y 0: a pillow (superellipse sections, fuller in the middle),
    the sewn end squared off, the other gathered into a tied neck with a little ear of cloth"""
    rng = rng or random.Random(0)
    n = 10
    def ring(sw, sh, flat=0.94):
        pts = []
        for i in range(n):
            a = TAU * i / n + 0.0001
            c, s = math.cos(a), math.sin(a)
            side = W / 2 * sw * math.copysign(abs(c) ** (2 / 3.2), c)
            up = H / 2 * sh * math.copysign(abs(s) ** (2 / 3.2), s)
            up = max(up, -H / 2 * flat)
            pts.append((up, side))
        return pts
    # stations from the sewn end (-x) to the neck (+x); sections: (x, width k, height k)
    st = [(-0.5, 0.82, 0.75), (-0.47, 0.95, 0.92), (-0.36, 1.0, 1.0), (-0.12, 1.02, 1.04 - sag), (0.12, 1.02, 1.03 - sag),
          (0.33, 0.98, 0.95), (0.42, 0.7, 0.68), (0.47, 0.28, 0.3), (0.5, 0.36, 0.38), (0.53, 0.3, 0.32)]
    if neck < 0: st = [(-x, w, h) for x, w, h in reversed(st)]
    cen = [(x * L, H / 2 * (h if abs(x) > 0.44 else 1.0) * 0 + H / 2, 0) for x, w, h in st]
    o = loft(cen, lambda i, t: ring(st[i][1], st[i][2]), M, name=name, smooth_angle=70, close=(True, True))  # (both ends gathered: no flat caps to meet a neighbour's)
    for v in o.data.vertices:  # lumpy fill, the bottom flat
        v.co += v.normal * rng.uniform(-0.004, 0.004)
        if v.co.z < 0.004 + floor: v.co.z = floor  # (neighbours' bottoms a hair apart: never one plane)
    return o


@prop('p_sandbags')
def build_sandbags():
    A = Atlas('sb_atlas', 64, 128)
    A.band('far', 16, paint_hessian(0xc0a066, 5))
    A.cell('tan', 32, 32, paint_hessian(0xcaa66a, 1)).cell('olive', 32, 32, paint_hessian(0x8a8a4a, 2))
    A.cell('pink', 32, 32, paint_hessian(0xff7ac8, 3, ('SAND?', 0x5a1040))).cell('tan2', 32, 32, paint_hessian(0xdcb878, 6))
    M = mat('sb_hessian', 0xffffff, rough=0.82, tex=A.image(), clearcoat=0.05)
    W_, H_, D_ = 3.0, 0.8, 1.0
    rng = random.Random(10)
    parts = []
    L, Wb, Hb = 0.71, 0.5, 0.2  # (fat enough that the two rows and the courses press into each other, like real ones; end to end they just touch)
    nb = 0
    for c in range(4):
        y0 = c * Hb
        inset = 0.035 * c  # the wall leans in a little as it goes up (battered, like a real one)
        off = (0.03 if c % 2 else -0.03)  # (courses staggered; 4 bags + the stagger fill the 3 m exactly)
        for row in (-1, 1):
            z = row * (D_ / 2 - Wb / 2 - 0.02 - inset)
            for i in range(4):
                x = -W_ / 2 + 0.385 + i * 0.74 + off
                x = max(-W_ / 2 + 0.355, min(W_ / 2 - 0.355, x))
                b = bag(L * rng.uniform(0.95, 1.0), Wb * rng.uniform(0.95, 1.02), Hb * rng.uniform(0.97, 1.03), M, f'sb_bag{c}{row}{i}',
                        neck=1 if (i + c + (row > 0)) % 2 else -1, sag=0.06 if c < 3 else 0.0, rng=rng,
                        floor=0.0035 * ((i % 2) + 2 * (row > 0)))  # (past the QA gate's 3 mm plane tolerance)
                b.location = gv(x, y0, z); b.rotation_euler = (0, 0, rng.uniform(-0.06, 0.06))
                key = 'pink' if (c, row, i) == (2, 1, 1) else rng.choice(['olive', 'tan', 'tan', 'tan2'])
                apply_mods(b)
                bpy.context.view_layer.objects.active = b
                b.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=False); b.select_set(False)
                uv_fit(b, A, key)  # (cells: fitted, each bag shows the whole weave)
                parts.append(b); nb += 1
    # lod1: each course as one lumpy slab
    far = []
    for c in range(4):
        inset = 0.035 * c
        def sec(i, t, inset=inset):
            d = D_ / 2 - 0.02 - inset; h = Hb
            return [(-h / 2, d - 0.03), (h / 2 - 0.05, d), (h / 2, d - 0.08), (h / 2, -d + 0.08), (h / 2 - 0.05, -d), (-h / 2, -d + 0.03)]
        f = loft([(-W_ / 2 + 0.02, c * Hb + Hb / 2, 0), (W_ / 2 - 0.02, c * Hb + Hb / 2, 0)], sec, M, name=f'sb_far{c}', smooth_angle=50)
        uv_trim(f, A, 'far', upm=0.9, grain='x'); far.append(f)
    return dict(lod0=parts, lod1=far, box=((-W_ / 2, 0, -D_ / 2), (W_ / 2, H_, D_ / 2)), ao=0.3, lod=30)


# ------------------------------------------------------------ p_rangemark
MARKS = [15, 30, 55, 105]

@prop('p_rangemark')
def build_marks():
    A = Atlas('rm_atlas', 128, 64)
    A.band('board', 16, paint_wood(0xf4efe4, 0xc8bca8, 21, edge=0.75, knots=0, lines=3))
    for d_ in MARKS:
        A.cell(f'm{d_}', 64, 16, plate(f'{d_} M', 0xffffff, 0x111114, 0xe8202a, 2))
    A.swatch('red', 0xe8202a, 0.05, 1).swatch('post', 0x7a5232, 0.1, 2).swatch('cap', 0xffd22e, 0.05, 3).swatch('bolt', 0x9a9aa4, 0.05, 4)
    M = mat('rm_paint', 0xffffff, rough=0.4, tex=A.image(), clearcoat=0.5)
    W_, H_, D_ = 4.0, 1.2, 0.4
    roots = []
    lod0_all, lod1_all = [], []
    groups = []
    for d_ in MARKS:
        parts, far = [], []
        for x in (-W_ / 2 + 0.1, W_ / 2 - 0.1):  # posts (a hair in from the cap's ends)
            p = box((0.18, H_ - 0.02, D_ - 0.04), (x, (H_ - 0.02) / 2, 0), M, bev=0.015, name=f'rm{d_}_post{x}'); uv_fit(p, A, 'post'); parts.append(p)
        for s in (-1, 1):  # the boards both sides, then the red frame and the plate
            for k in range(4):
                y = 0.06 + k * 0.27 + 0.13
                b = box((W_ - 0.36, 0.25, 0.05), (0, y, s * (D_ / 2 - 0.045)), M, bev=0.008, name=f'rm{d_}_b{s}{k}')
                uv_trim(b, A, 'board', upm=0.4, grain='x', uoff=k * 0.37); parts.append(b)
            for (fx, fy, fw, fh) in ((0, 0.12, W_ - 0.36, 0.05), (0, 1.0, W_ - 0.36, 0.05), (-1.795, 0.56, 0.05, 0.83), (1.795, 0.56, 0.05, 0.83)):
                fr = box((fw, fh, 0.02), (fx, fy, s * (D_ / 2 - 0.01)), M, bev=0.004, name=f'rm{d_}_fr{s}{fx}{fy}'); uv_fit(fr, A, 'red'); parts.append(fr)
            pl = box((2.6, 0.62, 0.015), (0, 0.56, s * (D_ / 2 - 0.012)), M, bev=0.004, name=f'rm{d_}_plate{s}')
            uv_fit(pl, A, f'm{d_}'); parts.append(pl)
            for bx in (-1.22, 1.22):
                for by in (0.3, 0.82):
                    parts.append(cyl(0.018, 0.012, (bx, by, s * (D_ / 2 - 0.002)), M, axis='z', seg=6, name=f'rm{d_}_bolt{s}{bx}{by}'))
                    uv_fit(parts[-1], A, 'bolt')
        cap = box((W_, 0.06, D_), (0, H_ - 0.03, 0), M, bev=0.012, name=f'rm{d_}_cap'); uv_fit(cap, A, 'cap'); parts.append(cap)
        f = box((W_, H_, D_ - 0.06), (0, H_ / 2, 0), M, name=f'rm{d_}_far'); uv_trim(f, A, 'board', upm=0.4, grain='x'); far.append(f)
        for s in (-1, 1):
            fp = box((2.6, 0.62, 0.01), (0, 0.56, s * (D_ / 2 - 0.025)), M, name=f'rm{d_}_farplate{s}'); uv_fit(fp, A, f'm{d_}'); far.append(fp)
        groups.append((d_, parts, far))
    return dict(groups=groups, box=((-W_ / 2, 0, -D_ / 2), (W_ / 2, H_, D_ / 2)), ao=0.3, lod=45)


def run_variants(fid, fn):
    """a prop whose copies pick a variant node (v15 / v30 ...): one node per variant under the root, each with its own
    lod0 and lod1 (propfield.js draws the node from its own origin)"""
    lib.reset(); lib._mats.clear()
    d = fn()
    lo, hi = V3(d['box'][0]), V3(d['box'][1])
    roots = []
    nodes = []
    for d_, parts, far in d['groups']:
        if opt('qa'): MK.qa(parts, f'{fid} v{d_}:lod0'); MK.qa(far, f'{fid} v{d_}:lod1')
        l0 = join(parts, f'{fid}_v{d_}_lod0'); l1 = join(far, f'{fid}_v{d_}_lod1')
        for o in (l0, l1):
            bpy.context.view_layer.objects.active = o
            for s in bpy.context.view_layer.objects.selected: s.select_set(False)
            o.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        MK.box_report(l0, lo, hi, f'{fid} v{d_} lod0')
        bake_ao([l0], dist=d['ao']); bake_ao([l1], dist=d['ao'])
        nodes.append((d_, l0, l1))
    meta = dict(id=fid[2:], kind='prop', lod=d['lod'], tint=False, size=[round(hi[i] - lo[i], 3) for i in range(3)],
                box=[[round(v, 3) for v in lo], [round(v, 3) for v in hi]], variants=[f'v{d_}' for d_ in MARKS])
    root = _link(bpy.data.objects.new(fid, None)); root['jf'] = json.dumps(meta)
    for d_, l0, l1 in nodes:
        v = _link(bpy.data.objects.new(f'v{d_}', None)); v.parent = root
        l0.parent = v
        e = _link(bpy.data.objects.new('lod1', None)); e.parent = v
        l1.parent = e
    print(f'JF_MATS {fid}: meta {json.dumps(meta)}')
    if not opt('no-export'): export(root, fid)
    if not opt('no-sheet'):
        show = [n for n in root.children if n.name == 'v105'][0]  # (the sheet shows one; the others are the same but the number)
        for n in root.children:
            for o in n.children_recursive: o.hide_render = n is not show
        t0, t1 = prop_stats(show)
        MK.sheet4(show, fid, t0, t1, 1, 1, res=(640, 420))
    return root


if __name__ == '__main__':
    for fid, fn in PROPS:
        if ONLY and fid[2:] not in ONLY and fid not in ONLY: continue
        if fid == 'p_rangemark': run_variants(fid, fn)
        else: MK.run_prop(fid, fn)
