# BACKROOMS for Roblox (18 Nov 2026): the hit boxes, spawns and water of the web map "backrooms" (shared/map.js
# backrooms(), dumped to tools/roblox/arenas/backrooms.json by webmap_dump.mjs), in studs local to the arena's origin.
# The owner: "We need more map variety ... bring back spooky forest and back room!!"
#
# The web map is a 60 x 60 grid of 4 m cells (240 m a side: 720 studs). Ported whole it would be a round's long walk,
# so the arena is the middle 40 x 40 cells (web x, z in [-80, 80] m: 480 studs a side), box for box x3. Everything in
# it is the web's: the high hall in the middle with its pillars, freestanding walls and low cover, the Office (site A,
# north-east), the Wet Room (site B, north-west) with its stair down into the flooded pool rooms under the west side,
# the second stair back up west of the hall, the pillar rooms, the long hall along the south and the hundreds of
# random rooms and doorways round them. Where the crop cuts a room it is closed by a wall on the crop line (no doorway
# leads out); the pool room the crop cuts at the south (web z 72 to 104) is closed off at its door instead.
# Sealed: the ceiling is a real hit box everywhere and the outer walls are real walls, so there is no wall box and no
# sky line (wallbox.py is for open-air arenas).
# Plain Python: backrooms_models.py (the kit), arena_plan.py and arena_check.py read the same numbers.
import os, json, math

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'arenas', 'backrooms.json')))
S = 3.0                     # studs per metre
CROP = 80.0                 # metres: the arena is web x, z in [-CROP, CROP]
T = 0.2                     # the web's wall thickness (m)
H, HH, PY = 4.2, 9.0, -4.5  # ceiling, the hall's ceiling, the pool rooms' floor (m)
POOL_Z = 72.0               # (m) the pool level stops here: the pool room past it is closed off at its door
U, O = 4.0, -120.0          # the web's cell and the grid's corner (m)
def gx(i): return O + i * U
def mid(i): return O + (i + 0.5) * U

# the hit boxes' looks: web material -> (Roblox material for impacts, colour for impacts, the web material)
MATS = {
    'wallpaper': ('SmoothPlastic', 'c8b46a', 'wallpaper'),
    'pooltile': ('Marble', 'e4e6e2', 'pooltile'),
    'step': ('Marble', 'e4e6e2', 'pooltile'),
    'carpetb': ('Fabric', '9a8a62', 'carpetb'),
    'concrete': ('Concrete', '9a968c', 'concrete'),
    'ceiltile': ('SmoothPlastic', 'e6e1d2', 'ceiltile'),
    'officecarpet': ('Fabric', '7b8590', 'officecarpet'),
    'cubicle': ('Fabric', '8c949c', 'cubicle'),
    'plaster': ('SmoothPlastic', 'd8d2c4', 'plaster'),
    'glass': ('Glass', '3a4048', 'glass'),
    'metal': ('Metal', 'b8b4aa', 'metal'),
    'white': ('SmoothPlastic', 'eeeeea', 'white'),
    'water': ('Glass', '9ccbd0', 'water'),
}

SOLID, ROT, SPAWNS, PADS, WATER, NOTES = [], [], [], [], [], []
TEAM = {'att': [], 'def': [], 'mid': []}
FLIGHTS = []      # (x0, z0, x1, z1) in studs: the stair holes (the kit draws the steps and the rails round them)
DECO = []         # (x0, y0, z0, x1, y1, z1, kind) in studs: look-only things from the web's deco (light states, puddles)

def st(v): return v * S

def add(x0, y0, z0, x1, y1, z1, m):
    """a box in web metres -> SOLID in studs"""
    SOLID.append((st(min(x0, x1)), st(min(y0, y1)), st(min(z0, z1)), st(max(x0, x1)), st(max(y0, y1)), st(max(z0, z1)), m))

# ---------------------------------------------------------------- the stair holes (shared/map.js flight(col, jt))
WEB_FLIGHTS = [(13, 17), (14, 36), (16, 51)]
HOLES = []
for (col, jt) in WEB_FLIGHTS:
    hx0, hz0, hx1, hz1 = gx(col), gx(jt + 1), gx(col + 1), gx(jt + 3)
    if hz1 <= CROP: HOLES.append((hx0, hz0, hx1, hz1)); FLIGHTS.append((st(hx0), st(hz0), st(hx1), st(hz1)))
def in_hole(b):
    for (hx0, hz0, hx1, hz1) in HOLES:
        if b['min'][0] >= hx0 - 0.01 and b['max'][0] <= hx1 + 0.01 and b['min'][2] >= hz0 - 0.01 and b['max'][2] <= hz1 + 0.01:
            return True
    return False

# ---------------------------------------------------------------- the web's boxes, cropped
E = CROP + T / 2            # (the crop's clip line: a wall standing on the crop line keeps its whole thickness)
def on_crop_line(x0, z0, x1, z1):
    """a wallpaper wall lying along one of the four crop lines (the continuous outer walls replace it)"""
    if x1 - x0 <= 0.3 and abs((x0 + x1) / 2) > CROP - 0.15: return True
    if z1 - z0 <= 0.3 and abs((z0 + z1) / 2) > CROP - 0.15: return True
    return False

dropped = 0
for b in D['boxes']:
    (x0, y0, z0), (x1, y1, z1), m = b['min'], b['max'], b['mat']
    pool = y1 <= -0.29                       # the pool level (floors, tiled walls and pillars under the floor)
    zmax = POOL_Z + T / 2 if pool else E
    cx0, cx1, cz0, cz1 = max(x0, -E), min(x1, E), max(z0, -E), min(z1, zmax)
    if cx1 - cx0 <= 1e-6 or cz1 - cz0 <= 1e-6: dropped += 1; continue
    # (a sliver left by the clip: a wall end poking past the crop line)
    if (cx1 - cx0 < min(0.25, x1 - x0) - 1e-6) or (cz1 - cz0 < min(0.25, z1 - z0) - 1e-6): dropped += 1; continue
    if m == 'wallpaper' and on_crop_line(cx0, cz0, cx1, cz1): dropped += 1; continue
    if m == 'pooltile' and in_hole(b) and y1 > PY + 0.01: m = 'step'
    add(cx0, y0, cz0, cx1, y1, cz1, m)

# the outer walls on the crop lines (wallpaper inside, a metre thick outside), from under the floor slab to the ceiling's top
OUT = 1.0
add(-CROP - OUT, -0.6, -CROP - OUT, CROP + OUT, H + 0.2, -CROP + T / 2, 'wallpaper')
add(-CROP - OUT, -0.6, CROP - T / 2, CROP + OUT, H + 0.2, CROP + OUT, 'wallpaper')
add(-CROP - OUT, -0.6, -CROP + T / 2, -CROP + T / 2, H + 0.2, CROP - T / 2, 'wallpaper')
add(CROP - T / 2, -0.6, -CROP + T / 2, CROP + OUT, H + 0.2, CROP - T / 2, 'wallpaper')
# the pool room past POOL_Z: its door in the tiled wall on web z 72 (shared/map.js pops 'x' 48) is closed
add(gx(13) + 0.6, PY, POOL_Z - T / 2, gx(16) - 0.6, -0.6, POOL_Z + T / 2, 'pooltile')

# two bits the crop shut in (their doorways were all outside it): the pillar room cut at the south gets a doorway from
# the long hall, the one-cell room in the south-west corner one from the room north of it. (a doorway as the web cuts
# them: 2 m wide, up into the ceiling)
def cut_door(axis, line, a, b):
    """open web metres a..b along a wallpaper wall lying on the grid line `line` (axis 'x': the wall runs along x at
    z = line; 'z': along z at x = line)"""
    global SOLID
    L, Ls = st(line), []
    for s in SOLID:
        x0, y0, z0, x1, y1, z1, m = s
        on = m == 'wallpaper' and y0 < st(H) and (abs((z0 + z1) / 2 - L) < 0.5 and z1 - z0 < 1.0 if axis == 'x' else abs((x0 + x1) / 2 - L) < 0.5 and x1 - x0 < 1.0)
        u0, u1 = (x0, x1) if axis == 'x' else (z0, z1)
        if not on or u1 <= st(a) or u0 >= st(b): Ls.append(s); continue
        for (v0, v1) in ((u0, st(a)), (st(b), u1)):
            if v1 - v0 > 0.05:
                Ls.append((v0, y0, z0, v1, y1, z1, m) if axis == 'x' else (x0, y0, v0, x1, y1, v1, m))
    SOLID = Ls
cut_door('x', gx(48), mid(32) - 1.0, mid(32) + 1.0)
cut_door('x', gx(49), mid(21) - 1.0, mid(21) + 1.0)

# ---------------------------------------------------------------- water and the look-only deco from the web
for b in D['deco']:
    (x0, y0, z0), (x1, y1, z1), m = b['min'], b['max'], b['mat']
    pool = y1 <= -0.29 or m == 'poolwater' and y0 < -1
    zmax = POOL_Z + T / 2 if pool else E
    cx0, cx1, cz0, cz1 = max(x0, -E), min(x1, E), max(z0, -E), min(z1, zmax)
    if cx1 - cx0 <= 1e-6 or cz1 - cz0 <= 1e-6: continue
    if m == 'poolwater' and y0 < -1:
        # the flooded pool rooms: the web's water is ankle-deep (0.42 m: you wade it, as in the web). (the room past
        # POOL_Z is closed off: its water goes)
        cz1 = min(cz1, POOL_Z)
        if cz1 - cz0 < 1.0: continue
        WATER.append((st(cx0), st(PY), st(cz0), st(cx1), st(y1), st(cz1)))
    else:
        DECO.append((st(cx0), st(y0), st(cz0), st(cx1), st(y1), st(cz1), m))

# ---------------------------------------------------------------- the rooms (for the kit's light panels and the plan)
# the web's room plan, the same dice (mulberry32, seed 1777) as shared/map.js backrooms(): which room each cell is
def _rng(seed):
    s = [seed & 0xffffffff]
    def imul(a, b): return (a * b) & 0xffffffff
    def r():
        s[0] = (s[0] + 0x6d2b79f5) & 0xffffffff
        a = s[0]
        t = imul(a ^ (a >> 15), 1 | a)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & 0xffffffff) ^ t
        return ((t ^ (t >> 14)) & 0xffffffff) / 4294967296
    return r

def _rooms():
    r = _rng(1777)
    N = 60
    ids = [-1] * (N * N)
    rooms = []
    def room(i0, j0, i1, j1, kind='room', step=0):
        k = len(rooms)
        rooms.append(dict(k=k, i0=i0, j0=j0, i1=i1, j1=j1, kind=kind, step=step))
        for i in range(i0, i1):
            for j in range(j0, j1): ids[i * N + j] = k
    room(22, 22, 38, 38, 'hall'); room(25, 1, 35, 5, 'lobby'); room(25, 55, 35, 59, 'lobby')
    room(41, 15, 48, 21, 'office'); room(12, 15, 19, 21, 'wet'); room(12, 50, 18, 55, 'drop'); room(12, 35, 17, 40, 'stairs')
    room(6, 9, 54, 10, 'long'); room(51, 14, 52, 54, 'long'); room(8, 24, 9, 50, 'long'); room(10, 47, 50, 48, 'long')
    room(2, 25, 8, 32, 'pillars', 1); room(53, 28, 59, 35, 'pillars', 2); room(39, 39, 46, 45, 'pillars', 1)
    room(40, 2, 47, 8, 'pillars', 2); room(8, 1, 14, 7, 'pillars', 2)
    sizes = [1, 2, 2, 2, 3, 3, 3, 4, 4, 5, 6]
    pick = lambda a: a[int(r() * len(a))]
    for j in range(N):
        for i in range(N):
            if ids[i * N + j] != -1: continue
            w, h = pick(sizes), pick(sizes)
            if r() < 0.2:
                l = 3 + int(r() * 6)
                if r() < 0.5: w, h = 1, l
                else: w, h = l, 1
            ww = hh = 0
            while ww < w and i + ww < N and ids[(i + ww) * N + j] == -1: ww += 1
            def row_free(jj):
                return all(ids[(i + a) * N + jj] == -1 for a in range(ww))
            while hh < h and j + hh < N and row_free(j + hh): hh += 1
            kind = 'pillars' if (ww * hh >= 16 and min(ww, hh) >= 4 and r() < 0.3) else 'room'
            room(i, j, i + ww, j + hh, kind, 2)
    return ids, rooms
ROOM_IDS, ROOMS = _rooms()
I0, I1 = int((-CROP - O) / U), int((CROP - O) / U)     # cells 10..49
def room_at(i, j): return ROOMS[ROOM_IDS[i * 60 + j]]

# ---------------------------------------------------------------- spawns
# team spawns (Matches swaps ends every round): attackers in the rooms by the long hall at the south, defenders in the
# rooms at the north end, both about x 0 with the high hall between them; the 1v1v1's third side east. Each faces the
# middle. (Chosen from the plan and checked: arena_check.py, 0 team spawn lines open)
def tspawn(side, x, z, fx, fz):
    TEAM[side].append((st(x), 0.3, st(z), fx, fz))
# (filled in below from SPAWN_CELLS; web metres, cell middles)
# attackers: the room north of the long hall (cells 28..30 x 45..46), defenders: the room at the north end west of the
# web's dark room (cells 26..28 x 13..14), the third side: the little room east of the hall (cells 45..46 x 28..29). Each
# spawn faces its room's doorway toward the hall (so a round never opens on a blank wall)
def toward(x, z, tx, tz):
    dx, dz = tx - x, tz - z
    n = math.hypot(dx, dz) or 1.0
    return round(dx / n, 3), round(dz / n, 3)
def team_at(side, x, z, door):
    fx, fz = toward(x, z, door[0], door[1])
    tspawn(side, x, z, fx, fz)
for k in range(4):
    for j in (45, 46): team_at('att', gx(28) + 1.5 + 3.0 * k, mid(j), (mid(28), gx(45) - 2.0))
for k in range(4):
    for j in (13, 14): team_at('def', gx(26) + 1.5 + 3.0 * k, mid(j), (mid(27), gx(15) + 2.0))
for i in (45, 46):
    for j in (28, 29): team_at('mid', mid(i), mid(j), (gx(45) - 2.0, mid(29)))
ATT_CELLS = [(28, 45), (30, 46)]; DEF_CELLS = [(26, 13), (28, 14)]; MID_CELLS = [(45, 28), (46, 29)]

# free-for-all: the web's own spawns that fall inside, then more by farthest-point picks over the cell middles
def _free_cell(i, j):
    x, z = mid(i), mid(j)
    for (hx0, hz0, hx1, hz1) in HOLES:
        if hx0 < x < hx1 and hz0 < z < hz1: return False
    return True
cand = [(mid(i), mid(j)) for i in range(I0, I1) for j in range(I0, I1) if _free_cell(i, j)]
ffa = [(s[0], s[2], s[1]) for s in D['spawns'] if abs(s[0]) < CROP - 1 and abs(s[2]) < CROP - 1 and (s[1] > -1 or s[2] < POOL_Z - 1)]
far = [min((math.hypot(c[0] - p[0], c[1] - p[1]) for p in ffa), default=1e9) for c in cand]
while len(ffa) < 26:
    k = max(range(len(cand)), key=lambda q: far[q])
    p = cand[k]
    ffa.append((p[0], p[1], 0.1))
    for q, c in enumerate(cand): far[q] = min(far[q], math.hypot(c[0] - p[0], c[1] - p[1]))
for (x, z, y) in ffa:
    SPAWNS.append((st(x), st(y) + 0.3 if y > -1 else st(PY) + 0.3, st(z)))

# ================================================================ for the plan (arena_plan.py)
TITLE = 'BACKROOMS'
BOUNDS = (-250.0, 250.0, -250.0, 250.0)
PLAN_PX = 2.2
LEVELS = [('THE FLOOR (y 0)', -1.0, 12.0, 0.0), ('THE POOL ROOMS UNDER THE WEST SIDE (y -13.5)', -14.0, -2.0, -13.5)]
FLOORS = ('carpetb', 'officecarpet', 'pooltile', 'concrete')
COLOURS = {'wallpaper': (176, 150, 70), 'pooltile': (226, 228, 222), 'carpetb': (150, 136, 100), 'concrete': (130, 126, 118),
           'ceiltile': (220, 214, 196), 'officecarpet': (120, 132, 146), 'cubicle': (140, 148, 156), 'plaster': (210, 204, 190),
           'glass': (60, 64, 72), 'metal': (184, 180, 170), 'white': (238, 238, 234), 'water': (156, 203, 208)}
NOTES = [(0.0, 0.0, 0, 'THE HALL'), (st(58.0), st(-48.0), 0, 'OFFICE'), (st(-58.0), st(-48.0), 0, 'WET ROOM'),
         (st(-60.0), st(10.0), 1, 'POOL ROOMS'), (st(-66.0), st(-44.0), 1, 'STAIR UP (WET ROOM)'), (st(-62.0), st(32.0), 1, 'STAIR UP'),
         (st(0.0), st(70.0), 0, 'LONG HALL'), (st(42.0), st(42.0), 0, 'PILLARS')]
PLAN_NOTE = ('the web\'s middle 40 x 40 cells, box for box x3; sealed (ceilings and outer walls real); the pool rooms are ankle-deep water '
             'under the west side, a stair down in the Wet Room and another west of the hall')

if __name__ == '__main__':
    print('solid %d (web boxes dropped by the crop %d), water %d, deco %d, spawns %d, team %s, flights %d' % (
        len(SOLID), dropped, len(WATER), len(DECO), len(SPAWNS), {k: len(v) for k, v in TEAM.items()}, len(FLIGHTS)))
    print('rooms', len(ROOMS), [(r['k'], r['kind'], r['i0'], r['j0'], r['i1'], r['j1']) for r in ROOMS if r['kind'] != 'room'][:22])
    for (i, j) in ATT_CELLS + DEF_CELLS + MID_CELLS:
        rm = room_at(i, j); print('spawn cell', (i, j), 'room', rm['k'], rm['kind'], (rm['i0'], rm['j0'], rm['i1'], rm['j1']))
