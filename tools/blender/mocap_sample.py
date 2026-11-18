"""Mixamo clip (.fbx) -> every frame's joint positions and hand turns as JSON (Roblox axes, metres), headless.

run:  blender.exe -b --factory-startup -P tools/blender/mocap_sample.py -- <in.fbx> <out.json>

(18 Nov 2026, the scythe's mocap attacks) the pose strips (tools/roblox/mocap_strip.py) and the first-person clips
(tools/roblox/mocap_vm.py) are drawn from this: where each joint is, frame by frame, and how each hand is turned.
  * Blender (x, y, z) -> Roblox (-x, z, y), as mixamo_r15.py: Mixamo faces Blender -Y, so the body faces Roblox -Z.
  * positions are each bone's head (its joint), in metres; "end" bones give the hands' and the head's tips.
  * hands: each hand bone's world turn (columns = its x, y, z axes in Roblox space); a Mixamo hand bone's y runs
    from the wrist to the fingers.
"""
import bpy, sys, json
from mathutils import Matrix

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
src, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src, automatic_bone_orientation=False)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = arm.animation_data.action
f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
M = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))
P = 'mixamorig:'
BONES = ['Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head', 'HeadTop_End',
         'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand', 'LeftHandMiddle1',
         'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand', 'RightHandMiddle1',
         'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase']
have = [b for b in BONES if (P + b) in arm.pose.bones]
mw = arm.matrix_world
def rot3(m4):
    m = m4.to_3x3()
    return Matrix([c.normalized() for c in m.transposed()]).transposed()
frames = []
for f in range(f0, f1 + 1):
    bpy.context.scene.frame_set(f)
    pos = {}
    for b in have:
        p = M @ (mw @ arm.pose.bones[P + b].head)
        pos[b] = [round(p.x, 5), round(p.y, 5), round(p.z, 5)]
    hands = {}
    for b in ('LeftHand', 'RightHand', 'Head', 'Spine2', 'Hips'):
        if (P + b) in arm.pose.bones:
            R = M @ rot3(mw @ arm.pose.bones[P + b].matrix) @ M.transposed()
            hands[b] = [[round(R[i][j], 5) for j in range(3)] for i in range(3)]
    frames.append({ 'f': f, 'pos': pos, 'rot': hands })
json.dump({ 'src': src.replace('\\', '/').split('/')[-1], 'fps': fps, 'f0': f0, 'f1': f1, 'frames': frames }, open(out, 'w'))
print('sampled %d frames at %g fps, %d bones -> %s' % (len(frames), fps, len(have), out))
