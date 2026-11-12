// The map editor's sounds, synthesized like the game's (audio.js): a hum while the grabby beam holds something, a
// clunk when it lands, a pew + pop for the plop cannon, a zap + poof for the yeet ray, a click when a turn snaps.
let ac = null, out = null;
function ctx() {
  if (ac) return ac;
  try { ac = new (window.AudioContext || window.webkitAudioContext)(); out = ac.createGain(); out.gain.value = 0.35; out.connect(ac.destination); } catch { ac = null; }
  return ac;
}
export function unlockAudio() { const a = ctx(); if (a && a.state === 'suspended') a.resume().catch(() => {}); }
export function setEdVolume(v) { if (ctx() && out) out.gain.value = Math.max(0, Math.min(1, v)) * 0.7; }
const now = () => ac.currentTime;
function env(g, t, a, peak, d) { g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + a); g.gain.exponentialRampToValueAtTime(0.0001, t + a + d); }
function tone(type, f0, f1, dur, peak = 0.5, at = 0) {
  if (!ctx()) return;
  const t = now() + at, o = ac.createOscillator(), g = ac.createGain();
  o.type = type; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + dur);
  env(g, t, 0.005, peak, dur); o.connect(g).connect(out); o.start(t); o.stop(t + dur + 0.05);
}
let noiseBuf = null;
function noise(dur, f0, f1, q = 1, peak = 0.5, at = 0, type = 'bandpass') {
  if (!ctx()) return;
  if (!noiseBuf) { noiseBuf = ac.createBuffer(1, ac.sampleRate, ac.sampleRate); const d = noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; }
  const t = now() + at, s = ac.createBufferSource(), f = ac.createBiquadFilter(), g = ac.createGain();
  s.buffer = noiseBuf; f.type = type; f.Q.value = q; f.frequency.setValueAtTime(f0, t); f.frequency.exponentialRampToValueAtTime(Math.max(30, f1), t + dur);
  env(g, t, 0.004, peak, dur); s.connect(f).connect(g).connect(out); s.start(t); s.stop(t + dur + 0.05);
}
export const sfxEd = {
  grab() { tone('square', 180, 620, 0.12, 0.25); noise(0.1, 3000, 900, 2, 0.25); },
  clunk() { tone('sine', 140, 45, 0.22, 0.7); noise(0.08, 900, 200, 1, 0.5); },
  thud(big) { tone('sine', big ? 90 : 120, 35, 0.3, 0.8); noise(0.14, 600, 120, 0.8, 0.6); },
  freeze() { tone('triangle', 1400, 700, 0.12, 0.3); tone('triangle', 2100, 1050, 0.12, 0.2, 0.05); },
  pew() { tone('square', 1100, 180, 0.16, 0.3); },
  pop() { tone('sine', 380, 1150, 0.09, 0.5); },
  zap() { noise(0.18, 6000, 800, 3, 0.35); tone('sawtooth', 900, 60, 0.2, 0.25); },
  poof() { noise(0.35, 1800, 200, 0.7, 0.5, 0.05); tone('sine', 520, 1600, 0.12, 0.25, 0.08); },
  click() { tone('square', 2400, 1800, 0.03, 0.18); },
  swap() { tone('triangle', 500, 900, 0.07, 0.2); },
  whoosh() { noise(0.4, 500, 2600, 0.6, 0.35); },
  nope() { tone('square', 220, 140, 0.18, 0.25); },
};
// the beam's hum: two detuned saws through a wobbling filter, on while you hold something
let hum = null;
export function humOn() {
  if (!ctx() || hum) return;
  const t = now(), g = ac.createGain(), f = ac.createBiquadFilter(), a = ac.createOscillator(), b = ac.createOscillator(), lfo = ac.createOscillator(), lg = ac.createGain();
  a.type = 'sawtooth'; b.type = 'sawtooth'; a.frequency.value = 72; b.frequency.value = 73.3;
  f.type = 'lowpass'; f.frequency.value = 520; f.Q.value = 6; lfo.frequency.value = 5.5; lg.gain.value = 260;
  lfo.connect(lg).connect(f.frequency); a.connect(f); b.connect(f); f.connect(g).connect(out);
  g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.16, t + 0.08);
  a.start(); b.start(); lfo.start();
  hum = { g, a, b, lfo, f };
}
export function humPitch(k) { if (hum) { hum.a.frequency.value = 72 * k; hum.b.frequency.value = 73.3 * k; } } // (strains when you push it far)
export function humOff() {
  if (!hum) return;
  const h = hum, t = now(); hum = null;
  h.g.gain.cancelScheduledValues(t); h.g.gain.setValueAtTime(h.g.gain.value || 0.1, t); h.g.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);
  for (const o of [h.a, h.b, h.lfo]) o.stop(t + 0.15);
}
