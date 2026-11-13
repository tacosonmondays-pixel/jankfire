# JANKFIRE weapon models -> Roblox-ready .glb files for Studio's 3D Importer (step 2: w_redline, w_marbles, w_katana).
# Unlike the props (export_models.py), the weapons keep their textures and one piece per node + material, named
# "<node>__<material>", so the Roblox code still finds the parts that move: the Redline's needle ("needle") and vents
# ("vents"), the katana's blade ("kat_blade", stretched with kills). Every transform is applied (each piece sits in the
# file's own frame, metres, -Z forward: the same frame as the code model in src/shared/WeaponModels.luau).
# run: blender52 -b --factory-startup -P tools/roblox/export_weapons.py -- <out_dir> <model.glb> [...]
import bpy, sys, os, json

argv = sys.argv[sys.argv.index('--') + 1:]
out_dir, files = argv[0], argv[1:]
os.makedirs(out_dir, exist_ok=True)
report = {}

def strip(n): return n.rsplit('.', 1)[0] if '.' in n and n.rsplit('.', 1)[1].isdigit() else n
def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)

for f in files:
    name = os.path.splitext(os.path.basename(f))[0]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    node_of = {o.name: strip(o.name) for o in meshes}
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
    pieces = []
    for o in list(bpy.context.scene.objects):
        node = node_of.get(o.name, strip(o.name))
        if len(o.data.materials) > 1:
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
            parts = list(bpy.context.selected_objects)
        else:
            parts = [o]
        for p in parts:
            m = p.data.materials[0] if p.data.materials else None
            p.name = node + '__' + (strip(m.name) if m else 'none')
            p.data.name = p.name
    # same node + material twice (a multi-primitive mesh): join them
    by = {}
    for o in bpy.context.scene.objects: by.setdefault(strip(o.name), []).append(o)
    for k, lst in by.items():
        if len(lst) > 1:
            bpy.ops.object.select_all(action='DESELECT')
            for o in lst: o.select_set(True)
            bpy.context.view_layer.objects.active = lst[0]
            bpy.ops.object.join()
            bpy.context.view_layer.objects.active.name = k
    lo, hi = [1e9] * 3, [-1e9] * 3
    for o in bpy.context.scene.objects:
        for v in o.data.vertices:
            # blender z-up -> glTF y-up: (x, y, z) -> (x, z, -y)
            g = (v.co.x, v.co.z, -v.co.y)
            for i in range(3): lo[i] = min(lo[i], g[i]); hi[i] = max(hi[i], g[i])
        pieces.append({'name': o.name, 'tris': tris(o)})
    out = os.path.join(out_dir, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False, export_apply=True, export_animations=False, export_yup=True)
    report[name] = {'pieces': pieces, 'tris': sum(p['tris'] for p in pieces), 'lo': [round(x, 4) for x in lo], 'hi': [round(x, 4) for x in hi], 'bytes': os.path.getsize(out)}
    print('EXPORTED', name, report[name]['tris'], 'tris', len(pieces), 'pieces', report[name]['lo'], report[name]['hi'])

with open(os.path.join(out_dir, 'export_report.json'), 'w') as fh: json.dump(report, fh, indent=1)
