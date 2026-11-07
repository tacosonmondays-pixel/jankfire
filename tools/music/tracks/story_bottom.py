# THE BOTTOM (OVERDUE district bed): lo-fi hip hop played on a broken accordion, 82 bpm, in A minor-ish (Dm9 G13
# Cmaj9 Am7). dusty swung boom-bap through a bitcrusher, a warm round bass, a sleepy electric piano, vinyl crackle,
# and the accordion: three detuned reeds, a wobbly tune, a wheezing bellows and a reed that sticks now and then
# (it keeps honking flat after the note, then squeaks out). dogs bark somewhere down the hill. night-time favela
# warmth. the drums are filtered in the first and last 4 bars so the loop folds into itself.
import numpy as np
from jf.song import Song, gm
from jf.dsp import ns, nm
from jf import inst, ambient as amb
from jf.kit import (P, Reverb, Delay, Chorus, Compressor, HighpassFilter, LowpassFilter, PeakFilter, Bitcrush,
                    LowShelfFilter, HighShelfFilter, riff, shift)

TITLE = 'The Bottom (night shift)'
ARTIST = 'Lumps & the Wok Dish'
SUBDIR = 'story'
BPM = 82
TARGET = -16.0
QUALITY = 5

INTRO, A, B, BREAK, A2, OUTRO, END = 0, 4, 16, 24, 28, 36, 40
SW = 0.09  # swing: offbeat 8ths land this many beats late

CH = [[nm('F3'), nm('A3'), nm('C4'), nm('E4')], [nm('F3'), nm('B3'), nm('E4')], [nm('E3'), nm('G3'), nm('B3'), nm('D4')], [nm('G3'), nm('C4'), nm('E4')]]
ROOT = [nm('D2'), nm('G1'), nm('C2'), nm('A1')]

M1 = ('A4:3 C5:1 E5:4 D5:2 C5:2 A4:4  _:2 B4:2 D5:2 F5:4 E5:2 D5:4  E5:6 D5:2 B4:4 G4:4  A4:8 _:4 C5:2 D5:2 '
      'E5:3 D5:1 C5:4 A4:2 C5:2 D5:4  F5:4 E5:2 D5:2 B4:4 G4:4  C5:2 E5:2 G5:6 F5:2 E5:4  E5:4 C5:4 A4:8')
M2 = ('_:4 F5:4 E5:2 D5:2 A5:4  G5:6 F5:2 D5:4 B4:4  C5:4 E5:4 G5:4 B4:4  A4:12 _:4 '
      'D5:2 E5:2 F5:4 A5:4 G5:4  F5:4 D5:4 B4:4 D5:4  E5:8 D5:4 B4:4  C5:4 A4:4 _:8')
WHEEZE = 'A4:2 C5:2 E5:4 D5:8  _:4 B4:2 D5:2 G4:8  E5:4 D5:2 B4:2 C5:8  A4:16'


def swing(b):
    f = b % 1
    return b + (SW if abs(f - 0.5) < 1e-6 else SW * 0.5 if abs(f - 0.25) < 1e-6 or abs(f - 0.75) < 1e-6 else 0)


def mel(text, bar0, stuck=None, vel=0.85, seed=0):
    """riff -> accordion notes, swung and a little late/early (played by a human, badly). stuck = {note index: secs}"""
    rng = np.random.default_rng(seed)
    out = []
    for i, (b, d, m) in enumerate(riff(text, bar0)):
        out.append((swing(b) + 0.02 * rng.standard_normal(), d * 0.92, m, vel * (0.85 + 0.15 * rng.random()), (stuck or {}).get(i, 0.0)))
    return out


def build():
    s = Song(TITLE, BPM, END)
    N, L = s.N, s.L
    s.eq = [LowShelfFilter(70, 0.5, 0.7), PeakFilter(300, -1.0, 0.8), HighShelfFilter(7000, 0.0, 0.7)]
    s.levels = dict(drums=-4.0, bass=-5.0, keys=-8.5, acc=-0.5, dogs=-12.0, crackle=-15.0)
    dusty = [(0, 1100), (A * 4 - 0.5, 1100), (A * 4, 20000), (OUTRO * 4 - 2, 20000), (OUTRO * 4 + 2, 1100), (END * 4, 1100)]
    s.bus('kick', 1.0, P([LowpassFilter(2500), Compressor(-12, 3, 5, 80)]), auto=dusty)
    s.bus('drums', 1.0, P([HighpassFilter(90), Bitcrush(11), LowpassFilter(7500), Compressor(-14, 3, 3, 60), Reverb(0.25, 0.6, 0.1, 0.95, 0.5)]), duck=0.15, auto=dusty)
    s.bus('bass', 1.0, P([HighpassFilter(30), Compressor(-14, 3, 5, 100)]), duck=0.35, duck_rel=0.1)
    s.bus('keys', 1.0, P([HighpassFilter(150), LowpassFilter(4200), Chorus(0.5, 0.3, 7, 0.0, 0.5), Reverb(0.45, 0.6, 0.25, 0.85, 0.9)]), duck=0.2, width=0.4)
    s.bus('acc', 1.0, P([HighpassFilter(160), PeakFilter(2800, -2.0, 1.0), Delay(60 / BPM * 0.75, 0.2, 0.12), Reverb(0.4, 0.55, 0.2, 0.9, 0.8)]), duck=0.1, width=0.3)
    s.bus('dogs', 1.0, P([HighpassFilter(350), LowpassFilter(2200), Reverb(0.85, 0.7, 0.55, 0.12, 1.0)]))
    s.bus('crackle', 1.0, P([HighpassFilter(200), LowpassFilter(9000)]))

    # ---------------- drums: boom-bap on the GM kit, swung, ghosted, then crushed and dusted
    rng = np.random.default_rng(3)
    kk, dr = [], []
    for bar in range(END):
        brk = BREAK <= bar < A2
        if not brk or bar == A2 - 1:
            pat = [0, 1.5, 2.5] if bar % 2 == 0 else [0, 0.75, 2.25, 2.5]
            if bar == A2 - 1: pat = [2.5, 3.25]
            for p in pat: kk.append((swing(bar * 4 + p), 0.2, 36, 0.8 if p == 0 else 0.62))
            if not brk:
                for p in (1, 3): dr.append((bar * 4 + p + 0.03, 0.2, 38, 0.62 + 0.06 * rng.random()))
                if bar % 4 == 3: dr.append((swing(bar * 4 + 3.75), 0.1, 38, 0.22))
        for i in range(8):
            b = bar * 4 + i / 2
            if brk and i % 2 == 0: continue
            v = (0.42 if i % 2 == 0 else 0.26) * (0.85 + 0.3 * rng.random())
            dr.append((swing(b), 0.1, 46 if (i == 7 and bar % 4 == 3) else 42, v * (0.7 if brk else 1)))
    s.add('kick', gm(-1, s.notes(kk), N))
    for b, *_ in kk: s.kick(b)
    s.add('drums', gm(-1, s.notes(dr), N))

    # ---------------- bass: lazy roots + a walk into the next chord
    bs = []
    for bar in range(A, OUTRO):
        r = ROOT[bar % 4]
        if BREAK <= bar < A2: bs.append((bar * 4, 3.5, r, 0.8)); continue
        bs += [(bar * 4, 1.4, r, 0.95), (swing(bar * 4 + 1.5), 0.45, r, 0.7), (bar * 4 + 2, 1.0, r + 7, 0.8),
               (swing(bar * 4 + 3.5), 0.45, ROOT[(bar + 1) % 4] + (1 if bar % 4 == 1 else -1), 0.65)]
    s.add('bass', amb.warmbass(s.notes(bs), N))

    # ---------------- sleepy electric piano: chords on 1, a soft re-hit on the swung "and" of 2
    kp = []
    for bar in range(END):
        c = CH[bar % 4]
        kp.append((bar * 4 + 0.02, 1.4, c, 0.42))
        if A <= bar < OUTRO and not (BREAK <= bar < A2): kp.append((swing(bar * 4 + 1.5), 2.2, c, 0.3))
        else: kp.append((bar * 4 + 2, 1.9, c, 0.3))
    s.add('keys', gm(4, s.notes(kp), N))

    # ---------------- the broken accordion
    acc = []
    for bar in list(range(INTRO, A)) + list(range(OUTRO, END)):  # chord swells, bellows only half working
        acc.append((bar * 4 + 0.05, 3.4, [m + 12 for m in CH[bar % 4]], 0.32, 0.0))
    acc += mel(M1, A, seed=1) + mel(M1[:M1.index('E5:3')], A + 8, {15: 1.1}, seed=2)
    acc += mel(M2, B, {12: 1.6}, seed=3)
    acc += mel(WHEEZE, BREAK, {3: 0.9, 11: 2.2}, vel=0.7, seed=4)
    acc += mel(M1, A2, {15: 1.3}, seed=5)
    acc = [(float(s.t(b)), float(s.t(b + d)) - float(s.t(b)), m, v, st) for b, d, m, v, st in acc]
    s.add('acc', amb.accordion(acc, N, L))

    # ---------------- night: crackle, dogs down the hill
    s.add('crackle', amb.crackle(s.n))
    for bar, beat, seed, size, n, pan in ((2, 1.5, 1, 1.0, 2, -0.7), (13, 2.0, 2, 0.85, 3, 0.6), (25, 0.5, 3, 1.1, 2, -0.4),
                                         (25, 2.5, 4, 0.8, 1, 0.7), (37, 1.0, 5, 1.0, 2, 0.5)):
        s.place('dogs', bar * 4 + beat, amb.bark(seed, size, n), 1.0, pan=pan)
    return s
