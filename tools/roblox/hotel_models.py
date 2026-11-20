# THE HOTEL hub's kit (20 Nov 2026; the owner: "try 3 new ones, on elike the previous hub one thats like a full hotel
# look"; "by old design I meant lke the chunker structes you know? we just add subtle texture to them now"). The chunky
# structure and furniture of a hotel interior: few big shapes, every sharp edge bevelled (2 steps) under a Weighted
# Normal; the subtle textures go on the big Studio surfaces (plaster walls, stone and carpet floors, wood dado) in
# HubHotel. Vault plan: Hubs/Hotel hub plan.md. 1 unit = 1 stud, Z up, a model's front faces -Y (+Z in Roblox).
# Origins: free-standing pieces at the middle of their footprint on the floor; WALL pieces at the wall's face (y 0),
# standing out toward -Y; CEILING pieces at the ceiling's underside (z 0), hanging down.
#   ht_pier        a square pier under the mezzanine, 3.4 x 3.4 x 13.05 (base, shaft 2.6, two-step capital)
#   ht_pilaster    a wall pilaster, the full 26 (base 3.6 wide, shaft 2.8, capital 3.6; 1.0 / 1.6 proud)
#   ht_pilasterMid the same, 18 high (the ballroom's walls, under the vault)
#   ht_pilasterLow the same, 14 high (the bar, the corridors)
#   ht_cornice     a cornice run, 8 long, 2.5 high, 1.7 proud; its top at z 0 (hang it under a ceiling)
#   ht_doorS       a deep surround for an 8 x 10 opening (its foot middle at the origin): jambs, head, cap, plinths
#   ht_doorL       the same for 16 x 14 (the ballroom's doors)
#   ht_baluster    a solid parapet run, 8 long: plinth, a framed recessed field, a rounded cap; 3.4 high, 1.6 deep
#   ht_newel       a newel post, 1.8 x 1.8 x 3.9 with a cap
#   ht_coffer      a coffer cell, 14 x 16, beams 1.4 wide and 2.0 deep, a recessed lamp housing in the middle (ceiling)
#   ht_chandelier  a ring chandelier, 10 across, 4.6 down from the ceiling: brass ring, cream drum, warm lamps
#   ht_palm        a palm in a big pot, about 8 high
#   ht_sofa        a sofa, 7.4 x 3.3 x 2.9 (upholstery in the hotel's one accent)
#   ht_armchair    an armchair, 3.6 x 3.3 x 2.9
#   ht_table       a low table, 4.4 x 2.6 x 1.3
#   ht_desk        the reception desk, 15 x 3.4 x 3.9: a panelled front, a stone top, a back shelf
#   ht_fountain    the fountain, the lobby's centre object: a basin 18 across (a 2-wide rim, 1.8 high), two tiers to 10
#   ht_dado        a panelled wood dado, 8 long, 4.6 high: skirting, two raised panels, a rail (wall piece)
#   ht_doors       closed panelled double doors in a frame, 7 x 9.6 (wall piece)
#   ht_sconce      a wall lamp, 1.2 x 0.9 x 1.8, its middle at the origin (wall piece)
#   ht_lift        lift doors in a deep surround, 11.6 x 12.15 (wall piece; HUBS travel stands in front)
#   ht_vault       one 17-long bay of the ballroom's barrel vault: the shell from the walls' top (18) up to 26.6
#   ht_vaultrib    a vault rib, 1.4 wide, from wall to wall, with a springer block each end
#   ht_wallpanel   a raised moulded panel, 6 x 10 (wall piece) for the bare plaster fields
# run: blender -b --factory-startup -P tools/roblox/hotel_models.py -- <out_dir> [preview.jpg]
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *

CREAM, CREAM2, STONE, STONE2 = 'e3d9c7', 'd2c6b2', 'cdc2b1', 'b5aa98'
WOOD, WOOD2, BRASS, DARK = '6e5340', '5b4434', 'a89466', '3a3530'
VAULT = 'cbbfab'                                        # (judge round 1: the ballroom's vault a step darker)
ACC, ACC2, FAB = '4d6a58', '5d7a67', '8a8072'          # the hotel's one accent (a quiet green) on the upholstery
POT, LEAF, LEAF2, TRUNK, SOIL = 'b8a48a', '4f7044', '5f7a4c', '7a6a55', '4a4038'
WARM, BASIN = 'ffe2b8', '8f9a98'
reset()

# ------------------------------------------------------------------ structure
def pier():
    bx('plastic', CREAM, 3.4, 3.4, 1.0, 0, 0, 0.5, bevel=0.25)
    bx('plastic', CREAM, 2.6, 2.6, 11.0, 0, 0, 6.5, bevel=0.3)
    bx('plastic', CREAM2, 3.0, 3.0, 0.5, 0, 0, 12.25, bevel=0.15)
    bx('plastic', CREAM, 3.4, 3.4, 0.55, 0, 0, 12.775, bevel=0.15)
pier(); keep('ht_pier')

def pilaster(H):
    bx('plastic', CREAM, 3.6, 1.6, 1.2, 0, -0.7, 0.6, bevel=0.22)            # base: y -1.5..0.1
    bx('plastic', CREAM, 2.8, 1.1, H - 2.8, 0, -0.45, 1.2 + (H - 2.8) / 2, bevel=0.25)  # shaft: y -1.0..0.1
    bx('plastic', CREAM2, 3.2, 1.4, 0.6, 0, -0.6, H - 1.3, bevel=0.15)       # the capital's lower step
    bx('plastic', CREAM, 3.6, 1.7, 1.0, 0, -0.75, H - 0.5, bevel=0.2)        # its top
pilaster(26); keep('ht_pilaster')
pilaster(18); keep('ht_pilasterMid')
pilaster(14); keep('ht_pilasterLow')

def cornice():
    bx('plastic', CREAM2, 8.0, 0.7, 1.5, 0, -0.3, -1.75, bevel=0.15)         # the band
    bx('plastic', CREAM, 8.0, 1.2, 0.5, 0, -0.55, -0.85, bevel=0.15)         # a step
    bx('plastic', CREAM, 8.0, 1.75, 0.6, 0, -0.8, -0.3, bevel=0.18)          # the drip at the top
cornice(); keep('ht_cornice')

def door_surround(W, H):
    for s in (-1, 1):
        x = s * (W / 2 + 0.7)
        bx('plastic', CREAM, 1.4, 1.2, H, x, -0.5, H / 2, bevel=0.25)          # jamb: y -1.1..0.1
        bx('plastic', CREAM2, 1.8, 1.5, 1.0, x, -0.65, 0.5, bevel=0.2)         # plinth block
        # the inner corner under the head, cut on the slant
        prism('plastic', CREAM, [(0, 0), (s * -1.1, 0), (0, -1.1)], 1.0, M=T(s * W / 2, -0.5, H) , bevel=0.08)
    bx('plastic', CREAM, W + 2.8, 1.2, 1.6, 0, -0.5, H + 0.8, bevel=0.25)      # the head
    bx('plastic', CREAM2, W + 3.6, 1.7, 0.55, 0, -0.75, H + 1.875, bevel=0.18) # its cap
door_surround(8, 10); keep('ht_doorS')
door_surround(16, 14); keep('ht_doorL')

def balustrade():
    # (round 2) a solid parapet: a plinth, a frame with a recessed field on both faces, a rounded cap
    bx('plastic', CREAM2, 8.0, 1.5, 0.8, 0, 0, 0.4, bevel=0.2)                # plinth: z 0..0.8
    for zz in (1.0, 2.6):
        bx('plastic', CREAM, 8.0, 1.1, 0.4, 0, 0, zz, bevel=0.12)               # the frame's rails
    for sx in (-1, 1):
        bx('plastic', CREAM, 0.7, 1.1, 2.0, sx * 3.65, 0, 1.8, bevel=0.12)      # its ends
    bx('plastic', CREAM2, 6.6, 0.8, 1.2, 0, 0, 1.8, bevel=0.08)               # the recessed field
    soft('plastic', CREAM, 8.0, 1.6, 0.6, 0, 0, 3.1, 0.25, pick='x')          # the cap: z 2.8..3.4, rounded along its length
balustrade(); keep('ht_baluster')
bx('plastic', CREAM, 1.8, 1.8, 3.3, 0, 0, 1.65, bevel=0.25)
bx('plastic', CREAM2, 2.1, 2.1, 0.6, 0, 0, 3.6, bevel=0.2)
keep('ht_newel')

def coffer():
    # (round 2) a 14 x 16 cell (4 x 4 over the lobby), beams 1.4 wide and 2.0 deep, a recessed lamp housing in the middle
    for sy in (-1, 1):
        bx('plastic', CREAM, 14.0, 1.4, 2.0, 0, sy * 7.3, -1.0, bevel=0.3)
    for sx in (-1, 1):
        bx('plastic', CREAM, 1.4, 13.2, 2.0, sx * 6.3, 0, -1.0, bevel=0.3)
    bx('plastic', CREAM2, 9.0, 10.4, 0.35, 0, 0, -0.175, bevel=0.12)          # the field's step
    for sy in (-1, 1):
        bx('plastic', CREAM, 5.2, 0.6, 0.7, 0, sy * 2.6, -0.65, bevel=0.15)     # the lamp's housing round a 4.6 x 4.6 opening
    for sx in (-1, 1):
        bx('plastic', CREAM, 0.6, 4.6, 0.7, sx * 2.6, 0, -0.65, bevel=0.15)
coffer(); keep('ht_coffer')

def chandelier():
    # (round 2) a thick ring, four thick spokes, eight big lamps (judge round 1: thin spokes and candles read as noise)
    cy('plastic', CREAM, 1.4, 0.4, 0, 0, -0.2, bevel=0.12)                    # ceiling rose
    cy('plastic', BRASS, 0.35, 3.0, 0, 0, -1.9, bevel=0.08)                   # the rod
    lathe('plastic', BRASS, ring_prof(4.8, 0.75, 10), M=T(0, 0, -4.0), segs=28, cap=False)
    lathe('plastic', CREAM, [(0.0, 0.0), (1.2, 0.0), (1.35, 0.5), (1.2, 1.4), (0.0, 1.4)], M=T(0, 0, -4.7), segs=16)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        bx('plastic', BRASS, 4.0, 0.6, 0.6, 2.9 * math.cos(a), 2.9 * math.sin(a), -4.0, bevel=0.15, rot=RZ(a))
    for i in range(8):
        a = i * math.pi / 4
        bx('neon', WARM, 0.9, 0.9, 1.1, 4.8 * math.cos(a), 4.8 * math.sin(a), -2.85, bevel=0.15)
        cy('plastic', BRASS, 0.65, 0.3, 4.8 * math.cos(a), 4.8 * math.sin(a), -3.5, bevel=0.08)
    lathe('neon', WARM, [(0.0, 0.0), (1.0, 0.05), (0.9, 0.55), (0.0, 0.6)], M=T(0, 0, -5.3), segs=16)
chandelier(); keep('ht_chandelier')

# ------------------------------------------------------------------ furniture and planting
def palm():
    lathe('plastic', POT, [(0.0, 0.0), (1.1, 0.0), (1.45, 1.9), (1.65, 2.0), (1.65, 2.3), (0.0, 2.3)], segs=16)
    cy('plastic', SOIL, 1.4, 0.1, 0, 0, 2.2, bevel=0.0)
    z = 2.2
    for i, (r0, r1, h, dx) in enumerate([(0.42, 0.36, 2.0, 0.0), (0.36, 0.3, 1.9, 0.15), (0.3, 0.26, 1.6, 0.3)]):
        cy('plastic', TRUNK, r0, h, dx, 0, z + h / 2, bevel=0.08, r2=r1)
        z += h - 0.1
    top = (0.35, 0, z)
    for i in range(7):
        a = i * 2 * math.pi / 7
        hexc = LEAF if i % 2 == 0 else LEAF2
        leaf = [(0, 0), (1.6, 0.55), (4.2, 0.0), (1.6, -0.55)]
        M = T(*top) @ RZ(a) @ RY(math.radians(28))
        prism('plastic', hexc, [(u, v * 0.25) for u, v in leaf], 1.2, M=M @ RX(math.radians(0)), bevel=0.06)
    ball('plastic', LEAF2, 0.5, top[0], top[1], top[2] + 0.1)
palm(); keep('ht_palm')

def seat(L):
    soft('fabric', FAB, L, 3.3, 1.0, 0, 0, 0.5, 0.3, pick='top')              # base
    soft('fabric', ACC, L - 1.8, 2.5, 0.6, 0, -0.25, 1.3, 0.28)               # seat cushion
    soft('fabric', ACC, L - 1.0, 0.9, 1.9, 0, 1.15, 1.95, 0.35)               # back
    for s in (-1, 1):
        soft('fabric', ACC2, 0.9, 3.3, 1.5, s * (L / 2 - 0.45), 0, 1.45, 0.4)   # arms
    for s in (-1, 1):
        for t in (-1, 1):
            cy('wood', WOOD2, 0.16, 0.25, s * (L / 2 - 0.5), t * 1.3, -0.12, bevel=0.03)
seat(7.4); keep('ht_sofa')
seat(3.6); keep('ht_armchair')

bx('wood', WOOD, 4.4, 2.6, 0.3, 0, 0, 1.15, bevel=0.12)
bx('plastic', STONE2, 3.6, 1.8, 1.0, 0, 0, 0.5, bevel=0.15)
keep('ht_table')

def desk():
    L = 15.0
    bx('wood', WOOD, L, 1.6, 3.4, 0, 0.1, 1.7, bevel=0.2)                     # the front block
    for i in range(5):
        x = -L / 2 + 1.5 + i * 3.0
        bx('wood', WOOD2, 2.4, 0.3, 2.2, x, -0.75, 1.8, bevel=0.1)              # raised panels
    bx('plastic', STONE, L + 0.6, 2.2, 0.35, 0, 0.0, 3.575, bevel=0.12)        # the stone top
    bx('plastic', DARK, L, 0.5, 0.4, 0, -0.65, 0.2, bevel=0.08)               # kick
    bx('wood', WOOD2, L - 0.4, 1.2, 2.8, 0, 1.6, 1.4, bevel=0.15)             # the staff's side: a low counter
desk(); keep('ht_desk')

def fountain():
    # (round 2) the lobby's centre object: a basin 18 across with a 2-wide rounded rim, a two-tier middle 10 high
    lathe('plastic', STONE, [(7.0, 0.0), (9.0, 0.0), (9.0, 1.4), (8.7, 1.8), (7.3, 1.8), (7.0, 1.5)], segs=36)
    cy('plastic', BASIN, 7.1, 0.3, 0, 0, 0.15, segs=36, bevel=0.0)
    lathe('plastic', STONE, [(0.0, 0.0), (2.2, 0.0), (2.2, 1.4), (1.5, 1.8), (1.2, 4.6), (1.6, 5.0), (0.0, 5.0)], segs=24)
    lathe('plastic', STONE, [(0.0, 4.9), (1.3, 4.9), (3.8, 5.6), (3.9, 6.1), (3.3, 6.2), (0.0, 6.0)], segs=28)
    lathe('plastic', STONE2, [(0.0, 6.0), (0.9, 6.0), (0.7, 7.6), (1.0, 7.9), (0.0, 7.9)], segs=16)
    lathe('plastic', STONE, [(0.0, 7.8), (0.8, 7.8), (2.2, 8.3), (2.2, 8.7), (1.8, 8.8), (0.0, 8.6)], segs=24)
    lathe('plastic', STONE2, [(0.0, 8.6), (0.5, 8.6), (0.35, 9.4), (0.6, 9.7), (0.0, 10.1)], segs=12)
fountain(); keep('ht_fountain')

# ------------------------------------------------------------------ wall pieces
def dado():
    bx('plastic', DARK, 8.0, 0.4, 0.6, 0, -0.15, 0.3, bevel=0.08)            # skirting
    bx('wood', WOOD, 8.0, 0.35, 3.6, 0, -0.12, 2.4, bevel=0.06)              # the boarding
    for s in (-1, 1):
        bx('wood', WOOD2, 3.2, 0.25, 2.6, s * 2.0, -0.35, 2.4, bevel=0.1)       # raised panels
    bx('wood', WOOD, 8.0, 0.6, 0.4, 0, -0.25, 4.4, bevel=0.12)               # the rail
dado(); keep('ht_dado')

def doors():
    for s in (-1, 1):
        bx('plastic', CREAM, 0.9, 0.9, 9.6, s * 3.05, -0.35, 4.8, bevel=0.2)
    bx('plastic', CREAM, 7.0, 0.9, 0.9, 0, -0.35, 9.15, bevel=0.2)
    for s in (-1, 1):
        bx('wood', WOOD, 2.55, 0.4, 8.6, s * 1.32, -0.2, 4.35, bevel=0.1)
        for z in (2.3, 6.2):
            bx('wood', WOOD2, 1.7, 0.2, 2.8, s * 1.32, -0.45, z, bevel=0.08)
        bx('plastic', BRASS, 0.2, 0.3, 1.2, s * 0.35, -0.55, 4.3, bevel=0.06)
doors(); keep('ht_doors')

def sconce():
    bx('plastic', BRASS, 0.8, 0.25, 1.4, 0, -0.12, 0, bevel=0.08)
    bx('plastic', BRASS, 0.2, 0.6, 0.2, 0, -0.5, -0.1, bevel=0.05)
    lathe('neon', WARM, [(0.0, 0.0), (0.55, 0.0), (0.38, 0.7), (0.0, 0.7)], M=T(0, -0.65, 0.0), segs=12)
sconce(); keep('ht_sconce')

def lift():
    door_surround(8, 10)
    for s in (-1, 1):
        bx('plastic', BRASS, 3.95, 0.4, 10.0, s * 2.02, -0.15, 5.0, bevel=0.08)
    bx('plastic', DARK, 3.0, 0.3, 0.9, 0, -1.2, 10.8, bevel=0.08)            # the floor indicator's plate, on the head
    bx('neon', WARM, 2.2, 0.1, 0.4, 0, -1.38, 10.8, bevel=0.0)
lift(); keep('ht_lift')

def wallpanel():
    # a raised moulded panel for a bare plaster field: 6 wide, 10 high (wall piece, its foot at the origin)
    for sz in (0.25, 9.75):
        bx('plastic', CREAM, 6.0, 0.4, 0.5, 0, -0.15, sz, bevel=0.12)
    for sx in (-1, 1):
        bx('plastic', CREAM, 0.5, 0.4, 9.0, sx * 2.75, -0.15, 5.0, bevel=0.12)
    bx('plastic', CREAM2, 4.6, 0.2, 8.6, 0, -0.05, 5.0, bevel=0.05)
wallpanel(); keep('ht_wallpanel')

# ------------------------------------------------------------------ the ballroom's barrel vault (52 wide, walls 18 high, crown 26)
R, ZC = 46.25, -20.25
A = math.asin(26.0 / R)
def arc(r, n=18):
    return [(r * math.sin(-A + 2 * A * i / n), ZC + r * math.cos(-A + 2 * A * i / n)) for i in range(n + 1)]
shell = arc(R) + arc(R + 0.7)[::-1]
prism('plastic', VAULT, shell, 17.0, bevel=0.0)
keep('ht_vault')
rib = arc(R - 1.2) + arc(R + 0.05)[::-1]
prism('plastic', CREAM2, rib, 1.4, bevel=0.15)
for s in (-1, 1):
    bx('plastic', CREAM, 2.0, 2.0, 2.4, s * 25.2, 0, 17.0, bevel=0.2)          # springers on the wall tops
keep('ht_vaultrib')

export_all('hotel.glb')
if len(sys.argv) > sys.argv.index('--') + 2:
    preview(sys.argv[sys.argv.index('--') + 2], cols=6)
