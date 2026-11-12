// node --test tests/story/hug.test.mjs : what lies on the Commute's hills follows them (commute.js hug). A prop resting
// on the ground leans with the slope under it and its footprint's edge never hangs over a dip; a mound, boulder or
// scrub tuft is sheared onto the slope so its base ring lies on the ground; rubble heaps' pieces each sit on the
// ground under them. Collision is untouched (boxes).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildChunk, packChunk } from '../../shared/city/chunk.js';
import { fieldAt } from '../../shared/city/ground.js';
import { FOOT } from '../../shared/city/commute.js';

const chunks = [];
for (let cx = 1; cx < 5; cx++) for (let cz = -4; cz < 4; cz++) chunks.push(packChunk(buildChunk('slice', cx, cz)));
const fieldOf = (p) => p.shapes.find((s) => s.kind === 'field' && s.mat === 'ground');

test('props resting on a slope lean with it and no edge of them hangs over the ground', () => {
  let leaning = 0, checked = 0, worst = 0, at = null;
  for (const p of chunks) {
    const f = fieldOf(p), T = p.ptilt;
    if (!f || !T) continue;
    for (let i = 0; i < p.prop.length / 7; i++) {
      const ax = T[i * 2], az = T[i * 2 + 1];
      if (!ax && !az) continue;
      leaning++;
      const x = p.prop[i * 7 + 1], y = p.prop[i * 7 + 2], z = p.prop[i * 7 + 3], id = p.ids[p.prop[i * 7]];
      // the prop's base plane after its lean: up turned by x then z, so its slope is dy/dx = -tan(az) / ..., dy/dz = tan(ax) / ...
      const nx = -Math.sin(az) * Math.cos(ax), ny = Math.cos(az) * Math.cos(ax), nz = Math.sin(ax);
      const s = p.prop[i * 7 + 5] || 1, rf = (FOOT[id] || 0.6) * s;
      for (const r of [rf * 0.5, rf]) for (let k = 0; k < 8; k++) { // (across its footprint)
        const a = k / 8 * 6.283, dx = Math.cos(a) * r, dz = Math.sin(a) * r, g = fieldAt(f, x + dx, z + dz);
        if (g == null) continue;
        const base = y - (nx * dx + nz * dz) / ny; // (the base plane's height there)
        checked++;
        if (base - g > worst) { worst = base - g; at = [id, x.toFixed(1), z.toFixed(1)]; }
      }
    }
  }
  assert.ok(leaning > 40, 'hardly anything leans: ' + leaning);
  assert.ok(checked > 100);
  assert.ok(worst < 0.06, `${at} hangs ${worst.toFixed(2)} m over the ground`);
});

test("mounds, boulders and scrub are sheared onto the slope: their base ring lies on the ground", () => {
  let n = 0, worst = 0, at = null;
  for (const p of chunks) {
    const f = fieldOf(p);
    if (!f) continue;
    for (const s of p.shapes) if (s.kind === 'blob' && s.shear) {
      n++;
      const R = Array.isArray(s.r) ? s.r : [s.r, s.r, s.r];
      for (let k = 0; k < 12; k++) { // the equator: where the blob meets the ground
        const a = k / 12 * 6.283, x = s.c[0] + Math.cos(a) * R[0], z = s.c[2] + Math.sin(a) * R[2], g = fieldAt(f, x, z);
        if (g == null) continue;
        const y = s.c[1] + s.shear[0] * (x - s.c[0]) + s.shear[1] * (z - s.c[2]);
        if (y - g > worst) { worst = y - g; at = s.c.map((v) => v.toFixed(1)); }
      }
    }
  }
  assert.ok(n > 30, 'hardly any sheared: ' + n);
  assert.ok(worst < 0.06, `a mound at ${at} hangs ${worst.toFixed(2)} m over the slope`);
});
