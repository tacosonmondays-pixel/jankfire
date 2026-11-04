// Every sound is synthesized from noise and beeps. Zero audio files. Maximum jank.
let ac = null, master = null, nbuf = null, vol = 0.5;
const loops = {};
const L = { pos: [0, 0, 0], yaw: 0 };

export function initAudio(v) {
  if (v != null) vol = v;
  if (ac) { ac.resume(); return; }
  const AC = window.AudioContext || window.webkitAudioContext;
  if (!AC) return;
  ac = new AC();
  master = ac.createGain();
  master.gain.value = vol;
  master.connect(ac.destination);
  nbuf = ac.createBuffer(1, ac.sampleRate * 2, ac.sampleRate);
  const d = nbuf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
}

export function setVolume(v) { vol = v; if (master) master.gain.value = v; }
export function setListener(p, yaw) { L.pos = p; L.yaw = yaw; }

function dest(pos) {
  const g = ac.createGain();
  if (!pos) { g.connect(master); return g; }
  const dx = pos[0] - L.pos[0], dy = pos[1] - L.pos[1], dz = pos[2] - L.pos[2];
  const dist = Math.hypot(dx, dy, dz);
  g.gain.value = 1 / (1 + dist / 10);
  if (dist < 0.5 || !ac.createStereoPanner) { g.connect(master); return g; }
  const pan = Math.max(-1, Math.min(1, (dx * Math.cos(L.yaw) - dz * Math.sin(L.yaw)) / dist));
  const p = ac.createStereoPanner();
  p.pan.value = pan * 0.8;
  g.connect(p); p.connect(master);
  return g;
}

function tone(type, f0, f1, dur, v, pos, delay = 0) {
  if (!ac) return;
  const t = ac.currentTime + delay;
  const o = ac.createOscillator();
  o.type = type;
  o.frequency.setValueAtTime(f0, t);
  o.frequency.exponentialRampToValueAtTime(Math.max(1, f1), t + dur);
  const g = ac.createGain();
  g.gain.setValueAtTime(v, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + dur);
  o.connect(g); g.connect(dest(pos));
  o.start(t); o.stop(t + dur + 0.05);
}

function noise(dur, v, type, f0, f1, pos, delay = 0, q = 1) {
  if (!ac) return;
  const t = ac.currentTime + delay;
  const s = ac.createBufferSource();
  s.buffer = nbuf;
  const f = ac.createBiquadFilter();
  f.type = type; f.Q.value = q;
  f.frequency.setValueAtTime(f0, t);
  f.frequency.exponentialRampToValueAtTime(Math.max(1, f1), t + dur);
  const g = ac.createGain();
  g.gain.setValueAtTime(v, t);
  g.gain.exponentialRampToValueAtTime(0.001, t + dur);
  s.connect(f); f.connect(g); g.connect(dest(pos));
  s.start(t, Math.random() * 1.5); s.stop(t + dur + 0.05);
}

export const sfx = {
  sniper(pos) { noise(0.7, 1, 'lowpass', 7000, 120, pos); tone('sawtooth', 220, 30, 0.5, 0.5, pos); tone('square', 1800, 200, 0.1, 0.15, pos); },
  boom(pos) { noise(1.1, 1, 'lowpass', 1800, 50, pos); tone('sine', 110, 25, 0.9, 0.9, pos); },
  squawk(pos) { tone('square', 700, 1500, 0.1, 0.22, pos); tone('square', 1500, 500, 0.18, 0.22, pos, 0.1); },
  pew(pos) { tone('square', 900, 250, 0.12, 0.2, pos); tone('sine', 300, 100, 0.08, 0.2, pos); },
  bonk(pos) { tone('square', 320, 70, 0.18, 0.45, pos); tone('triangle', 1300, 1250, 0.1, 0.3, pos); },
  whoops(pos) { tone('sine', 1600, 180, 0.7, 0.4, pos); tone('sine', 1610, 185, 0.7, 0.2, pos); },
  cough() { for (let i = 0; i < 3; i++) noise(0.16, 0.8, 'bandpass', 700, 350, null, i * 0.23, 2); },
  hit() { tone('square', 1900, 1900, 0.05, 0.18); },
  headshot() { tone('square', 2400, 2400, 0.07, 0.22); tone('square', 3300, 3300, 0.1, 0.18, null, 0.06); },
  hurt() { tone('sawtooth', 240, 90, 0.22, 0.3); },
  kill() {
    for (const [d, len] of [[0, 0.1], [0.13, 0.1], [0.26, 0.1], [0.4, 0.5]]) {
      for (const f of [466, 471, 233]) tone('sawtooth', f, f * 0.98, len, 0.1, null, d);
    }
  },
  death() { tone('sawtooth', 392, 370, 0.3, 0.25); tone('sawtooth', 370, 349, 0.3, 0.25, null, 0.32); tone('sawtooth', 349, 200, 0.9, 0.25, null, 0.64); },
  jump() { tone('sine', 280, 520, 0.07, 0.06); },
  pad(pos) { tone('sine', 140, 1000, 0.4, 0.4, pos); tone('square', 70, 500, 0.3, 0.08, pos); },
  grapple() { tone('sawtooth', 300, 1400, 0.12, 0.15); noise(0.1, 0.3, 'highpass', 3000, 6000); },
  swing(pos) { noise(0.16, 0.5, 'bandpass', 700, 2600, pos, 0, 2); },
  click() { tone('square', 500, 500, 0.03, 0.08); },
  land() { noise(0.08, 0.3, 'lowpass', 600, 100); },
  splat(pos) { noise(0.15, 0.5, 'lowpass', 2000, 300, pos); tone('sine', 200, 60, 0.15, 0.3, pos); },
  gun(id, pos, k = 0) {
    switch (id) {
      case 'marbles': noise(0.3, 0.9, 'lowpass', 3000, 120, pos); tone('sine', 110, 40, 0.25, 0.6, pos); for (let i = 0; i < 5; i++) tone('sine', 2400 + Math.random() * 2600, 2000, 0.03, 0.12, pos, 0.03 + i * 0.025); break;
      case 'redline': noise(0.1 - k * 0.05, 0.6, 'lowpass', 3800 + k * 3000, 300, pos); tone('square', 150 + k * 260, 70 + k * 120, 0.06 - k * 0.025, 0.22, pos); break;
      case 'ar': noise(0.13, 0.7, 'lowpass', 3500, 250, pos); tone('square', 160, 60, 0.08, 0.25, pos); break;
      case 'smg': noise(0.08, 0.5, 'lowpass', 5000, 400, pos); tone('square', 220, 90, 0.05, 0.18, pos); break;
      case 'shotgun': noise(0.45, 1, 'lowpass', 2600, 80, pos); tone('sine', 90, 30, 0.35, 0.8, pos); tone('square', 300, 200, 0.05, 0.2, pos, 0.35); break;
      case 'minigun': noise(0.05, 0.4, 'lowpass', 4000, 500, pos); break;
      case 'revolver': noise(0.35, 0.9, 'lowpass', 6000, 150, pos); tone('square', 1200, 300, 0.06, 0.2, pos); break;
      case 'sniper': sfx.sniper(pos); break;
      default: noise(0.1, 0.5, 'lowpass', 3000, 300, pos);
    }
  },
  reload() { tone('square', 400, 380, 0.04, 0.12); tone('square', 250, 240, 0.05, 0.12, null, 0.18); },
  empty() { tone('square', 900, 900, 0.02, 0.1); },
  marble(pos) { const f = 2600 + Math.random() * 2600; tone('sine', f, f * 0.92, 0.035, 0.07, pos); },
  ricochet(pos) { tone('sine', 2600, 900, 0.18, 0.15, pos); },
  squeak(pos) { tone('sine', 1100, 1900, 0.08, 0.3, pos); tone('sine', 1900, 1100, 0.1, 0.3, pos, 0.08); },
  thunk(pos) { tone('sine', 120, 50, 0.25, 0.7, pos); noise(0.12, 0.4, 'lowpass', 800, 100, pos); },
  strike(pos) { noise(0.6, 0.9, 'bandpass', 2500, 800, pos, 0, 0.8); tone('square', 600, 200, 0.2, 0.2, pos); },
  thwack(pos) { noise(0.07, 0.8, 'bandpass', 1800, 900, pos, 0, 1.5); },
  popper(pos) { noise(0.08, 0.9, 'highpass', 1500, 3000, pos); tone('sawtooth', 500, 700, 0.35, 0.15, pos, 0.05); },
  ting(pos) { tone('sine', 2800, 2700, 0.5, 0.35, pos); tone('sine', 4200, 4100, 0.3, 0.15, pos); },
  reverse(pos) { tone('sine', 300, 1600, 0.25, 0.3, pos); tone('triangle', 1600, 300, 0.25, 0.2, pos, 0.25); },
  hole(pos) { tone('sine', 80, 40, 2.4, 0.5, pos); noise(2.4, 0.3, 'lowpass', 300, 80, pos); },
  holePop(pos) { sfx.boom(pos); sfx.squeak(pos); },
  crunch(pos) { noise(0.09, 0.7, 'bandpass', 2200, 1400, pos, 0, 1.2); noise(0.07, 0.5, 'bandpass', 1800, 900, pos, 0.07, 1.2); },
  blow(pos) { noise(0.5, 0.35, 'highpass', 1500, 2500, pos); },
  rev(pos) { tone('sawtooth', 60, 140, 0.4, 0.15, pos); noise(0.4, 0.3, 'bandpass', 500, 900, pos); },
  bowShot(pos) { tone('triangle', 220, 90, 0.15, 0.35, pos); noise(0.12, 0.4, 'bandpass', 1200, 500, pos, 0, 2); },
  heal(pos) { tone('sine', 600, 1200, 0.25, 0.25, pos); tone('sine', 900, 1800, 0.25, 0.15, pos, 0.08); },
  laugh(pos) { for (let i = 0; i < 4; i++) tone('square', 500 - i * 40, 300, 0.09, 0.15, pos, i * 0.12); },
  snore() { noise(0.8, 0.25, 'lowpass', 400, 200); },
  partyHorn(pos) { tone('sawtooth', 420, 470, 0.5, 0.18, pos, 0.05); tone('square', 430, 480, 0.5, 0.08, pos, 0.05); },
  cash(pos) { tone('square', 1800, 1800, 0.06, 0.2, pos); tone('square', 2400, 2400, 0.3, 0.2, pos, 0.07); noise(0.2, 0.3, 'highpass', 4000, 6000, pos, 0.05); },
  glitch(pos) { for (let i = 0; i < 6; i++) tone('square', 200 + Math.random() * 2000, 100 + Math.random() * 3000, 0.04, 0.12, pos, i * 0.035); },
  pop(pos) { noise(0.06, 0.8, 'highpass', 800, 3000, pos); },
  error(pos) { tone('square', 880, 880, 0.12, 0.2, pos); tone('square', 660, 660, 0.25, 0.2, pos, 0.14); },
  yeet(pos) { noise(0.7, 0.5, 'bandpass', 400, 3000, pos, 0, 1.5); tone('sine', 300, 1400, 0.6, 0.15, pos); },
  choir(pos) { for (const [f, d] of [[523, 0], [659, 0.05], [784, 0.1], [1046, 0.15]]) tone('sine', f, f * 1.01, 2.2, 0.12, pos, d); },
  tbag(pos) { for (let i = 0; i < 3; i++) tone('sawtooth', 120 - i * 25, 40, 0.18, 0.3, pos, i * 0.1); },
};

const LOOPDEF = {
  fire: { type: 'lowpass', f: 900, q: 0.7, vol: 0.55 },
  inhale: { type: 'highpass', f: 2600, q: 0.7, vol: 0.14 },
  blower: { type: 'bandpass', f: 500, q: 0.6, vol: 0.5, osc: ['sawtooth', 68, 0.07] },
  spin: { type: 'bandpass', f: 1200, q: 2, vol: 0.25, osc: ['sawtooth', 110, 0.08] },
};

export function loopSfx(name, on) {
  if (!ac) return;
  let l = loops[name];
  if (!l) {
    if (!on) return;
    const def = LOOPDEF[name];
    const g = ac.createGain(); g.gain.value = 0; g.connect(master);
    const s = ac.createBufferSource(); s.buffer = nbuf; s.loop = true;
    const f = ac.createBiquadFilter(); f.type = def.type; f.frequency.value = def.f; f.Q.value = def.q;
    s.connect(f); f.connect(g); s.start();
    if (def.osc) {
      const o = ac.createOscillator(); o.type = def.osc[0]; o.frequency.value = def.osc[1];
      const og = ac.createGain(); og.gain.value = def.osc[2] / def.vol;
      o.connect(og); og.connect(g); o.start();
    }
    l = loops[name] = { g, on: false, def };
  }
  if (l.on !== on) {
    l.g.gain.setTargetAtTime(on ? l.def.vol : 0, ac.currentTime, 0.04);
    l.on = on;
  }
}

export function stopLoops() { for (const k in loops) loopSfx(k, false); }

// the backrooms hum: mains buzz from old fluorescent ballasts, two tubes slightly out of tune with each other. quiet, constant
let humG = null, humV = -1;
export function hum(on, k = 1) {
  if (!ac) return;
  const v = on ? 0.5 * k : 0;
  if (v === humV || (!humG && !v)) return;
  if (!humG) {
    humG = ac.createGain(); humG.gain.value = 0; humG.connect(master);
    const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 1400; lp.connect(humG);
    for (const [type, f, a] of [['sine', 60, 0.06], ['sawtooth', 120, 0.035], ['sawtooth', 120.4, 0.025], ['square', 180, 0.006]]) {
      const o = ac.createOscillator(); o.type = type; o.frequency.value = f;
      const g = ac.createGain(); g.gain.value = a; o.connect(g); g.connect(lp); o.start();
    }
    const s = ac.createBufferSource(); s.buffer = nbuf; s.loop = true; // the fizz of the tubes
    const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 5200; bp.Q.value = 4;
    const ng = ac.createGain(); ng.gain.value = 0.012;
    s.connect(bp); bp.connect(ng); ng.connect(humG); s.start();
  }
  humG.gain.setTargetAtTime(v, ac.currentTime, v ? 0.6 : 0.08);
  humV = v;
}
