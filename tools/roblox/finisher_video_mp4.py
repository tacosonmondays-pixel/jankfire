# The finisher videos' cut (19 Nov): a numbered PNG sequence plus sound cues -> an H.264 MP4 (1280x720) through
# headless Blender's video sequencer. Sounds are recordings only (the owner's rule): CC0 clips from our library.
# run: blender -b --factory-startup -P tools/roblox/finisher_video_mp4.py -- <frames dir> <cues.json> <out.mp4> [fps]
#   cues.json: [{"file": path, "frame": n (0-based video frame), "vol": 0.8, "len": frames (optional), "fade": frames}]
import bpy, json, os, sys

argv = sys.argv[sys.argv.index('--') + 1:]
src, cues_p, out = argv[0], argv[1], argv[2]
fps = int(argv[3]) if len(argv) > 3 else 24
names = sorted(n for n in os.listdir(src) if n.endswith('.png'))
cues = json.load(open(cues_p)) if cues_p != '-' else []

sc = bpy.context.scene
sc.render.fps = fps
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.resolution_percentage = 100
sc.frame_start, sc.frame_end = 1, len(names)
se = sc.sequence_editor_create()
st = se.strips
img = st.new_image('frames', os.path.join(src, names[0]), 1, 1)
for n in names[1:]:
    img.elements.append(n)
for i, c in enumerate(cues):
    s = st.new_sound(f'sfx{i}', c['file'], 2 + i, 1 + int(c['frame']))
    s.volume = c.get('vol', 1.0)
    if c.get('len'):
        s.frame_final_duration = int(c['len'])
    if c.get('fade'):
        # a short fade out at the end of the strip
        end = s.frame_final_end
        s.volume = c.get('vol', 1.0)
        s.keyframe_insert('volume', frame=end - int(c['fade']))
        s.volume = 0.0
        s.keyframe_insert('volume', frame=end)

ims = sc.render.image_settings
try:
    ims.media_type = 'VIDEO'
except Exception:
    pass
ims.file_format = 'FFMPEG'
ff = sc.render.ffmpeg
ff.format = 'MPEG4'
ff.codec = 'H264'
ff.constant_rate_factor = 'HIGH'
ff.ffmpeg_preset = 'GOOD'
ff.audio_codec = 'AAC' if cues else 'NONE'
ff.audio_bitrate = 192
ff.audio_channels = 'STEREO'
sc.render.use_sequencer = True
sc.render.filepath = out
bpy.ops.render.render(animation=True)
print('mp4', out, len(names), 'frames', len(cues), 'cues', flush=True)
