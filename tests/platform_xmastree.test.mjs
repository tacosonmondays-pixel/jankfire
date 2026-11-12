// Platform's wellhead christmas trees (p_xmastree, tools/blender/make_xmastree.py): six Blender props round each rig's
// wellbay. look-only: the pillar and the cross stay the solid boxes, every tree has the same outline (one fit for all)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { MAPS } from '../shared/map.js';

const buf = fs.readFileSync(new URL('../public/models/p_xmastree.glb', import.meta.url)), len = buf.readUInt32LE(12);
const meta = JSON.parse(JSON.parse(buf.slice(20, 20 + len).toString('utf8')).nodes.find((n) => n.extras && n.extras.jf).extras.jf);

for (const id of ['platform', 'platform_sd']) {
  test(`${id}: six christmas trees, each the model's exact outline`, () => {
    const m = MAPS[id], ps = m.boxes.props.filter((q) => q.id === 'xmastree');
    assert.equal(ps.length, 6);
    for (const p of ps) {
      assert.equal(p.y, 0, 'wings along x');
      for (let i = 0; i < 3; i++) { assert.ok(Math.abs(meta.box[0][i] - p.lo[i]) < 0.01, `lo[${i}] ${meta.box[0][i]} vs ${p.lo[i]}`); assert.ok(Math.abs(meta.box[1][i] - p.hi[i]) < 0.01, `hi[${i}] ${meta.box[1][i]} vs ${p.hi[i]}`); }
    }
    const solid = m.boxes.filter((b) => b.pv === 'xmastree');
    assert.equal(solid.length, 12, 'a pillar and a cross each');
    assert.ok(solid.every((b) => b.mat === 'rigred'));
  });
}
