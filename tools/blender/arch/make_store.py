# The Suburb's corner store (shared/map.js suburb(): an 18 x 12 brick shell()): KWIK-ISH, open 25/8. brick outside,
# sick-green lino inside, a tar roof behind a parapet with a steel cap, the stairs up to the roof done properly, every
# window framed (and broken, it's that kind of store), a neon OPEN, posters, a dumpster-side mural of graffiti
# run: blender52 -b --python tools/blender/arch/make_store.py -- [out.glb]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
left = [b for b in K.boxes if not b.get('_done')]
for b in left:
    print('plain:', b['mat'], b['min'], b['max'])
    K.plain(b, {'all': 'concrete'})
K.finish(OUT)
