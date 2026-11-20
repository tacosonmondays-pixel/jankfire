# THE PAD KIT (20 Nov 2026; the owner: "also the new pads look hideas referenbce rivals please"): ONE queue pad for every
# hub, a floor plate you step onto (Rivals' grammar: a plate one step up, the teams facing across a low divider, a spot
# per player, the count screen right behind, the mode's name over it; ours: the shapes, the foot-plates, the pale frame).
# The Studio side is HubKit's K.pad (the plates, rims, Glow, Slots and screens are Parts there: play-party's contract);
# these are the chunky pieces, all in the PAD's frame: the origin is the plinth's front middle on the walkway floor,
# the front (the walkway) is -Y here (+Z in Roblox), the bay goes back along +Y (-Z in Roblox). 1 unit = 1 stud, Z up.
#   (round 3, after two judge rounds: the team's colour IS the plate, big marks, no strips, an open gantry)
#   jpad_plinth   one bevelled block, 12.4 x 13.4 x 1.2, mid warm grey, with a 0.4 rim round its top (the lanes sit in it)
#   jpad_divider  the low pale kerb between the teams, 1.4 x 11.4 x 0.6, rounded on top, its origin at its foot's middle
#   jpad_spot     a player's mark: a raised bevelled pale disc, 2.4 across, 0.3 high (origin: foot middle) (round 4: the dark
#                 insets read as floor drains)
#   jpad_totem    the gantry at the plate's back edge (round 4: thick posts 1.6 into the plinth's back corners, the board
#                 raised clear of hats): posts x 4.3..5.9, the sill z 8.6..9.1, the board's back, a cap z 13.8..14.4;
#                 11.8 wide, y 11.5..13.1
# run: blender -b --factory-startup -P tools/roblox/pad_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *

TRIM, TRIM2, BASE, KICK, BACK = '7d7a76', '6b6863', '4a4f57', '3d4148', '33363c'   # (round 5: a mid warm grey, not the room's cream)
SPOT = 'e6e1d6'
reset()

# ------------------------------------------------------------------ jpad_plinth (round 3: one pale bevelled block, a step up)
# 12.4 wide x 13.4 deep x 1.2 high; the team plates are inset 0.7 from its edges, so its pale top border is the kerb
bx('plastic', TRIM, 12.4, 13.4, 1.2, 0, 6.7, 0.6, bevel=0.3)
for s in (-1, 1):                                                           # a dark kick band low on each side
    bx('plastic', KICK, 0.3, 12.2, 0.45, s * 6.22, 6.9, 0.3, bevel=0.1)
# (round 5) a raised rim round the top, so the team lanes sit 0.4 down in it: sides, front, the back under the gantry
for s in (-1, 1):
    bx('plastic', TRIM2, 0.7, 13.4, 0.4, s * 5.85, 6.7, 1.4, bevel=0.15)
bx('plastic', TRIM2, 11.0, 0.7, 0.4, 0, 0.35, 1.4, bevel=0.15)
bx('plastic', TRIM2, 11.0, 2.0, 0.4, 0, 12.4, 1.4, bevel=0.15)
keep('jpad_plinth')

# ------------------------------------------------------------------ jpad_divider (a low pale kerb between the teams)
soft('plastic', TRIM2, 1.4, 11.4, 0.6, 0, 0, 0.3, 0.3, pick='top')
keep('jpad_divider')

# ------------------------------------------------------------------ jpad_spot (a player's mark: a big pale square)
cy('plastic', SPOT, 1.2, 0.3, 0, 0, 0.15, segs=28, bevel=0.1)          # (round 5: a raised bevelled foot disc)
keep('jpad_spot')

# ------------------------------------------------------------------ jpad_totem (round 3: an open gantry at the plate's back edge)
YC, Z0 = 12.3, 1.2          # its middle (depth 1.4: y 11.6..13.0), it stands on the plinth's top
for s in (-1, 1):
    bx('plastic', TRIM, 1.6, 1.6, 12.6, s * 5.1, YC, Z0 + 6.3, bevel=0.35)            # posts: x 4.3..5.9, z 1.2..13.8
bx('plastic', TRIM2, 8.6, 1.3, 0.5, 0, YC, 8.85, bevel=0.14)                         # the sill under the board: z 8.6..9.1
bx('plastic', TRIM, 11.8, 1.9, 0.6, 0, YC, 14.1, bevel=0.25)                         # the cap: z 13.8..14.4
bx('plastic', BACK, 8.6, 0.3, 4.7, 0, YC + 0.55, 11.45, bevel=0.05)                  # the board's back: z 9.1..13.8
keep('jpad_totem')

export_all('pads.glb')
if len(sys.argv) > sys.argv.index('--') + 2:
    preview(sys.argv[sys.argv.index('--') + 2], cols=4)
