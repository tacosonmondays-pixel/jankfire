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
    'att': [(-46, 42), (-42, 45), (-38, 43), (-34, 46), (-30, 44), (-26, 47), (-36, 49.5), (-44, 48.5)],
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
    box(*c, mat)

# new cover (web metres x, z, size): a boulder outcrop between the defenders' spawns and the lookout, so no attacker spawn
# sees a defender spawn (the web's lots were 520 studs apart; these are 330)
EXTRA_ROCKS = [(15.5, -54.0, 1.7), (20.5, -55.8, 1.5), (11.5, -55.6, 1.3)]
for (x, z, s) in EXTRA_ROCKS:
    for (a0, y0, c0, a1, y1, c1, m) in ((x - s, -1.0, z - s * 0.8, x + s, s * 1.1, z + s * 0.8, 'rockf'),
                                        (x - s * 0.7, s * 1.1, z - s * 0.5, x + s * 0.5, s * 1.5, z + s * 0.6, 'rockf'),
                                        (x + s * 0.7, -1.0, z + s * 0.4, x + s * 1.5, s * 0.7, z + s * 1.2, 'rockmoss')):
        c = (lx(a0), y0 * S, lz(c0), lx(a1), y1 * S, lz(c1))
        KEPT.append((c, m, {'min': [a0, y0, c0], 'max': [a1, y1, c1], 'mat': m, 'av': 'rocks_forest'}))
        box(*c, m)

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
GROUND = []
def ground():
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
            if c: GROUND.append(c); box(*c, 'ground')
ground()

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
    best = None
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

if __name__ == '__main__':
    from collections import Counter
    print('solid %d (ground %d), hit %d, spawns %d, team %s, cleared trees %d, water %s' % (len(SOLID), len(GROUND), len(HIT_SOLID), len(SPAWNS),
          {k: len(v) for k, v in TEAM.items()}, len(CLEARED), WATER))
    print('kept web boxes by mat', Counter(m for (_, m, _) in KEPT).most_common(60))
    xs = [b[0] for b in HIT_SOLID] + [b[3] for b in HIT_SOLID]; zs = [b[2] for b in HIT_SOLID] + [b[5] for b in HIT_SOLID]
    print('extent x %.0f..%.0f z %.0f..%.0f' % (min(xs), max(xs), min(zs), max(zs)))
    for k, v in TEAM.items(): print(k, v)
    print('ffa', SPAWNS)
