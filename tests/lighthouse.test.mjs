// node --test tests/lighthouse.test.mjs : the octagonal lighthouse (shared/map.js lighthouse(), octoBoxes, lhStair): the
// iron stair round all eight faces takes you up and down without a snag (small steps, no step you can't just walk up),
// a bot finds its way up from every side, the gallery's railing holds at its cut corners, the bots' walk graph is whole
import test from 'node:test';
import assert from 'node:assert/strict';
import { MAPS, lhStair } from '../shared/map.js';
import { navPath, navLocate, navSteer } from '../shared/nav.js';
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

test('Islands: up the iron stair onto the gallery and back down, near the wall, in the middle and by the rail', () => {
  const m = MAPS.islands, S = lhStair(), C = [82, -6], L = 3 * Math.tan(Math.PI / 8);
  const line = (u) => { const P = []; for (let k = 0; k < 8; k++) { const a = (135 - 45 * k) * Math.PI / 180, n = [Math.cos(a), Math.sin(a)], t = [Math.sin(a), -Math.cos(a)];
    for (const s of [-L + 0.1, L - 0.1]) P.push([C[0] + n[0] * u + t[0] * s, 0, C[1] + n[1] * u + t[1] * s]);
    if (k < 7) { const R = u / Math.cos(Math.PI / 8); P.push([C[0] + Math.cos(a - Math.PI / 8) * R, 0, C[1] + Math.sin(a - Math.PI / 8) * R]); } } return P; };
  for (const u of [3.6, 3.95, 4.2]) for (const sp of [7, 14]) {
    const P = line(u), up = walk(m.boxes, [S.bot[0], 0.05, S.bot[2]], [...P, S.top], sp);
    assert.ok(up[1] > 17.9, `up at ${u}, ${sp} m/s: ${up}`);
    const down = walk(m.boxes, [S.top[0], 18.05, S.top[2]], [...P].reverse().concat([S.bot, [S.bot[0] - 2, 0, S.bot[2]]]), sp), v = [0, 0, 0];
    for (let k = 0; k < 30; k++) { v[1] -= 26 / 30; movePlayer(down, v, 1 / 30, m.boxes, false); } // (landed: running off the bottom step at a sprint you're still in the air)
    assert.ok(down[1] < 0.1, `down at ${u}, ${sp} m/s: ${down}`);
  }
  for (let i = 1; i < 80; i++) assert.ok(Math.abs(S.r * i - S.r * (i - 1) - 0.225) < 1e-9 && S.r < 0.6, 'every step one small step');
  assert.ok(navPath(m.graph, navLocate(m.graph, [80, 0.1, 0]), navLocate(m.graph, [85, 18.1, -10])), 'bot path to the gallery');
});
test('Islands: a bot steering by the walk graph gets up to the gallery from every side, and down again', () => {
  const m = MAPS.islands;
  const run = (from, goal) => {
    const pos = from.slice(), vel = [0, 0, 0], st = {}; let ground = true;
    for (let t = 0; t < 30; t += 1 / 30) {
      const s = navSteer(m.graph, st, pos, goal, t * 1000), l = Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) || 1;
      const [dx, dz] = s ? s : [(goal[0] - pos[0]) / l, (goal[2] - pos[2]) / l];
      if (s && s[2] && ground) vel[1] = 8;
      vel[0] = dx * 7; vel[2] = dz * 7; vel[1] -= 26 / 30;
      ground = !!movePlayer(pos, vel, 1 / 30, m.boxes, ground).ground;
      if (Math.hypot(goal[0] - pos[0], goal[2] - pos[2]) < 0.8 && Math.abs(goal[1] - pos[1]) < 0.5) return true;
    }
    return pos;
  };
  for (const [from, goal] of [[[80, 0.1, 0], [85, 18.1, -10]], [[70, 0.1, -6], [82, 18.1, -11.2]], [[90, 0.1, -6], [87, 18.1, -6]], [[74, 0.1, -12], [85, 18.1, -10]], [[84, 0.1, 4], [77.5, 18.1, -3.5]],
    [[86, 18.1, -11], [80, 0.1, 2]], [[82, 18.1, -11], [90, 0.1, 0]], [[86, 18.1, -3], [70, 0.1, -14]]]) assert.equal(run(from, goal), true, from + ' -> ' + goal);
});
test('Islands: the gallery railing holds, flats and cut corners', () => {
  const B = MAPS.islands.boxes;
  for (const [from, to] of [[[80, 18, -11], [74, 18, -14]], [[86.5, 18, -9], [90, 18, -14]], [[85.6, 18, -3.4], [90, 18, 2]], [[78.6, 18, -2.2], [74, 18, 2]], [[82, 18, -10], [82, 18, -14]], [[86.5, 18, -6], [90, 18, -6]]])
    assert.ok(walk(B, from, [to])[1] > 17.9, 'held from ' + from);
});
test('both maps: walk graphs whole', () => {
  for (const id of ['islands', 'islands_sd']) assert.deepEqual(MAPS[id].graph.bad, []);
});
