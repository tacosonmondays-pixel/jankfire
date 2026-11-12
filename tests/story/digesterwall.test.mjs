// node tests/story/digesterwall.test.mjs : the Digester Wall set piece (act1set.js DIGESTER, public/models/story/
// s_digester_wall.glb, tools/blender/make_story_digester_wall.py). It is placed once, facing the avenue; the office's own
// skin slabs, its door and the lung sunk in the block behind Dot are gone from that face (all look only: the gameplay
// boxes and the lung's bounce stay); the model's niches are where Dot and Mina stand (cast_slice.js), and both stand on
// the street; the file is listed, breathes, has a far copy and a code stand-in.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { buildChunk, packChunk, chunkBoxes } from '../../shared/city/chunk.js';
import { ChunkWorld } from '../../shared/city/world.js';
import { CHUNK, MAT_ID } from '../../shared/city/plan.js';
import { DIGESTER } from '../../shared/city/act1set.js';
import { NPC_SPOTS } from '../../shared/city/cast_slice.js';

const [ax, ay, az] = DIGESTER.at, [f0, f1] = DIGESTER.face;
const cx = Math.floor(ax / CHUNK), cz = Math.floor(az / CHUNK);
const near = [];
for (let i = cx - 1; i <= cx + 1; i++) for (let j = cz - 1; j <= cz + 1; j++) near.push(buildChunk('slice', i, j));
const here = near.find((c) => c.cx === cx && c.cz === cz);

// 1. placed once, at its spot, facing the avenue (+z)
const walls = near.flatMap((c) => c.props.filter((p) => p[0] === 'digester_wall'));
assert.equal(walls.length, 1, 'one digester wall');
assert.deepEqual(walls[0].slice(1, 5), [ax, ay, az, DIGESTER.yaw]);
assert.equal(DIGESTER.yaw, Math.PI);
// 2. nothing of the office pokes through it: its skin slabs, its door (a tongue, where Dot is), the buried lung pad
const onFace = (x, z) => x > f0 && x < f1 && Math.abs(z - az) < 0.3;
for (const c of near) {
  assert.ok(!c.props.some((p) => (p[0] === 'tongue' || p[0] === 'sphincter') && onFace(p[1], p[3])), 'a door on the wall face');
  assert.ok(!c.props.some((p) => p[0] === 'lung' && p[1] > f0 && p[1] < f1 && p[3] < az - 0.5), 'the lung sunk in the block shows through');
  const skin = new Set([MAT_ID.flesh, MAT_ID.liver, MAT_ID.fat]);
  assert.ok(!c.boxes.some((b) => (b[7] & 1) && skin.has(b[6]) && b[2] > az - 0.1 && b[5] < az + 0.3 && b[3] > f0 && b[0] < f1), 'a skin slab on the wall face');
}
// ...but the gameplay round it is untouched: the office block, the lung pad's hidden step and its bounce
const cols = chunkBoxes(packChunk(here));
assert.ok(cols.some((b) => b.min[2] < az - 30 && Math.abs(b.max[2] - az) < 1e-3 && b.min[0] <= f0 && b.max[0] >= f1), 'the office block is still solid');
assert.ok(cols.some((b) => b.mat === 'flesh' && Math.abs(b.max[1] - (ay + 0.7)) < 0.01 && b.max[2] > az), 'the lung pad step is still there');
assert.ok(near.some((c) => c.triggers.some((t) => t.kind === 'bounce' && t.box[0] < ax && t.box[3] > ax && t.box[5] > az)), 'the lung pad still bounces');
// 3. the niches are where the two of them are, and they stand on the street (not on the lung pad's step)
const W = new ChunkWorld([]);
for (const c of near) W.set(c.cx + ':' + c.cz, chunkBoxes(packChunk(c)));
W.sync();
const glb = fs.readFileSync(new URL('../../public/models/story/s_digester_wall.glb', import.meta.url));
const js = JSON.parse(glb.subarray(20, 20 + glb.readUInt32LE(12)).toString());
const meta = JSON.parse(js.nodes.find((n) => n.extras && n.extras.jf).extras.jf);
for (const id of ['dot', 'mina']) {
  const s = NPC_SPOTS[id].p, L = meta.sockets[id], d = DIGESTER.sockets[id];
  assert.deepEqual(s, d, id + ': cast_slice.js and DIGESTER disagree');
  const world = [ax - L[0], ay + L[1], az - L[2]]; // (the prop turned PI: x and z flip)
  for (let k = 0; k < 3; k++) assert.ok(Math.abs(world[k] - s[k]) < 0.01, `${id}'s niche (${world}) is not at her spot (${s})`);
  const h = W.raycast([s[0], s[1] + 1.5, s[2]], [0, -1, 0], 7.5);
  assert.ok(h && Math.abs(h.point[1] - ay) < 0.05, `${id} stands at ${h && h.point[1]}, not on the street (${ay})`);
}
// 4. the file: listed, breathing skin (props.js pulses *flesh*), a far copy of every part, the people it has in it
const index = JSON.parse(fs.readFileSync(new URL('../../public/models/story/index.json', import.meta.url), 'utf8'));
assert.ok(index.includes('s_digester_wall'), 'not in index.json');
const mats = js.materials.map((m) => m.name), meshes = js.nodes.filter((n) => n.mesh != null).map((n) => n.name);
assert.ok(mats.includes('dw_flesh_pulse') && mats.includes('dw_skin') && mats.includes('dw_bits'), 'materials: ' + mats);
for (const n of meshes.filter((n) => !n.endsWith('_lod1'))) assert.ok(meshes.includes(n + '_lod1'), n + ' has no far copy');
assert.ok(meta.people.length >= 6 && meta.people.some((p) => /waving/.test(p.note)), 'the people in it');
assert.ok(meta.tris < 70000 && meta.tris_lod1 < meta.tris / 3.5, 'tris ' + meta.tris + ' / ' + meta.tris_lod1);
// 5. no file = the code stand-in, not a magenta box
assert.match(fs.readFileSync(new URL('../../public/js/city/propcode.js', import.meta.url), 'utf8'), /\n  digester_wall: \[\[/);
console.log('digester wall ok:', meta.tris, 'tris,', meta.tris_lod1, 'far,', meta.people.length, 'people');
