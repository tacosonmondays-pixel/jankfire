// node --test tests/story/stairs.test.mjs : no stairs to nowhere, no bare cliffs (the owner's playtest: "a rectangular
// cliff with stairs that don't even go all the way"). over the whole slice (80 chunks):
//   - every flight of steps (kit.js stairsZ / stairsX, logged by STAIRS.log while the chunks build) starts on a floor,
//     ends on one (ahead or to the side), and a player holding forward walks from its foot to its top
//   - no tall cliff face (dirt, flesh, rubble... over 2 m above the floor in front) has a bare run of 8 m or more:
//     something dresses it (a shape, a render panel, a prop) or another material clads it (a retaining wall)
// the Gut border's bone stairs used to run 2 m into the cliff and stop a step short of the top; the south lip's stairs
// were clipped away to nothing; the Bottom's outside stairs hung in the air or climbed into the floor above
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { raycast, movePlayer } from '../../shared/physics.js';
import { STAIRS } from '../../shared/city/kit.js';
import { MATS } from '../../shared/city/plan.js';
import { SLICE } from '../../shared/city/slice.js';

const flights = new Map(), chunks = [], W = new ChunkWorld([]);
STAIRS.log = (f) => { if (f.chunk) flights.set([f.axis, f.w0, f.w1, f.a0, f.dir, f.ya, f.yb].map((v) => (typeof v === 'number' ? v.toFixed(2) : v)).join('|'), f); };
for (let cx = -5; cx < 5; cx++) for (let cz = -4; cz < 4; cz++) { const o = buildChunk('slice', cx, cz); chunks.push(o); W.set(cx + ':' + cz, chunkBoxes(packChunk(o))); }
STAIRS.log = null;
W.sync();
const floorAt = (x, z, from) => { const h = raycast([x, from, z], [0, -1, 0], 80, W.boxes); return h ? h.point[1] : -99; };

test('every flight of steps starts on a floor, reaches one, and you can walk up it', () => {
  const bad = [];
  let n = 0;
  for (const f of flights.values()) {
    if (Math.abs(f.yb - f.ya) < 0.3) continue;
    n++;
    const lo = Math.min(f.ya, f.yb), hi = Math.max(f.ya, f.yb), up = f.yb > f.ya, d = up ? f.dir : -f.dir;
    const topAt = up ? f.end + f.dir * 0.35 : f.a0 - f.dir * 0.35, botAt = up ? f.a0 - f.dir * 0.35 : f.end + f.dir * 0.35, lastStep = up ? f.end - f.dir * 0.27 : f.a0 + f.dir * 0.27;
    const pt = (along, w) => (f.axis === 'z' ? [w, along] : [along, w]), probs = [];
    for (const ac of [0.25, 0.5, 0.75]) {
      const w = f.w0 + (f.w1 - f.w0) * ac, t = floorAt(...pt(topAt, w), hi + 1.7), b = floorAt(...pt(botAt, w), lo + 1.7);
      const side = [f.w0 - 0.45, f.w1 + 0.45].some((sw) => Math.abs(floorAt(...pt(lastStep + d * 0.54, sw), hi + 1.7) - hi) <= 0.45); // (stepped off sideways)
      if (Math.abs(t - hi) > 0.45 && !side) probs.push(`top ${(t - hi).toFixed(2)}`);
      if (Math.abs(b - lo) > 0.45) probs.push(`foot ${(b - lo).toFixed(2)}`);
    }
    const [sx, sz] = pt(botAt - d * 0.6, (f.w0 + f.w1) / 2), pos = [sx, floorAt(sx, sz, lo + 1.7) + 0.02, sz], v = f.axis === 'z' ? [0, 0, d * 5] : [d * 5, 0, 0];
    let ground = true;
    for (let i = 0; i < 360 && ((f.axis === 'z' ? pos[2] : pos[0]) - topAt) * d < 0.2; i++) ground = !!movePlayer(pos, [v[0], ground ? -2 : -9, v[2]], 1 / 60, W.boxes, true).ground;
    if (pos[1] < hi - 0.3) probs.push(`walking up stops at ${pos.map((q) => q.toFixed(1))}`);
    if (probs.length) bad.push(`${f.axis} ${f.w0.toFixed(1)}..${f.w1.toFixed(1)} from ${f.a0.toFixed(1)} y ${f.ya.toFixed(1)}->${f.yb.toFixed(1)}: ${[...new Set(probs)].join(', ')}`);
  }
  assert.ok(n > 100, `only ${n} flights logged`);
  assert.deepEqual(bad, [], `${bad.length} of ${n} flights go nowhere`);
});

test('the Gut border has its stairs and the south lip has its own', () => {
  const at = (z0, z1, y) => [...flights.values()].filter((f) => f.axis === 'z' && Math.min(f.a0, f.end) >= z0 - 0.1 && Math.max(f.a0, f.end) <= z1 + 0.1 && Math.max(f.ya, f.yb) === y);
  assert.equal(at(-46, -30, SLICE.gut.y).length, 7, 'the bone stairs up the cliff (the gate and six avenues)');
  assert.ok(at(0, 8, SLICE.border.y).length >= 6, 'the stairs up the south lip');
  for (const f of at(0, 8, SLICE.border.y)) assert.ok(chunks.some((o) => o.cz === 0 && o.boxes.some((b) => b[0] < f.w1 && b[3] > f.w0 && b[2] < 1 && b[4] > SLICE.border.y - 0.5)), `the lip stairs at ${f.w0} aren't built`);
});

test('no tall cliff face is left bare', () => {
  const TERRAIN = new Set(['ground', 'flesh', 'rubble', 'ash', 'liver', 'bruise', 'blood', 'gums']), art = [], clad = [];
  for (const o of chunks) {
    for (const s of o.shapes) if (s.kind !== 'field') { for (const p of s.pts || s.q || [s.c || s.at]) if (p) art.push(p); }
    for (const dd of o.deco) art.push([dd[0], dd[1], dd[2]]);
    for (const p of o.props) art.push([p[1], p[2], p[3]]);
    for (const b of o.boxes) { if (b[7] & 1) for (const t of [0.25, 0.5, 0.75]) art.push([b[0] + (b[3] - b[0]) * t, (b[1] + b[4]) / 2, b[2] + (b[5] - b[2]) * t]); if (!(b[7] & 2) && !TERRAIN.has(MATS[b[6]][0]) && b[4] - b[1] > 1.2) clad.push(b); }
  }
  const dressed = (x, z, y0, y1) => art.some((p) => Math.abs(p[0] - x) < 1.2 && Math.abs(p[2] - z) < 1.2 && Math.hypot(p[0] - x, p[2] - z) < 1.2 && p[1] > y0 - 1 && p[1] < y1 + 1);
  const cladAt = (x, y, z) => clad.some((b) => x >= b[0] - 0.05 && x <= b[3] + 0.05 && z >= b[2] - 0.05 && z <= b[5] + 0.05 && y >= b[1] && y <= b[4]);
  const bare = [], seen = new Set();
  for (const o of chunks) for (const b of o.boxes) {
    if (b[7] & 3 || !TERRAIN.has(MATS[b[6]][0]) || b[4] - b[1] < 2) continue;
    if (b[0] < SLICE.x0 + 8 || b[3] > SLICE.x1 - 8 || b[2] < SLICE.z0 + 8 || b[5] > SLICE.z1 - 8) continue; // (the world's edge walls)
    for (const [ax, fixed, out] of [['x', b[2], -1], ['x', b[5], 1], ['z', b[0], -1], ['z', b[3], 1]]) {
      let run = 0;
      for (let a = (ax === 'x' ? b[0] : b[2]) + 0.5; a < (ax === 'x' ? b[3] : b[5]); a += 1.5) {
        const [x, z] = ax === 'x' ? [a, fixed + out * 0.5] : [fixed + out * 0.5, a], fl = floorAt(x, z, b[4] - 0.05), key = Math.round(x * 2) + ':' + Math.round(z * 2);
        const [fx, fz] = ax === 'x' ? [a, fixed] : [fixed, a];
        if (b[4] - fl < 2 || fl < -50 || seen.has(key) || dressed(fx, fz, fl, b[4]) || cladAt(fx, (fl + b[4]) / 2, fz)) { run = 0; continue; }
        seen.add(key);
        if ((run += 1.5) === 9) bare.push(`${MATS[b[6]][0]} face at ${fx.toFixed(1)},${fz.toFixed(1)} (${(b[4] - fl).toFixed(1)} m tall)`);
      }
    }
  }
  assert.deepEqual(bare, [], `${bare.length} bare cliff faces`);
});
