// Server memory with N story rooms: node --expose-gc --max-old-space-size=256 tools/city/heap.mjs <rooms> [city] [seconds]
// Each room has 2 players sprinting / driving straight lines across the city (11 and 30 m/s), the room's CityView keeps
// the chunks within 160 m loaded, players move with the real physics, and every room asks for an NPC path each second.
// Prints one JSON line: heap after GC before / after, cache stats, tick times.
import { CityCache, CityView } from '../../server/citycache.js';
import { CITIES, CHUNK } from '../../shared/city/plan.js';
const rooms = Number(process.argv[2] || 1), city = process.argv[3] || 'stress', secs = Number(process.argv[4] || 60);
const gc = () => { if (global.gc) { global.gc(); global.gc(); } return process.memoryUsage().heapUsed / 1048576; };
const C = CITIES[city], X0 = C.cx0 * CHUNK + 20, X1 = C.cx1 * CHUNK - 20, Z0 = C.cz0 * CHUNK + 20, Z1 = C.cz1 * CHUNK - 20;
let seed = 7; const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const base = gc();
let simT = 0;
const cache = new CityCache({ clock: () => simT * 1000 });
const R = [];
for (let i = 0; i < rooms; i++) {
  if (!cache.openRoom('r' + i)) throw new Error('room refused');
  const ps = [0, 1].map((k) => ({ pos: [X0 + rnd() * (X1 - X0), 40, Z0 + rnd() * (Z1 - Z0)], vel: [0, 0, 0], sp: k ? 30 : 11, dir: rnd() * 6.28 }));
  R.push({ view: new CityView(cache, city), ps, paths: 0, found: 0 });
}
const refused = rooms >= 8 ? cache.openRoom('extra') === null : null; // the 9th room gets "the city is full"
const dt = 0.05; let ticks = 0, tickMs = 0, maxTick = 0;
for (let t = 0; t < secs; t += dt) {
  const t0 = performance.now(); simT = t;
  for (const r of R) {
    for (const p of r.ps) { // fly the route straight (cars hop over buildings: worst case for chunk churn)
      p.pos[0] += Math.cos(p.dir) * p.sp * dt; p.pos[2] += Math.sin(p.dir) * p.sp * dt;
      if (p.pos[0] < X0 || p.pos[0] > X1) p.dir = Math.PI - p.dir; if (p.pos[2] < Z0 || p.pos[2] > Z1) p.dir = -p.dir;
      p.pos[0] = Math.max(X0, Math.min(X1, p.pos[0])); p.pos[2] = Math.max(Z0, Math.min(Z1, p.pos[2]));
    }
    r.view.update(r.ps.map((p) => p.pos));
    for (const p of r.ps) { const q = [p.pos[0], 60, p.pos[2]], v = [0, -30, 0]; r.view.world.movePlayer(q, v, dt, false); } // a body falling onto whatever is there
    if (ticks % 20 === 0) { const a = r.ps[0].pos; const path = r.view.path([a[0], 0.2, a[2]], [a[0] + 40, 0.2, a[2] + 30], 6000); r.paths++; if (path) r.found++; }
  }
  const ms = performance.now() - t0; tickMs += ms; maxTick = Math.max(maxTick, ticks > 20 ? ms : 0); ticks++;
}
const after = gc();
console.log(JSON.stringify({ rooms, city, secs, heapBaseMB: +base.toFixed(1), heapMB: +after.toFixed(1), heapDeltaMB: +(after - base).toFixed(1), rssMB: +(process.memoryUsage().rss / 1048576).toFixed(0), cache: cache.stats(), held: R.reduce((a, r) => a + r.view.held.size, 0), avgTickMs: +(tickMs / ticks).toFixed(2), maxTickMs: +maxTick.toFixed(1), paths: R.reduce((a, r) => a + r.paths, 0), pathsFound: R.reduce((a, r) => a + r.found, 0), ninthRoomRefused: refused }));
