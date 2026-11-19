# SPOOKY FOREST (18 Nov 2026), the web map "forest" ("Scary Forest") brought back for Roblox. The owner: "We need more
# map variety ... bring back spooky forest and back room!!". The hit boxes, spawns and water, in studs local to the
# arena's origin, as plain Python: the plan (arena_plan.py), the offline checks (arena_check.py) and the kit
# (forest_models.py) read the same numbers.
#
# The layout is the web's (tools/roblox/arenas/forest.json, written by webmap_dump.mjs from shared/map.js), x3 like
# every web port, cropped to the part a Rivals-style match needs: the web's property line was 200 x 168 m with the
# team lots at its far corners (520 studs apart); this keeps web x -80..92, z -66..64 (516 x 390 studs) with
# everything that gives the map its identity: the abandoned cabin, the campsite, the clearing with its standing stones,
# the fire lookout tower, the radio mast yard, the dock and the lake, the dirt road with the broken-down car and the
# fallen tree, the hunting stand. Shifted so the crop sits round the origin (OFFX, OFFZ).
#   teams: attackers come in on the south-west (behind the campsite, by the road), defenders on the north-east (behind
#   the lookout tower). Three lanes fall out of the web's own paths: west past the cabin and the hunting stand, middle
#   through the clearing, east along the road, the lake shore and the mast yard. Matches swaps the ends every round.
# Dropped (gags and anything with words): the office chair and the water cooler in the clearing, the HR memo board, the
# TV, the map sheet, every sign, the property-line stakes' orange tops (the crop's edge has its own rail fence).
# The ground is the web's shaped forest floor (shared/terrain.js heightfield): hit boxes merged from its 1 m cells,
# the kit draws it smooth. The lake (east of the shore) gets a real bed that shelves away to a swimmable depth.
# Wall box (PORT-PLAN section 36, tools/roblox/wallbox.py): no lid, the sky line, walls 30 studs out; a step to the
# woods' height behind the west, north and south edges (a ledge); none over the lake: the walls stand in the water.
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wallbox as WB

S = 3.0
D = json.load(open(os.path.join(HERE, 'arenas', 'forest.json')))
CROP = (-80.0, -66.0, 92.0, 64.0)          # web metres: x0, z0, x1, z1
OFFX, OFFZ = -18.0, 3.0                     # studs: puts the crop round the origin
X_EDGE, Z_EDGE = 258.0, 195.0               # the crop's half sizes, studs
SH = 72.0                                   # the web's lake shore (x, m)
SHORE = SH * S + OFFX                       # 198
EDGE_TOP, EDGE_SEEN = 42.0, 10.0            # the step's top (the woods behind it), how high the woods explain it
BASE = -24.0
WATER_Y = -0.9                              # the lake's surface (the web's lakewater top, -0.3 m)
LID = 150.0
TOWER_FLOOR = 12.368 * S                    # the lookout's cab floor (web 12.368 m)

def lx(x): return x * S + OFFX
def lz(z): return z * S + OFFZ
def wbox(b): return (lx(b['min'][0]), b['min'][1] * S, lz(b['min'][2]), lx(b['max'][0]), b['max'][1] * S, lz(b['max'][2]))
def in_crop(x, z, m=0.0): return CROP[0] - m <= x <= CROP[2] + m and CROP[1] - m <= z <= CROP[3] + m

# ---------------------------------------------------------------- the palette (look and impacts): web mat -> hex
COL = {
    'ground': '6e6852', 'needles': '6e6852', 'trail': '7a705a', 'dirtroad': '7c6c56', 'mud': '5b5345', 'gravel': '8c877d',
    'bark': '6c5948', 'bark2': '5f5043', 'deadbark': '8c8781', 'birch': 'd9d5cc', 'pine': '4f6a4b', 'pine2': '5b7551',
    'birchleaf': '7c8f5d', 'fern': '5f7a4c', 'bush': '566f48',
    'logwall': '7b6047', 'logside': '6f5741', 'logend': 'b39572', 'planks': '8a7056', 'cabinroof': '625e59', 'cabinroof2': '6d6863',
    'stonebase': '8f8a82', 'rockf': '86837a', 'rockmoss': '6f7a5f', 'rootball': '6a5646',
    'towerwood': '7c6b56', 'metal': '8d9196', 'chrome': 'b8bcc1', 'chainlink': '9a9ea2', 'cable': '45464a',
    'mastred': '9b4b43', 'mastwhite': 'd8d5cf', 'mastlight': 'ff5a46', 'shedmetal': '8a8f86', 'roofg': '707470',
    'concrete': 'a19d96', 'generator': '7a7e6c', 'carrust': '8a5b45', 'glassdark': '3a444e', 'tire': '3d3d40',
    'hazard2': 'ffa448', 'tentorange': 'b0733f', 'tentgreen': '627753', 'tentdark': '45483f', 'boatwood': '7f6551',
    'canoe': '8c624a', 'crate': 'a08662', 'cooler': '6c8888', 'white': 'd6d4ce', 'ash': '5c5a58', 'bedsheet': 'b9b3a7',
    'lantern': 'ffd08c', 'cabinwin': 'ffcf8f',
}
# the hit boxes' Roblox materials (impacts: dust, chips, sounds)
RBX = {'ground': 'Ground', 'needles': 'Ground', 'dirtroad': 'Ground', 'mud': 'Mud', 'gravel': 'Pebble',
       'bark': 'Wood', 'bark2': 'Wood', 'deadbark': 'Wood', 'birch': 'Wood', 'logwall': 'Wood', 'logside': 'Wood',
       'logend': 'Wood', 'rootball': 'Ground', 'planks': 'WoodPlanks', 'towerwood': 'WoodPlanks', 'boatwood': 'WoodPlanks',
       'canoe': 'Wood', 'crate': 'WoodPlanks', 'cabinroof': 'Slate', 'cabinroof2': 'Slate', 'stonebase': 'Cobblestone',
       'rockf': 'Rock', 'rockmoss': 'Rock', 'metal': 'Metal', 'chrome': 'Metal', 'chainlink': 'DiamondPlate',
       'cable': 'Rubber', 'mastred': 'Metal', 'mastwhite': 'Metal', 'mastlight': 'Glass', 'shedmetal': 'CorrodedMetal',
       'roofg': 'CorrodedMetal', 'concrete': 'Concrete', 'generator': 'Metal', 'carrust': 'CorrodedMetal',
       'glassdark': 'Glass', 'tire': 'Rubber', 'hazard2': 'Glass', 'tentorange': 'Fabric', 'tentgreen': 'Fabric',
       'tentdark': 'Fabric', 'cooler': 'SmoothPlastic', 'white': 'SmoothPlastic', 'ash': 'Ground', 'bedsheet': 'Fabric',
       'lantern': 'Glass', 'ledge': 'SmoothPlastic', 'bound': 'SmoothPlastic'}
MATS = {k: (RBX.get(k, 'SmoothPlastic'), COL.get(k, 'c8c4bd'), k) for k in set(RBX) | set(COL)}
MATS['ledge'] = WB.LEDGE
MATS['bound'] = WB.BOUND

# ---------------------------------------------------------------- what the web has that this port leaves out
DROP_MATS = {'officechair', 'hrboard', 'tvstatic', 'mapsheet', 'coolerwater', 'toyorange',
             'signtower', 'signmast', 'signranger', 'signtrail', 'signturn', 'mud', 'needles'}
CONVERT = {'radiopanel': 'metal'}
# (web metres x0, z0, x1, z1, top below): the clearing's office chair and its water cooler
DROP_AT = [(-2.6, -8.45, -1.65, -7.5, 1.6), (5.9, -6.1, 6.7, -5.3, 2.0)]
# the signs' posts and boards (adSign: two posts and a board 2.8 m along its line), web metres: x, z, along
SIGNS = [(19.4, -45.8, 'x'), (15.0, -64.4, 'x'), (41.4, 8.5, 'z')]

def dropped(b):
    if b['mat'] in DROP_MATS or b.get('ter'): return True
    cx, cz, cy = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2, (b['min'][1] + b['max'][1]) / 2
    for (x0, z0, x1, z1, ytop) in DROP_AT:
        if x0 <= cx <= x1 and z0 <= cz <= z1 and b['max'][1] <= ytop: return True
    if b['mat'] in ('logside', 'planks'):
        for (sx, sz, al) in SIGNS:
            da, dc = (abs(cx - sx), abs(cz - sz)) if al == 'x' else (abs(cz - sz), abs(cx - sx))
            if da <= 1.6 and dc <= 0.3 and cy < 3.0: return True
    return False

# ---------------------------------------------------------------- spawns (web metres; heights found on the hit boxes)
TEAM_WEB = {
    # attackers: behind the campsite, between it and the road (south-west); defenders: behind the lookout tower (north-east)
    # (19 Nov 2026: three moved 0.5 to 2.5 m to stand behind cover once the trunks' hit shapes were no wider than the bark)
    'att': [(-46, 42), (-42, 45), (-38, 43), (-34.5, 46), (-30, 44), (-24, 46), (-36, 49.5), (-46, 47)],
    'def': [(12, -58), (16, -61), (20, -59), (24, -62), (28, -60), (32, -58), (36, -61), (20, -63.5)],
    # a 1v1v1's third side: the radio mast yard (east)
    'mid': [(50, 10), (58, 2), (52, -2), (60, 10)],
}
_ac = [sum(p[0] for p in TEAM_WEB['att']) / 8, sum(p[1] for p in TEAM_WEB['att']) / 8]
_dc = [sum(p[0] for p in TEAM_WEB['def']) / 8, sum(p[1] for p in TEAM_WEB['def']) / 8]
_n = math.hypot(_dc[0] - _ac[0], _dc[1] - _ac[1])
FACE = {'att': ((_dc[0] - _ac[0]) / _n, (_dc[1] - _ac[1]) / _n), 'def': ((_ac[0] - _dc[0]) / _n, (_ac[1] - _dc[1]) / _n), 'mid': (-1.0, 0.0)}
EXTRA_FFA = [(-62, 40), (-10, 40), (34, 14), (-32, -8), (-64, -40), (2, 46), (44, -50)]
FFA_WEB = [(p[0], p[1], p[2]) for p in D['spawns'] if in_crop(p[0], p[2], -2.0)] + [(x, 0.2, z) for (x, z) in EXTRA_FFA]
ALL_SPAWN_XZ = [(p[0], p[2]) for p in FFA_WEB] + [p for v in TEAM_WEB.values() for p in v]

def near_spawn(x0, z0, x1, z1, r=2.2):
    for (sx, sz) in ALL_SPAWN_XZ:
        if x0 - r < sx < x1 + r and z0 - r < sz < z1 + r: return True
    return False

# ================================================================ the hit boxes
SOLID, ROT, SPAWNS, PADS, WATER, NOTES = [], [], [], [], [], []
TEAM = {'att': [], 'def': [], 'mid': []}
CLEARED = []         # (web x, z) of trees taken out for a spawn (the kit skips their look too)

def box(x0, y0, z0, x1, y1, z1, m):
    SOLID.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), m))

def clip(b):
    """a local box cut to the crop (land) or the lake (east of the shore, to the walls)"""
    x0, y0, z0, x1, y1, z1 = b
    X, Z, P = X_EDGE, Z_EDGE, WB.PUSH
    xa, xb = max(x0, -X), min(x1, X + P)
    za, zb = max(z0, -Z - P), min(z1, Z + P)
    if (xa + xb) / 2 < SHORE: za, zb = max(z0, -Z), min(z1, Z)       # (on land: only inside the crop)
    if xb - xa < 1e-3 or zb - za < 1e-3: return None
    return (xa, y0, za, xb, y1, zb)

# ---------------------------------------------------------------- collision that is the shape you see (19 Nov 2026)
# The owner (18 Nov): "forest has really janky hitboxes when running around ... you'll be stopped by either trees or
# something invisible on the ground". The web's boxes are square, the kit draws most of them round: every trunk's box
# stood out of its bark at the corners (a pine's 2.2-stud box round a 0.9-radius trunk: 0.66 studs of air at each
# corner), the boulders and logs were round over square boxes, and the floor was a staircase of 0.3-stud steps under a
# smooth slope. So the Forest's hit shapes now follow the drawing (forest_models.py draws the same numbers):
#   trunks: two upright cylinders inside the drawn bark (cos(pi/sides) of the drawn radius), nothing on canopies;
#   boulders: upright cylinders (and a box between them on long ones) inside the drawn lumpy rock, its low-poly faces
#     allowed for; rocks no higher than ROCK_LOW over the floor take shots but don't stop you;
#   logs, posts, poles, drums, tyres: cylinders inside the drawn ones; a log lying on the floor no higher than LOG_LOW
#     (the fallen trunks, the camp benches) takes shots and stops nothing, so a sprint or a slide carries you through
#     instead of stopping you dead (a ramp over them was tried on paper: at a sprint it throws you several studs up);
#     the tree across the road (3.3 high) stays a log you jump;
#   the floor: the drawn 2 m quads themselves, flat ones as boxes, sloped ones as tilted boxes, twisted ones as two
#     triangles (four wedges): no steps that aren't drawn (lips between neighbouring pieces: 0.4 studs at most).
# Flags (WebArena): "" stops you and takes shots, "c" stops you and takes no shots, "q" takes shots and stops nothing.
HULL_IN = []         # (kind, local box, web mat, web box): boxes replaced by hull shapes once the floor is known
CYL = []             # (ax, ay, az, bx, by, bz, radius, mat, flags): a cylinder from a to b
TILT = []            # (px, py, pz, xx, xy, xz, yx, yy, yz, sx, sy, sz, mat, kind 'b' | 'w', flags): a turned box or wedge
ROCK_LOW = 2.0       # boulders this high over the floor or lower (camp ring stones, pebbles): they take shots only
LOG_LOW = 2.6        # logs lying on the floor this high or lower (the fallen trunks, the camp benches): the same

def _sides(c):
    return (c[3] - c[0], c[4] - c[1], c[5] - c[2])

def hulled(c, mat, b):
    """True when this kept web box gets a hull shape instead (dress() in forest_models.py draws it round)"""
    if b.get('pv') in ('pine', 'birch', 'deadtree'): return True             # trunks: from the drawn trees, below
    if mat in ('rockf', 'rockmoss'): HULL_IN.append(('rock', c, mat, b)); return True
    sx, sy, sz = _sides(c)
    s = (sx, sy, sz)
    if mat == 'rootball': HULL_IN.append(('rootball', c, mat, b)); return True
    if mat in ('logside', 'logend', 'deadbark', 'bark', 'bark2', 'cable'):
        if mat == 'logend' and min(s) < 0.5 and sorted(s)[1] > 1.5: HULL_IN.append(('disc', c, mat, b)); return True
        if mat == 'logend' and sy < 0.5: return False                         # (firewood rows: drawn as boxes)
        big = max(s)
        if sy == big and sy > 2.5 * max(sx, sz): HULL_IN.append(('post', c, mat, b)); return True
        if sx == big or sz == big: HULL_IN.append(('log', c, mat, b)); return True
        return False
    if mat in ('mastred', 'mastwhite'): HULL_IN.append(('mast', c, mat, b)); return True
    if mat == 'metal' and sy > 2.0 and max(sx, sz) < 0.6: HULL_IN.append(('mpost', c, mat, b)); return True
    if mat == 'tire': HULL_IN.append(('tire', c, mat, b)); return True
    return False

KEPT = []            # (local box, web mat, web box) of every web box kept: the kit dresses from these
for b in D['boxes']:
    if dropped(b): continue
    mat = CONVERT.get(b['mat'], b['mat'])
    if b.get('pv') in ('pine', 'birch', 'deadtree'):
        cx, cz = (b['min'][0] + b['max'][0]) / 2, (b['min'][2] + b['max'][2]) / 2
        if not in_crop(cx, cz): continue
        if near_spawn(b['min'][0], b['min'][2], b['max'][0], b['max'][2]): CLEARED.append((cx, cz)); continue
    c = clip(wbox(b))
    if c is None: continue
    KEPT.append((c, mat, b))
    if not hulled(c, mat, b): box(*c, mat)

# new cover (web metres x, z, size): a boulder outcrop between the defenders' spawns and the lookout, so no attacker spawn
# sees a defender spawn (the web's lots were 520 studs apart; these are 330)
EXTRA_ROCKS = [(15.5, -54.0, 1.7), (20.5, -55.8, 1.5), (11.5, -55.6, 1.3)]
# (19 Nov 2026) with the trunks' hit shapes no wider than the bark, 18 of the 128 spawn-to-spawn lines threaded between
# the trees: ten more outcrops close them, six in front of the attackers' spawns (by the campsite), four in the woods
# below the lookout (found by a search over spots along the open lines with the rocks' real hulls, clear of spawns,
# trees, the road and each other)
EXTRA_ROCKS += [(-24.6, 43.2, 1.5), (15.1, -48.7, 1.5), (-38.9, 39.1, 1.5), (-31.5, 40.6, 1.5), (-32.1, 31.1, 1.5), (-23.6, 29.3, 1.5),
                (21.0, -38.1, 1.5), (3.2, -33.6, 1.5), (9.7, -38.7, 1.5), (-22.1, 38.5, 1.5)]
for (x, z, s) in EXTRA_ROCKS:
    for (a0, y0, c0, a1, y1, c1, m) in ((x - s, -1.0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'rockf'),
                                        (x - s * 0.7, s * 1.1, z - s * 0.5, x + s * 0.5, s * 1.5, z + s * 0.6, 'rockf'),
                                        (x + s * 0.7, -1.0, z + s * 0.4, x + s * 1.5, s * 0.7, z + s * 1.2, 'rockmoss')):
        c = (lx(a0), y0 * S, lz(c0), lx(a1), y1 * S, lz(c1))
        KEPT.append((c, m, {'min': [a0, y0, c0], 'max': [a1, y1, c1], 'mat': m, 'av': 'rocks_forest'}))
        hulled(c, m, {})

# the forest floor: the web's heightfield (on its 2 m vertices, as the kit draws it), every 1 m cell a box up to the
# middle of its corners (to 0.3 studs), cells of the same top merged into rectangles (4,451 web boxes over the whole
# map; here only the crop's)
T = D['terrain']
TX0, TZ0, TNX, TNZ, TH = T['x0'], T['z0'], T['nx'], T['nz'], T['H']
TVZ = TNZ + 1
def h_at(i, j): return TH[i * TVZ + j]
def h2(i, j):
    """the ground the kit draws: the web's heights on every second vertex (a 2 m grid), straight between them. the hit
    boxes follow this surface (so feet land where it's drawn: the 1 m web surface strays up to 0.9 studs from it)"""
    i0, j0 = i - i % 2, j - j % 2
    i1, j1 = min(i0 + 2, TNX), min(j0 + 2, TNZ)
    fu = (i - i0) / 2.0 if i1 > i0 else 0.0
    fv = (j - j0) / 2.0 if j1 > j0 else 0.0
    a, b, c, d = h_at(i0, j0), h_at(i1, j0), h_at(i0, j1), h_at(i1, j1)
    return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv
GROUND = []          # the old staircase floor (1 m cells to 0.3 studs): only the plan and the offline checks use it now
def ground_plan():
    i0 = max(0, int(math.floor(CROP[0] - TX0))); i1 = min(TNX, int(math.ceil(min(CROP[2], SH) - TX0)))
    j0 = max(0, int(math.floor(CROP[1] - TZ0))); j1 = min(TNZ, int(math.ceil(CROP[3] - TZ0)))
    nx, nz = i1 - i0, j1 - j0
    top = [[round((h2(i0 + i, j0 + j) + h2(i0 + i + 1, j0 + j) + h2(i0 + i, j0 + j + 1) + h2(i0 + i + 1, j0 + j + 1)) / 4 * S / 0.3) * 0.3
            for j in range(nz)] for i in range(nx)]
    used = [[False] * nz for _ in range(nx)]
    for i in range(nx):
        for j in range(nz):
            if used[i][j]: continue
            t = top[i][j]
            w = 1
            while i + w < nx and not used[i + w][j] and top[i + w][j] == t: w += 1
            h = 1
            while j + h < nz and all(not used[i + k][j + h] and top[i + k][j + h] == t for k in range(w)): h += 1
            for k in range(w):
                for l in range(h): used[i + k][j + l] = True
            c = clip((lx(TX0 + i0 + i), -9.0, lz(TZ0 + j0 + j), lx(TX0 + i0 + i + w), round(t, 2), lz(TZ0 + j0 + j + h)))
            if c: GROUND.append(c + ('ground',))
ground_plan()

# the floor you walk on (19 Nov 2026): the kit's own 2 m quads (forest_models.ground draws them at the web's heights
# + 0.03). a quad within FLAT_TOL of level is a box (level neighbours of one height merged); a sloped one a box turned
# to its plane; one twisted more than TWIST_TOL (its plane misses a corner by that much) two triangles on the diagonal
# the kit's quads are cut on (corner (i, j) to (i + 2, j + 2)), each two wedges. under every piece: solid down a way
FLAT_TOL, TWIST_TOL, GTHICK, GLIFT = 0.12, 0.2, 3.0, 0.03
QUAD = {}            # (i, j) of a quad's low corner -> ('flat', top) | ('tilt', h0, a, b) | ('tri', c00, c10, c01, c11)
GI = (max(0, int(math.floor(CROP[0] - TX0))), min(TNX, int(math.ceil(min(CROP[2], SH) - TX0))),
      max(0, int(math.floor(CROP[1] - TZ0))), min(TNZ, int(math.ceil(CROP[3] - TZ0))))

def _add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def _sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def _mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def _cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def _unit(a):
    n = math.sqrt(_dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n)

def turned(pos, X, Y, size, mat, kind='b', flags=''):
    TILT.append(tuple(round(v, 4) for v in (*pos, *X, *Y, *size)) + (mat, kind, flags))

def tri_wedges(a, b, c, thick, mat, flags=''):
    """a triangle as two wedges (the usual Roblox way: split on the foot of the longest side's height), each `thick`
    deep under the triangle (its top face is the triangle)"""
    ab, ac, bc = _sub(b, a), _sub(c, a), _sub(c, b)
    abd, acd, bcd = _dot(ab, ab), _dot(ac, ac), _dot(bc, bc)
    if abd > acd and abd > bcd: c, a = a, c
    elif acd > bcd and acd > abd: a, b = b, a
    ab, ac, bc = _sub(b, a), _sub(c, a), _sub(c, b)
    right = _unit(_cross(ac, ab))
    up = _unit(_cross(bc, right))
    back = _unit(bc)
    height = abs(_dot(ab, up))
    nup = right if right[1] > 0 else _mul(right, -1)
    down = _mul(nup, -thick / 2)
    turned(_add(_mul(_add(a, b), 0.5), down), right, up, (thick, height, abs(_dot(ab, back))), mat, 'w', flags)
    turned(_add(_mul(_add(a, c), 0.5), down), _mul(right, -1), up, (thick, height, abs(_dot(ac, back))), mat, 'w', flags)

def ground():
    i0, i1, j0, j1 = GI
    flats = {}
    for i in range(i0 - i0 % 2, i1, 2):
        for j in range(j0 - j0 % 2, j1, 2):
            c00, c10 = h_at(i, j) * S + GLIFT, h_at(i + 2, j) * S + GLIFT
            c01, c11 = h_at(i, j + 2) * S + GLIFT, h_at(i + 2, j + 2) * S + GLIFT
            cs = (c00, c10, c01, c11)
            if max(cs) - min(cs) < FLAT_TOL:
                t = round(sum(cs) / 4 / 0.05) * 0.05
                QUAD[(i, j)] = ('flat', t); flats[(i, j)] = t
                continue
            x0, xa, z0, za = lx(TX0 + i), lx(TX0 + i + 2), lz(TZ0 + j), lz(TZ0 + j + 2)
            w = xa - x0
            twist = abs(c00 + c11 - c10 - c01) / 4
            if twist <= TWIST_TOL:
                a = ((c10 - c00) + (c11 - c01)) / 2 / w
                b = ((c01 - c00) + (c11 - c10)) / 2 / w
                h0 = sum(cs) / 4
                QUAD[(i, j)] = ('tilt', h0, a, b)
                Y = _unit((-a, 1.0, -b))
                X = _unit((1.0, a, 0.0))
                Z = _cross(X, Y)
                pos = _add(((x0 + xa) / 2, h0, (z0 + za) / 2), _mul(Y, -GTHICK / 2))
                turned(pos, X, Y, ((w + 0.2) * math.sqrt(1 + a * a), GTHICK, (w + 0.2) / abs(Z[2])), 'ground')
            else:
                QUAD[(i, j)] = ('tri', c00, c10, c01, c11)
                p00, p10, p01, p11 = (x0, c00, z0), (xa, c10, z0), (x0, c01, za), (xa, c11, za)
                tri_wedges(p00, p01, p11, 2.0, 'ground')
                tri_wedges(p00, p11, p10, 2.0, 'ground')
    # the level quads, merged into rectangles of one height
    used = set()
    for i in range(i0 - i0 % 2, i1, 2):
        for j in range(j0 - j0 % 2, j1, 2):
            if (i, j) not in flats or (i, j) in used: continue
            t = flats[(i, j)]
            w = 2
            while (i + w, j) in flats and (i + w, j) not in used and flats[(i + w, j)] == t: w += 2
            h = 2
            while all((i + k, j + h) in flats and (i + k, j + h) not in used and flats[(i + k, j + h)] == t for k in range(0, w, 2)): h += 2
            for k in range(0, w, 2):
                for l in range(0, h, 2): used.add((i + k, j + l))
            box(lx(TX0 + i), -9.0, lz(TZ0 + j), lx(TX0 + i + w), round(t, 2), lz(TZ0 + j + h), 'ground')
ground()

def ground_y(x, z):
    """the floor's height at a local spot (None off the shaped floor: the lake)"""
    fi, fj = (x - OFFX) / S - TX0, (z - OFFZ) / S - TZ0
    i, j = int(math.floor(fi / 2)) * 2, int(math.floor(fj / 2)) * 2
    q = QUAD.get((i, j))
    if q is None: return None
    if q[0] == 'flat': return q[1]
    u, v = (fi - i) / 2.0, (fj - j) / 2.0           # 0..1 across the quad
    if q[0] == 'tilt':
        h0, a, b = q[1], q[2], q[3]
        return h0 + a * (u - 0.5) * 2 * S + b * (v - 0.5) * 2 * S
    c00, c10, c01, c11 = q[1:]
    if v >= u: return c00 + (c11 - c01) * u + (c01 - c00) * v        # (the triangle 00, 01, 11)
    return c00 + (c10 - c00) * u + (c11 - c10) * v                    # (the triangle 00, 11, 10)

def floor_min(points):
    ys = [ground_y(x, z) for (x, z) in points]
    ys = [y for y in ys if y is not None]
    return min(ys) if ys else 0.0

# ---------------------------------------------------------------- the hull shapes (see "collision that is the shape you see")
def insc(sides): return math.cos(math.pi / sides)
def cylv(x, z, y0, y1, r, mat, flags=''):
    CYL.append(tuple(round(v, 3) for v in (x, y0, z, x, y1, z, r)) + (mat, flags))
def cylh(a, b, r, mat, flags=''):
    CYL.append(tuple(round(v, 3) for v in (*a, *b, r)) + (mat, flags))

def tree_hulls():
    """the drawn trunks (forest_models.trees: pine / birch / dead, their radii and sides), as two upright cylinders each:
    one to head height at the bark's radius there, one thinner above"""
    n = 0
    for p in D['props']:
        kind = p['id']
        if kind not in ('pine', 'birch', 'deadtree'): continue
        wx, wy, wz = p['a']
        if not in_crop(wx, wz): continue
        if any(abs(wx - cx) < 0.3 and abs(wz - cz) < 0.3 for (cx, cz) in CLEARED): continue
        x, y, z = lx(wx), wy * S, lz(wz)
        ht = p['hi'][1] * S
        if kind == 'pine': base, r0, H, r2, sides, mat, top = y - 1.5, 0.9, ht * 0.62 + 1.5, 0.54, 7, 'bark', y + ht * 0.9
        elif kind == 'birch': base, r0, H, r2, sides, mat, top = y - 1.0, 0.62, ht * 0.85 + 1.0, 0.45, 8, 'birch', y + ht * 0.85
        else:
            h95 = ht * 0.95
            base, r0, H, r2, sides, mat, top = y - 1.0, 0.85, h95 + 1.0, 0.45, 6, 'deadbark', y + h95
        rad = lambda yy: r0 + (r2 - r0) * min(1.0, max(0.0, (yy - base) / H))
        knee = y + 5.5
        cylv(x, z, base, knee, insc(sides) * rad(knee) - 0.03, mat)
        cylv(x, z, knee, max(knee + 1.0, top), insc(sides) * r2 - 0.03, mat)
        n += 1
    return n

def rock_groups(items):
    """the kit's boulders (forest_models.rocks draws from this): touching boxes of one outcrop are one boulder per
    material. -> [(drawn box, mat, seed, icosphere subdivisions)]"""
    par = list(range(len(items)))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i, (a, _) in enumerate(items):
        for j in range(i + 1, len(items)):
            b = items[j][0]
            if a[0] <= b[3] + 0.1 and b[0] <= a[3] + 0.1 and a[2] <= b[5] + 0.1 and b[2] <= a[5] + 0.1 and a[1] <= b[4] + 0.1 and b[1] <= a[4] + 0.1:
                par[find(i)] = find(j)
    groups = {}
    for i, it in enumerate(items): groups.setdefault(find(i), []).append(it)
    out = []
    for k, g in enumerate(groups.values()):
        for mat in ('rockf', 'rockmoss'):
            bs = [b for (b, m) in g if m == mat]
            if not bs: continue
            bb = (min(b[0] for b in bs), min(b[1] for b in bs), min(b[2] for b in bs), max(b[3] for b in bs), max(b[4] for b in bs), max(b[5] for b in bs))
            sx, sy, sz = bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]
            if len(g) == 1 and sy > 1.4 * max(sx, sz):                          # a standing stone: a rough monolith
                x0, y0, z0, x1, y1, z1 = bb
                out.append(((x0 - 0.2, y0 - sy * 0.1, z0 - 0.2, x1 + 0.2, y1 + sy * 0.05, z1 + 0.2), mat, 2000 + k, 2))
            else:
                out.append((bb, mat, 1000 + k * 7 + (mat == 'rockmoss'), 2 if max(sx, sy, sz) > 2.5 else 1))
    return out

def _fib(n):
    g = math.pi * (3 - math.sqrt(5))
    for k in range(n):
        y = 1 - 2 * (k + 0.5) / n
        r = math.sqrt(max(0.0, 1 - y * y))
        yield (math.cos(g * k) * r, y, math.sin(g * k) * r)
FIB = list(_fib(2400))

def rock_surface(bb, seed, sub):
    """points on the drawn boulder's sides and top (forest_models.rock: the icosphere's directions pushed by the same
    noise and scaled; the foot, folded up into a dish under the rock, left out: 19 Nov, its points near the axis made
    every hull's main cylinder vanish), pulled in by the low-poly mesh's own inset (icosphere 1: 12 points, its faces 0.795 of the way out;
    2: 42 points, 0.934)"""
    import random as _r
    x0, y0, z0, x1, y1, z1 = bb
    sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
    r = _r.Random(seed)
    ph = [r.random() * 6.28 for _ in range(4)]
    f = 0.934 if sub >= 2 else 0.795
    c = ((x0 + x1) / 2, y0 + sy * 0.42, (z0 + z1) / 2)
    pts = []
    for (dx, dy, dz) in FIB:
        n = 0.09 * math.sin(3.1 * dx + ph[0]) * math.cos(2.7 * dz + ph[1]) + 0.06 * math.sin(5.3 * dy + ph[2]) + 0.05 * math.cos(4.1 * (dx + dz) + ph[3])
        vx, vy, vz = dx * (1 + n) * sx * 0.58, dy * (1 + n) * sy * 0.62, dz * (1 + n) * sz * 0.58
        if vy < -sy * 0.3: continue      # (the foot: folded up into a shallow dish under the rock, not its sides)
        pts.append((c[0] + vx * f, c[1] + vy * f, c[2] + vz * f))
    return c, pts, f

def rock_hull(bb, mat, seed, sub):
    c, pts, f = rock_surface(bb, seed, sub)
    sx, sy, sz = bb[3] - bb[0], bb[4] - bb[1], bb[5] - bb[2]
    g = floor_min([(c[0], c[2]), (bb[0], bb[2]), (bb[3], bb[5]), (bb[0], bb[5]), (bb[3], bb[2])])
    top = max(p[1] for p in pts)
    flags = 'q' if top - g <= ROCK_LOW else ''
    Ay = 0.62 * sy * f
    ya, yb, yc = c[1] - 0.45 * Ay, c[1] + 0.45 * Ay, c[1] + 0.8 * Ay
    trim = 0.9 if sub < 2 else 0.96       # (the mesh's flat faces between its points: checked against the mesh in forest_models)
    def inr(ax, az, lo, hi):
        return trim * min(math.hypot(p[0] - ax, p[2] - az) for p in pts if lo <= p[1] <= hi) - 0.05
    centres = [(c[0], c[2])]
    if sx > 1.35 * sz or sz > 1.35 * sx:
        along_x = sx > sz
        t = 0.58 * f * (max(sx, sz) - min(sx, sz))
        centres += [(c[0] + t, c[2]), (c[0] - t, c[2])] if along_x else [(c[0], c[2] + t), (c[0], c[2] - t)]
    rs = [inr(ax, az, ya, yb) for (ax, az) in centres]
    rc = inr(c[0], c[2], yb, yc)
    # (19 Nov) a main part topping out within the step-up's reach (Move.client lifts you onto lips up to 1.8 studs) with
    # the narrower top on it would be a ledge to hop onto and a cap to hit: such a rock is one narrower piece to its top
    one = yb - g <= 1.9 and rc > 0.3 and rs[0] > 0.25
    k = rc / rs[0] if one else 1.0
    top_y = yc if one else yb
    rs = [r * k for r in rs]
    for (ax, az), r in zip(centres, rs):
        if r > 0.25: cylv(ax, az, g - 0.6, top_y, r, mat, flags)
    if len(centres) == 3 and all(r > 0.25 for r in rs):
        w = min(rs)
        lo, hi = centres[2], centres[1]
        size = ((hi[0] - lo[0]) if sx > sz else 2 * w, top_y - (g - 0.6), 2 * w if sx > sz else (hi[1] - lo[1]))
        turned((c[0], (top_y + g - 0.6) / 2, c[2]), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), size, mat, 'b', flags)
    if not one and rc > 0.3: cylv(c[0], c[2], yb, yc, rc, mat, flags)
    return top - g, flags

ROCKS = []           # (drawn box, mat, seed, sub, height over the floor, flags): the kit draws them, the plan lists them
def hulls():
    nt = tree_hulls()
    rocks = rock_groups([(c, mat) for (kind, c, mat, b) in HULL_IN if kind == 'rock'])
    for (bb, mat, seed, sub) in rocks:
        hgt, fl = rock_hull(bb, mat, seed, sub)
        ROCKS.append((bb, mat, seed, sub, round(hgt, 2), fl))
    nl = 0
    for (kind, c, mat, b) in HULL_IN:
        x0, y0, z0, x1, y1, z1 = c
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
        if kind == 'rootball':                                      # (blob, 12-point icosphere: a box well inside it)
            k = 0.55
            box(cx - sx * k / 2, y0, cz - sz * k / 2, cx + sx * k / 2, y0 + sy * (0.5 + k / 2), cz + sz * k / 2, mat)
        elif kind == 'post':                                        # an upright log or pole: 8 sides at 1.05 x its box
            cylv(cx, cz, y0, y1, insc(8) * max(sx, sz) / 2 * 1.05 - 0.02, mat)
        elif kind == 'disc':                                        # a log's cut end (10 sides)
            s = sorted((sx, sy, sz)); r = insc(10) * s[1] / 2 - 0.02
            ax = (sx, sy, sz).index(s[0])
            a, b2 = ((x0, cy, cz), (x1, cy, cz)) if ax == 0 else (((cx, cy, z0), (cx, cy, z1)) if ax == 2 else ((cx, y0, cz), (cx, y1, cz)))
            g = floor_min([(cx, cz)])
            cylh(a, b2, r, mat, 'q' if (y0 <= g + 0.6 and y1 - g <= LOG_LOW) else '')
        elif kind == 'log':                                         # lying along x or z (10 sides)
            along = 'x' if sx >= sz else 'z'
            r = insc(10) * min(sy, sz if along == 'x' else sx) / 2 - 0.02
            a, b2 = ((x0, cy, cz), (x1, cy, cz)) if along == 'x' else ((cx, cy, z0), (cx, cy, z1))
            ln = max(sx, sz)
            pts = [((x0 + (x1 - x0) * k / 6, cz) if along == 'x' else (cx, z0 + (z1 - z0) * k / 6)) for k in range(7)]
            g = floor_min(pts)
            if ln > 3.2 and y0 <= g + 0.6 and y1 - g <= LOG_LOW:    # lying on the floor, knee high: run through it
                cylh(a, b2, r, mat, 'q')
                nl += 1
            else:
                cylh(a, b2, r, mat)
        elif kind == 'mast':
            cylv(cx, cz, y0, y1, insc(6) * 0.42 - 0.02, mat)
        elif kind == 'mpost':
            cylv(cx, cz, y0, y1, insc(6) * max(sx, sz) / 2 * 1.2 - 0.02, mat)
        elif kind == 'tire':
            r = insc(12) * sy / 2 - 0.02
            a, b2 = ((x0, cy, cz), (x1, cy, cz)) if sx < sz else ((cx, cy, z0), (cx, cy, z1))
            cylh(a, b2, r, mat)
    return nt, len(rocks), nl
HULL_COUNTS = hulls()

# the lake bed: shelves away from the shore to a swimmable depth (the web's lake was ankle deep: 0.7 m)
SHELVES = [(SHORE, SHORE + 12.0, -0.66, 'mud'), (SHORE + 12.0, SHORE + 27.0, -1.44, 'mud'),
           (SHORE + 27.0, SHORE + 42.0, -4.5, 'mud'), (SHORE + 42.0, X_EDGE + WB.PUSH, -14.0, 'mud')]
for (xa, xb, top, m) in SHELVES:
    box(xa, BASE, -Z_EDGE - WB.PUSH, xb, top, Z_EDGE + WB.PUSH, m)
# the water (terrain water: JankWater): the swimmable lake inside the walls (they stand in it), and past them the look of
# the lake going on to the far shore (WATER_FAR: the kit writes both into the layout; the plan draws only the first)
WATER.append((SHORE + 12.0, -16.0, -Z_EDGE - WB.PUSH, X_EDGE + WB.PUSH, WATER_Y, Z_EDGE + WB.PUSH))
WATER_FAR = [(X_EDGE + WB.PUSH, -16.0, -720.0, 672.0, WATER_Y, 720.0),
             (SHORE + 12.0, -16.0, -720.0, X_EDGE + WB.PUSH, WATER_Y, -Z_EDGE - WB.PUSH),
             (SHORE + 12.0, -16.0, Z_EDGE + WB.PUSH, X_EDGE + WB.PUSH, WATER_Y, 720.0)]

# ---------------------------------------------------------------- spawns
def floor_at(x, z, ymax):
    best = ground_y(x, z)                       # (the floor: tilted pieces now, not boxes)
    if best is not None and best > ymax: best = None
    for s in SOLID:
        if s[0] <= x <= s[3] and s[2] <= z <= s[5] and s[4] <= ymax:
            best = s[4] if best is None else max(best, s[4])
    return best

def put_spawn(wx, wz, wy=0.2, tower=False):
    x, z = lx(wx), lz(wz)
    ymax = TOWER_FLOOR + 1.0 if tower else wy * S + 2.0
    f = floor_at(x, z, ymax)
    return (round(x, 2), round((f if f is not None else 0.0) + 0.3, 2), round(z, 2))

for p in FFA_WEB:
    tower = p[1] > 10
    SPAWNS.append(put_spawn(p[0], p[2], p[1], tower))
for k, pts in TEAM_WEB.items():
    for (wx, wz) in pts:
        s = put_spawn(wx, wz)
        TEAM[k].append(s + (round(FACE[k][0], 3), round(FACE[k][1], 3)))

NOTES.extend([(lx(-50), lz(-24), 0, 'CABIN'), (lx(-30), lz(26), 0, 'CAMPSITE'), (lx(0), lz(-10), 0, 'CLEARING'),
              (lx(24), lz(-50), 0, 'LOOKOUT'), (lx(52), lz(4), 0, 'MAST YARD'), (lx(82), lz(-36), 0, 'DOCK'),
              (lx(84), lz(24), 0, 'LAKE'), (lx(-20), lz(56), 0, 'ROAD'), (lx(-74), lz(-46), 0, 'STAND'),
              (lx(24), lz(-50), 1, 'LOOKOUT CAB (37)'), (lx(-74), lz(-52), 1, 'STAND (12)'), (lx(-50), lz(-24), 1, 'CABIN ROOF')])

# ================================================================ for the plan (arena_plan.py)
TITLE = 'SPOOKY FOREST (the web forest, cropped)'
BOUNDS = (-X_EDGE - WB.PUSH - 14, X_EDGE + WB.PUSH + 14, -Z_EDGE - WB.PUSH - 14, Z_EDGE + WB.PUSH + 14)
PLAN_PX = 2.0
LEVELS = [('THE FOREST FLOOR (y about 0)', -8.0, 9.0, 0.0), ('UP HIGH: the stand 12, the cabin roof 10-17, the lookout cab 37', 9.0, 60.0, TOWER_FLOOR)]
FLOORS = ('ground', 'mud', 'planks', 'gravel', 'dirtroad', 'concrete', 'stonebase', 'towerwood', 'cabinroof', 'cabinroof2')
COLOURS = {k: tuple(int(COL[k][i:i + 2], 16) for i in (0, 2, 4)) for k in COL}
COLOURS.update({'ground': (120, 112, 88), 'bark': (60, 44, 34), 'bark2': (60, 44, 34), 'birch': (230, 226, 216),
                'deadbark': (150, 146, 140), 'mud': (84, 120, 150), 'logwall': (176, 120, 80), 'towerwood': (196, 160, 120)})
PLAN_NOTE = ('(olive: the forest floor rising over a stud; dark: hollows) the web forest cropped to its middle: attackers in from the south-west (campsite and road), defenders from the north-east '
             '(behind the lookout); lanes west (cabin, hunting stand), middle (the clearing), east (road, lake shore, mast yard); '
             'trunks are cover, canopies only drawn; the lake is swimmable east of the shore')

# ================================================================ the wall box (PORT-PLAN section 36), the lake side open
def forest_box(solid, rot, edge_top, edge_seen):
    X, Z, P, Tk = X_EDGE, Z_EDGE, WB.PUSH, WB.WALL_T
    out = list(solid)
    # the step: behind the west edge, and behind the north and south edges as far as the shore (the woods stand there)
    out.append((-X - P, BASE, -Z - P, -X, edge_top, Z + P, 'ledge'))
    out.append((-X, BASE, -Z - P, SHORE, edge_top, -Z, 'ledge'))
    out.append((-X, BASE, Z, SHORE, edge_top, Z + P, 'ledge'))
    # the walls, 30 studs out all round (over the lake they stand in the water)
    out.append((-X - P - Tk, BASE, -Z - P - Tk, X + P + Tk, WB.WALL_TOP, -Z - P, 'bound'))
    out.append((-X - P - Tk, BASE, Z + P, X + P + Tk, WB.WALL_TOP, Z + P + Tk, 'bound'))
    out.append((-X - P - Tk, BASE, -Z - P, -X - P, WB.WALL_TOP, Z + P, 'bound'))
    out.append((X + P, BASE, -Z - P, X + P + Tk, WB.WALL_TOP, Z + P, 'bound'))
    return out, list(rot), WB._info(edge_top, edge_seen)

HIT_SOLID, HIT_ROT, WALLBOX = forest_box(SOLID, ROT, EDGE_TOP, EDGE_SEEN)
HIT_CYL, HIT_TILT = CYL, TILT                   # (19 Nov 2026: written as the layout's solidC and solidT)

# for the plan and the offline checks (arena_plan.py, arena_check.py read boxes): the old staircase floor, and a box
# inside each cylinder that takes shots (sight lines stay honest: what's in the box is in the cylinder) and each rock
# box that takes shots. the ramps over logs take no shots: left out
def _inner(cy):
    ax, ay, az, bx, by, bz, r, mat, fl = cy
    k = r / math.sqrt(2)
    if abs(ax - bx) < 1e-6 and abs(az - bz) < 1e-6: return (ax - k, min(ay, by), az - k, ax + k, max(ay, by), az + k, mat)
    if abs(ay - by) < 1e-6 and abs(az - bz) < 1e-6: return (min(ax, bx), ay - k, az - k, max(ax, bx), ay + k, az + k, mat)
    return (ax - k, min(ay, by) - k, min(az, bz), ax + k, max(ay, by) + k, max(az, bz), mat)
CHECK_EXTRA = list(GROUND) + [_inner(cy) for cy in CYL if cy[8] != 'c'] + \
    [(t[0] - t[9] / 2, t[1] - t[10] / 2, t[2] - t[11] / 2, t[0] + t[9] / 2, t[1] + t[10] / 2, t[2] + t[11] / 2, t[12])
     for t in TILT if t[13] == 'b' and t[12] != 'ground' and t[14] != 'c']

if __name__ == '__main__':
    from collections import Counter
    print('solid %d (ground %d), hit %d, spawns %d, team %s, cleared trees %d, water %s' % (len(SOLID), len(GROUND), len(HIT_SOLID), len(SPAWNS),
          {k: len(v) for k, v in TEAM.items()}, len(CLEARED), WATER))
    print('kept web boxes by mat', Counter(m for (_, m, _) in KEPT).most_common(60))
    xs = [b[0] for b in HIT_SOLID] + [b[3] for b in HIT_SOLID]; zs = [b[2] for b in HIT_SOLID] + [b[5] for b in HIT_SOLID]
    print('extent x %.0f..%.0f z %.0f..%.0f' % (min(xs), max(xs), min(zs), max(zs)))
    for k, v in TEAM.items(): print(k, v)
    print('ffa', SPAWNS)
