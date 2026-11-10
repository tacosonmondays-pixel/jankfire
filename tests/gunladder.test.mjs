// gun game's rotating ladder: right shape every roll, real weapons only, and it actually rotates
import test from 'node:test';
import assert from 'node:assert/strict';
import { LADDER, LADDER_POOL, LADDER_TAKE, rollLadder } from '../shared/modes.js';
import { WEAPONS } from '../shared/weapons.js';

test('every pool weapon exists, no weapon is in two pools', () => {
  const all = [...LADDER_POOL.guns, ...LADDER_POOL.silly, ...LADDER_POOL.melee];
  for (const id of all) assert.ok(Object.hasOwn(WEAPONS, id), id);
  assert.equal(new Set(all).size, all.length);
  assert.ok(!all.includes('knife'));
  for (const id of LADDER_POOL.melee) assert.equal(WEAPONS[id].kind, 'melee'); // the humiliation rungs
});
test('a roll is guns, then silly, then melee, then the spoon', () => {
  let prev = null;
  for (let i = 0; i < 300; i++) {
    const L = rollLadder(prev);
    assert.equal(L.length, LADDER.length);
    assert.equal(new Set(L).size, L.length);
    assert.equal(L.at(-1), 'knife');
    let at = 0;
    for (const k of ['guns', 'silly', 'melee']) { for (const id of L.slice(at, at + LADDER_TAKE[k])) assert.ok(LADDER_POOL[k].includes(id), `${id} in ${k}`); at += LADDER_TAKE[k]; }
    if (prev) {
      assert.notEqual(L.join(), prev.join());
      for (const k of ['guns', 'silly', 'melee']) { // weapons that sat out go first: only as many repeats as it takes to fill the course
        const rested = LADDER_POOL[k].filter((id) => !prev.includes(id)).length, repeats = LADDER_POOL[k].filter((id) => prev.includes(id) && L.includes(id)).length;
        assert.equal(repeats, Math.max(0, LADDER_TAKE[k] - rested), k);
      }
    }
    prev = L;
  }
});
