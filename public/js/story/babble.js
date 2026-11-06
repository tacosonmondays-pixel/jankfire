// OVERDUE babble voices (DESIGN §8.1): no voice acting, every character gets a synthesized voice. A syllable every
// couple of letters while their line types out; its pitch follows the letters (so the same line always "sounds" the
// same), questions go up at the end. voice(spec) -> { blip(ch, i, text), level, update(dt) }: level (0..1) is the
// loudness right now, which the face rig uses to flap the jaw.
// kinds: tuba (lumps), kazoo (wee gordo), dialtone (mr. overtime: a dial tone + a typewriter click per word),
// crayon (auntie: warm, wobbly), grumble (dale), beep (corp temps), choir (the gut choir: a chord), wet (the gut)
import { audioOut } from '../audio.js';

const hash = (c) => { const k = c.toLowerCase().charCodeAt(0); return ((k * 2654435761) >>> 0) / 4294967296; };
const VOW = new Set('aeiouy');

const KIND = {
  tuba: { wave: 'sawtooth', f: 95, spread: 0.35, len: 0.13, filt: ['lowpass', 520, 3], vib: 5, gain: 0.32, sub: 0.5 },
  kazoo: { wave: 'square', f: 360, spread: 0.5, len: 0.07, filt: ['bandpass', 1400, 4], vib: 18, gain: 0.16, buzz: 0.12 },
  dialtone: { wave: 'sine', f: 350, spread: 0, len: 0.11, chord: [440 / 350], filt: ['lowpass', 2400, 1], gain: 0.16, click: true },
  crayon: { wave: 'triangle', f: 230, spread: 0.4, len: 0.1, filt: ['lowpass', 1800, 2], vib: 6.5, vibA: 0.035, gain: 0.3 },
  grumble: { wave: 'square', f: 120, spread: 0.3, len: 0.11, filt: ['lowpass', 700, 2], vib: 3, gain: 0.18 },
  beep: { wave: 'sine', f: 620, spread: 0.15, len: 0.06, filt: ['lowpass', 4000, 0.5], gain: 0.2, steps: true },
  choir: { wave: 'sine', f: 260, spread: 0.12, len: 0.2, chord: [1.25, 1.5, 2], filt: ['lowpass', 1600, 1], vib: 5, gain: 0.12, airy: 0.05 },
  wet: { wave: 'sine', f: 180, spread: 0.4, len: 0.09, filt: ['lowpass', 900, 6], drop: 0.5, gain: 0.3, buzz: 0.08 },
};
export const VOICE_KINDS = Object.keys(KIND);

let noiseBuf = null;
function noise(ac) {
  if (noiseBuf) return noiseBuf;
  noiseBuf = ac.createBuffer(1, ac.sampleRate * 0.5, ac.sampleRate);
  const d = noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  return noiseBuf;
}

export function voice(spec = {}) {
  const K = KIND[spec.kind] || KIND.beep, P = spec.pitch ?? 1, R = spec.rate ?? 1;
  const v = { level: 0, kind: spec.kind || 'beep', every: Math.max(1, Math.round(2 / R)), lastWord: -1 };
  // one syllable. ch = the letter it's on, end = near the end of the line, q = the line is a question
  function syl(ch, end, q, loud = 1) {
    v.level = Math.min(1, v.level + 0.75 * loud);
    const o = audioOut(); if (!o) return;
    const { ac, master } = o, t = ac.currentTime + 0.005, h = hash(ch);
    let f = K.f * P * (1 + (h - 0.5) * K.spread * (VOW.has(ch.toLowerCase()) ? 1.3 : 0.7));
    if (K.steps) f = K.f * P * [1, 1.25, 1.5, 0.8][Math.floor(h * 4)];
    if (end && q) f *= 1.35; else if (end) f *= 0.88;
    const len = K.len * (0.75 + h * 0.5) / Math.sqrt(R);
    const out = ac.createGain(); out.gain.setValueAtTime(0, t);
    out.gain.linearRampToValueAtTime(K.gain * loud, t + 0.012); out.gain.setValueAtTime(K.gain * loud, t + len * 0.6); out.gain.exponentialRampToValueAtTime(0.0008, t + len);
    const flt = ac.createBiquadFilter(); flt.type = K.filt[0]; flt.frequency.value = K.filt[1] * (0.85 + h * 0.3); flt.Q.value = K.filt[2];
    flt.connect(out); out.connect(master);
    for (const m of [1, ...(K.chord || [])]) {
      const os = ac.createOscillator(); os.type = K.wave; os.frequency.setValueAtTime(f * m, t);
      if (K.drop) os.frequency.exponentialRampToValueAtTime(f * m * K.drop, t + len);
      else os.frequency.linearRampToValueAtTime(f * m * (end && q ? 1.12 : 0.97), t + len);
      if (K.vib) { const l = ac.createOscillator(), lg = ac.createGain(); l.frequency.value = K.vib; lg.gain.value = f * m * (K.vibA ?? 0.02); l.connect(lg); lg.connect(os.frequency); l.start(t); l.stop(t + len + 0.02); }
      os.connect(flt); os.start(t); os.stop(t + len + 0.02);
    }
    if (K.sub) { const s = ac.createOscillator(), sg = ac.createGain(); s.type = 'sine'; s.frequency.value = f * 0.5; sg.gain.value = K.sub; s.connect(sg); sg.connect(flt); s.start(t); s.stop(t + len); }
    if (K.buzz || K.airy) { const n = ac.createBufferSource(), ng = ac.createGain(); n.buffer = noise(ac); ng.gain.value = (K.buzz || K.airy) * 2; n.connect(ng); ng.connect(flt); n.start(t, Math.random() * 0.3, len); }
  }
  function click() { // the typewriter (overtime): a sharp high noise tick + a tiny bell
    const o = audioOut(); if (!o) return;
    const { ac, master } = o, t = ac.currentTime + 0.002;
    const n = ac.createBufferSource(), f = ac.createBiquadFilter(), gn = ac.createGain();
    n.buffer = noise(ac); f.type = 'highpass'; f.frequency.value = 3500; gn.gain.setValueAtTime(0.25, t); gn.gain.exponentialRampToValueAtTime(0.001, t + 0.03);
    n.connect(f); f.connect(gn); gn.connect(master); n.start(t, 0, 0.04);
  }
  // called for each new letter typed: i = its index in text
  v.blip = (ch, i, text) => {
    if (!ch || !/[a-z0-9]/i.test(ch)) { if (ch === ' ' && K.click) click(); return; }
    if (i % v.every) return;
    const rest = text.slice(i);
    syl(ch, !/[a-z0-9].*[a-z0-9]{3}/i.test(rest.slice(1)), /\?\s*$/.test(text), /[A-Z]/.test(ch) && text === text.toUpperCase() ? 1.3 : 1);
  };
  v.say1 = (ch = 'a') => syl(ch, true, false); // a single grunt (cutscenes, reactions)
  v.update = (dt) => { v.level = Math.max(0, v.level - dt * 7); };
  return v;
}
