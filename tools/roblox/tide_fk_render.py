# Renders the pro animator's Tidecrest take offline (26 Nov 2026): his two KeyframeSequences posed on the katana package's
# own R15 rig by forward kinematics - the Motor6D rule Roblox uses, Part1 = Part0 * C0 * Transform * C1^-1, each pose's
# CFrame the Transform - with the katana and sheath on their own tracks, the blade stretched, under his camera (or ours:
# a lens file), on a plain stage or our set. Nothing in his file is run; it is read as numbers (rbxm_read).
#   blender -b --factory-startup -P tide_fk_render.py -- <take.rbxm> <package.rbxm> <out dir> <frames: 8,30,52 | all>
#       [--lens=<lens.json>] [--set=<kit .glb>] [--w=960] [--samples=16]
# Writes <out>/f<NNN>.jpg. Coordinates: Roblox studs, the take's space (the killer's root at frame 0 is the origin, the
# floor 3 below), turned into Blender's z-up on the way in.
import bpy, sys, os, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rbxm_read as R
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index('--') + 1:]
FLAGS = {a.split('=')[0]: (a.split('=', 1)[1] if '=' in a else True) for a in argv if a.startswith('--')}
ARGS = [a for a in argv if not a.startswith('--')]
TAKE, PKG, OUT, FR = ARGS[0], ARGS[1], ARGS[2], ARGS[3]
os.makedirs(OUT, exist_ok=True)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

P = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # Roblox (x, y, z) -> Blender (x, -z, y)
GZ = -0.62


def cfm(cf):
    """a Roblox CFrame ((x, y, z), [r00..r22]) as a 4x4"""
    (x, y, z), r = cf
    return Matrix(((r[0], r[1], r[2], x), (r[3], r[4], r[5], y), (r[6], r[7], r[8], z), (0, 0, 0, 1)))


# ---------------------------------------------------------------- the take: each sequence's pose per keyframe
take = R.load(TAKE)
seqs = {}
for k in take:
    if k.cls != 'KeyframeSequence':
        continue
    frames = []
    for kf in sorted((c for c in k.children if c.cls == 'Keyframe'), key=lambda c: c.props.get('Time', 0)):
        tr = {}
        stack = [(p, None) for p in kf.children if p.cls == 'Pose']
        while stack:
            p, parent = stack.pop()
            tr[p.name] = cfm(p.props.get('CFrame', ((0, 0, 0), [1, 0, 0, 0, 1, 0, 0, 0, 1])))
            stack += [(c, p.name) for c in p.children if c.cls == 'Pose']
        frames.append(tr)
    seqs[k.name] = frames
src = {i.name: i.props.get('Source', '') for i in take if i.cls == 'ModuleScript'}
import re
cam = {}
for m in re.finditer(r'\[(\d+)\]\s*=\s*\{\s*cf\s*=\s*CFrame\.new\(([^)]*)\)\s*,\s*fov\s*=\s*([\d.]+)\s*,\s*shot\s*=\s*(\d+)', src['CameraTrack']):
    v = [float(x) for x in m.group(2).split(',')]
    cam[int(m.group(1))] = (v, float(m.group(3)), int(m.group(4)))
blade = {int(m.group(1)): float(m.group(2)) for m in re.finditer(r'\[(\d+)\]\s*=\s*(-?[\d.]+)', src['BladeStretch'])}

# ---------------------------------------------------------------- the package rig: parts, joints, props
pkg = R.load(PKG)
byref = {i.ref: i for i in pkg}
fold = [i for i in pkg if i.cls == 'Folder' and i.name == 'Tidecrest'][0]
rig = [c for c in fold.children if c.name == 'R15_Katana_Rig'][0]
rest = {}
for c in rig.children:
    if c.cls in ('Part', 'MeshPart'):
        rest[c.name] = (cfm(c.props['CFrame']), Vector(c.props.get('size', (1, 1, 1))))
joints = {}   # Part1 name -> (Part0 name, C0, C1)
props = {}    # 'Katana' / 'Sheath' -> [(name, rel 4x4 to the root part, size)]
for d in pkg:
    if d.cls == 'Motor6D' and d.parent in byref:
        top = d
        while top.parent in byref and byref[top.parent] is not rig:
            top = byref[top.parent]
        if byref.get(top.parent) is not rig and top is not rig:
            pass
        p0, p1 = byref.get(d.props.get('Part0')), byref.get(d.props.get('Part1'))
        if p0 and p1 and (p0.parent == rig.ref or byref.get(p0.parent) and byref[p0.parent].parent == rig.ref):
            joints[p1.name] = (p0.name, cfm(d.props['C0']), cfm(d.props['C1']))
for mname, rname in (('KatanaModel', 'Katana'), ('SheathModel', 'Sheath')):
    m = [c for c in rig.children if c.name == mname][0]
    root = [c for c in m.children if c.name == rname][0]
    rr = cfm(root.props['CFrame'])
    props[rname] = [(c.name, rr.inverted() @ cfm(c.props['CFrame']), Vector(c.props.get('size', (0.2, 0.2, 0.2)))) for c in m.children if c.cls == 'MeshPart']
    rest[rname] = (rr, Vector(root.props.get('size', (0.2, 0.2, 0.2))))
print('JOINTS', sorted(joints), 'PROPS', {k: len(v) for k, v in props.items()})


def pose(frame_tr, root_cf):
    """every part's world 4x4 for one frame: walk out from the root"""
    out = {'HumanoidRootPart': root_cf}
    todo = True
    while todo:
        todo = False
        for p1, (p0, C0, C1) in joints.items():
            if p1 not in out and p0 in out:
                T = frame_tr.get(p1, Matrix.Identity(4))
                out[p1] = out[p0] @ C0 @ T @ C1.inverted()
                todo = True
    return out


# ---------------------------------------------------------------- the scene objects
def mat(name, rgb, emit=0.0, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1); b.inputs['Roughness'].default_value = rough
    if emit:
        b.inputs['Emission Color'].default_value = (*rgb, 1); b.inputs['Emission Strength'].default_value = emit
    return m


def box(name, size, m):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size.x, size.y, size.z)
    bpy.ops.object.transform_apply(scale=True)
    bev = o.modifiers.new('b', 'BEVEL'); bev.width = min(size) * 0.18; bev.segments = 2
    o.data.materials.append(m)
    return o


M_K = mat('killer', (0.09, 0.08, 0.1)); M_V = mat('victim', (0.42, 0.44, 0.48)); M_HEAD = mat('head', (0.85, 0.78, 0.7))
M_BLADE = mat('blade', (0.9, 0.92, 0.96), rough=0.2); M_GOLD = mat('gold', (0.75, 0.55, 0.2), rough=0.3); M_LAC = mat('lac', (0.03, 0.02, 0.03), rough=0.3)
bodies = {}
for who, mm in (('k', M_K), ('v', M_V)):
    bodies[who] = {}
    for name, (cf, size) in rest.items():
        if name in ('HumanoidRootPart', 'Katana', 'Sheath'):
            continue
        bodies[who][name] = box(who + name, size, M_HEAD if name == 'Head' else mm)
propObjs = {}
for rname, parts in props.items():
    for (nm, rel, size) in parts:
        m = M_BLADE if 'blade' in nm and 'gold' not in nm else (M_LAC if any(s in nm for s in ('body', 'tsuka', 'slot')) else M_GOLD)
        o = box('p_' + nm, size, m)
        propObjs[(rname, nm)] = (o, rel, size)
# the stage: a floor 3 under the origin, a mark every 6 studs down the lane
if '--set' not in FLAGS:
    bpy.ops.mesh.primitive_plane_add(size=200); fl = bpy.context.active_object
    fl.data.materials.append(mat('floor', (0.62, 0.6, 0.57), rough=0.9)); fl.matrix_world = P @ Matrix.Translation((0, -3, -20)) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
    for i in range(9):
        o = box('mark%d' % i, Vector((14, 0.04, 0.12)), mat('mark', (0.3, 0.29, 0.27)))
        o.matrix_world = P @ Matrix.Translation((0, -2.98, -6 * i))
else:
    with bpy.data.libraries.load(FLAGS['--set']) as (src_, dst_):
        dst_.objects = [n for n in src_.objects if n not in ('cam', 'sun')]
    for o in dst_.objects:
        if o is not None:
            bpy.context.scene.collection.objects.link(o)
            o.location.z -= 2.78   # (the set's floor is 0; the take's floor is 2.78 under its origin)
camd = bpy.data.cameras.new('cam'); camd.clip_end = 6000; camd.clip_start = 0.05; camd.sensor_fit = 'VERTICAL'
camo = bpy.data.objects.new('cam', camd); bpy.context.scene.collection.objects.link(camo); bpy.context.scene.camera = camo
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3.2 if '--set' not in FLAGS else 1.6; sun.angle = 0.1
if '--set' in FLAGS: sun.color = (0.7, 0.78, 1.0)
so = bpy.data.objects.new('sun', sun); bpy.context.scene.collection.objects.link(so); so.rotation_euler = (math.radians(50), 0, math.radians(-140)) if '--set' not in FLAGS else (math.radians(-72), 0, math.radians(4))
w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.6, 0.68, 1) if '--set' not in FLAGS else (0.06, 0.09, 0.18, 1)
bpy.context.scene.world = w
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(FLAGS.get('--samples', 16)); sc.cycles.use_denoising = False
W = int(FLAGS.get('--w', 960)); sc.render.resolution_x, sc.render.resolution_y = W, W * 9 // 16
sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'JPEG'

lens = json.load(open(FLAGS['--lens'])) if '--lens' in FLAGS else None
# (--timeline=<lens.json from tide_lens.py>: render the result's frames 0..N-1, each at its fractional take frame, the
# poses and the lens blended between his frames - an animatic through the speed ramps)
TL = json.load(open(FLAGS['--timeline'])) if '--timeline' in FLAGS else None


def blend(A, B, a):
    if a <= 1e-4: return A
    qa, qb = A.to_quaternion(), B.to_quaternion()
    T = A.to_translation().lerp(B.to_translation(), a)
    return Matrix.Translation(T) @ qa.slerp(qb, a).to_matrix().to_4x4()
ROOT_K = Matrix.Identity(4)
ROOT_V = Matrix.Translation((0, 0.22, -36)) @ Matrix.Rotation(math.pi, 4, 'Y')
NF = len(seqs['Tidecrest_Samurai'])
if TL:
    jobs = [(k, x) for k, x in enumerate(TL['timeline'])]
    if FR != 'all':
        a_, b_ = (int(x) for x in FR.split('-'))
        jobs = jobs[a_:b_]
else:
    jobs = [(f, float(f)) for f in (range(NF) if FR == 'all' else [int(x) for x in FR.split(',')])]
for outk, fx in jobs:
    f = int(fx); al = fx - f
    f1 = min(f + 1, NF - 1)
    for who, seq, root in (('k', 'Tidecrest_Samurai', ROOT_K), ('v', 'Tidecrest_Enemy', ROOT_V)):
        if al > 1e-4 and f1 != f:
            A_, B_ = seqs[seq][f], seqs[seq][f1]
            tr = {k: blend(A_[k], B_.get(k, A_[k]), al) for k in A_}
        else:
            tr = seqs[seq][f]
        W_ = pose(tr, root)
        for name, o in bodies[who].items():
            if name in W_: o.matrix_world = P @ W_[name]
        if who == 'k':
            L = blade.get(f, 1.0) + (blade.get(f1, 1.0) - blade.get(f, 1.0)) * al
            for (rname, nm), (o, rel, size) in propObjs.items():
                base = W_.get(rname)
                if base is None: continue
                if rname == 'Katana' and 'blade' in nm:
                    t = rel.to_translation()
                    rel2 = Matrix.Translation((t.x, t.y, GZ + (t.z - GZ) * L)) @ rel.to_quaternion().to_matrix().to_4x4() @ Matrix.Diagonal((1, 1, L, 1))
                    o.matrix_world = P @ base @ rel2
                else:
                    o.matrix_world = P @ base @ rel
    if TL:
        c0, c1 = TL['lens'][f], TL['lens'][f1]
        same = TL['shot'][f] == TL['shot'][f1]
        A_ = cfm(((c0[0], c0[1], c0[2]), c0[3:12]))
        if same and al > 1e-4:
            cf = blend(A_, cfm(((c1[0], c1[1], c1[2]), c1[3:12])), al)
            fov = c0[12] + (c1[12] - c0[12]) * al
        else:
            cf, fov = A_, c0[12]
    elif lens:
        c = lens[str(f)]
        cf, fov = cfm(((c[0], c[1], c[2]), c[3:12])), c[12]
    else:
        v, fov, _ = cam[f]
        cf = cfm(((v[0], v[1], v[2]), v[3:12]))
    camo.matrix_world = P @ cf
    camd.angle = math.radians(fov)
    sc.render.filepath = os.path.join(OUT, ('o%04d.jpg' % outk) if TL else ('f%03d.jpg' % f))
    bpy.ops.render.render(write_still=True)
    print('RENDERED', outk, fx)
