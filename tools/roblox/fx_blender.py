# JANKFIRE step 2 effects for Roblox, made in Blender (owner rule 2026-11-13: new visual effects are Blender assets).
# One small .glb per effect for Studio's 3D Importer (they go in ReplicatedStorage > JankfireFX). Single material each:
# the game's code colours them (Neon glow, the weapon's colour), so no textures need uploading. Real sizes in metres;
# the code scales them. Axes (glTF / Roblox): -Z = forward / along the streak, Y up. Plus a contact sheet.
# run: blender52 -b --factory-startup -P tools/roblox/fx_blender.py -- <out_dir>
import bpy, bmesh, sys, os, math, json, random
from mathutils import Vector, Matrix

out_dir = sys.argv[sys.argv.index('--') + 1:][0]
os.makedirs(out_dir, exist_ok=True)
random.seed(7)
report = {}

def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, rgb, emit=0.0, metal=0.0, rough=0.5, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    if emit:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emit
    if alpha < 1:
        b.inputs['Alpha'].default_value = alpha
    return m

# glTF (x, y, z) -> blender (x, -z, y): build in glTF axes, convert here
def G(x, y, z): return Vector((x, -z, y))

def obj_from(name, verts, faces, m):
    me = bpy.data.meshes.new(name)
    me.from_pydata([G(*v) for v in verts], [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(m)
    for p in me.polygons: p.use_smooth = False
    return o

def export(name, smooth=False):
    for o in bpy.context.scene.objects:
        if o.type == 'MESH':
            for p in o.data.polygons: p.use_smooth = smooth
    path = os.path.join(out_dir, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_yup=True, export_apply=True, export_animations=False)
    tr = sum(len(p.vertices) - 2 for o in bpy.context.scene.objects if o.type == 'MESH' for p in o.data.polygons)
    report[name] = {'tris': tr, 'bytes': os.path.getsize(path)}
    print('FX', name, tr, 'tris')

def star(points, r_out, r_in, z=0.0, thick=0.0):
    # a flat star in the XY plane (facing +Z / back at the shooter), with a little depth so it reads from the side
    v, f = [(0, 0, z + thick)], []
    for i in range(points * 2):
        a = math.pi * 2 * i / (points * 2)
        r = r_out if i % 2 == 0 else r_in
        v.append((math.cos(a) * r, math.sin(a) * r, z))
    n = points * 2
    for i in range(n): f.append((0, 1 + i, 1 + (i + 1) % n))
    # the back face too
    v.append((0, 0, z - thick))
    c = len(v) - 1
    for i in range(n): f.append((c, 1 + (i + 1) % n, 1 + i))
    return v, f

# ------------------------------------------------------------ muzzle flash: 16-point star + two side spikes along the barrel
fresh()
m = mat('fx_flash', (1.0, 0.85, 0.45), emit=8)
v, f = star(16, 0.12, 0.05, 0, 0.006)
# a second, smaller star rotated half a point, a hair forward: the hot core
v2, f2 = star(16, 0.07, 0.03, -0.004, 0.004)
o = len(v); v += [(x * math.cos(0.1) - y * math.sin(0.1), x * math.sin(0.1) + y * math.cos(0.1), z) for x, y, z in v2]; f += [tuple(i + o for i in t) for t in f2]
# side spikes: two crossed diamonds running forward 0.4 m, 0.14 m wide at the root
for ang in (0, math.pi / 2):
    ca, sa = math.cos(ang), math.sin(ang)
    o = len(v)
    pts = [(0, 0, 0.02), (0.07, 0, -0.08), (0, 0, -0.4), (-0.07, 0, -0.08)]
    v += [(x * ca, x * sa, z) for x, _, z in pts]
    f += [(o, o + 1, o + 2, o + 3), (o + 3, o + 2, o + 1, o)]
obj_from('fx_flash_star', v, f, m)
export('fx_flash_star')

# ------------------------------------------------------------ tracer: a streak 1 m long, thickest a third of the way back
fresh()
m = mat('fx_tracer', (1.0, 0.94, 0.63), emit=6)
v, f = [], []
rings = [(0.0, 0.0), (0.06, 0.5), (0.33, 1.0), (1.0, 0.25)]
segs = 6
for z, r in rings:
    for i in range(segs):
        a = math.pi * 2 * i / segs
        v.append((math.cos(a) * 0.015 * r, math.sin(a) * 0.015 * r, -z + 0.5))
for k in range(len(rings) - 1):
    for i in range(segs):
        a, b = k * segs + i, k * segs + (i + 1) % segs
        f.append((a, b, b + segs, a + segs))
obj_from('fx_tracer', v, f, m)
export('fx_tracer', smooth=True)

# ------------------------------------------------------------ brass casing: body, a neck, the rim, a primer
fresh()
m = mat('fx_casing', (0.84, 0.66, 0.27), metal=1, rough=0.25)
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.0048, depth=0.019, location=G(0, 0, 0))
body = bpy.context.object
body.rotation_euler = (math.pi / 2, 0, 0)
bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.0048, radius2=0.0035, depth=0.004, location=G(0, 0, -0.0115))
neck = bpy.context.object; neck.rotation_euler = (-math.pi / 2, 0, 0)
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.0035, depth=0.005, location=G(0, 0, -0.016))
mouth = bpy.context.object; mouth.rotation_euler = (math.pi / 2, 0, 0)
bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.0052, depth=0.0015, location=G(0, 0, 0.0095))
rim = bpy.context.object; rim.rotation_euler = (math.pi / 2, 0, 0)
for o in (body, neck, mouth, rim): o.data.materials.append(m)
bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
body.name = 'fx_casing'
export('fx_casing', smooth=True)

# ------------------------------------------------------------ marble: a glass ball (the code picks the colour)
fresh()
m = mat('fx_marble', (0.3, 0.6, 1.0), rough=0.05, alpha=0.85)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.026)
bpy.context.object.name = 'fx_marble'; bpy.context.object.data.materials.append(m)
export('fx_marble', smooth=True)

# ------------------------------------------------------------ spark: a thin hot streak, pointed both ends (flies along -Z)
fresh()
m = mat('fx_spark', (1.0, 0.95, 0.75), emit=10)
v = [(0, 0, -0.06), (0.006, 0, 0.0), (0, 0.006, 0.0), (-0.006, 0, 0.0), (0, -0.006, 0.0), (0, 0, 0.05)]
f = [(0, 2, 1), (0, 3, 2), (0, 4, 3), (0, 1, 4), (5, 1, 2), (5, 2, 3), (5, 3, 4), (5, 4, 1)]
obj_from('fx_spark', v, f, m)
export('fx_spark')

# ------------------------------------------------------------ impact burst (the melee hit flash): a spiky ball
fresh()
m = mat('fx_impact', (1.0, 1.0, 0.9), emit=8)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.08)
o = bpy.context.object; o.name = 'fx_impact'; o.data.materials.append(m)
bm = bmesh.new(); bm.from_mesh(o.data)
for vv in bm.verts: vv.co *= random.uniform(1.6, 2.6) if random.random() < 0.35 else random.uniform(0.85, 1.05)
bm.to_mesh(o.data); bm.free()
export('fx_impact')

# ------------------------------------------------------------ parry glint: a 4-point star
fresh()
m = mat('fx_parry', (0.85, 0.97, 1.0), emit=10)
v, f = star(4, 0.15, 0.025, 0, 0.01)
obj_from('fx_parry_star', v, f, m)
export('fx_parry_star')

# ------------------------------------------------------------ dust / debris chunk: a lumpy low-poly rock
fresh()
m = mat('fx_dust', (0.48, 0.41, 0.35), rough=0.9)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.02)
o = bpy.context.object; o.name = 'fx_dust'; o.data.materials.append(m)
bm = bmesh.new(); bm.from_mesh(o.data)
for vv in bm.verts: vv.co = Vector((vv.co.x * random.uniform(0.6, 1.3), vv.co.y * random.uniform(0.6, 1.3), vv.co.z * random.uniform(0.5, 1.0)))
bm.to_mesh(o.data); bm.free()
export('fx_dust')

# ------------------------------------------------------------ reload prop: the Redline's red jerry can (tiny, with a spout)
fresh()
red, dark = mat('p_jerrycan_red', (0.78, 0.08, 0.06), rough=0.4), mat('p_jerrycan_cap', (0.1, 0.1, 0.1))
bpy.ops.mesh.primitive_cube_add(size=1, location=G(0, 0, 0)); can = bpy.context.object
can.scale = (0.035, 0.09, 0.11)  # 3.5 cm wide, 9 cm deep, 11 cm tall (blender x, y, z)
bpy.ops.object.transform_apply(scale=True)
bev = can.modifiers.new('b', 'BEVEL'); bev.width = 0.008; bev.segments = 2
can.data.materials.append(red)
bpy.ops.mesh.primitive_cube_add(size=1, location=G(0, 0.06, 0.02)); handle = bpy.context.object
handle.scale = (0.012, 0.05, 0.012); bpy.ops.object.transform_apply(scale=True); handle.data.materials.append(red)
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.008, depth=0.05, location=G(0, 0.07, -0.05)); spout = bpy.context.object
spout.rotation_euler = (math.radians(-35), 0, 0); spout.data.materials.append(dark)
for o in (can, handle, spout):
    bpy.context.view_layer.objects.active = o
    for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active = can; bpy.ops.object.join(); can.name = 'p_jerrycan'
export('p_jerrycan')

# ------------------------------------------------------------ reload prop: a net bag of marbles
fresh()
net = mat('p_marblebag', (0.9, 0.35, 0.1), rough=0.8)
bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.045, location=G(0, 0, 0)); bag = bpy.context.object
bag.scale = (1, 1, 1.25); bpy.ops.object.transform_apply(scale=True)
wf = bag.modifiers.new('net', 'WIREFRAME'); wf.thickness = 0.004
bpy.ops.object.modifier_apply(modifier='net'); bag.data.materials.append(net)
glass = mat('p_marblebag_marbles', (0.3, 0.7, 1.0), rough=0.05)
for i in range(9):
    a = i * 2.4
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.014, location=G(math.cos(a) * 0.022, -0.02 + (i // 3) * 0.02, math.sin(a) * 0.022))
    bpy.context.object.data.materials.append(glass)
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.008, depth=0.03, location=G(0, 0.065, 0)); tie = bpy.context.object; tie.data.materials.append(net)
bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active = bag; bpy.ops.object.join(); bag.name = 'p_marblebag'
export('p_marblebag', smooth=True)

with open(os.path.join(out_dir, 'export_report.json'), 'w') as fh: json.dump(report, fh, indent=1)
