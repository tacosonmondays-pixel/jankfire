# Finisher storyboards on real R15 rigs (the owner, 19 Nov: "the joints are wacky, will you use an R15 dummy?").
# Poses are keyed here as R15 joint rotations (elbows, knees, wrists, waist), solved forward with the exact attachment
# offsets of the place's R15 rig (ServerStorage.PolishBackup.AnimTrial.Rig, AnimationConstraints), so the same part
# CFrames can be (1) previewed fast in headless Blender and (2) placed, anchored, on real rigs in Studio (Edit) for the
# photos. Scene layout is written in Blender axes (Z up, +Y forward); the rigs' maths runs in Roblox axes (Y up,
# -Z forward) and is mapped across with Blender = (x, -z, y).
# run: blender -b --factory-startup -P tools/roblox/finisher_r15.py -- <outdir> [board[:n,n]]
#   writes <board>_<n>.png (preview) and <board>_<n>.json (part CFrames, props, lens: Roblox axes) per frame
import bpy, bmesh, math, json, sys, os, random
import xml.etree.ElementTree as ET
from mathutils import Vector, Matrix, Euler, Quaternion
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]
ONLY = {}
SHEETS = [a_ for a_ in argv[1:] if a_.startswith('sheet:')]
VIDS = [a_.split(':', 1)[1] for a_ in argv[1:] if a_.startswith('video:')]   # video:tide -> the moving cut, frame by frame
argv = [a_ for a_ in argv if not a_.startswith('sheet:') and not a_.startswith('video:')]
for a_ in argv[1:]:
    k_, _, n_ = a_.partition(':')
    ONLY[k_] = {int(x) for x in n_.split(',')} if n_ else None
os.makedirs(OUT, exist_ok=True)
RW, RH = 960, 540
sc = bpy.context.scene

# ------------------------------------------------------------------ Roblox <-> Blender
MB = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # Roblox -> Blender (a point or a frame)
MB_INV = MB.inverted()


def rb(v):  # a Blender point -> Roblox
    return (MB_INV @ Vector((v[0], v[1], v[2], 1))).xyz


def br(v):  # a Roblox point -> Blender
    return (MB @ Vector((v[0], v[1], v[2], 1))).xyz


def CF(x=0, y=0, z=0):
    return Matrix.Translation((x, y, z))


def ANG(x=0, y=0, z=0):  # CFrame.Angles (degrees): Rx * Ry * Rz
    return (Matrix.Rotation(math.radians(x), 4, 'X') @ Matrix.Rotation(math.radians(y), 4, 'Y') @
            Matrix.Rotation(math.radians(z), 4, 'Z'))


def comps(m):  # a CFrame's 12 components (x, y, z, R00..R22), as GetComponents gives them
    return [round(m[0][3], 4), round(m[1][3], 4), round(m[2][3], 4),
            round(m[0][0], 5), round(m[0][1], 5), round(m[0][2], 5),
            round(m[1][0], 5), round(m[1][1], 5), round(m[1][2], 5),
            round(m[2][0], 5), round(m[2][1], 5), round(m[2][2], 5)]


# ------------------------------------------------------------------ the R15 rig (the place's, read 19 Nov)
SIZE = {'HumanoidRootPart': (2, 2, 1), 'LowerTorso': (2, 0.4, 1), 'UpperTorso': (2, 1.6, 1), 'Head': (1.2, 1.2, 1.2),
        'RightUpperArm': (1, 1.1687, 1), 'RightLowerArm': (1, 1.0519, 1), 'RightHand': (1, 0.3, 1),
        'LeftUpperArm': (1, 1.1687, 1), 'LeftLowerArm': (1, 1.0519, 1), 'LeftHand': (1, 0.3, 1),
        'RightUpperLeg': (1, 1.2166, 1), 'RightLowerLeg': (1, 1.1931, 1), 'RightFoot': (1, 0.3, 1),
        'LeftUpperLeg': (1, 1.2166, 1), 'LeftLowerLeg': (1, 1.1931, 1), 'LeftFoot': (1, 0.3, 1)}
# joint: (parent, child, attachment in the parent, attachment in the child)
JOINTS = [('Root', 'HumanoidRootPart', 'LowerTorso', (0, -1, 0), (0, -0.2, 0)),
          ('Waist', 'LowerTorso', 'UpperTorso', (0, 0.2, 0), (0, -0.8, 0)),
          ('Neck', 'UpperTorso', 'Head', (0, 0.8, 0), (0, -0.586, 0)),
          ('RightShoulder', 'UpperTorso', 'RightUpperArm', (1, 0.563, 0), (-0.5, 0.3943, 0)),
          ('RightElbow', 'RightUpperArm', 'RightLowerArm', (0, -0.3342, 0), (0, 0.2586, 0)),
          ('RightWrist', 'RightLowerArm', 'RightHand', (0, -0.5009, 0), (0, 0.125, 0)),
          ('LeftShoulder', 'UpperTorso', 'LeftUpperArm', (-1, 0.563, 0), (0.5, 0.3943, 0)),
          ('LeftElbow', 'LeftUpperArm', 'LeftLowerArm', (0, -0.3341, 0), (0, 0.2587, 0)),
          ('LeftWrist', 'LeftLowerArm', 'LeftHand', (0, -0.5009, 0), (0, 0.125, 0)),
          ('RightHip', 'LowerTorso', 'RightUpperLeg', (0.5, -0.2, 0), (0, 0.4208, 0)),
          ('RightKnee', 'RightUpperLeg', 'RightLowerLeg', (0, -0.4009, 0), (0, 0.3792, 0)),
          ('RightAnkle', 'RightLowerLeg', 'RightFoot', (0, -0.5472, 0), (0, 0.1019, 0)),
          ('LeftHip', 'LowerTorso', 'LeftUpperLeg', (-0.5, -0.2, 0), (0, 0.4208, 0)),
          ('LeftKnee', 'LeftUpperLeg', 'LeftLowerLeg', (0, -0.4011, 0), (0, 0.379, 0)),
          ('LeftAnkle', 'LeftLowerLeg', 'LeftFoot', (0, -0.5472, 0), (0, 0.1019, 0))]


CLIPDIR = os.environ.get('FIN_CLIPS', os.path.join(os.path.dirname(OUT.rstrip('/\\')), 'clips'))
_CLIPS = {}
PART_JOINT = {p1: name for name, p0, p1, a0, a1 in JOINTS}


def clip(name):
    # the owner's rule (19 Nov): every pose comes from a real reference, here a mocap clip (Mixamo or a MotionBricks take
    # made from our Mixamo clips), turned into R15 joint rotations by tools/blender/mixamo_r15.py
    if name not in _CLIPS:
        tree = ET.parse(os.path.join(CLIPDIR, name + '.rbxmx'))
        kfs = []
        for kf in tree.iter('Item'):
            if kf.get('class') != 'Keyframe':
                continue
            t = float(kf.find("Properties/float[@name='Time']").text)
            poses = {}
            for ps in kf.iter('Item'):
                if ps.get('class') != 'Pose':
                    continue
                nm = ps.find("Properties/string[@name='Name']").text
                ce = ps.find("Properties/CoordinateFrame[@name='CFrame']")
                v = [float(ce.find(tag).text) for tag in ('X', 'Y', 'Z', 'R00', 'R01', 'R02', 'R10', 'R11', 'R12', 'R20', 'R21', 'R22')]
                poses[nm] = Matrix(((v[3], v[4], v[5], v[0]), (v[6], v[7], v[8], v[1]), (v[9], v[10], v[11], v[2]), (0, 0, 0, 1)))
            kfs.append((t, poses))
        kfs.sort(key=lambda x: x[0])
        _CLIPS[name] = kfs
    return _CLIPS[name]


def clip_len(name):
    return clip(name)[-1][0]


LOOPS = {'mx_ninja_run', 'kp_runanimationset_forward_keyframesequence', 'id_06_dune_weight_shift'}


def clip_pose(name, t):
    if name in LOOPS:
        kfs = clip(name)
        L = kfs[-1][0]
        cyc = math.floor(t / L) if L > 0 else 0
        out = clip_pose_raw(name, t - cyc * L)
        if cyc and 'LowerTorso' in out:
            step = kfs[-1][1]['LowerTorso'].translation - kfs[0][1]['LowerTorso'].translation
            step.y = 0.0
            m = out['LowerTorso'].copy()
            m.translation = m.translation + step * cyc
            out['LowerTorso'] = m
        return out
    return clip_pose_raw(name, t)


_TRACKS = {}


def clip_pose_raw(name, t):
    # each joint on its own track (a keyframe may leave a joint out: the bought pack does), linear between its keys
    kfs = clip(name)
    if name not in _TRACKS:
        tr = {}
        for kt, poses in kfs:
            for part, m in poses.items():
                tr.setdefault(part, []).append((kt, m))
        _TRACKS[name] = tr
    t = max(kfs[0][0], min(kfs[-1][0], t))
    out = {}
    for part, keys in _TRACKS[name].items():
        if t <= keys[0][0] or len(keys) == 1:
            out[part] = keys[0][1].copy()
            continue
        if t >= keys[-1][0]:
            out[part] = keys[-1][1].copy()
            continue
        i = 0
        while i < len(keys) - 2 and keys[i + 1][0] <= t:
            i += 1
        (t0, ma), (t1, mb) = keys[i], keys[i + 1]
        u = 0 if t1 <= t0 else (t - t0) / (t1 - t0)
        q = ma.to_quaternion().slerp(mb.to_quaternion(), u)
        m = q.to_matrix().to_4x4()
        m.translation = ma.translation.lerp(mb.translation, u)
        out[part] = m
    return out


def aim_rot(d, twist=0.0):
    # the joint rotation that turns a limb hanging straight down (0,-1,0) to point along d (in the parent's axes)
    d = Vector(d).normalized()
    q = Vector((0, -1, 0)).rotation_difference(d)
    return q.to_matrix().to_4x4() @ Matrix.Rotation(math.radians(twist), 4, 'Y')


def solve(root_cf, pose):
    # pose keys: joint name -> 4x4 rotation; shortcuts: armR/armL/legR/legL (a direction), elbowR/elbowL (bend),
    # kneeR/kneeL (bend), waist/neck/wristR/wristL/ankleR/ankleL (x, y, z degrees)
    R = {}
    if pose.get('clip'):
        cn, ct = pose['clip']
        P = clip_pose(cn, ct)
        if pose.get('clip2'):
            cn2, ct2, w2 = pose['clip2']
            P2 = clip_pose(cn2, ct2)
            for part in set(P) | set(P2):
                a_, b_ = P.get(part), P2.get(part)
                if a_ is None or b_ is None:
                    P[part] = a_ if b_ is None else b_
                    continue
                q = a_.to_quaternion().slerp(b_.to_quaternion(), w2)
                m = q.to_matrix().to_4x4()
                m.translation = a_.translation.lerp(b_.translation, w2)
                P[part] = m
        for part, m in P.items():
            if part in PART_JOINT:
                R[PART_JOINT[part]] = m
    for side, s in (('R', 'Right'), ('L', 'Left')):
        if 'arm' + side in pose:
            R[s + 'Shoulder'] = aim_rot(pose['arm' + side], pose.get('armTwist' + side, 0))
        if 'elbow' + side in pose:
            R[s + 'Elbow'] = ANG(pose['elbow' + side], 0, 0)
        if 'wrist' + side in pose:
            R[s + 'Wrist'] = ANG(*pose['wrist' + side])
        if 'leg' + side in pose:
            R[s + 'Hip'] = aim_rot(pose['leg' + side], pose.get('legTwist' + side, 0))
        if 'knee' + side in pose:
            R[s + 'Knee'] = ANG(-pose['knee' + side], 0, 0)
        if 'ankle' + side in pose:
            an = pose['ankle' + side]
            R[s + 'Ankle'] = ANG(an[0] if isinstance(an, (tuple, list)) else an, 0, 0)
    if 'waist' in pose:
        R['Waist'] = ANG(*pose['waist'])
    if 'neck' in pose:
        R['Neck'] = ANG(*pose['neck'])
    cf = {'HumanoidRootPart': root_cf}
    for name, p0, p1, a0, a1 in JOINTS:
        cf[p1] = cf[p0] @ CF(*a0) @ R.get(name, Matrix.Identity(4)) @ CF(*a1).inverted()
    return cf


def lowest(cf):
    y = 1e9
    for n in ('RightFoot', 'LeftFoot', 'RightLowerLeg', 'LeftLowerLeg', 'RightHand', 'LeftHand', 'Head', 'UpperTorso', 'LowerTorso'):
        sx, sy, sz = SIZE[n]
        for cx in (-sx / 2, sx / 2):
            for cy in (-sy / 2, sy / 2):
                for cz in (-sz / 2, sz / 2):
                    y = min(y, (cf[n] @ Vector((cx, cy, cz, 1))).y)
    return y


def reach(root, pose, side, target_b):
    s = 'Right' if side == 'R' else 'Left'
    tgt = rb(target_b)
    best = None
    base = dict(pose)
    for i in range(500):
        # a Fibonacci sphere of arm directions
        y = 1 - 2 * (i + 0.5) / 500
        r = math.sqrt(max(0.0, 1 - y * y))
        a = math.pi * (3 - math.sqrt(5)) * i
        d = (math.cos(a) * r, y, math.sin(a) * r)
        if d[1] > 0.6:
            continue
        for el in range(0, 150, 6):
            base['arm' + side] = d
            base['elbow' + side] = el
            cf = solve(root, base)
            e = (cf[s + 'Hand'].translation - tgt).length
            if best is None or e < best[0]:
                best = (e, d, el)
    pose['arm' + side], pose['elbow' + side] = best[1], best[2]
    return best[0]


def rig(name, at, yaw, pose, body=(0, 0, 0), ground=True, floor_y=0.0, col=None, tr=0.0):
    # at: Blender (x, y, z = height of the HRP's base offset), yaw: degrees (0 = facing Blender +Y);
    # body: (pitch, yaw2, roll) of the whole body in degrees (pitch < 0 leans forward)
    p = rb((at[0], at[1], 0))
    root = CF(p.x, 3.0 + (at[2] if len(at) > 2 else 0.0), p.z) @ ANG(0, yaw, 0) @ ANG(*body)
    for side in ('R', 'L'):
        if pose.get('reach' + side) is not None:
            tb = pose['reach' + side]
            tb = tb(root) if callable(tb) else tb
            err = reach(root, pose, side, tb)
            print('   reach', name, side, round(err, 2), flush=True)
    cf = solve(root, pose)
    if pose.get('clip'):
        dy = max(0.0, floor_y - lowest(cf))
        if dy > 0:
            cf = {k: CF(0, dy, 0) @ v for k, v in cf.items()}
    elif ground and (len(at) < 3 or at[2] == 0):
        dy = floor_y - lowest(cf)
        cf = {k: CF(0, dy, 0) @ v for k, v in cf.items()}
    sc_ = pose.get('scatter', 0.0)
    if sc_ > 0:
        rs = random.Random(sum(map(ord, name)) + 11)
        for k in list(cf):
            if k == 'HumanoidRootPart':
                continue
            off = Vector((rs.uniform(-1, 1), rs.uniform(-0.2, 1), rs.uniform(-1, 1))).normalized() * sc_ * rs.uniform(0.4, 1.0)
            cf[k] = CF(*off) @ cf[k] @ ANG(rs.uniform(-40, 40) * sc_, rs.uniform(-40, 40) * sc_, rs.uniform(-40, 40) * sc_)
    RIGS.append({'name': name, 'cf': cf, 'col': col or (SHOOTER if name == 'k' else VICTIM), 'face': pose.get('face'),
                 'clip': pose.get('clip'), 'clip2': pose.get('clip2'), 'scatter': sc_, 'root0': root, 'tr': tr})
    return cf


KGRIP = os.environ.get('KGRIP', 'fist')


def hand_cf(cf, side='R'):
    # the katana's grip frame (blade along its -Z). 'fist': the handle through the closed hand, the blade out of the
    # thumb side, as the mocap's axe and sword grips hold it; 'fistb' the other way; 'arm': along the fingers
    h = cf[('Right' if side == 'R' else 'Left') + 'Hand']
    if KGRIP == 'arm':
        return h @ CF(0, 0, -0.045) @ ANG(-90, 0, 0)
    if KGRIP == 'fistb':
        return h @ CF(0, -0.12, 0) @ ANG(0, 180, 0)
    return h @ CF(0, -0.12, 0)


def wpt(cf_m, local):  # a point in a CFrame's space -> Blender world
    return br((cf_m @ Vector((local[0], local[1], local[2], 1))).xyz)


# ------------------------------------------------------------------ colours and props (Studio gets the same list)
SHOOTER = (0.22, 0.25, 0.33)
VICTIM = (0.72, 0.7, 0.67)   # (a shade under the floor: v1's white melted into it)
SKIN = (0.93, 0.60, 0.72)
INK = (0.05, 0.05, 0.07)
SAKURA = (0.95, 0.74, 0.82)
WOOD = (0.32, 0.23, 0.2)
LACQUER = (0.10, 0.07, 0.09)
STEEL = (0.86, 0.88, 0.92)
GOLD = (0.85, 0.68, 0.32)
FLOORC = (0.66, 0.66, 0.69)
PILLAR = (0.58, 0.59, 0.64)
RIGS = []
GUNS = []    # {'model': 'revolver_dust', 'cf': grip frame (Roblox), 'scale': 3}
PROPS = []   # {'shape': 'Block'|'Ball'|'Cylinder'|'Wedge', 'size': (x,y,z) Roblox, 'cf': 4x4 Roblox, 'col', 'mat', 'tag'}
KATANA = []  # Roblox CFrames of the katana grip (the place's katana_sakura, scaled x3)
SEM = {}     # this frame's semantics: 'sh' (scabbard: hip / lhand + m0), 'kat' (hand / home + push / through /
             # out + e), 'mouth' (the stand-in's scabbard mouth, Roblox CFrame looking down the scabbard), 'lens' anchor
KAT_MODE = []  # per KATANA entry: 'hand' (in the killer's right hand) or 'free' (placed: the sheath)


PROP_TR = [0.0]   # the transparency given to props made while it is set (a fading stroke in the video)


def prop(shape, size, cf, col, mat='SmoothPlastic', tag=''):
    PROPS.append({'shape': shape, 'size': tuple(size), 'cf': cf, 'col': col, 'mat': mat, 'tag': tag, 'tr': PROP_TR[0]})


def prop_box_between(a_b, b_b, w, h, col, up_b=(0, 0, 1), mat='SmoothPlastic', tag=''):
    # a box from Blender point a to b (Roblox frame: its length along Z)
    a, b = rb(a_b), rb(b_b)
    d = (b - a)
    L = d.length
    z = -d.normalized()
    upr = rb((up_b[0], up_b[1], up_b[2])) - rb((0, 0, 0))
    x = upr.cross(z)
    if x.length < 1e-4:
        x = Vector((1, 0, 0)).cross(z)
    x.normalize()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = (a + b) / 2
    prop('Block', (w, h, L), m, col, mat, tag)


def stage(kind='court'):
    prop('Block', (400, 1, 400), CF(0, -0.5, 0), FLOORC, 'SmoothPlastic', 'floor')
    rnd = random.Random(7)
    for i in range(14):
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(26, 70)
        h = rnd.uniform(10, 34)
        w = rnd.uniform(5, 12)
        prop('Block', (w, h, w), CF(math.cos(a) * r, h / 2, math.sin(a) * r), PILLAR, 'SmoothPlastic', 'pillar')


def tree(at_b, h=6.5):
    a = rb((at_b[0], at_b[1], 0))
    prop_box_between((at_b[0], at_b[1], 0), (at_b[0] + 0.4, at_b[1], h), 0.9, 0.9, WOOD, tag='tree')
    rnd = random.Random(int(at_b[0] * 10 + at_b[1]))
    for i in range(9):
        p = rb((at_b[0] + rnd.uniform(-2, 3), at_b[1] + rnd.uniform(-2, 2), h + rnd.uniform(-0.5, 1.6)))
        s = rnd.uniform(2.6, 4.0)
        prop('Ball', (s, s, s), CF(p.x, p.y, p.z), SAKURA if i % 3 else (0.9, 0.66, 0.76), 'SmoothPlastic', 'tree')


def petals(center_b, n, spread, seed=19, size=1.0):
    rnd = random.Random(seed)
    for i in range(n):
        p = rb(Vector(center_b) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))) * spread)
        m = CF(p.x, p.y, p.z) @ ANG(rnd.uniform(0, 360), rnd.uniform(0, 360), rnd.uniform(0, 360))
        prop('Block', (0.32 * size, 0.04, 0.22 * size), m, SAKURA, 'SmoothPlastic', 'petal')


def ink_arc(center_b, r, a0, a1, w0, w1, col, n=44, height=0.12, tag='smear'):
    # a flat band round center (Blender), angles in the Blender XY plane, radial width w0 -> w1
    c = Vector(center_b)
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        A = math.radians(a0 + (a1 - a0) * t0)
        B = math.radians(a0 + (a1 - a0) * t1)
        w = w0 + (w1 - w0) * (t0 + t1) / 2
        p0 = c + Vector((math.cos(A - 0.03), math.sin(A - 0.03), 0)) * r
        p1 = c + Vector((math.cos(B + 0.03), math.sin(B + 0.03), 0)) * r
        prop_box_between(p0, p1, w, height, col, up_b=(0, 0, 1), mat='Neon' if col == INK else 'SmoothPlastic', tag=tag)


def brush(a_b, b_b, bulge, width, facing_b, col, n=16, seed=29, tag='stroke'):
    a, b, f = Vector(a_b), Vector(b_b), Vector(facing_b).normalized()
    d = b - a
    side = d.cross(f).normalized()
    rnd = random.Random(seed)
    pts = [a + d * (i / n) + side * (bulge * math.sin(math.pi * i / n)) for i in range(n + 1)]
    for i in range(n):
        t = (i + 0.5) / n
        w = width * (math.sin(math.pi * min(1.0, t * 1.1)) ** 0.6) * rnd.uniform(0.75, 1.0) + 0.02
        prop_box_between(pts[i], pts[i + 1], 0.06, w, col, up_b=side, tag=tag, mat='Neon' if col == INK else 'SmoothPlastic')


def splats(center_b, n, spread, seed=23, size=1.0):
    rnd = random.Random(seed)
    for i in range(n):
        p = rb(Vector(center_b) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * spread)
        s = 0.18 * size * rnd.uniform(0.6, 1.6)
        prop('Ball', (s, s, s), CF(p.x, p.y, p.z), INK, 'SmoothPlastic', 'splat')


SHEATH_FLAT = [False]   # (the draw: the scabbard held level, its mouth forward, like the classic close-up of the draw)
SHEATH_LOCAL = [None]   # (mouth, tip) in the LowerTorso's space, read off the draw clip's own hands (see grip_sheath)


def sheath_line(cf):
    lt = cf['LowerTorso']
    if SHEATH_LOCAL[0] is not None:
        m_, t_ = SHEATH_LOCAL[0]
        mouth, tipp = lt @ m_, lt @ t_
        a, b = br(mouth.xyz), br(tipp.xyz)
        return a, b, (b - a).normalized()
    mouth = lt @ Vector((-0.95, 0.1, -0.75, 1))
    tipp = lt @ Vector((-1.25, -0.45 if SHEATH_FLAT[0] else -1.6, 2.2, 1))
    a, b = br(mouth.xyz), br(tipp.xyz)
    return a, b, (b - a).normalized()


def sheath(cf):
    # the scabbard at the left hip, mouth forward and up, running back and down (Roblox axes of the lower torso)
    a, b, _ = sheath_line(cf)
    d = (b - a).normalized()
    SEM.setdefault('sh', {'mode': 'hip'})
    ra, rd = rb(a), (rb(b) - rb(a)).normalized()
    SEM['mouth'] = comps(cf_look(ra, ra + rd))
    up = Vector((0, 0, 1)) - d * d.z
    up = up.normalized() * 0.1 if up.length > 1e-3 else Vector((0, 0, 0))
    a, b = a + up, b + up
    prop_box_between(a, b, 0.22, 0.4, LACQUER, tag='sheath')
    prop_box_between(a + d * 0.3, a + d * 0.5, 0.26, 0.44, SKIN, tag='sheath')
    prop_box_between(b - d * 0.25, b, 0.26, 0.44, GOLD, tag='sheath')
    return a - up, d


KAT_LEN = [1.0]   # the blade's length, x the normal (set per frame; 1 = the skin as it is)


def tipz():
    # the blade tip along the grip's -Z (studs, the x3 skin) for the current length
    return -(0.6 + 2.3 * KAT_LEN[0])


def katana_grip(m):
    KATANA.append(m)
    KAT_MODE.append('hand')
    SEM.setdefault('kat', {'mode': 'hand'})


# the bought Katana Combat Pack (20 Nov; vault Tools/Packs-20nov/katana-combat, never in git) animates the sword itself:
# its rig hangs the sword's handle off the right hand (Motor6D C0 = a -90 deg turn about X, C1 = identity) and every clip
# has a RightHandle track. The sword's blade runs along the handle's +Y; ours runs along our grip frame's -Z, so ours
# sits at handle * Rx(+90). The hand holds the handle at its origin.
PACK_C0 = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))


def pack_grip(K, clip_name, t):
    # our katana's grip frame (Roblox) from a pack clip's own sword track, or None when the clip has none
    pz = clip_pose(clip_name, t)
    T = pz.get('RightHandle')
    if T is None:
        return None
    return K['RightHand'] @ PACK_C0 @ T @ ANG(90, 0, 0)


def katana_pack(K, clip_name, t):
    m = pack_grip(K, clip_name, t)
    if m is None:
        return katana_grip(hand_cf(K))
    KATANA.append(m)
    KAT_MODE.append('hand')
    SEM['kat'] = {'mode': 'pack', 'T': comps(clip_pose(clip_name, t)['RightHandle'])}


def katana_at_b(guard_b, dir_b, up_b=(0, 0, 1)):
    # the katana placed by hand: its grip frame with the blade along dir (Blender), guard at the given point
    g = rb(guard_b)
    z = -(rb(Vector(guard_b) + Vector(dir_b)) - g).normalized()
    upr = rb(up_b) - rb((0, 0, 0))
    x = upr.cross(z)
    if x.length < 1e-4:
        x = Vector((1, 0, 0)).cross(z)
    x.normalize()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = g + z * 0.44  # the guard sits 0.148 m (x3) up the blade (local -Z) from the grip
    KATANA.append(m)
    KAT_MODE.append('free')
    SEM.setdefault('kat', {'mode': 'home', 'push': 0.0})


# ------------------------------------------------------------------ Blender preview
def setup():
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y = RW, RH
    sc.render.image_settings.file_format = 'PNG'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    try:
        sh.studio_light = 'basic.sl'
    except Exception:
        pass
    sh.color_type = 'OBJECT'
    sh.show_cavity = True
    sh.show_object_outline = True
    sh.object_outline_color = (0.05, 0.05, 0.07)
    sh.show_shadows = True
    sh.shadow_intensity = 0.3
    if sc.world is None:
        sc.world = bpy.data.worlds.new('w')
    sc.world.color = (0.62, 0.74, 0.88)


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.cameras):
        bpy.data.cameras.remove(c)


def bl_box(name, size, m_roblox, col, shape='Block', bevel=0.0):
    bm = bmesh.new()
    if shape == 'Ball':
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.5)
    elif shape == 'Cylinder':
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.5, radius2=0.5, depth=1.0)
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    else:
        bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.matrix_world = MB @ m_roblox
    ob.color = (*col, 1)
    sc.collection.objects.link(ob)
    if bevel:
        mo = ob.modifiers.new('b', 'BEVEL')
        mo.width = bevel
        mo.segments = 2
        mo.limit_method = 'NONE'
    return ob


def draw_preview():
    for r in RIGS:
        for n, m in r['cf'].items():
            if n == 'HumanoidRootPart':
                continue
            s = SIZE[n]
            bl_box(f"{r['name']}_{n}", s, m, r['col'], bevel=min(s) * 0.2)
        f = r.get('face') or {}
        if 'Head' in r['cf']:
            hd, hs = r['cf']['Head'], SIZE['Head']
            shut = f.get('LeftEyeClosed', 0.0)
            wide = f.get('LeftUpperLidRaiser', 0.0)
            eh = 0.2 * (1 - 0.75 * shut) + 0.08 * wide
            for x in (-0.2, 0.2):
                bl_box(f"{r['name']}_eye", (0.13, eh, 0.02), hd @ CF(x, 0.1, -hs[2] / 2 - 0.006), (0.05, 0.05, 0.06))
                if f.get('LeftBrowLowerer', 0.0) > 0.3:
                    bl_box(f"{r['name']}_brow", (0.24, 0.05, 0.02), hd @ CF(x * 1.05, 0.1 + eh / 2 + 0.06, -hs[2] / 2 - 0.006) @
                           ANG(0, 0, 14 if x < 0 else -14), (0.05, 0.05, 0.06))
    for p in PROPS:
        if p.get('tr', 0) >= 0.5:
            continue
        bl_box('prop_' + p['tag'], p['size'], p['cf'], p['col'], p['shape'])
    for g in GUNS:
        m = g['cf']
        bl_box('gun_body', (0.28, 0.42, 1.0), m @ CF(0, 0.1, -0.1), (0.12, 0.12, 0.14))
        bl_box('gun_barrel', (0.2, 0.2, 0.9), m @ CF(0, 0.2, -0.9), (0.12, 0.12, 0.14))
        bl_box('gun_grip', (0.24, 0.6, 0.3), m @ CF(0, -0.35, 0.3), (0.45, 0.3, 0.18))
    for m in KATANA:
        L_ = KAT_LEN[0]
        bl_box('kat_blade', (0.05, 0.27, 2.1 * L_), m @ CF(0, 0.1, -(0.4 + 1.05 * L_)), STEEL)
        bl_box('kat_guard', (0.33, 0.33, 0.1), m @ CF(0, 0, -0.44), GOLD)
        bl_box('kat_grip', (0.13, 0.15, 0.75), m @ CF(0, 0, 0), LACQUER)


CAMS = {}


def lens(pos_b, look_b, fov, roll=0.0):
    # the lens in Blender axes -> its Roblox CFrame (looking down -Z, up +Y in its own frame: the same in both)
    pos, look = Vector(pos_b), Vector(look_b)
    d = (look - pos).normalized()
    q = d.to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), math.radians(roll))
    mb = Matrix.Translation(pos) @ q.to_matrix().to_4x4()
    cd = bpy.data.cameras.new('cam')
    cd.sensor_fit = 'VERTICAL'
    cd.angle = math.radians(fov)
    cd.clip_start = 0.05
    cd.clip_end = 3000
    co = bpy.data.objects.new('cam', cd)
    sc.collection.objects.link(co)
    co.matrix_world = mb
    sc.camera = co
    CAMS['cf'] = MB_INV @ mb
    CAMS['fov'] = fov
    return co


def aim_lens(points_b, az, el, fov, roll=0.0, mx=0.84, my=0.66, off=(0, 0, 0), zmin=0.3):
    pts = [Vector(p) for p in points_b]
    c = sum(pts, Vector()) / len(pts) + Vector(off)
    a, e = math.radians(az), math.radians(el)
    dv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    d = 1.2
    while d < 200:
        pos = c + dv * d
        pos.z = max(pos.z, zmin)
        co = lens(pos, c, fov, roll)
        bpy.context.view_layer.update()
        ok = all(abs(v.x - 0.5) <= mx / 2 and abs(v.y - 0.5) <= my / 2 and v.z > 0.2 for v in (world_to_camera_view(sc, co, p) for p in pts))
        if ok:
            return pos, c
        bpy.data.objects.remove(co, do_unlink=True)
        d += 0.25
    return pos, c


def pts_of(cf, names=('Head', 'LeftFoot', 'RightFoot', 'RightHand', 'LeftHand')):
    return [br(cf[n].translation) for n in names]


BOARDS = {}


def frame(board, n):
    def deco(fn):
        BOARDS.setdefault(board, {})[n] = fn
        return fn
    return deco


# ------------------------------------------------------------------ the revolver (the place's revolver_dust, x3)
def rig_name(cf):
    return next((r['name'] for r in RIGS if r['cf'] is cf), None)


def revolver_in_hand(cf, tr=0.0):
    # the barrel runs on from the forearm, the gun's top toward the back of the hand; the grip sits in the palm
    g = cf['RightHand'] @ CF(0, -0.1, 0) @ ANG(-90, 0, 0) @ CF(0, 0.55, -0.25)
    if rig_name(cf) and not tr:
        SEM.setdefault('gun', {})[rig_name(cf)] = 'hand'
    GUNS.append({'model': 'revolver_dust', 'cf': g, 'tr': tr})
    return g


def holster(cf, gun_in=True):
    lt = cf['LowerTorso']
    h = lt @ CF(1.12, -0.45, -0.05)
    prop('Block', (0.32, 0.95, 0.55), h, (0.42, 0.27, 0.16), 'Leather', 'holster')
    prop('Block', (2.12, 0.28, 1.1), lt @ CF(0, 0.05, 0), (0.42, 0.27, 0.16), 'Leather', 'belt')
    if rig_name(cf):
        SEM.setdefault('hol', {})[rig_name(cf)] = 'in' if gun_in else 'empty'
    if gun_in:
        GUNS.append({'model': 'revolver_dust', 'cf': h @ CF(0, 0.15, 0) @ ANG(-90, 0, 0) @ CF(0, 0, -0.1)})
    return h


SAND = (0.86, 0.75, 0.57)
ROCK = (0.72, 0.49, 0.35)
CACTUS = (0.42, 0.52, 0.38)


DIRT = (0.74, 0.6, 0.42)


def desert():
    prop('Block', (500, 1, 500), CF(0, -0.5, 0), DIRT, 'Sand', 'ground')
    for x in (-1.7, 1.7):   # wheel ruts down the street
        prop_box_between((x, -30, 0.015), (x, 45, 0.015), 0.55, 0.03, (0.6, 0.48, 0.33), mat='Sand', tag='rut')
    rnd = random.Random(33)
    for j in range(14):     # footprints between them
        y = 1.0 + j * 1.15
        x = (0.35 if j % 2 else -0.35) + rnd.uniform(-0.1, 0.1)
        q = rb((x, y, 0.012))
        prop('Block', (0.32, 0.025, 0.55), CF(q.x, q.y, q.z) @ ANG(0, rnd.uniform(-12, 12), 0), (0.63, 0.5, 0.35), 'Sand', 'print')
    cyclorama(c=(0.0, 8.5), bands=((1.0, 0.76, 0.48), (0.97, 0.64, 0.43), (0.9, 0.54, 0.44), (0.74, 0.48, 0.5),
                                   (0.56, 0.43, 0.56), (0.42, 0.39, 0.55)), lid=(0.4, 0.38, 0.54))
    for at, size in (((-36, 30), (16, 14, 28)), ((-32, -8), (12, 10, 18)), ((40, 44), (18, 16, 22)), ((-60, 70), (30, 22, 40)), ((70, 10), (20, 18, 30))):
        q = rb((at[0], at[1], 0))
        prop('Block', (size[0], size[1], size[2]), CF(q.x, size[1] / 2, q.z), ROCK, 'Sandstone', 'mesa')
    for at, h in (((-9, 4), 4.4), ((8, 22), 3.6), ((10, -4), 3.0), ((-11, 26), 3.8)):
        q = rb((at[0], at[1], 0))
        prop('Cylinder', (h, 0.8, 0.8), CF(q.x, h / 2, q.z) @ ANG(0, 0, 90), CACTUS, 'SmoothPlastic', 'cactus')
        prop('Cylinder', (1.0, 0.56, 0.56), CF(q.x + 0.6, h * 0.45, q.z), CACTUS, 'SmoothPlastic', 'cactus')
        prop('Cylinder', (h * 0.35, 0.56, 0.56), CF(q.x + 1.1, h * 0.62, q.z) @ ANG(0, 0, 90), CACTUS, 'SmoothPlastic', 'cactus')
    for y in (-6, -2, 2):
        q = rb((-6.5, y, 0))
        prop('Block', (0.35, 2.2, 0.35), CF(q.x, 1.1, q.z), WOOD, 'Wood', 'fence')
    prop_box_between((-6.5, -6.2, 1.7), (-6.5, 2.2, 1.7), 0.2, 0.25, WOOD, tag='fence')


def tumbleweed(at_b, r=1.6, seed=5, rot=0.0, axis=(1, 0, 0)):
    # rot: how far it has rolled (radians about axis, Blender) - the same twigs, turned
    rnd = random.Random(seed)
    c = Vector(at_b)
    R = Matrix.Rotation(rot, 3, Vector(axis))
    for i in range(44):
        a = R @ (Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized() * r * rnd.uniform(0.6, 1.0))
        b = R @ (Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized() * r * rnd.uniform(0.6, 1.0))
        prop_box_between(c + a, c + b, 0.07, 0.07, (0.60, 0.46, 0.30) if i % 3 else (0.50, 0.38, 0.24), tag='tumbleweed')


def flash(at_b, size, facing_b, col=(1.0, 0.93, 0.62), rays=7, seed=3, tag='flash'):
    rnd = random.Random(seed)
    f = Vector(facing_b).normalized()
    u = f.cross(Vector((0, 0, 1)))
    if u.length < 1e-3:
        u = f.cross(Vector((1, 0, 0)))
    u.normalize()
    v = f.cross(u)
    c = Vector(at_b)
    for i in range(rays):
        a = 2 * math.pi * i / rays + rnd.random() * 0.4
        d = u * math.cos(a) + v * math.sin(a)
        prop_box_between(c, c + d * size * rnd.uniform(0.7, 1.3), size * 0.14, size * 0.05, col, mat='Neon', tag=tag)
    q = rb(c)
    prop('Ball', (size * 0.5,) * 3, CF(q.x, q.y, q.z), col, 'Neon', tag)


def puff(at_b, r, col=(0.78, 0.76, 0.74), tag='smoke'):
    q = rb(at_b)
    prop('Ball', (r, r, r), CF(q.x, q.y, q.z), col, 'SmoothPlastic', tag)


# ================================================================== DUST on R15
# Blender layout: the killer at the origin facing +Y, the victim 17 studs off facing back
DV = Vector((0, 17, 0))
SLINGR = {'armR': (0.28, -0.96, 0.02), 'elbowR': 18, 'wristR': (10, 0, 0), 'armL': (-0.22, -0.97, 0), 'elbowL': 12,
          'legR': (0.2, -0.98, 0), 'legL': (-0.2, -0.98, 0), 'kneeR': 8, 'kneeL': 8}
SQUINT = {'LeftEyeClosed': 0.55, 'RightEyeClosed': 0.55, 'LeftBrowLowerer': 0.8, 'RightBrowLowerer': 0.8, 'LeftLidTightener': 0.7, 'RightLidTightener': 0.7}
WIDE = {'LeftUpperLidRaiser': 1.0, 'RightUpperLidRaiser': 1.0, 'LeftInnerBrowRaiser': 0.9, 'RightInnerBrowRaiser': 0.9, 'JawDrop': 0.15}


def dust_rigs(kpose=None, vpose=None, kgun_in=True):
    K = rig('k', (0, 0, 0), 0, kpose or dict(SLINGR, face=SQUINT))
    holster(K, kgun_in)
    V = rig('v', (DV.x, DV.y, 0), 180, vpose or dict(SLINGR, face=WIDE))
    holster(V, True)
    return K, V


@frame('dust', 1)
def dust_1():
    desert()
    K, V = dust_rigs()
    hd = K['Head']
    eye = hd @ Vector((0, 0.1, -0.55, 1))
    fwd = hd @ Vector((0, 0.1, -2.4, 1))
    lens(br(fwd.xyz), br(eye.xyz), 16, 0)
    return {'name': "KILLER'S EYES", 'crop': 0.3}


@frame('dust', 2)
def dust_2():
    desert()
    K, V = dust_rigs()
    hd = V['Head']
    q = (hd @ Vector((0.38, 0.32, -0.6, 1))).xyz
    prop('Ball', (0.12, 0.17, 0.12), CF(q.x, q.y, q.z), (0.85, 0.92, 1.0), 'Glass', 'sweat')
    eye = hd @ Vector((0, 0.1, -0.55, 1))
    fwd = hd @ Vector((0, 0.1, -2.4, 1))
    lens(br(fwd.xyz), br(eye.xyz), 16, 4)
    return {'name': "VICTIM'S EYES", 'crop': 0.3}


@frame('dust', 3)
def dust_3():
    desert()
    K, V = dust_rigs(dict(SLINGR, armR=(0.3, -0.95, 0.06), wristR=(18, 0, 6), face=SQUINT))
    h = br(K['RightHand'].translation)
    lens(h + Vector((1.5, -2.8, -0.5)), h + Vector((-0.4, 1.6, 0.3)), 40, -6)
    return {'name': 'THE HAND'}


@frame('dust', 4)
def dust_4():
    desert()
    dust_rigs()
    tumbleweed((2.0, 8.5, 1.6), 1.6)
    lens((25, -1.5, 1.1), (0, 8.5, 2.4), 26, 0)
    return {'name': 'THE WIDE'}


@frame('dust', 5)
def dust_5():
    desert()
    K, V = dust_rigs(dict(SLINGR, armR=(0.05, -0.32, -0.95), elbowR=12, wristR=(0, 0, 0), armL=(0.5, -0.45, -0.74), elbowL=75,
                          legR=(0.3, -0.95, 0), legL=(-0.3, -0.95, 0), kneeR=25, kneeL=25, waist=(-6, 10, 0), face=SQUINT), kgun_in=False)
    g = revolver_in_hand(K)
    m = br((g @ Vector((0, 0.2, -1.5, 1))).xyz)
    flash(m + (m - br(g.translation)).normalized() * 0.4, 1.1, (1, -0.3, 0.2))
    puff(m + Vector((0.3, 0.6, 0.2)), 0.5, (0.86, 0.78, 0.62))
    pts = pts_of(K) + [m + Vector((0, 1.2, 0)), br(V['Head'].translation), br(V['LeftFoot'].translation)]
    aim_lens(pts, 28, -6, 54, 14, mx=0.84, my=0.66, zmin=0.6)
    return {'name': 'THE DRAW'}


@frame('dust', 6)
def dust_6():
    desert()
    K, V = dust_rigs(vpose=dict(SLINGR, neck=(12, 0, 0), waist=(10, 0, 0), face=WIDE))
    hit = br(V['UpperTorso'].translation) + Vector((0, -0.55, 0.1))
    prop_box_between(hit + Vector((0, -0.7, 0)), hit, 0.16, 0.16, (1.0, 0.95, 0.85), mat='Neon', tag='bullet')
    prop_box_between(hit + Vector((0, -12, -0.4)), hit + Vector((0, -0.7, 0)), 0.05, 0.05, (1.0, 0.95, 0.85), mat='Neon', tag='btrail')
    flash(hit + Vector((0, -0.2, 0)), 1.1, (-1, -1, 0.1), col=(1.0, 0.95, 0.85), rays=8, tag='shock')
    lens(br(V['UpperTorso'].translation) + Vector((-3.8, -5.0, 0.4)), br(V['UpperTorso'].translation) + Vector((0, 0, 0.6)), 40, -8)
    return {'name': 'HIT FRAME', 'impact': {'bg': [0.04, 0.03, 0.03], 'fg': [1.0, 0.72, 0.32], 'accent': ['bullet', 'btrail', 'shock'], 'accent_col': [1.0, 0.95, 0.85]}}


@frame('dust', 7)
def dust_7():
    desert()
    K, V = dust_rigs(vpose={'neck': (-32, 0, 0), 'waist': (-12, 0, 0), 'armR': (0.4, -0.9, -0.15), 'elbowR': 35, 'armL': (-0.4, -0.9, -0.15),
                            'elbowL': 35, 'legR': (0.18, -0.98, -0.1), 'kneeR': 22, 'legL': (-0.18, -0.98, -0.1), 'kneeL': 22, 'face': WIDE})
    c = br(V['UpperTorso'].translation)
    rnd = random.Random(600)
    for i in range(16):
        a = 2 * math.pi * i / 16
        r = 0.9 + 0.5 * (i % 3)
        q = rb(c + Vector((math.cos(a) * 2.0, 1.4 + abs(math.sin(a)) * 0.8, math.sin(a) * 1.6)))
        prop('Ball', (r, r, r), CF(q.x, q.y, q.z), SAND if i % 2 else (1.0, 0.86, 0.55), 'Sand', 'dustburst')
    pts = pts_of(V) + [c + Vector((2.2, 1.6, 1.8)), c + Vector((-2.2, 1.6, -1.6))]
    aim_lens(pts, 25, -8, 44, -6)
    return {'name': 'THE HIT'}


@frame('dust', 8)
def dust_8():
    desert()
    K, V = dust_rigs(dict(SLINGR, neck=(-14, 0, 0), armR=(0.35, -0.93, -0.1), elbowR=30, wristR=(-40, 0, 0), face=SQUINT), kgun_in=False)
    g = revolver_in_hand(K)
    h = br(K['RightHand'].translation)
    ink_arc(h + Vector((0.1, 0.0, -0.1)), 0.85, 30, 290, 0.08, 0.02, (1.0, 0.88, 0.6), n=20, tag='spin')
    m = br((g @ Vector((0, 0.2, -1.5, 1))).xyz)
    for i, (dz, r) in enumerate(((0.3, 0.2), (0.75, 0.28), (1.25, 0.34))):
        puff(m + Vector((0.05 * i, 0.05, dz)), r)
    pts = [br(K['Head'].translation), h + Vector((0, 0, -1.2)), m + Vector((0, 0, 1.4)), br(K['LeftHand'].translation)]
    aim_lens(pts, 145, 2, 36, 5, mx=0.8, my=0.66)
    return {'name': 'HOLSTER'}


# ================================================================== TIDECREST on R15
# Blender layout: the victim at the origin facing -Y (toward the run-up); the killer runs along +Y past them on the
# victim's right (x = +2.3) and ends behind them, back to back (+Y)
def cyclorama(r=120.0, n=32, bands=((1.0, 0.8, 0.52), (0.97, 0.69, 0.53), (0.86, 0.6, 0.6), (0.72, 0.55, 0.64),
                                     (0.58, 0.5, 0.66), (0.46, 0.44, 0.62)), h=40.0, c=(0.0, 0.0), lid=(0.42, 0.41, 0.6)):
    # a ring of painted sky round the set (Neon: lit the same from every side), warm at the horizon, dusk above; so the
    # sunset of the opening holds through every shot whichever way the lens looks (v1 swung to a blue sky at the clash)
    w = 2 * math.pi * r / n * 1.04
    for i in range(n):
        a = 2 * math.pi * i / n
        x, z = c[0] + math.cos(a) * r, -c[1] + math.sin(a) * r
        yaw = math.degrees(math.atan2(x - c[0], z + c[1]))
        for j, col in enumerate(bands):
            prop('Block', (w, h, 1.0), CF(x, h / 2 + j * h, z) @ ANG(0, yaw, 0), col, 'Neon', 'sky')
    # the lid (a low lens looking up sees dusk, not the map's sky); none of it casts a shadow (Studio and the game skip
    # shadows on 'sky')
    prop('Block', (2.2 * r, 1.0, 2.2 * r), CF(c[0], h * len(bands) + 0.5, -c[1]), lid, 'Neon', 'sky')


def disc(center_b, toward_b, radius, col, tag='sky'):
    # a flat round (Roblox Cylinder, axis = its X) facing a point
    a, b = rb(center_b), rb(toward_b)
    x = (b - a).normalized()
    z = x.cross(Vector((0, 1, 0))).normalized()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = a
    prop('Cylinder', (0.6, radius * 2, radius * 2), m, col, 'Neon', tag)


END_CAM = (-6.0, -8.5, 1.3)   # (Blender) the last shot's lens: low, in front of both, the winner three-quarter on


def sun_b():
    # the sun sits on the ring's far side on the line from the last shot's lens through the winner's chest
    c = Vector(END_CAM)
    k = Vector((K_BACK[0], K_BACK[1], 2.7))
    d = (k - c).normalized()
    t = 0.0
    while (c + d * t).xy.length < 116:
        t += 0.5
    return tuple(c + d * t)


def tide_stage(s=None):
    # s: the video's clock (seconds); the loose petals drift with it
    stage()
    cyclorama()
    disc(sun_b(), END_CAM, 15, (1.0, 0.94, 0.8))
    tree((-8, 11))
    tree((-15, -26), 5.8)
    if s is None:
        petals((-5, 9, 3), 10, 4, seed=401)
    else:
        petals_drift((-5, 9, 3), 10, 4, s, seed=401)


SPRINT = {'armR': (0.15, -0.55, 0.82), 'elbowR': 25, 'wristR': (-25, 0, 0), 'armL': (-0.1, -0.25, -0.95), 'elbowL': 95,
          'legR': (0, -0.25, -0.97), 'kneeR': 105, 'ankleR': (15,), 'legL': (0, -0.85, 0.52), 'kneeL': 55, 'ankleL': (-25,),
          'waist': (-12, 8, 0), 'neck': (22, 0, 0)}


@frame('tide', 1)
def tide_1():
    tide_stage()
    K = rig('k', (2.3, -11, 0), 0, SPRINT, body=(-28, 0, 0))
    katana_grip(hand_cf(K))
    rig('v', (0, 0, 0), 180, {'armR': (0.2, -1, 0), 'armL': (-0.2, -1, 0), 'elbowR': 10, 'elbowL': 10})
    pts = pts_of(K) + [wpt(hand_cf(K), (0, 0, -3.0))]
    pos, look = aim_lens(pts, 72, 3, 44, 0, mx=0.62, my=0.6, zmin=1.0)
    return {'name': 'RUN-UP', 'note': 'side-on tracking at blade height'}


@frame('tide', 2)
def tide_2():
    tide_stage()
    K = rig('k', (2.3, -4.8, 0), 0, {'waist': (-10, -50, 0), 'neck': (18, 30, 0), 'armR': (0.85, -0.35, 0.4), 'elbowR': 15,
                                    'wristR': (-10, 0, 0), 'armL': (-0.2, -0.3, -0.93), 'elbowL': 80,
                                    'legR': (0, -0.6, 0.8), 'kneeR': 55, 'legL': (0, -0.45, -0.89), 'kneeL': 85, 'ankleL': 10},
            body=(-24, 0, 0))
    katana_grip(hand_cf(K))
    pts = pts_of(K) + [wpt(hand_cf(K), (0, 0, -3.0))]
    aim_lens(pts, 168, -22, 84, -16, mx=0.8, my=0.62, zmin=0.45)
    return {'name': 'CLOSING', 'note': 'on the floor in their path, the FOV punch'}


@frame('tide', 4)
def tide_4():
    info = tide_3()
    info['name'] = 'CUT FRAME'
    info['impact'] = {'bg': [0.97, 0.96, 0.94], 'fg': [0.05, 0.05, 0.07], 'accent': ['smear', 'smear_edge'], 'accent_col': [0.93, 0.6, 0.72]}
    return info


@frame('tide', 3)
def tide_3():
    tide_stage()
    K = rig('k', (3.3, -0.3, 0), 0, {'armR': (-0.95, -0.15, -0.3), 'elbowR': 15, 'wristR': (-10, 0, 0), 'armL': (0.3, -0.5, 0.8),
                                       'elbowL': 40, 'legR': (0, -0.5, -0.86), 'kneeR': 80, 'legL': (0, -0.8, 0.6), 'kneeL': 30,
                                       'waist': (-14, 55, 0), 'neck': (10, -35, 0)}, body=(-22, 0, 0))
    katana_grip(hand_cf(K))
    V = rig('v', (0, 0, 0), 180, {'armR': (0.3, -0.25, -0.92), 'elbowR': 105, 'armL': (-0.3, -0.25, -0.92), 'elbowL': 105,
                                'waist': (8, 0, 0), 'neck': (12, 0, 0), 'legR': (0.1, -1, 0.1), 'kneeR': 15, 'legL': (-0.1, -1, -0.15), 'kneeL': 20})
    c = br(K['UpperTorso'].translation) + Vector((0, 0, -0.9))
    ink_arc(c, 2.9, 262, 150, 0.6, 2.2, INK)
    ink_arc(c + Vector((0, 0, 0.05)), 4.1, 262, 150, 0.15, 0.4, SKIN, tag='smear_edge')
    pts = pts_of(K) + pts_of(V) + [c + Vector((-3.5, 0, 0))]
    aim_lens(pts, 4, 18, 56, 10, mx=0.84, my=0.64)
    return {'name': 'THE PASS', 'note': 'low and tilted at the victim, the whip with the blade'}


@frame('tide', 5)
def tide_5():
    tide_stage()
    K = rig('k', (2.3, 6.4, 0), 0, {'armR': (0.55, -0.82, -0.1), 'elbowR': 12, 'armL': (-0.15, -1, 0), 'elbowL': 15,
                                       'legR': (0.08, -1, 0), 'legL': (-0.08, -1, 0)})
    katana_grip(hand_cf(K))
    V = rig('v', (0, 0, 0), 180, {'neck': (6, 48, 0), 'waist': (4, -14, 0), 'armR': (0.36, -0.93, 0.05), 'elbowR': 25,
                                'armL': (-0.34, -0.94, 0.0), 'elbowL': 30, 'legR': (0.15, -1, 0.05), 'kneeR': 12,
                                'legL': (-0.12, -1, -0.1), 'kneeL': 4})
    petals(br(V['Head'].translation) + Vector((0.5, -1.6, 0.3)), 9, 1.6, seed=411)
    hp = br(V['Head'].translation)
    lens(hp + Vector((2.6, -6.6, -0.3)), hp + Vector((-0.3, 0.8, -0.8)), 40, 0)
    return {'name': 'STILLNESS', 'note': 'the victim close, the killer soft behind'}


@frame('tide', 6)
def tide_6():
    tide_stage()
    kp = {'neck': (-24, 0, 0), 'waist': (-10, 12, 0), 'legR': (0.1, -1, 0), 'legL': (-0.1, -1, 0)}

    def grip_at(root):
        a, b, d = sheath_line(solve(root, kp))
        return a - d * 1.04

    def mouth_at(root):
        a, b, d = sheath_line(solve(root, kp))
        return a + d * 0.15

    kp['reachR'], kp['reachL'] = grip_at, mouth_at
    K = rig('k', (2.3, 6.4, 0), 0, kp)
    mouth, d = sheath(K)
    katana_at_b(mouth - d * 0.6, d)
    rig('v', (0, 0, 0), 180, {'neck': (0, -30, 0), 'armR': (0.3, -0.95, 0), 'armL': (-0.3, -0.95, 0)})
    hp = br(K['Head'].translation)
    pts = [hp + Vector((0, 0, 0.6)), mouth - d * 1.2, mouth + d * 2.0, br(K['RightHand'].translation), br(K['LeftHand'].translation)]
    aim_lens(pts, 212, 8, 40, 6, mx=0.8, my=0.66)
    return {'name': 'THE SHEATHE', 'note': "the killer's hands sliding the blade home"}


@frame('tide', 7)
def tide_7():
    tide_stage()
    K = rig('k', (2.3, 6.4, 0), 0, {'armR': (0.25, -0.97, 0), 'elbowR': 15, 'armL': (-0.25, -0.97, 0), 'elbowL': 15,
                                    'legR': (0.06, -1, 0.1), 'legL': (-0.06, -1, -0.12), 'kneeL': 8})
    mouth, d = sheath(K)
    katana_at_b(mouth, d)
    V = rig('v', (0, 0, 0), 180, {'neck': (-26, 0, 0), 'armR': (0.45, -0.89, 0), 'elbowR': 15, 'armL': (-0.45, -0.89, 0),
                                  'elbowL': 15, 'legR': (0.05, -1, 0), 'kneeR': 10, 'legL': (-0.05, -1, 0), 'kneeL': 10})
    c = br(V['UpperTorso'].translation) + Vector((0, 0, -0.6))
    brush(c + Vector((-0.75, -2.0, 1.5)), c + Vector((-0.75, 2.4, -1.1)), 0.35, 0.55, (-1, 0, 0), INK, seed=61)
    brush(c + Vector((-0.82, -1.6, 1.25)), c + Vector((-0.82, 2.0, -0.95)), 0.33, 0.16, (-1, 0, 0), SKIN, seed=62, tag='stroke_edge')
    splats(c + Vector((-0.8, 0.6, 0.0)), 14, 1.4, seed=71)
    lens((-9.6, 3.2, 2.8), (0.8, 3.2, 2.8), 44, 0)
    return {'name': 'THE CUT LANDS', 'note': 'back to back, the stroke appears'}


@frame('tide', 8)
def tide_8():
    tide_stage()
    K = rig('k', (2.3, 7.8, 0), 0, {'armR': (0.15, -0.95, 0.25), 'elbowR': 15, 'armL': (-0.15, -0.95, -0.25), 'elbowL': 20,
                                    'legR': (0, -0.95, -0.3), 'kneeR': 15, 'legL': (0, -0.93, 0.35), 'kneeL': 25})
    sheath(K)
    V = rig('v', (0, 0, 0.4), 180, {'neck': (-26, 0, 0), 'armR': (0.45, -0.89, 0), 'armL': (-0.45, -0.89, 0), 'scatter': 1.2})
    vc = br(V['UpperTorso'].translation)
    petals(vc + Vector((0, 0, 0.4)), 70, 2.8, seed=421, size=1.3)
    splats(vc, 26, 2.2, seed=81, size=1.4)
    lens((-7.5, -7.5, 8.5), (0.5, 1.6, 2.0), 54, 0)
    return {'name': 'PETALS', 'note': 'crane up and out'}


# ================================================================== the mocap versions (19 Nov, the owner's rule)
# every body below plays a real clip at a picked moment (contact sheets: r15sheets/contact_*.jpg); nothing is posed
# by hand. They replace the keyed frames of the same numbers above.
def hips_b(cn, t, yaw):
    # where a clip's hips are at time t (Blender, relative to the rig's base), from its own root motion
    m = clip_pose(cn, t).get('LowerTorso')
    off = m.translation if m else Vector((0, 0, 0))
    w = (ANG(0, yaw, 0) @ Vector((off.x, 0, off.z, 1))).xyz
    return br(w)


def at_for(cn, t, want_b, yaw):
    # the rig's base so that the clip's hips pass over want_b at time t
    o = hips_b(cn, t, yaw)
    return (want_b[0] - o.x, want_b[1] - o.y, 0)


SLASH, LOOK, SHEATHE, DRAW = 'inkfall_slash_t1', 'victim_lookaround_t2', 'sheathe_t2', 'quick_draw_t1'
T_HIT = 2.55
# the owner (20 Nov): "the slash misses the target and you somehow appear behind him". The take's slash swings out to
# the killer's RIGHT, the blade's middle about 4 studs from their hips, and the take ends with them stopped level with
# where they cut. So they run in on the victim's other side (x = -4): the blade's middle crosses the victim's waist at
# the hit; and afterwards they stay where the take leaves them - side by side, facing opposite ways (the one-stroke
# duel's ending), never moved behind the victim between shots
K_START = at_for(SLASH, T_HIT, (-3.2, 0.0), 0)
_kb = hips_b(SLASH, 3.33, 0)
K_BACK = (K_START[0] + _kb.x, K_START[1] + _kb.y)   # where the slash take ends (its hips at its last frame)


SMEAR = (1.0, 0.95, 0.97)   # the blade's light trail (v1's ink-black fan read as a dark blob: the cut must flash)


def blade_sweep(cn, at, yaw, t0, t1, n=14, col=SMEAR, width=None, tag='smear'):
    # an ink-brush smear along the blade's real path between t0 and t1 (the katana in the right hand of the clip; a pack
    # clip's own sword track when it has one; `at` may be a function of the clip time for a root that travels)
    pts = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        at_ = at(t) if callable(at) else at
        p = rb((at_[0], at_[1], 0))
        root = CF(p.x, 3.0, p.z) @ ANG(0, yaw, 0)
        cf = solve(root, {'clip': (cn, t)})
        g = pack_grip(cf, cn, t) or hand_cf(cf)
        pts.append((wpt(g, (0, 0, -0.6)), wpt(g, (0, 0, tipz()))))
    for i in range(n):
        (a0, b0), (a1, b1) = pts[i], pts[i + 1]
        mid0, mid1 = (a0 + b0) / 2, (a1 + b1) / 2
        L = (b0 - a0).length * (0.4 + 0.6 * i / n)
        prop_box_between(mid0, mid1 + (mid1 - mid0) * 0.15, 0.08, L, col, up_b=(b0 - a0).normalized(), tag=tag,
                         mat='Neon')


@frame('tide', 0)
def m_tide_0():
    # establish: a locked wide side-on two-shot, killer left, victim right, before any close-up
    tide_stage()
    K = rig('k', K_START, 0, {'clip': (SLASH, 0.0)})
    katana_grip(hand_cf(K))
    V = rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.0)})
    kh, vh = br(K['LowerTorso'].translation), br(V['LowerTorso'].translation)
    mid = (kh + vh) / 2
    lens(mid + Vector((30, 0, 1.4)), mid + Vector((0, 0, 0.6)), 34, 0)
    return {'name': 'ESTABLISH'}


@frame('tide', 1)
def m_tide_1():
    tide_stage()
    K = rig('k', K_START, 0, {'clip': (SLASH, 0.67)})
    katana_grip(hand_cf(K))
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.0)})
    pts = pts_of(K) + [wpt(hand_cf(K), (0, 0, -2.9))]
    aim_lens(pts, 72, 3, 44, 0, mx=0.62, my=0.6, zmin=1.0)
    return {'name': 'RUN-UP'}


@frame('tide', 2)
def m_tide_2():
    tide_stage()
    K = rig('k', K_START, 0, {'clip': (SLASH, 1.95)})
    katana_grip(hand_cf(K))
    pts = pts_of(K) + [wpt(hand_cf(K), (0, 0, -2.9))]
    aim_lens(pts, 168, -22, 84, -16, mx=0.8, my=0.62, zmin=0.45)
    return {'name': 'CLOSING'}


def m_pass(impact=False):
    tide_stage()
    K = rig('k', K_START, 0, {'clip': (SLASH, T_HIT)})
    katana_grip(hand_cf(K))
    V = rig('v', (0, 0, 0), 180, {'clip': ('bx_18_block_high_center', 0.35)})
    blade_sweep(SLASH, K_START, 0, T_HIT - 0.35, T_HIT, n=16)
    pts = pts_of(K) + pts_of(V) + [wpt(hand_cf(K), (0, 0, -2.9))]
    aim_lens(pts, -14, 16, 56, 12, mx=0.84, my=0.66)


@frame('tide', 3)
def m_tide_3():
    m_pass()
    return {'name': 'THE PASS'}


@frame('tide', 4)
def m_tide_4():
    m_pass(True)
    return {'name': 'CUT FRAME', 'impact': {'bg': [0.97, 0.96, 0.94], 'fg': [0.05, 0.05, 0.07], 'accent': ['smear'], 'accent_col': [0.93, 0.6, 0.72]}}


K_END_T = 3.33


@frame('tide', 5)
def m_tide_5():
    tide_stage()
    K = rig('k', at_for(SLASH, K_END_T, K_BACK, 0), 0, {'clip': (SLASH, K_END_T)})
    katana_grip(hand_cf(K))
    V = rig('v', (0, 0, 0), 180, {'clip': (LOOK, 1.35), 'face': {'LeftUpperLidRaiser': 0.8, 'RightUpperLidRaiser': 0.8}})
    petals(br(V['Head'].translation) + Vector((0.5, -1.6, 0.3)), 9, 1.6, seed=411)
    hp = br(V['Head'].translation)
    kp = br(K['Head'].translation)
    lens(hp + Vector((2.2, -6.2, -0.3)), hp * 0.8 + kp * 0.2 + Vector((0, 0, -0.8)), 40, 0)
    return {'name': 'STILLNESS'}


def k_end_spot():
    return K_BACK


@frame('tide', 6)
def m_tide_6():
    tide_stage()
    spot = k_end_spot()
    at = at_for(SHEATHE, 1.4, spot, 0)
    K = rig('k', at, 0, {'clip': (SHEATHE, 1.4)})
    a, b, d = sheath_line(K)
    sheath(K)
    katana_at_b(a - d * 0.6, d)
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 2.7)})
    hp = br(K['Head'].translation)
    pts = [hp + Vector((0, 0, 0.6)), a - d * 1.2, a + d * 2.0, br(K['RightHand'].translation), br(K['LeftHand'].translation)]
    aim_lens(pts, 212, 8, 40, 6, mx=0.8, my=0.66)
    return {'name': 'THE SHEATHE'}


@frame('tide', 7)
def m_tide_7():
    tide_stage()
    spot = k_end_spot()
    K = rig('k', at_for(SHEATHE, 2.8, spot, 0), 0, {'clip': (SHEATHE, 2.8)})
    a, b, d = sheath_line(K)
    sheath(K)
    katana_at_b(a, d)
    V = rig('v', (0, 0, 0), 180, {'clip': ('bx_27_hit_stomach', 0.24)})
    c = br(V['UpperTorso'].translation) + Vector((0, 0, -0.6))
    brush(c + Vector((-0.75, -2.0, 1.5)), c + Vector((-0.75, 2.4, -1.1)), 0.35, 0.55, (-1, 0, 0), INK, seed=61)
    brush(c + Vector((-0.82, -1.6, 1.25)), c + Vector((-0.82, 2.0, -0.95)), 0.33, 0.16, (-1, 0, 0), SKIN, seed=62, tag='stroke_edge')
    splats(c + Vector((-0.8, 0.6, 0.0)), 6, 1.0, seed=71, size=0.6)
    kp = br(K['UpperTorso'].translation)
    mid = (c + kp) / 2
    lens(mid + Vector((-10.5, 0, 0.2)), mid + Vector((0, 0, 0.2)), 44, 0)
    return {'name': 'THE CUT LANDS'}


@frame('tide', 8)
def m_tide_8():
    tide_stage()
    spot = k_end_spot()
    K = rig('k', at_for(SHEATHE, 2.8, (spot[0], spot[1] + 1.4), 0), 0, {'clip': (SHEATHE, 2.8)})
    sheath(K)
    V = rig('v', (0, 0, 0), 180, {'clip': ('bx_28_knockdown_liver', 1.2), 'scatter': 0.9})
    vc = br(V['UpperTorso'].translation)
    petals(vc + Vector((0, 0, 0.6)), 80, 2.8, seed=421, size=1.3)
    splats(vc, 8, 1.6, seed=81, size=0.6)
    lens((-7.5, -7.5, 8.5), (0.5, 1.6, 1.6), 54, 0)
    return {'name': 'PETALS'}


# ---------------- DUST, from the clips
IDLE_T = 0.0


HATS = [True]


def cowboy_hat(cf, col):
    hd = cf['Head']
    prop('Cylinder', (0.1, 2.6, 2.6), hd @ CF(0, 0.5, 0) @ ANG(0, 0, 90), col, 'SmoothPlastic', 'hat')
    prop('Block', (1.15, 0.75, 1.2), hd @ CF(0, 0.9, 0.05), col, 'SmoothPlastic', 'hat')
    prop('Block', (1.18, 0.14, 1.23), hd @ CF(0, 0.6, 0.05), (0.12, 0.09, 0.07), 'SmoothPlastic', 'hat')


def m_dust_rigs(kclip=(DRAW, IDLE_T), vclip=(DRAW, IDLE_T), kgun_in=True, kface=None, vface=None, vgun_in=True, vdz=0.0):
    K = rig('k', (0, 0, 0), 0, {'clip': kclip, 'face': kface if kface is not None else SQUINT})
    holster(K, kgun_in)
    V = rig('v', (DV.x, DV.y, vdz), 180, {'clip': vclip, 'face': vface if vface is not None else WIDE})
    holster(V, vgun_in)
    if HATS[0]:
        cowboy_hat(K, (0.24, 0.17, 0.11))
        cowboy_hat(V, (0.6, 0.47, 0.31))
    return K, V


@frame('dust', 1)
def m_dust_1():
    desert()
    K, V = m_dust_rigs()
    hd = K['Head']
    lens(br((hd @ Vector((0, 0.1, -2.4, 1))).xyz), br((hd @ Vector((0, 0.1, -0.55, 1))).xyz), 16, 0)
    return {'name': "KILLER'S EYES", 'crop': 0.3}


@frame('dust', 2)
def m_dust_2():
    desert()
    K, V = m_dust_rigs()
    hd = V['Head']
    q = (hd @ Vector((0.38, 0.32, -0.6, 1))).xyz
    prop('Ball', (0.12, 0.17, 0.12), CF(q.x, q.y, q.z), (0.85, 0.92, 1.0), 'Glass', 'sweat')
    lens(br((hd @ Vector((0, 0.1, -2.4, 1))).xyz), br((hd @ Vector((0, 0.1, -0.55, 1))).xyz), 16, 4)
    return {'name': "VICTIM'S EYES", 'crop': 0.3}


@frame('dust', 3)
def m_dust_3():
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, 0.12))
    h = br(K['RightHand'].translation)
    lens(h + Vector((1.5, -2.8, -0.5)), h + Vector((-0.4, 1.6, 0.3)), 40, -6)
    return {'name': 'THE HAND'}


@frame('dust', 4)
def m_dust_4():
    desert()
    m_dust_rigs()
    tumbleweed((2.0, 8.5, 1.6), 1.6)
    lens((25, -1.5, 1.1), (0, 8.5, 2.4), 26, 0)
    return {'name': 'THE WIDE'}


@frame('dust', 5)
def m_dust_5():
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, 0.75), kgun_in=False)
    g = revolver_in_hand(K)
    m = br((g @ Vector((0, 0.2, -1.5, 1))).xyz)
    flash(m + (m - br(g.translation)).normalized() * 0.4, 1.1, (1, -0.3, 0.2))
    puff(m + Vector((0.3, 0.6, 0.2)), 0.5, (0.86, 0.78, 0.62))
    pts = pts_of(K) + [m + Vector((0, 1.2, 0)), br(V['Head'].translation), br(V['LeftFoot'].translation)]
    aim_lens(pts, 28, -6, 54, 14, mx=0.84, my=0.66, zmin=0.6)
    return {'name': 'THE DRAW'}


@frame('dust', 6)
def m_dust_6():
    desert()
    K, V = m_dust_rigs(vclip=('bx_27_hit_stomach', 0.12))
    hit = br(V['UpperTorso'].translation) + Vector((0, -0.55, 0.1))
    prop_box_between(hit + Vector((0, -0.7, 0)), hit, 0.16, 0.16, (1.0, 0.95, 0.85), mat='Neon', tag='bullet')
    prop_box_between(hit + Vector((0, -12, -0.4)), hit + Vector((0, -0.7, 0)), 0.05, 0.05, (1.0, 0.95, 0.85), mat='Neon', tag='btrail')
    flash(hit + Vector((0, -0.2, 0)), 1.1, (-1, -1, 0.1), col=(1.0, 0.95, 0.85), rays=8, tag='shock')
    vt = br(V['UpperTorso'].translation)
    lens(vt + Vector((-3.8, -5.0, 0.4)), vt + Vector((0, 0, 0.6)), 40, -8)
    return {'name': 'HIT FRAME', 'impact': {'bg': [0.04, 0.03, 0.03], 'fg': [1.0, 0.72, 0.32], 'accent': ['bullet', 'btrail', 'shock'], 'accent_col': [1.0, 0.95, 0.85]}}


@frame('dust', 7)
def m_dust_7():
    desert()
    K, V = m_dust_rigs(vclip=('bx_27_hit_stomach', 0.48))
    c = br(V['UpperTorso'].translation)
    for i in range(16):
        a = 2 * math.pi * i / 16
        r = 0.9 + 0.5 * (i % 3)
        q = rb(c + Vector((math.cos(a) * 2.0, 1.4 + abs(math.sin(a)) * 0.8, math.sin(a) * 1.6)))
        prop('Ball', (r, r, r), CF(q.x, q.y, q.z), SAND if i % 2 else (1.0, 0.86, 0.55), 'Sand', 'dustburst')
    pts = pts_of(V) + [c + Vector((2.2, 1.6, 1.8)), c + Vector((-2.2, 1.6, -1.6))]
    aim_lens(pts, 25, -8, 44, -6)
    return {'name': 'THE HIT'}


@frame('dust', 8)
def m_dust_8():
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, 0.06), kgun_in=False, vclip=('bx_28_knockdown_liver', 1.2))
    g = revolver_in_hand(K)
    h = br(K['RightHand'].translation)
    m = br((g @ Vector((0, 0.2, -1.5, 1))).xyz)
    for i, (dz, r) in enumerate(((0.3, 0.2), (0.75, 0.28), (1.25, 0.34))):
        puff(m + Vector((0.05 * i, 0.05, dz)), r)
    pts = [br(K['Head'].translation), h + Vector((0, 0, -1.2)), m + Vector((0, 0, 1.4)), br(K['LeftHand'].translation)]
    aim_lens(pts, 145, 2, 36, 5, mx=0.8, my=0.66)
    return {'name': 'HOLSTER'}


# ================================================================== VIDEO: the moving cut (main, 19 Nov: the owner wants to
# judge it as a video). Each shot is a function of its frame number: the bodies play their clips frame by frame, the
# lens moves on a path, the effects grow with time. 24 fps. S keeps a shot's numbers from its first frame (a lens that
# must not jitter); VT[0] is the video's own clock (petals drift across cuts).
FPS = 24
VIDEO = {}
S = {}
VT = [0.0]


def shot(video, name, nframes):
    def deco(fn):
        VIDEO.setdefault(video, []).append((name, nframes, fn))
        return fn
    return deco


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def bounce(s_, land, h=0.45):
    # a body hitting the ground bounces up a little, twice, settling (s_ and land in seconds)
    if s_ <= land:
        return 0.0
    k = s_ - land
    return h * math.exp(-6.5 * k) * abs(math.sin(math.pi * k / 0.2))


def lerpv(a, b, u):
    return Vector(a).lerp(Vector(b), u)


def peek_rig(name, at, yaw, pose):
    # a body's parts at another moment (to frame a lens on where they will be), not added to the scene
    n0 = len(RIGS)
    cf = rig(name, at, yaw, pose)
    del RIGS[n0:]
    return cf


def petals_drift(center_b, n, spread, s, seed=19, size=1.0, vel=(0.6, -0.3, -0.35), spin=140):
    rnd = random.Random(seed)
    for i in range(n):
        base = Vector(center_b) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))) * spread
        ph = rnd.uniform(0, 6.28)
        p = rb(base + Vector(vel) * s + Vector((math.sin(ph + s * 3) * 0.25, 0, math.cos(ph + s * 2.3) * 0.12)))
        a = (rnd.uniform(0, 360) + spin * s, rnd.uniform(0, 360) + spin * 0.7 * s, rnd.uniform(0, 360))
        prop('Block', (0.32 * size, 0.04, 0.22 * size), CF(p.x, p.y, p.z) @ ANG(*a), SAKURA, 'SmoothPlastic', 'petal')


def burst(center_b, n, reach_, u, seed, kind='petal', size=1.0, fall=1.2):
    # pieces thrown out from a point: fast at first, slowing, then falling (u: 0 -> 1 over the burst)
    rnd = random.Random(seed)
    k = 1 - (1 - max(0.0, min(1.0, u))) ** 2.2
    for i in range(n):
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 1))).normalized()
        r = reach_ * rnd.uniform(0.35, 1.0)
        p = rb(Vector(center_b) + d * r * k + Vector((0, 0, -fall * u * u)))
        if kind == 'petal':
            a = (rnd.uniform(0, 360) + 300 * u, rnd.uniform(0, 360) + 200 * u, rnd.uniform(0, 360))
            prop('Block', (0.32 * size, 0.04, 0.22 * size), CF(p.x, p.y, p.z) @ ANG(*a),
                 SAKURA if i % 4 else (0.98, 0.86, 0.9), 'SmoothPlastic', 'petal')
        else:
            sz = 0.18 * size * rnd.uniform(0.6, 1.6) * (1 - 0.5 * u)
            prop('Ball', (sz, sz, sz), CF(p.x, p.y, p.z), INK, 'SmoothPlastic', 'splat')


DUST = {'list': [], 'last': {}}


def kick_dust(K, now, col=(0.78, 0.76, 0.74), tag='dust'):
    # a puff where a foot strikes the floor (the reference's crouched sprint kicks dust at every step); each grows,
    # drifts back along the run and thins out over half a second
    for f in ('LeftFoot', 'RightFoot'):
        q = K[f].translation
        if q.y < 0.6 and now - DUST['last'].get(f, -9.0) > 0.16:
            DUST['last'][f] = now
            DUST['list'].append((now, br(q)))
    keep = []
    for t0, pb in DUST['list']:
        age = now - t0
        if age > 0.5 or age < 0:
            continue
        keep.append((t0, pb))
        k = age / 0.5
        PROP_TR[0] = 0.3 + 0.65 * k
        for dx, dy, dz, r0 in ((0, 0, 0.2, 0.55), (0.35, -0.25, 0.15, 0.42), (-0.3, -0.35, 0.28, 0.36)):
            r = r0 * (1 + 1.7 * k)
            q = rb(pb + Vector((dx, dy - 0.9 * k, dz + 0.45 * k)))
            prop('Ball', (r, r, r), CF(q.x, max(q.y, r * 0.3), q.z), col, 'SmoothPlastic', tag)
        PROP_TR[0] = 0.0
    DUST['list'] = keep


IMPACT_TIDE = {'bg': [0.97, 0.96, 0.94], 'fg': [0.05, 0.05, 0.07], 'accent': ['smear'], 'accent_col': [0.93, 0.6, 0.72]}
STROKE_HIT = {'bg': [0.97, 0.96, 0.94], 'fg': [0.05, 0.05, 0.07], 'accent': ['stroke', 'stroke_edge'], 'accent_col': [0.93, 0.6, 0.72]}


def tv_k(at, t):
    K = rig('k', at, 0, {'clip': (SLASH, t)})
    katana_grip(hand_cf(K))
    return K


@shot('tide_old', 'ESTABLISH', 14)
def tv_establish(i, n):
    u = i / (n - 1)
    tide_stage(VT[0])
    K = tv_k(K_START, 0.3 * u)
    V = rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.3 * u)})
    if i == 0:
        S['mid'] = (br(K['LowerTorso'].translation) + br(V['LowerTorso'].translation)) / 2
    mid = S['mid']
    lens(mid + Vector((30 - 3 * ease(u), 0, 1.4)), mid + Vector((0, 0, 0.6)), 34, 0)


LONG_KAT = 6.0   # the gag's blade: six times the skin's


RUN = 'mx_ninja_run'        # Mixamo "Female Ninja Run": the lowest, most anime run on Mixamo (torso about 60 deg over)
DRAWC = 'mb_iai_draw'       # the two-hand iai draw (MotionBricks from our Mixamo poses, the owner's gif): hilt in the
                            # right hand, scabbard in the left, the arms spreading apart as the blade comes out
DRAW_LEN = 0.93
IAI_OUT = 0.62             # where the draw stops (the hands 3.5 studs apart, the sword's line still clear of the belly)
RUN_T = 30 / 24             # the run-up's length (s): long enough to cover the ground, no jump into the pass


def run_places():
    # where the run starts and ends: it ends where the slash take is at 1.6 s (the closing shot picks up from there)
    if 'run_at' not in S_FIX:
        h16 = Vector(K_START[:2]) + hips_b(SLASH, 1.6, 0).xy
        S_FIX['run_at'] = at_for(RUN, RUN_T, (h16.x, h16.y), 0)
        h0 = Vector(S_FIX['run_at'][:2]) + hips_b(RUN, 0.0, 0).xy
        S_FIX['run_h0'] = (h0.x, h0.y)
        S_FIX['draw_at'] = at_for(DRAWC, 0.0, S_FIX['run_h0'], 0)
        S_FIX['stance_at'] = at_for(SLASH, 0.0, S_FIX['run_h0'], 0)
    return S_FIX


S_FIX = {}


def kat_through(K, a, d):
    # the blade from the hand back through the scabbard's mouth (being drawn or put away): only as long as reaches 3
    # studs past the mouth (the scabbard hides the rest - the long blade's gag)
    grip = wpt(hand_cf(K), (0, 0, 0))
    v = a - grip
    if v.length < 0.5:
        KAT_LEN[0] = 1.0
        SEM['kat'] = {'mode': 'home', 'push': 0.0}
        katana_at_b(a, d)
        return
    SEM['kat'] = {'mode': 'through'}
    dirv = v.normalized()
    KAT_LEN[0] = max(1.0, (v.length + 3.0 - 0.6) / 2.3)
    katana_at_b(grip + dirv * 0.44, dirv)


def grip_sheath():
    # the owner (20 Nov): the hands must hold the sword like their gif - the right on the hilt, the left on the scabbard,
    # the guard between them. So the scabbard is placed from the draw clip itself: at the moment the right hand takes
    # the hilt, the guard sits just past that hand and the scabbard runs on through the left hand
    if 'gs' not in S_FIX:
        P = run_places()
        Kg = peek_rig('k', P['draw_at'], 0, {'clip': (DRAWC, t_grab())})
        lt_inv = Kg['LowerTorso'].inverted()
        r = lt_inv @ hand_cf(Kg).translation.to_4d()
        l = lt_inv @ Kg['LeftHand'].translation.to_4d()
        d = (l.xyz - r.xyz).normalized()
        m_ = r.xyz + d * 0.44
        S_FIX['gs'] = (Vector((m_.x, m_.y, m_.z, 1)), Vector(((m_ + d * 3.3).x, (m_ + d * 3.3).y, (m_ + d * 3.3).z, 1)))
    return S_FIX['gs']


def t_grab():
    # (the take opens on 0.1 s of still grip: both hands on the sword at the left hip)
    return 0.1


def mouth_off():
    # how far the scabbard's mouth sits from the left hand (toward the hilt): set at the grab, where the guard touches
    # the mouth (0.44 past the grip)
    if 'm0' not in S_FIX:
        P = run_places()
        Kg = peek_rig('k', P['draw_at'], 0, {'clip': (DRAWC, t_grab())})
        S_FIX['m0'] = max(0.2, (Kg['LeftHand'].translation - hand_cf(Kg).translation).length - 0.44)
    return S_FIX['m0']


def hands_sheath(K, fwd=0.0):
    # the scabbard held in the left hand: its mouth mouth_off() from that hand toward the right hand (the hilt), the
    # scabbard running back from the mouth through the left hand - the LowerTorso-space pair sheath_line uses
    R = hand_cf(K).translation
    L = K['LeftHand'].translation
    d = (L - R)
    d = d.normalized() if d.length > 1e-3 else Vector((-1, 0, 0))
    m_ = L - d * mouth_off()
    t_ = m_ + d * 3.3
    if fwd:
        look = -K['LowerTorso'].col[2].xyz
        m_, t_ = m_ + look * fwd, t_ + look * fwd
    SEM['sh'] = dict({'mode': 'lhand', 'm0': round(mouth_off(), 3)}, **({'fwd': round(fwd, 3)} if fwd else {}))
    inv = K['LowerTorso'].inverted()
    return (inv @ Vector((m_.x, m_.y, m_.z, 1)), inv @ Vector((t_.x, t_.y, t_.z, 1)))


@shot('tide_v3', 'THE DRAW', 10)
def tv_draw(i, n):
    # the owner (20 Nov, their gif): "a hand on the sheathe and a hand on the blade". The study's opening (Zenitsu's
    # thunderclap, Zoro's draw): the hands at the sword, broadside and a little high, tight on the guard between them;
    # the thumb eases the guard out of the mouth over 3 frames, a glint opens in the gap, and it holds
    P = run_places()
    tide_stage(VT[0])
    K = rig('k', P['draw_at'], 0, {'clip': (DRAWC, t_grab())})
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.0)})
    SHEATH_LOCAL[0] = hands_sheath(K)
    a, b, d = sheath_line(K)
    sheath(K)
    SHEATH_LOCAL[0] = None
    push = 0.12 * ease(min(1.0, max(0.0, (i - 3) / 2)))
    KAT_LEN[0] = 1.0
    SEM['kat'] = {'mode': 'home', 'push': round(push, 3)}
    katana_at_b(a - d * push, d)
    if i >= 4:
        side_ = d.cross(Vector((0, 0, 1))).normalized()
        if side_.dot(a - br(K['LowerTorso'].translation)) < 0:
            side_ = -side_
        g = a - d * (push * 0.5) + Vector((0, 0, 0.16)) + side_ * 0.12
        k_ = 1.5 if i == 5 else 0.8
        prop('Block', (0.04, 0.36 * k_, 0.04), CF(*rb(g)), (1.0, 0.98, 0.94), 'Neon', 'glint')
        prop('Block', (0.36 * k_, 0.04, 0.04), CF(*rb(g)), (1.0, 0.98, 0.94), 'Neon', 'glint')
    if i == 0:
        hips = br(K['LowerTorso'].translation)
        side = d.cross(Vector((0, 0, 1))).normalized()
        if side.dot(a - hips) < 0:
            side = -side
        c = a + d * 0.35                     # the guard and the scabbard's mouth, the left hand just in
        S['pos'], S['c'] = c + side * 2.5 + Vector((0, 0, 0.9)), c
    lens(S['pos'], S['c'], 34, 0)


@shot('tide_v3', 'THE PULL', 14)
def tv_pull(i, n):
    # the cut to the body (the study: low, front three-quarter, medium): the arms spread along the belt line, the blade
    # comes out between them over 12 frames, slower than life; a 2-frame hold with more blade out than a katana has
    u = i / (n - 1)
    P = run_places()
    tide_stage(VT[0])
    tg = t_grab()
    t = tg + (IAI_OUT - tg) * ease(min(1.0, i / 11))
    K = rig('k', P['draw_at'], 0, {'clip': (DRAWC, t)})
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.0)})
    SHEATH_LOCAL[0] = hands_sheath(K)
    a, b, d = sheath_line(K)
    sheath(K)
    kat_through(K, a, d)
    SHEATH_LOCAL[0] = None
    if i == 0:
        Ke = peek_rig('k', P['draw_at'], 0, {'clip': (DRAWC, IAI_OUT)})
        pts = pts_of(Ke) + [wpt(hand_cf(Ke), (0, 0, 0)), br(Ke['LeftHand'].translation)]
        S['pos'], S['c'] = aim_lens(pts, 200, -10, 40, 0, mx=0.86, my=0.8, zmin=0.45)
    lens(lerpv(S['pos'], S['c'] + (S['pos'] - S['c']) * 0.95, u), S['c'], 40, 0)


@shot('tide_v3', 'IT KEEPS COMING', 14)
def tv_coming(i, n):
    # the gag (the katana grows with kills): tight on the scabbard's mouth, the blade keeps coming out, faster and faster,
    # long after any blade should have ended (the hand is out of the shot)
    u = i / (n - 1)
    P = run_places()
    tide_stage(VT[0])
    K = rig('k', P['draw_at'], 0, {'clip': (DRAWC, IAI_OUT)})
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.05)})
    SHEATH_LOCAL[0] = hands_sheath(K)
    a, b, d = sheath_line(K)
    sheath(K)
    SHEATH_LOCAL[0] = None
    if i == 0:
        S['e0'] = max(1.0, (wpt(hand_cf(K), (0, 0, 0)) - a).length - 0.44)
    e = S['e0'] + (2.3 * LONG_KAT + 0.6 - 3.0 - S['e0']) * (u ** 1.6)
    KAT_LEN[0] = max(1.0, (e + 3.0 - 0.6) / 2.3)
    SEM['kat'] = {'mode': 'out', 'e': round(e, 3), 'glints': 1}
    katana_at_b(a - d * e, d)
    km = KATANA[-1]
    for j in range(40):
        x = 0.7 + j * 0.85                       # along the blade from the guard (fixed on the blade: it moves with it)
        out_ = e - x                             # how far this glint is out of the mouth (inside the scabbard if < 0)
        if out_ < 0.05 or out_ > 4.5:
            continue
        prop('Block', (0.1, 0.28, 0.07), km @ CF(0, 0.1, -(0.44 + x)), (1.0, 0.97, 0.95), 'Neon', 'glint')
    if i >= 2:
        burst(a - d * 0.15, 6 + i, 1.2, min(1.0, (i - 2) / 9), seed=500 + i, size=0.8, fall=0.4)
    if i == 0:
        # square on to the blade's way out (across the body now: the scabbard runs through the left hand), from in front
        hips = br(K['LowerTorso'].translation)
        side = d.cross(Vector((0, 0, 1))).normalized()
        if side.dot(a - hips) < 0:
            side = -side
        S['pos'], S['c'] = a + side * 3.3 + Vector((0, 0, -0.25)) - d * 0.7, a - d * 0.7
        S['d'] = d
    drift = -S['d'] * (0.9 * ease(u))
    lens(S['pos'] + drift, S['c'] + drift, 42, 6)


@shot('tide_v3', 'THE LENGTH', 14)
def tv_length(i, n):
    # the reveal, wide and low: the whole absurd blade out, its tip resting on the floor far ahead; a beat to take it in
    u = i / (n - 1)
    tide_stage(VT[0])
    KAT_LEN[0] = LONG_KAT
    K = tv_k(run_places()['stance_at'], 0.0)
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.1 + 0.3 * u)})
    if i == 0:
        pts = pts_of(K) + [wpt(hand_cf(K), (0, 0, tipz())), wpt(hand_cf(K), (0, 0, tipz() * 0.5))]
        S['pos'], S['c'] = aim_lens(pts, 290, -6, 40, 6, mx=0.84, my=0.6, zmin=0.6)
    lens(lerpv(S['pos'], S['c'] + (S['pos'] - S['c']) * 0.95, u), S['c'], 40, 6)


@shot('tide_v3', 'RUN-UP', 30)
def tv_runup(i, n):
    # the owner (20 Nov): "the run up is too quick and it sort of just teleports to him". The whole approach now, at the
    # run's own speed (no clip time skipped): low and long, ending where the closing shot carries on
    KAT_LEN[0] = LONG_KAT
    P = run_places()
    t = RUN_T * i / (n - 1)
    tide_stage(VT[0])
    K = rig('k', P['run_at'], 0, {'clip': (RUN, t)})
    katana_grip(hand_cf(K))
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.4 + i / FPS)})
    h = br(K['LowerTorso'].translation)
    if i == 0:
        Km = peek_rig('k', P['run_at'], 0, {'clip': (RUN, RUN_T / 2)})
        hm = br(Km['LowerTorso'].translation)
        pos, c = aim_lens(pts_of(Km) + [br(Km['Head'].translation) + Vector((0, 0, 0.8))], 298, -6, 74, 16, mx=0.42, my=0.5, zmin=0.35)
        S['off'], S['coff'], S['z'], S['cz'] = pos - hm, c - hm, pos.z, c.z
    pos, c = h + S['off'], h + S['coff']
    pos.z, c.z = S['z'], S['cz']
    kick_dust(K, VT[0])
    lens(pos, c, 74, 16)


@shot('tide_v3', 'CLOSING', 12)
def tv_closing(i, n):
    KAT_LEN[0] = LONG_KAT
    u = i / (n - 1)
    t = 1.6 + 0.5 * i / (n - 1)
    tide_stage(VT[0])
    K = tv_k(K_START, t)
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 1.7 + i / FPS)})
    blade_sweep(SLASH, K_START, 0, t - 0.12, t, n=6)
    ut = br(K['UpperTorso'].translation)
    if i == 0:
        # on the floor in their path, framed on where they arrive; the lens punches wider as they close
        Ke = peek_rig('k', K_START, 0, {'clip': (SLASH, 1.6 + (n - 1) / FPS)})
        # from the side of their path (az 125): straight ahead puts the victim's back against the lens
        pos, c = aim_lens(pts_of(Ke) + [wpt(hand_cf(Ke), (0, 0, tipz()))], 235, -18, 96, 20, mx=0.72, my=0.64, zmin=0.35)
        S['pos'], S['c'], S['ute'] = pos, c, br(Ke['UpperTorso'].translation)
    kick_dust(K, VT[0])
    lens(S['pos'], S['c'] + (ut - S['ute']) * 0.85, 70 + 26 * ease(u), 20)


@shot('tide_v3', 'THE PASS', 11)
def tv_pass(i, n):
    KAT_LEN[0] = LONG_KAT
    # the owner's manga page (20 Nov): full speed, low and wide from the outside of their line, near profile - the two
    # bodies meet in one blur. Afterimages trace the killer's path, dust is thrown up, the bright smear grows along the
    # blade's real path. The lens sits on the run-up's side of the line, so the killer keeps moving the same way on
    # screen (a cut that flips screen direction reads as a teleport)
    u = i / (n - 1)
    t = T_HIT - 0.45 + 0.45 * u
    tide_stage(VT[0])
    K = tv_k(K_START, t)
    for j, (dt_, tr_) in enumerate(((0.05, 0.55), (0.1, 0.72), (0.15, 0.86))):
        rig('kg%d' % j, K_START, 0, {'clip': (SLASH, t - dt_)}, tr=tr_)
    rig('v', (0, 0, 0), 180, {'clip': ('bx_18_block_high_center', 0.1 + 0.25 * u)})
    t0 = T_HIT - 0.35
    if t > t0 + 0.03:
        blade_sweep(SLASH, K_START, 0, t0, t, n=max(3, int(16 * (t - t0) / 0.35)))
    kick_dust(K, VT[0])
    if i == 0:
        Ke = peek_rig('k', K_START, 0, {'clip': (SLASH, T_HIT)})
        Ve = peek_rig('v', (0, 0, 0), 180, {'clip': ('bx_18_block_high_center', 0.35)})
        S['pos'], S['c'] = aim_lens(pts_of(Ke) + pts_of(Ve) + [wpt(hand_cf(Ke), (0, 0, tipz()))], 215, -6, 62, 7,
                                    mx=0.72, my=0.6, zmin=0.5)
    S['pass_look'] = S['c']
    if i == 0:
        S_FIX['pass_side'] = tuple(Vector(((S['pos'] - S['c']).x, (S['pos'] - S['c']).y, 0)).normalized())
    lens(S['pos'], S['c'], 64, 7 + 3 * u)


@shot('tide_v3', 'CUT FRAME', 6)
def tv_cutframe(i, n):
    KAT_LEN[0] = LONG_KAT
    tide_stage(VT[0])
    tv_k(K_START, T_HIT)
    rig('v', (0, 0, 0), 180, {'clip': ('bx_18_block_high_center', 0.35)})
    blade_sweep(SLASH, K_START, 0, T_HIT - 0.35, T_HIT, n=16)
    lens(S['pos'], S['pass_look'], 64, 10)
    if i in (2, 5):
        return {'impact': dict(IMPACT_TIDE, bg=IMPACT_TIDE['fg'], fg=IMPACT_TIDE['bg'])}
    return {'impact': IMPACT_TIDE}


@shot('tide_v3', 'BACK TO BACK', 16)
def tv_backtoback(i, n):
    KAT_LEN[0] = LONG_KAT
    # a held beat: side by side, facing away from each other, nobody looks back; the killer still in the follow-through,
    # the victim frozen in a guard that came too late. Low, in front of the killer, past the victim's back; a slow push
    u = i / (n - 1)
    tide_stage(VT[0])
    K = tv_k(K_START, min(K_END_T, 2.75 + 0.25 * u))
    V = rig('v', (0, 0, 0), 180, {'clip': ('bx_18_block_high_center', 0.35 + 0.05 * u)})
    if i == 0:
        kc, vc = br(K['UpperTorso'].translation), br(V['UpperTorso'].translation)
        m_ = (kc + vc) / 2
        S['pos'], S['c'] = m_ + Vector((-3.4, 19.5, 0.7)), m_ + Vector((0, 0, 0.1))
    lens(S['pos'], S['c'], 23, 0)


@shot('tide_v3', 'STILLNESS', 16)
def tv_still(i, n):
    u = i / (n - 1)
    s = i / FPS
    tide_stage(VT[0])
    KAT_LEN[0] = LONG_KAT
    K = tv_k(K_START, K_END_T)
    V = rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.95 + s), 'face': {'LeftUpperLidRaiser': 0.8, 'RightUpperLidRaiser': 0.8}})
    hp = br(V['Head'].translation)
    if i == 0:
        S['hp0'], S['kp0'] = hp, br(K['Head'].translation)
    hp0, kp0 = S['hp0'], S['kp0']
    petals_drift(hp0 + Vector((0.5, -1.6, 0.3)), 9, 1.6, s, seed=411, vel=(0.5, -0.2, -0.3))
    pos = lerpv(hp0 + Vector((2.2, -6.2, -0.3)), hp0 + Vector((1.8, -5.0, -0.25)), ease(u))
    lens(pos, (hp * 0.5 + hp0 * 0.5) * 0.8 + kp0 * 0.2 + Vector((0, 0, -0.8)), 40, 0)


def sheathe_at():
    # the draw clip, played backwards, puts the blade away: its last stance stood where the slash take ends
    if 'sh_at' not in S_FIX:
        S_FIX['sh_at'] = at_for(DRAWC, IAI_OUT, K_BACK, 0)
    return S_FIX['sh_at']


@shot('tide_v3', 'THE SHEATHE', 28)
def tv_sheathe(i, n):
    # slow, close and low on the hands: the long blade goes back through the scabbard's mouth (the scabbard swallows
    # what it can't hold), the guard meets the mouth on the last frame - the click
    u = i / (n - 1)
    tide_stage(VT[0])
    CLICK = 17
    w = min(1.0, i / CLICK)
    t = IAI_OUT - (IAI_OUT - t_grab()) * (1 - (1 - w) ** 2.2)
    K = rig('k', sheathe_at(), 0, {'clip': (DRAWC, t)})
    SHEATH_LOCAL[0] = hands_sheath(K)
    a, b, d = sheath_line(K)
    sheath(K)
    SHEATH_LOCAL[0] = None
    if i >= CLICK:
        KAT_LEN[0] = 1.0
        katana_at_b(a, d)
    else:
        kat_through(K, a, d)
    hips = br(K['LowerTorso'].translation)
    side = d.cross(Vector((0, 0, 1))).normalized()
    if side.dot(a - hips) < 0:
        side = -side
    c = a - d * 0.5
    lens(c + side * 2.8 + Vector((0, 0, -0.55)), c + Vector((0, 0, 0.05)), 38, 0)
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 2.2 + i / FPS)})


@shot('tide_v3', 'THE CUT LANDS', 14)
def tv_cutlands(i, n):
    s = i / FPS
    tide_stage(VT[0])
    K = rig('k', sheathe_at(), 0, {'clip': (DRAWC, t_grab())})
    SHEATH_LOCAL[0] = hands_sheath(K)
    a, b, d = sheath_line(K)
    sheath(K)
    SHEATH_LOCAL[0] = None
    katana_at_b(a, d)
    V = rig('v', (0, 0, 0), 180, {'clip': ('bx_27_hit_stomach', 0.05 + s)})
    if i == 0:
        S['c'] = br(V['UpperTorso'].translation) + Vector((0, 0, -0.6))
        S['kp'] = br(K['UpperTorso'].translation)
    c = S['c']
    PROP_TR[0] = 0.0 if i < 4 else min(0.85, (i - 4) * 0.1)   # the stroke fades after the hit
    brush(c + Vector((-2.2, -0.8, 0.55)), c + Vector((2.2, -0.8, -0.3)), 0.25, 0.5, (0, -1, 0), INK, seed=61)
    brush(c + Vector((-1.9, -0.86, 0.4)), c + Vector((1.9, -0.86, -0.2)), 0.22, 0.15, (0, -1, 0), SKIN, seed=62, tag='stroke_edge')
    PROP_TR[0] = 0.0
    if i >= 2:
        burst(c + Vector((0.4, -0.9, 0.0)), 10, 2.0, (i - 2) / 10, seed=71, kind='splat', size=0.7)
    mid = (c + S['kp']) / 2
    lens(mid + Vector((0.6, -10.5, 0.3)), mid + Vector((0, 0, 0.2)), 44, 0)
    if i < 2:
        return {'impact': STROKE_HIT}


@shot('tide_old', 'PETALS', 22)
def tv_petals(i, n):
    u = i / (n - 1)
    tide_stage(VT[0])
    K = rig('k', at_for(SHEATHE, 1.0, K_BACK, 0), 0, {'clip': (SHEATHE, 2.8)})
    a, b, d = sheath_line(K)
    sheath(K)
    katana_at_b(a, d)
    V = rig('v', (0, 0, 0), 180, {'clip': ('bx_28_knockdown_liver', 0.9 + 0.54 * u), 'scatter': 1.1 * ease(u)})
    if i == 0:
        S['vc'] = br(V['UpperTorso'].translation)
    vc = S['vc']
    burst(vc + Vector((0, 0, 0.4)), 80, 3.2, u, seed=421, size=1.3, fall=0.8)
    burst(vc, 8, 1.8, u, seed=81, kind='splat', size=0.6)
    # the manga page's last panel: low past the fallen victim to the winner standing against the sun
    kt = br(K['UpperTorso'].translation)
    lens(lerpv(END_CAM, Vector(END_CAM) * 0.86 + kt * 0.14, ease(u)), kt + Vector((0, 0, 0.2)), 40, 0)


@shot('tide_v3', 'THE END', 30)
def tv_end(i, n):
    # the owner's ending: "close up of you on the right with enemy in the background on the ground". The winner lets go
    # of the hilt; behind them the cut one folds, goes down backwards and settles, coming apart into petals
    u = i / (n - 1)
    s_ = i / FPS
    tide_stage(VT[0])
    K = rig('k', sheathe_at(), 0, {'clip': (DRAWC, t_grab())})
    SHEATH_LOCAL[0] = hands_sheath(K)
    a, b, d = sheath_line(K)
    sheath(K)
    SHEATH_LOCAL[0] = None
    katana_at_b(a, d)
    V = rig('v', (0, 0, bounce(s_, 0.6)), 180, {'clip': ('bx_29_knocked_out_back', min(3.6, 1.75 + 1.25 * s_)),
                                                 'scatter': 0.5 * ease((i - 18) / 11) if i > 18 else 0.0})
    if i == 0:
        S['kc'] = br(K['UpperTorso'].translation)
        S['vc0'] = br(V['UpperTorso'].translation)
    kc, vc0 = S['kc'], S['vc0']
    if i >= 12:
        vb = br(V['UpperTorso'].translation)
        burst(vb + Vector((0, 0, 0.3)), 60, 2.6, (i - 12) / (n - 13), seed=421, size=1.2, fall=0.6)
    cam = kc + Vector((-4.4, 4.2, 0.95))
    look = kc * 0.38 + vc0 * 0.62 + Vector((0, 0, -0.4))
    lens(lerpv(cam, kc + (cam - kc) * 0.92, ease(u)), look, 42, 0)


# ---------------- DUST, moving: the standoff. The owner (19 Nov): "add suspense and close ups to the western style" -
# eyes, eyes, the killer's hand, the victim's hand, the sweat, the far wide with the tumbleweed, then one last tighter
# look at the eyes before the snap. The owner again (20 Nov): "it goes too quickly ... not enough suspense" - so every
# hold is long and slow (the standoff alone runs 6 s; 8.3 s in all, past the usual window: the end screen waits)
@shot('dust', 'OVERHEAD', 36)
def dv_overhead(i, n):
    # the owner (20 Nov): "the opening shot ... over head of both, but it zooms in, and the borders come in"
    u = i / (n - 1)
    desert()
    m_dust_rigs()
    mid = Vector((0, DV.y / 2, 0))
    lens(lerpv(mid + Vector((-15, 0, 44)), mid + Vector((-7.5, 0, 21)), ease(u)), mid + Vector((0, 0, 0.5)), 46 - 8 * ease(u), 0)


@shot('dust', "KILLER'S EYES", 20)
def dv_keyes(i, n):
    u = i / (n - 1)
    desert()
    b = max(0.0, 1 - abs(u - 0.55) / 0.14)   # one slow blink in the hold
    K, V = m_dust_rigs(kface=dict(SQUINT, LeftEyeClosed=0.55 + 0.45 * b, RightEyeClosed=0.55 + 0.45 * b))
    hd = K['Head']
    lens(br((hd @ Vector((0, 0.17, -3.9 + 0.35 * ease(u), 1))).xyz), br((hd @ Vector((0, 0.2, -0.55, 1))).xyz), 18, 0)


@shot('dust', "VICTIM'S EYES", 18)
def dv_veyes(i, n):
    u = i / (n - 1)
    desert()
    dart = math.sin(u * math.pi * 3)          # the eyes dart one way, the other, back
    K, V = m_dust_rigs(vface=dict(WIDE, EyesLookLeft=max(0.0, dart), EyesLookRight=max(0.0, -dart)))
    hd = V['Head']
    q = (hd @ Vector((0.38, 0.32 - 0.3 * u, -0.6, 1))).xyz   # the bead of sweat runs down
    prop('Ball', (0.12, 0.17, 0.12), CF(q.x, q.y, q.z), (0.85, 0.92, 1.0), 'Glass', 'sweat')
    lens(br((hd @ Vector((0, 0.17, -3.9 + 0.3 * u, 1))).xyz), br((hd @ Vector((0, 0.2, -0.55, 1))).xyz), 18, 4)


@shot('dust', "KILLER'S HAND", 20)
def dv_hand(i, n):
    u = i / (n - 1)
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, 0.12 * ease(u)))    # the hand creeps down toward the holster
    if i == 0:
        S['h'] = br(K['RightHand'].translation)
    h0 = S['h']
    lens(h0 + Vector((1.5, -2.8 + 0.35 * u, -0.5)), h0 + Vector((-0.4, 1.6, 0.3)), 40, -6)


@shot('dust', "VICTIM'S HAND", 16)
def dv_vhand(i, n):
    # the reverse: over the victim's hip to the killer small down the street; the hand shakes as it creeps down (the
    # same clip, its time trembling round the moment, not a pose made by hand)
    u = i / (n - 1)
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, 0.12), vclip=(DRAW, 0.03 + 0.06 * ease(u) + 0.012 * math.sin(i * 2.3)))
    if i == 0:
        S['vh'] = br(V['RightHand'].translation)
    h0 = S['vh']
    lens(h0 + Vector((-1.5, 2.8 - 0.3 * u, -0.5)), h0 + Vector((0.4, -1.6, 0.3)), 38, 6)


@shot('dust_old', 'SWEAT', 14)
def dv_sweat(i, n):
    # tight on the victim's cheek: the bead of sweat runs down
    u = i / (n - 1)
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, 0.12), vclip=(DRAW, 0.09))
    hd = V['Head']
    q = (hd @ Vector((0.42, 0.02 - 0.32 * u, -0.6, 1))).xyz
    prop('Ball', (0.12, 0.17, 0.12), CF(q.x, q.y, q.z), (0.85, 0.92, 1.0), 'Glass', 'sweat')
    lens(br((hd @ Vector((1.5, 0.05, -1.7, 1))).xyz), br((hd @ Vector((0.25, -0.05, -0.5, 1))).xyz), 22, -8)


@shot('dust', 'THE WIDE', 34)
def dv_wide(i, n):
    u = i / (n - 1)
    desert()
    m_dust_rigs(kclip=(DRAW, 0.12))
    y = 12.5 - 8.5 * u                       # rolls right to left across the street between them
    r = 1.6
    tumbleweed((2.0, y, r + 0.25 * abs(math.sin(u * 9))), r, rot=-(12.5 - y) / r, axis=(1, 0, 0))
    lens((25, -1.5, 1.1), (0, 8.5, 2.4), 26, 0)


@shot('dust', 'EYES AGAIN', 10)
def dv_eyes2(i, n):
    # one last look, tighter and shorter than the first: the squint narrows to a slit
    u = i / (n - 1)
    desert()
    sq = 0.6 + 0.3 * ease(u)
    K, V = m_dust_rigs(kclip=(DRAW, 0.12), kface=dict(SQUINT, LeftEyeClosed=sq, RightEyeClosed=sq))
    hd = K['Head']
    lens(br((hd @ Vector((0, 0.15, -3.0 + 0.15 * u, 1))).xyz), br((hd @ Vector((0, 0.16, -0.55, 1))).xyz), 13, 0)


@shot('dust', 'THEIR EYES', 8)
def dv_veyes2(i, n):
    # and the other one's, as tight: wide and fixed now, no more darting (the owner, 20 Nov: "close ups of eyes on both")
    u = i / (n - 1)
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, 0.12), vclip=(DRAW, 0.09))
    hd = V['Head']
    q = (hd @ Vector((0.42, -0.1 - 0.1 * u, -0.6, 1))).xyz
    prop('Ball', (0.12, 0.17, 0.12), CF(q.x, q.y, q.z), (0.85, 0.92, 1.0), 'Glass', 'sweat')
    lens(br((hd @ Vector((0, 0.15, -3.0 + 0.15 * u, 1))).xyz), br((hd @ Vector((0, 0.16, -0.55, 1))).xyz), 13, -3)


@shot('dust', 'ENEMY REACHES', 8)
def dv_vreach(i, n):
    # the owner (20 Nov): "sneak a clip of enemy trying to reach gun, that would make the abrupt shot more impactful" -
    # behind the other one's arm: they go for it first
    u = i / (n - 1)
    desert()
    tv_ = 0.04 + 0.36 * u
    K, V = m_dust_rigs(kclip=(DRAW, 0.12), vclip=(DRAW, tv_), vgun_in=tv_ < 0.3)
    if tv_ >= 0.3:
        revolver_in_hand(V)
    if i == 0:
        S['vh'] = br(V['RightHand'].translation)
    h0 = S['vh']
    lens(h0 + Vector((-1.4, 2.6, -0.3)), h0 + Vector((0.4, -1.6, 0.0)), 44, 8)


DRAW_OUT = 0.3   # from here on the revolver is in the hand, not the holster


@shot('dust', 'THE DRAW', 10)
def dv_draw(i, n):
    # a perspective shot: low behind the gun hip, wide, tilted, looking up past the revolver to the victim far down
    # the street. The gun leaves smears - a bright streak along the muzzle's real path and fading copies of the gun
    u = i / (n - 1)
    t = 0.12 + 0.63 * u
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, t), kgun_in=t < DRAW_OUT, vclip=(DRAW, 0.4 + 0.08 * u), vgun_in=False)
    revolver_in_hand(V)
    if i == 0:
        Ke = peek_rig('k', (0, 0, 0), 0, {'clip': (DRAW, 0.75)})
        Ve = peek_rig('v', (DV.x, DV.y, 0), 180, {'clip': (DRAW, IDLE_T)})
        n0 = len(GUNS)
        g = revolver_in_hand(Ke)
        del GUNS[n0:]
        m = br((g @ Vector((0, 0.2, -1.5, 1))).xyz)
        hip = br(Ke['RightUpperLeg'].translation)
        S['pos'] = hip + Vector((2.5, -3.1, -0.45))
        S['c'] = m * 0.55 + br(Ve['Head'].translation) * 0.45
    if t >= DRAW_OUT:
        # the smear: the muzzle's path over the last frames, bright and thinning, and two fading gun copies behind
        pts = []
        for j in range(7):
            tj = max(DRAW_OUT, t - 0.16 * j / 6)
            Kj = peek_rig('k', (0, 0, 0), 0, {'clip': (DRAW, tj)})
            gj = Kj['RightHand'] @ CF(0, -0.1, 0) @ ANG(-90, 0, 0) @ CF(0, 0.55, -0.25)
            pts.append(br((gj @ Vector((0, 0.2, -1.2, 1))).xyz))
        for j in range(6):
            if (pts[j] - pts[j + 1]).length > 0.02:
                PROP_TR[0] = 0.15 + 0.12 * j
                prop_box_between(pts[j + 1], pts[j], 0.08, 0.32 * (1 - j / 7), (1.0, 0.92, 0.7), mat='Neon', tag='gsmear')
                PROP_TR[0] = 0.0
        for j, (dt_, tr_) in enumerate(((0.05, 0.55), (0.1, 0.78))):
            tj = t - dt_
            if tj >= DRAW_OUT:
                Kj = peek_rig('k', (0, 0, 0), 0, {'clip': (DRAW, tj)})
                revolver_in_hand(Kj, tr=tr_)
        g = revolver_in_hand(K)
        if u > 0.8:   # the shot: muzzle flash on the last frames
            m = br((g @ Vector((0, 0.2, -1.5, 1))).xyz)
            flash(m + (m - br(g.translation)).normalized() * 0.4, 1.1, (1, -0.3, 0.2))
            puff(m + Vector((0.3, 0.6, 0.2)), 0.5, (0.86, 0.78, 0.62))
    lens(S['pos'], S['c'], 70, 12 + 6 * u)


@shot('dust', 'HIT FRAME', 6)
def dv_hitframe(i, n):
    # (the owner: "1 frame is too short and it's also a different perspective") - the draw's own lens, held, the shot
    # landing far down the street: a line from the muzzle to the chest, the shock where it lands; two-tone, flickering
    # to its inverse
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, 0.75), kgun_in=False, vclip=('bx_30_knockdown_punch', 0.1 + 0.03 * i), vgun_in=False)
    g = revolver_in_hand(K)
    m = br((g @ Vector((0, 0.2, -1.5, 1))).xyz)
    hit = br(V['UpperTorso'].translation) + Vector((0, -0.55, 0.1))
    prop_box_between(m, hit, 0.09, 0.09, (1.0, 0.95, 0.85), mat='Neon', tag='btrail')
    flash(hit, 1.4 + 0.15 * i, (0, -1, 0.1), col=(1.0, 0.95, 0.85), rays=9, tag='shock')
    lens(S['pos'] + (S['c'] - S['pos']) * (0.02 * i), S['c'], 70, 18)
    gold, black = [1.0, 0.72, 0.32], [0.04, 0.03, 0.03]
    inv = i in (2, 5)
    return {'impact': {'bg': gold if inv else black, 'fg': black if inv else gold, 'accent': ['btrail', 'shock'],
                       'accent_col': [0.04, 0.03, 0.03] if inv else [1.0, 0.95, 0.85]}}


@shot('dust_old', 'THE HIT', 19)
def dv_hit(i, n):
    u = i / (n - 1)
    desert()
    tv_ = 0.1 + 1.5 * u ** 1.3
    K, V = m_dust_rigs(kclip=(DRAW, 0.75), kgun_in=False, vclip=('bx_30_knockdown_punch', tv_))
    revolver_in_hand(K)
    if u < 0.4:
        for j, (dt_, tr_) in enumerate(((0.06, 0.6), (0.12, 0.8))):
            rig('vg%d' % j, (DV.x, DV.y, 0), 180, {'clip': ('bx_30_knockdown_punch', max(0.0, tv_ - dt_))}, tr=tr_)
    c = br(V['UpperTorso'].translation)
    if i == 0:
        S['c'] = c
        Ve = peek_rig('v', (DV.x, DV.y, 0), 180, {'clip': ('bx_30_knockdown_punch', 1.6)})
        c0 = c
        pts = pts_of(V) + pts_of(Ve) + [c0 + Vector((2.2, 1.6, 1.8)), c0 + Vector((-2.2, 1.6, -1.6))]
        S['pos'], S['look'] = aim_lens(pts, 25, -8, 44, -6)
    c0 = S['c']
    k = 1 - (1 - u) ** 2.5   # the gold dust bursts out behind them and slows
    for j in range(16):
        a = 2 * math.pi * j / 16
        r = (0.9 + 0.5 * (j % 3)) * (0.4 + 0.6 * k)
        q = rb(c0 + Vector((math.cos(a) * 2.0 * k, 0.4 + (1.0 + abs(math.sin(a)) * 0.8) * k, math.sin(a) * 1.6 * k + 0.3 * u)))
        PROP_TR[0] = 0.5 * u
        prop('Ball', (r, r, r), CF(q.x, q.y, q.z), SAND if j % 2 else (1.0, 0.86, 0.55), 'Sand', 'dustburst')
        PROP_TR[0] = 0.0
    lens(S['pos'], S['look'], 44, -6)


@shot('dust_old', 'HOLSTER', 20)
def dv_holster(i, n):
    u = i / (n - 1)
    t = 0.75 - 0.69 * ease(u)       # the draw played backwards: the revolver goes home
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, t), kgun_in=t < DRAW_OUT, vclip=('bx_30_knockdown_punch', 1.6 + 0.3 * u))
    h = br(K['RightHand'].translation)
    if t >= DRAW_OUT:
        g = revolver_in_hand(K)
        if 0.1 < u < 0.55:          # the spin: a gold ring sweeping round the hand
            sweep = (u - 0.1) / 0.45
            ink_arc(h + Vector((0.1, 0.0, -0.1)), 0.85, 30 + 260 * sweep, 30 + 260 * sweep + 200, 0.08, 0.02, (1.0, 0.88, 0.6), n=16, tag='spin')
    if i == 0:
        Ke = peek_rig('k', (0, 0, 0), 0, {'clip': (DRAW, 0.06)})
        g0 = revolver_in_hand(Ke)
        GUNS.pop()
        m0 = br((g0 @ Vector((0, 0.2, -1.5, 1))).xyz)
        S['m'] = m0
        he = br(Ke['RightHand'].translation)
        pts = [br(Ke['Head'].translation) + Vector((0, 0, 0.9)), he + Vector((0, 0, -1.2)), m0 + Vector((0, 0, 1.4)), br(Ke['LeftHand'].translation)]
        S['pos'], S['c'] = aim_lens(pts, 145, 2, 36, 5, mx=0.8, my=0.64)
    # a curl of smoke rising and thinning from where the muzzle was
    for j, (dz, r) in enumerate(((0.3, 0.2), (0.75, 0.28), (1.25, 0.34))):
        PROP_TR[0] = min(0.9, 0.2 + 0.7 * u)
        puff(S['m'] + Vector((0.05 * j + 0.2 * u, 0.05, dz + 0.9 * u)), r * (1 + 0.6 * u))
        PROP_TR[0] = 0.0
    lens(lerpv(S['pos'], S['c'] + (S['pos'] - S['c']) * 0.88, ease(u)), S['c'], 36, 5)


@shot('dust', 'FAR SHOT', 48)
def dv_far(i, n):
    # the end, the owner's sketch: far and side-on. The shot rings out; the other one folds and goes down and stays
    # down, the dust bursts and clears; far off, the shooter puts the revolver home
    u = i / (n - 1)
    s_ = i / FPS
    desert()
    # (the owner: "a more natural fall - it sort of stiffens right at the end": the knockdown-punch take ends rigid; this
    # one, knocked out backwards, folds, drops and settles)
    tv_ = 1.7 + 1.0 * s_
    tk = 0.75 if s_ < 0.5 else max(0.06, 0.75 - 0.69 * ease((s_ - 0.5) / 0.8))
    K, V = m_dust_rigs(kclip=(DRAW, tk), kgun_in=tk < DRAW_OUT, vclip=('bx_29_knocked_out_back', tv_), vgun_in=False,
                       vdz=bounce(s_, 0.8))
    if tk >= DRAW_OUT:
        revolver_in_hand(K)
    if i == 0:
        S['vc'] = br(V['UpperTorso'].translation)
    vc = S['vc']
    rnd = random.Random(91)
    k = 1 - (1 - min(1.0, s_ / 0.6)) ** 2.5
    for j in range(16):
        a = rnd.uniform(0, 6.28)
        r0 = rnd.uniform(0.8, 2.2)
        d0 = rnd.uniform(0.3, 1.8)
        q = rb(vc + Vector((math.cos(a) * d0 * (0.3 + 0.9 * k + 0.6 * u), math.sin(a) * d0 * (0.3 + 0.9 * k + 0.6 * u),
                            -0.7 + 0.6 * u + rnd.uniform(0, 0.7))))
        PROP_TR[0] = min(0.97, 0.3 + 0.67 * u)
        rr = r0 * (0.5 + 0.7 * k + 0.5 * u)
        prop('Ball', (rr, rr, rr), CF(q.x, max(q.y, rr * 0.25), q.z), SAND if j % 2 else (0.95, 0.84, 0.62), 'Sand', 'dustcloud')
        PROP_TR[0] = 0.0
    lens((27.0 - 0.6 * u, DV.y / 2, 2.1), (0, DV.y / 2, 1.6), 33, 0)


def frame_data(info):
    return {'name': info.get('name', ''), 'impact': info.get('impact'), 'crop': info.get('crop', 0),
            'lens': {'cf': comps(CAMS['cf']), 'fov': CAMS['fov']},
            'rigs': [dict({'name': r['name'], 'col': r['col'], 'parts': {k: comps(v) for k, v in r['cf'].items()}},
                          **({'tr': r['tr']} if r.get('tr') else {})) for r in RIGS],
            'props': [dict({'shape': p['shape'], 'size': [round(x, 3) for x in p['size']], 'cf': comps(p['cf']), 'col': p['col'],
                            'mat': p['mat'], 'tag': p['tag']}, **({'tr': round(p['tr'], 2)} if p.get('tr') else {})) for p in PROPS],
            'katana': [comps(m) for m in KATANA], 'guns': [dict({'model': g['model'], 'cf': comps(g['cf'])}, **({'tr': g['tr']} if g.get('tr') else {})) for g in GUNS],
            'faces': {r['name']: r['face'] for r in RIGS if r.get('face')},
            # (for the game: which clip at what moment, where the root stands, where the katana is)
            'anim': {r['name']: dict({'clip': r['clip'][0], 't': round(r['clip'][1], 4), 'root': comps(r['cf']['HumanoidRootPart']),
                                      'sc': round(r.get('scatter', 0), 3)},
                                     **({'clip2': r['clip2'][0], 't2': round(r['clip2'][1], 4), 'w2': round(r['clip2'][2], 3)}
                                        if r.get('clip2') else {})) for r in RIGS if r.get('clip') and not r.get('tr')},
            # (the see-through afterimages too, for a runner that poses real bodies: their clip, moment and root)
            'ghost': {r['name']: {'clip': r['clip'][0], 't': round(r['clip'][1], 4), 'root': comps(r['cf']['HumanoidRootPart']),
                                  'tr': r['tr']} for r in RIGS if r.get('clip') and r.get('tr')},
            'kat': [kat_rel(m, mode) for m, mode in zip(KATANA, KAT_MODE)], 'katL': round(KAT_LEN[0], 3),
            'sem': dict(SEM)}


# ================================================================== TIDECREST v4 (20 Nov): the review's rebuild
# (notes finisher-boards/tidecrest-review.md: 4/10 for v3 - the pass didn't read as a hit, the run never closed the gap,
# the draw wasn't the gif, the ending lost the winner's face). The owner's words win; the review's shot list follows
# them, with the bought Katana Combat Pack for the whirl, the run, the dash-through cut and the death.
# One side of the line for every lens (the victim's side of the killer's lane): before the pass the killer travels
# left to right on screen, after it the winner stays screen-right and the victim screen-left (the owner's ending).
KPR = 'kp_readys_mainanimation_keyframesequence'          # the whirl into a crouched guard
KRUN = 'kp_runanimationset_forward_keyframesequence'      # the run (in place: the cut moves the root)
KDASH = 'kp_basicattacktypes_dashlight_keyframesequence'  # plant, dash-through cut (trail 0.17-0.30), follow-through
KDEATH = 'kp_death_actions_deathanimation_keyframesequence'
IDLE_W = 'id_06_dune_weight_shift'
LANE_X = -4.5      # the killer's lane, 4.5 studs off the victim: they never overlap on screen; the long blade spans it
RUN_V = 12.0       # studs/s
T4 = {}


def dash_slide(t):
    # the dash's travel along the lane (the clip plays in place): a short plant, 8 studs through the cut, a settle
    if t < 0.17:
        return -1.2 * (1 - t / 0.17)
    if t < 0.42:
        return 11.0 * (t - 0.17) / 0.25
    u = min(1.0, (t - 0.42) / 0.25)
    return 11.0 + 0.9 * (1 - (1 - u) ** 2)


def t4_fit():
    # where everything stands, solved from the clips: the lane offset so the dash's blade crosses the victim's belly,
    # the draw spot a run's length back, the guard's turn so its blade points at the victim's face, the blade's length
    if 'yp0' in T4:
        return T4
    old = KAT_LEN[0]
    KAT_LEN[0] = 8.0
    best = None
    for k in range(27):
        t = 0.17 + 0.13 * k / 26
        at = at_for(KDASH, t, (LANE_X, dash_slide(t)), 0)
        K = peek_rig('k', at, 0, {'clip': (KDASH, t)})
        g = pack_grip(K, KDASH, t)
        a, b = wpt(g, (0, 0, -0.6)), wpt(g, (0, 0, tipz()))
        if abs(b.x - a.x) < 1e-4:
            continue
        sv = (0.0 - a.x) / (b.x - a.x)
        if not 0.0 < sv < 1.0:
            continue
        q = a + (b - a) * sv
        sc_ = abs(q.z - 2.5)
        if best is None or sc_ < best[0]:
            best = (sc_, t, q)
    KAT_LEN[0] = old
    _, tc, q = best
    T4['tc'], T4['yp0'], T4['zc'] = tc, -q.y, q.z
    T4['y_end'] = T4['yp0'] + dash_slide(0.67)
    T4['end_cam'] = (LANE_X + 2.6, T4['y_end'] + 6.2, 2.9)
    spot = (LANE_X, T4['yp0'] - 1.2 - RUN_V * 30 / 24)
    T4['spot'] = spot
    face = Vector((0.0, 0.0, 4.4))
    d0 = face.xy - Vector(spot)
    yaw = -math.degrees(math.atan2(d0.x, d0.y))
    for _ in range(4):
        at = at_for(KPR, 0.0, spot, yaw)
        K = peek_rig('k', at, yaw, {'clip': (KPR, 0.95)})
        g = pack_grip(K, KPR, 0.95)
        a = wpt(g, (0, 0, 0))
        dv = wpt(g, (0, 0, -1)) - a
        want = face - a
        yaw -= math.degrees(math.atan2(want.x, want.y) - math.atan2(dv.x, dv.y))
    at = at_for(KPR, 0.0, spot, yaw)
    K = peek_rig('k', at, yaw, {'clip': (KPR, 0.95)})
    a = wpt(pack_grip(K, KPR, 0.95), (0, 0, 0))
    T4['yaw_g'] = yaw
    T4['L'] = max(4.0, ((face - a).length - 0.5 - 0.6) / 2.3)
    T4['Lf'] = min(T4['L'], 6.0)
    print('   t4 fit', {k_: (round(v, 3) if isinstance(v, float) else v) for k_, v in T4.items()}, flush=True)
    return T4


def dash_at(t):
    return at_for(KDASH, t, (LANE_X, t4_fit()['yp0'] + dash_slide(t)), 0)


def t4_stage(s_=None, view=None):
    stage()
    cyclorama()
    if view is not None:
        # (clear the pillars standing in a wide lens's way)
        a, b = Vector(view[0]), Vector(view[1])
        ab = b - a
        keep = []
        for pr in PROPS:
            if pr['tag'] == 'pillar':
                q = br(pr['cf'].translation)
                u = max(0.0, (Vector((q.x, q.y, 0)) - Vector((a.x, a.y, 0))).dot(Vector((ab.x, ab.y, 0))) / max(1e-6, Vector((ab.x, ab.y, 0)).length_squared))
                foot = Vector((a.x, a.y, 0)) + Vector((ab.x, ab.y, 0)) * u
                if (Vector((q.x, q.y, 0)) - foot).length < 14 + max(pr['size'][0], pr['size'][2]) / 2:
                    continue
            keep.append(pr)
        PROPS[:] = keep
    f = t4_fit()
    # the sun on the far ring behind the victim, on the ending lens's line through the winner (the manga's last panel)
    c = Vector(T4.get('end_cam', (LANE_X + 3.0, f['y_end'] + 7.0, 2.6)))
    w = Vector((0.6, 0.0, 3.0))
    d = (w - c).normalized()
    t = 0.0
    while (c + d * t).xy.length < 116:
        t += 0.5
    disc(tuple(c + d * t), tuple(c), 15, (1.0, 0.94, 0.8))
    tree((15.0, 13.0))
    tree((-15, -30), 5.8)
    tree((9.0, -18.0), 6.0)
    if s_ is None:
        petals((-2, 4, 3), 10, 4, seed=401)
    else:
        petals_drift((-2, 4, 3), 10, 4, s_, seed=401)


def t4_victim(clip, t, **kw):
    return rig('v', (0, 0, kw.pop('dz', 0.0)), 180, dict({'clip': (clip, t)}, **kw))


def iai_at():
    f = t4_fit()
    return at_for(DRAWC, 0.0, f['spot'], f['yaw_g'])


def readys_at():
    f = t4_fit()
    return at_for(KPR, 0.0, f['spot'], f['yaw_g'])


def front_of(a, d, hips):
    side = d.cross(Vector((0, 0, 1))).normalized()
    if side.dot(a - hips) < 0:
        side = -side
    return side


def ring_flash(c, n_lines, r0, r1, cam, seed=5, tag='smear', col=SMEAR):
    # action lines bursting out of a point, in the plane facing the lens (thin Neon slivers)
    fw = (Vector(cam) - c).normalized()
    ux = fw.cross(Vector((0, 0, 1)))
    ux = ux.normalized() if ux.length > 1e-3 else Vector((1, 0, 0))
    uy = ux.cross(fw).normalized()
    rnd = random.Random(seed)
    for j in range(n_lines):
        a = 2 * math.pi * j / n_lines + rnd.uniform(-0.12, 0.12)
        dv = ux * math.cos(a) + uy * math.sin(a)
        p0, p1 = c + dv * r0 * rnd.uniform(0.9, 1.2), c + dv * r1 * rnd.uniform(0.8, 1.15)
        prop_box_between(p0, p1, 0.02, 0.035, col, up_b=fw, mat='Neon', tag=tag)


@shot('tide', 'THE GRIP', 16)
def t4_grip(i, n):
    # [the owner's gif; Zenitsu's push] extreme close-up, square to the sword at hand height, a long lens, locked: the
    # guard between the hands; the thumb eases it out (6-8), a glint in the gap (9-10), a ring flash with action lines
    # bursting from the guard (11-13) and a bump; then it holds
    f = t4_fit()
    t4_stage(VT[0])
    K = rig('k', iai_at(), f['yaw_g'], {'clip': (DRAWC, t_grab())})
    t4_victim(LOOK, 0.0)
    SHEATH_LOCAL[0] = hands_sheath(K)
    a, b, d = sheath_line(K)
    sheath(K)
    SHEATH_LOCAL[0] = None
    push = 0.18 * ease(min(1.0, max(0.0, (i - 6) / 2)))
    KAT_LEN[0] = 1.0     # (home: what the scabbard holds doesn't show)
    SEM['kat'] = {'mode': 'home', 'push': round(push, 3)}
    katana_at_b(a - d * push, d)
    hips = br(K['LowerTorso'].translation)
    fr = front_of(a, d, hips)
    c = a + d * 0.45
    if i == 0:
        S['pos'] = c + fr * 4.6 + Vector((0, 0, 0.05))
    g = a - d * (push * 0.5) + Vector((0, 0, 0.14)) + fr * 0.12
    if 9 <= i <= 10:
        k_ = 1.6 if i == 10 else 0.9
        prop('Block', (0.04, 0.4 * k_, 0.04), CF(*rb(g)), (1.0, 0.98, 0.94), 'Neon', 'glint')
        prop('Block', (0.4 * k_, 0.04, 0.04), CF(*rb(g)), (1.0, 0.98, 0.94), 'Neon', 'glint')
    if 11 <= i <= 13:
        ring_flash(g, 11, 0.25 + 0.25 * (i - 11), 1.2 + 0.6 * (i - 11), S['pos'], seed=31 + i, tag='glint')
    bump = Vector((0, 0, 0.03)) if i == 11 else Vector((0, 0, 0))
    lens(S['pos'] + bump, c + bump, 24, 0)


@shot('tide', 'THE DRAW', 40)
def t4_draw(i, n):
    # [the gif; the round-2 board's ESTABLISH] low behind three-quarter over the sword hand's shoulder, the victim small
    # beyond. The whole two-hand take at about 0.7x (16-43), then a hold at full stretch with the blade STILL not out and
    # a glint running along it (44-51), then the tip pops free into the pack's whirl (52-55)
    f = t4_fit()
    t4_stage(VT[0])
    KAT_LEN[0] = f['L']
    if i <= 27:
        t = t_grab() + (DRAW_LEN - t_grab()) * i / 27
        K = rig('k', iai_at(), f['yaw_g'], {'clip': (DRAWC, t)})
    elif i <= 35:
        t = DRAW_LEN
        K = rig('k', iai_at(), f['yaw_g'], {'clip': (DRAWC, t)})
    else:
        w = (i - 35) / 4
        tr_ = 0.10 * w
        at = tuple(Vector(iai_at()).lerp(Vector(readys_at()), w))
        K = rig('k', at, f['yaw_g'], {'clip': (DRAWC, DRAW_LEN), 'clip2': (KPR, tr_, w)})
    t4_victim(LOOK, 1.2 * i / (n - 1))
    if i <= 35:
        fwd = 0.35 * min(1.0, max(0.0, (t - 0.5) / 0.43))
        SHEATH_LOCAL[0] = hands_sheath(K, fwd)
        a, b, d = sheath_line(K)
        sheath(K)
        SHEATH_LOCAL[0] = None
        kat_through(K, a, d)
        if 28 <= i <= 35:
            grip = wpt(hand_cf(K), (0, 0, 0))
            u = (i - 28) / 7
            gp = a.lerp(grip, u)
            prop('Block', (0.08, 0.08, 0.5), CF(*rb(gp)) @ ANG(0, 0, 45), (1.0, 0.98, 0.95), 'Neon', 'glint')
    else:
        SHEATH_LOCAL[0] = hands_sheath(K)
        sheath(K)
        SHEATH_LOCAL[0] = None
        katana_pack(K, KPR, 0.10 * (i - 35) / 4)
    if i == 0:
        Kp = peek_rig('k', iai_at(), f['yaw_g'], {'clip': (DRAWC, DRAW_LEN)})
        hd = br(Kp['Head'].translation)
        lt = Kp['LowerTorso']
        look = br((lt @ Vector((0, 0, -1, 0))).xyz)
        look = Vector((look.x, look.y, 0)).normalized()
        rt = Vector((look.y, -look.x, 0))
        hr, hl = wpt(hand_cf(Kp), (0, 0, 0)), br(Kp['LeftHand'].translation)
        mid = (hr + hl) / 2
        # over the sword hand's shoulder and above it: the blade lies across the front of the body, so a low back view
        # (the gif's) hides it - from up here it shows the whole way, the arms spreading, the victim small beyond
        # (from behind, even high, the body hides the blade: the take's draw stays low, unlike the gif's overhead arc. So
        # front three-quarter from the scabbard's side, a little above: the blade slides out between the spreading
        # arms the whole way; the wide reveal next sets the geography)
        S['pos'] = mid + look * 5.6 - rt * 3.4 + Vector((0, 0, 0.9))
        S['c'] = mid + rt * 0.5 + Vector((0, 0, 0.2))
    lens(S['pos'], S['c'], 54, 0)


@shot('tide', 'THE LENGTH', 26)
def t4_length(i, n):
    # [the owner's gag] wide, side-on, low, a long lens, locked: the giant blade whirls overhead in one arc (the pack's
    # own handle spin), settles into a crouched guard with its tip a hair from the victim's face, and holds while he
    # looks down the blade
    f = t4_fit()
    if i == 0:
        Ke = peek_rig('k', readys_at(), f['yaw_g'], {'clip': (KPR, 0.95)})
        KAT_LEN[0] = f['L']
        tip = wpt(pack_grip(Ke, KPR, 0.95), (0, 0, tipz()))
        Kw = peek_rig('k', readys_at(), f['yaw_g'], {'clip': (KPR, 0.25)})
        tipw = wpt(pack_grip(Kw, KPR, 0.25), (0, 0, tipz()))
        Vp = peek_rig('v', (0, 0, 0), 180, {'clip': (LOOK, 1.5)})
        pts = pts_of(Ke) + pts_of(Vp) + [tip, tipw]
        u_ = (Vector((0, 0)) - Vector(f['spot'])).normalized()
        pp = Vector((u_.y, -u_.x))
        if pp.x < 0:
            pp = -pp
        az = math.degrees(math.atan2(pp.x, -pp.y))
        S['pos'], S['c'] = aim_lens(pts, az, 3, 30, 0, mx=0.9, my=0.78, zmin=1.6)
    t4_stage(VT[0], view=(S['pos'], S['c']))
    KAT_LEN[0] = f['L']
    if i <= 7:
        t = 0.10 + 0.32 * i / 7
    elif i <= 17:
        t = 0.42 + 0.41 * (i - 8) / 9
    else:
        t = 0.83 + 0.27 * (i - 18) / 7
    K = rig('k', readys_at(), f['yaw_g'], {'clip': (KPR, t)})
    katana_pack(K, KPR, t)
    SHEATH_LOCAL[0] = hands_sheath(K)
    sheath(K)
    SHEATH_LOCAL[0] = None
    t4_victim(LOOK, 1.2 + 1.0 * i / (n - 1))
    if 0.3 <= t <= 0.66:
        blade_sweep(KPR, readys_at(), f['yaw_g'], max(0.18, t - 0.16), t, n=12)
    bump = Vector((0, 0, -0.06)) if i == 14 else Vector((0, 0, 0))
    lens(S['pos'] + bump, S['c'] + bump, 30, 0)


def kat_trail(K):
    # the blade trailing back and low from the right hand, its tip skimming the floor behind (a prop's angle, the body
    # stays the clip's)
    g = wpt(hand_cf(K), (0, 0, 0))
    lt = K['LowerTorso']
    look = br((lt @ Vector((0, 0, -1, 0))).xyz)
    look = Vector((look.x, look.y, 0)).normalized()
    dirv = (-look * 0.93 + Vector((0, 0, -0.36))).normalized()
    SEM['kat'] = {'mode': 'trail'}
    katana_at_b(g + dirv * 0.44, dirv)


def run_y(sec):
    return t4_fit()['spot'][1] + RUN_V * sec


@shot('tide', 'THE CHARGE', 22)
def t4_charge(i, n):
    # [the board's run-up; the owner: no teleport] side-on at blade height from the victim's side, trucking a little
    # slower than the runner: he gains across the frame, the victim already in it ahead and growing
    f = t4_fit()
    t4_stage(VT[0])
    KAT_LEN[0] = f['Lf']
    sec = i / FPS
    y = run_y(sec)
    K = rig('k', at_for(KRUN, sec, (LANE_X, y), 0), 0, {'clip': (KRUN, sec)})
    kat_trail(K)
    kick_dust(K, VT[0])
    t4_victim(LOOK, 2.2)
    cy = run_y(0) + 3.0 + RUN_V * 0.78 * sec
    lens(Vector((LANE_X + 9.5, cy - 4.0, 2.0)), Vector((LANE_X + 0.5, cy + 3.5, 1.9)), 50, 0)


@shot('tide', 'CLOSING', 14)
def t4_closing(i, n):
    # [the board's closing; "cool perspective"] on the floor just behind the victim's feet, looking up the lane: the
    # killer grows from a quarter to two thirds of the frame; the lens punches wider; the run's last strides, then the
    # dash's plant
    f = t4_fit()
    t4_stage(VT[0])
    KAT_LEN[0] = f['Lf']
    if i <= 7:
        sec = (22 + i) / FPS
        K = rig('k', at_for(KRUN, sec, (LANE_X, run_y(sec)), 0), 0, {'clip': (KRUN, sec)})
        kat_trail(K)
    else:
        t = 0.17 * (i - 8) / 5
        K = rig('k', dash_at(t), 0, {'clip': (KDASH, t)})
        katana_pack(K, KDASH, t)
    kick_dust(K, VT[0])
    t4_victim('bx_18_block_high_center', 0.10 * max(0.0, (i - 6) / 7))
    hk = br(K['UpperTorso'].translation)
    u = i / (n - 1)
    fov = 60 + 25 * (u ** 2.2)
    lens(Vector((-2.3, 2.9, 0.5)), hk + Vector((0, 0, -0.2)), fov, 11)


def pass_lens():
    if 'pass_cam' not in T4:
        f = t4_fit()
        c = Vector((LANE_X * 0.5, 0.0, 2.3))
        T4['pass_c'] = c
        T4['pass_cam'] = Vector((-3.0, 10.5, 1.2))
    return T4['pass_cam'], T4['pass_c']


@shot('tide', 'THE PASS', 9)
def t4_pass(i, n):
    # [manga panel 1; Zenitsu's 3-frame strike] low, ahead of the victim on his side of the lane: the killer comes at us
    # and cuts through in 9 frames; the smear follows the blade's real path across the belly; ink afterimages; a whip pan
    f = t4_fit()
    t4_stage(VT[0])
    KAT_LEN[0] = f['Lf']
    t = 0.17 + 0.25 * i / (n - 1)
    K = rig('k', dash_at(t), 0, {'clip': (KDASH, t)})
    katana_pack(K, KDASH, t)
    for j, (dt_, tr_) in enumerate(((0.04, 0.45), (0.08, 0.62), (0.12, 0.78))):
        if t - dt_ >= 0.12:
            rig('kg%d' % j, dash_at(t - dt_), 0, {'clip': (KDASH, t - dt_)}, col=(0.16, 0.12, 0.2), tr=tr_)
    if t > 0.18:
        blade_sweep(KDASH, dash_at, 0, 0.17, min(t, 0.31), n=max(3, int(14 * (min(t, 0.31) - 0.17) / 0.14)))
    kick_dust(K, VT[0])
    t4_victim('bx_18_block_high_center', 0.10 + 0.20 * i / (n - 1))
    pos, c = pass_lens()
    pan = Vector((0, 0, 0))
    if 2 <= i <= 5:
        pan = Vector((-0.5, 0, 0)) * ((i - 2) / 3)
    elif i > 5:
        pan = Vector((-0.5, 0, 0))
    lens(pos, c + pan, 50, 0)


@shot('tide', 'CUT FRAME', 6)
def t4_cut(i, n):
    # [the owner: longer than 1 frame, same perspective; Kenshin 2023] the pass's lens punched in on the contact, the
    # bodies apart: two-tone, the inverse on 2 and 5, action lines bursting from the contact on 3-4
    f = t4_fit()
    t4_stage(VT[0])
    KAT_LEN[0] = f['Lf']
    t = f['tc']
    K = rig('k', dash_at(t), 0, {'clip': (KDASH, t)})
    katana_pack(K, KDASH, t)
    t4_victim('bx_18_block_high_center', 0.25)
    blade_sweep(KDASH, dash_at, 0, 0.17, t + 0.02, n=14)
    pos, c = pass_lens()
    cc = Vector((0.0, 0.0, f['zc']))
    p2 = cc + (pos - cc) / 1.5
    if 3 <= i <= 4:
        ring_flash(cc, 14, 0.6, 3.2 + 0.6 * (i - 3), p2, seed=70 + i)
        splats(cc + Vector((0.3, 0.6, 0)), 3, 0.8, seed=80 + i, size=0.8)
    lens(p2, cc, 50, 5)
    if i in (2, 5):
        return {'impact': dict(IMPACT_TIDE, bg=IMPACT_TIDE['fg'], fg=IMPACT_TIDE['bg'])}
    return {'impact': IMPACT_TIDE}


@shot('tide', 'PAST HIM', 16)
def t4_past(i, n):
    # [manga panel 2, mirrored; Sanjuro's frozen wide] in front of the killer, low, a long lens, static: the winner
    # crouched in the follow-through, arms wide, the blade out, foreground right; the victim 6-8 studs behind, facing
    # away, frozen in a guard that came too late
    f = t4_fit()
    t4_stage(VT[0])
    KAT_LEN[0] = f['Lf']
    t = 0.42 + 0.25 * i / (n - 1)
    K = rig('k', dash_at(t), 0, {'clip': (KDASH, t)})
    katana_pack(K, KDASH, t)
    V = t4_victim('bx_18_block_high_center', 0.30 + 0.05 * i / (n - 1))
    if i == 0:
        Ke = peek_rig('k', dash_at(0.67), 0, {'clip': (KDASH, 0.67)})
        pts = pts_of(Ke) + pts_of(V)
        S['pos'], S['c'] = aim_lens(pts, 160, 4, 27, 0, mx=0.82, my=0.7, zmin=1.4)
    lens(S['pos'], S['c'], 27, 0)


@shot('tide', 'STILLNESS', 20)
def t4_still(i, n):
    # [the board; Zenitsu's face hold] close on the victim's face from his front-right, a slow push; the winner soft far
    # behind on the right; one petal crosses the face
    f = t4_fit()
    s_ = i / FPS
    t4_stage(VT[0])
    KAT_LEN[0] = f['Lf']
    K = rig('k', dash_at(0.67), 0, {'clip': (KDASH, 0.67)})
    katana_pack(K, KDASH, 0.67)
    V = t4_victim(LOOK, 0.95 + 0.8 * i / (n - 1), face={'LeftUpperLidRaiser': 0.8, 'RightUpperLidRaiser': 0.8})
    hp = br(V['Head'].translation)
    if i == 0:
        S['hp0'] = hp
    hp0 = S['hp0']
    petals_drift(hp0 + Vector((1.2, -0.9, 0.6)), 1, 0.05, s_, seed=433, vel=(-1.6, 0.2, -0.5))
    pos = lerpv(hp0 + Vector((3.4, -1.95, 0.05)), hp0 + Vector((3.23, -1.85, 0.05)), ease(i / (n - 1)))
    lens(pos, hp0 + Vector((0.0, 0.0, -0.05)), 32, 0)


def sheathe4_at():
    f = t4_fit()
    return at_for(DRAWC, IAI_OUT, (LANE_X, f['y_end']), 0)


@shot('tide', 'THE SHEATHE', 26)
def t4_sheathe(i, n):
    # [Kenshin's re-sheathe; Zoro's] extreme close-up, low, broadside, locked on the scabbard's mouth: the long blade
    # slides home slowing (0-15), the click (16) with a glint and a bump, then a held beat
    f = t4_fit()
    t4_stage(VT[0])
    CLICK = 16
    w = min(1.0, i / CLICK)
    t = IAI_OUT - (IAI_OUT - t_grab()) * (1 - (1 - w) ** 2.2)
    KAT_LEN[0] = f['L']
    K = rig('k', sheathe4_at(), 0, {'clip': (DRAWC, t)})
    SHEATH_LOCAL[0] = hands_sheath(K)
    a, b, d = sheath_line(K)
    sheath(K)
    SHEATH_LOCAL[0] = None
    if i >= CLICK:
        KAT_LEN[0] = 1.0
        SEM['kat'] = {'mode': 'home', 'push': 0.0}
        katana_at_b(a, d)
    else:
        kat_through(K, a, d)
    t4_victim('bx_18_block_high_center', 0.35)
    hips = br(K['LowerTorso'].translation)
    fr = front_of(a, d, hips)
    c = a - d * 0.5
    if i == CLICK:
        g = a + Vector((0, 0, 0.16)) + fr * 0.12
        prop('Block', (0.04, 0.5, 0.04), CF(*rb(g)), (1.0, 0.98, 0.94), 'Neon', 'glint')
        prop('Block', (0.5, 0.04, 0.04), CF(*rb(g)), (1.0, 0.98, 0.94), 'Neon', 'glint')
    bump = Vector((0, 0, 0.025)) if i == CLICK else Vector((0, 0, 0))
    lens(c + fr * 2.8 + Vector((0, 0, -0.55)) + bump, c + Vector((0, 0, 0.05)) + bump, 38, 0)


@shot('tide', 'THE CUT LANDS', 14)
def t4_cutlands(i, n):
    # [the board's delayed cut; Zenitsu's line] the victim alone, front three-quarter, belly in the middle: two-tone for
    # 2 frames, the ink stroke wipes across the belly in the swing's direction, splats burst, the stroke fades
    s_ = i / FPS
    t4_stage(VT[0])
    V = t4_victim('bx_27_hit_stomach', 0.05 + 0.55 * i / (n - 1))
    if i == 0:
        S['c'] = br(V['UpperTorso'].translation) + Vector((0, 0, -0.55))
    c = S['c']
    cam = c + Vector((3.4, -4.6, 0.5))
    fw = (cam - c).normalized()
    side = fw.cross(Vector((0, 0, 1))).normalized()
    wipe = min(1.0, max(0.0, (i - 1) / 3))
    if wipe > 0:
        PROP_TR[0] = 0.0 if i < 8 else min(0.85, (i - 8) * 0.13)
        a0, a1 = c - side * 2.1 + Vector((0, 0, 0.4)) + fw * 1.7, c + side * 2.1 + Vector((0, 0, -0.3)) + fw * 1.7
        brush(a0, a0.lerp(a1, wipe), 0.22, 0.62, fw, INK, seed=61)
        brush(a0 + Vector((0, 0, -0.05)), (a0 + Vector((0, 0, -0.05))).lerp(a1 + Vector((0, 0, -0.05)), wipe), 0.2, 0.14, fw,
              SKIN, seed=62, tag='stroke_edge')
        PROP_TR[0] = 0.0
    if i >= 4:
        burst(c + fw * 0.9, 10, 2.0, (i - 4) / 10, seed=71, kind='splat', size=0.7)
    lens(cam, c + Vector((0, 0, 0.15)), 40, 0)
    if i < 2:
        return {'impact': STROKE_HIT}


@shot('tide', 'THE END', 34)
def t4_end(i, n):
    # [the owner: "close up of you on the right with enemy in the background on the ground"; manga panel 3] the winner
    # on the right third, face in frame, a real idle, the katana home at the hip; behind on the left the cut one
    # crumples, hits the ground, bounces and rolls to rest (the pack's death), then comes apart into petals
    f = t4_fit()
    s_ = i / FPS
    t4_stage(VT[0])
    yaw_e = T4.get('yaw_end', -22.0)
    K = rig('k', at_for(IDLE_W, 0.0, (LANE_X, f['y_end']), yaw_e), yaw_e, {'clip': (IDLE_W, 0.4 + s_)})
    sheath(K)
    KAT_LEN[0] = 1.0
    a, b, d = sheath_line(K)
    katana_at_b(a, d)
    if i < 3:
        V = t4_victim('bx_27_hit_stomach', 0.60, clip2=(KDEATH, 0.05, (i + 1) / 3))
    else:
        td = 0.05 + (i - 3) / FPS
        land = 0.42
        V = t4_victim(KDEATH, min(1.33, td), dz=bounce(td, land, h=0.3),
                      scatter=0.5 * ease((i - 22) / 11) if i > 22 else 0.0)
    if i >= 15:
        vb = br(V['UpperTorso'].translation)
        burst(vb + Vector((0, 0, 0.3)), 70, 2.8, (i - 15) / (n - 16), seed=421, size=1.1, fall=0.5)
    if i == 0:
        hd = br(K['Head'].translation)
        to_cam = (Vector(T4['end_cam']).xy - hd.xy).normalized().to_3d()
        to_v = (Vector((0.0, 0.0)) - hd.xy).normalized().to_3d()
        cam = hd + to_cam * 4.6 + Vector((0, 0, -0.55))
        S['cam'], S['look'] = cam, hd + Vector((0.0, 0.0, -0.45)) + to_v * 1.7
    cam, look = S['cam'], S['look']
    lens(lerpv(cam, look + (cam - look) * 0.97, ease(i / (n - 1))), look, 36, 0)



def cf_look(a, b):
    z = -(Vector(b) - Vector(a)).normalized()
    upv = Vector((0, 1, 0)) if abs(z.y) < 0.98 else Vector((1, 0, 0))
    x = upv.cross(z).normalized()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(a)
    return m


# what a close lens follows on a real body (else it stays where it is in the world)
LENS_ANCHOR = {
    ('tide', 'THE GRIP'): 'mouth', ('tide', 'THE DRAW'): 'k.UpperTorso', ('tide', 'THE SHEATHE'): 'mouth',
    ('tide', 'STILLNESS'): 'v.Head', ('tide', 'THE END'): 'k.Head', ('tide', 'THE CUT LANDS'): 'v.UpperTorso',
    ('dust', "KILLER'S EYES"): 'k.Head', ('dust', "VICTIM'S EYES"): 'v.Head', ('dust', 'EYES AGAIN'): 'k.Head',
    ('dust', 'THEIR EYES'): 'v.Head', ('dust', "KILLER'S HAND"): 'k.LowerTorso', ('dust', "VICTIM'S HAND"): 'v.LowerTorso',
    ('dust', 'ENEMY REACHES'): 'v.LowerTorso', ('dust', 'THE DRAW'): 'k.LowerTorso',
}


def kat_rel(m, mode):
    if mode == 'hand':
        return {'mode': 'hand'}
    k = next((r for r in RIGS if r['name'] == 'k'), None)
    if not k:
        return {'mode': 'world', 'cf': comps(m)}
    return {'mode': 'lt', 'rel': comps(k['cf']['LowerTorso'].inverted() @ m)}


# ------------------------------------------------------------------ run
if VIDS:
    RW, RH = int(os.environ.get('FIN_VW', 640)), int(os.environ.get('FIN_VH', 360))
setup()
for vname in VIDS:
    vdir = os.path.join(OUT, 'video_' + vname)
    os.makedirs(vdir, exist_ok=True)
    allv, shots, k = {}, [], 0
    for sname, nf, fn in VIDEO[vname]:
        S.clear() if sname not in ('CUT FRAME', 'HIT FRAME') else None
        for i in range(nf):
            VT[0] = k / FPS
            clear()
            RIGS.clear(); PROPS.clear(); KATANA.clear(); GUNS.clear(); KAT_MODE.clear(); KAT_LEN[0] = 1.0
            SEM.clear()
            info = fn(i, nf) or {}
            info['name'] = sname
            if (vname, sname) in LENS_ANCHOR:
                SEM['lens'] = LENS_ANCHOR[(vname, sname)]
            if not os.environ.get('FIN_NOPNG'):
                draw_preview()
                sc.render.filepath = os.path.join(vdir, f'{k:03d}.png')
                bpy.ops.render.render(write_still=True)
            allv[f'v{k:03d}'] = frame_data(info)
            k += 1
        shots.append([sname, nf])
        print('shot', vname, sname, nf, flush=True)
    # the fixed set (floor, pillars, trees) is the same in every frame: stored once as '_stage'
    STATIC = ('floor', 'pillar', 'tree', 'rock', 'cactus', 'fence', 'mesa', 'sky', 'ground', 'rut', 'print')
    first = None
    for key in sorted(allv):
        f = allv[key]
        st = [p for p in f['props'] if p['tag'] in STATIC]
        if first is None:
            first = st
        if st == first:
            f['props'] = [p for p in f['props'] if p['tag'] not in STATIC]
            f['stage'] = True
    allv['_stage'] = {'props': first or []}
    with open(os.path.join(vdir, 'frames.json'), 'w') as fh:
        json.dump(allv, fh, separators=(',', ':'))
    with open(os.path.join(vdir, 'shots.json'), 'w') as fh:
        json.dump({'fps': FPS, 'shots': shots}, fh)
    print('video', vname, k, 'frames', flush=True)
if VIDS:
    sys.exit(0)
for sh_ in SHEETS:
    _, cn, n = sh_.split(':')
    n = int(n)
    L = clip_len(cn)
    for i in range(n):
        t = L * i / max(1, n - 1)
        clear()
        RIGS.clear(); PROPS.clear(); KATANA.clear(); GUNS.clear()
        prop('Block', (60, 1, 60), CF(0, -0.5, 0), FLOORC, 'SmoothPlastic', 'floor')
        K = rig('k', (0, 0, 0), 0, {'clip': (cn, t)}, ground=False)
        if pack_grip(K, cn, t) is not None:
            katana_pack(K, cn, t)     # (a pack clip: its own sword track)
        draw_preview()
        aim_lens(pts_of(K), 35, 8, 40, 0, mx=0.7, my=0.75)
        sc.render.filepath = os.path.join(OUT, f'sheet_{cn}_{i:02d}.png')
        bpy.ops.render.render(write_still=True)
    print('sheet', cn, n, round(L, 2), flush=True)
for board, frames in BOARDS.items():
    if ONLY and board not in ONLY:
        continue
    for n in sorted(frames):
        if ONLY.get(board) and n not in ONLY[board]:
            continue
        clear()
        RIGS.clear(); PROPS.clear(); KATANA.clear(); GUNS.clear()
        info = frames[n]()
        draw_preview()
        sc.render.filepath = os.path.join(OUT, f'{board}_{n}.png')
        bpy.ops.render.render(write_still=True)
        data = {'name': info['name'], 'impact': info.get('impact'), 'crop': info.get('crop', 0), 'lens': {'cf': comps(CAMS['cf']), 'fov': CAMS['fov']},
                'rigs': [dict({'name': r['name'], 'col': r['col'], 'parts': {k: comps(v) for k, v in r['cf'].items()}},
                          **({'tr': r['tr']} if r.get('tr') else {})) for r in RIGS],
                'props': [{'shape': p['shape'], 'size': [round(x, 3) for x in p['size']], 'cf': comps(p['cf']), 'col': p['col'], 'mat': p['mat'], 'tag': p['tag']} for p in PROPS],
                'katana': [comps(m) for m in KATANA], 'guns': [dict({'model': g['model'], 'cf': comps(g['cf'])}, **({'tr': g['tr']} if g.get('tr') else {})) for g in GUNS],
                'faces': {r['name']: r['face'] for r in RIGS if r.get('face')}}
        with open(os.path.join(OUT, f'{board}_{n}.json'), 'w') as fh:
            json.dump(data, fh)
        print('frame', board, n, len(PROPS), 'props', flush=True)
allf = {}
for f in sorted(os.listdir(OUT)):
    if f.endswith('.json') and not f.startswith('all'):
        allf[f[:-5]] = json.load(open(os.path.join(OUT, f)))
with open(os.path.join(OUT, 'all_frames.json'), 'w') as fh:
    json.dump(allf, fh)
print('done', len(allf))
