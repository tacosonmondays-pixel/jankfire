# The Rooftop penthouse (shared/map.js penthouse()): the glass pavilion in the middle of both Rooftop maps, drawn over
# its own boxes (tools/arch/dump.mjs), which stay what you bump into. A two-storey steel and glass box from the
# penthouse / pool-pavilion references: violet mirror glass between slim chrome mullions (glass you can't see through,
# like the walls you can't shoot through), a hot-pink candy spandrel between the floors, white corner columns, a deep
# white roof fascia with the pink neon in a channel, frosted glass balustrades with a chrome top rail round the roof and
# the stairwells, real stairs (wood up to the lounge, chequer plate up to the roof), glowing ceiling panels, the
# helipad painted on a raised deck with edge lights, a striped windsock. The furniture inside stays the map's boxes.
# Rooftop S&D's (penthouse_sd) has no door upstairs. local frame = the penthouse's (x +-10.15, z +-8.15, y up from
# the party block's roof).
# run: node tools/arch/dump.mjs rooftop penthouse tools/blender/arch/boxes/penthouse.json
#      node tools/arch/dump.mjs rooftop_sd penthouse_sd tools/blender/arch/boxes/penthouse_sd.json
#      blender52 -b --python tools/blender/arch/make_penthouse.py -- [penthouse|penthouse_sd]   (both by default)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
# gloss (0..1) and metal: archfield.js draws these with a standard material and a small night-sky reflection
MATS.update({
    'ph_glass': ('ph_glass', '#ffffff', {'gloss': 0.95}), 'ph_glassin': ('ph_glass', '#8a7aa8', {'gloss': 0.7}),
    'ph_frost': ('stucco', '#e6dcff', {'gloss': 0.8}), 'ph_chrome': ('metalplate', '#eef0f8', {'gloss': 0.9, 'metal': 1}),
    'ph_white': ('trim', '#fbf7ff', {'gloss': 0.6}), 'ph_pink': ('trim', '#ff4fc8', {'gloss': 0.7}),
    'ph_granite': ('concrete', '#4a4058', {'gloss': 0.4}), 'ph_carpet': ('carpet', '#e070c0', {}), 'ph_floor': ('planks', '#e8b888', {'gloss': 0.35}),
    'ph_ceiling': ('stucco', '#f4f0f8', {}), 'ph_deck': ('concrete', '#b4aac8', {}), 'ph_pad': ('tar', '#5a6270', {}),
    'ph_padline': ('trim', '#ffe14d', {}), 'ph_padh': ('trim', '#ffffff', {}), 'ph_tread': ('metalplate', '#c8ccd8', {'gloss': 0.5, 'metal': 1}),
    'ph_neon': ('trim', '#ff7ae0', {'glow': True, 'glowcol': '#ff4fd8'}), 'ph_lamp': ('stucco', '#fff6e8', {'glow': True, 'glowcol': '#fff0d8'}),
    'ph_padlamp': ('trim', '#7dff4f', {'glow': True, 'glowcol': '#39ff14'}), 'ph_sockr': ('trim', '#ff5a1a', {}), 'ph_sockw': ('trim', '#ffffff', {}),
})
NOCAST.update({'ph_chrome', 'ph_frost', 'ph_neon', 'ph_lamp', 'ph_padlamp', 'ph_padline', 'ph_padh', 'ph_sockr', 'ph_sockw', 'ph_tread'})
X1, Z1, T = 10.15, 8.15, 0.3  # outer faces, wall thickness
FLOORS = ((0.0, 3.75), (4.0, 7.6))  # the two storeys' walls
ROOF, PAR = 7.9, 8.7  # the roof's top, the parapet's top
MUL = 0.08  # mullion width
E = 0.002  # trims stand this far off the glass (never in its plane)


def sub_rect(r, c):
    """rectangle r (a0, a1, y0, y1) minus c: the up-to-four pieces left"""
    a0, a1, y0, y1 = r; c0, c1, d0, d1 = c
    if c1 <= a0 or c0 >= a1 or d1 <= y0 or d0 >= y1: return [r]
    out = []
    if c0 > a0: out.append((a0, c0, y0, y1))
    if c1 < a1: out.append((c1, a1, y0, y1))
    m0, m1 = max(a0, c0), min(a1, c1)
    if d0 > y0: out.append((m0, m1, y0, d0))
    if d1 < y1: out.append((m0, m1, d1, y1))
    return out


# fewer draw calls (one per material in the game): small parts share a bigger part's material
MERGE = {'ph_sockr': 'ph_pink', 'ph_sockw': 'ph_white', 'ph_padh': 'ph_white', 'trimdark': 'ph_chrome', 'ph_tread': 'ph_chrome', 'ph_ceiling': 'ph_white'}


def merge_mats(K, m):
    for (mat, node) in list(K.geo):
        if mat not in m: continue
        src = K.geo.pop((mat, node)); dst = K._bucket(m[mat], node); b = len(dst['v'])
        dst['v'] += src['v']; dst['uv'] += src['uv']; dst['f'] += [tuple(i + b for i in f) for f in src['f']]


def build(kind):
    K = Kit(os.path.join(HERE, 'boxes', kind + '.json'), seed=11)
    K.inside.append(((-X1 + T, 0, -Z1 + T), (X1 - T, ROOF, Z1 - T)))
    lamps_deco = [(x, 3.72, z, 1.6, 0.4) for x in (-6, 0, 5) for z in (-3, 3)] + [(x, 7.57, z, 1.6, 0.4) for x in (-4, 2) for z in (-4, 3)]

    # ---------------------------------------------------------------- the curtain wall: every glass wall box
    walls = K.take(lambda b: b['mat'] == 'glassblock')
    def face_mat(f, q):
        c = [sum(v[i] for v in q) / 4 for i in range(3)]
        if f in ('py', 'ny'): return 'ph_chrome'  # tops of parapets get a cap anyway; jamb heads / sills
        nrm = {'px': (1, 0, 0), 'nx': (-1, 0, 0), 'pz': (0, 0, 1), 'nz': (0, 0, -1)}[f]
        front = [c[i] + nrm[i] * 0.06 for i in range(3)]
        if K.is_inside(front): return 'ph_glassin'
        return 'ph_glass'
    # each wall plane in two: the storeys' walls, and the parapet round the roof (it's a balustrade, not glass)
    planes = {k + (p,): v for k, bs in K.walls(walls).items() for p, v in ((0, [b for b in bs if b['min'][1] < ROOF - 0.01]), (1, [b for b in bs if b['min'][1] >= ROOF - 0.01])) if v}
    for (axis, cc, tt, *_), bs in planes.items():
        for b in bs:
            ia = 0 if axis == 'x' else 2
            def mats(f, q, b=b, axis=axis):
                along = (axis == 'x' and f in ('px', 'nx')) or (axis == 'z' and f in ('pz', 'nz'))
                if along: return 'ph_chrome'  # the cut ends: door / window jambs, the wall's end
                return face_mat(f, q)
            K.box(b['min'], b['max'], {'all': mats}, sub=1.4)
        par = all(b['min'][1] >= ROOF - 0.01 for b in bs)
        out = 1 if cc > 0 else -1  # the outside of this wall plane (+z / +x for the far walls)
        ia = 0 if axis == 'x' else 2
        lo = -X1 if axis == 'x' else -Z1 + T; hi = -lo
        if par:
            # the roof's balustrade: frosted panels between posts, a chrome top rail
            for b in bs:
                for s in (out, -out):
                    o0, o1 = (tt / 2 + E, tt / 2 + 0.012) if s > 0 else (-tt / 2 - 0.012, -tt / 2 - E)
                    K.wbox(axis, cc, b['min'][ia] + 0.02, b['max'][ia] - 0.02, b['min'][1] + 0.04, b['max'][1] - 0.08, o0, o1, {'all': 'ph_frost'})
                FL.bar(K, K._P(axis, cc, b['min'][ia], PAR + 0.035, 0), K._P(axis, cc, b['max'][ia], PAR + 0.035, 0), 0.12, 'ph_chrome', h=0.07)
            continue
        # mullions (both faces) on a grid that splits each storey's run into equal bays, plus every opening's edge
        span = hi - lo; n = max(1, round(span / 1.36)); grid = [lo + span * k / n for k in range(n + 1)]
        ops = K.openings(axis, bs)
        edges = sorted(set([round(a, 3) for a, *_ in ops] + [round(o[1], 3) for o in ops]))
        lines = sorted(set([round(g, 3) for g in grid if all(abs(g - e) > 0.45 for e in edges)] + edges))
        lines = [a for a in lines if abs(a) < (X1 if axis == 'x' else Z1) - 0.4]  # (the corners are the columns')
        # every trim on each face laid out flat (along, height) first: frames, then mullions, then transoms, each cut
        # round what's already there, so no two pieces overlap (one back plane on the glass, nothing to flicker)
        lim = (X1 if axis == 'x' else Z1) - 0.33
        for s in (1, -1):
            lay = []
            def place(r, proud, lay=lay):
                pieces = [r]
                for e in lay: pieces = [q for p in pieces for q in sub_rect(p, e[:4])]
                lay += [p + (proud,) for p in pieces if p[1] - p[0] > 0.005 and p[3] - p[2] > 0.005]
            fr = 0.075 if s == out else 0.045
            BIG = (lo - 1, hi + 1)
            for yb in ((3.55, 4.05), (7.5, 7.95)): lay.append(BIG + yb + (None,))  # the spandrel and fascia bands (drawn round the outside below): trims stop at them
            for a0, a1, y0, y1, door in ops:  # the openings' chrome frames: jambs, head, a sill under windows
                place((a0 - 0.1, a0, y0, y1 + 0.1), fr); place((a1, a1 + 0.1, y0, y1 + 0.1), fr); place((a0, a1, y1, y1 + 0.1), fr)
                if not door: place((a0 - 0.1, a1 + 0.1, y0 - 0.08, y0), fr)
            lay.append(BIG + (0.0, 0.16, None))  # the plinth (frames stop short of it on their own)
            for a in lines:  # mullions up the wall's coverage on each line (the bits between the openings)
                if any(abs(a - e) < 1e-3 for e in edges): continue  # (an opening's edge: its frame is the mullion)
                cov = sorted((b['min'][1], b['max'][1]) for b in bs if b['min'][ia] - 1e-3 <= a <= b['max'][ia] + 1e-3)
                runs = []
                for y0, y1 in cov:
                    if runs and y0 <= runs[-1][1] + 1e-3: runs[-1][1] = max(runs[-1][1], y1)
                    else: runs.append([y0, y1])
                for y0, y1 in runs: place((max(lo, a - MUL / 2), min(hi, a + MUL / 2), y0, y1), 0.06 if s == out else 0.03)
            for (fy0, fy1) in FLOORS:  # transoms: a rail across the glass a bit over a metre up each storey
                yt = fy0 + 1.1
                segs = sorted((b['min'][ia], b['max'][ia]) for b in bs if b['min'][1] <= yt - 0.03 and b['max'][1] >= yt + 0.03)
                run = []
                for a0, a1 in segs:
                    if run and a0 <= run[-1][1] + 1e-3: run[-1][1] = max(run[-1][1], a1)
                    else: run.append([a0, a1])
                for a0, a1 in run: place((max(a0, -lim), min(a1, lim), yt - 0.03, yt + 0.03), 0.045 if s == out else 0.025)
            for (a0, a1, y0, y1, proud) in lay:
                if proud is None: continue
                o0, o1 = (tt / 2 + E, tt / 2 + proud) if s > 0 else (-tt / 2 - proud, -tt / 2 - E)
                K.wbox(axis, cc, a0 + 0.0015, a1 - 0.0015, y0 + 0.0015, y1 - 0.0015, o0, o1, {'all': 'ph_chrome'}, cull=False)
        # a glass slider parked beside each door
        for a0, a1, y0, y1, door in ops:
            if door and y1 - y0 > 2.0:
                # the sliding leaves, slid back over the fixed glass on the outside track (proud of the mullions)
                w = (a1 - a0) / 2
                for a, d in ((a0, -1), (a1, 1)):
                    if not any(b['min'][ia] - 1e-3 <= a + d * w <= b['max'][ia] + 1e-3 and b['min'][1] <= y0 + 0.05 for b in bs): continue
                    s = out
                    o0, o1 = (tt / 2 + 0.08, tt / 2 + 0.12) if s > 0 else (-tt / 2 - 0.12, -tt / 2 - 0.08)
                    p, q = sorted((a + d * 0.02, a + d * (w + 0.02)))
                    K.wbox(axis, cc, p + 0.055, q - 0.055, y0 + 0.02, y1 - 0.04, o0, o1, {'side': 'ph_glassin', 'top': 'ph_chrome', 'bottom': 'ph_chrome', 'px' if axis == 'z' else 'pz': 'ph_glassin', 'nx' if axis == 'z' else 'nz': 'ph_glassin'}, cull=False)
                    for e in (p - 0.005, q - 0.055):
                        K.wbox(axis, cc, e, e + 0.06, y0 + 0.02, y1 - 0.04, o0 - 0.005 * s, o1 + 0.005 * s, {'all': 'ph_chrome'}, cull=False)
    # ---------------------------------------------------------------- outside: columns, the spandrel, fascia, plinth
    for sx in (-1, 1):
        for sz in (-1, 1):
            xa, xb = sorted((sx * (X1 - 0.32), sx * (X1 + 0.1))); za, zb = sorted((sz * (Z1 - 0.32), sz * (Z1 + 0.1)))
            K.box((xa, 0.0, za), (xb, 7.95, zb), {'side': 'ph_white', 'top': 'ph_white', 'bottom': None}, cull=False)
            K.solids.append(((xa + 0.01, 0.0, za + 0.01), (xb - 0.01, 7.94, zb - 0.01)))  # (a solid now: AO, and what's buried in it can't flicker)
            # a chrome shoe at the foot
            xa2, xb2 = sorted((sx * (X1 - 0.36), sx * (X1 + 0.14))); za2, zb2 = sorted((sz * (Z1 - 0.36), sz * (Z1 + 0.14)))
            K.box((xa2, 0.0, za2), (xb2, 0.22, zb2), {'side': 'ph_chrome', 'top': 'ph_chrome'}, cull=False)
    def ring(y0, y1, o, mat, o0=0.0):
        """a band all round the outside from o0 to o proud of the glass, stopping at the corner columns"""
        for s in (-1, 1):
            K.wbox('x', s * (Z1 - T / 2), -X1 + 0.325, X1 - 0.325, y0, y1, *(sorted((s * (T / 2 + E + o0), s * (T / 2 + o)))), {'all': mat}, cull=False)
            K.wbox('z', s * (X1 - T / 2), -Z1 + 0.325, Z1 - 0.325, y0, y1, *(sorted((s * (T / 2 + E + o0), s * (T / 2 + o)))), {'all': mat}, cull=False)
    ring(3.602, 3.998, 0.08, 'ph_pink')  # the spandrel between the floors (the slab's edge)
    ring(3.55, 3.6, 0.1, 'ph_chrome'); ring(4.0, 4.05, 0.1, 'ph_chrome')
    ring(7.5, 7.95, 0.13, 'ph_white')  # the roof fascia
    ring(7.6, 7.62, 0.2, 'ph_white', o0=0.13); ring(7.82, 7.84, 0.2, 'ph_white', o0=0.13)  # its channel's lips
    # the neon in the channel: a tube all round (the old neon strip's spot)
    for s in (-1, 1):
        FL.bar(K, (-X1 + 0.12, 7.72, s * (Z1 + 0.18)), (X1 - 0.12, 7.72, s * (Z1 + 0.18)), 0.07, 'ph_neon')
        FL.bar(K, (s * (X1 + 0.18), 7.72, -Z1 + 0.12), (s * (X1 + 0.18), 7.72, Z1 - 0.12), 0.07, 'ph_neon')
    # the plinth: a dark granite course at the foot, stopping at the doors
    for (axis, cc, tt, *_), bs in planes.items():
        if any(b['min'][1] > 0.05 for b in bs) and not any(b['min'][1] < 0.05 for b in bs): continue
        ia = 0 if axis == 'x' else 2; out = 1 if cc > 0 else -1
        segs = sorted((b['min'][ia], b['max'][ia]) for b in bs if b['min'][1] < 0.05)
        run = []
        for a0, a1 in segs:
            if run and a0 <= run[-1][1] + 1e-3: run[-1][1] = max(run[-1][1], a1)
            else: run.append([a0, a1])
        for a0, a1 in run:
            lim = (X1 if axis == 'x' else Z1) - 0.365  # (to the corner columns' shoes)
            a0 = max(a0, -lim) if a0 <= -lim + 0.2 else a0 + 0.105; a1 = min(a1, lim) if a1 >= lim - 0.2 else a1 - 0.105  # (short of the door frames)
            o0, o1 = (tt / 2 + E, tt / 2 + 0.05) if out > 0 else (-tt / 2 - 0.05, -tt / 2 - E)
            if a1 > a0: K.wbox(axis, cc, a0, a1, 0.0, 0.16, o0, o1, {'all': 'ph_granite'}, cull=False)

    # ---------------------------------------------------------------- floors, ceilings, the roof deck
    for b in K.take(lambda b: b['mat'] == 'carpet'):
        K.plain(b, {'top': 'ph_carpet', 'side': 'ph_chrome'}, sub=1.6)
    for b in K.take(lambda b: b['mat'] == 'wood' and b['max'][1] - b['min'][1] < 0.3 and b['min'][1] > 3):
        K.plain(b, {'top': 'ph_floor', 'bottom': 'ph_ceiling', 'side': 'ph_white'}, sub=1.6)
    for b in K.take(lambda b: b['mat'] == 'roofg'):
        K.plain(b, {'top': 'ph_deck', 'bottom': 'ph_ceiling', 'side': 'ph_white'}, sub=1.6)
    # ceiling panels where the map had its lamps (they glow; a chrome rim)
    for (x, y, z, w, d) in lamps_deco:
        K.box((x - w / 2, y - 0.03, z - d / 2), (x + w / 2, y + 0.03, z + d / 2), {'bottom': 'ph_lamp', 'side': 'ph_chrome', 'top': None}, cull=False)
        K.box((x - w / 2 - 0.06, y + 0.015, z - d / 2 - 0.06), (x + w / 2 + 0.06, y + 0.03, z + d / 2 + 0.06), {'bottom': 'ph_chrome', 'side': 'ph_chrome', 'top': None}, cull=False)

    # ---------------------------------------------------------------- the stairs
    steps = K.take(lambda b: (b['mat'] == 'wood' and b['max'][1] - b['min'][1] >= 0.3) or (b['mat'] == 'metal' and b['min'][1] < 7.9 - 0.01 and 0.45 <= b['max'][2] - b['min'][2] <= 0.51 and b['max'][0] - b['min'][0] > 1.5))
    for seq, ax, d in K.stair_runs(steps):
        wood = seq[0]['mat'] == 'wood'
        c0 = seq[0]['min'][0]
        K.stairs(seq, ax, d, tread='ph_floor' if wood else 'ph_tread', riser='ph_white' if wood else 'ph_chrome', stringer='ph_white', rail_side=-1 if c0 > 0 else 1, rail='ph_chrome')
        for b in seq: b['_stair'] = True
    for b in steps:
        if not b.get('_stair'): K.plain(b, {'top': 'ph_tread', 'side': 'ph_white'})
    # rails round the stairwell and the roof hatch: frosted glass panels on chrome posts, a chrome top rail
    for b in K.take(lambda b: b['mat'] == 'metal' and b['max'][1] - b['min'][1] <= 1.05 and b['max'][1] - b['min'][1] > 0.5):
        x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
        along_x = x1 - x0 > z1 - z0
        if along_x: K.box((x0 + 0.02, y0 + 0.05, z0 + 0.03), (x1 - 0.02, y1 - 0.08, z1 - 0.03), {'all': 'ph_frost'}, cull=False)
        else: K.box((x0 + 0.03, y0 + 0.05, z0 + 0.02), (x1 - 0.03, y1 - 0.08, z1 - 0.02), {'all': 'ph_frost'}, cull=False)
        if along_x: K.box((x0 - 0.02, y1 - 0.08, z0 - 0.02), (x1 + 0.02, y1 + 0.02, z1 + 0.02), {'all': 'ph_chrome'}, cull=False)
        else: K.box((x0 - 0.02, y1 - 0.08, z0 + 0.03), (x1 + 0.02, y1 + 0.02, z1 - 0.03), {'all': 'ph_chrome'}, cull=False)  # (the rail along x has the corner)
        L = (x1 - x0) if along_x else (z1 - z0); n = max(1, round(L / 1.2))
        for k in range(n + 1):
            a = (x0 if along_x else z0) + L * k / n
            a = min(max(a, (x0 if along_x else z0) + 0.04), (x1 if along_x else z1) - 0.04)
            if along_x: K.box((a - 0.04, y0, z0 - 0.025), (a + 0.04, y1 - 0.08, z1 + 0.025), {'side': 'ph_chrome'}, cull=False)
            else: K.box((x0 - 0.025, y0, a - 0.04), (x1 + 0.025, y1 - 0.08, a + 0.04), {'side': 'ph_chrome'}, cull=False)

    # ---------------------------------------------------------------- the helipad: a raised deck, painted, edge lights
    for b in K.take(lambda b: b['mat'] == 'helipad'):
        x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
        K.plain(b, {'top': 'ph_pad', 'side': 'ph_padline'}, sub=1.5)
        y = y1 + 0.004
        def paint(p, mat):
            """a painted quad (4 points round at y) as a slab 4 mm proud, its edges sunk 1 cm into the pad"""
            K.quad(p, mat)
            for k in range(4):
                a, c = p[k], p[(k + 1) % 4]
                K.quad([(c[0], y1 - 0.01, c[2]), (a[0], y1 - 0.01, a[2]), a, c], mat)
        def flat(xa, za, xb, zb, mat):
            paint([(xa, y, zb), (xb, y, zb), (xb, y, za), (xa, y, za)], mat)
        # the touchdown ring (yellow), the H (white), a white edge line
        n = 32; r0, r1 = 3.2, 3.55
        for k in range(n):
            a, c = k * math.tau / n, (k + 1) * math.tau / n
            p = [(r1 * math.cos(a), y, r1 * math.sin(a)), (r1 * math.cos(c), y, r1 * math.sin(c)), (r0 * math.cos(c), y, r0 * math.sin(c)), (r0 * math.cos(a), y, r0 * math.sin(a))]
            paint(p if (p[1][0] - p[0][0]) * (p[3][2] - p[0][2]) - (p[1][2] - p[0][2]) * (p[3][0] - p[0][0]) < 0 else p[::-1], 'ph_padline')
        flat(-1.3, -1.6, -0.75, 1.6, 'ph_padh'); flat(0.75, -1.6, 1.3, 1.6, 'ph_padh'); flat(-0.75, -0.25, 0.75, 0.25, 'ph_padh')
        for (xa, za, xb, zb) in ((x0 + 0.15, z0 + 0.15, x1 - 0.15, z0 + 0.3), (x0 + 0.15, z1 - 0.3, x1 - 0.15, z1 - 0.15), (x0 + 0.15, z0 + 0.3, x0 + 0.3, z1 - 0.3), (x1 - 0.3, z0 + 0.3, x1 - 0.15, z1 - 0.3)):
            # dashed: 0.6 on, 0.4 off
            if xb - xa > zb - za:
                a = xa
                while a < xb - 0.1: flat(a, za, min(a + 0.6, xb), zb, 'ph_padh'); a += 1.0
            else:
                a = za
                while a < zb - 0.1: flat(xa, a, xb, min(a + 0.6, zb), 'ph_padh'); a += 1.0
        for k in range(12):  # edge lights: low green domes round it
            t = k / 12 * 4
            side, f = int(t), t - int(t)
            px, pz = [(x0 + (x1 - x0) * f, z0), (x1, z0 + (z1 - z0) * f), (x1 - (x1 - x0) * f, z1), (x0, z1 - (z1 - z0) * f)][side]
            px = min(max(px, x0 + 0.12), x1 - 0.12); pz = min(max(pz, z0 + 0.12), z1 - 0.12)
            FL.tube(K, (px, y1, pz), (px, y1 + 0.07, pz), 0.07, 0.04, 'ph_padlamp', n=6)

    # ---------------------------------------------------------------- the windsock: a striped mast, the sock on a hoop
    for b in K.take(lambda b: b['mat'] == 'metal' and b['max'][1] > 10):
        cx, cz = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2
        FL.tube(K, (cx, b['min'][1], cz), (cx, b['min'][1] + 0.12, cz), 0.16, 0.16, 'ph_chrome', n=8)
        for k in range(6):
            y0 = b['min'][1] + 0.12 + k * 0.48; FL.tube(K, (cx, y0, cz), (cx, y0 + 0.48, cz), 0.065, 0.065, 'ph_sockr' if k % 2 else 'ph_sockw', n=8, caps=(k == 0, k == 5))
        top = b['max'][1]
        FL.tube(K, (cx, top, cz), (cx, top + 0.1, cz), 0.09, 0.0, 'ph_chrome', n=8)
        # the hoop and the sock blowing out along +x (where the map's hazard box hung: x 8.88..10.2, y 10.3..10.75)
        hy = 10.52; FL.bar(K, (cx, hy, cz), (cx + 0.18, hy, cz), 0.04, 'ph_chrome')
        L = 1.3; segs = 5
        for k in range(segs):
            xa, xb = cx + 0.2 + L * k / segs, cx + 0.2 + L * (k + 1) / segs
            ra, rb = 0.24 - 0.12 * k / segs, 0.24 - 0.12 * (k + 1) / segs
            droop = lambda x: -0.06 * ((x - cx - 0.2) / L) ** 2
            FL.tube(K, (xa, hy + droop(xa), cz), (xb, hy + droop(xb), cz), ra, rb, 'ph_sockr' if k % 2 == 0 else 'ph_sockw', n=10, caps=(False, False), inside=True)

    left = [b for b in K.boxes if not b.get('_done')]
    for b in left:
        print('plain:', b['mat'], b['min'], b['max'])
        K.plain(b, {'all': 'ph_white'})
    return K


for kind in ([a for a in argv if a in ('penthouse', 'penthouse_sd')] or ['penthouse', 'penthouse_sd']):
    K = build(kind)
    merge_mats(K, MERGE)
    K.finish(os.path.join(OUTDIR, kind + '.glb'))
