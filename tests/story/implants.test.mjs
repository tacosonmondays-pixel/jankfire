// node tests/story/implants.test.mjs : implants, body budget, Drift, the clinic, HYPE + streak items, coupons, Second Stomach
import assert from 'node:assert/strict';
import { IMPLANTS, BODY_SLOTS, newBody, cleanBody, installOp, budget, driftOf, driftBand, perk, eatHp, rollQuality, QUALITY, SLICE_IMPLANTS } from '../../shared/story/implants.js';
import { newInv, invAdd, invTake, kindOf, count } from '../../shared/story/items.js';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/invsys.js';
import '../../shared/story/bodysys.js';
import { hypeCost, HYPE } from '../../shared/story/bodysys.js';
import { cleanSave } from '../../shared/story/save.js';
import { TEST } from '../../shared/story/testmap.js';
import { rng } from '../../shared/story/loot.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };
const ops = (inv) => ({ takeItem: (u) => invTake(inv, u), giveItem: (it) => invAdd(inv, it, { toBar: false }) });

t('every content implant has a real slot and is an item', () => {
  for (const [id, I] of Object.entries(IMPLANTS)) { assert.ok(BODY_SLOTS.includes(I.slot), id); assert.equal(kindOf(id), 'implant'); }
  for (const id of ['pigeon_eyes', 'spring_knees', 'core_second_stomach', 'core_cracked_punch_clock']) assert.ok(SLICE_IMPLANTS.includes(id));
});
t('budget and drift', () => {
  assert.equal(budget({ act: 1, cats: 0 }), 3); assert.equal(budget({ act: 3, cats: 7 }), 3 + 2 + 2);
  const b = newBody(), inv = newInv();
  for (const id of ['pigeon_eyes', 'spring_knees', 'spreadsheet_lobe', 'bear_trap_jaw', 'rubber_skin']) installOp(b, inv, { op: 'install', u: invAdd(inv, { b: id }) }, ops(inv));
  assert.equal(driftOf(b, { act: 1 }), 2); assert.equal(driftBand(2), 'fading'); assert.equal(driftBand(0), 'cale'); assert.equal(driftBand(4), 'employee');
  assert.equal(driftOf(b, { act: 3 }), 0);
});
t('install swaps the old one back into the bag; uninstall; bad ops', () => {
  const b = newBody(), inv = newInv();
  assert.ok(installOp(b, inv, { op: 'install', u: invAdd(inv, { b: 'pigeon_eyes' }) }, ops(inv)).ok);
  assert.equal(count(inv, 'pigeon_eyes'), 0);
  const r = installOp(b, inv, { op: 'install', u: invAdd(inv, { b: 'price_tag_eyes' }) }, ops(inv));
  assert.equal(r.swapped, 'pigeon_eyes'); assert.equal(count(inv, 'pigeon_eyes'), 1); assert.equal(b.slots.eyes.b, 'price_tag_eyes');
  assert.ok(installOp(b, inv, { op: 'uninstall', slot: 'eyes' }, ops(inv)).ok); assert.ok(!b.slots.eyes);
  for (const m of [{ op: 'install', u: 999 }, { op: 'install', u: invAdd(inv, { b: 'ar' }) }, { op: 'uninstall', slot: 'tail' }, { op: 'uninstall', slot: 'eyes' }, { op: 'x' }, null]) assert.ok(installOp(b, inv, m, ops(inv)).error, JSON.stringify(m));
});
t('cleanBody: wrong slots, junk, quality kept', () => {
  const c = cleanBody({ slots: { eyes: { b: 'spring_knees' }, legs: { b: 'spring_knees' }, heart: { b: 'core_cracked_punch_clock', ql: 'prime' }, guts: { b: 'nope' }, tail: { b: 'pigeon_eyes' } }, perm: 999 });
  assert.deepEqual(c.slots, { legs: { b: 'spring_knees' }, heart: { b: 'core_cracked_punch_clock', ql: 'prime' } }); assert.equal(c.perm, 20);
});
t('slice perks: numbers, quality, overload', () => {
  const b = newBody(), inv = newInv();
  installOp(b, inv, { op: 'install', u: invAdd(inv, { b: 'spring_knees' }) }, ops(inv));
  assert.equal(perk(b, 'spring_knees').jump, 1.8); assert.equal(perk(b, 'spring_knees').fold, 1 / 20); assert.equal(perk(b, 'pigeon_eyes'), null);
  installOp(b, inv, { op: 'install', u: invAdd(inv, { b: 'core_second_stomach', ql: 'premium' }) }, ops(inv));
  const s = perk(b, 'core_second_stomach'); assert.equal(eatHp(s, 'common'), 15); assert.equal(eatHp(s, 'premium'), 120);
  for (const id of ['pigeon_eyes', 'spreadsheet_lobe']) installOp(b, inv, { op: 'install', u: invAdd(inv, { b: id }) }, ops(inv));
  const over = perk(b, 'spring_knees', { act: 1 }); assert.ok(over.over); assert.ok(Math.abs(over.fold - 1.5 / 20) < 1e-9, 'over budget: louder downsides');
  assert.ok(perk(b, 'pigeon_eyes', { act: 1 }).flipEvery < 30);
});
t('core quality roll', () => { const r = rng(9), c = {}; for (let i = 0; i < 5000; i++) { const q = rollQuality(r); c[q] = (c[q] || 0) + 1; } assert.ok(c.fresh > c.bruised && c.bruised > c.prime && c.prime > c.premium, JSON.stringify(c)); for (const q of Object.keys(c)) assert.ok(QUALITY[q]); });
t('hype costs: moon boots 25 .. giant duck 100', () => { assert.equal(hypeCost('moonboots'), 25); assert.equal(hypeCost('giantduck'), 100); assert.ok(hypeCost('satellite') > 25 && hypeCost('satellite') < 100); });

t('sim: clinic buy/install/uninstall, coupons, drift message, save round trip', () => {
  const out = []; const sim = createSim({ send: (o) => out.push(o) }); sim.msg({ t: 'join' });
  assert.equal(sim.save.coupons, 5000, 'test lot coupons');
  const last = (k) => out.filter((o) => o.k === k).at(-1);
  sim.msg({ t: 'sty', k: 'clinic', op: 'buy', id: 'spring_knees' }); assert.equal(last('clinicErr').err, 'find a meat mechanic first');
  sim.msg({ t: 's', q: 1, p: TEST.clinic.p.map((x, i) => (i === 1 ? 0.1 : x)), v: [0, 0, 0] });
  sim.msg({ t: 'sty', k: 'clinic', op: 'buy', id: 'spring_knees' }); assert.equal(sim.save.coupons, 3500); assert.equal(count(sim.inv, 'spring_knees'), 1);
  sim.msg({ t: 'sty', k: 'clinic', op: 'buy', id: 'core_second_stomach' }); assert.match(last('clinicErr').err, /don't sell/);
  sim.msg({ t: 'sty', k: 'clinic', op: 'buy', id: '__proto__' }); sim.msg({ t: 'sty', k: 'clinic', op: 'buy', id: 5 });
  const u = sim.inv.bag.find((x) => x && x.b === 'spring_knees').u;
  sim.msg({ t: 'sty', k: 'clinic', op: 'install', u }); assert.equal(sim.body.slots.legs.b, 'spring_knees'); assert.equal(last('body').drift, 0); assert.equal(last('body').budget, 3);
  sim.msg({ t: 'sty', k: 'clinic', op: 'uninstall', slot: 'legs' }); assert.equal(sim.save.coupons, 3350); assert.equal(count(sim.inv, 'spring_knees'), 1);
  sim.msg({ t: 'sty', k: 'clinic', op: 'install', u: sim.inv.bag.find((x) => x && x.b === 'spring_knees').u });
  for (let i = 0; i < 3; i++) sim.msg({ t: 'sty', k: 'clinic', op: 'buy', id: 'lead_lining' }); // (the buying is fine; no budget in buying)
  sim.save.coupons = 100; sim.msg({ t: 'sty', k: 'clinic', op: 'buy', id: 'pigeon_eyes' }); assert.match(last('clinicErr').err, /1200 coupons/);
  sim.msg({ t: 'sty', k: 'save' }); const sv = cleanSave(out.filter((o) => o.k === 'saved').at(-1).save).save;
  assert.equal(sv.data.body.slots.legs.b, 'spring_knees'); assert.equal(sv.coupons, 100);
  const sim2 = createSim({ send: () => {}, save: sv }); assert.equal(sim2.body.slots.legs.b, 'spring_knees');
});
t('sim: HYPE fills, drains when quiet, pays for streak items', () => {
  const out = []; const sim = createSim({ send: (o) => out.push(o) }); sim.dev = true; sim.msg({ t: 'join' });
  const mb = sim.inv.bag.length && invAdd(sim.inv, { b: 'moonboots', q: 2 });
  sim.msg({ t: 'sty', k: 'streak', u: mb }); assert.equal(out.at(-1).why, 'short'); assert.equal(count(sim.inv, 'moonboots'), 2);
  sim.addHype(40, 'kill'); sim.msg({ t: 'sty', k: 'streak', u: mb });
  assert.deepEqual(out.find((o) => o.t === 'streak'), { t: 'streak', reward: 'moonboots', dur: 25 }); assert.equal(count(sim.inv, 'moonboots'), 1); assert.equal(sim.hype, 15);
  for (let i = 0; i < 30; i++) sim.tick(0.5); // 15 s: quiet after 8, then drain 1.5/s
  assert.ok(sim.hype < 15 && sim.hype >= 0, String(sim.hype));
  sim.addHype(500); assert.equal(sim.hype, HYPE.max);
  sim.msg({ t: 'sty', k: 'hypeEv', ev: 'grapple', n: 999 }); // capped, and rate limited
  sim.msg({ t: 'sty', k: 'save' }); assert.equal(cleanSave(out.filter((o) => o.k === 'saved').at(-1).save).save.data.hype, 100);
});
t('sim: Second Stomach eats dropped weapons, the third in a row says vomit', () => {
  const out = []; const sim = createSim({ send: (o) => out.push(o) }); sim.msg({ t: 'join' });
  const gun = [...sim.drops.values()].find((d) => kindOf(d.item.b) === 'gun');
  sim.msg({ t: 'sty', k: 'eatDrop', id: gun.id }); assert.match(out.at(-1).err, /one stomach/);
  sim.body.slots.guts = { b: 'core_second_stomach', ql: 'fresh' };
  sim.msg({ t: 's', q: 1, p: gun.p.slice(), v: [0, 0, 0] }); sim.me.hp = 40;
  sim.msg({ t: 'sty', k: 'eatDrop', id: gun.id }); const h = out.find((o) => o.t === 'heal');
  assert.equal(h.hp, 40 + eatHp(perk(sim.body, 'core_second_stomach'), gun.item.r)); assert.ok(!sim.drops.has(gun.id));
  const guns = [...sim.drops.values()].filter((d) => kindOf(d.item.b) === 'gun' || kindOf(d.item.b) === 'melee').slice(0, 2);
  for (const g of guns) { sim.msg({ t: 's', q: 1, p: g.p.slice(), v: [0, 0, 0] }); sim.msg({ t: 'sty', k: 'eatDrop', id: g.id }); }
  assert.equal(out.filter((o) => o.k === 'ate').at(-1).vomit, true);
  const snack = [...sim.drops.values()].find((d) => d.item.b === 'jank_cola');
  sim.msg({ t: 's', q: 1, p: snack.p.slice(), v: [0, 0, 0] }); sim.msg({ t: 'sty', k: 'eatDrop', id: snack.id }); assert.match(out.at(-1).err, /can't eat that/);
});
console.log(`\n${n} passed (${Object.keys(IMPLANTS).length} implants)`);
