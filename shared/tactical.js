// Plant & Defuse gunplay (this mode only): every gun has a fixed spray pattern you can learn, moving wrecks your aim,
// shift is a quiet slow walk. Shared so the client's shots, the server's hit check and the bots all use the same
// numbers. A shot's direction is worked out from the aim, the spray index, the spread and a per-shot random number that
// both sides can compute (seed + shot number), so the server can tell if a hit really followed the pattern.
import { WEAPONS } from './weapons.js';

export const TAC = {
  walkMul: 0.5, // shift = slow walk at this share of the run speed (silent: no footsteps for anyone else)
  still: 1.3, // m/s: at or under this you count as standing still
  run: 10, // m/s: full run speed (where moving inaccuracy tops out)
  runSpread: 0.07, // rad added at a full run (times the gun's `move`)
  airSpread: 0.13, // rad added in the air (jumping, falling, swinging)
  crouch: 0.7, // crouched and still: spread times this
  view: 0.45, // share of the pattern the camera kicks by (you see the climb; the rest is where shots land vs the crosshair)
  aimTol: 0.035, // server: the aim a hit claims vs the aim in the snapshot sent right before it (rad)
  dirTol: 0.006, // server: the hit's direction vs the one the pattern says (rad, rounding)
  spTol: 0.85, // server: a claimed spread can be this much under what the server thinks it should be (lag, edges)
  sleep: 1.5, // the bow's sleep arrow knocks you flat this long here (4 s everywhere else)
};

// spray patterns: keypoints [shot index, right (rad), up (rad)], straight lines between them; past the last one it
// holds there and wobbles side to side. reset: ms without firing before the next shot is the first again.
// move: how much running hurts this gun. first shots go where you aim
export const PATTERNS = {
  // the classic: straight up for ten, then it pulls left, swings back right, settles high
  ar: { reset: 380, move: 1, wob: 0.006, kp: [[0, 0, 0], [3, 0.002, 0.016], [9, 0.006, 0.07], [13, -0.02, 0.088], [18, -0.034, 0.094], [23, 0.018, 0.1], [29, 0.03, 0.104]] },
  // fast and light: a short climb, then a lazy zig-zag. made to be sprayed on the move a little
  smg: { reset: 300, move: 0.55, wob: 0.009, kp: [[0, 0, 0], [4, -0.003, 0.018], [10, 0.008, 0.038], [18, -0.012, 0.046], [26, 0.012, 0.05], [44, 0, 0.054]] },
  // the Redline climbs and drags hard right (it gets angrier at low HP: that's the fire rate, not the pattern)
  redline: { reset: 420, move: 1, wob: 0.006, kp: [[0, 0, 0], [3, 0.006, 0.02], [8, 0.03, 0.05], [14, 0.058, 0.064], [22, 0.07, 0.07], [39, 0.064, 0.078]] },
  // the minigun barely climbs but snakes side to side the whole belt
  minigun: { reset: 500, move: 0.8, wob: 0.022, kp: [[0, 0, 0], [6, 0.004, 0.012], [20, -0.012, 0.022], [60, 0.01, 0.03]] },
  // revolver taps: each shot kicks a little higher while you keep tapping fast
  revolver: { reset: 550, move: 1.3, wob: 0.002, kp: [[0, 0, 0], [1, 0.001, 0.012], [3, -0.003, 0.03], [5, 0.004, 0.044]] },
  // bolt sniper: one shot, but moving with it is hopeless
  sniper: { reset: 1100, move: 2.2, wob: 0, kp: [[0, 0, 0]] },
  shotgun: { reset: 800, move: 0.35, wob: 0, kp: [[0, 0, 0]] },
  marbles: { reset: 900, move: 0.2, wob: 0, kp: [[0, 0, 0]] },
};
const FALLBACK_MOVE = 1;
// a gun nobody wrote a pattern for (a new automatic): one made up from its id, so it's still the same every time
const made = new Map();
function madeUp(id) {
  if (made.has(id)) return made.get(id);
  const w = WEAPONS[id], r = rng(hashStr(id));
  const climb = 0.05 + r() * 0.05, side = (r() - 0.5) * 0.06, n = Math.max(4, Math.min(40, w.mag || 20));
  const p = { reset: 400, move: FALLBACK_MOVE, wob: 0.006, kp: [[0, 0, 0], [Math.ceil(n * 0.3), side * 0.2, climb * 0.7], [Math.ceil(n * 0.6), -side, climb * 0.9], [n, side, climb]] };
  made.set(id, p);
  return p;
}
export function patternOf(id) {
  if (Object.hasOwn(PATTERNS, id)) return PATTERNS[id];
  const w = WEAPONS[id];
  if (!w || w.kind !== 'hitscan') return null;
  return w.auto && w.mag ? madeUp(id) : { reset: 600, move: FALLBACK_MOVE, wob: 0, kp: [[0, 0, 0]] };
}
// where shot i of a spray goes, [right, up] in rad, relative to where you aim (i = 0: dead on)
export function patternAt(id, i) {
  const P = patternOf(id);
  if (!P || i <= 0) return [0, 0];
  const kp = P.kp, last = kp[kp.length - 1];
  if (i >= last[0]) return [last[1] + Math.sin(i * 0.9) * P.wob, last[2] + Math.sin(i * 0.37) * P.wob * 0.3];
  for (let k = 1; k < kp.length; k++) {
    if (i <= kp[k][0]) { const a = kp[k - 1], b = kp[k], t = (i - a[0]) / (b[0] - a[0] || 1); return [a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]; }
  }
  return [last[1], last[2]];
}
// the extra spread for how you're moving: speed (horizontal m/s), air (not on the floor), crouch (crouched)
export function moveSpread(id, speed, air, crouch) {
  const P = patternOf(id), mv = P ? P.move : FALLBACK_MOVE;
  if (air) return TAC.airSpread * mv;
  const k = Math.max(0, Math.min(1, (speed - TAC.still) / (TAC.run - TAC.still)));
  return TAC.runSpread * mv * k * (crouch ? 0.8 : 1);
}
// the whole spread of a shot: the gun's own (after aiming down sights and the room's hipfire setting) plus moving
export function tacSpread(id, base, speed, air, crouch) {
  const still = !air && speed <= TAC.still;
  return base * (still && crouch ? TAC.crouch : 1) + moveSpread(id, speed, air, crouch);
}

// ------------------------------------------------------------ the per-shot random number both sides know
export function hashStr(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
export function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
// a player's seed for this round (their id and the round number: nothing secret, it just can't be picked per shot)
export const shotSeed = (id, round) => (Math.imul(id | 0, 7919) + Math.imul(round | 0, 104729) + 12345) >>> 0;
// pellet k of shot q: [angle, how far out (0..1)]
export function spreadUnit(seed, q, k = 0) {
  const r = rng((seed ^ Math.imul((q | 0) + 1, 2654435761) ^ Math.imul(k + 1, 40503)) >>> 0);
  return [r() * Math.PI * 2, Math.sqrt(r())];
}
// the direction a shot goes: aim (yaw, pitch) + the pattern offset (already scaled) + the spread for pellet k
export function shotDir(yaw, pitch, off, sp, seed, q, k = 0) {
  const y = yaw - off[0], p = Math.max(-1.55, Math.min(1.55, pitch + off[1]));
  const cp = Math.cos(p), d = [-Math.sin(y) * cp, Math.sin(p), -Math.cos(y) * cp];
  if (!(sp > 0)) return d;
  const up = Math.abs(d[1]) < 0.99 ? [0, 1, 0] : [1, 0, 0];
  let r = [d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0]];
  const rl = Math.hypot(...r); r = r.map((x) => x / rl);
  const u = [r[1] * d[2] - r[2] * d[1], r[2] * d[0] - r[0] * d[2], r[0] * d[1] - r[1] * d[0]];
  const [a, f] = spreadUnit(seed, q, k), m = f * sp;
  const o = [d[0] + (r[0] * Math.cos(a) + u[0] * Math.sin(a)) * m, d[1] + (r[1] * Math.cos(a) + u[1] * Math.sin(a)) * m, d[2] + (r[2] * Math.cos(a) + u[2] * Math.sin(a)) * m];
  const l = Math.hypot(...o);
  return o.map((x) => x / l);
}
// the share of the pattern that moves the bullets (the camera takes the rest: TAC.view)
export const shotOffset = (id, i) => { const p = patternAt(id, i); return [p[0] * (1 - TAC.view), p[1] * (1 - TAC.view)]; };
export const angleBetween = (a, b) => Math.acos(Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2])));
