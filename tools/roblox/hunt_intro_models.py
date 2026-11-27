# HOUSE HUNT (27 Nov 2026; roblox/docs/HUNT.md section 11): the gunman's intro kit. Two small rooms on the same
# beats, swappable (the owner: "we can try both"). No mask (the owner, 27 Nov: "No mask for the killer!"):
#   hiA_room / hiA_props   A, their bedroom: the only light is a PC screen
#   hiB_room / hiB_props   B, an attic: the only light is an old TV showing static
# Each room stands round the gunman's feet at the origin, facing -z, the screen in front of him at z -6. The screens
# are not in the kit: each is one plain Part the client makes from HuntIntroData (its size, where it stands, its light),
# so swapping a room's light source is a data change.
# The guardrails (main, 27 Nov): plain props only, nothing on the walls that reads as a real-world symbol, poster or
# message; nothing readable on a screen; no gun anywhere.
# writes roblox/src/shared/HuntIntroData.luau (the rooms' screens, the actor's spot) and the kit:
# run: blender -b --factory-startup -P tools/roblox/hunt_intro_models.py -- <out dir> [<preview dir>] [--no-glb]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import arenakit as K
from arenakit import Tr, Ry, Rx

OUT_DIR = K.ARGS[0] if K.ARGS else os.path.join(K.HERE, 'out_huntintro')
PREVIEW = K.ARGS[1] if len(K.ARGS) > 1 else None
DATA = os.path.normpath(os.path.join(K.HERE, '..', '..', 'roblox', 'src', 'shared', 'HuntIntroData.luau'))

# quiet colours (they read near black in the intro's dark anyway; the screen's glow picks out the shapes)
WALL_A, FLOOR_A, CEIL_A, TRIM = '7d838b', '6f6258', 'b4b0a8', 'c9c5bc'
WOOD, WOOD2, DARK, STEEL = '6b5443', '57463a', '2c2e33', '8d9297'
DUVET, PILLOW, CARPET = '5d6671', 'b8b3a8', '4f4c49'
BEAM, BOARDS, PLASTER_B = '5e4c3c', '73624f', '8a847a'
BOX, BOX2, SHEET = 'a08a6c', '8c7a60', 'b9b4a8'

ROOM = dict(x0=-8.0, x1=8.0, z0=-7.0, z1=7.0, h=10.0)

# ---------------------------------------------------------------- A: their bedroom
def shell(prefix, wall, floor, ceil):
    m = prefix + '_room'
    x0, x1, z0, z1, h = ROOM['x0'], ROOM['x1'], ROOM['z0'], ROOM['z1'], ROOM['h']
    K.B(m, floor, x0 - 0.5, -0.5, z0 - 0.5, x1 + 0.5, 0.0, z1 + 0.5, bev=0.0, flat=True)
    K.B(m, ceil, x0 - 0.5, h, z0 - 0.5, x1 + 0.5, h + 0.5, z1 + 0.5, bev=0.0, flat=True)
    for (a, b, c, d) in ((x0 - 0.5, z0 - 0.5, x1 + 0.5, z0), (x0 - 0.5, z1, x1 + 0.5, z1 + 0.5), (x0 - 0.5, z0, x0, z1), (x1, z0, x1 + 0.5, z1)):
        K.B(m, wall, a, 0, b, c, h, d, bev=0.0, flat=True)
    for (a, b, c, d) in ((x0, z0, x1, z0 + 0.25), (x0, z1 - 0.25, x1, z1), (x0, z0, x0 + 0.25, z1), (x1 - 0.25, z0, x1, z1)):
        K.B(m, TRIM, a, 0, b, c, 0.7, d, bev=0.06, segs=1)                # skirting

def room_a():
    shell('hiA', WALL_A, FLOOR_A, CEIL_A)
    p = 'hiA_props'
    K.B(p, CARPET, -4.5, 0.0, -3.5, 4.5, 0.08, 3.5, bev=0.04, segs=1)     # a plain rug
    # the desk against the front wall, the monitor on it facing the room
    K.B(p, WOOD, -4.2, 3.0, -7.0, 4.2, 3.4, -4.6, bev=0.12)
    for x in (-3.9, 3.9):
        K.B(p, WOOD2, x - 0.3, 0, -6.8, x + 0.3, 3.0, -4.8, bev=0.08)
    K.B(p, WOOD2, 1.6, 0.4, -6.8, 3.6, 3.0, -4.9, bev=0.1)                # a drawer stack
    for y in (1.0, 2.0): K.B(p, DARK, 1.8, y - 0.06, -4.92, 3.4, y + 0.06, -4.86, bev=0.02, segs=1)
    K.B(p, DARK, -1.95, 3.4, -6.3, 1.95, 3.55, -5.9, bev=0.05)            # the monitor's foot
    K.B(p, DARK, -0.2, 3.55, -6.25, 0.2, 4.4, -6.0, bev=0.06)             # its neck
    K.B(p, DARK, -2.15, 4.2, -6.25, 2.15, 6.7, -5.85, bev=0.1)            # its body (the screen Part sits on its front)
    K.B(p, DARK, -1.4, 3.42, -5.6, 1.4, 3.55, -4.9, bev=0.04, segs=1)     # the keyboard
    K.B(p, DARK, -3.3, 0.0, -6.6, -2.2, 2.4, -4.9, bev=0.1)               # the tower under the desk
    K.cyl(p, STEEL, 3.0, 3.4, -5.4, 0.3, 0.55, segs=14, bev=0.06)         # a mug
    # the office chair, its own piece at its own origin (HuntIntroData.chair: pushed back and turned in the intro, at
    # the desk in the gunman's win film)
    c = 'hiA_chair'
    K.B(c, DARK, -1.1, 2.1, -1.1, 1.1, 2.5, 1.1, bev=0.2)
    K.B(c, DARK, -1.0, 2.5, 0.75, 1.0, 5.2, 1.05, bev=0.22)
    K.cyl(c, STEEL, 0.0, 0.4, 0.0, 0.14, 1.7, segs=10, bev=0.04)
    K.cyl(c, DARK, 0.0, 0.0, 0.0, 1.1, 0.4, segs=16, bev=0.1)
    # the bed along the left wall, its head at the back
    K.B(p, WOOD, -8.0, 0.0, -1.0, -3.4, 1.4, 7.0, bev=0.15)
    K.B(p, TRIM, -7.9, 1.4, -0.9, -3.5, 2.3, 6.9, bev=0.25)               # the mattress
    K.B(p, DUVET, -7.95, 2.0, -0.95, -3.45, 2.6, 4.8, bev=0.3)            # the duvet, thrown back
    K.B(p, PILLOW, -7.4, 2.3, 5.0, -4.0, 2.9, 6.6, bev=0.3)
    K.B(p, WOOD2, -8.0, 0.0, 6.6, -3.4, 4.6, 7.0, bev=0.12)               # the headboard
    # the wardrobe on the right wall, a nightstand by the bed
    K.B(p, WOOD, 6.4, 0.0, 1.0, 8.0, 8.2, 6.4, bev=0.15)
    K.B(p, WOOD2, 6.32, 0.3, 3.66, 6.42, 7.9, 3.74, bev=0.01, segs=1)
    for z in (3.2, 4.2): K.B(p, STEEL, 6.25, 3.8, z - 0.05, 6.35, 4.6, z + 0.05, bev=0.02, segs=1)
    K.B(p, WOOD, -3.2, 0.0, 5.0, -1.4, 2.2, 7.0, bev=0.12)
    # the window on the back wall, blinds shut
    K.B(p, TRIM, -2.6, 3.6, 6.7, 2.6, 7.6, 7.0, bev=0.08)
    for k in range(9):
        y = 3.85 + k * 0.42
        K.B(p, 'aeb2b6', -2.35, y - 0.12, 6.62, 2.35, y + 0.12, 6.7, bev=0.03, segs=1)
    # the door on the right wall, shut
    K.B(p, TRIM, 7.7, 0.0, -5.6, 8.0, 7.6, -1.6, bev=0.06)
    K.B(p, WOOD2, 7.75, 0.0, -5.3, 7.95, 7.3, -1.9, bev=0.05)
    K.cyl(p, STEEL, 7.62, 3.4, -2.4, 0.12, 0.25, segs=10, bev=0.03)
    # a plain shelf of plain boxes over the bed
    K.B(p, WOOD, -8.0, 5.6, 1.0, -6.9, 5.8, 5.0, bev=0.05)
    for (z, w, hh, col) in ((1.6, 0.9, 1.0, BOX), (2.8, 1.1, 0.8, BOX2), (4.1, 0.8, 1.2, BOX)):
        K.B(p, col, -7.9, 5.8, z - w / 2, -7.0, 5.8 + hh, z + w / 2, bev=0.08)

# ---------------------------------------------------------------- B: an attic
def room_b():
    m, p = 'hiB_room', 'hiB_props'
    x0, x1, z0, z1 = ROOM['x0'], ROOM['x1'], ROOM['z0'], ROOM['z1']
    K.B(m, BOARDS, x0 - 0.5, -0.5, z0 - 0.5, x1 + 0.5, 0.0, z1 + 0.5, bev=0.0, flat=True)
    for k in range(9):                                                     # the floor's board joints
        x = x0 + 1.75 * (k + 0.5)
        K.B(p, '5b4d3e', x - 0.03, 0.0, z0, x + 0.03, 0.02, z1, bev=0.0, flat=True)
    # the roof: two slopes from the knee walls (2.5 up at x +-8) to the ridge (11 up), boarded under the rafters
    eave, ridge = 2.5, 11.0
    ang = math.atan2(ridge - eave, 8.0)
    ln = math.hypot(8.0, ridge - eave)
    for sx in (-1, 1):
        M = Tr(sx * 8.0, eave, 0) @ K.Rz(-sx * ang) @ Tr(-sx * ln / 2, 0, 0)
        K.B(m, PLASTER_B, -ln / 2 - 0.3, 0.0, z0 - 0.5, ln / 2 + 0.3, 0.4, z1 + 0.5, bev=0.0, flat=True, M=M)
        K.B(m, PLASTER_B, sx * 8.0 - 0.25, 0.0, z0, sx * 8.0 + 0.25, eave, z1, bev=0.0, flat=True)   # the knee wall
        for z in [z0 + 0.6 + 2.5 * k for k in range(6)]:                   # rafters
            K.B(p, BEAM, -ln / 2, -0.7, z - 0.3, ln / 2, 0.0, z + 0.3, bev=0.1, M=M)
    for z in (z0 + 0.6 + 2.5 * 1, z0 + 0.6 + 2.5 * 4):                     # collar ties
        K.B(p, BEAM, -3.2, 8.0, z - 0.25, 3.2, 8.6, z + 0.25, bev=0.1)
    K.B(p, BEAM, -0.35, 10.3, z0, 0.35, 11.0, z1, bev=0.1)                  # the ridge beam
    for sz, zz in ((-1, z0), (1, z1)):                                     # the gable ends
        K.plate(m, PLASTER_B, [(-8.5, 0.0), (8.5, 0.0), (8.5, eave), (0.0, ridge + 0.4), (-8.5, eave)], 0.5,
                Tr(0, 0, zz if sz > 0 else zz - 0.5), bev=0.0)
    # a small round window high in the back gable, dark
    K.B(p, '25282d', -0.9, 5.4, z1 - 0.08, 0.9, 7.2, z1, bev=0.3)
    K.B(p, TRIM, -1.1, 5.2, z1 - 0.12, 1.1, 5.4, z1, bev=0.06, segs=1)
    # the old TV on a crate in front of him (the screen Part sits on its front)
    K.B(p, WOOD2, -2.2, 0.0, -7.0, 2.2, 2.4, -4.8, bev=0.12)               # the crate
    for x in (-2.2, 2.2): K.B(p, WOOD, x - 0.12, 0.0, -7.0, x + 0.12, 2.4, -4.8, bev=0.04)
    K.B(p, '4a4744', -2.0, 2.4, -6.9, 2.0, 5.6, -4.6, bev=0.45)            # the TV's deep body
    K.B(p, '3a3836', -1.75, 2.7, -4.75, 1.75, 5.3, -4.55, bev=0.2)         # its bezel
    for x in (-0.5, 0.5): K.cyl(p, '4a4744', x, 5.6, -5.8, 0.06, 1.2 + 0.3 * x, segs=6, bev=0.02)   # rabbit-ear stubs
    # boxes, a trunk, a sheeted armchair, a rolled rug, a lamp with no shade
    for (x, z, w, d, hh, col) in ((-6.4, -5.6, 2.4, 2.0, 1.8, BOX), (-6.2, -5.4, 1.8, 1.6, 1.4, BOX2), (6.0, -5.8, 2.6, 2.2, 2.0, BOX2),
                                  (6.4, -3.4, 2.0, 1.8, 1.5, BOX), (-6.6, 4.8, 2.4, 2.4, 2.2, BOX2), (5.8, 5.4, 2.8, 2.0, 1.6, BOX)):
        y0 = 0.0 if (x, z) != (-6.2, -5.4) else 1.8
        K.B(p, col, x - w / 2, y0, z - d / 2, x + w / 2, y0 + hh, z + d / 2, bev=0.08)
    K.B(p, WOOD, 2.6, 0.0, 4.6, 5.6, 1.8, 6.4, bev=0.18)                   # the trunk
    K.B(p, STEEL, 2.6, 1.0, 5.45, 5.6, 1.2, 5.55, bev=0.03, segs=1)
    K.B(p, SHEET, -5.4, 0.0, 0.2, -2.6, 2.4, 3.0, bev=0.7)                 # the armchair under a sheet
    K.B(p, SHEET, -5.4, 1.6, 2.2, -2.6, 4.2, 3.1, bev=0.5)
    K.cylx(p, '6e5a48', 2.4, 6.2, 0.5, -1.6, 0.5, segs=14, bev=0.1)        # a rolled rug along the right
    K.cyl(p, STEEL, 4.4, 0.0, 1.8, 0.7, 0.2, segs=14, bev=0.05)            # a lamp stand with no shade
    K.cyl(p, STEEL, 4.4, 0.2, 1.8, 0.08, 4.6, segs=8, bev=0.02)

# ---------------------------------------------------------------- the win films' pieces (27 Nov, the owner's endings)
def win_pieces():
    # the friends' couch in the attic (only in the hiders' win film), at its own origin, facing -z (the TV): a worn
    # two-seater with a blanket over one arm
    c = 'hiB_couch'
    FAB, CUSH, BLANKET = '7a6f63', '8b8073', '5f6b73'
    K.B(c, FAB, -3.0, 0.3, -1.4, 3.0, 1.5, 1.4, bev=0.35)                 # the base
    for x0 in (-2.6, 0.05):
        K.B(c, CUSH, x0, 1.5, -1.3, x0 + 2.55, 2.1, 1.0, bev=0.3)          # the seat cushions
    K.B(c, FAB, -3.0, 1.5, 0.9, 3.0, 4.0, 1.4, bev=0.4)                   # the back
    for sx in (-1, 1):
        K.B(c, FAB, sx * 3.0 - (0.7 if sx > 0 else 0), 0.3, -1.4, sx * 3.0 + (0.0 if sx > 0 else 0.7), 2.8, 1.4, bev=0.35)   # the arms
        K.B(c, WOOD2, sx * 2.6 - 0.2, 0.0, -1.2, sx * 2.6 + 0.2, 0.3, -0.8, bev=0.06)   # the feet
        K.B(c, WOOD2, sx * 2.6 - 0.2, 0.0, 0.8, sx * 2.6 + 0.2, 0.3, 1.2, bev=0.06)
    K.B(c, BLANKET, 2.3, 1.6, -1.45, 3.05, 2.9, 1.2, bev=0.3)              # a blanket over the right arm
    # a game controller (each friend holds one: welded to the right hand), at its own origin: chunky, plain, no marks
    g = 'hiB_pad'
    K.B(g, '3a3d42', -0.55, -0.12, -0.3, 0.55, 0.12, 0.25, bev=0.1)
    for sx in (-1, 1):
        K.cyl(g, '3a3d42', sx * 0.45, -0.12, 0.25, 0.2, 0.24, segs=12, bev=0.06)
        K.cyl(g, '8d9297', sx * 0.28, 0.12, -0.08, 0.08, 0.05, segs=10, bev=0.02)
    # a sofa cushion knocked to the floor (the gunman's win walk through the wrecked house)
    K.B('hiW_cushion', '8b8073', -1.2, 0.0, -1.0, 1.2, 0.6, 1.0, bev=0.28)

# ---------------------------------------------------------------- the data the client reads
SCREENS = {
    # where the light comes from: one Part (centre, size, facing +z = toward the actor), its colour and its light
    'A': dict(at=(0.0, 5.45, -5.83), size=(3.9, 2.25, 0.06), col='9fc4ff', light=('surface', 1.1, 16, 'b8d4ff')),   # (27 Nov test: 2.6 blew out)
    'B': dict(at=(0.0, 4.0, -4.53), size=(3.2, 2.3, 0.06), col='c8ccd2', light=('surface', 1.0, 15, 'e4e8f0')),
}
ACTOR = (0.0, 0.0, 0.0)
# where each piece sits in the kit (apart, so the previews and Studio's import don't overlap): the client moves a room
# by -origin to put the actor's feet at its spot
ORIGIN = {'hiA': (0.0, 0.0, 0.0), 'hiB': (40.0, 0.0, 0.0)}
# the pieces that stand at their own origin (the client places them from the spots below; the kit keeps each at its
# room's origin: hiA_chair at A's, hiB_couch and hiB_pad at B's, hiW_cushion at none)
PIECES = {'hiA_chair': 'hiA', 'hiB_couch': 'hiB', 'hiB_pad': 'hiB', 'hiW_cushion': None}
# spots in the rooms' own space: (x, y, z, yaw degrees); a seat is where the sitter's hips go
SPOTS = {
    'chairIntro': (2.8, 0.0, -2.6, -28.0),      # A: the chair pushed back and turned (the intro)
    'chairDesk': (0.0, 0.0, -2.9, 0.0),         # A: the chair at the desk (the gunman's win)
    'deskSeat': (0.0, 2.5, -2.95, 0.0),         # A: his hips on it, facing the screen
    'couch': (0.6, 0.0, 2.8, 0.0),              # B: the friends' couch, facing the TV
    'seat1': (-0.72, 2.1, 2.65, 0.0), 'seat2': (1.92, 2.1, 2.65, 0.0),   # B: its two seats
    'seat3': (-4.0, 2.4, 1.6, 14.0),            # B: the sheeted armchair
    'stand1': (-1.6, 0.0, 5.4, 6.0), 'stand2': (1.2, 0.0, 5.6, -8.0), 'stand3': (-3.8, 0.0, 4.7, 16.0),   # behind it
}

def write_data():
    def v3(t): return 'Vector3.new(%s)' % ', '.join(K.fmt(v) for v in t)
    o = ['--!strict', '-- GENERATED by tools/roblox/hunt_intro_models.py (HOUSE HUNT\'s gunman intro, roblox/docs/HUNT.md section 11).',
         '-- Studs in the room\'s own space: the actor\'s feet at the origin, facing -z; the screen in front of him.', 'return {',
         '\tactor = %s,' % v3(ACTOR), '\troom = { w = 16, d = 14, h = 10 },',
         '	origin = { A = %s, B = %s },' % (v3(ORIGIN['hiA']), v3(ORIGIN['hiB'])),
         '\tscreens = {']
    for k, s in SCREENS.items():
        lk, lb, lr, lc = s['light']
        o.append('\t\t%s = { at = %s, size = %s, col = "%s", light = { kind = "%s", brightness = %s, range = %s, col = "%s" } },' % (
            k, v3(s['at']), v3(s['size']), s['col'], lk, K.fmt(lb), K.fmt(lr), lc))
    o.append('\t},')
    o.append('\tpieces = { %s },' % ', '.join('%s = %s' % (k, ('"%s"' % v[2:]) if v else 'false') for k, v in PIECES.items()))
    o.append('\tspots = {')
    for k, (x, y, z, yaw) in SPOTS.items():
        o.append('\t\t%s = { %s, %s, %s, %s },' % (k, K.fmt(x), K.fmt(y), K.fmt(z), K.fmt(yaw)))
    o.append('\t},')
    o.append('}')
    with open(DATA, 'w', encoding='utf-8', newline='\n') as f: f.write('\n'.join(o) + '\n')
    print('WROTE', DATA)

for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
room_a(); room_b(); win_pieces()
# move each piece to its own spot in the kit
for (model, key), items in list(K.PIECES.items()):
    o = next((v for k, v in ORIGIN.items() if model.startswith(k + '_') or model == k), (0.0, 0.0, 0.0))
    if o != (0.0, 0.0, 0.0):
        K.PIECES[(model, key)] = [(bm, Tr(*o) @ M) for (bm, M) in items]
write_data()
# (previews only: the screens' glow, so the closed rooms aren't black)
if PREVIEW:
    for k, s in SCREENS.items():
        o = ORIGIN['hi' + k]
        col = s['light'][3]
        ld = bpy.data.lights.new('l', 'POINT'); ld.energy = 900.0; ld.shadow_soft_size = 1.2
        ld.color = [int(col[j:j + 2], 16) / 255 for j in (0, 2, 4)]
        ob = bpy.data.objects.new('l', ld); bpy.context.scene.collection.objects.link(ob)
        ob.location = (K.P @ Vector((s['at'][0] + o[0], s['at'][1] + o[1], s['at'][2] + 1.0 + o[2], 1))).xyz
VIEWS = [
    ('roomA', (5.5, 4.5, 6.5), (0, 3.5, -3), 22),
    ('roomB', (40 + 2.6, 5.0, 6.2), (40, 3.4, -3), 22),
]
K.finish('hunt_intro', OUT_DIR, PREVIEW, VIEWS if PREVIEW else (), prefix='intro')
