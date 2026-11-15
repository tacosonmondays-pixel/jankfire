# Pictures of the exported weapons under a paint (weapon_paint.py), without Studio: a side view and a view from behind
# the gun, roughly as the player holds it. For choosing colours and for before / after sheets. The lighting is
# Blender's, not Roblox's: use it to judge the palette, then look at the real thing in a Play test.
#
# run: blender -b --factory-startup -P tools/roblox/paint_preview.py -- <out_dir> [--paint calm|web] [--size 960x540]
#          roblox/assets/weapons/w_*.glb          (the EXPORTED files: pieces are named "<node>__<material>__<code>")
# writes <out_dir>/<gun>_<paint>_side.png and <gun>_<paint>_hand.png
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weapon_paint
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0]
rest = argv[1:]
def opt(name, default):
    if name in rest:
        i = rest.index(name); v = rest[i + 1]; del rest[i:i + 2]
        return v
    return default
paint = opt('--paint', weapon_paint.DEFAULT)
W, H = [int(x) for x in opt('--size', '960x540').split('x')]
samples = int(opt('--samples', '24'))
files = [a for a in rest if not a.startswith('--')]
os.makedirs(out_dir, exist_ok=True)

def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def strip(n): return n.rsplit('.', 1)[0] if '.' in n and n.rsplit('.', 1)[1].isdigit() else n

def flat_material(code):
    kind, col, alpha, _ = weapon_paint.parse(code)
    m = bpy.data.materials.get('paint_' + code) or bpy.data.materials.new('paint_' + code)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    rgb = [lin(int(col[j:j + 2], 16) / 255) for j in (0, 2, 4)]
    b.inputs['Base Color'].default_value = (*rgb, 1)
    metal, rough = {'p': (0.0, 0.45), 'r': (0.0, 0.8), 'w': (0.0, 0.55), 'm': (0.85, 0.42), 's': (1.0, 0.25), 'n': (0.0, 0.4), 'g': (0.0, 0.08)}[kind]
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    if kind == 'n':
        (b.inputs.get('Emission Color') or b.inputs.get('Emission')).default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = 3.0
    if kind == 'g':
        b.inputs['Alpha'].default_value = alpha if alpha is not None else 0.4
        if hasattr(m, 'surface_render_method'): m.surface_render_method = 'BLENDED'
    return m

def look_of_material(m):
    # enough of export_weapons.look_of to know the web code of a piece without the report: the name already has it
    return None

def setup_scene():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.20, 0.21, 0.24, 1); bg.inputs[1].default_value = 1.1
    return sc

def add_sun(rot, strength, col=(1, 1, 1)):
    d = bpy.data.lights.new('sun', 'SUN'); d.energy = strength; d.color = col; d.angle = math.radians(12)
    o = bpy.data.objects.new('sun', d); bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = [math.radians(a) for a in rot]
    return o

def camera(loc, target, ortho=None, lens=50):
    cd = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = loc
    d = (Vector(target) - Vector(loc)).normalized()
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.lens = lens
    cd.clip_start = 0.01
    bpy.context.scene.camera = co
    return co

for f in files:
    gun = os.path.splitext(os.path.basename(f))[0]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = setup_scene()
    bpy.ops.import_scene.gltf(filepath=f)
    meshes = [o for o in sc.objects if o.type == 'MESH']
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in meshes:
        for v in o.data.vertices:
            p = o.matrix_world @ v.co
            for i in range(3): lo[i] = min(lo[i], p[i]); hi[i] = max(hi[i], p[i])
        full = strip(o.name)
        parts = full.rsplit('__', 1)
        piece, name_code = (parts[0], parts[1]) if len(parts) == 2 and full.count('__') >= 2 else (full, None)
        has_tex = any(n.type == 'TEX_IMAGE' for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes)
        if name_code is None: continue
        web = name_code + ('+' if has_tex else '')
        code = web
        if paint == 'calm':
            t = weapon_paint.CALM.get(gun, {})
            code = t.get(piece) or t.get(piece.split('__', 1)[1]) or web
        if code == web: continue                      # the file's own material is the web look
        kind, col, alpha, keep = weapon_paint.parse(code)
        if keep and has_tex: continue                 # keeps its picture
        o.data.materials.clear(); o.data.materials.append(flat_material(code))
    c = (lo + hi) / 2
    size = hi - lo
    length = max(size.y, 0.2)
    add_sun((50, 0, 35), 3.2, (1.0, 0.97, 0.93))
    add_sun((60, 0, -140), 1.4, (0.85, 0.9, 1.0))
    add_sun((-20, 0, 80), 0.6)
    # the exported file is pre-turned for Roblox: the muzzle points at Blender -Y, up is +Z, the gun's left is +X
    cam = camera((c.x + 3, c.y, c.z), (c.x, c.y, c.z), ortho=max(length * 1.12, size.z * 1.12 * W / H))
    sc.render.filepath = os.path.join(out_dir, '%s_%s_side.png' % (gun, paint))
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    back = hi.y
    cam = camera((c.x + 0.16 * max(1, length / 0.7), back + 0.30 * max(1, length / 0.7), hi.z + 0.13 * max(1, length / 0.7)),
                 (c.x - 0.02, back - length * 0.55, c.z + 0.02), lens=30)
    sc.render.filepath = os.path.join(out_dir, '%s_%s_hand.png' % (gun, paint))
    bpy.ops.render.render(write_still=True)
    print('PREVIEW', gun, paint)
