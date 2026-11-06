// Overdrive Rig killstreak: the numbers both sides use. The client drives the rig (movement is client-side) and
// animates it; the server judges every punch, block, hack, missile and landing with these same numbers (server/rig.js).
import { FLAGS } from './weapons.js';

export const RIG = {
  dur: 25, // seconds (STREAKS.overdrive.dur is the one the server uses)
  shield: 100, // overshield on top of your HP: it soaks damage first
  kbTake: 0.15, // how much knockback still gets through: the rig shrugs hits off
  // movement: ground speed (m/s), sprint multiplier, ground accel, friction, air accel / cap, gravity, tap hop, eye
  // height, the speed where the overdrive trail starts, and how fast it turns its momentum toward where you push
  speed: 16, sprint: 1.45, accel: 7.5, fric: 4.2, airAccel: 24, airCap: 1.4, grav: 34, hop: 7.5, eye: 2.05, trail: 11, steer: 7,
  // rocket punch: hold to charge (s), cooldown, damage / dash length / knockback (horizontal, up) from no charge to full,
  // dash speed, how far in front of the rig the fist reaches, how wide the dash sweeps, and the wall slam bonus if they
  // hit a wall within wallWin s
  punch: { charge: 1.3, cd: 0.5, dmg: [35, 110], dist: [3.5, 15], speed: 52, kb: [28, 80], up: [7, 15], reach: 1.6, radius: 1.35, wall: 40, wallWin: 0.9 },
  // block: the front 120 degrees (cos 60), 80% off, 40 blocked damage = a full punch, walking speed while blocking
  block: { cos: 0.5, cut: 0.8, full: 40, slow: 0.45 },
  // quickhack: range, how long their grapple is fried, cooldown, how close to the crosshair (cos) the client looks
  hack: { range: 40, dur: 4, cd: 2.5, aim: 0.985 },
  // homing missiles: salvo size, cooldown, damage (direct; the blast falls off to 35% at r), blast radius, knockback,
  // speed (launch -> top), turn rate (rad/s), straight-up boost time before they home, life, seeker range + cone, ms apart
  miss: { n: 4, cd: 10, dmg: 22, r: 3.2, kb: 12, speed: [16, 44], turn: 4.2, boost: 0.25, life: 5, seek: 75, cos: 0.4, gap: 90 },
  // charged leap: hold to charge (s), cooldown, speed forward / up from no charge to full, landing shockwave (damage at
  // the middle, radius from no charge to full, knockback)
  leap: { charge: 0.9, cd: 0.7, h: [11, 27], up: [9.5, 17], dmg: 25, r: [4.5, 7.5], kb: 24 },
};
// every bit the rig sets in your snapshot FLAGS (the server clears them all unless it saw you activate the rig)
export const RIG_BITS = FLAGS.RIG | FLAGS.RIG_BLOCK | FLAGS.RIG_CHARGE | FLAGS.RIG_LEAP;

// streaks you can't start in the rig (they'd fight it for your body: the rig has its own movement), and the rig can't
// start inside a wrecking ball. a clash leaves the streak in your tray
const BODY = new Set(['moonboots', 'spinbot', 'wreckingball', 'overdrive']);
export const rigClash = (id, inRig, inBall) => (inRig && BODY.has(id)) || (inBall && id === 'overdrive');
const clamp01 = (k) => Math.max(0, Math.min(1, Number(k) || 0));
export const lerpK = (a, k) => a[0] + (a[1] - a[0]) * clamp01(k);
export const punchDmg = (c) => lerpK(RIG.punch.dmg, c);
export const punchDist = (c) => lerpK(RIG.punch.dist, c);
// the punch dashes where you look, but flatter (it's a lunge, not a dive into the floor)
export function dashDir(d) {
  const x = d[0], y = d[1] * 0.55, z = d[2], l = Math.hypot(x, y, z) || 1;
  return [x / l, y / l, z / l];
}
// the leap goes where you look, always at least a bit up
export function leapVel(c, d) {
  const L = RIG.leap, hl = Math.hypot(d[0], d[2]) || 1, h = lerpK(L.h, c);
  return [d[0] / hl * h, lerpK(L.up, c) + Math.max(0, d[1]) * 7, d[2] / hl * h];
}
// is `src` in front of someone at `pos` facing `yaw` (within the block cone)? flat, like the rig's arms
export function inFront(yaw, pos, src, cos = RIG.block.cos) {
  const dx = src[0] - pos[0], dz = src[2] - pos[2], l = Math.hypot(dx, dz);
  if (l < 0.3) return true; // point blank: it's in your arms
  return (-Math.sin(yaw) * dx - Math.cos(yaw) * dz) / l >= cos;
}
// what you shoot at (and what the grapple hooks onto): the frame is about 1.35x taller and much broader than a mannequin.
// k = the far-away draw scale, same as the mannequin's hitboxes
export function rigBoxes(pos, k = 1) {
  const [x, y, z] = pos, w = 0.82 * k, hw = 0.48 * k, b = 2.42 * k, t = 3.12 * k;
  return [
    { min: [x - w, y, z - w], max: [x + w, y + b, z + w], head: false },
    { min: [x - hw, y + b, z - hw], max: [x + hw, y + t, z + hw], head: true },
  ];
}
