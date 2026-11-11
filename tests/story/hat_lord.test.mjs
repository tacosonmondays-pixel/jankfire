// MADAM CHAIR (hat_lord): the model, its parts file, her skeleton and her clips agree with each other.
//   every joint the parts file names has a part in the glb (or is a pure pivot the file says is empty)
//   every named part of the parts file is a node of the glb, on the joint the file says
//   every marker sits on a joint that exists; the look-at marks are on the hat's eye pair
//   every channel of every clip drives a joint the skeleton has; loops come round where they began
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const ROOT = new URL('../../', import.meta.url).pathname;
const glb = fs.readFileSync(ROOT + 'public/models/cast/c_hat_lord.glb');
const gltf = JSON.parse(glb.subarray(20, 20 + glb.readUInt32LE(12)).toString('utf8'));
const parts = JSON.parse(fs.readFileSync(ROOT + 'public/models/cast/c_hat_lord.parts.json', 'utf8'));
const look = fs.readFileSync(ROOT + 'public/js/story/hatlook.js', 'utf8');
const { HL_DATA } = await import(ROOT + 'public/js/story/hl_clipdata.js');
const nodes = gltf.nodes.map((n) => n.name).filter((n) => /^part_/.test(n));
const jointOf = (n) => /^part_([A-Za-z]+)/.exec(n)[1], tagOf = (n) => (/__([A-Za-z]+)/.exec(n) || [])[1] || '';
const STD = ['body', 'legL', 'legR', 'kneeL', 'kneeR', 'spine', 'neck', 'head', 'armL', 'arm', 'foreL', 'foreR', 'handL', 'handR'];

test('hat_lord: the glb is cast format on her skeleton', () => {
  assert.ok(nodes.length > 60, 'part nodes: ' + nodes.length);
  const joints = Object.keys(parts.joints);
  for (const n of nodes) assert.ok(joints.includes(jointOf(n)), `${n} is on a joint the skeleton does not have`);
  // the names the game's dressCast reads are letters only
  for (const n of nodes) assert.match(n, /^part_[A-Za-z]+(__[A-Za-z]+)?(\.\d+)?$/, n);
  // her own joints are the ones hatlook.js makes
  for (const j of joints) if (!STD.includes(j)) assert.ok(new RegExp(`\\['${j}', '`).test(look), `hatlook.js EXTRA has no ${j}`);
  // every joint that should carry something does
  const empty = joints.filter((j) => !nodes.some((n) => jointOf(n) === j));
  assert.deepEqual(empty.sort(), [], 'joints with nothing on them');
});

test('hat_lord: every part and marker of the parts file is in the model', () => {
  for (const [tag, p] of Object.entries(parts.parts)) assert.ok(nodes.some((n) => tagOf(n) === tag && jointOf(n) === p.joint), `part ${tag} on ${p.joint} is not in the glb`);
  for (const [k, m] of Object.entries(parts.markers)) { assert.ok(parts.joints[m.joint], `marker ${k}: no joint ${m.joint}`); assert.ok(new RegExp(`\\b${k}: \\['${m.joint}'`).test(look), `hatlook.js MK has no ${k} on ${m.joint}`); }
  // she looks with the hat: the look-at marks are HER eye pair, on the hat's crown, and there are five weak points
  assert.equal(parts.look.at, 'eyeAt'); assert.deepEqual(parts.look.eyes, ['eyeHR', 'eyeHL']);
  for (const k of ['eyeAt', 'eyeHRAt', 'eyeHLAt']) assert.equal(parts.markers[k].joint, 'crown');
  assert.equal(parts.hit.weak.length, 5);
  for (const k of ['herEye', 'herLid', 'hatEyes', 'hatLid', 'bands', 'socket', 'cape', 'yoke', 'clasps']) assert.ok(parts.parts[k], 'named part ' + k);
  assert.ok(nodes.filter((n) => tagOf(n) === 'lod').length >= 20, 'a far LOD');
  assert.ok(parts.height > 2.7 && parts.height < 3.0, 'height ' + parts.height); assert.ok(parts.brimSpan >= 3, 'brim ' + parts.brimSpan);
  assert.ok(glb.length < 2 * 1024 * 1024, 'glb under 2 MB');
});

test('hat_lord: her clips drive joints she has, and the loops close', () => {
  const joints = new Set(Object.keys(parts.joints));
  const want = ['hl_idle', 'hl_walk', 'hl_duck', 'hl_talk', 'hl_offer', 'hl_bow', 'hl_lunge', 'hl_reveal', 'hl_attack_tell', 'hl_strike', 'hl_stagger', 'hl_hat_off'];
  for (const c of want) assert.ok(HL_DATA.clips[c], 'clip ' + c);
  for (const [name, C] of Object.entries(HL_DATA.clips)) {
    const chans = new Set(); for (const k of C.keys) for (const ch of Object.keys(k.p)) chans.add(ch); for (const o of C.osc) chans.add(o[0]); for (const b of C.blinks) for (const l of b[1]) chans.add(l + '.x');
    for (const ch of chans) { if (ch.startsWith('x.')) continue; const [j, a] = ch.split('.'); assert.ok(joints.has(j), `${name}: ${ch} drives no joint`); assert.match(a, /^(x|y|z|px|py|pz)$/, `${name}: ${ch}`); }
    if (C.loop) { // first key = last key, and every wobble fits the loop a whole number of times
      const a = C.keys[0], b = C.keys[C.keys.length - 1];
      assert.equal(b.t, C.loop, name + ' last key at the loop');
      for (const ch of new Set([...Object.keys(a.p), ...Object.keys(b.p)])) assert.ok(Math.abs((a.p[ch] ?? 0) - (b.p[ch] ?? 0)) < 1e-6, `${name}: ${ch} pops at the seam`);
      for (const [ch, , f] of C.osc) { const n = f * C.loop / (2 * Math.PI); assert.ok(Math.abs(n - Math.round(n)) < 1e-6, `${name}: ${ch} wobble does not fit the loop`); }
    }
    for (const [t] of C.marks) assert.ok(t >= 0 && t <= (C.len || C.loop || C.keys[C.keys.length - 1].t) + 1e-6, name + ' mark in range');
  }
});
