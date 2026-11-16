# Preview renders of the kit guns (tools/roblox/gun_models.py) without Studio: Cycles on the CPU, headless.
#   blender -b --factory-startup -P tools/roblox/gun_preview.py -- <out_dir> [--old <dir with the web w_*.glb>] [--size 640x400] [--fov 70] <id> [...]
# writes <out_dir>/<id>.png: a card of four panels
#   top left      the new model, three-quarter view (about the loadout's angle)
#   top right     the new model as the player holds it (the camera and pose the game uses: Weapons.luau vm p / r / s)
#   bottom left   the new model from its left side, flat on (the side the player sees), the row's spots marked
#   bottom right  the OLD web model in hand, same pose (when --old is given)
# the in-hand panel has no arms: it is for the gun's shape, colour blocks and sight line.
import bpy, sys, os, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mathutils import Matrix, Vector, Euler
import gunkit, gun_models
ALLG = dict(gun_models.BUILD); ALLG.update(gun_models.SKINS)
if '--set' in sys.argv and sys.argv[sys.argv.index('--set') + 1] == 'c':  # version C (gun_models_c.py)
    import gun_models_c
    ALLG = dict(gun_models_c.BUILD)
if '--set' in sys.argv and sys.argv[sys.argv.index('--set') + 1] == 'live':  # the picked set (gun_set.py)
    import gun_set
    ALLG = dict(gun_set.BUILD); ALLG.update(gun_set.SKINS)

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0]; rest = argv[1:]
old_dir = None; W, H = 640, 400; fov = 70.0; hold = 1.0
if '--old' in rest: i = rest.index('--old'); old_dir = rest[i + 1]; del rest[i:i + 2]
if '--size' in rest: i = rest.index('--size'); W, H = [int(x) for x in rest[i + 1].split('x')]; del rest[i:i + 2]
if '--fov' in rest: i = rest.index('--fov'); fov = float(rest[i + 1]); del rest[i:i + 2]
if '--set' in rest: i = rest.index('--set'); del rest[i:i + 2]
if '--hold' in rest: i = rest.index('--hold'); hold = float(rest[i + 1]); del rest[i:i + 2]  # the viewmodel's size factor (Holds.size)
ids = rest
os.makedirs(out_dir, exist_ok=True)


# the viewmodel rest poses, straight from the game's rows (metres; r = radians, CFrame.fromEulerAnglesXYZ)
def vm_poses():
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, '..', '..', 'roblox', 'src', 'shared', 'Weapons.luau'), encoding='utf8').read()
    out = {}
    for m in re.finditer(r'\n\t(\w+) = \{\n\t\tid = "(\w+)"(.*?)\n\t\},', src, re.S):
        v = re.search(r'vm = \{ p = Vector3\.new\(([^)]*)\) \* S, r = Vector3\.new\(([^)]*)\), s = ([\d.]+)', m.group(3))
        if v: out[m.group(2)] = ([float(x) for x in v.group(1).split(',')], [float(x) for x in v.group(2).split(',')], float(v.group(3)))
    return out


VM = vm_poses()
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # weapon frame -> Blender


def to_blender(mf): return C @ mf @ C.inverted()


def hold_matrix(wid):
    p, r, s = VM.get(wid, ([0.2, -0.2, -0.38], [0, 0.04, 0], 0.7))
    rot = Matrix.Rotation(r[0], 4, 'X') @ Matrix.Rotation(r[1], 4, 'Y') @ Matrix.Rotation(r[2], 4, 'Z')
    return to_blender(Matrix.Translation(Vector(p)) @ rot @ Matrix.Scale(s * hold, 4))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'; sc.cycles.samples = 24; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.75, 0.78, 0.85, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.55
    return sc


def sun(sc, rot, strength):
    d = bpy.data.lights.new('sun', 'SUN'); d.energy = strength; d.angle = 0.2
    o = bpy.data.objects.new('sun', d); o.rotation_euler = rot; sc.collection.objects.link(o)


def camera(sc, loc, look, ortho=None, fov_y=None, up=Vector((0, 0, 1))):
    cd = bpy.data.cameras.new('c'); o = bpy.data.objects.new('c', cd); sc.collection.objects.link(o)
    o.location = loc
    f = (Vector(look) - Vector(loc)).normalized()
    r = f.cross(up).normalized(); u = r.cross(f)
    o.rotation_euler = Matrix((r, u, -f)).transposed().to_euler()
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(fov_y or 40)
    cd.clip_start = 0.01; cd.clip_end = 100
    sc.camera = o


def render(path, crop=False):
    r = bpy.context.scene.render
    r.filepath = path
    if crop:  # the lower right 58% x 66% of a 16:9-ish view, which comes out W x H
        r.resolution_x, r.resolution_y = round(W / 0.58), round(H / 0.66)
        r.use_border = True; r.use_crop_to_border = True
        r.border_min_x, r.border_max_x, r.border_min_y, r.border_max_y = 0.42, 1.0, 0.0, 0.66
    bpy.ops.render.render(write_still=True)


def load_old(wid, at):
    f = os.path.join(old_dir, 'w_%s.glb' % wid)
    if not os.path.exists(f): return False
    bpy.ops.import_scene.gltf(filepath=f)
    root = bpy.data.objects.new('oldroot', None); bpy.context.scene.collection.objects.link(root)
    for o in list(bpy.context.scene.objects):
        if o.parent is None and o is not root: o.parent = root
    root.matrix_world = at
    return True


def marker(sc, at, col):
    import bmesh
    me = bpy.data.meshes.new('mk')
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.006); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('mk', me); sc.collection.objects.link(o); o.location = gunkit.P(at[0] - 0.08, at[1], at[2])
    m = bpy.data.materials.new('mk'); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    (b.inputs.get('Emission Color') or b.inputs.get('Emission')).default_value = col
    b.inputs['Emission Strength'].default_value = 5
    me.materials.append(m)


BG = np.array([0.20, 0.21, 0.24], dtype=np.float32)


def read(path):
    im = bpy.data.images.load(path)
    px = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
    bpy.data.images.remove(im)
    a = px[..., 3:4]
    img = np.concatenate([px[..., :3] * a + BG * (1 - a), np.ones_like(a)], axis=2)
    out = np.tile(np.append(BG, 1.0).astype(np.float32), (H, W, 1))  # (a cropped render can be a pixel short)
    h, w = min(H, img.shape[0]), min(W, img.shape[1])
    out[:h, :w] = img[:h, :w]
    return out


for wid in ids:
    g = ALLG[wid]()
    lo, hi = g.bounds()
    cz, cy = (lo[2] + hi[2]) / 2, (lo[1] + hi[1]) / 2
    L = hi[2] - lo[2]
    tmp = [os.path.join(out_dir, '_%s_%d.png' % (wid, i)) for i in range(4)]
    # 1: three-quarter, from the front left and above
    sc = reset(); g.to_scene(); sun(sc, Euler((math.radians(50), 0, math.radians(-40))), 3.0)
    mid = gunkit.P(0, cy, cz)
    camera(sc, mid + Vector((-0.75 * L, 0.80 * L, 0.42 * L)), mid, fov_y=42)
    render(tmp[0])
    # 2: in hand
    sc = reset(); g.to_scene(at=hold_matrix(wid)); sun(sc, Euler((math.radians(35), 0, math.radians(20))), 3.0)
    camera(sc, Vector((0, 0, 0)), Vector((0, 1, 0)), fov_y=fov)
    render(tmp[1], crop=True)
    # 3: left side, flat on (muzzle to the left), the row's spots marked
    sc = reset(); g.to_scene(); sun(sc, Euler((math.radians(60), 0, math.radians(-90))), 3.0)
    for name, at in g.spots.items(): marker(sc, at, (1, 0.2, 0.2, 1) if name in ('muzzle', 'sight') else (0.2, 0.8, 1, 1))
    camera(sc, gunkit.P(-3, cy, cz), gunkit.P(0, cy, cz), ortho=max(L * 1.08, (hi[1] - lo[1]) * 1.08 * W / H))
    render(tmp[2])
    # 4: the old model in hand
    have_old = False
    if old_dir:
        sc = reset(); have_old = load_old(wid, hold_matrix(wid)); sun(sc, Euler((math.radians(35), 0, math.radians(20))), 3.0)
        camera(sc, Vector((0, 0, 0)), Vector((0, 1, 0)), fov_y=fov)
        if have_old: render(tmp[3], crop=True)
    panels = [read(tmp[0]), read(tmp[1]), read(tmp[2]), read(tmp[3]) if have_old else np.tile(np.append(BG, 1.0).astype(np.float32), (H, W, 1))]
    top = np.concatenate(panels[0:2], axis=1); bot = np.concatenate(panels[2:4], axis=1)
    card = np.concatenate([bot, top], axis=0)  # (image rows run bottom-up)
    im = bpy.data.images.new('card', W * 2, H * 2, alpha=False); im.pixels = card.ravel().tolist()
    im.filepath_raw = os.path.join(out_dir, wid + '.png'); im.file_format = 'PNG'; im.save()
    for t in tmp:
        if os.path.exists(t): os.remove(t)
    print('CARD', im.filepath_raw, 'bounds', lo, hi, 'tris', g.tris(), 'pieces', len(g.pieces))
