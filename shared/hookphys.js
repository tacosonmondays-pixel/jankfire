// Grapple rope physics, shared by players (client, 120 Hz) and bots (server, 60 Hz) so everyone swings the same way.
// The rope is a pendulum: a steady wind pulls you toward the point (the old pull, so long grapples still build speed),
// a reel winds the rope in at a steady rate (and takes up any slack), it only ever pulls, it holds your swing at its
// length (so you keep your momentum and swing in arcs while it winds you in), and a catch is a spring + damper instead
// of a hard clamp, so catching a fall or reaching the point never spikes your velocity.
import { HOOK } from './weapons.js';

export const ROPE = {
  pull: HOOK.pull, // m/s²: steady wind toward the point, never capped, like the old pull (this is where grapple speed comes from)
  pullFade: 5, // m: the wind fades out over this much distance before minLen, so it never switches off in one step
  reel: 30, // m/s: steady reel-in speed once it's wound up (when you're not already closing faster on your own)
  wind: HOOK.pull, // m/s²: how fast the reel winds up
  round: 0.06, // s: smoothing on the reel speed so winding up / easing off never kicks
  minLen: 1.8, // m from your chest: the reel stops here and you hang
  reelLoad: 45, // m/s²: the reel stalls (the rope just holds its length) once your swing pulls on it harder than this, so
  // winding in under a fast swing can't spin you up like a tetherball. the wind still draws you in when the swing is slow
  arrive: 40, // m/s²: the closing speed profile you glide in on at the end, so you settle instead of slamming into it
  brake: 300, // m/s²: the most the arrival eases you down with...
  arriveZone: 6, // m: ...and only over the last stretch (up to twice this when you come in fast), never further out
  give: 0.2, // m: the rope takes up a swing over this much stretch, so going taut at speed ramps in over a few steps
  k: 600, // 1/s²: rope stiffness once it's stretched past its length
  zeta: 0.9, // damping ratio of the stretch
  soft: 0.15, // m: the damper fades in over this much stretch, so a catch ramps up instead of hitting all at once
  maxPull: 100, // m/s²: the most a catch pulls with on top of holding your swing. past that it pays out a little
  lift: 0.35, // share of gravity the rope takes while you're on it
  park: 3.5, // 1/s: once reeled in and slow, leftover swinging dies down so you settle under the point
};

// grapple jump: let go and get flung along your swing plus a modest hop. better on the upswing, swinging the way you look
export const ROPE_JUMP = { base: 2, mulMin: 0.06, mulMax: 0.14, up: 8.5, hang: 3.5 }; // hang: extra hop when you're barely moving, so hook-a-ledge-and-hop-up still works

const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
const smooth = (x) => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };

// one fixed step on the rope. h = hook state ({len, ...}, filled in on the first step, and again if anything else sets h.len),
// a = anchor, p = feet, v = velocity (gravity already applied this step). mutates v and h. returns how hard the rope
// pulled (m/s², toward the point). mul scales the wind and the reel (Spoons & Grapples pulls 1.35x)
export function ropeStep(h, a, p, v, dt, grav, mul = 1) {
  const dx = a[0] - p[0], dy = a[1] - (p[1] + 1), dz = a[2] - p[2];
  const dist = Math.hypot(dx, dy, dz);
  v[1] += grav * ROPE.lift * dt;
  h.dist = dist;
  if (dist < 0.05) { h.pull = 0; return 0; }
  const nx = dx / dist, ny = dy / dist, nz = dz / dist;
  let vin = v[0] * nx + v[1] * ny + v[2] * nz; // closing speed
  if (h.lp !== h.len) h.reel = null; // someone else set the rope length (a new hook, or another mode handing it back): start fresh
  const PULL = ROPE.pull * mul, REEL = ROPE.reel * mul;
  if (h.reel == null) { h.len = dist; h.reel = h.rt = clamp(vin, 0, REEL); h.pull = 0; h.n = [0, 0, 0]; } // first step: taut, already reeling if you were flying at it
  h.n[0] = nx; h.n[1] = ny; h.n[2] = nz; // rope direction, for the camera lean
  // the wind: a steady pull toward the point that fades out smoothly near the end (no on/off buzz at the anchor)
  const wf = PULL * smooth((dist - ROPE.minLen) / ROPE.pullFade);
  v[0] += nx * wf * dt; v[1] += ny * wf * dt; v[2] += nz * wf * dt; vin += wf * dt;
  // closing in faster than the reel: it takes up the slack, so the rope is there to swing you when you get close
  if (h.len > dist) h.len = Math.max(ROPE.minLen, dist);
  // reel: takes over from the wind as it fades, winds up to a steady speed and slows near the end so it stops right at
  // minLen. the corners of that speed profile are rounded off (rt = profile, reel = smoothed) so the pull never switches
  // on or off in one step
  const room = Math.max(0, h.len - ROPE.minLen);
  const want = (1 - wf / PULL) * Math.min(REEL, Math.sqrt(2 * ROPE.arrive * Math.max(0, room - h.reel * ROPE.round))); // aims early by the smoothing lag
  h.rt += clamp(want - h.rt, -ROPE.wind * 2 * dt, ROPE.wind * dt);
  h.reel += (h.rt - h.reel) * (1 - Math.exp(-dt / ROPE.round));
  if (h.reel * dt > room) h.reel = room / dt;
  const sp2 = v[0] * v[0] + v[1] * v[1] + v[2] * v[2], vt2 = Math.max(0, sp2 - vin * vin);
  const gOut = Math.max(0, grav * (1 - ROPE.lift) * ny); // the share of your weight hanging off the rope
  const stall = smooth((vt2 / dist + gOut - ROPE.reelLoad) / ROPE.reelLoad);
  const len0 = h.len;
  h.len = Math.max(ROPE.minLen, h.len - h.reel * (1 - stall) * dt);
  const ldot = (h.len - len0) / dt;
  // coming in head-on (you'd hit the point, not swing past it) over the last stretch: ease the closing speed down so
  // you arrive and settle instead of slamming into the wall it's stuck to. further out, or swinging past, it never brakes
  const miss = sp2 > 0.01 ? dist * Math.sqrt(vt2 / sp2) : 0; // how far from the point you'd fly past
  const zone = clamp((vin * vin) / ROPE.brake, ROPE.arriveZone, ROPE.arriveZone * 2);
  const az = (1 - smooth((Math.min(h.len, dist) - ROPE.minLen) / zone)) * (1 - smooth((miss - ROPE.minLen) / 2.5));
  const vmax = Math.sqrt(2 * ROPE.arrive * Math.max(0, dist - ROPE.minLen)) + 1.5;
  if (az > 0 && vin > vmax) {
    const dv = Math.min((vin - vmax) * 12 * dt, ROPE.brake * az * dt);
    v[0] -= nx * dv; v[1] -= ny * dv; v[2] -= nz * dv; vin -= dv;
  }
  // the rope itself, in two parts. pull only.
  // 1. holding the swing: take out the outward drift that swinging round the point makes this step (what the old hard
  //    rope did, but never more, and eased in over a few cm), so even a very fast swing is held with no bounce
  // 2. a catch (moving away from the point, e.g. falling onto the rope): spring + damper on the stretch, solved
  //    implicitly (stable at 60 and 120 Hz) and capped, so it ramps up and takes a hard catch out over a few steps
  let pull = 0;
  const C = dist - h.len;
  if (C > 0) {
    const hold = clamp(-vin - ldot, 0, (vt2 / dist + gOut) * dt * smooth(C / ROPE.give));
    vin += hold;
    const c = 2 * ROPE.zeta * Math.sqrt(ROPE.k) * smooth(C / ROPE.soft);
    const cdot = -vin - ldot; // how fast it's still stretching
    let dv = (dt * (cdot * (ROPE.k * dt + c) + ROPE.k * C)) / (1 + ROPE.k * dt * dt + c * dt);
    dv = clamp(dv, 0, ROPE.maxPull * dt) + hold; // catching a hard fall: it slips a little instead of jerking you
    if (dv > 0) { v[0] += nx * dv; v[1] += ny * dv; v[2] += nz * dv; pull = dv / dt; }
    const maxC = ROPE.maxPull / ROPE.k + 0.05;
    if (C > maxC) h.len = dist - maxC; // pays out, so stretch never builds up into a slingshot
  }
  pull += wf;
  // close to the point and slow: leftover sideways swinging dies down so you settle under it instead of whipping round
  // into the wall it's stuck to (fast swings past the point and swings further out keep everything)
  const sp = Math.hypot(v[0], v[1], v[2]);
  const parked = (1 - smooth((Math.min(h.len, dist) - ROPE.minLen) / 2.5)) * (1 - smooth((sp - 3) / 9));
  if (parked > 0) {
    const vr = v[0] * nx + v[1] * ny + v[2] * nz, k = 1 - Math.exp(-ROPE.park * parked * dt);
    v[0] -= (v[0] - nx * vr) * k; v[1] -= (v[1] - ny * vr) * k; v[2] -= (v[2] - nz * vr) * k;
  }
  h.pull = pull; h.lp = h.len;
  return pull;
}

// grapple jump: an impulse along your current swing direction plus a modest hop, added on top of your momentum
// (never replaces it). q = timing, 0..1: rising and swinging the way you look gets more. look = unit look vector.
// n (optional) = rope direction: the fling then never points into the point (bots letting go right by the wall)
export function ropeJump(v, look, n) {
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
  // the fling never pushes you further down: on a downswing it goes sideways (or the way you look when falling straight)
  let bx = dx, by = Math.max(0, dy), bz = dz;
  if (n) { const i = Math.max(0, bx * n[0] + by * n[1] + bz * n[2]); bx -= n[0] * i; by = Math.max(0, by - n[1] * i); bz -= n[2] * i; }
  const bl = Math.hypot(bx, by, bz);
  if (bl < 0.3) { bx += (look[0] / lh) * (0.3 - bl); bz += (look[2] / lh) * (0.3 - bl); }
  const bn = Math.hypot(bx, by, bz) || 1;
  v[0] += (bx / bn) * boost; v[1] += (by / bn) * boost; v[2] += (bz / bn) * boost;
  // a grapple jump never leaves you slower than you were (topped up sideways, so it never speeds up a fall)
  const s2 = Math.hypot(v[0], v[1], v[2]), min = sp + J.base * 0.5;
  if (s2 < min) {
    const h2 = Math.hypot(v[0], v[2]), want = Math.sqrt(Math.max(0, min * min - v[1] * v[1]));
    if (h2 > 0.01) { v[0] *= want / h2; v[2] *= want / h2; }
  }
  // the hop goes on last so nothing undoes it: full strength when you're falling (it saves you), less on a flat swing
  v[1] += J.up * Math.max(0.75 + 0.25 * q, smooth(-dy / 0.3)) + J.hang * (1 - smooth(sp / 10));
  return q;
}
