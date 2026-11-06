// the OVERDUE story sim: one tick function, two hosts. solo: public/js/story/simworker.js (a web worker in your
// browser, costs the server nothing). co-op (WP10): server/story.js's StoryRoom. pure: no node, no dom.
//
// it speaks the game's normal protocol to the client (welcome / spawn / tp / po), so the normal player controller,
// weapons and HUD run unchanged, plus story messages under t: 'sty' ({ t: 'sty', k: kind, ... }).
// systems plug in with addSystem({ id, init(sim), join(sim), tick(sim, dt), msg(sim, m) -> true if handled (story 'sty'
// messages), raw(sim, m) -> true if handled (the normal game messages: 'item', 'fire'...), save(sim) -> part, load(sim, part) }): the quest engine, loot, inventory, implants, late fees each own one, and their save part goes to
// save.data[id].
import { worldOf } from './worlds.js'; // the Bottom (the city slice) or the test lot
import { newSave } from './save.js';
import { fromSave, toSave } from './state.js'; // the story engine's state (WP8): flags, quests, met, codex, log, track...

const SYSTEMS = [];
export function addSystem(s) { if (!SYSTEMS.some((o) => o.id === s.id)) SYSTEMS.push(s); }

export function createSim({ send, save }) {
  const sv = save || newSave(0);
  const W = worldOf(sv.at && sv.at.map); // where this run is: save.at.map, else the city slice
  const sim = {
    world: W, zone: W.id,
    save: sv, send, t: 0, me: null, // me: the (one, solo) player { id, name, pos, seq, alive }
    clock: (sv.data.clock && Number.isFinite(sv.data.clock.min)) ? sv.data.clock.min : 17 * 60 + 29, // the district clock: stuck at 17:29 for now
    sty(k, o) { send({ t: 'sty', k, ...o }); },
    state: fromSave(sv.data), // hand this to makeStory({ state: sim.state }) (shared/story/story.js)
  };
  for (const s of SYSTEMS) if (s.init) s.init(sim);
  for (const s of SYSTEMS) if (s.load && sv.data[s.id] !== undefined) s.load(sim, sv.data[s.id]);

  sim.join = (m) => {
    const name = typeof m.name === 'string' && m.name.trim() ? m.name.trim().slice(0, 16) : 'CHANGE';
    const at = sv.at && sv.at.map === W.id && !sv.at.fresh ? sv.at : { p: W.spawn, yaw: W.yaw };
    sim.me = { id: 1, name, pos: at.p.slice(), yaw: at.yaw || 0, hp: 100, seq: 1, alive: true, item: typeof m.item === 'string' ? m.item.slice(0, 24) : '' };
    send({
      t: 'welcome', id: 1, name, color: '#ff4fd8', pos: sim.me.pos, q: sim.me.seq, mode: 'story', game: 'dm',
      cfg: { map: W.id, hip: 'normal', bots: 0, diff: 'normal', hr: 'off' },
      players: [], peels: [], projs: [], holes: [], bubbles: [], smokes: [], kat: [], tags: [], sprays: [], mpatch: [],
      wave: null, level: 1, account: false, round: null, vote: null, skip: null, team: 0,
      ic: { i: sim.me.item, n: 1, next: 0 },
    });
    sim.sty('hello', { slot: sv.slot, act: sv.act, chapter: sv.chapter, yaw: at.yaw || 0, clock: sim.clock, coupons: sv.coupons });
    for (const s of SYSTEMS) if (s.join) s.join(sim);
  };

  sim.msg = (m) => {
    if (!m || typeof m.t !== 'string') return;
    if (m.t === 'join') return sim.join(m);
    if (!sim.me) return;
    for (const s of SYSTEMS) if (s.raw && s.raw(sim, m)) return; // a system that wants a normal game message ('item', 'fire'...)
    if (m.t === 'pi') return send({ t: 'po', c: m.c });
    if (m.t === 's') { // your movement (client-authoritative, as in multiplayer): keep it for the save, catch the void
      if (m.q !== sim.me.seq || !Array.isArray(m.p) || m.p.length !== 3 || !m.p.every(Number.isFinite)) return;
      sim.me.pos = m.p.slice();
      if (Number.isFinite(m.y)) sim.me.yaw = m.y;
      if (m.p[1] < W.killY) { // fell out: the Machine dispenses you again (BEEP. CLUNK.)
        sim.me.seq++; sim.me.pos = W.spawn.slice();
        send({ t: 'spawn', p: sim.me.pos, q: sim.me.seq });
        sim.sty('redispensed', {});
      }
      return;
    }
    if (m.t === 'sty') {
      for (const s of SYSTEMS) if (s.msg && s.msg(sim, m)) return;
      if (m.k === 'save') return sim.sty('saved', { save: sim.snapshot(m.why) });
    }
  };

  sim.tick = (dt) => {
    sim.t += dt;
    sim.save.playtime += dt;
    for (const s of SYSTEMS) if (s.tick) s.tick(sim, dt);
  };

  // the save as it stands now (the client posts it to /api/story/save or keeps it locally)
  sim.snapshot = () => {
    const out = JSON.parse(JSON.stringify(sim.save));
    out.playtime = Math.floor(out.playtime);
    if (sim.me) out.at = { map: W.id, p: sim.me.pos.map((x) => Math.round(x * 100) / 100), yaw: Math.round((sim.me.yaw || 0) * 1000) / 1000 };
    Object.assign(out.data, toSave(sim.state)); // the engine's keys sit at the top of save.data (TECH_PLAN §7)
    out.data.clock = { min: sim.clock };
    for (const s of SYSTEMS) if (s.save) out.data[s.id] = s.save(sim);
    return out;
  };
  return sim;
}
