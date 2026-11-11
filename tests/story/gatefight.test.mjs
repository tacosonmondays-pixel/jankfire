// node tests/story/gatefight.test.mjs : Mr. Overtime at the real Gut Border Gate. the referee in the streamed slice
// (shared/story/refworld.js): the chunks round you are its collision, a boss spawned at the arena stands on the
// arena's real ground, the fight's death puts you back at the arena's start, and a fresh save's m04 goes through the
// fight step to the end (the fight resolved by the room: his whole pool taken off with real damage)
import assert from 'node:assert/strict';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/enginesys.js';
import '../../shared/story/invsys.js';
import '../../shared/story/solohost.js';
import '../../shared/story/refsys.js';
import { newSave } from '../../shared/story/save.js';
import { marksNear } from '../../shared/city/marks.js';
import { raycast } from '../../shared/physics.js';
import { STORY_SLICE } from '../../shared/city/storyworld.js';
import { makeStory } from '../../shared/story/story.js';
import * as overdue from '../../shared/story/content/overdue.js';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

const out = [];
const sim = createSim({ send: (o) => out.push(typeof o === 'string' ? JSON.parse(o) : o), save: newSave(0, 'story_slice') });
sim.raw = (s) => out.push(JSON.parse(s));
sim.msg({ t: 'join', name: 'tester' });
const sty = (k) => out.filter((o) => o.t === 'sty' && o.k === k);
const ev = (type) => sty('combat').map((o) => o.ev).filter((e) => e.type === type);
const run = async (secs) => { for (let i = 0; i < Math.round(secs * 20); i++) { sim.tick(0.05); await sleep(0); } };
for (let i = 0; i < 200 && !sim.ref; i++) await sleep(50);
assert.ok(sim.ref, 'room up in the slice: ' + (sim.refOff || ''));
const R = sim.ref, me = R.me, map = R.room.map;
const CP = marksNear('slice', -44, -14, 60, 'arena.player')[0].p, BOSSAT = marksNear('slice', -44, -14, 60, 'arena.boss')[0].p;

await t('the slice has real collision round you in the referee (the Machine\'s floor under the spawn)', async () => {
  assert.equal(R.room.cfg.map, 'story_slice');
  assert.ok(map.world && map.boxes.length > 500, 'boxes: ' + map.boxes.length);
  const s = STORY_SLICE.spawn, h = raycast([s[0], s[1] + 1, s[2]], [0, -1, 0], 4, map.boxes);
  assert.ok(h && h.t < 1.6, 'a floor under the spawn');
});

await t('warp: the story moves you to the arena (a new seq, the ground there loaded)', async () => {
  const q = me.seq;
  sim.msg({ t: 'sty', k: 'warp', at: CP, yaw: 0 });
  assert.equal(me.seq, q + 1); assert.deepEqual(me.pos, CP);
  assert.ok(out.some((o) => o.t === 'spawn' && o.q === q + 1), 'the client is told (spawn)');
  assert.ok(raycast([CP[0], CP[1] + 1, CP[2]], [0, -1, 0], 3, map.boxes), 'the landing is under you');
  sim.msg({ t: 'sty', k: 'warp', at: [1e4, 0, 0] }); assert.equal(me.seq, q + 1, 'too soon / out of the world: nothing');
  await run(1.1);
  sim.msg({ t: 'sty', k: 'warp', at: [9e4, 0, 9e4] }); assert.equal(me.seq, q + 1, 'outside the slice: nothing');
  sim.msg({ t: 'sty', k: 'warp', at: 'x' }); assert.equal(me.seq, q + 1);
});

let boss;
await t('overtime_1 spawns at the gate and stands on the gate\'s landing (not the void, not the test lot)', async () => {
  sim.msg({ t: 'sty', k: 'spawn', kind: 'overtime_1', id: 'overtime_1', at: BOSSAT });
  boss = sim.refEnemies().find((p) => p.sk.b);
  assert.ok(boss, 'he is up');
  const B = boss.sk.b; B.calm = true; B.next = Infinity;
  await run(2);
  assert.ok(boss.onGround, 'on the ground'); assert.ok(Math.abs(boss.pos[1] - 36) < 1, 'at the landing\'s height: ' + boss.pos[1]);
  assert.deepEqual(map.spawns[0], CP, 'the checkpoint is the arena\'s start while he is up');
});

await t('his staples stop in the gate\'s real walls', async () => {
  const B = boss.sk.b;
  // a staple fired from him straight into the house fronts (arenas.js: the staples' wall at x -76..-57, z ~-6)
  const o = [boss.pos[0], boss.pos[1] + 2, boss.pos[2]], to = [-66, 38, -6], d = to.map((x, i) => x - o[i]), l = Math.hypot(...d);
  const w = raycast(o, d.map((x) => x / l), 100, R.room.boxes);
  assert.ok(w && w.t < l + 1, 'something solid on the way to the house fronts');
  assert.ok(B, 'still a boss');
});

await t('a death in the fight: back at the arena\'s start, and he gives you a moment', async () => {
  me.spawnT = 0;
  R.room.damage(me, 500, boss, 'nailgun');
  assert.equal(me.alive, false);
  for (let i = 0; i < 120 && !me.alive; i++) { await run(0.1); await sleep(100); } // (the room's respawn wait is real time)
  assert.ok(me.alive, 'back up');
  assert.ok(Math.hypot(me.pos[0] - CP[0], me.pos[2] - CP[2]) < 0.5, 'at the arena\'s start: ' + me.pos);
  assert.ok(sty('cp').length >= 1, 'the client is told which way to face');
  const B = boss.sk.b; assert.ok(B.next >= B.t + 2, 'a grace beat before his next attack');
});

await t('the fight resolved with real damage: the phases, the end (killBoss), the checkpoint back to the Machine', async () => {
  const B = boss.sk.b;
  for (let i = 0; i < 400 && B.state !== 'done'; i++) {
    if (B.state === 'cut' && boss.sk.hold === false) { /* the client's scene would hold him: none here */ }
    if (B.state === 'fight' || B.state === 'rest') R.room.damage(boss, 400, me, 'ar');
    await run(0.25);
  }
  assert.equal(B.state, 'done', 'beaten (state ' + B.state + ')');
  const k = ev('kill').find((e) => e.boss === 'overtime_1');
  assert.ok(k && k.defeat, 'the fight\'s end is the story\'s kill');
  assert.ok(ev('phase').some((e) => e.phase === 1) && ev('phase').some((e) => e.phase === 2), 'through his phases');
  await run(0.5);
  assert.ok(!sim.refEnemies().includes(boss), 'he walks off');
  assert.deepEqual(map.spawns[0], STORY_SLICE.spawn, 'deaths go back to the Machine');
});

await t('a fresh save drives m04 CLOCKING IN through the fight step to done (the engine, the referee\'s kill)', async () => {
  const st = makeStory({ content: { ...overdue, init: [], autostart: [] }, host: { act() {}, event() {}, has: () => false } });
  for (const m of ['m01_return_to_sender', 'm02_soup_run', 'm03_somethings_digesting']) st.st.quests[m] = { done: true, step: '', t: 0 };
  assert.ok(st.quests.start('m04_clocking_in'), 'm04 starts');
  const step = () => (st.quests.objectives().find((o) => o.quest === 'm04_clocking_in') || {}).step;
  st.run(['flag:seen_c4']); st.tick(0.1);
  assert.equal(step(), 'fight');
  st.emit({ type: 'killBoss', boss: 'overtime_1' }); st.tick(0.1); // (what bossfight.js sends on the referee's kill above)
  assert.equal(step(), 'rip');
  st.run(['flag:heart_ripped']); st.tick(0.1);
  assert.equal(step(), 'after');
  st.emit({ type: 'talk', npc: 'overtime', node: 'm04_clocking_in.rescheduled.start' }); st.tick(0.1);
  assert.equal(step(), 'truck');
  st.run(['flag:truck_choice_made']); st.tick(0.1);
  assert.equal(step(), 'home');
  st.emit({ type: 'reach', zone: 'bottom:lostfound' }); st.tick(0.1);
  assert.ok(st.st.quests.m04_clocking_in.done, 'm04 done');
});

console.log(`${n} ok`);
process.exit(0);
