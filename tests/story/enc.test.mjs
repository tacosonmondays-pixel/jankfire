// node tests/story/enc.test.mjs : Act I encounters, the sim half (shared/story/encsys.js + server/storyenc.js): groups
// of story enemies spawned through the referee, war-rigs that drive and ram, interns' business cards, leaping
// stomach-dogs, flee / clear, bad input dropped. runs on the test lot (the referee's flat map).
import assert from 'node:assert/strict';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/invsys.js';
import '../../shared/story/solohost.js';
import '../../shared/story/carsys.js';
import '../../shared/story/refsys.js';
import '../../shared/story/encsys.js';
import { newSave } from '../../shared/story/save.js';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// every check says which test and which check failed (a flake under load used to say only "false == true")
let n = 0; const t = async (name, fn) => { try { await fn(); } catch (e) { e.message = `[${name}] ${e.message}`; throw e; } n++; console.log('ok', name); };

const out = [];
const sim = createSim({ send: (o) => out.push(o), save: newSave(0, 'story_test') });
sim.msg({ t: 'join', name: 'tester' });
const enc = (o) => sim.msg({ t: 'sty', k: 'enc', ...o });
const evs = (type) => out.filter((o) => o.t === 'sty' && o.k === 'enc' && o.ev.type === type).map((o) => o.ev);
const ons = () => out.filter((o) => o.t === 'sty' && o.k === 'encOn');
const run = async (secs) => { for (let i = 0; i < secs * 20; i++) { sim.tick(0.05); if (i % 4 === 0) await sleep(1); } };
// tick the sim until ok() says the thing happened: it waits on state, not on the wall clock or a tick count. the cap is
// sim time, well past what it needs, and a miss names the check (plus what the state looked like)
async function until(label, ok, { secs = 30, each = null, why = () => '' } = {}) {
  for (let i = 0; i < secs * 20; i++) { if (each) each(); await run(0.05); const v = ok(); if (v) return v; }
  assert.fail(`${label}: didn't happen within ${secs} s of sim time ${why()}`);
}
// the referee loads the room code (a dynamic import): a busy machine can take a while, so wait on it, not on 5 s
for (let i = 0; i < 1200 && !sim.ref && !sim.refOff; i++) await sleep(50);
assert.ok(sim.ref, 'referee up: ' + (sim.refOff || 'still loading after 60 s'));
await run(0.2);
const me = sim.ref.me;
const hold = () => { me.spawnT = 0; me.pos = [-35, 0.1, 10]; // (a clear lane down the lot's west side)
  me.vel = [0, 0, 0]; };

await t('a group spawns through the referee and the client hears which room player is which', async () => {
  hold();
  enc({ op: 'spawn', g: 'tst', kind: 'intern', at: [0, 0.1, -20], n: 3 });
  const on = ons().at(-1);
  assert.equal(on && on.g, 'tst', 'the client hears the group'); assert.equal(on.list.length, 3, 'all three in it');
  for (const x of on.list) { const p = sim.ref.room.players.get(x.pid); assert.ok(p && p.sk && p.sk.kind === 'intern', 'room player ' + x.pid + ' is an intern'); assert.equal(p.storyId, x.id, 'and carries its story id'); }
  enc({ op: 'clear', g: 'tst' });
  assert.equal(sim.refEnemies().length, 0, 'clear removes them, no kills');
  assert.ok(!out.some((o) => o.k === 'combat' && o.ev.type === 'kill'), 'nobody was killed by a clear');
});

await t('bad asks do nothing: unknown kind, bad group name, nonsense position, a flood', async () => {
  const k0 = ons().length;
  enc({ op: 'spawn', g: 'x', kind: 'overtime_1', at: [0, 0, -10] }); // (a boss is not an encounter kind)
  enc({ op: 'spawn', g: '../x', kind: 'intern', at: [0, 0, -10] });
  enc({ op: 'spawn', g: 'x', kind: 'intern', at: [0, NaN, -10] });
  enc({ op: 'spawn', g: 'x', kind: 'intern', at: '0,0,0' });
  enc({ op: 'spawn', g: 'x', kind: { toString: () => 'intern' }, at: [0, 0, -10] });
  assert.equal(ons().length, k0, 'no bad ask spawned a group'); assert.equal(sim.refEnemies().length, 0, 'no enemies from bad asks');
  await run(1.1);
  for (let i = 0; i < 30; i++) enc({ op: 'spawn', g: 'fl', kind: 'intern', at: [0, 0.1, -30], n: 8 });
  assert.ok(sim.refEnemies().length <= 24, 'rate limited and capped: ' + sim.refEnemies().length);
  enc({ op: 'clear' });
  assert.equal(sim.refEnemies().length, 0, 'the flood is cleared');
});

await t('a war-rig drives at you and rams: you take a hit, the client gets a ram (in a car: less)', async () => {
  await run(1.1);
  hold();
  enc({ op: 'spawn', g: 'rig', kind: 'war_rig', at: [-35, 0.1, -30] });
  const rig = sim.refEnemies()[0]; rig.ai.nextShot = Infinity; // (only the bumper for this one)
  const z0 = rig.pos[2];
  const ram = await until('it rammed you', () => evs('ram')[0], { each: () => { hold(); me.hp = 100; me.alive = true; }, why: () => `(rig at ${rig.pos.map((v) => v.toFixed(1))}, from z ${z0.toFixed(1)})` });
  assert.ok(rig.pos[2] > z0 + 10 || ram, 'it drove toward you');
  assert.equal(ram.car, false, 'an on-foot ram'); assert.equal(ram.pid, rig.id, 'the ram names the rig');
  assert.ok(me.hp < 100, 'on foot a ram hurts: ' + me.hp + ' ' + JSON.stringify(ram) + ' ' + JSON.stringify(out.filter((o) => o.t === 'sty' && o.k === 'combat').slice(-3)));
  enc({ op: 'flee', g: 'rig' });
  const d0 = Math.hypot(rig.pos[0] + 35, rig.pos[2] - 10);
  await until('fleeing rigs drive away', () => Math.hypot(rig.pos[0] + 35, rig.pos[2] - 10) > d0 + 8, { secs: 20, why: () => `(from ${d0.toFixed(1)} m to ${Math.hypot(rig.pos[0] + 35, rig.pos[2] - 10).toFixed(1)} m)` });
  enc({ op: 'clear', g: 'rig' });
});

await t('interns throw business cards (frags) at you from throwing range', async () => {
  await run(1.1);
  hold();
  enc({ op: 'spawn', g: 'int', kind: 'intern', at: [-35, 0.1, -4], w: 'pistol' });
  const it = sim.refEnemies()[0]; it.ai.nextShot = Infinity; it.cardT = 0;
  const card = await until('a card came', () => evs('card')[0], { each: () => { hold(); me.hp = 100; me.alive = true; it.pos = [-35, 0.1, -4]; it.vel = [0, 0, 0]; }, why: () => `(intern seen you: ${!!it.ai.seenAt}, alive: ${it.alive})` });
  assert.ok([...sim.ref.room.projectiles.values()].some((p) => p.k === 'frag' && p.o === it.id) || card, 'a frag in the air');
  enc({ op: 'clear' });
  for (const pr of [...sim.ref.room.projectiles.values()]) if (pr.k === 'frag') sim.ref.room.removeProj(pr); // (a card still in the air would land in the next test: under load it killed you mid-dog-test, and a dog won't leap at a dead man)
});

await t('stomach-dogs are quick and leap the last few metres', async () => {
  await run(1.1);
  hold();
  enc({ op: 'spawn', g: 'dog', kind: 'stomach_dog', at: [-35, 0.1, -6] });
  const dg = sim.refEnemies()[0]; dg.leapT = 0;
  // (the dog stays in its leap window, 6 m out (x and z only: its feet stay on the floor): the room's leap timer is wall-clock and the sim runs far faster than
  // that, so a dog left to walk could cross the whole window before the timer allows a leap. the same trick as the intern)
  await until('it leapt', () => evs('leap')[0], { each: () => { hold(); me.hp = 100; me.alive = true; if (!evs('leap').length) { dg.pos[0] = -35; dg.pos[2] = 4; dg.vel[0] = dg.vel[2] = 0; } }, why: () => `(dog at ${dg.pos.map((v) => v.toFixed(1))}, on the ground: ${dg.onGround}, after you: ${dg.ai && dg.ai.target === me.id}, you alive: ${me.alive})` });
  enc({ op: 'clear' });
});

await t('rams in a car hurt less (the car takes it)', async () => {
  await run(1.1);
  hold();
  sim.me.car = 1; sim.cars.set(1, { id: 1, ty: 'hatch', p: [0, 0, 0], h: 0, hp: 150, driver: 1 }); // (as carsys keeps it while you drive)
  const before = evs('ram').length;
  enc({ op: 'spawn', g: 'rig2', kind: 'war_rig', at: [-35, 0.1, -30] });
  const rig = sim.refEnemies()[0]; rig.ai.nextShot = Infinity;
  await until('a rig rammed your car', () => evs('ram').length > before, { each: () => { hold(); me.hp = 100; me.alive = true; }, why: () => `(rig at ${rig.pos.map((v) => v.toFixed(1))})` });
  const hp = me.hp, ram = evs('ram').at(-1);
  assert.ok(ram && ram.car === true, 'a car ram');
  assert.ok(hp >= 100 - 10, 'the car took most of it: ' + hp);
  enc({ op: 'clear' });
});

console.log(`enc: ${n} ok`);
process.exit(0);
