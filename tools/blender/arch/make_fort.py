# Fort Splinter (shared/map.js fort()): drawn over its own boxes (tools/arch/dump.mjs), which stay what you bump into.
# A weathered sea fort: coursed sandstone walls on a darker footing, moss climbing out of the sand and salt bloom
# running down under the string course; merlons with cap stones; four bastions with quoined corners, a corbelled
# cornice and a cannon port on each outward face (a muzzle poking out); timber gates with iron straps swung back flat
# against the inside of the wall, dressed jambs and a keystone over each; stone steps up to the wall walk (Islands);
# flagstones on the wall walk and in the courtyard. In the courtyard: a whitewashed lean-to armoury under a plank roof
# (its door open, cannonballs stacked inside), a stone well with a winch, a rope and a bucket under a little roof, and
# the flag on a proper mast. Barrels, crates, cannons, the cannonball pad and the flag itself stay the game's.
# Islands' fort has a postern in the west wall and the two stairs (its well and flagpole ride the dunes, so they stay
# the game's boxes there); Islands S&D's (fort_sd) a big west gate, no stairs
# (its north west leaf lies smashed on the ground: the armoury is in the way).
# local frame = the fort's (shared/map.js fort(): Islands puts it at 0,0; S&D at 77,-64).
# run: node tools/arch/dump.mjs islands fort tools/blender/arch/boxes/fort.json
#      node tools/arch/dump.mjs islands_sd fort_sd tools/blender/arch/boxes/fort_sd.json
#      blender52 -b --python tools/blender/arch/make_fort.py -- [fort|fort_sd]   (both by default)
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flair as FL
from archkit import Kit, OUTDIR, MATS, NOCAST
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
MATS.update({
    'fstone': ('stone', '#ecdcbc', {}), 'fstone2': ('stone', '#b4a68e', {}), 'fquoin': ('stone', '#fbf0d8', {}), 'fpave': ('stone', '#d2c4a6', {}),
    'fflag': ('stone', '#9c9a94', {}), 'fweather': ('weather', '#ffffff', {'alpha': True}), 'fplaster': ('stucco', '#f4ead4', {}),
    'fwood': ('planks', '#c08a58', {}), 'fwooddark': ('planks', '#7a5434', {}), 'firon': ('metalplate', '#3a3a42', {}), 'fport': ('tar', '#2a2026', {}),
    'frope': ('stucco', '#d2b07a', {}), 'fbrass': ('metalplate', '#e8b840', {}), 'fball': ('metalplate', '#2a2a30', {}),
})
NOCAST.update({'fweather', 'firon', 'frope', 'fbrass', 'fport'})
FW = 4.5                     # the wall walk
CX, CZ = -77.0, 0.0          # the courtyard's middle
OUT = {'n': (-13.0, 'z', -1), 's': (13.0, 'z', 1), 'w': (-87.0, 'x', -1), 'e': (-67.0, 'x', 1)}  # outer faces


def kind_of(b):
    (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']; w, h, d = x1 - x0, y1 - y0, z1 - z0
    if b['mat'] == 'metal': return 'pole'
    if b['mat'] == 'wood': return 'roof'
    if abs(h - 1.0) < 1e-3 and y0 >= FW - 1e-3: return 'merlon'
    if abs(w - 4) < 1e-3 and abs(d - 4) < 1e-3: return 'bastion'
    if (abs(z0 + 11) < 1e-3 and abs(z1 + 9.6) < 1e-3) or (abs(z0 - 9.6) < 1e-3 and abs(z1 - 11) < 1e-3): return 'step'
    if abs(x0 + 79.2) < 1e-3 and abs(x1 + 77.2) < 1e-3: return 'well'
    if min(w, d) < 0.45: return 'armoury'
    return 'wall'


def quoins(x, z, sx, sz, y0, y1):
    """dressed corner stones up a vertical corner at (x, z), the faces looking sx (x) and sz (z): long and short in turn"""
    y, k = y0, 0
    while y < y1 - 0.05:
        h = min(0.42, y1 - y); a, b = (0.55, 0.3) if k % 2 == 0 else (0.3, 0.55)
        K.box((min(x, x - sx * a), y, z - 0.0 if sz > 0 else z - 0.03), (max(x, x - sx * a), y + h - 0.02, z + 0.03 if sz > 0 else z), {'all': 'fquoin'})
        K.box((x - 0.0 if sx > 0 else x - 0.03, y, min(z, z - sz * b)), (x + 0.03 if sx > 0 else x, y + h - 0.02, max(z, z - sz * b)), {'all': 'fquoin'})
        y += h; k += 1


def weather_on(face, a0, a1, y0, y1, v0, v1, off=0.015):
    """the moss / salt overlay on an outer face: from a0 to a1 along it, uv v from v0 (foot) to v1"""
    c, ax, sg = OUT[face]; o = c + sg * off
    if ax == 'z': P = [(a0, y0, o), (a1, y0, o), (a1, y1, o), (a0, y1, o)]
    else: P = [(o, y0, a0), (o, y0, a1), (o, y1, a1), (o, y1, a0)]
    L = abs(a1 - a0) / 2.0
    q = [Vector(p) for p in P]; n = (q[1] - q[0]).cross(q[3] - q[0])
    want = Vector((0, 0, sg)) if ax == 'z' else Vector((sg, 0, 0))
    uv = [(0, v0), (L, v0), (L, v1), (0, v1)]
    if n.dot(want) < 0: P = P[::-1]; uv = uv[::-1]
    K.quad(P, 'fweather', uv=uv)


def leaf(hx, hz, ax, along, y0, y1, w, th, side, mat='fwood', smashed=False):
    """a timber gate leaf lying flat against a wall face: hinge at (hx, hz), running `along` (+1/-1) for w on axis ax,
    th thick, out from the face toward `side`; iron straps across, studs"""
    def P(a, o): return (hx + o * side, hz + a * along) if ax == 'z' else (hx + a * along, hz + o * side)
    if smashed:  # down in the gateway in broken planks (game coords, not the hinge's: it's not hanging from anything)
        for (x0, z0, x1, z1, y) in ((-84.7, -2.35, -83.0, -1.9, 0.024), (-83.7, -1.75, -82.1, -1.25, 0.026), (-84.3, -1.05, -83.4, -0.45, 0.024), (-82.9, -2.3, -82.3, -1.95, 0.028)):
            K.box((x0, y, z0), (x1, y + 0.09, z1), {'all': mat}, cull=False)
            K.box((x0 + 0.15, y + 0.09, z0 + 0.05), (x0 + 0.25, y + 0.11, z1 - 0.05), {'all': 'firon'}, cull=False)
        return
    p0, p1 = P(0.0, 0.0), P(w, th)
    K.box((min(p0[0], p1[0]), y0, min(p0[1], p1[1])), (max(p0[0], p1[0]), y1, max(p0[1], p1[1])), {'all': mat}, cull=False)
    for y in (y0 + 0.35, (y0 + y1) / 2, y1 - 0.4):  # the straps, out on its open face
        q0, q1 = P(0.02, th), P(w - 0.08, th + 0.02)
        K.box((min(q0[0], q1[0]), y, min(q0[1], q1[1])), (max(q0[0], q1[0]), y + 0.1, max(q0[1], q1[1])), {'all': 'firon'}, cull=False)
    r0, r1 = P(w - 0.35, th), P(w - 0.33, th + 0.06)  # a ring pull
    FL.tube(K, ((r0[0] + r1[0]) / 2, (y0 + y1) / 2 - 0.12, (r0[1] + r1[1]) / 2), ((r0[0] + r1[0]) / 2, (y0 + y1) / 2 - 0.3, (r0[1] + r1[1]) / 2), 0.03, 0.03, 'firon', n=4)


def dress_gate(face, a0, a1, top):
    """jamb stones and a flat arch with a keystone round an opening, on the outer face and the inner one"""
    c, ax, sg = OUT[face]
    for (cc, s) in ((c, sg), (c - sg * 2.0, -sg)):
        def B(a_lo, a_hi, y0, y1, d=0.05):
            if ax == 'z': K.box((a_lo, y0, min(cc, cc + s * d)), (a_hi, y1, max(cc, cc + s * d)), {'all': 'fquoin'})
            else: K.box((min(cc, cc + s * d), y0, a_lo), (max(cc, cc + s * d), y1, a_hi), {'all': 'fquoin'})
        y, k = 0.0, 0
        while y < top - 0.05:  # the jambs, long and short
            h = min(0.45, top - y); w = 0.45 if k % 2 == 0 else 0.28
            B(a0 - w, a0, y, y + h - 0.02); B(a1, a1 + w, y, y + h - 0.02); y += h; k += 1
        n = 7; span = a1 - a0 + 0.56
        for i in range(n):  # voussoirs over it, the keystone proud and taller
            s0 = a0 - 0.28 + span * i / n; s1 = s0 + span / n - 0.03
            key = i == n // 2
            B(s0, s1, top, top + (0.75 if key else 0.6), 0.08 if key else 0.05)


def port(face, a, y):
    """a cannon port on a bastion: a dark slot in a dressed frame, a muzzle poking out"""
    c, ax, sg = OUT[face] if face in OUT else face
    def B(a0, a1, y0, y1, d0, d1, m):
        if ax == 'z': K.box((a0, y0, min(c + sg * d0, c + sg * d1)), (a1, y1, max(c + sg * d0, c + sg * d1)), {'all': m})
        else: K.box((min(c + sg * d0, c + sg * d1), y0, a0), (max(c + sg * d0, c + sg * d1), y1, a1), {'all': m})
    B(a - 0.35, a + 0.35, y - 0.3, y + 0.3, 0.0, 0.012, 'fport')
    B(a - 0.5, a - 0.35, y - 0.3, y + 0.3, 0.0, 0.06, 'fquoin'); B(a + 0.35, a + 0.5, y - 0.3, y + 0.3, 0.0, 0.06, 'fquoin')  # (between the head and the sill: they meet, they don't overlap)
    B(a - 0.5, a + 0.5, y + 0.3, y + 0.45, 0.0, 0.07, 'fquoin'); B(a - 0.5, a + 0.5, y - 0.45, y - 0.3, 0.0, 0.08, 'fquoin')
    m0 = (a, y - 0.02, c + sg * 0.012) if ax == 'z' else (c + sg * 0.012, y - 0.02, a)
    m1 = (a, y - 0.04, c + sg * 0.28) if ax == 'z' else (c + sg * 0.28, y - 0.04, a)
    FL.tube(K, m0, m1, 0.13, 0.15, 'fball', n=8)
    m2 = (a, y - 0.04, c + sg * 0.26) if ax == 'z' else (c + sg * 0.26, y - 0.04, a)
    FL.tube(K, m2, m1, 0.16, 0.16, 'fball', n=8, caps=(True, False))


def ball(c, r, mat='fball'):
    x, y, z = c
    FL.tube(K, (x, y - r, z), (x, y, z), 0.0, r, mat, n=6, caps=(False, False)); FL.tube(K, (x, y, z), (x, y + r, z), r, 0.0, mat, n=6, caps=(False, False))


def build(kind):
    global K
    K = Kit(os.path.join(HERE, 'boxes', kind + '.json'), seed=7)
    K.ground = 0.0
    sd = kind == 'fort_sd'
    groups = {}
    for b in K.boxes: b['_done'] = True; groups.setdefault(kind_of(b), []).append(b)
    K.solids = [(b['min'], b['max']) for b in K.boxes if kind_of(b) != 'pole']
    # ---- walls: coursed stone, flagstones along the wall walk, a darker footing, a string course under the merlons
    for b in groups.get('wall', []):
        K.box(b['min'], b['max'], {'all': 'fstone', 'top': 'fpave'}, sub=1.5)
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        if y0 > 0.01: continue
        K.box((x0 - 0.06, 0, z0 - 0.06), (x1 + 0.06, 0.5, z1 + 0.06), {'all': 'fstone2'})
    for b in groups.get('bastion', []):
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        K.box(b['min'], b['max'], {'all': 'fstone', 'top': 'fpave'}, sub=1.5)
        K.box((x0 - 0.07, 0, z0 - 0.07), (x1 + 0.07, 0.6, z1 + 0.07), {'all': 'fstone2'})
        K.box((x0 - 0.1, 5.75, z0 - 0.1), (x1 + 0.1, 5.98, z1 + 0.1), {'side': 'fquoin', 'bottom': 'fquoin', 'top': None})  # the cornice
        sx, sz = (1 if x0 > CX else -1), (1 if z0 > CZ else -1)
        ox, oz = (x1 if sx > 0 else x0), (z1 if sz > 0 else z0)
        for k in range(6):  # corbels under it on the two outward faces
            t = x0 + 0.3 + k * 0.68
            K.box((t - 0.09, 5.45, oz - 0.08 if sz < 0 else oz), (t + 0.09, 5.75, oz if sz < 0 else oz + 0.08), {'all': 'fquoin'})
            t = z0 + 0.3 + k * 0.68
            K.box((ox - 0.08 if sx < 0 else ox, 5.45, t - 0.09), (ox if sx < 0 else ox + 0.08, 5.75, t + 0.09), {'all': 'fquoin'})
        quoins(ox, oz, sx, sz, 0.6, 5.45)
        port((oz, 'z', sz), (x0 + x1) / 2, 2.6); port((ox, 'x', sx), (z0 + z1) / 2, 2.6)
    # the string course on the walls' outer faces (bastion to bastion), weathering at their feet and under it
    for face, (c, ax, sg) in OUT.items():
        a0, a1 = (-84.0, -70.0) if ax == 'z' else (-10.0, 10.0)
        if ax == 'z': K.box((a0, 4.18, min(c, c + sg * 0.07)), (a1, 4.3, max(c, c + sg * 0.07)), {'all': 'fquoin'})
        else: K.box((min(c, c + sg * 0.07), 4.18, a0), (max(c, c + sg * 0.07), 4.3, a1), {'all': 'fquoin'})
        gaps = {'w': ((-2.5, 2.5) if sd else (-1.0, 1.0)), 'e': (-2.5, 2.5)}.get(face)
        for (s0, s1) in (((a0, gaps[0]), (gaps[1], a1)) if gaps else ((a0, a1),)):
            weather_on(face, s0 + 0.05, s1 - 0.05, 0.5, 1.7, 0.02, 0.6, off=0.004)
            weather_on(face, s0 + 0.05, s1 - 0.05, 3.1, 4.17, 0.55, 0.99, off=0.004)
    # ---- merlons with cap stones
    for b in groups.get('merlon', []):
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        K.box(b['min'], b['max'], {'all': 'fstone', 'top': None})
        K.box((x0 - 0.05, y1, z0 - 0.05), (x1 + 0.05, y1 + 0.1, z1 + 0.05), {'all': 'fquoin'}, cull=False)
    # ---- gates: dressed openings, the leaves swung back flat against the inside
    dress_gate('e', -2.5, 2.5, 3.4)
    leaf(-69.05, -2.5, 'z', -1, 0.0, 3.3, 2.45, 0.1, -1); leaf(-69.05, 2.5, 'z', 1, 0.0, 3.3, 2.45, 0.1, -1)  # (5 cm off the wall: over the jamb stones)
    if sd:
        dress_gate('w', -2.5, 2.5, 3.4)
        leaf(-84.95, 2.5, 'z', 1, 0.0, 3.3, 2.45, 0.1, 1)
        leaf(-84.95, -2.5, 'z', -1, 0.0, 3.3, 2.45, 0.1, 1, smashed=True)
    else:
        dress_gate('w', -1.0, 1.0, 2.4)
        leaf(-84.95, 1.0, 'z', 1, 0.0, 2.35, 1.95, 0.09, 1, mat='fwooddark')
    # ---- the stairs (Islands): stone steps, paler treads
    for b in groups.get('step', []):
        K.box(b['min'], b['max'], {'all': 'fstone', 'top': 'fquoin'})
    # ---- the armoury: whitewashed walls, a plank roof with its rafter ends showing, the door open, cannonballs inside
    for b in groups.get('armoury', []):
        K.box(b['min'], b['max'], {'all': 'fplaster'}, sub=1.2)
    for b in groups.get('roof', []):
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        K.box(b['min'], b['max'], {'top': 'fwood', 'bottom': 'fwooddark', 'side': 'fwooddark'})
        for k in range(7): z = z0 + 0.3 + k * (z1 - z0 - 0.6) / 6; K.box((x1 - 0.02, y0 - 0.16, z - 0.07), (x1 + 0.14, y0, z + 0.07), {'all': 'fwooddark'}, cull=False)
    leaf(-80.6, -6.7, 'z', -1, 0.0, 2.15, 1.38, 0.07, -1, mat='fwooddark')
    for (x, z) in ((-83.6, -6.0), (-83.6, -4.4)):
        for (ox, oz, oy) in ((-0.17, -0.17, 0), (0.17, -0.17, 0), (-0.17, 0.17, 0), (0.17, 0.17, 0), (0, 0, 0.27)):
            ball((x + ox, 0.17 + oy, z + oz), 0.17)
    # ---- the well: dressed stone, cap stones round the water, a winch on two posts, the rope, the bucket, a little roof
    for b in groups.get('well', []):
        (x0, y0, z0), (x1, y1, z1) = b['min'], b['max']
        K.box(b['min'], b['max'], {'all': 'fstone', 'top': None}, tile=1.2)
        for (a, bb) in (((x0, z0), (x1, z0 + 0.28)), ((x0, z1 - 0.28), (x1, z1)), ((x0, z0 + 0.28), (x0 + 0.28, z1 - 0.28)), ((x1 - 0.28, z0 + 0.28), (x1, z1 - 0.28))):
            K.box((a[0] - 0.03, y1, a[1] - (0.03 if a[1] == z0 else 0)), (bb[0] + 0.03 if bb[0] == x1 else bb[0], y1 + 0.1, bb[1] + (0.03 if bb[1] == z1 else 0)), {'all': 'fquoin'}, cull=False)
        for x in (-79.1, -77.3):
            K.box((x - 0.08, 1.1, 4.12), (x + 0.08, 2.75, 4.28), {'all': 'fwooddark'}, cull=False)
        FL.tube(K, (-79.02, 2.2, 4.2), (-77.38, 2.2, 4.2), 0.07, 0.07, 'fwood', n=8)
        FL.tube(K, (-78.6, 2.2, 4.2), (-77.9, 2.2, 4.2), 0.085, 0.085, 'frope', n=8)
        FL.bar(K, (-77.25, 2.2, 4.2), (-77.08, 2.2, 4.2), 0.04, 'firon'); FL.bar(K, (-77.1, 2.2, 4.2), (-77.1, 1.95, 4.2), 0.035, 'firon'); FL.bar(K, (-77.1, 1.97, 4.2), (-76.98, 1.97, 4.2), 0.04, 'fwooddark')
        FL.bar(K, (-78.2, 2.13, 4.2), (-78.2, 1.5, 4.2), 0.02, 'frope')
        FL.tube(K, (-78.2, 1.24, 4.2), (-78.2, 1.48, 4.2), 0.11, 0.13, 'fwood', n=8, caps=(True, False), inside=True)
        for y in (1.28, 1.43): FL.tube(K, (-78.2, y, 4.2), (-78.2, y + 0.03, 4.2), 0.118 + (y - 1.24) * 0.08, 0.12 + (y - 1.24) * 0.08, 'firon', n=8, caps=(False, False))
        FL.bar(K, (-78.33, 1.48, 4.2), (-78.2, 1.55, 4.2), 0.012, 'firon'); FL.bar(K, (-78.07, 1.48, 4.2), (-78.2, 1.55, 4.2), 0.012, 'firon')
        for (zz, s) in ((3.55, -1), (4.85, 1)):  # the roof: two plank slopes off a ridge on the posts
            p = [(-79.45, 2.6, zz), (-76.95, 2.6, zz), (-76.95, 2.97, 4.2), (-79.45, 2.97, 4.2)]
            if s < 0: p = [p[1], p[0], p[3], p[2]]
            FL.both(K, p, 'fwood')
        FL.bar(K, (-79.5, 2.99, 4.2), (-76.9, 2.99, 4.2), 0.07, 'fwooddark')
    # ---- the flag's mast: a stone foot, a dark mast with a gilt ball, the halyard down to a cleat
    for b in groups.get('pole', []):
        x, z = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2
        K.box((x - 0.35, 0, z - 0.35), (x + 0.35, 0.4, z + 0.35), {'all': 'fquoin'})
        FL.tube(K, (x, 0.4, z), (x, 10.9, z), 0.1, 0.065, 'fwooddark', n=8, caps=(False, True))
        ball((x, 11.0, z), 0.12, 'fbrass')
        FL.bar(K, (x + 0.08, 10.85, z), (x + 0.11, 1.3, z), 0.012, 'frope')
        FL.bar(K, (x + 0.09, 1.25, z - 0.08), (x + 0.09, 1.25, z + 0.08), 0.04, 'firon')
    # ---- flagstones in the courtyard (S&D's is flat ground; Islands' rolls with the dunes, so it stays sand)
    if sd: K.quad([(-85.0, 0.02, 11.0), (-69.0, 0.02, 11.0), (-69.0, 0.02, -11.0), (-85.0, 0.02, -11.0)], 'fflag', tile=1.3, sub=2.0)  # (2 cm up: 4 mm lost to the sand at range)
    K.finish(os.path.join(OUTDIR, kind + '.glb'))


for kind in ([a for a in argv if a in ('fort', 'fort_sd')] or ['fort', 'fort_sd']):
    build(kind)
