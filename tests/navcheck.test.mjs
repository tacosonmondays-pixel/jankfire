// node tests/navcheck.test.mjs : the map editor's bot check (shared/navcheck.js) finds what an edit cuts off
import assert from 'node:assert/strict';
import { MAPS } from '../shared/map.js';
import { navCheck } from '../shared/navcheck.js';
import { indexMap, applyOp } from '../shared/mapedit.js';
const fresh = async () => (await import('../shared/map.js?v=' + Math.random())).MAPS;
let n = 0; const t = async (name, fn) => { await fn(); n++; console.log('ok', name); };

await t('an untouched map: every spot as reachable as before, nothing lost', async () => {
  const B = await fresh(), r = navCheck(MAPS.warehouse, B.warehouse);
  assert.ok(r && r.nodes > 1000 && r.reach > 0);
  assert.equal(r.spots.filter((s) => s.was && !s.ok).length, 0); assert.equal(r.lost.length, 0);
});
await t('boxing in a bomb site: the site and the floor inside are flagged', async () => {
  const def = MAPS.forest, B = await fresh(), s = def.sites[0], idx = indexMap(def);
  const [x0, , z0] = s.min, [x1, , z1] = s.max, y = s.min[1], m = 3, h = 30, w = 1;
  const wall = (a, b) => ({ min: a, max: b, mat: 'stone' });
  applyOp(def, idx, { t: 'add', items: [{ list: 'b', boxes: [wall([x0 - m - w, y - 1, z0 - m - w], [x1 + m + w, y + h, z0 - m]), wall([x0 - m - w, y - 1, z1 + m], [x1 + m + w, y + h, z1 + m + w]), wall([x0 - m - w, y - 1, z0 - m], [x0 - m, y + h, z1 + m]), wall([x1 + m, y - 1, z0 - m], [x1 + m + w, y + h, z1 + m])] }] });
  const r = navCheck(def, B.forest), site = r.spots.find((p) => p.what === 'bomb site ' + s.id);
  assert.equal(site.was, true); assert.equal(site.ok, false, 'the boxed-in site');
  assert.ok(r.lost.length > 50, 'floor inside the box: ' + r.lost.length);
});
await t('a map without a walk graph says so', () => { assert.equal(navCheck(MAPS.crate, null), null); });
console.log(n, 'passed');
