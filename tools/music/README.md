# tools/music: the JANKFIRE soundtrack generator

Every generated track in `public/music/*.ogg` is a Python script in `tracks/`. Nothing is sampled: kicks, hoovers,
acid, stabs, drums, rubber ducks, kazoo, boings, the cash register and the robot "vocals" are synthesized in `jf/`.
A few instruments go through the FluidR3_GM soundfont (MIT, see `public/music/CREDITS.md`).

## Setup (once per machine)

```sh
apt-get install -y fluidsynth fluid-soundfont-gm ffmpeg
python3 -m venv /opt/music
/opt/music/bin/pip install numpy scipy numba pedalboard mido soundfile pyloudnorm matplotlib
```

## Render

```sh
/opt/music/bin/python tools/music/render.py                     # all tracks
/opt/music/bin/python tools/music/render.py spoon_fight_tekno   # one
```

Each run writes `public/music/<slug>.ogg` (Vorbis q6) and prints a JSON report; scratch files (wav, mix, spectrogram
png, `report.json`, `lengths.json`) go in `tools/music/.cache/work/` (git-ignored). Roughly 2-5 minutes per track.
Then `node tools/music/t_music.cjs <port>` (with the game server running) checks the music system in Chromium,
including that every loop file decodes to exactly its rendered length.

## How a track works

- `Song(title, bpm, bars, tempo=[(beat, bpm, 'step'|'ramp'), ...])`: a tempo map, so tempo jokes (half-speed
  sections, ramps, stumbles) move every part together.
- `s.bus(name, fx=Pedalboard([...]), duck=0..1, auto=[(beat, hz)])`: a mixer channel with effects, kick sidechain and
  lowpass automation. `s.place(bus, beat, sound)` drops a one-shot; `s.add(bus, line)` adds a whole-length line
  (hoover, acid, kazoo: legato instruments). `s.kick(beat)` registers a kick for the sidechain.
- `s.levels = {bus: LU}`: each bus's loudness while it plays, relative to the kick. The renderer sets the bus gains to
  hit these, so mixes are set by numbers, not by guessing gains.
- `s.tapestop(beat, beats)`, `s.repeat(beat, beats, slice)`: mix-level jokes (tape stop, beat-repeat stutter).
- `s.eq`: master tone. Mastering: glue compressor, EQ, gain to the loudness target (-8 LUFS), 4x-oversampled soft
  clip, a 17 kHz band-limit, a true-peak lookahead limiter, all run over two copies of the loop so the compressor
  state at the end matches the start. Every tail past the end is wrapped onto the start: the file loops seamlessly.
  The renderer re-masters lower if the encoded file's true peak is above -1.1 dBTP (Vorbis overshoots a little).

## Checks (we can't listen, so we measure)

`analyze.py` reports: integrated loudness + true peak of the encoded file (ffmpeg ebur128), the loop seam (high-band
energy across end->start vs the track's own 99th percentile, and the sample jump), band balance (compare with a
commercial-ish -4.5 dB/oct curve: sub -4.7, low -4.7, mud -9.8, mid -8.9, pres -12.7, air -16.6, fizz -19.3), the
kick vs bass overlap (bass low end inside the first 60 ms of each kick), each stem's level vs the kick, and a
spectrogram + short-term loudness picture.
