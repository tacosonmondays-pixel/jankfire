// ISLAND ARENA (docs/modes/BATTLE_ISLAND.md, "Second option"): Battle Island's island and heroes as a 6v6 team
// deathmatch. You start the match in your mech, dropped onto your team's pads in the island's middle (Scrap Mart vs
// Dead Air). It breaks: you're the pilot again and the MECH METER starts at 60% (Battle Island's meter: time, damage,
// kills); full = call it in again. Pilots respawn on foot when they die. Only mech kills score: first team to 30, or
// the most when the clock runs out. No zone, no loot, no sea: an invisible fence keeps everyone in the middle.
// Shared by the server (server/arena.js: the real rules) and the client (public/js/arena.js: the HUD, the fence).
import { GAMES, GAME_ORDER, TARGETS } from './modes.js';
import './island.js'; // (Battle Island's map + GAMES.island first: the arena rides on them)

export const ARENA = {
  kills: 30, // mech kills to win
  time: 600, // s on the clock (then the most mech kills wins)
  after: 60, // the meter after your mech breaks, and when you respawn on foot (at least this)
  late: 100, // a meter for someone who joins after the drop and can't be dropped in (no room on the pads)
  pad: 54, // the play area: the circle through Scrap Mart and Dead Air, + this many m (the temple's pad just makes it)
  mid: 25, // a pad this close to the line between the two halves is no-man's-land: nobody spawns there
  ring: 5, // m between the mechs dropped round a pad
  bots: 12, // a bots-only room: 6 a side
};
// test knobs: mech kills to win, s on the clock
const knob = (k, lo, hi) => { const v = typeof process !== 'undefined' && process.env ? Number(process.env[k]) : NaN; return Number.isFinite(v) && v >= lo && v <= hi ? v : null; };
if (knob('JF_ARENA_KILLS', 1, 999)) ARENA.kills = knob('JF_ARENA_KILLS', 1, 999) | 0;
if (knob('JF_ARENA_TIME', 10, 7200)) ARENA.time = knob('JF_ARENA_TIME', 10, 7200);

// the play area on a royale map with Battle Island's POIs: { c: [x, z], r, pads: { 1: [[x, y, z, r]...], 2: [...] } }.
// the middle between Scrap Mart (hangar) and Dead Air (radio); each team gets the drop pads on its half
const AREAS = new WeakMap();
export function arenaArea(map) {
  const R = map && map.royale;
  if (!R || typeof map !== 'object') return null;
  if (AREAS.has(map)) return AREAS.get(map);
  const pois = Array.isArray(R.pois) ? R.pois : [], a = pois.find((p) => p.id === 'hangar'), b = pois.find((p) => p.id === 'radio');
  let out = null;
  if (a && b && Array.isArray(R.drops)) {
    const c = [(a.c[0] + b.c[0]) / 2, (a.c[1] + b.c[1]) / 2], ax = [b.c[0] - a.c[0], b.c[1] - a.c[1]], al = Math.hypot(ax[0], ax[1]) || 1;
    const r = al / 2 + ARENA.pad, pads = { 1: [], 2: [] };
    for (const d of R.drops) {
      if (!Array.isArray(d) || Math.hypot(d[0] - c[0], d[2] - c[1]) > r - 6) continue;
      const side = ((d[0] - c[0]) * ax[0] + (d[2] - c[1]) * ax[1]) / al;
      if (Math.abs(side) >= ARENA.mid) pads[side < 0 ? 1 : 2].push(d.slice());
    }
    if (pads[1].length && pads[2].length) out = { c, r, pads };
  }
  AREAS.set(map, out);
  return out;
}
// in the play area (flat)? slack: metres of give
export const inArena = (A, x, z, slack = 0) => !!A && Math.hypot(x - A.c[0], z - A.c[1]) <= A.r + slack;

Object.assign(GAMES, {
  arena: { name: 'ISLAND ARENA', desc: '6v6 in mechs on the island\'s middle. your mech breaks: you\'re the pilot till your meter fills again. first team to 30 mech kills wins', teams: true, arena: true, islandMap: true, beta: true, mapOk: (m) => !!arenaArea(m) },
});
GAME_ORDER.push('arena');
TARGETS.ffa.arena = ARENA.kills; TARGETS.bots.arena = ARENA.kills;
