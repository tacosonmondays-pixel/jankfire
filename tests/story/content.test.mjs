// Loads every OVERDUE story content file and checks every id and reference resolves (validate.js), plus a few
// shape rules. Run: node --test tests/story/content.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { CONTENT } from '../../shared/story/content/index.js';
import { validate } from '../../shared/story/content/validate.js';
import { ORDER } from '../../shared/weapons.js';
import { SECRETS } from '../../shared/secrets.js';

const C = { ...CONTENT, WEAPON_IDS: [...ORDER, 'rigpunch'] };

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
