// the mech hero kit's data in the shipped mech files (public/models/x_mech_*.glb, root meta "jf"): the MECH DROP
// landing clips, the clip events the game plays (public/js/mechlook.js), the decal / spray slots.
// node --test tests/mechkit.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const FX = new Set(['dust', 'step', 'slam', 'spark', 'glint', 'burst', 'vent', 'flare', 'pop']);
function glb(name) {
  const d = fs.readFileSync(new URL(`../public/models/${name}.glb`, import.meta.url));
  assert.equal(d.toString('ascii', 0, 4), 'glTF');
  const n = d.readUInt32LE(12), j = JSON.parse(d.toString('utf8', 20, 20 + n));
  const root = j.nodes.find((x) => x.extras && typeof x.extras.jf === 'string');
  assert.ok(root, 'a root node with the jf meta');
  return { j, meta: JSON.parse(root.extras.jf), nodes: new Set(j.nodes.map((x) => x.name)), anims: new Set((j.animations || []).map((a) => a.name)) };
}

for (const id of ['x_mech_paperplane', 'x_mech_nightshift', 'x_mech_wrecking', 'x_mech_vending']) {
  test(`${id}: the landing clips are in the file and in the meta`, () => {
    const { meta, anims } = glb(id), byName = Object.fromEntries(meta.clips.map((c) => [c.name, c]));
    for (const c of ['drop_fall', 'hero_intro', 'drop_in', 'idle']) assert.ok(anims.has(c) && byName[c], c);
    assert.equal(byName.drop_fall.loop, true);
    assert.equal(byName.hero_intro.hold, true); // (an empty mech waits in its signature pose)
    assert.ok(byName.hero_intro.dur > 1 && byName.hero_intro.dur < 2.5, 'fits the 1.5 s landing shot, give or take');
  });
  test(`${id}: every clip event is well formed, inside its clip and at a node the model has`, () => {
    const { meta, nodes } = glb(id);
    let n = 0;
    for (const c of meta.clips) {
      if (c.events === undefined) continue;
      assert.ok(Array.isArray(c.events), c.name);
      for (const e of c.events) {
        n++;
        assert.ok(Number.isFinite(e.t) && e.t >= 0 && e.t <= c.dur + 1e-6, `${c.name} t ${e.t}`);
        assert.ok(FX.has(e.fx), `${c.name} fx ${e.fx}`);
        assert.ok(typeof e.at === 'string' && nodes.has(e.at), `${c.name} at ${e.at}`);
        if (e.shake !== undefined) assert.ok(Number.isFinite(e.shake) && e.shake > 0 && e.shake <= 1);
        if (e.ground !== undefined) assert.equal(e.ground, true);
      }
    }
    assert.ok(n >= 10, 'the weight pass put events in');
    const hi = meta.clips.find((c) => c.name === 'hero_intro');
    assert.ok(hi.events.some((e) => e.t === 0 && e.fx === 'slam' && e.shake > 0), 'the landing hits the floor at t = 0');
  });
  test(`${id}: a far LOD, if it has one, sits beside every near mesh and is cheaper`, () => {
    const { meta, nodes } = glb(id);
    if (!meta.lod) return; // (the files from before the detail pass have none)
    assert.ok(Number.isFinite(meta.lod.dist) && meta.lod.dist > 0, 'lod.dist');
    const near = [...nodes].filter((n) => /_mesh$/.test(n)), far = [...nodes].filter((n) => /_lod1$/.test(n));
    assert.ok(far.length > 0, 'far meshes');
    for (const n of far) assert.ok(nodes.has(n.replace(/_lod1$/, '_mesh')) && Object.hasOwn(meta.joints, n.replace(/_lod1$/, '')), n);
    for (const n of near) assert.ok(nodes.has(n.replace(/_mesh$/, '_lod1')), 'no far LOD for ' + n);
    const [tn, tf] = meta.lod.tris;
    assert.ok(tf > 0 && tf <= 16000 && tf < tn / 2, `far ${tf} vs near ${tn}`);
  });
  test(`${id}: decal / spray slots sit on a joint, with a marker each`, () => {
    const { meta, nodes } = glb(id);
    assert.ok(Array.isArray(meta.decal_slots) && meta.decal_slots.length >= 1);
    meta.decal_slots.forEach((s, i) => {
      assert.ok(Object.hasOwn(meta.joints, s.joint), s.joint);
      for (const k of ['at', 'dir', 'up']) assert.ok(Array.isArray(s[k]) && s[k].length === 3 && s[k].every(Number.isFinite), k);
      assert.ok(Math.abs(Math.hypot(...s.dir) - 1) < 0.02, 'dir is a unit vector');
      assert.ok(s.size > 0.2 && s.size < 2);
      assert.ok(nodes.has(`mk_${s.name}`) && s.name === `spray_${i}`, s.name);
    });
  });
}
