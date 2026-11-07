// node tests/story/drive.test.mjs : the arcade car (shared/story/drive.js) on a little box world
import assert from 'node:assert/strict';
import { newCar, stepCar, speedOf, fwdOf, topOf, carType, MAXV, DRIVE, carBoxes, seatOf } from '../../shared/story/drive.js';
import { query, raycast, resetGrid } from '../../shared/physics.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };
const W = (boxes) => { resetGrid(boxes); return { query: (a, b, c, d, out) => query(boxes, a, b, c, d, out), raycast: (o, d, m) => raycast(o, d, m, boxes) }; };
const flat = () => [{ min: [-500, -1, -500], max: [500, 0, 500] }];
const run = (c, inp, secs, world, opts) => { const ev = []; for (let i = 0; i < secs * 120; i++) ev.push(...stepCar(c, inp, 1 / 120, world, opts)); return ev; };

t('throttle reaches the top speed and holds it; brake stops; reverse is slow', () => {
  const w = W(flat()), c = newCar('hatch', [0, 0, 0], 0);
  run(c, { f: true }, 6, w); const top = topOf(carType('hatch'));
  assert.ok(Math.abs(speedOf(c) - top) < 1.5, `${speedOf(c)} vs ${top}`); assert.ok(c.z > 60 && Math.abs(c.x) < 0.5, 'straight ahead (+z at h 0)');
  run(c, { b: true }, 1.0, w); assert.ok(speedOf(c) < 4, `braked hard: ${speedOf(c)}`); // (keep holding: it reverses)
  run(c, { b: true }, 4, w); const f = fwdOf(c); assert.ok(c.vx * f[0] + c.vz * f[2] < -DRIVE.rev + 1.5 && c.vx * f[0] + c.vz * f[2] > -DRIVE.rev - 0.5, 'reverse capped');
  assert.ok(Math.abs(c.y) < 0.03 && c.ground, 'on the floor');
});
t('heavier is slower; the bus is a bus', () => { assert.ok(topOf(carType('bus')) < topOf(carType('sedan'))); assert.ok(topOf(carType('sofa')) > 30); assert.ok(MAXV('hatch') > topOf(carType('hatch')) * DRIVE.boostTop); });
t('steering: right turns right, tighter at speed', () => {
  const w = W(flat()), c = newCar('sedan', [0, 0, 0], 0);
  run(c, { f: true }, 1.5, w); const h0 = c.h; run(c, { f: true, r: true }, 0.5, w);
  assert.ok(c.h < h0, 'right lowers the heading'); // forward (sin h, cos h): facing +z, right is -x
  const c2 = newCar('sedan', [0, 0, 0], 0); run(c2, { f: true, r: true }, 1.2, w); assert.ok(c2.x < -1 && c2.h < -0.6, `turned toward -x: ${c2.x} ${c2.h}`);
  const slow = newCar('sedan', [0, 0, 0], 0); run(slow, { f: true }, 0.6, w); const fast = newCar('sedan', [0, 0, 0], 0); run(fast, { f: true }, 5, w);
  const r0 = slow.h, r1 = fast.h; run(slow, { r: true }, 0.2, w); run(fast, { r: true }, 0.2, w); assert.ok(Math.abs(fast.h - r1) / speedOf(fast) < Math.abs(slow.h - r0) / speedOf(slow), 'tighter at speed (per m/s)');
});
t('handbrake: the tail slides (big sideways speed), normal turns grip', () => {
  const w = W(flat()), slide = (hand) => { const c = newCar('hatch', [0, 0, 0], 0); run(c, { f: true }, 3, w); run(c, { f: true, r: true, hand }, 0.6, w); const f = fwdOf(c); const vl = Math.abs(c.vx * f[2] - c.vz * f[0]); return vl; };
  assert.ok(slide(true) > slide(false) * 2.5, `${slide(true)} vs ${slide(false)}`);
});
t('boost is faster, overheats, then cools', () => {
  const w = W(flat()), c = newCar('hatch', [0, 0, 0], 0);
  const ev = run(c, { f: true, boost: true }, 3.5, w); assert.ok(speedOf(c) > topOf(carType('hatch')) * 1.2, String(speedOf(c)));
  const ev2 = run(c, { f: true, boost: true }, 1.5, w); assert.ok([...ev, ...ev2].some((e) => e.overheat)); assert.ok(c.hot > 0);
  run(c, { f: true, boost: true }, 2, w); assert.ok(speedOf(c) < topOf(carType('hatch')) * 1.25, 'no boost while overheated');
});
t('walls stop you and bounce; fast = crash; very fast = through the windscreen', () => {
  const box = { min: [-50, 0, 30], max: [50, 6, 32] }, w = W([...flat(), box]);
  const c = newCar('hatch', [0, 0, 0], 0); const ev = run(c, { f: true }, 4, w);
  assert.ok(c.z < 30 - carType('hatch').L / 2 + 1.2, `stopped at the wall: ${c.z}`); assert.ok(ev.some((e) => e.crash || e.eject));
  const c2 = newCar('hatch', [0, 0, 20], 0); c2.vz = 45; const ev2 = run(c2, {}, 0.5, w); assert.ok(ev2.some((e) => e.eject), JSON.stringify(ev2)); assert.ok(c2.hp < carType('hatch').hp);
  const c3 = newCar('hatch', [0, 0, 24], 0); c3.vz = 6; const ev3 = run(c3, {}, 1, w); assert.ok(!ev3.some((e) => e.crash || e.eject), 'a bump is just a bump');
});
t('kerbs are climbed, walls are not', () => {
  const kerb = { min: [-50, 0, 10], max: [50, 0.4, 200] }, w = W([...flat(), kerb]);
  const c = newCar('hatch', [0, 0, 0], 0); run(c, { f: true }, 3, w); assert.ok(c.z > 20 && Math.abs(c.y - 0.4) < 0.05, `up the kerb: ${c.z} ${c.y}`);
  const step = { min: [-50, 0, 10], max: [50, 1.2, 200] }, w2 = W([...flat(), step]);
  const d = newCar('hatch', [0, 0, 0], 0); run(d, { f: true }, 3, w2); assert.ok(d.z < 10 && d.y < 0.1, `blocked: ${d.z}`);
});
t('off a ramp the car keeps flying (momentum), then lands', () => {
  const ramp = []; for (let i = 0; i < 20; i++) ramp.push({ min: [-5, 0, 20 + i], max: [5, (i + 1) * 0.3, 21 + i] }); // a stair-ramp 6 m up
  const w = W([...flat(), ...ramp]), c = newCar('hatch', [0, 0, 0], 0);
  let maxY = 0, airT = 0, landed = false;
  for (let i = 0; i < 6 * 120; i++) { const ev = stepCar(c, { f: true, boost: i < 240 }, 1 / 120, w); maxY = Math.max(maxY, c.y); if (!c.ground) airT += 1 / 120; if (ev.some((e) => e.land)) landed = true; }
  assert.ok(maxY > 5.5 && airT > 0.4 && landed && c.z > 50, `max ${maxY.toFixed(1)} air ${airT.toFixed(2)} z ${c.z.toFixed(0)}`);
});
t('slippery ground (marbles / peels): you slide', () => {
  const w = W(flat()), side = (slip) => { const c = newCar('hatch', [0, 0, 0], 0); run(c, { f: true }, 2.5, w); run(c, { f: true, l: true }, 0.7, w, { slip: () => slip }); const f = fwdOf(c); return Math.abs(c.vx * f[2] - c.vz * f[0]); };
  assert.ok(side(0.1) > side(1) * 2, `${side(0.1)} vs ${side(1)}`);
});
t('off the edge: gravity', () => { const w = W([{ min: [-5, -1, -5], max: [5, 0, 5] }]), c = newCar('hatch', [0, 0, 0], 0); run(c, { f: true }, 2.5, w); assert.ok(c.y < -5 && !c.ground); });
t('seat + boxes follow the car', () => { const c = newCar('van', [10, 2, 10], 1); const s = seatOf(c); assert.ok(Math.hypot(s[0] - 10, s[2] - 10) < 1.5 && s[1] > 3); assert.ok(carBoxes(c).length >= 2 && carBoxes(c).every((b) => b.car)); });
console.log(`\n${n} passed`);
