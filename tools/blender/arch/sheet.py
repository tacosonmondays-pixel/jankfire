# A turnaround sheet for an architecture glb: four views round it and one from above, EEVEE, the kit's textures with
# nearest filtering and the baked vertex AO multiplied in (as the game draws it), paint slots in a sample colour.
# run: blender52 -b --python tools/blender/arch/sheet.py -- public/models/arch/home.glb out.png [--res 480] [--hide v1,v2]
import bpy, sys, os, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, out = argv[0], argv[1]
RES = int(argv[argv.index('--res') + 1]) if '--res' in argv else 480
PAINT = {'siding': (1.0, 0.36, 0.64), 'roof': (0.02, 0.4, 0.38), 'trim': (0.9, 0.86, 0.78)}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
KIT = os.path.join(os.path.dirname(os.path.abspath(glb)), 'kit')
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree; bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bs: continue
    tex = m.get('tex')
    im = nt.nodes.new('ShaderNodeTexImage'); im.interpolation = 'Closest'
    if tex: im.image = bpy.data.images.load(os.path.join(KIT, tex + '.png'), check_existing=True)
    ca = nt.nodes.new('ShaderNodeVertexColor')
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1
    nt.links.new(im.outputs['Color'], mul.inputs[6]); nt.links.new(ca.outputs['Color'], mul.inputs[7])
    tint = nt.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs['Factor'].default_value = 1
    col = PAINT.get(m.get('paint')) if m.get('paint') else tuple(int(m.get('col', '#ffffff')[i:i + 2], 16) / 255 for i in (1, 3, 5))
    tint.inputs[7].default_value = (*[c ** 2.2 for c in col], 1)
    nt.links.new(mul.outputs[2], tint.inputs[6]); nt.links.new(tint.outputs[2], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 1
    if m.get('alpha'): nt.links.new(im.outputs['Alpha'], bs.inputs['Alpha'])
    if m.get('glow') or m.get('glowmap'):
        nt.links.new(im.outputs['Color'], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = 0.6 if m.get('glowmap') else 1.0
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x, sc.render.resolution_y = RES, int(RES * 0.75)
sc.render.film_transparent = False
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.32, 0.36, 0.5, 1); w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(50), 0, math.radians(35))
try: sc.eevee.taa_render_samples = 8
except Exception: pass
sc.view_settings.view_transform = 'Standard'
HIDE = set(argv[argv.index('--hide') + 1].split(',')) if '--hide' in argv else set()  # variant nodes to leave out (--hide v1,v2)
for o in [o for o in sc.objects if o.type == 'MESH' and (o.get('node') or o.name.split('|')[0]) in HIDE]: bpy.data.objects.remove(o)
meshes = [o for o in sc.objects if o.type == 'MESH']
mn = Vector((1e9,) * 3); mx = Vector((-1e9,) * 3)
for o in meshes:
    for c in o.bound_box:
        p = o.matrix_world @ Vector(c); mn = Vector(map(min, mn, p)); mx = Vector(map(max, mx, p))
if mx.z - mn.z > 60: mn.z = mx.z - 40  # a tower: frame its top
cen = (mn + mx) / 2; R = (mx - mn).length / 2
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 35
shots = []
for i, (az, el) in enumerate(((-35, 18), (35, 18), (145, 18), (215, 18), (-30, 55))):
    a, e = math.radians(az), math.radians(el)
    d = R * 1.9
    cam.location = cen + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d
    cam.rotation_euler = (cen - cam.location).to_track_quat('-Z', 'Y').to_euler()
    p = out.replace('.png', f'_{i}.png'); sc.render.filepath = p
    bpy.ops.render.render(write_still=True); shots.append(p)
print('SHOTS', ' '.join(shots))
