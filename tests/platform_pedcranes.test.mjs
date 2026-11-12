// Platform's pedestal cranes (tools/blender/make_pedcrane.py): p_pedcrane (the 34 m boom on its rest) and p_pedcrane_short (the
// 22 m one over the boat), Blender props over pedCrane()'s boxes. look-only: each copy fits its model's outline exactly
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { MAPS } from '../shared/map.js';

const meta = (id) => {
  const buf = fs.readFileSync(new URL(`../public/models/p_${id}.glb`, import.meta.url)), len = buf.readUInt32LE(12);
  return JSON.parse(JSON.parse(buf.slice(20, 20 + len).toString('utf8')).nodes.find((n) => n.extras && n.extras.jf).extras.jf);
};
for (const [map, want] of [['platform', { pedcrane: 1, pedcrane_short: 1 }], ['platform_sd', { pedcrane: 1, pedcrane_short: 0 }]]) {
  for (const [id, n] of Object.entries(want)) {
    test(`${map}: ${n} ${id}, its model's exact outline`, () => {
      const m = MAPS[map], ps = m.boxes.props.filter((q) => q.id === id);
      assert.equal(ps.length, n);
      if (!n) return;
      const mt = meta(id);
      for (const p of ps) for (let i = 0; i < 3; i++) { assert.ok(Math.abs(mt.box[0][i] - p.lo[i]) < 0.01, `lo[${i}] ${mt.box[0][i]} vs ${p.lo[i]}`); assert.ok(Math.abs(mt.box[1][i] - p.hi[i]) < 0.01, `hi[${i}] ${mt.box[1][i]} vs ${p.hi[i]}`); }
      // the boom you walk out on is still a solid box, 1.4 wide, its top at 11.6
      assert.ok(m.boxes.some((b) => b.pv === id && b.mat === 'truss' && b.max[1] === 11.6 && b.max[0] - b.min[0] + b.max[2] - b.min[2] > 20), 'the boom');
    });
  }
}
