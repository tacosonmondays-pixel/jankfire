// The Tall Guy From HR (Scary Forest): the server owns him, so everyone sees the same one in the same place.
// A visit: he turns up 36-52 m from someone (whoever is most on their own), out of their sight, between the trees.
// Each tick: who has him in view (he can't move while anyone does), who is staring right at him (their meter fills, faster
// up close). Nobody looking: every second or so he blinks a few metres closer to his target. Full meter, or he reaches
// his target unseen: he takes them (a death credited to him, or a transfer somewhere awful). Then he leaves for a while.
// Bots know the rules: they don't stare, they glance at him to freeze him when he's close behind them, and they back off.
import { HR, hrSight, stareRate } from '../shared/hr.js';
import { raycast, query } from '../shared/physics.js';
import { outOfBounds } from '../shared/bounds.js';
import { PH } from '../shared/physics.js';

const now = () => Date.now();
const rr = ([a, b]) => a + Math.random() * (b - a);
const r2 = (x) => Math.round(x * 100) / 100;
const eye = (p) => [p.pos[0], p.pos[1] + PH.eye, p.pos[2]];
const nv = (p) => !!p.nvOn; // night vision goggles down (server/gear.js): you see him from further out, and he gets you from further out
const qb = [];

export const hrSetting = (room) => (Object.hasOwn(HR.every, room.cfg.hr) ? room.cfg.hr : 'on');
// test knobs: JF_HR_FIRST=2 (seconds to his first visit), JF_HR_EVERY=10 (seconds between visits)
const T_FIRST = Number(process.env.JF_HR_FIRST), T_EVERY = Number(process.env.JF_HR_EVERY);
const nextVisit = (room, n, first) => {
  const ev = HR.every[hrSetting(room)];
  if (!ev) return Infinity;
  if (first) return n + (Number.isFinite(T_FIRST) ? T_FIRST : HR.first + rr([0, 15])) * 1000;
  return n + (Number.isFinite(T_EVERY) ? T_EVERY : rr(ev)) * 1000;
};
// a mode where he's welcome: a live round on a map that has him. (coop has its own monsters; training is for training)
function liveRound(room, n) {
  if (!room.map.hr || room.mode === 'coop' || room.mode === 'training' || !HR.every[hrSetting(room)]) return false;
  if (room.round && room.round.over) return false;
  if (room.bomb && (room.bomb.between || room.bomb.ph === 'done')) return false;
  return true;
}
// can he stand here? on the forest floor (not a roof, a rock, the lake), clear of trunks, inside the property line
function standOk(room, x, z) {
  const map = room.map, b = map.bounds;
  if (outOfBounds(map, [x, 0, z]) || x < b[0] + 3 || x > b[2] - 3 || z < b[1] + 3 || z > b[3] - 3) return null;
  if ((map.hr.keepOut || []).some((k) => x > k[0] && x < k[2] && z > k[1] && z < k[3])) return null;
  const down = raycast([x, 6, z], [0, -1, 0], 12, room.boxes);
  if (!down || down.point[1] > 0.3 || down.point[1] < -0.1) return null;
  for (const q of query(room.boxes, x - 0.6, z - 0.6, x + 0.6, z + 0.6, qb)) if (q.max[1] > down.point[1] + 0.2 && q.min[1] < HR.height && q.max[0] > x - 0.6 && q.min[0] < x + 0.6 && q.max[2] > z - 0.6 && q.min[2] < z + 0.6) return null;
  return [x, down.point[1], z];
}
// is anyone (alive, in range, facing him, nothing in between) looking his way?
function lineClear(room, e, h) { return !raycast(e, h.dir, Math.max(0, h.d - 0.8), room.boxes); }
function sights(room, at) {
  const out = [];
  for (const p of room.players.values()) {
    if (!p.alive || (p.isBot && p.ai && p.ai.dummy)) continue;
    const e = eye(p), h = hrSight(e, p.yaw || 0, p.pitch || 0, at, nv(p));
    if ((h.view || h.stare) && lineClear(room, e, h)) out.push([p, h]);
  }
  return out;
}
// who he's after: the loneliest (furthest from anyone else), humans a bit more than bots
function pickTarget(room) {
  const alive = [...room.players.values()].filter((p) => p.alive && !(p.isBot && p.ai && p.ai.dummy) && !p.trap && (!process.env.JF_HR_BOTS || p.isBot)); // JF_HR_BOTS: test knob, he only goes after bots
  let best = null, bs = -1;
  for (const p of alive) {
    let lone = 60;
    for (const q of alive) if (q !== p) lone = Math.min(lone, Math.hypot(q.pos[0] - p.pos[0], q.pos[2] - p.pos[2]));
    const s = lone * (p.isBot ? 1 : 1.6) + Math.random() * 12;
    if (s > bs) { bs = s; best = p; }
  }
  return best;
}
// would t see him standing at s if they looked that way? (not behind a rock or the toilet: he wants to be found)
function openTo(room, t, s) { const e = eye(t); return lineClear(room, e, hrSight(e, 0, 0, s, false)); }
// somewhere out of everyone's sight, far from the target, ideally right next to a trunk (between the trees)
function arrivalSpot(room, t) {
  let best = null, bs = -1;
  for (let i = 0; i < 60; i++) {
    const a = Math.random() * Math.PI * 2, d = rr(HR.far);
    const s = standOk(room, t.pos[0] + Math.cos(a) * d, t.pos[2] + Math.sin(a) * d);
    if (!s || sights(room, s).length) continue;
    let tree = 0;
    for (const q of query(room.boxes, s[0] - 2.5, s[2] - 2.5, s[0] + 2.5, s[2] + 2.5, qb)) if (/bark|birch/.test(q.mat)) tree++;
    const score = Math.min(3, tree) + Math.random() + (openTo(room, t, s) ? 5 : 0); // somewhere you'd see him if you turned round
    if (score > bs) { bs = score; best = s; }
  }
  return best;
}
function leave(room, why) {
  const h = room.hr;
  if (h.on) room.broadcast({ t: 'hr', on: 0, why });
  h.on = false; h.target = 0; h.stare.clear();
  h.next = nextVisit(room, now(), false);
}
// he's got them: a death credited to him, or a transfer somewhere awful (a death everywhere else he can't send you)
function take(room, p) {
  const h = room.hr, awful = room.map.hr.awful || [];
  room.broadcast({ t: 'hrx', id: p.id, p: h.p.map(r2) });
  if (Math.random() > HR.takeKill && awful.length && !(room.bomb && room.bomb.carrier === p.id)) {
    const w = awful[(Math.random() * awful.length) | 0];
    p.pos = w.p.slice(); p.vel = [0, 0, 0]; p.oobAt = 0;
    const send = p.ws && p.ws.readyState === 1 ? (o) => p.ws.send(JSON.stringify(o)) : null;
    if (send) send({ t: 'hrtp', p: w.p, where: w.name });
    room.broadcast({ t: 'chat', id: 0, m: `${p.name} got transferred to ${w.name.toLowerCase()}` });
  } else room.kill(p, null, 'hr');
  leave(room, 'took');
}

export function tickHR(room, dt) {
  const n = now();
  if (!room.hr || room.hr.map !== room.cfg.map) {
    if (room.hr && room.hr.on) room.broadcast({ t: 'hr', on: 0 });
    room.hr = { map: room.cfg.map, on: false, next: nextVisit(room, n, true), stare: new Map(), sendT: 0 };
  }
  const h = room.hr;
  if (!room.map.hr) return;
  if (h.setting !== hrSetting(room)) { h.setting = hrSetting(room); if (h.on && !HR.every[h.setting]) leave(room, 'off'); h.next = Math.min(h.next, nextVisit(room, n, false)); if (!HR.every[h.setting]) h.next = Infinity; }
  if (room.round && room.round.t0 && h.roundT0 !== room.round.t0) { h.roundT0 = room.round.t0; if (h.on) leave(room, 'round'); h.next = nextVisit(room, n, true); } // a fresh round: give everyone a moment first
  if (!liveRound(room, n)) { if (h.on) leave(room, 'round'); return; }
  if (!h.on) {
    if (n < h.next || !room.players.size) return;
    const t = pickTarget(room), s = t && arrivalSpot(room, t);
    if (!s) { h.next = n + 3000; return; }
    Object.assign(h, { on: true, p: s, target: t.id, born: n, stepT: rr(HR.stepEvery) + 1.5, pose: (Math.random() * 1000) | 0, yaw: Math.atan2(s[0] - t.pos[0], s[2] - t.pos[2]) });
    h.stare.clear();
    h.sendT = 0;
    return;
  }
  const t = room.players.get(h.target);
  if (!t || !t.alive) { leave(room, 'gone'); return; }
  const seen = sights(room, h.p);
  // the meters: staring fills yours, looking away drains it
  const staring = new Set();
  for (const [p, s] of seen) if (s.stare) { staring.add(p.id); h.stare.set(p.id, Math.min(1, (h.stare.get(p.id) || 0) + stareRate(s.d, nv(p)) * dt)); }
  for (const [id, k] of h.stare) if (!staring.has(id)) { const v = k - HR.decay * dt; if (v <= 0) h.stare.delete(id); else h.stare.set(id, v); }
  for (const [id, k] of h.stare) if (k >= 1) { const p = room.players.get(id); if (p && p.alive) { take(room, p); return; } }
  if (n - h.born > HR.life * 1000 && !seen.length) { leave(room, 'bored'); return; }
  // nobody's looking: blink closer (and turn to face them). close enough, still unseen: he's got them
  if (!seen.length) {
    h.stepT -= dt;
    const dx = t.pos[0] - h.p[0], dz = t.pos[2] - h.p[2], d = Math.hypot(dx, dz);
    if (d < HR.reach) { take(room, t); return; }
    if (h.stepT <= 0) {
      h.stepT = rr(HR.stepEvery);
      const st = Math.min(d - 1.2, rr(HR.step));
      let pick = null; // a step where they'd see him if they turned round, if there is one
      for (let k = 0; k < 10 && !(pick && pick.open); k++) {
        const side = (Math.random() - 0.5) * (k + 1) * 0.5, a = Math.atan2(dz, dx) + side;
        const s = standOk(room, h.p[0] + Math.cos(a) * st, h.p[2] + Math.sin(a) * st);
        if (s && !(pick && !openTo(room, t, s))) pick = { s, open: openTo(room, t, s) };
      }
      if (pick) { h.p = pick.s; h.pose = (Math.random() * 1000) | 0; h.moved = n; }
      h.yaw = Math.atan2(h.p[0] - t.pos[0], h.p[2] - t.pos[2]);
      if (Math.hypot(t.pos[0] - h.p[0], t.pos[2] - h.p[2]) < HR.reach) { take(room, t); return; }
    }
  }
  // tell everyone where he is (10 a second), and each person how far their own meter has got
  if (n - h.sendT >= 100) {
    h.sendT = n;
    const base = { t: 'hr', on: 1, p: h.p.map(r2), y: r2(h.yaw), tg: h.target, pose: h.pose };
    for (const p of room.players.values()) if (!p.isBot && p.ws && p.ws.readyState === 1) p.ws.send(JSON.stringify({ ...base, st: r2(h.stare.get(p.id) || 0) }));
  }
}

// bots: don't stare (look away once the meter starts), glance at him when he's close and you're the one he's after
// (that freezes him), and back off. returns the bot's move, changed or not
export function hrBot(room, b, dt, out) {
  const h = room.hr;
  if (!h || !h.on || !b.alive) return out;
  const e = eye(b), s = hrSight(e, b.yaw || 0, b.pitch || 0, h.p, nv(b));
  const k = h.stare.get(b.id) || 0;
  if (s.d > (nv(b) ? HR.seeNVG : HR.see) || !lineClear(room, e, s)) return out;
  const ai = b.ai, to = Math.atan2(-s.dir[0], -s.dir[2]), away = to + Math.PI;
  const turn = (want, rate) => { let d = want - b.yaw; d = Math.atan2(Math.sin(d), Math.cos(d)); b.yaw += d * Math.min(1, rate * dt); };
  const fighting = ai.seenAt && room.players.get(ai.target) && room.players.get(ai.target).alive;
  if (k > 0.3 || (s.stare && k > 0.12 && fighting)) { turn(away + (ai.seed % 1 - 0.5), 9); b.pitch *= 0.9; } // that's enough looking
  else if (h.target === b.id && s.d < 20 && !fighting && !s.view) turn(to, 6); // he's behind me: look, so he can't move
  if (h.target === b.id && s.d < 16) { // and get some distance (sideways a bit, not straight into a tree)
    const ax = -s.dir[0], az = -s.dir[2], l = Math.hypot(ax, az) || 1;
    return { wx: (ax / l) * 0.85 + (out.wx || 0) * 0.3, wz: (az / l) * 0.85 + (out.wz || 0) * 0.3, jump: out.jump };
  }
  return out;
}
