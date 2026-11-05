# tuning check (we can't listen): renders a track's stems (no mastering) and reports, per melodic stem,
#  - out_of_key: share of its pitched energy on notes outside the song's scale (KEY in the track module)
#  - cents: how far its strongest pitch sits from the nearest semitone (A440), median of |deviation|
# and the bars where the melodic parts together are most out of key.  usage: tune_check.py slug [slug...]
import sys, os, importlib, json
import numpy as np
from scipy.signal import stft
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from jf.dsp import SR

NOT_TONAL = {'kick', 'hats', 'clap', 'perc', 'fx', 'rumble', 'wind', 'snare', 'whoosh', 'chain', 'peel', 'jury', 'clock'}


def pitch_stats(x, scale):
    f, t, Z = stft(x, SR, nperseg=8192, noverlap=6144)
    P = np.abs(Z) ** 2
    band = (f > 70) & (f < 4200)
    fb = f[band]; Pb = P[band]
    pc = (np.round(12 * np.log2(fb / 440.0)) + 9) % 12
    tot = Pb.sum(1)
    w = np.array([tot[pc == k].sum() for k in range(12)])
    out = w[[k for k in range(12) if k not in scale]].sum() / (w.sum() + 1e-12)
    # strongest peak per loud frame -> cents off the grid (parabolic interpolation)
    devs, wts = [], []
    fr_e = Pb.sum(0)
    loud = fr_e > fr_e.max() * 1e-3
    lf = (f > 70) & (f < 1500)
    Pl = P[lf]; fl = f[lf]
    for j in np.flatnonzero(loud):
        col = Pl[:, j]; i = int(np.argmax(col))
        if 0 < i < len(col) - 1:
            a, b, c = np.log(col[i - 1] + 1e-20), np.log(col[i] + 1e-20), np.log(col[i + 1] + 1e-20)
            d = 0.5 * (a - c) / (a - 2 * b + c + 1e-20)
            fr = fl[i] + d * (fl[1] - fl[0])
            cents = 1200 * np.log2(fr / 440.0)
            devs.append((cents + 50) % 100 - 50); wts.append(col[i])
    devs = np.abs(np.array(devs)) if devs else np.array([0.0])
    return dict(out_of_key=round(float(out), 3), cents=round(float(np.median(devs)), 1), cents_p90=round(float(np.percentile(devs, 90)), 1)), w / (w.sum() + 1e-12)


def check(slug):
    mod = importlib.import_module('tracks.' + slug)
    scale = set(mod.KEY)
    s = mod.build()
    stems = s.render_stems()
    rep = {}
    tonal = []
    for k, y in stems.items():
        if k in NOT_TONAL: continue
        r, _ = pitch_stats(y.mean(1), scale); rep[k] = r; tonal.append(y.mean(1))
    mix = sum(tonal)
    # worst bars
    bars = []
    for bar in range(s.beats // s.bpb):
        a, b = int(s.t(bar * 4) * SR), int(s.t(bar * 4 + 4) * SR)
        seg = mix[a:b]
        if np.sqrt(np.mean(seg ** 2)) < 1e-3: continue
        r, _ = pitch_stats(seg, scale)
        bars.append((r['out_of_key'], bar))
    bars.sort(reverse=True)
    return dict(track=slug, stems=rep, worst_bars=[(b, round(o, 2)) for o, b in bars[:6]], median_bar=round(float(np.median([o for o, _ in bars])), 3))


if __name__ == '__main__':
    for slug in sys.argv[1:]:
        print(json.dumps(check(slug)), flush=True)
