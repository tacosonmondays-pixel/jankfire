// Every sound is synthesized from noise and beeps. Zero audio files. Maximum jank.
let ac = null, master = null, nbuf = null, vol = 0.5;
const loops = {};
const L = { pos: [0, 0, 0], yaw: 0 };
let hsAt = -1; // when the last headshot DINK played
let hsTakenAt = -1; // when the last headshot TONK played on you

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
// music.js plays through the same master, so the volume slider scales the music too
export function audioOut() { return ac ? { ac, master } : null; }
export function setListener(p, yaw) { L.pos = p; L.yaw = yaw; }
// sealed in a soap bubble: everything you hear goes through a low pass, like your head is underwater
let muffle = null;
export function setMuffle(on, instant, tc = 0.06) { // tc: how fast it eases there (a time constant, s)
  if (!ac) return;
  if (!muffle) { muffle = ac.createBiquadFilter(); muffle.type = 'lowpass'; muffle.frequency.value = 22000; master.disconnect(); master.connect(muffle); muffle.connect(ac.destination); }
  const f = muffle.frequency, t = ac.currentTime, to = on ? 480 : 22000;
  f.cancelScheduledValues(t);
  if (instant) f.setValueAtTime(to, t); else f.setTargetAtTime(to, t, tc);
}

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
// the overdrive rig makes its own sounds (rigsfx.js) with these: same context, master volume and panning
export const synth = { tone: (...a) => tone(...a), noise: (...a) => noise(...a), whoosh: (...a) => whoosh(...a), // (whoosh: lasso.js)
  dest: (p) => dest(p), get ac() { return ac; }, get out() { return master; } };

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

// filtered noise that fades in and out (noise() starts at full volume, which clicks): air rushing past
function whoosh(dur, v, f0, f1, q = 1.2, pos = null) {
  if (!ac) return;
  const t = ac.currentTime;
  const s = ac.createBufferSource();
  s.buffer = nbuf;
  const f = ac.createBiquadFilter();
  f.type = 'bandpass'; f.Q.value = q;
  f.frequency.setValueAtTime(f0, t);
  f.frequency.exponentialRampToValueAtTime(f1, t + dur * 0.45);
  f.frequency.exponentialRampToValueAtTime(f0 * 0.8, t + dur);
  const g = ac.createGain();
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(v, t + dur * 0.3);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  s.connect(f); f.connect(g); g.connect(dest(pos));
  s.start(t, Math.random() * 1.5); s.stop(t + dur + 0.05);
}

export const sfx = {
  // grapple jump: one clean whoosh, a little brighter when you timed it on the upswing
  ropeJump(q = 0) { whoosh(0.42, 0.32, 380, 1500 + q * 900); tone('sine', 150, 60, 0.14, 0.07); },
  sniper(pos) { noise(0.7, 1, 'lowpass', 7000, 120, pos); tone('sawtooth', 220, 30, 0.5, 0.5, pos); tone('square', 1800, 200, 0.1, 0.15, pos); },
  boom(pos) { noise(1.1, 1, 'lowpass', 1800, 50, pos); tone('sine', 110, 25, 0.9, 0.9, pos); },
  squawk(pos) { tone('square', 700, 1500, 0.1, 0.22, pos); tone('square', 1500, 500, 0.18, 0.22, pos, 0.1); },
  pew(pos) { tone('square', 900, 250, 0.12, 0.2, pos); tone('sine', 300, 100, 0.08, 0.2, pos); },
  bonk(pos) { tone('square', 320, 70, 0.18, 0.45, pos); tone('triangle', 1300, 1250, 0.1, 0.3, pos); },
  whoops(pos) { tone('sine', 1600, 180, 0.7, 0.4, pos); tone('sine', 1610, 185, 0.7, 0.2, pos); },
  cough() { for (let i = 0; i < 3; i++) noise(0.16, 0.8, 'bandpass', 700, 350, null, i * 0.23, 2); },
  hit() { tone('square', 1900, 1900, 0.05, 0.18); },
  // headshot DINK: struck steel rings at inharmonic partials (x2.76, x5.4), so stack those over a bright ping with a
  // tick of noise for the attack and a little bass thump under it. ko = the headshot killed: heavier, lower, a double ping
  headshot(ko) {
    if (!ac) return;
    const n = ac.currentTime, rapid = n - hsAt < 0.06; // minigun headshots: don't stack a wall of rings
    hsAt = n;
    if (ko) {
      noise(0.04, 0.5, 'highpass', 5000, 11000);
      for (const [f, v, d, dl] of [[1760, 0.26, 0.55, 0], [1767, 0.11, 0.5, 0], [1760 * 2.76, 0.1, 0.22, 0], [1760 * 5.4, 0.04, 0.1, 0], [2640, 0.2, 0.45, 0.075], [2640 * 2.76, 0.06, 0.14, 0.075]]) tone('sine', f, f * 0.985, d, v, null, dl);
      tone('triangle', 3520, 3480, 0.2, 0.08, null, 0.075);
      tone('sine', 130, 36, 0.32, 0.5); // the thump, bigger (kept under a boom: kill() plays on top)
      tone('square', 95, 40, 0.07, 0.08);
      noise(0.22, 0.3, 'lowpass', 900, 60);
      return;
    }
    const k = rapid ? 0.5 : 1;
    noise(0.025, 0.45 * k, 'highpass', 7000, 11000);
    tone('sine', 2350, 2310, 0.32 * k, 0.27 * k);
    tone('sine', 2358, 2318, 0.28 * k, 0.12 * k); // a hair detuned: shimmer
    tone('sine', 2350 * 2.76, 6380, 0.13, 0.09 * k);
    tone('sine', 2350 * 5.4, 12500, 0.05, 0.035 * k);
    tone('triangle', 3525, 3500, 0.09, 0.09 * k);
    tone('square', 4700, 4700, 0.015, 0.06 * k);
    if (!rapid) tone('sine', 175, 55, 0.12, 0.42); // thump
  },
  // you got headshot: a dull helmet TONK (low wobbly metal, felt through the skull) and a crunch.
  // ko = it killed you: deeper, longer, a bone crack and your ears ring
  headshotTaken(ko) {
    if (!ac) return;
    const n = ac.currentTime, rapid = n - hsTakenAt < 0.08;
    hsTakenAt = n;
    if (rapid && !ko) { // automatic fire on your head: full TONKs every 40 ms stack up and clip, so just a small one
      tone('triangle', 540, 455, 0.12, 0.16);
      noise(0.05, 0.25, 'bandpass', 2400, 1300, null, 0, 1.3);
      return;
    }
    const k = ko ? 1 : 0;
    tone('triangle', 540 - k * 150, 455 - k * 130, 0.26 + k * 0.25, 0.4);
    tone('sine', (540 - k * 150) * 2.32, 1000 - k * 330, 0.14 + k * 0.1, 0.16);
    tone('sine', (540 - k * 150) * 1.51, 760 - k * 220, 0.18, 0.12);
    tone('sine', 150 - k * 40, 42, 0.18 + k * 0.22, 0.55 + k * 0.1); // thump through the skull
    noise(0.09, 0.7, 'bandpass', 2400, 1300, null, 0.01, 1.3); // crunch
    noise(0.08, 0.5, 'bandpass', 1700, 800, null, 0.07, 1.3);
    if (ko) {
      noise(0.11, 0.6, 'bandpass', 3200, 900, null, 0.03, 2); // crack
      noise(0.4, 0.35, 'lowpass', 1200, 50);
      tone('sine', 3900, 3860, 1.5, 0.045, null, 0.06); // ringing ears
    }
  },
  hurt() { tone('sawtooth', 240, 90, 0.22, 0.3); },
  kill() {
    for (const [d, len] of [[0, 0.1], [0.13, 0.1], [0.26, 0.1], [0.4, 0.5]]) {
      for (const f of [466, 471, 233]) tone('sawtooth', f, f * 0.98, len, 0.1, null, d);
    }
  },
  death() { tone('sawtooth', 392, 370, 0.3, 0.25); tone('sawtooth', 370, 349, 0.3, 0.25, null, 0.32); tone('sawtooth', 349, 200, 0.9, 0.25, null, 0.64); },
  jump() { tone('sine', 280, 520, 0.07, 0.06); },
  pad(pos) { tone('sine', 140, 1000, 0.4, 0.4, pos); tone('square', 70, 500, 0.3, 0.08, pos); },
  grapple(skin, pos) { // the hook landing, per grapple skin. pos = someone else's hook: quieter, from where it hit
    const q = pos ? 0.6 : 1;
    switch (skin) {
      case 'chain': for (let i = 0; i < 4; i++) tone('triangle', 2100 + Math.random() * 1600, 1700, 0.06, 0.12 * q, pos, i * 0.035); noise(0.15, 0.25 * q, 'highpass', 3000, 6000, pos); break;
      case 'candy': tone('sine', 1568, 1568, 0.22, 0.14 * q, pos); tone('sine', 2093, 2093, 0.3, 0.1 * q, pos, 0.06); noise(0.08, 0.2 * q, 'highpass', 3000, 6000, pos); break;
      case 'plunger': tone('sine', 420, 90, 0.16, 0.45 * q, pos); noise(0.12, 0.35 * q, 'lowpass', 900, 200, pos); tone('square', 600, 950, 0.06, 0.05 * q, pos, 0.1); break;
      case 'vine': noise(0.18, 0.35 * q, 'bandpass', 600, 2200, pos, 0, 1.5); tone('triangle', 260, 170, 0.08, 0.35 * q, pos, 0.1); break;
      case 'laser': tone('square', 2400, 300, 0.18, 0.11 * q, pos); tone('sawtooth', 1200, 150, 0.2, 0.07 * q, pos); noise(0.1, 0.15 * q, 'highpass', 5000, 9000, pos); break;
      case 'sticky': noise(0.14, 0.5 * q, 'lowpass', 1800, 250, pos); tone('sine', 300, 110, 0.12, 0.3 * q, pos); tone('sine', 220, 340, 0.16, 0.14 * q, pos, 0.07); break;
      case 'rainbow': [1047, 1319, 1568, 2093].forEach((f, i) => tone('triangle', f, f, 0.14, 0.1 * q, pos, i * 0.05)); noise(0.1, 0.15 * q, 'highpass', 4000, 8000, pos); break;
      default: tone('sawtooth', 300, 1400, 0.12, 0.15 * q, pos); noise(0.1, 0.3 * q, 'highpass', 3000, 6000, pos);
    }
  },
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
  hammer(pos) { tone('square', 2300, 1500, 0.018, 0.12, pos); noise(0.025, 0.35, 'highpass', 3500, 6000, pos); }, // fanning: slap the hammer back
  twirl(pos) { noise(0.2, 0.16, 'bandpass', 700, 2400, pos, 0.02, 2.5); tone('square', 320, 260, 0.025, 0.06, pos, 0.24); }, // whirr round the finger, tk into the palm
  clatter(pos) { for (let i = 0; i < 10; i++) { const f = 2000 + Math.random() * 3600; tone('sine', f, f * 0.9, 0.04, 0.1, pos, i * 0.028 + Math.random() * 0.03); } noise(0.3, 0.18, 'highpass', 3000, 5000, pos); }, // a pile of marbles going everywhere
  marble(pos) { const f = 2600 + Math.random() * 2600; tone('sine', f, f * 0.92, 0.035, 0.07, pos); },
  ricochet(pos) { tone('sine', 2600, 900, 0.18, 0.15, pos); },
  squeak(pos) { tone('sine', 1100, 1900, 0.08, 0.3, pos); tone('sine', 1900, 1100, 0.1, 0.3, pos, 0.08); },
  thunk(pos) { tone('sine', 120, 50, 0.25, 0.7, pos); noise(0.12, 0.4, 'lowpass', 800, 100, pos); },
  strike(pos) { noise(0.6, 0.9, 'bandpass', 2500, 800, pos, 0, 0.8); tone('square', 600, 200, 0.2, 0.2, pos); },
  thwack(pos) { noise(0.07, 0.8, 'bandpass', 1800, 900, pos, 0, 1.5); },
  popper(pos) { noise(0.08, 0.9, 'highpass', 1500, 3000, pos); tone('sawtooth', 500, 700, 0.35, 0.15, pos, 0.05); },
  ting(pos) { tone('sine', 2800, 2700, 0.5, 0.35, pos); tone('sine', 4200, 4100, 0.3, 0.15, pos); },
  reverse(pos) { tone('sine', 300, 1600, 0.25, 0.3, pos); tone('triangle', 1600, 300, 0.25, 0.2, pos, 0.25); },
  hole(pos) { tone('sine', 80, 40, 2.9, 0.5, pos); noise(2.9, 0.3, 'lowpass', 300, 80, pos); },
  holePop(pos) { sfx.boom(pos); sfx.squeak(pos); },
  quack(pos, v = 1) { tone('sawtooth', 640, 390, 0.15, 0.2 * v, pos); tone('square', 1280, 780, 0.12, 0.05 * v, pos); noise(0.13, 0.3 * v, 'bandpass', 1400, 800, pos, 0, 5); },
  ropeSnap(pos) { tone('square', 2200, 300, 0.09, 0.2, pos); noise(0.08, 0.6, 'highpass', 2500, 5000, pos); },
  crunch(pos) { noise(0.09, 0.7, 'bandpass', 2200, 1400, pos, 0, 1.2); noise(0.07, 0.5, 'bandpass', 1800, 900, pos, 0.07, 1.2); },
  blow(pos) { noise(0.5, 0.35, 'highpass', 1500, 2500, pos); },
  // spray can: clack clack (the ball rattling), then pssssht: overlapping hiss bursts so it sputters, and a short cut-off
  spray(pos) {
    tone('square', 2300, 2100, 0.025, 0.07, pos); tone('square', 2000, 1800, 0.025, 0.07, pos, 0.07);
    noise(0.06, 0.35, 'bandpass', 900, 500, pos, 0.13, 1.2);
    for (let i = 0; i < 7; i++) noise(0.24, 0.3, 'highpass', 4600 - i * 120, 2600, pos, 0.15 + i * 0.07, 0.8);
    noise(0.09, 0.32, 'bandpass', 3600, 1400, pos, 0.66, 1.5);
  },
  rev(pos) { tone('sawtooth', 60, 140, 0.4, 0.15, pos); noise(0.4, 0.3, 'bandpass', 500, 900, pos); },
  bowShot(pos) { tone('triangle', 220, 90, 0.15, 0.35, pos); noise(0.12, 0.4, 'bandpass', 1200, 500, pos, 0, 2); },
  heal(pos) { tone('sine', 600, 1200, 0.25, 0.25, pos); tone('sine', 900, 1800, 0.25, 0.15, pos, 0.08); },
  laugh(pos) { for (let i = 0; i < 4; i++) tone('square', 500 - i * 40, 300, 0.09, 0.15, pos, i * 0.12); },
  snore() { noise(0.8, 0.25, 'lowpass', 400, 200); },
  partyHorn(pos) { tone('sawtooth', 420, 470, 0.5, 0.18, pos, 0.05); tone('square', 430, 480, 0.5, 0.08, pos, 0.05); },
  cash(pos) { tone('square', 1800, 1800, 0.06, 0.2, pos); tone('square', 2400, 2400, 0.3, 0.2, pos, 0.07); noise(0.2, 0.3, 'highpass', 4000, 6000, pos, 0.05); },
  glitch(pos) { for (let i = 0; i < 6; i++) tone('square', 200 + Math.random() * 2000, 100 + Math.random() * 3000, 0.04, 0.12, pos, i * 0.035); },
  pop(pos) { noise(0.06, 0.8, 'highpass', 800, 3000, pos); },
  // bubble wand: blowing one, a little one popping, getting sealed in, the giant one popping, blubbing inside
  bloop(pos) { const f = 240 + Math.random() * 180; tone('sine', f, f * 3.4, 0.11, 0.32, pos); tone('sine', f * 7, f * 9, 0.035, 0.05, pos, 0.09); },
  plip(pos) { tone('sine', 1800 + Math.random() * 900, 3400, 0.035, 0.1, pos); noise(0.03, 0.2, 'highpass', 3000, 6000, pos); },
  glorp(pos) { tone('sine', 130, 560, 0.34, 0.45, pos); tone('triangle', 85, 240, 0.42, 0.22, pos, 0.05); noise(0.35, 0.25, 'lowpass', 1200, 180, pos); },
  bigPop(pos) { noise(0.09, 1, 'highpass', 500, 3500, pos); tone('sine', 1150, 150, 0.14, 0.65, pos); tone('square', 2600, 900, 0.05, 0.12, pos); noise(0.5, 0.3, 'highpass', 5000, 9000, pos, 0.06); },
  blub(pos) { const f = 85 + Math.random() * 90; tone('sine', f, f * 2.7, 0.14, 0.3, pos); },
  error(pos) { tone('square', 880, 880, 0.12, 0.2, pos); tone('square', 660, 660, 0.25, 0.2, pos, 0.14); },
  yeet(pos) { noise(0.7, 0.5, 'bandpass', 400, 3000, pos, 0, 1.5); tone('sine', 300, 1400, 0.6, 0.15, pos); },
  choir(pos) { for (const [f, d] of [[523, 0], [659, 0.05], [784, 0.1], [1046, 0.15]]) tone('sine', f, f * 1.01, 2.2, 0.12, pos, d); },
  // wrecking ball: a struck steel ball rings with a few out-of-tune partials (k = how hard)
  clang(pos, k = 1) {
    for (const [f, d, v] of [[287, 1.1, 0.34], [701, 0.8, 0.24], [1133, 0.55, 0.17], [1789, 0.4, 0.12], [2647, 0.28, 0.08]]) {
      const ff = f * (0.96 + Math.random() * 0.08);
      tone('sine', ff, ff * 0.985, d * (0.5 + k * 0.5), v * k, pos);
    }
    noise(0.05, 0.7 * k, 'highpass', 2500, 7000, pos);
    tone('triangle', 140, 60, 0.12, 0.4 * k, pos);
  },
  // ground slam: a huge clang, the floor booming, rubble raining down after (k = how big: 0 off a hop, 1 from way up)
  slam(pos, k = 0.5) {
    const v = 0.55 + k * 0.45;
    noise(1 + k, v, 'lowpass', 1600, 35, pos); tone('sine', 92 - k * 22, 20, 0.9 + k * 0.9, v, pos); tone('square', 58, 26, 0.3 + k * 0.3, 0.3 * v, pos);
    sfx.clang(pos, 0.7 + k * 0.3);
    for (let i = 0; i < 3 + k * 6; i++) noise(0.1 + Math.random() * 0.08, 0.45, 'bandpass', 700 + Math.random() * 1600, 260, pos, 0.08 + i * 0.07 + Math.random() * 0.05, 1.4);
  },
  chain(pos) { for (let i = 0; i < 7; i++) tone('triangle', 1900 + Math.random() * 2200, 1400, 0.05, 0.11, pos, i * 0.028); noise(0.22, 0.22, 'highpass', 3000, 5200, pos); },
  wreck(pos) { sfx.clang(pos, 0.9); tone('sawtooth', 70, 380, 0.7, 0.14, pos, 0.05); noise(0.35, 0.5, 'lowpass', 900, 100, pos); },
  tbag(pos) { for (let i = 0; i < 3; i++) tone('sawtooth', 120 - i * 25, 40, 0.18, 0.3, pos, i * 0.1); },
  // scales of justice: the gavel lands with the stamp (0.1 s in); n bangs for a one-shot
  gavel(pos, n = 1) {
    for (let i = 0; i < n; i++) {
      const d = 0.1 + i * 0.22;
      noise(0.07, 1, 'bandpass', 1700, 700, pos, d, 1.6); tone('sine', 190, 60, 0.16, 0.8, pos, d);
      tone('square', 520, 260, 0.03, 0.15, pos, d); noise(0.25, 0.22, 'lowpass', 900, 200, pos, d + 0.04); // wood knock + the courtroom
    }
  },
  guilty(pos, big) { for (const [f, d, len] of [[196, 0, 0.16], [185, 0.2, 0.16], [147, 0.4, big ? 1.1 : 0.6]]) { tone('sawtooth', f, f * 0.99, len, 0.09, pos, d + 0.15); tone('square', f / 2, f / 2, len, 0.06, pos, d + 0.15); } }, // dun dun DUNNN
  acquit(pos) { tone('sine', 660, 660, 0.18, 0.16, pos, 0.12); tone('sine', 990, 990, 0.35, 0.14, pos, 0.24); tone('triangle', 1320, 1320, 0.4, 0.06, pos, 0.24); },
  chains(pos) { for (let i = 0; i < 6; i++) { const f = 2400 + Math.random() * 2600; tone('square', f, f * 0.9, 0.025, 0.035, pos, i * 0.035 + Math.random() * 0.02); } },
  // shredder: teeth chewing, a wet spit out of the chute, the overheat hiss, and other people's suction (k = spin)
  shred(pos) { noise(0.13, 0.75, 'bandpass', 1700, 450, pos, 0, 1.4); tone('square', 95, 55, 0.13, 0.22, pos); noise(0.05, 0.45, 'highpass', 3500, 6000, pos, 0.06); },
  spit(pos) { noise(0.18, 0.8, 'lowpass', 1500, 180, pos); tone('sine', 300, 70, 0.17, 0.4, pos); },
  overheat(pos) { noise(1.0, 0.35, 'highpass', 5200, 2400, pos); tone('square', 1300, 1300, 0.07, 0.14, pos); tone('square', 1300, 1300, 0.07, 0.14, pos, 0.13); },
  startup(pos) { for (let i = 0; i < 3; i++) noise(0.06, 0.55, 'lowpass', 1000, 180, pos, i * 0.075); tone('sawtooth', 45, 150, 0.55, 0.16, pos, 0.2); tone('square', 90, 380, 0.5, 0.05, pos, 0.22); }, // sputter sputter VRRRM
  suck(pos, k = 1) { noise(0.34, 0.2 + 0.25 * k, 'bandpass', 450 + 1000 * k, 300 + 700 * k, pos, 0, 1.1); tone('sawtooth', 70 + 170 * k, 76 + 180 * k, 0.32, 0.04 + 0.05 * k, pos); },
  // modes: zombie groans, getting infected, climbing / falling down the gun game ladder
  groan(pos) { const f = 80 + Math.random() * 45; tone('sawtooth', f, f * 0.7, 1.1, 0.2, pos); tone('sawtooth', f * 1.51, f * 1.02, 1.0, 0.09, pos, 0.06); noise(0.9, 0.22, 'bandpass', 520, 240, pos, 0, 3); },
  infected() { tone('sawtooth', 110, 52, 1.5, 0.3); tone('sawtooth', 117, 55, 1.5, 0.25); tone('square', 233, 110, 1.2, 0.07, null, 0.05); noise(1.3, 0.45, 'lowpass', 900, 50); },
  rankUp() { for (const [f, d] of [[523, 0], [659, 0.06], [784, 0.12], [1046, 0.18]]) tone('square', f, f, 0.09, 0.11, null, d); },
  sad() { for (const [f, d, l] of [[311, 0, 0.28], [294, 0.3, 0.28], [277, 0.6, 0.28], [262, 0.9, 0.9]]) tone('sawtooth', f, f * 0.97, l, 0.16, null, d); },
};
// katana parry: a struck blade. a free metal bar rings at 1 : 2.76 : 5.40 : 8.93 (not harmonic, that's what makes it
// sound like steel), over a scraping hiss, with a hard click on top and a detuned pair for the shimmer.
// perfect parries ring higher and longer, with a fifth and a low thump under it.
sfx.parry = (pos, perfect) => {
  const f = perfect ? 1480 : 1250, L = perfect ? 1.4 : 1;
  noise(0.035, 0.75, 'highpass', 5000, 9000, pos); // contact
  noise(0.42 * L, 0.42, 'bandpass', 8500, 3200, pos, 0.004, 2.5); // shhhing
  for (const [k, v, d] of [[1, 0.34, 1.1], [2.76, 0.22, 0.75], [5.4, 0.13, 0.45], [8.93, 0.07, 0.25]]) tone('sine', f * k, f * k * 0.996, d * L, v, pos);
  tone('sine', f * 1.006, f * 1.002, 0.9 * L, 0.16, pos); // beats against the fundamental
  if (perfect) { tone('sine', f * 1.5, f * 1.505, 1.4, 0.12, pos, 0.03); tone('sine', 150, 45, 0.2, 0.4, pos, 0.01); noise(0.12, 0.3, 'lowpass', 900, 120, pos, 0.01); }
};
// a small tick for the 2nd, 3rd... thing parried in one window (a minigun stream shouldn't SHING ten times)
sfx.tink = (pos) => { const f = 3000 + Math.random() * 600; tone('sine', f, f * 0.97, 0.12, 0.13, pos); noise(0.025, 0.45, 'highpass', 6000, 9000, pos); };

// ------------------------------------------------------------ no-scope hype: airhorn, ding, fireworks
let hornCurve = null;
// one brassy blast: detuned saws through a fuzz, with the little pitch scoop at the start that makes it a horn
function horn(f, at, dur, v) {
  if (!ac) return;
  const t = ac.currentTime + at;
  if (!hornCurve) { hornCurve = new Float32Array(256); for (let i = 0; i < 256; i++) hornCurve[i] = Math.tanh((i / 128 - 1) * 4); }
  const sh = ac.createWaveShaper(); sh.curve = hornCurve;
  const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 3200; lp.Q.value = 3;
  const g = ac.createGain();
  g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + 0.02);
  g.gain.setValueAtTime(v, t + Math.max(0.03, dur - 0.05)); g.gain.exponentialRampToValueAtTime(0.001, t + dur);
  sh.connect(lp); lp.connect(g); g.connect(master);
  for (const [type, m, det] of [['sawtooth', 1, -9], ['sawtooth', 1, 8], ['square', 1.5, 0], ['sawtooth', 2, 4]]) {
    const o = ac.createOscillator(); o.type = type; o.detune.value = det;
    o.frequency.setValueAtTime(f * m * 0.8, t); o.frequency.exponentialRampToValueAtTime(f * m, t + 0.045);
    const og = ac.createGain(); og.gain.value = 0.3;
    o.connect(og); og.connect(sh); o.start(t); o.stop(t + dur + 0.05);
  }
}
// fireworks are far away but loud: keep the direction (panning), fall off gently, and arrive late like real sound
function far(pos) {
  if (!pos) return [null, 0];
  const dx = pos[0] - L.pos[0], dy = pos[1] - L.pos[1], dz = pos[2] - L.pos[2], d = Math.hypot(dx, dy, dz), e = 6 + d * 0.2;
  const k = d > e ? e / d : 1;
  return [[L.pos[0] + dx * k, L.pos[1] + dy * k, L.pos[2] + dz * k], Math.min(0.6, d / 343)];
}
Object.assign(sfx, {
  noscope() { for (const [f, d] of [[1046, 0], [1568, 0.06], [2093, 0.12]]) tone('square', f, f, d ? 0.09 : 0.06, 0.12, null, d); noise(0.3, 0.3, 'bandpass', 500, 5000, null, 0, 2); },
  // BWAAA BWA BWA BWAAAAAA (short: BWA BWAAA)
  airhorn(short) { for (const [at, dur] of short ? [[0, 0.16], [0.22, 0.45]] : [[0, 0.34], [0.42, 0.12], [0.6, 0.12], [0.78, 0.9]]) horn(415, at, dur, short ? 0.2 : 0.28); },
  fwWhistle(pos, dur = 1) {
    if (!ac) return;
    const [q, dl] = far(pos), t = ac.currentTime + dl;
    const o = ac.createOscillator(); o.type = 'sine';
    o.frequency.setValueAtTime(900, t); o.frequency.exponentialRampToValueAtTime(2900, t + dur);
    const lfo = ac.createOscillator(); lfo.frequency.value = 22;
    const lg = ac.createGain(); lg.gain.value = 70; lfo.connect(lg); lg.connect(o.frequency);
    const g = ac.createGain();
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.14, t + 0.08);
    g.gain.setValueAtTime(0.14, t + dur * 0.85); g.gain.exponentialRampToValueAtTime(0.001, t + dur);
    o.connect(g); g.connect(dest(q));
    o.start(t); lfo.start(t); o.stop(t + dur + 0.05); lfo.stop(t + dur + 0.05);
    noise(dur, 0.1, 'bandpass', 2500, 5000, q, dl, 2);
  },
  fwBang(pos) { const [q, dl] = far(pos); noise(0.06, 1, 'highpass', 1500, 5000, q, dl); noise(1.3, 1, 'lowpass', 2400, 60, q, dl); tone('sine', 110, 28, 0.7, 0.9, q, dl); },
  fwCrackle(pos) { const [q, dl] = far(pos); for (let i = 0; i < 22; i++) noise(0.02 + Math.random() * 0.03, 0.25 + Math.random() * 0.35, 'highpass', 2500 + Math.random() * 3000, 6000, q, dl + 0.35 + Math.random() * 1.1); },
});

const LOOPDEF = {
  fire: { type: 'lowpass', f: 900, q: 0.7, vol: 0.55 },
  inhale: { type: 'highpass', f: 2600, q: 0.7, vol: 0.14 },
  blower: { type: 'bandpass', f: 500, q: 0.6, vol: 0.5, osc: ['sawtooth', 68, 0.07] },
  soapy: { type: 'lowpass', f: 300, q: 3, vol: 0.32, osc: ['sine', 52, 0.1] }, // inside a soap bubble: low underwater rumble
  spin: { type: 'bandpass', f: 1200, q: 2, vol: 0.25, osc: ['sawtooth', 110, 0.08] },
  roll: { type: 'lowpass', f: 240, q: 1.2, vol: 0.55, osc: ['sawtooth', 34, 0.06] }, // wrecking ball rumbling along the floor
};

// a tone that swells up instead of dying away (the whine before a blood cross bursts)
function bcSwell(type, f0, f1, dur, v, pos) {
  if (!ac) return;
  const t = ac.currentTime;
  const o = ac.createOscillator();
  o.type = type;
  o.frequency.setValueAtTime(f0, t);
  o.frequency.exponentialRampToValueAtTime(Math.max(1, f1), t + dur);
  const g = ac.createGain();
  g.gain.setValueAtTime(0.0005, t);
  g.gain.exponentialRampToValueAtTime(v, t + dur * 0.95);
  g.gain.linearRampToValueAtTime(0.0001, t + dur + 0.05);
  o.connect(g); g.connect(dest(pos));
  o.start(t); o.stop(t + dur + 0.08);
}
// Blood Cross
Object.assign(sfx, {
  bcBeat(pos) { // a wet heartbeat, lub-dub: you just paid 12 HP
    tone('sine', 95, 36, 0.16, 0.9, pos); noise(0.1, 0.5, 'lowpass', 500, 90, pos);
    tone('sine', 80, 32, 0.15, 0.6, pos, 0.17); noise(0.13, 0.4, 'bandpass', 700, 160, pos, 0.16, 2);
  },
  bcStick(pos) { noise(0.1, 0.6, 'bandpass', 1400, 300, pos, 0, 1.5); tone('sine', 380, 110, 0.09, 0.35, pos); },
  bcWhine(pos, dur = 0.6) { bcSwell('sawtooth', 170, 1500, dur, 0.12, pos); bcSwell('sine', 340, 2600, dur, 0.1, pos); },
  bcErupt(pos) { noise(0.22, 0.8, 'bandpass', 2400, 400, pos, 0, 0.9); tone('sawtooth', 140, 45, 0.2, 0.35, pos); tone('square', 900, 1800, 0.05, 0.08, pos); },
  bcBoom(pos) { // a splattery boom: the bang, then the wet bits landing
    noise(0.9, 1, 'lowpass', 1600, 60, pos); tone('sine', 120, 30, 0.8, 0.9, pos);
    for (let i = 0; i < 7; i++) noise(0.06 + Math.random() * 0.06, 0.45, 'bandpass', 900 + Math.random() * 1600, 200, pos, 0.05 + i * 0.045 + Math.random() * 0.03, 1.8);
  },
  bcFizzle(pos) { noise(0.35, 0.35, 'highpass', 3500, 6500, pos); tone('sine', 300, 120, 0.12, 0.1, pos, 0.2); },
  bcRefund() { tone('sine', 220, 660, 0.22, 0.25); tone('triangle', 440, 1320, 0.25, 0.15, null, 0.06); },
});

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

// a loop whose loudness follows something (0..1), e.g. the wrecking ball's rumble follows how fast it rolls
export function loopLevel(name, k) {
  if (!ac) return;
  const was = !!(loops[name] && loops[name].on);
  if (!(k > 0.02)) { if (was) loopSfx(name, false); return; }
  loopSfx(name, true);
  const l = loops[name];
  if (!was || Math.abs((l.k || 0) - k) > 0.03) { l.k = k; l.g.gain.setTargetAtTime(l.def.vol * Math.min(1, k), ac.currentTime, 0.06); }
}

export function stopLoops() { for (const k in loops) loopSfx(k, false); }

// shredder motor: a whine that climbs as the teeth spin up (k 0..1). it sits in loops so stopLoops() shuts it up too
export function shredMotor(k) {
  if (!ac) return;
  let l = loops.shredder;
  if (!l) {
    if (k <= 0.01) return;
    const g = ac.createGain(); g.gain.value = 0; g.connect(master);
    const s = ac.createBufferSource(); s.buffer = nbuf; s.loop = true;
    const f = ac.createBiquadFilter(); f.type = 'bandpass'; f.Q.value = 1.3; f.frequency.value = 300;
    s.connect(f); f.connect(g); s.start();
    const og = ac.createGain(); og.gain.value = 0.22; og.connect(g);
    const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = 50; o.connect(og); o.start();
    const o2 = ac.createOscillator(); o2.type = 'square'; o2.frequency.value = 100; o2.connect(og); o2.start();
    l = loops.shredder = { g, on: false, def: { vol: 0.45 }, f, o, o2 };
  }
  const on = k > 0.01, t = ac.currentTime;
  l.o.frequency.setTargetAtTime(48 + k * 230, t, 0.06);
  l.o2.frequency.setTargetAtTime(96 + k * 700, t, 0.06);
  l.f.frequency.setTargetAtTime(260 + k * 1900, t, 0.06);
  if (on || l.on) l.g.gain.setTargetAtTime(on ? 0.1 + k * 0.35 : 0, t, 0.05);
  l.on = on;
}

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
// chaos modes: a duck falling out of the sky (a whistle that drops as it comes down), lava hissing, a lava rumble
Object.assign(sfx, {
  whistle(pos, dur = 1.6) { tone('sine', 2300, 520, dur, 0.2, pos); tone('sine', 2330, 535, dur, 0.08, pos); },
  sizzle(pos) { noise(0.5, 0.55, 'highpass', 5200, 1800, pos, 0, 0.8); noise(0.25, 0.4, 'bandpass', 900, 300, pos, 0.02, 3); tone('square', 90, 40, 0.18, 0.12, pos); },
  rumble(pos) { noise(1.6, 0.7, 'lowpass', 260, 40, pos); tone('sawtooth', 55, 30, 1.4, 0.3, pos); for (let i = 0; i < 5; i++) noise(0.12, 0.35, 'highpass', 3000, 1200, pos, 0.2 + i * 0.22, 1); },
  chamber(pos) { tone('square', 1500, 1450, 0.04, 0.2, pos); tone('square', 700, 650, 0.07, 0.2, pos, 0.06); },
});

// ------------------------------------------------------------ new gear sounds
// laser pointer charge: a rising whine (k 0..1) with a wobble on top once it's full. sits in loops (stopLoops shuts it up)
export function laserWhine(k, pos = null) {
  if (!ac) return;
  let l = loops.laser;
  if (!l) {
    if (k <= 0.01) return;
    const g = ac.createGain(); g.gain.value = 0; g.connect(master);
    const o = ac.createOscillator(); o.type = 'sawtooth'; o.frequency.value = 200;
    const o2 = ac.createOscillator(); o2.type = 'sine'; o2.frequency.value = 400;
    const lfo = ac.createOscillator(); lfo.frequency.value = 9; const lg = ac.createGain(); lg.gain.value = 0; lfo.connect(lg); lg.connect(o2.frequency);
    const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.Q.value = 2; bp.frequency.value = 900;
    const og = ac.createGain(); og.gain.value = 0.35;
    o.connect(bp); bp.connect(og); o2.connect(og); og.connect(g);
    o.start(); o2.start(); lfo.start();
    l = loops.laser = { g, on: false, def: { vol: 0.3 }, o, o2, lg, bp };
  }
  const on = k > 0.01, t = ac.currentTime;
  l.o.frequency.setTargetAtTime(140 + k * 520, t, 0.05);
  l.o2.frequency.setTargetAtTime(600 + k * 1900, t, 0.05);
  l.bp.frequency.setTargetAtTime(700 + k * 2600, t, 0.05);
  l.lg.gain.setTargetAtTime(k >= 0.99 ? 120 : 0, t, 0.05);
  if (on || l.on) l.g.gain.setTargetAtTime(on ? 0.05 + k * 0.2 : 0, t, 0.04);
  l.on = on;
}
Object.assign(sfx, {
  // laser: a fat BWAAAM for a full one (k = charge), a pew for a tap
  laserFire(k = 1, pos = null) {
    tone('sawtooth', 1800, 90, 0.25 + k * 0.5, 0.18 + k * 0.12, pos); tone('square', 900, 60, 0.2 + k * 0.4, 0.1, pos);
    noise(0.2 + k * 0.4, 0.3 + k * 0.3, 'bandpass', 3000, 400, pos, 0, 1.5);
    if (k > 0.6) { tone('sine', 70, 40, 0.6, 0.35, pos); noise(0.5, 0.25, 'lowpass', 600, 80, pos, 0.05); }
  },
  laserHum(pos) { tone('sawtooth', 220 + Math.random() * 40, 200, 0.12, 0.05, pos); },
  // instant camera: shutter clack + flash pop, the motor spitting out a print, going through a photo
  shutter(pos = null) { noise(0.03, 0.6, 'highpass', 4000, 3000, pos); tone('square', 1200, 600, 0.03, 0.15, pos, 0.02); noise(0.05, 0.4, 'bandpass', 2000, 900, pos, 0.07, 2); tone('sine', 3200, 3600, 0.25, 0.05, pos, 0.08); },
  printWhirr(pos = null) { for (let i = 0; i < 6; i++) tone('square', 160 + i * 6, 150, 0.09, 0.08, pos, i * 0.08); noise(0.5, 0.15, 'bandpass', 1500, 1200, pos, 0, 4); },
  photoIn(pos = null) { tone('sine', 300, 1400, 0.35, 0.22, pos); tone('triangle', 600, 2600, 0.4, 0.12, pos, 0.05); noise(0.4, 0.3, 'bandpass', 600, 4000, pos, 0, 1.5); },
  photoOut(pos = null) { tone('sine', 1400, 300, 0.35, 0.22, pos); noise(0.3, 0.3, 'bandpass', 4000, 600, pos, 0, 1.5); tone('square', 880, 1320, 0.08, 0.1, pos, 0.3); },
  framePop(pos = null) { noise(0.25, 0.35, 'bandpass', 900, 300, pos, 0, 2); tone('triangle', 500, 900, 0.15, 0.15, pos); },
  // pop quiz: the calculator bonk, a school bell, ticks, a ding for right and a game-show buzzer for wrong
  calcBonk(pos = null) { tone('square', 700, 300, 0.07, 0.2, pos); noise(0.08, 0.4, 'bandpass', 1800, 900, pos, 0, 3); for (let i = 0; i < 3; i++) tone('square', 1800 + i * 300, 1800 + i * 300, 0.03, 0.06, pos, 0.08 + i * 0.05); },
  quizBell(pos = null) { for (let i = 0; i < 10; i++) { tone('triangle', 1250, 1240, 0.06, 0.18, pos, i * 0.055); tone('sine', 2500, 2480, 0.05, 0.06, pos, i * 0.055); } },
  quizTick(hurry) { tone('square', hurry ? 1500 : 1100, hurry ? 1500 : 1100, 0.025, hurry ? 0.12 : 0.07); },
  quizRight(pos = null) { for (const [f, d] of [[784, 0], [988, 0.09], [1175, 0.18], [1568, 0.3]]) tone('triangle', f, f, 0.22, 0.22, pos, d); tone('sine', 3136, 3136, 0.5, 0.05, pos, 0.3); },
  quizWrong(pos = null) { tone('sawtooth', 110, 105, 0.7, 0.3, pos); tone('square', 116, 110, 0.7, 0.2, pos); },
  // goggles: the flip-down clunk + power-up whine, power-down, the flash (pop + capacitor whine) and the ringing after one
  nvOn() { noise(0.05, 0.5, 'lowpass', 800, 300); tone('square', 120, 80, 0.06, 0.2); tone('sine', 2000, 9000, 0.6, 0.05, null, 0.08); },
  nvOff() { tone('sine', 9000, 1500, 0.35, 0.05); noise(0.05, 0.4, 'lowpass', 900, 300, null, 0.05); },
  nvFlash(pos = null) { noise(0.12, 0.9, 'highpass', 2500, 7000, pos); tone('sine', 200, 60, 0.25, 0.3, pos); tone('sine', 3000, 11000, 0.5, 0.06, pos, 0.1); },
  tinnitus(s = 2) { if (!ac) return; const t = ac.currentTime, o = ac.createOscillator(), g = ac.createGain(); o.type = 'sine'; o.frequency.value = 6200; g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.09, t + 0.05); g.gain.exponentialRampToValueAtTime(0.0001, t + Math.max(0.4, s * 1.3)); o.connect(g); g.connect(master); o.start(t); o.stop(t + s * 1.3 + 0.1); },
});

