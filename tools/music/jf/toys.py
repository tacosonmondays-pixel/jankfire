# the wacky stuff, all synthesized from scratch: boings, kazoo, squeaky toys, rubber ducks, cash registers,
# spoons, gavels, slide whistles, a soda can opening.
import numpy as np
from .dsp import SR, ns, tt, midi_hz, saw, pulse, sine, tri, noise, lp, bp, hp, adsr, expdec, fade, soft, norm, butter, resonators
from .inst import _contour, _smooth


def boing(note=55, length=0.7, up=7.0, wob=13.0, depth=1.2):
    """cartoon spring: a buzzy twang that jumps up and wobbles (jaw-harp-ish wah on top)"""
    n = ns(length); t = tt(n)
    p = note + up * (1 - np.exp(-t / 0.03)) + depth * np.sin(2 * np.pi * wob * t) * np.exp(-t / 0.35)
    f = midi_hz(p)
    src = pulse(f, 0.25) * 0.6 + tri(f) * 0.6
    wah = 900 + 1700 * (0.5 + 0.5 * np.sin(2 * np.pi * wob * t + 1.2)) * np.exp(-t / 0.4)
    x = bp(src, wah, 0.75) * 1.4 + 0.5 * tri(f)
    return x * expdec(n, length / 3.2, 0.002)


def kazoo(notes, n, buzz=1.0, seed=11):
    """kazoo melody: a hummed voice through a buzzing membrane. scoops into notes, wobbly vibrato, nasal formants"""
    pitch, gate, vel = _contour(notes, n, glide=0.04, dip=0.6, dip_t=0.04, vib=0.22, vib_hz=5.2, vib_delay=0.15)
    rng = np.random.default_rng(seed)
    jitter = butter(rng.normal(0, 1, n), 18) * 0.02
    f = midi_hz(pitch + jitter)
    src = saw(f) + 0.5 * pulse(f, 0.12)
    # the membrane: fast flutter of amplitude + hard asymmetric clip = that paper buzz
    flut = 1 + 0.25 * butter(rng.normal(0, 1, n), 2500) * buzz
    src = np.tanh(src * 2.2 * flut + 0.3) - np.tanh(0.3)
    x = bp(src, 520, 0.6) * 0.8 + bp(src, 1350, 0.75) * 1.0 + bp(src, 2650, 0.7) * 0.6 + bp(src, 4200, 0.6) * 0.25
    env = _smooth(gate, 1 - np.exp(-1 / (0.02 * SR)), 1 - np.exp(-1 / (0.05 * SR)))
    return soft(x * 1.5, 1.0) * env * np.maximum(vel, 0)


def squeak(note=88, length=0.22, seed=13):
    """squeezed toy: a breathy whistle that whoops up then drops"""
    n = ns(length); t = tt(n); u = t / length
    p = note - 2.0 * np.exp(-t / 0.012) - 2.0 * np.maximum(u - 0.85, 0) / 0.15
    f = midi_hz(p)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    x += 0.35 * bp(noise(n, seed), f, 0.9)
    return x * np.sin(np.pi * u) ** 0.7


def duck(note=79, length=0.2, seed=17, squeeze=1.0):
    """rubber duck: a reedy honk, pitch rises while squeezed, falls as air rushes back. pitched so ducks can play riffs"""
    n = ns(length); t = tt(n); u = t / length
    p = note - 1.2 * np.exp(-t / 0.012) - 2.5 * np.maximum(u - 0.82, 0) / 0.18 * squeeze
    rng = np.random.default_rng(seed)
    f = midi_hz(p + butter(rng.normal(0, 1, n), 40) * 0.03)
    src = pulse(f, 0.18) + 0.4 * saw(f)
    x = bp(src, 1200, 0.7) * 1.1 + bp(src, 2400, 0.8) * 0.9 + bp(src, 3700, 0.7) * 0.5
    x += 0.25 * bp(noise(n, seed), 3000, 0.4) * (1 - u)  # air
    env = np.minimum(1, t / 0.008) * np.clip((length - t) / 0.04, 0, 1) * (0.8 + 0.2 * np.sin(np.pi * u))
    return soft(x * 1.3, 1) * env


def quack(note=60, length=0.24, seed=19):
    """a duck's actual quack (nasal 'waak'): for the breakdown choir"""
    n = ns(length); t = tt(n); u = t / length
    f = midi_hz(note + 0.6 * (np.sin(np.pi * u) - 0.80) - 1.5 * np.maximum(u - 0.75, 0) / 0.25)  # the bump averages out ON the note
    src = saw(f) + 0.6 * pulse(f, 0.1)
    f1 = 500 + 400 * np.sin(np.pi * np.minimum(u * 1.6, 1)); f2 = 1300 + 600 * np.sin(np.pi * u)
    fr = np.stack([f1, f2, np.full(n, 2600.0), np.full(n, 3500.0)], 1)
    bw = np.stack([np.full(n, 220.0), np.full(n, 260.0), np.full(n, 320.0), np.full(n, 400.0)], 1)  # wide, so they don't ring at their own pitch
    g = np.stack([np.full(n, 1.0), np.full(n, 0.8), np.full(n, 0.5), np.full(n, 0.3)], 1)
    x = resonators(np.ascontiguousarray(src), np.ascontiguousarray(fr), np.ascontiguousarray(bw), np.ascontiguousarray(g))
    return soft(norm(x) * 1.6, 1) * np.minimum(1, t / 0.01) * np.clip((length - t) / 0.06, 0, 1)


def ching(length=1.4, f=2350.0, seed=23):
    """cash register: drawer clunk + bell 'ching' (inharmonic partials, slight beating)"""
    n = ns(length); t = tt(n)
    x = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 0.5), (2.76, 0.6, 0.3), (5.40, 0.35, 0.18), (8.93, 0.2, 0.1), (1.003, 0.7, 0.55)):
        x += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    clunk = lp(noise(n, seed), 900) * np.exp(-t / 0.02) * 1.5 + np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.03)
    bell = np.concatenate([np.zeros(ns(0.07)), x])[:n]
    return soft(clunk * 0.8 + bell * 0.6, 1.2) * fade(np.ones(n), 0, 0.05)


def bell(note=88, length=1.2):
    """just the register's bell, pitched: for chime melodies"""
    n = ns(length); t = tt(n); f = float(midi_hz(note)); x = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 0.45), (2.76, 0.5, 0.25), (5.40, 0.25, 0.12), (1.004, 0.6, 0.5), (0.5, 0.25, 0.3)):
        x += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
    return x * np.minimum(1, t / 0.001) * 0.5


def kaching(length=1.5, f=2350.0):
    """'ka' (two quick drawer ratchets) + 'ching' (f = the bell's pitch: tune it to the song)"""
    n = ns(length); out = np.zeros(n)
    for d in (0.0, 0.05):
        c = hp(noise(ns(0.03)), 2000) * np.exp(-tt(ns(0.03)) / 0.006)
        out[ns(d):ns(d) + len(c)] += c * 0.8
    c = ching(length - 0.08, f)
    out[ns(0.08):ns(0.08) + len(c)] += c
    return out


def clink(f=3100.0, length=0.35, seed=29):
    """spoon on spoon: metallic, bright, quick"""
    n = ns(length); t = tt(n); x = np.zeros(n)
    rng = np.random.default_rng(seed)
    for r, d in ((1.0, 0.12), (2.32, 0.08), (3.86, 0.05), (5.13, 0.04), (6.9, 0.03)):
        x += np.sin(2 * np.pi * f * r * (1 + 0.003 * rng.random()) * t + rng.random() * 6) * np.exp(-t / d) / r ** 0.4
    x += hp(noise(n, seed), 5000) * np.exp(-t / 0.003) * 0.8
    return x * 0.6


def gavel(length=0.5, tone=520.0, seed=31):
    """wooden gavel knock: resonant wood body + a click, with a bit of courtroom"""
    n = ns(length); t = tt(n)
    x = np.zeros(n)
    for r, a, d in ((1.0, 1.0, 0.05), (1.58, 0.6, 0.035), (2.43, 0.4, 0.02), (0.5, 0.5, 0.06)):
        x += a * np.sin(2 * np.pi * tone * r * t) * np.exp(-t / d)
    x += bp(noise(n, seed), 2500, 0.3) * np.exp(-t / 0.004) * 1.5
    return soft(x * 1.2, 1)


def slidewhistle(t0, dur, n, lo=72, hi=96, up=True, out=None, wob=0.0):
    """slide whistle glide (up or down), breathy"""
    out = np.zeros(n) if out is None else out
    a0 = ns(t0); L = min(n - a0, ns(dur))
    if L <= 0: return out
    u = np.linspace(0, 1, L); s = u if up else 1 - u
    p = lo + (hi - lo) * (s ** 0.8) + wob * np.sin(2 * np.pi * 7 * u * dur)
    f = midi_hz(p)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.08 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    x += 0.3 * bp(noise(L), f, 0.85)
    out[a0:a0 + L] += x * np.minimum(1, u / 0.05) * np.minimum(1, (1 - u) / 0.1)
    return out


def can_open(length=1.2, seed=37):
    """psshht + fizz: a soda can opening (Jank Cola)"""
    n = ns(length); t = tt(n)
    crack = bp(noise(n, seed), 3000, 0.5) * np.exp(-t / 0.004) * 2
    hiss = hp(noise(n, seed + 1), 3500) * np.exp(-t / 0.18) * (t > 0.01)
    rng = np.random.default_rng(seed)
    fizz = np.zeros(n)
    for _ in range(140):  # little bubble pops
        a = rng.uniform(0.05, length - 0.05); f = rng.uniform(2500, 7000); L = ns(0.006)
        i = ns(a)
        fizz[i:i + L] += np.sin(2 * np.pi * f * tt(L) * (1 + tt(L) * 40)) * np.exp(-tt(L) / 0.0015) * rng.uniform(0.2, 0.6) * np.exp(-a / 0.6)
    return crack + hiss * 0.8 + fizz


def marbles(length=1.0, density=40, seed=41):
    """marbles rolling + clacking: random glassy ticks"""
    n = ns(length); x = np.zeros(n); rng = np.random.default_rng(seed)
    for _ in range(int(density * length)):
        i = ns(rng.uniform(0, length - 0.02)); f = rng.uniform(3500, 6500); L = ns(0.015)
        x[i:i + L] += np.sin(2 * np.pi * f * tt(L)) * np.exp(-tt(L) / 0.002) * rng.uniform(0.3, 1)
    return x


def chain_clank(length=0.3, seed=43):
    """heavy chain link clank (wrecking ball)"""
    n = ns(length); t = tt(n); x = np.zeros(n); rng = np.random.default_rng(seed)
    for k in range(3):
        d = k * 0.035 + rng.uniform(0, 0.01)
        for r, dd in ((1.0, 0.06), (2.7, 0.04), (4.1, 0.03), (6.3, 0.02)):
            f = 900 * r * rng.uniform(0.97, 1.03)
            x += np.where(t > d, np.sin(2 * np.pi * f * (t - d)) * np.exp(-(t - d) / dd), 0) * (0.8 ** k)
    return soft(x * 0.7, 1.2)


def bonk(note=50, length=0.25):
    """cartoon head bonk: hollow wooden tone with a falling pitch"""
    n = ns(length); t = tt(n)
    f = midi_hz(note + 12 * np.exp(-t / 0.01))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.07) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 2.3) / SR) * np.exp(-t / 0.03)
    return soft(x * 1.3, 1)


def scratch(length=0.4, seed=47):
    """record scratch: a noisy tone wobbling back and forth"""
    n = ns(length); t = tt(n)
    sp = np.sin(2 * np.pi * (3 / length) * t)
    f = 300 + 900 * np.abs(sp)
    src = saw(f) * 0.5 + bp(noise(n, seed), f * 3, 0.5)
    return lp(src, 2500 + 2000 * np.abs(sp), 0.3) * np.sin(np.pi * t / length) * (0.4 + 0.6 * np.abs(sp))


def whistle(notes, n, seed=53):
    """a person whistling (western standoff): pure tone, breathy, wide slow vibrato, little scoops"""
    pitch, gate, vel = _contour(notes, n, glide=0.06, dip=0.4, dip_t=0.04, vib=0.18, vib_hz=5.0, vib_delay=0.2)
    f = midi_hz(pitch)
    ph = np.cumsum(f) / SR
    x = np.sin(2 * np.pi * ph) + 0.04 * np.sin(4 * np.pi * ph)
    x += 0.12 * bp(noise(n, seed), f, 0.9)
    env = _smooth(gate, 1 - np.exp(-1 / (0.03 * SR)), 1 - np.exp(-1 / (0.06 * SR)))
    return x * env * np.maximum(vel, 0)


def wind(length, seed=59):
    n = ns(length); t = tt(n)
    fc = 500 + 400 * np.sin(2 * np.pi * 0.23 * t) + 250 * np.sin(2 * np.pi * 0.61 * t + 1)
    return bp(noise(n, seed), fc, 0.7) * np.minimum(1, t / 1.0) * np.minimum(1, (length - t) / 1.0)


def peel(length=0.35, seed=61):
    """banana peel: a wet rip, a falling squelchy band of noise"""
    n = ns(length); t = tt(n); u = t / length
    fc = 3500 * (1 - u) ** 1.5 + 300
    rng = np.random.default_rng(seed)
    grit = (rng.random(n) < 0.08) * rng.uniform(-1, 1, n)  # little crackles of the skin tearing
    x = bp(noise(n, seed) * 0.6 + grit * 2.0, fc, 0.8)
    return soft(x * 2.0, 1) * np.sin(np.pi * np.minimum(u * 1.2, 1)) ** 0.5


def whoosh(length=1.2, pan_from=-1.0, pan_to=1.0, seed=67):
    """a wrecking ball swinging past: a swell of low-ish noise that pans across. returns stereo (n,2)"""
    n = ns(length); u = np.linspace(0, 1, n)
    sw = np.sin(np.pi * u) ** 2
    x = bp(noise(n, seed), 250 + 900 * sw, 0.5) * sw + 0.3 * lp(noise(n, seed + 1), 300) * sw
    p = pan_from + (pan_to - pan_from) * (0.5 - 0.5 * np.cos(np.pi * u))
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1) * np.sqrt(2)
