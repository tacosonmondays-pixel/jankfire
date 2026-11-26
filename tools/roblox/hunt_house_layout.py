# THE HOUSE (26 Nov 2026): the lobby of HOLDOUT, the one-gunman hunt mode (roblox/docs/HUNT.md). The owner: "Youll be
# in a house, with a backyard, there will be trampoline a garage tables outside for gamepasses with stuff. Itll be a
# bigish house so we can fit props inside, and people will spawn inisde and wait for a new game to start! They can run
# around interact with stuff, punch push super push."
#
# A big two-storey family house of our own design (no real house, no other game's map): the front porch and hall with
# the stair; the living room with its fireplace; the family room with glass doors to the patio; the kitchen and the
# dining room; a hallway with the cloakroom WC and a coat closet; the back hall to the garden; the garage with its roll-up
# door. Upstairs: a gallery over the hall, the main bedroom with its bathroom and walk-in closet, a kids' room, the guest
# room, the study, the playroom with a balcony over the patio, the family bathroom. Outside: the porch, the front lawn,
# the driveway and its hoop; the back garden with the patio (pergola, the three store tables, the grill), the lawn
# with the TRAMPOLINE, a big tree, a shed, the fence round it all.
#
# Everything in studs, local to the house's origin (workspace.Map.HuntHouse, world (0, 300, -90000)): x east, z south (the
# front door faces +z, the garden is at -z), y up; the ground floor's top at y 0, the yard's lawn at y -1.5. A storey is
# 13 studs: 12 clear, a 1-stud slab. Outside walls 2 thick, inside walls 1. Doors 6 wide, 9.5 tall; windows sill 3.5,
# head 9.5 over their floor. The game scale is about 1.5 x a real house: the main game's movement is fast (30 studs/s
# running), so rooms and halls are generous.
#
# Plain Python, no Blender: hunt_house_models.py (the kit) and the checks at the bottom read the same numbers.
#   py tools/roblox/hunt_house_layout.py          the checks: spawns, doors clear, every room reached
import os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from maplayout import SOLID, ROT, OPENS, box, rot, wall, slab

TITLE = 'THE HOUSE'
G0, U0 = 0.0, 13.0             # the floors' tops
CLEAR = 12.0                   # clear height of a storey
EAVE, RIDGE = 26.0, 41.0       # the main roof
GROUND = -1.5                  # the lawn
PATIO = -1.0                   # the patio and the garage floor
DOOR_W, DOOR_H = 6.0, 9.5
SILL, HEAD = 3.5, 9.5
X0, X1, Z0, Z1 = -60.0, 60.0, -42.0, 42.0        # the house's outside faces
GX1, GZ0 = 104.0, -12.0                          # the garage: x 60..104, z -12..42
LOT = (-88.0, -156.0, 112.0, 98.0)               # the lot's invisible walls (x0, z0, x1, z1)
BOUND_TOP = 220.0

# ================================================================ rooms (the kit's finishes, the lights, the switches)
ROOMS = []
def room(rid, name, lv, r, floor='oak', wall='plaster', light=True):
    ROOMS.append(dict(id=rid, name=name, lv=lv, r=tuple(float(v) for v in r), floor=floor, wall=wall, light=light))

# ground floor
room('entry', 'Hall', 'G', (-12, 4, 12, 40), 'oak')
room('living', 'Living Room', 'G', (-58, 2, -13, 40), 'oak')
room('family', 'Family Room', 'G', (-58, -40, -13, 1), 'oak')
room('passage', 'Hall', 'G', (-3.5, -12, 3.5, 4), 'oak', light=False)
room('wc', 'Cloakroom', 'G', (-12, -12, -4.5, 3), 'bathtile', 'tile')
room('coats', 'Coat Closet', 'G', (4.5, -12, 12, 3), 'oak')
room('backhall', 'Back Hall', 'G', (-12, -40, 12, -13), 'stone')
room('dining', 'Dining Room', 'G', (13, 4.5, 58, 40), 'oak')
room('kitchen', 'Kitchen', 'G', (13, -40, 58, 3.5), 'tilefloor')
room('garage', 'Garage', 'G', (60, -10, 102, 40), 'concrete', 'block')
# upper floor
room('gallery', 'Landing', 'U', (-12, -23, 12, 40), 'carpet')
room('mainbed', 'Main Bedroom', 'U', (-58, 10, -13, 40), 'carpet')
room('ensuite', 'Bathroom', 'U', (-58, -8, -36, 9), 'bathtile', 'tile')
room('closet', 'Walk-in Closet', 'U', (-35, -8, -13, 9), 'carpet')
room('kidsbed', "Kids' Room", 'U', (-58, -40, -13, -9), 'carpet')
room('guestbed', 'Guest Room', 'U', (13, 12, 58, 40), 'carpet')
room('study', 'Study', 'U', (13, -8, 58, 11), 'oak')
room('playroom', 'Playroom', 'U', (13, -40, 58, -9), 'carpet')
room('bath', 'Bathroom', 'U', (-12, -40, 12, -24), 'bathtile', 'tile')

LVY = {'G': G0, 'U': U0}

# ================================================================ walls (holes: (a0, a1, y0, y1, kind), local to the storey)
DOORS = []        # every door leaf HuntBuild hangs: dict(id, kind, axis, line, a0, a1, y0, y1, hinge, swing, rooms)
WINDOWS = []      # (axis, c0, c1, a0, a1, y0, y1, kind): the kit's frames and glass
def W_(axis, c0, c1, a0, a1, lv, y1, holes, m, ext=False):
    """a wall on one storey. axis 'x': it runs along x (a0..a1), c0..c1 its thickness in z; 'z' the other way.
    holes are local to the storey's floor (y 0 = its floor top)"""
    b = LVY[lv]
    y0 = GROUND if (ext and lv == 'G') else b
    hs = []
    for (h0, h1, hy0, hy1, kind) in holes:
        hs.append((h0, h1, b + hy0, b + hy1, kind))
        if kind.startswith('win') or kind in ('side', 'frost'):
            WINDOWS.append((axis, c0, c1, h0, h1, b + hy0, b + hy1, kind))
            cm = (c0 + c1) / 2                                   # (the glass: a hit box across the opening's middle)
            if axis == 'x': box(h0, b + hy0, cm - 0.2, h1, b + hy1, cm + 0.2, 'glass')
            else: box(cm - 0.2, b + hy0, h0, cm + 0.2, b + hy1, h1, 'glass')
    wall(axis, c0, c1, a0, a1, y0, b + y1, hs, m)

def door(did, kind, axis, line, a0, a1, lv, hinge='a0', swing=1, rooms=(), h=DOOR_H):
    """a door leaf in an opening: axis is the wall's run; line its centre line; hinge on a0's or a1's side; swing +1 opens
    toward +z (axis x) or +x (axis z)"""
    b = LVY[lv]
    DOORS.append(dict(id=did, kind=kind, axis=axis, line=float(line), a0=float(a0), a1=float(a1), y0=b, y1=b + h,
                      hinge=hinge, swing=swing, rooms=tuple(rooms), lv=lv))

D = lambda a0, a1, kind='door', h=DOOR_H: (a0, a1, 0.0, h, kind)
WIN = lambda a0, a1, kind='win', s=SILL, t=HEAD: (a0, a1, s, t, kind)

# ---------------------------------------------------------------- ground floor, outside (2 thick, from the lawn up)
W_('x', 40, 42, X0, X1, 'G', 13, [WIN(-52, -42), WIN(-30, -20), D(-3.5, 3.5, 'front', 10.0), WIN(-6.5, -4.5, 'side', 1.0, 9.0),
                                  WIN(4.5, 6.5, 'side', 1.0, 9.0), WIN(22, 32), WIN(40, 50)], 'brick', ext=True)
W_('x', -42, -40, X0, X1, 'G', 13, [D(-50, -30, 'slide', 10.0), WIN(-24, -16), D(-3.5, 3.5, 'back', DOOR_H),
                                    WIN(22, 34, 'win', 5.8, 10.0), D(44, 50, 'back', DOOR_H)], 'brick', ext=True)
W_('z', -60, -58, Z0 + 2, Z1 - 2, 'G', 13, [WIN(35, 39), WIN(3, 7), WIN(-38, -30)], 'brick', ext=True)
W_('z', 58, 60, Z0 + 2, GZ0, 'G', 13, [WIN(-34, -24, 'win', 5.8, 10.0)], 'brick', ext=True)      # the kitchen's east wall, outside the garage
W_('z', 58, 60, GZ0, Z1 - 2, 'G', 13, [D(-9, -3)], 'brick')                     # the wall to the garage
door('front', 'front', 'x', 41, -3.5, 3.5, 'G', 'a0', -1, h=10.0)
door('slide', 'slide', 'x', -41, -50, -30, 'G', 'a1', 1, h=10.0)
door('backhall', 'back', 'x', -41, -3.5, 3.5, 'G', 'a1', -1)
door('kitchenback', 'back', 'x', -41, 44, 50, 'G', 'a0', -1)
door('garage', 'int', 'z', 59, -9, -3, 'G', 'a1', 1, rooms=('kitchen', 'garage'))

# ---------------------------------------------------------------- ground floor, inside (1 thick)
W_('z', -13, -12, -40, 40, 'G', 12, [D(14, 32, 'arch', 10.0), D(-24, -18)], 'plaster')       # centre | west wing
door('family', 'int', 'z', -12.5, -24, -18, 'G', 'a0', -1, rooms=('backhall', 'family'))
W_('z', 12, 13, -40, 40, 'G', 12, [D(6, 15, 'arch', 10.0), D(-26, -20)], 'plaster')          # centre | east wing
door('kitchen', 'int', 'z', 12.5, -26, -20, 'G', 'a1', 1, rooms=('backhall', 'kitchen'))
W_('x', 1, 2, -58, -13, 'G', 12, [D(-48, -28, 'arch', 10.0)], 'plaster')                     # living | family
W_('x', 3.5, 4.5, 13, 58, 'G', 12, [D(18, 46, 'open', 10.5)], 'plaster')                      # dining | kitchen
# the middle: the cloakroom WC (west), the coat closet (east), the hallway between them
W_('x', 3, 4, -12, -4.5, 'G', 12, [], 'plaster')
W_('x', -13, -12, -12, -4.5, 'G', 12, [], 'plaster')
W_('z', -4.5, -3.5, -13, 4, 'G', 12, [D(-9, -3)], 'plaster')
door('wc', 'int', 'z', -4, -9, -3, 'G', 'a0', -1, rooms=('passage', 'wc'))
W_('x', 3, 4, 4.5, 12, 'G', 12, [], 'plaster')
W_('x', -13, -12, 4.5, 12, 'G', 12, [], 'plaster')
W_('z', 3.5, 4.5, -13, 4, 'G', 12, [D(-9, -3)], 'plaster')
door('coats', 'int', 'z', 4, -9, -3, 'G', 'a1', 1, rooms=('passage', 'coats'))

# ---------------------------------------------------------------- upper floor, outside
W_('x', 40, 42, X0, X1, 'U', 13, [WIN(-52, -42), WIN(-30, -20), WIN(-4, 4), WIN(22, 32), WIN(40, 50)], 'siding', ext=True)
W_('x', -42, -40, X0, X1, 'U', 13, [WIN(-52, -42), WIN(-30, -20), WIN(-4, 4, 'frost', 5.5), D(26, 32, 'balc', DOOR_H), WIN(40, 50)], 'siding', ext=True)
W_('z', -60, -58, Z0 + 2, Z1 - 2, 'U', 13, [WIN(33, 38), WIN(-2, 4, 'frost', 5.5), WIN(-38, -30)], 'siding', ext=True)
W_('z', 58, 60, Z0 + 2, Z1 - 2, 'U', 13, [WIN(34, 39), WIN(0, 6), WIN(-30, -22)], 'siding', ext=True)
door('balcony', 'back', 'x', -41, 26, 32, 'U', 'a0', -1)

# ---------------------------------------------------------------- upper floor, inside
W_('z', -13, -12, -40, 40, 'U', 12, [D(20, 26), D(-22, -16)], 'plaster')
door('mainbed', 'int', 'z', -12.5, 20, 26, 'U', 'a0', -1, rooms=('gallery', 'mainbed'))
door('kidsbed', 'int', 'z', -12.5, -22, -16, 'U', 'a1', -1, rooms=('gallery', 'kidsbed'))
W_('z', 12, 13, -40, 40, 'U', 12, [D(33, 39), D(-4, 2), D(-22, -16)], 'plaster')
door('guestbed', 'int', 'z', 12.5, 33, 39, 'U', 'a1', 1, rooms=('gallery', 'guestbed'))
door('study', 'int', 'z', 12.5, -4, 2, 'U', 'a0', 1, rooms=('gallery', 'study'))
door('playroom', 'int', 'z', 12.5, -22, -16, 'U', 'a1', 1, rooms=('gallery', 'playroom'))
W_('x', 9, 10, -58, -13, 'U', 12, [D(-53, -47), D(-27, -21)], 'plaster')                    # main bed | bath, closet
door('ensuite', 'int', 'x', 9.5, -53, -47, 'U', 'a0', -1, rooms=('mainbed', 'ensuite'))
door('closet', 'int', 'x', 9.5, -27, -21, 'U', 'a1', -1, rooms=('mainbed', 'closet'))
W_('x', -9, -8, -58, -13, 'U', 12, [], 'plaster')                                            # bath, closet | kids
W_('z', -36, -35, -8, 9, 'U', 12, [], 'plaster')                                             # bath | closet
W_('x', 11, 12, 13, 58, 'U', 12, [], 'plaster')                                              # guest | study
W_('x', -9, -8, 13, 58, 'U', 12, [], 'plaster')                                              # study | playroom
W_('x', -24, -23, -12, 12, 'U', 12, [D(-3, 3)], 'plaster')                                   # bath | landing
door('bath', 'int', 'x', -23.5, -3, 3, 'U', 'a0', -1, rooms=('gallery', 'bath'))

# ---------------------------------------------------------------- the garage (outside walls 2 thick, a flat roof at 14)
W_('z', 102, 104, GZ0, Z1, 'G', 15.5, [], 'siding', ext=True)
W_('x', GZ0, GZ0 + 2, 60, 104, 'G', 15.5, [(88, 94, -1.0, 8.5, 'door')], 'siding', ext=True)
door('garageside', 'int', 'x', GZ0 + 1, 88, 94, 'G', 'a1', -1, rooms=('garage', 'garden'))
DOORS[-1]['y0'] = PATIO; DOORS[-1]['y1'] = 8.5
W_('x', 40, 42, 60, 104, 'G', 15.5, [(66, 98, -1.0, 11.0, 'rollup')], 'siding', ext=True)
GARAGE_DOOR = dict(a0=66.0, a1=98.0, y0=PATIO, y1=11.0, z=41.0)       # the roll-up door (HuntBuild's moving panel)
slab(60, GZ0, 104, Z1, 13, 14, 'garageroof')

# ================================================================ floors, ceilings, the stair, the roof
VOID = (4.0, 17.8, 12.0, 31.0)       # the stairwell's hole in the upper floor (x0, z0, x1, z1)
slab(X0, Z0, X1, Z1, -1.5, 0.0, 'slab')                               # the ground floor
slab(60, GZ0, 102, Z1 - 2, -1.5, PATIO, 'garagefloor')                 # the garage, a step down
slab(X0 + 2, Z0 + 2, X1 - 2, Z1 - 2, 12.0, 13.0, 'slab', holes=[VOID])  # the upper floor
slab(X0 + 2, Z0 + 2, X1 - 2, Z1 - 2, 25.0, 26.0, 'slab')               # the upper ceiling (the roof sits on it)

STAIR = dict(x0=4.0, x1=12.0, z_bottom=36.0, run=1.4, n=13)     # 13 steps from z 36 (y 0) up toward -z to 17.8 (y 13)
for k in range(1, 14):
    z_hi, z_lo = 36.0 - 1.4 * (k - 1), 36.0 - 1.4 * k
    box(4.0, max(0.0, k - 3.0), z_lo, 12.0, float(k), z_hi, 'stair')
# under the stair from the 3rd step: a wall to the floor along its open side (the closet behind it is under the treads)
for k in range(3, 14):
    z_hi, z_lo = 36.0 - 1.4 * (k - 1), 36.0 - 1.4 * k
    box(3.5, 0.0, z_lo, 4.0, k - 2.0, z_hi, 'plaster')
# the stair's balustrade (solid, 3.4 over the step line) and the gallery's round the hole
for k in range(1, 14, 2):
    z_hi, z_lo = 36.0 - 1.4 * (k - 1), max(17.8, 36.0 - 1.4 * (k + 1))
    box(3.5, k, z_lo, 4.0, k + 3.4, z_hi, 'rail')
box(3.5, U0, VOID[1], 4.0, U0 + 3.4, VOID[3], 'rail')
box(4.0, U0, VOID[3], 12.0, U0 + 3.4, VOID[3] + 0.5, 'rail')

# the main roof: a gable along x, 2 over the walls at the eaves, ridge at 41; the gable ends stand on the side walls
ROOF = dict(x0=X0 - 2.0, x1=X1 + 2.0, z0=Z0 - 2.5, z1=Z1 + 2.5, eave=EAVE, ridge=RIDGE)
TILT = []     # (centre x, y, z, x axis, y axis, size, mat, 'b' | 'w', flags) for arenakit.write_layout's tilt
def plane(x0, x1, za, ya, zb, yb, th, mat):
    """a sloped slab from (z a, y a) to (z b, y b) across x0..x1, th thick under its top face"""
    dz, dy = zb - za, yb - ya
    ln = math.hypot(dz, dy)
    uz, uy = dz / ln, dy / ln                       # along the slope
    nz, ny = -uy * (1 if dz > 0 else -1), abs(uz)   # its up normal
    if ny < 0: nz, ny = -nz, -ny
    cx, cy, cz = (x0 + x1) / 2, (ya + yb) / 2 - ny * th / 2, (za + zb) / 2 - nz * th / 2
    TILT.append((cx, cy, cz, 1.0, 0.0, 0.0, 0.0, ny, nz, x1 - x0, th, ln, mat, 'b', ''))
plane(ROOF['x0'], ROOF['x1'], ROOF['z1'], EAVE - 0.9, 0.0, RIDGE, 1.2, 'roof')     # the front slope
plane(ROOF['x0'], ROOF['x1'], ROOF['z0'], EAVE - 0.9, 0.0, RIDGE, 1.2, 'roof')     # the back slope
# the gable walls (x = -60..-58 and 58..60): 2-stud bands up the triangle, each under the roof planes' top
for (gx0, gx1) in ((X0, X0 + 2), (X1 - 2, X1)):
    y_lo = EAVE
    while y_lo < RIDGE - 1.0:
        y_hi = min(RIDGE, y_lo + 2.0)
        hw = min(Z1, (Z1 + 2.5) * (RIDGE - y_hi) / (RIDGE - (EAVE - 0.9)) - 1.4)
        if hw > 0.5: box(gx0, y_lo, -hw, gx1, y_hi, hw, 'siding')
        y_lo = y_hi
# the chimney on the west gable
box(-63.0, GROUND, 15.0, -58.0, 47.0, 27.0, 'chimney')
# the porch (floor at 0, a flat roof on two posts) and its steps
slab(-14, 42, 14, 52, -1.5, 0.0, 'porch')
box(-10, -1.5, 52, 10, -0.75, 54, 'porchstep')
slab(-16, 42, 16, 55, 12.0, 13.0, 'porchroof')
for px in (-13.5, 13.5): box(px - 1, 0, 50, px + 1, 12, 52, 'post')
# the balcony over the patio (the playroom's door), on two posts; a solid parapet
slab(14, -56, 50, -42, 12.0, 13.0, 'balcony')
box(14, 13, -56, 50, 16.4, -55.4, 'rail'); box(14, 13, -56, 14.6, 16.4, -42, 'rail'); box(49.4, 13, -56, 50, 16.4, -42, 'rail')
for px in (15.5, 48.5): box(px - 1, PATIO, -56, px + 1, 12, -54, 'post')
# the garage roof's parapet (you can get up there from the trampoline)
box(60, 14, GZ0, 104, 15.5, GZ0 + 1, 'parapet'); box(103, 14, GZ0, 104, 15.5, Z1, 'parapet'); box(60, 14, Z1 - 1, 104, 15.5, Z1, 'parapet')

# ================================================================ the grounds
slab(LOT[0] - 2, LOT[1] - 2, LOT[2] + 2, LOT[3] + 2, -6.0, GROUND, 'grass',
     holes=[(X0, Z0, X1, Z1), (60, GZ0, 104, Z1), (-60, -64, 52, -42), (62, 42, 102, 82), (-3, 54, 3, 80), (-14, 42, 14, 52)])
slab(-60, -64, 52, -42, -6.0, PATIO, 'pavers')                   # the patio, a step down from the house
slab(62, 42, 102, 82, -6.0, PATIO, 'concrete')                   # the driveway
slab(-3, 54, 3, 80, -6.0, -1.2, 'pavers')                        # the front path
box(LOT[0] - 2, -6, 80, LOT[2] + 2, -1.2, 84, 'pavers')          # the sidewalk (over the lawn's edge)
# the back garden's fence: 7 high round the garden and the side yards; a gate in the west side yard
FENCE_H = 7.0
def fence(x0, z0, x1, z1): box(x0, GROUND, z0, x1, GROUND + FENCE_H, z1, 'fence')
fence(-86, -154, 110, -152)                  # the back
fence(-86, -154, -84, 36)                    # the west side, up to the side yard's front
fence(-86, 34, -84, 36)                      # the side yard's front: the gate at x -84..-78
fence(108, -154, 110, -12)                   # the east side, behind the garage
fence(104, -12, 110, -10)
GATE = dict(axis='x', line=35.0, a0=-84.0, a1=-78.0)
fence(-78, 34, -60, 36)
door('gate', 'gate', 'x', 35, -84, -78, 'G', 'a0', 1, h=FENCE_H)
DOORS[-1]['y0'] = GROUND; DOORS[-1]['y1'] = GROUND + FENCE_H
# the lot's invisible walls and lid
INVIS = []
for b in ((LOT[0] - 2, -6, LOT[1] - 2, LOT[0], BOUND_TOP, LOT[3] + 2), (LOT[2], -6, LOT[1] - 2, LOT[2] + 2, BOUND_TOP, LOT[3] + 2),
          (LOT[0], -6, LOT[1] - 2, LOT[2], BOUND_TOP, LOT[1]), (LOT[0], -6, LOT[3], LOT[2], BOUND_TOP, LOT[3] + 2),
          (LOT[0] - 2, BOUND_TOP, LOT[1] - 2, LOT[2] + 2, BOUND_TOP + 2, LOT[3] + 2)):
    box(*b, 'invis')

# ================================================================ furniture (hit boxes; FURN for the kit)
# kind -> (size x, y, z as it stands facing +z, hit boxes local to its bottom centre facing +z, or None = no hit box)
# a hit box list: [(x0, y0, z0, x1, y1, z1)]. Beds and tables stand clear underneath (3.5 and 4.6) so a hider lying down
# rolls under them (lying is 2.4 tall)
KINDS = {
    'sofa3':      ((18, 5.5, 7), [(-9, 0, -3.5, 9, 2.8, 3.5), (-9, 0, -3.5, 9, 5.5, -1.5)]),
    'sofa2':      ((12, 5.5, 7), [(-6, 0, -3.5, 6, 2.8, 3.5), (-6, 0, -3.5, 6, 5.5, -1.5)]),
    'sectional':  ((22, 5.5, 16), [(-11, 0, -8, 11, 2.8, -1), (-11, 0, -8, 11, 5.5, -6), (4, 0, -8, 11, 2.8, 8), (9, 0, -8, 11, 5.5, 8)]),
    'armchair':   ((7, 5.5, 7), [(-3.5, 0, -3.5, 3.5, 2.8, 3.5), (-3.5, 0, -3.5, 3.5, 5.5, -1.5)]),
    'coffee':     ((10, 2.2, 6), [(-5, 0, -3, 5, 2.2, 3)]),
    'media':      ((16, 3, 3.5), [(-8, 0, -1.75, 8, 3, 1.75)]),
    'bookcase':   ((8, 12, 2.5), [(-4, 0, -1.25, 4, 12, 1.25)]),
    'shelfwide':  ((14, 9, 2.5), [(-7, 0, -1.25, 7, 9, 1.25)]),
    'hearth':     ((10, 0.6, 4), None),
    'rug':        ((24, 0.1, 16), None),
    'rugsmall':   ((12, 0.1, 8), None),
    'lamp':       ((2, 9, 2), None),
    'plant':      ((3, 6, 3), [(-1.2, 0, -1.2, 1.2, 2.4, 1.2)]),
    'pingpong':   ((15, 4.6, 8.5), [(-7.5, 3.9, -4.25, 7.5, 4.6, 4.25), (-6.5, 0, -0.4, -5.5, 3.9, 0.4), (5.5, 0, -0.4, 6.5, 3.9, 0.4)]),
    'beanbag':    ((4.5, 3, 4.5), None),
    'piano':      ((10, 8, 4), [(-5, 0, -2, 5, 8, 2)]),
    'toychest':   ((6, 3, 3), [(-3, 0, -1.5, 3, 3, 1.5)]),
    'counter':    ((4, 5.4, 4), [(-2, 0, -2, 2, 5.4, 2)]),          # one 4-stud run (counters are rows of these)
    'island':     ((16, 5.4, 7), [(-8, 0, -3.5, 8, 5.4, 3.5)]),
    'stool':      ((2.4, 4, 2.4), None),
    'fridge':     ((6, 12, 5), [(-3, 0, -2.5, 3, 12, 2.5)]),
    'stove':      ((5, 5.4, 4), [(-2.5, 0, -2, 2.5, 5.4, 2)]),
    'sinkunit':   ((8, 5.4, 4), [(-4, 0, -2, 4, 5.4, 2)]),
    'tallcab':    ((5, 12, 4), [(-2.5, 0, -2, 2.5, 12, 2)]),
    'diningtable':((18, 5.4, 8), [(-9, 4.6, -4, 9, 5.4, 4), (-8.5, 0, -3.5, -7.7, 4.6, -2.7), (7.7, 0, -3.5, 8.5, 4.6, -2.7),
                                   (-8.5, 0, 2.7, -7.7, 4.6, 3.5), (7.7, 0, 2.7, 8.5, 4.6, 3.5)]),
    'chair':      ((2.8, 6, 2.8), [(-1.4, 0, -1.4, 1.4, 2.9, 1.4)]),
    'sideboard':  ((14, 5, 3), [(-7, 0, -1.5, 7, 5, 1.5)]),
    'toilet':     ((3, 4, 5), [(-1.5, 0, -2.5, 1.5, 2.8, 2.5), (-1.5, 0, -2.5, 1.5, 4.0, -1.3)]),
    'basin':      ((4, 5, 3), [(-2, 0, -1.5, 2, 5, 1.5)]),
    'vanity':     ((10, 5, 4), [(-5, 0, -2, 5, 5, 2)]),
    'bathtub':    ((7, 3.6, 15), [(-3.5, 0, -7.5, 3.5, 3.6, 7.5)]),
    'shower':     ((8, 12, 8), [(-4, 0, -4, 4, 12, -3.6), (-4, 0, -4, -3.6, 12, 4)]),
    'bedking':    ((14, 4.6, 17), [(-7, 3.4, -8.5, 7, 4.6, 8.5), (-7, 0, -8.5, 7, 9, -7.5)]),
    'beddouble':  ((11, 4.6, 15), [(-5.5, 3.4, -7.5, 5.5, 4.6, 7.5), (-5.5, 0, -7.5, 5.5, 8, -6.5)]),
    'bunk':       ((8, 12, 15), [(-4, 3.4, -7.5, 4, 4.4, 7.5), (-4, 8.6, -7.5, 4, 9.6, 7.5), (-4, 0, -7.5, 4, 12, -7.0),
                                  (-4, 0, 7.0, 4, 12, 7.5)]),
    'nightstand': ((3.5, 3.2, 3), [(-1.75, 0, -1.5, 1.75, 3.2, 1.5)]),
    'dresser':    ((10, 5, 3.5), [(-5, 0, -1.75, 5, 5, 1.75)]),
    'wardrobe':   ((8, 11, 4), [(-4, 0, -2, 4, 11, 2)]),
    'desk':       ((12, 4.6, 6), [(-6, 4.0, -3, 6, 4.6, 3), (-6, 0, -3, -5, 4.0, 3), (5, 0, -3, 6, 4.0, 3)]),
    'officechair':((3, 6, 3), None),
    'filing':     ((3, 5, 4), [(-1.5, 0, -2, 1.5, 5, 2)]),
    'shoeisland': ((8, 4, 5), [(-4, 0, -2.5, 4, 4, 2.5)]),
    'rail':       ((12, 9, 2.5), None),            # hanging clothes
    'pooltable':  ((14, 5, 8), [(-7, 3.2, -4, 7, 5, 4), (-6, 0, -3, 6, 3.2, 3)]),
    'tvwall':     ((12, 7, 0.6), None),
    'console':    ((8, 2.6, 3), [(-4, 0, -1.5, 4, 2.6, 1.5)]),
    'bench':      ((8, 3, 2.5), [(-4, 0, -1.25, 4, 3, 1.25)]),
    'coatrack':   ((6, 9, 1.5), None),
    # the garage
    'car':        ((9, 7, 20), [(-4.5, 0.8, -10, 4.5, 4.4, 10), (-4, 4.4, -5, 4, 7, 4)]),
    'workbench':  ((14, 5.4, 4), [(-7, 0, -2, 7, 5.4, 2)]),
    'shelving':   ((12, 11, 3), [(-6, 0, -1.5, 6, 11, 1.5)]),
    'freezer':    ((8, 5, 4.5), [(-4, 0, -2.25, 4, 5, 2.25)]),
    'washer':     ((5, 5.5, 5), [(-2.5, 0, -2.5, 2.5, 5.5, 2.5)]),
    'bikes':      ((8, 5, 2), None),
    'golfbag':    ((2.2, 5, 2.2), None),
    # outside
    'storetable': ((10, 5.2, 5), [(-5, 0, -2.5, 5, 5.2, 2.5)]),
    'umbrella':   ((12, 11, 12), [(-0.4, 0, -0.4, 0.4, 10, 0.4)]),
    'grill':      ((6, 6, 3.5), [(-3, 0, -1.75, 3, 5, 1.75)]),
    'lounger':    ((4, 3, 10), None),
    'patiochair': ((3, 5, 3), None),
    'patiotable': ((6, 4.6, 6), [(-3, 3.8, -3, 3, 4.6, 3), (-0.4, 0, -0.4, 0.4, 3.8, 0.4)]),
    'trampoline': ((28, 3.2, 28), None),           # its own hit shapes (TRAMP below)
    'swingset':   ((20, 13, 9), [(-10.4, 0, -4.0, -9.4, 12.5, 4.0), (9.4, 0, -4.0, 10.4, 12.5, 4.0)]),
    'tree':       ((30, 34, 30), [(-2, 0, -2, 2, 14, 2)]),
    'treebench':  ((12, 3, 12), None),
    'shed':       ((22, 13, 16), [(-11, 0, -8, 11, 10, -7), (-11, 0, 7, -3, 10, 8), (3, 0, 7, 11, 10, 8), (-11, 0, -8, -10, 10, 8), (10, 0, -8, 11, 10, 8),
                                  (-12, 10, -9, 12, 11.5, 9)]),
    'flowerbed':  ((20, 1.6, 4), [(-10, 0, -2, 10, 1.6, 2)]),
    'hedge':      ((20, 5, 4), [(-10, 0, -2, 10, 5, 2)]),
    'mailbox':    ((1.5, 5, 2), [(-0.4, 0, -0.4, 0.4, 5, 0.4)]),
    'hoop':       ((6, 18, 3), None),              # on the garage's front, over the door
    'hose':       ((3, 3, 2), None),
    'bins':       ((7, 5, 3.5), [(-3.5, 0, -1.75, 3.5, 5, 1.75)]),
    'board':      ((14, 8, 0.6), None),            # the round board on the hall wall
}
FURN = []         # (kind, cx, y, cz, turn) turn: quarter turns (0 faces +z, 1 faces +x, 2 -z, 3 -x)
def F(kind, cx, cz, y=0.0, turn=0, solid=True):
    FURN.append((kind, float(cx), float(y), float(cz), turn))
    hb = KINDS[kind][1]
    if not solid or not hb: return
    for (a0, b0, c0, a1, b1, c1) in hb:
        pts = [rq(a0, c0, turn), rq(a1, c1, turn)]
        xs, zs = [p[0] for p in pts], [p[1] for p in pts]
        box(cx + min(xs), y + b0, cz + min(zs), cx + max(xs), y + b1, cz + max(zs), 'furn_' + kind)
def rq(x, z, turn):
    for _ in range(turn % 4): x, z = z, -x
    return x, z

# ---------------------------------------------------------------- the living room (x -58..-13, z 2..40)
# the fireplace on the west wall (the chimney outside, z 15..27), bookcases either side, the TV over the mantel; the sofa
# faces it, the armchairs either end of the coffee table; the piano on the wall by the hall arch
F('hearth', -55.5, 21, turn=1)
F('tvwall', -57.6, 21, y=7.0, turn=1)
F('bookcase', -56.4, 11.5, turn=1); F('bookcase', -56.4, 30.5, turn=1)
F('rug', -40, 21, turn=1)
F('sofa3', -32, 21, turn=3)
F('armchair', -44, 33.5, turn=2); F('armchair', -44, 8.5, turn=0)
F('coffee', -42, 21, turn=1)
F('lamp', -26, 34); F('plant', -16, 37.5)
F('piano', -15.1, 7, turn=3)
# ---------------------------------------------------------------- the family room (x -58..-13, z -40..1): the games room
F('media', -56.2, -10, turn=1); F('tvwall', -57.6, -10, y=4.5, turn=1)
F('sofa3', -42, -10, turn=3); F('rugsmall', -49, -10, turn=1)
F('beanbag', -52, -2); F('beanbag', -47, -1)
F('pingpong', -24, -30, turn=1)
F('toychest', -55.5, -36, turn=1)
F('plant', -16, -3)
# ---------------------------------------------------------------- the hall (x -12..12, z 4..40) and the middle
F('bench', -10.7, 36, turn=1); F('coatrack', 11.2, 38, y=1.5, turn=3)
F('rugsmall', -2, 24, turn=1)
F('toilet', -9.5, -10.8, turn=1); F('basin', -10.5, 1, turn=1)
F('coatrack', 11.2, -3, y=1.5, turn=3)
# ---------------------------------------------------------------- the back hall (x -12..12, z -40..-13)
F('bench', -10.5, -30, turn=1); F('coatrack', -11.4, -36, y=1.5, turn=1)
F('washer', 9.3, -37, turn=2); F('washer', 9.3, -31.5, turn=3)
F('plant', 9.5, -16)
# ---------------------------------------------------------------- the dining room (x 13..58, z 4.5..40)
F('rug', 34, 22)
F('diningtable', 34, 22, turn=0)
for dx in (-6, 0, 6):
    F('chair', 34 + dx, 27.6, turn=2); F('chair', 34 + dx, 16.4, turn=0)
F('chair', 23.8, 22, turn=1); F('chair', 44.2, 22, turn=3)
F('sideboard', 56.2, 22, turn=3)
F('plant', 15.5, 37.5); F('plant', 55.5, 37.5)
# ---------------------------------------------------------------- the kitchen (x 13..58, z -40..3.5)
for zc in (-36, -32, -28, -24, -16, -12):              # the east wall's run of counters, the stove in it
    F('counter', 56, zc, turn=3)
F('stove', 55.5, -20, turn=3)
F('fridge', 55.5, 0.5, turn=3)
F('sinkunit', 28, -38, turn=0)                          # under the back window
for xc in (16, 20, 36, 40):
    F('counter', xc, -38, turn=0)
F('island', 34, -18, turn=0)
for dx in (-5, 0, 5): F('stool', 34 + dx, -12.5)
# ---------------------------------------------------------------- the garage (x 60..102, z -10..40)
F('car', 74, 18, y=PATIO, turn=0)
F('workbench', 100, 0, y=PATIO, turn=3)
F('shelving', 100.4, 14, y=PATIO, turn=3); F('shelving', 100.4, 26, y=PATIO, turn=3)
F('freezer', 92, 36.5, y=PATIO, turn=2)
F('bikes', 63, 32, y=PATIO, turn=1)
F('golfbag', 80.5, -8.2, y=PATIO)
# ---------------------------------------------------------------- upstairs: the main bedroom (x -58..-13, z 10..40)
F('bedking', -49, 24, y=U0, turn=1)                     # its head on the west wall
F('nightstand', -56.4, 14.5, y=U0, turn=1); F('nightstand', -56.4, 33.5, y=U0, turn=1)
F('dresser', -35, 38.2, y=U0, turn=2)
F('armchair', -20, 30, y=U0, turn=3)
F('rug', -38, 24, y=U0, turn=1)
# the main bedroom's bathroom (x -58..-36, z -8..9)
F('bathtub', -47, -4.5, y=U0, turn=1); F('vanity', -56, 3, y=U0, turn=1); F('toilet', -38.5, 5.5, y=U0, turn=2)
# the walk-in closet (x -35..-13, z -8..9)
F('shoeisland', -24, -0.5, y=U0, turn=1); F('rail', -24, -7, y=U0, turn=0); F('rail', -34, 0.5, y=U0, turn=1)
# the kids' room (x -58..-13, z -40..-9)
F('bunk', -53.9, -17, y=U0, turn=0)
F('desk', -36, -37, y=U0, turn=0); F('officechair', -36, -32.5, y=U0)
F('toychest', -47, -38.4, y=U0, turn=0)
F('bookcase', -15.4, -32, y=U0, turn=3)
F('rugsmall', -38, -22, y=U0); F('beanbag', -28, -14, y=U0)
# the landing (x -12..12, z -23..40 round the stairwell)
F('bookcase', -10.7, 34, y=U0, turn=1); F('armchair', -6, 36, y=U0, turn=2); F('plant', 10, 38, y=U0)
# the guest room (x 13..58, z 12..40)
F('beddouble', 49.5, 26, y=U0, turn=3)                  # its head on the east wall
F('nightstand', 56.4, 18.5, y=U0, turn=3); F('nightstand', 56.4, 33.5, y=U0, turn=3)
F('wardrobe', 15, 18, y=U0, turn=1); F('dresser', 34, 13.9, y=U0, turn=0)
# the study (x 13..58, z -8..11)
F('desk', 44, 1.5, y=U0, turn=0); F('officechair', 44, 6, y=U0)
F('bookcase', 56.6, -4, y=U0, turn=3); F('bookcase', 40, 9.7, y=U0, turn=2)
F('filing', 15.5, 8, y=U0, turn=1); F('sofa2', 26, -4.4, y=U0, turn=0)
# the playroom (x 13..58, z -40..-9)
F('pooltable', 44, -26, y=U0, turn=0)
F('media', 15.8, -32, y=U0, turn=1); F('tvwall', 13.4, -32, y=U0 + 4.5, turn=1)
F('console', 18.8, -32, y=U0, turn=1, solid=False)
F('sofa2', 24.5, -32, y=U0, turn=3)
F('toychest', 55.5, -36, y=U0, turn=3); F('beanbag', 28, -14, y=U0); F('shelfwide', 50, -10.3, y=U0, turn=2)
# the family bathroom (x -12..12, z -40..-24)
F('bathtub', 4.5, -36.5, y=U0, turn=1); F('vanity', -10, -30, y=U0, turn=1); F('toilet', -9.5, -38, y=U0, turn=1)
# ---------------------------------------------------------------- the patio (x -60..52, z -64..-42) and the garden
STORE = [   # the three store tables: tab, centre x, z (they face +z, the house)
    ('vip', -46.0, -55.0), ('coins', -31.0, -55.0), ('cases', -16.0, -55.0)]
for (_, tx, tz) in STORE:
    F('storetable', tx, tz, y=PATIO, turn=0)
# the pergola over the store tables: six posts, beams and rafters at 10.5..12 (the kit), the posts' hit boxes here
PERGOLA = dict(x0=-57.0, x1=-6.0, z0=-63.0, z1=-45.5, top=12.0)
for px in (PERGOLA['x0'], (PERGOLA['x0'] + PERGOLA['x1']) / 2, PERGOLA['x1']):
    for pz in (PERGOLA['z0'], PERGOLA['z1']):
        box(px - 0.9, PATIO, pz - 0.9, px + 0.9, 10.5, pz + 0.9, 'post')
F('grill', 34, -61, y=PATIO, turn=0)
F('patiotable', 26, -50, y=PATIO); F('patiochair', 22, -50, y=PATIO, turn=1); F('patiochair', 30, -50, y=PATIO, turn=3)
F('lounger', 40, -50, y=PATIO, turn=0)
TRAMP = dict(x=-34.0, z=-104.0, r=13.0, top=2.6, y=GROUND)      # the trampoline: its mat's centre, radius, top (HuntBuild's
F('trampoline', TRAMP['x'], TRAMP['z'], y=GROUND)              #  round mat and padded ring are the hit shapes)
F('tree', 54.0, -118.0, y=GROUND); F('treebench', 54.0, -118.0, y=GROUND)
F('swingset', 4.0, -108.0, y=GROUND, turn=0)                  # two swings (HubSeat seats on them: HuntBuild)
SWINGS = [(0.0, GROUND + 2.6, -108.0), (8.0, GROUND + 2.6, -108.0)]
F('shed', 90.0, -140.0, y=GROUND, turn=0)
F('flowerbed', -60, -150, y=GROUND, turn=0); F('flowerbed', -20, -150, y=GROUND, turn=0); F('flowerbed', 20, -150, y=GROUND, turn=0)
F('flowerbed', -82, -120, y=GROUND, turn=1); F('flowerbed', -82, -84, y=GROUND, turn=1)
F('hose', 58, -46, y=PATIO)
for hx in (-40, 0, 40, 60):                      # hedges along the back fence, between the flower beds
    F('hedge', hx, -149.5, y=GROUND)
F('flowerbed', 40, -128, y=GROUND, turn=0); F('flowerbed', 40, -136, y=GROUND, turn=0)
# ---------------------------------------------------------------- the front
F('tree', -44.0, 64.0, y=GROUND); F('hedge', -40, 77.5, y=GROUND); F('hedge', -18, 77.5, y=GROUND)
F('hedge', 22, 77.5, y=GROUND); F('hedge', 44, 77.5, y=GROUND)
F('mailbox', -6.5, 78.5, y=GROUND)
F('hoop', 82, 42.4, y=0.0, turn=0)
F('bins', 106, 46, y=GROUND, turn=3)

# ================================================================ the markers HuntBuild reads (roblox/docs/HUNT.md)
SPAWNS = []       # (x, y, z, face x, face z): inside, round the hall, the living room, the family room and the dining room
for (x, z) in ((-4, 30), (4, 13), (-6, 18), (-2, 10)): SPAWNS.append((x, G0, z, 0, -1))
for (x, z) in ((-26, 30), (-26, 12), (-50, 28), (-50, 14)): SPAWNS.append((x, G0, z, -1, 0))
for (x, z) in ((-30, -10), (-50, -32), (-18, -14), (-34, -36)): SPAWNS.append((x, G0, z, 0, 1))
for (x, z) in ((24, 34), (46, 34), (24, 10), (46, 10)): SPAWNS.append((x, G0, z, 0, -1))
EXIT = dict(door='front', at=(0.0, G0, 46.0))            # the front door: BACK TO HUB (on the porch, just outside it)
BOARD = dict(at=(-11.6, G0 + 6.4, 9.0), face=(1, 0, 0), size=(9, 6))    # the round board, on the hall's west wall
SWITCHES = []     # (room, x, y, z, face x, face z): a light switch by each room's door, 4.6 over its floor
def sw(rid, x, z, fx, fz):
    lv = [r for r in ROOMS if r['id'] == rid][0]['lv']
    SWITCHES.append((rid, float(x), LVY[lv] + (4.6 if rid != 'garage' else 3.6), float(z), fx, fz))
sw('entry', 6.0, 39.9, 0, -1); sw('living', -13.1, 12.5, -1, 0); sw('family', -13.1, -15.5, -1, 0); sw('wc', -4.6, -1.5, -1, 0)
sw('coats', 4.6, -1.5, 1, 0); sw('backhall', -5.5, -39.9, 0, 1); sw('dining', 13.1, 17, 1, 0); sw('kitchen', 13.1, -17.5, 1, 0)
sw('garage', 60.1, 0.5, 1, 0)
sw('gallery', -11.9, 15, 1, 0); sw('mainbed', -13.1, 27.5, -1, 0); sw('ensuite', -45.5, 8.9, 0, -1); sw('closet', -19.5, 8.9, 0, -1)
sw('kidsbed', -13.1, -14, -1, 0); sw('guestbed', 13.1, 31.5, 1, 0); sw('study', 13.1, 3.5, 1, 0); sw('playroom', 13.1, -14.5, 1, 0)
sw('bath', 4.5, -24.1, 0, -1)
GARAGE_BUTTON = (60.1, PATIO + 4.6, 30.0, 1, 0)
PROPS = [   # the interactables: (kind, x, y, z, room)
    ('tv', -57.4, 7.0, 21.0, 'living'), ('tv', -57.4, 4.5, -10.0, 'family'), ('tv', 13.6, U0 + 4.5, -32.0, 'playroom'),
    ('tap', 28.0, 5.4, -39.0, 'kitchen'), ('tap', -11.6, 5.0, 1.0, 'wc'), ('tap', -57.6, U0 + 5.0, 3.0, 'ensuite'),
    ('tap', -11.6, U0 + 5.0, -30.0, 'bath'), ('tap', 4.5, U0 + 3.6, -39.4, 'bath'), ('tap', -47.0, U0 + 3.6, -7.6, 'ensuite'),
    ('fridge', 55.5, 0.0, 0.5, 'kitchen'), ('toilet', -9.5, 0.0, -10.8, 'wc'), ('toilet', -38.5, U0, 5.5, 'ensuite'),
    ('toilet', -9.5, U0, -38.0, 'bath'), ('ball', 84.0, PATIO + 1.6, 64.0, 'driveway'), ('piano', -15.1, 0.0, 7.0, 'living'),
]
BOUNCY = ['bedking', 'beddouble', 'bunk']      # beds you can bounce on (a soft Trampoline)
ZONE = (LOT[0], -8.0, LOT[1], LOT[2], 160.0, LOT[3])    # the HuntZone box (x0, y0, z0, x1, y1, z1)

# ================================================================ lights: one ceiling fitting per room (two in big rooms)
LIGHTS = []       # (room, x, y, z, brightness, range, colour)
for r in ROOMS:
    if not r['light']: continue
    x0, z0, x1, z1 = r['r']
    y = LVY[r['lv']] + CLEAR - (0.8 if r['id'] != 'garage' else 0.6) + (1.0 if r['id'] == 'garage' else 0.0)
    big = (x1 - x0) * (z1 - z0) > 900
    spots = [((x0 + x1) / 2, (z0 + z1) / 2)] if not big else (
        [((x0 + x1) / 2, z0 + (z1 - z0) * 0.28), ((x0 + x1) / 2, z0 + (z1 - z0) * 0.72)] if (z1 - z0) >= (x1 - x0)
        else [(x0 + (x1 - x0) * 0.28, (z0 + z1) / 2), (x0 + (x1 - x0) * 0.72, (z0 + z1) / 2)])
    if r['id'] == 'gallery': spots = [(-4.0, 0.0), (-4.0, 34.0)]
    if r['id'] == 'entry': spots = [(-4.0, 22.0)]
    for (x, z) in spots:
        LIGHTS.append((r['id'], x, y, z, 0.9, 26.0 if r['id'] != 'garage' else 32.0, 'ffe6c8' if r['id'] != 'garage' else 'f2f0ea'))
LIGHTS.append(('porch', 0.0, 11.2, 47.0, 0.8, 18.0, 'ffd9a8'))
LIGHTS.append(('patio', -40.0, 9.8, -52.0, 0.7, 24.0, 'ffd9a8'))

# ================================================================ checks
def floor_at(x, z, y, tol=1.2):
    best = None
    for b in SOLID:
        if b[0] - 1e-6 <= x <= b[3] + 1e-6 and b[2] - 1e-6 <= z <= b[5] + 1e-6 and -tol <= y - b[4] <= tol:
            best = b[4] if best is None else max(best, b[4])
    return best

def blocked_pt(x, y, z, r=1.0, h0=0.6, h1=5.0):
    for b in SOLID:
        if b[6] == 'invis': continue
        if b[0] < x + r and b[3] > x - r and b[2] < z + r and b[5] > z - r and b[1] < y + h1 and b[4] > y + h0:
            return b
    return None

def door_clear():
    """every door leaf's swing: nothing solid within its sweep (the leaf's length round the hinge), floor to 8 up"""
    bad = []
    for d in DOORS:
        if d['kind'] in ('slide',): continue
        ln = d['a1'] - d['a0']
        hx = d['a0'] if d['hinge'] == 'a0' else d['a1']
        for k in range(1, 7):
            t = math.radians(90.0 * k / 6)
            s = 1 if d['hinge'] == 'a0' else -1
            u = hx + s * ln * 0.85 * math.cos(t)
            v = d['line'] + d['swing'] * ln * 0.85 * math.sin(t)
            x, z = (u, v) if d['axis'] == 'x' else (v, u)
            b = blocked_pt(x, d['y0'], z, 0.4, 0.3, 7.5)
            if b and b[6] not in ('grass', 'pavers', 'slab'):
                bad.append((d['id'], round(x, 1), round(z, 1), b[6])); break
    return bad

def spawn_check():
    bad = []
    for (x, y, z, *_r) in SPAWNS:
        f = floor_at(x, z, y)
        if f is None or blocked_pt(x, y, z, 1.4): bad.append((x, y, z, f, blocked_pt(x, y, z, 1.4)))
    return bad

def walk_check():
    """per floor: 1-stud cells with a floor near the storey's height and nothing from 0.6 to 5 up; a flood from the hall
    (ground) and from the stair's top (upper). every room should be mostly reached"""
    import collections
    miss, info = [], []
    for lv, y in (('G', G0), ('U', U0)):
        floor, occ = set(), set()
        for b in SOLID:
            x0, y0, z0, x1, y1, z1, m = b
            if m == 'invis': continue
            if y - 1.6 <= y1 <= y + 0.05 and not (y0 > y1 - 0.2 and m in ('rail',)):
                for i in range(int(math.floor(x0)), int(math.ceil(x1))):
                    for j in range(int(math.floor(z0)), int(math.ceil(z1))):
                        if x0 <= i + 0.5 <= x1 and z0 <= j + 0.5 <= z1: floor.add((i, j))
            if y1 > y + 0.6 + (1.0 if m == 'stair' else 0.0) and y0 < y + 5.0:
                for i in range(int(math.floor(x0 + 0.05)), int(math.ceil(x1 - 0.05))):
                    for j in range(int(math.floor(z0 + 0.05)), int(math.ceil(z1 - 0.05))): occ.add((i, j))
        free = floor - occ
        seeds = [(0, 30)] if lv == 'G' else [(0, 14), (-4, 16)]
        seen = set(s for s in seeds if s in free)
        q = collections.deque(seen)
        while q:
            i, j = q.popleft()
            for (a, b) in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if (a, b) in free and (a, b) not in seen: seen.add((a, b)); q.append((a, b))
        for r in ROOMS:
            if r['lv'] != lv: continue
            x0, z0, x1, z1 = (int(math.floor(v)) for v in r['r'])
            cells = [(i, j) for i in range(x0, x1) for j in range(z0, z1) if (i, j) in free]
            got = sum(1 for c in cells if c in seen)
            if not cells or got < 0.5 * len(cells): miss.append((lv, r['id'], got, len(cells)))
        info.append('%s: %d free cells, %d reached' % (lv, len(free), len(seen)))
    return miss, info

if __name__ == '__main__':
    print('solid %d, turned %d, tilted %d, doors %d, windows %d, furniture %d, spawns %d, lights %d' % (
        len(SOLID), len(ROT), len(TILT), len(DOORS), len(WINDOWS), len(FURN), len(SPAWNS), len(LIGHTS)))
    print('SPAWN PROBLEMS', spawn_check())
    print('DOOR SWINGS BLOCKED', door_clear())
    m, info = walk_check()
    print('\n'.join(info))
    print('ROOMS NOT REACHED %d %s' % (len(m), m))
