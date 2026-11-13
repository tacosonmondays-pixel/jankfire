// mech size (x1.35): the walking body vs doors, the drop's room check. node --test tests/mechscale.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { MECH, mechScale, mechBody, mechRoom, mechPlough, SCALE } from '../shared/mech.js';
import { MAPS } from '../shared/map.js';
import { movePlayer } from '../shared/physics.js';

const WB = MAPS.warehouse.boxes; // the warehouse: a 10 m roof over x -32..32; its east wall (x 31.7 - 32.3) has a door 5 m high at z -10..-3
// walk west along z from the yard into the east door for s seconds; where it ends up
function walk(body, z = -6.5, s = 3) {
  const p = [37, 0, z], v = [-8, 0, 0];
  for (let t = 0; t < s; t += 1 / 60) { v[0] = -8; v[1] -= 30 / 60; movePlayer(p, v, 1 / 60, WB, true, body); if (p[1] < 0) { p[1] = 0; v[1] = 0; } }
  return p;
}

test('walking: a 6.6 m mech stops at a 5 m door; a player (and the old 4.9 m mech) walks through', () => {
  const pp = walk(mechBody('paperplane')), ns = walk(mechBody('nightshift'));
  assert.ok(pp[0] > 32.3 && pp[0] < 33.6, `paper plane stops at the door frame: x ${pp[0].toFixed(2)}`);
  assert.ok(ns[0] > 32.3, `night shift too: x ${ns[0].toFixed(2)}`);
  assert.ok(walk(null)[0] < 20, 'a player walks in');
  mechScale(1);
  try { assert.ok(walk(mechBody('paperplane'))[0] < 20, 'size 1: the 4.9 m paper plane fits under it'); } finally { mechScale(SCALE.def); }
  // and it still walks the open yard, steps up a crate (step 1.35 m), not a wall-high box
  const p = [45, 0, 12], v = [0, 0, -8], curb = [{ min: [43, 0, 6], max: [47, 1.2, 7] }], crate = [{ min: [43, 0, 6], max: [47, 1.8, 7] }];
  for (let t = 0; t < 1.2; t += 1 / 60) { v[2] = -8; v[1] -= 0.5; movePlayer(p, v, 1 / 60, curb, true, mechBody('paperplane')); if (p[1] < 0) { p[1] = 0; v[1] = 0; } }
  assert.ok(p[2] < 6, `steps onto a 1.2 m crate (step ${MECH.body.step}): z ${p[2].toFixed(2)}`);
  const q = [45, 0, 12], w = [0, 0, -8];
  for (let t = 0; t < 1.2; t += 1 / 60) { w[2] = -8; w[1] -= 0.5; movePlayer(q, w, 1 / 60, crate, true, mechBody('paperplane')); if (q[1] < 0) { q[1] = 0; w[1] = 0; } }
  assert.ok(q[2] > 7, `a 1.8 m block stops it: z ${q[2].toFixed(2)}`);
});
test('the drop: no room under the roof, under the door lintel, against a wall; the open yard is fine', () => {
  for (const f of ['paperplane', 'nightshift']) {
    assert.equal(mechRoom([27, 0, -5], f, WB), false, f + ': inside the warehouse (between the rafters)');
    assert.equal(mechRoom([33, 0, -6.5], f, WB), false, f + ': in the doorway, under the wall over the door');
    assert.equal(mechRoom([33, 0, 5], f, WB), false, f + ': 0.7 m off the outside wall');
    assert.equal(mechRoom([45, 0, 12], f, WB), true, f + ': the open yard');
  }
  assert.equal(mechRoom([33.5, 0, 5], 'paperplane', WB), true, 'the paper plane fits 1.2 m off the wall');
  assert.equal(mechRoom([33.5, 0, 5], 'nightshift', WB), false, 'the wider knight does not');
  // an overhang: a slab 8 m up, off to the side of the marker (the middle ray misses it), still over the mech
  const over = [{ min: [-50, -1, -50], max: [50, 0, 50] }, { min: [0.7, 8, -3], max: [6, 8.4, 3] }];
  assert.equal(mechRoom([0, 0, 0], 'paperplane', over), false, 'an overhang over its shoulder');
  assert.equal(mechRoom([-3, 0, 0], 'paperplane', over), true, 'clear of it');
  // a waist-high crate by its feet is fine, one under its legs isn't
  const crate = (x) => [{ min: [-50, -1, -50], max: [50, 0, 50] }, { min: [x, 0, -0.5], max: [x + 1, 1.8, 0.5] }];
  assert.equal(mechRoom([0, 0, 0], 'nightshift', crate(1.3)), true, 'a crate by its feet');
  assert.equal(mechRoom([0, 0, 0], 'nightshift', crate(0.5)), false, 'a crate under its legs');
});
test('clutter: a mech ploughs through fronds, lamp arms, awnings and grids over its knees; roofs, walls and low stuff still stop it', () => {
  const B = (min, max, mat = 'metal') => ({ min, max, mat });
  assert.ok(mechPlough(B([0, 6, 0], [3, 6.2, 0.6], 'leaves')), 'a palm frond');
  assert.ok(mechPlough(B([0, 5.6, 0], [2, 5.9, 0.3])), 'a streetlight arm');
  assert.ok(mechPlough(B([0, 2.8, 0], [6, 3, 1.8], 'wood')), 'a shop awning');
  assert.ok(mechPlough(B([0, 3, 0], [8, 6, 0.2], 'grid')), 'a billboard grid');
  assert.ok(!mechPlough(B([0, 3.4, 0], [9, 3.7, 9], 'roofteal')), 'a roof');
  assert.ok(!mechPlough(B([0, 5, 0], [0.6, 10, 7], 'concrete')), 'the warehouse wall over its door');
  const b = mechBody('paperplane'), arm = B([0, 5.6, 0], [2, 5.9, 0.3]);
  assert.ok(b.skip(arm, 0) && !b.skip(arm, 4), 'only over its knees: an arm at its shins still stops it');
  // walking: a row of streetlight arms and an awning across the way don't stop it, the warehouse door still does
  const lot = [B([-50, -1, -50], [50, 0, 50]), B([-5, 5.6, 4], [5, 5.9, 4.3]), B([-5, 2.8, 0], [5, 3, 1.8], 'wood')];
  const p = [0, 0, 12], v = [0, 0, -8];
  for (let t = 0; t < 3; t += 1 / 60) { v[2] = -8; v[1] -= 0.5; movePlayer(p, v, 1 / 60, lot, true, b); if (p[1] < 0) { p[1] = 0; v[1] = 0; } }
  assert.ok(p[2] < -5, `ploughs through the lamp arms and the awning: z ${p[2].toFixed(2)}`);
  assert.ok(walk(b)[0] > 32.3, 'the warehouse door still stops it');
});
