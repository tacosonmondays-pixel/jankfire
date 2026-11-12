// MECH DROP, the sounds (synthesized like everything else: public/js/audio.js's tone + noise). A falling whistle and
// a huge boom for the drop, heavy servo steps, cannons, a sword whoosh, a shield clang, the jet roar, the eject pop.
import { synth } from './audio.js';

const T = (...a) => synth.tone(...a), N = (...a) => synth.noise(...a);
const rnd = (a, b) => a + Math.random() * (b - a);
function metal(pos, k = 1, base = 1, len = 1) { // a struck plate ringing down
  for (const [f, d, v] of [[160, 1.5, 0.3], [410, 1.0, 0.22], [760, 0.8, 0.16], [1190, 0.6, 0.12], [1850, 0.4, 0.08]]) T('sine', f * base * rnd(0.96, 1.04), f * base * 0.96, d * len * (0.5 + k * 0.5), v * k, pos);
}
export const mechsfx = {
  // the hero clips' own beats (mechlook events, see lookEvent): a pose glint, steam vents, a thruster flare, a part
  // popping, a scrape of sparks. the dust / step / slam beats already have gameplay sounds, so they stay quiet here
  look(fx, pos, k = 1) {
    if (fx === 'glint') { T('sine', 2600, 3400, 0.18, 0.07 * k, pos); T('sine', 3900, 5200, 0.12, 0.04 * k, pos, 0.05); }
    else if (fx === 'vent') N(0.7 * k, 0.35 * k, 'highpass', 5000, 1800, pos, 0, 0.9);
    else if (fx === 'flare') { N(0.4, 0.5 * k, 'bandpass', 400, 1600, pos, 0, 1.2); T('sawtooth', 70, 140, 0.35, 0.1 * k, pos); }
    else if (fx === 'burst') { T('sine', 140, 45, 0.25, 0.4 * k, pos); N(0.12, 0.4 * k, 'lowpass', 1800, 300, pos); }
    else if (fx === 'spark') { metal(pos, 0.4 * k, 2.2, 0.3); N(0.18, 0.5 * k, 'highpass', 4000, 9000, pos); }
    else if (fx === 'pop') { T('square', 500, 120, 0.12, 0.2 * k, pos); N(0.25, 0.5 * k, 'bandpass', 1200, 400, pos); }
  },
  // the call: a radio blip, then the long falling whistle (ms = how long it falls)
  call(pos, ms = 2500) {
    T('square', 880, 880, 0.08, 0.08, pos); T('square', 1320, 1320, 0.08, 0.08, pos, 0.1);
    const s = ms / 1000;
    T('sine', 2600, 300, s, 0.12, pos, 0.15); T('sine', 2610, 310, s, 0.06, pos, 0.15);
    N(s * 0.6, 0.15, 'bandpass', 900, 3000, pos, 0.15 + s * 0.4, 0.8);
  },
  // it hits the floor: a crunching BOOM, a sub drop and plates ringing
  land(pos) {
    T('sine', 90, 22, 1.4, 1, pos); N(1.2, 1, 'lowpass', 1600, 40, pos); N(0.25, 0.8, 'highpass', 1500, 6000, pos);
    T('square', 140, 40, 0.3, 0.3, pos); metal(pos, 0.9, 0.7, 1.4); metal(pos, 0.6, 1.3, 0.8);
  },
  // a footstep: tons of servo and steel (k = how hard)
  step(pos, k = 1, heavy = false) {
    T('sine', (heavy ? 60 : 85) * rnd(0.9, 1.1), 26, 0.36, 0.55 * k, pos); N(0.16, 0.45 * k, 'lowpass', 600, 60, pos);
    T('sawtooth', rnd(240, 300), rnd(420, 520), 0.12, 0.05 * k, pos, 0.02); N(0.05, 0.25 * k, 'bandpass', 2400, 1500, pos, 0.04, 2);
  },
  servo(pos, k = 1) { T('sawtooth', rnd(200, 260), rnd(600, 760), 0.22, 0.07 * k, pos); N(0.18, 0.08 * k, 'bandpass', 2000, 3400, pos, 0, 4); },
  climb(pos) { this.servo(pos, 1.2); metal(pos, 0.5, 1.6, 0.4); T('square', 660, 990, 0.12, 0.08, pos, 0.25); T('square', 990, 1320, 0.12, 0.08, pos, 0.38); },
  hatch(pos) { N(0.4, 0.4, 'highpass', 3000, 900, pos); T('sawtooth', 300, 120, 0.4, 0.08, pos); },
  // twin cannons: a punchy thud + a crack
  gun(pos, k = 1) { T('square', 220 * rnd(0.95, 1.05), 70, 0.09, 0.22 * k, pos); N(0.08, 0.5 * k, 'bandpass', 1800, 600, pos); T('sine', 120, 50, 0.12, 0.3 * k, pos); },
  // the sword: a long airy whoosh that rises, the big third swing lower and longer
  whoosh(pos, big = false) { N(big ? 0.45 : 0.3, big ? 0.7 : 0.5, 'bandpass', big ? 300 : 500, big ? 2600 : 3800, pos, 0, 1.4); T('sawtooth', big ? 120 : 180, big ? 60 : 90, big ? 0.35 : 0.22, 0.05, pos); },
  slash(pos) { N(0.08, 0.9, 'highpass', 2500, 8000, pos); metal(pos, 0.5, 2.2, 0.35); T('square', 900, 300, 0.08, 0.12, pos); },
  // the tower shield takes a hit: a huge CLANG
  clang(pos, k = 1) { N(0.05, 0.9 * k, 'highpass', 2000, 7000, pos); T('sine', 110, 40, 0.4, 0.6 * k, pos); metal(pos, 0.9 * k, 1, 1.2); metal(pos, 0.5 * k, 1.41, 0.7); },
  bash(pos) { this.clang(pos, 1.2); N(0.35, 0.8, 'lowpass', 900, 60, pos); T('sine', 80, 30, 0.4, 0.8, pos); },
  // boosts: the lunge / triple shift kick, the jet roar (a long burn), hover hiss
  boost(pos, k = 1) { N(0.5 * k, 0.8, 'bandpass', 500, 2600, pos, 0, 0.8); T('sawtooth', 90, 45, 0.4, 0.2, pos); T('sine', 400, 1600, 0.25, 0.08, pos); },
  jet(pos, s = 6) { N(s, 0.5, 'bandpass', 900, 500, pos, 0, 0.7); T('sawtooth', 70, 110, s, 0.12, pos); T('sine', 1400, 2400, 0.6, 0.06, pos); N(0.6, 0.9, 'lowpass', 2500, 200, pos); },
  hover(pos) { N(0.25, 0.18, 'bandpass', 1400, 1100, pos, 0, 1.2); },
  swarm(pos) { for (let i = 0; i < 12; i++) { N(0.3, 0.4, 'bandpass', 700, 3400, pos, i * 0.045, 1.4); T('square', 400, 1500, 0.1, 0.04, pos, i * 0.045); } },
  crane(pos) { T('triangle', 1200, 2400, 0.12, 0.1, pos); T('triangle', 1800, 1300, 0.1, 0.08, pos, 0.12); N(0.3, 0.2, 'highpass', 4000, 2000, pos, 0.05); }, // paper flapping + a cheep
  peck(pos) { T('square', 2400, 1800, 0.04, 0.1, pos); N(0.03, 0.4, 'highpass', 5000, 7000, pos); },
  slamUp(pos) { this.boost(pos, 1.2); T('sawtooth', 100, 400, 0.5, 0.1, pos); },
  quake(pos) { this.land(pos); N(0.8, 0.8, 'lowpass', 400, 30, pos, 0.05); },
  stomp(pos) { T('sine', 70, 20, 0.5, 0.9, pos); N(0.3, 0.9, 'lowpass', 900, 50, pos); T('square', 600, 80, 0.15, 0.2, pos, 0.02); N(0.08, 0.5, 'bandpass', 3000, 700, pos, 0.05, 3); }, // a SQUELCH-CRUNCH
  ram(pos, big = false) { metal(pos, big ? 1 : 0.6, 0.9, big ? 1 : 0.6); N(0.2, 0.8, 'lowpass', 1500, 80, pos); T('sine', 100, 40, 0.3, big ? 0.8 : 0.5, pos); },
  mark(pos, n = 1) { T('square', 700 + n * 180, 700 + n * 180, 0.06, 0.12, pos); T('square', 1400 + n * 360, 1400 + n * 360, 0.05, 0.06, pos, 0.07); }, // a punch-clock ding
  clock(pos) { for (let i = 0; i < 3; i++) T('square', 1600, 1600, 0.07, 0.15, pos, i * 0.11); T('sine', 300, 60, 0.8, 0.4, pos, 0.33); N(0.5, 0.5, 'highpass', 3000, 900, pos, 0.33); }, // the end-of-shift bell + a slump
  // EJECT! EJECT!: a klaxon, the canopy pop, the boom
  eject(pos) { for (let i = 0; i < 3; i++) { T('square', 800, 560, 0.12, 0.12, pos, i * 0.14); } N(0.12, 0.8, 'highpass', 2000, 5000, pos, 0.42); T('sine', 300, 1200, 0.2, 0.2, pos, 0.42); },
  boom(pos) { T('sine', 70, 18, 1.6, 1, pos); N(1.6, 1, 'lowpass', 2500, 40, pos); N(0.3, 0.9, 'highpass', 1200, 6000, pos); metal(pos, 1, 0.6, 1.5); for (let i = 0; i < 6; i++) metal(pos, 0.4, rnd(0.8, 2.2), 0.4); },
  denied() { T('square', 180, 120, 0.12, 0.12, null); },
  leave(pos) { N(1.6, 0.5, 'bandpass', 600, 2400, pos, 0, 0.8); T('sawtooth', 60, 180, 1.4, 0.1, pos); },
};
