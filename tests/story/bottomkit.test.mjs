// node tests/story/bottomkit.test.mjs : the Bottom's Blender kit (kit.js cubeKit / stairKit, bottom.js dress and the
// Long Stairs pieces) is look only. Built with the kit on and off: every box, light, trigger and mark is the same and
// every older prop is still there in the same order, so the kit's randoms never touch the generator's own stream.
// Also: the models exist, borders agree, the count per chunk stays in budget, roof junk stands clear of marks and lines
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { buildChunk, packChunk, chunkBoxes, hashChunk } from '../../shared/city/chunk.js';
import '../../shared/city/slice.js';
import { CITIES, CHUNK } from '../../shared/city/plan.js';
import { KIT } from '../../shared/city/kit.js';

const KIT_IDS = ['cube_corner', 'cube_eave', 'cube_window_a', 'cube_window_b', 'cube_window_c', 'container_doors', 'container_rib', 'cube_roofjunk_a', 'cube_roofjunk_b',
  'stair_step', 'stair_post', 'longstep_a', 'longstep_b', 'longrail', 'longpole', 'longplaque_a', 'longplaque_b'];
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
for (const id of KIT_IDS) { assert.ok(used.has(id), id + ' is never placed'); assert.ok(index.includes('s_' + id), 's_' + id + ' is not in index.json'); }
// 3. borders: four chunks built one by one hold the same kit props as the same ground built in one piece
const rect = buildChunk('slice', 0, 0, [-2 * CHUNK, 2 * CHUNK, 0, 4 * CHUNK]);
const key = (p) => p.map((v) => (typeof v === 'number' ? Math.fround(v) : v)).join(',');
const one = rect.props.filter(isKit).map(key).sort(), four = [];
for (const [cx, cz] of [[-2, 2], [-1, 2], [-2, 3], [-1, 3]]) four.push(...ON.get(cx + ',' + cz).props.filter(isKit).map(key));
assert.deepEqual(four.sort(), one, 'the kit differs across a chunk border');
// 4. budget (a prop is one instance; the far copies are 12-224 triangles): see docs/story/world/BOTTOM_KIT_PLACEMENT.md
const avg = kit / perChunk.length, max = Math.max(...perChunk);
assert.ok(avg <= 560 && max <= 900, `kit props per Bottom chunk: avg ${avg.toFixed(0)}, max ${max}`);
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
console.log(`bottom kit ok: ${kit} props over ${perChunk.length} chunks (avg ${avg.toFixed(0)}, max ${max}), ${junk} roofs with junk, ${nCol} collision boxes unchanged`);
