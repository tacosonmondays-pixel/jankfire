# instruments: drums, bass, leads. one-shots return a mono array; "line" instruments take a list of notes in seconds
# [(t0, dur, midi, vel, extra...)] and return one continuous mono signal of length n (so glides and legato work).
import numpy as np
from pedalboard import Pedalboard, Distortion, Compressor, Limiter, HighpassFilter, LowpassFilter, PeakFilter, Chorus, Reverb
from .dsp import (SR, ns, tt, midi_hz, saw, pulse, sine, tri, noise, lp, bp, hp, adsr, expdec, fade, soft, norm, butter)


def _pb(x, board):
    return board(np.asarray(x, dtype=np.float32)[None, :], SR)[0].astype(float)


# ------------------------------------------------------------------ kicks
_kcache = {}


def gabber_kick(note=29, length=0.34, drive=28.0, f0=445.0, tau_p=0.022, tau_a=0.30, tone=7500.0, punch=1.0, seed=1):
    """the hardcore kick: a fast sine sweep 445 Hz -> the note, then crushed so its tail rings AT the note (it tunes)"""
    key = ('g', note, round(length, 3), drive, f0, tau_p, tau_a, tone, punch)
    if key in _kcache: return _kcache[key]
    n = ns(length); t = tt(n)
    f1 = float(midi_hz(note))
    f = f1 + (f0 - f1) * np.exp(-t / tau_p) + (f0 * 2.2) * np.exp(-t / 0.0025)
    env = np.minimum(1, t / 0.0008) * (0.25 + 0.75 * np.exp(-t / tau_a))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env
    x += punch * 0.5 * hp(noise(n, seed), 2500) * np.exp(-t / 0.0025)  # the click
    x = _pb(x * 0.9, Pedalboard([PeakFilter(f1 * 2.0, 6, 0.8), Distortion(drive), HighpassFilter(28),
                                 PeakFilter(330, -5.0, 0.9), PeakFilter(2600, 3.0, 1.0), LowpassFilter(tone),
                                 Compressor(-12, 4, 0.5, 60), Limiter(-0.5, 60)]))
    # gate: hold, then a short release so back-to-back kicks don't smear
    x *= np.clip((length - t) / 0.018, 0, 1)
    x = fade(x, 0.0, 0.004)
    _kcache[key] = x
    return x


def tek_kick(note=33, length=0.30, drive=17.0):
    """hard tek: punchier, shorter sweep, less crushed, leaves room for the rumble + bass"""
    return gabber_kick(note, length, drive=drive, f0=380.0, tau_p=0.014, tau_a=0.11, tone=9000.0, punch=1.3)


def rumble(kick, length=0.25):
    """kick -> long dark reverb -> distortion -> lowpass: the rolling tek rumble (place it on the off-beat 16ths)"""
    x = np.concatenate([kick[:ns(0.05)], np.zeros(ns(length))])
    x = _pb(x, Pedalboard([Reverb(0.7, 0.2, 1.0, 0.0, 1.0), Distortion(14), LowpassFilter(160), HighpassFilter(35)]))
    x = norm(x, 0.9)
    return fade(x[:ns(length)] * expdec(ns(length), length * 0.5, 0.01), 0.003, 0.02)


# ------------------------------------------------------------------ drums
def hat(length=0.04, tone=8000.0, seed=None, metal=0.5):
    n = ns(length); t = tt(n)
    m = sum(pulse(np.full(n, f), 0.5) for f in (317, 459, 543, 731, 865, 1031)) / 6  # 808-ish metal
    x = (1 - metal) * noise(n, seed) + metal * m
    x = hp(bp(x, tone * 1.1, 0.3), tone)
    return x * expdec(n, length / 3.5, 0.0005)


def openhat(length=0.18, tone=7000.0, seed=None):
    return hat(length, tone, seed, 0.6) * 1.2


def clap(length=0.22, tone=1400.0, seed=None):
    n = ns(length); t = tt(n)
    e = np.zeros(n)
    for k, d in enumerate((0.0, 0.009, 0.018, 0.026)):
        e += np.where(t >= d, np.exp(-(t - d) / (0.006 if k < 3 else 0.06)), 0) * (t >= d)
    x = bp(noise(n, seed), tone, 0.55) * e
    return soft(x * 1.6, 1.2)


def snare(length=0.16, tone=190.0, seed=None, snap=1.0):
    n = ns(length); t = tt(n)
    body = np.sin(2 * np.pi * np.cumsum(tone * (1 + 0.6 * np.exp(-t / 0.01))) / SR) * np.exp(-t / 0.045)
    sn = hp(noise(n, seed), 1200) * np.exp(-t / 0.05) * snap
    return soft(body * 0.7 + sn * 0.8, 1.5)


def crash(length=1.6, seed=None):
    n = ns(length)
    x = hp(noise(n, seed), 4000) * 0.6 + hat(length, 6000, seed, 0.8) * 0.5
    return x * expdec(n, length / 3, 0.001)


def riser(length, f_from=300.0, f_to=9000.0, seed=None):
    """white-noise sweep up, for builds"""
    n = ns(length); u = np.linspace(0, 1, n)
    fc = f_from * (f_to / f_from) ** (u ** 1.5)
    x = bp(noise(n, seed), fc, 0.6) + 0.3 * hp(noise(n, seed), fc)
    return x * (u ** 1.3)


def downer(length=1.5, seed=None):
    n = ns(length); u = np.linspace(0, 1, n)
    x = lp(noise(n, seed), 9000 * (1 - u) ** 2 + 200, 0.4)
    return x * (1 - u) ** 1.5


def impact(length=2.0, note=24):
    """big boom for drops: sub drop + noise"""
    n = ns(length); t = tt(n)
    f = midi_hz(note) * (1 + 3 * np.exp(-t / 0.05))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.6)
    x += lp(noise(n), 1200) * np.exp(-t / 0.2) * 0.5
    return soft(x * 1.5, 1.0)


# ------------------------------------------------------------------ line instruments
def _contour(notes, n, glide=0.03, dip=0.0, dip_t=0.06, vib=0.0, vib_hz=5.5, vib_delay=0.15):
    """per-sample midi pitch + gate for a mono line. notes = [(t0, dur, midi, ...)].
    glide = portamento time between notes, dip = semitones the pitch scoops up from at each attack (hoover)"""
    pitch = np.full(n, float(notes[0][2]) if notes else 60.0)
    gate = np.zeros(n); vel = np.zeros(n); start = np.full(n, -1.0)
    prev = None
    for k, nt in enumerate(notes):
        t0, d, m = nt[0], nt[1], nt[2]
        v = nt[3] if len(nt) > 3 else 1.0
        a, b = ns(t0), min(n, ns(t0 + d))
        if a >= n: break
        nxt = notes[k + 1][0] if k + 1 < len(notes) else 1e9
        end = min(n, ns(nxt)) if nxt < t0 + d + 0.3 else min(n, b + ns(0.3))
        tl = (np.arange(a, end) - a) / SR
        p = np.full(len(tl), float(m))
        if prev is not None and glide > 0 and t0 - prev[1] < 0.02:
            p = m + (prev[0] - m) * np.exp(-tl / (glide / 3))
        if dip:
            p = p - dip * np.exp(-tl / (dip_t / 3))
        if vib:
            p = p + vib * np.sin(2 * np.pi * vib_hz * tl) * np.clip((tl - vib_delay) / 0.2, 0, 1)
        pitch[a:end] = p
        gate[a:b] = 1.0; vel[a:end] = v; start[a:end] = t0
        prev = (m, t0 + d)
    return pitch, gate, vel


from numba import njit


@njit(cache=True)
def _smooth(g, up, dn):
    out = np.empty_like(g); y = 0.0
    for i in range(g.shape[0]):
        c = up if g[i] > y else dn
        y += (g[i] - y) * c
        out[i] = y
    return out


def hoover(notes, n, detune=0.22, voices=7, dip=4.0, glide=0.06, bright=3800.0, seed=3):
    """the rave hoover: a stack of detuned saws + pulses an octave down, scooping up into each note, gliding between"""
    pitch, gate, vel = _contour(notes, n, glide=glide, dip=dip, dip_t=0.09, vib=0.15, vib_hz=6.0)
    rng = np.random.default_rng(seed)
    f = midi_hz(pitch)
    x = np.zeros(n)
    for k in range(voices):
        d = detune * (k / (voices - 1) * 2 - 1) if voices > 1 else 0
        drift = 1 + 0.002 * np.sin(2 * np.pi * (0.3 + 0.2 * rng.random()) * tt(n) + rng.random() * 6)
        x += saw(f * 2 ** (d / 12) * drift)
    pw = 0.5 + 0.35 * np.sin(2 * np.pi * 0.8 * tt(n))
    x += 1.2 * pulse(f / 2, pw) + 0.9 * pulse(f * 2 ** (-12.08 / 12), 1 - pw)
    env = _smooth(gate, 1 - np.exp(-1 / (0.006 * SR)), 1 - np.exp(-1 / (0.07 * SR)))
    x = lp(x / voices, bright * (0.6 + 0.4 * env), 0.15) * env * np.maximum(vel, 0.0)
    return x


def supersaw(notes, n, detune=0.18, voices=5, cut=5000.0, a=0.003, r=0.12, seed=5):
    """poly-ish: each note rendered separately (chords ok). notes = (t0, dur, midi|list, vel)"""
    out = np.zeros(n)
    for t0, d, ms, *rest in notes:
        v = rest[0] if rest else 1.0
        ms = ms if isinstance(ms, (list, tuple)) else [ms]
        a0 = ns(t0); L = min(n - a0, ns(d + r))
        if L <= 0: continue
        tl = tt(L); x = np.zeros(L)
        for m in ms:
            for k in range(voices):
                dd = detune * (k / max(1, voices - 1) * 2 - 1)
                x += saw(np.full(L, midi_hz(m) * 2 ** (dd / 12)))
        env = adsr(L, a, 0.2, 0.75, r, gate=d)
        x = lp(x / (voices * len(ms)) ** 0.7, cut * (0.35 + 0.65 * np.exp(-tl / 0.25)), 0.1) * env * v
        out[a0:a0 + L] += x
    return out


def stab(notes, n, cut=6000.0, decay=0.12, seed=7):
    """rave stab: a minor-chord blast with a snappy filter (and an octave squared under it)"""
    out = np.zeros(n)
    for t0, d, ms, *rest in notes:
        v = rest[0] if rest else 1.0
        ms = ms if isinstance(ms, (list, tuple)) else [ms]
        a0 = ns(t0); L = min(n - a0, ns(d + 0.15))
        if L <= 0: continue
        tl = tt(L); x = np.zeros(L)
        for m in ms:
            for dd in (-0.15, 0, 0.13):
                x += saw(np.full(L, midi_hz(m) * 2 ** (dd / 12)))
            x += 0.6 * pulse(np.full(L, midi_hz(m - 12)), 0.3)
        env = adsr(L, 0.001, decay, 0.0, 0.05, gate=d) * 0.8 + 0.2 * np.exp(-tl / (decay * 3))
        x = lp(x / len(ms), cut * np.exp(-tl / (decay * 1.2)) + 200, 0.35) * env * v
        out[a0:a0 + L] += soft(x * 1.5, 1.0)
    return out


def acid(notes, n, wave='saw', cut=380.0, envmod=3200.0, res=0.82, decay=0.16, drive=2.2):
    """303-style: notes (t0, dur, midi, vel, accent, slide). slide = glide into the next note without retriggering"""
    pitch = np.zeros(n); gate = np.zeros(n); fenv = np.zeros(n); acc = np.zeros(n)
    last = None
    for k, nt in enumerate(notes):
        t0, d, m = nt[0], nt[1], nt[2]
        v = nt[3] if len(nt) > 3 else 1.0
        ac = nt[4] if len(nt) > 4 else 0
        sl_in = last is not None and len(last) > 5 and last[5] and abs(last[0] + last[1] - t0) < 0.02
        a, b = ns(t0), min(n, ns(t0 + d))
        nx = min(n, ns(notes[k + 1][0])) if k + 1 < len(notes) else min(n, b + ns(0.2))
        tl = (np.arange(a, nx) - a) / SR
        if sl_in:
            pitch[a:nx] = m + (last[2] - m) * np.exp(-tl / 0.02)
            fenv[a:nx] = fenv[a - 1] * np.exp(-tl / decay) if a > 0 else 0
        else:
            pitch[a:nx] = m
            fenv[a:nx] = np.exp(-tl / (decay * (0.6 if ac else 1)))
        slide_out = len(nt) > 5 and nt[5]
        gate[a:(nx if slide_out else b)] = v
        acc[a:nx] = ac
        last = nt
    f = midi_hz(pitch)
    x = saw(f) if wave == 'saw' else pulse(f, 0.5)
    env = _smooth(gate, 1 - np.exp(-1 / (0.002 * SR)), 1 - np.exp(-1 / (0.012 * SR)))
    fc = cut + envmod * fenv * (1 + 0.8 * acc)
    y = lp(x, fc, res + 0.1 * acc)
    y = soft(y * drive * (1 + 0.5 * acc), 1.0) * env
    return y


def bass(notes, n, cut=900.0, sub=0.8, decay=0.09, drive=1.6):
    """bouncy off-beat bass: saw + sine sub with a quick filter pluck"""
    out = np.zeros(n)
    for t0, d, m, *rest in notes:
        v = rest[0] if rest else 1.0
        a0 = ns(t0); L = min(n - a0, ns(d + 0.03))
        if L <= 0: continue
        tl = tt(L); f = np.full(L, midi_hz(m))
        x = lp(saw(f, 0.0), cut * (0.3 + 2.5 * np.exp(-tl / decay)), 0.35) + sub * np.sin(2 * np.pi * f * tl)
        x = soft(x * drive, 1.0) * adsr(L, 0.002, 0.08, 0.7, 0.03, gate=d) * v
        out[a0:a0 + L] += x
    return out


def siren(t0, dur, n, lo=72, hi=79, rate=2.0, shape='square', out=None):
    """alarm: nee-naw between two notes (shape 'square' = two-tone, 'sweep' = wail)"""
    out = np.zeros(n) if out is None else out
    a0 = ns(t0); L = min(n - a0, ns(dur))
    if L <= 0: return out
    tl = tt(L)
    if shape == 'square':
        p = np.where((tl * rate) % 1 < 0.5, hi, lo).astype(float)
        p = butter(p, 30)
    else:
        p = lo + (hi - lo) * (0.5 - 0.5 * np.cos(2 * np.pi * rate * tl))
    f = midi_hz(p)
    x = pulse(f, 0.5) * 0.6 + saw(f * 1.005) * 0.4
    x = lp(x, 3500, 0.2) * adsr(L, 0.02, 0.1, 1.0, 0.1)
    out[a0:a0 + L] += soft(x * 2, 1)
    return out


def piano_ish(notes, n, seed=9):
    """bright rave-piano-ish: hammered fm chord, fast decay (only used if the soundfont piano isn't wanted)"""
    out = np.zeros(n)
    for t0, d, ms, *rest in notes:
        v = rest[0] if rest else 1.0
        ms = ms if isinstance(ms, (list, tuple)) else [ms]
        a0 = ns(t0); L = min(n - a0, ns(d + 0.4))
        if L <= 0: continue
        tl = tt(L); x = np.zeros(L)
        for m in ms:
            f = midi_hz(m)
            mod = np.sin(2 * np.pi * f * 2 * tl) * 2.5 * np.exp(-tl / 0.15)
            x += np.sin(2 * np.pi * f * tl + mod) * np.exp(-tl / 0.7)
        out[a0:a0 + L] += x / len(ms) * v * adsr(L, 0.001, 0.4, 0.4, 0.2, gate=d)
    return out
