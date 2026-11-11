// node tests/story/act1train.test.mjs : m06 TICKETS, PLEASE from a fresh save to the end of Act I. the mission's steps
// are driven the way the client drives them (public/js/story/trainfight.js: the referee's phase-1 event sets
// rp_phase1_done, the middle scene's [FIRE] / [TAKE] choices, the referee's defeat is the killBoss), the train fight
// itself resolved in the referee with dev damage, and the way out: back in the slice (at the tunnel mouth when the
// world has it), with act1_done, the Loop train and Jack's marrow
import assert from 'node:assert/strict';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/invsys.js';
import '../../shared/story/solohost.js';
import '../../shared/story/refsys.js';
import { newSave } from '../../shared/story/save.js';
import { TRAIN } from '../../shared/story/train.js';
import { travelTo, travelHome, DEFAULT_WORLD } from '../../shared/story/worlds.js';
import { makeStory } from '../../shared/story/story.js';
import * as overdue from '../../shared/story/content/overdue.js';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

const acts = [];
const st = makeStory({ content: { ...overdue, init: [], autostart: [] }, host: { act(a) { acts.push(a.do + ':' + (a.arg ?? '')); }, event() {}, has: () => false } });
const Q = 'm06_tickets_please';
const step = () => (st.quests.objectives().find((o) => o.quest === Q) || {}).step;
const tick = () => st.tick(0.1);
// (the scene's choice talks: the 'choice' pseudo-npc's node for a choice, answered like talk.js does: its option's do)
const choose = (ch, opt) => { const node = st.defs.npcs.choice.lines[`${Q}.${ch}`]; assert.ok(node, 'choice ' + ch); const o = (node.opts || []).find((x) => String(x[0]).includes(opt)); assert.ok(o, 'option ' + opt); const to = st.defs.npcs.choice.lines[o[1]]; st.run([...(o[2] && o[2].do || []), ...(to && to.do || [])]); };

await t('a fresh save gets to m06 and walks to the train (plan, fitted, board, the ride in)', async () => {
  for (const m of ['m01_return_to_sender', 'm02_soup_run', 'm03_somethings_digesting', 'm04_clocking_in', 'm05_second_stomach']) st.st.quests[m] = { done: true, step: '', t: 0 };
  assert.ok(st.quests.start(Q), 'm06 starts');
  assert.equal(step(), 'plan');
  st.emit({ type: 'talk', npc: 'gordo', node: `${Q}.the_loop.start` }); tick();
  assert.equal(step(), 'fitted');
  st.emit({ type: 'talk', npc: 'bev', node: `${Q}.loaner.start` }); tick();
  assert.equal(step(), 'board');
  st.emit({ type: 'reach', zone: 'bottom:service_tunnel' }); tick();
  assert.equal(step(), 'ride');
  assert.ok(acts.includes('scene:c6_mind_the_gap'), 'the ride in plays');
  assert.ok((st.defs.scenes.c6_mind_the_gap.onEnd || []).includes('flag:seen_c6_mind_the_gap'), 'its end moves the mission on');
  st.run(st.defs.scenes.c6_mind_the_gap.onEnd); tick();
  assert.equal(step(), 'hold', 'the fight step: trainfight.js travels to the train here');
});

await t('the save travels to the train and knows the way back', async () => {
  const s0 = { ...newSave(0, DEFAULT_WORLD), at: { map: DEFAULT_WORLD, p: [-150, 8, 120], yaw: 1 } };
  const s1 = travelTo(s0, TRAIN.id);
  assert.equal(s1.at.map, TRAIN.id); assert.deepEqual(s1.data.travelFrom.p, [-150, 8, 120]);
  const out = { map: DEFAULT_WORLD, p: [10, 20, -30], yaw: 2 };
  assert.deepEqual(travelHome(s1, out).at, out, 'out at the tunnel mouth when there is one');
  assert.deepEqual(travelHome(s1).at.p, [-150, 8, 120], 'else back where you got on');
  assert.deepEqual(travelHome(s1, { map: 'nope', p: [0, 0, 0] }).at.p, [-150, 8, 120], 'a junk spot is ignored');
});

// the fight in the referee, on the train
const out = [];
const sim = createSim({ send: (o) => out.push(o), save: newSave(0, TRAIN.id) });
sim.dev = true; sim.msg({ t: 'join', name: 'tester' });
for (let i = 0; i < 100 && !sim.ref; i++) await sleep(50);
const ev = (type) => out.filter((o) => o.t === 'sty' && o.k === 'combat' && o.ev.type === type).map((o) => o.ev);
const run = async (secs) => { for (let i = 0; i < Math.round(secs * 20); i++) { sim.tick(0.05); await sleep(0); } };
const dev = (o) => sim.msg({ t: 'sty', k: 'bossdev', ...o });
const ID = 'revenue_protection_1';

await t('phase 1 to its scripted end: the referee says so, the mission hears rp_phase1_done, the middle scene plays', async () => {
  assert.ok(sim.ref, 'room up on the train');
  sim.msg({ t: 'sty', k: 'spawn', kind: ID, id: ID, at: [0, 2, -16] });
  const e = sim.refEnemies()[0], B = e.sk.b; assert.ok(B && B.train, 'the train boss');
  B.calm = true; await run(0.5);
  for (let i = 0; i < 8 && B.phase === 0; i++) dev({ dmg: 900, part: 'eye' });
  const ph = ev('phase').find((p) => p.phase === 1 && p.invuln);
  assert.ok(ph, 'the phase-1 end event');
  st.run(['flag:rp_phase1_done']); tick(); // (trainfight.js on that event, at the hold step)
  assert.equal(step(), 'jack');
  assert.ok(acts.includes('scene:mo_carry_the_bit_that_works'), 'the middle scene plays');
  const sc = st.defs.scenes.mo_carry_the_bit_that_works;
  assert.ok(sc.kind === 'moment' && sc.len >= 60 && sc.tracks.filter((x) => x.choice).length === 2, 'a long moment with two choices in it (scene.js plays it whole)');
  assert.ok(sc.tracks.some((x) => (x.do || []).includes(`talk:choice/${Q}.fire`)) && sc.tracks.some((x) => (x.do || []).includes(`talk:choice/${Q}.take`)), 'the scene opens [FIRE] and [TAKE]');
});

await t('[FIRE] and [TAKE]: you do it, then the marrow; the step ends with Jack dead and the implant', async () => {
  sim.msg({ t: 'sty', k: 'hold', all: true, on: true }); await run(2); // the scene holds the room
  choose('fire', 'FIRE'); choose('take', 'TAKE');
  assert.ok(st.st.flags.jack_fired && st.st.flags.jack_marrow_taken);
  st.run(['flag:seen_mo_carry']); tick(); // (trainfight.js, when the scene is over)
  assert.equal(step(), 'break');
  assert.ok(acts.includes('implant:marrow_pallet_jack'), 'Jack\'s marrow is yours');
  assert.ok(st.st.flags['fate.pallet_jack.dead'], 'and Jack is dead');
  sim.msg({ t: 'sty', k: 'hold', all: true, on: false }); await run(1.6);
});

await t('phases 2 and 3 to the end: the referee\'s defeat is the killBoss; the terminus, P5b, END OF ACT I', async () => {
  const e = sim.refEnemies()[0], B = e.sk.b;
  for (let i = 0; i < 60 && B.state !== 'done'; i++) { if (B.state === 'fight') dev({ dmg: 900, i: i % 8 }); await run(0.3); }
  assert.equal(B.state, 'done', 'beaten');
  const k = ev('kill').find((x) => x.boss === ID); assert.ok(k && k.defeat);
  st.emit({ type: 'killBoss', boss: ID }); tick();
  assert.equal(step(), 'terminus');
  assert.ok(acts.includes('scene:c6b_terminus'));
  st.run(st.defs.scenes.c6b_terminus.onEnd || ['flag:seen_c6b']); tick();
  assert.equal(step(), 'p5b');
  assert.ok(acts.includes('scene:p5b_employee_4417'));
  st.run(st.defs.scenes.p5b_employee_4417.onEnd || ['flag:seen_p5b']); tick();
  assert.ok(st.st.quests[Q].done, 'm06 done');
  assert.ok(st.st.flags.act1_done, 'act I done'); assert.ok(st.st.flags.train_unlocked, 'the Loop train is yours');
  assert.ok(acts.some((a) => /^give:loop_train/.test(a)), 'the Loop train item');
});

console.log(`${n} ok`);
process.exit(0);
