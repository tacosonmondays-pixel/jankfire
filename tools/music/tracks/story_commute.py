# THE COMMUTE (OVERDUE wasteland bed): a road-trip rock riff on a kazoo, dust, distant car alarms that never stop.
# 96 bpm in E (mixolydian, E E A G-D). a lazy laid-back groove on the GM kit, a fingered bass, a crunchy guitar
# chugging power chords, the kazoo doing the riff like it's the best riff ever written, a second kazoo joining in
# thirds later. sunset wind and sand hiss the whole way, and two car alarms somewhere out in the dead traffic, each
# cycling through its whoops and beeps forever (they never sync up with the band). the first and last 4 bars are
# guitar + wind only, so the loop folds into itself. 48 bars = exactly 120 s.
import numpy as np
from jf.song import Song, gm
from jf.dsp import ns, nm
from jf import toys, inst, ambient as amb
from jf.kit import (P, Reverb, Delay, Chorus, Compressor, Distortion, HighpassFilter, LowpassFilter, PeakFilter,
                    LowShelfFilter, HighShelfFilter, riff, shift, diatonic)

TITLE = 'The Commute (rush hour, forever)'
ARTIST = 'The Unpaid Interns'
SUBDIR = 'story'
BPM = 96
TARGET = -16.0
QUALITY = 5

INTRO, A, B, BRK, A2, OUTRO, END = 0, 4, 20, 28, 32, 44, 48
MIXO = [4, 6, 8, 9, 11, 1, 2]  # E mixolydian
LAG = 0.03  # everyone plays a hair behind the beat: lazy

RIFF = ('E4:3 E4:1 G4:2 A4:2 B4:4 A4:2 G4:2  A4:2 G4:2 E4:4 D4:2 E4:6  '
        'E4:3 E4:1 G4:2 A4:2 B4:4 D5:2 B4:2  D5:2 B4:2 A4:4 G4:2 E4:6')
MELB = ('G4:8 E4:4 G4:4  B4:8 A4:4 G4:4  A4:6 F#4:2 D4:8  C#5:8 B4:4 A4:4 '
        'G4:4 A4:4 B4:4 C5:4  D5:8 B4:8  A4:4 B4:2 A4:2 F#4:8  E4:16')
PROG_A = [('E', 'E'), ('E', 'E'), ('A', 'A'), ('G', 'D')]  # chord per half bar
PROG_B = [('C', 'C'), ('G', 'G'), ('D', 'D'), ('A', 'A')]
PWR = {k: nm(v) for k, v in dict(E='E2', A='A2', G='G2', D='D3', C='C3').items()}


def chord_at(prog, bar, half):
    return prog[bar % 4][half]


def build():
    s = Song(TITLE, BPM, END)
    N, L = s.N, s.L
    s.eq = [LowShelfFilter(70, -0.5, 0.7), PeakFilter(300, -1.5, 0.8), HighShelfFilter(7000, 1.0, 0.7)]
    s.levels = dict(drums=-5.0, bass=-4.0, gtr=-6.0, kazoo=-1.0, kazoo2=-5.0, wind=-11.0, alarm=-13.0, alarm2=-17.0)
    s.bus('kick', 1.0, P([HighpassFilter(35), Compressor(-12, 3, 5, 80)]))
    s.bus('drums', 1.0, P([HighpassFilter(80), Compressor(-14, 3, 3, 60), Reverb(0.35, 0.5, 0.15, 0.9, 0.7)]), duck=0.1)
    s.bus('bass', 1.0, P([HighpassFilter(35), Compressor(-14, 3, 4, 80)]), duck=0.4, duck_rel=0.1)
    s.bus('gtr', 1.0, P([HighpassFilter(100), LowpassFilter(4500), Reverb(0.4, 0.6, 0.2, 0.85, 1.0)]), duck=0.15, width=0.6)
    s.bus('kazoo', 1.0, P([HighpassFilter(200), Delay(60 / BPM * 0.75, 0.25, 0.12), Reverb(0.35, 0.5, 0.18, 0.9, 0.6)]), duck=0.1)
    s.bus('kazoo2', 1.0, P([HighpassFilter(250), Reverb(0.4, 0.5, 0.25, 0.85, 0.8)]), width=0.5)
    s.bus('wind', 1.0, P([HighpassFilter(60)]))
    s.bus('alarm', 1.0, P([HighpassFilter(600), LowpassFilter(2600), Reverb(0.95, 0.75, 0.6, 0.08, 1.0)]))
    s.bus('alarm2', 1.0, P([HighpassFilter(700), LowpassFilter(2000), Reverb(0.95, 0.8, 0.6, 0.05, 1.0)]))

    groove = lambda bar: A <= bar < OUTRO
    rng = np.random.default_rng(11)

    # ---------------- drums: lazy rock beat (ride in B, just kick/snare/hat in the breakdown), crashes on the big bars
    kk, dr = [], []
    for bar in range(END):
        if not groove(bar): continue
        b0 = bar * 4 + LAG
        kp = [0, 2.5] if bar % 2 == 0 else [0, 1.5, 2.5, 3.5] if bar % 4 == 3 else [0, 2.5, 3.0]
        for p in kp: kk.append((b0 + p, 0.2, 36, 0.85 if p == 0 else 0.7))
        for p in (1, 3): dr.append((b0 + p + 0.02, 0.2, 38, 0.72 + 0.08 * rng.random()))
        cym = 51 if B <= bar < BRK else 42
        for i in range(8):
            dr.append((b0 + i / 2, 0.15, cym, (0.5 if i % 2 == 0 else 0.32) * (0.85 + 0.3 * rng.random())))
        if bar % 4 == 3 and bar not in (BRK - 1,): dr.append((b0 + 3.75, 0.1, 38, 0.3))
        if bar in (A, B, A2): dr.append((b0, 1.5, 49, 0.55))
        if bar == BRK - 1: dr += [(b0 + 3 + i * 0.25, 0.1, 47 - 2 * i, 0.6) for i in range(4)]
    s.add('kick', gm(-1, s.notes(kk), N))
    for b, *_ in kk: s.kick(b)
    s.add('drums', gm(-1, s.notes(dr), N))

    # ---------------- bass: roots on the kick, a lazy walk-up at the end of each 4
    bs = []
    for bar in range(A, OUTRO):
        prog = PROG_B if B <= bar < BRK else PROG_A
        for half in (0, 1):
            r = PWR[chord_at(prog, bar, half)] - 12
            bb = bar * 4 + half * 2 + LAG
            bs += [(bb, 1.2, r, 0.9), (bb + 1.5, 0.45, r + (7 if half else 0), 0.7)]
    for bar in list(range(INTRO, A)) + list(range(OUTRO, END)):  # intro/outro: one long lazy root per bar
        bs.append((bar * 4 + LAG + 0.04, 3.5, PWR[chord_at(PROG_A, bar, 0)] - 12, 0.75))
    s.add('bass', gm(33, s.notes(bs), N))

    # ---------------- guitar: power chords, long and lazy in the intro/outro, chugging in the groove
    gt = []
    for bar in range(END):
        prog = PROG_B if B <= bar < BRK else PROG_A
        for half in (0, 1):
            r = PWR[chord_at(prog, bar, half)]
            pc = [r, r + 7, r + 12]
            bb = bar * 4 + half * 2 + LAG
            if not groove(bar) or BRK <= bar < A2:
                if half == 0 or chord_at(prog, bar, 0) != chord_at(prog, bar, 1): gt.append((bb + 0.04, 3.6 if chord_at(prog, bar, 0) == chord_at(prog, bar, 1) else 1.8, pc, 0.85))
            else:
                gt += [(bb, 0.9, pc, 0.7), (bb + 1.0, 0.35, pc, 0.5), (bb + 1.5, 0.45, pc, 0.6)]
    s.add('gtr', gm(29, s.notes(gt), N))

    # ---------------- the kazoo riff (and a second kazoo in thirds on the last pass)
    kz = riff(RIFF, A) + riff(RIFF, A + 4) + riff(RIFF, A + 8) + riff(RIFF, A + 12)
    kz += riff(MELB, B)
    kz += riff(RIFF, A2) + riff(RIFF, A2 + 4) + riff(RIFF, A2 + 8)
    kz = [(b + LAG + 0.015 * rng.standard_normal(), d * 0.9, m, 0.9) for b, d, m in kz]
    s.add('kazoo', toys.kazoo(s.notes(kz), N), pan=-0.1)
    k2 = [(b, d, m, 0.8) for b, d, m, _ in diatonic([n for n in kz if n[0] >= (A2 + 4) * 4], 2, MIXO)]
    s.add('kazoo2', toys.kazoo(s.notes(k2), N, buzz=1.3, seed=12), pan=0.35)

    # ---------------- out there: wind + sand, and two car alarms that never stop (never in time with the band)
    s.add('wind', amb.dust(s.n, L))
    bsec = float(s.t(4)); segs = []
    kinds = ['whoop', 'beep', 'nee', 'warble']
    for c in range(END // 8):  # alarm 1: an 8-bar cycle, 2 bars per mode, a breath between modes
        for k, kind in enumerate(kinds):
            t0 = (c * 8 + k * 2) * bsec; segs.append((t0 + 0.1, t0 + 2 * bsec - 0.25, kind))
    s.add('alarm', amb.car_alarm(segs, N), pan=-0.65)
    segs2 = []
    for c in range(END // 6):  # alarm 2, further off: a 6-bar cycle starting 3 bars in, a bit lower
        for k, kind in enumerate(['chirp', 'nee', 'beep']):
            t0 = (c * 6 + k * 2 + 3) * bsec; segs2.append((t0 + 0.15, t0 + 2 * bsec - 0.3, kind))
    x = amb.car_alarm(segs2, s.n + ns(3 * bsec + 1), pitch=0.84)  # its last cycle runs past the end: wrap it onto the start
    y = x[:s.n].copy(); y[:len(x) - s.n] += x[s.n:]
    s.add('alarm2', y, pan=0.7)
    return s
