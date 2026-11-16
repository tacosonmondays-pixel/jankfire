// the loot opening's sounds (LootOpening.luau) as .wav files for Roblox, built like render_items.mjs from tone() (an
// oscillator sliding f0 -> f1 under a decaying gain) and noise() (filtered white noise under a decaying gain). new
// recipes (the web game's crate opening used its tick(): a short square blip), tuned for a calm, solid feel: a dry
// tick per card, a heavy landing, a latch snap, and a sting per rarity that grows with it. no music, no voices.
// run: node tools/roblox/render_loot.mjs [outDir = roblox/assets/sounds]
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

// [name, seconds, what it is, Roblox volume, recipe]
const LIST = [
  ['loot_tick', 0.07, 'a card going past the marker in the opening reel', 0.5, (b) => { tone(b, 'square', 1500, 1050, 0.022, 0.12); noise(b, 0.018, 0.3, 'highpass', 3000, 5200); tone(b, 'sine', 2600, 2100, 0.03, 0.06); }],
  ['loot_land', 0.55, 'a loot container landing on the ground', 0.9, (b) => { tone(b, 'sine', 125, 42, 0.36, 0.9); noise(b, 0.3, 0.7, 'lowpass', 900, 70); noise(b, 0.09, 0.22, 'bandpass', 1900, 1200, 0.03, 3); tone(b, 'sine', 70, 40, 0.2, 0.4, 0.14); }],
  ['loot_pop', 0.4, 'a container popping open (latch snap and a puff)', 0.8, (b) => { tone(b, 'square', 2500, 650, 0.04, 0.2); noise(b, 0.14, 0.6, 'highpass', 1100, 4200); tone(b, 'sine', 280, 920, 0.2, 0.25, 0.03); }],
  ['loot_win_common', 0.6, 'the reel landing on a common item', 0.6, (b) => { tone(b, 'sine', 660, 660, 0.35, 0.25); tone(b, 'sine', 990, 990, 0.4, 0.2, 0.08); }],
  ['loot_win_rare', 0.85, 'the reel landing on a rare item', 0.65, (b) => { [660, 880, 1320].forEach((f, i) => { tone(b, 'sine', f, f, 0.45, 0.22, i * 0.07); tone(b, 'triangle', f * 2, f * 2, 0.2, 0.05, i * 0.07); }); }],
  ['loot_win_epic', 1.2, 'the reel landing on an epic item', 0.7, (b) => { [523, 659, 784].forEach((f, i) => tone(b, 'sine', f, f, 0.9, 0.22, i * 0.05)); tone(b, 'triangle', 1568, 1568, 0.5, 0.06, 0.15); noise(b, 0.5, 0.12, 'bandpass', 1500, 6000, 0, 1.2); tone(b, 'sine', 110, 55, 0.4, 0.3); }],
  ['loot_win_legendary', 1.8, 'the reel landing on a legendary item', 0.8, (b) => { [523, 659, 784, 1047, 1319].forEach((f, i) => { tone(b, 'sine', f, f, 1.2 - i * 0.1, 0.2, i * 0.07); tone(b, 'triangle', f * 2, f * 2, 0.4, 0.04, i * 0.07); }); noise(b, 1.2, 0.14, 'highpass', 5000, 9000, 0.3); tone(b, 'sine', 95, 38, 0.7, 0.6); noise(b, 0.4, 0.35, 'lowpass', 600, 60); }],
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
