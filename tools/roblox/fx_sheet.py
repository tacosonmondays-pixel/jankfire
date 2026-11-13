# a contact sheet of the step 2 Roblox assets (the effects + the three weapons as exported), each scaled to fit its
# cell, with its name under it. Workbench (fast in the cloud's software GL).
# run: blender52 -b --factory-startup -P tools/roblox/fx_sheet.py -- <out.png> <glb> [<glb> ...]
import bpy, sys, os, math
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
out, files = argv[0], argv[1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
cols = 5
for i, f in enumerate(files):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    allnew = [o for o in bpy.data.objects if o not in before]
    new = [o for o in allnew if o.type == 'MESH']
    bpy.context.view_layer.update()
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in new:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    size = max(hi - lo); ctr = (lo + hi) / 2
    k = 1.6 / max(size, 1e-4)
    gx, gy = (i % cols) * 2.4, -(i // cols) * 2.6
    root = bpy.data.objects.new('cell%d' % i, None); sc.collection.objects.link(root)
    for o in allnew:
        if o.parent is None:
            mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
            o.location -= ctr
    # a 3/4 view: long things (guns, tracers) turned side-on to the camera
    root.rotation_euler = (math.radians(-18), 0, math.radians(-62))
    root.scale = (k, k, k)
    root.location = (gx, 0, gy)
    bpy.ops.object.text_add(location=(gx, 0, gy - 1.15)); t = bpy.context.object
    t.data.body = os.path.splitext(os.path.basename(f))[0]; t.data.align_x = 'CENTER'; t.data.size = 0.22
    t.rotation_euler = (math.pi / 2, 0, 0)
rows = (len(files) + cols - 1) // cols
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = cols * 2.4 + 0.4
cam.location = ((cols - 1) * 1.2, -10, -(rows - 1) * 1.3 - 0.25)
cam.rotation_euler = (math.radians(90), 0, 0)
sc.camera = cam
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_cavity = True; sh.show_object_outline = True
sh.background_type = 'VIEWPORT'; sh.background_color = (0.07, 0.03, 0.09)
sc.render.resolution_x = 1600; sc.render.resolution_y = int(1600 * (rows * 2.6) / (cols * 2.4 + 0.4))
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('SHEET', out)
