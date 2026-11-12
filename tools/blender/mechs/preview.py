# quick looks while iterating: blender52 -b -P tools/blender/mechs/preview.py -- <paperplane|nightshift> <outdir> [views] [samples] [pose]
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mechkit import *
import importlib
argv = sys.argv[sys.argv.index('--') + 1:]
which, out = argv[0], argv[1]
views = (argv[2] if len(argv) > 2 else 'q,front,side,back').split(',')
spp = int(argv[3]) if len(argv) > 3 else 16
lib.reset(); lib._mats.clear()
mod = importlib.import_module(which)
mk = mod.build(); mk.build_tree()
if len(argv) > 4 and hasattr(mod, 'POSES'): mk.pose(mod.POSES[argv[4]](mk))
h = mk.meta.get('height', 5.0)
VW = {'q': ((-5.5, h * 0.62, -8.5), 50), 'front': ((0, h * 0.52, -14), 55), 'side': ((14, h * 0.52, 0), 55), 'back': ((0, h * 0.52, 14), 55),
      'qb': ((6.5, h * 0.7, 8.0), 50), 'head': ((-1.4, h * 0.92, -2.6), 50), 'low': ((-3.5, 1.0, -6.5), 40), 'top': ((0.01, 16, 0), 40)}
cycles(spp, (720, 900)); studio((0, h / 2, 0), h)
os.makedirs(out, exist_ok=True)
for v in views:
    loc, lens = VW[v]
    tgt = (0, h * 0.5, 0) if v != 'head' else (0, h * 0.86, -0.1)
    camera(loc, tgt, lens)
    render(os.path.join(out, f'{which}_{v}.png'))
print('TRIS', mk.tris())
