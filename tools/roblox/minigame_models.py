# THE HUB'S MINI-GAMES (18 Nov 2026, the owner: "At the tables for the lobby hub can you add mini games that can actually
# be played, like arm wrestling based on hitting skill checks, another table has chess/checkers, maybe the arcade machine
# you can play like a mini version of the game against bots??"). the furniture and the pieces, the chunky way: few big
# rounded shapes, flat matte mid-value colours, nothing near-black, no metal; pieces that read as one fused form
# (the knight's head and the king's cross are remeshed into their bodies: no stuck-on primitives).
# 1 unit = 1 stud, Z up, a model's front faces -Y (Roblox +Z after the import), the floor is z 0. In Roblox terms
# (X, Y, Z) = (x, z, -y). studio-tools/MiniGameImport.luau builds the game templates round these (seats, the clasp,
# the board's squares, the cabinet's screen) from the same numbers (shared/MiniGames.luau LAYOUT).
#   mg_armtable    arm wrestling table: top 2.6 (x) x 2.4 (y), surface 3.25; elbow pads, pin pads, grip pegs
#   mg_stool       a round stool, seat top 2.0
#   mg_boardtable  games table 4.4 square, surface 3.0, an inlaid 8 x 8 board of 0.46 squares (surface 3.08)
#   mg_chair       a chair with a back, seat top 2.0, its back on +y (Roblox -Z: it faces Roblox +Z, like the rest)
#   mg_pawn mg_rook mg_knight mg_bishop mg_queen mg_king   chess pieces (base radius ~0.17, 0.40 to 0.72 tall)
#   mg_man         a checkers piece (radius 0.19, 0.1 tall); a king is two stacked
#   mg_cabinet     the arcade cabinet: 3.4 wide, 2.8 deep, 7.6 tall; screen recess and a lit marquee on its front
# run: blender -b --factory-startup -P tools/roblox/minigame_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *
import bpy

WOOD, WOOD2, WOODD = 'a48f6c', '8c7758', '6f5b45'
SLATE, SLATE2, DARK = '68707c', '5a616d', '4c535e'
CREAM, CREAM2, PAD = 'c4bfb5', 'b3aea4', '5c5f66'
SQ_L, SQ_D, FRAME = 'd6cdb9', '806a55', '5e4b3a'
IVORY = 'e6e0d4'
LIGHT, ACCENT = 'f2ede4', 'e0ac3c'
reset()

def fuse(model, voxel=0.012, ratio=0.35):
    """the last kept model as ONE fused form: voxel remesh (joins filleted), smoothed, then thinned"""
    _, objs, _, _ = MODELS[-1]
    for o in objs:
        rm = o.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = voxel; rm.use_smooth_shade = True
        sm = o.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.6; sm.iterations = 4
        dc = o.modifiers.new('dc', 'DECIMATE'); dc.ratio = ratio
        # the weighted normal (added by keep) goes last
        wn = o.modifiers.get('wn')
        if wn: o.modifiers.move(o.modifiers.find('wn'), len(o.modifiers) - 1)

# ------------------------------------------------------------------ mg_armtable
TOP_A = 3.25
soft('plastic', WOOD, 2.6, 2.4, 0.36, 0, 0, TOP_A - 0.18, 0.16, pick='all', segs=3, small=0.0)      # the top
soft('plastic', WOOD2, 2.3, 2.1, 0.2, 0, 0, TOP_A - 0.44, 0.08, pick='all', segs=2, small=0.0)      # its apron
cy('plastic', SLATE, 0.42, TOP_A - 0.55, 0, 0, (TOP_A - 0.55) / 2 + 0.3, segs=28, bevel=0.1)       # the column
lathe('plastic', SLATE2, dome_prof(1.15, 0.25, rim=0.12, steps=5), segs=36)                          # the foot
for sx, sy in ((1, 1), (-1, -1)):                                                                    # elbow pads (Roblox z = -y)
    soft('plastic', PAD, 0.78, 0.78, 0.16, 0.2 * sx, -0.75 * sy, TOP_A + 0.06, 0.07, pick='all', segs=2, small=0.0)
for sx in (1, -1):                                                                                   # pin pads
    soft('plastic', PAD, 0.62, 0.95, 0.14, 1.0 * sx, 0, TOP_A + 0.05, 0.06, pick='all', segs=2, small=0.0)
for sx, sy in ((-1, 1), (1, -1)):                                                                    # grip pegs
    cy('plastic', SLATE2, 0.11, 0.62, 1.1 * sx, -0.8 * sy, TOP_A + 0.31, segs=16, bevel=0.05)
    ball('plastic', SLATE2, 0.15, 1.1 * sx, -0.8 * sy, TOP_A + 0.64, sub=2)
keep('mg_armtable')

# ------------------------------------------------------------------ mg_stool
SEAT = 2.0
lathe('plastic', PAD, dome_prof(0.95, 0.16, rim=0.18, steps=5), M=T(0, 0, SEAT - 0.34), segs=32)  # the cushion
cy('plastic', WOOD2, 0.98, 0.16, 0, 0, SEAT - 0.42, segs=32, bevel=0.06)                           # its pan
cy('plastic', SLATE, 0.2, SEAT - 0.5, 0, 0, (SEAT - 0.5) / 2 + 0.12, segs=20, bevel=0.06)
lathe('plastic', SLATE2, ring_prof(0.62, 0.08, steps=8), M=T(0, 0, 0.75), segs=32, cap=False)        # the foot ring
lathe('plastic', SLATE2, dome_prof(0.75, 0.14, rim=0.08, steps=4), segs=32)                          # the foot
keep('mg_stool')

# ------------------------------------------------------------------ mg_boardtable
TOP_B = 3.0
SQ = 0.46
soft('plastic', WOOD, 4.4, 4.4, 0.32, 0, 0, TOP_B - 0.16, 0.16, pick='all', segs=3, small=0.0)
soft('plastic', FRAME, 4.08, 4.08, 0.12, 0, 0, TOP_B + 0.02, 0.05, pick='all', segs=2, small=0.0)   # the board's frame
for i in range(8):
    for j in range(8):
        dark = (i + j) % 2 == 0          # (a1, at i 0 j 0, is a dark square)
        x = (i - 3.5) * SQ
        y = (j - 3.5) * SQ
        bx('plastic', SQ_D if dark else SQ_L, SQ - 0.012, SQ - 0.012, 0.08, x, y, TOP_B + 0.06, bevel=0.012)   # (tops 0.02 over the frame's)
for sx in (1, -1):
    for sy in (1, -1):
        soft('plastic', SLATE, 0.34, 0.34, TOP_B - 0.3, 1.75 * sx, 1.75 * sy, (TOP_B - 0.3) / 2, 0.12, pick='up', segs=2, small=0.04)
soft('plastic', WOOD2, 3.9, 3.9, 0.22, 0, 0, TOP_B - 0.42, 0.08, pick='all', segs=2, small=0.0)      # the apron
keep('mg_boardtable')

# ------------------------------------------------------------------ mg_chair (faces -y = Roblox +Z)
soft('plastic', WOOD2, 1.9, 1.8, 0.2, 0, 0, SEAT - 0.32, 0.08, pick='all', segs=2, small=0.0)
soft('plastic', PAD, 1.75, 1.65, 0.24, 0, -0.02, SEAT - 0.12, 0.1, pick='all', segs=3, small=0.0)
soft('plastic', WOOD2, 1.9, 0.26, 2.2, 0, 0.82, SEAT + 0.9, 0.1, pick='all', segs=2, small=0.02)     # the back
soft('plastic', PAD, 1.6, 0.16, 1.3, 0, 0.66, SEAT + 1.0, 0.07, pick='all', segs=2, small=0.0)
for sx in (1, -1):
    for sy in (1, -1):
        soft('plastic', WOODD, 0.24, 0.24, SEAT - 0.4, 0.78 * sx, 0.74 * sy, (SEAT - 0.4) / 2, 0.07, pick='up', segs=2, small=0.03)
keep('mg_chair')

# ------------------------------------------------------------------ chess (white versions; the importer paints copies)
# (19 Nov 2026, the owner: "chess pieces should be easier to tell what they are"): each piece its own outline and a
# clear step in height, pawn 0.54 < rook 0.59 < knight 0.66 < bishop 0.84 < queen 0.91 < king 1.03: a pawn's big
# round head; the rook's four square battlements; the knight's head with a long snout and two ears; the bishop's tall
# mitre with its slanted slit and a bead on top; the queen's crown of beads; the king's cross. one fused form each
def base(r=0.18, h=0.1):
    return [(0.0, 0.0), (r, 0.0), (r, h * 0.5), (r * 0.92, h), (r * 0.72, h * 1.25)]

def cut_slab(sx, sy, sz, at, turn_y):
    """cut a slab out of the last kept model now (a boolean, applied), then drop the cutter: the export takes the scene"""
    ob = MODELS[-1][1][0]
    cm = bpy.data.meshes.new('cutter')
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    bm.to_mesh(cm); bm.free()
    cut = bpy.data.objects.new('cutter', cm)
    bpy.context.scene.collection.objects.link(cut)
    cut.matrix_world = Matrix.Translation(at) @ Matrix.Rotation(D(turn_y), 4, 'Y')
    wn = ob.modifiers.get('wn')
    if wn: ob.modifiers.remove(wn)
    bo = ob.modifiers.new('cut', 'BOOLEAN'); bo.operation = 'DIFFERENCE'; bo.object = cut; bo.solver = 'EXACT'
    dg = bpy.context.evaluated_depsgraph_get()
    me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    old = ob.data
    ob.data = me2
    nm = old.name
    bpy.data.meshes.remove(old)
    me2.name = nm   # (the mesh keeps its name: the importer reads the model and the colour from it)
    for p in me2.polygons: p.use_smooth = True
    w2 = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); w2.keep_sharp = False; w2.weight = 60
    bpy.data.objects.remove(cut)

# the pawn: a short neck, a collar, a big round head
lathe('plastic', IVORY, base(0.17) + [(0.085, 0.17), (0.07, 0.25), (0.115, 0.28), (0.115, 0.31), (0.07, 0.33), (0.0, 0.34)], segs=28)
ball('plastic', IVORY, 0.12, 0, 0, 0.42, sub=3)
keep('mg_pawn'); fuse('mg_pawn', voxel=0.008, ratio=0.3)
# the rook: a straight tower, a wide top and four square battlements round it
lathe('plastic', IVORY, base(0.19) + [(0.125, 0.2), (0.12, 0.42), (0.168, 0.45), (0.168, 0.5), (0.0, 0.5)], segs=32)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    bx('plastic', IVORY, 0.095, 0.095, 0.1, 0.105 * math.cos(a), 0.105 * math.sin(a), 0.54, bevel=0.015)
keep('mg_rook'); fuse('mg_rook', voxel=0.008, ratio=0.3)
# the knight: a round base and a horse's head grown out of it: a long snout forward, two ears, the mane down its back
lathe('plastic', IVORY, base(0.19) + [(0.125, 0.17), (0.0, 0.2)], segs=28)
HEAD = [(-0.12, 0.13), (0.11, 0.13), (0.12, 0.27), (0.08, 0.35), (0.17, 0.43), (0.2, 0.49), (0.16, 0.54), (0.06, 0.57),
        (0.035, 0.66), (0.0, 0.595), (-0.04, 0.66), (-0.07, 0.57), (-0.13, 0.5), (-0.16, 0.38), (-0.14, 0.24)]
prism('plastic', IVORY, HEAD, 0.17, M=RZ(D(-90)), bevel=0.035, segs=2)   # (the face looks along -y: Roblox +Z)
keep('mg_knight'); fuse('mg_knight', voxel=0.008, ratio=0.3)
# the bishop: a slim body, a collar, a tall mitre with a slanted slit cut in its front, a bead on top
lathe('plastic', IVORY, base(0.18) + [(0.09, 0.2), (0.066, 0.42), (0.118, 0.45), (0.118, 0.48), (0.07, 0.5), (0.1, 0.55),
                                      (0.108, 0.6), (0.092, 0.67), (0.055, 0.73), (0.0, 0.765)], segs=32)
ball('plastic', IVORY, 0.042, 0, 0, 0.795, sub=2)
keep('mg_bishop')
cut_slab(0.3, 0.17, 0.034, (0.02, -0.09, 0.64), -40)
fuse('mg_bishop', voxel=0.007, ratio=0.32)
# the queen: a waisted body flaring into a crown, eight beads round its rim and one on top
lathe('plastic', IVORY, base(0.19) + [(0.1, 0.22), (0.08, 0.55), (0.13, 0.59), (0.13, 0.62), (0.088, 0.65), (0.14, 0.76),
                                      (0.125, 0.78), (0.06, 0.77), (0.0, 0.8)], segs=32)
for k in range(8):
    a = k * math.pi / 4
    ball('plastic', IVORY, 0.035, 0.127 * math.cos(a), 0.127 * math.sin(a), 0.795, sub=2)
ball('plastic', IVORY, 0.06, 0, 0, 0.85, sub=2)
keep('mg_queen'); fuse('mg_queen', voxel=0.007, ratio=0.32)
# the king: the tallest, its body and a big chunky cross on top
lathe('plastic', IVORY, base(0.2) + [(0.11, 0.22), (0.09, 0.6), (0.145, 0.64), (0.145, 0.68), (0.1, 0.71), (0.135, 0.79),
                                     (0.07, 0.81), (0.0, 0.815)], segs=32)
bx('plastic', IVORY, 0.08, 0.08, 0.22, 0, 0, 0.92, bevel=0.025)
bx('plastic', IVORY, 0.21, 0.08, 0.07, 0, 0, 0.95, bevel=0.025)
keep('mg_king'); fuse('mg_king', voxel=0.008, ratio=0.3)

# ------------------------------------------------------------------ checkers
lathe('plastic', IVORY, [(0.0, 0.0), (0.19, 0.0), (0.2, 0.03), (0.2, 0.07), (0.185, 0.1), (0.13, 0.1), (0.12, 0.085),
                         (0.06, 0.085), (0.05, 0.095), (0.0, 0.095)], segs=32)
keep('mg_man')

# ------------------------------------------------------------------ mg_cabinet (front -y = Roblox +Z)
W, Dp, H = 3.4, 2.8, 7.6
F = -Dp / 2  # the front face's y
soft('plastic', SLATE2, W, Dp, 0.5, 0, 0, 0.25, 0.12, pick='all', segs=2, small=0.0)                       # plinth
soft('plastic', SLATE, W - 0.3, Dp - 0.5, 3.0, 0, 0.15, 0.5 + 1.5, 0.14, pick='up', segs=2, small=0.05)  # the lower body
soft('plastic', SLATE, W - 0.3, Dp - 1.5, 3.6, 0, 0.75, 3.5 + 1.8, 0.14, pick='up', segs=2, small=0.05)  # the upper body (its front behind the bezel)
for sx in (1, -1):                                                                                          # the side panels
    prism('plastic', CREAM2, [(-1.4, 0.0), (1.4, 0.0), (1.4, 7.6), (-0.4, 7.6), (-0.9, 6.3), (-0.5, 4.2),
                              (-1.4, 3.6)], 0.22, M=T(sx * (W / 2 - 0.11), 0, 0) @ RZ(D(90)), bevel=0.08)
# the control deck: a slab tipped toward the player, a stick and three buttons
deck = T(0, F + 0.55, 3.45) @ Matrix.Rotation(D(12), 4, 'X')   # (its back higher)
soft('plastic', DARK, W - 0.5, 1.1, 0.26, 0, 0, 0, 0.1, pick='all', segs=2, small=0.0, M=deck)
cy('plastic', CREAM, 0.06, 0.38, -0.7, 0.05, 0.3, segs=12, bevel=0.02, M=deck)
ball('plastic', ACCENT, 0.17, -0.7, 0.05, 0.52, sub=2, M=deck)
for i, (bxx, col) in enumerate(((0.25, ACCENT), (0.62, CREAM), (0.99, CREAM))):
    cy('plastic', col, 0.13, 0.12, bxx, 0.0 + (0.12 if i == 0 else 0.0), 0.16, segs=20, bevel=0.04, M=deck)
# the screen's bezel: a deep frame round a dark recess, tipped back (the game's screen part sits in it: importer)
scr = T(0, F + 1.15, 5.05) @ Matrix.Rotation(D(-14), 4, 'X')   # (its top leans away)
for (sx_, sz_, x_, z_) in ((2.95, 0.3, 0, 1.2), (2.95, 0.3, 0, -1.2), (0.3, 2.7, 1.33, 0), (0.3, 2.7, -1.33, 0)):
    soft('plastic', DARK, sx_, 0.3, sz_, x_, 0, z_, 0.08, pick='all', segs=2, small=0.0, M=scr)
bx('plastic', '3a3f48', 2.4, 0.06, 2.1, 0, 0.12, 0, bevel=0.0, M=scr)                                      # the recess
# the marquee: a lit panel in a chunky hood
soft('plastic', DARK, W - 0.4, 0.9, 1.0, 0, F + 0.95, 7.05, 0.12, pick='all', segs=2, small=0.0)
bx('neon', LIGHT, W - 0.75, 0.06, 0.66, 0, F + 0.49, 7.05, bevel=0.0)
soft('plastic', SLATE2, W, Dp - 0.6, 0.24, 0, 0.3, H - 0.12, 0.1, pick='all', segs=2, small=0.0)          # the lid
for sx in (1, -1):                                   # two cushions on the lid: seats (19 Nov: MiniGames L.arcade.topSeats)
    soft('plastic', PAD, 1.25, 1.25, 0.24, sx * 0.75, 0.3, H + 0.12, 0.1, pick='all', segs=2, small=0.0)
keep('mg_cabinet')

export_all('minigames.glb')
if len(sys.argv) > sys.argv.index('--') + 2:
    if len(sys.argv) > sys.argv.index('--') + 3:   # (a 3rd argument: only the models whose names hold it)
        want = sys.argv[sys.argv.index('--') + 3].split(',')
        for m in list(MODELS):
            if not any(w in m[0] for w in want):
                for o in m[1]: bpy.data.objects.remove(o)
                MODELS.remove(m)
    preview(sys.argv[sys.argv.index('--') + 2], cols=4, gap=1.5)
