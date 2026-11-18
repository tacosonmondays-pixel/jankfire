# STATION (18 Nov 2026): a new medium arena. The owner asked for "more map variety create our maps based off popular cod
# maps"; the rule is we never recreate another game's map, so this takes only the principles of classic medium
# shooter maps: three lanes, readable sightlines, power positions with counters, flank routes, cover rhythm, a few
# seconds from spawn to the first fight. The place is ours: a small-town terminus at golden hour, a train waiting.
#
#   the middle lane: two platforms either side of one track, a parked three-carriage train between them. You go
#     THROUGH the carriages (two doors a side each, never facing each other: no straight line across), across the
#     plank crossings between carriages, or drop into the track bed. Canopies on posts over the platforms; their flat
#     tops are a raised lane you can stand on, reached from the waiting rooms' upper floors.
#   the waiting rooms (one per side, the teams' bases): two floors; the ground floor opens onto the forecourt and the
#     platform, the upper floor's offices look over the train and step out onto the canopy roof.
#   the north lane: the station hall (the concourse, a terminus: the track ends at buffer stops under its south
#     windows). Indoor and close: ticket barriers, a kiosk, columns; a gallery along its south wall over the platforms.
#   the footbridge: a covered bridge high over the platforms and the train (the power position), up long stairs from
#     each forecourt; countered by the waiting rooms' upper windows, the hall's gallery, the canopy roofs and the
#     train's roof below it.
#   the south lane: the goods yard: a goods shed you go through each side, crates and pallets, a loading dock, the open
#     track bed (a low route), a plank crossing, a gantry crane overhead.
# Mirror-symmetric across x = 0. Studs, local to the arena's origin; platform and street level y = 0.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from maplayout import *
import maplayout as _M

T = 1.2
X_EDGE, Z_EDGE = 150.0, 100.0
TRENCH = (7.0, -4.0)            # half width, floor y of the track bed
CAR_X, CAR_FLOOR, CAR_TOP = 5.0, 0.6, 11.0
CARS = [(-66.0, -28.0), (-22.0, 16.0), (22.0, 60.0)]     # the carriages' z spans (gaps between them: plank crossings)
HALL = (-100.0, -72.0)          # the station hall's z span (north end)
UPF = 12.0                      # the waiting rooms' upper floor
CANOPY = 13.0
FB_Y, FB_Z = 20.0, (-46.0, -40.0)   # the footbridge: deck height, z span

MATS = {
    'paving': ('Slate', 'b5b0a6', 'paving'),
    'platform': ('Concrete', 'bdb8ad', 'concrete'),
    'ballast': ('Pebble', '8c8a85', 'gravel'),
    'brick': ('Brick', 'a8806a', 'brick'),
    'plaster': ('SmoothPlastic', 'd9d2c4', 'plaster'),
    'floor': ('WoodPlanks', 'b6987a', 'wood'),
    'step': ('Concrete', 'b2ada2', 'concrete'),
    'roof': ('Slate', '6f7276', 'roof'),
    'canopy': ('Metal', '8c9297', 'metal'),
    'iron': ('Metal', '6f777d', 'metal'),
    'train': ('Metal', '5f7a6c', 'metal'),
    'trainin': ('SmoothPlastic', 'cfc8b8', 'plaster'),
    'seat': ('Fabric', '7d7a74', 'furniture'),
    'wood': ('WoodPlanks', 'a5835f', 'wood'),
    'crate': ('WoodPlanks', 'b09470', 'wood'),
    'cover': ('SmoothPlastic', 'b9b4aa', 'cover'),
    'planter': ('Concrete', 'a9a49a', 'stone'),
    'tree': ('Wood', '75604b', 'wood'),
    'rail': ('Metal', '6f777d', 'metal'),
    'ledge': ('SmoothPlastic', 'c8c4bd', 'ledge'),
    'bound': ('SmoothPlastic', 'c8c4bd', 'bound'),
}

hx, ty = TRENCH
# ================================================================ the ground: street/platform level, the track bed cut out
slab(-X_EDGE, -Z_EDGE, X_EDGE, Z_EDGE, -6.0, 0.0, 'paving', holes=[(-hx, HALL[1], hx, Z_EDGE)])
box(-hx, ty - 1.0, HALL[1], hx, ty, Z_EDGE, 'ballast')
box(-hx, ty, HALL[1] - 1.0, hx, 2.4, HALL[1], 'iron')      # buffer stops at the end of the track (under the hall's windows)
tag('trench', (-hx, ty, HALL[1], hx, 0.0, Z_EDGE))

# ================================================================ the train: three carriages, doors offset side to side
for ci, (z0, z1) in enumerate(CARS):
    box(-CAR_X, ty, z0, CAR_X, CAR_FLOOR, z1, 'train')                                   # underframe, floor
    box(-CAR_X, CAR_TOP - 1.4, z0, CAR_X, CAR_TOP, z1, 'train')                          # roof (you can stand on it)
    for (zz0, zz1) in ((z0, z0 + T), (z1 - T, z1)):                                       # end walls
        box(-CAR_X, CAR_FLOOR, zz0, CAR_X, CAR_TOP - 1.4, zz1, 'train')
    L = z1 - z0
    for side, offs in ((-1, (6.0, 24.0)), (1, (13.0, 30.0))):                            # doors: never facing each other
        holes = [(z0 + o, z0 + o + 4.0, CAR_FLOOR, CAR_FLOOR + 8.0, 'door') for o in offs]
        # windows between the doors (you can shoot through, not climb through: y 4.2 to 7.4)
        wins = []
        a = z0 + T
        for (d0, d1) in sorted((h[0], h[1]) for h in holes) + [(z1 - T, z1 - T)]:
            if d0 - a > 6.0: wins.append((a + 1.2, d0 - 1.2, 4.2, 7.4, 'window'))
            a = d1
        xa, xb = (-CAR_X, -CAR_X + 0.6) if side < 0 else (CAR_X - 0.6, CAR_X)
        wall('z', xa, xb, z0 + T, z1 - T, CAR_FLOOR, CAR_TOP - 1.4, holes + wins, 'train')
    # seats inside: bays along both walls between that side's doors (never in front of one), an aisle down the middle
    for side, bays in ((-1, ((1.6, 5.2), (11.0, 23.0), (29.0, 36.4))), (1, ((1.6, 12.0), (18.0, 29.0)))):
        x0_, x1_ = (-CAR_X + 0.6, -1.6) if side < 0 else (1.6, CAR_X - 0.6)
        for (a, b) in bays:
            box(x0_, CAR_FLOOR, z0 + a, x1_, CAR_FLOOR + 2.4, z0 + b, 'seat')
    tag('car', (-CAR_X, ty, z0, CAR_X, CAR_TOP, z1), ci)
# plank crossings between the carriages and past the train's ends, at platform level
for (a, b) in ((CARS[0][1] + 1.0, CARS[1][0] - 1.0), (CARS[1][1] + 1.0, CARS[2][0] - 1.0), (CARS[2][1] + 6.0, CARS[2][1] + 10.0), (HALL[1] + 1.5, CARS[0][0] - 1.5)):
    box(-hx, -0.6, a, hx, 0.0, b, 'wood')
    tag('crossing', (-hx, -0.6, a, hx, 0.0, b))

with Mirror():
    # ============================================================ the west platform's canopy: posts, a flat top to stand on
    for z in range(-64, 66, 16):
        box(-25.0, 0.0, z - 0.5, -24.0, CANOPY - 1.0, z + 0.5, 'iron')
    box(-32.0, CANOPY - 1.0, -70.0, -9.0, CANOPY, 64.0, 'canopy')        # (from the waiting room's wall: its upper door steps out onto it)
    tag('canopy', (-32.0, CANOPY - 1.0, -70.0, -9.0, CANOPY, 64.0))
    # platform furniture: benches, a lamp-post line, a parcels trolley
    for z in (-52.0, -8.0, 38.0):
        box(-23.0, 0.0, z, -21.0, 2.0, z + 6.0, 'wood')
    box(-16.0, 0.0, 26.0, -12.0, 3.6, 32.0, 'crate')
    box(-17.0, 0.0, -34.0, -13.0, 3.0, -30.0, 'cover')
    # ============================================================ the waiting room (the team's base): two floors
    wx0, wx1, wz0, wz1 = -62.0, -32.0, -24.0, 24.0
    tag('waiting', (wx0, 0.0, wz0, wx1, 24.0, wz1), 'x+')
    wall('z', wx1 - T, wx1, wz0, wz1, 0.0, UPF, [(-16.0, -10.0, 0.0, 9.0, 'door'), (8.0, 14.0, 0.0, 9.0, 'door')], 'brick')
    wall('z', wx1 - T, wx1, wz0, wz1, UPF, 24.0, [(-20.0, -14.0, UPF + 2.5, UPF + 8.0, 'window'), (-4.0, 2.0, UPF + 2.5, UPF + 8.0, 'window'),
                                                   (14.0, 18.0, UPF + 1.0, UPF + 9.0, 'door')], 'brick')   # the door onto the canopy top
    wall('z', wx0, wx0 + T, wz0, wz1, 0.0, UPF, [(-12.0, -6.0, 0.0, 9.0, 'door'), (12.0, 18.0, 0.0, 9.0, 'door')], 'brick')
    wall('z', wx0, wx0 + T, wz0, wz1, UPF, 24.0, [(-6.0, 0.0, UPF + 2.5, UPF + 8.0, 'window')], 'brick')
    wall('x', wz1 - T, wz1, wx0 + T, wx1 - T, 0.0, 24.0, [(-54.0, -48.0, 0.0, 9.0, 'door'), (-44.0, -38.0, UPF + 2.5, UPF + 8.0, 'window')], 'brick')
    wall('x', wz0, wz0 + T, wx0 + T, wx1 - T, 0.0, 24.0, [(-54.0, -48.0, 0.0, 9.0, 'door'), (-44.0, -38.0, UPF + 2.5, UPF + 8.0, 'window')], 'brick')
    # the stair up the north wall inside, rising east; the upper floor with its stairwell; a flat roof with a parapet
    s0, s1 = wz0 + T, wz0 + T + 4.0
    xe = stair(s0, s1, wx0 + T + 3.0, 1, int(UPF), axis='x')
    hole = (wx0 + T + 3.0 + 4 * RUN, s0, xe, s1)
    slab(wx0, wz0, wx1, wz1, UPF - 0.8, UPF, 'floor', holes=[hole])
    rot((hole[0] + hole[2]) / 2, UPF + 1.8, s1 + 0.2, hole[2] - hole[0], 3.6, 0.4, 0.0, 'rail', 'c')
    rot(hole[0] - 0.2, UPF + 1.8, (s0 + s1) / 2, 0.4, 3.6, s1 - s0, 0.0, 'rail', 'c')
    box(wx0, 24.0, wz0, wx1, 25.0, wz1, 'roof')
    for (a, b, c, d) in ((wx0, wz0, wx1, wz0 + 0.8), (wx0, wz1 - 0.8, wx1, wz1), (wx0, wz0, wx0 + 0.8, wz1), (wx1 - 0.8, wz0, wx1, wz1)):
        box(a, 25.0, b, c, 27.4, d, 'brick')
    # inside: the ticket counter, benches (ground); desks (upstairs)
    box(-50.0, 0.0, 6.0, -48.0, 3.6, 18.0, 'wood')
    box(-44.0, 0.0, -10.0, -40.0, 2.0, -2.0, 'wood'); box(-56.0, 0.0, -2.0, -52.0, 2.0, 6.0, 'wood')
    box(-52.0, UPF, 4.0, -46.0, UPF + 2.6, 8.0, 'wood'); box(-42.0, UPF, -16.0, -36.0, UPF + 2.6, -12.0, 'wood')
    # ============================================================ the forecourt (west): planters and trees, a shelter, benches
    for (x, z) in ((-90.0, -30.0), (-90.0, 30.0), (-110.0, 0.0)):
        box(x - 3.0, 0.0, z - 3.0, x + 3.0, 2.4, z + 3.0, 'planter'); box(x - 0.8, 2.4, z - 0.8, x + 0.8, 26.0, z + 0.8, 'tree')
    box(-80.0, 0.0, 6.0, -72.0, 9.0, 7.2, 'cover'); box(-80.0, 9.0, 4.0, -72.0, 9.8, 12.0, 'roof')   # a shelter: back wall, roof
    box(-78.0, 0.0, 9.0, -74.0, 1.8, 11.0, 'wood')
    box(-84.0, 0.0, -16.0, -80.0, 4.0, -8.0, 'cover')                                                # a kiosk
    # ============================================================ the footbridge stair (west), up along x to the deck
    fz0, fz1 = FB_Z
    xs = stair(fz0, fz1, -72.0, 1, int(FB_Y), axis='x', run=1.4)
    for k in range(5):   # its side walls: a parapet 3.2 over the steps, in five lengths that climb with them
        xa, xb = -72.0 + k * 4 * RUN, -72.0 + (k + 1) * 4 * RUN
        box(xa, 0.0, fz0 - 1.0, xb, (k + 1) * 4 + 3.2, fz0, 'iron'); box(xa, 0.0, fz1, xb, (k + 1) * 4 + 3.2, fz1 + 1.0, 'iron')
    tag('fbstair', (-72.0, 0.0, fz0 - 1.0, xs, FB_Y + 3.2, fz1 + 1.0))
    for (x, z) in ((-100.0, -46.0), (-100.0, 46.0), (-76.0, -30.0), (-76.0, 30.0), (-122.0, -28.0), (-122.0, 28.0)):
        box(x - 0.4, 0.0, z - 0.4, x + 0.4, 12.0, z + 0.4, 'iron')            # lamp posts on the forecourt
        tag('lamppost', (x, 12.0, z))
    # ============================================================ the goods yard (south-west): a goods shed you go through, crates, a dock
    gx0, gx1, gz0, gz1 = -64.0, -34.0, 70.0, 96.0
    tag('shed', (gx0, 0.0, gz0, gx1, 16.0, gz1), 'x+')
    wall('z', gx1 - T, gx1, gz0, gz1, 0.0, 16.0, [(76.0, 84.0, 0.0, 10.0, 'door')], 'brick')
    wall('z', gx0, gx0 + T, gz0, gz1, 0.0, 16.0, [(80.0, 88.0, 0.0, 10.0, 'door')], 'brick')
    wall('x', gz0, gz0 + T, gx0 + T, gx1 - T, 0.0, 16.0, [(-52.0, -44.0, 0.0, 10.0, 'door')], 'brick')
    wall('x', gz1 - T, gz1, gx0 + T, gx1 - T, 0.0, 16.0, [], 'brick')
    box(gx0, 16.0, gz0, gx1, 17.0, gz1, 'roof')
    box(-58.0, 0.0, 86.0, -52.0, 4.0, 92.0, 'crate'); box(-42.0, 0.0, 74.0, -38.0, 3.0, 78.0, 'crate')
    box(-30.0, 0.0, 64.0, -10.0, 4.0, 72.0, 'platform')                                              # the loading dock (up 4)
    stair(-30.0, -24.0, 76.0, -1, 4, axis='z')                                                       # its steps
    for (x0, z0, x1, z1, h) in ((-26.0, 44.0, -20.0, 50.0, 4.0), (-24.0, 50.0, -20.0, 53.0, 2.4), (-72.0, 50.0, -66.0, 58.0, 5.0), (-84.0, 66.0, -78.0, 72.0, 4.0)):
        box(x0, 0.0, z0, x1, h, z1, 'crate')
    box(-30.0, 0.0, 84.0, -27.0, 18.0, 88.0, 'iron')                                                 # the gantry's leg
    # track-bed steps out at the south end (a low route back up onto the platforms): against the bed's side wall, rising
    # north to platform level, the middle of the bed left clear
    stair(-hx, -hx + 4.0, 96.0, -1, 4, y0=ty, axis='z')

# ================================================================ the station hall (north): the concourse, its gallery
hz0, hz1 = HALL
tag('hall', (-70.0, 0.0, hz0, 70.0, 32.0, hz1))
wall('x', hz0, hz0 + T, -70.0, 70.0, 0.0, 30.0, [], 'brick')
wall('x', hz1 - T, hz1, -70.0, 70.0, 0.0, 30.0,
     [(-30.0, -9.0, 0.0, 10.0, 'arch'), (9.0, 30.0, 0.0, 10.0, 'arch'), (-6.0, 6.0, 0.0, 6.0, 'arch'),
      (-50.0, -34.0, 15.0, 25.0, 'window'), (-24.0, -8.0, 15.0, 25.0, 'window'), (8.0, 24.0, 15.0, 25.0, 'window'), (34.0, 50.0, 15.0, 25.0, 'window')], 'brick')
for s in (-1, 1):
    wall('z', s * 70.0 - (T if s > 0 else 0.0), s * 70.0 + (0.0 if s > 0 else T), hz0 + T, hz1 - T, 0.0, 30.0,
         [(-94.0, -88.0, 0.0, 9.0, 'door'), (-84.0, -78.0, 0.0, 9.0, 'door')], 'brick')
box(-70.0, 30.0, hz0, 70.0, 32.0, hz1, 'roof')                                       # a flat roof (walkable)
box(-40.0, 32.0, -90.0, 40.0, 35.5, -82.0, 'roof')                                   # its glazed lantern (cover up there)
tag('lantern', (-40.0, 32.0, -90.0, 40.0, 35.5, -82.0))
# the gallery along the south wall at 12, stairs up at both ends, a rail along its edge
GX = 68.6 - (int(UPF) - 1) * RUN       # the gallery's ends: where its stairs (up from the hall's side walls) arrive, never over them
box(-GX, UPF - 0.8, hz1 - T - 7.0, GX, UPF, hz1 - T, 'floor')
rot(0.0, UPF + 1.8, hz1 - T - 7.2, 2 * GX, 3.6, 0.4, 0.0, 'rail', 'c')
for s in (-1, 1):
    stair(hz1 - T - 7.0, hz1 - T - 3.0, s * 68.6, -s, int(UPF) - 1, axis='x')
# the concourse: columns, ticket barrier rows, a kiosk in the middle, benches
for x in (-48.0, -24.0, 24.0, 48.0):
    for z in (-92.0, -82.0):
        box(x - 1.0, 0.0, z - 1.0, x + 1.0, 30.0, z + 1.0, 'brick')
for x0 in (-40.0, 20.0):
    for k in range(4):
        box(x0 + k * 5.0, 0.0, -86.0, x0 + k * 5.0 + 1.0, 3.4, -84.0, 'iron')
box(-6.0, 0.0, -92.0, 6.0, 9.0, -84.0, 'wood')                                         # the kiosk
box(-60.0, 0.0, -96.0, -54.0, 2.0, -93.0, 'wood'); box(54.0, 0.0, -96.0, 60.0, 2.0, -93.0, 'wood')
# ================================================================ the footbridge deck over everything
fz0, fz1 = FB_Z
box(-44.0, FB_Y - 1.0, fz0, 44.0, FB_Y, fz1, 'floor')
for (z0, z1) in ((fz0 - 1.0, fz0), (fz1, fz1 + 1.0)):
    wall('x', z0, z1, -44.0, 44.0, FB_Y, FB_Y + 7.0, [(-36.0, -20.0, FB_Y + 2.6, FB_Y + 6.0, 'window'), (-12.0, 12.0, FB_Y + 2.6, FB_Y + 6.0, 'window'),
                                                     (20.0, 36.0, FB_Y + 2.6, FB_Y + 6.0, 'window')], 'iron')
box(-44.0, FB_Y + 7.0, fz0 - 1.0, 44.0, FB_Y + 8.0, fz1 + 1.0, 'roof')
for x in (-18.0, 18.0):   # its piers on the platforms
    box(x - 1.0, 0.0, fz0 + 1.5, x + 1.0, FB_Y - 1.0, fz1 - 1.5, 'iron')
tag('footbridge', (-44.0, FB_Y - 1.0, fz0, 44.0, FB_Y + 8.0, fz1))
# the gantry crane over the goods yard tracks: a beam you can stand on
box(-30.0, 18.0, 84.0, 30.0, 20.0, 88.0, 'iron')

# ================================================================ spawns
for (x, z) in ((-136.0, -18.0), (-136.0, -6.0), (-136.0, 6.0), (-136.0, 18.0), (-128.0, -12.0), (-128.0, 12.0), (-142.0, 0.0), (-128.0, 0.0)):
    TEAM['att'].append((x, 0.3, z, 1.0, 0.0))
    TEAM['def'].append((-x, 0.3, z, -1.0, 0.0))
TEAM['mid'] = [(-30.0, 0.3, -94.0, 0.0, 1.0), (30.0, 0.3, -94.0, 0.0, 1.0), (-10.0, 0.3, 94.0, 0.0, -1.0), (10.0, 0.3, 94.0, 0.0, -1.0)]
for (x, y, z) in ((-47.0, 0.0, -14.0), (-40.0, UPF, 2.0), (-20.0, 0.0, -20.0), (-20.0, CANOPY, 0.0), (-1.0, CAR_FLOOR, 10.0), (-28.0, FB_Y, -43.0),
                  (-90.0, 0.0, -10.0), (-100.0, 0.0, 40.0), (-50.0, 0.0, 80.0), (-20.0, 4.0, 68.0), (-40.0, 0.0, -88.0), (-40.0, UPF, -77.0), (-2.0, ty, 80.0)):
    SPAWNS.append((x, y + 0.3, z)); SPAWNS.append((-x, y + 0.3, z))
NOTES.extend([(-47.0, 0.0, 0, 'WAITING ROOM'), (47.0, 0.0, 0, 'WAITING ROOM'), (0.0, -2.0, 0, 'TRAIN'), (-20.0, 40.0, 0, 'PLATFORM'),
              (0.0, -86.0, 0, 'STATION HALL'), (-49.0, 83.0, 0, 'GOODS SHED'), (-20.0, 68.0, 0, 'DOCK'), (-135.0, 0.0, 0, 'ATT'), (135.0, 0.0, 0, 'DEF'),
              (-60.0, -43.0, 0, 'FOOTBRIDGE STAIR'),
              (0.0, -43.0, 1, 'FOOTBRIDGE (20)'), (-20.0, 20.0, 1, 'CANOPY TOP (13)'), (-47.0, 8.0, 1, 'UPSTAIRS (12)'), (0.0, -77.0, 1, 'HALL GALLERY (12)'),
              (0.0, 40.0, 1, 'TRAIN ROOF (11)'), (0.0, 86.0, 1, 'GANTRY (20)')])

TITLE = 'STATION (new, medium)'
BOUNDS = (-190.0, 190.0, -140.0, 140.0)
LEVELS = [('STREETS, PLATFORMS, INSIDE THE TRAIN (y 0; the track bed at -4)', -5.0, 8.0, 0.0),
          ('UPSTAIRS, CANOPY TOPS, TRAIN ROOF, GALLERY (y 11 to 13)', 8.5, 17.0, 12.0),
          ('FOOTBRIDGE, GANTRY, ROOFS (y 18 and up)', 17.5, 40.0, 20.0)]
FLOORS = ('paving', 'platform', 'ballast', 'floor', 'step', 'canopy', 'wood', 'roof')
COLOURS = {'paving': (200, 196, 186), 'platform': (210, 204, 190), 'ballast': (140, 138, 133), 'brick': (150, 88, 98), 'plaster': (150, 88, 98),
           'floor': (200, 170, 130), 'step': (205, 186, 172), 'roof': (226, 190, 160), 'canopy': (180, 186, 192), 'iron': (120, 128, 134),
           'train': (95, 122, 108), 'trainin': (200, 196, 184), 'seat': (226, 160, 152), 'wood': (176, 132, 96), 'crate': (190, 150, 110),
           'cover': (226, 160, 152), 'planter': (150, 140, 120), 'tree': (90, 120, 70)}
PLAN_NOTE = ('three lanes: north the station hall (indoor, its gallery over the platforms), middle the platforms and the train you go '
             'through (doors offset side to side), south the goods yard (sheds, crates, the open track bed); the footbridge over the middle '
             'is the power spot, countered by the upstairs windows, the gallery, the canopy tops and the train roof')

import wallbox
HIT_SOLID, HIT_ROT, WALLBOX = wallbox.rect(SOLID, ROT, X_EDGE, Z_EDGE, -6.0, 30.0, 18.0, drop=lambda b: False)
blocked, floor_under, inside, pad_flight = _M.blocked, _M.floor_under, _M.inside, _M.pad_flight

if __name__ == '__main__':
    report()
