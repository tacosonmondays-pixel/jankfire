# DESERT v2: CANYON (17 Nov 2026). The owner: "can you create an entirely new bazar desert, suburb, make the shape
# unique, give it like unique properties ... theyre all v2 versions". This is the desert: a winding canyon between two
# mesas, mirror-symmetric across x = 0 (attackers camp in the west end, defenders in the east end).
#   the canyon (y 0)  a zigzag channel: each camp opens into a short corridor, the canyon turns north, runs east under
#                      the north mesa, turns south down a long leg and opens into the middle basin (shared). every bend
#                      breaks the long lines; outcrops, a dry riverbed, broken wagons and crates are the cover
#   the mesas (y 26)   flat rock tops north and south, reached by stairs carved into the canyon walls (two from each
#                      camp, one in each north leg, one in each south leg, two from the basin); rock spires, ruined
#                      walls and boulders up there so the high ground isn't free
#   the rope bridge    across the basin at x = 0, from the north mesa's tongue to the south mesa, 26 up: high, open
#   the sandstorm      now and then a storm blows through (DesertStorm.server picks when; DesertStorm.client thickens
#                      the haze and blows sand round you): it closes the mesa-to-mesa lines for a while
# Everything that is not walkable is solid up to y 150; a lid closes the top. Plain Python: desert2_models.py dresses it,
# arena_plan.py draws it.
import math

LID = 150.0
MESA = 26.0          # the mesa tops
RUN = 1.4            # every stair: 1 up per 1.4 along
X_EDGE, Z_EDGE = 172.0, 122.0

MATS = {
    'sand': ('Sand', 'd9b98a', 'sand'),
    'rock': ('Sandstone', 'c39a6c', 'rock'),
    'edge': ('Sandstone', 'b08a60', 'rock'),
    'spire': ('Sandstone', 'b58e64', 'rock'),
    'cover': ('Sandstone', 'c8a273', 'rock'),
    'wood': ('Wood', '8d6a4a', 'wood'),
    'crate': ('Wood', 'a07c56', 'crate'),
    'canvas': ('Fabric', '7f9590', 'canvas'),
    'step': ('Sandstone', 'cfa778', 'rock'),
    'plank': ('Wood', '9a7552', 'wood'),
    'rail': ('Fabric', '8a7458', 'rope'),
}

SOLID, ROT, SPAWNS, NOTES = [], [], [], []
TEAM = {'att': [], 'def': [], 'mid': []}
CANYON = []          # the canyon's rectangles (x0, z0, x1, z1), both halves
STAIRS = []          # (x_bot, x_top, z0, z1, axis 'x'|'z') for the kit: every stair's footprint and which way it climbs
SPIRES, BOULDERS, RUINS, WAGONS, CRATES, TENTS = [], [], [], [], [], []

def box(x0, y0, z0, x1, y1, z1, m):
    SOLID.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), m))
def both(x0, y0, z0, x1, y1, z1, m):
    box(x0, y0, z0, x1, y1, z1, m); box(-x0, y0, z0, -x1, y1, z1, m)
def rot(cx, cy, cz, sx, sy, sz, yaw, m, flags=''):
    ROT.append((cx, cy, cz, sx, sy, sz, yaw, m, flags))

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

# ================================================================ the canyon (west half; mirrored)
WEST = [
    ('camp', (-160.0, -34.0, -122.0, 34.0)),      # the camp at the canyon's west end (team spawns, tents, an overhang)
    ('corridor', (-122.0, -18.0, -96.0, 18.0)),   # out of the camp, east
    ('north leg', (-110.0, -72.0, -74.0, -18.0)), # the canyon turns north
    ('north run', (-74.0, -72.0, -34.0, -42.0)),  # east, under the north mesa
    ('south leg', (-50.0, -42.0, -16.0, 44.0)),   # south, the long leg
]
BASIN = (-16.0, 8.0, 16.0, 44.0)                  # the middle basin, shared; the bridge crosses it
for name, (x0, z0, x1, z1) in WEST:
    CANYON.append((x0, z0, x1, z1)); CANYON.append((-x1, z0, -x0, z1))
CANYON.append(BASIN)
# the canyon floor: sand everywhere (under the mesas too)
box(-X_EDGE, -6.0, -Z_EDGE, X_EDGE, 0.0, Z_EDGE, 'sand')
# the mesas: everything else inside the edge, solid from the floor to their tops
mesa = [(-X_EDGE, -Z_EDGE, X_EDGE, Z_EDGE)]
for c in CANYON: mesa = subtract(mesa, c)
MESA_RECTS = mesa
for (x0, z0, x1, z1) in mesa: box(x0, 0.0, z0, x1, MESA, z1, 'rock')
# the outer cliffs: past these lines the rock rises far above the mesas (solid to the lid): the playable mesa tops are
# the bands along the canyon, not the whole plateau
CLIFF_N, CLIFF_S, CLIFF_X = -100.0, 96.0, 162.0
box(-X_EDGE, 0.0, -Z_EDGE, X_EDGE, LID, CLIFF_N, 'edge')
box(-X_EDGE, 0.0, CLIFF_S, X_EDGE, LID, Z_EDGE, 'edge')
both(-X_EDGE, 0.0, CLIFF_N, -CLIFF_X, LID, CLIFF_S, 'edge')
# the edge: invisible walls and a lid (the kit raises tall cliffs round the outside)
box(-X_EDGE - 10, -6.0, -Z_EDGE - 10, -X_EDGE, LID, Z_EDGE + 10, 'edge')
box(X_EDGE, -6.0, -Z_EDGE - 10, X_EDGE + 10, LID, Z_EDGE + 10, 'edge')
box(-X_EDGE, -6.0, -Z_EDGE - 10, X_EDGE, LID, -Z_EDGE, 'edge')
box(-X_EDGE, -6.0, Z_EDGE, X_EDGE, LID, Z_EDGE + 10, 'edge')
box(-X_EDGE - 10, LID, -Z_EDGE - 10, X_EDGE + 10, LID + 5, Z_EDGE + 10, 'edge')

# ================================================================ stairs carved into the canyon walls (26 steps each)
N = int(MESA)
def stair_x(xb, xt, z0, z1):
    """steps climbing along x from xb (floor) to xt (top, level with the mesa beside or beyond it)"""
    s = 1.0 if xt > xb else -1.0
    for k in range(1, N + 1):
        a, b = xb + s * (k - 1) * RUN, xb + s * k * RUN
        box(a, 0.0, z0, b, float(k), z1, 'step')
    STAIRS.append((xb, xt, z0, z1, 'x'))
def stair_z(zb, zt, x0, x1):
    s = 1.0 if zt > zb else -1.0
    for k in range(1, N + 1):
        a, b = zb + s * (k - 1) * RUN, zb + s * k * RUN
        box(x0, 0.0, a, x1, float(k), b, 'step')
    STAIRS.append((zb, zt, x0, x1, 'z'))
SPAN = N * RUN       # 36.4
for s in (1, -1):
    # the camp: up its north and south walls, climbing toward the corridor (you step off east onto the mesa)
    stair_x(s * -158.0, s * (-158.0 + SPAN), -34.0, -27.0)
    stair_x(s * -158.0, s * (-158.0 + SPAN), 27.0, 34.0)
    # the north leg: up its west wall, climbing north (you step off west onto the strip by the camp)
    stair_z(-22.0, -22.0 - SPAN, s * -110.0, s * -103.0)
    # the south leg: up its west wall, climbing north (you step off west onto the peninsula)
    stair_z(42.0, 42.0 - SPAN, s * -50.0, s * -43.0)
    # the basin: along its south wall, climbing outward (you step off south onto the south mesa)
    stair_x(s * -2.0, s * (-2.0 - SPAN), 37.0, 44.0)
NOTES += [(-141, 0, 0, 'ATT CAMP'), (141, 0, 0, 'DEF CAMP'), (-92, -45, 0, 'NORTH LEG'), (92, -45, 0, 'NORTH LEG'),
          (-33, 0, 0, 'SOUTH LEG'), (33, 0, 0, 'SOUTH LEG'), (0, 30, 0, 'BASIN')]

# ================================================================ the camps: an overhang over the back, tents, crates
for s in (1, -1):
    box(s * -160.0, 16.0, -14.0, s * -146.0, MESA, 14.0, 'rock')          # the rock shelf over the camp's back
    TENTS.append((s * -150.0, 21.0, s)); TENTS.append((s * -150.0, -21.0, s))
    box(s * -154.0, 0.0, 17.0, s * -146.0, 7.0, 25.0, 'canvas')           # tents (cover)
    box(s * -154.0, 0.0, -25.0, s * -146.0, 7.0, -17.0, 'canvas')
    for (x, z) in ((-131.0, -9.0), (-131.0, 9.0)):                        # crates by the camp's mouth
        box(s * x - 2.5, 0.0, z - 2.5, s * x + 2.5, 5.0, z + 2.5, 'crate'); CRATES.append((s * x, z, 5.0))

# ================================================================ cover in the canyon (west half; mirrored)
def outcrop(x, z, w, d, h, m='cover'):
    box(x - w / 2, 0.0, z - d / 2, x + w / 2, h, z + d / 2, m); BOULDERS.append((x, 0.0, z, w, h, d))
for s in (1, -1):
    X = lambda v: s * v
    # the corridor: a fallen slab half across it
    outcrop(X(-109.0), 6.0, 7.0, 10.0, 6.0)
    # the north leg: an outcrop at the bend, crates further up
    outcrop(X(-86.0), -30.0, 10.0, 8.0, 8.0)
    box(X(-96.0) - 2.5, 0.0, -57.5, X(-96.0) + 2.5, 5.0, -52.5, 'crate'); CRATES.append((X(-96.0), -55.0, 5.0))
    # the north run: a broken wagon (low cover) and a rock
    box(X(-60.0) - 5.0, 0.0, -60.0, X(-60.0) + 5.0, 4.5, -54.0, 'wood'); WAGONS.append((X(-60.0), -57.0, s))
    outcrop(X(-44.0), -64.0, 8.0, 7.0, 7.0)
    # the south leg: two outcrops staggered (no straight line down the leg), a wagon
    outcrop(X(-27.0), -22.0, 9.0, 8.0, 8.0)
    outcrop(X(-36.0), 14.0, 8.0, 9.0, 7.0)
    box(X(-25.0) - 3.0, 0.0, 22.0, X(-25.0) + 3.0, 4.5, 32.0, 'wood'); WAGONS.append((X(-25.0), 27.0, s))
# the basin: one big boulder under the bridge, off the middle line
outcrop(0.0, 20.0, 12.0, 8.0, 9.0)
NOTES += [(0, -20, 1, 'NORTH TONGUE'), (0, 60, 1, 'SOUTH MESA'), (-110, -95, 1, 'NORTH MESA'), (110, -95, 1, 'NORTH MESA'),
          (0, 26, 1, 'ROPE BRIDGE')]

# ================================================================ the mesa tops: spires (solid to the lid), ruins, boulders
def spire(x, z, r, h):
    box(x - r, MESA, z - r, x + r, LID, z + r, 'spire'); SPIRES.append((x, z, r, h))
def ruin(x0, z0, x1, z1, h=4.0):
    box(x0, MESA, z0, x1, MESA + h, z1, 'cover'); RUINS.append((x0, z0, x1, z1, h))
def boulder(x, z, w, d, h):
    box(x - w / 2, MESA, z - d / 2, x + w / 2, MESA + h, z + d / 2, 'cover'); BOULDERS.append((x, MESA, z, w, h, d))
for s in (1, -1):
    X = lambda v: s * v
    # north mesa
    spire(X(-128.0), -60.0, 5.0, 48.0)
    ruin(X(-90.0), -96.0, X(-70.0), -93.0); ruin(X(-73.0), -93.0, X(-70.0), -84.0)
    boulder(X(-54.0), -88.0, 8.0, 6.0, 5.0)
    spire(X(-20.0), -86.0, 6.0, 56.0)
    boulder(X(-14.0), -40.0, 7.0, 7.0, 5.0)                      # on the tongue
    ruin(X(-28.0), -10.0, X(-24.0), 2.0)                          # the tongue's edge over the basin
    # south mesa and the peninsula
    spire(X(-72.0), 10.0, 5.5, 52.0)                              # the peninsula's spire
    ruin(X(-90.0), 26.0, X(-86.0), 40.0)
    boulder(X(-120.0), 62.0, 9.0, 7.0, 5.0)
    ruin(X(-100.0), 84.0, X(-78.0), 87.0)
    spire(X(-40.0), 80.0, 6.0, 50.0)
    boulder(X(-22.0), 58.0, 7.0, 6.0, 5.0)
    # more on the north band and the south mesa; low rock lips along the canyon's edges (peek, duck)
    boulder(X(-104.0), -84.0, 7.0, 6.0, 5.0)
    ruin(X(-46.0), -78.0, X(-40.0), -75.0, 3.0)                      # the lip over the north run
    ruin(X(-66.0), -78.0, X(-58.0), -75.0, 3.0)
    ruin(X(-12.0), 47.0, X(-4.0), 50.0, 3.0)                         # the lip over the basin (south)
    ruin(X(-30.0), 47.0, X(-22.0), 50.0, 3.0)
    boulder(X(-60.0), 72.0, 8.0, 6.0, 5.0)
    ruin(X(-150.0), 44.0, X(-146.0), 58.0)
    boulder(X(-110.0), 40.0, 6.0, 6.0, 4.0)
    # the strip by the camp (north) and the camp's south shoulder
    boulder(X(-116.0), -42.0, 6.0, 7.0, 5.0)
    boulder(X(-136.0), 50.0, 8.0, 6.0, 5.0)

# ================================================================ the rope bridge: a sagging deck of steps, rope rails
BRIDGE_Z0, BRIDGE_Z1, BRIDGE_W = 8.0, 44.0, 3.2       # (the deck from mesa edge to mesa edge, half width)
SAG = 1.5
def bridge_y(z):
    t = (z - BRIDGE_Z0) / (BRIDGE_Z1 - BRIDGE_Z0)
    return MESA - SAG * math.sin(math.pi * t)
BRIDGE_DECK = []
nseg = 12
for k in range(nseg):
    z0 = BRIDGE_Z0 + (BRIDGE_Z1 - BRIDGE_Z0) * k / nseg
    z1 = BRIDGE_Z0 + (BRIDGE_Z1 - BRIDGE_Z0) * (k + 1) / nseg
    top = round(bridge_y((z0 + z1) / 2) * 4) / 4
    box(-BRIDGE_W, top - 0.6, z0, BRIDGE_W, top, z1, 'plank'); BRIDGE_DECK.append((z0, z1, top))
    for sx in (-1, 1):   # the rope rails: they stop you, not bullets
        rot(sx * (BRIDGE_W + 0.25), top + 1.8, (z0 + z1) / 2, 0.5, 3.6, z1 - z0, 0.0, 'rail', 'c')

# ================================================================ spawns
for (x, z) in ((-150.0, -8.0), (-150.0, 8.0), (-140.0, -14.0), (-140.0, 0.0), (-140.0, 14.0), (-131.0, -20.0), (-131.0, 20.0), (-128.0, 0.0)):
    TEAM['att'].append((x, 0.3, z, 1.0, 0.0)); TEAM['def'].append((-x, 0.3, z, -1.0, 0.0))
TEAM['mid'] = [(-8.0, MESA + 0.3, -56.0, 0.0, 1.0), (8.0, MESA + 0.3, -56.0, 0.0, 1.0), (-8.0, MESA + 0.3, 76.0, 0.0, -1.0), (8.0, MESA + 0.3, 76.0, 0.0, -1.0)]
for (x, y, z) in ((-140, 0, -24), (-92, 0, -60), (-62, 0, -50), (-33, 0, -30), (-33, 0, 30), (-6, 0, 30),
                  (-100, MESA, -90), (-56, MESA, -92), (-110, MESA, 70), (-64, MESA, 30)):
    SPAWNS.append((x, y + 0.3, z)); SPAWNS.append((-x, y + 0.3, z))

# ================================================================ for the plan
TITLE = 'DESERT: CANYON (v2)'
BOUNDS = (-180, 180, -130, 130)
LEVELS = [('CANYON FLOOR (y 0)', 0.4, 9.0, 0.0), ('MESA TOPS (y 26) + the rope bridge', MESA + 0.4, MESA + 9.0, MESA)]
FLOORS = ('sand', 'rock', 'step', 'plank')
COLOURS = {'sand': (226, 200, 160), 'rock': (176, 136, 98), 'spire': (120, 84, 60), 'cover': (210, 150, 110), 'edge': (90, 66, 50),
           'crate': (190, 140, 90), 'wood': (150, 110, 80), 'canvas': (110, 150, 145), 'plank': (170, 120, 80), 'rail': (196, 138, 122),
           'step': (205, 180, 150)}
PLAN_NOTE = ('a winding canyon between two mesas: each camp -> corridor -> north leg -> north run -> south leg -> the basin; '
             'stairs carved into the walls; a rope bridge over the basin; sandstorms close the mesa lines now and then')
