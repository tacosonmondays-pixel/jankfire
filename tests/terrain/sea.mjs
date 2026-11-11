// node tests/terrain/sea.mjs : the Islands sea carries you. walk off a beach into deep water, float (head out, never sinking), paddle to the next island and step back out; nothing kills you until the map's edge (map.bounds)
import { MAPS } from '../../shared/map.js';
import { movePlayer, raycast } from '../../shared/physics.js';
import { swim, sink, SWIM } from '../../shared/pits.js';
import { outOfBounds } from '../../shared/bounds.js';
let fail = false; const ok = (c, s) => { console.log(c ? 'PASS' : 'FAIL', s); if (!c) fail = true; };
for (const id of ['islands', 'islands_sd']) {
  const m = MAPS[id], dt = 1 / 60, line = m.seaY - SWIM.seaRide;
  ok(m.seaSwim && m.killY < m.seaY - 20 && !!m.bounds, `${id}: floats, kill line ${m.killY}, bounds ${m.bounds}`);
  // from every spawn, head straight out to sea in four directions for 40 s: never under the float line, never dead; anyone who reaches the edge is out of bounds there (the countdown's job)
  let low = 9, floats = 0, oob = 0, landed = 0, runs = 0;
  for (const sp of m.spawns.slice(0, 8)) for (const [dx, dz] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
    const pos = sp.slice(), vel = [0, 0, 0]; let on = true, fl = false, wasFl = false; runs++;
    for (let t = 0; t < 60 * 40; t++) {
      const sp2 = fl ? 3.6 : 6; vel[0] = dx * sp2; vel[2] = dz * sp2; vel[1] -= 26 * dt;
      sink(m, pos, vel); fl = swim(m, m.boxes, pos, vel, dt);
      const r = movePlayer(pos, vel, dt, m.boxes, on || fl); on = !!r.ground && vel[1] <= 0.01;
      if (fl) { floats++; wasFl = true; } else if (wasFl && on && pos[1] > line + 0.3) { landed++; wasFl = false; }
      low = Math.min(low, pos[1]);
      if (outOfBounds(m, pos)) { oob++; break; }
    }
  }
  ok(low > line - 1.6 && low > m.killY, `${id}: lowest feet ${low.toFixed(2)} (float line ${line.toFixed(2)}, kill ${m.killY})`);
  ok(floats > 1000, `${id}: floated for ${floats} ticks over ${runs} walks out to sea`);
  ok(landed > 0, `${id}: stepped back out of the water onto sand ${landed} times`);
  ok(oob > 0, `${id}: ${oob} of ${runs} swam on out past the edge (out of bounds there)`);
  // a plunge from 12 m over open water: under for a moment, back up, settled at the line
  const far = [m.bounds[2] - 8, 12, 0]; const v = [0, 0, 0]; let lo = 9, set = -1;
  if (!raycast([far[0], 12, 0], [0, -1, 0], 60, m.boxes)) { for (let t = 0; t < 60 * 6; t++) { v[1] -= 26 * dt; sink(m, far, v); swim(m, m.boxes, far, v, dt); movePlayer(far, v, dt, m.boxes, false); lo = Math.min(lo, far[1]); if (set < 0 && t > 30 && Math.abs(far[1] - line) < 0.001) set = t / 60; }
    ok(set > 0 && lo > m.killY + 20, `${id}: plunge from 12 m went down to ${lo.toFixed(2)}, floating again after ${set.toFixed(2)} s`); }
}
process.exit(fail ? 1 : 0);
