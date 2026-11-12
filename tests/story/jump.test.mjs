// node --test tests/story/jump.test.mjs : the chapter select's jumps (shared/story/jump.js). each one plays a fresh save
// through the real engine up to its fight, so: the save is one the server's cleaner takes, the mission is on the right
// step with everything before it done (their flags, items, coupons, HYPE), you stand where the fight is, the train
// jump isn't sent home by the stranding check (#313), and the scratch slot is never one of the 3 real ones
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { jump, JUMPS, JUMP_SLOT } from '../../shared/story/jump.js';
import { cleanSave, SAVE } from '../../shared/story/save.js';
import { fromSave } from '../../shared/story/state.js';
import { makeStory } from '../../shared/story/story.js';
import { TRAIN, stranded } from '../../shared/story/train.js';
import { DEFAULT_WORLD } from '../../shared/story/worlds.js';
import * as overdue from '../../shared/story/content/overdue.js';

const LO = { primary: 'ar', secondary: 'pistol', melee: 'knife', item: 'frag' };
const bagOf = (s) => (s.data.inv.bag || []).filter(Boolean).map((x) => x.b);
// Continue on that save: the engine as boot.js builds it, and the main objective it shows
const resume = (s) => { const S = makeStory({ content: { ...overdue, init: [], autostart: [] }, state: fromSave(s.data) }); return S.quests.objectives().find((o) => o.kind === 'main'); };

test('the scratch slot is not a real slot', () => { assert.ok(JUMP_SLOT >= SAVE.slots); });

for (const id of Object.keys(JUMPS)) {
  test(`${id}: a clean save, the quest on its step, everything before it done`, () => {
    const J = JUMPS[id], { save, log } = jump(id, { loadout: LO });
    const c = cleanSave(save, { slot: save.slot });
    assert.ok(c.save, `the cleaner takes it (${c.error})`);
    assert.equal(c.save.slot, JUMP_SLOT);
    const o = resume(c.save);
    assert.equal(o && o.quest, J.quest); assert.equal(o.step, J.step);
    const order = Object.keys(overdue.quests).filter((q) => /^m0\d_/.test(q));
    for (const q of order.slice(0, order.indexOf(J.quest))) assert.equal(c.save.data.quests[q] && c.save.data.quests[q].done, true, `${q} done`);
    assert.ok(log.some((l) => / talk/.test(l)), 'talks were talked through');
    const flags = new Set(c.save.data.flags);
    for (const f of ['init_done', 'named_change', 'seen_c4', 'fate.mina.gut']) assert.ok(flags.has(f), f);
    for (const w of ['ar', 'pistol', 'knife']) assert.ok(bagOf(c.save).includes(w), `your loadout: ${w}`);
    assert.ok(c.save.coupons >= 300 && c.save.coupons <= 5000, `coupons ${c.save.coupons}`);
    assert.ok(c.save.data.hype > 0 && c.save.data.hype <= 100, `hype ${c.save.data.hype}`);
    assert.equal(c.save.chapter, J.quest);
  });
}

test('overtime: at the foot of the Gut Border Gate, his fight next', () => {
  const { save } = jump('overtime', { loadout: LO });
  assert.equal(save.at.map, DEFAULT_WORLD);
  assert.deepEqual(save.at.p, [-44, 36, -2]);
  assert.ok(!save.data.quests.m04_clocking_in.done);
  assert.ok(!save.data.flags.includes('beat_overtime_1'), 'not beaten yet');
});

test('train: on the train for the ride in, the way back is the service tunnel, nobody sends you home', () => {
  const { save } = jump('train', { loadout: LO });
  assert.equal(save.at.map, TRAIN.id);
  assert.equal(save.data.travelFrom.map, DEFAULT_WORLD);
  const q = save.data.quests.m06_tickets_please;
  assert.equal(stranded(q, q.step), false, 'the #313 stranding check keeps you aboard');
  assert.ok(!save.data.seen.includes('c6_mind_the_gap'), 'the ride in is still to play (on the train)');
  for (const f of ['beat_overtime_1', 'heart_ripped', 'seen_c5', 'implants_unlocked']) assert.ok(save.data.flags.includes(f), f);
  assert.equal(save.data.body.slots.heart && save.data.body.slots.heart.b, 'core_cracked_punch_clock', 'the punch-clock is in');
});
