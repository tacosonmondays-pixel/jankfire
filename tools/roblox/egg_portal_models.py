# THE GOLD DUMMIES' PORTAL (18 Nov 2026): the teleporter at the end of the little room behind the course's TOP door
# (studio-tools/TrainingLot.luau eggDoor; the owner, 17 Nov: the dead end "should lead to a portal teleporter that takes
# you to the training area that's in the air", 18 Nov: "this door is still open bro this is what should lead to the
# teleporter", and of the hub's pads, "I dont like the pillar of light from the teleporter": so no light column, no
# beam, nothing glowing upward). the training v2 kit's family: few big rounded pieces, flat matte colours, an off-white
# ring, slate clamps, one thin amber line, and the opening black (the owner, 17 Nov: "I like the old black entrances").
# 1 unit = 1 stud, Z up, the front faces -Y (Roblox +Z after the import), the floor is z 0.
#   te_portal   an upright ring 9.5 across on a low step: the ring's plane is y 0, the step runs 2.5 out in front of it
#               (10.6 wide, 0.6 tall), the black core is 0.25 behind the plane; 10.6 x 3.65 x 8.7
# run: blender -b --factory-startup -P tools/roblox/egg_portal_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *
from structkit import _emit

TRIM, PIER2, DEEP, SLATE, AMBER, CORE = 'e2ded5', 'c4c0b8', '3d414a', '62666f', 'f0a53a', '17181c'
reset()

ZC, R, r = 3.9, 3.95, 0.85          # the ring's middle (height), its radius and its tube's
TURN = T(0, 0, ZC) @ RX(math.pi / 2)  # (lathe spins round Z: turned so the ring stands up, its axis along Y)

# the step it stands on: a dark plinth with a pale top let in, running out in front of the ring
soft('plastic', DEEP, 10.6, 3.2, 0.6, 0, -0.9, 0.3, 0.25, pick='top', segs=2, small=0.04)
soft('plastic', PIER2, 9.8, 2.5, 0.06, 0, -1.05, 0.63, 0.2, pick='up', segs=2, small=0.0)
# the ring: chunky, off-white, its lower part sunk into the step
lathe('plastic', TRIM, ring_prof(R, r, 12), segs=44, cap=False, M=TURN)
# the black core, just behind the ring's middle (wider than the ring's hole: its edge hides behind the tube)
cy('plastic', CORE, 3.3, 0.3, 0, 0.25, ZC, axis='y', segs=44, bevel=0.05)
# the one accent: a thin amber line round the inside edge, on the ring's front
lathe('plastic', AMBER, ring_prof(3.2, 0.11, 8), segs=44, cap=False, M=T(0, -0.46, 0) @ TURN)
# three slate clamps on the ring (left, right, top): it reads as a machine, not a hoop
for a in (0.0, math.pi / 2, math.pi):
    x, z = R * math.cos(a), ZC + R * math.sin(a)
    if abs(math.sin(a)) > 0.5:
        soft('plastic', SLATE, 1.6, 2.3, 1.4, x, 0, z, 0.35, pick='all', segs=2, small=0.05)
    else:
        soft('plastic', SLATE, 1.4, 2.3, 1.6, x, 0, z, 0.35, pick='all', segs=2, small=0.05)
keep('te_portal')

export_all('egg_portal.glb')
if len(sys.argv) > sys.argv.index('--') + 2:
    preview(sys.argv[sys.argv.index('--') + 2], cols=2)
