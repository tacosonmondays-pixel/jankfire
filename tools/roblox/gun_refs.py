# Clean reference pictures of the base guns (the live kit, tools/roblox/gun_set.py), for drawing or generating skin
# ideas on top of them (17 Nov 2026: the owner generates skin pictures per gun, then builds them with Tripo).
#   blender -b --factory-startup -P tools/roblox/gun_refs.py -- <out_dir> [--size 1600] [<id> ...]   (no ids = all base guns)
# an id can also be a skin key (gun_set.SKINS, e.g. ar@ar_seraph; extra builder modules via JF_EXTRA).
# writes per gun, transparent PNGs, no markers or text:
#   <id>_side.png   the left side, flat on (orthographic, muzzle to the left): the side the player sees in first person
#   <id>_34.png     three-quarter from the front left and a little above (the loadout's angle)
# and prints the gun's size (metres) so a picture can be scaled back onto the model.
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Matrix, Vector, Euler
import gunkit, gun_set

ALLG = dict(gun_set.BUILD); ALLG.update(gun_set.SKINS)
argv = sys.argv[sys.argv.index('--') + 1:]
out_dir = argv[0]; rest = argv[1:]
S = 1600
if '--size' in rest: i = rest.index('--size'); S = int(rest[i + 1]); del rest[i:i + 2]
ids = rest or sorted(gun_set.BUILD)
os.makedirs(out_dir, exist_ok=True)


def reset(w, h):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'; sc.cycles.samples = 48; sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Standard'
    wd = bpy.data.worlds.new('w'); sc.world = wd; wd.use_nodes = True
    wd.node_tree.nodes['Background'].inputs[0].default_value = (0.82, 0.84, 0.88, 1)
    wd.node_tree.nodes['Background'].inputs[1].default_value = 0.6
    return sc


def sun(sc, rot, strength):
    d = bpy.data.lights.new('sun', 'SUN'); d.energy = strength; d.angle = 0.25
    o = bpy.data.objects.new('sun', d); o.rotation_euler = rot; sc.collection.objects.link(o)


def camera(sc, loc, look, ortho=None, fov_y=None, up=Vector((0, 0, 1))):
    cd = bpy.data.cameras.new('c'); o = bpy.data.objects.new('c', cd); sc.collection.objects.link(o)
    o.location = loc
    f = (Vector(look) - Vector(loc)).normalized()
    r = f.cross(up).normalized(); u = r.cross(f)
    o.rotation_euler = Matrix((r, u, -f)).transposed().to_euler()
    if ortho: cd.type = 'ORTHO'; cd.ortho_scale = ortho
    else: cd.sensor_fit = 'AUTO'; cd.angle = math.radians(fov_y or 30)
    cd.clip_start = 0.01; cd.clip_end = 100
    sc.camera = o


def shot(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


for wid in ids:
    g = ALLG[wid]()
    lo, hi = g.bounds()
    cz, cy = (lo[2] + hi[2]) / 2, (lo[1] + hi[1]) / 2
    L, Hh = hi[2] - lo[2], hi[1] - lo[1]
    # side: the frame fits the gun with 6% margin, wide guns get a wide picture
    asp = max(1.0, min(3.2, L / max(Hh, 1e-3)))
    w, h = S, max(320, round(S / asp))
    sc = reset(w, h); g.to_scene()
    sun(sc, Euler((math.radians(55), 0, math.radians(-90))), 2.6); sun(sc, Euler((math.radians(-40), 0, math.radians(-110))), 0.8)
    camera(sc, gunkit.P(-3, cy, cz), gunkit.P(0, cy, cz), ortho=max(L, Hh * w / h) * 1.06)
    shot(os.path.join(out_dir, wid + '_side.png'))
    # three-quarter
    sc = reset(round(S * 0.8), round(S * 0.6)); g.to_scene()
    sun(sc, Euler((math.radians(50), 0, math.radians(-40))), 2.6); sun(sc, Euler((math.radians(-30), 0, math.radians(140))), 0.7)
    mid = gunkit.P(0, cy, cz)
    camera(sc, mid + Vector((-0.75 * L, 0.80 * L, 0.42 * L)) * 1.5, mid, fov_y=34)
    shot(os.path.join(out_dir, wid + '_34.png'))
    print('REF', wid, 'length %.3f m, height %.3f m, width %.3f m' % (L, Hh, hi[0] - lo[0]), 'tris', g.tris())
