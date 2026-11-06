// node --test tests/story: the OVERDUE quest state machine, conditions, actions, dialogue and save round trips
import test from 'node:test';
import assert from 'node:assert/strict';
import { compile, test as cond } from '../../shared/story/cond.js';
import { newState, toSave, fromSave } from '../../shared/story/state.js';
import { makeStory } from '../../shared/story/story.js';
import * as lab from '../../shared/story/content/test/lab.js';

function mk(st) {
  const ev = [], acts = [], bag = new Set();
  const host = { has: (i) => bag.has(i), act: (a) => { acts.push(a); if (a.do === 'give') bag.add(a.arg || a.item); if (a.do === 'take') bag.delete(a.arg); }, event: (e) => ev.push(e) };
  const S = makeStory({ content: lab, state: st, host });
  return { S, ev, acts, bag, types: () => ev.map((e) => e.type) };
}
const talkThrough = (S, npc, picks = []) => { const T = S.talk(npc); let k = 0; for (let g = 0; g < 50 && !T.end; g++) { if (T.opts && T.i === T.lines.length - 1) { if (k >= picks.length) break; T.choose(picks[k++]); } else T.next(); } return T; };

test('conditions', () => {
  const st = newState();
  st.flags.a = true; st.vars.n = 3; st.standing.bottom = 5;
  st.quests.q = { step: 'drive', n: [1], t: 0 };
  assert.equal(cond('a && !b', st), true);
  assert.equal(cond('flag.a || flag.b', st), true);
  assert.equal(cond('var.n >= 3 && standing.bottom > 4', st), true);
  assert.equal(cond("q.q.step == 'drive'", st), true);
  assert.equal(cond('q.q.at.drive && q.q.active && !q.q.done', st), true);
  assert.equal(cond('!(a || b)', st), false);
  assert.equal(cond('has.pot', st, { has: (i) => i === 'pot' }), true);
  assert.equal(cond('', st), true);
  assert.throws(() => compile('a &&'));
  assert.throws(() => compile('a ; b'));
  assert.equal(compile('a && b'), compile('a && b')); // cached
});

test('3-step quest: fight branch, kills, delivery, reward, ending', () => {
  const { S, bag, types, acts, ev } = mk();
  talkThrough(S, 'lumps', [1, 0]); // "need anything?" -> soup -> starts the quest
  assert.ok(S.quests.isActive('lab_soup'));
  assert.equal(S.st.quests.lab_soup.step, 'pot');
  assert.equal(S.st.track, 'lab_soup');
  assert.ok(S.st.codex['lore.soup'] && S.st.met.lumps && S.st.codex['char.lumps']);
  S.emit({ type: 'pickup', item: 'banana' }); // wrong item: nothing
  assert.equal(S.st.quests.lab_soup.step, 'pot');
  bag.add('soup_pot'); S.emit({ type: 'pickup', item: 'soup_pot' });
  assert.equal(S.st.quests.lab_soup.step, 'interns');
  S.emit({ type: 'kill', kind: 'dummy' });
  assert.deepEqual(S.quests.objectives()[0].goals.map((g) => g.n), [1, 0]);
  S.emit({ type: 'kill', kind: 'dummy' });
  assert.equal(S.st.quests.lab_soup.step, 'deliver');
  assert.ok(S.quests.objectives()[0].timer <= 120);
  assert.equal(S.quests.objectives()[0].marker, 'auntie');
  talkThrough(S, 'auntie');
  assert.ok(S.st.quests.lab_soup.done);
  assert.equal(S.st.quests.lab_soup.end, 'fought');
  assert.ok(S.st.flags.soupHero && S.st.flags.lab_done && !S.st.flags.soupDeal);
  assert.equal(S.st.standing.bottom, 5);
  assert.ok(acts.some((a) => a.do === 'coupons' && a.arg === '300'));
  assert.ok(acts.some((a) => a.do === 'take' && a.arg === 'soup_pot'));
  assert.ok(!bag.has('soup_pot'));
  assert.deepEqual(types().filter((t) => /^quest/.test(t)), ['questStart', 'questDone']);
  assert.equal(ev.find((e) => e.type === 'questDone').grade, 'EXCEEDS EXPECTATIONS');
  assert.equal(S.st.track, '');
  assert.equal(S.talk('lumps').node, 'after'); // the conversation knows
});

test('branching conversation: the bribe changes flags, standing, the quest route and later lines', () => {
  const { S, bag } = mk();
  talkThrough(S, 'lumps', [1, 0]);
  bag.add('soup_pot'); S.emit({ type: 'pickup', item: 'soup_pot' });
  const T = talkThrough(S, 'gordo', [0, 0]); // lumps sent me -> pay him
  assert.deepEqual(T.history, [['start', 0], ['sent', 0]]);
  assert.ok(S.st.flags.bribedGordo && !S.st.flags.braveSoup);
  assert.equal(S.st.standing.bottom, -2);
  assert.ok(S.st.codex['frag.option_c_1']);
  assert.equal(S.st.quests.lab_soup.step, 'sneak'); // the flag goal's branch
  assert.equal(S.talk('gordo').node, 'paid');
  talkThrough(S, 'auntie');
  assert.equal(S.st.quests.lab_soup.end, 'bribed');
  assert.ok(S.st.flags.soupDeal);
  assert.equal(S.st.standing.bottom, 3);
});

test('the other answer goes the other way', () => {
  const { S } = mk();
  talkThrough(S, 'lumps', [1, 0]);
  S.st.quests.lab_soup.step = 'interns'; S.quests.enterStep('lab_soup', 'interns');
  talkThrough(S, 'gordo', [0, 1]); // fight them myself
  assert.ok(S.st.flags.braveSoup && !S.st.flags.bribedGordo);
  assert.equal(S.st.standing.bottom, 2);
  assert.equal(S.st.quests.lab_soup.step, 'interns');
  assert.equal(S.talk('gordo').node, 'brave2');
});

test('conditional answers hide, once-answers and again-lines', () => {
  const { S } = mk();
  const T = S.talk('gordo');
  assert.equal(T.opts.length, 2); // the soup answer needs the quest
  assert.ok(!T.opts.some((o) => /soup/.test(o.t)));
  const a = talkThrough(S, 'clerk');
  assert.equal(a.lines.length, 2);
  assert.equal(S.talk('clerk').lines.length, 1); // again
});

test('timer runs out: the step fails and retries from its checkpoint; a fail flag does too', () => {
  const { S, bag, types } = mk();
  talkThrough(S, 'lumps', [1, 0]);
  bag.add('soup_pot'); S.emit({ type: 'pickup', item: 'soup_pot' });
  S.emit({ type: 'kill', kind: 'dummy', n: 2 });
  assert.equal(S.st.quests.lab_soup.step, 'deliver');
  for (let i = 0; i < 125; i++) S.tick(1);
  assert.ok(types().includes('stepFail') && types().includes('stepRetry'));
  assert.equal(S.st.quests.lab_soup.step, 'deliver');
  assert.ok(S.st.quests.lab_soup.t < 10);
  S.run(['flag:soupSpilled']);
  assert.equal(types().filter((t) => t === 'stepFail').length, 2);
  S.run(['unflag:soupSpilled']);
  talkThrough(S, 'auntie');
  assert.ok(S.st.quests.lab_soup.done);
});

test('actions: vars, standing caps, branches, quest jumps, unknown verbs go to the host', () => {
  const { S, acts } = mk();
  S.run(['var:x=2', 'var:x+3', 'var:x-1', 'standing:corp+500', { if: 'var.x == 4', do: ['flag:four'], else: ['flag:notfour'] }, 'scene:lab_panels', 'toast:hi']);
  assert.equal(S.st.vars.x, 4);
  assert.equal(S.st.standing.corp, 100);
  assert.ok(S.st.flags.four && !S.st.flags.notfour);
  assert.deepEqual(acts.map((a) => a.do), ['scene', 'toast']);
  S.run(['quest.start:lab_soup/deliver']);
  assert.equal(S.st.quests.lab_soup.step, 'deliver');
  S.run(['quest.done:lab_soup/bribed']);
  assert.equal(S.st.quests.lab_soup.end, 'bribed');
  assert.equal(S.quests.start('lab_soup'), false); // done quests don't restart
});

test('save -> load -> resume mid-quest', () => {
  const a = mk();
  talkThrough(a.S, 'lumps', [1, 0]);
  a.bag.add('soup_pot'); a.S.emit({ type: 'pickup', item: 'soup_pot' });
  a.S.emit({ type: 'kill', kind: 'dummy' });
  a.S.tick(3.5);
  const data = JSON.parse(JSON.stringify(toSave(a.S.st)));
  assert.ok(Array.isArray(data.flags) && data.flags.includes('said.lumps.soup'));
  const b = mk(fromSave(data));
  b.bag.add('soup_pot');
  assert.equal(b.S.st.quests.lab_soup.step, 'interns');
  assert.deepEqual(b.S.st.quests.lab_soup.n, [1, 0]);
  assert.equal(b.S.st.quests.lab_soup.t, 3.5);
  b.S.emit({ type: 'kill', kind: 'dummy' });
  assert.equal(b.S.st.quests.lab_soup.step, 'deliver');
  talkThrough(b.S, 'auntie');
  assert.ok(b.S.st.quests.lab_soup.done);
  assert.equal(b.S.talk('lumps').node, 'after');
});

test('fromSave survives junk', () => {
  for (const junk of [null, 5, 'x', [], { flags: 'no' }, { quests: { a: 5, 'bad id!': {}, b: { step: 3, n: [NaN, 1e9, 'x'], t: Infinity, done: 'yes' } } }, { flags: Array(5000).fill('f'), vars: { a: '9', b: NaN, __proto__: 1 } }, { standing: { corp: 1e9 }, log: [1, 'ok'] }]) {
    const st = fromSave(junk);
    assert.equal(typeof st.flags, 'object');
  }
  const st = fromSave({ quests: { b: { step: 3, n: [NaN, 1e9, 'x'], t: Infinity, done: 'yes' } }, standing: { corp: 1e9 }, log: [1, 'ok'] });
  assert.deepEqual(st.quests.b, { step: '', n: [0, 1e4, 0], t: 0 });
  assert.equal(st.standing.corp, 100);
  assert.deepEqual(st.log, ['ok']);
});

test('content sanity: every quest step / branch / npc node reference exists', () => {
  for (const q of Object.values(lab.quests)) {
    const ids = new Set(q.steps.map((s) => s.id));
    for (const s of q.steps) for (const to of [s.next, s.failTo, ...(s.goals || []).map((g) => g.to)].flat().filter(Boolean)) {
      const t = typeof to === 'string' ? to : to.to;
      assert.ok(ids.has(t) || t.startsWith('end'), `${q.id}/${s.id} -> ${t}`);
    }
  }
  for (const n of Object.values(lab.npcs)) for (const [k, node] of Object.entries(n.lines)) {
    for (const o of node.opts || []) assert.ok(!o[1] || n.lines[o[1]], `${n.id}/${k} -> ${o[1]}`);
    for (const g of node.go || []) assert.ok(n.lines[g[1]], `${n.id}/${k} go ${g[1]}`);
  }
});
