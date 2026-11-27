# every frame of a video as JPEGs (Blender's sequencer, rendered as an animation; no ffmpeg needed), for popscan.py:
#   blender -b --factory-startup -P tools/roblox/vid_all.py -- <video> <outdir> [scale%]
import bpy, sys, os
args = sys.argv[sys.argv.index('--') + 1:]
video, outdir = args[0], args[1]
pct = int(args[2]) if len(args) > 2 else 50
os.makedirs(outdir, exist_ok=True)
sc = bpy.context.scene
sc.sequence_editor_create()
seqs = sc.sequence_editor.strips if hasattr(sc.sequence_editor, 'strips') else sc.sequence_editor.sequences
strip = seqs.new_movie('v', video, 1, 1)
fps = strip.fps if hasattr(strip, 'fps') else 30
sc.render.fps = int(round(fps))
el = strip.elements[0] if hasattr(strip, 'elements') and strip.elements else None
sc.render.resolution_x = el.orig_width if el else 1808
sc.render.resolution_y = el.orig_height if el else 752
sc.render.resolution_percentage = pct
sc.render.image_settings.file_format = 'JPEG'
sc.render.image_settings.quality = 85
sc.view_settings.view_transform = 'Standard'
sc.frame_start = 1
sc.frame_end = strip.frame_final_duration
sc.render.filepath = os.path.join(outdir, 'f_')
bpy.ops.render.render(animation=True)
print('FRAMES', strip.frame_final_duration, fps)
