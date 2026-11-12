# The Spire, Skyline's middle (shared/map.js skyline() / skylineSD(), spireArch()): drawn over its own boxes
# (tools/arch/dump.mjs), which stay what you bump into. The hub tower is a blue glass curtain wall 160 m down to the street:
# chrome mullions every bay, navy spandrel bands every floor, chrome fins up the corners, a few offices still lit at dusk,
# a cornice and a chrome-edged roof slab. The deck's parapet: concrete with a chrome cap and a cyan neon line inside.
# The shaft (shell(): five floors, four on S&D) in lighter glass with the window holes framed (shards left in the
# corners), floor bands, grated floors and stairs inside, the nest's parapet capped, four chrome fins rising past it
# for the silhouette (thin: nothing to stand on). The mast: an aviation-striped steel post on a flange, two grated
# service rings, panel and dish antennas, the pink neon halo (Skyline), the red beacon on top.
# local frame = the deck (0 = the deck's top, the shaft's middle at x 0, z 0).
# run: node tools/arch/dump.mjs skyline spire tools/blender/arch/boxes/spire.json
#      node tools/arch/dump.mjs skyline_sd spire_sd tools/blender/arch/boxes/spire_sd.json
#      blender52 -b --python tools/blender/arch/make_spire.py -- [spire|spire_sd]   (both by default)
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST, dress_shell, cap, corner_boards

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'spglass': ('fac_glass', '#ffffff', {}), 'spbody': ('fac_glass', '#ffffff', {}), 'spint': ('stucco', '#d8e2ee', {}), 'railglass': ('glass', '#e8f4ff', {}),
    'mullion': ('metalplate', '#e4ecf4', {}), 'spandrel': ('metalplate', '#4a6496', {}), 'grate': ('metalplate', '#80858e', {}),
    'mastred': ('trim', '#e8342c', {}), 'mastwhite': ('trim', '#f6f6f2', {}), 'steel': ('metalplate', '#5a6068', {}),
    'lit': ('stucco', '#ffd98a', {'glow': True}), 'litcool': ('stucco', '#9fe8ff', {'glow': True}),
    'neonpink': ('stucco', '#ff4fd8', {'glow': True}), 'neoncyan': ('stucco', '#4fd8ff', {'glow': True}), 'beacon': ('stucco', '#ff3030', {'glow': True}),
})
NOCAST.update({'railglass', 'mullion', 'grate', 'mastred', 'mastwhite', 'steel', 'lit', 'litcool', 'neonpink', 'neoncyan', 'beacon', 'spandrel'})
SHOW = -90  # below this the body is deep in the haze: plain glass, no relief
F = 4.4  # a storey (the shaft's, and the body's bands)


def build(id_):
    K = Kit(os.path.join(HERE, 'boxes', id_ + '.json'), seed=7)
    K.ground = -1e9
    rng = random.Random(11)
    body = K.take(lambda b: b['mat'] == 'glassblock' and b['max'][1] < -0.4)[0]
    x0, y0, z0 = body['min']; x1, y1, z1 = body['max']
    K.ground = y0
    mast = K.take(lambda b: b['mat'] == 'metal' and b['max'][1] - b['min'][1] > 5)[0]
    floors = 5 if id_ == 'spire' else 4

    # ---- the body: a curtain wall (the kit's fac_glass: a floor's spandrel over two panes a tile, 4.4 m), the floors
    # counted down from the roof. one quad per face below SHOW, a quad per floor above it (for the AO)
    sides = (('x', z0, -1, x0, x1), ('x', z1, 1, x0, x1), ('z', x0, -1, z0, z1), ('z', x1, 1, z0, z1))
    floors_y = [y1 - k * F for k in range(int((y1 - SHOW) / F) + 1)]  # each floor's top (its spandrel just under)
    for (axis, c, s, a0, a1) in sides:
        P = FL.WP(axis, c, s)
        nt = max(1, round((a1 - a0) / F))
        ends = (a0, a1) if s > 0 and axis == 'x' or s < 0 and axis == 'z' else (a1, a0)  # (counter-clockwise from outside)
        def q(ya, yb):
            va, vb = (ya - y1) / F + 1, (yb - y1) / F + 1
            K.quad([P(ends[0], ya), P(ends[1], ya), P(ends[1], yb), P(ends[0], yb)], 'spbody', uv=[(0, va), (nt, va), (nt, vb), (0, vb)], sub=None if yb <= SHOW else 6.0)
        q(y0, floors_y[-1])
        for k in range(len(floors_y) - 1): q(floors_y[k + 1], floors_y[k])
        # chrome mullion fins on the bay lines (the texture's two panes a tile)
        bay = (a1 - a0) / (2 * nt)
        for k in range(1, 2 * nt):
            a = a0 + k * bay
            p0, p1 = P(a - 0.06, floors_y[-1], 0), P(a + 0.06, y1 - 1.6, 0.12)
            K.box(tuple(min(p0[i], p1[i]) for i in range(3)), tuple(max(p0[i], p1[i]) for i in range(3)), {'side': 'mullion', 'top': 'mullion', 'bottom': 'mullion'}, cull=False)
        # a few offices still lit: a pane a hair off the glass, from fin to fin
        for kf in range(1, len(floors_y) - 1):
            yt = floors_y[kf]
            for k in range(2 * nt):
                if rng.random() > 0.13: continue
                a = a0 + k * bay
                FL.both(K, [P(a + 0.06, yt - F + 0.05, 0.025), P(a + bay - 0.06, yt - F + 0.05, 0.025), P(a + bay - 0.06, yt - 0.62, 0.025), P(a + 0.06, yt - 0.62, 0.025)], 'lit' if rng.random() < 0.8 else 'litcool')
    # every fourth floor a cyan neon line along its spandrel (the tower glows in rings at dusk; not over the map's own
    # neon crown, 2.1-2.6 m under the roof)
    for k, yt in enumerate(floors_y[1:], 1):
        if k % 4 != 2: continue
        K.box((x0 - 0.03, yt - 0.34, z0 - 0.03), (x1 + 0.03, yt - 0.24, z1 + 0.03), {'side': 'neoncyan', 'top': None, 'bottom': None}, cull=False)
    corner_boards(K, (x1 - x0) / 2, (z1 - z0) / 2, SHOW, y1 - 1.6, 'mullion', w=0.7, p=0.16)
    # the cornice under the slab: a navy fascia with a chrome lip
    K.box((x0 - 0.18, y1 - 1.6, z0 - 0.18), (x1 + 0.18, y1 - 0.62, z1 + 0.18), {'side': 'spandrel', 'bottom': 'spandrel', 'top': None}, cull=False)
    K.box((x0 - 0.24, y1 - 0.62, z0 - 0.24), (x1 + 0.24, y1 - 0.5, z1 + 0.24), {'side': 'mullion', 'bottom': 'mullion', 'top': None}, cull=False)
    # ---- the roof slab and the deck's parapet
    for b in K.take(lambda b: b['mat'] == 'concrete' and b['max'][1] - b['min'][1] < 0.6 and b['max'][0] - b['min'][0] > 20):
        K.plain(b, {'top': 'tar', 'side': 'mullion', 'bottom': 'spandrel'}, sub=4.0)
    for b in K.take(lambda b: b['mat'] == 'concrete' and b['min'][1] >= -0.01):
        K.plain(b, {'side': 'concrete', 'top': None}, sub=2.0)
        cap(K, b, 'mullion', o=0.05)
        bx0, by0, bz0 = b['min']; bx1, by1, bz1 = b['max']
        if bx1 - bx0 >= bz1 - bz0:  # the neon line on the inside face (toward the shaft)
            zi = bz1 if abs(bz1) < abs(bz0) else bz0; s = 1 if zi == bz1 else -1
            K.box((bx0 + 0.05, 0.72, min(zi, zi + s * 0.03)), (bx1 - 0.05, 0.8, max(zi, zi + s * 0.03)), {'all': 'neoncyan'}, cull=False)
        else:
            xi = bx1 if abs(bx1) < abs(bx0) else bx0; s = 1 if xi == bx1 else -1
            K.box((min(xi, xi + s * 0.03), 0.72, bz0 + 0.05), (max(xi, xi + s * 0.03), 0.8, bz1 - 0.05), {'all': 'neoncyan'}, cull=False)

    # ---- the stairwell rails: glass balustrades with a chrome cap (a hair off the stringer below them, which shares their plane)
    for b in K.take(lambda b: b['mat'] == 'wood'):
        (rx0, ry0, rz0), (rx1, ry1, rz1) = b['min'], b['max']
        K.box((rx0 + 0.015, ry0, rz0), (rx1 - 0.015, ry1 - 0.06, rz1), {'side': 'railglass', 'top': None, 'bottom': None}, cull=False)
        K.box((rx0 - 0.01, ry1 - 0.06, rz0), (rx1 + 0.01, ry1, rz1), {'all': 'mullion'}, cull=False)
    # ---- the shaft: shell() dressed (walls in light glass, holes framed, grated floors and stairs)
    shaft_walls = [dict(b) for b in K.boxes if b['mat'] == 'glassblock' and not b.get('_done')]
    dress_shell(K, 12, 12, floors, F, 'spglass', intm='spint', floor='grate', roof='tar', cap='mullion', band='spandrel',
                course='spandrel', corners='mullion', wall_mat='glassblock')
    top = floors * F + 0.3 + 0.8  # the nest parapet's top
    # the side walls' tops under the roof slab overlap the front / back walls' at the corners (shell() overlaps them there):
    # pull the side walls' top faces back off the corner squares (all under the slab, never seen)
    for key, g in K.geo.items():
        if key[0] != 'trim': continue
        for f in g['f']:
            vs = [g['v'][i] for i in f]
            if any(abs(v[1] - floors * F) > 1e-3 for v in vs): continue
            xs = [v[0] for v in vs]; zs = [v[2] for v in vs]
            if max(xs) - min(xs) < 0.31 and min(abs(x) for x in xs) > 5.84 and max(zs) - min(zs) > 0.5:
                for i in f: v = g['v'][i]; g['v'][i] = (v[0], v[1], max(-5.85, min(5.85, v[2])))
    for key, g in K.geo.items():  # the shaft's glass: the body's curtain wall, its panes 3 m wide so the mullions land on the piers
        if key[0] == 'spglass': g['uv'] = [(u * F / 6.0, v) for (u, v) in g['uv']]
    # chrome mullions up the piers between the windows: the middle of every stretch of wall that's solid the whole height
    # of every storey above the ground floor (read off the wall boxes, so no mullion ever crosses a window or a door)
    for (axis, c, s) in (('x', -6.0, -1), ('x', 6.0, 1), ('z', -6.0, -1), ('z', 6.0, 1)):
        ia = 0 if axis == 'x' else 2; ic = 2 if axis == 'x' else 0
        wb = [b for b in shaft_walls if abs((b['min'][ic] + b['max'][ic]) / 2 - c) < 0.2]
        def solid(a):
            return all(any(b['min'][ia] <= a - 0.1 and b['max'][ia] >= a + 0.1 and b['min'][1] <= f * F + 0.3 and b['max'][1] >= (f + 1) * F - 0.05 for b in wb) for f in range(1, floors))
        run, runs = [], []
        for k in range(-56, 57):
            a = k * 0.1
            if solid(a): run.append(a)
            elif run: runs.append(run); run = []
        if run: runs.append(run)
        P = FL.WP(axis, c, s)
        for r_ in runs:
            if r_[0] < -5.5 or r_[-1] > 5.5: continue  # (the corners have their fins)
            a = (r_[0] + r_[-1]) / 2
            p0, p1 = P(a - 0.05, F + 0.1, 0.15), P(a + 0.05, floors * F + 0.3, 0.15 + 0.08)
            K.box(tuple(min(p0[i], p1[i]) for i in range(3)), tuple(max(p0[i], p1[i]) for i in range(3)), {'side': 'mullion', 'top': 'mullion', 'bottom': 'mullion'}, cull=False)
    # chrome fins up the shaft's corners, rising 3 m past the parapet and tapering to a point
    for sx in (-1, 1):
        for sz in (-1, 1):
            cx, cz = sx * 6.18, sz * 6.18
            a = (cx, 0.3, cz); b = (cx, top, cz)
            K.box((cx - 0.13, 0.3, cz - 0.13), (cx + 0.13, top, cz + 0.13), {'side': 'mullion', 'top': None, 'bottom': None}, cull=False)
            tip = (sx * 6.6, top + 3.2, sz * 6.6)
            c4 = [(cx - 0.13, top, cz - 0.13), (cx + 0.13, top, cz - 0.13), (cx + 0.13, top, cz + 0.13), (cx - 0.13, top, cz + 0.13)]
            for k in range(4): FL.tri2(K, [c4[k], c4[(k + 1) % 4], tip], 'mullion')
    # a neon line round the shaft under the nest's parapet
    for (mn, mx) in (((-6.06, top - 1.0, -6.06), (6.06, top - 0.92, -6.0)), ((-6.06, top - 1.0, 6.0), (6.06, top - 0.92, 6.06)),
                     ((-6.06, top - 1.0, -6.0), (-6.0, top - 0.92, 6.0)), ((6.0, top - 1.0, -6.0), (6.06, top - 0.92, 6.0))):
        K.box(mn, mx, {'all': 'neonpink'}, cull=False)

    # ---- the mast: aviation stripes in 2 m bands round the post, a flange, two service rings, antennas, beacon
    mx0, my0, mz0 = mast['min']; mx1, my1, mz1 = mast['max']
    h = my1 - my0; nb = max(1, round(h / 2.0)); bh = h / nb
    for k in range(nb):
        K.box((mx0 - 0.02, my0 + k * bh, mz0 - 0.02), (mx1 + 0.02, my0 + (k + 1) * bh, mz1 + 0.02),
              {'side': 'mastred' if k % 2 else 'mastwhite', 'top': 'steel' if k == nb - 1 else None, 'bottom': None}, cull=False)
    K.box((mx0 - 0.35, my0, mz0 - 0.35), (mx1 + 0.35, my0 + 0.25, mz1 + 0.35), {'all': 'steel', 'bottom': None}, cull=False)  # the flange
    for k in range(8):  # its bolts
        a = k * math.pi / 4; bx, bz = math.cos(a) * 0.55, math.sin(a) * 0.55
        K.box((bx - 0.05, my0 + 0.25, bz - 0.05), (bx + 0.05, my0 + 0.33, bz + 0.05), {'all': 'steel', 'bottom': None}, cull=False)
    for yr in (my0 + h * 0.36, my0 + h * 0.7):  # service rings: an octagon of grating on brackets, a rail round it
        ro, ri = 1.0, 0.34
        oo = [(math.cos((k + 0.5) * math.pi / 4) * ro / math.cos(math.pi / 8), math.sin((k + 0.5) * math.pi / 4) * ro / math.cos(math.pi / 8)) for k in range(8)]
        ii = [(math.cos((k + 0.5) * math.pi / 4) * ri / math.cos(math.pi / 8), math.sin((k + 0.5) * math.pi / 4) * ri / math.cos(math.pi / 8)) for k in range(8)]
        for k in range(8):
            k2 = (k + 1) % 8
            q = [(ii[k][0], yr, ii[k][1]), (ii[k2][0], yr, ii[k2][1]), (oo[k2][0], yr, oo[k2][1]), (oo[k][0], yr, oo[k][1])]
            FL.both(K, q, 'grate')
            FL.bar(K, (oo[k][0], yr + 0.9, oo[k][1]), (oo[k2][0], yr + 0.9, oo[k2][1]), 0.05 + 0.006 * (k % 2), 'steel')  # (alternate sizes: neighbours don't share a face at the corner)
            FL.bar(K, (oo[k][0] * 0.97, yr - 0.03, oo[k][1] * 0.97), (oo[k][0] * 0.97, yr + 0.9, oo[k][1] * 0.97), 0.04, 'steel')
            FL.bar(K, (ii[k][0] * 0.95, yr - 0.6, ii[k][1] * 0.95), (oo[k][0] * 0.9, yr - 0.02, oo[k][1] * 0.9), 0.05, 'steel')  # brackets
    for k, (dx, dz) in enumerate(((1, 0), (0, 1), (-1, 0), (0, -1))):  # panel antennas, staggered
        ya = my0 + h * (0.45 + 0.06 * (k % 2))
        cx, cz = dx * 0.48, dz * 0.48
        K.box((cx - (0.06 if dx else 0.2), ya, cz - (0.2 if dx else 0.06)), (cx + (0.06 if dx else 0.2), ya + 1.6, cz + (0.2 if dx else 0.06)), {'all': 'mastwhite'}, cull=False)
        FL.bar(K, (dx * 0.31, ya + 0.3, dz * 0.31), (cx, ya + 0.3, cz), 0.06, 'steel'); FL.bar(K, (dx * 0.31, ya + 1.3, dz * 0.31), (cx, ya + 1.3, cz), 0.06, 'steel')
    FL.dish(K, (0.62, my0 + h * 0.78, 0.0), (1, -0.15, 0.3), r=0.45)
    FL.dish(K, (-0.62, my0 + h * 0.6, 0.1), (-1, -0.1, -0.4), r=0.4)
    if id_ == 'spire':  # the pink halo (the map's neon ring, 1.2 m square): an octagon band round the post
        yc = my0 + 12.0
        R0 = 0.6 / math.cos(math.pi / 8)
        pts = [(math.cos((k + 0.5) * math.pi / 4) * R0, math.sin((k + 0.5) * math.pi / 4) * R0) for k in range(8)]
        for k in range(8):
            k2 = (k + 1) % 8
            FL.both(K, [(pts[k][0], yc - 0.15, pts[k][1]), (pts[k2][0], yc - 0.15, pts[k2][1]), (pts[k2][0], yc + 0.15, pts[k2][1]), (pts[k][0], yc + 0.15, pts[k][1])], 'neonpink')
            FL.both(K, [(pts[k][0], yc + 0.15, pts[k][1]), (pts[k2][0], yc + 0.15, pts[k2][1]), (pts[k2][0] * 0.55, yc + 0.15, pts[k2][1] * 0.55), (pts[k][0] * 0.55, yc + 0.15, pts[k][1] * 0.55)], 'neonpink')
    # the beacon: a glowing red lantern in a steel cage on top (the map's neonred box, 0.6 m)
    K.box((mx0 - 0.02, my1, mz0 - 0.02), (mx1 + 0.02, my1 + 0.62, mz1 + 0.02), {'all': 'beacon'}, cull=False)
    for (cx, cz) in ((mx0 - 0.06, mz0 - 0.06), (mx1 + 0.06, mz0 - 0.06), (mx0 - 0.06, mz1 + 0.06), (mx1 + 0.06, mz1 + 0.06)):
        FL.bar(K, (cx, my1, cz), (cx, my1 + 0.73, cz), 0.04, 'steel')  # (into the lid, not flush under it)
    K.box((mx0 - 0.1, my1 + 0.7, mz0 - 0.1), (mx1 + 0.1, my1 + 0.76, mz1 + 0.1), {'all': 'steel'}, cull=False)
    FL.bar(K, (0, my1 + 0.73, 0), (0, my1 + 2.2, 0), 0.04, 'steel')  # the lightning rod (from inside the lid)

    # no grime runs under the shaft's windows: it's glass (the kit adds them to every sill)
    for key in [k for k in K.geo if k[0] == 'decal']: del K.geo[key]
    left = [b for b in K.boxes if not b.get('_done')]
    for b in left:
        print('plain:', b['mat'], b['min'], b['max'])
        K.plain(b, {'all': 'grate'})
    K.finish(os.path.join(OUTDIR, id_ + '.glb'))


for id_ in ([a for a in argv if a in ('spire', 'spire_sd')] or ['spire', 'spire_sd']):
    build(id_)
