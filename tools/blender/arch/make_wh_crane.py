# The gantry cranes on Warehouse (over the container yard) and Warehouse S&D (over site A): drawn over their own boxes
# (the two legs you bump into; the girder, trolley and hook were look-only boxes), which stay what they were. A rail-
# mounted gantry crane like the ones in real container yards, in safety orange: each leg a box column (exactly the
# game's leg) with hazard paint at the foot, a wheel bogie on a short run of rail with buffer stops, a ladder to a
# landing, then splitting into an A-frame above head height up to the portal beam; the main girder runs past both legs,
# with trolley rails on top, a railed walkway along one side, the company name, cable festoons hanging underneath and
# beacons on the ends; the trolley on top carries its winch house, the driver's cab hangs under it (lit), four ropes go
# down to a yellow lifting beam with hooks. local frame: the crane's middle (Warehouse 0,-36; S&D 44.5,-55.5).
# run: node tools/arch/dumpdeco.mjs warehouse wh_crane tools/blender/arch/boxes/wh_crane.json
#      node tools/arch/dumpdeco.mjs warehouse_sd wh_crane_sd tools/blender/arch/boxes/wh_crane_sd.json
#      blender52 -b --python tools/blender/arch/make_wh_crane.py -- [wh_crane|wh_crane_sd]   (both by default)
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'crorange': ('trim', '#ff7a1a', {}), 'crdark': ('metalplate', '#3a3e46', {}), 'crgrey': ('trim', '#9aa0a8', {}),
    'crhazy': ('trim', '#ffd400', {}), 'crhazk': ('trim', '#1c1c20', {}), 'crglass': ('glass', '#ffffff', {}), 'crlit': ('stucco', '#ffe0a0', {'glow': True}),
    'crbeacon': ('stucco', '#ffb030', {'glow': True}), 'crred': ('stucco', '#ff3030', {'glow': True, 'glowcol': '#ff3030'}),
    'crwalk': ('metalplate', '#8a9098', {}), 'crrail': ('metalplate', '#5a5e66', {}), 'crconc': ('concrete', '#c8c4bc', {}),
    'crrope': ('trim', '#2a2a30', {}), 'crcable': ('trim', '#1c1c22', {}),
})
NOCAST.update({'crdark', 'crgrey', 'crhazy', 'crhazk', 'crglass', 'crlit', 'crbeacon', 'crred', 'crrail', 'crconc', 'crrope', 'crcable'})
RAILS = {'wh_crane': (-8.0, 8.0), 'wh_crane_sd': (-2.2, 8.0)}  # local z the rails run (S&D: the yard fence is at -2.5)


def build(kind):
    d = json.load(open(os.path.join(HERE, 'boxes', kind + '.json')))
    deco = [b for b in d['boxes'] if b.get('deco')]
    d['boxes'] = [b for b in d['boxes'] if not b.get('deco')]
    K = Kit(d, seed=6)
    legs = sorted(K.boxes, key=lambda b: b['min'][0])
    gird = next(b for b in deco if b['mat'] == 'toyorange')
    trol = next(b for b in deco if b['mat'] == 'hazard')
    hook = next(b for b in deco if b['mat'] == 'metal')
    GY0, GY1 = gird['min'][1], gird['max'][1]
    GT = GY1 + 1.1  # the girder's top: a box girder 2 m deep (the game's look-only box was its bottom half)
    TX = (trol['min'][0] + trol['max'][0]) / 2
    rz0, rz1 = RAILS[kind]
    box = lambda mn, mx, m, cull=False: K.box(mn, mx, m if isinstance(m, dict) else {'all': m}, cull=cull)

    # ---- the legs
    for i, L in enumerate(legs):
        (x0, _, z0), (x1, y1, z1) = L['min'], L['max']
        x = (x0 + x1) / 2
        box((x0, 1.2, z0), (x1, 4.0, z1), {'all': 'crorange', 'bottom': None}, cull=True)  # the column (the game's leg)
        for k in range(6):  # hazard paint round the foot
            box((x0 - 0.004, k * 0.2, z0 - 0.004), (x1 + 0.004, k * 0.2 + 0.2, z1 + 0.004), {'all': 'crhazy' if k % 2 == 0 else 'crhazk', 'top': None if k < 5 else 'crhazk', 'bottom': None})
        # the bogie on its rails: a sill box, wheels, the rail and buffer stops
        box((x0 + 0.05, 0.12, -0.85), (x1 - 0.05, 0.62, 0.85), 'crdark')
        for zz in (-0.55, 0.55):
            FL.tube(K, (x0 + 0.1, 0.3, zz), (x1 - 0.1, 0.3, zz), 0.29, 0.29, 'crrail', n=10)
        box((x - 0.35, 0.0, rz0), (x + 0.35, 0.02, rz1), 'crconc')
        box((x - 0.04, 0.04, rz0), (x + 0.04, 0.1, rz1), {'all': 'crrail', 'bottom': None})
        box((x - 0.12, 0.02, rz0 + 0.01), (x + 0.12, 0.04, rz1 - 0.01), {'all': 'crrail', 'bottom': None})
        for zz, s in ((rz0, 1), (rz1, -1)):  # buffer stops over the rail ends
            box((x - 0.3, 0.02, min(zz - s * 0.02, zz + s * 0.3)), (x + 0.3, 0.5, max(zz - s * 0.02, zz + s * 0.3)), {'all': 'crhazy', 'top': 'crhazk', 'bottom': None})
        # a ladder up the outside face to a landing on the column's top
        out = -1 if x < 0 else 1
        fx = x1 if out > 0 else x0
        for zz in (-0.25, 0.25): FL.bar(K, (fx + out * 0.12, 0.6, zz), (fx + out * 0.12, 4.9, zz), 0.05, 'crgrey')
        for k in range(12): FL.bar(K, (fx + out * 0.12, 0.85 + k * 0.3, -0.25), (fx + out * 0.12, 0.85 + k * 0.3, 0.25), 0.03, 'crgrey')
        for zz in (-0.25, 0.25): FL.bar(K, (fx + out * 0.12, 1.2, zz), (fx + out * 0.02, 1.2, zz), 0.04, 'crgrey')
        box((x0 - 0.3, 4.0, z0 - 0.3), (x1 + 0.3, 4.12, z1 + 0.3), 'crwalk')  # the landing
        for (a, b) in (((x0 - 0.28, z0 - 0.28), (x1 + 0.28, z0 - 0.28)), ((x0 - 0.28, z1 + 0.28), (x1 + 0.28, z1 + 0.28)), ((x0 - 0.28, z0 - 0.28), (x0 - 0.28, z1 + 0.28)) if out < 0 else ((x1 + 0.28, z0 - 0.28), (x1 + 0.28, z1 + 0.28))):
            FL.bar(K, (a[0], 5.05 if a[1] == b[1] else 4.98, a[1]), (b[0], 5.05 if a[1] == b[1] else 4.98, b[1]), 0.04 if a[1] == b[1] else 0.032, 'crhazy')
        # the A-frame: two legs splaying out along the rails from the column's top to the portal beam
        for s in (-1, 1):
            FL.bar(K, (x, 4.05, s * 0.2), (x, GY0 - 0.4, s * 3.2), 0.55, 'crorange')
        box((x - 0.3, GY0 - 0.7, -3.6), (x + 0.3, GY0, 3.6), 'crorange')  # the portal beam
        FL.bar(K, (x, 6.4, -1.7), (x, 6.4, 1.7), 0.25, 'crorange')  # a tie across the A
        box((x - 0.31, GY0 - 0.71, -3.61), (x + 0.31, GY0 - 0.55, -3.0), 'crhazy'); box((x - 0.31, GY0 - 0.71, 3.0), (x + 0.31, GY0 - 0.55, 3.61), 'crhazy')

    # ---- the main girder, past both legs; trolley rails, a railed walkway, the name, festoons, beacons
    gx0, gx1 = legs[0]['min'][0] - 1.4, legs[-1]['max'][0] + 1.4
    box((gx0, GY0, -0.6), (gx1, GT, 0.6), {'all': 'crorange', 'nx': 'crhazy', 'px': 'crhazy'})
    for zz in (-0.42, 0.42): box((gx0 + 0.3, GT, zz - 0.05), (gx1 - 0.3, GT + 0.1, zz + 0.05), {'all': 'crrail', 'bottom': None})
    box((gx0, GY0 + 0.08, 0.6), (gx1, GY0 + 0.14, 1.45), 'crwalk')  # the walkway
    n = int((gx1 - gx0) / 1.5)
    for k in range(n + 1):
        xx = gx0 + 0.1 + k * (gx1 - gx0 - 0.2) / n
        FL.bar(K, (xx, GY0 + 0.15, 1.42), (xx, GY0 + 1.25, 1.42), 0.048, 'crhazy')
        FL.bar(K, (xx, GY0 + 0.06, 0.62), (xx, GY0 + 0.06, 1.4), 0.04, 'crdark')  # its brackets
    for y in (GY0 + 0.65, GY0 + 1.2): FL.bar(K, (gx0 + 0.1, y, 1.42), (gx1 - 0.1, y, 1.42), 0.04, 'crhazy')
    names = ((gx0 + gx1) / 2 - (gx1 - gx0) * 0.3, (gx0 + gx1) / 2 + (gx1 - gx0) * 0.3)
    for s in (-1, 1):
        for xa in names: K.decal_on('x', 0, s, 0.603, xa, (GY0 + GT) / 2, 'ad_jankcorp', w=3.4, h=1.7)
    xx = gx0 + 1.5
    while xx < gx1 - 1.0:  # stiffener ribs down the girder's sides (not over the names)
        if all(abs(xx - xa) > 1.9 for xa in names) and abs(xx - TX) > 1.8:
            for s in (-1, 1): box((xx - 0.05, GY0 + 0.12, min(s * 0.6, s * 0.64)), (xx + 0.05, GT - 0.12, max(s * 0.6, s * 0.64)), {'all': 'crorange', 'nz' if s > 0 else 'pz': None})
        xx += 3.0
    span = gx1 - gx0
    for k in range(6):  # cable festoons sagging under the girder
        xa = gx0 + 2.6 + k * (span - 5.2) / 6; xb = xa + (span - 5.2) / 6 * 0.8
        pts = [Vector((xa + (xb - xa) * t / 6, GY0 - 0.05 - 0.8 * math.sin(math.pi * t / 6), -0.45)) for t in range(7)]
        for p, q in zip(pts, pts[1:]): FL.bar(K, tuple(p), tuple(q), 0.05, 'crcable')
        box((xa - 0.1, GY0 - 0.12, -0.55), (xa + 0.1, GY0, -0.35), 'crdark')
    for xx in (gx0 + 0.3, gx1 - 0.3):
        FL.tube(K, (xx, GT + 0.06, 0.0), (xx, GT + 0.4, 0.0), 0.12, 0.12, 'crbeacon', n=8, caps=(False, True))
        box((xx - 0.18, GT, -0.18), (xx + 0.18, GT + 0.06, 0.18), {'all': 'crdark', 'bottom': None})
    FL.tube(K, ((gx0 + gx1) / 2, GT, -0.3), ((gx0 + gx1) / 2, GT + 0.22, -0.3), 0.09, 0.09, 'crred', n=8, caps=(False, True))

    # ---- the trolley: a winch house on top, the cab hung under it, ropes down to the lifting beam
    box((TX - 1.6, GT + 0.3, -0.9), (TX + 1.6, GT + 1.4, 0.9), {'all': 'crorange', 'top': 'crgrey'})
    for zz in (-0.42, 0.42):
        for xx in (TX - 1.2, TX + 1.2): FL.tube(K, (xx, GT + 0.24, zz - 0.12), (xx, GT + 0.24, zz + 0.12), 0.14, 0.14, 'crdark', n=8)
    FL.tube(K, (TX - 0.9, GT + 0.95, -0.95), (TX + 0.9, GT + 0.95, -0.95), 0.32, 0.32, 'crdark', n=10)  # the rope drum
    K.decal_on('x', 0, 1, 0.902, TX, GT + 0.85, 'sign_warn', w=0.6, h=0.6)
    cy0, cy1 = GY0 - 1.75, GY0 - 0.15
    box((TX + 0.2, GY0 - 0.15, 0.55), (TX + 1.7, GY0, 2.35), 'crdark')  # the cab's hanger
    box((TX + 0.3, cy0, 0.65), (TX + 1.6, cy1, 2.25), {'all': 'crorange', 'pz': 'crglass', 'bottom': 'crglass'})
    box((TX + 0.35, cy0 + 0.35, 2.25), (TX + 1.55, cy1 - 0.15, 2.26), 'crlit')  # the lamp inside, through the glass
    for xx in (TX - 0.7, TX + 0.7):
        for zz in (-0.35, 0.35): FL.bar(K, (xx, GY0 + 0.05, zz), (xx * 0.9 + TX * 0.1, hook['max'][1] + 0.05, zz * 0.85), 0.035, 'crrope')
    hy0, hy1 = hook['min'][1], hook['max'][1]
    box((TX - 1.5, hy1 - 0.35, -0.3), (TX + 1.5, hy1 + 0.1, 0.3), {'all': 'crhazy', 'top': 'crhazk'})  # the lifting beam
    for xx in (TX - 1.3, TX + 1.3):
        FL.bar(K, (xx, hy1 - 0.3, 0), (xx, hy0 + 0.2, 0), 0.05, 'crdark')
        FL.tube(K, (xx, hy0 + 0.22, -0.06), (xx, hy0 + 0.22, 0.06), 0.18, 0.18, 'crdark', n=8)  # hooks (round)
    FL.tube(K, (TX, hy1 + 0.1, 0), (TX, hy1 + 0.3, 0), 0.08, 0.08, 'crbeacon', n=8, caps=(False, True))
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in RAILS] or list(RAILS)):
    build(kind)
