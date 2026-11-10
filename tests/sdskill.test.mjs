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

// cover routes: the walk-graph search takes extra per-node costs, and a route goes round costly ground when it can
import { navPath, navLocate } from '../shared/nav.js';
import { MAPS } from '../shared/map.js';
test('cover and corner sense improve tier by tier (bad bots have none)', () => {
  const order = ['cracked', 'good', 'average', 'bad'];
  for (let i = 0; i < 3; i++) assert.ok(SKILL[order[i]].cover > SKILL[order[i + 1]].cover && SKILL[order[i]].pre > SKILL[order[i + 1]].pre);
  assert.equal(SKILL.bad.cover, 0); assert.equal(SKILL.bad.pre, 0);
});
test('a weighted route avoids the costly nodes and no weights means the old route', () => {
  const m = MAPS.warehouse_sd, g = m.graph, ts = m.teamSpawns;
  const a = navLocate(g, ts.att[0]), b = navLocate(g, ts.def[0]);
  const plain = navPath(g, a, b);
  assert.ok(plain && plain.length > 10);
  assert.deepEqual(navPath(g, a, b, undefined, null), plain);
  const w = new Float32Array(g.nodes.length), mid = plain.slice(Math.floor(plain.length / 3), Math.floor(plain.length * 2 / 3));
  for (const k of mid) w[k] = 4;
  const round = navPath(g, a, b, undefined, w), bad = new Set(mid);
  assert.ok(round && round[0] === a && round[round.length - 1] === b);
  assert.ok(round.filter((k) => bad.has(k)).length < mid.length / 2, 'went round most of it');
});
