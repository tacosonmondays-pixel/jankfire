// card deck 3D cards: the look is bigger than the hitbox, the pools stay capped, the suit comes from the last played card.
// node --test tests/cardfx.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { CARD_W, CARD_H, CAPS, GLOW, Pool, suitFor } from '../public/js/cardpool.js';
import { WEAPONS } from '../shared/weapons.js';

test('the card is drawn ~1.6x the old card, but the server card is untouched', () => {
  assert.ok(Math.abs(CARD_W / 0.18 - 1.6) < 0.05 && Math.abs(CARD_H / 0.26 - 1.6) < 0.05);
  const C = WEAPONS.card;
  assert.equal(C.r, 0.26); assert.equal(C.speed, 85); assert.equal(C.dmg, 11); assert.equal(C.fan, 6); assert.equal(C.flick, 2); assert.equal(C.kb, 4);
  // the looks never reach the hit logic: the server doesn't load them, and the client files don't write the card's numbers
  for (const f of ['server/room.js', 'server.js']) assert.ok(!/cardpool|cardfx|cardmesh/.test(readFileSync(new URL('../' + f, import.meta.url), 'utf8')));
  for (const f of ['cardfx.js', 'cardmesh.js', 'cardpool.js']) assert.ok(!/WEAPONS\.card\.\w+\s*=[^=]|\.r\s*=[^=]/.test(readFileSync(new URL('../public/js/' + f, import.meta.url), 'utf8')), f);
});

test('pools make each thing once and never grow past their cap (the oldest is recycled)', () => {
  let made = 0, stolen = [];
  const p = new Pool(4, (i) => ({ i, n: ++made }), (it) => stolen.push(it.i));
  const a = [];
  for (let k = 0; k < 10; k++) a.push(p.take());
  assert.equal(made, 4); assert.equal(p.live.length, 4);
  assert.deepEqual(stolen, [0, 1, 2, 3, 0, 1]);
  p.give(a[9]); assert.equal(p.live.length, 3); assert.equal(p.free.length, 1);
  assert.equal(p.take(), a[9]); assert.equal(made, 4); // reused, not made
  assert.equal(p.give({}), false); // not ours: ignored
  p.trim(2); assert.equal(p.live.length, 2);
  p.clear(); assert.equal(p.live.length, 0); assert.equal(p.free.length, 4);
  for (const k of ['fly', 'stuck', 'stuckPotato', 'puff']) assert.ok(CAPS[k] > 0 && CAPS[k] <= 96, k);
  assert.ok(CAPS.stuckPotato < CAPS.stuck);
  assert.ok(CAPS.fly >= 24 * 2, 'two face-card spade fans in the air at once still fit');
});

test('thrown cards take the suit of the card just played, else spades', () => {
  const last = new Map([[7, { suit: 'h', t: 1000 }]]);
  assert.equal(suitFor(last, 7, 1100), 'h');
  assert.equal(suitFor(last, 7, 2000), 's'); // too long ago: a bot's flick
  assert.equal(suitFor(last, 8, 1100), 's');
  for (const k of ['s', 'c', 'h', 'd', 'j']) assert.ok(Number.isInteger(GLOW[k]));
});
