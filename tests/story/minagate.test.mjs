// Mina is in the Digester Wall only after the m04 truck takes her there, and not once the Gut's decided (both endings
// free her); "...you're late." plays her `late` head turn
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test as cond } from '../../shared/story/cond.js';
import { NPC_SPOTS } from '../../shared/city/cast_slice.js';
import { MISSIONS_ACT3 as ACT3 } from '../../shared/story/content/missions/act3.js';

const st = (quests = {}, flags = {}) => ({ flags, vars: {}, standing: {}, met: {}, seen: {}, codex: {}, quests });
test('mina shows in the wall only between m04 and the gut deciding', () => {
  const c = NPC_SPOTS.mina.if;
  assert.ok(c, 'her wall spot has a condition');
  assert.equal(cond(c, st()), false, 'new game: not there');
  assert.equal(cond(c, st({ m03_somethings_digesting: { step: 'dot' } })), false, 'm03 (dot only says her name): not there');
  assert.equal(cond(c, st({ m03_somethings_digesting: { done: true }, m04_clocking_in: { step: 'truck' } })), false, 'during m04: not there yet');
  assert.equal(cond(c, st({ m04_clocking_in: { done: true } })), true, 'after m04: in the wall');
  assert.equal(cond(c, st({ m04_clocking_in: { done: true } }, { gut_decided: true })), false, 'gut decided (deal or takeover free her): gone');
});
test("'...you're late.' plays mina's late clip", () => {
  const hits = [];
  const walk = (o) => { if (Array.isArray(o)) o.forEach(walk); else if (o && typeof o === 'object') { if (o.t === "...you're late.") hits.push(o); Object.values(o).forEach(walk); } };
  walk(ACT3);
  assert.equal(hits.length, 1);
  assert.deepEqual(hits[0].do, ['anim:mina/late']);
  assert.match(readFileSync(new URL('../../public/js/story/actors.js', import.meta.url), 'utf8'), /\blate\s*:/, 'actors.js has a late clip');
});
