// Third-person locomotion for the mannequin: idle, walk, run, sprint and "zooming", strafes and backpedals, jumps,
// landings, bhop chains, the Plant & Defuse tiptoe, crouch walk, the slide and the marbles slip.
// Driven only by what everyone already gets: the interpolated position, the floor under them and their flags.
// The stride is placed foot-first: a planted foot slides back under the hips at exactly the speed they move (the hip
// angle is solved from where the foot must be), so feet don't skate at any speed. No allocations per frame (30 remotes).
// Angles are "world" leg angles (0 = straight down, + = foot forward, knee - = a normal bend); the body lean is taken
// back out of the hips so the legs stay where they're drawn when the torso tilts.
import * as THREE from 'three';
import { FLAGS } from '/shared/weapons.js';

const TAU = Math.PI * 2;
const L1 = 0.44, L2 = 0.45, HIP = 0.92, SOLE = 0.035, KNEE_R = 0.06; // thigh, shin + foot, hip height (mannequin units)
const cl = (v, a, b) => (v < a ? a : v > b ? b : v);
const ss = (a, b, v) => { const t = cl((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const mix = (a, b, t) => a + (b - a) * t;
const toward = (cur, tgt, rate, dt) => cur + (tgt - cur) * Math.min(1, rate * dt);
// weapons that leave the left hand free to swing (everything else has it on the gun)
const FREE = new Set([null, 'knife', 'bread', 'slipper', 'slapper', 'spoon', 'scales', 'claw', 'pistol', 'revolver', 'cig', 'cards', 'snowball', 'duck', 'taser', 'remote', 'radar', 'popper', 'reverse', 'water', 'scythe', 'camera']);
export const freeHand = (w) => FREE.has(w ?? null);

// the pose being built this frame. SUP: how high the hips sit (the planted foot on the floor, or hanging in the air)
const N = 14, P = new Float64Array(N), Q = new Float64Array(N), H2 = new Float64Array(N);
const HL = 0, HR = 1, KL = 2, KR = 3, ZL = 4, ZR = 5, LEAN = 6, ROLL = 7, SUP = 8, AX = 9, AY = 10, AZ = 11, HX = 12, TW = 13;
const blend = (k) => { if (k > 0.001) for (let i = 0; i < N; i++) P[i] += (Q[i] - P[i]) * k; };
// how far below the hip the lowest bit of a leg is (the foot, or the knee when it's folded under). the leg's euler order
// is x(z(v)): the side swing z first, then the hip x
const footDrop = (h, k, z) => { const ch = Math.cos(h), cz = Math.cos(z); return Math.max(L1 * cz * ch + KNEE_R, (L1 + L2 * Math.cos(k)) * cz * ch - L2 * Math.sin(k) * Math.sin(h) + SOLE); };
const drop = (q) => Math.max(footDrop(q[HL], q[KL], q[ZL]), footDrop(q[HR], q[KR], q[ZR]));

const qUndo = new THREE.Quaternion(), qT = new THREE.Quaternion(), AXX = new THREE.Vector3(1, 0, 0), AXY = new THREE.Vector3(0, 1, 0), AXZ = new THREE.Vector3(0, 0, 1);

function state(r) {
  return r.lo || (r.lo = {
    t: 0, ph: Math.random() * TAU, seed: Math.random() * 100, has: false, lx: 0, ly: 0, lz: 0, spd: 0, vy: 0, fw: 0, rt: 0,
    air: false, airT: 0, airK: 0, vyMin: 0, landT: -9, landK: 0, ant: 0, jumps: 0, crouchK: 0, slideK: 0, walkK: 0, zoomK: 0,
    hangK: 0, slipT: 9, slipK: 0, lean: 0, aimLean: 0, freeK: 0, hx: 0, az: 0, grounded: true, sup: HIP,
  });
}

// stride length (one full cycle, both feet) at local speed v
const strideLen = (v, back, crouch, sneak) => Math.min(3.6, 1 + 0.24 * v) * (back ? 0.78 : 1) * mix(1, 0.62, crouch) * mix(1, 0.6, sneak);

// the gait on the ground at local speed v (mannequin units/s) into q
function gait(q, o, v, dir, back, crouch, sneak, jk) {
  const wk = ss(0.25, 2.2, v), run = ss(5, 8.5, v) * (1 - crouch) * (1 - sneak), spr = ss(9.5, 12, v) * (1 - crouch) * (1 - sneak);
  const duty = mix(mix(0.62, 0.4, run), 0.33, spr); // share of the cycle a foot is on the floor
  const R = (duty * strideLen(v, back, crouch, sneak)) / 2 * wk; // the planted foot goes from +R to -R under the hip
  const kSt = mix(0.08, 0.28, run) + crouch * 1.85 + sneak * 0.3, kLoad = run * 0.22 + spr * 0.1;
  const kSw = (mix(0.95, 1.55, run) + spr * 0.6 + sneak * 0.75 - crouch * 0.5) * wk;
  const xoff = (run * 0.06 + spr * 0.05) * (back ? -1 : 1) + sneak * 0.03; // feet land a touch ahead when running
  const cd = Math.cos(dir), sd = Math.sin(dir), m = -Math.min(2 * R * (1 - duty) / duty, 1.3 * R);
  const idle = 1 - wk, sh = Math.sin(o.t * 0.5 + o.seed);
  let sup = 0, planted = false, flight = 0;
  for (let leg = 0; leg < 2; leg++) {
    const u = ((o.ph / TAU + leg * 0.5) % 1 + 1) % 1;
    let x, k, st = u < duty;
    if (st) { const a = u / duty; x = R * (1 - 2 * a); k = kSt + kLoad * Math.sin(Math.PI * a); }
    else { // swing: a hermite back to the front, carrying the planted foot's speed through (no snap at toe-off)
      const s = (u - duty) / (1 - duty), s2 = s * s, s3 = s2 * s;
      x = -R * (2 * s3 - 3 * s2 + 1) + m * (s3 - 2 * s2 + s) + R * (3 * s2 - 2 * s3) + m * (s3 - s2);
      k = kSt + kSw * Math.sin(Math.PI * Math.pow(s, 0.8));
      if (duty < 0.5) { const fu = (u % 0.5 - duty) / (0.5 - duty); if (fu > 0 && fu < 1) flight = Math.sin(Math.PI * fu); }
    }
    k += idle * (0.05 + Math.max(0, leg ? -sh : sh) * 0.22); // idle: a lazy weight shift from leg to leg
    k = -k * jk;
    // solve the hip for where the foot has to be: sideways first (z), then forward (x) round the bent knee
    const xf = x * cd + xoff, xl = x * sd, A = L1 + L2 * Math.cos(k), sk = L2 * Math.sin(k);
    const z = Math.asin(cl(xl / A, -0.8, 0.8)) + (leg ? 1 : -1) * Math.abs(sd) * 0.07 * wk; // (strafing: feet apart so they don't tangle)
    const A2 = A * Math.cos(z), le = Math.hypot(A2, sk), dl = Math.atan2(sk, A2);
    q[HL + leg] = Math.asin(cl(xf / le, -0.97, 0.97)) - dl - (leg ? 0.05 : 0) * crouch;
    q[KL + leg] = k; q[ZL + leg] = z;
    if (st) { planted = true; sup = Math.max(sup, Math.sqrt(Math.max(0, le * le - xf * xf)) + SOLE); }
    if (leg === 0) q[AX] = x / (R + 1e-6); // (the left foot's place in its stride: the free arm swings against it)
  }
  if (planted) o.sup = sup; else sup = o.sup; // in a run's flight phase both feet are up: the hips keep their height
  const sneakBob = sneak * wk * 0.035 * Math.abs(Math.sin(o.ph * 2));
  q[SUP] = sup + flight * (run * 0.045 + spr * 0.035) + sneakBob + idle * Math.sin(o.t * 2.1 + o.seed) * 0.006;
  q[LEAN] = -(0.04 * wk + 0.13 * run + 0.2 * spr) * (back ? -0.5 : 1) * Math.abs(cd) - crouch * 0.3 - sneak * 0.18 + idle * Math.sin(o.t * 2.1 + o.seed) * 0.012;
  q[ROLL] = -sd * (0.1 * wk + 0.08 * run) + idle * sh * 0.035;
  // the free arm swings against its leg, more pump the faster. sneaking: paws up
  q[AX] = -1.4 - q[AX] * wk * (mix(0.3, 0.55, run) + spr * 0.25) * (back ? -0.7 : 1) + run * 0.18 + spr * 0.08 + sneak * 0.8;
  q[AY] = 0.22 + run * 0.05; q[AZ] = 1.45 - sneak * 0.4;
  q[HX] = -q[LEAN] * 0.6 - flight * 0.04 * run;
  q[TW] = 0;
}

// zooming: past sprint speed the legs give up. lean way in, legs tucked back, arms streaming behind, hovering a bit
function zoom(q, o) {
  const fl = Math.sin(o.t * 31) * 0.09;
  q[HL] = -0.4 + fl; q[HR] = -0.15 - fl; q[KL] = -1.6; q[KR] = -1.25;
  q[ZL] = -0.06; q[ZR] = 0.06;
  q[LEAN] = -0.6; q[ROLL] = Math.sin(o.t * 7) * 0.04; q[SUP] = HIP - 0.08 + Math.sin(o.t * 11) * 0.02;
  q[AX] = -2.65 + fl * 0.5; q[AY] = 0.35; q[AZ] = 1.45;
  q[HX] = 0.42; q[TW] = 0;
}

// in the air: a tucked rise, then legs spread for the landing. long hangs pedal, big falls panic
function airPose(q, o, alt, vyl) {
  const tuck = ss(0, 0.16, o.airT), fall = ss(2.5, -3.5, vyl), panic = ss(-12, -20, vyl) * ss(0.5, 1.0, o.airT);
  const pd = Math.sin(o.t * 9) * 0.35 * ss(0.7, 1.2, o.airT) * (1 - panic); // a little bicycle kick
  for (let i = 0; i < 2; i++) {
    const lead = (i === 0) === !alt; // the lead leg swaps every jump so a bhop chain alternates
    const rh = lead ? mix(0.05, 0.95, tuck) : mix(-0.05, 0.4, tuck), rk = lead ? mix(-0.15, -1.55, tuck) : mix(-0.1, -1.15, tuck);
    const fh = lead ? 0.5 : -0.28, fk = lead ? -0.55 : -0.3;
    q[HL + i] = mix(rh, fh, fall) + (i ? -pd : pd) + panic * Math.sin(o.t * 17 + i * 2) * 0.6;
    q[KL + i] = mix(rk, fk, fall) - Math.abs(pd) * 0.6 - panic * (0.6 + Math.sin(o.t * 15 + i) * 0.5);
    q[ZL + i] = (i ? 1 : -1) * (0.08 + fall * 0.12 + panic * 0.25);
  }
  q[LEAN] = mix(-0.1, 0.06, fall); q[ROLL] = panic * Math.sin(o.t * 6) * 0.15; q[SUP] = HIP - 0.04 * tuck;
  q[AX] = mix(-0.9, -0.35, fall) + panic * ((o.t * 14) % TAU) * 0.6; q[AY] = mix(0.5, 1.1, fall); q[AZ] = 1.45;
  q[HX] = mix(0.12, -0.15, fall) + panic * Math.sin(o.t * 13) * 0.3; q[TW] = 0;
}

// hanging off a grapple: legs dangle together and trail behind the swing
function hang(q, o) {
  const s = Math.sin(o.t * 3.1 + o.seed) * 0.12;
  q[HL] = -0.15 + s; q[HR] = 0.1 - s; q[KL] = -0.55; q[KR] = -0.25;
  q[ZL] = -0.05; q[ZR] = 0.05;
  q[LEAN] = cl(-o.fw * 0.02, -0.4, 0.3); q[ROLL] = cl(-o.rt * 0.02, -0.4, 0.4); q[SUP] = HIP;
  q[AX] = -0.6 + s; q[AY] = 0.7; q[AZ] = 1.45; q[HX] = 0.1; q[TW] = 0;
}

// sliding: lead leg out straight, the other folded under, leaning back on the free hand
function slide(q, o) {
  const j = Math.sin(o.t * 40) * 0.03; // rattling over the floor
  q[HL] = 1.38 + j; q[HR] = 0.8; q[KL] = -0.06; q[KR] = -2.35;
  q[ZL] = -0.05; q[ZR] = 0.5;
  q[LEAN] = 0.62; q[ROLL] = 0.08 + j; q[SUP] = drop(q);
  q[AX] = -2.25; q[AY] = 0.75; q[AZ] = 1.45; q[HX] = -0.25; q[TW] = 0;
}

// the marbles slip, by time since the feet went: [t, hipL, hipR, kneeL, kneeR, lean, hip height, head]
const SLIP = [
  [0.00, 0.05, -0.05, -0.1, -0.1, 0.0, 0.92, 0],
  [0.09, 0.9, 0.45, -0.05, -0.35, 0.3, 1.0, 0.45],
  [0.26, 1.95, 1.55, -0.1, -0.5, 1.05, 1.12, 0.6],
  [0.42, 1.75, 2.0, -0.7, -0.15, 1.4, 0.62, 0.35],
  [0.52, 1.35, 1.55, -0.3, -0.55, 1.52, 0.2, -0.2],
  [0.6, 1.8, 1.95, -0.55, -0.25, 1.45, 0.3, 0.3],
  [0.7, 1.45, 1.6, -0.45, -0.6, 1.52, 0.2, 0.1],
  [1.4, 1.45, 1.6, -0.45, -0.6, 1.5, 0.2, 0.1],
  [1.62, 1.25, 1.05, -2.1, -1.9, 0.9, 0.38, 0.35],
  [1.82, 1.0, 0.85, -1.85, -1.6, 0.18, 0.6, 0.15],
  [2.05, 0.05, 0.0, -0.1, -0.08, 0.0, 0.92, 0],
];
export const SLIP_END = 2.05, SLIP_HOLD = 1.38;
function slipPose(q, o, jk) {
  const t = o.slipT, w = o.t; // (w: the kicking runs on real time, so it keeps going while the clock holds)
  let i = 0;
  while (i < SLIP.length - 2 && SLIP[i + 1][0] <= t) i++;
  const a = SLIP[i], b = SLIP[i + 1], u = ss(a[0], b[0], t);
  q[HL] = mix(a[1], b[1], u); q[HR] = mix(a[2], b[2], u); q[KL] = mix(a[3], b[3], u) * jk; q[KR] = mix(a[4], b[4], u) * jk;
  q[LEAN] = mix(a[5], b[5], u); q[SUP] = mix(a[6], b[6], u); q[HX] = mix(a[7], b[7], u);
  // on their back: legs kick like a flipped bug, rocking side to side
  const down = ss(0.62, 0.75, t) * (1 - ss(1.35, 1.5, t));
  q[HL] += Math.sin(w * 17) * 0.45 * down; q[HR] += Math.sin(w * 17 + 2.4) * 0.45 * down;
  q[KL] -= (0.4 + Math.sin(w * 17 + 1) * 0.4) * down * jk; q[KR] -= (0.4 + Math.sin(w * 17 + 3.4) * 0.4) * down * jk;
  q[ZL] = -0.15 - down * 0.2; q[ZR] = 0.15 + down * 0.2;
  q[ROLL] = 0; q[TW] = Math.sin(w * 9) * 0.3 * down;
  // free arm: a full windmill on the way down, then flailing at the sky, then pushing up off the floor
  const air = 1 - ss(0.5, 0.62, t), up = ss(1.4, 1.7, t);
  q[AX] = air * (-1.2 + t * 19) + (1 - air) * (1.4 + Math.sin(w * 12) * 0.7) * (1 - up) + up * -1.6;
  q[AY] = 0.9 * (1 - ss(1.7, 2, t)) + 0.22 * ss(1.7, 2, t); q[AZ] = 1.45;
}

// r: a Remote (or a killcam ghost). sets legs, knees, body and the free arm; leaves the gun arm alone
export function locoPose(r, dt, now) {
  const ch = r.ch, o = state(r), f = r.f | 0, sc = ch.root.scale.y || 1.2;
  o.t += dt;
  const x = r.pos[0], y = r.pos[1], z = r.pos[2];
  // how far they really went this frame (the interpolated position): drives the stride and the speeds
  let dx = 0, dy = 0, dz = 0;
  if (o.has && dt > 0) { dx = x - o.lx; dy = y - o.ly; dz = z - o.lz; if (dx * dx + dy * dy + dz * dz > 36) dx = dy = dz = 0; } // a respawn / teleport
  o.has = true; o.lx = x; o.ly = y; o.lz = z;
  const id = dt > 0 ? 1 / dt : 0;
  o.spd = toward(o.spd, Math.hypot(dx, dz) * id, 12, dt);
  o.vy = toward(o.vy, dy * id, 18, dt);
  // their motion in their own frame (forward / right), smoothed so the stride plane doesn't jitter
  const cy = Math.cos(r.yaw), sy = Math.sin(r.yaw);
  o.fw = toward(o.fw, (-sy * dx - cy * dz) * id, 10, dt); o.rt = toward(o.rt, (cy * dx - sy * dz) * id, 10, dt);
  // on the ground: close to the floor under them (last frame's shadow ray) and not flying up or down
  const gap = y - (r.gy ?? y);
  const grounded = (gap < 0.3 && Math.abs(o.vy) < 4) || gap < 0.06;
  if (!grounded) { if (!o.air) { o.air = true; o.airT = 0; o.vyMin = 0; o.jumps++; } o.airT += dt; o.vyMin = Math.min(o.vyMin, o.vy); }
  else if (o.air) { o.air = false; if (o.airT > 0.12) { o.landT = o.t; o.landK = cl((-o.vyMin - 3) / 18, 0.12, 1); } }
  o.grounded = !o.air || o.airT < 0.08; // (a step down a stair isn't a jump)
  // the jump that's coming: the newest snapshot is ~110 ms ahead of what's drawn, so a takeoff can be seen early
  const nb = r.buf && r.buf[r.buf.length - 1], soon = o.grounded && !!nb && nb.v[1] > 4 && nb.t > (r.rt || 0);
  o.ant = toward(o.ant, soon ? 1 : 0, soon ? 22 : 16, dt);
  const v = o.spd / sc, vyl = o.vy / sc;
  o.crouchK = toward(o.crouchK, (f & FLAGS.CROUCH) && !(f & FLAGS.SLIDE) ? 1 : 0, 12, dt);
  o.slideK = toward(o.slideK, f & FLAGS.SLIDE ? 1 : 0, 14, dt);
  o.walkK = toward(o.walkK, (f & FLAGS.WALK) && !(f & FLAGS.CROUCH) ? 1 : 0, 6, dt);
  o.airK = toward(o.airK, o.grounded ? 0 : 1, o.grounded ? 22 : 12, dt);
  o.hangK = toward(o.hangK, r.g ? 1 : 0, 6, dt);
  o.zoomK = toward(o.zoomK, ss(14, 20, v) * (1 - o.slideK), 5, dt);
  // the slip runs on its own clock: feet go, they land on their back and kick there while the flag lasts (more marbles
  // keep it on), then get up once it drops
  const slipF = !!(f & FLAGS.SLIP);
  if (slipF && !o.slipF && o.slipT > 1.0) o.slipT = 0;
  else if (slipF && o.slipT > SLIP_HOLD && o.slipT < SLIP_END) o.slipT = SLIP_HOLD;
  else if (o.slipT < SLIP_END + 0.3) o.slipT += dt;
  o.slipF = slipF;
  o.slipK = toward(o.slipK, o.slipT < SLIP_END - 0.25 ? 1 : 0, o.slipT < 0.1 ? 40 : 4.5, dt);
  if (f & FLAGS.SLEEP) { o.slipT = 9; o.slipK = 0; } // the nap takes it from here
  // stride direction in their frame; past ~110 degrees off forward it's a backpedal (the stride runs in reverse)
  let dir = Math.atan2(o.rt, o.fw), back = false;
  if (Math.abs(dir) > 1.9) { back = true; dir -= Math.PI * Math.sign(dir); }
  dir *= ss(0.3, 1.5, v);
  const frozen = r.frozenUntil > now;
  if (!frozen && o.grounded) { // phase = distance / stride length, capped so a zoom doesn't turn into a blur
    const L = strideLen(v, back, o.crouchK, o.walkK);
    o.ph += Math.min(TAU * 4.5 * dt, (Math.hypot(dx, dz) / sc / L) * TAU) * (back ? -1 : 1);
  }
  if (frozen) return; // frozen in an ice block: hold the pose
  const jk = ch.jank.wrongKnee ? -0.85 : 1; // the broken one bends the wrong way (a bit less, so it still reads as legs)

  gait(P, o, v, dir, back, o.crouchK, o.walkK, jk);
  if (o.zoomK > 0.001) { zoom(Q, o); blend(o.zoomK); }
  if (o.airK > 0.001) {
    airPose(Q, o, o.jumps & 1, vyl);
    if (o.hangK > 0.001) { hang(H2, o); for (let i = 0; i < N; i++) Q[i] += (H2[i] - Q[i]) * o.hangK; }
    blend(o.airK * (1 - o.zoomK * 0.7));
  }
  if (o.slideK > 0.001) { slide(Q, o); blend(o.slideK); }
  // landing squash (scaled by how hard they came down) and the crouch before a jump. the hips sink with the knees
  const lt = o.t - o.landT, ld = 0.16 + 0.24 * o.landK, d0 = drop(P);
  let sq = 0;
  if (lt >= 0 && lt < ld) {
    const u = lt / ld, e = (u < 0.22 ? ss(0, 0.22, u) : 1 - ss(0.22, 1, u)) * o.landK * (1 - o.airK);
    P[HL] += 0.75 * e; P[HR] += 0.6 * e; P[KL] -= 1.45 * e * jk; P[KR] -= 1.3 * e * jk; P[LEAN] -= 0.3 * e; P[HX] += 0.25 * e; P[AX] -= 0.5 * e;
    P[ZL] -= 0.12 * e; P[ZR] += 0.12 * e; sq += e;
  }
  if (o.ant > 0.001) { const e = o.ant * (1 - o.airK); P[HL] += 0.5 * e; P[HR] += 0.45 * e; P[KL] -= 1.0 * e * jk; P[KR] -= 0.95 * e * jk; P[LEAN] -= 0.14 * e; P[AX] -= 0.4 * e; sq += e; }
  if (sq > 0) P[SUP] += drop(P) - d0;
  if (o.slipK > 0.001) { slipPose(Q, o, jk); blend(o.slipK); }

  // ---- apply. the lean pivots round the hips; the legs get it taken back out
  const lean = P[LEAN], roll = P[ROLL] + ch.jank.lean * 0.3, tw = P[TW]; // (+ their built-in slouch)
  o.lean = lean; o.aimLean = lean * (1 - o.slipK); // (a slip throws the gun at the sky: no aim correction)
  ch.body.rotation.x = lean;
  ch.body.rotation.y = P[TW];
  ch.body.rotation.z = roll;
  // where the hip point lands after the body's rotation (x(y(z))): move the body so it stays put
  const hx0 = -HIP * Math.sin(roll), hy0 = HIP * Math.cos(roll);
  const hx1 = hx0 * Math.cos(tw), hz1 = -hx0 * Math.sin(tw);
  ch.body.position.set(-hx1, P[SUP] - (hy0 * Math.cos(lean) - hz1 * Math.sin(lean)), -(hy0 * Math.sin(lean) + hz1 * Math.cos(lean)));
  // legs: undo the body's roll / twist / lean, then the hip swing, then the side swing (exact, so strafing feet stay planted)
  qUndo.setFromAxisAngle(AXZ, -roll).multiply(qT.setFromAxisAngle(AXY, -tw));
  ch.legL.quaternion.copy(qUndo).multiply(qT.setFromAxisAngle(AXX, P[HL] - lean)).multiply(qT.setFromAxisAngle(AXZ, P[ZL]));
  ch.legR.quaternion.copy(qUndo).multiply(qT.setFromAxisAngle(AXX, P[HR] - lean)).multiply(qT.setFromAxisAngle(AXZ, P[ZR]));
  ch.kneeL.rotation.x = P[KL]; ch.kneeR.rotation.x = P[KR];
  o.hx = P[HX];
  // the free arm hangs and swings unless the hand is on a gun (akimbo keeps its own pose). a slip lets go of anything
  o.freeK = toward(o.freeK, r.weaponMeshL ? 0 : Math.max(freeHand(r.w) ? 1 : 0, o.slipK), 10, dt);
  o.az = 0;
  if (o.freeK > 0.001) {
    const k = o.freeK, a = ch.armL.rotation;
    a.x = mix(a.x, P[AX] - lean * 0.5, k); a.y = mix(a.y, P[AY], k); o.az = P[AZ] * k; // (hangs half with gravity through a lean)
  }
}

// the menu / locker mannequin: just breathing and the odd weight shift (it stands on a plinth, no walking)
export function idlePose(ch, t) {
  const sh = Math.sin(t * 0.5), b = Math.sin(t * 2.1);
  ch.body.position.y = b * 0.006 - 0.01 * Math.abs(sh);
  ch.kneeL.rotation.x = -(0.05 + Math.max(0, sh) * 0.2); ch.kneeR.rotation.x = -(0.05 + Math.max(0, -sh) * 0.2);
  ch.legL.rotation.x = Math.max(0, sh) * 0.08; ch.legR.rotation.x = Math.max(0, -sh) * 0.08;
  ch.body.rotation.z = ch.jank.lean * 0.3 + sh * 0.035;
  ch.head.rotation.x = b * 0.015;
}
