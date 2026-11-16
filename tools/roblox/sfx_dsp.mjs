// the small DSP kit behind render_sfx.mjs: buffers, seeded noise, RBJ biquads (fixed or swept), oscillators with
// band-limited edges, struck resonator banks, FM bells, saturation, a mono Freeverb, echo taps, a look-ahead limiter,
// a BS.1770-style loudness meter, and WAV in/out. plain Node, no dependencies.
import fs from 'node:fs';

export const SR = 44100;
const { PI, sin, cos, exp, tanh, abs, max, min, floor, round, log10, sqrt } = Math;

export const N = (s) => Math.max(1, round(s * SR));
export const zeros = (s) => new Float64Array(N(s));
export const db = (x) => Math.pow(10, x / 20);

// seeded random (mulberry32 on an FNV hash of the name), so every sound renders the same each time
export function rngFor(name) {
  let h = 2166136261;
  for (let i = 0; i < name.length; i++) { h ^= name.charCodeAt(i); h = Math.imul(h, 16777619); }
  let a = h >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function mix(dst, src, gain = 1, at = 0) {
  const o = round(at * SR);
  for (let i = 0; i < src.length; i++) { const j = o + i; if (j >= 0 && j < dst.length) dst[j] += src[i] * gain; }
  return dst;
}
export function gain(b, g) { for (let i = 0; i < b.length; i++) b[i] *= g; return b; }
export function peak(b) { let p = 0; for (let i = 0; i < b.length; i++) p = max(p, abs(b[i])); return p; }
export function norm(b, to = 1) { const p = peak(b); return p > 0 ? gain(b, to / p) : b; }
export function env(b, f, from = 0) { const o = round(from * SR); for (let i = 0; i < b.length; i++) b[i] *= f((i - o) / SR); return b; }

// envelopes: t in seconds; a = linear attack, d = exponential decay time constant (about -60 dB after 6.9 d)
export const ad = (a, d) => (t) => (t < 0 ? 0 : t < a ? t / a : exp(-(t - a) / d));
export const ahd = (a, h, d) => (t) => (t < 0 ? 0 : t < a ? t / a : t < a + h ? 1 : exp(-(t - a - h) / d));
// a swell that rises like exp and cuts off at `at` (a reversed decay), then dies in `rel`
export const swell = (at, d, rel) => (t) => (t < 0 ? 0 : t < at ? exp(-(at - t) / d) : exp(-(t - at) / rel));
// slide from f0 toward f1 with time constant T (thumps, sweeps)
export const glide = (f0, f1, T) => (t) => f1 + (f0 - f1) * exp(-t / T);
export const expRamp = (f0, f1, T) => (t) => f0 * Math.pow(f1 / f0, min(1, max(0, t / T)));

export function white(s, R) { const n = N(s), b = new Float64Array(n); for (let i = 0; i < n; i++) b[i] = R() * 2 - 1; return b; }
export function pink(s, R) {
  const n = N(s), o = new Float64Array(n);
  let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
  for (let i = 0; i < n; i++) {
    const w = R() * 2 - 1;
    b0 = 0.99886 * b0 + w * 0.0555179; b1 = 0.99332 * b1 + w * 0.0750759; b2 = 0.969 * b2 + w * 0.153852;
    b3 = 0.8665 * b3 + w * 0.3104856; b4 = 0.55 * b4 + w * 0.5329522; b5 = -0.7616 * b5 - w * 0.016898;
    o[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362) * 0.11; b6 = w * 0.115926;
  }
  return o;
}
export function brown(s, R) { const n = N(s), o = new Float64Array(n); let l = 0; for (let i = 0; i < n; i++) { l = (l + 0.02 * (R() * 2 - 1)) / 1.02; o[i] = l * 3.5; } return o; }

// RBJ cookbook biquads. type: lp hp bp (0 dB peak) peak ls hs
function coefs(type, f, q, g) {
  const w = 2 * PI * min(SR * 0.45, max(10, f)) / SR, cs = cos(w), sn = sin(w), al = sn / (2 * q), A = Math.pow(10, g / 40);
  let b0, b1, b2, a0, a1, a2;
  if (type === 'lp') { b0 = (1 - cs) / 2; b1 = 1 - cs; b2 = b0; a0 = 1 + al; a1 = -2 * cs; a2 = 1 - al; }
  else if (type === 'hp') { b0 = (1 + cs) / 2; b1 = -(1 + cs); b2 = b0; a0 = 1 + al; a1 = -2 * cs; a2 = 1 - al; }
  else if (type === 'bp') { b0 = al; b1 = 0; b2 = -al; a0 = 1 + al; a1 = -2 * cs; a2 = 1 - al; }
  else if (type === 'peak') { b0 = 1 + al * A; b1 = -2 * cs; b2 = 1 - al * A; a0 = 1 + al / A; a1 = -2 * cs; a2 = 1 - al / A; }
  else if (type === 'ls' || type === 'hs') {
    const s2 = 2 * sqrt(A) * al, sgn = type === 'ls' ? 1 : -1;
    b0 = A * ((A + 1) - sgn * (A - 1) * cs + s2); b1 = sgn * 2 * A * ((A - 1) - sgn * (A + 1) * cs); b2 = A * ((A + 1) - sgn * (A - 1) * cs - s2);
    a0 = (A + 1) + sgn * (A - 1) * cs + s2; a1 = -sgn * 2 * ((A - 1) + sgn * (A + 1) * cs); a2 = (A + 1) + sgn * (A - 1) * cs - s2;
  } else throw new Error('filter ' + type);
  return [b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0];
}
// f: Hz or (t) => Hz (re-tuned every 16 samples)
export function filt(b, type, f, q = 0.707, g = 0) {
  const dyn = typeof f === 'function';
  let c = coefs(type, dyn ? f(0) : f, q, g), x1 = 0, x2 = 0, y1 = 0, y2 = 0;
  for (let i = 0; i < b.length; i++) {
    if (dyn && (i & 15) === 0) c = coefs(type, f(i / SR), q, g);
    const x = b[i], y = c[0] * x + c[1] * x1 + c[2] * x2 - c[3] * y1 - c[4] * y2;
    x2 = x1; x1 = x; y2 = y1; y1 = y; b[i] = y;
  }
  return b;
}
export const lp = (b, f, q = 0.707) => filt(b, 'lp', f, q);
export const hp = (b, f, q = 0.707) => filt(b, 'hp', f, q);
export const bp = (b, f, q = 1) => filt(b, 'bp', f, q);
export const lp2 = (b, f, q = 0.707) => filt(filt(b, 'lp', f, q), 'lp', f, q);
export const hp2 = (b, f, q = 0.707) => filt(filt(b, 'hp', f, q), 'hp', f, q);

function blep(t, dt) {
  if (t < dt) { t /= dt; return t + t - t * t - 1; }
  if (t > 1 - dt) { t = (t - 1) / dt; return t * t + t + t + 1; }
  return 0;
}
// f: Hz or (t) => Hz. type: sine tri saw square pulse (w = duty)
export function osc(s, f, type = 'sine', ph0 = 0, w = 0.5) {
  const n = N(s), o = new Float64Array(n), dyn = typeof f === 'function';
  let ph = ph0;
  for (let i = 0; i < n; i++) {
    const hz = dyn ? f(i / SR) : f, dt = min(0.5, hz / SR);
    ph += dt; ph -= floor(ph);
    if (type === 'sine') o[i] = sin(2 * PI * ph);
    else if (type === 'tri') o[i] = 1 - 4 * abs(ph - 0.5);
    else if (type === 'saw') o[i] = 2 * ph - 1 - blep(ph, dt);
    else { const d = type === 'square' ? 0.5 : w; o[i] = (ph < d ? 1 : -1) + blep(ph, dt) - blep((ph + 1 - d) % 1, dt); }
  }
  return o;
}

// a struck thing: a short noise burst through a bank of ringing band-passes. modes: [Hz, Q, gain]
// (a band-pass rings for about Q / (pi f) seconds per e-fold)
export function strike(s, R, modes, sharp = 0.0006) {
  const x = zeros(s);
  const n = min(x.length, N(sharp * 8));
  for (let i = 0; i < n; i++) x[i] = (R() * 2 - 1) * exp(-i / (sharp * SR));
  const o = zeros(s);
  for (const [f, q, g] of modes) { const y = Float64Array.from(x); filt(y, 'bp', f, q); norm(y); mix(o, y, g); }
  return norm(o);
}
// pure decaying partials: [Hz, amp, decay s], with a tiny attack so it doesn't click unless asked (atk = 0)
export function partials(s, modes, R, atk = 0.0015) {
  const o = zeros(s);
  for (const [f, a, d] of modes) {
    const ph = R ? R() * 2 * PI : 0, k = 2 * PI * f / SR;
    for (let i = 0; i < o.length; i++) {
      const t = i / SR, e = a * (atk > 0 && t < atk ? t / atk : 1) * exp(-t / d);
      if (e < 1e-6 * a && t > atk) break;
      o[i] += e * sin(k * i + ph);
    }
  }
  return norm(o);
}
// FM bell / chime: carrier f, modulator f*ratio, index decaying so it starts bright and mellows
export function bell(s, f, { ratio = 3.01, index = 2, idxDecay = 0.08, decay = 0.4, atk = 0.002, detune = 0 } = {}) {
  const o = zeros(s);
  for (let i = 0; i < o.length; i++) {
    const t = i / SR, mi = index * exp(-t / idxDecay);
    const e = (t < atk ? t / atk : 1) * exp(-t / decay);
    o[i] = e * sin(2 * PI * f * (1 + detune) * t + mi * sin(2 * PI * f * ratio * t));
  }
  return o;
}

export function sat(b, drive = 2, asym = 0) {
  const k = 1 / tanh(drive), off = tanh(asym);
  for (let i = 0; i < b.length; i++) b[i] = (tanh(drive * b[i] + asym) - off) * k;
  return b;
}


// radix-2 FFT in place (re, im: power-of-two length); inverse = conjugate in and out, divide by n
export function fft(re, im) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) { let bit = n >> 1; for (; j & bit; bit >>= 1) j ^= bit; j ^= bit; if (i < j) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; } }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = -2 * PI / len, wr = cos(ang), wi = sin(ang), h = len >> 1;
    for (let i = 0; i < n; i += len) {
      let cr = 1, ci = 0;
      for (let k = 0; k < h; k++) {
        const p = i + k, q = p + h, br = re[q] * cr - im[q] * ci, bi = re[q] * ci + im[q] * cr;
        re[q] = re[p] - br; im[q] = im[p] - bi; re[p] += br; im[p] += bi;
        const t = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = t;
      }
    }
  }
}
export function convolve(x, h) {
  const n = x.length + h.length - 1; let M = 1; while (M < n) M <<= 1;
  const ar = new Float64Array(M), ai = new Float64Array(M), br = new Float64Array(M), bi = new Float64Array(M);
  ar.set(x); br.set(h); fft(ar, ai); fft(br, bi);
  for (let k = 0; k < M; k++) { const r = ar[k] * br[k] - ai[k] * bi[k], i = ar[k] * bi[k] + ai[k] * br[k]; ar[k] = r; ai[k] = -i; }
  fft(ar, ai);
  const o = new Float64Array(n); for (let k = 0; k < n; k++) o[k] = ar[k] / M; return o;
}
// a synthetic room: early reflections, then dense noise decaying by rt60 while its top end closes from hf0 to hf1
// (smooth, no comb flutter on hard transients the way Freeverb has)
const IRS = new Map();
export function roomIR({ rt60 = 0.8, hf0 = 9000, hf1 = 1200, pre = 0.012 } = {}) {
  const key = [rt60, hf0, hf1, pre].join('/');
  if (IRS.has(key)) return IRS.get(key);
  const R = rngFor('ir/' + key), len = rt60 * 1.1 + pre, h = zeros(len), P = N(pre);
  for (let i = P; i < h.length; i++) { const t = (i - P) / SR; h[i] = (R() * 2 - 1) * exp(-6.9 * t / rt60) * min(1, t / 0.004); }
  filt(h, 'lp', (t) => hf0 * Math.pow(hf1 / hf0, min(1, max(0, (t - pre) / rt60))), 0.7);
  for (let k = 0; k < 7; k++) { const at = N(pre * 0.4 + R() * 0.035), g = (0.5 + R() * 0.5) * (R() < 0.5 ? -1 : 1) * 3; if (at < h.length) h[at] += g * 0.1; }
  let e = 0; for (let i = 0; i < h.length; i++) e += h[i] * h[i];
  gain(h, 1 / sqrt(e));
  IRS.set(key, h); return h;
}
// convolve a sound with a room; the input is cut where it has died away (-70 dB) to keep it quick. wet only,
// as long as the input
export function convVerb(x, opts = {}) {
  const p = peak(x), fl = p * db(-70); let end = x.length - 1; while (end > 0 && abs(x[end]) < fl) end--;
  const y = convolve(x.subarray(0, end + 1), roomIR(opts));
  const o = new Float64Array(x.length); o.set(y.subarray(0, x.length)); return o;
}

// mono Freeverb (Jezar's tunings), wet only
export function verb(x, { room = 0.7, damp = 0.4, pre = 0.008, out = 0 } = {}) {
  const n = x.length + N(out), y = new Float64Array(n);
  const sc = SR / 44100, fb = room * 0.28 + 0.7, d1 = damp * 0.4, d2 = 1 - d1, P = N(pre);
  const combs = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617].map((l) => ({ b: new Float64Array(round(l * sc)), i: 0, s: 0 }));
  const aps = [556, 441, 341, 225].map((l) => ({ b: new Float64Array(round(l * sc)), i: 0 }));
  for (let i = 0; i < n; i++) {
    const inp = (i - P >= 0 && i - P < x.length ? x[i - P] : 0) * 0.015;
    let acc = 0;
    for (const c of combs) {
      const o = c.b[c.i]; c.s = o * d2 + c.s * d1; c.b[c.i] = inp + c.s * fb; c.i = (c.i + 1) % c.b.length; acc += o;
    }
    for (const a of aps) { const bo = a.b[a.i]; const o = -acc + bo; a.b[a.i] = acc + bo * 0.5; a.i = (a.i + 1) % a.b.length; acc = o; }
    y[i] = acc;
  }
  return y;
}
// discrete echoes (buildings across the street): [delay s, gain, low-pass Hz]
export function echoes(x, taps, total) {
  const o = new Float64Array(total || x.length);
  for (const [t, g, f] of taps) { const y = Float64Array.from(x); lp2(y, f); mix(o, y, g, t); }
  return o;
}

// look-ahead peak limiter: never above ceil, gain falls over `look` before a peak and recovers over `rel`
export function limit(b, ceilDb = -1, look = 0.0015, rel = 0.06) {
  const c = db(ceilDb), L = max(1, N(look)), n = b.length;
  const need = new Float64Array(n);
  for (let i = 0; i < n; i++) need[i] = min(1, c / max(1e-12, abs(b[i])));
  const mw = new Float64Array(n); // min over [i, i + L]
  const dq = []; let head = 0;
  for (let j = 0, i = -L; i < n; i++, j++) {
    if (j < n) { while (dq.length > head && need[dq[dq.length - 1]] >= need[j]) dq.pop(); dq.push(j); }
    if (i >= 0) { while (dq[head] < i) head++; mw[i] = need[dq[head]]; }
  }
  let acc = 0; const avg = new Float64Array(n);
  for (let i = 0; i < n; i++) { acc += mw[i]; if (i >= L) acc -= mw[i - L]; avg[i] = acc / min(i + 1, L); }
  const r = exp(-1 / (rel * SR));
  let g = 1;
  for (let i = 0; i < n; i++) { const t = min(avg[i], mw[i]); g = t < g ? t : t + (g - t) * r; b[i] *= min(g, need[i]); }
  return b;
}

// BS.1770 K-weighting and the loudest 400 ms window, in LUFS (short sounds are counted with silence around them,
// which is how they are heard)
export function loudness(b) {
  const x = Float64Array.from(b);
  filt(x, 'hs', 1681.97, 0.7071, 4.0);
  filt(x, 'hp', 38.13, 0.5);
  const W = N(0.4), H = N(0.01);
  const cs = new Float64Array(x.length + 1);
  for (let i = 0; i < x.length; i++) cs[i + 1] = cs[i] + x[i] * x[i];
  let best = 0;
  for (let s = -W + H; s < x.length; s += H) {
    const a = max(0, s), e = min(x.length, s + W);
    if (e > a) best = max(best, (cs[e] - cs[a]) / W);
  }
  return best > 0 ? -0.691 + 10 * log10(best) : -120;
}

// trim the silent end, fade it, stop DC
export function finish(b, { push = 4, hpHz = 28, fade = 0.02, floorDb = -64, ceil = -1, minLen = 0 } = {}) {
  hp(b, hpHz, 0.7);
  norm(b);
  if (push) gain(b, db(push));
  limit(b, ceil);
  const fl = db(floorDb);
  let end = b.length - 1;
  while (end > 0 && abs(b[end]) < fl) end--;
  end = Math.max(end + N(0.01), N(minLen));
  const o = b.slice(0, min(b.length, end));
  const F = min(N(fade), o.length);
  for (let i = 0; i < F; i++) o[o.length - 1 - i] *= i / F;
  const F0 = min(N(0.0005), o.length); // no step at the very start either
  for (let i = 0; i < F0; i++) o[i] *= i / F0;
  return o;
}

export function writeWav(file, b) {
  const pcm = Buffer.alloc(44 + b.length * 2);
  pcm.write('RIFF', 0); pcm.writeUInt32LE(36 + b.length * 2, 4); pcm.write('WAVEfmt ', 8); pcm.writeUInt32LE(16, 16);
  pcm.writeUInt16LE(1, 20); pcm.writeUInt16LE(1, 22); pcm.writeUInt32LE(SR, 24); pcm.writeUInt32LE(SR * 2, 28);
  pcm.writeUInt16LE(2, 32); pcm.writeUInt16LE(16, 34); pcm.write('data', 36); pcm.writeUInt32LE(b.length * 2, 40);
  for (let i = 0; i < b.length; i++) pcm.writeInt16LE(round(max(-1, min(1, b[i])) * 32767), 44 + i * 2);
  fs.writeFileSync(file, pcm);
}
export function readWav(file) {
  const d = fs.readFileSync(file);
  let p = 12, fmt = null, data = null;
  while (p + 8 <= d.length) {
    const id = d.toString('ascii', p, p + 4), sz = d.readUInt32LE(p + 4);
    if (id === 'fmt ') fmt = { ch: d.readUInt16LE(p + 10), sr: d.readUInt32LE(p + 12), bits: d.readUInt16LE(p + 22) };
    if (id === 'data') data = d.subarray(p + 8, p + 8 + sz);
    p += 8 + sz + (sz & 1);
  }
  if (!fmt || !data || fmt.bits !== 16) throw new Error('not 16-bit PCM: ' + file);
  const n = floor(data.length / (2 * fmt.ch)), o = new Float64Array(n);
  for (let i = 0; i < n; i++) { let s = 0; for (let c = 0; c < fmt.ch; c++) s += data.readInt16LE((i * fmt.ch + c) * 2); o[i] = s / fmt.ch / 32768; }
  return { sr: fmt.sr, data: o };
}
