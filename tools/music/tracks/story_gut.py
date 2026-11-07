# THE GUT (OVERDUE district bed): a choir humming one chord, a giant heartbeat as the kick drum, wet synth pads.
# 72 bpm, D major, locked to the district's flesh shader (it pulses lub-dub at 72 bpm): every beat is a LUB, a softer
# DUB lands 0.2 beat later. the Gut Choir hums D-A-D / F#-A-E for the whole loop (mmm, opening to ooh in the middle)
# and sways in pitch like it's breathing; squelchy saw pads open a little on every heartbeat; drips plink a tune,
# the stomach gurgles, the odd wet squish. cheerful and gross. 36 bars = exactly 120 s.
import numpy as np
from jf.song import Song
from jf.dsp import ns, nm, tt, SR, onepole_lp
from jf import ambient as amb
from jf.kit import (P, Reverb, Delay, Chorus, Compressor, HighpassFilter, LowpassFilter, PeakFilter, Phaser,
                    LowShelfFilter, HighShelfFilter, riff)

TITLE = 'The Gut (choir practice)'
ARTIST = 'The Gut Choir'
SUBDIR = 'story'
BPM = 72
TARGET = -16.0
QUALITY = 5

INTRO, A, SWELL, OUT, END = 0, 4, 20, 28, 36
DUB = 0.2  # the dub lands this many beats after the lub (matches the flesh shader)
PADS = [[nm('D3'), nm('F#3'), nm('A3'), nm('D4')], [nm('B2'), nm('D3'), nm('F#3'), nm('B3')],
        [nm('G2'), nm('B2'), nm('D3'), nm('G3')], [nm('D3'), nm('A3'), nm('D4'), nm('F#4')]]
DRIPS = ('_:8 F#5:4 A5:4 B5:8 A5:8  _:8 D6:4 B5:4 A5:16  '
         '_:8 E5:4 F#5:4 A5:8 F#5:8  _:12 D5:4 E5:8 D5:8')


def build():
    s = Song(TITLE, BPM, END)
    N, L, n = s.N, s.L, s.n
    s.eq = [LowShelfFilter(60, -0.5, 0.7), PeakFilter(350, -1.5, 0.8), HighShelfFilter(4500, 2.5, 0.7)]
    s.levels = dict(choir=-2.0, pad=-6.0, drip=-5.5, gurgle=-8.0, squelch=-9.5, tick=-13.0)
    s.bus('kick', 1.0, P([LowpassFilter(1800), Compressor(-12, 2.5, 5, 120), Reverb(0.3, 0.7, 0.08, 0.95, 0.3)]))
    s.bus('choir', 1.0, P([HighpassFilter(110), Chorus(0.3, 0.2, 9, 0.0, 0.35), Reverb(0.8, 0.5, 0.35, 0.75, 1.0)]), duck=0.12, duck_rel=0.25, width=0.5)
    s.bus('pad', 1.0, P([HighpassFilter(70), Phaser(0.11, 0.6, 700, 0.4, 0.4), Chorus(0.6, 0.3, 7, 0.0, 0.5), Reverb(0.6, 0.6, 0.3, 0.8, 1.0)]), duck=0.3, duck_rel=0.2, width=0.6)
    s.bus('drip', 1.0, P([HighpassFilter(300), Delay(60 / BPM * 0.75, 0.35, 0.3), Reverb(0.75, 0.5, 0.4, 0.7, 1.0)]), width=0.5)
    s.bus('gurgle', 1.0, P([HighpassFilter(45), Reverb(0.5, 0.7, 0.25, 0.85, 0.8)]))
    s.bus('squelch', 1.0, P([HighpassFilter(120), Reverb(0.45, 0.6, 0.2, 0.85, 0.8)]))
    s.bus('tick', 1.0, P([HighpassFilter(1500), Reverb(0.3, 0.6, 0.15, 0.9, 0.8)]), width=0.4)

    # ---------------- the heart: lub on every beat (beat 1 of each bar a touch harder), dub 0.2 beat later
    rng = np.random.default_rng(7)
    for b in range(END * 4):
        acc = 1.0 if b % 4 == 0 else 0.9
        s.place('kick', b, amb.lub(gain=acc * (0.95 + 0.05 * rng.random()), seed=b), 1.0)
        s.place('kick', b + DUB, amb.dub(seed=1000 + b), 1.0)
        s.kick(b)

    # ---------------- the choir: one chord, forever. hum -> ooh in the middle, back to hum
    T = tt(n)
    bp_ = lambda beat: float(s.t(beat))
    mo = np.interp(T, [0, bp_(A * 4), bp_(SWELL * 4 - 8), bp_(SWELL * 4 + 4), bp_(OUT * 4), bp_(END * 4)], [0.0, 0.0, 0.35, 0.8, 0.5, 0.0])
    mo = np.clip(mo + 0.1 * amb.per(T, L, 0.06), 0, 1)
    groups = [([nm('D3'), nm('A3'), nm('D4')], 1.0), ([nm('F#4'), nm('A4'), nm('E5')], 1.15)]
    s.add('choir', amb.choir(groups, n, L, mo))

    # ---------------- wet pads: one chord per 4 bars over the D pedal; the filter opens on every lub
    pn = []
    for bar in range(A, OUT, 4):
        pn.append((bar * 4, 16, PADS[((bar - A) // 4) % 4], 0.8))
    pn = [(bp_(b), bp_(b + d) - bp_(b), m, v) for b, d, m, v in pn]
    imp = np.zeros(N)
    for b in s.kicks: imp[ns(bp_(b))] += 1.0
    from scipy.signal import lfilter
    beat_env = lfilter([1.0], [1, -np.exp(-1 / (0.22 * SR))], imp)
    beat_env = np.minimum(beat_env, 1.5)
    TT = tt(N)
    deep = np.interp(TT, [0, bp_(SWELL * 4), bp_(SWELL * 4 + 8), bp_(OUT * 4), bp_(END * 4) + 6], [0.5, 0.6, 1.0, 0.6, 0.5])
    cut = 550 + 1100 * beat_env * deep + 180 * (0.5 + 0.5 * amb.per(TT, L, 0.09))
    s.add('pad', amb.wetpad(pn, N, cut, res=0.62))

    # ---------------- drips: a slow plinky tune, twice (the second time an octave down)
    for k, (bar0, octv) in enumerate(((A + 4, 0), (SWELL, -12))):
        for b, d, m in riff(DRIPS, bar0):
            if b >= OUT * 4: continue
            s.place('drip', b + 0.03 * rng.standard_normal(), amb.drip(m + octv, 0.6), 0.8 + 0.2 * rng.random(), pan=float(rng.uniform(-0.6, 0.6)))

    # ---------------- the stomach: gurgles, squishes on the backbeat, little wet clicks
    for i, (bar, beat) in enumerate(((2, 1.0), (7, 2.5), (11, 0.5), (15, 3.0), (19, 1.5), (23, 2.0), (26, 0.5), (30, 2.5), (34, 1.0))):
        s.place('gurgle', bar * 4 + beat, amb.gurgle(1.4 + 0.8 * rng.random(), seed=40 + i), 1.0, pan=float(rng.uniform(-0.7, 0.7)))
    for bar in range(A + 4, OUT + 2, 2):
        s.place('squelch', bar * 4 + 3 + DUB, amb.squelch(0.35 + 0.15 * rng.random(), seed=bar), 1.0, pan=float(rng.uniform(-0.4, 0.4)))
    for bar in range(SWELL - 4, OUT):
        for i in range(4):
            s.place('tick', bar * 4 + i + 0.5, amb.bubble(900 + 500 * rng.random(), 0.03, seed=bar * 4 + i), 0.5 + 0.4 * rng.random(), pan=float(rng.uniform(-0.8, 0.8)))
    return s
