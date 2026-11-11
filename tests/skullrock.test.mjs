// node --test tests/skullrock.test.mjs : Skull Rock is solid where it looks solid and open where it looks open, and
// the bots' ways round it work (shared/skullshape.js, shared/map.js skullRock())
import test from 'node:test';
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';
import { SKULL } from '../shared/skullshape.js';
import { navPath, navLocate } from '../shared/nav.js';
import { movePlayer, playerOverlap } from '../shared/physics.js';

const walk = (boxes, from, pts, speed = 6.5) => { // a body walking from point to point with the game's own physics
  const pos = from.slice(), vel = [0, 0, 0]; let ground = true;
  for (const to of pts) for (let k = 0; k < 600; k++) {
    const dx = to[0] - pos[0], dz = to[2] - pos[2], d = Math.hypot(dx, dz);
    if (d < 0.35) break;
    vel[0] = dx / d * speed; vel[2] = dz / d * speed; vel[1] -= 26 / 30;
    ground = !!movePlayer(pos, vel, 1 / 30, boxes, ground).ground;
  }
  return pos;
};
const near = (p, q, dy = 0.7) => Math.hypot(p[0] - q[0], p[2] - q[2]) < 0.6 && Math.abs(p[1] - q[1]) < dy;

test('Islands: the walk graph takes a bot from the beach up the spine to the crown, into the cave, and out of an eye', () => {
  const g = MAPS.islands.graph;
  assert.deepEqual(g.bad, []);
  const path = (a, b) => navPath(g, navLocate(g, a), navLocate(g, b));
  assert.ok(path([-11, 0.1, 61], [0, SKULL.TOP + 0.1, 70]), 'beach -> crown');
  assert.ok(path([0, SKULL.TOP + 0.1, 70], [-11, 0.1, 61]), 'crown -> beach');
  assert.ok(path([-6, -0.5, 30], [0.5, 0.1, 70.5]), 'sandbar -> the chest');
  assert.ok(path([3.5, SKULL.EYE + 0.1, 62.5], [-11, 0.1, 61]), 'an eye -> beach');
});
test('Islands: a body walks the bots\' route up the spine to the crown and back, and into the cave', () => {
  const B = MAPS.islands.boxes;
  assert.ok(near(walk(B, [0.5, -0.5, 87.5], [[0, 6, 79.4], [0.5, SKULL.TOP, 71.5]]), [0.5, SKULL.TOP, 71.5]), 'up');
  assert.ok(near(walk(B, [0.5, SKULL.TOP, 71.5], [[0, 6, 79.4], [0.5, -0.55, 87.5]]), [0.5, -0.3, 87.5]), 'down');
  const end = walk(B, [-0.5, 0, 57], [[-0.5, 0, 64.5], [0.5, 0, 71.5]]);
  assert.ok(near(end, [0.5, 0, 71.5]) && !playerOverlap(end, B), 'the cave');
  assert.ok(walk(B, [-11.5, 0, 69], [[-9, 0, 69]])[0] < -9.6, 'its side is a wall');
});
test('both maps: room to stand in the eyes and on the crown, none in the rock', () => {
  for (const [id, dz] of [['islands', 0], ['islands_sd', -33]]) {
    const B = MAPS[id].boxes;
    for (const s of [-1, 1]) assert.equal(playerOverlap([s * 3.5, SKULL.EYE + 0.01, 62.7 + dz], B), null, id + ' eye');
    assert.equal(playerOverlap([0, SKULL.TOP + 0.01, 69 + dz], B), null, id + ' crown');
    assert.ok(playerOverlap([6, 2, 70 + dz], B), id + ' inside the jaw is rock');
  }
});
test('Islands S&D: the skull without its spine, the walk graph whole', () => {
  const m = MAPS.islands_sd;
  assert.equal(m.boxes.filter((b) => b.av === 'skullspine').length, 0);
  assert.ok(m.boxes.filter((b) => b.av === 'skullrock').length > 100);
  assert.deepEqual(m.graph.bad, []);
  const B = m.boxes, end = walk(B, [-0.5, 0, 24], [[-0.5, 0, 31.5], [0.5, 0, 38.5]]);
  assert.ok(near(end, [0.5, 0, 38.5]), 'the cave');
});
