# JANKCORP HQ (shared/jankburg.js hq() -> map.js tower(): 4 tiers, glass, a helipad on the roof): p_jb_hq.
# The tallest thing in the city, as a setback skyscraper in a glass curtain wall: each tier a grid of mullions, spandrel
# bands at every floor and a scatter of lit offices (somebody always stays late), chrome fins up the corners and
# every few metres, terraces with glass balustrades on a chrome rail, a lobby with a revolving door and gold JANKCORP
# HQ letters on the south front, the steel frames the two 40 m logo banners hang in (the banners are the map's), and the
# crown: a lit JANK / CORP sign on all four sides, a parapet, the stair house, a skylight, red aircraft lights and a
# mast with a beacon.
# Frame: centred on the tower (x / z -12.4..12.4), y up from the plaza, the lobby front at +z (where the gold arrow is).
# Look only: tower()'s boxes stay the collision; the helipad picture and the logo banners stay the map's.
# run: blender52 -b --python tools/blender/jankburg/make_jb_hq.py -- [--qa] [--no-sheet] [--no-export]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
import jbkit as K
from jbkit import ARGV, Atlas, boxa, fill_uv, mesh, noise, concrete
import lib
from lib import mat, text_px, hexrgb, rod

rng = np.random.default_rng(152)
# the tiers as tower() builds them: (half width, y0, y1); the slab (half width + 0.4, 0.5 thick) on each
TIERS = [(12, 0.0, 31.0), (8, 31.5, 67.0), (5, 67.5, 107.0), (5, 107.5, 152.0)]
PPM = 4


# ------------------------------------------------------------ the atlas
def curtain(v, seed, lobby=False):
    h, w = v.shape[:2]; r = np.random.default_rng(seed)
    g = np.linspace(1.15, 0.85, h)[:, None, None]  # the sky's reflection, brighter up top
    v[:] = hexrgb(0x1d3c56) * g * (0.92 + 0.12 * noise(h, w, r, 8, 0.3)[..., None])
    fl = int(3.6 * PPM)
    for y in range(h - 1, -1, -fl):  # floors from the bottom: spandrel bands, then the lit offices
        v[max(0, y - 2):y + 1] = hexrgb(0x2c3448)
        for x0 in range(0, w, 6):
            if r.random() < 0.22:
                c = hexrgb([0xffe9b0, 0xffe9b0, 0xff7ad8, 0x8ff0ff][r.integers(0, 4)])
                v[max(0, y - fl + 2):max(0, y - 2), x0 + 1:x0 + 6] = v[max(0, y - fl + 2):max(0, y - 2), x0 + 1:x0 + 6] * 0.3 + c * 0.7
    v[:, ::6] = hexrgb(0x93a8bc)  # mullions
    if lobby:  # the double-height lobby: big panes, the revolving door's dark well, the doors either side
        L = int(6 * PPM)
        v[h - L:] = hexrgb(0x284660) * (0.95 + 0.1 * r.random((L, w, 1))); v[h - L:, ::12] = hexrgb(0x93a8bc); v[h - L] = hexrgb(0xb8c8d6)
        c = w // 2; v[h - 11:, c - 7:c + 7] = hexrgb(0x0e1420); v[h - 11:, c - 1:c + 1] = hexrgb(0xb8c8d6)
        v[h - 3:] = hexrgb(0x111018)


A = Atlas('jbhq_atlas', 512, 256, 0x1d3c56)
FACES = {}
x = 0
for i, (hw, y0, y1) in enumerate(TIERS):
    W, H = int(2 * hw * PPM), int((y1 - y0) * PPM)
    curtain(A.add(f't{i}', x, 0, W, H), 300 + i); FACES[i] = f't{i}'; x += W
    if i == 0: curtain(A.add('t0e', x, 0, W, H), 399, lobby=True); x += W
v = A.add('sign', x, 0, 40, 24); v[:] = hexrgb(0x16101e)
text_px(v, 'JANK', 8, 2, 1, 0xff4fd8); text_px(v, 'CORP', 8, 13, 1, 0xffe14d); v[0] = v[-1] = hexrgb(0xff4fd8)
v = A.add('slab', x, 32, 64, 8); concrete(v, 410, lifts=False, base=0xc8ccd6); v[:2] = hexrgb(0xe8eef4); v[-2:] = hexrgb(0x8a909c)
v = A.add('roof', x, 48, 64, 64); concrete(v, 411, lifts=False, base=0x6a6e7a)
v = A.add('house', x, 112, 32, 24); concrete(v, 412, lifts=False, base=0xb8bcc6); v[8:24, 12:20] = hexrgb(0x5a5f6e)
v = A.add('gold', x + 64, 32, 16, 16); v[:] = hexrgb(0xe8b83a) * (0.9 + 0.1 * rng.random((16, 16, 1)))
v = A.add('letters', 416, 0, 72, 12); v[:] = hexrgb(0x16101e); t = np.zeros_like(v); text_px(t, 'JANKCORP HQ', 4, 3, 1, 0xffffff)
m = t.sum(2) > 0; v[np.roll(np.roll(m, 1, 0), 1, 1) & ~m] = hexrgb(0x6a4a10); v[m] = hexrgb(0xffd24a)
for key, xx, c in (('chrome', 0, 0xd8e0e8), ('metal', 16, 0x5a5f6e), ('dark', 32, 0x24222c), ('white', 48, 0xeeeeee), ('conc', 64, 0x9ea2ae)):
    v = A.add(key, x + xx, 144, 16, 16); v[:] = hexrgb(c) * (0.94 + 0.06 * rng.random((16, 16, 1)))


def build():
    lib.reset(); lib._mats.clear()
    M = mat('jbhq', 0xffffff, rough=0.18, metal=0.1, clearcoat=0.8, tex=A.image())
    GLASS = mat('glass', 0x9fd8ff, rough=0.05, alpha=0.35)
    SIGN = mat('jbhq_sign', 0xffffff, rough=0.4, emit=0xffffff, strength=1.4, tex=A.image(), emit_tex=True)
    RED = mat('glow_red', 0xff3030, rough=0.3, emit=0xff3030, strength=2.0)
    P, Q = [], []
    for i, (hw, y0, y1) in enumerate(TIERS):
        top = y1
        if i == 3: top = 145.0  # (the crown's sign band sits over the last 6 m of glass)
        cells = {'-z': FACES[i], '+z': 't0e' if i == 0 else FACES[i], '-x': FACES[i], '+x': FACES[i]}
        P.append(boxa(f'hq_t{i}', (-hw, y0, -hw), (hw, top, hw), M, A, cells))
        Q.append(boxa(f'hq1_t{i}', (-hw, y0, -hw), (hw, top, hw), M, A, cells))
        sw = hw + 0.4  # the slab: concrete with a chrome edge
        P.append(boxa(f'hq_slab{i}', (-sw, y1, -sw), (sw, y1 + 0.5, sw), M, A, {'-z': 'slab', '+z': 'slab', '-x': 'slab', '+x': 'slab', '-y': 'conc', '+y': 'roof'}))
        Q.append(boxa(f'hq1_slab{i}', (-sw, y1, -sw), (sw, y1 + 0.5, sw), M, A, {'-z': 'slab', '+z': 'slab', '-x': 'slab', '+x': 'slab', '-y': 'conc', '+y': 'roof'}))
        # chrome fins: the corners, and every 3 m across the faces
        for sx in (-1, 1):
            for sz in (-1, 1):
                a, b = sorted((sx * (hw - 0.2), sx * (hw + 0.18))); c, d = sorted((sz * (hw - 0.2), sz * (hw + 0.18)))
                P.append(boxa('hq_cfin', (a, y0, c), (b, top, d), M, A, {'-z': 'chrome', '+z': 'chrome', '-x': 'chrome', '+x': 'chrome'}))
        n = int(2 * hw / 3)
        for k in range(1, n):
            u = -hw + k * 2 * hw / n
            for s in (-1, 1):
                fy0 = 6.2 if (i == 0) else y0  # (over the lobby)
                P.append(boxa('hq_fin', (u - 0.05, fy0, min(s * hw, s * (hw + 0.14))), (u + 0.05, top, max(s * hw, s * (hw + 0.14))), M, A, {('-z' if s < 0 else '+z'): 'chrome', '-x': 'chrome', '+x': 'chrome'}))
                P.append(boxa('hq_fin', (min(s * hw, s * (hw + 0.14)), fy0, u - 0.05), (max(s * hw, s * (hw + 0.14)), top, u + 0.05), M, A, {('-x' if s < 0 else '+x'): 'chrome', '-z': 'chrome', '+z': 'chrome'}))
        if i < 3:  # the terrace balustrade over this tier's slab: glass between a chrome base and top rail, posts
            rw, ry = hw + 0.4, y1 + 0.5
            for side in range(4):
                for lo_, hi_, gl in (((-rw + 0.251, ry, -rw), (rw, ry + 0.06, -rw + 0.25), False), ((-rw + 0.251, ry + 0.82, -rw), (rw, ry + 0.9, -rw + 0.25), False), ((-rw + 0.16, ry + 0.06, -rw + 0.1), (rw - 0.1, ry + 0.82, -rw + 0.15), True)):
                    o = boxa('hq_rail', lo_, hi_, GLASS if gl else M, A, {'all': 'chrome'})
                    o.data.transform(__import__('mathutils').Matrix.Rotation(side * math.pi / 2, 4, 'Z'))
                    P.append(o)
                for k in range(1, int(2 * rw / 2.0) + 1):  # (k = 0 is the next side's last post)
                    u = -rw + 0.06 + k * (2 * rw - 0.12) / int(2 * rw / 2.0)
                    o = boxa('hq_post', (u - 0.04, ry + 0.03, -rw + 0.08), (u + 0.04, ry + 0.85, -rw + 0.17), M, A, {'all': 'chrome'})
                    o.data.transform(__import__('mathutils').Matrix.Rotation(side * math.pi / 2, 4, 'Z'))
                    P.append(o)
    # the crown: the lit sign band, the parapet with a chrome cap, the stair house, a skylight, aircraft lights, the mast
    P.append(boxa('hq_sign', (-5.06, 145.0, -5.06), (5.06, 151.0, 5.06), SIGN, A, {'-z': 'sign', '+z': 'sign', '-x': 'sign', '+x': 'sign'}))
    P.append(boxa('hq_signback', (-5, 151.0, -5), (5, 152.0, 5), M, A, {'-z': 'dark', '+z': 'dark', '-x': 'dark', '+x': 'dark'}))
    Q.append(boxa('hq1_sign', (-5.06, 145.0, -5.06), (5.06, 152.0, 5.06), SIGN, A, {'-z': 'sign', '+z': 'sign', '-x': 'sign', '+x': 'sign'}))
    ring = [((-5, 152.5, -5), (5, 153.5, -4.6)), ((-5, 152.5, 4.6), (5, 153.5, 5)), ((-5, 152.5, -4.599), (-4.6, 153.5, 4.599)), ((4.6, 152.5, -4.599), (5, 153.5, 4.599))]
    for lo_, hi_ in ring:
        P.append(boxa('hq_parapet', lo_, hi_, M, A, {'-z': 'slab', '+z': 'slab', '-x': 'slab', '+x': 'slab'}))
        P.append(boxa('hq_pcap', (lo_[0] - 0.03, 153.5, lo_[2] - 0.03), (hi_[0] + 0.03, 153.58, hi_[2] + 0.03), M, A, {'all': 'chrome'}))
    P.append(boxa('hq_house', (-4, 152.5, -4), (1, 156.1, 0), M, A, {'-z': 'house', '+z': 'house', '-x': 'house', '+x': 'house'}))
    P.append(boxa('hq_house_cap', (-4.2, 156.1, -4.2), (1.2, 156.4, 0.2), M, A, {'all': 'metal'}))
    P.append(boxa('hq_skylight', (-2, 152.5, -2), (2, 153.1, 4), GLASS, A, {'all': 'chrome'}))
    P.append(boxa('hq_skyframe', (-2.04, 153.1, -2.04), (2.04, 153.16, 4.04), M, A, {'all': 'chrome'}))
    for sx in (-1, 1):
        for sz in (-1, 1):
            P.append(boxa('hq_aclight', (sx * 4.8 - 0.12, 153.58, sz * 4.8 - 0.12), (sx * 4.8 + 0.12, 153.8, sz * 4.8 + 0.12), RED, A, {'all': 'conc'}))
    P.append(fill_uv(rod((-1.5, 156.4, -2), (-1.5, 168.0, -2), 0.12, M, seg=6, name='hq_mast', r1=0.05), A, 'metal'))
    b = K.lathe_closed('hq_beacon', [(0.05, 167.9), (0.22, 167.9), (0.22, 168.3), (0.05, 168.45)], (-1.5, 0, -2), RED, seg=8); fill_uv(b, A, 'conc'); P.append(b)
    Q.append(fill_uv(rod((-1.5, 152.5, -2), (-1.5, 168.0, -2), 0.15, M, seg=4, name='hq1_mast'), A, 'metal'))
    # the lobby: gold JANKCORP HQ letters over the revolving door, a granite plinth all round
    P.append(boxa('hq_plinth', (-12.12, 0, -12.12), (12.12, 0.5, 12.12), M, A, {'-z': 'dark', '+z': 'dark', '-x': 'dark', '+x': 'dark', '+y': 'dark'}))
    P.append(boxa('hq_letters', (-4.5, 9.5, 12.0), (4.5, 10.7, 12.16), M, A, {'+z': 'letters', '-x': 'gold', '+x': 'gold', '+y': 'gold', '-y': 'gold'}))
    drum = K.lathe_closed('hq_door', [(1.3, 0.5), (1.45, 0.5), (1.45, 3.0), (1.3, 3.0)], (0, 0, 10.85), M, seg=16); fill_uv(drum, A, 'chrome'); P.append(drum)
    # the logo banners' frames (the banners hang at x +-12.1, y 30..70, z -4..4: the map draws them)
    for sx in (-1, 1):
        a, b = sorted((sx * 12.22, sx * 12.42))
        for zz in (-4.3, 4.1):
            P.append(boxa('hq_bframe', (a, 31.42, zz), (b, 70.6, zz + 0.2), M, A, {'all': 'metal'}))
        for yy in (29.6, 70.4):
            if yy > 31: P.append(boxa('hq_bbar', (a + 0.02, yy - 0.02, -4.28), (b - 0.02, yy + 0.18, 4.28), M, A, {'all': 'metal'}))
        for yy in (40.0, 55.0, 69.0):
            c, d = sorted((sx * 8.0, sx * 12.22))
            for zz in (-4.3, 4.1): P.append(boxa('hq_strut', (c, yy, zz), (d, yy + 0.18, zz + 0.2), M, A, {'all': 'metal'}))
    return P, Q, M


def main():
    P, Q, M = build()
    if '--qa-parts' in ARGV:  # which parts fight (names them), then stop
        from lib import apply_mods
        for o in P: apply_mods(o)
        sys.path.insert(0, os.path.join(lib.ROOT, '.claude', 'skills', 'blender-asset-qa', 'scripts'))
        import qa_check
        res = qa_check.run(objects=[o.name for o in P], profile='game', eps=0.0008, tol=0.002)
        for e in res.get('errors', []):
            if 'floating' not in str(e) and 'UV' not in str(e): print('QAP', str(e)[:200])
        return
    m0 = K.joined(P, 'jb_hq_lod0'); m1 = K.joined(Q, 'jb_hq_lod1')
    if '--qa' in ARGV: K.qa([m0], 'hq lod0'); K.qa([m1], 'hq lod1')
    lib.bake_ao([m0], dist=1.0); lib.bake_ao([m1], dist=1.0)
    root = lib.prop_finish('p_jb_hq', [m0], [m1], {'id': 'jb_hq', 'kind': 'prop', 'lod': 260, 'tint': False, 'box': [[-12.4, 0, -12.4], [12.4, 156.4, 12.4]]})
    lib.prop_stats(root)
    print('JF_EXTENT', K.extent([m0]))
    if '--no-export' not in ARGV: lib.export(root, 'p_jb_hq')
    if '--no-sheet' not in ARGV:
        e = next(c for c in root.children if c.name.startswith('lod1')); e.parent = None; m1.hide_render = True
        lib.sheet(root, 'p_jb_hq', extra_note='JANKCORP HQ', exposure=-0.2)


main()
