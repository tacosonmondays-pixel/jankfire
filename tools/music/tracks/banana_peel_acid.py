# BANANA PEEL ACID: 150 bpm hard tek / acid in C# minor (written in E minor, played 3 semitones down), a heavy
# sliding 808 under the kick, two 303s arguing, banana peels
# ripping, toys squeaking a tune in the break. joke: the beat keeps slipping (the tempo stumbles 150 -> 105 -> 150
# with a slide whistle and a bonk when it lands), and near the end it takes one huge slow-motion fall.
import numpy as np
from jf.song import Song
from jf.dsp import ns, nm, midi_hz
from jf import inst, toys, voice
from jf.kit import (gate_to_kicks, P, Reverb, Delay, Chorus, Distortion, Compressor, HighpassFilter, LowpassFilter, PeakFilter, Phaser,
                    LowShelfFilter, HighShelfFilter, steps, kicks, riff, shift, at_bar, acidpat, diatonic)

TITLE = 'Banana Peel Acid'
KEY = [4, 6, 7, 9, 11, 0, 2]  # E minor, as written (riffs move along this)
TRANSPOSE = -3  # ...sounding 3 semitones lower: C# minor
BPM = 150
TARGET = -8.0
QUALITY = 5  # busy, noisy track: q6 came out at 4.6 MB

INTRO, A, B, BREAK, DROP, FALL, DROP2, OUTRO, END = 0, 8, 24, 40, 48, 72, 76, 88, 96
SEMIS = [0, 0, -4, -2]  # E E C D, per 4 bars
SLIPS = [15, 23, 31, 39, 55, 63, 71, 83]  # bars whose last two beats stumble

ACID1 = ["E2 E2' . E3~ D3 E2 . B2' E2 . G2~ A2 E2 E3' . D3",
         "E2 E2' . E3~ D3 E2 . F2' E2 . G2~ A2 B2' . A2~ G2"]
ACID2 = ["B3' . B3 . A3~ G3 . E3 . B3' . D4~ E4 . B3 .",
         "B3' . B3 . A3~ G3 . E3 F3' . E3 . D3~ E3 . ."]
SQUEAKS = riff('G5:2 E5:2 C5:2 E5:2 G5:4 E5:4 C6:2 B5:2 G5:2 E5:2 G5:8 '    # over C
               'A5:2 F#5:2 D5:2 F#5:2 A5:4 F#5:4 D6:2 C6:2 A5:2 F#5:2 A5:8')  # over D


def tempo_map():
    tm = []
    for bar in SLIPS:  # stumble: down over a beat, back up over a beat
        b = bar * 4 + 2
        tm += [(b, BPM, 'step'), (b + 1, 105, 'ramp'), (b + 2, BPM, 'ramp')]
    f = FALL * 4
    tm += [(f + 4, BPM, 'step'), (f + 10, 55, 'ramp'), (f + 16, 55, 'step'), (f + 16.001, BPM, 'step')]
    return tm


def acid_sec(pats, bar0, bar1, octave=0):
    out = []
    for bar in range(bar0, bar1):
        out += shift(diatonic(acidpat(pats[bar % 2], bar), [0, 0, -2, -1][(bar // 4) % 4], KEY), 0, 12 * octave)  # E E C D along E minor
    return out


def build():
    s = Song(TITLE, BPM, END, tempo=tempo_map())
    s.transpose = TRANSPOSE
    say = lambda w, note, *a, **k: voice.say(w, note + TRANSPOSE, *a, **k)
    N = s.N
    s.eq = [LowShelfFilter(80, -2.0, 0.7), PeakFilter(300, -2.0, 0.8), PeakFilter(3200, 3.0, 0.6), HighShelfFilter(8000, 2.5, 0.7)]
    s.levels = dict(acid=-3.5, acid2=-5.0, bass=-5.5, toys=-6, whistle=-7, squeak=-6, vox=-5, peel=-9, hats=-11)
    s.bus('kick', 1.0, auto=[(0, 20000), (OUTRO * 4 + 16, 20000), (END * 4, 600)])
    s.bus('bass', 1.0, P([HighpassFilter(28), Compressor(-14, 3, 3, 80)]), duck=0.93, duck_rel=0.09)  # the 808
    s.bus('acid', 1.0, P([HighpassFilter(110), Distortion(4), Delay(60 / BPM * 0.75, 0.3, 0.18), Reverb(0.3, 0.5, 0.1, 0.95, 0.6)]), duck=0.45, width=0.3,
          auto=[(0, 500), (A * 4, 6000), (A * 4 + 0.01, 20000), (BREAK * 4, 20000), (BREAK * 4 + 1, 350), (DROP * 4 - 1, 12000), (DROP * 4, 20000)], res=0.45)
    s.bus('acid2', 1.0, P([HighpassFilter(150), Phaser(0.2, 0.7, 1200, 0.5, 0.5), Delay(60 / BPM * 0.5, 0.35, 0.22)]), duck=0.4, width=0.6)
    s.bus('hats', 1.0, P([HighpassFilter(700)]), duck=0.3)
    s.bus('perc', 1.0, P([HighpassFilter(500), Reverb(0.3, 0.5, 0.1, 0.95, 0.8)]), duck=0.2, width=0.5)
    s.bus('clap', 1.0, P([Reverb(0.4, 0.5, 0.25, 0.85, 0.7)]))
    s.levels.update(perc=-11)
    s.bus('vox', 1.0, P([HighpassFilter(150), Distortion(10), Delay(60 / BPM * 0.75, 0.3, 0.2), Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.2)
    s.bus('toys', 1.0, P([Reverb(0.45, 0.5, 0.2, 0.9, 1.0)]), width=0.3)
    s.bus('whistle', 1.0, P([Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]))
    s.bus('squeak', 1.0, P([HighpassFilter(400), Delay(60 / BPM * 0.75, 0.3, 0.2), Reverb(0.6, 0.5, 0.25, 0.85, 1.0)]), width=0.6)
    s.bus('peel', 1.0, P([Reverb(0.3, 0.5, 0.15, 0.9, 0.8)]))
    s.bus('fx', 1.0, P([Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.2)

    BASSROOT = [nm('E2'), nm('E2'), nm('C2'), nm('D2')]
    KICKNOTE = [nm('B1'), nm('B1'), nm('G1'), nm('A1')]  # the fifth of each chord, where a tek kick likes to sit
    root = lambda b: BASSROOT[int(b // 16) % 4]

    # ---------------- kick (tek), rumble, wonky bass
    kb = []
    for bar in list(range(4, BREAK)) + list(range(DROP, FALL + 1)) + list(range(DROP2, END)):
        if bar == FALL: kb += [bar * 4]; continue
        kb += [bar * 4 + i for i in range(4)]
    kicks(s, 'kick', kb, lambda b: KICKNOTE[int(b // 16) % 4], 'tek')
    # the 808: off the kick steps, a wonky slide up an octave or a fifth in every bar, a huge one when the fall lands
    EVEN = [(2, 0, 0), (5, 0, 0), (6, 12, 1), (10, 0, 0), (14, 0, 0)]
    ODD = [(2, 0, 0), (6, 0, 0), (10, 0, 0), (13, 0, 0), (14, 7, 1)]
    hits = []
    for bar in list(range(A, BREAK)) + list(range(DROP, FALL)) + list(range(DROP2, OUTRO)):
        for st, iv, sl in (ODD if bar % 2 else EVEN): hits.append((bar * 4 + st / 4, iv, sl))
    hits.append((FALL * 4 + 14, 0, 0))
    hits.sort()
    e8 = []
    for k, (b, iv, sl) in enumerate(hits):
        nxt = hits[k + 1][0] if k + 1 < len(hits) else b + 1
        e8.append((b, min(nxt - b, 3.0), root(b) + iv, 1.0, sl))
    s.add('bass', inst.eight08(s.notes(gate_to_kicks(s, e8)), N, decay=0.45, drive=3.2))

    # ---------------- acids
    a1 = acid_sec(ACID1, INTRO, FALL, 1) + acid_sec(ACID1, DROP2, END, 1)  # an octave up: the bass owns the low end
    s.add('acid', inst.acid(s.notes(a1), N, cut=280, envmod=3000, res=0.88, decay=0.15))
    a2 = acid_sec(ACID2, B, BREAK, 1) + acid_sec(ACID2, DROP + 8, FALL, 1) + acid_sec(ACID2, DROP2, OUTRO, 1)
    s.add('acid2', inst.acid(s.notes(a2), N, wave='square', cut=450, envmod=3800, res=0.82, decay=0.1, drive=3.0))

    # ---------------- hats, claps, perc
    for bar in range(A, END):
        if BREAK <= bar < DROP or bar == FALL + 1 or FALL + 2 <= bar < DROP2: continue
        for b, c in steps('h.o.h.oh' * 2, bar):
            s.place('hats', b, inst.openhat(0.09, 8000) if c == 'o' else inst.hat(0.025, 10000, seed=int(b * 4)), 1.0 if c == 'o' else 0.4)
        if B <= bar < BREAK or DROP <= bar < FALL or DROP2 <= bar < OUTRO:
            for b in (bar * 4 + 1, bar * 4 + 3): s.place('clap', b, inst.clap(0.2, 1400))
            for b, _ in steps('...x.....x...x..', bar): s.place('perc', b, toys.bonk(nm('E4') + TRANSPOSE + 7 * ((b * 4) % 8 == 5), 0.12), 0.5, pan=0.5 if (b * 4) % 8 == 5 else -0.5)

    # ---------------- the slips: peel rip, whistle down, bonk on landing
    for bar in SLIPS:
        b = bar * 4 + 2
        s.place('peel', b - 0.1, toys.peel(0.3, seed=bar), 1.0)
        s.add('whistle', toys.slidewhistle(float(s.t(b)), float(s.t(b + 1.8) - s.t(b)), N, 71 + TRANSPOSE, 95 + TRANSPOSE, up=False))
        s.place('toys', b + 2, toys.bonk(nm('C4') + TRANSPOSE, 0.3), 1.0)
    for bar in range(B, OUTRO, 8):
        if bar not in (BREAK,): s.place('vox', bar * 4 + 4 * 3 + 3, say('slip', 55, 1.15, bend=3), 0.8)

    # ---------------- break: toy squeak tune
    sq = at_bar(SQUEAKS[:11], BREAK) + at_bar(SQUEAKS[11:], BREAK + 4)  # break bars 40-43 are C, 44-47 are D
    for b, d, m in sq:
        s.place('squeak', b, toys.squeak(m + TRANSPOSE, min(0.25, float(s.t(b + d) - s.t(b)) * 0.95), seed=int(b * 9)), 1.0, pan=0.25 * np.sin(b))
    for bar in range(BREAK + 4, DROP):
        div = 2 if bar < BREAK + 6 else 4
        for i in range(4 * div):
            b = bar * 4 + i / div; u = (b - (BREAK + 4) * 4) / 16
            s.place('clap', b, inst.snare(0.08, 200 + u * 150, seed=i), 0.3 + 0.6 * u)
    s.place('fx', (BREAK + 4) * 4, inst.riser(float(s.t(DROP * 4) - s.t((BREAK + 4) * 4))), 0.7)
    for bar in (A, DROP, DROP2):
        s.place('fx', bar * 4, inst.crash(1.8), 0.6); s.place('fx', bar * 4, inst.impact(1.8, 23), 0.8)

    # ---------------- the big fall (slow motion): long whistle down, "aaah", a bonk, silence, back to it
    f = FALL * 4
    s.place('peel', f + 4, toys.peel(0.5, seed=99), 1.2)
    s.add('whistle', toys.slidewhistle(float(s.t(f + 4)), float(s.t(f + 14) - s.t(f + 4)), N, 64 + TRANSPOSE, 98 + TRANSPOSE, up=False, wob=0.6), 1.2)
    s.place('vox', f + 6, say('ah', 57, 1.1, dur=2.5, bend=-12, vib=0.6, slide=True), 1.0)
    s.place('toys', f + 14, toys.bonk(nm('G3') + TRANSPOSE, 0.4), 1.3)
    s.place('toys', f + 14.5, toys.boing(nm('E3') + TRANSPOSE, 0.8, up=12), 0.9)
    s.place('vox', f + 15, say('yeah', 52, 1.0, bend=-1), 0.9)
    s.place('vox', 4 * 4 + 12, say('slip', 52, 1.0), 0.8)
    return s
