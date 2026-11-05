# a song = a tempo map + buses. you place sounds at beats; render() runs each bus's effects, sidechains them to the
# kick, sums, masters to a loudness target and wraps every tail past the end back onto the start, so the file loops
# with no gap and no click (the end of the song flows into its own beginning).
import os, subprocess, tempfile, hashlib
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy.signal import resample_poly
from pedalboard import Pedalboard, Compressor, Limiter, HighpassFilter, LowShelfFilter, HighShelfFilter, PeakFilter
from .dsp import SR, ns, pan2, butter
from numba import njit
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import butter as _butter, sosfiltfilt
_LP = _butter(6, 17000, 'low', fs=44100, output='sos')


@njit(cache=True)
def _release(g, coef):
    out = np.empty_like(g); y = 1.0
    for i in range(g.shape[0]):
        y = y + (1.0 - y) * coef
        if g[i] < y: y = g[i]
        out[i] = y
    return out


def tp_limit(y, ceil, look=0.0015, release=0.06):
    """true-peak limiter: required gain from the 4x-oversampled peaks, min over a lookahead window, instant attack /
    smooth release, then a short box smooth (the window is 2x the box so the target is still met at the peak)"""
    up = np.abs(resample_poly(y, 4, 1, axis=0)).max(1)
    pk = np.maximum(up[:len(y) * 4].reshape(-1, 4).max(1), np.abs(y).max(1))[:len(y)]
    req = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    L = max(2, int(look * SR))
    g = minimum_filter1d(req, 2 * L + 1)
    g = _release(g, 1 - np.exp(-1 / (release * SR)))
    g = uniform_filter1d(g, L)
    g = np.minimum(g, minimum_filter1d(req, 3))
    return y * g[:, None]


def resample_rate(x, rate):
    pos = np.cumsum(rate) - rate[0]
    return np.interp(pos, np.arange(len(x)), x)

TAIL = 6.0  # seconds of overhang rendered past the loop point (reverb/delay tails), wrapped onto the start


class Song:
    def __init__(self, title, bpm, bars, tempo=None, bpb=4):
        """tempo = optional list of (beat, bpm, 'step'|'ramp') changes for tempo jokes; bpm is the starting tempo"""
        self.title, self.bpb = title, bpb
        self.beats = bars * bpb
        grid = np.arange(0, self.beats + 64 * bpb + 1e-9, 1 / 96)
        bpmv = np.full(len(grid), float(bpm))
        if tempo:
            pts = sorted(tempo)
            cur = float(bpm); cb = 0.0
            for b, v, kind in pts:
                i0 = np.searchsorted(grid, cb); i1 = np.searchsorted(grid, b)
                if kind == 'ramp':
                    bpmv[i0:i1] = np.linspace(cur, v, i1 - i0) if i1 > i0 else bpmv[i0:i1]
                else:
                    bpmv[i0:i1] = cur
                bpmv[i1:] = v; cur = float(v); cb = b
        dt = 60.0 / bpmv / 96
        self._grid = grid
        self._sec = np.concatenate([[0], np.cumsum(dt[:-1])])
        self.L = float(self.t(self.beats))  # loop length (s)
        self.n = ns(self.L)
        self.N = self.n + ns(TAIL)
        self.buses = {}
        self.kicks = []  # beat positions, for the sidechain
        self.regions = []  # mix-level jokes: tape stops, beat repeats
        self.eq = [LowShelfFilter(55, -1.0, 0.7), PeakFilter(320, -1.5, 0.8), HighShelfFilter(7000, 1.5, 0.7)]  # master tone, per song

    def t(self, beat):
        return np.interp(beat, self._grid, self._sec)

    def bar(self, b, beat=0.0):
        return b * self.bpb + beat

    def bus(self, name, gain=1.0, fx=None, duck=0.0, duck_rel=0.12, width=0.0, hp=0.0, auto=None, res=0.1):
        """duck = how far (0..1) the kick pushes this bus down; width = stereo widening (haas, 0..1);
        auto = lowpass automation [(beat, hz), ...] (log-interpolated), applied after the bus fx"""
        self.buses[name] = dict(buf=np.zeros((self.N, 2)), gain=gain, fx=fx, duck=duck, rel=duck_rel, width=width, hp=hp, auto=auto, res=res)
        return name

    def place(self, name, beat, x, gain=1.0, pan=0.0):
        if beat >= self.beats + 32: return
        b = self.buses[name]['buf']
        a = ns(self.t(beat))
        if a >= self.N: return
        y = pan2(x, pan) if x.ndim == 1 else x
        L = min(len(y), self.N - a)
        b[a:a + L] += y[:L] * gain

    def add(self, name, x, gain=1.0, pan=0.0):
        """a whole-length line (from a line instrument rendered with n = self.N)"""
        y = pan2(x, pan) if x.ndim == 1 else x
        L = min(len(y), self.N)
        self.buses[name]['buf'][:L] += y[:L] * gain

    def notes(self, items):
        """[(beat, beats_long, midi, *extra)] -> [(sec, sec_long, midi, *extra)] through the tempo map"""
        out = []
        for it in items:
            b, d = it[0], it[1]
            t0 = float(self.t(b)); out.append((t0, float(self.t(b + d)) - t0, *it[2:]))
        return out

    def kick(self, beat):
        self.kicks.append(beat)

    def tapestop(self, beat, beats, curve=1.6):
        """the whole mix slows to a halt (pitch drops with it) over `beats`, starting at `beat`"""
        self.regions.append(('stop', beat, beats, curve))

    def repeat(self, beat, beats, slice_beats):
        """beat-repeat: the first `slice_beats` of the region stutter for the whole region"""
        self.regions.append(('rep', beat, beats, slice_beats))

    def _regions(self, mix):
        for kind, b, d, arg in self.regions:
            a = ns(self.t(b)); e = ns(self.t(b + d)); L = e - a
            if kind == 'stop':
                u = np.linspace(0, 1, L)
                rate = (1 - u) ** arg
                src = mix[a:a + 2 * L].copy()
                y = np.stack([resample_rate(src[:, 0], rate), resample_rate(src[:, 1], rate)], 1)
                y = y[:L]; y = np.pad(y, ((0, L - len(y)), (0, 0)))
                y *= np.clip((1 - u) / 0.15, 0, 1)[:, None]
                mix[a:e] = y
            else:
                sl = ns(self.t(b + arg)) - a
                piece = mix[a:a + sl].copy()
                env = np.ones(sl); f = min(ns(0.004), sl // 4)
                env[:f] = np.linspace(0, 1, f); env[-f:] = np.linspace(1, 0, f)
                for k in range(a, e, sl):
                    m = min(sl, e - k); mix[k:k + m] = piece[:m] * env[:m, None]
        return mix

    # ------------------------------------------------------------------ render
    def _duck_curve(self, depth, rel):
        g = np.ones(self.n)
        if depth <= 0: return g
        for kb in self.kicks:
            a = ns(self.t(kb)) % self.n
            L = ns(rel * 5)
            tl = np.arange(L) / SR
            c = 1 - depth * np.exp(-tl / rel) * np.minimum(1, tl / 0.002 + 0.3)
            idx = (a + np.arange(L)) % self.n
            g[idx] = np.minimum(g[idx], c)
        return g

    def _wrap(self, y):
        out = y[:self.n].copy()
        rest = y[self.n:]
        while len(rest):
            L = min(len(rest), self.n); out[:L] += rest[:L]; rest = rest[L:]
        return out

    def render_stems(self):
        stems = {}
        for name, b in self.buses.items():
            y = b['buf']
            if not np.any(y): continue
            if b['hp']: y = np.stack([butter(y[:, 0], b['hp'], 'high'), butter(y[:, 1], b['hp'], 'high')], 1)
            if b['fx'] is not None:
                y = b['fx'](y.T.astype(np.float32), SR).T.astype(float)
                if len(y) < self.N: y = np.pad(y, ((0, self.N - len(y)), (0, 0)))
            if b['auto']:
                from .dsp import lp
                pts = sorted(b['auto'])
                ts = [float(self.t(pb)) for pb, _ in pts]; hz = [np.log(h) for _, h in pts]
                cut = np.exp(np.interp(np.arange(len(y)) / SR, ts, hz))
                y = np.stack([lp(y[:, 0], cut, b['res']), lp(y[:, 1], cut, b['res'])], 1)
            if b['width']:
                d = ns(0.012 * b['width'])
                side = (y[:, 0] - y[:, 1]) * 0.5; mid = (y[:, 0] + y[:, 1]) * 0.5
                dl = np.concatenate([np.zeros(d), mid[:-d]]) if d else mid
                y = np.stack([mid + side + (mid - dl) * 0.35 * b['width'], mid - side - (mid - dl) * 0.35 * b['width']], 1)
            y = np.stack([self._wrap(y[:, 0]), self._wrap(y[:, 1])], 1)
            y *= self._duck_curve(b['duck'], b['rel'])[:, None] * b['gain']
            stems[name] = y
        return stems

    def master(self, mix, target=-8.0, ceiling=-1.5):
        """glue comp -> eq -> gain to target -> oversampled soft clip -> limiter. run over two copies of the loop
        so the compressor/limiter state at the start equals the state at the end (seamless loop)."""
        meter = pyln.Meter(SR)
        pre = Pedalboard([HighpassFilter(24), Compressor(-14, 2.5, 8, 120)] + list(self.eq))
        x2 = np.concatenate([mix, mix])
        y = pre(x2.T.astype(np.float32), SR).T.astype(float)
        one = y[self.n:]
        gain = 10 ** ((target - meter.integrated_loudness(one)) / 20)
        for _ in range(3):  # limiting eats loudness, so aim a bit hotter each pass
            loud = meter.integrated_loudness(self._finish(one * gain, ceiling))
            if abs(loud - target) < 0.15: break
            gain *= 10 ** ((target - loud) / 20)
        z = self._finish(y * gain, ceiling)
        return z[self.n:2 * self.n]

    @staticmethod
    def _finish(y, ceiling):
        """oversampled soft clip into a true-peak lookahead limiter (gain from the 4x signal, so no intersample overs)"""
        c = 10 ** (ceiling / 20)
        up = resample_poly(y, 4, 1, axis=0)
        k = c * 1.02; kn = 0.75
        a = np.abs(up)
        up = np.where(a < k * kn, up, np.sign(up) * (k * kn + k * (1 - kn) * np.tanh((a - k * kn) / (k * (1 - kn)))))
        y = resample_poly(up, 1, 4, axis=0)
        # band-limit before the limiter: the codec throws the top away anyway, and doing it here means the limiter sees
        # the peaks that will really be in the file (vorbis q5 otherwise overshoots a crushed master by 3+ dB)
        y = sosfiltfilt(_LP, y, axis=0)
        return tp_limit(y, c)

    # default mix: each bus's loudness while it plays, in LU relative to the kick (K-weighted, so the kick's sub
    # counts for less than it sounds: these numbers lean everything a bit under it). a song overrides with self.levels
    LEVELS = dict(kick=0, vox=-4.5, lead=-4.5, hoover=-4.0, acid=-4.0, kazoo=-4.0, duck=-4.5, stab=-5.5, orch=-8, bells=-6,
                  clap=-8, snare=-8, hats=-13, perc=-10, fx=-7, siren=-10, pad=-12, bass=-6, rumble=-9, piano=-6, toys=-6)

    def render(self):
        stems = self.render_stems()
        lv = dict(self.LEVELS); lv.update(getattr(self, 'levels', {}))
        from .analyze_levels import active_lufs
        have = {k: active_lufs(y) for k, y in stems.items()}
        ref = have.get('kick')
        self.gains = {}
        if ref is not None:
            for k, y in stems.items():
                if k in lv and have[k] is not None and k != 'kick':
                    g = 10 ** ((ref + lv[k] - have[k]) / 20); y *= g; self.gains[k] = round(20 * np.log10(g), 1)
        return self._regions(sum(stems.values())), stems


# ------------------------------------------------------------------ soundfont (FluidSynth, FluidR3_GM, MIT licence)
SF2 = '/usr/share/sounds/sf2/FluidR3_GM.sf2'
CACHE = os.path.join(os.path.dirname(__file__), '..', '.cache')


def gm(program, notes, n, ch=0, gain=1.0, sf2=SF2):
    """render notes [(sec, sec_long, midi|list, vel 0..1)] on a General MIDI program with FluidSynth -> stereo (n,2)"""
    import mido
    key = hashlib.md5(repr((program, notes, n, ch, sf2)).encode()).hexdigest()[:16]
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f'gm_{key}.wav')
    if not os.path.exists(path):
        mid = mido.MidiFile(ticks_per_beat=480)
        tr = mido.MidiTrack(); mid.tracks.append(tr)
        tr.append(mido.MetaMessage('set_tempo', tempo=500000))
        chn = 9 if program < 0 else ch
        if program >= 0: tr.append(mido.Message('program_change', program=program, channel=chn))
        ev = []
        for t0, d, ms, *rest in notes:
            v = int(np.clip((rest[0] if rest else 0.9) * 127, 1, 127))
            for m in (ms if isinstance(ms, (list, tuple)) else [ms]):
                ev.append((t0, 1, m, v)); ev.append((t0 + d, 0, m, 0))
        ev.sort(key=lambda e: (e[0], e[1]))
        last = 0
        for t0, on, m, v in ev:
            tick = int(round(t0 * 960))
            tr.append(mido.Message('note_on' if on else 'note_off', note=int(m), velocity=v if on else 0, channel=chn, time=max(0, tick - last)))
            last = max(last, tick)
        with tempfile.TemporaryDirectory() as td:
            mp = os.path.join(td, 's.mid'); mid.save(mp)
            subprocess.run(['fluidsynth', '-ni', '-q', '-g', '0.6', '-R', '0', '-C', '0', '-F', path, '-r', str(SR), sf2, mp], check=True)
    y, sr = sf.read(path)
    assert sr == SR
    if y.ndim == 1: y = np.stack([y, y], 1)
    out = np.zeros((n, 2)); L = min(n, len(y)); out[:L] = y[:L]
    return out * gain
