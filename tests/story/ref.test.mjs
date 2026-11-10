// node tests/story/ref.test.mjs : the solo combat referee (shared/story/refsys.js + server/storyref.js): the real room
// in the sim, story enemies with their own HP, hits checked by the room, combat events in the agreed format
import assert from 'node:assert/strict';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/invsys.js';
import '../../shared/story/solohost.js';
import '../../shared/story/refsys.js';
import { newSave } from '../../shared/story/save.js';
import { ENEMIES } from '../../shared/story/content/enemies.js'; // (the referee reads its kinds from here: name, hp, weapon, tags)
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

const out = [];
const sim = createSim({ send: (o) => out.push(o), save: newSave(0, 'story_test') });
sim.msg({ t: 'join', name: 'tester' });
const ev = (type) => out.filter((o) => o.t === 'sty' && o.k === 'combat' && o.ev.type === type).map((o) => o.ev);
const run = async (secs) => { for (let i = 0; i < secs * 20; i++) { sim.tick(0.05); await sleep(1); } };

await t('the room comes up inside the sim (mode story, the test lot, you as player 1)', async () => {
  sim.msg({ t: 'sty', k: 'spawn', kind: 'corp_temp', at: [0, 0.1, -20], id: 'temp_a', hp: 200 }); // asked for before the room is up: queued
  for (let i = 0; i < 100 && !sim.ref; i++) await sleep(50);
  assert.ok(sim.ref, 'room up: ' + (sim.refOff || ''));
  assert.equal(sim.ref.room.mode, 'story'); assert.equal(sim.ref.room.cfg.map, 'story_test'); assert.equal(sim.ref.me.id, 1);
  assert.ok(!out.some((o) => o.t === 'welcome' && o.mode !== 'story'), 'only the sim\'s own welcome reaches the client');
});

await t('a queued spawn lands: the story name, its HP pool, no bots of its own', async () => {
  const es = sim.refEnemies();
  assert.equal(es.length, 1); assert.equal(es[0].name, ENEMIES.corp_temp.name); assert.equal(es[0].sk.max, 200); assert.equal(es[0].storyId, 'temp_a');
  assert.ok(out.some((o) => o.t === 'pj' && o.id === es[0].id), 'the client was told about it (pj)');
});

await t('hits go through the room\'s checks; a 200 HP enemy takes real numbers; the kill is reported', async () => {
  const R = sim.ref, me = R.me, e = sim.refEnemies()[0];
  e.ai.nextShot = Infinity; // (it doesn't shoot back for this one)
  me.pos = [0, 0.1, -12]; me.w = 'ar';
  e.pos = [0, 0.1, -17];
  const d = [0, 0, -1];
  for (let i = 0; i < 60 && e.alive; i++) { e.pos = [0, 0.1, -17]; e.vel = [0, 0, 0]; me.pos = [0, 0.1, -12]; R.room.handle(me, { t: 'hit', to: e.id, w: 'ar', n: 1, h: 0, d }); await run(0.15); await sleep(70); } // (the room's fire-rate check is real time) (pinned: its AI would walk it off)
  const hits = ev('hit').filter((h) => h.target === 'temp_a');
  assert.ok(hits.length >= 2, 'hits reported');
  assert.equal(hits[0].max, 200); assert.equal(hits[0].kind, 'corp_temp'); assert.equal(hits[0].by, 'me'); assert.equal(hits[0].weapon, 'ar');
  assert.ok(hits[0].dmg > 0 && hits[0].dmg <= 40 && hits[0].hp === 200 - hits[0].dmg, JSON.stringify(hits[0]));
  const k = ev('kill').find((x) => x.target === 'temp_a');
  assert.ok(k, 'kill reported'); assert.equal(k.by, 'me'); assert.deepEqual(k.tags, ENEMIES.corp_temp.tags); assert.equal(k.boss, false);
  assert.ok(Array.isArray(k.at) && k.at.length === 3);
});

await t('a hit the room doesn\'t believe (too far for the weapon / too fast) does nothing', async () => {
  const R = sim.ref, me = R.me;
  sim.msg({ t: 'sty', k: 'spawn', kind: 'raider', at: [0, 0.1, -20], id: 'far' });
  const e = sim.refEnemies().find((p) => p.storyId === 'far'); e.ai.nextShot = Infinity;
  e.pos = [0, 0.1, -400]; // way out of a knife's reach
  const hp0 = e.hp;
  for (let i = 0; i < 5; i++) R.room.handle(me, { t: 'hit', to: e.id, w: 'knife', d: [0, 0, -1] });
  assert.equal(e.hp, hp0);
  sim.msg({ t: 'sty', k: 'despawn', id: 'far' });
  assert.ok(!sim.refEnemies().some((p) => p.storyId === 'far'), 'despawned');
});

await t('the dead leave after a few seconds; enemies don\'t respawn', async () => {
  await run(5);
  assert.equal(sim.refEnemies().length, 0);
});

await t('enemies fight you, not each other; going down and coming back up are reported', async () => {
  const R = sim.ref, me = R.me;
  me.pos = [0, 0.1, -10];
  sim.msg({ t: 'sty', k: 'spawn', kind: 'raider', at: [0, 0.1, -14], n: 2 });
  const es = sim.refEnemies(); assert.equal(es.length, 2);
  for (const e of es) R.room.damage(e, 1, es.find((o) => o !== e), 'ar'); // friendly fire: the same side doesn't hurt itself
  assert.ok(es.every((e) => e.hp === 100), 'no damage between enemies');
  sim.msg({ t: 'sty', k: 'damage', id: 'me', dmg: 500, why: 'story' });
  assert.ok(!me.alive); assert.ok(ev('down').some((d) => d.who === 'me'));
  for (let i = 0; i < 80 && !me.alive; i++) { sim.tick(0.05); await sleep(50); } // (your respawn timer is the room's: real time)
  assert.ok(me.alive, 'respawned'); assert.ok(ev('up').some((d) => d.who === 'me'));
  assert.equal(sim.me.seq, me.seq, 'the sim mirrors your seq');
});

await t('hold: a held enemy stands still and holds its fire; let go, it moves again', async () => {
  const R = sim.ref;
  sim.msg({ t: 'sty', k: 'spawn', kind: 'raider', at: [3, 0.1, -14], id: 'held' });
  sim.msg({ t: 'sty', k: 'hold', id: 'held', on: true });
  const e = sim.refEnemies().find((p) => p.storyId === 'held'), p0 = e.pos.slice();
  await run(2);
  assert.deepEqual(e.pos.map((x) => Math.round(x * 10)), p0.map((x) => Math.round(x * 10)), 'stood still');
  sim.msg({ t: 'sty', k: 'hold', id: 'held', on: false });
  assert.equal(e.sk.hold, false);
  sim.msg({ t: 'sty', k: 'despawn', id: 'held' });
});

await t('the save still works with the referee up (you, where the room has you)', async () => {
  const s = sim.snapshot('test');
  assert.deepEqual(s.at.p, sim.ref.me.pos.map((x) => Math.round(x * 100) / 100));
});
console.log(n, 'passed');
process.exit(0);
