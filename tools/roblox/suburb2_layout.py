# SUBURB v2: "CUL-DE-SAC" (17 Nov 2026; the owner: "can you create an entirely new bazar desert, suburb, make the shape
# unique, give it like unique properties ... theyre all v2 versions"). The hit boxes, spawns, pads and water, in studs
# local to the arena's origin (street level y = 0). Plain Python: the plan (arena_plan.py) and the kit
# (suburb2_models.py) read the same numbers.
#
# The shape is a dumbbell, mirror-symmetric across x = 0 (attackers spawn in the west bulb, defenders in the east):
#   a round cul-de-sac at each end (the turning circle, a planted island, garden hedges as spawn cover, houses round it)
#   a main street between them, opening in the middle onto a village green (a hedged square with a bandstand)
#   two-storey houses along the street you can go through: front door, back door, a stair, upstairs windows over the
#   street and the yards; garages with flat roofs that lead in through an upstairs window
#   fenced backyards behind the houses: the flank lanes. north: two swimmable pools and a tree house up a stair.
#   south: trampolines that throw you onto a garage roof or across the yards onto a play fort, sheds, barbecues
# (18 Nov 2026: the builder opens the houses' roofs, roofs.open_up in suburb2_models.py: the hit boxes follow the kit's
# roofs and nothing stands over them; the houses round the turning circles shed you, being right over the spawns.)
# Everything that is not walkable is solid up to y 150 (no roofs to stand on but the garages', the tree house, the
# fort), the edge closed by an invisible wall and a lid. Gravity in play is 78 studs/s^2 (Config.grav), a jump about
# 4.9 studs: picket fences (3.2) are jumpable, hedges (5.6) are not.
import math

LID = 150.0
STEP, RUN = 1.0, 1.4
G = 78.0                 # workspace.Gravity in play (roblox/src/shared/Config.luau grav = 26 * 3)
JUMP = 27.6              # the jump's launch speed (Config.jump)
UP = 12.0                # the houses' upper floor (top)
WALLTOP = 24.0           # the houses' walls; the roof mass above
T = 1.2                  # wall thickness
GROOF = 11.0             # garage roofs
FENCE = 3.2

MATS = {
    'asphalt': ('Asphalt', '62656a', 'asphalt'),
    'lawn': ('Grass', '7d9268', 'grass'),
    'house': ('SmoothPlastic', 'd8d3c8', 'siding'),
    'roof': ('Slate', '6b6e74', 'roof'),
    'garage': ('SmoothPlastic', 'cfcac0', 'siding'),
    'fence': ('WoodPlanks', 'ece9e2', 'wood'),
    'hedge': ('Grass', '5c7552', 'hedge'),
    'wood': ('WoodPlanks', 'a3815e', 'wood'),
    'car': ('Metal', '9aa0a6', 'metal'),
    'tree': ('Wood', '75604b', 'wood'),
    'stone': ('Concrete', 'd6d0c4', 'stone'),
    'floor': ('WoodPlanks', 'b89a78', 'wood'),
    'step': ('WoodPlanks', 'ad8e6b', 'wood'),
    'edge': ('SmoothPlastic', 'c0c4c8', 'edge'),
    'ledge': ('SmoothPlastic', 'c8c4bd', 'ledge'),   # the wall box's step (wallbox.py)
    'bound': ('SmoothPlastic', 'c8c4bd', 'bound'),   # its walls
    'rail': ('Metal', 'e8e6e0', 'metal'),
    'cover': ('SmoothPlastic', 'cfc8bc', 'cover'),
}

SOLID, ROT, SPAWNS, PADS, WATER, NOTES = [], [], [], [], [], []
TEAM = {'att': [], 'def': [], 'mid': []}
HOUSES = []      # (x0, z0, x1, z1, front, garage side or None, stair side, enterable) for the kit
GARAGES = []     # (x0, z0, x1, z1, front)
POOLS = []       # (x0, z0, x1, z1)
ROUNDS = []      # (cx, cz, r, y0, y1, mat)
BULB_HOUSES = [] # (cx, cz, angle (radians, the way the front faces), width, depth)
STAIRS = []      # (x0, z0, x1, z1, axis 'x'|'z', direction +1|-1, steps): every stair, for the kit
OPENS = []       # (x0, y0, z0, x1, y1, z1, kind): door and window openings (the kit frames them)
CARS = []        # (no cars any more: the owner, 17 Nov, "remove the cars on suburb")
STREETSETS = []  # (x0, z0, x1, z1, kind): where the cars stood, cover of the same size: 'wall' a garden wall and clipped
                 # hedge (in front of the spawns), 'kerb' a brick planter with a hedge, a mailbox cluster and wheelie bins
FENCES = []      # (x0, z0, x1, z1)

def box(x0, y0, z0, x1, y1, z1, m):
    SOLID.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), m))

def rot(cx, cy, cz, sx, sy, sz, yaw, m, flags=''):
    ROT.append((cx, cy, cz, sx, sy, sz, yaw, m, flags))

def round_(cx, cz, r, y0, y1, m, n=4, flags='', note=True):
    if note: ROUNDS.append((cx, cz, r, y0, y1, m))
    for k in range(n):
        rot(cx, (y0 + y1) / 2, cz, 2 * r, y1 - y0, 2 * r, 90.0 * k / n, m, flags)

def ang_box(cx, cz, a, r0, r1, wid, y0, y1, m, flags=''):
    rc = (r0 + r1) / 2
    rot(cx + rc * math.cos(a), (y0 + y1) / 2, cz + rc * math.sin(a), r1 - r0, y1 - y0, wid, -math.degrees(a), m, flags)

def subtract(rects, h):
    out = []
    hx0, hz0, hx1, hz1 = h
    for (x0, z0, x1, z1) in rects:
        if hx1 <= x0 or hx0 >= x1 or hz1 <= z0 or hz0 >= z1:
            out.append((x0, z0, x1, z1)); continue
        if z0 < hz0: out.append((x0, z0, x1, hz0))
        if hz1 < z1: out.append((x0, hz1, x1, z1))
        mz0, mz1 = max(z0, hz0), min(z1, hz1)
        if x0 < hx0: out.append((x0, mz0, hx0, mz1))
        if hx1 < x1: out.append((hx1, mz0, x1, mz1))
    return out

# ---------------------------------------------------------------- mirroring: the west half is written once
class Mirror:
    """everything added between begin() and end() is copied to the east half (x -> -x; turned boxes' yaw -> -yaw)"""
    def __enter__(self):
        self.n = {k: len(v) for k, v in self.lists().items()}
        return self
    def lists(self):
        return {'SOLID': SOLID, 'ROT': ROT, 'PADS': PADS, 'WATER': WATER, 'HOUSES': HOUSES, 'GARAGES': GARAGES,
                'POOLS': POOLS, 'ROUNDS': ROUNDS, 'BULB_HOUSES': BULB_HOUSES, 'STAIRS': STAIRS, 'OPENS': OPENS,
                'CARS': CARS, 'FENCES': FENCES, 'NOTES': NOTES, 'STREETSETS': STREETSETS}
    def __exit__(self, *a):
        L = self.lists()
        new = {k: list(v[self.n[k]:]) for k, v in L.items()}
        for b in new['SOLID']: SOLID.append((-b[3], b[1], b[2], -b[0], b[4], b[5], b[6]))
        for r in new['ROT']: ROT.append((-r[0], r[1], r[2], r[3], r[4], r[5], -r[6], r[7], r[8]))
        for p in new['PADS']: PADS.append((-p[3], p[1], p[2], -p[0], p[4], p[5], -p[6], p[7], p[8]))
        for w in new['WATER']: WATER.append((-w[3], w[1], w[2], -w[0], w[4], w[5]))
        for h in new['HOUSES']:
            x0, z0, x1, z1, fr, gs, ss, en = h
            flip = {'x+': 'x-', 'x-': 'x+', None: None}
            HOUSES.append((-x1, z0, -x0, z1, fr, flip[gs], flip[ss], en))
        for g in new['GARAGES']: GARAGES.append((-g[2], g[1], -g[0], g[3], g[4]))
        for p in new['POOLS']: POOLS.append((-p[2], p[1], -p[0], p[3]))
        for r in new['ROUNDS']: ROUNDS.append((-r[0], r[1], r[2], r[3], r[4], r[5]))
        for b in new['BULB_HOUSES']: BULB_HOUSES.append((-b[0], b[1], math.pi - b[2], b[3], b[4]))
        for s in new['STAIRS']:
            x0, z0, x1, z1, ax, d, n = s
            STAIRS.append((-x1, z0, -x0, z1, ax, -d if ax == 'x' else d, n))
        for o in new['OPENS']: OPENS.append((-o[3], o[1], o[2], -o[0], o[4], o[5], o[6]))
        for c in new['CARS']: CARS.append((-c[2], c[1], -c[0], c[3]))
        for c in new['STREETSETS']: STREETSETS.append((-c[2], c[1], -c[0], c[3], c[4]))
        for f in new['FENCES']: FENCES.append((-f[2], f[1], -f[0], f[3]))
        for n_ in new['NOTES']: NOTES.append((-n_[0], n_[1], n_[2], n_[3]))

# ---------------------------------------------------------------- pieces
def wall(axis, c0, c1, a0, a1, y0, y1, holes, m='house'):
    """a wall lying along `axis` ('x': from a0 to a1 in x, its thickness c0..c1 in z; 'z': the other way) from y0 to
    y1, with rectangular holes [(a0, a1, y0, y1, kind)]"""
    rects = [(a0, y0, a1, y1)]
    for (h0, h1, hy0, hy1, kind) in holes:
        rects = subtract(rects, (h0, hy0, h1, hy1))
        if axis == 'x': OPENS.append((h0, hy0, c0, h1, hy1, c1, kind))
        else: OPENS.append((c0, hy0, h0, c1, hy1, h1, kind))
    for (u0, v0, u1, v1) in rects:
        if axis == 'x': box(u0, v0, c0, u1, v1, c1, m)
        else: box(c0, v0, u0, c1, v1, u1, m)

def stair(x0, x1, z_start, direction, n, y_from=0.0, m='step', width_axis='x', rails=False):
    """n steps along z from z_start (direction +1 or -1), across x0..x1, each 1 up and RUN along; solid down to y_from"""
    for k in range(1, n + 1):
        za = z_start + direction * (k - 1) * RUN
        zb = z_start + direction * k * RUN
        box(x0, y_from, za, x1, y_from + k * STEP, zb, m)
    zend = z_start + direction * n * RUN
    STAIRS.append((x0, min(z_start, zend), x1, max(z_start, zend), 'z', direction, n))
    return zend

def house(x0, z0, x1, z1, front, garage_side=None, stair_side='x-', enterable=True):
    """a two-storey house. front: +1 the street side is z1, -1 it is z0. enterable: doors front and back, a stair inside
    along the stair_side wall, the upper floor at UP with windows (openings) front, back and over the garage"""
    HOUSES.append((x0, z0, x1, z1, front, garage_side, stair_side, enterable))
    box(x0, WALLTOP, z0, x1, LID, z1, 'roof')
    if not enterable:
        box(x0, 0, z0, x1, WALLTOP, z1, 'house')
        return
    zf_wall = (z1 - T, z1) if front > 0 else (z0, z0 + T)
    zb_wall = (z0, z0 + T) if front > 0 else (z1 - T, z1)
    mid = (x0 + x1) / 2
    sx0 = x0 + T if stair_side == 'x-' else x1 - T - 5.0          # the stair's band across x
    sx1 = sx0 + 5.0
    # the front wall: a door in the middle, two upstairs windows
    wall('x', zf_wall[0], zf_wall[1], x0, x1, 0, WALLTOP,
         [(mid - 3, mid + 3, 0, 9, 'door'), (x0 + 4, x0 + 10, UP + 1.5, UP + 7.5, 'window'), (x1 - 10, x1 - 4, UP + 1.5, UP + 7.5, 'window')])
    # the back wall: the back door away from the stair, two upstairs windows
    bd = (mid + 1, mid + 7) if stair_side == 'x-' else (mid - 7, mid - 1)
    wall('x', zb_wall[0], zb_wall[1], x0, x1, 0, WALLTOP,
         [(bd[0], bd[1], 0, 9, 'door'), (x0 + 9, x0 + 15, UP + 1.5, UP + 7.5, 'window'), (x1 - 15, x1 - 9, UP + 1.5, UP + 7.5, 'window')])
    # the side walls: on the garage's side an upstairs window just over the garage's roof
    zi0, zi1 = z0 + T, z1 - T
    for side in ('x-', 'x+'):
        xa, xb = (x0, x0 + T) if side == 'x-' else (x1 - T, x1)
        holes = []
        if side == garage_side:
            wz = (z1 - 16, z1 - 10) if front > 0 else (z0 + 10, z0 + 16)
            holes.append((wz[0], wz[1], GROOF + 1.6, UP + 7.5, 'window'))
        wall('z', xa, xb, zi0, zi1, 0, WALLTOP, holes)
    # the stair: from just inside the front door's side wall toward the back, 12 steps up to the upper floor
    zs = (z1 - T - 2.0) if front > 0 else (z0 + T + 2.0)
    d = -front
    stair(sx0, sx1, zs, d, int(UP))
    # the upper floor, with the stairwell cut where the stair needs headroom (steps 5..12)
    ha, hb = zs + d * 4 * RUN, zs + d * int(UP) * RUN
    hole = (sx0, min(ha, hb), sx1, max(ha, hb))
    for (a0, c0, a1, c1) in subtract([(x0 + T, zi0, x1 - T, zi1)], hole):
        box(a0, UP - 0.8, c0, a1, UP, c1, 'floor')
    # rails round the stairwell on the upper floor (they stop you, not shots): its open long side and its front end
    rx = sx1 if stair_side == 'x-' else sx0
    rot(rx + (0.2 if stair_side == 'x-' else -0.2), UP + 1.8, (hole[1] + hole[3]) / 2, 0.4, 3.6, hole[3] - hole[1], 0.0, 'rail', 'c')
    rot((sx0 + sx1) / 2, UP + 1.8, ha, sx1 - sx0, 3.6, 0.4, 0.0, 'rail', 'c')     # (across its lower end: the stair comes up at the other)

def garage(x0, z0, x1, z1, front):
    GARAGES.append((x0, z0, x1, z1, front))
    box(x0, 0, z0, x1, GROOF, z1, 'garage')
    # a low parapet along its street edge (cover on the roof)
    zf = (z1 - 0.8, z1) if front > 0 else (z0, z0 + 0.8)
    box(x0, GROOF, zf[0], x1, GROOF + 2.2, zf[1], 'garage')

def fence(x0, z0, x1, z1, gates=()):
    """a picket fence along x or z with gate gaps [(a, b)] along its length"""
    along_x = (x1 - x0) > (z1 - z0)
    a0, a1 = (x0, x1) if along_x else (z0, z1)
    cuts = sorted(gates)
    pts, cur = [], a0
    for (g0, g1) in cuts:
        if g0 > cur: pts.append((cur, g0))
        cur = max(cur, g1)
    if cur < a1: pts.append((cur, a1))
    for (u0, u1) in pts:
        if along_x: box(u0, 0, z0, u1, FENCE, z1, 'fence'); FENCES.append((u0, z0, u1, z1))
        else: box(x0, 0, u0, x1, FENCE, u1, 'fence'); FENCES.append((x0, u0, x1, u1))

def hedge_wall(x0, z0, x1, z1):
    """a garden wall with a clipped hedge behind it: the size and height a parked car was (full cover)"""
    STREETSETS.append((x0, z0, x1, z1, 'wall'))
    box(x0, 0, z0, x1, 5.4, z1, 'hedge')

def kerb_set(x0, z0, x1, z1):
    """along the kerb where a car was: a brick planter with a hedge on it (5.4, full cover), a mailbox cluster (5.0) and
    two wheelie bins (4.2) at its east end, all in the car's footprint"""
    STREETSETS.append((x0, z0, x1, z1, 'kerb'))
    a, b = (x0, x1) if abs(x0) > abs(x1) else (x1, x0)        # (a: the end away from the middle)
    sg = 1.0 if b > a else -1.0
    u = lambda t: a + sg * t
    box(u(0.0), 0, z0, u(7.0), 2.4, z1, 'stone'); box(u(0.0), 2.4, z0, u(7.0), 5.4, z1, 'hedge')
    box(u(7.2), 0, z0 + 1.2, u(9.2), 5.0, z1 - 1.2, 'rail')
    box(u(9.4), 0, z0 + 0.6, u(12.0), 4.2, z1 - 0.6, 'cover')

def pool(x0, z0, x1, z1):
    POOLS.append((x0, z0, x1, z1))
    box(x0, -7.0, z0, x1, -6.0, z1, 'stone')                      # its floor
    WATER.append((x0, -6.0, z0, x1, -0.8, z1))

def tree(x, z, r=1.3, h=30.0):
    round_(x, z, r, 0, h, 'tree', n=2)

# ================================================================ the ground: one slab, holes for the pools
X_EDGE, Z_EDGE = 176.0, 112.0
BULB = (112.0, 0.0, 32.0)        # |x| of the cul-de-sac's centre, its z, the turning circle's radius

with Mirror():
    pool(-80.0, -96.0, -58.0, -74.0)
holes = [(p[0], p[1], p[2], p[3]) for p in POOLS]
for (xa, za, xb, zb, m) in ((-X_EDGE, -18.0, X_EDGE, 18.0, 'asphalt'), (-X_EDGE, -Z_EDGE, X_EDGE, -18.0, 'lawn'), (-X_EDGE, 18.0, X_EDGE, Z_EDGE, 'lawn')):
    rects = [(xa, za, xb, zb)]
    for h in holes: rects = subtract(rects, h)
    for (x0, z0, x1, z1) in rects: box(x0, -6.0, z0, x1, 0.0, z1, m)
# the edge: invisible walls and a lid
box(-X_EDGE - 10, -6, -Z_EDGE - 10, -X_EDGE, LID, Z_EDGE + 10, 'edge')
box(X_EDGE, -6, -Z_EDGE - 10, X_EDGE + 10, LID, Z_EDGE + 10, 'edge')
box(-X_EDGE, -6, -Z_EDGE - 10, X_EDGE, LID, -Z_EDGE, 'edge')
box(-X_EDGE, -6, Z_EDGE, X_EDGE, LID, Z_EDGE + 10, 'edge')
box(-X_EDGE - 10, LID, -Z_EDGE - 10, X_EDGE + 10, LID + 5, Z_EDGE + 10, 'edge')
# the back hedges along both long edges (tall, solid): the yards' far side
box(-X_EDGE, 0, -Z_EDGE, X_EDGE, LID, -106.0, 'hedge')
box(-X_EDGE, 0, 106.0, X_EDGE, LID, Z_EDGE, 'hedge')

with Mirror():
    bx, bz, br = -BULB[0], BULB[1], BULB[2]
    # ---------------------------------------------------------- the cul-de-sac (west): houses round its far end
    for deg in (130.0, 180.0, 230.0):
        a = math.radians(deg)
        BULB_HOUSES.append((bx + 48.0 * math.cos(a), bz + 48.0 * math.sin(a), a + math.pi, 24.0, 20.0))
        ang_box(bx, bz, a, 38.0, 58.0, 24.0, 0, LID, 'house')
    for deg in (155.0, 205.0):                                     # garden walls closing the gaps between them
        ang_box(bx, bz, math.radians(deg), 37.0, 58.0, 2.0, 0, 8.0, 'fence')
    box(-X_EDGE, 0, -64.0, -166.0, LID, 64.0, 'hedge')             # behind them
    box(-X_EDGE, 0, -Z_EDGE, -150.0, LID, -50.0, 'hedge')          # the far corners
    box(-X_EDGE, 0, 50.0, -150.0, LID, Z_EDGE, 'hedge')
    # the island in the turning circle (a planter and a tree), garden hedges in front of the spawns (where cars were)
    round_(bx, bz, 6.0, 0, 2.4, 'cover')
    tree(bx, bz, 1.5, 34.0)
    # the lawns either side of the turning circle: a low hedge and a tree each (cover between the spawn and the yards)
    box(-128.0, 0, -29.4, -116.0, 3.0, -28.0, 'hedge'); tree(-100.0, -34.0, 1.3, 30.0)
    box(-128.0, 0, 28.0, -116.0, 3.0, 29.4, 'hedge'); tree(-100.0, 34.0, 1.3, 30.0)
    hedge_wall(-102.0, -17.0, -96.0, -5.0)
    hedge_wall(-102.0, 5.0, -96.0, 17.0)
    # ---------------------------------------------------------- the street (west half)
    kerb_set(-78.0, -11.5, -66.0, -5.5)                            # along the kerbs (where parked cars were)
    kerb_set(-50.0, 5.5, -38.0, 11.5)
    for x in (-88.0, -60.0, -36.0):
        round_(x, -19.0, 0.45, 0, 13.0, 'rail', n=2)               # street lamps
        round_(x, 19.0, 0.45, 0, 13.0, 'rail', n=2)
    # ---------------------------------------------------------- the north row: house 1 + garage, house 2, the passages
    house(-86.0, -52.0, -60.0, -24.0, +1, garage_side='x+', stair_side='x-')
    garage(-60.0, -46.0, -48.0, -24.0, +1)
    stair(-48.0, -44.5, -25.0, -1, int(GROOF))                     # an outside stair up to the garage's roof
    house(-38.0, -62.0, -16.0, -38.0, +1, stair_side='x-')
    box(-84.0, 0, -20.6, -76.0, 3.0, -19.4, 'hedge')               # low front hedges (cover)
    box(-36.0, 0, -36.2, -30.0, 3.0, -35.0, 'hedge')
    # ---------------------------------------------------------- the south row
    house(-86.0, 24.0, -60.0, 52.0, -1, garage_side='x+', stair_side='x-')
    garage(-60.0, 24.0, -48.0, 46.0, -1)
    house(-38.0, 38.0, -16.0, 62.0, -1, stair_side='x-')
    box(-84.0, 0, 19.4, -76.0, 3.0, 20.6, 'hedge')
    box(-24.0, 0, 35.0, -18.0, 3.0, 36.2, 'hedge')
    # ---------------------------------------------------------- the north yards: fences with gates, a pool
    fence(-86.25, -106.0, -85.75, -52.0, gates=[(-82.0, -76.0)])
    fence(-38.25, -106.0, -37.75, -62.0, gates=[(-90.0, -84.0)])
    fence(-10.25, -106.0, -9.75, -62.0, gates=[(-98.0, -92.0)])
    box(-58.0, 0, -66.0, -52.0, 1.2, -60.0, 'cover')                # pool loungers, a low garden wall
    box(-30.0, 0, -96.0, -18.0, 3.4, -94.0, 'cover')
    round_(-50.0, -92.0, 3.5, 0, 4.0, 'cover')                     # a hot tub
    tree(-26.0, -78.0, 1.4, 30.0)
    # ---------------------------------------------------------- the south yards: fences, trampolines, a shed, barbecues
    fence(-86.25, 52.0, -85.75, 106.0, gates=[(76.0, 82.0)])
    fence(-38.25, 62.0, -37.75, 106.0, gates=[(66.0, 72.0)])
    fence(-10.25, 62.0, -9.75, 106.0, gates=[(98.0, 104.0)])
    box(-82.0, 0, 90.0, -70.0, 10.0, 102.0, 'wood')                # a shed
    box(-68.0, 0, 70.0, -65.0, 3.2, 73.0, 'cover')                 # barbecues
    box(-24.0, 0, 96.0, -21.0, 3.2, 99.0, 'cover')
    tree(-26.0, 72.0, 1.4, 30.0)
    # trampolines: one throws you onto the garage's roof, one across the yards onto the play fort in the middle
    PADS.append((-58.0, 0.0, 54.0, -50.0, 0.9, 62.0, 0.0, 50.0, -16.0))
    PADS.append((-34.0, 0.0, 80.0, -26.0, 0.9, 88.0, 30.0, 44.0, 0.0))
    # (18 Nov 2026, the roofs open: roofs.open_up) a trampoline on the north garage's roof (up the outside stair) throws
    # you onto the house's roof, a way up besides the grapple. (not on the south garage's: a spawn stands there, and the
    # yard trampoline lands there by the upstairs window)
    PADS.append((-57.0, GROOF, -38.0, -51.0, GROOF + 0.9, -32.0, -10.0, 62.0, 0.0))     # (lands south of the ridge: the chimney's north of it)
    NOTES.extend([(-73.0, -38.0, 0, 'HOUSE'), (-27.0, -50.0, 0, 'HOUSE'), (-73.0, 38.0, 0, 'HOUSE'),
                  (-27.0, 50.0, 0, 'HOUSE'), (-69.0, -85.0, 0, 'POOL'), (-54.0, 58.0, 0, 'TRAMPOLINE'), (-30.0, 84.0, 0, 'TRAMPOLINE'),
                  (-54.0, -35.0, 1, 'GARAGE ROOF'), (-54.0, 35.0, 1, 'GARAGE ROOF'), (-73.0, -38.0, 1, 'UPSTAIRS'), (-27.0, 50.0, 1, 'UPSTAIRS')])

# ================================================================ the middle (built once, symmetric itself)
# the houses at the head of the green (solid), the passages beside them
house(-10.0, -62.0, 10.0, -38.0, +1, enterable=False)
house(-10.0, 38.0, 10.0, 62.0, -1, enterable=False)
# the village green: a hedged square with gaps at its corners, a bandstand in the middle, benches
HG = 18.0
for (x0, z0, x1, z1) in ((-12.0, -HG, 12.0, -HG + 1.4), (-12.0, HG - 1.4, 12.0, HG), (-HG, -12.0, -HG + 1.4, 12.0), (HG - 1.4, -12.0, HG, 12.0)):
    box(x0, 0, z0, x1, 5.6, z1, 'hedge')
round_(0.0, 0.0, 7.0, 0, 1.2, 'wood')                              # the bandstand's floor (a step up)
for k in range(8):
    a = 2 * math.pi * k / 8 + math.pi / 8
    round_(6.2 * math.cos(a), 6.2 * math.sin(a), 0.45, 1.2, 10.5, 'wood', n=2)
box(-13.0, 0, -9.0, -10.0, 2.0, -3.0, 'cover'); box(10.0, 0, 3.0, 13.0, 2.0, 9.0, 'cover')     # benches
box(-13.0, 0, 3.0, -10.0, 2.0, 9.0, 'cover'); box(10.0, 0, -9.0, 13.0, 2.0, -3.0, 'cover')
NOTES.extend([(-112.0, 0.0, 0, 'ATT'), (112.0, 0.0, 0, 'DEF'), (0.0, 0.0, 0, 'GREEN'), (0.0, -92.0, 1, 'TREE HOUSE'), (0.0, 86.0, 1, 'PLAY FORT')])
# the tree house (north yards, in the middle): a stair up the yard to a platform round a big tree
TH_Y = 14.0
zt = stair(-2.5, 2.5, -63.6, -1, int(TH_Y))
box(-9.0, TH_Y - 1.0, -100.0, 9.0, TH_Y, zt, 'wood')
tree(0.0, -91.5, 2.0, 40.0)
box(-5.0, TH_Y, -100.0, 5.0, TH_Y + 6.0, -95.0, 'wood')            # the hut at its back
for (x0, z0, x1, z1) in ((-9.0, -100.0, -8.6, zt), (8.6, -100.0, 9.0, zt), (-9.0, zt - 0.4, -2.5, zt), (2.5, zt - 0.4, 9.0, zt)):
    rot((x0 + x1) / 2, TH_Y + 1.8, (z0 + z1) / 2, x1 - x0, 3.6, z1 - z0, 0.0, 'rail', 'c')
# the play fort (south yards, in the middle): a platform on posts, a stair from the back; the trampolines throw you onto it
PF_Y = 8.0
box(-7.0, PF_Y - 1.0, 80.0, 7.0, PF_Y, 92.0, 'wood')
for (x, z) in ((-6.5, 80.5), (6.5, 80.5), (-6.5, 91.5), (6.5, 91.5)):
    round_(x, z, 0.5, 0, PF_Y - 1.0, 'wood', n=2)
zf = stair(-2.0, 2.0, 103.2, -1, int(PF_Y))
for (x0, z0, x1, z1) in ((-7.0, 80.0, 7.0, 80.4), (-7.0, 91.6, -2.0, 92.0), (2.0, 91.6, 7.0, 92.0)):
    rot((x0 + x1) / 2, PF_Y + 1.25, (z0 + z1) / 2, x1 - x0, 2.5, z1 - z0, 0.0, 'rail', 'c')
box(-3.0, PF_Y, 81.0, 3.0, PF_Y + 3.0, 83.0, 'wood')               # a little wall on the fort (cover)

# ================================================================ spawns
# teams: attackers round the west turning circle behind the island and the parked cars, facing east; defenders mirrored
for (x, z) in ((-140.0, -14.0), (-140.0, -5.0), (-140.0, 5.0), (-140.0, 14.0), (-130.0, -10.0), (-130.0, 10.0), (-148.0, 0.0), (-128.0, -2.0)):
    TEAM['att'].append((x, 0.3, z, 1.0, 0.0))
    TEAM['def'].append((-x, 0.3, z, -1.0, 0.0))
TEAM['mid'] = [(-22.0, 0.3, -100.0, 0.0, 1.0), (22.0, 0.3, -100.0, 0.0, 1.0), (-22.0, 0.3, 102.0, 0.0, -1.0), (22.0, 0.3, 102.0, 0.0, -1.0)]
for (x, y, z) in ((-120.0, 0, -20.0), (-70.0, 0, 0.0), (-26.0, 0, 26.0), (-70.0, 0, -64.0), (-46.0, 0, -100.0), (-60.0, 0, 70.0),
                  (-46.0, 0, 96.0), (-73.0, UP, -32.0), (-27.0, UP, 46.0), (-54.0, GROOF, 30.0)):
    SPAWNS.append((x, y + 0.3, z)); SPAWNS.append((-x, y + 0.3, z))
SPAWNS.append((0.0, TH_Y + 0.3, -88.0)); SPAWNS.append((0.0, PF_Y + 0.3, 86.0))

# ================================================================ for the plan (arena_plan.py)
TITLE = 'SUBURB: CUL-DE-SAC (Suburb v2)'
BOUNDS = (-219.0, 219.0, -155.0, 155.0)   # (the wall box: walls to 216 / 152)
LEVELS = [('STREET AND YARDS (y 0)', 0.4, 9.0, 0.0), ('UPSTAIRS, GARAGE ROOFS, TREE HOUSE, FORT (y 8 to 14)', 7.5, 20.0, 12.0)]
FLOORS = ('asphalt', 'lawn', 'floor', 'step')
COLOURS = {'asphalt': (120, 122, 128), 'lawn': (150, 170, 128), 'house': (150, 88, 98), 'roof': (110, 70, 80),
           'garage': (205, 180, 160), 'fence': (245, 240, 230), 'hedge': (80, 110, 70), 'wood': (176, 132, 96),
           'car': (160, 170, 180), 'tree': (120, 90, 60), 'stone': (214, 208, 196), 'floor': (200, 170, 130)}
PLAN_NOTE = ('a dumbbell: a cul-de-sac at each end (spawns behind the island and the garden hedges), the street with the hedged green '
             'in the middle; houses you can go through (doors, a stair, upstairs windows); garage roofs into the upstairs; '
             'north yards: pools, a tree house; south yards: trampolines, a play fort')

# ================================================================ self-checks (py tools/roblox/suburb2_layout.py)
def _seg_box(a, b, bx):
    x0, y0, z0, x1, y1, z1 = bx
    t0, t1 = 0.0, 1.0
    for k, (lo, hi) in enumerate(((x0, x1), (y0, y1), (z0, z1))):
        d = b[k] - a[k]
        if abs(d) < 1e-9:
            if a[k] < lo or a[k] > hi: return False
        else:
            u0, u1 = (lo - a[k]) / d, (hi - a[k]) / d
            if u0 > u1: u0, u1 = u1, u0
            t0, t1 = max(t0, u0), min(t1, u1)
            if t0 > t1: return False
    return True

def _rot_local(p, r):
    cx, cy, cz, sx, sy, sz, yaw = r[:7]
    t = math.radians(yaw)
    dx, dz = p[0] - cx, p[2] - cz
    # world = R * local, local x -> (cos, -sin), local z -> (sin, cos)
    lx = dx * math.cos(t) - dz * math.sin(t)
    lz = dx * math.sin(t) + dz * math.cos(t)
    return (lx, p[1] - cy, lz)

def _seg_rot(a, b, r):
    la, lb = _rot_local(a, r), _rot_local(b, r)
    return _seg_box(la, lb, (-r[3] / 2, -r[4] / 2, -r[5] / 2, r[3] / 2, r[4] / 2, r[5] / 2))

def blocked(a, b, shots=True):
    for s in SOLID:
        if _seg_box(a, b, s[:6]): return True
    for r in ROT:
        if shots and 'c' in r[8]: continue
        if _seg_rot(a, b, r): return True
    return False

def floor_under(p):
    """the highest top of any box under the point, within 1.5"""
    best = None
    for s in SOLID:
        if s[0] <= p[0] <= s[3] and s[2] <= p[2] <= s[5] and -1.0 <= p[1] - s[4] <= 1.5:
            best = s[4] if best is None else max(best, s[4])
    for r in ROT:
        lp = _rot_local(p, r)
        if abs(lp[0]) <= r[3] / 2 and abs(lp[2]) <= r[5] / 2 and -1.0 <= p[1] - (r[1] + r[4] / 2) <= 1.5:
            top = r[1] + r[4] / 2
            best = top if best is None else max(best, top)
    return best

def inside(p):
    for s in SOLID:
        if s[0] < p[0] < s[3] and s[1] < p[1] < s[4] and s[2] < p[2] < s[5]: return s
    return None

def pad_flight(p):
    x0, y0, z0, x1, y1, z1, vx, vy, vz = p
    pos = [(x0 + x1) / 2, y1, (z0 + z1) / 2]
    v = [vx, vy, vz]
    t, dt = 0.0, 1 / 120
    while t < 4:
        nxt = [pos[0] + v[0] * dt, pos[1] + v[1] * dt, pos[2] + v[2] * dt]
        v[1] -= G * dt
        t += dt
        if v[1] < 0:
            for s in SOLID:
                if s[0] <= nxt[0] <= s[3] and s[2] <= nxt[2] <= s[5] and nxt[1] <= s[4] <= pos[1] + 0.01:
                    return (nxt[0], s[4], nxt[2], t, s[6])
        # (head-on walls on the way up/along)
        for s in SOLID:
            if s[0] < nxt[0] < s[3] and s[2] < nxt[2] < s[5] and s[1] < nxt[1] + 2.5 < s[4] and not (s[0] < pos[0] < s[3] and s[2] < pos[2] < s[5]):
                return (nxt[0], nxt[1], nxt[2], t, 'HIT ' + s[6])
        pos = nxt
    return None

# ================================================================ the wall box (18 Nov 2026: tools/roblox/wallbox.py)
# no lid; the walls 30 studs further out; the back and end hedges (solid to the lid till now, 12 high in the kit) and
# the ring past them become a step up to 32 (the houses and trees past the hedges reach 31.6): open air over the
# gardens behind, a ledge nobody can stay on. the kit dresses from SOLID and ROT as before; the builders write
# HIT_SOLID/HIT_ROT
import wallbox
HIT_SOLID, HIT_ROT, WALLBOX = wallbox.rect(SOLID, ROT, X_EDGE, Z_EDGE, -6.0, 32.0, 12.0, drop=lambda b: b[6] == 'edge',
                                           cut=lambda b: b[6] == 'hedge' and b[4] >= LID - 0.01)

if __name__ == '__main__':
    print('solid %d, turned %d, pads %d, water %d, spawns %d, team %s' % (len(SOLID), len(ROT), len(PADS), len(WATER), len(SPAWNS), {k: len(v) for k, v in TEAM.items()}))
    # team spawn sight lines (shots: rails don't block)
    open_, n = [], 0
    for a in TEAM['att']:
        for b in TEAM['def']:
            for h in (2.5, 4.6):
                n += 1
                pa, pb = (a[0], a[1] + h, a[2]), (b[0], b[1] + h, b[2])
                if not blocked(pa, pb): open_.append((a[:3], b[:3], h))
    print('team spawn sight lines open: %d of %d %s' % (len(open_), n, open_[:4]))
    bad = []
    for p in SPAWNS + [t[:3] for v in TEAM.values() for t in v]:
        f = floor_under(p)
        stuck = inside((p[0], p[1] + 2.5, p[2]))
        if f is None or stuck: bad.append((p, f, stuck and stuck[6]))
    print('spawns off a floor or inside something: %d %s' % (len(bad), bad[:6]))
    for p in PADS: print('pad at (%.0f, %.0f) lands' % ((p[0] + p[3]) / 2, (p[2] + p[5]) / 2), pad_flight(p))
    for w, pl in zip(WATER, POOLS): print('water', w, 'pool', pl)
