"""Mixamo clip (.fbx) -> every bone's world turn and the hips' place, frame by frame, as JSON (Blender axes), headless.

run:  blender.exe -b --factory-startup -P tools/motionbricks/mixamo_rot_sample.py -- <in.fbx> <out.json>

(19 Nov 2026, the MotionBricks trial: tools/motionbricks/README.md) the poses we hand NVIDIA's MotionBricks come from
our own Mixamo clips (its bundled sample clips are evaluation-only), retargeted onto its SOMA skeleton by mb_gen.py.
  * Blender axes as imported (Z up; a Mixamo body faces -Y), metres (the armature's 0.01 is in matrix_world).
  * rest: each bone's world turn (3x3, columns = its axes) and head in the T-pose; frames: each bone's world turn and
    the hips' head. a turn against the rest, D = R(t) R(rest)^-1, is what mixamo_r15.py puts on the R15 parts.
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
P = 'mixamorig:'
BONES = ['Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head', 'HeadTop_End',
         'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand', 'LeftHandMiddle1',
         'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand', 'RightHandMiddle1',
         'LeftUpLeg', 'LeftLeg', 'LeftFoot', 'LeftToeBase', 'LeftToe_End',
         'RightUpLeg', 'RightLeg', 'RightFoot', 'RightToeBase', 'RightToe_End']
have = [b for b in BONES if (P + b) in arm.pose.bones]
mw = arm.matrix_world
def rot3(m4):
    m = m4.to_3x3()
    return Matrix([c.normalized() for c in m.transposed()]).transposed()  # (columns to unit length: the 0.01 scale)
def m3(R): return [[round(R[i][j], 6) for j in range(3)] for i in range(3)]
def v3(v): return [round(v.x, 6), round(v.y, 6), round(v.z, 6)]
rest = {}
for b in have:
    bone = arm.data.bones[P + b]
    par = bone.parent.name[len(P):] if bone.parent and bone.parent.name.startswith(P) else None
    rest[b] = { 'rot': m3(rot3(mw @ bone.matrix_local)), 'head': v3(mw @ bone.head_local), 'parent': par }
frames = []
for f in range(f0, f1 + 1):
    bpy.context.scene.frame_set(f)
    rots = { b: m3(rot3(mw @ arm.pose.bones[P + b].matrix)) for b in have }
    heads = { b: v3(mw @ arm.pose.bones[P + b].head) for b in have }
    frames.append({ 'f': f, 'rot': rots, 'head': heads })
json.dump({ 'src': src.replace('\\', '/').split('/')[-1], 'fps': fps, 'f0': f0, 'f1': f1, 'bones': have, 'rest': rest,
            'frames': frames }, open(out, 'w'))
print('sampled %d frames at %g fps, %d bones -> %s' % (len(frames), fps, len(have), out))
