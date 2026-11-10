// Aim assist for touch players only (touch.js loads this; a mouse never does). Thumbs on glass can't track like a mouse,
// so near an enemy your look slows down a bit and the crosshair gets a gentle tug toward their body.
// kept fair on purpose:
//  - only enemies: never teammates, squadmates or anyone isFriend() says is on your side
//  - only in plain sight (the same raycast bullets use): no tracking through walls
//  - only inside a small ring round the crosshair, at a capped turn rate: it can't snap across the screen
//  - only while your thumbs are doing something: it never aims for you while you stand still
//  - it aims at the body, never the head, and it only turns YOUR camera. hits are still judged by the server like anyone's
import { ME, eye, look } from './player.js';
import { W } from './weapons.js';
import { raycast } from '/shared/physics.js';

const RING = 0.14;     // rad: enemies inside this ring round the crosshair slow your look (about 8 degrees)
const PULL = 0.085;    // rad: ...and inside this one the crosshair gets tugged
const RANGE = 90;      // m
const RATE = 0.38;     // rad/s: the fastest the tug ever turns you, at full strength
const A = { t: null, at: 0, activeUntil: 0 };

const wrap = (a) => { while (a > Math.PI) a -= 2 * Math.PI; while (a < -Math.PI) a += 2 * Math.PI; return a; };

// the enemy nearest the crosshair, in sight: { r, yawErr, pitchErr, ang, dist, size } or null. worked out once per frame
export function assistTarget(api, now) {
  if (A.at === now) return A.t;
  A.at = now; A.t = null;
  const e = eye(), l = look(), zoom = W.aim > 0.5 ? Math.max(1, W.zoom || 1) : 1;
  let best = null, bestScore = 1e9;
  for (const r of api.remotes()) {
    if (!api.enemy(r)) continue;
    const hb = r.hitboxes()[0];
    if (!hb) continue;
    const tx = (hb.min[0] + hb.max[0]) / 2 - e[0], ty = (hb.min[1] + hb.max[1]) / 2 - e[1], tz = (hb.min[2] + hb.max[2]) / 2 - e[2];
    const d = Math.hypot(tx, ty, tz);
    if (d > RANGE || d < 0.8) continue;
    const dir = [tx / d, ty / d, tz / d];
    const c = Math.max(-1, Math.min(1, dir[0] * l[0] + dir[1] * l[1] + dir[2] * l[2]));
    const size = Math.atan2(0.45, d); // how wide their body looks from here: up close the ring grows with them
    const ang = Math.acos(c);
    if (ang > (RING + size) / zoom) continue; // scoped in: the ring shrinks with the zoom, same size on screen
    if (ang >= bestScore) continue;
    if (raycast(e, dir, d, api.boxes())) continue; // a wall in the way: not a target
    bestScore = ang;
    best = { r, ang, dist: d, size, zoom, yawErr: wrap(Math.atan2(-dir[0], -dir[2]) - ME.yaw), pitchErr: Math.asin(dir[1]) - ME.pitch };
  }
  A.t = best;
  return best;
}

// touch look runs every drag through this: how much to slow the turn right now (1 = not at all)
export function assistSlow(api, now) {
  const k = api.strength();
  A.activeUntil = now + 350; // a thumb is steering
  if (k <= 0 || !api.ok()) return 1;
  const t = assistTarget(api, now);
  if (!t) return 1;
  const edge = (RING + t.size) / t.zoom;
  const close = 1 - Math.min(1, t.ang / edge); // 0 at the rim of the ring, 1 dead on
  return 1 - Math.min(0.6, 0.55 * k) * (0.35 + 0.65 * close);
}
// the stick counts as "doing something" too (strafing past someone)
export function assistPoke(now) { A.activeUntil = now + 350; }

// every frame: the tug. returns the target (auto fire asks who that is)
export function assistFrame(api, dt, now) {
  const k = api.strength();
  if (k <= 0 || !api.ok()) { A.t = null; A.at = now; return null; }
  const t = assistTarget(api, now);
  if (!t || now > A.activeUntil) return t;
  const zone = (PULL + t.size) / t.zoom;
  if (t.ang > zone || t.ang < 0.004) return t; // too far for a tug, or already on them
  const fall = 1 - t.ang / zone; // strongest near the middle, nothing at the rim: no yank when someone runs into the ring
  const step = Math.min(t.ang * 0.5, RATE * Math.min(1.5, k) * (0.3 + 0.7 * fall) * dt / t.zoom);
  const f = step / t.ang;
  ME.yaw += t.yawErr * f;
  ME.pitch = Math.max(-1.55, Math.min(1.55, ME.pitch + t.pitchErr * f));
  return t;
}
