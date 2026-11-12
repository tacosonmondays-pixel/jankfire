# THE FOUNDER (Suburb's park plaza; Suburb S&D's cul-de-sac): the estate's monument, drawn over its own boxes (shared/map.js
# founder(): the stone slab, the lawn, the chrome block, the googly cube, the plaque, the four cube hedges), which stay
# what you bump into. A raised planter of dressed granite blocks with a mowed lawn on it (HOA stripes), four clipped
# box topiaries, a ring of mulch and tulips round the plinth with an uplight at each corner, a KEEP OFF THE GRASS stake.
# The plinth is polished pink granite (stepped base, die with dark inset panels, a moulded cornice), a brass plaque on
# the front (OUR FOUNDER / HE OWNED ALL OF THIS / 1953 - ONGOING) and a small one on the back. On it the founder himself,
# as a giant glossy vinyl toy bust like the googly cube he replaces: a navy suit with lapels, a white shirt, a red tie and
# a gold pin, a rounded toy head in the same orange with the same disagreeing googly eyes, one under a gold monocle on a
# chain, a smug brow, a handlebar moustache, the maroon grin with two buck teeth, a top hat with a pink band, cocked, and
# a pigeon on the hat (it has been busy: the hat and a shoulder show it).
# Prop space: the plaza's middle on the ground, front (the plaque) -z, game metres at Suburb's sizes; the game fits it
# onto each copy's boxes (meta.box = their extent), so S&D's slightly taller slab (+0.1) stretches it a hair.
# blender52 -b --python tools/blender/make_founder.py [-- --no-export --qa --sheet --only=founder,founder_sd]
import os, sys, math, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from rpkit import *  # noqa (lib + Buf, Atlas, prims, qa, export_glb, compact_glb, bake_ao, final_colour, shot, contact)
from rpkit import _link
import lib

# the two copies: Suburb's planter is 0.4 tall on the grass; S&D's stands on the cul-de-sac's road and is 0.5 tall, so it
# gets its own file with the kerb 0.1 taller and everything on it 0.1 higher (one stretched model would float the lawn)
VARIANTS = {'founder': 0.0, 'founder_sd': 0.1}
ID, FID, DY = 'founder', 'p_founder', 0.0
LAWN_Y = 0.5                                  # the lawn's top (the boxes': the slab 0..0.4, the lawn 0.4..0.5)


# ------------------------------------------------------------ the three textures
def atlases():
    S = Atlas('fd_stone_a', 128, 128, rough=0.7)
    S.cell('kerb', 0, 0, 32, 32, 0x847e78, rough=0.82, var=0.08, seed=3, speck=0x5c5852, speck_p=0.14)
    S.cell('pink', 32, 0, 32, 32, 0xc8848a, rough=0.2, var=0.05, seed=4, speck=0x9a5862, speck_p=0.22)
    S.cell('dark', 64, 0, 32, 32, 0x9a5a66, rough=0.14, var=0.04, seed=5, speck=0x7a4450, speck_p=0.18)
    S.cell('mulch', 96, 0, 16, 16, 0x5a3220, rough=0.95, var=0.28, seed=6, speck=0x3a1c10, speck_p=0.3)
    S.cell('soil', 112, 0, 16, 16, 0x6a4a2a, rough=0.95, var=0.2, seed=7)
    S.cell('leaf', 96, 16, 16, 16, 0x2f8a2a, rough=0.72, var=0.30, seed=8, speck=0x1d5a1a, speck_p=0.25)
    S.cell('leaf2', 112, 16, 16, 16, 0x3fa034, rough=0.72, var=0.30, seed=9, speck=0x7dcf4f, speck_p=0.12)
    S.cell('turf', 96, 32, 32, 16, 0x358a28, rough=0.92, var=0.18, seed=10)
    # the lawn: mowed stripes the HOA measures with a ruler
    lw = S.cell('lawn', 0, 32, 64, 64, 0x3a9a2c, rough=0.92, var=0.12, seed=11)
    for k in range(0, 64, 16): lw[:, k:k + 8] *= 0.86
    r = np.random.default_rng(12); lw[r.random((64, 64)) < 0.04] = hexrgb(0x6cc048)
    # the stake's sign
    sg = S.cell('sign', 0, 96, 128, 32, 0xf8f4ec, rough=0.4)
    sg[0:2, :] = sg[-2:, :] = hexrgb(0xff3030); sg[:, 0:2] = sg[:, -2:] = hexrgb(0xff3030)
    text_px(sg, 'KEEP OFF THE GRASS', 10, 6, 1, 0xff3030); text_px(sg, 'OR ELSE.  - THE HOA', 8, 18, 1, 0x141018)
    C = Atlas('fd_candy_a', 64, 64, rough=0.28)
    SW = [('orange', 0xffb31a), ('navy', 0x2a3a9a), ('navy2', 0x1c2670), ('white', 0xf4f0ea), ('red', 0xe0203a), ('maroon', 0x7a0a2a),
          ('black', 0x141018), ('brown', 0x5a2a14), ('pink', 0xff4fd8), ('blush', 0xff7a9a), ('hat', 0x1e1626), ('pgrey', 0x8a90a0),
          ('pneck', 0x3a8a7a), ('beak', 0x45454e), ('feet', 0xff8aa0), ('poop', 0xf2f0e2), ('fpink', 0xff4fd8), ('fyel', 0xffe14d),
          ('fred', 0xff3030), ('fwhite', 0xfff4f4), ('stem', 0x3aa030), ('pdark', 0x5a6070)]
    for i, (k, c) in enumerate(SW): C.cell(k, (i % 8) * 8, (i // 8) * 8, 8, 8, c, rough=0.22 if k not in ('poop', 'stem', 'pgrey', 'pneck', 'pdark') else 0.6)
    tg = C.cell('tag', 0, 40, 64, 16, 0xfff4d0, rough=0.5)
    tg[0:1, :] = tg[-1:, :] = hexrgb(0xff4fd8); tg[:, 0:1] = tg[:, -1:] = hexrgb(0xff4fd8)
    text_px(tg, 'NOT A TOY', 5, 4, 1, 0xe0203a)
    M = Atlas('fd_metal_a', 192, 64, rough=0.3, metal=1.0)
    pl = M.cell('plaque', 0, 0, 144, 48, 0xd8a838, rough=0.32, metal=1.0, var=0.05, seed=13)
    pl[0:2, :] = pl[-2:, :] = hexrgb(0x8a6420); pl[:, 0:2] = pl[:, -2:] = hexrgb(0x8a6420)
    pl[4:5, 4:-4] = pl[-5:-4, 4:-4] = hexrgb(0x9a7428)
    ink = 0x2a1a08
    text_px(pl, 'OUR FOUNDER', 6, 8, 2, ink); text_px(pl, 'HE OWNED ALL OF THIS', 12, 27, 1, ink); text_px(pl, '1953 - ONGOING', 30, 37, 1, ink)
    M.cell('brass', 144, 0, 16, 16, 0xd8a838, rough=0.3, metal=1.0, var=0.04, seed=14)
    M.cell('gold', 160, 0, 16, 16, 0xffc838, rough=0.14, metal=1.0, var=0.03, seed=15)
    M.cell('steel', 176, 0, 16, 16, 0x8a9098, rough=0.38, metal=1.0, var=0.05, seed=16)
    M.cell('lens', 144, 16, 16, 16, 0xfff0c0, rough=0.2, metal=0.0)
    bp = M.cell('back', 0, 48, 192, 16, 0xd8a838, rough=0.32, metal=1.0, var=0.05, seed=17)
    bp[0:1, :] = bp[-1:, :] = hexrgb(0x8a6420)
    text_px(bp, 'PLEASE DO NOT LICK THE FOUNDER', 6, 4, 1, ink)
    em = np.zeros_like(M.px); x, y, w, h = M.R['lens']; em[y:y + h, x:x + w] = hexrgb(0xfff0c0)
    ms = S.material('fd_stone', rough=0.7, use_orm=True, metal_map=False)
    mc = C.material('fd_candy', rough=0.25, use_orm=True, metal_map=False)
    b = mc.node_tree.nodes['Principled BSDF']; b.inputs['Coat Weight'].default_value = 0.7; b.inputs['Coat Roughness'].default_value = 0.06
    mm = M.material('fd_metal', rough=0.3, metal=1.0, use_orm=True, emit_px=em, strength=2.0)
    return S, C, M, ms, mc, mm


# ------------------------------------------------------------ shapes
def rbox(hx, hy, hz, k=24, rows=10, n=3.2, nv=None, y_lo=-1.0, y_hi=1.0):
    """a rounded toy box (superellipse in plan and in height), centred, poles on y; y_lo / y_hi cut it flat"""
    nv = nv or n; R = []
    for i in range(rows + 1):
        t = lerp(y_lo, y_hi, i / rows)
        s = max(1e-3, (1 - abs(t) ** nv) ** (1 / nv)) if abs(t) < 1 else 1e-3
        R.append(superring(t * hy, hx * s, hz * s, k, n))
    return p_loft(R, cap0=y_lo > -1, cap1=y_hi < 1, tip0=None if y_lo > -1 else V3((0, -hy, 0)), tip1=None if y_hi < 1 else V3((0, hy, 0)))


def cbox(x0, y0, z0, x1, y1, z1, ch=0.02, bottom=False):
    """a block with its top edges chamfered (kerb stones, steps)"""
    def rect(y, d): return [V3((x0 + d, y, z0 + d)), V3((x1 - d, y, z0 + d)), V3((x1 - d, y, z1 - d)), V3((x0 + d, y, z1 - d))]
    return orient_from(p_loft([rect(y0, 0), rect(y1 - ch, 0), rect(y1, ch)], cap0=bottom, cap1=True), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def lathe_p(profile, k=20):
    """(r, y) profile turned round y -> a closed solid of revolution (the hat)"""
    tips = [V3((0, profile[i][1], 0)) if profile[i][0] < 1e-6 else None for i in (0, -1)]
    R = [[V3((math.sin(2 * math.pi * j / k) * r, y, math.cos(2 * math.pi * j / k) * r)) for j in range(k)] for r, y in profile if r > 1e-6]
    return p_loft(R, tip0=tips[0], tip1=tips[1])  # (profile: out along the bottom, up, back in along the top: faces look out)


def lin(rows, y):
    """interpolate (y, hx, hz, n) rows at y"""
    for a, b in zip(rows, rows[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0]); return tuple(lerp(a[i], b[i], t) for i in range(1, 4))
    r = rows[0] if y < rows[0][0] else rows[-1]; return r[1:]


def front_z(rows, x, y, off=0.0):
    """the -z face of a superellipse loft at (x, y), pushed out by off"""
    hx, hz, n = lin(rows, y)
    u = min(0.999, abs(x) / hx)
    return -(hz * (1 - u ** n) ** (1 / n)) - off


# ------------------------------------------------------------ the parts
HEAD_C, HEAD = 4.7, (1.55, 1.25, 1.45)
BUST = [(2.40, 1.72, 1.40, 3.0), (2.80, 1.74, 1.42, 3.0), (3.10, 1.66, 1.34, 2.8), (3.30, 1.40, 1.12, 2.5), (3.45, 0.95, 0.80, 2.2), (3.58, 0.62, 0.56, 2.0)]


def head_z(x, y, off=0.0):
    hx, hy, hz = HEAD; n = 3.2
    t = (y - HEAD_C) / hy; s = max(1e-3, (1 - min(0.999, abs(t)) ** n) ** (1 / n))
    u = min(0.999, abs(x) / (hx * s))
    return -(hz * s * (1 - u ** n) ** (1 / n)) - off


def patch(fx, ys, xs_of, zfn, off):
    """a sheet conforming to a surface: rows at ys, each row's x from xs_of(y) (same count), z = zfn(x, y, off)"""
    P = [[V3((x, y, zfn(x, y, off))) for x in xs_of(y)] for y in ys]
    return p_grid(P, flip=True)


def build(lod):
    S, C, M, ms, mc, mm = A_
    st, cd, mt = Buf('fd_stone_' + lod), Buf('fd_candy_' + lod), Buf('fd_metal_' + lod)
    hi = lod == 'lod0'
    # ---- the planter: dressed granite blocks round the edge, the lawn on top
    if hi:
        for side in range(4):
            n = 8 if side < 2 else 7
            a0, a1 = (-5.0, 5.0) if side < 2 else (-4.5, 4.5)
            L = (a1 - a0) / n
            for i in range(n):
                s0, s1 = a0 + i * L + 0.0008, a0 + (i + 1) * L - 0.0008  # (joints 1.6 mm: the chamfers read as the joints)
                jy = 0.4 - 0.008 * ((i * 7 + side * 3) % 3)  # (a few sit a touch low)
                if side == 0: pr = cbox(s0, 0, -5.0, s1, jy, -4.5, 0.03)
                elif side == 1: pr = cbox(s0, 0, 4.5, s1, jy, 5.0, 0.03)
                elif side == 2: pr = cbox(-5.0, 0, s0, -4.5, jy, s1, 0.03)
                else: pr = cbox(4.5, 0, s0, 5.0, jy, s1, 0.03)
                st.add(pr, ms, S.quad('kerb'))
    else:
        for (x0, z0, x1, z1) in ((-5, -5, 5, -4.5), (-5, 4.5, 5, 5), (-5, -4.5, -4.5, 4.5), (4.5, -4.5, 5, 4.5)):
            st.add(cbox(x0, 0, z0, x1, 0.4, z1, 0.0), ms, S.quad('kerb'))
    # the turf rolls over the edge of the soil onto the stones' inner edge
    def sq(y, h): return [V3((-h, y, -h)), V3((h, y, -h)), V3((h, y, h)), V3((-h, y, h))]
    st.add(orient_from(p_loft([sq(0.36, 4.5), sq(0.47, 4.49), sq(LAWN_Y, 4.43)]), (0, 0, 0)), ms, S.quad('turf'))
    st.add(p_quad((-4.43, LAWN_Y, 4.43), (4.43, LAWN_Y, 4.43), (4.43, LAWN_Y, -4.43), (-4.43, LAWN_Y, -4.43)), ms, S.fit('lawn'))
    # the mulch ring round the plinth (a frame of four beds) and the tulips in it
    for (x0, z0, x1, z1) in ((-2.2, -2.2, 2.2, -1.405), (-2.2, 1.405, 2.2, 2.2), (-2.2, -1.405, -1.405, 1.405), (1.405, -1.405, 2.2, 1.405)):
        st.add(cbox(x0, LAWN_Y - 0.02, z0, x1, LAWN_Y + 0.035, z1, 0.015), ms, S.quad('mulch'))
    if hi:
        cols = ['fpink', 'fyel', 'fred', 'fwhite']; k = 0
        for ring_d in (1.62, 1.98):
            pts = []
            for side in range(4):
                for i in range(6):
                    a = -ring_d + (i + 0.5 + 0.35 * (ring_d > 1.8)) * (2 * ring_d / 6.4)
                    pts.append([(a, -ring_d), (ring_d, a), (-a, ring_d), (-ring_d, -a)][side])
            for (x, z) in pts:
                h = 0.2 + 0.07 * ((k * 5) % 3)
                bx, bz = x + 0.03 * math.sin(k * 2.1), z + 0.03 * math.cos(k * 1.7)
                cd.add(p_prism(4, 0.012, h + 0.04, top=False), mc, C.fit('stem'), M=T(bx, LAWN_Y + 0.03, bz) @ RX(-math.pi / 2) @ RY(0.15 * math.sin(k)))
                cd.add(p_prism(6, 0.045, 0.085, r1=0.062, dome=0.015, bottom=True), mc, C.fit(cols[k % 4]), M=T(bx, LAWN_Y + 0.03 + h, bz) @ RX(-math.pi / 2))
                k += 1
    # an uplight at each corner of the bed, tipped at the founder
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * 1.8, sz * 1.8
            Mx = T(x, LAWN_Y + 0.02, z) @ frame(V3((-sx * 0.35, 1, -sz * 0.35)).normalized())
            mt.add(p_prism(10 if hi else 6, 0.1, 0.16, top=False), mm, M.quad('steel'), M=Mx)
            mt.add(p_prism(10 if hi else 6, 0.085, 0.165), mm, M.fit('lens'), M=Mx)
    # four clipped box topiaries on the corners of the lawn (their boxes: 1.2 cubes)
    for sx in (-1, 1):
        for sz in (-1, 1):
            leafy = 'leaf' if (sx + sz) % 4 else 'leaf2'
            if hi: st.add(rbox(0.63, 0.63, 0.63, k=20, rows=9, n=3.6, nv=4.5, y_lo=-0.97, y_hi=0.96), ms, S.quad(leafy), M=T(sx * 3.5, 1.1, sz * 3.5) @ RY(0.3 * sx * sz), jit=0.035, jf=4.5)
            else: st.add(p_box(1.2, 1.2, 1.2, taper=0.85), ms, S.quad(leafy), M=T(sx * 3.5, 1.1, sz * 3.5) @ RX(-math.pi / 2))
    # KEEP OFF THE GRASS, on a stake at the front of the lawn
    if hi:
        cd.add(p_box(0.04, 0.62, 0.04), mc, C.fit('white'), M=T(0.0, LAWN_Y + 0.27, -4.05))
        st.add(p_box(0.56, 0.16, 0.02), ms, S.face('sign', '-z'), M=T(0.0, LAWN_Y + 0.62, -4.08) @ RX(-0.12) @ SC(1, 1, 1))

    # ---- the plinth: polished pink granite, stepped base, die, moulded cornice (boxes: 2.8 square, 0.5..2.4)
    kk = 24 if hi else 8; nn = 9.0
    def sring(y, h): return superring(y, h, h, kk, nn, phase=math.pi / kk)
    st.add(p_loft([sring(LAWN_Y - 0.02, 1.4), sring(0.72, 1.4), sring(0.76, 1.36), sring(0.78, 1.32), sring(2.12, 1.32), sring(2.16, 1.36),
                   sring(2.24, 1.4), sring(2.4, 1.4)], cap1=True), ms, S.quad('pink'))
    if hi:  # dark inset panels on the three plain faces, the plaque on the front
        for (cx, cz, ax) in ((1.322, 0, 'x'), (-1.322, 0, 'x'), (0, 1.322, 'z')):
            if ax == 'x': pr = p_box(0.012, 0.98, 1.9); Mx = T(cx, 1.45, 0)
            else: pr = p_box(1.9, 0.98, 0.012); Mx = T(0, 1.45, cz)
            st.add(orient_from(pr, (0, 0, 0)), ms, S.quad('dark'), M=Mx)
        mt.add(p_box(1.72, 0.58, 0.04), mm, M.face('plaque', '-z'), M=T(0, 1.42, -1.335))
        for bx in (-0.8, 0.8):
            for by in (1.18, 1.66):
                mt.add(p_prism(6, 0.025, 0.015), mm, M.quad('brass'), M=T(bx, by, -1.355) @ RY(math.pi))
        mt.add(p_box(1.5, 0.13, 0.025), mm, M.face('back', 'z'), M=T(0, 1.75, 1.334))
    # ---- the founder: a giant vinyl toy bust (boxes: a 3.6 cube from 2.4)
    kb = 28 if hi else 8
    rings = [superring(y, hx, hz, kb, n) for (y, hx, hz, n) in BUST]
    cd.add(p_loft(rings, cap0=True, tip1=V3((0, BUST[-1][0] + 0.05, 0))), mc, C.fit('navy'))
    if hi:
        # the shirt's V, the lapels, the tie and its pin, a pocket square
        ys = [2.55 + i * 0.9 / 6 for i in range(7)]
        w = lambda y: 0.04 + (y - 2.55) / 0.9 * 0.5
        cd.add(patch(None, ys, lambda y: [lerp(-w(y), w(y), j / 4) for j in range(5)], lambda x, y, o: front_z(BUST, x, y, o), 0.012), mc, C.fit('white'))
        for s in (-1, 1):
            cd.add(patch(None, [2.5 + i * 0.95 / 6 for i in range(7)], lambda y, s=s: [s * (w(min(3.45, max(2.55, y))) + 0.01 + 0.35 * j / 3) for j in range(4)][::s],
                         lambda x, y, o: front_z(BUST, x, y, o), 0.03), mc, C.fit('navy2'))
        tw = lambda y: 0.12 + (3.3 - y) * 0.09
        cd.add(patch(None, [2.62 + i * 0.68 / 5 for i in range(6)], lambda y: [lerp(-tw(y), tw(y), j / 2) for j in range(3)], lambda x, y, o: front_z(BUST, x, y, o), 0.045), mc, C.fit('red'))
        cd.add(rbox(0.17, 0.12, 0.08, k=8, rows=3, n=3), mc, C.fit('red'), M=T(0, 3.37, front_z(BUST, 0, 3.37, 0.08)))
        cd.add(p_quad((0, 2.66, front_z(BUST, 0, 2.66, 0.047)), (0.17, 2.62, front_z(BUST, 0.17, 2.62, 0.046)), (0, 2.5, front_z(BUST, 0, 2.5, 0.046)), (-0.17, 2.62, front_z(BUST, -0.17, 2.62, 0.046))), mc, C.fit('red'))  # (the tie's point)
        mt.add(p_box(0.3, 0.04, 0.03), mm, M.quad('gold'), M=T(0, 3.0, front_z(BUST, 0, 3.0, 0.06)))
        px_, py_ = 1.02, 3.02
        cd.add(p_quad((px_ - 0.06, py_ + 0.2, front_z(BUST, px_ - 0.06, py_ + 0.2, 0.035)), (px_ + 0.1, py_ + 0.16, front_z(BUST, px_ + 0.1, py_ + 0.16, 0.035)),
                      (px_ + 0.18, py_, front_z(BUST, px_ + 0.18, py_, 0.035)), (px_ - 0.18, py_, front_z(BUST, px_ - 0.18, py_, 0.035))), mc, C.fit('pink'))  # (the pocket square)
        for by in (2.52,):
            mt.add(p_prism(8, 0.05, 0.03, dome=0.01), mm, M.quad('gold'), M=T(w(2.55) + 0.2, by, front_z(BUST, w(2.55) + 0.2, by, 0.02)) @ RY(math.pi))
        # the white collar round the neck
        cd.add(p_loft([superring(3.5, 0.66, 0.6, 16, 2.2), superring(3.68, 0.6, 0.55, 16, 2.2)]), mc, C.fit('white'))
    # the head: a rounded toy box in the googly cube's orange
    hx, hy, hz = HEAD
    cd.add(rbox(hx, hy, hz, k=32 if hi else 10, rows=14 if hi else 5, n=3.2), mc, C.fit('orange'), M=T(0, HEAD_C, 0))
    # googly eyes: they don't agree on where to look (like the cube's)
    for ex, (pdx, pdy) in ((-0.62, (0.09, -0.07)), (0.62, (-0.05, -0.1))):
        ey = 5.02; z0 = head_z(ex, ey, -0.1)
        F = T(ex, ey, z0) @ RX(math.pi)  # local +z -> game -z
        cd.add(p_prism(20 if hi else 8, 0.47, 0.24), mc, C.fit('black'), M=F)
        cd.add(p_prism(20 if hi else 8, 0.43, 0.25, dome=0.05), mc, C.fit('white'), M=F)
        cd.add(p_prism(14 if hi else 6, 0.19, 0.31, dome=0.02, top=True), mc, C.fit('black'), M=T(ex + pdx, ey + pdy, z0) @ RX(math.pi))
    if hi:
        # the brows: one up (smug), one down
        for s, rz, dy in ((-1, 0.22, 0.12), (1, -0.08, 0.0)):
            x = s * 0.66; y = 5.62 + dy
            cd.add(rbox(0.36, 0.07, 0.06, k=8, rows=3, n=3), mc, C.fit('brown'), M=T(x, y, head_z(x, y, 0.02)) @ RZ(rz * -s))
        # the monocle (on his right eye: the viewer's left), its chain down to the lapel
        ex = -0.62; ey = 5.02; zc = head_z(ex, ey, 0.3)
        ring_pts = [V3((ex + 0.53 * math.cos(2 * math.pi * j / 20), ey + 0.53 * math.sin(2 * math.pi * j / 20), zc)) for j in range(21)]
        mt.add(p_tube(ring_pts, 0.045, k=6), mm, M.quad('gold'))
        a = V3((ex - 0.42, ey - 0.33, zc)); b = V3((-1.38, 3.95, -1.32)); c = V3((-0.82, 3.28, front_z(BUST, -0.82, 3.28, 0.05)))
        ch = [a * (1 - t) ** 2 + b * (2 * t * (1 - t)) + c * t * t for t in [i / 11 for i in range(12)]]  # (it hangs, so it curves)
        mt.add(p_tube(ch, 0.022, k=4), mm, M.quad('gold'))
        # a button nose, the cheeks
        cd.add(p_ellipsoid(0.17, 0.14, 0.12, k=10, rings_n=5), mc, C.fit('orange'), M=T(0, 4.6, head_z(0, 4.6, -0.02)))
        for s in (-1, 1):
            x, y = s * 1.05, 4.28; Mx = T(x, y, head_z(x, y, -0.005)) @ frame(V3((s * 0.45, 0, -1)).normalized())
            cd.add(p_prism(12, 0.22, 0.012), mc, C.fit('blush'), M=Mx)
        # the handlebar moustache, curled up at both ends
        for s in (-1, 1):
            P = [(0.03, 4.39), (0.3, 4.34), (0.62, 4.38), (0.86, 4.5), (0.9, 4.66), (0.78, 4.74), (0.68, 4.66)]
            pts = [V3((s * x, y, head_z(x, y, 0.06 if x < 0.85 else 0.05))) for x, y in P]
            cd.add(p_tube(pts, [0.13, 0.12, 0.1, 0.075, 0.055, 0.04, 0.03], k=7, squash=0.7, cap0=True, tip1=pts[-1] + V3((-s * 0.03, -0.03, 0))), mc, C.fit('brown'))
        # the grin: a maroon half moon under the moustache, two buck teeth
        top, dep, hw = 4.2, 0.46, 0.74
        ys = [top - dep + dep * i / 6 for i in range(7)]
        xs = lambda y: [lerp(-1, 1, j / 6) * hw * max(0.08, math.sqrt(max(0.0, 1 - ((top - y) / dep) ** 2))) for j in range(7)]
        cd.add(patch(None, ys, xs, head_z, 0.012), mc, C.fit('maroon'))
        for tx in (-0.12, 0.12):
            cd.add(rbox(0.11, 0.1, 0.05, k=8, rows=3, n=4), mc, C.fit('white'), M=T(tx, 4.09, head_z(tx, 4.09, 0.03)))
    if hi:  # a sticker on the back of his head, slapped on crooked
        sy_ = 4.35; sz_ = -head_z(0.35, sy_, 0.0) + 0.006
        cd.add(p_box(0.62, 0.16, 0.012), mc, C.face('tag', 'z'), M=T(0.35, sy_, sz_) @ RZ(0.12))
    # the top hat, cocked, with a pink band
    HT = T(0.08, 5.93, 0.05) @ RZ(-0.1) @ RX(0.06)
    kh = 24 if hi else 8
    cd.add(lathe_p([(0.0, 0.0), (0.9, 0.0), (1.38, 0.0), (1.48, 0.1), (1.46, 0.15), (1.34, 0.07), (0.0, 0.07)], kh), mc, C.fit('hat'), M=HT)
    cd.add(p_loft([[V3((math.sin(2 * math.pi * j / kh) * r, y, math.cos(2 * math.pi * j / kh) * r)) for j in range(kh)] for r, y in ((0.92, 0.06), (0.96, 1.0))], cap1=True), mc, C.fit('hat'), M=HT)
    if hi:
        cd.add(p_loft([[V3((math.sin(2 * math.pi * j / kh) * r, y, math.cos(2 * math.pi * j / kh) * r)) for j in range(kh)] for r, y in ((0.9235, 0.1), (0.934, 0.32))]), mc, C.fit('pink'), M=HT)
        # the pigeon on the hat, looking over the park, and what it did
        PG = HT @ T(0.25, 1.0, 0.1) @ RY(0.6)
        cd.add(p_ellipsoid(0.16, 0.13, 0.26, k=8, rings_n=5), mc, C.fit('pgrey'), M=PG @ T(0, 0.17, 0))
        cd.add(p_ellipsoid(0.1, 0.1, 0.11, k=8, rings_n=4), mc, C.fit('pneck'), M=PG @ T(0, 0.3, -0.16))
        cd.add(p_ellipsoid(0.085, 0.09, 0.09, k=8, rings_n=4), mc, C.fit('pgrey'), M=PG @ T(0, 0.42, -0.24))
        cd.add(p_prism(5, 0.03, 0.08, r1=0.006), mc, C.fit('beak'), M=PG @ T(0, 0.41, -0.31) @ RX(math.pi * 0.95))
        for s in (-1, 1):
            cd.add(p_prism(6, 0.014, 0.012), mc, C.fit('black'), M=PG @ T(s * 0.062, 0.45, -0.28) @ RY(s * math.pi / 2))
            cd.add(p_box(0.03, 0.09, 0.03), mc, C.fit('feet'), M=PG @ T(s * 0.06, 0.045, 0.0))
            cd.add(p_box(0.04, 0.03, 0.26, taper=0.5), mc, C.fit('pdark'), M=PG @ T(s * 0.14, 0.2, 0.06) @ RY(s * 0.12))
        cd.add(p_box(0.16, 0.03, 0.24, taper=(1.4, 0.6)), mc, C.fit('pdark'), M=PG @ T(0, 0.15, 0.32) @ RX(0.35))
        for (x, y, z, s_) in ((0.95, 0.066, -0.55, 0.11), (-0.6, 0.066, 1.05, 0.08), (0.62, 0.996, 0.4, 0.07)):  # on the hat
            cd.add(p_prism(7, s_, 0.01, dome=0.012), mc, C.fit('poop'), M=HT @ T(x, y, z) @ RX(-math.pi / 2), jit=0.012, jf=20)
        cd.add(p_prism(7, 0.12, 0.012, dome=0.015), mc, C.fit('poop'), M=T(1.18, 3.365, -0.1) @ frame(V3((0.35, 1, 0)).normalized()), jit=0.015, jf=20)
    return st, cd, mt


def finish_all():
    global A_
    A_ = atlases()
    out = {}
    for lod in ('lod0', 'lod1'):
        bufs = build(lod)
        for b in bufs:  # (S&D: the kerb's top and everything on it up by DY, its foot stays on the road)
            if DY: b.V = [V3((v.x, v.y + DY, v.z)) if v.y > 0.2 else v for v in b.V]
        objs = [b.obj(sharp=40) for b in bufs if b.F]
        out[lod] = objs
    for lod in ('lod0', 'lod1'):
        bake_ao(out[lod], dist=0.45 if lod == 'lod0' else 0.6, samples=24, lo=0.42)
        for o in out[lod]: final_colour(o)
    tris0 = sum(tri_count(o) for o in out['lod0']); tris1 = sum(tri_count(o) for o in out['lod1'])
    meta = {'id': ID, 'kind': 'prop', 'lod': 90, 'tint': False, 'box': [[-5.0, 0.0, -5.0], [5.0, 6.0 + DY, 5.0]], 'tris': tris0, 'tris_lod1': tris1}
    root = lib.prop_finish(FID, out['lod0'], out['lod1'], meta)
    print('JF_TRIS', FID, 'lod0', tris0, 'lod1', tris1, 'mats', [m.name for o in out['lod0'] for m in o.data.materials])
    lo, hi_ = bounds(out['lod0']); print('JF_BOUNDS lod0', r3(lo), r3(hi_))
    return root, out['lod0'], out['lod1']


def studio():
    clear_studio(); world(0xffd3ec, 0.55)
    area(2600, (-8, 12, -14), (0, 3, 0), 10, (1.0, 0.95, 0.9))
    area(900, (12, 6, 6), (0, 3, 0), 8, (0.85, 0.9, 1.0))
    area(500, (0, 4, 14), (0, 3, 0), 6, (1.0, 0.8, 0.9))
    lib.box((60, 0.02, 60), pos=(0, -0.012, 0), m=mat('pv_floor', 0x6abf4a, rough=0.9), name='jf_set_floor')


def sheets(root, lod0, lod1):
    colour_preview([m for m in bpy.data.materials if m.name.startswith('fd_')], True)
    studio(); tmp = os.path.join(SHEETS, '_tmp_fd'); os.makedirs(tmp, exist_ok=True)
    m = json.loads(root['jf'])
    def go(name, views, cols, label, res, show_lod1=False):
        for o in lod0: o.hide_render = show_lod1
        for o in lod1: o.hide_render = not show_lod1
        paths = []; labels = []
        for k, (cap, cam, tg, lens) in enumerate(views):
            p_ = os.path.join(tmp, '%s_%d.png' % (name, k)); shot(p_, cam, tg, lens=lens, res=res, samples=16); paths.append(p_); labels.append(cap)
        return contact(paths, os.path.join(SHEETS, FID + ('' if name == 'sheet' else '_' + name)), label, cols=cols, labels=labels)
    go('sheet', [('front', (0, 4.0, -17), (0, 3.4, 0), 35), ('three quarter', (-11, 6.5, -11), (0, 3.2, 0), 35), ('side', (17, 4.0, 0), (0, 3.4, 0), 35),
                 ('back three quarter', (10, 6, 11), (0, 3.2, 0), 35), ('from above', (0.1, 22, -6), (0, 2, 0), 35), ('lod1 (far copy)', (-11, 6.5, -11), (0, 3.2, 0), 35)][:5],
       3, '%s  %d tris  far copy %d  plaza 10 x 10 m, the bust to 6 m (the hat and pigeon above)' % (FID, m['tris'], m['tris_lod1']), (640, 460))
    go('close', [('the founder', (-1.6, 5.2, -6.2), (0, 4.6, 0), 45), ('the plaque', (0.6, 1.5, -4.2), (0, 1.45, -1.3), 45),
                 ('the pigeon, the hat', (2.6, 7.6, -2.8), (0.3, 6.6, 0), 45), ('the beds, a topiary', (-5.6, 1.9, -5.4), (-2.2, 0.6, -2.2), 40)],
       2, '%s close-ups' % FID, (640, 460))
    go('lod1', [('lod1, three quarter', (-11, 6.5, -11), (0, 3.2, 0), 35), ('lod1, front', (0, 4.0, -17), (0, 3.4, 0), 35)], 2, '%s far copy (%d tris)' % (FID, m['tris_lod1']), (480, 340), True)
    for o in lod0 + lod1: o.hide_render = False
    try: os.rmdir(tmp)
    except OSError: pass


def main():
    global ID, FID, DY
    only = arg('only')
    for ID, DY in VARIANTS.items():
        if isinstance(only, str) and ID not in only.split(','): continue
        FID = 'p_' + ID
        reset(); lib._mats.clear()
        root, lod0, lod1 = finish_all()
        if '--qa' in ARGV:
            qa(FID + ' lod0', lod0, eps=0.0005, tol=0.004); qa(FID + ' lod1', lod1, eps=0.0005, tol=0.004)
        if '--no-export' not in ARGV:
            out = os.path.join(MODELS, FID + '.glb'); tmp_ = os.path.join(MODELS, '_tmp_' + FID + '.glb')
            compact_glb(export_glb(root, tmp_)); os.replace(tmp_, out)
            print('JF_OUT', out, os.path.getsize(out) // 1024, 'KB')
        if '--sheet' in ARGV and ID == 'founder': sheets(root, lod0, lod1)


main()
