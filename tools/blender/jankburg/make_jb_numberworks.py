# Number Works' yard (shared/jankburg.js numberWorks(), the toy factory district): the three smokestacks you can see
# from anywhere (p_jb_stack), the vats of something green (p_jb_vat), the chrome pipe runs (p_jb_pipe) and the
# columns they sit on (p_jb_pipepost).
#   stack: a square industrial chimney in red brick: a concrete plinth, a corbelled brick band under each of the three
#          hazard-striped steel bands (the boxes' bands), NUMBER WORKS down one face in white, a caged ladder up the
#          side, a soot-black crown under a cast-iron cap, a lightning rod and red aircraft lights.
#          frame: x / z -3..3, y 0..63 (the brick shaft is -2.5..2.5)
#   vat:   a square riveted steel tank, plates and stiffener ribs painted oxide red and peeling, a gauge and a valve
#          wheel out front, a MAY CONTAIN NUMBERS sign, a ladder, a chrome rim round the top and the glowing green
#          soup inside with bubbles. frame: x / z -3.8..3.8, y 0..7.4
#   pipe:  a 1 m chrome pipe with flanged joints every 5.5 m and a lagged (insulated) stretch, 22 m reference length
#          (fitted along x onto each run). frame: x -11..11, y 0..1.2 (the run's underside at 0), z -0.6..0.6
#   post:  an I-beam column with a base plate and a saddle on top. frame: x / z -0.3..0.3, y 0..7
# Look only: the boxes stay the collision.
# run: blender52 -b --python tools/blender/jankburg/make_jb_numberworks.py -- [--qa] [--no-sheet] [--no-export] [--only=stack,vat,pipe,post]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Matrix
import jbkit as K
from jbkit import ARGV, Atlas, boxa, fill_uv, mesh, noise
import lib
from lib import mat, text_px, hexrgb, px_disc, rod, _image, uv_box

ONLY = set(next((a.split('=', 1)[1] for a in ARGV if a.startswith('--only=')), '').split(',')) - {''}
rng = np.random.default_rng(713)


def brick_tex(S=64):
    v = np.zeros((S, S, 3), np.float32); r = np.random.default_rng(3)
    for row in range(8):
        off = 8 * (row % 2)
        for col in range(-1, 5):
            c = hexrgb(0xa8402a) * (0.8 + 0.3 * r.random())
            if r.random() < 0.08: c = hexrgb(0x6a2a1a)
            x0 = col * 16 + off
            v[row * 8:row * 8 + 8, max(0, x0):max(0, min(S, x0 + 16))] = c
    v[::8] = hexrgb(0x8a8078);
    for row in range(8):
        off = 8 * (row % 2)
        for col in range(5): v[row * 8:row * 8 + 8, (col * 16 + off) % S] = hexrgb(0x8a8078)
    v *= (0.9 + 0.12 * noise(S, S, r, 8, 0.4)[..., None])
    return _image('jbn_brick', np.clip(v, 0, 1))


A = Atlas('jbn_atlas', 256, 256, 0x808080)
v = A.add('hazard', 0, 0, 64, 8)
for k in range(-8, 64, 8):
    for j in range(8): v[j, max(0, k + j):max(0, k + j + 4)] = hexrgb(0xffcc22)
v[v.sum(2) < 1.0] = hexrgb(0x16141a)
v = A.add('soot', 0, 8, 32, 32); v[:] = hexrgb(0x2a2422) * (0.8 + 0.3 * noise(32, 32, rng, 4, 0.5)[..., None])
v = A.add('iron', 32, 8, 32, 32); v[:] = hexrgb(0x5a3a2a) * (0.8 + 0.3 * noise(32, 32, rng, 4, 0.6)[..., None])
v = A.add('conc', 64, 8, 32, 32); v[:] = hexrgb(0x9a9a9e) * (0.85 + 0.2 * noise(32, 32, rng, 4, 0.5)[..., None])
v = A.add('letters', 96, 0, 16, 128); v[:] = 0; t = np.zeros((128, 16, 3), np.float32)  # NUMBER / WORKS down a face
for i, ch in enumerate('NUMBER'): text_px(t, ch, 5, 4 + i * 9, 1, 0xffffff)
for i, ch in enumerate('WORKS'): text_px(t, ch, 5, 64 + i * 9, 1, 0xffffff)
v[:] = t
v = A.add('tank', 112, 0, 64, 64)  # oxide-red plates, rivet rows, peeling to grey primer, rust runs
v[:] = hexrgb(0xa83a2a) * (0.85 + 0.2 * noise(64, 64, rng, 8, 0.4)[..., None])
peel = noise(64, 64, rng, 8, 0.2) > 0.72; v[peel] = hexrgb(0x8a8a90)
v[::16] = hexrgb(0x6a2018); v[:, ::16] = hexrgb(0x6a2018)
v[2::16, 3::4] = hexrgb(0xd08070); v[13::16, 3::4] = hexrgb(0xd08070)
for c in rng.choice(64, 10, replace=False): ln = int(10 + 30 * rng.random()); y0 = int(64 * rng.random() * 0.5); v[y0:y0 + ln, c] = hexrgb(0x5a2a10)
v = A.add('sign', 176, 0, 64, 40); v[:] = hexrgb(0xffe14d); v[:3] = v[-3:] = v[:, :3] = v[:, -3:] = hexrgb(0x111018)
for txt, row in (('MAY', 6), ('CONTAIN', 16), ('NUMBERS', 26)):
    tw = len(txt) * 6 - 1; text_px(v, txt, 32 - tw // 2, row, 1, 0x111018)
v = A.add('gauge', 176, 40, 32, 32); v[:] = hexrgb(0x16101e); px_disc(v, 16, 16, 15, 0xd8e0e8); px_disc(v, 16, 16, 13, 0xfff8e8)
for k in range(9): a = -2.2 + k * 0.55; px_disc(v, 16 + 10 * math.sin(a), 16 - 10 * math.cos(a), 1, 0xff3030 if k > 6 else 0x16101e)
lib.px_line(v, 16, 16, 24, 9, 0xff3030, 1.5)
v = A.add('soup', 0, 64, 64, 64); v[:] = hexrgb(0x39ff14) * (0.7 + 0.35 * noise(64, 64, rng, 8, 0.5)[..., None])
for k in range(14): px_disc(v, 64 * rng.random(), 64 * rng.random(), 2 + 3 * rng.random(), 0xb0ff90, r_in=1.2)
v = A.add('lag', 64, 64, 32, 32); v[:] = hexrgb(0xd8d8d0) * (0.9 + 0.1 * noise(32, 32, rng, 4)[..., None]); v[::8] = hexrgb(0x8a8a88)
for key, x, y, c in (('chrome', 96, 128, 0xd8e0e8), ('metal', 112, 128, 0x5a5f6e), ('dark', 128, 128, 0x24222c), ('yellow', 144, 128, 0xffcc22),
                     ('white', 160, 128, 0xeeeeee), ('red', 176, 128, 0xff3030), ('steel', 192, 128, 0x7a8090)):
    v = A.add(key, x, y, 16, 16); v[:] = hexrgb(c) * (0.92 + 0.1 * rng.random((16, 16, 1)))


def mats():
    lib.reset(); lib._mats.clear()
    return {'brick': mat('jbn_brick', 0xffffff, rough=0.8, tex=brick_tex()), 'trim': mat('jbn_trim', 0xffffff, rough=0.5, tex=A.image()),
            'chrome': mat('jbn_chrome', 0xd8e0e8, rough=0.15, metal=1.0), 'soup': mat('jbn_soup', 0xffffff, rough=0.2, emit=0xffffff, strength=1.2, tex=A.image(), emit_tex=True),
            'red': mat('glow_red', 0xff3030, rough=0.3, emit=0xff3030, strength=2.0)}


def ring4(name, h0, h1, y0, y1, m, cells):
    """a square band round a shaft: outer half-size h0, inner h1"""
    sub = {k: c for k, c in cells.items() if k not in ('-z', '+z')}
    return [boxa(name, (-h0, y0, -h0), (h0, y1, -h1), m, A, cells), boxa(name, (-h0, y0, h1), (h0, y1, h0), m, A, cells),
            boxa(name, (-h0, y0, -h1 + 0.001), (-h1, y1, h1 - 0.001), m, A, sub), boxa(name, (h1, y0, -h1 + 0.001), (h0, y1, h1 - 0.001), m, A, sub)]


# ------------------------------------------------------------ the smokestack
def stack():
    M = mats(); P, Q = [], []
    S = 2.5
    o = boxa('s_shaft', (-S, 1.5, -S), (S, 62.0, S), M['brick'], A, {k: 'conc' for k in ('-z', '+z', '-x', '+x')}); uv_box(o, 1.6); P.append(o)
    P.append(boxa('s_plinth', (-2.7, 0, -2.7), (2.7, 1.5, 2.7), M['trim'], A, {k: 'conc' for k in ('-z', '+z', '-x', '+x', '+y')}))
    for y in (20, 40, 58):  # the steel bands (exactly the boxes), a corbelled course of brick under each
        P += ring4('s_band', 2.9, 2.5, y, y + 1.4, M['trim'], {'-z': 'hazard', '+z': 'hazard', '-x': 'hazard', '+x': 'hazard', '+y': 'metal', '-y': 'metal'})
        for o in ring4('s_corbel', 2.65, 2.5, y - 0.5, y, M['brick'], {'-z': 'conc', '+z': 'conc', '-x': 'conc', '+x': 'conc', '-y': 'conc'}): uv_box(o, 1.6); P.append(o)
    P.append(boxa('s_letters', (-0.45, 26.0, -2.53), (0.45, 38.0, -2.499), M['trim'], A, {'-z': 'letters', '-x': 'dark', '+x': 'dark', '+y': 'dark', '-y': 'dark'}))
    for o in ring4('s_crown', 2.6, 2.5, 59.6, 62.0, M['trim'], {'-z': 'soot', '+z': 'soot', '-x': 'soot', '+x': 'soot'}): P.append(o)
    P += ring4('s_cap', 3.0, 1.9, 62.0, 63.0, M['trim'], {'-z': 'iron', '+z': 'iron', '-x': 'iron', '+x': 'iron', '+y': 'iron', '-y': 'iron'})
    P.append(boxa('s_flue', (-1.9, 61.0, -1.9), (1.9, 62.9, 1.9), M['trim'], A, {'+y': 'dark'}))  # the black hole down the middle
    # the caged ladder up the +x face
    for zz in (-0.35, 0.35):
        P.append(fill_uv(rod((2.95, 1.5, zz), (2.95, 61.0, zz), 0.035, M['trim'], seg=6, name='s_rail'), A, 'steel'))
    for y in np.arange(2.0, 61.0, 0.6):
        P.append(fill_uv(rod((2.95, y, -0.35), (2.95, y, 0.35), 0.02, M['trim'], seg=4, name='s_rung'), A, 'steel'))
    for y in np.arange(5.1, 57.0, 2.0):  # the cage hoops (a three-sided frame) and the wall brackets
        for a, b in (((2.48, y, -0.4), (3.5, y, -0.4)), ((3.5, y, -0.4), (3.5, y, 0.4)), ((3.5, y, 0.4), (2.48, y, 0.4))):
            P.append(fill_uv(rod(a, b, 0.025, M['trim'], seg=4, name='s_hoop'), A, 'steel'))
    for zz in (-0.4, 0.4):
        P.append(fill_uv(rod((3.5, 4.0, zz), (3.5, 58.0, zz), 0.025, M['trim'], seg=4, name='s_cage_rail'), A, 'steel'))
    P.append(fill_uv(rod((-2.2, 63.0, -2.2), (-2.2, 66.0, -2.2), 0.04, M['trim'], seg=6, name='s_rod'), A, 'steel'))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.append(boxa('s_aclight', (sx * 2.75 - 0.12, 63.0, sz * 2.75 - 0.12), (sx * 2.75 + 0.12, 63.25, sz * 2.75 + 0.12), M['red'], A, {k: 'red' for k in K.SIDES}))
    o = boxa('s1_shaft', (-S, 0, -S), (S, 62.0, S), M['brick'], A, {k: 'conc' for k in ('-z', '+z', '-x', '+x')}); uv_box(o, 1.6); Q.append(o)
    for y in (20, 40, 58): Q.append(boxa('s1_band', (-2.9, y, -2.9), (2.9, y + 1.4, 2.9), M['trim'], A, {'-z': 'hazard', '+z': 'hazard', '-x': 'hazard', '+x': 'hazard', '+y': 'metal', '-y': 'metal'}))
    Q.append(boxa('s1_cap', (-3, 62, -3), (3, 63, 3), M['trim'], A, {'-z': 'iron', '+z': 'iron', '-x': 'iron', '+x': 'iron', '+y': 'soot', '-y': 'iron'}))
    return P, Q, ((-3, 0, -3), (3, 63, 3)), 300


# ------------------------------------------------------------ the vat
def vat():
    M = mats(); P, Q = [], []
    S = 3.5
    P.append(boxa('v_tank', (-S, 0, -S), (S, 7.0, S), M['trim'], A, {k: 'tank' for k in ('-z', '+z', '-x', '+x')}))
    for k in (-2.0, 0.0, 2.0):  # stiffener ribs up each face
        for s in (-1, 1):
            P.append(boxa('v_rib', (k - 0.08, 0.2, min(s * S, s * (S + 0.12))), (k + 0.08, 6.8, max(s * S, s * (S + 0.12))), M['trim'], A, {('-z' if s < 0 else '+z'): 'tank', '-x': 'tank', '+x': 'tank', '+y': 'tank', '-y': 'tank'}))
            P.append(boxa('v_rib', (min(s * S, s * (S + 0.12)), 0.2, k - 0.08), (max(s * S, s * (S + 0.12)), 6.8, k + 0.08), M['trim'], A, {('-x' if s < 0 else '+x'): 'tank', '-z': 'tank', '+z': 'tank', '+y': 'tank', '-y': 'tank'}))
    P += ring4('v_rim', 3.8, 3.2, 7.0, 7.4, M['trim'], {'-z': 'chrome', '+z': 'chrome', '-x': 'chrome', '+x': 'chrome', '+y': 'chrome', '-y': 'chrome'})
    P.append(boxa('v_soup', (-3.2, 7.0, -3.2), (3.2, 7.34, 3.2), M['soup'], A, {'+y': 'soup'}))
    for bx, bz, br in ((-1.8, -1.2, 0.4), (0.9, -2.1, 0.28), (1.7, 1.1, 0.45), (-0.6, 1.8, 0.22), (-2.2, 2.3, 0.3)):  # bubbles in the soup
        b = K.lathe_closed('v_bubble', [(0.02, 7.33), (br, 7.33), (br * 0.7, 7.33 + br * 0.6), (0.02, 7.33 + br * 0.75)], (bx, 0, bz), M['soup'], seg=10)
        fill_uv(b, A, 'soup'); P.append(b)
    P.append(boxa('v_sign', (-1.0, 3.8, -S - 0.05), (1.0, 5.05, -S - 0.01), M['trim'], A, {'-z': 'sign', '-x': 'yellow', '+x': 'yellow', '+y': 'yellow', '-y': 'yellow'}))
    g = K.lathe_closed('v_gauge', [(0.02, -0.12), (0.32, -0.12), (0.32, 0.001), (0.02, 0.001)], (0, 0, 0), M['trim'], seg=14, axis='z')
    fill_uv(g, A, 'gauge'); g.data.transform(Matrix.Translation(lib.gv(1.0, 2.6, -S))); P.append(g)
    wheel = K.lathe_closed('v_valve', [(0.34, -0.03), (0.42, -0.03), (0.42, 0.03), (0.34, 0.03)], (0, 0, 0), M['trim'], seg=12, axis='z')
    wheel.data.transform(Matrix.Translation(lib.gv(-1.9, 1.6, -S - 0.4))); fill_uv(wheel, A, 'red'); P.append(wheel)
    P.append(fill_uv(rod((-1.9, 1.6, -S - 0.4), (-1.9, 1.6, -S + 0.01), 0.06, M['trim'], seg=6, name='v_stem'), A, 'steel'))
    for xx in (-1.0, -0.4):  # a ladder up the +x side to the rim
        P.append(fill_uv(rod((S + 0.25, 0.0, xx), (S + 0.25, 7.6, xx), 0.03, M['trim'], seg=6, name='v_lrail'), A, 'steel'))
    for y in np.arange(0.4, 7.2, 0.45):
        P.append(fill_uv(rod((S + 0.25, y, -1.0), (S + 0.25, y, -0.4), 0.018, M['trim'], seg=4, name='v_rung'), A, 'steel'))
    for y in (1.0, 6.0):
        for xx in (-1.0, -0.4): P.append(fill_uv(rod((S - 0.01, y, xx), (S + 0.25, y, xx), 0.02, M['trim'], seg=4, name='v_lbracket'), A, 'steel'))
    Q.append(boxa('v1_tank', (-S, 0, -S), (S, 7.0, S), M['trim'], A, {k: 'tank' for k in ('-z', '+z', '-x', '+x')}))
    Q += ring4('v1_rim', 3.8, 3.2, 7.0, 7.4, M['trim'], {'-z': 'chrome', '+z': 'chrome', '-x': 'chrome', '+x': 'chrome', '+y': 'chrome', '-y': 'chrome'})
    Q.append(boxa('v1_soup', (-3.2, 7.0, -3.2), (3.2, 7.34, 3.2), M['soup'], A, {'+y': 'soup'}))
    return P, Q, ((-3.8, 0, -3.8), (3.8, 7.4, 3.8)), 120


# ------------------------------------------------------------ the pipe run and its posts
def pipe():
    M = mats(); P, Q = [], []
    L, y, r = 11.0, 0.6, 0.5
    P.append(K.lathe_closed('p_pipe', [(0.42, -L), (r, -L), (r, L), (0.42, L)], (0, y, 0), M['chrome'], seg=16, axis='x'))
    fill_uv(P[-1], A, 'chrome')
    for x in (-8.25, -2.75, 2.75, 8.25):  # flanged joints with bolt heads
        f = K.lathe_closed('p_flange', [(r - 0.01, -0.08), (0.62, -0.08), (0.62, 0.08), (r - 0.01, 0.08)], (x, y, 0), M['trim'], seg=16, axis='x'); fill_uv(f, A, 'steel'); P.append(f)
    lag = K.lathe_closed('p_lag', [(r - 0.01, -2.4), (0.58, -2.4), (0.58, 2.4), (r - 0.01, 2.4)], (0.0, y, 0), M['trim'], seg=16, axis='x')
    fill_uv(lag, A, 'lag'); P.append(lag)
    for x in (-L, L):  # blind end caps
        P.append(K.lathe_closed('p_cap', [(0.02, -0.06), (0.56, -0.06), (0.56, 0.06), (0.02, 0.06)], (x, y, 0), M['trim'], seg=16, axis='x')); fill_uv(P[-1], A, 'steel')
    Q.append(K.lathe_closed('p1_pipe', [(0.02, -L), (r, -L), (r, L), (0.02, L)], (0, y, 0), M['chrome'], seg=8, axis='x')); fill_uv(Q[-1], A, 'chrome')
    return P, Q, ((-11, 0, -0.6), (11, 1.2, 0.6)), 80


def post():
    M = mats(); P, Q = [], []
    P.append(boxa('q_web', (-0.04, 0.05, -0.28), (0.04, 6.95, 0.28), M['trim'], A, {k: 'steel' for k in K.SIDES}))
    for zz in (-0.3, 0.26):
        P.append(boxa('q_flange', (-0.3, 0.05, zz), (0.3, 6.95, zz + 0.04), M['trim'], A, {k: 'steel' for k in K.SIDES}))
    P.append(boxa('q_base', (-0.4, 0.0, -0.4), (0.4, 0.05, 0.4), M['trim'], A, {k: 'steel' for k in K.SIDES if k != '-y'}))
    P.append(boxa('q_saddle', (-0.35, 6.95, -0.35), (0.35, 7.0, 0.35), M['trim'], A, {k: 'yellow' for k in K.SIDES}))
    Q.append(boxa('q1', (-0.3, 0, -0.3), (0.3, 7.0, 0.3), M['trim'], A, {k: 'steel' for k in ('-z', '+z', '-x', '+x', '+y')}))
    return P, Q, ((-0.3, 0, -0.3), (0.3, 7.0, 0.3)), 60


def build(fid, fn, note):
    P, Q, box, lod = fn()
    for o in P + Q: lib.apply_mods(o)
    if '--qa-parts' in ARGV:
        sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
        import qa_check
        res = qa_check.run(objects=[o.name for o in P], profile='game', eps=0.0008, tol=0.002)
        for e in res.get('errors', []): print('QAP', fid, str(e)[:200])
        return
    m0 = lib.join(P, fid + '_lod0'); m1 = lib.join(Q, fid + '_lod1')  # (not welded: bands and rings butt together, welding their corners flips windings)
    if '--qa' in ARGV: K.qa([m0], fid + ' lod0'); K.qa([m1], fid + ' lod1')
    lib.bake_ao([m0], dist=0.8); lib.bake_ao([m1], dist=0.8)
    root = lib.prop_finish(fid, [m0], [m1], {'id': fid[2:], 'kind': 'prop', 'lod': lod, 'tint': False, 'box': [list(box[0]), list(box[1])]})
    lib.prop_stats(root)
    if '--no-export' not in ARGV: lib.export(root, fid)
    if '--no-sheet' not in ARGV:
        e = next(c for c in root.children if c.name.startswith('lod1')); e.parent = None; m1.hide_render = True
        lib.sheet(root, fid, extra_note=note, exposure=-0.2)


for key, fid, fn, note in (('stack', 'p_jb_stack', stack, 'NUMBER WORKS STACK'), ('vat', 'p_jb_vat', vat, 'NUMBER WORKS VAT'),
                           ('pipe', 'p_jb_pipe', pipe, 'PIPE RUN'), ('post', 'p_jb_pipepost', post, 'PIPE POST')):
    if not ONLY or key in ONLY: build(fid, fn, note)
