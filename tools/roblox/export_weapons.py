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

# what each material looks like, as one flat colour: Roblox's Open Cloud upload drops glTF colours and textures, so the
# importer needs them from here. base colour x the average of its texture, as an sRGB hex, + the PBR numbers
def srgb(c): return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
def tex_avg(sock, depth=0):
    # the average colour (file space, already sRGB) of the image feeding this socket, and any plain colour multiplied in
    if not sock.is_linked or depth > 6: return None, None
    n = sock.links[0].from_node
    if n.type == 'TEX_IMAGE' and n.image and n.image.size[0] > 0:
        import numpy as np
        px = np.array(n.image.pixels[:], dtype=np.float32).reshape(-1, n.image.channels)
        return [float(x) for x in px[:, :3].mean(axis=0)], None
    avg, fac = None, None
    for i in n.inputs:
        if i.type != 'RGBA': continue
        if i.is_linked:
            a, f = tex_avg(i, depth + 1)
            if a is not None: avg = a
            if f is not None: fac = f
        else:
            v = list(i.default_value)[:3]
            if n.type in ('MIX', 'MIX_RGB') and not (abs(v[0] - 1) < 1e-4 and abs(v[1] - 1) < 1e-4 and abs(v[2] - 1) < 1e-4): fac = v
    return avg, fac
def look_of(m):
    out = {'color': 'a3a2a5', 'metal': 0.0, 'rough': 0.5, 'glow': 0.0, 'alpha': 1.0}
    if not m or not m.use_nodes: return out
    bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf: return out
    def val(name, d):
        i = bsdf.inputs.get(name)
        return d if i is None or i.is_linked else (i.default_value if not hasattr(i.default_value, '__len__') else list(i.default_value))
    base = bsdf.inputs['Base Color']
    if base.is_linked:
        avg, fac = tex_avg(base)
        rgb = avg if avg is not None else [0.64, 0.635, 0.647]
        if fac is not None: rgb = [rgb[i] * srgb(fac[i]) for i in range(3)]
    else:
        rgb = [srgb(c) for c in list(base.default_value)[:3]]
    out['color'] = ''.join('%02x' % max(0, min(255, round(c * 255))) for c in rgb)
    out['metal'] = round(float(val('Metallic', 0.0)), 3)
    out['rough'] = round(float(val('Roughness', 0.5)), 3)
    out['alpha'] = round(float(val('Alpha', 1.0)), 3)
    es = val('Emission Strength', 0.0)
    ec = bsdf.inputs.get('Emission Color') or bsdf.inputs.get('Emission')
    if ec is not None and not ec.is_linked and float(es) > 0 and max(list(ec.default_value)[:3]) > 0.05:
        out['glow'] = round(float(es), 3)
        out['glowColor'] = ''.join('%02x' % max(0, min(255, round(srgb(c) * 255))) for c in list(ec.default_value)[:3])
    return out

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
        pieces.append({'name': o.name, 'tris': tris(o), 'look': look_of(o.data.materials[0] if o.data.materials else None)})
    out = os.path.join(out_dir, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False, export_apply=True, export_animations=False, export_yup=True)
    report[name] = {'pieces': pieces, 'tris': sum(p['tris'] for p in pieces), 'lo': [round(x, 4) for x in lo], 'hi': [round(x, 4) for x in hi], 'bytes': os.path.getsize(out)}
    print('EXPORTED', name, report[name]['tris'], 'tris', len(pieces), 'pieces', report[name]['lo'], report[name]['hi'])

# keep the files exported earlier in the report (one run usually does a few weapons, not all of them)
rp = os.path.join(out_dir, 'export_report.json')
if os.path.exists(rp):
    with open(rp) as fh: old = json.load(fh)
    old.update(report); report = old
with open(rp, 'w') as fh: json.dump(report, fh, indent=1)
