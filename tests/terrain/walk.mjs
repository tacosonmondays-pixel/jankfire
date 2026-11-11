// node tests/terrain/walk.mjs : walks straight lines over every map with shaped ground with the shared physics (stays on the ground, no pops), checks the spawns and the walk graph
import { MAPS } from '../../shared/map.js';
import '../../shared/jankburg.js'; // (registers Jankburg, the royale city: its outer ring is shaped ground)
import { movePlayer, playerOverlap, raycast } from '../../shared/physics.js';
let fail = false;
for (const id of process.argv.length > 2 ? process.argv.slice(2) : ['desert', 'suburb', 'bazaar', 'islands', 'forest', 'jankburg']) {
const m = MAPS[id], T = m.boxes.terrain, dt = 1 / 60;
let runs = 0, air = 0, ticks = 0, pops = 0, walls = 0, maxPop = 0, off = 0;
const r = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
for (let k = 0; k < 400; k++) {
  const x = T.x0 + 3 + r() * (T.nx - 6), z = T.z0 + 3 + r() * (T.nz - 6), g = T.at(x, z);
  if (g == null || playerOverlap([x, g + 0.01, z], m.boxes)) continue;
  const a = r() * 6.283, sp = 6 + r() * 10, pos = [x, g, z], vel = [0, 0, 0]; let on = true; runs++;
  for (let t = 0; t < 240; t++) {
    vel[0] = Math.cos(a) * sp; vel[2] = Math.sin(a) * sp; vel[1] -= 26 * dt;
    const py = pos[1], res = movePlayer(pos, vel, dt, m.boxes, on);
    on = !!res.ground && vel[1] <= 0.01; ticks++;
    if (res.wall) { walls++; break; }
    const gg = T.at(pos[0], pos[2]); if (gg == null) break;
    if (!on && pos[1] - gg < 0.5) air++;
    if (on && res.ground === T.box && Math.abs(pos[1] - gg) > 0.01) off++;
    const dy = Math.abs(pos[1] - py); if (on && dy > 0.2) { pops++; maxPop = Math.max(maxPop, dy); }
  }
}
console.log(id, { runs, ticks, airTicksNearGround: air, pops, maxPop: +maxPop.toFixed(2), hitSomething: walls, offSurface: off });
// spawns: free to stand, on the ground
let bad = 0; for (const p of [...m.spawns, ...((m.teamSpawns && m.teamSpawns.att) || []), ...((m.teamSpawns && m.teamSpawns.def) || [])]) { const h = raycast([p[0], p[1] + 1, p[2]], [0, -1, 0], 6, m.boxes); if (T.at(p[0], p[2]) == null && !playerOverlap(p, m.boxes)) continue; /* (not over shaped ground: the map's own business, a rooftop spawn in the city) */ if (playerOverlap(p, m.boxes) || !h || p[1] - h.point[1] > 2.1 || p[1] < h.point[1] - 0.01) { bad++; console.log('bad spawn', p, h && h.point[1]); } }
console.log(id, 'bad spawns', bad); if (bad) fail = true;
// props: how far is each lifted thing's base from the surface under its corners
console.log(id, 'nav nodes', m.graph.nodes.length);
}
process.exit(fail ? 1 : 0);
