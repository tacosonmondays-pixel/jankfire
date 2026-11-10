// Auto fire for touch players (touch.js loads this; a mouse never does): the gun fires by itself while the crosshair is on an
// enemy that's in range and in plain sight. it presses the same fire key the FIRE button does, after a short human-ish delay,
// so every weapon's own rules (cooldowns, ammo, reloads, spin-up, the server's hit checks) apply exactly as if a thumb did it.
// what it won't do: shoot friends, shoot through walls, no-scope a sniper for you, or play your cards.
import { ME, eye, look } from './player.js';
import { W } from './weapons.js';
import { WEAPONS } from '/shared/weapons.js';
import { raycast, rayBox } from '/shared/physics.js';

const PAD = 0.12;        // m: thumbs aren't pixel perfect, the crosshair counts a hair outside the hitbox
const MANUAL = new Set(['cig', 'lasso']); // hold-to-inhale and "fire lets go of them": yours to time
// how each kind of weapon gets its trigger pulled. anything not listed stays manual (cards, blood cross, remote, items...)
function ruleFor(id) {
  const w = WEAPONS[id];
  if (!w || MANUAL.has(id)) return null;
  if (w.kind === 'hitscan') return { mode: w.auto || w.spinup ? 'hold' : 'tap', range: Math.min(w.range || 150, 150), scope: !!(w.ads && w.ads.scope), grace: w.spinup ? 600 : 170 };
  if (w.kind === 'melee') return { mode: 'tap', range: Math.max(1.2, (w.range || 2.5) - 0.35) };
  if (w.kind === 'cone') return { mode: 'hold', range: (w.range || 10) * 0.85, grace: 200 };
  if (w.kind === 'proj') return { mode: w.auto ? 'hold' : 'tap', range: 40, grace: 170 };
  if (w.kind === 'bow') return { mode: 'draw', range: 70 };
  if (w.kind === 'beam') return { mode: 'hold', range: w.range || 100, grace: 250 };
  if (w.kind === 'zap') return { mode: 'tap', range: (w.range || 9) * 0.95 };
  return null;
}

// the enemy under the crosshair: nearest hitbox the look ray touches, nothing solid in between. { r, dist } or null
export function underCrosshair(api, maxT) {
  const o = eye(), d = look();
  let best = null;
  for (const r of api.remotes()) {
    if (!api.enemy(r)) continue;
    const dx = r.pos[0] - o[0], dz = r.pos[2] - o[2];
    if (dx * dx + dz * dz > (maxT + 3) * (maxT + 3)) continue;
    for (const hb of r.hitboxes()) {
      const h = rayBox(o, d, { min: [hb.min[0] - PAD, hb.min[1] - PAD, hb.min[2] - PAD], max: [hb.max[0] + PAD, hb.max[1] + PAD, hb.max[2] + PAD] }, best ? best.dist : maxT);
      if (h && (!best || h.t < best.dist)) best = { r, dist: h.t };
    }
  }
  if (!best) return null;
  const wall = raycast(o, d, best.dist, api.boxes());
  return wall && wall.t < best.dist - PAD * 2 ? null : best;
}

const A = { on: false, since: 0, seenAt: -1e9, react: 0, holding: false, upAt: 0, nextTap: 0, drawAt: 0, id: '', reloadAt: 0 };
function release(api) { if (A.holding) { A.holding = false; api.press(false); } A.upAt = 0; }
export function autoReset(api) { release(api); A.on = false; }

export function autoFrame(api, now) {
  if (!api.enabled() || !api.ok() || api.manual()) { autoReset(api); return; } // off, not playing, or your own thumb is on FIRE: hands off
  const id = W.cur, w = WEAPONS[id], rule = ruleFor(id);
  if (id !== A.id) { autoReset(api); A.id = id; A.nextTap = now + 220; } // new gun out: let it come up first
  if (!rule) return;
  const hit = underCrosshair(api, rule.range);
  const valid = !!hit && (!rule.scope || W.scoped); // snipers: scoped in or it's on you (no-scopes stay a skill)
  if (valid) {
    if (!A.on) { A.on = true; if (now - A.seenAt > 300) { A.since = now; A.react = 120 + Math.random() * 140; } } // a fresh target: a blink before the first shot
    A.seenAt = now;
  } else if (A.on && now - A.seenAt > (rule.grace || 0)) A.on = false;
  const armed = A.on && now - A.since >= A.react;
  // an empty mag: stop squeezing and reload once (the gun's own reload, same as tapping the ammo)
  if (w.mag && W.ammo[id] === 0 && !W.reloadId) { release(api); if (armed && now > A.reloadAt) { A.reloadAt = now + 900; api.reload(); } return; }
  if (W.reloadId === id) { release(api); return; }
  if (rule.mode === 'hold') {
    if (armed && !A.holding) { A.holding = true; api.press(true); }
    else if (!armed && A.holding) release(api);
  } else if (rule.mode === 'tap') {
    if (A.holding && now >= A.upAt) release(api);
    if (armed && valid && !A.holding && now >= A.nextTap) {
      A.holding = true; api.press(true);
      A.upAt = now + 60 + Math.random() * 40;
      A.nextTap = now + Math.max(w.rate ? 1000 / w.rate : 0, 140) + 30 + Math.random() * 70; // a finger, not a metronome
    }
  } else if (rule.mode === 'draw') { // bow: pull while they're in the crosshair, loose at full draw
    if (!A.holding && armed && valid && now >= A.nextTap) { A.holding = true; A.drawAt = now; api.press(true); }
    else if (A.holding && ((W.draw >= 1 && valid) || now - A.drawAt > 2600)) { release(api); A.nextTap = now + 250; }
  }
}
