// Lasso: the rope physics everyone shares. Whoever holds someone (the holder's client, or the server when a bot holds
// them) runs holdStep on the held body every tick and streams it; the server checks it and relays it.
// The trick (from fling games): the body is pulled toward a point L metres down your aim by a stiff, underdamped
// spring with a force cap. Turning at w rad/s moves that point at w * L, so a long line and a fast flick yank the body
// after it at 60+ m/s and it overshoots. Shaking side to side in time with the spring pumps the swing up, walking
// backwards adds your own speed, and when you let go the body keeps all of it.
import { movePlayer } from './physics.js';

export const LASSO = {
  // throw: hold fire to spin the loop overhead (full spin after spinT s), let go to throw it. a quick tap throws a short one
  spinT: 1.1, range: [12, 28], speed: [24, 38], grav: 6, r: 0.55, cd: 1.2, back: 34, drop: 0.35,
  // hold: rope length range (m), per wheel notch, reel speed on the held keys (m/s), where the loop cinches (m above the feet)
  len: [2, 16], wheel: 1.5, reel: 9, waist: 1.1,
  // the spring: stiffness (1/s², about 1.6 Hz), damping ratio (very bouncy) and its force cap (m/s², ~3.7 g). the rope
  // itself is never longer than L * rope[0] + rope[1]: it only pulls, so a hard turn swings them round instead of
  // letting them fly off. fric = drag on a body hauled along the floor
  k: 100, zeta: 0.12, aMax: 95, rope: [1.1, 1], fric: 8, give: 6, // give: m/s a body past the end of the rope is eased back in at
  // fling: launch = their velocity x mul + yours x inherit, capped. time = s before the hold breaks by itself
  mul: 1.2, inherit: 1, cap: 120, time: 5,
  // wriggling free: counted presses (min wrGap ms apart, ~2.5 s of mashing), progress lost per s when you stop
  wriggle: 18, wrGap: 60, wrDecay: 0.15,
  heldSpread: 0.22, // extra hipfire spread while you swing on someone's rope
  // splat: impact speed (m/s) where it starts to hurt, damage per m/s above that, most a single splat does. yeet = a
  // launch this fast gets the big YEET
  splat: [22, 2.4, 140], yeet: 45,
  stream: 30, // Hz: how often the holder sends the body
};

const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
export const aimDir = (yaw, pitch) => { const cp = Math.cos(pitch); return [-Math.sin(yaw) * cp, Math.sin(pitch), -Math.cos(yaw) * cp]; };
export const throwRange = (s) => LASSO.range[0] + (LASSO.range[1] - LASSO.range[0]) * clamp(s, 0, 1);
export const throwSpeed = (s) => LASSO.speed[0] + (LASSO.speed[1] - LASSO.speed[0]) * clamp(s, 0, 1);
export const ropeMax = (L) => L * LASSO.rope[0] + LASSO.rope[1];
export const clampLen = (L) => clamp(L, LASSO.len[0], LASSO.len[1]);
export function splatDmg(s) { const [a, k, m] = LASSO.splat; return s <= a ? 0 : Math.min(m, (s - a) * k); }
// what a release launches them with: their velocity x mul plus the holder's (x inherit), no faster than the cap
export function flingVel(v, hv, mul = LASSO.mul, inherit = LASSO.inherit) {
  const out = [0, 1, 2].map((i) => v[i] * mul + (hv ? hv[i] * inherit : 0));
  const s = Math.hypot(out[0], out[1], out[2]);
  if (s > LASSO.cap) for (let i = 0; i < 3; i++) out[i] *= LASSO.cap / s;
  return out;
}

// one fixed step of a held body. b = { pos (feet), vel } (mutated). h = the holder this step: { eye, dir (unit aim),
// L, hv (holder velocity) }. st = per-hold scratch ({ T } from last step, for the target's velocity).
// returns { T, d (waist to eye), taut, impact (m/s lost against the map this step), n (axis of that impact) }
const tmpV = [0, 0, 0], corr = [0, 0, 0];
export function holdStep(b, h, st, dt, boxes, grav = 26) {
  const p = b.pos, v = b.vel, W = LASSO.waist, e = h.eye;
  const T = [e[0] + h.dir[0] * h.L, e[1] + h.dir[1] * h.L, e[2] + h.dir[2] * h.L];
  const Tp = st.T || T;
  // the target's velocity: the damping is relative to it, so a steady walk or a slow turn doesn't drag behind
  const vT = [(T[0] - Tp[0]) / dt, (T[1] - Tp[1]) / dt, (T[2] - Tp[2]) / dt];
  st.T = T;
  const c = 2 * LASSO.zeta * Math.sqrt(LASSO.k); // damping (1/s)
  let ax = LASSO.k * (T[0] - p[0]) + c * (vT[0] - v[0]);
  let ay = LASSO.k * (T[1] - (p[1] + W)) + c * (vT[1] - v[1]);
  let az = LASSO.k * (T[2] - p[2]) + c * (vT[2] - v[2]);
  const am = Math.hypot(ax, ay, az);
  if (am > LASSO.aMax) { const s = LASSO.aMax / am; ax *= s; ay *= s; az *= s; }
  v[0] += ax * dt; v[1] += (ay - grav) * dt; v[2] += az * dt;
  // the rope: pull only. whatever would take them past its end (relative to you) is taken out, so a hard turn
  // swings them round you on the full rope instead of flinging them off it
  const Lr = ropeMax(h.L), hv = h.hv || [0, 0, 0];
  let dx = p[0] + v[0] * dt - e[0], dy = p[1] + W + v[1] * dt - e[1], dz = p[2] + v[2] * dt - e[2];
  let d = Math.hypot(dx, dy, dz), taut = d >= h.L * 0.985;
  if (d > Lr && d > 1e-6) {
    const nx = dx / d, ny = dy / d, nz = dz / d;
    const vr = (v[0] - hv[0]) * nx + (v[1] - hv[1]) * ny + (v[2] - hv[2]) * nz;
    if (vr > 0) { v[0] -= nx * vr; v[1] -= ny * vr; v[2] -= nz * vr; }
    taut = true;
  }
  tmpV[0] = v[0]; tmpV[1] = v[1]; tmpV[2] = v[2];
  const res = movePlayer(p, v, dt, boxes, false);
  // what the map took off (movePlayer zeroes the axes it hit): that's how hard they slammed into it
  let imp = 0, n = -1;
  for (let i = 0; i < 3; i++) if (v[i] === 0 && tmpV[i] !== 0) { const s = Math.abs(tmpV[i]); if (s > imp) { imp = s; n = i; } }
  if (res.ground) { // dragged along the floor: it grinds the speed down a bit
    const hs = Math.hypot(v[0], v[2]);
    if (hs > 0) { const k = Math.max(0, hs - LASSO.fric * dt) / hs; v[0] *= k; v[2] *= k; }
  }
  // still past the end (caught further out than the rope reaches, or a wall slid them out): ease them back onto it,
  // through the map like a move (never through walls) and only a little each step, without adding any speed
  dx = p[0] - e[0]; dy = p[1] + W - e[1]; dz = p[2] - e[2];
  d = Math.hypot(dx, dy, dz);
  if (d > Lr + 0.02) {
    const k = Math.min(d - Lr, LASSO.give * dt) / d / dt;
    corr[0] = -dx * k; corr[1] = -dy * k; corr[2] = -dz * k;
    movePlayer(p, corr, dt, boxes, false);
  }
  return { T, d, taut, impact: imp, n, ground: !!res.ground };
}

// replays: the 'lasso' holds from before the clip starts that are still on at t0 (ev = [{ s, m }], oldest first)
export function lassoPreroll(ev, t0) {
  return ev.filter((e) => e.m.t === 'lasso' && e.m.k === 'hold' && e.s < t0 && e.s > t0 - (LASSO.time + 1) * 1000 &&
    !ev.some((x) => x.m.t === 'lasso' && x.m.k === 'rel' && x.m.id === e.m.id && x.s >= e.s && x.s < t0));
}
