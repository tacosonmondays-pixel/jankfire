# shared helpers for JANKFIRE's chunky Roblox models (headless Blender): boxes and cylinders with their sharp edges
# rounded off, cartons and crates, and flush(), which writes one .glb with one mesh per material named
# "<model><n>__<kind>_<hex>" (the Studio importer paints each piece from that name).
# use: sys.path.insert(0, <this folder>); from chunky import *   (the output folder is the argument after "--")
import bpy, bmesh, sys, os, math
from mathutils import Matrix, Vector

out_dir = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out_dir, exist_ok=True)

STEEL, DARK, INK, YEL, LIGHT = '5b6478', '2e3140', '17141f', 'ffe14d', 'f4f8ff'
PINK, CYAN, CARD, TAPE, WOOD, WOOD2 = 'ff4fd8', '37d6ff', 'c9a26b', 'e9d9a8', 'a8703a', '8a5a32'

PIECES = {}
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    PIECES.clear()

def _emit(key, bm, mat):
    """round off the sharp edges of one primitive, move it into place, hand it to its material's pile"""
    def fn(main, bm=bm, mat=mat):
        me = bpy.data.meshes.new('tmp')
        bm.to_mesh(me)
        me.transform(mat)
        main.from_mesh(me)
        bpy.data.meshes.remove(me)
    PIECES.setdefault(key, []).append(fn)

def _bevel(bm, amount):
    if amount <= 0: return
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > 0.9]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=amount, offset_type='OFFSET', segments=2, profile=0.5, affect='EDGES', clamp_overlap=True)

def box(kind, hexc, sx, sy, sz, x, y, z, bevel=0.2, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    _bevel(bm, min(bevel, min(sx, sy, sz) * 0.42))
    _emit(kind + '_' + hexc, bm, Matrix.Translation((x, y, z)) @ (rot or Matrix.Identity(4)))

def cyl(kind, hexc, r, depth, x, y, z, axis='z', segs=18, bevel=0.15, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    _bevel(bm, min(bevel, depth * 0.42, r * 0.42))
    rot = Matrix.Identity(4)
    if axis == 'y': rot = Matrix.Rotation(math.pi / 2, 4, 'X')
    if axis == 'x': rot = Matrix.Rotation(math.pi / 2, 4, 'Y')
    _emit(kind + '_' + hexc, bm, Matrix.Translation((x, y, z)) @ rot)

def carton(x, y, z0, w, d, h, yaw=0.0):
    """a taped cardboard box standing on z0"""
    r = Matrix.Rotation(yaw, 4, 'Z')
    box('plastic', CARD, w, d, h, x, y, z0 + h / 2, bevel=0.22, rot=r)
    box('plastic', TAPE, w * 0.2, d + 0.06, h + 0.06, x, y, z0 + h / 2, bevel=0.05, rot=r)

def crate(x, y, z0, s=4.4, yaw=0.0):
    """a framed wooden crate standing on z0"""
    r = Matrix.Rotation(yaw, 4, 'Z')
    c = Matrix.Translation((x, y, z0 + s / 2)) @ r
    def put(kind, hexc, sx, sy, sz, lx, ly, lz, bevel):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
        _bevel(bm, bevel)
        _emit(kind + '_' + hexc, bm, c @ Matrix.Translation((lx, ly, lz)))
    put('wood', WOOD, s * 0.92, s * 0.92, s * 0.92, 0, 0, 0, 0.12)
    e, t = s * 0.46, s * 0.14
    for a in (-e, e):
        for b in (-e, e):
            put('wood', WOOD2, t, t, s, a, b, 0, 0.1)
            put('wood', WOOD2, s, t, t, 0, a, b, 0.1)
            put('wood', WOOD2, t, s, t, a, 0, b, 0.1)

def flush(model):
    objs = []
    for i, (key, fns) in enumerate(PIECES.items()):
        bm = bmesh.new()
        for fn in fns: fn(bm)
        me = bpy.data.meshes.new(model + str(i) + '__' + key)
        bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(me.name, me)
        bpy.context.scene.collection.objects.link(ob)
        wn = ob.modifiers.new('wn', 'WEIGHTED_NORMAL')
        wn.keep_sharp = False
        wn.weight = 60
        mt = bpy.data.materials.new(me.name)
        mt.use_nodes = True
        h = key.split('_')[1]
        rgb = [int(h[j:j + 2], 16) / 255 for j in (0, 2, 4)]
        lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        mt.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (lin[0], lin[1], lin[2], 1)
        me.materials.append(mt)
        objs.append(ob)
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    tris = 0
    for o in objs:
        for v in o.data.vertices:
            for k in range(3):
                lo[k] = min(lo[k], v.co[k]); hi[k] = max(hi[k], v.co[k])
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    out = os.path.join(out_dir, model + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False, export_apply=True, export_animations=False, export_yup=True)
    print('BUILT %s pieces %d tris %d lo %.2f %.2f %.2f hi %.2f %.2f %.2f' % (model, len(objs), tris, lo.x, lo.y, lo.z, hi.x, hi.y, hi.z))

RX = lambda a: Matrix.Rotation(a, 4, 'X')
RY = lambda a: Matrix.Rotation(a, 4, 'Y')
