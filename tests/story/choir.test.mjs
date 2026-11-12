// THE GUT CHOIR (ART_BIBLE #16): the models, the face, and where they stand.
//   both glbs are cast format: every part on a joint the code skeleton has, the skirt skinned to body + legs only
//   the choir face is stretched wider than a grin; rig.sing holds the jaw open between steps; rig.gaze beats rig.look
//   the Choir Lung's stalls (cast_slice.js CHOIR): 3-5 singers, both looks, inside the lung, facing across the aisle,
//   standing room with floor under them
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from 'three';
import { CHOIR } from '../../shared/city/cast_slice.js';
import { SLICE } from '../../shared/city/slice.js';
import { CHUNK } from '../../shared/city/plan.js';
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { playerOverlap } from '../../shared/physics.js';
import { buildFace, FACES } from '../../public/js/story/face.js';
const ROOT = new URL('../../', import.meta.url).pathname;
const STD = ['body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR'];
const gltfOf = (id) => { const b = fs.readFileSync(ROOT + `public/models/cast/c_${id}.glb`); return JSON.parse(b.subarray(20, 20 + b.readUInt32LE(12)).toString('utf8')); };

for (const id of ['choir', 'choir_b']) test(`${id}: the glb is cast format, its skirt skinned to the body and legs`, () => {
  const g = gltfOf(id), names = g.nodes.filter((n) => n.mesh != null).map((n) => n.name);
  for (const n of names) { const m = /^part_([A-Za-z]+)/.exec(n); assert.ok(m && STD.includes(m[1]), `${n}: not on a joint of the code skeleton`); }
  for (const j of ['head', 'neck', 'spine', 'arm', 'armL', 'foreL', 'foreR', 'handL', 'handR', 'kneeL', 'kneeR', 'body']) assert.ok(names.some((n) => n.startsWith('part_' + j)), `nothing on ${j}`);
  assert.equal((g.skins || []).length, 1, 'one skin (the skirt)');
  assert.deepEqual(g.skins[0].joints.map((i) => g.nodes[i].name).sort(), ['body', 'legL', 'legR']);
  const skinned = g.nodes.filter((n) => n.skin != null).map((n) => n.name);
  assert.deepEqual(skinned, ['part_body_skirt']);
  const lod = g.nodes.filter((n) => /__lod/.test(n.name || '')); assert.equal(lod.length, 0);
});

test('the choir face: a smile wider than a grin, a held jaw for singing, eyes that stay on you', () => {
  assert.ok(FACES.choir.st > FACES.grin.st && FACES.choir.smile >= FACES.grin.smile, 'stretched wider than a grin');
  const head = new THREE.Group(), r = buildFace(head, { s: 1.35, mouthW: 0.105, lip: 0x9a5a7a });
  r.set('choir'); for (let i = 0; i < 40; i++) r.update(0.05);
  const shut = r.jaw.rotation.x;
  r.sing = 0.8; r.update(0.05); r.update(0.05);
  assert.ok(r.jaw.rotation.x < shut - 0.3, `sing opens the jaw (${shut} -> ${r.jaw.rotation.x})`);
  r.flap = 0; r.update(0.05); assert.ok(r.jaw.rotation.x < shut - 0.3, 'and holds it while the babble is quiet (between stop-motion steps)');
  r.sing = 0; r.update(0.05); assert.ok(Math.abs(r.jaw.rotation.x - shut) < 1e-6, 'and lets go');
  head.updateMatrixWorld(true);
  r.look = new THREE.Vector3(5, 0, -1); r.gaze = new THREE.Vector3(-5, 0, -1);
  for (let i = 0; i < 30; i++) r.update(0.05);
  assert.ok(r.eyes[0].piv.rotation.y > 0.3, 'the gaze wins over the look (to their right, +x is -yaw: ' + r.eyes[0].piv.rotation.y + ')');
});

test('the Choir Lung: the stalls, either side of the aisle, standing room', () => {
  assert.ok(CHOIR.length >= 3 && CHOIR.length <= 5, 'a small group');
  assert.deepEqual([...new Set(CHOIR.map((c) => c.look))].sort(), ['choir', 'choir_b'], 'both of them');
  const C = SLICE.choir, ring = (p) => Math.hypot((p[0] - C.x) / 21, (p[2] - (C.z - 4)) / 19); // (gut.js choir(): the colonnade)
  const W = new ChunkWorld([]);
  const cx0 = Math.floor((C.x - 30) / CHUNK), cx1 = Math.floor((C.x + 30) / CHUNK), cz0 = Math.floor((C.z - 34) / CHUNK), cz1 = Math.floor((C.z + 26) / CHUNK);
  for (let cx = cx0; cx <= cx1; cx++) for (let cz = cz0; cz <= cz1; cz++) W.set(cx + ':' + cz, chunkBoxes(packChunk(buildChunk('slice', cx, cz))));
  W.sync();
  for (const s of CHOIR) {
    assert.ok(ring(s.p) < 0.7, `${s.look} at ${s.p} is inside the lung, well clear of its columns`);
    const across = Math.sign(C.x - s.p[0]); // (west row faces east, east row faces west: across the aisle)
    assert.ok(Math.abs(-Math.sin(s.face) - across) < 1e-6 && Math.abs(Math.cos(s.face)) < 1e-6, `${s.look} at ${s.p} faces across the aisle`);
    const h = W.raycast([s.p[0], s.p[1] + 1.5, s.p[2]], [0, -1, 0], 8);
    assert.ok(h && Math.abs(h.point[1] - s.p[1]) < 0.5, `${s.p}: floor under it (${h && h.point[1]})`);
    assert.ok(!playerOverlap([s.p[0], h.point[1] + 0.05, s.p[2]], W.boxes), `${s.p}: inside something`);
  }
  for (const a of CHOIR) for (const b of CHOIR) if (a !== b) assert.ok(Math.hypot(a.p[0] - b.p[0], a.p[2] - b.p[2]) > 1.1, 'room for their robes');
  const aisle = Math.min(...CHOIR.filter((c) => c.p[0] > C.x).map((c) => c.p[0])) - Math.max(...CHOIR.filter((c) => c.p[0] < C.x).map((c) => c.p[0]));
  assert.ok(aisle > 4, 'an aisle you can walk up between them: ' + aisle);
});
