# SPOON FIGHT TEKNO: 155 bpm hard tek in A minor. rolling kick with a rumble tail, bouncy off-beat bass, two
# squelchy acid lines arguing, spoons clinking instead of hi-hats, robots chanting "OI". joke: halfway the beat
# stops for a western standoff (whistling, spurs, wind) at half speed, then the spoons clash and it slams back.
import numpy as np
from jf.song import Song
from jf.dsp import ns, nm, midi_hz
from jf import inst, toys, voice
from jf.kit import (P, Reverb, Delay, Chorus, Distortion, Compressor, HighpassFilter, LowpassFilter, PeakFilter,
                    LowShelfFilter, HighShelfFilter, Phaser, steps, kicks, riff, shift, at_bar, acidpat, diatonic)

TITLE = 'Spoon Fight Tekno'
KEY = [9, 11, 0, 2, 4, 5, 7]  # A minor
BPM = 155
TARGET = -8.0

INTRO, A, B, BREAK, DROP2, STANDOFF, DROP3, OUTRO, END = 0, 8, 24, 32, 40, 56, 60, 84, 92
ROOTS = [nm('A1'), nm('A1'), nm('F1'), nm('G1')]  # per 2 bars

ACID1 = ["A2 . A2 A3' . A2 C3~ D3 A2 . G2' A2 . A3~ G3 E3'",
         "A2 . A2 A3' . A2 C3~ D3 A2 . F2' F2 . F3~ E3 G2'"]
ACID2 = ["E3' E3 . D3~ C3 . A2' A3 . G3~ F3 E3' . C3 D3~ E3",
         "E3' E3 . D3~ C3 . A2' A3 . Bb3~ A3 G3' . E3 F3~ E3"]
STANDOFF_TUNE = riff('E5:4 A5:2 E5:2 A5:6 _:2 G5:2 F5:2 E5:2 D5:2 E5:6 _:2 '
                     'C5:4 D5:2 E5:2 A4:6 _:2 B4:2 C5:2 B4:2 G4:2 A4:8')


def acid_section(pats, bar0, bar1, transpose_every2=True):
    out = []
    for bar in range(bar0, bar1):
        steps_ = [0, 0, -2, -1][(bar // 2) % 4] if transpose_every2 else 0  # A A F G, moved along A minor
        out += diatonic(acidpat(pats[bar % 2], bar), steps_, KEY)
    return out


def build():
    s = Song(TITLE, BPM, END, tempo=[(STANDOFF * 4, BPM / 2, 'step'), (DROP3 * 4, BPM, 'step')])
    N = s.N
    s.eq = [LowShelfFilter(60, -3.0, 0.7), PeakFilter(300, -1.5, 0.8), PeakFilter(3000, 2.5, 0.6), HighShelfFilter(8000, 2.0, 0.7)]
    s.levels = dict(acid=-3.0, bass=-7.5, rumble=-10, perc=-9, hats=-12, vox=-5, toys=-7, whistle=-5, wind=-16)
    s.bus('kick', 1.0, auto=[(0, 400), (7 * 4, 1500), (8 * 4 - 0.01, 1500), (8 * 4, 20000), (OUTRO * 4 + 16, 20000), (END * 4, 600)])
    s.bus('rumble', 1.0, duck=0.9, duck_rel=0.05)
    s.bus('bass', 1.0, P([HighpassFilter(40), Compressor(-15, 4, 2, 60)]), duck=0.85, duck_rel=0.07)
    s.bus('acid', 1.0, P([HighpassFilter(70), Delay(60 / BPM * 0.75, 0.35, 0.2), Reverb(0.3, 0.5, 0.1, 0.95, 0.6)]), duck=0.45, duck_rel=0.09, width=0.3,
          auto=[(0, 20000), (BREAK * 4, 400), (BREAK * 4 + 28, 9000), (DROP2 * 4, 20000), (OUTRO * 4, 20000), (END * 4, 500)], res=0.35)
    s.bus('acid2', 1.0, P([HighpassFilter(120), Phaser(0.3, 0.6, 900, 0.4, 0.5), Delay(60 / BPM * 0.5, 0.3, 0.2)]), duck=0.45, width=0.5)
    s.levels['acid2'] = -5.0
    s.bus('perc', 1.0, P([HighpassFilter(1500), Reverb(0.25, 0.4, 0.12, 0.95, 0.8)]), duck=0.2, width=0.4)
    s.bus('hats', 1.0, P([HighpassFilter(700)]), duck=0.3)
    s.bus('clap', 1.0, P([Reverb(0.4, 0.5, 0.25, 0.85, 0.7)]))
    s.bus('vox', 1.0, P([HighpassFilter(150), Distortion(12), Reverb(0.5, 0.5, 0.25, 0.85, 1.0)]), duck=0.2)
    s.bus('toys', 1.0, P([Reverb(0.4, 0.5, 0.2, 0.9, 1.0)]))
    s.bus('fx', 1.0, P([Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.2)
    s.bus('whistle', 1.0, P([Reverb(0.85, 0.3, 0.4, 0.7, 1.0)]))
    s.bus('wind', 1.0, width=1.0)

    root = lambda b: ROOTS[int(b // 8) % 4]

    # ---------------- kick + rumble + bass
    kb = []
    for bar in list(range(INTRO, BREAK)) + list(range(DROP2, STANDOFF)) + list(range(DROP3, END)):
        kb += [bar * 4 + i for i in range(4)]
        if bar % 8 == 7 and DROP2 <= bar < OUTRO: kb += [bar * 4 + 3.5, bar * 4 + 3.75]
    kicks(s, 'kick', kb, root, 'tek')
    for b in kb:
        if (b * 4) % 4 or not (A * 4 <= b < OUTRO * 4): continue
        s.place('rumble', b + 0.25, inst.rumble(inst.tek_kick(root(b), 0.3), float(s.t(b + 1) - s.t(b + 0.25)) - 0.005))
    bass = []
    for bar in list(range(A, BREAK)) + list(range(DROP2, STANDOFF)) + list(range(DROP3, OUTRO)):
        pat = '..x.' * 4 if bar < B else ('.xx.' * 4 if bar < BREAK or bar >= DROP3 else '..xx' * 4)
        for b, _ in steps(pat, bar): bass.append((b, 0.2, root(b) + 12, 1.0))
    s.add('bass', inst.bass(s.notes(bass), N, cut=700, sub=0.7))

    # ---------------- acid
    a1 = acid_section(ACID1, A, BREAK) + acid_section(ACID1, BREAK, DROP2) + acid_section(ACID1, DROP3, END)
    s.add('acid', inst.acid(s.notes(a1), N, cut=300, envmod=2800, res=0.86, decay=0.14))
    a2 = acid_section(ACID2, DROP2, STANDOFF) + acid_section(ACID2, DROP3 + 8, OUTRO)
    s.add('acid2', inst.acid(s.notes(shift(a2, 0, 12)), N, wave='square', cut=500, envmod=3600, res=0.8, decay=0.11, drive=2.8))

    # ---------------- spoons (the hats), real hats, claps
    rng = np.random.default_rng(5)
    for bar in range(INTRO, END):
        if STANDOFF <= bar < DROP3: continue
        pat = 'x.xxx.xxx.xxx.xx' if (bar >= A and not BREAK <= bar < DROP2) else 'x...x...x...x.x.'
        for b, c in steps(pat, bar):
            off = (b * 4) % 4
            f = [3136.0, 2637.0, 3520.0, 2349.3][int(off)]  # spoons tuned to G E A D
            s.place('perc', b, toys.clink(f, 0.2, seed=int(b * 16)), (1.0 if off == 2 else 0.55) * rng.uniform(0.8, 1.0), pan=rng.uniform(-0.5, 0.5))
        if bar >= A and not BREAK <= bar < DROP2:
            for b, _ in steps('..x...x...x...x.', bar): s.place('hats', b, inst.openhat(0.1, 8000))
        if B <= bar < BREAK or DROP2 <= bar < STANDOFF or DROP3 <= bar < OUTRO:
            for b in (bar * 4 + 1, bar * 4 + 3): s.place('clap', b, inst.clap(0.2, 1500))
        if bar % 8 == 7 and bar >= A:  # spoon rattle fill
            for i in range(8): s.place('perc', bar * 4 + 3 + i / 8, toys.clink([2637.0, 3136.0, 3520.0, 4186.0][i % 4], 0.15, seed=i), 0.6, pan=(i % 2) * 1.2 - 0.6)

    # ---------------- oi oi oi (four slightly different robots)
    def oi(beat, note, gain=1.0):
        for k, (dn, sz, dt, p) in enumerate(((0, 1.0, 0, 0), (0, 1.1, 0.008, -0.6), (0, 0.92, 0.015, 0.6), (12, 1.25, 0.004, 0.2))):
            s.place('vox', beat + dt, voice.say('oi', note + dn, sz, seed=k * 7 + int(beat), bend=-2.5), gain * (0.5 if k == 3 else 0.8), pan=p)
    for bar in list(range(B, BREAK)) + list(range(DROP3, OUTRO)):
        if bar % 2 == 1:
            for i in range(3): oi(bar * 4 + 0.5 + i, 50)
    for bar in (BREAK + 7,): oi(bar * 4 + 2, 52); oi(bar * 4 + 3, 55, 1.2)
    s.place('vox', 4 * 4, voice.say('spoon', 48, 1.0, dur=0.6), 0.9)
    s.place('vox', 6 * 4, voice.say('spoon', 48, 1.0, dur=0.6), 0.9)
    s.place('vox', (OUTRO + 4) * 4, voice.say('spoon', 48, 1.0, dur=0.6), 0.8)

    # ---------------- break: snare build into drop 2
    for bar in range(BREAK + 4, DROP2):
        div = 2 if bar < BREAK + 6 else 4
        for i in range(4 * div):
            b = bar * 4 + i / div; u = (b - (BREAK + 4) * 4) / 16
            s.place('clap', b, inst.snare(0.09, 200 + u * 150, seed=i), 0.3 + 0.6 * u)
    s.place('fx', (BREAK + 4) * 4, inst.riser(float(s.t(DROP2 * 4) - s.t((BREAK + 4) * 4))), 0.7)

    # ---------------- boings on the phrase ends
    for bar in range(A + 7, OUTRO, 8):
        if STANDOFF <= bar < DROP3: continue
        s.place('toys', bar * 4 + 3.5, toys.boing(nm('A3'), 0.6), 0.8)
    for bar in (DROP2, DROP3, A):
        s.place('fx', bar * 4, inst.crash(1.8), 0.6); s.place('fx', bar * 4, inst.impact(1.8, 21), 0.8)

    # ---------------- the standoff (half speed): whistle, spurs, wind, then CLANG
    s.add('whistle', toys.whistle(s.notes(at_bar(STANDOFF_TUNE, STANDOFF)), N))
    s.place('wind', STANDOFF * 4, toys.wind(float(s.t(DROP3 * 4) - s.t(STANDOFF * 4)) + 1.0))
    for bar in range(STANDOFF, DROP3):
        for b in (bar * 4, bar * 4 + 1.5, bar * 4 + 2, bar * 4 + 3.5):
            s.place('perc', b, toys.clink(5274.0, 0.25, seed=int(b * 3)), 0.25, pan=0.5)
        s.place('kick', bar * 4, inst.tek_kick(nm('A1'), 0.6), 0.5); s.kick(bar * 4)
    s.place('toys', DROP3 * 4 - 0.5, toys.clink(2637.0, 0.6) + toys.clink(3520.0, 0.6), 1.2)
    s.place('vox', DROP3 * 4 - 1, voice.say('oi', 55, 1.0, dur=0.3, bend=-4), 1.1)
    return s
