// node tests/story/loot.test.mjs : loot rolls (shared/story/loot.js) against the writer's tables
import assert from 'node:assert/strict';
import { rollTable, rollWeapon, rollEntry, legendaryItem, statsOf, compare, nameOf, hitWith, killWith, rng, RANGE, STATS, RARITY_ORDER, LOOT_TABLES, LEGENDARIES, BRANDS, MODIFIERS, LOOT_BASES } from '../../shared/story/loot.js';
import { makeItem, cleanInv, newInv, invAdd, kindOf } from '../../shared/story/items.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };

t('10,000 rolls match the table weights', () => {
  const T = LOOT_TABLES.lt_mission_rare, rand = rng(1), seen = {};
  for (let i = 0; i < 10000; i++) for (const it of rollTable('lt_mission_rare', rand)) seen[it.r] = (seen[it.r] || 0) + 1;
  const tot = T.entries.reduce((a, e) => a + e.w, 0);
  for (const e of T.entries) { const want = e.w / tot, got = (seen[e.rarity] || 0) / 10000; assert.ok(Math.abs(got - want) < 0.015, `${e.rarity}: ${got} vs ${want}`); }
  console.log('   ', JSON.stringify(seen));
});
t('district tables: brand + rarity per entry', () => {
  const rand = rng(7), c = {};
  for (let i = 0; i < 10000; i++) { const [it] = rollTable('lt_district_gut', rand); const k = it.r + (it.lg ? ':named' : it.br === 'gristle_biologics' || it.br === 'meat_mechanics' ? ':' + it.br : ':other'); c[k] = (c[k] || 0) + 1; }
  assert.ok(Math.abs(c['common:gristle_biologics'] / 1e4 - 0.5) < 0.02); assert.ok(Math.abs(c['rare:meat_mechanics'] / 1e4 - 0.3) < 0.02);
});
t('late night doubles premium', () => {
  const a = rng(3), b = rng(3); let p0 = 0, p1 = 0;
  for (let i = 0; i < 20000; i++) { p0 += rollTable('lt_boss_overtime_1', a).filter((x) => x.r === 'premium').length; p1 += rollTable('lt_boss_overtime_1', b, { late: true }).filter((x) => x.r === 'premium').length; }
  assert.ok(p1 / p0 > 1.6 && p1 / p0 < 2.3, `${p0} -> ${p1}`);
});
t('every table and legendary rolls real items', () => {
  const rand = rng(11), bad = [];
  for (const id of Object.keys(LOOT_TABLES)) for (let i = 0; i < 200; i++) for (const it of rollTable(id, rand)) if (!kindOf(it.b)) bad.push(id + ':' + it.b);
  assert.deepEqual(bad, []);
  for (const id of Object.keys(LEGENDARIES)) { const it = legendaryItem(id, rand); assert.ok(kindOf(it.b), id); assert.equal(it.lg, id); assert.equal(nameOf(it), LEGENDARIES[id].name); }
  assert.ok(LOOT_BASES.length >= 35);
});
t('stat ranges per rarity, and seeds rebuild the same stats', () => {
  for (const r of RARITY_ORDER) for (let i = 0; i < 300; i++) {
    const it = { b: 'ar', r, s: ((i + 1) * 2654435761) >>> 0 || 1 }; // no brand, no mods: the pure rarity roll
    const s = statsOf(it), [lo, hi] = RANGE[r];
    for (const [k, , dir] of STATS) { const bonus = dir > 0 ? s[k] - 1 : 1 / s[k] - 1; assert.ok(bonus >= lo - 0.002 && bonus <= hi + 0.002, `${r} ${k} ${bonus}`); }
    assert.deepEqual(statsOf(JSON.parse(JSON.stringify(it))), s);
  }
  const a = rollWeapon({ rarity: 'epic', base: 'redline', brand: 'corp' }, rng(5)), b = rollWeapon({ rarity: 'epic', base: 'redline', brand: 'corp' }, rng(5));
  assert.deepEqual(a, b); assert.deepEqual(statsOf(a), statsOf(b));
});
t('brands and mods change the numbers', () => {
  const base = { b: 'shotgun', r: 'rare', s: 99 };
  assert.ok(statsOf({ ...base, br: 'corp' }).spread < statsOf(base).spread);
  assert.ok(Math.abs(statsOf({ ...base, m: ['bouncy'] }).kb / statsOf(base).kb - 1.8) < 0.01);
  assert.ok(statsOf({ ...base, m: ['haunted'] }).tags.includes('haunted'));
  assert.ok(statsOf({ ...base, br: 'bottom_scrap' }).part);
  assert.deepEqual(statsOf({ ...base, m: ['nope'] }).mods, []);
});
t('mods per rarity: commons mostly plain, legendaries always have one', () => {
  const rand = rng(21); let c0 = 0, l1 = 0;
  for (let i = 0; i < 2000; i++) { if (!rollWeapon({ rarity: 'common' }, rand).m) c0++; if ((rollWeapon({ rarity: 'legendary' }, rand).m || []).length >= 1) l1++; }
  assert.ok(c0 > 1300 && l1 === 2000, `${c0} ${l1}`);
});
t('compare card arrows', () => {
  const a = { b: 'ar', r: 'common', s: 1 }, b = { b: 'ar', r: 'premium', s: 2 };
  const c = compare(a, b);
  assert.equal(c.length, STATS.length); assert.ok(c.filter((x) => x.up).length >= 5, JSON.stringify(c));
});
t('items keep loot fields through the save cleaner, junk ids dropped', () => {
  const inv = newInv(); invAdd(inv, rollWeapon({ rarity: 'epic', brand: 'famiglia' }, rng(2))); invAdd(inv, legendaryItem('severance_package', rng(3)));
  const c = cleanInv(JSON.parse(JSON.stringify(inv)));
  assert.equal(c.bag[0].br, 'famiglia'); assert.equal(c.bag[1].lg, 'severance_package'); assert.equal(c.bag[1].r, 'legendary');
  const j = makeItem('ar', { br: 'evil', m: ['x', 'bouncy'], lg: 'fake', r: 'premium' }); assert.ok(!j.br && !j.lg); assert.deepEqual(j.m, ['bouncy']);
});
t('the four slice legendaries do their thing', () => {
  const lb = legendaryItem('late_bloomer', rng(1)), lbS = statsOf(lb);
  assert.ok(Math.abs(hitWith(lb, { dmg: 10, late: 30 }).dmg - 10 * lbS.dmg * 1.3) < 1e-9);
  assert.ok(Math.abs(hitWith(lb, { dmg: 10, late: 999 }).dmg - 10 * lbS.dmg * 1.6) < 1e-9, 'caps at +60%');
  assert.deepEqual(hitWith(legendaryItem('grandmas_hands', rng(1)), { dmg: 20 }).fx, [{ heal: 6 }, { say: 'sweetie' }, { slip: true }]);
  const ladle = hitWith(legendaryItem('mothers_ladle', rng(1)), { dmg: 40 }).fx;
  assert.ok(ladle[0].splash.cone && ladle[0].splash.r === 3 && ladle[1].puddle.life === 6 && ladle[1].puddle.kind === 'soup');
  assert.deepEqual(killWith(legendaryItem('severance_package', rng(1))), [{ coupons: 50 }]);
  assert.deepEqual(killWith(rollWeapon({}, rng(1))), []);
});
t('lumps ring falls back to a holdable base', () => { const it = legendaryItem('lumps_ring', rng(1)); assert.equal(it.b, 'slapper'); });
t('organ core entries wait for WP5 (no crash, no ghost item)', () => { assert.equal(rollEntry({ item: 'core_cracked_punch_clock' }), null); });
t('seed 0 is a stock item: plain numbers', () => { const s = statsOf({ b: 'ar', r: 'common', s: 0 }); for (const [k] of STATS) assert.equal(s[k], 1, k); });
console.log(`\n${n} passed (${Object.keys(LEGENDARIES).length} legendaries, ${Object.keys(BRANDS).length} brands, ${Object.keys(MODIFIERS).length} mods, ${Object.keys(LOOT_TABLES).length} tables)`);
