// node tests/story/boss.test.mjs : boss fights in the combat referee (server/storyboss.js through shared/story/refsys.js):
// Mr. Overtime's first fight from its design data. spawn, part hits and crits, the plate, phases at their thresholds,
// the hold between phases, an attack's damage window, and the fight's end (he isn't killed: it's rescheduled)
import assert from 'node:assert/strict';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/invsys.js';
import '../../shared/story/solohost.js';
import '../../shared/story/refsys.js';
import { newSave } from '../../shared/story/save.js';
import { BOSSES } from '../../shared/story/content/bosses.js';
import { WEAPONS } from '../../shared/weapons.js';
import { BOSS } from '../../server/storyboss.js';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

const D = BOSSES.overtime_1, HEALTH = D.layers.find((l) => l.bar === 'health').of, CRIT = D.weakPoints[0].crit;
const out = [];
const sim = createSim({ send: (o) => out.push(o), save: newSave(0, 'story_test') });
sim.msg({ t: 'join', name: 'tester' });
const ev = (type) => out.filter((o) => o.t === 'sty' && o.k === 'combat' && o.ev.type === type).map((o) => o.ev);
const run = async (secs) => { for (let i = 0; i < Math.round(secs * 20); i++) { sim.tick(0.05); await sleep(0); } };
for (let i = 0; i < 100 && !sim.ref; i++) await sleep(50);
assert.ok(sim.ref, 'room up: ' + (sim.refOff || ''));
const R = sim.ref, me = R.me;
let e, B;
// you, standing in front of him (he faces +z) on an open bit of the test lot; he keeps his hands to himself unless asked
const BX = -15, BZ = 10;
const place = (d = 9, x = 0) => { me.pos = [BX + x, 0.1, BZ + d]; me.hp = 100; me.alive = true; me.spawnT = 0; e.pos = [BX, e.pos[1], BZ]; e.yaw = Math.PI; };
const quiet = () => { B.next = Infinity; B.act = null; B.shots.length = 0; B.ring = null; };
// a shot from your eyes at a spot on him (his own space: x right, y up, z forward = towards you)
const aimAt = (x, y, z) => { const o = [me.pos[0], me.pos[1] + 1.6, me.pos[2]], p = [e.pos[0] - x, e.pos[1] + y, e.pos[2] + z], d = p.map((v, i) => v - o[i]), l = Math.hypot(...d); return d.map((v) => v / l); };
const shoot = async (d, w = 'ar') => { const a = ev('hit').length; R.room.handle(me, { t: 'hit', to: e.id, w, n: 1, h: 1, d }); await sleep(130); return ev('hit').slice(a).filter((h) => h.target === 'overtime_1'); }; // (h: 1 = a claimed headshot: he takes none) (the room's fire-rate check is real time)
const hurt = (amt) => R.room.damage(e, amt, me, 'ar'); // no ray: counts like a blast

await t('spawn: the boss from content/bosses.js, his real pool, one at a time, the client is told', async () => {
  sim.msg({ t: 'sty', k: 'spawn', kind: 'overtime_1', at: [BX, 0.1, BZ], hp: 5, n: 3 });
  sim.msg({ t: 'sty', k: 'spawn', kind: 'overtime_1', at: [BX + 4, 0.1, BZ] }); // already here
  const es = sim.refEnemies();
  assert.equal(es.length, 1); e = es[0]; B = e.sk.b;
  assert.ok(B, 'a boss'); assert.equal(e.sk.max, D.hp); assert.equal(B.hp, 4200); assert.equal(e.name, 'MR. OVERTIME'); assert.equal(e.sk.boss, true);
  assert.deepEqual(B.def.phases.map((p) => p.to), [50, 45, 0]);
  assert.deepEqual(B.def.phases.map((p) => p.moves), [['staple', 'slam'], [], ['punchin', 'fan']]);
  assert.equal(B.def.phases[1].rest, 15); assert.equal(B.def.health, HEALTH); assert.equal(B.def.crit, CRIT);
  assert.ok(B.def.parts && B.def.parts.parts.heart && B.def.parts.parts.plate, 'the hitboxes from c_overtime.parts.json');
  const on = out.find((o) => o.t === 'sty' && o.k === 'boss' && o.on);
  assert.deepEqual({ id: on.id, pid: on.pid, hp: on.hp, max: on.max, health: on.health, name: on.name, phase: on.phase, who: on.who }, { id: 'overtime_1', pid: e.id, hp: 4200, max: 4200, health: HEALTH, name: 'MR. OVERTIME', phase: 'COLLECTION', who: 'overtime' });
  await run(0.5); quiet();
});

await t('part hits: the plate takes it in full, the rest is soft, a claimed headshot is nothing, a wide shot misses', async () => {
  place();
  const plate = await shoot(aimAt(0, 3.38, 1.07));
  assert.equal(plate.length, 1); assert.equal(plate[0].part, 'plate'); assert.equal(plate[0].crit, false); assert.equal(plate[0].head, false);
  assert.equal(plate[0].dmg, WEAPONS.ar.dmg); assert.equal(plate[0].max, 4200); assert.equal(plate[0].hp, 4200 - WEAPONS.ar.dmg); assert.equal(plate[0].boss, 'overtime_1'); assert.equal(plate[0].by, 'me');
  const legs = await shoot(aimAt(0, 0.9, 0));
  assert.equal(legs[0].part, 'body'); assert.equal(legs[0].dmg, Math.round(WEAPONS.ar.dmg * BOSS.soft));
  const head = await shoot(aimAt(0, 4.68, 0.34));
  assert.equal(head[0].part, 'head'); assert.equal(head[0].crit, false); assert.equal(head[0].dmg, Math.round(WEAPONS.ar.dmg * BOSS.soft));
  assert.equal((await shoot([1, 0, 0])).length, 0, 'a shot that doesn\'t cross him');
  assert.equal((await shoot(aimAt(3.5, 3, 0))).length, 0, 'past his shoulder');
  assert.ok(e.hp <= 100 && e.hp > 98, 'his room HP is the pool scaled to 100');
});

await t('an attack has a tell and a real window: the staple fires on its mark, at where you stood on the last clack', async () => {
  place(9); quiet(); B.want = 'staple'; B.next = 0;
  const marks = B.def.parts.marks.ot_staple, a0 = ev('act').length, h0 = ev('hit').filter((h) => h.target === 'me').length;
  await run(0.1);
  const act = ev('act')[a0];
  assert.ok(act, 'act reported'); assert.equal(act.clip, 'ot_staple'); assert.equal(act.move, 'staple'); assert.equal(act.boss, 'overtime_1'); assert.ok(Array.isArray(act.at));
  await run(marks.fire - 0.15); // the tell: nothing has left the stapler yet
  assert.equal(me.hp, 100, 'no damage before the fire mark'); assert.equal(B.shots.length, 0);
  await run(0.6);
  const hits = ev('hit').filter((h) => h.target === 'me').slice(h0);
  assert.equal(hits.length, 1, 'stood still: stapled'); assert.equal(hits[0].by, 'overtime_1'); assert.ok(me.hp < 100);
  // again, but you strafe on the second clack: it misses and stays in the floor
  await run(1.2); place(9); quiet(); B.want = 'staple'; B.next = 0;
  const f0 = ev('fx').length;
  await run(marks.clack2 + 0.05); me.pos = [BX + 4, 0.1, BZ + 9];
  await run(1);
  assert.equal(me.hp, 100, 'dodged'); assert.equal(ev('hit').filter((h) => h.target === 'me').length, h0 + 1);
  const fx = ev('fx').slice(f0);
  assert.equal(fx.length, 1, 'the miss is stuck somewhere'); assert.equal(fx[0].k, 'staple'); assert.ok(Math.hypot(fx[0].at[0] - BX, fx[0].at[2] - BZ - 9) < 5, 'in the floor just past where you were: ' + fx[0].at);
});

await t('the Overtime Slam: the ring gets you on the floor as it passes, not before the landing, not in the air', async () => {
  await run(1.2); place(6); quiet(); B.want = 'slam'; B.next = 0;
  const land = B.def.parts.marks.ot_slam.land;
  await run(land - 0.1);
  assert.equal(ev('act').at(-1).clip, 'ot_slam'); assert.equal(me.hp, 100, 'no damage before he lands');
  await run(0.9);
  assert.ok(me.hp < 100, 'on the floor when the ring passed');
  await run(1.5); place(6); quiet(); B.want = 'slam'; B.next = 0;
  await run(land - 0.1); me.pos[1] = 0.1 + 1.4; // a jump
  await run(1.2);
  assert.equal(me.hp, 100, 'in the air: it passed under you');
});

await t('the plate: armour first; at the health bar it comes off (one hit never eats past it), then the heart crits', async () => {
  await run(1.5); place(); quiet();
  for (let i = 0; i < 4 && B.plate; i++) hurt(900);
  assert.equal(B.hp, HEALTH); assert.equal(B.plate, false);
  const parts = ev('part');
  assert.equal(parts.length, 1); assert.deepEqual({ part: parts[0].part, state: parts[0].state, boss: parts[0].boss }, { part: 'plate', state: 'plate_off', boss: 'overtime_1' });
  const heart = await shoot(aimAt(0, 3.39, 0.98));
  assert.equal(heart[0].part, 'heart'); assert.equal(heart[0].crit, true); assert.equal(heart[0].dmg, Math.round(WEAPONS.ar.dmg * CRIT));
  me.pos = [BX, 0.1, BZ - 9]; // behind him: the clock face is on the other side
  const back = await shoot(aimAt(0, 3.39, 0.2));
  assert.equal(back[0].crit, false); assert.equal(back[0].part, 'body');
});

await t('phases at their thresholds: half HP = the coffee break; he can\'t be hurt while the cutscene holds him', async () => {
  place(); quiet();
  for (let i = 0; i < 4 && B.phase === 0; i++) hurt(900);
  assert.equal(B.phase, 1); assert.equal(B.hp, 2100, 'stopped at 50%');
  const ph = ev('phase');
  assert.equal(ph.length, 1); assert.deepEqual({ phase: ph[0].phase, name: ph[0].name, invuln: ph[0].invuln, boss: ph[0].boss }, { phase: 1, name: 'COFFEE BREAK', invuln: true, boss: 'overtime_1' });
  assert.equal(hurt(500), false, 'between phases: nothing lands');
  sim.msg({ t: 'sty', k: 'hold', all: true, on: true }); // the client's cutscene
  await run(2.5);
  assert.equal(B.state, 'cut'); assert.equal(hurt(500), false); assert.equal(B.hp, 2100);
  sim.msg({ t: 'sty', k: 'hold', all: true, on: false });
  await run(BOSS.cut + 0.2);
  assert.equal(B.state, 'rest'); assert.equal(ev('phase').length, 2); assert.equal(ev('phase')[1].invuln, false);
  // the break: he sits (the heart is lower) and does nothing; free crits
  const a0 = ev('act').length;
  await run(4);
  assert.equal(ev('act').length, a0, 'no attacks on his break');
  const sit = await shoot(aimAt(0, 3.39 - 1.05, 0.98));
  assert.equal(sit[0].part, 'heart'); assert.equal(sit[0].crit, true);
  for (let i = 0; i < 3 && B.phase === 1; i++) hurt(900);
  assert.equal(B.phase, 2); assert.equal(B.hp, 1890, 'stopped at 45%');
  assert.deepEqual({ phase: ev('phase')[2].phase, name: ev('phase')[2].name }, { phase: 2, name: 'PUNCHING IN' });
  await run(BOSS.cut + 0.2);
  assert.equal(B.state, 'fight');
});

await t('the break also ends on the clock (15 s), whatever his HP', async () => {
  const s2 = createSim({ send: () => {}, save: newSave(0, 'story_test') });
  s2.msg({ t: 'join', name: 'tester2' });
  for (let i = 0; i < 100 && !s2.ref; i++) await sleep(50);
  s2.msg({ t: 'sty', k: 'spawn', kind: 'overtime_1', at: [BX, 0.1, BZ] });
  const e2 = s2.refEnemies()[0], B2 = e2.sk.b;
  for (let i = 0; i < 6 && B2.phase === 0; i++) s2.ref.room.damage(e2, 900, s2.ref.me, 'ar');
  for (let i = 0; i < 20 * 17 && B2.phase === 1; i++) { s2.tick(0.05); if (i % 40 === 0) await sleep(0); }
  assert.equal(B2.phase, 2); assert.equal(B2.hp, 2100);
});

await t('Punch In: the slot is a crit while it\'s open; the grab only gets you in front of him and close', async () => {
  place(4); quiet(); B.want = 'punchin'; B.next = 0;
  const m = B.def.parts.marks.ot_punchin;
  await run(m.slotOpen + 0.15);
  assert.equal(ev('act').at(-1).clip, 'ot_punchin'); assert.equal(me.hp, 100);
  const slot = await shoot(aimAt(0, 2.87, 0.85));
  assert.ok(slot[0].crit, 'into the open slot: ' + JSON.stringify(slot[0]));
  await run(m.grab - m.slotOpen + 0.1);
  assert.ok(me.hp < 100, 'grabbed');
  await run(2.5); place(4); quiet(); B.want = 'punchin'; B.next = 0;
  await run(m.grab - 0.2); me.pos = [BX + 6, 0.1, BZ + 1]; // a dash to the side after he commits
  await run(0.5);
  assert.equal(me.hp, 100, 'dodged the grab');
});

await t('the end: at 0 he is beaten, not killed. one kill event for the quest (boss id), he leaves the room, you can\'t farm him', async () => {
  await run(2.5); place(); quiet();
  const k0 = ev('kill').length;
  for (let i = 0; i < 8 && B.state !== 'done'; i++) hurt(900);
  assert.equal(B.hp, 0); assert.equal(B.state, 'done'); assert.ok(e.alive, 'alive in the room'); assert.equal(hurt(900), false);
  const ks = ev('kill').slice(k0);
  assert.equal(ks.length, 1); assert.equal(ks[0].boss, 'overtime_1'); assert.equal(ks[0].kind, 'overtime_1'); assert.equal(ks[0].by, 'me'); assert.equal(ks[0].defeat, true);
  assert.ok(!out.some((o) => o.t === 'kill' && o.v === e.id), 'no kill-feed death');
  await run(0.2);
  assert.equal(sim.refEnemies().length, 0, 'gone from the room');
  assert.ok(out.some((o) => o.t === 'sty' && o.k === 'boss' && o.on === false && o.id === 'overtime_1'));
  assert.equal(ev('phase').length, 4); assert.equal(ev('part').length, 1);
});

await t('safety: junk boss defs and junk hits do nothing; a plain enemy is still a plain enemy', async () => {
  const room = R.room;
  const j = room.storySpawn({ kind: 'x', hp: 50, boss: { id: 'x', hp: 'lots', phases: [] } }, [BX, 0.1, BZ]);
  assert.equal(j.sk.b, undefined); assert.equal(j.sk.boss, false);
  room.storyDespawn(j);
  sim.msg({ t: 'sty', k: 'spawn', kind: 'overtime_1', at: [BX, 0.1, BZ] });
  e = sim.refEnemies()[0]; B = e.sk.b; place(); quiet();
  for (const d of [null, 'x', [1, 2], [NaN, 0, 1], [0, 0, 0], [1e9, 0, 0]]) R.room.handle(me, { t: 'hit', to: e.id, w: 'ar', n: 1, d });
  assert.equal(hurt(NaN), false); assert.equal(hurt(-5), false); assert.equal(hurt(Infinity), false);
  assert.equal(B.hp, 4200);
  hurt(1e6); assert.equal(B.hp, 4200 - BOSS.maxHit, 'one hit is capped');
  room.kill(e, me, 'void'); assert.ok(e.alive, 'the room can\'t kill him');
  sim.msg({ t: 'sty', k: 'despawn', id: 'overtime_1' });
  assert.equal(sim.refEnemies().length, 0);
});
console.log(n, 'passed');
process.exit(0);
