// node --test tests/lighthouse.test.mjs : the octagonal lighthouse (shared/map.js lighthouse(), octoBoxes): the stair
// still takes you to the gallery, the gallery's railing holds at its cut corners, the bots' walk graph is whole
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

test('Islands: up the outside stair onto the gallery, and a bot route there', () => {
  const m = MAPS.islands, g = m.graph;
  const end = walk(m.boxes, [78, 0, -2.2], [[86, 4.5, -2.2], [85.8, 4.5, -2.3], [85.8, 9, -9.8], [85.8, 9, -9.8], [78.2, 13.5, -9.8], [78.2, 13.5, -9.6], [78.2, 18, -2.5]]);
  assert.ok(end[1] > 17.9, 'on the gallery: ' + end);
  assert.ok(navPath(g, navLocate(g, [80, 0.1, 0]), navLocate(g, [86, 18.1, -11])), 'bot path to the gallery');
});
test('Islands: the gallery railing holds, flats and cut corners', () => {
  const B = MAPS.islands.boxes;
  for (const [from, to] of [[[80, 18, -11], [74, 18, -14]], [[86.5, 18, -9], [90, 18, -14]], [[85.6, 18, -3.4], [90, 18, 2]], [[78.6, 18, -2.2], [74, 18, 2]], [[82, 18, -10], [82, 18, -14]], [[86.5, 18, -6], [90, 18, -6]]])
    assert.ok(walk(B, from, [to])[1] > 17.9, 'held from ' + from);
});
test('both maps: walk graphs whole', () => {
  for (const id of ['islands', 'islands_sd']) assert.deepEqual(MAPS[id].graph.bad, []);
});
