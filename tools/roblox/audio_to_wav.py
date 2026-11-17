# Blender script: decode audio files (ogg / mp3 / flac / wav) to 44.1 kHz mono 16-bit WAV with Blender's own audio
# library (aud), since this PC has no ffmpeg. Used for the Freesound downloads (tools/roblox/freesound_web.mjs).
#   blender.exe -b --factory-startup --python-exit-code 1 -P tools/roblox/audio_to_wav.py -- <inDir> <outDir>
import os
import sys

import aud

argv = sys.argv[sys.argv.index("--") + 1:]
src, dst = argv[0], argv[1]
os.makedirs(dst, exist_ok=True)
n = 0
for f in sorted(os.listdir(src)):
    if not f.lower().endswith((".ogg", ".mp3", ".flac", ".wav")):
        continue
    out = os.path.join(dst, os.path.splitext(f)[0] + ".wav")
    if os.path.exists(out):
        continue
    try:
        s = aud.Sound(os.path.join(src, f)).rechannel(1).resample(44100, False)
        s.write(out, rate=44100, channels=aud.CHANNELS_MONO, format=aud.FORMAT_S16, container=aud.CONTAINER_WAV, codec=aud.CODEC_PCM)
        n += 1
    except Exception as e:  # a file aud can't decode: skip it (and any half-written output), keep going
        print("skipped", f, e)
        if os.path.exists(out):
            os.remove(out)
print("converted", n)
