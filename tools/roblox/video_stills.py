# Stills out of a video (a Studio video_capture's .mp4, a reference clip): headless Blender loads it as a movie strip and
# renders the asked frames as JPEGs (26 Nov 2026; no ffmpeg on this PC).
#   blender -b --factory-startup -P video_stills.py -- <video> <out dir> <times in s: 0.5,1.2,... | every=<s>> [--w=960]
# Writes <out>/t<seconds>.jpg (and prints the clip's frame rate and length).
import bpy, sys, os

argv = sys.argv[sys.argv.index('--') + 1:]
VID, OUT, WHEN = argv[0], argv[1], argv[2]
W = next((int(a.split('=')[1]) for a in argv if a.startswith('--w=')), 960)
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
sc.sequence_editor_create()
strip = sc.sequence_editor.strips.new_movie('v', VID, channel=1, frame_start=1)
fps = strip.fps if hasattr(strip, 'fps') and strip.fps else 30.0
n = strip.frame_final_duration
sc.render.fps = int(round(fps))
sc.frame_start, sc.frame_end = 1, n
el = strip.elements[0] if hasattr(strip, 'elements') and len(strip.elements) else None
ow = getattr(el, 'orig_width', 0) or 1280
oh = getattr(el, 'orig_height', 0) or 720
sc.render.resolution_x, sc.render.resolution_y = W, int(W * oh / ow) // 2 * 2
# (a movie strip keeps its own pixel size: rendered smaller it shows only its middle. Scale it to the output -
# 26 Nov: stills taken at half width were the centre half of each frame, which read as a lens twice too tight)
strip.transform.scale_x = W / ow
strip.transform.scale_y = (int(W * oh / ow) // 2 * 2) / oh
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'JPEG'
print('VIDEO fps %.2f frames %d (%.2f s) %dx%d' % (fps, n, n / fps, ow, oh))
if WHEN.startswith('every='):
    step = float(WHEN.split('=')[1])
    times = [i * step for i in range(int((n / fps) / step) + 1)]
else:
    times = [float(x) for x in WHEN.split(',')]
for t in times:
    f = 1 + int(round(t * fps))
    if f > n: continue
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUT, 't%06.2f.jpg' % t)
    bpy.ops.render.render(write_still=True)
    print('STILL', t, f)
