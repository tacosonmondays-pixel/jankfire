// node --test tests/story/act1drive.test.mjs : the Sauce Run (m02) and the drive into the Gut (m03) in a car, with the
// real car physics (shared/story/drive.js) on the real slice collision. The Unpaid's ramp over the Ring Road collapse:
// fast, you fly the gap and land on the deck past it; slow, you drop into the gap and drive out up the planks; and the
// whole road from the Ring Road over the jump, up the hill, into the Gut, along Peristalsis Avenue and down to the gate
// passes through each mission's zone. (tests/story/e2e/t_act1drive.cjs drives the start of it in a browser, real keys.)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { newCar, stepCar } from '../../shared/story/drive.js';
import { query, raycast } from '../../shared/physics.js';
import { PLACES } from '../../shared/city/slice.js';
import { RAMP } from '../../shared/city/act1set.js';

const W = new ChunkWorld([]);
for (let cx = -5; cx < 5; cx++) for (let cz = -4; cz < 4; cz++) W.set(cx + ':' + cz, chunkBoxes(packChunk(buildChunk('slice', cx, cz))));
W.sync();
const world = { query: (a, b, c, d, out) => query(W.boxes, a, b, c, d, out), raycast: (o, d, m) => raycast(o, d, m, W.boxes) };
const DT = 1 / 60, MID = (RAMP.x0 + RAMP.x1) / 2;

// drive straight north up the middle lane, throttle while under `cap` m/s; returns the samples
function north(z0, cap, secs) {
  const c = newCar('sedan', [MID, 30, z0], Math.PI), out = [], evs = [];
  for (let i = 0; i < secs / DT; i++) { const ev = stepCar(c, { f: Math.hypot(c.vx, c.vz) < cap }, DT, world, {}); evs.push(...ev); out.push([c.z, c.y, c.ground, Math.hypot(c.vx, c.vz)]); }
  return { c, out, evs };
}

test('fast: JUMP IT, fly the collapse, land on the deck past it', () => {
  const { c, out, evs } = north(160, 40, 8);
  const lipV = out.find((s) => s[0] < RAMP.z0 + 1)[3];
  const air = out.filter((s) => s[0] < RAMP.z0 && s[0] > RAMP.exit[0] && !s[2]);
  const dip = Math.min(...out.filter((s) => s[0] < RAMP.z0 - 3 && s[0] > RAMP.exit[1]).map((s) => s[1])); // (the gap's floor is ~15-15.5)
  assert.ok(lipV > 18, 'too slow off the lip: ' + lipV.toFixed(1));
  assert.ok(air.length > 10, 'never left the ground over the gap');
  assert.ok(dip > 15.9, 'fell into the gap (lowest ' + dip.toFixed(2) + ')');
  assert.ok(!evs.some((e) => e.kind === 'eject'), 'thrown out of the car');
  assert.ok(c.z < 40, 'stopped after the landing at z ' + c.z.toFixed(1));
});

test('slow: drop into the gap and drive out up the planks (no soft-lock)', () => {
  const { c, out } = north(118, 7, 22);
  assert.ok(out.some((s) => s[0] < RAMP.z0 - 2 && s[0] > RAMP.exit[1] && s[1] < 16), 'never dropped into the gap');
  assert.ok(c.z < 60, 'stuck in the gap at z ' + c.z.toFixed(1) + ' y ' + c.y.toFixed(1));
});

test('the road: Ring Road -> the jump -> up the hill -> into the Gut -> Peristalsis Avenue -> the gate', () => {
  const ROUTE = [[MID, 150], [MID, 80], [MID, -60], [MID, -150], [150, -172], [60, -164], [60, -188], [8, -188], [8, -130], [-122, -130], [-128, -130], [-44, -130], [-44, -60], [-44, -30], [-44, -17]];
  const P = []; let from = [182.4, 247];
  for (const [x, z] of ROUTE) { const n = Math.max(1, Math.ceil(Math.hypot(x - from[0], z - from[1]) / 3)); for (let i = 1; i <= n; i++) P.push([from[0] + (x - from[0]) * i / n, from[1] + (z - from[1]) * i / n]); from = [x, z]; }
  const c = newCar('sedan', [182.4, 0.3, 247], Math.PI), hit = [];
  const zones = ['commute:ring_road', 'gut:peristalsis', 'gut:border'].map((id) => ({ id, p: PLACES[id].p, r: PLACES[id].r }));
  let k = 0, t = 0, best = 0, bestT = 0;
  while (k < P.length && t < 150) {
    for (let j = k; j < Math.min(P.length, k + 12); j++) if (Math.hypot(P[j][0] - c.x, P[j][1] - c.z) < 4.5) k = j + 1;
    if (k > best) { best = k; bestT = t; }
    assert.ok(t - bestT < 15, `stuck at ${[c.x, c.y, c.z].map((v) => v.toFixed(1))} on the way to ${P[k]}`);
    let tgt = P[Math.min(P.length - 1, k)]; for (let j = k; j < P.length; j++) { tgt = P[j]; if (Math.hypot(P[j][0] - c.x, P[j][1] - c.z) > 9) break; }
    let err = Math.atan2(tgt[0] - c.x, tgt[1] - c.z) - c.h; err = Math.atan2(Math.sin(err), Math.cos(err));
    const sp = Math.hypot(c.vx, c.vz), cap = Math.abs(err) > 0.6 ? 6 : 26, back = t - bestT > 5 && t - bestT < 7.5;
    const ev = stepCar(c, { f: !back && sp < cap, b: back || sp > cap + 6, l: (back ? -err : err) > 0.06, r: (back ? -err : err) < -0.06 }, DT, world, {});
    assert.ok(!ev.some((e) => e.kind === 'eject'), `thrown out at ${[c.x, c.y, c.z].map((v) => v.toFixed(1))}`);
    for (const z of zones) if (!hit.includes(z.id) && Math.hypot(c.x - z.p[0], c.z - z.p[2]) < z.r && Math.abs(c.y - z.p[1]) < 4) hit.push(z.id);
    t += DT;
  }
  assert.equal(k, P.length, 'didn\'t get to the gate');
  assert.deepEqual(hit, zones.map((z) => z.id), 'zones driven through, in order');
  console.log(`  the drive: ${t.toFixed(0)} s from the Ring Road to the gate`);
});
