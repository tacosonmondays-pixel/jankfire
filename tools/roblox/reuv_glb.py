# Re-UV an uploaded kit .glb in place (27 Nov 2026: the wrap UV standard changed, tools/roblox/gun_uvs.py).
#
#   blender -b --factory-startup -P tools/roblox/reuv_glb.py -- <out_dir> [--render <dir>] [--v1] <uploaded .glb> [...]
#
# Takes the EXACT file that was uploaded (roblox/assets/weapons-kit/w_<id>[@<skin>].glb: turned for Roblox, every
# piece named "<node>__<material>__<look code>"), turns it back into the gun's frame, gives the wrappable pieces new
# UVs (gun_uvs.unwrap, the gun's own SCALE), turns it for Roblox again and writes <out_dir>/<same name>.glb. Nothing
# else changes: the same pieces, names, vertices and normals, so in Studio the new meshes go onto the live parts with
# MeshPart:ApplyMesh (studio-tools/WeaponReUV.luau) and every attribute, child and paint on the parts stays.
# A piece keeps its UVs when it can't wear a wrap: neon (code n...), glass (g...) or its own picture (a code with "+").
# --render writes a check picture per gun from 3 angles (left, top, three-quarter from the stock end) with a dot-grid
# picture on every re-UV'd piece. --v1 uses the old standard (gun_uvs_v1.py: to rebuild the old-UV models).
import bpy, sys, os, re, math, importlib
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv.pop(0)
render_dir = None
if '--render' in argv:
    i = argv.index('--render'); render_dir = argv[i + 1]; del argv[i:i + 2]
v1 = '--v1' in argv
argv = [a for a in argv if a != '--v1']
uvm = importlib.import_module('gun_uvs_v1' if v1 else 'gun_uvs')
os.makedirs(out_dir, exist_ok=True)
if render_dir: os.makedirs(render_dir, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
DOTS = os.path.join(render_dir or out_dir, '_dots.png')


def wrappable(name):
    code = name.split('__')[-1] if '__' in name else ''
    code = re.sub(r'\.\d+$', '', code)
    if not code: return True
    if code[0] in 'ng': return False
    if code.endswith('+'): return False
    return True


def dots_png():
    if os.path.exists(DOTS): return
    img = bpy.data.images.new('dots', 512, 512)
    px = [0.0] * (512 * 512 * 4)
    for y in range(512):
        for x in range(512):
            cx, cy = (x % 128) - 64, (y % 128) - 64
            r = math.hypot(cx, cy)
            k = ((x // 128) + (y // 128)) % 4
            col = [(0.84, 0.25, 0.2), (0.18, 0.41, 0.77), (0.95, 0.69, 0.16), (0.2, 0.59, 0.35)][k]
            inside = 14 < r < 30
            line = (x % 128) < 2 or (y % 128) < 2
            c = col if inside else ((0.25, 0.25, 0.25) if line else (0.92, 0.9, 0.86))
            i = (y * 512 + x) * 4
            px[i:i + 4] = [c[0], c[1], c[2], 1.0]
    img.pixels = px
    img.filepath_raw = DOTS; img.file_format = 'PNG'; img.save()


def render_check(name, objs, wrap):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 10; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'
    if not sc.world:
        w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
        w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.2, 0.2, 0.22, 1)
        w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.8
    mat = bpy.data.materials.new('dots'); mat.use_nodes = True
    nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
    im = nt.nodes.new('ShaderNodeTexImage'); im.image = bpy.data.images.load(DOTS, check_existing=True)
    nt.links.new(im.outputs['Color'], bs.inputs['Base Color'])
    grey = bpy.data.materials.new('grey'); grey.use_nodes = True
    grey.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1)
    keep = {}
    for o in objs:
        keep[o.name] = [s.material for s in o.material_slots]
        m = mat if o in wrap else grey
        if not o.material_slots: o.data.materials.append(m)
        for s in o.material_slots: s.material = m
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        for v in o.data.vertices:
            q = Vector((v.co.x, v.co.z, -v.co.y)); lo = Vector(map(min, lo, q)); hi = Vector(map(max, hi, q))
    c = (lo + hi) / 2; L = max(hi.z - lo.z, 0.05); H = hi.y - lo.y
    def P(x, y, z): return Vector((x, -z, y))
    views = (('left', P(-3, c.y, c.z), L * 1.08, (900, int(900 * max(0.34, H * 1.2 / L)))),
             ('top', P(c.x - 0.02, c.y + 3, c.z + 0.001), L * 1.08, (900, 330)),
             ('q3s', P(c.x - 1.3, c.y + 1.1, c.z + 2.0), L * 0.8, (900, 560)))
    paths = []
    for v, eye, ortho, res in views:
        cd = bpy.data.cameras.new(v); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_start = 0.01
        co = bpy.data.objects.new(v, cd); sc.collection.objects.link(co)
        look = P(c.x, c.y, c.z)
        co.location = eye; co.rotation_euler = (look - eye).to_track_quat('-Z', 'Y').to_euler()
        sc.camera = co; sc.render.resolution_x, sc.render.resolution_y = res
        p = os.path.join(render_dir, '%s__%s.png' % (name, v)); sc.render.filepath = p
        bpy.ops.render.render(write_still=True); paths.append(p)
    for o in objs:
        for s, m in zip(o.material_slots, keep[o.name]): s.material = m
    return paths


if render_dir: dots_png()
for src in argv:
    name = os.path.splitext(os.path.basename(src))[0]
    gid = name[2:] if name.startswith('w_') else name
    base = gid.split('@')[0]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in objs:
        if o.data.users > 1: o.data = o.data.copy()
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in [o for o in bpy.context.scene.objects if o.type == 'EMPTY']: bpy.data.objects.remove(o)
    # back into the gun's frame (the upload turn is PRE_TURN about up: turning again by it undoes it)
    rbxglb.turn_for_roblox(objs)
    wrap = [o for o in objs if wrappable(o.name)]
    uvm.unwrap(wrap, uvm.SCALE.get(base, 1.0))
    if render_dir: render_check(name, objs, wrap)
    rbxglb.turn_for_roblox(objs)
    out = os.path.join(out_dir, name + '.glb')
    size = rbxglb.export_glb(out, tangents=True)
    print('REUV', name, 'pieces', len(objs), 'reuv', len(wrap), 'bytes', size)
