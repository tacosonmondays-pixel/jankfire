# Skyline's bridges from the Spire's deck out to the ring (shared/map.js tubeBridge() / skyBridge(), skyline()): drawn
# over their own boxes (tools/arch/dump.mjs), which stay what you walk on and hide behind.
#   tube   (north, south): a glass skywalk. a steel deck on a box-girder belly with lamps, glass walls held by steel
#          portal frames every 3.2 m (columns outside the glass, a beam over the roof), a dark metal roof with a chrome
#          fascia. The neon and lamps inside stay the map's.
#   girder (east, west): an open steel bridge. a grated deck with blue edges, slatted rail panels with a yellow cap
#          rail and posts, and under the deck two Warren trusses (chords, diagonals, cross-bracing) hanging below it.
#          The neon along the rails stays the map's.
# local frame: the bridge's middle; the tube runs along z, the girder along x (rot 0: the south / east one).
# run: node tools/arch/dump.mjs skyline tube tools/blender/arch/boxes/tube.json   (and girder)
#      blender52 -b --python tools/blender/arch/make_bridges.py -- [tube|girder]   (both by default)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST, cap

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'deck': ('metalplate', '#9ca2ac', {}), 'beam': ('metalplate', '#3060b8', {}), 'under': ('metalplate', '#2a2c32', {}),
    'tubeglass': ('glass', '#e2f2ff', {}), 'roofdark': ('metalplate', '#3a3e48', {}), 'chrome': ('metalplate', '#e4ecf4', {}),
    'mesh': ('louvre', '#c0c6d0', {}), 'handrail': ('trim', '#ffe14d', {}), 'lamp': ('stucco', '#ffd98a', {'glow': True}),
})
NOCAST.update({'mesh', 'handrail', 'lamp', 'chrome'})


def tube():
    K = Kit(os.path.join(HERE, 'boxes', 'tube.json'), seed=3); K.ground = -1e9
    deck = K.take(lambda b: b['mat'] == 'concrete')[0]
    roof = K.take(lambda b: b['mat'] == 'roofg')[0]
    walls = K.take(lambda b: b['mat'] == 'glassblock')
    (x0, yd0, z0), (x1, yd1, z1) = deck['min'], deck['max']
    yr0, yr1 = roof['min'][1], roof['max'][1]
    K.box(deck['min'], deck['max'], {'top': 'deck', 'side': 'beam', 'bottom': 'under'}, sub=4.0)
    for w in walls: K.box(w['min'], w['max'], {'side': 'tubeglass', 'top': None, 'bottom': None}, sub=None, cull=False)
    K.box(roof['min'], roof['max'], {'top': 'roofdark', 'side': 'chrome', 'bottom': 'roofdark'}, sub=4.0, cull=False)
    # the belly: a box girder under the deck, lamps along it
    K.box((x0 + 0.6, yd0 - 0.7, z0), (x1 - 0.6, yd0, z1), {'side': 'beam', 'bottom': 'under', 'top': None}, cull=False)
    n = int((z1 - z0) / 3.2)
    for k in range(n + 1):
        z = z0 + 0.3 + k * (z1 - z0 - 0.6) / n
        for s in (-1, 1):  # portal columns outside the glass, a beam over the roof
            xa, xb = (x1, x1 + 0.12) if s > 0 else (x0 - 0.12, x0)
            K.box((xa, yd0 - 0.1, z - 0.12), (xb, yr1 + 0.04, z + 0.12), {'all': 'beam'}, cull=False)
        K.box((x0 - 0.13, yr1, z - 0.11), (x1 + 0.13, yr1 + 0.12, z + 0.11), {'all': 'beam', 'bottom': None}, cull=False)  # (a hair slimmer than the columns: no shared faces)
        if k % 3 == 1: K.box((-0.3, yd0 - 0.82, z - 0.3), (0.3, yd0 - 0.7, z + 0.3), {'all': 'lamp'}, cull=False)
    K.finish(os.path.join(OUTDIR, 'tube.glb'))


def girder():
    K = Kit(os.path.join(HERE, 'boxes', 'girder.json'), seed=4); K.ground = -1e9
    deck = K.take(lambda b: b['mat'] == 'grid')[0]
    rails = K.take(lambda b: b['mat'] == 'metal')
    (x0, yd0, z0), (x1, yd1, z1) = deck['min'], deck['max']
    K.box(deck['min'], deck['max'], {'top': 'deck', 'side': 'beam', 'bottom': 'under'}, sub=4.0)
    for r in rails:
        K.box(r['min'], r['max'], {'side': 'mesh', 'top': None, 'bottom': None}, sub=None, cull=False)
        (rx0, ry0, rz0), (rx1, ry1, rz1) = r['min'], r['max']
        K.box((rx0, ry1, rz0 - 0.03), (rx1, ry1 + 0.08, rz1 + 0.03), {'all': 'handrail'}, cull=False)  # the cap rail
    n = int((x1 - x0) / 3.0)
    for k in range(n + 1):  # posts outside the panels
        x = x0 + 0.2 + k * (x1 - x0 - 0.4) / n
        for s in (-1, 1):
            za, zb = (z1, z1 + 0.08) if s > 0 else (z0 - 0.08, z0)
            K.box((x - 0.05, yd0, za), (x + 0.05, yd1 + 1.26, zb), {'all': 'beam'}, cull=False)  # (taller than the cap rail)
    # the Warren trusses under the deck: a bottom chord 2 m down, diagonals zig-zagging, cross-bracing between
    yb = yd0 - 2.0
    for s in (-1, 1):
        z = s * 1.7
        K.bar([(x0 + 0.3, yb, z), (x1 - 0.3, yb, z)], 0.18, 0.18, 'beam')
        K.bar([(x0 + 0.3, yd0 - 0.09, z), (x1 - 0.3, yd0 - 0.09, z)], 0.16, 0.16, 'beam')
        pts = [x0 + 0.3 + k * (x1 - x0 - 0.6) / n for k in range(n + 1)]
        for k in range(n):
            a, b = pts[k], pts[k + 1]
            if k % 2 == 0: K.bar([(a, yd0 - 0.17, z), (b, yb + 0.09, z)], 0.12, 0.12, 'beam')
            else: K.bar([(a, yb + 0.09, z), (b, yd0 - 0.17, z)], 0.12, 0.12, 'beam')
    for k in range(0, n + 1, 2):
        x = x0 + 0.3 + k * (x1 - x0 - 0.6) / n
        K.bar([(x, yb, -1.6), (x, yb, 1.6)], 0.1, 0.1, 'under')
        if k % 4 == 2: K.box((x - 0.25, yd0 - 0.32, -0.25), (x + 0.25, yd0 - 0.2, 0.25), {'all': 'lamp'}, cull=False)
    K.finish(os.path.join(OUTDIR, 'girder.glb'))


ids = [a for a in argv if a in ('tube', 'girder')] or ['tube', 'girder']
if 'tube' in ids: tube()
if 'girder' in ids: girder()
