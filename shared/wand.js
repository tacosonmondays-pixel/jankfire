// Bubble Wand: where a soap bubble is t seconds after it was blown. It's a formula, not a simulation, so the server
// (which does the hits) and every client (which draws it) put it in the same place without syncing anything.
// It slows from the blow speed to a lazy drift the same way it was going, floats up a little,
// and bobs + sways out of step with the bubbles next to it (seed = projectile id).
import { WEAPONS } from './weapons.js';

export function soapAt(p0, v0, seed, t, out = [0, 0, 0]) {
  const w = WEAPONS.soap;
  const hl = Math.hypot(v0[0], v0[2]), dx = hl > 1e-6 ? v0[0] / hl : 0, dz = hl > 1e-6 ? v0[2] / hl : 0;
  const D = [dx * w.drift, w.lift, dz * w.drift]; // what it ends up doing
  const e = (1 - Math.exp(-w.drag * t)) / w.drag; // how much of the blow speed is used up
  const ph = seed * 2.39996; // golden angle: neighbours never bob together
  const bob = w.bob * (Math.sin(t * 4.2 + ph) - Math.sin(ph));
  const sway = w.sway * (Math.sin(t * 2.6 + ph * 1.7) - Math.sin(ph * 1.7)); // sideways to the way it's going
  out[0] = p0[0] + D[0] * t + (v0[0] - D[0]) * e - dz * sway;
  out[1] = p0[1] + D[1] * t + (v0[1] - D[1]) * e + bob;
  out[2] = p0[2] + D[2] * t + (v0[2] - D[2]) * e + dx * sway;
  return out;
}

// someone sealed in a giant bubble (y = its middle above their feet, r = radius) gets hit on the bubble, not their body:
// one box round it. the server sweeps projectiles against it, clients ray-test it (k = how much bigger far-away people are drawn)
export const TRAP = { y: 1.14, r: 1.38, box: 1.1 };
export function trapBoxes(pos, k = 1) {
  const h = TRAP.box * k, c = [pos[0], pos[1] + TRAP.y * k, pos[2]];
  return [{ head: false, min: [c[0] - h, c[1] - h, c[2] - h], max: [c[0] + h, c[1] + h, c[2] + h] }];
}
