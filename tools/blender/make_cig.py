# Cigarette + the Fat Cigar skin.
# Cigarette: a king-size filter cigarette (84 mm x 7.8 mm, 25 mm cork-pattern tipping paper) x2.2 long and a bit
# chunkier (20 mm) so it reads in the hand, filling the code model's 0.185 m from the ember to the filter. Paper with a
# glued seam, a gold brand band and a printed warning (MAY CAUSE JANK), a scorched burn line, a glowing ember with
# flakes of ash, a fibrous filter end.
# Fat Cigar: a fat gordo (152 mm x 60 ring gauge) x1.45: hand-rolled maduro wrapper with veins and the spiral seam,
# a rounded cut cap, a red and gold band, a long firm ash on a glowing foot.
# The ember (+ its ash) is the `tip` node: weapons.js swells it as you inhale. Glows never take a wrap.
# run: blender -b --python tools/blender/make_cig.py
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *


def ember_px(px):  # a glowing coal: hot orange with darker cracks and a few white-hot spots
    h, w = px.shape[:2]
    r = np.random.default_rng(5)
    px[:] = hexrgb(0xff6a1a)[None, None] * (0.85 + 0.15 * r.random((h, w, 1)))
    for k in range(6): px_line(px, r.integers(0, w), r.integers(0, h), r.integers(0, w), r.integers(0, h), 0x7a1000, 1.0)
    px[r.random((h, w)) < 0.06] = hexrgb(0xffd860)


def flakes(n, z0, r, size, m, seed, spread=0.004):
    """little grey flakes of ash stuck round an ember's front rim"""
    rng = random.Random(seed); out = []
    for i in range(n):
        a = 2 * math.pi * (i + rng.random() * 0.6) / n
        rr = r * rng.uniform(0.75, 1.02)
        f = box((size * rng.uniform(0.8, 1.4), size * rng.uniform(0.5, 0.9), size * rng.uniform(0.6, 1.1)),
                (math.cos(a) * rr, math.sin(a) * rr, z0 - rng.uniform(0, spread)), m, rot=(rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), a))
        out.append(jitter(f, size * 0.18, seed + i))
    return out


def cigarette():
    R = 0.0099
    Z_BURN, Z_JOIN, Z_END = -0.0875, 0.026, 0.0775
    def paper_px(px):  # u = 0 at the filter, 1 at the burning end (so the print reads left to right on the right side)
        h, w = px.shape[:2]
        rng = np.random.default_rng(4)
        px[:] = hexrgb(0xf3f1ea) * (0.97 + 0.03 * rng.random((h, w, 1)))
        px[:, :, :] *= 1.0 - 0.05 * ((np.arange(w) % 7) == 0)[None, :, None]  # laid paper lines
        px[int(h * 0.62):int(h * 0.62) + 1] = hexrgb(0xdcd8cc)  # the glued seam, underneath
        for x in range(w):  # scorch toward the burn line
            k = max(0.0, (x / w - 0.86) / 0.14)
            px[:, x] = px[:, x] * (1 - 0.75 * k ** 1.6) + hexrgb(0x5a3214) * 0.75 * k ** 1.6
        for x0 in (6, 10): px[:, x0:x0 + 1] = hexrgb(0xc8a040)  # gold brand band next to the filter
        text_px(px, 'MAY CAUSE JANK', 18, int(h * 0.80), 1, 0x8a1a2a)
        text_px(px, 'JANK LIGHTS', 18, int(h * 0.06), 1, 0x9a7a2a)
    def cork_px(px):
        h, w = px.shape[:2]
        rng = np.random.default_rng(11)
        lo = np.kron(rng.random((h // 4, w // 4)), np.ones((4, 4)))[:h, :w]
        n = 0.55 * lo + 0.45 * rng.random((h, w))
        px[:] = hexrgb(0xd88a3c)[None, None] * (0.86 + 0.24 * n[:, :, None])
        px[rng.random((h, w)) < 0.10] = hexrgb(0xa85a20)
        px[rng.random((h, w)) < 0.05] = hexrgb(0xf2b868)
        px[:, w - 4:w - 2] = hexrgb(0xe8c050)  # gold line at the join
    paper = mat('cg_paper', 0xffffff, rough=0.62, tex=tex_canvas('cg_paper_t', 128, 32, paper_px))
    cork = mat('cg_cork', 0xffffff, rough=0.42, clearcoat=0.25, tex=tex_canvas('cg_cork_t', 64, 32, cork_px))
    fibre = mat('cg_fibre', 0xffffff, rough=0.95, tex=tex_noise('cg_fibre_t', 0xf2ecdc, var=0.06, size=16, speck=0xd8cfb8, speck_p=0.2, seed=3))
    char = mat('cg_char', 0x2a160a, rough=0.9, emit=0x3a0a00, strength=0.6)
    ember = mat('cg_ember', 0xffffff, rough=0.8, emit=0xffffff, strength=4.0, tex=tex_canvas('cg_ember_t', 16, 16, ember_px), emit_tex=True)
    ash = mat('cg_ash', 0xffffff, rough=0.95, emit=0x0a0402, strength=0.3,
              tex=tex_noise('cg_ash_t', 0x6e6a64, var=0.2, size=16, speck=0xb8b4ac, speck_p=0.18, seed=8))
    parts = []; A = parts.append
    rod = lathe([(R * 0.97, Z_BURN), (R, Z_BURN + 0.004), (R, Z_JOIN)], m=paper, seg=24, cap=False, name='rod')
    uv_cyl(rod, 'z', Z_JOIN, Z_BURN, turn=0.0); A(rod)
    tip_p = lathe([(R + 0.0002, Z_JOIN), (R + 0.0002, Z_END - 0.0005), (R * 0.97, Z_END)], m=cork, seg=24, cap=False, name='tipping')
    uv_cyl(tip_p, 'z', Z_END, Z_JOIN); A(tip_p)
    A(lathe([(R * 0.97, Z_END - 0.0012), (0.0, Z_END - 0.0012)], m=fibre, seg=24, name='filter_end'))
    A(lathe([(R * 0.965, Z_JOIN - 0.0005), (R * 0.965, Z_JOIN + 0.0005)], m=paper, seg=24, name='join_fill'))  # no gap at the join
    A(jitter(lathe([(R * 1.015, Z_BURN + 0.0012), (R * 1.03, Z_BURN), (R * 0.9, Z_BURN - 0.0012)], m=char, seg=18, name='burnline'), 0.0004, 5))
    # the ember (+ ash flakes): the `tip` node, origin at its middle so it swells in place
    emb = lathe([(R * 0.985, Z_BURN + 0.0005), (R * 1.0, -0.092), (R * 0.95, -0.0975), (R * 0.78, -0.1015), (R * 0.45, -0.1038), (0.0, -0.1045)], m=ember, seg=18, name='ember')
    jitter(emb, 0.00035, 9); uv_box(emb, 0.01)
    tip = part([emb] + flakes(10, -0.0965, R * 0.97, 0.0019, ash, 21, spread=0.002), 'tip', pivot=(0, 0, -0.094))
    for p in parts: p.select_set(False)
    WZ = {'cg_cork': 'a', 'cg_fibre': 'a', 'cg_paper': 'b'}
    meta = {'kind': 'weapon', 'id': 'cig', 'paint': ['cg_cork'], 'muzzle': [0, 0, -0.11], 'tip': 'tip',
            'hatAt': [[0, R + 0.0002, 0.055], 0.04]}
    return finish('w_cig', zone_join(parts, 'cig_body', WZ, default='n') + [tip], meta)


def cigar():
    S = 1.45 / 1000
    R = 0.0205
    Z_FOOT, Z_HEAD = -0.104, 0.116
    rng = random.Random(3)
    def wrapper_px(px):  # u along the cigar, v round it: maduro leaf, veins, the spiral seam
        h, w = px.shape[:2]
        r = np.random.default_rng(6)
        lo = np.kron(r.random((h // 8, w // 8)), np.ones((8, 8)))[:h, :w]
        px[:] = hexrgb(0x6a3a1c)[None, None] * (0.82 + 0.3 * (0.6 * lo + 0.4 * r.random((h, w)))[:, :, None])
        for k in range(7):  # veins run diagonally off the leaf's midrib
            x0, y0 = r.integers(0, w), r.integers(0, h)
            px_line(px, x0, y0, x0 + 26, y0 + 9, 0x9a6438, 1.0)
        for x in range(w):  # the spiral seam
            y = int((x * h / 64 + 3) % h); px[y, x] = hexrgb(0x3a1e0c); px[(y + 1) % h, x] = hexrgb(0x8a5430)
    def band_px(px):
        h, w = px.shape[:2]
        px[:] = hexrgb(0xb81c2c)
        px[:2] = px[-2:] = hexrgb(0xe8c050); px[3:4] = px[-4:-3] = hexrgb(0x6a0a14)
        for k in range(2):
            x0 = 6 + k * (w // 2)
            text_px(px, 'JANKFIRE', x0, 4, 1, 0xf2d060)
            px_disc(px, x0 + 54, h / 2, 4.5, 0xf2d060); px_disc(px, x0 + 54, h / 2, 2.5, 0xb81c2c); px_disc(px, x0 + 54, h / 2, 1.2, 0xf2d060)
    wrap = mat('cc_wrapper', 0xffffff, rough=0.5, clearcoat=0.2, tex=tex_canvas('cc_wrapper_t', 128, 48, wrapper_px))
    band = mat('cc_band', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('cc_band_t', 160, 15, band_px))
    filler = mat('cc_filler', 0xffffff, rough=0.95, tex=tex_noise('cc_filler_t', 0x8a5a2a, var=0.25, size=16, speck=0x4a2a10, speck_p=0.3, seed=2))
    char = mat('cc_char', 0x24140a, rough=0.9, emit=0x3a0a00, strength=0.6)
    ember = mat('cc_ember', 0xffffff, rough=0.8, emit=0xffffff, strength=3.0, tex=tex_canvas('cc_ember_t', 16, 16, ember_px), emit_tex=True)
    def ash_px(px):  # firm cigar ash: grey bands (each puff) with darker seams and pale flecks
        h, w = px.shape[:2]
        r = np.random.default_rng(13)
        for x in range(w): px[:, x] = hexrgb(0x8a867e if (x // 3) % 2 else 0x6a665f)
        px[:] *= (0.88 + 0.2 * r.random((h, w, 1)))
        px[r.random((h, w)) < 0.12] = hexrgb(0xc8c4bc)
    ash = mat('cc_ash', 0xffffff, rough=0.95, emit=0x0a0402, strength=0.3, tex=tex_canvas('cc_ash_t', 16, 16, ash_px))
    parts = []; A = parts.append
    # hand rolled: the radius wanders a little along the length; the head rounds over into a cut cap
    prof = [(R * 0.97, Z_FOOT)]
    for i in range(1, 12):
        z = Z_FOOT + (0.098 - Z_FOOT) * i / 11
        prof.append((R * (1 + 0.012 * math.sin(i * 1.7) + rng.uniform(-0.006, 0.006)), z))
    prof += [(R * 0.97, 0.104), (R * 0.86, 0.11), (R * 0.68, 0.1145), (R * 0.56, Z_HEAD)]
    body = lathe(prof, m=wrap, seg=28, cap=False, name='body')
    uv_cyl(body, 'z', Z_HEAD, Z_FOOT); A(body)
    A(lathe([(R * 0.56, Z_HEAD - 0.0004), (0.0, Z_HEAD - 0.001)], m=filler, seg=20, name='cut'))
    bd = lathe([(R * 1.035, 0.048), (R * 1.04, 0.05), (R * 1.04, 0.078), (R * 1.035, 0.08)], m=band, seg=28, cap=False, name='band')
    uv_cyl(bd, 'z', 0.048, 0.08, turn=math.pi / 2 - 0.5); A(bd)
    # the band's picture runs round it, so the uvs go the other way: u round, v along
    me = bd.data; uvl = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices: u, v = uvl[li].uv; uvl[li].uv = (v, u)
    A(jitter(lathe([(R * 1.005, Z_FOOT + 0.0015), (R * 1.02, Z_FOOT + 0.0003), (R * 0.98, Z_FOOT - 0.0004)], m=char, seg=20, name='burnline'), 0.0004, 4))
    emb = lathe([(R * 0.985, Z_FOOT), (R * 0.99, Z_FOOT - 0.003), (R * 0.95, Z_FOOT - 0.0055)], m=ember, seg=20, name='ember')
    jitter(emb, 0.0004, 7); uv_box(emb, 0.012)
    ashc = lathe([(R * 0.9, Z_FOOT - 0.005), (R * 0.93, -0.112), (R * 0.92, -0.117), (R * 0.8, -0.1205), (R * 0.4, -0.1215), (0.0, -0.1215)],
                 m=ash, seg=20, name='ash')
    uv_cyl(ashc, 'z', Z_FOOT, -0.1215)
    jitter(ashc, 0.0007, 12)
    tip = part([emb, ashc], 'tip', pivot=(0, 0, Z_FOOT - 0.003))
    WZ = {'cc_wrapper': 'a', 'cc_filler': 'a', 'cc_band': 'n'}
    meta = {'kind': 'weapon', 'id': 'cig', 'skin': 'cig_cigar', 'paint': ['cc_wrapper'], 'muzzle': [0, 0, -0.11], 'tip': 'tip',
            'hatAt': [[0, R * 1.04, 0.064], 0.045]}
    return finish('w_cig_cigar', zone_join(parts, 'cigar_body', WZ, default='n') + [tip], meta)


main_multi(lambda: [(cigarette(), "w_cig"), (cigar(), "w_cig_cigar")], exposure=-0.8)
