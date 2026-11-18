// THE BOARD OF DIRECTORS (the web's five hidden cats: shared/secrets.js, public/js/lorecats.js), the dump half.
// The web's own buildCat, in each cat's own pose (one updateCat step lays the pose on), written in three moving
// pieces (body with legs, head with ears, tail) plus the bits that stay as they are. The owner wants creatures as ONE
// cohesive mesh with real joins, never stacked primitives (chunky-model-style, 18 Nov), so lore_cat_meshes.py voxel-
// remeshes each piece's "solid" triangles into one smooth body and paints it from all of them.
// Every triangle: x,y,z x3 (studs, in its joint's frame), colour, kind:
//   solid   makes the shape (torso, belly, haunches, legs, paws, skull, cheeks, muzzle, ears, tail)
//   paint   colour only, never shape (tabby stripes, the forehead M, calico patches: they lie on the fur)
//   detail  kept as it is, on the surface (eyes, nose, Gravy's crown, Biscuit's glasses, Beans' tie, Meatloaf's lanyard)
//   prop    Gremlin's cardboard box (its LEGAL label becomes plain card)
// Whiskers are left out (hair-thin boxes).
// usage: node --import ./tools/roblox/lore_register.mjs tools/roblox/lore_cat_dump.mjs <out_dir>
import './lore_dom_stub.mjs';
import * as THREE from 'three';
import fs from 'node:fs';
const { buildCat, updateCat } = await import('file:///C:/Users/soup2/jankfire-port/public/js/lorecats.js');
const { SECRETS } = await import('file:///C:/Users/soup2/jankfire-port/shared/secrets.js');
const K = 3.5; // studs per web metre (a touch over the people's 3: a cat has to read in the hub)
const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
const ACC = new Set(['ffc21a', 'ff3a6a', '2a2a30', 'd02030', 'a01020', '2a6cff']); // crown, jewel, glasses, tie, lanyard
const report = {};
for (const id of Object.keys(SECRETS).filter((k) => SECRETS[k].kind === 'cat')) {
  const s = SECRETS[id];
  const c = buildCat(s);
  updateCat(c, 1 / 60, 1000, null); // the pose on
  const root = c.root; root.name = 'npc';
  c.body.name = 'body'; c.neck.name = 'neck'; c.tailBase.name = 'tailBase';
  root.updateMatrixWorld(true);
  const JN = [root, c.body, c.neck, c.tailBase];
  const jointOf = (n) => { let p = n; while (p && !JN.includes(p)) p = p.parent; return p; };
  const under = (n, a) => { for (let p = n; p; p = p.parent) if (p === a) return true; return false; };
  const eyeGroups = c.eyes.map((e) => e.e);
  const joints = [];
  for (const n of JN) {
    const par = n === root ? null : jointOf(n.parent);
    const pm = par ? new THREE.Matrix4().compose(par.getWorldPosition(new THREE.Vector3()), par.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1)) : new THREE.Matrix4();
    const nm = new THREE.Matrix4().compose(n.getWorldPosition(new THREE.Vector3()), n.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1));
    const rel = pm.clone().invert().multiply(nm), rp = new THREE.Vector3(), rq = new THREE.Quaternion(); rel.decompose(rp, rq, new THREE.Vector3());
    const ws = n.parent ? n.parent.getWorldScale(new THREE.Vector3()).x : 1;
    joints.push({ name: n.name, parent: par ? par.name : null, cf: [...rp.multiplyScalar(K).toArray().map((v) => +v.toFixed(5)), ...rq.toArray().map((v) => +v.toFixed(6))],
      pos: n.position.toArray().map((v) => +v.toFixed(5)), rot: [n.rotation.x, n.rotation.y, n.rotation.z].map((v) => +v.toFixed(5)), order: 'XYZ', posScale: +(ws * K).toFixed(5), moves: n !== root });
  }
  const pieces = {}; const A = new THREE.Vector3(), B = new THREE.Vector3(), C = new THREE.Vector3();
  root.traverse((m) => {
    if (!m.isMesh) return;
    for (let p = m; p; p = p.parent) if (!p.visible) return;
    const g0 = m.geometry, gp = g0.parameters || {};
    const col = (Array.isArray(m.material) ? m.material[0] : m.material).color.getHexString();
    const sc = m.scale;
    let kind = 'solid';
    if (g0.type === 'BoxGeometry' && gp.width >= 0.07 && gp.height < 0.004) return; // whiskers
    if (c.boxG && under(m, c.boxG)) kind = 'prop';
    else if (eyeGroups.some((e) => under(m, e))) kind = 'detail';
    else if (ACC.has(col) || (g0.type === 'TorusGeometry')) kind = 'detail';
    else if (g0.type === 'BoxGeometry' && (gp.width < 0.03 && gp.height < 0.03)) kind = 'detail'; // nose and the line under it (the M marks are paint, below)
    if (g0.type === 'BoxGeometry' && gp.width < 0.01 && gp.height > 0.02) kind = 'paint'; // the forehead M
    if (g0.type === 'SphereGeometry' && sc.z <= 0.12) kind = 'paint'; // tabby stripes: thin slices over the torso
    if (s.coat === 'calico' && g0.type === 'SphereGeometry' && (col === c.coat.b.toString(16).padStart(6, '0') || col === c.coat.c.toString(16).padStart(6, '0')) && under(m, c.body) && !under(m, c.neck) && !under(m, c.tailBase)) kind = 'paint';
    if (col === '050505' || col === 'ffffff' && under(m, c.body) && !under(m, c.neck) && g0.type === 'BoxGeometry') kind = 'detail'; // pupils, Meatloaf's badge
    const j = jointOf(m), jm = new THREE.Matrix4().compose(j.getWorldPosition(new THREE.Vector3()), j.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1)).invert();
    const M = jm.multiply(m.matrixWorld), flip = M.determinant() < 0;
    const g = g0.index ? g0.toNonIndexed() : g0, pos = g.attributes.position;
    const key = j.name === 'npc' ? 'box' : j.name;
    const list = (pieces[key] ||= []);
    for (let i = 0; i < pos.count; i += 3) {
      A.fromBufferAttribute(pos, i).applyMatrix4(M).multiplyScalar(K); B.fromBufferAttribute(pos, i + 1).applyMatrix4(M).multiplyScalar(K); C.fromBufferAttribute(pos, i + 2).applyMatrix4(M).multiplyScalar(K);
      const q = flip ? [A, C, B] : [A, B, C];
      list.push([...q.flatMap((v) => [+v.x.toFixed(4), +v.y.toFixed(4), +v.z.toFixed(4)]), col, kind]);
    }
  });
  const box = new THREE.Box3().setFromObject(root);
  fs.writeFileSync(`${out}/${id}.json`, JSON.stringify({ id, name: s.name, K, pose: s.pose, coat: s.coat, joints, pieces, box: [box.min.toArray().map((v) => v * K), box.max.toArray().map((v) => v * K)] }));
  const kinds = {}; for (const [k, v] of Object.entries(pieces)) for (const t of v) kinds[k + ':' + t[10]] = (kinds[k + ':' + t[10]] || 0) + 1;
  report[id] = { pose: s.pose, coat: s.coat, size: box.getSize(new THREE.Vector3()).multiplyScalar(K).toArray().map((v) => +v.toFixed(2)), kinds };
}
console.log(JSON.stringify(report, null, 1));
