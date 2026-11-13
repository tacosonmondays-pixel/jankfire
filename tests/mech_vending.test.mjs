// VENDING MACHINE's sign wall, the pure part: vmWallCross (shared/mech.js) honours each half's clipped width (wl / wr:
// where a building stopped it), so a sign next to a building never blocks shots inside the room behind it.
// node --test tests/mech_vending.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { MECH, vmWallCross } from '../shared/mech.js';

const W = MECH.vending.wall;
// a wall at the origin facing -z (yaw 0): its face is the x axis, +x is its right (wr), -x its left (wl)
const shot = (x) => vmWallCross(WALL, [x, 1.5, -10], [x, 1.5, 10]);
let WALL = { p: [0, 0, 0], yaw: 0 };
test('a full-width sign stops shots across its whole width', () => {
  assert.ok(shot(W.w / 2 - 0.3));
  assert.ok(shot(-W.w / 2 + 0.3));
  assert.equal(shot(W.w / 2 + 0.3), null);
});
test('a sign clipped by a building on its right (wr 1.2) stops nothing past 1.2 m on that side', () => {
  WALL = { p: [0, 0, 0], yaw: 0, wl: W.w / 2, wr: 1.2 };
  assert.ok(shot(1.0));
  assert.equal(shot(1.5), null);
  assert.equal(shot(W.w / 2 - 0.3), null);
  assert.ok(shot(-W.w / 2 + 0.3)); // (the other half is whole)
});
test('turned round (yaw pi), right and left swap with it', () => {
  WALL = { p: [0, 0, 0], yaw: Math.PI, wl: 1.2, wr: W.w / 2 };
  assert.ok(shot(-3.0)); // (world -x is its right now: whole)
  assert.equal(shot(1.5), null); // its left (world +x) is clipped at 1.2
});
