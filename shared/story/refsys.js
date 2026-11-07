// the solo combat referee (a sim system): the game's real room code (server/room.js, mode 'story': server/storyref.js)
// running inside the story's web worker, so story fights use exactly the PvP rules (hit checks, damage, knockback,
// items, peels, marbles, parries, grapples) and enemies are the game's bots with a story kind.
//   the room owns you while it runs: HP, hits, deaths, respawns, your seq. the sim mirrors you (sim.me) for the save
//   client -> sim  every normal game message (fire / hit / item / use / parry / grap / s / pi ...) goes to the room;
//                  { t: 'sty', k: 'spawn', kind, at, n?, id?, name?, hp?, w? }  enemies (n of them, around at)
//                  { t: 'sty', k: 'despawn', id? | kind? }                       gone (no kill, no loot)
//                  { t: 'sty', k: 'damage', id, dmg }                            a scripted hurt ('me' = you)
//                  { t: 'sty', k: 'hold', id? | kind? | all: true, on }          freeze / let go (cutscenes, talks)
//   sim -> client  the room's own messages, as in a match (enemies are remote players), and
//                  { t: 'sty', k: 'combat', ev }  ev in the format agreed with the story engine (WP8):
//                  hit { target, kind, dmg, by, weapon, head, hp, max } · kill { target, kind, by, weapon, head, at,
//                  boss, tags, npc } · down { who, by } · up { who }   (target / who: 'me', an npc id or 'e<n>')
// for other systems: sim.ref (null until the room is up), sim.refSpawn(def, at) -> enemy id, sim.refEnemies()
import { addSystem } from './sim.js';

export const REF = { maxAlive: 24, near: 220, maxHp: 5000, bodyMs: 4000, step: 1 / 60, maxSteps: 8 };
// enemy kinds the referee knows by itself; the story engine's own defs (hp, weapon, name, look, tags) override these
export const ENEMY_KINDS = {
  dummy: { hp: 100, w: 'pistol', name: 'Intern', tags: ['test'] },
  corp_temp: { hp: 80, w: 'pistol', name: '☺ CORP TEMP', tags: ['corp', 'ranged'] }, // (the same as content/enemies.js, which wins when it loads)
  raider: { hp: 120, w: 'shotgun', name: 'Raider', tags: ['raider'] },
};
// the story engine's own enemy table (shared/story/content/enemies.js, WP8): name, hp, weapon, tags, faction (= side:
// factions don't cover for each other, interns and temps will happily shoot through one another to get to you)
let CONTENT = null;
function loadKinds() { return import('./content/enemies.js').then((m) => { CONTENT = m.ENEMIES || null; }).catch(() => { CONTENT = null; }); } // (not there yet: the defaults)
function kindOf(id) {
  const c = CONTENT && Object.hasOwn(CONTENT, id) ? CONTENT[id] : null;
  const tags = c && Array.isArray(c.tags) ? c.tags : [];
  if (c) return { hp: c.hp, w: c.weapon, name: c.name, tags, side: c.faction === 'bottom' || tags.includes('ally') ? 'you' : c.faction || 'enemy' }; // (the Bottom's own people are never against you)
  return Object.hasOwn(ENEMY_KINDS, id) ? ENEMY_KINDS[id] : ENEMY_KINDS.dummy;
}
const isId = (s) => typeof s === 'string' && /^[a-z0-9_:-]{1,40}$/i.test(s);
const v3 = (a) => Array.isArray(a) && a.length === 3 && a.every((x) => Number.isFinite(x) && Math.abs(x) < 1e5);
const r2 = (x) => Math.round(x * 100) / 100;

// the room code reads process.env for its test knobs: the browser has no process, so it gets an empty one
function shimProcess() {
  if (globalThis.process && globalThis.process.env) return;
  globalThis.process = { env: {}, versions: {}, platform: 'browser', memoryUsage: () => ({ heapUsed: 0, rss: 0 }), on() {} };
}
// the map the room plays on: the test lot is a normal map (same builder as the client); the slice comes with the
// worker-side city (TODO: ChunkWorld boxes around you)
async function mapFor(zone) {
  const M = await import('../map.js');
  if (zone === 'story_test' && !M.MAPS.story_test) {
    const { buildTestMap } = await import('./testmap.js');
    const m = buildTestMap({ builder: M.builder, horizon: M.horizon, rng: M.rng, lollipop: M.lollipop, conifer: M.conifer });
    M.unstick(m.boxes, m.spawns); M.MAPS.story_test = m;
  }
  return M.MAPS[zone] ? zone : null;
}

function boot(sim) {
  if (sim.refBooting) return;
  sim.refBooting = true;
  shimProcess();
  Promise.all([import('../../server/room.js'), mapFor(sim.zone), loadKinds()]).then(([R, mapId]) => {
    if (!mapId || !sim.me) { sim.refOff = mapId ? '' : 'no map'; return; }
    const room = new R.Room(`story:${sim.zone}`, 'story');
    room.cfg.map = mapId; room.cfg.bots = 0; room.cfg.hr = 'off';
    const out = sim.raw || ((s) => sim.send(JSON.parse(s)));
    const ws = { readyState: 1, send: (s) => { if (s.startsWith('{"t":"welcome"')) return; out(s); } }; // (the sim already welcomed you)
    const me = room.addHuman(ws, { t: 'join', name: sim.me.name, item: sim.me.item || 'frag', mode: 'story' });
    me.pos = sim.me.pos.slice(); me.seq = sim.me.seq; me.yaw = sim.me.yaw || 0;
    room.onStory = (ev) => report(sim, ev);
    sim.ref = { room, me, acc: 0, ids: new Map(), was: true };
    sim.sty('refOn', { id: me.id });
    for (const q of sim.refQ.splice(0)) sim.msg(q); // spawns the story asked for while the room was loading
  }).catch((e) => { sim.refOff = String(e && e.message || e); sim.sty('refOff', { why: sim.refOff.slice(0, 120) }); });
}

// a room player -> the id the story engine knows it by
function idOf(sim, p) {
  if (!p) return 'world';
  if (sim.ref && p === sim.ref.me) return 'me';
  if (p.sk) return p.sk.npc || p.storyId || `e${p.id}`;
  return 'ally';
}
function report(sim, ev) {
  const t = ev.t, sk = t.sk, by = ev.by && ev.by !== t ? idOf(sim, ev.by) : ev.by === t ? 'self' : 'world';
  if (ev.type === 'hit') {
    const max = sk ? sk.max : 100, hp = Math.max(0, Math.round(t.hp * max / 100));
    sim.sty('combat', { ev: { type: 'hit', target: idOf(sim, t), kind: sk ? sk.kind : 'you', dmg: Math.round(ev.dmg), by, weapon: ev.w || '', head: !!ev.head, hp, max } });
  } else if (ev.type === 'kill') {
    if (!sk) { sim.sty('combat', { ev: { type: 'down', who: idOf(sim, t), by: ev.by && ev.by.sk ? ev.by.sk.kind : by } }); return; }
    sim.sty('combat', { ev: { type: 'kill', target: idOf(sim, t), kind: sk.kind, by, weapon: ev.w || '', head: !!t.lastHs, at: t.pos.map(r2), boss: sk.boss, tags: sk.tags, ...(sk.npc ? { npc: sk.npc } : {}) } });
  }
}

// a story enemy from a def (+ the kind's defaults), near `at`
function spawnOne(sim, m, at) {
  const R = sim.ref; if (!R) return 0;
  if ([...R.room.players.values()].filter((p) => p.sk && p.alive).length >= REF.maxAlive) return 0;
  const base = kindOf(m.kind);
  const def = { kind: m.kind, name: typeof m.name === 'string' ? m.name.slice(0, 24) : base.name, hp: Number.isFinite(m.hp) ? Math.max(1, Math.min(REF.maxHp, m.hp)) : base.hp,
    w: typeof m.w === 'string' ? m.w : base.w, tags: base.tags, npc: isId(m.npc) ? m.npc : '', boss: false, side: m.side === 'you' ? 'you' : isId(base.side) ? base.side : 'enemy' };
  const b = R.room.storySpawn(def, at);
  if (isId(m.id)) b.storyId = m.id;
  return b.id;
}

addSystem({
  id: 'ref',
  init(sim) {
    sim.ref = null; sim.refQ = [];
    sim.refSpawn = (def, at) => spawnOne(sim, def, at);
    sim.refEnemies = () => (sim.ref ? [...sim.ref.room.players.values()].filter((p) => p.sk) : []);
  },
  join(sim) { boot(sim); },
  tick(sim, dt) {
    const R = sim.ref; if (!R) return;
    R.acc = Math.min(R.acc + dt, REF.step * REF.maxSteps);
    while (R.acc >= REF.step) { R.acc -= REF.step; R.room.tick(REF.step); }
    R.room.snapshot();
    // mirror you for the save (and the other systems), and say when you're back up
    const me = R.me; sim.me.pos = me.pos.slice(); sim.me.seq = me.seq; sim.me.yaw = me.yaw; sim.me.hp = me.hp; sim.me.alive = me.alive;
    if (me.alive && !R.was) sim.sty('combat', { ev: { type: 'up', who: 'me' } });
    R.was = me.alive;
    // the fallen leave after a moment
    for (const p of [...R.room.players.values()]) if (p.sk && !p.alive && sim.t >= (p.goneAt ??= sim.t + REF.bodyMs / 1000)) R.room.storyDespawn(p); // (sim time: slow-mo and cutscenes hold them too)
  },
  raw(sim, m) {
    const R = sim.ref; if (!R) return false; // (still loading: the sim's own handling)
    if (m.t === 'join') return true;
    if (m.t === 'sty') return false; // story messages are the systems' (msg below)
    R.room.handle(R.me, m);
    return true;
  },
  msg(sim, m) {
    const R = sim.ref;
    if (!R && (m.k === 'spawn' || m.k === 'despawn' || m.k === 'damage' || m.k === 'hold')) { if (!sim.refOff && sim.refQ.length < 32) sim.refQ.push(m); return true; } // (the room is still loading)
    switch (m.k) {
      case 'spawn': {
        if (!R || typeof m.kind !== 'string' || !isId(m.kind) || !v3(m.at)) return true;
        if (Math.hypot(m.at[0] - R.me.pos[0], m.at[2] - R.me.pos[2]) > REF.near) return true;
        const n = Math.max(1, Math.min(8, m.n | 0 || 1));
        for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2, r = n > 1 ? 1.5 : 0; spawnOne(sim, m, [m.at[0] + Math.cos(a) * r, m.at[1], m.at[2] + Math.sin(a) * r]); }
        return true;
      }
      case 'despawn': {
        if (!R) return true;
        for (const p of sim.refEnemies()) if ((isId(m.id) && idOf(sim, p) === m.id) || (isId(m.kind) && !m.id && p.sk.kind === m.kind)) R.room.storyDespawn(p);
        return true;
      }
      case 'hold': {
        if (!R) return true;
        for (const p of sim.refEnemies()) if (m.all === true || (isId(m.id) && idOf(sim, p) === m.id) || (isId(m.kind) && !m.id && p.sk.kind === m.kind)) p.sk.hold = m.on !== false;
        return true;
      }
      case 'damage': {
        if (!R || !Number.isFinite(m.dmg) || m.dmg <= 0) return true;
        const t = m.id === 'me' ? R.me : sim.refEnemies().find((p) => idOf(sim, p) === m.id);
        if (t && t.alive) R.room.damage(t, Math.min(m.dmg, REF.maxHp), null, typeof m.why === 'string' && isId(m.why) ? m.why : 'story', false);
        return true;
      }
    }
    return false;
  },
});
