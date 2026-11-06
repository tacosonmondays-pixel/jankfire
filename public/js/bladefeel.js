// Knives + katana, re-felt toward a snappy arena-shooter style: a quick, readable anticipation (cock it, a tiny hang),
// a whip of a cut, a held overshoot with a long smear, then a springy settle. The weapon is the star: tosses and spins
// happen to the knife while the hand stays where it is (the 'toss' channel moves only the weapon, round the grip), the
// fingers let go during a toss and close on the catch ('hp'), and blades sway a little when idle.
// Server timing is untouched: every swing keeps its `hit` and its total length.
//   toss [dx, dy, dz, rx, ry, rz]  the weapon off the hand (wrap space, turning round the grip point)
//   hp [k]                         the hand opens (0 holding .. 1 open)
import * as THREE from 'three';
import { ANIMS } from './anim.js';
import { mixPose, pose as poseHand } from './hands.js';

const PI = Math.PI, PI2 = PI * 2;
const K = (t, p = [0, 0, 0], r = [0, 0, 0], e = 'smooth', s = 1) => ({ t, p, r, e, s });
const T0 = [0, 0, 0, 0, 0, 0];

const FEEL = {
  // forward slash, right to left: cock up and right, a hair of hang, WHIP, overshoot, spring back (hit 0.1, 0.4 s)
  swing_knife: { hit: 0.1, keys: [
    K(0), K(0.05, [0.085, 0.09, 0.05], [0.32, -0.64, -0.64]), K(0.075, [0.095, 0.1, 0.055], [0.37, -0.7, -0.7], 'linear'),
    K(0.12, [-0.15, 0.0, -0.16], [-0.12, 1.0, 0.86], 'snap'), K(0.18, [-0.18, -0.02, -0.14], [-0.18, 1.12, 0.96]),
    K(0.4, [0, 0, 0], [0, 0, 0], 'back'),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.24] },
  swing_knife2: { hit: 0.1, keys: [
    K(0), K(0.05, [-0.11, 0.07, 0.04], [0.26, 0.82, 0.66]), K(0.075, [-0.12, 0.08, 0.045], [0.3, 0.88, 0.72], 'linear'),
    K(0.12, [0.09, 0.0, -0.16], [-0.12, -0.84, -0.8], 'snap'), K(0.18, [0.11, -0.02, -0.14], [-0.18, -0.95, -0.88]),
    K(0.4, [0, 0, 0], [0, 0, 0], 'back'),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.24] },
  swing_knife_cleaver: { hit: 0.14, keys: [ // overhead chop: a big raise, a hang, CHOP, it bites in and stays a beat
    K(0), K(0.08, [0.02, 0.13, 0.08], [1.05, 0.12, 0.12]), K(0.11, [0.02, 0.14, 0.09], [1.12, 0.12, 0.12], 'linear'),
    K(0.16, [-0.03, -0.1, -0.14], [-0.92, 0, -0.05], 'snap'), K(0.27, [-0.03, -0.115, -0.125], [-1.0, 0, -0.05]),
    K(0.46, [0, 0, 0], [0, 0, 0], 'back'),
  ], events: [[0.1, 'whoosh']], trail: [0.1, 0.28] },
  swing_knife_karambit: { hit: 0.1, keys: [ // a hooking rake: wrist cocked back, rip across, the claw flicks round
    K(0), K(0.05, [0.09, 0.06, 0.02], [-0.22, -0.66, -0.98]), K(0.075, [0.1, 0.065, 0.025], [-0.25, -0.7, -1.04], 'linear'),
    K(0.12, [-0.16, 0.01, -0.14], [0.32, 0.95, 0.95], 'snap'), K(0.18, [-0.18, -0.01, -0.12], [0.38, 1.06, 1.08]),
    K(0.4, [0, 0, 0], [0, 0, 0], 'back'),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.24] },
  swing_knife_karambit2: { hit: 0.1, keys: [
    K(0), K(0.05, [-0.11, 0.05, 0.02], [-0.22, 0.76, 0.88]), K(0.075, [-0.12, 0.055, 0.025], [-0.25, 0.8, 0.94], 'linear'),
    K(0.12, [0.09, 0.01, -0.14], [0.32, -0.85, -0.95], 'snap'), K(0.18, [0.1, -0.01, -0.12], [0.38, -0.96, -1.08]),
    K(0.4, [0, 0, 0], [0, 0, 0], 'back'),
  ], events: [[0.07, 'whoosh']], trail: [0.07, 0.24] },
  // draw: it comes up spinning end over end in your fingers and slaps into the grip (the hand stays put)
  draw_knife: { keys: [K(0, [0.01, -0.16, 0.02], [-0.5, 0, 0]), K(0.2, [0, 0.02, 0], [0.1, 0, 0], 'snap'), K(0.3, [0, -0.006, 0], [-0.04, 0, 0]), K(0.4)],
    ch: { toss: [[0, 0, 0.02, 0, -PI2, 0, 0], [0.24, 0, 0, 0, 0, 0, 0]], hp: [[0, 0.6], [0.2, 0.6], [0.26, 0]] }, events: [[0.1, 'whoosh'], [0.25, 'shing']] },
  // classic knife: side-on, a dip, flip it up end over end and catch it, roll to the flipside, a twirl, back
  inspect_knife: { keys: [
    K(0), K(0.25, [-0.07, 0.06, -0.02], [0.1, 1.45, 0.08]), K(1.75, [-0.07, 0.065, -0.02], [0.12, 1.47, 0.08]), K(2.1), // fully side-on: it flips across the screen, not at you
  ], ch: {
    toss: [[0.25, ...T0], [0.33, 0, -0.012, 0, 0, 0, 0], [0.58, 0, 0.12, -0.05, PI, 0, 0], [0.8, 0, 0, 0, PI2, 0, 0], // flip up, caught
      [0.86, 0, -0.008, 0, PI2, 0, 0], [0.96, 0, 0, 0, PI2, 0, 0], [1.15, 0, 0, 0, PI2, 0, PI], [1.4, 0, 0, 0, PI2, 0, PI], // roll to the flipside
      [1.75, 0, 0, 0, PI2, 0, PI2]], // and round
    hp: [[0.32, 0], [0.38, 0.85], [0.74, 0.85], [0.8, 0]],
  }, events: [[0.38, 'whoosh'], [0.8, 'thwack'], [1.15, 'ting'], [1.5, 'whoosh']] },
  // kitchen knife: turn it over, then a flat spin toss off the palm, caught by the handle
  inspect_knife_kitchen: { keys: [
    K(0), K(0.3, [-0.07, 0.06, 0.01], [0.15, 0.7, 0.2]), K(1.0, [-0.07, 0.06, 0.01], [0.15, 0.7, 0.2 + PI]), K(1.3, [-0.07, 0.06, 0.01], [0.15, 0.7, 0.2 + PI2]),
    K(1.85, [-0.07, 0.065, 0.01], [0.15, 0.7, 0.2 + PI2]), K(2.1, [0, 0, 0], [0, 0, PI2]),
  ], ch: { toss: [[1.3, ...T0], [1.36, 0, -0.01, 0, 0, 0, 0], [1.56, 0, 0.12, -0.04, 0, PI, 0], [1.78, 0, 0, 0, 0, PI2, 0]], hp: [[1.35, 0], [1.4, 0.9], [1.72, 0.9], [1.78, 0]] },
  events: [[0.65, 'ting'], [1.4, 'whoosh'], [1.78, 'thwack']] },
  // bowie: up from the hip with a barrel roll toss and catch (the hand waits for it)
  draw_knife_bowie: { keys: [K(0, [0, -0.2, 0.02], [-0.5, 0, 0]), K(0.16, [0, 0.02, 0], [0.08, 0, 0], 'snap'), K(0.5)],
    ch: { toss: [[0, 0, 0.0, 0, 0, 0, 0], [0.14, 0, 0, 0, 0, 0, 0], [0.26, 0, 0.12, -0.02, PI, 0, PI], [0.38, 0, 0, 0, PI2, 0, PI2]], hp: [[0.13, 0], [0.17, 0.9], [0.34, 0.9], [0.38, 0]] },
    events: [[0.17, 'whoosh'], [0.38, 'thwack']] },
  inspect_knife_bowie: { keys: [
    K(0), K(0.25, [-0.06, 0.04, -0.02], [0.15, 1.4, 0.1]), K(0.9, [-0.06, 0.045, -0.02], [0.15, 1.42, 0.1]),
    K(1.15, [-0.08, 0.1, 0], [1.25, 0.5, 0.1]), K(1.6, [-0.08, 0.1, 0], [1.2, 0.95, 0.12]), K(2.0),
  ], ch: { toss: [[0.3, ...T0], [0.36, 0, -0.012, 0, 0, 0, 0], [0.6, 0, 0.13, -0.05, PI, 0, PI], [0.85, 0, 0, 0, PI2, 0, PI2]], hp: [[0.35, 0], [0.4, 0.9], [0.8, 0.9], [0.85, 0]] },
  events: [[0.4, 'whoosh'], [0.85, 'thwack'], [1.3, 'ting']] },
  // cleaver: flips up out of the hand on the draw and lands in it
  draw_knife_cleaver: { keys: [K(0, [0, -0.2, 0], [-0.6, 0.6, 0]), K(0.2, [-0.04, 0.03, -0.03], [0.05, 1.3, 0], 'snap'), K(0.42, [-0.04, 0.03, -0.03], [0.05, 1.3, 0]), K(0.48, [0, 0, 0], [0, 0, 0], 'back')], // side-on for the flip
    ch: { toss: [[0, 0, 0, 0, 0, 0, 0], [0.18, 0, 0, 0, 0, 0, 0], [0.3, 0, 0.08, -0.03, -PI, 0, 0], [0.42, 0, 0, 0, -PI2, 0, 0]], hp: [[0.17, 0], [0.21, 0.8], [0.38, 0.8], [0.42, 0]] },
    events: [[0.2, 'whoosh'], [0.42, 'clunk']] },
};
for (const a of Object.values(FEEL)) a.dur = a.keys[a.keys.length - 1].t;
Object.assign(ANIMS, FEEL);

// ------------------------------------------------------------ per frame (weapons.js): the toss + the hand letting go
const qA = new THREE.Quaternion(), eA = new THREE.Euler(), vP = new THREE.Vector3(), vR = new THREE.Vector3();
export function bladeStep(m, an, at, sampleCh) {
  const t = an && sampleCh(an, 'toss', at), hp = an && sampleCh(an, 'hp', at), g = m.g;
  if (t) {
    const pv = m.pivot || (m.hand ? m.hand.position : vP.set(0, 0, 0)); // round the grip point (wrap space)
    eA.set(t[3], t[4], t[5]); g.quaternion.setFromEuler(eA);
    vR.copy(pv).applyQuaternion(g.quaternion);
    g.position.set(pv.x + t[0] - vR.x, pv.y + t[1] - vR.y, pv.z + t[2] - vR.z);
    m.tossed = true;
  } else if (m.tossed) { g.position.set(0, 0, 0); g.rotation.set(0, 0, 0); m.tossed = false; }
  const h = m.hand && m.hand.userData.hand;
  if (h) {
    const base = (m.hand.userData.handCfg && m.hand.userData.handCfg.pose) || 'grip', k = hp ? hp[0] : 0;
    if (k > 0.001 || m.handOpen) { poseHand(m.hand, k > 0.001 ? mixPose(base, 'open', k) : base); m.handOpen = k > 0.001; }
  }
}

// a slow idle sway for the blades (figure of eight, the tip leads): [px, py, pz, rx, ry, rz]
export function bladeIdle(id, now, k) {
  if (id !== 'katana' && id !== 'knife') return null;
  const t = now * 0.001, a = id === 'katana' ? 1 : 0.7;
  return [Math.sin(t * 0.9) * 0.004 * a * k, Math.sin(t * 1.8) * 0.003 * a * k, 0, Math.sin(t * 1.8 + 0.6) * 0.022 * a * k, Math.sin(t * 0.9) * 0.018 * a * k, Math.sin(t * 0.9 + 1.2) * 0.03 * a * k];
}
export const TRAIL_LIFE = { katana: 180, knife: 160 }; // a longer smear for the blades (ms)
