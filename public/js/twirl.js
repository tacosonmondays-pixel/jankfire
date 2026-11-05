// Revolver twirl: the gun spins round your trigger finger (its own X axis, pivot at the trigger guard), over forward
// and back into the grip. Your viewmodel, other players and replays all use this.
// Every spin starts from wherever the gun is right now (angle and speed) and lands on a whole turn, so cutting one
// short (fanning the hammer mid-twirl) never snaps. Forward = negative angle (the muzzle dips first).
import { WEAPONS } from '/shared/weapons.js';

const PI2 = Math.PI * 2;
export const PIVOT = [0, -0.02, 0.02]; // trigger guard, in gun model space

export function newTwirl() { return { a: 0, v: 0, rest: 0, seg: null, k: 0 }; }
export function resetTwirl(s) { s.a = 0; s.v = 0; s.rest = 0; s.seg = null; s.k = 0; }
export const twirling = (s) => !!s.seg || s.a !== 0 || s.v !== 0;

// spin forward onto the next whole turn at least `min` radians away, in `dur` s, arriving at speed `v1` (rad/s, < 0).
// coast > 0: keep turning at v1 that long afterwards (fanning: the next shot starts the next turn), then wind down.
// coast = 0: it lands in your palm and rocks a little before it settles.
export function spin(s, dur, v1 = 0, min = Math.PI, coast = 0) {
  const n = Math.trunc(s.a / PI2) * PI2; // whole turns look the same: keep the numbers small
  s.a -= n; s.rest -= n;
  s.seg = { a0: s.a, v0: s.v, a1: Math.floor((s.a - min) / PI2) * PI2, v1, t: 0, dur: Math.max(0.02, dur), coast };
}
// wind down from whatever it's doing and catch it
export const settle = (s, dur = 0.3) => spin(s, dur, -8, Math.PI);
// after a shot. tap: one quick cowboy twirl, back in the hand in ~0.25 s (before the next tap is allowed).
// fanned: one whole turn timed to land on the next shot, and it keeps spinning
export function twirlShot(s, fan) {
  const r = WEAPONS.revolver.fanHammer.rate;
  if (fan) spin(s, 1 / r, -PI2 * r, Math.PI, 0.12);
  else spin(s, 0.24, -7, 1.5 * Math.PI);
}

export function stepTwirl(s, dt) {
  const g = s.seg;
  let left = 0; // time left over for the catch spring this frame
  if (g) {
    g.t += dt;
    if (g.t < g.dur) { // cubic hermite: matches angle + speed at both ends
      const D = g.dur, u = g.t / D, u2 = u * u, u3 = u2 * u;
      s.a = (2 * u3 - 3 * u2 + 1) * g.a0 + (u3 - 2 * u2 + u) * D * g.v0 + (3 * u2 - 2 * u3) * g.a1 + (u3 - u2) * D * g.v1;
      s.v = ((6 * u2 - 6 * u) * g.a0 + (3 * u2 - 4 * u + 1) * D * g.v0 + (6 * u - 6 * u2) * g.a1 + (3 * u2 - 2 * u) * D * g.v1) / D;
    } else if (g.coast > 0) {
      s.a = g.a1 + g.v1 * (g.t - g.dur); s.v = g.v1;
      if (g.t >= g.dur + g.coast) settle(s); // nobody kept it going: wind down from here
    } else { s.seg = null; s.a = g.a1; s.v = g.v1; s.rest = g.a1; left = g.t - g.dur; }
  } else left = dt;
  if (!s.seg && left > 0 && (s.a !== 0 || s.v !== 0)) { // caught: a stiff spring rocks it back onto the grip
    const n = Math.min(20, Math.max(1, Math.ceil(left * 240))), h = left / n;
    for (let i = 0; i < n; i++) { s.v += (-900 * (s.a - s.rest) - 36 * s.v) * h; s.a += s.v * h; }
    if (Math.abs(s.a - s.rest) < 0.002 && Math.abs(s.v) < 0.05) { s.a = 0; s.v = 0; s.rest = 0; }
  }
  s.k += ((s.seg || Math.abs(s.v) > 1 ? 1 : 0) - s.k) * Math.min(1, dt * 14); // how far into the twirl pose
  return s.a;
}

// rotate obj by angle a about the trigger guard (obj's own X axis). scale: obj's uniform scale
export function applyTwirl(obj, a, scale = 1) {
  const py = PIVOT[1] * scale, pz = PIVOT[2] * scale, c = Math.cos(a), sn = Math.sin(a);
  obj.rotation.x = a;
  obj.position.set(0, py - (py * c - pz * sn), pz - (py * sn + pz * c));
}
