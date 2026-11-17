# THE GUT arena's layout (17 Nov 2026): the hit boxes, spawns and team spawns, in studs local to the arena's origin
# (street level y = 0). Plain Python with no Blender in it, so the plan drawing (gut_plan.py) and the kit
# (gut_models.py) read the same numbers. The owner: "Can we have a map based on the gut district? We have this awesome
# heart tower build it would be a shame to not use it!! Maybe it can have a lower part that's a subway and the big
# train boss can pass by as an Easter egg".
#
# The plan, mirror-symmetric across x = 0 (attackers spawn in the west hall, defenders in the east hall):
#   street (y 0)    hall | yards | three lanes (the covered Tube north, the Approach in the middle, the open Avenue
#                   south) split by two blocks with an alley each | the round Plaza with the heart tower, a north court
#                   (a dome pavilion) and a south court (a gazebo) | the same again mirrored
#   tower           a spiral stair from the plinth up 315 degrees to a walkway balcony 21 studs up (the legs hold it);
#                   above a gate the stair and the heart are look only
#   subway (y -30)  one long platform under the south half, x -100..100, the track behind a full-height glass screen;
#                   stairs: one at each end up into each hall, two from the Plaza's south side
# Everything that is not walkable (buildings, the halls' roofs, the edge) is solid up to y 150, so there are no roofs
# to stand on; the edge is closed by an invisible wall and a lid at y 150.
import math

LID = 150.0          # top of the closed world
STEP, RUN = 1.0, 1.4 # every stair: 1 stud up per 1.4 along
PLAT = -30.0         # the platform's top
TRACK = -34.0        # the track bed's top
CEIL = -6.0          # the street slab's underside = the station's ceiling

# the hit boxes' looks (impacts): key -> (Roblox material, colour hex, what it is)
MATS = {
    'paving': ('SmoothPlastic', 'e7d5c8', 'paving'),
    'wall': ('SmoothPlastic', 'dfb2ab', 'enamel'),
    'block': ('SmoothPlastic', 'd9a7a2', 'enamel'),
    'edge': ('SmoothPlastic', 'c99a96', 'edge'),
    'cover': ('SmoothPlastic', 'e8c3bc', 'enamel'),
    'ivory': ('SmoothPlastic', 'efe3d6', 'ivory'),
    'tread': ('SmoothPlastic', 'e9bdb6', 'ivory'),
    'tile': ('SmoothPlastic', 'efe6dc', 'tile'),
    'step': ('SmoothPlastic', 'e2cfc2', 'tile'),
    'glass': ('Glass', 'f3d9da', 'glass'),
    'rail': ('Metal', 'd8a28c', 'metal'),
}

SOLID = []   # (x0, y0, z0, x1, y1, z1, mat)
ROT = []     # (cx, cy, cz, sx, sy, sz, yaw degrees (Roblox CFrame.Angles(0, yaw, 0)), mat, flags) flags: 'c' = collides, takes no shots
SPAWNS = []
TEAM = {'att': [], 'def': [], 'mid': []}
NOTES = []   # (x, z, level, text) for the plan
ROUNDS = []  # (cx, cz, r, y0, y1, mat): every round post (the kit dresses them)
BENCHES = [] # (cx, cz, angle, r0, r1, width, y0, y1): the Plaza's benches

def box(x0, y0, z0, x1, y1, z1, m):
    SOLID.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1), m))

def both(x0, y0, z0, x1, y1, z1, m):
    """a box on the west side and its mirror on the east"""
    box(x0, y0, z0, x1, y1, z1, m); box(-x0, y0, z0, -x1, y1, z1, m)

def rot(cx, cy, cz, sx, sy, sz, yaw, m, flags=''):
    ROT.append((cx, cy, cz, sx, sy, sz, yaw, m, flags))

def ang_box(cx, cz, a, r0, r1, wid, y0, y1, m, flags=''):
    """a box from radius r0 to r1 along the direction (cos a, 0, sin a) from (cx, cz), `wid` wide across it"""
    if m == 'cover': BENCHES.append((cx, cz, a, r0, r1, wid, y0, y1))
    rc = (r0 + r1) / 2
    rot(cx + rc * math.cos(a), (y0 + y1) / 2, cz + rc * math.sin(a), r1 - r0, y1 - y0, wid, -math.degrees(a), m, flags)

def round_(cx, cz, r, y0, y1, m, n=4, flags=''):
    """a round post: n squares turned 90/n degrees apart (n=2: an octagon, n=4: 16 sides), flats at radius r"""
    ROUNDS.append((cx, cz, r, y0, y1, m))
    for k in range(n):
        rot(cx, (y0 + y1) / 2, cz, 2 * r, y1 - y0, 2 * r, 90.0 * k / n, m, flags)

def subtract(rects, h):
    """[(x0, z0, x1, z1)] minus the hole h"""
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

# ================================================================ the street slab and the edge
X_EDGE, Z_EDGE = 150.0, 104.0
X_HALL = 112.0        # the halls' front walls
X_MID = 56.0          # where the lanes meet the centre
Z_IN, Z_TUBE, Z_OUTN = 36.0, 72.0, 96.0    # the blocks' inner faces, the Tube's south face, its north face
Z_AVE = 70.0          # the south blocks' face on the Avenue
# stairs: (x of the top, x of the bottom, z0, z1, top y, bottom y)
MID_STAIR = (20.0, 62.0, 24.0, 34.0)      # top at |x| 20 on the Plaza, down outward to |x| 62 on the platform
END_STAIR = (142.0, 100.0, 22.0, 32.0)    # top at |x| 142 in the hall, down inward to |x| 100 at the platform's end
HEAD = 7.0            # headroom: the slab is cut where a stair comes within this of its underside
def stair_open(top, bottom):
    """the stretch of a stair (|x|) where the slab over it must be cut"""
    k = int(math.ceil((CEIL - HEAD) - PLAT))      # the first step whose top is closer than HEAD to the ceiling
    d = (k - 1) * RUN
    return (bottom - d if top < bottom else bottom + d)
MID_OPEN = stair_open(MID_STAIR[0], MID_STAIR[1])   # |x| where the Plaza's opening starts (outer end)
END_OPEN = stair_open(END_STAIR[0], END_STAIR[1])   # |x| where the hall's opening starts (inner end)
OPENINGS = []
for s in (1, -1):
    OPENINGS.append((min(s * MID_STAIR[0], s * MID_OPEN), MID_STAIR[2], max(s * MID_STAIR[0], s * MID_OPEN), MID_STAIR[3]))
    OPENINGS.append((min(s * END_STAIR[0], s * END_OPEN), END_STAIR[2], max(s * END_STAIR[0], s * END_OPEN), END_STAIR[3]))
slab = [(-X_EDGE, -Z_EDGE, X_EDGE, Z_EDGE)]
for h in OPENINGS: slab = subtract(slab, h)
for (x0, z0, x1, z1) in slab: box(x0, CEIL, z0, x1, 0.0, z1, 'paving')
# the edge: invisible walls round the outside and a lid
box(-X_EDGE - 10, CEIL, -Z_EDGE - 10, -X_EDGE, LID, Z_EDGE + 10, 'edge')
box(X_EDGE, CEIL, -Z_EDGE - 10, X_EDGE + 10, LID, Z_EDGE + 10, 'edge')
box(-X_EDGE, CEIL, -Z_EDGE - 10, X_EDGE, LID, -Z_EDGE, 'edge')
box(-X_EDGE, CEIL, Z_EDGE, X_EDGE, LID, Z_EDGE + 10, 'edge')
box(-X_EDGE - 10, LID, -Z_EDGE - 10, X_EDGE + 10, LID + 5, Z_EDGE + 10, 'edge')

# ================================================================ the halls (west = attackers; mirrored east)
HALL_Z = 40.0          # the hall's inside: z -40..40
HALL_TOP = 20.0        # its ceiling
W = 4.0                # wall thickness
# the roof: solid from the ceiling to the lid
both(-X_EDGE, HALL_TOP, -HALL_Z - W, -X_HALL + W, LID, HALL_Z + W, 'wall')
# the front wall (onto the Approach) with two doors, z -22..-10 and 10..22, 12 high
for (z0, z1) in ((-HALL_Z - W, -22.0), (-10.0, 10.0), (22.0, HALL_Z + W)):
    both(-X_HALL, 0, z0, -X_HALL + W, HALL_TOP, z1, 'wall')
for (z0, z1) in ((-22.0, -10.0), (10.0, 22.0)):
    both(-X_HALL, 12.0, z0, -X_HALL + W, HALL_TOP, z1, 'wall')
# the north and south walls, each with a door x -140..-124 onto the yards
for (z0, z1) in ((-HALL_Z - W, -HALL_Z), (HALL_Z, HALL_Z + W)):
    both(-X_EDGE, 0, z0, -140.0, HALL_TOP, z1, 'wall')
    both(-124.0, 0, z0, -X_HALL + W, HALL_TOP, z1, 'wall')
    both(-140.0, 12.0, z0, -124.0, HALL_TOP, z1, 'wall')
NOTES += [(-132, 0, 0, 'ATT HALL'), (132, 0, 0, 'DEF HALL')]

# ================================================================ the blocks between the lanes (solid to the lid)
# north block z -72..-36 with an alley x -98..-90; south block z 36..70 with an alley x -78..-70 (offset so no line
# runs from the Tube to the Avenue)
N_ALLEY, S_ALLEY = (-98.0, -90.0), (-78.0, -70.0)
both(-X_HALL, 0, -Z_TUBE, N_ALLEY[0], LID, -Z_IN, 'block')
both(N_ALLEY[1], 0, -Z_TUBE, -X_MID, LID, -Z_IN, 'block')
both(-X_HALL, 0, Z_IN, S_ALLEY[0], LID, Z_AVE, 'block')
both(S_ALLEY[1], 0, Z_IN, -X_MID, LID, Z_AVE, 'block')

# ================================================================ the Tube (north lane): covered, z -96..-72, 18 high
TUBE_TOP = 18.0
both(-X_HALL, 0, -Z_EDGE, -X_MID, LID, -Z_OUTN, 'block')          # its north side
both(-X_HALL, TUBE_TOP, -Z_OUTN, -X_MID, LID, -Z_TUBE, 'block')    # its roof
# cover inside: three soft benches, alternating sides
both(-104.0, 0, -Z_OUTN, -97.0, 3.6, -Z_OUTN + 6, 'cover')
both(-87.0, 0, -Z_TUBE - 6, -80.0, 3.6, -Z_TUBE, 'cover')
both(-69.0, 0, -Z_OUTN, -62.0, 3.6, -Z_OUTN + 6, 'cover')
NOTES += [(-84, -84, 0, 'THE TUBE'), (84, -84, 0, 'THE TUBE')]

# ================================================================ the Approach (middle lane) and the Avenue (south lane)
for s in (1, -1):
    round_(s * -84.0, 0.0, 7.0, 0, LID, 'block')                  # the kiosk dome: blocks the line between the halls
    # screens a few steps in front of each hall door: you come out left or right of them, and no line runs from
    # one hall's doors to the other's
    box(s * -100.0, 0, -19.0, s * -95.0, 6.0, -13.0, 'cover')
    box(s * -100.0, 0, 13.0, s * -95.0, 6.0, 19.0, 'cover')
    box(s * -70.0, 0, 22.0, s * -64.0, 3.6, 28.0, 'cover')
    box(s * -70.0, 0, -30.0, s * -62.0, 3.6, -26.0, 'cover')
    # the Avenue: open sky, planters and a low bench
    box(s * -102.0, 0, 78.0, s * -94.0, 3.6, 84.0, 'cover')
    box(s * -84.0, 0, 92.0, s * -76.0, 3.6, 98.0, 'cover')
    box(s * -66.0, 0, 76.0, s * -60.0, 3.6, 86.0, 'cover')
    # the yards by the halls
    round_(s * -131.0, -70.0, 4.5, 0, 3.6, 'cover')
    round_(s * -131.0, 72.0, 4.5, 0, 3.6, 'cover')
NOTES += [(-84, 14, 0, 'APPROACH'), (84, 14, 0, 'APPROACH'), (-84, 87, 0, 'AVENUE'), (84, 87, 0, 'AVENUE')]

# ================================================================ the centre: the Plaza, the courts
round_(0.0, -80.0, 13.0, 0, LID, 'block')        # the north court's dome pavilion
round_(0.0, 87.0, 10.0, 0, LID, 'block')         # the south court's gazebo
for (x, z) in ((-46.0, -46.0), (46.0, -46.0), (-46.0, 46.0), (46.0, 46.0)):
    round_(x, z, 5.0, 0, 3.6, 'cover')            # round planters at the Plaza's corners
# curved benches on the Plaza (one straight box each, turned to face the tower)
for d in (32.0, 148.0, 212.0, 328.0):
    a = math.radians(d)
    ang_box(0, 0, a, 41.0, 43.5, 11.0, 0, 3.2, 'cover')
NOTES += [(0, -98, 0, 'NORTH COURT'), (0, 100, 0, 'SOUTH COURT'), (0, -40, 0, 'PLAZA')]

# ================================================================ the heart tower (gut_heart.py has the look)
import gut_heart_dims as T     # (the tower's numbers, shared with the look)
TOWER = (0.0, 0.0)
STAIR_PHASE = -math.pi / 2       # the stair's foot faces north
LEG0 = 0.0                       # the legs' feet on the axes: (+-31, 0) and (0, +-31)
(r1, h1), (r2, h2) = T.PLINTH
round_(0, 0, r1 * 0.985, 0, h1, 'ivory')
round_(0, 0, r2 * 0.985, h1, h2, 'ivory')
round_(0, 0, 5.1, h2, 40.0, 'ivory', n=2)       # the core, up past the balcony (above it the tower is look only)
for i in range(4):
    a = LEG0 + i * math.pi / 2
    ang_box(0, 0, a, T.LEG_FOOT - 4.5, T.LEG_FOOT + 4.5, 9.0, 0, 4.5, 'ivory')       # the foot pad
    ang_box(0, 0, a, T.LEG_FOOT - 7.5, T.LEG_FOOT - 1.5, 5.4, 4.5, 10.0, 'ivory')   # the leg's low end
# the climbable treads (thick, overlapping), and a rail on their outside that you cannot fall past (takes no shots)
treads = T.walk_treads(STAIR_PHASE)
for k, (a, ty) in enumerate(treads):
    ang_box(0, 0, a, T.STAIR_R0 - 0.2, T.STAIR_R1, 4.6, ty - 2.5, ty, 'tread')
    if k < len(treads) - 3:
        ang_box(0, 0, a, T.STAIR_R1 - 0.6, T.STAIR_R1 + 0.2, 5.0, ty, ty + 3.6, 'rail', 'c')
# the balcony: a ring of 24 boxes, its rail (no shots stopped), the wall round its inside (you cannot step from it onto
# the stair above), and the gate across the stair just over it
for k in range(24):
    a = 2 * math.pi * k / 24
    ang_box(0, 0, a, T.BALC_R0 - 0.3, T.BALC_R1, 5.8, T.BALC_Y - 1.6, T.BALC_Y, 'ivory')
    ang_box(0, 0, a, T.BALC_R1 - 0.9, T.BALC_R1 - 0.1, 5.8, T.BALC_Y, T.BALC_Y + 3.6, 'rail', 'c')
a_arrive0, a_arrive1 = treads[-3][0] - T.STAIR_STEP / 2, treads[-1][0] + T.STAIR_STEP / 2
for k in range(32):
    a = 2 * math.pi * k / 32
    rel = (a - a_arrive0) % (2 * math.pi)
    if rel < (a_arrive1 - a_arrive0) % (2 * math.pi): continue
    ang_box(0, 0, a, T.BALC_R0 - 0.5, T.BALC_R0 - 0.1, 3.4, T.BALC_Y, T.BALC_Y + 20.0, 'rail', 'c')
ga = treads[-1][0] + T.STAIR_STEP / 2
rot(((T.STAIR_R0 + T.STAIR_R1) / 2) * math.cos(ga), T.BALC_Y + 10.0, ((T.STAIR_R0 + T.STAIR_R1) / 2) * math.sin(ga),
    T.STAIR_R1 - T.STAIR_R0 + 0.6, 20.0, 0.8, -math.degrees(ga) + 90.0, 'rail', 'c')
NOTES += [(0, 0, 0, 'HEART TOWER')]

# ================================================================ the subway (y -30): one platform under the south half
X_PLAT = 100.0
Z_PLAT0, Z_PLAT1 = 18.0, 46.0     # the platform; the glass screen at 46..47
Z_TR0, Z_TR1 = 46.0, 70.0         # the track's trench (its middle, z 58, is the train's line)
TRAIN_Z = 58.0
box(-X_PLAT, TRACK, Z_PLAT0, X_PLAT, PLAT, Z_PLAT1, 'tile')                          # the platform
box(-X_PLAT - 4, TRACK - 6, Z_TR0, X_PLAT + 4, TRACK, Z_TR1, 'tile')                 # the trench's floor (out of reach)
box(-X_PLAT - 4, TRACK - 6, Z_PLAT0 - 4, X_PLAT + 4, CEIL, Z_PLAT0, 'tile')         # the north wall
box(-X_PLAT - 4, TRACK - 6, Z_TR1, X_PLAT + 4, CEIL, Z_TR1 + 4, 'tile')             # the wall beyond the track
box(-X_PLAT, PLAT, Z_TR0, X_PLAT, CEIL, Z_TR0 + 1.0, 'glass')                        # the platform screen: full height
for s in (1, -1):
    # the platform's ends, with the end stair's passage through them (z 22..32)
    box(s * -X_PLAT, TRACK, Z_PLAT0, s * -(X_PLAT + 4), CEIL, END_STAIR[2], 'tile')
    box(s * -X_PLAT, TRACK, END_STAIR[3], s * -(X_PLAT + 4), CEIL, Z_TR0, 'tile')
    # the end of the trench: closed past the tunnel mouth (the tunnel itself is look only)
    box(s * -(X_PLAT + 4), TRACK - 6, Z_TR0, s * -(X_PLAT + 8), CEIL, Z_TR1, 'tile')
NOTES += [(0, 32, -1, 'PLATFORM'), (0, 58, -1, 'TRACK (behind glass)')]

def stair(x_top, x_bot, z0, z1, mat='step'):
    """30 steps from the platform (y -30) up to the street (y 0); x_top/x_bot are signed. rails on both sides (no shots)"""
    sgn = 1.0 if x_top > x_bot else -1.0      # +1: going up toward +x
    n = int(round((0.0 - PLAT) / STEP))
    for k in range(1, n + 1):
        xa = x_bot + sgn * (k - 1) * RUN
        xb = x_bot + sgn * k * RUN
        top = PLAT + k * STEP
        box(xa, TRACK, z0, xb, top, z1, mat)
        if top > PLAT + 3.0:
            for (za, zb) in ((z0, z0 + 0.5), (z1 - 0.5, z1)):
                rot((xa + xb) / 2, top + 1.8, (za + zb) / 2, abs(xb - xa), 3.6, zb - za, 0.0, 'rail', 'c')
for s in (1, -1):
    stair(s * -MID_STAIR[0], s * -MID_STAIR[1], MID_STAIR[2], MID_STAIR[3])
    stair(s * -END_STAIR[0], s * -END_STAIR[1], END_STAIR[2], END_STAIR[3])
    # the end stair's passage: walls both sides from the trench's depth up to the slab
    box(s * -X_PLAT, TRACK, END_STAIR[2] - 2.0, s * -END_STAIR[0], CEIL, END_STAIR[2], 'tile')
    box(s * -X_PLAT, TRACK, END_STAIR[3], s * -END_STAIR[0], CEIL, END_STAIR[3] + 2.0, 'tile')
    box(s * -END_STAIR[0], TRACK, END_STAIR[2] - 2.0, s * -(END_STAIR[0] + 2.0), CEIL, END_STAIR[3] + 2.0, 'tile')
# rails round the street openings (open at the stair's top end), no shots stopped
def rails(x0, z0, x1, z1, open_x):
    for (za, zb) in ((z0 - 0.5, z0), (z1, z1 + 0.5)):
        rot((x0 + x1) / 2, 1.8, (za + zb) / 2, x1 - x0, 3.6, 0.5, 0.0, 'rail', 'c')
    xe = x1 if open_x == x0 else x0          # the closed end
    rot(xe + (0.25 if xe == x1 else -0.25), 1.8, (z0 + z1) / 2, 0.5, 3.6, z1 - z0 + 1.0, 0.0, 'rail', 'c')
for h in OPENINGS:
    x0, z0, x1, z1 = h
    # the stair's top end is the side nearer its top x
    tops = (MID_STAIR[0], -MID_STAIR[0], END_STAIR[0], -END_STAIR[0])
    open_x = x0 if min(abs(x0 - t) for t in tops) < min(abs(x1 - t) for t in tops) else x1
    rails(x0, z0, x1, z1, open_x)
# cover on the platform: round columns, a booth in the middle, low benches by the glass
for x in (-80.0, -45.0, -12.0, 12.0, 45.0, 80.0):
    round_(x, 21.0, 1.9, PLAT, CEIL, 'tile', n=2)
for x in (-92.0, -70.0, -30.0, 30.0, 70.0, 92.0):
    round_(x, 40.0, 1.9, PLAT, CEIL, 'tile', n=2)
box(-6.0, PLAT, 26.0, 6.0, PLAT + 8.0, 34.0, 'wall')
for x in (-55.0, -18.0, 18.0, 55.0):
    box(x - 4.0, PLAT, 42.5, x + 4.0, PLAT + 1.6, 44.5, 'cover')

# ================================================================ spawns
# free-for-all: spread round the map, every one on a floor
for (x, y, z) in ((-140, 0, -20), (-128, 0, -84), (-128, 0, 88), (-84, 0, -84), (-100, 0, 8), (-84, 0, 88),
                  (-36, 0, -90), (-36, 0, 70), (-85, PLAT, 40), (-40, PLAT, 21)):
    SPAWNS.append((x, y + 0.3, z)); SPAWNS.append((-x, y + 0.3, -z if y == 0 and abs(z) > 60 else z))
# teams: attackers in the west hall facing east, defenders mirrored; a third side (1v1v1) in the courts
for (x, z) in ((-144, -30), (-144, -16), (-144, -2), (-144, 6), (-132, -24), (-132, -8), (-132, 8), (-132, 36)):
    TEAM['att'].append((x, 0.3, z, 1.0, 0.0))
    TEAM['def'].append((-x, 0.3, z, -1.0, 0.0))
TEAM['mid'] = [(-26, 0.3, -98, 0.0, 1.0), (26, 0.3, -98, 0.0, 1.0), (-26, 0.3, 98, 0.0, -1.0), (26, 0.3, 98, 0.0, -1.0)]
