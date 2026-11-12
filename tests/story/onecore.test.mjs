// node --test tests/story/onecore.test.mjs : there is ONE Punch-Clock core in the story (and one of Jack's marrow). you rip it out of Mr. Overtime
// in m04 and Bev puts it in at m05 (the implant:<id> action installs the one you carry). a playthrough of Act I through
// the real engine (shared/story/jump.js) ends with it in your heart and none spare in the bag
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { jump } from '../../shared/story/jump.js';
import { quests } from '../../shared/story/content/overdue.js';

const CORE = 'core_cracked_punch_clock', MARROW = 'marrow_pallet_jack';
const spare = (s, b) => (s.data.inv.bag || []).filter((x) => x && x.b === b).reduce((n, x) => n + (x.q || 1), 0);
const LO = { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' };

test('Act I start to end: the core is in, 0 spare', () => {
  const first = quests.m07_an_offer.steps[0].id;
  const { save } = jump({ quest: 'm07_an_offer', step: first }, { loadout: LO });
  for (const q of ['m04_clocking_in', 'm05_second_stomach', 'm06_tickets_please']) assert.equal(save.data.quests[q] && save.data.quests[q].done, true, q);
  assert.ok(save.data.flags.includes('act1_done'));
  assert.equal(save.data.body.slots.heart && save.data.body.slots.heart.b, CORE, 'in your heart');
  assert.equal(spare(save, CORE), 0, 'none spare in the bag');
  assert.equal(save.data.body.slots.spine && save.data.body.slots.spine.b, MARROW, "jack's marrow: in your spine (m06)");
  assert.equal(spare(save, MARROW), 0, 'no spare marrow either');
});

test('after the rip (m04) you carry exactly one, before m05 puts it in', () => {
  const { save } = jump({ quest: 'm05_second_stomach', step: 'clinic' }, { loadout: LO });
  assert.equal(spare(save, CORE), 1);
  assert.ok(!save.data.body.slots.heart);
});

test('nothing in the script hands the core over again', () => {
  const grants = JSON.stringify(quests).match(new RegExp(`(give|implant):${CORE}`, 'g')) || [];
  assert.deepEqual(grants.sort(), [`give:${CORE}`, `implant:${CORE}`], 'the rip gives it, the install puts it in');
  const mg = JSON.stringify(quests).match(new RegExp(`(give|implant):${MARROW}`, 'g')) || [];
  assert.deepEqual(mg, [`implant:${MARROW}`], 'the marrow: only the jack step');
});
