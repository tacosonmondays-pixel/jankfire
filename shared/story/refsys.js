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
//   bosses (server/storyboss.js): spawn a kind that is a boss in content/bosses.js (one at a time). on top of the above:
//                  { t: 'sty', k: 'boss', on, id, pid, hp, max, health, name, phase, who }  he's in the room (pid: his room id) / gone
//                  hit also has { part, crit, boss } · phase { target, kind, boss, phase, name, line, invuln } ·
//                  part { target, kind, boss, part, state } · act { target, kind, boss, move, clip, t0, at, yaw } ·
//                  fx { target, kind, boss, k: 'staple', at, n } · kill { ..., boss: <boss id>, defeat } ends the fight
//                  tests only (sim.dev): { t: 'sty', k: 'bossdev', want?: <move>, calm?: bool }
//   the train fight (server/storytrain.js, boss revenue_protection_1): its events ride the same 'combat' message:
//                  state { gap, hp, max, phase, stage, plates, open, marrow, arms, jack } · gap { gap, rate, jack } ·
//                  arm { id, k, sock, st, dur, tgt, hp, max ... } · arms { clear } · plate { i, st } · stage { stage, name } ·
//                  flinch { open, gap } · shrug { at } · bloom { at } · swept · snatched · lunge { st } · bag { hp } · off ·
//                  fail { why, line } · reset. hit also has { arm }. the Blood Drive: { t: 'fire', w: 'blooddrive', k?, o, d }
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
// bosses: the fight's numbers come from content/bosses.js (hp, phases, layers, the weak point's crit) and the model's
// parts file (hitboxes, clip marks). what the room can run of each phase's mechanics is named here (the rest: not yet)
let BOSSES = null;
const PARTS = {}, PART_FILES = { overtime: 'c_overtime.parts.json', revenue_protection: '../story/revenue_protection.parts.json' }; // (the train boss's file is with the story models)
const TRAIN_BOSS = { revenue_protection: true }; // not a walking bot: server/storytrain.js runs it (arms, THE GAP)
const MOVES = { 'Staple Gun': 'staple', 'Overtime Slam': 'slam', 'Punch In': 'punchin', 'Staple Fan': 'fan' }, REST = { 'Coffee Break': 15 };
const BOSS_SIDE = { overtime: 'corp' }; // (his own collectors don't get stapled)
async function loadJson(file) {
  if (typeof location !== 'undefined' && typeof fetch === 'function') { const r = await fetch('/models/cast/' + file); return r.ok ? r.json() : null; } // the worker
  const fs = await import('node:fs/promises'); // node (tests, co-op later)
  return JSON.parse(await fs.readFile(new URL('../../public/models/cast/' + file, import.meta.url), 'utf8'));
}
function loadBosses() {
  return import('./content/bosses.js').then((m) => { BOSSES = m.BOSSES || null; }).catch(() => { BOSSES = null; })
    .then(() => Promise.all(Object.entries(PART_FILES).map(([who, f]) => loadJson(f).then((j) => { PARTS[who] = j; }).catch(() => { PARTS[who] = null; }))));
}
// the room's def for a boss kind (server/storyboss.js cleans it again), or null
function bossOf(id) {
  const b = BOSSES && Object.hasOwn(BOSSES, id) ? BOSSES[id] : null;
  if (!b || !Number.isFinite(b.hp) || !Array.isArray(b.phases) || !Object.hasOwn(PART_FILES, b.who)) return null; // (only bosses the room has hitboxes for)
  const moves = (p) => (Array.isArray(p.mechanics) ? p.mechanics : []).map((x) => MOVES[x && x.name]).filter(Boolean);
  const rest = (p) => (Array.isArray(p.mechanics) ? p.mechanics : []).reduce((a, x) => a || REST[x && x.name] || 0, 0);
  const health = (Array.isArray(b.layers) ? b.layers : []).find((l) => l && l.bar === 'health'), wp = Array.isArray(b.weakPoints) ? b.weakPoints[0] : null;
  if (TRAIN_BOSS[b.who]) { // its crits by name (boss_fights.js weakPoints: the wrists, the eye housings, the Inspector), its model's parts file as it is
    const cr = (re) => { const p = (Array.isArray(b.weakPoints) ? b.weakPoints : []).find((x) => x && re.test(String(x.name))); return p && Number.isFinite(p.crit) ? p.crit : undefined; };
    return { id, name: b.name, who: b.who, side: 'enemy', hp: b.hp, health: health && Number.isFinite(health.of) ? health.of : b.hp, phases: b.phases.map((p) => ({ name: p.name, line: p.line, to: Array.isArray(p.hp) ? p.hp[1] : 0 })),
      train: { parts: PARTS[b.who] || null, crit: { knot: cr(/wrist/i), eye: cr(/eye/i), insp: cr(/inspector/i) } } };
  }
  return { id, name: b.name, who: b.who, side: BOSS_SIDE[b.who] || 'enemy', hp: b.hp, health: health && Number.isFinite(health.of) ? health.of : b.hp, crit: wp && Number.isFinite(wp.crit) ? wp.crit : 2,
    phases: b.phases.map((p) => ({ name: p.name, line: p.line, to: Array.isArray(p.hp) ? p.hp[1] : 0, moves: moves(p), rest: rest(p) })), parts: PARTS[b.who] || null };
}
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
  if (zone === 'story_train' && !M.MAPS.story_train) { // the last two cars in the Under-Hill Loop (shared/story/train.js)
    const { buildTrainMap } = await import('./train.js');
    const m = buildTrainMap({ builder: M.builder });
    M.unstick(m.boxes, m.spawns); M.MAPS.story_train = m;
  }
  return M.MAPS[zone] ? zone : null;
}

function boot(sim) {
  if (sim.refBooting) return;
  sim.refBooting = true;
  shimProcess();
  Promise.all([import('../../server/room.js'), mapFor(sim.zone), loadKinds(), loadBosses()]).then(([R, mapId]) => {
    if (!mapId || !sim.me) { sim.refOff = mapId ? '' : 'no map'; return; }
    const room = new R.Room(`story:${sim.zone}`, 'story');
    room.cfg.map = mapId; room.cfg.bots = 0; room.cfg.hr = 'off';
    const out = sim.raw || ((s) => sim.send(JSON.parse(s)));
    const ws = { readyState: 1, send: (s) => { if (s.startsWith('{"t":"welcome"')) return; out(s); } }; // (the sim already welcomed you)
    const me = room.addHuman(ws, { t: 'join', name: sim.me.name, item: sim.me.item || 'frag', mode: 'story' });
    me.pos = sim.me.pos.slice(); me.seq = sim.me.seq; me.yaw = sim.me.yaw || 0;
    room.onStory = (ev) => report(sim, ev);
    room.storyFree = () => { const f = sim.state && sim.state.flags; return !!(f && (f.jack_marrow_taken || f.seen_mo_carry)); }; // Jack's marrow: blood weapons are free while they fire (storytrain.js driveFree)
    sim.ref = { room, me, acc: 0, ids: new Map(), was: true, boss: null, bye: [] };
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
  if (sk && sk.b && ev.type !== 'kill') return reportBoss(sim, ev, by);
  if (ev.type === 'hit') {
    const max = sk ? sk.max : 100, hp = Math.max(0, Math.round(t.hp * max / 100));
    sim.sty('combat', { ev: { type: 'hit', target: idOf(sim, t), kind: sk ? sk.kind : 'you', dmg: Math.round(ev.dmg), by, weapon: ev.w || '', head: !!ev.head, hp, max } });
  } else if (ev.type === 'kill') {
    if (!sk) { sim.sty('combat', { ev: { type: 'down', who: idOf(sim, t), by: ev.by && ev.by.sk ? ev.by.sk.kind : by } }); return; }
    sim.sty('combat', { ev: { type: 'kill', target: idOf(sim, t), kind: sk.kind, by, weapon: ev.w || '', head: !!t.lastHs, at: t.pos.map(r2), boss: sk.boss, tags: sk.tags, ...(sk.npc ? { npc: sk.npc } : {}) } });
  }
}

// a boss's events: the same ids as everyone's, plus boss (its content id: the client's fight hooks key on it)
function reportBoss(sim, ev, by) {
  const t = ev.t, sk = t.sk, base = { target: idOf(sim, t), kind: sk.kind, boss: sk.b.id };
  const out = (o) => sim.sty('combat', { ev: { type: ev.type, ...base, ...o } });
  if (ev.rp) out(ev.rp); // the train fight's own events (gap, arm, plate, stage, flinch...): as the room made them
  else if (ev.type === 'hit') out({ dmg: Math.round(ev.dmg), by, weapon: ev.w || '', head: false, hp: ev.hp, max: ev.max, part: ev.part, crit: !!ev.crit, ...(ev.arm ? { arm: ev.arm } : {}) });
  else if (ev.type === 'phase') out({ phase: ev.phase, name: ev.name, line: ev.line, invuln: !!ev.invuln });
  else if (ev.type === 'part') out({ part: ev.part, state: ev.state });
  else if (ev.type === 'act') out({ move: ev.move, clip: ev.clip, t0: r2(sim.t), at: t.pos.map(r2), yaw: r2(t.yaw) });
  else if (ev.type === 'bfx') sim.sty('combat', { ev: { type: 'fx', ...base, k: ev.k, at: ev.at.map(r2), n: ev.n.map(r2) } });
  else if (ev.type === 'defeat') { // the fight's end is the story's 'kill' (its killBoss goal); he leaves the room, alive
    sim.sty('combat', { ev: { type: 'kill', ...base, by, weapon: ev.w || '', head: false, at: t.pos.map(r2), tags: sk.tags, defeat: true } });
    if (sim.ref) sim.ref.bye.push(t);
  }
}

// a story enemy from a def (+ the kind's defaults), near `at`
function spawnOne(sim, m, at) {
  const R = sim.ref; if (!R) return 0;
  if ([...R.room.players.values()].filter((p) => p.sk && p.alive).length >= REF.maxAlive) return 0;
  const boss = bossOf(m.kind);
  if (boss) return spawnBoss(sim, m, at, boss);
  const base = kindOf(m.kind);
  const def = { kind: m.kind, name: typeof m.name === 'string' ? m.name.slice(0, 24) : base.name, hp: Number.isFinite(m.hp) ? Math.max(1, Math.min(REF.maxHp, m.hp)) : base.hp,
    w: typeof m.w === 'string' ? m.w : base.w, tags: base.tags, npc: isId(m.npc) ? m.npc : '', boss: false, side: m.side === 'you' ? 'you' : isId(base.side) ? base.side : 'enemy' };
  const b = R.room.storySpawn(def, at);
  if (isId(m.id)) b.storyId = m.id;
  return b.id;
}

// a boss: one at a time, its numbers are the content's (a spawn message can't change them), facing you
function spawnBoss(sim, m, at, boss) {
  const R = sim.ref;
  if (R.boss && R.room.players.get(R.boss.id) === R.boss) return 0;
  if (boss.train && m.resume === 1) boss.train.start = 1; // (the train fight, picked up after its middle scene: storytrain.js)
  const b = R.room.storySpawn({ kind: m.kind, name: typeof boss.name === 'string' ? boss.name.slice(0, 24) : 'BOSS', hp: boss.hp, w: 'nailgun', tags: ['boss'], npc: '', boss, side: boss.side }, at);
  if (!b.sk.b) { R.room.storyDespawn(b); return 0; } // (the def didn't hold up)
  b.storyId = isId(m.id) ? m.id : m.kind;
  b.yaw = Math.atan2(-(R.me.pos[0] - at[0]), -(R.me.pos[2] - at[2]));
  R.boss = b;
  sim.sty('boss', { on: true, id: b.sk.b.id, pid: b.id, hp: b.sk.b.hp, max: b.sk.max, health: b.sk.b.def.health, name: b.name, phase: b.sk.b.def.phases[0].name, who: typeof boss.who === 'string' ? boss.who : '' });
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
    // a beaten boss walks off in the story, not in the room; and the client hears when he's gone, however he went
    for (const p of R.bye.splice(0)) R.room.storyDespawn(p);
    if (R.boss && R.room.players.get(R.boss.id) !== R.boss) { sim.sty('boss', { on: false, id: R.boss.sk.b.id, pid: R.boss.id }); R.boss = null; }
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
        const n = bossOf(m.kind) ? 1 : Math.max(1, Math.min(8, m.n | 0 || 1));
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
      case 'bossdev': { // tests (?storydev=1): his next attack, and whether he only attacks when asked
        const B = R && sim.dev === true && R.boss && R.boss.sk.b; if (!B) return true;
        if (B.train) { R.room.rpDev(R.boss, m); return true; } // (the train fight stages its own moments)
        if (typeof m.want === 'string' && isId(m.want)) { B.want = m.want; B.next = B.t; }
        if (typeof m.calm === 'boolean') B.calm = m.calm;
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
