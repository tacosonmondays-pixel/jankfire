# The Desert's adobe hut (shared/map.js adobeHut(): a 6 x 5 one-room shell() with a parapet and a ladder up the side):
# mud plaster in the hut's own paint, thick buttressed corners, a paler cap on the parapet, roof beams (vigas) poking out
# front and back, wooden frames, rain spouts with their stains down the west wall, a string of chillies by the door, the
# ladder as a ladder. variants (the game picks one per hut): a water pot by the door / a blanket airing on the parapet /
# firewood stacked against the wall. look only: the boxes are the hut you bump into.
# run: blender52 -b --python tools/blender/arch/make_adobe.py -- [out.glb]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST, dress_shell

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(OUTDIR, 'adobe.glb')
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({'adobe@siding': ('stucco', '#ffffff', {}), 'adobecap': ('stucco', '#f0dcb8', {}), 'adobeband': ('stucco', '#a07c54', {}), 'adoberoof': ('stucco', '#c09868', {}),
             'log': ('planks', '#7a4e2c', {}), 'trim': ('planks', '#8e6038', {}), 'chili': ('trim', '#d02a1c', {})})  # (this model's frames are wood)
NOCAST.update({'log', 'chili'})
K = Kit(os.path.join(HERE, 'boxes', 'adobe.json'), seed=11)
W, D, F = 6, 5, 3.2
for b in K.boxes:  # the walls and the roof slab share a map material (the hut's paint): tell them apart by shape
    if b['mat'] != 'wood': b['mat'] = 'slab' if b['max'][1] - b['min'][1] <= 0.31 else 'wall'
dress_shell(K, W, D, 1, F, 'adobe@siding', intm='wallint', floor='floorwood', roof='adoberoof', cap='adobecap', band='adobeband', course='adobe@siding', corners='adobe@siding', wall_mat='wall')
# the ladder (+x side): its rails and rungs as timber
for b in [b for b in K.boxes if not b.get('_done')]:
    if b['min'][0] > 3.1:
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']; b['_done'] = True
        if y1 - y0 > 1: K.box((x0 + 0.04, y0, z0), (x1 - 0.04, y1, z1), {'all': 'log'}, cull=False)  # a rail: a plank on edge
        else: K.box((x0 + 0.01, y0 + 0.004, z0), (x1 - 0.01, y1 - 0.003, z1), {'all': 'log'}, cull=False)  # a rung (its top is the step's, a hair under: the window's frame is level with one)
# vigas: the roof beams' ends, out through the wall front and back (above head height)
for k in range(6):
    x = -2.25 + k * 0.9
    FL.tube(K, (x, 2.92, -2.6), (x + 0.01 * (k % 3 - 1), 2.9, -3.08 - 0.05 * (k % 2)), 0.085, 0.075, 'log', n=6)
    FL.tube(K, (x, 2.92, 2.6), (x, 2.9, 3.02 + 0.06 * ((k + 1) % 2)), 0.085, 0.075, 'log', n=6)
# canales: two rain spouts through the west parapet, a stain under each
for z in (-1.2, 1.3):
    K.box((-3.52, 3.53, z - 0.09), (-3.1, 3.62, z + 0.09), {'all': 'log'}, cull=False)
    K.decal_on('z', -3, -1, 0.1515, z, 3.14, 'grime_run', w=0.8, h=1.9, anchor='top')
K.decal_on('x', -2.5, -1, 0.1515, -2.1, 0.5, 'grime_crack', w=1.2, h=1.2, anchor='bottom')
K.decal_on('x', 2.5, 1, 0.1515, 1.9, 1.3, 'grime_crack', w=1.0, h=1.0, anchor='bottom')
K.decal_on('x', 2.5, 1, 0.1515, -1.8, 0.31, 'grime_mould', w=1.6, h=0.7, anchor='bottom')
# a string of chillies on a peg by the door
FL.tube(K, (1.32, 2.32, -2.66), (1.32, 2.32, -2.8), 0.02, 0.02, 'log', n=4)
FL.tube(K, (1.32, 2.3, -2.76), (1.32, 1.95, -2.76), 0.05, 0.085, 'chili', n=6)
FL.tube(K, (1.32, 1.95, -2.76), (1.33, 1.5, -2.75), 0.085, 0.02, 'chili', n=6)
# v0: a water pot by the door
P0 = (-1.75, -3.05)
for (ya, yb, ra, rb) in ((0.0, 0.16, 0.11, 0.24), (0.16, 0.36, 0.24, 0.2), (0.36, 0.45, 0.2, 0.1), (0.45, 0.5, 0.1, 0.13)):
    FL.tube(K, (P0[0], ya, P0[1]), (P0[0], yb, P0[1]), ra, rb, 'terracotta', n=8, caps=(ya == 0.0, yb == 0.5), node='v0')
# v1: a striped blanket airing over the front parapet
FL.obox(K, (1.1, 3.5, -2.69), (2.2, 4.375, -2.655), {'side': 'pink', 'top': 'pink', 'bottom': 'pink'}, node='v1')
FL.obox(K, (1.105, 4.368, -2.685), (2.195, 4.385, -2.25), {'side': 'pink', 'top': 'pink', 'bottom': None}, node='v1')
for (y, m) in ((3.62, 'yellow'), (3.84, 'cyan'), (4.06, 'yellow')):
    FL.obox(K, (1.095, y, -2.697), (2.205, y + 0.09, -2.65), {'side': m, 'top': m, 'bottom': m}, node='v1')
# v2: firewood stacked against the west wall
for k, (z, y) in enumerate(((-0.6, 0.09), (-0.4, 0.09), (-0.2, 0.09), (0.0, 0.09), (-0.5, 0.25), (-0.3, 0.25), (-0.1, 0.25), (-0.4, 0.41))):
    FL.tube(K, (-3.2, y, z), (-3.95 - 0.04 * (k % 3), y, z + 0.02 * (k % 2)), 0.09, 0.085, 'log', n=6, node='v2')

for b in [b for b in K.boxes if not b.get('_done')]:
    print('plain:', b['mat'], b['min'], b['max'])
    K.plain(b, {'all': 'adobe@siding'})
K.finish(OUT)
