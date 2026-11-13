// TROLLEY: carried players (scooped / riding in the basket) are stopped before Battle Island's and Jank Royale's own
// message handlers, which act and return. a stub room with the real handle() and the real carry checks.
// node --test tests/mech_trolley.test.mjs
import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { Room } from '../server/room.js';

after(() => setImmediate(() => process.exit(process.exitCode || 0))); // (the room module keeps timers running)
function scene(k) {
  const R = Object.create(Room.prototype), seen = [];
  const p = { id: 2, alive: true, seq: 1, mheld: { by: 1, f: 'trolley', k, seq: 1 } };
  for (const k of ['isleOn', 'brOn']) Object.defineProperty(R, k, { value: true }); // (getters on the real room)
  Object.assign(R, { players: new Map([[2, p]]), isEcon: () => false,
    mechCarrier: () => ({ id: 1 }), // (still in the basket)
    isleHandle: (q, m) => { seen.push('isle:' + m.t); return true; }, brHandle: (q, m) => { seen.push('br:' + m.t); return true; } });
  return { R, p, seen };
}
const ISLE_BR = ['use', 'hero', 'deploy', 'brheal', 'brpick', 'brdrop', 'brswap', 'brkick', 'brjump'];

test('scooped: none of the island / royale actions get through (revive, hero swap, calling a mech, loot, heals)', () => {
  const { R, p, seen } = scene('scoop');
  for (const t of ISLE_BR) R.handle(p, { t });
  assert.deepEqual(seen, []);
});
test('riding: heals still work, the rest is stopped', () => {
  const { R, p, seen } = scene('ride');
  for (const t of ISLE_BR) R.handle(p, { t });
  assert.deepEqual(seen, ['isle:brheal']);
});
test('carried: snapshots still reach the modes (the carrier puts them in place after)', () => {
  const { R, p, seen } = scene('scoop');
  R.handle(p, { t: 's', q: 1 });
  assert.deepEqual(seen, ['isle:s']);
});
test('let go (no carrier any more): everything reaches the modes again', () => {
  const { R, p, seen } = scene('scoop');
  R.mechCarrier = () => null; R.mechUnhold = (t) => { t.mheld = null; };
  R.handle(p, { t: 'use' });
  assert.deepEqual(seen, ['isle:use']); assert.equal(p.mheld, null);
});
test('scooped or climbing into the seat: out of any shopping cart and off any revive first', () => {
  const R = Object.create(Room.prototype), gone = [], rv = [];
  const cart = { id: 9, rider: 2 }, t = { id: 2, alive: true, seq: 1, ride: 9, irv: { to: 5 } }, c = { id: 1, mech: { f: 'trolley' } };
  Object.assign(R, { carts: new Map([[9, cart]]), lassoDrop: () => {}, cartLetGo: (k, v) => { gone.push(k.id); t.ride = 0; }, isleRvStop: (p, why) => { rv.push(why); p.irv = null; } });
  R.mechHold(c, t, 'scoop');
  assert.deepEqual(gone, [9]); assert.equal(t.ride, 0); assert.deepEqual(rv, ['released']); assert.equal(t.mheld.by, 1);
});
