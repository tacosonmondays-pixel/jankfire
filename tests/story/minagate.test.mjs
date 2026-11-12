// Mina is in the Digester Wall only while her fate is gut (m04 truck sends her, both act III endings free her), and "...you're late." plays her `late` head turn
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test as cond } from '../../shared/story/cond.js';
import { NPC_SPOTS } from '../../shared/city/cast_slice.js';
import { MISSIONS_ACT3 as ACT3 } from '../../shared/story/content/missions/act3.js';

const st = (quests = {}, flags = {}) => ({ flags, vars: {}, standing: {}, met: {}, seen: {}, codex: {}, quests });
test('mina shows in the wall only while her fate is gut (after m04, until act III frees her)', () => {
  const c = NPC_SPOTS.mina.if, f = (v) => ({ [`fate.mina.${v}`]: true });
  assert.ok(c, 'her wall spot has a condition');
  assert.equal(cond(c, st({}, f('alive'))), false, 'new game (alive): not there');
  assert.equal(cond(c, st({ m03_somethings_digesting: { step: 'dot' } }, f('alive'))), false, 'm03 (dot only says her name): not there');
  assert.equal(cond(c, st({ m04_clocking_in: { step: 'truck' } }, f('alive'))), false, 'during m04: not there yet');
  assert.equal(cond(c, st({ m04_clocking_in: { done: true } }, f('gut'))), true, 'after m04 (fate gut): in the wall');
  assert.equal(cond(c, st({ m04_clocking_in: { done: true } }, f('freed'))), false, 'freed in act III: gone');
});
test('m04 sends her to the gut and both act III endings free her', () => {
  const src = (p) => readFileSync(new URL(p, import.meta.url), 'utf8');
  assert.match(src('../../shared/story/content/missions/act1.js'), /fate:mina=gut/);
  assert.equal((src('../../shared/story/content/missions/act3.js').match(/fate:mina=freed/g) || []).length, 2);
});
test("'...you're late.' plays mina's late clip", () => {
  const hits = [];
  const walk = (o) => { if (Array.isArray(o)) o.forEach(walk); else if (o && typeof o === 'object') { if (o.t === "...you're late.") hits.push(o); Object.values(o).forEach(walk); } };
  walk(ACT3);
  assert.equal(hits.length, 1);
  assert.deepEqual(hits[0].do, ['anim:mina/late']);
  assert.match(readFileSync(new URL('../../public/js/story/actors.js', import.meta.url), 'utf8'), /\blate\s*:/, 'actors.js has a late clip');
});
