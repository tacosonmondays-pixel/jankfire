# JANKFIRE Blender models -> Roblox-ready .glb files (one per model, for Studio's 3D Importer / bulk import).
# What changes from the web files: the far-away `lod1` copy is dropped, every transform is applied (so each piece sits
# in the file's own frame, unrotated: MeshSwap.luau relies on that), pieces are joined per material (one MeshPart per
# material) and keep their part tag (v0/v1/v2/fence/door... from the node's `node` extra) in the name, vertex colours are
# folded into the material colour (Roblox shows a MeshPart in one colour), and every piece is checked against Roblox's
# 20k-triangle cap (decimated to fit, and reported, if over).
# run: blender -b --factory-startup -P tools/roblox/export_models.py -- <out_dir> <model.glb> [<model.glb> ...]
import bpy, sys, os, json

CAP = 20000
argv = sys.argv[sys.argv.index('--') + 1:]
out_dir, files = argv[0], argv[1:]
os.makedirs(out_dir, exist_ok=True)
report = {}

def strip(n): return n.rsplit('.', 1)[0] if '.' in n and n.rsplit('.', 1)[1].isdigit() else n

def node_tag(o):
    for p in [o] + list(iter_parents(o)):
        v = p.get('node')
        if isinstance(v, str) and v: return v
    return ''

def iter_parents(o):
    p = o.parent
    while p: yield p; p = p.parent

def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)

for f in files:
    name = os.path.splitext(os.path.basename(f))[0]
    if os.sep + 'arch' + os.sep in f: name = 'arch_' + name
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f)
    objs = list(bpy.context.scene.objects)
    # the far copy goes (and everything under it)
    far = [o for o in objs if strip(o.name) == 'lod1' or any(strip(p.name) == 'lod1' for p in iter_parents(o))]
    tags = {o.name: node_tag(o) for o in objs}
    for o in far: bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    # unparent keeping the world transform, then apply it: every piece in file space, unrotated
    bpy.ops.object.select_all(action='DESELECT')
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in [o for o in bpy.context.scene.objects if o.type != 'MESH']: bpy.data.objects.remove(o, do_unlink=True)
    # split multi-material pieces so each piece has one material
    for o in list(bpy.context.scene.objects):
        if len(o.data.materials) > 1:
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            t = tags.get(o.name, '')
            bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
            for s in bpy.context.selected_objects: tags[s.name] = t
    # fold vertex colours into the material colour (their average), one material copy per tag+material
    groups = {}
    for o in bpy.context.scene.objects:
        m = o.data.materials[0] if o.data.materials else None
        key = (tags.get(o.name, ''), strip(m.name) if m else 'none')
        groups.setdefault(key, []).append(o)
    pieces = []
    for (tag, mname), lst in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in lst: o.select_set(True)
        bpy.context.view_layer.objects.active = lst[0]
        if len(lst) > 1: bpy.ops.object.join()
        o = bpy.context.view_layer.objects.active
        o.name = (tag + '_' if tag else '') + mname
        o.data.name = o.name
        ca = o.data.color_attributes.active_color if o.data.color_attributes else None
        if ca is not None and len(ca.data):
            avg = [0.0, 0.0, 0.0]
            for d in ca.data:
                c = d.color
                for i in range(3): avg[i] += c[i]
            avg = [x / len(ca.data) for x in avg]
            m = o.data.materials[0] if o.data.materials else None
            if m is not None and m.use_nodes:
                m2 = m.copy(); m2.name = o.name; o.data.materials[0] = m2
                bsdf = next((n for n in m2.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if bsdf is not None:
                    inp = bsdf.inputs['Base Color']
                    for l in list(inp.links): m2.node_tree.links.remove(l)  # (the vertex-colour node feeding it)
                    bc = list(inp.default_value)
                    inp.default_value = (bc[0] * avg[0], bc[1] * avg[1], bc[2] * avg[2], 1.0)
            for a in list(o.data.color_attributes):
                try: o.data.color_attributes.remove(a)
                except RuntimeError: pass  # (a nameless colour attribute can't be removed; the colour is already folded in)
        n = tris(o)
        if n > CAP:
            mod = o.modifiers.new('cap', 'DECIMATE'); mod.ratio = (CAP * 0.95) / n
            bpy.ops.object.modifier_apply(modifier='cap')
        pieces.append({'name': o.name, 'tris': tris(o), 'decimated_from': n if n > CAP else None})
    out = os.path.join(out_dir, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False, export_apply=True, export_animations=False, export_yup=True)
    report[name] = {'pieces': pieces, 'tris': sum(p['tris'] for p in pieces), 'bytes': os.path.getsize(out)}
    print('EXPORTED', name, report[name]['tris'], 'tris', len(pieces), 'pieces')

with open(os.path.join(out_dir, 'export_report.json'), 'w') as fh: json.dump(report, fh, indent=1)
