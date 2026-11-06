// Overdrive Rig killstreak, the sounds (all synthesized, like everything else): a deep servo hum + whine while you're
// in it, footsteps that thud, a huge metal CLANG when a punch lands, rockets, hacks, shields, craters.
import { synth } from './audio.js';

const T = (...a) => synth.tone(...a), N = (...a) => synth.noise(...a);
const rnd = (a, b) => a + Math.random() * (b - a);
// a struck chunk of steel: a few out-of-tune partials ringing down (k = how hard)
function metal(pos, k = 1, base = 1, len = 1) {
  for (const [f, d, v] of [[183, 1.4, 0.3], [437, 1.0, 0.24], [791, 0.8, 0.18], [1219, 0.6, 0.13], [1833, 0.45, 0.09], [2671, 0.3, 0.06]]) {
    const ff = f * base * rnd(0.95, 1.05);
    T('sine', ff, ff * 0.97, d * len * (0.5 + k * 0.5), v * k, pos);
  }
}
export const rigsfx = {
  // powering up: a boom, servos winding up, hydraulics, plates clanking shut
  on(pos) {
    N(0.9, 0.7, 'lowpass', 900, 40, pos); T('sine', 70, 28, 1.1, 0.7, pos);
    T('sawtooth', 60, 520, 0.9, 0.12, pos, 0.05); T('square', 120, 900, 0.8, 0.05, pos, 0.1);
    N(0.5, 0.45, 'highpass', 2500, 6000, pos, 0.35);
    for (let i = 0; i < 5; i++) { metal(pos, 0.35, rnd(0.8, 1.5), 0.3); N(0.05, 0.6, 'bandpass', 1800, 900, pos, 0.25 + i * 0.09, 1.2); }
  },
  // powering down: whine falling, a long hiss, loose plates rattling
  off(pos) {
    T('sawtooth', 480, 50, 1.0, 0.12, pos); N(0.9, 0.4, 'highpass', 4000, 1500, pos, 0.05);
    for (let i = 0; i < 4; i++) N(0.05, 0.45, 'bandpass', 1500, 700, pos, 0.2 + i * 0.12, 1.4);
  },
  // a footstep: tons of steel landing on a floor (k = how hard)
  stomp(pos, k = 1) {
    T('sine', 78 * rnd(0.9, 1.1), 28, 0.32, 0.55 * k, pos); N(0.14, 0.5 * k, 'lowpass', 700, 60, pos);
    N(0.04, 0.3 * k, 'bandpass', 2600, 1600, pos, 0.01, 2); T('square', 160, 90, 0.05, 0.08 * k, pos);
  },
  servo(pos, k = 1) { T('sawtooth', rnd(260, 340), rnd(520, 700), 0.16, 0.06 * k, pos); N(0.12, 0.08 * k, 'bandpass', 2200, 3200, pos, 0, 4); },
  // the rocket punch lets go: thrusters roar, air rips
  release(pos, c = 1) {
    N(0.45, 0.7, 'bandpass', 400, 2400, pos, 0, 0.9); N(0.3, 0.5, 'lowpass', 1500, 120, pos);
    T('sawtooth', 90 + c * 60, 40, 0.35, 0.25, pos); T('sine', 300, 1400, 0.25, 0.08 + c * 0.08, pos);
  },
  // it LANDS. a huge metal CLANG: the hit, the ring, the low thump under it (k = how charged)
  clang(pos, k = 1) {
    N(0.06, 1, 'highpass', 1800, 6000, pos); N(0.25, 0.9, 'lowpass', 2500, 80, pos);
    T('sine', 120, 35, 0.5, 0.9 * Math.max(0.5, k), pos); T('square', 240, 60, 0.12, 0.3, pos);
    metal(pos, 0.8 + k * 0.4, 1, 1.3); metal(pos, 0.5, 1.37, 0.8);
  },
  wall(pos) { N(0.3, 0.9, 'lowpass', 1400, 50, pos); T('sine', 90, 30, 0.45, 0.7, pos); N(0.12, 0.5, 'bandpass', 900, 400, pos, 0.05, 1.5); metal(pos, 0.4, 0.7, 0.5); },
  // a blocked hit: steel deflecting steel
  block(pos) { metal(pos, 0.45, rnd(1.1, 1.6), 0.4); N(0.05, 0.5, 'highpass', 3000, 6000, pos); T('square', 210, 110, 0.06, 0.12, pos); },
  // the hex overshield taking a hit (and breaking)
  shield(pos) { T('square', rnd(1800, 2600), rnd(600, 900), 0.08, 0.06, pos); N(0.08, 0.25, 'highpass', 5000, 9000, pos); T('sine', 900, 1400, 0.1, 0.05, pos); },
  shieldBreak(pos) { for (let i = 0; i < 6; i++) T('sine', rnd(2000, 4500), rnd(800, 1500), 0.3, 0.07, pos, i * 0.02); N(0.5, 0.5, 'highpass', 6000, 2000, pos); T('sawtooth', 600, 60, 0.6, 0.15, pos); },
  missiles(pos) { for (let i = 0; i < 4; i++) { N(0.4, 0.5, 'bandpass', 600, 3000, pos, i * 0.09, 1.2); T('square', 300, 1200, 0.12, 0.06, pos, i * 0.09); } T('square', 140, 90, 0.06, 0.15, pos); },
  boom(pos) { N(0.7, 0.9, 'lowpass', 2000, 60, pos); T('sine', 120, 30, 0.6, 0.6, pos); N(0.2, 0.4, 'bandpass', 3000, 900, pos, 0.02); },
  hack(pos) { for (let i = 0; i < 6; i++) T('square', rnd(900, 2800), rnd(400, 3200), 0.04, 0.07, pos, i * 0.03); T('sine', 1760, 1760, 0.12, 0.08, pos, 0.22); T('sine', 2350, 2350, 0.16, 0.08, pos, 0.3); },
  hacked() { for (let i = 0; i < 10; i++) T('square', rnd(100, 3000), rnd(60, 4000), 0.05, 0.1, null, i * 0.035); N(0.5, 0.35, 'bandpass', 1500, 400, null, 0, 6); T('sawtooth', 880, 110, 0.5, 0.1, null, 0.1); },
  leap(pos, c = 1) { N(0.45, 0.7, 'highpass', 1800, 600, pos); T('sine', 90, 220, 0.25, 0.4, pos); N(0.3, 0.6 * c + 0.2, 'lowpass', 1200, 80, pos); T('sawtooth', 70, 30, 0.3, 0.2, pos); },
  land(pos, k = 1) {
    N(0.8 + k * 0.5, 0.9, 'lowpass', 1300, 35, pos); T('sine', 85 - k * 20, 22, 0.9 + k * 0.6, 0.8, pos); T('square', 60, 26, 0.3, 0.25, pos);
    metal(pos, 0.5 + k * 0.3, 0.6, 0.8);
    for (let i = 0; i < 3 + k * 5; i++) N(0.1, 0.4, 'bandpass', rnd(700, 2200), 260, pos, 0.08 + i * 0.07, 1.4);
  },
  burst(pos) { N(1.2, 1, 'lowpass', 2200, 40, pos); T('sine', 100, 20, 1.2, 0.9, pos); for (let i = 0; i < 10; i++) { metal(pos, 0.3, rnd(0.8, 2.2), 0.3); N(0.06, 0.5, 'bandpass', rnd(1200, 3000), 800, pos, 0.1 + i * 0.09, 1.2); } },
  // a jet burst: a rising roar of noise over a low thump, a crackle on top
  thrust(pos, k = 1) { N(0.5, 0.75 * k, 'bandpass', 400, 2600, pos, 0, 0.8); N(0.35, 0.5 * k, 'lowpass', 900, 120, pos); T('sine', 70, 140, 0.3, 0.35 * k, pos); N(0.2, 0.25 * k, 'highpass', 5000, 8000, pos, 0.04); },
  denied() { T('square', 330, 330, 0.07, 0.1); T('square', 220, 220, 0.12, 0.1, null, 0.08); },
  ready() { T('sine', 1320, 1320, 0.08, 0.07); T('sine', 1980, 1980, 0.14, 0.07, null, 0.07); },
};

// ------------------------------------------------------------ the hum: you're wearing a machine
// a low drone with a tremolo, a servo whine that climbs with speed, and a charge whine that climbs with the punch.
// lives while the rig is on; follows the master volume
let H = null;
function hum() {
  const ac = synth.ac;
  if (H || !ac) return H;
  const out = ac.createGain(); out.gain.value = 0; out.connect(synth.out);
  const lp = ac.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 240; lp.Q.value = 3; lp.connect(out);
  const o1 = ac.createOscillator(); o1.type = 'sawtooth'; o1.frequency.value = 44; o1.connect(lp);
  const o2 = ac.createOscillator(); o2.type = 'square'; o2.frequency.value = 88.6;
  const g2 = ac.createGain(); g2.gain.value = 0.22; o2.connect(g2); g2.connect(lp);
  const lfo = ac.createOscillator(); lfo.frequency.value = 6.5;
  const lg = ac.createGain(); lg.gain.value = 40; lfo.connect(lg); lg.connect(lp.frequency);
  const whine = ac.createGain(); whine.gain.value = 0; whine.connect(synth.out);
  const bp = ac.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 900; bp.Q.value = 7; bp.connect(whine);
  const o3 = ac.createOscillator(); o3.type = 'sawtooth'; o3.frequency.value = 300; o3.connect(bp);
  const chg = ac.createGain(); chg.gain.value = 0; chg.connect(synth.out);
  const o4 = ac.createOscillator(); o4.type = 'triangle'; o4.frequency.value = 380; o4.connect(chg);
  for (const o of [o1, o2, lfo, o3, o4]) o.start();
  H = { ac, out, lp, o1, o3, o4, bp, whine, chg, on: false };
  return H;
}
// k: { on, speed (m/s), motion (0..1 arms moving), charge (0..1, < 0 = not charging), slow (0..1 the overdrive tint) }
export function rigHum(k) {
  const h = hum();
  if (!h) return;
  const t = h.ac.currentTime;
  if (!k.on) { if (h.on) { h.out.gain.setTargetAtTime(0, t, 0.08); h.whine.gain.setTargetAtTime(0, t, 0.05); h.chg.gain.setTargetAtTime(0, t, 0.03); h.on = false; } return; }
  h.on = true;
  const sp = Math.min(1, (k.speed || 0) / 24);
  // fast in overdrive: the drone drops and drags (a bit of slow motion in your ears)
  h.out.gain.setTargetAtTime(0.16 + sp * 0.06, t, 0.1);
  h.o1.frequency.setTargetAtTime(44 - (k.slow || 0) * 10 + sp * 6, t, 0.2);
  h.bp.frequency.setTargetAtTime(700 + sp * 1600 + (k.motion || 0) * 600, t, 0.08);
  h.o3.frequency.setTargetAtTime(220 + sp * 480 + (k.motion || 0) * 200, t, 0.08);
  h.whine.gain.setTargetAtTime(0.015 + sp * 0.05 + (k.motion || 0) * 0.04, t, 0.08);
  const c = k.charge;
  if (c >= 0) { h.o4.frequency.setTargetAtTime(300 + c * c * 1500 + (c >= 1 ? Math.random() * 120 : 0), t, 0.03); h.chg.gain.setTargetAtTime(0.025 + c * 0.06, t, 0.03); }
  else h.chg.gain.setTargetAtTime(0, t, 0.04);
}
