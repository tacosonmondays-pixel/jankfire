# Pack several re-UV'd kit .glb files into ONE upload (27 Nov 2026): every piece is renamed "<book key>~<piece>",
# nothing else changes (positions, UVs, normals, tangents stay as reuv_glb.py wrote them). In Studio,
# studio-tools/WeaponReUV.luau R.applyPack(assetId) splits the pieces by key again and puts each new mesh on the live
# parts (MeshPart:ApplyMesh). One upload per family batch instead of one per gun.
#
#   blender -b --factory-startup -P tools/roblox/reuv_pack.py -- <out .glb> <re-UV'd w_<key>.glb> [...]
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb

argv = sys.argv[sys.argv.index('--') + 1:]
out, files = argv[0], argv[1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
n = 0
for f in files:
    key = os.path.splitext(os.path.basename(f))[0]
    key = key[2:] if key.startswith('w_') else key
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    for o in set(bpy.context.scene.objects) - before:
        if o.type == 'MESH':
            nm = o.name
            # (an artist-kit build names a piece by its node only, "body_wzA", and keeps the slot in its material;
            # the uploads and the live parts say "body_wzA__duck": put the slot back)
            if '__' not in nm and o.material_slots and o.material_slots[0].material:
                nm = nm.split('.')[0] + '__' + o.material_slots[0].material.name.split('.')[0]
            o.name = key + '~' + nm
            n += 1
objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in objs:
    if o.data.users > 1: o.data = o.data.copy()
    o.data.name = o.name   # Roblox names an imported MeshPart after the MESH, not the object (27 Nov: the first packs
                           # arrived as "trim__...001" with no key)
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in [o for o in bpy.context.scene.objects if o.type == 'EMPTY']: bpy.data.objects.remove(o)
size = rbxglb.export_glb(out, tangents=True)
print('PACK', out, 'guns', len(files), 'pieces', n, 'bytes', size)
