# PALLET JACK, the man: textures and materials, head, neck, torso (skin + singlet), the hi-vis vest, hips and belt,
# trousers, calves and boots, arms and hands. The machine in him is jackrig.py; what happens to him is jackdmg.py.
# Every function builds in one joint's frame (game axes, unit scale; the game scales the root x1.18) and hands the
# pieces to J.P.add(joint, objs, tag). J.S keeps the surfaces so the rig parts can sit on them.
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jackkit import *  # noqa

ID = 'pallet_jack'
SK = 0xeea488
PI = math.pi


class Jack:
    def __init__(s):
        s.P = Parts(ID); s.M = {}; s.S = {}; s.marks = {}; s.vals = {}


def knots(kn):
    """a smooth function of the angle round the body, mirrored left / right: kn = [(|a|, value)...] from 0 (front) to pi"""
    def f(a):
        a = abs(math.atan2(math.sin(a), math.cos(a)))
        i = 0
        while i < len(kn) - 2 and a > kn[i + 1][0]: i += 1
        p1, p2 = kn[i], kn[i + 1]; p0 = kn[i - 1] if i > 0 else p1; p3 = kn[i + 2] if i + 2 < len(kn) else p2
        t = min(1.0, max(0.0, (a - p1[0]) / max(1e-9, p2[0] - p1[0])))
        return castkit_cr(p0[1], p1[1], p2[1], p3[1], t)
    return f


def castkit_cr(p0, p1, p2, p3, t):
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)


# ------------------------------------------------------------------------------------------------ textures
def marker_text(px, s, x0, y0, sizes, col, seed=3, bold=1):
    """hand lettering with a fat marker: the 5x7 glyphs at any height per letter (sizes), each one nudged and leaning"""
    rr = random.Random(seed); c = hexrgb(col); h, w = px.shape[:2]
    x = float(x0)
    for i, ch in enumerate(s):
        g = FONT.get(ch.upper(), FONT[' ']); sz = sizes[min(i, len(sizes) - 1)]
        cw = sz * 0.62 / 5; chh = sz / 7
        dy = rr.uniform(-1.2, 1.2); lean = rr.uniform(-0.06, 0.1)
        for ry, row in enumerate(g):
            for rx, bit in enumerate(row):
                if bit != '1': continue
                xa = x + rx * cw + (6 - ry) * lean * cw; ya = y0 + dy + ry * chh
                x1, y1 = int(round(xa)), int(round(ya)); x2, y2 = int(round(xa + cw + bold * 0.6)), int(round(ya + chh + bold * 0.4))
                px[max(0, y1):min(h, max(y2, y1 + 1)), max(0, x1):min(w, max(x2, x1 + 1))] = c * (0.85 + 0.3 * rr.random())
        x += sz * 0.62 + max(1.0, sz * 0.14)
    return x


def t_hivis(px):  # v = height on the vest: silver bands round the body, fabric grain, grime toward the hem
    h, w = px.shape[:2]; r = np.random.default_rng(51)
    px[:] = hexrgb(0xdcf532) * (0.93 + 0.07 * r.random((h, w, 1)))
    for y in range(h):
        if y % 3 == 0: px[y] *= 0.965
    for a, b in ((0.60, 0.69), (0.78, 0.87)):  # rows from the top: the two bands
        y0, y1 = int(a * h), int(b * h)
        px[y0:y1] = hexrgb(0xc4cad0) * (0.9 + 0.1 * r.random((y1 - y0, w, 1)))
        px[y0] = hexrgb(0x8a9096); px[y1 - 1] = hexrgb(0x8a9096)
        for y in range(y0 + 2, y1 - 1, 3): px[y] *= 0.93
    g = np.linspace(1.0, 0.8, h // 4)[:, None, None]; px[h - h // 4:] *= g  # grubby hem
    px[r.random((h, w)) < 0.012] = hexrgb(0x8a9a2a)


def t_vestback(px):
    h, w = px.shape[:2]; r = np.random.default_rng(52)
    px[:] = hexrgb(0xdcf532) * (0.93 + 0.07 * r.random((h, w, 1)))
    for y in range(0, h, 3): px[y] *= 0.965
    x1 = marker_text(px, 'MARSH', 20, 6, [21, 21, 20, 21, 20], 0x18182a, seed=7, bold=2)
    marker_text(px, 'DELIVERIES', 6, 36, [16, 16, 15, 15, 14, 13, 12, 10, 9, 8], 0x18182a, seed=9, bold=1)
    px_line(px, 8, 55, 104, 53, 0x18182a, w=2)  # underlined once, not quite straight
    px[r.random((h, w)) < 0.01] = hexrgb(0x8a9a2a)
    px[h - 4:] *= 0.86


def t_rib(px):
    h, w = px.shape[:2]; r = np.random.default_rng(53)
    px[:] = hexrgb(0xddd6c4) * (0.95 + 0.05 * r.random((h, w, 1)))
    for x in range(0, w, 4): px[:, x] = hexrgb(0xbfb7a2)
    for x in range(1, w, 4): px[:, x] *= 1.03


def t_keg(px):  # u round the back of the keg, v up it (256 x 128)
    h, w = px.shape[:2]; r = np.random.default_rng(54)
    streak = np.kron(r.random((h, 1)), np.ones((1, w)))
    px[:] = hexrgb(0xc4cad0) * (0.86 + 0.14 * streak[:, :, None]) * (0.96 + 0.04 * r.random((h, w, 1)))
    for k in range(60):  # scratches
        x0 = r.integers(0, w - 30); y = r.integers(2, h - 2); px[y, x0:x0 + r.integers(6, 28)] = hexrgb(0xdcdfe3)
    # heat tint low down, round the fire door: straw -> blue
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot((xx - w / 2) / (w * 0.2), (yy - h * 0.78) / (h * 0.3))
    k = np.clip(1.25 - d, 0, 1)[:, :, None]
    heat = np.where(d[:, :, None] < 0.55, hexrgb(0x5a66a0), hexrgb(0xc8a05a))
    px[:] = px * (1 - 0.6 * k) + heat * 0.6 * k
    # the brewery's stencil, half scrubbed off
    msk = np.zeros((h, w, 3), np.float32)
    text_px(msk, 'RETURN', w // 2 - 35, 22, 2, 0xffffff); text_px(msk, 'EMPTY', w // 2 - 29, 42, 2, 0xffffff)
    keep = (msk[:, :, 0] > 0) & (r.random((h, w)) < 0.9)
    px[keep] = px[keep] * 0.15 + hexrgb(0x22262c) * 0.85
    # bev's plate
    x0, y0 = w // 2 + 44, h - 30
    px[y0:y0 + 11, x0:x0 + 27] = hexrgb(0xc89a3a); px[y0, x0:x0 + 27] = hexrgb(0x7a5a1a); px[y0 + 10, x0:x0 + 27] = hexrgb(0x7a5a1a)
    text_px(px, 'BEV', x0 + 2, y0 + 2, 1, 0x3a2a0a); text_px(px, '15', x0 + 15, y0 + 2, 1, 0x3a2a0a)
    for (cx, cy) in ((x0 + 1, y0 + 5), (x0 + 25, y0 + 5)): px[cy, cx] = hexrgb(0x3a2a0a)
    px[r.random((h, w)) < 0.006] = hexrgb(0x6a4a2a)  # rust freckles


def t_dial(px):
    h, w = px.shape[:2]; c = w / 2
    px[:] = hexrgb(0x2a2a2e)
    px_disc(px, c, c, c - 1, 0xf2ecd8)
    px_disc(px, c, c, c - 3, 0x3aa84a, r_in=c - 7, a0=-2.2, a1=0.5)
    px_disc(px, c, c, c - 3, 0xe8c030, r_in=c - 7, a0=0.5, a1=1.3)
    px_disc(px, c, c, c - 3, 0xd03020, r_in=c - 7, a0=1.3, a1=2.2)
    for i in range(12):
        a = -2.2 + 4.4 * i / 11
        px_line(px, c + math.sin(a) * (c - 3), c - math.cos(a) * (c - 3), c + math.sin(a) * (c - 9), c - math.cos(a) * (c - 9), 0x1a1a1e, w=1)
    text_px(px, 'BAR', int(c - 8), int(c + 6), 1, 0x1a1a1e)


def t_check(px):  # the tea towel: cream, red windowpane check, soup
    h, w = px.shape[:2]; r = np.random.default_rng(55)
    px[:] = hexrgb(0xf0e8d2) * (0.94 + 0.06 * r.random((h, w, 1)))
    for k in range(0, w, 8): px[:, k] = hexrgb(0xcc4a3a); px[k, :] = hexrgb(0xcc4a3a)
    for k in range(4, w, 8): px[:, k] *= 0.94; px[k, :] *= 0.94
    yy, xx = np.mgrid[0:h, 0:w]
    for (cx, cy, rad, col) in ((9, 20, 7, 0xd8862a), (22, 9, 5, 0xc8701e), (25, 25, 4, 0xd8862a), (5, 5, 3, 0xb85a1a)):
        m = rpkit.blob_mask(h, w, cx, cy, rad, seed=cx * 7 + cy, yy=yy, xx=xx)
        px[m] = px[m] * 0.45 + hexrgb(col) * 0.55


def t_haz(px):
    h, w = px.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    k = ((xx + yy) // 5) % 2
    px[:] = np.where(k[:, :, None] == 0, hexrgb(0xe8c020), hexrgb(0x1c1c20))
    r = np.random.default_rng(56); px[r.random((h, w)) < 0.07] = hexrgb(0x8a8e94)


def t_tattoo(px):
    h, w = px.shape[:2]; r = np.random.default_rng(41)
    px[:] = hexrgb(SK) * (0.93 + 0.14 * r.random((h, w, 1)))
    ink = 0x3a4a5a
    text_px(px, 'THIS WAY UP', 2, 12, 1, ink)
    for cx in (12, 52):  # the two arrows off a parcel
        px_line(px, cx, 9, cx, 2, ink, w=1); px_line(px, cx - 3, 5, cx, 2, ink, w=1); px_line(px, cx + 3, 5, cx, 2, ink, w=1)
    px[21, 4:60] = hexrgb(ink)
    fade = r.random((h, w)) < 0.22
    px[fade] = hexrgb(SK) * (0.93 + 0.14 * r.random((int(fade.sum()), 1)))


def t_char(px):
    h, w = px.shape[:2]; r = np.random.default_rng(57)
    lo = np.kron(r.random((h // 4, w // 4)), np.ones((4, 4)))
    px[:] = hexrgb(0x1e1c1f) * (0.7 + 0.6 * lo[:, :, None])
    px[r.random((h, w)) < 0.05] = hexrgb(0x4a4648)
    for k in range(7):  # cracks with a little red left in them
        x, y = r.integers(0, w), r.integers(0, h)
        for i in range(9):
            px[y % h, x % w] = hexrgb(0x8a2a20); x += r.integers(-1, 2); y += 1


def t_wrap(px):
    h, w = px.shape[:2]; r = np.random.default_rng(58)
    px[:] = hexrgb(0xb8a37a) * (0.85 + 0.15 * r.random((h, w, 1)))
    for y in range(0, h, 4): px[y] = hexrgb(0x6a5a3a)
    px[r.random((h, w)) < 0.1] = hexrgb(0x3a342a)


def fluoro(name, tex):
    """hi-vis: it gives a little light back (the texture glows faintly), so it reads in the Bottom's dusk"""
    m = mat(name, 0xffffff, rough=0.85, tex=tex, emit=0xffffff, strength=0.22, emit_tex=True); m.use_backface_culling = False
    return m


def materials(J):
    M = J.M
    M['skin'] = rubber('pj_skin', SK, skin_tex('pj_pores', SK, 0xc46a56, size=64, seed=41, p=0.05))
    M['stub'] = rubber('pj_stubble', SK, tex_noise('pj_stub', SK, 0.07, 64, speck=0x8a6257, speck_p=0.34, seed=42), rough=0.5)
    M['scar'] = rubber('pj_scar', 0xf6c2b2, tex_noise('pj_scartex', 0xf6c2b2, 0.05, 32, speck=0xffe0d6, speck_p=0.12, seed=43), rough=0.28)
    M['lines'] = rubber('pj_lines', 0xdf8672, skin_tex('pj_linetex', 0xdf8672, 0xb85a4a, size=32, seed=44, p=0.06), rough=0.36)
    M['lip'] = rubber('pj_raw', 0xc0584e, rough=0.3)
    M['singlet'] = cloth('pj_singlet', 0xffffff, tex_canvas('pj_rib', 16, 16, t_rib))
    M['hivis'] = fluoro('pj_hivis', tex_canvas('pj_hivistex', 16, 128, t_hivis))
    M['vestback'] = fluoro('pj_vestback', tex_canvas('pj_vestbacktex', 128, 64, t_vestback))
    M['hiplain'] = fluoro('pj_hivisplain', tex_noise('pj_hiplaintex', 0xdcf532, 0.06, 16, seed=64))
    M['reflect'] = mat('pj_reflect', 0xc4cad0, rough=0.35, metal=0.3)
    M['bind'] = cloth('pj_bind', 0x2a2c30)
    M['paper'] = mat('pj_paper', 0xf2ecd8, rough=0.7)
    M['canvas'] = cloth('pj_canvas', 0x35506c, tex_noise('pj_canvastex', 0x35506c, 0.1, 32, speck=0x4a6a88, speck_p=0.06, seed=45))
    M['cuff'] = cloth('pj_cuff', 0x5d7f9e, tex_noise('pj_cufftex', 0x5d7f9e, 0.08, 32, seed=46))
    M['belt'] = mat('pj_belt', 0x5c3a22, rough=0.5, clearcoat=0.2, tex=tex_noise('pj_belttex', 0x5c3a22, 0.14, 32, speck=0x3a2414, speck_p=0.05, seed=47))
    M['boot'] = mat('pj_boot', 0xb5803c, rough=0.62, tex=tex_noise('pj_boottex', 0xb5803c, 0.14, 32, speck=0x7a5222, speck_p=0.08, seed=48))
    M['sole'] = mat('pj_sole', 0x2c2420, rough=0.85)
    M['lace'] = mat('pj_lace', 0xd8c89a, rough=0.8)
    M['steel'] = mat('pj_steel', 0x9aa0a8, rough=0.36, metal=0.6, tex=tex_noise('pj_steeltex', 0x8a9098, 0.1, 32, speck=0x5e646c, speck_p=0.04, seed=49))
    M['chrome'] = mat('pj_chrome', 0xe2e6ec, rough=0.18, metal=0.55, clearcoat=0.5)
    M['blued'] = mat('pj_blued', 0x525a78, rough=0.3, metal=0.6, tex=tex_noise('pj_bluedtex', 0x4a5068, 0.16, 32, speck=0x8a6a4a, speck_p=0.06, seed=50))
    M['red'] = mat('pj_red', 0xc8372a, rough=0.3, clearcoat=0.5, tex=tex_noise('pj_redtex', 0xc8372a, 0.08, 32, speck=0x8a8e94, speck_p=0.06, seed=59))
    M['keg'] = mat('pj_keg', 0xffffff, rough=0.33, metal=0.5, tex=tex_canvas('pj_kegtex', 256, 128, t_keg))
    M['kegplain'] = mat('pj_kegplain', 0xbcc2c8, rough=0.35, metal=0.5, tex=tex_noise('pj_kegp', 0xbcc2c8, 0.08, 32, seed=60))
    M['brass'] = mat('pj_brass', 0xd2a444, rough=0.3, metal=0.65)
    M['copper'] = mat('pj_copper', 0xc26e42, rough=0.34, metal=0.6, tex=tex_noise('pj_coppertex', 0xb8643a, 0.14, 32, speck=0x4a8a6a, speck_p=0.05, seed=61))
    M['dark'] = mat('pj_dark', 0x1e1e22, rough=0.6)
    M['soot'] = mat('pj_soot', 0x121214, rough=0.9)
    M['dial'] = mat('pj_dial', 0xffffff, rough=0.25, tex=tex_canvas('pj_dialtex', 48, 48, t_dial), emit=0xffffff, strength=0.25, emit_tex=True)
    M['glass'] = glassmat('pj_glass', 0xd8eef8, 0.3)
    M['needle'] = mat('pj_needle', 0xd02a1a, rough=0.4)
    M['glow'] = mat('pj_glow', 0xff6a2a, rough=0.5, emit=0xff5a22, strength=2.2)
    M['hose'] = mat('pj_hose', 0x5a1a1c, rough=0.45, clearcoat=0.3)
    M['wrap'] = cloth('pj_wrap', 0xffffff, tex_canvas('pj_wraptex', 16, 16, t_wrap))
    M['haz'] = mat('pj_haz', 0xffffff, rough=0.4, tex=tex_canvas('pj_haztex', 32, 16, t_haz))
    M['hair'] = mat('pj_hair', 0x3a2a22, rough=0.7, tex=tex_noise('pj_hairtex', 0x3a2a22, 0.22, 32, speck=0x8a8480, speck_p=0.16, seed=62))
    M['towel'] = cloth('pj_towel', 0xffffff, tex_canvas('pj_check', 32, 32, t_check))
    M['tattoo'] = rubber('pj_tattoo', 0xffffff, tex_canvas('pj_tattootex', 64, 32, t_tattoo))
    M['nail'] = rubber('pj_nail', 0xf6d2c0, rough=0.3)
    M['band'] = mat('pj_rubberband', 0xb0452e, rough=0.6)
    M['key'] = mat('pj_key', 0xd0b868, rough=0.3, metal=0.6)
    # what happens to him
    M['char'] = mat('pj_char', 0xffffff, rough=0.75, tex=tex_canvas('pj_chartex', 32, 32, t_char))
    M['bone'] = mat('pj_bone', 0xe6d8ba, rough=0.5, tex=tex_noise('pj_bonetex', 0xe6d8ba, 0.1, 16, speck=0xb89a7a, speck_p=0.08, seed=63))
    M['wound'] = mat('pj_wound', 0x5a0c12, rough=0.18, clearcoat=0.6)
    M['blood'] = mat('pj_blood', 0x7a1016, rough=0.3, clearcoat=0.4)
    M['hole'] = mat('pj_hole', 0x12060a, rough=0.9)
    M['core'] = mat('pj_core', 0xff3a22, rough=0.4, emit=0xff2a14, strength=3.0)
    M['marrow'] = mat('pj_marrow', 0xff2414, rough=0.25, clearcoat=0.6, emit=0xff1a0a, strength=1.6)
    M['lanyard'] = cloth('pj_lanyard', 0x4fd8ff)
    M['card'] = mat('pj_card', 0xf4f2ea, rough=0.5)
    return M


def mat_where(o, m, test):
    """hand the faces whose middle passes test(game point) a second material"""
    apply_mods(o)
    me = o.data
    if m.name not in [x.name for x in me.materials]: me.materials.append(m)
    idx = [x.name for x in me.materials].index(m.name)
    mw = o.matrix_basis
    for p in me.polygons:
        c = mw @ p.center
        if test(Vector((c.x, c.z, -c.y))): p.material_index = idx
    return o


# ------------------------------------------------------------------------------------------------ head + neck
EYES = [(-0.054, 0.168, -0.0993), (0.054, 0.168, -0.0993)]   # (where looks.js puts the eye pivots: face z -0.108 + 0.35 eye radii)
MOUTH = (0, 0.064, -0.124)


def head(J):
    M = J.M; hd = []
    hc = Vector((0, 0.142, 0.004)); R = (0.131, 0.146, 0.132)
    eyes = [Vector(e) for e in EYES]; mo = Vector(MOUTH)

    def fn(p, n):
        g = hc + p; off = 0.0
        for e in eyes: off -= 0.021 * gauss((g - e).length, 0.031)                             # sockets
        if n.z < -0.1:
            off += 0.012 * gauss(g.y - 0.206, 0.017) * smooth01(0.105 - abs(g.x), 0.0, 0.03)     # a heavy brow
            off += 0.009 * gauss(g.y - 0.126, 0.03) * gauss(abs(g.x) - 0.08, 0.03)               # cheekbones
            off += 0.016 * gauss(g.y - 0.072, 0.045) * gauss(g.x, 0.075)                         # the muzzle the mouth sits in
            off -= 0.004 * gauss((g - mo).length, 0.02)
            off -= 0.006 * gauss(g.y - 0.103, 0.012) * gauss(abs(g.x) - 0.05, 0.02)              # the lines from nose to mouth
        low = smooth01(0.115 - g.y, 0.0, 0.085)
        off += 0.024 * low * abs(n.x) ** 1.4                                                    # a broad jaw, wide all the way down
        off += 0.013 * smooth01(0.062 - g.y, 0, 0.05) * max(0.0, -n.z) * gauss(g.x, 0.075)       # a square chin
        off -= 0.007 * smooth01(g.y - 0.245, 0, 0.04)                                           # a flat crown
        return off
    sk = blob('skull', tuple(hc), R, M['skin'], fn=fn, seg=26, rings=18)

    def stubble_w(p):
        w = smooth01(0.118 - p.y, 0.0, 0.03) * smooth01(0.075 - p.z, 0.0, 0.05)
        sb = smooth01(abs(p.x), 0.095, 0.115) * smooth01(0.21 - p.y, 0, 0.03) * smooth01(p.y, 0.09, 0.12) * gauss(p.z + 0.0, 0.045)  # sideburns
        return max(w, sb)

    def tn(p, n):
        c = (1.0, 1.0, 1.0)
        c = mix3(c, (1.0, 0.8, 0.78), 0.75 * gauss(p.y - 0.122, 0.03) * gauss(abs(p.x) - 0.082, 0.032) * smooth01(-p.z, 0.02, 0.07))  # flushed cheeks
        c = mix3(c, (0.8, 0.68, 0.76), 0.8 * gauss(p.y - 0.139, 0.012) * gauss(abs(p.x) - 0.054, 0.024) * smooth01(-p.z, 0.05, 0.09))  # tired
        c = mix3(c, (0.74, 0.68, 0.7), 0.9 * stubble_w(p))
        c = mix3(c, (0.9, 0.78, 0.76), 0.5 * smooth01(p.y, 0.25, 0.3))
        return c
    tint(sk, tn)
    mat_where(sk, M['stub'], lambda c: stubble_w(c) > 0.45)
    hd.append(sk)
    # the nose: broken once, set by nobody. the bridge jogs to his left and there's a pale line across it
    npts = [(0.0, 0.178, -0.116), (0.004, 0.16, -0.127), (-0.008, 0.143, -0.134), (-0.004, 0.126, -0.141), (0.002, 0.11, -0.146), (0.002, 0.1, -0.136)]
    nose = limb('nose', npts, [0.012, 0.015, 0.018, 0.02, 0.023, 0.017], M['skin'], seg=8, squash=(0.8, 1.0))
    tint(nose, lambda p, n: mix3((1, 1, 1), (1.0, 0.76, 0.74), smooth01(0.15 - p.y, 0, 0.05) * 0.8))
    hd.append(nose)
    for sx in (-1, 1):
        w = blob('nostril%d' % sx, (0.002 + sx * 0.018, 0.107, -0.131), (0.0135, 0.0115, 0.015), M['skin'])
        tint(w, lambda p, n: (1.0, 0.78, 0.76)); hd.append(w)
        hd.append(blob('nhole%d' % sx, (0.002 + sx * 0.011, 0.0985, -0.138), (0.0062, 0.004, 0.0065), M['lip']))
    hd.append(tube([(-0.02, 0.149, -0.132), (-0.008, 0.146, -0.1495), (0.004, 0.15, -0.145), (0.014, 0.154, -0.13)], 0.003, M['scar'], seg=4, name='nosescar'))
    # under his eyes; the ridge of the brow gets a second lump over his right eye (an old one)
    for sx in (-1, 1):
        b = blob('bag%d' % sx, (sx * 0.054, 0.1365, -0.112), (0.024, 0.007, 0.007), M['skin'])
        tint(b, lambda p, n: (0.76, 0.6, 0.68)); hd.append(b)
    sc = tube([(0.068, 0.214, -0.112), (0.078, 0.2, -0.108), (0.083, 0.186, -0.1)], 0.0032, M['scar'], seg=4, name='browscar'); hd.append(sc)
    # ears: big, the left one thickened
    for sx in (-1, 1):
        e = blob('ear%d' % sx, (sx * 0.14, 0.15, 0.014), (0.017, 0.04, 0.029), M['skin'],
                 fn=lambda p, n, sx=sx: (0.006 * math.sin(p.y * 160) if sx < 0 else 0.0) - 0.006 * max(0.0, sx * n.x) * gauss(p.y, 0.02), seg=10, rings=6)
        e.rotation_euler = Euler((0, 0, sx * 0.0), 'XYZ')
        tint(e, lambda p, n: (1.0, 0.78, 0.76)); hd.append(e)
        hd.append(blob('earin%d' % sx, (sx * 0.153, 0.15, 0.006), (0.004, 0.022, 0.013), M['lip'], seg=6, rings=4))
    # hair: short, going back at the temples, grey coming in
    def hair_fn(p, n):
        g = Vector((0, 0.215, 0.022)) + p
        line = 0.228 + 0.026 * gauss(g.x, 0.045) - 0.012 * gauss(abs(g.x) - 0.09, 0.03)   # the hairline: a widow's peak, high temples
        cut = g.z < 0.03 and g.y < line - max(0.0, g.z + 0.11) * 0.55
        if g.z >= 0.03 and g.y < 0.118: cut = True   # the neckline at the back
        if abs(g.x) > 0.1 and g.z < 0.045 and g.y < 0.2: cut = True  # round the ears
        return -0.075 if cut else 0.004 * math.sin(g.x * 90) * math.sin(g.z * 70)
    hr = blob('hair', (0, 0.215, 0.022), (0.138, 0.086, 0.136), M['hair'], fn=hair_fn, seg=16, rings=10)
    hd.append(hr)
    J.P.add('head', hd)
    # ---- the neck: thick, with a line up each side under the skin
    ns = Surf([(-0.085, 0.125, 0.115, 0.12, 0, 0.006, 2.2), (-0.03, 0.112, 0.104, 0.108, 0, 0.004, 2.2), (0.03, 0.104, 0.098, 0.104, 0, 0.0, 2.2), (0.075, 0.102, 0.096, 0.102, 0, 0.0, 2.2)])
    J.S['neck'] = ns
    nk = ns.mesh('neck', M['skin'], [-0.085, -0.04, 0.0, 0.04, 0.075], seg=14)
    tint(nk, lambda p, n: mix3((1, 1, 1), (0.68, 0.64, 0.68), 0.8 * smooth01(p.y, 0.02, 0.07) * smooth01(-n.z, -0.2, 0.4)))
    nkp = [nk]
    for sx in (-1, 1):
        nkp.append(ns.line('nline%d' % sx, [(-0.08, sx * 1.0), (-0.03, sx * 0.9), (0.02, sx * 1.05), (0.07, sx * 1.3)], 0.011, M['lines'], n=6))
    J.P.add('neck', nkp[:1]); J.P.add('neck', nkp[1:], 'lines', note='the hydraulic lines under his skin (material pj_lines: the game can pulse it)')


# ------------------------------------------------------------------------------------------------ torso
TORSO = [(-0.09, 0.3, 0.215, 0.2, 0, 0.0, 2.6), (0.0, 0.318, 0.246, 0.21, 0, -0.002, 2.6), (0.1, 0.338, 0.272, 0.216, 0, -0.006, 2.6),
         (0.2, 0.352, 0.266, 0.222, 0, -0.004, 2.8), (0.3, 0.376, 0.25, 0.226, 0, 0.0, 3.0), (0.4, 0.396, 0.236, 0.226, 0, 0.0, 3.0),
         (0.47, 0.376, 0.214, 0.214, 0, 0.004, 2.8), (0.53, 0.29, 0.168, 0.178, 0, 0.008, 2.5), (0.575, 0.18, 0.128, 0.135, 0, 0.008, 2.3), (0.61, 0.125, 0.112, 0.118, 0, 0.006, 2.2)]
SING_TOP = [(0.0, 0.365), (0.3, 0.39), (0.52, 0.45), (0.72, 0.462), (1.05, 0.36), (1.4, 0.292), (1.75, 0.3), (2.15, 0.39), (2.5, 0.462), (2.75, 0.47), (PI, 0.448)]
STRAP = [(0.458, 0.62), (0.5, 0.7), (0.545, 0.95), (0.566, PI / 2), (0.548, 2.2), (0.5, 2.48), (0.462, 2.6)]
KEG = dict(y0=0.058, y1=0.368, r=0.142, cz=0.236)        # the boiler: where it is (spine frame)
VEST_TOP = [(0.0, 0.28), (0.14, 0.3), (0.4, 0.43), (0.62, 0.508), (0.85, 0.5), (1.15, 0.33), (1.5, 0.262), (1.9, 0.3), (2.3, 0.47), (2.5, 0.53), (PI, 0.548)]
VEST_BOT = [(0.0, 0.0), (1.2, -0.012), (2.2, 0.004), (2.42, 0.07), (2.56, 0.335), (2.7, 0.39), (PI, 0.397)]
VEST_V = (-0.02, 0.56)
VEST_OPEN = 0.15


def torso(J):
    M = J.M
    ts = Surf(TORSO); J.S['torso'] = ts
    sp = []
    # the skin he shows: shoulders, the top of the chest, his sides under the arms
    stop = knots(SING_TOP)
    body = ts.mesh('torso', M['skin'], [0.0, 0.14, 0.28, 0.42, 0.55, 0.67, 0.78, 0.87, 0.94, 1.0], seg=28, bot=lambda a: stop(a) - 0.045, top=lambda a: 0.61, cap=(False, True))
    def tn(p, n):
        c = (1, 1, 1)
        c = mix3(c, (1.0, 0.84, 0.82), 0.5 * gauss(p.y - 0.42, 0.06) * smooth01(-n.z, 0.2, 0.8))   # a flushed chest
        c = mix3(c, (0.9, 0.8, 0.8), 0.5 * smooth01(n.z, 0.2, 0.8) * gauss(p.y - 0.5, 0.08))
        return c
    tint(body, tn); sp.append(body)
    # the singlet: ribbed, off white, a scooped neck and deep armholes; soup down the front of it
    top = knots(SING_TOP)
    sg = ts.mesh('singlet', M['singlet'], [i / 9 for i in range(10)], seg=28, off=0.006, top=top, bot=lambda a: -0.09, uv=(0, 14, 0, 4), vr=(-0.09, 0.47))
    def stain(p, n):
        c = (1, 1, 1)
        f = smooth01(-n.z, 0.1, 0.7)
        nz = 0.5 + 0.5 * noise.noise(Vector((p.x * 9, p.y * 9, 3.1)))
        c = mix3(c, (0.86, 0.6, 0.34), 0.75 * f * gauss(p.x - 0.07, 0.06) * gauss(p.y - 0.22, 0.05) * (0.6 + 0.8 * nz))    # soup
        c = mix3(c, (0.8, 0.52, 0.3), 0.65 * f * gauss(p.x + 0.12, 0.035) * gauss(p.y - 0.12, 0.04))
        c = mix3(c, (0.8, 0.52, 0.3), 0.5 * f * gauss(p.x + 0.03, 0.02) * gauss(p.y - 0.31, 0.03))
        c = mix3(c, (0.78, 0.76, 0.72), 0.55 * gauss(p.y - 0.4, 0.07) * (1 - 0.5 * nz))                                   # sweat round the neck
        c = mix3(c, (0.74, 0.72, 0.68), 0.6 * smooth01(0.03 - p.y, 0, 0.1))                                              # grubby where it tucks in
        c = mix3(c, (0.7, 0.68, 0.66), 0.6 * smooth01(n.z, 0.3, 0.9) * gauss(p.y - 0.2, 0.2) * gauss(p.x, 0.16))          # scorched grey round the boiler
        return c
    tint(sg, stain); sp.append(sg)
    for sx in (-1, 1):
        st = ts.strip('strap%d' % sx, M['singlet'], [(y, sx * a) for y, a in STRAP], 0.07, off=0.007, n=11, uv=(0, 1.5, 0, 6),
                      lift=lambda t: 0.012 * gauss(t - 0.12, 0.12))
        sp.append(st)
    # scar tissue over plate: the breastbone (in the scoop of the singlet), both shoulder blades
    pl = []
    pl.append(ts.plate('plate_sternum', M['scar'], 0.412, 0.0, 0.07, 0.11, off=0.006, n=3.0))
    pl += ts.stitches('stitch', M['lip'], 0.412, 0.0, 0.07, 0.11, n=3.0, count=10, off=0.0065)
    for sx in (-1, 1): pl.append(ts.plate('plate_blade%d' % sx, M['scar'], 0.498, PI + sx * 0.42, 0.075, 0.12, off=0.006, n=3.5))
    for (y, a) in ((0.428, -0.11), (0.428, 0.11), (0.396, 0.0)): pl.append(rivet(tuple(ts.p(y, a, 0.006)), 0.0075, M['steel'], tuple(ts.n(y, a))))
    for sx in (-1, 1):
        for (dy, da) in ((0.022, -0.12), (0.022, 0.12), (-0.024, 0.0)):
            y, a = 0.498 + dy, PI + sx * 0.42 + da
            pl.append(rivet(tuple(ts.p(y, a, 0.006)), 0.0075, M['steel'], tuple(ts.n(y, a))))
    # the corner the skin never took to: bare plate showing on his right shoulder blade
    pl.append(ts.plate('plate_bare', M['steel'], 0.522, PI - 0.56, 0.03, 0.045, off=0.0085, n=2.5, spokes=8))
    J.P.add('spine', sp)
    J.P.add('spine', pl, 'plates', note='scar tissue grown over armour plate (pj_scar), rivets and one bare corner')
    # hydraulic lines under the skin: off the collarbone down to the armpits, up the back from the boiler to the shoulders
    ln = []
    for sx in (-1, 1):
        ln.append(ts.line('l_chest%d' % sx, [(0.468, sx * 0.34), (0.44, sx * 0.62), (0.42, sx * 0.95), (0.37, sx * 1.22), (0.31, sx * 1.36)], 0.012, M['lines'], n=7))
        ln.append(ts.line('l_side%d' % sx, [(0.3, sx * 1.62), (0.36, sx * 1.72), (0.43, sx * 1.9), (0.47, sx * 2.1)], 0.011, M['lines'], n=6))
        ln.append(ts.line('l_back%d' % sx, [(0.45, PI - sx * 0.2), (0.5, PI - sx * 0.16), (0.545, PI - sx * 0.3), (0.572, PI - sx * 0.75)], 0.012, M['lines'], n=6))
    J.P.add('spine', ln, 'lines')


def vest(J):
    """the hi-vis: its own piece (tag vest), open down the front, an arch cut out of the back for the boiler,
    MARSH DELIVERIES across the shoulders in marker, a docket book and a pen in the pockets"""
    M = J.M; ts = J.S['torso']
    top = knots(VEST_TOP); bot = knots(VEST_BOT)
    off = lambda y, a: 0.02 + 0.022 * smooth01(0.2 - y, 0.0, 0.22) * (0.6 + 0.4 * math.cos(3 * a)) + 0.012 * gauss(abs(math.atan2(math.sin(a), math.cos(a))) - 0.3, 0.25) * smooth01(0.3 - y, 0, 0.2)
    rows = [i / 7 for i in range(8)]
    A0, A1 = VEST_OPEN, PI - 0.75
    vs = []
    r_ = ts.mesh('vest_r', M['hivis'], rows, seg=13, a0=A0, a1=A1, off=off, top=top, bot=bot, uv=(0, 3, 0, 1), vr=VEST_V)
    l_ = ts.mesh('vest_l', M['hivis'], rows, seg=13, a0=TAU - A1, a1=TAU - A0, off=off, top=top, bot=bot, uv=(0, 3, 0, 1), vr=VEST_V)
    b_ = ts.mesh('vest_b', M['vestback'], rows, seg=10, a0=A1, a1=TAU - A1, off=off, top=top, bot=bot, uv=(1, 0, 0, 1), vr=(0.36, 0.56))
    def grime(p, n):
        c = (1, 1, 1)
        c = mix3(c, (0.8, 0.78, 0.7), 0.6 * smooth01(0.1 - p.y, 0, 0.14))
        c = mix3(c, (0.62, 0.6, 0.56), 0.7 * smooth01(n.z, 0.5, 0.95) * smooth01(0.46 - p.y, 0, 0.09))   # soot where it sits on the boiler
        return c
    for o in (r_, l_, b_): tint(o, grime)
    vs += [r_, l_, b_]
    # over the shoulders: the yoke, a silver brace down each
    for sx in (-1, 1):
        pts = [(0.5, 0.66), (0.535, 0.82), (0.566, 1.2), (0.578, PI / 2), (0.568, 2.0), (0.54, 2.36), (0.52, 2.48)]
        vs.append(ts.strip('vyoke%d' % sx, M['hivis'], [(y, sx * a) for y, a in pts], 0.125, off=0.024, n=11, uv=(0, 1, 0.9, 1.0)))
        vs.append(ts.strip('vbrace%d' % sx, M['reflect'], [(y, sx * a) for y, a in pts], 0.034, off=0.0275, n=11))
        # the brace carries on down the front to the top band
        vs.append(ts.strip('vbrace_f%d' % sx, M['reflect'], [(0.5, sx * 0.66), (0.42, sx * 0.6), (0.33, sx * 0.56), (0.262, sx * 0.54)], 0.034, off=0.026, n=6, lift=lambda t: 0.004 * t))
    # binding round the edges: the front opening, the hem (a fat dark tape)
    def edge(pts, nm, r=0.0045): vs.append(sweep([tuple(ts.p(y, a, off(y, a) + 0.001)) for y, a in pts], r, M['bind'], seg=4, name=nm))
    for sx in (-1, 1):
        a_ = sx * A0
        edge([(bot(a_) + (top(a_) - bot(a_)) * i / 6, a_) for i in range(7)], 'vb_front%d' % sx)
        edge([(bot(sx * a), sx * a) for a in [A0 + (2.38 - A0) * i / 12 for i in range(13)]], 'vb_hem%d' % sx)
    edge([(bot(a), a) for a in [2.38 + (TAU - 4.76) * i / 12 for i in range(13)]], 'vb_arch', r=0.0052)
    # a chest pocket with a pen in it (his left), a hip pocket with the docket book (his right)
    def pocket(yc, ac, w, h, nm):
        o = ts.plate(nm, M['hiplain'], yc, ac, h, w, off=off(yc, ac) + 0.006, n=6.0, spokes=12, sink=-0.002, inner=0.9)
        return o
    vs.append(pocket(0.33, -0.46, 0.085, 0.075, 'vpock_chest'))
    pp = ts.p(0.362, -0.5, off(0.36, -0.5) + 0.011); pn = ts.n(0.362, -0.5)
    vs.append(rod(tuple(pp - Vector((0, 0.03, 0))), tuple(pp + Vector((0, 0.035, 0))), 0.0045, mat('pj_pen', 0x2a4ad0, rough=0.3), seg=6, name='pen'))
    vs.append(pocket(0.09, 0.62, 0.13, 0.1, 'vpock_hip'))
    dp = ts.p(0.135, 0.62, off(0.135, 0.62) + 0.012)
    dk = box((0.085, 0.07, 0.014), tuple(dp), M['paper'], bev=0.002, rot=(0.08, -0.55, 0.12), name='dockets'); vs.append(dk)
    dk2 = box((0.089, 0.016, 0.026), tuple(dp + Vector((0, 0.034, 0))), M['bind'], rot=(0.08, -0.55, 0.12), name='docketspine'); vs.append(dk2)
    J.P.add('spine', vs, 'vest', note='the hi-vis vest, MARSH DELIVERIES in marker. removable: he gives it to Dumpling')


# ------------------------------------------------------------------------------------------------ hips, belt, trousers
PELVIS = [(0.79, 0.24, 0.165, 0.18, 0, 0.005, 2.4), (0.86, 0.3, 0.215, 0.215, 0, 0.004, 2.5), (0.93, 0.328, 0.252, 0.226, 0, 0.0, 2.6), (1.0, 0.338, 0.266, 0.23, 0, 0.0, 2.6), (1.05, 0.338, 0.266, 0.23, 0, 0.0, 2.6)]


def hips(J):
    M = J.M
    ps = Surf(PELVIS); J.S['pelvis'] = ps
    bd = []
    pv = ps.mesh('pelvis', M['canvas'], [0.79, 0.83, 0.88, 0.93, 0.98, 1.03], seg=24, cap=(True, True))
    tint(pv, lambda p, n: mix3((1, 1, 1), (0.8, 0.8, 0.82), 0.5 * smooth01(0.86 - p.y, 0, 0.07)))
    bd.append(pv)
    # the lifting belt: brown leather, tall at the back where the boiler sits on it, a steel two-prong buckle
    bt = knots([(0.0, 1.018), (1.0, 1.024), (2.0, 1.04), (PI, 1.05)]); bb = knots([(0.0, 0.962), (1.2, 0.955), (2.2, 0.94), (PI, 0.935)])
    belt = ps.mesh('belt', M['belt'], [0, 0.5, 1], seg=28, off=0.014, top=bt, bot=bb)
    bl = [belt]
    for (yy, o_) in ((bt, 0.0), (bb, 0.0)):
        bl.append(sweep([tuple(ps.p(yy(a), a, 0.012)) for a in [TAU * i / 18 for i in range(19)]], 0.0065, M['belt'], seg=3, name='beltedge'))
    bf = ps.p(0.99, 0.0, 0.02)
    for (dx, dy, w, h, dz) in ((0, 0.03, 0.07, 0.012, 0.0015), (0, -0.03, 0.07, 0.012, 0.0015), (-0.042, 0, 0.014, 0.075, 0.0), (0.042, 0, 0.014, 0.075, 0.0)):
        bl.append(box((w, h, 0.012 - dz * 2), (bf.x + dx, bf.y + dy, bf.z - 0.004), M['steel'], bev=0.003, name='buckle'))
    for dy in (-0.012, 0.012): bl.append(rod((bf.x - 0.04, bf.y + dy, bf.z - 0.008), (bf.x + 0.02, bf.y + dy, bf.z - 0.012), 0.0035, M['steel'], seg=5, name='prong'))
    tg = ps.strip('belttail', M['belt'], [(0.985, -0.1), (0.98, -0.25), (0.972, -0.42)], 0.05, off=0.022, n=5); bl.append(tg)
    # trouser details: the fly, a button, the back pockets, belt loops
    bd.append(box((0.012, 0.11, 0.01), tuple(ps.p(0.895, 0.0, 0.004)), M['canvas'], bev=0.003, name='fly'))
    bd.append(rivet(tuple(ps.p(0.948, 0.0, 0.004)), 0.011, M['brass'], tuple(ps.n(0.948, 0.0))))
    for sx in (-1, 1):
        bd.append(ps.plate('backpocket%d' % sx, M['canvas'], 0.885, PI + sx * 0.52, 0.11, 0.125, off=0.005, n=5.0, spokes=12, sink=0.001, inner=0.88))
        for a in (0.55, 1.5, 2.55): bl.append(ps.strip('loop%d' % sx, M['canvas'], [(0.925, sx * a), (0.99, sx * a), (1.06, sx * a)], 0.022, off=0.024, n=3))
    # keys on a carabiner off his left hip
    kp = ps.p(0.935, -1.25, 0.014)
    ky = [tube([(kp.x, kp.y + 0.03, kp.z), (kp.x - 0.012, kp.y + 0.012, kp.z), (kp.x - 0.01, kp.y - 0.02, kp.z), (kp.x + 0.008, kp.y - 0.022, kp.z), (kp.x + 0.008, kp.y + 0.02, kp.z), (kp.x, kp.y + 0.03, kp.z)], 0.004, M['chrome'], seg=4, name='carabiner')]
    for i, (dz, rz) in enumerate(((-0.012, 0.3), (0.0, -0.2), (0.014, 0.1))):
        ky.append(box((0.016, 0.05, 0.003), (kp.x - 0.004, kp.y - 0.05, kp.z + dz), M['key'], bev=0.001, rot=(rz * 0.5, 0.4, rz), name='key'))
    J.P.add('body', bd + bl + ky)
    # ---- the tea towel in his back right pocket: red check, soup on it
    c0 = ps.p(0.925, PI - 0.52, 0.012); n0 = ps.n(0.925, PI - 0.52); side = Vector((0, 1, 0)).cross(n0).normalized()
    def tw(u, v):
        fold = 0.012 * math.sin(u * 9.0 + v * 2.0) * (0.4 + v) + 0.02 * v * v
        drop = v * 0.26 + 0.035 * (u - 0.5) * v
        q = c0 + side * ((u - 0.5) * 0.13 * (1 - 0.25 * v)) - Vector((0, 1, 0)) * drop + n0 * (0.012 + fold - 0.03 * v)
        if v < 0.12: q = q - n0 * 0.01 * (0.12 - v) / 0.12   # tucked into the pocket's mouth
        return tuple(q)
    tw_o = sheet_mesh('towel', M['towel'], tw, nu=6, nv=9, thick=0.006)
    J.P.add('body', [tw_o], 'towel', note='the soup-stained tea towel in his back pocket')


def legs(J):
    M = J.M
    for k, kn, sx in (('legL', 'kneeL', -1), ('legR', 'kneeR', 1)):
        # thigh (leg frame, scaled 0.8 by the game): trousers, a knee patch, a cargo pocket on the left
        th = Surf([(0.05, 0.128, 0.125, 0.13, 0, 0.0, 2.2), (-0.1, 0.136, 0.14, 0.135, 0, -0.004, 2.2), (-0.26, 0.124, 0.128, 0.122, 0, -0.004, 2.2), (-0.4, 0.114, 0.114, 0.112, 0, 0.0, 2.2), (-0.47, 0.112, 0.112, 0.112, 0, 0.0, 2.2)])
        J.S[k] = th
        o = th.mesh('thigh' + k, M['canvas'], [0.05, -0.05, -0.16, -0.27, -0.37, -0.47], seg=16, cap=(True, True))
        tint(o, lambda p, n: mix3((1, 1, 1), (1.18, 1.16, 1.12), 0.5 * gauss(p.y + 0.4, 0.07) * smooth01(-n.z, 0.2, 0.8)))   # worn pale at the knee
        lg = [o]
        lg.append(th.plate('kneepatch' + k, M['cuff'], -0.385, 0.0, 0.15, 0.15, off=0.005, n=5.0, spokes=12, sink=0.001, inner=0.88))
        if sx < 0:
            lg.append(th.plate('cargo', M['canvas'], -0.2, -PI / 2, 0.15, 0.13, off=0.014, n=6.0, spokes=12, sink=0.0, inner=0.9))
            lg.append(th.plate('cargoflap', M['canvas'], -0.145, -PI / 2, 0.05, 0.14, off=0.02, n=6.0, spokes=12, sink=0.004, inner=0.9))
            lg.append(rivet(tuple(th.p(-0.16, -PI / 2, 0.022)), 0.008, M['brass'], (-1, 0, 0)))
        lg.append(th.line('seam' + k, [(0.02, sx * PI / 2), (-0.2, sx * PI / 2), (-0.44, sx * PI / 2)], 0.004, M['canvas'], sink=0.2, seg=4))
        J.P.add(k, lg)
        # ---- the lower leg (knee frame): the knee under cloth, the turn-up, the calf at the back, the boot. the piston
        # down the front of it is jackrig.py
        kp = [ball(0.116, (0, -0.005, -0.004), M['canvas'], scale=(1, 0.95, 1.0), seg=10, rings=7, name='knee' + kn)]
        cuff = lathe([(0.097, -0.115), (0.118, -0.118), (0.126, -0.1), (0.127, -0.07), (0.122, -0.052), (0.112, -0.05)], (0, 0, 0.004), M['cuff'], seg=16, axis='y', name='cuff' + kn, cap=False)
        kp.append(cuff)
        kp.append(cyl(0.107, 0.004, (0, -0.104, 0.004), M['dark'], axis='y', seg=14, name='cuffin' + kn))
        cs = Surf([(-0.1, 0.07, 0.04, 0.06, 0, 0.052, 2.2), (-0.17, 0.078, 0.042, 0.086, 0, 0.056, 2.2), (-0.24, 0.07, 0.04, 0.074, 0, 0.052, 2.2), (-0.31, 0.058, 0.038, 0.052, 0, 0.046, 2.2), (-0.35, 0.056, 0.04, 0.05, 0, 0.042, 2.2)])
        J.S[kn] = cs
        cf = cs.mesh('calf' + kn, M['skin'], [-0.1, -0.14, -0.19, -0.24, -0.29, -0.35], seg=12)
        tint(cf, lambda p, n: mix3((1, 1, 1), (0.92, 0.78, 0.76), 0.6 * smooth01(-n.z, 0.3, 0.9)))
        kp.append(cf)
        kp.append(cs.line('calfline' + kn, [(-0.11, PI - sx * 0.5), (-0.18, PI - sx * 0.2), (-0.26, PI + sx * 0.25), (-0.33, PI + sx * 0.1)], 0.01, M['lines'], n=6))
        kp += boot(J, kn, sx)
        J.P.add(kn, kp)


def boot(J, kn, sx):
    """a steel-toe work boot, big: tan leather worn through to the cap, a lugged sole, speed hooks, a pull loop"""
    M = J.M; out = []
    SOLE_Y = -0.455
    # the foot: sections along z (heel +0.1 ... toe -0.28): a dome over a flat bottom
    stn = [(0.105, 0.034, 0.05), (0.09, 0.058, 0.098), (0.04, 0.068, 0.124), (-0.03, 0.073, 0.108), (-0.1, 0.078, 0.088), (-0.17, 0.082, 0.078), (-0.225, 0.08, 0.076), (-0.262, 0.064, 0.066), (-0.283, 0.035, 0.045)]
    def ring(i, t, grow=0.0):
        z, hw, hh = stn[i]; hw += grow; hh += grow
        out_ = [(hh * math.sin(PI * k / 8) ** 0.75, hw * math.cos(PI * k / 8)) for k in range(9)]
        return out_ + [(-0.004 - grow * 2.5, -hw * 0.6), (-0.004 - grow * 2.5, 0.0), (-0.004 - grow * 2.5, hw * 0.6)]
    cen = [(0, SOLE_Y + 0.03, z) for z, _, _ in stn]
    up = loft(cen, ring, M['boot'], name='boot' + kn, up=(0, 1, 0), close=(False, True))
    def scuff(p, n):
        c = (1, 1, 1)
        c = mix3(c, (0.62, 0.58, 0.56), 0.7 * smooth01(-p.z, 0.16, 0.26))            # worn dark toward the toe
        c = mix3(c, (0.7, 0.66, 0.62), 0.5 * smooth01(SOLE_Y + 0.07 - p.y, 0, 0.03))  # along the welt
        return c
    tint(up, scuff); out.append(up)
    # the steel cap, showing where the leather has gone
    cap_stn = [5, 6, 7, 8]
    capo = loft([(cen[i][0], cen[i][1], cen[i][2] - 0.0015 * k) for k, i in enumerate(cap_stn)], lambda i, t: ring(cap_stn[i], t, grow=0.004), M['steel'], name='toecap' + kn, up=(0, 1, 0), close=(False, True))
    tint(capo, lambda p, n: mix3((1, 1, 1), (0.6, 0.56, 0.52), 0.6 * smooth01(p.z, -0.25, -0.19)))
    out.append(capo)
    # the shaft round the ankle, padded collar, tongue, laces on hooks, pull loop
    sh = Surf([(-0.292, 0.074, 0.072, 0.078, 0, 0.03, 2.2), (-0.33, 0.07, 0.07, 0.074, 0, 0.03, 2.2), (-0.39, 0.068, 0.085, 0.072, 0, 0.026, 2.2), (-0.43, 0.066, 0.1, 0.07, 0, 0.022, 2.2)])
    J.S['shaft' + kn] = sh
    so = sh.mesh('shaft' + kn, M['boot'], [-0.292, -0.325, -0.36, -0.395, -0.43], seg=12)
    tint(so, scuff); out.append(so)
    out.append(sweep([tuple(sh.p(-0.292, TAU * i / 12, 0.004)) for i in range(13)], 0.011, M['belt'], seg=5, name='collar' + kn))
    # a metatarsal guard over the laces: a ribbed steel shield hinged at the ankle (the shin's piston bolts to it)
    def guard(u, v):
        z = -0.068 - 0.116 * v; y = -0.316 - 0.066 * v ** 1.25
        x = (u - 0.5) * (0.094 + 0.03 * v)
        return (x, y - 0.03 * (2 * u - 1) ** 2 * (0.6 + 0.4 * v) + 0.004 * math.cos(v * PI * 6), z - 0.004 * math.cos(v * PI * 6) * 0.3)
    out.append(sheet_mesh('metguard' + kn, M['steel'], guard, nu=4, nv=6, thick=0.008, uv=False))
    out.append(rod((-0.058, -0.314, -0.064), (0.058, -0.314, -0.064), 0.008, M['blued'], seg=6, name='guardpin' + kn))
    for s2 in (-1, 1): out.append(box((0.012, 0.04, 0.03), (s2 * 0.056, -0.312, -0.052), M['steel'], bev=0.003, name='guardlug'))
    out.append(tube([(-0.012, -0.3, 0.1), (-0.012, -0.262, 0.112), (0.012, -0.262, 0.112), (0.012, -0.3, 0.1)], 0.005, M['belt'], seg=4, name='pull' + kn))
    # the sole: a thick welted slab with a heel block and lugs
    def sring(i, t):
        z, hw, hh = stn[i]; hw += 0.009
        return [(0.0, hw * 0.94), (0.0, -hw * 0.94), (-0.008, -hw), (-0.03, -hw), (-0.03, hw), (-0.008, hw)]
    sole = loft([(0, SOLE_Y + 0.03, z - (0.008 if i == len(stn) - 1 else 0) + (0.006 if i == 0 else 0)) for i, (z, _, _) in enumerate(stn)], sring, M['sole'], name='sole' + kn, up=(0, 1, 0))
    out.append(sole)
    out.append(box((0.118, 0.022, 0.085), (0, SOLE_Y + 0.006, 0.058), M['sole'], bev=0.005, name='heel' + kn))
    for i in range(3): out.append(box((0.13, 0.012, 0.026), (0, SOLE_Y + 0.004, -0.07 - i * 0.07), M['sole'], name='lug'))
    return out


# ------------------------------------------------------------------------------------------------ arms and hands
UP, FO = JOINTS[ID]['joints']['arm'][1] - JOINTS[ID]['joints']['foreR'][1], 0.27   # (upper arm, forearm: the look's lengths)
UP = 0.27
WRIST = -(FO + 0.034)   # where the hand joint is, down the forearm


def arm_surf():
    return Surf([(0.112, 0.045, 0.045, 0.05, 0, 0.0, 2.1), (0.08, 0.106, 0.106, 0.112, 0, 0.0, 2.2), (0.02, 0.13, 0.128, 0.136, 0, 0.0, 2.3), (-0.05, 0.118, 0.122, 0.13, 0, 0.0, 2.2),
                 (-0.12, 0.11, 0.128, 0.12, 0, -0.006, 2.2), (-0.19, 0.098, 0.108, 0.102, 0, -0.002, 2.2), (-0.255, 0.086, 0.086, 0.094, 0, 0.0, 2.2), (-0.3, 0.083, 0.083, 0.088, 0, 0.0, 2.2)])


def arms(J):
    M = J.M
    for k, fk, hk, sx in (('armL', 'foreL', 'handL', -1), ('arm', 'foreR', 'handR', 1)):
        A = arm_surf(); J.S[k] = A
        up = A.mesh('upper' + k, M['skin'], [0.112, 0.08, 0.04, 0.0, -0.05, -0.1, -0.15, -0.2, -0.25, -0.3], seg=16, cap=(True, True))
        def at(p, n, sx=sx):
            c = mix3((1, 1, 1), (1.0, 0.86, 0.84), 0.5 * smooth01(p.y, -0.02, 0.1))          # sun on the shoulders
            c = mix3(c, (0.9, 0.7, 0.68), 0.7 * smooth01(-0.21 - p.y, 0, 0.07) * smooth01(n.z, -0.2, 0.7))   # the elbow, rough and red
            c = mix3(c, (1.08, 1.04, 1.02), 0.5 * smooth01(-sx * n.x, 0.3, 0.9) * gauss(p.y + 0.14, 0.09))        # paler inside the arm
            return c
        tint(up, at)
        J.P.add(k, [up])
        # the shoulder cap: plate under scar tissue, three rivets, a bare corner on the right one
        pl = [A.plate('plate_sh' + k, M['scar'], 0.01, sx * 1.35, 0.15, 0.2, off=0.007, n=3.2, spokes=16)]
        for (dy, da) in ((0.045, -0.5), (0.045, 0.5), (-0.05, -0.42), (-0.05, 0.42)):
            y, a = 0.01 + dy, sx * 1.35 + da
            pl.append(rivet(tuple(A.p(y, a, 0.007)), 0.008, M['steel'], tuple(A.n(y, a))))
        pl += A.stitches('stitch', M['lip'], 0.01, sx * 1.35, 0.15, 0.2, n=3.2, count=12, skip=(2,) if sx > 0 else ())
        if sx > 0: pl.append(A.plate('plate_sh_bare', M['steel'], 0.066, sx * 1.02, 0.036, 0.06, off=0.0095, n=2.5, spokes=8))
        # the anchor of the collarbone, bolted to the front of the shoulder
        pl.append(A.plate('anchor' + k, M['steel'], 0.0, sx * 0.12, 0.062, 0.062, off=0.008, n=2.6, spokes=10, sink=0.002))
        for i in range(3):
            t = TAU * i / 3 + 0.5; y, a = 0.0 + 0.018 * math.cos(t), sx * 0.12 + 0.14 * math.sin(t)
            pl.append(hexbolt(tuple(A.p(y, a, 0.008)), 0.0075, 0.007, M['blued'], tuple(A.n(y, a))))
        J.P.add(k, pl, 'plates')
        ln = [A.line('l_bi%s1' % k, [(0.0, sx * 0.3), (-0.07, sx * 0.1), (-0.15, -sx * 0.25), (-0.23, -sx * 0.5), (-0.29, -sx * 0.55)], 0.012, M['lines'], n=7),
              A.line('l_bi%s2' % k, [(-0.02, sx * 0.62), (-0.09, sx * 0.72), (-0.18, sx * 0.5), (-0.27, sx * 0.3)], 0.01, M['lines'], n=6),
              A.line('l_tri%s' % k, [(-0.06, sx * 2.5), (-0.14, sx * 2.3), (-0.22, sx * 2.6), (-0.29, sx * 2.5)], 0.011, M['lines'], n=6)]
        J.P.add(k, ln, 'lines')
        if sx < 0: forearm_left(J, fk, hk)


def forearm_left(J, fk, hk):
    """his own forearm: thick, lined, THIS WAY UP tattooed on it, rubber bands round the wrist. an open hand"""
    M = J.M; sx = -1
    F = Surf([(0.05, 0.086, 0.086, 0.098, 0, 0.004, 2.2), (-0.03, 0.11, 0.104, 0.11, 0, 0.0, 2.2), (-0.09, 0.114, 0.106, 0.108, 0, 0.0, 2.2), (-0.16, 0.098, 0.09, 0.094, 0, 0.0, 2.2),
              (-0.23, 0.078, 0.07, 0.074, 0, 0.0, 2.2), (-0.29, 0.066, 0.056, 0.058, 0, 0.0, 2.2), (-0.32, 0.064, 0.054, 0.056, 0, 0.0, 2.2)])
    J.S[fk] = F
    fo = F.mesh('fore' + fk, M['skin'], [0.05, 0.0, -0.045, -0.09, -0.135, -0.18, -0.225, -0.27, -0.32], seg=14, cap=(True, True))
    tint(fo, lambda p, n: mix3((1, 1, 1), (0.94, 0.8, 0.78), 0.5 * smooth01(p.y, -0.02, 0.05)))
    fp = [fo]
    tat = F.mesh('tattoo', M['tattoo'], [-0.15, -0.128, -0.106, -0.084, -0.062], seg=6, a0=-PI / 2 - 0.62, a1=-PI / 2 + 0.62, off=0.0016, uv=(1, 0, 0, 1))
    fp.append(tat)
    for i, dy in enumerate((0.0, 0.009, 0.017)):
        fp.append(sweep([tuple(F.p(-0.275 + dy + 0.003 * math.sin(a * 2 + i), a, 0.003)) for a in [TAU * j / 10 for j in range(11)]], 0.004, M['band'], seg=3, name='rubberband'))
    J.P.add(fk, fp)
    J.P.add(fk, [F.line('l_f1', [(0.02, sx * 0.4), (-0.05, sx * 0.15), (-0.13, -sx * 0.1), (-0.21, sx * 0.1), (-0.29, sx * 0.0)], 0.011, M['lines'], n=7),
                 F.line('l_f2', [(0.0, sx * 2.4), (-0.08, sx * 2.1), (-0.17, sx * 2.3), (-0.27, sx * 2.2)], 0.01, M['lines'], n=6)], 'lines')
    J.P.add(hk, open_hand(J, sx))


def open_hand(J, sx):
    """the left hand, relaxed and open (hand frame: wrist at 0, fingers down -y, the palm faces back +z, thumb forward)"""
    M = J.M; out = []
    hc = Vector((0, -0.095, 0.0))
    palm = blob('palm', tuple(hc), (0.074, 0.088, 0.04), M['skin'], fn=lambda p, n: -0.01 * max(0.0, n.z) * gauss(p.y, 0.05) + 0.006 * max(0.0, -n.z) * gauss(p.y - 0.03, 0.04), seg=14, rings=10)
    tint(palm, lambda p, n: mix3((1, 1, 1), (1.0, 0.82, 0.8), 0.6 * smooth01(n.z, 0.1, 0.7)))
    out.append(palm)
    out.append(limb('wrist', [(0, 0.02, 0), (0, -0.05, 0)], [0.058, 0.06], M['skin'], seg=10, squash=(0.85, 1.0)))
    for fi in range(4):
        fx = sx * (0.054 - fi * 0.036) * -1.0   # index nearest the thumb (the inner side: +x on a left hand)
        L = 1.0 - abs(fi - 1.3) * 0.11; cu = 0.55 + fi * 0.12
        b = Vector((fx, -0.168, 0.0))
        p1 = b + Vector((0, -0.058 * L, 0.012 * cu)); p2 = p1 + Vector((0, -0.04 * L, 0.03 * cu)); p3 = p2 + Vector((0, -0.024 * L, 0.03 * cu))
        f = limb('finger%d' % fi, [tuple(b + Vector((0, 0.02 + fi * 0.004, 0.002 * fi))), tuple(b), tuple(p1), tuple(p2), tuple(p3)], [0.021, 0.0215, 0.02, 0.018, 0.0145], M['skin'], seg=8)
        tint(f, lambda p, n: mix3((1, 1, 1), (1.0, 0.82, 0.8), 0.4))
        out.append(f)
        out.append(blob('nail%d' % fi, tuple(p3 + Vector((0, 0.004, -0.012))), (0.011, 0.011, 0.005), M['nail'], seg=6, rings=4))
        out.append(blob('knuck%d' % fi, tuple(b + Vector((0, 0.004, -0.014))), (0.02, 0.018, 0.014), M['skin'], seg=6, rings=4))
    tb = Vector((-sx * 0.066, -0.07, -0.012))
    out.append(limb('thumb', [tuple(tb + Vector((sx * 0.02, 0.03, 0.01))), tuple(tb), tuple(tb + Vector((-sx * 0.022, -0.05, -0.022))), tuple(tb + Vector((-sx * 0.026, -0.092, -0.036)))], [0.028, 0.027, 0.023, 0.018], M['skin'], seg=8))
    out.append(blob('thumbnail', tuple(tb + Vector((-sx * 0.03, -0.092, -0.048))), (0.012, 0.012, 0.005), M['nail'], seg=6, rings=4))
    return out
