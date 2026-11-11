// node --test tests/story/terrain.test.mjs : the Commute's hills (shared/city/ground.js). What you see is what you stand
// on (the drawn grid, the physics' heightfield and the hidden steps agree), chunks meet at their seams, nothing is too
// steep to walk, a player walks across the wasteland without catching on a step, a car drives over the hills and down
// a gully without bouncing off box edges, and the bots' walk graph crosses it.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { buildChunkNav, NavWorld } from '../../shared/city/cnav.js';
import { meshChunk } from '../../shared/city/mesh.js';
import { newCar, stepCar } from '../../shared/story/drive.js';
import { query, raycast, movePlayer } from '../../shared/physics.js';
import { commuteY, FLAT } from '../../shared/city/ground.js';
import { SLICE, PLACES, groundY } from '../../shared/city/slice.js';

const W = new ChunkWorld([]), N = new NavWorld(), P = new Map();
for (let cx = 1; cx < 5; cx++) for (let cz = -4; cz < 4; cz++) { const p = packChunk(buildChunk('slice', cx, cz)); P.set(cx + ':' + cz, p); W.set(cx + ':' + cz, chunkBoxes(p)); N.set(cx, cz, buildChunkNav(p)); }
W.sync();
// the ground on its own (its hidden steps and its grid, none of the junk standing on it): walking and driving over the
// hills is tested on this, so a ruined wall in the way doesn't hide a step that catches you
const G = new ChunkWorld([]);
for (const [k, l] of W.chunks) G.set(k, Object.assign(l.filter((b) => b.ter), { fields: l.fields }));
G.sync();
const T = W.boxes.terrain, field = (k) => P.get(k).shapes.find((s) => s.kind === 'field');
const world = { query: (a, b, c, d, out) => query(G.boxes, a, b, c, d, out), raycast: (o, d, m) => raycast(o, d, m, G.boxes) };

test('every Commute chunk has its ground, and neighbours meet exactly at the seam', () => {
  assert.ok(T, 'no heightfield on the loaded chunks');
  for (const [k, p] of P) {
    const f = field(k);
    assert.ok(f, 'no ground in chunk ' + k);
    const [cx, cz] = k.split(':').map(Number), e = P.get(cx + 1 + ':' + cz), s = P.get(cx + ':' + (cz + 1));
    if (e) { const g = field(cx + 1 + ':' + cz); for (let j = 0; j <= f.nz; j++) assert.equal(f.H[f.nx * (f.nz + 1) + j], g.H[j], 'east seam ' + k); }
    if (s) { const g = field(cx + ':' + (cz + 1)); for (let i = 0; i <= f.nx; i++) assert.equal(f.H[i * (f.nz + 1) + f.nz], g.H[i * (g.nz + 1)], 'south seam ' + k); }
  }
});

test('nothing steeper than you can walk or drive up', () => {
  let worst = 0, at = null;
  for (let x = 98; x < 318; x += 2) for (let z = -254; z < 254; z += 2) {
    const a = T.at(x, z), s = Math.max(Math.abs(T.at(x + 2, z) - a), Math.abs(T.at(x, z + 2) - a)) / 2;
    if (s > worst) { worst = s; at = [x, z]; }
  }
  assert.ok(worst < 0.34, `a ${(worst * 100).toFixed(0)}% slope at ${at}`);
});

test('what you see is what you stand on: the drawn grid, the heightfield, rays and the hidden steps agree', () => {
  const m = meshChunk(P.get('3:0'), 0).solid, f = field('3:0');
  let hits = 0;
  for (let v = 0; v < m.verts; v++) { // the drawn ground's points are the grid's points
    const x = m.pos[v * 3], y = m.pos[v * 3 + 1], z = m.pos[v * 3 + 2];
    if (!Number.isInteger((x - f.x0) / f.cell) || !Number.isInteger((z - f.z0) / f.cell) || Math.abs(T.at(x, z) - y) > 1e-4) continue;
    hits++;
  }
  assert.ok(hits >= (f.nx + 1) * (f.nz + 1), 'the drawn ground is not the grid (' + hits + ' points match)');
  let worst = 0;
  for (let i = 0; i < 400; i++) { // a bullet straight down lands on the ground you see, not on a step
    const x = 130 + ((i * 37) % 180), z = -240 + ((i * 53) % 480), g = T.at(x, z);
    if (g == null) continue;
    const h = raycast([x, g + 20, z], [0, -1, 0], 60, W.boxes);
    worst = Math.max(worst, Math.abs(h.point[1] - g) - (h.box.ter === 1 ? 0 : 99));
    if (h.box === T.box) assert.ok(Math.abs(h.point[1] - g) < 0.03, `ray off the ground at ${x},${z}: ${h.point[1]} vs ${g}`);
  }
  for (const b of W.boxes) if (b.ter) { // the steps under it stay within a few cm of the surface over their whole cell
    for (const [x, z] of [[b.min[0] + 0.01, b.min[2] + 0.01], [b.max[0] - 0.01, b.max[2] - 0.01], [(b.min[0] + b.max[0]) / 2, (b.min[2] + b.max[2]) / 2]]) {
      const g = T.at(x, z);
      assert.ok(g != null && Math.abs(b.max[1] - g) < 0.75, `a hidden step ${b.max[1].toFixed(2)} vs the ground ${g} at ${x},${z}`);
    }
  }
});

test('walk the wasteland: over hills and through gullies without catching on a step', () => {
  const lines = [[[100, 40], [160, 40]], [[205, 150], [312, 150]], [[205, -20], [312, -120]], [[230, -230], [300, 200]], [[110, -230], [150, 100]], [[250, 200], [250, -230]]];
  for (const [a, b] of lines) {
    const pos = [a[0], T.at(a[0], a[1]) + 0.05, a[1]], d = [b[0] - a[0], b[1] - a[1]], L = Math.hypot(...d), v = [d[0] / L * 6, 0, d[1] / L * 6];
    let maxOff = 0, t = 0, ground = true;
    for (; t < L / 6 + 3; t += 1 / 60) {
      const vel = [v[0], ground ? -2 : pos[1] > T.at(pos[0], pos[2]) + 0.05 ? -9 : -2, v[2]];
      const r = movePlayer(pos, vel, 1 / 60, G.boxes, true);
      ground = !!r.ground;
      const g = T.at(pos[0], pos[2]);
      if (g != null) maxOff = Math.max(maxOff, Math.abs(pos[1] - g));
      if (Math.hypot(pos[0] - b[0], pos[2] - b[1]) < 1) break;
    }
    const left = Math.hypot(pos[0] - b[0], pos[2] - b[1]);
    assert.ok(left < 1, `walk ${a} -> ${b} stuck at ${pos.map((q) => q.toFixed(1))}`);
    assert.ok(maxOff < 0.12, `walk ${a} -> ${b}: ${maxOff.toFixed(2)} m off the ground you see`);
  }
});

test('drive across the wasteland: up the hills, down a gully, no bouncing off box edges', () => {
  // (h: 0 drives south, +z; PI / 2 east)
  for (const [p, h, secs] of [[[208, 0, 170], Math.PI / 2, 6], [[300, 0, 200], Math.PI, 14], [[250, 0, 230], Math.PI, 26], [[214, 0, -40], Math.PI / 2 + 0.6, 5], [[130, 0, 100], Math.PI, 12], [[110, 0, -200], 0.3, 10]]) {
    p[1] = T.at(p[0], p[2]) + 0.05;
    const c = newCar('sedan', p, h), evs = [];
    let air = 0, far = 0;
    for (let i = 0; i < secs * 60; i++) {
      evs.push(...stepCar(c, { f: Math.hypot(c.vx, c.vz) < 16 }, 1 / 60, world, {}));
      if (!c.ground) air++;
      far = Math.max(far, Math.hypot(c.x - p[0], c.z - p[2]));
      const g = T.at(c.x, c.z); // (a car rides on the highest of its wheels: on a slope its middle is up to ~0.5 m over the ground)
      if (g != null && c.ground) assert.ok(c.y - g > -0.03 && c.y - g < 0.6, `the car floats or sinks at ${c.x.toFixed(1)},${c.z.toFixed(1)}: ${c.y.toFixed(2)} vs ${g.toFixed(2)}`);
    }
    const hits = evs.filter((e) => e.crash || e.eject);
    console.log(`  drive from ${p.map((q) => q.toFixed(0))}: ${far.toFixed(0)} m, ${(air / 60).toFixed(2)} s in the air, ${hits.length} crashes`);
    assert.ok(far > secs * 9, `the car got ${far.toFixed(0)} m from ${p}`);
    assert.equal(hits.length, 0, 'crashed into the ground: ' + JSON.stringify(hits));
    assert.ok(air < secs * 60 * 0.12, `bounced: ${(air / 60).toFixed(2)} s in the air`);
  }
});

test('the bots walk it: the camp, the fallen 13, the Loop and the road meet up', () => {
  const at = (x, z) => [x, T.at(x, z), z];
  const C = SLICE.camp, D = SLICE.digit, L = PLACES['commute:underhill_loop'].p;
  for (const [a, b] of [[at(C.x, C.z + 20), at(D.x - 4, D.z + 14)], [at(D.x - 4, D.z + 14), at(L[0] - 12, L[2])], [at(C.x, C.z + 20), at(140, 60)], [at(140, 60), at(130, -60)]]) assert.ok(N.path(a, b, 3e6), `no walk ${a.map((q) => q.toFixed(0))} -> ${b.map((q) => q.toFixed(0))}`);
});

test('things built on the old flat ground still sit on it', () => {
  for (const f of FLAT) if (typeof f[4] === 'number') for (const [x, z] of [[(f[0] + f[2]) / 2, (f[1] + f[3]) / 2]]) {
    const xx = Math.min(319, Math.max(96, x)), zz = Math.min(255, Math.max(-255, z));
    assert.ok(Math.abs(commuteY(xx, zz) - f[4]) < 0.06, `the level patch ${f.slice(0, 4)} isn't level at ${xx},${zz}: ${commuteY(xx, zz)} vs ${f[4]}`);
  }
  assert.equal(groundY(250, 0), commuteY(250, 0), "slice.js groundY doesn't know about the hills");
});
