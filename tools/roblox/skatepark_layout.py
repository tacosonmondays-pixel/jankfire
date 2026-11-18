# SKATEPARK (18 Nov 2026): a new small, fast arena. The owner asked for "more map variety create our maps based off
# popular cod maps"; the rule is we never recreate another game's map, so this takes only the principles of classic
# small shooter maps: two facing bases with a contested middle, short lanes, spawn-to-fight in a few seconds, every
# power position with counters. Everything else is ours: a city skatepark at dusk under floodlights.
#
#   W and E: a clubhouse each (the teams' bases): a skate shop on the ground floor (front door onto the park, side doors
#     onto both lanes, a back door from the spawn yard), a roof deck behind a parapet over the park, up an inside stair
#     or a springboard by its north wall. The teams spawn in the yard behind it.
#   the middle: a sunken bowl (6 deep, stepped walls the kit draws as smooth transitions) with a bridge across it north
#     to south (deck at 2, low walls: the line between the clubhouses' front doors is broken), its piers in the bowl
#   north lane: ledges, a quarter-pipe each end with a deck on top (a flank perch), a bus-stop style shelter in the middle
#     whose flat roof you can stand on, planters with trees
#   south lane: the bleachers (five rows up to 9: a perch over the bowl, open to the bridge, the shelter roof and both
#     clubhouse roofs), snack kiosks, a low manual pad
# Mirror-symmetric across x = 0 (Matches swaps ends every round anyway). Street level y = 0, studs, local to the origin.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from maplayout import *
import maplayout as _M

T = 1.2
X_EDGE, Z_EDGE = 108.0, 70.0     # the old edge: the wall box's step starts here (wallbox.py pushes the walls 30 out)
ROOF = 12.0                      # the clubhouses' roof deck
BOWL = (32.0, 22.0, 6.0)         # half x, half z, depth
BRIDGE_Y = 2.0

MATS = {
    'concrete': ('Concrete', 'b9b8b4', 'concrete'),
    'bowl': ('Concrete', 'aeb0b0', 'concrete'),
    'club': ('SmoothPlastic', 'c9c4ba', 'plaster'),
    'roof': ('Concrete', 'a6a7a8', 'concrete'),
    'step': ('Concrete', 'b2b1ad', 'concrete'),
    'wood': ('WoodPlanks', 'a5835f', 'wood'),
    'metal': ('Metal', '9aa0a6', 'metal'),
    'rail': ('Metal', '8f969c', 'metal'),
    'planter': ('Concrete', 'a9a49a', 'stone'),
    'tree': ('Wood', '75604b', 'wood'),
    'cover': ('SmoothPlastic', 'b4b6b8', 'cover'),
    'kiosk': ('SmoothPlastic', 'c2bdb2', 'plaster'),
    'ledge': ('SmoothPlastic', 'c8c4bd', 'ledge'),   # the wall box's step (wallbox.py)
    'bound': ('SmoothPlastic', 'c8c4bd', 'bound'),   # its walls
}

# ================================================================ the ground: one slab, the bowl cut out of it
bx, bz, bd = BOWL
slab(-X_EDGE, -Z_EDGE, X_EDGE, Z_EDGE, -6.0, 0.0, 'concrete', holes=[(-bx, -bz, bx, bz)])
box(-bx, -bd - 1.0, -bz, bx, -bd, bz, 'bowl')                          # the bowl's floor
RUNB = 0.75
for k in range(int(bd) - 1):                                           # its stepped walls: rings 1 deep each
    a, b = k * RUNB, (k + 1) * RUNB
    top = -(k + 1)
    for (x0, z0, x1, z1) in ((-bx + a, -bz + a, bx - a, -bz + b), (-bx + a, bz - b, bx - a, bz - a),
                             (-bx + a, -bz + b, -bx + b, bz - b), (bx - b, -bz + b, bx - a, bz - b)):
        box(x0, -bd, z0, x1, top, z1, 'bowl')
tag('bowl', (-bx, -bd, -bz, bx, 0.0, bz), RUNB)
# the bridge across the bowl, north to south, its low walls with a gap in the middle of each, two piers
box(-4.0, BRIDGE_Y - 1.0, -bz - 3.0, 4.0, BRIDGE_Y, bz + 3.0, 'concrete')
for s in (-1, 1):
    box(-4.0, 0.0, min(s * bz, s * (bz + 3.0)), 4.0, BRIDGE_Y - 1.0, max(s * bz, s * (bz + 3.0)), 'concrete')   # its ends on the plaza
    for (z0, z1) in ((-bz - 3.0, -14.0), (-10.0, 10.0), (14.0, bz + 3.0)):                                  # its low walls, two gaps
        box(s * 4.0 - (0.8 if s > 0 else 0.0), BRIDGE_Y, z0, s * 4.0 + (0.0 if s > 0 else 0.8), BRIDGE_Y + 3.2, z1, 'concrete')
    box(-3.0, -bd, min(s * 6.0, s * 9.0), 3.0, BRIDGE_Y - 1.0, max(s * 6.0, s * 9.0), 'concrete')                # a pier
# ramps up onto the bridge from the lanes (2 steps each end)
for s in (-1, 1):
    zs = s * (bz + 3.0)
    stair(-4.0, 4.0, zs + s * 2.8, -s, 2, run=1.4, m='step')
tag('bridge', (-4.0, BRIDGE_Y - 1.0, -bz - 3.0, 4.0, BRIDGE_Y, bz + 3.0))

with Mirror():
    # ============================================================ the west clubhouse (attackers' base)
    cx0, cx1, cz0, cz1 = -96.0, -66.0, -22.0, 22.0
    tag('club', (cx0, 0.0, cz0, cx1, ROOF, cz1), 'x+')
    wall('z', cx1 - T, cx1, cz0, cz1, 0.0, ROOF - 1.0, [(-3.0, 3.0, 0.0, 9.0, 'door'), (-17.0, -11.0, 3.5, 8.0, 'window'), (11.0, 17.0, 3.5, 8.0, 'window')], 'club')
    wall('z', cx0, cx0 + T, cz0, cz1, 0.0, ROOF - 1.0, [(7.0, 13.0, 0.0, 9.0, 'door')], 'club')    # (off the front door's line)
    wall('x', cz1 - T, cz1, cx0 + T, cx1 - T, 0.0, ROOF - 1.0, [(-84.0, -78.0, 0.0, 9.0, 'door'), (-75.0, -70.0, 3.5, 8.0, 'window')], 'club')
    wall('x', cz0, cz0 + T, cx0 + T, cx1 - T, 0.0, ROOF - 1.0, [(-94.0, -89.0, 0.0, 9.0, 'door'), (-75.0, -70.0, 3.5, 8.0, 'window')], 'club')
    # the inside stair up the south wall, rising west; the roof cut over its top steps
    sz0, sz1 = cz0 + T, cz0 + T + 4.0
    xe = stair(sz0, sz1, cx1 - T - 1.6, -1, int(ROOF), axis='x', m='step')
    hole = (xe, sz0, cx1 - T - 1.6 - 5 * RUN, sz1)
    slab(cx0, cz0, cx1, cz1, ROOF - 1.0, ROOF, 'roof', holes=[hole])
    rot((hole[0] + hole[2]) / 2, ROOF + 1.8, sz1 + 0.2, hole[2] - hole[0], 3.6, 0.4, 0.0, 'rail', 'c')
    rot(hole[2] + 0.2, ROOF + 1.8, (sz0 + sz1) / 2, 0.4, 3.6, sz1 - sz0, 0.0, 'rail', 'c')
    # the roof deck: a parapet on the park side (lower in its middle, to peek over crouched), rails on the others
    box(cx1 - T, ROOF, cz0, cx1, ROOF + 3.2, -4.0, 'club'); box(cx1 - T, ROOF, 4.0, cx1, ROOF + 3.2, cz1, 'club')
    box(cx1 - T, ROOF, -4.0, cx1, ROOF + 1.6, 4.0, 'club')
    rot((cx0 + cx1) / 2, ROOF + 1.8, cz1 - 0.2, cx1 - cx0 - T, 3.6, 0.4, 0.0, 'rail', 'c')
    rot((cx0 + cx1) / 2, ROOF + 1.8, cz0 + 0.2, cx1 - cx0 - T, 3.6, 0.4, 0.0, 'rail', 'c')
    rot(cx0 + 0.2, ROOF + 1.8, 0.0, 0.4, 3.6, cz1 - cz0, 0.0, 'rail', 'c')
    # inside: the shop counter, racks (cover)
    box(-88.0, 0.0, -11.0, -76.0, 3.4, -9.0, 'wood')
    box(-92.0, 0.0, 6.0, -90.0, 6.0, 16.0, 'wood')
    box(-80.0, 0.0, 12.0, -72.0, 2.6, 15.0, 'cover')
    # the springboard by the north wall onto the roof deck
    PADS.append((-88.0, 0.0, 24.0, -84.0, 0.9, 28.0, 0.0, 52.0, -9.0))
    # ============================================================ the plaza between the clubhouse and the bowl: cover rhythm
    box(-56.0, 0.0, -17.0, -50.0, 1.8, -11.0, 'cover')                 # funboxes (low cover, jump on them)
    box(-56.0, 0.0, 11.0, -50.0, 1.8, 17.0, 'cover')
    box(-44.0, 0.0, -3.0, -41.0, 3.6, 3.0, 'cover')                    # a kicker block in front of the door (breaks door-to-bowl)
    box(-20.0, -6.0, -4.0, -14.0, -3.0, 4.0, 'cover')                  # a funbox in the bowl's west half
    # ============================================================ north lane (west half)
    box(-34.0, 0.0, 36.0, -20.0, 1.8, 38.2, 'cover')                   # a skate ledge
    # the quarter-pipe: steps up west to a deck at 6 (a flank perch), its back wall, a stair down its north end
    qx0, qx1, qz0, qz1 = -54.0, -42.0, 30.0, 60.0
    for k in range(6):
        box(qx1 - (k + 1) * 1.2, 0.0, qz0, qx1 - k * 1.2, k + 1.0, qz1, 'step' if k < 5 else 'concrete')
    box(qx0, 0.0, qz0, qx1 - 7.2, 6.0, qz1, 'concrete')
    tag('qpipe', (qx0, 0.0, qz0, qx1, 6.0, qz1), 'x+')
    rot(qx0 + 0.2, 6.0 + 1.8, (qz0 + qz1) / 2, 0.4, 3.6, qz1 - qz0, 0.0, 'rail', 'c')
    box(-30.0, 0.0, 58.0, -24.0, 2.4, 64.0, 'planter'); box(-28.2, 2.4, 60.2, -25.8, 26.0, 61.8, 'tree')
    box(-64.0, 0.0, 40.0, -58.0, 2.4, 46.0, 'planter'); box(-62.2, 2.4, 42.2, -59.8, 26.0, 43.8, 'tree')
    # ============================================================ south lane (west half)
    box(-48.0, 0.0, -52.0, -40.0, 9.0, -42.0, 'kiosk')                 # a snack kiosk (its canopy is look only)
    box(-24.0, 0.0, -40.0, -14.0, 1.0, -36.0, 'cover')                 # a manual pad
    box(-62.0, 0.0, -36.0, -56.0, 2.4, -30.0, 'planter'); box(-60.2, 2.4, -33.8, -57.8, 26.0, -32.2, 'tree')

# ================================================================ the middle of the lanes (built once)
# the shelter on the north lane: back wall, a flat roof you can stand on (y 10), a bench inside, posts at the front
box(-11.0, 0.0, 57.0, 11.0, 9.0, 58.2, 'concrete')
box(-11.0, 9.0, 47.0, 11.0, 10.0, 58.2, 'roof')
for x in (-10.0, 10.0):
    box(x - 0.4, 0.0, 47.4, x + 0.4, 9.0, 48.2, 'metal')
box(-8.0, 0.0, 53.0, 8.0, 1.6, 55.0, 'wood')
tag('shelter', (-11.0, 0.0, 47.0, 11.0, 10.0, 58.2))
# a ledge each side of the bridge's north ramp
box(-14.0, 0.0, 30.0, -8.0, 1.8, 32.0, 'cover'); box(8.0, 0.0, 30.0, 14.0, 1.8, 32.0, 'cover')
# the bleachers on the south lane: five rows rising south to 9, a rail along the top
for k in range(5):
    z1 = -50.0 - 3.0 * k
    box(-24.0, 0.0, z1 - 3.0 - (1.0 if k == 4 else 0.0), 24.0, 1.8 * (k + 1), z1, 'wood')
rot(0.0, 9.0 + 1.8, -66.8, 48.0, 3.6, 0.4, 0.0, 'rail', 'c')
tag('bleachers', (-24.0, 0.0, -66.0, 24.0, 9.0, -50.0))

# ================================================================ spawns
for (x, z) in ((-104.0, -14.0), (-104.0, -5.0), (-104.0, 5.0), (-104.0, 14.0), (-100.0, -10.0), (-100.0, 10.0), (-106.0, 0.0), (-100.0, 0.0)):
    fz = -0.8 if z < -1 else 0.8           # (facing past the clubhouse's corner toward a lane, not into its back wall)
    TEAM['att'].append((x, 0.3, z, 0.6, fz))
    TEAM['def'].append((-x, 0.3, z, -0.6, fz))
TEAM['mid'] = [(-16.0, 0.3, 64.0, 0.0, -1.0), (16.0, 0.3, 64.0, 0.0, -1.0), (-32.0, 0.3, -62.0, 0.0, 1.0), (32.0, 0.3, -62.0, 0.0, 1.0)]
for (x, y, z) in ((-80.0, 0.0, 0.0), (-81.0, ROOF, 8.0), (-48.0, 6.0, 45.0), (-36.0, 0.0, 46.0), (-18.0, -6.0, -10.0), (-50.0, 0.0, -20.0),
                  (-34.0, 0.0, -46.0), (-60.0, 0.0, 60.0)):
    SPAWNS.append((x, y + 0.3, z)); SPAWNS.append((-x, y + 0.3, z))
SPAWNS += [(0.0, BRIDGE_Y + 0.3, 12.0), (0.0, 10.3, 52.0), (0.0, 9.3, -64.0), (0.0, 0.3, 40.0)]
NOTES.extend([(-81.0, 0.0, 0, 'CLUBHOUSE'), (81.0, 0.0, 0, 'CLUBHOUSE'), (-18.0, 0.0, 0, 'BOWL (-6)'), (0.0, -12.0, 0, 'BRIDGE (2)'),
              (0.0, 52.0, 0, 'SHELTER'), (0.0, -58.0, 0, 'BLEACHERS'), (-48.0, 45.0, 0, 'QUARTER-PIPE DECK (6)'),
              (-44.0, -47.0, 0, 'KIOSK'), (-104.0, 0.0, 0, 'ATT'), (104.0, 0.0, 0, 'DEF'),
              (-81.0, 0.0, 1, 'ROOF DECK (12)'), (81.0, 0.0, 1, 'ROOF DECK (12)'), (0.0, 52.0, 1, 'SHELTER ROOF (10)'), (0.0, -58.0, 1, 'BLEACHERS TOP (9)')])

# ================================================================ for the plan (arena_plan.py)
TITLE = 'SKATEPARK (new, small)'
BOUNDS = (-150.0, 150.0, -110.0, 110.0)
LEVELS = [('THE PARK (y 0; the bowl at -6)', -7.0, 7.0, 0.0), ('ROOF DECKS, SHELTER ROOF, BLEACHERS TOP (y 9 to 12)', 7.5, 20.0, 12.0)]
FLOORS = ('concrete', 'bowl', 'step', 'roof', 'wood')
COLOURS = {'concrete': (190, 190, 186), 'bowl': (160, 170, 176), 'club': (150, 88, 98), 'roof': (226, 190, 160), 'step': (205, 186, 172),
           'wood': (176, 132, 96), 'metal': (160, 170, 180), 'planter': (150, 140, 120), 'tree': (90, 120, 70), 'cover': (226, 160, 152),
           'kiosk': (170, 110, 110)}
PLAN_NOTE = ('two clubhouses face each other across a sunken bowl; a bridge crosses the bowl north to south; north lane: ledges, '
             'quarter-pipe decks, a shelter with a roof to stand on; south lane: bleachers over the bowl, kiosks; '
             'springboards onto the clubhouse roofs')

# ================================================================ the wall box (wallbox.py): no lid, walls 30 out, the step to the edge scenery
import wallbox
HIT_SOLID, HIT_ROT, WALLBOX = wallbox.rect(SOLID, ROT, X_EDGE, Z_EDGE, -6.0, 24.0, 14.0, drop=lambda b: False)
blocked, floor_under, inside, pad_flight = _M.blocked, _M.floor_under, _M.inside, _M.pad_flight

if __name__ == '__main__':
    report()
