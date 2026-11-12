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
#   p_berm        the backstop at the end of the lanes (render-only, 120 x 16 x 15): a lumpy earth bank, grass on its
#                 crown, bullet-pocked front, a crib of timber ties along its toe, six paper targets on frames in front
#                 (sticking out past its boxes toward the lanes) and a red range flag on top
#   p_watchtower  the two range towers behind the spawn (render-only, 4.8 x 10.8): timber legs with X bracing, a plank
#                 deck with a railing and a RANGE CONTROL sign, a ladder up the back, a corrugated roof on corner
#                 posts, a red beacon, a megaphone
# run: blender52 -b --python tools/blender/make_range.py -- [--only=rangebench,sandbags] [--no-sheet] [--no-export] [--qa]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib
from lib import _link
import make_market as MK
from make_market import Atlas, paint_wood, paint_noise, uv_trim, uv_fit, poly_obj, outward, sweep, opt, V3, TAU, fcen, _gn

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


# ------------------------------------------------------------ p_berm
def paint_dirt(px):
    h, w = px.shape[:2]; r = np.random.default_rng(41)
    n = MK.tnoise(w, h, 16, 4, r)
    px[:] = hexrgb(0xa8743e)[None, None] * (0.78 + 0.35 * n[:, :, None]) * (0.92 + 0.12 * r.random((h, w, 1)))
    px[r.random((h, w)) < 0.025] = hexrgb(0x5a3a1c)  # bullet holes
    px[r.random((h, w)) < 0.02] = hexrgb(0xd8b080)  # pebbles


def paint_grass(px):
    h, w = px.shape[:2]; r = np.random.default_rng(42)
    px[:] = hexrgb(0x4ad040)[None, None] * (0.8 + 0.3 * MK.tnoise(w, h, 16, 4, r)[:, :, None])
    m = (np.arange(h)[:, None] > h * 0.7) & (r.random((h, w)) < 0.5)  # ragged edge down into the dirt
    px[m] = hexrgb(0x8a6a3a)


def paint_target(px):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    px[:] = hexrgb(0xf4ecd8)
    d = np.hypot(xx - w / 2 + 0.5, (yy - h * 0.55) * 1.0)
    for k, c in ((6, 0x141018), (5, 0xffffff), (4, 0x141018), (3, 0xffffff), (2, 0xff2a3a), (1, 0xffe14d)):
        px[d < k * w * 0.075] = hexrgb(c)
    text_px(px, 'JANK', (w - 23) // 2, 3, 1, 0xff2a3a)
    px[d < 1.2] = hexrgb(0x141018)
    for x_, y_ in ((w * 0.44, h * 0.5), (w * 0.62, h * 0.66), (w * 0.3, h * 0.72)):  # somebody hit it, eventually
        px[int(y_), int(x_)] = hexrgb(0x000000)


def paint_flag(px):
    h, w = px.shape[:2]; r = np.random.default_rng(43)
    px[:] = hexrgb(0xff2a3a) * (0.9 + 0.1 * r.random((h, w, 1)))


@prop('p_berm')
def build_berm():
    A = Atlas('bm_atlas', 128, 128)
    A.band('dirt', 32, paint_dirt).band('grass', 16, paint_grass).band('tie', 16, paint_wood(0x6a4a2a, 0x3a2614, 44, edge=0.6, knots=2))
    A.cell('target', 32, 32, paint_target).cell('flag', 16, 16, paint_flag).cell('steel', 8, 8, paint_noise(0x9a9aa6, 0.05, 45))
    A.cell('card', 16, 16, paint_noise(0xc8a070, 0.08, 46))
    M = mat('bm_dirt', 0xffffff, rough=0.85, tex=A.image(), clearcoat=0.0)
    Mp = mat('bm_paint', 0xffffff, rough=0.5, tex=A.image(), clearcoat=0.2)
    HW, HD, H = 60.0, 7.5, 16.0
    prof = [(7.5, 0.0), (6.4, 2.4), (5.0, 6.4), (3.4, 10.8), (2.3, 14.0), (1.2, 15.6), (0.0, 16.0), (-1.6, 15.6), (-3.0, 14.0), (-4.8, 9.6), (-6.4, 4.2), (-7.5, 0.0)]
    xs = list(np.linspace(-HW, HW, 61))
    def fac(x):
        t = max(0.0, (abs(x) - 46.0) / 14.0)
        return 1.0 - 0.8 * (t * t * (3 - 2 * t))
    rings = []
    for x in xs:
        f = fac(x)
        rings.append([(y * f, z * (0.75 + 0.25 * f)) for z, y in prof])
    def ring(i, t):  # (up, side): the profile, closed along the ground
        return rings[i]
    o = loft([(x, 0, 0) for x in xs], ring, M, name='bm_bank', smooth_angle=55, cap=False)
    # the ends: a fan down to the ground at each end (no n-gons)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    n = len(prof)
    ends = [(end, [bm.verts[end * n + k] for k in range(n)]) for end in (0, len(xs) - 1)]  # (before adding any)
    for end, vs in ends:
        c = bm.verts.new(sum((v.co for v in vs), Vector()) / n)
        for k in range(n - 1):
            try: bm.faces.new((vs[k], vs[k + 1], c) if end else (vs[k + 1], vs[k], c))
            except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    rr = np.random.default_rng(47)
    for v in bm.verts:  # lumpy, not on the ground line
        if v.co.z > 0.05: v.co += Vector((rr.uniform(-0.25, 0.25), rr.uniform(-0.25, 0.25), rr.uniform(-0.3, 0.3)))
    bm.to_mesh(o.data); bm.free()
    grassy = lambda poly, P_: _gn(poly.normal).y > 0.8 and fcen(poly, P_).y > 13.0
    uv_trim(o, A, 'grass', upm=0.1, grain='x', sel=grassy)
    uv_trim(o, A, 'dirt', upm=0.08, grain='x', sel=lambda poly, P_: not grassy(poly, P_))
    parts = [o]
    rng = random.Random(48)
    # the timber crib along the toe: two courses of old ties, butted end to end, half buried, the top course on the bottom one
    for c in range(2):
        x = -52.0 + c * 1.3
        while x < 52.0:
            L = rng.uniform(2.4, 2.7)
            t = box((L - 0.04, 0.26, 0.24), (x + L / 2, 0.09 + c * 0.22, 6.85 - c * 0.15), M, bev=0.03, rot=(0, rng.uniform(-0.02, 0.02), 0), name=f'bm_tie{c}_{x:.1f}')
            uv_trim(t, A, 'tie', upm=0.4, grain='x'); parts.append(t)
            x += L
    # targets on frames in front (toward the lanes, past the boxes: you see them down the range)
    for k, x in enumerate((-40.0, -24.0, -8.0, 8.0, 24.0, 40.0)):
        z = 9.2 + rng.uniform(-0.2, 0.2)
        for sx in (-0.62, 0.62):
            p = box((0.09, 2.5, 0.09), (x + sx, 1.25, z), Mp, bev=0.012, name=f'bm_post{k}{sx}'); uv_trim(p, A, 'tie', upm=0.4, grain='y'); parts.append(p)
        bk = box((1.3, 1.7, 0.03), (x, 1.65, z + 0.06), Mp, bev=0.008, name=f'bm_card{k}'); uv_fit(bk, A, 'card'); parts.append(bk)
        tg = box((1.1, 1.5, 0.006), (x, 1.65, z + 0.08), Mp, name=f'bm_target{k}'); uv_fit(tg, A, 'target'); parts.append(tg)
        cl = box((1.36, 0.06, 0.08), (x, 2.48, z + 0.03), Mp, bev=0.01, name=f'bm_clip{k}'); uv_fit(cl, A, 'steel'); parts.append(cl)
    # the red flag on top
    pole = cyl(0.06, 5.0, (-44.0, 15.5 + 2.5, 0.0), Mp, axis='y', seg=8, name='bm_pole'); uv_fit(pole, A, 'steel'); parts.append(pole)
    rows = []
    for j in range(5):
        y = 19.9 - j * 0.3
        rows.append([(-44.0 + 0.06 + i * 0.3, y, 0.12 * math.sin(i * 1.3 + j * 0.2)) for i in range(7)])
    fl = MK.sheet_obj(rows, Mp, 'bm_flag', smooth_angle=70)
    sol = fl.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.03; sol.offset = 0.0
    apply_mods(fl); outward(fl); uv_fit(fl, A, 'flag'); parts.append(fl)
    far = []
    xs1 = xs[::6]
    f = loft([(x, 0, 0) for x in xs1], lambda i, t: [(y * fac(xs1[i]), z * (0.75 + 0.25 * fac(xs1[i]))) for z, y in prof[::2] + [prof[-1]]], M, name='bm_far', smooth_angle=55, cap=False)
    uv_trim(f, A, 'dirt', upm=0.08, grain='x'); far.append(f)
    # (no targets far away: a few pixels at 220 m)
    return dict(lod0=parts, lod1=far, box=((-HW, 0, -HD), (HW, H, HD)), ao=3.0, lod=220, sheet=dict(res=(900, 420)))


# ------------------------------------------------------------ p_watchtower
def paint_sign(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xffd22e); px[:2] = px[-2:] = hexrgb(0x141018); px[:, :2] = px[:, -2:] = hexrgb(0x141018)
    text_px(px, 'RANGE', (w - 29) // 2, 3, 1, 0x141018)
    text_px(px, 'CONTROL', (w - 41) // 2, 12, 1, 0x141018)


@prop('p_watchtower')
def build_tower():
    A = Atlas('wt_atlas', 128, 128)
    A.band('timber', 16, paint_wood(0x9a6a3a, 0x5a3a1c, 51, edge=0.65, knots=2))
    A.band('plank', 16, paint_wood(0xb88850, 0x6a4422, 52, edge=0.55, knots=1))
    A.cell('sign', 64, 24, paint_sign).cell('red', 8, 8, paint_noise(0xff2a3a, 0.04, 53)).cell('white', 8, 8, paint_noise(0xf4f4f0, 0.04, 54))
    A.cell('black', 8, 8, paint_noise(0x1a1820, 0.04, 55))
    M = mat('wt_wood', 0xffffff, rough=0.6, tex=A.image(), clearcoat=0.15)
    Mm = mat('wt_metal', 0xc8ccd6, rough=0.35, metal=0.9)
    G_ = mat('glow', 0xff2a3a, rough=0.3, emit=0xff3020, strength=3.0)
    parts = []
    L, P = 1.6, 0.3
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = box((P, 7.9, P), (sx * L, 4.05, sz * L), M, bev=0.03, name=f'wt_leg{sx}{sz}'); uv_trim(p, A, 'timber', upm=0.25, grain='y'); parts.append(p)
            fp = box((0.5, 0.12, 0.5), (sx * L, 0.06, sz * L), Mm, bev=0.02, name=f'wt_foot{sx}{sz}'); uv_box(fp, 0.5); parts.append(fp)  # (steel footing plates)
    # X bracing on all four sides and a girt half way up
    for yaw in (0.0, math.pi / 2, math.pi, -math.pi / 2):
        c, s_ = math.cos(yaw), math.sin(yaw)
        def T(x, y, z): return (x * c + z * s_, y, -x * s_ + z * c)
        out = L + P / 2 + 0.04
        for a, b in (((-L, 0.6), (L, 7.4)), ((L, 0.6), (-L, 7.4))):
            bb = MK.box_between(T(a[0], a[1], out), T(b[0], b[1], out), 0.18, 0.06, M, f'wt_brace{yaw:.2f}{a[0]}')
            uv_trim(bb, A, 'plank', upm=0.3); parts.append(bb)
        g = MK.box_between(T(-L - P / 2, 4.0, out + 0.07), T(L + P / 2, 4.0, out + 0.07), 0.2, 0.06, M, f'wt_girt{yaw:.2f}')
        uv_trim(g, A, 'plank', upm=0.3); parts.append(g)
    # deck: joists and planks
    for k in range(3):  # joists across, planks along: every plank sits on all three
        j = box((0.12, 0.16, 4.4), (-1.5 + k * 1.5, 8.08, 0), M, bev=0.015, name=f'wt_joist{k}'); uv_trim(j, A, 'timber', upm=0.25, grain='z'); parts.append(j)
    for k in range(11):
        z = -2.2 + 0.2 + k * 0.4
        pl = box((4.4, 0.14, 0.37), (0, 8.225, z), M, bev=0.015, name=f'wt_deck{k}'); uv_trim(pl, A, 'plank', upm=0.3, grain='x', uoff=k * 0.37); parts.append(pl)
    # railing: posts, a top rail, plank walls on three sides (the back is open at the ladder)
    for sx in (-1, 1):
        for sz in (-1, 1):
            rp = box((0.14, 2.2, 0.14), (sx * 2.06, 8.3 + 1.1, sz * 2.06), M, bev=0.015, name=f'wt_rpost{sx}{sz}'); uv_trim(rp, A, 'timber', upm=0.25, grain='y'); parts.append(rp)
    for name_, size, pos in (('front', (4.0, 0.9, 0.05), (0, 8.75, -2.06)), ('left', (0.05, 0.9, 4.0), (-2.06, 8.75, 0)), ('right', (0.05, 0.9, 4.0), (2.06, 8.75, 0))):
        wl = box(size, pos, M, bev=0.01, name=f'wt_wall_{name_}'); uv_trim(wl, A, 'plank', upm=0.3, grain='x' if size[0] > 1 else 'z'); parts.append(wl)
    for name_, size, pos in (('front', (4.2, 0.08, 0.12), (0, 9.24, -2.06)), ('left', (0.12, 0.08, 4.2), (-2.06, 9.24, 0)), ('right', (0.12, 0.08, 4.2), (2.06, 9.24, 0)),
                             ('backl', (1.25, 0.08, 0.12), (-1.47, 9.24, 2.06)), ('backr', (1.25, 0.08, 0.12), (1.47, 9.24, 2.06))):
        tr = box(size, pos, M, bev=0.015, name=f'wt_rail_{name_}'); uv_trim(tr, A, 'timber', upm=0.25, grain='x' if size[0] > 1 else 'z'); parts.append(tr)
    sg = box((1.8, 0.62, 0.03), (0, 8.75, -2.1), M, bev=0.008, name='wt_sign'); uv_fit(sg, A, 'sign'); parts.append(sg)
    # the ladder up the back
    for sx in (-0.34, 0.34):
        lr = MK.box_between((sx, 0.0, 2.36), (sx, 9.0, 2.0), 0.08, 0.06, M, f'wt_lrail{sx}'); uv_trim(lr, A, 'timber', upm=0.25); parts.append(lr)
    for k in range(27):
        y = 0.3 + k * 0.3
        if y > 8.1: break
        z = 2.36 - 0.36 * y / 9.0
        rg = cyl(0.025, 0.66, (0, y, z), Mm, axis='x', seg=6, name=f'wt_rung{k}'); uv_box(rg, 0.2); parts.append(rg)
    # the corrugated roof on the railing posts (they run on up to it), a hair of fall to the back
    rows = []
    for j in range(2):
        z = -2.4 + j * 4.8
        rows.append([(-2.4 + i * 0.1, 10.62 - 0.06 * j + 0.04 * math.sin(i * math.pi / 2), z) for i in range(49)])
    rf = MK.sheet_obj(rows, Mm, 'wt_roof', smooth_angle=80)
    sol = rf.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 0.05; sol.offset = 0.0
    apply_mods(rf); outward(rf); uv_box(rf, 0.5); parts.append(rf)
    bc = lathe([(0.12, 0.0), (0.12, 0.06), (0.1, 0.2), (0.05, 0.28), (0.0, 0.3)], (1.4, 10.66, -1.4), G_, seg=12, axis='y', name='wt_beacon'); uv_box(bc, 0.2); parts.append(bc)
    bb_ = cyl(0.14, 0.06, (1.4, 10.66, -1.4), Mm, axis='y', seg=12, name='wt_beaconbase'); uv_box(bb_, 0.2); parts.append(bb_)
    mg = lathe([(0.05, 0.0), (0.06, 0.18), (0.16, 0.42), (0.17, 0.44), (0.0, 0.44)], (-1.3, 9.32, -2.06), M, seg=12, axis='z', name='wt_megaphone', rot=(0.25, 0, 0))  # (resting on the front rail)
    uv_fit(mg, A, 'white'); parts.append(mg)
    far = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = box((P, 8.0, P), (sx * L, 4.0, sz * L), M, name=f'wt_far_leg{sx}{sz}'); uv_trim(p, A, 'timber', upm=0.25, grain='y'); far.append(p)
    hut = box((4.4, 1.3, 4.4), (0, 8.65, 0), M, name='wt_far_deck'); uv_trim(hut, A, 'plank', upm=0.3, grain='x'); far.append(hut)
    fr = box((4.8, 0.2, 4.8), (0, 10.6, 0), Mm, name='wt_far_roof'); uv_box(fr, 0.5); far.append(fr)
    for sx in (-1, 1):
        for sz in (-1, 1):
            cp = box((0.12, 1.0, 0.12), (sx * 2.06, 10.0, sz * 2.06), M, name=f'wt_far_cpost{sx}{sz}'); uv_trim(cp, A, 'timber', upm=0.25, grain='y'); far.append(cp)
    return dict(lod0=parts, lod1=far, box=((-2.4, 0, -2.4), (2.4, 10.8, 2.4)), ao=0.8, lod=60)


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
