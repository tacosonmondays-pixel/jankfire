// node --test tests/suburb_playground.test.mjs : Suburb's playground slide (shared/map.js suburb(), the Blender chute in
// tools/blender/make_playground.py): its 28 small steps take you up the chute onto the tower's deck and back down without a
// snag, in both lanes and by the walls; every step is under the model's chute line within 5 cm; the walk graph is whole
import test from 'node:test';
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';
import { navPath, navLocate } from '../shared/nav.js';
import { movePlayer } from '../shared/physics.js';

const walk = (boxes, from, pts, speed = 7) => {
  const pos = from.slice(), vel = [0, 0, 0]; let ground = true;
  for (const to of pts) for (let k = 0; k < 600; k++) {
    const dx = to[0] - pos[0], dz = to[2] - pos[2], d = Math.hypot(dx, dz);
    if (d < 0.35) break;
    vel[0] = dx / d * speed; vel[2] = dz / d * speed; vel[1] -= 26 / 30;
    ground = !!movePlayer(pos, vel, 1 / 30, boxes, ground).ground;
  }
  return pos;
};
const OX = -24; // the playground's frame (P = B.local(-24, 0, 0))

test('Suburb: up the slide onto the deck and back down, in both lanes and by the walls, walking and sprinting', () => {
  const B = MAPS.suburb.boxes;
  for (const z of [-4.9, -4.6, -4.0, -3.4, -3.1]) for (const sp of [5, 7, 12]) {
    const up = walk(B, [OX + 0.2, 0.12, z], [[OX - 6.5, 0, z], [OX - 9, 0, -4]], sp);
    assert.ok(up[1] > 3.15, `up the slide at z ${z}, ${sp} m/s: ${up}`);
    const down = walk(B, [OX - 9, 3.25, -4], [[OX - 6.5, 0, z], [OX + 0.5, 0, z]], sp), v = [0, 0, 0];
    for (let k = 0; k < 30; k++) { v[1] -= 26 / 30; movePlayer(down, v, 1 / 30, B, false); }
    assert.ok(down[1] < 0.2 && down[0] > OX - 0.5, `down the slide at z ${z}, ${sp} m/s: ${down}`);
  }
});

test('Suburb: the slide steps sit under the chute line, small steps all the way', () => {
  const S = MAPS.suburb.boxes.filter((b) => b.mat === 'toyteal' && b.min[2] === -5.2 && b.pv === 'playground').sort((a, b) => a.min[0] - b.min[0]);
  assert.equal(S.length, 30);
  const line = (x) => 3.2 - 2.66 * Math.max(0, Math.min(1, (x - OX + 6.14) / 4.55)); // (the model's chute, before its rounding and ripple)
  for (let i = 1; i < S.length; i++) {
    assert.ok(S[i - 1].max[1] - S[i].max[1] <= 0.1, 'a small step down');
    assert.ok(Math.abs(S[i].min[0] - S[i - 1].max[0]) < 1e-9, 'no gaps');
  }
  for (const b of S.slice(1, -1)) for (const x of [b.min[0], (b.min[0] + b.max[0]) / 2, b.max[0]]) assert.ok(Math.abs(line(x) - b.max[1]) <= 0.0476, `step at ${x}`);
});

test('Suburb: bots still cross the park, and the walk graph is whole', () => {
  const g = MAPS.suburb.graph;
  assert.deepEqual(g.bad, []);
  for (const [a, b] of [[[-79.5, 0.2, 0], [79.5, 0.2, 0]], [[-30, 0.2, -12], [-20, 0.2, 12]], [[-24, 0.2, -9], [-24, 0.2, 9]]])
    assert.ok(navPath(g, navLocate(g, a), navLocate(g, b)), a + ' -> ' + b);
});
