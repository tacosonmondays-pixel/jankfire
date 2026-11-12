// node tests/story/bossbar.test.mjs : a boss's bar never outlives his fight. the client clears it when the referee says
// he's gone ({ t: 'sty', k: 'boss', on: false }); bossfight.js asks the referee to remove him when his fight step ends
// any way at all (a skipped or faked step too). here: the referee side of that, in the slice and on the test lot
import assert from 'node:assert/strict';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/invsys.js';
import '../../shared/story/solohost.js';
import '../../shared/story/refsys.js';
import { newSave } from '../../shared/story/save.js';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

for (const map of ['story_test', 'story_slice']) {
  const out = [];
  const sim = createSim({ send: (o) => out.push(o), save: newSave(0, map) });
  sim.raw = (s) => out.push(JSON.parse(s));
  sim.msg({ t: 'join', name: 'tester' });
  for (let i = 0; i < 200 && !sim.ref; i++) await sleep(50);
  const run = async (secs) => { for (let i = 0; i < Math.round(secs * 20); i++) { sim.tick(0.05); await sleep(0); } };
  const boss = () => out.filter((o) => o.t === 'sty' && o.k === 'boss');
  const me = sim.ref.me, at = [me.pos[0], me.pos[1], me.pos[2] - 12];
  await t(`${map}: a fight step that ends without his defeat: despawn by id, the client hears he's gone, the room is empty`, async () => {
    sim.msg({ t: 'sty', k: 'spawn', kind: 'overtime_1', id: 'overtime_1', at });
    await run(0.3);
    assert.equal(boss().at(-1).on, true, 'the bar comes up');
    sim.msg({ t: 'sty', k: 'despawn', id: 'overtime_1' }); // (bossfight.js, when the step moves on)
    await run(0.2);
    const off = boss().at(-1);
    assert.equal(off.on, false, 'the bar goes'); assert.equal(off.id, 'overtime_1');
    assert.equal(sim.refEnemies().length, 0);
  });
  await t(`${map}: after a real defeat the same despawn is harmless (he's already gone, no second message)`, async () => {
    sim.msg({ t: 'sty', k: 'spawn', kind: 'overtime_1', id: 'overtime_1', at });
    await run(0.3);
    const e = sim.refEnemies()[0], B = e.sk.b; B.calm = true; B.next = Infinity;
    for (let i = 0; i < 400 && B.state !== 'done'; i++) { if (B.state === 'fight' || B.state === 'rest') sim.ref.room.damage(e, 400, me, 'ar'); await run(0.25); }
    assert.equal(B.state, 'done');
    await run(0.2);
    const offs = boss().filter((o) => o.on === false).length;
    sim.msg({ t: 'sty', k: 'despawn', id: 'overtime_1' }); await run(0.2);
    assert.equal(boss().filter((o) => o.on === false).length, offs, 'nothing more');
    assert.equal(sim.refEnemies().length, 0);
  });
}
console.log(`${n} ok`);
process.exit(0);
