// a contact sheet of sounds as a PNG: per sound its name, length and loudness, the waveform, and a log-frequency
// spectrogram (40 Hz at the bottom to 20 kHz at the top, -90..0 dB, dark to bright). for checking renders by eye.
// run: node tools/roblox/sfx_sheet.mjs out.png file1.wav file2.wav ...   (or a directory: every .wav in it)
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { readWav, loudness } from './sfx_dsp.mjs';

const [outFile, ...ins] = process.argv.slice(2);
let files = [];
for (const p of ins) {
  if (fs.statSync(p).isDirectory()) files.push(...fs.readdirSync(p).filter((f) => f.endsWith('.wav')).sort().map((f) => path.join(p, f)));
  else files.push(p);
}

const PW = 300, LH = 14, WH = 36, SH = 110, PH = LH + WH + SH + 6, COLS = 4, PAD = 6;
const rows = Math.ceil(files.length / COLS);
const W = COLS * (PW + PAD) + PAD, H = rows * (PH + PAD) + PAD;
const img = Buffer.alloc(W * H * 3, 18);
const put = (x, y, r, g, b) => { if (x < 0 || y < 0 || x >= W || y >= H) return; const i = (y * W + x) * 3; img[i] = r; img[i + 1] = g; img[i + 2] = b; };

// 3x5 font
const G = {
  a: '010101111101101', b: '110101110101110', c: '011100100100011', d: '110101101101110', e: '111100110100111', f: '111100110100100',
  g: '011100101101011', h: '101101111101101', i: '111010010010111', j: '001001001101010', k: '101101110101101', l: '100100100100111',
  m: '101111111101101', n: '110101101101101', o: '010101101101010', p: '110101110100100', q: '010101101110011', r: '110101110101101',
  s: '011100010001110', t: '111010010010010', u: '101101101101111', v: '101101101101010', w: '101101111111101', x: '101101010101101',
  y: '101101010010010', z: '111001010100111', 0: '111101101101111', 1: '010110010010111', 2: '110001010100111', 3: '110001010001110',
  4: '101101111001001', 5: '111100110001110', 6: '011100111101111', 7: '111001010010010', 8: '111101111101111', 9: '111101111001110',
  _: '000000000000111', '#': '101111101111101', '.': '000000000000010', '-': '000000111000000', ':': '000010000010000', ' ': '000000000000000',
};
function text(x, y, s, c = [230, 230, 230]) {
  for (const ch of s.toLowerCase()) {
    const g = G[ch] || G[' '];
    for (let r = 0; r < 5; r++) for (let q = 0; q < 3; q++) if (g[r * 3 + q] === '1') for (let a = 0; a < 2; a++) for (let b = 0; b < 2; b++) put(x + q * 2 + a, y + r * 2 + b, ...c);
    x += 8;
  }
}
// magma-ish colour map
const STOPS = [[0, 0, 4], [40, 11, 84], [101, 21, 110], [159, 42, 99], [212, 72, 66], [245, 125, 21], [250, 193, 39], [252, 255, 164]];
function cmap(u) {
  u = Math.max(0, Math.min(1, u)) * (STOPS.length - 1);
  const i = Math.min(STOPS.length - 2, Math.floor(u)), f = u - i, a = STOPS[i], b = STOPS[i + 1];
  return [0, 1, 2].map((k) => Math.round(a[k] + (b[k] - a[k]) * f));
}
function fft(re, im) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) { let bit = n >> 1; for (; j & bit; bit >>= 1) j ^= bit; j ^= bit; if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; } }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = -2 * Math.PI / len, wr = Math.cos(ang), wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) {
      let cr = 1, ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const ar = re[i + k], ai = im[i + k], br = re[i + k + len / 2] * cr - im[i + k + len / 2] * ci, bi = re[i + k + len / 2] * ci + im[i + k + len / 2] * cr;
        re[i + k] = ar + br; im[i + k] = ai + bi; re[i + k + len / 2] = ar - br; im[i + k + len / 2] = ai - bi;
        const t = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = t;
      }
    }
  }
}

files.forEach((file, idx) => {
  const { sr, data } = readWav(file);
  const ox = PAD + (idx % COLS) * (PW + PAD), oy = PAD + Math.floor(idx / COLS) * (PH + PAD);
  const secs = data.length / sr, L = loudness(data);
  let pk = 0; for (const x of data) pk = Math.max(pk, Math.abs(x));
  text(ox, oy + 2, `${path.basename(file, '.wav')} ${secs.toFixed(2)}s ${L.toFixed(0)}lu`);
  if (pk >= 0.999) text(ox + PW - 24, oy + 2, 'clip', [255, 80, 80]);
  // waveform (min/max per column)
  const wy = oy + LH, mid = wy + WH / 2;
  for (let x = 0; x < PW; x++) {
    const a = Math.floor(x * data.length / PW), b = Math.max(a + 1, Math.floor((x + 1) * data.length / PW));
    let lo = 0, hi = 0; for (let i = a; i < b && i < data.length; i++) { lo = Math.min(lo, data[i]); hi = Math.max(hi, data[i]); }
    for (let y = Math.round(mid - hi * WH / 2); y <= Math.round(mid - lo * WH / 2); y++) put(ox + x, y, 120, 200, 255);
    put(ox + x, mid, 60, 60, 70);
  }
  // spectrogram: one 1024-point frame per column
  const sy = wy + WH + 2, F = 1024, win = new Float64Array(F).map((_, i) => 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (F - 1)));
  const fmin = 40, fmax = Math.min(20000, sr / 2);
  for (let x = 0; x < PW; x++) {
    const c = Math.floor((x + 0.5) * data.length / PW), re = new Float64Array(F), im = new Float64Array(F);
    for (let i = 0; i < F; i++) { const j = c - F / 2 + i; re[i] = j >= 0 && j < data.length ? data[j] * win[i] : 0; }
    fft(re, im);
    for (let y = 0; y < SH; y++) {
      const f = fmin * Math.pow(fmax / fmin, 1 - y / (SH - 1)), bin = Math.min(F / 2 - 1, Math.round(f * F / sr));
      const mag = Math.hypot(re[bin], im[bin]) / (F / 4), dB = 20 * Math.log10(mag + 1e-9);
      put(ox + x, sy + y, ...cmap((dB + 90) / 90));
    }
  }
});

// PNG out
const crcT = new Int32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c; });
const crc = (buf) => { let c = -1; for (const b of buf) c = crcT[(c ^ b) & 255] ^ (c >>> 8); return (c ^ -1) >>> 0; };
const chunk = (type, data) => { const l = Buffer.alloc(4); l.writeUInt32BE(data.length); const td = Buffer.concat([Buffer.from(type), data]); const c = Buffer.alloc(4); c.writeUInt32BE(crc(td)); return Buffer.concat([l, td, c]); };
const raw = Buffer.alloc((W * 3 + 1) * H);
for (let y = 0; y < H; y++) img.copy(raw, y * (W * 3 + 1) + 1, y * W * 3, (y + 1) * W * 3);
const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(W, 0); ihdr.writeUInt32BE(H, 4); ihdr[8] = 8; ihdr[9] = 2;
fs.writeFileSync(outFile, Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]));
console.log(`${files.length} sounds -> ${outFile} (${W}x${H})`);
