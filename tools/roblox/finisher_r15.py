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
argv = [a_ for a_ in argv if not a_.startswith('sheet:')]
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


def clip_pose(name, t):
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


def rig(name, at, yaw, pose, body=(0, 0, 0), ground=True, floor_y=0.0, col=None):
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
    RIGS.append({'name': name, 'cf': cf, 'col': col or (SHOOTER if name == 'k' else VICTIM), 'face': pose.get('face')})
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
VICTIM = (0.82, 0.8, 0.77)
SKIN = (0.93, 0.60, 0.72)
INK = (0.05, 0.05, 0.07)
SAKURA = (0.95, 0.74, 0.82)
WOOD = (0.32, 0.23, 0.2)
LACQUER = (0.10, 0.07, 0.09)
STEEL = (0.86, 0.88, 0.92)
GOLD = (0.85, 0.68, 0.32)
FLOORC = (0.86, 0.86, 0.88)
PILLAR = (0.72, 0.73, 0.77)
RIGS = []
GUNS = []    # {'model': 'revolver_dust', 'cf': grip frame (Roblox), 'scale': 3}
PROPS = []   # {'shape': 'Block'|'Ball'|'Cylinder'|'Wedge', 'size': (x,y,z) Roblox, 'cf': 4x4 Roblox, 'col', 'mat', 'tag'}
KATANA = []  # Roblox CFrames of the katana grip (the place's katana_sakura, scaled x3)


def prop(shape, size, cf, col, mat='SmoothPlastic', tag=''):
    PROPS.append({'shape': shape, 'size': tuple(size), 'cf': cf, 'col': col, 'mat': mat, 'tag': tag})


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


def katana_grip(m):
    KATANA.append(m)


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
        bl_box('prop_' + p['tag'], p['size'], p['cf'], p['col'], p['shape'])
    for g in GUNS:
        m = g['cf']
        bl_box('gun_body', (0.28, 0.42, 1.0), m @ CF(0, 0.1, -0.1), (0.12, 0.12, 0.14))
        bl_box('gun_barrel', (0.2, 0.2, 0.9), m @ CF(0, 0.2, -0.9), (0.12, 0.12, 0.14))
        bl_box('gun_grip', (0.24, 0.6, 0.3), m @ CF(0, -0.35, 0.3), (0.45, 0.3, 0.18))
    for m in KATANA:
        bl_box('kat_blade', (0.05, 0.27, 2.1), m @ CF(0, 0.1, -1.45), STEEL)
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
def revolver_in_hand(cf):
    # the barrel runs on from the forearm, the gun's top toward the back of the hand; the grip sits in the palm
    g = cf['RightHand'] @ CF(0, -0.1, 0) @ ANG(-90, 0, 0) @ CF(0, 0.55, -0.25)
    GUNS.append({'model': 'revolver_dust', 'cf': g})
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


def tumbleweed(at_b, r=1.6, seed=5):
    rnd = random.Random(seed)
    c = Vector(at_b)
    for i in range(44):
        a = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized() * r * rnd.uniform(0.6, 1.0)
        b = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized() * r * rnd.uniform(0.6, 1.0)
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
def tide_stage():
    stage()
    tree((-8, 11))
    tree((-15, -26), 5.8)
    petals((-5, 9, 3), 10, 4, seed=401)


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
K_START = at_for(SLASH, T_HIT, (3.3, 0.0), 0)
K_BACK = (2.6, 6.6)   # after the pass: a few steps on, back to back with the victim (the owner's beat sheet)


def blade_sweep(cn, at, yaw, t0, t1, n=14, col=INK, width=None, tag='smear'):
    # an ink-brush smear along the blade's real path between t0 and t1 (the katana in the right hand of the clip)
    pts = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        p = rb((at[0], at[1], 0))
        root = CF(p.x, 3.0, p.z) @ ANG(0, yaw, 0)
        cf = solve(root, {'clip': (cn, t)})
        g = hand_cf(cf)
        pts.append((wpt(g, (0, 0, -0.6)), wpt(g, (0, 0, -2.9))))
    for i in range(n):
        (a0, b0), (a1, b1) = pts[i], pts[i + 1]
        mid0, mid1 = (a0 + b0) / 2, (a1 + b1) / 2
        L = (b0 - a0).length * (0.4 + 0.6 * i / n)
        prop_box_between(mid0, mid1 + (mid1 - mid0) * 0.15, 0.08, L, col, up_b=(b0 - a0).normalized(), tag=tag,
                         mat='Neon' if col == INK else 'SmoothPlastic')


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
    splats(c + Vector((-0.8, 0.6, 0.0)), 14, 1.4, seed=71)
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
    petals(vc + Vector((0, 0, 0.6)), 70, 2.8, seed=421, size=1.3)
    splats(vc, 26, 2.2, seed=81, size=1.4)
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


# ------------------------------------------------------------------ run
setup()
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
                'rigs': [{'name': r['name'], 'col': r['col'], 'parts': {k: comps(v) for k, v in r['cf'].items()}} for r in RIGS],
                'props': [{'shape': p['shape'], 'size': [round(x, 3) for x in p['size']], 'cf': comps(p['cf']), 'col': p['col'], 'mat': p['mat'], 'tag': p['tag']} for p in PROPS],
                'katana': [comps(m) for m in KATANA], 'guns': [{'model': g['model'], 'cf': comps(g['cf'])} for g in GUNS],
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
