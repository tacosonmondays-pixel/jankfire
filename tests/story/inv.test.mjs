// node tests/story/inv.test.mjs : the Tote Bag / quick bar / locker (shared/story/items.js) and the inventory sim system
import assert from 'node:assert/strict';
import { newInv, invAdd, invOp, invTake, cleanInv, kindOf, barWeapons, starterInv, count, INV, makeItem } from '../../shared/story/items.js';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/invsys.js';
import { cleanSave } from '../../shared/story/save.js';
import { WEAPONS, ITEMS, STREAKS } from '../../shared/weapons.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };

t('kinds', () => {
  assert.equal(kindOf('ar'), 'gun'); assert.equal(kindOf('revolver'), 'gun'); assert.equal(kindOf('katana'), 'melee');
  assert.equal(kindOf('frag'), 'gear'); assert.equal(kindOf('moonboots'), 'streak'); assert.equal(kindOf('jank_cola'), 'snack');
  for (const bad of ['rigpunch', 'claw', 'nope', '__proto__', 'constructor', 5, null]) assert.equal(kindOf(bad), null, String(bad));
});
t('every held weapon, gear and streak is an item', () => {
  for (const [id, w] of Object.entries(WEAPONS)) if (['primary', 'secondary', 'melee'].includes(w.slot) && !w.modeOnly) assert.ok(makeItem(id), id);
  for (const id of [...Object.keys(ITEMS), ...Object.keys(STREAKS)]) assert.ok(makeItem(id), id);
});
t('add: bar fills, stacks cap, full bag', () => {
  const inv = newInv();
  const a = invAdd(inv, { b: 'ar' }), b = invAdd(inv, { b: 'katana' });
  assert.deepEqual(inv.bar.slice(0, 2), [a, b]);
  for (let i = 0; i < 5; i++) invAdd(inv, { b: 'moonboots' });
  assert.equal(count(inv, 'moonboots'), 5); assert.equal(inv.bag.filter((x) => x && x.b === 'moonboots').map((x) => x.q).join(), '3,2');
  invAdd(inv, { b: 'bottlecap' }); assert.ok(!inv.bar.includes(inv.bag.find((x) => x && x.b === 'bottlecap').u), 'junk stays off the bar');
  while (invAdd(inv, { b: 'ar' }));
  assert.equal(inv.bag.filter(Boolean).length, INV.bag);
  const extra = { b: 'bottlecap', q: 30 }; assert.ok(invAdd(inv, extra) === 0 && extra.q === 11, 'stacked 19 onto the cap, 11 left over');
});
t('ops: only items you have, quest items stay', () => {
  const inv = starterInv({ primary: 'redline', secondary: 'marbles', melee: 'knife', item: 'frag' });
  assert.deepEqual(barWeapons(inv), ['redline', 'marbles', 'knife', null, null, null, null, null]);
  assert.ok(invOp(inv, { op: 'bar', slot: 7, u: inv.bar[0] }).ok); assert.equal(barWeapons(inv)[7], 'redline'); assert.equal(inv.bar[0], null);
  for (const bad of [{ op: 'bar', slot: 8, u: 1 }, { op: 'bar', slot: 0, u: 999 }, { op: 'bar', slot: -1, u: null }, { op: 'bar', slot: '1', u: 1 }, { op: 'move', from: 0, to: 99 }, { op: 'drop', u: 999 }, { op: 'stash', u: 1 }, { op: 'zzz' }, null, { op: 5 }])
    assert.ok(invOp(inv, bad).error, JSON.stringify(bad));
  const q = invAdd(inv, { b: 'page_corp' }); // a keep item (content/items.js): no bar, no drop
  assert.ok(invOp(inv, { op: 'bar', slot: 3, u: q }).error); assert.ok(invOp(inv, { op: 'drop', u: q }).error);
  const d = invOp(inv, { op: 'drop', u: inv.bar[1] }); assert.equal(d.dropped.b, 'marbles'); assert.equal(inv.bar[1], null);
  assert.ok(invOp(inv, { op: 'stash', u: inv.bar[2] }, { atLocker: true }).ok); assert.equal(inv.locker[0].b, 'knife');
  assert.ok(invOp(inv, { op: 'unstash', i: 0 }, { atLocker: true }).ok); assert.equal(inv.locker.length, 0); assert.equal(count(inv, 'knife'), 1);
});
t('take part of a stack', () => { const inv = newInv(); const u = invAdd(inv, { b: 'jank_cola', q: 3 }); assert.equal(invTake(inv, u, 2).q, 2); assert.equal(count(inv, 'jank_cola'), 1); });
t('clean a hand-edited inventory', () => {
  const c = cleanInv({ cap: 9999, bag: [{ u: 1, b: 'ar' }, { u: 1, b: 'smg' }, { u: 2, b: 'nope' }, { u: 3, b: 'moonboots', q: 99 }, 'x', { u: -4, b: 'ar' }], bar: [1, 1, 3, 77, 'a'], locker: [{ b: 'katana' }, { b: 'zz' }], next: -5 });
  assert.equal(c.cap, INV.bagMax); assert.equal(c.bag[0].b, 'ar'); assert.equal(c.bag[1], null); assert.equal(c.bag[2], null); assert.equal(c.bag[3].q, 3);
  assert.deepEqual(c.bar, [1, null, 3, null, null, null, null, null]); assert.equal(c.locker.length, 1); assert.equal(c.next, 4);
  assert.deepEqual(cleanInv('junk').bag.length, INV.bag);
});
t('sim: starter, pick, drop, gear charges, eat, save round trip', () => {
  const out = []; const sim = createSim({ send: (o) => out.push(o) });
  sim.msg({ t: 'join', name: 'x', item: 'frag' });
  const drops = out.find((o) => o.k === 'drops').list; assert.ok(drops.length >= 8);
  sim.msg({ t: 'sty', k: 'starter', lo: { primary: 'ar', secondary: 'pistol', melee: 'bread', item: 'medkit' } });
  assert.deepEqual(barWeapons(sim.inv).slice(0, 3), ['ar', 'pistol', 'bread']);
  sim.msg({ t: 'sty', k: 'starter', lo: { primary: 'sniper' } }); // only once
  const cola = drops.find((d) => d.item.b === 'jank_cola');
  sim.msg({ t: 'sty', k: 'pick', id: cola.id }); assert.equal(out.at(-1).err, 'too far');
  sim.msg({ t: 's', q: 1, p: cola.p.slice(), v: [0, 0, 0] });
  sim.msg({ t: 'sty', k: 'pick', id: cola.id }); assert.equal(count(sim.inv, 'jank_cola'), 3); assert.ok(out.some((o) => o.k === 'drop-' && o.id === cola.id));
  sim.msg({ t: 'sty', k: 'pick', id: cola.id }); assert.equal(count(sim.inv, 'jank_cola'), 3, 'no double pick');
  sim.me.hp = 50; const cu = sim.inv.bag.find((x) => x && x.b === 'jank_cola').u;
  sim.msg({ t: 'sty', k: 'eat', u: cu }); assert.equal(out.find((o) => o.t === 'heal').hp, 75); assert.equal(count(sim.inv, 'jank_cola'), 2);
  const mk = sim.inv.bag.find((x) => x && x.b === 'medkit').u;
  sim.msg({ t: 'sty', k: 'gear', u: mk }); assert.deepEqual(out.at(-1), { t: 'ic', i: 'medkit', n: 1, next: 0 });
  sim.msg({ t: 'item', i: 'medkit' }); assert.equal(count(sim.inv, 'medkit'), 0); assert.equal(out.find((o) => o.t === 'ic' && o.n === 0).i, 'medkit');
  sim.msg({ t: 'item', i: 'medkit' }); // nothing left: ignored
  sim.msg({ t: 'sty', k: 'inv', op: 'drop', u: sim.inv.bar[0] }); assert.equal(out.filter((o) => o.k === 'drop+').at(-1).d.item.b, 'ar');
  sim.msg({ t: 'sty', k: 'save' }); const sv = cleanSave(out.at(-1).save).save;
  assert.ok(sv.data.flags.includes('testLoot')); assert.equal(sv.data.inv.bag.filter(Boolean).length, sim.inv.bag.filter(Boolean).length);
  const out2 = []; const sim2 = createSim({ send: (o) => out2.push(o), save: sv }); sim2.msg({ t: 'join' });
  assert.deepEqual(sim2.inv.bar, sim.inv.bar); assert.equal(out2.find((o) => o.k === 'drops').list.length, Math.min(40, sim.drops.size), 'the floor comes back as it was (not seeded twice)');
});
t('dev give only with the dev flag', () => {
  const out = []; const sim = createSim({ send: (o) => out.push(o) }); sim.msg({ t: 'join' });
  sim.msg({ t: 'sty', k: 'give', b: 'minigun', slot: 2 }); assert.equal(count(sim.inv, 'minigun'), 0);
  sim.dev = true; sim.msg({ t: 'sty', k: 'give', b: 'minigun', slot: 2 }); assert.equal(barWeapons(sim.inv)[2], 'minigun');
});
t('floor loot survives a save (cap per zone, oldest first)', () => {
  const out = []; const sim = createSim({ send: (o) => out.push(o) }); sim.msg({ t: 'join' });
  const n0 = sim.drops.size; assert.ok(n0 > 5);
  sim.msg({ t: 'sty', k: 'save' }); const sv = cleanSave(out.at(-1).save).save;
  assert.equal(sv.data.floor.story_test.length, Math.min(40, n0));
  const out2 = []; const sim2 = createSim({ send: (o) => out2.push(o), save: sv }); sim2.msg({ t: 'join' });
  assert.equal(sim2.drops.size, Math.min(40, n0), 'the pile is back, and not seeded twice');
  for (let i = 0; i < 80; i++) sim2.dropAt({ b: 'bottlecap' }, [0, 0.6, 0]);
  assert.equal(sim2.drops.size, 60, 'live cap'); sim2.msg({ t: 'sty', k: 'save' });
  const f = cleanSave(out2.at(-1).save).save.data.floor.story_test; assert.equal(f.length, 40); assert.ok(f.every((d) => d.item.b === 'bottlecap'), 'newest kept');
  assert.deepEqual(cleanSave({ ...sv, data: { ...sv.data, floor: { 'BAD ZONE': [], story_test: [{ item: { b: 'nope' }, p: [0, 0, 0] }, { item: { b: 'ar' }, p: [NaN, 1, 1] }] } } }).save?.data.floor ?? {}, {});
});
console.log(`${n} passed (+ floor)`);
