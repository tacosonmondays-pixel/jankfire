# JANK COLA RAVE: 174 bpm gabber in F minor. a can cracks open, the kick tunes itself to the chords, hoovers,
# orchestra-hit rave stabs, a cash register that rings on the phrase ends, a robot shouting "JANK... COLA".
# joke: the middle drops to half speed (the sugar crash) and revs back up.
import numpy as np
from jf.song import Song, gm
from jf.dsp import ns, nm, midi_hz
from jf import inst, toys, voice
from jf.kit import P, LowShelfFilter as P_LS, PeakFilter as P_PK, HighShelfFilter as P_HS, Reverb, Delay, Chorus, Distortion, Compressor, HighpassFilter, LowpassFilter, PeakFilter, steps, kicks, riff, shift, at_bar

TITLE = 'Jank Cola Rave'
BPM = 174
TARGET = -8.0

# sections (bars)
INTRO, DROPA, BREAK, DROPB, SLOMO, REV, DROPC, OUTRO, END = 0, 8, 24, 32, 56, 62, 64, 88, 96
PROG = [nm('F1'), nm('F1'), nm('Ab1'), nm('Bb1')]           # kick tunings per bar (Fm Fm Db Eb)
CHORDS = [[nm('F4'), nm('Ab4'), nm('C5')], [nm('F4'), nm('Ab4'), nm('C5')], [nm('Db4'), nm('F4'), nm('Ab4')], [nm('Eb4'), nm('G4'), nm('Bb4')]]

HOOVER = riff('F3:3 F3:3 Ab3:2 C4:3 Ab3:3 F3:2 '
              'F3:3 F3:3 Ab3:2 Eb4:3 C4:3 Ab3:2 '
              'Db4:3 C4:3 Ab3:2 F3:3 Ab3:3 Db4:2 '
              'Eb4:3 Bb3:3 G3:2 Bb3:2 C4:2 Db4:2 Eb4:2')
THEME = riff('C5:2 C5:2 Ab4:2 C5:2 F5:4 Eb5:2 C5:2 '
             'Db5:2 C5:2 Ab4:2 G4:2 Ab4:4 F4:4 '
             'F5:2 F5:2 Eb5:2 Db5:2 C5:2 Db5:2 F5:4 '
             'Eb5:2 Eb5:2 G5:2 Eb5:2 Bb4:4 _:4')


def tile(r, bar0, bar1, every=4):
    out = []
    for b in range(bar0, bar1, every): out += at_bar(r, b)
    return [n for n in out if n[0] < bar1 * 4]


def build():
    s = Song(TITLE, BPM, END, tempo=[(SLOMO * 4, 87, 'step'), (REV * 4, 87, 'step'), (DROPC * 4, 174, 'ramp')])
    N = s.N
    s.bus('kick', 1.0, auto=[(0, 350), (6 * 4, 900), (8 * 4 - 0.01, 900), (8 * 4, 20000), (OUTRO * 4 + 16, 20000), (END * 4, 500)])
    s.eq = [P_LS(60, -2.5, 0.7), P_PK(320, -1.0, 0.8), P_PK(3500, 1.5, 0.7), P_HS(8000, 3.0, 0.7)]
    s.bus('hats', 0.5, P([HighpassFilter(600)]), duck=0.35, duck_rel=0.06)
    s.bus('clap', 0.42, P([Reverb(0.35, 0.5, 0.25, 0.85, 0.6)]), duck=0.1)
    s.bus('hoover', 0.5, P([Chorus(0.6, 0.25, 6, 0.0, 0.4), HighpassFilter(90), Reverb(0.45, 0.6, 0.18, 0.9, 0.9)]), duck=0.7, duck_rel=0.11, width=0.4,
          auto=[(0, 20000), (OUTRO * 4, 20000), (END * 4, 900)])
    s.bus('lead', 0.33, P([HighpassFilter(250), Delay(60 / BPM * 0.75, 0.3, 0.22), Reverb(0.6, 0.5, 0.25, 0.8, 1.0)]), duck=0.6, duck_rel=0.1, width=0.8)
    s.bus('stab', 0.42, P([HighpassFilter(180), Reverb(0.55, 0.5, 0.25, 0.8, 1.0)]), duck=0.55, duck_rel=0.1, width=0.5)
    s.bus('orch', 0.55, P([HighpassFilter(150), Compressor(-12, 3, 1, 80)]), duck=0.45)
    s.bus('vox', 0.62, P([HighpassFilter(160), Distortion(9), Delay(60 / BPM * 0.5, 0.25, 0.18), Reverb(0.4, 0.5, 0.2, 0.9, 1.0)]), duck=0.25)
    s.bus('fx', 0.42, P([Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.15)
    s.bus('bells', 0.45, P([Reverb(0.75, 0.4, 0.35, 0.75, 1.0)]), width=0.7)
    s.bus('pad', 0.22, P([HighpassFilter(200), Chorus(0.3, 0.3, 8, 0, 0.5), Reverb(0.8, 0.5, 0.4, 0.7, 1.0)]), width=1.0, duck=0.4)
    s.bus('siren', 0.2, P([HighpassFilter(300), Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.5)

    tune = lambda b: PROG[int(b // 4) % 4]

    # ---------------- kick
    four = []
    for bar in list(range(INTRO, BREAK)) + list(range(DROPB, SLOMO)) + list(range(DROPC, END)):
        four += [bar * 4 + i for i in range(4)]
        if bar >= DROPC and bar < OUTRO and bar % 4 == 3: four += [bar * 4 + 3.25, bar * 4 + 3.5, bar * 4 + 3.75]  # gabber roll
        if bar in (DROPB + 7, DROPB + 15, DROPB + 23): four += [bar * 4 + 3.5]
    for bar in range(SLOMO, REV): four += [bar * 4, bar * 4 + 2.5]  # half-time boom
    for bar in range(REV, DROPC): four += [bar * 4 + i for i in range(4)]
    kicks(s, 'kick', four, tune, 'gabber')

    # ---------------- hats + claps
    for bar in range(INTRO, END):
        if BREAK <= bar < DROPB or SLOMO <= bar < REV: continue
        pat = '..x...x...x...x.' if bar < DROPA else ('hhxhhhxhhhxhhhxh' if DROPC <= bar < OUTRO else '.hx..hx..hx..hxh')
        for b, c in steps(pat, bar):
            s.place('hats', b, inst.openhat(0.12) if c == 'x' else inst.hat(0.03, seed=int(b * 4)), 0.9 if c == 'x' else 0.5)
        if DROPB <= bar < SLOMO or DROPC <= bar < OUTRO:
            for b in (bar * 4 + 1, bar * 4 + 3): s.place('clap', b, inst.clap())

    # ---------------- hoover
    hv = tile(HOOVER, DROPA, BREAK) + tile(HOOVER, DROPB + 8, SLOMO) + tile(HOOVER, DROPC, END)
    s.add('hoover', inst.hoover(s.notes(hv), N))

    # ---------------- theme lead (supersaw) in drop B second half + drop C
    th = tile(THEME, DROPB, DROPB + 8) + tile(THEME, DROPB + 16, SLOMO) + tile(THEME, DROPC + 8, OUTRO)
    s.add('lead', inst.supersaw(s.notes(th), N, cut=6500))

    # ---------------- stabs: 3-3-2 on the chord, break + drops
    stabs = []
    for bar in list(range(BREAK, DROPB)) + list(range(DROPB, DROPB + 8)) + list(range(DROPC, DROPC + 8)) + list(range(DROPC + 16, OUTRO)):
        ch = CHORDS[bar % 4]
        pat = 'x..x..x.x..x..x.' if bar < DROPB else '..x...x...x..x.x'
        for b, _ in steps(pat, bar): stabs.append((b, 0.2, ch, 0.9))
    s.add('stab', inst.stab(s.notes(stabs), N))
    orch = [(b, 0.25, [c - 12 for c in ch], v) for b, d, ch, v in stabs if (b * 4) % 16 in (0, 6, 12)]
    s.add('orch', gm(55, s.notes(orch), N))

    # ---------------- break: pad + siren + build
    pad = [(bar * 4, 4, CHORDS[bar % 4], 0.8) for bar in range(BREAK, DROPB)]
    s.add('pad', inst.supersaw(s.notes(pad), N, cut=2500, a=0.3, r=0.6))
    s.add('siren', inst.siren(float(s.t(BREAK * 4 + 16)), float(s.t(DROPB * 4 - 2) - s.t(BREAK * 4 + 16)), N, 77, 84, rate=1.45))
    s.add('siren', inst.siren(float(s.t((DROPC + 16) * 4)), float(s.t(OUTRO * 4) - s.t((DROPC + 16) * 4)), N, 72, 79, rate=1.45 * 2), 0.8)
    for bar in range(BREAK + 4, DROPB):  # snare roll: 8ths, then 16ths, then 32nds
        div = 2 if bar < BREAK + 6 else (4 if bar < BREAK + 7 else 8)
        for i in range(4 * div):
            b = bar * 4 + i / div
            s.place('clap', b, inst.snare(0.1, 200 + (b - (BREAK + 4) * 4) * 6, seed=i), 0.25 + 0.6 * (b - (BREAK + 4) * 4) / 16)
    s.place('fx', (BREAK + 4) * 4, inst.riser(float(s.t(DROPB * 4) - s.t((BREAK + 4) * 4))), 0.7)
    s.tapestop(DROPB * 4 - 2, 2)

    # ---------------- slow-mo sugar crash: register bells play the theme at half speed, the robot slurs
    bel = tile(THEME, SLOMO, SLOMO + 4)
    for b, d, m in bel: s.place('bells', b, toys.bell(m + 12, 1.6), 0.6)
    pad2 = [(bar * 4, 4, CHORDS[bar % 4], 0.7) for bar in range(SLOMO, REV)]
    s.add('pad', inst.supersaw(s.notes(pad2), N, cut=1800, a=0.5, r=1.0))
    s.place('vox', (SLOMO + 4) * 4, voice.say('jank', 41, 0.85, dur=1.2, bend=-4), 0.9)
    s.place('vox', (SLOMO + 5) * 4, voice.say('cola', 39, 0.85, dur=1.5, bend=-5), 0.9)
    s.place('fx', SLOMO * 4, toys.can_open(2.5), 0.7)
    for bar in range(REV, DROPC):  # the rev: snare roll speeding up with the tempo
        for i in range(16): s.place('clap', bar * 4 + i / 4, inst.snare(0.08, 220 + i * 8 + (bar - REV) * 120, seed=i), 0.3 + 0.04 * i)
    s.place('fx', REV * 4, inst.riser(float(s.t(DROPC * 4) - s.t(REV * 4)), 500, 12000), 0.8)
    s.place('vox', DROPC * 4 - 2, voice.stutter('jank', reps=4, gap=float(s.t(1) - s.t(0.75)), note=53, size=1.1), 1.0)

    # ---------------- drops: impacts, cash register, crashes, vocal chops
    for bar in (DROPA, DROPB, DROPC):
        s.place('fx', bar * 4, inst.impact(2.2, 17), 0.9)
        s.place('fx', bar * 4, inst.crash(2.0), 0.6)
    for bar in range(DROPA, END, 8):
        if SLOMO <= bar < DROPC: continue
        s.place('fx', bar * 4 + 7 * 4 + 2, toys.kaching(1.5), 0.85)
    for bar in list(range(DROPB, SLOMO, 4)) + list(range(DROPC, OUTRO, 4)):
        s.place('vox', bar * 4, voice.say('jank', 53, 1.05, bend=-2), 0.9)
        s.place('vox', bar * 4 + 2.5, voice.say('co', 60, 1.35), 0.7)
        s.place('vox', bar * 4 + 3, voice.say('la', 58, 1.35), 0.7)
    for bar in range(BREAK, DROPB, 2):
        s.place('vox', bar * 4 + 3, voice.say('cola', 65, 1.45, bend=1), 0.6, pan=-0.3 if bar % 4 else 0.3)
    s.repeat((DROPC + 15) * 4 + 2, 2, 0.25)  # 16th stutter before the second half of drop C

    # ---------------- intro / outro: the can, a robot, the loop back
    s.place('fx', 0, toys.can_open(1.6), 0.9)
    s.place('vox', 4 * 4, voice.say('jank', 50, 1.0, dur=0.6), 0.8)
    s.place('vox', 5 * 4, voice.say('cola', 55, 1.3, dur=0.8), 0.8)
    s.place('fx', 4 * 4, inst.riser(float(s.t(8 * 4) - s.t(4 * 4))), 0.6)
    s.place('fx', OUTRO * 4 + 16, toys.kaching(1.5), 0.8)
    s.place('vox', (OUTRO + 4) * 4, voice.say('jank', 50, 1.0, dur=0.6), 0.7)
    s.place('vox', (OUTRO + 5) * 4, voice.say('cola', 55, 1.3, dur=0.8), 0.7)
    s.place('fx', (END - 1) * 4, inst.downer(1.4), 0.5)
    return s
