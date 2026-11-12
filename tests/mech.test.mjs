// mech drop: the shared numbers and helpers (shared/mech.js). node --test tests/mech.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { MECH, MF, MECH_BITS, FRAMES, mechFrame, isFrame, mechBoxes, energyAt, spend, newEnergy, speedCap, inArc, ramHit, dropHit, addMark, mechClash } from '../shared/mech.js';
import { FLAGS, STREAKS, WEAPONS, validLoadout, validStreaks } from '../shared/weapons.js';
import { BODY } from '../shared/bodyhp.js';

test('the streak: 9 kills, between the rig and the giant duck, pickable', () => {
  assert.equal(STREAKS.mechdrop.kills, MECH.kills);
  assert.ok(STREAKS.mechdrop.kills > STREAKS.overdrive.kills && STREAKS.mechdrop.kills < STREAKS.giantduck.kills);
  assert.deepEqual(validStreaks(['mechdrop', 'scythe', 'moonboots']), ['moonboots', 'scythe', 'mechdrop']);
});
test('frames: two of them, anything else is the paper plane, and the loadout keeps your pick', () => {
  assert.deepEqual(FRAMES.slice(0, 2), ['paperplane', 'nightshift']); assert.ok(FRAMES.includes('wrecking'));
  assert.equal(mechFrame('nightshift'), 'nightshift');
  for (const bad of [undefined, null, 3, '__proto__', 'NIGHTSHIFT', {}, ['nightshift']]) { assert.equal(mechFrame(bad), 'paperplane'); assert.equal(isFrame(bad), false); }
  assert.equal(validLoadout({ mech: 'nightshift' }).mech, 'nightshift');
  assert.equal(validLoadout({ mech: 'tank' }).mech, 'paperplane');
  assert.equal(validLoadout(null).mech, 'paperplane');
});
test('armour pools: 900 / 1500, no drain', () => {
  assert.equal(BODY.paperplane.hp, 900); assert.equal(BODY.nightshift.hp, 1500);
  assert.equal(BODY.paperplane.decay, 0); assert.equal(BODY.nightshift.decay, 0);
});
test('flags: four new bits, all different from every other flag, the frame names share them', () => {
  const mine = [FLAGS.MECH, FLAGS.MECH_A, FLAGS.MECH_B, FLAGS.MECH_C];
  assert.equal(new Set(mine).size, 4);
  for (const [k, v] of Object.entries(FLAGS)) if (!k.startsWith('MECH')) for (const b of mine) assert.equal(v & b, 0, k);
  assert.equal(MF.HOVER, MF.SHIELD); assert.equal(MF.JET, MF.SLAM); assert.equal(MF.DASH, MF.SLASH);
  // the top bit survives the trip through a snapshot (num(x) | 0) and clears cleanly
  const f = (FLAGS.MECH | MF.DASH | FLAGS.CROUCH) | 0;
  assert.ok(f & MF.DASH); assert.equal(f & ~MECH_BITS, FLAGS.CROUCH);
  assert.equal(JSON.parse(JSON.stringify(f)) | 0, f);
});
test('kill feed names for every move', () => {
  for (const w of ['mechdrop', 'mechgun', 'mechlunge', 'mechcrane', 'mechmissile', 'mechjet', 'mechsword', 'mechbash', 'mechtriple', 'mechslam', 'mechstomp', 'mechram', 'mechboom']) assert.ok(WEAPONS[w] && WEAPONS[w].name, w);
});
test('hitboxes: the frame in three stacked boxes, the chest band (the cockpit) is the headshot, sized per frame', () => {
  const b = mechBoxes([10, 2, -4], 'nightshift');
  assert.equal(b.length, 3); assert.deepEqual(b.map((x) => x.head), [false, true, false]);
  assert.equal(b[2].max[1], 2 + MECH.nightshift.h);
  assert.equal(b[0].max[1], b[1].min[1]); assert.equal(b[1].max[1], b[2].min[1]); // stacked, no overlap
  assert.ok(Math.abs((b[0].max[0] - b[0].min[0]) - 2.4) < 1e-9); // MECHS.md: about 2.4 wide
  const p = mechBoxes([0, 0, 0], 'paperplane');
  assert.ok(Math.abs(p[2].max[1] - 4.9) < 1e-9 && Math.abs((p[0].max[0] - p[0].min[0]) - 1.6) < 1e-9);
});
test('energy: spends, refuses when short, refills after the delay', () => {
  const E = newEnergy(0);
  assert.ok(spend(E, 25, 0)); assert.ok(spend(E, 25, 100)); assert.ok(spend(E, 25, 200)); assert.ok(spend(E, 25, 300));
  assert.equal(spend(E, 25, 400), false);
  assert.equal(Math.round(energyAt(E, 300 + MECH.energy.delay * 1000)), 0); // still waiting
  assert.equal(Math.round(energyAt(E, 300 + MECH.energy.delay * 1000 + 1000)), MECH.energy.regen);
  assert.equal(energyAt(E, 1e6), MECH.energy.max);
});
test('speed caps follow what you are doing', () => {
  assert.equal(speedCap('paperplane', FLAGS.MECH | MF.JET), MECH.paperplane.jet.speed);
  assert.equal(speedCap('paperplane', FLAGS.MECH | MF.DASH), MECH.paperplane.lunge.speed);
  assert.equal(speedCap('nightshift', FLAGS.MECH), MECH.nightshift.speed);
  assert.equal(speedCap('nightshift', FLAGS.MECH | MF.SLASH), MECH.nightshift.triple.speed);
  assert.equal(speedCap('nightshift', FLAGS.MECH | MF.SHIELD), MECH.nightshift.speed * MECH.nightshift.shield.slow); // behind the shield: 45%
});
test('sword arc: in front, in reach; not behind', () => {
  assert.ok(inArc([0, 0, 0], 0, [0, 0, -5], 6.2, 0.2));
  assert.ok(inArc([0, 0, 0], 0, [3, 0, -3], 6.2, 0.2));
  assert.ok(!inArc([0, 0, 0], 0, [0, 0, 5], 6.2, 0.2));
  assert.ok(!inArc([0, 0, 0], 0, [0, 0, -9], 6.2, 0.2));
  assert.ok(inArc([0, 0, 0], 0, [0.5, 0, 0.5], 6.2, 0.2)); // right under it
});
test('rams scale with speed; drop shockwave falls off', () => {
  assert.equal(ramHit(3), null);
  assert.ok(ramHit(14).dmg > ramHit(8).dmg && ramHit(14).kb > ramHit(8).kb);
  assert.ok(ramHit(100).dmg <= MECH.ram.cap);
  assert.equal(dropHit(0).dmg, MECH.drop.dmg);
  assert.ok(dropHit(5).dmg < dropHit(1).dmg);
  assert.equal(dropHit(MECH.drop.r + 0.1), null);
});
test('overtime: the 4th mark clocks them out, then they are immune for a bit; marks fade', () => {
  const T = MECH.nightshift.overtime, o = { n: 0, until: 0 };
  assert.equal(addMark(o, 0), false); assert.equal(addMark(o, 100), false); assert.equal(addMark(o, 200), false);
  assert.equal(addMark(o, 300), true);
  assert.equal(addMark(o, 400), false); assert.equal(o.n, 0); // immune: nothing builds
  const o2 = { n: 0, until: 0 };
  addMark(o2, 0); addMark(o2, 100);
  addMark(o2, 100 + T.fade * 1000 + 1); assert.equal(o2.n, 1); // faded: started over
  const o3 = { n: 0, until: 0 }; addMark(o3, 0); addMark(o3, 1); addMark(o3, 2); addMark(o3, 3);
  for (let t = 4; t < (T.stun + T.immune) * 1000; t += 50) assert.equal(addMark(o3, t), false, 'no stun lock');
});
test('clashes: no body streaks in a mech, no mech drop in the rig / ball / with one out', () => {
  assert.ok(mechClash('overdrive', true, false, false, false));
  assert.ok(mechClash('wreckingball', true, false, false, false));
  assert.ok(!mechClash('chickenstrike', true, false, false, false));
  assert.ok(mechClash('mechdrop', false, true, false, false));
  assert.ok(mechClash('mechdrop', false, false, true, false));
  assert.ok(mechClash('mechdrop', false, false, false, true));
  assert.ok(!mechClash('mechdrop', false, false, false, false));
});
