// the utility items' sounds as .wav files for Roblox, with no browser and no ffmpeg, the same way render_guns.mjs does
// the guns: public/js/audio.js builds these out of tone() (an oscillator sliding f0 -> f1 under a decaying gain) and
// noise() (white noise through a sweeping low / high pass under a decaying gain); the recipes below are copied from its
// sfx.boom / heal / reverse / pop / blow. keep them in step with audio.js.
// run: node tools/roblox/render_items.mjs [outDir = roblox/assets/sounds]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const OUT = path.resolve(process.argv[2] || path.join(ROOT, 'roblox/assets/sounds'));
const SR = 44100;

let seed = 7654321;
const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
const ramp = (v0, v1, u) => v0 * Math.pow(v1 / v0, Math.min(1, Math.max(0, u))); // exponentialRampToValueAtTime

function tone(buf, type, f0, f1, dur, v, delay = 0) {
  const a = Math.floor(delay * SR), n = Math.floor((dur + 0.05) * SR);
  let ph = 0;
  for (let i = 0; i < n && a + i < buf.length; i++) {
    const u = i / (dur * SR);
    ph += ramp(f0, Math.max(1, f1), u) / SR;
    const x = ph % 1;
    const w = type === 'sine' ? Math.sin(2 * Math.PI * x) : type === 'square' ? (x < 0.5 ? 1 : -1) : type === 'sawtooth' ? 2 * x - 1 : 1 - 4 * Math.abs(x - 0.5);
    buf[a + i] += w * ramp(v, 0.001, u);
  }
}
function noise(buf, dur, v, type, f0, f1, delay = 0, q = 1) {
  const a = Math.floor(delay * SR), n = Math.floor((dur + 0.05) * SR);
  let x1 = 0, x2 = 0, y1 = 0, y2 = 0;
  const g = Math.pow(10, q / 20);
  for (let i = 0; i < n && a + i < buf.length; i++) {
    const u = i / (dur * SR);
    const w0 = 2 * Math.PI * Math.min(SR * 0.49, ramp(f0, Math.max(1, f1), u)) / SR;
    const cs = Math.cos(w0), al = Math.sin(w0) / (2 * g);
    let b0, b1, b2;
    let al2 = al;
    if (type === 'highpass') { b0 = (1 + cs) / 2; b1 = -(1 + cs); b2 = (1 + cs) / 2; }
    else if (type === 'bandpass') { al2 = Math.sin(w0) / (2 * q); b0 = al2; b1 = 0; b2 = -al2; } // (Web Audio: Q is linear for a band pass)
    else { b0 = (1 - cs) / 2; b1 = 1 - cs; b2 = (1 - cs) / 2; }
    const a0 = 1 + al2, a1 = -2 * cs, a2 = 1 - al2;
    const x = rnd() * 2 - 1;
    const y = (b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2) / a0;
    x2 = x1; x1 = x; y2 = y1; y1 = y;
    buf[a + i] += y * ramp(v, 0.001, u);
  }
}

// [name, seconds, what it is, Roblox volume, recipe (audio.js)]
const LIST = [
  ['boom', 1.2, 'a frag going off (sfx.boom)', 0.9, (b) => { noise(b, 1.1, 1, 'lowpass', 1800, 50); tone(b, 'sine', 110, 25, 0.9, 0.9); }],
  ['heal', 0.4, 'the medkit (sfx.heal)', 0.6, (b) => { tone(b, 'sine', 600, 1200, 0.25, 0.25); tone(b, 'sine', 900, 1800, 0.25, 0.15, 0.08); }],
  ['reverse', 0.55, 'a shield dome going up (sfx.reverse)', 0.6, (b) => { tone(b, 'sine', 300, 1600, 0.25, 0.3); tone(b, 'triangle', 1600, 300, 0.25, 0.2, 0.25); }],
  ['pop', 0.12, 'a shield dome going out (sfx.pop)', 0.6, (b) => { noise(b, 0.06, 0.8, 'highpass', 800, 3000); }],
  ['blow', 0.55, 'a smoke bomb popping into a cloud (sfx.blow)', 0.6, (b) => { noise(b, 0.5, 0.35, 'highpass', 1500, 2500); }],
  ['popper', 0.6, 'the party popper going off (sfx.popper + sfx.partyHorn)', 0.7, (b) => { noise(b, 0.08, 0.9, 'highpass', 1500, 3000); tone(b, 'sawtooth', 500, 700, 0.35, 0.15, 0.05); tone(b, 'sawtooth', 420, 470, 0.5, 0.18, 0.05); tone(b, 'square', 430, 480, 0.5, 0.08, 0.05); }],
  ['squeak', 0.25, 'a rubber duck squeak (sfx.squeak)', 0.6, (b) => { tone(b, 'sine', 1100, 1900, 0.08, 0.3); tone(b, 'sine', 1900, 1100, 0.1, 0.3, 0.08); }],
  ['quack', 0.22, 'the duck sticking to someone (sfx.quack)', 0.7, (b) => { tone(b, 'sawtooth', 640, 390, 0.15, 0.2); tone(b, 'square', 1280, 780, 0.12, 0.05); noise(b, 0.13, 0.3, 'bandpass', 1400, 800, 0, 5); }],
  ['hole', 3.0, 'a black hole humming (sfx.hole)', 0.7, (b) => { tone(b, 'sine', 80, 40, 2.9, 0.5); noise(b, 2.9, 0.3, 'lowpass', 300, 80); }],
  ['ropesnap', 0.15, 'your rope snapping in a black hole (sfx.ropeSnap)', 0.6, (b) => { tone(b, 'square', 2200, 300, 0.09, 0.2); noise(b, 0.08, 0.6, 'highpass', 2500, 5000); }],
];

const ONLY = process.argv.slice(3); // (a list of names: render just those)
fs.mkdirSync(OUT, { recursive: true });
for (const [name, secs, what, vol, fn] of LIST) {
  if (ONLY.length && !ONLY.includes(name)) continue;
  const buf = new Float32Array(Math.floor(secs * SR));
  fn(buf);
  let peak = 0;
  for (const x of buf) peak = Math.max(peak, Math.abs(x));
  const k = peak > 0.98 ? 0.98 / peak : 1; // (never clip)
  const n = buf.length, wav = Buffer.alloc(44 + n * 2);
  wav.write('RIFF', 0); wav.writeUInt32LE(36 + n * 2, 4); wav.write('WAVEfmt ', 8); wav.writeUInt32LE(16, 16);
  wav.writeUInt16LE(1, 20); wav.writeUInt16LE(1, 22); wav.writeUInt32LE(SR, 24); wav.writeUInt32LE(SR * 2, 28);
  wav.writeUInt16LE(2, 32); wav.writeUInt16LE(16, 34); wav.write('data', 36); wav.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) wav.writeInt16LE(Math.round(Math.max(-1, Math.min(1, buf[i] * k)) * 32767), 44 + i * 2);
  fs.writeFileSync(path.join(OUT, name + '.wav'), wav);
  console.log(name, secs + ' s', 'peak', peak.toFixed(2), 'vol', vol, '-', what);
}
