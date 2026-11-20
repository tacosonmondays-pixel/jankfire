# High Noon's sweat drop (20 Nov 2026). The owner, on the victim's close-up: "the sweat drop is sort of just a b all can
# it be a little better?" - a teardrop instead of the glass ball: a pointed top, a full round bottom, smooth. The
# profile is the teardrop curve x = sin(t) * sin(t/2)^M, z = cos(t) (t from the tip at the top to the bottom),
# revolved round the vertical; 1 unit tall, the tip up (+Y in the .glb, as Roblox reads it). FinisherScene sizes it,
# paints it (Glass, a pale blue) and adds its highlight.
#   blender -b --factory-startup -P sweat_drop.py -- <out dir>
import bpy, bmesh, sys, os, math

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = ARGS[0] if ARGS else os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

M = 1.15     # the taper: higher = a sharper point
RINGS = 28   # profile steps, tip to bottom
SEGS = 32    # round the vertical

prof = []
for i in range(RINGS + 1):
    t = math.pi * i / RINGS
    r = math.sin(t) * math.sin(t / 2) ** M
    z = math.cos(t)
    prof.append((r, z))
# 1 unit tall, the bottom at z = 0
zmin = min(z for _, z in prof); zmax = max(z for _, z in prof)
prof = [(r / (zmax - zmin), (z - zmin) / (zmax - zmin)) for r, z in prof]

bm = bmesh.new()
tip = bm.verts.new((0, 0, prof[0][1]))
bottom = bm.verts.new((0, 0, prof[-1][1]))
rings = []
for r, z in prof[1:-1]:
    ring = [bm.verts.new((r * math.cos(2 * math.pi * k / SEGS), r * math.sin(2 * math.pi * k / SEGS), z)) for k in range(SEGS)]
    rings.append(ring)
for k in range(SEGS):
    k2 = (k + 1) % SEGS
    bm.faces.new((tip, rings[0][k], rings[0][k2]))
    for j in range(len(rings) - 1):
        bm.faces.new((rings[j][k], rings[j + 1][k], rings[j + 1][k2], rings[j][k2]))
    bm.faces.new((rings[-1][k], bottom, rings[-1][k2]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('SweatDrop')
bm.to_mesh(me)
bm.free()
for poly in me.polygons:
    poly.use_smooth = True
ob = bpy.data.objects.new('SweatDrop', me)
bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new('drop')
mat.diffuse_color = (0.85, 0.93, 1.0, 1.0)
me.materials.append(mat)
out = os.path.join(OUT, 'sweat_drop.glb')
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False, export_yup=True, export_apply=True)
w = max(math.hypot(v.co.x, v.co.y) for v in me.vertices) * 2
print('[sweat_drop] wrote', out, 'verts', len(me.vertices), 'width/height %.3f' % w)
