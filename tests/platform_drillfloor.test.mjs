// Platform's drilling side under and on the drill floor (tools/blender/make_drillfloor.py): p_substructure (the columns,
// girders, the BOP stack down to the cellar deck, the mud tanks and pumps) and p_drillfloor (the rotary table, the
// drawworks, the doghouse). look-only: their solid boxes stay (the TDM defenders spawn among them)
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { MAPS } from '../shared/map.js';

const meta = (id) => {
  const buf = fs.readFileSync(new URL(`../public/models/p_${id}.glb`, import.meta.url)), len = buf.readUInt32LE(12);
  return JSON.parse(JSON.parse(buf.slice(20, 20 + len).toString('utf8')).nodes.find((n) => n.extras && n.extras.jf).extras.jf);
};
for (const [map, dz] of [['platform', 0], ['platform_sd', -44]]) {
  for (const [id, y, solid] of [['substructure', 0, 12], ['drillfloor', 7.2, 2]]) {
    test(`${map}: the ${id}, its model's exact outline`, () => {
      const m = MAPS[map], ps = [...m.boxes.props, ...m.deco.props].filter((q) => q.id === id), mt = meta(id);
      assert.equal(ps.length, 1);
      assert.deepEqual(ps[0].a, [-24, y, dz]);
      for (let i = 0; i < 3; i++) { assert.ok(Math.abs(mt.box[0][i] - ps[0].lo[i]) < 0.01, `lo[${i}] ${mt.box[0][i]} vs ${ps[0].lo[i]}`); assert.ok(Math.abs(mt.box[1][i] - ps[0].hi[i]) < 0.01, `hi[${i}] ${mt.box[1][i]} vs ${ps[0].hi[i]}`); }
      assert.equal(m.boxes.filter((b) => b.pv === id).length, solid, 'its solid boxes are tagged');
      assert.ok(!m.boxes.some((b) => b.pv === id && b.mat === 'deckplate'), 'the drill floor\'s deck plate stays the game\'s');
    });
  }
}
