# story-mode beds (OVERDUE districts): quieter, stranger instruments. an accordion with a stuck reed, far-off dogs,
# a heartbeat kick, a humming choir, wet pads, gurgles, drips, car alarms, dust and vinyl crackle.
# continuous textures are rendered a bit long and loopify()'d so they join their own start with no seam.
import numpy as np
from numba import njit
from .dsp import SR, ns, tt, midi_hz, saw, pulse, sine, tri, noise, lp, bp, hp, expdec, fade, soft, butter, norm, onepole_lp
from .inst import _contour, _smooth


def loopify(x, n, xf):
    """x (>= n + xf long) -> exactly n samples that loop: the overhang past n is crossfaded (equal power) into the
    start, so sample n-1 runs straight into sample 0. use for drones/noise beds that never stop"""
    y = x[:n].copy(); u = np.linspace(0, 1, xf)
    fi, fo = np.sin(u * np.pi / 2), np.cos(u * np.pi / 2)
    if y.ndim == 2: fi, fo = fi[:, None], fo[:, None]
    y[:xf] = x[:xf] * fi + x[n:n + xf] * fo
    return y


def per(t, L, hz, ph=0.0):
    """a sine lfo whose rate is rounded so it fits the loop a whole number of times (no jump at the loop point)"""
    k = max(1, round(L * hz))
    return np.sin(2 * np.pi * k * t / L + ph)


def slow_noise(n, hz, seed):
    """smooth random wander -1..1-ish (breath swells, drift)"""
    m = max(4, int(n / SR * hz * 4) + 4)
    pts = np.random.default_rng(seed).uniform(-1, 1, m)
    return np.interp(np.linspace(0, m - 3, n), np.arange(m), pts)


# ------------------------------------------------------------------ the Bottom
def accordion(notes, n, L, seed=71, wow=0.12):
    """notes [(t0, dur, midi|list, vel, stuck_s)]: three detuned reeds (musette wobble), wobbly tuning, bellows
    wheeze and an air leak. stuck_s > 0 = the sharp reed sticks open: it keeps honking that long after the note,
    sagging flat and wavering, then lets go with a squeak"""
    rng = np.random.default_rng(seed)
    out = np.zeros(n)
    for t0, d, ms, *rest in notes:
        v = rest[0] if rest else 0.8; stuck = rest[1] if len(rest) > 1 else 0.0
        for m in (ms if isinstance(ms, (list, tuple)) else [ms]):
            rel = 0.07; mn = ns(d + rel + stuck + 0.08); a = ns(t0)
            if a >= n: continue
            t = tt(mn); ta = t0 + t
            env = _smooth((t < d).astype(float), 1 - np.exp(-1 / (0.025 * SR)), 1 - np.exp(-1 / (rel / 3 * SR)))
            base = m + wow * per(ta, L, 0.31) + 0.5 * wow * per(ta, L, 0.83, 1.3) + 0.04 * rng.standard_normal()
            x = np.zeros(mn)
            for det, w in ((0.0, 1.0), (0.14, 0.8), (-0.09, 0.7)):
                f = midi_hz(base + det)
                x += w * (0.6 * pulse(f, 0.32) + 0.4 * saw(f))
            x *= env
            if stuck > 0:
                u = np.clip((t - d) / stuck, 0, 1)
                f = midi_hz(base + 0.14 - 0.5 * u ** 1.5 + 0.09 * np.sin(2 * np.pi * 6.5 * t))
                se = _smooth(((t >= d - 0.02) & (t < d + stuck)).astype(float), 1 - np.exp(-1 / (0.01 * SR)), 1 - np.exp(-1 / (0.004 * SR)))
                x += 0.9 * (0.6 * pulse(f, 0.3) + 0.4 * saw(f)) * se * (0.7 + 0.3 * np.sin(2 * np.pi * 3.1 * t))
                sq = np.exp(-np.maximum(t - (d + stuck), 0) / 0.035) * (t >= d + stuck - 0.01)
                x += 0.6 * bp(noise(mn, int(rng.integers(1 << 30))), midi_hz(m + 24) * (1 - 0.2 * u), 0.85) * sq
            L2 = min(mn, n - a); out[a:a + L2] += x[:L2] * v
    y = bp(out, 1150, 0.35) * 0.9 + lp(out, 2600, 0.1) * 0.6  # honky reed body, no fizz
    T = tt(n)
    bel = 0.86 + 0.14 * per(T, L, 0.42)  # bellows push/pull
    leak = bp(noise(n, seed + 1), 2300, 0.4) * 0.01 * (0.6 + 0.4 * per(T, L, 0.42, 0.5))
    return y * bel + leak


def bark(seed=0, size=1.0, barks=2, gap=0.27):
    """a dog going 'rowf rowf': buzzy pitch-jumping voice through mouth formants, a growly flutter"""
    rng = np.random.default_rng(seed)
    out = np.zeros(ns(barks * gap + 0.4))
    for i in range(barks):
        Lb = 0.15 + 0.06 * rng.random(); m = ns(Lb); t = tt(m); u = t / Lb
        f0 = (300 + 90 * rng.random()) * size
        f = f0 * (1 + 0.55 * np.sin(np.pi * np.minimum(u * 1.7, 1))) * (1 - 0.3 * u)
        src = saw(f) * 0.8 + noise(m, int(rng.integers(1 << 30))) * 0.5
        src *= 1 + 0.45 * np.sin(2 * np.pi * (26 + 12 * rng.random()) * t)
        x = bp(src, 700 * size, 0.6) * 1.0 + bp(src, 1350 * size, 0.6) * 0.7 + bp(src, 2600 * size, 0.5) * 0.3
        x *= np.minimum(1, t / 0.006) * np.exp(-t / (0.055 + 0.02 * rng.random()))
        a = ns(i * gap * (0.9 + 0.2 * rng.random())); out[a:a + m] += x
    return norm(fade(out), 0.9)


def crackle(n, seed=5, rate=7.0):
    """vinyl: sparse pops (a few big ones), a soft hiss and a little rumble. stereo, loops"""
    rng = np.random.default_rng(seed); xf = ns(0.5); m = n + xf
    ch = []
    for c in range(2):
        imp = (rng.random(m) < rate / SR) * rng.pareto(2.2, m) * np.sign(rng.uniform(-1, 1, m))
        pops = bp(np.clip(imp, -6, 6), 2600 + 800 * c, 0.3) * 0.25
        ch.append(pops + lp(noise(m, seed + 10 + c), 5000) * 0.012 + butter(noise(m, seed + 20 + c), 60) * 0.06)
    return loopify(np.stack(ch, 1), n, xf)


def warmbass(notes, n, cut=520.0, drive=1.4):
    """round upright-ish synth bass: sine + a bit of triangle, soft pluck, warm saturation"""
    pitch, gate, vel = _contour(notes, n, glide=0.02)
    f = midi_hz(pitch)
    x = sine(f) + 0.3 * tri(f) + 0.15 * sine(2 * f)
    env = _smooth(gate, 1 - np.exp(-1 / (0.004 * SR)), 1 - np.exp(-1 / (0.05 * SR)))
    x = soft(x * drive, 1.0) * env * np.maximum(vel, 0)
    return lp(x, cut, 0.1)


# ------------------------------------------------------------------ the Gut
def lub(f=46.0, length=0.5, gain=1.0, seed=0, decay=0.17):
    """one heartbeat thump: a sine dropping onto f, a wet 'thup' of noise, saturated so it reads on small speakers"""
    n = ns(length); t = tt(n)
    fr = f * (1 + 1.5 * np.exp(-t / 0.025))
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.minimum(1, t / 0.005) * np.exp(-t / decay)
    x += bp(noise(n, seed), 140, 0.55) * np.exp(-t / 0.035) * 0.9
    return fade(soft(x * 1.6, 1.3), 0.001, 0.05) * gain


def dub(seed=1):
    return lub(60.0, 0.32, 0.62, seed, decay=0.1)


@njit(cache=True)
def _fbank(x, mo, fa, fb, bw, ga, gb):
    """4 parallel resonators whose formants morph per sample between sets fa and fb (mo 0..1)"""
    n = x.shape[0]; k = fa.shape[0]; out = np.zeros(n)
    y1 = np.zeros(k); y2 = np.zeros(k)
    for i in range(n):
        s = 0.0; m = mo[i]
        for j in range(k):
            fq = fa[j] + (fb[j] - fa[j]) * m
            r = np.exp(-np.pi * bw[j] / 44100.0)
            c = 2.0 * r * np.cos(2.0 * np.pi * fq / 44100.0)
            y = (1.0 - r) * x[i] + c * y1[j] - r * r * y2[j]
            y2[j] = y1[j]; y1[j] = y
            s += y * (ga[j] + (gb[j] - ga[j]) * m)
        out[i] = s
    return out


HUM = np.array([280.0, 1000, 2200, 3300]); OOH = np.array([340.0, 780, 2350, 3300])


def choir(groups, n, L, morph, seed=81, voices=3, sway=0.12):
    """a choir humming 'mmm' on one chord. groups = [(midis, size)], size scales the formants (bigger = smaller
    heads, the sopranos). every singer drifts, has their own vibrato and breath swells; morph (n,) 0..1 opens the
    hum towards 'ooh'. the whole choir sways in pitch together, like it's breathing. returns n samples that loop"""
    rng = np.random.default_rng(seed); xf = ns(1.0); m = n + xf; T = tt(m)
    mo = np.ascontiguousarray(np.concatenate([morph, morph[:xf]]) if len(morph) == n else morph[:m], dtype=float)
    sw = sway * per(T, L, 0.07) + 0.04 * per(T, L, 0.19, 2.0)
    out = np.zeros(m)
    for midis, size in groups:
        src = np.zeros(m)
        for note in midis:
            for v in range(voices):
                vib = 0.13 * np.sin(2 * np.pi * (4.6 + 1.1 * rng.random()) * T + rng.random() * 6.28)
                drift = 0.07 * slow_noise(m, 0.15, int(rng.integers(1 << 30))) + (v - (voices - 1) / 2) * 0.07
                f = midi_hz(note + sw + vib + drift)
                swell = 0.65 + 0.35 * slow_noise(m, 0.12, int(rng.integers(1 << 30)))
                src += saw(f) * swell
        src = lp(src, 3800, 0.0) + 0.02 * bp(noise(m, int(rng.integers(1 << 30))), 1200, 0.3) * len(midis)
        bwd = np.array([60.0, 110, 170, 240])
        out += _fbank(np.ascontiguousarray(src), mo, HUM * size, OOH * size, bwd, np.array([1.0, 2.0, 2.0, 1.0]), np.array([1.0, 2.6, 2.0, 1.0]))
    return loopify(out, n, xf)


def wetpad(notes, n, cut, res=0.6, seed=91, a=0.9, r=1.6):
    """squelchy detuned-saw pad through a resonant lowpass (cut: per-sample Hz). notes (t0, dur, [midis], vel)"""
    rng = np.random.default_rng(seed); x = np.zeros(n)
    for t0, d, ms, *rest in notes:
        v = rest[0] if rest else 1.0; i0 = ns(t0); mn = ns(d + r + 0.1)
        if i0 >= n: continue
        t = tt(mn); env = np.where(t < d, np.minimum(1, t / a), np.exp(-(t - d) / (r / 4)) * np.minimum(1, d / a))
        y = np.zeros(mn)
        for mm in (ms if isinstance(ms, (list, tuple)) else [ms]):
            for det in (-0.12, 0.0, 0.1):
                y += saw(midi_hz(mm + det) * (1 + 0.002 * np.sin(2 * np.pi * (0.3 + rng.random() * 0.4) * t)))
        L2 = min(mn, n - i0); x[i0:i0 + L2] += (y * env * v)[:L2]
    return lp(x, cut, res)


def bubble(f0=250.0, length=0.09, seed=0):
    """'blup': a sine whose pitch shoots up as the bubble pops"""
    n = ns(length); t = tt(n)
    f = f0 * (1 + 1.2 * (1 - np.exp(-t / 0.02)))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / 0.002) * np.exp(-t / (length / 3))


def gurgle(length=1.6, seed=0):
    """a stomach growl (low buzzy groan, wobbling) with a cluster of bubbles blupping up through it"""
    rng = np.random.default_rng(seed); n = ns(length); t = tt(n); u = t / length
    f = (55 + 25 * rng.random()) * (1 + 0.15 * slow_noise(n, 3, seed) + 0.25 * u)
    gr = bp(saw(f) * (1 + 0.6 * np.sin(2 * np.pi * (9 + 6 * rng.random()) * t)), 320 + 200 * u, 0.6) * np.sin(np.pi * u) ** 1.5 * 0.8
    x = gr + 0.15 * lp(noise(n, seed + 1), 200) * np.sin(np.pi * u)
    k = int(6 + 8 * rng.random())
    for i in range(k):
        p = (i / k) ** 0.7 * 0.85 + 0.05 * rng.random()
        b = bubble(150 + 380 * rng.random(), 0.05 + 0.08 * rng.random(), seed + i)
        a = ns(p * length); x[a:a + len(b)] += b[:max(0, n - a)] * (0.5 + 0.5 * rng.random())
    return fade(x, 0.01, 0.1)


def squelch(length=0.4, seed=0):
    """a wet squish: a resonant band of noise falling fast, with a little sub 'schlorp' under it"""
    n = ns(length); t = tt(n); u = t / length
    fc = 2400 * (1 - u) ** 2 + 260 + 180 * np.sin(2 * np.pi * 23 * t)
    x = bp(noise(n, seed), fc, 0.82) * np.minimum(1, t / 0.008) * (1 - u) ** 1.2
    x += 0.5 * np.sin(2 * np.pi * np.cumsum(200 * (1 - 0.7 * u)) / SR) * np.exp(-t / 0.06)
    return fade(soft(x * 1.5, 1.0), 0.001, 0.02)


def drip(note=86, length=0.5):
    """a water drop 'plip' tuned to a note: a quick upward chirp that rings out"""
    n = ns(length); t = tt(n); f0 = float(midi_hz(note))
    f = f0 * (0.62 + 0.38 * (1 - np.exp(-t / 0.012)))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / 0.001) * np.exp(-t / 0.09)


# ------------------------------------------------------------------ the Commute
def car_alarm(segs, n, pitch=1.0):
    """segs = [(t0, t1, kind)]: kind 'whoop' (sweeps up), 'beep', 'nee' (two-tone), 'warble' (fast trill),
    'chirp' (quick yelps). a tinny horn speaker: a buzzy pulse through a narrow mid band"""
    f = np.full(n, 1000.0 * pitch); g = np.zeros(n)
    for t0, t1, kind in segs:
        a, b = ns(t0), min(n, ns(t1))
        if a >= n: continue
        t = tt(b - a)
        if kind == 'whoop': ph = (t / 0.45) % 1; f[a:b] = pitch * (520 + 1100 * ph ** 0.7); g[a:b] = 1
        elif kind == 'beep': f[a:b] = pitch * 1250; g[a:b] = (t / 0.25) % 1 < 0.5
        elif kind == 'nee': f[a:b] = pitch * np.where((t / 0.32) % 1 < 0.5, 760, 1020); g[a:b] = 1
        elif kind == 'warble': f[a:b] = pitch * (1000 + 320 * np.sin(2 * np.pi * 9 * t)); g[a:b] = 1
        elif kind == 'chirp': ph = (t / 0.16) % 1; f[a:b] = pitch * (1400 - 700 * ph); g[a:b] = ph < 0.8
    g = _smooth(g.astype(float), 1 - np.exp(-1 / (0.003 * SR)), 1 - np.exp(-1 / (0.006 * SR)))
    x = pulse(f, 0.4) * 0.7 + saw(f) * 0.3
    x = bp(x, 1700, 0.35) + 0.3 * bp(x, 3200, 0.5)
    return soft(x * 1.5, 1.0) * g


def dust(n, L, seed=59, gusts=1.0):
    """wasteland wind: a hollow moaning band of noise that wanders, gusts, and sand hiss riding the gusts. stereo, loops"""
    xf = ns(1.0); m = n + xf; T = tt(m); ch = []
    for c in range(2):
        ph = c * 1.7
        gust = 0.55 + 0.45 * (0.6 * per(T, L, 0.045, ph) + 0.4 * per(T, L, 0.13, 2 * ph + 1))
        fc = 380 + 260 * per(T, L, 0.07, ph) + 160 * per(T, L, 0.23, ph + 2) + 300 * gust
        moan = bp(noise(m, seed + c), fc, 0.75) * gust
        sand = hp(noise(m, seed + 10 + c), 4500) * 0.12 * gust ** 3 * gusts
        ch.append(moan + sand + 0.25 * butter(noise(m, seed + 20 + c), 120) * gust)
    return loopify(np.stack(ch, 1), n, xf)
