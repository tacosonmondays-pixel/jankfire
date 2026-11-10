// the enemy table the combat referee reads: every weapon, faction and look resolves; every boss add has an enemy
import test from 'node:test';
import assert from 'node:assert/strict';
import { ENEMIES, ADDS } from '../../shared/story/content/index.js';
import { FIGHTS } from '../../shared/story/content/boss_fights.js';
import { FACTIONS } from '../../shared/story/content/world.js';
import * as W from '../../shared/weapons.js';

const WEAPONS = W.WEAPONS || W.default || W;

test('every enemy has hp, a real weapon, a real faction and a look', () => {
  for (const [id, e] of Object.entries(ENEMIES)) {
    assert.match(id, /^[a-z0-9_]+$/, id);
    assert.ok(Number.isFinite(e.hp) && e.hp > 0, `${id} hp`);
    assert.ok(Object.hasOwn(WEAPONS, e.weapon), `${id} weapon ${e.weapon}`);
    assert.ok(Object.hasOwn(FACTIONS, e.faction), `${id} faction ${e.faction}`);
    assert.ok(typeof e.look === 'string' || (e.look && e.look.body), `${id} look`);
    assert.ok(Array.isArray(e.tags) && e.name && e.does && e.line, `${id} fields`);
  }
});

test('boss adds map to enemies', () => {
  for (const [id, n] of Object.entries(ADDS)) assert.ok(ENEMIES[n], `${id} -> ${n}`);
  const named = new Set(Object.values(FIGHTS).flatMap((f) => (f.adds || []).map((a) => a.name)));
  for (const k of Object.keys(ADDS)) assert.ok(named.has(k), `ADDS has '${k}' but no boss fight has those adds`);
});
