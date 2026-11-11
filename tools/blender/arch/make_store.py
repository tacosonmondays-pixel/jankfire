# The Suburb's corner store (shared/map.js suburb(): an 18 x 12 brick shell()): KWIK-ISH, open 25/8. brick outside,
# sick-green lino inside, a tar roof behind a parapet with a steel cap, the stairs up to the roof done properly, every
# window framed (and broken, it's that kind of store), a neon OPEN, posters, a dumpster-side mural of graffiti
# run: blender52 -b --python tools/blender/arch/make_store.py -- [out.glb]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, dress_shell

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(OUTDIR, 'store.glb')
HERE = os.path.dirname(os.path.abspath(__file__))
K = Kit(os.path.join(HERE, 'boxes', 'store.json'), seed=7)
W, D, F = 18, 12, 4.2
dress_shell(K, W, D, 1, F, 'brick', intm='wallint2', floor='lino', roof='tar', cap='metal', band='concrete', course='concrete', corners='concrete', wall_mat='brick')
# the shop front (local -z): the name on a lightbox over the door, OPEN in neon, posters in the windows, stickers
K.decal_on('z', -9, -1, 0.17, 0, 2.9, 'sign_kwik', w=5.0, h=1.25, anchor='bottom', glow=True)  # (the front has the map's own sign)
K.decal_on('x', -6, -1, 0.17, -4.5, 2.45, 'neon_open', w=1.2, h=0.6, glow=True)
for a, cell in ((-8.4, 'poster_1'), (-4.0, 'ad_gristle'), (4.0, 'ad_teeth'), (8.4, 'sign_help')):
    K.decal_on('x', -6, -1, 0.17, a, 1.0 if cell.startswith('poster') else 0.55, cell, w=0.9 if cell.startswith('poster') else 1.2, h=1.3 if cell.startswith('poster') else 0.6, anchor='bottom')
for a in (1.3, 1.55, -1.4):
    K.decal_on('x', -6, -1, 0.17, a, 1.4 + (a > 0) * 0.3, 'sticker_%d' % int(abs(a * 10) % 4), w=0.2, h=0.2)
# the sides and the back: graffiti, an AC unit's drip, a big painted-on ad for JANKCORP, the electric meter and a vent
K.decal_on('z', 9, 1, 0.17, 2.0, 0.15, 'tag_0', w=2.6, h=1.3, anchor='bottom')
K.decal_on('z', 9, 1, 0.17, -2.5, 1.2, 'ad_jankcorp', w=4.0, h=2.0, anchor='bottom')
K.decal_on('z', -9, -1, 0.17, -3.0, 0.15, 'tag_2', w=2.0, h=1.0, anchor='bottom')
K.decal_on('z', -9, -1, 0.17, 4.0, 1.5, 'jbox', w=0.6, h=0.6)
K.decal_on('x', 6, 1, 0.17, -3.0, 1.2, 'meter', w=0.5, h=0.5)
K.decal_on('x', 6, 1, 0.17, 5.5, 2.8, 'vent', w=0.7, h=0.7)
K.decal_on('x', 6, 1, 0.17, 1.0, 0.15, 'tag_3', w=2.2, h=1.1, anchor='bottom')
for a in (-7.5, 0.5, 7.0): K.decal_on('x', -6, -1, 0.17, a, 4.15, 'grime_run', w=1.6, h=2.2, anchor='top')
for a in (-5.0, 3.0): K.decal_on('x', 6, 1, 0.17, a, 0.0, 'grime_mould', w=2.4, h=1.0, anchor='bottom')
# a wall-mounted AC box on the back, dripping (built onto the wall: shallow, nothing to stand on)
K.box((2.4, 2.9, 6.15), (3.4, 3.5, 6.55), {'all': 'metal'}, cull=False)
K.decal_on('x', 6.55, 1, 0.003, 2.9, 3.2, 'vent', w=0.8, h=0.5)
# a drainpipe at each back corner, off the roof
for x in (-8.7, 8.7):
    K.bar([(x, 0.15, 6.2), (x, F + 0.65, 6.2)], 0.1, 0.1, 'metaldark')
    K.bar([(x, F + 0.6, 6.2), (x, F + 0.6, 5.85)], 0.08, 0.08, 'metaldark')
# ---- shape: a stepped false front over the door with the name on it, a long striped awning over the shopfront, and
# the mascot: a giant slush cup on a bracket out over the pavement (too high and too far out to stand on)
PT = F + 0.65 + 0.06  # the parapet's cap
for (xa, xb, ya, yb) in ((-4.2, 4.2, 0, 0.9), (-2.6, 2.6, 0.9, 1.7)):
    FL.obox(K, (xa, PT + ya, -6.15), (xb, PT + yb, -5.9), {'side': 'brick', 'top': 'metal', 'bottom': None})
K.decal_on('x', -6.15, -1, 0.004, 0, PT + 0.42, 'sign_kwik', w=4.6, h=1.15, anchor='bottom', glow=True)
FL.awning(K, 'x', -6.15, -1, -8.6, 8.6, 3.35, depth=1.5, drop=0.6, mat='awning@roof', valance=0.22, stripe=0.6)
CX, CZ, CY = 7.4, -7.9, F + 1.1
FL.bar(K, (CX, CY - 0.1, -6.15), (CX, CY - 0.1, CZ), 0.14, 'metaldark'); FL.bar(K, (CX, CY - 0.1, CZ + 0.7), (CX, CY + 1.3, -6.15), 0.07, 'metaldark')
FL.tube(K, (CX, CY, CZ), (CX, CY + 1.9, CZ), 0.5, 0.78, 'cyan', n=10, caps=(True, False))
FL.tube(K, (CX, CY + 1.9, CZ), (CX, CY + 2.0, CZ), 0.82, 0.82, 'trim', n=10)
FL.tube(K, (CX, CY + 2.0, CZ), (CX, CY + 2.45, CZ), 0.74, 0.3, 'pink', n=10)  # the slush, heaped
FL.tube(K, (CX + 0.2, CY + 1.9, CZ), (CX + 0.75, CY + 3.3, CZ - 0.1), 0.07, 0.07, 'yellow', n=6)  # the straw
FL.tube(K, (CX, CY + 0.75, CZ), (CX, CY + 1.25, CZ), 0.6, 0.71, 'yellow', n=10, caps=(False, False))  # its band
# on the roof against the back parapet: a vent stack with a cowl, leaning
FL.tube(K, (-6.5, F + 0.3, 5.3), (-6.4, F + 1.9, 5.35), 0.16, 0.16, 'metal', n=8)
FL.tube(K, (-6.4, F + 1.9, 5.35), (-6.38, F + 2.15, 5.36), 0.3, 0.1, 'metaldark', n=8)
FL.aerial(K, (6.9, F + 0.72, 5.75), h=2.2, lean=(-0.1, 0.04), rungs=5)

left = [b for b in K.boxes if not b.get('_done')]
for b in left:
    print('plain:', b['mat'], b['min'], b['max'])
    K.plain(b, {'all': 'concrete'})
K.finish(OUT)
