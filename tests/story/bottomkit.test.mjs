// node tests/story/bottomkit.test.mjs : the Bottom's Blender kit (kit.js cubeKit / stairKit, bottom.js dress and the
// Long Stairs pieces) is look only. Built with the kit on and off: every box, light, trigger and mark is the same and
// every older prop is still there in the same order, so the kit's randoms never touch the generator's own stream.
// Also: the models exist, borders agree, the count per chunk stays in budget, roof junk stands clear of marks and lines
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { buildChunk, packChunk, chunkBoxes, hashChunk } from '../../shared/city/chunk.js';
import '../../shared/city/slice.js';
import { CITIES, CHUNK, MAT_ID } from '../../shared/city/plan.js';
import { KIT, KIT_SIZE, paintOf } from '../../shared/city/kit.js';

const KIT_IDS = ['cube_corner', 'cube_eave', 'cube_window_a', 'cube_window_b', 'cube_window_c', 'container_doors', 'container_rib', 'cube_roofjunk_a', 'cube_roofjunk_b',
  'stair_step', 'stair_post', 'longstep_a', 'longstep_b', 'longrail', 'longpole', 'longplaque_a', 'longplaque_b',
  'cube_corner_b', 'cube_eave_b', 'cube_eave4', 'cube_eave6', 'container_rib_half', 'longrail_b', 'longpole_b']; // (the second line: the kit's second pass)
const UNUSED = ['longpole', 'cube_eave']; // (longpole stands on the ground beside a rail, and the Long Stairs' poles stand in the rail: they are all longpole_b. cube_eave is the 2 m lip with a rag: the 6 m one carries the rags now)
const isKit = (p) => KIT_IDS.includes(p[0]);
const C = CITIES.slice, all = [];
for (let cz = C.cz0; cz < C.cz1; cz++) for (let cx = C.cx0; cx < C.cx1; cx++) all.push([cx, cz]);
const build = (on) => { KIT.on = on; const m = new Map(); for (const [cx, cz] of all) m.set(cx + ',' + cz, buildChunk('slice', cx, cz)); KIT.on = true; return m; };
const ON = build(true), OFF = build(false);

// 1. look only: nothing but props differs, and the old props keep their order
let kit = 0, nCol = 0;
const used = new Set(), perChunk = [];
for (const [id, a] of ON) {
  const b = OFF.get(id), pa = packChunk(a), pb = packChunk(b);
  assert.deepEqual(chunkBoxes(pa), chunkBoxes(pb), 'collision boxes changed in chunk ' + id);
  nCol += chunkBoxes(pa).length;
  for (const f of ['boxes', 'deco', 'shapes', 'lanes', 'spawns', 'triggers', 'marks', 'lights']) assert.deepEqual(a[f], b[f], f + ' changed in chunk ' + id);
  assert.deepEqual(a.props.filter((p) => !isKit(p)), b.props, 'an older prop moved in chunk ' + id);
  assert.ok(!b.props.some(isKit), 'kit off still places kit props');
  const n = a.props.filter(isKit).length; kit += n;
  for (const p of a.props) if (isKit(p)) used.add(p[0]);
  const inBottom = a.cz >= 0 && a.cx < 2; // (the Bottom is x < 96, z >= 0)
  if (!inBottom) assert.equal(n, 0, 'kit props outside the Bottom, chunk ' + id);
  else perChunk.push(n);
  assert.equal(hashChunk(pa), hashChunk(packChunk(buildChunk('slice', a.cx, a.cz))), 'chunk ' + id + ' is not deterministic');
}
// 2. every piece is used, and has a model with a far copy listed
const index = JSON.parse(fs.readFileSync(new URL('../../public/models/story/index.json', import.meta.url), 'utf8'));
for (const id of KIT_IDS) { assert.ok(used.has(id) || UNUSED.includes(id), id + ' is never placed'); assert.ok(index.includes('s_' + id), 's_' + id + ' is not in index.json'); }
// 2b. the sizes the placement works from (kit.js KIT_SIZE) are the sizes the models were built to (each .glb's 'jf' meta)
const meta = (id) => { const b = fs.readFileSync(new URL('../../public/models/story/s_' + id + '.glb', import.meta.url)), j = JSON.parse(b.subarray(20, 20 + b.readUInt32LE(12)).toString()); return JSON.parse(j.nodes.find((n) => n.extras && n.extras.jf).extras.jf); };
assert.equal(meta('cube_corner').h, KIT_SIZE.corner); assert.equal(meta('cube_corner_b').h, KIT_SIZE.corner);
assert.deepEqual([meta('container_rib').size[1], meta('container_rib_half').size[1]], [KIT_SIZE.rib, KIT_SIZE.rib]);
assert.deepEqual([meta('container_rib').size[0], meta('container_rib_half').size[0]], KIT_SIZE.ribW);
assert.deepEqual(meta('container_doors').size, KIT_SIZE.doors);
assert.deepEqual([meta('cube_eave6').run, meta('cube_eave4').run, meta('cube_eave_b').run], KIT_SIZE.eave); assert.equal(meta('cube_eave').run, 2);
assert.deepEqual([meta('cube_eave6').rag, meta('cube_eave4').rag, meta('cube_eave_b').rag, meta('cube_eave').rag], [true, false, false, true]);
assert.deepEqual([meta('longrail').climb, meta('longrail_b').climb], KIT_SIZE.rail);
assert.deepEqual([meta('longpole_b').h, ...meta('longpole_b').frame], KIT_SIZE.poleB);
// 2c. the client knows every piece: a draw distance (FAR) or a detail share, an empty stand-in, and the same paint list
const propsJs = fs.readFileSync(new URL('../../public/js/city/props.js', import.meta.url), 'utf8'), codeJs = fs.readFileSync(new URL('../../public/js/city/propcode.js', import.meta.url), 'utf8');
for (const id of KIT_IDS) { assert.ok(new RegExp('\\b' + id + ': [\\d.]+').test(propsJs) || /^long(pole|step|rail)/.test(id), id + ' has no FAR / DETAIL entry in props.js'); assert.ok(codeJs.includes("'" + id + "'"), id + ' has no stand-in in propcode.js'); }
const paints = eval(/const PAINTS = (\[[^\]]+\])/.exec(propsJs)[1]);
assert.deepEqual(paints.slice(8), [0xff9a4d, 0x9a7aff]); // (the containers' orange and purple, after the eight that variant numbers wrap over)
assert.deepEqual([0xff7a9a, 0x5fd3c6, 0xffd24d, 0x9a7aff, 0xff9a4d].map((t) => paintOf(t)[0]), [6, 7, 5, -2, -1]); // every container colour has its paint
for (const o of ON.values()) for (const p of o.props) assert.ok(p[6] >= -2 && Number.isInteger(p[6]) || !isKit(p), 'a paint variant props.js cannot draw: ' + p);
// 3. borders: four chunks built one by one hold the same kit props as the same ground built in one piece
const rect = buildChunk('slice', 0, 0, [-2 * CHUNK, 2 * CHUNK, 0, 4 * CHUNK]);
const key = (p) => p.map((v) => (typeof v === 'number' ? Math.fround(v) : v)).join(',');
const one = rect.props.filter(isKit).map(key).sort(), four = [];
for (const [cx, cz] of [[-2, 2], [-1, 2], [-2, 3], [-1, 3]]) four.push(...ON.get(cx + ',' + cz).props.filter(isKit).map(key));
assert.deepEqual(four.sort(), one, 'the kit differs across a chunk border');
// 4. budget (a prop is one instance; the far copies are 12-224 triangles): see docs/story/world/BOTTOM_KIT_PLACEMENT.md
const avg = kit / perChunk.length, max = Math.max(...perChunk);
assert.ok(avg <= 380 && max <= 620, `kit props per Bottom chunk: avg ${avg.toFixed(0)}, max ${max}`);
// 5. roof junk and plaques keep out of the way: nothing within 2.5 m of a mark (quests, grapple rings, crowd spots) or a
// zipline's ends, one of each plaque, on the Long Stairs and well away from the quest spot at its foot
const marks = [], zips = [];
for (const o of ON.values()) { for (const m of o.marks) if (m.id !== 'crowd') marks.push(m.p); for (const t of o.triggers) if (t.kind === 'zip') zips.push(t.a, t.b); }
const near = (p, list, d) => list.some((q) => Math.hypot(q[0] - p[1], q[1] - p[2], q[2] - p[3]) < d);
let junk = 0;
for (const o of ON.values()) for (const p of o.props) if (/^cube_roofjunk/.test(p[0])) { junk++; assert.ok(!near(p, marks, 2.5) && !near(p, zips, 2.5), 'roof junk in the way at ' + p.slice(1, 4)); }
const plq = [...ON.values()].flatMap((o) => o.props.filter((p) => /^longplaque/.test(p[0])));
assert.equal(plq.length, 2); assert.notEqual(plq[0][0], plq[1][0]);
const foot = [...ON.values()].flatMap((o) => o.marks).find((m) => m.id === 'bottom:long_stairs').p;
for (const p of plq) assert.ok(p[1] > -48 && p[1] < -40 && Math.hypot(p[1] - foot[0], p[3] - foot[2]) > 20, 'a plaque is off the stairs or on the quest spot');
// 6. every piece sits on something solid, the right way round: probe points in the model's frame (front = -z), turned
// into the world, must be inside a collision box (the wall behind a window, the step under a tread, the rail under a coping)
const IN = { cube_corner_b: [[-0.5, 1, 0.1], [-0.1, 1, 0.5]], cube_eave_b: [[0, -0.15, 0.1], [0.8, -0.15, 0.1]], cube_eave4: [[0, -0.15, 0.1], [1.6, -0.15, 0.1], [-1.6, -0.15, 0.1]],
  cube_eave6: [[0, -0.15, 0.1], [2.6, -0.15, 0.1], [-2.6, -0.15, 0.1]], container_rib_half: [[0, 1.4, 0.1]], longrail_b: [[0, -0.1, -1.2]], longpole_b: [[0, -0.3, 0], [0, 2, 0]],
  cube_window_a: [[0, -0.3, 0.1]], cube_window_b: [[0, -0.3, 0.1]], cube_window_c: [[0, -0.3, 0.1]], cube_eave: [[0, -0.15, 0.1], [0, 0.1, 0.05]], cube_corner: [[0.5, 1, 0.1], [0.1, 1, 0.5]],
  container_rib: [[0, 1.4, 0.1]], container_doors: [[0, 1.3, 0.1], [-1, 0.5, 0.1], [1, 2.2, 0.1]], cube_roofjunk_a: [[0, -0.1, 0]], cube_roofjunk_b: [[0, -0.1, 0]], stair_step: [[0, -0.1, 0.27]],
  longstep_a: [[0, -0.05, -0.4]], longstep_b: [[0, -0.05, -0.4]], longrail: [[0, -0.1, -1.2]], longpole: [[0, 3, 0]], longplaque_a: [[0, -0.05, 0]], longplaque_b: [[0, -0.05, 0]] };
const grid = new Map(), CELL = 8;
for (const o of ON.values()) for (const b of chunkBoxes(packChunk(o))) for (let i = Math.floor(b.min[0] / CELL); i <= Math.floor(b.max[0] / CELL); i++) for (let j = Math.floor(b.min[2] / CELL); j <= Math.floor(b.max[2] / CELL); j++) { const g = i + ',' + j; if (!grid.has(g)) grid.set(g, []); grid.get(g).push(b); }
const solid = (x, y, z) => (grid.get(Math.floor(x / CELL) + ',' + Math.floor(z / CELL)) || []).some((b) => x > b.min[0] && x < b.max[0] && y > b.min[1] && y < b.max[1] && z > b.min[2] && z < b.max[2]);
for (const o of ON.values()) for (const p of o.props) for (const m of IN[p[0]] || []) {
  const c = Math.cos(p[4]), s = Math.sin(p[4]);
  assert.ok(solid(p[1] + (m[0] * c + m[2] * s) * p[5], p[2] + m[1] * p[5], p[3] + (-m[0] * s + m[2] * c) * p[5]), p[0] + ' is not on a wall / step at ' + p.slice(1, 4).map((v) => v.toFixed(1)));
}
// 7. nothing stands proud of its roof: a corner post or a rib strip tops out inside the slab over its wall (the piece's
// top, 0.1 m in, is inside a box), and each lamp post's neon box sits in its sign frame
for (const o of ON.values()) for (const p of o.props) {
  const H = /^cube_corner/.test(p[0]) ? KIT_SIZE.corner : /^container_rib/.test(p[0]) ? KIT_SIZE.rib : 0; if (!H) continue;
  const c = Math.cos(p[4]), s = Math.sin(p[4]), m = [/corner_b/.test(p[0]) ? -0.5 : /corner/.test(p[0]) ? 0.5 : 0, H - 0.02, 0.05];
  assert.ok(solid(p[1] + (m[0] * c + m[2] * s) * p[5], p[2] + m[1] * p[5], p[3] + (-m[0] * s + m[2] * c) * p[5]), p[0] + ' pokes over its roof at ' + p.slice(1, 4).map((v) => v.toFixed(1)));
}
const NEON = ['neon', 'cyanglow', 'greenglow'].map((n) => MAT_ID[n]); let framed = 0;
for (const o of ON.values()) for (const p of o.props) if (p[0] === 'longpole_b') {
  const dir = Math.abs(p[4]) < 0.1 ? -1 : 1; // (the arm reaches -x, or +x when turned round)
  const box = o.boxes.find((b) => NEON.includes(b[6]) && Math.abs(b[1] - (p[2] + KIT_SIZE.poleB[1])) < 0.01 && Math.abs(b[4] - (p[2] + KIT_SIZE.poleB[2])) < 0.01 && b[2] < p[3] && b[5] > p[3] && (dir < 0 ? b[0] > p[1] - 1.95 && b[3] < p[1] - 0.1 : b[0] > p[1] + 0.1 && b[3] < p[1] + 1.95));
  assert.ok(box, 'no neon box in the frame of the lamp post at ' + p.slice(1, 4)); framed++;
}
assert.equal(framed, 18);
console.log(`bottom kit ok: ${kit} props over ${perChunk.length} chunks (avg ${avg.toFixed(0)}, max ${max}), ${junk} roofs with junk, ${nCol} collision boxes unchanged`);
