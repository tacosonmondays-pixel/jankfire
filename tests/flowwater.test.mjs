// node --test tests/flowwater.test.mjs : flowing water (shared/flowwater.js, drawn by public/js/flowwater.js). parts named
// *_water are streams and *_pool still water; the fountains' models carry those tags; streams land where they should;
// the splash pool never holds more than its cap (none on Potato); box fountains get jets, other maps don't
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { waterTag, landSpots, capFor, PARTICLE_CAP, DropRing, boxFountains, jetPath } from '../shared/flowwater.js';
import { MAPS } from '../shared/map.js';

const glbMats = (f) => { const b = fs.readFileSync(new URL('../public/models/' + f, import.meta.url)), n = b.readUInt32LE(12); return JSON.parse(b.subarray(20, 20 + n).toString()).materials.map((m) => m.name); };

test('tags: *_water is a stream, *_pool is still water, everything else is left alone', () => {
  assert.equal(waterTag('jbf_jet_water'), 'stream');
  assert.equal(waterTag('sk_drink_water'), 'stream');
  assert.equal(waterTag('jbf_jet_water.001'), 'stream'); // (Blender's duplicate names)
  assert.equal(waterTag('waterfall_water_wzN'), 'stream');
  assert.equal(waterTag('jbf_basin_pool'), 'pool');
  assert.equal(waterTag('Pond_Pool.002'), 'pool');
  for (const n of ['water', 'watertower', 'poolwater', 'wp_waterproof', 'carpool_lane', '', null, undefined]) assert.equal(waterTag(n), null, String(n));
});

test('the fountains ship tagged: the Smiling Fountain\'s jets and basin, the school\'s drinking fountain', () => {
  const jb = glbMats('p_jb_fountain.glb');
  assert.ok(jb.some((m) => waterTag(m) === 'stream'), jb.join());
  assert.ok(jb.some((m) => waterTag(m) === 'pool'), jb.join());
  assert.ok(!jb.includes('water'), 'the old untagged water material is gone');
  assert.ok(glbMats('p_schoolkit.glb').some((m) => waterTag(m) === 'stream'));
});

test('a jet into a pool lands where it hits the water; a lone trickle lands at its bottom end, small', () => {
  const pos = [];
  for (const [x, y, z] of jetPath([0, 6, -6.5], [0, 0.55, -8.7], 0.9, 16)) for (let k = 0; k < 8; k++) pos.push(x + 0.3 * Math.cos(k), y + 0.3 * Math.sin(k), z);
  const s = landSpots(pos, 0.55);
  assert.equal(s.length, 1);
  assert.ok(Math.abs(s[0].z + 8.7) < 0.5 && Math.abs(s[0].x) < 0.3 && s[0].y === 0.55, JSON.stringify(s));
  const arc = [];
  for (const [x, y, z] of jetPath([0.08, 1.07, 0], [-0.06, 0.98, 0.1], 0.04, 6)) for (let k = 0; k < 6; k++) arc.push(x + 0.008 * Math.cos(k), y + 0.008 * Math.sin(k), z);
  const t = landSpots(arc, null);
  assert.equal(t.length, 1);
  assert.ok(t[0].s < 0.2 && Math.abs(t[0].x + 0.06) < 0.03, JSON.stringify(t));
  assert.deepEqual(landSpots([], 0.5), []);
});

test('splash particles: Potato gets none, the pool never grows past its cap', () => {
  assert.equal(capFor(0), 0);
  for (let q = 1; q <= 3; q++) assert.ok(capFor(q) > 0 && capFor(q) <= 800);
  assert.equal(capFor(99), PARTICLE_CAP[3]);
  const r = new DropRing(capFor(1));
  for (let i = 0; i < 1000; i++) r.spawn(i, 0, 0, 0, 1, 0, 0, 5, i % 3, 1);
  assert.equal(r.p.length, r.cap * 3);
  assert.equal(r.live(1), r.cap); // all slots in use, none extra
  assert.equal(r.p[((1000 - 1) % r.cap) * 3], 999); // the newest wrote over the oldest
  assert.equal(r.live(100), 0); // and they all die
  const none = new DropRing(0);
  assert.equal(none.spawn(0, 0, 0, 0, 0, 0, 0, 1, 0), -1);
  assert.equal(Math.floor(r.t[2] / 10), 0); // (kind and size packed in one float)
});

test('box fountains: the Bazaar\'s plazas and the rooftop garden get jets that land in their pools; plain pools don\'t', () => {
  const boxes = (id) => [...MAPS[id].boxes, ...MAPS[id].deco];
  const baz = boxFountains(boxes('bazaar'));
  assert.equal(baz.length, 8); // two fountains, four arcs each
  const pools = boxes('bazaar').filter((b) => b.mat === 'water');
  for (const j of baz) {
    assert.ok(j.from[1] > j.to[1] + 1, 'falls');
    assert.ok(pools.some((w) => j.to[0] > w.min[0] && j.to[0] < w.max[0] && j.to[2] > w.min[2] && j.to[2] < w.max[2] && Math.abs(j.to[1] - w.max[1]) < 0.01), 'lands in a pool');
  }
  assert.equal(boxFountains(boxes('skyline')).length, 4);
  for (const id of ['crate', 'suburb', 'islands', 'forest', 'desert']) assert.equal(boxFountains(boxes(id)).length, 0, id);
});
