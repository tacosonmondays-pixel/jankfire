# The shut show home (shared/map.js facadeHouse(): Suburb S&D's houses you can't go into), drawn over its own boxes, which
# stay what you bump into: the same house as make_home.py from the street (lap siding in the house's paint, a foundation
# band, a string course, corner boards, the fascia, the hip roof over its curb, the brick chimney, the porch, the brick
# garage) but every window has its blinds down or its curtains drawn, the front door is shut (panel door, brass knob, mail
# slot), the roller door is down, a FOR SALE board hangs off the porch and another is taped in an upstairs window.
# The map's neon OPEN HOUSE sign over the door stays the game's own (it's lit).
# run: node tools/arch/dump.mjs suburb_sd home_shut tools/blender/arch/boxes/home_shut.json
#      blender52 -b --python tools/blender/arch/make_home_shut.py -- [out.glb]
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archkit import Kit, OUTDIR, MATS, NOCAST, corner_boards
import flair as FL
import hiproof as HR

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(OUTDIR, 'home_shut.glb')
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({'blind': ('louvre', '#f2ead6', {}), 'blind2': ('louvre', '#ffe7a8', {}), 'curtain': ('stucco', '#ff8ac8', {}), 'curtain2': ('stucco', '#8ad8ff', {}),
             'curtain3': ('stucco', '#c8ff8a', {}), 'pane': ('glass', '#ffffff', {})})
NOCAST.update({'blind', 'blind2', 'curtain', 'curtain2', 'curtain3', 'pane'})
K = Kit(os.path.join(HERE, 'boxes', 'home_shut.json'), seed=21)
R = random.Random(5)
F = 3.4
eq = lambda a, b: abs(a - b) < 1e-3

# ---- the body: siding all round (its top is under the roof), bands, corner boards, drainpipes
body = K.take(lambda b: b['mat'].startswith('side') or b['mat'] in ('blue',))[0]
K.plain(body, {'side': 'siding@siding', 'top': None, 'bottom': None}, sub=1.6)
for (y0, y1, m) in ((0.0, 0.32, 'concrete'), (F - 0.02, F + 0.2, 'trim'), (2 * F - 0.25, 2 * F, 'trim')):
    o = 0.03
    K.box((-7 - o, y0, -6 - o), (7 + o, y1, -6), {'all': m}, cull=False); K.box((-7 - o, y0, 6), (7 + o, y1, 6 + o), {'all': m}, cull=False)
    K.box((-7 - o, y0, -6), (-7, y1, 6), {'all': m}, cull=False); K.box((7, y0, 1.2 if y0 < 3.2 else -6), (7 + o, y1, 6), {'all': m}, cull=False)  # (the garage covers the east side's front)
corner_boards(K, 7.0, 6.0, 0.32, 2 * F - 0.25, 'trim')
for x in (-6.75, 6.75):
    K.bar([(x, 0.15, 6.12), (x, 2 * F - 0.1, 6.12)], 0.09, 0.09, 'metal')
    K.bar([(x, 0.15, 6.17), (x, 0.15, 6.4)], 0.09, 0.09, 'metal')


# ---- the windows: the map's painted ones (facadeHouse), every one shut: blinds or curtains, casing, a sill, shutters
def window(axis, c, s, a, y, shut, front_back, k):
    a0, a1, y0, y1 = a - 0.75, a + 0.75, y, y + 1.2
    cw, cd = 0.09, 0.035
    if shut.startswith('blind'):
        K.wbox(axis, c, a0, a1, y0, y1, 0, s * 0.01, {'all': shut}, cull=False)
    else:  # drawn curtains, a crack of dark glass where they meet, a valance over them
        K.wbox(axis, c, a0, a1, y0, y1, 0, s * 0.006, {'all': 'pane'}, cull=False)
        gap = 0.04 + 0.08 * R.random()
        K.wbox(axis, c, a0, (a0 + a1) / 2 - gap / 2, y0, y1 - 0.12, s * 0.006, s * 0.014, {'all': shut}, cull=False)
        K.wbox(axis, c, (a0 + a1) / 2 + gap / 2, a1, y0, y1 - 0.12, s * 0.006, s * 0.014, {'all': shut}, cull=False)
        K.wbox(axis, c, a0, a1, y1 - 0.12, y1, s * 0.006, s * 0.016, {'all': shut}, cull=False)
    K.wbox(axis, c, a0 - cw, a0, y0 - 0.02, y1 + cw, 0, s * cd, {'all': 'trim'}, cull=False)
    K.wbox(axis, c, a1, a1 + cw, y0 - 0.02, y1 + cw, 0, s * cd, {'all': 'trim'}, cull=False)
    K.wbox(axis, c, a0 - cw - 0.02, a1 + cw + 0.02, y1, y1 + cw + 0.03, 0, s * (cd + 0.02), {'all': 'trim'}, cull=False)
    K.wbox(axis, c, a0 - cw - 0.04, a1 + cw + 0.04, y0 - 0.05, y0, 0, s * 0.09, {'all': 'trim'}, cull=False)
    K.wbox(axis, c, (a0 + a1) / 2 - 0.02, (a0 + a1) / 2 + 0.02, y0, y1, s * 0.01, s * 0.022, {'all': 'trim'}, cull=False) if shut.startswith('blind') else None
    if front_back:  # shutters, in the roof's colour
        for sd in (-1, 1):
            aa = a0 - 0.09 - 0.44 if sd < 0 else a1 + 0.09
            K.wbox(axis, c, aa, aa + 0.44, y0 - 0.02, y1 + 0.05, 0, s * 0.048, {'all': 'shutter@roof', ('pz' if s > 0 else 'nz') if axis == 'x' else ('px' if s > 0 else 'nx'): 'louvre@roof'}, cull=False)
    if R.random() < 0.45: K.decal_on(axis, c, s, 0.004, a, y0 - 0.06, 'grime_run', w=1.3, h=min(1.0, y0 - 0.1), anchor='top')

SHUT = ['blind', 'blind', 'curtain', 'blind2', 'curtain2', 'blind', 'curtain3', 'blind2']
k = 0
for (c, s) in ((-6.0, -1), (6.0, 1)):  # front, back
    for y in (1.1, 4.5):
        for x in (-5, -2.2, 2.2, 5):
            if y < 2 and abs(x) < 3: continue
            window('x', c, s, x, y, SHUT[k % len(SHUT)], True, k); k += 1
            if y < 2: FL.flowerbox(K, 'x', c, s, x - 0.8, x + 0.8, y - 0.08, seed=k)
for (c, s) in ((-7.0, -1), (7.0, 1)):  # the sides
    for y in (1.1, 4.5):
        for z in (-3, 3):
            window('z', c, s, z, y, SHUT[(k + 3) % len(SHUT)], False, k); k += 1
# a FOR SALE board taped inside an upstairs front window
K.decal_on('x', -6.0, -1, 0.02, 2.2, 5.05, 'sign_sale', w=0.9, h=0.6)

# ---- the front door, shut: a panel door in a casing, a brass knob, a mail slot, a doorbell, a mat
K.wbox('x', -6.0, -1.0, 1.0, 0.25, 2.6, 0, -0.045, {'all': 'door'}, cull=False)
for (a0, a1, y0, y1) in ((-0.8, -0.08, 0.45, 1.35), (0.08, 0.8, 0.45, 1.35), (-0.8, -0.08, 1.55, 2.4), (0.08, 0.8, 1.55, 2.4)):
    K.wbox('x', -6.0, a0, a1, y0, y1, -0.045, -0.06, {'all': 'door'}, cull=False)  # its raised panels
for (a0, a1, y0, y1) in ((-1.1, -1.0, 0.25, 2.6), (1.0, 1.1, 0.25, 2.6), (-1.12, 1.12, 2.6, 2.7)):  # (the jambs stop under the head)
    K.wbox('x', -6.0, a0, a1, y0, y1, 0, -0.05, {'all': 'trim'}, cull=False)
K.wbox('x', -6.0, 0.62, 0.72, 1.3, 1.4, -0.06, -0.11, {'all': 'brass'}, cull=False)
K.wbox('x', -6.0, -0.25, 0.25, 1.42, 1.5, -0.06, -0.075, {'all': 'brass'}, cull=False)
K.wbox('x', -6.0, 1.22, 1.32, 1.3, 1.42, 0, -0.03, {'all': 'brass'}, cull=False)
K.box((-0.8, 0.25, -7.2), (0.8, 0.27, -6.3), {'all': 'rubber'}, cull=False)

# ---- the porch: decking, posts with a base and a cap, its roof, a little gable over it, the FOR SALE board on chains
for b in K.take(lambda b: b['mat'] == 'wood' and eq(b['min'][1], 0) and eq(b['max'][1], 0.25)):
    K.plain(b, {'top': 'floorwood', 'side': 'trim', 'bottom': None}, sub=1.2)
for b in K.take(lambda b: b['mat'] == 'wood' and eq(b['min'][1], 0.25) and eq(b['max'][1], 3.0)):
    K.plain(b, {'all': 'trim'})
    x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
    for (ya, yb) in ((y0, y0 + 0.25), (y1 - 0.18, y1)):
        K.box((x0 - 0.04, ya, z0 - 0.04), (x1 + 0.04, yb, z1 + 0.04), {'all': 'trim'}, cull=False)
for b in K.take(lambda b: b['mat'].startswith('roof') and eq(b['min'][1], 3.0)):
    K.plain(b, {'top': 'shingle@roof', 'bottom': 'ceiling', 'side': 'trim'})
FL.gable(K, 'x', -7.8, -1, -2.5, 2.5, 3.25, 0.95, 0.12, 'siding@siding', props=False)
for x in (1.15, 2.05):
    FL.bar(K, (x, 3.03, -7.6), (x, 2.6, -7.6), 0.02, 'metaldark')  # (its ends into the roof and the board)
FL.obox(K, (1.0, 2.1, -7.62), (2.2, 2.62, -7.58), 'trim')
K.decal_on('x', -7.6, -1, 0.025, 1.6, 2.36, 'sign_sale', w=1.1, h=0.46)

# ---- the garage: brick, the roller door down, a tar roof with a metal edge
for b in K.take(lambda b: b['mat'] == 'brick' and eq(b['min'][1], 0)):
    K.plain(b, {'side': 'brick', 'top': None, 'bottom': None}, sub=1.6)
K.wbox('x', -6.0, 7.6, 12.4, 0.1, 2.7, 0, -0.04, {'all': 'corrugated'}, cull=False)
K.wbox('x', -6.0, 7.45, 7.6, 0.0, 2.7, 0, -0.06, {'all': 'metal'}, cull=False); K.wbox('x', -6.0, 12.4, 12.55, 0.0, 2.7, 0, -0.06, {'all': 'metal'}, cull=False)
K.wbox('x', -6.0, 7.45, 12.55, 2.7, 2.85, 0, -0.06, {'all': 'metal'}, cull=False)
K.wbox('x', -6.0, 9.6, 10.4, 0.42, 0.5, -0.04, -0.07, {'all': 'metaldark'}, cull=False)  # its handle
for b in K.take(lambda b: b['mat'] == 'roofg' and eq(b['min'][1], 3.2)):
    K.plain(b, {'top': 'tar', 'bottom': 'corrugated', 'side': 'metal'})
K.decal_on('x', -6.0, -1, 0.045, 10.0, 0.25, 'tag_2', w=2.0, h=1.0, anchor='bottom')

# ---- the roof: the eave slab (shingles round the curb, a fascia, a soffit), the curb, the hip roof, the chimney
for b in K.take(lambda b: b['mat'].startswith('roof') and eq(b['min'][1], 2 * F) and b['max'][0] - b['min'][0] > 14):
    K.plain(b, {'top': 'shingle@roof', 'bottom': 'ceiling', 'side': 'trim'}, sub=1.5)
for b in K.take(lambda b: b['mat'].startswith('roof') and eq(b['min'][1], 2 * F + 0.3) and b['max'][0] - b['min'][0] > 12):
    K.plain(b, {'side': 'trimdark', 'top': None, 'bottom': None}, sub=1.5)
K.take(lambda b: b['mat'].startswith('roof') and b['min'][1] >= 2 * F + 0.74)
HR.hip_roof(K, 2 * F + 0.75)
for b in K.take(lambda b: b['mat'] == 'brick' and b['min'][1] > 2 * F):
    K.plain(b, {'all': 'brick'}, sub=0.8)
    x0, y0, z0 = b['min']; x1, y1, z1 = b['max']
    K.box((x0 - 0.08, y1, z0 - 0.08), (x1 + 0.08, y1 + 0.12, z1 + 0.08), {'all': 'concrete'}, cull=False)
FL.tube(K, (4.05, 9.535, 2.15), (4.05, 9.98, 2.15), 0.17, 0.12, 'terracotta', n=8)
FL.aerial(K, (3.55, 9.53, 1.65), h=1.7, lean=(-0.1, 0.08))

# ---- grime and bits: a meter, a dryer vent, mould by the ground, runs under the eaves, a poster on the garage side
K.decal_on('z', 7.0, 1, 0.004, -3.5, 1.3, 'meter', w=0.45, h=0.45)
K.decal_on('z', -7.0, -1, 0.004, -4.6, 0.5, 'dryer', w=0.35, h=0.35)
K.decal_on('z', -7.0, -1, 0.004, 0.0, 0.0, 'grime_mould', w=2.2, h=1.1, anchor='bottom')
K.decal_on('x', 6.0, 1, 0.004, -3.0, 0.0, 'grime_mould', w=2.6, h=1.2, anchor='bottom')
K.decal_on('x', -6.0, -1, 0.004, -5.6, 6.5, 'grime_run', w=1.2, h=1.8, anchor='top')
K.decal_on('z', 13.0, 1, 0.004, -2.4, 1.6, 'poster_3', w=0.6, h=0.9)

left = [b for b in K.boxes if not b.get('_done')]
for b in left:
    print('plain:', b['mat'], b['min'], b['max'])
    K.plain(b, {'all': 'trim'})
K.finish(OUT)
