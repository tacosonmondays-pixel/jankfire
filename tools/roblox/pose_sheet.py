# key poses of the Roblox viewmodels, rendered from the exported Blender weapons (roblox/assets/weapons) with the SAME
# pose maths the game uses (src/client/Viewmodel.luau: rest pose + the clip's keys from Anims; the katana's quaternion
# blend; its blade stretch per kill), seen from the player's eye with a 70 degree camera. one PNG per pose.
# run: blender52 -b --factory-startup -P tools/roblox/pose_sheet.py -- <out_dir>
import bpy, sys, os, math, json
from mathutils import Matrix, Vector, Euler, Quaternion
out = sys.argv[sys.argv.index('--') + 1:][0]
os.makedirs(out, exist_ok=True)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
A = json.load(open(os.path.join(ROOT, 'roblox/build/anims.json')))
VM = {'redline': ([0.2, -0.2, -0.37], [0, 0.04, 0], 0.72), 'marbles': ([0.18, -0.19, -0.34], [0, 0.05, 0], 0.8), 'katana': ([0.1, -0.185, -0.44], [0.85, -0.7, 0.25], 0.85)}
ADS = {'redline': [0, -0.0737 * 0.72, -0.17 - 0.1058 * 0.72], 'marbles': [0.06, min(-0.1, -0.03 - 0.1479 * 0.8), -0.3]}
EASE = {'linear': lambda u: u, 'smooth': lambda u: u * u * (3 - 2 * u), 'snap': lambda u: 1 - (1 - u) ** 3, 'in': lambda u: u ** 3,
        'back': lambda u: 1 + 2.9 * (u - 1) ** 3 + 1.9 * (u - 1) ** 2}
C = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # glTF -> blender axes

def sample(name, t, base):
    a = A[name]; keys = a['keys']
    k0, k1 = keys[0], keys[-1]
    for i in range(len(keys) - 1):
        if keys[i]['t'] <= t < keys[i + 1]['t']: k0, k1 = keys[i], keys[i + 1]; break
    span = k1['t'] - k0['t']; u = min(1, max(0, (t - k0['t']) / span)) if span > 0 else 1
    e = EASE[k1['e']](u)
    p = [k0['p'][i] + (k1['p'][i] - k0['p'][i]) * e for i in range(3)]
    if a.get('slerp'):
        sb = a['slerp']
        q0 = Euler([sb[i] + k0['r'][i] for i in range(3)], 'XYZ').to_quaternion()
        q1 = Euler([sb[i] + k1['r'][i] for i in range(3)], 'XYZ').to_quaternion()
        return p, q0.slerp(q1, e).to_matrix().to_4x4()
    r = [base[i] + k0['r'][i] + (k1['r'][i] - k0['r'][i]) * e for i in range(3)]
    return p, Euler(r, 'XYZ').to_matrix().to_4x4()

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam)
    cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(70); cam.data.clip_start = 0.01
    cam.rotation_euler = (math.radians(90), 0, 0); sc.camera = cam
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = True
    sh.background_type = 'VIEWPORT'; sh.background_color = (0.16, 0.12, 0.3)
    sc.render.resolution_x, sc.render.resolution_y = 640, 400
    return sc

def load(wid):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'roblox/assets/weapons/w_%s.glb' % wid))
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in objs: o['rest'] = [list(r) for r in o.matrix_world]
    return objs

def prop(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'roblox/assets/fx/%s.glb' % name))
    return [o for o in bpy.data.objects if o not in before and o.type == 'MESH']

def place(objs, M, kat=0):
    z0 = -0.139
    st = Matrix.Translation((0, 0, z0)) @ Matrix.Diagonal((1, 1, 1 + 0.55 * kat, 1)) @ Matrix.Translation((0, 0, -z0))
    for o in objs:
        rest = Matrix(o['rest'])
        # rest is in blender axes: back to glTF, pose there, then to blender
        g = C.inverted() @ rest
        if kat and 'kat_blade' in o.name: g = st @ g
        o.matrix_world = C @ M @ g

def pose(wid, clip=None, t=0.0, aim=0.0, kat=0):
    p0, r0, s = VM[wid]
    p, rot = [0, 0, 0], Euler(r0, 'XYZ').to_matrix().to_4x4()
    if clip:
        p, rot = sample(clip, t, r0)
    pos = Vector(p0) + Vector(p)
    if aim and wid in ADS:
        pos = pos.lerp(Vector(ADS[wid]), aim); rot = Matrix.Identity(4)
    return Matrix.Translation(pos) @ rot @ Matrix.Diagonal((s, s, s, 1))

SHOTS = [
    ('redline_rest', 'redline', None, 0, 0, 0, None), ('redline_draw', 'redline', 'draw_gun', 0.1, 0, 0, None),
    ('redline_aim', 'redline', None, 0, 1, 0, None), ('redline_reload', 'redline', 'reload_redline', 0.7, 0, 0, 'p_jerrycan'),
    ('marbles_rest', 'marbles', None, 0, 0, 0, None), ('marbles_aim', 'marbles', None, 0, 1, 0, None),
    ('marbles_reload', 'marbles', 'reload_marbles', 0.9, 0, 0, 'p_marblebag'),
    ('katana_kamae', 'katana', None, 0, 0, 0, None), ('katana_cocked', 'katana', 'swing_katana', 0.07, 0, 0, None),
    ('katana_hit', 'katana', 'swing_katana', 0.12, 0, 0, None), ('katana_through', 'katana', 'swing_katana', 0.2, 0, 0, None),
    ('katana_parry', 'katana', 'parry_katana', 0.2, 0, 0, None), ('katana_4kills', 'katana', None, 0, 0, 4, None),
]
for name, wid, clip, t, aim, kat, pr in SHOTS:
    sc = setup()
    objs = load(wid)
    M = pose(wid, clip, t, aim, kat)
    place(objs, M, kat)
    if pr: # the reload prop, where Viewmodel.luau holds it (gun-relative)
        po = prop(pr)
        s = VM[wid][2]
        if pr == 'p_jerrycan': at = Matrix.Translation((-0.05 * s, 0.12 * s, -0.06 * s)) @ Matrix.Rotation(-1.4, 4, 'Z')
        else: at = Matrix.Translation((0, 0.2 * s, -0.06 * s)) @ Matrix.Rotation(2.4, 4, 'Z')
        for o in po:
            g = C.inverted() @ o.matrix_world
            o.matrix_world = C @ M @ Matrix.Diagonal((1 / s, 1 / s, 1 / s, 1)) @ at @ Matrix.Diagonal((s, s, s, 1)) @ g
    sc.render.filepath = os.path.join(out, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('POSE', name)
