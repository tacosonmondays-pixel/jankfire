# Jankfield High's furniture (Zombies): one file, p_schoolkit.glb, a node per piece (shared/zmschool.js places them with
# L.P('schoolkit', x, z, r, { v: '<name>' }); its own boxes stay as the collision and the no-model fallback).
# every piece: origin on the floor at the middle of its footprint, long side along x, the side you use toward +z.
# run: blender52 -b --python tools/blender/make_schoolkit.py -- [--qa] [--only=a,b (a review sheet of just those, no export)]
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *  # noqa
from sidekit import quad

M = {}


def mats():
    def lab(name, w, h, bg, lines, fg=0x120818, scale=1):
        def draw(px):
            px[:] = hexrgb(bg)
            for i, (s, c) in enumerate(lines): text_px(px, s, 2, 2 + i * 9 * scale, scale, c if c is not None else fg)
        return mat(name, 0xffffff, rough=0.5, tex=tex_canvas(name + '_t', w, h, draw))
    M.update(
        wood=mat('sk_wood', 0xb8824a, rough=0.5, clearcoat=0.3, tex=tex_wood('sk_wood_t', 0xc08a50, 0x7a4a22, size=32, seed=11, rings=5)),
        dwood=mat('sk_dwood', 0x6a3e1e, rough=0.4, clearcoat=0.5, tex=tex_wood('sk_dwood_t', 0x70421f, 0x3e220e, size=32, seed=12, rings=6)),
        lam=mat('sk_lam', 0xf0e8d4, rough=0.35, clearcoat=0.4, tex=tex_noise('sk_lam_t', 0xf0e8d4, 0.05, 16, seed=3)),
        steel=mat('sk_steel', 0x9aa0aa, rough=0.3, metal=0.9), chrome=mat('sk_chrome', 0xe0e4ea, rough=0.12, metal=1.0),
        dark=mat('sk_dark', 0x26222c, rough=0.5), rubber=mat('sk_rubber', 0x18161c, rough=0.8),
        blue=mat('sk_blue', 0x3a8ae0, rough=0.28, clearcoat=0.7), pink=mat('sk_pink', 0xff4fd8, rough=0.28, clearcoat=0.7),
        yellow=mat('sk_yellow', 0xffe14d, rough=0.3, clearcoat=0.6), cyan=mat('sk_cyan', 0x4fd8ff, rough=0.28, clearcoat=0.7), water=mat('sk_drink_water', 0x4fd8ff, rough=0.05, clearcoat=0.7),
        red=mat('sk_red', 0xe0302a, rough=0.3, clearcoat=0.6), green=mat('sk_green', 0x2a8a4a, rough=0.35, clearcoat=0.5),
        white=mat('sk_white', 0xf4f2ea, rough=0.4), orange=mat('sk_orange', 0xff6a1a, rough=0.3, clearcoat=0.6),
        gold=mat('sk_gold', 0xf0c040, rough=0.18, metal=1.0), glass=mat('sk_glass', 0xbfe8ff, rough=0.08, alpha=0.25),
        slate=mat('sk_slate', 0x2a2e34, rough=0.25, clearcoat=0.6), leather=mat('sk_leather', 0x5a2a1c, rough=0.45, clearcoat=0.3),
        cream=mat('sk_cream', 0xe8dcc0, rough=0.5), brick=mat('sk_brick', 0xb85a3a, rough=0.8, tex=tex_noise('sk_brick_t', 0xb85a3a, 0.14, 16, seed=7)),
        glow=mat('sk_glow', 0xff8a2a, emit=0xff6a1a, strength=3.0), flame=mat('sk_flame', 0x7ad0ff, emit=0x4fd8ff, strength=2.5),
        goo=mat('sk_goo', 0x7dff4f, rough=0.1, clearcoat=1.0, emit=0x39ff14, strength=0.5), beige=mat('sk_beige', 0xd8c090, rough=0.6),
        meat=mat('sk_meat', 0x9a5a3a, rough=0.5), net=mat('sk_net', 0xf4f2ea, rough=0.7), ball=mat('sk_ball', 0xe8742a, rough=0.6),
        l_num=lab('sk_num', 16, 12, 0xf4f2ea, [('07', None)]), l_boiler=lab('sk_lboiler', 64, 22, 0xffe14d, [('BOILER', None), ('DO NOT KICK', 0xe0102a)]),
        l_school=lab('sk_lschool', 100, 22, 0xff4fd8, [('JANKFIELD HIGH', 0xffe14d), ('SIGN IN OR ELSE', 0xffffff)]),
        l_prin=lab('sk_lprin', 58, 12, 0xf0c040, [('PRINCIPAL', None)]), l_boss=lab('sk_lboss', 34, 22, 0xf4f2ea, [('#1', 0xe0102a), ('BOSS', None)]),
        l_think=lab('sk_lthink', 34, 12, 0xffe14d, [('THINK', None)]), l_part=lab('sk_lpart', 64, 12, 0x3a8ae0, [('PARTICIPANT', 0xffffff)]),
        l_menu=lab('sk_lmenu', 46, 22, 0x1a3a2a, [('BEIGE', 0xffffff), ('MEAT?', 0xffe14d)]), l_fume=lab('sk_lfume', 58, 22, 0xffe14d, [('FUMES', None), ('MOSTLY', 0xe0102a)]),
        l_hot=lab('sk_lhot', 34, 12, 0xe0302a, [('HOT', 0xffffff)]), l_files=lab('sk_lfiles', 28, 12, 0xf4f2ea, [('A-Z', None)]),
    )
    def art(px):
        px[:] = hexrgb(0xbfe8ff); px[20:, :] = hexrgb(0x7dff4f)
        px_disc(px, 24, 7, 4, 0xffe14d); px[12:22, 6:16] = hexrgb(0xff3030); px_line(px, 4, 12, 11, 6, 0x8a4a2a, 2); px_line(px, 11, 6, 18, 12, 0x8a4a2a, 2)
    M['art'] = mat('sk_art', 0xffffff, rough=0.6, tex=tex_canvas('sk_art_t', 32, 28, art))
    def board(px):
        px[:] = hexrgb(0xf4f0e8); px[:2] = px[-2:] = hexrgb(0xc8202c); px[:, :2] = px[:, -2:] = hexrgb(0xc8202c)
        px[14:16, 14:34] = hexrgb(0xc8202c); px[14:28, 14:16] = px[14:28, 32:34] = hexrgb(0xc8202c)
    M['board'] = mat('sk_board', 0xffffff, rough=0.3, clearcoat=0.6, tex=tex_canvas('sk_board_t', 48, 32, board))


def decal(c, w, h, m, axis='z', sx=1):
    q = quad(c, w, h, m, axis=axis, sx=sx); q['keep_uv'] = 1
    return q


def legs(pts, h, r=0.022, m=None, y0=0.0):
    return [rod((x, y0, z), (x, h, z), r, m or M['steel'], seg=6) for x, z in pts]


def books(x0, x1, y, z, depth, seed, face=1):
    """a row of book spines along x on a shelf at height y, their backs at z, spines toward face"""
    r = random.Random(seed); out = []; x = x0
    cols = [M['red'], M['blue'], M['green'], M['yellow'], M['pink'], M['cyan'], M['cream'], M['leather'], M['orange']]
    while x < x1 - 0.03:
        w = r.uniform(0.035, 0.075); h = r.uniform(0.2, 0.3); d = depth * r.uniform(0.78, 0.98)
        if x + w > x1: break
        if r.random() < 0.1: x += w; continue  # a gap
        lean = r.uniform(-0.08, 0.08) if r.random() < 0.15 else 0
        out.append(box((w, h, d), (x + w / 2, y + h / 2 + 0.001, z + face * d / 2), r.choice(cols), rot=(0, 0, lean)))
        x += w + 0.003
    return out


# ---------------------------------------------------------------- the pieces
def lunchtable():  # 3.2 x 2.3 (the table itself 3.2 x 1.2), top 0.8: a fold-up cafeteria table, benches bolted on
    P = [box((3.2, 0.05, 0.92), (0, 0.775, 0), M['lam'], bev=0.012), box((3.22, 0.03, 0.94), (0, 0.755, 0), M['pink'], bev=0.008)]
    for sz, m in ((-1, M['blue']), (1, M['pink'])):
        P.append(box((3.0, 0.045, 0.3), (0, 0.45, sz * 0.86), m, bev=0.014))
        for x in (-1.15, 0, 1.15):
            P.append(tube([(x, 0.762, sz * 0.3), (x, 0.3, sz * 0.5), (x, 0.3, sz * 0.86), (x, 0.445, sz * 0.86)], 0.022, M['steel'], seg=6))
            P.append(rod((x, 0.31, sz * 0.5), (x, 0.03, sz * 0.62), 0.019, M['steel'], seg=6))
            P.append(cyl(0.04, 0.03, (x, 0.04, sz * 0.62), M['rubber'], axis='x', seg=8))
    for x in (-1.15, 1.15): P.append(rod((x, 0.44, -0.44), (x, 0.44, 0.44), 0.016, M['steel'], seg=6))
    P.append(box((0.42, 0.02, 0.3), (-0.8, 0.81, 0.1), M['cyan'], bev=0.006, rot=(0, 0.2, 0)))  # a tray somebody left
    P.append(cyl(0.035, 0.09, (-0.9, 0.865, 0.12), M['white'], axis='y', seg=8))
    P.append(box((0.07, 0.11, 0.07), (-0.68, 0.875, 0.05), M['white'], bev=0.006)); P.append(box((0.082, 0.03, 0.082), (-0.68, 0.905, 0.05), M['blue']))
    P.append(ball(0.045, (0.9, 0.845, -0.15), M['red'], seg=8, rings=6))  # an apple for nobody
    return P


def servery():  # 1.2 x 3.4, top 1.05, long along z, you queue on the +x side
    P = [box((0.9, 0.84, 3.4), (-0.15, 0.5, 0), M['steel'], bev=0.01), box((0.96, 0.06, 3.44), (-0.15, 0.93, 0), M['chrome'], bev=0.008),
         box((0.88, 0.1, 3.36), (-0.15, 0.05, 0), M['dark'])]
    for y in (0.78,):  # the tray rail
        for dx in (0.4, 0.5, 0.58): P.append(rod((dx, y, -1.68), (dx, y, 1.68), 0.014, M['chrome'], seg=6))
        for z in (-1.6, -0.55, 0.55, 1.6): P.append(tube([(0.3, y - 0.12, z), (0.4, y - 0.02, z), (0.6, y - 0.02, z)], 0.012, M['chrome'], seg=4))
    for i, (z, m) in enumerate(((-1.15, M['beige']), (-0.38, M['meat']), (0.38, M['beige']))):  # the wells: beige, meat?, more beige
        P.append(box((0.6, 0.02, 0.66), (-0.15, 0.965, z), M['dark'], bev=0.004))
        P.append(ball(0.26, (-0.15, 0.95, z), m, scale=(1.0, 0.28, 1.15), seg=10, rings=6))
        P.append(rod((-0.15, 1.0, z), (0.05, 1.16, z + 0.1), 0.012, M['chrome'], seg=5))  # a ladle
    for z in (-1.66, 1.66): P.append(rod((0.22, 0.96, z), (0.22, 1.5, z), 0.016, M['chrome'], seg=6))
    P.append(box((0.02, 0.4, 3.3), (0.22, 1.28, 0), M['glass']))  # the sneeze guard
    P.append(rod((0.22, 1.5, -1.68), (0.22, 1.5, 1.68), 0.016, M['chrome'], seg=6))
    for k in range(5): P.append(box((0.4, 0.016, 0.3), (-0.15, 0.965 + k * 0.015, 1.3), (M['cyan'], M['pink'], M['yellow'])[k % 3], bev=0.004, rot=(0, k * 0.07, 0)))
    P.append(decal((0.302, 0.55, -0.9), 0.5, 0.24, M['l_menu'], axis='x'))
    return P


def lockers(paint):  # 2.0 x 0.5, 2.0 tall: four lockers, one of them never shut properly
    P = [box((2.0, 1.9, 0.46), (0, 1.03, -0.02), paint, bev=0.006), box((2.0, 0.08, 0.4), (0, 0.04, -0.04), M['dark']),
         box((2.02, 0.03, 0.5), (0, 1.985, 0), M['steel'], bev=0.006)]
    for i in range(4):
        x = -0.75 + i * 0.5; ajar = i == 2
        d = [box((0.46, 1.84, 0.02), (0, 0, 0), paint, bev=0.005)]
        for k in range(4): d.append(box((0.3, 0.014, 0.012), (0, 0.72 - k * 0.05, 0.012), M['dark']))
        for k in range(3): d.append(box((0.3, 0.014, 0.012), (0, -0.7 - k * 0.05, 0.012), M['dark']))
        d.append(box((0.03, 0.12, 0.03), (0.17, 0.05, 0.02), M['chrome'], bev=0.006))
        d.append(decal((0, 0.84, 0.0116), 0.1, 0.075, M['l_num']))
        if i == 1: d.append(decal((-0.05, 0.3, 0.0116), 0.12, 0.12, M['yellow']))  # a sticker
        o = join(d, 'door')
        o.location = gv(x + (0.23 if ajar else 0), 1.04, 0.222 if not ajar else 0.215)
        if ajar:  # swung on its hinge edge
            o.data.transform(Matrix.Translation(gv(-0.23, 0, 0))); o.rotation_euler = (0, 0, -0.5)
        P.append(o)
    P.append(box((0.3, 0.2, 0.28), (0.26, 0.3, -0.02), M['pink'], bev=0.03))  # what's in the open one: a gym bag
    return P


def labbench():  # 3.0 x 1.4, top 0.9
    P = [box((3.0, 0.06, 1.4), (0, 0.87, 0), M['slate'], bev=0.01), box((2.8, 0.74, 1.2), (0, 0.47, 0), M['lam'], bev=0.006), box((2.76, 0.1, 1.16), (0, 0.05, 0), M['dark'])]
    for sz in (-1, 1):
        for i in range(4):
            x = -1.05 + i * 0.7
            P.append(box((0.64, 0.6, 0.016), (x, 0.47, sz * 0.606), M['cream'], bev=0.006)); P.append(box((0.16, 0.02, 0.03), (x, 0.7, sz * 0.622), M['chrome'], bev=0.006))
    P.append(box((0.5, 0.012, 0.4), (-1.0, 0.902, 0), M['steel'], bev=0.004)); P.append(box((0.42, 0.014, 0.32), (-1.0, 0.905, 0), M['dark']))  # the sink
    P.append(tube([(-1.0, 0.9, -0.26), (-1.0, 1.22, -0.26), (-1.0, 1.3, -0.18), (-1.0, 1.24, -0.08)], 0.016, M['chrome'], seg=6))
    P.append(cyl(0.05, 0.025, (0.1, 0.912, 0.1), M['steel'], axis='y', seg=10)); P.append(cyl(0.016, 0.13, (0.1, 0.985, 0.1), M['chrome'], axis='y', seg=8))  # a burner, still lit
    P.append(cyl(0.02, 0.09, (0.1, 1.09, 0.1), M['flame'], axis='y', seg=8, r2=0.002))
    P.append(tube([(0.1, 0.92, 0.05), (0.2, 0.905, -0.2), (0.5, 0.905, -0.4)], 0.008, M['orange'], seg=4)); P.append(cyl(0.02, 0.07, (0.5, 0.93, -0.4), M['yellow'], axis='y', seg=8))
    P.append(lathe([(0.001, 0.0), (0.085, 0.0), (0.09, 0.03), (0.03, 0.14), (0.026, 0.22), (0.032, 0.225), (0.001, 0.225)], (0.75, 0.9, 0.25), M['glass'], seg=10, axis='y'))  # a flask of something
    P.append(lathe([(0.001, 0.004), (0.078, 0.004), (0.082, 0.03), (0.05, 0.085), (0.001, 0.085)], (0.75, 0.9, 0.25), M['goo'], seg=10, axis='y'))
    P.append(box((0.3, 0.05, 0.08), (1.1, 0.925, -0.3), M['wood'], bev=0.006))  # a test tube rack
    for i in range(4): P.append(cyl(0.014, 0.14, (0.99 + i * 0.075, 0.99, -0.3), (M['pink'], M['cyan'], M['yellow'], M['goo'])[i], axis='y', seg=6))
    return P


def fume():  # 2.6 x 1.0, 2.2 tall
    P = [box((2.6, 0.9, 1.0), (0, 0.45, 0), M['lam'], bev=0.008), box((2.64, 0.05, 1.04), (0, 0.925, 0), M['slate'], bev=0.008),
         box((2.6, 0.3, 1.0), (0, 2.05, 0), M['lam'], bev=0.008), box((0.08, 0.96, 1.0), (-1.26, 1.42, 0), M['lam']), box((0.08, 0.96, 1.0), (1.26, 1.42, 0), M['lam']),
         box((2.44, 0.96, 0.06), (0, 1.42, -0.47), M['cream']), box((2.44, 0.5, 0.02), (0, 1.66, 0.46), M['glass']), box((2.48, 0.05, 0.05), (0, 1.39, 0.47), M['steel'], bev=0.01)]
    P.append(cyl(0.2, 0.9, (0.6, 2.62, -0.1), M['steel'], axis='y', seg=10)); P.append(cyl(0.23, 0.05, (0.6, 2.4, -0.1), M['chrome'], axis='y', seg=10))
    for i in range(3): P.append(box((0.6, 0.5, 0.016), (-0.82 + i * 0.82, 0.45, 0.506), M['cream'], bev=0.006))
    P.append(lathe([(0.001, 0), (0.1, 0), (0.11, 0.04), (0.035, 0.2), (0.03, 0.3), (0.001, 0.3)], (-0.5, 0.95, 0), M['glass'], seg=10, axis='y'))
    P.append(lathe([(0.001, 0.004), (0.094, 0.004), (0.1, 0.04), (0.07, 0.11), (0.001, 0.11)], (-0.5, 0.95, 0), M['pink'], seg=10, axis='y'))
    for k in range(3): P.append(ball(0.05 + k * 0.02, (-0.5 + k * 0.05, 1.28 + k * 0.1, 0), M['white'], seg=8, rings=6))  # the fumes
    P.append(decal((0.7, 2.05, 0.502), 0.58, 0.22, M['l_fume']))
    return P


def boiler():  # 4 x 4, 2.6 tall (+ the flue)
    P = [lathe([(0.001, 0.1), (1.45, 0.1), (1.5, 0.18), (1.5, 2.1), (1.3, 2.42), (0.8, 2.58), (0.001, 2.62)], (-0.3, 0.0, -0.3), M['red'], seg=18, axis='y')]
    for y in (0.5, 1.3, 2.05): P.append(lathe([(1.5, -0.04), (1.53, -0.03), (1.53, 0.03), (1.5, 0.04)], (-0.3, y, -0.3), M['steel'], seg=18, axis='y', cap=False))
    P.append(cyl(0.3, 1.6, (-0.3, 3.35, -0.3), M['steel'], axis='y', seg=12)); P.append(cyl(0.34, 0.08, (-0.3, 2.66, -0.3), M['chrome'], axis='y', seg=12))
    P.append(box((1.0, 0.9, 0.7), (-0.3, 0.5, 1.45), M['dark'], bev=0.03)); P.append(box((0.5, 0.1, 0.04), (-0.3, 0.42, 1.81), M['glow']))  # the burner, its little window
    P.append(box((0.6, 0.3, 0.03), (-0.3, 0.75, 1.805), M['steel'], bev=0.01))
    P.append(rod((0.1, 0.9, 1.6), (0.1, 1.24, 1.6), 0.025, M['steel'], seg=6)); P.append(cyl(0.13, 0.05, (0.1, 1.33, 1.6), M['chrome'], axis='z', seg=12)); P.append(cyl(0.112, 0.06, (0.1, 1.33, 1.6), M['white'], axis='z', seg=12))  # a gauge
    P.append(box((0.012, 0.09, 0.012), (0.1, 1.35, 1.633), M['red'], rot=(0, 0, 0.6)))
    pipe = [(1.1, 0.3, -0.3), (1.6, 0.3, -0.3), (1.6, 0.3, 1.4), (1.6, 2.0, 1.4), (1.6, 2.0, 1.9)]
    P.append(tube(pipe, 0.09, M['steel'], seg=8)); P.append(tube([(-1.75, 1.6, -0.3), (-1.95, 1.6, -0.3), (-1.95, 3.4, -0.3)], 0.07, M['yellow'], seg=8))
    for p in ((1.6, 1.1, 1.4), (-1.95, 2.4, -0.3)):  # valve wheels
        P.append(tube([(p[0] + 0.16 * math.cos(a), p[1] + 0.16 * math.sin(a), p[2] + 0.14) for a in [i * math.pi / 4 for i in range(8)]], 0.018, M['blue'], seg=4, closed=True))
        P.append(rod((p[0], p[1], p[2]), (p[0], p[1], p[2] + 0.15), 0.02, M['steel'], seg=6))
        for a in (0, math.pi / 2): P.append(rod((p[0] - 0.16 * math.cos(a), p[1] - 0.16 * math.sin(a), p[2] + 0.14), (p[0] + 0.16 * math.cos(a), p[1] + 0.16 * math.sin(a), p[2] + 0.14), 0.012, M['blue'], seg=4))
    for a in (0.6, 2.2, 3.8, 5.4): P.append(box((0.22, 0.16, 0.22), (-0.3 + math.cos(a) * 1.4, 0.08, -0.3 + math.sin(a) * 1.4), M['steel'], bev=0.01))
    P.append(decal((-0.3, 1.55, 1.2315), 0.9, 0.31, M['l_boiler']))
    P.append(box((0.94, 0.35, 0.14), (-0.3, 1.55, 1.16), M['steel'], bev=0.004))
    return P


def vault():  # 1.6 x 0.8, 1.0 tall: a vaulting box, four tiers and a padded top
    P = []
    for k in range(4):
        w0 = 1.6 - k * 0.1; P.append(box((w0, 0.2, 0.8 - k * 0.07), (0, 0.11 + k * 0.205, 0), M['wood'], bev=0.012))
        for sx in (-1, 1): P.append(box((0.03, 0.06, 0.2), (sx * (w0 / 2 + 0.005), 0.11 + k * 0.205, 0), M['dark'], bev=0.006))
    P.append(box((1.26, 0.14, 0.56), (0, 0.89, 0), M['leather'], bev=0.045, seg=3))
    return P


def gymmat(m):  # 3 x 2, 0.3 thick: a crash mat, folded seams, handles
    P = [box((3.0, 0.28, 2.0), (0, 0.15, 0), m, bev=0.05, seg=3)]
    for x in (-0.75, 0, 0.75): P.append(box((0.03, 0.286, 2.01), (x, 0.15, 0), M['dark']))
    for x in (-1.1, 1.1):
        for sz in (-1, 1): P.append(tube([(x - 0.12, 0.15, sz * 1.0), (x - 0.1, 0.15, sz * 1.06), (x + 0.1, 0.15, sz * 1.06), (x + 0.12, 0.15, sz * 1.0)], 0.014, M['dark'], seg=4))
    return P


def hoop():  # on a wall behind it (-z): the board at z 0..0.06, the rim out to +0.62. origin on the floor under the board
    P = [box((1.8, 1.2, 0.05), (0, 3.2, 0.03), M['white'], bev=0.006), decal((0, 3.2, 0.0565), 1.74, 1.14, M['board'])]
    for sx in (-1, 1): P.append(tube([(sx * 0.6, 3.5, 0.0), (sx * 0.6, 3.6, -0.3)], 0.03, M['steel'], seg=6)); P.append(tube([(sx * 0.6, 2.9, 0.0), (sx * 0.6, 3.3, -0.3)], 0.03, M['steel'], seg=6))
    P.append(box((0.16, 0.12, 0.14), (0, 2.88, 0.12), M['orange'], bev=0.01))
    ring = lambda r, y, n=14: [(math.cos(i * 2 * math.pi / n) * r, y, 0.42 + math.sin(i * 2 * math.pi / n) * r) for i in range(n)]
    P.append(tube(ring(0.23, 2.9), 0.014, M['orange'], seg=6, closed=True))
    P.append(tube(ring(0.14, 2.5, 10), 0.008, M['net'], seg=4, closed=True)); P.append(tube(ring(0.19, 2.7, 10), 0.008, M['net'], seg=4, closed=True))
    for i in range(10):
        a, b = i * 2 * math.pi / 10, (i + 1) * 2 * math.pi / 10
        P.append(tube([(math.cos(a) * 0.23, 2.9, 0.42 + math.sin(a) * 0.23), (math.cos(b) * 0.19, 2.7, 0.42 + math.sin(b) * 0.19), (math.cos(a) * 0.14, 2.5, 0.42 + math.sin(a) * 0.14)], 0.006, M['net'], seg=4))
    return P


def ballrack():  # 1.6 x 0.6, 1.0 tall
    P = []
    for sx in (-1, 1):
        P.append(tube([(sx * 0.76, 0.06, -0.12), (sx * 0.76, 1.0, -0.12), (sx * 0.76, 1.0, 0.12), (sx * 0.76, 0.06, 0.12)], 0.02, M['steel'], seg=6))
        for sz in (-1, 1): P.append(cyl(0.05, 0.04, (sx * 0.76, 0.05, sz * 0.12), M['rubber'], axis='x', seg=8))
    for y in (0.3, 0.72):
        for z in (-0.12, 0.12): P.append(rod((-0.76, y, z), (0.76, y, z), 0.016, M['steel'], seg=6))
        for i in range(5 if y < 0.5 else 4): P.append(ball(0.14, (-0.56 + i * 0.29 + (0 if y < 0.5 else 0.12), y + 0.085, 0), M['ball'] if (i + int(y * 10)) % 4 else M['pink'], seg=10, rings=8))
    return P


def reception():  # 5 x 1.5, 1.1 tall: you stand on the +z side
    P = [box((5.0, 0.72, 0.9), (0, 0.38, -0.3), M['lam'], bev=0.008), box((5.04, 0.05, 0.96), (0, 0.765, -0.3), M['wood'], bev=0.01),
         box((5.0, 1.0, 0.5), (0, 0.56, 0.5), M['dwood'], bev=0.012), box((5.06, 0.05, 0.6), (0, 1.075, 0.5), M['wood'], bev=0.012), box((4.96, 0.08, 1.46), (0, 0.04, 0), M['dark'])]
    P.append(decal((0, 0.6, 0.7665), 2.6, 0.57, M['l_school']))
    P.append(box((2.7, 0.66, 0.04), (0, 0.6, 0.745), M['yellow'], bev=0.006))
    P.append(box((0.5, 0.34, 0.04), (-1.2, 1.02, -0.4), M['dark'], bev=0.01, rot=(-0.15, 3.0, 0))); P.append(box((0.08, 0.14, 0.08), (-1.2, 0.87, -0.4), M['dark'])); P.append(box((0.26, 0.02, 0.18), (-1.2, 0.8, -0.4), M['dark']))  # a monitor
    P.append(box((0.44, 0.015, 0.15), (-1.2, 0.798, -0.1), M['cream'], bev=0.004))
    P.append(lathe([(0.001, 0), (0.07, 0), (0.07, 0.015), (0.05, 0.04), (0.02, 0.06), (0.001, 0.062)], (1.2, 1.1, 0.5), M['chrome'], seg=10, axis='y')); P.append(cyl(0.012, 0.02, (1.2, 1.17, 0.5), M['chrome'], axis='y', seg=6))  # the bell
    P.append(box((0.24, 0.012, 0.32), (0.4, 1.106, 0.5), M['wood'], bev=0.004, rot=(0, 0.2, 0))); P.append(box((0.21, 0.004, 0.28), (0.4, 1.114, 0.5), M['white'], rot=(0, 0.2, 0)))  # sign in
    P.append(lathe([(0.001, 0), (0.11, 0), (0.14, 0.24), (0.001, 0.24)], (2.1, 1.1, 0.5), M['brick'], seg=8, axis='y'))  # a plant, plastic
    for i in range(6): a = i * 1.05; P.append(ball(0.09, (2.1 + math.cos(a) * 0.08, 1.44 + (i % 2) * 0.05, 0.5 + math.sin(a) * 0.08), M['green'], scale=(0.6, 1.7, 0.6), seg=6, rings=5, rot=(math.sin(a) * 0.4, 0, math.cos(a) * 0.4)))
    return P


def trophy():  # 0.6 x 3.0, 2.0 tall, long along z, the glass toward +x
    P = [box((0.6, 0.5, 3.0), (0, 0.25, 0), M['dwood'], bev=0.012), box((0.6, 0.08, 3.0), (0, 1.96, 0), M['dwood'], bev=0.012), box((0.05, 1.42, 2.92), (-0.275, 1.21, 0), M['dwood']),
         box((0.56, 1.42, 0.05), (0, 1.21, -1.475), M['dwood']), box((0.56, 1.42, 0.05), (0, 1.21, 1.475), M['dwood']), box((0.016, 1.4, 2.9), (0.285, 1.21, 0), M['glass'])]
    for y in (0.98, 1.46): P.append(box((0.54, 0.02, 2.92), (0.01, y, 0), M['glass']))
    cup = [(0.001, 0), (0.07, 0), (0.07, 0.02), (0.015, 0.05), (0.015, 0.12), (0.05, 0.16), (0.085, 0.3), (0.075, 0.3), (0.045, 0.17), (0.001, 0.17)]
    r = random.Random(5)
    for y in (0.5, 0.99, 1.47):
        for i in range(4):
            z = -1.1 + i * 0.73 + r.uniform(-0.1, 0.1); k = r.uniform(0.7, 1.25)
            P.append(lathe([(a * k, b * k) for a, b in cup], (0.02, y - 0.003, z), M['gold'] if r.random() < 0.7 else M['chrome'], seg=10, axis='y'))
    P.append(decal((0.3078, 0.28, 0.9), 0.42, 0.08, M['l_part'], axis='x'))
    P.append(box((0.012, 0.1, 0.44), (0.3, 0.28, 0.9), M['blue']))
    return P


def bookshelf():  # 2.0 x 0.7, 2.2 tall, books both sides, tiles along x
    P = [box((0.05, 2.2, 0.7), (-0.975, 1.1, 0), M['wood']), box((0.05, 2.2, 0.7), (0.975, 1.1, 0), M['wood']), box((1.9, 0.04, 0.7), (0, 2.18, 0), M['wood']),
         box((1.9, 2.1, 0.03), (0, 1.07, 0), M['dwood']), box((1.86, 0.1, 0.66), (0, 0.05, 0), M['dwood'])]
    for k in range(5):
        y = 0.1 + k * 0.41
        P.append(box((1.9, 0.03, 0.68), (0, y, 0), M['wood']))
        for f in (-1, 1): P += books(-0.93, 0.93, y + 0.015, f * 0.02, 0.3, 100 + k * 2 + (f > 0), face=f)
    return P


def readtable():  # 2.4 x 1.4, 0.8 tall, four chairs pushed in
    P = [box((2.4, 0.05, 1.4), (0, 0.775, 0), M['wood'], bev=0.012), box((2.2, 0.08, 1.2), (0, 0.71, 0), M['dwood'])]
    P += legs([(-1.1, -0.6), (1.1, -0.6), (-1.1, 0.6), (1.1, 0.6)], 0.72, 0.04, M['dwood'])
    for x, sz in ((-0.6, -1), (0.6, -1), (-0.6, 1), (0.6, 1)):
        P.append(box((0.42, 0.04, 0.4), (x, 0.45, sz * 0.62), M['blue'] if sz < 0 else M['pink'], bev=0.012)); P.append(box((0.42, 0.3, 0.04), (x, 0.8, sz * 0.83), M['blue'] if sz < 0 else M['pink'], bev=0.012))
        for dx in (-0.18, 0.18): P.append(rod((x + dx, 0, sz * 0.45), (x + dx, 0.45, sz * 0.45), 0.016, M['steel'], seg=5)); P.append(rod((x + dx, 0, sz * 0.83), (x + dx, 0.93, sz * 0.83), 0.016, M['steel'], seg=5))
    P.append(box((0.3, 0.03, 0.22), (-0.2, 0.816, 0.1), M['cream'], bev=0.006, rot=(0, 0.3, 0))); P.append(box((0.3, 0.012, 0.004), (-0.2, 0.833, 0.1), M['red'], rot=(0, 0.3 + 1.57, 0)))  # an open book
    P.append(lathe([(0.001, 0), (0.08, 0), (0.08, 0.02), (0.012, 0.03), (0.012, 0.26)], (0.7, 0.8, -0.2), M['gold'], seg=8, axis='y', cap=False)); P.append(cyl(0.05, 0.3, (0.7, 1.09, -0.2), M['green'], axis='x', seg=8))  # a banker's lamp
    return P


def easel():  # 0.9 x 0.6, 1.6 tall, the canvas toward +z
    P = [rod((-0.38, 0, 0.22), (-0.025, 1.6, -0.02), 0.022, M['wood'], seg=6), rod((0.38, 0, 0.22), (0.025, 1.6, -0.02), 0.022, M['wood'], seg=6), rod((0, 0, -0.28), (0, 1.6, -0.02), 0.022, M['wood'], seg=6),
         box((0.8, 0.04, 0.1), (0, 0.72, 0.15), M['wood'], bev=0.006), box((0.72, 0.64, 0.05), (0, 1.05, 0.11), M['white'], bev=0.004), box((0.5, 0.05, 0.12), (0, 1.3, 0.06), M['wood'])]
    P.append(decal((0, 1.05, 0.1365), 0.66, 0.58, M['art']))
    for i, m in enumerate((M['red'], M['blue'], M['yellow'])): P.append(cyl(0.03, 0.05, (-0.22 + i * 0.1, 0.76, 0.16), m, axis='y', seg=8))
    P.append(rod((0.2, 0.745, 0.17), (0.34, 0.75, 0.17), 0.008, M['dwood'], seg=5))
    return P


def kiln():  # 1.6 x 1.6, 1.8 tall
    P = [lathe([(0.001, 0.25), (0.72, 0.25), (0.75, 0.3), (0.75, 1.5), (0.72, 1.55), (0.001, 1.55)], (0, 0, 0), M['brick'], seg=10, axis='y'),
         lathe([(0.001, 1.56), (0.78, 1.56), (0.78, 1.72), (0.6, 1.78), (0.001, 1.8)], (0, 0, 0), M['steel'], seg=10, axis='y')]
    for y in (0.5, 0.95, 1.4): P.append(lathe([(0.75, -0.035), (0.775, -0.025), (0.775, 0.025), (0.75, 0.035)], (0, y, 0), M['steel'], seg=10, axis='y', cap=False))
    for a in (0.3, 1.87, 3.44, 5.0): P.append(rod((math.cos(a) * 0.55, 0, math.sin(a) * 0.55), (math.cos(a) * 0.55, 0.3, math.sin(a) * 0.55), 0.04, M['steel'], seg=6))
    P.append(box((0.3, 0.4, 0.14), (0.0, 0.95, 0.79), M['dark'], bev=0.012)); P.append(box((0.2, 0.05, 0.02), (0, 1.05, 0.862), M['glow'])); P.append(cyl(0.035, 0.03, (0, 0.88, 0.87), M['red'], axis='z', seg=8))
    P.append(tube([(-0.2, 1.75, 0.5), (-0.2, 1.86, 0.4), (0.2, 1.86, 0.4), (0.2, 1.75, 0.5)], 0.02, M['dark'], seg=5))
    P.append(decal((0.42, 1.2, 0.69), 0.32, 0.11, M['l_hot'])); P[-1].rotation_euler = (0, 0, 0)
    return P


def desk():  # 3.4 x 1.6, 0.9 tall: the principal's. too big on purpose. you sit on the -z side
    P = [box((3.4, 0.07, 1.6), (0, 0.865, 0), M['dwood'], bev=0.016), box((2.9, 0.012, 1.1), (0, 0.903, 0), M['green'], bev=0.004),
         box((0.9, 0.76, 1.4), (-1.15, 0.45, 0), M['dwood'], bev=0.01), box((0.9, 0.76, 1.4), (1.15, 0.45, 0), M['dwood'], bev=0.01), box((1.5, 0.6, 0.05), (0, 0.53, 0.6), M['dwood']),
         box((0.86, 0.07, 1.36), (-1.15, 0.035, 0), M['dark']), box((0.86, 0.07, 1.36), (1.15, 0.035, 0), M['dark'])]
    for x in (-1.15, 1.15):
        for k in range(3): P.append(box((0.74, 0.2, 0.02), (x, 0.2 + k * 0.235, -0.706), M['wood'], bev=0.006)); P.append(box((0.2, 0.025, 0.03), (x, 0.2 + k * 0.235, -0.722), M['gold'], bev=0.008))
    P.append(box((0.6, 0.11, 0.06), (0, 0.95, 0.6), M['dwood'], bev=0.01)); P.append(decal((0, 0.95, 0.6315), 0.56, 0.085, M['l_prin']))
    P.append(lathe([(0.001, 0), (0.045, 0), (0.048, 0.1), (0.04, 0.1), (0.038, 0.01), (0.001, 0.01)], (0.9, 0.91, -0.2), M['white'], seg=10, axis='y')); P.append(box((0.05, 0.04, 0.014), (0.9, 0.96, -0.152), M['white'])); P.append(decal((0.9, 0.96, -0.1436), 0.046, 0.036, M['l_boss']))  # the mug
    P.append(tube([(0.948, 0.99, -0.2), (0.985, 0.98, -0.2), (0.985, 0.94, -0.2), (0.948, 0.93, -0.2)], 0.008, M['white'], seg=4))
    for k in range(6): P.append(box((0.22, 0.009, 0.3), (-0.7, 0.913 + k * 0.007, 0.0), M['pink'] if k % 2 else M['white'], rot=(0, k * 0.09 - 0.2, 0)))  # detention slips
    P.append(box((0.22, 0.05, 0.2), (-1.3, 0.935, -0.3), M['dark'], bev=0.012)); P.append(box((0.07, 0.04, 0.2), (-1.38, 0.975, -0.3), M['dark'], bev=0.012))  # a phone
    P.append(tube([(-1.3, 0.95, -0.2), (-1.2, 0.92, -0.05), (-1.3, 0.92, 0.1)], 0.006, M['dark'], seg=4))
    P.append(lathe([(0.001, 0), (0.09, 0), (0.09, 0.02), (0.014, 0.03), (0.014, 0.34)], (0.3, 0.91, 0.3), M['gold'], seg=8, axis='y', cap=False)); P.append(lathe([(0.05, 0.3), (0.15, 0.3), (0.08, 0.46), (0.05, 0.46)], (0.3, 0.91, 0.3), M['green'], seg=10, axis='y'))
    return P


def bigchair():  # 0.9 x 0.9, seat 0.55, the back to 1.5
    P = [box((0.7, 0.14, 0.66), (0, 0.55, 0.02), M['leather'], bev=0.05, seg=3), box((0.7, 0.95, 0.14), (0, 1.02, -0.32), M['leather'], bev=0.05, seg=3, rot=(-0.12, 0, 0)),
         cyl(0.04, 0.36, (0, 0.3, 0), M['chrome'], axis='y', seg=8)]
    for sx in (-1, 1): P.append(box((0.08, 0.06, 0.5), (sx * 0.38, 0.78, 0.0), M['dwood'], bev=0.02)); P.append(rod((sx * 0.38, 0.55, 0.1), (sx * 0.38, 0.76, 0.1), 0.02, M['chrome'], seg=6))
    for i in range(5):
        a = i * 2 * math.pi / 5
        P.append(rod((0, 0.13, 0), (math.cos(a) * 0.4, 0.07, math.sin(a) * 0.4), 0.025, M['chrome'], seg=6)); P.append(ball(0.04, (math.cos(a) * 0.4, 0.04, math.sin(a) * 0.4), M['rubber'], seg=8, rings=6))
    for k in range(3): P.append(ball(0.02, (-0.18 + k * 0.18, 1.2, -0.262), M['gold'], seg=6, rings=4))  # buttons, to feel important
    return P


def stool():  # 0.7 x 0.7, 0.6 tall: the naughty stool
    P = [cyl(0.2, 0.05, (0, 0.575, 0), M['pink'], axis='y', seg=12, bev=0.01)]
    for i in range(3):
        a = i * 2.094 + 0.5; P.append(rod((math.cos(a) * 0.12, 0.56, math.sin(a) * 0.12), (math.cos(a) * 0.24, 0.0, math.sin(a) * 0.24), 0.02, M['wood'], seg=6))
    P.append(tube([(math.cos(i * 0.5236) * 0.19, 0.22, math.sin(i * 0.5236) * 0.19) for i in range(12)], 0.012, M['wood'], seg=4, closed=True))
    P.append(decal((0, 0.6016, 0), 0.26, 0.09, M['l_think'], axis='y'))
    return P


def filing():  # 0.7 x 1.0, 1.5 tall, two stacks side by side along z, the drawers toward -x
    P = [box((0.7, 1.46, 1.0), (0.0, 0.76, 0), M['steel'], bev=0.008), box((0.66, 0.04, 0.96), (0, 0.02, 0), M['dark'])]
    for iz in (-0.25, 0.25):
        for k in range(4):
            out = 0.22 if (iz > 0 and k == 2) else 0
            P.append(box((0.03 + out, 0.32, 0.44), (-0.352 - out / 2, 0.22 + k * 0.36, iz), M['cream'], bev=0.006))
            P.append(box((0.03, 0.03, 0.16), (-0.375 - out, 0.3 + k * 0.36, iz), M['chrome'], bev=0.008)); P.append(decal((-0.3685 - out, 0.2 + k * 0.36, iz), 0.14, 0.06, M['l_files'], axis='x', sx=-1))
    P.append(box((0.18, 0.2, 0.4), (-0.46, 1.03, 0.25), M['yellow']))  # the open one is full
    return P


def bench():  # 3.0 x 0.6, 0.45 tall
    P = []
    for z in (-0.2, -0.07, 0.07, 0.2): P.append(box((3.0, 0.04, 0.11), (0, 0.43, z), M['wood'], bev=0.012))
    for x in (-1.2, 1.2):
        P.append(tube([(x, 0.0, -0.26), (x, 0.4, -0.22), (x, 0.4, 0.22), (x, 0.0, 0.26)], 0.022, M['steel'], seg=6))
    return P


def arttable(seed=0):  # 2.6 x 1.2, 0.8 tall: paint everywhere
    P = [box((2.6, 0.06, 1.2), (0, 0.77, 0), M['wood'], bev=0.012), box((2.4, 0.08, 1.0), (0, 0.7, 0), M['dwood'])]
    P += legs([(-1.2, -0.5), (1.2, -0.5), (-1.2, 0.5), (1.2, 0.5)], 0.72, 0.035, M['dwood'])
    r = random.Random(3 + seed)
    for i, m in enumerate((M['pink'], M['cyan'], M['yellow'], M['red'], M['goo'])):
        x, z = r.uniform(-1.0, 1.0), r.uniform(-0.4, 0.4)
        P.append(cyl(r.uniform(0.07, 0.16), 0.012 + i * 0.006, (x, 0.802 + i * 0.0015, z), m, axis='y', seg=9))  # splats
        P.append(cyl(0.045, 0.1, (-1.0 + i * 0.14, 0.85, -0.42), M['white'], axis='y', seg=8)); P.append(cyl(0.04, 0.012, (-1.0 + i * 0.14, 0.902, -0.42), m, axis='y', seg=8))  # pots
    P.append(cyl(0.05, 0.13, (0.9, 0.865, 0.35), M['glass'], axis='y', seg=8))
    for k in range(3): P.append(rod((0.9, 0.82, 0.35), (0.86 + k * 0.05, 1.08, 0.33 + k * 0.03), 0.006, M['dwood'], seg=4))  # brushes in a jar
    P.append(box((0.42, 0.005, 0.3), (0.2, 0.8, 0.1), M['white'], rot=(0, 0.3, 0)))
    return P


def studentdesk():  # 0.7 x 0.9, 0.75 tall: the chair-desk combo, facing +z (the board)
    P = [box((0.6, 0.03, 0.42), (0, 0.74, 0.2), M['lam'], bev=0.01), box((0.5, 0.1, 0.3), (0, 0.66, 0.2), M['steel'], bev=0.01),
         box((0.42, 0.04, 0.4), (0, 0.45, -0.2), M['blue'], bev=0.014), box((0.42, 0.3, 0.04), (0, 0.8, -0.4), M['blue'], bev=0.014)]
    for sx in (-1, 1):
        P.append(tube([(sx * 0.2, 0.0, -0.4), (sx * 0.2, 0.92, -0.4)], 0.016, M['steel'], seg=5)); P.append(tube([(sx * 0.2, 0.0, -0.02), (sx * 0.2, 0.44, -0.02)], 0.016, M['steel'], seg=5))
        P.append(tube([(sx * 0.27, 0.0, 0.38), (sx * 0.27, 0.72, 0.38)], 0.016, M['steel'], seg=5)); P.append(rod((sx * 0.2, 0.1, -0.4), (sx * 0.27, 0.1, 0.38), 0.012, M['steel'], seg=4))
    P.append(box((0.2, 0.012, 0.26), (0.05, 0.761, 0.2), M['white'], rot=(0, 0.25, 0))); P.append(rod((-0.2, 0.762, 0.12), (-0.08, 0.762, 0.3), 0.007, M['yellow'], seg=5))
    return P


def bin_():  # 0.5 x 0.5, 0.8 tall
    P = [lathe([(0.001, 0.0), (0.19, 0.0), (0.24, 0.7), (0.25, 0.72), (0.22, 0.72), (0.175, 0.03), (0.001, 0.03)], (0, 0, 0), M['green'], seg=10, axis='y')]
    for i, m in enumerate((M['white'], M['pink'], M['cream'], M['yellow'])): P.append(ball(0.1, (math.cos(i * 1.6) * 0.13, 0.68 + (i % 2) * 0.06, math.sin(i * 1.6) * 0.09), m, seg=6, rings=4, scale=(1, 0.8, 1.1)))
    return P


def fountain():  # 0.5 x 0.4 on a wall behind it (-z), 1.0 tall
    P = [box((0.46, 0.5, 0.36), (0, 0.72, 0.0), M['steel'], bev=0.03), box((0.4, 0.02, 0.28), (0, 0.975, 0.02), M['dark'], bev=0.004), box((0.1, 0.7, 0.1), (0, 0.35, -0.12), M['steel'])]
    P.append(tube([(0.12, 0.97, -0.08), (0.12, 1.05, -0.08), (0.08, 1.07, -0.02)], 0.012, M['chrome'], seg=5)); P.append(box((0.3, 0.05, 0.02), (0, 0.8, 0.188), M['chrome'], bev=0.008))
    arc = [(0.08, 1.07, -0.02), (0.05, 1.105, 0.005), (0.02, 1.12, 0.03), (-0.01, 1.095, 0.055), (-0.04, 1.04, 0.08), (-0.06, 0.985, 0.1)]
    P.append(stream_uv(sweep(arc, [0.008, 0.008, 0.008, 0.009, 0.01, 0.011], M['water'], seg=6, name='sk_drink_water'), arc, 6))  # it never turned off (*_water: the game makes it flow)
    return P


def globe():  # 0.6 x 0.6, 1.3 tall
    P = [lathe([(0.001, 0), (0.22, 0), (0.22, 0.03), (0.03, 0.06), (0.025, 0.8), (0.001, 0.8)], (0, 0, 0), M['dwood'], seg=10, axis='y'), ball(0.24, (0, 1.04, 0), M['blue'], seg=12, rings=8)]
    for a, b, s in ((0.5, 0.3, 0.1), (2.2, -0.2, 0.12), (3.6, 0.4, 0.09), (5.0, 0.0, 0.11), (1.2, -0.5, 0.07)):
        P.append(ball(s, (math.cos(a) * math.cos(b) * 0.2, 1.04 + math.sin(b) * 0.2, math.sin(a) * math.cos(b) * 0.2), M['green'], seg=6, rings=5, scale=(1, 1.2, 1)))
    P.append(tube([(0, 0.78, 0), (0.2, 0.82, 0), (0.3, 1.04, 0), (0.2, 1.27, 0), (0, 1.31, 0)], 0.012, M['gold'], seg=5))
    return P


V = {'lunchtable': lunchtable, 'servery': servery, 'lockers': lambda: lockers(M['blue']), 'lockersp': lambda: lockers(M['pink']), 'labbench': labbench, 'fume': fume,
     'boiler': boiler, 'vault': vault, 'gymmat': lambda: gymmat(M['blue']), 'gymmatp': lambda: gymmat(M['pink']), 'hoop': hoop, 'ballrack': ballrack, 'reception': reception,
     'trophy': trophy, 'bookshelf': bookshelf, 'readtable': readtable, 'easel': easel, 'kiln': kiln, 'desk': desk, 'bigchair': bigchair, 'stool': stool, 'filing': filing,
     'bench': bench, 'arttable': arttable, 'studentdesk': studentdesk, 'bin': bin_, 'fountain': fountain, 'globe': globe}


ORDER = []
SPACING = 6.0


def build(names=None, spacing=6.0):
    global SPACING
    SPACING = spacing; ORDER[:] = list(names or V)
    mats()
    parts = []
    for i, n in enumerate(names or V):
        objs = [o for o in V[n]() if o is not None]
        for o in objs:
            apply_mods(o)
            if not o.get('keep_uv'): uv_box(o, 0.5)
        p = part(objs, n, pivot=(0, 0, 0))
        me = p.data; me.calc_loop_triangles(); print('JF_PART', n, len(me.loop_triangles), [round(v, 2) for v in (*p.bound_box[0], *p.bound_box[6])])
        p.location.x += i * spacing  # side by side in the file (the game resets each one to its own origin)
        parts.append(p)
    return finish('p_schoolkit', parts, {'kind': 'prop', 'id': 'schoolkit', 'variants': list(names or V)})


def qa(root):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.claude', 'skills', 'blender-asset-qa', 'scripts'))
    import qa_check
    hits = set()
    if os.environ.get('JF_ZF_DEBUG'):  # where the coplanar faces are (piece, x, height, z), to find a z-fight by hand
        pit = qa_check._point_in_tri
        def spy(q, a, b, c, n):
            r = pit(q, a, b, c, n)
            if r and sys._getframe(1).f_locals.get('d', 0) > 0: k = round(q.x / SPACING); hits.add((k, round(q.x - k * SPACING, 2), round(q.z, 3), round(-q.y, 2), round(abs(n.x), 1), round(abs(n.z), 1), round(abs(n.y), 1)))
            return r
        qa_check._point_in_tri = spy
    bpy.context.view_layer.update()
    res = qa_check.run(objects=[o.name for o in root.children], profile='game')
    print('JF_QA', 'schoolkit', 'PASS' if res['pass'] else 'FAIL', len(res['errors']), 'errors', len(res['warnings']), 'warnings')
    for e in res['errors']: print('JF_QA_E', str(e)[:300])
    for w in res['warnings']: print('JF_QA_W', str(w)[:200])
    names = ORDER
    for h in sorted(hits): print('JF_ZF', names[h[0]] if 0 <= h[0] < len(names) else h[0], h[1:])


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = [a.split('=')[1].split(',') for a in argv if a.startswith('--only=')]
    reset()
    if only:  # a review sheet of a few pieces, close together
        root = build(only[0], spacing=max(3.4, 1.0))
        if '--qa' in argv: qa(root)
        sheet(root, 'p_schoolkit_' + only[0][0], views=('persp', 'front', 'back_persp', 'top'), res=(900, 420))
    else:
        root = build()
        if '--qa' in argv: qa(root)
        if '--no-export' not in argv: export(root, 'p_schoolkit')
