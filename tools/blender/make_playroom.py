# JANKFIRE map pass, Crate: the giant kid's playroom round the toy tower (shared/map.js crate(), render-only boxes).
# Map props (the props lane, make_market.py's flow). Each is built on its boxes at their real (giant) size, y 0 = the
# carpet, long along x; meta.box = the boxes' extent in the prop's frame.
#   p_crayon     a wax crayon lying down (18 across, 160 long): sharpened cone tip worn flat, a paper wrapper with
#                black zigzag bands and a JANKOLA label, a flat back end. wax + wrapper are `tint` (the map's toyblue /
#                toygreen / toyyellow colour each copy)
#   p_bigball    the "giant ball" (it was a cube): a glossy red playground ball, pebbled, a yellow band round it with
#                blue pinstripes and a big yellow star on each side
#   p_kidbed     the bed: a lilac painted wooden frame with ball-topped posts, a headboard with a star cut out, slats
#                showing under the side rail, a ticking-striped mattress, a teal duvet with stars hanging over the
#                sides, a plump pillow
#   p_toytrain   the train set: pink plastic rails on wooden sleepers, a wooden toy engine (red boiler and chassis,
#                yellow cab with windows, black chimney, brass dome, cowcatcher, six wheels with brass hubs)
#   p_blockpile  the two blocks in the corner: make_crate.py's toy blocks (a pink one, an orange one on top, turned)
# run: blender52 -b --python tools/blender/make_playroom.py -- [--only=crayon,bigball] [--no-sheet] [--no-export] [--qa]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from lib import _link
import lib
import make_market as MK
from make_market import img_tile, Atlas, paint_wood, paint_paint, paint_noise, uv_trim, uv_fit, poly_obj, outward, opt, V3, TAU, fcen, _gn
from make_crate import toy_atlas, toy_block, xform, flat_big, far_block, shape_prism

ONLY = [s for s in (opt('only', '') or '').split(',') if s]
PROPS = []
def prop(fid):
    def reg(fn): PROPS.append((fid, fn)); return fn
    return reg


def uv_round_x(o, A, key, x0, x1, turns=1.0):
    """parts turned round game x (a crayon lying down): u goes round, v runs x0..x1 down the band"""
    apply_mods(o)
    me = o.data; uv = MK._uvl(o); P = MK._gp(o)
    u0, v0, u1, v1 = A.uvrect(key)
    for poly in me.polygons:
        ls = []
        for li in poly.loop_indices:
            p = P[me.loops[li].vertex_index]
            a = (math.atan2(p.z, p.y) / TAU + 0.5) * turns  # (the part's own frame: its axis is x)
            ls.append([li, a, v0 + (v1 - v0) * min(1, max(0, (p.x - x0) / (x1 - x0)))])
        ref = ls[0][1]
        for e in ls:
            while e[1] - ref > turns / 2: e[1] -= turns
            while e[1] - ref < -turns / 2: e[1] += turns
        for li, a, v in ls: uv[li].uv = (a, v)  # (a band: u tiles round)
    return o


# ------------------------------------------------------------ p_crayon
def paint_wrapper(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf4f0e8)
    for y0 in (3, h - 6):  # zigzag bands
        for x in range(w):
            yy = y0 + int(abs((x % 8) - 4) * 0.75)
            px[yy:yy + 2, x] = hexrgb(0x141018)
    text_px(px, 'JANKOLA', 3, h // 2 - 7, 2, 0x141018)
    text_px(px, 'JANKOLA', w // 2 + 3, h // 2 - 7, 2, 0x141018)


@prop('p_crayon')
def build_crayon():
    A = Atlas('cy_atlas', 128, 64)
    A.band('label', 32, paint_wrapper)
    A.cell('wax', 32, 32, paint_noise(0xffffff, 0.06, 7)).cell('paper', 32, 32, paint_noise(0xf2eee4, 0.05, 8))
    T = mat('tint', 0xffffff, rough=0.38, tex=img_tile('cy_wax', 32, 32, paint_noise(0xf4f4f4, 0.07, 3)), clearcoat=0.35)
    M = mat('cy_paper', 0xffffff, rough=0.7, tex=A.image())
    R, L = 9.0, 160.0
    x0 = -L / 2
    seg = 24
    # the wax: flat back end, the body under the wrapper, the sharpened cone worn flat at the tip
    prof = [(0.0, x0), (R * 0.82, x0), (R * 0.88, x0 + 0.6), (R * 0.88, x0 + 4), (R * 0.88, L / 2 - 30), (R * 0.86, L / 2 - 26),
            (R * 0.62, L / 2 - 14), (R * 0.36, L / 2 - 4), (R * 0.28, L / 2 - 1.2), (R * 0.22, L / 2), (0.0, L / 2)]
    wax = lathe(prof, (0, R, 0), T, seg=seg, axis='x', name='cy_wax')
    MK.uv_trim(wax, A, 'wax', upm=0.05, grain='x')  # (the tint texture tiles; the atlas rect is ignored by its own image)
    # the paper wrapper: a sleeve a hair bigger, its edges rolled
    wp = [(R * 0.88, x0 + 6), (R * 0.99, x0 + 6.4), (R * 1.0, x0 + 8), (R * 1.0, L / 2 - 34), (R * 0.99, L / 2 - 32.6), (R * 0.88, L / 2 - 32.2)]
    wr = lathe(wp, (0, R, 0), T, seg=seg, axis='x', name='cy_wrap', cap=False)
    MK.uv_trim(wr, A, 'wax', upm=0.05, grain='x')
    lab = lathe([(R * 0.995, -22.0), (R * 1.012, -21.0), (R * 1.012, 21.0), (R * 0.995, 22.0)], (0, R, 0), M, seg=seg, axis='x', name='cy_label', cap=False)
    uv_round_x(lab, A, 'label', -22.0, 22.0)
    parts = [wax, wr, lab]
    far = [lathe([(0.0, x0), (R * 0.9, x0), (R, x0 + 6), (R, L / 2 - 30), (R * 0.3, L / 2 - 2), (0.0, L / 2)], (0, R, 0), T, seg=8, axis='x', name='cy_far')]
    MK.uv_trim(far[0], A, 'wax', upm=0.05, grain='x')
    return dict(lod0=parts, lod1=far, box=((-L / 2, 0, -R), (L / 2, 2 * R, R)), ao=6.0, lod=400, sheet=dict(bg=0xffd6ec))


# ------------------------------------------------------------ p_bigball
def paint_ball(px):
    """equirectangular: u round the ball, v pole to pole. red, pebbled; a yellow band at the equator with blue
    pinstripes; a yellow star on each side"""
    h, w = px.shape[:2]; r = np.random.default_rng(5)
    yy, xx = np.mgrid[0:h, 0:w]
    px[:] = hexrgb(0xff2a3a) * (0.9 + 0.12 * r.random((h, w, 1)))
    px[(r.random((h, w)) < 0.08)] *= 1.12
    eq = np.abs(yy - h / 2) < h * 0.08
    px[eq] = hexrgb(0xffd21a)
    for s in (-1, 1):
        px[np.abs(yy - (h / 2 + s * h * 0.095)) < 1.2] = hexrgb(0x2a6cff)
    for cu in (0.25, 0.75):  # stars (squashed toward the poles like a map would be)
        cx, cy = cu * w, h * 0.24
        a = np.arctan2(-(yy - cy), (xx - cx) * 0.5) - np.pi / 2  # (a point straight up)
        d = np.hypot((xx - cx) * 0.5, yy - cy)
        f = (a / TAU * 5) % 1.0
        rad = h * (0.055 + 0.085 * np.abs(f * 2 - 1))  # a proper five-pointed star: points out, notches in
        m = d < rad
        px[m] = hexrgb(0xffe14d)


def uv_sphere(o, R):
    """equirectangular UVs round the part's own centre; a pole vertex takes the u of the face it's in"""
    me = o.data; uv = MK._uvl(o); P = MK._gp(o)
    for poly in me.polygons:
        ls = []
        for li in poly.loop_indices:
            p = P[me.loops[li].vertex_index]
            pole = abs(abs(p.y) - R) < R * 1e-4
            ls.append([li, None if pole else math.atan2(p.z, p.x) / TAU + 0.5, 0.5 + math.asin(max(-1, min(1, p.y / R))) / math.pi])
        us = [e[1] for e in ls if e[1] is not None]
        ref = us[0]
        for e in ls:
            if e[1] is None: continue
            while e[1] - ref > 0.5: e[1] -= 1
            while e[1] - ref < -0.5: e[1] += 1
        avg = sum(e[1] for e in ls if e[1] is not None) / len(us)
        for li, u, v in ls: uv[li].uv = (avg if u is None else u, v)


@prop('p_bigball')
def build_ball():
    tex = img_tile('bb_tex', 256, 128, paint_ball)
    M = mat('bb_rubber', 0xffffff, rough=0.3, tex=tex, clearcoat=0.8)
    R = 60.0
    b = ball(R, (0, R, 0), M, seg=40, rings=24, name='bb_ball'); uv_sphere(b, R)
    for v in b.data.vertices:  # it squashes a little where it sits (the mesh is round its own centre)
        if v.co.z < -R * 0.97: v.co.z = -R * 0.97
    f = ball(R, (0, R, 0), M, seg=16, rings=10, name='bb_far'); uv_sphere(f, R)
    return dict(lod0=[b], lod1=[f], box=((-R, 0, -R), (R, 2 * R, R)), ao=20.0, lod=500, sheet=dict(bg=0xffd6ec))


# ------------------------------------------------------------ p_kidbed
def paint_ticking(px):
    h, w = px.shape[:2]
    px[:] = hexrgb(0xf8f4ee)
    for x in range(0, w, 8): px[:, x:x + 2] = hexrgb(0x8ab8ff)


def paint_duvet(px):
    h, w = px.shape[:2]; r = np.random.default_rng(2)
    px[:] = hexrgb(0x19c8bc) * (0.94 + 0.08 * r.random((h, w, 1)))
    for k in range(9):
        cx, cy, s = r.integers(4, w - 4), r.integers(4, h - 4), r.integers(2, 4)
        for dx in range(-s, s + 1):
            px[(cy) % h, (cx + dx) % w] = hexrgb(0xffe14d); px[(cy + dx) % h, cx % w] = hexrgb(0xffe14d)
    for k in range(0, w, 16): px[:, k] *= 0.9  # quilting lines
    for k in range(0, h, 16): px[k, :] *= 0.9


@prop('p_kidbed')
def build_bed():
    A = Atlas('kb_atlas', 128, 128)
    A.band('frame', 16, paint_paint(0xc8a0ff, 0xe0b080, 12, wear=0.12, edge=0.9))
    A.band('slat', 16, paint_wood(0xe8c08a, 0xa8743a, 13, edge=0.7, knots=1))
    A.cell('tick', 32, 32, paint_ticking).cell('duvet', 32, 32, paint_duvet).cell('pillow', 32, 32, paint_noise(0xfff6fa, 0.04, 4))
    A.cell('knob', 16, 16, paint_noise(0xffe14d, 0.05, 5)).cell('dark', 16, 16, paint_noise(0x6a4aa0, 0.05, 6))
    M = mat('kb_paint', 0xffffff, rough=0.4, tex=A.image(), clearcoat=0.5)
    W, D = 260.0, 260.0  # x across, z long; the head at +z
    hw, hd = W / 2, D / 2
    parts = []
    post = 12.0
    for sx in (-1, 1):
        for sz, top in ((1, 108.0), (-1, 84.0)):
            p = box((post, top, post), (sx * (hw - post / 2), top / 2, sz * (hd - post / 2)), M, bev=1.5, name=f'kb_post{sx}{sz}')
            uv_trim(p, A, 'frame', upm=0.02, grain='y'); parts.append(p)
            k = ball(post * 0.62, (sx * (hw - post / 2), top + post * 0.45, sz * (hd - post / 2)), M, seg=16, rings=10, name=f'kb_knob{sx}{sz}')
            uv_fit(k, A, 'knob'); parts.append(k)
    # side rails and end rails
    for sx in (-1, 1):
        r_ = box((6, 18, D - 2 * post), (sx * (hw - 4), 34, 0), M, bev=1.2, name=f'kb_side{sx}'); uv_trim(r_, A, 'frame', upm=0.02, grain='z'); parts.append(r_)
    for sz in (-1, 1):
        r_ = box((W - 2 * post, 18, 6), (0, 34, sz * (hd - 4)), M, bev=1.2, name=f'kb_end{sz}'); uv_trim(r_, A, 'frame', upm=0.02, grain='x'); parts.append(r_)
    # slats under the mattress, showing between the rails
    for k in range(9):
        z = -hd + post + 10 + k * (D - 2 * post - 20) / 8
        s_ = box((W - 2 * post + 24, 3, 10), (0, 41, z), M, bev=0.6, name=f'kb_slat{k}'); uv_trim(s_, A, 'slat', upm=0.03, grain='x'); parts.append(s_)
    # the headboard: a panel between the head posts with a star cut out of it; the footboard lower
    hb = box((W - 2 * post, 50, 5), (0, 72, hd - 5), M, bev=1.5, name='kb_head')
    st = shape_prism('star', 15, 20, M, 'kb_starcut', z0=-10); st.location = gv(0, 74, hd - 5); cut(hb, st)
    flat_big(hb); uv_trim(hb, A, 'frame', upm=0.02, grain='x'); parts.append(hb)
    fb = box((W - 2 * post, 30, 5), (0, 58, -hd + 5), M, bev=1.5, name='kb_foot'); uv_trim(fb, A, 'frame', upm=0.02, grain='x'); parts.append(fb)
    # the mattress (ticking), the duvet over it hanging down the sides, the pillow
    mt = box((W - 2 * post - 6, 26, D - 2 * post - 6), (0, 56, 0), M, bev=5, seg=3, name='kb_mattress'); uv_fit(mt, A, 'tick'); parts.append(mt)
    dz0, dz1 = -hd + post - 4, hd - post - 64  # the duvet: from over the foot to short of the pillow
    rows = []
    nx, nzs = 13, 9
    for j in range(nzs + 1):
        z = dz0 + (dz1 - dz0) * j / nzs
        row = []
        for i in range(nx + 1):
            t = i / nx
            x = (t - 0.5) * (W - 2 * post + 10)
            edge = abs(t - 0.5) * 2
            # flat on top, rolling over the mattress edge and hanging down the sides (a little wavy)
            if edge < 0.86: y = 72.5 + 2.0 * math.sin(z * 0.05 + x * 0.03)  # (its underside stays clear of the mattress top)
            else:
                k_ = (edge - 0.86) / 0.14
                y = 72.5 - k_ * 31 + 1.5 * math.sin(z * 0.1)
                x = math.copysign(hw - post + 3 + 3 * math.sin(k_ * math.pi / 2), x)
            row.append((x, y, z))
        rows.append(row)
    dv = MK.sheet_obj(rows, M, 'kb_duvet', smooth_angle=70)
    sol = dv.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 2.5; sol.offset = 1.0
    apply_mods(dv); outward(dv); uv_fit(dv, A, 'duvet', axis='y'); parts.append(dv)
    # pillow: a plump lofted cushion near the head
    def psec(i, t):
        k_ = math.sin(math.pi * min(1, max(0, t))) ** 0.5
        out = []
        for a in range(12):
            th = TAU * a / 12
            out.append((9 * k_ * math.copysign(abs(math.sin(th)) ** 0.7, math.sin(th)) + 0.001, 34 * math.copysign(abs(math.cos(th)) ** 0.7, math.cos(th))))
        return out
    pl = loft([(x, 77, hd - post - 32) for x in np.linspace(-95, 95, 9)], psec, M, name='kb_pillow', smooth_angle=70, close=(True, True))
    outward(pl); uv_fit(pl, A, 'pillow'); parts.append(pl)
    # lod1: the frame as boxes, the bedding as a block
    far = []
    for sx in (-1, 1):
        for sz, top in ((1, 108.0), (-1, 84.0)):
            p = box((post, top, post), (sx * (hw - post / 2), top / 2, sz * (hd - post / 2)), M, name=f'kb_far_post{sx}{sz}'); uv_trim(p, A, 'frame', upm=0.02, grain='y'); far.append(p)
    fb1 = box((W - 2 * post, 50, 5), (0, 72, hd - 5), M, name='kb_far_head'); uv_trim(fb1, A, 'frame', upm=0.02, grain='x'); far.append(fb1)
    bd = box((W - 2 * post + 6, 30, D - 2 * post + 4), (0, 58, 0), M, bev=4, seg=1, name='kb_far_bed'); uv_fit(bd, A, 'duvet'); far.append(bd)
    return dict(lod0=parts, lod1=far, box=((-hw, 0, -hd), (hw, 120, hd)), ao=25.0, lod=500, sheet=dict(bg=0xffd6ec))


# ------------------------------------------------------------ p_toytrain
@prop('p_toytrain')
def build_train():
    A = Atlas('tr_atlas', 128, 128)
    A.band('wood', 16, paint_wood(0xe8c08a, 0xa8743a, 21, edge=0.7, knots=1))
    A.band('red', 16, paint_paint(0xff2a3a, 0xe0b080, 22, wear=0.08, edge=0.85))
    A.band('yellow', 16, paint_paint(0xffd21a, 0xe0b080, 23, wear=0.08, edge=0.85))
    A.cell('pink', 16, 16, paint_noise(0xff5ad0, 0.04, 1)).cell('black', 16, 16, paint_noise(0x1a1820, 0.05, 2))
    A.cell('brass', 16, 16, paint_noise(0xe0b040, 0.06, 3)).cell('glass', 16, 16, paint_noise(0x2a3448, 0.05, 4))
    M = mat('tr_paint', 0xffffff, rough=0.36, tex=A.image(), clearcoat=0.55)
    parts = []
    # the track: rails at z -45..-35 and 35..45 (8 tall), sleepers every 14 between them (4 x 4)
    for s in (-1, 1):
        rl = box((200, 6, 10), (0, 3, s * 40), M, bev=1.2, seg=2, name=f'tr_rail{s}'); uv_fit(rl, A, 'pink'); parts.append(rl)
        lip = box((200, 2.2, 4), (0, 7, s * 40), M, bev=0.8, name=f'tr_head{s}'); uv_fit(lip, A, 'pink'); parts.append(lip)
    for k, x in enumerate(np.arange(-94, 100, 14)):
        sl = box((4, 4, 70), (x + 2, 2, 0), M, bev=0.6, name=f'tr_sleeper{k}'); uv_trim(sl, A, 'wood', upm=0.05, grain='z'); parts.append(sl)
    # the engine (front toward -x): chassis, boiler, smokebox, chimney, dome, cowcatcher; the cab behind
    ch = box((52, 8, 38), (-35, 12, 0), M, bev=1.5, name='tr_chassis'); uv_trim(ch, A, 'red', upm=0.03, grain='x'); parts.append(ch)
    bo = cyl(13, 40, (-40, 29, 0), M, axis='x', seg=24, bev=1.0, name='tr_boiler'); uv_trim(bo, A, 'red', upm=0.03, grain='x'); parts.append(bo)
    sb = cyl(13.6, 6, (-58, 29, 0), M, axis='x', seg=24, bev=1.0, name='tr_smokebox'); uv_fit(sb, A, 'black'); parts.append(sb)
    for k, x in enumerate((-48, -32)):
        bd = cyl(13.4, 2.2, (x, 29, 0), M, axis='x', seg=24, bev=0.4, name=f'tr_band{k}'); uv_fit(bd, A, 'brass'); parts.append(bd)
    chim = lathe([(4.2, 0), (4.2, 6), (6.0, 10), (6.4, 11), (0.0, 11)], (-50, 40, 0), M, seg=16, axis='y', name='tr_chimney'); uv_fit(chim, A, 'black'); parts.append(chim)
    dome = lathe([(5.5, 0), (5.5, 2), (4.8, 4.5), (2.8, 6.2), (0.0, 6.8)], (-34, 40, 0), M, seg=16, axis='y', name='tr_dome'); uv_fit(dome, A, 'brass'); parts.append(dome)
    cc = poly_obj([(-61, 8, -18), (-61, 8, 18), (-61, 18, 18), (-61, 18, -18), (-68, 4.5, -14), (-68, 4.5, 14)],
                  [(0, 1, 2, 3), (4, 5, 1, 0), (5, 2, 1), (4, 0, 3), (3, 2, 5, 4)], M, 'tr_cowcatcher')
    outward(cc); bevel(cc, 0.8, 2, 40); uv_fit(cc, A, 'yellow'); parts.append(cc)
    cab = box((28, 28, 38), (-1, 26, 0), M, bev=1.5, name='tr_cab')
    for s in (-1, 1):  # side windows (solid glass panes behind: it's a toy)
        wcut = box((12, 10, 8), (-2, 31, s * 19), M, name=f'tr_wincut{s}'); cut(cab, wcut)
    flat_big(cab); uv_trim(cab, A, 'yellow', upm=0.03, grain='x'); parts.append(cab)
    for s in (-1, 1):
        gl = box((12, 10, 1), (-2, 31, s * 16.5), M, name=f'tr_glass{s}'); uv_fit(gl, A, 'glass'); parts.append(gl)
    roof = box((34, 3, 42), (-1, 41.5, 0), M, bev=1.2, name='tr_roof'); uv_trim(roof, A, 'red', upm=0.03, grain='x'); parts.append(roof)
    for s in (-1, 1):  # wheels: three a side under the chassis, brass hubs, a coupling rod
        for k, x in enumerate((-52, -36, -20)):
            wh = cyl(7, 5, (x, 7, s * 21.2), M, axis='z', seg=20, bev=0.8, name=f'tr_wheel{s}{k}'); uv_fit(wh, A, 'black'); parts.append(wh)
            hb = cyl(2.4, 1.4, (x, 7, s * 24.2), M, axis='z', seg=10, bev=0.3, name=f'tr_hub{s}{k}'); uv_fit(hb, A, 'brass'); parts.append(hb)
        rod = box((34, 1.6, 1.2), (-36, 6, s * 25.2), M, bev=0.3, name=f'tr_rod{s}'); uv_fit(rod, A, 'brass'); parts.append(rod)
    far = []
    for s in (-1, 1):
        f = box((200, 8, 10), (0, 4, s * 40), M, name=f'tr_far_rail{s}'); uv_fit(f, A, 'pink'); far.append(f)
    fs = box((190, 3.8, 70), (0, 1.9, 0), M, name='tr_far_sleepers'); uv_trim(fs, A, 'wood', upm=0.05, grain='z'); far.append(fs)
    fe = box((60, 37, 38), (-33, 21.5, 0), M, bev=2, seg=1, name='tr_far_engine'); uv_trim(fe, A, 'red', upm=0.03, grain='x'); far.append(fe)
    return dict(lod0=parts, lod1=far, box=((-100.0, 0.0, -45.0), (100.0, 40.0, 45.0)), ao=10.0, lod=500, sheet=dict(bg=0xffd6ec))


# ------------------------------------------------------------ p_blockpile
@prop('p_blockpile')
def build_pile():
    A = toy_atlas('bp_atlas')
    M = mat('bp_paint', 0xffffff, rough=0.34, tex=A.image(), clearcoat=0.6)
    parts, far = [], []
    for k, (c, s, yaw, col, l1, l2, lc, mouth) in enumerate((((0, 30, 0), 60, 0.0, 'pink', 'B', 'Z', 'yellowL', 'mouthP'),
                                                           ((0, 80, 0), 40, 0.26, 'orange', 'O', '!', 'pinkL', 'mouthO'))):
        sides = [(0.0, col, ('face', mouth)), (math.pi, col, ('text', l2, lc)), (math.pi / 2, col, ('text', l1, lc)), (-math.pi / 2, col, ('face', mouth))]
        p = toy_block(s, s, s, sides, A, M, f'bp{k}')
        xform(p, yaw, c); parts += p
        f = far_block(s, s, s, A, M, col, f'bp_far{k}'); xform([f], yaw, c); far.append(f)
    return dict(lod0=parts, lod1=far, box=((-30.0, 0.0, -30.0), (30.0, 100.0, 30.0)), ao=10.0, lod=500, sheet=dict(bg=0xffd6ec))


if __name__ == '__main__':
    for fid, fn in PROPS:
        if ONLY and fid[2:] not in ONLY and fid not in ONLY: continue
        MK.run_prop(fid, fn)
