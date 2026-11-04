// Grapple rope physics, shared by players (client, 120 Hz) and bots (server, 60 Hz) so everyone swings the same way.
// The rope is a pendulum: a reel winds it in at a steady rate, it only ever pulls, it keeps your sideways momentum
// (so you swing in arcs while it winds you in), and it's a stiff spring + damper instead of a hard clamp, so catching
// a fall or reaching the point never spikes your velocity.
import { HOOK } from './weapons.js';

export const ROPE = {
  reel: 30, // m/s: steady reel-in speed once it's wound up
  wind: HOOK.pull, // m/s²: how fast the reel winds up (the old pull strength, so the first moment feels the same)
  round: 0.06, // s: smoothing on the reel speed so winding up / easing off never kicks
  minLen: 1.8, // m from your chest: the reel stops here and you hang
  arrive: 40, // m/s²: closing speed eases off near the point (you glide in and settle instead of slamming into it)
  k: 600, // 1/s²: rope stiffness once it's stretched past its length
  zeta: 0.9, // damping ratio of the stretch
  soft: 0.15, // m: the damper fades in over this much stretch, so a catch ramps up instead of hitting all at once
  maxPull: 140, // m/s²: the most the rope pulls with. past that it pays out a little instead of yanking you
  lift: 0.35, // share of gravity the rope takes while you're on it
  park: 3.5, // 1/s: once reeled in, leftover swinging dies down so you settle under the point
};

// grapple jump: let go and get flung along your swing plus a modest hop. better on the upswing, swinging the way you look
export const ROPE_JUMP = { base: 2, mulMin: 0.06, mulMax: 0.14, up: 8.5, hang: 3.5 }; // hang: extra hop when you're barely moving, so hook-a-ledge-and-hop-up still works

const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
const smooth = (x) => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };

// one fixed step on the rope. h = hook state ({len, ...}, filled in on the first step), a = anchor, p = feet, v = velocity
// (gravity already applied this step). mutates v and h. returns how hard the rope pulled (m/s², toward the point).
export function ropeStep(h, a, p, v, dt, grav) {
  const dx = a[0] - p[0], dy = a[1] - (p[1] + 1), dz = a[2] - p[2];
  const dist = Math.hypot(dx, dy, dz);
  v[1] += grav * ROPE.lift * dt;
  h.dist = dist;
  if (dist < 0.05) { h.pull = 0; return 0; }
  const nx = dx / dist, ny = dy / dist, nz = dz / dist;
  let vin = v[0] * nx + v[1] * ny + v[2] * nz; // closing speed
  if (h.reel == null) { h.len = dist; h.reel = h.rt = clamp(vin, 0, ROPE.reel); h.pull = 0; h.n = [0, 0, 0]; } // first step: taut, already reeling if you were flying at it
  h.n[0] = nx; h.n[1] = ny; h.n[2] = nz; // rope direction, for the camera lean
  // reel: winds up to a steady speed and slows near the end so it stops right at minLen. the corners of that
  // speed profile are rounded off (rt = profile, reel = smoothed) so the pull never switches on or off in one step
  const room = Math.max(0, h.len - ROPE.minLen);
  const want = Math.min(ROPE.reel, Math.sqrt(2 * ROPE.arrive * Math.max(0, room - h.reel * ROPE.round))); // aims early by the smoothing lag
  h.rt += clamp(want - h.rt, -ROPE.wind * 2 * dt, ROPE.wind * dt);
  h.reel += (h.rt - h.reel) * (1 - Math.exp(-dt / ROPE.round));
  if (h.reel * dt > room) h.reel = room / dt;
  const len0 = h.len;
  h.len = Math.max(ROPE.minLen, h.len - h.reel * dt);
  const ldot = (h.len - len0) / dt;
  // closing in fast near the point: ease the closing speed down (a damper on the excess, capped) so you arrive and settle
  const vmax = Math.sqrt(2 * ROPE.arrive * Math.max(0, dist - ROPE.minLen)) + 1.5;
  if (vin > vmax) {
    const dv = Math.min((vin - vmax) * 12 * dt, ROPE.arrive * 1.5 * dt);
    v[0] -= nx * dv; v[1] -= ny * dv; v[2] -= nz * dv; vin -= dv;
  }
  // the rope itself: spring + damper on the stretch, solved implicitly (stable at 60 and 120 Hz), pull only, capped
  let pull = 0;
  const C = dist - h.len;
  if (C > 0) {
    const c = 2 * ROPE.zeta * Math.sqrt(ROPE.k) * smooth(C / ROPE.soft);
    const cdot = -vin - ldot; // how fast it's stretching
    let dv = (dt * (cdot * (ROPE.k * dt + c) + ROPE.k * C)) / (1 + ROPE.k * dt * dt + c * dt);
    dv = Math.min(dv, ROPE.maxPull * dt); // can't hold you: it slips instead of jerking you
    if (dv > 0) { v[0] += nx * dv; v[1] += ny * dv; v[2] += nz * dv; pull = dv / dt; }
    const maxC = ROPE.maxPull / ROPE.k + 0.05;
    if (C > maxC) h.len = dist - maxC; // pays out, so stretch never builds up into a slingshot
  }
  // being pulled in conserves angular momentum, which would spin you up like a tetherball. keep the sideways speed
  // you had instead (weighted by how hard the rope pulls, so it fades in and out with the rope)
  const vr = v[0] * nx + v[1] * ny + v[2] * nz, w = smooth(pull / 25);
  if (w > 0 && vr > 0) {
    const tx = v[0] - nx * vr, ty = v[1] - ny * vr, tz = v[2] - nz * vr;
    const f = 1 - w * Math.min(0.2, (vr * dt) / dist);
    v[0] = nx * vr + tx * f; v[1] = ny * vr + ty * f; v[2] = nz * vr + tz * f;
  }
  // close to the point: leftover swinging dies down so you settle under it instead of whipping round into the
  // wall it's stuck to (swings further out keep everything)
  const parked = 1 - smooth((Math.min(h.len, dist) - ROPE.minLen) / 2.5);
  if (parked > 0) {
    const k = 1 - Math.exp(-ROPE.park * parked * dt);
    v[0] -= v[0] * k; v[1] -= v[1] * k; v[2] -= v[2] * k;
  }
  h.pull = pull;
  return pull;
}

// grapple jump: an impulse along your current swing direction plus a modest hop, added on top of your momentum
// (never replaces it). q = timing, 0..1: rising and swinging the way you look gets more. look = unit look vector.
export function ropeJump(v, look) {
  const sp = Math.hypot(v[0], v[1], v[2]);
  const lh = Math.hypot(look[0], look[2]) || 1;
  let dx, dy, dz;
  if (sp > 2) { dx = v[0] / sp; dy = v[1] / sp; dz = v[2] / sp; } else { dx = look[0] / lh; dy = 0; dz = look[2] / lh; }
  const hl = Math.hypot(dx, dz);
  const up = smooth((dy + 0.15) / 0.6); // 0 swinging down, 1 climbing at ~25 degrees or more
  const fwd = hl > 0.05 ? smooth(((dx * look[0] + dz * look[2]) / (hl * lh) + 0.2) / 1.0) : 1;
  const q = up * (0.5 + 0.5 * fwd);
  const J = ROPE_JUMP;
  const boost = J.base + sp * (J.mulMin + (J.mulMax - J.mulMin) * q);
  v[0] += dx * boost; v[1] += dy * boost + J.up * (0.75 + 0.25 * q) + J.hang * (1 - smooth(sp / 10)); v[2] += dz * boost;
  // the hop slows a steep fall a little, but a grapple jump never leaves you slower than you were
  const sp2 = Math.hypot(v[0], v[1], v[2]), min = sp + J.base * 0.5;
  if (sp2 < min && sp2 > 0) { const k = min / sp2; v[0] *= k; v[1] *= k; v[2] *= k; }
  return q;
}
