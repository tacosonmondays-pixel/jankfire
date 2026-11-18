"""Mixamo clip (.fbx, mixamorig skeleton) -> a Roblox R15 KeyframeSequence (.rbxmx), headless.

run:  blender.exe -b --factory-startup -P tools/blender/mixamo_r15.py -- <in.fbx> <out.rbxm> [--name N] [--hip 2.2]
      [--priority idle|movement|action|core] [--no-loop] [--blend 6] [--every 1] [--keep-drift]
      [--from F] [--to F] [--warp "s:t,s:t,..."] [--upper]
then: upload <out.rbxm> through Open Cloud as assetType "Animation" (approved at once; the id plays on any R15 Animator).
      Open Cloud refuses an XML file for an Animation ("not supported yet"), so a .rbxm out is built from the .rbxmx it
      writes beside it with Rojo (ROJO, or ~/.aftman/tool-storage/rojo-rbx/rojo/7.7.1/rojo.exe). an .rbxmx out is just
      the XML.

how (17 Nov 2026, the shopkeeper's and the hub regulars' mocap idles):
  * each R15 part follows one Mixamo bone: LowerTorso Hips, UpperTorso Spine2 (Spine and Spine1 fold into the waist),
    Head Head (Neck folds in), the arms Arm / ForeArm / Hand, the legs UpLeg / Leg / Foot (shoulders and toes fold in).
  * a bone's turn this frame is its world rotation against its rest (Mixamo's T-pose), D = R(t) R(rest)^-1. the R15
    part gets that turn on top of where it would be if the R15 rig stood in Mixamo's rest pose: its arms raised to the
    T (R15's rest has them down), everything else as R15's rest. so W(part) = D Q(part), and a joint's pose is
    W(parent)^-1 W(child) (R15's joints have no turn of their own at rest).
  * Blender (x, y, z) -> Roblox (-x, z, y): Mixamo faces Blender -Y, Roblox characters face -Z.
  * the hips' movement goes on the Root pose (HumanoidRootPart -> LowerTorso), scaled from metres by hip / Mixamo's hip
    height (hip = an R15 avatar's LowerTorso over the floor, studs). its sideways drift is taken out: the line from the
    first frame to the last is removed (so it loops), then the middle (so it sways about where he stands). up and down
    stays. --keep-drift keeps it all.
  * looping clips (last frame = the first) drop the last frame; others get their last --blend frames eased into the first.
  * prints a summary: frames, length, how far the hips sway, each part's largest turn.
  (18 Nov 2026, the scythe's mocap attacks) --from / --to keep only those source frames; --warp maps each keyframe's
  time (seconds from --from) through a piecewise-linear line of source:clip pairs, so a strike's hit can land when
  the game judges it; --upper keys only the waist, the head and the arms (the hips, the legs and the root are left
  unkeyed: weight 0), so the legs keep walking under it.
"""
import bpy, sys, math, json
from mathutils import Matrix, Vector, Quaternion

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if len(argv) < 2:
    print('usage: blender -b --factory-startup -P mixamo_r15.py -- in.fbx out.rbxmx [--name N] [--hip 2.2]'); sys.exit(1)
src, out = argv[0], argv[1]
def opt(name, default):
    return argv[argv.index(name) + 1] if name in argv else default
NAME = opt('--name', out.replace('\\', '/').split('/')[-1].rsplit('.', 1)[0])
HIP = float(opt('--hip', '2.2'))
EVERY = max(1, int(opt('--every', '1')))
BLEND = int(opt('--blend', '6'))
LOOP = '--no-loop' not in argv
KEEP_DRIFT = '--keep-drift' in argv
PRIORITY = { 'idle': 0, 'movement': 1, 'action': 2, 'core': 1000 }[opt('--priority', 'idle')]
UPPER = '--upper' in argv
WARP = [tuple(float(x) for x in kv.split(':')) for kv in opt('--warp', '').split(',') if kv]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src, automatic_bone_orientation=False)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = arm.animation_data.action
f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
if '--from' in argv: f0 = max(f0, int(opt('--from', f0)))
if '--to' in argv: f1 = min(f1, int(opt('--to', f1)))
fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base

M = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))  # Blender world -> Roblox world
P = 'mixamorig:'
# R15 part -> its Mixamo bone, its parent part, and Q (where it stands when the R15 rig takes Mixamo's rest pose)
RZ = lambda deg: Matrix.Rotation(math.radians(deg), 3, 'Z')
PARTS = [
    ('LowerTorso', 'Hips', 'HumanoidRootPart', Matrix.Identity(3)),
    ('UpperTorso', 'Spine2', 'LowerTorso', Matrix.Identity(3)),
    ('Head', 'Head', 'UpperTorso', Matrix.Identity(3)),
    ('LeftUpperArm', 'LeftArm', 'UpperTorso', RZ(-90)), ('LeftLowerArm', 'LeftForeArm', 'LeftUpperArm', RZ(-90)), ('LeftHand', 'LeftHand', 'LeftLowerArm', RZ(-90)),
    ('RightUpperArm', 'RightArm', 'UpperTorso', RZ(90)), ('RightLowerArm', 'RightForeArm', 'RightUpperArm', RZ(90)), ('RightHand', 'RightHand', 'RightLowerArm', RZ(90)),
    ('LeftUpperLeg', 'LeftUpLeg', 'LowerTorso', Matrix.Identity(3)), ('LeftLowerLeg', 'LeftLeg', 'LeftUpperLeg', Matrix.Identity(3)), ('LeftFoot', 'LeftFoot', 'LeftLowerLeg', Matrix.Identity(3)),
    ('RightUpperLeg', 'RightUpLeg', 'LowerTorso', Matrix.Identity(3)), ('RightLowerLeg', 'RightLeg', 'RightUpperLeg', Matrix.Identity(3)), ('RightFoot', 'RightFoot', 'RightLowerLeg', Matrix.Identity(3)),
]
TREE = { 'HumanoidRootPart': ['LowerTorso'], 'LowerTorso': ['UpperTorso', 'LeftUpperLeg', 'RightUpperLeg'],
         'UpperTorso': ['Head', 'LeftUpperArm', 'RightUpperArm'], 'LeftUpperArm': ['LeftLowerArm'], 'LeftLowerArm': ['LeftHand'],
         'RightUpperArm': ['RightLowerArm'], 'RightLowerArm': ['RightHand'], 'LeftUpperLeg': ['LeftLowerLeg'], 'LeftLowerLeg': ['LeftFoot'],
         'RightUpperLeg': ['RightLowerLeg'], 'RightLowerLeg': ['RightFoot'] }

def rot3(m4):
    m = m4.to_3x3()
    return Matrix([c.normalized() for c in m.transposed()]).transposed()  # (columns to unit length: the armature is at 0.01)
mw = arm.matrix_world
rest = { b.name: rot3(mw @ b.matrix_local) for b in arm.data.bones }
hips_rest = mw @ arm.data.bones[P + 'Hips'].head_local
mix_hip = hips_rest.z  # metres over the floor (Mixamo stands at z = 0)
scale = HIP / mix_hip

frames = list(range(f0, f1 + 1, EVERY))
raw = []  # per frame: { part: world rotation (Roblox) }, hips offset (Roblox, studs)
for f in frames:
    bpy.context.scene.frame_set(f)
    W = { 'HumanoidRootPart': Matrix.Identity(3) }
    for part, bone, parent, Q in PARTS:
        pb = arm.pose.bones[P + bone]
        D = rot3(mw @ pb.matrix) @ rest[P + bone].transposed()
        W[part] = M @ D @ M.transposed() @ Q
    h = mw @ arm.pose.bones[P + 'Hips'].head
    off = M @ (h - hips_rest) * scale
    raw.append((W, Vector(off)))

def joint_poses(W):
    return { part: W[parent].transposed() @ W[part] for part, bone, parent, Q in PARTS }

# looping: a clip whose last frame is its first drops it; another eases its last BLEND frames into the first
def same(a, b):
    for p in a[0]:
        if a[0][p].to_quaternion().rotation_difference(b[0][p].to_quaternion()).angle > 0.02: return False
    return (a[1] - b[1]).length < 0.02
looped_already = len(raw) > 2 and same(raw[0], raw[-1])
if LOOP and looped_already:
    raw = raw[:-1]; frames = frames[:-1]
poses = [(joint_poses(W), off) for W, off in raw]
if LOOP and not looped_already and BLEND > 0 and len(poses) > BLEND + 2:
    first = poses[0]
    n = len(poses)
    for k in range(BLEND):
        i = n - BLEND + k
        a = (k + 1) / (BLEND + 1)
        a = a * a * (3 - 2 * a)
        rots = { p: poses[i][0][p].to_quaternion().slerp(first[0][p].to_quaternion(), a).to_matrix() for p in poses[i][0] }
        poses[i] = (rots, poses[i][1].lerp(first[1], a))

# the hips' sideways drift out (x and z): the first-to-last line, then the middle
if not KEEP_DRIFT and len(poses) > 1:
    a, b = poses[0][1], poses[-1][1]
    n = len(poses)
    lined = []
    for i, (r, off) in enumerate(poses):
        t = i / (n - 1)
        o = off.copy(); o.x -= a.x + (b.x - a.x) * t; o.z -= a.z + (b.z - a.z) * t
        lined.append((r, o))
    mx = sum(o.x for _, o in lined) / n
    mz = sum(o.z for _, o in lined) / n
    poses = [(r, Vector((o.x - mx, o.y, o.z - mz))) for r, o in lined]

# ---------------------------------------------------------------- the .rbxmx
ref = [0]
def nref():
    ref[0] += 1
    return 'RBX%08X' % ref[0]
def cf_xml(name, pos, R):
    v = [pos.x, pos.y, pos.z] + [R[i][j] for i in range(3) for j in range(3)]
    tags = ['X', 'Y', 'Z', 'R00', 'R01', 'R02', 'R10', 'R11', 'R12', 'R20', 'R21', 'R22']
    return '<CoordinateFrame name="%s">%s</CoordinateFrame>' % (name, ''.join('<%s>%.6f</%s>' % (t, x, t) for t, x in zip(tags, v)))
UNKEYED = { 'HumanoidRootPart', 'LowerTorso' } if UPPER else set()
LEGS = { 'LeftUpperLeg', 'RightUpperLeg' }
def pose_xml(part, rots, hips):
    R = Matrix.Identity(3) if part == 'HumanoidRootPart' or part in UNKEYED else rots[part]
    pos = hips if part == 'LowerTorso' and not UPPER else Vector((0, 0, 0))
    kids = ''.join(pose_xml(c, rots, hips) for c in TREE.get(part, []) if not (UPPER and c in LEGS))
    wt = 0 if part in UNKEYED else 1
    return ('<Item class="Pose" referent="%s"><Properties><string name="Name">%s</string>%s<float name="Weight">%d</float>'
            '<token name="EasingStyle">0</token><token name="EasingDirection">0</token></Properties>%s</Item>') % (nref(), part, cf_xml('CFrame', pos, R), wt, kids)
def warp(t):
    if not WARP: return t
    if t <= WARP[0][0]: return WARP[0][1] + (t - WARP[0][0])
    for (s0, d0), (s1, d1) in zip(WARP, WARP[1:]):
        if t <= s1: return d0 + (t - s0) * (d1 - d0) / (s1 - s0)
    return WARP[-1][1] + (t - WARP[-1][0])
items = []
for i, (rots, hips) in enumerate(poses):
    t = warp((frames[i] - frames[0]) / fps)
    items.append('<Item class="Keyframe" referent="%s"><Properties><string name="Name">Keyframe</string><float name="Time">%.5f</float></Properties>%s</Item>'
                 % (nref(), t, pose_xml('HumanoidRootPart', rots, hips)))
length = warp((frames[-1] - frames[0]) / fps) + (EVERY / fps if LOOP else 0)
if LOOP:  # (the loop's last key: the first pose again at the full length, so the track's Length is the whole cycle)
    rots, hips = poses[0]
    items.append('<Item class="Keyframe" referent="%s"><Properties><string name="Name">Keyframe</string><float name="Time">%.5f</float></Properties>%s</Item>'
                 % (nref(), length, pose_xml('HumanoidRootPart', rots, hips)))
xml = ('<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" version="4"><Item class="KeyframeSequence" referent="%s"><Properties>'
       '<string name="Name">%s</string><bool name="Loop">%s</bool><token name="Priority">%d</token></Properties>%s</Item></roblox>'
       % (nref(), NAME, 'true' if LOOP else 'false', PRIORITY, ''.join(items)))
binary = out.lower().endswith('.rbxm')
xml_path = out + 'x' if binary else out
open(xml_path, 'w', encoding='utf-8').write(xml)
if binary:
    import os, subprocess
    rojo = os.environ.get('ROJO') or os.path.join(os.path.expanduser('~'), '.aftman', 'tool-storage', 'rojo-rbx', 'rojo', '7.7.1', 'rojo.exe')
    proj = out + '.project.json'
    open(proj, 'w', encoding='utf-8').write(json.dumps({ 'name': NAME, 'tree': { '$path': os.path.basename(xml_path) } }))
    subprocess.run([rojo, 'build', proj, '-o', out], check=True)
    os.remove(proj)

# ---------------------------------------------------------------- the summary
turn = {}
for rots, _ in poses:
    for p, R in rots.items():
        turn[p] = max(turn.get(p, 0), math.degrees(R.to_quaternion().angle))
xs = [o.x for _, o in poses]; ys = [o.y for _, o in poses]; zs = [o.z for _, o in poses]
summary = { 'name': NAME, 'keyframes': len(items), 'length': round(length, 3), 'fps': fps, 'looped_already': looped_already,
            'scale_studs_per_m': round(scale, 3), 'hips_sway_studs': { 'x': [round(min(xs), 3), round(max(xs), 3)], 'y': [round(min(ys), 3), round(max(ys), 3)], 'z': [round(min(zs), 3), round(max(zs), 3)] },
            'largest_turn_deg': { p: round(v, 1) for p, v in sorted(turn.items(), key=lambda kv: -kv[1]) } }
print('MIXAMO_R15 ' + json.dumps(summary))
