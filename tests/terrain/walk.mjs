// node tests/terrain/walk.mjs : walks straight lines over the shaped Desert with the shared physics (stays on the ground, no pops), checks the spawns and the walk graph
import { MAPS } from '../../shared/map.js';
import { movePlayer, playerOverlap, raycast } from '../../shared/physics.js';
const m = MAPS.desert, T = m.boxes.terrain, dt = 1 / 60;
let runs = 0, air = 0, ticks = 0, pops = 0, walls = 0, maxPop = 0, off = 0;
const r = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
for (let k = 0; k < 400; k++) {
  const x = -95 + r() * 190, z = -95 + r() * 190, g = T.at(x, z);
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
console.log({ runs, ticks, airTicksNearGround: air, pops, maxPop: +maxPop.toFixed(2), hitSomething: walls, offSurface: off });
// spawns: free to stand, on the ground
let bad = 0; for (const p of [...m.spawns, ...m.teamSpawns.att, ...m.teamSpawns.def]) { const h = raycast([p[0], p[1] + 1, p[2]], [0, -1, 0], 6, m.boxes); if (playerOverlap(p, m.boxes) || !h || p[1] - h.point[1] > 0.5 || p[1] < h.point[1] - 0.01) { bad++; console.log('bad spawn', p, h && h.point[1]); } }
console.log('bad spawns', bad);
// props: how far is each lifted thing's base from the surface under its corners
const g = m.graph; console.log('nav nodes', g.nodes.length, 'base nodes', MAPS.desert_sd.graph.nodes.length);
