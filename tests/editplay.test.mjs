// node --max-old-space-size=256 tests/editplay.test.mjs : PLAY WITH BOTS can't hurt the server. the security review's
// crash (one 600 m box on Islands ran a 256 MB server out of memory building the bots' graph) is refused at every step
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';
import { validEdits } from '../shared/mapedit.js';
import { buildEdited, dropEdited, okEdit } from '../shared/editmaps.js';
import { buildNav } from '../shared/nav.js';
let n = 0; const t = (name, fn) => { fn(); n++; console.log('ok', name); };
const add = (min, max, extra = {}) => ({ t: 'add', items: [{ list: 'b', boxes: [{ min, max, mat: 'stone', ...extra }] }] });
const crash = add([-300, -50, -300], [300, 50, 300]);

t("the review's exact op (a 600 m box on Islands) is refused", () => {
  assert.equal(validEdits({ map: 'islands', ops: [crash] }), false);
  assert.equal(okEdit({ base: 'islands', ops: [crash] }), false);
  assert.equal(buildEdited('ed_islands_1', { base: 'islands', ops: [crash] }), null);
});
t('boxes far off the map, inside out, or over 500 m a side are refused', () => {
  for (const op of [add([5000, 0, 0], [5001, 1, 1]), add([0, 0, 0], [-1, 1, 1]), add([0, 0, 0], [501, 1, 1])]) assert.equal(validEdits({ map: 'islands', ops: [op] }), false, JSON.stringify(op));
  assert.equal(validEdits({ map: 'islands', ops: [add([0, 0, 0], [400, 1, 1])] }), true, 'a big floor is fine');
});
t('sizes stacked op after op are capped (x64 at most), and q is 0..3', () => {
  const xf = (k, q = 0) => ({ t: 'xf', sel: ['x'], o: [0, 0, 0], k, q, d: [0, 0, 0] });
  assert.equal(validEdits({ map: 'islands', ops: [xf(8), xf(8)] }), true);
  assert.equal(validEdits({ map: 'islands', ops: [xf(8), xf(8), xf(2)] }), false);
  assert.equal(validEdits({ map: 'islands', ops: [xf(1, 7)] }), false);
  assert.equal(validEdits({ map: 'islands', ops: [xf(100)] }), false);
});
t('a replay that ends up with an oversized box builds nothing', () => {
  const e = { base: 'warehouse', ops: [add([0, 0, 0], [300, 1, 300]), { t: 'xf', sel: ['b|b|stone|0,0,0|300,1,300'], o: [0, 0, 0], k: 2, q: 0, d: [0, 0, 0] }] };
  assert.equal(okEdit(e), true, 'each op on its own looks fine');
  assert.equal(buildEdited('ed_warehouse_2', e), null, 'but 600 m after both is refused');
  assert.equal(Object.hasOwn(MAPS, 'ed_warehouse_2'), false);
});
t('unknown keys never reach physics or the bots (a box claiming to be a terrain step, nested junk)', () => {
  const id = buildEdited('ed_warehouse_3', { base: 'warehouse', ops: [add([1, 0, 1], [2, 1, 2], { ter: 1, junk: { a: { b: 1 } } })] });
  assert.ok(id); const b = MAPS[id].boxes.find((x) => x.min[0] === 1 && x.min[2] === 1 && x.mat === 'stone');
  assert.ok(b && b.ter === undefined && b.junk === undefined); dropEdited(id); assert.equal(Object.hasOwn(MAPS, id), false);
  assert.equal(validEdits({ map: 'x', ops: [{ t: 'add', items: [{ list: 'b', boxes: [{ min: [0, 0, 0], max: [1, 1, 1], mat: 'x', av: 'home' }], arch: { id: 'home', p: [0, 0, 0], paint: { a: { b: 'c' } } } }] }] }), false, 'a nested paint');
});
t('the bots graph stays small even for a box much bigger than its grid (second guard in nav.js)', () => {
  const h0 = process.memoryUsage().heapUsed, t0 = Date.now();
  const g = buildNav([{ min: [-1e5, -1, -1e5], max: [1e5, 0, 1e5], mat: 'stone' }, { min: [-1e5, 0, 3], max: [1e5, 3, 4], mat: 'stone' }], { x0: 0, z0: 0, n: 60, cell: 1, levels: [0], band: 0.5 });
  assert.ok(g.nodes.length > 1000 && Date.now() - t0 < 5000, 'built, quickly'); assert.ok(process.memoryUsage().heapUsed - h0 < 200e6, 'without blowing up memory');
});
console.log(n, 'passed');
