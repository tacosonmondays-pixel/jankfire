# Skyline's towers (shared/map.js skyline(): roofTop() bodies 150-170 m down to the street, TOWER_ARCH): drawn over
# their own boxes like the south tower (make_tenement.py), one model per tower (each has its own size and its own
# parapet gaps). Three looks, all from the kit's facades:
#   tenement (E, NE): the grimy brick tenement: piers up the corners, a stone course every two floors, a corbelled
#     cornice, fire escapes zig-zagging down two faces, drainpipes, AC boxes and washing out of the windows, a ghost ad
#   office (N, W, SE, SW): an 80s office block: ribbon windows (lit at dusk), chrome fins up the corners, a slim metal
#     band every two floors, a dark fascia with a chrome lip under the slab, a vertical blade sign on one corner
#   concrete (NW, the building site's tower): the same office grid in raw grey concrete, heavy bands, square piers
# The roof slab and the parapet (with its gaps) are capped; the roof's set piece stays the map's. Below SHOW the faces
# are plain (deep in the haze). Visual only: the boxes stay what you bump into.
# run: node tools/arch/dump.mjs skyline <id> tools/blender/arch/boxes/<id>.json   (for each id below)
#      blender52 -b --python tools/blender/arch/make_tower.py -- [id ...]   (all by default)
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST, cap

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
STYLE = {'tenement_e': 'tenement', 'tenement_ne': 'tenement', 'office_n': 'office', 'office_w': 'office', 'office_se': 'office',
         'office_sw': 'office', 'concrete_nw': 'concrete'}
MATS.update({'fac_conc': ('fac_office', '#a2acba', {}), 'chrome': ('metalplate', '#e4ecf4', {}), 'navy': ('metalplate', '#2c3a5c', {}),
             'neonpink': ('stucco', '#ff4fd8', {'glow': True}), 'neonyellow': ('stucco', '#ffe14d', {'glow': True}),
             'lit': ('stucco', '#ffe2a0', {'glow': True}), 'litcool': ('stucco', '#a8ecff', {'glow': True})})
NOCAST.update({'chrome', 'navy', 'neonpink', 'neonyellow', 'lit', 'litcool'})
TILE = 7.0
SHOW = -84  # below this it's deep in the haze: plain facade, no relief


def build(id_):
    style = STYLE[id_]
    K = Kit(os.path.join(HERE, 'boxes', id_ + '.json'), seed=hash(id_) & 255)
    rng = random.Random(len(id_) * 7 + 3)
    body = K.take(lambda b: b['max'][1] - b['min'][1] > 20)[0]
    x0, y0, z0 = body['min']; x1, y1, z1 = body['max']
    K.ground = y0
    TOP = y1
    fac = {'tenement': 'fac_tenement', 'office': 'fac_office', 'concrete': 'fac_conc'}[style]
    # ---- the facade: four faces, whole bays across each (u stretched a hair), v counted down from the top
    def face(p0, p1, along):
        n = max(1, round(along / TILE))
        for (ya, yb) in [(y0, SHOW)] + [(SHOW + k * TILE, min(TOP, SHOW + (k + 1) * TILE)) for k in range(int((TOP - SHOW) / TILE) + 1)]:
            if yb <= ya: continue
            va, vb = (ya - TOP) / TILE, (yb - TOP) / TILE
            P = [(p0[0], ya, p0[1]), (p1[0], ya, p1[1]), (p1[0], yb, p1[1]), (p0[0], yb, p0[1])]
            K.quad(P, fac, uv=[(0, va), (n, va), (n, vb), (0, vb)], sub=None if ya < SHOW else 8.0)
    face((x0, z1), (x1, z1), x1 - x0); face((x1, z0), (x0, z0), x1 - x0)
    face((x1, z1), (x1, z0), z1 - z0); face((x0, z0), (x0, z1), z1 - z0)
    # ---- offices still lit at dusk (office / concrete): whole windows of the facade texture (two rows, four bays a
    # tile) as thin glowing panes against the glass, so every tower sparkles differently
    if style != 'tenement':
        for (axis, c, s, a0, a1) in (('x', z0, -1, x0, x1), ('x', z1, 1, x0, x1), ('z', x0, -1, z0, z1), ('z', x1, 1, z0, z1)):
            nt = max(1, round((a1 - a0) / TILE)); tw = (a1 - a0) / nt
            P = FL.WP(axis, c, s)
            for kt in range(int((TOP - SHOW) / TILE)):
                yt = TOP - kt * TILE
                for (r0, r1) in ((1.25, 3.0), (4.75, 6.55)):
                    for it in range(nt):
                        for iw in range(4):
                            if rng.random() > 0.14: continue
                            u0 = a0 + it * tw + (iw * 32 + 2) / 128 * tw; u1 = a0 + it * tw + (iw * 32 + 30) / 128 * tw
                            if s < 0 and axis == 'x' or s > 0 and axis == 'z': u0, u1 = a0 + a1 - u1, a0 + a1 - u0  # (u runs the other way on these faces)
                            p, q = P(u0, yt - r1, 0.0), P(u1, yt - r0, 0.025)
                            K.box(tuple(min(p[i], q[i]) for i in range(3)), tuple(max(p[i], q[i]) for i in range(3)), {'all': 'lit' if rng.random() < 0.8 else 'litcool'})
    # ---- relief on the part you see: a course every two floors, piers / fins up the corners, the cornice
    course = {'tenement': ('concrete', 0.26, 0.1), 'office': ('chrome', 0.14, 0.06), 'concrete': ('concrete', 0.45, 0.14)}[style]
    for k in range(1, int((TOP - SHOW) / TILE) + 1):
        y = TOP - k * TILE; m, h, o = course
        K.box((x0 - o, y - h / 2, z0 - o), (x1 + o, y + h / 2, z1 + o), {'side': m, 'top': m, 'bottom': m}, cull=False)
    pier = {'tenement': ('brick', 0.6, 0.22), 'office': ('chrome', 0.45, 0.16), 'concrete': ('concrete', 0.9, 0.3)}[style]
    for (cx, cz) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        sx, sz = (1 if cx > (x0 + x1) / 2 else -1), (1 if cz > (z0 + z1) / 2 else -1)
        m, w, p = pier
        K.box((min(cx, cx + sx * p) - (w if sx > 0 else 0), SHOW, min(cz, cz + sz * p) - (w if sz > 0 else 0)),
              (max(cx, cx + sx * p) + (w if sx < 0 else 0), -2.75, max(cz, cz + sz * p) + (w if sz < 0 else 0)), {'all': m}, sub=7.0, cull=False)
    if style == 'tenement':  # a frieze band, corbels every 1.6 m under the slab's 40 cm overhang
        K.box((x0 - 0.16, -1.25, z0 - 0.16), (x1 + 0.16, TOP, z1 + 0.16), {'side': 'trimdark', 'bottom': 'trimdark', 'top': None}, cull=False)
        for (a0, a1, fixed, axis, s) in ((x0, x1, z0, 'x', -1), (x0, x1, z1, 'x', 1), (z0, z1, x0, 'z', -1), (z0, z1, x1, 'z', 1)):
            n = int((a1 - a0) / 1.6)
            for k in range(n + 1):
                a = a0 + 0.4 + k * (a1 - a0 - 0.8) / max(1, n)
                o0, o1 = (fixed + 0.16, fixed + 0.38) if s > 0 else (fixed - 0.38, fixed - 0.16)
                mn, mx = ((a - 0.12, -0.95, o0), (a + 0.12, TOP, o1)) if axis == 'x' else ((o0, -0.95, a - 0.12), (o1, TOP, a + 0.12))
                K.box(mn, mx, {'all': 'concrete'}, cull=False)
    else:  # a dark fascia with a chrome lip under the slab
        K.box((x0 - 0.14, -1.5, z0 - 0.14), (x1 + 0.14, TOP - 0.1, z1 + 0.14), {'side': 'navy' if style == 'office' else 'concrete', 'bottom': 'navy' if style == 'office' else 'concrete', 'top': None}, cull=False)
        K.box((x0 - 0.2, TOP - 0.1, z0 - 0.2), (x1 + 0.2, TOP, z1 + 0.2), {'side': 'chrome', 'bottom': 'chrome', 'top': None}, cull=False)
    # ---- the roof slab (its overhang over the cornice) and the parapet with a steel cap
    for b in K.take(lambda b: b['mat'] == 'concrete' and b['max'][1] - b['min'][1] < 0.6 and b['max'][0] - b['min'][0] > 20):
        K.plain(b, {'top': 'tar', 'side': 'concrete', 'bottom': 'concrete'}, sub=4.0)
    for b in K.take(lambda b: b['mat'] == 'concrete' and b['min'][1] >= -0.01):
        K.plain(b, {'side': 'concrete', 'top': None}, sub=2.0)
        cap(K, b, 'metal', o=0.05)
    # ---- shape and personality, on the faces below the roof (nothing new to stand on)
    sides = (('x', z0, -1, x0, x1), ('x', z1, 1, x0, x1), ('z', x0, -1, z0, z1), ('z', x1, 1, z0, z1))
    if style == 'tenement':
        for (px, pz, nx, nz) in ((x0 + 3.1, z0 - 0.12, 0, -1), (x1 - 6.6, z0 - 0.12, 0, -1), (x1 + 0.12, z1 - 4.0, 1, 0), (x0 - 0.12, z0 + 9.0, -1, 0)):
            K.bar([(px, SHOW, pz), (px, -1.3, pz)], 0.16, 0.16, 'metaldark')  # drainpipes
            for k in range(int((-1.3 - SHOW) / 7)):
                y = -1.3 - k * 7
                K.bar([(px - nx * 0.1, y, pz - nz * 0.1), (px, y, pz)], 0.22, 0.06, 'metal')
        FL.fire_escape(K, 'x', z1, 1, x0 + 5.0, x0 + 10.5, -3.6, 7, 3.5, depth=1.3)
        FL.fire_escape(K, 'z', x0, -1, z0 + 6.0, z0 + 11.5, -3.6, 7, 3.5, depth=1.3)
        for (axis, face_, s, lo, hi) in sides:
            P = FL.WP(axis, face_, s)
            taken = []
            for k in range(8):  # AC boxes hung out of windows (never two in one spot: they'd flicker)
                a = lo + 2.0 + rng.random() * (hi - lo - 4.0); y = -5.0 - int(rng.random() * 8) * 3.5
                if any(abs(a - ta) < 1.0 and abs(y - ty) < 0.6 for ta, ty in taken): continue
                taken.append((a, y))
                p, q = P(a - 0.4, y, 0.02), P(a + 0.4, y + 0.5, 0.5)
                FL.obox(K, [min(p[i], q[i]) for i in range(3)], [max(p[i], q[i]) for i in range(3)], 'metal')
        K.decal_on('x', z1, 1, 0.012, (x0 + x1) / 2 - 3, -4.0, rng.choice(['ad_teeth', 'ad_smile']), w=12, h=6, anchor='top')
        K.decal_on('z', x1, 1, 0.012, 0, -6.0, 'ad_jankcorp', w=12, h=6, anchor='top')
        for (axis, c, s, a) in (('x', z0, -1, -6), ('x', z1, 1, 7), ('z', x1, 1, -5), ('z', x0, -1, 4)):
            K.decal_on(axis, c, s, 0.011, a, -1.3, 'grime_run', w=4, h=9, anchor='top')
    else:
        # a vertical blade sign off one corner on two arms, glowing letters down it
        cx, cz = x1, z0
        bx, bz = cx + 0.9, cz - 0.9
        for y in (-4.5, -18.5): FL.bar(K, (cx, y, cz), (bx, y, bz), 0.12, 'metaldark')
        FL.obox(K, (bx - 0.2, -19.0, bz - 0.75), (bx + 0.2, -4.0, bz + 0.75), {'side': 'navy', 'top': 'navy', 'bottom': 'navy'})
        glow = 'neonpink' if style == 'office' else 'neonyellow'
        for i in range(6):
            for sgn in (-1, 1):
                FL.obox(K, (bx + sgn * 0.2 - (0.03 if sgn < 0 else 0), -6.2 - i * 2.2, bz - 0.5), (bx + sgn * 0.2 + (0.03 if sgn > 0 else 0), -4.9 - i * 2.2, bz + 0.5), glow)
        K.decal_on('x', z1, 1, 0.012, (x0 + x1) / 2, -4.5, rng.choice(['ad_jankcorp', 'ad_smile', 'ad_teeth']), w=12, h=6, anchor='top')
        for (axis, c, s, a) in (('x', z0, -1, -5), ('z', x0, -1, 6)):
            K.decal_on(axis, c, s, 0.011, a, -1.6, 'grime_run', w=4, h=10, anchor='top')
    left = [b for b in K.boxes if not b.get('_done')]
    for b in left:
        print('plain:', b['mat'], b['min'], b['max'])
        K.plain(b, {'all': 'concrete'})
    K.finish(os.path.join(OUTDIR, id_ + '.glb'))


for id_ in ([a for a in argv if a in STYLE] or list(STYLE)):
    build(id_)
