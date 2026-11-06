// Butterfly knife (balisong) flips, done the way the real thing moves. Whatever handle is in your hand stays put; the
// blade and the other handle swing round the pivot pins. The 'bal' channel is world angles about the pivot, in the hand's
// frame: [blade, safe handle, bite handle, lift]. 0 = pointing where it does open in the hand (blade forward, handles back
// in the palm); a handle's own angle on the blade is its world angle minus the blade's (0 open, PI shut over the blade).
// The whole knife turns round the pivot by the blade angle, so a held handle (its world angle not changing) never moves
// while the blade swings, and lift tosses the whole thing off the hand for an aerial. Every key ends on whole turns.
import { ANIMS } from './anim.js';

const PI = Math.PI, PI2 = PI * 2;
const K = (t, p = [0, 0, 0], r = [0, 0, 0], e = 'smooth', s = 1) => ({ t, p, r, e, s });
const SIDE = 1.15; // wrist turned so the pivot axis points at you: the flips go round in front of your eyes
const BAL = {
  // closed in the fist on the way up; thumb the latch, the bite handle swings out over the top, then a flick of the wrist
  // swings the blade down and round to the front while that handle comes back over into the palm: snap, open
  draw_knife_butterfly: { keys: [
    K(0, [0, -0.17, 0.02], [-0.5, 0.3, 0]), K(0.14, [-0.05, 0.06, 0], [0.05, 0.95, 0.1], 'snap'),
    K(0.26, [-0.05, 0.075, 0], [0.28, 0.95, 0.12]), // flick up...
    K(0.4, [-0.05, 0.05, 0], [-0.08, 0.95, 0.08], 'snap'), // ...and down: the blade comes round
    K(0.5, [-0.025, 0.02, 0], [0.06, 0.6, 0.06]), K(0.66),
  ], ch: { bal: [[0, PI, 0, 0, 0], [0.12, PI, 0, 0, 0], [0.24, PI, 0, PI, 0], [0.42, PI2, 0, PI2, 0]] },
  events: [[0.12, 'latch'], [0.24, 'balClack'], [0.42, 'balClack'], [0.52, 'latch']] },
  // side-on so you can see it: reverse basic shut, basic open, switch grip and fan it the other way, then an aerial
  // (it leaves your hand, does a full turn round the pivot, and you catch it), latch it, done
  inspect_knife_butterfly: { keys: [
    K(0), K(0.25, [-0.09, 0.11, 0], [0.1, SIDE, 0.1]),
    K(0.36, [-0.09, 0.12, 0], [0.24, SIDE, 0.1]), K(0.5, [-0.09, 0.11, 0], [0.06, SIDE, 0.1], 'snap'), // shut
    K(0.68, [-0.09, 0.12, 0], [0.22, SIDE, 0.1]), K(0.82, [-0.09, 0.11, 0], [0.06, SIDE, 0.1], 'snap'), // open
    K(1.0, [-0.09, 0.12, 0], [0.22, SIDE, 0.12]), K(1.15, [-0.09, 0.11, 0], [0.08, SIDE, 0.12], 'snap'), // fan: shut
    K(1.27, [-0.09, 0.12, 0], [0.22, SIDE, 0.12]), K(1.4, [-0.09, 0.11, 0], [0.06, SIDE, 0.1], 'snap'), // fan: open
    K(1.55, [-0.09, 0.095, 0], [0.0, SIDE, 0.1]), K(1.63, [-0.09, 0.135, 0], [0.3, SIDE, 0.1], 'snap'), // toss
    K(1.92, [-0.09, 0.085, 0], [0.02, SIDE, 0.1]), K(2.0, [-0.09, 0.105, 0], [0.12, SIDE, 0.1], 'back'), // catch
    K(2.25, [-0.09, 0.11, 0], [0.1, SIDE, 0.1]), K(2.6),
  ], ch: { bal: [
    [0.28, 0, 0, 0, 0],
    [0.42, -PI, 0, -PI, 0], [0.52, -PI, 0, -PI2, 0], // reverse basic: blade + bite handle back over the top, bite handle into the palm
    [0.6, -PI, 0, -PI2, 0], [0.7, -PI, 0, -PI * 3, 0], [0.82, -PI2, 0, -PI * 4, 0], // basic: bite handle out, blade round, open
    [0.95, -PI2, 0, -PI * 4, 0], [1.05, -PI, PI, -PI * 4, 0], [1.15, -PI, PI2, -PI * 4, 0], // grip the bite handle now: the safe one fans shut
    [1.2, -PI, PI2, -PI * 4, 0], [1.3, -PI, PI * 3, -PI * 4, 0], [1.4, 0, PI * 4, -PI * 4, 0], // and open again
    [1.6, 0, PI * 4, -PI * 4, 0], [1.66, 0.2, PI * 4 + 0.2, -PI * 4 + 0.2, 0.09], // aerial: off the hand...
    [1.82, PI + 0.6, PI * 5 + 0.6, -PI * 3 + 0.6, 0.17], [1.96, PI2, PI * 6, -PI2, 0], // ...one whole turn, caught
  ] }, events: [[0.42, 'balClack'], [0.52, 'balClack'], [0.7, 'balClack'], [0.82, 'balClack'], [1.05, 'balClack'], [1.15, 'balClack'], [1.3, 'balClack'], [1.4, 'balClack'], [1.62, 'whoosh'], [1.96, 'thwack'], [2.2, 'latch']] },
};
for (const a of Object.values(BAL)) a.dur = a.keys[a.keys.length - 1].t;
Object.assign(ANIMS, BAL);

// every frame (weapons.js): the knife round its pivot + each handle on the blade
export function balisongStep(m, an, at, sampleCh) {
  const ud = m.g.userData, h = ud.handles;
  const v = (an && sampleCh(an, 'bal', at)) || [0, 0, 0, 0];
  const [ab, a1, a2, lift] = v;
  h[0].rotation.x = a1 - ab; h[1].rotation.x = a2 - ab;
  const pz = h[0].position.z * m.cfg.s; // the pivot, in wrap space
  m.g.rotation.x = ab;
  m.g.position.set(0, Math.sin(ab) * pz + lift, pz - Math.cos(ab) * pz);
}
