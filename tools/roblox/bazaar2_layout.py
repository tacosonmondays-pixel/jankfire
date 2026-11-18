# BAZAAR v2, "BAZAAR: ROOFTOPS" (17 Nov 2026): a new desert market town, not the web port. The owner: "can you create an
# entirely new bazar desert, suburb, make the shape unique, give it like usnique properties, maybe bazar has an upper
# area or something" / "theyre all v2 versions". Plain Python: the hit boxes, pads, water and spawns, in studs local to
# the arena's origin (street level y 0). bazaar2_models.py dresses it; arena_plan.py draws it.
#
# The shape: an oval walled town (a 330 x 250 ellipse) round a square oasis pool, mirror-symmetric across x = 0
# (attackers in the west gate courtyard, defenders in the east).
#   street (y 0)   courtyard | a covered souk (north) under the roofs, the main street, an open spice market (south) |
#                  the plaza round the pool (swim it; a domed well on its island blocks the street-to-street line) | a
#                  domed market hall you walk through (north) and the caravanserai with its wind tower (south)
#   roofs (y 18)   the upper bazaar: the flat roofs of every block, the souk's roof and the hall's, one network joined by
#                  plank bridges, with parapets and roof clutter for cover. Up by outside stairs and canvas springboards
#                  (pads) that throw you onto the roofs
import math

LID = 150.0
H = 18.0            # the roofs
STEP, RUN = 1.0, 1.4
GRAV = 78.0         # Workspace.Gravity (26 m/s2 x 3: Move.client)

MATS = {
    'paving': ('Sandstone', 'd9c3a0', 'sand'),
    'roof': ('SmoothPlastic', 'e8dcc6', 'plaster'),
    'wall': ('SmoothPlastic', 'e2d4bb', 'plaster'),
    'block': ('SmoothPlastic', 'e2d4bb', 'plaster'),
    'edge': ('Sandstone', 'c8b08b', 'stone'),
    'ledge': ('SmoothPlastic', 'c8c4bd', 'ledge'),   # the wall box's step (wallbox.py)
    'bound': ('SmoothPlastic', 'c8c4bd', 'bound'),   # its walls
    'cover': ('Wood', '8a6a4a', 'wood'),
    'pot': ('Slate', 'b9764f', 'clay'),
    'stone': ('Sandstone', 'b8a688', 'stone'),
    'step': ('Sandstone', 'c9b48f', 'stone'),
    'wood': ('Wood', '8a6a4a', 'wood'),
    'rail': ('Wood', '6e5238', 'wood'),
}
SOLID, ROT, PADS, WATER, SPAWNS, NOTES = [], [], [], [], [], []
TEAM = {'att': [], 'def': [], 'mid': []}
ROUNDS = []        # (cx, cz, r, y0, y1, mat): round things (pots, palms, the hall's drum)
STAIRS = []        # (x0, z0, x1, z1, axis, up_dir, y0, y1): every stair, for the kit
BRIDGES = []       # (x0, z0, x1, z1): plank bridges at roof level
PARAPETS = []      # (x0, z0, x1, z1): low walls on roof edges

def box(x0, y0, z0, x1, y1, z1, m):
    SOLID.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), m))
def both(x0, y0, z0, x1, y1, z1, m):
    box(x0, y0, z0, x1, y1, z1, m); box(-x0, y0, z0, -x1, y1, z1, m)
def rot(cx, cy, cz, sx, sy, sz, yaw, m, flags=''):
    ROT.append((cx, cy, cz, sx, sy, sz, yaw, m, flags))
def round_(cx, cz, r, y0, y1, m, n=2, flags=''):
    ROUNDS.append((cx, cz, r, y0, y1, m))
    for k in range(n): rot(cx, (y0 + y1) / 2, cz, 2 * r, y1 - y0, 2 * r, 90.0 * k / n, m, flags)
def subtract(rects, h):
    out = []
    hx0, hz0, hx1, hz1 = h
    for (x0, z0, x1, z1) in rects:
        if hx1 <= x0 or hx0 >= x1 or hz1 <= z0 or hz0 >= z1: out.append((x0, z0, x1, z1)); continue
        if z0 < hz0: out.append((x0, z0, x1, hz0))
        if hz1 < z1: out.append((x0, hz1, x1, z1))
        mz0, mz1 = max(z0, hz0), min(z1, hz1)
        if x0 < hx0: out.append((x0, mz0, hx0, mz1))
        if hx1 < x1: out.append((hx1, mz0, x1, mz1))
    return out

# ================================================================ the ground, the pool, the wall
A_, B_ = 165.0, 125.0                     # the town wall's ellipse (inner face)
POOL = 20.0                               # the pool: x and z -20..20, water to 0.6 under the rim
ISLAND = 8.0                              # the domed well on its island: x and z -8..8
slab = subtract([(-A_ - 8, -B_ - 8, A_ + 8, B_ + 8)], (-POOL, -POOL, POOL, POOL))
for (x0, z0, x1, z1) in slab: box(x0, -6.0, z0, x1, 0.0, z1, 'paving')
box(-POOL, -12.0, -POOL, POOL, -8.0, POOL, 'stone')                    # the pool's floor
WATER.append((-POOL, -8.0, -POOL, POOL, -0.6, POOL))
box(-ISLAND, -8.0, -ISLAND, ISLAND, 12.0, ISLAND, 'block')             # the well house on its island (solid)
# the wall: 48 turned boxes along the ellipse, solid to the lid, and a lid
N = 48
for k in range(N):
    t0, t1 = 2 * math.pi * k / N, 2 * math.pi * (k + 1) / N
    p0 = (A_ * math.cos(t0), B_ * math.sin(t0)); p1 = (A_ * math.cos(t1), B_ * math.sin(t1))
    mx, mz = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    dx, dz = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dz)
    nx, nz = dz / ln, -dx / ln                                           # outward
    if nx * mx + nz * mz < 0: nx, nz = -nx, -nz
    th = 10.0
    rot(mx + nx * th / 2, (LID - 6) / 2, mz + nz * th / 2, ln + 4.0, LID + 6, th, -math.degrees(math.atan2(dz, dx)), 'edge')
box(-A_ - 20, LID, -B_ - 20, A_ + 20, LID + 5, B_ + 20, 'edge')

def inside(x, z, m=0.0): return (x / (A_ - m)) ** 2 + (z / (B_ - m)) ** 2 < 1.0

# ================================================================ the blocks (west half; mirrored), roofs at 18
X_YARD = -128.0      # the courtyard's east edge / the blocks' west edge
X_IN = -60.0         # the inner blocks' east edge (the plaza begins)
def block(x0, z0, x1, z1, h=H, solid_top=None):
    """a house block: solid to its roof; the roof is walkable"""
    both(x0, 0.0, z0, x1, h, z1, 'block')
# north-inner (two houses, an alley x -100..-94), south-inner (two houses, an alley x -104..-98: offset)
block(-128.0, -38.0, -100.0, -8.0); block(-94.0, -38.0, X_IN, -8.0)
block(-128.0, 8.0, -104.0, 38.0); block(-98.0, 8.0, X_IN, 38.0)
# the souk: a covered street z -58..-38 from the courtyard's north yard to the junction by the hall; its roof (10..18)
both(-128.0, 10.0, -58.0, -40.0, H, -38.0, 'roof')
# north-outer and south-outer blocks, against the wall (whatever is left between them and the wall is solid)
block(-112.0, -86.0, -44.0, -58.0)
block(-112.0, 62.0, -44.0, 88.0)
both(-128.0, 0.0, -B_ - 10, -112.0, LID, -58.0, 'edge')                # dead space behind (inside the wall)
both(-112.0, 0.0, -B_ - 10, -44.0, LID, -86.0, 'edge')
both(-128.0, 0.0, 62.0, -112.0, LID, B_ + 10, 'edge')
both(-112.0, 0.0, 88.0, -44.0, LID, B_ + 10, 'edge')
both(-A_ - 10, 0.0, -B_ - 10, -128.0, LID, -60.0, 'edge')              # round the courtyard's yards
both(-A_ - 10, 0.0, 60.0, -128.0, LID, B_ + 10, 'edge')
# the courtyard (x -165..-128, z -26..26, the spawns) and its two yards (z -60..-26 to the souk, 26..60 to the market)
NOTES.extend([(-146, 0, 0, 'ATT COURTYARD'), (146, 0, 0, 'DEF COURTYARD'), (-84, -48, 0, 'SOUK (covered)'), (84, -48, 0, 'SOUK (covered)'),
              (-84, 50, 0, 'SPICE MARKET'), (84, 50, 0, 'SPICE MARKET'), (-92, 0, 0, 'MAIN STREET'), (0, -30, 0, 'POOL + WELL'),
              (0, -62, 0, 'MARKET HALL'), (0, 62, 0, 'CARAVANSERAI')])

# ================================================================ the centre: the market hall (north), the caravanserai (south)
# the hall: walls 4 thick round x -36..36, z -80..-40; doors west/east (z -56..-44, 12 high) onto the souks' junctions and
# south (x -6..6) onto the plaza; a ceiling at 14, its roof at 18 (walkable), a raised fountain inside that breaks the
# souk-hall-souk line; a drum under the dome on the roof (cover up there)
HX, HZ0, HZ1 = 36.0, -80.0, -40.0
both(-HX, 0.0, HZ0, -HX + 4, 14.0, -56.0, 'wall'); both(-HX, 0.0, -44.0, -HX + 4, 14.0, HZ1, 'wall')
both(-HX, 12.0, -56.0, -HX + 4, 14.0, -44.0, 'wall')
box(-HX, 0.0, HZ0, HX, 14.0, HZ0 + 4, 'wall')                          # north wall
both(-HX, 0.0, HZ1 - 4, -6.0, 14.0, HZ1, 'wall')                         # south wall, the door x -6..6
box(-6.0, 12.0, HZ1 - 4, 6.0, 14.0, HZ1, 'wall')
box(-HX, 14.0, HZ0, HX, H, HZ1, 'roof')                                  # the roof slab
box(-7.0, 0.0, -66.0, 7.0, 3.5, -46.0, 'stone')                          # the fountain's basin (cover), its spout above
box(-2.5, 3.5, -58.0, 2.5, 9.0, -54.0, 'stone')
round_(0.0, -60.0, 11.0, H, H + 9.0, 'roof', n=4)                        # the dome's drum on the roof
for (x, z) in ((-20.0, -60.0), (20.0, -60.0), (-20.0, -50.0), (20.0, -50.0)):
    round_(x, z, 1.4, 0.0, 14.0, 'stone', n=2)                           # columns inside
# the caravanserai: solid, its roof walkable; the wind tower on it
box(-HX, 0.0, 44.0, HX, H, 80.0, 'block')
box(-5.0, H, 57.0, 5.0, 46.0, 67.0, 'block')                              # the wind tower (to 46)
box(-HX, 0.0, 80.0, HX, LID, B_ + 10, 'edge'); box(-HX, 0.0, -B_ - 10, HX, LID, HZ0, 'edge')
# the plaza's west edge: the inner blocks end at x -60; corners x -60..-36 open; the hall/caravanserai at |x| <= 36

# ================================================================ roofs: parapets on street edges (gaps where you step
# off a stair or land from a springboard), clutter, bridges
def parapet(x0, z0, x1, z1):
    PARAPETS.append((x0, z0, x1, z1)); PARAPETS.append((-x1, z0, -x0, z1))
    both(x0, H, z0, x1, H + 3.0, z1, 'wall')
# north-inner block A1/A2 south edge (onto the main street), with a gap where the springboard throws you
parapet(-128.0, -9.0, -118.0, -8.0); parapet(-102.0, -9.0, -100.0, -8.0); parapet(-94.0, -9.0, -87.0, -8.0); parapet(-80.0, -9.0, -60.0, -8.0)
parapet(-128.0, 8.0, -118.0, 9.0); parapet(-106.0, 8.0, -104.0, 9.0); parapet(-98.0, 8.0, -87.0, 9.0); parapet(-80.0, 8.0, -60.0, 9.0)
# the inner blocks' plaza edge
parapet(-61.0, -24.0, -60.0, -9.0); parapet(-61.0, 9.0, -60.0, 24.0)
# the outer blocks' street edges
parapet(-112.0, 61.0, -96.0, 62.0); parapet(-74.0, 61.0, -44.0, 62.0)
# the hall's and caravanserai's plaza edges (the gaps over the springboards' landings)
box(-HX, H, HZ1 - 1, -18.0, H + 3, HZ1, 'wall'); box(18.0, H, HZ1 - 1, HX, H + 3, HZ1, 'wall')
box(-HX, H, 44.0, -18.0, H + 3, 45.0, 'wall'); box(18.0, H, 44.0, HX, H + 3, 45.0, 'wall')
for p in ((-HX, HZ1 - 1, -18.0, HZ1), (18.0, HZ1 - 1, HX, HZ1), (-HX, 44.0, -18.0, 45.0), (18.0, 44.0, HX, 45.0)): PARAPETS.append(p)
# roof clutter: stair-houses, water tanks (round), a laundry-hung screen, each a block for cover
both(-120.0, H, -30.0, -112.0, H + 7.0, -22.0, 'block')                  # stair-house on A1
both(-84.0, H, -30.0, -76.0, H + 7.0, -22.0, 'block')                    # stair-house on A2
both(-118.0, H, 18.0, -110.0, H + 7.0, 26.0, 'block')                    # on C1
both(-80.0, H, 24.0, -72.0, H + 7.0, 32.0, 'block')                      # on C2
for (x, z) in ((-100.0, -74.0), (-58.0, -70.0), (-66.0, 74.0), (-96.0, 76.0), (-70.0, -48.0)):
    round_(x, z, 3.2, H, H + 6.0, 'pot', n=4); round_(-x, z, 3.2, H, H + 6.0, 'pot', n=4)   # water tanks (also on the souk's roof)
both(-90.0, H, -64.0, -80.0, H + 5.0, -62.0, 'wood')                     # a screen of hung cloth on B
both(-90.0, H, 66.0, -80.0, H + 5.0, 68.0, 'wood')
# bridges (planks at roof level, rails that take no shots)
def bridge(x0, z0, x1, z1, along):
    for s in (1, -1):
        xa, xb = (x0, x1) if s > 0 else (-x1, -x0)
        BRIDGES.append((xa, z0, xb, z1))
        box(xa, H - 0.8, z0, xb, H, z1, 'wood')
        if along == 'z':
            for xx in (xa, xb - 0.4):
                rot(xx + 0.2, H + 1.8, (z0 + z1) / 2, 0.4, 3.6, z1 - z0, 0.0, 'rail', 'c')
        else:
            for zz in (z0, z1 - 0.4):
                rot((xa + xb) / 2, H + 1.8, zz + 0.2, xb - xa, 3.6, 0.4, 0.0, 'rail', 'c')
bridge(-86.0, -8.0, -81.0, 8.0, 'z')              # over the main street, north roofs to south roofs
bridge(-110.0, 38.0, -105.0, 62.0, 'z')           # over the spice market, the south-inner roof to the south-outer one
bridge(-40.0, -52.0, -36.0, -47.0, 'x')           # the souk's roof to the hall's roof, over the junction
block(-44.0, -86.0, -36.0, -58.0)                 # a narrow house joins the north-outer block's roof to the hall's
block(-44.0, 62.0, -36.0, 80.0)                   # and the south-outer block's to the caravanserai's
both(-44.0, 0.0, -B_ - 10, -36.0, LID, -86.0, 'edge')
both(-44.0, 0.0, 80.0, -36.0, LID, B_ + 10, 'edge')

# ================================================================ stairs up (street to roofs)
def stair(x0, z0, x1, z1, axis, up, top=H, base=0.0, mat='step'):
    """a straight stair in the rectangle; axis 'x' or 'z' it climbs along; up = +1/-1 the direction it rises"""
    n = int(round((top - base) / STEP))
    for s in (1, -1):
        X0, X1 = (x0, x1) if s > 0 else (-x1, -x0)
        u = up if (axis == 'z' or s > 0) else -up
        STAIRS.append((X0, z0, X1, z1, axis, u, base, top))
        for k in range(1, n + 1):
            if axis == 'z':
                za = (z0 if u > 0 else z1) + u * (k - 1) * RUN; zb = za + u * RUN
                box(X0, base, za, X1, base + k * STEP, zb, mat)
            else:
                xa = (X0 if u > 0 else X1) + u * (k - 1) * RUN; xb = xa + u * RUN
                box(xa, base, z0, xb, base + k * STEP, z1, mat)
# the courtyard: up the west faces of the inner blocks (north one climbs north onto A1, south one south onto C1)
stair(-134.0, -28.2, -128.0, -3.0, 'z', -1)
stair(-134.0, 3.0, -128.0, 28.2, 'z', 1)
# the spice market: against the south-outer block's north face, climbing west onto it
stair(-87.2, 56.0, -62.0, 62.0, 'x', -1)
# the plaza corners: against the inner blocks' plaza faces, up to their roofs
stair(-60.0, -38.0, -54.0, -12.8, 'z', -1)
stair(-60.0, 12.8, -54.0, 38.0, 'z', 1)
NOTES.extend([(-131, -30, 1, 'stairs'), (-131, 30, 1, 'stairs')])

# ================================================================ springboards (canvas pads that throw you onto roofs)
def pad(x0, z0, x1, z1, vx, vy, vz):
    PADS.append((x0, 0.0, z0, x1, 0.9, z1, vx, vy, vz)); PADS.append((-x1, 0.0, z0, -x0, 0.9, z1, -vx, vy, vz))
pad(-117.0, -6.5, -111.0, -1.5, 0.0, 66.0, -12.0)        # the main street: onto the north-inner roof (the parapet's gap)
pad(-110.0, 1.5, -104.0, 6.5, 0.0, 66.0, 12.0)           # onto the south-inner roof
pad(-15.0, -31.0, -9.0, -25.0, 0.0, 66.0, -12.0)        # the plaza: onto the hall's roof
pad(-15.0, 25.0, -9.0, 31.0, 0.0, 66.0, 12.0)            # onto the caravanserai's roof

# ================================================================ cover on the street
def stall(x0, z0, x1, z1):
    both(x0, 0.0, z0, x1, 3.6, z1, 'cover')
# the main street: market stalls along both sides (offset north/south so no line runs down it clean)
stall(-124.0, -8.0, -118.0, -5.0); stall(-96.0, -8.0, -88.0, -5.0); stall(-76.0, 5.0, -68.0, 8.0); stall(-100.0, 5.0, -92.0, 8.0)
# the souk: stalls inside, alternating sides
stall(-120.0, -58.0, -112.0, -54.0); stall(-104.0, -42.0, -96.0, -38.0); stall(-80.0, -58.0, -72.0, -54.0); stall(-64.0, -42.0, -56.0, -38.0)
# the spice market: open stalls, crates, sacks
stall(-122.0, 44.0, -114.0, 48.0); stall(-108.0, 52.0, -100.0, 56.0); stall(-76.0, 40.0, -68.0, 44.0); stall(-56.0, 48.0, -48.0, 52.0)
# the courtyard: wagons and a well
both(-156.0, 0.0, -18.0, -148.0, 4.5, -8.0, 'wood'); both(-156.0, 0.0, 8.0, -148.0, 4.5, 18.0, 'wood')
round_(-140.0, 0.0, 3.4, 0.0, 3.6, 'stone', n=4); round_(140.0, 0.0, 3.4, 0.0, 3.6, 'stone', n=4)
# the plaza: big clay pots and palms round the pool, stalls at the corners
for (x, z) in ((-30.0, -12.0), (-30.0, 12.0), (-44.0, -28.0), (-44.0, 30.0)):
    round_(x, z, 2.6, 0.0, 4.2, 'pot', n=4); round_(-x, z, 2.6, 0.0, 4.2, 'pot', n=4)
PALMS = [(-24.0, -24.0), (-24.0, 24.0), (-50.0, -2.0), (24.0, -24.0), (24.0, 24.0), (50.0, -2.0)]
for (x, z) in PALMS: round_(x, z, 1.2, 0.0, 26.0, 'wood', n=2)
stall(-56.0, -24.0, -48.0, -20.0); stall(-56.0, 20.0, -48.0, 24.0)

# ================================================================ spawns
for (x, z) in ((-158, -20), (-158, -6), (-158, 6), (-158, 20), (-146, -14), (-146, 14), (-138, -22), (-138, 22)):
    TEAM['att'].append((x, 0.3, z, 1.0, 0.0)); TEAM['def'].append((-x, 0.3, z, -1.0, 0.0))
TEAM['mid'] = [(-24, 0.3, -70, 0.0, 1.0), (24, 0.3, -70, 0.0, 1.0), (-48, 0.3, 36, 0.0, -1.0), (48, 0.3, 36, 0.0, -1.0)]
for (x, y, z) in ((-150, 0, -40), (-84, 0, -48), (-124, 0, 0), (-84, 0, 50), (-140, 0, 44), (-110, H, -20), (-70, H, 20),
                  (-80, H, -72), (-90, H, 74), (-46, 0, 0), (-20, H, -66), (-22, H, 60)):
    SPAWNS.append((x, y + 0.3, z)); SPAWNS.append((-x, y + 0.3, z))

# ================================================================ for the plan and the checks
BOUNDS = (-210, 210, -170, 170)   # (the wall box: the oval wall to 205 x 165)
LEVELS = [('STREET (y 0)', 0.4, 9.0, 0.0), ('ROOFS (y 18): the upper bazaar', H + 0.4, H + 9.0, H)]
TITLE = 'BAZAAR: ROOFTOPS'
PLAN_NOTE = ('Two full levels: the street (covered souk north, open spice market south, a domed hall you walk through, the pool you '
             'swim) and the roofs (one network: bridges over the streets, stairs and canvas springboards up).')
COLOURS = {'roof': (232, 214, 186), 'pot': (190, 120, 84), 'stone': (190, 170, 140), 'wood': (150, 110, 76)}
FLOORS = ('paving', 'roof', 'block', 'step', 'wood')

def segment_blocked(a, b):
    """is the straight line a -> b blocked by any solid box (axis or turned)?"""
    import math as m
    for (x0, y0, z0, x1, y1, z1, mt) in SOLID:
        if seg_box(a, b, (x0, y0, z0), (x1, y1, z1)): return True
    for (cx, cy, cz, sx, sy, sz, yaw, mt, fl) in ROT:
        t = m.radians(yaw)
        def loc(p):
            dx, dy, dz = p[0] - cx, p[1] - cy, p[2] - cz
            return (dx * m.cos(t) - dz * m.sin(t), dy, dx * m.sin(t) + dz * m.cos(t))
        if seg_box(loc(a), loc(b), (-sx / 2, -sy / 2, -sz / 2), (sx / 2, sy / 2, sz / 2)): return True
    return False
def seg_box(a, b, lo, hi):
    t0, t1 = 0.0, 1.0
    for k in range(3):
        d = b[k] - a[k]
        if abs(d) < 1e-9:
            if a[k] < lo[k] or a[k] > hi[k]: return False
        else:
            u0, u1 = (lo[k] - a[k]) / d, (hi[k] - a[k]) / d
            if u0 > u1: u0, u1 = u1, u0
            t0, t1 = max(t0, u0), min(t1, u1)
            if t0 > t1: return False
    return True
def pad_flight(p, g=GRAV):
    """where a pad throws you (feet), stepping like WebArena.check"""
    pos = [(p[0] + p[3]) / 2, p[4] + 3.0, (p[2] + p[5]) / 2]
    v = [p[6], p[7], p[8]]
    t = 0.0
    while t < 4.0:
        nxt = [pos[0] + v[0] / 60, pos[1] + v[1] / 60, pos[2] + v[2] / 60]
        v[1] -= g / 60; t += 1 / 60
        if v[1] < 0 and segment_blocked((pos[0], pos[1] - 2.6, pos[2]), (nxt[0], nxt[1] - 2.6, nxt[2])):
            return (nxt[0], nxt[1] - 2.6, nxt[2], t)
        pos = nxt
    return (pos[0], pos[1] - 2.6, pos[2], None)

# ================================================================ the wall box (18 Nov 2026: tools/roblox/wallbox.py)
# no lid; the oval wall 30 studs further out (the ellipse 195 x 155); between, a step up to the town wall's top (the
# kit's crenellations reach 33.2): the dunes outside the wall stay out of bounds, the air over them is open. the dead
# space behind the outer houses stays solid to the old lid (under the sky line nobody gets up there). the kit
# dresses from SOLID and ROT as before; the builders write HIT_SOLID/HIT_ROT
import wallbox
HIT_SOLID, HIT_ROT, WALLBOX = wallbox.oval(SOLID, ROT, A_, B_, -6.0, 34.0, 33.0, drop=lambda b: b[6] == 'edge' and b[1] >= LID,
                                           drop_rot=lambda r: r[7] == 'edge', n=N)

if __name__ == '__main__':
    print('solid', len(SOLID), 'rot', len(ROT), 'pads', len(PADS), 'water', len(WATER), 'spawns', len(SPAWNS))
    op = 0; n = 0
    for a in TEAM['att']:
        for b in TEAM['def']:
            for h in (2.5, 4.6):
                n += 1
                if not segment_blocked((a[0], a[1] + h, a[2]), (b[0], b[1] + h, b[2])): op += 1; print('open', a[:3], b[:3], h)
    print('team sight lines open', op, 'of', n)
    for p in PADS: print('pad', p[:6], '->', tuple(round(v, 1) if v is not None else None for v in pad_flight(p)))
    for s in SPAWNS + [t[:3] for t in TEAM['att'] + TEAM['def'] + TEAM['mid']]:
        if not segment_blocked((s[0], s[1] + 2, s[2]), (s[0], s[1] - 2, s[2])): print('spawn NOT on a floor', s)
        if segment_blocked((s[0], s[1] + 0.6, s[2]), (s[0], s[1] + 4.5, s[2])): print('spawn INSIDE something', s)
