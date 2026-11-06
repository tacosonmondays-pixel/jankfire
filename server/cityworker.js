// The server's city worker thread: builds chunks (boxes + walk graph) and answers NPC path queries off the main
// thread, so a story room's 20 Hz tick never waits on a 60 ms chunk build or a long search. Keeps its own LRU of
// walk graphs (they live here; the main thread only gets the boxes it needs for physics).
// in:  { op: 'build', id, city, cx, cz }        out: { op: 'build', id, packed, nodes, ms }
//      { op: 'path', id, city, a, b, max }      out: { op: 'path', id, path | null, ms }
import { parentPort } from 'node:worker_threads';
import { buildChunk, packChunk, transferList } from '../shared/city/chunk.js';
import { buildChunkNav, NavWorld } from '../shared/city/cnav.js';
import { CHUNK, inCity } from '../shared/city/plan.js';
import '../shared/city/gens.js';

const MAX = 500, navs = new Map(), worlds = new Map(); // id -> nav, city -> NavWorld (every nav we hold)
function nav(city, cx, cz) {
  const id = city + ':' + cx + ':' + cz;
  let n = navs.get(id);
  if (n) { navs.delete(id); navs.set(id, n); return n; }
  n = buildChunkNav(packChunk(buildChunk(city, cx, cz)));
  keep(city, id, n);
  return n;
}
function keep(city, id, n) {
  navs.set(id, n);
  if (!worlds.has(city)) worlds.set(city, new NavWorld());
  worlds.get(city).set(n.cx, n.cz, n);
  while (navs.size > MAX) { const [old, o] = navs.entries().next().value; navs.delete(old); worlds.get(old.split(':')[0]).drop(o.cx, o.cz); }
}

parentPort.on('message', (m) => {
  const t = performance.now();
  try {
    if (m.op === 'build') {
      const packed = packChunk(buildChunk(m.city, m.cx, m.cz)), n = buildChunkNav(packed);
      keep(m.city, m.id, n);
      parentPort.postMessage({ op: 'build', id: m.id, packed, nodes: n.nodes, navBytes: n.bytes, ms: performance.now() - t }, transferList(packed));
    } else if (m.op === 'path') {
      // make sure every chunk the straight line crosses (+1 round it) has its graph here
      const [a, b] = [m.a, m.b], x0 = Math.floor(Math.min(a[0], b[0]) / CHUNK) - 1, x1 = Math.floor(Math.max(a[0], b[0]) / CHUNK) + 1;
      const z0 = Math.floor(Math.min(a[2], b[2]) / CHUNK) - 1, z1 = Math.floor(Math.max(a[2], b[2]) / CHUNK) + 1;
      if ((x1 - x0 + 1) * (z1 - z0 + 1) <= 36) for (let cx = x0; cx <= x1; cx++) for (let cz = z0; cz <= z1; cz++) if (inCity(m.city, cx, cz)) nav(m.city, cx, cz);
      const w = worlds.get(m.city), path = w ? w.path(a, b, m.max || 4000) : null;
      parentPort.postMessage({ op: 'path', id: m.id, path, ms: performance.now() - t });
    }
  } catch (e) { parentPort.postMessage({ op: m.op, id: m.id, err: String(e && e.stack || e) }); }
});
