// story bosses (OVERDUE): the referee's half of a boss fight, on the story room (server/storyref.js installs it). the
// room owns his HP, layers, parts, phases and attacks; the client only shows them (public/js/story/bossfight.js).
//   a boss is a story enemy with sk.b (its fight state). its def comes from the story content (shared/story/refsys.js
//   builds it from content/bosses.js + the model's parts file), cleaned again here:
//     def.boss = { id, hp, health, crit, phases: [{ name, to, line, moves: [..], rest }], parts }
//       hp      the whole pool (armour + health). health: the bar under the armour (the plate is on while hp > health)
//       phases  to = the hp % the phase ends at; moves = his attacks in it; rest = seconds he sits still (the coffee break)
//       parts   c_<who>.parts.json: part boxes, the body capsule, clip marks and offsets (root space, front -z)
//   hits: a 'hit' message's ray is tested against his parts here (the client only says "i hit him"): the weak point
//   (the heart, once the plate is off; the slot while it's open) crits, the plate takes it while it's on, anything else
//   is soft. his room HP stays 1..100 like everyone's; the real numbers go out in the events
//   events (room.onStory): hit { part, crit, hp, max } · phase { phase, name, invuln } · part { part, state } ·
//   act { move, clip } · bfx { k: 'staple', at, n } · defeat (the fight's end: he is not killed, the story takes over)
//   held (sk.hold: a cutscene, a talk) or between phases he can't be hurt and does nothing
import { FLAGS } from '../shared/weapons.js';
import { raycast, movePlayer, PH } from '../shared/physics.js';

export const BOSS = {
  soft: 0.5, // off the weak point ("only the clock face takes full damage"; the design gives no number)
  maxHit: 1000, cut: 1, rest: 15, // one hit's cap · seconds a phase change holds him at least · the coffee break
  slack: 0.12, bodySlack: 0.35, // metres added round a part / the body when checking a shot
  turn: 2.6, aim: 5, walk: 2.4, near: 7, far: 10, // rad/s idle and while aiming · m/s · he closes in past `far`, stops at `near`
  gap: [1.8, 3], wet: 1.5, first: 2.5, // seconds between attacks (soaked clockwork runs slow: x wet)
  shots: 12, // staples in the air at once
  moves: {
    staple: { clip: 'ot_staple', len: 1.6, lock: 'clack2', fire: 'fire', speed: 38, dmg: 30, life: 2.2, kb: 5, w: 'nailgun' },
    fan: { clip: 'ot_fan', len: 2.2, lock: 'clack10', fire: 'fan', n: 5, step: 0.25, h: 1.3, speed: 38, dmg: 22, life: 2.2, kb: 4, w: 'nailgun' },
    slam: { clip: 'ot_slam', len: 2.4, fire: 'land', ring: 12, ringT: 0.9, air: 0.7, dmg: 40, kb: 7, up: 9, w: 'story' },
    punchin: { clip: 'ot_punchin', len: 2.6, open: 'slotOpen', fire: 'grab', close: 'slotClose', commit: 0.35, reach: 5.5, cone: 0.9, dmg: 55, kb: 14, up: 5, w: 'story' },
  },
};
// his clips' marks if the parts file didn't come (the same numbers as c_overtime.parts.json)
const MARKS0 = { ot_staple: { clack2: 0.7, fire: 0.85 }, ot_fan: { clack10: 1.3, fan: 1.6 }, ot_slam: { land: 1.42 }, ot_punchin: { slotOpen: 0.35, grab: 1.1, slotClose: 2.3 } };

const fin = Number.isFinite;
const v3 = (a, max) => (Array.isArray(a) && a.length === 3 && a.every((x) => fin(x) && Math.abs(x) <= max) ? a.slice() : null);
const isName = (s) => typeof s === 'string' && /^[a-zA-Z0-9_]{1,24}$/.test(s);
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ss = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const wrapA = (a) => { while (a > Math.PI) a -= Math.PI * 2; while (a < -Math.PI) a += Math.PI * 2; return a; };

// the parts file, kept only as far as it makes sense (it's data from the model pipeline, but the room trusts nothing)
export function cleanParts(j) {
  if (!j || typeof j !== 'object') return null;
  const out = { parts: {}, body: null, markers: {}, marks: {}, clips: {} };
  for (const [k, p] of Object.entries(j.parts && typeof j.parts === 'object' ? j.parts : {}).slice(0, 24)) {
    const c = p && v3(p.c, 50), h = p && v3(p.h, 20);
    if (isName(k) && c && h && h.every((x) => x > 0)) out.parts[k] = { c, h, joint: isName(p.joint) ? p.joint : '' };
  }
  const b = j.body;
  if (b && fin(b.r) && b.r > 0 && b.r < 20 && fin(b.h) && b.h > 0 && b.h < 60 && v3(b.c, 50)) out.body = { r: b.r, h: b.h, c: b.c.slice() };
  for (const [k, p] of Object.entries(j.markers && typeof j.markers === 'object' ? j.markers : {}).slice(0, 24)) { const c = v3(p, 50); if (isName(k) && c) out.markers[k] = c; }
  for (const [k, ms] of Object.entries(j.marks && typeof j.marks === 'object' ? j.marks : {}).slice(0, 32)) {
    if (!isName(k) || !ms || typeof ms !== 'object') continue;
    const o = {}; for (const [n, t] of Object.entries(ms).slice(0, 24)) if (isName(n) && fin(t) && t >= 0 && t < 60) o[n] = t;
    out.marks[k] = o;
  }
  for (const [k, c] of Object.entries(j.clips && typeof j.clips === 'object' ? j.clips : {}).slice(0, 32)) {
    if (!isName(k) || !c || !Array.isArray(c.t) || c.t.length > 200 || !c.t.every((x) => fin(x) && x >= 0)) continue;
    const o = { t: c.t.slice(), dy: null, gunR: null };
    if (Array.isArray(c.body_dy) && c.body_dy.length === c.t.length && c.body_dy.every((x) => fin(x) && Math.abs(x) < 20)) o.dy = c.body_dy.slice();
    if (Array.isArray(c.gunR) && c.gunR.length === c.t.length && c.gunR.every((x) => v3(x, 50))) o.gunR = c.gunR.map((x) => x.slice());
    out.clips[k] = o;
  }
  return out.body ? out : null;
}
// a boss def as the room keeps it. null = not a boss anyone can fight
export function cleanBoss(d) {
  if (!d || typeof d !== 'object' || !isName(d.id) || !fin(d.hp) || d.hp < 1 || !Array.isArray(d.phases) || !d.phases.length) return null;
  const hp = Math.min(1e6, d.hp), phases = [];
  let last = 100;
  for (const p of d.phases.slice(0, 8)) {
    if (!p || !fin(p.to) || p.to < 0 || p.to >= last) return null; // (each phase ends lower than the one before)
    last = p.to;
    phases.push({ name: typeof p.name === 'string' ? p.name.slice(0, 40) : '', line: typeof p.line === 'string' ? p.line.slice(0, 120) : '', to: p.to,
      moves: (Array.isArray(p.moves) ? p.moves : []).filter((m) => Object.hasOwn(BOSS.moves, m)).slice(0, 8), rest: fin(p.rest) && p.rest > 0 ? Math.min(120, p.rest) : 0 });
  }
  phases[phases.length - 1].to = 0;
  return { id: d.id, hp, health: fin(d.health) && d.health > 0 && d.health < hp ? d.health : hp, crit: fin(d.crit) ? clamp(d.crit, 1, 10) : 2, phases, parts: cleanParts(d.parts) };
}

// ---------------------------------------------------------------- where his parts are right now (root space)
const lerp = (a, b, k) => a + (b - a) * k;
function sample(c, key, t) {
  const ts = c.t, a = c[key]; if (!a) return null;
  let i = 0; while (i < ts.length - 1 && ts[i + 1] <= t) i++;
  const j = Math.min(ts.length - 1, i + 1), k = ts[j] > ts[i] ? clamp((t - ts[i]) / (ts[j] - ts[i]), 0, 1) : 0;
  return Array.isArray(a[i]) ? a[i].map((x, n) => lerp(x, a[j][n], k)) : lerp(a[i], a[j], k);
}
// the clip he's in and how far into it: an attack, or sitting with his coffee
function clipOf(B) {
  if (B.act) return [BOSS.moves[B.act.k].clip, B.act.t];
  if (B.state === 'rest') return ['ot_coffee', B.t - B.restT];
  return null;
}
function poseOf(B) {
  const P = B.def.parts, cl = P && clipOf(B), c = cl && P.clips[cl[0]];
  return { dy: c ? sample(c, 'dy', cl[1]) || 0 : 0, gunR: c ? sample(c, 'gunR', cl[1]) : null };
}
const toLocal = (b, p) => { const c = Math.cos(b.yaw), s = Math.sin(b.yaw), x = p[0] - b.pos[0], z = p[2] - b.pos[2]; return [x * c - z * s, p[1] - b.pos[1], x * s + z * c]; };
const dirLocal = (b, d) => { const c = Math.cos(b.yaw), s = Math.sin(b.yaw); return [d[0] * c - d[2] * s, d[1], d[0] * s + d[2] * c]; };
const toWorld = (b, p) => { const c = Math.cos(b.yaw), s = Math.sin(b.yaw); return [b.pos[0] + p[0] * c + p[2] * s, b.pos[1] + p[1], b.pos[2] - p[0] * s + p[2] * c]; };
// a ray against a box (centre, half extents, grown by g): the distance in, or -1
function rayAabb(o, d, c, h, g) {
  let t0 = 0, t1 = 1e9;
  for (let a = 0; a < 3; a++) {
    const lo = c[a] - h[a] - g, hi = c[a] + h[a] + g;
    if (Math.abs(d[a]) < 1e-9) { if (o[a] < lo || o[a] > hi) return -1; continue; }
    let a0 = (lo - o[a]) / d[a], a1 = (hi - o[a]) / d[a]; if (a0 > a1) { const x = a0; a0 = a1; a1 = x; }
    if (a0 > t0) t0 = a0; if (a1 < t1) t1 = a1; if (t0 > t1) return -1;
  }
  return t0;
}
// a ray against the body (an upright cylinder is close enough to his capsule)
function rayBody(o, d, body, dy, g) {
  const r = body.r + g, y0 = body.c[1] + dy - body.h / 2 - g, y1 = body.c[1] + dy + body.h / 2 + g;
  const ox = o[0] - body.c[0], oz = o[2] - body.c[2], a = d[0] * d[0] + d[2] * d[2], bq = ox * d[0] + oz * d[2], cq = ox * ox + oz * oz - r * r;
  let t = 0;
  if (cq > 0) { if (a < 1e-9) return -1; const disc = bq * bq - a * cq; if (disc < 0) return -1; t = (-bq - Math.sqrt(disc)) / a; if (t < 0) return -1; }
  const y = o[1] + d[1] * t;
  if (y >= y0 && y <= y1) return t;
  if (Math.abs(d[1]) < 1e-9) return -1;
  const tc = ((d[1] > 0 ? y0 : y1) - o[1]) / d[1]; if (tc < t) return -1; // (in through the top or the bottom)
  const x = ox + d[0] * tc, z = oz + d[2] * tc;
  return x * x + z * z <= r * r ? tc : -1;
}

export function installStoryBoss(Room) {
  const P = Room.prototype;
  const ev = (room, o) => { if (room.onStory) room.onStory(o); };
  const marksOf = (B, clip) => ({ ...(MARKS0[clip] || {}), ...((B.def.parts && B.def.parts.marks[clip]) || {}) });
  const slotOpen = (B) => { const A = B.act, m = A && BOSS.moves[A.k]; return !!(m && m.open && A.t >= A.marks[m.open] && A.t < A.marks[m.close]); };

  // a boss's fight state on a story enemy (storySpawn calls it). false = the def isn't a boss
  P.bossInit = function (b, d) {
    const def = cleanBoss(d); if (!def) return false;
    b.sk.max = def.hp; b.sk.boss = true;
    b.sk.b = { def, id: def.id, hp: def.hp, plate: def.health < def.hp, phase: 0, state: 'fight', t: 0, cutT: 0, restT: 0, next: BOSS.first, act: null, shots: [], ring: null, last: '', want: '', home: b.pos.slice(), ray: null };
    b.ai.nextShot = Infinity; b.vel = [0, 0, 0];
    return true;
  };
  // which part a shot from o along d (world) lands on: { part, t } or null (it doesn't cross him at all).
  // the plate covers the heart while it's on; the heart and the slot only count from the front; soft bits (tie, card,
  // cables) are just body
  P.bossRay = function (b, o, d) {
    const B = b.sk.b, Pt = B.def.parts; if (!Pt) return { part: 'body', t: 0 };
    const lo = toLocal(b, o), ld = dirLocal(b, d), pose = poseOf(B), g = BOSS.slack, front = ld[2] > 0.05;
    const at = (k) => {
      const p = Pt.parts[k]; if (!p) return -1;
      const c = k === 'gunR' && pose.gunR ? pose.gunR : [p.c[0], p.c[1] + pose.dy, p.c[2]];
      return rayAabb(lo, ld, c, p.h, g);
    };
    let t;
    if (front && B.plate && (t = at('plate')) >= 0) return { part: 'plate', t };
    if (front && !B.plate && (t = at('heart')) >= 0) return { part: 'heart', t };
    if (front && slotOpen(B) && ((t = at('slot')) >= 0 || (t = at('heart')) >= 0)) return { part: 'slot', t }; // shoot inside it
    for (const k of ['head', 'gunR', 'gunL']) if ((t = at(k)) >= 0) return { part: k, t };
    t = rayBody(lo, ld, Pt.body, pose.dy, BOSS.bodySlack);
    return t >= 0 ? { part: 'body', t } : null;
  };
  // a hit on a boss: the room works out the part itself and takes no headshots from the client
  const onHit0 = P.onHit;
  P.onHit = function (p, m) {
    const t = this.mode === 'story' && m ? this.players.get(m.to) : null, B = t && t.sk && t.sk.b;
    if (!B) return onHit0.call(this, p, m);
    const d = v3(m.d, 2), l = d ? Math.hypot(d[0], d[1], d[2]) : 0;
    if (!d || l < 0.5 || !p.alive || !t.alive) return;
    const h = this.bossRay(t, [p.pos[0], p.pos[1] + PH.eye, p.pos[2]], d.map((x) => x / l));
    if (!h) return; // the shot doesn't cross him
    B.ray = h;
    try { onHit0.call(this, p, { ...m, h: 0 }); } finally { B.ray = null; }
  };
  // damage to a boss (storyref's damage hands it over). amt is in real HP
  P.bossDamage = function (t, amt, attacker, w, hs, from) {
    const B = t.sk.b, D = B.def;
    if (!fin(amt) || amt <= 0 || !t.alive) return false;
    if ((B.state !== 'fight' && B.state !== 'rest') || t.sk.hold) return false; // a cutscene, between phases, or done
    if (this.hitBlocked(t, attacker, w, from)) return false;
    const part = B.ray ? B.ray.part : 'blast', crit = part === 'heart' || part === 'slot'; // (no ray: explosions, fire, scripted hurts)
    const mul = crit ? D.crit : B.plate && (part === 'plate' || part === 'blast') ? 1 : BOSS.soft;
    // a phase never skips: this hit stops at the phase's end, and at the plate
    const floor = Math.max(D.hp * D.phases[B.phase].to / 100, B.plate ? D.health : 0), hp0 = B.hp;
    B.hp = Math.max(floor, B.hp - Math.min(amt, BOSS.maxHit) * mul);
    const dealt = hp0 - B.hp; if (dealt <= 0) return false;
    t.hp = Math.max(1, 100 * B.hp / D.hp); // (he never dies in the room: the story ends the fight)
    t.lastHs = false;
    this.tag(t, attacker, w);
    this.broadcast({ t: 'dmg', to: t.id, from: attacker ? attacker.id : 0, a: Math.round(Math.min(dealt, 999)), w, hs: crit });
    ev(this, { type: 'hit', t, by: attacker, w, dmg: dealt, head: false, part, crit, hp: Math.round(B.hp), max: D.hp });
    if (B.plate && B.hp <= D.health) { B.plate = false; ev(this, { type: 'part', t, part: 'plate', state: 'plate_off' }); }
    if (B.hp <= D.hp * D.phases[B.phase].to / 100) {
      if (B.phase >= D.phases.length - 1) this.bossDefeat(t, attacker, w); else this.bossPhase(t, B.phase + 1);
    }
    return true;
  };
  // the next phase: whatever he was doing stops, and he can't be hurt until the client's cutscene lets him go
  P.bossPhase = function (b, i) {
    const B = b.sk.b; if (i <= B.phase || i >= B.def.phases.length) return;
    B.phase = i; B.act = null; B.shots.length = 0; B.ring = null; B.state = 'cut'; B.cutT = B.t; b.vel = [0, 0, 0];
    const ph = B.def.phases[i];
    ev(this, { type: 'phase', t: b, phase: i, name: ph.name, line: ph.line, invuln: true });
  };
  // the end of the fight: he stops for good. nobody dies here: the story does the rest (the rip, the retreat)
  P.bossDefeat = function (b, by, w) {
    const B = b.sk.b; if (B.state === 'done') return;
    B.state = 'done'; B.act = null; B.shots.length = 0; B.ring = null; b.sk.hold = true; b.vel = [0, 0, 0];
    ev(this, { type: 'defeat', t: b, by, w });
  };

  // ---------------------------------------------------------------- his turn, every room tick
  const targetOf = (room, b) => { let best = null, bd = 1e9; for (const p of room.players.values()) { if (p === b || !p.alive || room.friendly(b, p)) continue; const d = Math.hypot(p.pos[0] - b.pos[0], p.pos[2] - b.pos[2]); if (d < bd) { bd = d; best = p; } } return best; };
  const face = (b, t, rate, dt) => { const want = Math.atan2(-(t.pos[0] - b.pos[0]), -(t.pos[2] - b.pos[2])); b.yaw += clamp(wrapA(want - b.yaw), -rate * dt, rate * dt); };
  const low = (p) => !!(p.f & (FLAGS.SLIDE | FLAGS.CROUCH));
  // where the right stapler's muzzle is (the clip's offset on top of its rest spot)
  function muzzle(b, B) {
    const Pt = B.def.parts, mz = Pt && Pt.markers.muzzleR, g0 = Pt && Pt.parts.gunR, pose = poseOf(B);
    if (!mz) return [b.pos[0], b.pos[1] + 3, b.pos[2]];
    const g = pose.gunR && g0 ? [pose.gunR[0] - g0.c[0], pose.gunR[1] - g0.c[1], pose.gunR[2] - g0.c[2]] : [0, pose.dy, 0];
    return toWorld(b, [mz[0] + g[0], mz[1] + g[1], mz[2] + g[2] - 0.6]); // (a little out in front, clear of his own arm)
  }
  function shoot(room, b, B, m, from, to) {
    if (B.shots.length >= BOSS.shots) return;
    const d = [to[0] - from[0], to[1] - from[1], to[2] - from[2]], l = Math.hypot(d[0], d[1], d[2]); if (l < 0.01) return;
    B.shots.push({ p: from.slice(), d: d.map((x) => x / l), left: m.life, m });
  }
  // staples fly; a miss stays in whatever it hit (the client draws it: his misses are your grapple points)
  function stepShots(room, b, B, dt) {
    for (let i = B.shots.length - 1; i >= 0; i--) {
      const s = B.shots[i], m = s.m, len = m.speed * dt, wall = raycast(s.p, s.d, len, room.boxes), reach = wall ? wall.t : len;
      let hit = null;
      for (const p of room.players.values()) {
        if (p === b || !p.alive || room.friendly(b, p)) continue;
        const k = clamp((p.pos[0] - s.p[0]) * s.d[0] + (p.pos[1] + 0.9 - s.p[1]) * s.d[1] + (p.pos[2] - s.p[2]) * s.d[2], 0, reach);
        const q = [s.p[0] + s.d[0] * k, s.p[1] + s.d[1] * k, s.p[2] + s.d[2] * k], top = low(p) ? 0.95 : PH.height;
        if (Math.hypot(q[0] - p.pos[0], q[2] - p.pos[2]) < 0.6 && q[1] > p.pos[1] - 0.15 && q[1] < p.pos[1] + top + 0.15) { hit = p; break; }
      }
      if (hit) { room.damage(hit, m.dmg, b, m.w); room.knock(hit, [s.d[0] * m.kb, 2, s.d[2] * m.kb], m.w); B.shots.splice(i, 1); continue; }
      if (wall) { ev(room, { type: 'bfx', t: b, k: 'staple', at: [s.p[0] + s.d[0] * wall.t, s.p[1] + s.d[1] * wall.t, s.p[2] + s.d[2] * wall.t], n: wall.normal || [0, 1, 0] }); B.shots.splice(i, 1); continue; }
      for (let a = 0; a < 3; a++) s.p[a] += s.d[a] * len;
      if ((s.left -= dt) <= 0) B.shots.splice(i, 1);
    }
  }
  // the slam's ring races out over the floor: it gets whoever is standing on it as it passes (be in the air)
  function stepRing(room, b, B, dt) {
    const R = B.ring, m = BOSS.moves.slam; if (!R) return;
    const r0 = R.r; R.t += dt; R.r = 1 + ss(R.t / m.ringT) * (m.ring - 1);
    for (const p of room.players.values()) {
      if (p === b || !p.alive || R.hit.has(p.id) || room.friendly(b, p)) continue;
      const dx = p.pos[0] - R.at[0], dz = p.pos[2] - R.at[2], d = Math.hypot(dx, dz), up = p.pos[1] - R.at[1];
      if (d < r0 || d > R.r) continue;
      R.hit.add(p.id); // (it passes you once, hit or not)
      if (up >= m.air || up < -2) continue; // jumped it (or on another floor)
      room.damage(p, m.dmg, b, m.w);
      room.knock(p, [d > 0.1 ? dx / d * m.kb : 0, m.up, d > 0.1 ? dz / d * m.kb : 0], m.w);
    }
    if (R.t >= m.ringT) B.ring = null;
  }
  function startAct(room, b, B, k, tgt) {
    const m = BOSS.moves[k];
    B.act = { k, t: 0, marks: marksOf(B, m.clip), aim: null, fired: false, tgt: tgt.id };
    B.last = k; B.want = '';
    ev(room, { type: 'act', t: b, move: k, clip: m.clip });
  }
  function stepAct(room, b, B, dt) {
    const A = B.act, m = BOSS.moves[A.k], t0 = A.t, tgt = room.players.get(A.tgt);
    A.t += dt;
    const at = (name) => { const x = A.marks[name]; return fin(x) && t0 < x && A.t >= x; }; // this tick crossed that mark
    const live = tgt && tgt.alive;
    if (A.k === 'staple' || A.k === 'fan') {
      if (live && !A.aim) face(b, tgt, BOSS.aim, dt);
      if (live && at(m.lock)) A.aim = [tgt.pos[0], tgt.pos[1], tgt.pos[2]]; // where you were on the last clack: strafe now
      if (at(m.fire) && !A.fired) {
        A.fired = true;
        const from = muzzle(b, B), aim = A.aim || [b.pos[0] - Math.sin(b.yaw) * 12, b.pos[1], b.pos[2] - Math.cos(b.yaw) * 12];
        if (A.k === 'staple') shoot(room, b, B, m, from, [aim[0], aim[1] + 0.9, aim[2]]);
        else { // the fan: five staples flat across the floor at chest height (slide under it)
          const dx = aim[0] - from[0], dz = aim[2] - from[2], d = Math.max(4, Math.hypot(dx, dz)), a0 = Math.atan2(dx, dz);
          for (let i = 0; i < m.n; i++) { const a = a0 + (i - (m.n - 1) / 2) * m.step; shoot(room, b, B, m, from, [from[0] + Math.sin(a) * d, aim[1] + m.h, from[2] + Math.cos(a) * d]); }
        }
      }
    } else if (A.k === 'slam') {
      if (at(m.fire)) B.ring = { at: b.pos.slice(), t: 0, r: 0, hit: new Set() };
    } else if (A.k === 'punchin') {
      if (live && A.t < A.marks[m.fire] - m.commit) face(b, tgt, BOSS.aim, dt); // he commits before the grab: dash sideways
      if (at(m.fire) && live) {
        const dx = tgt.pos[0] - b.pos[0], dz = tgt.pos[2] - b.pos[2], d = Math.hypot(dx, dz), off = Math.abs(wrapA(Math.atan2(-dx, -dz) - b.yaw));
        if (d <= m.reach && off <= m.cone && Math.abs(tgt.pos[1] - b.pos[1]) < 3) {
          room.damage(tgt, m.dmg, b, m.w);
          room.knock(tgt, [-Math.sin(b.yaw) * m.kb, m.up, -Math.cos(b.yaw) * m.kb], m.w);
        }
      }
    }
    if (A.t >= m.len) { B.act = null; const [g0, g1] = BOSS.gap; B.next = B.t + (g0 + Math.random() * (g1 - g0)) * (Date.now() < (b.soakUntil || 0) ? BOSS.wet : 1); }
  }
  // what he does next: close in for the grab or the slam, staples from range, never the same thing three times
  function pick(B, d) {
    const ms = B.def.phases[B.phase].moves; if (!ms.length) return '';
    if (B.want && ms.includes(B.want)) return B.want; // (tests / scripts ask for one)
    const ok = ms.filter((k) => (k === 'punchin' ? d <= BOSS.moves.punchin.reach + 1.5 : k === 'slam' ? d <= BOSS.moves.slam.ring : true));
    const pool = ok.length > 1 ? ok.filter((k) => k !== B.last) : ok.length ? ok : ms.filter((k) => k !== 'punchin');
    return pool.length ? pool[(Math.random() * pool.length) | 0] : '';
  }
  P.bossStep = function (b, dt) {
    const B = b.sk.b, v = b.vel;
    v[0] = 0; v[2] = 0; // nothing shoves him around
    if (B.state !== 'done' && !b.sk.hold) {
      B.t += dt;
      const tgt = targetOf(this, b);
      if (B.state === 'cut') { // the client's cutscene holds him (sk.hold); after it, a beat, then he's back
        if (B.t - B.cutT >= BOSS.cut) { const ph = B.def.phases[B.phase]; B.state = ph.rest ? 'rest' : 'fight'; B.restT = B.t; B.next = B.t + BOSS.first; ev(this, { type: 'phase', t: b, phase: B.phase, name: ph.name, line: '', invuln: false }); }
      } else if (B.state === 'rest') { // his break: free hits, then the next phase whatever his HP
        if (B.t - B.restT >= (B.def.phases[B.phase].rest || BOSS.rest)) this.bossPhase(b, B.phase + 1);
      } else {
        stepShots(this, b, B, dt); stepRing(this, b, B, dt);
        if (B.act) stepAct(this, b, B, dt);
        else if (tgt) {
          face(b, tgt, BOSS.turn, dt);
          const dx = tgt.pos[0] - b.pos[0], dz = tgt.pos[2] - b.pos[2], d = Math.hypot(dx, dz);
          B.go = d > BOSS.far ? true : d < BOSS.near ? false : !!B.go;
          if (B.go && b.onGround) { v[0] = dx / d * BOSS.walk; v[2] = dz / d * BOSS.walk; }
          if (B.t >= B.next) { const k = pick(B, d); if (k) startAct(this, b, B, k, tgt); else B.next = B.t + 1; }
        }
      }
    } else if (B.act || B.shots.length || B.ring) { B.act = null; B.shots.length = 0; B.ring = null; } // held mid-attack: it's off
    v[1] = Math.min(0, v[1]) - 26 * dt; // (and nothing launches him)
    const res = movePlayer(b.pos, v, dt, this.boxes, b.onGround);
    b.onGround = !!res.ground && v[1] <= 0.01;
    if (b.onGround) b.ground = b.pos.slice();
    b.f = 0;
    if (b.pos[1] < this.map.killY) { b.pos = B.home.slice(); b.vel = [0, 0, 0]; } // fell out of the world: back to his mark
  };
}
