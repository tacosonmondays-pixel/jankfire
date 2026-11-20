# THE PAD KIT (20 Nov 2026; the owner: "also the new pads look hideas referenbce rivals please"): ONE queue pad for every
# hub, a floor plate you step onto (Rivals' grammar: a plate one step up, the teams facing across a low divider, a spot
# per player, the count screen right behind, the mode's name over it; ours: the shapes, the foot-plates, the pale frame).
# The Studio side is HubKit's K.pad (the plates, rims, Glow, Slots and screens are Parts there: play-party's contract);
# these are the chunky pieces, all in the PAD's frame: the origin is the plinth's front middle on the walkway floor,
# the front (the walkway) is -Y here (+Z in Roblox), the bay goes back along +Y (-Z in Roblox). 1 unit = 1 stud, Z up.
#   (round 3, after two judge rounds: the team's colour IS the plate, big marks, no strips, an open gantry)
#   jpad_plinth   one pale bevelled block, 12.4 x 13.4 x 1.2 (its top border is the kerb round the team plates)
#   jpad_divider  the low pale kerb between the teams, 1.0 x 11.4 x 0.45, its origin at its foot's middle
#   jpad_spot     a player's mark, a pale rounded square 2.6 x 2.6 x 0.08 with a darker inset (origin: foot middle)
#   jpad_totem    the gantry at the plate's back edge: two posts, the board's sill (z 7.1..7.6), the board's back, a
#                 cap at 14.2; 10.8 wide, y 11.6..13.0
# run: blender -b --factory-startup -P tools/roblox/pad_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *

TRIM, TRIM2, BASE, KICK, BACK = 'c9c5bc', 'b5b1a8', '4a4f57', '3d4148', '33363c'
SPOT, SPOTIN = 'dcd8cf', '40444b'
reset()

# ------------------------------------------------------------------ jpad_plinth (round 3: one pale bevelled block, a step up)
# 12.4 wide x 13.4 deep x 1.2 high; the team plates are inset 0.7 from its edges, so its pale top border is the kerb
bx('plastic', TRIM, 12.4, 13.4, 1.2, 0, 6.7, 0.6, bevel=0.3)
for s in (-1, 1):                                                           # a dark kick band low on each side
    bx('plastic', KICK, 0.3, 12.2, 0.45, s * 6.22, 6.9, 0.3, bevel=0.1)
keep('jpad_plinth')

# ------------------------------------------------------------------ jpad_divider (a low pale kerb between the teams)
soft('plastic', TRIM2, 1.0, 11.4, 0.45, 0, 0, 0.225, 0.2, pick='top')
keep('jpad_divider')

# ------------------------------------------------------------------ jpad_spot (a player's mark: a big pale square)
soft('plastic', SPOT, 2.6, 2.6, 0.08, 0, 0, 0.04, 0.04, pick='top')
bx('plastic', SPOTIN, 1.5, 1.5, 0.1, 0, 0, 0.05, bevel=0.02)
keep('jpad_spot')

# ------------------------------------------------------------------ jpad_totem (round 3: an open gantry at the plate's back edge)
YC, Z0 = 12.3, 1.2          # its middle (depth 1.4: y 11.6..13.0), it stands on the plinth's top
for s in (-1, 1):
    bx('plastic', TRIM, 1.0, 1.4, 12.4, s * 4.8, YC, Z0 + 6.2, bevel=0.25)            # posts: x 4.3..5.3, z 1.2..13.6
bx('plastic', TRIM2, 8.6, 1.2, 0.5, 0, YC, Z0 + 6.15, bevel=0.12)                    # the sill under the board: z 7.1..7.6
bx('plastic', TRIM, 10.8, 1.8, 0.6, 0, YC, Z0 + 12.4 + 0.3, bevel=0.22)              # the cap: z 13.6..14.2
bx('plastic', BACK, 8.6, 0.3, 6.0, 0, YC + 0.55, Z0 + 9.4, bevel=0.05)                # the board's back
keep('jpad_totem')

export_all('pads.glb')
if len(sys.argv) > sys.argv.index('--') + 2:
    preview(sys.argv[sys.argv.index('--') + 2], cols=4)
