// story encounters, the sim half (a sim system): the client's encounter director (public/js/story/encounters.js) asks
// for groups of enemies by name; this spawns them through the referee (refsys.js sim.refSpawn), says which room player
// is which (so the client can draw a war-rig over a bot and give it a rig-sized hitbox), and turns the room's encounter
// events (server/storyenc.js room.onEnc) into damage and juice.
//   client -> sim  { t: 'sty', k: 'enc', op: 'spawn', g, kind, at, n?, w?, name?, hp? }   a group (up to 8 per call)
//                  { t: 'sty', k: 'enc', op: 'flee', g }    its rigs pull back (honking), the rest keep going
//                  { t: 'sty', k: 'enc', op: 'clear', g? }  gone, no kills, no loot (no g = every group)
//   sim -> client  { t: 'sty', k: 'encOn', g, list: [{ pid, id, kind }] } · { t: 'sty', k: 'enc', ev: { type, pid, ... } }
// pure: no dom, no node (the solo worker; a co-op StoryRoom later).
import { addSystem } from './sim.js';

export const ENCSYS = { kinds: ['intern', 'war_rig', 'stomach_dog', 'collector', 'choir_singer', 'corp_temp', 'timekeeping_drone'], perCall: 8, groups: 12, perGroup: 24, opsPerSec: 8,
  ram: { car: 7, foot: 26, kb: 0.55 } };
const gid = (s) => typeof s === 'string' && /^[a-z0-9_]{1,16}$/.test(s);
const v3 = (a) => Array.isArray(a) && a.length === 3 && a.every((x) => Number.isFinite(x) && Math.abs(x) < 1e5);
const WOK = /^[a-z0-9_]{1,16}$/;

function onEnc(sim, ev) {
  const R = sim.ref; if (!R || !ev || !ev.b) return;
  const pid = ev.b.id;
  if (ev.type === 'ram') {
    if (ev.t !== R.me) return; // (rigs only hunt you; allies get bumped by the physics, not this)
    const car = !!(sim.carOf && sim.carOf()), C = ENCSYS.ram;
    R.room.damage(R.me, car ? C.car : C.foot, ev.b, 'car', false);
    if (!car && R.me.alive) R.room.knock(R.me, ev.v.map((x) => x * C.kb), 'ram');
    sim.sty('enc', { ev: { type: 'ram', pid, car, v: ev.v.map((x) => Math.round(x * 10) / 10), speed: Math.round(ev.speed || 0) } });
  } else if (ev.type === 'card' || ev.type === 'leap') sim.sty('enc', { ev: { type: ev.type, pid } });
}

addSystem({
  id: 'enc',
  init(sim) { sim.enc = { groups: new Map(), n: 0, ops: 0, opsT: 0 }; },
  tick(sim) {
    const R = sim.ref; if (!R) return;
    if (!R.encHook || R.room.onEnc !== R.encHook) { R.encHook = (ev) => onEnc(sim, ev); R.room.onEnc = R.encHook; }
    // forget the dead and the gone (the referee clears bodies)
    for (const [g, list] of sim.enc.groups) { const live = list.filter((x) => R.room.players.get(x.pid) === x.p); if (live.length !== list.length) sim.enc.groups.set(g, live); }
  },
  msg(sim, m) {
    if (m.k !== 'enc') return false;
    const E = sim.enc, R = sim.ref;
    if (sim.t - E.opsT >= 1) { E.opsT = sim.t; E.ops = 0; }
    if (m.op === 'spawn' && ++E.ops > ENCSYS.opsPerSec) return true; // (a flood of spawns: dropped. clearing up never is)
    if (!R) return true; // (no referee: no encounter fights. the director keeps asking)
    if (m.op === 'spawn') {
      if (!gid(m.g) || typeof m.kind !== 'string' || !ENCSYS.kinds.includes(m.kind) || !v3(m.at)) return true;
      if (!E.groups.has(m.g) && E.groups.size >= ENCSYS.groups) return true;
      const list = E.groups.get(m.g) || [], n = Math.max(1, Math.min(ENCSYS.perCall, m.n | 0 || 1)), out = [];
      for (let i = 0; i < n && list.length < ENCSYS.perGroup; i++) {
        const a = (i / n) * Math.PI * 2, r = n > 1 ? 2.2 : 0, id = `${m.g}_${++E.n}`;
        const pid = sim.refSpawn({ kind: m.kind, id, ...(typeof m.w === 'string' && WOK.test(m.w) ? { w: m.w } : {}), ...(typeof m.name === 'string' ? { name: m.name.slice(0, 24) } : {}), ...(Number.isFinite(m.hp) ? { hp: m.hp } : {}) },
          [m.at[0] + Math.cos(a) * r, m.at[1], m.at[2] + Math.sin(a) * r]);
        const p = pid && R.room.players.get(pid);
        if (!p) continue;
        list.push({ pid, id, kind: m.kind, p }); out.push({ pid, id, kind: m.kind });
      }
      E.groups.set(m.g, list);
      sim.sty('encOn', { g: m.g, list: out });
      return true;
    }
    if (m.op === 'flee') { for (const x of (gid(m.g) && E.groups.get(m.g)) || []) if (x.p.sk) x.p.sk.flee = true; return true; }
    if (m.op === 'clear') {
      for (const [g, list] of E.groups) { if (m.g != null && g !== m.g) continue; for (const x of list) R.room.storyDespawn(x.p); E.groups.delete(g); }
      return true;
    }
    return true;
  },
});
