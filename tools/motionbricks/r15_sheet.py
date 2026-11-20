"""Contact sheet of R15 clips on the place's real R15 rig, rendered in Blender (headless).

run:  blender.exe -b --factory-startup -P tools/motionbricks/r15_sheet.py -- out.png [--frames 8] [--travel]
          clip.rbxmx[@label[@t0@t1]] ... ['#title'] ...

(19 Nov 2026, the Kimodo / MotionBricks trials) reads the KeyframeSequence XML that mixamo_r15.py writes (the .rbxmx
beside each .rbxm), solves the rig forward with the attachment offsets of the place's R15 rig (the same numbers as
tools/roblox/finisher_r15.py: Part1 = Part0 * C0 * Pose * C1^-1), and lays every row out in one scene: one clip per
row, frames across it, each cell centred on that frame's hips over the ground (the travel is shown as a number unless
--travel keeps it). One orthographic three-quarter render, Workbench. Left side blue, right side orange, as the stick
sheets. A row starting '#' is a title band.
"""
import bpy, math, sys, os
import xml.etree.ElementTree as ET
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv.pop(0)
N, TRAVEL = 8, False
while argv and argv[0].startswith('--'):
    k = argv.pop(0)
    if k == '--frames': N = int(argv.pop(0))
    elif k == '--travel': TRAVEL = True

SIZE = {'LowerTorso': (2, 0.4, 1), 'UpperTorso': (2, 1.6, 1), 'Head': (1.2, 1.2, 1.2),
        'RightUpperArm': (1, 1.1687, 1), 'RightLowerArm': (1, 1.0519, 1), 'RightHand': (1, 0.3, 1),
        'LeftUpperArm': (1, 1.1687, 1), 'LeftLowerArm': (1, 1.0519, 1), 'LeftHand': (1, 0.3, 1),
        'RightUpperLeg': (1, 1.2166, 1), 'RightLowerLeg': (1, 1.1931, 1), 'RightFoot': (1, 0.3, 1),
        'LeftUpperLeg': (1, 1.2166, 1), 'LeftLowerLeg': (1, 1.1931, 1), 'LeftFoot': (1, 0.3, 1)}
JOINTS = [('HumanoidRootPart', 'LowerTorso', (0, -1, 0), (0, -0.2, 0)),
          ('LowerTorso', 'UpperTorso', (0, 0.2, 0), (0, -0.8, 0)),
          ('UpperTorso', 'Head', (0, 0.8, 0), (0, -0.586, 0)),
          ('UpperTorso', 'RightUpperArm', (1, 0.563, 0), (-0.5, 0.3943, 0)),
          ('RightUpperArm', 'RightLowerArm', (0, -0.3342, 0), (0, 0.2586, 0)),
          ('RightLowerArm', 'RightHand', (0, -0.5009, 0), (0, 0.125, 0)),
          ('UpperTorso', 'LeftUpperArm', (-1, 0.563, 0), (0.5, 0.3943, 0)),
          ('LeftUpperArm', 'LeftLowerArm', (0, -0.3341, 0), (0, 0.2587, 0)),
          ('LeftLowerArm', 'LeftHand', (0, -0.5009, 0), (0, 0.125, 0)),
          ('LowerTorso', 'RightUpperLeg', (0.5, -0.2, 0), (0, 0.4208, 0)),
          ('RightUpperLeg', 'RightLowerLeg', (0, -0.4009, 0), (0, 0.3792, 0)),
          ('RightLowerLeg', 'RightFoot', (0, -0.5472, 0), (0, 0.1019, 0)),
          ('LowerTorso', 'LeftUpperLeg', (-0.5, -0.2, 0), (0, 0.4208, 0)),
          ('LeftUpperLeg', 'LeftLowerLeg', (0, -0.4011, 0), (0, 0.379, 0)),
          ('LeftLowerLeg', 'LeftFoot', (0, -0.5472, 0), (0, 0.1019, 0))]
MB = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # Roblox -> Blender: (x, y, z) -> (x, -z, y)
T = lambda x, y, z: Matrix.Translation((x, y, z))


def load(path):
    kfs = []
    for kf in ET.parse(path).iter('Item'):
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
    return kfs


def pose_at(kfs, t):
    t = max(kfs[0][0], min(kfs[-1][0], t))
    i = 0
    while i < len(kfs) - 2 and kfs[i + 1][0] <= t:
        i += 1
    (t0, a), (t1, b) = kfs[i], kfs[min(i + 1, len(kfs) - 1)]
    u = 0 if t1 <= t0 else (t - t0) / (t1 - t0)
    out = {}
    for part, ma in a.items():
        mb = b.get(part, ma)
        m = ma.to_quaternion().slerp(mb.to_quaternion(), u).to_matrix().to_4x4()
        m.translation = ma.translation.lerp(mb.translation, u)
        out[part] = m
    return out


def solve(pose):
    cf = {'HumanoidRootPart': T(0, 3.0, 0)}  # (the root 3 studs up: an R15 avatar's HRP over the floor)
    for p0, p1, a0, a1 in JOINTS:
        cf[p1] = cf[p0] @ T(*a0) @ pose.get(p1, Matrix.Identity(4)) @ T(*a1).inverted()
    return cf


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
mats = {}


def mat(name, rgb):
    if name not in mats:
        m = bpy.data.materials.new(name)
        m.diffuse_color = (*rgb, 1)
        mats[name] = m
    return mats[name]


COL = lambda part: ((0.43, 0.63, 0.92) if part.startswith('Left') else (0.92, 0.47, 0.35) if part.startswith('Right')
                    else (0.80, 0.80, 0.82) if part != 'Head' else (0.95, 0.85, 0.55))
CELL_X, ROW_Z = 7.0, 9.5
YAW, PITCH = math.radians(35), math.radians(12)
# the view: from in front of the rig (it faces Roblox -Z, Blender +Y) and off to its right, a little above
cam_dir = Vector((math.sin(YAW) * math.cos(PITCH), math.cos(YAW) * math.cos(PITCH), math.sin(PITCH)))
right = Vector((0, 0, 1)).cross(cam_dir).normalized()  # (the image's right: a rig facing the lens shows its right side on the left)
up = cam_dir.cross(right).normalized()


def box(name, size, m_b, col):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = Vector(size)
    o.matrix_world = m_b @ Matrix.Diagonal((*size, 1))
    o.data.materials.append(mat(str(col), col))
    return o


def text(s, at, size=0.9, col=(1, 1, 1)):
    bpy.ops.object.text_add(location=at)
    o = bpy.context.active_object
    o.data.body = s
    o.data.size = size
    # (face the camera: the text's x along the view's right, y along its up)
    rot = Matrix((right, up, cam_dir)).transposed()
    o.matrix_world = Matrix.Translation(at) @ rot.to_4x4()
    o.data.materials.append(mat(str(col), col))
    return o


rows = []
for spec in argv:
    if spec.startswith('#'):
        rows.append(('title', spec[1:]))
        continue
    parts = spec.split('@')
    kfs = load(parts[0])
    label = parts[1] if len(parts) > 1 else os.path.basename(parts[0])
    t0, t1 = (float(parts[2]), float(parts[3])) if len(parts) > 3 else (kfs[0][0], kfs[-1][0])
    rows.append(('clip', label, kfs, t0, t1))

# rows run down the page: in the scene each one is ROW_Z lower and placed so the view sees it straight
row_i = 0
z = 0.0
for r in rows:
    origin = -up * z
    if r[0] == 'title':
        text(r[1], origin + right * (-CELL_X * 1.6) + up * 6.2, 1.1, (1.0, 0.86, 0.47))
        z += 3.0
        continue
    _, label, kfs, t0, t1 = r
    text(label, origin + right * (-CELL_X * 1.6) + up * 5.0, 0.75)
    text('%.2f s' % (kfs[-1][0]), origin + right * (-CELL_X * 1.6) + up * 3.9, 0.6, (0.6, 0.6, 0.65))
    base = None
    for c in range(N):
        t = t0 + (t1 - t0) * c / max(1, N - 1)
        cf = solve(pose_at(kfs, t))
        hips = cf['LowerTorso'].translation.copy()
        if base is None:
            base = hips.copy()
        shift = Vector((0, 0, 0)) if TRAVEL else Vector((hips.x, 0, hips.z))
        travel = Vector((hips.x - base.x, 0, hips.z - base.z)).length
        cell = origin + right * (CELL_X * c)
        for part, size in SIZE.items():
            m = cf[part].copy()
            m.translation = m.translation - shift
            box('%s_%d_%d' % (part, row_i, c), size, Matrix.Translation(cell) @ MB @ m, COL(part))
        text('%.2fs' % t + ('  %.1f st' % travel if travel > 0.5 else ''), cell + up * 7.4 + right * -2.5, 0.5, (0.7, 0.7, 0.75))
    # a floor line under the row
    row_i += 1
    z += ROW_Z

# the camera: orthographic, along -cam_dir, framing everything
cam_data = bpy.data.cameras.new('cam')
cam_data.type = 'ORTHO'
cam = bpy.data.objects.new('cam', cam_data)
sc.collection.objects.link(cam)
width = CELL_X * (N + 2.2)
top = 8.2  # (the first row's time labels and a title band's text sit up to here)
bottom = -(z - (ROW_Z if rows and rows[-1][0] == 'clip' else 3.0)) - 2.0
height = top - bottom
centre = right * (CELL_X * (N - 1) / 2 - CELL_X * 0.8) + up * ((top + bottom) / 2)
cam.matrix_world = Matrix.Translation(centre + cam_dir * 200) @ Matrix((right, up, cam_dir)).transposed().to_4x4()
cam_data.ortho_scale = width
cam_data.clip_end = 1000
sc.camera = cam
px = 150
sc.render.resolution_x = int(width * px / CELL_X * 1.0)
sc.render.resolution_y = int(height * px / CELL_X * 1.0)
cam_data.sensor_fit = 'HORIZONTAL'
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'
sc.display.shading.color_type = 'MATERIAL'
sc.display.shading.show_shadows = False
sc.display.shading.show_cavity = True
sc.world = bpy.data.worlds.new('w')
sc.world.color = (0.14, 0.15, 0.17)
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('R15_SHEET ok', OUT, sc.render.resolution_x, sc.render.resolution_y)
