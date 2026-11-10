// walk into the pond from the bank and across: wading, then floating with the head out, then out the far side
import { MAPS } from '../../shared/map.js';
import { movePlayer } from '../../shared/physics.js';
import { swim, SWIM } from '../../shared/pits.js';
const m = MAPS.desert, T = m.boxes.terrain, dt = 1 / 60, top = m.pools[0].top;
const pos = [22, T.at(22, 61), 61], vel = [0, 0, 0]; let on = true, log = [], fl = 0, minY = 9, maxUnder = 0;
for (let t = 0; t < 60 * 14; t++) {
  vel[0] = 3.2; vel[2] = 0; vel[1] -= 26 * dt;
  const res = movePlayer(pos, vel, dt, m.boxes, on); on = !!res.ground && vel[1] <= 0.01;
  const f = swim(m, m.boxes, pos, vel, dt); if (f) fl++;
  minY = Math.min(minY, pos[1]); maxUnder = Math.max(maxUnder, top - (pos[1] + 1.6));
  if (t % 45 === 0) log.push(`x${pos[0].toFixed(1)} feet${pos[1].toFixed(2)} bed${T.at(pos[0], pos[2]).toFixed(2)} ${f ? 'FLOAT' : on ? 'ground' : 'air'}`);
}
console.log(log.join('\n')); console.log({ floatTicks: fl, lowestFeet: +minY.toFixed(2), eyesUnderBy: +maxUnder.toFixed(2), line: top - SWIM.ride, endX: +pos[0].toFixed(1) });
// a plunge from 6 m up over the middle: goes under, comes back up, settles
const p = [36, 6, 61], v = [0, 0, 0]; let low = 9, settle = -1;
for (let t = 0; t < 60 * 6; t++) { v[1] -= 26 * dt; movePlayer(p, v, dt, m.boxes, false); swim(m, m.boxes, p, v, dt); low = Math.min(low, p[1]); if (settle < 0 && t > 30 && Math.abs(p[1] - (top - SWIM.ride)) < 0.001 && v[1] === 0) settle = t / 60; }
console.log('plunge: lowest feet', low.toFixed(2), 'bed', T.at(36, 61).toFixed(2), 'settled after s', settle);
// diving: hold crouch in the middle and you go down to the bed, let go and you come back up
{ const p = [36, top - SWIM.ride, 61], v = [0, 0, 0]; let on = false, down = -1, up = -1;
  for (let t = 0; t < 60 * 8; t++) { const dive = t < 60 * 4; v[1] -= 26 * dt; const r = movePlayer(p, v, dt, m.boxes, on); on = !!r.ground && v[1] <= 0.01; swim(m, m.boxes, p, v, dt, dive);
    if (down < 0 && on) down = t / 60; if (!dive && up < 0 && Math.abs(p[1] - (top - SWIM.ride)) < 0.001) up = t / 60 - 4; }
  console.log('dive: on the bed after s', down, '| back at the surface s after letting go', +up.toFixed(2)); }
