// node tests/story/chapters.test.mjs : the save slot cards' "ACT n · mission" line (shared/story/chapters.js): every
// main mission has a label, and a save reads as the mission its quests say it's on (not always "return to sender")
import assert from 'node:assert/strict';
import { MISSIONS } from '../../shared/story/content/index.js';
import { CHAPTER_LIST, CHAPTER, chapterOf } from '../../shared/story/chapters.js';
import { saveCard, newSave, cleanSave, CHAPTERS } from '../../shared/story/save.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };
const sv = (quests, extra = {}) => ({ ...newSave(0), ...extra, data: { flags: [], seen: [], quests } });
const card = (quests, extra) => { const c = saveCard(sv(quests, extra)); return `ACT ${c.act} · ${c.title}`; };

t('every mission id has a label, an act and a place in the order', () => {
  const ids = Object.keys(MISSIONS);
  assert.ok(ids.length >= 30, 'all five acts: ' + ids.length);
  for (const id of ids) {
    assert.ok(Object.hasOwn(CHAPTER, id), 'no chapter for ' + id);
    const c = CHAPTER[id];
    assert.ok(typeof c.label === 'string' && c.label.length > 0 && c.label === c.label.toLowerCase(), `${id} label: ${c.label}`);
    assert.equal(c.act, MISSIONS[id].act, id + ' act');
    assert.ok(CHAPTERS.includes(id), id + ' in CHAPTERS');
  }
  assert.equal(CHAPTER_LIST.length, ids.length);
  for (let i = 1; i < CHAPTER_LIST.length; i++) { const a = CHAPTER_LIST[i - 1], b = CHAPTER_LIST[i]; assert.ok(a.act < b.act || (a.act === b.act && a.n <= b.n), `order: ${a.id} before ${b.id}`); }
  assert.equal(CHAPTER.m06_tickets_please.label, 'tickets please');
  assert.ok(CHAPTER.m06_tickets_please.i < CHAPTER.m06_option_c.i, "act I's m06 before act II's");
});
t('a new game reads as the first mission', () => {
  assert.equal(card({}), 'ACT 1 · please take your item');
  assert.equal(CHAPTERS[0], 'm01_return_to_sender');
  assert.equal(cleanSave(newSave(1), { slot: 1 }).save.chapter, 'm01_return_to_sender');
});
t('the card follows the quests: the furthest mission in progress, else the last one done', () => {
  const done = { step: '', n: [], t: 0, done: true }, on = (s) => ({ step: s, n: [], t: 0 });
  assert.equal(card({ m01_return_to_sender: done, m02_sauce_run: on('drive') }), 'ACT 1 · sauce run');
  assert.equal(card({ m01_return_to_sender: done, m02_sauce_run: done, m03_somethings_digesting: done, m04_clocking_in: done, m05_second_stomach: done, m06_tickets_please: on('board') }), 'ACT 1 · tickets please');
  assert.equal(card({ m05_second_stomach: done, m06_tickets_please: done }), 'ACT 1 · tickets please', 'end of act I');
  assert.equal(card({ m06_tickets_please: done, m06_option_c: on('a'), m07_an_offer: on('b') }), 'ACT 2 · an offer');
  assert.equal(card({ m09_workday_1600: on('x') }), 'ACT 2 · the last workday: 16:00');
  assert.equal(card({ m31_fully_billable: done, m32_fully_vested: on('x') }), 'ACT 5 · fully vested');
  assert.equal(card({ m03_somethings_digesting: done, side_cat_lady: on('x') }), "ACT 1 · something's digesting", 'side quests never count');
});
t('junk quest data never throws and reads as a new game; an old save with no quests keeps its chapter', () => {
  for (const d of [null, 5, 'x', [], { quests: null }, { quests: [] }, { quests: { m02_sauce_run: null, __proto__: { m05_second_stomach: { done: true } } } }]) assert.equal(chapterOf(d).id, 'm01_return_to_sender', JSON.stringify(d));
  assert.equal(chapterOf({}, 'return_to_sender').id, 'm01_return_to_sender', 'the legacy chapter name');
  assert.equal(chapterOf({}, 'm04_clocking_in').id, 'm04_clocking_in');
  assert.equal(chapterOf({}, 'nope').id, 'm01_return_to_sender');
  const c = saveCard({ slot: 1, act: 1, chapter: 'return_to_sender', playtime: 5, coupons: 1, at: { map: 'story_slice' } }); // (no data at all)
  assert.equal(c.title, 'please take your item'); assert.equal(c.act, 1); assert.ok(!('data' in c));
});
console.log(`chapters: ${n} ok`);
