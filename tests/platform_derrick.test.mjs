// Platform's derrick (p_derrick, tools/blender/make_derrick.py): one Blender model over the derrick's boxes on both rig
// maps. look-only: the solid boxes (the bottom section's legs, the monkey board and its rails) stay where they were
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { MAPS } from '../shared/map.js';

const glb = () => {
  const buf = fs.readFileSync(new URL('../public/models/p_derrick.glb', import.meta.url)), len = buf.readUInt32LE(12);
  const gl = JSON.parse(buf.slice(20, 20 + len).toString('utf8'));
  return JSON.parse(gl.nodes.find((n) => n.extras && n.extras.jf).extras.jf);
};

for (const [id, dz] of [['platform', 0], ['platform_sd', -44]]) {
  test(`${id}: the derrick is one prop placement, its model built to exactly its boxes`, () => {
    const m = MAPS[id], meta = glb();
    const ps = m.boxes.props.filter((q) => q.id === 'derrick');
    assert.equal(ps.length, 1, 'one derrick');
    const p = ps[0];
    assert.deepEqual(p.a, [-24, 7.2, dz], 'standing in the middle of the drill floor');
    for (let i = 0; i < 3; i++) { assert.ok(Math.abs(meta.box[0][i] - p.lo[i]) < 0.01, `lo[${i}] ${meta.box[0][i]} vs ${p.lo[i]}`); assert.ok(Math.abs(meta.box[1][i] - p.hi[i]) < 0.01, `hi[${i}] ${meta.box[1][i]} vs ${p.hi[i]}`); }
    // the solid ones: four legs of the bottom section, the monkey board, its three top rails
    const solid = m.boxes.filter((b) => b.pv === 'derrick');
    assert.equal(solid.length, 8, 'eight solid boxes under the model');
    assert.equal(solid.filter((b) => b.mat === 'rigred' && b.min[1] === 7.2 && b.max[1] === 13.2).length, 4, 'the four legs');
    assert.ok(solid.some((b) => b.mat === 'grating' && b.min[1] === 22.2), 'the monkey board');
    // the GLUG board is the model's now (it's drawn on stand-offs); the drill floor and its stairs aren't the derrick's
    assert.ok(m.deco.some((b) => b.mat === 'adglug' && b.pv === 'derrick'), 'the board is under the model');
    assert.ok(!m.boxes.some((b) => b.mat === 'deckplate' && b.pv === 'derrick'), 'the drill floor stays the game\'s');
  });
}
