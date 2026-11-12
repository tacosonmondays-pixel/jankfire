// The bots' walk graphs, and what the server works out from them, kept only for maps a room is using. Built all at once
// they came to ~150 MB of the ~256 MB heap Render gives us, so a map's graph (plus its maze lanes, the bomb bots' spots,
// the buy zones, the royale's loot spots, the zombies' nav grid) is dropped once no room has been on it for a while (the
// TTL), and built again when a room starts on it (at the start, never mid-match).
// The modules with caches of their own register them: onForget((map, id) => ...) to drop them, onWarm(...) to build them.
import { MAPS } from '../shared/map.js';

const used = new Map(); // map id -> the last time a room was on it
const forgetters = [], warmers = [];
const born = Date.now(); // (a graph built before any room used its map counts from here)
const mem = () => { const u = process.memoryUsage(); return `heap ${(u.heapUsed / 1048576).toFixed(0)} MB, rss ${(u.rss / 1048576).toFixed(0)} MB`; };
export function onForget(fn) { forgetters.push(fn); }
export function onWarm(fn) { warmers.push(fn); }
export const graphBuilt = (m) => !!(m && m.peekGraph && m.peekGraph());
// a map that's going away for good (the map editor's PLAY HERE copies): its graph and every cache built from it
export function forgetMap(id) {
  const m = MAPS[id];
  if (m) { if (m.dropGraph) m.dropGraph(); for (const fn of forgetters) fn(m, id); }
  used.delete(id);
}

// a room is on map id (just started on it, or still there): note it, and build what its bots need right away
export function warmMap(room, id) {
  used.set(id, Date.now());
  const m = MAPS[id];
  if (!m) return;
  const had = graphBuilt(m), t0 = Date.now();
  void m.graph; void m.nav; // (the maze maps build their lanes from the graph)
  for (const fn of warmers) fn(room, m, id);
  if (!had && graphBuilt(m)) console.log(`[graphs] built ${id} (${m.peekGraph().nodes.length} nodes) in ${Date.now() - t0} ms for room ${room.id}. ${mem()}`);
}

// drop everything built for maps no room has been on for ttl ms. rooms: the live rooms. returns what was dropped
export function sweepGraphs(rooms, ttl, now = Date.now()) {
  for (const r of rooms) if (r.cfg && MAPS[r.cfg.map]) used.set(r.cfg.map, now);
  const gone = [];
  for (const [id, m] of Object.entries(MAPS)) {
    if (!graphBuilt(m) || now - (used.get(id) ?? born) < ttl) continue;
    const nodes = m.peekGraph().nodes.length;
    m.dropGraph();
    for (const fn of forgetters) fn(m, id);
    used.delete(id);
    gone.push(`${id} (${nodes} nodes)`);
  }
  if (gone.length) {
    if (global.gc) global.gc(); // (tests only: node --expose-gc. so the heap printed is what's really left)
    const left = Object.entries(MAPS).filter(([, m]) => graphBuilt(m)).map(([id]) => id);
    console.log(`[graphs] dropped ${gone.join(', ')}: no room on them for ${(ttl / 60e3).toFixed(1)} min. still built: ${left.join(', ') || 'none'}. ${mem()}`);
  }
  return gone;
}
export function startGraphSweeper(rooms, ttl, every) {
  const t = setInterval(() => { try { sweepGraphs(rooms(), ttl); } catch (e) { console.error('[graphs] sweep failed', e); } }, every);
  if (t.unref) t.unref();
  return t;
}
