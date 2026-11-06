# WRECKING BALL WARM-UP: 200 bpm gabber / terror in C minor, disguised as an aerobics class. a robot coach counts
# ONE TWO THREE FOUR over a cheesy synth bass at 100 bpm, and the tempo ramps up until it's 200. chains clank, the
# ball swings across the speakers, an alarm riff, hoovers. the outro is the cool-down, ramping back to 100 bpm,
# so the loop flows straight back into the warm-up.
import numpy as np
from jf.song import Song, gm
from jf.dsp import ns, nm, midi_hz
from jf import inst, toys, voice
from jf.kit import (P, Reverb, Delay, Chorus, Distortion, Compressor, HighpassFilter, LowpassFilter, PeakFilter,
                    LowShelfFilter, HighShelfFilter, steps, kicks, riff, shift, at_bar, acidpat)

TITLE = 'Wrecking Ball Warm-Up'
KEY = [0, 2, 3, 5, 7, 8, 10, 11]  # C minor (+ B for the G chord)
BPM = 200
TARGET = -8.0

WARM, A, B, BREAK, DROP, SWING, DROP2, COOL, END = 0, 8, 24, 40, 48, 72, 80, 96, 104
KICKNOTE = [nm('G1'), nm('Ab1'), nm('Bb1'), nm('G1')]
CHORDS = [[nm('C4'), nm('Eb4'), nm('G4')], [nm('C4'), nm('Eb4'), nm('Ab4')], [nm('D4'), nm('F4'), nm('Bb4')], [nm('D4'), nm('G4'), nm('B4')]]
ROOT = [nm('C2'), nm('Ab1'), nm('Bb1'), nm('G1')]

HOOVER = riff('C4:6 Eb4:2 G4:4 F4:4 Eb4:4 C4:4 Ab3:4 C4:4 Bb3:6 D4:2 F4:4 Bb4:4 G4:8 D4:4 B3:4')  # Cm Ab Bb G
# the alarm riff as chord degrees (R root, 5 fifth, 3 third, 2 step, L low fifth, 7 low seventh), filled in per chord
ALARM = "R . R 5' . R 3~ 2 R . L' . R . 7~ R"
ALARM_CH = [dict(R='C5', **{'5': 'G5', '3': 'Eb5', '2': 'D5', 'L': 'G4', '7': 'Bb4'}),
            dict(R='Ab4', **{'5': 'Eb5', '3': 'C5', '2': 'Bb4', 'L': 'Eb4', '7': 'G4'}),
            dict(R='Bb4', **{'5': 'F5', '3': 'D5', '2': 'C5', 'L': 'F4', '7': 'Ab4'}),
            dict(R='G4', **{'5': 'D5', '3': 'B4', '2': 'Ab4', 'L': 'D4', '7': 'F4'})]


def alarm_bar(bar):
    ch = ALARM_CH[bar % 4]
    toks = [t if t == '.' else ch[t[0]] + t[1:] for t in ALARM.split()]
    return acidpat(' '.join(toks), bar, gate=0.8)


def tile(r, bar0, bar1):
    out = []
    for b in range(bar0, bar1, 4): out += at_bar(r, b)
    return [n for n in out if n[0] < bar1 * 4]


def build():
    s = Song(TITLE, 100, END, tempo=[(4 * 4, 100, 'step'), (A * 4, BPM, 'ramp'), (COOL * 4, BPM, 'step'), (END * 4 - 4, 100, 'ramp')])
    N = s.N
    s.eq = [LowShelfFilter(60, -2.0, 0.7), PeakFilter(320, -1.5, 0.8), HighShelfFilter(8000, 2.0, 0.7)]
    s.levels = dict(hoover=-4.5, alarm=-5.5, coach=-3.5, aero=-7, chain=-7, whoosh=-8, stab=-6, vox=-5, siren=-11)
    s.bus('kick', 1.0)
    s.bus('hats', 1.0, P([HighpassFilter(800)]), duck=0.3)
    s.bus('clap', 1.0, P([Reverb(0.4, 0.5, 0.2, 0.9, 0.7)]))
    s.bus('hoover', 1.0, P([Chorus(0.6, 0.25, 6, 0.0, 0.4), HighpassFilter(90), Reverb(0.5, 0.6, 0.2, 0.9, 0.9)]), duck=0.75, duck_rel=0.1, width=0.4)
    s.bus('alarm', 1.0, P([HighpassFilter(250), Distortion(8), Delay(60 / BPM * 0.75, 0.25, 0.15), Reverb(0.4, 0.5, 0.15, 0.9, 0.8)]), duck=0.5, width=0.3)
    s.bus('stab', 1.0, P([HighpassFilter(180), Reverb(0.55, 0.5, 0.25, 0.8, 1.0)]), duck=0.55, width=0.5)
    s.bus('coach', 1.0, P([HighpassFilter(140), Distortion(6), Reverb(0.3, 0.5, 0.12, 0.95, 0.6)]))
    s.bus('aero', 1.0, P([HighpassFilter(45), Compressor(-14, 3, 2, 60)]), duck=0.7)
    s.bus('chain', 1.0, P([Reverb(0.5, 0.4, 0.2, 0.9, 1.0)]), width=0.4)
    s.bus('whoosh', 1.0, P([Reverb(0.6, 0.5, 0.2, 0.9, 1.0)]))
    s.bus('vox', 1.0, P([HighpassFilter(150), Distortion(10), Delay(60 / BPM * 0.5, 0.25, 0.18), Reverb(0.4, 0.5, 0.2, 0.9, 1.0)]), duck=0.2)
    s.bus('siren', 1.0, P([HighpassFilter(300), Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.5)
    s.bus('fx', 1.0, P([Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.2)

    tune = lambda b: KICKNOTE[int(b // 4) % 4]

    # ---------------- warm-up: aerobics synth bass + claps + the coach, ramping
    aero = []
    for bar in list(range(WARM, A)) + list(range(COOL, END)):
        for i in range(8):
            b = bar * 4 + i / 2
            aero.append((b, 0.4, ROOT[bar % 4] + 12 * (i % 2) + 12, 0.9))
    s.add('aero', gm(38, s.notes(aero), N))
    for bar in list(range(WARM, A)) + list(range(COOL, END)):
        for b in (bar * 4 + 1, bar * 4 + 3): s.place('clap', b, inst.clap(0.2, 1500), 0.8)
        for b, _ in steps('..x...x...x...x.', bar): s.place('hats', b, inst.openhat(0.1, 8000), 0.8)
    for bar, words in ((0, ('one', 'two', 'three', 'four')), (2, ('one', 'two', 'three', 'four')), (4, ('faster',)), (6, ('faster',))):
        for i, w in enumerate(words):
            s.place('coach', bar * 4 + i, voice.say(w, 51 if bar < 4 else 55, 1.05, seed=bar * 4 + i, bend=-2), 1.0)
    for bar, w in ((COOL, 'breathe'), (COOL + 2, 'breathe'), (COOL + 4, 'four'), (COOL + 6, 'two')):
        s.place('coach', bar * 4, voice.say(w, 48, 1.0, dur=0.7 if w == 'breathe' else None, bend=-3), 1.0)
    s.place('coach', (A - 1) * 4 + 2, voice.say('go', 55, 1.1), 1.0)
    s.place('fx', 4 * 4, inst.riser(float(s.t(A * 4) - s.t(4 * 4)), 400, 11000), 0.8)

    # ---------------- kick: 4/4 from bar 4 (rides the ramp), rolls, half-time in the swing
    kb = []
    for bar in list(range(4, BREAK)) + list(range(DROP, SWING)) + list(range(DROP2, COOL + 2)):
        kb += [bar * 4 + i for i in range(4)]
        if bar % 8 == 7 and (DROP <= bar < SWING or DROP2 <= bar < COOL): kb += [bar * 4 + 3.25, bar * 4 + 3.5, bar * 4 + 3.75]
        if bar % 4 == 3 and A <= bar < BREAK: kb += [bar * 4 + 3.5]
    for bar in range(SWING, DROP2): kb += [bar * 4, bar * 4 + 2]
    kicks(s, 'kick', kb, tune, 'gabber', drive=30.0)

    # ---------------- hats, claps
    for bar in range(A, COOL):
        if BREAK <= bar < DROP: continue
        for b, c in steps('h.o.h.o.h.o.h.oh', bar):
            s.place('hats', b, inst.openhat(0.08, 8000) if c == 'o' else inst.hat(0.025, 10000, seed=int(b * 4)), 1.0 if c == 'o' else 0.4)
        if B <= bar < BREAK or DROP <= bar < SWING or DROP2 <= bar < COOL:
            for b in (bar * 4 + 1, bar * 4 + 3): s.place('clap', b, inst.clap(0.18, 1500))

    # ---------------- alarm riff (gnarly square acid), hoover theme, stabs
    al = []
    for bar in list(range(A, BREAK)) + list(range(DROP + 8, SWING)) + list(range(DROP2, COOL)):
        al += alarm_bar(bar)
    s.add('alarm', inst.acid(s.notes(al), N, wave='square', cut=1400, envmod=4000, res=0.55, decay=0.12, drive=3.0))
    hv = tile(HOOVER, B, BREAK) + tile(HOOVER, DROP, SWING) + tile(HOOVER, DROP2 + 8, COOL)
    s.add('hoover', inst.hoover(s.notes(hv), N, dip=5.0))
    st = []
    for bar in list(range(BREAK, DROP)) + list(range(DROP, DROP + 8)) + list(range(SWING, DROP2)):
        for b, _ in steps('x..x..x...x..x..' if BREAK <= bar < DROP else 'x.....x...x.....', bar): st.append((b, 0.2, CHORDS[bar % 4], 0.9))
    s.add('stab', inst.stab(s.notes(st), N))

    # ---------------- the ball: chains + swings
    for bar in range(BREAK, DROP, 2):
        s.place('whoosh', bar * 4, toys.whoosh(float(s.t(bar * 4 + 8) - s.t(bar * 4)) * 0.95, -1 if (bar // 2) % 2 else 1, 1 if (bar // 2) % 2 else -1, seed=bar))
        s.place('chain', bar * 4, toys.chain_clank(0.35, seed=bar), 0.9, pan=-0.6 if (bar // 2) % 2 else 0.6)
    for bar in range(SWING, DROP2, 2):
        s.place('whoosh', bar * 4, toys.whoosh(float(s.t(bar * 4 + 8) - s.t(bar * 4)) * 0.95, -1 if (bar // 2) % 2 else 1, 1 if (bar // 2) % 2 else -1, seed=bar), 0.8)
    for bar in list(range(A, BREAK, 4)) + list(range(DROP, SWING, 4)) + list(range(DROP2, COOL, 4)):
        s.place('chain', bar * 4 + 3.5, toys.chain_clank(0.3, seed=bar), 0.8, pan=0.4)
    for bar in (A, DROP, DROP2):
        s.place('fx', bar * 4, inst.impact(2.2, 19), 1.0); s.place('fx', bar * 4, inst.crash(2.0), 0.6)

    # ---------------- vocals + alarm
    for bar in list(range(B, BREAK, 4)) + list(range(DROP, SWING, 4)) + list(range(DROP2, COOL, 4)):
        s.place('vox', bar * 4 + 3, voice.stutter('go', 2, gap=float(s.t(0.5) - s.t(0)), note=55, size=1.1), 0.9)
    for bar in range(BREAK + 4, DROP):
        div = 2 if bar < BREAK + 6 else (4 if bar < BREAK + 7 else 8)
        for i in range(4 * div):
            b = bar * 4 + i / div; u = (b - (BREAK + 4) * 4) / 16
            s.place('clap', b, inst.snare(0.07, 220 + u * 160, seed=i), 0.25 + 0.6 * u)
    s.place('fx', (BREAK + 4) * 4, inst.riser(float(s.t(DROP * 4) - s.t((BREAK + 4) * 4))), 0.7)
    s.add('siren', inst.siren(float(s.t((DROP2 + 8) * 4)), float(s.t(COOL * 4) - s.t((DROP2 + 8) * 4)), N, 72, 79, rate=1.6))
    s.place('coach', SWING * 4, voice.say('faster', 55, 1.05), 1.0)
    s.place('coach', (DROP2 - 1) * 4 + 2, voice.say('go', 55, 1.1), 1.0)
    s.repeat((DROP2 - 1) * 4 + 3, 1, 0.125)
    return s
