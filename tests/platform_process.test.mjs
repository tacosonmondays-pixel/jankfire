// Platform's process deck (tools/blender/make_process.py): the separators (p_separator) and the pipe rack (p_piperack)
// are Blender props over their boxes on both rig maps. look-only: every copy fits its model's outline exactly
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { MAPS } from '../shared/map.js';

const meta = (id) => {
  const buf = fs.readFileSync(new URL(`../public/models/p_${id}.glb`, import.meta.url)), len = buf.readUInt32LE(12);
  return JSON.parse(JSON.parse(buf.slice(20, 20 + len).toString('utf8')).nodes.find((n) => n.extras && n.extras.jf).extras.jf);
};
for (const [map, n] of [['platform', 2], ['platform_sd', 1]]) {
  for (const [id, copies, solid] of [['separator', n, 7], ['piperack', 1, 22]]) {
    test(`${map}: ${copies} ${id}, each the model's exact outline`, () => {
      const m = MAPS[map], ps = m.boxes.props.filter((q) => q.id === id), mt = meta(id);
      assert.equal(ps.length, copies);
      for (const p of ps) for (let i = 0; i < 3; i++) { assert.ok(Math.abs(mt.box[0][i] - p.lo[i]) < 0.01, `lo[${i}] ${mt.box[0][i]} vs ${p.lo[i]}`); assert.ok(Math.abs(mt.box[1][i] - p.hi[i]) < 0.01, `hi[${i}] ${mt.box[1][i]} vs ${p.hi[i]}`); }
      assert.equal(m.boxes.filter((b) => b.pv === id).length, copies * solid, 'its solid boxes are tagged');
    });
  }
}
