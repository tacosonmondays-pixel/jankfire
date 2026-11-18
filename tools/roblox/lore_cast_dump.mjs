// THE STORY CAST (OVERDUE), the joints half: the web's own buildLook (public/js/story/looks.js) builds each one's code
// skeleton; at the rest dressCast uses (root at the origin, scale 1, the head untilted) every joint's frame is written,
// with the code meshes the Blender model doesn't replace (the face rig on the head, any joint the .glb has no part for),
// so cast_meshes.py can put the .glb's part_<joint> meshes into the same frames.
// usage: node --import ./lore_register.mjs cast_dump.mjs <out_dir> ids...
import './lore_dom_stub.mjs';
import * as THREE from 'three';
import fs from 'node:fs';
const { buildLook } = await import('file:///C:/Users/soup2/jankfire-port/public/js/story/looks.js');
const K = 3;
const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
const ids = process.argv.slice(3);
const JN = ['root', 'lift', 'body', 'spine', 'legL', 'legR', 'kneeL', 'kneeR', 'head', 'neck', 'arm', 'armL', 'foreL', 'foreR', 'handL', 'handR'];
function glbParts(id) {
  const b = fs.readFileSync(`C:/Users/soup2/jankfire-port/public/models/cast/c_${id}.glb`), len = b.readUInt32LE(12), j = JSON.parse(b.slice(20, 20 + len).toString());
  return new Set((j.nodes || []).map((n) => /^part_([A-Za-z]+)/.exec(n.name || '')).filter(Boolean).map((m) => m[1]));
}
const hex = (c) => c.getHexString();
const report = {};
for (const id of ids) {
  const L = buildLook(id), ch = L.ch;
  const s = ch.root.scale.x, tilt = ch.head.rotation.z;
  ch.head.rotation.z = 0; ch.root.scale.setScalar(1); ch.root.position.set(0, 0, 0); ch.root.rotation.set(0, 0, 0); ch.root.updateMatrixWorld(true);
  const dressed = glbParts(id);
  const isJ = (n) => JN.some((k) => ch[k] === n);
  const nameOf = (n) => JN.find((k) => ch[k] === n);
  const jointOf = (n) => { let p = n; while (p && !isJ(p)) p = p.parent; return p; };
  const joints = [];
  for (const k of JN) {
    const n = ch[k]; if (!n) continue;
    const par = n === ch.root ? null : jointOf(n.parent);
    const pm = par ? new THREE.Matrix4().compose(par.getWorldPosition(new THREE.Vector3()), par.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1)) : new THREE.Matrix4();
    const nm = new THREE.Matrix4().compose(n.getWorldPosition(new THREE.Vector3()), n.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1));
    const rel = pm.clone().invert().multiply(nm), rp = new THREE.Vector3(), rq = new THREE.Quaternion(); rel.decompose(rp, rq, new THREE.Vector3());
    const wp = n.getWorldPosition(new THREE.Vector3()), wq = n.getWorldQuaternion(new THREE.Quaternion());
    joints.push({ name: k, parent: par ? nameOf(par) : null, cf: [...rp.multiplyScalar(K * s).toArray().map((v) => +v.toFixed(5)), ...rq.toArray().map((v) => +v.toFixed(6))],
      world: [...wp.toArray(), ...wq.toArray()].map((v) => +v.toFixed(6)), pos: n.position.toArray().map((v) => +v.toFixed(5)),
      rot: [n.rotation.x, n.rotation.y, n.rotation.z].map((v) => +v.toFixed(5)), order: n.rotation.order,
      posScale: +(K * s * (n.parent ? n.parent.getWorldScale(new THREE.Vector3()).x : 1)).toFixed(5), dressed: dressed.has(k) });
  }
  // the code meshes kept: the face rig, and every mesh on a joint the .glb doesn't dress
  const keep = L.face ? L.face.root : null;
  const under = (m, a) => { for (let p = m; p; p = p.parent) if (p === a) return true; return false; };
  const pieces = {}; const A = new THREE.Vector3(), B = new THREE.Vector3(), C = new THREE.Vector3();
  ch.root.traverse((m) => {
    if (!m.isMesh) return;
    for (let p = m; p; p = p.parent) if (!p.visible) return;
    const j = jointOf(m), jn = nameOf(j);
    if (dressed.has(jn) && !(keep && under(m, keep))) return;
    const jm = new THREE.Matrix4().compose(j.getWorldPosition(new THREE.Vector3()), j.getWorldQuaternion(new THREE.Quaternion()), new THREE.Vector3(1, 1, 1)).invert();
    const M = jm.multiply(m.matrixWorld), flip = M.determinant() < 0;
    const g = m.geometry.index ? m.geometry.toNonIndexed() : m.geometry, pos = g.attributes.position;
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    const groups = g.groups && g.groups.length ? g.groups : [{ start: 0, count: pos.count, materialIndex: 0 }];
    const list = (pieces[jn] ||= []);
    for (const gr of groups) {
      const mat = mats[gr.materialIndex || 0] || mats[0];
      if (!mat || mat.visible === false || (mat.transparent && mat.opacity < 0.2)) continue;
      const col = mat.color ? hex(mat.color) : 'ffffff';
      for (let i = gr.start; i < gr.start + gr.count; i += 3) {
        A.fromBufferAttribute(pos, i).applyMatrix4(M).multiplyScalar(K * s); B.fromBufferAttribute(pos, i + 1).applyMatrix4(M).multiplyScalar(K * s); C.fromBufferAttribute(pos, i + 2).applyMatrix4(M).multiplyScalar(K * s);
        const q = flip ? [A, C, B] : [A, B, C];
        list.push([...q.flatMap((v) => [+v.x.toFixed(4), +v.y.toFixed(4), +v.z.toFixed(4)]), col, 0]);
      }
    }
  });
  fs.writeFileSync(`${out}/${id}.json`, JSON.stringify({ id, K, scale: s, tilt, height: L.height, joints, pieces }));
  report[id] = { s: +s.toFixed(3), h: L.height, tilt: +tilt.toFixed(3), dressed: [...dressed].join(','), code: Object.fromEntries(Object.entries(pieces).map(([k, v]) => [k, v.length])) };
}
console.log(JSON.stringify(report, null, 1));
