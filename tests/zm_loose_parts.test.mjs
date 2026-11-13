// "sometimes when you kill zombies their body parts stay floating": every loose piece (a gib, a severed limb, a hat)
// has to end up on the floor under it, wherever the zombie died and however hard it was hit. They used to keep the floor
// found under the body, so a piece that flew off stairs, a bench, a bed, a balcony or the skybridge stopped in mid-air.
import test from 'node:test';
import assert from 'node:assert/strict';
import '../shared/zombies.js';
import { MAPS } from '../shared/map.js';
import { looseStep, floorUnder } from '../shared/loose.js';

// seeded, so a failure is the same failure next time
const rng = (s) => () => { s |= 0; s = (s + 0x6d2b79f5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
// how it died -> how its pieces leave: [sideways speed, upward speed, height the piece starts at above the feet]
const WAYS = { headshot: [5, 6, 1.6], melee: [3, 4, 1.0], explosion: [14, 11, 1.0], shredder: [9, 3, 0.6], falling: [2, -6, 3.5] };
// places a zombie dies (feet): the awkward ones on purpose
const SPOTS = {
  school: [[0, 2.3, -8, 'the main stairs, half way'], [0, 4.5, -12.6, 'the top of the main stairs'], [13.5, 2.3, 15, 'the bleachers'], [11.5, 4.5, 2, 'the gym balcony edge'],
    [7.4, 0.45, 11, 'on the lobby bench'], [-19, 0.8, 13, 'on a lunch table'], [26, 0.3, 18, 'on a gym mat'], [-2, 4.5, 4, 'upstairs by the stairwell glass'], [-20, 4.5, 12, 'between the library shelves'], [0, 0, 16, 'the lobby floor']],
  hospital: [[0.5, 1.2, -18, 'the ramp, lane A'], [-1, 3.4, -22, 'the ramp, lane B'], [28, 2.3, 15, 'the fire stairs'], [0, 4.5, 0, 'the middle of the skybridge'], [-4, 4.5, 1.6, 'the skybridge rail'],
    [0, 4.5, -10.6, 'the overlook'], [-28.6, 0.6, -10, 'on a ward bed'], [18, 5.1, 12.5, 'on an intensive care bed'], [15.5, 0.9, -13, 'on a morgue slab'], [0, 0, 14, 'the Emergency floor']],
};
const settle = (boxes, o, p, rest) => { for (let i = 0; i < 60 * 12; i++) looseStep(boxes, o, p, 1 / 60, rest); };

for (const [id, spots] of Object.entries(SPOTS)) {
  test(`${id}: no piece is left hanging, wherever and however the zombie died`, () => {
    const boxes = MAPS[id].boxes, R = rng(id.length * 7919);
    let n = 0, fellFar = 0;
    for (const [x, y, z, where] of spots) for (const [way, [side, up, h]] of Object.entries(WAYS)) for (let k = 0; k < 14; k++) {
      const a = R() * Math.PI * 2, sp = side * (0.4 + R() * 0.8), rest = k % 5 === 0 ? 0.16 : 0.05; // (a head lies higher than a hand)
      const p = { x, y: y + h * (0.5 + R() * 0.6), z }, startFloor = floorUnder(boxes, x, y + 0.2, z);
      const o = { v: [Math.cos(a) * sp, up * (0.5 + R() * 0.7), Math.sin(a) * sp], floorY: startFloor }; // (what remote.js / zmlimbs.js start a piece with)
      settle(boxes, o, p, rest);
      const f = floorUnder(boxes, p.x, p.y, p.z);
      if (f < -1e8) { assert.ok(p.y < -50, `${where}, ${way}: a piece left the building and hung at y ${p.y.toFixed(2)}`); continue; } // (through a window: it has to keep falling)
      assert.ok(p.y - f <= rest + 0.03, `${where}, ${way}: a piece hangs ${(p.y - f).toFixed(2)} m above the floor at ${p.x.toFixed(1)}, ${p.y.toFixed(2)}, ${p.z.toFixed(1)}`);
      assert.ok(p.y - f >= rest - 0.03, `${where}, ${way}: a piece sank ${(f - p.y).toFixed(2)} m into the floor`);
      assert.ok(Math.hypot(...o.v) < 0.5, `${where}, ${way}: a piece never came to rest (speed ${Math.hypot(...o.v).toFixed(2)})`);
      if (startFloor - f > 1) fellFar++;
      n++;
    }
    assert.ok(n > spots.length * 5 * 14 * 0.9, 'most pieces stay inside the building');
    assert.ok(fellFar > 20, 'the test really does throw pieces off high places (' + fellFar + ' ended up more than a metre below where they started)');
  });
}

test('the old rule is what left them floating (the floor under the body, kept for good)', () => {
  const boxes = MAPS.hospital.boxes, p = { x: 0, y: 5.5, z: 1.2 }, o = { v: [0, 3, 6], floorY: floorUnder(boxes, 0, 4.7, 1.2) }; // off the skybridge, over the waiting room
  assert.ok(Math.abs(o.floorY - 4.5) < 0.01);
  settle(boxes, o, p, 0.05);
  assert.ok(p.y < 0.2, 'it lands in the waiting room below (was: stopped at bridge height, 4.5 m up), y ' + p.y.toFixed(2));
});
