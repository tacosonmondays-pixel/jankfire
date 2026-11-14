# the training hall's WAREHOUSE kit for Roblox, built from code in headless Blender (1 unit = 1 stud, Z up, the front
# faces -Y, the floor at z 0). the look: few big chunky shapes, every sharp edge rounded off (a 2-step bevel + weighted
# normals, so the big faces stay flat and the edges catch the light), flat colours, white light panels.
# one mesh per material, named "<model><n>__<kind>_<hex>": Open Cloud uploads drop colours, so the importer paints each
# piece from its name (kinds: plastic neon wood diamond).
#   wh_column   a fat steel column, 36 tall, light slots on two faces
#   wh_girder   a 56-long roof girder with two hanging light panels
#   wh_mezz     a 28 x 16 mezzanine deck 14 up: two front posts, the back edge sits on the wall
#   wh_rail     14 of yellow safety rail
#   wh_stairs   stairs 14 up over a run of 21, 8 wide
#   wh_rack     a bay of pallet racking, 16 x 5 x 24, loaded
#   wh_rollup   a 26 x 22 roll-up door (shut) for a wall
#   wh_van      a delivery van with a daft face
#   wh_forklift a forklift holding a pallet
#   wh_crate    a 5-stud framed crate
# run: blender -b --factory-startup -P tools/roblox/warehouse_models.py -- <out_dir>
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

# ------------------------------------------------------------------ wh_column
reset()
box('plastic', DARK, 6.4, 6.4, 3.0, 0, 0, 1.5, bevel=0.5)            # the foot
box('plastic', YEL, 5.2, 5.2, 1.5, 0, 0, 3.75, bevel=0.3)            # a safety collar
box('plastic', INK, 5.4, 5.4, 0.5, 0, 0, 3.75, bevel=0.12)           # ...with a dark band round it
box('plastic', STEEL, 4.0, 4.0, 30.5, 0, 0, 18.25, bevel=0.6)        # the shaft
box('plastic', STEEL, 10.0, 5.0, 3.0, 0, 0, 34.5, bevel=0.7)         # the head the girder sits on
for s in (-1, 1):
    box('plastic', DARK, 3.4, 3.4, 3.4, s * 3.3, 0, 31.9, bevel=0.35, rot=RY(math.pi / 4))   # a gusset each side
    box('plastic', '1f2230', 2.0, 0.36, 9.6, 0, s * 2.0, 12.0, bevel=0.12)                   # a light slot, front and back
    box('neon', LIGHT, 1.0, 0.36, 8.2, 0, s * 2.1, 12.0, bevel=0.1)
flush('wh_column')

# ------------------------------------------------------------------ wh_girder (the beam is z 2.4 .. 6.4, the lamps hang to 0)
reset()
box('plastic', STEEL, 56, 3.4, 0.8, 0, 0, 2.8, bevel=0.2)
box('plastic', STEEL, 56, 1.0, 2.6, 0, 0, 4.4, bevel=0.1)
box('plastic', STEEL, 56, 3.4, 0.8, 0, 0, 6.0, bevel=0.2)
for i in range(8):
    box('plastic', DARK, 0.8, 3.0, 2.5, -24.5 + i * 7.0, 0, 4.4, bevel=0.14)
for x in (-14, 14):
    for dx in (-4, 4): box('plastic', DARK, 0.6, 0.6, 1.6, x + dx, 0, 1.75, bevel=0.1)
    box('plastic', DARK, 12.4, 4.4, 1.0, x, 0, 0.65, bevel=0.32)
    box('neon', LIGHT, 10.8, 3.0, 0.3, x, 0, 0.14, bevel=0.1)
flush('wh_girder')

# ------------------------------------------------------------------ wh_mezz (deck top at z 14; -Y is the open side)
reset()
box('plastic', DARK, 28, 16, 1.0, 0, 0, 13.4, bevel=0.22)
box('diamond', '6a7084', 27.4, 15.4, 0.16, 0, 0, 13.94, bevel=0)
box('plastic', INK, 28.2, 0.9, 2.4, 0, -8.0, 12.9, bevel=0.28)        # the front edge beam
box('plastic', YEL, 28.3, 0.3, 0.5, 0, -8.4, 13.2, bevel=0.1)
box('plastic', DARK, 28, 1.0, 1.8, 0, 7.5, 12.5, bevel=0.2)           # the ledger on the wall side
for x in (-12, 12):
    box('plastic', STEEL, 2.4, 2.4, 12.9, x, -6.4, 6.45, bevel=0.38)
    box('plastic', DARK, 3.8, 3.8, 1.0, x, -6.4, 0.5, bevel=0.3)
    box('plastic', DARK, 3.6, 3.6, 0.9, x, -6.4, 12.45, bevel=0.25)
for x in (-9, 0, 9):
    box('plastic', DARK, 0.9, 15.2, 1.3, x, 0, 12.3, bevel=0.16)
for x in (-4.5, 4.5):
    box('plastic', INK, 7.4, 1.5, 0.5, x, -1.0, 12.7, bevel=0.14)     # two lamps under the deck
    box('neon', LIGHT, 6.6, 0.9, 0.2, x, -1.0, 12.44, bevel=0.06)
flush('wh_mezz')

# ------------------------------------------------------------------ wh_rail (stands on z 0, runs along X)
reset()
for x in (-6.5, 0, 6.5): box('plastic', YEL, 0.7, 0.7, 4.2, x, 0, 2.1, bevel=0.16)
box('plastic', YEL, 14, 0.8, 0.8, 0, 0, 4.3, bevel=0.24)
box('plastic', YEL, 14, 0.45, 0.45, 0, 0, 2.3, bevel=0.12)
box('plastic', INK, 14, 0.3, 0.8, 0, 0, 0.4, bevel=0.08)
flush('wh_rail')

# ------------------------------------------------------------------ wh_stairs (top at y 0 z 14, foot at y -21 z 0)
reset()
ang, run = math.atan2(14, 21), math.hypot(14, 21)
for s in (-1, 1):
    box('plastic', DARK, 0.8, run, 2.2, s * 4.0, -10.5, 6.3, bevel=0.2, rot=RX(ang))
    box('plastic', YEL, 0.7, run, 0.7, s * 4.0, -10.5, 11.2, bevel=0.2, rot=RX(ang))
    for y in (-1.0, -7.4, -13.8, -20.2):
        box('plastic', YEL, 0.6, 0.6, 4.0, s * 4.0, y, 14 + y * (14 / 21.0) + 2.1, bevel=0.14)
for i in range(13):
    box('plastic', '6a7084', 7.4, 1.4, 0.5, 0, -(i + 0.5) * 1.5, 13 - i - 0.25, bevel=0.14)
flush('wh_stairs')

# ------------------------------------------------------------------ wh_rack
reset()
UPR, BEAM = '2b7fa8', 'ffb02e'
for x in (-7.5, 7.5):
    for y in (-2.1, 2.1): box('plastic', UPR, 0.9, 0.9, 24, x, y, 12, bevel=0.18)
    box('plastic', UPR, 0.6, 4.2, 0.6, x, 0, 23.5, bevel=0.1)
    box('plastic', UPR, 0.6, 4.2, 0.6, x, 0, 4.5, bevel=0.1)
    box('plastic', UPR, 0.6, 4.2, 0.6, x, 0, 12.5, bevel=0.1)
for top in (1.0, 9.0, 17.0):
    for y in (-2.1, 2.1): box('plastic', BEAM, 15.4, 0.6, 1.0, 0, y, top - 0.5, bevel=0.16)
    box('wood', WOOD2, 14.6, 3.8, 0.3, 0, 0, top - 0.16, bevel=0.05)
# what's on it
carton(-4.6, 0, 1.0, 4.6, 3.8, 3.6)
crate(0.7, 0, 1.0, 4.4)
cyl('plastic', CYAN, 1.35, 4.4, 5.0, 0.2, 3.2, segs=16, bevel=0.2)
cyl('plastic', INK, 1.4, 0.5, 5.0, 0.2, 4.2, segs=16, bevel=0.08)
box('wood', WOOD2, 5.4, 4.2, 0.5, -4.2, 0, 9.25, bevel=0.06)
box('plastic', 'e8ecf4', 5.2, 4.0, 5.0, -4.2, 0, 12.0, bevel=0.45)     # a wrapped pallet
carton(1.3, 0.1, 9.0, 3.8, 3.6, 3.0, 0.08)
carton(1.2, 0.0, 12.0, 2.4, 2.4, 1.8, -0.3)
carton(5.3, -0.1, 9.0, 3.6, 3.6, 3.6, -0.06)
crate(-4.8, 0, 17.0, 4.4, 0.05)
carton(2.6, 0, 17.0, 7.0, 3.6, 2.6, 0.03)
carton(1.4, 0.1, 19.6, 2.8, 2.6, 2.0, 0.35)
flush('wh_rack')

# ------------------------------------------------------------------ wh_rollup (the wall is at y +0.7; it faces -Y)
reset()
for s in (-1, 1):
    box('plastic', DARK, 2.6, 1.6, 22, s * 11.7, 0, 11, bevel=0.36)
    box('plastic', YEL, 2.8, 1.8, 6.4, s * 11.7, 0, 3.2, bevel=0.3)
    for z in (1.6, 4.0): box('plastic', INK, 2.9, 1.9, 0.8, s * 11.7, 0, z, bevel=0.12)
box('plastic', DARK, 26, 1.8, 3.2, 0, 0, 20.4, bevel=0.42)
for i in range(9):
    box('plastic', '7d8496', 20.8, 0.6, 2.0, 0, 0.1, 1.5 + i * 2.04, bevel=0.24)
for x in (-8, -4, 0, 4, 8):
    box('plastic', INK, 3.0, 0.2, 1.4, x, -0.22, 1.5 + 5 * 2.04, bevel=0.08)
    box('neon', 'ffe9b8', 2.5, 0.2, 0.95, x, -0.28, 1.5 + 5 * 2.04, bevel=0.06)
box('plastic', INK, 20.8, 0.9, 0.5, 0, 0.1, 0.25, bevel=0.1)
box('neon', LIGHT, 12, 0.36, 0.5, 0, -0.9, 19.5, bevel=0.1)
box('plastic', PINK, 3.2, 0.3, 2.0, -9.6, -0.92, 20.7, bevel=0.14)
flush('wh_rollup')

# ------------------------------------------------------------------ wh_van (nose at -Y)
reset()
box('plastic', PINK, 10, 14, 8.6, 0, 2.55, 6.7, bevel=0.95)                # the box
box('plastic', PINK, 9.7, 6.6, 6.2, 0, -7.4, 5.5, bevel=1.1)               # the cab
for s in (-1, 1):
    box('plastic', YEL, 0.14, 12.2, 1.0, s * 5.0, 2.55, 4.6, bevel=0.04)   # a stripe down each side
    box('plastic', '1f2a3a', 0.3, 3.4, 2.3, s * 4.75, -7.2, 6.7, bevel=0.1)
    cyl('neon', 'ffe9b8', 0.8, 0.3, s * 3.3, -10.72, 4.6, axis='y', segs=14, bevel=0.08)   # eyes
    box('neon', 'ff3b3b', 0.9, 0.25, 1.8, s * 4.1, 9.5, 5.4, bevel=0.08)
    box('plastic', INK, 0.5, 0.4, 1.0, s * 5.15, -9.3, 7.0, bevel=0.12)
    for y in (-7.2, 6.2):
        cyl('plastic', INK, 2.0, 1.6, s * 4.7, y, 2.0, axis='x', segs=18, bevel=0.4)
        cyl('plastic', 'd6dbe3', 0.95, 0.3, s * 5.5, y, 2.0, axis='x', segs=12, bevel=0.08)
box('plastic', '1f2a3a', 8.2, 0.3, 2.5, 0, -10.62, 6.9, bevel=0.1)         # windscreen
box('plastic', INK, 3.8, 0.3, 0.8, 0.3, -10.72, 3.9, bevel=0.1, rot=RY(0.06))   # a flat mouth, a little crooked
box('plastic', DARK, 10.3, 1.2, 1.4, 0, -10.5, 2.8, bevel=0.36)
box('plastic', DARK, 10.3, 1.0, 1.2, 0, 9.5, 2.8, bevel=0.3)
box('plastic', INK, 0.16, 0.12, 7.2, 0, 9.56, 6.7, bevel=0)
for y in (-0.6, 6.0): box('plastic', DARK, 9.0, 0.5, 0.5, 0, y, 11.25, bevel=0.12)
for x in (-3.2, 3.4): cyl('plastic', YEL, 0.42, 11.5, x, 2.6, 11.9, axis='y', segs=10, bevel=0.1)
carton(0.1, 2.4, 11.5, 3.0, 3.0, 2.0, 0.2)
flush('wh_van')

# ------------------------------------------------------------------ wh_forklift (forks at -Y)
reset()
box('plastic', YEL, 5.0, 5.6, 3.4, 0, 0.6, 3.0, bevel=0.55)
box('plastic', DARK, 5.2, 2.2, 4.6, 0, 3.7, 3.4, bevel=0.6)
box('plastic', INK, 2.4, 2.0, 0.8, 0, 0.9, 5.1, bevel=0.26)
box('plastic', INK, 2.4, 0.6, 2.2, 0, 2.0, 6.0, bevel=0.2)
box('plastic', INK, 0.36, 0.36, 2.2, 0, -1.2, 5.6, bevel=0.1, rot=RX(0.35))
cyl('plastic', INK, 0.8, 0.26, 0, -1.6, 6.7, axis='y', segs=12, bevel=0.08)
for sx in (-2.2, 2.2):
    for y in (-1.9, 3.2): box('plastic', DARK, 0.46, 0.46, 5.4, sx, y, 7.3, bevel=0.12)
box('plastic', DARK, 5.0, 5.8, 0.46, 0, 0.65, 10.1, bevel=0.16)
cyl('neon', 'ff9a1f', 0.42, 0.6, 1.6, 2.6, 10.62, segs=12, bevel=0.1)
for s in (-1, 1):
    box('plastic', DARK, 0.7, 0.8, 10.4, s * 1.6, -2.9, 5.6, bevel=0.16)
    box('plastic', '8a909e', 0.9, 5.2, 0.36, s * 1.3, -6.2, 3.35, bevel=0.1)
    cyl('plastic', INK, 1.3, 1.1, s * 2.5, -1.6, 1.3, axis='x', segs=16, bevel=0.3)
    cyl('plastic', YEL, 0.5, 0.2, s * 3.1, -1.6, 1.3, axis='x', segs=10, bevel=0.05)
    cyl('plastic', INK, 1.0, 1.0, s * 2.3, 3.0, 1.0, axis='x', segs=16, bevel=0.26)
for z in (6.0, 10.4): box('plastic', DARK, 3.9, 0.6, 0.7, 0, -2.9, z, bevel=0.14)
box('plastic', INK, 4.2, 0.5, 2.6, 0, -3.5, 4.6, bevel=0.14)
box('wood', WOOD2, 5.2, 5.2, 0.6, 0, -6.3, 3.85, bevel=0.06)
carton(0, -6.3, 4.15, 4.6, 4.6, 3.2, 0.04)
carton(0.5, -6.0, 7.35, 2.6, 2.4, 1.8, 0.4)
flush('wh_forklift')

# ------------------------------------------------------------------ wh_crate
reset()
crate(0, 0, 0, 5.0)
box('plastic', PINK, 1.7, 0.1, 1.7, 0, -2.36, 2.5, bevel=0.03)
flush('wh_crate')
