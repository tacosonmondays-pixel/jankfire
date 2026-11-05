# pattern helpers shared by the tracks
import numpy as np
from pedalboard import (Pedalboard, Reverb, Delay, Chorus, Distortion, Compressor, HighpassFilter, LowpassFilter,
                        PeakFilter, Phaser, Bitcrush, Gain, HighShelfFilter, LowShelfFilter)
from .dsp import SR, ns, nm, midi_hz
from . import inst

P = Pedalboard


def steps(pattern, bar=0, every=1):
    """'x..x..x.' -> beat offsets of the hits (each char = a 16th). '-' / '.' rest, any other char hits.
    returns [(beat, char)]"""
    return [(bar * 4 + i / 4, c) for i, c in enumerate(pattern.replace(' ', '')) if c not in '.-']


def kicks(s, bus, beats, note_at, kind='gabber', gain=1.0, maxlen=0.6, **kw):
    """place kicks at beats (sorted), each tuned by note_at(beat) and cut just before the next one"""
    beats = sorted(set(beats))
    for i, b in enumerate(beats):
        nxt = beats[i + 1] if i + 1 < len(beats) else b + 1
        L = min(maxlen, float(s.t(nxt) - s.t(b)) - 0.002)
        k = (inst.gabber_kick if kind == 'gabber' else inst.tek_kick)(note_at(b), round(L, 3), **kw)
        s.place(bus, b, k, gain)
        s.kick(b)


def riff(text, bar0=0, octave=0, length_scale=1.0):
    """'F4:2 . G4:1 Ab4:3' -> note list (beat, beats, midi). token = NOTE:len16 (len in 16ths), '.' = 16th rest,
    '_:n' = n 16ths rest. reads left to right from bar0"""
    pos = bar0 * 4.0; out = []
    for tok in text.split():
        if tok == '.': pos += 0.25; continue
        name, _, ln = tok.partition(':')
        d = (int(ln) if ln else 1) * 0.25
        if name != '_': out.append((pos, d * length_scale, nm(name) + 12 * octave))
        pos += d
    return out


def shift(notes, beats=0.0, semis=0):
    return [(b + beats, d, m + semis, *r) for b, d, m, *r in notes]


def at_bar(notes, bar):
    """keep a riff's relative timing but start it at `bar`"""
    if not notes: return []
    b0 = (notes[0][0] // 4) * 4
    return shift(notes, bar * 4 - b0)


def acidpat(text, bar0=0, octave=0, gate=0.55, vel=1.0):
    """303 step pattern, one token per 16th: NOTE (staccato), NOTE' (accent), NOTE~ (slide into the next), '.' rest.
    -> [(beat, beats, midi, vel, accent, slide)]"""
    out = []
    for i, tok in enumerate(text.split()):
        if tok == '.': continue
        acc = "'" in tok; sl = '~' in tok
        name = tok.replace("'", '').replace('~', '')
        out.append((bar0 * 4 + i / 4, 0.25 if sl else 0.25 * gate, nm(name) + 12 * octave, vel, int(acc), int(sl)))
    return out


def diatonic(notes, steps, scale, sharpen=()):
    """move notes `steps` scale steps along `scale` (pitch classes, C=0). sharpen = pitch classes to raise a
    semitone afterwards (e.g. the leading tone in a V chord). keeps acid riffs in key when they follow the chords"""
    sc = sorted(scale)
    out = []
    for b, d, m, *r in notes:
        pc = m % 12; o = m // 12
        if pc not in sc: out.append((b, d, m, *r)); continue
        i = sc.index(pc) + steps
        nm2 = (o + i // len(sc)) * 12 + sc[i % len(sc)]
        if nm2 % 12 in sharpen: nm2 += 1
        out.append((b, d, nm2, *r))
    return out
