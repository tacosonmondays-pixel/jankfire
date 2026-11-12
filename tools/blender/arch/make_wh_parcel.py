# Site B on Warehouse S&D, the parcel shed (shared/map.js warehouseSD()): drawn over its own boxes, which stay what you
# bump into. A steel parcel shed in the site's cyan: profiled cladding on a concrete plinth, a cyan fascia and parapet,
# downpipes; roller shutters rolled up in every door (B main's head left clear for the game's cyan neon), a white liner
# and blue columns inside under roof beams and rooflights, high-bay lamps on chains, a cyan epoxy floor with yellow
# walkway lines. The sorting belt is a skirted powered conveyor: a black rubber belt between side guards, end drums,
# access hatches, an emergency pull-cord and stop buttons, a control box. The sorter is a teal cabinet with seams,
# louvres, chevron hazard paint, a control desk with a glowing screen, a stack light and an intake on its roof. The
# parcel cages are wire roll cages on castors. The parcels, pallets and crates, the B boards and the neon stay the
# game's. local frame: the shed's middle (44, 42).
# run: node tools/arch/dumpdeco.mjs warehouse_sd wh_parcel tools/blender/arch/boxes/wh_parcel.json
#      blender52 -b --python tools/blender/arch/make_wh_parcel.py
import os, sys, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST, bands

HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'pbclad': ('profile', '#78c8f0', {}), 'pbliner': ('profile', '#f0f4f4', {}), 'pbplinth': ('concrete', '#e6e2d8', {}), 'pbcyan': ('profile', '#4fd8ff', {}),
    'pbcope': ('metalplate', '#d8dce2', {}), 'pbsteel': ('trim', '#3a3d44', {}), 'pbcolumn': ('trim', '#2f6fd0', {}), 'pbbeam': ('trim', '#ffc21a', {}),
    'pbdeck': ('profile', '#e6eaee', {}), 'pbroof': ('profile', '#3a6ab8', {}), 'pbshutter': ('louvre', '#4fd8ff', {}), 'pbdrum': ('metalplate', '#8a919c', {}),
    'pbhazy': ('trim', '#ffd400', {}), 'pbhazk': ('trim', '#1c1c20', {}), 'pbfloor': ('lino', '#8ce0ec', {}), 'pbline': ('trim', '#ffe14d', {}),
    'pblamp': ('metalplate', '#c9ced6', {}), 'pbglow': ('stucco', '#fff3c8', {'glow': True}), 'pbsky': ('glass', '#d8f4ff', {'glow': True}),
    'pbbelt': ('tar', '#2a2a30', {}), 'pbbody': ('metalplate', '#b8c0c8', {}), 'pbbody2': ('metalplate', '#8e98a2', {}), 'pbred': ('trim', '#ff3030', {}),
    'pbteal': ('trim', '#1aa8a4', {}), 'pbteal2': ('trim', '#148a86', {}), 'pbvent': ('louvre', '#0e6c6a', {}), 'pbscreen': ('stucco', '#4fd8ff', {'glow': True, 'glowcol': '#4fd8ff'}),
    'pbgreen': ('stucco', '#39ff14', {'glow': True, 'glowcol': '#39ff14'}), 'pbamber': ('stucco', '#ffb030', {'glow': True}), 'pbmouth': ('tar', '#101014', {}),
    'pbcage': ('metalplate', '#c2c8d0', {}), 'pbbump': ('trim', '#4fd8ff', {}), 'pbwheel': ('tar', '#1e1e24', {}),
})
NOCAST.update({'pbcope', 'pbsteel', 'pbcolumn', 'pbbeam', 'pbshutter', 'pbdrum', 'pbhazy', 'pbhazk', 'pbline', 'pblamp', 'pbglow', 'pbsky', 'pbred', 'pbvent',
               'pbscreen', 'pbgreen', 'pbamber', 'pbmouth', 'pbcage', 'pbbump', 'pbwheel', 'pbdeck', 'pbliner', 'pbcyan', 'pbbody2', 'pbteal2'})
T, HX = 0.5, 14.0  # wall thickness, half size (square shed)


def build():
    d = json.load(open(os.path.join(HERE, 'boxes', 'wh_parcel.json')))
    deco = [b for b in d['boxes'] if b.get('deco')]
    d['boxes'] = [b for b in d['boxes'] if not b.get('deco') and b['mat'] != 'cardboard']  # (the parcels are props)
    K = Kit(d, seed=12)
    rng = random.Random(8)
    walls = K.take(lambda b: b['mat'] == 'containerb')
    roof = K.take(lambda b: b['mat'] == 'roofblue')[0]
    floor = K.take(lambda b: b['mat'] == 'floorcyan')[0]
    belt = K.take(lambda b: b['mat'] == 'metal')[0]; top = K.take(lambda b: b['mat'] == 'tire')[0]
    sorter = K.take(lambda b: b['mat'] == 'toyteal')[0]; K.take(lambda b: b['mat'] == 'hazard')
    cages = K.take(lambda b: b['mat'] == 'grid')
    H = roof['min'][1]
    K.inside.append(((-HX + T / 2, 0, -HX + T / 2), (HX - T / 2, H, HX - T / 2)))
    planes = {}
    for b in walls:
        if b['max'][2] - b['min'][2] <= T + 0.01 and abs(abs(b['min'][2] + b['max'][2]) / 2 - HX) < 0.01: k = ('x', HX if b['min'][2] > 0 else -HX, T, 0)
        else: k = ('z', HX if b['min'][0] > 0 else -HX, T, 0)
        planes.setdefault(k, []).append(b)
    assert len(planes) == 4

    def F(axis, c, s, a0, a1, y0, y1, d0, d1, mats, cull=True):
        f = c + s * T / 2
        o0, o1 = sorted((f - c + s * d0, f - c + s * d1))
        K.wbox(axis, c, a0, a1, y0, y1, o0, o1, mats if isinstance(mats, dict) else {'all': mats}, cull=cull)
    box = lambda mn, mx, m, cull=False: K.box(mn, mx, m if isinstance(m, dict) else {'all': m}, cull=cull)

    # ---- the walls: cyan cladding out, white liner in, plinth, fascia round the top, a dado inside
    doors = []
    for (axis, c, t, _), bs in planes.items():
        so = 1 if c > 0 else -1
        ops = K.wall_plane(axis, c, t, bs, 'pbclad', 'pbliner', trim='pbsteel', sub=2.0, frames=False, sill=False, shards=False, doors=False)
        doors += [(axis, c, so, a0, a1, y1) for (a0, a1, y0, y1, isdoor) in ops if isdoor]
        oo = (T / 2, T / 2 + 0.06) if so > 0 else (-T / 2 - 0.06, -T / 2)
        oi = (-T / 2 - 0.04, -T / 2) if so > 0 else (T / 2, T / 2 + 0.04)
        bands(K, axis, c, bs, [(0.0, 1.2, 'pbplinth')], *oo)
        bands(K, axis, c, bs, [(1.2, 1.26, 'pbcope')], *(((T / 2, T / 2 + 0.1) if so > 0 else (-T / 2 - 0.1, -T / 2))))
        bands(K, axis, c, bs, [(0.0, 1.0, 'pbplinth'), (1.0, 1.14, 'pbhazy')], *oi)
        ext = 0.3 if axis == 'x' else 0.25
        F(axis, c, so, -HX - ext, HX + ext, H - 0.9, H + 1.0, 0, 0.05, {'all': 'pbcyan', 'top': 'pbcope'}, cull=False)
    ex = HX + T / 2
    for sx in (-1, 1):
        for sz in (-1, 1):
            for (y0, y1, p, m) in ((0.0, 1.2, 0.06, 'pbplinth'), (1.2, 1.26, 0.1, 'pbcope')):
                xa, xb = sorted((sx * (ex - 0.005), sx * (ex + p))); za, zb = sorted((sz * (ex - T - 0.005), sz * (ex + p)))
                box((xa, y0, za), (xb, y1, zb), m)
            xa, xb = sorted((sx * (ex - 0.6), sx * (ex + 0.05))); za, zb = sorted((sz * (ex - 0.6), sz * (ex + 0.05)))
            box((xa, 1.26, za), (xb, H - 0.9, zb), 'pbcyan')
    # parapet + coping, the roof with rooflights and vents, the deck under it
    y0, y1 = H + 0.5, H + 1.0
    for (mn, mx, out) in (((-ex, y0, -ex), (ex, y1, -ex + 0.3), 'nz'), ((-ex, y0, ex - 0.3), (ex, y1, ex), 'pz'),
                          ((-ex, y0, -ex + 0.3), (-ex + 0.3, y1, ex - 0.3), 'nx'), ((ex - 0.3, y0, -ex + 0.3), (ex, y1, ex - 0.3), 'px')):
        K.box(mn, mx, {'all': 'pbclad', out: None, 'top': None}, cull=False)
    for (mn, mx) in (((-ex - 0.09, y1, -ex - 0.09), (ex + 0.09, y1 + 0.07, -ex + 0.34)), ((-ex - 0.09, y1, ex - 0.34), (ex + 0.09, y1 + 0.07, ex + 0.09)),
                     ((-ex - 0.09, y1, -ex + 0.34), (-ex + 0.34, y1 + 0.07, ex - 0.34)), ((ex - 0.34, y1, -ex + 0.34), (ex + 0.09, y1 + 0.07, ex - 0.34))):
        box(mn, mx, 'pbcope')
    K.plain(roof, {'top': 'pbroof', 'side': None, 'bottom': 'pbdeck'}, sub=3.0)
    RT = roof['max'][1]
    BEAMS = (-7.0, 0.0, 7.0)
    for z in (-10.5, -3.5, 3.5, 10.5):
        x = -11.0
        while x + 2.6 <= 11.0:
            box((x, RT, z - 0.55), (x + 2.6, RT + 0.12, z + 0.55), {'top': 'pbsky', 'side': 'pbcope'})
            K.quad([(x, H - 0.03, z - 0.55), (x + 2.6, H - 0.03, z - 0.55), (x + 2.6, H - 0.03, z + 0.55), (x, H - 0.03, z + 0.55)], 'pbliner')
            x += 3.4
    for (x, z) in ((-6.0, 0.0), (6.0, 7.0)):
        FL.tube(K, (x, RT, z), (x, RT + 0.45, z), 0.2, 0.2, 'pblamp', n=10, caps=(False, False))
        FL.tube(K, (x, RT + 0.45, z), (x, RT + 0.9, z), 0.34, 0.34, 'pbvent', n=12, caps=(False, False))
        FL.tube(K, (x, RT + 0.9, z), (x, RT + 1.12, z), 0.34, 0.05, 'pbcope', n=12, caps=(False, True))
        FL.tube(K, (x, RT + 0.45, z), (x, RT + 0.46, z), 0.35, 0.35, 'pbcope', n=12, caps=(True, False))

    # ---- the doors: roller shutters rolled up (B main's head stays clear for the game's neon)
    for (axis, c, so, a0, a1, y1) in doors:
        si = -so
        neon = axis == 'z' and c < 0
        dy = 0.35 if neon else 0.0
        F(axis, c, si, a0 - 0.25, a1 + 0.25, y1 + dy, y1 + dy + 0.7, 0, 0.55, 'pbdrum')
        for (p, q) in ((a0 - 0.14, a0), (a1, a1 + 0.14)): F(axis, c, si, p, q, 0, y1 + dy, 0, 0.14, 'pbsteel')
        F(axis, c, si, a0, a1, y1 - 0.38, y1, 0.05, 0.09, 'pbshutter', cull=False)
        F(axis, c, si, a0, a1, y1 - 0.44, y1 - 0.38, 0.04, 0.1, 'pbhazk', cull=False)
        for (p, q) in ((a0 - 0.16, a0), (a1, a1 + 0.16)):
            for k in range(7): F(axis, c, so, p, q, k * 0.19, k * 0.19 + 0.19, 0, 0.09, 'pbhazy' if k % 2 == 0 else 'pbhazk')
            F(axis, c, so, p, q, 1.33, y1, 0, 0.09, 'pbsteel')
        F(axis, c, so, a0 - 0.16, a1 + 0.16, y1, y1 + 0.08, 0, 0.09, 'pbsteel')
        if not neon:
            n = max(2, round((a1 - a0 + 0.32) / 0.6)); w = (a1 - a0 + 0.32) / n
            for k in range(n): F(axis, c, so, a0 - 0.16 + k * w, a0 - 0.16 + (k + 1) * w, y1 + 0.08, y1 + 0.32, 0, 0.07, 'pbhazy' if k % 2 == 0 else 'pbhazk')
    # downpipes in the corners of each face, pink-free here: cyan
    for (axis, c, t, _), bs in planes.items():
        so = 1 if c > 0 else -1
        for a in (-HX + 1.1, HX - 1.1):
            if any(o[0] == axis and o[1] == c and o[3] - 1.2 < a < o[4] + 1.2 for o in doors): continue
            F(axis, c, so, a - 0.22, a + 0.22, H + 0.45, H + 0.9, 0.05, 0.34, 'pbcyan', cull=False)
            f = c + so * T / 2
            pt = (lambda a, y, o: (a, y, f + so * o)) if axis == 'x' else (lambda a, y, o: (f + so * o, y, a))
            FL.bar(K, pt(a, H + 0.46, 0.2), pt(a, 0.32, 0.2), 0.13, 'pbbump')
            FL.bar(K, pt(a, 0.38, 0.2), pt(a, 0.1, 0.42), 0.115, 'pbbump')

    # ---- inside: columns up the walls, yellow roof beams across, high-bay lamps, the floor
    for z in BEAMS:
        box((-HX + T / 2, H - 0.5, z - 0.15), (HX - T / 2, H, z + 0.15), {'all': 'pbbeam', 'top': None})
        for c in (-HX, HX):
            si = 1 if c < 0 else -1
            F('z', c, si, z - 0.04, z + 0.04, 0, H - 0.5, 0, 0.24, 'pbcolumn')
            F('z', c, si, z - 0.18, z + 0.18, 0, H - 0.5, 0.24, 0.29, 'pbcolumn')
    for b in deco:
        if b['mat'] != 'lamp': continue
        x, z = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2
        ly = b['min'][1]
        FL.bar(K, (x, H - 0.45, z), (x, ly + 0.38, z), 0.035, 'pbsteel')
        FL.tube(K, (x, ly + 0.42, z), (x, ly + 0.2, z), 0.18, 0.21, 'pblamp', n=10, caps=(True, False))
        FL.tube(K, (x, ly + 0.2, z), (x, ly + 0.02, z), 0.24, 0.6, 'pblamp', n=12, caps=(False, False), inside=True)
        FL.tube(K, (x, ly + 0.035, z), (x, ly + 0.03, z), 0.57, 0.57, 'pbglow', n=12, caps=(False, True))
    K.plain(floor, {'top': 'pbfloor', 'side': None}, sub=3.0)  # (its edges are against the walls)
    fy = floor['max'][1] + 0.004
    for (x0, z0, x1, z1) in ((-13.6, 1.6, 13.6, 1.75), (-13.6, 4.45, 13.6, 4.6), (-12.5, -4.0, -12.35, 4.0)):  # walkway lines
        K.quad([(x0, fy, z1), (x1, fy, z1), (x1, fy, z0), (x0, fy, z0)], 'pbline')

    # ---- the sorting belt: a skirted powered conveyor
    (bx0, _, bz0), (bx1, by1, bz1) = belt['min'], belt['max']
    box((bx0, 0.0, bz0), (bx1, by1, bz1), {'all': 'pbbody', 'top': None, 'bottom': None})
    box((bx0 - 0.004, 0.0, bz0 - 0.004), (bx1 + 0.004, 0.12, bz1 + 0.004), {'all': 'pbbody2', 'top': None, 'bottom': None})  # kick plate
    k = 0; x = bx0 + 0.8
    while x < bx1 - 0.8:  # access hatches with two screws, both sides
        for (z, s) in ((bz0, -1), (bz1, 1)):
            box((x - 0.35, 0.3, min(z, z + s * 0.012)), (x + 0.35, 0.8, max(z, z + s * 0.012)), 'pbbody2')
        x += 2.0
    (tx0, ty0, tz0), (tx1, ty1, tz1) = top['min'], top['max']
    box((tx0, ty0, tz0), (tx1, ty1, tz1), {'all': 'pbbelt', 'bottom': None})
    for (z0, z1) in ((bz0, tz0), (tz1, bz1)): box((bx0, by1, z0), (bx1, by1 + 0.18, z1), {'all': 'pbbody', 'bottom': None})  # side guards
    for xx in (bx0, bx1):  # end drums
        FL.tube(K, (xx, ty1 - 0.12, tz0 + 0.02), (xx, ty1 - 0.12, tz1 - 0.02), 0.12, 0.12, 'pbdrum', n=10)
    for xx in [bx0 + 0.6 + i * (bx1 - bx0 - 1.2) / 4 for i in range(5)]:  # the pull-cord posts on the near side, a red stop button on each
        FL.bar(K, (xx, by1 + 0.18, bz1 + 0.02), (xx, by1 + 0.42, bz1 + 0.02), 0.03, 'pbsteel')
        box((xx - 0.06, by1 + 0.3, bz1 + 0.035), (xx + 0.06, by1 + 0.42, bz1 + 0.1), 'pbhazy')
        FL.tube(K, (xx, by1 + 0.36, bz1 + 0.1), (xx, by1 + 0.36, bz1 + 0.13), 0.045, 0.045, 'pbred', n=8)
    FL.bar(K, (bx0 + 0.6, by1 + 0.4, bz1 + 0.02), (bx1 - 0.6, by1 + 0.4, bz1 + 0.02), 0.012, 'pbhazy')
    box((bx1 - 0.6, by1 + 0.18, bz0 - 0.32), (bx1 - 0.1, by1 + 0.75, bz0 - 0.02), {'all': 'pbbody2', 'nz': 'pbteal'})  # the control box
    for i, m in enumerate(('pbgreen', 'pbred', 'pbamber')):
        FL.tube(K, (bx1 - 0.48 + i * 0.14, by1 + 0.5, bz0 - 0.32), (bx1 - 0.48 + i * 0.14, by1 + 0.5, bz0 - 0.35), 0.04, 0.04, m, n=8)

    # ---- the sorter: a teal cabinet, chevron hazard band, a control desk with a screen, a stack light, an intake
    (sx0, _, sz0), (sx1, sy1, sz1) = sorter['min'], sorter['max']
    box((sx0, 0, sz0), (sx1, sy1, sz1), {'all': 'pbteal', 'bottom': None, 'top': 'pbbody2'})
    for i in range(1, 4):  # panel seams
        a = sx0 + i * (sx1 - sx0) / 4
        for (z, s) in ((sz0, -1), (sz1, 1)): box((a - 0.02, 0.1, min(z, z + s * 0.015)), (a + 0.02, sy1 - 0.1, max(z, z + s * 0.015)), 'pbteal2')
        a = sz0 + i * (sz1 - sz0) / 4
        for (x, s) in ((sx0, -1), (sx1, 1)): box((min(x, x + s * 0.015), 0.1, a - 0.02), (max(x, x + s * 0.015), sy1 - 0.1, a + 0.02), 'pbteal2')
    n = 10
    for i in range(n):  # the hazard band, wrapped round in blocks
        for (z, s) in ((sz0, -1), (sz1, 1)):
            box((sx0 + i * (sx1 - sx0) / n, 1.1, min(z, z + s * 0.1)), (sx0 + (i + 1) * (sx1 - sx0) / n, 1.5, max(z, z + s * 0.1)), 'pbhazy' if i % 2 == 0 else 'pbhazk')
            box((min(sx0 if s < 0 else sx1, (sx0 if s < 0 else sx1) + s * 0.1), 1.1, sz0 + i * (sz1 - sz0) / n), (max(sx0 if s < 0 else sx1, (sx0 if s < 0 else sx1) + s * 0.1), 1.5, sz0 + (i + 1) * (sz1 - sz0) / n), 'pbhazy' if i % 2 == 1 else 'pbhazk')
    for (x, s) in ((sx0, -1),):  # louvres on the far side
        for a in (sz0 + 0.8, sz1 - 0.8):
            K.quad([(x - 0.004, 1.8, a + 0.5), (x - 0.004, 1.8, a - 0.5), (x - 0.004, 2.3, a - 0.5), (x - 0.004, 2.3, a + 0.5)], 'pbvent')
    # the desk on the +x face: a sloped top with a screen and buttons (it hangs off the box at waist height)
    dz0, dz1 = (sz0 + sz1) / 2 - 0.75, (sz0 + sz1) / 2 + 0.75
    K.prism([(sx1 + 0.002, 0.75, 0), (sx1 + 0.35, 0.75, 0), (sx1 + 0.35, 0.9, 0), (sx1 + 0.002, 1.08, 0)], 2, dz0, dz1, 'pbbody2')  # (under the hazard band)
    dy = lambda x: 1.08 - 0.18 / 0.348 * (x - sx1 - 0.002)  # the desk's sloped top
    K.quad([(sx1 + 0.08, dy(sx1 + 0.08) + 0.006, dz0 + 0.15), (sx1 + 0.08, dy(sx1 + 0.08) + 0.006, dz0 + 0.75), (sx1 + 0.3, dy(sx1 + 0.3) + 0.006, dz0 + 0.75), (sx1 + 0.3, dy(sx1 + 0.3) + 0.006, dz0 + 0.15)], 'pbscreen')
    for i, m in enumerate(('pbgreen', 'pbred', 'pbamber', 'pbgreen')):
        z = dz0 + 0.95 + i * 0.16
        FL.tube(K, (sx1 + 0.2, dy(sx1 + 0.2) - 0.01, z), (sx1 + 0.2 + 0.017, dy(sx1 + 0.2) + 0.026, z), 0.04, 0.04, m, n=8)
    for i, m in enumerate(('pbgreen', 'pbamber', 'pbred')):  # the stack light
        FL.tube(K, (sx1 - 0.25, sy1 + 0.04 + i * 0.13, sz1 - 0.25), (sx1 - 0.25, sy1 + 0.16 + i * 0.13, sz1 - 0.25), 0.08, 0.08, m, n=10, caps=(False, i == 2))
    FL.tube(K, (sx1 - 0.25, sy1, sz1 - 0.25), (sx1 - 0.25, sy1 + 0.04, sz1 - 0.25), 0.1, 0.1, 'pbsteel', n=10, caps=(False, False))
    box((sx0 + 0.9, sy1, sz0 + 0.9), (sx1 - 1.1, sy1 + 0.1, sz1 - 0.9), {'all': 'pbsteel', 'top': None, 'bottom': None})  # the intake rim
    K.quad([(sx0 + 0.899, sy1 + 0.02, sz1 - 0.899), (sx1 - 1.099, sy1 + 0.02, sz1 - 0.899), (sx1 - 1.099, sy1 + 0.02, sz0 + 0.899), (sx0 + 0.899, sy1 + 0.02, sz0 + 0.899)], 'pbmouth')
    K.decal_on('x', sz1, 1, 0.0035, sx0 + (sx1 - sx0) * 0.625, 2.05, 'sign_warn', w=0.6, h=0.6)

    # ---- the parcel cages: wire roll cages on castors
    for b in cages:
        (x0, _, z0), (x1, y1, z1) = b['min'], b['max']
        box((x0, 0.12, z0), (x1, 0.2, z1), {'all': 'pbcage', 'bottom': 'pbcage'})  # the base frame
        for (x, z) in ((x0 + 0.12, z0 + 0.12), (x1 - 0.12, z0 + 0.12), (x0 + 0.12, z1 - 0.12), (x1 - 0.12, z1 - 0.12)):
            FL.tube(K, (x - 0.04, 0.06, z), (x + 0.04, 0.06, z), 0.06, 0.06, 'pbwheel', n=8)
            box((x - 0.05, 0.1, z - 0.05), (x + 0.05, 0.12, z + 0.05), 'pbsteel')
        for (x, z) in ((x0 + 0.03, z0 + 0.03), (x1 - 0.03, z0 + 0.03), (x0 + 0.03, z1 - 0.03), (x1 - 0.03, z1 - 0.03)):
            FL.bar(K, (x, 0.19, z), (x, y1, z), 0.05, 'pbcage')
        for y in (0.9, y1 - 0.03):
            for (p, q) in (((x0, z0 + 0.03), (x1, z0 + 0.03)), ((x0, z1 - 0.03), (x1, z1 - 0.03)), ((x0 + 0.03, z0), (x0 + 0.03, z1)), ((x1 - 0.03, z0), (x1 - 0.03, z1))):
                FL.bar(K, (p[0], y, p[1]), (q[0], y, q[1]), (0.04 if y < 1 else 0.045) + (0.006 if p[0] == q[0] else 0), 'pbcage')  # (the two directions a hair different: no shared faces at the corners)
        for t in range(1, 7):  # the mesh: verticals on all four sides
            for (p, q) in (((x0 + t * (x1 - x0) / 7, z0 + 0.03), None), ((x0 + t * (x1 - x0) / 7, z1 - 0.03), None), ((x0 + 0.03, z0 + t * (z1 - z0) / 7), None), ((x1 - 0.03, z0 + t * (z1 - z0) / 7), None)):
                FL.bar(K, (p[0], 0.19, p[1]), (p[0], y1 - 0.05, p[1]), 0.016, 'pbcage')
        box((x0 - 0.02, 0.2, z0 - 0.02), (x1 + 0.02, 0.3, z1 + 0.02), {'all': 'pbbump', 'top': None, 'bottom': None})  # the bumper
    K.finish(os.path.join(OUTDIR, 'wh_parcel.glb'))


build()
