// node --test tests/volcano_sd.test.mjs : Islands S&D's volcano (shared/map.js volcano(), drawn by volcano_sd.glb): its
// terraces cut across the corners and its stone steps (0.3 m) still take you from the beach to the crater by both
// sides, a bot steering by the walk graph gets up from either spawn, and the walk graph is whole
import test from 'node:test';
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';
import { navSteer } from '../shared/nav.js';
import { movePlayer } from '../shared/physics.js';

const m = MAPS.islands_sd, dz = -10, P = (x, y, z) => [x, y, z + dz]; // (the volcano's own frame: it stands 10 m north)
const walk = (from, pts, speed = 7) => {
  const pos = from.slice(), vel = [0, 0, 0]; let ground = true;
  for (const to of pts) for (let k = 0; k < 600; k++) {
    const dx = to[0] - pos[0], dz2 = to[2] - pos[2], d = Math.hypot(dx, dz2);
    if (d < 0.35) break;
    vel[0] = dx / d * speed; vel[2] = dz2 / d * speed; vel[1] -= 26 / 30;
    ground = !!movePlayer(pos, vel, 1 / 30, m.boxes, ground).ground;
  }
  return pos;
};
test('Islands S&D volcano: up the south side and the east side to the crater, and up the west side and the north stair', () => {
  for (const sp of [7, 12]) {
    const a = walk(P(0, 0.1, 17), [P(0, 3, 8), P(11, 3, 7), P(14.6, 3, -2), P(9, 6, -2), P(5, 6, 6.8), P(0, 6, 6.9), P(0, 9, 1.5)], sp);
    assert.ok(a[1] > 8.9, `south and east, ${sp} m/s: ${a}`);
    const b = walk(P(-23, 0.1, -7), [P(-19.6, 0, -7.2), P(-13, 3, -7.2), P(-12, 3, 1.75), P(-14.6, 3, 1.75), P(-9, 6, 1.75), P(-7, 6, -10), P(-4, 6, -12.8), P(0, 6, -12.9), P(0, 9, -7.5)], sp);
    assert.ok(b[1] > 8.9, `west and north, ${sp} m/s: ${b}`);
  }
});
test('Islands S&D volcano: a bot steering by the walk graph gets up from either spawn and back down', () => {
  const run = (from, goal) => {
    const pos = from.slice(), vel = [0, 0, 0], st = {}; let ground = true;
    for (let t = 0; t < 45; t += 1 / 30) {
      const s = navSteer(m.graph, st, pos, goal, t * 1000), l = Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) || 1;
      const [dx, dz2] = s ? s : [(goal[0] - pos[0]) / l, (goal[2] - pos[2]) / l];
      if (s && s[2] && ground) vel[1] = 8;
      vel[0] = dx * 7; vel[2] = dz2 * 7; vel[1] -= 26 / 30;
      ground = !!movePlayer(pos, vel, 1 / 30, m.boxes, ground).ground;
      if (Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) < 0.8 && Math.abs(goal[1] - pos[1]) < 0.5) return true;
    }
    return pos;
  };
  for (const [from, goal] of [[[0, 0.1, 46], P(3.5, 9.1, 0)], [[-4, 0.1, -60], P(-3.5, 9.1, -6)], [P(3.5, 9.1, 0), [6, 0.1, 2.5]], [[-48, 0.1, -16], P(-12, 3.1, -2)], [[48, 0.1, -16], P(-5, 6.1, -11)]])
    assert.equal(run(from, goal), true, from + ' -> ' + goal);
});
test('Islands S&D: walk graph whole', () => assert.deepEqual(m.graph.bad, []));
