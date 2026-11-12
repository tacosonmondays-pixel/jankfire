// node --test tests/suburb_houses.test.mjs : the Suburb houses' hip roofs (shared/map.js hipCap(), the Blender roof in
// tools/blender/arch/hiproof.py): from the curb you walk up the slope onto the top and back down without a snag on every
// house, open or shut, on both maps; the steps are small and stay under the shingles; the walk graphs are whole
import test from 'node:test';
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';
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
const W = (p, lx, lz) => { const [x, z] = [[lx, lz], [-lz, lx], [-lx, -lz], [lz, -lx]][p.r & 3]; return [p.p[0] + x, p.p[2] + z]; }; // (builder local(): the house's frame -> the world)
const houses = (id) => MAPS[id].boxes.arch.filter((a) => a.id === 'home' || a.id === 'home_shut');

test('every house: from the curb up the hip roof onto the top and back down, all four sides', () => {
  let n = 0;
  for (const id of ['suburb', 'suburb_sd']) for (const p of houses(id)) {
    const B = MAPS[id].boxes, top = W(p, 0, 0);
    for (const [lx, lz] of [[0, -5.25], [0, 5.25], [-6.25, 0], [6.25, 0], [-6.25, -5.25]]) { // (the walk stops 0.35 short: on the walkway)
      const [x, z] = W(p, lx, lz);
      const up = walk(B, [x, 7.56, z], [[top[0], 0, top[1]]]);
      assert.ok(up[1] > 8.44, `${id} ${p.id} at ${p.p}: up from ${lx},${lz}: ${up}`);
      const down = walk(B, [top[0], 8.46, top[1]], [[x, 0, z]]), v = [0, 0, 0];
      for (let k = 0; k < 20; k++) { v[1] -= 26 / 30; movePlayer(down, v, 1 / 30, B, true); } // (landed: off the last step you're still in the air)
      assert.ok(Math.abs(down[1] - 7.55) < 0.02, `${id} ${p.id} at ${p.p}: down to ${lx},${lz}: ${down}`);
      n++;
    }
  }
  assert.equal(n, 5 * 16);
});

test('the parapet covers you as before: beside it you stand on the walkway at the old bottom tier\'s height', () => {
  for (const id of ['suburb', 'suburb_sd']) for (const p of houses(id)) {
    if (p.id !== 'home') continue; // (the shut houses have no parapet)
    const B = MAPS[id].boxes;
    for (const [lx, lz] of [[0, -5.25], [0, 5.25], [-6.25, 0], [6.25, 0], [-3, -5.25], [6.25, 3]]) {
      const [x, z] = W(p, lx, lz), at = [x, 8.2, z], v = [0, 0, 0];
      for (let k = 0; k < 30; k++) { v[1] -= 26 / 30; movePlayer(at, v, 1 / 30, B, true); }
      assert.ok(Math.abs(at[1] - 7.55) < 0.02, `${id} at ${p.p}, by the parapet at ${lx},${lz}: ${at}`);
    }
  }
});

test('the roof steps: six of 0.15 from the curb, each under the shingles within 7.5 cm', () => {
  for (const id of ['suburb', 'suburb_sd']) for (const p of houses(id)) {
    const S = MAPS[id].boxes.filter((b) => b.av === p.id && b.ai === MAPS[id].boxes.arch.indexOf(p) && b.min[1] >= 7.549 && b.max[1] <= 8.451 && b.mat.startsWith('roof')).sort((a, b) => a.min[1] - b.min[1]);
    assert.equal(S.length, 6, `${id} ${p.p}`);
    S.forEach((b, i) => {
      assert.ok(Math.abs(b.max[1] - b.min[1] - 0.15) < 1e-9 && Math.abs(b.min[1] - (7.55 + 0.15 * i)) < 1e-9);
      const hx = (b.max[0] - b.min[0]) / 2, hz = (b.max[2] - b.min[2]) / 2, ex = (p.r & 1) ? hz : hx, ez = (p.r & 1) ? hx : hz; // (its half sizes in the house's frame)
      const sx = 7.55 + 0.9 * (5.6 - ex) / 2.8, sz = 7.55 + 0.9 * (4.6 - ez) / 2.4; // (the shingles' height over its edge)
      assert.ok(Math.abs(sx - (b.max[1] - 0.075)) < 0.005 && Math.abs(sz - (b.max[1] - 0.075)) < 0.005, `${id} ${p.p} step ${i}`);
    });
  }
});

test('both maps: walk graphs whole', () => {
  for (const id of ['suburb', 'suburb_sd']) assert.deepEqual(MAPS[id].graph.bad, []);
});
