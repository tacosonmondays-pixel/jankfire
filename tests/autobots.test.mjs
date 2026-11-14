// the offline hub's automatic bot count (shared/autobots.js): by map size, even teams, own-sized modes left alone
import test from 'node:test';
import assert from 'node:assert/strict';
import { autoBots, AUTO_BOTS } from '../shared/autobots.js';
import { GAMES } from '../shared/modes.js';
import { MAPS, MAP_ORDER } from '../shared/map.js';

test('small maps get fewer bots, big maps more', () => {
  assert.equal(autoBots('dm', 'crate', GAMES, MAPS), AUTO_BOTS.tiny);
  assert.equal(autoBots('dm', 'platform', GAMES, MAPS), AUTO_BOTS.medium);
  assert.equal(autoBots('dm', 'suburb', GAMES, MAPS), AUTO_BOTS.large);
  assert.equal(autoBots('dm', 'skyline', GAMES, MAPS), AUTO_BOTS.huge);
  assert.ok(autoBots('dm', 'crate', GAMES, MAPS) < autoBots('dm', 'skyline', GAMES, MAPS));
  assert.equal(autoBots('dm', 'nope', GAMES, MAPS), AUTO_BOTS.medium); // (a map with no size tag: medium)
});
test('team modes always come out even (you + the bots)', () => {
  for (const g of Object.keys(GAMES).filter((g) => GAMES[g].teams && g !== 'bomb')) for (const m of MAP_ORDER) {
    const n = autoBots(g, m, GAMES, MAPS);
    assert.equal((n + 1) % 2, 0, `${g} on ${m}: ${n} bots + you`);
  }
});
test('modes that size their own room are left alone', () => {
  for (const g of ['zm', 'bomb', 'bgn', 'br', 'island']) assert.equal(autoBots(g, 'crate', GAMES, MAPS), null, g);
});
test('never more than the server clamp', () => {
  for (const g of Object.keys(GAMES)) for (const m of MAP_ORDER) { const n = autoBots(g, m, GAMES, MAPS); assert.ok(n == null || (n >= 0 && n <= 12), `${g} ${m} ${n}`); }
});
