# Re-UV a LIVE mesh whose upload file is gone (27 Nov 2026: the Seraph Pistol's wing piece came from a v946 upload
# that was never kept). Read the mesh out of Studio with an EditableMesh (Edit, execute_luau; the JSON is long: return
# it in 80,000-character slices and join them), then this rebuilds it in Blender with the live per-corner normals,
# gives it new-standard UVs (gun_uvs.unwrap at the gun's scale) and writes a one-piece pack named "<key>~<piece>" for
# studio-tools/WeaponReUV.luau R.applyPack. The dump, in Studio:
#   local em = AssetService:CreateEditableMeshAsync(part.MeshContent)
#   v = { GetPosition(v) for GetVertices() }, f = { GetFaceVertices(f) as 1-based indices }, n = { GetNormal(GetFaceNormals(f)) }
#   HttpService:JSONEncode({ v = v, f = f, n = n })
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbxglb, gun_uvs
argv = sys.argv[sys.argv.index('--') + 1:]
dump, out, name, scale = argv[0], argv[1], argv[2], float(argv[3])
d = json.load(open(dump))
bpy.ops.wm.read_factory_settings(use_empty=True)
verts = [(x, -z, y) for x, y, z in d['v']]           # (Roblox / glTF y-up -> Blender z-up, as the glTF importer does)
faces = [[i - 1 for i in f] for f in d['f']]
me = bpy.data.meshes.new(name)
me.from_pydata(verts, [], faces)
me.update()
o = bpy.data.objects.new(name, me)
bpy.context.scene.collection.objects.link(o)
# the live per-corner normals
lnor = []
for f, ns in zip(faces, d['n']):
    for n in ns: lnor.append((n[0], -n[2], n[1]))
if len(lnor) == len(me.loops):
    me.normals_split_custom_set(lnor)
rbxglb.turn_for_roblox([o])        # back into the gun's frame (the upload turn is its own inverse)
gun_uvs.unwrap([o], scale)
rbxglb.turn_for_roblox([o])
o.data.name = o.name
size = rbxglb.export_glb(out, tangents=True)
lo = [min(v.co[i] for v in me.vertices) for i in range(3)]; hi = [max(v.co[i] for v in me.vertices) for i in range(3)]
print('DUMPPACK', out, len(me.vertices), 'verts', [round(h - l, 4) for l, h in zip(lo, hi)], size, 'bytes')
