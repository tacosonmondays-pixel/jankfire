# ARCTIC CABIN (18 Nov 2026; the owner: "make an artic cabin"). A brand-new arena of our own: a snowed-in cabin
# compound in a mountain valley. The hit boxes, spawns and team spawns in studs local to the arena's origin (ground
# y = 0). Plain Python: the plan (arena_plan.py), the checks (arena_check.py) and the kit (arctic_models.py) read the
# same numbers. No layout, landmark, name or look from any other game: what it takes from classic shooter maps is only
# their principles (three lanes, readable sight lines, power positions with counters, flanks, cover rhythm, short
# spawn-to-fight times).
#
# Mirror-symmetric across x = 0 (attackers spawn at the west end, defenders at the east; Matches swaps ends each round).
# North is -z. Three lanes, west to east:
#   north   THE RIDGE: a rock shelf along the whole north side, its top at y 14, its face stepped in three strata. Up from
#           each spawn yard by a wide stone stair, and from the middle yard by a narrow stair each side. A knoll in its
#           middle (y 20) splits the ridge's long line; the paths pass in front of it and behind it.
#   middle  THE CABIN: a big two-storey log cabin on the centre line. Ground floor: two wings and a great room round a
#           double-sided stone hearth (the hearth stands in every straight line through the cabin's doors). Upstairs:
#           the wings' rooms (windows west/east over the yards, north at the ridge, south onto the balcony), a gallery
#           along the great room's north wall joining them, and a covered balcony along the south face, reached from the
#           rooms or by an outside stair at each end. The roof is a low-pitched snow roof you can walk on (its hit boxes
#           are terraces that follow its slope), the chimney its only cover: a high, exposed power position.
#   south   THE POND: a frozen pond across the south, a boathouse at each tip you can walk through, ice-fishing huts and
#           snowdrifts across the ice (cover every 15-25 studs), an island with a big pine in the middle. Behind it the
#           south woods: pines, drifts and a buried rail fence, the long flank.
#   yards   between the spawns and the cabin: a sauna you can go into, a woodshed under the ridge (its roof steps up to
#           the ridge top), a tool shed with a flat roof you climb by crates, firewood stacks, pines, drifts.
# Gravity 78 studs/s^2, a jump about 4.9 studs: rail fences (2.4) and crates (4.2) are jumpable, drifts (4.2) are cover.
import math

LID = 150.0
STEP, RUN = 1.0, 1.4
G = 78.0
UP = 12.0                # the cabin's upper floor (top)
WALLTOP = 24.0           # the cabin's walls
T = 1.4                  # the cabin's log walls
COURSE = 1.2             # one log course (every opening's top and bottom sits on a course line)
DOOR, WIN0, WIN1, UWIN0, UWIN1 = 9.6, 3.6, 8.4, 14.4, 20.4
RIDGE = 14.0             # the ridge top
KNOLL = 20.0             # the knoll on the ridge
X_EDGE, Z_EDGE = 150.0, 110.0
CLIFF = -66.0            # the ridge's face (its lowest stratum)

MATS = {
    'snow': ('Snow', 'd9dee2', 'snow'),
    'ice': ('Ice', 'b4c7d1', 'ice'),
    'rock': ('Rock', '868a90', 'rock'),
    'log': ('WoodPlanks', '7a5d45', 'wood'),
    'floor': ('WoodPlanks', '9c7e62', 'wood'),
    'step': ('WoodPlanks', '94775c', 'wood'),
    'roof': ('Snow', 'dde2e6', 'snow'),
    'stone': ('Slate', '8a8b8e', 'stone'),
    'wood': ('Wood', '7d6b5c', 'wood'),
    'drift': ('Snow', 'dce1e5', 'snow'),
    'tree': ('Wood', '5e4a3a', 'wood'),
    'fence': ('Wood', '7b6450', 'wood'),
    'rail': ('Wood', '7b6450', 'wood'),
    'firewood': ('Wood', '8a6a4c', 'wood'),
    'cover': ('WoodPlanks', '8f7458', 'wood'),
    'edge': ('SmoothPlastic', 'c8c4bd', 'edge'),
    'ledge': ('SmoothPlastic', 'c8c4bd', 'ledge'),   # the wall box's step (wallbox.py)
    'bound': ('SmoothPlastic', 'c8c4bd', 'bound'),   # its walls
}

SOLID, ROT, SPAWNS, PADS, WATER, NOTES = [], [], [], [], [], []
TEAM = {'att': [], 'def': [], 'mid': []}
OPENS = []       # (x0, y0, z0, x1, y1, z1, kind): door and window openings (the kit frames them)
STAIRS = []      # (x0, z0, x1, z1, axis 'x'|'z', direction +1|-1, steps, y_from, mat): every stair, for the kit
TREES = []       # (x, z, r, h, y0): every pine (the trunk is the hit box; the tiers are look only)
DRIFTS = []      # (cx, cz, rx, rz, h, yaw degrees, lean): every snowdrift (hit boxes inscribed under the dome; lean: the top
                 # leans this fraction of rx along the drift's local x, windswept)
HUTS = []        # (x0, z0, x1, z1, kind): outbuildings and huts, for the kit: 'sauna', 'woodshed', 'toolshed', 'boathouse', 'icehut'
FIREWOOD = []    # (x0, y0, z0, x1, y1, z1): firewood stacks
FENCES = []      # (x0, z0, x1, z1): buried rail fences
ROCKS = []       # (x0, y0, z0, x1, y1, z1): boulders and lips (rounded boxes in the kit)
CRATES = []      # (x0, y0, z0, x1, y1, z1)
FURNITURE = []   # (x0, y0, z0, x1, y1, z1, kind)

def box(x0, y0, z0, x1, y1, z1, m):
    SOLID.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), m))

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

def circle_boxes(cx, cz, rx, rz, y0, y1, yaw, m, flags=''):
    """a round (or oval) footprint as three boxes whose corners lie on the ellipse (a 16-sided cover of it)"""
    for (a, b) in ((0.924, 0.383), (0.707, 0.707), (0.383, 0.924)):
        rot(cx, (y0 + y1) / 2, cz, 2 * a * rx, y1 - y0, 2 * b * rz, yaw, m, flags)

# ---------------------------------------------------------------- mirroring: the west half is written once
class Mirror:
    """everything added inside is copied to the east half (x -> -x; turned boxes' yaw -> -yaw)"""
    def lists(self):
        return {'SOLID': SOLID, 'ROT': ROT, 'PADS': PADS, 'WATER': WATER, 'OPENS': OPENS, 'STAIRS': STAIRS, 'TREES': TREES,
                'DRIFTS': DRIFTS, 'HUTS': HUTS, 'FIREWOOD': FIREWOOD, 'FENCES': FENCES, 'ROCKS': ROCKS, 'CRATES': CRATES,
                'FURNITURE': FURNITURE, 'NOTES': NOTES, 'SPAWNS': SPAWNS}
    def __enter__(self):
        self.n = {k: len(v) for k, v in self.lists().items()}
        return self
    def __exit__(self, *a):
        L = self.lists()
        new = {k: list(v[self.n[k]:]) for k, v in L.items()}
        for b in new['SOLID']: SOLID.append((-b[3], b[1], b[2], -b[0], b[4], b[5], b[6]))
        for r in new['ROT']: ROT.append((-r[0], r[1], r[2], r[3], r[4], r[5], -r[6], r[7], r[8]))
        for p in new['PADS']: PADS.append((-p[3], p[1], p[2], -p[0], p[4], p[5], -p[6], p[7], p[8]))
        for w in new['WATER']: WATER.append((-w[3], w[1], w[2], -w[0], w[4], w[5]))
        for o in new['OPENS']: OPENS.append((-o[3], o[1], o[2], -o[0], o[4], o[5], o[6]))
        for s in new['STAIRS']:
            x0, z0, x1, z1, ax, d, n, yf, m = s
            STAIRS.append((-x1, z0, -x0, z1, ax, -d if ax == 'x' else d, n, yf, m))
        for t in new['TREES']: TREES.append((-t[0], t[1], t[2], t[3], t[4]))
        for d in new['DRIFTS']: DRIFTS.append((-d[0], d[1], d[2], d[3], d[4], -d[5], -d[6]))
        for h in new['HUTS']: HUTS.append((-h[2], h[1], -h[0], h[3], h[4]))
        for f in new['FIREWOOD']: FIREWOOD.append((-f[3], f[1], f[2], -f[0], f[4], f[5]))
        for f in new['FENCES']: FENCES.append((-f[2], f[1], -f[0], f[3]))
        for b in new['ROCKS']: ROCKS.append((-b[3], b[1], b[2], -b[0], b[4], b[5]))
        for b in new['CRATES']: CRATES.append((-b[3], b[1], b[2], -b[0], b[4], b[5]))
        for b in new['FURNITURE']: FURNITURE.append((-b[3], b[1], b[2], -b[0], b[4], b[5], b[6]))
        for n_ in new['NOTES']: NOTES.append((-n_[0], n_[1], n_[2], n_[3]))
        for s in new['SPAWNS']: SPAWNS.append((-s[0], s[1], s[2]))

# ---------------------------------------------------------------- pieces
def wall(axis, c0, c1, a0, a1, y0, y1, holes, m='log'):
    """a wall along `axis` ('x': from a0 to a1 in x, thickness c0..c1 in z; 'z': the other way) from y0 to y1 with
    rectangular holes [(a0, a1, y0, y1, kind)]"""
    rects = [(a0, y0, a1, y1)]
    for (h0, h1, hy0, hy1, kind) in holes:
        rects = subtract(rects, (h0, hy0, h1, hy1))
        if axis == 'x': OPENS.append((h0, hy0, c0, h1, hy1, c1, kind))
        else: OPENS.append((c0, hy0, h0, c1, hy1, h1, kind))
    for (u0, v0, u1, v1) in rects:
        if axis == 'x': box(u0, v0, c0, u1, v1, c1, m)
        else: box(c0, v0, u0, c1, v1, u1, m)

def stair_z(x0, x1, z_start, direction, n, y_from=0.0, m='step'):
    """n steps along z from z_start (direction +1/-1), across x0..x1, each STEP up and RUN along; solid down to y_from"""
    for k in range(1, n + 1):
        za = z_start + direction * (k - 1) * RUN
        zb = z_start + direction * k * RUN
        box(x0, y_from, za, x1, y_from + k * STEP, zb, m)
    zend = z_start + direction * n * RUN
    STAIRS.append((x0, min(z_start, zend), x1, max(z_start, zend), 'z', direction, n, y_from, m))
    return zend

def stair_x(z0, z1, x_start, direction, n, y_from=0.0, m='step'):
    for k in range(1, n + 1):
        xa = x_start + direction * (k - 1) * RUN
        xb = x_start + direction * k * RUN
        box(xa, y_from, z0, xb, y_from + k * STEP, z1, m)
    xend = x_start + direction * n * RUN
    STAIRS.append((min(x_start, xend), z0, max(x_start, xend), z1, 'x', direction, n, y_from, m))
    return xend

def tree(x, z, r=1.2, h=30.0, y0=0.0):
    TREES.append((x, z, r, h, y0))
    for k in range(2):
        rot(x, y0 + h / 2, z, 2 * r, h, 2 * r, 45.0 * k, 'tree')

def drift(cx, cz, rx, rz, h, yaw=0.0, lean=0.3):
    """a snowdrift: a dome rx by rz, h high, its top leaning `lean` of rx along its local x (the kit's look). its hit
    boxes sit inside the dome: three bands, each a 16-sided cover of the dome's section at the band's top, moved with
    the lean"""
    DRIFTS.append((cx, cz, rx, rz, h, yaw, lean))
    t = math.radians(yaw)
    ux, uz = math.cos(t), -math.sin(t)          # (the drift's local x in the world: CFrame.Angles(0, yaw, 0))
    for (f0, f1) in ((0.0, 0.3), (0.3, 0.6), (0.6, 0.85)):
        k = math.sqrt(max(0.0, 1.0 - f1 * f1))
        d = lean * rx * f1
        circle_boxes(cx + d * ux, cz + d * uz, rx * k, rz * k, h * f0, h * f1, yaw, 'drift')

def firewood(x0, z0, x1, z1, h):
    FIREWOOD.append((x0, 0.0, z0, x1, h, z1))
    box(x0, 0, z0, x1, h, z1, 'firewood')

def fence(x0, z0, x1, z1, gates=()):
    """a buried split-rail fence (2.4 high, jumpable) along x or z with gaps [(a, b)]"""
    along_x = (x1 - x0) > (z1 - z0)
    a0, a1 = (x0, x1) if along_x else (z0, z1)
    pts, cur = [], a0
    for (g0, g1) in sorted(gates):
        if g0 > cur: pts.append((cur, g0))
        cur = max(cur, g1)
    if cur < a1: pts.append((cur, a1))
    for (u0, u1) in pts:
        if along_x: box(u0, 0, z0, u1, 2.4, z1, 'fence'); FENCES.append((u0, z0, u1, z1))
        else: box(x0, 0, u0, x1, 2.4, u1, 'fence'); FENCES.append((x0, u0, x1, u1))

def rock(x0, y0, z0, x1, y1, z1):
    ROCKS.append((x0, y0, z0, x1, y1, z1))
    box(x0, y0, z0, x1, y1, z1, 'rock')

def crate(x0, y0, z0, x1, y1, z1):
    CRATES.append((x0, y0, z0, x1, y1, z1))
    box(x0, y0, z0, x1, y1, z1, 'cover')

def furn(x0, y0, z0, x1, y1, z1, kind):
    FURNITURE.append((x0, y0, z0, x1, y1, z1, kind))
    box(x0, y0, z0, x1, y1, z1, 'cover')

# ================================================================ the ground: snow, the frozen pond (ice), the ridge
POND = (0.0, 50.0, 82.0, 30.0)          # centre x, z, semi-axes
def pond_half(z):
    cx, cz, a, b = POND
    t = (z - cz) / b
    return a * math.sqrt(max(0.0, 1.0 - t * t))
ICE = []                                 # the ice strips (hit boxes; the kit draws a smooth oval)
zz = POND[1] - POND[3]
while zz < POND[1] + POND[3] - 1e-6:
    z2 = min(zz + 4.0, POND[1] + POND[3])
    w = pond_half((zz + z2) / 2)
    if w > 1.0: ICE.append((-w, zz, w, z2))
    zz = z2
rects = [(-X_EDGE, CLIFF, X_EDGE, Z_EDGE)]
for h in ICE: rects = subtract(rects, h)
for (x0, z0, x1, z1) in rects: box(x0, -6.0, z0, x1, 0.0, z1, 'snow')
for (x0, z0, x1, z1) in ICE: box(x0, -6.0, z0, x1, 0.0, z1, 'ice')
# the ridge: three strata, each a little further back (the kit draws the same steps)
box(-X_EDGE, -6.0, -Z_EDGE, X_EDGE, 5.0, CLIFF, 'rock')
box(-X_EDGE, 5.0, -Z_EDGE, X_EDGE, 10.0, CLIFF - 0.8, 'rock')
box(-X_EDGE, 10.0, -Z_EDGE, X_EDGE, RIDGE, CLIFF - 1.6, 'rock')
# the knoll in its middle, a low stone wall along its front, a stair up each side
box(-14.0, RIDGE, -96.0, 14.0, KNOLL, -78.0, 'rock')
rock(-12.0, KNOLL, -80.0, -3.5, KNOLL + 2.8, -78.4)
rock(3.5, KNOLL, -80.0, 12.0, KNOLL + 2.8, -78.4)
NOTES.extend([(0.0, -87.0, 2, 'KNOLL'), (0.0, -102.0, 1, 'RIDGE'), (0.0, -72.0, 1, 'FRONT PATH')])

# ================================================================ the cabin: x -34..34, z -48..-10
CX, CZ0, CZ1 = 34.0, -48.0, -10.0
PART = 14.0              # the partitions between the wings and the great room (x = +-14)
# the great room's own pieces (symmetric, built once)
box(-5.0, 0.0, -34.0, 5.0, WALLTOP, -16.0, 'stone')            # the double-sided hearth
box(-3.5, WALLTOP, -28.0, 3.5, 36.0, -22.0, 'stone')            # its chimney through the roof
box(-PART + 0.6, UP - 0.8, CZ0 + T, PART - 0.6, UP, -40.0, 'floor')   # the gallery along the north wall
rot(0.0, UP + 1.8, -39.8, 2 * (PART - 0.6), 3.6, 0.4, 0.0, 'rail', 'c')
# the balcony along the south face (y 12) on posts, the porch under it
BAL = (-30.0, CZ1, 30.0, -3.6)
box(BAL[0], UP - 0.8, BAL[1], BAL[2], UP, BAL[3], 'floor')
box(BAL[0], 0.0, BAL[1], BAL[2], 0.4, BAL[3], 'floor')
rot(0.0, UP + 1.8, BAL[3] + 0.2, BAL[2] - BAL[0], 3.6, 0.4, 0.0, 'rail', 'c')
for x in (-29.4, -15.0, 15.0, 29.4):
    rot(x, 11.0, BAL[3] + 0.5, 0.9, 22.0, 0.9, 0.0, 'wood')
# the roof: a low-pitched gable along x (ridge z -29 at y 29.5, slope 0.27), walkable: terraces 1 stud apart that follow
# its surface within half a stud. over the walls they start at the ceiling (24); outside them (the north overhang, the
# part over the balcony) lower, leaving the balcony 8.5 studs of headroom
ROOF_RIDGE_Z, ROOF_TOP, ROOF_S = -29.0, 29.5, 0.27
ROOF_Z0, ROOF_Z1, ROOF_X = CZ0 - 1.4, -2.5, CX + 1.4
ROOF_TERRACES = []
k = 0
while True:
    top = ROOF_TOP - k
    d = (k + 0.5) / ROOF_S
    za, zb = max(ROOF_Z0, ROOF_RIDGE_Z - d), min(ROOF_Z1, ROOF_RIDGE_Z + d)
    ROOF_TERRACES.append((za, zb, top))
    for (p0, p1, inside) in ((za, min(zb, CZ0), False), (max(za, CZ0), min(zb, CZ1), True), (max(za, CZ1), zb, False)):
        if p1 - p0 < 0.05: continue
        bot = WALLTOP if inside else max(top - 2.0, 20.5)
        if top - bot > 0.05: box(-ROOF_X, bot, p0, ROOF_X, top, p1, 'roof')
    if za <= ROOF_Z0 and zb >= ROOF_Z1: break
    k += 1
def roof_y(z):
    """the snow roof's surface (the kit's look)"""
    return ROOF_TOP - ROOF_S * abs(z - ROOF_RIDGE_Z)
NOTES.extend([(0.0, -25.0, 0, 'HEARTH'), (0.0, -6.5, 1, 'BALCONY'), (0.0, -44.0, 1, 'GALLERY'), (0.0, -36.0, 2, 'CABIN ROOF')])

with Mirror():
    # ------------------------------------------------------------ the cabin's west half
    x0w, x1w = -CX, 0.0
    # the north wall: a back door into the wing, a great-room window; upstairs a wing window and a gallery window
    wall('x', CZ0, CZ0 + T, x0w, x1w, 0, WALLTOP,
         [(-30.0, -24.0, 0, DOOR, 'door'), (-10.0, -5.0, WIN0, WIN1, 'window'), (-25.0, -20.0, UWIN0, UWIN1, 'window'), (-9.0, -4.0, UWIN0, UWIN1, 'window')])
    # the south wall: the wing's door to the porch, half the great room's double door; upstairs the wing's door to the
    # balcony and a window over the stair, big windows from the great room onto the balcony
    wall('x', CZ1 - T, CZ1, x0w, x1w, 0, WALLTOP,
         [(-30.0, -25.0, 0, DOOR, 'door'), (-4.0, 0.0, 0, DOOR, 'door'), (-11.0, -6.0, WIN0, WIN1, 'window'),
          (-30.0, -25.0, UP, UP + DOOR, 'door'), (-23.0, -20.0, UWIN0, UWIN1, 'window'), (-11.0, -5.0, UWIN0, UP + DOOR, 'window')])
    # the west wall: the door and a window in the hearth's shadow (every straight line through them ends on it); upstairs
    # two windows over the west yard
    wall('z', -CX, -CX + T, CZ0 + T, CZ1 - T, 0, WALLTOP,
         [(-33.0, -27.0, 0, DOOR, 'door'), (-22.0, -17.0, WIN0, WIN1, 'window'), (-40.0, -35.0, UWIN0, UWIN1, 'window'), (-22.0, -17.0, UWIN0, UWIN1, 'window')])
    # the partition between the wing and the great room: a doorway on the ground (north part), one upstairs to the gallery
    wall('z', -PART - 0.6, -PART + 0.6, CZ0 + T, CZ1 - T, 0, WALLTOP,
         [(-42.0, -36.0, 0, DOOR, 'door'), (-46.0, -41.0, UP, UP + DOOR, 'door')])
    # the stair along the partition, from the porch side up toward the north
    sx0, sx1 = -PART - 0.6 - 5.0, -PART - 0.6
    zs = CZ1 - T - 1.0
    stair_z(sx0, sx1, zs, -1, int(UP))
    ha, hb = zs - 4 * RUN, zs - int(UP) * RUN
    hole = (sx0, min(ha, hb), sx1, max(ha, hb))
    for (a0, c0, a1, c1) in subtract([(-CX + T, CZ0 + T, -PART - 0.6, CZ1 - T)], hole):
        box(a0, UP - 0.8, c0, a1, UP, c1, 'floor')
    rot(sx0 - 0.2, UP + 1.8, (hole[1] + hole[3]) / 2, 0.4, 3.6, hole[3] - hole[1], 0.0, 'rail', 'c')
    rot((sx0 + sx1) / 2, UP + 1.8, ha, sx1 - sx0, 3.6, 0.4, 0.0, 'rail', 'c')
    # the outside stair from the yard up to the balcony's end
    stair_x(-9.6, -4.6, -46.8, +1, int(UP))
    # a small porch roof over the west door
    box(-CX - 3.2, 10.0, -34.0, -CX, 10.8, -26.0, 'roof')
    # furniture (cover inside): the kitchen counter under the west window, a table; upstairs beds and a wardrobe
    furn(-CX + T, 0, -23.0, -CX + T + 2.6, 3.2, -16.0, 'counter')
    furn(-27.0, 0, -42.0, -21.0, 2.8, -38.0, 'table')
    furn(-CX + T, UP, -46.6 + 0.2, -CX + T + 5.0, UP + 2.2, -43.0, 'bed')
    furn(-CX + T, UP, -15.0, -CX + T + 2.4, UP + 8.0, -12.0, 'wardrobe')
    furn(-12.4, 0, -14.0, -9.0, 2.6, -11.4 - 0.1, 'bench')

    # ------------------------------------------------------------ the north yard: the ridge stairs, the woodshed, firewood
    stair_z(-49.0, -44.0, -46.4, -1, int(RIDGE))                    # the narrow mid stair
    box(-49.0, 0.0, CLIFF - 1.6, -44.0, RIDGE, CLIFF, 'step')       # (its top cut into the strata)
    stair_z(-132.0, -124.0, -46.4, -1, int(RIDGE))                  # the wide end stair by the spawn yard
    box(-132.0, 0.0, CLIFF - 1.6, -124.0, RIDGE, CLIFF, 'step')
    # the woodshed against the cliff: side walls, an open front, logs stacked at the back; its lean-to roof steps up to
    # the ridge top (walkable)
    HUTS.append((-74.0, CLIFF, -58.0, -55.0, 'woodshed'))
    box(-74.0, 0, CLIFF - 1.6, -73.0, 9.4, -55.0, 'wood'); box(-59.0, 0, CLIFF - 1.6, -58.0, 9.4, -55.0, 'wood')
    for (za, top) in ((-54.2, 10.4), (-58.2, 11.4), (-62.2, 12.4)):
        box(-74.6, top - 1.0, CLIFF - 1.6, -57.4, top, za, 'roof')
    firewood(-73.0, CLIFF + 0.2, -59.0, -61.0, 5.5)
    firewood(-21.0, -59.0, -9.0, -56.0, 4.4)                       # in front of the back doors
    # the tool shed by the spawn yard: flat roof, climbed by two crates
    HUTS.append((-112.0, -40.0, -100.0, -28.0, 'toolshed'))
    box(-112.0, 0, -40.0, -100.0, 10.0, -28.0, 'wood')
    box(-112.6, 10.0, -40.6, -99.4, 10.8, -27.4, 'roof')
    crate(-104.0, 0, -27.8, -100.0, 4.2, -24.0)
    crate(-108.4, 0, -27.8, -104.2, 8.4, -24.4)
    NOTES.extend([(-66.0, -60.0, 0, 'WOODSHED'), (-106.0, -34.0, 0, 'TOOL SHED'), (-46.5, -56.0, 0, 'STAIR'), (-128.0, -56.0, 0, 'STAIR')])

    # ------------------------------------------------------------ the sauna (you go in by its east door)
    HUTS.append((-76.0, -2.0, -62.0, 12.0, 'sauna'))
    wall('z', -63.2, -62.0, -0.8, 10.8, 0, 10.0, [(2.0, 7.0, 0, 8.0, 'door')], m='wood')
    wall('z', -76.0, -74.8, -0.8, 10.8, 0, 10.0, [], m='wood')
    wall('x', -2.0, -0.8, -76.0, -62.0, 0, 10.0, [(-71.0, -67.0, 3.5, 7.0, 'window')], m='wood')
    wall('x', 10.8, 12.0, -76.0, -62.0, 0, 10.0, [(-71.0, -67.0, 3.5, 7.0, 'window')], m='wood')
    furn(-74.8, 0, 0.6, -71.6, 2.4, 9.2, 'sauna_bench')
    furn(-66.0, 0, 7.8, -63.2, 4.0, 10.8, 'stove')
    for (za, zb, top) in ((-2.8, 12.8, 10.8), (-0.2, 10.2, 11.8), (2.6, 7.4, 12.6)):
        box(-76.8, top - 0.8, za, -61.2, top, zb, 'roof')
    NOTES.append((-69.0, 5.0, 0, 'SAUNA'))

    # ------------------------------------------------------------ the boathouse at the pond's west tip (open onto the ice)
    HUTS.append((-102.0, 32.0, -86.0, 54.0, 'boathouse'))
    wall('z', -87.2, -86.0, 33.2, 52.8, 0, 13.0, [(36.0, 50.0, 0, 10.0, 'slip')], m='wood')
    wall('z', -102.0, -100.8, 33.2, 52.8, 0, 13.0, [(40.0, 45.0, 0, 9.0, 'door')], m='wood')
    wall('x', 32.0, 33.2, -102.0, -86.0, 0, 13.0, [(-97.0, -92.0, 4.0, 8.0, 'window')], m='wood')
    wall('x', 52.8, 54.0, -102.0, -86.0, 0, 13.0, [(-97.0, -92.0, 4.0, 8.0, 'window')], m='wood')
    box(-102.8, 13.0, 31.2, -85.2, LID, 54.8, 'roof')               # its steep roof (solid to the old lid; roofs.py)
    furn(-99.0, 0, 37.0, -89.0, 2.6, 41.0, 'boat')
    crate(-100.4, 0, 47.0, -97.0, 3.6, 51.0)
    NOTES.append((-94.0, 43.0, 0, 'BOATHOUSE'))

    # ------------------------------------------------------------ the pond: ice-fishing huts, drifts on the ice
    HUTS.append((-31.0, 35.0, -25.0, 41.0, 'icehut'))
    box(-31.0, 0, 35.0, -25.0, 8.0, 41.0, 'wood')
    HUTS.append((-19.0, 63.0, -13.0, 69.0, 'icehut'))
    box(-19.0, 0, 63.0, -13.0, 8.0, 69.0, 'wood')
    drift(-54.0, 28.0, 8.0, 6.0, 4.4, 20.0, 0.3)
    drift(-58.0, 68.0, 7.5, 6.0, 4.4, -15.0, -0.3)
    drift(-38.0, 56.0, 5.5, 4.5, 4.0, 40.0, 0.25)
    NOTES.extend([(-28.0, 38.0, 0, 'HUT'), (-16.0, 66.0, 0, 'HUT')])

    # ------------------------------------------------------------ the yards: spawn screens, pines, drifts, fences
    # the spawn yard's woodpile screens: two staggered stacks, overlapping in z (no straight line out of the yard passes
    # between them; you walk round either end or through the stagger)
    firewood(-122.0, -22.0, -118.0, 2.0, 6.4)
    firewood(-116.0, -2.0, -112.0, 22.0, 6.4)
    drift(-112.0, 24.0, 7.0, 5.0, 4.4, 75.0)
    drift(-94.0, 6.0, 6.0, 5.0, 4.2, 10.0)
    drift(-88.0, -40.0, 6.5, 5.0, 4.2, -30.0)
    drift(-46.0, 14.0, 5.0, 4.0, 3.8, 0.0)
    for (x, z, r) in ((-138.0, -48.0, 1.4), (-90.0, -22.0, 1.2), (-128.0, 58.0, 1.4), (-142.0, 84.0, 1.3), (-116.0, -8.0 - 50.0, 1.2),
                      (-60.0, 20.0, 1.1)):
        tree(x, z, r, 30.0)
    fence(-82.0, 15.8, -36.0, 16.4, gates=[(-70.0, -62.0), (-50.0, -44.0)])   # the pond's north shore
    # the south woods: pines, drifts, a buried rail fence along the pond's south shore, boulders
    for (x, z, r) in ((-124.0, 96.0, 1.4), (-100.0, 86.0, 1.3), (-76.0, 100.0, 1.4), (-52.0, 92.0, 1.2), (-30.0, 104.0, 1.3),
                      (-12.0, 88.0, 1.2), (-140.0, 104.0, 1.3)):
        tree(x, z, r, 30.0)
    drift(-86.0, 98.0, 6.0, 4.5, 4.0, 30.0)
    drift(-42.0, 98.0, 5.5, 4.5, 4.0, -20.0)
    drift(-110.0, 104.0, 6.0, 4.0, 3.6, 0.0)
    fence(-80.0, 84.6, -20.0, 85.2, gates=[(-64.0, -56.0), (-36.0, -30.0)])
    rock(-66.0, 0, 102.0, -58.0, 4.6, 108.0)
    # more cover through the south woods (its long lines broken every 30-40 studs)
    for (x, z, r) in ((-64.0, 88.0, 1.3), (-110.0, 92.0, 1.3), (-40.0, 86.5, 1.2), (-90.0, 106.0, 1.3), (-20.0, 96.0, 1.2), (-136.0, 92.0, 1.3)):
        tree(x, z, r, 30.0)
    rock(-52.0, 0, 81.0, -46.0, 4.4, 84.2)
    rock(-118.0, 0, 82.0, -111.0, 5.2, 87.0)
    rock(-30.0, 0, 88.0, -24.0, 5.0, 92.0)
    firewood(-100.0, 96.0, -94.0, 100.0, 5.2)
    tree(-46.0, 94.0, 1.3, 30.0)
    rock(-12.0, 0, 100.0, -6.0, 5.4, 104.0)
    rock(-80.0, 0, 106.5, -73.0, 5.6, 110.0)
    # a woodpile in the north yard between the cabin's corner and the mid stair
    firewood(-43.0, -52.0, -38.0, -49.0, 5.6)
    # ------------------------------------------------------------ the ridge top: pines, lip rocks along the front, boulders
    for (x, z, r) in ((-40.0, -92.0, 1.3), (-72.0, -102.0, 1.4), (-100.0, -86.0, 1.3), (-58.0, -80.0, 1.1), (-126.0, -100.0, 1.4),
                      (-142.0, -78.0, 1.2), (-22.0, -104.0, 1.2)):
        tree(x, z, r, 26.0, y0=RIDGE)
    for (x0, x1) in ((-38.0, -30.0), (-68.0, -61.0), (-102.0, -94.0), (-146.0, -139.0)):
        rock(x0, RIDGE, -71.4, x1, RIDGE + 4.6, CLIFF - 1.6)
    rock(-30.0, RIDGE, -98.0, -24.0, RIDGE + 4.2, -92.0)
    # boulders that break the ridge's long lines: one on the front path beside the knoll, one across the back path
    rock(-25.0, RIDGE, -78.0, -18.0, RIDGE + 4.6, -71.4)
    rock(-40.0, RIDGE, -110.0, -33.0, RIDGE + 5.4, -96.0)
    rock(-86.0, RIDGE, -96.0, -79.0, RIDGE + 4.0, -89.0)
    # the knoll's west stair
    stair_x(-90.0, -85.0, -22.4, +1, int(KNOLL - RIDGE), y_from=RIDGE, m='stone')

# the yard in front of the porch: a stone fire pit with two log benches, a woodpile each side (cover in the open field)
FIREPIT = (0.0, 10.0, 3.2)
circle_boxes(0.0, 10.0, 3.2, 3.2, 0.0, 1.4, 22.5, 'rock')
with Mirror():
    furn(-9.5, 0, 6.0, -7.5, 1.8, 14.0, 'logbench')
    firewood(-24.0, 2.0, -16.0, 5.0, 4.4)
firewood(-4.0, 13.0, 4.0, 19.5, 5.8)                             # a woodpile on the pond's north shore, mid-line

# the pond's middle: the island (a low snowy mound) with a big pine and two boulders
ISLAND = (0.0, 50.0, 9.0, 1.0)
circle_boxes(0.0, 50.0, 9.0, 9.0, 0.0, 1.0, 0.0, 'snow')
tree(0.0, 50.0, 2.0, 36.0)
rock(-5.0, 1.0, 41.0, 2.0, 6.8, 47.5)                             # the island's boulders: they and the pine close the
rock(1.5, 1.0, 52.0, 6.5, 5.0, 56.5)                              # lines between the boathouses' slips
NOTES.extend([(0.0, 60.0, 0, 'ISLAND'), (0.0, 30.0, 0, 'FROZEN POND'), (0.0, 98.0, 0, 'SOUTH WOODS')])

# ================================================================ spawns
# teams: attackers in the west spawn yard facing east, defenders mirrored; the third side (1v1v1) in the south woods
for (x, z) in ((-144.0, -14.0), (-144.0, -4.0), (-144.0, 6.0), (-144.0, 16.0), (-134.0, -9.0), (-134.0, 1.0), (-134.0, 11.0), (-127.0, 4.0)):
    TEAM['att'].append((x, 0.3, z, 1.0, 0.0))
    TEAM['def'].append((-x, 0.3, z, -1.0, 0.0))
TEAM['mid'] = [(-16.0, 0.3, 98.0, 0.0, -1.0), (16.0, 0.3, 98.0, 0.0, -1.0), (0.0, 0.3, 106.0, 0.0, -1.0), (0.0, 0.3, 95.0, 0.0, -1.0)]
with Mirror():
    for (x, y, z) in ((-136.0, 0.0, 48.0), (-108.0, 0.0, -16.0), (-80.0, 0.0, 40.0), (-82.0, 0.0, -30.0), (-66.0, 0.0, -48.0),
                      (-46.0, 0.0, 2.0), (-24.0, 0.0, -30.0), (-25.0, UP, -36.0), (-70.0, RIDGE, -90.0), (-28.0, 0.0, 96.0),
                      (-44.0, 0.0, 40.0), (-116.0, RIDGE, -80.0)):
        SPAWNS.append((x, y + 0.3, z))
for p in ((0.0, KNOLL + 0.3, -87.0), (0.0, UP + 0.3, -43.0), (0.0, 0.7, -6.8), (0.0, 0.3, 33.0)):
    SPAWNS.append(p)

# ================================================================ for the plan (arena_plan.py)
TITLE = 'ARCTIC CABIN'
BOUNDS = (-183.0, 183.0, -143.0, 143.0)   # (the wall box: walls to 180 / 140)
LEVELS = [('GROUND: YARDS, CABIN, POND (y 0)', 0.6, 10.0, 0.0), ('UPSTAIRS, BALCONY, RIDGE (y 12 to 14)', 10.0, 19.6, 13.0),
          ('KNOLL, CABIN ROOF (y 20 to 29.5)', 19.6, 31.0, 25.0)]
FLOORS = ('snow', 'ice', 'floor', 'step', 'rock', 'roof')
COLOURS = {'snow': (196, 204, 212), 'ice': (150, 186, 206), 'rock': (128, 128, 138), 'log': (150, 100, 70), 'stone': (120, 120, 126),
           'floor': (200, 170, 130), 'step': (205, 186, 172), 'roof': (184, 194, 206), 'wood': (176, 132, 96), 'tree': (70, 112, 74),
           'drift': (224, 230, 238), 'fence': (160, 120, 90), 'firewood': (150, 106, 72), 'cover': (226, 160, 152)}
PLAN_NOTE = ('three lanes: the ridge (north, a knoll in its middle), the cabin (through the wings and round the hearth, up to the '
             'gallery and the balcony, onto the roof), the frozen pond (boathouses, huts, drifts, the island) with the south woods behind; '
             'sauna, woodshed and tool shed in the yards')

# ================================================================ self-checks (py tools/roblox/arctic_layout.py)
def floor_under(p):
    best = None
    for s in SOLID:
        if s[0] <= p[0] <= s[3] and s[2] <= p[2] <= s[5] and -1.0 <= p[1] - s[4] <= 1.5:
            best = s[4] if best is None else max(best, s[4])
    return best

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
        for s in SOLID:
            if s[0] < nxt[0] < s[3] and s[2] < nxt[2] < s[5] and s[1] < nxt[1] + 2.5 < s[4] and not (s[0] < pos[0] < s[3] and s[2] < pos[2] < s[5]):
                return (nxt[0], nxt[1], nxt[2], t, 'HIT ' + s[6])
        pos = nxt
    return None

# ================================================================ the wall box (tools/roblox/wallbox.py)
# no lid; the walls 30 studs out; between the old edge and them a step up to 36 (the snowbanks and pines past the edge,
# the rock wall behind the ridge), a ledge nobody can stay on; the snowbank walls seen to 10 (above: pines, the grid)
import wallbox
HIT_SOLID, HIT_ROT, WALLBOX = wallbox.rect(SOLID, ROT, X_EDGE, Z_EDGE, -6.0, 36.0, 10.0, drop=lambda b: b[6] == 'edge')

if __name__ == '__main__':
    print('solid %d, turned %d, pads %d, water %d, spawns %d, team %s' % (len(SOLID), len(ROT), len(PADS), len(WATER), len(SPAWNS), {k: len(v) for k, v in TEAM.items()}))
    print('roof terraces', [(round(a, 1), round(b, 1), t) for (a, b, t) in ROOF_TERRACES])
    for p in PADS: print('pad at (%.0f, %.0f) lands' % ((p[0] + p[3]) / 2, (p[2] + p[5]) / 2), pad_flight(p))
