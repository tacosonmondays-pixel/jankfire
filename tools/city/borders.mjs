// Chunk borders behave like there were none: node tools/city/borders.mjs [city] [x0 z0 x1 z1]
// Builds an area two ways, as streamed chunks (a ChunkWorld) and as one piece (the same generators, unclipped), then:
//  - 4000 rays (bullets) fired along and across the chunk borders: same hit distance in both
//  - 600 grenades (stepProjectile) thrown across borders: same landing spot
//  - players walked along every border line and across it, on the ground and on building floors: same end position,
//    never stopped by a seam where a clipped box meets its other half
// Exit code 1 on any mismatch.
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { CHUNK } from '../../shared/city/plan.js';
import { raycast, movePlayer, stepProjectile, resetGrid } from '../../shared/physics.js';
import '../../shared/city/slice.js';
const a = process.argv.slice(2), city = a[0] || 'stress';
const [X0, Z0, X1, Z1] = a.length >= 5 ? a.slice(1, 5).map(Number) : [-128, -128, 128, 128];
const W = new ChunkWorld([]);
for (let cx = X0 / CHUNK; cx < X1 / CHUNK; cx++) for (let cz = Z0 / CHUNK; cz < Z1 / CHUNK; cz++) W.set(cx + ':' + cz, chunkBoxes(packChunk(buildChunk(city, cx, cz))));
W.sync();
const ONE = chunkBoxes(packChunk(buildChunk(city, 0, 0, [X0, Z0, X1, Z1]))); resetGrid(ONE);
let seed = 99; const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const solidAt = (p, r) => ONE.some((b) => p[0] + r > b.min[0] && p[0] - r < b.max[0] && p[1] + r > b.min[1] && p[1] - r < b.max[1] && p[2] + r > b.min[2] && p[2] - r < b.max[2]); // starts inside a wall: no answer is right
let skipped = 0;
const fails = []; let rays = 0, nades = 0, walks = 0, stuck = 0;
const borders = []; for (let x = X0 + CHUNK; x < X1; x += CHUNK) borders.push(x);
// rays: from random points near a border, aimed across it or exactly along it
for (let i = 0; i < 4000; i++) {
  const bx = borders[(rnd() * borders.length) | 0], along = i % 4 === 0, alongX = rnd() < 0.5;
  const o = [alongX ? bx + (along ? 0 : (rnd() - 0.5) * 20) : X0 + 10 + rnd() * (X1 - X0 - 20), 0.5 + rnd() * 30, alongX ? Z0 + 10 + rnd() * (Z1 - Z0 - 20) : bx + (along ? 0 : (rnd() - 0.5) * 20)];
  let d = along ? (alongX ? [0, (rnd() - 0.5) * 0.4, rnd() < 0.5 ? 1 : -1] : [rnd() < 0.5 ? 1 : -1, (rnd() - 0.5) * 0.4, 0]) : [rnd() - 0.5, (rnd() - 0.6) * 0.6, rnd() - 0.5];
  const l = Math.hypot(...d); d = d.map((v) => v / l);
  const h1 = raycast(o, d, 120, W.boxes), h2 = raycast(o, d, 120, ONE); rays++;
  const t1 = h1 ? h1.t : -1, t2 = h2 ? h2.t : -1;
  if (Math.abs(t1 - t2) > 1e-3) fails.push(['ray', o, d, t1, t2]);
}
// grenades: thrown from one side of a border to the other, 3 s of flight with bounces
const bounce = (pr, boxes) => { for (let k = 0; k < 180; k++) { const h = stepProjectile(pr, 1 / 60, boxes, 18); if (h) { pr.v[h.axis ?? 1] *= -0.4; for (let j = 0; j < 3; j++) pr.v[j] *= 0.8; } } return pr.p; };
for (let i = 0; i < 600; i++) {
  const bx = borders[(rnd() * borders.length) | 0], s = rnd() < 0.5 ? -1 : 1, z = Z0 + 10 + rnd() * (Z1 - Z0 - 20), y = 1 + rnd() * 20;
  const v = [-s * (6 + rnd() * 10), 4 + rnd() * 6, (rnd() - 0.5) * 8], sw = rnd() < 0.5;
  const mk = () => ({ p: sw ? [z, y, bx + s * 4] : [bx + s * 4, y, z], v: sw ? [v[2], v[1], v[0]] : [...v], r: 0.15 });
  if (solidAt(mk().p, 0.15)) { skipped++; continue; }
  const p1 = bounce(mk(), W.boxes), p2 = bounce(mk(), ONE); nades++;
  if (Math.hypot(p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2]) > 1e-3) fails.push(['nade', p1, p2]);
}
// walking: along each border (straddling it) and across it, from ground level and from random heights (lands on floors)
const walk = (boxes, p0, dir, secs) => { const p = [...p0], v = [0, 0, 0]; let g = false; for (let k = 0; k < secs * 60; k++) { v[0] = dir[0] * 7; v[2] = dir[1] * 7; v[1] -= 24 / 60; const r = movePlayer(p, v, 1 / 60, boxes, g); g = !!r.ground; } return p; };
for (let i = 0; i < 400; i++) {
  const bx = borders[(rnd() * borders.length) | 0], c = Z0 + 10 + rnd() * (Z1 - Z0 - 20), y = rnd() < 0.5 ? 0.3 : 1 + rnd() * 30, mode = i % 3;
  const sw = rnd() < 0.5;
  const p0 = mode === 0 ? [bx, y, c] : [bx - 6, y, c], dir = mode === 0 ? [0, rnd() < 0.5 ? 1 : -1] : [1, 0];
  const P = sw ? [p0[2], p0[1], p0[0]] : p0, D = sw ? [dir[1], dir[0]] : dir;
  if (solidAt([P[0], P[1] + 0.9, P[2]], 0.9)) { skipped++; continue; }
  const e1 = walk(W.boxes, P, D, 3), e2 = walk(ONE, P, D, 3); walks++;
  if (Math.hypot(e1[0] - e2[0], e1[1] - e2[1], e1[2] - e2[2]) > 1e-3) fails.push(['walk', P, D, e1, e2]);
  // a seam must never stop you: walking straight across a border on open ground gets you ~21 m
  if (mode !== 0 && Math.abs((D[0] ? e1[0] - P[0] : e1[2] - P[2])) < 1 && Math.abs((D[0] ? e2[0] - P[0] : e2[2] - P[2])) > 1) stuck++;
}
console.log(JSON.stringify({ city, area: [X0, Z0, X1, Z1], chunkBoxes: W.boxes.length, oneBoxes: ONE.length, rays, nades, walks, skippedInsideWalls: skipped, mismatches: fails.length, seamStops: stuck, first: fails.slice(0, 3) }));
process.exit(fails.length || stuck ? 1 : 0);
