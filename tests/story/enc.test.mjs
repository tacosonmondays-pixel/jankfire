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
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

const out = [];
const sim = createSim({ send: (o) => out.push(o), save: newSave(0, 'story_test') });
sim.msg({ t: 'join', name: 'tester' });
const enc = (o) => sim.msg({ t: 'sty', k: 'enc', ...o });
const evs = (type) => out.filter((o) => o.t === 'sty' && o.k === 'enc' && o.ev.type === type).map((o) => o.ev);
const ons = () => out.filter((o) => o.t === 'sty' && o.k === 'encOn');
const run = async (secs) => { for (let i = 0; i < secs * 20; i++) { sim.tick(0.05); if (i % 4 === 0) await sleep(1); } };
for (let i = 0; i < 100 && !sim.ref; i++) await sleep(50);
assert.ok(sim.ref, 'referee up: ' + (sim.refOff || ''));
await run(0.2);
const me = sim.ref.me;
const hold = () => { me.spawnT = 0; me.pos = [-35, 0.1, 10]; // (a clear lane down the lot's west side)
  me.vel = [0, 0, 0]; };

await t('a group spawns through the referee and the client hears which room player is which', async () => {
  hold();
  enc({ op: 'spawn', g: 'tst', kind: 'intern', at: [0, 0.1, -20], n: 3 });
  const on = ons().at(-1);
  assert.equal(on.g, 'tst'); assert.equal(on.list.length, 3);
  for (const x of on.list) { const p = sim.ref.room.players.get(x.pid); assert.ok(p && p.sk && p.sk.kind === 'intern'); assert.equal(p.storyId, x.id); }
  enc({ op: 'clear', g: 'tst' });
  assert.equal(sim.refEnemies().length, 0, 'clear removes them, no kills');
  assert.ok(!out.some((o) => o.k === 'combat' && o.ev.type === 'kill'));
});

await t('bad asks do nothing: unknown kind, bad group name, nonsense position, a flood', async () => {
  const k0 = ons().length;
  enc({ op: 'spawn', g: 'x', kind: 'overtime_1', at: [0, 0, -10] }); // (a boss is not an encounter kind)
  enc({ op: 'spawn', g: '../x', kind: 'intern', at: [0, 0, -10] });
  enc({ op: 'spawn', g: 'x', kind: 'intern', at: [0, NaN, -10] });
  enc({ op: 'spawn', g: 'x', kind: 'intern', at: '0,0,0' });
  enc({ op: 'spawn', g: 'x', kind: { toString: () => 'intern' }, at: [0, 0, -10] });
  assert.equal(ons().length, k0); assert.equal(sim.refEnemies().length, 0);
  await run(1.1);
  for (let i = 0; i < 30; i++) enc({ op: 'spawn', g: 'fl', kind: 'intern', at: [0, 0.1, -30], n: 8 });
  assert.ok(sim.refEnemies().length <= 24, 'rate limited and capped: ' + sim.refEnemies().length);
  enc({ op: 'clear' });
  assert.equal(sim.refEnemies().length, 0);
});

await t('a war-rig drives at you and rams: you take a hit, the client gets a ram (in a car: less)', async () => {
  await run(1.1);
  hold();
  enc({ op: 'spawn', g: 'rig', kind: 'war_rig', at: [-35, 0.1, -30] });
  const rig = sim.refEnemies()[0]; rig.ai.nextShot = Infinity; // (only the bumper for this one)
  const z0 = rig.pos[2];
  let ram = null;
  for (let i = 0; i < 320 && !ram; i++) { hold(); me.hp = 100; me.alive = true; await run(0.05); ram = evs('ram')[0]; }
  assert.ok(rig.pos[2] > z0 + 10 || ram, 'it drove toward you');
  assert.ok(ram, 'it rammed you');
  assert.equal(ram.car, false); assert.equal(ram.pid, rig.id);
  assert.ok(me.hp < 100, 'on foot a ram hurts: ' + me.hp + ' ' + JSON.stringify(ram) + ' ' + JSON.stringify(out.filter((o) => o.t === 'sty' && o.k === 'combat').slice(-3)));
  enc({ op: 'flee', g: 'rig' });
  const d0 = Math.hypot(rig.pos[0] + 35, rig.pos[2] - 10);
  await run(3);
  assert.ok(Math.hypot(rig.pos[0] + 35, rig.pos[2] - 10) > d0 + 8, 'fleeing rigs drive away');
  enc({ op: 'clear', g: 'rig' });
});

await t('interns throw business cards (frags) at you from throwing range', async () => {
  await run(1.1);
  hold();
  enc({ op: 'spawn', g: 'int', kind: 'intern', at: [-35, 0.1, -4], w: 'pistol' });
  const it = sim.refEnemies()[0]; it.ai.nextShot = Infinity; it.cardT = 0;
  let card = null;
  for (let i = 0; i < 300 && !card; i++) { hold(); me.hp = 100; it.pos = [-35, 0.1, -4]; it.vel = [0, 0, 0]; await run(0.05); card = evs('card')[0]; }
  assert.ok(card, 'a card came');
  assert.ok([...sim.ref.room.projectiles.values()].some((p) => p.k === 'frag' && p.o === it.id) || card, 'a frag in the air');
  enc({ op: 'clear' });
});

await t('stomach-dogs are quick and leap the last few metres', async () => {
  await run(1.1);
  hold();
  enc({ op: 'spawn', g: 'dog', kind: 'stomach_dog', at: [-35, 0.1, -6] });
  const dg = sim.refEnemies()[0]; dg.leapT = 0;
  let leap = null;
  for (let i = 0; i < 320 && !leap; i++) { hold(); me.hp = 100; await run(0.05); leap = evs('leap')[0]; }
  assert.ok(leap, 'it leapt');
  enc({ op: 'clear' });
});

await t('rams in a car hurt less (the car takes it)', async () => {
  await run(1.1);
  hold();
  sim.me.car = 1; sim.cars.set(1, { id: 1, ty: 'hatch', p: [0, 0, 0], h: 0, hp: 150, driver: 1 }); // (as carsys keeps it while you drive)
  const before = evs('ram').length;
  enc({ op: 'spawn', g: 'rig2', kind: 'war_rig', at: [-35, 0.1, -30] });
  const rig = sim.refEnemies()[0]; rig.ai.nextShot = Infinity;
  let hp = 100;
  for (let i = 0; i < 320 && evs('ram').length === before; i++) { hold(); me.hp = 100; me.alive = true; await run(0.05); hp = me.hp; }
  const ram = evs('ram').at(-1);
  assert.ok(ram && ram.car === true, 'a car ram');
  assert.ok(hp >= 100 - 10, 'the car took most of it: ' + hp);
  enc({ op: 'clear' });
});

console.log(`enc: ${n} ok`);
process.exit(0);
