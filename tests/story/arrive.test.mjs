// node --test tests/story/arrive.test.mjs : scenes happen where they're set (the world lane). A step that waits for its
// scene at a place (m04's c4 at the Sunset Wall) only plays it once you get there; a step that goes somewhere (m03's
// drive into the Gut) plays its scene on arrival; a step with no place, or right after a fight, plays at its start.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as overdue from '../../shared/story/content/overdue.js';
import { makeStory } from '../../shared/story/story.js';

function story() {
  const scenes = [];
  const host = { has: () => false, act: (a) => { if (a.do === 'scene') scenes.push(a.arg ?? a.item); }, event() {} };
  const S = makeStory({ content: overdue, host });
  S.run(overdue.init);
  return { S, scenes };
}
const done = (S, id) => { S.st.quests[id] = { ...(S.st.quests[id] || {}), done: true, step: null, n: [], t: 0 }; };

test('m04: c4 waits for the Sunset Wall', () => {
  const ids = overdue.quests.m04_clocking_in.steps.map((s) => s.id);
  assert.deepEqual(ids.slice(0, 2), ['sunset' + overdue.ARRIVE, 'sunset']);
  const { S, scenes } = story();
  for (const q of ['m01_return_to_sender', 'm02_sauce_run', 'm03_somethings_digesting']) done(S, q);
  S.quests.start('m04_clocking_in');
  assert.ok(!scenes.includes('c4_clocking_in'), 'c4 played before you got there');
  assert.equal(S.quests.objectives().find((o) => o.quest === 'm04_clocking_in').marker, 'bottom:sunset_spot');
  S.emit({ type: 'reach', zone: 'gut:border' }); // (somewhere else: nothing)
  assert.ok(!scenes.includes('c4_clocking_in'));
  S.emit({ type: 'reach', zone: 'bottom:sunset_spot' });
  assert.ok(scenes.includes('c4_clocking_in'), 'c4 plays at the Sunset Wall');
});

test('m03: c3 plays on reaching Peristalsis Avenue, not before', () => {
  const { S, scenes } = story();
  for (const q of ['m01_return_to_sender', 'm02_sauce_run']) done(S, q);
  S.quests.start('m03_somethings_digesting');
  assert.ok(!scenes.includes('c3_its_breathing'), 'c3 played at the start of the drive');
  S.emit({ type: 'reach', zone: 'gut:peristalsis' });
  assert.ok(scenes.includes('c3_its_breathing'), 'c3 plays on arrival');
});

test('no place, or right after a fight: the scene plays at the step start', () => {
  const m06 = overdue.quests.m06_tickets_please.steps;
  assert.ok(!m06.some((s) => s.id === 'terminus' + overdue.ARRIVE), "m06's terminus follows the train fight: no arrive step");
  assert.ok(m06.find((s) => s.id === 'terminus').do.includes('scene:c6b_terminus'));
  assert.ok(overdue.quests.m01_return_to_sender.steps.find((s) => s.id === 'c1').do.includes('scene:c1_please_take_your_item'));
});

test('m02: the soup is delivered at the trade post, not the moment you hold it; the trade post talks to you there', () => {
  const talks = [];
  const S2 = makeStory({ content: overdue, host: { has: (i) => i === 'soup_pot', act: (a) => { if (a.do === 'talk') talks.push(a.arg); }, event() {} } });
  S2.run(overdue.init); done(S2, 'm01_return_to_sender');
  S2.quests.start('m02_sauce_run'); S2.quests.enterStep('m02_sauce_run', 'deliver');
  S2.tick(1);
  assert.equal(S2.st.quests.m02_sauce_run.step, 'deliver', 'delivered from wherever you were');
  assert.ok(!talks.some((t) => t.includes('trade_post')), 'the trade post talk opened away from the trade post');
  S2.emit({ type: 'reach', zone: 'gut:border' });
  assert.ok(S2.st.quests.m02_sauce_run.done, 'delivered at the gate');
  assert.ok(talks.some((t) => t.includes('trade_post')));
});

test("talkAt 'arrive': Dumpling scores the landing on the roof, Auntie's talks wait for home", () => {
  for (const [q, st, talk] of [['m01_return_to_sender', 'swing', 'dumpling_score'], ['m04_clocking_in', 'home', 'aftermath'], ['m05_second_stomach', 'home', 'night']]) {
    const steps = overdue.quests[q].steps, i = steps.findIndex((s) => s.id === st), act = `${q}.${talk}.start`;
    assert.ok(!(steps[i].do || []).some((a) => typeof a === 'string' && a.includes(act)), `${q}/${st}: ${talk} opens at the step start`);
    const after = i + 1 < steps.length ? steps[i + 1].do || [] : overdue.quests[q].onDone;
    assert.ok(after.some((a) => typeof a === 'string' && a.includes(act)), `${q}/${st}: ${talk} doesn't open on arrival`);
  }
  // the car ride is a talk on the way: it stays at the start of the drive
  assert.ok(overdue.quests.m02_sauce_run.steps.find((s) => s.id === 'drive').do.some((a) => typeof a === 'string' && a.includes('car_ride')));
});
