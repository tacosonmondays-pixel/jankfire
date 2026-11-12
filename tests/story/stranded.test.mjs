// node --test tests/story/stranded.test.mjs : nobody gets stuck on the train. a slot started on the old train demo link
// (?story=1&storytest=1&train=1) was saved ON the train with Act I's first step still to do; Continue put you back
// there with "win the match" and no way off. trainfight.js now takes anyone home who's on the train outside m06's train
// part (shared/story/train.js stranded()), and travelHome lands that save in the city at the start.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { TRAIN, ONBOARD, stranded } from '../../shared/story/train.js';
import { travelTo, travelHome, DEFAULT_WORLD, WORLDS } from '../../shared/story/worlds.js';
import { newSave, cleanSave } from '../../shared/story/save.js';
import { quests } from '../../shared/story/content/overdue.js';

// what the old demo link left in the slot (trimmed from a real one: new game on the train, m01 at its first step)
const demo = () => cleanSave({ v: 1, slot: 0, act: 1, chapter: 'return_to_sender', playtime: 25, coupons: 0, at: { map: 'story_train', p: [-1.6, 1, 7.71], yaw: 0 },
  data: { flags: ['init_done', 'turf.bottom.bottom'], quests: { m01_return_to_sender: { step: 'sim', goals: [] } }, seen: [] } }).save;

test('a demo save on the train is stranded, and going home puts it in the city at the start', () => {
  const s = demo();
  assert.equal(s.at.map, TRAIN.id);
  assert.equal(stranded(s.data.quests.m06_tickets_please, ''), true, "m06 never started: nothing to do on the train");
  const h = travelHome(s, null);
  assert.equal(h.at.map, DEFAULT_WORLD);
  assert.deepEqual(h.at.p, WORLDS[DEFAULT_WORLD].spawn);
  assert.equal(h.at.fresh, true);
  assert.deepEqual(h.data.quests, s.data.quests, 'the progress comes along');
  assert.ok(cleanSave(h, { slot: 0, prev: s }).save, 'and the server still takes it');
});

test('a real trip keeps you on the train for the whole fight and brings you back where you boarded', () => {
  for (const step of ONBOARD) assert.equal(stranded({ step }, step), false, step);
  assert.equal(stranded({ done: true }, ''), false, 'done: the tunnel mouth exit (its own path) takes you home');
  for (const step of ['plan', 'fitted', 'board']) assert.equal(stranded({ step }, step), true, step);
  const city = { ...newSave(0), at: { map: DEFAULT_WORLD, p: [-150, 2, 180], yaw: 1 } }, on = travelTo(city, TRAIN.id);
  assert.equal(on.at.map, TRAIN.id);
  assert.deepEqual(travelHome(on, null).at.p, [-150, 2, 180]);
});

test("every m06 step after boarding is one the train keeps you for (a new step there would strand you)", () => {
  const ids = quests.m06_tickets_please.steps.map((s) => s.id), after = ids.slice(ids.indexOf('board') + 1);
  assert.ok(after.length > 0);
  assert.deepEqual(after, ONBOARD);
});
