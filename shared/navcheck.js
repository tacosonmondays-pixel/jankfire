// The map editor's bot check: can bots still get everywhere they need to after the edits? Uses the same walk graph the
// server's bots use (the map's own lazy `graph`, shared/nav.js), rebuilt from the edited boxes. Pure: the editor draws
// the answer, a test can run it on the server side.
import { navLocate } from './nav.js';

// the spots bots must reach: spawns, team spawns, bomb sites, the zombies maps' wall guns / machines / crate / power
export function keyPoints(def) {
  const out = [], add = (p, what) => { if (Array.isArray(p) && p.length >= 3 && p.every(Number.isFinite)) out.push({ p: [p[0], p[1], p[2]], what }); };
  (def.spawns || []).forEach((p, i) => add(p, 'spawn ' + (i + 1)));
  if (def.teamSpawns) for (const k of ['att', 'def']) (def.teamSpawns[k] || []).forEach((p, i) => add(p, (k === 'att' ? 'attacker' : 'defender') + ' spawn ' + (i + 1)));
  for (const s of def.sites || []) if (s.min && s.max) add([(s.min[0] + s.max[0]) / 2, s.min[1], (s.min[2] + s.max[2]) / 2], 'bomb site ' + s.id);
  const z = def.zm;
  if (z) {
    for (const b of z.buys || []) add(b.at, 'wall gun ' + b.w);
    for (const k of ['crate', 'power', 'cola', 'up', 'mach']) if (z[k]) add(z[k].at, k === 'up' ? 'upgrade machine' : k === 'mach' ? 'cheat machine' : k);
    for (const c of z.colas || []) add(c.at, 'cola ' + c.id);
  }
  return out;
}
// the main area: the biggest set of nodes one spawn can walk to (links run one way: drops). a spawn boxed in with a
// bomb site can still reach that site, so "from any spawn" isn't enough. a Uint8Array over the nodes
export function reachable(g, def) {
  const starts = [...(def.spawns || []), ...(def.teamSpawns ? [...(def.teamSpawns.att || []), ...(def.teamSpawns.def || [])] : [])];
  let best = new Uint8Array(g.nodes.length), bn = 0;
  const done = new Uint8Array(g.nodes.length);
  for (const p of starts) {
    const k0 = navLocate(g, p);
    if (k0 < 0 || done[k0]) continue; // (already inside an area we walked)
    const seen = new Uint8Array(g.nodes.length), q = [k0]; seen[k0] = 1; let n = 1;
    while (q.length) { const k = q.pop(); for (let e = g.off[k], e1 = g.off[k + 1]; e < e1; e++) { const m = g.to[e]; if (!seen[m]) { seen[m] = 1; n++; q.push(m); } } }
    for (let k = 0; k < seen.length; k++) if (seen[k]) done[k] = 1;
    if (n > bn) { bn = n; best = seen; }
  }
  return best;
}
const cellKey = (p) => Math.round(p[0] * 2) + ',' + Math.round(p[1] * 2) + ',' + Math.round(p[2] * 2);
// the check. def: the edited map, base: the same map without your edits (or null). returns null when the map has no walk
// graph (open maps: bots walk straight at things there)
export function navCheck(def, base) {
  if (!Object.getOwnPropertyDescriptor(def, 'graph')) return null;
  if (def.dropGraph) def.dropGraph(); // (built from the boxes as they are now)
  const g = def.graph, r = reachable(g, def), pts = keyPoints(def);
  const okAt = (G, R, p) => { const k = navLocate(G, p); return k >= 0 && !!R[k] && Math.hypot(G.nodes[k][0] - p[0], G.nodes[k][2] - p[2]) < 3; };
  let bg = null, br = null;
  if (base && Object.getOwnPropertyDescriptor(base, 'graph')) { if (base.dropGraph) base.dropGraph(); bg = base.graph; br = reachable(bg, base); }
  const spots = pts.map((s) => ({ ...s, ok: okAt(g, r, s.p), was: bg ? okAt(bg, br, s.p) : null }));
  // floor bots used to get to and now can't: nodes that still exist but are cut off, plus floor that's covered now
  const lost = [];
  if (bg) {
    const now = new Map(); g.nodes.forEach((p, k) => now.set(cellKey(p), k));
    bg.nodes.forEach((p, k) => { if (!br[k]) return; const n = now.get(cellKey(p)); if (n !== undefined && !r[n]) lost.push(p); });
  }
  let n = 0; for (let k = 0; k < r.length; k++) n += r[k];
  return { nodes: g.nodes.length, reach: n, spots, lost };
}
