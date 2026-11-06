// node tests/story/save.test.mjs : the story save cleaner (shared/story/save.js) and the sim's protocol (sim.js)
import assert from 'node:assert/strict';
import { cleanSave, newSave, jsonOk, saveCard, SAVE, FALLBACK } from '../../shared/story/save.js';
import { createSim } from '../../shared/story/sim.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };

t('fresh save cleans to itself', () => { const s = newSave(1); assert.deepEqual(cleanSave(s, { slot: 1 }).save, { ...s, slot: 1 }); });
t('a new game starts in the Bottom at its spawn (the city slice), the test lot on request', async () => {
  const { STORY_SLICE } = await import('../../shared/city/storyworld.js');
  const out = []; createSim({ send: (o) => out.push(o) }).msg({ t: 'join' });
  assert.equal(out[0].cfg.map, 'story_slice'); assert.deepEqual(out[0].pos, STORY_SLICE.spawn);
  const o2 = []; createSim({ send: (o) => o2.push(o), save: newSave(0, 'story_test') }).msg({ t: 'join' }); assert.equal(o2[0].cfg.map, 'story_test');
});
t('act can only go up by one', () => {
  assert.equal(cleanSave({ ...newSave(), act: 3 }).error, 'bad act');
  assert.ok(cleanSave({ ...newSave(), act: 3 }, { prev: { act: 2 } }).save);
  assert.equal(cleanSave({ ...newSave(), act: 9 }, { prev: { act: 8 } }).error, 'bad act');
  assert.equal(cleanSave({ ...newSave(), act: 1.5 }).error, 'bad act');
});
t('junk is rejected', () => {
  for (const bad of [null, 5, 'x', [], { act: 'one' }, { ...newSave(), playtime: NaN }, { ...newSave(), playtime: -1 }, { ...newSave(), coupons: 1e13 }])
    assert.ok(cleanSave(bad).error, JSON.stringify(bad));
  assert.equal(cleanSave(JSON.parse('{"act":1,"playtime":0,"coupons":0,"__proto__":{"x":1}}')).error, 'bad save');
  assert.equal(cleanSave({ ...newSave(), data: { _acct: 1 } }).error, 'bad save');
  let deep = {}; const root = deep; for (let i = 0; i < 20; i++) deep = deep.a = {};
  assert.equal(cleanSave({ ...newSave(), data: { x: root } }).error, 'bad save');
  assert.equal(cleanSave({ ...newSave(), data: { s: 'x'.repeat(3000) } }).error, 'bad save');
});
t('size caps (64 KB table, 24 KB fallback)', () => {
  const big = { ...newSave(), data: { flags: [], junk: Array.from({ length: 30 }, () => 'y'.repeat(1000)) } };
  assert.ok(cleanSave(big).save);
  assert.equal(cleanSave(big, { maxBytes: FALLBACK.maxBytes }).error, 'save too big');
});
t('parts are cleaned, bad keys dropped, position rounded', () => {
  const r = cleanSave({ ...newSave(), at: { map: 'story_test', p: [1.23456, 2, 3], yaw: 0.12345 }, data: { flags: ['a', 'a', 5, 'b'], 'Bad Key': 1, quests: [1] } }).save;
  assert.deepEqual(r.data.flags, ['a', 'b']); assert.deepEqual(r.data.quests, {}); assert.ok(!('Bad Key' in r.data));
  assert.deepEqual(r.at.p, [1.23, 2, 3]); assert.equal(r.at.yaw, 0.123);
  assert.equal(cleanSave({ ...newSave(), at: { p: [Infinity, 0, 0] } }).error, 'bad save');
  assert.deepEqual(cleanSave({ ...newSave(), at: { p: [1e9, 0, 0] } }).save.at.p, [0, 0.1, 6]);
});
t('card has no data', () => { const c = saveCard(newSave(2)); assert.equal(c.slot, 2); assert.ok(!('data' in c)); assert.equal(saveCard(null), null); });
t('jsonOk', () => { assert.ok(jsonOk({ a: [1, 'x', null, true] })); assert.ok(!jsonOk({ a: () => 1 })); assert.ok(!jsonOk({ a: new Date() })); });
t('sim: join -> welcome, ping, void respawn, save snapshot', () => {
  const out = []; const sim = createSim({ send: (o) => out.push(o), save: newSave(0, 'story_test') });
  sim.msg({ t: 'join', name: 'tester', item: 'popper' });
  const w = out.find((o) => o.t === 'welcome');
  assert.equal(w.mode, 'story'); assert.equal(w.cfg.map, 'story_test'); assert.equal(w.ic.i, 'popper');
  assert.ok(out.find((o) => o.t === 'sty' && o.k === 'hello'));
  sim.msg({ t: 'pi', c: 5 }); assert.deepEqual(out.at(-1), { t: 'po', c: 5 });
  sim.msg({ t: 's', q: 1, p: [3, 1, 4], v: [0, 0, 0], y: 1.5 });
  sim.tick(2);
  sim.msg({ t: 'sty', k: 'save' });
  const sv = out.at(-1).save; assert.deepEqual(sv.at.p, [3, 1, 4]); assert.equal(sv.at.yaw, 1.5); assert.equal(sv.playtime, 2);
  assert.ok(cleanSave(sv).save, 'a snapshot passes the server cleaner');
  sim.msg({ t: 's', q: 1, p: [0, -50, 0], v: [0, 0, 0] });
  assert.equal(out.at(-2).t, 'spawn'); assert.equal(out.at(-2).q, 2);
  sim.msg({ t: 's', q: 1, p: [9, 9, 9], v: [0, 0, 0] }); // old seq: ignored
  sim.msg({ t: 'sty', k: 'save' }); assert.notDeepEqual(out.at(-1).save.at.p, [9, 9, 9]);
  for (const junk of [null, 1, { t: 5 }, { t: 's', q: 2, p: [NaN, 0, 0] }, { t: 's', q: 2, p: 'x' }]) sim.msg(junk);
});
t('sim: resumes where the save was', () => {
  const out = []; const s = newSave(0, 'story_test'); delete s.at.fresh; s.at.p = [5, 0.1, 5]; s.at.yaw = 2;
  createSim({ send: (o) => out.push(o), save: s }).msg({ t: 'join' });
  assert.deepEqual(out[0].pos, [5, 0.1, 5]); assert.equal(out[1].yaw, 2); assert.equal(out[0].name, 'CHANGE');
});
t('sim: story engine state round-trips through the save', () => {
  const s = newSave(0); s.data.flags = ['metChoir']; s.data.met = ['lumps']; s.data.quests = { sauce: { step: 'car', n: [1], t: 3 } }; s.data.track = 'sauce';
  const out = []; const sim = createSim({ send: (o) => out.push(o), save: cleanSave(s).save });
  assert.equal(sim.state.flags.metChoir, true); assert.equal(sim.state.quests.sauce.step, 'car');
  sim.state.flags.newOne = true; sim.state.codex['char.lumps'] = true;
  sim.msg({ t: 'join' }); sim.msg({ t: 'sty', k: 'save' });
  const d = cleanSave(out.at(-1).save).save.data;
  assert.deepEqual(d.flags.sort(), ['metChoir', 'newOne']); assert.deepEqual(d.met, ['lumps']); assert.deepEqual(d.codex, ['char.lumps']); assert.equal(d.track, 'sauce'); assert.equal(d.quests.sauce.n[0], 1);
});
console.log(`\n${n} passed (SAVE.v ${SAVE.v})`);
