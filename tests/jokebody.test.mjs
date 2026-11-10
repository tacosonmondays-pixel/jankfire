// the joke body (head / butt sliders, build): only clean values get through validLook, bots roll valid ones
import test from 'node:test';
import assert from 'node:assert/strict';
import { validLook, BUILDS, JOKE_MAX, BODY_KEYS } from '../shared/looks.js';
import { botLook } from '../server/botlook.js';

test('validLook keeps good joke-body values and drops the rest', () => {
  const a = new Set();
  assert.deepEqual((({ build, bigHead, bigButt }) => [build, bigHead, bigButt])(validLook({ build: 'f', bigHead: 4, bigButt: 2 }, a)), ['f', 4, 2]);
  for (const bad of [{ build: 'x', bigHead: 9, bigButt: -1 }, { build: '__proto__', bigHead: 1.5, bigButt: '3' }, { build: ['f'], bigHead: NaN, bigButt: Infinity }, { build: null, bigHead: {}, bigButt: [] }]) {
    const o = validLook(bad, a);
    assert.deepEqual([o.build, o.bigHead, o.bigButt], ['', 0, 0]);
  }
});
test('every body slider takes 0..max and nothing else', () => {
  const a = new Set();
  for (const k of BODY_KEYS) {
    assert.equal(validLook({ [k]: JOKE_MAX }, a)[k], JOKE_MAX);
    for (const bad of [JOKE_MAX + 1, -1, 1.5, '2', null, NaN]) assert.equal(validLook({ [k]: bad }, a)[k], 0, `${k}=${bad}`);
  }
});
test('bots: always valid, and most of them stay normal', () => {
  let big = 0;
  for (let s = 1; s <= 400; s++) {
    const { look } = botLook(s);
    assert.ok(Object.hasOwn(BUILDS, look.build));
    for (const k of ['bigHead', 'bigButt']) assert.ok(Number.isInteger(look[k]) && look[k] >= 0 && look[k] <= JOKE_MAX);
    if (look.bigHead || look.bigButt) big++;
  }
  assert.ok(big > 20 && big < 160, `joke bodies on ${big} of 400 bots`);
});
