# The Warehouse hall (shared/map.js warehouse() / warehouseSD(), hallArch()): drawn over its own boxes, which stay what
# you bump into. A steel-framed distribution shed like a real regional depot: a precast concrete plinth with a drip
# flashing, silver trapezoidal cladding over it, a hot pink fascia band round the top with the parapet behind it and a
# coping on that, pink corner flashings and downpipes off hopper heads; the clerestory window cuts get steel frames, drip
# hoods and a few broken panes; every door is a roller shutter rolled up into its drum (yellow slats, guide channels
# inside, hazard-striped jambs and a striped head outside); the dock doors (Warehouse's south wall) get black dock
# shelters, rubber bumpers, dock lights on arms and numbered lightboxes. On the blue roof: rooflight strips glowing with
# the lamps inside, turbine vents, two AC units, a hatch. Inside: a concrete dado with a safety stripe, cream liner
# panels, blue steel columns under yellow lattice girders (the game's rafters are their bottom chords), purlins, and
# high-bay lamps on chains. A few mismatched replacement panels and some graffiti on the plinth: it's been here a while.
# The company boards (pictures) stay the game's. local frame = the map's (the hall is centred on 0, 0).
# run: node tools/arch/dumpdeco.mjs warehouse wh_hall tools/blender/arch/boxes/wh_hall.json
#      node tools/arch/dumpdeco.mjs warehouse_sd wh_hall_sd tools/blender/arch/boxes/wh_hall_sd.json
#      blender52 -b --python tools/blender/arch/make_wh_hall.py -- [wh_hall|wh_hall_sd]   (both by default)
import os, sys, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST, bands

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'whclad': ('profile', '#d2d8e2', {}), 'whliner': ('profile', '#f2ecdc', {}), 'whplinth': ('concrete', '#ece6da', {}),
    'whdado': ('concrete', '#c4c0b6', {}), 'whpink': ('profile', '#ff4fd8', {}), 'whpinkflat': ('trim', '#ff4fd8', {}),
    'whcope': ('metalplate', '#d8dce2', {}), 'whsteel': ('trim', '#3a3d44', {}), 'whgirder': ('trim', '#ffc21a', {}),
    'whcolumn': ('trim', '#2f6fd0', {}), 'whpurlin': ('trim', '#a4acb8', {}), 'whdeck': ('profile', '#e6eaee', {}),
    'whroof': ('profile', '#4a78c8', {}), 'whshutter': ('louvre', '#ffd23a', {}), 'whdrum': ('metalplate', '#8a919c', {}),
    'whhazy': ('trim', '#ffd400', {}), 'whhazk': ('trim', '#1c1c20', {}), 'whseal': ('tar', '#2a2830', {}),
    'whlamp': ('metalplate', '#c9ced6', {}), 'whglow': ('stucco', '#fff3c8', {'glow': True}), 'whsign': ('stucco', '#ffe14d', {'glow': True}),
    'whsky': ('glass', '#d8f4ff', {'glow': True}), 'whskyin': ('trim', '#a8c4dc', {}), 'whpatch': ('corrugated', '#7fd6c8', {}),
    'whpatch2': ('corrugated', '#e8a0c0', {}), 'whvent': ('louvre', '#c0c4ca', {}), 'whhvac': ('metalplate', '#e4e2da', {}), 'whfan': ('tar', '#1e1e24', {}),
})
NOCAST.update({'whgirder', 'whcolumn', 'whdrum', 'whshutter', 'whhvac', 'whseal', 'whpink', 'whdado'})  # (under the roof, or skins on the walls: the sun never needs them)
NOCAST.update({'whpinkflat', 'whcope', 'whsteel', 'whhazy', 'whhazk', 'whlamp', 'whglow', 'whsign', 'whsky', 'whskyin', 'whpatch', 'whpatch2', 'whvent', 'whfan', 'whpurlin'})
VAR = {'wh_hall': dict(HX=32.0, HZ=18.0, H=10.0, docks=True), 'wh_hall_sd': dict(HX=24.0, HZ=22.0, H=9.0, docks=False)}
T = 0.6  # wall thickness


def build(kind):
    v = VAR[kind]; HX, HZ, H = v['HX'], v['HZ'], v['H']
    d = json.load(open(os.path.join(HERE, 'boxes', kind + '.json')))
    deco = [b for b in d['boxes'] if b.get('deco')]
    d['boxes'] = [b for b in d['boxes'] if not b.get('deco')]  # (the deco is dressing to replace, not something solid)
    K = Kit(d, seed=11)
    rng = random.Random(5)
    K.inside.append(((-HX + T / 2, 0, -HZ + T / 2), (HX - T / 2, H, HZ - T / 2)))
    rafters = sorted(K.take(lambda b: b['mat'] == 'wood'), key=lambda b: b['min'][2])
    RB = rafters[0]['min'][1]  # the girders' bottom chord: the game's rafters
    walls = K.take(lambda b: b['mat'] == 'metal')
    roof = K.take(lambda b: b['mat'] == 'roofblue')[0]
    doors, wins = [], []
    planes = {}  # the four walls (Kit.walls would take a sliver between a door and a window for a wall across)
    for b in walls:
        if abs(abs(b['min'][2] + b['max'][2]) / 2 - HZ) < 0.01 and b['max'][2] - b['min'][2] < 0.61: k = ('x', HZ if b['min'][2] > 0 else -HZ, T, 0)
        else: k = ('z', HX if b['min'][0] > 0 else -HX, T, 0)
        planes.setdefault(k, []).append(b)
    assert len(planes) == 4 and all(abs(abs((b['min'][0] + b['max'][0]) / 2) - HX) < 0.01 for k, bs in planes.items() if k[0] == 'z' for b in bs), 'the walls'

    def F(axis, c, s, a0, a1, y0, y1, d0, d1, mats, cull=True):
        """a box on a wall face: s = which side (+1 = toward +x/+z), d0..d1 = how far out from that face"""
        f = c + s * T / 2
        o0, o1 = sorted((f - c + s * d0, f - c + s * d1))
        K.wbox(axis, c, a0, a1, y0, y1, o0, o1, mats if isinstance(mats, dict) else {'all': mats}, cull=cull)
    pend = []
    def Fd(axis, c, s, a0, a1, y0, y1, d0, d1, mats):
        """F, held back: the door dressing is registered as solid first, so the faces where its pieces meet are dropped"""
        f = c + s * T / 2
        o0, o1 = sorted((f - c + s * d0, f - c + s * d1))
        p, q = K._P(axis, c, a0, y0, o0), K._P(axis, c, a1, y1, o1)
        K.solids.append(([min(p[i], q[i]) for i in range(3)], [max(p[i], q[i]) for i in range(3)]))
        pend.append((axis, c, s, a0, a1, y0, y1, d0, d1, mats))

    # ---- the walls: cladding out, liner in, the openings found
    for (axis, c, t, _), bs in planes.items():
        so = 1 if c > 0 else -1  # outside
        ops = K.wall_plane(axis, c, t, bs, 'whclad', 'whliner', trim='whsteel', sub=2.0, frames=False, sill=False, shards=False, doors=False)
        for (a0, a1, y0, y1, isdoor) in ops: (doors if isdoor else wins).append((axis, c, so, a0, a1, y0, y1))
        oo = (T / 2, T / 2 + 0.06) if so > 0 else (-T / 2 - 0.06, -T / 2)
        oi = (-T / 2 - 0.04, -T / 2) if so > 0 else (T / 2, T / 2 + 0.04)
        bands(K, axis, c, bs, [(0.0, 2.4, 'whplinth')], *oo)
        bands(K, axis, c, bs, [(2.4, 2.46, 'whcope')], *(((T / 2, T / 2 + 0.1) if so > 0 else (-T / 2 - 0.1, -T / 2))))  # the drip flashing
        bands(K, axis, c, bs, [(0.0, 1.2, 'whdado'), (1.2, 1.36, 'whhazy')], *oi)
        L = HX if axis == 'x' else HZ
        # the fascia: one pink band right round the top, over the wall head, the roof's edge and the parapet
        ext = 0.35 if axis == 'x' else 0.3
        F(axis, c, so, -L - ext, L + ext, H - 1.3, H + 1.1, 0, 0.05, {'all': 'whpink', 'top': 'whcope'}, cull=False)
        # jank: a few replacement panels that never matched
        for k in range(2 if axis == 'x' else 1):
            for _ in range(20):
                a = rng.uniform(-L + 2, L - 2)
                if all(not (o[3] - 1.2 < a < o[4] + 1.2) for o in doors + wins if o[0] == axis and o[1] == c): break
            F(axis, c, so, a - 0.5, a + 0.5, 2.47, 2.47 + rng.uniform(2.2, 3.4), 0.012, 0.016, {'all': 'whpatch' if k == 0 else 'whpatch2'}, cull=False)

    # ---- the parapet behind the fascia, the coping on it
    y0, y1 = H + 0.5, H + 1.1
    ex, ez = HX + 0.3, HZ + 0.3
    for (mn, mx, out) in (((-ex, y0, -ez), (ex, y1, -ez + 0.3), 'nz'), ((-ex, y0, ez - 0.3), (ex, y1, ez), 'pz'),
                          ((-ex, y0, -ez + 0.3), (-ex + 0.3, y1, ez - 0.3), 'nx'), ((ex - 0.3, y0, -ez + 0.3), (ex, y1, ez - 0.3), 'px')):
        K.box(mn, mx, {'all': 'whclad', out: None, 'top': None}, cull=False)
    for (mn, mx) in (((-ex - 0.09, y1, -ez - 0.09), (ex + 0.09, y1 + 0.07, -ez + 0.34)), ((-ex - 0.09, y1, ez - 0.34), (ex + 0.09, y1 + 0.07, ez + 0.09)),
                     ((-ex - 0.09, y1, -ez + 0.34), (-ex + 0.34, y1 + 0.07, ez - 0.34)), ((ex - 0.34, y1, -ez + 0.34), (ex + 0.09, y1 + 0.07, ez - 0.34))):
        K.box(mn, mx, {'all': 'whcope'}, cull=False)

    # ---- the roof: the deck, rooflight strips (lit from inside), vents, AC units, a hatch
    K.plain(roof, {'top': 'whroof', 'side': None, 'bottom': 'whdeck'}, sub=4.0)
    zs = [(rafters[i]['max'][2] + rafters[i + 1]['min'][2]) / 2 for i in range(len(rafters) - 1)]
    RT = roof['max'][1]
    for z in zs:
        x = -HX + 3.0
        while x + 2.6 <= HX - 3.0:
            K.box((x, RT, z - 0.6), (x + 2.6, RT + 0.12, z + 0.6), {'top': 'whsky', 'side': 'whcope'}, cull=False)
            K.quad([(x, H - 0.03, z - 0.6), (x + 2.6, H - 0.03, z - 0.6), (x + 2.6, H - 0.03, z + 0.6), (x, H - 0.03, z + 0.6)], 'whskyin')
            x += 3.2
    cx = [-HX * 0.62, -HX * 0.2, HX * 0.25, HX * 0.66]
    for i, x in enumerate(cx):  # turbine vents on the girder lines, between the rooflights
        z = rafters[1 + (i % 2) * (len(rafters) - 3)]['min'][2] + 0.25
        FL.tube(K, (x, RT, z), (x, RT + 0.45, z), 0.2, 0.2, 'whlamp', n=10, caps=(False, False))
        FL.tube(K, (x, RT + 0.45, z), (x, RT + 0.95, z), 0.36, 0.36, 'whvent', n=12, caps=(False, False))
        FL.tube(K, (x, RT + 0.95, z), (x, RT + 1.2, z), 0.36, 0.05, 'whcope', n=12, caps=(False, True))
        FL.tube(K, (x, RT + 0.45, z), (x, RT + 0.46, z), 0.37, 0.37, 'whcope', n=12, caps=(True, False))
    for (x, z) in ((HX * 0.42, rafters[len(rafters) // 2]['min'][2] + 0.25 + 1.4), (-HX * 0.42, rafters[len(rafters) // 2 - 1]['min'][2] + 0.25 - 1.4)):
        K.box((x - 1.3, RT + 0.08, z - 0.65), (x + 1.3, RT + 1.3, z + 0.65), {'all': 'whhvac'}, cull=False)
        for s in (-1, 1): K.quad([(x - 1.2, RT + 0.2, z + s * 0.656), (x + 1.2, RT + 0.15, z + s * 0.656), (x + 1.2, RT + 1.15, z + s * 0.656), (x - 1.2, RT + 1.15, z + s * 0.656)][::(1 if s > 0 else -1)], 'whvent')
        for fx in (x - 0.6, x + 0.6):
            FL.tube(K, (fx, RT + 1.3, z), (fx, RT + 1.34, z), 0.48, 0.48, 'whcope', n=12, caps=(False, True))
            FL.tube(K, (fx, RT + 1.34, z), (fx, RT + 1.345, z), 0.4, 0.4, 'whfan', n=12, caps=(False, True))
        K.box((x - 1.4, RT, z - 0.75), (x + 1.4, RT + 0.08, z + 0.75), {'all': 'whsteel'}, cull=False)  # the plinth it stands on
    hx, hz = HX * 0.05, (rafters[-2]['min'][2] + rafters[-2]['max'][2]) / 2
    K.box((hx - 0.55, RT, hz - 0.55), (hx + 0.55, RT + 0.45, hz + 0.55), {'all': 'whhvac'}, cull=False)
    K.box((hx - 0.62, RT + 0.45, hz - 0.62), (hx + 0.62, RT + 0.52, hz + 0.62), {'all': 'whdrum'}, cull=False)

    # ---- the clerestory: steel frames, sills, a drip hood, broken panes in the corners
    for (axis, c, so, a0, a1, y0, y1) in wins:
        K.dress_opening(axis, c, T, a0, a1, y0, y1, False, 'whsteel', True, True, True, False)
        F(axis, c, so, a0 - 0.15, a1 + 0.15, y1 + 0.12, y1 + 0.19, 0, 0.16, 'whcope', cull=False)

    # ---- the doors: roller shutters rolled up into their drums. docks get shelters, bumpers, lights and numbers
    docks = sorted([o for o in doors if v['docks'] and o[0] == 'x' and o[1] > 0], key=lambda o: o[3])
    signs = sorted([b for b in deco if b['mat'] == 'neonyellow'], key=lambda b: b['min'][0])
    for (axis, c, so, a0, a1, y0, y1) in doors:
        si = -so
        dock = (axis, c, so, a0, a1, y0, y1) in docks
        # inside: the drum box over the head, guide channels down the jambs, the curtain's last slats and bottom bar
        F(axis, c, si, a0 - 0.25, a1 + 0.25, y1, y1 + 0.75, 0, 0.55, {'all': 'whdrum'})
        for (p, q) in ((a0 - 0.14, a0), (a1, a1 + 0.14)): F(axis, c, si, p, q, 0, y1, 0, 0.14, 'whsteel')
        F(axis, c, si, a0, a1, y1 - 0.38, y1, 0.05, 0.09, 'whshutter', cull=False)
        F(axis, c, si, a0, a1, y1 - 0.44, y1 - 0.38, 0.04, 0.1, 'whhazk', cull=False)
        # outside: steel flashing round it, hazard paint up the jambs
        for (p, q) in ((a0 - 0.16, a0), (a1, a1 + 0.16)):
            for k in range(7): Fd(axis, c, so, p, q, k * 0.2, k * 0.2 + 0.2, 0, 0.09, 'whhazy' if k % 2 == 0 else 'whhazk')
            Fd(axis, c, so, p, q, 1.4, y1, 0, 0.09, 'whsteel')
        Fd(axis, c, so, a0 - 0.16, a1 + 0.16, y1, y1 + 0.16, 0, 0.09, 'whsteel')
        if not dock:  # a striped head over it
            n = max(2, round((a1 - a0 + 0.32) / 0.6))
            w = (a1 - a0 + 0.32) / n
            for k in range(n): Fd(axis, c, so, a0 - 0.16 + k * w, a0 - 0.16 + (k + 1) * w, y1 + 0.16, y1 + 0.4, 0, 0.07, 'whhazy' if k % 2 == 0 else 'whhazk')
            K.decal_on(axis, c, so, T / 2 + 0.002, a1 + 0.75, 2.95, 'sign_warn', w=0.6, h=0.6)
            continue
        i = docks.index((axis, c, so, a0, a1, y0, y1))
        for (p, q) in ((a0 - 0.5, a0 - 0.16), (a1 + 0.16, a1 + 0.5)): Fd(axis, c, so, p, q, 0.0, y1 + 0.16, 0, 0.3, 'whseal')  # the shelter's side pads
        Fd(axis, c, so, a0 - 0.5, a1 + 0.5, y1 + 0.16, y1 + 0.7, 0, 0.36, 'whseal')  # its head curtain
        for (p, q) in ((a0 - 0.95, a0 - 0.55), (a1 + 0.55, a1 + 0.95)):
            F(axis, c, so, p, q, 0.15, 0.6, 0, 0.18, 'whseal')
            F(axis, c, so, p - 0.03, q + 0.03, 0.12, 0.63, 0, 0.03, 'whsteel', cull=False)  # (its plate)
        # the dock light: a box on the wall, an arm out toward the door, a lamp head
        la = a1 + 1.3
        F(axis, c, so, la - 0.15, la + 0.15, 2.7, 3.0, 0.09, 0.2, 'whsteel', cull=False)
        f = c + so * (T / 2 + 0.2)
        pt = (lambda a, y, o: (a, y, f + so * o)) if axis == 'x' else (lambda a, y, o: (f + so * o, y, a))
        FL.bar(K, pt(la, 2.85, 0.0), pt(la - 0.45, 2.95, 0.55), 0.05, 'whsteel')
        FL.tube(K, pt(la - 0.45, 2.95, 0.55), pt(la - 0.62, 2.82, 0.72), 0.13, 0.16, 'whlamp', n=8, caps=(True, False))
        FL.tube(K, pt(la - 0.62, 2.82, 0.72), pt(la - 0.63, 2.81, 0.73), 0.15, 0.15, 'whglow', n=8, caps=(False, True))
        # the number: a lightbox where the game's sign is (its light stays the game's)
        if i < len(signs):
            s = signs[i]; sa0, sa1 = (s['min'][0], s['max'][0]) if axis == 'x' else (s['min'][2], s['max'][2])
            face = ('pz' if so > 0 else 'nz') if axis == 'x' else ('px' if so > 0 else 'nx')
            F(axis, c, so, sa0, sa1, y1 + 0.85, y1 + 1.65, 0.09, 0.2, {'all': 'whsteel', face: 'whsign'}, cull=False)
            K.decal_on(axis, c, so, T / 2 + 0.205, (sa0 + sa1) / 2, y1 + 1.25, 'num_%d' % (i + 1), w=0.85, h=0.64)

    for a in pend: F(*a)
    # ---- inside: blue columns up the walls (between the windows, and under every girder end), yellow lattice girders
    # over the game's rafters, purlins across them under the deck
    def clear(axis, c, a, w=0.6):
        return all(not (o[3] - w < a < o[4] + w) for o in doors if o[0] == axis and o[1] == c)
    cols = []
    for (axis, c, t, _), bs in planes.items():
        if axis == 'x':
            ws = sorted(o[3] for o in wins if o[0] == axis and o[1] == c)
            for k in range(len(ws) - 1):
                a = (ws[k] + ws[k + 1] + 1.5) / 2
                if clear(axis, c, a): cols.append((axis, c, a, H - 0.25))
        else:
            for r in rafters:
                a = (r['min'][2] + r['max'][2]) / 2
                if clear(axis, c, a): cols.append((axis, c, a, RB))
    for (axis, c, a, top) in cols:
        si = -1 if c > 0 else 1
        F(axis, c, si, a - 0.04, a + 0.04, 0, top, 0, 0.26, 'whcolumn')  # web
        F(axis, c, si, a - 0.19, a + 0.19, 0, top, 0.26, 0.31, 'whcolumn')  # flange
        F(axis, c, si, a - 0.26, a + 0.26, 0, 0.03, 0, 0.36, 'whsteel', cull=False)  # base plate
        if top < H - 0.5: F(axis, c, si, a - 0.24, a + 0.24, top - 0.05, top, 0, 0.4, 'whsteel', cull=False)  # the cap the girder sits on
    for r in rafters:
        (x0, y0, z0), (x1, y1, z1) = r['min'], r['max']
        zc = (z0 + z1) / 2
        K.box((x0, y0, z0), (x1, y1, z1), {'all': 'whgirder'})  # bottom chord
        K.box((x0, H - 0.26, zc - 0.18), (x1, H, zc + 0.18), {'all': 'whgirder'})  # top chord
        n = int((x1 - x0) / 2.0)
        step = (x1 - x0 - 0.6) / n
        for k in range(n):
            xa, xb = x0 + 0.3 + k * step, x0 + 0.3 + (k + 1) * step
            lo, hi = (y1, H - 0.26) if k % 2 == 0 else (H - 0.26, y1)
            FL.bar(K, (xa, lo, zc), (xb, hi, zc), 0.11 if k % 2 == 0 else 0.1, 'whgirder')
            if k % 3 == 0: FL.bar(K, (xa, y1 - 0.05, zc), (xa, H - 0.21, zc), 0.07, 'whgirder')
    x = -HX + 1.5
    while x < HX - 1.0:
        K.box((x - 0.06, H - 0.2, -HZ + T / 2), (x + 0.06, H, HZ - T / 2), {'all': 'whpurlin'})
        x += 3.0

    # ---- the high-bay lamps (the game's lamp boxes still light the floor): a chain, the driver, a spun reflector, the lens
    for b in deco:
        if b['mat'] != 'lamp': continue
        x, z = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2
        ly = b['min'][1]
        FL.bar(K, (x, RB + 0.06, z), (x, ly + 0.38, z), 0.035, 'whsteel')
        FL.tube(K, (x, ly + 0.42, z), (x, ly + 0.2, z), 0.18, 0.21, 'whlamp', n=10, caps=(True, False))
        FL.tube(K, (x, ly + 0.2, z), (x, ly + 0.02, z), 0.24, 0.6, 'whlamp', n=12, caps=(False, False), inside=True)
        FL.tube(K, (x, ly + 0.035, z), (x, ly + 0.03, z), 0.57, 0.57, 'whglow', n=12, caps=(False, True))

    # ---- downpipes off hopper heads (pink, like the fascia), pink corner flashings
    for (axis, c, t, _), bs in planes.items():
        so = 1 if c > 0 else -1
        L = HX if axis == 'x' else HZ
        ws = sorted(o[3] + 0.75 for o in wins if o[0] == axis and o[1] == c)  # (window centres)
        pa = [-L + 1.2, L - 1.2] + [(ws[k] + ws[k + 1]) / 2 for k in range(0, len(ws) - 1, 3)]
        for a in pa:
            if not clear(axis, c, a, 1.2): continue
            F(axis, c, so, a - 0.24, a + 0.24, H + 0.45, H + 0.95, 0.05, 0.36, 'whpinkflat', cull=False)
            f = c + so * T / 2
            pt = (lambda a, y, o: (a, y, f + so * o)) if axis == 'x' else (lambda a, y, o: (f + so * o, y, a))
            FL.bar(K, pt(a, H + 0.46, 0.2), pt(a, 0.32, 0.2), 0.13, 'whpinkflat')
            FL.bar(K, pt(a, 0.38, 0.2), pt(a, 0.1, 0.42), 0.115, 'whpinkflat')
            for y in (2.9, 5.4, 7.9):
                if y < H - 1.4: F(axis, c, so, a - 0.1, a + 0.1, y, y + 0.06, 0.06, 0.29, 'whsteel', cull=False)  # brackets
    for sx in (-1, 1):
        for sz in (-1, 1):
            xa, xb = sorted((sx * (ex - 0.65), sx * (ex + 0.05))); za, zb = sorted((sz * (ez - 0.65), sz * (ez + 0.05)))
            K.box((xa, 2.46, za), (xb, H - 1.3, zb), {'all': 'whpinkflat'}, cull=False)
            for (y0_, y1_, p, m) in ((0.0, 2.4, 0.06, 'whplinth'), (2.4, 2.46, 0.1, 'whcope')):  # the plinth and its drip round the corner
                xa, xb = sorted((sx * (ex - 0.005), sx * (ex + p))); za, zb = sorted((sz * (ez - T - 0.005), sz * (ez + p)))
                K.box((xa, y0_, za), (xb, y1_, zb), {'all': m}, cull=False)

    # ---- graffiti, posters and stickers low on the plinth, grime under some windows (dress_opening did those)
    tags = ['tag_0', 'tag_1', 'tag_2', 'tag_3', 'poster_1', 'sticker_2', 'poster_3', 'sticker_0']
    for k, (axis, c) in enumerate([('x', -HZ), ('x', HZ), ('z', -HX), ('z', HX)] * 2):
        so = 1 if c > 0 else -1
        L = HX if axis == 'x' else HZ
        for _ in range(30):
            a = rng.uniform(-L + 3, L - 3)
            if clear(axis, c, a, 3.0): break
        cell = tags[k % len(tags)]
        w, h = (2.4, 1.2) if cell.startswith('tag') else (0.7, 1.0) if cell.startswith('poster') else (0.35, 0.35)
        K.decal_on(axis, c, so, T / 2 + 0.062, a, 1.2 if cell.startswith('tag') else 1.5, cell, w=w, h=h)

    if os.environ.get('ZALL'): K.zcheck(limit=1000); return
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in VAR] or list(VAR)):
    build(kind)
