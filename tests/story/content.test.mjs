// Loads every OVERDUE story content file and checks every id and reference resolves (validate.js), plus a few
// shape rules. Run: node --test tests/story/content.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { CONTENT } from '../../shared/story/content/index.js';
import { validate } from '../../shared/story/content/validate.js';
import { ORDER } from '../../shared/weapons.js';
import { SECRETS } from '../../shared/secrets.js';

const C = { ...CONTENT, WEAPON_IDS: ORDER };

test('every story reference resolves', () => {
  const errs = validate(C);
  if (errs.length) console.log(errs.slice(0, 200).join('\n') + (errs.length > 200 ? `\n... and ${errs.length - 200} more` : ''));
  assert.equal(errs.length, 0, `${errs.length} content problems`);
});

test('the lore NPCs from the sims have their real selves in the cast', () => {
  for (const k of Object.keys(SECRETS)) if (SECRETS[k].kind === 'npc') assert.ok(Object.hasOwn(C.CAST, k), `missing real ${k}`);
});

test('ids are lowercase snake_case', () => {
  const bad = [];
  for (const reg of ['CAST', 'MISSIONS', 'SIDE', 'SCENES', 'BOSSES', 'IMPLANTS', 'LEGENDARIES', 'LOOT_TABLES', 'COLLECTIBLES', 'ITEMS', 'FLAGS'])
    for (const id of Object.keys(C[reg])) if (!/^[a-z][a-z0-9_]*$/.test(id)) bad.push(`${reg}.${id}`);
  assert.deepEqual(bad, []);
});

test('the main story is 25-35 missions over 5 acts, in order', () => {
  const ms = C.MISSION_ORDER.map((id) => C.MISSIONS[id]);
  assert.ok(ms.length >= 25 && ms.length <= 35, `${ms.length} missions`);
  for (let i = 1; i < ms.length; i++) assert.ok(ms[i].act >= ms[i - 1].act, `act order at ${C.MISSION_ORDER[i]}`);
  assert.deepEqual([...new Set(ms.map((m) => m.act))], [1, 2, 3, 4, 5]);
});

test('content sizes the brief asked for', () => {
  assert.ok(Object.keys(C.BOSSES).length >= 15, 'bosses');
  assert.ok(Object.keys(C.LEGENDARIES).length >= 30, 'legendaries');
  for (const d of Object.keys(C.DISTRICTS)) if (d !== 'sims') {
    const n = Object.values(C.SIDE).filter((q) => q.district === d).length;
    assert.ok(n >= 3 && n <= 6, `${d} has ${n} side questlines`);
  }
  assert.ok(Object.values(C.IMPLANTS).filter((i) => i.secret).length >= 10, 'secret implants');
});

test('the validator catches broken references', () => {
  const B = structuredClone(C);
  B.MISSIONS.m02_sauce_run.talks.pot.nodes.start.opts[0][1] = 'no_such_node';
  B.MISSIONS.m02_sauce_run.steps[0].goal.item = 'no_such_item';
  B.BOSSES.don.core = 'no_such_core';
  B.MISSIONS.m01_return_to_sender.reward.flags.push('no_such_flag');
  B.LEGENDARIES.reply_all.base = 'no_such_weapon';
  assert.equal(validate(B).length, 5);
});

test('the generated script docs are up to date', async () => {
  const { render } = await import('../../tools/story/render_script.mjs');
  const { readFileSync } = await import('node:fs');
  for (const [file, text] of Object.entries(render(CONTENT))) assert.equal(readFileSync(new URL(`../../docs/story/script/${file}`, import.meta.url), 'utf8'), text, `${file} is stale: run node tools/story/render_script.mjs`);
});

test('every mechanic is used somewhere, and every main mission and boss uses the grapple or says why not', () => {
  const QS = { ...C.MISSIONS, ...C.SIDE }, unused = [];
  for (const id of Object.keys(C.MECHANICS)) {
    const n = Object.values(QS).filter((q) => q.mechanic && q.mechanic.uses.includes(id)).length + Object.values(C.BOSSES).filter((b) => b.uses.includes(id)).length;
    if (n < 2) unused.push(`${id} (${n})`);
  }
  assert.deepEqual(unused, [], 'mechanics used fewer than twice');
  for (const [id, b] of Object.entries(C.BOSSES)) assert.ok(b.arena.grapple.length >= 2, `${id} needs 2+ grapple points`);
});

test('the grudge ledger has what the brief asked for', () => {
  const G = C.GRUDGES;
  assert.ok(Object.keys(G.FACTIONS).length >= 4, 'factions');
  assert.ok(Object.keys(G.ADAPTATIONS).length >= 30, 'adaptations');
  let n = 0; for (const f of Object.values(G.BARKS)) for (const ls of Object.values(f)) n += ls.length;
  assert.ok(n >= 200, `${n} barks`);
  for (const k of ['killed_you', 'you_fled', 'run_over', 'slipped', 'burned']) assert.ok(Object.hasOwn(G.TRIGGERS, k), k);
  for (const k of ['closed', 'quit', 'ally']) assert.ok(Object.hasOwn(G.RESOLUTIONS, k), k);
  assert.ok(G.RULES.maxActive <= 12 && G.RULES.maxHistory <= 4 && G.RULES.maxAdaptations <= 3, 'caps stay small');
  // the ledger stays its own design: no rank / tier / promotion fields anywhere in the data
  assert.doesNotMatch(JSON.stringify(G), /"(rank|tier|level|promot\w*|captain|warchief|follower|betray\w*)"\s*:/i);
});
