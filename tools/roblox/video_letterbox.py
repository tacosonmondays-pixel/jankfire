# A Studio recording (video_capture's .mp4, which leaves the game's own on-screen bars out) cut to a stretch and given
# letterbox bars, with its own sound, as an H.264/AAC mp4 - through headless Blender's sequencer (26 Nov 2026).
#   blender -b --factory-startup -P video_letterbox.py -- <in.mp4> <out.mp4> <start s> <end s> [--bar=0.105] [--w=1280]
# (the bars are two black colour strips moved to the edges: an image strip of a bars PNG didn't draw in Blender 5.3)
import bpy, sys, os

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, T0, T1 = argv[0], argv[1], float(argv[2]), float(argv[3])
BAR = next((float(a.split('=')[1]) for a in argv if a.startswith('--bar=')), 0.105)
W = next((int(a.split('=')[1]) for a in argv if a.startswith('--w=')), 1280)
sc = bpy.context.scene
se = sc.sequence_editor_create()
mv = se.strips.new_movie('rec', SRC, channel=1, frame_start=1)
fps = mv.fps if getattr(mv, 'fps', 0) else 30.0
sc.render.fps = int(round(fps))
se.strips.new_sound('recsnd', SRC, channel=2, frame_start=1)
el = mv.elements[0]
ow, oh = el.orig_width or 1536, el.orig_height or 752
f0, f1 = 1 + int(round(T0 * fps)), 1 + int(round(T1 * fps))
sc.frame_start, sc.frame_end = f0, f1
H = int(W * oh / ow) // 2 * 2
sc.render.resolution_x, sc.render.resolution_y = W, H
# (scaled to the output: a movie strip keeps its own pixel size and would show only its middle)
mv.transform.scale_x, mv.transform.scale_y = W / ow, H / oh
sc.render.resolution_percentage = 100
for k, ch in (((1, 3), (-1, 4)) if BAR > 0 else ()):  # (--bar=0: the recording already has the game's own bars)
    c = se.strips.new_effect('bar%d' % ch, 'COLOR', channel=ch, frame_start=f0, length=f1 - f0 + 1)
    c.color = (0, 0, 0)
    c.blend_type = 'ALPHA_OVER'
    c.transform.scale_y = BAR
    c.transform.offset_y = k * (H / 2 - H * BAR / 2)
sc.view_settings.view_transform = 'Standard'
# (two passes: the barred frames as images first - encoded straight to H.264 the colour strips came out missing in
# Blender 5.3 - then those images and the recording's own sound into the mp4)
seq = OUT + '_frames'
os.makedirs(seq, exist_ok=True)
sc.render.image_settings.media_type = 'IMAGE'
sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = os.path.join(seq, 'f')
bpy.ops.render.render(animation=True)
names = sorted(n for n in os.listdir(seq) if n.endswith('.png'))
# (the encode runs in a fresh Blender: done in this session, the frames came out of the mp4 without their bars)
import json, subprocess
job = {'frames': seq, 'names': names, 'sound': SRC, 'offset': f0 - 1, 'fps': int(round(fps)), 'out': OUT, 'w': W, 'h': H}
jp = OUT + '_job.json'
json.dump(job, open(jp, 'w'))
here = os.path.dirname(os.path.abspath(__file__))
subprocess.run([bpy.app.binary_path, '-b', '--factory-startup', '-P', os.path.join(here, 'frames_to_mp4.py'), '--', jp], check=True)
for n in names: os.remove(os.path.join(seq, n))
os.rmdir(seq)
os.remove(jp)
print('WROTE', OUT, len(names), 'frames at', fps)
