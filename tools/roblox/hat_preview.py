# Preview renders of the weapon hats (hat_models.py) without Studio: Cycles on the CPU, headless.
#
#   blender -b --factory-startup -P tools/roblox/hat_preview.py -- <out_dir> sheet
#       hats.png: all ten hats on their own, three-quarter view, one size
#   blender -b --factory-startup -P tools/roblox/hat_preview.py -- <out_dir> eye <hat> [gun ...]
#       eye_<hat>.png: the hat on each gun as the player holds it (the game's camera, 70 degree view, the gun at its
#       rest pose and size from Weapons.luau vm and tools/roblox/holds.json), the crosshair marked. The spot is the
#       one in hat_spots.json, its height measured like hat_spots.py does.
#   blender ... -- <out_dir> side <hat> [gun ...]      the same from the gun's left, flat on (where it sits)
import bpy, bmesh, sys, os, math, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mathutils import Matrix, Vector, Euler
from mathutils.bvhtree import BVHTree
import gunkit, hat_models
# the guns: the live set (gun_set.py, the owner's A/B/C picks) unless --set kit (gun_models.py, round 8)
if '--set' in sys.argv and sys.argv[sys.argv.index('--set') + 1] == 'kit':
    import gun_models as GUNS
else:
    import gun_set as GUNS

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
argv = sys.argv[sys.argv.index('--') + 1:]
if '--set' in argv: i = argv.index('--set'); del argv[i:i + 2]
SPOT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hat_spots.json')
if '--spots' in argv: i = argv.index('--spots'); SPOT_FILE = argv[i + 1]; del argv[i:i + 2]  # (try other seats)
out_dir, mode, rest = argv[0], argv[1], argv[2:]
os.makedirs(out_dir, exist_ok=True)
W, H = 640, 360
BG = np.array([0.20, 0.21, 0.24], dtype=np.float32)
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # weapon frame -> Blender
HOLDS = json.load(open(os.path.join(HERE, 'holds.json')))
SPOTS = json.load(open(SPOT_FILE))
GUN_IDS = ['ar', 'smg', 'burst', 'lmg', 'dmr', 'sniper', 'lever', 'shotgun', 'autoshot', 'sawnoff', 'pistol', 'revolver',
        'redline', 'marbles', 'katana', 'shredder']


def to_blender(mf): return C @ mf @ C.inverted()


def vm_poses():
    src = open(os.path.join(ROOT, 'roblox', 'src', 'shared', 'Weapons.luau'), encoding='utf8').read()
    out = {}
    for m in re.finditer(r'\n\t(\w+) = \{\n\t\tid = "(\w+)"(.*?)\n\t\},', src, re.S):
        v = re.search(r'vm = \{ p = Vector3\.new\(([^)]*)\) \* S, r = Vector3\.new\(([^)]*)\), s = ([\d.]+)', m.group(3))
        if v: out[m.group(2)] = ([float(x) for x in v.group(1).split(',')], [float(x) for x in v.group(2).split(',')], float(v.group(3)))
    return out


VM = vm_poses()


def hold_matrix(wid):
    wid = wid.split('@')[0]
    p, r, s = VM.get(wid, ([0.2, -0.2, -0.38], [0, 0.04, 0], 0.7))
    row = HOLDS.get(wid, {}) if isinstance(HOLDS.get(wid), dict) else {}
    size = HOLDS.get('_size', 1.0) * row.get('scale', 1.0)
    sh = row.get('shift', [0, 0, 0])
    p = [p[i] + sh[i] for i in range(3)]
    rot = Matrix.Rotation(r[0], 4, 'X') @ Matrix.Rotation(r[1], 4, 'Y') @ Matrix.Rotation(r[2], 4, 'Z')
    return to_blender(Matrix.Translation(Vector(p)) @ rot @ Matrix.Scale(s * size, 4))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'; sc.cycles.samples = 20; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.75, 0.78, 0.85, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.6
    d = bpy.data.lights.new('sun', 'SUN'); d.energy = 3.0; d.angle = 0.2
    o = bpy.data.objects.new('sun', d); o.rotation_euler = Euler((math.radians(40), 0, math.radians(25))); sc.collection.objects.link(o)
    return sc


def camera(sc, loc, look, fov_y=40, ortho=None, up=Vector((0, 0, 1))):
    cd = bpy.data.cameras.new('c'); o = bpy.data.objects.new('c', cd); sc.collection.objects.link(o)
    o.location = loc
    f = (Vector(look) - Vector(loc)).normalized()
    r = f.cross(up).normalized(); u = r.cross(f)
    o.rotation_euler = Matrix((r, u, -f)).transposed().to_euler()
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(fov_y)
    cd.clip_start = 0.005; cd.clip_end = 100
    sc.camera = o


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def read(path, cross=False):
    im = bpy.data.images.load(path)
    px = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
    bpy.data.images.remove(im)
    a = px[..., 3:4]
    img = np.concatenate([px[..., :3] * a + BG * (1 - a), np.ones_like(a)], axis=2)
    if cross:  # the crosshair: a small white plus at the middle
        cy, cx = img.shape[0] // 2, img.shape[1] // 2
        img[cy - 1:cy + 1, cx - 7:cx + 7, :3] = 1.0
        img[cy - 7:cy + 7, cx - 1:cx + 1, :3] = 1.0
    return img


def tile(imgs, cols, path):
    blank = np.tile(np.append(BG, 1.0).astype(np.float32), (H, W, 1))
    while len(imgs) % cols: imgs.append(blank)
    rows = [np.concatenate(imgs[i:i + cols], axis=1) for i in range(0, len(imgs), cols)]
    card = np.concatenate(rows[::-1], axis=0)  # (image rows run bottom-up)
    im = bpy.data.images.new('card', card.shape[1], card.shape[0], alpha=False); im.pixels = card.ravel().tolist()
    im.filepath_raw = path; im.file_format = 'PNG'; im.save()
    print('CARD', path)


def gun_tree(g):
    bm = bmesh.new()
    for b in g.pieces.values():
        me = bpy.data.meshes.new('t'); b.to_mesh(me); bm.from_mesh(me); bpy.data.meshes.remove(me)
    t = BVHTree.FromBMesh(bm); bm.free()
    return t


def spot_matrix(wid, g, hid=None):
    sp = SPOTS.get(wid) or SPOTS[wid.split('@')[0]]
    if hid in hat_models.SEATED:  # (the googly eyes stand on the gun themselves: their own height, upright, no saddle)
        t = gun_tree(g)
        def topf(a, b):
            hit = t.ray_cast(Vector((a, -b, 1.0)), Vector((0, 0, -1)))
            return hit[0].z if hit[0] is not None else None
        ex, ey, _, ez = hat_models.eyes_seat(topf, sp)
        return (Matrix.Translation(Vector((ex, ey, ez))) @ Matrix.Rotation(math.radians(sp.get('yaw', 0)), 4, 'Y')
                @ Matrix.Scale(sp.get('s', 1.0), 4))
    x, z = sp.get('x', 0.0), sp['z']
    if 'y' in sp: y = sp['y']
    else:
        hit = gun_tree(g).ray_cast(Vector((x, -z, 1.0)), Vector((0, 0, -1)))
        y = hit[0].z if hit[0] is not None else 0.0
    y -= sp.get('sink', 0.002)
    # (the saddle lifts the hat along its own up, as GunHats.make does; the slate puck itself is not drawn here)
    return (Matrix.Translation(Vector((x, y, z))) @ Matrix.Rotation(math.radians(sp.get('yaw', 0)), 4, 'Y')
            @ Matrix.Rotation(math.radians(sp.get('pitch', 0)), 4, 'X') @ Matrix.Translation(Vector((0, sp.get('saddle', 0.0), 0)))
            @ Matrix.Scale(sp.get('s', 1.0), 4))


if mode == 'sheet':  # (sheet [hat ...]: those hats only)
    imgs = []
    for hid in (rest or hat_models.HATS):
        sc = reset()
        hat_models.make(hid).to_scene()
        mid = gunkit.P(0, 0.03, 0)
        camera(sc, mid + Vector((-0.11, -0.14, 0.085)), mid, fov_y=36)
        p = os.path.join(out_dir, '_h_%s.png' % hid); render(p); imgs.append(read(p)); os.remove(p)
    tile(imgs, 5, os.path.join(out_dir, 'hats.png'))
elif mode in ('eye', 'side'):
    hid = rest[0]
    guns = rest[1:] or GUN_IDS
    imgs = []
    for wid in guns:
        sc = reset()
        g = GUNS.SKINS[wid]() if '@' in wid else GUNS.BUILD[wid]()
        hm = spot_matrix(wid, g, hid)
        h = hat_models.make(hid) if hid != 'none' else None
        if mode == 'eye':
            at = hold_matrix(wid)
            g.to_scene(at=at)
            if h: h.to_scene(at=at @ to_blender(hm))
            camera(sc, Vector((0, 0, 0)), Vector((0, 1, 0)), fov_y=70)
        else:
            g.to_scene()
            if h: h.to_scene(at=to_blender(hm))
            lo, hi = g.bounds()
            cz, cy = (lo[2] + hi[2]) / 2, (lo[1] + hi[1]) / 2 + 0.03
            L = hi[2] - lo[2]
            camera(sc, gunkit.P(-3, cy, cz), gunkit.P(0, cy, cz), ortho=max(L * 1.08, (hi[1] - lo[1] + 0.1) * 1.08 * W / H))
        p = os.path.join(out_dir, '_%s_%s.png' % (mode, wid)); render(p); imgs.append(read(p, cross=mode == 'eye')); os.remove(p)
    tile(imgs, 4, os.path.join(out_dir, '%s_%s.png' % (mode, hid)))
