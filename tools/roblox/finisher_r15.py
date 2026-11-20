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


LOOPS = {'mx_ninja_run'}


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


def clip_pose_raw(name, t):
    kfs = clip(name)
    t = max(kfs[0][0], min(kfs[-1][0], t))
    i = 0
    while i < len(kfs) - 2 and kfs[i + 1][0] <= t:
        i += 1
    (t0, a), (t1, b) = kfs[i], kfs[min(i + 1, len(kfs) - 1)]
    u = 0 if t1 <= t0 else (t - t0) / (t1 - t0)
    out = {}
    for part in a:
        ma, mb = a[part], b.get(part, a[part])
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
        for part, m in clip_pose(cn, ct).items():
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
                 'clip': pose.get('clip'), 'scatter': sc_, 'root0': root, 'tr': tr})
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


def sheath_line(cf):
    lt = cf['LowerTorso']
    mouth = lt @ Vector((-0.95, 0.1, -0.75, 1))
    tipp = lt @ Vector((-1.25, -1.6, 2.2, 1))
    a, b = br(mouth.xyz), br(tipp.xyz)
    return a, b, (b - a).normalized()


def sheath(cf):
    # the scabbard at the left hip, mouth forward and up, running back and down (Roblox axes of the lower torso)
    a, b, _ = sheath_line(cf)
    prop_box_between(a, b, 0.22, 0.34, LACQUER, tag='sheath')
    d = (b - a).normalized()
    prop_box_between(a + d * 0.3, a + d * 0.5, 0.26, 0.38, SKIN, tag='sheath')
    prop_box_between(b - d * 0.25, b, 0.26, 0.38, GOLD, tag='sheath')
    return a, d


KAT_LEN = [1.0]   # the blade's length, x the normal (set per frame; 1 = the skin as it is)


def tipz():
    # the blade tip along the grip's -Z (studs, the x3 skin) for the current length
    return -(0.6 + 2.3 * KAT_LEN[0])


def katana_grip(m):
    KATANA.append(m)
    KAT_MODE.append('hand')


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
def revolver_in_hand(cf, tr=0.0):
    # the barrel runs on from the forearm, the gun's top toward the back of the hand; the grip sits in the palm
    g = cf['RightHand'] @ CF(0, -0.1, 0) @ ANG(-90, 0, 0) @ CF(0, 0.55, -0.25)
    GUNS.append({'model': 'revolver_dust', 'cf': g, 'tr': tr})
    return g


def holster(cf, gun_in=True):
    lt = cf['LowerTorso']
    h = lt @ CF(1.12, -0.45, -0.05)
    prop('Block', (0.32, 0.95, 0.55), h, (0.42, 0.27, 0.16), 'Leather', 'holster')
    prop('Block', (2.12, 0.28, 1.1), lt @ CF(0, 0.05, 0), (0.42, 0.27, 0.16), 'Leather', 'belt')
    if gun_in:
        GUNS.append({'model': 'revolver_dust', 'cf': h @ CF(0, 0.15, 0) @ ANG(-90, 0, 0) @ CF(0, 0, -0.1)})
    return h


SAND = (0.86, 0.75, 0.57)
ROCK = (0.72, 0.49, 0.35)
CACTUS = (0.42, 0.52, 0.38)


def desert():
    prop('Block', (500, 1, 500), CF(0, -0.5, 0), SAND, 'Sand', 'floor')
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
                                     (0.58, 0.5, 0.66), (0.46, 0.44, 0.62)), h=40.0):
    # a ring of painted sky round the set (Neon: lit the same from every side), warm at the horizon, dusk above; so the
    # sunset of the opening holds through every shot whichever way the lens looks (v1 swung to a blue sky at the clash)
    w = 2 * math.pi * r / n * 1.04
    for i in range(n):
        a = 2 * math.pi * i / n
        x, z = math.cos(a) * r, math.sin(a) * r
        yaw = math.degrees(math.atan2(x, z))
        for j, col in enumerate(bands):
            prop('Block', (w, h, 1.0), CF(x, h / 2 + j * h, z) @ ANG(0, yaw, 0), col, 'Neon', 'sky')
    # the lid (a low lens looking up sees dusk, not the map's sky); none of it casts a shadow (Studio and the game skip
    # shadows on 'sky')
    prop('Block', (2.2 * r, 1.0, 2.2 * r), CF(0, h * len(bands) + 0.5, 0), (0.42, 0.41, 0.6), 'Neon', 'sky')


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
    # an ink-brush smear along the blade's real path between t0 and t1 (the katana in the right hand of the clip)
    pts = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        p = rb((at[0], at[1], 0))
        root = CF(p.x, 3.0, p.z) @ ANG(0, yaw, 0)
        cf = solve(root, {'clip': (cn, t)})
        g = hand_cf(cf)
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


def m_dust_rigs(kclip=(DRAW, IDLE_T), vclip=(DRAW, IDLE_T), kgun_in=True, kface=None, vface=None):
    K = rig('k', (0, 0, 0), 0, {'clip': kclip, 'face': kface if kface is not None else SQUINT})
    holster(K, kgun_in)
    V = rig('v', (DV.x, DV.y, 0), 180, {'clip': vclip, 'face': vface if vface is not None else WIDE})
    holster(V, True)
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
DRAWC = 'mx_draw_a'         # Mixamo "Draw Sword 1": the hand goes to the hilt at the left hip and pulls it out
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
    if v.length < 0.2:
        KAT_LEN[0] = 1.0
        katana_at_b(a, d)
        return
    dirv = v.normalized()
    KAT_LEN[0] = max(1.0, (v.length + 3.0 - 0.6) / 2.3)
    katana_at_b(grip + dirv * 0.44, dirv)


def t_grab():
    # the moment the draw clip's hand is on the hilt (closest to the scabbard's mouth)
    if 'tg' not in S_FIX:
        P = run_places()
        best = (9e9, 0.0)
        for k in range(26):
            t = 0.5 * k / 25
            Kp = peek_rig('k', P['draw_at'], 0, {'clip': (DRAWC, t)})
            a, b, d = sheath_line(Kp)
            e = (wpt(hand_cf(Kp), (0, 0, 0)) - (a - d * 0.5)).length
            if e < best[0]:
                best = (e, t)
        S_FIX['tg'] = best[1]
    return S_FIX['tg']


@shot('tide', 'THE DRAW', 14)
def tv_draw(i, n):
    # the owner (20 Nov): the sword has to be UNSHEATHED, not just appear. The hand goes to the hilt and pulls; the
    # blade comes out of the scabbard's mouth behind it
    u = i / (n - 1)
    P = run_places()
    tide_stage(VT[0])
    t = 0.5 * u
    K = rig('k', P['draw_at'], 0, {'clip': (DRAWC, t)})
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.0)})
    a, b, d = sheath_line(K)
    sheath(K)
    if t < t_grab():
        katana_at_b(a, d)
    else:
        kat_through(K, a, d)
    if i == 0:
        hips = br(K['LowerTorso'].translation)
        S['pos'], S['c'] = hips + Vector((-3.0, 3.6, 0.9)), a + Vector((0.4, 0.6, 0.55))
    lens(S['pos'], S['c'], 48, -6)


@shot('tide', 'IT KEEPS COMING', 14)
def tv_coming(i, n):
    # the gag (the katana grows with kills): tight on the scabbard's mouth, the blade keeps coming out, faster and faster,
    # long after any blade should have ended (the hand is out of the shot)
    u = i / (n - 1)
    P = run_places()
    tide_stage(VT[0])
    K = rig('k', P['draw_at'], 0, {'clip': (DRAWC, 0.5)})
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.05)})
    a, b, d = sheath_line(K)
    sheath(K)
    e = 1.2 + (2.3 * LONG_KAT + 0.6 - 3.0 - 1.2) * (u ** 1.6)
    KAT_LEN[0] = max(1.0, (e + 3.0 - 0.6) / 2.3)
    katana_at_b(a - d * e, d)
    if i == 0:
        hips = br(K['LowerTorso'].translation)
        out = Vector(((a - hips).x, (a - hips).y, 0)).normalized()
        S['a'], S['d'], S['out'] = a, d, out
    a, d, out = S['a'], S['d'], S['out']
    lens(a + out * 1.9 + Vector((0, 0, 0.45)) + d * 0.6, a - d * 2.2, 50, 8)


@shot('tide', 'THE LENGTH', 14)
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


@shot('tide', 'RUN-UP', 30)
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
        pos, c = aim_lens(pts_of(Km) + [wpt(hand_cf(Km), (0, 0, tipz() * 0.6))], 298, -10, 74, 16, mx=0.62, my=0.66, zmin=0.35)
        S['off'], S['coff'], S['z'], S['cz'] = pos - hm, c - hm, pos.z, c.z
    pos, c = h + S['off'], h + S['coff']
    pos.z, c.z = S['z'], S['cz']
    kick_dust(K, VT[0])
    lens(pos, c, 74, 16)


@shot('tide', 'CLOSING', 12)
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


@shot('tide', 'THE PASS', 11)
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
    lens(S['pos'], S['c'], 64, 7 + 3 * u)


@shot('tide', 'CUT FRAME', 3)
def tv_cutframe(i, n):
    KAT_LEN[0] = LONG_KAT
    tide_stage(VT[0])
    tv_k(K_START, T_HIT)
    rig('v', (0, 0, 0), 180, {'clip': ('bx_18_block_high_center', 0.35)})
    blade_sweep(SLASH, K_START, 0, T_HIT - 0.35, T_HIT, n=16)
    # (the hit holds 3 frames; the lens bumps along the cut)
    lens(S['pos'] + Vector((0, 0.08 * (i + 1), 0)), S['pass_look'], 64, 10)
    return {'impact': IMPACT_TIDE}


@shot('tide', 'BACK TO BACK', 12)
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
        S['m'] = (kc + vc) / 2
        S['pos0'] = S['m'] + Vector((-1.6, 9.5, -0.9))
    lens(lerpv(S['pos0'], S['m'] + (S['pos0'] - S['m']) * 0.88, ease(u)), S['m'] + Vector((0, 0, 0.1)), 46, 4)


@shot('tide_old', 'STILLNESS', 12)
def tv_still(i, n):
    u = i / (n - 1)
    s = i / FPS
    tide_stage(VT[0])
    K = tv_k(K_START, K_END_T)
    V = rig('v', (0, 0, 0), 180, {'clip': (LOOK, 0.95 + s), 'face': {'LeftUpperLidRaiser': 0.8, 'RightUpperLidRaiser': 0.8}})
    hp = br(V['Head'].translation)
    if i == 0:
        S['hp0'], S['kp0'] = hp, br(K['Head'].translation)
    hp0, kp0 = S['hp0'], S['kp0']
    petals_drift(hp0 + Vector((0.5, -1.6, 0.3)), 9, 1.6, s, seed=411, vel=(0.5, -0.2, -0.3))
    pos = lerpv(hp0 + Vector((2.2, -6.2, -0.3)), hp0 + Vector((1.8, -5.0, -0.25)), ease(u))
    lens(pos, (hp * 0.5 + hp0 * 0.5) * 0.8 + kp0 * 0.2 + Vector((0, 0, -0.8)), 40, 0)


@shot('tide_old', 'THE SHEATHE', 14)
def tv_sheathe(i, n):
    u = i / (n - 1)
    tide_stage(VT[0])
    at = at_for(SHEATHE, 1.0, K_BACK, 0)
    K = rig('k', at, 0, {'clip': (SHEATHE, 1.0 + 0.4 * u)})
    a, b, d = sheath_line(K)
    sheath(K)
    katana_at_b(a - d * (1.5 * (1 - ease(u))), d)   # the last inches slide home; the guard meets the mouth at the end
    rig('v', (0, 0, 0), 180, {'clip': (LOOK, 1.85 + i / FPS)})
    if i == 0:
        Ke = peek_rig('k', at, 0, {'clip': (SHEATHE, 1.4)})
        a2, b2, d2 = sheath_line(Ke)
        hp = br(Ke['Head'].translation)
        pts = [hp + Vector((0, 0, 0.6)), a2 - d2 * 1.2, a2 + d2 * 2.0, br(Ke['RightHand'].translation), br(Ke['LeftHand'].translation)]
        S['pos'], S['c'] = aim_lens(pts, 212, 8, 40, 6, mx=0.8, my=0.66)
    lens(lerpv(S['pos'], S['c'] + (S['pos'] - S['c']) * 0.9, ease(u)), S['c'], 40, 6)


@shot('tide_old', 'THE CUT LANDS', 12)
def tv_cutlands(i, n):
    s = i / FPS
    tide_stage(VT[0])
    K = rig('k', at_for(SHEATHE, 1.0, K_BACK, 0), 0, {'clip': (SHEATHE, min(2.8, 2.35 + s))})
    a, b, d = sheath_line(K)
    sheath(K)
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


@shot('tide', 'THE END', 40)
def tv_end(i, n):
    # close on the winner, on the right of the frame; the one they cut stands behind, on the left. The long blade slides
    # home (the last of it; the scabbard swallows the rest); on the click the cut shows across their belly, they fold and
    # go down, and come apart into petals on the ground
    u = i / (n - 1)
    s_ = i / FPS
    CLICK = 16
    tide_stage(VT[0])
    at = at_for(SHEATHE, 1.0, K_BACK, 0)
    K = rig('k', at, 0, {'clip': (SHEATHE, 1.0 + 0.4 * min(1.0, i / CLICK) if i <= CLICK else min(2.8, 1.4 + (i - CLICK) / FPS))})
    a, b, d = sheath_line(K)
    sheath(K)
    e = 2.6 * (1 - ease(min(1.0, i / CLICK)))
    KAT_LEN[0] = max(1.0, (e + 3.0 - 0.6) / 2.3)
    katana_at_b(a - d * e, d)
    if i < CLICK:
        vclip = ('bx_18_block_high_center', 0.4)
    elif i < CLICK + 6:
        vclip = ('bx_27_hit_stomach', 0.05 + (i - CLICK) / FPS)
    else:
        vclip = ('bx_30_knockdown_punch', min(2.0, 0.6 + 1.1 * (i - CLICK - 6) / FPS * 1.6))
    V = rig('v', (0, 0, 0), 180, {'clip': vclip, 'scatter': 0.6 * ease((i - 30) / 9) if i > 30 else 0.0})
    if i == 0:
        S['kc'] = br(K['UpperTorso'].translation)
        S['vc0'] = br(V['UpperTorso'].translation)
    kc, vc0 = S['kc'], S['vc0']
    if i >= CLICK:
        c = vc0 + Vector((0, 0, -0.6))
        PROP_TR[0] = 0.0 if i < CLICK + 5 else min(0.9, (i - CLICK - 5) * 0.09)
        brush(c + Vector((-2.2, -0.8, 0.55)), c + Vector((2.2, -0.8, -0.3)), 0.25, 0.5, (0, -1, 0), INK, seed=61)
        brush(c + Vector((-1.9, -0.86, 0.4)), c + Vector((1.9, -0.86, -0.2)), 0.22, 0.15, (0, -1, 0), SKIN, seed=62, tag='stroke_edge')
        PROP_TR[0] = 0.0
    if i >= CLICK + 10:
        vb = br(V['UpperTorso'].translation)
        burst(vb + Vector((0, 0, 0.3)), 60, 2.6, (i - CLICK - 10) / (n - CLICK - 11), seed=421, size=1.2, fall=0.6)
    cam = kc + Vector((-4.4, 4.2, 0.95))
    look = kc * 0.38 + vc0 * 0.62 + Vector((0, 0, -0.1))
    lens(lerpv(cam, kc + (cam - kc) * 0.92, ease(u)), look, 42, 0)
    if CLICK <= i < CLICK + 2:
        return {'impact': STROKE_HIT}


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
    lens(br((hd @ Vector((0, 0.24, -2.4 + 0.25 * ease(u), 1))).xyz), br((hd @ Vector((0, 0.24, -0.55, 1))).xyz), 16, 0)


@shot('dust', "VICTIM'S EYES", 18)
def dv_veyes(i, n):
    u = i / (n - 1)
    desert()
    dart = math.sin(u * math.pi * 3)          # the eyes dart one way, the other, back
    K, V = m_dust_rigs(vface=dict(WIDE, EyesLookLeft=max(0.0, dart), EyesLookRight=max(0.0, -dart)))
    hd = V['Head']
    q = (hd @ Vector((0.38, 0.32 - 0.3 * u, -0.6, 1))).xyz   # the bead of sweat runs down
    prop('Ball', (0.12, 0.17, 0.12), CF(q.x, q.y, q.z), (0.85, 0.92, 1.0), 'Glass', 'sweat')
    lens(br((hd @ Vector((0, 0.24, -2.4 + 0.2 * u, 1))).xyz), br((hd @ Vector((0, 0.24, -0.55, 1))).xyz), 16, 4)


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
    lens(br((hd @ Vector((0, 0.26, -1.9 + 0.12 * u, 1))).xyz), br((hd @ Vector((0, 0.26, -0.55, 1))).xyz), 11, 0)


@shot('dust', 'THEIR EYES', 8)
def dv_veyes2(i, n):
    # and the other one's, as tight: wide and fixed now, no more darting (the owner, 20 Nov: "close ups of eyes on both")
    u = i / (n - 1)
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, 0.12), vclip=(DRAW, 0.09))
    hd = V['Head']
    q = (hd @ Vector((0.42, -0.1 - 0.1 * u, -0.6, 1))).xyz
    prop('Ball', (0.12, 0.17, 0.12), CF(q.x, q.y, q.z), (0.85, 0.92, 1.0), 'Glass', 'sweat')
    lens(br((hd @ Vector((0, 0.26, -1.9 + 0.12 * u, 1))).xyz), br((hd @ Vector((0, 0.26, -0.55, 1))).xyz), 11, -3)


DRAW_OUT = 0.3   # from here on the revolver is in the hand, not the holster


@shot('dust', 'THE DRAW', 10)
def dv_draw(i, n):
    # a perspective shot: low behind the gun hip, wide, tilted, looking up past the revolver to the victim far down
    # the street. The gun leaves smears - a bright streak along the muzzle's real path and fading copies of the gun
    u = i / (n - 1)
    t = 0.12 + 0.63 * u
    desert()
    K, V = m_dust_rigs(kclip=(DRAW, t), kgun_in=t < DRAW_OUT)
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


@shot('dust', 'HIT FRAME', 2)
def dv_hitframe(i, n):
    return m_dust_6()


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
    K, V = m_dust_rigs(kclip=(DRAW, tk), kgun_in=tk < DRAW_OUT, vclip=('bx_29_knocked_out_back', tv_))
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
            'anim': {r['name']: {'clip': r['clip'][0], 't': round(r['clip'][1], 4), 'root': comps(r['cf']['HumanoidRootPart']),
                                 'sc': round(r.get('scatter', 0), 3)} for r in RIGS if r.get('clip') and not r.get('tr')},
            'kat': [kat_rel(m, mode) for m, mode in zip(KATANA, KAT_MODE)], 'katL': round(KAT_LEN[0], 3)}


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
        S.clear() if sname != 'CUT FRAME' else None
        for i in range(nf):
            VT[0] = k / FPS
            clear()
            RIGS.clear(); PROPS.clear(); KATANA.clear(); GUNS.clear(); KAT_MODE.clear(); KAT_LEN[0] = 1.0
            info = fn(i, nf) or {}
            info['name'] = sname
            if not os.environ.get('FIN_NOPNG'):
                draw_preview()
                sc.render.filepath = os.path.join(vdir, f'{k:03d}.png')
                bpy.ops.render.render(write_still=True)
            allv[f'v{k:03d}'] = frame_data(info)
            k += 1
        shots.append([sname, nf])
        print('shot', vname, sname, nf, flush=True)
    # the fixed set (floor, pillars, trees) is the same in every frame: stored once as '_stage'
    STATIC = ('floor', 'pillar', 'tree', 'rock', 'cactus', 'fence', 'mesa', 'sky')
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
