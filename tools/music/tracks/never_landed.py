# NEVER LANDED: 158 bpm hardtek in G minor (Gm Eb Bb F) with a vocaloid-style lead. the training dummy became a pop
# idol: a bright synthesized singer on exact notes with quick idol slides, rolling tek kick, a heavy sliding 808,
# acid, rave chords. lyrics are original and about the game ("I never landed... jank jank fire in the sky").
# joke: in the floaty break the idol glitches ("ne-ne-ne-ne-ver") and the whole track stutters into the drop.
import numpy as np
from jf.song import Song
from jf.dsp import ns, nm, midi_hz
from jf import inst, toys, voice
from jf.kit import (gate_to_kicks, P, Reverb, Delay, Chorus, Distortion, Compressor, HighpassFilter, LowpassFilter, PeakFilter, Phaser,
                    LowShelfFilter, HighShelfFilter, steps, kicks, riff, shift, at_bar, acidpat, diatonic, lyric)

TITLE = 'Never Landed'
ARTIST = 'Target Dummy Idol'
KEY = [7, 9, 10, 0, 2, 3, 5]  # G minor
BPM = 158
TARGET = -8.0

INTRO, VERSE, PRE, CH1, BREAK, DROP, VERSE2, CH3, OUTRO, END = 0, 8, 16, 24, 40, 48, 64, 72, 88, 96
CHORDS = [[nm('G3'), nm('Bb3'), nm('D4')], [nm('Eb3'), nm('G3'), nm('Bb3')], [nm('Bb3'), nm('D4'), nm('F4')], [nm('F3'), nm('A3'), nm('C4')]]
ROOT808 = [nm('G1'), nm('Eb1'), nm('Bb1'), nm('F1')]
KICKNOTE = [nm('G1'), nm('G1'), nm('F1'), nm('F1')]
ACID_STEPS = [0, -2, 2, -1]  # the acid riff follows Gm Eb Bb F along G minor

# syllables -> phonemes (the voice's phoneme set: see jf/voice.py)
SYL = {
    'I': [('a', .1), ('I', .08)], 'ne': [('n', .05), ('e', .1)], 'ver': [('v', .05), ('er', .1)],
    'lan': [('l', .05), ('ae', .12), ('n', .05)], 'ded': [('d', .03), ('I', .1), ('d', .03)],
    'fi': [('f', .06), ('a', .1), ('I', .06)], 're': [('er', .15)], 'in': [('I', .08), ('n', .05)],
    'the': [('d', .03), ('uh', .08)], 'sky': [('s', .07), ('k', .03), ('a', .1), ('I', .07)],
    'bye': [('b', .03), ('a', .12), ('I', .08)], 'la': [('l', .05), ('a', .15)],
    'my': [('m', .05), ('a', .1), ('I', .06)], 'hand': [('h', .05), ('ae', .12), ('n', .05), ('d', .03)],
    'mar': [('m', .05), ('a', .12), ('r', .05)], 'bles': [('b', .03), ('uh', .06), ('l', .06), ('z', .06)],
    'on': [('o', .1), ('n', .05)], 'floor': [('f', .06), ('l', .04), ('o', .12), ('r', .06)],
    'slide': [('s', .07), ('l', .04), ('a', .12), ('I', .06), ('d', .03)], 'want': [('w', .05), ('o', .1), ('n', .04), ('t', .03)],
    'need': [('n', .05), ('i', .12), ('d', .03)], 'more': [('m', .05), ('o', .12), ('r', .07)],
}
CHORUS = ('I:D5:2 ne:D5:2 ver:C5:2 lan:Bb4:4 ded:G4:4 _:2 '
          'I:G4:2 ne:Bb4:2 ver:C5:2 lan:Eb5:4 ded:D5:4 _:2 '
          'jank:F5:3 jank:F5:3 fi:D5:2 re:Bb4:2 in:C5:2 the:D5:4 '
          'sky:C5:8 _:2 la:A4:2 la:C5:2 la:F5:2 '
          'I:D5:2 ne:D5:2 ver:C5:2 lan:Bb4:4 ded:G4:4 _:2 '
          'I:G4:2 ne:Bb4:2 ver:C5:2 lan:Eb5:4 ded:G5:4 _:2 '
          'no:F5:4 no:D5:4 no:Bb4:6 _:2 '
          'bye:C5:4 bye:A4:4 bye:F4:6 _:2')
VERSE_A = ('spoon:G4:3 in:G4:3 my:Bb4:2 hand:D5:6 _:2 '
           'mar:Eb5:3 bles:D5:3 on:Bb4:2 the:G4:2 floor:Bb4:6 '
           'slip:F4:2 slip:Bb4:2 slip:D5:2 _:2 slide:F5:8 '
           'I:F5:2 want:Eb5:2 more:C5:10 _:2')
VERSE_B = VERSE_A.replace('I:F5:2 want:Eb5:2 more:C5:10', 'I:F5:2 need:Eb5:2 more:D5:10')
FLOAT = ('I:D5:4 ne:D5:4 ver:C5:4 lan:Bb4:8 ded:G4:8 _:4 '
         'jank:F5:4 fi:D5:4 re:Bb4:4 in:C5:4 the:D5:4 sky:C5:12')
PRE_LA = 'la:G4:2 la:Bb4:2 la:D5:4 la:C5:2 la:Bb4:2 la:A4:4 ' * 4
ACID = "G2 . G2 G3' . G2 Bb2~ C3 G2 . F2' G2 . G3~ F3 D3'"


def build():
    s = Song(TITLE, BPM, END)
    N = s.N
    s.eq = [LowShelfFilter(60, -2.0, 0.7), PeakFilter(300, -1.5, 0.8), PeakFilter(3200, 3.5, 0.6), HighShelfFilter(8000, 3.0, 0.7)]
    s.levels = dict(sing=-1.5, harm=-8, lead=-8, pad=-12, stab=-6.5, acid=-5.5, bass=-5.5, hats=-10, clap=-7.5, fx=-7, chop=-6)
    s.bus('kick', 1.0, auto=[(0, 400), (7 * 4, 1500), (8 * 4 - 0.01, 1500), (8 * 4, 20000), (OUTRO * 4 + 16, 20000), (END * 4, 600)])
    s.bus('bass', 1.0, P([HighpassFilter(28), Compressor(-14, 3, 3, 80)]), duck=0.93, duck_rel=0.09)
    s.bus('hats', 1.0, P([HighpassFilter(700)]), duck=0.3)
    s.bus('clap', 1.0, P([Reverb(0.4, 0.5, 0.22, 0.88, 0.7)]))
    s.bus('sing', 1.0, P([HighpassFilter(180), Compressor(-18, 4, 3, 80), HighShelfFilter(5000, 3.0, 0.7),
                          Delay(60 / BPM * 0.75, 0.25, 0.14), Reverb(0.45, 0.5, 0.2, 0.9, 0.8)]), duck=0.2)
    s.bus('harm', 1.0, P([HighpassFilter(250), Chorus(0.6, 0.3, 8, 0, 0.5), Reverb(0.6, 0.5, 0.3, 0.8, 1.0)]), duck=0.3, width=0.8)
    s.bus('chop', 1.0, P([HighpassFilter(200), Delay(60 / BPM * 0.5, 0.35, 0.25), Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), width=0.6)
    s.bus('lead', 1.0, P([HighpassFilter(300), Chorus(0.5, 0.3, 7, 0, 0.4), Reverb(0.6, 0.5, 0.25, 0.8, 1.0)]), duck=0.6, width=0.9)
    s.bus('pad', 1.0, P([HighpassFilter(200), Chorus(0.3, 0.3, 8, 0, 0.5), Reverb(0.8, 0.5, 0.4, 0.7, 1.0)]), width=1.0, duck=0.5,
          auto=[(0, 900), (8 * 4, 6000), (OUTRO * 4, 6000), (END * 4, 900)])
    s.bus('stab', 1.0, P([HighpassFilter(180), Reverb(0.5, 0.5, 0.22, 0.85, 1.0)]), duck=0.55, width=0.5)
    s.bus('acid', 1.0, P([HighpassFilter(110), Delay(60 / BPM * 0.75, 0.3, 0.16), Reverb(0.3, 0.5, 0.1, 0.95, 0.6)]), duck=0.45, width=0.3)
    s.bus('fx', 1.0, P([Reverb(0.5, 0.5, 0.2, 0.9, 1.0)]), duck=0.2)

    ch = lambda bar: bar % 4

    # ---------------- kick: rolling tek 4/4 (none in the break), rolls on phrase ends
    kb = []
    for bar in list(range(4, BREAK)) + list(range(DROP, END)):
        kb += [bar * 4 + i for i in range(4)]
        if bar % 8 == 7 and bar >= CH1 and bar < OUTRO and bar != BREAK - 1: kb += [bar * 4 + 3.5, bar * 4 + 3.75]
    kicks(s, 'kick', kb, lambda b: KICKNOTE[ch(int(b // 4))], 'tek')

    # ---------------- the 808: between the kicks, octave slides, follows the chords
    EVEN = [(2, 0, 0), (6, 0, 0), (10, 0, 0), (11, 12, 1), (14, 0, 0)]
    ODD = [(2, 0, 0), (5, 0, 0), (9, 0, 0), (13, 7, 0), (15, 12, 1)]
    hits = []
    for bar in list(range(VERSE, BREAK)) + list(range(DROP, END)):
        for st, iv, sl in (ODD if bar % 2 else EVEN): hits.append((bar * 4 + st / 4, ROOT808[ch(bar)] + iv, sl))
    hits.append(((BREAK + 7) * 4 + 2, ROOT808[3] + 12, 0))  # one boom under the glitch
    hits.sort()
    e8 = [(b, min((hits[k + 1][0] if k + 1 < len(hits) else b + 1) - b, 2.0), m, 1.0, sl) for k, (b, m, sl) in enumerate(hits)]
    s.add('bass', inst.eight08(s.notes(gate_to_kicks(s, e8)), N, decay=0.5, drive=3.0))

    # ---------------- hats + claps
    for bar in range(4, END):
        if BREAK <= bar < DROP: continue
        pat = '..o...o...o...o.' if bar < VERSE else 'h.o.h.ohh.o.h.oh'
        for b, c in steps(pat, bar):
            s.place('hats', b, inst.openhat(0.09, 8000) if c == 'o' else inst.hat(0.025, 10000, seed=int(b * 4)), 1.0 if c == 'o' else 0.4)
        if PRE <= bar < BREAK or DROP <= bar < OUTRO:
            for b in (bar * 4 + 1, bar * 4 + 3): s.place('clap', b, inst.clap(0.2, 1500))

    # ---------------- chords: pad in the intro/break/outro, rave stabs in the choruses
    pad = [(bar * 4, 4, CHORDS[ch(bar)], 0.8) for bar in list(range(INTRO, VERSE)) + list(range(BREAK, DROP)) + list(range(OUTRO, END))]
    s.add('pad', inst.supersaw(s.notes(pad), N, cut=3000, a=0.3, r=0.7))
    st = []
    for bar in list(range(PRE, BREAK)) + list(range(DROP, VERSE2)) + list(range(CH3, OUTRO)):
        for b, _ in steps('..x...x...x..x.x' if bar >= CH1 else '..x...x...x...x.', bar): st.append((b, 0.2, [m + 12 for m in CHORDS[ch(bar)]], 0.9))
    s.add('stab', inst.stab(s.notes(st), N))

    # ---------------- acid in the second verse and the last chorus
    ac = []
    for bar in list(range(VERSE2, OUTRO)):
        ac += diatonic(acidpat(ACID, bar), ACID_STEPS[ch(bar)], KEY)
    s.add('acid', inst.acid(s.notes(shift(ac, 0, 12)), N, cut=320, envmod=3000, res=0.84, decay=0.13))

    # ---------------- the idol sings
    sing = lambda text, bar, **k: voice.sing(s, k.pop('bus', 'sing'), lyric(text, bar), SYL, **k)
    for bar in (VERSE, VERSE2): sing(VERSE_A, bar, seed=bar); sing(VERSE_B, bar + 4, seed=bar + 1)
    for bar in (CH1, CH1 + 8, DROP, DROP + 8, CH3, CH3 + 8): sing(CHORUS, bar, seed=bar)
    for bar in (CH1 + 8, DROP, DROP + 8, CH3 + 8):  # a harmony a third above, wider and softer
        voice.sing(s, 'harm', diatonic(lyric(CHORUS, bar), 2, KEY), SYL, size=1.34, seed=bar + 50)
    sing(PRE_LA, PRE, bus='chop', seed=7)
    sing(FLOAT, BREAK, seed=40, vib=0.4); sing(FLOAT, BREAK + 4, seed=44, vib=0.4)
    voice.sing(s, 'harm', [(b, d, m - 12, w) for b, d, m, w in lyric(FLOAT, BREAK + 4)], SYL, size=1.15, seed=60)
    # lead synth doubles the chorus an octave up in the drop and the last chorus
    ld = [(b, d * 0.9, m + 12) for b, d, m, w in lyric(CHORUS, DROP) + lyric(CHORUS, DROP + 8) + lyric(CHORUS, CH3 + 8)]
    s.add('lead', inst.supersaw(s.notes(ld), N, cut=6000))
    # intro + outro chops
    for b, m in ((6 * 4, nm('D5')), (6 * 4 + 1.5, nm('C5')), (7 * 4, nm('Bb4')), (7 * 4 + 1.5, nm('A4'))):
        voice.sing(s, 'chop', [(b, 1, m, 'la')], SYL, seed=int(b))
    sing('bye:C5:4 bye:A4:4 bye:F4:6 _:2', OUTRO + 3, seed=90)
    sing('bye:C5:4 bye:A4:4 bye:F4:6 _:2', OUTRO + 7, bus='chop', seed=91)

    # ---------------- the glitch: the idol skips ("ne-ne-ne-ne-ver") and the track stutters into the drop
    g0 = (BREAK + 7) * 4
    for i in range(6):
        voice.sing(s, 'sing', [(g0 + i * 0.25, 0.25, nm('D5') + [0, 0, 2, 3, 5, 7][i], 'ne')], SYL, seed=70 + i)
    voice.sing(s, 'sing', [(g0 + 1.5, 0.5, nm('A5'), 'ver')], SYL, seed=77)
    s.repeat(g0 + 2, 2, 0.125)
    s.place('fx', (BREAK + 4) * 4, inst.riser(float(s.t(DROP * 4) - s.t((BREAK + 4) * 4))), 0.7)
    for bar in range(PRE + 4, CH1):  # snare build into the first chorus
        div = 2 if bar < PRE + 6 else (4 if bar < PRE + 7 else 8)
        for i in range(4 * div):
            b = bar * 4 + i / div; u = (b - (PRE + 4) * 4) / 16
            s.place('clap', b, inst.snare(0.08, 210 + u * 160, seed=i), 0.25 + 0.6 * u)
    s.place('fx', (PRE + 4) * 4, inst.riser(float(s.t(CH1 * 4) - s.t((PRE + 4) * 4))), 0.7)
    s.place('fx', 4 * 4, inst.riser(float(s.t(VERSE * 4) - s.t(4 * 4))), 0.5)
    for bar in (VERSE, CH1, DROP, CH3):
        s.place('fx', bar * 4, inst.crash(1.8), 0.6); s.place('fx', bar * 4, inst.impact(1.8, 19), 0.8)
    return s
