// node --test tests/story/oldsaves.test.mjs : a save from an older build still plays on. the content keeps moving
// (p5b moved from m05 to m06, steps got split and renamed), and a save can hold a running quest on a step that's gone,
// or a quest the content dropped. before: the first froze that chapter (no objective, nothing after it ever started),
// the second made every tick throw (the whole story dead). now: the dropped quest is ignored and the stuck one starts
// over from its first step (quests.js repair(), boot.js runs it when a save loads).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { fromSave, toSave } from '../../shared/story/state.js';
import { makeStory } from '../../shared/story/story.js';
import * as overdue from '../../shared/story/content/overdue.js';

const load = (data) => {
  const ev = [];
  const S = makeStory({ content: overdue, state: fromSave(data), host: { has: () => false, act: () => {}, event: (e) => ev.push(e) } });
  return { S, ev, boot: () => { S.quests.repair(); for (const id of overdue.autostart) S.quests.start(id); } }; // (what boot.js autostart() does)
};
const done = (...ids) => Object.fromEntries(ids.map((id) => [id, { step: '', n: [], t: 0, done: true }]));
const A1 = ['m01_return_to_sender', 'm02_sauce_run', 'm03_somethings_digesting', 'm04_clocking_in'];

test('a chapter parked on a step that moved away starts over and the act carries on', () => {
  const { S, ev, boot } = load({ flags: ['init_done'], quests: { ...done(...A1), m05_second_stomach: { step: 'p5b', n: [0], t: 12 } } });
  assert.deepEqual(S.quests.objectives().map((o) => o.quest), [], 'before: stuck with no objective (the bug)');
  boot();
  const o = S.quests.objectives().find((x) => x.kind === 'main');
  assert.equal(o && o.quest + '.' + o.step, 'm05_second_stomach.clinic');
  assert.ok(ev.some((e) => e.type === 'warn' && /m05_second_stomach/.test(e.text)));
  S.quests.finish('m05_second_stomach'); S.quests.start('m06_tickets_please');
  assert.equal(S.quests.objectives().find((x) => x.kind === 'main').quest, 'm06_tickets_please', 'the train chapter comes next');
});

test('a quest the content dropped is ignored instead of breaking every tick', () => {
  const { S, boot } = load({ flags: ['init_done'], quests: { ...done('m01_return_to_sender'), old_gone_quest: { step: 'x', n: [], t: 0 } }, track: 'old_gone_quest' });
  boot();
  assert.doesNotThrow(() => { S.tick(0.5); S.quests.objectives(); S.emitQuest({ type: 'reach', zone: 'bottom:lostfound' }); });
  assert.equal(S.quests.objectives().find((x) => x.kind === 'main').quest, 'm02_sauce_run');
  assert.ok(toSave(S.st).quests.old_gone_quest, 'kept in the save (a newer build might know it), just not run');
});

test("a healthy save is left alone", () => {
  const { S, ev, boot } = load({ flags: ['init_done'], quests: { ...done('m01_return_to_sender'), m02_sauce_run: { step: 'drive', n: [0], t: 3 } } });
  boot();
  assert.equal(S.st.quests.m02_sauce_run.step, 'drive');
  assert.equal(S.st.quests.m02_sauce_run.t, 3);
  assert.ok(!ev.some((e) => e.type === 'warn'));
});
