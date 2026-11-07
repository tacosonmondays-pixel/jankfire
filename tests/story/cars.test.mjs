// node tests/story/cars.test.mjs : story cars in the sim (shared/story/carsys.js): get in / out, the anti-cheat checks, saving
import assert from 'node:assert/strict';
import { createSim } from '../../shared/story/sim.js';
import '../../shared/story/carsys.js';
import { CARSYS, PARKED } from '../../shared/story/carsys.js';
import { WORLDS } from '../../shared/story/worlds.js';
import { MAXV } from '../../shared/story/drive.js';
import { newSave, cleanSave } from '../../shared/story/save.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };
const mk = (world = 'story_test', save) => { const out = []; const sim = createSim({ send: (o) => out.push(o), save: save || newSave(0, world) }); sim.msg({ t: 'join' }); return { sim, out, last: (k) => out.filter((o) => o.k === k).at(-1) }; };
const at = (sim, p) => sim.msg({ t: 's', q: sim.me.seq, p, v: [0, 0, 0] });

t('no parked car sits on (or next to) the spawn: you come out of the Machine, not into a bonnet', () => {
  for (const [w, list] of Object.entries(PARKED)) for (const [ty, p] of list) {
    const sp = WORLDS[w].spawn, d = Math.hypot(p[0] - sp[0], p[2] - sp[2]);
    assert.ok(d >= 5, `${w} ${ty} is ${d.toFixed(1)} m from the spawn`);
  }
});
t('fresh worlds have parked cars (the Bottom has the sofa-car)', () => {
  assert.ok(mk('story_slice').sim.cars.size >= 2); assert.ok([...mk('story_slice').sim.cars.values()].some((c) => c.ty === 'sofa'));
  assert.ok(mk('story_test').last('cars').list.length >= 3);
});
t('get in: only next to it, only if nobody is driving', () => {
  const { sim, last } = mk(); const c = [...sim.cars.values()][0];
  sim.msg({ t: 'sty', k: 'carIn', id: c.id }); assert.equal(last('carFix').why, 'too far'); assert.equal(c.driver, 0);
  at(sim, [c.p[0] + 2, c.p[1], c.p[2]]); sim.msg({ t: 'sty', k: 'carIn', id: c.id }); assert.equal(last('carIn').id, c.id); assert.equal(sim.carOf(), c);
  const other = [...sim.cars.values()][1]; at(sim, other.p.slice()); sim.msg({ t: 'sty', k: 'carIn', id: other.id }); assert.equal(last('carFix').why, 'taken', 'one car at a time');
  sim.msg({ t: 'sty', k: 'carIn', id: 999 }); sim.msg({ t: 'sty', k: 'carIn', id: 'x' });
});
t('driving updates: plausible ones stick; too fast, teleports, flying up and spam are refused', () => {
  const { sim, last } = mk(); const c = [...sim.cars.values()][0]; at(sim, c.p.slice()); sim.msg({ t: 'sty', k: 'carIn', id: c.id });
  const p0 = c.p.slice();
  sim.tick(0.1); sim.msg({ t: 'sty', k: 'car', id: c.id, p: [p0[0], p0[1], p0[2] + 3], h: 0.1, v: [0, 0, 30] }); assert.equal(c.p[2], p0[2] + 3, 'ok move');
  sim.tick(0.1); sim.msg({ t: 'sty', k: 'car', id: c.id, p: [p0[0], p0[1], p0[2] + 3 + MAXV(c.ty) * 0.1 + CARSYS.slack + 5], h: 0, v: [0, 0, 30] });
  assert.equal(last('carFix').why, 'too fast'); assert.equal(c.p[2], p0[2] + 3, 'snapped back');
  sim.tick(5); sim.msg({ t: 'sty', k: 'car', id: c.id, p: [p0[0] + 500, p0[1], p0[2]], h: 0, v: [0, 0, 0] }); assert.equal(last('carFix').why, 'teleport');
  sim.tick(0.1); sim.msg({ t: 'sty', k: 'car', id: c.id, p: [p0[0], p0[1] + 40, p0[2] + 3], h: 0, v: [0, 0, 0] }); assert.ok(c.p[1] < p0[1] + 1, 'no flying up');
  sim.tick(0.1); sim.msg({ t: 'sty', k: 'car', id: c.id, p: [p0[0], p0[1], p0[2] + 4], h: 0, v: [0, 0, MAXV(c.ty) + 50] }); assert.equal(c.p[2], p0[2] + 3, 'claimed speed over the cap');
  sim.tick(0.1); sim.msg({ t: 'sty', k: 'car', id: c.id, p: [p0[0], p0[1], p0[2] + 4], h: 0 }); const z = c.p[2];
  sim.msg({ t: 'sty', k: 'car', id: c.id, p: [p0[0], p0[1], p0[2] + 4.5], h: 0 }); assert.equal(c.p[2], z, 'rate limited');
  for (const junk of [{ p: 'x' }, { p: [NaN, 0, 0], h: 0 }, { p: [0, 0, 0], h: 'a' }, { p: [1e9, 0, 0], h: 0 }]) sim.msg({ t: 'sty', k: 'car', id: c.id, ...junk });
  sim.tick(0.1); sim.msg({ t: 'sty', k: 'car', id: c.id, p: [p0[0], p0[1] - 30, p0[2] + 4], h: 0, hp: 9999 }); assert.ok(c.p[1] < p0[1] - 20, 'falling is fine'); assert.ok(c.hp <= 190, 'hp only goes down');
});
t('only the driver can move it; get out frees it', () => {
  const { sim, last } = mk(); const [a, b] = [...sim.cars.values()];
  at(sim, a.p.slice()); sim.msg({ t: 'sty', k: 'car', id: a.id, p: [0, 0, 0], h: 0 }); assert.notDeepEqual(a.p, [0, 0, 0], 'not in it');
  sim.msg({ t: 'sty', k: 'carIn', id: a.id }); sim.tick(0.2);
  sim.msg({ t: 'sty', k: 'car', id: b.id, p: b.p.map((x, i) => (i === 2 ? x + 1 : x)), h: 0 }); assert.equal(b.p[2], [...mk().sim.cars.values()][1].p[2], 'not yours');
  sim.msg({ t: 'sty', k: 'carOut', id: a.id, p: [a.p[0] + 1, a.p[1], a.p[2]], h: 1 }); assert.equal(last('carOut').id, a.id); assert.equal(a.driver, 0); assert.equal(sim.me.car, 0);
});
t('cars are saved where you left them (per zone)', () => {
  const { sim, out } = mk(); const c = [...sim.cars.values()][0]; at(sim, c.p.slice()); sim.msg({ t: 'sty', k: 'carIn', id: c.id });
  sim.tick(0.3); sim.msg({ t: 'sty', k: 'carOut', id: c.id, p: [c.p[0] + 5, c.p[1], c.p[2]], h: 2 });
  sim.msg({ t: 'sty', k: 'save' }); const sv = cleanSave(out.filter((o) => o.k === 'saved').at(-1).save).save;
  const again = mk('story_test', sv).sim; const c2 = [...again.cars.values()].find((x) => x.ty === c.ty);
  assert.equal(c2.p[0], c.p[0]); assert.equal(c2.h, 2); assert.equal(again.cars.size, sim.cars.size, 'not parked twice');
  assert.deepEqual(cleanSave({ ...sv, data: { ...sv.data, cars: { story_test: [{ ty: 'tank', p: [0, 0, 0], h: 0 }, { ty: 'sofa', p: [1e9, 0, 0], h: 0 }], 'BAD ZONE': [] } } }).save.data.cars, {});
});
t('a car that fell into the void is towed back', () => {
  const { sim, last } = mk(); const c = [...sim.cars.values()][0]; const home = c.p.slice(); at(sim, c.p.slice()); sim.msg({ t: 'sty', k: 'carIn', id: c.id });
  for (let i = 0; i < 20; i++) { sim.tick(0.25); sim.msg({ t: 'sty', k: 'car', id: c.id, p: [home[0], home[1] - i * 5, home[2]], h: 0 }); }
  sim.msg({ t: 'sty', k: 'carOut', id: c.id, p: [home[0], home[1] - 100, home[2]], h: 0 });
  assert.ok(last('carOut').towed); assert.ok(c.p[1] > sim.world.killY);
});
console.log(`\n${n} passed`);
