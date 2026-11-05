# HUNG JURY HARDCORE: 180 bpm gabber in D minor (Dm Bb Gm A). court is in session: church organ, gavel knocks,
# a kazoo plays the solemn theme, robots shout ORDER and GUILTY. the jury goes out (a clock ticks in the silence).
# joke: the hung jury. left speaker in 4, right speaker in 3, "YES" on the left, "NO" on the right, until the gavel.
import numpy as np
from jf.song import Song, gm
from jf.dsp import ns, nm, midi_hz
from jf import inst, toys, voice
from jf.kit import (P, Reverb, Delay, Chorus, Distortion, Compressor, HighpassFilter, LowpassFilter, PeakFilter,
                    LowShelfFilter, HighShelfFilter, steps, kicks, riff, shift, at_bar)

TITLE = 'Hung Jury Hardcore'
BPM = 180
TARGET = -8.0

INTRO, A, B, BREAK, CLOCK, DROP, HUNG, DROP2, OUTRO, END = 0, 8, 24, 40, 46, 48, 64, 68, 88, 96
KICKNOTE = [nm('A1'), nm('Bb1'), nm('G1'), nm('A1')]
ORGAN = [[nm('D3'), nm('D4'), nm('F4'), nm('A4')], [nm('Bb2'), nm('D4'), nm('F4'), nm('Bb4')],
         [nm('G2'), nm('D4'), nm('G4'), nm('Bb4')], [nm('A2'), nm('C#4'), nm('E4'), nm('A4')]]

THEME = riff('D5:4 _:4 A4:2 D5:2 F5:4 E5:2 D5:2 C5:2 D5:2 Bb4:8 G4:2 Bb4:2 D5:4 G5:4 F5:2 E5:2 E5:4 C#5:4 A4:6 _:2 '
             'D5:4 _:4 A4:2 D5:2 F5:4 G5:2 F5:2 E5:2 F5:2 D5:8 Bb5:3 A5:3 G5:2 F5:3 E5:3 D5:2 C#5:4 E5:4 A5:4 A4:4')
HOOVER = riff('D3:3 D3:3 F3:2 A3:3 D3:3 F3:2 Bb2:3 Bb2:3 D3:2 F3:3 Bb2:3 D3:2 '
              'G2:3 G2:3 Bb2:2 D3:3 G3:3 F3:2 A2:3 A2:3 C#3:2 E3:3 G3:3 C#3:2')


def tile(r, bar0, bar1, span=4):
    out = []
    for b in range(bar0, bar1, span): out += at_bar(r, b)
    return [n for n in out if n[0] < bar1 * 4]


def build():
    s = Song(TITLE, BPM, END)
    N = s.N
    s.eq = [LowShelfFilter(60, -2.0, 0.7), PeakFilter(320, -1.5, 0.8), HighShelfFilter(8000, 2.0, 0.7)]
    s.levels = dict(kazoo=-3.5, hoover=-5, organ=-7, gavel=-6, vox=-4.5, jury=-16, clock=-9, siren=-11)
    s.bus('kick', 1.0, auto=[(0, 300), (4 * 4, 300), (8 * 4 - 0.01, 1800), (8 * 4, 20000), (OUTRO * 4 + 8, 20000), (END * 4, 400)])
    s.bus('hats', 1.0, P([HighpassFilter(800)]), duck=0.3)
    s.bus('clap', 1.0, P([Reverb(0.4, 0.5, 0.2, 0.9, 0.7)]))
    s.bus('kazoo', 1.0, P([HighpassFilter(200), Delay(60 / BPM * 0.75, 0.2, 0.12), Reverb(0.45, 0.5, 0.18, 0.9, 0.7)]), duck=0.45, width=0.25)
    s.bus('hoover', 1.0, P([Chorus(0.6, 0.25, 6, 0.0, 0.4), HighpassFilter(90), Reverb(0.45, 0.6, 0.18, 0.9, 0.9)]), duck=0.75, duck_rel=0.11, width=0.4)
    s.bus('organ', 1.0, P([HighpassFilter(80), Reverb(0.9, 0.4, 0.45, 0.7, 1.0)]), duck=0.5, width=0.6)
    s.bus('gavel', 1.0, P([Reverb(0.75, 0.3, 0.35, 0.8, 1.0)]))
    s.bus('vox', 1.0, P([HighpassFilter(150), Distortion(10), Reverb(0.55, 0.5, 0.25, 0.85, 1.0)]), duck=0.2)
    s.bus('jury', 1.0, P([HighpassFilter(200), Reverb(0.6, 0.5, 0.3, 0.8, 1.0)]), width=1.0)
    s.bus('clock', 1.0, P([Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]))
    s.bus('siren', 1.0, P([HighpassFilter(300), Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.5)
    s.bus('fx', 1.0, P([Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.2)

    tune = lambda b: KICKNOTE[int(b // 4) % 4]

    # ---------------- kick
    kb = []
    for bar in list(range(4, BREAK)) + list(range(DROP, HUNG)) + list(range(DROP2, END)):
        kb += [bar * 4 + i for i in range(4)]
        if bar % 8 == 7 and (DROP <= bar < HUNG or DROP2 <= bar < OUTRO): kb += [bar * 4 + 3.25, bar * 4 + 3.5, bar * 4 + 3.75]
    kicks(s, 'kick', kb, tune, 'gabber')
    # the hung jury: left in 4, right in 3 (four bars), each side tuned its own way
    for i in range(16):
        b = HUNG * 4 + i
        s.place('kick', b, inst.gabber_kick(nm('A1'), round(float(s.t(b + 1) - s.t(b)) - 0.002, 3)), 1.0, pan=-0.85); s.kick(b)
    for i in range(12):
        b = HUNG * 4 + i * 4 / 3
        s.place('kick', b, inst.gabber_kick(nm('Bb1'), round(float(s.t(b + 4 / 3) - s.t(b)) - 0.002, 3)), 1.0, pan=0.85)
        s.place('vox', b + 0.5, voice.say('no', 50, 1.05, seed=i, bend=-3), 0.9, pan=0.85)
    for i in range(0, 16, 1):
        s.place('vox', HUNG * 4 + i + 0.5, voice.say('yes', 55, 1.2, seed=i + 40, bend=2), 0.8, pan=-0.85)

    # ---------------- hats / claps
    for bar in range(A, END):
        if BREAK <= bar < DROP or HUNG <= bar < DROP2: continue
        for b, c in steps('h.o.h.o.h.o.h.oh' if bar >= DROP else '..o...o...o...o.', bar):
            s.place('hats', b, inst.openhat(0.1, 7500) if c == 'o' else inst.hat(0.03, 9000, seed=int(b * 4)), 1.0 if c == 'o' else 0.4)
        if B <= bar < BREAK or DROP <= bar < HUNG or DROP2 <= bar < OUTRO:
            for b in (bar * 4 + 1, bar * 4 + 3): s.place('clap', b, inst.clap(0.2, 1300))

    # ---------------- court is in session: organ
    org = [(bar * 4, 4, ORGAN[bar % 4], 0.85) for bar in list(range(INTRO, A)) + list(range(BREAK, CLOCK)) + list(range(OUTRO, END))]
    org += [(bar * 4, 0.5, ORGAN[bar % 4], 0.8) for bar in range(DROP + 8, HUNG)] + [(bar * 4 + 2.5, 0.5, ORGAN[bar % 4], 0.7) for bar in range(DROP + 8, HUNG)]
    s.add('organ', gm(19, s.notes(org), N))

    # ---------------- gavels: three knocks to open, on the 1 of every other bar in the drops, the verdict
    for b in (6 * 4, 6 * 4 + 1, 6 * 4 + 2):
        s.place('gavel', b, toys.gavel(0.6, 480), 1.0)
    s.place('vox', 7 * 4, voice.say('order', 48, 1.0, dur=0.7, bend=-3), 1.0)
    for bar in list(range(A, BREAK, 2)) + list(range(DROP, HUNG, 2)) + list(range(DROP2, OUTRO, 2)):
        s.place('gavel', bar * 4, toys.gavel(0.4, 520, seed=bar), 0.6)
    for b in (DROP2 * 4 - 3, DROP2 * 4 - 2, DROP2 * 4 - 1):
        s.place('gavel', b, toys.gavel(0.6, 460), 1.1)
    s.place('vox', DROP2 * 4 - 3, voice.say('order', 50, 1.0, dur=0.55, bend=-3), 1.0)

    # ---------------- kazoo theme + hoover riff
    kz = tile(THEME, A, B, 8) + tile(THEME, B + 8, BREAK, 8) + tile(THEME, BREAK + 2, CLOCK, 8) + tile(THEME, DROP, HUNG, 8) + tile(THEME, DROP2 + 8, OUTRO, 8)
    s.add('kazoo', toys.kazoo(s.notes(kz), N))
    hv = tile(HOOVER, B, BREAK) + tile(HOOVER, DROP + 8, HUNG) + tile(HOOVER, DROP2, OUTRO)
    s.add('hoover', inst.hoover(s.notes(hv), N))

    # ---------------- vocals
    for bar in list(range(B, BREAK, 4)) + list(range(DROP, HUNG, 4)) + list(range(DROP2, OUTRO, 4)):
        s.place('vox', bar * 4 + 3, voice.say('guilty', 52, 1.05, bend=-2), 0.9)
    s.place('vox', CLOCK * 4 + 7, voice.say('guilty', 50, 1.0, dur=0.8, bend=-5), 1.1)

    # ---------------- the jury is out: murmur under the organ, then a clock ticks in the silence
    rng = np.random.default_rng(11)
    vow = ['a', 'uh', 'e', 'o', 'er', 'I', 'm', 'n']
    for i in range(36):
        b = BREAK * 4 + rng.uniform(0, (CLOCK - BREAK) * 4 + 6)
        word = [(str(rng.choice(vow)), rng.uniform(0.06, 0.14)) for _ in range(rng.integers(2, 5))]
        s.place('jury', b, voice.say(word, rng.uniform(44, 56), rng.uniform(0.9, 1.3), seed=i, bend=rng.uniform(-3, 2)), rng.uniform(0.4, 1.0), pan=rng.uniform(-0.9, 0.9))
    for i in range(8):
        b = CLOCK * 4 + i
        s.place('clock', b, toys.gavel(0.08, 1900 if i % 2 == 0 else 1500, seed=i), 0.8)
    s.place('fx', CLOCK * 4 + 4, inst.riser(float(s.t(DROP * 4) - s.t(CLOCK * 4 + 4)), 400, 10000), 0.8)
    for bar in (A, DROP, DROP2):
        s.place('fx', bar * 4, inst.impact(2.0, 21), 0.9); s.place('fx', bar * 4, inst.crash(2.0), 0.6)

    # ---------------- alarm in drop 2's second half
    s.add('siren', inst.siren(float(s.t((DROP2 + 12) * 4)), float(s.t(OUTRO * 4) - s.t((DROP2 + 12) * 4)), N, 74, 81, rate=1.5, shape='sweep'))
    s.place('vox', (OUTRO + 4) * 4, voice.say('order', 46, 0.95, dur=0.8, bend=-4), 0.8)
    return s
