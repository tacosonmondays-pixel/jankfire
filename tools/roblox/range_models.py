# CARDBOARD CARL'S, the training hall's target lane: its props for Roblox, built from code in headless Blender (1 unit = 1 stud, Z up, the
# front faces -Y, feet / floor at z 0). one mesh per material, named "<model><n>__<kind>_<hex>": Open Cloud uploads
# drop colours, so the importer paints each piece from its name (kinds: metal chrome neon plastic glass wood fabric).
#   bc_cutout: a pop-up cardboard target the size of the game's hit boxes (body 3.1 x 4.86, head 2.3 up to 6.9)
#   bc_rangecounter: a firing counter with a little console, spent brass, an ammo tin and a drink
# run: blender -b --factory-startup -P tools/roblox/range_models.py -- <out_dir>
import bpy, bmesh, sys, os, math, random
from mathutils import Matrix

out_dir = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out_dir, exist_ok=True)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

PIECES = {}
def add(fn, kind, hexc):
    PIECES.setdefault(kind + '_' + hexc, []).append(fn)

def box(kind, hexc, sx, sy, sz, x, y, z, rot=None):
    def fn(bm):
        m = Matrix.Translation((x, y, z)) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((sx, sy, sz, 1))
        bmesh.ops.create_cube(bm, size=1.0, matrix=m)
    add(fn, kind, hexc)

def cyl(kind, hexc, r, depth, x, y, z, axis='z', segs=20, r2=None):
    def fn(bm):
        rot = Matrix.Identity(4)
        if axis == 'y': rot = Matrix.Rotation(math.pi / 2, 4, 'X')
        if axis == 'x': rot = Matrix.Rotation(math.pi / 2, 4, 'Y')
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=depth,
                              matrix=Matrix.Translation((x, y, z)) @ rot)
    add(fn, kind, hexc)

def flush(model):
    objs = []
    for i, (key, fns) in enumerate(PIECES.items()):
        bm = bmesh.new()
        for fn in fns: fn(bm)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(model + str(i) + '__' + key)
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(me.name, me)
        bpy.context.scene.collection.objects.link(ob)
        mt = bpy.data.materials.new(me.name)
        mt.use_nodes = True
        h = key.split('_')[1]
        rgb = [int(h[j:j + 2], 16) / 255 for j in (0, 2, 4)]
        lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        mt.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (lin[0], lin[1], lin[2], 1)
        me.materials.append(mt)
        objs.append(ob)
    PIECES.clear()
    out = os.path.join(out_dir, model.replace('bc_', '') + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=False, export_apply=True, export_animations=False, export_yup=True)
    tris = sum(len(p.vertices) - 2 for o in objs for p in o.data.polygons)
    print('BUILT', model, len(objs), 'pieces', tris, 'tris', out)

# ------------------------------------------------------------------ bc_cutout ("cardboard carl")
reset()
CARD, CARD2, RED, WHITE, INK, WOOD, STEEL, TAPE = 'c9a26b', 'b08a56', 'e2342b', 'f4f2ec', '17141f', '8a5a32', '2a2d38', 'ffe14d'
F = -0.14  # the printed side sits just in front of the board
box('plastic', CARD, 3.1, 0.22, 3.5, 0, 0, 2.95)             # torso
box('plastic', CARD, 1.25, 0.22, 1.25, -0.82, 0, 0.62)       # legs: two stubs, one shorter (jank)
box('plastic', CARD, 1.25, 0.22, 1.05, 0.82, 0, 0.72)
box('plastic', CARD2, 0.9, 0.2, 2.3, -1.95, 0, 3.3, Matrix.Rotation(0.22, 4, 'Y'))   # arms, slightly akimbo
box('plastic', CARD2, 0.9, 0.2, 2.3, 1.95, 0, 3.3, Matrix.Rotation(-0.22, 4, 'Y'))
cyl('plastic', CARD, 1.12, 0.22, 0, 0, 5.85, axis='y', segs=10)                      # head (a ten-sided cut)
box('plastic', CARD2, 0.7, 0.22, 0.4, 0, 0, 4.82)                                    # neck
# the bullseye on the chest and a smaller one on the forehead
cyl('plastic', RED, 1.0, 0.05, 0, F, 3.1, axis='y', segs=24)
cyl('plastic', WHITE, 0.68, 0.05, 0, F - 0.03, 3.1, axis='y', segs=24)
cyl('plastic', RED, 0.34, 0.05, 0, F - 0.06, 3.1, axis='y', segs=24)
cyl('plastic', RED, 0.3, 0.05, 0, F, 6.45, axis='y', segs=16)
# a face drawn in a hurry: one eye bigger, a flat mouth
cyl('plastic', INK, 0.2, 0.05, -0.42, F, 5.95, axis='y', segs=12)
cyl('plastic', INK, 0.13, 0.05, 0.42, F, 6.0, axis='y', segs=12)
box('plastic', INK, 0.75, 0.05, 0.1, 0.02, F, 5.35, Matrix.Rotation(0.12, 4, 'Y'))
box('plastic', TAPE, 0.9, 0.05, 0.22, -0.95, F, 4.45, Matrix.Rotation(0.5, 4, 'Y'))  # packing tape
box('plastic', TAPE, 0.7, 0.05, 0.2, 1.0, F, 1.7, Matrix.Rotation(-0.4, 4, 'Y'))
# the stand: a post behind, a steel foot with a hinge
box('wood', WOOD, 0.34, 0.34, 5.2, 0, 0.3, 2.7)
box('wood', WOOD, 2.2, 0.3, 0.3, 0, 0.3, 4.2)
box('metal', STEEL, 3.4, 1.7, 0.24, 0, 0.25, 0.12)
cyl('chrome', 'd6dbe3', 0.16, 3.0, 0, 0.3, 0.3, axis='x', segs=12)
flush('bc_cutout')

# ------------------------------------------------------------------ bc_rangecounter
reset()
box('metal', '2a2d38', 9.0, 2.4, 3.1, 0, 0, 1.55)                    # the body
box('metal', '3a3f4a', 9.0, 0.12, 2.3, 0, -1.26, 1.5)                # a front panel, proud of it
box('wood', '8a5a32', 9.5, 3.0, 0.3, 0, -0.15, 3.25)                 # the top, with an overhang toward the shooter
box('plastic', 'ffe14d', 9.5, 0.16, 0.32, 0, -1.66, 3.25)            # hazard edge
for i in range(-4, 5):                                               # ...with black chevrons on it
    box('plastic', '17141f', 0.34, 0.18, 0.34, i * 1.05, -1.67, 3.25, Matrix.Rotation(0.6, 4, 'Y'))
# the console on the right: a wedge with a lit screen
box('plastic', '17141f', 2.6, 1.5, 0.9, 3.0, 0.5, 3.85, Matrix.Rotation(-0.5, 4, 'X'))
box('neon', '37d6ff', 2.2, 0.06, 1.0, 3.0, 0.02, 4.02, Matrix.Rotation(-0.5, 4, 'X'))
box('plastic', 'ff4fd8', 0.3, 0.3, 0.2, 2.2, -0.62, 3.5)             # a big button
# spent brass, an ammo tin, a drink
random.seed(4)
for i in range(9):
    cyl('metal', 'e0b040', 0.07, 0.34, -3.6 + random.random() * 3.4, -0.9 + random.random() * 1.2, 3.47, axis='x' if i % 2 else 'y', segs=8)
box('metal', '4a5a2c', 1.6, 1.0, 0.9, -1.2, 0.6, 3.85)
box('plastic', 'ffe14d', 1.0, 0.04, 0.4, -1.2, 0.09, 3.9)
cyl('plastic', 'ff4fd8', 0.3, 0.8, 0.6, 0.5, 3.8, segs=14, r2=0.36)
cyl('plastic', 'f4f2ec', 0.05, 1.1, 0.72, 0.5, 4.3, segs=6)          # the straw
box('metal', '2a2d38', 0.4, 2.2, 0.3, -4.1, 0, 0.15)                 # feet
box('metal', '2a2d38', 0.4, 2.2, 0.3, 4.1, 0, 0.15)
flush('bc_rangecounter')
