// Plant & Defuse bot skill tiers: the sheets get better tier by tier, and difficulty moves who shows up
import test from 'node:test';
import assert from 'node:assert/strict';
import { SKILL, rollTier } from '../server/sdskill.js';

test('each tier is better than the next at everything that matters', () => {
  const order = ['cracked', 'good', 'average', 'bad'];
  for (let i = 0; i < 3; i++) {
    const a = SKILL[order[i]], b = SKILL[order[i + 1]];
    assert.ok(a.head > b.head && a.err < b.err && a.react < b.react && a.comp > b.comp && a.tap > b.tap && a.snap > b.snap, `${a.name} > ${b.name}`);
  }
});
test('lobbies are mixed, and difficulty shifts the mix', () => {
  const count = (diff) => { const c = { cracked: 0, good: 0, average: 0, bad: 0 }; for (let i = 0; i < 4000; i++) c[rollTier(diff, (i + 0.5) / 4000)]++; return c; };
  const e = count('easy'), n = count('normal'), h = count('hard');
  assert.equal(e.cracked, 0);
  assert.ok(n.cracked > 0 && n.bad > 0 && n.good > 0 && n.average > 0, 'normal has every kind');
  assert.ok(h.cracked > n.cracked && h.bad < n.bad && e.bad > n.bad);
  assert.ok(h.bad > 0, 'even hard lobbies have someone having a bad day');
  assert.equal(rollTier('nonsense', 0.5), rollTier('normal', 0.5));
});
