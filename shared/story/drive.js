// OVERDUE drivable cars (WP7): an arcade car over the game's box world. pure: no dom, no node; the client drives with
// it (client-authoritative like player movement) and the co-op server checks speeds with the same numbers (MAXV).
//   newCar(ty, p, h)                     a car state: { ty, x, y, z, h, vx, vy, vz, steer, heat, hot, ground, air, hp }
//   stepCar(car, inp, dt, world, opts)   one physics step. inp { f, b, l, r, hand, boost }; world { query, raycast }
//                                        (shared/physics.js style over BOXES / a ChunkWorld); opts.slip(x, z) -> grip
//                                        multiplier for marbles / peels. returns events: [{ crash, v } | { eject, v } |
//                                        { land, v } | { overheat }]
//   speedOf(car), fwdOf(car), seatOf(car) (where the driver's eye goes), carBoxes(car) (for bullets / projectiles)
// handling: throttle, brake, reverse, steering that tightens at speed, a handbrake drift, a boost you can hold until it
// overheats, momentum kept off ramps (no ground = keep flying), terraces climbed up to a kerb, wall hits that bounce,
// and above a speed the driver goes through the windscreen.
import { CARS } from '../traffic.js';

export const DRIVE = { grav: 24, step: 0.65, brake: 32, rev: 10, drag: 0.22, roll: 1.2, grip: 11, hand: 2.0, slipGrip: 0.18,
  turn: 2.3, boostTop: 1.55, boostAcc: 1.8, heatUp: 1 / 4, heatDown: 1 / 6, hotFor: 3, crash: 13, eject: 27, restit: 0.35 };
// the slice's own cars on top of the traffic ones: the Bottom's sofa-car (ART_BIBLE model 9) is a couch with wheels
export const STORY_CARS = { sofa: { L: 3.0, W: 1.9, H: 1.5, hp: 120, mass: 0.9, acc: 3.0, story: true } };
export const carType = (ty) => (Object.hasOwn(STORY_CARS, ty) ? STORY_CARS[ty] : Object.hasOwn(CARS, ty) ? CARS[ty] : CARS.hatch);
export const topOf = (T) => Math.max(16, 40 - 4.5 * T.mass); // m/s on the flat (hatch ~35, bus ~18)
// the most a car can ever do (boost, downhill, a ramp): what a server lets a client claim
export const MAXV = (ty) => topOf(carType(ty)) * DRIVE.boostTop * 1.6 + 10;

export function newCar(ty, p = [0, 0, 0], h = 0) {
  const T = carType(ty);
  return { ty: Object.hasOwn(STORY_CARS, ty) || Object.hasOwn(CARS, ty) ? ty : 'hatch', x: p[0], y: p[1], z: p[2], h, vx: 0, vy: 0, vz: 0, steer: 0, heat: 0, hot: 0, ground: true, air: 0, hp: T.hp, spin: 0 };
}
export const fwdOf = (c) => [Math.sin(c.h), 0, Math.cos(c.h)];
export const speedOf = (c) => Math.hypot(c.vx, c.vz);
export function seatOf(c) { const T = carType(c.ty), f = fwdOf(c), s = [f[2], 0, -f[0]]; return [c.x - f[0] * T.L * 0.08 + s[0] * T.W * 0.22, c.y + T.H * 0.62, c.z - f[2] * T.L * 0.08 + s[2] * T.W * 0.22]; }
// the car as boxes (axis-aligned around its circles): enough for "a bullet hit the car" and "a car hit you"
export function carBoxes(c) {
  const T = carType(c.ty), f = fwdOf(c), r = T.W / 2, n = Math.max(2, Math.round(T.L / T.W)), out = [];
  for (let i = 0; i < n; i++) { const k = (i / (n - 1) - 0.5) * (T.L - T.W), x = c.x + f[0] * k, z = c.z + f[2] * k; out.push({ min: [x - r, c.y, z - r], max: [x + r, c.y + T.H, z + r], car: true }); }
  return out;
}

const tmp = [];
export function stepCar(c, inp, dt, world, opts = {}) {
  const T = carType(c.ty), ev = [], f = fwdOf(c), s = [f[2], 0, -f[0]]; // s: the car's right
  // speeds in the car's frame
  let vf = c.vx * f[0] + c.vz * f[2], vl = c.vx * s[0] + c.vz * s[2];
  const slip = opts.slip ? opts.slip(c.x, c.z) : 1;
  // boost: hold it, it heats up; overheated = no boost for a few seconds
  c.hot = Math.max(0, c.hot - dt);
  const boosting = inp.boost && c.hot <= 0 && c.ground && vf > -1;
  if (boosting) { c.heat += DRIVE.heatUp * dt; if (c.heat >= 1) { c.heat = 1; c.hot = DRIVE.hotFor; ev.push({ overheat: true }); } }
  else c.heat = Math.max(0, c.heat - DRIVE.heatDown * dt);
  const top = topOf(T) * (boosting ? DRIVE.boostTop : 1), acc = T.acc * 4 * (boosting ? DRIVE.boostAcc : 1);
  if (c.ground) {
    // steering first: quick at walking pace, tighter at speed, backwards when reversing; the handbrake swings it round
    const want = (inp.r ? 1 : 0) - (inp.l ? 1 : 0);
    c.steer += (want - c.steer) * Math.min(1, dt * 8);
    const sp = Math.min(1, Math.abs(vf) / 5) * Math.sign(vf), tight = 1 / (1 + Math.abs(vf) / 32);
    c.h -= c.steer * DRIVE.turn * sp * tight * (inp.hand ? 1.6 : 1) * dt;
    // then the speed you have, seen from the NEW heading: the tyres pull it in line (grip) unless you're on the handbrake
    // or something slippery. what they don't pull in is a drift
    const f1 = fwdOf(c), s1 = [f1[2], 0, -f1[0]];
    vf = c.vx * f1[0] + c.vz * f1[2]; vl = c.vx * s1[0] + c.vz * s1[2];
    // throttle / brake / reverse
    if (inp.f && !inp.b) vf += (vf < top ? acc : -acc * 0.5) * dt;
    else if (inp.b && !inp.f) vf -= (vf > 0.5 ? DRIVE.brake : vf > -DRIVE.rev ? acc * 0.7 : 0) * dt;
    else vf -= Math.sign(vf) * Math.min(Math.abs(vf), DRIVE.roll * dt); // coasting
    vf -= vf * DRIVE.drag * dt * (Math.abs(vf) > top ? 6 : 1); // over the top speed (boost let go, downhill): eases back
    if (inp.hand) vf -= Math.sign(vf) * Math.min(Math.abs(vf), 6 * dt);
    const grip = (inp.hand ? DRIVE.hand : DRIVE.grip) * (slip < 1 ? Math.max(DRIVE.slipGrip, slip) : 1);
    vl *= Math.exp(-grip * dt);
    c.vx = f1[0] * vf + s1[0] * vl; c.vz = f1[2] * vf + s1[2] * vl;
  }
  const f2 = fwdOf(c);
  c.vy -= DRIVE.grav * dt;
  // move, then fix: walls (circles along the car vs boxes taller than a kerb), then the ground
  c.x += c.vx * dt; c.z += c.vz * dt; c.y += c.vy * dt;
  const r = T.W / 2, n = Math.max(2, Math.round(T.L / T.W)), lo = c.y + DRIVE.step, hi = c.y + T.H;
  let hit = 0;
  for (let i = 0; i < n; i++) {
    const k = (i / (n - 1) - 0.5) * (T.L - T.W);
    let cx = c.x + f2[0] * k, cz = c.z + f2[2] * k;
    const list = world.query(cx - r - 0.5, cz - r - 0.5, cx + r + 0.5, cz + r + 0.5, tmp);
    for (const b of list) {
      if (b.car || b.max[1] <= lo || b.min[1] >= hi) continue; // a kerb (the wheels climb it) or overhead
      const px = Math.max(b.min[0], Math.min(cx, b.max[0])), pz = Math.max(b.min[2], Math.min(cz, b.max[2]));
      let dx = cx - px, dz = cz - pz, d = Math.hypot(dx, dz);
      if (d >= r) continue;
      if (d < 1e-6) { // the centre is inside the box: out the nearest side
        const o = [cx - b.min[0], b.max[0] - cx, cz - b.min[2], b.max[2] - cz], m = Math.min(...o), j = o.indexOf(m);
        dx = j === 0 ? -1 : j === 1 ? 1 : 0; dz = j === 2 ? -1 : j === 3 ? 1 : 0; d = 0;
        const push = m + r; c.x += dx * push; c.z += dz * push; cx += dx * push; cz += dz * push;
      } else { const push = r - d; dx /= d; dz /= d; c.x += dx * push; c.z += dz * push; cx += dx * push; cz += dz * push; }
      const into = -(c.vx * dx + c.vz * dz); // speed straight into the wall
      if (into > 0) { c.vx += dx * into * (1 + DRIVE.restit); c.vz += dz * into * (1 + DRIVE.restit); hit = Math.max(hit, into); c.spin += (Math.random() - 0.5) * into * 0.08; }
    }
  }
  if (hit > DRIVE.eject) ev.push({ eject: true, v: hit });
  else if (hit > DRIVE.crash) ev.push({ crash: true, v: hit });
  if (hit > DRIVE.crash) c.hp = Math.max(0, c.hp - (hit - DRIVE.crash) * 6);
  if (c.spin) { c.h += c.spin * dt; c.spin *= Math.exp(-3 * dt); if (Math.abs(c.spin) < 0.01) c.spin = 0; }
  // ground: the highest floor under the car within a step of its wheels (rays at the nose, the middle, the tail)
  let floor = -Infinity;
  for (const k of [-0.4, 0, 0.4]) {
    const o = [c.x + f2[0] * T.L * k, c.y + DRIVE.step + 0.05, c.z + f2[2] * T.L * k];
    const g = world.raycast(o, [0, -1, 0], DRIVE.step + 0.05 + Math.max(0.3, -c.vy * dt + 0.05));
    if (g && g.point[1] > floor) floor = g.point[1];
  }
  const was = c.ground;
  if (floor > -Infinity && c.y <= floor + 0.02) {
    if (!was && c.air > 0.25) ev.push({ land: true, v: -c.vy });
    c.y = floor; if (c.vy < 0) c.vy = 0; c.ground = true; c.air = 0;
  } else { c.ground = false; c.air += dt; }
  return ev;
}
