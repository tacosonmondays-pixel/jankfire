# Before/after cells of the utility items (headless Blender, Cycles CPU): each item alone in a square, framed by its
# own size, a calm grey studio. For the owner's pick sheets; item_sheet_tile.py lays the cells out.
#
#   blender -b --factory-startup -P tools/roblox/item_sheet.py -- <out_dir> <id ...>
#
# writes <out_dir>/<id>_before.png (item_models.py: the first models), <id>_after.png and <id>_after_back.png
# (item_models2.py), plus <id>_hand.png: the new one from about where first person sees it (behind and above)
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import item_models as old
import item_models2 as new

OLD_ID = {'quiz': 'calc'}
SIZE = 520


def render(g, path, view, objs=None):
    """objs: the item already in a fresh scene (a caller that changed its materials): render those as they are"""
    if objs is None:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        objs = g.to_scene()
    sc = bpy.context.scene
    lo, hi = g.bounds()
    # (the item frame -> Blender: x, -z, y)
    c = Vector(((lo[0] + hi[0]) / 2, -(lo[2] + hi[2]) / 2, (lo[1] + hi[1]) / 2))
    rad = 0.5 * (Vector(hi) - Vector(lo)).length
    d = Vector(view).normalized()
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    sc.collection.objects.link(cam)
    cam.data.lens = 60
    cam.data.clip_start = rad * 0.02
    cam.data.clip_end = rad * 50
    half = math.atan(18 / 60)
    dist = rad / math.sin(half) * 1.04
    cam.location = c + d * dist
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    # key up-left of the camera, a fill from the other side, a rim from behind (all relative to the view)
    right = d.cross(Vector((0, 0, 1))).normalized()
    for off, e, s in (((-0.9, 0.5, 1.0), 55, 1.4), ((1.0, 0.6, 0.2), 16, 1.6), ((0.2, -1.4, 0.9), 26, 1.2)):
        pos = c + (right * off[0] + d * off[1] + Vector((0, 0, 1)) * off[2]).normalized() * dist * 1.3
        l = bpy.data.objects.new('l', bpy.data.lights.new('l', 'AREA'))
        l.data.energy = e * (dist * 1.3) ** 2 / 9.0
        l.data.size = s * rad * 2
        l.location = pos
        l.rotation_euler = (c - pos).to_track_quat('-Z', 'Y').to_euler()
        sc.collection.objects.link(l)
    w = bpy.data.worlds.new('w')
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.42, 0.44, 0.47, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
    sc.world = w
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 28; sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = SIZE
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


# views in Blender's frame (item front = -z = Blender +y): front-left-above, back-right-above, first person
FRONT = (-0.62, 0.72, 0.42)
BACK = (0.66, -0.68, 0.4)
HAND = (0.25, -0.85, 0.75)

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    out = argv[0]
    os.makedirs(out, exist_ok=True)
    for iid in argv[1:]:
        if iid.startswith('--'): continue
        oid = OLD_ID.get(iid, iid)
        render(old.BUILD[oid](), os.path.join(out, iid + '_before.png'), FRONT)
        render(new.BUILD2[iid](), os.path.join(out, iid + '_after.png'), FRONT)
        render(new.BUILD2[iid](), os.path.join(out, iid + '_after_back.png'), BACK)
        render(old.BUILD[oid](), os.path.join(out, iid + '_before_back.png'), BACK)
        print('CELLS', iid)
