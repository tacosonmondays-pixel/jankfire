# measure a rendered track (we can't listen, so we look): loudness, true peak, band balance, the loop seam,
# kick vs bass overlap, and a spectrogram picture.  usage: analyze.py file.ogg [more.ogg...]  (or import measure())
import sys, os, json, subprocess, re
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy.signal import resample_poly, stft

BANDS = [(20, 60, 'sub'), (60, 250, 'low'), (250, 500, 'mud'), (500, 2000, 'mid'), (2000, 6000, 'pres'), (6000, 12000, 'air'), (12000, 20000, 'fizz')]


def ffmpeg_loud(path):
    r = subprocess.run(['ffmpeg', '-nostats', '-hide_banner', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
    s = r.stderr[r.stderr.rfind('Summary:'):]
    gi = re.search(r'I:\s+(-?[\d.]+) LUFS', s); tp = re.search(r'Peak:\s+(-?[\d.]+) dBFS', s); lra = re.search(r'LRA:\s+([\d.]+) LU', s)
    return float(gi.group(1)), float(tp.group(1)), float(lra.group(1))


def seam(y, sr):
    """click check at the loop point: high-passed energy in a 6 ms window across end->start vs the same measure
    everywhere else (median and 99th pct). ratio near 1 = invisible seam."""
    mono = y.mean(1)
    from scipy.signal import butter, sosfiltfilt
    sos = butter(4, 3000, 'high', fs=sr, output='sos')
    w = int(0.006 * sr)
    joined = np.concatenate([mono[-sr:], mono[:sr]])
    hj = sosfiltfilt(sos, joined)
    at = np.sqrt(np.mean(hj[sr - w // 2:sr + w // 2] ** 2))
    h = sosfiltfilt(sos, mono)
    frames = np.sqrt(np.mean(h[:len(h) // w * w].reshape(-1, w) ** 2, axis=1))
    jump = abs(mono[0] - mono[-1]); typ = np.percentile(np.abs(np.diff(mono)), 99.9)
    return dict(seam_hf_vs_median=round(at / (np.median(frames) + 1e-12), 2), seam_hf_vs_p99=round(at / (np.percentile(frames, 99) + 1e-12), 2),
                seam_sample_jump_vs_p999_step=round(jump / (typ + 1e-12), 2))


def bands(y, sr):
    f, _, Z = stft(y.mean(1), sr, nperseg=8192)
    P = (np.abs(Z) ** 2).mean(1)
    tot = P[(f >= 20)].sum()
    return {name: round(10 * np.log10(P[(f >= a) & (f < b)].sum() / tot + 1e-12), 1) for a, b, name in BANDS}


def kick_vs_bass(stems, kicks_sec, sr, kick_bus='kick', bass_buses=('bass', 'acid', 'rumble', 'hoover', 'kazoo', 'lead')):
    """low band (<150 Hz) energy of the bass-ish buses inside the first 60 ms of each kick, relative to the kick's own
    low band there, and relative to the bass buses' own level between kicks. both negative = they take turns."""
    from scipy.signal import butter, sosfilt
    sos = butter(4, 150, 'low', fs=sr, output='sos')
    k = sosfilt(sos, stems[kick_bus].mean(1)) if kick_bus in stems else None
    b = sum(sosfilt(sos, stems[n].mean(1)) for n in bass_buses if n in stems)
    if k is None or np.isscalar(b): return {}
    m = np.zeros(len(k), bool)
    for t in kicks_sec:
        a = int(t * sr); m[a:a + int(0.06 * sr)] = True
    ek = np.mean(k[m] ** 2); eb_in = np.mean(b[m] ** 2); eb_out = np.mean(b[~m] ** 2) + 1e-12
    return dict(bass_under_kick_db=round(10 * np.log10(eb_in / ek + 1e-12), 1), bass_ducked_db=round(10 * np.log10(eb_in / eb_out + 1e-12), 1))


def stem_levels(stems, sr):
    """each stem's loudness (LUFS-ish, K-weighted) while it's actually playing, relative to the kick"""
    from jf.analyze_levels import active_lufs
    out = {k: v for k, v in ((k, active_lufs(y, sr)) for k, y in stems.items()) if v is not None}
    ref = out.get('kick', 0)
    return {k: round(v - ref, 1) for k, v in sorted(out.items(), key=lambda kv: -kv[1])}


def picture(y, sr, png, title):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    mono = y.mean(1)
    f, t, Z = stft(mono, sr, nperseg=4096, noverlap=3072)
    S = 20 * np.log10(np.abs(Z) + 1e-9)
    fig, ax = plt.subplots(2, 1, figsize=(14, 7), gridspec_kw=dict(height_ratios=[3, 1]))
    ax[0].pcolormesh(t, f, S, vmin=S.max() - 90, vmax=S.max(), cmap='magma', shading='auto')
    ax[0].set_yscale('symlog', linthresh=200); ax[0].set_ylim(20, 20000); ax[0].set_ylabel('Hz'); ax[0].set_title(title)
    for h in (60, 250, 500, 6000, 12000): ax[0].axhline(h, color='c', lw=0.4, alpha=0.6)
    meter = pyln.Meter(sr, block_size=0.4)
    hop = int(sr * 1.0); st = []
    for i in range(0, len(y) - 3 * sr, hop):
        st.append(meter.integrated_loudness(y[i:i + 3 * sr]))
    ax[1].plot(np.arange(len(st)), st, color='m'); ax[1].set_ylim(-30, -3); ax[1].set_ylabel('LUFS (3 s)'); ax[1].set_xlabel('s')
    ax[1].axhspan(-9, -7, color='y', alpha=0.2); ax[1].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(png, dpi=80); plt.close(fig)


def measure(path, stems=None, kicks_sec=None, png=None, title=''):
    y, sr = sf.read(path, always_2d=True)
    i_lufs, tp, lra = ffmpeg_loud(path)
    up = resample_poly(y, 4, 1, axis=0)
    r = dict(file=os.path.basename(path), dur=round(len(y) / sr, 1), lufs=i_lufs, true_peak_dbtp=tp,
             tp_numpy=round(20 * np.log10(np.abs(up).max()), 2), lra=lra, size_mb=round(os.path.getsize(path) / 1e6, 2))
    r.update(seam(y, sr)); r['bands_db'] = bands(y, sr)
    if stems is not None and kicks_sec is not None: r.update(kick_vs_bass(stems, kicks_sec, sr))
    if stems is not None: r['stems_vs_kick'] = stem_levels(stems, sr)
    if png: picture(y, sr, png, title or r['file'])
    return r


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(measure(p, png=os.path.splitext(p)[0] + '.png')))
