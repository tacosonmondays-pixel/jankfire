// THE HEADLINER (jester_lord): the model, its parts file, his skeleton and his clips agree with each other.
//   the glb is the cast format: part_<joint>__<tag> nodes on joints the skeleton has, skinned on one skin whose joints
//   are his joints by name, a far model, a hidden stump
//   every part and marker of the parts file is in the model / in jesterlook.js MK, at the same numbers
//   the rig in jl_clipdata.js, the parts file and joints.json are the same skeleton: 14 cast joints, 8 legs of 4
//   every channel of every clip drives a joint he has; loops come round where they began; no leg whips round
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const ROOT = new URL('../../', import.meta.url).pathname;
const glb = fs.readFileSync(ROOT + 'public/models/cast/c_jester_lord.glb');
const gltf = JSON.parse(glb.subarray(20, 20 + glb.readUInt32LE(12)).toString('utf8'));
const parts = JSON.parse(fs.readFileSync(ROOT + 'public/models/cast/c_jester_lord.parts.json', 'utf8'));
const look = fs.readFileSync(ROOT + 'public/js/story/jesterlook.js', 'utf8');
const joints = JSON.parse(fs.readFileSync(ROOT + 'tools/blender/cast/joints.json', 'utf8')).jester_lord;
const { JL_DATA } = await import(ROOT + 'public/js/story/jl_clipdata.js');
const nodes = gltf.nodes.map((n) => n.name).filter((n) => /^part_/.test(n));
const jointOf = (n) => /^part_([A-Za-z]+)/.exec(n)[1], tagOf = (n) => (/__([A-Za-z]+)/.exec(n) || [])[1] || '';
const STD = ['body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR'];
const RIG = JL_DATA.rig.map((e) => e[0]);

test('jester_lord: the glb is cast format, skinned on his skeleton', () => {
  for (const n of nodes) assert.match(n, /^part_[A-Za-z]+(__[A-Za-z]+)?(\.\d+)?$/, n); // (the names the game's dressCast reads are letters only)
  for (const n of nodes) assert.ok(RIG.includes(jointOf(n)), `${n} is on a joint the skeleton does not have`);
  assert.deepEqual([...new Set(nodes.map(tagOf))].sort(), ['dmgStump', 'jester', 'lod', 'spider']);
  assert.equal(gltf.skins.length, 1, 'one skin');
  const skinJoints = gltf.skins[0].joints.map((i) => gltf.nodes[i].name);
  assert.deepEqual([...skinJoints].sort(), [...RIG].sort(), 'the skin\'s joints are his joints, by name');
  const skinned = gltf.nodes.filter((n) => n.skin !== undefined).map((n) => tagOf(n.name));
  assert.deepEqual(skinned.sort(), ['jester', 'lod', 'spider'], 'the two halves and the far model are skinned; the stump rides the thorax');
  assert.ok(glb.length < 2 * 1024 * 1024, 'glb under 2 MB: ' + glb.length);
  assert.ok(gltf.materials.length <= 4, 'four materials at most (draw calls): ' + gltf.materials.length);
});

test('jester_lord: every part and marker of the parts file is in the model and the look', () => {
  for (const [tag, p] of Object.entries(parts.parts)) assert.ok(nodes.some((n) => tagOf(n) === tag && jointOf(n) === p.joint), `part ${tag} on ${p.joint} is not in the glb`);
  const near = parts.parts.spider.tris + parts.parts.jester.tris;
  assert.ok(near <= 26000, 'near model triangles ' + near); assert.ok(parts.parts.lod.tris < near / 4, 'far model ' + parts.parts.lod.tris);
  for (const [k, m] of Object.entries(parts.markers)) {
    assert.ok(RIG.includes(m.joint), `marker ${k}: no joint ${m.joint}`);
    const hit = new RegExp(`\\b${k}: \\['${m.joint}', ([^\\]]+)\\]`).exec(look);
    assert.ok(hit, `jesterlook.js MK has no ${k} on ${m.joint}`);
    const v = hit[1].split(',').map(Number);
    for (let i = 0; i < 3; i++) assert.ok(Math.abs(v[i] - m.local[i]) < 1e-3, `MK ${k} is not where the parts file says (${v} vs ${m.local})`);
  }
  assert.equal(parts.look.at, 'eyeAt'); assert.equal(parts.hit.legOff, 'RB');
  assert.equal(Object.keys(parts.hit.legs).length, 8, 'eight legs to aim at');
  assert.ok(parts.height > 3.0 && parts.height < 3.6, 'height ' + parts.height); assert.ok(parts.heightWithHat > 3.5 && parts.heightWithHat < 4.1, 'with the hat ' + parts.heightWithHat);
  assert.ok(parts.legSpan[0] > 4.5, 'leg span ' + parts.legSpan);
});

test('jester_lord: one skeleton everywhere (clip data, parts file, joints.json)', () => {
  assert.ok(RIG.length <= 64, 'joints ' + RIG.length);
  for (const j of STD) assert.ok(RIG.includes(j), 'the cast joint ' + j);
  for (const s of 'RL') for (const p of 'ABCD') for (const pre of ['fem', 'tib', 'foot', 'bell']) assert.ok(RIG.includes(pre + s + p), 'leg joint ' + pre + s + p);
  assert.equal(JL_DATA.bells.length, 10, 'a bell on every foot and on both horns');
  for (const [n, par, p, r] of JL_DATA.rig) {
    assert.match(n, /^[A-Za-z]+$/, n);
    const J = parts.joints[n]; assert.ok(J, 'parts file joint ' + n); assert.equal(J.parent, par, n + ' parent');
    for (let i = 0; i < 3; i++) { assert.ok(Math.abs(J.p[i] - p[i]) < 1e-3, n + ' place'); assert.ok(Math.abs(J.r[i] - r[i]) < 1e-3, n + ' rest turn'); }
    assert.equal(joints.parents[n], par, 'joints.json parent ' + n);
    for (let i = 0; i < 3; i++) assert.ok(Math.abs(joints.local[n].p[i] - p[i]) < 1e-3, 'joints.json place ' + n);
  }
  assert.match(fs.readFileSync(ROOT + 'public/js/story/looks.js', 'utf8'), /jester_lord: \(\) => jesterLordLook\(/, 'looks.js registers him');
});

test('jester_lord: his clips drive joints he has, the loops close, no leg whips round', () => {
  const have = new Set(RIG);
  for (const c of ['jl_idle', 'jl_talk', 'jl_bow', 'jl_walk', 'jl_hang', 'jl_drop', 'jl_leg_off', 'jl_leg_back']) assert.ok(JL_DATA.clips[c], 'clip ' + c);
  for (const [name, C] of Object.entries(JL_DATA.clips)) {
    const chans = new Set(); for (const k of C.keys) for (const ch of Object.keys(k.p)) chans.add(ch); for (const o of C.osc) chans.add(o[0]);
    for (const ch of chans) { if (ch.startsWith('x.')) continue; const [j, a] = ch.split('.'); assert.ok(have.has(j), `${name}: ${ch} drives no joint`); assert.match(a, /^(x|y|z|px|py|pz)$/, `${name}: ${ch}`); }
    for (let i = 1; i < C.keys.length; i++) assert.ok(C.keys[i].t >= C.keys[i - 1].t, name + ' keys in order');
    if (C.loop) { // first key = last key, and every wobble fits the loop a whole number of times
      const a = C.keys[0], b = C.keys[C.keys.length - 1];
      assert.equal(b.t, C.loop, name + ' last key at the loop');
      for (const ch of new Set([...Object.keys(a.p), ...Object.keys(b.p)])) assert.ok(Math.abs((a.p[ch] ?? 0) - (b.p[ch] ?? 0)) < 1e-3, `${name}: ${ch} pops at the seam`);
      for (const [ch, , f] of C.osc) { const n = (f * C.loop) / (2 * Math.PI); assert.ok(Math.abs(n - Math.round(n)) < 1e-6, `${name}: ${ch} wobble does not fit the loop`); }
    }
    for (const [t] of C.marks) assert.ok(t >= 0 && t <= (C.len || C.loop || C.keys[C.keys.length - 1].t) + 1e-6, name + ' mark in range');
    // a femur's turn never jumps more than half a turn between two keys (an euler that wraps whips the leg round in a frame)
    for (const ch of chans) if (/^fem[RL][A-D]\.[xyz]$/.test(ch)) for (let i = 1; i < C.keys.length; i++) assert.ok(Math.abs((C.keys[i].p[ch] ?? 0) - (C.keys[i - 1].p[ch] ?? 0)) < Math.PI, `${name}: ${ch} jumps at ${C.keys[i].t}`);
  }
  assert.ok(JL_DATA.clips.jl_leg_off.keys.some((k) => Math.hypot(k.p['femRB.px'] ?? 0, k.p['femRB.py'] ?? 0, k.p['femRB.pz'] ?? 0) > 2.5), 'the leg really flies off');
});
