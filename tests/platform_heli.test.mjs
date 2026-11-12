// Platform's helideck chopper is the Blender news chopper (p_heli), like Skyline's: look-only, the same outline
import test from 'node:test';
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';

test('both rig maps: the chopper on the helideck is p_heli, fitted like every other copy', () => {
  const ref = MAPS.skyline.boxes.props.find((q) => q.id === 'heli');
  for (const [id, dz] of [['platform', 0], ['platform_sd', -44]]) {
    const ps = MAPS[id].boxes.props.filter((q) => q.id === 'heli');
    assert.equal(ps.length, 1, id);
    const near = (a, b) => a.every((v, i) => Math.abs(v - b[i]) < 0.01);
    assert.ok(near(ps[0].a, [45.5, 10.83, 0.5 + dz]), 'on the H');
    assert.ok(near(ps[0].lo, ref.lo) && near(ps[0].hi, ref.hi), 'the same outline as Skyline\'s (the one fit every copy gets)');
    assert.ok(MAPS[id].boxes.filter((b) => b.pv === 'heli').length >= 6, 'its solid boxes are tagged');
  }
});
