# formant "vocals": a buzzy glottal source through moving formant resonators + noise for the consonants.
# it sounds like a robot shouting through a tin can, which is exactly the point. words are phoneme lists.
import numpy as np
from .dsp import SR, ns, tt, midi_hz, saw, noise, bp, hp, lp, butter, resonators, soft, norm

# F1..F4 (Hz), adult-ish voice. size > 1 shrinks the "head" (cartoon / chipmunk)
PH = {
    'a': (730, 1090, 2440, 3400), 'ae': (660, 1720, 2410, 3400), 'e': (530, 1840, 2480, 3500),
    'i': (270, 2290, 3010, 3600), 'I': (390, 1990, 2550, 3600), 'o': (570, 840, 2410, 3400),
    'O': (450, 800, 2830, 3500), 'u': (300, 870, 2240, 3400), 'U': (440, 1020, 2240, 3400),
    'uh': (640, 1190, 2390, 3400), 'er': (490, 1350, 1690, 3300),
    'n': (280, 1700, 2600, 3400), 'ng': (280, 2000, 2700, 3400), 'm': (280, 1000, 2200, 3300),
    'l': (360, 1050, 2600, 3400), 'r': (420, 1300, 1600, 3200), 'w': (300, 700, 2200, 3300), 'y': (260, 2300, 3050, 3600),
}
# consonants: kind, noise centre, noise q, loudness
CONS = {
    's': ('f', 6500, 0.3, 0.5), 'sh': ('f', 2800, 0.55, 0.6), 'f': ('f', 4000, 0.1, 0.25), 'h': ('h', 0, 0, 0.35),
    'v': ('vf', 3500, 0.1, 0.2), 'z': ('vf', 6000, 0.3, 0.35), 'dj': ('vs', 2700, 0.5, 0.6),
    'k': ('p', 2000, 0.5, 0.9), 't': ('p', 4500, 0.4, 0.8), 'p': ('p', 900, 0.3, 0.6),
    'g': ('b', 1800, 0.5, 0.6), 'd': ('b', 3500, 0.4, 0.5), 'b': ('b', 700, 0.3, 0.5),
}
VOICED_AMP = {'n': 0.35, 'ng': 0.35, 'm': 0.35, 'l': 0.7, 'r': 0.75, 'w': 0.6, 'y': 0.7}

WORDS = {
    'jank': [('dj', .06), ('ae', .17), ('ng', .07), ('k', .05)],
    'fire': [('f', .08), ('a', .12), ('I', .08), ('er', .16)],
    'oi': [('o', .13), ('I', .12)],
    'yeah': [('y', .05), ('e', .1), ('ae', .18)],
    'go': [('g', .03), ('O', .13), ('u', .08)],
    'hey': [('h', .05), ('e', .14), ('i', .08)],
    'co': [('k', .05), ('O', .16)],
    'la': [('l', .06), ('uh', .16)],
    'cola': [('k', .05), ('O', .13), ('l', .06), ('uh', .14)],
    'or': [('o', .12), ('r', .08)],
    'der': [('d', .03), ('er', .16)],
    'order': [('o', .12), ('r', .06), ('d', .03), ('er', .16)],
    'duck': [('d', .03), ('uh', .14), ('k', .05)],
    'spoon': [('s', .09), ('p', .03), ('u', .16), ('n', .08)],
    'woo': [('w', .06), ('u', .3)],
    'guilty': [('g', .03), ('I', .1), ('l', .06), ('t', .03), ('i', .14)],
    'slip': [('s', .08), ('l', .05), ('I', .1), ('p', .04)],
    'yes': [('y', .05), ('e', .14), ('s', .1)],
    'no': [('n', .06), ('O', .14), ('u', .07)],
    'jump': [('dj', .06), ('uh', .13), ('m', .06), ('p', .04)],
    'big': [('b', .03), ('I', .12), ('g', .05)],
    'bang': [('b', .03), ('ae', .16), ('ng', .09)],
    'ah': [('a', .3)],
    'one': [('w', .05), ('uh', .12), ('n', .08)],
    'two': [('t', .04), ('u', .16)],
    'three': [('f', .05), ('r', .04), ('i', .15)],
    'four': [('f', .07), ('o', .12), ('r', .08)],
    'faster': [('f', .06), ('ae', .12), ('s', .08), ('t', .03), ('er', .12)],
    'breathe': [('b', .03), ('r', .04), ('i', .2), ('v', .08)],
    'uh': [('uh', .2)],
}


def say(word, note=50, size=1.0, dur=None, bend=-1.5, breath=0.05, seed=0, vib=0.0):
    """render one word (key of WORDS or a phoneme list). dur stretches it. returns mono"""
    seq = WORDS[word] if isinstance(word, str) else word
    total = sum(d for _, d in seq)
    k = (dur / total) if dur else 1.0
    seq = [(p, d * k if p in PH else d * min(k, 1.5)) for p, d in seq]  # consonants don't stretch much
    total = sum(d for _, d in seq)
    n = ns(total) + ns(0.03)
    t = tt(n)
    # formant track: each vowel-ish segment holds its target, transitions are smoothed (~25 ms)
    F = np.zeros((n, 4)); vamp = np.zeros(n); namp = np.zeros(n); nois = np.zeros(n)
    rng = np.random.default_rng(seed)
    pos = 0.0; last = None
    tgt_list = []
    for p, d in seq:
        a, b = ns(pos), ns(pos + d)
        if p in PH:
            last = np.array(PH[p], dtype=float) * size
            vamp[a:b] = VOICED_AMP.get(p, 1.0)
        else:
            kind, fc, q, lv = CONS[p]
            L = b - a
            src = noise(L, int(rng.integers(1 << 30)))
            if kind in ('f', 'vf', 'vs'):
                x = bp(src, fc * size ** 0.5, q) if q > 0.15 else hp(src, fc * 0.5)
                env = np.sin(np.linspace(0, np.pi, L)) ** 0.5
                nois[a:b] += x * env * lv * 2
                if kind != 'f': vamp[a:b] = 0.3
            elif kind == 'h':
                namp[a:b] = lv
            elif kind in ('p', 'b'):
                cl = int(L * 0.55)  # closure, then the burst
                br = L - cl
                x = bp(src[:br], fc * size ** 0.5, q) * np.exp(-np.arange(br) / (0.008 * SR))
                nois[a + cl:b] += x * lv * 2.5
                if kind == 'b': vamp[a:a + cl] = 0.15
                namp[a + cl:b] = lv * 0.3 * np.exp(-np.arange(br) / (0.01 * SR))
        if last is None:
            nxt = next((PH[q] for q, _ in seq if q in PH), PH['uh'])
            last = np.array(nxt, dtype=float) * size
        F[a:b] = last
        pos += d
    F[ns(pos):] = last
    for j in range(4): F[:, j] = butter(np.pad(F[:, j], (ns(0.05), 0), mode='edge'), 14)[ns(0.05):]  # smooth glides
    vamp = butter(vamp, 60); namp = butter(namp, 80)
    # glottal source: saw + jitter, tilted down
    f0 = midi_hz(note + bend * (t / total) + vib * np.sin(2 * np.pi * 5.5 * t) + butter(rng.normal(0, 1, n), 20) * 0.1)
    g = lp(saw(f0), 2500 * size, 0.0) + 0.3 * saw(f0)
    asp = noise(n, seed + 7) * (namp + breath * vamp)
    exc = g * vamp + asp
    bw = np.tile(np.array([80, 110, 160, 220.0]) * size ** 0.5, (n, 1))
    gains = np.tile(np.array([1.0, 0.7, 0.45, 0.25]), (n, 1))
    y = resonators(np.ascontiguousarray(exc), np.ascontiguousarray(F), np.ascontiguousarray(bw), np.ascontiguousarray(gains))
    y = norm(y, 0.8) + nois * 0.35
    edge = np.minimum(1, t / 0.005) * np.clip((total + 0.03 - t) / 0.02, 0, 1)
    return soft(y * 1.4, 1) * edge


def stutter(word, reps=3, gap=0.09, chop=0.06, **kw):
    """'J-J-J-JANK': the first chop of the word repeated, then the whole thing"""
    w = say(word, **kw)
    c = w[:ns(chop)] * np.linspace(1, 0.2, ns(chop)) ** 0.3
    out = np.zeros(ns(gap) * reps + len(w))
    for r in range(reps): out[ns(gap) * r:ns(gap) * r + len(c)] += c
    out[ns(gap) * reps:] += w
    return out
