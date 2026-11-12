// node --test tests/story/bottomstairs.test.mjs : the Bottom's narrow stairs between terraces walk you all the way up
// onto the lane above. they used to end at that lane's 0.9 m lip wall (jump it, or turn round): now the wall has a gap
// at the top of every flight.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { movePlayer, query } from '../../shared/physics.js';
import { SLICE } from '../../shared/city/slice.js';
import { flightLen } from '../../shared/city/kit.js';

const W = new ChunkWorld([]);
for (let cx = -5; cx < 2; cx++) for (let cz = 0; cz < 4; cz++) W.set(cx + ':' + cz, chunkBoxes(packChunk(buildChunk('slice', cx, cz))));
W.sync();
const T = SLICE.bottom, zS = (k) => 256 - T.terr * k, yOf = (k) => k * T.rise;

test('walk up every narrow stair onto the lane above, no jump', () => {
  let walked = 0;
  const stuck = [];
  for (let k = 0; k < T.n - 1; k++) for (let sx = -300 + (k * 23) % 40; sx < 90; sx += 66 + (k * 7) % 12) {
    const zn = zS(k + 1), z0 = zn + flightLen(T.rise) + 1.2;
    // is there a flight here? (a stair the layout skipped, behind a landmark, has no step at its foot)
    const foot = query(W.boxes, sx - 0.5, zn + flightLen(T.rise) - 1, sx + 0.5, zn + flightLen(T.rise) - 0.2, []).some((b) => b.max[1] > yOf(k) + 0.05 && b.max[1] < yOf(k) + 0.5 && b.min[0] <= sx && b.max[0] >= sx);
    if (!foot) continue;
    const pos = [sx, yOf(k) + 0.05, z0];
    let ok = false;
    for (let t = 0; t < 8 && !ok; t += 1 / 60) { movePlayer(pos, [0, -3, -4.5], 1 / 60, W.boxes, true); ok = pos[2] < zn - 2 && Math.abs(pos[1] - yOf(k + 1)) < 0.3; }
    walked++;
    if (!ok) stuck.push(`terrace ${k} stair at x ${sx}: stopped at ${pos.map((v) => v.toFixed(1))}`);
  }
  assert.ok(walked >= 30, 'only found ' + walked + ' stairs');
  assert.deepEqual(stuck, [], stuck.join('\n'));
});
