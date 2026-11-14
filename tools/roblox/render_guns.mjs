// the plain guns' shot sounds as .wav files for Roblox, with no browser and no ffmpeg: public/js/audio.js builds every
// gun shot out of two Web Audio primitives, tone() (an oscillator sliding f0 -> f1 under a decaying gain) and noise()
// (white noise through a sweeping low/high pass under a decaying gain), so this renders the same recipes offline.
// the recipes below are copied from sfx.gun() in audio.js: keep them in step when a gun's sound changes there.
// (render_sounds.cjs does the same job through headless Chromium + ffmpeg for sounds that use more of Web Audio.)
// run: node tools/roblox/render_guns.mjs [outDir = roblox/assets/sounds]
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const OUT = path.resolve(process.argv[2] || path.join(ROOT, 'roblox/assets/sounds'));
const SR = 44100;

let seed = 1234567;
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
  const g = Math.pow(10, q / 20); // Web Audio: Q is in dB for low / high pass
  for (let i = 0; i < n && a + i < buf.length; i++) {
    const u = i / (dur * SR);
    const w0 = 2 * Math.PI * Math.min(SR * 0.49, ramp(f0, Math.max(1, f1), u)) / SR;
    const cs = Math.cos(w0), al = Math.sin(w0) / (2 * g);
    let b0, b1, b2;
    if (type === 'highpass') { b0 = (1 + cs) / 2; b1 = -(1 + cs); b2 = (1 + cs) / 2; } else { b0 = (1 - cs) / 2; b1 = 1 - cs; b2 = (1 - cs) / 2; }
    const a0 = 1 + al, a1 = -2 * cs, a2 = 1 - al;
    const x = rnd() * 2 - 1;
    const y = (b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2) / a0;
    x2 = x1; x1 = x; y2 = y1; y1 = y;
    buf[a + i] += y * ramp(v, 0.001, u);
  }
}

// [name, seconds, what it is, Roblox volume, recipe]
const GUNS = [
  ['gun_ar', 0.2, 'Assault Rifle shot', 0.6, (b) => { noise(b, 0.13, 0.7, 'lowpass', 3500, 250); tone(b, 'square', 160, 60, 0.08, 0.25); }],
  ['gun_smg', 0.15, 'SMG shot', 0.55, (b) => { noise(b, 0.08, 0.5, 'lowpass', 5000, 400); tone(b, 'square', 220, 90, 0.05, 0.18); }],
  ['gun_shotgun', 0.55, 'Shotgun shot (boom + the pump after)', 0.8, (b) => { noise(b, 0.45, 1, 'lowpass', 2600, 80); tone(b, 'sine', 90, 30, 0.35, 0.8); tone(b, 'square', 300, 200, 0.05, 0.2, 0.35); }],
  ['gun_minigun', 0.11, 'Minigun shot', 0.5, (b) => { noise(b, 0.05, 0.4, 'lowpass', 4000, 500); }],
  ['gun_revolver', 0.42, 'Revolver shot', 0.75, (b) => { noise(b, 0.35, 0.9, 'lowpass', 6000, 150); tone(b, 'square', 1200, 300, 0.06, 0.2); }],
  ['gun_burst', 0.16, 'Hat Trick shot', 0.6, (b) => { noise(b, 0.09, 0.62, 'lowpass', 5200, 380); tone(b, 'square', 200, 75, 0.055, 0.2); noise(b, 0.02, 0.25, 'highpass', 5000, 8000); }],
  ['gun_lmg', 0.18, 'Belt Sander shot (cold barrel)', 0.6, (b) => { noise(b, 0.11, 0.5, 'lowpass', 2800, 180); tone(b, 'square', 120, 45, 0.08, 0.2); }],
  ['gun_dmr', 0.5, 'Second Opinion shot', 0.75, (b) => { noise(b, 0.42, 0.95, 'lowpass', 6500, 130); tone(b, 'sawtooth', 260, 38, 0.3, 0.42); tone(b, 'square', 1500, 240, 0.07, 0.16); }],
  ['gun_lever', 0.4, 'Yeehaw shot', 0.75, (b) => { noise(b, 0.32, 0.85, 'lowpass', 5200, 120); tone(b, 'sine', 150, 42, 0.26, 0.55); tone(b, 'square', 900, 260, 0.05, 0.12); }],
  ['gun_autoshot', 0.38, 'Lawn Mower shot', 0.75, (b) => { noise(b, 0.3, 0.9, 'lowpass', 2400, 90); tone(b, 'sine', 85, 30, 0.25, 0.65); tone(b, 'square', 260, 180, 0.04, 0.16, 0.04); }],
  ['gun_pistol', 0.24, 'Plan B shot', 0.65, (b) => { noise(b, 0.16, 0.75, 'lowpass', 5200, 220); tone(b, 'square', 950, 240, 0.045, 0.2); noise(b, 0.03, 0.3, 'highpass', 4000, 7000); }],
  ['gun_akimbo', 0.13, 'Lefty & Righty shot', 0.5, (b) => { noise(b, 0.065, 0.45, 'lowpass', 5600, 500); tone(b, 'square', 370, 130, 0.04, 0.15); }],
  ['gun_sawnoff', 0.68, 'Half a Shotgun shot', 0.85, (b) => { noise(b, 0.6, 1, 'lowpass', 2200, 60); tone(b, 'sine', 75, 24, 0.45, 0.95); noise(b, 0.06, 0.6, 'highpass', 2500, 5000); tone(b, 'square', 220, 90, 0.08, 0.25, 0.02); }],
];

fs.mkdirSync(OUT, { recursive: true });
const list = [];
for (const [name, secs, what, vol, recipe] of GUNS) {
  const buf = new Float64Array(Math.ceil(secs * SR));
  recipe(buf);
  let peak = 0;
  for (const x of buf) peak = Math.max(peak, Math.abs(x));
  const k = peak > 0.98 ? 0.98 / peak : 1; // only tame what would clip; quiet guns stay quiet
  const fade = Math.floor(0.008 * SR);
  const pcm = Buffer.alloc(44 + buf.length * 2);
  pcm.write('RIFF', 0); pcm.writeUInt32LE(36 + buf.length * 2, 4); pcm.write('WAVEfmt ', 8); pcm.writeUInt32LE(16, 16);
  pcm.writeUInt16LE(1, 20); pcm.writeUInt16LE(1, 22); pcm.writeUInt32LE(SR, 24); pcm.writeUInt32LE(SR * 2, 28);
  pcm.writeUInt16LE(2, 32); pcm.writeUInt16LE(16, 34); pcm.write('data', 36); pcm.writeUInt32LE(buf.length * 2, 40);
  for (let i = 0; i < buf.length; i++) {
    const tail = Math.min(1, (buf.length - 1 - i) / fade);
    pcm.writeInt16LE(Math.round(Math.max(-1, Math.min(1, buf[i] * k * tail)) * 32767), 44 + i * 2);
  }
  fs.writeFileSync(path.join(OUT, name + '.wav'), pcm);
  list.push({ name, what, vol, secs, peak: Math.round(Math.min(peak, 0.98) * 100) / 100 });
}
fs.writeFileSync(path.join(OUT, 'guns.json'), JSON.stringify(list, null, 1));
console.log(list.map((s) => `${s.name} ${s.secs}s peak ${s.peak}`).join('\n'));
