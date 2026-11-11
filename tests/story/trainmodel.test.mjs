// node --test tests/story/trainmodel.test.mjs : the Blender train set against THE TABLE it stands in for.
// public/models/story/rp_train.glb is only the look of the train: the room collides with boxes built from
// shared/story/train.js (HW, CARS, COVER). so every car and every cover piece is measured here against that table,
// straight out of the .glb's vertices: nothing may be wider than the deck, the decks and the van's roof are where you
// stand, the middle lane and the 2 m under the roof are clear, the steps are the table's steps, each cover piece fills
// its box. also: the parts file's names are nodes in the file, its markers are there, the tunnel kit's pieces tile at
// the bore's size, and the budgets hold.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { HW, CARS, CAR, COVER, CREW, ARENA } from '../../shared/story/train.js';

const DIR = new URL('../../public/models/story/', import.meta.url);
const CT = { 5120: [Int8Array, 1], 5121: [Uint8Array, 1], 5122: [Int16Array, 2], 5123: [Uint16Array, 2], 5125: [Uint32Array, 4], 5126: [Float32Array, 4] }, NC = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };
// a .glb as { nodes by name: { verts: [[x, y, z]...] in the file's root space, faces: [[i, j, k]...] into verts, tris, materials, hidden, parent } }
function readGlb(name) {
  const raw = fs.readFileSync(new URL(name, DIR)), jl = raw.readUInt32LE(12), js = JSON.parse(raw.subarray(20, 20 + jl).toString('utf8')), bin = raw.subarray(20 + jl + 8);
  const acc = (i) => { const a = js.accessors[i], bv = js.bufferViews[a.bufferView], [C, sz] = CT[a.componentType], n = NC[a.type], off = (bv.byteOffset || 0) + (a.byteOffset || 0), st = bv.byteStride || sz * n, out = [];
    for (let k = 0; k < a.count; k++) { const v = new C(bin.buffer.slice(bin.byteOffset + off + k * st, bin.byteOffset + off + k * st + sz * n)); out.push(Array.from(v)); } return out; };
  const nodes = {}, parent = new Map();
  js.nodes.forEach((n, i) => { for (const c of n.children || []) parent.set(c, i); });
  const world = (i) => { let t = [0, 0, 0]; for (let k = i; k !== undefined; k = parent.get(k)) { const n = js.nodes[k]; assert.ok(!n.rotation || n.rotation.every((x, j) => Math.abs(x - (j === 3 ? 1 : 0)) < 1e-5), `${n.name}: a turned node`); assert.ok(!n.scale || n.scale.every((x) => Math.abs(x - 1) < 1e-5), `${n.name}: a scaled node`); if (n.translation) t = t.map((x, j) => x + n.translation[j]); } return t; };
  js.nodes.forEach((n, i) => {
    const o = { name: n.name, parent: parent.has(i) ? js.nodes[parent.get(i)].name : null, hidden: !!(n.extras && n.extras.jf_hidden), verts: [], faces: [], tris: 0, materials: [], extras: n.extras || {} };
    if (n.mesh !== undefined) { const t = world(i); for (const p of js.meshes[n.mesh].primitives) { const b0 = o.verts.length, ix = acc(p.indices); for (const v of acc(p.attributes.POSITION)) o.verts.push([v[0] + t[0], v[1] + t[1], v[2] + t[2]]); for (let k = 0; k < ix.length; k += 3) o.faces.push([b0 + ix[k][0], b0 + ix[k + 1][0], b0 + ix[k + 2][0]]); o.tris += ix.length / 3; o.materials.push(js.materials[p.material].name); } }
    nodes[n.name] = o;
  });
  return { nodes, size: raw.length, tris: Object.values(nodes).reduce((s, n) => s + n.tris, 0), materials: js.materials.map((m) => m.name), images: (js.images || []).length };
}
const box = (vs) => { const lo = [1e9, 1e9, 1e9], hi = [-1e9, -1e9, -1e9]; for (const v of vs) for (let i = 0; i < 3; i++) { if (v[i] < lo[i]) lo[i] = v[i]; if (v[i] > hi[i]) hi[i] = v[i]; } return { lo, hi }; };
const near = (a, b, e = 0.012) => Math.abs(a - b) <= e;
// every triangle of some nodes as its own box { lo, hi } (the cars are boards and plates: a face's box is the face)
const triBoxes = (nodes) => nodes.flatMap((n) => n.faces.map((f) => box(f.map((i) => n.verts[i]))));
const inBox = (tb, lo, hi) => tb.filter((t) => t.lo[0] < hi[0] && t.hi[0] > lo[0] && t.lo[1] < hi[1] && t.hi[1] > lo[1] && t.lo[2] < hi[2] && t.hi[2] > lo[2]);
const T = readGlb('rp_train.glb'), P = JSON.parse(fs.readFileSync(new URL('rp_train.parts.json', DIR), 'utf8'));
const under = (car, pred = () => true) => Object.values(T.nodes).filter((n) => n.parent === 'car_' + car && n.verts.length && pred(n));
const shown = (n) => !n.hidden && !/_lod$/.test(n.name);

test('the parts file: built to today\'s table, every part a node, every marker there', () => {
  assert.equal(P.table.HW, HW);
  assert.deepEqual(P.table.cars, JSON.parse(JSON.stringify(CARS)), 'the train was built to another CARS: rebuild it (tools/blender/make_rp_train.py)');
  assert.deepEqual(P.table.cover, JSON.parse(JSON.stringify(COVER)), 'the train was built to another COVER: rebuild it');
  for (const p of P.parts) { assert.ok(T.nodes[p.name], `part ${p.name} is not in rp_train.glb`); assert.equal(!!p.hidden, T.nodes[p.name].hidden, `${p.name}: hidden in one and not the other`); }
  for (const n of Object.values(T.nodes)) if (n.verts.length) assert.ok(P.parts.some((p) => p.name === n.name), `${n.name} is in the file and not in the parts list`);
  for (const c of CARS) for (const k of ['car_' + c.id, c.id + '_body', c.id + '_lod']) assert.ok(T.nodes[k], k);
  for (const k of ['flat_end', 'flat_end_bitten', 'wagon_coupling', 'wagon_tail', 'loco_headlamp', 'loco_glass', 'loco_cablamp', 'van_lamp']) assert.ok(T.nodes[k], k);
  assert.ok(T.nodes.flat_end_bitten.hidden && !T.nodes.flat_end.hidden, 'the torn end is the hidden one');
  assert.equal(T.nodes.wagon_coupling.parent, 'car_wagon', 'the wagon\'s coupling goes with the wagon');
  const m = P.markers, v3 = (a) => Array.isArray(a) && a.length === 3 && a.every(Number.isFinite);
  assert.deepEqual(m.crew.map((c) => [c.id, c.pos]), CREW.map((c) => [c.id, c.p]));
  assert.ok(v3(m.back_rail.a) && v3(m.back_rail.b) && near(m.back_rail.a[1], CAR.wagon.deck + CAR.wagon.rail) && near(m.back_rail.a[2], CAR.wagon.z0 + 0.05, 0.06), 'the back rail is at the grips\' height');
  assert.equal(m.couplings.length, 3); for (const c of m.couplings) { assert.ok(v3(c.pin) && T.nodes[c.node], 'a coupling\'s pin and node'); }
  for (const k of ['tail_lamp', 'brake_handle', 'flask', 'kettle']) assert.ok(v3(m[k]), k);
  for (const k of ['cab_seat', 'headlamp', 'work_lamp']) assert.ok(v3(m[k].pos), k);
  assert.ok(v3(m.fridge.at) && v3(m.fridge.lean.pos) && T.nodes[m.fridge.node] && v3(m.handtruck.pos), 'the fridge Jack falls against, the hand truck\'s spot');
  const L = CAR.loco; assert.ok(m.cab_seat.pos[2] > L.z0 && m.cab_seat.pos[2] < L.z0 + 2.6 && m.headlamp.pos[2] > L.z1 - 0.6, 'the seat is in the cab, the lamp on the nose');
});

test('every car fits its line of the table', () => {
  for (const c of CARS) {
    const parts = under(c.id, (n) => shown(n) && !/^cover_/.test(n.name)), b = box(parts.flatMap((n) => n.verts));
    assert.ok(parts.length, c.id);
    assert.ok(b.lo[0] >= -HW - 0.06 && b.hi[0] <= HW + 0.06, `${c.id} is ${(b.hi[0] - b.lo[0]).toFixed(2)} m wide: the deck is ${2 * HW}`);
    assert.ok(b.lo[2] >= c.z0 - 0.5 && b.hi[2] <= c.z1 + 0.62, `${c.id} runs z ${b.lo[2].toFixed(2)} .. ${b.hi[2].toFixed(2)}: its car is ${c.z0} .. ${c.z1}`); // (buffers, couplings and lamps reach into the 0.6 m gaps)
    assert.ok(b.lo[1] >= 0.15, `${c.id} goes under the rail's top (${b.lo[1].toFixed(2)})`);
    const body = T.nodes[c.id + '_body'], bb = box(body.verts);
    assert.ok(near(bb.lo[2], c.z0, 0.5) && near(bb.hi[2], c.z1, 0.62) && bb.hi[0] > HW - 0.25 - (c.id === 'loco' ? 0.2 : 0) && bb.lo[0] < -HW + 0.25 + (c.id === 'loco' ? 0.2 : 0), `${c.id}_body is its car's size`);
    const lod = box(T.nodes[c.id + '_lod'].verts);
    assert.ok(near(lod.lo[2], c.z0, 0.2) && near(lod.hi[2], c.z1, 0.2) && lod.lo[0] >= -HW - 0.02 && lod.hi[0] <= HW + 0.02 && T.nodes[c.id + '_lod'].tris <= 600, `${c.id}_lod`);
  }
  const lo = CAR.loco, lb = box(T.nodes.loco_body.verts); assert.ok(near(lb.hi[1], lo.top, 0.25), `the loco is ${lb.hi[1].toFixed(2)} high: the table says ${lo.top}`);
});

test('the decks are where you stand: at the table\'s height, the middle lane clear', () => {
  for (const id of ['wagon', 'flat', 'van']) {
    const c = CAR[id], lane = inBox(triBoxes(under(id, shown)), [-0.5, 0, c.z0 + 0.35], [0.5, c.deck + (c.under || 9) - 0.002, c.z1 - 0.35]), top = Math.max(...lane.map((t) => t.hi[1]));
    assert.ok(near(top, c.deck, 0.006), `${id}: the top of what is in the middle lane is ${top.toFixed(3)}, the deck is ${c.deck}`);
    const boards = lane.filter((t) => near(t.lo[1], c.deck, 0.002) && near(t.hi[1], c.deck, 0.002)), cover = boards.reduce((s, t) => s + (Math.min(t.hi[2], c.z1 - 0.35) - Math.max(t.lo[2], c.z0 + 0.35)) * 1 / 2, 0);
    assert.ok(cover > (c.z1 - c.z0 - 0.7) * 0.9, `${id}: the lane is decked from end to end (${cover.toFixed(2)} m of ${(c.z1 - c.z0 - 0.7).toFixed(2)})`);
  }
  // the flatbed's and the van's decks reach the edge (HW): a foot on the table's deck is on the model's
  for (const id of ['flat', 'van']) { const c = CAR[id], vs = T.nodes[id + '_body'].verts.filter((v) => near(v[1], c.deck, 0.002)); assert.ok(Math.max(...vs.map((v) => v[0])) >= HW - 0.002 && Math.min(...vs.map((v) => v[0])) <= -HW + 0.002, `${id}: the deck reaches the edge`); }
});

test('the wagon: a rail round three sides at the grips\' height, open to the flatbed', () => {
  const c = CAR.wagon, vs = T.nodes.wagon_body.verts, y = c.deck + c.rail, tb = triBoxes([T.nodes.wagon_body]);
  assert.ok(near(Math.max(...vs.map((v) => v[1])), y, 0.006), `the wagon's top is ${Math.max(...vs.map((v) => v[1])).toFixed(3)}: the rail is ${y}`);
  for (const sx of [1, -1]) for (const k of [0.15, 0.5, 0.85]) { const z = c.z0 + (c.z1 - c.z0) * k, x = sx * (HW - 0.05); assert.ok(inBox(tb, [x - 0.06, y - 0.02, z - 0.1], [x + 0.06, y + 0.01, z + 0.1]).length, `the rail is at the side grip ${sx} ${k}`); }
  for (const sx of [1, -1]) assert.ok(inBox(tb, [sx * 0.9 - 0.1, y - 0.02, c.z0], [sx * 0.9 + 0.1, y + 0.01, c.z0 + 0.1]).length, 'the rail is at the back grips');
  assert.equal(inBox(tb, [-HW + 0.6, c.deck + 0.12, c.z1 - 0.4], [HW - 0.6, 9, c.z1 + 0.3]).length, 0, 'nothing across the wagon\'s front: you walk onto the flatbed');
  assert.equal(inBox(tb, [-HW + 0.2, c.deck + 0.42, c.z0 + 0.3], [HW - 0.2, 9, c.z1 - 0.3]).length, 0, 'nothing inside it tall enough to hide behind that the room has no box for');
  assert.equal(inBox(tb, [-1.2, c.deck + 0.12, c.z0 + 0.3], [1.2, 9, c.z1 - 0.3]).length, 0, 'and nothing to trip on away from its sides');
});

test('the van: the table\'s steps, four posts, 2 m of headroom, a flat roof', () => {
  const c = CAR.van, parts = under('van', (n) => shown(n) && !/^cover_/.test(n.name)), tb = triBoxes(parts), rise = (c.roof - c.deck) / c.stairs, run = (c.roofZ0 - c.z0) / c.stairs, yU = c.deck + c.under;
  for (let k = 0; k < c.stairs; k++) {
    const y = c.deck + (k + 1) * rise, lo = [-HW + 0.1, c.deck, c.z0 + k * run + 0.08], hi = [-HW + c.stairW - 0.1, y + 0.5, c.z0 + (k + 1) * run - 0.08], top = Math.max(...inBox(tb, lo, hi).map((t) => t.hi[1]));
    assert.ok(near(top, y, 0.006), `step ${k + 1} is at ${top.toFixed(3)}: the table has ${y.toFixed(3)}`);
  }
  const tread = inBox(tb, [-HW - 1, c.deck + rise - 0.003, c.z0 - 1], [HW, c.deck + rise + 0.003, c.z0 + run - 0.02]).filter((t) => near(t.lo[1], t.hi[1], 0.001));
  assert.ok(near(Math.max(...tread.map((t) => t.hi[0])), -HW + c.stairW, 0.006) && near(Math.min(...tread.map((t) => t.lo[0])), -HW, 0.006) && near(Math.min(...tread.map((t) => t.lo[2])), c.z0, 0.01), 'the steps are stairW wide and start at the car\'s end');
  // headroom: from just over the deck to the roof's underside, nothing between the posts but what is against the sides
  const mid = inBox(tb, [-HW + 0.5, c.deck + 0.12, c.roofZ0 + 0.3], [HW - 0.5, yU - 0.002, c.z1 - 0.3]);
  assert.equal(mid.length, 0, `${mid.length} faces of the van hang in the 2 m under its roof, e.g. ${JSON.stringify(mid[0])}`);
  for (const sx of [-1, 1]) for (const z of [c.roofZ0, c.z1 - 0.14]) { const x = sx * (HW - 0.07); assert.ok(inBox(tb, [x - 0.08, c.deck + 0.6, z - 0.01], [x + 0.08, yU - 0.5, z + 0.15]).filter((t) => t.lo[1] < c.deck + 0.05 && t.hi[1] > yU - 0.05).length >= 4, `a post at ${sx} ${z}`); }
  const roof = inBox(tb, [-HW + 0.25, yU - 0.001, c.roofZ0 + 0.3], [HW - 0.25, 99, c.z1 - 0.25]);
  assert.ok(near(Math.max(...roof.map((t) => t.hi[1])), c.roof, 0.004), `the roof's top is ${Math.max(...roof.map((t) => t.hi[1])).toFixed(3)}: the table has ${c.roof} (nothing stands on it away from its edges)`);
  assert.ok(near(Math.min(...roof.map((t) => t.lo[1])), yU, 0.004), 'its underside is 2 m over the deck');
});

test('each cover piece fills its COVER box', () => {
  const k = {};
  for (const [i, [car, x, z, w, h, d]] of COVER.entries()) {
    const j = k[car] = (k[car] ?? -1) + 1, n = T.nodes[`cover_${car}_${j}`], y = CAR[car].deck;
    assert.ok(n && n.verts.length && n.parent === 'car_' + car, `cover_${car}_${j}`);
    const b = box(n.verts), lo = [x - w / 2, y, z - d / 2], hi = [x + w / 2, y + h, z + d / 2];
    for (let a = 0; a < 3; a++) {
      assert.ok(b.lo[a] >= lo[a] - 0.03 && b.hi[a] <= hi[a] + 0.03, `cover ${i} (${n.name}) pokes out of its box on axis ${a}: ${b.lo[a].toFixed(3)} .. ${b.hi[a].toFixed(3)} against ${lo[a]} .. ${hi[a]}`);
      assert.ok(b.hi[a] - b.lo[a] >= (hi[a] - lo[a]) * 0.93, `cover ${i} (${n.name}) is smaller than what you bump into on axis ${a}`);
    }
    const p = P.parts.find((q) => q.name === n.name); assert.equal(p.cover, i); assert.ok(near(p.pivot[0], x) && near(p.pivot[1], y) && near(p.pivot[2], z), `${n.name}: its origin is the middle of its foot`);
  }
  assert.equal(P.parts.filter((p) => p.kind === 'fridge').length, 1); assert.equal(P.markers.fridge.node, P.parts.find((p) => p.kind === 'fridge').name);
});

test('the bitten end takes nothing of the deck away', () => {
  const c = CAR.flat, b = box(T.nodes.flat_end_bitten.verts);
  assert.ok(b.hi[1] <= c.deck + 0.12 && b.hi[2] <= c.z0 + 1.5 && b.lo[2] >= c.z0 - 0.75 && Math.abs(b.lo[0]) <= HW + 0.3 && Math.abs(b.hi[0]) <= HW + 0.3, JSON.stringify(b));
  assert.ok(Math.max(...T.nodes.flat_end_bitten.verts.filter((v) => v[2] > c.z0 + 0.12).map((v) => v[1])) <= c.deck + 0.012, 'over the deck it is only scratches');
});

test('budgets: triangles, materials, size', () => {
  const tr = (car) => under(car, shown).reduce((s, n) => s + n.tris, 0), whole = CARS.reduce((s, c) => s + tr(c.id), 0);
  assert.ok(whole >= 30000 && whole <= 60000, `the four cars are ${whole} triangles`);
  assert.deepEqual(T.materials.slice().sort(), ['tr_atlas', 'tr_glass', 'tr_headlamp', 'tr_tail', 'tr_worklamp']);
  for (const n of Object.values(T.nodes)) if (n.verts.length) assert.ok(n.materials.length === 1, `${n.name} is one material (one draw call)`);
  const sizes = ['rp_train.glb', 'rp_tunnel.glb', 'rp_commuter.glb'].map((f) => fs.statSync(new URL(f, DIR)).size);
  assert.ok(sizes.reduce((a, b) => a + b, 0) < 4.3e6, `the three files are ${(sizes.reduce((a, b) => a + b, 0) / 1e6).toFixed(2)} MB`);
});

test('the tunnel kit: pieces that tile, at the bore\'s size', () => {
  const K = readGlb('rp_tunnel.glb'), R = ARENA.boreR, cy = ARENA.cy;
  for (const k of ['tk_lining', 'tk_lining_b', 'tk_niche', 'tk_track', 'tk_track_far', 'tk_cables', 'tk_bulbs', 'tk_bulb_lit', 'tk_bulb_dead', 'tk_phone', 'tk_marker', 'tk_signal', 'tp_portal']) assert.ok(K.nodes[k] && K.nodes[k].verts.length, k);
  for (const k of ['tk_lining', 'tk_lining_b', 'tk_niche', 'tk_track', 'tk_track_far', 'tk_cables']) { const b = box(K.nodes[k].verts); assert.ok(near(b.lo[2], 0, 0.02) && near(b.hi[2], 6, 0.02), `${k} is 6 m long (${b.lo[2].toFixed(2)} .. ${b.hi[2].toFixed(2)})`); assert.ok(K.nodes[k].tris <= 1500, `${k}: ${K.nodes[k].tris} triangles`); }
  { const b = box(K.nodes.tk_bulbs.verts); assert.ok(near(b.lo[2], 0, 0.3) && near(b.hi[2], 12, 0.05), 'the bulb string runs 12 m'); }
  const rad = K.nodes.tk_lining.verts.map((v) => Math.hypot(v[0], v[1] - cy));
  assert.ok(near(Math.max(...rad), R, 0.02) && Math.min(...rad) > R - 0.2, `the lining is the ${2 * R} m bore (${Math.min(...rad).toFixed(2)} .. ${Math.max(...rad).toFixed(2)})`);
  assert.ok(near(Math.min(...K.nodes.tk_lining.verts.map((v) => v[1])), 0, 0.05), 'it comes down to the track bed');
  for (const k of ['tk_track', 'tk_track_far']) { const bed = K.nodes[k].verts.filter((v) => Math.abs(v[0]) < 1.6), rails = bed.filter((v) => v[1] > 0.19);
    assert.ok(rails.length && rails.every((v) => Math.abs(Math.abs(v[0]) - 0.75) < 0.07), `${k}: the rails are where the room's are`);
    assert.ok(near(Math.max(...bed.map((v) => v[1])), P.table.rail_y, 0.004), `${k}: the rail's top is what the wheels were built to`); }
  assert.deepEqual(K.nodes.tk_bulb_lit.materials, ['tk_bulb_on']); assert.deepEqual(K.nodes.tk_bulb_dead.materials, ['tk_bulb_off']);
  for (const p of P.tunnel.parts) assert.ok(K.nodes[p.name] && K.nodes[p.name].verts.length, `the parts file's ${p.name} is not in rp_tunnel.glb`); // (trainset.js looks the pieces up by these names)
  for (const n of Object.values(K.nodes)) if (n.verts.length) assert.ok(P.tunnel.parts.some((p) => p.name === n.name), `${n.name} is in rp_tunnel.glb and not in the parts file`);
  const wheels = Math.min(...T.nodes.wagon_body.verts.map((v) => v[1])); assert.ok(wheels > P.table.rail_y - 0.04 && wheels < P.table.rail_y + 0.01, `the wheels stand on the rail (${wheels.toFixed(3)})`);
});

test('the dead commuter train: one carriage, its ends, a far one', () => {
  const C = readGlb('rp_commuter.glb');
  for (const k of ['cm_car', 'cm_end', 'cm_end_torn', 'cm_glass', 'cm_lod']) assert.ok(C.nodes[k] && C.nodes[k].verts.length, k);
  assert.ok(C.nodes.cm_end_torn.hidden && C.nodes.cm_lod.hidden);
  for (const p of P.commuter.parts) assert.ok(C.nodes[p.name] && C.nodes[p.name].verts.length, `the parts file's ${p.name} is not in rp_commuter.glb`);
  assert.ok(C.nodes.cm_car.tris + C.nodes.cm_end.tris + C.nodes.cm_glass.tris <= 6000, `a carriage is ${C.nodes.cm_car.tris + C.nodes.cm_end.tris + C.nodes.cm_glass.tris} triangles`);
  assert.ok(C.nodes.cm_lod.tris <= 600, `far: ${C.nodes.cm_lod.tris}`);
  const b = box(C.nodes.cm_car.verts.concat(C.nodes.cm_end.verts)); assert.ok(b.hi[2] - b.lo[2] <= 20.0 && b.hi[2] - b.lo[2] > 19, 'a carriage fits its 20 m pitch');
});
