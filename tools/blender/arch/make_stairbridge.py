# Skyline's stair bridges (shared/map.js stairBridge(), the eight between the ring towers and the corners): drawn over
# their own boxes (tools/arch/dump.mjs), which stay what you walk on. Each step (a 0.4 m slab) is a steel tread with a
# chequer-plate top and a blue-painted edge; two blue plate-girder stringers run under the steps' edges from tower to
# tower with a cyan neon line along them; the rails (a 1 m solid strip on each step) are slatted steel panels with a
# yellow safety handrail along the slope on posts every few steps; lamps hang under the steps.
#   stairhi: up 12 m from the ring (40) to the high corners (52); stairlo: down 10 m to the low corners (30)
# local frame: the bridge's middle, along +x from the low end at rot 0 (the map turns each placement).
# run: node tools/arch/dump.mjs skyline stairhi tools/blender/arch/boxes/stairhi.json   (and stairlo)
#      blender52 -b --python tools/blender/arch/make_stairbridge.py -- [stairhi|stairlo]   (both by default)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'tread': ('metalplate', '#a6aab2', {}), 'beam': ('metalplate', '#3060b8', {}), 'under': ('metalplate', '#2a2c32', {}),
    'mesh': ('louvre', '#c0c6d0', {}), 'handrail': ('trim', '#ffe14d', {}),
    'neoncyan': ('stucco', '#4fd8ff', {'glow': True}), 'lamp': ('stucco', '#ffd98a', {'glow': True}),
})
NOCAST.update({'mesh', 'handrail', 'neoncyan', 'lamp'})


def build(id_):
    K = Kit(os.path.join(HERE, 'boxes', id_ + '.json'), seed=5)
    K.ground = -1e9
    steps = sorted(K.take(lambda b: b['mat'] == 'concrete'), key=lambda b: b['min'][0])
    rails = K.take(lambda b: b['mat'] == 'metal')
    up = steps[-1]['max'][1] > steps[0]['max'][1]
    if not up: steps = steps[::-1]  # low -> high
    hw = steps[0]['max'][2]  # half width (2 m)
    # ---- the treads: each slab a steel step, chequer plate on top, painted edges, dark underneath
    for b in steps:
        K.box(b['min'], b['max'], {'top': 'tread', 'side': 'beam', 'bottom': 'under'}, sub=None, cull=False)
    # the nosing line: the low step's back-bottom corner to the high step's top front
    lo, hi = steps[0], steps[-1]
    xl = lo['min'][0] if hi['max'][0] > lo['max'][0] else lo['max'][0]
    xh = hi['max'][0] if hi['max'][0] > lo['max'][0] else hi['min'][0]
    yl, yh = lo['max'][1], hi['max'][1]
    line = lambda x: yl + (yh - yl) * (x - xl) / (xh - xl)
    # ---- the stringers: a plate girder under each edge, the neon along it, lamps under the middle
    for s in (-1, 1):
        o0, o1 = (hw, hw + 0.16) if s > 0 else (-hw - 0.16, -hw)
        poly = [(xl, line(xl) + 0.04, 0), (xh, line(xh) + 0.04, 0), (xh, line(xh) - 0.7, 0), (xl, line(xl) - 0.7, 0)]
        K.prism(poly, 2, o0, o1, 'beam')
        zz = s * (hw + 0.17)
        K.bar([(xl + 0.2, line(xl + 0.2) - 0.3, zz), (xh - 0.2, line(xh - 0.2) - 0.3, zz)], 0.05, 0.05, 'neoncyan')
    n = len(steps)
    for k in range(2, n - 1, 5):  # lamps under the steps
        b = steps[k]; cx = (b['min'][0] + b['max'][0]) / 2
        K.box((cx - 0.25, b['min'][1] - 0.12, -0.25), (cx + 0.25, b['min'][1], 0.25), {'all': 'lamp'}, cull=False)
    # ---- the rails: each step's strip a slatted panel, capped; posts every few steps; the handrail along the slope
    for b in rails:
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        K.box((x0, y0, z0), (x1, y1, z1), {'side': 'mesh', 'top': 'beam', 'bottom': None}, sub=None, cull=False)
    for k in range(0, n, 3):
        b = steps[k]; x = b['min'][0] if up else b['max'][0]
        for s in (-1, 1):
            z0, z1 = (hw, hw + 0.08) if s > 0 else (-hw - 0.08, -hw)
            K.box((x - 0.04, b['max'][1] - 0.02, z0), (x + 0.04, b['max'][1] + 1.12, z1), {'all': 'handrail'}, cull=False)
    xe = hi['max'][0] if hi['max'][0] > lo['max'][0] else hi['min'][0]
    for s in (-1, 1):
        zz = s * (hw + 0.04)
        K.bar([(xl, line(xl) + 1.1, zz), (xh, line(xh) + 1.1, zz)], 0.1, 0.06, 'handrail')  # (wider than the posts: no shared faces)
    left = [b for b in K.boxes if not b.get('_done')]
    for b in left:
        print('plain:', b['mat'], b['min'], b['max'])
        K.plain(b, {'all': 'tread'})
    K.finish(os.path.join(OUTDIR, id_ + '.glb'))


for id_ in ([a for a in argv if a in ('stairhi', 'stairlo')] or ['stairhi', 'stairlo']):
    build(id_)
