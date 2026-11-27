# A numbered image sequence plus one sound (a recording's own audio, offset) -> an H.264/AAC mp4, in a fresh headless
# Blender (26 Nov 2026; video_letterbox.py's second pass).
#   blender -b --factory-startup -P frames_to_mp4.py -- <job.json>
#   job: {frames: dir, names: [files], sound: path or null, offset: frames the sound starts before frame 1, fps, out, w, h}
import bpy, sys, os, json
job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
sc = bpy.context.scene
se = sc.sequence_editor_create()
img = se.strips.new_image('frames', os.path.join(job['frames'], job['names'][0]), 1, 1)
for n in job['names'][1:]:
    img.elements.append(n)
if job.get('sound'):
    se.strips.new_sound('snd', job['sound'], 2, 1 - int(job.get('offset', 0)))
sc.render.fps = int(job['fps'])
sc.frame_start, sc.frame_end = 1, len(job['names'])
sc.render.resolution_x, sc.render.resolution_y = int(job['w']), int(job['h'])
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.media_type = 'VIDEO'
sc.render.ffmpeg.format = 'MPEG4'
sc.render.ffmpeg.codec = 'H264'
sc.render.ffmpeg.constant_rate_factor = 'HIGH'
sc.render.ffmpeg.audio_codec = 'AAC'
sc.render.ffmpeg.audio_bitrate = 192
sc.render.filepath = job['out']
bpy.ops.render.render(animation=True)
print('ENCODED', job['out'], len(job['names']))
