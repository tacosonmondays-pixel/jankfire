# THE ROOFTOP'S PLANT KIT (structure pass, 15 Nov 2026): the things three judges said paint could not give the two spawn
# roofs. chunky style (few big rounded shapes, flat colours), the serious pass's palette (neutral greys, warm white
# light, one amber accent). 1 unit = 1 stud, Z up, front = -Y, floor at z 0, centred on x 0 y 0.
#   rt_chiller    air-cooled chiller on a plinth, 20.4 x 8.4 x 7: louvre bays, three fans on top, a control cabinet
#   rt_vents      a curb with two mushroom vents, a louvred exhaust box and a flue, 8 x 8 x 9
#   rt_stairhead  a stair bulkhead with a mono-pitch roof, 14.5 x 19 x 10.4: door and lamp in the tall -Y end
#   rt_skylight   a ridge skylight, 9 x 12 x 3.2: glass on rafters, a lit room below
#   rt_dome       a dome rooflight on a curb, 5 x 5 x 2.3
#   rt_duct       a run of duct on three stands, 16 x 3.4 x 3
#   rt_pier       a parapet pier with a marker lamp, 2.8 x 2.4 x 4.8
#   rt_coping     one length of parapet coping, 12 x 1.8 x 0.5 (stretched along X in Studio)
#   rt_kiosk      a plant room with louvred double doors, 13.2 x 12 x 8.4 (fits over the east roof's shed)
#   rt_cowl       a round roof fan on a curb, 6 x 6 x 4.7
#   rt_tank       a tank lying on two saddles, 10 x 5 x 5.6
#   rt_walllamp   a wall lamp, 2.4 x 1 x 0.8 (the wall is at +Y)
# rt_chiller, rt_vents, rt_stairhead and rt_tank also come mirrored (rt_chillerM ...) for the east roof.
#   rt_plinth, rt_stack (+M), rt_ductL (+M), rt_barrel: added after the first judging (see the end of the file)
#   rt_liftsign   the plate that stands in for the hut's white-on-white LIFT box, 4.6 x 0.4 x 1.7 (no letters: Studio
#                 puts the word on it)
# run: blender -b --factory-startup -P tools/roblox/roofdress_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *

WALL, TRIM, COPE, CASE, MIDG, GRAPH, DARK = 'a3a19c', 'c9c7c1', '8b8984', '9a9da3', '6a6e77', '4d515a', '34363d'
AMBER, WARM, GLASS, ROOM = 'd6a738', 'f2dcc0', '465a69', 'e8d2b0'
reset()

# ------------------------------------------------------------------ rt_chiller
bx('concrete', COPE, 20.4, 8.4, 0.6, 0, 0, 0.3, 0.15)
for sy in (-2.6, 2.6): bx('plastic', GRAPH, 18.4, 0.9, 0.5, 0.6, sy, 0.85, 0.12)
soft('plastic', CASE, 18.0, 7.4, 4.5, 0.8, 0, 3.35, 0.5, pick='top')
for side, yaw in ((-1, 0.0), (1, math.pi)):
    for i in (-1, 0, 1):
        louvre(0.8 + i * 5.7, side * 3.7, 3.2, 5.0, 3.0, yaw)
for i in (-1, 0, 1): fan(0.8 + i * 5.8, 0, 5.6, 2.6)
bx('plastic', TRIM, 0.7, 3.4, 3.4, 9.95, -1.4, 3.3, 0.15)
bx('plastic', AMBER, 0.76, 3.5, 0.45, 9.95, -1.4, 4.6, 0.08)
bx('neon', WARM, 0.8, 0.7, 0.32, 9.95, -2.4, 3.7, 0.05)
for sy in (-1.7, 1.7):
    cy('plastic', MIDG, 0.45, 1.5, -8.8, sy, 2.6, axis='x', bevel=0.08, segs=12)
    cy('plastic', MIDG, 0.45, 2.0, -9.4, sy, 1.6, bevel=0.08, segs=12)
    ball('plastic', MIDG, 0.5, -9.4, sy, 2.6)
    cy('plastic', TRIM, 0.62, 0.35, -9.4, sy, 0.78, bevel=0.08, segs=12)
both('rt_chiller')

# ------------------------------------------------------------------ rt_vents
def mushroom(x, y, z0, r, h, rc):
    cy('plastic', TRIM, r + 0.35, 0.5, x, y, z0 + 0.25, bevel=0.12)
    cy('plastic', CASE, r, h, x, y, z0 + h / 2, bevel=0.1)
    cy('plastic', DARK, r * 0.8, 0.6, x, y, z0 + h + 0.25, bevel=0.02)
    lathe('plastic', TRIM, dome_prof(rc, rc * 0.42, rim=0.35), T(x, y, z0 + h + 0.45), segs=20)

bx('concrete', COPE, 8.0, 8.0, 0.8, 0, 0, 0.4, 0.18)
mushroom(-1.7, -1.5, 0.8, 1.35, 5.4, 2.5)
mushroom(2.3, 2.0, 0.8, 0.95, 3.0, 1.8)
soft('plastic', CASE, 2.8, 2.8, 4.0, 2.3, -2.2, 2.8, 0.3, pick='up')
louvre(2.3, -3.6, 3.2, 2.2, 2.2, 0.0, n=4)
louvre(3.7, -2.2, 3.2, 2.2, 2.2, math.pi / 2, n=4)
bx('plastic', GRAPH, 3.4, 3.4, 0.5, 2.3, -2.2, 5.05, 0.15)
cy('plastic', MIDG, 0.6, 7.0, -2.5, 2.5, 4.3, bevel=0.1, segs=14)
for z in (3.2, 6.4): cy('plastic', TRIM, 0.85, 0.5, -2.5, 2.5, z, bevel=0.12, segs=14)
cy('plastic', MIDG, 0.25, 0.5, -2.5, 2.5, 7.95, bevel=0.03, segs=8)
cy('plastic', GRAPH, 1.25, 0.8, -2.5, 2.5, 8.5, r2=0.3, bevel=0.08, segs=14)
both('rt_vents')

# ------------------------------------------------------------------ rt_stairhead
bx('concrete', COPE, 14.5, 16.5, 1.0, 0, 0, 0.5, 0.2)
prism('concrete', WALL, [(-8, 0.6), (8, 0.6), (8, 7.4), (-8, 10.0)], 14.0, RZ(math.pi / 2), bevel=0.3)
slope = math.atan2(2.6, 16.0)
bx('plastic', GRAPH, 15.2, 17.4, 0.7, 0, 0, 9.1, 0.25, rot=RX(-slope))
bx('plastic', TRIM, 14.3, 0.4, 0.8, 0, -8.05, 9.25, 0.1)
bx('plastic', DARK, 4.6, 0.5, 7.2, 0, -8.05, 4.4, 0.1)
bx('plastic', MIDG, 3.8, 0.4, 6.6, 0, -8.2, 4.2, 0.1)
bx('glass', GLASS, 1.2, 0.46, 1.7, 0.9, -8.22, 5.9, 0.08)
bx('plastic', AMBER, 3.8, 0.46, 0.6, 0, -8.22, 1.25, 0.06)
bx('plastic', TRIM, 0.25, 0.3, 1.2, -1.3, -8.45, 4.2, 0.08)
doorlamp(0, -8.0, 8.55)
bx('concrete', COPE, 6.0, 2.4, 0.5, 0, -9.4, 0.25, 0.12)
louvre(7.0, 2.0, 4.6, 5.0, 3.2, math.pi / 2)
louvre(-7.0, 2.0, 4.6, 5.0, 3.2, -math.pi / 2)
cy('plastic', MIDG, 0.35, 6.6, 6.3, 8.3, 3.9, bevel=0.08, segs=10)
soft('plastic', CASE, 4.0, 1.3, 2.4, -2.0, 8.6, 4.6, 0.3, pick='all')
both('rt_stairhead')

# ------------------------------------------------------------------ rt_skylight
soft('plastic', TRIM, 9.0, 12.0, 0.9, 0, 0, 0.45, 0.25, pick='up')
bx('neon', ROOM, 7.0, 10.2, 0.12, 0, 0, 0.93, 0.02)
prism('glass', GLASS, [(-4.1, 0.9), (4.1, 0.9), (0, 3.0)], 11.2, I4, bevel=0.05)
bx('plastic', GRAPH, 0.5, 11.8, 0.45, 0, 0, 3.0, 0.12)
ra, rl = math.atan2(2.1, 4.1), math.hypot(2.1, 4.1)
for y in (-5.7, -2.85, 0, 2.85, 5.7):
    for s in (-1, 1):
        bx('plastic', GRAPH, rl + 0.2, 0.4, 0.35, s * 2.05, y, 2.07, 0.1, rot=RY(s * ra))
for s in (-1, 1): bx('plastic', GRAPH, 0.45, 11.8, 0.4, s * 4.2, 0, 1.0, 0.1)
keep('rt_skylight')

# ------------------------------------------------------------------ rt_dome
soft('plastic', TRIM, 5.0, 5.0, 0.8, 0, 0, 0.4, 0.35, pick='up')
cy('plastic', GRAPH, 2.2, 0.2, 0, 0, 0.88, bevel=0.04, segs=24)
lathe('plastic', 'd9d6cd', dome_prof(2.1, 1.25, rim=0.12, steps=7), T(0, 0, 0.95), segs=24)
keep('rt_dome')

# ------------------------------------------------------------------ rt_duct
soft('plastic', CASE, 16.0, 2.2, 1.8, 0, 0, 2.1, 0.3, pick='x')
for x in (-6, -2, 2, 6): bx('plastic', TRIM, 0.35, 2.5, 2.1, x, 0, 2.1, 0.08)
for x in (-6.5, 0, 6.5):
    bx('concrete', COPE, 1.4, 3.4, 0.3, x, 0, 0.15, 0.08)
    bx('plastic', GRAPH, 0.5, 2.8, 0.4, x, 0, 1.0, 0.1)
    for sy in (-1.1, 1.1): bx('plastic', GRAPH, 0.45, 0.45, 0.9, x, sy, 0.6, 0.08)
keep('rt_duct')

# ------------------------------------------------------------------ rt_pier
bx('concrete', COPE, 2.4, 2.0, 3.6, 0, 0, 1.8, 0.25)
bx('plastic', TRIM, 2.8, 2.4, 0.5, 0, 0, 3.75, 0.18)
cy('plastic', DARK, 0.78, 0.3, 0, 0, 4.15, segs=16, bevel=0.08)
lathe('neon', WARM, dome_prof(0.62, 0.5, rim=0.22, steps=5), T(0, 0, 4.3), segs=16)
keep('rt_pier')

# ------------------------------------------------------------------ rt_coping
soft('plastic', TRIM, 12.0, 1.8, 0.5, 0, 0, 0.25, 0.2, pick='x', small=0.0)
keep('rt_coping')

# ------------------------------------------------------------------ rt_kiosk
bx('concrete', COPE, 12.4, 11.2, 0.8, 0, 0, 0.4, 0.18)
soft('concrete', WALL, 12.0, 10.8, 7.4, 0, 0, 4.0, 0.35, pick='up')
bx('plastic', TRIM, 12.3, 11.1, 0.5, 0, 0, 7.45, 0.12)
soft('plastic', GRAPH, 13.2, 12.0, 0.7, 0, 0, 8.05, 0.3, pick='up')
bx('plastic', DARK, 7.4, 0.4, 6.6, 0, -5.38, 3.9, 0.1)
for sx in (-1.78, 1.78): louvre(sx, -5.45, 3.9, 3.3, 6.0, 0.0, n=9, frame=MIDG, slat=CASE)
bx('plastic', AMBER, 1.3, 0.3, 1.3, 4.9, -5.42, 5.2, 0.12)
doorlamp(0, -5.4, 7.0, w=3.4)
soft('plastic', CASE, 1.6, 3.4, 2.8, 6.7, 1.2, 2.6, 0.3, pick='all')
cy('plastic', TRIM, 1.1, 0.3, 7.55, 1.2, 2.6, axis='x', segs=18, bevel=0.08)
cy('plastic', DARK, 0.85, 0.34, 7.56, 1.2, 2.6, axis='x', segs=18, bevel=0.02)
cy('plastic', MIDG, 0.22, 6.4, 6.15, -3.6, 3.9, segs=8, bevel=0.05)
keep('rt_kiosk')

# ------------------------------------------------------------------ rt_cowl
bx('concrete', COPE, 6.0, 6.0, 0.8, 0, 0, 0.4, 0.18)
cy('plastic', CASE, 2.5, 2.4, 0, 0, 2.0, segs=24, bevel=0.2)
cy('plastic', DARK, 2.1, 0.5, 0, 0, 3.35, segs=24, bevel=0.02)
lathe('plastic', TRIM, dome_prof(2.9, 0.9, rim=0.3, steps=6), T(0, 0, 3.5), segs=24)
keep('rt_cowl')

# ------------------------------------------------------------------ rt_tank
for sx in (-2.8, 2.8):
    bx('concrete', COPE, 1.2, 4.6, 1.7, sx, 0, 0.85, 0.15)
    cy('plastic', TRIM, 2.42, 0.45, sx, 0, 3.2, axis='x', segs=24, bevel=0.1)
cy('plastic', CASE, 2.3, 7.0, 0, 0, 3.2, axis='x', segs=24, bevel=0.02)
for s in (-1, 1):
    lathe('plastic', CASE, dome_prof(2.3, 1.5, steps=6), T(s * 3.5, 0, 3.2) @ RY(s * math.pi / 2), segs=24)
cy('plastic', MIDG, 0.7, 0.5, 0.8, 0, 5.6, segs=14, bevel=0.1)
cy('plastic', MIDG, 0.3, 2.6, -1.2, -1.9, 4.2, segs=8, bevel=0.05)
bx('plastic', AMBER, 0.5, 0.25, 2.2, 1.6, -2.28, 3.2, 0.08)
both('rt_tank')

# ------------------------------------------------------------------ rt_walllamp
bx('plastic', DARK, 2.4, 1.0, 0.6, 0, 0, 0.5, 0.14)
bx('neon', WARM, 2.0, 0.74, 0.2, 0, -0.03, 0.15, 0.05)
keep('rt_walllamp')

# ------------------------------------------------------------------ rt_liftsign
soft('plastic', '16181d', 4.6, 0.36, 1.7, 0, 0, 0.85, 0.12, pick='y')
bx('plastic', AMBER, 4.6, 0.4, 0.14, 0, -0.02, 0.07, 0.03)
keep('rt_liftsign')

# ------------------------------------------------------------------ round 2 (after the first judging)
# rt_plinth: a kerbed plinth, 22 x 12 x 1, for a second plant group between the spawns and the roof's edge
soft('concrete', COPE, 22.0, 12.0, 1.0, 0, 0, 0.5, 0.7, pick='up', segs=3, small=0.22)
bx('concrete', MIDG, 20.2, 10.2, 0.12, 0, 0, 1.0, 0.0)
keep('rt_plinth')

# rt_stack: three flues on a curb, 6 x 6 x 11.6: the tall thing a roof needs beside its hut
bx('concrete', COPE, 6.0, 6.0, 0.8, 0, 0, 0.4, 0.18)
for (x, y, r, h) in ((-1.3, -1.0, 1.15, 10.0), (1.45, -0.8, 0.95, 7.6), (0.2, 1.6, 0.85, 5.6)):
    cy('plastic', TRIM, r + 0.3, 0.5, x, y, 1.05, bevel=0.12, segs=16)
    cy('plastic', CASE, r, h, x, y, 0.8 + h / 2, bevel=0.1, segs=16)
    cy('plastic', TRIM, r + 0.16, 0.5, x, y, 0.8 + h * 0.62, bevel=0.1, segs=16)
    cy('plastic', DARK, r * 0.78, 0.3, x, y, 0.8 + h + 0.1, bevel=0.02, segs=16)
    cy('plastic', GRAPH, r + 0.45, 0.7, x, y, 0.8 + h + 0.55, r2=r * 0.5, bevel=0.08, segs=16)
bx('plastic', GRAPH, 3.6, 0.45, 0.5, 0.1, -0.9, 4.6, 0.1)
both('rt_stack')

# rt_ductL: a waist-high duct that turns a corner, 12 along X then 8 along -Y, on stands
soft('plastic', CASE, 12.0, 2.2, 1.8, 0, 0, 2.1, 0.3, pick='x')
soft('plastic', CASE, 2.2, 8.0, 1.8, 6.0, -4.0, 2.1, 0.3, pick='y')
cy('plastic', CASE, 1.5, 1.8, 6.0, 0, 2.1, segs=20, bevel=0.3)
for x in (-4.5, -0.5, 3.5): bx('plastic', TRIM, 0.35, 2.5, 2.1, x, 0, 2.1, 0.08)
for y in (-3.0, -6.6): bx('plastic', TRIM, 2.5, 0.35, 2.1, 6.0, y, 2.1, 0.08)
louvre(6.0, -8.0, 2.1, 1.9, 1.5, 0.0, n=3)
for (x, y, turn) in ((-5.0, 0, 0), (0.5, 0, 0), (6.0, -5.0, 1)):
    M = T(x, y, 0) @ RZ(turn * math.pi / 2)
    bx('concrete', COPE, 1.4, 3.4, 0.3, 0, 0, 0.15, 0.08, M)
    bx('plastic', GRAPH, 0.5, 2.8, 0.4, 0, 0, 1.0, 0.1, M)
    for sy in (-1.1, 1.1): bx('plastic', GRAPH, 0.45, 0.45, 0.9, 0, sy, 0.6, 0.08, M)
both('rt_ductL')

# rt_barrel: one long barrel rooflight, 15 x 5 x 2.9 (it stands in for the three domes in a row)
soft('plastic', TRIM, 15.0, 5.0, 0.8, 0, 0, 0.4, 0.35, pick='up')
bx('neon', ROOM, 13.2, 3.0, 0.1, 0, 0, 0.84, 0.02)
cy('glass', GLASS, 2.05, 14.0, 0, 0, 0.8, axis='x', segs=24, bevel=0.02)
for x in (-6.9, -3.45, 0, 3.45, 6.9): cy('plastic', GRAPH, 2.2, 0.36, x, 0, 0.8, axis='x', segs=24, bevel=0.06)
bx('plastic', GRAPH, 14.2, 0.36, 0.3, 0, 0, 2.95, 0.08)
keep('rt_barrel')

export_all('roofdress.glb')
argv = sys.argv[sys.argv.index('--') + 1:]
if len(argv) > 1: preview(argv[1], cols=5)
