# Preview a wrap texture on a kit gun without Studio: headless Blender, Cycles on the CPU.
#
#   blender -b --factory-startup -P tools/roblox/wrap_preview.py -- <out_dir> <kit src .glb> <wraps dir> <mode> [--left] <wrap id> [...]
#
# mode = normal | reverse | full (the loadout's three: normal paints the _wzA pieces, reverse the _wzB ones, full
# everything but nothing else). Writes <out_dir>/<gun>__<wrap>__<mode>__fp.png (roughly the first-person view: from
# behind, above and left of the gun) and __left.png (the left side, flat on). The UVs come from gun_uvs.py, the
# exact pass the export uses; the maps and settings from <wraps dir>/wraps.json (wrap_textures.py).
import bpy, sys, os, json, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gun_uvs
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir, src, wdir, mode = argv[0], argv[1], argv[2], argv[3]
only_left = '--left' in argv  # (the side view only: quicker, for reviewing many wraps)
wraps = [a for a in argv[4:] if not a.startswith('--')]
os.makedirs(out_dir, exist_ok=True)
spec = json.load(open(os.path.join(wdir, 'wraps.json')))
gun = os.path.splitext(os.path.basename(src))[0]
wid_gun = gun[2:] if gun.startswith('w_') else gun


def P(x, y, z): return Vector((x, -z, y))  # gun frame -> Blender


def paints(md, zone):
    if md == 'full' or zone == 'ab': return True
    return zone == ('b' if md == 'reverse' else 'a')


def wrap_mat(wid):
    s = spec[wid]; m = s['maps']
    mat = bpy.data.materials.new('wrap_' + wid); mat.use_nodes = True
    nt = mat.node_tree; bs = nt.nodes['Principled BSDF']
    def img(name, colour):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(os.path.join(wdir, name))
        n.image.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
        n.interpolation = 'Cubic'
        return n
    col = img(m['color'], True)
    nt.links.new(col.outputs['Color'], bs.inputs['Base Color'])
    for key, sock in (('rough', 'Roughness'), ('metal', 'Metallic')):
        v = m.get(key)
        if isinstance(v, str): nt.links.new(img(v, False).outputs['Color'], bs.inputs[sock])
        elif v is not None: bs.inputs[sock].default_value = v
    if isinstance(m.get('normal'), str):
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nt.links.new(img(m['normal'], False).outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bs.inputs['Normal'])
    e = m.get('emit')
    if e:
        k = s.get('emissive', 1.0)
        tint = s.get('tint', 'ffffff')
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
        nt.links.new(col.outputs['Color'], mul.inputs['A'])
        mul.inputs['B'].default_value = [int(tint[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [1]
        nt.links.new(mul.outputs['Result'], bs.inputs['Emission Color'])
        if isinstance(e, str):
            em = img(e, False)
            sc = nt.nodes.new('ShaderNodeMath'); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = k
            nt.links.new(em.outputs['Color'], sc.inputs[0]); nt.links.new(sc.outputs['Value'], bs.inputs['Emission Strength'])
        else:
            bs.inputs['Emission Strength'].default_value = e * k
    return mat


def scene_setup():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 28; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    grad = w.node_tree.nodes.new('ShaderNodeTexGradient')
    tc = w.node_tree.nodes.new('ShaderNodeTexCoord')
    mp = w.node_tree.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, math.pi / 2, 0)
    ramp = w.node_tree.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.05, 0.05, 0.06, 1); ramp.color_ramp.elements[1].color = (0.75, 0.74, 0.7, 1)
    w.node_tree.links.new(tc.outputs['Generated'], mp.inputs['Vector']); w.node_tree.links.new(mp.outputs['Vector'], grad.inputs['Vector'])
    w.node_tree.links.new(grad.outputs['Fac'], ramp.inputs['Fac']); w.node_tree.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 0.9
    for loc, e, col, size in (((-1.2, 1.0, 2.2), 260, (1.0, 0.93, 0.82), 1.6), ((1.6, -1.0, 1.4), 90, (0.85, 0.9, 1.0), 2.0), ((-1.0, -2.0, 0.6), 60, (1, 1, 1), 1.5)):
        ld = bpy.data.lights.new('l', 'AREA'); ld.energy = e; ld.color = col; ld.size = size
        lo = bpy.data.objects.new('l', ld); sc.collection.objects.link(lo); lo.location = loc
        d = Vector((0, 0, 0)) - lo.location
        lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def camera(name, eye, look, lens_deg=70, ortho=None):
    cd = bpy.data.cameras.new(name)
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.sensor_fit = 'VERTICAL'; cd.angle_y = math.radians(lens_deg)
    cd.clip_start = 0.01
    co = bpy.data.objects.new(name, cd); bpy.context.scene.collection.objects.link(co)
    co.location = eye
    co.rotation_euler = (look - eye).to_track_quat('-Z', 'Y').to_euler()
    return co


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    if o.data.users > 1: o.data = o.data.copy()
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
gun_uvs.unwrap(meshes, gun_uvs.SCALE.get(wid_gun, 1.0))
scene_setup()
lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
for o in meshes:
    for v in o.data.vertices:
        g = Vector((v.co.x, v.co.z, -v.co.y))
        lo = Vector(map(min, lo, g)); hi = Vector(map(max, hi, g))
L = hi.z - lo.z
orig = {o.name: [s.material for s in o.material_slots] for o in meshes}
for wid in wraps:
    mat = wrap_mat(wid)
    for o in meshes:
        name = (o.name + ' ' + ' '.join(m.name for m in orig[o.name] if m)).lower()
        z = re.search(r'_wz([a-z]+)', name)
        zone = z.group(1) if z else 'b'
        for i, s in enumerate(o.material_slots):
            s.material = mat if paints(mode, zone) else orig[o.name][i]
    sc = bpy.context.scene
    for view, cam, res in (
        ('fp', camera('fp', P(-0.2, 0.17, 0.12), P(0.03, -0.02, lo.z + L * 0.1), 68), (1280, 720)),
        ('left', camera('left', P(-3.0, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2), P(0, (lo.y + hi.y) / 2, (lo.z + hi.z) / 2), ortho=L * 1.08), (1400, int(1400 * max(0.3, (hi.y - lo.y) * 1.25 / L)))),
    ):
        if only_left and view != 'left': continue
        sc.camera = cam; sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = os.path.join(out_dir, '%s__%s__%s__%s.png' % (wid_gun, wid, mode, view))
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)
