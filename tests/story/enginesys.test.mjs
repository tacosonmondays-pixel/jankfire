// the engine's state reaches the save through the sim (shared/story/enginesys.js), and junk doesn't
import test from 'node:test';
import assert from 'node:assert/strict';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/enginesys.js';
import { cleanSave } from '../../shared/story/save.js';
import { makeStory } from '../../shared/story/story.js';
import { toSave } from '../../shared/story/state.js';
import * as lab from '../../shared/story/content/test/lab.js';

test('engine state -> sim -> snapshot -> cleanSave -> sim -> same state', () => {
  const out = [];
  const sim = createSim({ send: (m) => out.push(m) });
  sim.msg({ t: 'join', name: 'x' });
  const S = makeStory({ content: lab, host: { has: () => true } });
  S.run(['quest.start:lab_soup', 'flag:bribedGordo', 'standing:bottom-2', 'codex:lore.soup', 'log:lumps|soup']);
  sim.msg({ t: 'sty', k: 'engine', st: JSON.parse(JSON.stringify(toSave(S.st))), bag: ['soup_pot', 'bad id!'], coupons: 280 });
  sim.msg({ t: 'sty', k: 'save', why: 'test' });
  const saved = out.find((m) => m.k === 'saved').save;
  const { save } = cleanSave(saved, { slot: 0 });
  assert.ok(save, 'the cleaner keeps it');
  assert.deepEqual(save.data.bagStub, ['soup_pot']);
  assert.equal(save.coupons, 280);
  assert.equal(save.data.quests.lab_soup.step, 'pot');
  assert.ok(save.data.flags.includes('bribedGordo'));
  const sim2 = createSim({ send: () => {}, save });
  assert.equal(sim2.state.quests.lab_soup.step, 'pot');
  assert.equal(sim2.state.standing.bottom, -2);
  assert.ok(sim2.state.codex['lore.soup']);
  assert.equal(sim2.state.log.at(-1), 'lumps|soup');
});

test('junk engine messages are ignored or cleaned', () => {
  const sim = createSim({ send: () => {} });
  for (const st of [null, 5, 'x', [], { quests: { a: { step: 9e99 } }, flags: 'no' }]) sim.msg({ t: 'sty', k: 'engine', st, bag: 'nope', coupons: NaN });
  assert.equal(typeof sim.state.flags, 'object');
  assert.equal(sim.save.coupons, 0);
});
