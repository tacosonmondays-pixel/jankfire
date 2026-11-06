// The new primaries' shared rules: the Nail Gun's pin, the Tennis Ball Launcher's bounces and the Shopping Cart
// Cannon's carts. The server runs the real thing (server/primaries.js); the client uses the same steps to predict
// balls and to drive a cart you're riding, so both sides agree on how things roll and bounce.
import { WEAPONS } from './weapons.js';
import { query, movePlayer } from './physics.js';

export const NAILS = WEAPONS.nailgun.nails;

// ------------------------------------------------------------ tennis balls
// moves a ball with full bounces (restitution e on the hit axis, a little scrub on the others) and counts the
// bounces that hit harder than minBounce (rolling along the floor doesn't count). returns { n, hit } for this step
export function stepBall(pr, dt, allBoxes, grav, minBounce = 3, e = 0.8) {
  const p = pr.p, v = pr.v, r = pr.r;
  v[1] -= grav * dt;
  const m = r + 0.5;
  const boxes = query(allBoxes, Math.min(p[0], p[0] + v[0] * dt) - m, Math.min(p[2], p[2] + v[2] * dt) - m,
    Math.max(p[0], p[0] + v[0] * dt) + m, Math.max(p[2], p[2] + v[2] * dt) + m, []);
  const dist = Math.hypot(v[0], v[1], v[2]) * dt;
  const steps = Math.min(60, Math.max(1, Math.ceil(dist / Math.max(0.08, r))));
  const sdt = dt / steps;
  let n = 0, hit = null;
  for (let i = 0; i < steps; i++) {
    for (let ax = 0; ax < 3; ax++) {
      const d = v[ax] * sdt;
      if (!d) continue;
      p[ax] += d;
      for (const b of boxes) {
        if (!(p[0] - r < b.max[0] && p[0] + r > b.min[0] && p[1] - r < b.max[1] && p[1] + r > b.min[1] && p[2] - r < b.max[2] && p[2] + r > b.min[2])) continue;
        p[ax] = d > 0 ? b.min[ax] - r - 1e-4 : b.max[ax] + r + 1e-4;
        const sp = Math.abs(v[ax]);
        if (sp > minBounce) { n++; hit = { axis: ax, sign: d > 0 ? -1 : 1, p: p.slice(), sp }; }
        v[ax] = -v[ax] * e;
        for (let o = 0; o < 3; o++) if (o !== ax) v[o] *= 0.94; // fuzz scrubs a bit of speed off
        if (ax === 1 && sp < 1.2) v[1] = 0; // resting on the floor: stop jittering
        break;
      }
    }
  }
  return { n, hit };
}
export const ballDmg = (b) => WEAPONS.tennis.dmg * (1 + WEAPONS.tennis.bonus * Math.min(b, WEAPONS.tennis.bounces));

// ------------------------------------------------------------ shopping carts
// a cart is a box on wheels: p = middle of its bottom, yaw = the way its handle points away from (it rolls along -z)
export const CART = {
  L: 0.95, W: 0.6, H: 1.0, // real cart: ~95 cm long, 60 wide, 1 m to the handle
  top: 1.0, // stand / ride on it at this height above its bottom
  max: 6, mine: 3, // most carts in a room at once, and per shooter (the oldest goes)
  fric: 6, airDrag: 0.02, wallBounce: 0.35, restSp: 0.5, restT: 0.25,
  minSp: 4, dmgK: 3, dmgMax: 80, kbK: 1.3, kbUp: 7, hitCd: 700, slow: 0.75, ownerSafe: 0.4,
  dropBoost: 0.35, // falling off something turns this much of the fall into forward speed (riding down stairs speeds you up)
  ride: { acc: 7, top: 11, fric: 1.4, turn: 2.6, reach: 1.1, upTol: 0.7, autoSp: 6, maxSp: 26, jump: 9 },
  sync: 0.1,
};
// the axis-aligned box a cart takes up (its turned footprint's bounding box)
export function cartBox(c, pad = 0) {
  const s = Math.abs(Math.sin(c.yaw || 0)), co = Math.abs(Math.cos(c.yaw || 0));
  const hx = (CART.L / 2) * s + (CART.W / 2) * co + pad, hz = (CART.L / 2) * co + (CART.W / 2) * s + pad;
  return { min: [c.p[0] - hx, c.p[1], c.p[2] - hz], max: [c.p[0] + hx, c.p[1] + CART.H + pad, c.p[2] + hz] };
}
export const boxHit = (a, b) => a.min[0] < b.max[0] && a.max[0] > b.min[0] && a.min[1] < b.max[1] && a.max[1] > b.min[1] && a.min[2] < b.max[2] && a.max[2] > b.min[2];
export const yawOfV = (v, yaw) => (Math.hypot(v[0], v[2]) > 0.8 ? Math.atan2(-v[0], -v[2]) : yaw);
// one physics step for a free cart (flying or rolling). collides like a player (the same box mover, steps up curbs and
// stairs), bounces off walls a bit, rolls with friction, and a drop turns into speed. returns { ground, wall }
export function stepCart(c, dt, boxes, fric = CART.fric) {
  const v = c.v, v0 = v.slice();
  v[1] -= 26 * dt;
  const res = movePlayer(c.p, v, dt, boxes, !!c.ground);
  if (res.wall) for (const ax of [0, 2]) if (v[ax] === 0 && v0[ax]) v[ax] = -v0[ax] * CART.wallBounce;
  const ground = !!res.ground && v[1] <= 0.01;
  if (ground && !c.ground && c.fall < -6) { // landed off a drop: some of the fall becomes roll
    const hs = Math.hypot(v[0], v[2]);
    if (hs > 0.5) { const k = 1 + (-c.fall * CART.dropBoost) / hs; v[0] *= k; v[2] *= k; }
  }
  c.fall = ground ? 0 : Math.min(c.fall || 0, v[1]);
  if (ground) {
    const hs = Math.hypot(v[0], v[2]);
    if (hs > 0) { const ns = Math.max(0, hs - fric * dt) / hs; v[0] *= ns; v[2] *= ns; }
  }
  c.ground = ground;
  c.yaw = yawOfV(v, c.yaw);
  return { ground, wall: res.wall };
}
// how hard a cart moving at sp m/s ploughs someone
export function ploughOf(sp) {
  if (!(sp >= CART.minSp)) return null;
  return { dmg: Math.min(CART.dmgMax, sp * CART.dmgK), kb: sp * CART.kbK, up: CART.kbUp };
}
