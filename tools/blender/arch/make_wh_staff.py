# The staff block on Warehouse S&D (shared/map.js warehouseSD(), the defenders spawn behind it): drawn over its own
# boxes (one solid block and its roof slab), which stay what you bump into. A two-storey office block like the ones
# bolted onto real depots: hot pink rainscreen panels in two tones on a dark backing with open joints, a pale band
# between the floors, a brick-grey plinth; aluminium windows with a mullion and a transom, some lit behind their blinds
# (the night shift), sills under them; the staff entrance on the spawn side: glazed doors and side lights under a flat
# canopy on tie rods with a downlight, the company name over it, bulkhead lamps along the wall; a fire door at the north
# end; pink downpipes; on the roof a parapet with a coping, the lift overrun, two AC units, a dish and a bent aerial.
# The NOW HIRING picture on the courtyard side stays the game's. local frame: the block's centre (60.5, 0).
# run: node tools/arch/dumpdeco.mjs warehouse_sd wh_staff tools/blender/arch/boxes/wh_staff.json
#      blender52 -b --python tools/blender/arch/make_wh_staff.py
import os, sys, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST

HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'stpanel': ('trim', '#e8389c', {}), 'stpanel2': ('trim', '#ff5cb6', {}), 'stback': ('trim', '#26202c', {}),
    'stband': ('stucco', '#f4f2ec', {}), 'stplinth': ('concrete', '#8c8a92', {}), 'stframe': ('metalplate', '#3a3e46', {}),
    'stglass': ('glass', '#ffffff', {}), 'stlit': ('louvre', '#ffe2a0', {'glow': True}), 'stsill': ('trim', '#ecebe6', {}),
    'stcope': ('metalplate', '#c8ccd2', {}), 'stroof': ('tar', '#ffffff', {}), 'stglow': ('stucco', '#fff3c8', {'glow': True}),
    'stpipe': ('trim', '#ff4fd8', {}), 'stcanopy': ('metalplate', '#d6dade', {}), 'stdoor': ('trim', '#d83a3a', {}),
    'sthvac': ('metalplate', '#e4e2da', {}), 'stvent': ('louvre', '#b8bcc2', {}), 'stfan': ('tar', '#1e1e24', {}), 'stexit': ('stucco', '#39ff14', {'glow': True}),
})
NOCAST.update({'stframe', 'stglass', 'stlit', 'stsill', 'stcope', 'stglow', 'stpipe', 'stvent', 'stfan', 'stexit', 'stdoor'})
W, L, H = 2.5, 18.0, 7.2  # half depth (x), half length (z), wall height
WINS = [(c, y0, y0 + 1.8) for c in range(-14, 15, 4) for y0 in (1.2, 4.4)]  # (the game's glass boxes: 2 m wide)


def build():
    d = json.load(open(os.path.join(HERE, 'boxes', 'wh_staff.json')))
    d['boxes'] = [b for b in d['boxes'] if not b.get('deco')]
    K = Kit(d, seed=3)
    rng = random.Random(9)
    block = next(b for b in K.boxes if b['mat'] == 'magenta')
    roof = next(b for b in K.boxes if b['mat'] == 'roofg')
    K.plain(block, {'all': 'stback'}, sub=2.0)
    K.plain(roof, {'top': 'stroof', 'side': 'stcope', 'bottom': 'stcope'}, sub=3.0)

    def X(s, o): return s * (W + o)  # a point o out from the long face on side s (+1 = east, the spawn)

    def fbox(s, z0, z1, y0, y1, o0, o1, m, cull=False):
        """a box on a long face, o0..o1 out from it"""
        xa, xb = sorted((X(s, o0), X(s, o1)))
        m = dict(m) if isinstance(m, dict) else {'all': m}
        m.setdefault('nx' if s > 0 else 'px', None)  # (its back, against the wall: never seen)
        K.box((xa, y0, z0), (xb, y1, z1), m, cull=cull)

    def ebox(t, x0, x1, y0, y1, o0, o1, m):
        """a box on an end face (t = +1: the south end, z = +L)"""
        za, zb = sorted((t * (L + o0), t * (L + o1)))
        m = dict(m) if isinstance(m, dict) else {'all': m}
        m.setdefault('nz' if t > 0 else 'pz', None)
        K.box((x0, y0, za), (x1, y1, zb), m, cull=False)

    def panels(s, z0, z1, y0, y1, maxw=1.2, maxh=1.35):
        """rainscreen panels over a rectangle of a long face: open 2 cm joints, two tones"""
        nz, ny = max(1, math.ceil((z1 - z0) / maxw - 1e-6)), max(1, math.ceil((y1 - y0) / maxh - 1e-6))
        w, h = (z1 - z0) / nz, (y1 - y0) / ny
        for i in range(nz):
            for j in range(ny):
                fbox(s, z0 + i * w + 0.01, z0 + (i + 1) * w - 0.01, y0 + j * h + 0.01, y0 + (j + 1) * h - 0.01, 0, 0.04, 'stpanel2' if rng.random() < 0.3 else 'stpanel')

    # ---- the long faces: plinth, panels round the windows, the band between the floors
    door = (-3.0, 3.0)  # the staff entrance (east, ground floor)
    for s in (-1, 1):
        for (za, zb) in (((-L, door[0] - 0.06), (door[1] + 0.06, L)) if s > 0 else ((-L, L),)): fbox(s, za, zb, 0, 0.45, 0, 0.06, 'stplinth')
        fbox(s, -L, L, 3.0, 4.4, 0, 0.035 if s < 0 else 0.05, 'stband')  # (west: under the NOW HIRING board, 5 cm out)
        cuts = sorted(set([-L, L] + [c + e for c in range(-14, 15, 4) for e in (-1, 1)]))
        for fl, (ya, yb) in enumerate(((0.45, 3.0), (4.4, 6.2))):
            for k in range(len(cuts) - 1):
                z0, z1 = cuts[k], cuts[k + 1]
                mid = (z0 + z1) / 2
                win = any(abs(mid - c) < 1 for c in range(-14, 15, 4))
                if s > 0 and fl == 0 and door[0] - 0.01 < mid < door[1] + 0.01: continue
                if win:
                    if fl == 0: panels(s, z0, z1, ya, 1.2)  # under the window
                    continue
                panels(s, z0, z1, ya, yb)
        panels(s, -L, L, 6.2, H, maxw=1.2, maxh=1.0)
        # windows: glass on the face, an aluminium frame round it, a mullion, a transom, a sill
        for (c, y0, y1) in WINS:
            if s > 0 and y0 < 2 and door[0] < c < door[1]: continue
            lit = rng.random() < 0.45
            fbox(s, c - 1, c + 1, y0, y1, 0, 0.006, {'all': 'stframe', 'px' if s > 0 else 'nx': 'stlit' if lit else 'stglass'})
            for (za, zb, ya, yb) in ((c - 1, c - 0.93, y0, y1), (c + 0.93, c + 1, y0, y1), (c - 0.93, c + 0.93, y0, y0 + 0.07), (c - 0.93, c + 0.93, y1 - 0.07, y1)):
                fbox(s, za, zb, ya, yb, 0.006, 0.09, 'stframe')
            fbox(s, c - 0.025, c + 0.025, y0 + 0.07, y1 - 0.07, 0.006, 0.07, 'stframe')
            ty = y0 + 1.8 * 0.68
            fbox(s, c - 0.93, c - 0.025, ty - 0.025, ty + 0.025, 0.006, 0.065, 'stframe'); fbox(s, c + 0.025, c + 0.93, ty - 0.025, ty + 0.025, 0.006, 0.065, 'stframe')
            if y0 < 2: fbox(s, c - 1.08, c + 1.08, y0 - 0.06, y0, 0, 0.12, 'stsill')
        # downpipes off little hoppers under the roof's edge, near each end
        for z in (-L + 0.6, L - 0.6):
            fbox(s, z - 0.17, z + 0.17, 6.75, 7.15, 0.04, 0.3, 'stpipe')
            FL.bar(K, (X(s, 0.16), 6.76, z), (X(s, 0.16), 0.3, z), 0.12, 'stpipe')
            FL.bar(K, (X(s, 0.16), 0.36, z), (X(s, 0.36), 0.08, z), 0.105, 'stpipe')
            for y in (1.6, 3.7, 5.6): fbox(s, z - 0.09, z + 0.09, y, y + 0.05, 0.04, 0.23, 'stframe')

    # ---- the staff entrance (east): glazed doors and side lights, a canopy on tie rods, the name over it, lamps
    s = 1
    fbox(s, door[0], door[1], 0.0, 3.0, 0, 0.006, {'all': 'stframe', 'px': 'stglass'})
    for z in (door[0], -1.0, 0.0, 1.0, door[1]): fbox(s, z - 0.05, z + 0.05, 0, 2.95, 0.006, 0.1, 'stframe')
    fbox(s, door[0], door[1], 2.45, 2.55, 0.006, 0.09, 'stframe'); fbox(s, door[0] - 0.06, door[1] + 0.06, 2.92, 3.0, 0.006, 0.11, 'stframe')
    for z in (-0.5, 0.5):  # push bars
        FL.bar(K, (X(s, 0.12), 1.05, z - 0.32), (X(s, 0.12), 1.05, z + 0.32), 0.04, 'stcope')
    fbox(s, door[0] - 0.4, door[1] + 0.4, 3.0, 3.16, 0.05, 1.6, {'all': 'stcanopy', 'nx': None})
    fbox(s, door[0] - 0.42, door[1] + 0.42, 2.95, 3.25, 1.6, 1.66, 'stpipe')
    for z in (-0.9, 0.9): fbox(s, z - 0.35, z + 0.35, 2.99, 3.0, 0.5, 1.1, 'stglow')  # its downlights
    for z in (door[0] - 0.2, door[1] + 0.2): FL.bar(K, (X(s, 1.5), 3.16, z), (X(s, 0.05), 4.25, z), 0.035, 'stframe')
    K.decal_on('z', 0, 1, W + 0.056, 0, 3.7, 'ad_jankcorp', w=2.2, h=1.1)
    K.decal_on('z', 0, 1, W + 0.046, -4.0, 1.6, 'sign_loiter', w=0.55, h=0.55)
    for z in (-12, -8, 8, 12):  # bulkhead lamps between the ground floor windows
        fbox(s, z - 0.14, z + 0.14, 2.45, 2.71, 0.04, 0.14, 'stframe')
        fbox(s, z - 0.1, z + 0.1, 2.49, 2.67, 0.14, 0.16, 'stglow')

    # ---- the ends: panels, corner trims, the fire door (north) with its exit sign
    for t in (-1, 1):
        for (xa, xb) in (((-W, -0.72), (0.72, W)) if t < 0 else ((-W, W),)): ebox(t, xa, xb, 0, 0.45, 0, 0.06, 'stplinth')
        ebox(t, -W, W, 3.0, 4.4, 0, 0.05, 'stband')
        nx = 4
        for i in range(nx):
            for (ya, yb, ny) in ((0.45, 3.0, 2), (4.4, H, 2)):
                h = (yb - ya) / ny
                for j in range(ny):
                    xa, xb = -W + i * (2 * W / nx) + 0.01, -W + (i + 1) * (2 * W / nx) - 0.01
                    if t < 0 and ya < 1 and xa < 0.72 and xb > -0.72: continue  # (the fire door: filled in round it below)
                    ebox(t, xa, xb, ya + j * h + 0.01, ya + (j + 1) * h - 0.01, 0, 0.04, 'stpanel2' if rng.random() < 0.3 else 'stpanel')
        for sx in (-1, 1):  # corner trims over the panel edges
            xa, xb = sorted((sx * (W - 0.1), sx * (W + 0.08)))
            za, zb = sorted((t * (L - 0.1), t * (L + 0.08)))
            K.box((xa, 0.0, za), (xb, H, zb), {'all': 'stcope'}, cull=False)
    for (xa, xb, ya, yb) in ((-1.24, -0.73, 0.46, 1.71), (-1.24, -0.73, 1.73, 2.99), (0.73, 1.24, 0.46, 1.71), (0.73, 1.24, 1.73, 2.99), (-0.71, 0.71, 2.37, 2.99)):
        ebox(-1, xa, xb, ya, yb, 0, 0.04, 'stpanel')
    ebox(-1, -0.62, 0.62, 0.0, 2.25, 0, 0.05, 'stdoor')
    for (xa, xb, ya, yb) in ((-0.72, -0.62, 0, 2.35), (0.62, 0.72, 0, 2.35), (-0.62, 0.62, 2.25, 2.35)): ebox(-1, xa, xb, ya, yb, 0, 0.08, 'stframe')
    FL.bar(K, (-0.45, 1.05, -(L + 0.09)), (0.45, 1.05, -(L + 0.09)), 0.04, 'stcope')
    ebox(-1, -0.3, 0.3, 2.45, 2.7, 0, 0.08, {'all': 'stframe', 'nz': 'stexit'})
    K.decal_on('x', -L, -1, 0.042, 0, 5.6, 'ad_jankcorp', w=3.2, h=1.6)

    # ---- the roof: a parapet with a coping, the lift overrun, AC units, a dish, an aerial
    RT, rx, rz = roof['max'][1], roof['max'][0], roof['max'][2]
    for (mn, mx, out) in (((-rx, RT, -rz), (rx, RT + 0.45, -rz + 0.2), 'nz'), ((-rx, RT, rz - 0.2), (rx, RT + 0.45, rz), 'pz'),
                          ((-rx, RT, -rz + 0.2), (-rx + 0.2, RT + 0.45, rz - 0.2), 'nx'), ((rx - 0.2, RT, -rz + 0.2), (rx, RT + 0.45, rz - 0.2), 'px')):
        K.box(mn, mx, {'all': 'stband', out: 'stcope', 'top': None}, cull=False)
    for (mn, mx) in (((-rx - 0.04, RT + 0.45, -rz - 0.04), (rx + 0.04, RT + 0.5, -rz + 0.24)), ((-rx - 0.04, RT + 0.45, rz - 0.24), (rx + 0.04, RT + 0.5, rz + 0.04)),
                     ((-rx - 0.04, RT + 0.45, -rz + 0.24), (-rx + 0.24, RT + 0.5, rz - 0.24)), ((rx - 0.24, RT + 0.45, -rz + 0.24), (rx + 0.04, RT + 0.5, rz - 0.24))):
        K.box(mn, mx, {'all': 'stcope'}, cull=False)
    K.box((-1.3, RT, 9.0), (1.3, RT + 1.9, 11.6), {'all': 'stband', 'top': 'stcope'}, cull=False)  # the lift overrun
    K.quad([(1.306, RT + 0.6, 10.9), (1.306, RT + 0.6, 9.7), (1.306, RT + 1.5, 9.7), (1.306, RT + 1.5, 10.9)], 'stvent')
    for z in (-9.0, -4.5):
        K.box((-1.0, RT, z - 0.7), (1.0, RT + 0.08, z + 0.7), {'all': 'stframe'}, cull=False)
        K.box((-0.85, RT + 0.08, z - 0.6), (0.85, RT + 1.15, z + 0.6), {'all': 'sthvac'}, cull=False)
        for sx in (-1, 1): K.quad([(sx * 0.856, RT + 0.2, z - 0.5), (sx * 0.856, RT + 0.2, z + 0.5), (sx * 0.856, RT + 1.05, z + 0.5), (sx * 0.856, RT + 1.05, z - 0.5)][::(-1 if sx > 0 else 1)], 'stvent')
        FL.tube(K, (0, RT + 1.15, z), (0, RT + 1.19, z), 0.45, 0.45, 'stcope', n=12, caps=(False, True))
        FL.tube(K, (0, RT + 1.19, z), (0, RT + 1.195, z), 0.38, 0.38, 'stfan', n=12, caps=(False, True))
    FL.dish(K, (1.6, RT, 3.0), (0.6, 0.9, -0.4), r=0.45)
    FL.aerial(K, (-1.7, RT, 14.5), h=1.9)
    K.finish(os.path.join(OUTDIR, 'wh_staff.glb'))


build()
