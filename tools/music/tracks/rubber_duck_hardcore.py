# RUBBER DUCK HARDCORE: 190 bpm happy hardcore stomp (Bm G D A). pitched rubber-duck squeaks play the riff,
# rave piano on the off-beats, a quack choir in the break, a duck alarm. joke: the whole thing falls into a 3/4
# waltz with a tuba ("oom-pah-pah"), the ducks waltz, one lonely squeak in the silence, then the kick comes back.
import numpy as np
from jf.song import Song, gm
from jf.dsp import ns, nm, midi_hz
from jf import inst, toys, voice
from jf.kit import (P, Reverb, Delay, Chorus, Distortion, Compressor, HighpassFilter, LowpassFilter, PeakFilter,
                    LowShelfFilter, HighShelfFilter, steps, kicks, riff, shift, at_bar)

TITLE = 'Rubber Duck Hardcore'
KEY = [2, 4, 6, 7, 9, 11, 1]  # D major / B minor
BPM = 190
TARGET = -8.0

INTRO, A, BREAK, DROP, WALTZ, DROP2, OUTRO, END = 0, 8, 24, 32, 64, 70, 94, 102
KICKNOTE = [nm('B1'), nm('G1'), nm('A1'), nm('A1')]
PIANO = [[nm('B3'), nm('D4'), nm('F#4')], [nm('B3'), nm('D4'), nm('G4')], [nm('A3'), nm('D4'), nm('F#4')], [nm('A3'), nm('C#4'), nm('E4')]]
ROOT = [nm('B2'), nm('G2'), nm('D2'), nm('A2')]

DUCKS = riff('F#5:3 F#5:3 E5:2 D5:3 E5:3 F#5:2 '
             'G5:3 F#5:3 E5:2 D5:3 B4:3 D5:2 '
             'A5:3 F#5:3 D5:2 F#5:3 A5:3 F#5:2 '
             'E5:3 E5:3 C#5:2 E5:2 F#5:2 E5:2 C#5:2')
ANTHEM = riff('D5:4 F#5:4 B5:6 A5:2 G5:4 F#5:4 E5:4 D5:4 F#5:4 A5:4 D6:6 C#6:2 E5:4 C#6:4 A5:8')
WALTZ_TUNE = riff('D5:6 F#5:2 A5:4 A5:8 F#5:4 G5:6 A5:2 B5:4 B5:8 G5:4 A5:6 G5:2 F#5:4 E5:6 F#5:2 G5:4 F#5:4 E5:4 C#5:4 D5:12')
WALTZ_CH = ['D', 'D', 'G', 'G', 'A', 'A', 'A', 'D']


def tile(r, bar0, bar1):
    out = []
    for b in range(bar0, bar1, 4): out += at_bar(r, b)
    return [n for n in out if n[0] < bar1 * 4]


def build():
    s = Song(TITLE, BPM, END, tempo=[(WALTZ * 4, 140, 'step'), (DROP2 * 4, BPM, 'step')])
    N = s.N
    s.eq = [LowShelfFilter(60, -2.0, 0.7), PeakFilter(330, -1.5, 0.8), HighShelfFilter(8000, 2.0, 0.7)]
    s.levels = dict(duck=-4.0, piano=-7, lead=-5, quack=-6, tuba=-6, siren=-11, vox=-5.5, toys=-8)
    s.bus('kick', 1.0, auto=[(0, 500), (7 * 4, 2000), (8 * 4 - 0.01, 2000), (8 * 4, 20000), (OUTRO * 4 + 16, 20000), (END * 4, 700)])
    s.bus('hats', 1.0, P([HighpassFilter(800)]), duck=0.3)
    s.bus('clap', 1.0, P([Reverb(0.35, 0.5, 0.2, 0.9, 0.7)]))
    s.bus('duck', 1.0, P([HighpassFilter(300), Delay(60 / BPM * 0.75, 0.25, 0.15), Reverb(0.4, 0.5, 0.2, 0.9, 0.8)]), duck=0.4, width=0.3)
    s.bus('piano', 1.0, P([HighpassFilter(150), Compressor(-16, 3, 2, 80), Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.6, duck_rel=0.1, width=0.5)
    s.bus('lead', 1.0, P([HighpassFilter(250), Chorus(0.5, 0.3, 7, 0, 0.4), Delay(60 / BPM * 0.75, 0.3, 0.2), Reverb(0.6, 0.5, 0.25, 0.8, 1.0)]), duck=0.6, width=0.9)
    s.bus('quack', 1.0, P([Reverb(0.5, 0.5, 0.25, 0.85, 1.0)]), width=0.6)
    s.bus('tuba', 1.0, P([Reverb(0.3, 0.5, 0.15, 0.9, 0.5)]))
    s.bus('siren', 1.0, P([HighpassFilter(300), Distortion(6), Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.5)
    s.bus('vox', 1.0, P([HighpassFilter(150), Distortion(10), Delay(60 / BPM * 0.5, 0.25, 0.18), Reverb(0.4, 0.5, 0.2, 0.9, 1.0)]), duck=0.2)
    s.bus('toys', 1.0, P([Reverb(0.45, 0.5, 0.25, 0.85, 1.0)]), width=0.5)
    s.bus('fx', 1.0, P([Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.2)
    s.bus('pad', 1.0, P([HighpassFilter(200), Chorus(0.3, 0.3, 8, 0, 0.5), Reverb(0.8, 0.5, 0.4, 0.7, 1.0)]), width=1.0, duck=0.5)

    # chord of a bar. drop 2 starts on bar 71 (after the waltz + the squeak bar), so from there the 4-bar
    # progression counts from 71, or the ducks/lead (tiled from 71) would play a bar out of step with the piano
    ph = lambda bar: (bar - (DROP2 + 1)) % 4 if bar >= DROP2 + 1 else bar % 4
    tune = lambda b: KICKNOTE[ph(int(b // 4))]
    chord = ph

    # ---------------- kick: 4/4 stomp, rolls on the phrase ends
    kb = []
    for bar in list(range(INTRO, BREAK)) + list(range(DROP, WALTZ)) + list(range(DROP2 + 1, END)):
        kb += [bar * 4 + i for i in range(4)]
        if bar % 8 == 7 and (DROP <= bar < WALTZ - 1 or DROP2 <= bar < OUTRO): kb += [bar * 4 + 3.5, bar * 4 + 3.75]
        if bar == WALTZ - 1: kb = [b for b in kb if b < bar * 4 + 2]
    kicks(s, 'kick', kb, tune, 'gabber', drive=26.0, f0=500.0, tau_a=0.22)

    # ---------------- hats / claps
    for bar in range(INTRO, END):
        if BREAK <= bar < DROP or WALTZ <= bar <= DROP2: continue
        for b, c in steps('..o...o...o...o.' if bar < A else 'h.o.h.o.h.o.h.oh', bar):
            s.place('hats', b, inst.openhat(0.11, 7500) if c == 'o' else inst.hat(0.03, 9000, seed=int(b * 4)), 1.0 if c == 'o' else 0.45)
        if DROP <= bar < WALTZ or DROP2 < bar < OUTRO:
            for b in (bar * 4 + 1, bar * 4 + 3): s.place('clap', b, inst.clap(0.2, 1600))

    # ---------------- ducks: the riff
    def duckline(notes, gain=1.0, pan=0.0):
        for b, d, m in notes:
            L = min(0.24, float(s.t(b + d) - s.t(b)) * 0.92)
            s.place('duck', b, toys.duck(m, L, seed=int(b * 8)), gain, pan=pan)
    duckline(tile(DUCKS, A, BREAK)); duckline(tile(DUCKS, DROP + 8, WALTZ)); duckline(tile(DUCKS, DROP2 + 1, OUTRO))
    duckline(shift(tile(DUCKS, DROP2 + 9, OUTRO), 0, -12), 0.6, -0.4)  # a big duck joins, an octave down
    # intro: ducks squeaking at random, getting the idea
    rng = np.random.default_rng(3)
    for bar in range(INTRO, A):
        for b, _ in steps('x..x..x.' * 2 if bar >= 4 else 'x.......x.......', bar):
            s.place('duck', b, toys.duck(int(rng.choice([71, 74, 78, 81])), 0.18, seed=int(b * 7)), 0.7, pan=rng.uniform(-0.6, 0.6))

    # ---------------- rave piano on the off-beats (FluidSynth, bright piano)
    pn = []
    for bar in list(range(A, BREAK)) + list(range(DROP, WALTZ)) + list(range(DROP2 + 1, OUTRO)):
        for b, _ in steps('..x...x...x..x.x', bar): pn.append((b, 0.22, PIANO[chord(bar)], 0.9))
    for bar in range(BREAK, DROP):
        pn += [(bar * 4, 1.5, PIANO[chord(bar)], 0.8), (bar * 4 + 1.5, 1.0, PIANO[chord(bar)], 0.6), (bar * 4 + 3, 1.0, [m + 12 for m in PIANO[chord(bar)]], 0.6)]
    s.add('piano', gm(1, s.notes(pn), N))

    # ---------------- anthem lead
    an = tile(ANTHEM, DROP, DROP + 8) + tile(ANTHEM, DROP + 16, WALTZ) + tile(ANTHEM, DROP2 + 9, OUTRO)
    s.add('lead', inst.supersaw(s.notes(an), N, cut=7000, detune=0.22, voices=7))
    s.add('pad', inst.supersaw(s.notes([(bar * 4, 4, PIANO[chord(bar)], 0.8) for bar in range(BREAK, DROP)]), N, cut=2400, a=0.25, r=0.6))

    # ---------------- break: quack choir + duck alarm + build
    for bar in range(BREAK, DROP):
        ch = PIANO[chord(bar)]
        for i, (b, k) in enumerate(((0, 0), (0.75, 1), (1.5, 2), (2.5, 1), (3, 0))):
            if bar % 2 == 1 and i > 2: continue
            s.place('quack', bar * 4 + b, toys.quack(ch[k] - 12 + (12 if bar % 2 else 0), 0.22, seed=bar * 5 + i), 0.9, pan=(k - 1) * 0.5)
    s.add('siren', inst.siren(float(s.t((BREAK + 4) * 4)), float(s.t(DROP * 4 - 1) - s.t((BREAK + 4) * 4)), N, 81, 86, rate=1.58))
    for bar in range(BREAK + 4, DROP):
        div = 2 if bar < BREAK + 6 else (4 if bar < BREAK + 7 else 8)
        for i in range(4 * div):
            b = bar * 4 + i / div; u = (b - (BREAK + 4) * 4) / 16
            s.place('clap', b, inst.snare(0.08, 210 + u * 160, seed=i), 0.25 + 0.6 * u)
    s.place('fx', (BREAK + 4) * 4, inst.riser(float(s.t(DROP * 4) - s.t((BREAK + 4) * 4))), 0.7)
    s.place('duck', DROP * 4 - 0.5, toys.duck(nm('F#5'), 0.3), 1.2)  # the squeak before the drop

    # ---------------- the duck waltz (3/4, 140 bpm, tuba + ducks)
    w0 = WALTZ * 4
    tuba, pah = [], []
    WROOT = dict(D=nm('D2'), G=nm('G1'), A=nm('A1'))
    WCH = dict(D=[nm('F#4'), nm('A4'), nm('D5')], G=[nm('G4'), nm('B4'), nm('D5')], A=[nm('E4'), nm('A4'), nm('C#5')])
    for i, c in enumerate(WALTZ_CH):
        b = w0 + i * 3
        tuba.append((b, 0.9, WROOT[c] + (7 if i % 2 else 0), 1.0))
        pah += [(b + 1, 0.4, WCH[c], 0.6), (b + 2, 0.4, WCH[c], 0.55)]
        s.place('kick', b, inst.gabber_kick(nm('A1'), 0.4, drive=12.0, tau_a=0.1), 0.5); s.kick(b)
    s.add('tuba', gm(58, s.notes(tuba), N))
    s.add('piano', gm(1, s.notes(pah), N), 0.8)
    duckline(shift(WALTZ_TUNE, w0 - WALTZ_TUNE[0][0]), 1.0)
    s.place('toys', w0 + 24 - 0.01, toys.squeak(88, 0.3), 0.9)  # the lonely squeak in the silence before drop 2 (beat 24 = the gap)
    s.place('vox', DROP2 * 4 + 2, voice.say('duck', 50, 1.0, bend=-3), 1.1)
    s.place('fx', DROP2 * 4 + 4, inst.impact(2.0, 23), 0.9); s.place('fx', DROP2 * 4 + 4, inst.crash(2.0), 0.6)

    # ---------------- drop 2: alarm, vocals
    s.add('siren', inst.siren(float(s.t((DROP2 + 17) * 4)), float(s.t(OUTRO * 4) - s.t((DROP2 + 17) * 4)), N, 78, 83, rate=3.17), 0.8)
    for bar in list(range(DROP, WALTZ, 4)) + list(range(DROP2 + 1, OUTRO, 4)):
        s.place('vox', bar * 4 + 3, voice.say('duck', 54, 1.1, bend=-2), 0.9)
    for bar in (DROP, A):
        s.place('fx', bar * 4, inst.impact(2.0, 23), 0.9); s.place('fx', bar * 4, inst.crash(2.0), 0.6)
    s.place('vox', (DROP + 15) * 4 + 2, voice.stutter('yeah', 3, gap=float(s.t(0.5) - s.t(0)), note=55, size=1.2), 0.9)
    s.place('vox', (OUTRO + 4) * 4, voice.say('duck', 47, 1.0, dur=0.5), 0.8)
    s.place('fx', (END - 1) * 4, inst.downer(1.2), 0.5)
    return s
