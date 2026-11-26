# JANKFIELD HIGH for Roblox (20 Nov 2026): the zombies school. The owner: "A multi level multi section map, lets bring
# back zombies!! We can used colored dummies for now!! It'll be a big highschool multiple floors courtyard basement
# classrooms bathrooms etc!! Bring everything we got from jank fire!!"
#
# It starts from the web map shared/zmschool.js (the owner's own design): the entrance lobby you start in, the
# cafeteria, the locker hall with the main stairs, the science lab, the double-height gym with its balcony and the
# bleachers up to it; upstairs the long hall, the library, the art room (the Cheat Machine) and the principal's office
# (the Warranty Voider); windows onto boarded ledges the zombies climb in from; roller shutters you buy open. Then it
# grows the way the owner asked:
#   - four levels: a BASEMENT (the boiler room with the power, maintenance tunnels, storage), the ground floor, the
#     upper floor and the ROOF (HVAC, a greenhouse, the water tower);
#   - an open-air COURTYARD in the middle that the halls on both floors look onto: the halls run round it in a ring, so
#     every floor is a loop;
#   - RESTROOMS on every floor, a row of real CLASSROOMS on both floors, the gym's own locker rooms, a nurse's office,
#     a weight room, a music room, a computer lab and a teachers' lounge;
#   - five ways between floors: the main stairs (locker hall), the bleachers (gym), the west stairwell (basement to
#     roof), the east stairwell (basement to roof), so there are loops between floors as well as round them.
# Our own design throughout: no real school, no other game's map.
#
# Built to the zombies mode's contract (roblox/docs/ZOMBIES.md, weapons-port): the ZM folder of markers, 12-wide shutters,
# 6 x 6 boarded windows onto closed ledges, and every slope gentle enough for the zombies' nav grid (1.6 studs of rise
# per 3 of run at most): so every stair is a ramp you collide with (a 1-in-2 slope), its steps drawn by the kit.
# Everything is in studs, local to the arena's origin: x east, z south (the front doors face +z), y up, the ground
# floor at y 0. A floor is 16 studs (15 clear, a 1-stud slab). Plain Python: school_models.py (the kit, in Blender),
# school_plan.py (the plan sheet) and the checks at the bottom read the same numbers.
#
# THE WALLS ARE WORKED OUT FROM THE ROOMS: every level is a list of room rectangles (ROOMS) rastered on a 1-stud grid;
# wherever two rooms that need a wall meet there is a 1-stud wall on the line (rooms of one area meet openly unless
# one of them is an enclosed room: a classroom, a restroom), and round the outside a 2-stud wall. Doors, doorways and
# windows are cut out of those walls by position (OPENINGS). So moving a room moves its walls.
import os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import maplayout as _M
from maplayout import SOLID, ROT, SPAWNS, PADS, WATER, NOTES, TEAM, box, rot

TITLE = 'JANKFIELD HIGH'
LV = {'B': -16.0, 'G': 0.0, 'U': 16.0, 'R': 32.0}
ORDER = ('B', 'G', 'U', 'R')
CEIL = 15.0                   # clear height of a floor; its slab above is CEIL..CEIL+1
TI, TX = 1.0, 2.0             # inside walls (centred on the line), outside walls (outward from the line)
PARAPET_TOP = 35.5            # the roof's parapet
FENCE_TOP = 42.0              # the fence on the roof's edges (so nobody hops off into an unopened part)
GYM_LID, GYM_WALL = (37.0, 38.0), 39.0
TOWER_LID, TOWER_WALL = (46.0, 47.0), 47.0
FX0, FX1, FZ0, FZ1 = -120, 160, -88, 96        # the building's footprint
GX0, GZ0 = FX0 - 6, FZ0 - 6                     # the raster's corner (room for the outside walls)
NX, NZ = (FX1 + 6) - GX0, (FZ1 + 6) - GZ0

# ================================================================ areas (what the zombies mode opens, door by door)
AREAS = {
    'lobby': 'Main Entrance', 'cafe': 'Cafeteria', 'whall': 'West Hall', 'lab': 'Science Lab', 'court': 'Courtyard',
    'lockers': 'Locker Hall', 'gym': 'Gym', 'nhall': 'Classroom Hall', 'gymwing': 'Locker Rooms', 'weights': 'Weight Room',
    'wstair': 'West Stairwell', 'netower': 'East Stairwell', 'tunnels': 'Maintenance Tunnels', 'boiler': 'Boiler Room',
    'upper': 'Upstairs Hall', 'library': 'Library', 'art': 'Art Room', 'office': "Principal's Office",
    'lounge': "Teachers' Lounge", 'complab': 'Computer Lab', 'music': 'Music Room', 'roof': 'Rooftop',
}
START = 'lobby'

ROOMS = []
def room(rid, area, lv, r, look, fmat='lino', floor=True, enclosed=False, tower=False, lid=None, wtop=None, name=None):
    """one rectangle of a level. area: the zombies area it belongs to (None: the courtyard's air, '_roofx': roof nobody
    walks). look: what kind of room (the kit paints and dresses by it). floor: it has a slab under it at its level.
    enclosed: walled off even from its own area (classrooms, restrooms: they open through doorways)"""
    ROOMS.append(dict(id=rid, area=area, lv=lv, r=tuple(float(v) for v in r), look=look, fmat=fmat, floor=floor,
                      enclosed=enclosed, tower=tower, lid=lid, wtop=wtop, name=name))

def towers(lv):
    room('wstair_' + lv, 'wstair', lv, (-120, -34, -100, 0), 'tower', 'stair', floor=(lv == 'B'), tower=True,
         lid=TOWER_LID if lv == 'R' else None, wtop=TOWER_WALL if lv == 'R' else None)
    room('netower_' + lv, 'netower', lv, (140, -88, 160, -48), 'tower', 'stair', floor=(lv == 'B'), tower=True,
         lid=TOWER_LID if lv == 'R' else None, wtop=TOWER_WALL if lv == 'R' else None)

# ---------------------------------------------------------------- BASEMENT (y -16)
room('w1', 'tunnels', 'B', (-120, 0, -44, 12), 'tunnel', 'concrete')
room('staffwc', 'tunnels', 'B', (-88, 12, -72, 24), 'restroom', 'restroomtile', enclosed=True, name='Staff Restroom')
room('w2', 'tunnels', 'B', (-56, -88, -44, 0), 'tunnel', 'concrete')
room('t1', 'tunnels', 'B', (-44, -48, 64, -36), 'tunnel', 'concrete')
room('t2', 'tunnels', 'B', (-44, -88, 64, -76), 'tunnel', 'concrete')
room('econn', 'tunnels', 'B', (52, -76, 64, -48), 'tunnel', 'concrete')
room('storage', 'tunnels', 'B', (-44, -76, -12, -48), 'storage', 'concrete', enclosed=True, name='Storage')
room('lostfound', 'tunnels', 'B', (-12, -76, 20, -48), 'storage', 'concrete', enclosed=True, name='Lost and Found')
room('workshop', 'tunnels', 'B', (20, -76, 52, -48), 'workshop', 'concrete', enclosed=True, name='Workshop')
room('boiler', 'boiler', 'B', (64, -88, 140, -36), 'boiler', 'concrete')
room('boiler_l', 'boiler', 'B', (140, -48, 160, -36), 'boiler', 'concrete')
towers('B')

# ---------------------------------------------------------------- GROUND FLOOR (y 0)
room('lab', 'lab', 'G', (-120, -88, -56, -34), 'lab', 'lino')
room('boys_g', 'whall', 'G', (-100, -34, -56, 0), 'restroom', 'restroomtile', enclosed=True, name="Boys' Restroom")
room('passage_g', 'whall', 'G', (-120, 0, -56, 12), 'hall', 'lino')
room('girls_g', 'whall', 'G', (-120, 12, -56, 28), 'restroom', 'restroomtile', enclosed=True, name="Girls' Restroom")
room('cafe_n', 'cafe', 'G', (-120, 28, -56, 48), 'cafe', 'tile')
room('cafe', 'cafe', 'G', (-120, 48, -32, 96), 'cafe', 'tile')
room('whall_g', 'whall', 'G', (-56, -48, -40, 48), 'hall', 'lino')
room('cr101', 'nhall', 'G', (-56, -88, -24, -48), 'classroom', 'lino', enclosed=True, name='Room 101')
room('cr102', 'nhall', 'G', (-24, -88, 8, -48), 'classroom', 'lino', enclosed=True, name='Room 102')
room('cr103', 'nhall', 'G', (8, -88, 40, -48), 'classroom', 'lino', enclosed=True, name='Room 103')
room('nhall_g', 'nhall', 'G', (-40, -48, 40, -32), 'hall', 'lino')
room('court', 'court', 'G', (-40, -32, 40, 32), 'court', 'pavers')
room('shall', 'lobby', 'G', (-40, 32, 40, 48), 'hall', 'lino')
room('lobby', 'lobby', 'G', (-32, 48, 32, 96), 'lobby', 'terrazzo')
room('nurse', 'lobby', 'G', (32, 48, 64, 96), 'nurse', 'lino', enclosed=True, name="Nurse's Office")
room('janitor', 'lockers', 'G', (40, -88, 64, -48), 'janitor', 'concrete', enclosed=True, name="Janitor's Room")
room('lockers', 'lockers', 'G', (40, -48, 64, 48), 'hall', 'lino')
room('boysl', 'gymwing', 'G', (64, -88, 102, -48), 'lockerroom', 'restroomtile', enclosed=True, name="Boys' Locker Room")
room('girlsl', 'gymwing', 'G', (102, -88, 140, -48), 'lockerroom', 'restroomtile', enclosed=True, name="Girls' Locker Room")
room('gcorr', 'gymwing', 'G', (64, -48, 160, -32), 'hall', 'lino')
room('gym', 'gym', 'G', (64, -32, 160, 56), 'gym', 'gymwood')
room('weights', 'weights', 'G', (64, 56, 160, 96), 'weights', 'rubber')
towers('G')

# ---------------------------------------------------------------- UPPER FLOOR (y 16)
room('art', 'art', 'U', (-120, -88, -56, -34), 'art', 'wood')
room('boys_u', 'upper', 'U', (-100, -34, -56, 0), 'restroom', 'restroomtile', enclosed=True, name="Boys' Restroom")
room('passage_u', 'upper', 'U', (-120, 0, -56, 12), 'hall', 'lino')
room('girls_u', 'upper', 'U', (-120, 12, -56, 28), 'restroom', 'restroomtile', enclosed=True, name="Girls' Restroom")
room('library_n', 'library', 'U', (-120, 28, -56, 48), 'library', 'carpet')
room('library', 'library', 'U', (-120, 48, -32, 96), 'library', 'carpet')
room('uw', 'upper', 'U', (-56, -48, -40, 48), 'hall', 'lino')
room('cr201', 'upper', 'U', (-56, -88, -24, -48), 'classroom', 'lino', enclosed=True, name='Room 201')
room('cr202', 'upper', 'U', (-24, -88, 8, -48), 'classroom', 'lino', enclosed=True, name='Room 202')
room('cr203', 'upper', 'U', (8, -88, 40, -48), 'classroom', 'lino', enclosed=True, name='Room 203')
room('un', 'upper', 'U', (-40, -48, 40, -32), 'hall', 'lino')
room('courtair_u', None, 'U', (-40, -32, 40, 32), 'courtair', floor=False)
room('us', 'upper', 'U', (-40, 32, 40, 48), 'hall', 'lino')
room('frontoffice', 'office', 'U', (-32, 48, 32, 68), 'office', 'carpet', name='Front Office')
room('principal', 'office', 'U', (-32, 68, 32, 96), 'principal', 'carpet', enclosed=True, name="Principal's Office")
room('lounge', 'lounge', 'U', (32, 48, 64, 96), 'lounge', 'carpet')
room('bookroom', 'upper', 'U', (40, -88, 64, -48), 'storage', 'lino', enclosed=True, name='Book Room')
room('ue', 'upper', 'U', (40, -48, 64, 48), 'hall', 'lino')
room('landing', 'lockers', 'U', (54, -20, 64, -10), 'landing', 'lino')         # the top of the main stairs, this side of its shutter
room('stairhole', 'lockers', 'U', (54, -10, 64, 10), 'stairhole', floor=False) # glass to the ceiling round it
# (20 Nov, the owner: "usually whene theres stairs the floor above is still there". The hole is only over the stairs'
#  top two thirds now; the upper hall's floor runs on over the bottom third, 9.5 studs over the treads there)
room('complab', 'complab', 'U', (64, -88, 140, -48), 'complab', 'carpet', enclosed=True)
room('ucorr', 'complab', 'U', (64, -48, 160, -32), 'hall', 'lino')
room('balcony', 'gym', 'U', (64, -32, 76, 56), 'balcony', 'gymwood')         # the gym's balcony: you walk up the bleachers, no door
room('gymair', 'gym', 'U', (76, -32, 160, 56), 'gymair', floor=False)
room('music', 'music', 'U', (64, 56, 160, 96), 'music', 'wood')
towers('U')

# ---------------------------------------------------------------- ROOF (y 32)
room('roof', 'roof', 'R', (-120, -88, 160, -32), 'roof', 'roofdeck')
room('roof_w', 'roof', 'R', (-120, -32, -56, 0), 'roof', 'roofdeck')
for k, r in enumerate(((-120, 0, -40, 96), (-56, -32, -40, 0), (-40, 32, 64, 96), (40, -32, 64, 32), (64, 56, 160, 96))):
    room('roofx%d' % k, '_roofx', 'R', r, 'roofx', 'roofdeck')
room('courtair_r', None, 'R', (-40, -32, 40, 32), 'courtair', floor=False)
room('gymtop', '_gymtop', 'R', (64, -32, 160, 56), 'gymtop', floor=False, lid=GYM_LID, wtop=GYM_WALL)
towers('R')

# ================================================================ the raster
GRID = {}
def _raster():
    for lv in ORDER:
        g = [[-1] * NZ for _ in range(NX)]
        for k, r in enumerate(ROOMS):
            if r['lv'] != lv: continue
            x0, z0, x1, z1 = (int(v) for v in r['r'])
            for i in range(x0 - GX0, x1 - GX0):
                col = g[i]
                for j in range(z0 - GZ0, z1 - GZ0): col[j] = k
        GRID[lv] = g
_raster()

def room_at(lv, x, z):
    i, j = int(math.floor(x)) - GX0, int(math.floor(z)) - GZ0
    if 0 <= i < NX and 0 <= j < NZ:
        k = GRID[lv][i][j]
        return ROOMS[k] if k >= 0 else None
    return None

def needs_wall(a, b):
    A, B_ = ROOMS[a], ROOMS[b]
    if A['area'] is None or B_['area'] is None: return True
    if A['area'] == B_['area'] and not (A['enclosed'] or B_['enclosed'] or A['tower'] or B_['tower']): return False
    return True

GYMISH = ('gym', 'balcony', 'gymair')
def wall_kinds(lv, A, B_):
    """[(material, y0, y1, flags)] for the wall between rooms A and B at a level (flags 'c': stops you, takes no shots)"""
    if lv == 'R':
        ar = {A['area'], B_['area']}
        if 'roof' in ar and '_roofx' in ar: return [('brick', 31.0, PARAPET_TOP, ''), ('fence', PARAPET_TOP, FENCE_TOP, 'c')]
        if A['tower'] or B_['tower']: return [('block', 31.0, TOWER_WALL, '')]
        if 'gymtop' in (A['look'], B_['look']):
            out = [('block', 31.0, GYM_WALL, '')]
            if 'roof' in ar: out.append(('fence', GYM_WALL, GYM_WALL + 5.0, 'c'))
            return out
        out = [('brick', 31.0, PARAPET_TOP, '')]
        if 'roof' in ar: out.append(('fence', PARAPET_TOP, FENCE_TOP, 'c'))
        return out
    L = LV[lv]
    y0, y1 = L - 1.0, L + CEIL
    looks = (A['look'], B_['look'])
    if A['tower'] or B_['tower'] or lv == 'B' or any(x in GYMISH for x in looks): return [('block', y0, y1, '')]
    if 'stairhole' in looks: return [('glass', y0, y1, '')]
    if 'court' in looks or 'courtair' in looks: return [('brick', y0, y1, '')]
    return [('plaster', y0, y1, '')]

# ================================================================ walls
WALLS = []        # dict(box, mat, lv, axis, line, a (room index on the - side), b (+ side or -1), ext)
FENCES = []       # (x0, y0, z0, x1, y1, z1): 'c' boxes (chain-link): stop you, take no shots

def _runs(lv):
    """interior wall runs: (axis, line, from, to, a, b). axis 'z': the wall runs along z at x = line (a west, b east);
    'x': along x at z = line (a north, b south)"""
    g, out = GRID[lv], []
    for i in range(1, NX):
        j = 0
        while j < NZ:
            a, b = g[i - 1][j], g[i][j]
            if a == b or a < 0 or b < 0 or not needs_wall(a, b): j += 1; continue
            j0 = j
            while j < NZ and g[i - 1][j] == a and g[i][j] == b: j += 1
            out.append(('z', GX0 + i, GZ0 + j0, GZ0 + j, a, b))
    for j in range(1, NZ):
        i = 0
        while i < NX:
            a, b = g[i][j - 1], g[i][j]
            if a == b or a < 0 or b < 0 or not needs_wall(a, b): i += 1; continue
            i0 = i
            while i < NX and g[i][j - 1] == a and g[i][j] == b: i += 1
            out.append(('x', GZ0 + j, GX0 + i0, GX0 + i, a, b))
    return out

def _interior(lv):
    runs = _runs(lv)
    cells = set()
    for (ax, line, s0, s1, a, b) in runs:
        for s in range(s0, s1): cells.add((ax, line, s))
    for (ax, line, s0, s1, a, b) in runs:
        e0 = 0.5 if (ax, line, s0 - 1) not in cells else 0.0      # (a run's end carries on half a stud into the
        e1 = 0.5 if (ax, line, s1) not in cells else 0.0          #  wall it meets: no notch in the corner)
        for (mat, y0, y1, fl) in wall_kinds(lv, ROOMS[a], ROOMS[b]):
            th = 0.2 if mat == 'fence' else TI / 2
            if ax == 'z': bx = (line - th, y0, s0 - e0, line + th, y1, s1 + e1)
            else: bx = (s0 - e0, y0, line - th, s1 + e1, y1, line + th)
            if fl == 'c': FENCES.append(bx)
            else: WALLS.append(dict(box=bx, mat=mat, lv=lv, axis=ax, line=line, a=a, b=b, ext=False))

def _greedy(cells):
    """a set of (i, j) -> rectangles (i0, j0, i1, j1), row-major greedy"""
    left, out = set(cells), []
    for (i, j) in sorted(cells):
        if (i, j) not in left: continue
        i1 = i
        while (i1 + 1, j) in left: i1 += 1
        j1 = j
        while all((ii, j1 + 1) in left for ii in range(i, i1 + 1)): j1 += 1
        for ii in range(i, i1 + 1):
            for jj in range(j, j1 + 1): left.discard((ii, jj))
        out.append((i, j, i1 + 1, j1 + 1))
    return out

def _exterior(lv):
    """the outside walls: every empty cell within 2 of a room, as tall as its tallest neighbour needs"""
    g, L = GRID[lv], LV[lv]
    groups = {}
    for i in range(NX):
        for j in range(NZ):
            if g[i][j] >= 0: continue
            top = None
            for di in (-2, -1, 0, 1, 2):
                for dj in (-2, -1, 0, 1, 2):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < NX and 0 <= jj < NZ and g[ii][jj] >= 0:
                        R_ = ROOMS[g[ii][jj]]
                        t = R_['wtop'] if R_['wtop'] is not None else (PARAPET_TOP if lv == 'R' else L + CEIL)
                        top = t if top is None else max(top, t)
            if top is None: continue
            y0 = L - 1.0
            mat = 'earth' if lv == 'B' else 'brick'
            groups.setdefault((y0, top, mat), set()).add((i, j))
    for (y0, y1, mat), cells in groups.items():
        for (i0, j0, i1, j1) in _greedy(cells):
            bx = (GX0 + i0, y0, GZ0 + j0, GX0 + i1, y1, GZ0 + j1)
            thin_x = (i1 - i0) <= 2
            WALLS.append(dict(box=bx, mat=mat, lv=lv, axis='z' if thin_x else 'x', line=None, a=-1, b=-1, ext=True))

def _roof_fences():
    """a fence on the parapet wherever the walkable roof meets the outside or the courtyard's air"""
    g = GRID['R']
    def walk(k): return k >= 0 and ROOMS[k]['area'] == 'roof'
    def open_(k): return k < 0 or ROOMS[k]['area'] is None
    for i in range(1, NX):
        j = 0
        while j < NZ:
            a, b = g[i - 1][j], g[i][j]
            side = 1 if (walk(a) and open_(b) and b < 0) else (-1 if (walk(b) and open_(a) and a < 0) else 0)
            if not side: j += 1; continue
            j0 = j
            while j < NZ and (g[i - 1][j], g[i][j]) == (a, b): j += 1
            x = GX0 + i + side * 1.0
            FENCES.append((x - 0.2, PARAPET_TOP, GZ0 + j0 - 1.2, x + 0.2, FENCE_TOP, GZ0 + j + 1.2))
    for j in range(1, NZ):
        i = 0
        while i < NX:
            a, b = g[i][j - 1], g[i][j]
            side = 1 if (walk(a) and open_(b) and b < 0) else (-1 if (walk(b) and open_(a) and a < 0) else 0)
            if not side: i += 1; continue
            i0 = i
            while i < NX and (g[i][j - 1], g[i][j]) == (a, b): i += 1
            z = GZ0 + j + side * 1.0
            FENCES.append((GX0 + i0 - 1.2, PARAPET_TOP, z - 0.2, GX0 + i + 1.2, FENCE_TOP, z + 0.2))

for _lv in ORDER:
    _interior(_lv); _exterior(_lv)
_roof_fences()

# ================================================================ openings: doors you buy, doorways, windows
OPENINGS = []     # dict(lv, axis, line, a0, a1, y0, y1, kind, ref)
def opening(lv, axis, line, c, w, y0, y1, kind, ref=None):
    OPENINGS.append(dict(lv=lv, axis=axis, line=float(line), a0=c - w / 2, a1=c + w / 2, y0=y0, y1=y1, kind=kind, ref=ref))

DOOR_H, WAY_H, WAY_W = 10.0, 10.5, 10.0
# (a, b, price, level, axis, line, centre, width): a shutter between areas a and b. axis 'z': in a wall along z at
# x = line; 'x': along x at z = line. The order of the prices: the lobby's doors first, the courtyard and the power in
# the middle, the upstairs rooms after, the roof and the principal's office (the Warranty Voider) last
DOOR_LIST = [
    ('lobby', 'cafe', 750, 'G', 'z', -32, 64, 12), ('lobby', 'lockers', 750, 'G', 'z', 40, 40, 12),
    ('lobby', 'whall', 1000, 'G', 'z', -40, 40, 12), ('lobby', 'court', 1250, 'G', 'x', 32, 0, 12),
    ('cafe', 'whall', 750, 'G', 'z', -56, 38, 12), ('whall', 'court', 1000, 'G', 'z', -40, 0, 12),
    ('whall', 'lab', 1000, 'G', 'z', -56, -41, 12), ('whall', 'wstair', 1000, 'G', 'x', 0, -110, 10),
    ('whall', 'nhall', 1000, 'G', 'z', -40, -40, 12), ('lockers', 'nhall', 1000, 'G', 'z', 40, -40, 12),
    ('lockers', 'gymwing', 1000, 'G', 'z', 64, -40, 12), ('lockers', 'gym', 1000, 'G', 'z', 64, 30, 12),
    ('gymwing', 'gym', 750, 'G', 'x', -32, 124, 12), ('gymwing', 'netower', 1000, 'G', 'x', -48, 150, 10),
    ('gym', 'weights', 750, 'G', 'x', 56, 124, 12),
    ('wstair', 'tunnels', 1250, 'B', 'x', 0, -110, 10), ('tunnels', 'boiler', 1250, 'B', 'z', 64, -42, 12),
    ('netower', 'boiler', 1250, 'B', 'x', -48, 150, 10),
    ('lockers', 'upper', 1250, 'U', 'x', -20, 59.25, 9), ('gym', 'upper', 1000, 'U', 'z', 64, 36, 12),
    ('gym', 'music', 1000, 'U', 'x', 56, 70, 12), ('wstair', 'upper', 1000, 'U', 'x', 0, -110, 10),
    ('netower', 'complab', 1000, 'U', 'x', -48, 150, 10), ('upper', 'library', 1000, 'U', 'x', 48, -48, 12),
    ('upper', 'art', 1000, 'U', 'z', -56, -41, 12), ('upper', 'office', 2000, 'U', 'x', 48, 0, 12),
    ('upper', 'lounge', 750, 'U', 'x', 48, 52, 12), ('upper', 'complab', 1000, 'U', 'z', 64, -40, 12),
    ('wstair', 'roof', 1500, 'R', 'z', -100, -5, 10), ('netower', 'roof', 1500, 'R', 'z', 140, -53, 10),
]
DOORS = []
for (a, b, price, lv, ax, line, c, w) in DOOR_LIST:
    L = 32.0 if lv == 'R' else LV[lv]
    h = DOOR_H
    if ax == 'z': bmin, bmax = (line - 0.5, L, c - w / 2), (line + 0.5, L + h, c + w / 2)
    else: bmin, bmax = (c - w / 2, L, line - 0.5), (c + w / 2, L + h, line + 0.5)
    at = (line, L + h / 2, c) if ax == 'z' else (c, L + h / 2, line)
    DOORS.append(dict(a=a, b=b, price=price, name=AREAS[b], lv=lv, box=dict(min=bmin, max=bmax), at=at, axis=ax, line=line, c=c, w=w))
    opening(lv, ax, line, c, w, L, L + h, 'door', len(DOORS) - 1)

# free doorways (lv, axis, line, centre): into the enclosed rooms of an area (10 wide: a crowd gets through)
WAYS = [
    ('G', 'z', 32, 72), ('G', 'x', 0, -78), ('G', 'x', 12, -88), ('G', 'x', -48, -32), ('G', 'x', -48, -8),
    ('G', 'x', -48, 26), ('G', 'x', -48, 52), ('G', 'x', -48, 83), ('G', 'x', -48, 121),
    ('U', 'x', 0, -78), ('U', 'x', 12, -88), ('U', 'x', -48, -32), ('U', 'x', -48, -8), ('U', 'x', -48, 26),
    ('U', 'x', -48, 52), ('U', 'x', 68, 0), ('U', 'x', -48, 100),
    ('B', 'x', 12, -80), ('B', 'x', -48, -28), ('B', 'x', -76, -28), ('B', 'x', -48, 4), ('B', 'x', -76, 4),
    ('B', 'x', -48, 36), ('B', 'x', -76, 36), ('B', 'z', -12, -62), ('B', 'z', 20, -62),
]
for (lv, ax, line, c) in WAYS:
    opening(lv, ax, line, c, WAY_W, LV[lv], LV[lv] + WAY_H, 'doorway')

# ---------------------------------------------------------------- zombie windows: where they climb in
# (area, level, kind, axis, line, centre). kind: window (6 x 6, boarded; outside a hedged bay on the ground, a fire
# escape upstairs), gate (a gap in the roof's parapet onto a ladder cage), grate (a boarded grate in the basement onto a
# drain pit), shed (in the courtyard: a groundskeeper's shed whose boarded door they come out of)
ZW = [
    ('lobby', 'G', 'window', 'x', 96, -14), ('lobby', 'G', 'window', 'x', 96, 14), ('lobby', 'G', 'window', 'x', 96, 48),
    ('cafe', 'G', 'window', 'x', 96, -108), ('cafe', 'G', 'window', 'x', 96, -88), ('cafe', 'G', 'window', 'x', 96, -48),
    ('cafe', 'G', 'window', 'z', -120, 52), ('cafe', 'G', 'window', 'z', -120, 80),
    ('whall', 'G', 'window', 'z', -120, 6), ('whall', 'G', 'window', 'z', -120, 20),
    ('lab', 'G', 'window', 'x', -88, -104), ('lab', 'G', 'window', 'x', -88, -72), ('lab', 'G', 'window', 'z', -120, -64),
    ('lab', 'G', 'window', 'z', -120, -46),
    ('court', 'G', 'shed', 'z', -32, -21), ('court', 'G', 'shed', 'z', 32, 21),
    ('gym', 'G', 'window', 'z', 160, -12), ('gym', 'G', 'window', 'z', 160, 20), ('gym', 'G', 'window', 'z', 160, 44),
    ('nhall', 'G', 'window', 'x', -88, -40), ('nhall', 'G', 'window', 'x', -88, -8), ('nhall', 'G', 'window', 'x', -88, 24),
    ('lockers', 'G', 'window', 'x', -88, 52),
    ('gymwing', 'G', 'window', 'x', -88, 83), ('gymwing', 'G', 'window', 'x', -88, 121), ('gymwing', 'G', 'window', 'z', 160, -40),
    ('weights', 'G', 'window', 'x', 96, 88), ('weights', 'G', 'window', 'x', 96, 136), ('weights', 'G', 'window', 'z', 160, 76),
    ('upper', 'U', 'window', 'x', -88, -40), ('upper', 'U', 'window', 'x', -88, -8), ('upper', 'U', 'window', 'x', -88, 24),
    ('upper', 'U', 'window', 'x', -88, 52), ('upper', 'U', 'window', 'z', -120, 6), ('upper', 'U', 'window', 'z', -120, 20),
    ('library', 'U', 'window', 'z', -120, 40), ('library', 'U', 'window', 'z', -120, 72), ('library', 'U', 'window', 'x', 96, -100),
    ('library', 'U', 'window', 'x', 96, -72), ('library', 'U', 'window', 'x', 96, -44),
    ('art', 'U', 'window', 'x', -88, -104), ('art', 'U', 'window', 'x', -88, -72), ('art', 'U', 'window', 'z', -120, -64),
    ('art', 'U', 'window', 'z', -120, -46),
    ('office', 'U', 'window', 'x', 96, -16), ('office', 'U', 'window', 'x', 96, 16), ('lounge', 'U', 'window', 'x', 96, 48),
    ('complab', 'U', 'window', 'x', -88, 83), ('complab', 'U', 'window', 'x', -88, 121), ('complab', 'U', 'window', 'z', 160, -40),
    ('music', 'U', 'window', 'x', 96, 88), ('music', 'U', 'window', 'x', 96, 136), ('music', 'U', 'window', 'z', 160, 76),
    ('roof', 'R', 'gate', 'x', -88, -80), ('roof', 'R', 'gate', 'x', -88, 0), ('roof', 'R', 'gate', 'x', -88, 80),
    ('roof', 'R', 'gate', 'z', -120, -16),
    ('tunnels', 'B', 'grate', 'x', -88, -20), ('tunnels', 'B', 'grate', 'x', -88, 40), ('tunnels', 'B', 'grate', 'x', 12, -110),
    ('boiler', 'B', 'grate', 'x', -88, 86), ('boiler', 'B', 'grate', 'x', -88, 118),
]
WINDOWS = []      # the zombies mode's windows: area, kind, out (where one appears), in (where it lands inside),
                  # at (the boards' middle), n (into the room), w, h (the opening)
NICHES = []       # (kind, x0, z0, x1, z1, floor y, outward (ox, oz)): what the kit dresses outside each window
WIN = dict(window=(6.0, 3.0, 9.0), gate=(6.0, 0.0, 6.0), grate=(6.0, 1.0, 7.0), shed=(6.0, 0.5, 6.5))
SHEDS = []        # (x0, z0, x1, z1): the courtyard's sheds (walls and roof: hit boxes below)

def _outward(lv, ax, line, c):
    """which way is outside at this point of an outside wall: (ox, oz)"""
    if ax == 'x':
        return (0, 1) if room_at(lv, c, line + 0.5) is None else (0, -1)
    return (1, 0) if room_at(lv, line + 0.5, c) is None else (-1, 0)

for (area, lv, kind, ax, line, c) in ZW:
    L = LV[lv]
    w, s0, s1 = WIN[kind]
    base = 32.0 if kind == 'gate' else L
    if kind == 'shed':
        # a shed against the courtyard's wall, its boarded door facing into the courtyard (x 'line' is the wall it
        # backs onto: -32 / 32 here means 8 studs out from the hall's wall at -40 / 40)
        sx0, sx1 = (-40.0, -32.0) if line < 0 else (32.0, 40.0)
        SHEDS.append((sx0, c - 5.0, sx1, c + 5.0))
        ox = 1 if line < 0 else -1                          # the way out of the shed: into the courtyard
        fx = sx1 if ox > 0 else sx0
        WINDOWS.append(dict(area=area, kind=kind, out=((sx0 + sx1) / 2 - ox * 1.0, 0.0, c), **{'in': (fx + ox * 4.0, 0.0, c)},
                            at=(fx - ox * 0.5, (s0 + s1) / 2, c), n=(float(ox), 0.0, 0.0), w=w, h=s1 - s0))
        NICHES.append(('shed', sx0, c - 5.0, sx1, c + 5.0, 0.0, (-ox, 0)))
        continue
    ox, oz = _outward(lv, ax, line, c)
    opening(lv, ax, line, c, w, base + s0, base + s1 if kind != 'gate' else FENCE_TOP, 'zwin', len(WINDOWS))
    face = line + TX * (ox + oz)              # the outside face of the wall (ox or oz is 0)
    def P(d, l, y):
        return (face + ox * d, y, l) if ax == 'z' else (l, y, face + oz * d)
    depth = 8.0
    out = P(depth - 2.0, c, base)
    inn = P(-TX - 4.0, c, base)
    at = P(-TX / 2, c, base + (s0 + s1) / 2)
    WINDOWS.append(dict(area=area, kind=kind, out=out, **{'in': inn}, at=at, n=(-float(ox), 0.0, -float(oz)), w=w, h=s1 - s0))
    d0, d1 = face, face + (ox + oz) * depth
    if ax == 'x': nx0, nx1, nz0, nz1 = c - 6.0, c + 6.0, min(d0, d1), max(d0, d1)
    else: nx0, nx1, nz0, nz1 = min(d0, d1), max(d0, d1), c - 6.0, c + 6.0
    NICHES.append((kind, nx0, nz0, nx1, nz1, base, (ox, oz)))

# ---------------------------------------------------------------- courtyard glass (look only: the kit cuts the
# windows the halls look onto the courtyard through; the hit wall stays whole, glass stops you and your bullets)
GLASS = []        # (lv, axis, line, a0, a1, y0, y1)
def _court_glass():
    busy = [(o['lv'], o['axis'], o['line'], o['a0'] - 3, o['a1'] + 3) for o in OPENINGS]
    busy += [('G', 'z', -40.0, s[1] - 1, s[3] + 1) for s in SHEDS if s[0] < 0] + [('G', 'z', 40.0, s[1] - 1, s[3] + 1) for s in SHEDS if s[0] > 0]
    for lv in ('G', 'U'):
        L = LV[lv]
        for (ax, line, s0, s1) in (('x', -32, -40, 40), ('x', 32, -40, 40), ('z', -40, -32, 32), ('z', 40, -32, 32)):
            n = int((s1 - s0) // 16)
            for k in range(n):
                c = s0 + 8 + 16 * k
                a0, a1 = c - 5.5, c + 5.5
                if any(b[0] == lv and b[1] == ax and abs(b[2] - line) < 0.1 and a1 > b[3] and a0 < b[4] for b in busy): continue
                GLASS.append((lv, ax, float(line), a0, a1, L + 3.0, L + 12.0))
_court_glass()

# ---------------------------------------------------------------- cut the openings out of the walls
def _cut():
    global WALLS, FENCES
    for o in OPENINGS:
        ax, line = o['axis'], o['line']
        new = []
        for w in WALLS:
            x0, y0, z0, x1, y1, z1 = w['box']
            if y1 <= o['y0'] or y0 >= o['y1']: new.append(w); continue
            if ax == 'x':
                on = z1 - z0 <= 2.6 and z0 >= line - 2.1 and z1 <= line + 2.1
                u0, u1 = x0, x1
            else:
                on = x1 - x0 <= 2.6 and x0 >= line - 2.1 and x1 <= line + 2.1
                u0, u1 = z0, z1
            if not on or u1 <= o['a0'] or u0 >= o['a1']: new.append(w); continue
            pieces = []
            if y0 < o['y0']: pieces.append((u0, y0, u1, o['y0']))
            if y1 > o['y1']: pieces.append((u0, o['y1'], u1, y1))
            my0, my1 = max(y0, o['y0']), min(y1, o['y1'])
            if u0 < o['a0']: pieces.append((u0, my0, o['a0'], my1))
            if u1 > o['a1']: pieces.append((o['a1'], my0, u1, my1))
            for (p0, q0, p1, q1) in pieces:
                if p1 - p0 < 0.05 or q1 - q0 < 0.05: continue
                bx = (p0, q0, z0, p1, q1, z1) if ax == 'x' else (x0, q0, p0, x1, q1, p1)
                new.append(dict(w, box=bx))
            o['cut'] = o.get('cut', 0) + 1
        WALLS = new
        if o['kind'] in ('zwin', 'door'):      # (and the fence over a roof gate, a roof door)
            nf = []
            for (x0, y0, z0, x1, y1, z1) in FENCES:
                if ax == 'x': on, u0, u1 = (z0 >= line - 2.1 and z1 <= line + 2.1 and z1 - z0 < 1), x0, x1
                else: on, u0, u1 = (x0 >= line - 2.1 and x1 <= line + 2.1 and x1 - x0 < 1), z0, z1
                if not on or u1 <= o['a0'] or u0 >= o['a1'] or y1 <= o['y0'] or y0 >= o['y1']: nf.append((x0, y0, z0, x1, y1, z1)); continue
                for (p0, p1) in ((u0, o['a0']), (o['a1'], u1)):
                    if p1 - p0 > 0.05: nf.append((p0, y0, z0, p1, y1, z1) if ax == 'x' else (x0, y0, p0, x1, y1, p1))
            FENCES = nf
_cut()

# ================================================================ floors, ceilings, lids
SLABS = []        # (x0, y0, z0, x1, y1, z1, floor material, level)
def _slabs():
    for lv in ORDER:
        L = LV[lv]
        g = GRID[lv]
        groups = {}
        for i in range(NX):
            for j in range(NZ):
                k = g[i][j]
                if k < 0 or not ROOMS[k]['floor']: continue
                groups.setdefault(ROOMS[k]['fmat'], set()).add((i, j))
        for fm, cells in groups.items():
            for (i0, j0, i1, j1) in _greedy(cells):
                SLABS.append((GX0 + i0, L - 1.0, GZ0 + j0, GX0 + i1, L, GZ0 + j1, fm, lv))
        for r in ROOMS:
            if r['lv'] == lv and r['lid']:
                x0, z0, x1, z1 = r['r']
                SLABS.append((x0, r['lid'][0], z0, x1, r['lid'][1], z1, 'rooflid', lv))
_slabs()

# the ground outside the building (the niches stand on it; the kit dresses the school's grounds round it)
YARD = (-190.0, -150.0, 230.0, 170.0)
for (x0, z0, x1, z1) in _M.subtract([(YARD[0], YARD[1], YARD[2], YARD[3])], (FX0, FZ0, FX1, FZ1)):
    SLABS.append((x0, -1.0, z0, x1, 0.0, z1, 'grass', 'G'))

# ================================================================ stairs: ramps you collide with, steps the kit draws
STAIRS = []       # (kind, x0, z0, x1, z1, y0, y1, way up): for the kit and the plan
STEPS = []        # (x0, y0, z0, x1, y1, z1, kind): solid boxes (landings, the fill under a ramp, posts)
TILT = []         # (centre x, y, z, x axis (3), y axis (3), size (3), material, 'b', flags): the ramps
def step(x0, y0, z0, x1, y1, z1, kind='stair'):
    STEPS.append((min(x0, x1), y0, min(z0, z1), max(x0, x1), y1, max(z0, z1), kind))

THICK = 1.5
def ramp(a, b, width, mat='ramp'):
    """a sloped slab whose top runs from a = (x, y, z) to b (b higher), straight along x or along z, `width` across"""
    ax, ay, az = a
    bx, by, bz = b
    ln = math.sqrt((bx - ax) ** 2 + (by - ay) ** 2 + (bz - az) ** 2)
    u = ((bx - ax) / ln, (by - ay) / ln, (bz - az) / ln)
    c = (1.0, 0.0, 0.0) if abs(bz - az) > abs(bx - ax) else (0.0, 0.0, 1.0)      # across
    # the slab's normal: c x u or u x c, whichever points up
    n = (c[1] * u[2] - c[2] * u[1], c[2] * u[0] - c[0] * u[2], c[0] * u[1] - c[1] * u[0])
    if n[1] < 0: n = (-n[0], -n[1], -n[2])
    m = ((ax + bx) / 2 - n[0] * THICK / 2, (ay + by) / 2 - n[1] * THICK / 2, (az + bz) / 2 - n[2] * THICK / 2)
    TILT.append((m[0], m[1], m[2], c[0], c[1], c[2], n[0], n[1], n[2], width, THICK, ln, mat, 'b', ''))

# the main stairs: 16 steps (2 deep) up the east side of the locker hall, from z 22 north to the landing at z -10
MS_X0, MS_X1 = 54.0, 64.0
ramp((59.0, 0.0, 22.0), (59.0, 16.0, -10.0), MS_X1 - MS_X0)
for k in range(1, 17):            # (the steps' boxes under the ramp: nothing to walk into under the stairs)
    step(MS_X0, 0.0, 22 - 2.0 * k, MS_X1, k - 0.5, 22 - 2.0 * (k - 1), 'mainstair')
# (20 Nov, v2: a solid parapet up the stairs' open side, stepping with the treads, 3.4 over each; it stops you too)
for k in range(1, 17):
    step(MS_X0 - 0.35, 0.0, 22 - 2.0 * k, MS_X0 + 0.35, k - 0.5 + 3.4, 22 - 2.0 * (k - 1), 'parapet')
STAIRS.append(('main', MS_X0, -10.0, MS_X1, 22.0, 0.0, 16.0, 'north'))

def tower(x0, x1, xm, zA, zB, f1, f2, name, door_side):
    """a switchback stairwell, basement to roof. landing A (doors) zA = (z0, z1), landing B zB half way up; flight 1 on
    f1 (an x range) from landing A toward landing B, flight 2 on f2 back; a wall down the middle at xm. Each flight is a
    16-stud ramp rising 8 (a 1-in-2 slope: the zombies' nav takes it)"""
    toward_b = -1 if zB[0] < zA[0] else 1
    za_edge = zA[0] if toward_b < 0 else zA[1]          # where landing A meets the flights
    zb_edge = zB[1] if toward_b < 0 else zB[0]          # where landing B meets them
    for lv in ('B', 'G', 'U'):
        L = LV[lv]
        if lv != 'B': step(x0, L - 1.0, zA[0], x1, L, zA[1], 'landing')
        step(x0, L + 6.5 if lv != 'B' else L, zB[0], x1, L + 8.0, zB[1], 'landing')
        ramp(((f1[0] + f1[1]) / 2, L, za_edge), ((f1[0] + f1[1]) / 2, L + 8.0, zb_edge), f1[1] - f1[0])
        ramp(((f2[0] + f2[1]) / 2, L + 8.0, zb_edge), ((f2[0] + f2[1]) / 2, L + 16.0, za_edge), f2[1] - f2[0])
        if lv == 'B':            # (under the bottom flights: filled)
            step(f1[0], L, min(za_edge, zb_edge), f1[1], L + 0.2, max(za_edge, zb_edge), 'fill')
            step(f2[0], L, min(za_edge, zb_edge), f2[1], L + 7.0, max(za_edge, zb_edge), 'fill')
        step(xm - 0.5, L, min(za_edge, zb_edge), xm + 0.5, L + 16.0, max(za_edge, zb_edge), 'towerwall')
    # the roof: all of the top except over flight 2's last stretch (a rail round that hole)
    hz0, hz1 = min(za_edge, zb_edge), max(za_edge, zb_edge)
    for (a, b, c, d) in _M.subtract([(min(x0, x1), min(zA[0], zB[0]), max(x0, x1), max(zA[1], zB[1]))], (min(f2), hz0, max(f2), hz1)):
        step(a, 31.0, b, c, 32.0, d, 'landing')
    FENCES.append((xm - 0.2, 32.0, hz0, xm + 0.2, 35.5, hz1))
    FENCES.append((min(f2), 32.0, zb_edge - 0.2, max(f2), 35.5, zb_edge + 0.2))
    STAIRS.append((name, min(x0, x1), min(zA[0], zB[0]), max(x0, x1), max(zA[1], zB[1]), -16.0, 32.0, 'switchback'))

tower(-120, -100, -110, (-10, 0), (-34, -26), (-120, -110), (-110, -100), 'west', 's')
tower(140, 160, 150, (-58, -48), (-88, -74), (150, 160), (140, 150), 'east', 's')

# the bleachers: 16 rows (2 deep) you climb from the gym floor at x 108 west up to the balcony (x 76, y 16)
ramp((108.0, 0.0, 16.0), (76.0, 16.0, 16.0), 40.0, 'bleacher')
for k in range(1, 17):
    step(108 - 2.0 * k, 0.0, -4, 108 - 2.0 * (k - 1), k - 0.5, 36, 'bleacher')
# (20 Nov, v2: solid side walls up both sides of the bleachers, stepping with the rows, 3.2 over each)
for k in range(1, 17):
    for (za, zb) in ((-4.7, -4.0), (36.0, 36.7)):
        step(108 - 2.0 * k, 0.0, za, 108 - 2.0 * (k - 1), k - 0.5 + 3.2, zb, 'parapet')
STAIRS.append(('bleachers', 76, -4, 108, 36, 0.0, 16.0, 'west'))
FENCES.append((75.6, 16.0, -32.0, 76.0, 19.5, -4.0)); FENCES.append((75.6, 16.0, 36.0, 76.0, 19.5, 56.0))   # the balcony's rail
for z in (-26.0, -14.0, 42.0, 50.0): step(74.0, 0.0, z - 1.0, 76.0, 15.0, z + 1.0, 'post')                   # posts under it

# ================================================================ furniture (hit boxes the kit dresses; FURN for the kit)
FURN = []         # (kind, cx, y, cz, sx, sy, sz, turn, extra)
# (26 Nov 2026, the owner: "make sure propls dont clip into walls or other objkects and props") a prop set against a
# wall stops at the wall's hit face: v2's piers ARE that face (the panels sit 0.35 behind it), so a locker sunk half a
# stud in had the piers running through it. F() slides a prop out of any wall it was placed into, along the shorter
# way out. pieces made to sit in or on a wall keep their place (NO_NUDGE). the props check: school_clip.py
NO_NUDGE = {'stallwall', 'showerwall', 'stalls', 'showers', 'frontdoors', 'hoop', 'pipes', 'greenhouse', 'shed', 'board',
            'mirror', 'scoreboard', 'watertank', 'towerleg', 'flag', 'skylight', 'solar', 'dish', 'hvac', 'tree'}
def _off_walls(kind, cx, base, cz, sx, sy, sz):
    if kind in NO_NUDGE: return cx, cz
    for _ in range(4):
        moved = False
        for w in WALLS:
            b = w['box']
            ox = min(cx + sx / 2, b[3]) - max(cx - sx / 2, b[0])
            oy = min(base + sy, b[4]) - max(base, b[1])
            oz = min(cz + sz / 2, b[5]) - max(cz - sz / 2, b[2])
            if ox > 0.02 and oy > 0.02 and oz > 0.02:
                if ox < oz: cx += (ox + 0.02) * (1 if cx > (b[0] + b[3]) / 2 else -1)
                else: cz += (oz + 0.02) * (1 if cz > (b[2] + b[5]) / 2 else -1)
                moved = True
        if not moved: break
    return round(cx, 3), round(cz, 3)
def F(kind, cx, cz, lv, sx, sy, sz, turn=0, flags='', y=None, solid=True, **kw):
    base = LV[lv] if y is None else y
    if turn % 2: sx, sz = sz, sx
    cx, cz = _off_walls(kind, float(cx), base, float(cz), float(sx), float(sy), float(sz))
    FURN.append((kind, float(cx), base, float(cz), float(sx), float(sy), float(sz), turn, kw))
    if not solid: return
    if flags: rot(cx, base + sy / 2, cz, sx, sy, sz, 0.0, 'furn', flags)
    else: box(cx - sx / 2, base, cz - sz / 2, cx + sx / 2, base + sy, cz + sz / 2, 'furn_' + kind)

def classroom(x0, z0, x1, z1, lv):
    """a real classroom: the board on the west wall, the teacher's desk in front of it, 4 x 4 desks facing it"""
    F('board', x0 + 0.7, (z0 + z1) / 2, lv, 0.4, 6.0, 16.0, y=LV[lv] + 3.5, solid=False, face='e')
    F('teacherdesk', x0 + 6.5, (z0 + z1) / 2 + 2, lv, 3.6, 2.6, 7.0, face='e')
    for cx in (x0 + 12, x0 + 17, x0 + 22, x0 + 27):
        for cz in (z0 + 10, z0 + 16, z0 + 22, z0 + 28):
            F('desk', cx, cz, lv, 2.6, 2.5, 3.0, face='w')
    F('cubbies', x1 - 1.2, z0 + 8, lv, 1.6, 4.0, 10.0)
    F('flag', x0 + 1.2, z0 + 3, lv, 0.6, 9.0, 0.6, solid=False)

for (x0, x1) in ((-56, -24), (-24, 8), (8, 40)):
    classroom(x0, -88, x1, -48, 'G'); classroom(x0, -88, x1, -48, 'U')

def restroom(x0, z0, x1, z1, lv, stalls_on='north', sinks=None, stall_from=4):
    """stalls along one long wall (partitions, doors open), sinks on the other. sinks = (x from, x to) along that wall
    (26 Nov 2026: clear of the doorway, which is in that wall: the run used to cross it), or 'west' (on the west wall);
    stall_from = studs from the west wall to the first partition (clear of a zombie window landing there)"""
    n = int((x1 - x0 - stall_from - 4) // 5)
    zs = z0 if stalls_on == 'north' else z1 - 6.5
    for k in range(n + 1):
        F('stallwall', x0 + stall_from + 5 * k, zs + 3.25, lv, 0.4, 7.0, 6.5)
    F('stalls', x0 + stall_from + 2.5 * n, zs + 3.25, lv, 5.0 * n, 7.0, 6.5, solid=False, n=n, face='s' if stalls_on == 'north' else 'n')
    zk = z1 - 1.4 if stalls_on == 'north' else z0 + 1.4
    if sinks == 'west':
        zm = z0 + 2.8 if stalls_on == 'south' else z1 - 2.8
        F('sinks', x0 + 1.4, zm, lv, 4.4, 3.0, 2.6, turn=1, face='e')
        F('mirror', x0 + 0.6, zm, lv, 0.2, 4.0, 4.4, y=LV[lv] + 4.5, solid=False, face='e')
        return
    sa, sb = sinks if sinks else (x0 + 4, x0 + 4 + (x1 - x0 - 8) * 0.5)
    F('sinks', (sa + sb) / 2, zk, lv, sb - sa, 3.0, 2.6)
    F('mirror', (sa + sb) / 2, zk + (0.8 if stalls_on == 'north' else -0.8), lv, sb - sa, 4.0, 0.2, y=LV[lv] + 4.5, solid=False)   # (flat on the wall's face)

for lv in ('G', 'U'):
    restroom(-100, -34, -56, 0, lv, 'north', sinks=(-96, -84))           # (the doorway: x -83 .. -73 in the south wall)
    restroom(-120, 12, -56, 28, lv, 'south', sinks=(-115, -97), stall_from=8)   # (doorway x -93 .. -83; a window lands at x -116)
restroom(-88, 12, -72, 24, 'B', 'south', sinks='west')                    # (the doorway is most of the north wall)

# ---- the lobby: the reception desk, the trophy case, pillars, benches, the front doors (chained: look only)
F('reception', 0, 76, 'G', 18.0, 3.4, 4.0, face='n')
for x in (-16, 16):
    F('pillar', x, 58, 'G', 3.0, 15.0, 3.0)
F('trophy', -30.6, 84, 'G', 2.4, 7.5, 12.0)
F('bench', 28.8, 82, 'G', 9.0, 1.6, 2.2, turn=1)
F('bench', -22, 92, 'G', 9.0, 1.6, 2.2)
F('plant', 26, 92, 'G', 3.0, 5.0, 3.0)
F('plant', -28, 52, 'G', 3.0, 5.0, 3.0)
F('frontdoors', 0, 96, 'G', 12.0, 10.0, 1.0, solid=False, face='n')
# ---- the nurse: beds, a desk, a cabinet
for z in (60, 72, 84):
    F('bed', 59.5, z, 'G', 7.0, 2.4, 3.6)
F('desk_big', 40, 58, 'G', 3.6, 2.6, 7.0, face='e')
F('cabinet', 33.4, 88, 'G', 1.6, 6.0, 6.0)
# ---- the cafeteria: the kitchen behind the serving counter, long tables
for (z0, z1) in ((30, 44), (50, 76), (82, 94)):
    F('servery', -96.5, (z0 + z1) / 2, 'G', 3.0, 3.2, z1 - z0, face='e')
for (z0, z1) in ((30, 46), (58, 74), (86, 92)):
    F('kitchen', -118.0, (z0 + z1) / 2, 'G', 4.0, 3.6, z1 - z0)
F('fridge', -108, 30.2, 'G', 6.0, 8.0, 2.4)
for cx in (-84, -66, -48):
    for cz in (56, 70, 84):
        F('lunchtable', cx, cz, 'G', 12.0, 2.6, 6.4)
for cx in (-84, -66):
    F('lunchtable', cx, 38, 'G', 12.0, 2.6, 6.4)
F('trash', -58, 30.5, 'G', 2.0, 3.0, 2.0); F('trash', -34.5, 93.5, 'G', 2.0, 3.0, 2.0)
# ---- the lab: benches with sinks, fume cupboards
for cx in (-104, -88, -72):
    for cz in (-76, -61, -46):
        F('labbench', cx, cz, 'G', 9.0, 2.8, 4.2, face='n')
F('fume', -62, -86.4, 'G', 8.0, 6.6, 3.0)
F('fume', -118.4, -38.5, 'G', 3.0, 6.6, 8.0)      # (26 Nov: clear of the window the zombies climb in at z -46)
F('cabinet', -57.6, -62, 'G', 1.6, 6.0, 8.0)
F('skeleton', -63, -36.4, 'G', 2.0, 5.4, 2.0)      # (26 Nov: out of the hall door's way, into the corner)
# ---- lockers along the halls (between doors)
def lockers(x0, z0, x1, z1, lv, face):
    F('lockers', (x0 + x1) / 2, (z0 + z1) / 2, lv, x1 - x0, 6.5, z1 - z0, face=face)
lockers(62.4, -32, 64, -24, 'G', 'w')          # the locker hall: its east wall beside the stairs' foot and top
lockers(-56, -30, -54.4, -22, 'G', 'e'); lockers(-56, -16, -54.4, -2, 'G', 'e'); lockers(-56, 14, -54.4, 26, 'G', 'e')
lockers(-56, -30, -54.4, -2, 'U', 'e'); lockers(-56, 14, -54.4, 26, 'U', 'e')
lockers(62.4, -32, 64, -24.8, 'U', 'w')        # (26 Nov: clear of the upstairs door at z -20)
for (x0, x1) in ((-26, -14), (-2, 18), (32, 38)):     # (between the classroom doors)
    lockers(x0, -48, x1, -46.4, 'G', 's'); lockers(x0, -48, x1, -46.4, 'U', 's')
F('bench', 44, -12, 'G', 2.2, 1.6, 9.0)
# ---- the janitor's room
F('shelf', 62.6, -70, 'G', 2.4, 8.0, 20.0); F('mopsink', 44, -84, 'G', 4.0, 2.6, 4.0); F('cart', 50, -62, 'G', 3.0, 3.6, 5.0)
# ---- the courtyard: the big tree, planters, benches, picnic tables, the flagpole, the two sheds
F('tree', 0, 0, 'G', 14.0, 2.4, 14.0)
for (x, z) in ((-24, 26), (24, -26)):
    F('planter', x, z, 'G', 8.0, 2.4, 3.0)
for (x, z) in ((-14, 14), (14, -14), (-14, -14), (14, 14)):
    F('picnic', x, z, 'G', 7.0, 2.4, 6.0)
for (x, z, t) in ((-34, 6, 1), (34, -6, 1), (0, -27, 0), (0, 27, 0)):
    F('bench', x, z + (-0.6 if z == 27 else 0), 'G', 9.0, 1.6, 2.2, turn=t)     # (26 Nov: the north one clear of the lobby door)
F('flagpole', -34, 27, 'G', 0.8, 30.0, 0.8)
F('bikerack', 34, 8, 'G', 2.0, 2.4, 9.0)
for (x0, z0, x1, z1) in SHEDS:
    F('shed', (x0 + x1) / 2, (z0 + z1) / 2, 'G', x1 - x0, 10.0, z1 - z0, solid=False, door='e' if x0 < 0 else 'w')
# ---- the gym: mats, a vaulting box, the ball racks, hoops on the end walls
F('vault', 136, -20, 'G', 5.0, 3.2, 2.6)
F('mat', 126, 46, 'G', 9.0, 0.6, 6.0, flags='q')
F('mat', 142, 46, 'G', 9.0, 0.6, 6.0, flags='q')
F('ballrack', 156.6, -26, 'G', 2.4, 3.2, 5.0)
F('ballrack', 110, 54.4, 'G', 5.0, 3.2, 2.4)      # (26 Nov: clear of the weight room door, x 118 .. 130)
F('hoop', 134, -31.2, 'G', 6.0, 4.0, 1.6, y=8.0, solid=False, face='s')
F('hoop', 134, 55.2, 'G', 6.0, 4.0, 1.6, y=8.0, solid=False, face='n')
F('scoreboard', 159.4, 12, 'G', 0.6, 6.0, 14.0, y=20.0, solid=False, face='w')
# ---- the gym's locker rooms
for (x0, x1) in ((64, 102), (102, 140)):
    wx = 83 if x0 == 64 else 121              # (26 Nov: the zombies' window in the north wall: no lockers under it)
    lockers(x0 + 2, -88, wx - 4, -86.4, 'G', 's'); lockers(wx + 4, -88, x1 - 2, -86.4, 'G', 's')
    F('bench', (x0 + x1) / 2, -74, 'G', 16.0, 1.6, 2.2)
    F('bench', (x0 + x1) / 2, -64, 'G', 16.0, 1.6, 2.2)
    F('showers', x1 - 5, -57, 'G', 8.0, 7.5, 12.0, solid=False)
    F('showerwall', x1 - 9.2, -57, 'G', 0.4, 7.5, 12.0)
# ---- the weight room
for (x, z) in ((84, 70), (102, 70), (120, 70), (84, 84), (102, 84), (120, 84)):
    F('weightbench', x, z, 'G', 6.0, 1.8, 2.2)
F('rack', 158.4, 64, 'G', 2.4, 6.5, 12.0); F('rack', 146, 94.4, 'G', 12.0, 6.5, 2.4)
F('mirror', 64.6, 76, 'G', 0.2, 7.0, 24.0, y=1.5, solid=False)
# ---- the tunnels, storage, the workshop
for (x, z) in ((-40, -72), (-16, -52), (-30, -60), (6, -66), (14, -52), (-6, -72)):
    F('crate', x, z, 'B', 3.6, 3.6, 3.6)
F('crate', -40, -72, 'B', 3.6, 3.6, 3.6, y=-12.4)
for x in (-17.5, 14.5):                   # (26 Nov: beside the south doorways, x -33 .. -23 and -1 .. 9, not across them)
    F('shelf', x, -74.6, 'B', 9.0, 8.0, 2.4)
F('workbench', 25.5, -73.8, 'B', 9.0, 3.2, 3.4)    # (and beside the workshop's, x 31 .. 41); F('workbench', 50.6, -62, 'B', 2.8, 3.2, 12.0)
F('pipes', 10, -42, 'B', 108.0, 2.0, 2.0, y=-4.5, solid=False)
F('pipes', -50, -40, 'B', 2.0, 2.0, 80.0, y=-4.5, solid=False)
# ---- the boiler room: two boilers, the water heater, the generator; the power switch on the east wall
for x in (84, 112):
    F('boiler', x, -70, 'B', 12.0, 9.0, 12.0)
F('heater', 134, -42, 'B', 5.0, 9.0, 5.0)
F('generator', 150, -40, 'B', 6.0, 5.0, 5.0)
F('pipes', 102, -52, 'B', 70.0, 2.4, 2.4, y=-6.0, solid=False)
# ---- upstairs: the library (stacks you weave between, reading tables)
for x in (-108, -96, -84, -72):
    for (z0, z1) in ((52, 66), (74, 88)):
        F('bookshelf', x, (z0 + z1) / 2, 'U', 2.2, 7.0, z1 - z0)
for z in (58, 72, 86):
    F('readtable', -46, z, 'U', 7.0, 2.5, 4.0)
for x in (-100, -80, -64):
    F('readtable', x, 38, 'U', 7.0, 2.5, 4.0)
F('desk_big', -112, 94, 'U', 9.0, 3.4, 3.6)
F('globe', -36, 92, 'U', 2.2, 4.2, 2.2)
# ---- the art room: tables, easels, the kiln (the Cheat Machine on the north wall)
for cx in (-104, -88, -72):
    for cz in (-74, -57):
        F('arttable', cx, cz, 'U', 8.0, 2.5, 4.0)
for (x, z) in ((-110, -44), (-96, -44), (-82, -44), (-68, -46), (-62, -64)):
    F('easel', x, z, 'U', 2.7, 4.8, 1.6, face='n')
F('kiln', -115.5, -39.5, 'U', 5.0, 5.4, 5.0)
F('drying', -57.4, -76, 'U', 1.8, 6.0, 10.0)
# ---- the principal's office and the front office
F('counter', 0, 60, 'U', 22.0, 3.4, 3.0, face='n')
for x in (-24, -20, 20, 24):
    F('chair', x, 52, 'U', 2.2, 2.6, 2.2, face='s')
F('filing', 29.8, 58, 'U', 2.6, 4.5, 6.0)
F('bigdesk', 0, 80, 'U', 10.0, 2.7, 5.0, face='n')
F('bigchair', 0, 84, 'U', 2.6, 3.0, 2.6, solid=False, face='n')
for x in (-24, 24):
    F('bookshelf', x, 94.8, 'U', 10.0, 7.0, 2.2)
F('filing', -30.4, 74, 'U', 2.6, 4.5, 6.0)
F('trophy', 30.8, 80, 'U', 2.4, 7.5, 8.0)
# ---- the teachers' lounge
F('couch', 40, 88, 'U', 9.0, 2.8, 3.6, face='n'); F('couch', 56, 88, 'U', 9.0, 2.8, 3.6, face='n')
F('coffeetable', 48, 82, 'U', 7.0, 1.6, 3.0, flags='q')
F('counter', 62.4, 64, 'U', 2.6, 3.4, 16.0)
F('table', 44, 62, 'U', 8.0, 2.6, 5.0)
# ---- the computer lab
for z in (-80, -70, -60):
    for (x0, x1) in ((70, 96), (106, 134)):
        F('computers', (x0 + x1) / 2, z, 'U', x1 - x0, 2.7, 3.2, face='n')
F('desk_big', 72, -52, 'U', 9.0, 2.6, 3.6, face='s')
# ---- the music room: the piano, the drum riser, chairs
F('piano', 150, 66, 'U', 6.0, 4.2, 3.0, face='w')
F('riser', 112, 90, 'U', 24.0, 1.0, 8.0)
for (x, z) in ((98, 72), (104, 70), (110, 69), (116, 69), (122, 70), (128, 72), (100, 80), (108, 78), (116, 78), (124, 80)):
    F('chair', x, z, 'U', 2.2, 2.6, 2.2, flags='q', face='s')
F('cabinet', 66, 82, 'U', 2.0, 6.0, 12.0)
# ---- the roof: HVAC units, the greenhouse, the water tower, solar panels, skylights
for (x, z) in ((-80, -60), (-20, -60), (20, -44), (60, -60), (100, -44), (128, -70)):
    F('hvac', x, z, 'R', 12.0, 7.0, 8.0)
F('greenhouse', -104, -56, 'R', 22.0, 11.0, 30.0, solid=False)
for (x0, z0, x1, z1) in ((-115, -71, -93, -70.6), (-115, -41.4, -93, -41), (-115.4, -71, -115, -41), (-93, -71, -92.6, -62), (-93, -50, -92.6, -41)):
    box(x0, 32.0, z0, x1, 43.0, z1, 'greenglass')
for (x, z) in ((40, -80), (52, -80), (40, -68), (52, -68)):
    F('towerleg', x, z, 'R', 1.4, 18.0, 1.4)
F('watertank', 46, -74, 'R', 16.0, 12.0, 16.0, y=50.0, solid=False)
for z in (-84, -76):
    F('solar', -40, z, 'R', 24.0, 3.5, 5.0, face='s')
for x in (-6, 6):
    F('skylight', x, -40, 'R', 8.0, 2.0, 8.0)
F('dish', 112, -76, 'R', 6.0, 7.0, 6.0, face='s')

def FACE(item):
    """which way a piece of furniture faces: 'n' (-z), 's' (+z), 'e' (+x), 'w' (-x). Its own face= if given, else its back
    is to the nearest wall within 3 studs of its box (it faces away from it), else 's'"""
    kind, cx, y, cz, sx, sy, sz, turn, kw = item
    if kw.get('face'): return kw['face']
    lv = min(LV, key=lambda k: abs(LV[k] - y)) if y < 31.5 else 'R'
    r = room_at(lv, cx, cz)
    if r is None: return 's'
    x0, z0, x1, z1 = r['r']
    gaps = {'w': (cx - sx / 2) - x0, 'e': x1 - (cx + sx / 2), 'n': (cz - sz / 2) - z0, 's': z1 - (cz + sz / 2)}
    side = min(gaps, key=gaps.get)
    if gaps[side] > 3.0: return 's'
    return {'w': 'e', 'e': 'w', 'n': 's', 's': 'n'}[side]

# the kit's textured surfaces: one colour key each (the kit gives meshes of that colour world-scaled UVs and the
# layout a SurfaceAppearance picture for it); each hex is near its picture's own average, so an untextured view reads
# the same. Pictures: tools/roblox/school_textures.py (TEX there: the studs one repeat covers)
TEXKEY = {'lino': 'c5c3b9', 'cafetile': 'bdb2a0', 'terrazzo': 'd7d1c5', 'rtile_floor': 'c9d2d4', 'rtile_wall': 'e4e6e2',
          'hallwall': 'd9d3c3', 'classwall': 'e2dccd', 'block': 'c2c0ba', 'brick': '8d5f4f', 'gymwood': 'cfa66f',
          'woodfloor': 'a8794f', 'carpet': '7d8792', 'ceiling': 'eceae4', 'concrete': '9c9a94', 'chalkboard': '33473b',
          'pavers': 'a99d8a', 'rubber': '35363a', 'lockers': '74859a'}
ACCENT = '3f7f86'      # the school's one accent (muted teal): seats, trims, the trophy case, mats

# ================================================================ machines, wall buys, the crate, the power
def face(lv, ax, line, c, into):
    """the point on a wall's face toward the room on side `into` (+1: the + side of the line) at c along it"""
    other = room_at(lv, line - into * 0.5, c) if ax == 'z' else room_at(lv, c, line - into * 0.5)
    off = 0.0 if other is None else TI / 2
    if ax == 'z': return (line + into * off, c), (float(into), 0.0)
    return (c, line + into * off), (0.0, float(into))

def onwall(lv, ax, line, c, into, up, out=0.05):
    (fx, fz), (nx, nz) = face(lv, ax, line, c, into)
    return (fx + nx * out, LV[lv] + up, fz + nz * out), (nx, 0.0, nz)

# wall buys: chalk outlines (the contract: 4 wide x 2 tall, flat on the wall), shoulder height. OUR weapon ids
BUYS = []
for (w, price, lv, ax, line, c, into) in [
    ('revolver', 300, 'G', 'z', -32, 84, 1), ('smg', 900, 'G', 'z', 32, 58, -1),
    ('bread', 600, 'G', 'x', 28, -80, 1), ('shotgun', 1200, 'G', 'z', -40, -20, -1),
    ('lever', 1100, 'G', 'x', -88, -88, 1), ('banana', 750, 'G', 'z', 40, -24, 1),
    ('autoshot', 1400, 'G', 'x', -32, 92, 1), ('akimbo', 900, 'G', 'x', -32, -24, -1),
    ('sawnoff', 800, 'G', 'x', -48, 70, 1), ('lmg', 1600, 'G', 'z', 64, 66, 1),
    ('dmr', 1300, 'G', 'x', -32, 20, 1), ('burst', 1300, 'B', 'x', -48, 12, 1),
    ('ar', 1200, 'U', 'x', 32, -20, 1), ('sniper', 1500, 'U', 'z', 64, 26, -1),
    ('bow', 1000, 'U', 'x', 96, -86, -1), ('katana', 2000, 'U', 'z', -32, 86, 1),
    ('cards', 1100, 'U', 'z', 64, -70, 1), ('marbles', 1500, 'U', 'x', 96, 112, -1),
    ('tennis', 1200, 'R', 'z', -100, -22, 1), ('nailgun', 1400, 'B', 'z', 64, -62, 1),
]:
    at, n = onwall(lv, ax, line, c, into, 4.65)
    BUYS.append(dict(w=w, price=price, at=at, n=n, lv=lv))

def machine(lv, ax, line, c, into, depth):
    """the contract's marker: the floor point under the machine's front middle, facing out (the mode brings the model)"""
    (fx, fz), (nx, nz) = face(lv, ax, line, c, into)
    return dict(at=(fx + nx * depth, LV[lv], fz + nz * depth), n=(nx, 0.0, nz), lv=lv, depth=depth)

COLA = dict(machine('G', 'z', 64, 42, -1, 2.1), id='jank')               # Jank Cola, by the gym door
COLAS = [dict(machine('G', 'z', 32, 90, -1, 2.1), id='getup'),           # the lobby
         dict(machine('G', 'x', 96, -68, -1, 2.1), id='legday'),         # the cafeteria
         dict(machine('U', 'z', -120, 64, 1, 2.1), id='pockets'),        # the library
         dict(machine('U', 'z', -56, 40, 1, 2.1), id='thirdhand')]       # the upstairs hall
MACH = machine('U', 'x', -88, -88, 1, 2.2)                               # the Cheat Machine: the art room
UP = machine('U', 'x', 96, 0, -1, 3.0)                                   # the Warranty Voider: the principal's office
_p, _n = onwall('B', 'z', 160, -42, -1, 4.8, out=0.3)
POWER = dict(at=_p, n=_n, lv='B')                                       # the power: the boiler room's east wall
CRATE = dict(at=(154.0, 0.0, 2.0), n=(-1.0, 0.0, 0.0), price=950, lv='G')    # by the gym's east wall
CRATES = [CRATE, dict(at=(0.0, 0.0, -20.0), n=(0.0, 0.0, 1.0), lv='G'), dict(at=(-90.0, 16.0, 44.0), n=(0.0, 0.0, 1.0), lv='U'),
          dict(at=(4.0, -16.0, -56.0), n=(0.0, 0.0, 1.0), lv='B'), dict(at=(0.0, 32.0, -50.0), n=(0.0, 0.0, 1.0), lv='R')]

# the players' start: the lobby, facing the courtyard (north)
PLAYER_SPAWNS = [(float(x), 0.0, float(z)) for (x, z) in ((-12, 62), (-4, 62), (4, 62), (12, 62), (-12, 68), (-4, 68), (4, 68), (12, 68))]
for p in PLAYER_SPAWNS: SPAWNS.append((p[0], 0.3, p[2]))

# ================================================================ the niches' hit boxes (zombies' side of a window)
def _niches():
    for (kind, x0, z0, x1, z1, y, (ox, oz)) in NICHES:
        if kind == 'shed':
            # brick walls round three sides and the front with its doorway (the opening), a roof
            fx = x1 if ox < 0 else x0                     # (ox points from the courtyard into the shed: its front is the other side)
            front = x1 if x0 < 0 else x0
            back = x0 if x0 < 0 else x1
            box(min(back, back + (1 if x0 < 0 else -1)), 0.0, z0, max(back, back + (1 if x0 < 0 else -1)), 10.0, z1, 'brick')
            box(x0, 0.0, z0, x1, 10.0, z0 + 1.0, 'brick'); box(x0, 0.0, z1 - 1.0, x1, 10.0, z1, 'brick')
            fr0, fr1 = (front - 1.0, front) if x0 < 0 else (front, front + 1.0)
            c = (z0 + z1) / 2
            box(fr0, 0.0, z0, fr1, 10.0, c - 3.0, 'brick'); box(fr0, 0.0, c + 3.0, fr1, 10.0, z1, 'brick')
            box(fr0, 6.5, c - 3.0, fr1, 10.0, c + 3.0, 'brick'); box(fr0, 0.0, c - 3.0, fr1, 0.5, c + 3.0, 'brick')
            box(x0 - 0.5, 10.0, z0 - 0.5, x1 + 0.5, 11.0, z1 + 0.5, 'roofg')
            continue
        if kind == 'grate':
            box(x0, y - 1.0, z0, x1, y, z1, 'concrete')
            box(x0, y + 12.0, z0, x1, y + 13.0, z1, 'concrete')
        top = {'window': y + 15.0, 'gate': y + 12.0, 'grate': y + 12.0}[kind]
        if kind == 'window' and y > 1:          # a fire escape: a grated platform, the cage to stop you
            box(x0, y - 1.0, z0, x1, y, z1, 'grating')
        if kind == 'gate':
            box(x0, y - 1.0, z0, x1, y, z1, 'grating')
        sides = []
        if ox:
            far = x1 if ox > 0 else x0
            sides += [(far - 0.3 if ox > 0 else far, z0, far if ox > 0 else far + 0.3, z1)]
            sides += [(x0, z0 - 0.3, x1, z0), (x0, z1, x1, z1 + 0.3)]
        else:
            far = z1 if oz > 0 else z0
            sides += [(x0, far - 0.3 if oz > 0 else far, x1, far if oz > 0 else far + 0.3)]
            sides += [(x0 - 0.3, z0, x0, z1), (x1, z0, x1 + 0.3, z1)]
        hedge = kind == 'window' and y < 1
        for (a, b, c, d) in sides:
            if kind == 'grate':
                box(a, y, b, c, top, d, 'concrete'); continue
            if hedge:
                box(a, y, b, c, y + 7.0, d, 'hedge')
                FENCES.append((a, y + 7.0, b, c, top, d))
            else:
                FENCES.append((a, y, b, c, top, d))
        if kind != 'grate':
            FENCES.append((x0, top, z0, x1, top + 0.4, z1))
_niches()

# ================================================================ into the shared lists (SOLID, ROT) + checks
for w in WALLS:
    box(*w['box'], w['mat'])
for s in SLABS:
    box(*s[:6], s[6])
for s in STEPS:
    box(*s[:6], s[6])
for (x0, y0, z0, x1, y1, z1) in FENCES:
    rot((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, x1 - x0, y1 - y0, z1 - z0, 0.0, 'fence', 'c')

# the zombies' areas: each room's rectangle, floor to ceiling
AREA_RECTS = []
for r in ROOMS:
    if r['area'] in (None, '_roofx', '_gymtop'): continue
    L = 32.0 if r['lv'] == 'R' else LV[r['lv']]
    y1 = L + CEIL
    if r['look'] in ('balcony', 'gymair'): y1 = GYM_LID[0]
    if r['look'] == 'gym': y1 = L + 16.0
    if r['look'] == 'stairhole': y1 = L + CEIL
    if r['lv'] == 'R': y1 = TOWER_LID[0] if r['tower'] else 46.0
    if r['tower'] and r['lv'] != 'R': y1 = L + 16.0
    AREA_RECTS.append(dict(id=r['area'], name=AREAS[r['area']], room=r['id'], r=r['r'], y=(L, y1), lv=r['lv']))

NAV_BOUNDS = (FX0 - 1.0, -17.0, FZ0 - 1.0, FX1 + 1.0, 47.0, FZ1 + 1.0)
ZM = dict(label='Jankfield High', start=START, nav=NAV_BOUNDS, areas=AREA_RECTS, doors=DOORS, windows=WINDOWS, buys=BUYS,
          crates=CRATES, power=POWER, cola=COLA, colas=COLAS, mach=MACH, up=UP, spawns=PLAYER_SPAWNS)

# for the plan sheet and arena_plan.py
BOUNDS = (-200.0, 240.0, -160.0, 180.0)
LEVELS = [('BASEMENT (y -16)', -17.0, -2.0, -16.0), ('GROUND FLOOR (y 0)', -0.5, 14.0, 0.0),
          ('UPPER FLOOR (y 16)', 15.5, 30.0, 16.0), ('ROOF (y 32)', 31.5, 46.0, 32.0)]

blocked, floor_under, inside = _M.blocked, _M.floor_under, _M.inside

def check():
    bad = []
    for o in OPENINGS:
        if not o.get('cut'): bad.append(('opening cut nothing', o['lv'], o['kind'], o['axis'], o['line'], (o['a0'] + o['a1']) / 2))
    for p in SPAWNS:
        if floor_under(p) is None or inside((p[0], p[1] + 2.5, p[2])): bad.append(('spawn', p))
    for d in DOORS:
        (x, y, z) = d['at']
        for s in (-1, 1):
            q = (x + s * 2.0, d['box']['min'][1] + 2.5, z) if d['axis'] == 'z' else (x, d['box']['min'][1] + 2.5, z + s * 2.0)
            hit = inside(q)
            if hit: bad.append(('door blocked', d['a'], d['b'], s, hit[6]))
    for w in WINDOWS:
        p = w['in']
        if inside((p[0], p[1] + 2.5, p[2])): bad.append(('window lands in something', w['area'], p, inside((p[0], p[1] + 2.5, p[2]))[6]))
        if floor_under((p[0], p[1] + 0.3, p[2])) is None: bad.append(('window lands on no floor', w['area'], p))
        q = w['out']
        if floor_under((q[0], q[1] + 0.3, q[2])) is None: bad.append(('window spawn on no floor', w['area'], q))
        if inside((q[0], q[1] + 2.5, q[2])): bad.append(('window spawn inside something', w['area'], q, inside((q[0], q[1] + 2.5, q[2]))[6]))
    for b in BUYS + [COLA] + COLAS + [MACH, UP, POWER]:
        p = b['at']
        n = b['n']
        if 'depth' in b:      # a machine: the 4 x 3 of wall behind its front must be clear, and the floor in front
            for (u, v) in ((-1.4, -0.5), (1.4, -0.5), (0.0, -b['depth'] + 0.4), (0.0, 2.0)):
                q = (p[0] + n[0] * v + n[2] * u, LV[b['lv']] + 2.5, p[2] + n[2] * v + n[0] * u)
                if inside(q): bad.append(('machine space taken', b.get('id', 'machine'), p, inside(q)[6]))
        else:
            q = (p[0] + n[0] * 2.5, LV[b['lv']] + 2.5, p[2] + n[2] * 2.5)
            if inside(q): bad.append(('in front of a buy is blocked', b.get('w') or 'power', p, inside(q)[6]))
    for c in CRATES:
        p = c['at']
        for (u, v) in ((-2.7, 0), (2.7, 0), (0, 2.5)):
            q = (p[0] + c['n'][2] * u + c['n'][0] * v, p[1] + 2.0, p[2] + c['n'][0] * u + c['n'][2] * v)
            if inside(q): bad.append(('crate spot taken', p, inside(q)[6]))
    return bad

def tilt_top(x, z, lv):
    """the top of a ramp under (x, z) near level lv's height band, or None"""
    best = None
    for t in TILT:
        cx, cy, cz, Xx, Xy, Xz, Yx, Yy, Yz, sx, sy, sz = t[:12]
        # local coords: along X (across), Z = X x Y (along the slope)
        Zx, Zy, Zz = Xy * Yz - Xz * Yy, Xz * Yx - Xx * Yz, Xx * Yy - Xy * Yx
        dx, dz = x - cx, z - cz
        # the top plane: points p with (p - c).Y = sy/2; solve for y at (x, z)
        if abs(Yy) < 1e-6: continue
        y = cy + (sy / 2 - (dx * Yx + dz * Yz)) / Yy
        lx = dx * Xx + (y - cy) * Xy + dz * Xz
        lz = dx * Zx + (y - cy) * Zy + dz * Zz
        if abs(lx) <= sx / 2 and abs(lz) <= sz / 2:
            if best is None or y > best: best = y
    return best

if __name__ == '__main__':
    print('rooms %d, walls %d, slabs %d, steps %d, ramps %d, fences %d, furniture %d, solid %d, turned %d' % (
        len(ROOMS), len(WALLS), len(SLABS), len(STEPS), len(TILT), len(FENCES), len(FURN), len(SOLID), len(ROT)))
    print('doors %d, windows %d, buys %d, areas %d (%d rects), openings %d, glass %d' % (
        len(DOORS), len(WINDOWS), len(BUYS), len(set(a['id'] for a in AREA_RECTS)), len(AREA_RECTS), len(OPENINGS), len(GLASS)))
    probs = check()
    print('PROBLEMS %d' % len(probs))
    for p in probs[:40]: print('  ', p)
    # the ramps against the nav's rule: at most 1.6 studs of rise per 3 of run
    worst = 0.0
    for t in TILT:
        slope = abs(t[7]) and abs(math.sqrt(t[6] ** 2 + t[8] ** 2) / t[7])
        worst = max(worst, slope * 3.0)
    print('steepest ramp: %.2f studs of rise per 3 of run (the nav takes 1.6)' % worst)

# ================================================================ can you walk everywhere? (a flood over 1-stud cells)
def walk_check(verbose=True):
    """per level: cells with a floor at the level's height and nothing in the way from 0.6 to 5 studs up; a flood from
    the start (ground), from each stairwell landing (other levels) and from the main stairs' landing; every room should
    be reached. returns the rooms not reached"""
    import collections
    miss = []
    for lv in ORDER:
        L = LV[lv]
        floor, occ = set(), set()
        for b in SOLID:
            x0, y0, z0, x1, y1, z1 = b[:6]
            if abs(y1 - L) < 0.3 or (lv == 'R' and abs(y1 - 32.0) < 0.3):
                for i in range(int(math.floor(x0)), int(math.ceil(x1))):
                    for j in range(int(math.floor(z0)), int(math.ceil(z1))):
                        if x0 <= i + 0.5 <= x1 and z0 <= j + 0.5 <= z1: floor.add((i, j))
            if y1 > L + 0.6 and y0 < L + 5.0:       # (any overlap: a 0.3-stud fence between two cell middles still stops you)
                for i in range(int(math.floor(x0 + 0.05)), int(math.ceil(x1 - 0.05))):
                    for j in range(int(math.floor(z0 + 0.05)), int(math.ceil(z1 - 0.05))): occ.add((i, j))
        for r in ROT:
            if 'q' in r[8]: continue
            cx, cy, cz, sx, sy, sz = r[:6]
            if cy + sy / 2 > L + 0.6 and cy - sy / 2 < L + 5.0:
                for i in range(int(math.floor(cx - sx / 2 + 0.05)), int(math.ceil(cx + sx / 2 - 0.05))):
                    for j in range(int(math.floor(cz - sz / 2 + 0.05)), int(math.ceil(cz + sz / 2 - 0.05))): occ.add((i, j))
        free = floor - occ
        seeds = []
        if lv == 'G': seeds.append((0, 64))
        seeds += [(-110, -4), (150, -52)]
        if lv == 'U': seeds.append((59, -15))
        seen = set(s for s in seeds if s in free)
        q = collections.deque(seen)
        while q:
            i, j = q.popleft()
            for (a, b) in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if (a, b) in free and (a, b) not in seen: seen.add((a, b)); q.append((a, b))
        for r in ROOMS:
            if r['lv'] != lv or not r['floor'] or r['area'] in (None, '_roofx'): continue
            x0, z0, x1, z1 = (int(v) for v in r['r'])
            cells = [(i, j) for i in range(x0, x1) for j in range(z0, z1) if (i, j) in free]
            got = sum(1 for c in cells if c in seen)
            if not cells or got < 0.5 * len(cells): miss.append((lv, r['id'], got, len(cells)))
        out_ = [c for c in seen if not (FX0 - 2 <= c[0] < FX1 + 2 and FZ0 - 2 <= c[1] < FZ1 + 2)]
        far = [c for c in out_ if not any(n[1] - 1 <= c[0] <= n[3] + 1 and n[2] - 1 <= c[1] <= n[4] + 1 for n in NICHES)]
        if far: miss.append((lv, 'LEAKS OUTSIDE', len(far), far[:3]))
        if verbose: print('walk %s: %d free cells, %d reached, %d in the niches, %d past them' % (lv, len(free), len(seen), len(out_) - len(far), len(far)))
    return miss

if __name__ == '__main__':
    m = walk_check()
    print('ROOMS NOT REACHED %d %s' % (len(m), m))
