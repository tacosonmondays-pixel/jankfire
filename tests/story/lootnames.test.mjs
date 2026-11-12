// node --test tests/story/lootnames.test.mjs : no raw ids on a loot card. LOST PROPERTY (the bins weapon in m01) was given
// by its content id, which isn't a weapon: the bag refused it, it lay on the floor for good and its card read
// "LOST_PROPERTY_WEAPON". now a story weapon id becomes its base gun with its name, and every story item a mission can
// hand you makes a real bag item whose card name is a name.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeItem, newInv, invAdd, itemAt, infoOf, kindOf, NAMED_WEAPONS } from '../../shared/story/items.js';
import { nameOf } from '../../shared/story/loot.js';
import { CONTENT } from '../../shared/story/content/index.js';
import { validate } from '../../shared/story/content/validate.js';
import { ORDER } from '../../shared/weapons.js';

const cardName = (it) => (kindOf(it.b) === 'gun' || kindOf(it.b) === 'melee' ? nameOf(it) : infoOf(it).name); // (what lootfx.js lootCard prints)

test('the bins weapon goes in the bag as a rare Plan B called LOST PROPERTY', () => {
  const inv = newInv(), u = invAdd(inv, { b: 'lost_property_weapon', q: 0 }); // (what qgive hands the sim)
  assert.ok(u, 'the bag took it');
  const it = itemAt(inv, u);
  assert.equal(it.b, 'pistol');
  assert.equal(it.r, 'rare');
  assert.equal(cardName(it), 'LOST PROPERTY');
});

test('every item a mission, a side quest or a loot table can hand you has a real name on its card', () => {
  const ids = new Set(Object.keys(CONTENT.ITEMS));
  for (const q of [...Object.values(CONTENT.MISSIONS), ...Object.values(CONTENT.SIDE)]) {
    for (const i of (q.reward && q.reward.items) || []) ids.add(i);
    for (const s of q.steps || []) for (const g of s.goals || (s.goal ? [s.goal] : [])) if (g.item) ids.add(g.item);
  }
  for (const t of Object.values(CONTENT.LOOT_TABLES)) for (const e of t.entries || []) if (e.item) ids.add(e.item);
  let n = 0;
  for (const id of ids) {
    if (!Object.hasOwn(CONTENT.ITEMS, id)) continue; // (implants and legendaries have their own cards)
    const it = makeItem(id);
    assert.ok(it, `${id}: the bag can't hold it`);
    const name = cardName(it);
    assert.ok(name && name !== id && !/_/.test(name), `${id}: its card says ${JSON.stringify(name)}`);
    n++;
  }
  assert.ok(n > 20 && Object.keys(NAMED_WEAPONS).length >= 2);
});

test('the content check refuses a story item without a name', () => {
  const C = { ...structuredClone(CONTENT), WEAPON_IDS: ORDER };
  assert.equal(validate(C).length, 0);
  C.ITEMS.nameless_thing = { kind: 'quest', desc: 'a thing.' };
  C.ITEMS.lost_property_weapon.base = 'no_such_gun';
  const errs = validate(C);
  assert.ok(errs.some((e) => /nameless_thing: missing name/.test(e)), errs.join('\n'));
  assert.ok(errs.some((e) => /lost_property_weapon: unknown base/.test(e)), errs.join('\n'));
});

test("a named story weapon's description is its own, not the base gun's", () => {
  const it = makeItem('lost_property_weapon');
  assert.match(infoOf(it).desc, /Someone lost this/);
  assert.doesNotMatch(infoOf(makeItem('pistol')).desc, /Someone lost this/);
});
