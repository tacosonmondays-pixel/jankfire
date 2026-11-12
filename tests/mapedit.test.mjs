// node tests/mapedit.test.mjs : the map editor's edit model (shared/mapedit.js). every map indexes into things, an
// edit replays to the same layout on a fresh build, undo puts it back exactly, a remodelled map reports stale ops
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';
import { indexMap, bySig, pivotOf, applyOp, applyEdits, xfThing, xfUndo, thingData, validEdits, canScale } from '../shared/mapedit.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };
const snap = (def) => JSON.stringify([def.boxes, def.boxes.props, def.boxes.arch, def.deco, def.deco && def.deco.props]);
const fresh = async () => (await import('../shared/map.js?v=' + Math.random())).MAPS; // a second build of every map

t('every map indexes: each box in one thing, each prop with boxes or a look-only model, signatures unique', () => {
  for (const [id, def] of Object.entries(MAPS)) {
    if (def.stream) continue;
    const idx = indexMap(def), look = bySig(idx);
    assert.equal(look.size, idx.things.length, id + ': a signature per thing');
    const seen = new Set();
    for (const th of idx.things) for (const b of th.boxes) { assert.ok(!seen.has(b), id + ': a box in two things'); seen.add(b); }
    const free = def.boxes.filter((b) => !b.ter && !seen.has(b));
    assert.equal(free.length, 0, id + ': boxes that are in no thing');
  }
});

const ops = [];
t('move + turn + size + delete + copy on Warehouse, then undo the moves exactly', () => {
  const def = MAPS.warehouse, idx = indexMap(def), before = snap(def);
  const look = bySig(idx), props = idx.things.filter((x) => x.kind === 'prop' && x.boxes.length), boxes = idx.things.filter((x) => x.kind === 'box');
  const a = props[3], b = boxes[40];
  for (const [th, k, q, d] of [[a, 1, 1, [4, 0, -2]], [b, 1.21, 3, [0.5, 1, 0]]]) {
    const op = { t: 'xf', sel: [look.sig.get(th)], o: pivotOf(th), k, q, d };
    ops.push(op); assert.ok(applyOp(def, idx, op).ok);
  }
  const u1 = xfUndo(ops[1].o, ops[1].k, ops[1].q, ops[1].d), u0 = xfUndo(ops[0].o, ops[0].k, ops[0].q, ops[0].d);
  xfThing(b, ...u1); xfThing(a, ...u0);
  const r = (s) => JSON.stringify(JSON.parse(s, (k, v) => (typeof v === 'number' ? Math.round(v * 1000) / 1000 : v))); // (float dust: edits round to 0.1 mm)
  assert.ok(r(snap(def)) === r(before), 'undo puts every box and placement back');
  xfThing(a, ops[0].o, ops[0].k, ops[0].q, ops[0].d); xfThing(b, ops[1].o, ops[1].k, ops[1].q, ops[1].d); // (redo)
  const look2 = bySig(idx), c = props[10];
  ops.push({ t: 'add', items: [thingData(c)] }); applyOp(def, idx, ops[2], look2);
  ops.push({ t: 'del', sel: [look2.sig.get(props[20])] }); assert.ok(applyOp(def, idx, ops[3], look2).ok);
  assert.ok(validEdits({ map: 'warehouse', ops }), 'its own ops pass the checks');
});

const MAPS2 = await fresh();
t('the same ops on a fresh build of Warehouse give the same map', () => {
  const r = applyEdits(MAPS2.warehouse, { map: 'warehouse', ops });
  assert.equal(r.stale.length, 0);
  assert.ok(snap(MAPS2.warehouse) === snap(MAPS.warehouse), 'replayed map differs');
});

t('a quarter turn keeps boxes exact boxes (sizes swap, nothing grows)', () => {
  const def = MAPS2.desert, idx = indexMap(def), th = idx.things.find((x) => x.kind === 'prop' && x.boxes.length > 2);
  const sz = (b) => [0, 1, 2].map((i) => +(b.max[i] - b.min[i]).toFixed(4));
  const s0 = th.boxes.map(sz); xfThing(th, pivotOf(th), 1, 1, [0, 0, 0]);
  th.boxes.forEach((b, i) => assert.deepEqual(sz(b), [s0[i][2], s0[i][1], s0[i][0]]));
});

t('buildings move and turn but never scale', () => {
  const def = MAPS2.suburb, idx = indexMap(def), th = idx.things.find((x) => x.kind === 'arch');
  assert.ok(th && th.boxes.length > 4 && !canScale(th));
  const p0 = [...th.arch.p], r0 = th.arch.r; xfThing(th, pivotOf(th), 2, 1, [3, 0, 0]);
  assert.deepEqual(th.arch.p, [p0[0] + 3, p0[1], p0[2]]); assert.equal(th.arch.r, (r0 - 1) & 3);
});

t('ops whose thing is gone (a remodelled map) come back as stale, the rest still apply', () => {
  const def = MAPS2.crate, idx = indexMap(def), th = idx.things[5], look = bySig(idx);
  const e = { map: 'crate', ops: [{ t: 'del', sel: ['b|b|stone|999,0,999|1000,1,1000'] }, { t: 'xf', sel: [look.sig.get(th)], o: pivotOf(th), k: 1, q: 0, d: [0, 2, 0] }] };
  const r = applyEdits(def, e);
  assert.equal(r.stale.length, 1); assert.equal(r.stale[0].op, e.ops[0]);
});

t('broken or hostile edit files are refused', () => {
  for (const e of [null, {}, { map: 'x', ops: 'no' }, { map: 'x', ops: [{ t: 'nuke' }] }, { map: 'x', ops: [{ t: 'xf', sel: ['a'], o: [0, 0, 0], k: 1, q: 0, d: [NaN, 0, 0] }] },
    { map: 'x', ops: [{ t: 'xf', sel: ['a'], o: [0, 0, 0], k: 0, q: 0, d: [0, 0, 0] }] }, { map: 'x', ops: [{ t: 'add', items: [{ boxes: [{ min: [0, 0], max: [1, 1, 1], mat: 'x' }] }] }] },
    { map: 'x', ops: [{ t: 'add', items: [{ boxes: [{ min: [0, 0, 0], max: [1, 1, 1e9], mat: 'x' }] }] }] }, { map: 'x', ops: new Array(5001).fill({ t: 'del', sel: [] }) }]) assert.equal(validEdits(e), false, JSON.stringify(e).slice(0, 80));
});
console.log(n, 'passed');
