# The Skyline's south tower (shared/map.js skyline(): roofTop() over a 160 m 'tenement' body): a grimy brick tenement.
# the facade is the kit's tenement texture (two bays x two floors a tile, lit windows glow at dusk), fitted so whole
# bays meet at the corners; brick piers up the corners, a stone string course every two floors, a heavy cornice on
# corbels under the roof slab's overhang, the parapet with a steel cap, drainpipes and cables down the faces, and the
# ghost of a GRISTLE & SONS ad painted on the brick. the roof garden itself (skyGarden) stays the map's
# run: blender52 -b --python tools/blender/arch/make_tenement.py -- [out.glb]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, cap

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = argv[0] if argv else os.path.join(OUTDIR, 'tenement.glb')
HERE = os.path.dirname(os.path.abspath(__file__))
K = Kit(os.path.join(HERE, 'boxes', 'tenement.json'), seed=3)
K.ground = -1e9
body = K.take(lambda b: b['mat'] == 'tenement')[0]
x0, y0, z0 = body['min']; x1, y1, z1 = body['max']
TILE = 7.0
TOP = y1  # -0.5: the roof slab sits on it
SHOW = -84  # below this it's deep in the haze: plain facade, no relief
# ---- the facade: four faces, whole bays across each (u stretched a hair), v counted down from the top
def face(p0, p1, along):
    n = max(1, round(along / TILE)); tu = along / n
    for (ya, yb) in [(y0, SHOW)] + [(SHOW + k * TILE, min(TOP, SHOW + (k + 1) * TILE)) for k in range(int((TOP - SHOW) / TILE) + 1)]:
        if yb <= ya: continue
        va, vb = (ya - TOP) / TILE, (yb - TOP) / TILE
        P = [(p0[0], ya, p0[1]), (p1[0], ya, p1[1]), (p1[0], yb, p1[1]), (p0[0], yb, p0[1])]
        K.quad(P, 'fac_tenement', uv=[(0, va), (n, va), (n, vb), (0, vb)], sub=None if ya < SHOW else 8.0)
face((x0, z1), (x1, z1), x1 - x0); face((x1, z0), (x0, z0), x1 - x0)
face((x1, z1), (x1, z0), z1 - z0); face((x0, z0), (x0, z1), z1 - z0)
# ---- relief on the part you see: string courses every two floors, piers up the corners, the cornice
for k in range(1, int((TOP - SHOW) / TILE) + 1):
    y = TOP - k * TILE
    K.box((x0 - 0.1, y - 0.12, z0 - 0.1), (x1 + 0.1, y + 0.14, z1 + 0.1), {'side': 'concrete', 'top': 'concrete', 'bottom': 'concrete'}, cull=False)
for (cx, cz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
    sx, sz = (1 if cx > 0 else -1), (1 if cz > 0 else -1)
    K.box((min(cx, cx + sx * 0.22) - (0.6 if sx > 0 else 0), SHOW, min(cz, cz + sz * 0.22) - (0.6 if sz > 0 else 0)),
          (max(cx, cx + sx * 0.22) + (0.6 if sx < 0 else 0), -2.75, max(cz, cz + sz * 0.22) + (0.6 if sz < 0 else 0)), {'all': 'brick'}, sub=7.0, cull=False)
# the cornice: a frieze band, corbels every 1.6 m under the slab's 40 cm overhang
K.box((x0 - 0.16, -1.25, z0 - 0.16), (x1 + 0.16, TOP, z1 + 0.16), {'side': 'trimdark', 'bottom': 'trimdark', 'top': None}, cull=False)
for (a0, a1, fixed, axis, s) in ((x0, x1, z0, 'x', -1), (x0, x1, z1, 'x', 1), (z0, z1, x0, 'z', -1), (z0, z1, x1, 'z', 1)):
    n = int((a1 - a0) / 1.6)
    for k in range(n + 1):
        a = a0 + 0.4 + k * (a1 - a0 - 0.8) / max(1, n)
        o0, o1 = (fixed + 0.16, fixed + 0.38) if s > 0 else (fixed - 0.38, fixed - 0.16)
        mn, mx = ((a - 0.12, -0.95, o0), (a + 0.12, TOP, o1)) if axis == 'x' else ((o0, -0.95, a - 0.12), (o1, TOP, a + 0.12))
        K.box(mn, mx, {'all': 'concrete'}, cull=False)
# ---- the roof slab (its overhang is the cornice's top) and the parapet with a steel cap
for b in K.take(lambda b: b['mat'] == 'concrete' and b['max'][1] - b['min'][1] < 0.6 and b['max'][0] - b['min'][0] > 20):
    K.plain(b, {'top': 'tar', 'side': 'concrete', 'bottom': 'concrete'}, sub=4.0)
for b in K.take(lambda b: b['mat'] == 'concrete' and b['min'][1] >= -0.01):
    K.plain(b, {'side': 'concrete', 'top': None}, sub=2.0)
    cap(K, b, 'metal', o=0.05)
# ---- drainpipes and cables down the faces, a ghost ad, soot
for (px, pz, nx, nz) in ((x0 + 3.1, z0 - 0.12, 0, -1), (x1 - 6.6, z0 - 0.12, 0, -1), (x1 + 0.12, z1 - 4.0, 1, 0), (x0 - 0.12, z0 + 9.0, -1, 0)):
    K.bar([(px, SHOW, pz), (px, -1.3, pz)], 0.16, 0.16, 'metaldark')
    for k in range(int((-1.3 - SHOW) / 7)):  # brackets
        y = -1.3 - k * 7
        K.bar([(px - nz * 0.0 - nx * 0.1, y, pz - nz * 0.1), (px, y, pz)], 0.22, 0.06, 'metal')
for (pa, pb) in (((x0 + 8.0, -1.3, z0 - 0.06), (x0 + 8.3, -30, z0 - 0.06)), ((x0 + 8.4, -1.3, z0 - 0.06), (x0 + 13.0, -12, z0 - 0.06))):
    K.bar([pa, pb], 0.05, 0.05, 'rubber')
K.decal_on('x', z0, -1, 0.012, (x0 + x1) / 2 + 4, -4.0, 'ad_gristle', w=14, h=7, anchor='top')
K.decal_on('z', x0, -1, 0.012, 0, -6.0, 'ad_jankcorp', w=14, h=7, anchor='top')
K.decal_on('z', x1, 1, 0.012, -2, -3.5, 'tag_1', w=6, h=3, anchor='top')
for (axis, c, s, a) in (('x', z0, -1, -8), ('x', z1, 1, 5), ('z', x1, 1, 7), ('z', x0, -1, -6)):
    K.decal_on(axis, c, s, 0.011, a, -1.3, 'grime_run', w=4, h=9, anchor='top')
# ---- shape: iron fire escapes zigzagging down two faces, a vertical blade sign on the corner, AC boxes and washing
# hung out of windows. all of it on the faces, below the roof: nothing new to stand on up top
FL.fire_escape(K, 'x', z1, 1, x0 + 5.0, x0 + 10.5, -3.6, 7, 3.5, depth=1.3)
FL.fire_escape(K, 'z', x1, 1, z0 + 6.0, z0 + 11.5, -3.6, 7, 3.5, depth=1.3)
bx, bz = x1 + 0.9, z0 - 0.9  # the blade sign, off the corner on two arms
for y in (-4.0, -15.5): FL.bar(K, (x1, y, z0), (bx, y, bz), 0.12, 'metaldark')
FL.obox(K, (bx - 0.2, -16.0, bz - 0.75), (bx + 0.2, -3.5, bz + 0.75), {'side': 'metaldark', 'top': 'metaldark', 'bottom': 'metaldark'})
for i, c in enumerate(('pink', 'yellow', 'cyan', 'pink', 'yellow')):
    for sgn in (-1, 1):
        FL.obox(K, (bx + sgn * 0.2 - (0.03 if sgn < 0 else 0), -5.6 - i * 2.2, bz - 0.5), (bx + sgn * 0.2 + (0.03 if sgn > 0 else 0), -4.2 - i * 2.2, bz + 0.5), c)
import random as _r
_r.seed(31)
for (axis, face, s, lo, hi) in (('x', z0, -1, x0, x1), ('x', z1, 1, x0, x1), ('z', x0, -1, z0, z1), ('z', x1, 1, z0, z1)):
    P = FL.WP(axis, face, s)
    for k in range(9):
        a = lo + 2.0 + _r.random() * (hi - lo - 4.0); y = -5.0 - int(_r.random() * 8) * 3.5
        p, q = P(a - 0.4, y, 0.02), P(a + 0.4, y + 0.5, 0.5)
        FL.obox(K, [min(p[i], q[i]) for i in range(3)], [max(p[i], q[i]) for i in range(3)], 'metal')
    for k in range(4):  # a washing line between two windows, things on it
        a = lo + 3.0 + _r.random() * (hi - lo - 9.0); y = -6.2 - int(_r.random() * 7) * 3.5; L = 2.6 + _r.random() * 1.5
        oo = 0.31 + 0.03 * k  # (each line in its own plane, its cloths hung on its centre)
        FL.bar(K, P(a, y, oo), P(a + L, y - 0.1, oo), 0.02, 'rubber')
        for j in range(int(L / 0.6)):
            aa = a + 0.2 + j * 0.6; hh = 0.35 + 0.3 * _r.random(); yl = y - 0.1 * (aa + 0.21 - a) / L
            FL.both(K, [P(aa, yl - hh, oo), P(aa + 0.42, yl - hh, oo), P(aa + 0.42, yl, oo), P(aa, yl, oo)], ('pink', 'yellow', 'cyan', 'trim')[(j + k) % 4])

left = [b for b in K.boxes if not b.get('_done')]
for b in left:
    print('plain:', b['mat'], b['min'], b['max'])
    K.plain(b, {'all': 'concrete'})
K.finish(OUT)
