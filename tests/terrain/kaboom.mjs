// node tests/terrain/kaboom.mjs : the walk graph gets from each beach and the village up into Mount Kaboom's crater and back, and every step of those routes really walks (shared physics)
import { MAPS } from '../../shared/map.js';
import { navLocate, navPath } from '../../shared/nav.js';
import { movePlayer } from '../../shared/physics.js';
const m = MAPS[process.argv[2] || 'islands'], g = m.graph, T = m.boxes.terrain, dt = 1 / 60;
const walk = (p, q) => { const pos = [p[0], T.at(p[0], p[2]) ?? p[1], p[2]], vel = [0, 0, 0]; let on = true;
  for (let t = 0; t < 150; t++) { const dx = q[0] - pos[0], dz = q[2] - pos[2], d = Math.hypot(dx, dz); if (d < 0.35 && on) return Math.abs(pos[1] - q[1]) < 1.2; vel[0] = dx / Math.max(d, .01) * 6; vel[2] = dz / Math.max(d, .01) * 6; vel[1] -= 26 * dt; const r = movePlayer(pos, vel, dt, m.boxes, on); on = !!r.ground && vel[1] <= 0.01; } return false; };
let fail = 0;
for (const [name, from] of [['west beach', [-26, 0, -3]], ['tiki village', [0, 0, 17]], ['east beach', [26, 0, -3]], ['north', [0, 0, -25]]]) for (const [tn, to] of [['crater', [2.8, 11.5, -3]], ['back down', null]]) {
  const A = tn === 'crater' ? from : [2.8, 11.5, -3], B = tn === 'crater' ? to : from;
  const a = navLocate(g, A), b = navLocate(g, B), path = navPath(g, a, b);
  if (!path) { console.log(name, tn, 'NO PATH'); fail++; continue; }
  let bad = 0, top = 0; for (let i = 1; i < path.length; i++) { const p = g.nodes[path[i - 1]], q = g.nodes[path[i]]; top = Math.max(top, q[1]); if (!walk(p, q)) { bad++; console.log("  bad", p, q); } }
  console.log(name, tn, 'steps', path.length, 'top', top.toFixed(1), 'unwalkable steps', bad); if (bad) fail++;
}
process.exit(fail ? 1 : 0);
