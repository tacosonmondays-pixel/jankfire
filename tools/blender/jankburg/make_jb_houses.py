# Jankburg's city houses (shared/jankburg.js cityHouse(): twelve kinds, every lot of a kind the same size now), one
# Blender building per kind over its own boxes (the shell() rooms and stairs, the upper floors, the roofs), for
# public/js/archfield.js like the Suburb's houses: the arch kit's textures, walls built round their real openings
# (frames, sills, broken panes), real stairs, floors and ceilings, vertex AO. Painted kinds take each lot's paint
# (their '@siding' / '@roof' parts). The lots' furniture, signs, awnings and AC stay the map's.
#   capsule3/4  white stucco pods under an office-window block        noodle / bodega / pawn  painted siding shop + a brick flat
#   walkup      painted siding ground floor, brick walk-up above      model   painted siding two-storey, a stepped shingle roof
#   container   two shipping containers (corrugated, painted)         squat   plank walls, a plank flat above (graffiti)
#   dorm        concrete lobby, five storeys of office windows        arcade  painted stucco + a brick flat
#   pastel      painted siding two-storey, a stepped shingle roof     biolab  glass ground floor, a glass block above
# needs tools/blender/jankburg/houses/<id>.json (node tools/arch/dump.mjs, see README): one per kind
# run: blender52 -b --python tools/blender/jankburg/make_jb_houses.py -- [--only=jbh_dorm,...]
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'arch'))
import archkit
from archkit import Kit, OUTDIR, dress_shell, cap

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ONLY = set(next((a.split('=', 1)[1] for a in argv if a.startswith('--only=')), '').split(',')) - {''}
# kit materials the city needs that the Suburb didn't (painted stucco and corrugated, the glass office facade)
archkit.MATS.update({'stucco@siding': ('stucco', '#ffffff', {}), 'corrugated@siding': ('corrugated', '#ffffff', {}),
                     'fac_glass': ('fac_glass', '#ffffff', {}), 'planks': ('planks', '#c8b8a0', {})})
F = 3.4
LOT = {'capsule': (9, 9), 'noodle': (12, 11), 'bodega': (11, 11), 'walkup': (8, 12), 'model': (13, 11), 'container': (6, 12), 'squat': (10, 11),
       'dorm': (16, 13), 'arcade': (13, 12), 'pastel': (12, 10), 'biolab': (12, 11), 'pawn': (13, 12)}
# kind: (shell floors, storey, walls (ext), the shell boxes' material key, upper facade, inside, floor, roof)
KINDS = {
    'capsule': (1, F, 'stucco@siding', 'white', 'fac_office', 'wallint2', 'lino', 'tar'),
    'noodle': (1, F, 'siding@siding', None, 'fac_tenement', 'wallint', 'lino', 'tar'),
    'bodega': (1, F, 'siding@siding', None, 'fac_tenement', 'wallint2', 'lino', 'tar'),
    'walkup': (1, F, 'siding@siding', None, 'fac_tenement', 'wallint', 'floorwood', 'tar'),
    'model': (2, F, 'siding@siding', None, None, 'wallint', 'carpet', 'shingle@roof'),
    'container': (2, 2.9, 'corrugated@siding', None, None, 'metal', 'metal', 'metal'),
    'squat': (1, F, 'planks', 'graffiti', 'fac_tenement', 'wallint2', 'floorwood', 'tar'),
    'dorm': (1, F, 'concrete', 'office', 'fac_office', 'wallint2', 'carpet', 'tar'),
    'arcade': (1, F, 'stucco@siding', None, 'fac_tenement', 'wallint', 'carpet', 'tar'),
    'pastel': (2, F, 'siding@siding', None, None, 'wallint', 'floorwood', 'shingle@roof'),
    'biolab': (1, F, 'glass', 'glass', 'fac_glass', 'wallint2', 'lino', 'tar'),
    'pawn': (1, F, 'siding@siding', None, 'fac_tenement', 'wallint', 'concrete', 'tar'),
}


def build(hid):
    kind = hid[4:].rstrip('34')
    floors, f, ext, wall_mat, fac, intm, floor, roof = KINDS[kind]
    w, d = LOT[kind]
    K = Kit(os.path.join(HERE, 'houses', hid + '.json'), seed=len(hid) * 7)
    if wall_mat is None:  # (painted kinds: the walls are whatever paint the first lot got: the commonest wall-thick box)
        from collections import Counter
        thin = lambda b: min(b['max'][0] - b['min'][0], b['max'][2] - b['min'][2]) < 0.31 and b['min'][1] < 0.1 and b['max'][1] - b['min'][1] > 1.0
        wall_mat = Counter(b['mat'] for b in K.boxes if thin(b)).most_common(1)[0][0]
    top = floors * f
    # the upper floors / roofs above the shell (upper(): the facade block, its roof slab, the parapet strips; the
    # model and pastel houses' stepped roofs; the containers' seam): dressed on their own
    hw, hd = w / 2, d / 2
    upper = K.take(lambda b: b['min'][1] >= top + 0.25 and b['min'][1] > F)
    seam = K.take(lambda b: kind == 'container' and abs(b['min'][1] - 2.9) < 1e-3 and b['max'][0] - b['min'][0] > w)
    dress_shell(K, w, d, floors, f, ext, intm=intm, floor=floor, roof='tar' if roof == 'shingle@roof' else roof, cap='metal',
                band='concrete', course='trim' if 'siding' in ext else 'concrete', corners='trim' if 'siding' in ext else 'concrete', wall_mat=wall_mat)
    for b in seam:  # (it runs right through the walls: drawn as a band 2 cm proud of them, round the outside)
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        K.box((x0 - 0.02, y0, z0 - 0.02), (x1 + 0.02, y1, z1 + 0.02), {'side': 'metaldark', 'top': None, 'bottom': None}, cull=False)
    for b in upper:
        h = b['max'][1] - b['min'][1]; bw = b['max'][0] - b['min'][0]; bd = b['max'][2] - b['min'][2]
        if roof == 'shingle@roof':  # the stepped toy roofs
            K.plain(b, {'side': 'shingle@roof', 'top': 'shingle@roof', 'bottom': 'ceiling'})
        elif h > 2.0:  # the upper floors' block: windows on every face
            K.plain(b, {'side': fac, 'top': None, 'bottom': None}, sub=None if fac.startswith('fac') else 1.6)
        elif h <= 0.31 and bw > w - 0.1:  # its roof slab
            K.plain(b, {'top': 'tar', 'side': 'concrete', 'bottom': 'concrete'}, sub=2.0)
        else:  # the parapet strips front and back, capped
            K.plain(b, {'side': 'concrete', 'top': None}, sub=2.0); cap(K, b, 'metal')
    left = [b for b in K.boxes if not b.get('_done')]
    for b in left:
        print('plain:', hid, b['mat'], b['min'], b['max'])
        K.plain(b, {'all': 'concrete'})
    K.finish(os.path.join(OUTDIR, hid + '.glb'))


IDS = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, 'houses')) if f.endswith('.json'))
for hid in IDS:
    if not ONLY or hid in ONLY: build(hid)
