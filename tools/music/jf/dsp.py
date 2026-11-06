# low-level dsp: oscillators, filters, envelopes. per-sample loops are numba-compiled (cached to __pycache__),
# everything else is plain numpy. all mono float64 at SR unless said otherwise.
import numpy as np
from numba import njit

SR = 44100


def secs(n): return n / SR
def ns(t): return int(round(t * SR))
def tt(n): return np.arange(n) / SR


def midi_hz(m): return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69) / 12)


NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def nm(s):
    """'F#2' -> midi number. ints pass through."""
    if not isinstance(s, str): return s
    i = 1; v = NOTE[s[0].upper()]
    while i < len(s) and s[i] in '#b':
        v += 1 if s[i] == '#' else -1; i += 1
    return v + 12 * (int(s[i:]) + 1)


# ------------------------------------------------------------------ oscillators (phase from a per-sample freq array)
def phase(freq, ph0=0.0):
    """cumulative phase in cycles (0..inf) for a per-sample frequency array"""
    return ph0 + np.cumsum(np.asarray(freq, dtype=float)) / SR


@njit(cache=True)
def _blep(t, dt):
    if t < dt:
        t /= dt; return t + t - t * t - 1.0
    if t > 1.0 - dt:
        t = (t - 1.0) / dt; return t * t + t + t + 1.0
    return 0.0


@njit(cache=True)
def saw_bl(freq, ph0):
    """polyblep sawtooth, freq per sample"""
    n = freq.shape[0]; out = np.empty(n); p = ph0
    for i in range(n):
        dt = freq[i] / 44100.0
        out[i] = 2.0 * p - 1.0 - _blep(p, dt)
        p += dt
        if p >= 1.0: p -= 1.0
    return out


@njit(cache=True)
def pulse_bl(freq, width, ph0):
    """polyblep pulse/square, width per sample (0.5 = square)"""
    n = freq.shape[0]; out = np.empty(n); p = ph0
    for i in range(n):
        dt = freq[i] / 44100.0; w = width[i]
        v = 1.0 if p < w else -1.0
        v += _blep(p, dt)
        q = p - w
        if q < 0.0: q += 1.0
        v -= _blep(q, dt)
        out[i] = v
        p += dt
        if p >= 1.0: p -= 1.0
    return out


def saw(freq, ph0=None):
    freq = np.ascontiguousarray(freq, dtype=float)
    return saw_bl(freq, np.random.rand() if ph0 is None else ph0)


def pulse(freq, width=0.5, ph0=None):
    freq = np.ascontiguousarray(freq, dtype=float)
    w = np.ascontiguousarray(np.broadcast_to(width, freq.shape), dtype=float)
    return pulse_bl(freq, w, np.random.rand() if ph0 is None else ph0)


def sine(freq, ph0=0.0):
    return np.sin(2 * np.pi * phase(freq, ph0))


def tri(freq, ph0=0.0):
    p = phase(freq, ph0) % 1.0
    return 4 * np.abs(p - 0.5) - 1


def noise(n, seed=None):
    rng = np.random.default_rng(seed)
    return rng.uniform(-1, 1, n)


# ------------------------------------------------------------------ filters
@njit(cache=True)
def svf(x, cutoff, res, mode):
    """chamberlin-ish (zdf / cytomic) state variable filter, per-sample cutoff (Hz) + resonance 0..1.
    mode 0 lp, 1 bp, 2 hp. with a soft tanh in the loop so high res squelches instead of exploding (303-ish)."""
    n = x.shape[0]; out = np.empty(n)
    ic1 = 0.0; ic2 = 0.0
    for i in range(n):
        fc = cutoff[i]
        if fc < 10.0: fc = 10.0
        if fc > 20000.0: fc = 20000.0
        g = np.tan(np.pi * fc / 44100.0)
        k = 2.0 - 2.0 * res[i] * 0.985
        a1 = 1.0 / (1.0 + g * (g + k)); a2 = g * a1; a3 = g * a2
        v0 = x[i]
        v3 = v0 - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2.0 * v1 - ic1
        ic2 = 2.0 * v2 - ic2
        ic1 = np.tanh(ic1 * 0.7) / 0.7  # saturate the band state: the squelch
        if mode == 0: out[i] = v2
        elif mode == 1: out[i] = v1
        else: out[i] = v0 - k * v1 - v2
    return out


def lp(x, cutoff, res=0.0):
    x = np.ascontiguousarray(x, dtype=float)
    c = np.ascontiguousarray(np.broadcast_to(cutoff, x.shape), dtype=float)
    r = np.ascontiguousarray(np.broadcast_to(res, x.shape), dtype=float)
    return svf(x, c, r, 0)


def bp(x, cutoff, res=0.5):
    x = np.ascontiguousarray(x, dtype=float)
    c = np.ascontiguousarray(np.broadcast_to(cutoff, x.shape), dtype=float)
    r = np.ascontiguousarray(np.broadcast_to(res, x.shape), dtype=float)
    return svf(x, c, r, 1)


def hp(x, cutoff, res=0.0):
    x = np.ascontiguousarray(x, dtype=float)
    c = np.ascontiguousarray(np.broadcast_to(cutoff, x.shape), dtype=float)
    r = np.ascontiguousarray(np.broadcast_to(res, x.shape), dtype=float)
    return svf(x, c, r, 2)


@njit(cache=True)
def resonators(x, freqs, bws, gains):
    """parallel 2-pole resonators with time-varying freq/bw (k formants): freqs/bws/gains are (n, k). formant synthesis."""
    n = x.shape[0]; k = freqs.shape[1]; out = np.zeros(n)
    y1 = np.zeros(k); y2 = np.zeros(k)
    for i in range(n):
        s = 0.0
        for j in range(k):
            r = np.exp(-np.pi * bws[i, j] / 44100.0)
            c = 2.0 * r * np.cos(2.0 * np.pi * freqs[i, j] / 44100.0)
            y = (1.0 - r) * x[i] + c * y1[j] - r * r * y2[j]
            y2[j] = y1[j]; y1[j] = y
            s += y * gains[i, j]
        out[i] = s
    return out


def onepole_lp(x, fc):
    from scipy.signal import lfilter
    a = np.exp(-2 * np.pi * fc / SR)
    return lfilter([1 - a], [1, -a], x)


def butter(x, fc, kind='low', order=2):
    from scipy.signal import butter as b, sosfilt
    return sosfilt(b(order, fc, btype=kind, fs=SR, output='sos'), x)


# ------------------------------------------------------------------ envelopes + shaping
def adsr(n, a=0.005, d=0.1, s=0.7, r=0.05, gate=None):
    """gate = seconds held (default: whole length minus release)"""
    t = tt(n)
    g = (n / SR - r) if gate is None else gate
    e = np.where(t < a, t / max(a, 1e-6), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-6)))
    lvl_at_gate = (g / max(a, 1e-6)) if g < a else s + (1 - s) * np.exp(-(g - a) / max(d, 1e-6))
    rel = lvl_at_gate * np.exp(-(t - g) / max(r / 4, 1e-6))
    return np.where(t < g, e, rel)


def expdec(n, tau, a=0.001):
    t = tt(n)
    return np.minimum(1, t / a) * np.exp(-t / tau)


def fade(x, fin=0.002, fout=0.005):
    x = x.copy(); a = min(ns(fin), len(x)); b = min(ns(fout), len(x))
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b)
    return x


def soft(x, drive=1.0):
    return np.tanh(x * drive) / np.tanh(drive) if drive > 0 else x


def norm(x, peak=1.0):
    m = np.max(np.abs(x)) if len(x) else 0
    return x * (peak / m) if m > 0 else x


def pan2(x, p=0.0):
    """mono -> stereo (n,2), equal power, p -1..1"""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * np.sqrt(2)


def resample(x, rate):
    """play x back at a per-sample rate (array or scalar): tape stops, chipmunks"""
    rate = np.broadcast_to(rate, (len(x),)) if np.ndim(rate) == 0 else rate
    pos = np.cumsum(rate) - rate[0]
    pos = pos[pos < len(x) - 1]
    return np.interp(pos, np.arange(len(x)), x)
