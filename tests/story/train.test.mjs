// node tests/story/train.test.mjs : REVENUE PROTECTION, the train fight, in the combat referee (server/storytrain.js
// through shared/story/refsys.js) from its design data: spawn, THE GAP closing while an arm grips and opening on a
// sever, a sweeper's damage window and its dodges, the four-severs flinch, phases and the hold round the middle scene,
// the plate stages in order, the Inspector, the defeat, the fail at 0 m, and the Blood Drive (cost, rate, story-only)
import assert from 'node:assert/strict';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/invsys.js';
import '../../shared/story/solohost.js';
import '../../shared/story/refsys.js';
import { newSave } from '../../shared/story/save.js';
import { BOSSES } from '../../shared/story/content/bosses.js';
import { WEAPONS, FLAGS, ORDER, SLOTS, validLoadout } from '../../shared/weapons.js';
import { LADDER } from '../../shared/modes.js';
import { RP, ARENA, TRAIN, armPose, plateAt, offTrain, geoFrom, GEO0 } from '../../shared/story/train.js';
import { cleanTrain } from '../../server/storytrain.js';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

const ID = 'revenue_protection_1', D = BOSSES[ID], HEALTH = D.layers.find((l) => l.bar === 'health').of, W = WEAPONS.blooddrive;
async function boot() {
  const out = [], sim = createSim({ send: (o) => out.push(o), save: newSave(0, TRAIN.id) });
  sim.dev = true; sim.msg({ t: 'join', name: 'tester' });
  for (let i = 0; i < 100 && !sim.ref; i++) await sleep(50);
  assert.ok(sim.ref, 'room up: ' + (sim.refOff || ''));
  const ev = (type) => out.filter((o) => o.t === 'sty' && o.k === 'combat' && o.ev.type === type).map((o) => o.ev);
  const run = async (secs) => { for (let i = 0; i < Math.round(secs * 20); i++) { sim.tick(0.05); await sleep(0); } };
  return { out, sim, ev, run, R: sim.ref, me: sim.ref.me };
}
const { out, sim, ev, run, R, me } = await boot();
let e, B;
const dev = (o) => sim.msg({ t: 'sty', k: 'bossdev', ...o });
const stand = (p = [0, 1.0, 4.5]) => { me.pos = p.slice(); me.hp = 100; me.alive = true; me.spawnT = 0; me.f = 0; };
const eye = () => [me.pos[0], me.pos[1] + 1.6, me.pos[2]];
const aim = (p) => { const o = eye(), d = p.map((v, i) => v - o[i]), l = Math.hypot(...d); return d.map((v) => v / l); };
// one Blood Drive bolt at a world point, the ring already up to speed (the spin-up and the rate have their own test)
const bolt = (p) => { const a = ev('hit').length; me.bd = { ...(me.bd || { key: '', n: 0, dryT: 0 }), on: Date.now() - 5000, last: Date.now(), tok: 3, tokT: Date.now() }; R.room.handle(me, { t: 'fire', w: 'blooddrive', o: eye(), d: aim(p) }); return ev('hit').slice(a).filter((h) => h.target === ID); };
const face = (x, y) => [x, ARENA.cy + y, B.def.geo.faceZ - B.gap]; // a spot on the mask's face (its own x, y)
const knot = (a) => armPose(B.def.geo, a, B.gap).wrist;
const quiet = () => { B.calm = true; B.arms.length = 0; B.severs.length = 0; };
const dmgTo = (pct) => { for (let i = 0; i < 40 && B.hp > D.hp * pct / 100 + 0.5 && B.state === 'fight'; i++) dev({ dmg: Math.min(1000, B.hp - D.hp * pct / 100), i: i % 8 }); };

await t('the arena: the last two cars in the bore, a story map the referee loads; you start on the wagon', async () => {
  assert.equal(sim.zone, TRAIN.id); assert.equal(R.room.cfg.map, TRAIN.id); assert.deepEqual(me.pos, TRAIN.spawn);
  assert.ok(R.room.boxes.length > 15); assert.equal(offTrain([0, 1.0, 4.5]), false); assert.equal(offTrain([0, 1.3, 12]), false);
  assert.equal(offTrain([3, 0.9, 4]), true, 'over the side'); assert.equal(offTrain([0, 0.1, -3]), true, 'on the track behind'); assert.equal(offTrain([2.4, 2.2, 4]), false, 'mid jump is not off yet');
});

await t('spawn: the boss from content/bosses.js, its real pool, one at a time, the client is told everything', async () => {
  sim.msg({ t: 'sty', k: 'spawn', kind: ID, id: ID, at: [0, 3, -30], hp: 5, n: 3 });
  sim.msg({ t: 'sty', k: 'spawn', kind: ID, id: ID, at: [0, 3, -30] }); // already here
  const es = sim.refEnemies();
  assert.equal(es.length, 1); e = es[0]; B = e.sk.b;
  assert.ok(B && B.train, 'the train fight'); assert.equal(e.sk.max, D.hp); assert.equal(B.hp, 5000); assert.equal(e.name, 'REVENUE PROTECTION');
  assert.deepEqual(B.def.phases.map((p) => [p.name, p.to]), [['TICKETS, PLEASE', 60], ['PENALTY FARE', 25], ['END OF THE LINE', 0]]);
  assert.equal(B.def.health, HEALTH); assert.deepEqual(B.def.crit, { knot: 2, eye: 2, insp: 2.5 });
  assert.equal(B.def.geo.sockets.length, 12); assert.equal(B.def.geo.crack.length, 25); assert.deepEqual(B.def.geo.insp.crit, [0, -2.404, -0.721]);
  const on = out.find((o) => o.t === 'sty' && o.k === 'boss' && o.on);
  assert.deepEqual({ id: on.id, pid: on.pid, hp: on.hp, max: on.max, health: on.health, name: on.name, phase: on.phase, who: on.who }, { id: ID, pid: e.id, hp: 5000, max: 5000, health: HEALTH, name: 'REVENUE PROTECTION', phase: 'TICKETS, PLEASE', who: 'revenue_protection' });
  B.calm = true; await run(0.2);
  const st = ev('state')[0];
  assert.ok(st, 'state sent'); assert.equal(st.boss, ID); assert.equal(st.gap, RP.gap.start); assert.equal(st.phase, 0); assert.deepEqual(st.plates, Array(12).fill(0)); assert.equal(st.marrow, false);
  assert.deepEqual(e.pos, [0, ARENA.cy, -30], 'it sits in the middle of the mask, THE GAP behind you');
});

await t('THE GAP: it closes 1 m/s for every arm that has the rail, not before; a sever opens it and pays blood back', async () => {
  stand(); quiet(); B.gap = 30;
  dev({ want: 'grab' });
  const a = B.arms[0]; assert.ok(a && a.k === 'grab' && a.st === 'reach'); assert.equal(ev('arm').at(-1).st, 'reach'); assert.equal(ev('arm').at(-1).dur, RP.grab.reach);
  await run(RP.grab.reach - 0.3);
  assert.equal(B.gap, 30, 'still reaching: nothing closes'); assert.equal(a.st, 'reach');
  await run(0.5); assert.equal(a.st, 'grip'); assert.equal(ev('arm').at(-1).st, 'grip');
  const g0 = B.gap; await run(2);
  assert.ok(Math.abs(g0 - B.gap - 2) < 0.11, '1 m/s: ' + (g0 - B.gap));
  const gm = ev('gap').at(-1); assert.equal(gm.rate, -1); assert.ok(Math.abs(gm.gap - B.gap) < 0.4); assert.ok(gm.jack > 0.9);
  // the rope does little; the wrist knot is the weak point
  const P = armPose(B.def.geo, a, B.gap), mid = P.pts[Math.floor(P.pts.length / 2)];
  const rope = bolt(mid); assert.equal(rope[0].part, 'rope'); assert.equal(rope[0].arm, a.id); assert.equal(rope[0].crit, false); assert.equal(rope[0].dmg, Math.round(W.dmg * RP.arm.rope));
  dev({ want: 'grab' }); dev({ grip: true }); await run(1.1);
  assert.ok(Math.abs(g0 - 2 - B.gap - 2.2) < 0.25, 'two arms: 2 m/s');
  me.hp = 60; const gap1 = B.gap, hs = [];
  for (let i = 0; i < 12 && a.st !== 'cut'; i++) hs.push(...bolt(knot(a)));
  assert.equal(hs[0].part, 'knot'); assert.equal(hs[0].crit, true); assert.equal(hs[0].dmg, W.dmg * 2);
  assert.equal(a.st, 'cut', 'severed'); assert.ok(hs.length <= 9, 'nine bolts at most (fewer with the bloom): ' + hs.length);
  const cut = ev('arm').filter((x) => x.id === a.id).at(-1);
  assert.equal(cut.st, 'cut'); assert.equal(cut.blood, RP.arm.blood, 'blood back');
  assert.ok(Math.abs(B.gap - gap1 - RP.gap.sever) < 0.01, 'the gap opens');
  assert.equal(me.hp, 60 - (hs.length + 0) * W.cost + RP.arm.blood, '2 HP a bolt, 20 back');
  await run(RP.arm.cut + 0.2);
  assert.ok(!B.arms.includes(a), 'the stump is gone'); assert.equal(ev('arm').filter((x) => x.id === a.id).at(-1).st, 'gone');
});

await t('a sweeper: a tell, then a real window as the bar passes you; jump the knee-high one, slide under the head-high one', async () => {
  const pass = (RP.sweep.tell + (4.5 - RP.sweep.z0) / RP.sweep.speed), go = async (hi, mid) => { stand(); quiet(); dev({ want: 'sweep', hi, side: 1 }); await run(RP.sweep.tell - 0.15); assert.equal(me.hp, 100, 'the tell: no damage yet'); assert.equal(B.arms[0].st, 'tell'); mid(); await run(pass - RP.sweep.tell + 0.4); };
  const s0 = ev('swept').length;
  await go(false, () => {});
  assert.equal(me.hp, 100 - RP.sweep.dmg, 'stood on the deck: swept'); assert.equal(ev('swept').length, s0 + 1); assert.ok(out.some((o) => o.t === 'kb' && o.w === 'sweeper'), 'and thrown');
  assert.equal(ev('hit').filter((h) => h.target === 'me').at(-1).by, ID);
  await go(false, () => { me.pos[1] = 1.0 + 0.8; }); assert.equal(me.hp, 100, 'jumped it');
  await go(true, () => {}); assert.equal(me.hp, 100 - RP.sweep.dmg, 'head height, standing: swept');
  await go(true, () => { me.f = FLAGS.SLIDE; }); assert.equal(me.hp, 100, 'slid under it');
  await go(true, () => { me.f = FLAGS.CROUCH; }); assert.equal(me.hp, 100, 'ducked it');
  await go(false, () => { me.pos = [0, 1.3, 14]; }); assert.equal(me.hp, 100, 'the bar is not at the flatbed yet'); await run(0.8); assert.equal(me.hp, 100 - RP.sweep.dmg, 'it runs the whole deck');
  assert.equal(ev('swept').length, s0 + 3);
  await run(RP.arm.back + 0.6); assert.equal(B.arms.length, 0, 'it leaves by itself');
});

await t('a snatcher: it has you for six seconds; shoot it off, or it hurts and THE GAP is gone', async () => {
  stand(); quiet(); B.gap = 30; dev({ want: 'snatch' });
  assert.equal(B.arms.length, 1, 'one at a time in phase 1'); const a = B.arms[0];
  await run(RP.snatch.reach + 0.2); assert.equal(a.st, 'hold'); assert.equal(me.hp, 100);
  assert.ok(Math.abs(a.tgt[1] - (me.pos[1] + RP.snatch.up)) < 0.01, 'its wrist is over you');
  await run(RP.snatch.hold - 0.5); assert.equal(me.hp, 100, 'not yet');
  await run(0.6);
  assert.equal(me.hp, 100 - RP.snatch.dmg); assert.equal(B.gap, 30 - RP.snatch.gap); assert.equal(ev('snatched').length, 1); assert.equal(a.st, 'back');
  await run(1.3); stand(); dev({ want: 'snatch' }); const a2 = B.arms[0];
  await run(RP.snatch.reach + 0.5);
  for (let i = 0; i < 12 && a2.st !== 'cut'; i++) bolt(knot(a2));
  assert.equal(a2.st, 'cut'); await run(RP.snatch.hold); assert.equal(ev('snatched').length, 1, 'shot off in time');
});

await t('phase 1: the mask shrugs bolts off; four severs inside ten seconds and it flinches: the eyes open, and then it can be hurt', async () => {
  stand(); quiet(); B.gap = 10;
  const s0 = ev('shrug').length;
  assert.equal(bolt(face(1.26, 3.05)).length, 0, 'a plate'); assert.equal(bolt(face(1.25, 0.7)).length, 0, 'a shut eye housing'); assert.equal(B.hp, 5000);
  assert.ok(ev('shrug').length > s0, 'the client hears the tink');
  assert.equal(bolt([20, 3, -10]).length, 0, 'into the wall');
  for (let i = 0; i < 3; i++) dev({ want: 'grab' });
  dev({ sever: true }); assert.equal(B.severs.length, 3); assert.equal(ev('flinch').length, 0, 'three is not four');
  await run(1.5); dev({ want: 'grab' }); dev({ sever: true });
  const f = ev('flinch'); assert.equal(f.length, 1); assert.equal(f[0].open, RP.flinch.open);
  assert.ok(Math.abs(B.gap - (10 + 4 * RP.gap.sever + RP.gap.flinch)) < 0.01, 'severs and the flinch open the gap');
  const hit = bolt(face(1.25, 0.7));
  assert.equal(hit.length, 1); assert.equal(hit[0].part, 'eye'); assert.equal(hit[0].crit, true); assert.equal(hit[0].dmg, W.dmg * 2); assert.equal(hit[0].hp, 5000 - W.dmg * 2); assert.equal(hit[0].by, 'me'); assert.equal(hit[0].weapon, 'blooddrive');
  assert.equal(bolt(face(-1.25, 0.7))[0].part, 'eye', 'the right one too'); assert.equal(bolt(face(1.26, 3.05)).length, 0, 'the plates still shrug');
  await run(RP.flinch.open + 0.2);
  assert.equal(bolt(face(1.25, 0.7)).length, 0, 'shut again');
  // severs too far apart are not a flinch
  B.severs.length = 0;
  for (let i = 0; i < 4; i++) { dev({ want: 'grab' }); dev({ sever: true }); await run(3.6); }
  assert.equal(ev('flinch').length, 1);
  assert.ok(e.hp <= 100 && e.hp > 97, 'its room HP is the pool scaled to 100');
});

await t('phase 1 ends at 60%: the event for the middle scene, THE GAP at 6 m, and it holds until the scene lets go', async () => {
  stand(); quiet();
  for (let i = 0; i < 6 && B.phase === 0; i++) dev({ dmg: 900, part: 'eye' });
  assert.equal(B.phase, 1); assert.equal(B.hp, 3000, 'stopped at 60%'); assert.equal(B.state, 'cut'); assert.equal(B.gap, RP.gap.moment);
  const ph = ev('phase');
  assert.equal(ph.length, 1); assert.deepEqual({ phase: ph[0].phase, name: ph[0].name, invuln: ph[0].invuln, boss: ph[0].boss }, { phase: 1, name: 'PENALTY FARE', invuln: true, boss: ID });
  assert.equal(ev('gap').at(-1).gap, RP.gap.moment);
  sim.msg({ t: 'sty', k: 'hold', all: true, on: true }); // the client's scene (mo_carry_the_bit_that_works)
  dev({ dmg: 500 }); dev({ want: 'grab' });
  await run(3);
  assert.equal(B.state, 'cut'); assert.equal(B.hp, 3000); assert.equal(B.gap, RP.gap.moment, 'it holds'); assert.equal(B.arms.length, 0); assert.equal(ev('stage').length, 0);
  sim.msg({ t: 'sty', k: 'hold', all: true, on: false });
  await run(RP.cut + 0.2);
  assert.equal(B.state, 'fight'); assert.equal(ev('phase').length, 2); assert.equal(ev('phase')[1].invuln, false);
  assert.deepEqual(ev('stage').map((s) => s.name), ['hairline'], 'phase 2 opens on the first break stage');
  assert.equal(B.marrow, true, 'you have Jack\'s marrow now');
});

await t('phase 2: plates take it, craze at half and fall; the stages come in order: hairline, the left eye, the smile', async () => {
  stand(); quiet(); B.gap = 20;
  const p5 = face(1.26, 3.05), i = plateAt(1.26, 3.05); assert.equal(i, 5);
  const h = bolt(p5); assert.equal(h[0].part, 'plate'); assert.equal(h[0].dmg, W.dmg); assert.equal(me.hp, 100, 'free while it spins');
  dev({ dmg: RP.mask.plateHp / 2, part: 'plate', i }); assert.deepEqual(ev('plate').at(-1), { ...ev('plate').at(-1), i, st: 1 }, 'crazed');
  dev({ dmg: RP.mask.plateHp / 2, part: 'plate', i }); assert.equal(ev('plate').at(-1).st, 2, 'it falls'); assert.equal(B.plates[i].st, 2);
  const hole = bolt(p5); assert.equal(hole[0].part, 'hole'); assert.equal(hole[0].dmg, W.dmg * RP.mask.soft);
  assert.equal(bolt(face(1.25, 0.7))[0].part, 'lamp', 'the left eye is still a lamp');
  dmgTo(45); assert.deepEqual(ev('stage').map((s) => s.name), ['hairline', 'left_eye']);
  const le = bolt(face(1.25, 0.7)); assert.equal(le[0].part, 'eye'); assert.equal(le[0].crit, true, 'blown: a way in');
  assert.equal(bolt(face(-1.25, 0.7))[0].part, 'lamp', 'the right one is not');
  assert.equal(bolt(face(0, -2.4))[0].part, 'plate', 'the mouth is still shut');
  dmgTo(30); assert.deepEqual(ev('stage').map((s) => [s.stage, s.name]), [[1, 'hairline'], [2, 'left_eye'], [3, 'smile']]);
  assert.equal(B.plates[9].st, 2); assert.equal(B.plates[10].st, 2); assert.ok(B.smile);
  assert.equal(bolt(face(2.5, -3))[0].part, 'mass', 'the lower third is off: the mouth'); assert.equal(B.phase, 1);
  // two snatchers at once from here
  dev({ want: 'snatch' }); assert.equal(B.arms.filter((a) => a.k === 'snatch').length, 2); quiet();
});

await t('phase 3: END OF THE LINE at 25%; the Inspector is the crit spot, everything else barely counts; it lunges', async () => {
  dmgTo(25);
  assert.equal(B.phase, 2); assert.equal(B.hp, HEALTH, 'the armour layer is gone: his bar'); assert.equal(B.state, 'cut');
  assert.deepEqual({ phase: ev('phase')[2].phase, name: ev('phase')[2].name, invuln: true }, { phase: 2, name: 'END OF THE LINE', invuln: true });
  assert.equal(bolt(face(0, -2.4)).length, 0, 'between phases nothing lands');
  await run(RP.cut + 0.2); assert.equal(B.state, 'fight'); quiet(); stand(); B.gap = 14;
  const I = B.def.geo.insp, crit = bolt([I.crit[0], ARENA.cy + I.crit[1], I.crit[2] - B.gap]);
  assert.equal(crit[0].part, 'insp'); assert.equal(crit[0].crit, true); assert.equal(crit[0].dmg, W.dmg * 2.5);
  assert.equal(bolt([I.head.c[0], ARENA.cy + I.head.c[1] + 0.1, I.head.c[2] - B.gap])[0].part, 'inspbody');
  const far = bolt(face(-1.3, 3)); assert.equal(far[0].part, 'plate'); assert.equal(far[0].dmg, Math.round(W.dmg * RP.mask.far));
  // the lunge: a tell, then it takes ground; inside 6 m it bites whoever is still on the wagon
  B.gap = 9; dev({ want: 'lunge' }); B.calm = false; B.nextArm = Infinity; await run(0.15); B.calm = true;
  assert.equal(ev('lunge').at(-1).st, 'tell'); await run(RP.lunge.tell - 0.4); assert.equal(B.gap, 9); assert.equal(me.hp, 100);
  await run(0.5);
  assert.equal(B.gap, 9 - RP.lunge.gap); assert.equal(ev('lunge').at(-1).st, 'hit'); assert.equal(me.hp, 100 - RP.lunge.dmg, 'on the wagon: bitten');
  stand([0, 1.3, 12]); B.gap = 9; dev({ want: 'lunge' }); B.calm = false; B.nextArm = Infinity; await run(RP.lunge.tell + 0.3); B.calm = true;
  assert.equal(me.hp, 100, 'on the flatbed: it misses'); assert.equal(ev('lunge').at(-1).bit, 0);
});

await t('the finish: at 0 it is beaten, not killed. one kill event for the quest, it leaves the room, nothing more lands', async () => {
  stand(); quiet(); const k0 = ev('kill').length;
  for (let i = 0; i < 6 && B.state !== 'done'; i++) dev({ dmg: 900 });
  if (B.state !== 'done') for (let i = 0; i < 6 && B.state !== 'done'; i++) R.room.damage(e, 900, me, 'ar');
  assert.equal(B.hp, 0); assert.equal(B.state, 'done'); assert.ok(e.alive, 'alive in the room');
  const ks = ev('kill').slice(k0);
  assert.equal(ks.length, 1); assert.deepEqual({ boss: ks[0].boss, kind: ks[0].kind, by: ks[0].by, defeat: ks[0].defeat }, { boss: ID, kind: ID, by: 'me', defeat: true });
  assert.ok(!out.some((o) => o.t === 'kill' && o.v === e.id), 'no kill-feed death');
  await run(0.2);
  assert.equal(sim.refEnemies().length, 0, 'gone from the room'); assert.ok(out.some((o) => o.t === 'sty' && o.k === 'boss' && o.on === false && o.id === ID));
  assert.equal(ev('phase').length, 4); assert.equal(ev('fail').length, 0);
});

await t('the fail: THE GAP at 0 m and it has you; the fight starts again from the phase\'s beginning. the track puts you back', async () => {
  const S = await boot(); S.sim.msg({ t: 'sty', k: 'spawn', kind: ID, id: ID, at: [0, 3, -30] });
  const e2 = S.sim.refEnemies()[0], B2 = e2.sk.b, m2 = S.me; B2.calm = true; m2.spawnT = 0; m2.pos = [0, 1, 4.5];
  await S.run(0.2);
  // off the train: 25 and back on the deck, once
  m2.pos = [3, 0.3, 4]; await S.run(0.3);
  assert.equal(m2.hp, 100 - RP.off.dmg); assert.deepEqual(m2.pos, ARENA.back); assert.equal(S.ev('off').length, 1);
  assert.ok(S.out.some((o) => o.t === 'tp'), 'the client is moved');
  B2.hp = 4000; B2.plates[3].st = 1; // (no checkpoint saves this: phase 1 starts whole)
  S.sim.msg({ t: 'sty', k: 'bossdev', want: 'grab' }); S.sim.msg({ t: 'sty', k: 'bossdev', grip: true }); S.sim.msg({ t: 'sty', k: 'bossdev', gap: 0.6 });
  await S.run(1);
  const f = S.ev('fail'); assert.equal(f.length, 1); assert.equal(f[0].why, 'gap'); assert.equal(f[0].line, 'fare evaded. briefly.'); assert.equal(B2.state, 'failed');
  assert.equal(m2.alive, false, 'caught'); assert.ok(S.ev('down').some((d) => d.who === 'me' && d.by === ID));
  assert.equal(B2.arms.length, 0);
  await S.run(RP.fail + 0.5); assert.equal(B2.state, 'failed', 'it waits for you');
  m2.alive = true; m2.hp = 100; m2.pos = ARENA.back.slice(); await S.run(0.2);
  assert.equal(B2.state, 'fight'); assert.equal(B2.gap, RP.gap.start); assert.equal(B2.hp, 5000); assert.equal(B2.plates[3].st, 0); assert.equal(S.ev('reset').length, 1); assert.equal(S.ev('state').length, 2);
  // Jack's bar: phase 1 also ends when he can't hold the rail any more, with the mask's bar dropping to its line
  B2.jack = RP.jack - 0.3; B2.calm = false; B2.nextArm = Infinity; await S.run(0.5);
  assert.equal(B2.phase, 1); assert.equal(B2.hp, 3000); assert.equal(S.ev('phase')[0].name, 'PENALTY FARE');
  // dying any other way is the same fail; phase 2 restarts as phase 2, at the retry distance
  await S.run(RP.cut + 0.2); B2.calm = true; B2.hp = 2500; m2.alive = false; await S.run(0.2);
  assert.equal(S.ev('fail').at(-1).why, 'dead'); m2.alive = true; m2.hp = 100; await S.run(RP.fail + 0.3);
  assert.equal(B2.phase, 1); assert.equal(B2.hp, 3000); assert.equal(B2.gap, RP.gap.retry); assert.equal(B2.marrow, true);
});

await t('the Blood Drive: a spin-up, 14 a second and no faster, 2 HP a bolt, dry at your last blood, walls stop it, free on Jack\'s marrow', async () => {
  const S = await boot(), m2 = S.me, room = S.R.room; m2.spawnT = 0; m2.pos = [0, 1.3, 12];
  S.sim.msg({ t: 'sty', k: 'spawn', kind: 'dummy', id: 'd1', at: [0, 1.3, 15], hp: 400 });
  const d1 = S.sim.refEnemies()[0]; d1.pos = [0, 1.3, 15]; d1.sk.hold = true;
  const fire = (d = [0, 0, 1]) => room.handle(m2, { t: 'fire', w: 'blooddrive', o: [0, 2.9, 12], d }), hits = () => S.ev('hit').filter((h) => h.target === 'd1');
  fire(); fire(); assert.equal(hits().length, 0, 'the first pulls are the wind-up'); assert.equal(m2.hp, 100);
  await sleep(300); fire(); assert.equal(hits().length, 0, 'still winding up');
  await sleep(W.spin * 1000 - 250);
  for (let i = 0; i < 40; i++) fire(); // a flood
  assert.ok(hits().length >= 1 && hits().length <= 3, 'a flood buys a few bolts, not forty: ' + hits().length);
  assert.equal(m2.hp, 100 - hits().length * W.cost); assert.equal(hits()[0].dmg, W.dmg); assert.equal(hits()[0].weapon, 'blooddrive');
  const h0 = hits().length; await sleep(1000); for (let i = 0; i < 40; i++) fire();
  assert.ok(hits().length - h0 <= 3, 'the bucket never banks more than three');
  // the real rate over a second of held fire
  const h1 = hits().length, t0 = Date.now(); while (Date.now() - t0 < 1000) { fire(); await sleep(15); }
  const got = hits().length - h1; assert.ok(got >= 9 && got <= 19, 'about 14 a second: ' + got);
  assert.ok(S.out.some((o) => o.t === 'bcross' && o.k === 'stick'), 'the sixth bolt in the same target blooms a cross');
  // a wall, the range, junk
  const h2 = hits().length; m2.bd.tok = 3; fire([0, 0, -1]); fire([1, 0, 0]); assert.equal(hits().length, h2, 'not through the air or the wall');
  for (const d of [null, 'x', [1, 2], [NaN, 0, 1], [0, 0, 0], [1e9, 0, 0]]) { m2.bd.tok = 3; room.handle(m2, { t: 'fire', w: 'blooddrive', o: [0, 2.9, 12], d }); }
  for (const o of [null, 'x', [NaN, 0, 0], [0, 900, 0]]) { m2.bd.tok = 3; m2.hp = 100; room.handle(m2, { t: 'fire', w: 'blooddrive', o, d: [1, 0, 0] }); }
  assert.equal(hits().length, h2); room.handle(m2, { t: 'fire', w: 'blooddrive', k: {} }); room.handle(m2, { t: 'fire', w: 'blooddrive', k: 'stop' }); assert.equal(m2.bd.on, 0);
  // out of blood: it runs dry, it never takes your last HP
  m2.bd.on = Date.now() - 5000; m2.bd.last = Date.now(); m2.bd.tok = 3; m2.hp = 2; fire();
  assert.equal(m2.hp, 2); assert.ok(S.out.some((o) => o.t === 'bdrive' && o.k === 'dry'));
  // a kill pays blood back; with the marrow's flag it costs nothing
  d1.hp = 1; m2.hp = 50; m2.bd.tok = 3; m2.bd.last = Date.now(); fire(); assert.equal(d1.alive, false); assert.equal(m2.hp, 50 - W.cost + W.heal);
  S.sim.state.flags.jack_marrow_taken = true; m2.bd.tok = 3; m2.bd.last = Date.now(); m2.hp = 50; fire(); assert.equal(m2.hp, 50, 'free');
  delete S.sim.state.flags.jack_marrow_taken;
  // dead men don't fire
  m2.alive = false; m2.bd.tok = 3; fire(); m2.alive = true;
});

await t('story-only: no slot, no loadout, no ladder; a normal room ignores it, and a normal hit there is still a normal hit', async () => {
  assert.equal(W.slot, null); assert.ok(!SLOTS.includes(W.slot)); assert.ok(!ORDER.includes('blooddrive')); assert.ok(!LADDER.includes('blooddrive'));
  for (const s of SLOTS) assert.notEqual(validLoadout({ [s]: 'blooddrive' })[s], 'blooddrive');
  const { ROYALE_LOOT, LOOT } = await import('../../shared/royale.js').catch(() => ({})); assert.ok(!JSON.stringify(ROYALE_LOOT || LOOT || {}).includes('blooddrive'));
  const { Room } = await import('../../server/room.js');
  const room = new Room('plain', 'bots'), sent = [];
  const p = room.addHuman({ readyState: 1, send: (x) => sent.push(JSON.parse(x)) }, { t: 'join', name: 'p', mode: 'bots', primary: 'blooddrive' }), b = room.addBot({});
  assert.equal(b.sk, undefined); assert.notEqual(p.w, 'blooddrive'); assert.notEqual(b.w, 'blooddrive');
  p.pos = [0, 0.1, 0]; p.spawnT = 0; b.pos = [0, 0.1, -6]; const n0 = sent.length;
  for (const k of [undefined, 'spin', 'stop']) room.handle(p, { t: 'fire', w: 'blooddrive', k, o: [0, 1.7, 0], d: [0, 0, -1] });
  await sleep(700); for (let i = 0; i < 5; i++) room.handle(p, { t: 'fire', w: 'blooddrive', o: [0, 1.7, 0], d: [0, 0, -1] });
  room.handle(p, { t: 'hit', to: b.id, w: 'blooddrive', n: 1, h: 1, d: [0, 0, -1] });
  assert.equal(b.hp, 100); assert.equal(p.hp, 100); assert.equal(p.bd, undefined); assert.equal(sent.length, n0, 'nothing went out');
  p.w = 'ar'; room.handle(p, { t: 'hit', to: b.id, w: 'ar', n: 1, h: 1, d: [0, 0, -1] });
  assert.equal(b.hp, 100 - WEAPONS.ar.dmg * WEAPONS.ar.head); assert.ok(sent.some((m) => m.t === 'dmg' && m.to === b.id && m.hs === true));
  room.kill(b, p, 'ar'); assert.equal(b.alive, false);
});

await t('safety: junk defs, junk dev messages and junk hits do nothing; any other gun is judged by the same ray; overtime is still overtime', async () => {
  assert.equal(cleanTrain(null), null); assert.equal(cleanTrain({ id: 'x', hp: 'lots', phases: [], train: {} }), null);
  assert.equal(cleanTrain({ id: 'x', hp: 100, phases: [{ to: 60 }, { to: 70 }, { to: 0 }], train: {} }), null, 'phases must go down');
  const c = cleanTrain({ id: 'x', hp: 100, phases: [{ to: 60 }, { to: 25 }, { to: 9 }], train: { parts: { markers: { sockets: 'no', inspector: { crit: [NaN, 0, 0] } } }, crit: { knot: 1e9, eye: 'x' } } });
  assert.deepEqual(c.crit, { knot: 10, eye: 2, insp: 2.5 }); assert.deepEqual(c.geo, GEO0, 'a broken parts file falls back whole'); assert.equal(c.phases[2].to, 0);
  assert.deepEqual(geoFrom({ markers: { smile_crack: [[0, 0]] } }).crack, GEO0.crack);
  const j = R.room.storySpawn({ kind: 'x', hp: 50, boss: { id: 'x', hp: 5, phases: [], train: {} } }, [0, 1.3, 12]);
  assert.equal(j.sk.b, undefined); assert.equal(j.sk.boss, false); R.room.storyDespawn(j);
  sim.msg({ t: 'sty', k: 'spawn', kind: ID, id: ID, at: [0, 3, -30] });
  e = sim.refEnemies()[0]; B = e.sk.b; stand(); quiet(); await run(0.2);
  for (const m of [{ want: {} }, { want: 'slam' }, { gap: 'x' }, { gap: NaN }, { dmg: -5 }, { dmg: 'x' }, { calm: 1 }, { sever: 1 }, { grip: 'y' }, { part: '../x', dmg: 5 }]) dev(m);
  assert.equal(B.hp, 5000); assert.equal(B.arms.length, 0); assert.equal(B.gap, 30); assert.equal(B.calm, true);
  dev({ gap: 1e9 }); assert.equal(B.gap, RP.gap.max);
  dev({ pin: true }); dev({ want: 'grab' }); dev({ grip: true }); await run(1); assert.equal(B.gap, RP.gap.max, 'a pinned gap holds (screenshots)'); dev({ pin: false }); quiet();
  for (const d of [null, 'x', [1, 2], [NaN, 0, 1], [0, 0, 0], [1e9, 0, 0]]) R.room.handle(me, { t: 'hit', to: e.id, w: 'ar', n: 1, d });
  assert.equal(R.room.damage(e, NaN, me, 'ar'), false); assert.equal(R.room.damage(e, -5, me, 'ar'), false); assert.equal(R.room.damage(e, 500, me, 'ar'), false, 'phase 1: a blast is shrugged off');
  R.room.kill(e, me, 'void'); assert.ok(e.alive, 'the room can\'t kill it');
  dev({ want: 'grab' }); const a = B.arms[0], h0 = ev('hit').length;
  R.room.handle(me, { t: 'hit', to: e.id, w: 'ar', n: 1, h: 1, d: aim(knot(a)) }); await sleep(130);
  const h = ev('hit').slice(h0); assert.equal(h.length, 1); assert.equal(h[0].part, 'knot'); assert.equal(h[0].dmg, WEAPONS.ar.dmg * 2); assert.equal(h[0].head, false);
  R.room.handle(me, { t: 'hit', to: e.id, w: 'ar', n: 1, d: [1, 0, 0] }); await sleep(130); assert.equal(ev('hit').length, h0 + 1, 'a shot that crosses nothing');
  sim.dev = false; dev({ gap: 3 }); assert.equal(B.gap, 30, 'dev messages need ?storydev=1'); sim.dev = true;
  sim.msg({ t: 'sty', k: 'despawn', id: ID }); assert.equal(sim.refEnemies().length, 0);
  // the first boss still spawns and fights by its own rules in the same room
  sim.msg({ t: 'sty', k: 'spawn', kind: 'overtime_1', at: [0, 1.3, 12] });
  const ot = sim.refEnemies()[0]; assert.ok(ot.sk.b && !ot.sk.b.train); assert.equal(ot.sk.b.hp, 4200); R.room.damage(ot, 100, me, 'ar'); assert.equal(ot.sk.b.hp, 4100);
});
console.log(n, 'passed');
process.exit(0);
