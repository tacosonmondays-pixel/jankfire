# Map-vote card pictures from an arena's own kit builder (18 Nov 2026). Runs tools/roblox/<map>_models.py as it is, but
# renders only the card cameras given here, at card quality (1280 x 720, more samples, denoised), with no .glb written.
# The builder's own light setup (its sky, sun, and any lamp wrapper it puts round arenakit.render_previews) is kept.
# The pictures have no text, signs or logos (shared/MapCards.luau; memory roblox-upload-content-rules).
#   blender -b --factory-startup -P tools/roblox/card_render.py -- <map>_models.py <out_dir> "name:x,y,z:tx,ty,tz:lens;..." [builder flags]
import sys, os, math, runpy
argv = sys.argv[sys.argv.index('--') + 1:]
SCRIPT, OUT, CARDS, EXTRA = argv[0], argv[1], argv[2], argv[3:]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.makedirs(OUT, exist_ok=True)
SCRIPT = SCRIPT if os.path.isabs(SCRIPT) else os.path.join(HERE, SCRIPT)
# what the builder sees: its out dir (unused: no glb), a preview dir (so its lamp wrappers switch on), --no-glb
sys.argv = [sys.argv[0], '--', os.path.join(OUT, '_tmp'), OUT, '--no-glb'] + EXTRA
import bpy
from mathutils import Vector
import arenakit as K
K.ARGS[:] = [os.path.join(OUT, '_tmp'), OUT]
K.FLAGS[:] = ['--no-glb'] + [f for f in EXTRA if f.startswith('--')]

VIEWS = []
for c in CARDS.split(';'):
    if not c.strip(): continue
    name, p, t, lens = c.split(':')
    VIEWS.append((name, tuple(float(v) for v in p.split(',')), tuple(float(v) for v in t.split(',')), float(lens)))


def render_cards(folder, views, prefix, sky=(0.55, 0.6, 0.7), sun_rot=(50, 0, -130), sun_energy=3.2):
    os.makedirs(folder, exist_ok=True)
    sc = bpy.context.scene
    cam_data = bpy.data.cameras.new('cam'); cam_data.clip_end = 8000
    cam = bpy.data.objects.new('cam', cam_data); sc.collection.objects.link(cam)
    sc.camera = cam
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = sun_energy; sun.angle = 0.15; sun.color = (1.0, 0.94, 0.86)
    so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so); so.rotation_euler = tuple(math.radians(a) for a in sun_rot)
    w = bpy.data.worlds.new('w'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (sky[0], sky[1], sky[2], 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    sc.world = w
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 96; sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception: pass
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92
    for (name, cp, tp, lens) in VIEWS:
        c = K.P @ Vector((cp[0], cp[1], cp[2], 1)); t = K.P @ Vector((tp[0], tp[1], tp[2], 1))
        cam.location = c.xyz
        cam.rotation_euler = (t.xyz - c.xyz).to_track_quat('-Z', 'Y').to_euler()
        cam_data.lens = lens
        sc.render.filepath = os.path.join(folder, 'card_%s.jpg' % name)
        bpy.ops.render.render(write_still=True)
        print('CARD', sc.render.filepath)


K.render_previews = render_cards
# a builder with its own renderer (the Forest's night) still renders at card quality: set just before every render
def _quality(scene, *a):
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 96; scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.render.image_settings.quality = 92
bpy.app.handlers.render_pre.append(_quality)
_finish = K.finish
def finish(kit, out_dir, preview_dir=None, views=(), prefix='kit', **pv):
    return _finish(kit, out_dir, OUT, VIEWS, prefix=prefix, **pv)
K.finish = finish
_write = K.write_layout
K.write_layout = lambda *a, **k: print('(card render: layout not rewritten)')
runpy.run_path(SCRIPT, run_name='__main__')
