# THE GYM'S BOXING GLOVES (19 Nov 2026; the boxing mini-game, roblox/docs/MINIGAMES.md). welded to a boxer's hands for a
# bout only (server/MiniGames.server ctx.gloves). the chunky way: one padded fist with the thumb grown into it (a voxel
# remesh, no stuck-on thumb), a cream cuff with one amber band. the fist's colour is set per corner in the game
# (the mesh is painted mid grey: the part's Color is the glove's colour).
# 1 unit = 1 stud, Z up; (Roblox X, Y, Z) = (x, z, -y). the origin is the middle of the avatar's hand: the glove runs
# along the forearm (Roblox +Y = toward the elbow, the cuff), the fist past the fingers (Roblox -Y), the thumb on the
# back of the hand's front face (Roblox -Z = Blender +y)
#   mg_glove   a glove (both hands use it)
# run: blender -b --factory-startup -P tools/roblox/boxing_models.py -- <out_dir> [preview.jpg]
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from structkit import *
import bpy

GLOVE, CUFF, BAND = 'a3a3a3', 'e6e0d4', 'e0ac3c'
reset()

def fuse(voxel=0.02, ratio=0.35):
    _, objs, _, _ = MODELS[-1]
    for o in objs:
        if '__plastic_' + GLOVE not in o.name: continue
        rm = o.modifiers.new('rm', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = voxel; rm.use_smooth_shade = True
        sm = o.modifiers.new('sm', 'SMOOTH'); sm.factor = 0.7; sm.iterations = 6
        dc = o.modifiers.new('dc', 'DECIMATE'); dc.ratio = ratio
        if o.modifiers.get('wn'): o.modifiers.move(o.modifiers.find('wn'), len(o.modifiers) - 1)

# the fist: a big rounded pad past the fingers, swelling forward over the knuckles
soft('plastic', GLOVE, 0.92, 0.8, 1.0, 0, 0.02, -0.2, 0.34, pick='all', segs=4, small=0.0)
ball('plastic', GLOVE, 0.42, 0, 0.12, -0.38, sc=(1.05, 0.95, 1.0), sub=3)          # (the striking face, fuller)
# the thumb, lying along the front of the fist, grown into it
soft('plastic', GLOVE, 0.26, 0.3, 0.62, -0.24, 0.36, -0.02, 0.12, pick='all', segs=3, small=0.0)
# the wrist the cuff closes over (fused into the fist)
cy('plastic', GLOVE, 0.33, 0.3, 0, 0, 0.32, segs=24, bevel=0.06)
# the cuff and its band
lathe('plastic', CUFF, [(0.0, 0.42), (0.35, 0.42), (0.38, 0.47), (0.38, 0.86), (0.34, 0.9), (0.0, 0.9)], segs=28)
lathe('plastic', BAND, [(0.0, 0.55), (0.393, 0.55), (0.393, 0.63), (0.0, 0.63)], segs=28)
keep('mg_glove'); fuse()

export_all('boxing.glb')
if len(sys.argv) > sys.argv.index('--') + 2:
    preview(sys.argv[sys.argv.index('--') + 2], cols=2, gap=1.0)
